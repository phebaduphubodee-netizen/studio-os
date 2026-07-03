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


def _bedroom_with(*extra_items, builtins=()):
    spec = _bedroom()
    spec["items"].extend(extra_items)
    spec["builtins"].extend(builtins)
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


def test_name_only_tv_is_named_only_warn_not_fail():
    # a mere NAME match (kind is not a TV kind) is a soft hint -> named_only -> WARN,
    # never a hard FAIL: a 'ตู้ทีวี' console must not block a deliverable (Agent-2 F1).
    spec = _bedroom()
    spec["builtins"].append({"name": "ผนัง ทีวี", "kind": "feature_wall",
                             "x": 100, "y": 5000, "w": 2000, "d": 200, "h": 2700})
    rep = P.check(spec)
    assert rep["tv_status"] == "named_only"
    assert _s(rep, "tv_positioned") == P.WARN and rep["status"] != P.FAIL


def test_tv_named_console_does_not_hard_fail():
    # the concrete false-block from scrutiny: a Thai "TV cabinet" with no discrete screen
    spec = _bedroom()
    spec["items"].append({"name": "ตู้ทีวี", "kind": "console",
                          "x": 100, "y": 100, "w": 1600, "d": 450, "h": 550})
    _results, verdict = P.report(spec)
    assert verdict != P.FAIL           # WARN/REVIEW at worst, never a hard gate stop
    assert P.find_tv(spec)[1] == "named_only"


# ---- real production specs must be CAUGHT ----
def _spec(fn):
    # the specs are committed fixtures — a missing one is a real failure, not a silent
    # skip (a `return None` guard used to let the suite go green with the real-spec tests
    # quietly no-op'd).
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", fn)
    assert os.path.exists(p), f"fixture spec missing: {p}"
    return json.load(open(p, encoding="utf-8"))


def test_real_bedroom_suite_tv_now_positioned():
    # the fused headboard_tv was SPLIT onto the foot wall (2026-07-03 FUNCTION-gate fix):
    # the real spec must now PASS the TV rules (fused -> positioned) and no longer FAIL.
    # (test_fused_headboard_tv_is_flagged + living_condo still prove the CATCH capability.)
    spec = _spec("bedroom_suite.json")
    if spec is None:
        return
    rep = P.check(spec)
    assert rep["tv_status"] == "positioned"
    assert _s(rep, "tv_positioned") == P.PASS
    assert _s(rep, "tv_faces_viewer") == P.PASS
    assert _s(rep, "tv_not_over_viewer") == P.PASS
    assert _s(rep, "tv_viewing_distance") == P.PASS
    assert _s(rep, "door_vs_bed_head") == P.PASS      # head north, door south -> ok
    assert rep["status"] == P.PASS                    # fully clean after the wardrobe re-type


def test_real_living_condo_is_caught():
    spec = _spec("living_condo.json")
    if spec is None:
        return
    rep = P.check(spec)
    assert rep["viewer_kind"] == "sofa"
    assert rep["tv_status"] == "fused" and rep["status"] == P.FAIL   # tv_feature wall


# ---- furniture dimensions vs ergonomic norms (GS-02/06; ergonomics_ref / NLM DR) ----
def test_furniture_within_norms_passes():
    spec = _bedroom_with({"name": "ct", "kind": "coffee_table", "x": 100, "y": 100,
                          "w": 1000, "d": 500, "h": 400})
    assert _s(P.check(spec), "furniture_dimensions") == P.PASS


def test_oversized_bed_warns():
    spec = _bedroom()
    spec["items"][0]["w"], spec["items"][0]["d"] = 2500, 2500   # far off any standard mattress
    assert _s(P.check(spec), "furniture_dimensions") == P.WARN


def test_bad_coffee_table_height_warns():
    spec = _bedroom_with({"name": "ct", "kind": "coffee_table", "x": 100, "y": 100,
                          "w": 1000, "d": 500, "h": 800})   # 800mm = way too tall for a coffee table
    assert _s(P.check(spec), "furniture_dimensions") == P.WARN


def test_shallow_wardrobe_warns():
    spec = _bedroom_with(builtins=[{"name": "wd", "kind": "wardrobe", "x": 0, "y": 0,
                                    "w": 100, "d": 3000, "h": 2400}])   # 100mm can't hang clothes
    assert _s(P.check(spec), "furniture_dimensions") == P.WARN


def test_standard_bed_passes_within_tolerance():
    spec = _bedroom()
    spec["items"][0]["w"], spec["items"][0]["d"] = 1524, 2032   # exact Queen
    assert _s(P.check(spec), "furniture_dimensions") == P.PASS


def test_real_bedroom_furniture_now_within_norms():
    # the 100mm 'wardrobe' beside the bed was re-typed to a shallow 'cabinet' (its true
    # function; the two 600mm wardrobes handle clothes). furniture_dimensions must now PASS
    # on the real spec. (test_shallow_wardrobe_warns keeps proving the shallow-depth CATCH.)
    spec = _spec("bedroom_suite.json")
    if spec is None:
        return
    f = next((x for x in P.check(spec)["findings"] if x["rule"] == "furniture_dimensions"), None)
    assert f is not None and f["status"] == P.PASS, f


# ---- bathroom fixture logic (GS-05 use-frequency + wet/dry zoning; NLM DR f61fded1) ----
def _bath(fixtures, door=(1000, 0, 800), wall="south"):
    dx, dy, dw = door
    return {"room": {"outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
            "subrooms": [{"name": "ensuite",
                          "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]],
                          "door": {"x": dx, "y": dy, "w": dw, "wall": wall},
                          "fixtures": fixtures}]}


def _fx(kind, x, y, w=800, d=500):
    return {"name": kind, "kind": kind, "x": x, "y": y, "w": w, "d": d}


def test_bathroom_good_ordering_passes():
    spec = _bath([_fx("vanity", 100, 100), _fx("wc", 2400, 1200, 400, 650),
                  _fx("shower", 100, 2000, 900, 900), _fx("tub", 1500, 2100, 1400, 750)])
    assert _s(P.check(spec), "bathroom_logic") == P.PASS


def test_bathroom_shower_at_entry_fails():
    spec = _bath([_fx("vanity", 100, 1500), _fx("shower", 1000, 100, 900, 900)])
    assert _s(P.check(spec), "bathroom_logic") == P.FAIL


def test_bathroom_wet_not_at_back_warns():
    spec = _bath([_fx("vanity", 100, 100), _fx("wc", 2400, 2400, 400, 500),
                  _fx("shower", 100, 400, 900, 900)])
    assert _s(P.check(spec), "bathroom_logic") == P.WARN


def test_bathroom_rule_skips_without_bathroom():
    assert _s(P.check(_bedroom(_tv())), "bathroom_logic") is None


def test_real_ensuite_follows_frequency_and_zoning():
    spec = _spec("bedroom_suite.json")
    if spec is None:
        return
    assert _s(P.check(spec), "bathroom_logic") == P.PASS      # basin at entry, wet deep


# ---- seating faces a focal (GS-03/26; couples to build_room auto-face) ----
def _living_seats(*seats, table=None, tv=None):
    spec = {"room": {"outline_mm": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]]},
            "items": list(seats), "builtins": []}
    if table:
        spec["items"].append(table)
    if tv:
        spec["items"].append(tv)
    return spec


def test_seating_faces_table_passes():
    # sofa at y4000 facing -Y (rot 0) toward a coffee table at y2500 (in front)
    sofa = {"name": "sofa", "kind": "sofa", "x": 2000, "y": 4000, "w": 2000, "d": 900, "h": 850, "rot": 0}
    table = {"name": "ct", "kind": "coffee_table", "x": 2500, "y": 2500, "w": 1000, "d": 600, "h": 400}
    assert _s(P.check(_living_seats(sofa, table=table)), "seating_faces_focal") == P.PASS


def test_seating_away_from_focal_warns():
    # armchair faces +Y (rot 180) but the only table is at -Y (behind it)
    chair = {"name": "arm", "kind": "armchair", "x": 2500, "y": 4000, "w": 800, "d": 800, "h": 750, "rot": 180}
    table = {"name": "ct", "kind": "coffee_table", "x": 2500, "y": 2000, "w": 1000, "d": 600, "h": 400}
    assert _s(P.check(_living_seats(chair, table=table)), "seating_faces_focal") == P.WARN


def test_lone_seat_no_focal_not_judged():
    # a solo seat with nothing to face is UNJUDGED (None), not a false WARN — it may face
    # a window/view the spec can't model (narrowed rule; Agent-1 F2).
    chair = {"name": "arm", "kind": "armchair", "x": 2500, "y": 3000, "w": 800, "d": 800, "h": 750, "rot": 0}
    assert _s(P.check(_living_seats(chair)), "seating_faces_focal") is None


def test_seating_without_rot_not_judged():
    # no explicit rot -> orientation not knowable here (build_room auto-face is narrow) -> None
    chair = {"name": "arm", "kind": "armchair", "x": 2500, "y": 3000, "w": 800, "d": 800, "h": 750}  # no rot
    table = {"name": "ct", "kind": "coffee_table", "x": 2500, "y": 1500, "w": 1000, "d": 600, "h": 400}
    assert _s(P.check(_living_seats(chair, table=table)), "seating_faces_focal") is None


def test_seating_perpendicular_focal_warns():
    # focal exactly to the side (dot == 0, not > 0) counts as "not facing" -> WARN boundary
    chair = {"name": "arm", "kind": "armchair", "x": 2000, "y": 2000, "w": 800, "d": 800, "h": 750, "rot": 0}  # faces -Y
    table = {"name": "ct", "kind": "coffee_table", "x": 3500, "y": 2000, "w": 800, "d": 800, "h": 400}          # due +X
    assert _s(P.check(_living_seats(chair, table=table)), "seating_faces_focal") == P.WARN


def test_two_seats_facing_each_other_pass():
    # a conversation pair with no table: each seat is the other's focal
    a = {"name": "a", "kind": "armchair", "x": 2000, "y": 2000, "w": 800, "d": 800, "h": 750, "rot": 180}  # +Y
    b = {"name": "b", "kind": "armchair", "x": 2000, "y": 4000, "w": 800, "d": 800, "h": 750, "rot": 0}     # -Y
    assert _s(P.check(_living_seats(a, b)), "seating_faces_focal") == P.PASS


def test_seating_rule_skips_without_seats():
    assert _s(P.check(_bedroom(_tv())), "seating_faces_focal") is None


def test_real_living_condo_seating_passes():
    spec = _spec("living_condo.json")
    if spec is None:
        return
    assert _s(P.check(spec), "seating_faces_focal") == P.PASS   # sofa->table/TV, armchair->table


# ---- report(): the (results, verdict) gate contract (drops into make_all / repair_loop / suite_package) ----
def test_report_fail_on_fused_tv():
    spec = _bedroom()
    spec["builtins"].append({"name": "hb/tv", "kind": "headboard_tv",
                             "x": 1970, "y": 5000, "w": 3330, "d": 574, "h": 2800})
    results, verdict = P.report(spec)
    assert verdict == P.FAIL
    assert results and all(r["check"].startswith("function:") for r in results)
    assert any(r["check"] == "function:tv_positioned" and r["status"] == P.FAIL for r in results)


def test_report_pass_on_good_tv():
    _results, verdict = P.report(_bedroom(_tv()))
    assert verdict == P.PASS


def test_report_review_on_warn_only():
    spec = _bedroom(_tv())
    spec["items"][0]["w"], spec["items"][0]["d"] = 2500, 2500   # off-standard bed -> WARN, no FAIL
    _results, verdict = P.report(spec)
    assert verdict == "REVIEW"


def test_report_unwired_when_nothing_applies():
    spec = {"room": {"outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "items": [{"name": "rug", "kind": "rug", "x": 500, "y": 500, "w": 2000, "d": 2000}],
            "builtins": []}
    results, verdict = P.report(spec)
    assert verdict == P.UNWIRED and results == []


# ---- @0.1 inch specs are normalized to mm and gated by the SAME rules ----
def _inch_living(tv_y_in):
    # 14x16 ft living room; sofa faces -Y (rot 0); entry door auto-synthesised south.
    return {"schema": "interior-ai/room-spec@0.1",
            "room": {"width_in": 168, "depth_in": 192, "ceiling_in": 96, "type": "living"},
            "items": [{"name": "sofa", "kind": "sofa", "x": 42, "y": 150, "w": 84, "d": 36, "h": 34},
                      {"name": "tv", "kind": "tv", "x": 60, "y": tv_y_in, "w": 48, "d": 4, "h": 28}]}


def test_inch_spec_normalized_to_mm():
    norm = P._normalize(_inch_living(6))
    assert "outline_mm" in norm["room"] and norm["door"]["wall"] == "south"
    assert abs(norm["room"]["outline_mm"][1][0] - 168 * 25.4) < 1e-6      # width scaled ×25.4
    assert abs(norm["items"][0]["w"] - 84 * 25.4) < 1e-6                  # element scaled ×25.4


def test_inch_spec_tv_in_front_passes():
    results, verdict = P.report(_inch_living(tv_y_in=6))                  # south side, in front
    assert verdict in (P.PASS, "REVIEW")
    assert next(r["status"] for r in results if r["check"] == "function:tv_faces_viewer") == P.PASS


def test_inch_spec_tv_behind_sofa_fails():
    results, verdict = P.report(_inch_living(tv_y_in=185))               # behind the sofa (north)
    assert verdict == P.FAIL
    assert next(r["status"] for r in results if r["check"] == "function:tv_faces_viewer") == P.FAIL


# ---- robustness / edge cases (from adversarial scrutiny) ----
def test_malformed_item_missing_dims_does_not_crash():
    # a pre-render gate must DEGRADE, never throw, on a malformed element (missing w/d)
    spec = {"room": {"outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "items": [{"kind": "bed", "x": 1000, "y": 1000, "d": 2000},          # no "w"
                      {"kind": "tv", "x": 1500, "y": 100}],                       # no w/d
            "builtins": []}
    results, verdict = P.report(spec)          # must return, not raise
    assert verdict in (P.PASS, "REVIEW", P.FAIL, P.UNWIRED)


def test_find_tv_prefers_positioned_over_named():
    spec = _bedroom()
    spec["items"].append({"name": "tv", "kind": "tv", "x": 2500, "y": 150, "w": 1000, "d": 100, "h": 700})
    spec["builtins"].append({"name": "ผนัง ทีวี", "kind": "feature_wall", "x": 0, "y": 5800, "w": 3000, "d": 150})
    assert P.find_tv(spec)[1] == "positioned"   # a real TV outranks a name-only wall


def test_normalize_depth_only_inch_not_misread():
    # _is_inch keys on width_in; a spec with only depth_in is NOT treated as inch
    spec = {"room": {"depth_in": 120, "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
            "items": [], "builtins": []}
    assert P._normalize(spec) is spec          # untouched (treated as @0.2)


# ---- integration: the FUNCTION layer is now part of the pre-render Gate 0 (repair_loop) ----
def test_repair_loop_gate0_includes_function_and_fails_fused_tv():
    import repair_loop
    spec = _spec("living_condo.json")                                     # still a fused tv_feature
    if spec is None:
        return
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs", "living_condo.json")
    results, verdict = repair_loop._real_geometry_fn(spec, path)
    assert verdict == P.FAIL                                              # fused TV escalates the gate
    assert any(r["check"] == "function:tv_positioned" and r["status"] == P.FAIL for r in results)


TESTS = [test_good_tv_on_foot_wall_passes, test_tv_behind_head_fails, test_tv_over_bed_fails,
         test_tv_too_close_warns, test_bed_rotated_180_flips_front, test_living_sofa_is_the_viewer,
         test_living_tv_behind_sofa_fails, test_door_on_head_wall_fails, test_door_on_other_wall_passes,
         test_door_rule_skips_without_bed_or_door, test_fused_headboard_tv_is_flagged,
         test_no_tv_room_does_not_false_fail, test_name_only_tv_is_named_only_warn_not_fail,
         test_tv_named_console_does_not_hard_fail,
         test_real_bedroom_suite_tv_now_positioned, test_real_living_condo_is_caught,
         test_furniture_within_norms_passes, test_oversized_bed_warns,
         test_bad_coffee_table_height_warns, test_shallow_wardrobe_warns,
         test_standard_bed_passes_within_tolerance, test_real_bedroom_furniture_now_within_norms,
         test_bathroom_good_ordering_passes, test_bathroom_shower_at_entry_fails,
         test_bathroom_wet_not_at_back_warns, test_bathroom_rule_skips_without_bathroom,
         test_real_ensuite_follows_frequency_and_zoning,
         test_seating_faces_table_passes, test_seating_away_from_focal_warns,
         test_lone_seat_no_focal_not_judged, test_seating_without_rot_not_judged,
         test_seating_perpendicular_focal_warns,
         test_two_seats_facing_each_other_pass, test_seating_rule_skips_without_seats,
         test_real_living_condo_seating_passes,
         test_report_fail_on_fused_tv, test_report_pass_on_good_tv, test_report_review_on_warn_only,
         test_report_unwired_when_nothing_applies, test_inch_spec_normalized_to_mm,
         test_inch_spec_tv_in_front_passes, test_inch_spec_tv_behind_sofa_fails,
         test_malformed_item_missing_dims_does_not_crash, test_find_tv_prefers_positioned_over_named,
         test_normalize_depth_only_inch_not_misread,
         test_repair_loop_gate0_includes_function_and_fails_fused_tv]


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
