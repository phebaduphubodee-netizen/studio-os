"""Unit tests for casement_sheers.py (ELEMENT 6 D-E6-1) + the build_room wiring pins.
Run: python -m pytest test_casement_sheers.py -q
"""
import copy
import json
import math
import os

import pytest

import casement_sheers as CS

HERE = os.path.dirname(__file__)
CANON = os.path.join(HERE, "../../projects/PRJ-2026-002_c001-house/03_layout/"
                           "master-suite.CANONICAL.spec.json")


def _spec(**kw):
    s = {
        "room": {
            "outline_mm": [[0, 0], [4000, 0], [4000, 6000], [0, 6000]],
            "ceiling_mm": 2800,
            "openings": [
                {"id": "win-a", "type": "glass", "rect": [0, 1000, 0, 1600],
                 "sill_mm": 1000, "head_mm": 2200},
                {"id": "win-b", "type": "glass", "rect": [0, 3000, 0, 3600],
                 "sill_mm": 1000, "head_mm": 2200},
                {"id": "door-x", "type": "door", "rect": [4000, 2000, 4000, 3000],
                 "head_mm": 2100},
            ],
        },
        "curtains": {"render_state": {"sheer_alpha": 0.38}},
        "casement_sheers": {"windows": {"win-a": {"state": "drawn"},
                                        "win-b": {"state": "drawn"}}},
    }
    s.update(kw)
    return s


# ---------------------------------------------------------------- opt-in + layout

def test_no_block_returns_empty():
    assert CS.sheer_ribbons({}) == []
    assert CS.sheer_ribbons({"room": {"outline_mm": [[0, 0], [1, 0], [1, 1]]}}) == []


def test_two_windows_two_sill_length_ribbons():
    rbs = CS.sheer_ribbons(_spec())
    assert len(rbs) == 2
    assert {r["window"] for r in rbs} == {"win-a", "win-b"}
    for r in rbs:
        # z DERIVES from the opening's own sill/head — sill-length, never floor-to-ceiling
        assert r["z0"] == pytest.approx((1000 + CS.HEM_ABOVE_SILL_MM) * 0.001)
        assert r["z1"] == pytest.approx(2.2)
        assert r["state"] == "drawn"
        assert r["name"].startswith("sheer__")


def test_ribbon_hangs_room_side_within_the_rod_band():
    rbs = CS.sheer_ribbons(_spec())
    amp = CS.amp_mm()
    for r in rbs:
        assert r["sign"] == 1            # room is east of the x0 plane
        for x_m, _y in r["pts"]:
            assert (CS.ROD_OFFSET_MM - amp - 1e-6) * 0.001 <= x_m \
                   <= (CS.ROD_OFFSET_MM + amp + 1e-6) * 0.001


def test_ribbon_stays_inside_its_own_opening_span():
    """The panel never leaves its reveal — the plan-level half of 'the flanking opal
    strips / mirror pier are never occluded' (D-E6-1; the render half is LOOK)."""
    rbs = {r["window"]: r for r in CS.sheer_ribbons(_spec())}
    for oid, (lo, hi) in (("win-a", (1000, 1600)), ("win-b", (3000, 3600))):
        ys = [y for _x, y in rbs[oid]["pts"]]
        assert min(ys) >= (lo + CS.SIDE_CLEAR_MM - 1e-6) * 0.001
        assert max(ys) <= (hi - CS.SIDE_CLEAR_MM + 1e-6) * 0.001


def test_amplitude_derives_from_fullness_not_a_second_constant():
    a = CS.amp_mm()
    k = 2.0 * math.pi / CS.WAVELEN_MM
    assert math.sqrt(1.0 + (a * k) ** 2 / 2.0) == pytest.approx(CS.FULLNESS)
    with pytest.raises(ValueError, match="fullness"):
        CS.amp_mm(fullness=1.0)


def test_rod_offset_is_spec_overridable():
    s = _spec()
    s["casement_sheers"]["rod_offset_mm"] = 80
    assert all(x >= (80 - CS.amp_mm() - 1e-6) * 0.001
               for r in CS.sheer_ribbons(s) for x, _ in r["pts"])


# ---------------------------------------------------------------- RAISE paths

def test_parked_raises_until_a_park_is_designed():
    s = _spec()
    s["casement_sheers"]["windows"]["win-a"]["state"] = "parked"
    with pytest.raises(ValueError, match="drawn-only"):
        CS.sheer_ribbons(s)


def test_unknown_state_raises():
    s = _spec()
    s["casement_sheers"]["windows"]["win-a"]["state"] = "open"
    with pytest.raises(ValueError, match="drawn"):
        CS.sheer_ribbons(s)


def test_missing_state_raises():
    s = _spec()
    s["casement_sheers"]["windows"]["win-a"] = {}
    with pytest.raises(ValueError, match="drawn"):
        CS.sheer_ribbons(s)


def test_unknown_window_id_raises():
    s = _spec()
    s["casement_sheers"]["windows"]["win-TYPO"] = {"state": "drawn"}
    with pytest.raises(ValueError, match="unknown opening"):
        CS.sheer_ribbons(s)


def test_non_glass_opening_raises():
    s = _spec()
    s["casement_sheers"]["windows"] = {"door-x": {"state": "drawn"}}
    with pytest.raises(ValueError, match="not glass"):
        CS.sheer_ribbons(s)


def test_missing_sill_or_head_raises_never_floor_to_ceiling():
    s = _spec()
    del s["room"]["openings"][0]["sill_mm"]
    with pytest.raises(ValueError, match="sill_mm/head_mm"):
        CS.sheer_ribbons(s)
    s = _spec()
    del s["room"]["openings"][1]["head_mm"]
    with pytest.raises(ValueError, match="sill_mm/head_mm"):
        CS.sheer_ribbons(s)


def test_missing_windows_map_raises():
    s = _spec()
    s["casement_sheers"] = {"rod_offset_mm": 50}
    with pytest.raises(ValueError, match="windows"):
        CS.sheer_ribbons(s)


def test_missing_outline_raises():
    s = _spec()
    s["room"]["outline_mm"] = []
    with pytest.raises(ValueError, match="outline"):
        CS.sheer_ribbons(s)


def test_bad_rod_offset_raises():
    s = _spec()
    s["casement_sheers"]["rod_offset_mm"] = 0
    with pytest.raises(ValueError, match="rod_offset"):
        CS.sheer_ribbons(s)


def test_diagonal_rect_raises():
    s = _spec()
    s["room"]["openings"][0]["rect"] = [0, 1000, 300, 1600]
    with pytest.raises(ValueError, match="axis-aligned"):
        CS.sheer_ribbons(s)


# ------------------------------------------------- cross-block alpha pin (ONE source)

def test_alpha_missing_curtains_block_raises():
    s = _spec()
    del s["curtains"]
    with pytest.raises(ValueError, match="curtains"):
        CS.sheer_ribbons(s)


def test_alpha_missing_key_raises():
    s = _spec(curtains={"render_state": {}})
    with pytest.raises(ValueError, match="sheer_alpha"):
        CS.sheer_ribbons(s)


def test_alpha_out_of_bounds_raises():
    for bad in (0.01, 0.95, 38):
        s = _spec(curtains={"render_state": {"sheer_alpha": bad}})
        with pytest.raises(ValueError, match="sheer_alpha"):
            CS.sheer_ribbons(s)


# ---------------------------------------------------------------- canonical FILE

def _canon():
    with open(CANON, encoding="utf-8") as f:
        return json.load(f)


def test_canonical_block_covers_exactly_the_two_west_casements():
    spec = _canon()
    wins = spec["casement_sheers"]["windows"]
    assert set(wins) == {"glz-west-win1", "glz-west-win2"}
    assert all(w["state"] == "drawn" for w in wins.values())


def test_canonical_file_yields_two_drawn_sill_length_ribbons():
    rbs = CS.sheer_ribbons(_canon())
    assert len(rbs) == 2
    for r in rbs:
        assert r["z0"] == pytest.approx(1.015)   # sill 1000 + hem 15 [est]
        assert r["z1"] == pytest.approx(2.2)     # head 2200 [est]
        assert r["sign"] == 1                    # fabric hangs INTO the room (east of x0)
        assert r["alpha"] == pytest.approx(0.38)  # the east system's ONE transmission


def test_canonical_ribbons_stay_clear_of_the_strip_and_pier_bands():
    """Plan pin of D-E6-1's disjointness claim: the sheers live inside their reveals
    (y2898-3498 / y4999-5599); the opal strip centres (y3523.7 / y4974.3) and the
    mirror pier between them carry NO fabric. (Render-side verify = LOOK, by
    projection, per build-consequence 11.)"""
    rbs = {r["window"]: r for r in CS.sheer_ribbons(_canon())}
    y1 = [y * 1000 for _x, y in rbs["glz-west-win1"]["pts"]]
    y2 = [y * 1000 for _x, y in rbs["glz-west-win2"]["pts"]]
    assert max(y1) < 3523.7 - 20, "win1 sheer reaches the south opal strip band"
    assert min(y2) > 4974.3 + 20, "win2 sheer reaches the north opal strip band"
    assert max(y1) < 4999 and min(y2) > 3498.3, "fabric on the mirror pier"


def test_canonical_spec_dropping_curtains_block_raises():
    spec = copy.deepcopy(_canon())
    del spec["curtains"]
    with pytest.raises(ValueError, match="curtains"):
        CS.sheer_ribbons(spec)


def test_canonical_records_the_blackout_absence():
    """D-E6-1 probe: 'no blackout data exists at glz-west-win1/2' is a RECORDED
    absence (anti-reopen), not an accident of omission."""
    cs = _canon()["casement_sheers"]
    assert "no_blackout" in cs and "still_owner" in cs["no_blackout"]


# ------------------------------------------------- build_room wiring pins (source)
# The consumer is bpy-layer, untestable under plain python — these pins hold the
# wiring the DD names (build-consequence 3): runs AFTER _add_curtains inside the
# same --hero skip, RAISES when `curtain_sheer` is absent (get-or-create would fork
# a second sheer identity), and every ribbon escapes the bevel/material passes.

def _build_room_src():
    with open(os.path.join(HERE, "build_room.py"), encoding="utf-8") as f:
        return f.read()


def test_build_room_consumer_body_pins():
    src = _build_room_src()
    assert "def _add_casement_sheers" in src, "consumer missing — data without a consumer"
    body = src.split("def _add_casement_sheers")[1].split("\ndef ")[0]
    assert '"ph_model"' in body, "ribbons must escape the wide bevel + material passes"
    assert 'bpy.data.materials.get("curtain_sheer")' in body and "raise ValueError" in body, \
        "an absent curtain_sheer must RAISE (get-or-create forks the sheer identity)"
    assert "get-or-create" in body or "fork" in body


def test_build_room_call_after_curtains_inside_the_hero_skip():
    src = _build_room_src()
    blk = src.split("CURTAINS — skipped only for --hero")[1]
    blk = blk[:blk.index("_add_vanity_mirror")]
    assert "_add_curtains(spec, h)" in blk and "_add_casement_sheers(spec)" in blk, \
        "the sheers call must live in the same not-_hero dressing block as the curtains"
    assert blk.index("_add_curtains(spec, h)") < blk.index("_add_casement_sheers(spec)"), \
        "the sheers must run AFTER _add_curtains (which owns the curtain_sheer material)"


def test_build_rect_guard_refuses_a_casement_sheers_spec():
    """The rect path consumes none of the suite blocks — a rect spec carrying
    casement_sheers would silently render bare glass (the exact revert-by-omission
    class the block exists to kill)."""
    src = _build_room_src()
    guard = src.split("_suite_only = [")[1].split("]")[0]
    assert '"casement_sheers"' in guard
