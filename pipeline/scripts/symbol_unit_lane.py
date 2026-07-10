"""
symbol_unit_lane.py -- GT-UNIT decomposition lane: what is the remaining recall gap MADE OF?

WHY: wall_aware_lane (2026-07-10) measured cross-wall closing-fusion at +2.6pp detection
recall (10.7% -> 13.3%, ORACLE-WALLS ceiling) and attributed the remaining 86.7% per-object
recall gap to "within-room fusion + sub-object granularity" WITHOUT splitting the two. The
split decides the next lane: if the gap is mostly GRANULARITY (the reader correctly emits one
cluster per plan-symbol, but GT counts each 3D sub-object -- duvet, pillow, chair-under-table
-- as its own row), the fix is a SCORING unit, not a reader change; if it is mostly REAL
within-room fusion (one cluster covering several distinct plan-symbols), the fix is a
symbol-level splitter. This lane measures the split, member-exact.

MECHANISM: the SAME preds as the committed wall-aware run -- the unedited reader (BEFORE)
and the wall-barrier re-cluster (AFTER) -- are re-derived deterministically (the run dir
stores score cards, not pred boxes) and CROSS-CHECKED per scene against the committed
cards.jsonl (--pin-cards): n_gt/n_pred/matched/missed_ids must be equal, else the row is
counted as a pin mismatch and reported loudly. A scene that RAISES -- including this
lane's own loud-drift asserts (grouping mirror, wall-region mirror, bucket-leak) -- is
counted as drift_assert/error AND as an unscored pinned scene: the ALL-GREEN flag
requires zero mismatches, zero absents, zero unscored-pinned and zero raises, so the pin
denominator cannot shrink silently (adversarial review 2026-07-10, the flattering-scorer
hole's 5th per-lane recurrence -- this time a blanket except converting drift alarms into
quiet skips). No new reader mechanism runs; the F2/F3 enrichment stack is skipped
entirely (detection-only re-score).

Each side's pred is then scored against a SECOND GT unit: the PLAN-SYMBOL
(synth_plan_2d.group_symbols -- v1.1's calibrated 90mm single-linkage proxy, imported and
pinned, never re-implemented). Every sanitized GT element lands in EXACTLY ONE bucket
(the sum equals n_gt per scene, asserted):

  matched                per-object match (IoU >= 0.5, one-to-one) -- the committed headline
  decor_micro            <150mm on BOTH axes (pillows, lamps): the reader's own screen
                         excludes it and no kept pred can plausibly reach IoU 0.5
  decor_thin_elongated   <150mm on exactly ONE axis (curtains, rails, wardrobe bands):
                         screened out of the SYMBOL unit by the reader's own thin rule,
                         but long enough that a kept pred CAN in principle match it --
                         matched thin elements are counted per side (matched_thin) so the
                         screen's cost is measured, never asserted
  oversize_single        single object >3.6m on both axes (reader drops as merged_blob)
  granularity            UNMATCHED member of a MATCHED symbol -- the reader DID emit a
                         cluster for this symbol; the per-object unit alone calls it a miss
  union_oversize_region  member of an UNMATCHED symbol whose union exceeds 3.6m both axes
                         (dense transitive chain -- the grouping proxy's own known limit,
                         measured in v1.1). The reader usually drops such blobs, but a
                         near-the-bar union CAN still match a one-axis-oversize kept pred
                         -- how often is MEASURED per side (oversize_sym_matched), never
                         asserted away; a matched oversize symbol's members count as
                         granularity because the reader genuinely emitted that cluster
  fused_cross_symbol     member of an unmatched normal symbol majority-covered by a kept
                         pred that majority-covers >=2 symbols -- REAL fusion at symbol level
  geometric_drift        member of an unmatched symbol majority-covered by pred(s) covering
                         only this symbol (bloat/offset/one-to-one assignment loss)
  touched_only           member of an unmatched symbol some pred intersects but none covers
  dropped_no_pred        member of an unmatched symbol no kept pred intersects at all
                         (its ink died in a dropped blob/thin/speckle component)

"majority-covered" = intersection / symbol area >= COVER_FRAC (0.5; fused counts at
0.25/0.75 are printed as a sensitivity line so the bar cannot silently shape the story).

SECONDARY UNIT (AFTER side only, ORACLE-WALLS -- disclosed): WALL-PARTITIONED grouping --
same members, same fuse rule, but two members may only union when their footprint centres
lie in the same wall-partitioned region (the barrier's own region labelling; a centre ON
the dilated barrier is a wildcard). The delta vs the plain grouping measures how much of
union_oversize_region is CROSS-WALL chaining (v1.1's known mega-chain limit) vs genuinely
dense in-room mass. This variant consumes gt['wall_lines'] and is quoted only as ceiling.

WHAT THIS LANE IS NOT: not a new recall claim. The per-object numbers (10.7% / 13.3%)
REMAIN the committed headlines; symbol-level recall here is a decomposition instrument,
and (v1.1 doctrine) symbol-level recall is FLATTERED by region-lumping -- member-level
coverage and the bucket table are the honest reading. The matched-symbol IoU HISTOGRAM
(0.1 bins up from the 0.5 bar) is aggregated and printed per side so a barely-0.5 bloated
match cannot quietly inflate `granularity` -- the <0.6 band bounds that inflation.

TIER: BEFORE side = blind reader on the closed-loop oriented synth (same as committed).
AFTER side + wall-partitioned grouping = ORACLE-WALLS (gt wall geometry; ceiling only).
The grouping itself consumes GT footprints on the SCORING side only -- it never touches
the pred (same doctrine as synth_plan_2d v1.1's realistic lane).

    python symbol_unit_lane.py --score <gt-dir> <out-dir> [limit N] [--pin-cards <run-dir>]
"""
import glob
import json
import os
import sys
import time

import numpy as np
import scipy.ndimage as ndi

import benchmark_reader as B
import f2_facing_lane as F2L
import plan_cluster as PC
import svg_plan_reader as R
import wall_aware_lane as W
from synth_plan_2d import FUSE_GAP_MM, _as_footprint, _fuses, _member_class, group_symbols

LANE_VERSION = "symbol_unit_lane v1.0"

COVER_FRAC = 0.5          # majority-coverage bar for fused/drift classification (disclosed)
COVER_FRAC_SENS = (0.25, 0.75)   # sensitivity bars printed beside the headline bucket

BUCKETS = ("matched", "decor_micro", "decor_thin_elongated", "oversize_single",
           "granularity", "union_oversize_region", "fused_cross_symbol",
           "geometric_drift", "touched_only", "dropped_no_pred")

THIN_MM = 150.0           # the reader's own thin bar (plan_cluster._screen_component)


# ---- plan-symbol membership (mirrors group_symbols' loop; PINNED against its output) ------
def symbol_membership(clean_elements, fuse_gap=FUSE_GAP_MM, allowed=None):
    """The v1.1 grouping WITH the member->symbol assignment group_symbols does not expose.
    Returns (symbols, member_of, decor_idx, oversize_idx):
      symbols      [{id,x,y,w,d,n_members,member_idx:[...]}] in group_symbols' order
      member_of    {clean_index -> symbol position}
      decor_idx    set of clean indices screened thin (<150mm an axis)
      oversize_idx set of clean indices screened as single-object merged_blob
    `allowed(i, j)` (indices into the MEMBER list) optionally vetoes a union -- the
    wall-partitioned variant. With allowed=None the emitted symbols are asserted equal to
    group_symbols' own output by the caller (test + per-scene pin), so this mirror cannot
    drift silently -- same doctrine as wall_aware_lane mirroring cluster_segments' loop."""
    fps = [_as_footprint(e) for e in clean_elements]
    members, member_clean_idx = [], []
    decor_idx, oversize_idx = set(), set()
    for i, e in enumerate(fps):
        keep, reason = _member_class(e)
        if keep:
            members.append(e)
            member_clean_idx.append(i)
        elif reason == "thin":
            decor_idx.add(i)
        else:
            oversize_idx.add(i)

    n = len(members)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if allowed is not None and not allowed(i, j):
                continue
            if _fuses(members[i], members[j], fuse_gap):
                parent[find(i)] = find(j)

    groups, order = {}, []
    for i in range(n):
        r = find(i)
        if r not in groups:
            groups[r] = []
            order.append(r)
        groups[r].append(i)

    symbols, member_of = [], {}
    for gi, r in enumerate(order):
        idx = groups[r]
        ms = [members[k] for k in idx]
        x0 = min(float(m["x"]) for m in ms)
        y0 = min(float(m["y"]) for m in ms)
        x1 = max(float(m["x"]) + float(m["w"]) for m in ms)
        y1 = max(float(m["y"]) + float(m["d"]) for m in ms)
        symbols.append({"id": f"s{gi:04d}", "x": round(x0, 1), "y": round(y0, 1),
                        "w": round(x1 - x0, 1), "d": round(y1 - y0, 1),
                        "n_members": len(ms),
                        "member_idx": [member_clean_idx[k] for k in idx]})
        for k in idx:
            member_of[member_clean_idx[k]] = gi
    return symbols, member_of, decor_idx, oversize_idx


def assert_matches_group_symbols(clean_elements, symbols, meta=None):
    """Loud drift pin: the mirrored membership must emit group_symbols' exact geometry."""
    ref = group_symbols({"meta": meta or {}, "elements": clean_elements})[0]["elements"]
    got = [{"id": s["id"], "x": s["x"], "y": s["y"], "w": s["w"], "d": s["d"],
            "n_members": s["n_members"]} for s in symbols]
    want = [{k: s[k] for k in ("id", "x", "y", "w", "d", "n_members")} for s in ref]
    if got != want:
        raise AssertionError(
            f"symbol_membership drifted from group_symbols: {len(got)} vs {len(want)} symbols")


# ---- wall-region partition (AFTER-side secondary unit; mirrors wall_barrier_elements) ----
def wall_regions(segs_mm, wall_lines):
    """(regions_label_array, zone, res, n_regions) with the EXACT canvas/raster/dilation
    wall_barrier_elements uses (constants imported from that lane; zone/res mirrored
    line-for-line). The caller pins n_regions against the wall_aware stats of the same
    scene, so this mirror cannot drift silently either. None when no usable walls."""
    if not segs_mm:
        return None, None, None, 0
    wsegs = [[(float(w["x1"]), float(w["y1"])), (float(w["x2"]), float(w["y2"]))]
             for w in (wall_lines or [])]
    wsegs = [s for s in wsegs if s[0] != s[1]]
    if not wsegs:
        return None, None, None, 0
    xs = [p[0] for seg in segs_mm for p in seg]
    ys = [p[1] for seg in segs_mm for p in seg]
    zone = (min(xs) - R.ZONE_PAD_MM, min(ys) - R.ZONE_PAD_MM,
            max(xs) + R.ZONE_PAD_MM, max(ys) + R.ZONE_PAD_MM)
    extent = max(zone[2] - zone[0], zone[3] - zone[1])
    res = max(R.BASE_RES_MM, extent / R.MAX_RASTER_PX)
    Wc = int((zone[2] - zone[0]) / res)
    Hc = int((zone[3] - zone[1]) / res)
    barrier = PC._rasterize(wsegs, zone, Wc, Hc)
    st = ndi.generate_binary_structure(2, 2)
    barrier = ndi.binary_dilation(barrier, structure=st, iterations=W.BARRIER_DILATE_PX)
    regions, n_regions = ndi.label(~barrier, structure=st)
    return regions, zone, res, int(n_regions)


def region_of_centre(fp, regions, zone, res):
    """Region id under a footprint's centre pixel; 0 = on the dilated barrier (wildcard).
    Off-canvas centres clip to the border pixel (padded zone makes that near-impossible)."""
    X0, _, _, Y1 = zone
    cx = float(fp["x"]) + float(fp["w"]) / 2.0
    cy = float(fp["y"]) + float(fp["d"]) / 2.0
    col = min(max(int((cx - X0) / res), 0), regions.shape[1] - 1)
    row = min(max(int((Y1 - cy) / res), 0), regions.shape[0] - 1)
    return int(regions[row, col])


# ---- the decomposition ---------------------------------------------------------------------
def _inter_area(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    w = min(ax1, bx1) - max(ax0, bx0)
    h = min(ay1, by1) - max(ay0, by0)
    return max(w, 0.0) * max(h, 0.0)


def _fp(e):
    x, y, w, d = float(e["x"]), float(e["y"]), float(e["w"]), float(e["d"])
    return (x, y, x + w, y + d)


def decompose(clean, pred_el, symbols, member_of, decor_idx, oversize_idx):
    """One side's full accounting. Returns {perobj, matched_thin, perobj_missed_ids,
    symbol, buckets, fused_sens, sym_iou_hist, pred_purity}.
    buckets: element counts summing EXACTLY to len(clean) (asserted)."""
    pairs, missed, phantom = B.match_elements(clean, pred_el)
    perobj = B.score_detection(pairs, missed, phantom)
    matched_gt = {id(g) for g, _p, _v in pairs}         # identity: clean rows are unique objs

    sym_el = [{k: s[k] for k in ("id", "x", "y", "w", "d")} for s in symbols]
    spairs, smissed, sphantom = B.match_elements(sym_el, pred_el)
    sdet = B.score_detection(spairs, smissed, sphantom)
    matched_sym = {s["id"] for s, _p, _v in spairs}
    sym_ious = sorted(v for _s, _p, v in spairs)

    # coverage of each symbol by each kept pred (for fused/drift/touched classification)
    pred_fps = [_fp(p) for p in pred_el]
    sym_fps = [_fp(s) for s in sym_el]
    sym_area = [max((f[2] - f[0]) * (f[3] - f[1]), 1e-9) for f in sym_fps]
    cover = np.zeros((len(sym_el), len(pred_el)))       # inter / symbol area
    for si, sf in enumerate(sym_fps):
        for pi, pf in enumerate(pred_fps):
            ia = _inter_area(sf, pf)
            if ia > 0:
                cover[si, pi] = ia / sym_area[si]
    n_cov_per_pred = {}                                 # bar -> per-pred covered-symbol count
    for bar in (COVER_FRAC,) + COVER_FRAC_SENS:
        n_cov_per_pred[bar] = (cover >= bar).sum(axis=0) if len(pred_el) else np.zeros(0)

    def classify_symbol(si, bar):
        """matched / fused / drift / touched / dropped for one symbol at one bar."""
        s = symbols[si]
        if s["id"] in matched_sym:
            return "matched"
        if not PC._screen_component(s["w"], s["d"])[0]:
            return "union_oversize"
        if len(pred_el) == 0:
            return "dropped"
        covering = np.where(cover[si] >= bar)[0]
        if any(n_cov_per_pred[bar][pi] >= 2 for pi in covering):
            return "fused"
        if len(covering):
            return "drift"
        if cover[si].max() > 0:
            return "touched"
        return "dropped"

    sym_class = [classify_symbol(si, COVER_FRAC) for si in range(len(symbols))]
    buckets = {b: 0 for b in BUCKETS}
    matched_thin = 0
    for i, e in enumerate(clean):
        if id(e) in matched_gt:
            buckets["matched"] += 1
            if i in decor_idx:
                matched_thin += 1              # a thin GT element a kept pred DID reach --
            continue                           # measured, so the screen's cost is never asserted
        if i in decor_idx:
            f = _as_footprint(e)
            micro = float(f["w"]) < THIN_MM and float(f["d"]) < THIN_MM
            buckets["decor_micro" if micro else "decor_thin_elongated"] += 1
        elif i in oversize_idx:
            buckets["oversize_single"] += 1
        else:
            c = sym_class[member_of[i]]
            buckets[{"matched": "granularity", "union_oversize": "union_oversize_region",
                     "fused": "fused_cross_symbol", "drift": "geometric_drift",
                     "touched": "touched_only", "dropped": "dropped_no_pred"}[c]] += 1
    total = sum(buckets.values())
    if total != len(clean):
        raise AssertionError(f"bucket leak: {total} != n_gt {len(clean)}")

    fused_sens = {}
    for bar in COVER_FRAC_SENS:
        cnt = 0
        for i in range(len(clean)):
            if id(clean[i]) in matched_gt or i in decor_idx or i in oversize_idx:
                continue
            if classify_symbol(member_of[i], bar) == "fused":
                cnt += 1
        fused_sens[bar] = cnt

    # matched-symbol IoU histogram, 0.1 bins up from the 0.5 match bar: the <0.6 band
    # bounds how much `granularity` a barely-matched bloated cluster can have credited
    iou_hist = [0, 0, 0, 0, 0]
    for v in sym_ious:
        iou_hist[min(int((v - 0.5) / 0.1), 4)] += 1
    oversize_sym_matched = sum(1 for s in symbols if s["id"] in matched_sym
                               and not PC._screen_component(s["w"], s["d"])[0])
    purity = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for pi in range(len(pred_el)):
        k = int(n_cov_per_pred[COVER_FRAC][pi])
        purity["3+" if k >= 3 else str(k)] += 1
    members_total = len(clean) - len(decor_idx) - len(oversize_idx)
    members_in_matched = sum(s["n_members"] for s in symbols if s["id"] in matched_sym)
    return {"perobj": {k: perobj[k] for k in ("n_gt", "n_pred", "matched")},
            "matched_thin": matched_thin,
            "perobj_missed_ids": sorted(perobj["missed_ids"], key=str),
            "symbol": {"n_sym": sdet["n_gt"], "n_pred": sdet["n_pred"],
                       "matched": sdet["matched"],
                       "oversize_sym_matched": oversize_sym_matched,
                       "members_total": members_total,
                       "members_in_matched_sym": members_in_matched},
            "buckets": buckets, "fused_sens": {str(k): v for k, v in fused_sens.items()},
            "sym_iou_hist": iou_hist,
            "pred_purity": purity}


# ---- one scene ----------------------------------------------------------------------------
def score_scene(gt_doc, tmp_dir):
    """Preds re-derived EXACTLY as the wall-aware run (same oriented synth, same reader,
    same barrier), then detection-only decomposition on both sides + the wall-partitioned
    secondary unit on the after side."""
    svg, _ = F2L.oriented_svg(gt_doc)
    p = os.path.join(tmp_dir, "oriented.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    pred_b = R.read_sheet(p, 1.0)
    ink = R.read_ink(p)
    segs, csegs = ink["segs"], ink["curve_segs"]
    pred_a, wstats = W.wall_aware_pred(pred_b, segs, csegs, gt_doc.get("wall_lines"))

    clean, malformed = B.sanitize_elements(gt_doc.get("elements", []))
    pred_b_el, _ = B.sanitize_elements(pred_b["elements"])
    pred_a_el, _ = B.sanitize_elements(pred_a["elements"])

    symbols, member_of, decor_idx, oversize_idx = symbol_membership(clean)
    assert_matches_group_symbols(clean, symbols, meta=gt_doc.get("meta"))

    row = {"malformed_gt": len(malformed),
           "before": decompose(clean, pred_b_el, symbols, member_of, decor_idx, oversize_idx),
           "after": decompose(clean, pred_a_el, symbols, member_of, decor_idx, oversize_idx)}

    regions, zone, res, n_regions = wall_regions(segs, gt_doc.get("wall_lines"))
    if regions is not None:
        if n_regions != wstats.get("n_regions"):
            raise AssertionError(f"wall_regions drifted from wall_barrier_elements: "
                                 f"{n_regions} != {wstats.get('n_regions')}")
        fps = [_as_footprint(e) for e in clean]
        reg = {}                                        # member index (clean idx) -> region

        def allowed_factory(member_clean_idx):
            def allowed(i, j):
                a, b = reg[member_clean_idx[i]], reg[member_clean_idx[j]]
                return a == 0 or b == 0 or a == b
            return allowed

        # membership needs the member list first to map indices; compute regions for every
        # clean element (cheap) and veto on the two members' regions
        for i, f in enumerate(fps):
            reg[i] = region_of_centre(f, regions, zone, res)
        member_clean_idx = sorted(member_of)            # clean indices that are members
        idx_map = member_clean_idx                      # member position -> clean index
        symbols_w, member_of_w, decor_w, oversize_w = symbol_membership(
            clean, allowed=allowed_factory(idx_map))
        if (decor_w, oversize_w) != (decor_idx, oversize_idx):
            raise AssertionError("wall-partitioned variant changed the member screen")
        row["after_wallgroup"] = decompose(clean, pred_a_el, symbols_w, member_of_w,
                                           decor_w, oversize_w)
        row["n_regions"] = n_regions
    return row


# ---- pin against the committed run ---------------------------------------------------------
def load_pin_cards(run_dir):
    """cards.jsonl -> {scene: (det_before, det_after)} with missed_ids kept for the strong
    per-scene equality pin. Skipped rows in the committed run are absent (they re-skip here)."""
    pins = {}
    with open(os.path.join(run_dir, "cards.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if "card_before" in r:
                pins[r["scene"]] = (r["card_before"]["detection"],
                                    r["card_after"]["detection"])
    return pins


def check_pin(row, pin):
    """True when this scene's re-derived per-object detection equals the committed card on
    BOTH sides: n_gt, n_pred, matched, and the exact missed-id set."""
    for side, det in (("before", pin[0]), ("after", pin[1])):
        d = row[side]["perobj"]
        if (d["n_gt"], d["n_pred"], d["matched"]) != (det["n_gt"], det["n_pred"],
                                                      det["matched"]):
            return False
        if sorted(row[side]["perobj_missed_ids"], key=str) != sorted(det["missed_ids"],
                                                                     key=str):
            return False
    return True


# ---- corpus run ----------------------------------------------------------------------------
def score_corpus(gt_dir, out_dir, limit=None, pin_dir=None):
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    pins = load_pin_cards(pin_dir) if pin_dir else None
    rows, skipped = [], {"error": 0, "drift_assert": 0, "units": 0}
    pin_ok, pin_bad, pin_expected, pin_absent, pin_bad_scenes = 0, 0, 0, 0, []
    t0 = time.time()
    with open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8") as out, \
            tempfile.TemporaryDirectory() as td:
        for k, gfp in enumerate(gt_files):
            base = os.path.basename(gfp)[:-len(".gt.json")]
            if pins is not None and base in pins:
                pin_expected += 1              # attempted AND pinned: must end ok or bad,
            try:                               # else it shows up as unscored (never silent)
                gt = json.load(open(gfp, encoding="utf-8"))
                if (gt.get("meta") or {}).get("units") != "mm":
                    skipped["units"] += 1
                    out.write(json.dumps({"scene": base, "skipped": "units"}) + "\n")
                    continue
                row = {"scene": base, **score_scene(gt, td)}
                if pins is not None:
                    if base not in pins:
                        pin_absent += 1
                    elif check_pin(row, pins[base]):
                        pin_ok += 1
                    else:
                        pin_bad += 1
                        pin_bad_scenes.append(base)
                for side in ("before", "after", "after_wallgroup"):
                    row.get(side, {}).pop("perobj_missed_ids", None)  # pin-checked, then shed
                rows.append(row)
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            except AssertionError as e:
                # the lane's OWN loud-drift alarms (grouping mirror, wall-region mirror,
                # bucket leak): one scene costs one row, but the raise is counted in its
                # own bucket and blocks the ALL-GREEN flag -- a drift alarm must never
                # degrade into a quiet skip (adversarial review 2026-07-10)
                skipped["drift_assert"] += 1
                out.write(json.dumps({"scene": base, "skipped": "drift_assert",
                                      "error": str(e)}) + "\n")
            except Exception as e:
                skipped["error"] += 1
                out.write(json.dumps({"scene": base, "skipped": "error",
                                      "error": f"{type(e).__name__}: {e}"}) + "\n")
            finally:
                out.flush()
                if (k + 1) % 100 == 0:
                    print(f"  {k + 1}/{len(gt_files)}  scored={len(rows)}  "
                          f"({time.time() - t0:.0f}s)", flush=True)
    pin = None if pins is None else {"ok": pin_ok, "bad": pin_bad, "absent": pin_absent,
                                     "unscored_pinned": pin_expected - pin_ok - pin_bad,
                                     "bad_scenes": pin_bad_scenes[:20]}
    report = render_report(rows, skipped, len(gt_files), time.time() - t0, pin=pin)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return rows, skipped


def _pct(a, b):
    return f"{100.0 * a / b:.1f}%" if b else "n/a"


def render_report(rows, skipped, n_total, secs, pin=None):
    if not rows:
        return "# symbol_unit_lane\n\nno gt scored -- " + json.dumps(skipped)

    def agg_side(side):
        A = {"perobj": {"n_gt": 0, "n_pred": 0, "matched": 0}, "matched_thin": 0,
             "symbol": {"n_sym": 0, "n_pred": 0, "matched": 0, "oversize_sym_matched": 0,
                        "members_total": 0, "members_in_matched_sym": 0},
             "buckets": {b: 0 for b in BUCKETS}, "fused_sens": {}, "purity": {},
             "iou_hist": [0, 0, 0, 0, 0]}
        for r in rows:
            s = r.get(side)
            if not s:
                continue
            A["matched_thin"] += s.get("matched_thin", 0)
            for k in A["perobj"]:
                A["perobj"][k] += s["perobj"][k]
            for k in A["symbol"]:
                A["symbol"][k] += s["symbol"][k]
            for k in BUCKETS:
                A["buckets"][k] += s["buckets"][k]
            for i, v in enumerate(s.get("sym_iou_hist") or []):
                A["iou_hist"][i] += v
            for k, v in s["fused_sens"].items():
                A["fused_sens"][k] = A["fused_sens"].get(k, 0) + v
            for k, v in s["pred_purity"].items():
                A["purity"][k] = A["purity"].get(k, 0) + v
        return A

    b, a = agg_side("before"), agg_side("after")
    wg = agg_side("after_wallgroup")
    n_wg = sum(1 for r in rows if r.get("after_wallgroup"))

    def bucket_table(A):
        n_gt = A["perobj"]["n_gt"]
        gap = n_gt - A["buckets"]["matched"]
        L = ["| bucket | elements | % of GT | % of gap |", "|---|---|---|---|"]
        for k in BUCKETS:
            v = A["buckets"][k]
            of_gap = "" if k == "matched" else _pct(v, gap)
            L.append(f"| {k} | {v} | {_pct(v, n_gt)} | {of_gap} |")
        L.append(f"| TOTAL | {sum(A['buckets'].values())} | 100% | gap={gap} |")
        return L

    def sym_line(A):
        s = A["symbol"]
        return (f"symbols {s['n_sym']} matched {s['matched']} ({_pct(s['matched'], s['n_sym'])}); "
                f"symbol-precision {_pct(s['matched'], s['n_pred'])}; member coverage "
                f"{s['members_in_matched_sym']}/{s['members_total']} "
                f"({_pct(s['members_in_matched_sym'], s['members_total'])}); "
                f"matched-though-union-oversize {s['oversize_sym_matched']}")

    def iou_line(A):
        h = A["iou_hist"]
        n = sum(h)
        return (f"- matched-symbol IoU histogram [.5-.6/.6-.7/.7-.8/.8-.9/.9-1.0]: "
                f"{h} -- barely-matched (<0.6) {h[0]}/{n} ({_pct(h[0], n)}); granularity "
                f"credited through those symbols is bounded by that band")

    L = [
        "# symbol_unit_lane -- what the remaining recall gap is MADE OF", "",
        "**GT-UNIT decomposition.** Per-object recall headlines are UNCHANGED by "
        "construction (this lane only re-buckets; this run reproduces before "
        f"{_pct(b['perobj']['matched'], b['perobj']['n_gt'])} / after "
        f"{_pct(a['perobj']['matched'], a['perobj']['n_gt'])} -- the pin line verifies "
        "equality with the committed run); every GT element is re-bucketed against the "
        f"plan-symbol unit (synth_plan_2d.group_symbols, fuse gap {FUSE_GAP_MM:.0f}mm, "
        "pinned mirror). AFTER side + wall-partitioned grouping = ORACLE-WALLS "
        "(ceiling, disclosed).", "",
        f"- {LANE_VERSION}; reader {R.READER_VERSION} (UNEDITED); wall lane {W.LANE_VERSION}; "
        f"cover bar {COVER_FRAC} (sensitivity {COVER_FRAC_SENS})",
        f"- scenes: {len(rows)} scored / {n_total} (skipped {json.dumps(skipped)}); "
        f"wall-clock {secs:.0f}s",
    ]
    if pin is not None:
        raises = skipped.get("error", 0) + skipped.get("drift_assert", 0)
        green = (not pin["bad"] and not pin["absent"]
                 and not pin.get("unscored_pinned") and not raises)
        flag = ("**ALL GREEN**" if green else
                "**PIN NOT CLEAN -- do not quote until resolved**")
        L.append(f"- pred-reproduction pin vs committed run: {pin['ok']} equal / "
                 f"{pin['bad']} mismatched / {pin['absent']} absent / "
                 f"{pin.get('unscored_pinned', 0)} pinned-but-unscored (raised or "
                 f"skipped) -- {flag}"
                 + (f"; first bad: {pin['bad_scenes']}" if pin["bad_scenes"] else ""))
        if skipped.get("drift_assert"):
            L.append(f"- **DRIFT ASSERT FIRED on {skipped['drift_assert']} scene(s)** -- "
                     "a mirrored code path diverged from its upstream; fix before "
                     "trusting ANY number in this report")
    else:
        L.append("- pred-reproduction pin: NOT RUN (--pin-cards not given) -- per-object "
                 "counts below must equal the committed run before quoting")
    L += ["", "## BEFORE (unedited reader, blind synth)",
          f"- per-object: matched {b['perobj']['matched']}/{b['perobj']['n_gt']} "
          f"({_pct(b['perobj']['matched'], b['perobj']['n_gt'])}), "
          f"n_pred {b['perobj']['n_pred']}; matched-despite-thin-screen "
          f"{b['matched_thin']}",
          f"- symbol unit: {sym_line(b)}", iou_line(b), ""]
    L += bucket_table(b)
    L += ["", "## AFTER (wall barrier, ORACLE-WALLS)",
          f"- per-object: matched {a['perobj']['matched']}/{a['perobj']['n_gt']} "
          f"({_pct(a['perobj']['matched'], a['perobj']['n_gt'])}), "
          f"n_pred {a['perobj']['n_pred']}; matched-despite-thin-screen "
          f"{a['matched_thin']}",
          f"- symbol unit: {sym_line(a)}", iou_line(a), ""]
    L += bucket_table(a)
    L += ["",
          f"- fused_cross_symbol sensitivity (after): bar {COVER_FRAC} -> "
          f"{a['buckets']['fused_cross_symbol']}; "
          + "; ".join(f"bar {k} -> {v}" for k, v in sorted(a["fused_sens"].items())),
          f"- pred purity (after, symbols majority-covered per kept pred): "
          f"{json.dumps(a['purity'])}",
          f"- pred purity (before): {json.dumps(b['purity'])}"]
    if n_wg:
        L += ["", f"## AFTER + WALL-PARTITIONED grouping (secondary unit, DOUBLE ORACLE; "
                  f"{n_wg} scenes with walls)",
              f"- symbol unit: {sym_line(wg)}", iou_line(wg), ""]
        L += bucket_table(wg)
        L += ["", "- delta vs plain grouping isolates CROSS-WALL chaining inside "
                  "union_oversize_region: "
                  f"{a['buckets']['union_oversize_region']} -> "
                  f"{wg['buckets']['union_oversize_region']} members "
                  f"({a['buckets']['union_oversize_region'] - wg['buckets']['union_oversize_region']:+d} "
                  "= chain mass a wall-aware grouping resolves)"]
    L += ["", "## reading discipline",
          "- symbol-level recall is FLATTERED by region-lumping (v1.1 doctrine): quote the "
          "bucket table + member coverage, never the symbol recall alone.",
          "- `granularity` = the reader emitted a matched cluster for that symbol; the "
          "per-object unit alone scores its members as misses. It is a SCORING-UNIT gap, "
          "not a reader failure.",
          "- `fused_cross_symbol` + `geometric_drift` + `touched_only` + `dropped_no_pred` "
          "= the REAL detection work remaining at symbol grain.",
          "- the PLAIN grouping chains across walls exactly like the reader's ink (v1.1 "
          "known mega-chain limit), so before-side `granularity` absorbs cross-wall lumps; "
          "the AFTER + wall-partitioned table is the wall-clean decomposition.",
          "- decor buckets are the reader's own thin screen, split: decor_micro (<150mm "
          "both axes) cannot plausibly reach IoU 0.5 against a kept pred; "
          "decor_thin_elongated (curtains/rails) CAN -- the matched-despite-thin-screen "
          "count above measures how often that actually happens, so the screen's cost is "
          "measured, never asserted. Both stay in the per-object denominator: the "
          "committed 13.3% is honest against full GT.",
          f"", f"engines: {LANE_VERSION} / {W.LANE_VERSION} / {R.READER_VERSION}"]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 4 and argv[1] == "--score":
        limit, pin_dir = None, None
        rest = argv[4:]
        i = 0
        while i < len(rest):
            if rest[i] == "limit" and i + 1 < len(rest) and rest[i + 1].isdigit():
                limit = int(rest[i + 1]); i += 2
            elif rest[i] == "--pin-cards" and i + 1 < len(rest):
                pin_dir = rest[i + 1]; i += 2
            else:
                i += 1
        score_corpus(argv[2], argv[3], limit=limit, pin_dir=pin_dir)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
