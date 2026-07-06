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


# ---- identity binding: DOUBLE-CLAIM only (two pieces on one drawn cluster) ------------
def test_identity_double_claim_keys_on_matched_not_claim():
    # two pieces best-overlap the SAME drawn cluster while recording DIFFERENT stale claims;
    # the flag must key on the MATCHED cluster's id (5), proving it ignores the volatile claim.
    clusters = [_c(100, 100, 400, 400, i=5)]
    loose = [{"x": 100, "y": 100, "w": 400, "d": 400, "kind": "sofa", "name": "a", "cluster": 5},
             {"x": 100, "y": 100, "w": 400, "d": 400, "kind": "sofa", "name": "b", "cluster": 99}]
    loose_r = [G.classify_item(it, clusters, lambda fp: 0, BIG) for it in loose]
    flags = G.identity_check(loose, loose_r, clusters)
    assert flags == [{"type": "double_claim", "cluster": 5, "names": ["a", "b"]}], flags


def test_identity_double_claim_fires_on_drift_status():
    # two DRIFT-status pieces (partial overlap) on one cluster still count -> covers the drift branch
    clusters = [_c(0, 0, 400, 600, i=7)]
    loose = [{"x": 200, "y": 0, "w": 400, "d": 600, "kind": "sofa", "name": "a"},
             {"x": 200, "y": 0, "w": 400, "d": 600, "kind": "sofa", "name": "b"}]
    loose_r = [G.classify_item(it, clusters, lambda fp: 0, BIG) for it in loose]
    assert all(r["status"] == "drift" for r in loose_r), loose_r
    assert G.identity_check(loose, loose_r, clusters) == [{"type": "double_claim", "cluster": 7, "names": ["a", "b"]}]


def test_identity_no_dup_when_pieces_on_different_clusters():
    clusters = [_c(100, 100, 400, 400, i=5), _c(3000, 3000, 400, 400, i=8)]
    loose = [{"x": 100, "y": 100, "w": 400, "d": 400, "kind": "sofa", "name": "a"},
             {"x": 3000, "y": 3000, "w": 400, "d": 400, "kind": "sofa", "name": "b"}]
    loose_r = [G.classify_item(it, clusters, lambda fp: 0, BIG) for it in loose]
    assert G.identity_check(loose, loose_r, clusters) == []


def test_identity_ignores_floating():
    # a floating piece (no cluster overlap) is not counted toward a double-claim
    clusters = [_c(100, 100, 400, 400, i=5)]
    loose = [{"x": 9000, "y": 9000, "w": 400, "d": 400, "kind": "sofa", "name": "float"},
             {"x": 100, "y": 100, "w": 400, "d": 400, "kind": "sofa", "name": "ok"}]
    loose_r = [G.classify_item(it, clusters, lambda fp: 0, BIG) for it in loose]
    assert G.identity_check(loose, loose_r, clusters) == []


# ---- dismissals ledger (one-to-one, scaled tol, shape guards) ------------------------
def test_sig_match_center_and_size():
    c = _c(6254, 5350, 894, 948)
    assert G._sig_match(c, {"x": 6260, "y": 5340, "w": 890, "d": 950})       # near + same size
    assert not G._sig_match(c, {"x": 3000, "y": 3000, "w": 894, "d": 948})   # far centre
    assert not G._sig_match(c, {"x": 6254, "y": 5350, "w": 400, "d": 400})   # wrong size


def test_sig_match_size_isolated():
    # SAME centre, size far over the scaled tolerance -> must NOT match (size alone discriminates)
    c = _c(6250, 5350, 900, 900)                          # centre (6700,5800)
    entry = {"x": 5300, "y": 4400, "w": 2800, "d": 2800}  # SAME centre (6700,5800), far bigger
    assert not G._sig_match(c, entry), "size must reject even with an identical centre"


def test_sig_match_curve_discriminator():
    door = _c(6254, 5350, 894, 948, curve=False)                       # rectilinear door swing
    entry = {"x": 6254, "y": 5350, "w": 894, "d": 948, "curve": True}  # organic dismissal
    assert not G._sig_match(door, entry), "a curve/organic mismatch must not match"


def test_sig_match_missing_key_is_no_match_not_crash():
    c = _c(6254, 5350, 894, 948)
    assert G._sig_match(c, {"y": 5350, "w": 894, "d": 948}) is False   # missing 'x' -> skip, no crash


def test_apply_dismissals_splits():
    unplaced = [{"id": 2, "x": 6254, "y": 5350, "w": 894, "d": 948, "area_m2": 0.06, "curve": False},
                {"id": 36, "x": -132, "y": -574, "w": 390, "d": 1074, "area_m2": 0.14, "curve": True}]
    ledger = [{"x": 6254, "y": 5350, "w": 894, "d": 948, "reason": "door swing", "by": "owner"}]
    kept, dismissed = G.apply_dismissals(unplaced, ledger)
    assert [c["id"] for c in kept] == [36], kept
    assert [c["id"] for c in dismissed] == [2] and dismissed[0]["reason"] == "door swing", dismissed


def test_apply_dismissals_one_entry_dismisses_one_cluster():
    # a genuine furniture cluster (id7) sitting NEAR the dismissed door must SURVIVE (stay unplaced),
    # not be silenced by the single door dismissal -> the cardinal completeness guarantee.
    door = {"id": 2, "x": 6254, "y": 5350, "w": 894, "d": 948, "curve": False}
    near = {"id": 7, "x": 6300, "y": 5400, "w": 900, "d": 900, "curve": False}
    ledger = [{"x": 6254, "y": 5350, "w": 894, "d": 948, "reason": "door", "by": "o"}]
    kept, dismissed = G.apply_dismissals([door, near], ledger)
    assert [c["id"] for c in dismissed] == [2], dismissed        # only the nearest (the door)
    assert [c["id"] for c in kept] == [7], kept                  # the real piece stays flagged


def test_gate_dismissed_unplaced_does_not_review():
    clusters = [_c(100, 200, 400, 600, i=1), _c(3000, 3000, 700, 700, i=2)]
    loose = [{"x": 100, "y": 200, "w": 400, "d": 600, "kind": "sofa", "name": "x"}]
    ledger = [{"x": 3000, "y": 3000, "w": 700, "d": 700, "reason": "label", "by": "t"}]
    r = G.gate(loose=loose, fixed=[], clusters=clusters, ink_count=lambda fp: 0, zone=BIG, dismissed=ledger)
    assert r["verdict"] == "PASS", r
    assert len(r["dismissed"]) == 1 and r["unplaced"] == [], r


# ---- merged-blob completeness (a fused region must surface, not silently drop) --------
def test_gate_merged_blob_drives_review_and_is_dismissable():
    clusters = [_c(100, 200, 400, 600, i=1)]
    loose = [{"x": 100, "y": 200, "w": 400, "d": 600, "kind": "sofa", "name": "x"}]
    dropped = [{"reason": "merged_blob", "x": 0, "y": 0, "w": 5000, "d": 6000, "area_m2": 3.0, "fill": 0.07}]
    r = G.gate(loose=loose, fixed=[], clusters=clusters, ink_count=lambda fp: 0, zone=BIG, dropped=dropped)
    assert r["verdict"] == "REVIEW" and len(r["merged"]) == 1, r      # surfaced, not silently dropped
    ledger = [{"x": 0, "y": 0, "w": 5000, "d": 6000, "reason": "linework", "by": "o"}]
    r2 = G.gate(loose=loose, fixed=[], clusters=clusters, ink_count=lambda fp: 0, zone=BIG,
                dropped=dropped, dismissed=ledger)
    assert r2["verdict"] == "PASS" and r2["merged"] == [] and len(r2["dismissed"]) == 1, r2


# ---- calibration hard-check (needs a LONG wall at the line; coincidence-proof) --------
def test_check_wall_grid_pass_with_long_walls():
    segs = [[[0, 0], [0, 3000]], [[10600, 0], [10600, 3000]], [[0, 0], [5000, 0]]]
    checks = [{"axis": "x", "mm": 0, "tol_mm": 100}, {"axis": "x", "mm": 10600, "tol_mm": 150},
              {"axis": "y", "mm": 0, "tol_mm": 100}]
    assert G.check_wall_grid(segs, checks) == []


def test_check_wall_grid_fails_when_line_offset():
    segs = [[[200, 0], [200, 3000]]]     # long wall, but 200mm off x=0 (tol 100)
    fails = G.check_wall_grid(segs, [{"axis": "x", "mm": 0, "tol_mm": 100}])
    assert len(fails) == 1 and fails[0]["found_long_wall"] is False, fails


def test_check_wall_grid_rejects_short_coincidental_wall():
    # a SHORT wall exactly at the line must NOT satisfy it (this is the coincidence-proofing)
    segs = [[[0, 0], [0, 500]]]           # only 500mm long, < default min_len 1500
    fails = G.check_wall_grid(segs, [{"axis": "x", "mm": 0, "tol_mm": 100}])
    assert len(fails) == 1, fails


def test_check_wall_grid_empty_fails():
    segs = [[[0, 0], [5000, 0]]]          # only horizontal -> no vertical wall for an x check
    fails = G.check_wall_grid(segs, [{"axis": "x", "mm": 0, "tol_mm": 100}])
    assert len(fails) == 1, fails


def test_check_wall_grid_catches_gross_scale_error():
    # correct -> pass; +5% scaled -> the x=10600 long wall moves to 11130, none within tol -> FAIL
    walls = [[[0, 0], [0, 4000]], [[10600, 0], [10600, 4000]]]
    checks = [{"axis": "x", "mm": 10600, "tol_mm": 120}]
    assert G.check_wall_grid(walls, checks) == []
    scaled = [[[a[0] * 1.05, a[1] * 1.05], [b[0] * 1.05, b[1] * 1.05]] for (a, b) in walls]
    assert len(G.check_wall_grid(scaled, checks)) == 1, "a gross +5% scale must be caught"


def test_check_wall_grid_nearer_endpoint_passes():
    # a long, slightly non-axis-aligned wall touching x=0 at ONE end (other end 250mm off) must
    # PASS via the nearer endpoint -- pins min(), not max(), endpoint semantics.
    segs = [[[0, 0], [250, 4000]]]
    assert G.check_wall_grid(segs, [{"axis": "x", "mm": 0, "tol_mm": 120}]) == []


def test_check_wall_grid_missing_mm_is_skipped():
    segs = [[[0, 0], [0, 4000]]]
    assert G.check_wall_grid(segs, [{"axis": "x"}]) == []          # no 'mm' -> ignore, not crash/fail


def test_check_wall_grid_skips_malformed_segment():
    segs = [[1, 2, 3, 4], [[0, 0], [0, 4000]]]                     # garbage then a real x=0 wall
    assert G.check_wall_grid(segs, [{"axis": "x", "mm": 0, "tol_mm": 100}]) == []


def test_sig_match_proportional_tol_is_load_bearing():
    # a LARGE dismissal (3000mm) whose centre is 200mm off matches ONLY because tol scales to size
    # (0.15*3000=450 > 200); the same 200mm offset on a SMALL entry is rejected by the 120 floor.
    assert G._sig_match(_c(0, 0, 3000, 3000), {"x": 200, "y": 0, "w": 3000, "d": 3000})
    assert not G._sig_match(_c(0, 0, 400, 400), {"x": 200, "y": 0, "w": 400, "d": 400})


def test_apply_dismissals_skips_non_dict_entries():
    unplaced = [{"id": 2, "x": 6254, "y": 5350, "w": 894, "d": 948, "curve": False}]
    ledger = [None, "oops", 123, {"x": 6254, "y": 5350, "w": 894, "d": 948, "reason": "door"}]
    kept, dismissed = G.apply_dismissals(unplaced, ledger)        # junk entries must not crash
    assert [c["id"] for c in dismissed] == [2], dismissed


def test_facing_flags_surfaces_ambiguous_180():
    # a bed whose only strip is on the claimed-FRONT edge -> facing_flags SURFACES it (soft),
    # so the commonest (180-deg) facing error is not silently passed.
    rect = [[[0, 0], [2000, 0]], [[2000, 0], [2000, 2100]],
            [[2000, 2100], [0, 2100]], [[0, 2100], [0, 0]]]
    strip = [[[90, 260], [1910, 260]]]                           # strip ~260mm above the S edge
    bed = {"x": 0, "y": 0, "w": 2000, "d": 2100, "kind": "bed", "rot": 0, "name": "bed"}
    flags = G.facing_flags([bed], rect + strip)
    assert len(flags) == 1 and flags[0]["verdict"] == "ambiguous", flags


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} placement_gate tests passed")
