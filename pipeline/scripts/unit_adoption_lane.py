"""unit_adoption_lane -- OPTION C: adopt the plan-symbol unit as the headline unit.

WHAT THIS LANE PRODUCES: the OFFICIAL headline numbers of the 2D reader on this corpus
under the adopted unit (plan_symbol_unit.UNIT_GTWALL), BLIND tier (walls from
wall_detect on sheet ink), plus the full unit matrix (plain / ink-canvas instrument /
gt-canvas official x blind / oracle preds) computed in ONE run -- so every cell is
same-preds, same-run, and no number ever has to be quoted across runs or units.

THE BRIDGE, NOT A REDEFINITION: the canonical unit fixes the ink-canvas wart (the
committed instrument sized the partition canvas from the sheet's ink bbox -- see
plan_symbol_unit docstring), so its numbers differ from the committed sym_blind /
sym_oracle instrument. This lane therefore re-derives the preds EXACTLY as the
committed blind_wall_lane run (same oriented synth, same wall ink, same detector, same
barrier -- the identity pins from that lane are kept) and pins PER SCENE against the
committed blind-walls cards on THREE faces:
  1. detection tuples (n_gt, n_pred, matched, missed_ids) for BOTH arms  -> same preds;
  2. the ink-canvas symbol instrument (trimmed decompose dicts, both arms) -> the
     committed instrument reproduced bit-exact;
  3. n_regions of the ink-canvas partition                               -> same mirror.
Only with those pins ALL-GREEN is the measured ink->gt canvas DELTA (printed per run)
licensed as "the definitional fix costs X", instead of a silent unit change. A run
without --pin-cards prints OFFICIAL NUMBERS UNBRIDGED and is never green.

DEMOTION: the per-object unit (benchmark_reader detection) is printed as a DIAGNOSTIC
tier only -- it is ~saturated (13.3% reached vs ~15.4% derived ceiling, 2026-07-10b)
and no longer the lane family's headline.

TIER: BLIND headline (detector preds); oracle-walls column kept as the alarm reference
(blind > oracle on any symbol metric = contamination ALARM, never a win).

    python unit_adoption_lane.py --score <gt-dir> <out-dir> [limit N]
                                 [--pin-cards <committed-blind-walls-run-dir>]
"""
import copy
import glob
import json
import os
import sys
import time

import benchmark_reader as B
import f2_facing_lane as F2L
import plan_symbol_unit as PSU
import svg_plan_reader as R
import wall_aware_lane as W
import wall_detect as WD
from blind_wall_lane import _trim_dec
from symbol_unit_lane import (assert_matches_group_symbols, region_of_centre,
                              symbol_membership, wall_regions)
from symbol_unit_lane import decompose as su_decompose
from synth_plan_2d import SYNTH_VERSION, _as_footprint

LANE_VERSION = "unit_adoption_lane v1.0"


def _arm_pred(base_pred, elements, tier):
    """Tier-marked copy of the naive read (wall_aware_pred doctrine): a pred can never
    be mistaken for another tier's."""
    out = copy.deepcopy(base_pred)
    out["elements"] = elements
    out["meta"]["unit_adoption_lane"] = {"tier": tier, "lane": LANE_VERSION}
    return out


def _san(doc):
    el, _ = B.sanitize_elements(doc.get("elements"))
    return el


def _has_usable_walls(gt):
    """True iff at least one wall_line is non-degenerate (mirrors gt_wall_regions'
    emptiness test). `if not gt['wall_lines']` alone misses a list of all-zero-length
    walls -- such a scene has NO partition yet would not count as no_walls (review)."""
    for w in (gt.get("wall_lines") or []):
        try:
            if (float(w["x1"]), float(w["y1"])) != (float(w["x2"]), float(w["y2"])):
                return True
        except (KeyError, TypeError, ValueError):
            continue
    return False


def _det_tuple(d):
    return (d["n_gt"], d["n_pred"], d["matched"],
            sorted(d.get("missed_ids") or [], key=str))


def score_scene(gt_doc, tmp_dir, return_preds=False):
    """One scene: the committed blind-walls sheet + arms re-derived (MIRROR, pinned per
    scene against the committed cards by the caller), then the full unit matrix on the
    blind + oracle preds.

    DETECTION is scored on the F2-ENRICHED preds (pred_bv/pred_ov) EXACTLY as the
    committed blind_wall_lane did (its card_blind/card_oracle scored enriched preds), so
    the detection bridge pin is exact-by-construction. Rot is rot-INVARIANT for AABB IoU
    (footprint() is rot-aware), but _attach_rot rounds 90/270 footprints to 0.1mm, and a
    knife-edge IoU~0.5 pair could flip between the rounded (committed) and raw preds --
    enriching here removes that risk instead of asserting it away (adversarial review).
    The SYMBOL instruments (ink-canvas + official unit) use the UN-enriched sanitized
    preds, matching the committed sym_blind/sym_oracle instrument (which sanitized the
    un-enriched arm pred), so those bridge faces are exact too."""
    svg0, sstats = F2L.oriented_svg(gt_doc)
    svg, expected, n_deg = WD.append_wall_ink(svg0, gt_doc.get("wall_lines"))
    p = os.path.join(tmp_dir, "unitadopt.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)

    pred_n = R.read_sheet(p, 1.0)
    ink = R.read_ink(p)
    segs, csegs = ink["segs"], ink["curve_segs"]

    # identity pins mirrored from blind_wall_lane: the appended wall ink must be EXACTLY
    # read_ink's tail slice, and the strip slice before it must re-derive numerically --
    # a shifted slice RAISES (drift_assert), never scores shifted
    n_wall = len(expected)
    if n_wall:
        if len(segs) < n_wall:
            raise AssertionError(f"wall ink slice missing: {len(segs)} segs < {n_wall}")
        for k, (ea, eb) in enumerate(expected):
            (ga, gb) = segs[len(segs) - n_wall + k]
            if (abs(ga[0] - ea[0]) > 0.05 or abs(ga[1] - ea[1]) > 0.05
                    or abs(gb[0] - eb[0]) > 0.05 or abs(gb[1] - eb[1]) > 0.05):
                raise AssertionError(f"wall ink identity pin failed at tail index {k}")
    true_wall = set(range(len(segs) - n_wall, len(segs))) if n_wall else set()
    n_strips = sstats["strips_drawn"]
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

    det = WD.detect_walls(segs)
    wall_idx = det["wall_idx"]
    segs_b = [s for i, s in enumerate(segs) if i not in wall_idx]
    segs_o = [s for i, s in enumerate(segs) if i not in true_wall]
    el_b, _st_b = W.wall_barrier_elements(segs_b, csegs, det["centerlines"])
    el_o, _st_o = W.wall_barrier_elements(segs_o, csegs, gt_doc.get("wall_lines"))
    pred_b = _arm_pred(pred_n, el_b, "BLIND")
    pred_o = _arm_pred(pred_n, el_o, "ORACLE-WALLS")

    # detection: score the ENRICHED preds, exactly as the committed cards did
    pred_bv, _emit_b = F2L.enrich_pred_with_facing(pred_b, segs_b)
    pred_ov, _emit_o = F2L.enrich_pred_with_facing(pred_o, segs_o)
    det_b = B.score_pair(gt_doc, pred_bv)["detection"]
    det_o = B.score_pair(gt_doc, pred_ov)["detection"]

    # symbol instruments: the UN-enriched sanitized arm preds (matches committed sym_*)
    pred_b_el = _san(pred_b)
    pred_o_el = _san(pred_o)

    # committed INK-CANVAS instrument, mirrored from blind_wall_lane (the pin bridge)
    clean = _san(gt_doc)
    symbols, member_of, decor_idx, oversize_idx = symbol_membership(clean)
    assert_matches_group_symbols(clean, symbols, meta=gt_doc.get("meta"))
    regions, zone, res, n_regions_ink = wall_regions(segs, gt_doc.get("wall_lines"))
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
        symbols_u, member_u, decor_u, oversize_u = symbols, member_of, decor_idx, oversize_idx
    sym_ink_b = _trim_dec(su_decompose(clean, pred_b_el, symbols_u, member_u,
                                       decor_u, oversize_u))
    sym_ink_o = _trim_dec(su_decompose(clean, pred_o_el, symbols_u, member_u,
                                       decor_u, oversize_u))

    # the ADOPTED unit (canonical, gt-canvas) + the legacy plain unit, same preds
    unit_gt = PSU.build_unit(gt_doc, PSU.UNIT_GTWALL)
    unit_plain = PSU.build_unit(gt_doc, PSU.UNIT_PLAIN)

    row = {"n_walls_drawn": n_wall,
           "det_blind": det_b, "det_oracle": det_o,
           "n_regions_ink": int(n_regions_ink), "n_regions_gt": unit_gt["n_regions"],
           "sym_ink_blind": sym_ink_b, "sym_ink_oracle": sym_ink_o,
           "card_gt_blind": PSU.score_against_unit(unit_gt, pred_b_el),
           "card_gt_oracle": PSU.score_against_unit(unit_gt, pred_o_el),
           "card_plain_blind": PSU.score_against_unit(unit_plain, pred_b_el),
           "card_plain_oracle": PSU.score_against_unit(unit_plain, pred_o_el)}
    if return_preds:
        return row, {"pred_n": pred_n, "pred_b": pred_b, "pred_o": pred_o,
                     "pred_bv": pred_bv, "pred_ov": pred_ov,
                     "segs": segs, "segs_b": segs_b}
    return row


# ---- pins vs the committed blind-walls run --------------------------------------------------
def load_pin_cards(run_dir):
    """Committed blind_wall_lane cards.jsonl -> per scene: detection tuples of BOTH arms
    + the trimmed ink-canvas symbol instrument + its n_regions. Skipped committed rows
    are absent (they re-skip here)."""
    pins = {}
    with open(os.path.join(run_dir, "cards.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if "card_blind" not in r:
                continue
            pins[r["scene"]] = {
                "det_blind": _det_tuple(r["card_blind"]["detection"]),
                "det_oracle": _det_tuple(r["card_oracle"]["detection"]),
                "sym_blind": r.get("sym_blind"), "sym_oracle": r.get("sym_oracle"),
                "n_regions": r.get("n_regions")}
    return pins


def _jnorm(x):
    return json.loads(json.dumps(x, sort_keys=True))


def check_pin(row, pin):
    """Which pin faces disagree (empty list = the scene reproduces the committed run)."""
    bad = []
    for arm in ("blind", "oracle"):
        got = list(_det_tuple(row[f"det_{arm}"]))
        want = list(pin[f"det_{arm}"])
        # committed missed_ids were json round-tripped; normalize both sides
        if _jnorm(got) != _jnorm(want):
            bad.append(f"det_{arm}")
        if pin[f"sym_{arm}"] is None:
            bad.append(f"sym_{arm}_missing_in_pin")
        elif _jnorm(row[f"sym_ink_{arm}"]) != _jnorm(pin[f"sym_{arm}"]):
            bad.append(f"sym_{arm}")
    if pin["n_regions"] is None or int(row["n_regions_ink"]) != int(pin["n_regions"]):
        bad.append("n_regions")
    return bad


# ---- corpus run -----------------------------------------------------------------------------
def score_corpus(gt_dir, out_dir, limit=None, pin_dir=None):
    """Every *.gt.json through score_scene; cards.jsonl streamed, report.md at the end.
    One bad scene costs one row, never the run; AssertionError = drift_assert (its own
    skip bucket -- a drift alarm inside a tolerance loop must be visible in BOTH the
    skip taxonomy and the green flag, 2026-07-10b doctrine)."""
    import tempfile
    os.makedirs(out_dir, exist_ok=True)
    gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.gt.json")))
    if not gt_files:
        raise SystemExit(f"no *.gt.json under {gt_dir}")
    n_available = len(gt_files)          # BEFORE truncation -- a limit run must not read
    if limit:                            # as full coverage of a small corpus (review)
        gt_files = gt_files[:int(limit)]
    pins = load_pin_cards(pin_dir) if pin_dir else None
    pin_stats = ({"expected": len(pins), "compared": 0, "mismatch": 0, "absent": 0,
                  "mismatch_scenes": [], "faces": {}} if pins is not None else None)
    rows, skipped = [], {"error": 0, "drift_assert": 0, "units": 0, "no_walls": 0}
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
                if not _has_usable_walls(gt):        # empty OR all-degenerate wall_lines
                    skipped["no_walls"] += 1          # scored anyway; COUNTED (doctrine)
                row = {"scene": base, **score_scene(gt, td)}
                if pins is not None:
                    if base not in pins:
                        pin_stats["absent"] += 1
                        row["pin"] = "absent"
                    else:
                        bad = check_pin(row, pins[base])
                        pin_stats["compared"] += 1
                        if bad:
                            pin_stats["mismatch"] += 1
                            for f in bad:
                                pin_stats["faces"][f] = pin_stats["faces"].get(f, 0) + 1
                            if len(pin_stats["mismatch_scenes"]) < 20:
                                pin_stats["mismatch_scenes"].append(base)
                            row["pin"] = "MISMATCH:" + ",".join(bad)
                        else:
                            row["pin"] = "ok"
                # heavy per-element lists shed AFTER the pin check (pin needs missed_ids)
                for arm in ("det_blind", "det_oracle"):
                    row[arm] = {kk: row[arm][kk] for kk in
                                ("n_gt", "n_pred", "matched", "recall", "precision")}
                rows.append(row)
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            except AssertionError as e:
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
    report = render_report(rows, skipped, len(gt_files), time.time() - t0,
                           pin_stats=pin_stats, n_available=n_available, limit=limit)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nwrote {out_dir}/cards.jsonl + report.md")
    return rows, skipped


# ---- report ---------------------------------------------------------------------------------
INK_INSTRUMENT_ID = "plan-symbol/ink-canvas-instrument/committed-mirror"

# the ONE symbol metric set the doctrine's alarm covers ("ANY symbol metric")
SYMBOL_METRICS = ("symbol_recall", "member_coverage", "symbol_precision")


def _pct(v):
    return "n/a" if v is None else f"{100.0 * v:.1f}%"


def _agg_ink(rows, key):
    """Sum-based aggregate of the committed ink-canvas instrument. STAMPED with its own
    id (not a UNIT_* id): it is the committed mirror this lane pins against, NOT an
    official unit -- but rule 2 forbids an UNSTAMPED card in the matrix, so it carries
    INK_INSTRUMENT_ID and require_same_unit still refuses to average it with a unit."""
    n_sym = matched = n_pred = members = in_matched = 0
    for r in rows:
        s = r[key]["symbol"]
        n_sym += s["n_sym"]
        matched += s["matched"]
        n_pred += s["n_pred"]
        members += s["members_total"]
        in_matched += s["members_in_matched_sym"]
    return {"unit_id": INK_INSTRUMENT_ID, "n_sym": n_sym, "matched": matched,
            "n_pred": n_pred,
            "symbol_recall": (matched / n_sym) if n_sym else None,
            "symbol_precision": (matched / n_pred) if n_pred else None,
            "members_total": members,
            "member_coverage": (in_matched / members) if members else None}


def _alarm_line(agg_blind, agg_oracle, label="gt-unit"):
    """Doctrine rule 3: blind beating oracle on ANY symbol metric is contamination.
    Checks ALL of SYMBOL_METRICS (recall, member coverage, AND precision -- the earlier
    version silently omitted precision while the prose said 'any', adversarial review).
    The clear message names exactly the metrics it checked, so it can never over-claim."""
    hot = []
    for m in SYMBOL_METRICS:
        b, o = agg_blind.get(m), agg_oracle.get(m)
        if b is not None and o is not None and b > o:
            hot.append(m)
    checked = ", ".join(SYMBOL_METRICS)
    if hot:
        return (f"**ALARM ({label}): blind > oracle on " + ", ".join(hot)
                + " -- contamination signal; DO NOT QUOTE until explained.**")
    return f"blind <= oracle on all checked symbol metrics [{checked}] ({label}); alarm clear."


def render_report(rows, skipped, n_total, secs, pin_stats=None, n_available=None,
                  limit=None):
    if not rows:
        return "# unit_adoption_lane\n\nno gt scored -- " + json.dumps(skipped)

    agg_gt_b = PSU.agg_cards([r["card_gt_blind"] for r in rows])
    agg_gt_o = PSU.agg_cards([r["card_gt_oracle"] for r in rows])
    agg_pl_b = PSU.agg_cards([r["card_plain_blind"] for r in rows])
    agg_pl_o = PSU.agg_cards([r["card_plain_oracle"] for r in rows])
    agg_ink_b = _agg_ink(rows, "sym_ink_blind")
    agg_ink_o = _agg_ink(rows, "sym_ink_oracle")

    po = {"n_gt": 0, "matched_b": 0, "n_pred_b": 0, "matched_o": 0, "n_pred_o": 0}
    for r in rows:
        po["n_gt"] += r["det_blind"]["n_gt"]
        po["matched_b"] += r["det_blind"]["matched"]
        po["n_pred_b"] += r["det_blind"]["n_pred"]
        po["matched_o"] += r["det_oracle"]["matched"]
        po["n_pred_o"] += r["det_oracle"]["n_pred"]

    n_region_delta_scenes = sum(1 for r in rows
                                if r["n_regions_ink"] != r["n_regions_gt"])
    # scenes where the gt partition never split the canvas -> plain-90mm geometry scored
    # under the GTWALL stamp (plain grouping FLATTERS recall via region-lumping -- v1.1
    # doctrine). n_regions_gt: 0 = no usable walls (plain grouping); 1 = walls present
    # but the barrier did not divide the element region. Both are "no real partition".
    n_trivial = sum(1 for r in rows if int(r["n_regions_gt"]) <= 1)
    n_wallless = sum(1 for r in rows if int(r["n_regions_gt"]) == 0)

    def _delta(a, b):
        return None if (a is None or b is None) else (a - b)
    d_nsym = agg_gt_b["n_sym"] - agg_ink_b["n_sym"]
    d_recall = _delta(agg_gt_b["symbol_recall"], agg_ink_b["symbol_recall"])
    d_cov = _delta(agg_gt_b["member_coverage"], agg_ink_b["member_coverage"])

    def _pp(v):
        return "n/a" if v is None else f"{v * 100:+.2f}pp"

    unscored_pinned = (pin_stats["expected"] - pin_stats["compared"]
                       if pin_stats else None)
    truncated = bool(limit) and n_available is not None and n_available > n_total
    green = (skipped["error"] == 0 and skipped["drift_assert"] == 0
             and pin_stats is not None and pin_stats["mismatch"] == 0
             and pin_stats["absent"] == 0 and unscored_pinned == 0
             and not truncated)               # a partial run is NEVER the corpus headline
    status = "GREEN" if green else "NOT GREEN"
    quotable = "QUOTABLE" if green else "UNQUOTABLE -- run is NOT GREEN"

    L = []
    L.append("# unit_adoption_lane -- OPTION C: the plan-symbol unit IS the headline unit")
    L.append("")
    L.append(f"**UNIT: {PSU.UNIT_GTWALL}** (answer-key-side GT construction; canvas = "
             f"f(gt) only -- see plan_symbol_unit doctrine). **TIER: BLIND preds** "
             f"(wall_detect on sheet ink; oracle column = alarm reference only).")
    L.append("")
    cover_note = (f"{len(rows)} scored / {n_total}"
                  + (f" -- **PARTIAL RUN: limit={limit} of {n_available} available; "
                     f"these are NOT corpus numbers**" if truncated else
                     (f" (full corpus of {n_available})" if n_available else "")))
    L.append(f"- scenes: {cover_note}; skipped {json.dumps(skipped)}")
    L.append(f"- no-real-partition scenes (n_regions_gt<=1): {n_trivial}/{len(rows)} "
             f"({n_wallless} with no usable walls at all) -- these score PLAIN-90mm "
             f"geometry under the GTWALL stamp; plain grouping flatters recall via "
             f"region-lumping, so inspect this share before quoting the headline")
    L.append(f"- ALL-GREEN reconciliation: {status} "
             f"(errors {skipped['error']}, drift_asserts {skipped['drift_assert']}, "
             + (f"pin mismatches {pin_stats['mismatch']}, absent {pin_stats['absent']}, "
                f"pinned-but-unscored {unscored_pinned}"
                if pin_stats else "pins NOT RUN")
             + (f", truncated {truncated}" if truncated else "") + ")")
    if pin_stats:
        L.append(f"- BRIDGE PINS (COMPUTED per scene vs the committed blind-walls run; "
                 f"faces: detection x2 arms, ink-canvas symbol instrument x2, n_regions): "
                 f"{pin_stats['compared']} compared, **{pin_stats['mismatch']} "
                 f"mismatch(es)**, {pin_stats['absent']} absent"
                 + (f"; mismatch faces {json.dumps(pin_stats['faces'])}, first scenes "
                    f"{pin_stats['mismatch_scenes']}" if pin_stats["mismatch"] else ""))
    else:
        L.append("- **OFFICIAL NUMBERS UNBRIDGED -- BRIDGE PINS NOT RUN (no --pin-cards). "
                 "The canonical unit differs from the committed instrument BY DEFINITION; "
                 "without the per-scene pins this run's numbers must not be quoted.**")
    L.append(f"- wall-clock {secs:.0f}s")
    L.append("")
    L.append(f"## OFFICIAL HEADLINE -- symbol tier ({PSU.UNIT_GTWALL}) -- {quotable}")
    L.append("")
    L.append("| metric | **BLIND (the headline)** | oracle-walls (alarm ref) |")
    L.append("|---|---|---|")
    L.append(f"| symbol recall | **{_pct(agg_gt_b['symbol_recall'])}** "
             f"({agg_gt_b['matched']}/{agg_gt_b['n_sym']}) | "
             f"{_pct(agg_gt_o['symbol_recall'])} "
             f"({agg_gt_o['matched']}/{agg_gt_o['n_sym']}) |")
    L.append(f"| member coverage | **{_pct(agg_gt_b['member_coverage'])}** | "
             f"{_pct(agg_gt_o['member_coverage'])} |")
    L.append(f"| symbol precision | **{_pct(agg_gt_b['symbol_precision'])}** | "
             f"{_pct(agg_gt_o['symbol_precision'])} |")
    L.append("")
    L.append(f"- {_alarm_line(agg_gt_b, agg_gt_o, 'gt-unit')}")
    L.append("")
    L.append("## unit matrix -- same preds, every unit, computed THIS run")
    L.append("")
    L.append("| unit (id, corpus n_sym) | blind recall / coverage | oracle recall / coverage | alarm |")
    L.append("|---|---|---|---|")
    for uid, ab, ao in ((PSU.UNIT_PLAIN, agg_pl_b, agg_pl_o),
                        (INK_INSTRUMENT_ID + " (committed def)", agg_ink_b, agg_ink_o),
                        ("**" + PSU.UNIT_GTWALL + " -- OFFICIAL**", agg_gt_b, agg_gt_o)):
        al = "hot" if "ALARM" in _alarm_line(ab, ao) else "clear"
        L.append(f"| {uid} ({ab['n_sym']}) | {_pct(ab['symbol_recall'])} "
                 f"/ {_pct(ab['member_coverage'])} | {_pct(ao['symbol_recall'])} "
                 f"/ {_pct(ao['member_coverage'])} | {al} |")
    L.append("")
    L.append("UNIT LAW: numbers from different rows are NOT comparable at any n -- a "
             "delta across rows is a unit-definition change, not a reader change. "
             "plan_symbol_unit.require_same_unit RAISES on any attempt to average two "
             "rows together; the ONE sanctioned cross-row subtraction is the canvas "
             "delta below (ink-instrument -> gt-unit), which exists precisely to price "
             "the definition change and is licensed only when the bridge pins are GREEN.")
    L.append("")
    L.append("## canvas delta -- the definitional fix, MEASURED (ink-canvas -> gt-canvas)")
    L.append("")
    licensed = (green and pin_stats is not None)
    L.append(f"- n_sym: {agg_ink_b['n_sym']} (ink) -> {agg_gt_b['n_sym']} (gt), "
             f"delta {d_nsym:+d}")
    L.append(f"- scenes where the partition's region count changed: "
             f"{n_region_delta_scenes} / {len(rows)}")
    L.append(f"- blind headline shift: recall {_pp(d_recall)}, member coverage "
             f"{_pp(d_cov)} -- the price/gain of freezing the canvas to gt.json")
    if licensed:
        L.append("- LICENSED: the bridge pins above are GREEN, so this cross-unit "
                 "subtraction is the sanctioned measure of the definition change.")
    else:
        L.append("- **UNLICENSED: the bridge pins are NOT GREEN (or were not run) -- "
                 "the ink-instrument column is unverified, so this delta must NOT be "
                 "quoted as the definitional cost until the pins are clean.**")
    L.append("")
    L.append("## per-object unit -- DEMOTED to diagnostic (never the headline)")
    L.append("")
    L.append(f"- detection recall {_pct(po['matched_b'] / po['n_gt'] if po['n_gt'] else None)} "
             f"({po['matched_b']}/{po['n_gt']}), precision "
             f"{_pct(po['matched_b'] / po['n_pred_b'] if po['n_pred_b'] else None)} "
             f"(blind); oracle matched {po['matched_o']}. UNIT: per-object detection "
             f"(benchmark_reader, IoU 0.5) -- a DIFFERENT unit from the headline; never "
             f"compare the two numbers.")
    L.append("- the unit is ~SATURATED: ~15.4% derived structural ceiling vs 13.3% "
             "reached (symbol_unit lane 2026-07-10b) -- one-to-one matching yields ~1 "
             "match per symbol, so progress on it measures the unit, not the reader. "
             "It remains the committed detection metric elsewhere, quoted with its own "
             "label; this lane demotes it in the HEADLINE only.")
    L.append("")
    L.append("## doctrine (what 'adopted' means)")
    L.append("")
    L.append(f"1. the headline unit is {PSU.UNIT_GTWALL}: symbol recall + member coverage "
             f"+ symbol precision.")
    L.append("2. every quoted number carries unit_id + n_sym; cross-unit averaging RAISES "
             "(require_same_unit). The lone sanctioned cross-unit arithmetic is the "
             "green-gated canvas delta.")
    L.append("3. blind > oracle on ANY of [" + ", ".join(SYMBOL_METRICS) + "] is an "
             "ALARM, never a win -- checked on every matrix row (see 'alarm' column).")
    L.append("4. a corpus with NO usable walls in ANY scene would headline "
             + PSU.UNIT_PLAIN + " under its own id (see the no-real-partition line "
             "above: " + f"{n_wallless}/{len(rows)} here); a scene with unusable walls "
             "inside this wall-bearing corpus keeps the gt-wall id, its partition "
             "collapsing to plain grouping (n_regions_gt 0), disclosed not hidden.")
    L.append("5. the unit is a pure function of gt.json (no ink, no preds in the API), "
             "and its /v1 constants are frozen (plan_symbol_unit._assert_frozen raises "
             "on drift).")
    L.append("")
    if n_wallless == len(rows):
        L.append("**WARNING: NO scene in this corpus has usable walls -- the OFFICIAL "
                 "GTWALL headline is plain-90mm geometry throughout. Per doctrine rule "
                 "4 this corpus should be headlined under " + PSU.UNIT_PLAIN + ".**")
        L.append("")
    L.append("## what this number IS (and is not)")
    L.append("")
    L.append("- CLOSED LOOP: same oriented synth + drawn gt walls as the committed "
             "blind-walls run -- ink-recovery through a real detector, not "
             "generalization; detector constants remain IN-SAMPLE (disclosed there).")
    L.append("- the unit consumes gt wall_lines on the ANSWER-KEY side only; pred tier "
             "is orthogonal and stamped in every pred's meta.")
    L.append("- decor (<150mm) and single-object merged blobs stay OUT of the symbol "
             "unit and IN the per-object denominator -- no denominator ever shrank.")
    L.append("")
    L.append(f"engines: {LANE_VERSION} / {PSU.UNIT_MODULE_VERSION} / "
             f"{WD.__name__} + {W.LANE_VERSION} / {F2L.LANE_VERSION} / "
             f"{R.READER_VERSION} (UNEDITED) / {SYNTH_VERSION}")
    return "\n".join(L)


def main(argv):
    if len(argv) >= 4 and argv[1] == "--score":
        limit, pin_dir = None, None
        rest = argv[4:]
        i = 0
        while i < len(rest):
            if rest[i] == "--pin-cards" and i + 1 < len(rest):
                pin_dir = rest[i + 1]
                i += 2
            elif rest[i].isdigit():
                limit = int(rest[i])
                i += 1
            elif rest[i] == "limit" and i + 1 < len(rest):
                limit = int(rest[i + 1])
                i += 2
            else:
                raise SystemExit(f"unknown arg: {rest[i]}")
        score_corpus(argv[2], argv[3], limit=limit, pin_dir=pin_dir)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
