"""
test_facade_reader.py -- the ZONE-SCOPED glazed-facade reader (pure geometry, no fitz).

Fixtures use the REAL floor-2 sitting-room numbers already verified in test_zone_flag.py:
the south edge y_s=0 spanning x[5750,10650] (4900 mm), the glazed facade drawn as a 0.48 pt PAIR
at c~=98.9 (inner glass) and c~=200 (frame), each ~4.9 m, and the OUTER garden slab-lip pair at
c~=-1050/-1152. The reader must surface the c~=99 line ONLY (garden excluded by the 600 mm band),
reject furniture double-lines (short + don't span the open edge), and abstain on a walled edge.
The last test is the PRODUCTION REPLAY on the real PDF (fitz-guarded skip).

    python test_facade_reader.py     (or: pytest test_facade_reader.py)
"""
import json
import os

import facade_reader as F
import zone_flag as Z

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))       # pipeline/scripts -> pipeline -> repo root

# ---- real sitting-room fixtures (verified coordinates, mm) ----------------------------
SITTING_OUTLINE = [[5750, 0], [10650, 0], [10650, 6250], [5750, 6250]]   # south edge y_s=0
XLO, XHI, YS = 5750.0, 10650.0, 0.0
EDGE = XHI - XLO                                        # 4900


def _run(axis, c, lo, hi, pieces=1, coverage=1.0):
    """A merged-run dict shaped exactly like glazing_candidates.merge_runs output."""
    return {"axis": axis, "c": float(c), "lo": float(lo), "hi": float(hi),
            "length": float(hi - lo), "pieces": pieces, "coverage": coverage}


# the real facade pair as merged runs: inner glass c=98.9, frame twin c=200 (101 mm apart)
FACADE_PAIR = [_run("h", 98.9, 5752.3, 10649.8), _run("h", 200.0, 5752.3, 10551.4)]


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ---- facade_band ----------------------------------------------------------------------
def test_facade_band_from_south_outline_edge():
    b = F.facade_band(SITTING_OUTLINE)
    assert approx(b["y_s"], 0.0) and approx(b["xlo"], 5750) and approx(b["xhi"], 10650)
    assert approx(b["band_lo"], -600.0) and approx(b["band_hi"], 300.0)   # 600 south / 300 north


# ---- open_edge_span -------------------------------------------------------------------
def test_open_edge_span_open_when_no_wall():
    walled, open_span = F.open_edge_span(YS, XLO, XHI, [])
    assert approx(walled, 0.0) and approx(open_span, EDGE)


def test_open_edge_span_walled_when_thick_wall_covers_edge():
    # a thick south wall decomposed into ~200 mm pieces still unions to full coverage
    wall = [[[x, 0], [x + 200, 0]] for x in range(5750, 10650, 200)]
    walled, open_span = F.open_edge_span(YS, XLO, XHI, wall)
    assert walled >= 0.99 and open_span <= EDGE * 0.01


# ---- classify_facade: the happy real-pair case ----------------------------------------
def test_classify_emits_single_inner_glass_line():
    cands = F.classify_facade(FACADE_PAIR, YS, XLO, XHI, [])
    assert len(cands) == 1                              # the pair collapses to ONE candidate
    c = cands[0]
    assert approx(c["c"], 98.9) and approx(c["pair_c"], 200.0)   # emits the inner (nearest-y_s) line
    assert c["tier"] == "glazed_facade" and c["score"] >= 4 and c["span_frac"] >= 0.9


# ---- adversarial: furniture double-line must NOT classify (headline defense) -----------
def test_furniture_double_line_rejected():
    # two 800 mm parallel h-runs ~100 mm apart, inside the band -- a bed/sofa outline twin
    furn = [_run("h", 50.0, 7000, 7800), _run("h", 150.0, 7000, 7800)]
    assert F.classify_facade(furn, YS, XLO, XHI, []) == []   # fails min_len AND span_frac


# ---- adversarial: the OUTER garden edge must be excluded by the band -------------------
def test_garden_edge_excluded_by_band():
    # the garden slab-lip pair DOES span + pair, but sits ~1150 mm south -> outside the 600 band.
    # (this pair would pass zone_flag.facade_corroborated's looser 1500 mm window.)
    garden = [_run("h", -1050.0, 3003.7, 10551.4), _run("h", -1151.6, 3003.7, 10751.4)]
    assert F.classify_facade(garden, YS, XLO, XHI, []) == []


# ---- adversarial: a walled-south room abstains ----------------------------------------
def test_walled_south_abstains_even_with_facade_ink():
    wall = [[[x, 0], [x + 200, 0]] for x in range(5750, 10650, 200)]   # >=0.6 coverage
    assert F.classify_facade(FACADE_PAIR, YS, XLO, XHI, wall) == []


# ---- adversarial: a lone spanning run (no pair) is not a facade ------------------------
def test_lone_run_without_pair_rejected():
    lone = [_run("h", 99.0, 5752.3, 10649.8)]
    assert F.classify_facade(lone, YS, XLO, XHI, []) == []


# ---- cap + rank + dedupe --------------------------------------------------------------
def test_cap_two_and_rank_by_distance_to_datum():
    # the facade pair (inner 98.9) plus a second in-band spanning pair further from y_s
    second = [_run("h", -300.0, 5752.3, 10649.8), _run("h", -400.0, 5752.3, 10649.8)]
    cands = F.classify_facade(FACADE_PAIR + second, YS, XLO, XHI, [])
    assert len(cands) == 2                              # capped, one per pair (deduped)
    assert approx(cands[0]["c"], 98.9) and approx(cands[1]["c"], -300.0)  # nearest-to-datum first


# ---- drop-in feed: a classify_facade candidate corroborates in zone_flag unchanged ----
def test_cluster_dedup_on_line_not_index_pair_and_no_eviction():
    # >=3 spanning runs clustered near the datum: the near-datum line is find_pair's mate for TWO
    # index-pairs. Dedup on the (i,mate) key would emit that ONE line twice and, under cap 2, EVICT
    # the real facade. Dedup on the emitted line must collapse it and keep the real 98.9 facade.
    cluster = [_run("h", -30, 5752, 10649), _run("h", 10, 5752, 10649), _run("h", 60, 5752, 10649)]
    only = F.classify_facade(cluster, YS, XLO, XHI, [])
    assert [c["c"] for c in only] == [10.0]                  # one physical line, emitted ONCE
    both = F.classify_facade(cluster + list(FACADE_PAIR), YS, XLO, XHI, [])
    cs = sorted(c["c"] for c in both)
    assert 98.9 in cs and len(both) == len(set(c["c"] for c in both))   # real facade survives; no dup


def test_candidate_is_dropin_feed_for_zone_flag():
    cand = F.classify_facade(FACADE_PAIR, YS, XLO, XHI, [])[0]
    ok, ev = Z.facade_corroborated(YS, XLO, XHI, [cand], [])
    assert ok is True and approx(ev["glazing_c"], cand["c"])


# ---- facade_candidates orchestrator: per-room tagging ---------------------------------
def test_facade_candidates_tags_room_and_counts():
    # raw thin segs for the facade pair (two long h fragments) + a short furniture twin
    thin = [[[5752.3, 98.9], [10649.8, 98.9]], [[5752.3, 200.0], [10551.4, 200.0]],
            [[7000, 50], [7800, 50]], [[7000, 150], [7800, 150]]]
    cands, per_room = F.facade_candidates(thin, [], [("sitting_room", SITTING_OUTLINE)])
    assert per_room == {"sitting_room": 1}
    assert len(cands) == 1 and cands[0]["room"] == "sitting_room" and approx(cands[0]["c"], 98.9)


def test_malformed_outline_scans_nothing_never_crashes():
    cands, per_room = F.facade_candidates([], [], [("bad", [[1, 2]])])   # <3 points
    assert cands == [] and per_room == {"bad": 0}


# ---- PRODUCTION REPLAY: the real PDF, non-circular ------------------------------------
def _find(*rels):
    for r in rels:
        p = os.path.join(_REPO, r)
        if os.path.exists(p):
            return p
    return None


def test_real_pdf_surfaces_facade_not_garden():
    """Read RAW thin ink off the real sheet, band-filter the real sitting room, and assert the
    reader surfaces the c~=99 glass line (NOT the c~=-1151 garden edge), a HANDFUL not 298.
    Skips cleanly without PyMuPDF / the real files (repo convention)."""
    try:
        import fitz  # noqa: F401
    except Exception:
        return
    pdf = _find("projects/PRJ-2026-002_c001-house/00_intake/raw-local/"
                "The City สาทร - สุขสวัสดิ์_Plan funiture 02.pdf")
    walls = _find("projects/PRJ-2026-002_c001-house/03_layout/v4/floor2-walls-mm.json",
                  "projects/PRJ-2026-002_c001-house/03_layout/floor2-walls-mm.json")
    if not pdf or not walls:
        return
    meta = json.load(open(walls, encoding="utf-8"))
    scale, (x0, y0), page = meta["scale_mm_per_pt"], meta["origin_pt"], meta["page"]
    wall_segs = [s for s in meta.get("segments", []) if F._valid_seg(s)]
    thin = F.extract_thin(pdf, page, scale, x0, y0)
    cands, per_room = F.facade_candidates(thin, wall_segs, [("sitting_room", SITTING_OUTLINE)])
    assert per_room["sitting_room"] <= 2, f"noisy: {per_room}"         # a HANDFUL, not 298
    assert cands, "facade not found on the real sheet"
    top = cands[0]
    assert -50 <= top["c"] <= 300, f"expected the facade near y_s not the garden, got c={top['c']}"
    assert top["span_frac"] >= 0.7 and top["length_mm"] >= 2000
    assert top["c"] > -600, "surfaced the garden slab-lip, not the facade"


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed")
