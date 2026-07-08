"""
test_synth_plan_2d.py -- unit tests for the 2D-plan synthesizer that lets OUR reader be RUN
on a Structured3D-derived plan and scored for REAL (F3 pred!=gt, not the symmetric selftest).

Pinned behaviors:
  - ROUND-TRIP: a synthesized furniture rectangle is recovered by svg_plan_reader's own
    morphology and MATCHES the gt element (so F3 scores on a real matched pair, not a meta
    count). This proves the whole path synth -> reader -> benchmark_reader end-to-end.
  - ANNOTATION-BLIND: the indoor/outdoor label is NEVER drawn -- two gt docs that differ ONLY
    in `indoor` synthesize to a BYTE-IDENTICAL SVG. F3 therefore measures geometry-only
    inference, never a leaked answer key (the same honesty core as svg_plan_reader.read_ink).
  - ALWAYS-INDOOR BASELINE: svg_plan_reader emits no indoor key, so scoring the synthesized
    plan yields the honest baseline -- indoor pieces right, OUTDOOR pieces wrong, and the
    wrong_ids are exactly the outdoor (balcony/garden) furniture the reader would misclassify.

    python3 -m pytest test_synth_plan_2d.py -q
"""
import os
import tempfile

import benchmark_reader as B
import svg_plan_reader as R
import synth_plan_2d as S


def _gt(elements, walls=None, glaz=None):
    return {"meta": {"units": "mm", "scene": "t"}, "elements": elements,
            "openings": [], "glazing_lines": glaz or [], "wall_lines": walls or []}


def _read(svg_str):
    """Write the SVG to a temp file and run OUR reader on it at mm scale (1.0)."""
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "s.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(svg_str)
        return R.read_sheet(p, 1.0)


# ---- tracer: synth -> reader -> score, F3 on a real matched pair -------------------------
def test_roundtrip_single_box_is_recovered_and_scored():
    gt = _gt([{"id": "o0", "x": 1000.0, "y": 2000.0, "w": 600.0, "d": 400.0, "indoor": True}])
    pred = _read(S.synth_svg(gt))
    card = B.score_pair(gt, pred)
    assert card["detection"]["matched"] == 1        # the box is recovered by the reader
    assert card["F3_indoor"]["n"] == 1              # F3 scores on the matched pair (real, not meta)


# ---- anti-leakage: indoor is never drawn -------------------------------------------------
def test_synth_is_annotation_blind_to_indoor():
    el = {"id": "o0", "x": 0.0, "y": 0.0, "w": 600.0, "d": 400.0}
    svg_in = S.synth_svg(_gt([{**el, "indoor": True}]))
    svg_out = S.synth_svg(_gt([{**el, "indoor": False}]))
    assert svg_in == svg_out                        # the label never reaches the drawing
    assert "indoor" not in svg_in and "<text" not in svg_in
    assert "balcony" not in svg_in and "garden" not in svg_in


# ---- the honest always-indoor F3 baseline ------------------------------------------------
def test_always_indoor_baseline_flags_outdoor_pieces():
    gt = _gt([{"id": "o0", "x": 0.0, "y": 0.0, "w": 600.0, "d": 400.0, "indoor": True},
              {"id": "o1", "x": 3000.0, "y": 0.0, "w": 600.0, "d": 400.0, "indoor": False}])
    pred = _read(S.synth_svg(gt))
    card = B.score_pair(gt, pred)
    f3 = card["F3_indoor"]
    assert f3["n"] == 2 and f3["hits"] == 1         # indoor right, outdoor wrong (reader is silent=indoor)
    assert "o1" in f3["wrong_ids"]                  # the outdoor piece is the one the reader misses


# ---- KNOWN LIMIT (pinned, not hidden): furniture within CLOSE_MM merges out of the F3 set ---
def test_furniture_within_close_mm_merges_and_drops_from_f3():
    """DETECTION-LIMITED SAMPLE, documented in the module honesty notes. Two furniture pieces
    drawn closer than the reader's CLOSE_MM (40mm) merge into ONE cluster whose AABB matches
    NEITHER gt box -> both leave the matched set, so F3 does not score them (n drops). This is
    the real-data failure mode the adversarial review flagged: the F3 baseline is measured on
    the DETECTED subset, and clustered furniture (bed+flush nightstand, stacked cushions) is
    under-sampled. Pinned so the limit is explicit; the control below proves separation recovers
    both."""
    # 20mm gap (< CLOSE_MM): the two boxes merge -> F3 loses both
    merged = _gt([{"id": "o0", "x": 0.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": True},
                  {"id": "o1", "x": 520.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": False}])
    card_m = B.score_pair(merged, _read(S.synth_svg(merged)))
    assert card_m["F3_indoor"]["n"] < 2             # at least one (here both) dropped by the merge
    # control: 3000mm apart -> both recovered, both scored
    apart = _gt([{"id": "o0", "x": 0.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": True},
                 {"id": "o1", "x": 3000.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": False}])
    card_a = B.score_pair(apart, _read(S.synth_svg(apart)))
    assert card_a["F3_indoor"]["n"] == 2
