"""Tests for bed_pixels — the rung that measures a NAMED OBJECT in the render.

The negative controls here are the ways this rung could go quietly blind, and
each is a defect shape this repo has already paid for:

  * it cannot find the mattress    — and reports 0% instead of refusing. That is
                                     "could not look" printing like "looked and
                                     it was fine" (R11's own sentence).
  * a new object is exempt         — R9b: "a rule that names the objects it
                                     applies to will always exempt the next one".
                                     The guard it replaced covered 2 of 5 placed
                                     classes.
  * the projection stops fitting   — the split would put bare mattress in the
                                     'top' bucket, the one place a flattering
                                     number could hide. The sign of `shift_y`
                                     alone is worth 384 px on the hero frame.
  * a corrupt material snapshot    — room_bedroom_suite_eye_p2r4's sidecar
                                     records every object wearing `census__N`,
                                     a real dict of real strings naming
                                     materials that existed for two seconds.

The last two tests walk the LANE'S OWN FRAMES rather than a fixture, for the
reason test_trn002_materials learned the hard way: a rule proved on a hand-made
dict is proved about the dict.
"""
import glob
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bed_pixels as BP  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "pipeline", "output")


def _m(**kw):
    base = {"core_objects": ["bed__mattress"], "roster": 4, "unknown": [],
            "touching_core": [], "px": {}, "core_px": 0, "core_share": 0.0,
            "sliver_px": BP.SLIVER_PX}
    base.update(kw)
    return base


# --- roles come from the material, never from the name ------------------------

def test_role_is_read_off_the_material():
    names = {1: "bed__mattress", 2: "bed__cloth__acq1", 3: "bed__base"}
    mats = {"bed__mattress": ["bed_mattress"], "bed__cloth__acq1": ["bed_duvet"],
            "bed__base": ["bed_base"]}
    role, unknown = BP.roles_of(names, mats)
    assert role["bed__mattress"] == BP.CORE
    assert role["bed__cloth__acq1"] == BP.BEDDING
    assert role["bed__base"] == BP.FRAME
    assert unknown == []


def test_a_renamed_mattress_is_still_the_core():
    """The whole point of keying on the material: rename the object and the rung
    still finds it. A name-matching guard would go blind here."""
    role, unknown = BP.roles_of({1: "sleep_platform_v2"},
                                {"sleep_platform_v2": ["bed_mattress"]})
    assert role == {"sleep_platform_v2": BP.CORE}
    assert unknown == []


def test_an_object_with_no_material_is_returned_not_dropped():
    role, unknown = BP.roles_of({1: "mystery"}, {})
    assert role == {}
    assert unknown == [("mystery", None)]


# --- the verdict --------------------------------------------------------------

def test_a_visible_core_is_reported_loudly_and_is_not_a_violation():
    """The absolute defect is true of all 15 masked frames this lane has, so a
    flat cut on it would be red on every render — the shape R13 warns gets
    switched off. It speaks on every run and blocks nothing."""
    m = _m(core_px=270_691, core_share=0.44, split={"core_flank": 254_849})
    assert BP.check(m) == []
    st = BP.standing(m)
    assert st and "MATTRESS IS VISIBLE" in st[0]
    assert any("VERTICAL SIDE FACE" in s for s in st)
    assert any("flank-panel" in s for s in st), "the target must cite its panel"


def test_a_covered_core_says_nothing():
    assert BP.standing(_m(core_px=0)) == []


def test_an_antialiased_rim_does_not_read_as_a_bare_bed():
    """The floor is value_probe's own MIN_PIXELS — reused, not invented."""
    assert BP.standing(_m(core_px=BP.SLIVER_PX)) == []
    assert BP.standing(_m(core_px=BP.SLIVER_PX + 1, core_share=0.0004))


# --- the ratchet, which is the half that blocks --------------------------------

CAM = {"res": [2400, 1800, 100], "lens": 24.0, "shift": [0.0, -0.08],
       "matrix": [[1, 0, 0, 0]]}
BASE = {"camera": CAM, "frame": "p2r49", "core_px": 270_691,
        "core_flank": 254_849}


def test_the_ratchet_holds_when_nothing_got_worse():
    m = _m(core_px=270_691, split={"core_flank": 254_849})
    v, _n, ran = BP.ratchet(m, BASE, CAM)
    assert ran and v == []


def test_the_ratchet_bites_on_the_regression_it_was_built_from():
    """p2r44's real numbers against p2r49's baseline. Bare flank rose 11,694 ->
    295,661 px across the rounds that swapped hand-built cloth for a bought set,
    while coverage read 94.0% and fall_sides read 4/4 throughout."""
    m = _m(core_px=332_879, split={"core_flank": 295_661})
    v, _n, ran = BP.ratchet(m, BASE, CAM)
    assert ran and len(v) == 2
    assert all("rose from" in s for s in v)


def test_a_frame_that_improves_is_never_a_violation():
    m = _m(core_px=11_694, split={"core_flank": 11_694})
    v, _n, ran = BP.ratchet(m, BASE, CAM)
    assert ran and v == []


def test_a_different_camera_is_refused_rather_than_compared():
    """A pixel count is a property of the view. The playblast is half size, so
    its counts would 'improve' for a reason that says nothing about the bed."""
    m = _m(core_px=3_525, split={"core_flank": 3_525})
    v, notes, ran = BP.ratchet(m, BASE, dict(CAM, res=[1200, 900, 100]))
    assert not ran and v == []
    assert any("DID NOT RUN" in n for n in notes)


def test_no_baseline_does_not_read_as_a_pass():
    v, notes, ran = BP.ratchet(_m(core_px=1), None, CAM)
    assert not ran and v == []
    assert any("DID NOT RUN" in n for n in notes)


def test_no_core_in_the_roster_REFUSES_rather_than_passing():
    with pytest.raises(BP.CouldNotRun):
        BP.check(_m(core_objects=[]))


def test_a_new_material_over_the_mattress_blocks():
    v = BP.check(_m(unknown=[("bed__topper", "linen_x")],
                    touching_core=["bed__topper"], px={"bed__topper": 9000}))
    assert len(v) == 1 and "bed__topper" in v[0] and "linen_x" in v[0]


def test_the_same_new_material_across_the_room_does_not_block():
    v = BP.check(_m(unknown=[("rug", "linen_x")], touching_core=[],
                    px={"rug": 9000}))
    assert v == []


def test_a_sliver_of_an_unknown_object_does_not_block():
    v = BP.check(_m(unknown=[("bed__tag", "linen_x")],
                    touching_core=["bed__tag"], px={"bed__tag": 12}))
    assert v == []


# --- geometry -----------------------------------------------------------------

def test_plan_overlap_is_by_footprint_not_by_distance():
    aabbs = {"m": [[0, 0, 0], [2, 2, 1]],
             "on_it": [[1, 1, 1], [3, 3, 2]],
             "across_the_room": [[9, 9, 0], [10, 10, 1]]}
    assert BP.plan_overlaps(aabbs, ["m"]) == {"m", "on_it"}


def test_in_quad_holds_for_either_winding():
    quad_ccw = [(0, 0), (10, 0), (10, 10), (0, 10)]
    quad_cw = list(reversed(quad_ccw))
    for q in (quad_ccw, quad_cw):
        got = BP._in_quad([5, 20], [5, 5], q)
        assert bool(got[0]) and not bool(got[1])


def test_a_material_snapshot_taken_after_the_census_mask_is_refused():
    side = {"ids": {"1": "bed__mattress"},
            "wears": {"bed__mattress": ["census__8"]}}
    with pytest.raises(BP.CouldNotRun):
        BP.materials_for(side, None)


def test_no_material_source_at_all_refuses():
    with pytest.raises(BP.CouldNotRun):
        BP.materials_for({"ids": {"1": "x"}}, None)


# --- and the lane itself ------------------------------------------------------

def _frames():
    out = []
    for m in sorted(glob.glob(os.path.join(OUT, "*.idmask.png"))):
        stem = m[: -len(".idmask.png")]
        if all(os.path.isfile(stem + s)
               for s in (".png", ".idmask.json", ".scene.json")):
            out.append(stem)
    return out


@pytest.mark.parametrize("stem", _frames(), ids=os.path.basename)
def test_the_projection_reproduces_every_frames_own_mask(stem):
    """THE POSITIVE CONTROL, on real frames. Every object big enough to measure
    must have its measured pixel rows inside its projected AABB rows. This is
    what settled the sign of `shift_y` — the wrong one is off by 384 px on the
    hero frame, which is larger than the feature the split exists to find."""
    side = BP.load_sidecar(stem + ".idmask.json")
    ids, names, _px, beauty = BP.compose(stem + ".png", stem + ".idmask.png", side)
    cam = BP.camera_from(side, beauty.shape[1], beauty.shape[0])
    ok, lines = BP.projection_selfcheck(ids, names,
                                        BP.aabbs_from_dump(stem + ".scene.json"),
                                        cam)
    assert ok, os.path.basename(stem) + "\n" + "\n".join(lines)


@pytest.mark.parametrize("stem", _frames(), ids=os.path.basename)
def test_every_frame_measures_and_its_split_adds_up(stem):
    m = BP.measure(stem + ".png", stem + ".idmask.png", stem + ".idmask.json",
                   stem + ".scene.json")
    assert m["core_objects"], "no core found on a frame of this lane's own bed"
    assert m["split"] is not None, m["split_unavailable"]
    s = m["split"]
    assert s["core_top"] + s["core_flank"] == m["core_px"]
    assert 0 <= s["core_top"] <= m["core_px"]


# --- the two seams the pre-commit review found --------------------------------
# Both are the same shape this repo has already paid for twice: a rung that could
# not run producing a number that reads exactly like evidence.

def test_a_dump_from_another_render_is_refused():
    """Measured before the guard existed: p2r49's frame through p2r45's dump
    reports the core at 87.7% of the sleeping surface instead of 44.0%, with the
    ratchet printing `held`. value_probe's own rule, applied to the third file in
    the joint."""
    frames = _frames()
    a = os.path.join(OUT, "room_bedroom_suite_eye_p2r49")
    b = os.path.join(OUT, "room_bedroom_suite_eye_p2r45")
    if a not in frames or b not in frames:
        pytest.skip("both reference frames are not on disk")
    with pytest.raises(BP.CouldNotRun) as e:
        BP.measure(a + ".png", a + ".idmask.png", a + ".idmask.json",
                   b + ".scene.json")
    assert "DUMP/BEAUTY MISMATCH" in str(e.value)


def test_an_unreadable_baseline_is_could_not_run_not_a_regression(tmp_path):
    """It used to let JSONDecodeError escape, and the caller turned that into an
    uncaught traceback and exit 1 — this module's code for `the bed got worse`.
    A corrupt file would have printed as a regression."""
    bad = tmp_path / "b.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(BP.CouldNotRun):
        BP.load_baseline(str(bad))


def test_a_missing_baseline_is_not_an_error():
    base, path = BP.load_baseline(str(os.path.join(OUT, "no-such-baseline.json")))
    assert base is None and path.endswith("no-such-baseline.json")
