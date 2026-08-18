#!/usr/bin/env python3
"""test_placement_logic.py — pin the human-usage placement rules with synthetic specs
+ the real production specs (which must be CAUGHT: TV fused/uncontrolled).

Deterministic, no render/model. Proves the checker (a) PASSes correct placements,
(b) FAILs the exact designer complaints — TV behind the viewer's head, TV over the
bed, the entry door sharing the bed-head wall (GS-01), (c) works for a living room
(primary viewer = the sofa) and a kitchen (NKBA work-triangle), and (d) still CATCHES
a fused TV (synthetic specs) now that BOTH production specs are fixed — bedroom_suite
and living_condo split their fused TV onto a real wall and must PASS.

Run: python pipeline/scripts/test_placement_logic.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement_logic as P  # noqa: E402


def _bedroom(tv=None, bed_rot=0, door_wall=None, nightstand=True):
    # bed centred at (3000,4000), 2000x2000, foot faces -Y (rot 0) -> head wall = north.
    # A COMPLETE bedroom carries a bedside table (bed_has_nightstand, 2026-07-12) — the TV/door
    # tests assert an overall PASS, so the scaffold must not be furnishing-incomplete. Pass
    # nightstand=False for the specs that exercise the nightstand rule itself.
    spec = {"room": {"outline_mm": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]]},
            "items": [{"name": "bed", "kind": "bed", "x": 2000, "y": 3000,
                       "w": 2000, "d": 2000, "h": 600}],
            "builtins": []}
    if nightstand:
        spec["items"].append({"name": "โต๊ะข้างเตียง", "kind": "side_table",
                              "x": 1500, "y": 4500, "w": 400, "d": 500, "h": 550})
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


def _bedroom_with(*extra_items, builtins=(), nightstand=True):
    spec = _bedroom(nightstand=nightstand)
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
    # 2026-07-12 — bed_has_nightstand now REVIEWs this spec, and that is a TRUE finding, not a
    # regression: bedroom_suite has a 100 mm-deep "ตู้โชว์บาง built-in ข้างเตียง" but NO bedside
    # table — you cannot set down a glass of water. That is verbatim the omission a real paying
    # client sent back for rework. The spec is NOT edited to make this green: the gate is right
    # and the reference spec is furnishing-incomplete. Pin it, surface it, let the owner decide.
    assert _s(rep, "bed_has_nightstand") == P.WARN
    assert rep["status"] == P.WARN                    # TV/door/geometry clean; furnishing gap open
    assert [f["rule"] for f in rep["findings"] if f["status"] != P.PASS] == ["bed_has_nightstand"]


def test_real_living_condo_tv_now_positioned():
    # the fused tv_feature wall was SPLIT into a plain 'cabinet' media wall + a standalone
    # 'tv_panel' facing the sofa (2026-07-04 FUNCTION-gate fix). The real spec must now PASS
    # every TV rule. (test_fused_headboard_tv_is_flagged + test_report_fail_on_fused_tv keep
    # proving the fused-TV CATCH capability with synthetic specs.)
    spec = _spec("living_condo.json")
    rep = P.check(spec)
    assert rep["viewer_kind"] == "sofa"
    assert rep["tv_status"] == "positioned"
    assert _s(rep, "tv_positioned") == P.PASS
    assert _s(rep, "tv_faces_viewer") == P.PASS
    assert _s(rep, "tv_not_over_viewer") == P.PASS
    assert _s(rep, "tv_viewing_distance") == P.PASS
    # NOTE 2026-07-04: overall is now REVIEW, not PASS — the new seating_clear_of_screen rule
    # correctly flags living_condo's reading armchair sitting in front of the TV (the designer's
    # GS-03 "เก้าอี้อยู่ใต้ทีวี / TV อยู่หลังคนนั่ง" comment). The TV rules above still PASS; the armchair
    # is a real defect (living_condo is slated for retirement in favour of the Floor-1 derivation).
    assert _s(rep, "seating_clear_of_screen") == P.WARN
    assert rep["status"] == P.WARN                     # check() reports raw WARN (report() maps it to REVIEW)


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


# ---- seating clear of the screen (GS-03; designer 2026-07-04 "เก้าอี้อยู่ใต้ทีวี") ----
def _sofa(x=2000, y=1000):
    return {"name": "sofa", "kind": "sofa", "x": x, "y": y, "w": 2000, "d": 900, "h": 850, "rot": 180}


def _wall_tv(x=2300, y=5000):
    return {"name": "tv", "kind": "tv_panel", "x": x, "y": y, "w": 1400, "d": 50, "h": 800, "mount_mm": 900}


def test_seat_in_front_of_tv_warns():
    # armchair sits in the sofa→TV corridor -> WARN (the TV would be behind whoever sits there)
    chair = {"name": "arm", "kind": "armchair", "x": 2500, "y": 3500, "w": 800, "d": 800, "h": 750, "rot": 0}
    spec = _living_seats(_sofa(), chair, tv=_wall_tv())
    assert _s(P.check(spec), "seating_clear_of_screen") == P.WARN


def test_seat_beside_tv_passes():
    # armchair well to the side of the sightline (lateral > screen band) -> PASS
    chair = {"name": "arm", "kind": "armchair", "x": 5000, "y": 3500, "w": 800, "d": 800, "h": 750, "rot": 0}
    spec = _living_seats(_sofa(), chair, tv=_wall_tv())
    assert _s(P.check(spec), "seating_clear_of_screen") == P.PASS


def test_seat_beside_screen_within_old_band_passes():
    # a chair 1.3 m to the SIDE: the old full-screen-width band flagged it; the narrowed
    # screen_half+seat_half (~1.1 m) does not — it provably can't sit under the screen
    # (scrutiny 2026-07-04, GS-26 angled-chair false-fire).
    chair = {"name": "arm", "kind": "armchair", "x": 3900, "y": 3500, "w": 800, "d": 800, "h": 750, "rot": 0}
    spec = _living_seats(_sofa(), chair, tv=_wall_tv())
    assert _s(P.check(spec), "seating_clear_of_screen") == P.PASS


def test_seat_just_in_front_of_viewer_warns():
    # a seat close to the sofa but dead in the sightline (t ≈ 0.18*axlen): the old 0.25*axlen
    # near bound MISSED it -> now WARNs (scrutiny 2026-07-04 false-miss).
    chair = {"name": "arm", "kind": "armchair", "x": 2600, "y": 1700, "w": 800, "d": 800, "h": 750, "rot": 0}
    spec = _living_seats(_sofa(), chair, tv=_wall_tv())
    assert _s(P.check(spec), "seating_clear_of_screen") == P.WARN


def test_seat_rule_none_without_tv():
    chair = {"name": "arm", "kind": "armchair", "x": 2500, "y": 3500, "w": 800, "d": 800, "h": 750, "rot": 0}
    assert _s(P.check(_living_seats(_sofa(), chair)), "seating_clear_of_screen") is None


def test_seat_rule_none_without_secondary_seat():
    assert _s(P.check(_living_seats(_sofa(), tv=_wall_tv())), "seating_clear_of_screen") is None


def test_real_living_condo_armchair_flagged_under_tv():
    # the exact defect the designer circled: the reading armchair sits in front of the TV
    assert _s(P.check(_spec("living_condo.json")), "seating_clear_of_screen") == P.WARN


# ---- kitchen work-triangle (NKBA; ergonomics_ref / NLM DR f61fded1) ----
def _kitchen(*appliances, room=(3000, 3000)):
    W, D = room
    return {"room": {"type": "kitchen", "outline_mm": [[0, 0], [W, 0], [W, D], [0, D]]},
            "items": [], "builtins": list(appliances)}


def _ap(kind, x, y, w=600, d=600):
    return {"name": kind, "kind": kind, "x": x, "y": y, "w": w, "d": d, "h": 850}


def test_kitchen_good_triangle_passes():
    # the kitchen_demo geometry: legs 1250/1460/2438, perimeter 5148 (all in band)
    spec = _kitchen(_ap("refrigerator", 0, 2100, 700, 700), _ap("sink", 50, 900),
                    _ap("cooktop", 1200, 0))
    assert _s(P.check(spec), "kitchen_work_triangle") == P.PASS


def test_kitchen_leg_too_far_warns():
    # push the fridge to the far corner so a leg exceeds 2743 mm
    spec = _kitchen(_ap("refrigerator", 5200, 5200, 700, 700), _ap("sink", 50, 900),
                    _ap("cooktop", 1200, 0), room=(6000, 6000))
    assert _s(P.check(spec), "kitchen_work_triangle") == P.WARN


def test_kitchen_single_long_leg_warns():
    # ISOLATE the leg-max clause (scrutiny 2026-07-04): one leg 2800 mm (>2743) while the
    # perimeter stays 6800 mm (<=7925), so ONLY the 'too far apart' branch may fire — proves
    # the upper-leg bound is pinned independently of the perimeter clause. Centres:
    # sink(300,300) cooktop(3100,300) fridge(1700,1728) -> legs 2800/2000/2000.
    spec = _kitchen(_ap("sink", 0, 0), _ap("cooktop", 2800, 0),
                    _ap("refrigerator", 1400, 1428), room=(3600, 2400))
    f = next(x for x in P.check(spec)["findings"] if x["rule"] == "kitchen_work_triangle")
    assert f["status"] == P.WARN, f
    assert "too far apart" in f["detail"] and "perimeter" not in f["detail"], f


def test_kitchen_leg_too_tight_warns():
    # all three appliances crammed together -> legs below 1219 mm
    spec = _kitchen(_ap("refrigerator", 0, 800, 600, 600), _ap("sink", 0, 0),
                    _ap("cooktop", 700, 0))
    assert _s(P.check(spec), "kitchen_work_triangle") == P.WARN


def test_kitchen_perimeter_too_large_warns():
    # an equilateral triangle, side 2700 mm: each leg is legal (<2743) but the perimeter is
    # 8100 mm (>7925) -> only the perimeter clause warns
    spec = _kitchen(_ap("refrigerator", 0, 0, 600, 600),       # centre (300,300)
                    _ap("sink", 2700, 0, 600, 600),            # centre (3000,300) -> leg 2700
                    _ap("cooktop", 1350, 2338, 600, 600),      # centre (1650,2638) -> legs 2700
                    room=(3600, 3600))
    r = P.check(spec)
    f = next(x for x in r["findings"] if x["rule"] == "kitchen_work_triangle")
    assert f["status"] == P.WARN and "perimeter" in f["detail"], f


def test_kitchen_rule_skips_without_full_triangle():
    # only two vertices -> not checkable (a kitchenette is not faulted for a missing vertex)
    spec = _kitchen(_ap("sink", 50, 900), _ap("cooktop", 1200, 0))
    assert _s(P.check(spec), "kitchen_work_triangle") is None


def test_kitchen_rule_skips_non_kitchen_rooms():
    # a bedroom / living room never trips the kitchen rule
    assert _s(P.check(_bedroom(_tv())), "kitchen_work_triangle") is None
    assert _s(P.check(_living(_tv())), "kitchen_work_triangle") is None


def test_bath_sink_in_subroom_is_not_a_kitchen_sink():
    # a bathroom "sink" (subroom fixture) must NOT be read as a kitchen vertex even with a
    # main-room cooktop+fridge present -> the rule scopes to the MAIN room, so it stays None
    spec = _bath([_fx("sink", 100, 100), _fx("wc", 2400, 1200, 400, 650)])
    spec.setdefault("builtins", []).extend([_ap("cooktop", 1200, 0), _ap("refrigerator", 0, 2100, 700, 700)])
    assert _s(P.check(spec), "kitchen_work_triangle") is None    # only 2 main-room vertices


def test_real_kitchen_demo_triangle_passes():
    spec = _spec("kitchen_demo.json")
    rep = P.check(spec)
    assert _s(rep, "kitchen_work_triangle") == P.PASS
    assert rep["status"] == P.PASS


# ---- TV wall-mount height (designer 2026-07-04: "ทำไมเอา TV ไปติดไว้ที่พื้น?") ----
def _tv_panel(mount=None, h=800, x=2000, y=0):
    b = {"name": "wall tv", "kind": "tv_panel", "x": x, "y": y, "w": 1400, "d": 50, "h": h, "rot": 180}
    if mount is not None:
        b["mount_mm"] = mount
    return b


def test_tv_mount_height_pass_when_mounted():
    spec = _bedroom_with(builtins=(_tv_panel(mount=650),))
    assert _s(P.check(spec), "tv_mount_height") == P.PASS


def test_tv_mount_height_warns_without_mount():
    # a wall tv_panel with no mount_mm renders as a floor block -> WARN (the designer's flag)
    spec = _bedroom_with(builtins=(_tv_panel(mount=None),))
    f = next(x for x in P.check(spec)["findings"] if x["rule"] == "tv_mount_height")
    assert f["status"] == P.WARN and "floor-standing" in f["detail"], f


def test_tv_mount_height_warns_above_ceiling():
    # mount 2200 + h 800 = 3000 mm > 2800 ceiling -> WARN
    spec = _bedroom_with(builtins=(_tv_panel(mount=2200),))
    f = next(x for x in P.check(spec)["findings"] if x["rule"] == "tv_mount_height")
    assert f["status"] == P.WARN and "ceiling" in f["detail"], f


def test_tv_mount_height_none_for_generic_tv_or_console():
    # a generic 'tv' item (ambiguous) and a tv_console (sits on a unit) are exempt -> None
    assert _s(P.check(_bedroom(_tv())), "tv_mount_height") is None
    console = {"name": "console tv", "kind": "tv_console", "x": 2000, "y": 0, "w": 1400, "d": 400, "h": 600}
    assert _s(P.check(_bedroom_with(builtins=(console,))), "tv_mount_height") is None


def test_tv_mount_height_warns_for_builtin_tv():
    # a wall TV authored as a BUILTIN kind 'tv' (not tv_panel) with no mount also floor-blocks
    # -> WARN (scrutiny 2026-07-04: the rule's own comment says tv_panel/tv). A loose 'tv' item
    # stays exempt (test_tv_mount_height_none_for_generic_tv_or_console pins that).
    tv = {"name": "wall tv", "kind": "tv", "x": 2000, "y": 0, "w": 1400, "d": 50, "h": 800}
    f = next(x for x in P.check(_bedroom_with(builtins=(tv,)))["findings"] if x["rule"] == "tv_mount_height")
    assert f["status"] == P.WARN and "floor-standing" in f["detail"], f


def test_real_specs_tv_now_mounted():
    for name in ("bedroom_suite.json", "living_condo.json"):
        assert _s(P.check(_spec(name)), "tv_mount_height") == P.PASS, name


# ---- camera has a reason (GS-04/05/22; shares camera_config.solve_eye_camera with build_room) ----
def test_camera_reason_passes_real_specs():
    for name in ("bedroom_suite.json", "living_condo.json"):
        assert _s(P.check(_spec(name)), "camera_has_a_reason") == P.PASS, name


def test_camera_reason_warns_when_no_shot_exists():
    # a full-height built-in fills the room -> no clear standing spot with line of sight;
    # build_room --eye would SystemExit at render time. This rule is ADVISORY (WARN, never
    # FAIL): the eye camera is opt-in and the default pipeline renders the overview, so a
    # "no eye shot" must never hard-abort the shared FUNCTION gate (scrutiny 2026-07-04).
    spec = {"room": {"outline_mm": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]},
            "builtins": [{"kind": "wall", "name": "block", "x": 200, "y": 200, "w": 1600, "d": 1600, "h": 2800}],
            "items": [{"kind": "bed", "name": "bed", "x": 600, "y": 600, "w": 800, "d": 800, "h": 600}]}
    f = next(x for x in P.check(spec)["findings"] if x["rule"] == "camera_has_a_reason")
    assert f["status"] == P.WARN and "no valid shot" in f["detail"], f


def test_camera_reason_never_fails_a_deliverable():
    # SAFETY PIN (scrutiny 2026-07-04): the camera rule must NEVER contribute a FAIL — it
    # validates the opt-in --eye camera, not what the automated pipeline renders, so a hard
    # FAIL would false-block non-eye deliverables. The packed-room no-shot case is the only
    # path that could FAIL; assert report() stays out of FAIL when the camera is the only issue.
    spec = {"room": {"outline_mm": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]},
            "builtins": [{"kind": "wall", "name": "block", "x": 200, "y": 200, "w": 1600, "d": 1600, "h": 2800}],
            "items": [{"kind": "bed", "name": "bed", "x": 600, "y": 600, "w": 800, "d": 800, "h": 600}]}
    cam = next(x for x in P.check(spec)["findings"] if x["rule"] == "camera_has_a_reason")
    assert cam["status"] != P.FAIL, cam


def test_camera_reason_none_for_inch_spec():
    # @0.1 inch specs render via build_rect (add_camera_and_light) — NO eye camera even under
    # --eye — so the rule must return None despite _normalize synthesising an outline_mm.
    assert _s(P.check(_inch_living(tv_y_in=6)), "camera_has_a_reason") is None


def test_camera_reason_warns_on_dead_wall_frame():
    # a big empty room with one tiny stool in a corner -> the far standing spot frames
    # almost all bare wall (low subject share) -> advisory WARN, never FAIL
    spec = {"room": {"outline_mm": [[0, 0], [8000, 0], [8000, 8000], [0, 8000]]},
            "items": [{"kind": "stool", "name": "stool", "x": 200, "y": 200, "w": 400, "d": 400, "h": 450}]}
    f = next(x for x in P.check(spec)["findings"] if x["rule"] == "camera_has_a_reason")
    assert f["status"] == P.WARN and "bare wall" in f["detail"], f


def test_camera_reason_none_without_a_framable_subject():
    # a rug-only room has nothing to frame -> not applicable (None), not a false WARN
    spec = {"room": {"outline_mm": [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]},
            "items": [{"kind": "rug", "name": "rug", "x": 500, "y": 500, "w": 2000, "d": 2000}],
            "builtins": []}
    assert _s(P.check(spec), "camera_has_a_reason") is None


def test_camera_reason_none_without_metric_outline():
    # no room.outline_mm and not an inch spec -> can't solve a standing spot -> None (degrade)
    spec = {"room": {"type": "loft"},
            "items": [{"kind": "bed", "name": "bed", "x": 0, "y": 0, "w": 2000, "d": 2000, "h": 600}]}
    assert _s(P.check(spec), "camera_has_a_reason") is None


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
    # The safety property: a fused TV must ABORT before a paid render EVEN WHEN the geometry
    # gate passes — that lives in the FUNCTION-escalation branch of _real_geometry_fn. Use a
    # WELL-FORMED spec (ceiling + a valid south door on the bed's FOOT wall) whose geometry
    # verdict is NOT FAIL, so the gate FAIL can ONLY be the fused-TV escalation. (Scrutiny
    # 2026-07-04: the earlier minimal spec FAILed suite_clearance on its own — missing
    # ceiling_mm — so verdict==FAIL held even with the escalation removed. This version
    # discriminates: delete the escalation line and geometry stays REVIEW/PASS -> test fails.)
    import repair_loop
    import suite_clearance
    spec = _bedroom(door_wall="south")            # bed foot faces south -> door on the FOOT wall (ok)
    spec["room"]["ceiling_mm"] = 2700
    spec["door"] = {"wall": "south", "x": 2500, "y": 0, "w": 900, "h": 1900, "swing": "in-left"}
    spec["builtins"].append({"name": "หัวเตียง/ทีวี built-in", "kind": "headboard_tv",
                             "x": 1970, "y": 5000, "w": 3330, "d": 574, "h": 2800})
    assert suite_clearance.report(spec)[1] != P.FAIL, suite_clearance.report(spec)   # geometry passes
    results, verdict = repair_loop._real_geometry_fn(spec, "")
    assert verdict == P.FAIL                       # fused TV ESCALATES a passing geometry to FAIL
    assert any(r["check"] == "function:tv_positioned" and r["status"] == P.FAIL for r in results)


TESTS = [test_good_tv_on_foot_wall_passes, test_tv_behind_head_fails, test_tv_over_bed_fails,
         test_tv_too_close_warns, test_bed_rotated_180_flips_front, test_living_sofa_is_the_viewer,
         test_living_tv_behind_sofa_fails, test_door_on_head_wall_fails, test_door_on_other_wall_passes,
         test_door_rule_skips_without_bed_or_door, test_fused_headboard_tv_is_flagged,
         test_no_tv_room_does_not_false_fail, test_name_only_tv_is_named_only_warn_not_fail,
         test_tv_named_console_does_not_hard_fail,
         test_real_bedroom_suite_tv_now_positioned, test_real_living_condo_tv_now_positioned,
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
         test_seat_in_front_of_tv_warns, test_seat_beside_tv_passes, test_seat_rule_none_without_tv,
         test_seat_beside_screen_within_old_band_passes, test_seat_just_in_front_of_viewer_warns,
         test_seat_rule_none_without_secondary_seat, test_real_living_condo_armchair_flagged_under_tv,
         test_kitchen_good_triangle_passes, test_kitchen_leg_too_far_warns,
         test_kitchen_single_long_leg_warns,
         test_kitchen_leg_too_tight_warns, test_kitchen_perimeter_too_large_warns,
         test_kitchen_rule_skips_without_full_triangle, test_kitchen_rule_skips_non_kitchen_rooms,
         test_bath_sink_in_subroom_is_not_a_kitchen_sink, test_real_kitchen_demo_triangle_passes,
         test_tv_mount_height_pass_when_mounted, test_tv_mount_height_warns_without_mount,
         test_tv_mount_height_warns_above_ceiling, test_tv_mount_height_none_for_generic_tv_or_console,
         test_tv_mount_height_warns_for_builtin_tv, test_real_specs_tv_now_mounted,
         test_camera_reason_passes_real_specs, test_camera_reason_warns_when_no_shot_exists,
         test_camera_reason_never_fails_a_deliverable, test_camera_reason_none_for_inch_spec,
         test_camera_reason_warns_on_dead_wall_frame, test_camera_reason_none_without_a_framable_subject,
         test_camera_reason_none_without_metric_outline,
         test_report_fail_on_fused_tv, test_report_pass_on_good_tv, test_report_review_on_warn_only,
         test_report_unwired_when_nothing_applies, test_inch_spec_normalized_to_mm,
         test_inch_spec_tv_in_front_passes, test_inch_spec_tv_behind_sofa_fails,
         test_malformed_item_missing_dims_does_not_crash, test_find_tv_prefers_positioned_over_named,
         test_normalize_depth_only_inch_not_misread,
         test_repair_loop_gate0_includes_function_and_fails_fused_tv]


# ---- FURNISHING COMPLETENESS (client-revision rules, 2026-07-12) ----
# _bedroom()'s bed: x2000-4000, y3000-5000, rot 0 -> foot faces -Y, so the HEAD is the +Y (north) end.
def _nightstand(x=1500, y=4500, w=400, d=500, h=450):
    return {"name": "โต๊ะข้างเตียง", "kind": "side_table", "x": x, "y": y, "w": w, "d": d, "h": h}


def test_bed_without_nightstand_warns():
    assert _s(P.check(_bedroom(nightstand=False)), "bed_has_nightstand") == P.WARN


def test_bed_with_nightstand_at_head_passes():
    assert _s(P.check(_bedroom_with(_nightstand(), nightstand=False)), "bed_has_nightstand") == P.PASS


def test_nightstand_at_the_foot_does_not_count():
    # same table, parked at the FOOT end (y1200 -> centre y1450 < bed centre 4000): not a nightstand
    assert _s(P.check(_bedroom_with(_nightstand(y=1200), nightstand=False)),
              "bed_has_nightstand") == P.WARN


def test_nightstand_across_the_room_does_not_count():
    # at the head end but 2.6 m away from the bed's west edge — out of arm's reach (>900mm)
    assert _s(P.check(_bedroom_with(_nightstand(x=-1200), nightstand=False)),
              "bed_has_nightstand") == P.WARN


def test_rotated_bed_tracks_its_head():
    # rot 0 -> head is the +Y (north) end: a table at y4500 IS beside the head
    assert _s(P.check(_bedroom_with(_nightstand(y=4500), nightstand=False)),
              "bed_has_nightstand") == P.PASS
    # rot 180 -> foot faces +Y, so the head swaps to the SOUTH (y3000) end: the SAME table is
    # now at the foot (WARN), and only a table at the south end counts (PASS)
    spec = _bedroom_with(_nightstand(y=4500), nightstand=False)
    spec["items"][0]["rot"] = 180
    assert _s(P.check(spec), "bed_has_nightstand") == P.WARN
    spec2 = _bedroom_with(_nightstand(y=2500), nightstand=False)
    spec2["items"][0]["rot"] = 180
    assert _s(P.check(spec2), "bed_has_nightstand") == P.PASS


def test_no_bed_no_nightstand_rule():
    assert _s(P.check(_living()), "bed_has_nightstand") is None


def test_bedside_table_judged_on_the_nightstand_band_not_the_lounge_band():
    # a bedside table must reach mattress height (~520-650). Judged as a LOUNGE side_table
    # (380-480) it false-WARNs — which is what PRJ-2026-002's real 520 mm ones were doing.
    tall = _bedroom_with(_nightstand(y=4500), nightstand=False)
    tall["items"][-1]["h"] = 550
    assert _s(P.check(tall), "furniture_dimensions") == P.PASS
    # ...but the SAME kind away from the bed is still a lounge table and still gets the lounge band
    lounge = _bedroom_with(_nightstand(x=5000, y=300), nightstand=False)
    lounge["items"][-1]["h"] = 550
    assert _s(P.check(lounge), "furniture_dimensions") == P.WARN
    # and a bedside table that is genuinely absurd (a 900 mm chest) still WARNs on its own band
    absurd = _bedroom_with(_nightstand(y=4500), nightstand=False)
    absurd["items"][-1]["h"] = 900
    assert _s(P.check(absurd), "furniture_dimensions") == P.WARN


# ---- nightstand deck vs mattress top — the RELATION the band cannot ask (P2i) ----
def test_nightstand_below_reach_warns():
    # the filed defect verbatim (C2#10): deck 520 beside a 600 mattress = -80 mm. The
    # nightstand BAND (380-700) passes it — the relation rule is what catches it.
    spec = _bedroom_with(_nightstand(y=4500), nightstand=False)
    spec["items"][-1]["h"] = 520
    rep = P.check(spec)
    assert _s(rep, "furniture_dimensions") == P.PASS      # the band is blind to it, by design
    assert _s(rep, "nightstand_vs_mattress") == P.WARN


def test_nightstand_at_reach_passes():
    # PRJ-2026-002's current 580 vs 600 (-20) and the p2r43 built +18 case both sit in band
    spec = _bedroom_with(_nightstand(y=4500), nightstand=False)
    spec["items"][-1]["h"] = 580
    assert _s(P.check(spec), "nightstand_vs_mattress") == P.PASS


def test_nightstand_towering_warns():
    spec = _bedroom_with(_nightstand(y=4500), nightstand=False)
    spec["items"][-1]["h"] = 900                          # crowds the sleeper's head space
    assert _s(P.check(spec), "nightstand_vs_mattress") == P.WARN


def test_nightstand_relation_needs_a_nightstand_and_a_bed_height():
    # absence of the table is bed_has_nightstand's finding; this rule stays silent
    assert _s(P.check(_bedroom(nightstand=False)), "nightstand_vs_mattress") is None
    # a table at the FOOT is not a nightstand -> not related to the mattress
    foot = _bedroom_with(_nightstand(y=2500), nightstand=False)
    assert _s(P.check(foot), "nightstand_vs_mattress") is None
    # a bed with no height claim: nothing to relate against, never a guess
    nb = _bedroom_with(_nightstand(y=4500), nightstand=False)
    nb["items"][0]["h"] = 0
    assert _s(P.check(nb), "nightstand_vs_mattress") is None
    # missing table h -> that table is skipped, not guessed (scaffold-only spec => PASS trivially
    # would be a silent pass, so assert the finding still reports over the remaining table)
    two = _bedroom_with(_nightstand(y=4500), _nightstand(x=2900, y=4500), nightstand=False)
    two["items"][-1]["h"] = 0
    two["items"][-2]["h"] = 520
    assert _s(P.check(two), "nightstand_vs_mattress") == P.WARN
    # and when NO deck carries a height, the rule is not applicable — a PASS claiming
    # "decks within band" over zero measured decks would be a silent pass (scrutiny catch)
    none_measurable = _bedroom_with(_nightstand(y=4500), nightstand=False)
    none_measurable["items"][-1]["h"] = 0
    assert _s(P.check(none_measurable), "nightstand_vs_mattress") is None


def _dining(kind="dining_table", name="โต๊ะกินข้าว 6 ที่นั่ง"):
    return {"name": name, "kind": kind, "x": 1000, "y": 1000, "w": 1800, "d": 900, "h": 750}


def test_dining_table_correct_kind_passes():
    assert _s(P.check(_bedroom_with(_dining())), "dining_table_pendant") == P.PASS


def test_dining_table_miskinded_warns():
    # authored as a generic 'table' -> lighting.py hangs NO pendant over it (the client's complaint)
    assert _s(P.check(_bedroom_with(_dining(kind="table"))), "dining_table_pendant") == P.WARN
    assert _s(P.check(_bedroom_with(_dining(kind="round_table"))), "dining_table_pendant") == P.WARN


def test_english_dining_name_also_caught():
    assert _s(P.check(_bedroom_with(_dining(kind="table", name="Dining table (6 seat)"))),
              "dining_table_pendant") == P.WARN


def test_non_dining_table_not_flagged():
    # a coffee table / console must NOT be mistaken for a dining table
    assert _s(P.check(_bedroom_with(_dining(kind="coffee_table", name="โต๊ะกลาง"))),
              "dining_table_pendant") is None


def test_formal_thai_dining_name_caught():
    # โต๊ะรับประทานอาหาร = the formal Thai for dining table; the รับประทาน infix must not hide it
    assert _s(P.check(_bedroom_with(_dining(kind="table", name="โต๊ะรับประทานอาหาร"))),
              "dining_table_pendant") == P.WARN


def test_seat_count_table_name_caught():
    # the studio's house style names by seat count (cf. living_condo 'โต๊ะทานข้าว 4 ที่')
    assert _s(P.check(_bedroom_with(_dining(kind="table", name="โต๊ะ 6 ที่นั่ง"))),
              "dining_table_pendant") == P.WARN


def test_dining_named_chairs_do_not_false_warn():
    # a CORRECT dining room: a real dining_table + chairs named 'Dining Chair N'. The chairs are
    # not table-family kinds, so the rule must PASS on the table and never WARN on the chairs
    # (the old \bdining\b regex WARNed all four and told the user to re-kind a chair as a table).
    spec = _bedroom_with(
        _dining(kind="dining_table", name="Dining Table"),
        {"name": "Dining Chair 1", "kind": "chair", "x": 900, "y": 500, "w": 450, "d": 450, "h": 900},
        {"name": "Dining Chair 2", "kind": "dining_chair", "x": 1400, "y": 500, "w": 450, "d": 450, "h": 900},
        {"name": "Dining Pendant", "kind": "pendant", "x": 1200, "y": 1200, "w": 300, "d": 300, "h": 400},
        {"name": "Dining area rug", "kind": "rug", "x": 800, "y": 800, "w": 2000, "d": 1400, "h": 5})
    assert _s(P.check(spec), "dining_table_pendant") == P.PASS


def test_dining_chair_alone_is_not_a_slipped_table():
    # a bare 'Dining Chair' (no table in the room) must not itself trigger the rule
    assert _s(P.check(_bedroom_with(
        {"name": "Dining Chair", "kind": "chair", "x": 900, "y": 500, "w": 450, "d": 450, "h": 900})),
        "dining_table_pendant") is None


def _bath_sub(*fixtures):     # NOT _bath — that name is already taken at the top of this file
    return {"room": {"outline_mm": [[0, 0], [6000, 0], [6000, 6000], [0, 6000]]},
            "items": [], "builtins": [],
            "subrooms": [{"name": "ห้องน้ำ", "type": "bathroom",
                          "outline_mm": [[0, 0], [2400, 0], [2400, 2400], [0, 2400]],
                          "door": {"wall": "south", "x": 900, "y": 0, "w": 800},
                          "fixtures": list(fixtures)}]}


def _basin(kind="basin", x=200, y=1800):
    return {"name": "อ่างล้างหน้า", "kind": kind, "x": x, "y": y, "w": 600, "d": 450, "h": 850}


def _cab(x=200, y=1800):
    return {"name": "ตู้ใต้อ่าง", "kind": "cabinet", "x": x, "y": y, "w": 600, "d": 450, "h": 800}


def test_bare_basin_without_storage_warns():
    assert _s(P.check(_bath_sub(_basin())), "basin_has_storage") == P.WARN


def test_basin_with_cabinet_under_it_passes():
    assert _s(P.check(_bath_sub(_basin(), _cab())), "basin_has_storage") == P.PASS


def test_cabinet_across_the_room_does_not_count():
    assert _s(P.check(_bath_sub(_basin(), _cab(x=1900, y=200))), "basin_has_storage") == P.WARN


def test_vanity_is_not_a_bare_basin():
    # a 'vanity' IS basin+cabinet -> the rule must not apply at all (no finding, no silent PASS)
    assert _s(P.check(_bath_sub(_basin(kind="vanity"))), "basin_has_storage") is None


def test_kitchen_sink_is_not_a_bathroom_basin():
    # a main-room kitchen sink lives in a counter run and is the work-triangle rule's business;
    # basin_has_storage scans SUBROOMS only and must stay silent here
    spec = _bedroom_with({"name": "ซิงค์ครัว", "kind": "sink", "x": 500, "y": 500,
                          "w": 800, "d": 600, "h": 900})
    assert _s(P.check(spec), "basin_has_storage") is None


TESTS += [test_bed_without_nightstand_warns, test_bed_with_nightstand_at_head_passes,
          test_nightstand_at_the_foot_does_not_count, test_nightstand_across_the_room_does_not_count,
          test_rotated_bed_tracks_its_head, test_no_bed_no_nightstand_rule,
          test_bedside_table_judged_on_the_nightstand_band_not_the_lounge_band,
          test_dining_table_correct_kind_passes, test_dining_table_miskinded_warns,
          test_english_dining_name_also_caught, test_non_dining_table_not_flagged,
          test_formal_thai_dining_name_caught, test_seat_count_table_name_caught,
          test_dining_named_chairs_do_not_false_warn, test_dining_chair_alone_is_not_a_slipped_table,
          test_bare_basin_without_storage_warns, test_basin_with_cabinet_under_it_passes,
          test_cabinet_across_the_room_does_not_count, test_vanity_is_not_a_bare_basin,
          test_kitchen_sink_is_not_a_bathroom_basin]


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
