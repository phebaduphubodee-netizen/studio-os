"""Tests for texture_check.

The metric has to be pinned on inputs whose answer is known by construction,
because every interesting reading it produces is a ratio between two frames
neither of which is a controlled stimulus. If it cannot tell a flat patch from a
grainy one of the SAME mean, nothing downstream of it means anything.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texture_check as TC  # noqa: E402


def _img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L")


def _flat(v=128, n=64):
    return _img(np.full((n, n), v, dtype=np.float32))


def _grainy(v=128, amp=20, n=64, seed=0):
    rng = np.random.default_rng(seed)
    return _img(np.full((n, n), v, dtype=np.float32) + rng.normal(0, amp, (n, n)))


def _ramp(v0=100, v1=160, n=64):
    return _img(np.tile(np.linspace(v0, v1, n, dtype=np.float32), (n, 1)))


def test_a_flat_patch_has_almost_no_high_frequency():
    im = _flat()
    assert TC.hf(TC.hf_field(im, 2.0), np.asarray(im, np.float32)) < 1e-3


def test_a_grainy_patch_has_much_more_than_a_flat_one_of_the_same_mean():
    a = np.asarray(_flat(), np.float32)
    b = np.asarray(_grainy(), np.float32)
    ha = TC.hf(TC.hf_field(_flat(), 2.0), a)
    hb = TC.hf(TC.hf_field(_grainy(), 2.0), b)
    assert hb > 50 * max(ha, 1e-6)


def test_a_smooth_GRADIENT_is_not_counted_as_texture():
    # This is the entire reason the module exists rather than reusing the
    # ladder's IQR/median: a lighting ramp across a surface must not read as
    # surface detail. IQR/median on this ramp is ~0.29; hf must be near zero.
    im = _ramp()
    assert TC.hf(TC.hf_field(im, 2.0), np.asarray(im, np.float32)) < 0.01


def test_the_measure_is_scale_invariant_in_brightness():
    # A dark surface and a bright one with the same RELATIVE grain must score
    # the same, or every dark object in the frame reads as smooth.
    bright = TC.hf(TC.hf_field(_grainy(200, 20), 2.0),
                   np.asarray(_grainy(200, 20), np.float32))
    dark = TC.hf(TC.hf_field(_grainy(100, 10), 2.0),
                 np.asarray(_grainy(100, 10), np.float32))
    assert abs(bright - dark) / bright < 0.15


def test_a_near_black_surface_returns_None_rather_than_a_huge_number():
    im = _grainy(2, 1)
    assert TC.hf(TC.hf_field(im, 2.0), np.asarray(im, np.float32)) is None


def test_coarser_sigma_sees_coarser_structure():
    # Fine noise mostly survives a small blur and is removed by a large one, so
    # its residual FALLS with sigma. Pins the direction the report reads scales in.
    im = _grainy(128, 20)
    a = np.asarray(im, np.float32)
    fine = TC.hf(TC.hf_field(im, 1.0), a)
    coarse = TC.hf(TC.hf_field(im, 6.0), a)
    assert coarse > fine  # residual GROWS as more is subtracted...
    # ...and the pair is what the report compares, never one alone.


# --- the dead-declaration audit -------------------------------------------

class _Mats:
    MAP_FILE = {"wood": ("d.png", "r.png", "n.png")}
    PALETTE = {"oak": ((0.5, 0.4, 0.3), 0.6, 0.0, "wood", 3.2),
               "paint": ((0.8, 0.8, 0.8), 0.75, 0.0, None, 0.0)}
    NORMAL_STRENGTH = {"oak": 0.4, "paint": 0.6}
    EMISSIVE = {"paint": 30.0}


def test_a_normal_strength_on_an_unmapped_row_is_reported():
    dead = TC.unreachable_normal_rows(_Mats)
    assert dead["NORMAL_STRENGTH"] == ["paint"]


def test_an_emissive_on_an_unmapped_row_is_NOT_reported():
    # EMISSIVE is applied before build_materials' early return, so it is legal
    # without a map. The first draft of the audit flagged it and was wrong.
    assert "EMISSIVE" not in TC.unreachable_normal_rows(_Mats)


def test_a_clean_table_reports_nothing():
    class Clean(_Mats):
        NORMAL_STRENGTH = {"oak": 0.4}
    assert TC.unreachable_normal_rows(Clean) == {}
