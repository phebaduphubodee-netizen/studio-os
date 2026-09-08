"""test_sheer_check.py — the two readings, and the properties that make them readings.

The tests that earn their place here are the ones that pin the properties the metric was
CHOSEN for. A structure number that a uniform darkening can move is the bar this rung
replaced, so `test_darkening_cannot_move_the_structure_number` is the whole point of the
file; the rest guard the could-not-run contract.
"""
import io
import json
import os
import sys

import numpy as np
import pytest
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheer_check as sc
import value_probe as vp

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "pipeline", "output")
FRAME = os.path.join(OUT, "room_bedroom_suite_eye_p2r95.png")


def _have(stem):
    return all(os.path.isfile(stem + ext)
               for ext in (".png", ".matmask.png", ".matmask.json"))


REAL = _have(FRAME[:-4])


# ------------------------------------------------------------------ the metric itself --
def test_darkening_cannot_move_the_structure_number():
    """THE REASON THIS METRIC EXISTS. The bar it replaced — 'share of the band inside
    [0.80,0.90) <= 40%' — was satisfied in a real sweep by darkening the whole field
    (8.89% at direct 0.90) while detail fell 44%. With the selection held FIXED (which is
    what selecting cloth BY MATERIAL guarantees), RMS contrast must not move at all."""
    rng = np.random.default_rng(7)
    base = np.clip(0.82 + 0.05 * rng.standard_normal((300, 300)).astype(np.float32), 0, 1)
    sel = np.ones((300, 300), bool)
    ref = sc.rms_contrast(base, sel)
    for k in (0.95, 0.85, 0.75):
        assert sc.rms_contrast(base * k, sel) == pytest.approx(ref, rel=0.02), k


def test_a_brightness_threshold_would_have_broken_that():
    """Why the selection is by material and not by luma — this is the bug the test above
    caught on its first run. Re-selecting by a FIXED threshold as the image darkens moves
    pixels across it, so the 'invariant' number drifts."""
    rng = np.random.default_rng(7)
    base = np.clip(0.62 + 0.05 * rng.standard_normal((300, 300)).astype(np.float32), 0, 1)
    a = sc.rms_contrast(base, base > 0.60)
    b = sc.rms_contrast(base * 0.75, (base * 0.75) > 0.60)
    assert abs(b - a) / a > 0.10, "a fixed luma threshold should have drifted here"


def test_removing_structure_does_move_it():
    """Positive control: a metric nothing can move is not a metric."""
    rng = np.random.default_rng(7)
    sel = np.ones((300, 300), bool)
    textured = np.clip(0.82 + 0.05 * rng.standard_normal((300, 300)).astype(np.float32), 0, 1)
    flat = np.full((300, 300), 0.82, np.float32)
    assert sc.rms_contrast(flat, sel) < sc.rms_contrast(textured, sel) * 0.5


# ------------------------------------------------------- the could-not-run contract ----
def test_missing_mask_is_exit_2_not_a_pass(tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (64, 64)).save(p)
    assert sc.main([str(p)]) == 2


def test_a_mask_from_another_frame_is_refused(tmp_path):
    beauty = tmp_path / "f.png"
    Image.new("RGB", (200, 200), (200, 200, 200)).save(beauty)
    Image.new("RGB", (100, 100)).save(tmp_path / "f.matmask.png")
    (tmp_path / "f.matmask.json").write_text(json.dumps({"ids": {"1": "curtain_sheer"}}))
    with pytest.raises(RuntimeError, match="different sizes"):
        sc.measure(str(beauty), str(tmp_path / "f.matmask.png"),
                   str(tmp_path / "f.matmask.json"))


def test_a_frame_with_no_sheer_is_refused(tmp_path):
    beauty = tmp_path / "f.png"
    Image.new("RGB", (100, 100)).save(beauty)
    Image.new("RGB", (100, 100)).save(tmp_path / "f.matmask.png")
    (tmp_path / "f.matmask.json").write_text(json.dumps({"ids": {"1": "wall_paint"}}))
    with pytest.raises(RuntimeError, match="no `curtain_sheer`"):
        sc.measure(str(beauty), str(tmp_path / "f.matmask.png"),
                   str(tmp_path / "f.matmask.json"))


# --------------------------------------------------------------- on a real frame -------
@pytest.mark.skipif(not REAL, reason="p2r95 frame + masks not on disk")
def test_the_band_is_the_whole_curtain_wall_not_just_the_sheer():
    """The first cut derived the band from the SHEER alone, so parking the blackout over
    the west end moved it 1694 -> 1877 and the before/after described different
    rectangles. The union does not move when the fabric is re-parked."""
    r = sc.measure(FRAME, FRAME[:-4] + ".matmask.png", FRAME[:-4] + ".matmask.json")
    assert r["band"][0] == 1694, r["band"]
    assert r["band"][2] == 2400, r["band"]


@pytest.mark.skipif(not REAL, reason="p2r95 frame + masks not on disk")
def test_it_reports_the_hem_defect_that_C2_found_by_eye():
    """p2r95 is the frame the defect was measured on: 133 of 706 fabric columns show
    GLAZING beneath the hem. Note what this is NOT counting — the first version counted
    FLOOR under the hem, which is under every hem at every height because the floor lies
    between the camera and the cloth, and it duly reported a real fix as a regression
    (47.2% -> 62.0%). Glass under a curtain is the defect; floor under one is a room."""
    r = sc.measure(FRAME, FRAME[:-4] + ".matmask.png", FRAME[:-4] + ".matmask.json")
    assert r["fabric_columns"] > 100
    assert r["behind_under_pct"] > sc.BEHIND_UNDER_MAX_PCT, (
        "if this passes, the fixture is no longer the frame the defect was measured on")


@pytest.mark.skipif(not _have(os.path.join(OUT, "room_bedroom_suite_eye_p2r96")),
                    reason="p2r96 frame + masks not on disk")
def test_the_fixed_frame_reads_clean():
    """The other half of the pair. Without this the test above passes for a rung that
    can only ever say FAIL."""
    f = os.path.join(OUT, "room_bedroom_suite_eye_p2r96.png")
    r = sc.measure(f, f[:-4] + ".matmask.png", f[:-4] + ".matmask.json")
    assert r["behind_under_pct"] == 0.0
    assert r["local_contrast"] >= sc.STRUCTURE_MIN
