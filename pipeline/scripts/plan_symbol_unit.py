"""plan_symbol_unit -- the OFFICIAL plan-symbol scoring unit (option C: unit adoption).

WHY THIS MODULE EXISTS: symbol_unit_lane (2026-07-10b) measured the per-object scoring
unit as ~SATURATED (13.3% reached vs ~15.4% derived structural ceiling; 55.5% of the
gap is decor below the reader's own 150mm screen and 26.0% is sub-object granularity of
symbols the reader DID match). The plan-symbol unit is therefore adopted as the headline
scoring unit; this module is its single, version-stamped definition. Lanes import from
HERE -- a symbol-tier number computed anywhere else is a mirror and must be pinned.

UNIT IDS (a number quoted without its unit id + n_sym is unquotable):
  UNIT_PLAIN  = "plan-symbol/plain-90mm/v1"
  UNIT_GTWALL = "plan-symbol/gt-wall-partitioned-90mm/v1"   <- THE headline unit

DEFINITION (both variants; grouping primitives imported from synth_plan_2d v1.1 and
symbol_unit_lane -- never re-implemented):
  members  : GT elements passing _member_class (thin <150mm axis -> decor; oversize
             single -> merged blob); decor + oversize stay OUT of the symbol unit but
             IN the per-object denominator (never shrink a denominator).
  fuse     : single-linkage union at edge gap <= FUSE_GAP_MM (90mm) between members.
  partition (UNIT_GTWALL only): two members may union only when their footprint centres
             lie in the same gt-wall region (centre ON the dilated barrier = wildcard).
             A plan symbol never spans a wall; the plain unit's cross-wall mega-chains
             are grouping artifacts (measured: 17,673 members = 4.6pp of GT).
  canvas   : derived from GT GEOMETRY ONLY (sanitized element footprints + wall
             endpoints, ZONE_PAD_MM pad, wall_barrier_elements' res formula/dilation).
             The committed ink-canvas instrument (symbol_unit_lane.wall_regions) sizes
             the canvas from the SHEET'S INK bbox, so the same scene's unit shifted
             with what the reader happened to read (corpus n_sym 89,098 vs 89,108
             between two committed lanes). An answer key whose denominator moves with
             the pred sheet is not frozen; v1 canvas is a pure function of gt.json.
  scores   : symbol recall = matched symbols / n_sym; member coverage = members of
             matched symbols / members total; symbol precision = matched / kept preds.
             Matching = benchmark_reader.match_elements on symbol union-AABBs (IoU 0.5,
             one-to-one) -- same machinery as the per-object unit, coarser boxes.

DOCTRINE (the adoption; each rule has a pinned test or a report instrument):
  1. HEADLINE = UNIT_GTWALL symbol recall + member coverage. The per-object unit is
     DEMOTED to a diagnostic tier: always print it labeled, never headline it.
  2. Every quoted number carries its unit_id and n_sym. Cross-unit comparison RAISES
     (require_same_unit) -- the 2026-07-10c near-miss quoted the PLAIN 76.9/65.6 next
     to wall-partitioned 67.0/64.7 (~30% finer denominator by definition).
  3. blind > oracle on any symbol metric is an ALARM (contamination), never a win.
  4. A corpus without wall_lines scores UNIT_PLAIN under its own id -- the ids keep
     the numbers from silently mixing. A scene with unusable walls inside a UNIT_GTWALL
     corpus keeps the UNIT_GTWALL id (partition is trivially one region -- that IS the
     definition on such a scene, not a fallback to a different unit).
  5. The unit is pred-independent BY API: build_unit(gt_doc) takes no ink, no preds.

TIER NOTE: the unit consumes gt wall_lines on the ANSWER-KEY side only (a GT construction,
like the GT boxes themselves). Pred tier (blind/oracle walls) is a property of the PREDS
and is disclosed wherever scores are quoted -- unit and tier are orthogonal axes.
"""
import scipy.ndimage as ndi

import benchmark_reader as B
import plan_cluster as PC
import svg_plan_reader as R
import wall_aware_lane as W
from symbol_unit_lane import THIN_MM
from symbol_unit_lane import (assert_matches_group_symbols, decompose, region_of_centre,
                              symbol_membership)
from synth_plan_2d import FUSE_GAP_MM, _as_footprint

UNIT_MODULE_VERSION = "plan_symbol_unit v1.0"

UNIT_PLAIN = "plan-symbol/plain-90mm/v1"
UNIT_GTWALL = "plan-symbol/gt-wall-partitioned-90mm/v1"

# The '/v1' ids above are a PROMISE: this exact grouping + canvas geometry. But the unit
# is built from constants that live in OTHER modules (the reader, the barrier lane, the
# synth grouping) -- edit one of them and the answer key would shift SILENTLY under the
# same id (adversarial review 2026-07-10, a major doctrine finding). assert_matches_
# group_symbols cannot catch it: bump FUSE_GAP_MM and the mirror AND its reference move
# together. So the '/v1' contract is these frozen values; build_unit checks the live
# imports against them and RAISES if any drifted, forcing a version bump to accompany a
# constant change. (A tuned constant is a NEW unit, never a silent re-definition of v1.)
UNIT_CONSTANTS_V1 = {
    "FUSE_GAP_MM": 90.0, "THIN_MM": 150.0, "ZONE_PAD_MM": 100.0,
    "BASE_RES_MM": 6.0, "MAX_RASTER_PX": 3000, "BARRIER_DILATE_PX": 1,
}


class UnitMismatch(ValueError):
    """Raised on any cross-unit comparison or an unstamped card (doctrine rule 2)."""


class UnitConstantsDrift(AssertionError):
    """Raised when a live constant the unit is built from drifted from the frozen /v1
    contract -- the answer key changed and the version id did not (doctrine rule).
    """


def _assert_frozen():
    live = {"FUSE_GAP_MM": FUSE_GAP_MM, "THIN_MM": THIN_MM, "ZONE_PAD_MM": R.ZONE_PAD_MM,
            "BASE_RES_MM": R.BASE_RES_MM, "MAX_RASTER_PX": R.MAX_RASTER_PX,
            "BARRIER_DILATE_PX": W.BARRIER_DILATE_PX}
    drift = {k: (UNIT_CONSTANTS_V1[k], live[k]) for k in UNIT_CONSTANTS_V1
             if live[k] != UNIT_CONSTANTS_V1[k]}
    if drift:
        raise UnitConstantsDrift(
            "unit /v1 constant(s) drifted (want, live): " + repr(drift)
            + " -- a tuned constant is a NEW unit; bump the version id, do not "
              "silently redefine v1")


def gt_wall_regions(fps, wall_lines):
    """(regions, zone, res, n_regions) on a canvas derived from GT geometry ONLY:
    sanitized element footprints + wall endpoints, ZONE_PAD_MM pad, and the exact
    res/raster/dilation wall_barrier_elements uses. Same constants as the committed
    ink-canvas mirror (symbol_unit_lane.wall_regions); ONLY the canvas source differs,
    which makes the partition -- and therefore the unit -- a pure function of gt.json.
    None when no usable walls (partition trivially one region)."""
    wsegs = [[(float(w["x1"]), float(w["y1"])), (float(w["x2"]), float(w["y2"]))]
             for w in (wall_lines or [])]
    wsegs = [s for s in wsegs if s[0] != s[1]]
    if not wsegs:
        return None, None, None, 0
    xs = ([float(f["x"]) for f in fps] + [float(f["x"]) + float(f["w"]) for f in fps]
          + [p[0] for s in wsegs for p in s])
    ys = ([float(f["y"]) for f in fps] + [float(f["y"]) + float(f["d"]) for f in fps]
          + [p[1] for s in wsegs for p in s])
    zone = (min(xs) - R.ZONE_PAD_MM, min(ys) - R.ZONE_PAD_MM,
            max(xs) + R.ZONE_PAD_MM, max(ys) + R.ZONE_PAD_MM)
    extent = max(zone[2] - zone[0], zone[3] - zone[1])
    res = max(R.BASE_RES_MM, extent / R.MAX_RASTER_PX)
    # res is set by the LONGEST axis; a very long wall + a narrow element column can drive
    # the SHORT axis below res, giving int()=0 -> a 0-width raster -> region_of_centre
    # clips to col -1 -> IndexError (adversarial review repro). One-pixel floor keeps the
    # canvas non-degenerate; such a scene has no meaningful partition anyway (n_regions
    # collapses to 1) and is disclosed as a trivial partition downstream.
    Wc = max(1, int((zone[2] - zone[0]) / res))
    Hc = max(1, int((zone[3] - zone[1]) / res))
    barrier = PC._rasterize(wsegs, zone, Wc, Hc)
    st = ndi.generate_binary_structure(2, 2)
    barrier = ndi.binary_dilation(barrier, structure=st, iterations=W.BARRIER_DILATE_PX)
    regions, n_regions = ndi.label(~barrier, structure=st)
    return regions, zone, res, int(n_regions)


def build_unit(gt_doc, unit_id=UNIT_GTWALL):
    """The answer key for one scene: a pure function of gt_doc (no ink, no preds --
    doctrine rule 5). The plain grouping is always mirrored + pinned against
    group_symbols (loud drift assert) even when the partitioned variant is returned."""
    if unit_id not in (UNIT_PLAIN, UNIT_GTWALL):
        raise UnitMismatch(f"unknown unit id: {unit_id!r}")
    _assert_frozen()          # the /v1 answer key is these constants; drift RAISES
    clean, malformed = B.sanitize_elements(gt_doc.get("elements"))
    symbols, member_of, decor_idx, oversize_idx = symbol_membership(clean)
    assert_matches_group_symbols(clean, symbols, meta=gt_doc.get("meta"))
    n_regions = 0
    if unit_id == UNIT_GTWALL:
        fps = [_as_footprint(e) for e in clean]
        regions, zone, res, n_regions = gt_wall_regions(fps, gt_doc.get("wall_lines"))
        if regions is not None:
            reg = {i: region_of_centre(f, regions, zone, res) for i, f in enumerate(fps)}
            member_clean_idx = sorted(member_of)

            def allowed(i, j):
                a, b = reg[member_clean_idx[i]], reg[member_clean_idx[j]]
                return a == 0 or b == 0 or a == b

            symbols_u, member_u, decor_u, oversize_u = symbol_membership(clean,
                                                                         allowed=allowed)
            if (decor_u, oversize_u) != (decor_idx, oversize_idx):
                raise AssertionError("wall partition changed the member screen")
            symbols, member_of = symbols_u, member_u
    return {"unit_id": unit_id, "clean": clean, "malformed_gt": len(malformed),
            "symbols": symbols, "member_of": member_of, "decor_idx": decor_idx,
            "oversize_idx": oversize_idx, "n_regions": int(n_regions),
            "n_sym": len(symbols),
            "members_total": len(clean) - len(decor_idx) - len(oversize_idx)}


def score_against_unit(unit, pred_elements):
    """One pred side vs the unit -> a unit-STAMPED card (counts + derived ratios).
    pred_elements must already be sanitized (benchmark_reader.sanitize_elements)."""
    dec = decompose(unit["clean"], pred_elements, unit["symbols"], unit["member_of"],
                    unit["decor_idx"], unit["oversize_idx"])
    s = dec["symbol"]
    return {"unit_id": unit["unit_id"], "n_sym": s["n_sym"],
            "symbol_recall": (s["matched"] / s["n_sym"]) if s["n_sym"] else None,
            "member_coverage": ((s["members_in_matched_sym"] / s["members_total"])
                                if s["members_total"] else None),
            "symbol_precision": (s["matched"] / s["n_pred"]) if s["n_pred"] else None,
            "perobj": dec["perobj"], "matched_thin": dec["matched_thin"],
            "symbol": s, "buckets": dec["buckets"],
            "sym_iou_hist": dec["sym_iou_hist"], "pred_purity": dec["pred_purity"]}


def require_same_unit(card_a, card_b):
    """Doctrine rule 2: comparing numbers from different units is an ERROR, not a
    footnote. Returns the shared unit_id so callers can stamp derived tables."""
    ua, ub = (card_a or {}).get("unit_id"), (card_b or {}).get("unit_id")
    if not ua or not ub:
        raise UnitMismatch("card without a unit_id is unquotable")
    if ua != ub:
        raise UnitMismatch(f"cross-unit comparison: {ua} vs {ub} -- a delta between "
                           f"them attributes a unit-definition change to the reader")
    return ua


def agg_cards(cards):
    """Sum-based corpus aggregate (never ratio-averaging); refuses to mix units."""
    cards = [c for c in cards if c]
    if not cards:
        return None
    for c in cards[1:]:
        require_same_unit(cards[0], c)
    n_sym = matched = n_pred = members = in_matched = 0
    for c in cards:
        s = c["symbol"]
        n_sym += s["n_sym"]
        matched += s["matched"]
        n_pred += s["n_pred"]
        members += s["members_total"]
        in_matched += s["members_in_matched_sym"]
    return {"unit_id": cards[0]["unit_id"], "n_sym": n_sym, "matched": matched,
            "n_pred": n_pred,
            "symbol_recall": (matched / n_sym) if n_sym else None,
            "symbol_precision": (matched / n_pred) if n_pred else None,
            "members_total": members, "members_in_matched": in_matched,
            "member_coverage": (in_matched / members) if members else None}
