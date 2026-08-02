"""Tests for placement_check.py — the R9 guard.

Pure: no bpy, no .blend, no Blender. The fixtures reproduce the RELATIONSHIPS the
rules are about (a figure on a base, a plinth on a toe-kick, a ceiling on ten
walls), because those relationships are what the check reasons over and an AABB
dump is the only thing it ever sees.

Every scope rule below has a NEGATIVE control beside it. Three of the four scope
corrections in this file's history were found by the check convicting correct
construction, so a rule with no negative control here is a rule that has not been
shown to discriminate.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement_check as P                             # noqa: E402


def ob(name, x, y, z, w=100.0, d=100.0, h=100.0, rot=(0, 0, 0), parent=None):
    """A box by its min corner + size, in mm."""
    return {"name": name, "type": "MESH", "hidden_render": False,
            "min": [x, y, z], "max": [x + w, y + d, z + h],
            "rot_deg": list(rot), "parent": parent}


def fails(objs):
    return [f for f in P.check(objs) if f["sev"] == "FAIL"]


def kinds(objs):
    return sorted({f["kind"] for f in fails(objs)})


FLOOR = ob("floor", -5000, -5000, -100, 10000, 10000, 100)


# ------------------------------------------------------------------ FLOATING ---

def test_an_object_resting_on_a_support_is_clean():
    assert fails([FLOOR, ob("base", 0, 0, 0), ob("fig", 10, 10, 100, 80, 80, 200)]) == []


def test_an_object_held_up_by_nothing_is_FLOATING():
    f = fails([FLOOR, ob("base", 0, 0, 0), ob("fig", 10, 10, 140, 80, 80, 200)])
    assert [x["kind"] for x in f] == ["FLOATING"]
    assert "40.0mm away" in f[0]["detail"]


def test_something_touching_a_wall_but_standing_on_nothing_is_not_FLOATING():
    """A hung or wall-let element is legitimate and is not this check's business.
    Negative control for the rule above."""
    objs = [FLOOR, ob("wall", 0, 0, 0, 50, 1000, 3000),
            ob("shelf", 50, 100, 900, 300, 200, 30)]
    assert "FLOATING" not in kinds(objs)


def test_ground_is_derived_not_assumed_to_be_zero():
    """A scene built on a slab, or below datum, must still work."""
    objs = [ob("slab", -500, -500, -900, 2000, 2000, 100),
            ob("thing", 0, 0, -800, 100, 100, 100)]
    assert P.ground_z(objs) == -900
    assert fails(objs) == []


# ------------------------------------------------------------------ OFF-AXIS ---

def test_a_tipped_object_is_OFF_AXIS():
    objs = [FLOOR, ob("base", 0, 0, 0), ob("fig", 10, 10, 100, 80, 80, 200, rot=(2.0, 0, 0))]
    assert "OFF-AXIS" in kinds(objs)


def test_yaw_about_Z_is_legitimate_and_never_flagged():
    """Negative control: a rotated-in-plan object is ordinary design. Only a TIP
    is a matrix error."""
    objs = [FLOOR, ob("base", 0, 0, 0), ob("fig", 10, 10, 100, 80, 80, 200, rot=(0, 0, 45.0))]
    assert "OFF-AXIS" not in kinds(objs)


def test_off_axis_is_reported_per_part_not_per_group():
    """Grouping must not hide a tipped part inside a level assembly."""
    objs = [FLOOR, ob("base", 0, 0, 0),
            ob("body", 10, 10, 100, 80, 80, 200, parent="root"),
            ob("arm", 20, 20, 200, 20, 20, 40, rot=(3.0, 0, 0), parent="root")]
    assert [f["object"] for f in fails(objs) if f["kind"] == "OFF-AXIS"] == ["arm"]


# ------------------------------------------------------------------ OVERHANG ---

def test_a_freestanding_object_hanging_off_its_only_support_is_OVERHANG():
    """Round 16: the image was overhanging its own base."""
    objs = [FLOOR, ob("base", 0, 0, 0, 100, 100, 100),
            ob("fig", 60, 10, 100, 80, 80, 200)]
    f = [x for x in fails(objs) if x["kind"] == "OVERHANG"]
    assert f and "40.0mm past `base`" in f[0]["detail"]


def test_an_object_within_its_support_is_clean():
    """Negative control with a real margin: 10 mm proud on each side is fine."""
    objs = [FLOOR, ob("base", 0, 0, 0, 100, 100, 100), ob("fig", 10, 10, 100, 80, 80, 200)]
    assert "OVERHANG" not in kinds(objs)


def test_a_built_element_braced_by_a_wall_is_NOT_overhang():
    """THE FIRST FALSE-POSITIVE RUN: 27 pieces of correct construction convicted,
    zero props. A plinth overhanging its own toe-kick is what a toe-kick IS — and
    the plinth is held by the wall behind it as well."""
    objs = [FLOOR,
            ob("wall", 0, 200, 0, 2000, 50, 3000),
            ob("toe", 100, 100, 0, 200, 100, 100),
            ob("plinth", 0, 100, 100, 400, 100, 200)]   # hangs past toe on both sides
    assert "OVERHANG" not in kinds(objs)


def test_an_element_spanning_several_supports_is_NOT_overhang():
    """THE THIRD FALSE POSITIVE: a ceiling rests on ten wall pieces at one height,
    and no single one contains a 6 x 4.5 m slab. Containment is the wrong question
    for a spanning element — the rule's premise is that ONE thing holds it up."""
    walls = [ob(f"w{i}", x, y, 0, 50, 50, 1000)
             for i, (x, y) in enumerate([(0, 0), (950, 0), (0, 950), (950, 950)])]
    objs = [FLOOR] + walls + [ob("slab", 0, 0, 1000, 1000, 1000, 50)]
    assert "OVERHANG" not in kinds(objs)


def test_contents_do_not_brace_their_container():
    """THE FOURTH CORRECTION: the vase escaped because the flowers standing IN it
    are a lateral contact. A thing wholly inside your own footprint cannot hold
    you up — so the vase is still checked, and still convicted."""
    objs = [FLOOR, ob("step", 0, 0, 0, 400, 400, 100),
            ob("vase", 360, 100, 100, 80, 80, 300),          # hangs 40 past the step
            ob("stem", 380, 120, 400, 20, 20, 200)]          # inside the vase footprint
    f = [x for x in fails(objs) if x["kind"] == "OVERHANG"]
    assert f and f[0]["object"] == "vase", fails(objs)


def test_a_multi_part_assembly_is_judged_as_ONE_thing():
    """THE SECOND CORRECTION, and it is why the guard would have PASSED round 16:
    a figure is several meshes that touch each other, so no part of it was ever
    'freestanding' and the whole class stayed exempt."""
    objs = [FLOOR, ob("base", 0, 0, 0, 100, 100, 100),
            ob("body", 60, 10, 100, 80, 80, 200, parent="root"),
            ob("head", 70, 20, 300, 60, 60, 60, parent="body")]
    f = [x for x in fails(objs) if x["kind"] == "OVERHANG"]
    assert f, fails(objs)
    assert "+1 parts" in f[0]["object"] or "+2 parts" in f[0]["object"]


def test_parent_chain_is_cycle_safe():
    parent = {"a": "b", "b": "a"}
    assert P.root_of("a", parent) in ("a", "b")          # terminates, no hang


# ---------------------------------------------------------------- advisories ---

def test_interpenetration_is_ADVISORY_and_never_fails_the_run():
    """An AABB cannot tell interlocking from intersecting. Promoting this to FAIL
    would train the reader to mute the instrument, which is how the previous debt
    instrument died."""
    objs = [FLOOR, ob("a", 0, 0, 0, 200, 200, 200), ob("b", 100, 100, 100, 200, 200, 200)]
    found = P.check(objs)
    assert any(f["kind"] == "INTERPENETRATION" for f in found)
    assert all(f["sev"] == "ADVISORY" for f in found if f["kind"] == "INTERPENETRATION")


def test_hidden_and_non_mesh_objects_are_not_judged():
    """An EMPTY has no bounds and a hide_render object is not in the picture.
    Judging either would report a defect nobody can see."""
    objs = [FLOOR,
            {"name": "e", "type": "EMPTY", "hidden_render": False, "rot_deg": [9, 9, 9]},
            dict(ob("ghost", 0, 0, 5000), hidden_render=True)]
    assert fails(objs) == []


# ------------------------------------------------------------ the live scene ---

def test_the_tolerances_are_claims_about_the_real_world():
    """Pinned so a future run cannot quietly widen them to make a lane pass."""
    assert P.CONTACT_TOL_MM == 1.0
    assert P.OVERHANG_TOL_MM == 2.0
    assert P.AXIS_TOL_DEG == 0.05


@pytest.mark.parametrize("dy,expect", [(-100.0, False), (-140.0, True)])
def test_the_overhang_threshold_discriminates_at_the_real_margin(dy, expect):
    """Taken from the live TRN-001 scene: the vase has 125.9 mm of step in front of
    it. At -100 mm it is still standing on the step and must NOT be flagged; at
    -140 mm it is over the edge and must be. A guard that fires at both is not
    measuring the margin."""
    objs = [FLOOR,
            ob("step", -1258, -311, 0, 2242, 311, 455),
            ob("vase", -1077, -185.1 + dy, 455, 80.2, 80.2, 300)]
    assert ("OVERHANG" in kinds(objs)) is expect
