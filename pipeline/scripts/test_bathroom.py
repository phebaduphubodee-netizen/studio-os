"""Unit tests for bathroom.py (pure ensuite fixture massing). Run: python -m pytest."""
import copy
import json
import os

import pytest

import bathroom as B

KNOWN_MATS = {"porcelain", "stone", "oak", "brass", "glass", "tray", "mirror",
              "blackalu", "opal",   # element-5 task-bar roles (D-E5-5)
              "towel"}              # element-6 terry textiles (D-E6-3, ONE token)


def test_every_emittable_mat_has_a_router_row():
    """The consumer's mat->object router is a CLOSED vocabulary that RAISES on unknowns
    (material_presets.FIXTURE_MAT_OBJECT, director review 2026-07-21). Every mat this
    module may emit must therefore hold a row there — otherwise a fixture that renders
    fine today explodes at build time the day its branch is exercised."""
    import material_presets as mp
    assert KNOWN_MATS <= set(mp.FIXTURE_MAT_OBJECT), \
        f"mats without a router row: {KNOWN_MATS - set(mp.FIXTURE_MAT_OBJECT)}"

# ink-true footprints from element4-ensuite_ink-read-2026-07-18.json
VANITY = {"kind": "vanity_double", "name": "vanity", "x": 1077, "y": 5923, "w": 2047, "d": 654, "h": 850,
          "design": {"counter_x0_mm": 77, "counter_len_mm": 3047, "basin_ctr_x_mm": [1576.9, 2627.5]}}
WC = {"kind": "toilet", "name": "wc", "x": 55, "y": 6031, "w": 685, "d": 609, "h": 800}
TUB = {"kind": "bathtub", "name": "tub", "x": 1125, "y": 7596, "w": 2000, "d": 978, "h": 560}
SHOWER = {"kind": "shower", "name": "shower", "x": 55, "y": 7320, "w": 1070, "d": 1276, "h": 2200}
PART = {"kind": "glass_partition", "name": "partition", "x": 1125, "y": 7329, "w": 10, "d": 1266, "h": 2000}


def _all_positive(parts):
    return all(p["dx"] > 0 and p["dy"] > 0 and p["dz"] > 0 for p in parts)


def _mats_known(parts):
    return {p["mat"] for p in parts} <= KNOWN_MATS


def _bbox(p):
    return (p["x"], p["y"], p["x"] + p["dx"], p["y"] + p["dy"])


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _bbox(a)
    bx0, by0, bx1, by1 = _bbox(b)
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def test_all_fixtures_produce_positive_boxes_with_known_mats():
    for fx in (VANITY, WC, TUB, SHOWER, PART):
        parts = B.fixture_parts(fx)
        assert parts, f"{fx['kind']} produced no parts"
        assert _all_positive(parts), f"{fx['kind']} has a zero/negative box"
        assert _mats_known(parts), f"{fx['kind']} has an unknown material role"


def test_unknown_kind_falls_back_to_empty():
    assert B.fixture_parts({"kind": "sofa", "x": 0, "y": 0, "w": 1, "d": 1, "h": 1}) == []


def test_vanity_has_oak_cabinet_stone_counter_two_porcelain_basins_two_brass_taps():
    parts = {p["name"]: p for p in B.vanity_parts(VANITY)}
    assert parts["vanity_cabinet"]["mat"] == "oak"
    assert parts["vanity_counter"]["mat"] == "stone"
    basins = [p for n, p in parts.items() if "basin" in n]
    taps = [p for n, p in parts.items() if "tap" in n]
    assert len(basins) == 2 and all(p["mat"] == "porcelain" for p in basins)
    assert len(taps) == 2 and all(p["mat"] == "brass" for p in taps)


def test_vanity_counter_spans_the_full_3047_run_but_cabinet_does_not():
    parts = {p["name"]: p for p in B.vanity_parts(VANITY)}
    counter, ledge, cab = parts["vanity_counter"], parts["vanity_ledge"], parts["vanity_cabinet"]
    # counter (deep, over cabinet) + west ledge together cover x77..3124 (=3047)
    west = min(counter["x"], ledge["x"])
    east = max(counter["x"] + counter["dx"], ledge["x"] + ledge["dx"])
    assert abs(west - 77) < 2 and abs((east - west) - 3047) < 40, (west, east)
    # the OAK cabinet must NOT extend west of x1077 (else it builds through the SW WC)
    assert cab["x"] >= 1077 - 1, f"oak cabinet west edge {cab['x']} intrudes on the WC zone"


def test_vanity_oak_stays_a_low_accent_not_a_full_height_mass():
    # D1-A anti-monopoly: the oak gesture is the LOW cabinet body, never a wall-height block
    cab = next(p for p in B.vanity_parts(VANITY) if p["name"] == "vanity_cabinet")
    assert cab["z"] + cab["dz"] <= 850, "oak cabinet taller than the 850 counter — not a low accent"


def test_vanity_builds_the_decided_mirror_above_the_counter():
    # D-E4-2: the full-width frameless mirror is a DECIDED element — it must be BUILT, not
    # left to a note (the revert-by-omission trap). Above the counter, routed to the mirror role.
    mir = next((p for p in B.vanity_parts(VANITY) if "mirror" in p["name"]), None)
    assert mir is not None, "vanity mirror (D-E4-2) is missing — a decided element omitted"
    assert mir["mat"] == "mirror"
    assert mir["z"] >= VANITY["h"], "mirror must sit ABOVE the counter, not on/behind it"


def test_wc_does_not_collide_with_the_vanity_cabinet():
    cab = next(p for p in B.vanity_parts(VANITY) if p["name"] == "vanity_cabinet")
    for wp in B.toilet_parts(WC):
        assert not _overlap(wp, cab), f"WC part {wp['name']} overlaps the oak vanity cabinet"


def test_wc_tank_sits_at_the_west_wall_and_bowl_projects_east():
    parts = {p["name"]: p for p in B.toilet_parts(WC)}
    assert parts["wc_tank"]["x"] <= parts["wc_bowl"]["x"], "tank must be west of the bowl"


def test_tub_is_an_open_recess_four_aprons_plus_floor_plus_stone_deck():
    parts = {p["name"]: p for p in B.bathtub_parts(TUB)}
    for edge in ("apron_s", "apron_n", "apron_w", "apron_e"):
        assert f"tub_{edge}" in parts and parts[f"tub_{edge}"]["mat"] == "porcelain"
    assert parts["tub_floor"]["dz"] < TUB["h"], "tub floor must be below the rim (a recess)"
    assert any(p["mat"] == "stone" for n, p in parts.items() if "deck" in n), "no stone deck cap"


def test_shower_has_glass_screen_tray_and_brass_head():
    parts = {p["name"]: p for p in B.shower_parts(SHOWER)}
    assert parts["shower_screen"]["mat"] == "glass"
    assert parts["shower_tray"]["mat"] == "tray"
    assert parts["shower_head"]["mat"] == "brass"


def test_glass_partition_is_one_thin_glass_panel():
    parts = B.glass_partition_parts(PART)
    assert len(parts) == 1 and parts[0]["mat"] == "glass"
    assert parts[0]["dx"] >= B.GLASS_T - 0.01, "partition thinner than a glass panel"


def test_all_fixture_parts_aggregates_every_fixture():
    total = B.all_fixture_parts([VANITY, WC, TUB, SHOWER, PART])
    assert len(total) == sum(len(B.fixture_parts(fx)) for fx in (VANITY, WC, TUB, SHOWER, PART))


# ======================================================================================
# ELEMENT 6 (D-E6-3/-4/-5): the Purist accessory set + textiles (accessory_parts)
# ======================================================================================

CENSUS = {"bath_on_bar": 2, "hand_on_south_hook": 1, "hand_on_counter": 1,
          "robes_on_north_hook": 2, "bath_mat": 1}
DOOR = {"id": "door-ensuite", "type": "door", "rect": [3150, 6596, 3150, 7596]}
ACC = {"kind": "bath_accessories", "name": "acc",
       "design": {"census": dict(CENSUS), "bar_len_mm": 610}}
SUBROOM = {"outline_mm": [[0, 5850], [3150, 5850], [3150, 8650], [0, 8650]],
           "openings": [DOOR], "fixtures": [VANITY, WC, TUB, SHOWER, PART, ACC]}


def _acc_parts(acc=None, subroom=None):
    return B.accessory_parts(acc or copy.deepcopy(ACC), subroom or SUBROOM)


def _boxes_overlap_3d(a, b):
    return (a["x"] < b["x"] + b["dx"] and b["x"] < a["x"] + a["dx"]
            and a["y"] < b["y"] + b["dy"] and b["y"] < a["y"] + a["dy"]
            and a["z"] < b["z"] + b["dz"] and b["z"] < a["z"] + a["dz"])


def test_accessories_emit_bar_hooks_holder_all_brass():
    parts = {p["name"]: p for p in _acc_parts()}
    hardware = ["acc_towelbar_rail", "acc_towelbar_post0", "acc_towelbar_post1",
                "acc_robe_hook_s", "acc_robe_hook_n", "acc_paper_holder"]
    for nm in hardware:
        assert nm in parts, f"{nm} missing — the locked Purist row was not built"
        assert parts[nm]["mat"] == "brass", f"{nm} must ride the EXISTING brass row"


def test_every_census_entry_materializes_a_soft_mass():
    """D-E6-3 probe: hardware succeeding with zero textiles must fail — the census is
    the ONE towel inventory and every entry becomes a 'towel' part."""
    soft = [p for p in _acc_parts() if p["mat"] == "towel"]
    assert len(soft) == sum(CENSUS.values())
    names = {p["name"] for p in soft}
    assert {"acc_bath_towel0", "acc_bath_towel1", "acc_hand_towel_hook0",
            "acc_hand_towel_counter0", "acc_robe0", "acc_robe1",
            "acc_bath_mat0"} == names


def test_textiles_all_wear_the_one_towel_token():
    for p in _acc_parts():
        assert p["mat"] in ("brass", "towel"), \
            f"{p['name']}: accessories emit only brass hardware + towel textiles"


def test_bar_sits_on_the_west_wall_in_the_wc_to_curb_segment():
    parts = {p["name"]: p for p in _acc_parts()}
    rail = parts["acc_towelbar_rail"]
    wc_n = WC["y"] + WC["d"]            # 6640
    curb_s = SHOWER["y"]                # 7320
    assert rail["y"] >= wc_n and rail["y"] + rail["dy"] <= curb_s, \
        "bar must live between the WC north edge and the shower curb"
    assert rail["dy"] == pytest.approx(610), "the locked 24in row (bar_len_mm data)"
    assert rail["x"] < 200, "bar must hug the WEST (x55) wall plane"


def test_bar_18in_fallback_is_spec_data_not_code():
    """The 18in fallback lives in bar_len_mm (spec data, the schedule FILE untouched).
    INTERPLAY, disclosed: a 457 bar cannot carry 2 x 280 towels side by side — taking
    the fallback forces the census question back to the owner (the guard below RAISES
    loud rather than interpenetrating the towels silently)."""
    acc = copy.deepcopy(ACC)
    acc["design"]["bar_len_mm"] = 457
    acc["design"]["census"]["bath_on_bar"] = 1
    rail = next(p for p in _acc_parts(acc) if p["name"] == "acc_towelbar_rail")
    assert rail["dy"] == pytest.approx(457)
    acc["design"]["census"]["bath_on_bar"] = 2
    with pytest.raises(ValueError, match="interpenetrate"):
        _acc_parts(acc)


def test_bar_that_cannot_fit_its_segment_raises():
    acc = copy.deepcopy(ACC)
    acc["design"]["bar_len_mm"] = 700    # segment is only ~680
    with pytest.raises(ValueError, match="fallback"):
        _acc_parts(acc)


def test_census_overfilling_the_bar_raises():
    acc = copy.deepcopy(ACC)
    acc["design"]["census"]["bath_on_bar"] = 3   # 3 x 280 > 610
    with pytest.raises(ValueError, match="interpenetrate"):
        _acc_parts(acc)


def test_paper_holder_is_north_of_the_cistern_and_clear_of_it():
    """D-E6-3 probe (the DD's collision fix): the drafted holder band landed ON the
    built wc_tank massing — the re-sited holder must clear every WC part in 3D."""
    holder = next(p for p in _acc_parts() if p["name"] == "acc_paper_holder")
    assert holder["y"] >= WC["y"] + WC["d"] - 1, "holder must start NORTH of the WC"
    for wp in B.toilet_parts(WC):
        assert not _boxes_overlap_3d(holder, wp), f"holder collides with {wp['name']}"
    bar_parts = [p for p in _acc_parts() if "towel" in p["name"] or "bar" in p["name"]]
    for bp in bar_parts:
        assert not _boxes_overlap_3d(holder, bp), f"holder collides with {bp['name']}"


def test_mat_centre_derives_from_the_built_shower_entry_gap():
    """D-E6-4 probe: never a hardcoded x — shift the shower and the mat must follow
    the SAME SCREEN_FRAC-derived gap shower_parts builds."""
    for dx in (0, 300):
        sh = dict(SHOWER, x=SHOWER["x"] + dx)
        sub = {**SUBROOM, "fixtures": [VANITY, WC, TUB, sh, PART, ACC]}
        mat = next(p for p in _acc_parts(subroom=sub) if p["name"] == "acc_bath_mat0")
        g0, g1 = B.shower_entry_gap(sh)
        assert mat["x"] + mat["dx"] / 2 == pytest.approx((g0 + g1) / 2), \
            "mat centre != built entry-gap centre"
        screen = next(p for p in B.shower_parts(sh) if p["name"] == "shower_screen")
        assert screen["x"] + screen["dx"] == pytest.approx(g0), \
            "shower_entry_gap disagrees with the BUILT screen — two truths"


def test_mat_lies_in_the_dry_strip_south_of_the_curb():
    mat = next(p for p in _acc_parts() if p["name"] == "acc_bath_mat0")
    assert mat["y"] + mat["dy"] <= SHOWER["y"], "mat crosses the curb into the shower"
    assert mat["y"] >= VANITY["y"] + VANITY["d"], "mat runs under the vanity front"
    assert mat["z"] == 0 and mat["dz"] <= 25, "a flat MAT, not a mass"


def test_wet_dry_law_no_textile_in_the_wet_zone():
    """D-E6-5 probe: no textile part intersects the shower enclosure volume, any tub
    part (deck/aprons), or any glass part — nothing draped over glass or tub."""
    textiles = [p for p in _acc_parts() if p["mat"] == "towel"]
    shower_vol = {"x": SHOWER["x"], "y": SHOWER["y"], "z": 0,
                  "dx": SHOWER["w"], "dy": SHOWER["d"], "dz": SHOWER["h"]}
    solids = ([shower_vol] + B.bathtub_parts(TUB) + B.glass_partition_parts(PART)
              + [p for p in B.shower_parts(SHOWER) if p["mat"] == "glass"])
    for t in textiles:
        for s in solids:
            assert not _boxes_overlap_3d(t, s), \
                f"textile {t['name']} enters the wet zone via {s.get('name', 'shower')}"


def test_textiles_clear_the_built_hardware_and_fixtures_in_3d():
    """The massing must be buildable: no towel inside a basin/counter/mirror, robes
    above the tub deck, towels clear of the holder."""
    parts = _acc_parts()
    textiles = [p for p in parts if p["mat"] == "towel"]
    counter_zone = [p for p in B.vanity_parts(VANITY)
                    if p["name"] in ("vanity_basin0", "vanity_basin1", "vanity_mirror",
                                     "vanity_cabinet")]
    for t in textiles:
        for s in counter_zone:
            assert not _boxes_overlap_3d(t, s), f"{t['name']} collides with {s['name']}"


def test_hook_side_assignment_is_pinned_to_the_door_jambs():
    """Review catch 2026-07-21 (verified by actually swapping the sides and running
    the suite green): D-E6-3's decided assignment — SOUTH jamb = hand towel, NORTH
    jamb = robes — had no pin; a silent s/n swap passed all 1834 tests. Bounds derive
    from the DOOR rect, like the build does."""
    parts = {p["name"]: p for p in _acc_parts()}
    door_y0, door_y1 = sorted((DOOR["rect"][1], DOOR["rect"][3]))
    hand = parts["acc_hand_towel_hook0"]
    assert hand["y"] + hand["dy"] <= door_y0, \
        "the hand towel must hang on the SOUTH jamb (beside the basins)"
    for nm, p in parts.items():
        if nm.startswith("acc_robe") and "hook" not in nm:
            assert p["y"] >= door_y1, f"{nm} must hang on the NORTH jamb (tub side)"
    assert parts["acc_robe_hook_s"]["y"] < door_y0 < door_y1 < parts["acc_robe_hook_n"]["y"]


def test_robes_hang_in_air_above_the_tub_deck_never_on_it():
    """D-E6-5 interpretation, recorded: 'no towel over the glass or tub edge' bans
    textiles RESTING/DRAPED ON them (3D contact — the wet/dry law test above); the
    DD's own D-E6-3 sites the robes 'fronting the tub-deck east end', which plan-
    overlaps the deck cap (it reaches within ~5mm of the party wall) for ANY wall-hung
    piece there. The robes therefore must hang with real AIR below them — pinned as a
    >=250mm z-gap over every tub part they plan-overlap (review 2026-07-21)."""
    robes = [p for p in _acc_parts() if p["name"].startswith("acc_robe")
             and "hook" not in p["name"]]
    assert robes, "census promises robes"
    for r in robes:
        for tp in B.bathtub_parts(TUB):
            plan_overlap = (r["x"] < tp["x"] + tp["dx"] and tp["x"] < r["x"] + r["dx"]
                            and r["y"] < tp["y"] + tp["dy"] and tp["y"] < r["y"] + r["dy"])
            if plan_overlap:
                assert r["z"] >= tp["z"] + tp["dz"] + 250, \
                    f"{r['name']} hangs too close over {tp['name']} — reads as ON the tub"


def test_missing_subroom_raises():
    with pytest.raises(ValueError, match="subroom"):
        B.accessory_parts(copy.deepcopy(ACC), None)
    with pytest.raises(ValueError, match="subroom"):
        B.fixture_parts(copy.deepcopy(ACC))     # the dispatch default must not soften it


def test_missing_or_empty_census_raises():
    for bad_design in ({}, {"census": {}}, {"census": None}):
        acc = {"kind": "bath_accessories", "design": bad_design}
        with pytest.raises(ValueError, match="census"):
            B.accessory_parts(acc, SUBROOM)


def test_unknown_census_key_raises():
    acc = copy.deepcopy(ACC)
    acc["design"]["census"]["towel_ring"] = 1    # a ring = schedule change = owner
    with pytest.raises(ValueError, match="unknown census key"):
        _acc_parts(acc)


def test_all_zero_census_raises_never_a_white_box():
    acc = copy.deepcopy(ACC)
    acc["design"]["census"] = {k: 0 for k in CENSUS}
    with pytest.raises(ValueError, match="all-zero"):
        _acc_parts(acc)


def test_bad_census_count_raises():
    for bad in (-1, 1.5, "2", True):
        acc = copy.deepcopy(ACC)
        acc["design"]["census"]["bath_on_bar"] = bad
        with pytest.raises(ValueError, match="non-negative int"):
            _acc_parts(acc)


def test_missing_sibling_fixture_or_door_raises():
    for drop_kind in ("toilet", "shower"):
        sub = {**SUBROOM, "fixtures": [f for f in SUBROOM["fixtures"]
                                       if f.get("kind") != drop_kind]}
        with pytest.raises(ValueError, match="exactly 1"):
            _acc_parts(subroom=sub)
    with pytest.raises(ValueError, match="door"):
        _acc_parts(subroom={**SUBROOM, "openings": []})


def test_door_on_a_y_wall_raises():
    sub = {**SUBROOM, "openings": [{"type": "door", "rect": [1000, 8650, 2000, 8650]}]}
    with pytest.raises(ValueError, match="x-plane"):
        _acc_parts(subroom=sub)


def test_mat_rides_the_fixture_lane_not_the_item_rug_lane():
    """DD build-consequence 8 pin: the ensuite mat CANNOT be a spec item — _add_rug
    forces the bedroom's herringbone PBR and curtains._obstacles special-cases rugs;
    'rug' being UNAPPLIABLE in material_presets pins that the item lane stays closed."""
    import material_presets as mp
    assert "rug" in mp.UNAPPLIABLE_KINDS
    assert any(p["name"] == "acc_bath_mat0" and p["mat"] == "towel"
               for p in _acc_parts())


# ---------------------------------------------------------------- canonical FILE (e6)

CANON = os.path.join(os.path.dirname(__file__),
                     "../../projects/PRJ-2026-002_c001-house/03_layout/"
                     "master-suite.CANONICAL.spec.json")


def _canon():
    with open(CANON, encoding="utf-8") as f:
        return json.load(f)


def _canon_bath(spec):
    return next(s for s in spec["subrooms"] if s.get("type") == "bathroom")


def test_canonical_carries_the_accessories_fixture_with_the_dd_census():
    bath = _canon_bath(_canon())
    acc = [f for f in bath["fixtures"] if f.get("kind") == "bath_accessories"]
    assert len(acc) == 1, "the decided accessory set must exist as spec DATA"
    census = acc[0]["design"]["census"]
    assert census == {"bath_on_bar": 2, "hand_on_south_hook": 1, "hand_on_counter": 1,
                      "robes_on_north_hook": 2, "bath_mat": 1}, \
        "the D-E6-3 census (bath x2, hand x1+x1, robe x2, mat x1)"
    assert "x" not in acc[0] and "w" not in acc[0], \
        "DATA-only entry — a bbox would leak into the mass/obstacle sets"


def test_canonical_accessories_build_nonempty_parts():
    """DD build-consequence 8: accessory-shaped data that routes to zero parts is the
    white-box swallow — the canonical spec must produce the full set."""
    bath = _canon_bath(_canon())
    acc = next(f for f in bath["fixtures"] if f.get("kind") == "bath_accessories")
    parts = B.fixture_parts(acc, subroom=bath)
    assert parts and len([p for p in parts if p["mat"] == "towel"]) == 7
    assert all(p["mat"] in KNOWN_MATS for p in parts)


def test_canonical_both_copies_of_both_ensuite_casements_say_decided_bare():
    """D-E6-2 probe: the BARE note rides on ALL FOUR opening copies (envelope x2 +
    subroom x2) — inert anti-reopen data."""
    spec = _canon()
    envelope = {o["id"]: o for o in spec["room"]["openings"]}
    sub = {o["id"]: o for o in _canon_bath(spec)["openings"]}
    for oid in ("glz-ensuite-win1", "glz-ensuite-win2"):
        for copy_name, ops in (("envelope", envelope), ("subroom", sub)):
            assert "D-E6-2 DECIDED BARE" in ops[oid].get("note", ""), \
                f"{oid} {copy_name} copy lost the BARE ruling"


def test_canonical_no_build_lane_creates_fabric_at_the_ensuite_casements():
    """D-E6-2 probe: the casement_sheers block must NOT name the ensuite casements —
    the sheers lane is the only fabric-at-window lane, and it covers exactly the two
    BEDROOM casements."""
    spec = _canon()
    wins = set(spec["casement_sheers"]["windows"])
    assert wins == {"glz-west-win1", "glz-west-win2"}
    assert not wins & {"glz-ensuite-win1", "glz-ensuite-win2"}


def test_canonical_purist_schedule_file_untouched_by_the_build():
    """D-E6-3 probe: the 18in fallback is spec data — the schedule FILE carries no e6
    edit (its accessory rows are used verbatim). Pin: the file, if present, does not
    mention element 6 or the census."""
    sched = os.path.join(os.path.dirname(CANON),
                         "element4-ensuite_ffe-brass-schedule-PURIST-2026-07-20.md")
    if os.path.exists(sched):
        text = open(sched, encoding="utf-8").read()
        assert "bath_on_bar" not in text and "D-E6" not in text, \
            "the locked schedule FILE must stay byte-untouched by element 6"
