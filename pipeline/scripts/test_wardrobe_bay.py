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


def test_open_flag_builds_open_dressing_not_closed_leaves():
    """THE DRESSING GALLERY (owner redesign 2026-07-22): open:true now BUILDS the
    open dressing composition (brass rails + microcement drawer fronts + open oak
    shelves), routed by token — NOT closed mineral leaves. (The e7-era E7-F2 RAISE
    is retired: the flag is honoured, which is the correct resolution of the swallow.)"""
    sr = _mini_bay()
    sr["fixtures"][0]["open"] = True
    parts = WB.bay_parts(sr)
    roles = {MP.mill_object_role(MP.fixture_part_name(p["mat"], p["name"])) for p in parts}
    assert "brass" in roles and "oak" in roles and "microcement" in roles
    assert not any("door" in p["name"] for p in parts)          # no closed leaves
    assert any("rail" in p["name"] for p in parts)              # real hang rails


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
    move to the other face — if it didn't, a facing flip would survive green. (Checks the
    extremum of the closed anchor's leaves, robust to whatever the front geometry is.)"""
    sr = _mini_bay()                                             # mass hugs NORTH -> fronts SOUTH
    door_s = [p for p in WB.bay_parts(sr) if "door" in p["name"]]
    assert min(p["y"] for p in door_s) == pytest.approx(2400.0, abs=0.3)   # front face at low y
    sr2 = _mini_bay()
    sr2["fixtures"][0]["y"] = 0                                   # same mass on the SOUTH edge
    door_n = [p for p in WB.bay_parts(sr2) if "door" in p["name"]]
    assert max(p["y"] + p["dy"] for p in door_n) == pytest.approx(600.0, abs=0.3)  # front at high y


# ------------------------------------------------------------ part vocabulary + mats
def test_dressing_gallery_material_mix_every_part_to_a_suite_material():
    """THE DRESSING GALLERY: the bay is now an OPEN oak-and-brass dressing room + one
    cool closed anchor. Every part must route to a KNOWN suite material (no silent
    default), and the mix must actually be present: oak + brass + microcement + the
    mirror jewel — never all-grey again."""
    parts = WB.bay_parts(_bay())
    assert parts, "canonical bay must emit parts"
    roles = [MP.mill_object_role(MP.fixture_part_name(p["mat"], p["name"])) for p in parts]
    rs = set(roles)
    assert rs <= {"oak", "brass", "microcement", "mirror"}, f"foreign material: {rs}"
    assert {"oak", "brass", "microcement", "mirror"} <= rs, f"mix incomplete: {rs}"
    assert roles.count("oak") > roles.count("microcement")     # warm oak is the body now


def test_open_masses_carry_the_dressing_composition():
    """The two open masses show real dressing content: brass hang rails, floating
    microcement drawer fronts, open oak shelves, a corner niche."""
    parts = WB.bay_parts(_bay())
    joined = " ".join(p["name"] for p in parts)
    for token in ("rail", "shelf", "drawer_front", "towerback", "niche"):
        assert token in joined, f"open dressing token missing: {token}"


def _role_of(p):
    return MP.mill_object_role(MP.fixture_part_name(p["mat"], p["name"]))


def test_open_part_tokens_route_to_the_right_material_per_token():
    """WB-1: pin the per-TOKEN routing on the OPEN masses (the closed BF09-2 anchor is
    uniformly microcement, pinned elsewhere) — a rail that slipped to oak, or a drawer
    front that slipped off microcement, would pass the set-level mix test but is caught
    here."""
    for p in WB.bay_parts(_bay()):
        n = p["name"]
        if n.startswith("bayBF09-2"):                          # the closed anchor: all mineral
            assert _role_of(p) == "microcement", f"anchor part not microcement: {n}"
            continue
        if "rail" in n:
            assert _role_of(p) == "brass", f"rail not brass: {n}"
        elif "drawer_front" in n or "towerback" in n:
            assert _role_of(p) == "microcement", f"front/towerback not microcement: {n}"
        elif "mirror" in n:
            assert _role_of(p) == "mirror", f"mirror token not mirror: {n}"
        elif any(t in n for t in ("shelf", "gable", "plinth", "top", "back", "carcass",
                                  "filler")):
            assert _role_of(p) == "oak", f"oak-carcass token not oak: {n}"


def test_open_mass_filler_is_oak_closed_anchor_leaves_are_mineral():
    """WB-TQ-1: the slab material follows the mass — an OPEN mass's scribe/blind slabs
    are OAK (warm carcass), a CLOSED anchor's leaves are cool MICROCEMENT."""
    parts = WB.bay_parts(_bay())
    for p in parts:
        if "filler" in p["name"] or "carcass_blind" in p["name"]:
            assert _role_of(p) == "oak", f"open-mass slab not oak: {p['name']}"
        if "door" in p["name"]:                                # only the closed anchor has doors
            assert _role_of(p) == "microcement", f"anchor leaf not microcement: {p['name']}"


def test_closed_anchor_is_flat_mineral_with_a_counter_reveal():
    """BF09-2 stays the ONE cool closed anchor: flat microcement leaves (NO fluting —
    the owner rejected it, so no _rd/_bk reed tokens survive) split by the horizontal
    counter-datum reveal into lower + upper."""
    parts = WB.bay_parts(_bay())
    assert not any("_rd" in p["name"] or "_bk" in p["name"] for p in parts)  # fluting gone
    anchor = [p for p in parts if "door" in p["name"]]         # only the closed anchor has doors
    assert anchor, "the closed anchor must render leaves"
    assert all(p["mat"] == "mineral" for p in anchor)
    assert any("_lo" in p["name"] for p in anchor) and any("_hi" in p["name"] for p in anchor)


def test_out_of_range_counter_reveal_fails_loud():
    """E7-REV-1: a mistyped counter_reveal_mm must RAISE, never silently no-split back
    to a blank locker (the revert-by-omission the module exists to prevent)."""
    bay = _bay()
    for bad in (72, 7200, 40, 0):
        broken = copy.deepcopy(bay)
        anchor = next(f for f in broken["fixtures"] if not f.get("open"))
        anchor["design"]["counter_reveal_mm"] = bad
        with pytest.raises(ValueError, match="counter_reveal"):
            WB.bay_parts(broken)


def test_interior_filler_between_run_segments_fails_loud():
    """E7-COALESCE-2: the open composition spans [fronted_lo, fronted_hi]; a sub-MIN_BAY
    station creating an INTERIOR filler between run segments would be overlapped — RAISE."""
    sr = _mini_bay()                                           # run x100..2100
    sr["fixtures"][0]["open"] = True
    # two stations 100mm apart make a 100mm interior filler between two run segments
    sr["fixtures"][0]["design"]["divider_stations_mm"] = [1000, 1100]
    with pytest.raises(ValueError, match="INSIDE the fronted run"):
        WB.bay_parts(sr)


def test_mirror_niche_is_the_focal_jewel_at_the_north_terminal_niche():
    """niche_mirror -> exactly one mirror part at the TERMINAL niche (north end of the
    east hero leg, before the blind corner y7995.8) — MG-2: pin the position, not just
    existence. Removing the mirror emission must RAISE, not silently drop the jewel."""
    parts = WB.bay_parts(_bay())
    mir = [p for p in parts if MP.mill_object_role(MP.fixture_part_name(p["mat"], p["name"])) == "mirror"]
    assert len(mir) == 1 and mir[0]["dz"] > 2000            # full-height niche-back mirror
    m = mir[0]
    # the east hero leg spans y4621.9..7995.8 fronted; the terminal niche is at its NORTH
    # end, so the mirror sits in the top third and clears the blind corner
    assert 7000.0 < m["y"] and m["y"] + m["dy"] <= 7995.9, f"mirror not at the terminal niche: {m}"
    assert m["x"] + m["dx"] <= 5654.1                       # inside the east leg, near its back
    # a niche_mirror mass that yields no mirror part must fail (swap-and-demand-red)
    import types
    real = WB.millwork.millwork_parts

    def strip_mirror(*a, **kw):
        return [p for p in real(*a, **kw) if "mirror" not in p[0]]
    WB.millwork.millwork_parts = strip_mirror
    try:
        with pytest.raises(ValueError, match="mirror"):
            WB.bay_parts(_bay())
    finally:
        WB.millwork.millwork_parts = real


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


def test_open_composition_follows_the_boundary_station():
    """Derivation, not entrenchment: the fronted OPEN composition begins at the drawn
    boundary station (after the 73 scribe filler) — move that station and the whole
    composition shifts with it (never a hardcoded x)."""
    bay = _bay()                                                # north leg open, filler @3327.4
    north = [p for p in WB.bay_parts(bay)
             if p["name"].startswith("bayBF09-1-0") and "filler" not in p["name"]]
    start = min(p["x"] for p in north)
    assert abs(start - 3327.4) < 1.0                            # composition starts at the station
    moved = copy.deepcopy(bay)
    moved["fixtures"][0]["design"]["divider_stations_mm"] = [3427.4, 4428.8]
    north2 = [p for p in WB.bay_parts(moved)
              if p["name"].startswith("bayBF09-1-0") and "filler" not in p["name"]]
    assert abs(min(p["x"] for p in north2) - 3427.4) < 1.0      # it followed the moved station


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


def test_canonical_dressing_gallery_open_closed_split():
    """THE DRESSING GALLERY: the flush note stays deleted; exactly the two BF09-1
    masses carry open:true, the east one carries niche_mirror, and BF09-2 stays the
    ONE closed cool anchor (with the counter-datum reveal)."""
    raw = open(CANON, encoding="utf-8").read()
    assert "flush to ensuite east wall" not in raw
    fixtures = _bay()["fixtures"]
    opened = [f for f in fixtures if f.get("open")]
    closed = [f for f in fixtures if not f.get("open")]
    assert len(opened) == 2 and all(f["bf"] == "BF09-1" for f in opened)
    assert len(closed) == 1 and closed[0]["bf"] == "BF09-2"
    assert sum(1 for f in fixtures if f.get("niche_mirror")) == 1     # one focal jewel
    assert closed[0]["design"].get("counter_reveal_mm")              # the composed calm face


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
    for frag in ("wardrobe bay", "OPEN oak-and-brass", "HANGING GARMENTS",
                 "MIRROR-BACKED", "deliberately BARE", "oak floor CONTINUING", "mouth stub"):
        assert frag in story, f"armour clause missing from material_story: {frag}"
    assert "wood-grain" not in story or "NOT wood-grain" in story    # the anchor may say NOT
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
    """The open/closed counts DERIVE from spec data: 2 open masses + 1 closed anchor."""
    spec = _canon()
    story = " ".join(MP.wardrobe_bay_story_bits(spec))
    assert "2 open composed mass(es)" in story
    assert "1 calm cool CLOSED anchor(s)" in story
    # drop the closed anchor -> the closed-anchor clause disappears (derivation, not copy)
    fewer = copy.deepcopy(spec)
    _bay(fewer)["fixtures"] = [f for f in _bay(fewer)["fixtures"] if f.get("open")]
    story2 = " ".join(MP.wardrobe_bay_story_bits(fewer))
    assert "2 open composed mass(es)" in story2 and "CLOSED anchor" not in story2


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
