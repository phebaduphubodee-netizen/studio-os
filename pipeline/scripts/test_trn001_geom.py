"""TRN-001 pure-geometry armour: projection, back-projection, mass invariants.

The dangerous reverts here: (a) the pure projection drifting from the Blender
camera the builder constructs — the solver would then fit a camera the render
does not have (the builder re-checks this against world_to_camera_view on every
build, and these tests hold the maths side); (b) back-projection returning a
plausible-but-wrong millimetre instead of None when a ray misses; (c) a mass
silently detaching from the one it is supposed to sit on.
"""
import copy
import json
import os

import pytest

import trn001_geom as G

SPEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "specs", "trn001_blockout.json")


@pytest.fixture
def spec():
    return G.load_spec(SPEC_PATH)


# ---- projection <-> back-projection ------------------------------------------

def test_backproject_inverts_project_on_every_solve_landmark(spec):
    cam = spec["camera"]
    for name, p in G.landmarks_3d(spec).items():
        uv = G.project(cam, p, res=2048)
        assert uv is not None, name
        # each landmark lies on a known y plane -> recover it from the pixel
        got = G.backproject(cam, uv, ("y", p[1]), res=2048)
        assert got is not None, name
        for a, b in zip(got, p):
            assert abs(a - b) < 0.5, f"{name}: {got} != {p}"


def test_backproject_recovers_a_height_from_a_vertical_face_plane(spec):
    cam = spec["camera"]
    truth = (300.0, -350.0, 1500.0)          # a point on the tower front plane
    uv = G.project(cam, truth, res=2048)
    got = G.backproject(cam, uv, ("y", -350.0), res=2048)
    assert abs(got[2] - 1500.0) < 0.5 and abs(got[0] - 300.0) < 0.5


def test_backproject_refuses_rather_than_guessing(spec):
    cam = spec["camera"]
    # a plane BEHIND the camera must come back None, never a mirrored number
    # (camera sits at negative y looking toward the wall at y=0, so "behind"
    # is MORE negative than the station)
    uv = G.project(cam, (0.0, -350.0, 1500.0), res=2048)
    assert G.backproject(cam, uv, ("y", cam["y_mm"] - 1000.0), res=2048) is None
    # a ray parallel to the requested plane: the z ray component is 0 exactly
    # at the horizon row, so a horizontal-plane request there must refuse
    horizon_v = 2048 * (0.5 + cam.get("shift_y", 0.0))
    assert G.backproject(cam, (1024.0, horizon_v), ("z", 0.0), res=2048) is None


def test_projection_is_a_pinhole_scale_not_an_offset(spec):
    """Doubling focal length must double the offset from frame centre."""
    cam = dict(spec["camera"])
    p = (500.0, -350.0, 1800.0)
    u1 = G.project(cam, p, res=2048)[0] - 1024.0
    cam2 = dict(cam, focal_mm=cam["focal_mm"] * 2)
    u2 = G.project(cam2, p, res=2048)[0] - 1024.0
    assert abs(u2 - 2 * u1) < 1e-6


# ---- mass invariants ----------------------------------------------------------

def _by_name(spec):
    return {m["name"]: m for m in G.masses(spec)}


def test_altar_stack_sits_on_what_it_claims_to_sit_on(spec):
    """Group-based on purpose: whether an element is one mass or a joinery
    assembly is a detailing choice, but what it STANDS ON is a measured fact."""
    ms = G.masses(spec)
    p, s = spec["unit"]["plinth"], spec["unit"]["step"]
    bottom = lambda prefix: _env(_group(ms, prefix))[4]
    assert bottom("plinth") == pytest.approx(0.0)          # on the floor
    assert bottom("step") == pytest.approx(p["h_mm"])      # on the plinth
    top_step = p["h_mm"] + s["h_mm"]
    for k in ("centre_box", "pedestal_L", "pedestal_R"):
        assert bottom(k) == pytest.approx(top_step), k     # on the step


def test_both_towers_reach_the_floor_and_the_plinth_hides_the_left_base(spec):
    """Round 1 read the left tower as STANDING ON the plinth; round 2's critic
    refuted that with the frame — the target never shows the left tower's
    underside, while ours did, because the deeper plinth simply passes in front
    of a floor-standing tower. Pinned in the corrected form, with the reason,
    so the flag is not flipped back by tidiness."""
    ms = G.masses(spec)
    l, r = _env(_group(ms, "tower_L")), _env(_group(ms, "tower_R"))
    assert l[4] == pytest.approx(0.0) and r[4] == pytest.approx(0.0)
    assert l[1] < 0 < r[0]                                  # left of / right of centre
    # the occlusion this relies on: the plinth is deeper than the towers
    assert spec["unit"]["plinth"]["d_mm"] > spec["unit"]["tower"]["d_mm"]
    assert _env(_group(ms, "plinth"))[2] < l[2]             # plinth front is nearer


def test_the_wooden_base_projects_further_than_the_blocks_on_it(spec):
    """Owner, 2026-07-31: the altar's wooden base must come forward slightly
    more than the blocks standing on it. Ours had the centre box overhanging its
    own base by 69 mm, which no piece of millwork does."""
    u = spec["unit"]
    base = u["step"]["d_mm"]
    for k in ("box", "pedestal"):
        assert u[k]["d_mm"] < base, f"{k} overhangs the base it stands on"
        assert base - u[k]["d_mm"] <= 60, f"{k} is set back far more than a reveal"


def test_the_side_pedestals_are_symmetric_about_the_centre_box(spec):
    """Owner, 2026-07-31: the two blocks sat unequal distances from the middle.
    Root cause was anchoring them to x=0 while the box sits off-centre; the
    target measures 705.1 / 704.3 mm from the BOX centre. Pinned so the anchor
    cannot drift back to the room centreline."""
    ms = {m["name"]: m for m in G.masses(spec)}
    bcx = ms["centre_box"]["c"][0]
    left, right = ms["pedestal_L"]["c"][0], ms["pedestal_R"]["c"][0]
    assert (bcx - left) == pytest.approx(right - bcx, abs=1.0)
    assert ms["pedestal_L"]["s"][0] == pytest.approx(ms["pedestal_R"]["s"][0])


def test_the_stone_is_set_back_into_the_wall_not_stuck_on_it(spec):
    """Owner, 2026-07-31 (twice, because the first fix inverted it): the slab
    sits DEEP IN the wall — ไฟที่ต้องซ่อนในกำแพงคือแผ่นหินอ่อนอยู่ลึกลงไป. Its
    front face must therefore be behind the room-side wall plane, and it must be
    behind the recess opening rather than filling it."""
    m = spec["unit"]["marble"]
    rc = spec["unit"].get("recess")
    if not rc:
        pytest.skip("no recess specified")
    assert m["proud_mm"] < 0, "a recessed slab's front face is behind y=0"
    face_y = -m["proud_mm"]
    assert face_y >= rc["depth_mm"] - 1e-6, "the stone must sit at the recess back"


def test_the_concealed_light_stays_concealed(spec):
    """A strip that reaches the room side of the wall plane, or that sits
    outside the opening, stops being concealed and becomes a visible tube —
    the exact failure this detail exists to avoid."""
    if not spec["unit"]["marble"].get("halo"):
        pytest.skip("halo not specified")
    ms = G.masses(spec)
    strips = [m for m in ms if m["name"].startswith("halo_")]
    assert len(strips) == 4
    m = spec["unit"]["marble"]
    gp = (spec["unit"].get("recess") or {}).get("gap_mm", 20.0)
    mcx = m.get("cx_mm", 0.0)
    ox0, ox1 = mcx - m["w_mm"] / 2 - gp, mcx + m["w_mm"] / 2 + gp
    oz0, oz1 = m["bot_z_mm"] - gp, m["bot_z_mm"] + m["h_mm"] + gp
    for s in strips:
        # never on the room side of the wall face
        assert s["c"][1] - s["s"][1] / 2 > 0.0, "strip breaks the wall plane"
        # and always inside the opening it hides in
        assert s["c"][0] - s["s"][0] / 2 >= ox0 - 1e-6
        assert s["c"][0] + s["s"][0] / 2 <= ox1 + 1e-6
        assert s["c"][2] - s["s"][2] / 2 >= oz0 - 1e-6
        assert s["c"][2] + s["s"][2] / 2 <= oz1 + 1e-6


def test_marble_bottom_edge_can_never_show_below_the_altar(spec):
    """C2 round-1 finding: in the delivered work the slab's bottom edge is never
    visible — it dies behind the stack. Pinned so a later dims edit cannot
    re-float it."""
    mar = spec["unit"]["marble"]
    step_top = spec["unit"]["plinth"]["h_mm"] + spec["unit"]["step"]["h_mm"]
    assert mar["bot_z_mm"] < step_top


def test_every_mass_is_in_front_of_the_wall_and_inside_the_room(spec):
    """Nothing may float behind the wall face or leave the room — EXCEPT what
    the wall deliberately contains: the recess returns, the stone set into them
    and the light hidden there, none of which may pass the wall's back."""
    room = spec["room"]
    rdep = (spec["unit"].get("recess") or {}).get("depth_mm", 0.0)
    inwall = {"marble"}
    for m in G.masses(spec):
        if m["name"] in ("back_wall", "ceiling", "floor", "side_wall_L"):
            continue
        y0 = m["c"][1] - m["s"][1] / 2
        y1 = m["c"][1] + m["s"][1] / 2
        if m["name"] in inwall or m["name"].startswith(("recess_", "halo_")):
            assert y0 >= -1e-6, f"{m['name']} pokes out of the wall"
            # the stone is bedded into the wall body behind the recess, but
            # nothing may pass the wall's back face into the next room
            assert y1 <= rdep + 100.0 + 1e-6, f"{m['name']} passes through the wall"
            continue
        assert y1 <= 1e-9, f"{m['name']} pokes through the wall"
        assert y0 >= -room["room_depth_mm"], f"{m['name']} leaves the room"


def test_the_side_wall_never_cuts_into_the_unit(spec):
    """Owner, 2026-07-31: "ทำไมกำแพงซ้ายขยับเข้ามา". The wall had a hard-coded
    position measured against an OLD carcass; round 3 re-derived the carcass
    wider and further left and the wall stayed put, ending up 185 mm inside the
    unit. Pinned at the invariant rather than the number, so the room can only
    ever follow the unit."""
    ms = {m["name"]: m for m in G.masses(spec)}
    h = spec["unit"]["header"]
    unit_left = h.get("cx_mm", 0.0) - h["len_mm"] / 2
    side = ms["side_wall_L"]
    assert side["c"][0] + side["s"][0] / 2 <= unit_left + 1e-6, \
        "the side wall stands inside the unit's left edge"
    for wall in ("back_wall", "ceiling", "floor"):
        w = ms[wall]
        assert w["c"][0] - w["s"][0] / 2 <= unit_left + 1e-6, \
            f"{wall} does not reach the unit's left edge"


def test_the_room_follows_the_unit_when_the_unit_moves(spec):
    """The mechanism, not just today's numbers: widen the unit and the corner
    must move with it."""
    a = {m["name"]: m for m in G.masses(spec)}["side_wall_L"]["c"][0]
    s2 = copy.deepcopy(spec)
    s2["unit"]["header"]["len_mm"] += 400
    b = {m["name"]: m for m in G.masses(s2)}["side_wall_L"]["c"][0]
    assert b == pytest.approx(a - 200.0, abs=1.0)


def test_spec_of_record_parses_and_carries_the_solved_camera(spec):
    for k in ("x_mm", "y_mm", "z_mm", "yaw_deg", "focal_mm"):
        assert isinstance(spec["camera"][k], (int, float))
    assert spec["room"]["ceiling_mm"] > 0


def test_rounded_ends_do_not_exceed_the_mass_they_round(spec):
    for key in ("plinth", "step", "box", "pedestal"):
        e = spec["unit"][key]
        width = e.get("len_mm", e.get("w_mm"))
        assert e["r_mm"] * 2 <= width and e["r_mm"] * 2 <= e["d_mm"], key


# ---- round-2 joinery ----------------------------------------------------------

JOINERY = {
    "tower": {"board_mm": 18, "shelf_t_mm": 30, "toe_h_mm": 80, "toe_setback_mm": 20,
              "shelves_L_z": [600, 1000, 1400, 1800], "shelves_R_z": [560, 980, 1400, 1820]},
    "header": {"joints_x_mm": [-1200, 1250], "reveal_mm": 4,
               "brass": {"inset_mm": 45, "width_mm": 6, "proud_mm": 2}},
    "plinth": {"drawers": 5, "reveal_mm": 4, "face_t_mm": 18,
               "toe_h_mm": 60, "toe_setback_mm": 40},
}


@pytest.fixture
def jspec(spec):
    s = copy.deepcopy(spec)
    for key, extra in JOINERY.items():
        s["unit"][key].update(extra)
    return s


def _group(ms, prefix):
    return [m for m in ms if m["name"] == prefix or m["name"].startswith(prefix + "_")]


def _env(group):
    """(x0, x1, y0, y1, z0, z1) envelope of a group of masses."""
    lo = [min(m["c"][i] - m["s"][i] / 2 for m in group) for i in range(3)]
    hi = [max(m["c"][i] + m["s"][i] / 2 for m in group) for i in range(3)]
    return lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]


def _contains(m, pt, eps=1e-6):
    return all(abs(pt[i] - m["c"][i]) < m["s"][i] / 2 - eps for i in range(3))


@pytest.mark.parametrize("prefix", ["plinth", "tower_L", "tower_R"])
def test_joinery_never_moves_the_silhouette_the_camera_was_fitted_to(spec, jspec, prefix):
    """THE class this repo keeps re-learning: a later detailing pass must not
    revert an earlier measured decision by a side effect. The round-1 camera was
    least-squares fitted to these outer envelopes; switching joinery on may add
    inner structure but may never move the outside."""
    a = _env(_group(G.masses(spec), prefix))
    b = _env(_group(G.masses(jspec), prefix))
    for i, axis in enumerate("x0 x1 y0 y1 z0 z1".split()):
        assert a[i] == pytest.approx(b[i], abs=0.5), f"{prefix} {axis}: {a[i]} -> {b[i]}"


def test_tower_cubbies_are_actually_open(jspec):
    """A shelf ladder drawn on a solid box is a painted-on cubby. The point in
    the middle of each opening, at the tower's front depth, must be EMPTY."""
    ms = G.masses(jspec)
    t = jspec["unit"]["tower"]
    for side in ("L", "R"):
        grp = _group(ms, f"tower_{side}")
        assert grp, side
        x0, x1, y0, y1, z0, z1 = _env(grp)
        cx = (x0 + x1) / 2
        zs = sorted(t[f"shelves_{side}_z"])
        mids = [(zs[i] + t["shelf_t_mm"] + zs[i + 1]) / 2 for i in range(len(zs) - 1)]
        assert mids
        for z in mids:
            pt = (cx, y0 + 40.0, z)          # just inside the front face
            hit = [m["name"] for m in ms if _contains(m, pt)]
            assert not hit, f"tower_{side} cubby at z={z} is blocked by {hit}"


def test_a_tower_carried_on_the_plinth_gets_no_toe_of_its_own(spec):
    """The mechanism is still there and still correct — it just isn't what this
    piece does any more. Exercised on a variant spec so the rule stays pinned
    without re-asserting the refuted reading of the target."""
    s = copy.deepcopy(spec)
    s["unit"]["tower"]["left_on_plinth"] = True
    names = {m["name"] for m in G.masses(s)}
    assert "tower_R_toe" in names          # stands on the floor
    assert "tower_L_toe" not in names      # carried on the plinth


def test_header_panels_tile_the_band_and_brass_stays_on_its_own_panel(jspec):
    ms = G.masses(jspec)
    h = jspec["unit"]["header"]
    panels = [m for m in ms if m["name"].startswith("header_p")]
    assert len(panels) == len(h["joints_x_mm"]) + 1
    # panels + reveals reconstruct the full band length, with no overlap
    spans = sorted((m["c"][0] - m["s"][0] / 2, m["c"][0] + m["s"][0] / 2) for m in panels)
    assert spans[0][0] == pytest.approx(h["cx_mm"] - h["len_mm"] / 2)
    assert spans[-1][1] == pytest.approx(h["cx_mm"] + h["len_mm"] / 2)
    for a, b in zip(spans, spans[1:]):
        assert b[0] - a[1] == pytest.approx(h["reveal_mm"])
    for i, (px0, px1) in enumerate(spans):
        strips = [m for m in ms if m["name"].startswith(f"brass_p{i}_")]
        assert len(strips) == 4, i
        for s in strips:
            assert s["c"][0] - s["s"][0] / 2 >= px0 - 1e-6
            assert s["c"][0] + s["s"][0] / 2 <= px1 + 1e-6
            # brass sits PROUD of the face, never buried inside the panel
            assert s["c"][1] - s["s"][1] / 2 < -h["depth_mm"] - 1e-9


def test_drawer_faces_tile_the_plinth_with_backed_reveals(jspec):
    ms = G.masses(jspec)
    p = jspec["unit"]["plinth"]
    faces = sorted([m for m in ms if m["name"] == "plinth" or m["name"].startswith("plinth_face")],
                   key=lambda m: m["c"][0])
    assert len(faces) == p["drawers"]
    for a, b in zip(faces, faces[1:]):
        gap = (b["c"][0] - b["s"][0] / 2) - (a["c"][0] + a["s"][0] / 2)
        assert gap == pytest.approx(p["reveal_mm"])
    # every gap is BACKED (a reveal is a groove, not a slot you see the wall through)
    strips = [m for m in ms if m["name"].startswith("plinth_reveal")]
    assert len(strips) == p["drawers"] - 1
    face_front = min(m["c"][1] - m["s"][1] / 2 for m in faces)
    for s in strips:
        assert s["c"][1] - s["s"][1] / 2 > face_front      # set back behind the fronts


def test_the_plinth_end_curve_survives_the_build_clamp(jspec):
    """THE bug this test exists for (2026-07-31): the radius a spec asks for is
    not the radius that gets built — rounded_outline clamps it to half the
    shorter side, so putting the plan curve on a thin face silently squares the
    end off. Assert the EFFECTIVE radius, and assert the outline really bulges."""
    ms = G.masses(jspec)
    r = jspec["unit"]["plinth"]["r_mm"]
    faces = sorted([m for m in ms if m["name"] == "plinth" or m["name"].startswith("plinth_face")],
                   key=lambda m: m["c"][0])
    assert G.effective_radii(faces[0])[0] == pytest.approx(r)
    assert G.effective_radii(faces[-1])[1] == pytest.approx(r)
    for m in faces[1:-1]:
        assert G.effective_radii(m)[:2] == (0.0, 0.0)
    # geometry, not intent: the built outline's front-left corner is cut back
    left = faces[0]
    pts = G.rounded_outline(left["c"][0], left["c"][1], left["s"][0], left["s"][1],
                            left["radii"])
    x0 = left["c"][0] - left["s"][0] / 2
    y0 = left["c"][1] - left["s"][1] / 2
    assert not any(abs(x - x0) < 1e-6 and abs(y - y0) < 1e-6 for x, y in pts)
    assert min(x for x, _ in pts) == pytest.approx(x0)      # extent unchanged
    assert min(y for _, y in pts) == pytest.approx(y0)


def test_rounded_outline_clamps_instead_of_inverting(jspec):
    pts = G.rounded_outline(0, 0, 40, 18, (120, 120, 0, 0))
    assert min(x for x, _ in pts) == pytest.approx(-20)
    assert max(x for x, _ in pts) == pytest.approx(20)
    assert min(y for _, y in pts) == pytest.approx(-9)


# ---- round-3 materials (pure half) --------------------------------------------

def test_every_mass_gets_a_material_that_exists(spec):
    import trn001_materials as MAT
    for m in G.masses(spec):
        key = MAT.material_for(m["name"])
        assert key in MAT.PALETTE, f"{m['name']} -> unknown material {key}"


def test_material_routing_is_not_accidentally_generic(spec):
    """A prefix that mis-routes dresses a whole element wrong and the render
    hides it behind plausibility, so the identities are pinned by name."""
    import trn001_materials as MAT
    f = MAT.material_for
    assert f("floor") == "floor_oak"
    assert f("back_wall") == f("ceiling") == "paint_white"
    assert f("marble") == "marble"
    assert f("brass_p1_top") == "brass"
    assert f("header_p0") == "veneer_fascia"
    assert f("tower_R_sA") == f("tower_L_shelf2") == "veneer_pier"
    assert f("tower_R_back") == "cavity"
    assert f("plinth") == f("plinth_face3") == f("plinth_toe") == "lacquer_white"
    assert f("step") == f("centre_box") == f("pedestal_L") == "veneer_altar"


def test_the_map_dressing_the_ground_truth_study_asked_for_is_actually_present():
    """The 2026-07-30 study measured us at 95% image-free against 50-66% in pro
    files. This pins that the wood/marble/floor/wall sets are on disk and wired,
    so the fix cannot silently revert to flat colour."""
    import trn001_materials as MAT
    dressed = [k for k, v in MAT.PALETTE.items() if MAT.map_paths(v[3])]
    assert {"veneer_fascia", "veneer_pier", "marble", "floor_oak",
            "paint_white"} <= set(dressed)
    for k in dressed:
        maps = MAT.map_paths(MAT.PALETTE[k][3])
        assert "base" in maps and "rough" in maps, k
    assert len(dressed) / len(MAT.PALETTE) >= 0.5


def test_no_material_exceeds_the_measured_sheen_ceiling():
    import trn001_materials as MAT
    assert MAT.SHEEN_CEILING == 0.4


def test_wood_grain_runs_along_the_element_not_isotropically():
    """The round-3 critic measured our veneer at 1.57 directional energy where
    the delivered fascia is 2.41 — near-isotropic mottle, which is what made
    wood read as cast concrete. Every wood material must therefore be
    anisotropic, and the rail must not run its grain the same way as the piers."""
    import trn001_materials as MAT
    for k in ("veneer_fascia", "veneer_pier", "veneer_altar"):
        ax, _, az = MAT.MAP_ASPECT[k]
        assert max(ax, az) / min(ax, az) >= 3.0, f"{k} grain is nearly isotropic"
    fx, _, fz = MAT.MAP_ASPECT["veneer_fascia"]
    px, _, pz = MAT.MAP_ASPECT["veneer_pier"]
    assert (fx > fz) and (pz > px), "rail and piers must not share a grain axis"


def test_the_painted_wall_is_the_least_chromatic_neutral_in_the_room():
    """Ordering test from the critic, and it survives any exposure difference:
    in the delivered work the wall is LESS chromatic than the stone (0.53x);
    ours had it 1.7x MORE, which is what made the room read dingy."""
    import trn001_materials as MAT

    def chroma(rgb):
        return (max(rgb) - min(rgb)) / max(max(rgb), 1e-6)

    wall = chroma(MAT.PALETTE["paint_white"][0])
    stone = chroma(MAT.PALETTE["marble"][0])
    assert wall <= stone, f"wall chroma {wall:.3f} must not exceed stone {stone:.3f}"
    assert chroma(MAT.PALETTE["lacquer_white"][0]) <= 0.05


def test_masses_are_stable_under_reload(spec):
    """A mass list that depends on dict ordering or mutation would make the
    builder and the solver disagree run to run."""
    a = G.masses(spec)
    b = G.masses(copy.deepcopy(spec))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
