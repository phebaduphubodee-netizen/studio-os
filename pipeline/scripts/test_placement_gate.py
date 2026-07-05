"""
test_placement_gate.py — unit tests for the PURE gate logic (no PDF needed).

Covers the footprint rotation math (the subtle rot-swap that silently offsets every
check if wrong), IoU, per-item classification for all states incl. the centroid-outside-
zone guard, strictness-by-KIND (a free-standing piece floats-and-FAILs even inside
builtins[]; a wall unit inside items[] does NOT hard-fail), the unplaced-cluster
completeness scan, and the room verdict. The PDF-backed run() is exercised on real data.

    python test_placement_gate.py
"""
import placement_gate as G

BIG = (-1e7, -1e7, 1e7, 1e7)     # a zone that always contains the footprint centroid


def approx(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def _c(x, y, w, d, area=None, curve=False, i=1):
    return {"id": i, "x": x, "y": y, "w": w, "d": d,
            "area_m2": area if area is not None else round(w * d / 1e6, 3), "curve": curve}


# ---- footprint / iou -----------------------------------------------------------------
def test_footprint_norot():
    fp = G.footprint({"x": 100, "y": 200, "w": 400, "d": 600})
    assert approx(fp, (100, 200, 500, 800)), fp


def test_footprint_rot270_swaps_axes():
    fp = G.footprint({"x": 3095, "y": 125, "w": 2140, "d": 1970, "rot": 270})
    assert approx(fp, (3180, 40, 5150, 2180)), fp
    ew, ns = fp[2] - fp[0], fp[3] - fp[1]
    assert approx((ew, ns), (1970, 2140)), (ew, ns)


def test_footprint_diagonal_bbox_grows():
    fp = G.footprint({"x": 0, "y": 0, "w": 1000, "d": 200, "rot": 45})
    ew, ns = fp[2] - fp[0], fp[3] - fp[1]
    exp = (1000 + 200) / (2 ** 0.5)
    assert approx((ew, ns), (exp, exp)), (ew, ns, exp)


def test_footprint_offset():
    fp = G.footprint({"x": 0, "y": 0, "w": 200, "d": 200}, offset=(1000, -500))
    assert approx(fp, (1000, -500, 1200, -300)), fp


def test_iou():
    a = (0, 0, 400, 600)
    assert G.iou(a, a) == 1.0
    assert G.iou(a, (1000, 1000, 1400, 1600)) == 0.0
    assert abs(G.iou(a, (200, 0, 600, 600)) - 1 / 3) < 1e-6


# ---- classify_item -------------------------------------------------------------------
def test_classify_matched():
    r = G.classify_item({"x": 100, "y": 200, "w": 400, "d": 600, "kind": "sofa"},
                        [_c(100, 200, 400, 600)], lambda fp: 0, BIG)
    assert r["status"] == "matched", r


def test_classify_drift():
    r = G.classify_item({"x": 0, "y": 0, "w": 400, "d": 600, "kind": "sofa"},
                        [_c(200, 0, 400, 600)], lambda fp: 0, BIG)
    assert r["status"] == "drift", r


def test_classify_floating_when_no_ink():
    r = G.classify_item({"x": 0, "y": 0, "w": 400, "d": 600, "kind": "sofa"},
                        [], lambda fp: 0, BIG, strict=True)
    assert r["status"] == "floating", r


def test_classify_on_ink_when_ink_present():
    r = G.classify_item({"x": 0, "y": 0, "w": 400, "d": 600, "kind": "sofa"},
                        [], lambda fp: 100, BIG, strict=True)
    assert r["status"] == "on_ink", r


def test_classify_lenient_never_floats():
    r = G.classify_item({"x": 0, "y": 0, "w": 400, "d": 600, "kind": "wardrobe"},
                        [], lambda fp: 0, BIG, strict=False)
    assert r["status"] == "unverified", r


def test_classify_outside_zone_is_unverified_not_floating():
    # a strict piece whose centroid is outside the rasterised zone must NOT hard-fail
    zone = (0, 0, 5000, 5000)
    r = G.classify_item({"x": 9000, "y": 9000, "w": 400, "d": 600, "kind": "sofa"},
                        [], lambda fp: 0, zone, strict=True)
    assert r["status"] == "unverified", r


# ---- unplaced completeness -----------------------------------------------------------
def test_unplaced_flags_big_uncovered_only():
    item_fp = G.footprint({"x": 0, "y": 0, "w": 400, "d": 600})
    clusters = [_c(0, 0, 400, 600, i=1),
                _c(2000, 2000, 600, 800, i=2),
                _c(5000, 5000, 100, 100, i=3)]
    up = G.unplaced_clusters(clusters, [item_fp])
    assert [c["id"] for c in up] == [2], up


# ---- gate verdict (strictness by KIND, not by array) ---------------------------------
def test_gate_fail_on_floating_loose():
    r = G.gate(loose=[{"x": 9000, "y": 9000, "w": 400, "d": 600, "kind": "sofa", "name": "floater"}],
               fixed=[], clusters=[], ink_count=lambda fp: 0, zone=(8000, 8000, 10000, 10000))
    assert r["verdict"] == "FAIL", r


def test_gate_fail_on_floating_furniture_in_builtins():
    # a bed mis-sorted into builtins[] must still FAIL if it floats (kind-based strictness)
    r = G.gate(loose=[], fixed=[{"x": 100, "y": 100, "w": 2000, "d": 1900, "kind": "bed", "name": "ghost bed"}],
               clusters=[], ink_count=lambda fp: 0, zone=(-100, -100, 5000, 5000))
    assert r["verdict"] == "FAIL", r


def test_gate_wallkind_in_items_does_not_fail():
    # a wall wardrobe placed in items[] with no cluster/ink is UNVERIFIED (REVIEW), not FAIL
    r = G.gate(loose=[{"x": 100, "y": 100, "w": 600, "d": 2600, "kind": "wardrobe", "name": "wall wd"}],
               fixed=[], clusters=[], ink_count=lambda fp: 0, zone=(-100, -100, 5000, 5000))
    assert r["verdict"] == "REVIEW", r


def test_gate_pass_when_all_matched():
    r = G.gate(loose=[{"x": 100, "y": 200, "w": 400, "d": 600, "kind": "sofa", "name": "x"}],
               fixed=[], clusters=[_c(100, 200, 400, 600)], ink_count=lambda fp: 0, zone=BIG)
    assert r["verdict"] == "PASS", r


def test_gate_review_on_drift():
    r = G.gate(loose=[{"x": 0, "y": 0, "w": 400, "d": 600, "kind": "sofa", "name": "x"}],
               fixed=[], clusters=[_c(200, 0, 400, 600)], ink_count=lambda fp: 0, zone=BIG)
    assert r["verdict"] == "REVIEW", r


def test_gate_review_on_unplaced_even_if_items_ok():
    r = G.gate(loose=[{"x": 100, "y": 200, "w": 400, "d": 600, "kind": "sofa", "name": "x"}],
               fixed=[],
               clusters=[_c(100, 200, 400, 600, i=1), _c(3000, 3000, 700, 700, i=2)],
               ink_count=lambda fp: 0, zone=BIG)
    assert r["verdict"] == "REVIEW", r
    assert [c["id"] for c in r["unplaced"]] == [2], r["unplaced"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} placement_gate tests passed")
