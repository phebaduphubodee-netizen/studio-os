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
        # WHAT THIS ROW HAS TO BE IS PAIRS, NOT TWO OF THEM. The assertion here
        # read `len(spec["contact"]) == 2` and so pinned the NUMBER OF PAIRS at
        # whatever it happened to be the day it was written. That is a count
        # with no meaning: the registry's own comment says a site is named and
        # "lists the material pairs that can carry it", one per leg — so the
        # test forbade the very thing the field is for, and adding the acquired
        # leg's dressing (`acq_bed_throw`, 2026-08-26) failed it. Pin the
        # invariant the docstring actually states instead.
        for field in ("contact", "control_contact"):
            pairs = PE._pairs(spec[field])
            assert pairs, f"{key}: {field} names no pair"
            for p in pairs:
                assert len(p) == 2 and all(isinstance(m, str) and m
                                           for m in p), f"{key}: {field} {p!r}"
                assert p[0] != p[1], f"{key}: {field} {p!r} is a material on itself"
        assert (set(PE._pairs(spec["contact"]))
                .isdisjoint(PE._pairs(spec["control_contact"]))), key
        assert "ours_box" not in spec, f"{key}: a derived site must not carry a box"
        rb = spec.get("retired_box")
        assert rb and rb.get("why"), key


# ------------------------------------------------- the subject guard (p2r79)
#
# WHAT THESE PIN, and it is a defect this harness shipped rather than a
# hypothetical: every `ours_box` is a FRACTION OF THE FRAME, the owner adopted a
# different camera on 2026-08-26 (D-152), and every frozen box slid onto other
# objects in the same move without a single rung noticing. Measured after the
# fact from the matmask: `rug_edge` held 0.8% rug at p2r77 and 3.9% at p2r78rc
# while printing ROLLED (pass) both times — the first reading was the BED
# PLINTH's edge, the second was open pile with no edge in the box at all.
# `duvet_fold` was 21% then 15% duvet, the rest curtain and floor, so "2.1x the
# delivered comforter" was largely curtain pleats.

def _subject_frame(tmp_path, subject_frac, stem="room_x_subj"):
    """A frame whose declared box is `subject_frac` its own subject and the rest
    a decoy material, with the luminance identical either way — so anything the
    guard catches, it catches from the MASK and not from the picture."""
    H, W = 1200, 1600
    rng = np.random.default_rng(3)
    L = 150.0 + 25.0 * rng.standard_normal((H, W))
    rgb = np.repeat(np.clip(L, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
    p = tmp_path / f"{stem}.png"
    Image.fromarray(rgb).save(p)
    ids = np.full((H, W), 5, dtype=np.int32)            # decoy everywhere
    cut = int(H * subject_frac)
    ids[:cut, :] = 7                                    # subject at the top
    _matmask_png(str(p).rsplit(".", 1)[0], ids,
                 {"the_subject": 7, "the_decoy": 5})
    return p


def _run_only(p, spec, tag="t"):
    """Run the harness with ONE synthetic rung in the registry, restoring it
    afterwards whatever happens.

    THE ARCHIVE DIRS ARE REDIRECTED INTO tmp_path TOO. `PE.run` saves every crop
    it takes under the project's stage dir, so a test that runs it writes
    synthetic crops into the repo — `p2-exit-crops/probe/` is exactly that,
    left behind by an earlier test and committed. A test that dirties the
    working tree teaches everyone to ignore `git status`."""
    old = dict(PE.CROPS)
    stage, private = PE.STAGE_DIR, PE.PRIVATE_DIR
    try:
        PE.CROPS.clear()
        PE.CROPS["probe"] = spec
        PE.STAGE_DIR = os.path.join(os.path.dirname(str(p)), "_stage")
        PE.PRIVATE_DIR = os.path.join(os.path.dirname(str(p)), "_private")
        return PE.run(str(p), tag=tag)
    finally:
        PE.CROPS.clear()
        PE.CROPS.update(old)
        PE.STAGE_DIR, PE.PRIVATE_DIR = stage, private


def test_subject_share_reads_the_mask_not_the_picture(tmp_path):
    p = _subject_frame(tmp_path, 0.80)
    (id_arr, n2i), why = PE._decoded_matmask(str(p))
    assert id_arr is not None, why
    share, occ = PE._subject_share(id_arr, n2i, PE._norm_img(str(p)),
                                   (0.0, 0.0, 1.0, 1.0), ("the_subject",))
    assert 0.79 < share < 0.81
    assert occ[0][0] == "the_subject"


def test_a_box_that_is_not_on_its_subject_is_refused(tmp_path, capsys):
    """The whole point. The box is legal, the crop is measurable, the picture is
    unremarkable — and the rung must still refuse, because what is under the box
    is not what the rung is named after."""
    p = _subject_frame(tmp_path, 0.20)
    rc = _run_only(p, {"kind": "autocorr", "declared": "test",
                       "ours_box": (0.0, 0.0, 1.0, 1.0),
                       "subject_materials": ("the_subject",)})
    out = capsys.readouterr().out
    assert rc == 2, out
    assert "BOX COULD NOT RUN" in out
    assert "the_decoy" in out, "the refusal must name what IS under the box"


def test_a_box_on_its_subject_runs(tmp_path, capsys):
    """The other side of the control: the guard must not simply always refuse."""
    p = _subject_frame(tmp_path, 0.80)
    rc = _run_only(p, {"kind": "autocorr", "declared": "test",
                       "ours_box": (0.0, 0.0, 1.0, 1.0),
                       "subject_materials": ("the_subject",)})
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "subject check" in out and "80.0%" in out


def test_every_box_rung_declares_its_subject():
    """NO ALLOWLIST (R9b). This repo had already found this exact defect on ONE
    crop — cloth_edge's `retired_box`, p2r41: "a working control proved the
    METHOD could see; nothing ever checked that the BOX HELD A BOUNDARY" — and
    fixed it as a note about that one box, leaving four others unchecked for
    fifteen rounds. A rule that names the objects it applies to will always
    exempt the next one, so the requirement is on the SHAPE of a registry entry:
    if you measure inside a typed box, you say what is supposed to be in it."""
    for key, spec in PE.CROPS.items():
        if "ours_box" not in spec:
            continue
        subj = spec.get("subject_materials")
        assert subj, f"{key}: a typed box with no declared subject cannot be checked"
        assert all(isinstance(m, str) and m for m in PE._names(subj)), key


def test_the_subject_floor_is_a_can_i_see_it_bar_not_a_quality_bar():
    """Pinned so a future round cannot quietly raise it into a quality cut, or
    drop it to where a box that is mostly something else still counts."""
    assert 0.40 <= PE.SUBJECT_MIN_SHARE <= 0.60


# ------------------------------- ledger vs frame, and the namespace collision

def test_absent_by_declaration_needs_every_named_material():
    """One present leg makes a site present. If any name in the list is not
    declared absent, the rung may not print a signed absence over it."""
    # the argument is a MATERIAL name; the table is keyed by OBJECT and the
    # lookup normalises `bed__x` -> `bed_x` to bridge them (see the collision
    # test below for why that bridge is only ever half-true)
    assert PE._absent_by_declaration("bed_throw")
    assert PE._absent_by_declaration(("bed_throw", "bed_coverlet"))
    assert PE._absent_by_declaration(("bed_throw", "acq_bed_throw")) is None


def test_a_material_with_pixels_is_present_whatever_the_ledger_says(tmp_path):
    """THE COLLISION, pinned. `value_ladder.DECLARED_ABSENT` is keyed by OBJECT
    and this rung names a MATERIAL, and the lookup bridged them with a
    `bed__`->`bed_` mangle. On the acquired set that inverts the meaning: D-086
    declares the OBJECT `bed__duvet` absent precisely BECAUSE the bought set is
    one fused mesh, and D-138 says that mesh WEARS the material `bed_duvet`. So
    the material renders while its object is correctly signed absent, and the
    harness printed "absent by decision, not unmeasured" over 7% of the frame."""
    H, W = 1200, 1600
    rng = np.random.default_rng(5)
    L = 150.0 + 25.0 * rng.standard_normal((H, W))
    rgb = np.repeat(np.clip(L, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
    p = tmp_path / "room_x_ledger.png"
    Image.fromarray(rgb).save(p)
    ids = np.full((H, W), 7, dtype=np.int32)
    _matmask_png(str(p).rsplit(".", 1)[0], ids, {"bed_duvet": 7})
    (id_arr, n2i), _why = PE._decoded_matmask(str(p))
    # the ledger says the OBJECT is gone, and the name-mangled lookup happily
    # reports that as the MATERIAL being gone ...
    assert PE._absent_by_declaration("bed_duvet")
    # ... and the frame says the MATERIAL is right there. The frame wins.
    assert PE._has_pixels(id_arr, n2i, ("bed_duvet",)) == ["bed_duvet"]
    assert PE._has_pixels(id_arr, n2i, ("bed_throw",)) == []


# ------------------------------------- the edge site is derived, not typed

def _sloped_edge_frame(tmp_path, rise, stem="room_x_slope"):
    """Floor above, rug below, the boundary sloping across the frame — the shape
    a real rug's far edge has. `rise` is how many rows the transition is spread
    over. The DECLARED box deliberately sits somewhere else entirely."""
    H, W = 1200, 1600
    L = np.full((H, W), 150.0)
    ids = np.zeros((H, W), dtype=np.int32)
    for x in range(W):
        y = 300 + int(400 * x / W)                       # the sloping contact
        L[:y, x] = 190.0
        for k in range(rise):
            f = (k + 1) / float(rise + 1)
            L[y + k, x] = 190.0 + (150.0 - 190.0) * f
        ids[:y, x] = 3                                   # floor
        ids[y:, x] = 4                                   # rug
    rgb = np.repeat(np.clip(L, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
    p = tmp_path / f"{stem}.png"
    Image.fromarray(rgb).save(p)
    _matmask_png(str(p).rsplit(".", 1)[0], ids, {"floor": 3, "rug": 4})
    return p


def test_the_edge_site_is_derived_from_the_mask_not_the_declared_box(tmp_path):
    """The typed box points at open rug with no boundary in it — exactly the
    p2r78rc state. Derived from the contact, the rung finds the edge anyway and
    measures the rise it was built with."""
    p = _sloped_edge_frame(tmp_path, rise=10)
    ours = PE._norm_img(str(p))
    (id_arr, n2i), _ = PE._decoded_matmask(str(p))
    spec = {"kind": "edge_profile", "declared": "test",
            "contact": (("floor", "rug"),), "cut_rise_px": 3.0}
    c, _, res = PE.rung_edge(ours, spec, id_arr, n2i)
    assert c is not None
    assert res["site"] == "floor over rug"
    assert res["cols"] > 500
    assert res["rise_px_median"] >= 4.0, res


def test_a_sharp_step_still_reads_sharp_through_the_derived_site(tmp_path):
    """The negative control for the rung above: same sloped geometry, no rise.
    A derivation that made every edge look rolled would be worse than the box."""
    p = _sloped_edge_frame(tmp_path, rise=1, stem="room_x_slope_hard")
    ours = PE._norm_img(str(p))
    (id_arr, n2i), _ = PE._decoded_matmask(str(p))
    spec = {"kind": "edge_profile", "declared": "test",
            "contact": (("floor", "rug"),), "cut_rise_px": 3.0}
    _c, _, res = PE.rung_edge(ours, spec, id_arr, n2i)
    assert res["rise_px_median"] <= 3.0, res


def test_contact_strip_straightens_the_line():
    """A sloped boundary in a plain rectangular crop is mostly not-the-boundary,
    and edge_rise_width's per-column argmax then finds whatever else is there.
    Every column of the rectified strip must carry the transition at the SAME
    offset, which is what makes the per-column measurement about the edge."""
    L = np.zeros((200, 300))
    cols = {}
    for x in range(300):
        y = 40 + x // 3
        L[:y, x] = 200.0
        L[y:, x] = 100.0
        cols[x] = y
    strip = PE._contact_strip(L, cols, half=16)
    assert strip is not None and strip.shape[0] == 33
    # the same profile in every column: bright above the centre, dark below
    assert np.allclose(strip[15, :], 200.0)
    assert np.allclose(strip[16, :], 100.0)


def test_contact_strip_drops_columns_it_cannot_window():
    """Clamping a window that runs off the image would silently measure a
    different offset — so those columns leave, and if none survive the rung
    refuses rather than answering from three of them."""
    L = np.zeros((50, 100))
    assert PE._contact_strip(L, {x: 2 for x in range(100)}, half=16) is None


# ---------------------------- the autocorr rung's own positive control (p2r79)

def test_the_autocorr_rung_carries_a_tiled_positive_control():
    """A clean absence test that never demonstrates it CAN fire is a rung that
    prints 'no defect' and 'could not see' in the same words. D-056 already cost
    five rounds of exactly that. The control is built from the crop itself, so it
    survives a camera change that shrinks the repeat below `min_lag`."""
    unique = _panels(unique=True)
    im = Image.fromarray(np.clip(unique, 0, 255).astype(np.uint8))
    _c, _a, res = PE.rung_autocorr(im.convert("RGB"),
                                   {"ours_box": (0.0, 0.0, 1.0, 1.0)})
    assert res["periodic"] is False, "unique figure must read clean"
    assert res["control_fired"] is True, (
        "and the same estimator on the same pixels must still fire on a repeat")


def test_a_clean_autocorr_with_a_dead_control_is_could_not_run(tmp_path, capsys):
    """Flat grey: nothing to find, and nothing findable. The rung must refuse
    rather than report the flat crop as a passing wood panel."""
    H, W = 1200, 1600
    Image.fromarray(np.full((H, W, 3), 128, dtype=np.uint8)).save(
        tmp_path / "room_x_flat.png")
    rc = _run_only(tmp_path / "room_x_flat.png",
                   {"kind": "autocorr", "declared": "test",
                    "ours_box": (0.1, 0.1, 0.9, 0.9),
                    "subject_materials": ("the_subject",)})
    out = capsys.readouterr().out
    # no matmask beside this frame -> the subject guard refuses first, which is
    # itself the right answer; assert the harness never calls it a pass
    assert rc == 2, out


# ---------------------------------------------------------------------------
# THE NOISE FLOOR MUST BE REACHABLE BY THE SIGNAL (TRN-004, 2026-08-29).
#
# Found by reproducing a tutorial and running this rung's own D-056 control on
# the result: a PERFECT self-tiled repeat scored peak 1.000 against floor 1.260
# and printed `not periodic`. A normalised autocorrelation cannot exceed 1.0, so
# a floor at or above 1.0 is not a strict bar, it is a failed estimate — and a
# verdict read against it is "could not look" wearing the face of "looked and it
# was clear", which R11 outlaws by name.
# ---------------------------------------------------------------------------
def _perfect_repeat(w=260, h=200, seed=3):
    """An image that IS a repeat by construction: random content, then its own
    left half duplicated. Peak is 1.000 at lag w/2 or the estimator is broken."""
    rng = np.random.default_rng(seed)
    base = rng.random((h, w // 2))
    base = base + np.linspace(0, 0.4, w // 2)[None, :]     # some broad structure
    return np.concatenate([base, base], axis=1)


def test_a_perfect_repeat_is_found_and_the_floor_stays_under_one():
    L = _perfect_repeat()
    peak, lag, floor = PE.autocorr_peak(L, min_lag=12)
    assert peak > 0.9, f"a literal repeat scored {peak}"
    assert lag == L.shape[1] // 2, f"found lag {lag}, expected {L.shape[1] // 2}"
    assert floor < 1.0, (
        f"floor {floor:.3f} is at or above the 1.0 ceiling the signal cannot "
        f"exceed — the surrogate estimate failed")
    assert peak > floor, "the rung must FIRE on a perfect repeat"


def test_the_floor_is_stable_across_surrogate_seeds():
    """At the shipped n=8 the floor ranged 0.541-1.260 over 12 seeds and one of
    them blocked a perfect repeat. Pinning a seed made that reproducible, not
    right. This asserts the estimator, not the pinned draw."""
    L = _perfect_repeat()
    A = L - L.mean(axis=1, keepdims=True)
    p0 = A.mean(axis=0)
    W = len(p0)
    floors = []
    for seed in range(8):
        rng = np.random.default_rng(seed)
        peaks = []
        for _ in range(PE._SURROGATES):
            sh = p0[rng.permutation(W)]
            pk, _, _ = PE.autocorr_peak(np.tile(sh, (4, 1)), min_lag=12)
            peaks.append(pk)
        floors.append(float(np.mean(peaks) + 3.0 * np.std(peaks)))
    assert max(floors) < 1.0, f"a seed produced an impossible floor: {max(floors):.3f}"
    assert PE._SURROGATES >= 32, "8 surrogates was measured to be too few"


def test_an_impossible_floor_is_could_not_run_never_a_pass():
    """The structural guard, independent of the surrogate count: if the floor
    ever comes back >= 1.0 the crop must carry NO verdict."""
    res = {"peak": 0.0, "lag_px": 0, "floor": 1.26, "periodic": False,
           "control_floor": 0.5}
    for tag, f in (("frame", res["floor"]), ("control", res["control_floor"])):
        if f >= PE._FLOOR_IMPOSSIBLE:
            res["could_not_run"] = "impossible floor"
            res["periodic"] = None
            break
    assert res["could_not_run"]
    assert res["periodic"] is None, "an unrunnable rung must not report `not periodic`"
