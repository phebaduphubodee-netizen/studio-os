"""
test_millwork.py — the CAD invariant for procedural built-ins, and the model-fit gate.

Pure python, no bpy (millwork.py is bpy-free by design, same as furniture.py). Run:
    python -m pytest pipeline/scripts/test_millwork.py -q
"""
import math
import pytest

import millwork as M

# The real PRJ-2026-002 v4 master-bedroom built-ins (mm -> m). These are the pieces the pro critic
# was looking at when it wrote "the wardrobe is a texture-mapped box with basic hardware".
BF09_3 = dict(kind="wardrobe",  x=2.300, y=2.650, W=3.300, D=0.600, H=2.800)   # tall door run
BF14   = dict(kind="headboard", x=5.150, y=-0.275, W=0.100, D=2.925, H=2.800)  # slat wall
BF11   = dict(kind="cabinet",   x=0.000, y=2.650, W=0.600, D=3.200, H=0.750)   # built-in desk
BF10   = dict(kind="cabinet",   x=0.650, y=5.250, W=2.500, D=0.600, H=2.800)   # tall door run

# vertex-average of the v4 outline [[0,-450],[5500,-450],[5500,2650],[5650,2650],[5650,8650],[0,8650]]
ROOM_CTR = (3.7167, 3.6167)
# the v4 items' footprint centres (m) — what the facing inference actually reads
ITEMS = [
    (4.159, 1.1005),    # bed (head EAST)
    (2.898, 1.129),     # bench at the foot
    (4.944, 2.458),     # side table NE
    (4.944, -0.191),    # side table SE
    (1.125, 4.255),     # armchair at the BF11 desk (the only piece in the dressing zone)
    (0.606, 1.153),     # tall TV console, west wall
]


def _parts(b, room_ctr=ROOM_CTR, items=ITEMS, floor_standing=True, face=None):
    axis, sign, src = M.mill_axis(b["x"], b["y"], b["W"], b["D"], room_ctr, items, face)
    assert axis is not None, "these four are all runs; mill_axis must not bail"
    return M.millwork_parts(b["kind"], b["W"], b["D"], b["H"], axis, sign,
                            floor_standing=floor_standing), axis, sign, src


def _assert_inside(parts, b):
    """THE INVARIANT: the plan-measured footprint never moves. Geometry may not silently grow it."""
    for nm, x, y, z, dx, dy, dz in parts:
        assert dx > 0 and dy > 0 and dz > 0, f"{nm}: degenerate box"
        assert -1e-9 <= x and x + dx <= b["W"] + 1e-9, f"{nm}: x out of bbox ({x}+{dx} > {b['W']})"
        assert -1e-9 <= y and y + dy <= b["D"] + 1e-9, f"{nm}: y out of bbox ({y}+{dy} > {b['D']})"
        assert -1e-9 <= z and z + dz <= b["H"] + 1e-9, f"{nm}: z out of bbox ({z}+{dz} > {b['H']})"


# ---- the CAD invariant, swept -------------------------------------------------------------------
@pytest.mark.parametrize("b", [BF09_3, BF14, BF11, BF10])
def test_real_builtins_stay_inside_their_plan_bbox(b):
    parts, _, _, _ = _parts(b)
    assert parts, f"{b['kind']} should generate joinery"
    _assert_inside(parts, b)


@pytest.mark.parametrize("kind", ["wardrobe", "headboard", "cabinet"])
@pytest.mark.parametrize("W,D,H", [
    (3.300, 0.600, 2.800),   # the real wardrobe
    (0.100, 2.925, 2.800),   # the real slat wall (depth on X)
    (0.600, 3.200, 0.750),   # the real desk
    (0.300, 1.000, 2.400),   # a narrow tall run
    (1.000, 0.300, 0.400),   # a low shallow run
    (0.080, 0.500, 2.800),   # pathologically shallow (depth < the door thickness)
    (0.500, 0.060, 0.200),   # pathologically small every way
    (6.000, 0.650, 2.400),   # a long run (many leaves)
])
@pytest.mark.parametrize("sign", [1, -1])
def test_invariant_holds_for_every_shape_kind_and_facing(kind, W, D, H, sign):
    """A degenerate built-in must get FEWER parts — never a part outside its footprint."""
    axis = "x" if W < D else "y"
    parts = M.millwork_parts(kind, W, D, H, axis, sign)
    _assert_inside(parts, dict(W=W, D=D, H=H))


# ---- FACING: the semantic layer ------------------------------------------------------------------
# Facing is the owner's to declare (this repo's two-layer law). It is load-bearing: the clay is the
# beauty pass's STRUCTURAL CONTROL, so a wardrobe whose leaves face the wall teaches the repaint
# that the wardrobe opens into the plaster — worse than leaving it a box.
def test_the_room_centroid_is_the_WRONG_way_to_infer_facing():
    """THE BUG THIS TEST CAUGHT (2026-07-12, pre-render). PRJ-2026-002's suite outline is L-shaped
    (bedroom + dressing), and BF09-3 sits ON the boundary. The outline's vertex-centroid lands in
    the DRESSING zone, north of the wardrobe — so a centroid rule opens the wardrobe AWAY from the
    bed it serves. Pin the counterexample so nobody 'simplifies' the inference back to a centroid."""
    cx, cy = ROOM_CTR
    assert cy > BF09_3["y"] + BF09_3["D"] / 2.0, "the centroid really is on the wrong side"
    _, sign_centroid, src = M.mill_axis(BF09_3["x"], BF09_3["y"], BF09_3["W"], BF09_3["D"],
                                        ROOM_CTR, item_ctrs=())      # no items -> centroid path
    assert (sign_centroid, src) == (1, "centroid"), "centroid alone points the doors NORTH — wrong"
    _, sign_items, src2 = M.mill_axis(BF09_3["x"], BF09_3["y"], BF09_3["W"], BF09_3["D"],
                                      ROOM_CTR, ITEMS)
    assert (sign_items, src2) == (-1, "items"), "reading the furniture points the doors SOUTH — right"


@pytest.mark.parametrize("b,axis,sign,what", [
    (BF09_3, "y", -1, "wardrobe faces SOUTH, at the bed it serves (5 pieces s / 1 n)"),
    (BF14,   "x", -1, "the bed-head slat wall faces WEST, into the room (0 pieces e / 6 w)"),
    (BF11,   "x",  1, "the built-in desk is on the WEST wall and faces EAST (6 pieces e / 0 w)"),
    (BF10,   "y", -1, "the dressing cabinet faces SOUTH, into the dressing zone"),
])
def test_every_real_builtin_faces_the_side_it_serves(b, axis, sign, what):
    _, ax, sg, src = _parts(b)
    assert (ax, sg) == (axis, sign), what
    assert src == "items"


def test_an_owner_declared_face_wins_and_defines_the_axis():
    """Two-layer law: a declared facing is authoritative — no inference, no ratio screen. It sets
    the axis and the sign outright; the only thing the code may add is a REVIEW note when the
    declaration opens the run from its end (see test_a_declaration_that_opens_the_run_from_its_END).
    It may never silently substitute its own guess."""
    for face, want in (("N", ("y", 1)), ("S", ("y", -1)), ("E", ("x", 1)), ("W", ("x", -1))):
        ax, sg, src = M.mill_axis(BF09_3["x"], BF09_3["y"], BF09_3["W"], BF09_3["D"],
                                  ROOM_CTR, ITEMS, face=face)
        assert (ax, sg) == want, "the owner's face defines the axis and the sign"
        assert src.startswith("declared"), "and it is never demoted to a heuristic"
    # it overrides the inference, even when the inference disagrees (items say S; owner says N)
    ax, sg, src = M.mill_axis(BF09_3["x"], BF09_3["y"], BF09_3["W"], BF09_3["D"],
                              ROOM_CTR, ITEMS, face="N")
    assert sg == 1 and src == "declared", "the owner outranks the heuristic. Always."


# ---- the wardrobe: door leaves, reveals, toe-kick, pull-gap --------------------------------------
def test_wardrobe_gets_leaves_reveals_toekick_and_pullgap():
    parts, axis, sign, _ = _parts(BF09_3)
    names = [p[0] for p in parts]
    assert (axis, sign) == ("y", -1)
    assert "carcass" in names and "plinth" in names
    doors = [p for p in parts if p[0].startswith("door")]
    assert len(doors) == 6, f"3.3 m run / 0.55 m target leaf = 6 leaves, got {len(doors)}"

    # leaves are equal, and separated by a REAL reveal (the shadow line the repaint reads)
    widths = {round(p[4], 6) for p in doors}          # dx = along-run for a Y-depth piece
    assert len(widths) == 1, "leaves must be equal width"
    leaf = widths.pop()
    assert abs(leaf - (3.300 - 7 * M.REVEAL) / 6) < 1e-9
    xs = sorted(p[1] for p in doors)
    for a, b in zip(xs, xs[1:]):
        assert abs((b - a) - (leaf + M.REVEAL)) < 1e-9, "leaves must be gapped by exactly one reveal"
    assert abs(xs[0] - M.REVEAL) < 1e-9, "an end reveal too, or the run reads as a slab"

    # the pull-gap is the hardware: doors stop short of the top, exposing the carcass -> shadow rail
    door_top = max(p[3] + p[6] for p in doors)
    assert abs((BF09_3["H"] - door_top) - M.PULL_H) < 1e-9
    # ...and start above the toe-kick
    assert abs(min(p[3] for p in doors) - M.PLINTH_H) < 1e-9


def test_leaves_stand_proud_of_the_carcass_on_the_room_side():
    parts, _, _, _ = _parts(BF09_3)
    doors = [p for p in parts if p[0].startswith("door")]
    carc = next(p for p in parts if p[0] == "carcass")
    door_front = min(p[2] for p in doors)                      # y of the leaf face (sign -1 -> low Y)
    assert door_front == pytest.approx(0.0, abs=1e-9), "leaves sit ON the front plane of the bbox"
    assert carc[2] == pytest.approx(M.T_DOOR, abs=1e-9), "the carcass is set back by one leaf"
    assert door_front < carc[2], "leaves must stand PROUD of the carcass — that gap IS the reveal"


def test_toekick_is_set_back_so_it_casts():
    parts, _, _, _ = _parts(BF09_3)
    plinth = next(p for p in parts if p[0] == "plinth")
    doors = [p for p in parts if p[0].startswith("door")]
    door_front = min(p[2] for p in doors)
    assert plinth[2] - door_front == pytest.approx(M.PLINTH_R, abs=1e-9), \
        "the toe-kick must be recessed from the door face, or there is no shadow at the floor"
    assert plinth[6] == pytest.approx(M.PLINTH_H)


def test_wall_mounted_run_gets_no_toekick():
    """A floating cabinet has no floor to kick."""
    parts, _, _, _ = _parts(BF09_3, floor_standing=False)
    assert not any(p[0] == "plinth" for p in parts)
    assert min(p[3] for p in parts if p[0].startswith("door")) == pytest.approx(0.0)


# ---- the slat wall ------------------------------------------------------------------------------
def test_headboard_becomes_battens_not_a_box():
    parts, axis, sign, _ = _parts(BF14)
    assert (axis, sign) == ("x", -1)
    slats = [p for p in parts if p[0].startswith("slat")]
    assert any(p[0] == "backer" for p in parts)
    assert len(slats) >= 30, f"a 2.925 m run at ~67 mm pitch is ~43 battens, got {len(slats)}"
    backer = next(p for p in parts if p[0] == "backer")
    assert all(p[3] == pytest.approx(0.0) for p in slats), "battens run full height"
    assert all(p[6] == pytest.approx(BF14["H"]) for p in slats)
    assert min(p[1] for p in slats) < backer[1], "battens must stand proud toward the room"
    ys = sorted(p[2] for p in slats)
    gaps = [b - a - M.SLAT_W for a, b in zip(ys, ys[1:])]
    assert all(g > 0.010 for g in gaps), "battens must be gapped or it is just a panel"


def test_slat_wall_too_short_falls_back_to_a_box():
    assert M.millwork_parts("headboard", 0.100, 0.090, 2.8, "x", 1) == []


# ---- the slat wall: a design block overrides the rhythm -----------------------------------------
def test_a_headboard_design_block_sets_the_slat_rhythm():
    """BF14 D2-A = 40 mm face / 20 mm gap (2:1, 66% solid). The design block must drive the pitch;
    absent one, the DEFAULT constants render — the pinned test above depends on that fallback."""
    d = {"slat_face_mm": 40, "slat_gap_mm": 20, "slat_depth_mm": 22}
    parts = M.millwork_parts("headboard", 0.100, 2.540, 2.800, "x", -1, design=d)
    slats = [p for p in parts if p[0].startswith("slat")]
    # depth axis is X here, so the along-run FACE width is dy (p[5]); dx (p[4]) is the proudness
    assert all(abs(p[5] - 0.040) < 1e-9 for p in slats), "every batten face is the design's 40 mm"
    assert all(abs(p[4] - 0.022) < 1e-9 for p in slats), "and it stands 22 mm proud (slat_depth_mm)"
    # 2540 mm / (40+20) pitch -> ~42 battens, redistributed to end flush
    assert len(slats) == int(2.540 // 0.060)
    # a design block with no slat keys falls back to the module defaults (no crash, no zero-div)
    dflt = M.millwork_parts("headboard", 0.100, 2.540, 2.800, "x", -1, design={"element": 1})
    assert any(abs(p[5] - M.SLAT_W) < 1e-9 for p in dflt if p[0].startswith("slat"))


# ---- the slat wall: an ISSUED SCHEDULE outranks the auto-fit -------------------------------------
# BF14 as ISSUED 2026-07-16c (element1-oak-signature-wall_DD-2026-07-16.md, D2-A-MODULE): AKUWALL
# 27/13 on the ink-proven 3250.2 x 2800. Numbers are the DD's, not the code's — if the code and this
# table ever disagree, the code is wrong.
ISSUED = dict(slats=77, field_mm=3067.0, reveal_mm=12.0,
              post_south_mm=79.6, post_north_mm=79.6, cut_length_mm=2776,
              post_south_material="microcement", post_north_material="oak")
AKUWALL = {"slat_face_mm": 27, "slat_gap_mm": 13, "slat_depth_mm": 12}
BF14_RUN, BF14_H, BF14_W = 3.250, 2.800, 0.100      # spec `d` is a NOMINAL integer; ink = 3250.2


def _bf14_issued():
    return M.millwork_parts("headboard", BF14_W, BF14_RUN, BF14_H, "x", -1,
                            design=dict(AKUWALL, schedule=ISSUED))


def test_the_issued_schedule_renders_77_slats_not_the_81_the_autofit_wants():
    """THE POINT OF THE WHOLE BRANCH. The auto-fit divides the run by the module and redistributes
    the remainder into every gap: 81 slats at pitch 40.12, both ends dying in a half-gap of air.
    The ISSUE is 77 at a TRUE 40 pitch bracketed by two real terminal members. The owner chose the
    AKUWALL module by LOOKING at a render of the 81-slat auto-fit — the module was his to judge and
    he judged it right, but the render was never the issued wall. This is that gap, closed."""
    parts = _bf14_issued()
    slats = [p for p in parts if p[0].startswith("slat")]
    assert len(slats) == 77, f"the issued schedule is 77 slats, got {len(slats)}"
    assert len([p for p in parts if p[0] == "jambmineral"]) == 1
    assert len([p for p in parts if p[0] == "postoak"]) == 1
    # the field is BUTTED (starts and ends flush on a slat face), not centred in a pitch
    ys = sorted(p[2] for p in slats)
    assert all(abs(p[5] - 0.027) < 1e-9 for p in slats), "every batten face is the issued 27 mm"
    pitches = [b - a for a, b in zip(ys, ys[1:])]
    assert all(abs(q - 0.040) < 1e-9 for q in pitches), "a TRUE 40 pitch — not 40.12 redistributed"
    gaps = [b - a - 0.027 for a, b in zip(ys, ys[1:])]
    assert all(abs(g - 0.013) < 1e-9 for g in gaps), "the issued 13 mm gap, undrifted"
    field = (ys[-1] + 0.027) - ys[0]
    assert field * 1000 == pytest.approx(3067.0, abs=0.05), "77 x 27 + 76 x 13 = 3067.0 exact"


def test_the_north_terminus_is_SCRIBED_so_the_02_never_drops_a_member():
    """Datum south, scribe north (the DD's instruction). The spec's `d` is a nominal 3250 while the
    schedule closes on the ink's 3250.2 — a LITERAL 79.6 north post would end at 3250.2, overrun the
    bbox, and `part()` would SILENTLY DROP it: a render missing a member that still looks fine. The
    terminus is therefore whatever run REMAINS, and the 0.2 dies exactly where the DD says it dies."""
    parts = _bf14_issued()
    jamb = next(p for p in parts if p[0] == "jambmineral")
    post = next(p for p in parts if p[0] == "postoak")
    assert jamb[2] == pytest.approx(0.0), "the SOUTH is the datum — the jamb starts on it"
    assert jamb[5] * 1000 == pytest.approx(79.6, abs=0.01), "the south jamb is issued at a literal 79.6"
    assert post[5] * 1000 == pytest.approx(79.4, abs=0.01), "the north terminus SCRIBES to 79.4"
    assert (post[2] + post[5]) == pytest.approx(BF14_RUN, abs=1e-9), "and it closes ON the wall"
    # the member is REAL, not dropped
    assert post[5] > 0.070, "a dropped terminus is the failure this test exists to catch"


def test_the_shaft_floats_on_a_12mm_reveal_and_the_backer_is_what_shows_in_it():
    """D7-B item 5: one reveal number, 12, all round -> BF14 reads as one 2776 shaft floating on a
    single dark line. The auto-fit ran the battens FULL height (0 -> 2800): no reveal existed at all,
    so the issued cut length was a number in a document that no render had ever obeyed."""
    parts = _bf14_issued()
    members = [p for p in parts if not p[0].startswith("backer")]
    backer = next(p for p in parts if p[0] == "backer")
    assert all(p[3] * 1000 == pytest.approx(12.0, abs=0.01) for p in members), "12 mm floor reveal"
    assert all(p[6] * 1000 == pytest.approx(2776.0, abs=0.05) for p in members), "cut length 2776"
    assert all(p[3] + p[6] == pytest.approx(BF14_H - 0.012) for p in members), "12 mm ceiling reveal"
    assert backer[3] == pytest.approx(0.0) and backer[6] == pytest.approx(BF14_H), \
        "the backer runs FULL height — what shows in the reveal is the dark backer, not a void"


def test_EVERY_reveal_is_backed_dark_including_the_terminals():
    """THE BUG THE FIRST RENDER SHIPPED WITH (review 2026-07-16c). The field backer must stop short
    of the full-depth terminal members (z-fight) — but stopping short left each terminal's 12 mm
    floor/ceiling reveal as a HOLE STRAIGHT THROUGH THE WALL. A raycast in the shipped .blend proved
    it: under the jamb the 'shadow gap' looked out to the full-height east glass and rendered as a
    DAYLIGHT slot; under the post it read as lit plaster 347 mm behind. The single dark line BF14
    floats on broke BRIGHT at exactly the two ends D7 exists to show.

    So: sweep the whole run at floor and ceiling level, and assert something dark backs it EVERYWHERE."""
    parts = _bf14_issued()
    backers = [p for p in parts if p[0].startswith("backer")]
    for z_probe, where in ((0.006, "floor reveal"), (2.794, "ceiling reveal")):
        for y_probe, what in ((0.040, "under the JAMB"), (1.600, "under the field"),
                              (3.210, "under the POST")):
            hit = [p for p in backers
                   if p[2] - 1e-9 <= y_probe <= p[2] + p[5] + 1e-9
                   and p[3] - 1e-9 <= z_probe <= p[3] + p[6] + 1e-9]
            assert hit, f"{what}, the {where} is UNBACKED — it renders as a hole through the wall"
    # and the backing sits at the SAME set-back everywhere, so the dark line reads as one line
    assert len({round(p[1], 6) for p in backers}) == 1, "every reveal is backed at the same depth"


def test_the_reveal_backing_never_routes_to_mineral():
    """The names are a contract with a router that checks `endswith('mineral')` BEFORE
    `startswith('backer')`. A filler named `backer_jambmineral` would paint MICROCEMENT — which the
    DD explicitly forbids in a reveal ("reveal interiors get the dark backer, NOT trowelled mineral —
    a 15 x 22 slot will not take a burnished coat"). Pin the routing, not just the name."""
    import material_presets as mp
    for p in _bf14_issued():
        if p[0].startswith("backer"):
            assert mp.mill_object_role(f"mill__BF14__{p[0]}") == "backing", \
                f"{p[0]} routes to the wrong material — a reveal must never be trowelled mineral"


def test_the_backer_stops_short_of_the_full_depth_terminal_members():
    """The terminal members are the wall's full 100 mm thickness (the south jamb is the curtain
    mouth's west shoulder; the north terminus scribes into BF09-3). A backer spanning the whole run
    would interpenetrate both — the cross-material z-fight review 2026-07-16 caught on the tower."""
    parts = _bf14_issued()
    backer = next(p for p in parts if p[0] == "backer")
    jamb = next(p for p in parts if p[0] == "jambmineral")
    post = next(p for p in parts if p[0] == "postoak")
    assert backer[2] >= jamb[2] + jamb[5] - 1e-9, "backer starts at/after the jamb's north face"
    assert backer[2] + backer[5] <= post[2] + 1e-9, "and stops at/before the terminus' south face"
    assert jamb[4] == pytest.approx(BF14_W), "the jamb is the wall's FULL depth"
    assert post[4] == pytest.approx(BF14_W), "so is the terminus"
    slats = [p for p in parts if p[0].startswith("slat")]
    assert all(p[4] == pytest.approx(0.012) for p in slats), "battens stand 12 proud of the backer"


@pytest.mark.parametrize("bad,why", [
    (dict(ISSUED, slats=78), "a slat count edited without re-deriving field_mm"),
    (dict(ISSUED, cut_length_mm=2770), "a cut length that disagrees with H - 2 x reveal"),
    (dict(ISSUED, slats=1), "a degenerate slat count"),
    (dict(ISSUED, slats=77.9), "a fractional count int() would silently TRUNCATE to 77 — and then "
                               "field_mm, re-derived from the truncated count, agrees with itself"),
    # EVERY cross-check is REQUIRED. An optional one is a safety net the schedule can decline, and
    # the number that would catch the mistake is exactly the one a careless edit drops.
    ({k: v for k, v in ISSUED.items() if k != "reveal_mm"}, "a cutting list missing a number"),
    ({k: v for k, v in ISSUED.items() if k != "field_mm"}, "no field_mm = no module cross-check"),
    ({k: v for k, v in ISSUED.items() if k != "cut_length_mm"}, "no cut length to check against"),
    ({k: v for k, v in ISSUED.items() if k != "post_north_mm"}, "an UNBOUNDED scribe"),
    # A DESIGN decision must not be revertible by an omission: no terminal material -> no oak default
    ({k: v for k, v in ISSUED.items() if k != "post_south_material"}, "D7 reverting to oak silently"),
    ({k: v for k, v in ISSUED.items() if k != "post_north_material"}, "an undeclared terminal"),
    (dict(ISSUED, post_south_material="walnut"), "a material typo"),
])
def test_an_inconsistent_schedule_FAILS_LOUD_it_never_renders_a_wall_nobody_issued(bad, why):
    with pytest.raises(ValueError):
        M.millwork_parts("headboard", BF14_W, BF14_RUN, BF14_H, "x", -1,
                         design=dict(AKUWALL, schedule=bad))


@pytest.mark.parametrize("run,why", [
    (3.180, "a run too short for the schedule"),
    (3.500, "a run the schedule no longer describes"),
])
def test_a_run_that_disagrees_with_its_schedule_FAILS_LOUD(run, why):
    """The scribe absorbs the ink's sub-mm, NOT a different wall. If `d` is edited without
    re-issuing the schedule, that is two walls and it must raise — not silently scribe a 329 mm
    'terminus' or drop the member off the end."""
    with pytest.raises(ValueError, match="scribe|terminus"):
        M.millwork_parts("headboard", BF14_W, run, BF14_H, "x", -1,
                         design=dict(AKUWALL, schedule=ISSUED))


@pytest.mark.parametrize("kind", ["wardrobe", "cabinet", "panel", "tv_panel"])
def test_a_schedule_on_the_WRONG_KIND_is_never_silently_discarded(kind):
    """Only the headboard branch reads `schedule`, so on any other kind an issued cutting list — the
    slat count, the field, D7's terminal materials — evaporated with no warning and a different piece
    rendered. Screened FIRST, ahead of the degenerate-bbox and PANEL_KINDS early returns, which would
    otherwise swallow it just as quietly."""
    with pytest.raises(ValueError, match="headboard"):
        M.millwork_parts(kind, 0.600, 3.300, 2.800, "y", -1, design=dict(AKUWALL, schedule=ISSUED))
    # even a degenerate bbox must not swallow it
    with pytest.raises(ValueError, match="headboard"):
        M.millwork_parts(kind, 0.0, 0.0, 0.0, "y", -1, design=dict(AKUWALL, schedule=ISSUED))


def test_no_schedule_block_keeps_the_autofit_byte_identical():
    """OPT-IN, like `open` and `design` before it: every other slat wall in the repo must render
    exactly what it rendered yesterday."""
    auto = M.millwork_parts("headboard", BF14_W, BF14_RUN, BF14_H, "x", -1, design=AKUWALL)
    assert len([p for p in auto if p[0].startswith("slat")]) == 81, "the auto-fit still auto-fits"
    assert not any(p[0] in ("jambmineral", "postoak") for p in auto), "no terminal members uninvited"
    assert all(p[6] == pytest.approx(BF14_H) for p in auto), "and no reveal uninvited"


def test_the_canonical_spec_builds_its_own_issued_schedule():
    """END-TO-END on the real artifact: the spec ALREADY carried design.schedule — the build layer
    was simply ignoring it. Reads the shipped JSON so a spec edit that breaks the issue fails HERE."""
    import io
    import json
    import os
    p = os.path.join(os.path.dirname(__file__), "..", "..", "projects",
                     "PRJ-2026-002_c001-house", "03_layout", "master-suite.CANONICAL.spec.json")
    b = next(x for x in json.load(io.open(p, encoding="utf-8"))["builtins"] if x.get("bf") == "BF14")
    parts = M.millwork_parts(b["kind"], b["w"] / 1000, b["d"] / 1000, b["h"] / 1000, "x", -1,
                             design=b.get("design"))
    assert len([x for x in parts if x[0].startswith("slat")]) == 77
    assert {"jambmineral", "postoak", "backer"} <= {x[0] for x in parts}


# ---- the OPEN dressing wall: no leaves, you see INTO it ------------------------------------------
OPEN = dict(kind="wardrobe", W=3.300, D=0.600, H=2.800)   # BF09-3 as an open:true dressing wall


def test_open_wardrobe_has_NO_leaves_and_you_see_into_it():
    """`open_front=True` builds an open dressing wall: a brass rail, floating drawers, open shelves,
    and NO door leaves — the exact opposite of the closed run. The gaps + the microcement fronts are
    what a repaint reads as open sourceable joinery where a door run reads as a shut box."""
    parts = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    names = [p[0] for p in parts]
    assert not any(n.startswith("door") for n in names), "an OPEN wall has no leaves"
    assert any(n.startswith("rail") for n in names), "a brass hang-rail"
    assert any("front" in n for n in names), "floating drawer fronts"
    assert any(n.startswith("shelf") for n in names), "open shelves"
    assert "back" in names and "top" in names, "a carcass you see into"


def test_open_is_OPT_IN_the_default_call_still_builds_a_door_run():
    """The flag is opt-in: the SAME piece without it must still produce the closed leaves the
    pinned wardrobe test depends on. A silent switch would rebuild every shipped wardrobe."""
    closed = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1)
    assert any(p[0].startswith("door") for p in closed)
    opened = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    assert not any(p[0].startswith("door") for p in opened)


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("W,D,H", [(3.300, 0.600, 2.800), (2.000, 0.550, 2.400),
                                   (1.200, 0.600, 2.700), (0.040, 0.600, 2.800)])
def test_open_wall_never_leaves_its_plan_bbox(W, D, H, sign):
    """The CAD invariant again: an open wall's rail/drawers/shelves may never grow the footprint.
    The last shape is a 40 mm-DEEP shallow wall (not a tiny run) — it still composes, and every
    part must stay inside. part() drops any box that would overflow, so this can never fail loudly
    but a code bug that mis-computes an offset would."""
    axis = "x" if W < D else "y"
    parts = M.millwork_parts("wardrobe", W, D, H, axis, sign, open_front=True)
    _assert_inside(parts, dict(W=W, D=D, H=H))


def test_open_hang_bay_has_BOTH_signed_zones():
    """D4-A signed a two-zone bay: a DOUBLE short-hang (two stacked rails) + a SINGLE full-hang
    (one lower rail). The first cut emitted one rail at 2.37 m — above the signed full-hang height
    and dropping the short-hang zone. Pin both zones and a plausible full-hang height."""
    parts = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    rails = [p for p in parts if p[0].startswith("rail")]
    assert any(p[0].startswith("rail_short") for p in rails), "the double short-hang zone"
    assert sum(p[0].startswith("rail_short") for p in rails) == 2, "short-hang is DOUBLE (two rails)"
    assert any(p[0] == "rail_full" for p in rails), "the single full-hang rail"
    full = next(p for p in rails if p[0] == "rail_full")
    assert 1.6 <= full[3] <= 2.1, f"full-hang rail at a plausible height, got z={full[3]:.2f}"


def test_open_part_names_route_brass_and_microcement():
    """build_room paints mill__ parts by the trailing name: 'rail*' -> satin brass, '*front*' and
    'towerback' -> cool microcement, the rest -> oak. Pin the names the router keys on."""
    parts = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    names = [p[0] for p in parts]
    assert any(n.startswith("rail") for n in names)                   # -> brass
    assert any("front" in n or n.startswith("towerback") for n in names)  # -> microcement


def test_open_drawers_actually_FLOAT():
    """D3-A: the drawer stack floats — a real air/shadow reveal below it, not a stack sitting on
    the floor. The lowest drawer front must start well above the plinth."""
    parts = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    fronts = [p for p in parts if "front" in p[0]]
    assert fronts, "there are drawer fronts"
    assert min(p[3] for p in fronts) >= M.FLOAT_Z - 1e-9, "the stack floats above the floor"


def test_open_display_shelves_respect_the_span_rule():
    """Ask1/NLM load rule: an open shelf spans <= MAX_SPAN before it needs a divider — that is WHY
    the tower AND the mid-bay gable exist. EVERY shelf (bay short/full-hang, tower, niche) must
    stay within it — no exclusions. (Review 2026-07-16: the first cut had a single 1.46 m
    unsupported bay shelf and the test HID it by excluding shelf_bay; the mid-gable split fixed
    the geometry, so the exclusion is gone and the test is honest.)"""
    parts = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    shelves = [p for p in parts if p[0].startswith("shelf")]
    assert len(shelves) >= 4, "bay (x2) + tower + niche shelves"
    for p in shelves:
        span = p[4] if OPEN["W"] > OPEN["D"] else p[5]   # along-run dimension (axis y -> dx=p[4])
        assert span <= M.MAX_SPAN + 1e-9, f"{p[0]} span {span:.3f} exceeds MAX_SPAN {M.MAX_SPAN}"


def test_cell_internals_reach_their_right_gable_no_18mm_slot():
    """P2r-8 regression, measured off the built p2r17 scene before the fix:
    every cell's internals ended exactly one CARC_T (18 mm) short of the gable
    on their right (tower 7.0778 vs gable face 7.0958; bay-1-0 tower 4.553 vs
    4.5706) — C2-r12#10's 'dark shadow slot beside the white drawer stack'.
    The old arithmetic sized internals `span - 2*CARC_T` as if both flanking
    gable slabs lay inside the span; each span already starts at its left
    gable's inner face. An internal must END where the next slab STARTS."""
    parts = M.millwork_parts(OPEN["kind"], OPEN["W"], OPEN["D"], OPEN["H"], "y", -1, open_front=True)
    by = {p[0]: p for p in parts}
    gable_starts = sorted(p[1] for p in parts if p[0].startswith("gable"))
    for nm in ("shelf_sh", "shelf_fh", "shelf_tw0", "shelf_tw1", "towerback",
               "drawer_box0"):
        p = by.get(nm)
        assert p is not None, nm
        edge = p[1] + p[4]
        nxt = [g for g in gable_starts if g >= edge - 1e-6]
        assert nxt, f"{nm} has no gable to its right"
        assert abs(edge - nxt[0]) < 1e-6, \
            f"{nm} ends {1000 * (nxt[0] - edge):.1f} mm short of its gable"
    # microcement fronts keep exactly the 2 mm/side handleless reveal — never
    # coplanar with an oak gable face, never the old 18 mm void
    f, tb = by["drawer_front0"], by["towerback"]
    assert f[1] == pytest.approx(tb[1] + 0.002)
    assert f[1] + f[4] == pytest.approx(tb[1] + tb[4] - 0.002)


def test_a_typo_in_a_slat_design_block_FAILS_LOUD():
    """Review 2026-07-16: the slat overrides guarded only truthiness, so a metre/mm slip
    (slat_face_mm=0.04 -> 42k slivers), a sign-flip (-40), or an extra zero (4000) rendered wrong
    geometry or a silent box. An implausible value must RAISE — same discipline as normalize_face."""
    good = dict(slat_face_mm=40, slat_gap_mm=20, slat_depth_mm=22)
    assert M.millwork_parts("headboard", 0.100, 2.540, 2.800, "x", -1, design=good), "the signed values still build"
    for bad in (dict(slat_face_mm=0.04), dict(slat_gap_mm=-20), dict(slat_face_mm=4000),
                dict(slat_depth_mm=0), dict(slat_face_mm="oops")):
        with pytest.raises((ValueError, TypeError)):
            M.millwork_parts("headboard", 0.100, 2.540, 2.800, "x", -1, design=bad)


def test_a_tiny_open_run_falls_back_to_a_box():
    """Too short a RUN to seat even the gables -> return [] and the caller keeps the plain box,
    never a pile of degenerate slivers. (axis 'x' => the run is the D dimension, so D is the tiny
    one here.)"""
    assert M.millwork_parts("wardrobe", 0.600, 0.040, 2.800, "x", -1, open_front=True) == []


# ---- the low run --------------------------------------------------------------------------------
def test_desk_gets_an_overhanging_worktop():
    parts, _, _, _ = _parts(BF11)
    names = [p[0] for p in parts]
    assert names == ["top", "carcass"]
    top = next(p for p in parts if p[0] == "top")
    carc = next(p for p in parts if p[0] == "carcass")
    assert top[3] + top[6] == pytest.approx(BF11["H"]), "the worktop is the top of the piece"
    assert top[6] == pytest.approx(M.TOP_T)
    # the carcass is set back under the lip -> a shadow under the worktop
    assert carc[4] < top[4], "carcass must be shallower than the worktop (X is the depth axis here)"


# ---- shapes that are NOT millwork ---------------------------------------------------------------
@pytest.mark.parametrize("kind", sorted(M.PANEL_KINDS))
@pytest.mark.parametrize("H,mount", [(0.800, False), (0.800, True), (2.000, True)])
def test_a_wall_panel_stays_a_FLUSH_box(kind, H, mount):
    """CAUGHT IN REVIEW — a regression I shipped. Every built-in was routed through the generator
    with no kind screen, so `specs/living_room`'s 1400 x 100 mm wall TV took the LOW-RUN branch: it
    came out capped by a 40 mm worktop lip with its SCREEN set 30 mm BEHIND the plan face. The clay
    is the beauty pass's structural control, so that teaches the repaint a floating shelf where the
    plan says a television. A panel's face IS the plan face: return [] and keep the flush box."""
    assert M.millwork_parts(kind, 1.400, 0.100, H, "y", -1, floor_standing=mount) == []


def test_a_wall_hung_LOW_piece_has_nothing_to_overhang():
    """A floating shelf has no worktop lip and no toe-kick — but a wall-hung TALL cabinet is real
    joinery and KEEPS its leaves (it just loses the plinth: no floor to kick)."""
    assert M.millwork_parts("cabinet", 1.2, 0.35, 0.40, "y", -1, floor_standing=False) == []
    tall = M.millwork_parts("cabinet", 1.2, 0.35, 2.20, "y", -1, floor_standing=False)
    assert any(p[0].startswith("door") for p in tall) and not any(p[0] == "plinth" for p in tall)


# ---- an owner's declaration must be READ, not silently dropped -----------------------------------
@pytest.mark.parametrize("raw,want", [("S", "S"), ("s", "S"), (" south ", "S"), ("South", "S"),
                                      ("EAST", "E"), ("w", "W"), ("N", "N"), (None, None), ("", None)])
def test_a_face_declaration_is_normalized(raw, want):
    assert M.normalize_face(raw) == want


def test_an_unreadable_face_RAISES_instead_of_quietly_becoming_a_guess():
    """CAUGHT IN REVIEW. An exact-string match meant 'south' fell through to the heuristic — and
    build_room would then print "declare a `face`" at an owner who had just declared one. Silently
    demoting a signature to a guess is the exact failure the two-layer law exists to prevent."""
    for bad in ("SW", "front", "left", "0"):
        with pytest.raises(ValueError):
            M.normalize_face(bad)


def test_a_declaration_that_opens_the_run_from_its_END_is_flagged_not_hidden():
    """The owner still WINS — we never override a signature. But 'face E' on a 3.3 m x 0.6 m wardrobe
    means opening it from the 600 mm end, and that must be SAID, not silently built."""
    ax, sg, src = M.mill_axis(BF09_3["x"], BF09_3["y"], BF09_3["W"], BF09_3["D"],
                              ROOM_CTR, ITEMS, face="E")
    assert (ax, sg) == ("x", 1), "the owner's face is still authoritative"
    assert src == "declared-cross-run", "...and the caller is told to confirm it"
    # a sane declaration on the same piece stays plain 'declared'
    assert M.mill_axis(BF09_3["x"], BF09_3["y"], BF09_3["W"], BF09_3["D"],
                       ROOM_CTR, ITEMS, face="S")[2] == "declared"


def test_a_squat_block_is_left_alone():
    """We do not pretend a chunky block has door leaves."""
    axis, sign, src = M.mill_axis(0, 0, 1.0, 0.9, ROOM_CTR, ITEMS)     # ratio 1.11 < RUN_RATIO
    assert (axis, sign, src) == (None, 0, None)


def test_degenerate_bbox_is_left_alone():
    assert M.mill_axis(0, 0, 0.0, 1.0, ROOM_CTR, ITEMS) == (None, 0, None)
    assert M.millwork_parts("wardrobe", 0.0, 1.0, 2.8, "y", 1) == []


# ---- units: this module is METRES, furniture.py next door is INCHES -----------------------------
def test_constants_are_metres_not_inches():
    """A pasted inch constant would sail through every geometric test above and only show up as a
    wardrobe with 14-inch-thick doors. Pin the magnitude."""
    for nm in ("T_DOOR", "REVEAL", "PLINTH_H", "PLINTH_R", "PULL_H", "SLAT_W", "SLAT_GAP",
               "SLAT_PR", "TOP_T", "TOP_REC"):
        v = getattr(M, nm)
        assert 0.001 <= v <= 0.15, f"{nm}={v} is not a plausible METRE-scale joinery dimension"
    assert 0.3 <= M.LEAF_W <= 0.9, "a door leaf is ~450-600 mm"


# ================================================================================================
# THE MODEL-FIT GATE
# ================================================================================================
# Native post-import bboxes, MEASURED in Blender 5.1 (headless bpy, exactly what place_model sees).
# Not from a spec sheet, not from a model page — from the mesh. Pin them: if a re-download changes
# a bbox, these tests must fail loudly rather than a render quietly changing.
NATIVE = {
    "coffee_table_round_01":   (1.301, 1.301, 0.491),
    "Ottoman_01":              (0.885, 0.621, 0.624),
    "modern_arm_chair_01":     (0.820, 0.987, 1.023),
    "sofa_02":                 (1.807, 0.818, 0.709),
    "ClassicNightstand_01":    (0.568, 0.424, 0.700),
    "ArmChair_01":             (0.848, 0.766, 1.065),
    "Sofa_01":                 (1.572, 0.658, 0.796),
}


def test_the_pancake_side_tables_are_refused():
    """THE LIVE BUG THIS GATE FOUND (2026-07-12, present in the judged 3.5/5 renders).
    MODEL_MAP sends `side_table` -> `coffee_table_round_01`, a 1301 mm round COFFEE table. Uniformly
    fitted into a 300 x 300 mm bedside slot it scales to 0.23 and renders 113 mm TALL — an
    ankle-high saucer beside a 600 mm bed. The pro critic wrote "the floating nightstands are
    overly simplistic geometric primitives": they were never primitives, they were a real mesh
    squashed to a pancake. Same failure in every room (111-226 mm across bedroom/living/sitting)."""
    for slot, want_h in [((0.300, 0.300, 0.520), 113), ((0.350, 0.350, 0.450), 132),
                         ((0.600, 0.600, 0.450), 226)]:
        s, ok, why = M.model_fit(*NATIVE["coffee_table_round_01"], *slot)
        assert not ok and "height" in why
        assert round(NATIVE["coffee_table_round_01"][2] * s * 1000) == want_h, why


def test_the_ottoman_blob_would_be_refused():
    """The 885 x 621 mm ottoman fitted into a 504 x 1002 mm foot-of-bed slot fills 35% of the
    footprint — the "dark leather blob" the pro critic scored as "a simple box shape on legs" in
    MasterSuite v01/v03. A SCALE bug, never a mesh-quality bug.

    HONESTY, caught in review: this gate is NOT what stops the ottoman today. `kind == "bench"` is
    intercepted into `_build_bench` BEFORE MODEL_MAP is consulted (build_room's item loop), so the
    mesh has not been placed since 2026-07-11 — and the now-dead `MODEL_MAP["bench"]` entry has been
    removed. This stays as a unit test of model_fit's ARITHMETIC on the historic case, not as a
    claim about the live render path. Do not quote it as "the gate fixed the blob"."""
    s, ok, why = M.model_fit(*NATIVE["Ottoman_01"], 0.504, 1.002, 0.450)
    assert not ok and "aspect" in why
    assert s == pytest.approx(0.504 / 0.885, rel=1e-6)


def test_the_decor_plant_pancake_is_refused_too():
    """Same bug, third lane: `calathea_orbifolia_01` is a 2492 x 1194 mm FLOOR plant, and
    _dress_scene was dropping it into a 220 mm TABLETOP slot -> a 37 mm-tall green smear. The gate
    refuses it; build_room now draws a procedural pot instead of silently losing the styling cue
    (styling_and_life is a scored axis — a decor piece must never just vanish because a gate said
    no). Caught in review: the reject path had no fallback at all."""
    s, ok, why = M.model_fit(2.492, 1.194, 0.424, 0.22, 0.22, 0.30)
    assert not ok and "aspect" in why
    assert round(0.424 * s * 1000) == 37, "it used to render 37 mm tall"


@pytest.mark.parametrize("slug,slot", [
    ("modern_arm_chair_01", (0.510, 0.546, 0.750)),   # master bedroom, at the desk
    ("modern_arm_chair_01", (0.750, 0.750, 0.750)),   # living room
    ("sofa_02",             (1.900, 0.950, 0.800)),   # living room
    ("sofa_02",             (2.202, 1.008, 0.800)),   # sitting room
    ("coffee_table_round_01", (1.000, 1.000, 0.450)),  # living room COFFEE table (its real job)
    ("coffee_table_round_01", (0.700, 0.700, 0.400)),  # specs/sitting_room — THE KNIFE EDGE, below
    ("ClassicNightstand_01",  (0.400, 0.380, 0.520)),  # a real nightstand slot
])
def test_the_gate_does_not_regress_what_already_renders(slug, slot):
    """A gate that refuses good meshes is worse than no gate. Every model/slot pair that renders
    acceptably today must still PASS — the gate only removes the pancakes."""
    _, ok, why = M.model_fit(*NATIVE[slug], *slot)
    assert ok, f"{slug} into {slot} must still pass, got: {why}"


def test_the_one_knife_edge_pair_in_the_corpus_is_pinned():
    """Found in review: specs/sitting_room's 700x700x400 coffee_table clears H_LO by ONE PERCENT
    (h_ratio 0.6605 vs the 0.65 floor). It is the only pair in the whole corpus that would flip on
    a small threshold nudge, so it is pinned here — nudge H_LO to 0.67 'for cleanliness' and a real,
    currently-fine coffee table silently becomes a primitive. That is what this test is for."""
    s, ok, _ = M.model_fit(*NATIVE["coffee_table_round_01"], 0.700, 0.700, 0.400)
    h_ratio = NATIVE["coffee_table_round_01"][2] * s / 0.400
    assert ok
    assert h_ratio == pytest.approx(0.6605, abs=5e-4)
    assert h_ratio - M.H_LO < 0.02, "if this margin ever grows, someone moved the threshold"


def test_a_mesh_that_matches_its_slot_passes():
    s, ok, why = M.model_fit(0.500, 0.450, 0.600, 0.500, 0.450, 0.600)
    assert ok and s == pytest.approx(1.0) and why.startswith("ok at scale 1.000")


def test_a_mesh_too_tall_for_its_slot_is_refused():
    """Same footprint, wrong height class — a bar stool in a side-table slot."""
    _, ok, why = M.model_fit(0.500, 0.500, 1.500, 0.500, 0.500, 0.600)
    assert not ok and "height" in why


def test_the_gate_takes_no_rot_because_the_slot_is_already_local():
    """The gate takes NO rot, and the reason is a SCHEMA fact, not a caution: a spec item's w/d are
    the piece's OWN LOCAL un-rotated dims (`gen_floor2_v4_specs.to_spec` PRE-SWAPS them for a
    cardinal quarter-turn so the renderer's fit-then-rotate lands the world AABB back on the drawn
    bbox). So the slot a mesh must fit IS the unrotated (w, d). Swapping the target axes here would
    DOUBLE-APPLY the generator's pre-swap and start rejecting correctly-placed furniture.

    (An earlier docstring justified this by claiming build_room had "two contradictory angle
    conventions". That was WRONG and is retracted — there is exactly one. See
    test_facing_convention.py.)"""
    import inspect
    # The two slot arguments are KEYWORD-ONLY-by-position and carry no geometry: they
    # answer "is this the right kind of object", which no rotation convention affects.
    assert list(inspect.signature(M.model_fit).parameters) == [
        "mw", "md", "mh", "w", "d", "h", "model_slot", "item_slot"]


def test_degenerate_mesh_is_refused_not_divided_by_zero():
    for args in [(0, 1, 1, 1, 1, 1), (1, 0, 1, 1, 1, 1), (1, 1, 0, 1, 1, 1),
                 (1, 1, 1, 0, 1, 1), (1, 1, 1, 1, 0, 1), (1, 1, 1, 1, 1, 0)]:
        s, ok, why = M.model_fit(*args)
        assert not ok and s == 0.0 and "degenerate" in why


def test_the_gate_never_lets_a_mesh_exceed_its_plan_footprint():
    """Whatever it accepts, the scaled mesh must fit INSIDE the slot — the CAD invariant again,
    this time for imported geometry."""
    import itertools
    for mw, md, mh, w, d, h in itertools.product(
            (0.3, 1.0, 2.1), (0.4, 0.9), (0.4, 1.8), (0.5, 1.2), (0.6, 2.0), (0.5, 2.4)):
        s, ok, _ = M.model_fit(mw, md, mh, w, d, h)
        if not ok:
            continue
        assert mw * s <= w + 1e-9, f"scaled mesh {mw*s} exceeds slot {w}"
        assert md * s <= d + 1e-9, f"scaled mesh {md*s} exceeds slot {d}"


# ---------------------------------------------------------------------------
# ELEMENT 2 — west wall: OPEN display bookshelf + LOW makeup vanity (2026-07-17)
# ink-trued footprints (mm -> m); both face EAST into the room (depth axis x, sign +1).
# ---------------------------------------------------------------------------
BOOKSHELF = dict(kind="bookshelf", W=0.600, D=1.800, H=1.800)   # freestanding open grid, tall
VANITY    = dict(kind="vanity",    W=0.498, D=3.199, H=0.750)   # low seated makeup vanity


def _e2(b, design=None):
    return M.millwork_parts(b["kind"], b["W"], b["D"], b["H"], "x", 1, design=design)


def _inside(parts, W, D, H):
    for nm, x, y, z, dx, dy, dz in parts:
        assert -1e-9 <= x and x + dx <= W + 1e-9, f"{nm} x out of bbox"
        assert -1e-9 <= y and y + dy <= D + 1e-9, f"{nm} y out of bbox"
        assert -1e-9 <= z and z + dz <= H + 1e-9, f"{nm} z out of bbox"


def test_bookshelf_is_an_open_grid_not_a_closed_door_run():
    """h1800 >= TALL_H would otherwise build door leaves; the bookshelf branch must intercept and
    emit an OPEN grid: oak shelves + cool verticals, and (decision B) NO back panel."""
    parts = _e2(BOOKSHELF)
    names = [p[0] for p in parts]
    assert parts, "bookshelf produced no parts"
    assert not any(n.startswith(("door", "carcass", "plinth")) for n in names), \
        "an open bookshelf must NOT get closed door leaves / a set-back carcass"
    assert not any(n.startswith("back") for n in names), "decision B: NO back panel (see-through)"
    assert any(n.startswith("shelf") for n in names), "no oak shelf boards"
    assert any(n.startswith("cool_vert") for n in names), "no cool gables/dividers"
    _inside(parts, **{"W": 0.600, "D": 1.800, "H": 1.800})


def test_bookshelf_bays_never_exceed_the_open_shelf_load_span():
    """Every open-shelf bay span (a shelf's along-run length) must stay <= MAX_SPAN, or the shelf
    sags. The divider count is derived, not hardcoded — this is the assert that catches a regression
    if the derivation changes."""
    for run in (1.2, 1.8, 2.4, 3.0):
        parts = M.millwork_parts("bookshelf", 0.600, run, 1.800, "x", 1)
        shelf_spans = [p[5] for p in parts if p[0].startswith("shelf")]   # dy = along-run length
        assert shelf_spans, f"run {run}: no shelves"
        assert max(shelf_spans) <= M.MAX_SPAN + 1e-6, \
            f"run {run}: a bay span {max(shelf_spans):.3f} exceeds MAX_SPAN {M.MAX_SPAN}"


def test_vanity_has_a_kneehole_between_two_drawer_banks():
    """The LOW vanity must read as a seated makeup station: a counter over two drawer banks that
    FLANK an open kneehole the seat pulls into (not a solid sideboard)."""
    parts = _e2(VANITY)
    assert any(p[0] == "counter" for p in parts), "no Caesarstone counter"
    bodies = [p for p in parts if p[0].startswith("cool_body")]
    assert len(bodies) == 2, f"expected two flanking drawer banks, got {len(bodies)}"
    spans = sorted((p[2], p[2] + p[5]) for p in bodies)   # along_off..+along_len along the run
    gap = spans[1][0] - spans[0][1]                        # the kneehole void between them
    assert gap > 0.5, f"kneehole gap {gap:.3f} m too small — the seat must fit"
    assert any("drawer_front" in p[0] for p in parts), "no drawer fronts under the counter"
    _inside(parts, 0.498, 3.199, 0.750)


def test_vanity_counter_spans_the_full_run_over_the_kneehole():
    """Knees go UNDER the counter in the kneehole, so the counter must span the whole run and sit at
    the top of the low box."""
    parts = _e2(VANITY)
    c = next(p for p in parts if p[0] == "counter")
    assert abs(c[5] - VANITY["D"]) < 1e-6, "counter must span the full run (knees pass under it)"
    assert c[3] > VANITY["H"] * 0.5 and c[3] + c[6] <= VANITY["H"] + 1e-9, \
        "counter must sit at the top of the low vanity"


def test_kneehole_width_is_design_driven_not_hardcoded():
    d = {"element": 2, "kneehole_width_m": 1.40, "kneehole_center_frac": 0.5155}
    parts = _e2(VANITY, design=d)
    bodies = sorted((p[2], p[2] + p[5]) for p in parts if p[0].startswith("cool_body"))
    kh = bodies[1][0] - bodies[0][1]
    assert abs(kh - 1.40) < 0.02, f"kneehole {kh:.3f} should follow the design value 1.40"


def test_canonical_spec_west_wall_builds_element2_joinery():
    """The file build_room consumes: its bookshelf + BF11 vanity builtins must build their element-2
    branches (a stale spec that reverts to a plain box would pass a fixture test but fail here)."""
    import json, os
    p = os.path.join(os.path.dirname(__file__), "..", "..", "projects",
                     "PRJ-2026-002_c001-house", "03_layout", "master-suite.CANONICAL.spec.json")
    with open(p, encoding="utf-8") as fh:
        spec = json.load(fh)
    book = next(b for b in spec["builtins"] if b["kind"] == "bookshelf")
    van = next(b for b in spec["builtins"] if b["kind"] == "vanity")
    bp = M.millwork_parts("bookshelf", book["w"] / 1000, book["d"] / 1000, book["h"] / 1000,
                          "x", 1, design=book.get("design"))
    vp = M.millwork_parts("vanity", van["w"] / 1000, van["d"] / 1000, van["h"] / 1000,
                          "x", 1, design=van.get("design"))
    assert any(p[0].startswith("shelf") for p in bp) and any(p[0].startswith("cool_vert") for p in bp)
    assert any(p[0] == "counter" for p in vp)
    assert sum(1 for p in vp if p[0].startswith("cool_body")) == 2
    _inside(bp, book["w"] / 1000, book["d"] / 1000, book["h"] / 1000)
    _inside(vp, van["w"] / 1000, van["d"] / 1000, van["h"] / 1000)


def test_vanity_mirror_box_resolves_well_formed_from_the_canonical_spec():
    """The frameless mirror is a DECIDED element (D2-3). A spec edit that drops/mistypes its block
    silently renders no mirror (build_room returns 0 at exit 0), so THIS test — not the render — is
    the omission guard. Also pins the review fix: field height ~700 (ergonomic 610-762) + centre
    ~1200 AFF, NOT the kneehole's 900/1250 the placeholder had copied."""
    import json, os
    p = os.path.join(os.path.dirname(__file__), "..", "..", "projects",
                     "PRJ-2026-002_c001-house", "03_layout", "master-suite.CANONICAL.spec.json")
    with open(p, encoding="utf-8") as fh:
        spec = json.load(fh)
    box = M.vanity_mirror_box(spec)
    assert box is not None, "the canonical BF11 vanity must carry a frameless mirror (D2-3)"
    name, x_mm, y_mm, sill_mm, w_mm, d_mm, h_mm = box
    assert name.endswith("__mirror")
    assert 610 <= h_mm <= 762, f"mirror field height {h_mm} must sit in the ergonomic 610-762"
    assert 1120 <= sill_mm + h_mm / 2 <= 1267, \
        f"mirror centre {sill_mm + h_mm/2} must be at the seated eye level 1120-1267"


def test_vanity_mirror_box_is_opt_in_and_fails_loud():
    assert M.vanity_mirror_box({"builtins": [{"kind": "vanity", "design": {"element": 2}}]}) is None
    assert M.vanity_mirror_box({"builtins": []}) is None
    assert M.vanity_mirror_box({}) is None
    for bad in ({"x_mm": 0},   # missing keys
                {"x_mm": 0, "y_mm": 1, "sill_mm": 1, "w_mm": 1, "d_mm": 1, "h_mm": -5}):  # non-positive
        with pytest.raises(ValueError):
            M.vanity_mirror_box({"builtins": [{"kind": "vanity", "design": {"mirror": bad}}]})


def test_vanity_kneehole_fails_loud_on_implausible_values():
    """The vanity branch must RAISE on a metre/mm slip (1400 vs 1.40) or a frac-vs-mm confusion
    (3549 vs 0.51), like the headboard branch does — not silently build a seat-less sideboard or a
    counter floating with no drawer banks (review 2026-07-17)."""
    for bad in ({"kneehole_width_m": 1400},                 # mm-as-metres slip
                {"kneehole_width_m": VANITY["D"] + 0.1},    # wider than the run
                {"kneehole_width_m": -0.5},                 # sign flip
                {"kneehole_center_frac": 3549},             # mm-as-fraction slip
                {"kneehole_center_frac": 1.6}):             # off-run centre
        with pytest.raises(ValueError):
            M.millwork_parts("vanity", VANITY["W"], VANITY["D"], VANITY["H"], "x", 1,
                             design={"element": 2, **bad})
    # the shipped canonical values still build (no false positive)
    ok = M.millwork_parts("vanity", VANITY["W"], VANITY["D"], VANITY["H"], "x", 1,
                          design={"element": 2, "kneehole_width_m": 1.40, "kneehole_center_frac": 0.5155})
    assert any(p[0] == "counter" for p in ok)


# --- ELEMENT 3: bedside nightstand + dome lamp (nightstand_lamp_parts) ----------------------------
# The real PRJ-2026-002 nightstands: ink ~501x498/501 mm, h520, a brass dome lamp on top.
NS = dict(w_m=0.501, d_m=0.498, h_m=0.520)


def test_nightstand_cabinet_is_joinery_not_a_sealed_box():
    """ROUND-6 LANE C (C2#7): the solid block became toe + carcass + drawer face —
    three shadow lines — while KEEPING the old invariants: the mass still rises from
    the floor to h, nothing leaves the footprint, and the only air is the one reveal.
    (This test supersedes test_nightstand_body_fills_the_whole_footprint_from_the_floor;
    the verdict + triage live in verdict-round6-2026-07-30.md.)"""
    parts = M.nightstand_lamp_parts(**NS)
    cab = {p[0]: p for p in parts if not p[0].startswith("lamp_")}
    assert set(cab) == {"toe", "body", "drawer"}
    _, ox, oy, oz, dx, dy, dz = cab["toe"]
    assert oz == 0.0 and ox == oy == M.NS_TOE_R > 0, "toe sits on the floor, set back"
    assert dx == NS["w_m"] - 2 * M.NS_TOE_R and dy == NS["d_m"] - 2 * M.NS_TOE_R
    _, bx, by, bz, bdx, bdy, bdz = cab["body"]
    assert (bx, by) == (0.0, 0.0) and (bdx, bdy) == (NS["w_m"], NS["d_m"])
    assert abs(bz - M.NS_TOE_H) < 1e-9, "carcass starts where the toe ends (no gap)"
    _, qx, qy, qz, qdx, qdy, qdz = cab["drawer"]
    assert (qx, qy) == (0.0, 0.0) and (qdx, qdy) == (NS["w_m"], NS["d_m"])
    assert abs(qz + qdz - NS["h_m"]) < 1e-9, "drawer face tops out exactly at h"
    assert abs(qz - (bz + bdz) - M.NS_REV) < 1e-9, "exactly ONE reveal, the declared width"


def test_nightstand_too_small_for_joinery_stays_one_solid_body():
    """Degenerate -> FEWER parts, never a part outside the footprint (the module law)."""
    parts = M.nightstand_lamp_parts(0.1, 0.1, 0.15, lamp=False)
    assert [p[0] for p in parts] == ["body"]
    assert parts[0][1:] == (0.0, 0.0, 0.0, 0.1, 0.1, 0.15)


def test_nightstand_lamp_sits_on_top_and_inside_the_footprint():
    parts = M.nightstand_lamp_parts(**NS)
    lamp = [p for p in parts if p[0].startswith("lamp_")]
    assert {p[0] for p in lamp} == {"lamp_base", "lamp_stem", "lamp_shade"}, "brass base+stem+dome shade"
    for name, ox, oy, oz, dx, dy, dz in lamp:
        assert oz >= NS["h_m"] - 1e-9, f"{name} must sit ON TOP of the cabinet (z>=H)"
        assert ox >= -1e-9 and ox + dx <= NS["w_m"] + 1e-9, f"{name} overhangs in x (a render lie)"
        assert oy >= -1e-9 and oy + dy <= NS["d_m"] + 1e-9, f"{name} overhangs in y (a render lie)"
    shade = next(p for p in lamp if p[0] == "lamp_shade")
    base = next(p for p in lamp if p[0] == "lamp_base")
    assert shade[6] > 0 and shade[3] > base[3], "the dome shade must be wider than the brass base"


def test_nightstand_lamp_opt_out():
    parts = M.nightstand_lamp_parts(0.5, 0.5, 0.5, lamp=False)
    assert [p[0] for p in parts] == ["toe", "body", "drawer"], \
        "lamp=False yields just the cabinet (its three joinery parts)"


def test_nightstand_lamp_never_overhangs_for_any_aspect_ratio():
    # containment is a sizing invariant (EVERY lamp part's half-width scales with min(w,d): base
    # 0.17, stem 0.028, shade 0.34 — all <= 0.5*min <= half of either axis), not a runtime guard.
    # Includes TINY dims (0.02) that a fixed-width stem used to overhang — the regime the earlier
    # test never reached (review 2026-07-18).
    for w, d in ((0.5, 0.5), (0.9, 0.3), (0.3, 0.9), (1.2, 0.15), (0.15, 1.2),
                 (0.02, 0.5), (0.5, 0.02), (0.001, 0.001)):
        for name, ox, oy, oz, dx, dy, dz in M.nightstand_lamp_parts(w, d, 0.5):
            assert -1e-9 <= ox and ox + dx <= w + 1e-9, f"{name} overhangs x at {w}x{d}"
            assert -1e-9 <= oy and oy + dy <= d + 1e-9, f"{name} overhangs y at {w}x{d}"


def test_nightstand_fails_loud_on_non_positive_dims():
    for bad in (dict(w_m=0, d_m=0.5, h_m=0.5), dict(w_m=0.5, d_m=-0.1, h_m=0.5),
                dict(w_m=0.5, d_m=0.5, h_m=0.0)):
        with pytest.raises(ValueError):
            M.nightstand_lamp_parts(**bad)


# ---------------------------------------------------------------- tub chair (element-2 seat)

def _lay(rot=270.0, w=0.510, d=0.546, h=0.750):
    return M.tub_chair_curved(w, d, h, rot_deg=rot)


def test_tub_chair_inscribed_and_centred():
    """The wrap circle inscribes min(w,d), centred — nothing leaves the footprint."""
    w, d = 0.510, 0.546
    lay = _lay()
    assert lay["R"] * 2 <= min(w, d)
    assert abs(lay["cx"] - w / 2) < 1e-9 and abs(lay["cy"] - d / 2) < 1e-9
    for lg in lay["legs"]:
        assert (lg["x"] ** 2 + lg["y"] ** 2) ** 0.5 + lg["r_top"] <= lay["R"] + 1e-9


def test_tub_chair_rim_seat_heights():
    lay = M.tub_chair_curved(0.510, 0.546, 0.750, seat_h_m=0.41, rot_deg=270)
    sh = lay["shell"]
    # SWEPT rim (owner 2026-07-22): tall back = h, low arms above the seat but below the back
    assert abs(sh["z1_back"] - 0.750) < 1e-9               # the backrest = the label rim height
    assert lay["seat"]["z0"] < sh["z1_arm"] < sh["z1_back"]  # arms sit between seat and back
    assert sh["z1_arm"] > 0.41                             # the arms clear the seat (a hand-rest)
    assert abs(lay["seat"]["z1"] - 0.41) < 1e-9            # seat = pass-through, not a frozen [est]
    assert lay["seat"]["dome_z"] > lay["seat"]["z1"]       # the cushion is PROUD (a pad, not a disc)
    assert lay["seat"]["dome_z"] < sh["z1_arm"]            # but nestles below the arm rim
    assert lay["seat"]["r"] < sh["r_in"]                   # cushion sits inside the wrap


def test_tub_chair_opening_faces_front_any_rot():
    """THE ONE FACING CONVENTION: front azimuth = rot-90 deg; the opening's centre must
    aim there for cardinal AND non-cardinal rots (the curve killed the cardinal limit)."""
    for rot in (0.0, 90.0, 270.0, 45.0, 213.0):
        lay = _lay(rot=rot)
        th0, th1 = lay["shell"]["th0"], lay["shell"]["th1"]
        opening_centre = (th1 + th0) / 2 + math.pi        # opposite the wrap centre
        want = math.radians(rot - 90.0)
        diff = (opening_centre - want) % (2 * math.pi)
        assert min(diff, 2 * math.pi - diff) < 1e-6, rot


def test_tub_chair_legs_under_the_wrap_not_the_opening():
    lay = _lay(rot=270.0)
    th0, th1 = lay["shell"]["th0"], lay["shell"]["th1"]
    for lg in lay["legs"]:
        a = math.atan2(lg["y"], lg["x"]) % (2 * math.pi)
        rel = (a - th0) % (2 * math.pi)
        assert rel <= (th1 - th0) + 1e-9                   # every leg inside the wrap arc


def test_open_front_niche_mirror_opt_in():
    """THE DRESSING GALLERY (2026-07-22): open_front gains niche_mirror — default OFF is
    byte-identical (BF09-3 never sees it), ON adds exactly one 'niche_mirror' part at the
    niche back, full-height."""
    base = M.millwork_parts("wardrobe", 0.6, 3.4, 2.8, "x", -1, open_front=True)
    withm = M.millwork_parts("wardrobe", 0.6, 3.4, 2.8, "x", -1, open_front=True,
                             niche_mirror=True)
    assert not any("mirror" in p[0] for p in base)             # default off = no mirror
    mir = [p for p in withm if "mirror" in p[0]]
    assert len(mir) == 1 and mir[0][6] > 2.0                   # one, full-height (dz)
    # the mirror is the ONLY difference (same part count + 1)
    assert len(withm) == len(base) + 1


def test_tub_chair_fail_loud():
    with pytest.raises(ValueError):
        M.tub_chair_curved(0.5, 0.5, 0.75, seat_h_m=0.8)   # seat above rim
    with pytest.raises(ValueError):
        M.tub_chair_curved(-0.5, 0.5, 0.75)                # negative dim
    with pytest.raises(ValueError):
        M.tub_chair_curved(0.5, 0.5, 0.75, opening_deg=200)  # not a tub


# --- the class gate (2026-08-10) --------------------------------------------------
# `model_fit` took six numbers and no class, so a bounding box was the only thing
# standing between the acquire path and an armchair in a nightstand slot. Measured on
# the live shelf against this room's own slots, all three of these were a FIT:
# ArmChair_01 -> side_table at 0.591, Ottoman_01 -> side_table at 0.566,
# coffee_table_round_01 -> bed base at 1.537. The class was in CATALOG.json the whole
# time and nothing read it.

def test_an_armchair_is_refused_for_a_nightstand_slot_at_any_scale():
    s, ok, why = M.model_fit(*NATIVE["ArmChair_01"], 0.501, 0.498, 0.520)
    assert ok, "the geometric fit is what made this dangerous — it passes"
    s, ok, why = M.model_fit(*NATIVE["ArmChair_01"], 0.501, 0.498, 0.520,
                             model_slot="seating", item_slot="case")
    assert not ok and "class mismatch" in why and "No scale" in why


def test_a_coffee_table_is_refused_for_the_bed_slot():
    _, ok, _ = M.model_fit(*NATIVE["coffee_table_round_01"], 2.000, 2.149, 0.600)
    assert ok
    _, ok, why = M.model_fit(*NATIVE["coffee_table_round_01"], 2.000, 2.149, 0.600,
                             model_slot="case", item_slot="bed")
    assert not ok and "class mismatch" in why


def test_the_right_class_still_fits_and_the_scale_is_reported():
    s, ok, why = M.model_fit(*NATIVE["ClassicNightstand_01"], 0.501, 0.498, 0.520,
                             model_slot="case", item_slot="case")
    assert ok and f"{s:.3f}" in why and "case" in why


def test_an_unresolved_class_is_reported_never_assumed_to_match():
    """'Could not look' must not read like 'looked and it matched'. The geometric
    verdict stands, and the reason says the class was not checked."""
    for ms, isl in (("seating", None), (None, "case"), (None, None)):
        s, ok, why = M.model_fit(*NATIVE["ClassicNightstand_01"], 0.501, 0.498, 0.520,
                                 model_slot=ms, item_slot=isl)
        assert ok and "CLASS NOT CHECKED" in why


def test_the_class_check_runs_before_the_geometry():
    """A wrong-class mesh must be refused by NAME, not incidentally by aspect — the
    reject line is a SOURCING signal and it has to say the right thing."""
    _, ok, why = M.model_fit(*NATIVE["Sofa_01"], 0.501, 0.498, 0.520,
                             model_slot="seating", item_slot="case")
    assert not ok and "class mismatch" in why and "aspect" not in why
