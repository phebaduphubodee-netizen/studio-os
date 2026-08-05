"""Tests for trn002_materials — the PURE half only (no bpy).

The load-bearing one is test_every_mass_in_the_spec_has_a_material: the class of
defect it exists to catch is a mass silently falling through to a default, which
this repo has recorded as "a default nobody set is a decision nobody made".
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn002_materials as MAT  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE = os.path.join(REPO, "training", "TRN-002")


def _spec_files():
    """EVERY spec in the lane, not just the newest.

    This test used to pin spec_r7 by name and went green while the spec the
    builder actually renders drifted away from it. Checking them all also
    enforces the other half: a rename must not silently break a past round,
    because re-rendering a past round is how a regression gets caught."""
    import glob
    return sorted(glob.glob(os.path.join(LANE, "spec_r*.json")))


def _masses():
    out = []
    for p in _spec_files():
        with open(p, encoding="utf-8") as f:
            out += [m["name"] for m in json.load(f)["masses"]]
    return sorted(set(out))


def test_every_mass_in_the_spec_has_a_material():
    missing = []
    for name in _masses():
        try:
            MAT.material_for(name)
        except KeyError:
            missing.append(name)
    assert not missing, f"masses with no material rule: {missing}"


def test_unmapped_mass_raises_rather_than_defaulting():
    with pytest.raises(KeyError):
        MAT.material_for("a_mass_that_does_not_exist")


def test_exact_beats_prefix():
    # rev_* are reveals, but if an exact rule is ever added for one it must win
    assert MAT.material_for("rev_3") == "reveal_shadow"
    assert MAT.material_for("dl_1") == "lens_warm"
    assert MAT.material_for("shelf_board4") == "veneer_travertine"


def test_the_left_run_is_one_material():
    """The critics' recurring 'it reads as two pieces stuck together' is answered
    by continuous material across the flush planes — so console, desk, pier and
    the etagere must resolve to the SAME key, and a change that splits them
    should fail here rather than in a critique."""
    keys = {MAT.material_for(n) for n in
            ("console", "desk", "desk_pier", "shelf_col_base", "shelf_col_back",
             "shelf_board2", "shelf_board3", "shelf_board4")}
    assert len(keys) == 1, f"the left run must be one material, got {keys}"


def test_every_assigned_key_exists_in_the_palette_once_filled():
    """PALETTE starts empty (values arrive from the measurement pass); once a
    key is present, EVERY assigned key must be present — a half-filled palette
    is how a mass gets rendered in default grey without anyone noticing."""
    if not MAT.PALETTE:
        pytest.skip("palette not yet populated by the measurement pass")
    assigned = {MAT.material_for(n) for n in _masses()}
    assert assigned <= set(MAT.PALETTE), (
        f"assigned but absent from PALETTE: {sorted(assigned - set(MAT.PALETTE))}")


def test_every_palette_row_declares_its_provenance():
    for key in MAT.PALETTE:
        assert key in MAT.PALETTE_PROV and MAT.PALETTE_PROV[key], (
            f"{key} has a value but no stated basis")
