"""Tests for sheet_recon.py — DRW-1's bridge between the drawing and the build.

Both-sides controls, per the doubt discipline: every rule that can pass must be
shown failing on the thing it exists to refuse. The two live lies caught on the
instrument's FIRST night are pinned as regressions:
  * bbox coverage: an L-shaped millwork run's union bbox "covered" the bed drawn
    inside its elbow — footprint coverage must read ~0 there;
  * ratio-cap blindness: bed__headboard sat exactly on the drawn headboard band
    and scored 0.00 because its parent assembly was too big — the part tier must
    see it.
"""
import copy

import sheet_recon as sr


def _obj(name, x0, y0, z0, x1, y1, z1, in_frustum=True, hidden=False):
    return {"name": name, "hidden_render": hidden,
            "aabb": [[x0, y0, z0], [x1, y1, z1]], "in_frustum": in_frustum}


# ---------------------------------------------------------------- geometry --
def test_rect_overlap_area():
    assert sr.rect_overlap_area((0, 0, 10, 10), (5, 5, 10, 10)) == 25
    assert sr.rect_overlap_area((0, 0, 10, 10), (20, 20, 5, 5)) == 0


def test_rect_vs_convex_poly_in_out_straddle_none():
    poly = [[0, 0], [100, 0], [100, 100], [0, 100]]
    assert sr.rect_intersects_convex_poly((10, 10, 20, 20), poly) is True
    assert sr.rect_intersects_convex_poly((200, 200, 20, 20), poly) is False
    assert sr.rect_intersects_convex_poly((90, 90, 40, 40), poly) is True
    assert sr.rect_intersects_convex_poly((10, 10, 20, 20), None) is None
    # diamond: the rect sits in the poly's BBOX corner but outside the poly —
    # a bbox pretest alone would lie here
    diamond = [[50, 0], [100, 50], [50, 100], [0, 50]]
    assert sr.rect_intersects_convex_poly((0, 0, 10, 10), diamond) is False


def test_coverage_L_shape_interior_is_not_covered():
    # two 100mm bands forming an L; the elbow interior is empty
    bands = [(0, 0, 1000, 100), (0, 0, 100, 1000)]
    inner = (300, 300, 400, 400)
    assert sr.coverage_by_parts(inner, bands) == 0.0
    on_band = (200, 0, 400, 100)
    assert sr.coverage_by_parts(on_band, bands) > 0.95


# ---------------------------------------------------------------- assemblies --
def test_prefix_split_and_spatial_split():
    objs = [
        _obj("nightstand__a", 0.0, 0.0, 0.0, 0.3, 0.3, 0.5),
        _obj("nightstand__b", 3.0, 0.0, 0.0, 3.3, 0.3, 0.5),
        _obj("bed__frame", 1.0, 0.0, 0.0, 3.0, 2.0, 0.3),
        _obj("bed__mattress", 1.05, 0.05, 0.3, 2.95, 1.95, 0.6),
    ]
    asm = sr.assemblies_from_dump(objs)
    names = sorted(a["name"] for a in asm)
    # nightstand splits into two spatial components; bed parts merge into one
    assert sum(1 for n in names if n.startswith("nightstand@")) == 2
    assert sum(1 for n in names if n.startswith("bed")) == 1
    bed = next(a for a in asm if a["name"].startswith("bed"))
    assert len(bed["parts"]) == 2
    assert abs(bed["footprint_m2"] - (2 * 2 + 1.9 * 1.9)) < 0.05


def test_hidden_render_objects_are_not_assemblies():
    objs = [_obj("ghost", 0, 0, 0, 1, 1, 1, hidden=True)]
    assert sr.assemblies_from_dump(objs) == []


def test_frustum_flag_any_true_and_any_none():
    objs = [_obj("m__a", 0, 0, 0, 1, 1, 1, in_frustum=False),
            _obj("m__b", 0.9, 0, 0, 2, 1, 1, in_frustum=True)]
    assert sr.assemblies_from_dump(objs)[0]["in_frustum"] is True
    objs2 = [_obj("m__a", 0, 0, 0, 1, 1, 1, in_frustum=False)]
    del objs2[0]["in_frustum"]
    objs2[0]["in_frustum"] = None
    assert sr.assemblies_from_dump(objs2)[0]["in_frustum"] is None


# ------------------------------------------------------------------ matching --
def _asm(objs):
    return sr.assemblies_from_dump(objs)


def test_loose_item_matches_and_floor_is_refused_by_footprint():
    objs = [_obj("floor", 0, 0, -0.1, 6, 9, 0.0),
            _obj("bench__seat", 2.6, 0.6, 0.0, 3.15, 1.65, 0.45)]
    row = {"rect_mm": (2646, 626, 504, 1008), "floor_standing": True}
    cands = sr.match_row(row, _asm(objs))
    assert cands and cands[0]["assembly"].startswith("bench")
    assert all("floor" not in c["assembly"] for c in cands)


def test_small_band_matches_part_of_big_assembly():
    # REGRESSION (first live run): headboard band vs the whole bed assembly
    objs = [_obj("bed__frame", 3.2, 0.05, 0.0, 5.14, 2.2, 0.6),
            _obj("bed__headboard", 5.14, -0.05, 0.0, 5.2, 2.35, 1.1)]
    row = {"rect_mm": (5140, -46, 60, 2352), "floor_standing": True}
    cands = sr.match_row(row, _asm(objs))
    assert cands and cands[0]["assembly"].endswith("/bed__headboard")
    assert cands[0]["coverage"] >= sr.COVER_MIN


def test_L_bbox_does_not_cover_its_interior():
    # REGRESSION (first live run): millwork L "covered" the bed via union bbox
    objs = [_obj("mill__band_e", 5.2, -0.45, 0.0, 5.3, 3.4, 2.8),
            _obj("mill__band_n", 2.35, 2.8, 0.0, 5.3, 3.4, 2.8)]
    bed_row = {"rect_mm": (3048, 100, 2134, 1981), "floor_standing": True}
    cands = sr.match_row(bed_row, _asm(objs))
    assert all(c["coverage"] < sr.COVER_MIN for c in cands)


def test_rug_is_demoted_when_a_rising_candidate_also_clears():
    objs = [_obj("rug", 2.2, -0.35, 0.0, 5.3, 2.15, 0.012),
            _obj("bed__frame", 3.0, 0.1, 0.0, 5.15, 2.1, 0.6)]
    row = {"rect_mm": (3048, 100, 2100, 1950), "floor_standing": True}
    cands = sr.match_row(row, _asm(objs))
    assert cands[0]["assembly"].startswith("bed")


def test_floor_standing_refuses_ceiling_objects():
    objs = [_obj("pelmet__band", 4.7, 2.2, 2.4, 5.0, 2.5, 2.8)]
    row = {"rect_mm": (4794, 2306, 300, 300), "floor_standing": True}
    assert sr.match_row(row, _asm(objs)) == []
    # the same band is a legal candidate for a NON-floor-standing (full-height) row
    row2 = {"rect_mm": (4794, 2306, 300, 300)}
    assert sr.match_row(row2, _asm(objs)) != []


# ------------------------------------------------------------------ verdicts --
def _row(cov=None, gap=None):
    r = {"rect_mm": (0, 0, 100, 100), "gap": gap}
    if cov is not None:
        r["match"] = {"candidates": [{"assembly": "a", "coverage": cov}]}
    return r


def test_verdict_matched_gap_unresolved():
    assert sr.verdict_of(_row(cov=0.9)) == ("matched", None)
    assert sr.verdict_of(_row()) == ("UNRESOLVED", None)
    ok_gap = {"reason": "outside camera scope", "decided_by": "builder"}
    assert sr.verdict_of(_row(gap=ok_gap)) == ("declared_gap", None)


def test_pending_gap_is_refused_by_name():
    v, warn = sr.verdict_of(_row(gap={"reason": "x", "decided_by": "pending"}))
    assert v == "UNRESOLVED" and "pending" in warn


def test_stale_gap_warns_when_object_is_built():
    v, warn = sr.verdict_of(
        _row(cov=0.9, gap={"reason": "x", "decided_by": "builder"}))
    assert v == "matched" and "STALE" in warn


# ----------------------------------------------------------------- reconcile --
def _dump(objs, poly=None):
    d = {"objects": objs}
    if poly:
        d["camera"] = {"floor_poly_mm": poly}
    return d


def test_reconcile_blocking_rules():
    objs = [_obj("bench__seat", 2.6, 0.6, 0.0, 3.15, 1.65, 0.45)]
    rows = [
        {"id": "A", "rect_mm": [2646, 626, 504, 1008], "floor_standing": True,
         "gap": None},                                     # matched
        {"id": "B", "rect_mm": [0, 0, 500, 500], "gap": None},   # unresolved, in poly
        {"id": "C", "rect_mm": [90000, 90000, 500, 500], "gap": None},  # out of poly
    ]
    poly = [[-1000, -1000], [7000, -1000], [7000, 9000], [-1000, 9000]]
    out, s = sr.reconcile(copy.deepcopy(rows), _dump(objs, poly), "f.json",
                          today="2026-08-11")
    assert s["matched"] == 1 and s["unresolved"] == 2
    # out-of-frustum unresolved does not block; in-frustum does
    assert s["blocking"] == 1
    # machine never invents the human half
    assert all("identity" not in r or r["identity"] is None for r in out
               if r["id"] == "B")


def test_unknown_frustum_blocks():
    objs = [_obj("x__a", 0, 0, 0, 0.1, 0.1, 0.1)]
    del objs[0]["in_frustum"]
    rows = [{"id": "B", "rect_mm": [4000, 4000, 500, 500], "gap": None}]
    _out, s = sr.reconcile(rows, _dump(objs), "f.json", today="2026-08-11")
    assert s["unresolved"] == 1 and s["blocking"] == 1


def test_frames_agree_and_disagree():
    objs = [_obj("a", 0, -0.7, 0, 5.65, 8.65, 2.8)]
    rows = [{"rect_mm": [0, -450, 5650, 9050]}]
    assert sr._frames_agree(rows, {"objects": objs}) is True
    shifted = [_obj("a", 50, 49.3, 0, 55.65, 58.65, 2.8)]
    assert sr._frames_agree(rows, {"objects": shifted}) is False


def test_thai_row_names_survive_a_cp1252_stdout(tmp_path, monkeypatch):
    """REGRESSION: --recon crashed printing Thai names through a cp1252 console,
    and the crash exited 1 — the code that means 'a claim is broken'. A console
    encoding must never be able to forge a verdict."""
    import io
    import json as _json
    import os as _os
    led = {"source_sheet": {"pdf": "x.pdf", "page": 1},
           "extract_params": {"zone": [0, 0, 1, 1], "close_mm": 18},
           "rows": [{"id": "SR-01", "key": "k", "rect_mm": [2646, 626, 504, 1008],
                     "drawn_as": "ม้านั่งปลายเตียง", "floor_standing": True,
                     "gap": None}]}
    lp = tmp_path / "led.json"
    lp.write_text(_json.dumps(led, ensure_ascii=False), encoding="utf-8")
    dp = tmp_path / "dump.json"
    dp.write_text(_json.dumps({"objects": [
        _obj("bench__seat", 2.6, 0.6, 0.0, 3.15, 1.65, 0.45)]}), encoding="utf-8")
    monkeypatch.setattr(sr, "LEDGER", str(lp))
    fake = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sr.sys, "stdout", fake)
    rc = sr.main(["sheet_recon", "--recon", str(dp)])
    assert rc == 0


# --------------------------------------------------------------- spec ratchet --
def _ratchet_ledger():
    return {"rows": [{"id": "SR-01", "spec_mass": "bed"}],
            "spec_ratchet": {"baseline": {"bed": [1, 2, 3, 4, 5],
                                          "old_lamp": [9, 9, 9, 9, 9]}}}


def _mass(name, x=1, y=2, w=3, d=4, h=5, ref=None):
    m = {"name": name, "x": x, "y": y, "w": w, "d": d, "h": h}
    if ref is not None:
        m["sheet_ref"] = ref
    return m


def test_ratchet_grandfathers_unchanged_and_counts_debt():
    spec = {"items": [_mass("bed"), _mass("old_lamp", 9, 9, 9, 9, 9)]}
    viol, stats = sr.spec_ratchet_check(_ratchet_ledger(), spec)
    assert viol == []
    assert stats["covered"] == 1 and stats["backfill_debt"] == 1


def test_ratchet_bites_on_edit_and_on_new():
    spec = {"items": [_mass("bed", x=999),              # edited, no ref
                      _mass("new_chair")]}              # new, no ref
    viol, _ = sr.spec_ratchet_check(_ratchet_ledger(), spec)
    assert len(viol) == 2
    assert any("EDITED" in v for v in viol) and any("NEW" in v for v in viol)


def test_ratchet_accepts_sr_ref_and_declared_not_in_drawing():
    spec = {"items": [_mass("bed", x=999, ref="SR-01"),
                      _mass("rug", ref="not-in-drawing: styling decision D1-A")]}
    viol, stats = sr.spec_ratchet_check(_ratchet_ledger(), spec)
    assert viol == []
    assert stats["edited_ok"] == 1 and stats["new_ok"] == 1


def test_ratchet_refuses_bogus_ref_and_empty_reason():
    spec = {"items": [_mass("bed", x=999, ref="SR-99"),        # id not in ledger
                      _mass("thing", ref="not-in-drawing: x")]}  # reason too thin
    viol, _ = sr.spec_ratchet_check(_ratchet_ledger(), spec)
    assert len(viol) == 2


def test_ratchet_backfill_lands_via_declared_ref_on_unchanged_mass():
    spec = {"items": [_mass("old_lamp", 9, 9, 9, 9, 9,
                            ref="not-in-drawing: styling decision, lamp rides D3-3")]}
    viol, stats = sr.spec_ratchet_check(_ratchet_ledger(), spec)
    assert viol == [] and stats["covered"] == 1 and stats["backfill_debt"] == 0


def test_ratchet_without_baseline_is_could_not_run():
    viol, stats = sr.spec_ratchet_check({"rows": []}, {"items": [_mass("bed")]})
    assert viol is None and stats is None


def test_gate_line_names_the_counts():
    line = sr.gate_line({"drawn": 18, "matched": 17, "gaps": 0, "unresolved": 1,
                         "blocking": 0, "frustum_source": "floor_poly"})
    assert "18 drawn" in line and "1 UNRESOLVED" in line and "0 blocking" in line
