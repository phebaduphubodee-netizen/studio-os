"""
test_render_mask_labels.py -- unit tests for the Structured3D render-mask -> {obj_id: kind}
labels lane. Pairs with render_mask_labels.run_selftest() (the end-to-end adapter handshake):
the selftest proves F2 goes UNWIRED->WIRED, these pin the pairing math + I/O + honesty edges so
a silent drift (colormap decode, cross-view majority, void handling, an over-eager map) is
caught. All fixtures are SELF-AUTHORED tiny arrays -- nothing here redistributes the corpus.

    python3 -m pytest test_render_mask_labels.py -q
"""
import json
import os
import tempfile

import numpy as np
import pytest
from PIL import Image

import render_mask_labels as R


# ---- fixtures --------------------------------------------------------------------------------
def _paint(shape, spec, fill_inst=R.INSTANCE_VOID, fill_sem=R.SEMANTIC_VOID):
    """spec = {obj_id: (nyu_class, (row_slice, col_slice))} -> (instance, semantic) int arrays."""
    inst = np.full(shape, fill_inst, dtype=np.int64)
    sem = np.full(shape, fill_sem, dtype=np.int64)
    for oid, (cls, sl) in spec.items():
        inst[sl] = oid
        sem[sl] = cls
    return inst, sem


def _write_view(dirpath, inst, sem):
    os.makedirs(dirpath, exist_ok=True)
    Image.fromarray(inst.astype(np.uint16)).save(os.path.join(dirpath, "instance.png"))
    Image.fromarray(sem.astype(np.uint8)).save(os.path.join(dirpath, "semantic.png"))


# ---- core pairing ---------------------------------------------------------------------------
def test_pair_arrays_counts_per_instance_and_skips_void():
    inst, sem = _paint((10, 10), {0: (4, (slice(0, 5), slice(0, 10))),      # bed, 50 px
                                  1: (6, (slice(5, 10), slice(0, 10)))})    # sofa, 50 px
    got = R.pair_arrays(inst, sem)
    assert set(got) == {0, 1}
    assert got[0][4] == 50 and got[1][6] == 50
    # the void region (instance 65535) contributes nothing
    assert R.INSTANCE_VOID not in got


def test_pair_arrays_semantic_void_pixels_ignored():
    # obj 0 spans 100 px but only 10 carry a real class (rest semantic-void 0)
    inst = np.full((10, 10), R.INSTANCE_VOID, dtype=np.int64)
    sem = np.zeros((10, 10), dtype=np.int64)
    inst[:, :] = 0
    sem[0, :] = 4                      # 10 px of bed, 90 px void
    got = R.pair_arrays(inst, sem)
    assert got[0][4] == 10 and sum(got[0].values()) == 10


def test_pair_arrays_shape_mismatch_raises():
    with pytest.raises(ValueError, match="shape mismatch"):
        R.pair_arrays(np.zeros((4, 4), np.int64), np.zeros((4, 5), np.int64))


def test_void_only_instance_has_empty_counter():
    inst = np.full((4, 4), R.INSTANCE_VOID, dtype=np.int64)
    sem = np.zeros((4, 4), dtype=np.int64)
    inst[0, 0] = 7                     # instance present, but its one pixel is semantic-void
    got = R.pair_arrays(inst, sem)
    assert 7 in got and len(got[7]) == 0    # seen, but no class -> reported unmapped downstream


# ---- mask I/O (real PNG round-trip incl. 16-bit instance) -----------------------------------
def test_png_roundtrip_uint16_instance_and_uint8_semantic():
    d = tempfile.mkdtemp(prefix="rml_io_")
    inst, sem = _paint((8, 8), {0: (4, (slice(0, 4), slice(0, 8))),
                                40000: (6, (slice(4, 8), slice(0, 8)))})   # >255 id proves 16-bit
    _write_view(d, inst, sem)
    got = R.pair_view(os.path.join(d, "instance.png"), os.path.join(d, "semantic.png"))
    assert got[0][4] == 32 and got[40000][6] == 32


def test_read_mask_rejects_3channel_rgb():
    d = tempfile.mkdtemp(prefix="rml_rgb_")
    p = os.path.join(d, "semantic.png")
    Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8)).save(p)
    with pytest.raises(ValueError, match="raw class-id"):
        R.read_mask(p)


def test_read_mask_decodes_paletted_class_id_as_index():
    # Structured3D semantic.png is mode 'P' whose palette is a DISPLAY colormap and whose INDEX is
    # the NYU class id (verified 2026-07-09 on panorama_00: indices all in 0..40). read_mask must
    # DECODE it -- return the indices AS class ids -- not reject it. The palette (colormap) must not
    # change the returned values.
    d = tempfile.mkdtemp(prefix="rml_pal_ok_")
    p = os.path.join(d, "semantic.png")
    arr = np.array([[0, 4], [22, 40]], dtype=np.uint8)          # void, bed, ceiling, otherprop
    im = Image.frombytes("P", (2, 2), arr.tobytes())
    im.putpalette([(i * 7) % 256 for i in range(768)])         # arbitrary display colormap
    im.save(p)
    assert Image.open(p).mode == "P"
    got = R.read_mask(p)
    assert got.tolist() == arr.tolist()                        # indices returned AS class ids


def test_read_mask_rejects_paletted_out_of_nyu_range():
    # a paletted mask whose index exceeds the NYU-40 ceiling is NOT class-id-as-index (a genuinely
    # different colormap) -> the guard STILL fires hard, never mislabelling (adversarial finding
    # 2026-07-09 intent preserved for the surprise case).
    d = tempfile.mkdtemp(prefix="rml_pal_bad_")
    p = os.path.join(d, "semantic.png")
    arr = np.array([[0, 200], [5, 6]], dtype=np.uint8)         # 200 > 40 -> not a class id
    im = Image.frombytes("P", (2, 2), arr.tobytes())
    im.putpalette([(i * 7) % 256 for i in range(768)])         # full palette -> index 200 survives
    im.save(p)
    assert int(np.asarray(Image.open(p)).max()) == 200         # guard the fixture itself
    with pytest.raises(ValueError, match="NYU-40 ceiling"):
        R.read_mask(p)


# ---- cross-view aggregation + confidence -----------------------------------------------------
def test_majority_summed_across_views():
    d = tempfile.mkdtemp(prefix="rml_mv_")
    # view A: obj 0 mostly sofa(6) w/ a little bed(4); view B: obj 0 all bed -> summed = bed wins
    ia, sa = _paint((10, 10), {0: (6, (slice(0, 10), slice(0, 10)))})
    sa[0, :] = 4                                       # 10 bed vs 90 sofa in view A
    ib, sb = _paint((10, 10), {0: (4, (slice(0, 10), slice(0, 10)))})   # 100 bed in view B
    _write_view(os.path.join(d, "roomA", "panorama", "full"), ia, sa)
    _write_view(os.path.join(d, "roomB", "panorama", "full"), ib, sb)
    labels, rep = R.scene_labels(d)
    assert labels[0] == "bed"                          # 110 bed vs 90 sofa across both views
    assert rep["views_paired"] == 2


def _one_object_two_classes(bed_px, sofa_px):
    """A 1x(bed+sofa) single-object view: obj 0 with bed_px pixels of bed(4) then sofa_px sofa(6)."""
    n = bed_px + sofa_px
    inst = np.zeros((1, n), dtype=np.int64)             # all obj 0 (0 is a valid instance id)
    sem = np.empty((1, n), dtype=np.int64)
    sem[0, :bed_px] = 4
    sem[0, bed_px:] = 6
    return inst, sem


def test_low_confidence_emitted_but_flagged():
    d = tempfile.mkdtemp(prefix="rml_lc_")
    inst, sem = _one_object_two_classes(55, 45)         # conf 0.55: clears emit floor, < LOW_CONF
    _write_view(os.path.join(d, "roomA", "panorama", "full"), inst, sem)
    labels, rep = R.scene_labels(d)
    assert labels.get(0) == "bed"                       # 0.55 > MIN_CONF_EMIT -> emitted (majority)
    assert rep["low_confidence"] and rep["low_confidence"][0]["obj_id"] == 0
    assert rep["disagreements"] and rep["disagreements"][0]["obj_id"] == 0


def test_tie_not_emitted_reported_ambiguous():
    d = tempfile.mkdtemp(prefix="rml_tie_")
    inst, sem = _one_object_two_classes(50, 50)         # conf 0.5, NOT > MIN_CONF_EMIT -> not emitted
    _write_view(os.path.join(d, "roomA", "panorama", "full"), inst, sem)
    labels, rep = R.scene_labels(d)
    assert 0 not in labels                              # a coin-flip is never emitted as GT
    assert rep["ambiguous_unlabelled"] and rep["ambiguous_unlabelled"][0]["obj_id"] == 0


def test_min_pixels_floor_drops_tiny_object():
    d = tempfile.mkdtemp(prefix="rml_min_")
    inst, sem = _paint((10, 10), {0: (4, (slice(0, 2), slice(0, 5)))})   # 10 px bed < MIN_PIXELS
    _write_view(os.path.join(d, "roomA", "panorama", "full"), inst, sem)
    labels, rep = R.scene_labels(d)
    assert 0 not in labels and rep["ambiguous_unlabelled"][0]["pixels"] == 10


# ---- honesty: unmapped classes never fabricated ---------------------------------------------
def test_unmapped_nyu_class_left_unlabelled_and_reported():
    d = tempfile.mkdtemp(prefix="rml_um_")
    inst, sem = _paint((10, 10), {0: (4, (slice(0, 5), slice(0, 10))),     # bed -> mapped
                                  1: (39, (slice(5, 10), slice(0, 10)))})  # otherfurniture -> not
    _write_view(os.path.join(d, "roomA", "panorama", "full"), inst, sem)
    labels, rep = R.scene_labels(d)
    assert labels == {0: "bed"}
    assert rep["unmapped_by_class"].get("otherfurniture") == 1
    assert rep["labelled"] == 1 and rep["instances_seen"] == 2


def test_perspective_skipped_by_default_opt_in_with_flag():
    d = tempfile.mkdtemp(prefix="rml_persp_")
    inst_p, sem_p = _paint((8, 8), {0: (4, (slice(0, 8), slice(0, 8)))})       # panorama: bed
    inst_x, sem_x = _paint((8, 8), {1: (6, (slice(0, 8), slice(0, 8)))})       # perspective: sofa
    _write_view(os.path.join(d, "roomA", "panorama", "full"), inst_p, sem_p)
    _write_view(os.path.join(d, "roomA", "perspective", "full", "0"), inst_x, sem_x)
    # default: panorama only (the verified instance-id space) -> perspective view is skipped
    labels, rep = R.scene_labels(d)
    assert labels == {0: "bed"} and rep["perspective_views_skipped"] == 1 and rep["views_paired"] == 1
    # opt-in: both views pair
    labels2, rep2 = R.scene_labels(d, include_perspective=True)
    assert set(labels2) == {0, 1} and rep2["views_paired"] == 2


def test_scene_with_no_semantic_sibling_reports_unpaired():
    d = tempfile.mkdtemp(prefix="rml_np_")
    vd = os.path.join(d, "roomA", "panorama", "full")
    os.makedirs(vd, exist_ok=True)
    inst, _ = _paint((6, 6), {0: (4, (slice(0, 6), slice(0, 6)))})
    Image.fromarray(inst.astype(np.uint16)).save(os.path.join(vd, "instance.png"))   # no semantic
    labels, rep = R.scene_labels(d)
    assert labels == {} and rep["views_unpaired_no_semantic"] == 1 and rep["views_paired"] == 0


# ---- corpus format + adapter handshake -------------------------------------------------------
def test_corpus_labels_shape_and_str_keys():
    root = tempfile.mkdtemp(prefix="rml_corpus_")
    sd = os.path.join(root, "scene_00000", "2D_rendering", "roomA", "panorama", "full")
    inst, sem = _paint((6, 6), {0: (33, (slice(0, 6), slice(0, 6)))})      # toilet
    _write_view(sd, inst, sem)
    out, reports = R.corpus_labels(root)
    assert out == {"scene_00000": {"0": "toilet"}}                          # keys are strings (JSON)
    assert len(reports) == 1 and reports[0]["facing_wired"] == 1


def test_map_is_stable_no_silent_drift():
    # guards the two judgement calls + the facing set the whole F2 unblock rests on
    assert R.NYU40_TO_BENCH[25] == "tv_panel"          # television -> panel (not console)
    assert R.NYU40_TO_BENCH[4] == "bed" and R.NYU40_TO_BENCH[33] == "toilet"
    assert 39 not in R.NYU40_TO_BENCH and 1 not in R.NYU40_TO_BENCH   # otherfurniture / wall unmapped
    facing, norm = R._facing_kinds()
    wired = {k for k in R.NYU40_TO_BENCH.values() if norm(k) in facing}
    assert {"bed", "sofa", "chair", "desk", "toilet", "cabinet", "tv_panel"} <= wired


def test_end_to_end_f2_unwired_to_wired():
    """pytest mirror of run_selftest's handshake, so CI catches an adapter/schema regression."""
    R.run_selftest()   # raises on any assertion failure
