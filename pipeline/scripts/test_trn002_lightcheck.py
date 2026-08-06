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


def _two_frames(tmp_path, ours, tgt):
    grid = np.full(ours.shape[:2], 4, dtype=np.int32)
    png, js = _write_mask(tmp_path, grid)
    fo, ft = tmp_path / "o.png", tmp_path / "t.png"
    Image.fromarray(ours).save(fo)
    Image.fromarray(tgt).save(ft)
    return LC.ladder(str(fo), str(ft), png, js, erode_px=1, min_px=10)["rows"]["obj4"]


def test_dispersion_flag_fires_when_the_target_holds_foreign_content(tmp_path):
    ours = np.full((32, 32, 3), 128, dtype=np.uint8)
    tgt = ours.copy()
    tgt[:, :16] = 20                        # half the region is a foreign object
    row = _two_frames(tmp_path, ours, tgt)
    assert row["dispersed"] is True
    assert row["spread_ratio"] is None or row["spread_ratio"] > 1.6


def test_a_gradient_both_frames_see_is_not_called_foreign_content(tmp_path):
    """The separation this instrument owes: a wall running window-bright to
    corner-dark is dispersed and perfectly clean. Our frame shares the target's
    geometry, so it shows the same gradient — and spread_ratio near 1 is what
    says so. A flag that called this 'contaminated' would be naming a cause it
    cannot see."""
    ramp = np.linspace(40, 220, 32).astype(np.uint8)
    grad = np.repeat(ramp[None, :, None], 32, axis=0).repeat(3, axis=2)
    row = _two_frames(tmp_path, grad.copy(), grad.copy())
    assert row["dispersed"] is True, "a real gradient should still be reported"
    assert abs(row["spread_ratio"] - 1.0) < 0.05, (
        "both frames see it, so the ratio must say 'gradient', not 'foreign'")


# ---- LEVEL / SHAPE: the r24 split -------------------------------------------

def _row(err, n=1000, align="ALIGNED", spread=1.0):
    return {"ladder_error": err, "n_px": n, "alignment": align,
            "spread_ratio": spread}


def test_shape_is_invariant_to_the_choice_of_reference():
    """The whole point of the split. Re-normalising every row to a different
    object multiplies each ladder_error by one constant; LEVEL must move and
    SHAPE must not."""
    base = {"rows": {"a": _row(0.8), "b": _row(1.0), "c": _row(1.5),
                     "d": _row(0.6), "e": _row(1.2)}}
    k = 1.37
    shifted = {"rows": {n: _row(v["ladder_error"] * k)
                        for n, v in base["rows"].items()}}
    x, y = LC.level_and_shape(base), LC.level_and_shape(shifted)
    assert abs(y["level"] / x["level"] - k) < 1e-9
    assert abs(y["shape"] - x["shape"]) < 1e-9


def test_level_carries_a_uniform_error_and_shape_reports_none():
    """r24's actual failure: twenty-one rows fell together because the
    reference came up. That is ONE defect, and SHAPE must say so."""
    lad = {"rows": {n: _row(0.72) for n in "abcdef"}}
    ls = LC.level_and_shape(lad)
    assert abs(ls["level"] - 0.72) < 1e-9
    assert ls["shape"] < 1e-9


def test_untrustworthy_rows_are_dropped_by_the_instruments_own_verdicts():
    lad = {"rows": {"ok": _row(1.1), "moved": _row(4.9, align="OFF BY +6px"),
                    "dirty": _row(0.2, spread=7.1), "ok2": _row(0.9),
                    "ok3": _row(1.0), "ok4": _row(1.05)}}
    ls = LC.level_and_shape(lad)
    assert ls["dropped"] == ["dirty", "moved"]
    assert ls["n"] == 4


def test_pinned_membership_beats_self_selection():
    """A metric that re-chooses its own rows per frame can rank a change by
    which rows it decided to drop — the r24 bracket's seven-object subset."""
    lad = {"rows": {n: _row(e) for n, e in
                    (("a", 1.0), ("b", 1.1), ("c", 3.0), ("d", 0.9), ("e", 1.05))}}
    everything = LC.level_and_shape(lad)
    flattering = LC.level_and_shape(lad, rows={"a", "b", "d", "e"})
    assert flattering["shape"] < everything["shape"]
    assert flattering["n"] == 4 and everything["n"] == 5


def test_too_few_rows_returns_nothing_rather_than_a_number():
    assert LC.level_and_shape({"rows": {"a": _row(1.0), "b": _row(1.1)}}) is None


# ---- contact_profile: the test that validates itself -------------------------

import numpy as _np

_CAM = {"x_mm": 0.0, "y_mm": -8000.0, "z_mm": 1500.0, "yaw_deg": 0.0,
        "focal_mm": 38.841, "shift_x": 0.0, "shift_y": 0.0}
_WH = (400, 300)
_FOOT = ((0.0, -3000.0), (2000.0, 2000.0))
_BANDS = ((0, 150), (150, 300), (300, 600))
_REF = (600, 1400)


def _synthetic(field):
    """A floor filling the frame, id 1, shaded by `field(x_mm, y_mm)`.

    The object's own footprint is punched OUT of the floor id, because in a real
    frame those pixels belong to the object, not to the surface it stands on.
    Leaving them in is what made the first cut of this test return 1.000 on both
    faces: the whole footprint interior sits at d=0 and averages the field."""
    import trn002_geom as G
    (cx, cy), (sx, sy) = _FOOT
    lum = _np.zeros((_WH[1], _WH[0]), dtype=_np.float32)
    ids = _np.ones((_WH[1], _WH[0]), dtype=_np.int32)
    for v in range(_WH[1]):
        for u in range(_WH[0]):
            p = G.backproject(_CAM, (u + .5, v + .5), ("z", 6.0), _WH)
            if (p is None or p[1] > 0 or p[1] < -7000
                    or (abs(p[0] - cx) < sx / 2 and abs(p[1] - cy) < sy / 2)):
                ids[v, u] = 0
            else:
                lum[v, u] = field(p[0], p[1])
    return lum, ids


def test_a_directional_gradient_splits_the_two_faces_opposite_ways():
    """The self-validation. A pure ramp in x is brighter on one side of the
    object and dimmer on the other, so the -x and -y faces MUST disagree —
    which is how this test tells a beam apart from an occlusion."""
    lum, ids = _synthetic(lambda x, y: 1.0 + 0.00020 * x)
    out = LC.contact_profile(lum, ids, 1, _CAM, _FOOT, wh=_WH, min_px=20,
                             bands=_BANDS, ref_band=_REF, erode_px=0)
    a, b = out["-x"], out["+x"]
    assert a and b, (a, b)
    assert (a[0] - 1.0) * (b[0] - 1.0) < 0, (a[0], b[0])


def test_a_radial_dip_at_the_edge_darkens_both_faces():
    """What occlusion looks like: a function of distance from the object only."""
    def f(x, y):
        d = max(abs(x) - 1000.0, 0.0, abs(y + 3000.0) - 1000.0)
        return 0.4 + 0.6 * min(d / 600.0, 1.0)
    lum, ids = _synthetic(f)
    out = LC.contact_profile(lum, ids, 1, _CAM, _FOOT, wh=_WH, min_px=20,
                             bands=_BANDS, ref_band=_REF, erode_px=0)
    # -y is legitimately absent: the fixture camera is level at z=1500 with a
    # 19.2 deg half-FOV, so the floor between it and the object falls below the
    # frame. A face with no pixels must report None, never a number.
    assert out["-y"] is None, out["-y"]
    for face in ("-x", "+x", "+y"):
        assert out[face][0] < 0.75, (face, out[face])
        assert out[face][0] < out[face][2], (face, out[face])


def test_a_flat_field_reports_no_contact_effect():
    lum, ids = _synthetic(lambda x, y: 0.5)
    out = LC.contact_profile(lum, ids, 1, _CAM, _FOOT, wh=_WH, min_px=20,
                             bands=_BANDS, ref_band=_REF, erode_px=0)
    for face, vals in out.items():
        assert vals is None or all(abs(v - 1.0) < 1e-6 for v in vals
                                   if v is not None), (face, vals)


def test_a_band_with_too_few_pixels_is_None_rather_than_a_number():
    lum, ids = _synthetic(lambda x, y: 0.5)
    out = LC.contact_profile(lum, ids, 1, _CAM, _FOOT, wh=_WH, min_px=10**6,
                             bands=_BANDS, ref_band=_REF, erode_px=0)
    assert all(v is None for v in out.values()), out
