"""test_cushion_study_derive.py — known answers for the D17 cushion study.

WHY THESE EXIST. Four verifier rounds on the day-11 note recomputed NUMBERS and passed a
script whose DEFINITIONS were wrong (a metric named like another metric, a formula that only
held for quads). Every test below pins a DEFINITION rather than a value, and each one names
the specific mistake it would have caught — including two made and caught inside this unit.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cushion_study_derive as c  # noqa: E402
from study_probe_read import load, meshes  # noqa: E402

ART = os.path.join(c.REPO, "qa", "blenderkit-study-cushions.json")


@pytest.fixture(scope="module")
def art():
    with open(ART, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- lean_deg


@pytest.mark.parametrize("rot,want", [
    ([0, 0, 0], 0.0),
    ([45, 0, 0], 45.0),
    ([90, 0, 0], 90.0),
    ([0, 45, 0], 45.0),
    ([-45, 0, 0], 45.0),
])
def test_lean_is_the_angle_off_vertical(rot, want):
    assert c._lean_deg(rot) == pytest.approx(want, abs=0.05)


def test_a_yaw_is_not_a_lean():
    """(0,0,-90) spins a pillow about the vertical; it does not tip it. If this ever starts
    returning 90 the note's whole pose table inverts."""
    assert c._lean_deg([0, 0, -90]) == 0.0


def test_lean_uses_a_real_matrix_not_the_x_euler():
    """Bed-Pillow.001 is (45,0,-9). Reading 'the x euler' gives the right answer there by
    luck; a combined rotation is where the shortcut breaks. On (45,0,-90) the x euler still
    says 45 while the true tilt off vertical is 45 as well -- so the case that separates them
    is a y term: (45,45,0) is NOT 45."""
    assert c._lean_deg([45, 0, -9]) == pytest.approx(44.9, abs=0.2)
    assert c._lean_deg([45, 45, 0]) != pytest.approx(45.0, abs=1.0)


# ---------------------------------------------------- the instrument's blind spot


def test_the_francesca_pillows_are_upright_and_lean_deg_cannot_see_it(art):
    """THE BLIND SPOT, PINNED. Pose baked into mesh data is invisible to lean_deg. If someone
    'fixes' lean_deg later, this test tells them what z_rank was for."""
    s = art["arrangement"]["62253e5c"]
    fr = [p for p in s["pillows"] if p["name"].startswith("Francesca")]
    assert len(fr) == 3
    for p in fr:
        assert p["lean_deg"] == 0.0                     # the transform says flat...
        assert p["presents_mm"] == 512                  # ...and it is standing 512 tall
        assert p["z_rank"] <= 2                         # z is not the smallest extent


def test_z_rank_never_rounds_before_it_compares(art):
    """CAUGHT BY ROUND-2 VERIFICATION. The first z_rank rounded each world extent to whole mm
    BEFORE sorting, then used list.index(), which returns the first of two now-equal entries.
    ba112721's four pillows have z as the strict minimum on all four, but came out 3,3,2,2 --
    and the note then explained that flip as "the spans differ by a few mm", which its own rows
    refute (two pillows with the SAME 0.6 mm gap landed on opposite ranks). An instrument that
    rounds before it compares invents ties the geometry does not have."""
    ranks = [p["z_rank"] for p in art["arrangement"]["ba112721"]["pillows"]]
    assert ranks == [3, 3, 3, 3], ranks
    # and the rows where the rank is not a real signal say so rather than reading confident
    ties = [p["z_rank_is_near_tie"] for p in art["arrangement"]["ba112721"]["pillows"]]
    assert sum(ties) == 3, ties


def test_z_rank_cannot_see_a_lean_only_a_full_stand_up(art):
    """The limitation the fix exposed, pinned so it is not re-forgotten: a pillow leaning 44.9
    still has z as its smallest extent, so it ranks 3 exactly like one lying flat. z_rank
    separates UPRIGHT from not-upright; it says nothing about tilt."""
    leaning = art["arrangement"]["ba112721"]["pillows"]
    assert {p["lean_deg"] for p in leaning} == {44.9}
    assert {p["z_rank"] for p in leaning} == {3}          # a 45 deg lean reads as flat
    flat = art["arrangement"]["a682383b"]["pillows"][0]
    assert flat["lean_deg"] == 0.0 and flat["z_rank"] == 3   # so does an actually-flat one
    upright = [p for p in art["arrangement"]["62253e5c"]["pillows"]
               if p["name"].startswith("Francesca")]
    assert {p["z_rank"] for p in upright} == {2}          # only standing up moves the rank


def test_face_area_dispersion_is_measured_not_inferred(art):
    """Round 2 filed that "we spread polygons evenly" was an inference a MEAN cannot support.
    It is now a measurement, and this pins both sides of it."""
    src = art["ours"]["source_object"]["face_area_mm2"]
    assert src["p90_over_p10"] == 1.04 and src["cv"] < 0.1
    shells = [art["construction"][k]["objects"] for k in ("aac13b32", "da65b0fa", "7ca290af")]
    bodies = [next(o for o in objs if o["name"] == art["construction"][k]["body_name"])
              for k, objs in zip(("aac13b32", "da65b0fa", "7ca290af"), shells)]
    for b in bodies:
        assert b["face_area_mm2"]["p90_over_p10"] > 20, b["name"]


def test_z_rank_3_means_lying_flat(art):
    """a682383b's single fused pillow is 1127 x 504 x 200 -- z smallest -- so rank 3."""
    p = art["arrangement"]["a682383b"]["pillows"][0]
    assert p["world_extents_mm"] == [1127, 504, 200]
    assert p["z_rank"] == 3


# ------------------------------------------------------- asset size and shares


def test_asset_size_is_the_union_not_the_densest_mesh(art):
    """CAUGHT IN THIS UNIT: asset_dims_mm was taken from the mesh with the most polygons,
    which on aac13b32 is a 641x136x20 fringe strip. The asset is a 168 mm thick pillow."""
    d = art["construction"]["aac13b32"]["asset_dims_mm"]
    assert d[2] == 168, d
    assert d != [641, 136, 20]


def test_detail_share_is_withheld_on_a_single_resolution_asset(art):
    """CAUGHT IN THIS UNIT: c4450c29 is two whole pillows at edge 7.69 and 7.71. Calling the
    second one '63.2% detail' was a category error, so the share is None below spread 2.0."""
    s = art["construction"]["c4450c29"]
    assert s["edge_spread"] < 2.0
    assert s["detail_vert_share"] is None
    t = art["construction"]["aac13b32"]
    assert t["edge_spread"] >= 2.0
    assert t["detail_vert_share"] > 0.99


# ------------------------------------------------------------- per-slot data


def test_absent_per_slot_is_not_measured_rather_than_zero():
    """A dump probed before 2026-09-02 carries no per_slot key. Returning [] would read as
    'this object has no faces on any material', which is the opposite of the truth."""
    assert c._slots({"mesh": {}}) is None
    got = c._slots({"mesh": {"per_slot": [{"slot": 0, "material": "m", "faces": 2,
                                           "area_m2": 1.0},
                                          {"slot": 1, "material": "n", "faces": 1,
                                           "area_m2": 3.0}]}})
    assert [round(q["area_share"], 3) for q in got] == [0.25, 0.75]


def test_both_fabrics_of_the_bought_cushion_are_on_real_faces(art):
    """The claim R5 rests on. Slot faces must sum to the object's own quad count, or the
    'we discarded a second fabric' sentence is not supported."""
    src = art["ours"]["source_object"]
    assert src["slots_with_no_face"] == []
    assert sum(q["faces"] for q in src["per_slot"]) == src["quads"] == 136864
    assert {q["material"] for q in src["per_slot"]} == {"White Fabric", "Light Beige Fabric"}


# ------------------------------------------------------- the axis and the tie


def test_a_bed_is_longer_than_it_is_wide_so_the_longer_axis_is_not_the_width(art):
    """CAUGHT IN THIS UNIT, and it is the D16 fill bug one unit later: on a wardrobe the
    longer plan axis is the width; on a bed it is the LENGTH. The keys must not say 'width'."""
    s = art["arrangement"]["ba112721"]
    assert "long_axis" in s and "short_axis" in s
    assert "width_axis" not in s
    assert s["bed_plan_mm"] == [1662, 2172] and s["long_axis"] == "y"


def test_a_near_square_plan_flags_itself_instead_of_picking_an_axis(art):
    """62253e5c's plan is 2434 x 2245 (1.08). The overlap NUMBERS are real there; the labels
    'front-to-back' and 'side-by-side' are a coin-flip, and the note may not use them."""
    assert art["arrangement"]["62253e5c"]["plan_is_near_tie"] is True
    assert art["arrangement"]["ba112721"]["plan_is_near_tie"] is False


# --------------------------------------------------------- the naming floor


def test_name_matching_finds_the_misspelling_and_still_misses_bed_008():
    """The count of staged beds with identifiable pillows is a FLOOR. This test exists so
    nobody later reads it as a census: Bed.008 is a headboard cushion that no word rule
    reaches, and the note says so."""
    assert c._is_pillow("Cusions") is True
    assert c._is_pillow("Pillow") is True
    assert c._is_pillow("Bed.008") is False
    _, d = load("ee42aa0e")
    assert [o["name"] for o in meshes(d) if c._is_pillow(o["name"])] == []


def test_products_are_product_shots_so_no_pose_claim_may_come_from_them(art):
    """The premise of section 0. If a future fetch adds a posed product, this fails and the
    note's 'not one of them can answer a question about pose' has to be rewritten."""
    for pre, s in art["construction"].items():
        for o in s["objects"]:
            assert all(abs(v) <= 0.5 for v in o["rot_deg"]), (pre, o["name"], o["rot_deg"])
