"""Tests for f2_facing_lane -- the first pred!=gt cardinal_correct (F2) lane.

The load-bearing pins:
  - strips land on the BACK edge (opposite of front) in facing_reader's inner band, for all
    four cardinals, INCLUDING a rot-90/270 kinded element whose local rect must be baked
    into the true AABB first (the double-rotation lesson);
  - the loop is not a self-confirming mirror: a 180-corrupted DRAWING scores 'flipped'
    against the true GT, and a strip-less drawing scores 'unreported' -- never a default;
  - blindness ledger: indoor never changes a byte of the SVG; zero strips == byte-identical
    to the blind synthesizer;
  - the wall-prior lane points AWAY from the backing wall on all four sides and stays
    honestly silent off-wall (it is an oracle-tier PRIOR, but its sign must be right).
"""
import copy
import json
import os

import benchmark_reader as B
import f2_facing_lane as F
import placement_gate as PG
import synth_plan_2d as S


def _doc(elements, walls=None):
    return {"meta": {"units": "mm", "n_elements": len(elements)},
            "elements": [dict(e) for e in elements], "openings": [],
            "glazing_lines": [], "wall_lines": list(walls or [])}


def _sofa(id_, x, y, rot=None, kind="sofa", w=2000.0, d=900.0):
    e = {"id": id_, "x": float(x), "y": float(y), "w": w, "d": d, "kind": kind}
    if rot is not None:
        e["rot"] = float(rot)
    return e


# ---- strip geometry ----------------------------------------------------------------------
def test_strip_on_back_edge_all_cardinals():
    """front(rot)=(sin,-cos): rot 0 faces S -> strip near the N edge; 90 faces E -> W edge;
    180 -> S edge; 270 -> E edge. The strip must sit at the INSET fraction inside the TRUE
    AABB and run parallel to that edge."""
    for rot, back in ((0, "N"), (90, "W"), (180, "S"), (270, "E")):
        e = _sofa("o1", 0, 0, rot=rot)
        line = F._strip_line(e)
        assert line is not None, f"rot {rot}: no strip"
        (ax, ay), (bx, by) = line
        x0, y0, x1, y1 = PG.footprint(e)
        w, h = x1 - x0, y1 - y0
        if back in ("N", "S"):
            assert ay == by, f"rot {rot}: strip not horizontal"
            want = (y1 - F.STRIP_INSET_FRAC * h) if back == "N" else (y0 + F.STRIP_INSET_FRAC * h)
            assert abs(ay - want) < 1e-6
            assert x0 < min(ax, bx) and max(ax, bx) < x1
        else:
            assert ax == bx, f"rot {rot}: strip not vertical"
            want = (x1 - F.STRIP_INSET_FRAC * w) if back == "E" else (x0 + F.STRIP_INSET_FRAC * w)
            assert abs(ax - want) < 1e-6
            assert y0 < min(ay, by) and max(ay, by) < y1


def test_rot90_strip_lives_in_the_rotated_footprint():
    """A kinded element stores the LOCAL un-yawed rect; the strip must be placed in the
    rot-baked AABB (footprint), or every 90/270 piece gets a strip outside its drawn rect."""
    e = _sofa("o1", 0, 0, rot=90)
    x0, y0, x1, y1 = PG.footprint(e)          # 900 x 2000, not 2000 x 900
    assert (x1 - x0, y1 - y0) == (900.0, 2000.0)
    (ax, ay), (bx, by) = F._strip_line(e)
    assert x0 <= min(ax, bx) and max(ax, bx) <= x1
    assert y0 <= min(ay, by) and max(ay, by) <= y1


def test_no_strip_for_noncardinal_rotless_or_nonfacing_kind():
    assert F._strip_line(_sofa("a", 0, 0, rot=45)) is None          # non-cardinal
    assert F._strip_line(_sofa("b", 0, 0)) is None                  # rot-less
    assert F._strip_line(_sofa("c", 0, 0, rot=0, kind="table")) is None   # no facing symbol
    assert F._strip_line(_sofa("d", 0, 0, rot=-90)) is not None     # -90 == 270 (W-facing)


# ---- oriented SVG ------------------------------------------------------------------------
def test_oriented_svg_zero_strips_is_byte_identical_blind():
    doc = _doc([_sofa("o1", 0, 0, kind="table", rot=0), _sofa("o2", 5000, 0)])
    svg, st = F.oriented_svg(doc)
    assert svg == S.synth_svg(doc)
    assert st["strips_drawn"] == 0


def test_oriented_svg_counts_every_skip():
    doc = _doc([_sofa("o1", 0, 0, rot=0), _sofa("o2", 5000, 0, rot=38),
                _sofa("o3", 10000, 0, kind="table", rot=0)])
    svg, st = F.oriented_svg(doc)
    assert st == {"strips_drawn": 1, "skipped_noncardinal_or_rotless": 1,
                  "skipped_nonfacing_kind": 1}
    assert svg.count("<line") == 1


def test_indoor_flip_never_changes_a_byte():
    """The F3 blindness invariant survives the oriented lane: strips read kind+rot only."""
    a = _doc([_sofa("o1", 0, 0, rot=0), _sofa("o2", 5000, 0, rot=90)])
    b = copy.deepcopy(a)
    for e in a["elements"]:
        e["indoor"] = True
    for e in b["elements"]:
        e["indoor"] = False
    assert F.oriented_svg(a)[0] == F.oriented_svg(b)[0]


# ---- closed loop through the UNEDITED reader ----------------------------------------------
def test_closed_loop_recovers_all_four_cardinals(tmp_path):
    """Four isolated sofas at rot 0/90/180/270 -> oriented SVG -> svg_plan_reader (unedited)
    -> facing post-pass -> score_pair: every matched pair must bucket 'exact' (the post-pass
    emits the exact cardinal). This is the wire-proof that reader ink round-trips facing."""
    doc = _doc([_sofa("o1", 0, 0, rot=0), _sofa("o2", 6000, 0, rot=90),
                _sofa("o3", 0, 6000, rot=180), _sofa("o4", 6000, 6000, rot=270)])
    row = F.score_scene(doc, str(tmp_path))
    f2 = row["card_visual"]["F2_facing"]
    assert f2["n"] == 4, f2
    assert f2["buckets"]["exact"] == 4, f2
    assert f2["cardinal_correct"] == 1.0
    assert row["visual_emit"]["rot_emitted"] == 4
    # the HEADLINE wiring pin (review find: a mutant scoring the RAW pred here survived the
    # suite): f2_visual_nobed must be computed from the ENRICHED pred, not the rot-less one
    assert row["f2_visual_nobed"]["n"] == 4
    assert row["f2_visual_nobed"]["cardinal_correct"] == 1.0
    # the blind baseline on the SAME detection set stays all-unreported (0.0, not UNWIRED)
    assert row["f2_blind"]["n"] == 4
    assert row["f2_blind"]["buckets"]["unreported"] == 4
    assert row["f2_blind"]["cardinal_correct"] == 0.0


def test_planted_180_flip_scores_flipped_not_exact(tmp_path):
    """Anti-self-confirmation: draw the strip from a CORRUPTED gt (rot+180) and score against
    the TRUE gt -- the lane must report 'flipped'. If this ever reads 'exact', the loop is
    grading its own homework."""
    truth = _doc([_sofa("o1", 0, 0, rot=0)])
    corrupt = copy.deepcopy(truth)
    corrupt["elements"][0]["rot"] = 180.0
    svg, _ = F.oriented_svg(corrupt)
    p = os.path.join(str(tmp_path), "flip.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    import svg_plan_reader as R
    pred, _ = F.enrich_pred_with_facing(R.read_sheet(p, 1.0), R.read_ink(p)["segs"])
    f2 = B.score_pair(truth, pred)["F2_facing"]
    assert f2["buckets"]["flipped"] == 1 and f2["buckets"]["exact"] == 0, f2


def test_strip_less_drawing_stays_unreported(tmp_path):
    """GT carries rot but the drawing is the BLIND synthesizer's bare rect (no strip): pred
    must stay rot-less and the pair buckets 'unreported' -- never a defaulted angle."""
    truth = _doc([_sofa("o1", 0, 0, rot=0)])
    svg = S.synth_svg(truth)                    # blind lane: no facing ink at all
    p = os.path.join(str(tmp_path), "bare.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    import svg_plan_reader as R
    pred, est = F.enrich_pred_with_facing(R.read_sheet(p, 1.0), R.read_ink(p)["segs"])
    assert est["rot_emitted"] == 0
    f2 = B.score_pair(truth, pred)["F2_facing"]
    assert f2["buckets"]["unreported"] == 1, f2


def test_fused_neighbour_outline_does_not_spoof_facing(tmp_path):
    """The fusion-spoof pin (observed live on scene_00006): an UNLABELED neighbour rect
    within the reader's fuse distance merges into the sofa's cluster; its outline then sits
    at an interior inset of the fused bbox where read_facing would score it as a giant
    'strip'. Outline rings are filtered before the read, so the true back-strip must win."""
    truth = _doc([_sofa("o1", 0, 0, rot=0),
                  {"id": "o2", "x": -650.0, "y": 0.0, "w": 600.0, "d": 900.0}])
    svg, st = F.oriented_svg(truth)
    assert st["strips_drawn"] == 1
    p = os.path.join(str(tmp_path), "fused.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    import svg_plan_reader as R
    pred = R.read_sheet(p, 1.0)
    assert len(pred["elements"]) == 1           # the two rects DID fuse (gap 50 < ~90)
    pv, est = F.enrich_pred_with_facing(pred, R.read_ink(p)["segs"])
    assert est["rot_emitted"] == 1
    f2 = B.score_pair(truth, pv)["F2_facing"]
    assert f2["buckets"]["exact"] == 1, f2


def test_ring_filter_drops_rect_outlines_keeps_strips():
    """4-segment closed rectangles are outline ink; the lone strip stroke survives."""
    rect = [[(0.0, 0.0), (2000.0, 0.0)], [(2000.0, 0.0), (2000.0, 900.0)],
            [(2000.0, 900.0), (0.0, 900.0)], [(0.0, 900.0), (0.0, 0.0)]]
    strip = [[(400.0, 792.0), (1600.0, 792.0)]]
    ring = F._ring_member_idx(rect + strip)
    assert ring == {0, 1, 2, 3}


def test_ring_filter_removes_duplicate_flush_edges():
    """Flush-adjacent furniture draws TWO identical verticals at the shared edge; every
    coincident side must be removed, or the survivor spoofs a full-height 'strip' on a
    fused cluster (scene_00005 o15: W=1.0 from one leftover edge -> 90-degree wrong)."""
    rect = [[(0.0, 0.0), (2000.0, 0.0)], [(2000.0, 0.0), (2000.0, 900.0)],
            [(2000.0, 900.0), (0.0, 900.0)], [(0.0, 900.0), (0.0, 0.0)]]
    dup_left = [[(0.0, 0.0), (0.0, 900.0)]]     # a flush neighbour's coincident right edge
    ring = F._ring_member_idx(rect + dup_left)
    assert ring == {0, 1, 2, 3, 4}


def test_attach_rot_reemits_local_rect_so_footprint_round_trips():
    """Pred-side double-rotation pin (the adapter's 9a8c4b3 lesson, mirrored): attaching rot
    90/270 to a world-AABB element must re-emit the local un-yawed rect so
    placement_gate.footprint rebuilds the SAME AABB. Without this every correct 90/270 read
    swaps its axes under footprint() and detection-misses at IoU<0.5."""
    el = {"id": "c1", "x": 6548.0, "y": -544.0, "w": 900.0, "d": 1998.0}
    before = PG.footprint(el)
    F._attach_rot(el, 90)
    after = PG.footprint(el)
    assert all(abs(a - b) < 0.11 for a, b in zip(before, after)), (before, after)
    assert el["rot"] == 90.0
    el0 = {"id": "c2", "x": 0.0, "y": 0.0, "w": 2000.0, "d": 900.0}
    F._attach_rot(el0, 180)                     # 0/180: geometry untouched
    assert (el0["x"], el0["y"], el0["w"], el0["d"]) == (0.0, 0.0, 2000.0, 900.0)


def test_washed_out_read_stays_rotless_never_defaulted(tmp_path):
    """The flattering-scorer hole (M3.2 lesson, benchmark_reader.score_facing docstring):
    ink PRESENT but unreadable must stay rot-less and bucket 'unreported' -- never default
    to rot 0 (the most common GT). The bare-rect test alone does not pin this: there the
    ring filter empties `local` before read_facing runs. Here a decoy stroke mirrored on
    the OPPOSITE edge leaves non-empty local segs with a dominance washout (facing=None) --
    a mutant that defaults rot when segments exist would score 'exact' and inflate."""
    truth = _doc([_sofa("o1", 0, 0, rot=0)])
    svg, st = F.oriented_svg(truth)
    assert st["strips_drawn"] == 1              # real strip in the N band (y=792)
    decoy = '<line x1="400.0" y1="108.0" x2="1600.0" y2="108.0"/>'   # mirrored S-band stroke
    svg = svg.replace("</svg>", decoy + "\n</svg>")
    p = os.path.join(str(tmp_path), "washout.svg")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(svg)
    import svg_plan_reader as R
    pred, est = F.enrich_pred_with_facing(R.read_sheet(p, 1.0), R.read_ink(p)["segs"])
    assert est["rot_emitted"] == 0
    f2 = B.score_pair(truth, pred)["F2_facing"]
    assert f2["buckets"]["unreported"] == 1, f2


# ---- beds-excluded headline ----------------------------------------------------------------
def test_facing_nobed_excludes_beds_from_n():
    """S3D bed rot encodes the length axis, not facing (validated report) -- the headline
    must be computable without beds while score_pair's card still includes them."""
    gt = _doc([_sofa("o1", 0, 0, rot=0), _sofa("o2", 6000, 0, rot=0, kind="bed")])
    pred = copy.deepcopy(gt)                    # perfect pred, rot included
    full = B.score_pair(gt, pred)["F2_facing"]
    nobed = F._facing_nobed(gt, pred)
    assert full["n"] == 2 and nobed["n"] == 1


# ---- wall-prior oracle lane -----------------------------------------------------------------
def test_wall_prior_faces_away_from_backing_wall_all_sides():
    """Back to the N wall -> face S (rot 0); E wall -> W (270); S wall -> N (180);
    W wall -> E (90). Sign errors here would silently mirror the whole oracle lane."""
    el = {"id": "c1", "x": 0.0, "y": 0.0, "w": 2000.0, "d": 900.0}
    for wall, want in (
        ({"x1": -500, "y1": 950, "x2": 2500, "y2": 950}, 0.0),      # N wall (gap 50)
        ({"x1": 2050, "y1": -500, "x2": 2050, "y2": 1400}, 270.0),  # E wall
        ({"x1": -500, "y1": -50, "x2": 2500, "y2": -50}, 180.0),    # S wall
        ({"x1": -50, "y1": -500, "x2": -50, "y2": 1400}, 90.0),     # W wall
    ):
        pred = {"elements": [dict(el)]}
        out, st = F.wall_prior_pred(pred, [wall])
        assert st["rot_emitted"] == 1
        assert out["elements"][0]["rot"] == want, (wall, out["elements"][0])


def test_wall_prior_stays_silent_off_wall():
    el = {"id": "c1", "x": 0.0, "y": 0.0, "w": 2000.0, "d": 900.0}
    far = {"x1": -500, "y1": 2000, "x2": 2500, "y2": 2000}   # gap 1100 > 450
    out, st = F.wall_prior_pred({"elements": [dict(el)]}, [far])
    assert st["rot_emitted"] == 0
    assert "rot" not in out["elements"][0]


def test_wall_prior_never_mutates_input():
    pred = {"elements": [{"id": "c1", "x": 0.0, "y": 0.0, "w": 2000.0, "d": 900.0}]}
    F.wall_prior_pred(pred, [{"x1": -500, "y1": 950, "x2": 2500, "y2": 950}])
    assert "rot" not in pred["elements"][0]


# ---- aggregation + corpus runner ------------------------------------------------------------
def test_sum_facing_sums_integer_counts_not_ratios():
    a = {"buckets": {"exact": 1, "cardinal": 0, "flipped": 0, "wrong": 0, "unreported": 0}}
    b = {"buckets": {"exact": 0, "cardinal": 1, "flipped": 1, "wrong": 0, "unreported": 1}}
    agg = F._sum_facing([a, b, None])
    assert agg["n"] == 4 and agg["hits"] == 2 and agg["cardinal_correct"] == 0.5


def test_score_corpus_writes_rows_and_report(tmp_path):
    gt_dir, out_dir = tmp_path / "gt", tmp_path / "out"
    os.makedirs(gt_dir)
    doc = _doc([_sofa("o1", 0, 0, rot=0), _sofa("o2", 6000, 0, rot=90)],
               walls=[{"x1": -500, "y1": 950, "x2": 2500, "y2": 950}])
    with open(gt_dir / "scene_x.gt.json", "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    rows, skipped = F.score_corpus(str(gt_dir), str(out_dir))
    assert len(rows) == 1 and skipped == {"error": 0, "units": 0}
    assert (out_dir / "cards.jsonl").exists() and (out_dir / "report.md").exists()
    rep = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "cardinal_correct" in rep and "ORACLE-WALLS TIER" in rep
    assert "CLOSED LOOP" in rep
    # oracle-lane wiring pins (review find: two mutants survived -- visual card mislabeled
    # as oracle, and wall_prior run on the ENRICHED pred). The fixture discriminates: o1 is
    # wall-backed (exact via the prior), o2 is off-wall (must stay unreported in the oracle
    # lane even though the VISUAL lane read its strip). Either mutant turns this into
    # {exact: 2, unreported: 0}.
    assert rows[0]["card_oracle"]["F2_facing"]["buckets"] == \
        {"exact": 1, "cardinal": 0, "flipped": 0, "wrong": 0, "unreported": 1}
    assert rows[0]["f2_visual_nobed"]["n"] == 2
    assert rows[0]["f2_visual_nobed"]["cardinal_correct"] == 1.0


def test_score_corpus_skips_non_mm_units(tmp_path):
    gt_dir, out_dir = tmp_path / "gt", tmp_path / "out"
    os.makedirs(gt_dir)
    doc = _doc([_sofa("o1", 0, 0, rot=0)])
    doc["meta"]["units"] = "cm"
    with open(gt_dir / "scene_bad.gt.json", "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    rows, skipped = F.score_corpus(str(gt_dir), str(out_dir))
    assert rows == [] and skipped["units"] == 1
