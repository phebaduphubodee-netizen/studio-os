"""
test_facing_convention.py — PIN THE ONE FACING CONVENTION.

2026-07-12. This suite exists because the convention was stated in five places, tested in none, and
I briefly convinced myself (wrongly) that two of those statements CONTRADICTED each other. They do
not. What was actually true is worse and quieter: `place_model` passed the RAW spec rot, which is
correct only while every mapped mesh's native front happens to be -Y — and half the models had no
declared native front at all (fail-open). Both are now closed, and pinned here.

THE CONVENTION
    spec rot -> FRONT points (sin rot, -cos rot).  rot 0 = -Y = SOUTH; rot rotates CCW about +Z.
    front azimuth (deg, +X=0, +Y=90) = rot - 90.       BACK/head = -front.

THE LAW
    place_model.rot = (desired world FRONT azimuth) - MODEL_FRONT_DEG[slug]
                    = spec_rot - 90 - MODEL_FRONT_DEG[slug]

build_room imports bpy, so we stub it: nothing at module scope calls into Blender.
Run:  python -m pytest pipeline/scripts/test_facing_convention.py -q
"""
import math
import sys
import types

import pytest

if "bpy" not in sys.modules:                    # module-scope import only; no Blender needed
    _stub = types.ModuleType("bpy")
    _stub.data = types.SimpleNamespace()
    _stub.ops = types.SimpleNamespace()
    _stub.context = types.SimpleNamespace()
    sys.modules["bpy"] = _stub

import build_room as BR
import facing_reader
import placement_logic


CARDINALS = [(0, "S", (0, -1)), (90, "E", (1, 0)), (180, "N", (0, 1)), (270, "W", (-1, 0))]


# ---- the convention itself: five modules, one meaning -------------------------------------------
@pytest.mark.parametrize("rot,letter,front", CARDINALS)
def test_every_module_agrees_on_what_rot_means(rot, letter, front):
    """facing_reader, placement_logic and _head_dir must all be the SAME convention. If this test
    ever fails, do not 'reconcile' them by adding an offset somewhere — find which one moved."""
    assert facing_reader._FACING[rot] == letter

    fx, fy = placement_logic._front_vec(rot)
    assert (round(fx), round(fy)) == front, "front = (sin rot, -cos rot)"

    # _head_dir spells the same convention on the BACK vector: head = -front
    axis, sign = BR._head_dir(rot)
    hx, hy = (sign, 0) if axis == "x" else (0, sign)
    assert (hx, hy) == (-front[0], -front[1]), "the head/back is the OPPOSITE of the front"


def test_the_owner_confirmed_v4_notes_are_both_satisfied():
    """The two owner-written notes in the shipped v4 spec are the acceptance test for the whole
    convention, and they look contradictory until you notice one is about a BACK and one a FRONT:
      bed      rot 270, "head EAST"   -> head = +X   (a sleeper faces the FOOT, i.e. WEST)
      armchair rot 270, "faces W"     -> front = -X
    Both must hold under ONE convention. They do."""
    axis, sign = BR._head_dir(270)
    assert (axis, sign) == ("x", 1), "bed rot 270 -> head EAST (matches the v4 bed note)"
    fx, fy = placement_logic._front_vec(270)
    assert (round(fx), round(fy)) == (-1, 0), "armchair rot 270 -> faces WEST (matches its note)"


@pytest.mark.parametrize("rot,letter,front", CARDINALS)
def test_front_azimuth_is_rot_minus_90(rot, letter, front):
    az = math.radians(rot - 90.0)
    assert (round(math.cos(az)), round(math.sin(az))) == front


# ---- MODEL_FRONT_DEG: measured, and complete ----------------------------------------------------
def test_every_mapped_model_declares_a_measured_native_front():
    """FAIL-OPEN, CLOSED. A MODEL_MAP slug with no MODEL_FRONT_DEG entry used to be handed the raw
    spec rot with its native front simply unknown — a silent, unbounded rotation error. (Three
    slugs were in that state: coffee_table_round_01, ClassicNightstand_01, Ottoman_01.)"""
    missing = set(BR.MODEL_MAP.values()) - set(BR.MODEL_FRONT_DEG)
    assert not missing, f"MODEL_MAP slugs with no measured native front: {missing}"


def test_all_native_fronts_are_minus_Y_as_measured():
    """MEASURED, not asserted: every mesh was imported headless and shot in orthographic elevation
    from the SOUTH; all nine presented their FRONT to that camera. Pin it — if a re-download or a
    new model changes this, the law below stops collapsing to the raw rot and THAT must be loud."""
    assert set(BR.MODEL_FRONT_DEG.values()) == {-90.0}


# ---- THE LAW -------------------------------------------------------------------------------------
@pytest.mark.parametrize("slug", sorted(set(v for v in [] ) | set(["sofa_02", "modern_arm_chair_01",
                                                                   "ClassicNightstand_01"])))
@pytest.mark.parametrize("rot", [0, 8, 90, 180, 225, 270, 332, 360])
def test_the_law_collapses_to_the_raw_spec_rot_today(slug, rot):
    """The behaviour-identity guarantee for the 2026-07-12 refactor: writing THE LAW into the plain
    path changed no pixel, because every native front is -90. This test is what makes that a fact
    rather than a hope — and it will FAIL the day someone adds a model that breaks the assumption,
    which is exactly when a human needs to look."""
    assert BR.model_rot(rot, slug) == pytest.approx(float(rot))


def test_the_law_actually_corrects_a_model_whose_front_is_not_minus_Y():
    """The point of writing the law down. A hypothetical mesh importing front-EAST (azimuth 0) must
    be rotated an extra -90 to satisfy the same spec rot."""
    BR.MODEL_FRONT_DEG["_probe_faces_east"] = 0.0
    try:
        assert BR.model_rot(0, "_probe_faces_east") == pytest.approx(-90.0)
        assert BR.model_rot(90, "_probe_faces_east") == pytest.approx(0.0)
        # sanity: a spec rot 90 means front EAST; a mesh already facing east needs no rotation. OK.
    finally:
        del BR.MODEL_FRONT_DEG["_probe_faces_east"]


def test_the_law_agrees_with_the_render_calibrated_autoface_anchor():
    """The auto-face branch ("fixes 'all chairs face the wrong way'") is the only rotation maths in
    this file that was ever calibrated against a real render, so it is ground truth. It computes
    `front_azimuth - MODEL_FRONT_DEG[slug]`. THE LAW must reduce to exactly that."""
    for slug in ("sofa_02", "modern_arm_chair_01"):
        for front_az in (-180, -90, 0, 37.5, 90, 180):
            spec_rot = front_az + 90.0                       # invert front_az = rot - 90
            anchor = front_az - BR.MODEL_FRONT_DEG[slug]     # what auto-face passes
            assert BR.model_rot(spec_rot, slug) == pytest.approx(anchor)


def test_an_unmapped_slug_defaults_to_the_measured_norm_not_to_zero():
    """Defaulting the native front to 0 would inject a silent 90 deg error on any slug that slipped
    past the completeness check. Default to the measured norm (-90) so the fallback is the truth."""
    assert BR.model_rot(123.0, "not_a_real_slug") == pytest.approx(123.0)


# ---- what the spec's w/d MEAN (the reason model_fit takes no rot) --------------------------------
def test_spec_wd_are_local_dims_so_the_fit_target_is_unrotated():
    """`gen_floor2_v4_specs.to_spec` PRE-SWAPS w/d for a cardinal quarter-turn, precisely so that the
    renderer's fit-then-rotate lands the world AABB back on the drawn cluster bbox. So a spec item's
    w/d are its OWN local dims, and millwork.model_fit must fit the UNROTATED (w, d) — swapping the
    axes there would double-apply the generator's pre-swap and reject correctly-placed furniture.

    Worked on the real v4 sitting-room sofa (rot 90 = faces EAST, spec 2202 x 1008):
      drawn cluster bbox  = 1008 EW x 2202 NS   (a 2.2 m sofa along the west wall, facing east)
      to_spec pre-swap    -> spec w=2202 (its LENGTH), d=1008 (its DEPTH)
      fit sofa_02 (1807 x 818) into 2202 x 1008 -> s = 1.219 -> 2202 x 997, front still -Y
      rotate 90 CCW about the footprint centre  -> 997 EW x 2202 NS, front now +X = EAST
    Final AABB == the drawn bbox. Nothing overflows; the fit-then-rotate order is CORRECT."""
    import millwork
    s, ok, _ = millwork.model_fit(1.807, 0.818, 0.709, 2.202, 1.008, 0.800)
    assert ok and s == pytest.approx(min(2.202 / 1.807, 1.008 / 0.818), rel=1e-9)
    length, depth = 1.807 * s, 0.818 * s                 # as fitted, un-rotated
    assert (round(length, 3), round(depth, 3)) == (2.202, 0.997)
    # after the 90 deg rotation the world AABB swaps back onto the drawn cluster
    assert (round(depth, 3), round(length, 3)) == (0.997, 2.202)
    import inspect
    assert "rot" not in inspect.signature(millwork.model_fit).parameters
