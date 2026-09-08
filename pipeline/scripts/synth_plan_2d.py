"""
synth_plan_2d.py -- Structured3D gt.json -> an annotation-blind 2D SVG floor plan, so OUR
reader (svg_plan_reader) can be RUN on a synthesized plan and scored for REAL. This closes the
gap the plan-extraction memory named ("reader-scores need a 2D synthesizer"): until now the
Structured3D lane could only run benchmark_reader gt-vs-gt, a SYMMETRIC selftest that cannot
catch an error (a convention flip, an over-emitted flag, all self-match with distance 0). The
3D corpus is the indoor/outdoor ANSWER KEY; this module draws the 2D a reader would see and
runs the reader on it, so F3_indoor becomes a pred!=gt number for the FIRST time on any corpus.

    python synth_plan_2d.py <scene.gt.json> <out.svg> [--walls]
    python synth_plan_2d.py --score <gt-dir> <out-dir> [limit N] [--walls] [--realistic] [--fuse-gap MM]

TWO SCORING LANES (--score):
  per-object (default) -- draw EVERY element, score vs the raw per-object GT. The conservative
    baseline; F3 n is ~a tenth of GT because Structured3D 3D sub-objects fuse under the reader's
    closing and match no single per-object box (see the DETECTION note below).
  --realistic         -- the PLAN-SYMBOL lane (v1.1): filter sub-150mm decor, GROUP co-located
    drawable objects into the single furniture SYMBOL a 2D plan would draw (union footprint +
    room-consensus indoor), and score the reader's fused cluster against THAT. Same always-indoor
    baseline, but a ~1.5x larger, plan-faithful F3 slice with ~1.7x more OUTDOOR test cases. See
    group_symbols; grouping is geometry-only so the annotation-blindness invariant is unchanged.

THE HONESTY CORE (mirrors svg_plan_reader.read_ink's annotation-blindness): the indoor label is
NEVER drawn. synth_svg reads x/y/w/d geometry ONLY; two gt docs that differ solely in `indoor`
produce a BYTE-IDENTICAL SVG (pinned by test_synth_plan_2d). So F3 measures whether GEOMETRY
alone recovers the room semantics -- it cannot leak the answer key into the reader's input.

WHAT THE F3 NUMBER MEANS (read this before quoting it): svg_plan_reader has NO indoor
classifier -- it emits no `indoor` key, so benchmark_reader scores every matched pred element
as indoor=True (silence = ordinary this-floor-indoor). The resulting F3 accuracy is therefore
the ALWAYS-INDOOR BASELINE: it equals the indoor fraction among matched pairs, and its
`wrong_ids` are exactly the OUTDOOR (balcony/garden) pieces the reader would misclassify. The
value of this module is NOT that baseline number (which the adapter's meta already implies) --
it is that the loop is now WIRED end-to-end: an indoor-inference upgrade to the reader (e.g.
generalising zone_flag beyond the south-facade case) becomes an immediately SCOREABLE pred!=gt
delta over this baseline, on real balcony/garden ground truth.

DETECTION RECALL IS LOW ON THIS CORPUS -- AND THAT IS NOT A SOUNDNESS PASS (adversarially
verified 2026-07-08). F3 scores only on MATCHED pairs, and plan_cluster recovers roughly a
TENTH of the synthesized footprints (~10% recall over the 200-scene sample), because: (a) ~54-
63% of Structured3D 'objects' are sub-150mm decor (cups, books, picture frames) that the reader
screens as thin ink BY DESIGN; (b) boxes >~3.6m on both axes drop as merged_blob; and (c)
furniture drawn within CLOSE_MM (40mm) -- a bed with a flush nightstand, stacked cushions --
MERGES into one cluster whose AABB matches neither GT box, so BOTH pieces leave the F3 set. So
F3 is measured on the DETECTED SUBSET (~1.7k of ~20k indoor-carrying GT). Read render_report's
representativeness line before quoting F3: the matched subset's OUTDOOR fraction is reported
next to the corpus outdoor rate -- on the 200-scene run they are close (~5.6% vs ~4.7%), so the
baseline is NOT optimistically biased against outdoor, but the sample is SMALL and clustered
furniture is under-represented. Raising the scoreable slice (a realistic size-filtered draw +
instance separation) is the clear next slice; the hard detection test remains FloorPlanCAD's
real symbol ink, not these clean rectangles.

WALLS (opt-in, --walls): the synthesized plan can also draw gt['wall_lines'] + glazing as thin
structure lines (a realistic plan). It is OFF by default for the headline F3 lane because a
furniture rect drawn hard against a wall merges into the wall network under plan_cluster's CLOSE
and is then not recovered as its own element -- which would drop detection recall and conflate
'reader can't separate furniture from walls' (a real but SEPARATE morphology problem) with the
F3 measurement. Furniture-only isolates the F3 variable; walls are there for the geometric-indoor
follow-up lane (which needs the enclosure geometry to infer indoor without the label).
"""
import glob
import json
import os
import sys
import time

import benchmark_reader as B
import placement_gate as PG                  # footprint(): the SAME AABB benchmark_reader scores
import svg_plan_reader as R
from plan_cluster import _screen_component   # the reader's OWN size screen -> zero drift

SYNTH_VERSION = "synth_plan_2d v1.1"
PAD_MM = 100.0

# The reader FUSES two drawn footprints closer than this edge-gap (mm) into one cluster --
# EMPIRICALLY CALIBRATED against svg_plan_reader itself (scratchpad/calibrate_fuse: two 500mm
# rects at res=6mm stay one cluster up to a 90mm gap, separate at 100mm; a 200mm nightstand
# fuses into a 1500mm bed's union at every gap tested <=80mm). It is DELIBERATELY larger than
# svg_plan_reader.CLOSE_MM=40 (the closing RADIUS): binary_closing bridges a gap up to ~2*r,
# so the reader's real symbol-fusing distance is ~2x CLOSE_MM. Grouping GT at this calibrated
# distance is what makes a GT plan-symbol line up with the cluster the reader will actually
# emit; the achieved detection recall in the report MEASURES how good this proxy is (a fixed
# 90mm slightly under-groups the few scenes coarser than res=6mm -- reported, never assumed).
FUSE_GAP_MM = 90.0


def _as_footprint(e):
    """An element with x/y/w/d replaced by its TRUE axis-aligned footprint (placement_gate.footprint
    -- the same AABB benchmark_reader scores) and rot dropped. A rot-less (blind-lane) element is
    returned UNCHANGED, byte-identical; a KINDED element (local un-yawed rect + rot, the adapter's
    double-rotation fix) gets its rotation baked into the drawn/grouped AABB. Every geometry consumer
    below (draw, fuse, group, size-screen) then sees what the reader will actually see + what the GT
    scores -- without this a labelled corpus would silently draw every 90/270 piece un-rotated."""
    if e.get("rot") in (None, 0, 0.0):
        return e                            # blind / axis-aligned: unchanged (byte-identical)
    x0, y0, x1, y1 = PG.footprint(e)
    out = {k: v for k, v in e.items() if k != "rot"}
    out["x"], out["y"] = round(x0, 1), round(y0, 1)
    out["w"], out["d"] = round(x1 - x0, 1), round(y1 - y0, 1)
    return out


def synth_svg(gt_doc, include_walls=False):
    """gt.json document -> an SVG string in mm (scale 1.0), ANNOTATION-BLIND. Furniture elements
    become <rect> footprints (the reader's morphology recovers each AABB); with include_walls,
    gt['wall_lines'] + gt['glazing_lines'] are drawn as thin <line> structure. The indoor/kind
    fields are NEVER read -- only geometry (x/y/w/d + rot, baked into the footprint AABB via
    _as_footprint) and wall endpoints reach the drawing, so the blindness invariant is unchanged."""
    elements = [_as_footprint(e) for e in (gt_doc.get("elements", []) or [])]
    walls = (gt_doc.get("wall_lines", []) or []) if include_walls else []
    glaz = (gt_doc.get("glazing_lines", []) or []) if include_walls else []

    xs, ys = [], []
    for e in elements:
        xs += [float(e["x"]), float(e["x"]) + float(e["w"])]
        ys += [float(e["y"]), float(e["y"]) + float(e["d"])]
    for w in walls + glaz:
        xs += [float(w["x1"]), float(w["x2"])]
        ys += [float(w["y1"]), float(w["y2"])]
    if not xs:                                  # an empty plan still emits a valid (empty) SVG
        xs, ys = [0.0, 1.0], [0.0, 1.0]
    minx, miny = min(xs) - PAD_MM, min(ys) - PAD_MM
    vw, vh = (max(xs) - min(xs)) + 2 * PAD_MM, (max(ys) - min(ys)) + 2 * PAD_MM

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="{minx:.1f} {miny:.1f} {vw:.1f} {vh:.1f}">']
    # structure first (drawn under the furniture), then furniture footprints. Order is geometry
    # only -- it never depends on indoor/kind, so the blindness invariant holds.
    for w in walls:
        parts.append(f'<line x1="{float(w["x1"]):.1f}" y1="{float(w["y1"]):.1f}" '
                     f'x2="{float(w["x2"]):.1f}" y2="{float(w["y2"]):.1f}"/>')
    for g in glaz:
        parts.append(f'<line x1="{float(g["x1"]):.1f}" y1="{float(g["y1"]):.1f}" '
                     f'x2="{float(g["x2"]):.1f}" y2="{float(g["y2"]):.1f}"/>')
    for e in elements:
        parts.append(f'<rect x="{float(e["x"]):.1f}" y="{float(e["y"]):.1f}" '
                     f'width="{float(e["w"]):.1f}" height="{float(e["d"]):.1f}"/>')
    parts.append('</svg>')
    return "\n".join(parts)


# ---- realistic plan-symbol lane (the F3 slice expander) -----------------------------------
# WHY (measured 2026-07-08): the per-object v1.0 lane scored F3 on ~1.7k of ~27k GT because a
# Structured3D scene stores 3D SUB-objects (a bed's frame + mattress + duvet + pillows; a table
# with the chairs tucked under it) that project to OVERLAPPING 2D footprints. 47.7% of GT is
# sub-150mm decor the reader screens as thin; of the drawable 52%, 81% has a neighbour within
# the reader's fuse distance -> the reader emits ONE cluster whose AABB matches NONE of the
# per-object GT boxes, so every fused piece leaves the F3 set. But a real 2D floor plan draws
# those sub-objects as ONE furniture SYMBOL. This lane changes the GT UNIT from 3D-object to
# plan-symbol (the correct unit for a 2D-plan reader): filter decor, GROUP co-located drawable
# objects (geometry only) into union symbols, give each the room-consensus indoor label, and
# score the reader's fused cluster against THAT. It is NOT a reader upgrade and NOT a higher
# accuracy claim -- the reader still has no indoor classifier, so F3 stays the always-indoor
# BASELINE; the deliverable is a 1.5x larger, plan-faithful scoreable slice with ~1.7x more
# OUTDOOR test cases (balcony/garden symbols, the hard half a future classifier must win on).
#
# HONESTY INVARIANTS (mirrors the v1.0 core):
#   - annotation-blind: grouping + drawing read x/y/w/d ONLY. The indoor consensus is computed
#     on the GT (scoring) side and NEVER reaches the SVG, so two docs differing only in indoor
#     still synthesize byte-identically (pinned in test_synth_plan_2d).
#   - decor filter reuses the reader's OWN _screen_component (no threshold can drift).
#   - a group whose members DISAGREE on indoor (indoor True and False both present -- 52/3892
#     symbols, a piece straddling a balcony threshold) emits NO indoor key: it is COUNTED as
#     mixed and left out of F3, never forced to a guessed side.
#   - a union footprint the reader would itself drop as merged_blob (>3600mm both axes) is kept
#     in GT (it is a real drawn thing) and COUNTED -- it simply cannot match, an honest
#     detection miss, not a hidden exclusion.
def _member_class(e):
    """(is_drawable, reason). Reuses the reader's size screen so 'what a plan draws' == 'what
    the reader can keep': thin (<150mm either axis) decor and single-object merged_blob
    (>3600mm both) are NOT drawn -- exactly the components the reader would screen anyway."""
    keep, reason = _screen_component(float(e["w"]), float(e["d"]))
    return keep, reason


def _fuses(a, b, gap):
    """True if two footprints are within `gap` mm on BOTH axes (so the reader's morphological
    closing bridges them into one component). Overlap on an axis counts as gap 0."""
    ax0, ay0, ax1, ay1 = float(a["x"]), float(a["y"]), float(a["x"]) + float(a["w"]), float(a["y"]) + float(a["d"])
    bx0, by0, bx1, by1 = float(b["x"]), float(b["y"]), float(b["x"]) + float(b["w"]), float(b["y"]) + float(b["d"])
    gx = max(bx0 - ax1, ax0 - bx1, 0.0)
    gy = max(by0 - ay1, ay0 - by1, 0.0)
    return gx < gap and gy < gap


def group_symbols(gt_doc, fuse_gap=FUSE_GAP_MM):
    """gt_doc -> (symbols_doc, stats). Filter elements to drawable furniture (reader screen),
    single-linkage GROUP those within fuse_gap on both axes (union-find), and emit one union
    symbol per group with a room-consensus indoor label. symbols_doc has the benchmark_reader
    element schema {id,x,y,w,d,indoor?} -- it is the GT the reader's fused clusters are scored
    against. Deterministic: members keep gt order; groups are numbered by lowest member index.

    KNOWN LIMIT -- CROSS-ROOM CHAINING (adversarial review 2026-07-08, MEASURED, not hidden):
    the headline lane draws FURNITURE ONLY (no walls), and this is pure single-linkage with no
    diameter cap, so in a dense scene a transitive chain of near-neighbours fuses across a wall
    the ink never drew -- ~26% of drawable members (indoor-heavy) collapse into a handful of
    union-oversize regions (worst: one 1220-member 25.8m symbol spanning 8 rooms). Those regions
    are NOT plan symbols; they are dense multi-object areas the furniture-only reader cannot
    resolve WITHOUT walls (the reader's own clustering blobs them too -- verified: it emits a
    matching mega-cluster, so this does NOT inflate the F3 slice; if anything it SHRINKS it, so
    +slice is conservative). A union-diameter cap was tested and REJECTED: it does not recover
    slice (F3 n flat 959->964 over caps 8000..4000) and only trades detection recall for cosmetics
    -- so the honest choice is to MEASURE the member-level loss (stat.members_in_oversize + its
    indoor/outdoor split, stat.largest_symbol_*) and surface it loudly, and read symbol-level
    detection recall as FLATTERED by region-lumping (member-level coverage is the honest number).
    The real fix is a wall-aware reader (the oracle-walls lane), a separate slice."""
    raw = [_as_footprint(e) for e in (gt_doc.get("elements", []) or [])]
    members, n_decor, n_oversize_single = [], 0, 0
    for e in raw:
        keep, reason = _member_class(e)
        if keep:
            members.append(e)
        elif reason == "thin":
            n_decor += 1
        else:                                  # merged_blob single object (>3600 both axes)
            n_oversize_single += 1

    n = len(members)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if _fuses(members[i], members[j], fuse_gap):
                parent[find(i)] = find(j)

    groups = {}                                # root -> [member indices], first-seen order
    order = []
    for i in range(n):
        r = find(i)
        if r not in groups:
            groups[r] = []
            order.append(r)
        groups[r].append(i)

    symbols = []
    stat = {"singleton": 0, "multi": 0, "union_oversize": 0, "mixed_indoor": 0,
            "excluded_distinct": 0,            # union_oversize OR mixed (not additive: they overlap)
            "indoor_true": 0, "indoor_false": 0, "indoor_none": 0,
            # member-level loss to union-oversize dense regions (the honest magnitude, ~7x the
            # symbol count) + the indoor/outdoor split of what leaves the F3 slice this way
            "members_in_oversize": 0, "members_oversize_indoor_true": 0,
            "members_oversize_indoor_false": 0, "members_oversize_indoor_none": 0,
            "largest_symbol_members": 0, "largest_symbol_span_mm": 0.0}
    for gi, r in enumerate(order):
        idx = groups[r]
        ms = [members[k] for k in idx]
        x0 = min(float(m["x"]) for m in ms)
        y0 = min(float(m["y"]) for m in ms)
        x1 = max(float(m["x"]) + float(m["w"]) for m in ms)
        y1 = max(float(m["y"]) + float(m["d"]) for m in ms)
        sym = {"id": f"s{gi:04d}", "x": round(x0, 1), "y": round(y0, 1),
               "w": round(x1 - x0, 1), "d": round(y1 - y0, 1), "n_members": len(ms)}
        stat["multi" if len(ms) > 1 else "singleton"] += 1
        if len(ms) > stat["largest_symbol_members"]:
            stat["largest_symbol_members"] = len(ms)
            stat["largest_symbol_span_mm"] = round(max(sym["w"], sym["d"]), 1)
        keep_union, _ru = _screen_component(sym["w"], sym["d"])
        is_oversize = not keep_union           # union itself is merged_blob -> reader will drop
        if is_oversize:
            stat["union_oversize"] += 1
            stat["members_in_oversize"] += len(ms)
            for m in ms:                       # split the lost members by their own indoor label
                iv = m.get("indoor")
                stat["members_oversize_indoor_true" if iv is True else
                     "members_oversize_indoor_false" if iv is False else
                     "members_oversize_indoor_none"] += 1
        votes = set(m.get("indoor") for m in ms if m.get("indoor") is not None)
        is_mixed = votes == {True, False}
        if is_mixed:
            stat["mixed_indoor"] += 1          # straddles a boundary: no indoor key, counted
            stat["indoor_none"] += 1
        elif votes == {True}:
            sym["indoor"] = True
            stat["indoor_true"] += 1
        elif votes == {False}:
            sym["indoor"] = False
            stat["indoor_false"] += 1
        else:                                  # no member carried indoor (undefined/no-room)
            stat["indoor_none"] += 1
        if is_oversize or is_mixed:            # DISTINCT F3-excluded (the two reasons overlap)
            stat["excluded_distinct"] += 1
        symbols.append(sym)

    stat.update({"n_symbols": len(symbols), "n_members_drawn": n,
                 "n_decor_filtered": n_decor, "n_oversize_single_filtered": n_oversize_single,
                 "fuse_gap_mm": fuse_gap})
    symbols_doc = {"meta": {**(gt_doc.get("meta") or {}), "symbols": True},
                   "elements": symbols, "openings": [], "glazing_lines": [], "wall_lines": []}
    return symbols_doc, stat


def _members_doc(gt_doc):
    """gt_doc with only the DRAWABLE furniture members (decor + single-object merged_blob
    removed). This is what the realistic SVG draws -- the reader then does the fusing itself,
    so its morphology is genuinely tested (we draw members, not pre-fused union rects)."""
    members = [ne for ne in (_as_footprint(e) for e in (gt_doc.get("elements", []) or []))
               if _member_class(ne)[0]]
    return {**gt_doc, "elements": members}


def score_gt(gt_doc, include_walls=False, tmp_dir=None, realistic=False,
             fuse_gap=FUSE_GAP_MM):
    """Synthesize gt_doc -> SVG -> run svg_plan_reader -> benchmark_reader card. Returns
    (card, pred, stat). The reader needs a file path, so the SVG is written to tmp_dir (a
    caller-owned scratch dir) or a fresh temp file.

    realistic=False (default) is the per-object v1.0 lane: draw every element, score vs the raw
    per-object GT. realistic=True is the plan-symbol lane: draw only drawable furniture members,
    let the reader fuse them, and score the fused clusters against the union symbols (see
    group_symbols). stat is the grouping breakdown in realistic mode, else None."""
    import tempfile
    if realistic:
        score_doc, stat = group_symbols(gt_doc, fuse_gap=fuse_gap)
        draw_doc = _members_doc(gt_doc)
    else:
        score_doc, stat, draw_doc = gt_doc, None, gt_doc
    svg = synth_svg(draw_doc, include_walls=include_walls)
    if tmp_dir is not None:
        p = os.path.join(tmp_dir, "synth.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(svg)
        pred = R.read_sheet(p, 1.0)
    else:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "synth.svg")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(svg)
            pred = R.read_sheet(p, 1.0)
    card = B.score_pair(score_doc, pred)
    return card, pred, stat


def score_corpus(gt_dir, out_dir, limit=None, include_walls=False, realistic=False,
                 fuse_gap=FUSE_GAP_MM):
    """Synthesize + read + score every gt.json in gt_dir. Writes cards.jsonl (streamed, so a
    mid-run death keeps finished work) + report.md, and returns (cards, skipped). One bad file
    costs ONE row, never the run (mirrors svg_plan_reader.run_baseline). realistic=True runs the
    plan-symbol lane (group_symbols) instead of the per-object lane."""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    cards, skipped = [], {"error": 0, "units": 0}
    gt_el_total = corpus_indoor_true = corpus_indoor_false = 0   # corpus-wide totals for the
    #                                     recall + representativeness lines in render_report
    grp = {"n_symbols": 0, "singleton": 0, "multi": 0, "union_oversize": 0, "mixed_indoor": 0,
           "excluded_distinct": 0,
           "n_members_drawn": 0, "n_decor_filtered": 0, "n_oversize_single_filtered": 0,
           "indoor_true": 0, "indoor_false": 0, "indoor_none": 0,
           "members_in_oversize": 0, "members_oversize_indoor_true": 0,
           "members_oversize_indoor_false": 0, "members_oversize_indoor_none": 0,
           # largest_symbol_* are MAXes, not sums -> tracked separately below (not in the += loop)
           "largest_symbol_members": 0, "largest_symbol_span_mm": 0.0} if realistic else None
    t0 = time.time()
    with open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8") as rows, \
            tempfile.TemporaryDirectory() as td:
        for k, gfp in enumerate(gt_files):
            base = os.path.basename(gfp)[:-len(".gt.json")]
            try:
                gt = json.load(open(gfp, encoding="utf-8"))
                if (gt.get("meta") or {}).get("units") != "mm":
                    skipped["units"] += 1
                    rows.write(json.dumps({"scene": base, "skipped": "units"}) + "\n")
                    continue
                gm = gt.get("meta") or {}
                gt_el_total += gm.get("n_elements", len(gt.get("elements", [])))
                corpus_indoor_true += gm.get("indoor_true", 0)
                corpus_indoor_false += gm.get("indoor_false", 0)
                card, _pred, stat = score_gt(gt, include_walls=include_walls, tmp_dir=td,
                                             realistic=realistic, fuse_gap=fuse_gap)
                cards.append(card)
                if realistic and stat:
                    for key in grp:
                        if key.startswith("largest_symbol_"):
                            grp[key] = max(grp[key], stat.get(key, 0))   # corpus max, not sum
                        else:
                            grp[key] += stat.get(key, 0)
                rows.write(json.dumps({"scene": base, "card": card}, ensure_ascii=False) + "\n")
            except Exception as e:              # one bad sheet costs one row, never the run
                skipped["error"] += 1
                rows.write(json.dumps({"scene": base, "skipped": "error",
                                       "error": f"{type(e).__name__}: {e}"}) + "\n")
            finally:
                rows.flush()
                if (k + 1) % 50 == 0:
                    print(f"  {k + 1}/{len(gt_files)}  scored={len(cards)} ({time.time()-t0:.0f}s)")
    report = render_report(cards, skipped, len(gt_files), time.time() - t0, include_walls,
                           gt_el_total=gt_el_total,
                           corpus_indoor=(corpus_indoor_true, corpus_indoor_false),
                           realistic=realistic, grp=grp, fuse_gap=fuse_gap)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return cards, skipped


def render_report(cards, skipped, n_total, secs, include_walls,
                  gt_el_total=None, corpus_indoor=None, realistic=False, grp=None,
                  fuse_gap=FUSE_GAP_MM):
    if not cards:
        return "# synth_plan_2d F3 lane\n\nno gt scored -- " + json.dumps(skipped)
    agg = B.aggregate(cards)
    det, f3 = agg["detection"], agg["F3_indoor"]
    # Because the reader is always-indoor, EVERY F3 wrong call is an OUTDOOR piece it missed, so
    # f3_wrong = matched OUTDOOR pairs. That lets us report the matched subset's outdoor fraction
    # next to the corpus outdoor rate -- the representativeness check the adversarial review asked
    # for (is the small detected subsample biased against outdoor? measure it, don't assume).
    f3_wrong = sum(len(c["F3_indoor"].get("wrong_ids") or []) for c in cards)
    matched_out_frac = (f3_wrong / f3["n"]) if f3["n"] else None
    # denominator + reference outdoor rate differ by lane: the plan-symbol lane scores SYMBOLS,
    # so 'of all GT' and 'corpus outdoor rate' must be symbol-level, not per-object, or the
    # representativeness check would compare a symbol subset against a per-object base rate.
    # per-object corpus outdoor rate (from the raw un-grouped GT meta) -- computed in BOTH lanes
    # so the realistic lane has a reference the representativeness check can actually FALSIFY: the
    # symbol-level rate is post-grouping/post-mixed-drop, so comparing matched-vs-symbol only
    # validates matching, blind to any bias the grouping itself introduced (adversarial review
    # 2026-07-08). The per-object rate is upstream of grouping -> a real cross-check.
    perobj_out_frac = None
    if corpus_indoor and (corpus_indoor[0] + corpus_indoor[1]):
        perobj_out_frac = corpus_indoor[1] / (corpus_indoor[0] + corpus_indoor[1])
    if realistic and grp:
        f3_denom, f3_denom_label = grp["n_symbols"], "plan symbols"
        sym_out = grp["indoor_true"] + grp["indoor_false"]
        corpus_out_frac = (grp["indoor_false"] / sym_out) if sym_out else None
    else:
        f3_denom, f3_denom_label = gt_el_total, "GT elements"
        corpus_out_frac = perobj_out_frac
    f3_of_denom = (f3["n"] / f3_denom) if f3_denom else None

    def pct(v):
        return "n/a" if v is None else f"{100.0 * v:.1f}%"

    verdict_counts = {}
    for c in cards:
        v = c["F3_indoor"]["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    lane = ("PLAN-SYMBOL lane (realistic: decor filtered, co-located objects grouped)"
            if realistic else "per-object lane (v1.0: every element drawn + scored)")
    L = [
        f"# synth_plan_2d -- REAL F3 reader score on Structured3D (pred != gt)", "",
        f"- LANE: {lane}",
        f"- synthesizer: {SYNTH_VERSION}  (walls drawn: {include_walls})",
        f"- reader: {R.READER_VERSION} (annotation-blind ink -> plan_cluster morphology; "
        f"NO indoor classifier -> the F3 number below is the ALWAYS-INDOOR BASELINE)",
        f"- scenes: {len(cards)} scored / {n_total} gt "
        f"(skipped {json.dumps(skipped)}); wall-clock {secs:.0f}s", "",
    ]
    if realistic and grp:
        drawn = grp["n_members_drawn"]
        m_ov = grp["members_in_oversize"]
        m_ov_frac = (m_ov / drawn) if drawn else 0.0
        L += [
            f"## realistic grouping (fuse gap {fuse_gap:.0f} mm, calibrated to the reader)",
            f"- members drawn (furniture-scale): {drawn}  "
            f"(filtered out: {grp['n_decor_filtered']} sub-150mm decor + "
            f"{grp['n_oversize_single_filtered']} single-object merged_blob -- a real plan draws "
            f"neither)",
            f"- plan symbols formed: {grp['n_symbols']}  "
            f"(singleton {grp['singleton']} + multi-object {grp['multi']}); "
            f"largest symbol {grp['largest_symbol_members']} members / "
            f"{grp['largest_symbol_span_mm']/1000.0:.1f} m span",
            f"- symbols excluded from F3 (DISTINCT, the two reasons overlap): "
            f"{grp['excluded_distinct']}  = {grp['union_oversize']} union-oversize + "
            f"{grp['mixed_indoor']} mixed-indoor - "
            f"{grp['union_oversize'] + grp['mixed_indoor'] - grp['excluded_distinct']} counted in both",
            f"- CROSS-ROOM CHAINING LOSS (the honest magnitude): {m_ov} of {drawn} drawn members "
            f"({pct(m_ov_frac)}) collapse into the {grp['union_oversize']} union-oversize regions "
            f"-- these are NOT plan symbols but DENSE multi-object areas the furniture-only reader "
            f"cannot resolve without walls (single-linkage chains across un-drawn walls). Lost "
            f"members carry indoor True={grp['members_oversize_indoor_true']} "
            f"False={grp['members_oversize_indoor_false']} "
            f"no-key={grp['members_oversize_indoor_none']} -> that outdoor loss is why the symbol "
            f"vs per-object outdoor rates are cross-checked below.",
            f"- symbol indoor split: True={grp['indoor_true']} False={grp['indoor_false']} "
            f"no-key={grp['indoor_none']}", "",
        ]
    L += [
        f"## detection -- {'over PLAN SYMBOLS' if realistic else 'LOW RECALL BY EXPECTATION'}",
        f"- GT {det['n_gt']} vs pred {det['n_pred']} -> matched {det['matched']}: "
        f"recall {pct(det['recall'])}, precision {pct(det['precision'])}",
        (f"- detection is the reader FUSING drawn members back into the grouped symbol: recall "
         f"measures how well the {fuse_gap:.0f}mm grouping proxy matches the reader's real "
         f"closing, NOT a capability jump. It is also FLATTERED by region-lumping -- the "
         f"{pct((grp['members_in_oversize'] / grp['n_members_drawn']) if grp['n_members_drawn'] else 0)} "
         f"of members that chain into union-oversize regions cost only ~{grp['union_oversize']} "
         f"misses, not their member count; the cross-room-chaining loss above is the honest "
         f"coverage. (soundness note, not a pass.)" if realistic else
         f"- recall is low because ~54-63% of GT is sub-150mm decor the reader screens as thin, "
         f"plus furniture-vs-furniture merges under CLOSE_MM=40 -> F3 is scored on the DETECTED "
         f"SUBSET, not all GT (see honesty notes; NOT an easy round-trip)."), "",
        f"## F3 indoor (THE deliverable -- first pred!=gt indoor score on any corpus)",
        f"- accuracy {pct(f3['accuracy'])} on {f3['n']} matched pairs carrying GT indoor"
        + (f" ({pct(f3_of_denom)} of {f3_denom} {f3_denom_label})" if f3_of_denom is not None else ""),
        f"- {f3_wrong} wrong calls = OUTDOOR (balcony/garden) pieces the always-indoor reader "
        f"misclassifies -- these wrong_ids are exactly where an indoor-inference upgrade must win",
        f"- REPRESENTATIVENESS: matched-subset outdoor fraction {pct(matched_out_frac)}"
        + (f" vs {'symbol' if realistic else 'corpus'} outdoor rate {pct(corpus_out_frac)}"
           if corpus_out_frac is not None else "")
        + (f" vs PER-OBJECT (pre-grouping) outdoor rate {pct(perobj_out_frac)}"
           if realistic and perobj_out_frac is not None else "")
        + (" -- the matched-vs-symbol pair validates MATCHING only (both post-grouping); the "
           "per-object rate is the non-blind cross-check. They stay close, but boundary-straddling "
           "outdoor furniture (the mixed-indoor groups) is excluded UPSTREAM and NOT covered here "
           "-- a future indoor-classifier must be judged on those separately, at member level."
           if realistic else
           " -- close => the baseline is NOT optimistically biased against outdoor (measured)."),
        f"- per-scene F3 verdicts: {verdict_counts}", "",
        "## honesty notes",
        "- F3 accuracy == indoor fraction among matched pairs BY CONSTRUCTION (the reader is "
        "silent=indoor). The number is the BASELINE TO BEAT; the win is the wired pred!=gt loop.",
        "- annotation-blind: the indoor label is never drawn (test_synth_plan_2d pins byte-"
        "identity across an indoor flip). No answer key leaks into the reader's input.",
    ]
    if realistic:
        L += [
            "- PLAN-SYMBOL lane: the scoreable UNIT is a plan furniture symbol (co-located 3D "
            "sub-objects fused as a draughtsperson would draw them), NOT the raw 3D object. This "
            "is a bigger, plan-faithful slice, NOT a reader upgrade -- accuracy is still the "
            "always-indoor baseline; the deliverable is slice size + a larger OUTDOOR sample.",
            "- grouping + decor filter are GEOMETRY-ONLY and reuse the reader's own size screen; "
            "the indoor consensus is computed on the GT side and never drawn (blindness holds).",
            "- KNOWN LIMIT (measured, not hidden): pure single-linkage with no wall barrier chains "
            "dense furniture across un-drawn walls -> the union-oversize regions above are NOT "
            "clean symbols but unresolvable dense areas (~1/4 of drawn members). A diameter cap was "
            "tested + REJECTED (does not recover slice: F3 n flat over caps; only trades recall for "
            "cosmetics). The real fix is a wall-aware reader (oracle-walls lane), a separate slice; "
            "here the loss is surfaced (cross-room-chaining line) and symbol recall read as "
            "flattered by lumping.",
            "- mixed-indoor groups get NO label (counted, distinct-excluded above), never a guessed "
            "side; union-oversize symbols are kept in GT and simply miss (honest detection loss).",
        ]
    else:
        L += [
            "- DETECTION-LIMITED SAMPLE: F3 n is ~a tenth of GT. plan_cluster screens sub-150mm "
            "decor and MERGES furniture drawn within CLOSE_MM=40 (bed+flush nightstand -> one "
            "blob matching neither, both leave F3). test_synth_plan_2d pins this merge limit. Run "
            "--realistic to score the plan-symbol lane that recovers the fused furniture.",
            "- furniture-only by default; --walls adds structure but ALSO merges wall-adjacent "
            "furniture -- quote the furniture-only lane as the F3 headline.",
        ]
    L += ["", f"synthesizer: {SYNTH_VERSION}"]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 2 and argv[1] == "--score":
        if len(argv) < 4:
            raise SystemExit("usage: synth_plan_2d.py --score <gt-dir> <out-dir> "
                             "[limit N] [--walls] [--realistic] [--fuse-gap MM]")
        walls = "--walls" in argv
        realistic = "--realistic" in argv
        fuse_gap = FUSE_GAP_MM
        rest = [a for a in argv[4:] if a not in ("--walls", "--realistic")]
        limit = None
        i = 0
        while i < len(rest):
            if rest[i] == "limit" and i + 1 < len(rest) and rest[i + 1].isdigit():
                limit = int(rest[i + 1]); i += 2
            elif rest[i] == "--fuse-gap" and i + 1 < len(rest):
                fuse_gap = float(rest[i + 1]); i += 2
            else:
                i += 1
        score_corpus(argv[2], argv[3], limit=limit, include_walls=walls,
                     realistic=realistic, fuse_gap=fuse_gap)
    elif len(argv) >= 3:
        walls = "--walls" in argv
        gt = json.load(open(argv[1], encoding="utf-8"))
        svg = synth_svg(gt, include_walls=walls)
        with open(argv[2], "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {argv[2]} ({len(gt.get('elements', []))} elements, walls={walls})")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
