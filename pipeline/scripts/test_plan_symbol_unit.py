"""Tests for plan_symbol_unit -- the adopted headline unit's load-bearing pins.

  - PURITY: build_unit is a pure function of gt.json (no ink/pred in the API; two
    builds are byte-identical);
  - THE MOTIVATING WART, REPRODUCED: the committed ink-canvas partition changes when
    unrelated ink extends the sheet bbox (res coarsens -> a near-wall centre lands ON
    the dilated barrier -> wildcard union), while the gt-canvas unit is immune;
  - PARTITION SEMANTICS: the gt-wall unit keeps a 60mm-gap cross-wall pair as two
    symbols where the plain unit fuses them; no walls -> plain geometry under the
    SAME gt-wall id; the member screen is partition-invariant;
  - SCORE FORMULAS: recall / member coverage / precision on a hand-built case, and
    buckets always sum to n_gt;
  - UNIT LAW: require_same_unit raises on cross-unit comparison and unstamped cards;
    agg_cards refuses to mix units.
"""
import json

import plan_symbol_unit as PSU
import symbol_unit_lane as SU
from synth_plan_2d import _as_footprint


def _el(id_, x, y, w, d):
    return {"id": id_, "x": float(x), "y": float(y), "w": float(w), "d": float(d)}


def _wall(x1, y1, x2, y2):
    return {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def _doc(elements, walls=None):
    return {"meta": {"units": "mm", "n_elements": len(elements)},
            "elements": [dict(e) for e in elements], "openings": [],
            "glazing_lines": [], "wall_lines": list(walls or [])}


# closed two-room box: ring + divider at x=840; 'a' left, 'b' right with its centre
# only 20mm right of the divider (the near-wall centre the wart needs)
def _two_room_doc():
    return _doc([_el("a", 0, 0, 700, 600), _el("b", 760, 0, 200, 600)],
                walls=[_wall(-200, -200, 1900, -200), _wall(1900, -200, 1900, 800),
                       _wall(1900, 800, -200, 800), _wall(-200, 800, -200, -200),
                       _wall(840, -200, 840, 800)])


def _unit_geom(unit):
    return json.dumps([{k: s[k] for k in ("id", "x", "y", "w", "d", "n_members")}
                       for s in unit["symbols"]], sort_keys=True)


def test_unit_is_pure_and_deterministic():
    gt = _two_room_doc()
    u1 = PSU.build_unit(gt, PSU.UNIT_GTWALL)
    u2 = PSU.build_unit(gt, PSU.UNIT_GTWALL)
    assert _unit_geom(u1) == _unit_geom(u2)
    assert u1["n_regions"] == u2["n_regions"]
    assert u1["unit_id"] == PSU.UNIT_GTWALL


def test_gtwall_splits_cross_wall_pair_plain_fuses():
    gt = _two_room_doc()
    u_gt = PSU.build_unit(gt, PSU.UNIT_GTWALL)
    u_pl = PSU.build_unit(gt, PSU.UNIT_PLAIN)
    assert u_pl["n_sym"] == 1                    # 60mm gap fuses under plain 90mm
    assert u_gt["n_sym"] == 2                    # divider keeps the rooms apart
    assert u_gt["n_regions"] >= 3                # left / right / outside
    assert u_gt["members_total"] == u_pl["members_total"] == 2


def test_ink_canvas_wart_reproduced_gt_canvas_immune():
    """The committed instrument's partition depends on the SHEET'S ink bbox: append one
    far-away ink segment (nothing else changes), the raster res coarsens, the dilated
    barrier band widens past b's 20mm-off-wall centre -> wildcard -> the pair fuses.
    The canonical unit never sees ink, so it cannot move."""
    gt = _two_room_doc()
    clean = PSU.build_unit(gt, PSU.UNIT_PLAIN)["clean"]
    fps = [_as_footprint(e) for e in clean]

    def partitioned_n_sym(segs):
        regions, zone, res, _n = SU.wall_regions(segs, gt["wall_lines"])
        assert regions is not None
        reg = {i: SU.region_of_centre(f, regions, zone, res) for i, f in enumerate(fps)}
        symbols0, member_of, _dec, _ov = SU.symbol_membership(clean)
        idx = sorted(member_of)

        def allowed(i, j):
            a, b = reg[idx[i]], reg[idx[j]]
            return a == 0 or b == 0 or a == b

        symbols, _m, _d, _o = SU.symbol_membership(clean, allowed=allowed)
        return len(symbols), res

    tight = [[(-200.0, -200.0), (1900.0, 800.0)]]          # ink bbox ~ the gt scene
    far = tight + [[(150000.0, 0.0), (150001.0, 1.0)]]     # one stray far-away stroke
    n_tight, res_tight = partitioned_n_sym(tight)
    n_far, res_far = partitioned_n_sym(far)
    assert res_far > res_tight                              # canvas moved with the ink
    assert n_tight == 2 and n_far == 1                      # ...and so did the UNIT
    # the canonical unit has no ink parameter at all; same answer both times
    assert PSU.build_unit(gt, PSU.UNIT_GTWALL)["n_sym"] == 2


def test_no_walls_keeps_gtwall_id_with_plain_geometry():
    gt = _doc([_el("a", 0, 0, 700, 600), _el("b", 760, 0, 200, 600)])
    u_gt = PSU.build_unit(gt, PSU.UNIT_GTWALL)
    u_pl = PSU.build_unit(gt, PSU.UNIT_PLAIN)
    assert u_gt["n_regions"] == 0
    assert _unit_geom(u_gt) == _unit_geom(u_pl)   # geometry identical...
    assert u_gt["unit_id"] == PSU.UNIT_GTWALL     # ...but the id never silently flips


def test_score_formulas_and_bucket_conservation():
    gt = _two_room_doc()
    unit = PSU.build_unit(gt, PSU.UNIT_GTWALL)
    pred = [_el("p0", 0, 0, 700, 600)]                     # exact match of 'a' only
    card = PSU.score_against_unit(unit, pred)
    assert card["unit_id"] == PSU.UNIT_GTWALL
    assert card["n_sym"] == 2
    assert card["symbol"]["matched"] == 1
    assert abs(card["symbol_recall"] - 0.5) < 1e-9
    assert abs(card["member_coverage"] - 0.5) < 1e-9
    assert abs(card["symbol_precision"] - 1.0) < 1e-9
    assert sum(card["buckets"].values()) == len(unit["clean"])
    assert card["perobj"]["matched"] == 1                  # per-object stays diagnostic


def test_unit_law_raises_on_cross_unit_and_unstamped():
    gt = _two_room_doc()
    pred = [_el("p0", 0, 0, 700, 600)]
    c_gt = PSU.score_against_unit(PSU.build_unit(gt, PSU.UNIT_GTWALL), pred)
    c_pl = PSU.score_against_unit(PSU.build_unit(gt, PSU.UNIT_PLAIN), pred)
    try:
        PSU.require_same_unit(c_gt, c_pl)
        raise AssertionError("cross-unit comparison did not raise")
    except PSU.UnitMismatch:
        pass
    try:
        PSU.require_same_unit(c_gt, {"symbol_recall": 0.5})
        raise AssertionError("unstamped card did not raise")
    except PSU.UnitMismatch:
        pass
    try:
        PSU.agg_cards([c_gt, c_pl])
        raise AssertionError("agg_cards mixed units")
    except PSU.UnitMismatch:
        pass
    agg = PSU.agg_cards([c_gt, c_gt])
    assert agg["unit_id"] == PSU.UNIT_GTWALL and agg["n_sym"] == 4


def test_unknown_unit_id_rejected():
    try:
        PSU.build_unit(_two_room_doc(), "plan-symbol/typo/v9")
        raise AssertionError("unknown unit id accepted")
    except PSU.UnitMismatch:
        pass


def test_frozen_constants_drift_raises():
    """The '/v1' id is a promise about the grouping constants; if one drifts, build_unit
    must RAISE (a tuned constant is a NEW unit, not a silent redefinition of v1)."""
    gt = _two_room_doc()
    PSU.build_unit(gt, PSU.UNIT_GTWALL)               # baseline: no drift, no raise
    saved = PSU.FUSE_GAP_MM
    try:
        PSU.FUSE_GAP_MM = 91.0                         # bump the fuse gap
        try:
            PSU.build_unit(gt, PSU.UNIT_GTWALL)
            raise AssertionError("constant drift did not raise")
        except PSU.UnitConstantsDrift:
            pass
    finally:
        PSU.FUSE_GAP_MM = saved
    PSU.build_unit(gt, PSU.UNIT_GTWALL)               # restored: raises no more


def test_gt_wall_regions_no_crash_on_degenerate_raster():
    """C6 repro: a very long wall + a narrow element column drives one raster axis to
    int()=0; region_of_centre then clipped to col -1 and IndexError'd. The 1px floor
    keeps build_unit total over gt.json (its documented contract)."""
    gt = _doc([_el("a", 100, 0, 500, 500), _el("b", 100, 700, 500, 500)],
              walls=[_wall(0, 0, 0, 3_000_000)])       # 3 km wall, 800mm-wide zone
    unit = PSU.build_unit(gt, PSU.UNIT_GTWALL)         # must not raise (was IndexError)
    assert unit["unit_id"] == PSU.UNIT_GTWALL
    assert unit["n_sym"] >= 1
    # the raster is non-degenerate (>=1px each axis); on this pathological zone the whole
    # 1px column is barrier, so n_regions collapses to 0 (no partition) -- but no crash
    regions, _z, _r, n = PSU.gt_wall_regions(
        [PSU._as_footprint(e) for e in unit["clean"]], gt["wall_lines"])
    assert regions is not None and regions.shape[1] >= 1 and n >= 0
