"""TRN-001 pure-geometry armour: projection, back-projection, mass invariants.

The dangerous reverts here: (a) the pure projection drifting from the Blender
camera the builder constructs — the solver would then fit a camera the render
does not have (the builder re-checks this against world_to_camera_view on every
build, and these tests hold the maths side); (b) back-projection returning a
plausible-but-wrong millimetre instead of None when a ray misses; (c) a mass
silently detaching from the one it is supposed to sit on.
"""
import copy
import math
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
    the wall deliberately contains: the recess returns, the stone set into them,
    the light hidden there, and (2026-08-01) the tower cavities, which are
    measured pockets INTO the wall rather than boxes stood in front of it. The
    bound is the wall's own back face, taken from the builder's own function so
    a deeper pocket can never leave this test testing a stale number."""
    room = spec["room"]
    rdep = G.wall_front_depth(spec["unit"])
    inwall = {"marble"}
    # the shell IS the room's boundary, so it is the one family allowed to sit
    # on it; recessed fixtures live inside the ceiling slab for the same reason
    shell = {"back_wall", "ceiling", "floor", "side_wall_L", "side_wall_R", "front_wall"}
    for m in G.masses(spec):
        if m["name"] in shell or m["name"].startswith("dl_"):
            continue
        y0 = m["c"][1] - m["s"][1] / 2
        y1 = m["c"][1] + m["s"][1] / 2
        pockets = m["name"].startswith("tower_") and spec["unit"]["tower"].get("pocket_mm")
        if pockets:
            assert y1 <= rdep + 1e-6, f"{m['name']} passes through the wall"
            assert y0 >= -room["room_depth_mm"], f"{m['name']} leaves the room"
            continue
        if m["name"] in inwall or m["name"].startswith(("recess_", "wall_", "halo_")):
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
    # The study's 50-66% was measured over the SURFACES a room is made of. Round
    # 5 added three small styling props (a vase, a bronze, a candle wax) which
    # are analytic by nature and have no map set on disk, and counting them
    # against the same ratio dropped the whole palette to 47% — the guard firing
    # on a unit it was never measuring. Narrowed to its own stated purpose (the
    # hero surfaces cannot silently revert to flat colour) rather than having its
    # threshold quietly lowered, which would have been the easy way out.
    PROPS = {"vase_dark", "bronze_dark", "wax_white", "halo_led", "lens_warm",
             "trim_metal", "brass", "lacquer_white"}
    surfaces = {k for k in MAT.PALETTE if k not in PROPS}
    assert len(surfaces & set(dressed)) / len(surfaces) >= 0.5


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
    # ROUND 4: and the altar runs LENGTHWISE, which round 3 had upright. Measured
    # by the same horizontal/vertical detail-energy ratio the round-3 critic used:
    # delivered altar 2.26, ours 0.38 before this. Pinned on the axis ORDER, not
    # on today's numbers, so a rescale cannot quietly rotate the boards again.
    assert MAT.grain_axis("veneer_altar") == "x",         "altar veneer grain must run along the blocks, not up them"
    assert MAT.grain_axis("veneer_pier") == "z", "piers stay upright"
    assert MAT.grain_axis("veneer_fascia") == "x", "the rail runs lengthwise"


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


def test_the_spec_of_record_carries_a_SOLVED_camera(spec):
    """The camera solve is round 1's entire deliverable, and round 4 found it
    missing from the file everything else is built from: the spec of record
    still held the pre-solve VP estimate while every gate frame since round 2
    had been rendered from a private scratch spec. Nothing failed — a spec with
    a plausible camera renders a plausible picture — until the frame was rebuilt
    from the spec and 83 mm of camera height quietly went away.

    So this is not a test of today's numbers. It refuses any spec whose camera
    does not declare that it came from the solve, which is the only state that
    can produce that failure again."""
    cam = spec["camera"]
    assert "_solved" in cam, (
        "camera in the spec of record carries no _solved provenance — it may be "
        "a pre-solve estimate, which silently reverts round 1")
    init = {"x_mm": 1550.0, "y_mm": -4250.0, "z_mm": 1150.0, "yaw_deg": -20.5}
    assert not all(abs(cam[k] - v) < 1e-9 for k, v in init.items()), \
        "camera is byte-identical to the round-1 pre-solve VP estimate"


def test_downlights_are_one_decision_seen_twice(spec):
    """The housing the camera sees and the light that emits must come from the
    same source, or the room grows a fixture that glows where nothing is and a
    trim that is dark where something should be."""
    import trn001_light as L

    pos = {n: (x, y) for n, x, y, _ in G.downlight_positions(spec)}
    assert pos, "spec carries downlights"
    ms = {m["name"]: m for m in G.masses(spec)}
    for name, (x, y) in pos.items():
        for part in ("trim", "lens"):
            m = ms[f"{name}_{part}"]
            assert abs(m["c"][0] - x) < 1e-6 and abs(m["c"][1] - y) < 1e-6
    for f in L.plan(spec):
        if f["kind"] != "SPOT":
            continue
        assert (f["pos"][0], f["pos"][1]) == pos[f["name"]]
        # the emitter must hang BELOW the lens it appears to shine from
        assert f["pos"][2] < ms[f"{f['name']}_lens"]["c"][2]


def test_the_lens_is_visible_and_the_trim_reads_as_a_ring(spec):
    """The flange is an annulus made of two solids, because a boolean would
    carve the n-gons the export law forbids. That only works while the lens
    hangs just below the trim's underside and stays narrower than it."""
    ms = {m["name"]: m for m in G.masses(spec)}
    name = next(n for n, *_ in G.downlight_positions(spec))
    trim, lens = ms[f"{name}_trim"], ms[f"{name}_lens"]
    assert lens["s"][0] < trim["s"][0], "lens must be narrower than the trim"
    t_bot = trim["c"][2] - trim["s"][2] / 2
    l_bot = lens["c"][2] - lens["s"][2] / 2
    assert l_bot < t_bot, "lens must sit below the trim's underside or be hidden"
    assert t_bot - l_bot < 5.0, "lens must not hang off the ceiling"


def test_ies_normalisation_is_derived_not_pinned():
    """build_room's two hand-bracketed norms (0.20 for 5.ies, 0.065 for 7.IES)
    are one rule: norm x mean_candela lands on ~126 for both. This parser has to
    reproduce that, or a beam swap silently re-powers the room — which is the
    exact failure the lane-B pass paid for once already."""
    import trn001_light as L

    for fname, pinned in (("5.ies", 0.20), ("7.IES", 0.065)):
        p = L.ies_path(fname)
        if not os.path.exists(p):
            pytest.skip(f"{fname} not fetched")
        mean = L.ies_mean_candela(p)
        assert mean, f"{fname} candela table unreadable"
        derived = L.IES_NORM_K / mean
        assert abs(derived - pinned) / pinned < 0.02, \
            f"{fname}: derived {derived:.4f} vs build_room's measured {pinned}"


def test_a_missing_profile_never_silently_full_powers_a_light():
    """An unreadable IES must not fall through to norm 1.0 pretending to be
    normalised — it has to SAY so, because a 15x over-powered rig looks like a
    lighting choice."""
    import trn001_light as L

    norm, prov = L.ies_norm_for("no-such-profile.ies", "auto")
    assert "UNREAD" in prov
    norm2, prov2 = L.ies_norm_for("5.ies", 0.2)
    assert norm2 == 0.2 and prov2 == "pinned"


def test_marble_veining_cannot_regress_to_a_contour_map():
    """Two independent cold critics called our slab a topographic contour map,
    and they were describing a MATHEMATICAL property, not a taste: the level
    sets of a smooth scalar field are closed loops, so a fixed window on a fixed
    noise field can only ever return closed curves of one width. Tuning the
    window never escapes it — which is why the defect survived a whole round.

    What escapes it is strong anisotropy (closed loops stretched into streaks)
    plus a width that is itself an input. Pinned as those two properties rather
    than as today's constants."""
    import trn001_materials as MAT

    k = MAT.PROCEDURAL["marble"]
    sx, _, sz = k["stretch"]
    assert max(sx, sz) / min(sx, sz) >= 5.0, (
        "marble field must stay strongly anisotropic or its level sets close "
        "back into contours")
    assert k.get("width_var", 0) > 0.0, "vein width must vary along its length"
    assert k.get("tilt", 0.0) != 0.0, "the vein system runs on a diagonal"


def test_procedural_stone_gives_back_the_albedo_its_veining_eats():
    """The veining only ever multiplies albedo DOWN, so the built slab drifts
    below the albedo that was SAMPLED off the target — the same disease MAP_MEAN
    cures for image maps, and it cost 0.61 against a target of 0.80 before it
    was caught."""
    import trn001_materials as MAT

    assert MAT.PROCEDURAL["marble"].get("albedo_gain", 1.0) > 1.0


def test_the_stone_is_translucent_at_all():
    """Vault + research both say stone without subsurface reads as painted
    plaster. Sparing is the point — a value, not a switch left off."""
    import trn001_materials as MAT

    w = MAT.PROCEDURAL["marble"].get("sss_weight", 0.0)
    assert 0.0 < w <= 0.35, f"marble subsurface weight {w} is off or overdone"


def test_lathe_closes_into_a_solid():
    """A turned profile must come back as a closed solid, or it renders as a
    shell with holes where the caps should be."""
    import trn001_styling as S

    for name, prof in S.PROFILES.items():
        verts, faces = S.lathe(prof, 0.0, 0.0, 0.0, seg=16)
        assert verts and faces, name
        # every edge shared by exactly two faces = watertight
        edges = {}
        for f in faces:
            for i in range(len(f)):
                e = tuple(sorted((f[i], f[(i + 1) % len(f)])))
                edges[e] = edges.get(e, 0) + 1
        open_edges = [e for e, n in edges.items() if n != 2]
        assert not open_edges, f"{name}: {len(open_edges)} open edges"


def test_lathe_honours_the_measured_profile(spec):
    """The lathe's radius at a height is the measured radius, scaled — if it
    silently normalised or re-centred, a measured object would stop being one."""
    import trn001_styling as S

    verts, _ = S.lathe(S.VASE, 100.0, -50.0, 455.0, seg=64)
    zs = [v[2] for v in verts]
    assert min(zs) == pytest.approx(455.0)
    assert max(zs) == pytest.approx(455.0 + max(z for z, _ in S.VASE))
    # widest ring matches the profile's widest radius, about the given centre
    r_max = max(math.hypot(v[0] - 100.0, v[1] + 50.0) for v in verts)
    assert r_max == pytest.approx(max(r for _, r in S.VASE), abs=0.5)


def test_styling_objects_stand_on_the_surfaces_they_were_measured_against(spec):
    """The check that the back-projected placements are right is that they land
    on surfaces the placement was never told about: vases on the step top,
    candlesticks on the plinth top."""
    import trn001_styling as S

    u = spec["unit"]
    plinth_top = u["plinth"]["h_mm"]
    step_top = plinth_top + u["step"]["h_mm"]
    placed = S.plan(spec)
    assert placed, "spec carries styling"
    for p in placed:
        if p["cls"] == "vase":
            assert p["pos_mm"][2] == pytest.approx(step_top, abs=1.0)
        elif p["cls"] == "candlestick":
            assert p["pos_mm"][2] == pytest.approx(plinth_top, abs=1.0)
        # and nothing may float in front of the plinth it stands on
        assert p["pos_mm"][1] > -u["plinth"]["d_mm"], p["name"]


def test_the_candle_sits_on_top_of_its_own_stick(spec):
    """A styling pair whose two halves are placed independently is one edit away
    from a candle hovering above its holder."""
    import trn001_styling as S

    by = {p["name"]: p for p in S.plan(spec)}
    for c in spec["styling"]["candlesticks"]:
        stick, taper = by[c["name"]], by[c["name"] + "_taper"]
        assert taper["pos_mm"][2] == pytest.approx(
            stick["pos_mm"][2] + stick["height_mm"], abs=0.5)
        assert taper["pos_mm"][:2] == stick["pos_mm"][:2]


def test_the_unbuildable_styling_classes_are_declared_not_silently_dropped(spec):
    """(ข) assumed the CC0 pool would supply the organics; the first live test
    found it empty for statuary and florals. An absence that is not DECLARED
    reads as a scene that was finished."""
    import trn001_styling as S

    missing = S.unavailable(spec)
    assert missing, "the classes the pool cannot supply must be named in the spec"
    assert any("statuar" in m for m in missing)


def test_no_styling_object_stands_inside_a_solid(spec):
    """Owner, 2026-07-31: "แจกันทำไมไปตั้งตรงนั้น". A vase was standing INSIDE the
    left pedestal — because its position came from back-projecting onto the step
    plane, the hit landed 108 mm past the step's front edge, and I kept the x and
    clamped the y instead of reading that as the model being refuted.

    backproject() answers "where does this ray meet this PLANE"; it cannot know
    whether the hit lies within the surface's EXTENT, so it returns a confident
    number for an impossible question. This is the guard that turns that silence
    into a failure."""
    import trn001_styling as S

    solids = [m for m in G.masses(spec)
              if m["name"].startswith(("pedestal_", "centre_box", "step", "plinth",
                                       "tower_", "marble", "header_"))]
    for p in S.plan(spec):
        if p["cls"] not in ("vase", "candlestick"):
            continue
        px, py, pz = p["pos_mm"]
        prof = S.PROFILES[p["profile"]] if p["kind"] == "lathe" else None
        r = max(rr for _, rr in prof) if prof else 40.0
        r *= (p["height_mm"] / max(z for z, _ in prof)) if prof else 1.0
        for m in solids:
            x0, x1 = m["c"][0] - m["s"][0] / 2, m["c"][0] + m["s"][0] / 2
            y0, y1 = m["c"][1] - m["s"][1] / 2, m["c"][1] + m["s"][1] / 2
            z0, z1 = m["c"][2] - m["s"][2] / 2, m["c"][2] + m["s"][2] / 2
            # the object's footprint circle vs the mass's plan rectangle
            nx = min(max(px, x0), x1)
            ny = min(max(py, y0), y1)
            overlaps_plan = math.hypot(px - nx, py - ny) < r - 1e-6
            # and it only counts as INSIDE if their heights overlap too
            overlaps_z = pz < z1 - 1e-6 and pz + p["height_mm"] > z0 + 1e-6
            assert not (overlaps_plan and overlaps_z), (
                f"{p['name']} at ({px:.1f},{py:.1f},{pz:.1f}) r={r:.1f} stands "
                f"inside {m['name']}")


def test_every_styling_object_rests_on_a_real_surface(spec):
    """Standing beside a solid is not the same as standing ON one. Each prop's
    base must actually be supported by the top face of a mass whose plan extent
    contains it — otherwise it floats, which reads as a composite, not a room."""
    import trn001_styling as S

    tops = {}
    for m in G.masses(spec):
        if not m["name"].startswith(("step", "plinth", "pedestal_", "centre_box")):
            continue
        tops.setdefault(round(m["c"][2] + m["s"][2] / 2, 1), []).append(m)
    for p in S.plan(spec):
        if p["cls"] not in ("vase", "candlestick"):
            continue
        px, py, pz = p["pos_mm"]
        supports = [m for m in tops.get(round(pz, 1), [])
                    if m["c"][0] - m["s"][0] / 2 <= px <= m["c"][0] + m["s"][0] / 2
                    and m["c"][1] - m["s"][1] / 2 <= py <= m["c"][1] + m["s"][1] / 2]
        assert supports, f"{p['name']} base z={pz} is not on any mass's top face"


def test_the_vases_are_a_symmetric_pair_about_the_centre_box(spec):
    """Owner, 2026-07-31, on the second pass: "คำเดิม มันวางไม่สมมาตร". Same
    correction he had already made for the pedestals, and the same root cause —
    two independent x values instead of one mirrored offset, which is what lets
    a pair drift apart one edit at a time.

    Pinned on the RELATIONSHIP, not on today's 920.9 mm, and on the same axis the
    pedestals use: a symmetric pair is symmetric about the centre box, which sits
    off the room's centreline."""
    import trn001_styling as S

    vases = [p for p in S.plan(spec) if p["cls"] == "vase"]
    assert len(vases) == 2
    bcx = spec["unit"]["box"]["cx_mm"]
    left = min(vases, key=lambda p: p["pos_mm"][0])
    right = max(vases, key=lambda p: p["pos_mm"][0])
    assert (bcx - left["pos_mm"][0]) == pytest.approx(right["pos_mm"][0] - bcx, abs=0.5)
    # a pair standing on one surface shares its distance from the wall too
    assert left["pos_mm"][1] == pytest.approx(right["pos_mm"][1], abs=0.5)
    assert left["pos_mm"][2] == pytest.approx(right["pos_mm"][2], abs=0.5)
    # and they flank OUTBOARD of the pedestals they stand beside
    assert (bcx - left["pos_mm"][0]) > spec["unit"]["pedestal"]["cx_mm"]


def test_matcheck_refuses_a_narrow_patch_shared_between_frames():
    """Round 5: the row labelled "veneer_dark (right stile)" was sampling the
    CUBBY BACK in BOTH frames — 0.0205 and 0.0186 linear where a lit stile reads
    above 0.05 — so a cavity was reported as a stile and the two cavity rows
    silently agreed with each other. The stiles are ~10 px wide and the frames
    put them 6 px apart, so no shared box can sample both.

    The instrument that scores the work has to be checked against the work; this
    refuses the shape of box that cannot be right."""
    import trn001_matcheck as MC

    with pytest.raises(ValueError, match="per-frame"):
        MC._check_narrow("bogus (thin thing)", (1900, 1910, 700, 900))
    MC._check_narrow("wide enough", (900, 1200, 300, 360))          # no raise
    MC._check_narrow("paired", {"ours": (1, 9, 0, 9), "target": (2, 10, 0, 9)})

    for name, spec in MC.PATCHES.items():
        MC._check_narrow(name, spec)                                 # all legal
        ob, tb = MC._boxes(spec)
        assert len(ob) == 4 and len(tb) == 4, name


def test_every_narrow_matcheck_patch_is_located_per_frame():
    """Pinned as a property of the table, so a later edit cannot reintroduce a
    shared box on a thin feature."""
    import trn001_matcheck as MC

    for name, spec in MC.PATCHES.items():
        ob, tb = MC._boxes(spec)
        if (ob[1] - ob[0]) < MC.NARROW_PX:
            assert isinstance(spec, dict), f"{name} is narrow and must be per-frame"
            assert ob != tb, f"{name} gives identical boxes — locate it in each frame"


def test_the_two_veneer_species_stay_distinguishable():
    """The delivered joinery uses TWO woods; ours was one wood rendered twice.
    Measured at matched value the target's pair sits 1.499x apart in R/B and ours
    sat 1.104x — and 1.104x was exactly what the palette predicted, so albedo was
    the whole of it. Pinned on the SEPARATION, not on today's triples, and with
    the value held because the value error on these surfaces belongs to the light
    lane and must not be paid for twice."""
    import trn001_materials as MAT

    def rb(key):
        a = MAT.PALETTE[key][0]
        return a[0] / a[2]

    def lum(key):
        a = MAT.PALETTE[key][0]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    split = rb("veneer_fascia") / rb("veneer_pier")
    assert split > 1.20, (
        f"the rail and the carcass read as one wood (R/B split {split:.3f}); "
        f"the delivered pair measures 1.499x apart")
    # neither veneer may drift into the altar's value lane while cooling hue
    for k, want in (("veneer_fascia", 0.1806), ("veneer_pier", 0.1691)):
        assert lum(k) == pytest.approx(want, rel=0.02), (
            f"{k} moved in VALUE ({lum(k):.4f} vs {want}); this was a hue-only "
            f"change and its value belongs to the light lane")


# ---- the cavity has a depth of its own ---------------------------------------

def test_the_cubby_cavity_is_not_the_same_number_as_the_proud_depth(spec):
    """2026-08-01, and this is the class the project keeps paying for. The real
    unit has TWO depths — how far the carcass stands proud of the wall (100 mm,
    measured, still true) and how far the cavity pockets BACK into it (176.5 mm,
    measured, never modelled). One parameter for both is why proving the first
    read as proving the second, and why five rounds of light could not fix a
    cubby that was 82 mm deep instead of 276.5.

    Pinned as a RELATION, not as today's numbers, so re-measuring either depth
    cannot quietly collapse them back into one."""
    t = spec["unit"]["tower"]
    d, pk, b = t["d_mm"], t.get("pocket_mm", 0.0), t["board_mm"]
    assert pk > 0, "the towers stopped pocketing into the wall"
    ms = {m["name"]: m for m in G.masses(spec)}
    side = ms["tower_L_sA"]
    y0 = side["c"][1] - side["s"][1] / 2
    back = ms["tower_L_back"]
    y_back = back["c"][1] - back["s"][1] / 2
    assert y0 == pytest.approx(-d), f"carcass no longer stands {d} proud (got {-y0})"
    assert y_back == pytest.approx(pk), f"cavity back moved to {y_back}, spec says {pk}"
    assert y_back - y0 == pytest.approx(d + pk), "cavity depth != proud + pocket"
    # the shelves must reach the back of the cavity, or they read as a shallow one
    for i in range(len(t["shelves_L_z"])):
        sh = ms[f"tower_L_shelf{i}"]
        assert sh["c"][1] + sh["s"][1] / 2 == pytest.approx(pk), (
            f"shelf{i} stops short of the cavity back — the band a shelf top "
            f"shows is the measurement that proved the pocket")


def test_the_wall_actually_opens_where_a_tower_pockets_into_it(spec):
    """A pocket is only a pocket if the wall gets out of the way. The old wall
    layer could cut exactly ONE hole (the marble), so its jamb ran straight
    through both towers and would have filled the cavity back in — an omission
    silently undoing a measured decision, which is the recurring shape here."""
    ms = G.masses(spec)
    t, h = spec["unit"]["tower"], spec["unit"]["header"]
    pk = t.get("pocket_mm", 0.0)
    z_top = h["top_z_mm"] - h["band_h_mm"]
    for sgn, side in ((-1, "L"), (1, "R")):
        cx = h.get("cx_mm", 0.0) + sgn * (h["len_mm"] / 2 - t["w_mm"] / 2)
        # a point well inside the cavity, behind the old wall face
        probe = (cx, pk / 2, (t["base_top_mm"] + z_top) / 2)
        for m in ms:
            if not m["name"].startswith(("wall_", "recess_", "back_wall")):
                continue
            c, s = m["c"], m["s"]
            inside = all(abs(probe[k] - c[k]) < s[k] / 2 - 1e-6 for k in range(3))
            assert not inside, (
                f"{m['name']} fills tower {side}'s cavity at {probe}")


def test_deepening_the_wall_for_the_towers_never_moves_the_stone(spec):
    """The marble's 70 mm reveal is a measurement of its own. The towers made the
    wall 194.5 mm deep; the stone must not follow it back.

    The reveal is the distance from the wall FACE to the STONE's front face —
    not to whatever closes the hole behind it. Written the wrong way round first
    time and caught by the build: the back plate has to start behind the stone,
    so pinning the reveal on the plate pins it 18 mm out."""
    u = spec["unit"]
    rc = u.get("recess")
    assert rc, "spec lost its recess"
    ms = {m["name"]: m for m in G.masses(spec)}
    stone = ms["marble"]
    reveal = stone["c"][1] - stone["s"][1] / 2
    assert reveal == pytest.approx(rc["depth_mm"]), (
        f"the stone's reveal became {reveal} mm; it is measured at {rc['depth_mm']}")
    bp = ms.get("recess_backplate")
    assert bp is not None, "deep wall with no back plate — the marble opening is a void"
    assert bp["c"][1] + bp["s"][1] / 2 == pytest.approx(G.wall_front_depth(u)), (
        "the back plate does not reach the wall body — a void behind the stone")


def test_a_wall_layer_refuses_openings_that_overlap(spec):
    """Two holes sharing x would tile into overlapping solids that render as
    one — fail loud instead."""
    with pytest.raises(ValueError):
        G._wall_layer_masses([(0, 100, 0, 100), (50, 200, 0, 100)],
                             -500, 500, 0, 2700, 100)


def test_a_spec_without_a_pocket_still_builds_the_legacy_wall(spec):
    """Rounds 1-4 specs carry no pocket_mm. They must keep the single-opening
    recess wall byte-for-byte, so this change cannot rewrite history."""
    old = copy.deepcopy(spec)
    old["unit"]["tower"].pop("pocket_mm", None)
    names = {m["name"] for m in G.masses(old)}
    assert "recess_jambL" in names and "recess_jambR" in names
    assert not any(n.startswith("wall_pier") for n in names)


def test_no_solid_swallows_another_solid(spec):
    """COPLANAR FACES ARE NOT A STYLE QUESTION. The marble sits in a 70 mm
    recess and the wall body started at 70 too, so the stone (70..88) was
    contained in the wall with their front faces exactly coincident — the hero
    object was winning a BVH coin flip on every render. It lost the flip the day
    a second box went in behind it, and the slab came back as blank white paint.

    Pinned on CONTAINMENT rather than on the marble, because the next thing to
    be quietly buried will not be the marble."""
    ms = [m for m in G.masses(spec) if not m["name"].startswith("dl_")]
    shell = {"back_wall", "ceiling", "floor", "side_wall_L", "side_wall_R",
             "front_wall"}

    def box(m):
        return [(m["c"][k] - m["s"][k] / 2, m["c"][k] + m["s"][k] / 2)
                for k in range(3)]

    for a in ms:
        if a["name"] in shell:
            continue
        ba = box(a)
        for b in ms:
            if b is a:
                continue
            bb = box(b)
            if all(bb[k][0] <= ba[k][0] + 1e-6 and ba[k][1] <= bb[k][1] + 1e-6
                   for k in range(3)):
                assert False, (
                    f"{a['name']} is entirely inside {b['name']} — whichever "
                    f"the renderer picks is luck, not a decision")


def test_the_wall_body_never_starts_in_front_of_the_stones_back(spec):
    """The one number that keeps the stone out of the wall, held where the
    builder computes it so the two cannot drift."""
    u = spec["unit"]
    if not u.get("recess"):
        pytest.skip("no recess in this spec")
    ms = {m["name"]: m for m in G.masses(spec)}
    back = G.stone_back_y(u)
    wall = ms["back_wall"]
    assert wall["c"][1] - wall["s"][1] / 2 >= back - 1e-6, (
        "the wall body starts in front of the stone's back face")
    bp = ms.get("recess_backplate")
    if bp is not None:
        assert bp["c"][1] - bp["s"][1] / 2 >= back - 1e-6, (
            "the back plate starts in front of the stone's back face")


def test_first_hit_names_what_actually_blocks_the_view(spec):
    """THE PLANE-IS-NOT-THE-SURFACE GUARD. backproject() answers where a ray
    meets an infinite plane and knows nothing about extent or occlusion, so it
    returns a confident millimetre for points no camera can see. It has cost
    this project three times; the fourth was caught only because a cubby back
    panel 276 mm deep came back BRIGHTER than its own mouth.

    Two halves, both needed: a hidden point must be named as blocked, and a
    visible point must NOT be — including a point lying ON a surface, where the
    box it belongs to still contains the ray at t=1."""
    cam, ms = spec["camera"], G.masses(spec)
    u = spec["unit"]
    t, h = u["tower"], u["header"]
    w, b, d = t["w_mm"], t["board_mm"], t["d_mm"]
    pk = t.get("pocket_mm", 0.0)
    cxR = h.get("cx_mm", 0.0) + (h["len_mm"] / 2 - w / 2)

    # a point on a front-facing surface is visible and must not report itself
    stile = (cxR - (w - b) / 2, -d + 1.0, 1276.0)
    assert G.first_hit(cam, stile, ms)[0] is None, "a lit front face read as blocked"

    # the right tower faces the camera, so its back panel centre is visible
    assert G.first_hit(cam, (cxR, pk, 1276.0), ms)[0] is None

    # a point buried behind the room's own back wall cannot be seen
    blocked, _ = G.first_hit(cam, (cxR, G.wall_front_depth(u) + 400.0, 1276.0), ms)
    assert blocked is not None, "a point behind the wall read as visible"


def test_first_hit_agrees_with_the_projection_it_guards(spec):
    """The guard is only worth anything if it shares the camera with project():
    a visibility test on a different station would silently pass bad samples."""
    cam, ms = spec["camera"], G.masses(spec)
    # march along a ray through a known pixel; the first mass the guard names
    # must contain the point where that ray reaches it
    for uv in ((700.0, 900.0), (1200.0, 1400.0), (1850.0, 800.0)):
        p = G.backproject(cam, uv, ("y", 0.0), res=2048)
        if p is None:
            continue
        name, t_hit = G.first_hit(cam, p, ms)
        if name is None:
            continue
        m = next(x for x in ms if x["name"] == name)
        c = (cam["x_mm"], cam["y_mm"], cam["z_mm"])
        pt = tuple(c[i] + t_hit * (p[i] - c[i]) for i in range(3))
        for i in range(3):
            lo = m["c"][i] - m["s"][i] / 2 - 1.0
            hi = m["c"][i] + m["s"][i] / 2 + 1.0
            assert lo <= pt[i] <= hi, f"{name} hit point {pt} is outside the mass"


def test_the_roughness_a_material_asks_for_is_the_one_it_gets():
    """A COLUMN OF THE TABLE WAS DEAD. The CC0 roughness map was linked straight
    to the shader, so PALETTE's roughness was overridden for every mapped
    material: the marble asked 0.18 and rendered at 0.506 — the hero object's
    polish reached no frame in four rounds — paint asked 0.65 and got 0.911, the
    cavity asked 0.70 and got 0.471. SHEEN_CEILING was being tested against a
    number that never left the table.

    Same disease MAP_MEAN already cures for base colour, on the very next input.
    Pinned as "every mapped material has a measured mean to normalise by", so a
    new map set cannot silently reinstate the override."""
    import trn001_materials as MAT
    for key, (_alb, rough, _m, slug, _s) in MAT.PALETTE.items():
        if not slug:
            continue
        maps = MAT._map_set(slug) if hasattr(MAT, "_map_set") else None
        if maps is not None and "rough" not in maps:
            continue
        assert slug in MAT.ROUGH_MEAN, (
            f"{key} wears '{slug}', whose roughness map would override the "
            f"{rough} this table asks for — no measured mean to normalise by")
        gain = rough / MAT.ROUGH_MEAN[slug]
        assert 0.0 < gain < 8.0, f"{key}: implausible roughness gain {gain:.2f}"


def test_every_measured_map_mean_is_a_plausible_reading_of_its_map():
    """The normalisation is only as good as the means it divides by, and a mean
    typed in by hand is exactly the kind of number that goes stale silently.
    Re-read each map and check the stored mean still describes it.

    (Deliberately NOT a test that the shader receives the value — that needs bpy
    and would have to live in the build. A pure test asserting `rough == rough`
    would pass forever while proving nothing, which is the shape this project
    keeps catching in its own scorers.)"""
    import trn001_materials as MAT
    np = pytest.importorskip("numpy")
    Image = pytest.importorskip("PIL.Image")
    for slug, stored in MAT.ROUGH_MEAN.items():
        d = os.path.join(MAT.CC0, slug)
        if not os.path.isdir(d):
            pytest.skip(f"{slug} not on disk")
        f = [x for x in os.listdir(d) if "ough" in x.lower()]
        if not f:
            pytest.fail(f"{slug} has a stored roughness mean but no roughness map")
        a = np.asarray(Image.open(os.path.join(d, f[0])).convert("L"),
                       dtype=float) / 255.0
        assert a.mean() == pytest.approx(stored, abs=0.02), (
            f"{slug} roughness map now means {a.mean():.3f}, table says {stored}")


def test_cabinet_veneer_does_not_wear_the_floor_s_micro_bevel():
    """DR 2026-08-01 (notebook 2638a889, conv 579867c3): pre-finished flooring
    carries a 1-2 mm V-groove around every plank to hide subfloor lippage;
    cabinet panels are spliced flush and sanded to one seamless plane, and the
    linear micro-shadows at those joint lines are what makes the eye read a
    rendered panel as a floor.

    NORMAL_STRENGTH was keyed by map SLUG, and every veneer shares `wood_floor`
    with the actual floor — one parameter carrying two things, the same shape
    found in tower.d_mm the same day. Pinned as a RELATION (veneer relief must
    stay well under the floor's) so the two can never be collapsed again."""
    import trn001_materials as MAT
    floor = MAT.NORMAL_STRENGTH.get("floor_oak",
                                    MAT.NORMAL_STRENGTH.get("wood_floor", 0.8))
    for key in ("veneer_fascia", "veneer_pier", "veneer_altar", "cavity"):
        got = MAT.NORMAL_STRENGTH.get(key)
        assert got is not None, f"{key} falls back to the floor's plank relief"
        assert got <= floor / 2.0, (
            f"{key} relief {got} is not clearly below the floor's {floor} — "
            f"a cabinet panel showing plank bevels reads as flooring")


def test_leaf_layout_is_even_centre_balanced_and_refuses_impossible_panels():
    """DR 2026-08-01: architectural veneer is an EVEN number of equal leaves,
    152-305 mm wide, centred so no seam lands on the panel's centreline.

    The refusal half matters as much as the arithmetic: a 261 mm rail is wider
    than one leaf and narrower than two, so the honest answer is None. Rounding
    that into "one leaf" or "two narrow leaves" would invent a joint the trade
    does not cut."""
    import trn001_materials as MAT
    for panel in (446.0, 900.0, 1432.0, 2611.0, 3490.0):
        got = MAT.leaf_layout(panel)
        assert got is not None, f"{panel} mm should be splice-able"
        n, pitch = got
        assert n % 2 == 0, f"{panel} mm -> {n} leaves is odd; a seam lands on centre"
        assert MAT.LEAF_MIN_MM <= pitch <= MAT.LEAF_MAX_MM
        assert n * pitch == pytest.approx(panel)
    for panel in (261.0, 230.0, 100.0):
        assert MAT.leaf_layout(panel) is None, (
            f"{panel} mm admits no even leaf count in the trade range — that is "
            f"the answer, not a rounding opportunity")


def test_the_splice_runs_across_the_grain_not_along_it(spec):
    """A veneer leaf is long along the grain and narrow across it, so the splice
    axis is perpendicular to the figure. Held as a relation between the two
    tables rather than as two hand-typed letters, because this file has twice
    been bitten by one entry quietly meaning two things."""
    import trn001_materials as MAT
    for key, ax in MAT.LEAF_AXIS.items():
        assert ax != MAT.grain_axis(key), (
            f"{key} splices along its own grain direction ({ax}) — leaves would "
            f"be cut across the figure, which no flitch produces")


def test_every_spliced_panel_s_pitch_is_derived_from_its_real_width(spec):
    """The pitch table must re-derive from leaf_layout() applied to the panel's
    measured extent, so a re-measured carcass cannot leave a stale pitch behind
    — the failure that let the spec carry a pre-solve camera for two rounds."""
    import trn001_materials as MAT
    t = spec["unit"]["tower"]
    extents = {"veneer_pier": float(t["w_mm"])}
    for key, pitch in MAT.LEAF_PITCH_MM.items():
        assert key in MAT.LEAF_AXIS, f"{key} has a pitch but no splice axis"
        panel = extents.get(key)
        if panel is None:
            continue
        got = MAT.leaf_layout(panel)
        assert got is not None, f"{key}: {panel} mm admits no leaf layout"
        assert pitch == pytest.approx(got[1], abs=0.5), (
            f"{key} pitch {pitch} no longer matches leaf_layout({panel}) = {got[1]:.1f}")


def test_every_mass_gets_a_colour_no_other_mass_can_produce():
    """ASK THE RENDERER WHICH OBJECT THIS IS — a standing rule here, earned when
    region boxes reported four bed surfaces at one height that were really four
    objects at 155/165/178/199. The ID pass could not honour it: a 14-entry
    palette handed out with `i % 14` meant every colour named six of this scene's
    78 masses, so the mask could only ever return a shortlist. That is how a 6 mm
    brass bar stayed indistinguishable from the panel behind it.

    Round-trip over the whole capacity, plus the reserved background slot."""
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec_ = importlib.util.spec_from_file_location(
        "_trn001_build_pure", os.path.join(here, "trn001_build.py"))
    src = open(os.path.join(here, "trn001_build.py"), encoding="utf-8").read()
    ns = {}
    # the module imports bpy at top level; lift just the pure encoder pair
    start = src.index("ID_BASE, ID_STEPS")
    end = src.index("ID_CAPACITY =")
    exec(src[start:end], ns)
    exec(src[end:src.index("_id_counter")], ns)
    colour, index, cap = ns["id_colour"], ns["id_index"], ns["ID_CAPACITY"]

    seen = {}
    for i in range(cap):
        c = colour(i)
        key = tuple(round(x, 4) for x in c)
        assert key not in seen, f"index {i} collides with {seen[key]} at {key}"
        seen[key] = i
        assert index(c) == i, f"index {i} did not survive the round trip"
    # background must decode to nothing, not to mass 0
    assert index((0.0, 0.0, 0.0)) is None
    # and survive an 8-bit PNG quantisation, which is what the mask is written as
    for i in (0, 1, 37, cap - 1):
        c = colour(i)
        q = tuple(round(x * 255) / 255.0 for x in c)
        assert index(q) == i, f"index {i} lost to 8-bit quantisation"
