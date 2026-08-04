"""Tests for trn002_lightcheck — pure, no bpy, no real frames.

The load-bearing test is the codec round-trip: this module DECODES a mask that
id_mask.py ENCODES, and the two live in different files. value_probe owns the
codec and both must go through it — a private copy is how a mask starts
decoding to plausible-looking garbage after the original changes. (This test
was written because the first draft of the decoder did exactly that.)
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn002_lightcheck as LC  # noqa: E402
import value_probe as VP        # noqa: E402


def _write_mask(tmp_path, ids_grid):
    """Encode an id grid the way id_mask.py does, and write its sidecar."""
    h, w = ids_grid.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for i in np.unique(ids_grid):
        if i == 0:
            continue
        rgb[ids_grid == i] = VP.id_to_srgb(int(i))
    png = tmp_path / "m.png"
    Image.fromarray(rgb).save(png)
    names = {str(int(i)): f"SM_TRN002_obj{int(i)}" for i in np.unique(ids_grid) if i}
    (tmp_path / "m.json").write_text(
        json.dumps({"source": {"blend": "t"}, "ids": names}), encoding="utf-8")
    return str(png), str(tmp_path / "m.json")


def test_decode_round_trips_value_probes_encoder(tmp_path):
    grid = np.zeros((16, 16), dtype=np.int32)
    grid[:8, :8] = 3
    grid[:8, 8:] = 41
    grid[8:, :] = 200
    png, js = _write_mask(tmp_path, grid)
    ids, names = LC.decode_mask(png, js)
    assert np.array_equal(ids, grid), "decoded ids differ from encoded ids"
    assert names[3] == "SM_TRN002_obj3"


def test_sidecar_provenance_block_is_not_mistaken_for_an_id(tmp_path):
    """id_mask writes {"source": {...}, "ids": {...}}; a decoder that iterates
    the top level crashes on 'source'. It did."""
    grid = np.full((8, 8), 5, dtype=np.int32)
    png, js = _write_mask(tmp_path, grid)
    _, names = LC.decode_mask(png, js)
    assert set(names) == {5}


def test_erode_removes_the_boundary_ring():
    m = np.zeros((10, 10), dtype=bool)
    m[2:8, 2:8] = True                     # 6x6 = 36
    assert LC.erode(m, 1).sum() == 16      # 4x4
    assert LC.erode(m, 2).sum() == 4       # 2x2


def test_identical_frames_give_a_flat_ladder(tmp_path):
    """A frame compared against itself must report ladder_error 1.0 for every
    measurable row — if it does not, the normalisation is wrong and every real
    reading is wrong by the same amount."""
    rng = np.random.default_rng(0)
    h = w = 64
    grid = np.zeros((h, w), dtype=np.int32)
    grid[:32, :] = 1
    grid[32:, :] = 2
    png, js = _write_mask(tmp_path, grid)
    img = (rng.uniform(40, 200, (h, w, 3))).astype(np.uint8)
    img[32:] = (img[32:] * 0.5).astype(np.uint8)      # a real ladder step
    f = tmp_path / "f.png"
    Image.fromarray(img).save(f)
    out = LC.ladder(str(f), str(f), png, js, erode_px=1, min_px=10, dirty=9.9)
    for name, row in out["rows"].items():
        if "ladder_error" in row:
            assert abs(row["ladder_error"] - 1.0) < 1e-6, (name, row)


def test_too_small_a_region_is_unmeasurable_not_noise(tmp_path):
    grid = np.zeros((16, 16), dtype=np.int32)
    grid[:2, :2] = 7                       # 4 px, erodes to nothing
    grid[4:, 4:] = 9
    png, js = _write_mask(tmp_path, grid)
    img = np.full((16, 16, 3), 128, dtype=np.uint8)
    f = tmp_path / "f.png"
    Image.fromarray(img).save(f)
    out = LC.ladder(str(f), str(f), png, js, erode_px=1, min_px=20)
    assert "UNMEASURABLE" in out["rows"]["obj7"]["status"]
    assert "ours" in out["rows"]["obj9"]


def test_contamination_flag_fires_on_a_dirty_region(tmp_path):
    """Where the target holds an object we do not model, the sample is not that
    surface — high spread must FLAG rather than average in."""
    grid = np.full((32, 32), 4, dtype=np.int32)
    png, js = _write_mask(tmp_path, grid)
    ours = np.full((32, 32, 3), 128, dtype=np.uint8)
    tgt = ours.copy()
    tgt[:, :16] = 20                        # half the region is a foreign object
    fo, ft = tmp_path / "o.png", tmp_path / "t.png"
    Image.fromarray(ours).save(fo)
    Image.fromarray(tgt).save(ft)
    out = LC.ladder(str(fo), str(ft), png, js, erode_px=1, min_px=10)
    assert out["rows"]["obj4"]["contaminated"] is True
