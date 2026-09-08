"""
test_benchmark_reader.py -- unit tests for the backwards-benchmark scoring engine.

Every metric is pinned with a fixture that FAILS it and one that PASSES it, because a
scorer that flatters is worse than no scorer (the M3.2 judge-leniency lesson: '5/5 SHIP'
from a lenient judge was the costliest artifact in the pipeline's history). Edge cases
pin the honesty contract: no eligible data => UNWIRED, never PASS; detection misses must
NOT leak into semantic scores (they are counted separately).
"""
import benchmark_reader as B


def el(id, kind, x, y, w, d, rot=None, **kw):
    e = {"id": id, "kind": kind, "x": x, "y": y, "w": w, "d": d}
    if rot is not None:
        e["rot"] = rot
    e.update(kw)
    return e


# ---- matching ---------------------------------------------------------------------------
def test_match_greedy_best_iou_one_to_one():
    gt = [el("g1", "bed", 0, 0, 2000, 1800), el("g2", "desk", 5000, 0, 1200, 600)]
    pred = [el("p1", "bed", 50, 0, 2000, 1800),          # near-perfect overlap with g1
            el("p2", "cabinet", 5050, 0, 1200, 600)]     # overlaps g2
    pairs, missed, phantom = B.match_elements(gt, pred)
    assert len(pairs) == 2 and not missed and not phantom
    assert {(g["id"], p["id"]) for g, p, _ in pairs} == {("g1", "p1"), ("g2", "p2")}

def test_match_reports_missed_and_phantom():
    gt = [el("g1", "bed", 0, 0, 2000, 1800)]
    pred = [el("p1", "bed", 9000, 9000, 2000, 1800)]     # nowhere near
    pairs, missed, phantom = B.match_elements(gt, pred)
    assert not pairs and [m["id"] for m in missed] == ["g1"] and [p["id"] for p in phantom] == ["p1"]

def test_match_respects_iou_threshold():
    gt = [el("g1", "bed", 0, 0, 2000, 1800)]
    pred = [el("p1", "bed", 1500, 0, 2000, 1800)]        # IoU ~0.14 < 0.5
    pairs, _m, _p = B.match_elements(gt, pred)
    assert not pairs


# ---- F1 identity ------------------------------------------------------------------------
def test_identity_swap_is_caught_with_confusion_pair():
    gt = [el("g1", "desk", 0, 0, 1200, 600)]
    pred = [el("p1", "cabinet", 0, 0, 1200, 600)]        # the BF11 desk->cabinet class
    pairs, _m, _p = B.match_elements(gt, pred)
    f1 = B.score_identity(pairs)
    assert f1["accuracy"] == 0.0
    assert f1["confusion"] == {"desk->cabinet": 1}
    assert f1["per_kind"]["desk"]["recall"] == 0.0

def test_identity_synonyms_normalise_before_compare():
    gt = [el("g1", "tv_console", 0, 0, 1600, 450)]
    pred = [el("p1", "tv_cabinet", 0, 0, 1600, 450)]
    pairs, _m, _p = B.match_elements(gt, pred)
    assert B.score_identity(pairs)["accuracy"] == 1.0

def test_identity_not_polluted_by_detection_misses():
    gt = [el("g1", "bed", 0, 0, 2000, 1800), el("g2", "desk", 9000, 9000, 1200, 600)]
    pred = [el("p1", "bed", 0, 0, 2000, 1800)]           # g2 missed entirely
    pairs, missed, _p = B.match_elements(gt, pred)
    f1 = B.score_identity(pairs)
    assert f1["accuracy"] == 1.0 and len(missed) == 1    # miss counted, not blended


# ---- F2 facing --------------------------------------------------------------------------
def test_facing_buckets_exact_cardinal_flipped_wrong():
    # note the deliberate shapes: the cardinal-off (30 deg) case uses a SQUARE armchair,
    # because a 30-deg-misread ELONGATED piece inflates its axis-aligned bbox until
    # IoU < 0.5 and it exits via detection (miss+phantom), not via facing -- see
    # test_facing_nonrectangular_misread_surfaces_as_detection_miss below
    gt = [el("g1", "bed", 0, 0, 2000, 1800, rot=0),
          el("g2", "armchair", 4000, 0, 800, 800, rot=90),
          el("g3", "sofa", 8000, 0, 2200, 900, rot=0),
          el("g4", "chair", 12000, 0, 600, 600, rot=350)]
    pred = [el("p1", "bed", 0, 0, 2000, 1800, rot=3),          # exact
            el("p2", "armchair", 4000, 0, 800, 800, rot=120),  # cardinal (30 off)
            el("p3", "sofa", 8000, 0, 2200, 900, rot=180),     # flipped
            el("p4", "chair", 12000, 0, 600, 600, rot=250)]    # wrong (100 off)
    pairs, _m, _p = B.match_elements(gt, pred)
    f2 = B.score_facing(pairs)
    assert f2["buckets"] == {"exact": 1, "cardinal": 1, "flipped": 1, "wrong": 1,
                             "unreported": 0}
    assert f2["cardinal_correct"] == 0.5

def test_facing_nonrectangular_misread_surfaces_as_detection_miss():
    # documented boundary: a sofa read 30 deg off grows its axis-aligned footprint so
    # far that IoU drops below 0.5 -- the error is REPORTED (as miss+phantom), just in
    # the detection row rather than the facing row; nothing is silently absorbed
    gt = [el("g1", "sofa", 0, 0, 2200, 900, rot=90)]
    pred = [el("p1", "sofa", 0, 0, 2200, 900, rot=120)]
    pairs, missed, phantom = B.match_elements(gt, pred)
    assert not pairs and len(missed) == 1 and len(phantom) == 1

def test_facing_wraps_360():
    assert B.angle_diff(355, 5) == 10.0
    assert B.angle_diff(0, 180) == 180.0

def test_facing_skips_symmetric_kinds_and_missing_rot():
    gt = [el("g1", "side_table", 0, 0, 500, 500, rot=0),     # symmetric kind: no facing
          el("g2", "bed", 4000, 0, 2000, 1800)]              # asymmetric but NO gt rot
    pred = [el("p1", "side_table", 0, 0, 500, 500, rot=180),
            el("p2", "bed", 4000, 0, 2000, 1800, rot=180)]
    pairs, _m, _p = B.match_elements(gt, pred)
    f2 = B.score_facing(pairs)
    assert f2["n"] == 0 and f2["cardinal_correct"] is None   # nothing scoreable -> honest


# ---- F3 indoor / F5 floor ---------------------------------------------------------------
def test_indoor_binary_catches_the_lounge_vs_terrace_class():
    gt = [el("g1", "armchair", 0, 0, 800, 800, indoor=True)]     # glassed-in lounge chair
    pred = [el("p1", "armchair", 0, 0, 800, 800, indoor=False)]  # read as terrace: wrong
    pairs, _m, _p = B.match_elements(gt, pred)
    f3 = B._score_binary(pairs, "indoor")
    assert f3["accuracy"] == 0.0 and f3["wrong_ids"] == ["g1"]

def test_floor_membership_catches_grade_level_trees():
    gt = [el("g1", "tree", 0, 0, 900, 900, floor=False)]     # drawn-through grade tree
    pred = [el("p1", "tree", 0, 0, 900, 900, floor=True)]    # placed on this storey: wrong
    pairs, _m, _p = B.match_elements(gt, pred)
    f5 = B._score_binary(pairs, "floor")
    assert f5["accuracy"] == 0.0

def test_binary_pred_default_true_matches_common_generator_omission():
    # generators rarely emit indoor/floor flags; an omitted pred field means "this floor,
    # indoor" -- GT False must then score it WRONG, not skip it
    gt = [el("g1", "tree", 0, 0, 900, 900, floor=False)]
    pred = [el("p1", "tree", 0, 0, 900, 900)]
    pairs, _m, _p = B.match_elements(gt, pred)
    assert B._score_binary(pairs, "floor")["accuracy"] == 0.0


# ---- F4 openings ------------------------------------------------------------------------
def test_openings_subtype_confusion_sliding_vs_window():
    gt_o = [{"type": "sliding", "x": 0, "y": 0, "w": 1800, "d": 100},
            {"type": "door", "x": 5000, "y": 0, "w": 900, "d": 100}]
    pred_o = [{"type": "window", "x": 0, "y": 0, "w": 1800, "d": 100},
              {"type": "door", "x": 5050, "y": 0, "w": 900, "d": 100}]
    f4 = B.score_openings(gt_o, pred_o)
    assert f4["matched"] == 2
    assert f4["subtype_accuracy"] == 0.5
    assert f4["subtype_confusion"] == {"sliding->window": 1}

def test_openings_missed_detection_lowers_recall():
    gt_o = [{"type": "sliding", "x": 0, "y": 0, "w": 1800, "d": 100},
            {"type": "opening", "x": 9000, "y": 0, "w": 1200, "d": 100}]
    f4 = B.score_openings(gt_o, [{"type": "sliding", "x": 0, "y": 0, "w": 1800, "d": 100}])
    assert f4["recall"] == 0.5 and f4["precision"] == 1.0


# ---- F6 glazing flag-recall / flag-precision -------------------------------------------
def gl(x1, y1, x2, y2, kind=None):
    s = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if kind is not None:
        s["kind"] = kind
    return s


def test_glazing_flag_recall_and_precision():
    # gt: two glazed runs; pred flags one correctly + one phantom far away
    gt = [gl(0, 100, 4000, 100, "curtain_wall"), gl(0, 5000, 4000, 5000, "railing")]
    pred = [gl(0, 100, 4000, 100), gl(0, 9000, 4000, 9000)]     # 1 hit, 1 phantom
    f6 = B.score_glazing(gt, pred)
    assert f6["matched"] == 1 and f6["recall"] == 0.5 and f6["precision"] == 0.5


def test_glazing_per_kind_recall_separates_curtain_wall_and_railing():
    gt = [gl(0, 100, 4000, 100, "curtain_wall"), gl(0, 5000, 4000, 5000, "railing")]
    pred = [gl(0, 100, 4000, 100)]                              # only the curtain wall
    f6 = B.score_glazing(gt, pred)
    assert f6["per_kind_gt"]["curtain_wall"]["recall"] == 1.0
    assert f6["per_kind_gt"]["railing"]["recall"] == 0.0        # railing not hidden


def test_glazing_offset_beyond_perp_tol_does_not_match():
    gt = [gl(0, 100, 4000, 100)]
    pred = [gl(0, 500, 4000, 500)]                              # 400mm off > 250 tol
    assert B.score_glazing(gt, pred)["matched"] == 0


def test_glazing_insufficient_overlap_does_not_match():
    gt = [gl(0, 100, 4000, 100)]                                # span 0..4000
    pred = [gl(3800, 100, 5000, 100)]                           # overlaps only 200 of 1200
    assert B.score_glazing(gt, pred)["matched"] == 0


def test_glazing_blind_reader_reviews_never_unwired_passes():
    # GT carries glass but the pred emits no glazing_lines -> recall 0 -> REVIEW, NOT a
    # silent UNWIRED pass. Pins the same anti-flattery rule F2/F4 enforce.
    gt = {"elements": [], "glazing_lines": [gl(0, 100, 4000, 100, "curtain_wall")]}
    pred = {"elements": []}                                     # glazing-blind reader
    f6 = B.score_pair(gt, pred)["F6_glazing"]
    assert f6["recall"] == 0.0 and f6["verdict"] == "REVIEW"


def test_glazing_unwired_when_neither_side_has_lines():
    card = B.score_pair({"elements": []}, {"elements": []})
    assert card["F6_glazing"]["verdict"] == "UNWIRED"


def test_glazing_perpendicular_diagonals_do_not_match():
    # two 45deg diagonals crossing only at their midpoint bucket to the same axis+offset+
    # span; without the direction gate they'd false-match at recall/precision 1.0
    gt = [gl(0, 0, 1000, 1000, "curtain_wall")]
    pred = [gl(0, 1000, 1000, 0)]                               # perpendicular
    assert B.score_glazing(gt, pred)["matched"] == 0


def test_glazing_parallel_diagonals_still_match():
    gt = [gl(0, 0, 1000, 1000, "curtain_wall")]
    pred = [gl(0, 0, 1000, 1000)]                               # same direction
    assert B.score_glazing(gt, pred)["matched"] == 1


def test_glazing_perp_tol_independent_of_open_tol_on_mm_sheet():
    # tightening the OPENING tolerance on an mm sheet must not move the GLAZING perp tol
    gt = {"meta": {"units": "mm"}, "elements": [],
          "glazing_lines": [gl(0, 100, 4000, 100, "curtain_wall")]}
    pred = {"meta": {"units": "mm"}, "elements": [],
            "glazing_lines": [gl(0, 300, 4000, 300)]}          # 200mm off, within 250 default
    assert B.score_pair(gt, pred)["F6_glazing"]["matched"] == 1
    assert B.score_pair(gt, pred, open_tol=100)["F6_glazing"]["matched"] == 1  # unchanged


def test_glazing_malformed_line_reported_not_fatal():
    gt = {"elements": [], "glazing_lines": [gl(0, 100, 4000, 100), {"x1": 0, "y1": 0}]}
    pred = {"elements": [], "glazing_lines": [gl(0, 100, 4000, 100)]}
    card = B.score_pair(gt, pred)                               # must not raise
    assert card["malformed"]["gt_glazing"] == 1
    assert card["F6_glazing"]["matched"] == 1


# ---- sanitation + robustness (one malformed element must not kill a corpus run) ---------
def test_rot_null_string_and_cardinal_survive_scoring():
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 1800, rot=0)]}
    for bad_rot in (None, "90", "N", "garbage"):
        pred = {"elements": [{"id": "p1", "kind": "bed", "x": 0, "y": 0,
                              "w": 2000, "d": 1800, "rot": bad_rot}]}
        card = B.score_pair(gt, pred)                        # must not raise
        assert card["detection"]["matched"] == 1, bad_rot
    # cardinal letters map via the build_floor convention: N = 180
    gt2 = {"elements": [el("g1", "bed", 0, 0, 2000, 1800, rot=180)]}
    card = B.score_pair(gt2, {"elements": [{"id": "p1", "kind": "bed", "x": 0, "y": 0,
                                            "w": 2000, "d": 1800, "rot": "N"}]})
    assert card["F2_facing"]["buckets"]["exact"] == 1

def test_malformed_elements_are_reported_not_fatal():
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 1800),
                       {"id": "g2", "kind": "desk", "x": None, "y": 0, "w": 1, "d": 1}]}
    pred = {"elements": [el("p1", "bed", 0, 0, 2000, 1800)]}
    card = B.score_pair(gt, pred)
    assert card["malformed"]["gt_elements"] == ["g2"]
    assert card["detection"]["matched"] == 1

def test_openings_missing_xy_or_null_wd_are_survivable():
    # null w/d degrade to a point opening at (x, y) -- put it at the pred's CENTRE
    gt = {"elements": [], "openings": [{"type": "door", "x": 450, "y": 50, "w": None, "d": None},
                                       {"type": "door"}]}                 # no x/y: malformed
    pred = {"elements": [], "openings": [{"type": "door", "x": 0, "y": 0, "w": 900, "d": 100}]}
    card = B.score_pair(gt, pred)                            # must not raise
    assert card["malformed"]["gt_openings"] == 1
    assert card["F4_openings"]["matched"] == 1

def test_facing_blind_reader_cannot_pass_f2():
    # GT rot=0 everywhere (the most common value); pred never emits rot -> every pair
    # buckets 'unreported' and the metric REVIEWs. Defaulting missing rot to 0 here
    # would score 1.0 -- the flattering-scorer hole this test pins shut.
    gt = {"elements": [el(f"g{i}", "bed", i * 5000, 0, 2000, 1800, rot=0) for i in range(3)]}
    pred = {"elements": [el(f"p{i}", "bed", i * 5000, 0, 2000, 1800) for i in range(3)]}
    card = B.score_pair(gt, pred)
    f2 = card["F2_facing"]
    assert f2["buckets"]["unreported"] == 3 and f2["cardinal_correct"] == 0.0
    assert f2["verdict"] == "REVIEW"

def test_f2_cheat_mutant_cannot_copy_gt_rot():
    # pred rot present and WRONG must stay wrong even when GT rot is the common 0
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 1800, rot=0)]}
    pred = {"elements": [el("p1", "bed", 0, 0, 2000, 1800, rot=180)]}
    assert B.score_pair(gt, pred)["F2_facing"]["buckets"]["flipped"] == 1

def test_binary_gt_null_is_ineligible_pred_null_is_default_true():
    gt = [el("g1", "tree", 0, 0, 900, 900, floor=None),      # annotator couldn't tell
          el("g2", "tree", 4000, 0, 900, 900, floor=False)]
    pred = [el("p1", "tree", 0, 0, 900, 900, floor=False),
            el("p2", "tree", 4000, 0, 900, 900, floor=None)] # null = didn't say = True
    pairs, _m, _p = B.match_elements(gt, pred)
    f5 = B._score_binary(pairs, "floor")
    assert f5["n"] == 1 and f5["accuracy"] == 0.0            # only g2 eligible; p2 wrong

def test_f4_total_detection_failure_is_review_never_pass():
    gt = {"elements": [], "openings": [{"type": "door", "x": 0, "y": 0, "w": 900, "d": 100}]}
    pred = {"elements": [], "openings": [{"type": "door", "x": 90000, "y": 0, "w": 900, "d": 100}]}
    f4 = B.score_pair(gt, pred)["F4_openings"]
    assert f4["matched"] == 0 and f4["recall"] == 0.0 and f4["verdict"] == "REVIEW"

def test_openings_beyond_tolerance_do_not_match():
    gt_o = [{"type": "door", "x": 0, "y": 0, "w": 900, "d": 100}]
    pred_o = [{"type": "door", "x": 5000, "y": 0, "w": 900, "d": 100}]   # 5 m away
    f4 = B.score_openings(gt_o, pred_o)
    assert f4["matched"] == 0

def test_matching_prefers_same_kind_on_iou_ties():
    # two co-located same-footprint elements: kind-blind tie-breaking can cross-pair
    # them and manufacture two identity confusions where zero errors exist
    gt = [el("g1", "bed", 0, 0, 2000, 2000), el("g2", "sofa", 0, 0, 2000, 2000)]
    pred = [el("p1", "sofa", 0, 0, 2000, 2000), el("p2", "bed", 0, 0, 2000, 2000)]
    pairs, _m, _p = B.match_elements(gt, pred)
    f1 = B.score_identity(pairs)
    assert f1["accuracy"] == 1.0 and f1["confusion"] == {}

def test_pass_bar_position_is_090():
    # 9/10 correct -> PASS at the 0.9 bar; 8/10 -> REVIEW. Pins the bar's position,
    # not just its extremes.
    gt = {"elements": [el(f"g{i}", "bed", i * 5000, 0, 2000, 1800, indoor=True) for i in range(10)]}
    def pred_with(k_wrong):
        return {"elements": [el(f"p{i}", "bed", i * 5000, 0, 2000, 1800,
                                indoor=(i >= k_wrong)) for i in range(10)]}
    assert B.score_pair(gt, pred_with(1))["F3_indoor"]["verdict"] == "PASS"
    assert B.score_pair(gt, pred_with(2))["F3_indoor"]["verdict"] == "REVIEW"

def test_low_n_flag_marks_provisional_verdicts():
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 1800, indoor=True)]}
    pred = {"elements": [el("p1", "bed", 0, 0, 2000, 1800, indoor=True)]}
    card = B.score_pair(gt, pred)
    assert card["F3_indoor"]["verdict"] == "PASS" and card["F3_indoor"]["low_n"] is True
    assert "(low n" in B.render_report(card)

def test_f2_bucket_band_edges():
    assert B.angle_diff(0, 40) == 40.0                       # cardinal band edge food
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 2000, rot=0),
                       el("g2", "bed", 9000, 0, 2000, 2000, rot=0),
                       el("g3", "bed", 18000, 0, 2000, 2000, rot=0)]}
    pred = {"elements": [el("p1", "bed", 0, 0, 2000, 2000, rot=40),      # cardinal
                         el("p2", "bed", 9000, 0, 2000, 2000, rot=50),   # wrong (>45, not flip)
                         el("p3", "bed", 18000, 0, 2000, 2000, rot=140)]}  # flipped (|140-180|=40)
    f2 = B.score_pair(gt, pred)["F2_facing"]
    assert f2["buckets"]["cardinal"] == 1 and f2["buckets"]["wrong"] == 1 \
        and f2["buckets"]["flipped"] == 1

def test_kind_synonyms_and_facing_kinds_pinned():
    for raw, canon in B.KIND_SYNONYMS.items():
        assert B.norm_kind(raw) == canon
    assert B.FACING_KINDS == {"bed", "sofa", "loveseat", "armchair", "chair", "bench",
                              "tv_panel", "tv_console", "desk", "toilet", "wardrobe",
                              "cabinet"}                     # de-scoping F2 must be loud


# ---- scorecard assembly -----------------------------------------------------------------
def test_score_pair_unwired_when_no_eligible_data():
    card = B.score_pair({"elements": []}, {"elements": []})
    for k in ("detection", "F1_identity", "F2_facing", "F3_indoor", "F4_openings",
              "F5_floor", "F6_glazing"):
        assert card[k]["verdict"] == "UNWIRED", k          # empty is UNWIRED, never PASS

def test_score_pair_end_to_end_verdicts():
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 1800, rot=0, indoor=True, floor=True)],
          "openings": [{"type": "sliding", "x": 0, "y": 2000, "w": 1800, "d": 100}]}
    pred_good = {"elements": [el("p1", "bed", 0, 0, 2000, 1800, rot=0, indoor=True, floor=True)],
                 "openings": [{"type": "sliding", "x": 0, "y": 2000, "w": 1800, "d": 100}]}
    card = B.score_pair(gt, pred_good)
    assert all(card[k]["verdict"] == "PASS"
               for k in ("detection", "F1_identity", "F2_facing", "F3_indoor",
                         "F4_openings", "F5_floor"))
    pred_bad = {"elements": [el("p1", "sofa", 0, 0, 2000, 1800, rot=180, indoor=False)],
                "openings": [{"type": "window", "x": 0, "y": 2000, "w": 1800, "d": 100}]}
    card = B.score_pair(gt, pred_bad)
    assert card["F1_identity"]["verdict"] == "REVIEW"      # bed read as sofa
    assert card["F2_facing"]["verdict"] == "REVIEW"        # flipped
    assert card["F3_indoor"]["verdict"] == "REVIEW"        # indoor read as outdoor
    assert card["F4_openings"]["verdict"] == "REVIEW"      # sliding->window

def test_aggregate_recomputes_from_counts():
    gt = {"elements": [el("g1", "bed", 0, 0, 2000, 1800, rot=0)]}
    good = {"elements": [el("p1", "bed", 0, 0, 2000, 1800, rot=0)]}
    bad = {"elements": [el("p1", "desk", 0, 0, 2000, 1800, rot=180)]}
    cards = [B.score_pair(gt, good), B.score_pair(gt, bad)]
    agg = B.aggregate(cards)
    assert agg["pairs"] == 2
    assert agg["F1_identity"] == {"n": 2, "accuracy": 0.5}
    assert agg["F2_facing"]["cardinal_correct"] == 0.5

def test_aggregate_recomputes_f6_from_counts():
    gt = {"elements": [], "glazing_lines": [gl(0, 100, 4000, 100, "curtain_wall"),
                                            gl(0, 5000, 4000, 5000, "railing")]}
    hit1 = {"elements": [], "glazing_lines": [gl(0, 100, 4000, 100)]}     # 1/2 recall
    hit2 = {"elements": [], "glazing_lines": [gl(0, 100, 4000, 100),
                                              gl(0, 5000, 4000, 5000)]}   # 2/2 recall
    agg = B.aggregate([B.score_pair(gt, hit1), B.score_pair(gt, hit2)])
    assert agg["F6_glazing"]["n_gt"] == 4 and agg["F6_glazing"]["matched"] == 3
    assert agg["F6_glazing"]["recall"] == 0.75
    assert agg["F6_glazing"]["per_kind_gt"]["railing"]["recall"] == 0.5


def test_render_report_mentions_unwired_honesty():
    card = B.score_pair({"elements": []}, {"elements": []})
    txt = B.render_report(card)
    assert "UNWIRED" in txt and "not a pass" in txt


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} benchmark_reader tests passed")
