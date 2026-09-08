#!/usr/bin/env python3
"""Tests for edge_drift.py — the guard that has to fire BEFORE any generative edit is
allowed near this lane's geometry.

What is pinned here is not "the code runs". It is the three ways this probe could lie:
  - it must CATCH a mass that moved (that is its whole job),
  - it must refuse to call an INVISIBLE silhouette a pass (R10's white-box-on-white),
  - it must refuse a returned frame that is a different CROP rather than score it.
"""
import json
import os
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edge_drift as ed
import value_probe as vp

H, W = 200, 300


def _mask_with(box, oid):
    """A mask frame: everything id 0 (black) except `box` = (y0, y1, x0, x1) at `oid`."""
    m = np.zeros((H, W, 3), dtype=np.float32)
    y0, y1, x0, x1 = box
    m[y0:y1, x0:x1] = vp.id_to_srgb(oid)
    return m


def _beauty_with(box, fg=200.0, bg=40.0):
    b = np.full((H, W, 3), bg, dtype=np.float32)
    y0, y1, x0, x1 = box
    b[y0:y1, x0:x1] = fg
    return b


BOX = (60, 140, 80, 200)


def test_an_unmoved_object_reads_HELD():
    mask, before = _mask_with(BOX, 1), _beauty_with(BOX)
    rows, s = ed.compare(before, before.copy(), mask, {1: "slab"})
    assert rows[0]["verdict"] == "HELD"
    assert rows[0]["after_miss"] == pytest.approx(0.0, abs=0.02)
    assert s["counts"]["DRIFT"] == 0


@pytest.mark.parametrize("shift", [8, 20, 45])
def test_a_moved_object_reads_DRIFT_and_the_report_says_how_far(shift):
    """A pure translation along x is the case a MEDIAN distance misses — the top and bottom
    runs still overlap, so half the outline reads 0. The share-of-outline statistic sees
    it, and p95 still carries HOW FAR so the row is actionable rather than an alarm."""
    mask, before = _mask_with(BOX, 1), _beauty_with(BOX)
    y0, y1, x0, x1 = BOX
    after = _beauty_with((y0, y1, x0 + shift, x1 + shift))
    rows, _ = ed.compare(before, after, mask, {1: "slab"})
    assert rows[0]["verdict"] == "DRIFT"
    # The two vertical runs (2*80) lose their edge outright, and the leading `shift` px of
    # each horizontal run fall off the moved box's ends — so the lost share GROWS with the
    # distance travelled, which is the behaviour that makes the column readable.
    assert rows[0]["lost"] == pytest.approx((160 + 2 * shift) / 396, abs=0.06)
    assert rows[0]["after_p95"] == pytest.approx(shift, rel=0.35)


def test_a_median_would_have_missed_that_translation_which_is_why_it_is_not_used():
    """Pins the reason for the statistic, not just its value: if this ever goes back to a
    median the test that catches the regression is this one."""
    mask, before = _mask_with(BOX, 1), _beauty_with(BOX)
    y0, y1, x0, x1 = BOX
    after = _beauty_with((y0, y1, x0 + 8, x1 + 8))
    g = ed.gradient_magnitude(ed.luma_of(after))
    d = ed.distance_to_edges(g >= max(np.percentile(ed.gradient_magnitude(
        ed.luma_of(before)), ed.EDGE_PCTILE), ed.EDGE_ABS_FLOOR))
    nb = ed.boundary_mask(vp.decode_ids(mask.astype(np.int16)), 1)
    assert float(np.median(d[nb])) <= 1.0          # a median says "held" — it is wrong


def test_a_silhouette_with_no_edge_in_the_SENT_frame_is_UNCHECKABLE_not_HELD():
    """R10's white box next to a white box. The mask knows the boundary is there; the
    picture we sent never showed it, so there was never a signal to lose. Calling that a
    pass is how a probe starts flattering — it would report clean on the objects it is
    least able to see."""
    mask = _mask_with(BOX, 1)
    flat = np.full((H, W, 3), 128.0, dtype=np.float32)   # object and ground identical
    rows, s = ed.compare(flat, flat.copy(), mask, {1: "white_box"})
    assert rows[0]["verdict"] == "UNCHECKABLE"
    assert s["counts"]["HELD"] == 0


def test_an_invisible_object_stays_UNCHECKABLE_even_when_the_edit_moved_it():
    """The dangerous direction of the same case: never let 'I could not see it' be read
    as 'it did not move'."""
    mask = _mask_with(BOX, 1)
    flat = np.full((H, W, 3), 128.0, dtype=np.float32)
    after = _beauty_with((60, 140, 130, 250))            # something appears elsewhere
    rows, _ = ed.compare(flat, after, mask, {1: "white_box"})
    assert rows[0]["verdict"] == "UNCHECKABLE"


def test_the_report_says_so_when_nothing_at_all_was_checked():
    mask = _mask_with(BOX, 1)
    flat = np.full((H, W, 3), 128.0, dtype=np.float32)
    rows, s = ed.compare(flat, flat.copy(), mask, {1: "white_box"})
    assert "NOTHING WAS CHECKED" in ed.report(rows, s)


def test_a_busier_returned_frame_is_surfaced_because_it_makes_the_test_easier():
    """Failure mode 2. Noise everywhere means every silhouette finds an edge nearby; the
    reader has to be told the bar dropped, in the same breath as the verdict."""
    rng = np.random.default_rng(7)
    mask, before = _mask_with(BOX, 1), _beauty_with(BOX)
    after = before + rng.normal(0, 60, before.shape).astype(np.float32)
    rows, s = ed.compare(before, after, mask, {1: "slab"})
    assert s["edge_density_ratio"] > 1.25
    assert "this test got EASIER" in ed.report(rows, s)


def test_structure_the_model_added_is_reported():
    mask, before = _mask_with(BOX, 1), _beauty_with(BOX)
    after = before.copy()
    after[10:40, 230:290] = 255.0                        # a lamp nobody asked for
    _, s = ed.compare(before, after, mask, {1: "slab"})
    assert s["invented_edge_share"] > 0.05


def test_the_threshold_comes_from_the_SENT_frame_not_from_each_frame():
    """If each frame set its own threshold, a washed-out return would re-normalise its way
    to a clean sheet and a noisy one would raise the bar it then cleared. Pinned directly:
    two utterly different returns, one threshold."""
    rng = np.random.default_rng(3)
    mask, before = _mask_with(BOX, 1), _beauty_with(BOX)
    _, flat = ed.compare(before, before * 0.02, mask, {1: "slab"})
    _, noisy = ed.compare(before, rng.uniform(0, 255, before.shape).astype(np.float32),
                          mask, {1: "slab"})
    assert flat["edge_threshold"] == noisy["edge_threshold"]
    assert flat["edge_density_after"] < flat["edge_density_before"] < noisy["edge_density_after"]


def test_a_flat_sent_frame_cannot_come_back_all_clear():
    """The floor's own reason. Before it existed, p90 of a mostly-flat frame was 0.0,
    `grad >= 0.0` made EVERY pixel an edge, and a box that moved right across the frame
    reported HELD at distance 0."""
    mask = _mask_with(BOX, 1)
    before = _beauty_with(BOX, fg=128.4, bg=128.0)       # a 0.4-level step: not structure
    y0, y1, x0, x1 = BOX
    after = _beauty_with((y0, y1, x0 + 60, x1 + 60), fg=128.4, bg=128.0)
    rows, s = ed.compare(before, after, mask, {1: "ghost"})
    assert s["edge_threshold"] == ed.EDGE_ABS_FLOOR
    assert s["edge_threshold_from"] == "floor"
    assert rows[0]["verdict"] == "UNCHECKABLE"           # never HELD
    assert "little structure to check" in ed.report(rows, s)


def test_the_frame_border_is_not_charged_to_the_model():
    """An object the camera cuts off has a silhouette along the frame edge that no render
    will ever put a line under."""
    mask = _mask_with((0, H, 0, 120), 1)
    before = _beauty_with((0, H, 0, 120))
    rows, _ = ed.compare(before, before.copy(), mask, {1: "cut_wall"})
    assert rows[0]["verdict"] == "HELD"
    assert rows[0]["boundary_px"] < H + 2 * 120          # only the one interior run


def test_a_sliver_reports_NO_OUTLINE_rather_than_a_verdict():
    mask = _mask_with((100, 104, 100, 105), 1)
    before = _beauty_with((100, 104, 100, 105))
    rows, _ = ed.compare(before, before.copy(), mask, {1: "speck"})
    assert rows[0]["verdict"] == "NO-OUTLINE"


def test_ids_are_read_through_value_probes_own_codec():
    """One definition, both halves — a private copy of the palette decode in this file is
    how id 0's reservation drifts apart from the module that renders the mask."""
    m = _mask_with(BOX, 7)
    ids = vp.decode_ids(m.astype(np.int16))
    assert ids[100, 100] == 7 and ids[0, 0] == 0


def _write(tmp, name, arr):
    p = os.path.join(tmp, name)
    Image.fromarray(arr.astype(np.uint8)).save(p)
    return p


def test_cli_refuses_a_returned_frame_that_was_re_cropped(tmp_path):
    tmp = str(tmp_path)
    mask_p = _write(tmp, "m.png", _mask_with(BOX, 1))
    before_p = _write(tmp, "b.png", _beauty_with(BOX))
    after_p = _write(tmp, "a.png", np.full((H, H, 3), 40.0))     # square: different crop
    json_p = os.path.join(tmp, "m.json")
    json.dump({"source": {}, "ids": {"1": "slab"}}, open(json_p, "w"))
    with pytest.raises(ed.DriftError, match="DIFFERENT CROP"):
        ed._main(["edge_drift", before_p, after_p, mask_p, json_p])


def test_cli_accepts_a_pure_rescale_and_says_it_rescaled(tmp_path, capsys):
    tmp = str(tmp_path)
    mask_p = _write(tmp, "b.png", _mask_with(BOX, 1))            # stem must match `before`
    before_p = _write(tmp, "b_beauty.png", _beauty_with(BOX))
    big = Image.fromarray(_beauty_with(BOX).astype(np.uint8)).resize((W * 2, H * 2))
    after_p = os.path.join(tmp, "a.png")
    big.save(after_p)
    json_p = os.path.join(tmp, "b.json")
    json.dump({"source": {}, "ids": {"1": "slab"}}, open(json_p, "w"))
    rc = ed._main(["edge_drift", before_p, after_p, mask_p, json_p])
    assert rc == 0
    assert "aspect preserved" in capsys.readouterr().out


def test_cli_refuses_a_mask_from_a_different_build(tmp_path):
    """value_probe's provenance law, applied here: equal size is not equal camera."""
    tmp = str(tmp_path)
    mask_p = _write(tmp, "m.png", _mask_with(BOX, 1))
    before_p = _write(tmp, "b.png", _beauty_with(BOX))
    json_p = os.path.join(tmp, "m.json")
    json.dump({"source": {"blend": "some_other_round"}, "ids": {"1": "slab"}},
              open(json_p, "w"))
    with pytest.raises(ed.DriftError, match="MASK/BEFORE MISMATCH"):
        ed._main(["edge_drift", before_p, before_p, mask_p, json_p])


def test_cli_exit_code_is_1_when_something_drifted(tmp_path):
    """The gate contract: a caller that only reads the exit code still stops."""
    tmp = str(tmp_path)
    mask_p = _write(tmp, "b.png", _mask_with(BOX, 1))
    before_p = _write(tmp, "b_beauty.png", _beauty_with(BOX))
    y0, y1, x0, x1 = BOX
    after_p = _write(tmp, "a.png", _beauty_with((y0, y1, x0 + 40, x1 + 40)))
    json_p = os.path.join(tmp, "b.json")
    json.dump({"source": {}, "ids": {"1": "slab"}}, open(json_p, "w"))
    assert ed._main(["edge_drift", before_p, after_p, mask_p, json_p]) == 1
