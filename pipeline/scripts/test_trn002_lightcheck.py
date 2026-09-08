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


# ---- SHAPE_FLAT: the blind spot px weighting has ------------------------------

def test_px_weighting_hides_an_error_the_objects_carry():
    """r27's real shape, in miniature. Two huge planes agree; four small
    objects are wrong by 1.5x in both directions. The px-weighted SHAPE says
    the frame is nearly right, which it is — and says nothing about the objects,
    which is the question a viewer is asking.

    Measured on r27's own artifacts, the real numbers were 0.2000 weighted
    against 0.3359 flat."""
    lad = {"rows": {"wall": _row(1.0, n=150000), "ceiling": _row(1.0, n=100000),
                    "desk": _row(1.5, n=800), "chair": _row(0.67, n=800),
                    "lamp": _row(1.5, n=600), "vase": _row(0.67, n=600)}}
    ls = LC.level_and_shape(lad)
    assert ls["shape"] < 0.05, "the frame IS right, and SHAPE should say so"
    assert ls["shape_flat"] > 0.3, "the objects are NOT, and something must say so"
    assert ls["weight_gap"] > 6


def test_both_spreads_are_still_invariant_to_the_reference():
    """SHAPE_FLAT would be worthless if it could be moved by re-normalising."""
    base = {"rows": {"a": _row(0.8, n=10), "b": _row(1.0, n=900),
                     "c": _row(1.5, n=50), "d": _row(0.6, n=7000),
                     "e": _row(1.2, n=300)}}
    k = 0.61
    shifted = {"rows": {n: _row(v["ladder_error"] * k, n=v["n_px"])
                        for n, v in base["rows"].items()}}
    x, y = LC.level_and_shape(base), LC.level_and_shape(shifted)
    assert abs(y["shape"] - x["shape"]) < 1e-9
    assert abs(y["shape_flat"] - x["shape_flat"]) < 1e-9


# ---- SLOPE / RHO: the two readings a spread of ratios cannot give -------------

def _vrow(o, t, n=1000, align="ALIGNED", spread=1.0):
    return {"ours": o, "target": t, "ladder_error": o / t, "n_px": n,
            "alignment": align, "spread_ratio": spread}


_TGT = (0.52, 0.44, 0.37, 0.30, 0.21, 0.15, 0.09)


def test_a_uniform_exposure_error_is_not_a_compression():
    """THE NEGATIVE CONTROL, and the reason SLOPE exists. Every object at 0.70x
    the target is one exposure scalar: LEVEL catches it, and SLOPE and RHO must
    both come back perfect. A metric that called this 'flat' would send the lane
    to repaint materials over a mistake in one number."""
    lad = {"rows": {f"o{i}": _vrow(0.70 * t, t) for i, t in enumerate(_TGT)}}
    co = LC.contrast_and_order(lad)
    assert abs(co["slope"] - 1.0) < 1e-9
    assert abs(co["rho"] - 1.0) < 1e-9
    assert abs(co["range_ours"] - co["range_target"]) < 1e-9
    assert abs(LC.level_and_shape(lad)["level"] - 0.70) < 1e-9


def test_a_compressed_frame_is_caught_with_the_order_intact():
    """Ours = target^0.5 rescaled: the exact 'every object is the same white
    plastic' failure. The ORDER is perfect, so RHO alone would pass it."""
    import numpy as _n
    lad = {"rows": {f"o{i}": _vrow(0.5 * t ** 0.5, t) for i, t in enumerate(_TGT)}}
    co = LC.contrast_and_order(lad)
    assert abs(co["slope"] - 0.5) < 1e-6
    assert abs(co["rho"] - 1.0) < 1e-9, "order is intact — RHO cannot catch this"
    assert co["range_ours"] < co["range_target"]
    assert _n.isfinite(co["slope"])


def test_a_scrambled_order_is_caught_with_the_range_intact():
    """The complement: same values, wrong objects. SLOPE degrades but RHO is
    the reading that names it."""
    shuffled = [_TGT[i] for i in (3, 0, 6, 1, 5, 2, 4)]
    lad = {"rows": {f"o{i}": _vrow(shuffled[i], t) for i, t in enumerate(_TGT)}}
    co = LC.contrast_and_order(lad)
    assert abs(co["range_ours"] - co["range_target"]) < 1e-9, "same values"
    assert co["rho"] < 0.6


def test_slope_and_rho_survive_a_change_of_reference():
    """Reference-invariance is claimed in the docstring; a claim in a docstring
    is not a property."""
    lad = {"rows": {f"o{i}": _vrow(0.5 * t ** 0.5, t) for i, t in enumerate(_TGT)}}
    scaled = {"rows": {k: _vrow(v["ours"] * 1.9, v["target"] * 0.4)
                       for k, v in lad["rows"].items()}}
    a, b = LC.contrast_and_order(lad), LC.contrast_and_order(scaled)
    assert abs(a["slope"] - b["slope"]) < 1e-9
    assert abs(a["rho"] - b["rho"]) < 1e-9


def test_the_extremes_are_named_so_a_two_point_claim_can_be_checked():
    lad = {"rows": {f"o{i}": _vrow(t, t) for i, t in enumerate(_TGT)}}
    co = LC.contrast_and_order(lad)
    assert co["ours_extremes"] == ["o0", "o6"]
    assert co["target_extremes"] == ["o0", "o6"]


def test_untrustworthy_rows_are_dropped_by_contrast_too():
    """ONE definition of trustworthy, shared. A row SHAPE drops and SLOPE keeps
    would let the two disagree for a reason neither reports."""
    lad = {"rows": {f"o{i}": _vrow(t, t) for i, t in enumerate(_TGT)}}
    lad["rows"]["moved"] = _vrow(9.0, 0.01, align="OFF BY +6px")
    lad["rows"]["dirty"] = _vrow(9.0, 0.01, spread=7.1)
    co = LC.contrast_and_order(lad)
    assert co["n"] == len(_TGT)
    assert "moved" not in co["used"] and "dirty" not in co["used"]


def test_spearman_averages_ties_instead_of_taking_input_order():
    assert abs(LC.spearman([1, 2, 2, 3], [1, 2, 2, 3]) - 1.0) < 1e-12
    assert abs(LC.spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1.0) < 1e-12
    assert abs(LC.spearman([1, 1, 1, 1], [4, 3, 2, 1])) < 1e-12


# ---- by_material: light and albedo, separated by an identity -----------------

def test_within_one_material_a_spread_can_only_be_light():
    """Six objects on two materials. Ours modulates each material half as hard
    as the target does, while the two materials sit at exactly the target's own
    means — so this is a pure LIGHT failure and the split must say so."""
    rows = {}
    # exact reciprocal pairs, so each material's geometric mean is its own
    # value and log(ours span) / log(target span) is exactly 0.5 by algebra
    for i, (o, t) in enumerate([(1.3, 1.69), (1.0, 1.0), (1 / 1.3, 1 / 1.69)]):
        rows[f"oak{i}"] = _vrow(0.20 * o, 0.20 * t)
        rows[f"pnt{i}"] = _vrow(0.50 * o, 0.50 * t)
    bm = LC.by_material({"rows": rows},
                        material_of=lambda k: "veneer_oak" if k.startswith("oak")
                        else "paint_white")
    assert abs(bm["light_span"] - 0.5) < 1e-9
    assert bm["n_materials_spanned"] == 2
    assert abs(bm["materials"]["veneer_oak"]["target_mean"] - 0.20) < 1e-9


def test_a_material_the_target_does_not_modulate_is_excluded_not_divided_by():
    """log(1.02)/log(1.0) is infinity dressed as evidence."""
    rows = {"a": _vrow(0.30, 0.40), "b": _vrow(0.306, 0.40),
            "c": _vrow(0.20, 0.30), "d": _vrow(0.34, 0.12)}
    bm = LC.by_material({"rows": rows},
                        material_of=lambda k: "flat" if k in "ab" else "lit")
    assert "light_span" not in bm["materials"]["flat"]
    assert bm["n_materials_spanned"] == 1


def test_a_name_the_material_table_refuses_is_skipped_not_guessed():
    def refusing(k):
        if k == "mystery":
            raise KeyError(k)
        return "paint_white"
    rows = {"a": _vrow(0.30, 0.40), "b": _vrow(0.20, 0.30),
            "mystery": _vrow(0.9, 0.01)}
    bm = LC.by_material({"rows": rows}, material_of=refusing)
    assert list(bm["materials"]) == ["paint_white"]
    assert bm["materials"]["paint_white"]["objects"] == ["a", "b"]


def test_the_real_material_table_answers_for_the_lane_s_own_objects():
    """by_material's default is trn002_materials.material_for. If that import
    or those names ever move, this reading goes silently empty."""
    rows = {n: _vrow(0.3, 0.4) for n in
            ("desk", "console", "floor_planks", "left_wall", "bed_platform")}
    bm = LC.by_material({"rows": rows})
    assert "veneer_oak" in bm["materials"]
    assert set(bm["materials"]["veneer_oak"]["objects"]) == {"desk", "console"}


# ---- the mask coverage guard -------------------------------------------------

def test_a_mass_the_mask_never_saw_is_reported_not_skipped(tmp_path):
    """The defect: `id_mask.py` filters by name substring, the cloth solver
    emitted `duvet` without the SM_TRN002_ prefix, and thirty-one rounds of
    per-object measurement silently excluded the three largest soft-goods
    objects in the frame. A filter that matches nothing just returns fewer
    rows."""
    spec = tmp_path / "s.json"
    spec.write_text(json.dumps({"camera": {}, "masses": [
        {"name": "bed_platform", "c": [0, 0, 0]}, {"name": "duvet", "c": [0, 0, 0]},
        {"name": "throw_woven", "c": [0, 0, 0]}]}), encoding="utf-8")
    absent = LC.absent_from_mask(str(spec), {1: "SM_TRN002_bed_platform"})
    assert absent == ["duvet", "throw_woven"]
    assert LC.absent_from_mask(None, {1: "x"}) is None


def test_a_cavity_takes_its_depth_from_the_host_it_names(tmp_path):
    """r29's arch pocket has no `c`, and reading one raised — which is how a
    live instrument stops running on the round that changed the geometry. A
    mouth is at its host's face, so the depth is derived, not typed."""
    spec = tmp_path / "s.json"
    spec.write_text(json.dumps({
        "camera": {"x_mm": 0.0, "y_mm": -1000.0, "z_mm": 0.0},
        "masses": [{"name": "petcave", "c": [0, 0, 0]},
                   {"name": "petcave_mouth", "host": "petcave"},
                   {"name": "orphan"}]}), encoding="utf-8")
    d = LC.depths_from_spec(str(spec), {1: "SM_TRN002_petcave",
                                        2: "SM_TRN002_petcave_mouth",
                                        3: "SM_TRN002_orphan"})
    assert abs(d[1] - 1000.0) < 1e-9 and abs(d[2] - 1000.0) < 1e-9
    assert 3 not in d, "a mass with no derivable centre is left out, not invented"


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


# ------------------------------------------------- aim, as a claim (r30) --
# Three emitters in this lane have been found firing 180 degrees from where
# their own comment said. An Euler triple can only be believed; a place can be
# checked, so every aimed emitter now declares WHERE IT POINTS and this pins it.

def test_every_aimed_emitter_points_where_it_says_it_does():
    import trn002_light as L
    checked = 0
    for f in L.plan():
        e = L.aim_error_deg(f)
        if e is None:
            continue
        checked += 1
        assert e < 45.0, f"{f['name']} points {e:.1f} deg from its own aim_at_mm"
    assert checked >= 3, f"only {checked} emitters declare an aim"


def test_every_area_emitter_declares_an_aim():
    """No opt-out. A rule that names the emitters it applies to will exempt the
    next one — R9b's lesson, and this lane's fourth aimed light is the one this
    guard exists for."""
    import trn002_light as L
    missing = [f["name"] for f in L.plan()
               if f.get("kind") == "AREA" and "aim_at_mm" not in f]
    assert not missing, f"AREA emitters with no declared aim: {missing}"


def test_the_normal_is_computed_and_not_assumed():
    """Blender emits along -Z and applies XYZ in order. These four are the
    cases the lane actually got wrong."""
    import trn002_light as L
    for rot, want in (((0, 0, 0), (0, 0, -1)),
                      ((90, 0, 0), (0, 1, 0)),
                      ((-90, 0, 0), (0, -1, 0)),
                      ((90, 0, -90), (1, 0, 0))):
        got = L.normal_of(rot)
        assert all(abs(a - b) < 1e-9 for a, b in zip(got, want)), (rot, got, want)


def test_a_light_fired_backwards_is_caught():
    """Negative control: the exact r30 defect — +90 where -90 was meant.

    Built from a literal rather than from CLOSET, because CLOSET no longer HAS
    a typed rot_deg: it declares a place and `rot_for_aim` solves the angles, so
    the defect is now unrepresentable there. The control has to keep existing
    anyway — the guard's whole value is that it still fires on any emitter that
    goes back to typing its Euler."""
    import trn002_light as L
    bad = {"kind": "AREA", "loc_mm": (0.0, 0.0, 0.0),
           "aim_at_mm": (0.0, -1000.0, 0.0), "rot_deg": (90.0, 0.0, 0.0)}
    assert L.aim_error_deg(bad) > 150.0, L.aim_error_deg(bad)


def test_an_aim_solved_from_a_place_round_trips():
    """rot_for_aim then normal_of must return the direction asked for, on aims
    that are not axis-aligned — the first cut of the solver was 180 deg out and
    only a non-trivial aim shows it."""
    import trn002_light as L
    for loc, aim in (((-3400.0, 400.0, 2500.0), (-3400.0, 2400.0, 700.0)),
                     ((0.0, 0.0, 0.0), (1000.0, -500.0, -800.0)),
                     ((100.0, 200.0, 300.0), (-900.0, 1200.0, 100.0))):
        e = L.aim_error_deg({"kind": "AREA", "loc_mm": loc, "aim_at_mm": aim,
                             "rot_deg": L.rot_for_aim(loc, aim)})
        assert e < 1e-6, (loc, aim, e)
