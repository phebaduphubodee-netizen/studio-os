"""Pins for symbol_unit_lane: the mirrored grouping cannot drift from group_symbols, the
bucket accounting cannot leak, the two headline buckets (granularity / fused_cross_symbol)
classify the constructed cases they exist for, the wall-partitioned variant splits exactly
at walls, and the pred-reproduction pin actually fails on a mismatch."""
import json
import os
import sys

import pytest

import symbol_unit_lane as SU
from synth_plan_2d import group_symbols

MM = {"units": "mm"}


def doc(elements, walls=None):
    return {"meta": dict(MM), "elements": elements,
            "wall_lines": walls or [], "glazing_lines": [], "openings": []}


def el(i, x, y, w, d, **kw):
    return {"id": f"o{i}", "x": x, "y": y, "w": w, "d": d, **kw}


# ---- membership mirror pin -----------------------------------------------------------------
def _mirror_case(elements):
    symbols, member_of, decor, oversize = SU.symbol_membership(elements)
    SU.assert_matches_group_symbols(elements, symbols)   # raises on drift
    ref = group_symbols({"meta": dict(MM), "elements": elements})[0]["elements"]
    assert len(symbols) == len(ref)
    # membership is internally consistent: n_members == assigned members, every member
    # inside its union AABB
    for gi, s in enumerate(symbols):
        assert s["n_members"] == len(s["member_idx"])
        for i in s["member_idx"]:
            assert member_of[i] == gi
    assigned = {i for s in symbols for i in s["member_idx"]}
    assert assigned | decor | oversize == set(range(len(elements)))
    assert not (assigned & decor) and not (assigned & oversize)


def test_membership_matches_group_symbols_simple_groups():
    _mirror_case([el(0, 0, 0, 2000, 1800), el(1, 2050, 0, 400, 400),      # fuse (gap 50)
                  el(2, 6000, 6000, 600, 600),                            # singleton
                  el(3, 10, 10, 60, 90),                                  # decor (thin)
                  el(4, -9000, -9000, 4000, 4000)])                       # oversize single


def test_membership_matches_group_symbols_rot_and_chain():
    # rot 90 bakes into the footprint (w/d swap around centre) exactly as group_symbols does;
    # a transitive chain a-b-c groups even though a-c alone would not fuse
    _mirror_case([el(0, 0, 0, 1600, 400, rot=90.0), el(1, 0, 900, 400, 400),
                  el(2, 0, 1350, 400, 400), el(3, 0, 1800, 400, 400)])


def test_wall_partition_vetoes_cross_wall_union():
    elements = [el(0, 0, 0, 2000, 2000), el(1, 2060, 0, 2000, 2000)]      # gap 60 < 90
    plain, _m, _d, _o = SU.symbol_membership(elements)
    assert len(plain) == 1 and plain[0]["n_members"] == 2
    split, m2, _d2, _o2 = SU.symbol_membership(
        elements, allowed=lambda i, j: False)                             # hard veto
    assert len(split) == 2 and all(s["n_members"] == 1 for s in split)
    assert m2 == {0: 0, 1: 1}


# ---- end-to-end scenes through the real reader ---------------------------------------------
def test_granularity_bucket_bed_plus_nightstand(tmp_path):
    # 50mm gap: the reader fuses both into one cluster; the union matches the BED per-object
    # (IoU 0.82) and matches the SYMBOL; the nightstand is a granularity member, not a miss
    d = doc([el(0, 0, 0, 2000, 1800), el(1, 2050, 0, 400, 400)])
    row = SU.score_scene(d, str(tmp_path))
    for side in ("before", "after"):
        assert row[side]["perobj"] == {"n_gt": 2, "n_pred": 1, "matched": 1}
        assert row[side]["buckets"]["matched"] == 1
        assert row[side]["buckets"]["granularity"] == 1
        assert sum(row[side]["buckets"].values()) == 2
        assert row[side]["symbol"]["matched"] == 1
        assert row[side]["symbol"]["members_in_matched_sym"] == 2
    assert "after_wallgroup" not in row                    # no walls -> no secondary unit


def test_fused_cross_symbol_via_decor_bridge(tmp_path):
    # two 600mm symbols 260mm apart (grouping keeps them separate: 260 > 90) bridged in INK
    # by a thin decor rect (70mm gaps, inside the closing's ~84mm reach): ONE pred cluster
    # covers both -> REAL within-room fusion, classified fused_cross_symbol for both members
    d = doc([el(0, 0, 0, 600, 600), el(1, 860, 0, 600, 600),
             el(2, 670, 240, 120, 120)])
    row = SU.score_scene(d, str(tmp_path))
    for side in ("before", "after"):
        assert row[side]["perobj"]["matched"] == 0
        assert row[side]["buckets"]["fused_cross_symbol"] == 2
        assert row[side]["buckets"]["decor_micro"] == 1
        assert sum(row[side]["buckets"].values()) == 3
        assert row[side]["pred_purity"]["2"] == 1          # the one cluster covers 2 symbols


def test_cross_wall_pair_before_after_and_wallgroup(tmp_path):
    # two rooms' identical cabinets 60mm apart across a wall: BEFORE the reader fuses them
    # (each rect vs the union sits just under IoU 0.5 -> both unmatched; the PLAIN grouping
    # chains across the wall exactly like the ink, so the union symbol matches and both
    # members read as `granularity` -- the v1.1 chain-lumping limit, documented). AFTER the
    # barrier severs the bridge: both match per-object; the WALL-PARTITIONED unit vetoes the
    # union so its symbol set is 2, both matched.
    walls = [{"x1": 2030.0, "y1": -200.0, "x2": 2030.0, "y2": 2200.0}]
    d = doc([el(0, 0, 0, 2000, 2000), el(1, 2060, 0, 2000, 2000)], walls=walls)
    row = SU.score_scene(d, str(tmp_path))
    assert row["before"]["perobj"]["matched"] == 0
    assert row["before"]["buckets"]["granularity"] == 2
    assert row["after"]["perobj"]["matched"] == 2
    assert row["after"]["buckets"]["matched"] == 2
    wg = row["after_wallgroup"]
    assert wg["symbol"]["n_sym"] == 2 and wg["symbol"]["matched"] == 2
    assert wg["buckets"]["matched"] == 2
    assert row["n_regions"] >= 2


def test_zero_walls_after_equals_before(tmp_path):
    d = doc([el(0, 0, 0, 600, 600), el(1, 2000, 2000, 800, 500)])
    row = SU.score_scene(d, str(tmp_path))
    assert row["before"] == row["after"]


def test_elongated_thin_bucket_and_matched_thin_counter():
    # a curtain (<150mm one axis) is screened out of the SYMBOL unit but a kept pred CAN
    # reach it at IoU 0.5 -- unmatched it buckets as decor_thin_elongated, matched it
    # buckets as matched AND increments matched_thin (the screen's measured cost)
    curtain = el(0, 0, 0, 140, 3000)
    symbols, member_of, decor, oversize = SU.symbol_membership([curtain])
    assert decor == {0} and not symbols
    out = SU.decompose([curtain], [], symbols, member_of, decor, oversize)
    assert out["buckets"]["decor_thin_elongated"] == 1
    assert out["matched_thin"] == 0
    pred = [{"id": "p0", "x": -5.0, "y": 0.0, "w": 150.0, "d": 3000.0}]
    out2 = SU.decompose([curtain], pred, symbols, member_of, decor, oversize)
    assert out2["buckets"]["matched"] == 1
    assert out2["matched_thin"] == 1


# ---- pred-reproduction pin mechanism --------------------------------------------------------
def _fake_row(matched, missed):
    side = {"perobj": {"n_gt": matched + len(missed), "n_pred": matched, "matched": matched},
            "perobj_missed_ids": sorted(missed)}
    return {"before": side, "after": json.loads(json.dumps(side))}


def _fake_pin(matched, missed):
    det = {"n_gt": matched + len(missed), "n_pred": matched, "matched": matched,
           "missed_ids": list(missed)}
    return (det, json.loads(json.dumps(det)))


def test_check_pin_equal_and_mismatch():
    assert SU.check_pin(_fake_row(3, ["o1", "o2"]), _fake_pin(3, ["o2", "o1"]))
    assert not SU.check_pin(_fake_row(3, ["o1", "o2"]), _fake_pin(4, ["o1"]))
    assert not SU.check_pin(_fake_row(3, ["o1", "o2"]), _fake_pin(3, ["o1", "o9"]))


def test_load_pin_cards_skips_skipped_rows(tmp_path):
    p = tmp_path / "run"
    os.makedirs(p)
    with open(p / "cards.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"scene": "s1", "skipped": "error"}) + "\n")
        fh.write(json.dumps({"scene": "s2",
                             "card_before": {"detection": _fake_pin(1, [])[0]},
                             "card_after": {"detection": _fake_pin(1, [])[0]}}) + "\n")
    pins = SU.load_pin_cards(str(p))
    assert set(pins) == {"s2"}


def test_iou_histogram_counts_matched_symbols(tmp_path):
    # every matched symbol lands in exactly one 0.1 bin; the sum equals symbol.matched
    d = doc([el(0, 0, 0, 2000, 1800), el(1, 2050, 0, 400, 400),
             el(2, 8000, 8000, 900, 700)])
    row = SU.score_scene(d, str(tmp_path))
    for side in ("before", "after"):
        assert sum(row[side]["sym_iou_hist"]) == row[side]["symbol"]["matched"] == 2


def test_oversize_symbol_that_matches_counts_as_granularity_and_is_counted():
    # a 3700x3700 union symbol CAN match a one-axis-oversize kept pred (only both-axes
    # >3600 preds are dropped): its members bucket as granularity (the reader genuinely
    # emitted that cluster) and the event is COUNTED, never asserted impossible
    e = el(0, 0, 0, 3700, 3700)
    symbols, member_of, decor, oversize = SU.symbol_membership([e])
    assert oversize == {0} and not symbols       # single-object oversize: screened upstream
    # two members whose union is oversize: 3700x1800 stacked with a 100mm gap
    e1, e2 = el(0, 0, 0, 3700, 1800), el(1, 0, 1880, 3700, 1820)
    symbols, member_of, decor, oversize = SU.symbol_membership([e1, e2])
    assert len(symbols) == 1 and symbols[0]["d"] == 3700.0
    pred = [{"id": "p0", "x": 0.0, "y": 0.0, "w": 3700.0, "d": 3600.0}]  # kept: one axis <=3600
    out = SU.decompose([e1, e2], pred, symbols, member_of, decor, oversize)
    assert out["symbol"]["oversize_sym_matched"] == 1
    assert out["buckets"]["granularity"] + out["buckets"]["matched"] == 2
    assert out["buckets"]["union_oversize_region"] == 0


def test_drift_assert_blocks_all_green(tmp_path, monkeypatch):
    # a scene whose loud-drift assert fires must surface as drift_assert + pinned-but-
    # unscored and flip the flag -- never a quiet skip under an ALL-GREEN banner
    gt_dir = tmp_path / "gt"
    run_dir = tmp_path / "committed"
    out_dir = tmp_path / "out"
    os.makedirs(gt_dir); os.makedirs(run_dir)
    for name in ("scene_a", "scene_b"):
        with open(gt_dir / f"{name}.gt.json", "w", encoding="utf-8") as fh:
            json.dump(doc([el(0, 0, 0, 600, 600)]), fh)
    det = {"n_gt": 1, "n_pred": 1, "matched": 1, "missed_ids": []}
    with open(run_dir / "cards.jsonl", "w", encoding="utf-8") as fh:
        for name in ("scene_a", "scene_b"):
            fh.write(json.dumps({"scene": name, "card_before": {"detection": det},
                                 "card_after": {"detection": det}}) + "\n")
    real = SU.score_scene

    def boom(gt_doc, td):
        if gt_doc.get("_boom"):
            raise AssertionError("mirror drifted")
        return real(gt_doc, td)

    monkeypatch.setattr(SU, "score_scene", boom)
    with open(gt_dir / "scene_b.gt.json", encoding="utf-8") as fh:
        d2 = json.load(fh)
    d2["_boom"] = True
    with open(gt_dir / "scene_b.gt.json", "w", encoding="utf-8") as fh:
        json.dump(d2, fh)
    rows, skipped = SU.score_corpus(str(gt_dir), str(out_dir), pin_dir=str(run_dir))
    assert skipped["drift_assert"] == 1
    report = open(out_dir / "report.md", encoding="utf-8").read()
    assert "DRIFT ASSERT FIRED" in report
    assert "ALL GREEN" not in report
    assert "1 pinned-but-unscored" in report


# ---- bucket accounting cannot leak (the invariant is asserted inside decompose) -------------
def test_bucket_leak_raises():
    # decompose asserts sum(buckets) == n_gt; drive it with a clean set + empty pred so
    # every element must land in a non-matched bucket
    clean = [el(0, 0, 0, 600, 600), el(1, 10, 10, 50, 50), el(2, 5000, 5000, 4000, 4000)]
    symbols, member_of, decor, oversize = SU.symbol_membership(clean)
    out = SU.decompose(clean, [], symbols, member_of, decor, oversize)
    assert out["buckets"]["dropped_no_pred"] == 1          # the drawable symbol, no pred
    assert out["buckets"]["decor_micro"] == 1
    assert out["buckets"]["oversize_single"] == 1
    assert sum(out["buckets"].values()) == 3


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
