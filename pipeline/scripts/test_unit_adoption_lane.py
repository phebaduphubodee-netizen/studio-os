"""Tests for unit_adoption_lane -- option C's bridge and report pins.

  - the row carries the full unit matrix and, with a perfect detector, the blind and
    oracle symbol cards agree (arms differ only by detector error, by construction);
  - DETECTION IS ENRICHMENT-INVARIANT: the committed cards scored F2-ENRICHED preds,
    this lane scores un-enriched ones -- pinned equal (rot never enters IoU matching);
  - THE BRIDGE: pins vs a real committed blind_wall_lane run are GREEN when untouched;
    a mutated committed symbol instrument OR detection card kills ALL-GREEN with the
    face named; a run without --pin-cards prints UNBRIDGED and is never green;
  - skip taxonomy: units / error / drift_assert all counted, all in the green line;
  - the report headlines the adopted unit, demotes per-object, prints the UNIT LAW and
    the measured canvas delta; the blind>oracle alarm helper fires only on blind wins.
"""
import json
import os
import tempfile

import blind_wall_lane as BWL
import benchmark_reader as B
import f2_facing_lane as F2L
import plan_symbol_unit as PSU
import unit_adoption_lane as L


def _el(id_, x, y, w, d, kind=None, rot=None):
    e = {"id": id_, "x": float(x), "y": float(y), "w": float(w), "d": float(d)}
    if kind is not None:
        e["kind"] = kind
    if rot is not None:
        e["rot"] = float(rot)
    return e


def _wall(x1, y1, x2, y2):
    return {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def _doc(elements, walls=None):
    return {"meta": {"units": "mm", "n_elements": len(elements)},
            "elements": [dict(e) for e in elements], "openings": [],
            "glazing_lines": [], "wall_lines": list(walls or [])}


def _two_room_doc():
    return _doc([_el("a", 0, 0, 800, 600), _el("b", 860, 0, 800, 600)],
                walls=[_wall(-200, -200, 1900, -200), _wall(1900, -200, 1900, 800),
                       _wall(1900, 800, -200, 800), _wall(-200, 800, -200, -200),
                       _wall(830, -200, 830, 800)])


def _scene(gt, **kw):
    with tempfile.TemporaryDirectory() as td:
        return L.score_scene(gt, td, **kw)


def test_row_unit_matrix_and_perfect_detector_equivalence():
    row = _scene(_two_room_doc())
    for k in ("card_gt_blind", "card_gt_oracle", "card_plain_blind",
              "card_plain_oracle", "sym_ink_blind", "sym_ink_oracle"):
        assert k in row
    assert row["card_gt_blind"]["unit_id"] == PSU.UNIT_GTWALL
    assert row["card_plain_blind"]["unit_id"] == PSU.UNIT_PLAIN
    assert row["card_gt_blind"]["n_sym"] == 2          # divider splits the 60mm pair
    assert row["card_plain_blind"]["n_sym"] == 1       # plain unit fuses it
    # perfect detector on this scene: blind == oracle everywhere that matters
    assert row["card_gt_blind"]["symbol"] == row["card_gt_oracle"]["symbol"]
    assert row["sym_ink_blind"]["symbol"] == row["sym_ink_oracle"]["symbol"]
    assert (row["det_blind"]["n_gt"], row["det_blind"]["n_pred"],
            row["det_blind"]["matched"]) == (2, 2, 2)
    assert row["det_blind"]["matched"] == row["det_oracle"]["matched"]


def test_detection_scored_on_enriched_pred_matching_committed():
    """The committed blind-walls card_blind scored the F2-ENRICHED pred; this lane must
    score the SAME enriched pred so the detection bridge pin is exact-by-construction
    (not merely rot-invariant-up-to-0.1mm-rounding). Pin: row['det_blind'] == score_pair
    on the lane's own enriched pred, and equals the committed pipeline's card."""
    gt = _doc([_el("s", 0, 0, 2000, 900, kind="sofa", rot=0.0)],
              walls=[_wall(-400, -150, 2400, -150), _wall(-400, 1050, 2400, 1050)])
    with tempfile.TemporaryDirectory() as td:
        row, preds = L.score_scene(gt, td, return_preds=True)
    det_enriched = B.score_pair(gt, preds["pred_bv"])["detection"]
    # score_scene keeps the full card (missed_ids shed later in score_corpus, AFTER pins)
    assert row["det_blind"] == det_enriched
    # and the lane's enriched pred is exactly what blind_wall_lane enriches (same call)
    pred_bv_ref, _e = F2L.enrich_pred_with_facing(preds["pred_b"], preds["segs_b"])
    assert B.score_pair(gt, pred_bv_ref)["detection"] == row["det_blind"]


def _mini_corpus(td, gt):
    gt_dir = os.path.join(td, "gt")
    os.makedirs(gt_dir)
    with open(os.path.join(gt_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
        json.dump(gt, fh)
    committed = os.path.join(td, "committed")
    BWL.score_corpus(gt_dir, committed, symbol=True)
    return gt_dir, committed


def test_bridge_pins_green_then_mutations_kill():
    gt = _two_room_doc()
    with tempfile.TemporaryDirectory() as td:
        gt_dir, committed = _mini_corpus(td, gt)

        out1 = os.path.join(td, "out1")
        L.score_corpus(gt_dir, out1, pin_dir=committed)
        rep = open(os.path.join(out1, "report.md"), encoding="utf-8").read()
        assert "1 compared, **0 mismatch(es)**" in rep
        assert "ALL-GREEN reconciliation: GREEN" in rep

        # mutate the committed SYMBOL instrument -> sym face named, NOT GREEN
        cards_p = os.path.join(committed, "cards.jsonl")
        card = json.loads(open(cards_p, encoding="utf-8").read())
        card["sym_blind"]["symbol"]["matched"] += 1
        with open(cards_p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(card) + "\n")
        out2 = os.path.join(td, "out2")
        L.score_corpus(gt_dir, out2, pin_dir=committed)
        rep2 = open(os.path.join(out2, "report.md"), encoding="utf-8").read()
        assert "**1 mismatch(es)**" in rep2 and "sym_blind" in rep2
        assert "ALL-GREEN reconciliation: NOT GREEN" in rep2

        # mutate the committed detection card instead -> det face named, NOT GREEN
        card["sym_blind"]["symbol"]["matched"] -= 1
        card["card_blind"]["detection"]["matched"] += 1
        with open(cards_p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(card) + "\n")
        out3 = os.path.join(td, "out3")
        L.score_corpus(gt_dir, out3, pin_dir=committed)
        rep3 = open(os.path.join(out3, "report.md"), encoding="utf-8").read()
        assert "det_blind" in rep3 and "NOT GREEN" in rep3

        # no --pin-cards -> UNBRIDGED, never green
        out4 = os.path.join(td, "out4")
        L.score_corpus(gt_dir, out4)
        rep4 = open(os.path.join(out4, "report.md"), encoding="utf-8").read()
        assert "OFFICIAL NUMBERS UNBRIDGED" in rep4
        assert "ALL-GREEN reconciliation: NOT GREEN" in rep4


def test_bridge_pin_nregions_and_oracle_faces():
    """C11: the n_regions face and the det_oracle/sym_oracle faces are pinned too, not
    just det_blind/sym_blind. Mutate the committed n_regions -> the n_regions face fires;
    mutate the committed oracle detection -> the det_oracle face fires."""
    gt = _two_room_doc()
    with tempfile.TemporaryDirectory() as td:
        gt_dir, committed = _mini_corpus(td, gt)
        cards_p = os.path.join(committed, "cards.jsonl")
        base = json.loads(open(cards_p, encoding="utf-8").read())

        c1 = dict(base)
        c1["n_regions"] = int(base["n_regions"]) + 7
        with open(cards_p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(c1) + "\n")
        o1 = os.path.join(td, "o1")
        L.score_corpus(gt_dir, o1, pin_dir=committed)
        rep = open(os.path.join(o1, "report.md"), encoding="utf-8").read()
        assert '"n_regions"' in rep and "NOT GREEN" in rep

        c2 = dict(base)
        c2["card_oracle"]["detection"]["matched"] += 1
        with open(cards_p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(c2) + "\n")
        o2 = os.path.join(td, "o2")
        L.score_corpus(gt_dir, o2, pin_dir=committed)
        rep2 = open(os.path.join(o2, "report.md"), encoding="utf-8").read()
        assert "det_oracle" in rep2 and "NOT GREEN" in rep2


def test_bridge_absent_face_kills_green():
    """A scored scene missing from the committed pins is 'absent' and kills green
    (its OFFICIAL number was never verified against a committed card)."""
    gt = _two_room_doc()
    with tempfile.TemporaryDirectory() as td:
        gt_dir, committed = _mini_corpus(td, gt)
        # committed pins are for a DIFFERENT scene id -> this run's scene is absent
        cards_p = os.path.join(committed, "cards.jsonl")
        card = json.loads(open(cards_p, encoding="utf-8").read())
        card["scene"] = "other_scene"
        with open(cards_p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(card) + "\n")
        out = os.path.join(td, "out")
        L.score_corpus(gt_dir, out, pin_dir=committed)
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
        assert "absent 1" in rep and "NOT GREEN" in rep


def test_degenerate_walls_counted_no_walls_and_trivial():
    """A scene whose only wall_lines are zero-length has NO usable walls: it must count
    as no_walls (not silently 0) and score plain geometry under the GTWALL stamp, which
    the report discloses as a no-real-partition scene (review: `if not wall_lines` alone
    missed the all-degenerate case)."""
    gt = _doc([_el("a", 0, 0, 800, 600)], walls=[_wall(500, 500, 500, 500)])
    assert L._has_usable_walls(gt) is False
    row = _scene(gt)
    assert row["n_regions_gt"] == 0
    assert row["card_gt_blind"]["unit_id"] == PSU.UNIT_GTWALL   # id never silently flips
    with tempfile.TemporaryDirectory() as td:
        gt_dir = os.path.join(td, "gt")
        os.makedirs(gt_dir)
        with open(os.path.join(gt_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
            json.dump(gt, fh)
        out = os.path.join(td, "out")
        _rows, skipped = L.score_corpus(gt_dir, out)
        assert skipped["no_walls"] == 1
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
        assert "no-real-partition scenes (n_regions_gt<=1): 1/1" in rep
        assert "NO scene in this corpus has usable walls" in rep   # rule-4 corpus warning


def test_limit_truncation_is_disclosed():
    """A limit run over a larger corpus must read as PARTIAL, never as full coverage of
    a small corpus, and must never be GREEN (review: partial numbers passing as corpus)."""
    with tempfile.TemporaryDirectory() as td:
        gt_dir = os.path.join(td, "gt")
        os.makedirs(gt_dir)
        for i in range(3):
            with open(os.path.join(gt_dir, f"s{i}.gt.json"), "w", encoding="utf-8") as fh:
                json.dump(_two_room_doc(), fh)
        out = os.path.join(td, "out")
        L.score_corpus(gt_dir, out, limit=1)
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
        assert "PARTIAL RUN: limit=1 of 3" in rep
        assert "NOT GREEN" in rep


def test_pinned_but_unscored_reconciliation_kills_green():
    """A pin file with MORE scenes than were scored must not stay green (the
    2026-07-10b lesson: the green flag and the skip taxonomy must both see it)."""
    gt = _two_room_doc()
    with tempfile.TemporaryDirectory() as td:
        gt_dir, committed = _mini_corpus(td, gt)
        # append a second committed scene this run will never score
        cards_p = os.path.join(committed, "cards.jsonl")
        card = json.loads(open(cards_p, encoding="utf-8").read())
        ghost = dict(card)
        ghost["scene"] = "s2"
        with open(cards_p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ghost) + "\n")
        out = os.path.join(td, "out")
        L.score_corpus(gt_dir, out, pin_dir=committed)
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
        assert "pinned-but-unscored 1" in rep
        assert "ALL-GREEN reconciliation: NOT GREEN" in rep


def test_report_headline_demotion_law_and_delta():
    gt = _two_room_doc()
    with tempfile.TemporaryDirectory() as td:
        gt_dir, committed = _mini_corpus(td, gt)
        out = os.path.join(td, "out")
        L.score_corpus(gt_dir, out, pin_dir=committed)
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
    assert PSU.UNIT_GTWALL in rep and PSU.UNIT_PLAIN in rep
    assert "OFFICIAL HEADLINE" in rep
    assert "DEMOTED to diagnostic" in rep
    assert "UNIT LAW" in rep
    assert "canvas delta" in rep
    assert "alarm clear" in rep                       # blind never beats oracle here
    # green run: headline is QUOTABLE and the delta is LICENSED
    assert "QUOTABLE" in rep and "UNQUOTABLE" not in rep
    assert "LICENSED: the bridge pins above are GREEN" in rep


def test_canvas_delta_unlicensed_and_headline_unquotable_without_pins():
    """C1/C4/C7: without pins the headline is UNQUOTABLE and the canvas delta is
    explicitly UNLICENSED -- the licensing prose must not print when there are no pins."""
    gt = _two_room_doc()
    with tempfile.TemporaryDirectory() as td:
        gt_dir = os.path.join(td, "gt")
        os.makedirs(gt_dir)
        with open(os.path.join(gt_dir, "s1.gt.json"), "w", encoding="utf-8") as fh:
            json.dump(gt, fh)
        out = os.path.join(td, "out")
        L.score_corpus(gt_dir, out)                   # no --pin-cards
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
    assert "OFFICIAL HEADLINE" in rep and "UNQUOTABLE" in rep
    assert "UNLICENSED" in rep
    assert "LICENSED: the bridge pins above are GREEN" not in rep


def test_skip_taxonomy_units_error_drift():
    good = _two_room_doc()
    bad_units = _doc([_el("a", 0, 0, 800, 600)])
    bad_units["meta"]["units"] = "svg-unit"
    broken = {"meta": {"units": "mm"}, "elements": [{"id": "x", "x": "NOT_A_NUMBER",
              "y": 0, "w": 500, "d": 500}], "wall_lines": "not-a-list"}
    with tempfile.TemporaryDirectory() as td:
        gt_dir = os.path.join(td, "gt")
        os.makedirs(gt_dir)
        for name, doc in (("s1", good), ("s2", bad_units), ("s3", broken)):
            with open(os.path.join(gt_dir, f"{name}.gt.json"), "w", encoding="utf-8") as fh:
                json.dump(doc, fh)
        out = os.path.join(td, "out")
        rows, skipped = L.score_corpus(gt_dir, out)
        assert len(rows) == 1
        assert skipped["units"] == 1 and skipped["error"] == 1
        rep = open(os.path.join(out, "report.md"), encoding="utf-8").read()
        assert "drift_asserts 0" in rep               # taxonomy visible in the flag line
        lines = open(os.path.join(out, "cards.jsonl"), encoding="utf-8").read().splitlines()
        assert {json.loads(x).get("skipped") for x in lines} == {None, "units", "error"}


def test_alarm_fires_only_when_blind_beats_oracle():
    b = {"symbol_recall": 0.68, "member_coverage": 0.64, "symbol_precision": 0.70}
    o = {"symbol_recall": 0.67, "member_coverage": 0.65, "symbol_precision": 0.70}
    line = L._alarm_line(b, o)
    assert "ALARM" in line and "symbol_recall" in line
    assert "member_coverage" not in line              # only the winning metric is named
    assert "alarm clear" in L._alarm_line(o, o)       # equality is never an alarm


def test_alarm_checks_precision_not_just_recall_and_coverage():
    """C0/C5/C8: doctrine says ANY symbol metric; precision was silently omitted. A blind
    arm that beats oracle ONLY on precision must still ALARM."""
    b = {"symbol_recall": 0.60, "member_coverage": 0.60, "symbol_precision": 0.80}
    o = {"symbol_recall": 0.67, "member_coverage": 0.65, "symbol_precision": 0.70}
    line = L._alarm_line(b, o)
    assert "ALARM" in line and "symbol_precision" in line
    # the clear message names every metric it checked -> can never over-claim 'all'
    clear = L._alarm_line(o, o)
    for m in L.SYMBOL_METRICS:
        assert m in clear
