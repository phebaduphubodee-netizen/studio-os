"""Tests for wall_aware_lane -- the cross-wall fusion split wrapper.

The load-bearing pins:
  - ZERO-WALLS EQUIVALENCE: with wall_lines=[] the lane's elements are GEOMETRY-IDENTICAL
    to the unedited svg_plan_reader's (x/y/w/d/curve/fill + order; ids differ by design,
    w### vs c###) -- the mirrored morphology has not drifted (this is the test that
    screams if plan_cluster/read_sheet change under the wrapper);
  - the barrier splits a fused cross-wall pair (the lane's whole reason to exist) but
    does NOT split the same pair when no wall crosses it -- the delta is walls, not noise;
  - merged_blob recovery: a whole-room fusion the reader DROPS (>3.6m both axes) comes
    back as per-side scoreable elements;
  - split-through is documented behavior: ink genuinely drawn across a wall is cut;
  - a scene without wall_lines scores delta ZERO by construction;
  - the oracle tier is disclosed on the pred meta AND in the report.
"""
import json
import os
import tempfile

import svg_plan_reader as R
import synth_plan_2d as S
import wall_aware_lane as W


def _doc(elements, walls=None):
    return {"meta": {"units": "mm", "n_elements": len(elements)},
            "elements": [dict(e) for e in elements], "openings": [],
            "glazing_lines": [], "wall_lines": list(walls or [])}


def _el(id_, x, y, w, d, kind=None, rot=None, indoor=None):
    e = {"id": id_, "x": float(x), "y": float(y), "w": float(w), "d": float(d)}
    if kind is not None:
        e["kind"] = kind
    if rot is not None:
        e["rot"] = float(rot)
    if indoor is not None:
        e["indoor"] = indoor
    return e


def _rect_segs(x, y, w, d):
    """The 4 ring segments read_ink emits for a <rect> footprint."""
    ring = [(x, y), (x + w, y), (x + w, y + d), (x, y + d), (x, y)]
    return [[a, b] for a, b in zip(ring, ring[1:])]


def _wall(x1, y1, x2, y2):
    return {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


def _geom(elements):
    return [(e["x"], e["y"], e["w"], e["d"], e["curve"], e["fill"]) for e in elements]


# ---- zero-walls equivalence (the drift alarm) ----------------------------------------------
def test_zero_walls_is_reader_equivalent():
    """With no walls, the wrapper must reproduce the UNEDITED reader's elements exactly
    (geometry, curve, fill, order) through the real SVG round-trip -- zone padding, res,
    close radius and screen all mirrored. If this breaks, the mirror has drifted."""
    gt = _doc([_el("a", 0, 0, 1200, 700), _el("b", 2000, 1500, 900, 400),
               _el("c", -1500, 300, 600, 600)])
    svg = S.synth_svg(gt)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(svg)
        pred = R.read_sheet(p, 1.0)
        ink = R.read_ink(p)
    els, stats = W.wall_barrier_elements(ink["segs"], ink["curve_segs"], [])
    assert _geom(els) == _geom(pred["elements"])
    assert stats["n_wall_segs"] == 0 and stats["wall_px"] == 0


def test_empty_ink_is_empty():
    els, stats = W.wall_barrier_elements([], [], [_wall(0, 0, 0, 1000)])
    assert els == [] and stats["kept"] == 0


# ---- the split itself ----------------------------------------------------------------------
def test_wall_splits_fused_cross_wall_pair():
    """Two 800x600 rects, 60mm edge gap (inside the reader's ~90mm fusion distance), a
    vertical wall between them: one cluster without the wall, two with it."""
    segs = _rect_segs(0, 0, 800, 600) + _rect_segs(860, 0, 800, 600)
    before, _ = W.wall_barrier_elements(segs, [], [])
    assert len(before) == 1, f"calibration drift: expected fusion, got {len(before)}"
    after, stats = W.wall_barrier_elements(segs, [], [_wall(830, -200, 830, 800)])
    assert len(after) == 2, f"wall failed to split: {after}"
    assert stats["wall_px"] > 0
    xs = sorted(e["x"] for e in after)
    assert xs[0] < 100 and xs[1] > 700          # one part per side, near the true corners


def test_no_wall_no_split_and_far_wall_no_split():
    segs = _rect_segs(0, 0, 800, 600) + _rect_segs(860, 0, 800, 600)
    after_far, _ = W.wall_barrier_elements(segs, [], [_wall(5000, -200, 5000, 800)])
    assert len(after_far) == 1                  # a wall elsewhere must change nothing


def test_merged_blob_recovery():
    """A cross-wall fusion >3.6m on BOTH axes is DROPPED whole by the reader's screen
    (every GT element inside = a miss). The barrier cuts it at the wall; the per-side
    parts pass the screen and come back as elements."""
    segs = _rect_segs(0, 0, 3700, 2000) + _rect_segs(0, 2060, 3700, 2000)
    before, bstats = W.wall_barrier_elements(segs, [], [])
    assert before == [] and bstats["dropped_blob"] == 1
    after, astats = W.wall_barrier_elements(segs, [], [_wall(-200, 2030, 3900, 2030)])
    assert len(after) == 2 and astats["dropped_blob"] == 0


def test_real_ink_across_wall_is_never_cut():
    """BRIDGE-ONLY barrier: an element genuinely INKED across a wall (curtain, window
    band, wardrobe bbox overlapping the wall) stays ONE piece -- only closing-added
    bridge pixels are severed. The first probe cut real ink and shredded wall-hugging
    elements below the size screen (scenes lost up to half their matches) -- pinned.
    Such kept crossers are COUNTED as residual_cross_region, never asserted away."""
    segs = _rect_segs(0, 0, 2000, 900)
    after, stats = W.wall_barrier_elements(segs, [], [_wall(1000, -200, 1000, 1100)])
    assert len(after) == 1
    assert stats["residual_cross_region"] == 1
    assert stats["n_regions"] >= 2


def test_ink_overlapping_wall_does_not_reopen_the_bridge():
    """Adversarial-review regression (2026-07-10, reproduced): with the cut applied
    AFTER the closing, a stub of real ink poking a few mm past the wall centreline
    punched a hole in the ~3px band and reconnected the rooms through the surviving
    bridge mass beyond it. Severing MID-closing (dilate -> cut -> erode) lets erosion
    eat the stranded far-side mass back: the split must hold at any overlap depth."""
    segs = _rect_segs(0, 0, 800, 600) + _rect_segs(860, 0, 800, 600)
    stub = [[(800.0, 300.0), (835.0, 300.0)]]        # ends 5mm past the wall at x=830
    after, stats = W.wall_barrier_elements(segs + stub, [],
                                           [_wall(830, -200, 830, 800)])
    assert len(after) == 2, f"stub reopened the cross-wall bridge: {after}"
    assert stats["residual_cross_region"] == 0


def test_partial_span_wall_route_around_is_documented():
    """A wall trace that does NOT span the bridge leaves the fusion intact: the bridge
    routes around the trace end (door gaps, junction-broken traces). Pinned as the
    DOCUMENTED residual -- the report discloses it instead of claiming zero cross-wall
    fusion in the residual."""
    segs = _rect_segs(0, 0, 800, 600) + _rect_segs(860, 0, 800, 600)
    partial, pstats = W.wall_barrier_elements(segs, [], [_wall(830, 200, 830, 400)])
    assert len(partial) == 1 and pstats["wall_px"] > 0
    door_gap, _ = W.wall_barrier_elements(segs, [], [_wall(830, -200, 830, 150),
                                                     _wall(830, 450, 830, 800)])
    assert len(door_gap) == 1


def test_barrier_elements_never_carry_rot():
    """The blind-baseline guarantee is structural: no element from the barrier morphology
    may carry rot (rot only ever attaches later, from read ink evidence). The zero-walls
    equivalence pin projects rot away, so this must be pinned separately."""
    segs = _rect_segs(0, 0, 800, 600) + _rect_segs(860, 0, 800, 600)
    after, _ = W.wall_barrier_elements(segs, [], [_wall(830, -200, 830, 800)])
    assert after and all("rot" not in e for e in after)


def test_thin_wall_hugging_element_survives_the_barrier():
    """An element lying ON the wall line (a 200mm-deep window/curtain band) must survive
    intact: cutting real ink would drop it under the 150mm thin-screen."""
    segs = _rect_segs(0, -100, 1800, 200)               # band centred on the wall line
    after, _ = W.wall_barrier_elements(segs, [], [_wall(-200, 0, 2000, 0)])
    assert len(after) == 1


def test_diagonal_wall_rasterizes_without_crash():
    """A diagonal wall INSIDE the ink zone rasterizes as a barrier (no axis-aligned
    assumption) without touching an element it does not cross. A wall OUTSIDE the ink
    zone contributes nothing -- the zone is the reader's own raster window."""
    segs = _rect_segs(0, 0, 800, 600)
    after, stats = W.wall_barrier_elements(segs, [], [_wall(830, -90, 890, 690)])
    assert len(after) == 1 and stats["wall_px"] > 0
    outside, ostats = W.wall_barrier_elements(segs, [], [_wall(-500, 2000, 2500, 2600)])
    assert len(outside) == 1 and ostats["wall_px"] == 0


def test_degenerate_wall_seg_is_ignored():
    segs = _rect_segs(0, 0, 800, 600)
    after, stats = W.wall_barrier_elements(segs, [], [_wall(400, 300, 400, 300)])
    assert len(after) == 1 and stats["wall_px"] == 0


# ---- scene-level before/after ---------------------------------------------------------------
def _two_sofas_across_wall():
    """Two sofas back-to-back across a wall, 60mm apart: the fused cluster matches NEITHER
    GT footprint at IoU>=0.5, so before-the-wall the pair contributes nothing to F2."""
    a = _el("s1", 0, 0, 2000, 900, kind="sofa", rot=0, indoor=True)
    b = _el("s2", 0, 960, 2000, 900, kind="sofa", rot=180, indoor=True)
    return _doc([a, b], walls=[_wall(-100, 930, 2100, 930)])


def test_scene_cross_wall_f2_recovered():
    gt = _two_sofas_across_wall()
    with tempfile.TemporaryDirectory() as td:
        row = W.score_scene(gt, td, oracle=False)
    assert row["card_before"]["detection"]["matched"] == 0      # fusion killed the match
    assert row["card_after"]["detection"]["matched"] == 2       # barrier restored it
    assert row["f2_nobed_before"]["n"] == 0
    assert row["f2_nobed_after"]["n"] == 2
    assert row["f2_nobed_after"]["buckets"]["exact"] == 2       # strips read per side
    # F3 rides the same matched set: 0 eligible pairs before, 2 after
    assert row["card_before"]["F3_indoor"]["n"] == 0
    assert row["card_after"]["F3_indoor"]["n"] == 2
    # MEASURED blind baseline: un-enriched preds never carry rot on either side
    for key in ("f2_blind_before", "f2_blind_after"):
        bl = row[key]
        assert bl["buckets"]["exact"] == 0 and bl["hits"] == 0
        assert bl["n"] == bl["buckets"]["unreported"]
    # transition decomposition: nothing matched before, both pairs are NEW exacts
    t = row["f2_transitions"]
    assert t["before_n"] == 0 and t["changed"] == {} and t["new"] == {"exact": 2}


def test_scene_without_walls_scores_delta_zero():
    gt = _doc([_el("s1", 0, 0, 2000, 900, kind="sofa", rot=0),
               _el("t1", 3000, 0, 1200, 700)])
    with tempfile.TemporaryDirectory() as td:
        row = W.score_scene(gt, td, oracle=False)
    db, da = row["card_before"]["detection"], row["card_after"]["detection"]
    assert (db["n_pred"], db["matched"]) == (da["n_pred"], da["matched"])
    assert row["f2_nobed_before"]["buckets"] == row["f2_nobed_after"]["buckets"]
    assert row["wall_aware"]["n_wall_segs"] == 0


# ---- disclosure ------------------------------------------------------------------------------
def test_oracle_tier_disclosed_on_pred_and_report():
    gt = _two_sofas_across_wall()
    with tempfile.TemporaryDirectory() as td:
        svg, _ = W.F2L.oriented_svg(gt)
        p = os.path.join(td, "t.svg")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(svg)
        pred_b = R.read_sheet(p, 1.0)
        ink = R.read_ink(p)
        pred_a, _ = W.wall_aware_pred(pred_b, ink["segs"], ink["curve_segs"],
                                      gt["wall_lines"])
        assert pred_a["meta"]["wall_aware"]["tier"] == "ORACLE-WALLS"
        assert "wall_aware" not in pred_b["meta"]               # the before-pred stays blind
        row = W.score_scene(gt, td, oracle=True)
    report = W.render_report([{"scene": "t", **row}],
                             {"error": 0, "units": 0, "no_walls": 0}, 1, 1.0)
    assert "ORACLE-WALLS" in report
    assert "NEVER the blind headline" in report
    # rows are json-serializable (the corpus run streams them)
    json.dumps(row)
