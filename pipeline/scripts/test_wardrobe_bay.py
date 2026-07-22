"""Unit tests for wardrobe_bay.py (ELEMENT 7) + the canonical-spec pins + the wiring
pins — the dd-decisions manifest's probes, walked as tests
(element7-wardrobe-bay_dd-decisions.json).
Run: python -m pytest test_wardrobe_bay.py -q
"""
import copy
import json
import os
import re

import pytest

import bathroom
import material_presets as MP
import millwork
import wardrobe_bay as WB

HERE = os.path.dirname(__file__)
CANON = os.path.join(HERE, "../../projects/PRJ-2026-002_c001-house/03_layout/"
                           "master-suite.CANONICAL.spec.json")


def _canon():
    with open(CANON, encoding="utf-8") as f:
        return json.load(f)


def _bay(spec=None):
    spec = spec or _canon()
    return next(s for s in spec["subrooms"] if s.get("type") == "wardrobe")


def _mini_bay(**over):
    """A minimal synthetic wardrobe subroom: one north-wall mass fronting south."""
    sr = {
        "name": "bay", "type": "wardrobe",
        "outline_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]],
        "ceiling_mm": 2800,
        "openings": [{"id": "zone-open-south", "type": "opening",
                      "rect": [0, 0, 3000, 0], "sill_mm": 0, "head_mm": 2800}],
        "fixtures": [{"name": "w1", "kind": "wardrobe", "bf": "T1",
                      "x": 100, "y": 2400, "w": 2000, "d": 600, "h": 2800,
                      "design": {"divider_stations_mm": [1100]}}],
    }
    sr.update(over)
    return sr


# ---------------------------------------------------------------- RAISE contract
def test_raises_on_non_wardrobe_subroom():
    with pytest.raises(ValueError, match="type='wardrobe'"):
        WB.bay_parts({"type": "bathroom"})


def test_raises_without_zone_open_south():
    sr = _mini_bay()
    sr["openings"] = [o for o in sr["openings"] if o["id"] != "zone-open-south"]
    with pytest.raises(ValueError, match="zone-open-south"):
        WB.bay_parts(sr)


def test_raises_on_foreign_kind():
    sr = _mini_bay()
    sr["fixtures"].append({"name": "x", "kind": "bathtub",
                           "x": 0, "y": 0, "w": 500, "d": 400, "h": 500})
    with pytest.raises(ValueError, match="not owned"):
        WB.bay_parts(sr)


def test_raises_on_empty_fixtures():
    with pytest.raises(ValueError, match="no fixtures"):
        WB.bay_parts(_mini_bay(fixtures=[]))


def test_raises_on_absent_stations():
    sr = _mini_bay()
    del sr["fixtures"][0]["design"]["divider_stations_mm"]
    with pytest.raises(ValueError, match="ABSENT"):
        WB.bay_parts(sr)


def test_raises_on_station_outside_run():
    sr = _mini_bay()
    sr["fixtures"][0]["design"]["divider_stations_mm"] = [2500]  # run x100..2100
    with pytest.raises(ValueError, match="outside its run"):
        WB.bay_parts(sr)


def test_raises_on_unsorted_stations():
    sr = _mini_bay()
    sr["fixtures"][0]["design"]["divider_stations_mm"] = [1500, 700]
    with pytest.raises(ValueError, match="ascending"):
        WB.bay_parts(sr)


def test_raises_on_unknown_design_key():
    sr = _mini_bay()
    sr["fixtures"][0]["design"]["divider_stationz_mm"] = [1100]  # typo'd key
    del sr["fixtures"][0]["design"]["divider_stations_mm"]
    with pytest.raises(ValueError, match="unknown design key"):
        WB.bay_parts(sr)


def test_raises_on_front_stop_outside_run():
    sr = _mini_bay()
    sr["fixtures"][0]["design"]["front_stop_mm"] = 5000
    with pytest.raises(ValueError, match="front_stop"):
        WB.bay_parts(sr)


def test_raises_on_square_mass():
    sr = _mini_bay()
    sr["fixtures"][0].update(w=600, d=600, design={"divider_stations_mm": []})
    with pytest.raises(ValueError, match="square"):
        WB.bay_parts(sr)


def test_raises_below_tall_h_never_worktop_parts():
    """Review catch E7-CODE-1: below millwork.TALL_H the tall run silently falls
    through to the LOW worktop branch (non-empty -> the zero-parts RAISE never
    fires) — a decided closed wardrobe must never render as a desk."""
    sr = _mini_bay()
    sr["fixtures"][0]["h"] = 1500
    with pytest.raises(ValueError, match="TALL_H"):
        WB.bay_parts(sr)


def test_raises_on_open_flag_never_silently_closed():
    """Review catch E7-F2: a fixture-level open:true is a design decision this
    module does not own — swallowing it would render a decided-open mass CLOSED."""
    sr = _mini_bay()
    sr["fixtures"][0]["open"] = True
    with pytest.raises(ValueError, match="open"):
        WB.bay_parts(sr)


def test_raises_on_equal_gap_tie():
    """Review catch E7-CODE-2: a depth-axis gap tie is as ambiguous as a square
    bbox — RAISE, never guess a front."""
    sr = _mini_bay()
    sr["fixtures"][0].update(y=1200, d=600)                     # 1200 gap both sides
    with pytest.raises(ValueError, match="tie"):
        WB.bay_parts(sr)


# ------------------------------------------------------- facing DERIVED, not declared
def test_front_faces_derive_toward_the_free_floor():
    sr_bbox = (0.0, 0.0, 3000.0, 3000.0)
    north_mass = {"name": "n", "x": 100, "y": 2400, "w": 2000, "d": 600}
    axis, sign = WB.front_axis_sign(north_mass, sr_bbox)
    assert (axis, sign) == ("y", -1)              # hugs the north edge -> fronts SOUTH
    south_mass = dict(north_mass, y=0)
    assert WB.front_axis_sign(south_mass, sr_bbox) == ("y", 1)   # flipped -> fronts NORTH
    east_mass = {"name": "e", "x": 2400, "y": 100, "w": 600, "d": 2000}
    assert WB.front_axis_sign(east_mass, sr_bbox) == ("x", -1)   # fronts WEST


def test_swap_and_demand_red_leaves_move_with_the_derived_face():
    """The e6 hook-swap lesson: flip the mass to the other edge and the LEAF FRONT must
    move to the other face — if it didn't, a facing flip would survive green. (Robust to
    the 2026-07-22 fluting: the reeds define the front plane, so check the extremum.)"""
    sr = _mini_bay()                                             # mass hugs NORTH -> fronts SOUTH
    door_s = [p for p in WB.bay_parts(sr) if "door" in p["name"]]
    assert min(p["y"] for p in door_s) == pytest.approx(2400.0, abs=0.3)   # front face at low y
    sr2 = _mini_bay()
    sr2["fixtures"][0]["y"] = 0                                   # same mass on the SOUTH edge
    door_n = [p for p in WB.bay_parts(sr2) if "door" in p["name"]]
    assert max(p["y"] + p["dy"] for p in door_n) == pytest.approx(600.0, abs=0.3)  # front at high y


# ------------------------------------------------------------ part vocabulary + mats
def test_closed_module_vocabulary_and_mineral_only():
    parts = WB.bay_parts(_bay())
    assert parts, "canonical bay must emit parts"
    for p in parts:
        assert p["mat"] == "mineral"
        token = re.sub(r"^bay[^_]*_", "", p["name"])
        assert re.match(r"^(carcass|plinth|door\d+|filler\d*|carcass_blind\d*)", token), \
            f"foreign part token in the closed vocabulary: {p['name']}"
    # D-E7-5: internals are joinery-tier — no open-dressing tokens may ever appear
    joined = " ".join(p["name"] for p in parts)
    for banned in ("rail", "shelf", "drawer", "towerback", "gable", "niche"):
        assert banned not in joined


def test_every_part_routes_microcement_never_oak_or_brass():
    for p in WB.bay_parts(_bay()):
        obj = MP.fixture_part_name(p["mat"], p["name"])
        assert MP.mill_object_role(obj) == "microcement"


def test_fronts_are_fluted_reeds_proud_of_a_backer():
    """Owner refinement 2026-07-22: every door leaf is a recessed BACKER + vertical REED
    battens (the flat leaf is gone) — so the fronts read as fluted joinery, not a blank
    slab. Reeds outnumber backers (>= 3 per leaf) and each reed is thinner in the depth
    axis than nothing survives as a full flat leaf."""
    parts = WB.bay_parts(_bay())
    backs = [p for p in parts if "_bk" in p["name"]]
    reeds = [p for p in parts if "_rd" in p["name"]]
    assert backs and reeds
    assert len(reeds) >= 3 * len(backs)                # >= 3 reeds per leaf
    # a reed is proud of its backer in the depth axis (thinner footprint, casts a groove)
    for p in reeds:
        assert min(p["dx"], p["dy"]) <= WB.REED_PROUD_M / WB.MM + 0.1
    # no flat full-thickness (20mm) leaf remains
    assert not any("door" in p["name"] and "_bk" not in p["name"] and "_rd" not in p["name"]
                   for p in parts)


def test_parts_stay_inside_their_fixture_bboxes():
    bay = _bay()
    boxes = [(f["x"], f["y"], f["x"] + f["w"], f["y"] + f["d"], f["h"])
             for f in bay["fixtures"]]
    for p in WB.bay_parts(bay):
        inside = any(x0 - 0.1 <= p["x"] and p["x"] + p["dx"] <= x1 + 0.1 and
                     y0 - 0.1 <= p["y"] and p["y"] + p["dy"] <= y1 + 0.1 and
                     p["z"] + p["dz"] <= h + 0.1
                     for (x0, y0, x1, y1, h) in boxes)
        assert inside, f"part escapes every fixture bbox: {p}"


def test_scribe_filler_rule_is_the_declared_constant_not_73():
    """A segment under MIN_BAY_MM is a leafless filler — the canonical 73.0 sliver
    AND any other sub-threshold segment; the threshold is the declared constant."""
    parts = WB.bay_parts(_bay())
    fillers = [p for p in parts if "filler" in p["name"]]
    assert len(fillers) == 1 and abs(fillers[0]["dx"] - 73.0) < 0.1
    sr = _mini_bay()
    sr["fixtures"][0]["design"]["divider_stations_mm"] = [100 + WB.MIN_BAY_MM - 10]
    got = WB.bay_parts(sr)
    assert any("filler" in p["name"] for p in got)


def test_blind_corner_has_carcass_but_no_front():
    """The east leg's drawn front-stop (y7995.8): beyond it the L-corner is BLIND —
    carcass only, zero door parts (the recorded absence, D-E7-4)."""
    parts = WB.bay_parts(_bay())
    blind = [p for p in parts if "carcass_blind" in p["name"]]
    assert len(blind) == 1
    b = blind[0]
    assert abs(b["y"] - 7995.8) < 0.1 and abs((b["y"] + b["dy"]) - 8595.7) < 0.1
    for p in parts:
        # the front-stop lives on the EAST LEG's run axis (y); north-leg leaves sit
        # legitimately at y7995.8 on their own southern front plane
        if "door" in p["name"] and p["name"].startswith("bayBF09-1-1"):
            assert p["y"] + p["dy"] <= 7995.9, f"a leaf crossed the front-stop: {p}"


def test_leaf_reveals_land_on_the_drawn_stations_and_follow_them():
    """Derivation, not entrenchment: leaves derive from the spec stations — moving a
    station in a COPY moves the leaves; the canonical file's stations are the ink."""
    bay = _bay()
    parts = WB.bay_parts(bay)
    # each leaf's BACKER spans the full leaf run; its x = the leaf's left edge (robust to
    # the fluting — one backer per leaf, vs many reeds)
    door_lo_x = sorted(p["x"] for p in parts if "_bk" in p["name"])
    # north leg: first leaf starts one REVEAL east of the first drawn station (3327.4+3)
    assert any(abs(x - 3330.4) < 0.5 for x in door_lo_x)
    moved = copy.deepcopy(bay)
    moved["fixtures"][0]["design"]["divider_stations_mm"] = [3427.4, 4428.8]
    moved_lo = sorted(p["x"] for p in WB.bay_parts(moved) if "_bk" in p["name"])
    assert any(abs(x - 3430.4) < 0.5 for x in moved_lo)
    assert door_lo_x != moved_lo


def test_millwork_is_the_derivation_source(monkeypatch):
    """D-E7-3 probe: leaf geometry derives from millwork.millwork_parts — the module
    CALLS it (no re-implementation)."""
    calls = []
    real = millwork.millwork_parts

    def spy(*a, **kw):
        calls.append(a)
        return real(*a, **kw)

    monkeypatch.setattr(WB.millwork, "millwork_parts", spy)
    WB.bay_parts(_bay())
    assert calls and all(a[0] == "wardrobe" for a in calls)


def test_zero_millwork_parts_raises_never_white_slab(monkeypatch):
    monkeypatch.setattr(WB.millwork, "millwork_parts", lambda *a, **kw: [])
    with pytest.raises(ValueError, match="zero millwork parts"):
        WB.bay_parts(_bay())


# ------------------------------------------------------------- canonical-file pins
def test_canonical_bay_identity_and_junction_pins():
    """D-E7-1: the adopted ink as spec data + the junction pins whose operands BOTH
    come from spec data (ink_faces) — moving any one datum alone goes red."""
    bay = _bay()
    fx = {("BF09-1" if f["bf"] == "BF09-1" else "BF09-2",
           round(f["y"], 1)): f for f in bay["fixtures"]}
    assert len(bay["fixtures"]) == 3
    assert all(f["kind"] == "wardrobe" for f in bay["fixtures"])
    ink = bay["ink_faces"]
    nl = next(f for f in bay["fixtures"] if f["bf"] == "BF09-1" and f["d"] < 1000)
    el = next(f for f in bay["fixtures"] if f["bf"] == "BF09-1" and f["d"] > 1000)
    b2 = next(f for f in bay["fixtures"] if f["bf"] == "BF09-2")
    assert abs((nl["x"] + nl["w"]) - el["x"]) < 0.05            # butt line x5054.1
    assert abs((el["y"] + el["d"]) - ink["north_interior_y"]) < 0.05
    assert abs((nl["y"] + nl["d"]) - ink["north_interior_y"]) < 0.05
    assert abs(b2["x"] - (ink["west_party_bay_face_x"] + ink["slide_lane_clear_mm"])) < 0.05
    assert nl["x"] == ink["west_party_bay_face_x"]              # north leg starts on the face
    # review catch E7R-2: the x-pin alone left BF09-2's y-extent (the mouth line)
    # and the east leg's back unpinned — 'moving either datum alone goes red' now
    # holds for the full slide geometry: BF09-2's north end IS the baycut's south
    # edge (both spec data), and the east leg's back sits on the recorded east face.
    cut = next(o for o in bay["openings"] if o["id"] == "door-ensuite-baycut")
    assert abs((b2["y"] + b2["d"]) - min(cut["rect"][1], cut["rect"][3])) < 0.5
    assert abs((el["x"] + el["w"]) - ink["east_party_face_x"]) < 0.05
    # BF09-2 builds the DRAWN depth; the label conflict is flagged
    assert b2["w"] == 501.5 and "label_conflict" in b2["design"]
    # the 4mm overshoot is disclosed, not silently 'fixed'
    assert el["x"] + el["w"] > 5650.0 and "4.0" in el["note"]


def test_canonical_flush_note_deleted_and_open_flag_absent():
    raw = open(CANON, encoding="utf-8").read()
    assert "flush to ensuite east wall" not in raw
    assert all("open" not in f or not f.get("open") for f in _bay()["fixtures"])


def test_canonical_zone_open_south_record():
    bay = _bay()
    z = next(o for o in bay["openings"] if o["id"] == "zone-open-south")
    assert z["type"] == "opening" and z["sill_mm"] == 0
    assert z["head_mm"] == bay.get("ceiling_mm", 2800)          # head==ceiling -> no lintel
    x0, y0, x1, y1 = z["rect"]
    ox = [p[0] for p in bay["outline_mm"]]
    oy = [p[1] for p in bay["outline_mm"]]
    assert y0 == y1 == min(oy) and min(x0, x1) == min(ox) and max(x0, x1) == max(ox)
    assert "2298.0" in z["note"]                                # the clear-span disclosure


def test_canonical_baycut_narrowed_and_ensuite_side_untouched():
    """D-E7-9 merge ruling: bay side = the 898 clear passage; ensuite side = e4's
    full rough opening, byte-identical rect."""
    spec = _canon()
    bay = _bay(spec)
    cut = next(o for o in bay["openings"] if o["id"] == "door-ensuite-baycut")
    assert cut["rect"] == [3150, 6698, 3150, 7596]
    ens = next(s for s in spec["subrooms"] if s.get("type") == "bathroom")
    door = next(o for o in ens["openings"] if o["id"] == "door-ensuite")
    assert door["rect"] == [3150, 6596, 3150, 7596]
    slide = bay["door_ensuite_slide"]
    assert slide["mechanism"] == "surface_slide_south"
    assert slide["owner_confirm"] == "OPEN"                     # silent closure fails here


def test_canonical_cameras_and_lighting_amendment():
    spec = _canon()
    cams = spec["eye_camera_variants"]
    for name in ("wardrobe_bay_entry", "wardrobe_bay_dressing", "wardrobe_bay_doorlane"):
        assert cams[name]["in_subroom"] == "wardrobe"
    assert "OUTSIDE" in cams["wardrobe_bay_entry"]["note"]      # the disclosed stretch
    for name in ("wardrobe_bay_entry", "wardrobe_bay_doorlane"):
        assert "BF09-2" in cams[name]["note"]                   # the 8th-omission pin
    amb = spec["lighting"]["ambient"]["note"]
    assert "NO camera sees" not in amb.replace("'RCP-tier placeholder NO camera sees", "")
    assert "AMENDED BY ELEMENT 7" in amb
    assert "fixtures" not in spec["lighting"]                   # S9 stays closed


def test_e5_bay_row_re_derives_from_the_trued_masses():
    """D-E7-6: the clip set reads the subroom fixtures, so the trued rects flow
    through — the dropped can lands inside BF09-1 and the disclosure fires."""
    import element5_lighting as e5
    spec = _canon()
    fixtures, metas = e5.ambient_plan(spec, spec["lighting"])
    bay_meta = next(m for m in metas if "wardrobe" in str(m.get("zone", "")))
    assert bay_meta["n_grid"] == 3 and bay_meta["n"] == 2
    assert bay_meta["dropped_in_masses"][0]["mass"] == "BF09-1"
    kept = [(f["x"], f["y"]) for f in fixtures
            if "wardrobe" in str(f.get("zone", ""))]
    assert (4400.0, 7250.0) in kept and (4400.0, 6316.7) in kept


# ------------------------------------------------------------------- wiring pins
def test_build_room_routes_by_subroom_type_source_text():
    """D-E7-3 merge ruling: build_room is bpy-layer (unimportable here), so the
    routing branch is pinned as SOURCE TEXT — and pinned in ORDER (review catch
    E7-F3: existence alone lets the branch drift BELOW the bathroom dispatch,
    where bay fixtures would first white-slab through the silent [] fallback):
    predicate < bay_parts call < its continue < the bathroom dispatch."""
    src = open(os.path.join(HERE, "build_room.py"), encoding="utf-8").read()
    assert "import wardrobe_bay" in src
    loop = src[src.index("for si, sr in enumerate"):]
    i_pred = loop.index('sr.get("type") == "wardrobe"')
    i_bay = loop.index("wardrobe_bay.bay_parts(sr)")
    i_bath = loop.index("bathroom.fixture_parts")
    assert i_pred < i_bay < i_bath
    assert i_bay < loop.index("continue", i_bay) < i_bath      # the early-exit is real


def test_bathroom_lane_untouched_scope_pin():
    """The bathroom lane never owns wardrobes (routing happens by TYPE). Review
    catch E7-F3/E7R-3: the first version's second assert ended in `or True` — a
    tautology that could not catch the bathroom lane growing a wardrobe branch."""
    assert "wardrobe" not in bathroom.DISPATCH                  # no dispatch widening
    assert bathroom.fixture_parts({"kind": "wardrobe", "name": "x",
                                   "x": 0, "y": 0, "w": 600, "d": 600, "h": 2800}) == []


def test_fixture_mat_object_mineral_row_and_closed_vocab():
    assert MP.FIXTURE_MAT_OBJECT["mineral"] == "mill__{b}__cool"
    with pytest.raises(ValueError, match="unknown mat role"):
        MP.fixture_part_name("granite", "x")


# ------------------------------------------------------------------- story armour
def test_story_bits_ride_in_material_story_and_gate_on_the_bay():
    spec = _canon()
    story = MP.material_story(None, spec)
    for frag in ("wardrobe bay", "NEVER wood-grain", "OPEN to the bedroom",
                 "deliberately BARE", "oak floor CONTINUING", "mouth stub"):
        assert frag in story, f"armour clause missing from material_story: {frag}"
    bare = copy.deepcopy(spec)
    bare["subrooms"] = [s for s in bare["subrooms"] if s.get("type") != "wardrobe"]
    assert "wardrobe bay" not in MP.material_story(None, bare)


def test_story_bits_cross_block_pin_raises_without_zone_open():
    spec = _canon()
    bay = _bay(spec)
    bay["openings"] = [o for o in bay["openings"] if o["id"] != "zone-open-south"]
    with pytest.raises(ValueError, match="zone-open-south"):
        MP.wardrobe_bay_story_bits(spec)


def test_story_passage_width_derives_from_the_baycut_rect():
    spec = _canon()
    assert any("~898" in b for b in MP.wardrobe_bay_story_bits(spec))
    moved = copy.deepcopy(spec)
    cut = next(o for o in _bay(moved)["openings"] if o["id"] == "door-ensuite-baycut")
    cut["rect"] = [3150, 6798, 3150, 7596]
    assert any("~798" in b for b in MP.wardrobe_bay_story_bits(moved))


def test_story_mass_count_derives_from_the_fixtures():
    spec = _canon()
    assert any("(3 closed built-in mass(es))" in b
               for b in MP.wardrobe_bay_story_bits(spec))
    fewer = copy.deepcopy(spec)
    _bay(fewer)["fixtures"].pop()
    assert any("(2 closed built-in mass(es))" in b
               for b in MP.wardrobe_bay_story_bits(fewer))


def test_bay_floor_is_bare_and_a_floor_intruder_raises():
    """D-E7-10 probe 1 (review catch E7-F1): nothing intrudes on the bay clear
    floor TODAY, and the bare-floor armour DERIVES from the scan — dropping an
    item into the bay makes both the scan and the story bit go red, so the polish
    armour can never silently order a decided item erased (the prose-copy shape)."""
    spec = _canon()
    assert WB.bay_floor_intruders(spec) == []
    story = MP.material_story(None, spec)
    assert "deliberately BARE" in story
    intruded = copy.deepcopy(spec)
    intruded.setdefault("items", []).append(
        {"name": "rogue valet", "kind": "stool", "x": 4000, "y": 7000,
         "w": 400, "d": 400, "h": 900})
    assert WB.bay_floor_intruders(intruded) == ["rogue valet"]
    with pytest.raises(ValueError, match="no longer BARE"):
        MP.wardrobe_bay_story_bits(intruded)
