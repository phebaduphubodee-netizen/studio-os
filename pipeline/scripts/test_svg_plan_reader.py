"""test_svg_plan_reader.py -- unit tests for the annotation-blind SVG reader lane.

The load-bearing test is BLINDNESS: the corpus SVGs carry the answer key inline
(semantic-id / instance-id / layer labels), so the reader must produce byte-identical
ink whether or not those attributes exist. Everything else is geometry plumbing.

    python -m pytest test_svg_plan_reader.py -q
"""
import json
import os

import benchmark_reader as B
import svg_plan_reader as R

SVG_HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<svg version="1.1" viewBox="0 0 100.0 100.0" '
            'xmlns="http://www.w3.org/2000/svg" '
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">\n')


def _write(tmp_path, name, body):
    fp = os.path.join(str(tmp_path), name)
    with open(fp, "w", encoding="utf-8") as fh:
        fh.write(SVG_HEAD + body + "</svg>\n")
    return fp


# ---- annotation blindness ----------------------------------------------------------------
ANNOTATED = ('<g id="layerWALL" inkscape:groupmode="layer" inkscape:label="WALL">\n'
             '<path d="M 10,10 L 20,10" semantic-id="1" instance-id="-1" '
             'stroke="rgb(0,0,0)" stroke-width="0.1"/>\n'
             '<path d="M 30,30 L 30,40 L 35,40" semantic-id="15" instance-id="7"/>\n'
             '<path d="M 60,60 L 70,60" semantic-id="5" instance-id="3"/>\n'
             '<circle cx="50" cy="50" r="2" semantic-id="23" instance-id="9"/>\n'
             '</g>\n')
STRIPPED = ('<g>\n'
            '<path d="M 10,10 L 20,10" stroke="rgb(0,0,0)" stroke-width="0.1"/>\n'
            '<path d="M 30,30 L 30,40 L 35,40"/>\n'
            '<path d="M 60,60 L 70,60"/>\n'
            '<circle cx="50" cy="50" r="2"/>\n'
            '</g>\n')


def _dense_pair():
    """(annotated, stripped) twin bodies with MORE annotated primitives than the densest
    real corpus sheet (0946-2738.svg: 3,905) -- round-2 scrutiny proved a leak gated on
    'many annotated attrs' (>10) slips past a small fixture while firing on 89.5% of
    the real corpus. Density >= corpus max makes any threshold leak inert on the whole
    benchmark BY CONSTRUCTION. Ids cycle the full 1..35 vocabulary so value-keyed skips
    (e.g. 'drop id 5') break strip-equivalence too."""
    ann, bare = [], []
    for k in range(4100):
        x, y = 5 + (k % 64) * 1.4, 5 + (k // 64) * 1.4
        d = f'M {x:.1f},{y:.1f} L {x + 1:.1f},{y:.1f}'
        ann.append(f'<path d="{d}" semantic-id="{1 + k % 35}" instance-id="{k % 97}"/>')
        bare.append(f'<path d="{d}"/>')
    return ('<g inkscape:groupmode="layer" inkscape:label="L1">\n'
            + "\n".join(ann) + '\n</g>\n',
            '<g>\n' + "\n".join(bare) + '\n</g>\n')


def test_reader_is_annotation_blind(tmp_path):
    a = R.read_ink(_write(tmp_path, "a.svg", ANNOTATED))
    b = R.read_ink(_write(tmp_path, "b.svg", STRIPPED))
    assert a == b, "reader output changed when annotation attributes were stripped"
    assert len(a["segs"]) == 1 + 2 + 1 + 16


def test_read_sheet_is_annotation_blind(tmp_path):
    """The BINDING blindness proof (scrutiny 2026-07-06: the static scan alone cannot
    bind -- attribute names live in string literals however the access is written).
    read_sheet end-to-end on an annotated sheet and its stripped twin must emit the
    identical pred document; any leak form whatsoever fails this, including one added
    later inside read_sheet itself."""
    a = R.read_sheet(_write(tmp_path, "a.svg", ANNOTATED), 100.0)
    b = R.read_sheet(_write(tmp_path, "b.svg", STRIPPED), 100.0)
    a["meta"].pop("file")
    b["meta"].pop("file")
    assert a == b, "read_sheet output changed when annotation attributes were stripped"


def test_read_sheet_blind_at_corpus_density(tmp_path):
    """Round-2 mutant killer: a leak firing only above an annotation-density threshold
    (>10 attrs) survived the small fixture while hitting 89.5% of real sheets. The
    dense twin (4,100 annotated prims > corpus max 3,905, all 35 ids) leaves such a
    leak nowhere to hide."""
    ann, bare = _dense_pair()
    a = R.read_sheet(_write(tmp_path, "dense_a.svg", ann), 100.0)
    b = R.read_sheet(_write(tmp_path, "dense_b.svg", bare), 100.0)
    a["meta"].pop("file")
    b["meta"].pop("file")
    assert a == b, "read_sheet output changed at corpus-level annotation density"


REAL_SHEET = os.path.join("C:\\", "Users", "teza_", "studio-datasets",
                          "floorplancad", "test-00", "0000-0009.svg")


def test_read_sheet_blind_on_real_corpus_sheet(tmp_path):
    """Corpus-twin: a REAL FloorPlanCAD sheet vs the same bytes with every annotation
    attribute deleted in-memory -- binds blindness against real-world structure the
    synthetic fixtures cannot imitate. Skips (never silently passes) off this machine."""
    import re

    import pytest
    if not os.path.exists(REAL_SHEET):
        pytest.skip("FloorPlanCAD corpus not present on this machine")
    raw = open(REAL_SHEET, encoding="utf-8").read()
    stripped = re.sub(r'\s(?:semantic-id|instance-id|inkscape:[\w-]+|id)="[^"]*"', "", raw)
    assert stripped != raw, "strip regex matched nothing -- fixture rotted"
    fa, fb = os.path.join(str(tmp_path), "real_a.svg"), os.path.join(str(tmp_path), "real_b.svg")
    open(fa, "w", encoding="utf-8").write(raw)
    open(fb, "w", encoding="utf-8").write(stripped)
    a, b = R.read_sheet(fa, 100.0), R.read_sheet(fb, 100.0)
    a["meta"].pop("file")
    b["meta"].pop("file")
    assert a == b, "read_sheet output changed when a real sheet's annotations were stripped"


def test_reader_source_never_names_annotation_attrs():
    """Static tripwire (secondary to the behavioral test above): the reader module must
    not name the answer-key attributes in executable code NOR in any string literal
    except the module docstring (which documents the honesty contract). Catches the
    obvious el.get(\"...\") leak at review time; split-string obfuscation is caught by
    the behavioral test, not this one."""
    import io
    import tokenize
    src = open(R.__file__, encoding="utf-8").read()
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    strings = [t.string for t in toks if t.type == tokenize.STRING]
    module_doc = strings[0] if strings else ""
    code = " ".join(t.string for t in toks
                    if t.type not in (tokenize.COMMENT, tokenize.STRING))
    for needle in ("semantic", "inkscape", "INK_NS", "instance_id"):
        assert needle not in code, f"reader code references {needle!r}"
    for s in strings:
        if s is module_doc:
            continue
        for needle in ("semantic-id", "instance-id", "inkscape"):
            assert needle not in s, f"reader string literal references {needle!r}: {s[:80]}"


# ---- ink extraction ----------------------------------------------------------------------
def test_path_ink_polylines_and_curves():
    segs, csegs = R._path_ink("M 0,0 L 10,0 L 10,5")
    assert segs == [[(0.0, 0.0), (10.0, 0.0)], [(10.0, 0.0), (10.0, 5.0)]]
    assert csegs == []
    # arc: sweep samples connect through (curve segs present, chain unbroken)
    segs, csegs = R._path_ink("M 0,0 A 5,5 0 0 1 10,0")
    assert len(segs) >= 8 and csegs
    # move breaks the chain
    segs, _ = R._path_ink("M 0,0 L 10,0 M 20,0 L 30,0")
    assert len(segs) == 2


def test_read_ink_counts_and_shapes(tmp_path):
    body = ('<path d="M 1,1 L 2,1" transform="translate(3,3)"/>\n'
            '<text x="5" y="5">3600</text>\n'
            '<rect x="10" y="10" width="4" height="2"/>\n'
            '<polygon points="20,20 25,20 25,25"/>\n'
            '<polyline points="30,30 35,30 35,35"/>\n')
    ink = R.read_ink(_write(tmp_path, "c.svg", body))
    assert ink["transforms_skipped"] == 1      # transform-bearing prim skipped, counted
    assert ink["text_skipped"] == 1
    assert len(ink["segs"]) == 4 + 3 + 2       # rect ring + closed polygon + open polyline


# ---- sheet -> pred -----------------------------------------------------------------------
def _sheet_svg(tmp_path):
    # scale 100 mm/unit: 6x6-unit rect = 600x600 mm symbol; two 12-unit verticals
    # 1 unit (=100 mm) apart = a glazing-style pair 1200 mm long
    body = ('<rect x="10" y="10" width="6" height="6"/>\n'
            '<path d="M 50,10 L 50,22"/>\n'
            '<path d="M 51,10 L 51,22"/>\n')
    return _write(tmp_path, "sheet.svg", body)


def test_read_sheet_clusters_and_openings(tmp_path):
    pred = R.read_sheet(_sheet_svg(tmp_path), 100.0)
    assert pred["meta"]["units"] == "mm"
    assert pred["meta"]["res_mm_per_px"] == R.BASE_RES_MM
    els = pred["elements"]
    assert len(els) == 1, els                  # the pair lines are thin -> not furniture
    e = els[0]
    assert abs(e["w"] - 600) <= 2 * R.BASE_RES_MM and abs(e["d"] - 600) <= 2 * R.BASE_RES_MM
    # position pin: same frame as gt.json (raw svg frame x scale, y down, NO flip) and
    # scale applied exactly once -- a y-flip or double-scale regression fails here
    assert abs(e["x"] - 1000) <= 2 * R.BASE_RES_MM and abs(e["y"] - 1000) <= 2 * R.BASE_RES_MM
    assert "kind" not in e                     # no classifier -> no kind, ever
    ops = pred["openings"]
    assert ops and all(o["type"] == "candidate" for o in ops)
    assert any(abs(o["x"] - 5000) < 60 or abs(o["x"] - 5100) < 60 for o in ops)


def test_candidate_type_never_earns_subtype_credit():
    """Mutation pin (scrutiny 2026-07-06): the earlier type='opening' sentinel silently
    collected F4 subtype credit against GT bare-opening symbols (5/15 smoke sheets
    scored nonzero subtype accuracy with zero classifiers). 'candidate' sits outside
    the GT vocabulary, so subtype accuracy must stay 0 even on a perfect location hit."""
    gt = [{"type": "opening", "x": 0, "y": 0, "w": 100, "d": 1000}]
    pred = [{"type": "candidate", "x": 0, "y": 0, "w": 100, "d": 1000}]
    f4 = B.score_openings(gt, pred)
    assert f4["matched"] == 1
    assert f4["subtype_accuracy"] == 0.0
    assert f4["subtype_confusion"] == {"opening->candidate": 1}


def test_read_sheet_res_caps_on_huge_sheets(tmp_path):
    """Round-2 mutant killer: the bound is pinned to the LITERAL 3000, not to
    R.MAX_RASTER_PX -- a self-referential assert survived MAX_RASTER_PX -> 30000,
    which un-caps the raster (a 500 m sheet at 6 mm/px = ~83k px per axis: OOM)."""
    fp = _write(tmp_path, "huge.svg", '<path d="M 0,0 L 100,0"/>\n')
    pred = R.read_sheet(fp, 5000.0)            # 500 m sheet
    res = pred["meta"]["res_mm_per_px"]
    assert res > R.BASE_RES_MM
    assert (100 * 5000.0 + 2 * R.ZONE_PAD_MM) / res <= 3001


def test_read_sheet_empty_svg(tmp_path):
    pred = R.read_sheet(_write(tmp_path, "empty.svg", ""), 100.0)
    assert pred["elements"] == [] and pred["openings"] == []


# ---- baseline runner ---------------------------------------------------------------------
def test_run_baseline_skips_and_scores(tmp_path):
    svg_dir = os.path.join(str(tmp_path), "svg")
    gt_dir = os.path.join(str(tmp_path), "gt")
    out_dir = os.path.join(str(tmp_path), "out")
    os.makedirs(svg_dir)
    os.makedirs(gt_dir)
    _sheet = _sheet_svg(tmp_path)
    os.replace(_sheet, os.path.join(svg_dir, "s1.svg"))
    gt_mm = {"meta": {"units": "mm", "scale_mm_per_unit": 100.0},
             "elements": [{"id": "g1", "kind": "table",
                           "x": 1000, "y": 1000, "w": 600, "d": 600}],
             "openings": [{"type": "sliding", "x": 5000, "y": 1000, "w": 100, "d": 1200}]}
    with open(os.path.join(gt_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
        json.dump(gt_mm, fh)
    with open(os.path.join(gt_dir, "s2.gt.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": {"units": "svg-unit", "scale_mm_per_unit": None},
                   "elements": [], "openings": []}, fh)
    with open(os.path.join(gt_dir, "s3.gt.json"), "w", encoding="utf-8") as fh:
        json.dump(gt_mm, fh)                   # mm units but no s3.svg on disk
    # round-2 mutant killer: an exception INSIDE the per-sheet try must be COUNTED
    # (deleting the skipped['error'] increment passed the old suite vacuously) --
    # units say mm but scale is null, so float(None) raises after the skip checks
    with open(os.path.join(gt_dir, "s0.gt.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": {"units": "mm", "scale_mm_per_unit": None},
                   "elements": [], "openings": []}, fh)
    import shutil
    shutil.copy(os.path.join(svg_dir, "s1.svg"), os.path.join(svg_dir, "s0.svg"))
    cards, skipped = R.run_baseline(svg_dir, gt_dir, out_dir)
    assert len(cards) == 1
    assert skipped == {"svg-unit": 1, "svg-missing": 1, "error": 1}
    card = cards[0]
    assert card["detection"]["matched"] == 1           # the 600x600 symbol is found
    assert card["F1_identity"]["accuracy"] == 0.0      # honest: reader has no classifier
    assert card["F4_openings"]["per_type_gt"]["sliding"]["matched"] == 1
    assert card["F2_facing"]["verdict"] == "UNWIRED"
    assert os.path.exists(os.path.join(out_dir, "preds", "s1.pred.json"))
    assert os.path.exists(os.path.join(out_dir, "report.md"))
    rep = open(os.path.join(out_dir, "report.md"), encoding="utf-8").read()
    assert "sliding: 1/1" in rep
    rows = [json.loads(l) for l in open(os.path.join(out_dir, "cards.jsonl"),
                                        encoding="utf-8")]
    assert sum(1 for r in rows if r.get("skipped")) == 3
    err_rows = [r for r in rows if r.get("skipped") == "error"]
    assert len(err_rows) == 1 and "TypeError" in err_rows[0]["error"]
    assert len(rows) == 4                      # every gt file got exactly one row


def test_report_without_cards_is_honest():
    rep = R.render_baseline_report([], {"svg-unit": 3, "svg-missing": 0, "error": 0}, 3, 1.0)
    assert "no sheets scored" in rep


def test_overlay_writes_png(tmp_path):
    pred = R.read_sheet(_sheet_svg(tmp_path), 100.0)
    out = os.path.join(str(tmp_path), "ov.png")
    # gt opening WITHOUT w/d: sanitize_openings tolerates it in scoring, so the picture
    # must too (round-2 probe: raw o['w'] access crashed the overlay AFTER the card row)
    R.render_overlay(pred, {"elements": [], "openings": [{"x": 0, "y": 0}]},
                     [[(0, 0), (1000, 0)]], out)
    assert os.path.getsize(out) > 0


# ---- benchmark_reader per-type extension (used by the report headline) --------------------
def test_score_openings_per_type_gt():
    gt = [{"type": "sliding", "x": 0, "y": 0, "w": 100, "d": 1000},
          {"type": "door", "x": 5000, "y": 0, "w": 900, "d": 100}]
    pred = [{"type": "opening", "x": 0, "y": 0, "w": 100, "d": 1000}]
    f4 = B.score_openings(gt, pred)
    assert f4["per_type_gt"]["sliding"] == {"n_gt": 1, "matched": 1, "recall": 1.0}
    assert f4["per_type_gt"]["door"] == {"n_gt": 1, "matched": 0, "recall": 0.0}


def test_per_type_recall_denominator_with_multiple_gt():
    """Round-2 mutant killer: every earlier pin used n_gt=1 per type, where a corrupted
    denominator (matched/max(1, n_gt-1)) is indistinguishable from matched/n_gt. Two
    sliding doors, one found -> the per-sheet triage number must read 0.5, not 1.0."""
    gt = [{"type": "sliding", "x": 0, "y": 0, "w": 100, "d": 1000},
          {"type": "sliding", "x": 9000, "y": 0, "w": 100, "d": 1000}]
    pred = [{"type": "candidate", "x": 0, "y": 0, "w": 100, "d": 1000}]
    f4 = B.score_openings(gt, pred)
    assert f4["per_type_gt"]["sliding"] == {"n_gt": 2, "matched": 1, "recall": 0.5}


def test_per_type_matched_uses_gt_index_set():
    """Round-2 mutant killer: counting per-type matches with the PRED index set survived
    every fixture where matched gt/pred indices coincided at 0. An unmatched door at
    gt index 0 + a matched sliding at gt index 1 makes the two sets differ: the mutant
    (i in used_p) INVERTS the headline (door 100%/sliding 0%) -- pin the true counts."""
    gt = [{"type": "door", "x": 90000, "y": 0, "w": 900, "d": 100},
          {"type": "sliding", "x": 0, "y": 0, "w": 1800, "d": 100}]
    pred = [{"type": "sliding", "x": 0, "y": 0, "w": 1800, "d": 100}]
    f4 = B.score_openings(gt, pred)
    assert f4["per_type_gt"]["sliding"] == {"n_gt": 1, "matched": 1, "recall": 1.0}
    assert f4["per_type_gt"]["door"] == {"n_gt": 1, "matched": 0, "recall": 0.0}


def test_aggregate_sums_per_type_gt():
    gt_doc = {"elements": [], "openings": [{"type": "sliding", "x": 0, "y": 0,
                                            "w": 100, "d": 1000}]}
    hit = {"elements": [], "openings": [{"type": "opening", "x": 0, "y": 0,
                                         "w": 100, "d": 1000}]}
    miss = {"elements": [], "openings": []}
    cards = [B.score_pair(gt_doc, hit), B.score_pair(gt_doc, miss)]
    agg = B.aggregate(cards)
    assert agg["F4_openings"]["per_type_gt"]["sliding"] == {
        "n_gt": 2, "matched": 1, "recall": 0.5}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
