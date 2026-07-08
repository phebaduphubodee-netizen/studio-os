"""
test_cross_signal.py -- unit tests for the cross-signal self-doubt check.

Pins every check firing + every abstain/suppress path, the two-layer suppression law
(owner sign -> no flag), honest coverage (no eligible data is DISTINGUISHABLE from clean),
and the flagship REAL case: on v4 scene-graph.sitting_room.json the owner-signed tub chairs
facing the corroborated south glass must NOT be flagged by check (a).
"""
import json
import os

import cross_signal as X

HERE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.normpath(os.path.join(
    HERE, "..", "..", "projects", "PRJ-2026-002_c001-house", "03_layout", "v4"))


def _load(name):
    with open(os.path.join(V4, name), encoding="utf-8") as fh:
        return json.load(fh)


def _rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _spec(items=None, builtins=None, subrooms=None, rtype="sitting_room", outline=None):
    return {"schema": "interior-ai/room-spec@0.2",
            "room": {"type": rtype, "wall_thk_mm": 100,
                     "outline_mm": outline or _rect(0, 0, 4000, 4000)},
            "builtins": builtins or [], "items": items or [], "subrooms": subrooms or []}


def _sig(check, records):
    return [r for r in records if r["signal"] == f"cross_signal:{check}"]


# ======================================================================================
# (a) facing_vs_kind
# ======================================================================================
def test_a_chair_jammed_against_solid_north_wall_fires():
    # chair near the north wall (y~4000), rot 180 -> front points NORTH into the wall; room open
    # to the south behind it; a solid horizontal wall runs the full north edge.
    chair = {"name": "reading chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180}
    walls = [[[0, 4000], [4000, 4000]]]                       # full north wall
    recs = _sig("facing_vs_kind", X.check_room(_spec(items=[chair]), walls=walls))
    assert len(recs) == 1
    assert recs[0]["severity"] == "HIGH" and recs[0]["subjects"] == ["reading chair"]


def test_a_owner_signed_facing_suppresses_the_flag():
    # SAME jammed chair, but the owner signed the facing (two-layer law) -> no flag.
    chair = {"name": "reading chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180, "facing_source": "owner-signed"}
    walls = [[[0, 4000], [4000, 4000]]]
    assert _sig("facing_vs_kind", X.check_room(_spec(items=[chair]), walls=walls)) == []


def test_a_owner_signed_via_confirmed_ledger_suppresses():
    chair = {"name": "reading chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180}
    walls = [[[0, 4000], [4000, 4000]]]
    confirmed = [{"name": "reading chair", "rot": 180, "w": 500, "d": 500, "by": "owner"}]
    recs = _sig("facing_vs_kind",
                X.check_room(_spec(items=[chair]), walls=walls, params={"confirmed": confirmed}))
    assert recs == []


def test_a_seat_far_from_wall_does_not_fire():
    # front clearance large (open room in front) -> not a wall-facer (the sofa case)
    chair = {"name": "chair", "kind": "chair", "x": 1750, "y": 1750,
             "w": 500, "d": 500, "rot": 180}
    walls = [[[0, 4000], [4000, 4000]]]
    assert _sig("facing_vs_kind", X.check_room(_spec(items=[chair]), walls=walls)) == []


def test_a_no_wall_evidence_abstains():
    # jammed chair but NO walls provided -> glass-vs-wall unknown -> ABSTAIN (never guess)
    chair = {"name": "chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180}
    assert _sig("facing_vs_kind", X.check_room(_spec(items=[chair]))) == []


def test_a_seat_facing_corroborated_south_glass_never_fires():
    # a tub-chair-like seat hard against the south edge, facing it -- but the edge is
    # corroborated GLASS (the view) -> never a flag, even jammed close.
    chair = {"name": "tub", "kind": "armchair", "x": 1750, "y": 100,
             "w": 600, "d": 600, "rot": 0}                    # rot 0 -> faces SOUTH (ymin)
    outline = _rect(0, 0, 4000, 4000)
    glazing = [{"axis": "h", "c": 90.0, "score": 5, "span": [0, 4000]}]  # strong south glass
    walls = []                                                # south edge OPEN (no wall)
    assert _sig("facing_vs_kind",
                X.check_room(_spec(items=[chair], outline=outline),
                             walls=walls, glazing_cands=glazing)) == []


def test_a_seat_facing_corroborated_east_glass_never_fires():
    # a view chair hard against the EAST edge facing it, where that edge is corroborated GLASS on a
    # NON-south facade. The generalised glass exoneration must spare it -- the old south-only guard
    # would have falsely accused a genuine view-facer here. rot 90 -> faces EAST (xmax). A wall on the
    # same edge would otherwise make it fire, so this proves the glazing spares it, not the wall gate.
    chair = {"name": "view chair", "kind": "armchair", "x": 3400, "y": 1750,
             "w": 500, "d": 500, "rot": 90}
    outline = _rect(0, 0, 4000, 4000)
    glazing = [{"axis": "v", "c": 4010.0, "score": 5, "span": [0, 4000]}]  # strong east glass
    walls = [[[4000, 0], [4000, 4000]]]                                    # a wall on the same edge
    assert _sig("facing_vs_kind",
                X.check_room(_spec(items=[chair], outline=outline),
                             walls=walls, glazing_cands=glazing)) == []


def test_a_seat_facing_east_solid_wall_still_fires():
    # the mirror guard: the SAME east-facing view chair against a solid east wall with NO glazing
    # DOES fire (the generalised exoneration must not blind the genuine east wall-facer).
    chair = {"name": "view chair", "kind": "armchair", "x": 3400, "y": 1750,
             "w": 500, "d": 500, "rot": 90}
    outline = _rect(0, 0, 4000, 4000)
    walls = [[[4000, 0], [4000, 4000]]]
    recs = _sig("facing_vs_kind",
                X.check_room(_spec(items=[chair], outline=outline), walls=walls))
    assert len(recs) == 1 and recs[0]["severity"] == "HIGH"


def test_a_seat_without_rot_abstains():
    chair = {"name": "bench", "kind": "bench", "x": 1750, "y": 3400, "w": 500, "d": 500}
    walls = [[[0, 4000], [4000, 4000]]]
    assert _sig("facing_vs_kind", X.check_room(_spec(items=[chair]), walls=walls)) == []


def test_a_wall_behind_too_alcove_does_not_fire():
    # both front AND back are walls (a tight alcove) -> not clearly wrong -> no flag
    chair = {"name": "chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180}
    tiny = _rect(0, 3300, 4000, 4000)         # only ~700mm deep -> back clearance < seat_back_open
    walls = [[[0, 4000], [4000, 4000]]]
    assert _sig("facing_vs_kind",
                X.check_room(_spec(items=[chair], outline=tiny), walls=walls)) == []


# ======================================================================================
# (b) function_vs_placement
# ======================================================================================
def test_b_desk_with_no_seat_fires_medium():
    desk = {"name": "desk", "kind": "desk", "x": 100, "y": 100, "w": 1200, "d": 600}
    recs = _sig("function_vs_placement", X.check_room(_spec(items=[desk])))
    assert len(recs) == 1 and recs[0]["severity"] == "MEDIUM"


def test_b_desk_with_a_chair_in_reach_does_not_fire():
    desk = {"name": "desk", "kind": "desk", "x": 100, "y": 100, "w": 1200, "d": 600}
    chair = {"name": "chair", "kind": "chair", "x": 400, "y": 750, "w": 500, "d": 500}
    assert _sig("function_vs_placement", X.check_room(_spec(items=[desk, chair]))) == []


def test_b_tv_with_nothing_facing_fires_low():
    # a TV on the east wall + a sofa that faces WEST (away) -> LOW advisory
    tv = {"name": "TV panel", "kind": "tv_panel", "x": 3900, "y": 1800, "w": 100, "d": 400}
    sofa = {"name": "sofa", "kind": "sofa", "x": 500, "y": 1700, "w": 2000, "d": 900, "rot": 270}
    recs = _sig("function_vs_placement", X.check_room(_spec(items=[tv, sofa])))
    tvrecs = [r for r in recs if "TV" in r["detail"] or "faces" in r["detail"]]
    assert any(r["severity"] == "LOW" for r in tvrecs)


def test_b_tv_with_a_sofa_facing_it_does_not_fire():
    tv = {"name": "TV panel", "kind": "tv_panel", "x": 3900, "y": 1800, "w": 100, "d": 400}
    sofa = {"name": "sofa", "kind": "sofa", "x": 500, "y": 1700, "w": 2000, "d": 900, "rot": 90}
    recs = _sig("function_vs_placement", X.check_room(_spec(items=[tv, sofa])))
    assert not any("no seating/bed is oriented" in r["detail"] for r in recs)


def test_b_tv_abstains_when_room_has_no_seating():
    tv = {"name": "TV panel", "kind": "tv_panel", "x": 3900, "y": 1800, "w": 100, "d": 400}
    assert _sig("function_vs_placement", X.check_room(_spec(items=[tv]))) == []


# ======================================================================================
# (c) zone_vs_geometry
# ======================================================================================
def test_c_below_grade_label_on_inside_piece_fires_high():
    piece = {"name": "planter", "kind": "planter", "x": 1800, "y": 1800,
             "w": 400, "d": 400, "zone": "below_grade"}
    recs = _sig("zone_vs_geometry", X.check_room(_spec(items=[piece])))
    assert len(recs) == 1 and recs[0]["severity"] == "HIGH"


def test_c_owner_signed_zone_suppresses():
    # owner deliberately signed below_grade for an inside-drawn void -> two-layer law -> no flag
    piece = {"name": "void", "kind": "opening", "x": 1800, "y": 1800, "w": 400, "d": 400,
             "zone": "below_grade", "zone_source": "owner-signed"}
    assert _sig("zone_vs_geometry", X.check_room(_spec(items=[piece]))) == []


def test_c_indoor_or_unlabelled_piece_does_not_fire():
    piece = {"name": "table", "kind": "side_table", "x": 1800, "y": 1800, "w": 400, "d": 400}
    assert _sig("zone_vs_geometry", X.check_room(_spec(items=[piece]))) == []


def test_c_outdoor_label_truly_outside_does_not_fire():
    # labelled outdoor AND drawn well outside the outline -> reads consistent -> no contradiction
    piece = {"name": "tree", "kind": "tree", "x": 1800, "y": -3000, "w": 400, "d": 400,
             "zone": "below_grade"}
    assert _sig("zone_vs_geometry", X.check_room(_spec(items=[piece]))) == []


# ======================================================================================
# (d) facade_vs_wall
# ======================================================================================
def test_d_glass_claimed_where_wall_runs_fires_medium():
    # a strong glazing line on the south edge WHILE a full wall covers that edge -> contradiction
    outline = _rect(0, 0, 4000, 4000)
    glazing = [{"axis": "h", "c": 40.0, "score": 5, "span": [0, 4000]}]
    walls = [[[0, 0], [4000, 0]]]                             # full south wall
    recs = _sig("facade_vs_wall",
                X.check_room(_spec(outline=outline), walls=walls, glazing_cands=glazing))
    assert len(recs) == 1 and recs[0]["severity"] == "MEDIUM"


def test_d_open_glass_facade_does_not_fire():
    outline = _rect(0, 0, 4000, 4000)
    glazing = [{"axis": "h", "c": 40.0, "score": 5, "span": [0, 4000]}]
    walls = []                                                # south edge OPEN -> real glass facade
    assert _sig("facade_vs_wall",
                X.check_room(_spec(outline=outline), walls=walls, glazing_cands=glazing)) == []


# ======================================================================================
# (e) ffe_vs_room
# ======================================================================================
def test_e_toilet_in_living_room_fires_high():
    toilet = {"name": "WC", "kind": "toilet", "x": 200, "y": 200, "w": 400, "d": 700}
    recs = _sig("ffe_vs_room",
                X.check_room(_spec(items=[toilet], rtype="living_room")))
    assert len(recs) == 1 and recs[0]["severity"] == "HIGH"


def test_e_stove_in_bedroom_fires_high():
    stove = {"name": "hob", "kind": "stove", "x": 200, "y": 200, "w": 600, "d": 600}
    recs = _sig("ffe_vs_room", X.check_room(_spec(items=[stove], rtype="bedroom")))
    assert len(recs) == 1 and recs[0]["severity"] == "HIGH"


def test_e_toilet_in_bathroom_subroom_is_fine():
    # the SAME toilet inside a subroom typed 'bathroom' is compatible -> no flag
    sub = {"name": "ensuite", "type": "bathroom", "outline_mm": _rect(0, 0, 2000, 2000),
           "fixtures": [{"name": "WC", "kind": "toilet", "x": 200, "y": 200, "w": 400, "d": 700}]}
    recs = _sig("ffe_vs_room",
                X.check_room(_spec(rtype="bedroom", subrooms=[sub])))
    assert recs == []


def test_e_unknown_room_type_abstains():
    toilet = {"name": "WC", "kind": "toilet", "x": 200, "y": 200, "w": 400, "d": 700}
    recs = _sig("ffe_vs_room", X.check_room(_spec(items=[toilet], rtype="mystery_zone")))
    assert recs == []


# ======================================================================================
# honest coverage
# ======================================================================================
def test_coverage_distinguishes_eligible_from_skipped():
    # a room with a seat+rot+walls but no surface/TV/zone/glazing: (a) eligible, others skipped
    chair = {"name": "chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180}
    cov = X.check_coverage(_spec(items=[chair]), walls=[[[0, 4000], [4000, 4000]]])
    assert cov["facing_vs_kind"]["eligible"] is True
    assert cov["function_vs_placement"]["eligible"] is False
    assert cov["facade_vs_wall"]["eligible"] is False        # no glazing candidates
    assert cov["zone_vs_geometry"]["eligible"] is False      # no non-indoor label


def test_coverage_facing_skipped_without_wall_evidence_is_not_a_pass():
    # a seat with rot but NO wall/glazing evidence: NOT eligible -> silence != clean
    chair = {"name": "chair", "kind": "chair", "x": 1750, "y": 3400,
             "w": 500, "d": 500, "rot": 180}
    cov = X.check_coverage(_spec(items=[chair]))
    assert cov["facing_vs_kind"]["eligible"] is False
    assert "wall/glazing" in cov["facing_vs_kind"]["reason"]


def test_coverage_empty_room_all_skipped():
    cov = X.check_coverage(_spec())
    assert all(v["eligible"] is False for v in cov.values())


# ======================================================================================
# REAL DATA -- the flagship: v4 sitting room, owner-signed tub chairs face the glass
# ======================================================================================
def test_real_v4_sitting_room_tub_chairs_not_flagged():
    spec = _load("scene-graph.sitting_room.json")
    glz = _load("glazing-candidates.json").get("candidates")
    walls = _load("floor2-walls-mm.json").get("segments")
    review = _load("placement-review.json")
    confirmed = review.get("confirmed")

    recs = X.check_room(spec, walls=walls, glazing_cands=glz,
                        params={"confirmed": confirmed})
    facing = _sig("facing_vs_kind", recs)
    # HARD REQUIREMENT: neither tub chair is flagged (they face the corroborated south glass
    # AND their facing is owner-signed) -- and no seating in the room is a false wall-facer.
    assert facing == [], f"unexpected facing flags on the real sitting room: {facing}"


def test_real_v4_sitting_room_no_false_positive_anywhere():
    spec = _load("scene-graph.sitting_room.json")
    glz = _load("glazing-candidates.json").get("candidates")
    walls = _load("floor2-walls-mm.json").get("segments")
    confirmed = _load("placement-review.json").get("confirmed")
    recs = X.check_room(spec, walls=walls, glazing_cands=glz, params={"confirmed": confirmed})
    # the sofa faces the BF13 TV -> (b) must not flag 'nothing faces the TV'; no wet/kitchen
    # fixtures -> (e) clean; the corroborated OPEN glass facade -> (d) clean.
    assert not any("no seating/bed is oriented" in r["detail"] for r in recs)
    assert _sig("ffe_vs_room", recs) == []
    assert _sig("facade_vs_wall", recs) == []


def test_real_v4_master_bedroom_no_false_positive():
    spec = _load("scene-graph.master_bedroom.json")
    glz = _load("glazing-candidates.json").get("candidates")
    walls = _load("floor2-walls-mm.json").get("segments")
    confirmed = _load("placement-review.json").get("confirmed")
    recs = X.check_room(spec, walls=walls, glazing_cands=glz, params={"confirmed": confirmed})
    # ensuite toilet/bathtub/shower are in a 'bathroom' subroom -> (e) must NOT flag them;
    # the bench (no rot) and the west-facing desk chair are not wall-facers.
    assert _sig("ffe_vs_room", recs) == []
    assert _sig("facing_vs_kind", recs) == []


def test_real_v4_coverage_reports_read_sources():
    spec = _load("scene-graph.sitting_room.json")
    glz = _load("glazing-candidates.json").get("candidates")
    walls = _load("floor2-walls-mm.json").get("segments")
    cov = X.check_coverage(spec, walls=walls, glazing_cands=glz)
    assert cov["facing_vs_kind"]["eligible"] is True         # sofa+tub chairs carry rot
    assert cov["facade_vs_wall"]["eligible"] is True         # walls + glazing both present
    assert cov["ffe_vs_room"]["eligible"] is True            # sitting_room is a classifiable dry room


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} cross_signal tests passed")
