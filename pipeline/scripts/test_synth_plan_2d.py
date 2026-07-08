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


# ==== v1.1 PLAN-SYMBOL lane (the F3 slice expander) =======================================
# ---- tracer: the fused furniture that DROPS from per-object F3 is RECOVERED as one symbol --
def test_realistic_recovers_fused_furniture_the_per_object_lane_loses():
    """The exact failure the per-object lane pins above (two pieces within the reader's fuse
    distance both leave F3) is RECOVERED by --realistic: they group into ONE plan symbol whose
    union footprint the reader's fused cluster matches -> F3 scores it. This is the whole point
    of the slice expander, proven end-to-end (group -> draw members -> reader fuses -> score)."""
    # 20mm gap, BOTH indoor (one room) -> per-object F3 loses both; realistic recovers one symbol
    gt = _gt([{"id": "o0", "x": 0.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": True},
              {"id": "o1", "x": 520.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": True}])
    per_card, _p, _s = S.score_gt(gt, realistic=False)
    assert per_card["F3_indoor"]["n"] < 2            # per-object: fused pieces leave F3
    real_card, _pr, stat = S.score_gt(gt, realistic=True)
    assert stat["n_symbols"] == 1 and stat["multi"] == 1
    assert real_card["F3_indoor"]["n"] == 1          # realistic: the union symbol IS scored
    assert real_card["F3_indoor"]["hits"] == 1       # both indoor -> reader silent=indoor correct


# ---- anti-leakage: the realistic draw is still blind to indoor ---------------------------
def test_realistic_draw_is_annotation_blind_to_indoor():
    els = [{"id": "o0", "x": 0.0, "y": 0.0, "w": 600.0, "d": 400.0},
           {"id": "o1", "x": 620.0, "y": 0.0, "w": 600.0, "d": 400.0}]
    in_t = S.synth_svg(S._members_doc(_gt([{**e, "indoor": True} for e in els])))
    in_f = S.synth_svg(S._members_doc(_gt([{**e, "indoor": False} for e in els])))
    assert in_t == in_f                              # consensus indoor never reaches the drawing
    assert "indoor" not in in_t and "<text" not in in_t


# ---- grouping: decor filtered, co-located furniture fused, union + consensus indoor -------
def test_group_symbols_filters_decor_and_fuses_colocated():
    doc = _gt([{"id": "cup", "x": 100.0, "y": 100.0, "w": 90.0, "d": 90.0, "indoor": True},  # <150 decor
               {"id": "bed", "x": 0.0, "y": 0.0, "w": 1800.0, "d": 1500.0, "indoor": True},
               {"id": "ns", "x": 1810.0, "y": 0.0, "w": 400.0, "d": 400.0, "indoor": True}])  # 10mm gap
    sym_doc, stat = S.group_symbols(doc)
    assert stat["n_decor_filtered"] == 1             # the cup is not drawn
    assert stat["n_symbols"] == 1 and stat["multi"] == 1
    s = sym_doc["elements"][0]
    assert s["n_members"] == 2                       # bed + nightstand, cup excluded
    assert (s["x"], s["y"]) == (0.0, 0.0) and (s["w"], s["d"]) == (2210.0, 1500.0)  # union AABB
    assert s["indoor"] is True                       # room consensus


def test_group_symbols_mixed_indoor_gets_no_label_and_is_counted():
    # two fused pieces disagree on indoor (a chair straddling a balcony threshold): no forced side
    doc = _gt([{"id": "a", "x": 0.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": True},
               {"id": "b", "x": 520.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": False}])
    sym_doc, stat = S.group_symbols(doc)
    assert stat["n_symbols"] == 1 and stat["mixed_indoor"] == 1
    assert "indoor" not in sym_doc["elements"][0]    # counted, never guessed to a side


def test_group_symbols_separates_beyond_fuse_gap():
    # 3000mm apart -> two distinct symbols, each keeps its own indoor
    doc = _gt([{"id": "a", "x": 0.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": True},
               {"id": "b", "x": 3000.0, "y": 0.0, "w": 500.0, "d": 500.0, "indoor": False}])
    sym_doc, stat = S.group_symbols(doc)
    assert stat["n_symbols"] == 2 and stat["singleton"] == 2
    assert stat["indoor_true"] == 1 and stat["indoor_false"] == 1


# ---- honesty: cross-room chaining loss is measured at MEMBER level, not hidden as 1 symbol ----
def test_group_symbols_counts_member_level_oversize_loss():
    """An L-chain of 3 furniture pieces fuses into ONE union >3600mm on both axes -> a dense
    region the reader will drop. The honesty fix requires the MEMBER-level loss (3, not '1
    symbol') and its indoor/outdoor split to be counted (adversarial review 2026-07-08)."""
    doc = _gt([{"id": "a", "x": 0.0,    "y": 0.0,    "w": 2000.0, "d": 2000.0, "indoor": True},
               {"id": "b", "x": 2050.0, "y": 0.0,    "w": 2000.0, "d": 2000.0, "indoor": True},   # 50mm gap
               {"id": "c", "x": 0.0,    "y": 2050.0, "w": 2000.0, "d": 2000.0, "indoor": True}])   # 50mm gap
    sym_doc, stat = S.group_symbols(doc)
    assert stat["n_symbols"] == 1 and stat["union_oversize"] == 1        # union 4050x4050 both >3600
    assert stat["members_in_oversize"] == 3                             # the honest magnitude, not "1"
    assert stat["members_oversize_indoor_true"] == 3
    assert stat["largest_symbol_members"] == 3


def test_group_symbols_distinct_excluded_is_not_additive():
    """A symbol that is BOTH union-oversize AND mixed-indoor must be counted ONCE in
    excluded_distinct, so the report cannot double-count (union_oversize + mixed = 2 but the
    distinct exclusion is 1)."""
    doc = _gt([{"id": "a", "x": 0.0,    "y": 0.0,    "w": 2000.0, "d": 2000.0, "indoor": True},
               {"id": "b", "x": 2050.0, "y": 0.0,    "w": 2000.0, "d": 2000.0, "indoor": False},  # mixed vote
               {"id": "c", "x": 0.0,    "y": 2050.0, "w": 2000.0, "d": 2000.0, "indoor": True}])
    sym_doc, stat = S.group_symbols(doc)
    assert stat["union_oversize"] == 1 and stat["mixed_indoor"] == 1
    assert stat["excluded_distinct"] == 1                              # counted once, not 2
    assert stat["members_oversize_indoor_true"] == 2 and stat["members_oversize_indoor_false"] == 1
