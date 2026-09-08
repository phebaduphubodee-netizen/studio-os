"""Tests for blind_wall_lane -- the un-oracled wall tier (naive / BLIND / oracle arms).

The load-bearing pins:
  - IDENTITY PIN: the appended wall ink is exactly read_ink's tail slice (a shifted
    slice RAISES and lands in the error counter, never scores);
  - PERFECT-DETECTION EQUIVALENCE: when the detector classifies exactly the true wall
    ink and its centerline matches gt, the blind arm's cards EQUAL the oracle arm's --
    the two arms differ only by detector error, by construction;
  - the blind arm SPLITS the fused cross-wall pair the naive arm cannot (the lane's
    reason to exist), end-to-end through the real SVG round-trip;
  - ZERO-WALLS: a scene without walls scores all three arms identical;
  - ANNOTATION BLINDNESS: two gt docs differing only in indoor labels produce identical
    blind-arm detection (geometry never reads the labels);
  - F2 SURVIVAL: a facing element's back-strip near a wall keeps its rot emission in the
    blind arm (the co-terminous screen working end-to-end);
  - the symbol tier rows exist, the wall-partitioned unit fires (n_regions >= 2), and
    blind == oracle symbol counts on a clean scene;
  - skip taxonomy: units/error are counted, rows land in cards.jsonl, and the report
    carries the BLIND tier banner + the ALL-GREEN reconciliation line.
"""
import json
import os
import tempfile

import blind_wall_lane as L


def _el(id_, x, y, w, d, kind=None, rot=None, indoor=None):
    e = {"id": id_, "x": float(x), "y": float(y), "w": float(w), "d": float(d)}
    if kind is not None:
        e["kind"] = kind
    if rot is not None:
        e["rot"] = float(rot)
    if indoor is not None:
        e["indoor"] = indoor
    return e


def _wall(x1, y1, x2, y2):
    return {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def _doc(elements, walls=None):
    return {"meta": {"units": "mm", "n_elements": len(elements)},
            "elements": [dict(e) for e in elements], "openings": [],
            "glazing_lines": [], "wall_lines": list(walls or [])}


def _det_counts(card):
    d = card["detection"]
    return (d["n_gt"], d["n_pred"], d["matched"])


def _scene(gt, symbol=True):
    with tempfile.TemporaryDirectory() as td:
        return L.score_scene(gt, td, symbol=symbol)


# the fused-pair scene: two 800x600 rects at a 60mm edge gap (inside the reader's ~90mm
# fusion distance), a vertical wall between them (test_wall_aware_lane calibration)
def _fused_pair_doc():
    return _doc([_el("a", 0, 0, 800, 600), _el("b", 860, 0, 800, 600)],
                walls=[_wall(830, -400, 830, 1000)])


def test_identity_pin_and_detector_confusion_clean_scene():
    row = _scene(_fused_pair_doc(), symbol=False)
    d = row["detector"]
    assert row["n_walls_drawn"] == 2               # two face lines for one wall
    assert d["tp"] == 2 and d["fn"] == 0           # both faces classified
    assert d["strips_eaten"] == 0
    assert d["cov"]["recall_len"] > 0.99 and d["cov"]["walls_zero"] == 0


def test_blind_splits_what_naive_fuses_and_matches_oracle():
    """End-to-end: naive fuses the pair (0 matched), blind splits at the DETECTED wall
    (2 matched), and with a perfect classification the blind cards EQUAL oracle's."""
    row = _scene(_fused_pair_doc(), symbol=False)
    assert _det_counts(row["card_naive"]) == (2, 1, 0)
    assert _det_counts(row["card_blind"]) == (2, 2, 2)
    assert _det_counts(row["card_oracle"]) == (2, 2, 2)
    assert row["detector"]["fp"] == 0 and row["detector"]["fn"] == 0
    # perfect detection -> the arms are the same computation
    assert _det_counts(row["card_blind"]) == _det_counts(row["card_oracle"])
    assert row["f2_nobed_blind"] == row["f2_nobed_oracle"]
    t = row["f2_transitions_o2b"]
    assert t["changed"] == {} and t["left_matched_set"] == 0


def test_zero_walls_all_arms_identical():
    gt = _doc([_el("a", 0, 0, 1200, 700), _el("b", 2500, 1500, 900, 400)])
    row = _scene(gt, symbol=False)
    assert row["n_walls_drawn"] == 0
    assert (_det_counts(row["card_naive"]) == _det_counts(row["card_blind"])
            == _det_counts(row["card_oracle"]))
    assert row["detector"]["tp"] == 0 and row["detector"]["fn"] == 0


def test_annotation_blindness_indoor_never_read():
    a = _fused_pair_doc()
    b = _fused_pair_doc()
    for e in b["elements"]:
        e["indoor"] = False
    ra = _scene(a, symbol=False)
    rb = _scene(b, symbol=False)
    assert _det_counts(ra["card_blind"]) == _det_counts(rb["card_blind"])
    assert ra["detector"] == rb["detector"]


def test_f2_strip_survives_blind_masking():
    """A sofa backed near a wall: its back-strip is parallel wall-window ink, and losing
    it to the detector = losing the F2 emission. Walls flank BOTH long sides so the pin
    holds regardless of which side the strip lands on."""
    gt = _doc([_el("s", 0, 0, 2000, 900, kind="sofa", rot=0.0)],
              walls=[_wall(-400, -150, 2400, -150), _wall(-400, 1050, 2400, 1050)])
    row = _scene(gt, symbol=False)
    assert row["strips"]["strips_drawn"] == 1
    assert row["detector"]["strips_eaten"] == 0
    assert row["emit_blind"]["rot_emitted"] == row["emit_oracle"]["rot_emitted"] == 1
    assert row["f2_nobed_blind"]["hits"] == 1


def test_symbol_tier_rows_and_partition():
    """A closed two-room box (ring + divider): the region partition must fire (left room,
    right room, outside), the plain 90mm grouping would FUSE the 60mm-gap pair into one
    symbol, and the wall-partitioned unit must keep them apart -- with a perfect detector
    the blind and oracle symbol counts are equal."""
    gt = _doc([_el("a", 0, 0, 800, 600), _el("b", 860, 0, 800, 600)],
              walls=[_wall(-200, -200, 1900, -200), _wall(1900, -200, 1900, 800),
                     _wall(1900, 800, -200, 800), _wall(-200, 800, -200, -200),
                     _wall(830, -200, 830, 800)])
    row = _scene(gt, symbol=True)
    assert "sym_blind" in row and "sym_oracle" in row
    assert row["n_regions"] >= 3                   # left room / right room / outside
    assert row["sym_blind"]["symbol"]["n_sym"] == 2      # partitioned unit: NOT one fused symbol
    assert row["sym_blind"]["symbol"] == row["sym_oracle"]["symbol"]
    assert sum(row["sym_blind"]["buckets"].values()) == 2


def test_equivalence_pin_computed_not_prose():
    """The cross-sheet claim must be COMPUTED per run (adversarial review: it was a
    hardcoded 'verified 0-mismatch' f-string). A matching committed card -> GREEN with
    0 mismatches; a mutated one -> mismatch counted AND ALL-GREEN killed; no pin dir ->
    the report says the references are UNVERIFIED."""
    gt = _fused_pair_doc()
    row = _scene(gt, symbol=False)
    d = row["card_oracle"]["detection"]
    committed = {"scene": "s1", "card_after": {"detection": {
        "n_gt": d["n_gt"], "n_pred": d["n_pred"], "matched": d["matched"],
        "missed_ids": d.get("missed_ids") or []}}}
    with tempfile.TemporaryDirectory() as td:
        gt_dir = os.path.join(td, "gt")
        os.makedirs(gt_dir)
        with open(os.path.join(gt_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
            json.dump(gt, fh)
        pin_dir = os.path.join(td, "committed")
        os.makedirs(pin_dir)
        with open(os.path.join(pin_dir, "cards.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(committed) + "\n")
        out1 = os.path.join(td, "out1")
        L.score_corpus(gt_dir, out1, symbol=False, pin_dir=pin_dir)
        rep = open(os.path.join(out1, "report.md"), encoding="utf-8").read()
        assert "1 compared, **0 mismatch(es)**" in rep and "GREEN" in rep
        # mutate the committed card -> mismatch + NOT GREEN
        committed["card_after"]["detection"]["matched"] += 1
        with open(os.path.join(pin_dir, "cards.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(committed) + "\n")
        out2 = os.path.join(td, "out2")
        L.score_corpus(gt_dir, out2, symbol=False, pin_dir=pin_dir)
        rep2 = open(os.path.join(out2, "report.md"), encoding="utf-8").read()
        assert "**1 mismatch(es)**" in rep2 and "NOT GREEN" in rep2
        # no pin dir -> explicit UNVERIFIED line, never a verification claim
        out3 = os.path.join(td, "out3")
        L.score_corpus(gt_dir, out3, symbol=False)
        rep3 = open(os.path.join(out3, "report.md"), encoding="utf-8").read()
        assert "EQUIVALENCE PIN NOT RUN" in rep3
        assert "verified 0-mismatch" not in rep3


def test_naive_wallink_contamination_measured():
    """The wall-prior-in-disguise instrument: a rot-less element over a wall gains a
    naive-arm rot emission from gt wall ink; the instrument must count it and blind/
    oracle must stay silent (their ink is masked)."""
    gt = _doc([_el("s", 0, 0, 2000, 600)],
              walls=[_wall(100, 550, 1900, 550)])
    row = _scene(gt, symbol=False)
    assert row["strips"]["strips_drawn"] == 0
    assert row["emit_naive"]["rot_emitted"] == 1
    assert row["naive_wallink_rot"] == 1
    assert row["emit_blind"]["rot_emitted"] == 0
    assert row["emit_oracle"]["rot_emitted"] == 0


def test_corpus_skip_taxonomy_and_report_banner():
    good = _fused_pair_doc()
    bad_units = _doc([_el("a", 0, 0, 800, 600)])
    bad_units["meta"]["units"] = "svg-unit"
    broken = {"meta": {"units": "mm"}, "elements": [{"id": "x", "x": "NOT_A_NUMBER",
              "y": 0, "w": 500, "d": 500}], "wall_lines": "not-a-list"}
    with tempfile.TemporaryDirectory() as td:
        gt_dir = os.path.join(td, "gt")
        out_dir = os.path.join(td, "out")
        os.makedirs(gt_dir)
        for name, doc in (("s1", good), ("s2", bad_units), ("s3", broken)):
            with open(os.path.join(gt_dir, f"{name}.gt.json"), "w", encoding="utf-8") as fh:
                json.dump(doc, fh)
        rows, skipped = L.score_corpus(gt_dir, out_dir, symbol=False)
        assert len(rows) == 1
        assert skipped["units"] == 1 and skipped["error"] == 1
        report = open(os.path.join(out_dir, "report.md"), encoding="utf-8").read()
        assert "TIER: BLIND" in report
        assert "ALL-GREEN reconciliation: NOT GREEN" in report
        lines = open(os.path.join(out_dir, "cards.jsonl"), encoding="utf-8").read().splitlines()
        assert len(lines) == 3
        kinds = {json.loads(x).get("skipped") for x in lines}
        assert kinds == {None, "units", "error"}
