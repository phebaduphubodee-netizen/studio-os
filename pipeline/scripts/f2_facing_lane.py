"""
f2_facing_lane.py -- the FIRST pred!=gt cardinal_correct (F2 facing) measurement on any corpus.

WHY: after the 2026-07-09 convention validation (native yaw == build_floor rot, basis[0]=side,
qa/reports/f2-facing-convention-validated-2026-07-09.md) the GT side of F2 is closed -- but no
number exists because BOTH halves of the pred side were missing: synth_plan_2d draws bare
rects (zero facing ink) and svg_plan_reader is facing-blind (pred never carries rot), so every
eligible pair buckets 'unreported' and cardinal_correct reads 0.0 -- a number that measures
rot-emission ABSENCE, not angular error. This module supplies both halves WITHOUT editing any
existing file (svg_plan_reader/kind_priors are owned by a parallel session; synth_plan_2d's
byte-identity pins make in-place edits costlier than wrapping):

  1. ORIENTED SYNTH (oriented_svg): take synth_plan_2d.synth_svg's blind plan and APPEND a
     back-strip <line> per facing-kind element with a cardinal GT rot -- the headboard/backrest
     stroke a real plan draws, placed exactly per facing_reader's doctrine (parallel to the back
     edge = opposite(front), inset inside the 5-45%% inner band).
  2. VISUAL POST-PASS (enrich_pred_with_facing): run the UNEDITED svg_plan_reader.read_sheet,
     then re-read the raw ink (read_ink), clip segments per pred bbox, and let
     facing_reader.read_facing recover the strip -> pred rot via rot_from_facing. Pred-visible
     ink ONLY -- the post-pass never touches the gt doc.
  3. SCORE: benchmark_reader.score_pair unchanged; cardinal_correct falls out of the existing
     F2 card. A beds-excluded headline is computed via score_facing(facing_kinds - {'bed'})
     because S3D bed basis[0]-yaw encodes the LENGTH axis, not facing (validated report).

WHAT THE NUMBER IS (read before quoting): a CLOSED-LOOP ink-recovery score. The strip is drawn
FROM GT rot (exactly as a draughtsperson encodes facing in a real symbol), so cardinal_correct
measures "reader + facing post-pass recover the facing a plan legitimately encodes" -- the F2
analog of the synth F3 lane. It is NOT generalization to real-world symbol ink (FloorPlanCAD
carries no rot GT, so that lane stays UNWIRED); a flip/rotation ERROR planted in the drawing is
still caught (pinned by test: a 180-corrupted drawing scores 'flipped', not 'exact').

SECONDARY LANE (--oracle default-on): wall-prior rot -- predict front = away from the nearest
backing wall (gap <= 450mm), rot = forward_to_build_floor_rot(inward normal). This CONSUMES
gt['wall_lines'] and is therefore ORACLE-WALLS TIER (disclosed; precedent
floorplancad-oracle-walls-2026-07-07.md): it is a PRIOR, not a visual read, ceiling ~94.5%
on wall-backed strong-front per the validation report.

BLINDNESS LEDGER (what leaks and what cannot): indoor is NEVER read -- two gt docs differing
only in indoor produce byte-identical oriented SVGs (pinned). GT rot IS drawn (that is the
lane's purpose, disclosed above). Strip presence also reveals WHICH elements are facing-kinds;
F1 identity is not scored on this lane (pred carries no kind), so no identity leak is scored.

    python f2_facing_lane.py --score <gt-dir> <out-dir> [limit N] [--no-oracle]
"""
import copy
import glob
import json
import math
import os
import sys
import time

import benchmark_reader as B
import placement_gate as PG
import svg_plan_reader as R
import synth_plan_2d as S
from facing_reader import facing_from_rot, opposite, read_facing, rot_from_facing
from rot_reconcile import forward_to_build_floor_rot

LANE_VERSION = "f2_facing_lane v1.0"

# Back-strip placement: inset fraction of the perpendicular extent, measured inward from the
# back edge. Must sit inside facing_reader's inner band (5-45%); 12% mirrors a real ~150-250mm
# headboard on a ~1-2m piece and stays in-band even after the reader's raster wobble (~6mm/px)
# shifts the pred bbox a few mm.
STRIP_INSET_FRAC = 0.12
# Strip run as a fraction of the back edge, centred. Must clear read_facing's min_score=0.35
# after clipping to the (slightly different) pred bbox; 0.60 leaves margin without touching
# the corners (corner contact would fuse the strip into the outline ring visually).
STRIP_SPAN_FRAC = 0.60
# Segment-to-element clipping slack for the post-pass: pred bboxes are raster-derived
# (res ~6mm/px), so a strip drawn in the GT AABB can land a few mm outside the pred bbox.
CLIP_EPS_MM = 15.0
# Wall-prior lane: an element whose AABB sits within this gap of a wall is "wall-backed"
# (WALL_BACKED_MM from the validation oracle, qa/reports/f2-facing-convention-validated-*.md).
WALL_BACKED_MM = 450.0


def _strip_line(e):
    """The back-strip endpoints ((x1,y1),(x2,y2)) for a facing-kind element with a cardinal
    rot, in the element's TRUE axis-aligned footprint (placement_gate.footprint -- the same
    AABB the drawn rect and the scorer use; kinded elements carry the local un-yawed rect so
    footprint() must bake the rot, exactly as synth_plan_2d._as_footprint does for the rect).
    Returns None when the element has no cardinal facing to draw (non-cardinal rot, no rot,
    kind not facing-asymmetric) -- the element then stays a bare rect and scores 'unreported',
    never a guessed strip."""
    if B.norm_kind(e.get("kind")) not in B.FACING_KINDS:
        return None
    facing = facing_from_rot(e.get("rot"))
    if facing is None:                          # rot-less or non-cardinal: nothing to draw
        return None
    back = opposite(facing)
    x0, y0, x1, y1 = PG.footprint(e)
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return None
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    if back in ("N", "S"):
        yy = (y1 - STRIP_INSET_FRAC * h) if back == "N" else (y0 + STRIP_INSET_FRAC * h)
        half = (STRIP_SPAN_FRAC * w) / 2.0
        return (cx - half, yy), (cx + half, yy)
    xx = (x1 - STRIP_INSET_FRAC * w) if back == "E" else (x0 + STRIP_INSET_FRAC * w)
    half = (STRIP_SPAN_FRAC * h) / 2.0
    return (xx, cy - half), (xx, cy + half)


def oriented_svg(gt_doc, include_walls=False):
    """synth_plan_2d.synth_svg + one back-strip <line> per facing-kind cardinal-rot element.
    The blind renderer is reused VERBATIM (imported, not copied): strips are appended before
    </svg>, so an element set with zero drawable strips yields the byte-identical blind SVG.
    Returns (svg, stats); stats counts every skip (nothing is silently undrawn)."""
    base = S.synth_svg(gt_doc, include_walls=include_walls)
    strips, skipped_noncardinal, skipped_nonfacing = [], 0, 0
    for e in (gt_doc.get("elements", []) or []):
        if B.norm_kind(e.get("kind")) not in B.FACING_KINDS:
            skipped_nonfacing += 1
            continue
        line = _strip_line(e)
        if line is None:
            skipped_noncardinal += 1            # facing kind, but rot absent/non-cardinal
            continue
        (ax, ay), (bx, by) = line
        strips.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}"/>')
    stats = {"strips_drawn": len(strips), "skipped_noncardinal_or_rotless": skipped_noncardinal,
             "skipped_nonfacing_kind": skipped_nonfacing}
    if not strips:
        return base, stats
    return base.replace("</svg>", "\n".join(strips + ["</svg>"])), stats


def _attach_rot(el, rot):
    """Attach a CARDINAL rot to a pred element whose x/y/w/d is its world AABB, re-emitting
    the LOCAL un-yawed rect (w/d swapped + centre preserved at 90/270) so
    placement_gate.footprint rebuilds the SAME AABB. This mirrors the adapter's
    double-rotation fix on the pred side -- without it every correct 90/270 read re-rotates
    into a swapped AABB, drops below IoU 0.5, and becomes a detection MISS (observed live:
    o2/o4 vanished from the matched set the moment rot was attached)."""
    r = int(round(float(rot))) % 360
    if r in (90, 270):
        w, d = float(el["w"]), float(el["d"])
        cx, cy = float(el["x"]) + w / 2.0, float(el["y"]) + d / 2.0
        el["w"], el["d"] = d, w
        el["x"], el["y"] = round(cx - d / 2.0, 1), round(cy - w / 2.0, 1)
    el["rot"] = float(r)


def _ring_member_idx(segs, tol=0.6):
    """Indices of segments that are edges of a CLOSED axis-aligned rectangle (two horizontals
    with the same x-extent + two verticals with the same y-extent joining their corners).
    Those rings are furniture OUTLINES, not facing ink -- and they must be identified on the
    WHOLE sheet before per-element clipping, because a fused cluster's bbox contains a
    NEIGHBOUR's outline at an interior inset where it spoofs read_facing (observed live:
    a flat fused cabinet cluster read W=6.3 from five neighbour outlines vs the real strip's
    N=0.77 -> 90-degree wrong). A back-strip is a single unpaired stroke and never rings."""
    def k(v):
        return round(float(v), 1)
    hs, vs = {}, {}
    for i, s in enumerate(segs):
        (x0, y0), (x1, y1) = s
        if abs(y1 - y0) <= tol and abs(x1 - x0) > tol:
            a, b = sorted((x0, x1))
            hs.setdefault((k(a), k(b)), []).append((k(0.5 * (y0 + y1)), i))
        elif abs(x1 - x0) <= tol and abs(y1 - y0) > tol:
            a, b = sorted((y0, y1))
            vs.setdefault((k(a), k(b)), []).append((k(0.5 * (x0 + x1)), i))
    ring = set()
    for (xa, xb), rows in hs.items():
        if len(rows) < 2:
            continue
        for i1 in range(len(rows)):
            for i2 in range(i1 + 1, len(rows)):
                (ya, ia), (yb, ib) = rows[i1], rows[i2]
                if ya == yb:
                    continue
                lo, hi = (ya, yb) if ya < yb else (yb, ya)
                sides = vs.get((lo, hi), [])
                left = [ix for xv, ix in sides if xv == xa]
                right = [ix for xv, ix in sides if xv == xb]
                if left and right:
                    # remove EVERY coincident side, not just one: flush-adjacent furniture
                    # draws two identical verticals at the shared edge, and the survivor
                    # spoofed a W=1.0 'strip' on a fused cluster (scene_00005 o15, observed)
                    ring.update((ia, ib))
                    ring.update(left)
                    ring.update(right)
    return ring


def enrich_pred_with_facing(pred, segs_mm):
    """A COPY of pred whose elements carry rot wherever facing_reader reads a dominant
    back-strip from the PRED-VISIBLE ink. segs_mm = read_ink segments already scaled to mm.
    Closed rectangle outlines are filtered out first (_ring_member_idx) -- outline ink is
    not facing ink. Conservative by inheritance: a bare rect or a washed-out read stays
    rot-less (scored 'unreported'), never defaulted. Returns (pred_copy, stats)."""
    ring = _ring_member_idx(segs_mm)
    segs_mm = [s for i, s in enumerate(segs_mm) if i not in ring]
    out = copy.deepcopy(pred)
    n_emitted = 0
    for el in out.get("elements", []):
        x0, y0 = float(el["x"]) - CLIP_EPS_MM, float(el["y"]) - CLIP_EPS_MM
        x1 = float(el["x"]) + float(el["w"]) + CLIP_EPS_MM
        y1 = float(el["y"]) + float(el["d"]) + CLIP_EPS_MM
        local = [s for s in segs_mm
                 if x0 <= s[0][0] <= x1 and y0 <= s[0][1] <= y1
                 and x0 <= s[1][0] <= x1 and y0 <= s[1][1] <= y1]
        rf = read_facing(local, (float(el["x"]), float(el["y"]),
                                 float(el["x"]) + float(el["w"]),
                                 float(el["y"]) + float(el["d"])))
        if rf["facing"] is not None:
            _attach_rot(el, rot_from_facing(rf["facing"]))
            n_emitted += 1
    return out, {"rot_emitted": n_emitted, "rot_silent": len(out.get("elements", [])) - n_emitted}


def _seg_closest(cx, cy, seg):
    """(dist, (nx, ny)) from point to segment: distance + unit vector from the closest point
    on the segment TOWARD the query point. None normal for a degenerate/zero distance."""
    ax, ay = float(seg["x1"]), float(seg["y1"])
    bx, by = float(seg["x2"]), float(seg["y2"])
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((cx - ax) * dx + (cy - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    vx, vy = cx - qx, cy - qy
    dist = math.hypot(vx, vy)
    if dist < 1e-9:
        return dist, None
    return dist, (vx / dist, vy / dist)


def wall_prior_pred(pred, wall_lines):
    """ORACLE-WALLS TIER (consumes gt wall_lines -- disclose wherever scored): a COPY of pred
    where every element within WALL_BACKED_MM edge-gap of a wall gets rot = the build_floor
    angle of the wall's inward normal (front points from the backing wall INTO the room --
    the same geometry that VALIDATED the GT convention). Off-wall elements stay rot-less.
    This is a PRIOR, not a visual read; its known ceiling is ~94.5% on wall-backed
    strong-front kinds (n=73, validation report)."""
    out = copy.deepcopy(pred)
    n_emitted = n_diag = 0
    for el in out.get("elements", []):
        w, d = float(el["w"]), float(el["d"])
        cx, cy = float(el["x"]) + w / 2.0, float(el["y"]) + d / 2.0
        best = None
        for seg in (wall_lines or []):
            dist, n = _seg_closest(cx, cy, seg)
            if n is None:
                continue
            # support radius of the AABB along n = how far the element's edge extends from
            # its centroid toward the wall; gap = wall-to-edge clearance, not wall-to-centre
            gap = dist - ((w / 2.0) * abs(n[0]) + (d / 2.0) * abs(n[1]))
            if gap <= WALL_BACKED_MM and (best is None or gap < best[0]):
                best = (gap, n)
        if best is not None:
            rot = forward_to_build_floor_rot(best[1][0], best[1][1])
            if rot is None:
                continue
            # snap to the nearest cardinal: the pred element's x/y/w/d is a world AABB, so
            # rot must be cardinal for _attach_rot's local-rect re-emission to be exact. A
            # diagonal backing wall (>20deg off-cardinal) is SKIPPED (counted), not forced.
            card = min((0.0, 90.0, 180.0, 270.0), key=lambda c: B.angle_diff(rot, c))
            if B.angle_diff(rot, card) > 20.0:
                n_diag += 1
                continue
            _attach_rot(el, card)
            n_emitted += 1
    return out, {"rot_emitted": n_emitted, "skipped_diagonal_wall": n_diag,
                 "rot_silent": len(out.get("elements", [])) - n_emitted}


def _facing_nobed(gt_doc, pred_doc):
    """score_facing with beds excluded (S3D bed basis[0]-yaw encodes LENGTH, not facing --
    the validated report mandates excluding them from the strong-front headline). Runs the
    SAME sanitize + matcher score_pair uses, so the pair set is identical."""
    gt_el, _ = B.sanitize_elements(gt_doc.get("elements"))
    pr_el, _ = B.sanitize_elements(pred_doc.get("elements"))
    pairs, _m, _p = B.match_elements(gt_el, pr_el)
    return B.score_facing(pairs, facing_kinds=B.FACING_KINDS - {"bed"})


def score_scene(gt_doc, tmp_dir, oracle=True):
    """One scene through the full lane. Returns a row dict:
    card_visual (score_pair on the strip-read pred), f2_visual_nobed,
    card_oracle/f2_oracle_nobed (wall-prior, oracle-walls tier) when oracle=True,
    f2_blind (the same detection set with NO rot emission -- the 0.0 baseline),
    strip/emission stats."""
    svg, sstats = oriented_svg(gt_doc)
    p = os.path.join(tmp_dir, "oriented.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    pred = R.read_sheet(p, 1.0)
    segs = R.read_ink(p)["segs"]                # scale 1.0 -> svg units ARE mm
    pred_v, vstats = enrich_pred_with_facing(pred, segs)
    card_v = B.score_pair(gt_doc, pred_v)
    row = {"card_visual": card_v,
           "f2_visual_nobed": _facing_nobed(gt_doc, pred_v),
           "f2_blind": B.score_pair(gt_doc, pred)["F2_facing"],
           "strips": sstats, "visual_emit": vstats}
    if oracle:
        pred_o, ostats = wall_prior_pred(pred, gt_doc.get("wall_lines"))
        row["card_oracle"] = B.score_pair(gt_doc, pred_o)
        row["f2_oracle_nobed"] = _facing_nobed(gt_doc, pred_o)
        row["oracle_emit"] = ostats
    return row


def _sum_facing(dicts):
    """Aggregate score_facing / F2-card dicts across scenes from INTEGER counts (never
    ratio-averaging -- a low-n scene must not weigh like a full one)."""
    buckets = {"exact": 0, "cardinal": 0, "flipped": 0, "wrong": 0, "unreported": 0}
    for f in dicts:
        if not f:
            continue
        fb = f.get("buckets") or {}
        for b in buckets:
            buckets[b] += fb.get(b, 0)
    n = sum(buckets.values())
    ok = buckets["exact"] + buckets["cardinal"]
    return {"n": n, "hits": ok, "cardinal_correct": (ok / n) if n else None, "buckets": buckets}


def score_corpus(gt_dir, out_dir, limit=None, oracle=True):
    """Run the lane over every *.gt.json; write cards.jsonl (streamed) + report.md.
    One bad scene costs one row, never the run (mirrors synth_plan_2d.score_corpus)."""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    rows, skipped = [], {"error": 0, "units": 0}
    t0 = time.time()
    with open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8") as out, \
            tempfile.TemporaryDirectory() as td:
        for gfp in gt_files:
            base = os.path.basename(gfp)[:-len(".gt.json")]
            try:
                gt = json.load(open(gfp, encoding="utf-8"))
                if (gt.get("meta") or {}).get("units") != "mm":
                    skipped["units"] += 1
                    out.write(json.dumps({"scene": base, "skipped": "units"}) + "\n")
                    continue
                row = {"scene": base, **score_scene(gt, td, oracle=oracle)}
                rows.append(row)
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception as e:
                skipped["error"] += 1
                out.write(json.dumps({"scene": base, "skipped": "error",
                                      "error": f"{type(e).__name__}: {e}"}) + "\n")
            finally:
                out.flush()
    report = render_report(rows, skipped, len(gt_files), time.time() - t0, oracle=oracle)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return rows, skipped


def render_report(rows, skipped, n_total, secs, oracle=True):
    if not rows:
        return "# f2_facing_lane\n\nno gt scored -- " + json.dumps(skipped)
    agg_v = B.aggregate([r["card_visual"] for r in rows])
    det = agg_v["detection"]
    vis = _sum_facing([r["card_visual"]["F2_facing"] for r in rows])
    vis_nobed = _sum_facing([r.get("f2_visual_nobed") for r in rows])
    blind = _sum_facing([r.get("f2_blind") for r in rows])
    strips = sum(r["strips"]["strips_drawn"] for r in rows)
    noncard = sum(r["strips"]["skipped_noncardinal_or_rotless"] for r in rows)
    emitted = sum(r["visual_emit"]["rot_emitted"] for r in rows)

    def pct(v):
        return "n/a" if v is None else f"{100.0 * v:.1f}%"

    L = [
        "# f2_facing_lane -- FIRST pred!=gt cardinal_correct (F2 facing) on any corpus", "",
        f"- {LANE_VERSION}; synthesizer {S.SYNTH_VERSION} + back-strips; reader {R.READER_VERSION} "
        f"(UNEDITED, facing-blind) + facing_reader post-pass",
        f"- scenes: {len(rows)} scored / {n_total} (skipped {json.dumps(skipped)}); "
        f"wall-clock {secs:.0f}s",
        f"- detection context: GT {det['n_gt']} vs pred {det['n_pred']} -> matched "
        f"{det['matched']} (recall {pct(det['recall'])}) -- F2 scores the MATCHED subset only", "",
        "## headline -- VISUAL lane, beds excluded (closed-loop ink recovery)",
        f"| metric | value | meaning |",
        f"|---|---|---|",
        f"| cardinal_correct | {pct(vis_nobed['cardinal_correct'])} | reader+post-pass recover "
        f"the drawn facing, n={vis_nobed['n']} |",
        f"| buckets | {json.dumps(vis_nobed['buckets'])} | unreported = honest silence, counted in n |",
        "",
        f"- beds INCLUDED (contaminated -- S3D bed rot encodes length axis, not facing): "
        f"cardinal_correct {pct(vis['cardinal_correct'])} on n={vis['n']} "
        f"{json.dumps(vis['buckets'])}",
        f"- facing-blind baseline on the SAME detection set: "
        f"cardinal_correct {pct(blind['cardinal_correct'])} on n={blind['n']} "
        f"(all unreported -- what F2 read before this lane)",
        f"- strips drawn {strips} (skipped: {noncard} rot-less/non-cardinal facing-kinds); "
        f"post-pass emitted rot on {emitted} pred elements",
    ]
    if oracle and any("card_oracle" in r for r in rows):
        orc = _sum_facing([r["card_oracle"]["F2_facing"] for r in rows if "card_oracle" in r])
        orc_nobed = _sum_facing([r.get("f2_oracle_nobed") for r in rows])
        L += [
            "",
            "## secondary -- WALL-PRIOR lane (ORACLE-WALLS TIER: consumes gt wall_lines)",
            f"- beds excluded: cardinal_correct {pct(orc_nobed['cardinal_correct'])} on "
            f"n={orc_nobed['n']} {json.dumps(orc_nobed['buckets'])}",
            f"- beds included: cardinal_correct {pct(orc['cardinal_correct'])} on n={orc['n']}",
            "- a PRIOR (front = away from backing wall), not a read; ~94.5% known ceiling on "
            "wall-backed strong-front; off-wall elements stay honestly unreported",
        ]
    L += [
        "", "## what the headline IS (and is not)",
        "- CLOSED LOOP: the strip is drawn FROM GT rot (as a real plan encodes facing), so this "
        "measures ink-recovery fidelity end-to-end through the UNEDITED reader -- not "
        "generalization to real-world symbol ink (FloorPlanCAD has no rot GT; that lane stays "
        "UNWIRED). A planted 180-flip in the drawing scores 'flipped', not 'exact' (pinned).",
        "- OUTLINE-RING FILTER: closed rectangle outlines (incl. duplicated flush edges) are "
        "removed before the facing read -- outline ink is not facing ink. Without it, fused "
        "clusters read NEIGHBOUR outlines as giant strips (naive post-pass scored 66.7%; the "
        "failures were 90-degree fusion spoofs, not angular noise -- both mechanisms pinned).",
        "- n is SMALL (detection recall on this corpus ~7-10%: sub-object fusion) -- read "
        "aggregate buckets, not per-scene verdicts; low_n applies.",
        "- unreported counts AGAINST cardinal_correct by design (anti-flattery rule).",
        "- BEDS score 'exact' here BY CONSTRUCTION (the strip is drawn from the same GT rot "
        "being scored) -- the bed caveat is SEMANTIC (S3D bed yaw encodes length, not true "
        "facing), so the beds-excluded row stays the headline.",
        "", f"engines: {LANE_VERSION} / {S.SYNTH_VERSION} / {R.READER_VERSION}",
    ]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 4 and argv[1] == "--score":
        limit, oracle = None, "--no-oracle" not in argv
        rest = [a for a in argv[4:] if a != "--no-oracle"]
        i = 0
        while i < len(rest):
            if rest[i] == "limit" and i + 1 < len(rest) and rest[i + 1].isdigit():
                limit = int(rest[i + 1]); i += 2
            else:
                i += 1
        score_corpus(argv[2], argv[3], limit=limit, oracle=oracle)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
