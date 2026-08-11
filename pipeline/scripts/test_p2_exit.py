"""P2r-7: the exit harness must fail on what it claims to see — every rung gets
a synthetic control on BOTH sides (a defect it must catch, a non-defect it must
not call one), because the repo's recorded failure mode is instruments that can
only go green."""
import json
import os

import numpy as np
from PIL import Image

import p2_exit as PE


# ---------------------------------------------------------------- registry

def test_registry_boxes_are_valid_fractions():
    for key, spec in PE.CROPS.items():
        for bk in ("ours_box", "anchor_box"):
            if bk in spec:
                x0, y0, x1, y1 = spec[bk]
                assert 0.0 <= x0 < x1 <= 1.0, (key, bk)
                assert 0.0 <= y0 < y1 <= 1.0, (key, bk)
        assert spec["kind"] in ("octave_energy", "autocorr", "edge_profile",
                                "dup_shells"), key
        assert spec["declared"], key  # a box with no provenance can drift


def test_ql_frame_is_refused_as_could_not_run(tmp_path):
    p = tmp_path / "room_x_p9_ql.png"
    Image.new("RGB", (64, 64)).save(p)
    assert PE.run(str(p)) == 2


def test_missing_render_is_could_not_run(tmp_path):
    assert PE.run(str(tmp_path / "nope.png")) == 2


# ---------------------------------------------------------------- autocorr

def _panels(unique, W=360, H=120, pitch=90, seams=True, seed=1):
    """Synthetic veneer: broad vertical streaks per panel; optionally 2px dark
    seams at every pitch. unique=False tiles ONE panel's figure (the defect)."""
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W))
    chunks = pitch // 12 + 1

    def _fig():
        return np.repeat(rng.normal(0, 12, chunks), 12)[:pitch]

    base = _fig()
    for i in range(W // pitch):
        fig = base if not unique else _fig()
        img[:, i * pitch:(i + 1) * pitch] = 128 + fig[None, :]
    if seams:
        img[:, ::pitch] = 40.0
        img[:, 1::pitch] = 40.0
    return img


def test_tiled_figure_is_periodic():
    peak, lag, floor = PE.autocorr_peak(_panels(unique=False))
    assert peak > floor
    assert abs(lag - 90) <= 3  # the peak sits at the panel pitch


def test_unique_figure_with_real_seams_is_not_called_tiling():
    peak, _, floor = PE.autocorr_peak(_panels(unique=True))
    assert peak <= floor


def test_noise_is_not_periodic():
    rng = np.random.default_rng(3)
    peak, _, floor = PE.autocorr_peak(rng.normal(128, 20, (120, 360)))
    assert peak <= floor


def test_broad_gradient_is_not_periodic():
    """Regression pin: the first live p2r8 run read the shoulder of a smooth
    broad-correlation decay as PERIODIC at exactly min_lag. Real un-tiled wood
    (broad streaks, one slow tonal drift across the crop) must not trip the
    cut."""
    x = np.arange(360)[None, :].astype(np.float64)
    img = 128.0 + 30.0 * np.sin(2 * np.pi * x / 700.0)  # one broad half-wave
    peak, lag, floor = PE.autocorr_peak(np.repeat(img, 120, axis=0))
    assert peak == 0.0 or peak <= floor


# ---------------------------------------------------------------- edge

def _edge_img(width):
    """Vertical luminance transition of the given 10-90% extent, centred."""
    H, W = 96, 64
    y = np.arange(H)[:, None].astype(np.float64)
    if width <= 1:
        col = np.where(y < H // 2, 60.0, 200.0)
    else:
        col = 60.0 + 140.0 * np.clip((y - (H // 2 - width / 2)) / width, 0, 1)
    return np.repeat(col, W, axis=1)


def test_step_edge_reads_narrow_and_ramp_reads_wide():
    step = PE.edge_rise_width(_edge_img(1))
    ramp = PE.edge_rise_width(_edge_img(10))
    assert step <= 2.5
    assert ramp >= 6.0
    assert ramp > step


def test_edge_with_no_transition_is_nan():
    w = PE.edge_rise_width(np.full((64, 32), 128.0))
    assert w != w  # NaN — "no edge found" must not print like a number


# ---------------------------------------------------------------- dup shells

def _scene(tmp_path, objs):
    p = tmp_path / "s.scene.json"
    p.write_text(json.dumps({"schema": "scene-dump@2", "objects": objs}),
                 encoding="utf-8")
    return str(p)


def _rec(name, aabb=None):
    r = {"name": name}
    if aabb is not None:
        r["aabb"] = aabb
    return r


def test_coincident_pair_is_counted_and_cut(tmp_path):
    box = [[0.0, 0.0, 0.0], [0.5, 0.5, 1.0]]
    pairs, res = PE.rung_dup_shells(_scene(tmp_path, [
        _rec("mill__rail1__acq0", box),
        _rec("mill__rail1__acq10", [[r[0], r[1], r[2]] for r in box]),
        _rec("mill__rail1__acq2", [[1.0, 0.0, 0.0], [1.5, 0.5, 1.0]]),
    ]))
    assert res["coincident_pairs"] == 1
    assert pairs == [("mill__rail1__acq0", "mill__rail1__acq10")]


def test_different_items_never_pair_even_when_coincident(tmp_path):
    box = [[0.0, 0.0, 0.0], [0.5, 0.5, 1.0]]
    _, res = PE.rung_dup_shells(_scene(tmp_path, [
        _rec("mill__rail1__acq0", box), _rec("mill__rail2__acq0", box)]))
    assert res["coincident_pairs"] == 0


def test_missing_aabb_is_could_not_run_not_zero(tmp_path):
    pairs, res = PE.rung_dup_shells(_scene(tmp_path, [
        _rec("mill__rail1__acq0"), _rec("mill__rail1__acq1")]))
    assert pairs is None
    assert "could_not_run" in res  # the vacuous-zero class, refused by name


# ---------------------------------------------------------------- octave rung

def test_folded_cloth_scores_more_band_energy_than_flat(tmp_path):
    H, W = 400, 640
    y = np.arange(H)[:, None]
    flat = np.full((H, W), 180.0)
    folds = 180.0 + 40.0 * np.sin(2 * np.pi * y / 24.0) * np.ones((1, W))
    e_flat = PE.dc._octave_energy(flat)
    e_folds = PE.dc._octave_energy(folds)
    assert e_folds > 4 * max(e_flat, 1e-9)
