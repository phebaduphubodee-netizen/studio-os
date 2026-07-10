"""
blind_wall_lane.py -- UN-ORACLE the wall tier: the wall_aware/symbol_unit ceiling numbers
re-measured with a REAL wall detector instead of gt['wall_lines'].

WHY: the whole wall tier to date is ORACLE-WALLS -- wall_aware_lane's +2.6pp detection
recall (10.7 -> 13.3), the symbol-unit tier (76.9% symbol recall / 65.6% member coverage)
and the F2 wall-prior band all consume the answer key's wall geometry, because the
oriented synth sheet carries NO wall ink at all: a wall that is never drawn cannot be
detected blind, so the ceiling could not be cashed. This lane closes that hole in the
production shape (the PDF lane's shape): make walls OBSERVABLE on the sheet, detect them
from the sheet ONLY, and re-run the same split -- so the oracle band converts into a
blind number plus a measured detector gap.

SHEET (closed loop, disclosed): f2_facing_lane.oriented_svg (rects + back-strips,
UNCHANGED) + wall_detect.append_wall_ink -- gt wall centerlines drawn as DOUBLE parallel
lines at +/-50mm (the standard architectural wall convention, the same signal
pdf_extract_walls keys on for real sheets via stroke thickness). gt wall_lines reach the
DRAWING side exactly like gt rot reaches the back-strips (precedent, disclosed); nothing
else about the sheet changes. Glazing is NOT drawn (scoped out, disclosed).

THREE ARMS on the SAME sheet, same ink, same enrichment stack:
  NAIVE   the unedited reader on the walls-drawn sheet, walls unknown -- measures what
          wall ink COSTS a wall-unaware reader (the reason the PDF lane strips walls
          first: plan_cluster.extract_clusters' `w >= 0.6: continue`).
  BLIND   the production pipeline: wall_detect.detect_walls on the ink (geometry only,
          ring-filtered) -> classified wall segments MASKED OUT of the symbol ink
          (segment-identity masking, the SVG analog of the PDF lane's thick-stroke skip)
          -> detected centerlines as the wall_aware mid-closing barrier. No gt field
          reaches this arm past the drawing step.
  ORACLE  same-sheet ceiling: the TRUE wall-ink identity (the appended slice) masked
          out + gt centerlines as the barrier. The blind-vs-oracle delta is CAUSALLY the
          detector's cost; comparing blind to the committed no-wall-sheet numbers alone
          would confound sheet change with detector quality.

MASKING is segment-identity, not raster erasure: classified segments are dropped from
the segment LIST before rasterization, so real furniture ink is never cut (the
cut-real-ink trap, pinned in wall_aware_lane). csegs (curve ink) never contains wall
lines (<line> ink is straight) and passes through unchanged.

SYMBOL TIER (secondary): the plan-symbol decomposition (symbol_unit_lane's decompose,
imported + its own internal pins) re-scored on the blind and oracle arms. The UNIT stays
gt-wall-partitioned (unit definition is answer-key-side GT construction -- standard for
a benchmark and disclosed); what is un-oracled here is the PRED: barrier + masking from
detected walls. UNIT WARNING: the committed 76.9/65.6 headline is the PLAIN 90mm unit
(68.5k symbols); this lane's wall-partitioned unit is finer (~89.1k symbols, ~30%
larger denominator), so the two are NOT comparable at any n -- the same-sheet oracle
column is the only reference for the blind symbol number (adversarial review).

MEASURED, NEVER ASSERTED: detector quality per scene (segment-classification confusion
vs the true appended slice + length-weighted centerline coverage vs gt, zero-coverage
split micro/real), strips eaten by misclassification (the F2 wound channel; the strip
slice is numerically identity-pinned like the wall slice), rot-silent baselines for ALL
THREE arms, per-pair F2 transitions oracle->blind (the fn-leak flip channel shows up
here). Skip taxonomy {error, units, no_walls} is printed with the ALL-GREEN
reconciliation line (flattering-scorer doctrine, 6th-recurrence watch: the identity
pins RAISE into the error counter, so a shifted slice can never quietly score), and the
symbol section counts plain-unit fallbacks instead of letting them blend in.

    python blind_wall_lane.py --score <gt-dir> <out-dir> [limit N] [--no-symbol]
                              [--pin-cards <committed-wall-aware-run-dir>]
"""
import copy
import glob
import json
import os
import sys
import time

import benchmark_reader as B
import f2_facing_lane as F2L
import svg_plan_reader as R
import wall_aware_lane as W
import wall_detect as WD
from symbol_unit_lane import (assert_matches_group_symbols, decompose, region_of_centre,
                              symbol_membership, wall_regions)
from synth_plan_2d import _as_footprint

LANE_VERSION = "blind_wall_lane v1.0"


# ---- one scene, three arms -----------------------------------------------------------------
def _arm_pred(base_pred, elements, stats, tier):
    """A COPY of the naive pred with lane-derived elements + a tier-marked meta block, so
    an arm's pred can never be mistaken for another tier's (wall_aware_pred doctrine).
    Openings/meta are inherited from the naive read -- F4 is NOT a deliverable of this
    lane (naive openings see wall ink; disclosed in the report)."""
    out = copy.deepcopy(base_pred)
    out["elements"] = elements
    out["meta"]["blind_wall_lane"] = {"tier": tier, "lane": LANE_VERSION, **stats}
    return out


def _sanitized(doc):
    el, _ = B.sanitize_elements(doc.get("elements"))
    return el


def _trim_dec(dec):
    """The per-scene keep of a decompose() card: counts only (perobj_missed_ids is the
    heavy list; the corpus questions here are aggregate)."""
    return {"perobj": dec["perobj"], "matched_thin": dec["matched_thin"],
            "symbol": dec["symbol"], "buckets": dec["buckets"],
            "sym_iou_hist": dec["sym_iou_hist"], "pred_purity": dec["pred_purity"]}


def score_scene(gt_doc, tmp_dir, symbol=True):
    """One scene: walls-drawn sheet -> naive/blind/oracle preds -> detection + F2 + F3
    cards per arm + detector quality + (optional) the symbol-tier decomposition on the
    blind and oracle arms."""
    svg0, sstats = F2L.oriented_svg(gt_doc)
    svg, expected, n_deg = WD.append_wall_ink(svg0, gt_doc.get("wall_lines"))
    p = os.path.join(tmp_dir, "blindwall.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)

    pred_n = R.read_sheet(p, 1.0)                 # NAIVE arm (walls unknown)
    ink = R.read_ink(p)                            # scale 1.0 -> svg units ARE mm
    segs, csegs = ink["segs"], ink["curve_segs"]

    # identity pin: the appended wall ink must be EXACTLY the tail slice of read_ink's
    # segment list (strips precede it; zero-length drops upstream cannot shift a tail
    # index). A mismatch RAISES -> counted as a scene error, never scored shifted.
    n_wall = len(expected)
    if n_wall:
        if len(segs) < n_wall:
            raise AssertionError(f"wall ink slice missing: {len(segs)} segs < {n_wall}")
        for k, (ea, eb) in enumerate(expected):
            (ga, gb) = segs[len(segs) - n_wall + k]
            if (abs(ga[0] - ea[0]) > 0.05 or abs(ga[1] - ea[1]) > 0.05
                    or abs(gb[0] - eb[0]) > 0.05 or abs(gb[1] - eb[1]) > 0.05):
                raise AssertionError(f"wall ink identity pin failed at tail index {k}: "
                                     f"{(ga, gb)} != {(ea, eb)}")
    true_wall = set(range(len(segs) - n_wall, len(segs))) if n_wall else set()
    # strip slice: pinned NUMERICALLY exactly like the wall slice (re-derive the strip
    # endpoints via the same _strip_line oriented_svg drew from) -- a re-ordered synth
    # would otherwise silently shift what strips_eaten counts (adversarial review)
    n_strips = sstats["strips_drawn"]
    strip_idx = set(range(len(segs) - n_wall - n_strips, len(segs) - n_wall))
    exp_strips = [F2L._strip_line(e) for e in (gt_doc.get("elements", []) or [])
                  if B.norm_kind(e.get("kind")) in B.FACING_KINDS
                  and F2L._strip_line(e) is not None]
    if len(exp_strips) != n_strips:
        raise AssertionError(f"strip slice pin: re-derived {len(exp_strips)} strips "
                             f"!= drawn {n_strips}")
    for k, ((ax, ay), (bx, by)) in enumerate(exp_strips):
        (ga, gb) = segs[len(segs) - n_wall - n_strips + k]
        if (abs(ga[0] - round(ax, 1)) > 0.05 or abs(ga[1] - round(ay, 1)) > 0.05
                or abs(gb[0] - round(bx, 1)) > 0.05 or abs(gb[1] - round(by, 1)) > 0.05):
            raise AssertionError(f"strip ink identity pin failed at strip index {k}")

    # BLIND detection: ink geometry only (furniture-ring filter from the same ink;
    # the F2 enrichment below keeps its own, stricter ring filter -- different purpose)
    det = WD.detect_walls(segs)
    wall_idx = det["wall_idx"]
    fn_idx = true_wall - wall_idx
    # fn split by face length: a face below MIN_LINE_MM is skipped before pairing, so
    # its fn is BY CONSTRUCTION -- lumping it with real misses would let a detector
    # regression hide inside the micro-wall narrative (same hardening as walls_zero)
    fn_micro = sum(1 for i in fn_idx
                   if ((segs[i][1][0] - segs[i][0][0]) ** 2
                       + (segs[i][1][1] - segs[i][0][1]) ** 2) < WD.MIN_LINE_MM ** 2)
    cls = {"tp": len(wall_idx & true_wall), "fp": len(wall_idx - true_wall),
           "fn": len(fn_idx), "fn_micro": fn_micro, "fn_real": len(fn_idx) - fn_micro,
           "strips_eaten": len(wall_idx & strip_idx),
           "n_true_wall_segs": n_wall, "degenerate_walls_skipped": n_deg}
    cov = WD.coverage_vs_gt(det["centerlines"], gt_doc.get("wall_lines"))

    segs_b = [s for i, s in enumerate(segs) if i not in wall_idx]
    segs_o = [s for i, s in enumerate(segs) if i not in true_wall]
    el_b, st_b = W.wall_barrier_elements(segs_b, csegs, det["centerlines"])
    el_o, st_o = W.wall_barrier_elements(segs_o, csegs, gt_doc.get("wall_lines"))
    pred_b = _arm_pred(pred_n, el_b, {**det["stats"], **cls}, "BLIND")
    pred_o = _arm_pred(pred_n, el_o, st_o, "ORACLE-WALLS")

    # F2 enrichment per arm on that arm's own visible (post-mask) ink
    pred_nv, emit_n = F2L.enrich_pred_with_facing(pred_n, segs)
    pred_bv, emit_b = F2L.enrich_pred_with_facing(pred_b, segs_b)
    pred_ov, emit_o = F2L.enrich_pred_with_facing(pred_o, segs_o)
    nobed_n = F2L._facing_nobed(gt_doc, pred_nv)
    nobed_b = F2L._facing_nobed(gt_doc, pred_bv)
    nobed_o = F2L._facing_nobed(gt_doc, pred_ov)
    # WALL-PRIOR-IN-DISGUISE instrument (REPORT side only; uses the true wall-ink
    # identity to MEASURE, never to score): the naive arm's enrichment sees gt-drawn
    # wall faces, and read_facing consumes an in-band face as a back-strip -- usually
    # CORRECTLY oriented, because the wall sits behind the furniture (the disclosed
    # ~94.5% oracle wall-prior geometry). Re-enrich the same naive pred on wall-masked
    # ink; every emission that vanishes was answer-key wall geometry, not strip
    # recovery (adversarial review 2026-07-10, reproduced on a rot-less element).
    _, emit_n_nowall = F2L.enrich_pred_with_facing(pred_n, segs_o)
    naive_wallink_rot = emit_n["rot_emitted"] - emit_n_nowall["rot_emitted"]

    row = {"n_walls_drawn": n_wall, "detector": {**det["stats"], **cls, "cov": cov},
           "card_naive": B.score_pair(gt_doc, pred_nv),
           "card_blind": B.score_pair(gt_doc, pred_bv),
           "card_oracle": B.score_pair(gt_doc, pred_ov),
           "f2_nobed_naive": nobed_n, "f2_nobed_blind": nobed_b, "f2_nobed_oracle": nobed_o,
           # MEASURED rot-silent baselines, ALL THREE arms, BEDS-EXCLUDED (same
           # population as the headline table -- a beds-included baseline printed in
           # the beds-excluded section left an unexplained n gap, adversarial review;
           # un-enriched preds: anything but unreported = rot without ink = defect)
           "f2_base_naive": F2L._facing_nobed(gt_doc, pred_n),
           "f2_base_blind": F2L._facing_nobed(gt_doc, pred_b),
           "f2_base_oracle": F2L._facing_nobed(gt_doc, pred_o),
           "naive_wallink_rot": naive_wallink_rot,
           "emit_naive_nowall": emit_n_nowall,
           # what the detector COSTS, per before-matched pair (oracle -> blind)
           "f2_transitions_o2b": W.facing_transitions(nobed_o, nobed_b),
           "strips": sstats, "emit_naive": emit_n, "emit_blind": emit_b,
           "emit_oracle": emit_o, "wa_blind": st_b, "wa_oracle": st_o}

    if symbol:
        clean = _sanitized(gt_doc)
        symbols, member_of, decor_idx, oversize_idx = symbol_membership(clean)
        assert_matches_group_symbols(clean, symbols, meta=gt_doc.get("meta"))
        regions, zone, res, n_regions = wall_regions(segs, gt_doc.get("wall_lines"))
        if regions is not None:
            fps = [_as_footprint(e) for e in clean]
            reg = {i: region_of_centre(f, regions, zone, res) for i, f in enumerate(fps)}
            member_clean_idx = sorted(member_of)

            def allowed(i, j):
                a, b = reg[member_clean_idx[i]], reg[member_clean_idx[j]]
                return a == 0 or b == 0 or a == b

            symbols_u, member_u, decor_u, oversize_u = symbol_membership(clean, allowed=allowed)
            if (decor_u, oversize_u) != (decor_idx, oversize_idx):
                raise AssertionError("wall-partitioned unit changed the member screen")
        else:
            # no usable walls: the plain grouping IS the unit (counted via n_regions=0)
            symbols_u, member_u, decor_u, oversize_u = symbols, member_of, decor_idx, oversize_idx
        row["n_regions"] = int(n_regions)
        row["sym_blind"] = _trim_dec(decompose(clean, _sanitized(pred_b), symbols_u,
                                               member_u, decor_u, oversize_u))
        row["sym_oracle"] = _trim_dec(decompose(clean, _sanitized(pred_o), symbols_u,
                                                member_u, decor_u, oversize_u))
    return row


# ---- equivalence pin vs the committed wall-aware run ----------------------------------------
def load_pin_cards(run_dir):
    """Committed wall_aware cards.jsonl -> {scene: (n_gt, n_pred, matched, missed_ids)}
    of the AFTER (gt-barrier) arm. The oracle arm here is the same computation on the
    same masked ink, so per-scene equality is the COMPUTED basis for quoting the
    committed 10.7/13.3 references next to this lane's columns -- previously that claim
    was hardcoded report prose printed by every run (adversarial review 2026-07-10, the
    6th-recurrence shape: a drift alarm that existed only as words)."""
    pins = {}
    with open(os.path.join(run_dir, "cards.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if "card_after" in r:
                d = r["card_after"]["detection"]
                pins[r["scene"]] = (d["n_gt"], d["n_pred"], d["matched"],
                                    sorted(d.get("missed_ids") or [], key=str))
    return pins


def check_pin(row, pin):
    d = row["card_oracle"]["detection"]
    return (d["n_gt"], d["n_pred"], d["matched"],
            sorted(d.get("missed_ids") or [], key=str)) == pin


# ---- corpus run ---------------------------------------------------------------------------
def score_corpus(gt_dir, out_dir, limit=None, symbol=True, pin_dir=None):
    """Every *.gt.json through score_scene; cards.jsonl streamed, report.md at the end.
    One bad scene costs one row, never the run (wall_aware_lane doctrine). pin_dir =
    a committed wall_aware run dir; when given, every scene's oracle arm is compared
    against the committed after-arm card and mismatches are counted (and kill
    ALL-GREEN); when absent the report says so instead of claiming verification."""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    if limit:
        gt_files = gt_files[:int(limit)]
    pins = load_pin_cards(pin_dir) if pin_dir else None
    pin_stats = {"compared": 0, "mismatch": 0, "absent": 0,
                 "mismatch_scenes": []} if pins is not None else None
    rows, skipped = [], {"error": 0, "units": 0, "no_walls": 0}
    t0 = time.time()
    with open(os.path.join(out_dir, "cards.jsonl"), "w", encoding="utf-8") as out, \
            tempfile.TemporaryDirectory() as td:
        for k, gfp in enumerate(gt_files):
            base = os.path.basename(gfp)[:-len(".gt.json")]
            try:
                gt = json.load(open(gfp, encoding="utf-8"))
                if (gt.get("meta") or {}).get("units") != "mm":
                    skipped["units"] += 1
                    out.write(json.dumps({"scene": base, "skipped": "units"}) + "\n")
                    continue
                if not gt.get("wall_lines"):
                    skipped["no_walls"] += 1          # scored anyway; COUNTED (doctrine)
                row = {"scene": base, **score_scene(gt, td, symbol=symbol)}
                if pins is not None:
                    if base not in pins:
                        pin_stats["absent"] += 1
                        row["pin"] = "absent"
                    elif check_pin(row, pins[base]):
                        pin_stats["compared"] += 1
                        row["pin"] = "ok"
                    else:
                        pin_stats["compared"] += 1
                        pin_stats["mismatch"] += 1
                        if len(pin_stats["mismatch_scenes"]) < 20:
                            pin_stats["mismatch_scenes"].append(base)
                        row["pin"] = "MISMATCH"
                rows.append(row)
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception as e:
                skipped["error"] += 1
                out.write(json.dumps({"scene": base, "skipped": "error",
                                      "error": f"{type(e).__name__}: {e}"}) + "\n")
            finally:
                out.flush()
                if (k + 1) % 100 == 0:
                    print(f"  {k + 1}/{len(gt_files)}  scored={len(rows)}  "
                          f"({time.time() - t0:.0f}s)", flush=True)
    report = render_report(rows, skipped, len(gt_files), time.time() - t0,
                           symbol=symbol, pin_stats=pin_stats)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return rows, skipped


def _pct(v):
    return "n/a" if v is None else f"{100.0 * v:.1f}%"


def _sym_agg(rows, key):
    """Sum-based symbol-tier aggregate for one arm (never ratio-averaging)."""
    n_sym = matched = members = in_matched = 0
    for r in rows:
        d = r.get(key)
        if not d:
            continue
        s = d["symbol"]
        n_sym += s["n_sym"]
        matched += s["matched"]
        members += s["members_total"]
        in_matched += s["members_in_matched_sym"]
    return {"n_sym": n_sym, "matched": matched,
            "recall_sym": (matched / n_sym) if n_sym else None,
            "members_total": members, "members_in_matched": in_matched,
            "member_coverage": (in_matched / members) if members else None}


def render_report(rows, skipped, n_total, secs, symbol=True, pin_stats=None):
    if not rows:
        return "# blind_wall_lane\n\nno gt scored -- " + json.dumps(skipped)
    aggs = {arm: B.aggregate([r[f"card_{arm}"] for r in rows])
            for arm in ("naive", "blind", "oracle")}
    det = {arm: aggs[arm]["detection"] for arm in aggs}
    f3 = {arm: aggs[arm]["F3_indoor"] for arm in aggs}
    nb = {arm: F2L._sum_facing([r[f"f2_nobed_{arm}"] for r in rows])
          for arm in ("naive", "blind", "oracle")}
    base_n = F2L._sum_facing([r.get("f2_base_naive") for r in rows])
    base_b = F2L._sum_facing([r.get("f2_base_blind") for r in rows])
    base_o = F2L._sum_facing([r.get("f2_base_oracle") for r in rows])

    # detector aggregates
    tp = sum(r["detector"]["tp"] for r in rows)
    fp = sum(r["detector"]["fp"] for r in rows)
    fn = sum(r["detector"]["fn"] for r in rows)
    fn_micro = sum(r["detector"].get("fn_micro", 0) for r in rows)
    fn_real = sum(r["detector"].get("fn_real", 0) for r in rows)
    strips_eaten = sum(r["detector"]["strips_eaten"] for r in rows)
    naive_wallink = sum(r.get("naive_wallink_rot", 0) for r in rows)
    naive_emit = sum(r["emit_naive"]["rot_emitted"] for r in rows)
    gt_len = sum(r["detector"]["cov"]["gt_len"] for r in rows)
    gt_cov = sum(r["detector"]["cov"]["gt_covered"] for r in rows)
    det_len = sum(r["detector"]["cov"]["det_len"] for r in rows)
    det_cov = sum(r["detector"]["cov"]["det_covered"] for r in rows)
    zero_micro = sum(r["detector"]["cov"].get("walls_zero_micro", 0) for r in rows)
    zero_real = sum(r["detector"]["cov"].get("walls_zero_real", 0) for r in rows)
    zero_max = max((r["detector"]["cov"].get("zero_max_len", 0) for r in rows), default=0)
    n_gt_walls = sum(r["detector"]["cov"]["n_gt_walls"] for r in rows)
    n_wall_scenes = sum(1 for r in rows if r["n_walls_drawn"])
    low_scenes = sum(1 for r in rows
                     if (r["detector"]["cov"]["recall_len"] or 0) < 0.9
                     and r["n_walls_drawn"])

    # oracle -> blind per-pair transitions (what the detector costs on the common subset)
    trans = {"before_n": 0, "unchanged": 0, "left_matched_set": 0, "changed": {}, "new": {}}
    for r in rows:
        t = r.get("f2_transitions_o2b") or {}
        trans["before_n"] += t.get("before_n", 0)
        trans["unchanged"] += t.get("unchanged", 0)
        trans["left_matched_set"] += t.get("left_matched_set", 0)
        for k, v in (t.get("changed") or {}).items():
            trans["changed"][k] = trans["changed"].get(k, 0) + v
        for k, v in (t.get("new") or {}).items():
            trans["new"][k] = trans["new"].get(k, 0) + v
    _RANK = {"exact": 3, "cardinal": 2, "unreported": 1, "wrong": 0, "flipped": 0,
             "left_matched_set": -1}
    downgrades = sum(v for k, v in trans["changed"].items()
                     if _RANK.get(k.split("->")[1], -1) < _RANK.get(k.split("->")[0], 3))
    # in the oracle->blind direction an UPGRADE is not an improvement: the blind arm
    # sees strictly less honest ink than oracle, so a pair that gets BETTER can only
    # have been fed by detector-fn wall faces (gt geometry acting as the wall prior) --
    # gt-assisted credit, flagged exactly like downgrades (adversarial review)
    upgrades = sum(v for k, v in trans["changed"].items()
                   if _RANK.get(k.split("->")[1], -1) > _RANK.get(k.split("->")[0], 3))
    new_nonsilent = sum(v for k, v in trans["new"].items() if k != "unreported")

    green = (skipped["error"] == 0
             and (pin_stats is None or (pin_stats["mismatch"] == 0)))
    L = [
        "# blind_wall_lane -- the wall tier UN-ORACLED: naive / BLIND / oracle on the "
        "same walls-drawn sheet", "",
        "**TIER: BLIND headline** -- the blind arm's walls come from wall_detect on the",
        "sheet ink only (geometry, ring-filtered); no gt field reaches that arm past the",
        "DRAWING step. CLOSED LOOP disclosed: walls are drawn from gt centerlines as",
        f"double lines at +/-{WD.WALL_T_MM / 2:.0f}mm (the convention pdf_extract_walls",
        "keys on for real sheets); detector thresholds are tuned to that convention.",
        "Glazing is NOT drawn. The oracle arm is the SAME-SHEET ceiling (true ink",
        "identity + gt centerlines), so blind-vs-oracle isolates the detector's cost.", "",
        f"- {LANE_VERSION}; wall_detect T={WD.WALL_T_MM:.0f}mm gap[{WD.GAP_MIN_MM:.0f},"
        f"{WD.GAP_MAX_MM:.0f}]; {W.LANE_VERSION} barrier (unedited); f2 {F2L.LANE_VERSION}; "
        f"reader {R.READER_VERSION} (UNEDITED, wrapper only)",
        f"- scenes: {len(rows)} scored / {n_total} (skipped {json.dumps(skipped)}); "
        f"wall-clock {secs:.0f}s",
        f"- ALL-GREEN reconciliation: {'GREEN' if green else 'NOT GREEN'} -- errors "
        f"include every raised identity/drift pin (a shifted wall slice can never "
        f"quietly score); no_walls scenes are scored AND counted; a pin mismatch "
        f"(below) kills the flag",
        ("- EQUIVALENCE PIN (COMPUTED per scene, oracle arm vs the committed wall-aware "
         f"after-arm): {pin_stats['compared']} compared, "
         f"**{pin_stats['mismatch']} mismatch(es)**"
         + (f" ({', '.join(pin_stats['mismatch_scenes'])}"
            + ("..." if pin_stats['mismatch'] > 20 else "") + ")"
            if pin_stats["mismatch"] else "")
         + f", {pin_stats['absent']} absent from the committed run -- this is the "
         f"basis for quoting the committed references below"
         if pin_stats is not None else
         "- EQUIVALENCE PIN NOT RUN (no --pin-cards): the committed cross-sheet "
         "references below are UNVERIFIED for this run -- quote the same-sheet "
         "oracle column only"), "",
        "## detector quality (measured per scene, never assumed)",
        "| metric | value |",
        "|---|---|",
        f"| wall-segment classification | tp {tp} / fp {fp} / fn {fn} -> precision "
        f"{_pct(tp / (tp + fp) if tp + fp else None)}, recall "
        f"{_pct(tp / (tp + fn) if tp + fn else None)} -- fn split: micro-face "
        f"<{WD.MIN_LINE_MM:.0f}mm (by construction) {fn_micro}, **real {fn_real}** |",
        f"| centerline length coverage (recall) | {_pct(gt_cov / gt_len if gt_len else None)} "
        f"of {gt_len / 1000.0:.0f} m gt wall (tolerance: lat 60mm / ang 6deg -- a "
        f"systematic ~50mm offset would still score covered; the seg-level row above "
        f"is exact-identity) |",
        f"| centerline length precision | {_pct(det_cov / det_len if det_len else None)} "
        f"of {det_len / 1000.0:.0f} m detected |",
        f"| gt walls with ZERO coverage | {zero_micro + zero_real} / {n_gt_walls} -- "
        f"micro <{WD.MIN_LINE_MM:.0f}mm (undetectable by construction): {zero_micro}; "
        f"**REAL misses >={WD.MIN_LINE_MM:.0f}mm: {zero_real}** (longest {zero_max:.0f}mm) |",
        f"| back-strips eaten (misclassified as wall ink) | {strips_eaten} |",
        f"| scenes with length-recall < 90% | {low_scenes} / {n_wall_scenes} "
        f"walls-drawn scenes ({len(rows) - n_wall_scenes} no-wall scenes excluded from "
        f"both sides) |", "",
        "## detection -- the un-oracled headline",
        "| metric | naive (walls unknown) | BLIND (detector) | oracle (same sheet) |",
        "|---|---|---|---|",
        f"| recall | {_pct(det['naive']['recall'])} | **{_pct(det['blind']['recall'])}** | "
        f"{_pct(det['oracle']['recall'])} |",
        f"| precision | {_pct(det['naive']['precision'])} | "
        f"**{_pct(det['blind']['precision'])}** | {_pct(det['oracle']['precision'])} |",
        f"| matched | {det['naive']['matched']} | {det['blind']['matched']} | "
        f"{det['oracle']['matched']} |",
        f"| n_pred | {det['naive']['n_pred']} | {det['blind']['n_pred']} | "
        f"{det['oracle']['n_pred']} |",
        "",
        f"(committed no-wall-sheet references, n=3,500 scenes: reader 10.7% recall blind "
        f"headline; gt-barrier 13.3% ORACLE -- structured3d-wall-aware-2026-07-10.md. "
        f"THIS run n={len(rows)}: same-population only at full corpus; on a partial run "
        f"the only apples-to-apples ceiling is the same-sheet oracle column. Whether "
        f"the oracle arm actually reproduces the committed after-arm is the COMPUTED "
        f"equivalence-pin line at the top of this report, never assumed.)", "",
        "## F2 facing -- visual lane, beds excluded",
        "| metric | naive | BLIND | oracle |",
        "|---|---|---|---|",
        f"| cardinal_correct | {_pct(nb['naive']['cardinal_correct'])} | "
        f"**{_pct(nb['blind']['cardinal_correct'])}** | "
        f"{_pct(nb['oracle']['cardinal_correct'])} |",
        f"| n / hits | {nb['naive']['n']} / {nb['naive']['hits']} | "
        f"{nb['blind']['n']} / {nb['blind']['hits']} | "
        f"{nb['oracle']['n']} / {nb['oracle']['hits']} |",
        f"| buckets | {json.dumps(nb['naive']['buckets'])} | "
        f"{json.dumps(nb['blind']['buckets'])} | {json.dumps(nb['oracle']['buckets'])} |",
        "",
        f"### per-pair decomposition, oracle -> blind (the detector's F2 cost on the "
        f"common subset; aggregates compare two populations)",
        f"- of {trans['before_n']} oracle-matched facing pairs: {trans['unchanged']} "
        f"unchanged, changed/left {json.dumps(trans['changed']) if trans['changed'] else 'none'}"
        + (f" -- **{downgrades} DOWNGRADE(S), inspect before quoting**" if downgrades
           else " -- zero downgrades")
        + (f"; **{upgrades} UPGRADE(S) = GT-ASSISTED CREDIT** (blind sees strictly "
           f"less honest ink than oracle, so a pair can only improve via detector-fn "
           f"wall faces acting as the wall prior -- contamination, not improvement)"
           if upgrades else ""),
        f"- newly matched in blind only: {sum(trans['new'].values())} "
        f"({json.dumps(trans['new'])})"
        + (f" -- **{new_nonsilent} carry non-unreported buckets: same gt-assisted "
           f"caveat as upgrades**" if new_nonsilent else ""),
        f"- rot-silent baselines MEASURED per arm, beds-excluded (un-enriched preds, "
        f"same population as the table above): naive "
        f"{_pct(base_n['cardinal_correct'])} n={base_n['n']}; blind "
        f"{_pct(base_b['cardinal_correct'])} n={base_b['n']} "
        f"{json.dumps(base_b['buckets'])}; oracle {_pct(base_o['cardinal_correct'])} "
        f"n={base_o['n']} (anything but unreported = rot without ink = lane defect)",
        f"- **NAIVE F2 COLUMN IS WALL-PRIOR-CONTAMINATED (measured)**: "
        f"{naive_wallink} of the naive arm's {naive_emit} rot emissions vanish when "
        f"the true wall ink is masked out of its enrichment -- those reads are "
        f"answer-key wall geometry consumed as back-strips (the ~94.5% oracle "
        f"wall-prior in disguise), not strip recovery. Quote the naive column for "
        f"DETECTION only, never for facing.",
        f"- LOW-N / POPULATION discipline: the naive column's facing population is "
        f"survivor-selected (only clusters that survived un-masked wall-ink fusion) and "
        f"much smaller (n={nb['naive']['n']} vs {nb['blind']['n']}) -- read buckets, not "
        f"the percentage; per-scene low_n applies to all three arms", "",
        "## F3 indoor (matched-set composition; pred stays indoor-silent)",
        f"- naive {_pct(f3['naive']['accuracy'])} (n={f3['naive']['n']}) | blind "
        f"{_pct(f3['blind']['accuracy'])} (n={f3['blind']['n']}) | oracle "
        f"{_pct(f3['oracle']['accuracy'])} (n={f3['oracle']['n']})",
    ]
    if symbol and any("sym_blind" in r for r in rows):
        sb = _sym_agg(rows, "sym_blind")
        so = _sym_agg(rows, "sym_oracle")
        n_symrows = sum(1 for r in rows if "sym_blind" in r)
        n_wallpart = sum(1 for r in rows if "sym_blind" in r and r.get("n_regions", 0) > 0)
        L += [
            "", "## symbol tier (plan-symbol unit; UNIT definition is gt-wall-partitioned "
            "-- answer-key-side GT construction, disclosed; the PRED is what is un-oracled)",
            f"- wall-partitioned unit fired on {n_wallpart}/{n_symrows} scored scenes"
            + (f" -- **{n_symrows - n_wallpart} scene(s) fell back to the PLAIN 90mm "
               f"unit (no usable walls); that unit region-lumps and flatters symbol "
               f"recall (v1.1 doctrine), inspect before quoting**"
               if n_symrows != n_wallpart else " (zero plain-unit fallbacks)"),
            "| metric | BLIND pred | oracle pred |",
            "|---|---|---|",
            f"| symbol recall | **{_pct(sb['recall_sym'])}** ({sb['matched']}/{sb['n_sym']}) | "
            f"{_pct(so['recall_sym'])} ({so['matched']}/{so['n_sym']}) |",
            f"| member coverage | **{_pct(sb['member_coverage'])}** | "
            f"{_pct(so['member_coverage'])} |",
            "",
            f"(UNIT WARNING -- the committed symbol-unit headline 76.9% / 65.6% "
            f"(structured3d-symbol-unit-2026-07-10.md) is the PLAIN 90mm unit "
            f"(68,517 symbols corpus-wide); THIS lane scores the finer WALL-PARTITIONED "
            f"unit (~89,098 symbols, ~30% larger denominator by definition), so those "
            f"numbers are NOT comparable to this table at any n -- comparing them "
            f"attributes a unit change to the detector. The same-sheet oracle column "
            f"is the only reference; THIS run n={len(rows)}.)",
        ]
    L += [
        "", "## what this number IS (and is not)",
        "- BLIND means: past the drawing step, the blind arm consumes sheet ink only. "
        "The DRAWING is closed-loop (walls drawn from gt, T=100mm double lines) exactly "
        "as F2 strips are drawn from gt rot -- ink-recovery fidelity, not generalization "
        "to real sheets; production sheets need per-family threshold re-derivation, and "
        "the DOCTRINE (classify wall strokes, mask, barrier) is what transfers.",
        "- masking is segment-identity (list drop), never raster erasure -- real "
        "furniture ink is never cut (wall_aware pinned trap).",
        "- the naive arm shows what wall ink costs an unaware reader; it is the reason "
        "the production PDF lane strips thick strokes before clustering.",
        "- F4/openings are NOT a deliverable here: all arms inherit the naive read's "
        "openings, whose candidate lane saw wall ink.",
        "- detector errors are the deliverable, not noise: strips_eaten, fp/fn, coverage "
        "and the oracle->blind transition table bound exactly what the detector costs.",
        "- KNOWN fn LEAK CHANNEL: an undetected wall face stays in the blind arm's ink "
        "and can spoof the facing read on shallow elements (exact->flipped transitions "
        "in the decomposition -- pilot forensic: 230mm-deep cabinets, fn face inside "
        "the clip window). The transition table IS the measurement of this channel.",
        "- IN-SAMPLE THRESHOLDS: wall_detect's constants (gap window, ALIGN_TOL, "
        "ring-pair veto, mutual-best) were iterated against pilot slices of THIS corpus "
        "(scenes 0-199 forensics), so the corpus run is in-sample for threshold "
        "selection. The transferable claim is the doctrine (classify, mask, barrier), "
        "never the constants.",
        f"", f"engines: {LANE_VERSION} / wall_detect / {W.LANE_VERSION} / "
        f"{F2L.LANE_VERSION} / {R.READER_VERSION} / synthesizer {F2L.S.SYNTH_VERSION} "
        f"(the dependency whose drift breaks cross-sheet comparability -- pinned by "
        f"the computed equivalence line, and version-stamped here)",
    ]
    return "\n".join(L)


def main(argv):
    if len(argv) >= 4 and argv[1] == "--score":
        limit, symbol, pin_dir = None, "--no-symbol" not in argv, None
        rest = [a for a in argv[4:] if a != "--no-symbol"]
        i = 0
        while i < len(rest):
            if rest[i] == "limit" and i + 1 < len(rest) and rest[i + 1].isdigit():
                limit = int(rest[i + 1]); i += 2
            elif rest[i] == "--pin-cards" and i + 1 < len(rest):
                pin_dir = rest[i + 1]; i += 2
            else:
                i += 1
        score_corpus(argv[2], argv[3], limit=limit, symbol=symbol, pin_dir=pin_dir)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
