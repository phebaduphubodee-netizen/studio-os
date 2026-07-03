#!/usr/bin/env python3
"""test_placement_logic.py — pin the human-usage placement rules with synthetic specs
+ the real production specs (which must be CAUGHT: TV fused/uncontrolled).

Deterministic, no render/model. Proves the checker (a) PASSes correct placements,
(b) FAILs the exact designer complaints — TV behind the viewer's head, TV over the
bed, the entry door sharing the bed-head wall (GS-01), (c) works for a living room
(primary viewer = the sofa), and (d) flags the REAL bug in both production specs
(TV fused into the headboard / a feature wall -> no controllable position).

Run: python pipeline/scripts/test_placement_logic.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement_logic as P  # noqa: E402


def _bedroom(tv=None, bed_rot=0, door_wall=None):
    # bed centred at (3000,4000), 2000x2000, foot faces -Y (rot 0) -> head wall = north
    spec = {"room": {"outline_mm": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]]},
            "items": [{"name": "bed", "kind": "bed", "x": 2000, "y": 3000,
                       "w": 2000, "d": 2000, "h": 600}],
            "builtins": []}
    if bed_rot:
        spec["items"][0]["rot"] = bed_rot
    if door_wall:
        spec["door"] = {"wall": door_wall, "x": 2500, "y": 0, "w": 900}
    if tv:
        spec["items"].append(tv)
    return spec


def _living(tv=None, sofa_rot=0):
    # sofa centred at (3000,4450), faces -Y (rot 0) -> TV belongs on the south side
    spec = {"room": {"outline_mm": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]]},
            "items": [{"name": "sofa", "kind": "sofa", "x": 2000, "y": 4000,
                       "w": 2000, "d": 900, "h": 850}],
            "builtins": []}
    if sofa_rot:
        spec["items"][0]["rot"] = sofa_rot
    if tv:
        spec["items"].append(tv)
    return spec


def _s(rep, rule):
    return next((f["status"] for f in rep["findings"] if f["rule"] == rule), None)


def _tv(x=2500, y=150, w=1000, d=100):
    return {"name": "tv", "kind": "tv", "x": x, "y": y, "w": w, "d": d, "h": 700}


# ---- TV vs a bed ----
def test_good_tv_on_foot_wall_passes():
    rep = P.check(_bedroom(_tv()))
    assert rep["status"] == P.PASS, rep
    assert _s(rep, "tv_positioned") == P.PASS
    assert _s(rep, "tv_faces_viewer") == P.PASS
    assert _s(rep, "tv_not_over_viewer") == P.PASS


def test_tv_behind_head_fails():
    rep = P.check(_bedroom(_tv(y=5800)))       # north wall = behind the headboard
    assert rep["status"] == P.FAIL
    assert _s(rep, "tv_faces_viewer") == P.FAIL


def test_tv_over_bed_fails():
    rep = P.check(_bedroom(_tv(y=3500, d=200)))
    assert _s(rep, "tv_not_over_viewer") == P.FAIL
    assert rep["status"] == P.FAIL


def test_tv_too_close_warns():
    rep = P.check(_bedroom(_tv(y=2900)))       # ~1050 mm from bed centre
    assert _s(rep, "tv_viewing_distance") == P.WARN
    assert _s(rep, "tv_faces_viewer") == P.PASS


def test_bed_rotated_180_flips_front():
    assert _s(P.check(_bedroom(_tv(y=5800), bed_rot=180)), "tv_faces_viewer") == P.PASS
    assert _s(P.check(_bedroom(_tv(y=150), bed_rot=180)), "tv_faces_viewer") == P.FAIL


# ---- TV vs a sofa (living room; primary viewer generalisation) ----
def test_living_sofa_is_the_viewer():
    rep = P.check(_living(_tv(y=150)))         # TV in front of a -Y-facing sofa
    assert rep["viewer_kind"] == "sofa"
    assert _s(rep, "tv_faces_viewer") == P.PASS


def test_living_tv_behind_sofa_fails():
    rep = P.check(_living(_tv(y=5800)))
    assert _s(rep, "tv_faces_viewer") == P.FAIL


# ---- door vs bed head (GS-01) ----
def test_door_on_head_wall_fails():
    rep = P.check(_bedroom(door_wall="north"))     # head faces north; door on north
    assert _s(rep, "door_vs_bed_head") == P.FAIL
    assert rep["status"] == P.FAIL


def test_door_on_other_wall_passes():
    rep = P.check(_bedroom(door_wall="south"))
    assert _s(rep, "door_vs_bed_head") == P.PASS


def test_door_rule_skips_without_bed_or_door():
    assert _s(P.check(_living(_tv())), "door_vs_bed_head") is None     # no bed
    assert _s(P.check(_bedroom(_tv())), "door_vs_bed_head") is None    # no door


# ---- fused / absent handling ----
def test_fused_headboard_tv_is_flagged():
    spec = _bedroom()
    spec["builtins"].append({"name": "หัวเตียง/ทีวี built-in", "kind": "headboard_tv",
                             "x": 1970, "y": 5000, "w": 3330, "d": 574, "h": 2800})
    rep = P.check(spec)
    assert rep["tv_status"] == "fused"
    assert _s(rep, "tv_positioned") == P.FAIL and rep["status"] == P.FAIL


def test_no_tv_room_does_not_false_fail():
    rep = P.check(_bedroom())
    assert rep["tv_status"] == "absent"
    assert rep["status"] != P.FAIL


def test_name_only_thai_tv_detected_as_fused():
    spec = _bedroom()
    spec["builtins"].append({"name": "ผนัง ทีวี", "kind": "feature_wall",
                             "x": 100, "y": 5000, "w": 2000, "d": 200, "h": 2700})
    assert P.check(spec)["tv_status"] == "fused"


# ---- real production specs must be CAUGHT ----
def _spec(fn):
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(root, "pipeline", "scripts", "specs", fn)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def test_real_bedroom_suite_is_caught():
    spec = _spec("bedroom_suite.json")
    if spec is None:
        return
    rep = P.check(spec)
    assert rep["tv_status"] == "fused" and rep["status"] == P.FAIL
    assert _s(rep, "door_vs_bed_head") == P.PASS      # head north, door south -> ok


def test_real_living_condo_is_caught():
    spec = _spec("living_condo.json")
    if spec is None:
        return
    rep = P.check(spec)
    assert rep["viewer_kind"] == "sofa"
    assert rep["tv_status"] == "fused" and rep["status"] == P.FAIL   # tv_feature wall


TESTS = [test_good_tv_on_foot_wall_passes, test_tv_behind_head_fails, test_tv_over_bed_fails,
         test_tv_too_close_warns, test_bed_rotated_180_flips_front, test_living_sofa_is_the_viewer,
         test_living_tv_behind_sofa_fails, test_door_on_head_wall_fails, test_door_on_other_wall_passes,
         test_door_rule_skips_without_bed_or_door, test_fused_headboard_tv_is_flagged,
         test_no_tv_room_does_not_false_fail, test_name_only_thai_tv_detected_as_fused,
         test_real_bedroom_suite_is_caught, test_real_living_condo_is_caught]


def main():
    passed = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
