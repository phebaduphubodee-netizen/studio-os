"""
test_floorplancad_adapter.py -- unit tests for the FloorPlanCAD SVG -> gt.json adapter.

Fixtures are SELF-AUTHORED synthetic SVGs (the corpus is CC BY-NC and lives outside the
repo; nothing here redistributes it). Pinned per the scorer-honesty doctrine: every skip
path must be COUNTED (unknown ids, transforms, malformed), calibration must refuse to
guess (None below support, out-of-band rejected), and the emitted schema must round-trip
benchmark_reader with F2/F3/F5 UNWIRED -- a fabricated rot/indoor flag would poison the
whole backwards-learning lane.
"""
import io
import json
import os
import tempfile

import benchmark_reader as B
import floorplancad_adapter as A


def _svg(body):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<svg version="1.1" viewBox="0 0 100.0 100.0" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">\n'
            + body + "\n</svg>")


def _convert(body, **kw):
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, "t.svg")
        with open(fp, "w", encoding="utf-8") as fh:
            fh.write(_svg(body))
        return A.convert(fp, **kw)


def layer(label, inner):
    return (f'<g id="layer{label}" inkscape:groupmode="layer" '
            f'inkscape:label="{label}">{inner}</g>')


def prim(sem, inst, d, tag="path", extra=""):
    if tag == "path":
        return f'<path d="{d}" semantic-id="{sem}" instance-id="{inst}" {extra}/>'
    raise ValueError(tag)


# a calibration block: text "3000" over a parallel 30-unit unannotated line -> 100 mm/unit
CAL = layer("PUB_DIM",
            '<path d="M 10,90 L 40,90"/>'
            '<path d="M 10,80 L 40,80"/>'
            '<path d="M 60,90 L 90,90"/>'
            '<text x="25" y="89.5" font-size="2">3000</text>'
            '<text x="25" y="79.5" font-size="2">3000</text>'
            '<text x="75" y="89.5" font-size="2">3000</text>')


# ---- path walking ------------------------------------------------------------------------
def test_walk_path_abs_rel_hv_z():
    pts = A.walk_path("M 1,2 L 3,2 h 2 V 5 Z")
    assert pts[0] == ((1.0, 2.0), "move")
    assert ((3.0, 2.0), "draw") in pts and ((5.0, 2.0), "draw") in pts
    assert ((5.0, 5.0), "draw") in pts
    assert pts[-1] == ((1.0, 2.0), "draw")          # Z closes back to subpath start

def test_walk_path_arc_consumes_flags_not_as_coords():
    # A rx ry rot laf sf x y -- naive number-pairing would fabricate points like (10,10)
    pts = A.walk_path("M 0,0 A 10 10 0 0 1 5,5")
    assert ((5.0, 5.0), "draw") in pts
    xs = [p for (p, f) in pts]
    assert (10.0, 10.0) not in xs and (0.0, 1.0) not in xs

def test_walk_path_curve_ctrl_points_are_extent_only():
    pts = A.walk_path("M 0,0 C 1,9 2,9 3,0")
    flags = {p: f for p, f in pts}
    assert flags[(1.0, 9.0)] == "ctrl" and flags[(3.0, 0.0)] == "draw"

def test_walk_path_malformed_tail_keeps_prefix():
    pts = A.walk_path("M 0,0 L 5,0 L 9")           # dangling y
    assert ((5.0, 0.0), "draw") in pts

def test_path_segments_chords_and_move_breaks():
    segs = A.path_segments("M 0,0 L 10,0 M 20,0 L 30,0")
    assert segs == [((0.0, 0.0), (10.0, 0.0)), ((20.0, 0.0), (30.0, 0.0))]
    # ctrl points never anchor a segment: chord goes pen->endpoint
    segs = A.path_segments("M 0,0 C 1,9 2,9 3,0")
    assert segs == [((0.0, 0.0), (3.0, 0.0))]


# ---- element extraction ------------------------------------------------------------------
def test_element_grouped_across_prims_bbox_and_id():
    body = layer("FURN",
                 prim(14, 7, "M 10,10 L 30,10") + prim(14, 7, "M 10,10 L 10,28"))
    doc = _convert(body)
    assert len(doc["elements"]) == 1
    e = doc["elements"][0]
    assert e["id"] == "s14_i7" and e["kind"] == "bed" and e["n_prims"] == 2
    assert (e["x"], e["y"], e["w"], e["d"]) == (10.0, 10.0, 20.0, 18.0)
    assert doc["meta"]["units"] == "svg-unit"      # no dims -> uncalibrated, flagged

def test_no_rot_indoor_floor_ever_emitted():
    doc = _convert(layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9 Z")))
    e = doc["elements"][0]
    assert "rot" not in e and "indoor" not in e and "floor" not in e

def test_openings_typed_sliding_vs_door_vs_window_vs_opening():
    body = layer("D",
                 prim(3, 1, "M 0,0 L 9,0") + prim(5, 2, "M 20,0 L 34,0") +
                 prim(9, 3, "M 40,0 L 50,0") + prim(12, 4, "M 60,0 L 66,0"))
    doc = _convert(body)
    types = {o["subtype_raw"]: o["type"] for o in doc["openings"]}
    assert types == {"single_door": "door", "sliding_door": "sliding",
                     "window": "window", "opening_symbol": "opening"}
    assert doc["elements"] == []

def test_stuff_wall_counted_not_emitted():
    doc = _convert(layer("WALL", prim(1, -1, "M 0,0 L 99,0") * 3))
    assert doc["elements"] == [] and doc["openings"] == []
    assert doc["meta"]["stuff_counts"] == {"wall": 3}

def test_curtain_wall_and_railing_go_to_glazing_channel():
    body = layer("A-GLAZ", prim(2, -1, "M 0,50 L 60,50")) + \
           layer("RAIL", prim(33, -1, "M 0,60 L 40,60"))
    doc = _convert(body)
    kinds = {(g["kind"], g["x1"], g["x2"]) for g in doc["glazing_lines"]}
    assert kinds == {("curtain_wall", 0.0, 60.0), ("railing", 0.0, 40.0)}
    assert doc["glazing_lines"][0]["layer"] == "A-GLAZ"

def test_wall_lines_exported_including_instanced():
    # class-1 wall geometry is exported for BOTH stuff (-1) and instanced prims;
    # counters must stay exactly what the old count-only branch produced
    body = layer("WALL", prim(1, -1, "M 0,0 L 99,0") + prim(1, 7, "M 0,10 L 50,10"))
    doc = _convert(body)
    assert doc["elements"] == [] and doc["openings"] == []
    got = {(w["x1"], w["y1"], w["x2"], w["y2"]) for w in doc["wall_lines"]}
    assert got == {(0.0, 0.0, 99.0, 0.0), (0.0, 10.0, 50.0, 10.0)}
    assert doc["meta"]["stuff_counts"] == {"wall": 2}
    assert doc["meta"]["instanced_stuff"] == 1

def test_wall_lines_scaled_when_calibrated():
    doc = _convert(CAL + layer("WALL", prim(1, -1, "M 0,50 L 60,50")))
    w = doc["wall_lines"][0]
    assert (w["x1"], w["x2"], w["y1"]) == (0.0, 6000.0, 5000.0)

def test_unknown_semantic_id_counted_never_guessed():
    doc = _convert(layer("X", prim(99, 5, "M 0,0 L 5,0")))
    assert doc["elements"] == []
    assert doc["meta"]["unknown_ids"] == {"99": 1}

def test_transform_bearing_prim_skipped_and_counted():
    body = layer("F", prim(13, 1, "M 0,0 L 20,0", extra='transform="translate(3,4)"')
                 + prim(13, 1, "M 0,0 L 20,0 L 20,9"))
    doc = _convert(body)
    assert doc["meta"]["transforms_skipped"] == 1
    assert len(doc["elements"]) == 1               # untransformed prim still lands

def test_malformed_path_counted():
    doc = _convert(layer("F", prim(13, 1, "")))
    assert doc["elements"] == [] and doc["meta"]["malformed_prims"] == 1

def test_mixed_instance_id_across_classes_counted():
    body = layer("F", prim(13, 9, "M 0,0 L 5,0 L 5,4") + prim(14, 9, "M 20,0 L 25,0 L 25,4"))
    doc = _convert(body)
    assert doc["meta"]["mixed_instances"] == 1
    assert len(doc["elements"]) == 2               # split, never merged cross-kind

def test_order_inferred_ids_surface_in_meta():
    doc = _convert(layer("D", prim(7, 1, "M 0,0 L 9,0")))
    assert doc["meta"]["order_inferred_ids_seen"] == {"revolving_door": 1}
    assert doc["openings"][0]["subtype_raw"] == "revolving_door"

def test_root_level_prims_not_lost():
    doc = _convert(prim(13, 1, "M 0,0 L 20,0 L 20,9"))
    assert len(doc["elements"]) == 1
    assert doc["elements"][0]["layer"] == "<root>"


# ---- calibration -------------------------------------------------------------------------
def test_calibration_from_dim_texts():
    doc = _convert(CAL + layer("F", prim(18, 1, "M 10,10 L 31,10 L 31,15.6 Z")))
    m = doc["meta"]
    assert m["units"] == "mm" and m["scale_mm_per_unit"] == 100.0
    e = doc["elements"][0]
    assert (e["w"], e["d"]) == (2100.0, 560.0)     # the survey's wardrobe anchor
    assert m["calib"]["support"] == 3

def test_calibration_refuses_below_support():
    body = layer("PUB_DIM", '<path d="M 10,90 L 40,90"/>'
                            '<text x="25" y="89.5" font-size="2">3000</text>')
    doc = _convert(body + layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] is None
    assert doc["meta"]["units"] == "svg-unit"
    assert doc["meta"]["calib"]["n_ratio_candidates"] == 1

def test_calibration_mode_cluster_survives_noise():
    noise = ('<path d="M 0,10 L 4,10"/><text x="2" y="9.5" font-size="2">9999</text>')
    doc = _convert(layer("PUB_DIM", noise) + CAL +
                   layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] == 100.0

def test_calibration_rejects_out_of_band_scale():
    # 30-unit lines labelled "300" -> 10 mm/unit -> sheet 1 m: not a floor plan
    body = layer("PUB_DIM",
                 '<path d="M 10,90 L 40,90"/><path d="M 10,80 L 40,80"/>'
                 '<path d="M 60,90 L 90,90"/>'
                 '<text x="25" y="89.5" font-size="2">300</text>'
                 '<text x="25" y="79.5" font-size="2">300</text>'
                 '<text x="75" y="89.5" font-size="2">300</text>')
    doc = _convert(body + layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] is None

def test_dim_text_nonnumeric_and_tiny_values_ignored():
    body = layer("PUB_DIM", '<path d="M 10,90 L 40,90"/>'
                            '<text x="25" y="89.5" font-size="2">A1</text>'
                            '<text x="25" y="89.7" font-size="2">12</text>')
    doc = _convert(body)
    assert doc["meta"]["calib"]["n_dim_texts"] == 0

def test_glazing_lines_scaled_when_calibrated():
    doc = _convert(CAL + layer("G", prim(2, -1, "M 0,50 L 60,50")))
    g = doc["glazing_lines"][0]
    assert (g["x1"], g["x2"], g["y1"]) == (0.0, 6000.0, 5000.0)

def test_door_mm_median_reported_only_when_calibrated():
    doc_cal = _convert(CAL + layer("D", prim(3, 1, "M 10,10 L 19,10 L 19,19")))
    assert doc_cal["meta"]["door_mm_median"] == 900.0
    doc_raw = _convert(layer("D", prim(3, 1, "M 10,10 L 19,10 L 19,19")))
    assert doc_raw["meta"]["door_mm_median"] is None


# ---- scrutiny 2026-07-06 pins (12 confirmed findings) --------------------------------------
def test_arc_true_extent_half_circle():
    # half circle 0,0 -> 10,0 r=5 sweep=1: centre (5,0), bulge at y=-5 (W3C F.6.5)
    doc = _convert(layer("F", prim(13, 1, "M 0,0 A 5,5 0 0,1 10,0")))
    e = doc["elements"][0]
    assert (e["x"], e["w"]) == (0.0, 10.0)
    assert abs(e["y"] - (-5.0)) < 0.1 and abs(e["d"] - 5.0) < 0.1

def test_arc_circle_as_two_half_arcs_not_zero_area():
    # the 0905-0041 sink pattern: a full circle drawn as two 180-degree arcs used to
    # collapse to a zero-area chord pair -> unmatchable GT
    d = "M 10,20 A 5,5 0 1,0 10,30 A 5,5 0 1,0 10,20"
    doc = _convert(layer("F", prim(23, 1, d)))
    e = doc["elements"][0]
    assert abs(e["w"] - 10.0) < 0.2 and abs(e["d"] - 10.0) < 0.2
    assert doc["meta"]["degenerate_dropped"] == []

def test_arc_flags_still_not_coordinates():
    doc = _convert(layer("F", prim(13, 1, "M 0,0 A 10 10 0 0 1 5,5 L 6,1")))
    e = doc["elements"][0]
    assert e["x"] >= -10.5 and e["w"] < 25     # no fabricated (10,10)/(0,1) points

def test_zero_extent_element_dropped_and_counted():
    doc = _convert(layer("F", prim(13, 1, "M 0,0 L 10,0")))       # pure 1D line-work
    assert doc["elements"] == []
    assert doc["meta"]["degenerate_dropped"] == ["s13_i1"]

def test_zero_extent_opening_kept():
    doc = _convert(layer("D", prim(9, 1, "M 40,0 L 50,0")))       # windows are thin: ok
    assert len(doc["openings"]) == 1
    assert doc["meta"]["degenerate_dropped"] == []

def test_transform_prim_geometry_excluded_from_bbox():
    # mutant M4b: counting the skip but still pooling its points must fail this
    body = layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")
                 + prim(13, 1, "M 500,500 L 900,900", extra='transform="translate(3,4)"'))
    doc = _convert(body)
    e = doc["elements"][0]
    assert doc["meta"]["transforms_skipped"] == 1
    assert (e["x"], e["y"], e["w"], e["d"]) == (0.0, 0.0, 20.0, 9.0)

def test_calibration_overprinted_duplicate_texts_are_one_vote():
    # the 0844-0210 pattern: 7 identical texts on one anchor + one segment == ONE
    # measurement -> must refuse (support comes from distinct dim lines)
    body = layer("PUB_DIM", '<path d="M 10,90 L 40,90"/>'
                 + '<text x="25" y="89.5" font-size="2">3000</text>' * 7)
    doc = _convert(body + layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] is None
    assert doc["meta"]["calib"]["n_texts_unique"] == 1

def test_calibration_shared_border_segment_is_one_measurement():
    # the 0581-0771 pattern: 3 distinct texts all leaning on the same sheet border
    body = layer("PUB_DIM", '<path d="M 0,88.7 L 100,88.7"/>'
                 '<text x="20" y="88.5" font-size="2">4100</text>'
                 '<text x="55" y="88.5" font-size="2">4100</text>'
                 '<text x="80" y="88.5" font-size="2">4100</text>')
    doc = _convert(body + layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] is None
    assert doc["meta"]["calib"]["distinct_segments"] == 1

def test_calibration_ignores_tick_fragments_shorter_than_text():
    # the 0940-0044 pattern: tiny tick strokes sit CLOSER than the real dim line;
    # length gate (>=2.5x font-size) must reject them so the true line wins
    ticks = '<path d="M 24.6,89.8 L 25.4,89.8"/><path d="M 24.6,79.8 L 25.4,79.8"/>' \
            '<path d="M 74.6,89.8 L 75.4,89.8"/>'
    doc = _convert(layer("PUB_DIM", ticks) + CAL +
                   layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] == 100.0

def test_calibration_revoked_when_doors_contradict_scale():
    # a confidently-accepted scale that renders the file's doors at 300mm is wrong:
    # the id-map door anchor revokes it and the file drops to flagged svg units
    body = CAL + layer("D", prim(3, 1, "M 10,10 L 13,10 L 13,13"))   # 3u door -> 300mm
    doc = _convert(body)
    assert doc["meta"]["scale_mm_per_unit"] is None
    assert doc["meta"]["units"] == "svg-unit"
    assert "door-band" in doc["meta"]["calib"]["rejected_by"]
    assert doc["openings"][0]["w"] == 3.0          # re-assembled unscaled

def test_calibration_kept_when_doors_agree():
    doc = _convert(CAL + layer("D", prim(3, 1, "M 10,10 L 19,10 L 19,19")))
    assert doc["meta"]["scale_mm_per_unit"] == 100.0
    assert "rejected_by" not in doc["meta"]["calib"]

def test_calibration_fraction_guard_refuses_junk_dilution():
    # mutant M3b: deleting CALIB_MIN_FRACTION must fail this (3 good vs 6 scattered)
    junk = "".join(
        f'<path d="M 10,{y} L {10 + L},{y}"/><text x="{10 + L / 2}" y="{y - 0.5}" '
        f'font-size="2">{v}</text>'
        for y, L, v in [(70, 10, 5000), (60, 30, 7000), (50, 50, 11000),
                        (40, 12, 6100), (30, 33, 9100), (20, 47, 13300)])
    doc = _convert(layer("PUB_DIM", junk) + CAL +
                   layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9")))
    assert doc["meta"]["scale_mm_per_unit"] is None

def test_mm_rounding_precision_survives():
    # mutant M7b: rounding to whole mm-tens would lose the .3
    doc = _convert(CAL + layer("F", prim(13, 1, "M 10.253,10 L 30.253,10 L 30.253,19 Z")))
    assert doc["elements"][0]["x"] == 1025.3

def test_no_rot_fabricated_on_openings_either():
    # mutant M6b: a fabricated rot=0 on openings is invisible to F2 (elements-only)
    doc = _convert(layer("D", prim(3, 1, "M 0,0 L 9,0 L 9,9")))
    assert "rot" not in doc["openings"][0]

def test_instanced_stuff_never_becomes_element():
    doc = _convert(layer("W", prim(1, 5, "M 0,0 L 50,0 L 50,3")))
    assert doc["elements"] == []
    assert doc["meta"]["stuff_counts"] == {"wall": 1}
    assert doc["meta"]["instanced_stuff"] == 1

def test_text_with_garbage_semantic_id_counted_not_crash():
    body = layer("X", '<text x="1" y="1" semantic-id="oops">300</text>') + \
           layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9"))
    doc = _convert(body)
    assert doc["meta"]["unknown_ids"] == {"oops": 1}
    assert len(doc["elements"]) == 1

def test_batch_survives_a_file_that_crashes_convert():
    import tempfile as _tf
    real_convert = A.convert
    def boom(fp, split=None):
        if "b.svg" in fp:
            raise ValueError("synthetic crash")
        return real_convert(fp, split=split)
    with _tf.TemporaryDirectory() as td:
        svg_dir = os.path.join(td, "svgs")
        os.makedirs(svg_dir)
        for name in ("a", "b", "c"):
            with open(os.path.join(svg_dir, name + ".svg"), "w", encoding="utf-8") as fh:
                fh.write(_svg(layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9"))))
        A.convert = boom
        try:
            A.run_batch(svg_dir, os.path.join(td, "gt"))
        finally:
            A.convert = real_convert
        man = {json.loads(ln)["file"]: json.loads(ln) for ln in
               open(os.path.join(td, "gt", "manifest.jsonl"), encoding="utf-8")}
        assert man["b"]["ok"] is False and "ValueError" in man["b"]["error"]
        assert man["a"]["ok"] and man["c"]["ok"]          # rest of the corpus survives


def test_score_pair_refuses_unit_mismatch_and_naked_svg_units():
    import pytest
    doc_mm = _convert(CAL + layer("F", prim(14, 1, "M 10,10 L 30,10 L 30,28 Z")))
    doc_svg = _convert(layer("F", prim(14, 1, "M 10,10 L 30,10 L 30,28 Z")))
    assert doc_mm["meta"]["units"] == "mm" and doc_svg["meta"]["units"] == "svg-unit"
    with pytest.raises(ValueError):
        B.score_pair(doc_mm, doc_svg)                     # mixed units: refuse
    with pytest.raises(ValueError):
        B.score_pair(doc_svg, doc_svg)                    # svg units need explicit tol
    card = B.score_pair(doc_svg, doc_svg, open_tol=3.0)   # conscious choice: fine
    assert card["detection"]["verdict"] == "PASS"


# ---- benchmark_reader integration ---------------------------------------------------------
def test_gt_vs_gt_scores_perfect_and_unwired_where_no_data():
    body = CAL + layer("F", prim(14, 1, "M 10,10 L 30,10 L 30,28 Z") +
                       prim(17, 2, "M 40,10 L 56,10 L 56,14 Z")) + \
           layer("D", prim(5, 3, "M 60,10 L 74,10"))
    doc = _convert(body)
    card = B.score_pair(doc, doc)
    assert card["detection"]["verdict"] == "PASS" and card["detection"]["recall"] == 1.0
    assert card["F1_identity"]["accuracy"] == 1.0
    assert card["F4_openings"]["subtype_accuracy"] == 1.0
    for f in ("F2_facing", "F3_indoor", "F5_floor"):
        assert card[f]["verdict"] == "UNWIRED"
    assert not any(card["malformed"].values())

def test_tv_cabinet_kind_matches_repo_synonym():
    doc = _convert(layer("F", prim(17, 1, "M 0,0 L 16,0 L 16,4 Z")))
    gt = doc["elements"][0]
    pred = dict(gt, kind="tv_console")             # our generator's name for the same thing
    assert B.score_identity([(gt, pred, 1.0)])["accuracy"] == 1.0

def test_json_roundtrip_and_batch_manifest(tmp_path=None):
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        svg_dir = os.path.join(td, "svgs")
        os.makedirs(svg_dir)
        for name, body in [("a", CAL + layer("F", prim(13, 1, "M 0,0 L 20,0 L 20,9 Z"))),
                           ("b", layer("W", prim(1, -1, "M 0,0 L 99,0")))]:
            with open(os.path.join(svg_dir, name + ".svg"), "w", encoding="utf-8") as fh:
                fh.write(_svg(body))
        out_dir = os.path.join(td, "gt")
        A.run_batch(svg_dir, out_dir)
        man = [json.loads(ln) for ln in
               open(os.path.join(out_dir, "manifest.jsonl"), encoding="utf-8")]
        assert [m["file"] for m in man] == ["a", "b"]
        assert man[0]["units"] == "mm" and man[1]["units"] == "svg-unit"
        assert os.path.exists(os.path.join(out_dir, "summary.md"))
        doc = json.load(open(os.path.join(out_dir, "a.gt.json"), encoding="utf-8"))
        assert doc["elements"][0]["kind"] == "sofa"
