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


# ---- semantic-truth ledger: owner-signed facings persist + suppress the gate flag ----
def test_confirmed_facing_matches_by_name():
    bed = {"name": "เตียง", "w": 1650, "d": 2090}
    conf = [{"room": "master", "name": "เตียง", "facing": "W", "by": "owner", "date": "2026-07-06"}]
    assert G.confirmed_facing(bed, conf) == "W"


def test_confirmed_facing_none_when_name_differs():
    assert G.confirmed_facing({"name": "sofa"}, [{"name": "bed", "facing": "W"}]) is None


def test_confirmed_facing_size_guard_rejects_reused_name():
    # a confirmed entry sized for a small stool must NOT attach to a big bed that reused the name
    bed = {"name": "x", "w": 1650, "d": 2090}
    assert G.confirmed_facing(bed, [{"name": "x", "facing": "W", "w": 500, "d": 500}]) is None


def test_confirmed_facing_no_size_on_entry_still_matches():
    assert G.confirmed_facing({"name": "x", "w": 1650, "d": 2090}, [{"name": "x", "facing": "N"}]) == "N"


def test_load_confirmed_drops_non_dicts():
    led = {"confirmed": [{"name": "b", "facing": "W"}, None, "oops", 7]}
    got = G.load_confirmed(led)
    assert len(got) == 1 and got[0]["name"] == "b", got


def test_load_confirmed_tolerates_missing_or_malformed():
    assert G.load_confirmed({}) == []
    assert G.load_confirmed({"confirmed": "nope"}) == []
    assert G.load_confirmed(None) == []


def test_facing_flag_suppressed_once_owner_signs():
    # the SAME fixture that flags 'ambiguous' above must go SILENT once the owner signs the facing
    rect = [[[0, 0], [2000, 0]], [[2000, 0], [2000, 2100]],
            [[2000, 2100], [0, 2100]], [[0, 2100], [0, 0]]]
    strip = [[[90, 260], [1910, 260]]]
    bed = {"x": 0, "y": 0, "w": 2000, "d": 2100, "kind": "bed", "rot": 0, "name": "bed"}
    signed = [{"room": "*", "name": "bed", "facing": "S", "w": 2000, "d": 2100, "by": "owner", "date": "2026-07-06"}]
    assert G.facing_flags([bed], rect + strip, confirmed=signed) == []
    # and without the signature it still flags (the suppression is what changed, not the read)
    assert len(G.facing_flags([bed], rect + strip)) == 1


def test_facing_flag_contradicting_sign_is_raised_not_suppressed():
    # signing the OPPOSITE of the BUILT rot must NOT silence the flag — catching that regression
    # (a rebuild re-rolled the rot away from the owner's signed truth) is the ledger's whole point.
    rect = [[[0, 0], [2000, 0]], [[2000, 0], [2000, 2100]],
            [[2000, 2100], [0, 2100]], [[0, 2100], [0, 0]]]
    strip = [[[90, 260], [1910, 260]]]
    bed = {"x": 0, "y": 0, "w": 2000, "d": 2100, "kind": "bed", "rot": 0, "name": "bed"}   # rot0 -> faces S
    signed_opp = [{"room": "*", "name": "bed", "facing": "N", "w": 2000, "d": 2100}]        # owner signed N
    flags = G.facing_flags([bed], rect + strip, confirmed=signed_opp)
    assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags
    assert flags[0]["claimed"] == "S" and flags[0]["read"] == "N", flags


def test_confirmed_facing_rejects_non_cardinal_typo():
    # a truthy-but-non-cardinal sign ('south','n','N ',180,'') must NOT suppress — the generator's
    # rot_from_facing would apply nothing, so the two ledger consumers would silently disagree.
    bed = {"name": "bed", "w": 2000, "d": 2100}
    for bad in ("south", "n", "N ", 180, "", None):
        assert G.confirmed_facing(bed, [{"name": "bed", "facing": bad}]) is None, bad
    assert G.confirmed_facing(bed, [{"name": "bed", "facing": "N"}]) == "N"   # a real cardinal matches


# ---- rot-aware ledger (non-cardinal facings, e.g. angled terrace chairs) --------------
def test_confirmed_rot_cardinal_facing_letter():
    for letter, rot in (("S", 0), ("E", 90), ("N", 180), ("W", 270)):
        assert G.confirmed_rot({"name": "x"}, [{"name": "x", "facing": letter}]) == rot, letter


def test_confirmed_rot_numeric_non_cardinal():
    # the tub chairs the cardinal ledger could NOT express (rot 12 / 335)
    assert G.confirmed_rot({"name": "c", "w": 680, "d": 640}, [{"name": "c", "rot": 12}]) == 12
    assert G.confirmed_rot({"name": "c", "w": 680, "d": 640}, [{"name": "c", "rot": 335}]) == 335


def test_confirmed_rot_rounds_and_wraps():
    assert G.confirmed_rot({"name": "c"}, [{"name": "c", "rot": 359.6}]) == 0      # rounds -> 360 -> 0
    assert G.confirmed_rot({"name": "c"}, [{"name": "c", "rot": -25}]) == 335      # wraps
    assert G.confirmed_rot({"name": "c"}, [{"name": "c", "rot": 11.7}]) == 12      # rounds to nearest deg


def test_confirmed_rot_numeric_beats_facing_letter():
    assert G.confirmed_rot({"name": "c"}, [{"name": "c", "facing": "S", "rot": 12}]) == 12


def test_confirmed_rot_malformed_rot_falls_back_to_facing():
    assert G.confirmed_rot({"name": "c"}, [{"name": "c", "facing": "E", "rot": "oops"}]) == 90
    # ...and with no usable facing either -> None (nothing applied)
    assert G.confirmed_rot({"name": "c"}, [{"name": "c", "rot": "oops"}]) is None


def test_confirmed_rot_typo_facing_no_rot_is_none():
    for bad in ("south", "n", "N ", 180, "", None):
        assert G.confirmed_rot({"name": "c"}, [{"name": "c", "facing": bad}]) is None, bad


def test_confirmed_rot_size_guard():
    # a stale entry sized for a stool must NOT re-orient a big chair that reused the name
    assert G.confirmed_rot({"name": "c", "w": 680, "d": 640},
                           [{"name": "c", "rot": 12, "w": 300, "d": 300}]) is None


def test_confirmed_rot_typo_then_correction_not_shadowed():
    # the owner signs a TYPO, then APPENDS the valid correction with the same name+size. confirmed_rot
    # must scan PAST the unusable first entry to the correction (mirrors confirmed_facing), else the
    # signature is silently dropped in BOTH the gate and the generator — the regression the ledger exists
    # to catch. Covers both a bad facing letter and a malformed numeric rot as the shadowing entry.
    piece = {"name": "bed", "w": 2000, "d": 1800}
    assert G.confirmed_rot(piece, [{"name": "bed", "facing": "bogus", "w": 2000, "d": 1800},
                                   {"name": "bed", "facing": "N", "w": 2000, "d": 1800}]) == 180
    assert G.confirmed_rot(piece, [{"name": "bed", "rot": "junk", "w": 2000, "d": 1800},
                                   {"name": "bed", "rot": 335, "w": 2000, "d": 1800}]) == 335
    # generator + gate both honour the correction (single source): resolve_rot applies it, and a build
    # that contradicts the correction is raised rather than silently dropped.
    conf = [{"name": "bed", "facing": "bogus", "w": 2000, "d": 1800},
            {"name": "bed", "facing": "N", "w": 2000, "d": 1800}]
    assert G.resolve_rot("bed", 0, 2000, 1800, conf) == (180, "owner-signed")
    built_S = {"x": 0, "y": 0, "w": 2000, "d": 1800, "kind": "bed", "rot": 0, "name": "bed"}
    flags = G.facing_flags([built_S], [], confirmed=conf)
    assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags
    # ...and no matching entry yields a usable rot -> None (unchanged)
    assert G.confirmed_rot(piece, [{"name": "bed", "facing": "bogus", "w": 2000, "d": 1800},
                                   {"name": "bed", "rot": "junk", "w": 2000, "d": 1800}]) is None


def test_facing_flags_signed_backstop_survives_missing_facing_reader():
    # the owner-signed contradiction backstop is pure rot arithmetic (confirmed_rot/_norm_rot) and MUST
    # NOT be disabled when facing_reader is unimportable — only the geometric strip-read + cardinal-letter
    # labels depend on it. Simulate the missing module (sys.modules[name]=None -> import raises).
    import sys
    signed = [{"name": "bed", "facing": "N", "w": 2000, "d": 2100}]   # N(180) vs built 0(S)
    bed = {"x": 0, "y": 0, "w": 2000, "d": 2100, "kind": "bed", "rot": 0, "name": "bed"}
    saved = sys.modules.get("facing_reader")
    sys.modules["facing_reader"] = None
    try:
        flags = G.facing_flags([bed], [], confirmed=signed)
        assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags
        assert flags[0]["read"] == "rot180" and flags[0]["claimed"] == "rot0", flags  # labels degrade to deg
        # a MATCHING sign still suppresses without FR
        ok = dict(bed, rot=180)
        assert G.facing_flags([ok], [], confirmed=signed) == []
    finally:
        if saved is not None:
            sys.modules["facing_reader"] = saved
        else:
            del sys.modules["facing_reader"]


def test_resolve_rot_no_ledger_is_handrot():
    assert G.resolve_rot("c", 90, 680, 640, []) == (90, None)
    assert G.resolve_rot("c", 90, 680, 640, None) == (90, None)


def test_resolve_rot_signed_overrides_incl_non_cardinal():
    assert G.resolve_rot("c", 90, 680, 640, [{"name": "c", "facing": "W"}]) == (270, "owner-signed")
    assert G.resolve_rot("c", 12, 680, 640, [{"name": "c", "rot": 335}]) == (335, "owner-signed")


def test_resolve_rot_agreeing_sign_still_tagged():
    assert G.resolve_rot("c", 12, 680, 640, [{"name": "c", "rot": 12}]) == (12, "owner-signed")


def test_facing_flags_non_cardinal_sign_suppressed_when_built_matches():
    # an angled armchair built at rot 12 with an owner sign of rot 12 -> no flag (adjudicated)
    chair = {"x": 0, "y": 0, "w": 680, "d": 640, "kind": "armchair", "rot": 12, "name": "tub L"}
    signed = [{"name": "tub L", "rot": 12, "w": 680, "d": 640}]
    assert G.facing_flags([chair], [], confirmed=signed) == []
    # DISCRIMINATOR: prove the suppression is because the SIGNED branch ran, not because empty fsegs
    # mask everything for a facing kind. The SAME piece with a CONTRADICTING sign must raise; if a
    # regression made the sign silently stop matching (confirmed_rot -> None), this would fall through
    # to the empty-fsegs geometric read and wrongly return [] -> this assertion catches that.
    contra = [{"name": "tub L", "rot": 90, "w": 680, "d": 640}]
    f = G.facing_flags([chair], [], confirmed=contra)
    assert len(f) == 1 and f[0]["verdict"] == "contradicts_signed", f


def test_facing_flags_non_cardinal_contradiction_raised():
    # built at rot 12 but the owner signed rot 335 -> contradicts_signed (rot-space), read shows the deg
    chair = {"x": 0, "y": 0, "w": 680, "d": 640, "kind": "armchair", "rot": 12, "name": "tub L"}
    signed = [{"name": "tub L", "rot": 335, "w": 680, "d": 640}]
    flags = G.facing_flags([chair], [], confirmed=signed)
    assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags
    assert flags[0]["claimed"] == "rot12" and flags[0]["read"] == "rot335", flags


def test_facing_flags_malformed_built_rot_never_suppresses_a_sign():
    # a MALFORMED built rot (null/garbage) must NOT be coerced to 0(=S) and silently 'match' an S sign.
    # A garbage orientation cannot be shown to agree with the owner's sign -> contradicts_signed.
    signed_S = [{"name": "bed", "facing": "S", "w": 2000, "d": 2100}]
    for bad in (None, "oops"):
        bed = {"x": 0, "y": 0, "w": 2000, "d": 2100, "kind": "bed", "rot": bad, "name": "bed"}
        flags = G.facing_flags([bed], [], confirmed=signed_S)
        assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", (bad, flags)
        assert flags[0]["claimed"] is None, (bad, flags)   # honest: the built rot is unreadable
    # a genuine rot 0 STILL suppresses on an S sign (the legit case is unaffected)
    ok = {"x": 0, "y": 0, "w": 2000, "d": 2100, "kind": "bed", "rot": 0, "name": "bed"}
    assert G.facing_flags([ok], [], confirmed=signed_S) == []


def test_facing_flags_signed_NON_facing_kind_is_verified():
    # the generator applies a sign to ANY kind, so the gate must verify ANY kind. A signed side_table
    # (NOT a _FACING_KIND) whose built rot contradicts the sign must be flagged, not silently skipped.
    tbl = {"x": 0, "y": 0, "w": 400, "d": 600, "kind": "side_table", "rot": 0, "name": "console"}
    signed = [{"name": "console", "facing": "E", "w": 400, "d": 600}]   # E(90) vs built 0(S)
    flags = G.facing_flags([tbl], [], confirmed=signed)
    assert len(flags) == 1 and flags[0]["verdict"] == "contradicts_signed", flags
    # ...and when the sign matches the build, it is adjudicated (suppressed)
    tbl_ok = dict(tbl, rot=90)
    assert G.facing_flags([tbl_ok], [], confirmed=signed) == []
    # an UNSIGNED non-facing kind is still ignored (no geometric strip read for it)
    assert G.facing_flags([dict(tbl, name="unsigned")], []) == []


# ---- reconcile_confirmed (orphan detection: the silent-detachment backstop) -----------
def test_reconcile_all_matched():
    pieces = [{"name": "chair L", "kind": "armchair", "w": 680, "d": 640, "rot": 8},
              {"name": "chair R", "kind": "armchair", "w": 660, "d": 640, "rot": 332}]
    confirmed = [{"name": "chair L", "rot": 8, "w": 680, "d": 640},
                 {"name": "chair R", "rot": 332, "w": 660, "d": 640}]
    matched, orphaned = G.reconcile_confirmed(pieces, confirmed)
    assert len(matched) == 2 and orphaned == [], (matched, orphaned)


def test_reconcile_rename_orphans_the_sign():
    # the owner signed 'chair L' but the generator renamed the piece -> the sign binds to nothing
    pieces = [{"name": "lounge chair (renamed)", "kind": "armchair", "w": 680, "d": 640, "rot": 8}]
    confirmed = [{"name": "chair L", "rot": 8, "w": 680, "d": 640}]
    matched, orphaned = G.reconcile_confirmed(pieces, confirmed)
    assert matched == [] and len(orphaned) == 1 and orphaned[0]["name"] == "chair L", (matched, orphaned)


def test_reconcile_size_edit_orphans_the_sign():
    # same name, but the piece was resized beyond tol -> the size guard detaches the stale sign
    pieces = [{"name": "chair L", "kind": "armchair", "w": 300, "d": 300, "rot": 8}]
    confirmed = [{"name": "chair L", "rot": 8, "w": 680, "d": 640}]
    _matched, orphaned = G.reconcile_confirmed(pieces, confirmed)
    assert len(orphaned) == 1, orphaned


def test_reconcile_sizeless_sign_matches_on_name():
    # a cardinal sign carrying no w/d must NOT false-orphan (the size guard is a no-op) -> name match
    pieces = [{"name": "sofa", "kind": "sofa", "w": 1000, "d": 2200, "rot": 90}]
    confirmed = [{"name": "sofa", "facing": "W"}]
    matched, orphaned = G.reconcile_confirmed(pieces, confirmed)
    assert len(matched) == 1 and orphaned == [], (matched, orphaned)


def test_reconcile_empty_and_garbage_safe():
    assert G.reconcile_confirmed([], []) == ([], [])
    assert G.reconcile_confirmed([{"name": "x", "w": 1, "d": 1}], None) == ([], [])
    m, o = G.reconcile_confirmed([{"name": "x", "w": 1, "d": 1}], ["oops", {"name": "x"}])  # non-dict skipped
    assert len(m) == 1 and o == [], (m, o)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} placement_gate tests passed")
