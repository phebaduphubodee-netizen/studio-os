"""P2r-6: the census must not be able to lie in the two shapes this repo's
instruments have lied in — a fabricated number where nothing was measured, and
a silent drop of what it could not attribute."""
import json
import os

import numpy as np
from PIL import Image

import map_census as MC
import value_probe as vp


def _write_mask(tmp_path, plane_ids, ids, has_image):
    """plane_ids: (H, W) int array of palette ids. Writes the png+json pair."""
    H, W = plane_ids.shape
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for i in np.unique(plane_ids):
        if i == 0:
            continue
        arr[plane_ids == i] = vp.id_to_srgb(int(i))
    p = str(tmp_path / "room_t.matmask.png")
    Image.fromarray(arr).save(p)
    with open(os.path.splitext(p)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump({"schema": "matmask@1", "source": {},
                   "ids": {str(k): v for k, v in ids.items()},
                   "has_image": has_image}, f)
    return p


def test_decode_roundtrips_the_palette():
    plane = np.zeros((4, 4, 3), dtype=np.uint8)
    plane[:] = vp.id_to_srgb(37)
    assert (MC.decode_ids(plane) == 37).all()


def test_census_shares_and_coverage(tmp_path):
    plane = np.zeros((100, 100), dtype=int)
    plane[:, :50] = 1          # textured oak, 50%
    plane[:, 50:80] = 2        # untextured plaster, 30%
    plane[:, 80:] = 3          # textured linen, 20%
    p = _write_mask(tmp_path, plane,
                    {1: "oak", 2: "plaster", 3: "linen"},
                    {"oak": True, "plaster": False, "linen": True})
    c = MC.census(p)
    assert abs(c["covered_pct"] - 70.0) < 0.01
    assert c["rows"][0]["material"] == "oak"
    short = [r for r in c["rows"] if not r["has_image"]]
    assert short[0]["material"] == "plaster"
    assert abs(short[0]["share_pct"] - 30.0) < 0.01


def test_background_pixels_are_unmeasured_not_covered(tmp_path):
    plane = np.zeros((10, 10), dtype=int)   # all id 0
    plane[0, 0] = 1
    p = _write_mask(tmp_path, plane, {1: "oak"}, {"oak": True})
    c = MC.census(p)
    assert c["covered_pct"] < 1.01          # one textured pixel only
    assert c["unmeasured_pct"] > 98.0       # the void is NAMED, never absorbed


def test_missing_mask_is_none_never_zero(tmp_path):
    assert MC.census(str(tmp_path / "nope.matmask.png")) is None


def test_report_names_the_shortfall(tmp_path):
    plane = np.ones((10, 10), dtype=int)
    plane[:, 5:] = 2
    p = _write_mask(tmp_path, plane, {1: "oak", 2: "plaster"},
                    {"oak": False, "plaster": False})
    lines = MC.report_lines(MC.census(p))
    assert "0.0%" in lines[0] or "0%" in lines[0]
    assert any("oak" in ln and "plaster" in ln for ln in lines[1:])


def test_mask_sidecar_naming():
    assert MC.mask_sidecar("out/room_x_eye_p9.png") == "out/room_x_eye_p9.matmask.png"
