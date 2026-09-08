"""luma_range — a flat frame reads low, a keyed frame reads high, and a frame
smaller than the measuring size is refused (exit 2) unless the playblast use is
named. Synthetic images so the test owns its answer."""
import os
import sys

import numpy as np
import pytest
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import luma_range as lr  # noqa: E402


def _png(tmp_path, name, arr):
    p = tmp_path / name
    Image.fromarray(arr.astype(np.uint8), "RGB").save(p)
    return str(p)


def test_flat_grey_has_ratio_one(tmp_path):
    a = np.full((900, 1600, 3), 128)
    r = lr.measure(_png(tmp_path, "flat.png", a))
    assert r["ratio"] == pytest.approx(1.0)
    assert r["measured_at"] == [1600, 900]


def test_keyed_frame_reads_high(tmp_path):
    a = np.full((900, 1600, 3), 40)
    a[:, :400] = 230                      # a quarter of the frame in sun
    r = lr.measure(_png(tmp_path, "keyed.png", a))
    assert r["ratio"] == pytest.approx(230 / 40, rel=0.02)


def test_larger_frame_is_resized_to_the_long_edge(tmp_path):
    a = np.full((1800, 2400, 3), 100)
    r = lr.measure(_png(tmp_path, "big.png", a))
    assert r["measured_at"] == [1600, 1200]
    assert r["native_size"] == [2400, 1800]


def test_smaller_frame_refused_unless_playblast_named(tmp_path):
    a = np.full((450, 800, 3), 100)
    p = _png(tmp_path, "small.png", a)
    with pytest.raises(RuntimeError):
        lr.measure(p)
    r = lr.measure(p, allow_upscale=True)
    assert r["measured_native"] is True
    assert lr.main([p]) == 2
    assert lr.main([p, "--allow-upscale"]) == 1     # ratio 1.0 under the 5.0 floor


def test_exit_codes(tmp_path):
    a = np.full((900, 1600, 3), 40)
    a[:, :400] = 230
    p = _png(tmp_path, "keyed.png", a)
    assert lr.main([p]) == 0
    assert lr.main([p, "--min", "9"]) == 1
    assert lr.main([str(tmp_path / "missing.png")]) == 2
