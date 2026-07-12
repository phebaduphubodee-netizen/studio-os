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
    assert ok and why == "ok" and s == pytest.approx(1.0)


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
    assert list(inspect.signature(M.model_fit).parameters) == ["mw", "md", "mh", "w", "d", "h"]


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
