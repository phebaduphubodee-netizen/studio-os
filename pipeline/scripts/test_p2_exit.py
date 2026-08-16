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
        for bk in ("ours_box", "anchor_box", "control_box"):
            if bk in spec:
                x0, y0, x1, y1 = spec[bk]
                assert 0.0 <= x0 < x1 <= 1.0, (key, bk)
                assert 0.0 <= y0 < y1 <= 1.0, (key, bk)
        assert spec["kind"] in ("octave_energy", "autocorr", "edge_profile",
                                "dup_shells", "shadow_line", "shadow_contact"), key
        assert spec["declared"], key  # a box with no provenance can drift


def test_an_absence_rung_carries_its_own_positive_control():
    """A rung whose PASS is 'we found nothing' must declare the control that proves it
    could have found something. Two rungs in this file's history reported clean while
    being structurally unable to see the case they were named for; this test makes the
    control a property of the registry rather than of whoever ran it that day."""
    for key, spec in PE.CROPS.items():
        if spec["kind"] == "shadow_line":
            assert "control_box" in spec, key
            assert spec["ours_box"] != spec["control_box"], key
        if spec["kind"] == "shadow_contact":
            assert "control_contact" in spec, key
            assert tuple(spec["contact"]) != tuple(spec["control_contact"]), key


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


def test_a_two_tile_repeat_is_caught():
    """D-056, the rung's blind spot for five rounds. `wood_boards` asks about "TWO
    adjacent veneer panels" carrying the same figure — and a crop framing exactly two
    tiles repeats at lag W/2, which the old search bound (hi = W//2) excluded by one.
    So the rung printed `no peak above floor` every round while being unable to see its
    own headline case, and a cross-vendor critic filed the tiling item six times against
    that clean. This is the control that must never go quiet again."""
    peak, lag, floor = PE.autocorr_peak(_panels(unique=False, W=360, pitch=180))
    assert peak > floor, "a two-panel crop of ONE repeated figure must read periodic"
    assert abs(lag - 180) <= 4


def test_widening_the_search_did_not_make_noise_periodic():
    """The other half of D-056: the floor is measured through the SAME widened path,
    so a longer search must not manufacture a peak out of shuffled noise."""
    rng = np.random.default_rng(11)
    peak, _, floor = PE.autocorr_peak(rng.normal(128, 20, (120, 480)))
    assert peak <= floor


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


def test_rug_edge_cut_is_declared_above_the_whole_step_band():
    """P2r-3 graduated rug_edge from report-only to a declared cut. The cut
    must sit strictly above what BOTH step controls read (ideal 0-1 px,
    resample-sharp ~1-2 px) so a die-cut edge can never pass, and at/below the
    rolled control so a real rollover never fails."""
    cut = PE.CROPS["rug_edge"]["cut_rise_px"]
    step = PE.edge_rise_width(_edge_img(1))
    ramp = PE.edge_rise_width(_edge_img(10))
    assert step < cut, "a sharp step must break the cut"
    assert ramp >= cut, "a rolled edge must hold the cut"


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


# ------------------------------------------------------- shadow_contact rung

def _matmask_png(path, ids_arr, names):
    """Write a matmask pair the way the build does: ids in value_probe's palette
    plus the sidecar naming them."""
    import value_probe as vp
    h, w = ids_arr.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for i in np.unique(ids_arr):
        rgb[ids_arr == i] = vp.id_to_srgb(int(i))
    Image.fromarray(rgb).save(str(path) + ".matmask.png")
    json.dump({"schema": 1, "ids": {str(v): k for k, v in names.items()}},
              open(str(path) + ".matmask.json", "w", encoding="utf-8"))


def _two_cloth_frame(tmp_path, dip, stem="room_x_p1"):
    """A frame with one cloth lying on another at row 480, plus a pillow lying on
    it at row 800 that ALWAYS casts a line (the positive control). `dip` is how
    many codes the cloth boundary undershoots — 0 is a bare step with no thickness.

    THE LONG EDGE IS 1600 ON PURPOSE: `dc._norm` upscales anything smaller, and
    LANCZOS rings at a hard step — a synthetic at 320px reads a 1.0 ratio for a
    step with no dip at all, i.e. the resampler manufactures the very undershoot
    the rung is looking for. (Checked on the real frame too, where it does not
    bite: native 2400 reads 39.0%/88.8% and the LE1600 normalise 36.4%/88.2%.)"""
    H, W = 1200, 1600
    L = np.full((H, W), 190.0)
    L[480:, :] = 150.0                                  # the cloth-on-cloth step
    if dip:
        L[476:480, :] = 150.0 - dip
    L[800:, :] = 175.0                                  # pillow region below
    L[792:800, :] = 175.0 - 45.0                        # control line, always deep
    rgb = np.repeat(np.clip(L, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
    p = tmp_path / f"{stem}.png"
    Image.fromarray(rgb).save(p)
    ids = np.full((H, W), 9, dtype=np.int32)            # bed_throw
    ids[:480, :] = 7                                    # bed_duvet above it
    ids[800:, :] = 11                                   # bed_pillow at the bottom
    _matmask_png(str(p).rsplit(".", 1)[0], ids,
                 {"bed_duvet": 7, "bed_throw": 9, "bed_pillow": 11})
    return p


_CONTACT_SPEC = {
    "kind": "shadow_contact",
    "contact": ("bed_duvet", "bed_throw"),
    "control_contact": ("bed_throw", "bed_pillow"),
    "cut_ratio": 0.5,
}


def _run_contact(p, spec=None):
    ours = PE._norm_img(str(p))
    return PE.rung_shadow_contact(ours, str(p), spec or _CONTACT_SPEC)


def test_contact_rung_calls_a_cast_line_an_edge(tmp_path):
    _, _, res = _run_contact(_two_cloth_frame(tmp_path, dip=40))
    assert res["ran"], res
    assert res["ratio"] >= 0.5, res


def test_contact_rung_calls_a_bare_step_no_line(tmp_path):
    """A material change with no thickness: same two plateaus, no undershoot."""
    _, _, res = _run_contact(_two_cloth_frame(tmp_path, dip=0))
    assert res["ran"], res
    assert res["ratio"] < 0.5, res


def test_contact_rung_refuses_when_the_named_material_is_absent(tmp_path):
    """The p2r41 defect, made unrepeatable: a site that names a contact which is
    not in the frame must be COULD NOT RUN, never a confident absence."""
    spec = dict(_CONTACT_SPEC, contact=("bed_coverlet", "bed_throw"))
    co, cc, res = _run_contact(_two_cloth_frame(tmp_path, dip=0), spec)
    assert co is None and cc is None
    assert "could_not_run" in res and "bed_coverlet" in res["could_not_run"]


def test_contact_rung_refuses_without_a_matmask(tmp_path):
    p = tmp_path / "room_x_p2.png"
    Image.new("RGB", (1600, 1200), (180, 180, 180)).save(p)
    co, _, res = PE.rung_shadow_contact(PE._norm_img(str(p)), str(p), _CONTACT_SPEC)
    assert co is None and "matmask" in res["could_not_run"]


def test_contact_rung_reports_sibling_edges_of_the_same_object(tmp_path):
    spec = dict(_CONTACT_SPEC,
                sibling_contacts=(("bed_throw", "bed_pillow"),))
    _, _, res = _run_contact(_two_cloth_frame(tmp_path, dip=40), spec)
    assert res["siblings"] and res["siblings"][0]["pct"] > 90.0


def test_the_registry_contact_site_is_named_not_typed():
    """A shadow_contact entry must name its site and its control as material pairs,
    they must differ, and the retired typed box must stay on the record with the
    reason it was retired — a retired box with no record gets re-typed."""
    for key, spec in PE.CROPS.items():
        if spec["kind"] != "shadow_contact":
            continue
        assert len(spec["contact"]) == 2, key
        assert len(spec["control_contact"]) == 2, key
        assert tuple(spec["contact"]) != tuple(spec["control_contact"]), key
        assert "ours_box" not in spec, f"{key}: a derived site must not carry a box"
        rb = spec.get("retired_box")
        assert rb and rb.get("why"), key
