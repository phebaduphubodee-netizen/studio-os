#!/usr/bin/env python3
"""Tests for transform_check.py — the rung that asks whether a modifier width in
this scene still means millimetres.

THE TEST THIS FILE EXISTS TO AVOID. This repo has shipped, in writing, a test
that "computed the answer from the same probe as the code" and a rung whose
definition made it impossible to fail. So the cases below never ask the module
to agree with itself: every expectation is a number written here by hand, and
the two that matter most are the ones where a GREEN answer would be a lie —
a dump with no `scale` key, and a positive control that does not fire.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transform_check as TC                                 # noqa: E402

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "transform_check.py")


def _dump(tmp_path, objs, name="d.scene.json"):
    p = tmp_path / name
    p.write_text(json.dumps({"schema": "scene-dump@2", "objects": objs}),
                 encoding="utf-8")
    return str(p)


def _run(path):
    r = subprocess.run([sys.executable, SCRIPT, path], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# --------------------------------------------------------------- the predicate

def test_scale_alone_is_not_a_defect():
    """A scaled mesh with no local-space modifier is a legitimate state — a
    scaled backdrop plane, a scaled proxy. The defect is the PAIR. A rung that
    convicted scale alone would fire on every honest object in a scene that used
    scaling deliberately, and would be switched off in a week."""
    hit, _ = TC.offends({"name": "plane", "scale": [4.0, 4.0, 1.0],
                         "local_space_mods": []})
    assert hit is False


def test_a_modifier_alone_is_not_a_defect():
    hit, worst = TC.offends({"name": "door", "scale": [1.0, 1.0, 1.0],
                             "local_space_mods": ["BEVEL", "SOLIDIFY"]})
    assert hit is False and abs(worst - 1.0) < 1e-9


def test_the_pair_is_the_defect_and_the_worst_axis_is_reported():
    """Non-uniform scale is the nastier case: two axes look innocent. The report
    must name the axis that is actually multiplying the width, not an average."""
    hit, worst = TC.offends({"name": "seat", "scale": [1.0, 1.0, 2.5],
                             "local_space_mods": ["SOLIDIFY"]})
    assert hit is True
    assert abs(worst - 2.5) < 1e-9


def test_a_scale_below_one_offends_just_as_much():
    """0.4 shrinks an 18 mm solidify to 7.2 mm. Half of this defect class makes
    things too THIN, and an `if scale > 1` test would have missed all of it."""
    hit, worst = TC.offends({"name": "shelf", "scale": [0.4, 0.4, 0.4],
                            "local_space_mods": ["BEVEL"]})
    assert hit is True and abs(worst - 0.4) < 1e-9


def test_float_noise_from_a_matrix_decomposition_does_not_convict():
    """`scale` comes out of matrix_world.to_scale(), so an identity transform
    lands near 1.0 but not exactly. The band is written here by hand (1e-4) so
    that widening it in the module is a test failure, not a silent relaxation."""
    hit, _ = TC.offends({"name": "x", "scale": [1.0000001, 0.9999999, 1.0],
                         "local_space_mods": ["BEVEL"]})
    assert hit is False


def test_the_modifier_set_is_types_not_object_names():
    """R9b in one assertion: the rung's scope is the closed set of Blender
    modifier types whose arithmetic is scale-sensitive, so a new object class is
    covered the day it is built. If someone converts this to a list of object
    name substrings, this fails."""
    assert set(TC.LOCAL_SPACE_MODS) >= {"SOLIDIFY", "BEVEL", "MIRROR", "ARRAY"}
    assert all(m.isupper() for m in TC.LOCAL_SPACE_MODS)


# ------------------------------------------------------- the could-not-run gate

def test_a_dump_without_the_scale_key_exits_2_and_never_0(tmp_path):
    """THE LOAD-BEARING CASE. Every dump written before 2026-08-29 has no
    `scale`. Reading that as "no object is scaled" would print a clean bill of
    health for a scene nobody looked at — the vacuous zero this repo has now
    filed under four different names."""
    p = _dump(tmp_path, [{"name": "a", "local_space_mods": ["BEVEL"]},
                         {"name": "b", "local_space_mods": []}])
    code, out = _run(p)
    assert code == 2, out
    # TWO refusals live here and both are exit 2. This dump trips the sharper one
    # first, because mesh "a" carries a local-space modifier AND no scale — it is
    # individually unjudgeable, which is a stronger statement than "the file is old".
    assert "cannot be judged and must not be excused" in out
    assert "a" in out


def test_an_old_dump_with_nothing_to_judge_still_exits_2(tmp_path):
    """The other half: no record carries a local-space modifier, so nothing is
    individually unjudgeable — and the dump is STILL refused, because a scene nobody
    measured is not a scene with nothing wrong."""
    p = _dump(tmp_path, [{"name": "a", "local_space_mods": []},
                         {"name": "b", "local_space_mods": []}])
    code, out = _run(p)
    assert code == 2, out
    assert "predates the key" in out


def test_one_unjudgeable_mass_is_not_excused_by_a_thousand_clean_ones(tmp_path):
    """THE CASE THE FIRST VERSION GOT WRONG. The gate was all-or-nothing, so a single
    mesh with a modifier and no scale was dropped from numerator AND denominator, and
    the rung then printed a claim about EVERY mesh. Exit 0 here would be the vacuous
    zero wearing a pass."""
    objs = [{"name": f"clean{i}", "scale": [1.0, 1.0, 1.0],
             "local_space_mods": ["BEVEL"]} for i in range(50)]
    objs.append({"name": "OFFENDER_no_scale_key", "local_space_mods": ["SOLIDIFY"]})
    code, out = _run(_dump(tmp_path, objs))
    assert code == 2, out
    assert "OFFENDER_no_scale_key" in out


def test_an_empty_dump_exits_2(tmp_path):
    code, out = _run(_dump(tmp_path, []))
    assert code == 2, out


def test_an_unreadable_dump_exits_2(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    code, out = _run(str(p))
    assert code == 2, out


def test_a_missing_file_exits_2(tmp_path):
    code, out = _run(str(tmp_path / "nope.json"))
    assert code == 2, out


# ---------------------------------------------------------- the positive control

def test_the_positive_control_fires_on_its_own_data():
    assert TC._positive_control() is True


def test_the_control_would_catch_a_predicate_that_says_yes_to_everything(
        monkeypatch):
    """A control that only checks "did it convict the planted defect" passes for
    a predicate hard-wired to True. This asserts the OTHER half is real."""
    monkeypatch.setattr(TC, "offends", lambda rec: (True, 9.9))
    assert TC._positive_control() is False


def test_the_control_would_catch_a_predicate_that_says_no_to_everything(
        monkeypatch):
    monkeypatch.setattr(TC, "offends", lambda rec: (False, 1.0))
    assert TC._positive_control() is False


def test_a_dead_control_forces_exit_2_even_on_a_clean_scene(tmp_path,
                                                            monkeypatch):
    """If the detector cannot be shown to detect, a clean scene is not evidence.
    Run in-process so the monkeypatch is visible."""
    monkeypatch.setattr(TC, "_positive_control", lambda: False)
    p = _dump(tmp_path, [{"name": "a", "scale": [1.0, 1.0, 1.0],
                          "local_space_mods": ["BEVEL"]}])
    assert TC.main([p]) == 2


# ---------------------------------------------------------------- end to end

def test_clean_scene_exits_0_and_says_what_it_judged(tmp_path):
    p = _dump(tmp_path, [
        {"name": "mill__door", "scale": [1.0, 1.0, 1.0],
         "local_space_mods": ["BEVEL", "SOLIDIFY"]},
        {"name": "rug__acq0", "scale": [1.0, 1.0, 1.0], "local_space_mods": []}])
    code, out = _run(p)
    assert code == 0, out
    # A pass that does not print its denominator is indistinguishable from a
    # pass that had nothing to look at.
    assert "1 carry a local-space modifier" in out
    assert "positive control FIRED" in out


def test_planted_offender_exits_1_and_is_named(tmp_path):
    p = _dump(tmp_path, [
        {"name": "mill__door", "scale": [1.0, 1.0, 1.0],
         "local_space_mods": ["BEVEL"]},
        {"name": "bench__acq0__seat", "scale": [1.0, 1.0, 2.5],
         "local_space_mods": ["SOLIDIFY"]}])
    code, out = _run(p)
    assert code == 1, out
    assert "bench__acq0__seat" in out
    assert "2.5000" in out


def test_a_scene_shaped_like_the_scene_of_record_exits_0(tmp_path):
    """RENAMED 2026-08-29, because the first name stated a conclusion the body does
    not reach. It builds 496 synthetic records at scale 1 and asserts exit 0 — that is
    the module's arithmetic at the shipped SHAPE (hundreds of bevelled masses), not a
    fact about p2r90, which has no artefact carrying the key. The 496/244 figures are
    the measured ones and are why the shape is this shape; the assertion is about the
    shape only."""
    objs = [{"name": f"m{i}", "scale": [1.0, 1.0, 1.0],
             "local_space_mods": ["BEVEL"]} for i in range(244)]
    objs += [{"name": f"p{i}", "scale": [1.0, 1.0, 1.0],
              "local_space_mods": []} for i in range(252)]
    code, out = _run(_dump(tmp_path, objs))
    assert code == 0, out
    assert "496 meshes" in out
    assert "244 carry a local-space modifier" in out
