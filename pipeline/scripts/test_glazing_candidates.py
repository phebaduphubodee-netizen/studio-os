"""
test_glazing_candidates.py -- unit tests for the PURE promotion logic (no fitz/PDF).

The fixtures below use the REAL numbers from the floor-2 sheet probe (2026-07-06):
the owner-patched SW-corner wall faces exist in raw ink as 0.48 pt fragments --
west verticals at x=-46.6 / 55.0 (101.6 mm pair), south returns at y=-799.3 /
-697.8 (101.5 mm pair), fragmented (e.g. 604.1->654.9 splinters). The promotion
rule must re-derive those four faces as candidates FROM RAW INK with the manual
patch removed from the wall set -- that is the whole point of the module. The
symmetric risk is over-promotion: bare furniture ink with no structural evidence
must NOT be promoted, and thin ink redrawn over an existing wall is not news.
"""
import glazing_candidates as G

# real raw thin fragments (probe of the actual sheet, mm) -- the SW corner patch zone
SW_THIN = [
    [[55.0, 451.2], [55.0, -697.8]],
    [[-46.6, 451.2], [-46.6, -799.3]],
    [[-46.6, 498.8], [-46.6, 451.2]],
    [[55.0, 451.2], [55.0, 498.8]],
    [[55.0, -697.8], [604.1, -697.8]],
    [[-46.6, -799.3], [604.1, -799.3]],
    [[654.9, -697.8], [604.1, -697.8]],
    [[604.1, -799.3], [654.9, -799.3]],
]
# the extracted THICK walls the SW faces continue from (owner snapped tops to 600):
# a west wall face pair above y=600 and a pier east of the south return
SW_WALLS = [
    [[-46.6, 3000.0], [-46.6, 600.0]],
    [[55.0, 3000.0], [55.0, 600.0]],
    [[604.1, -600.0], [604.1, -900.0]],
]
# the owner's signed patch (post-snap coordinates, from the real manual_additions)
SW_MANUAL = [
    [[-47, 600], [-47, -799]],
    [[55, 600], [55, -698]],
    [[-47, -799], [604, -799]],
    [[55, -698], [604, -698]],
]


def _cand_at(cands, axis, c, tol=8.0):
    hits = [x for x in cands if x["axis"] == axis and abs(x["c"] - c) <= tol]
    assert hits, f"no candidate at {axis}@{c} in {[(x['axis'], x['c']) for x in cands]}"
    return hits[0]


# ---- axis_run ------------------------------------------------------------------------
def test_axis_run_classifies_and_orders():
    assert G.axis_run([[10, 500], [10, -200]]) == ("v", 10.0, -200, 500)
    assert G.axis_run([[900, 40], [100, 40]]) == ("h", 40.0, 100, 900)
    assert G.axis_run([[0, 0], [300, 280]]) is None          # slanted -> not a run
    assert G.axis_run("garbage") is None


# ---- merge_runs ----------------------------------------------------------------------
def test_merge_runs_fuses_real_fragments_into_one_run_per_face():
    runs = G.merge_runs(SW_THIN)
    verts = sorted((r["c"], r["lo"], r["hi"]) for r in runs if r["axis"] == "v")
    hors = sorted((r["c"], r["lo"], r["hi"]) for r in runs if r["axis"] == "h")
    assert len(verts) == 2 and len(hors) == 2                # 8 fragments -> 4 faces
    assert verts[0][0] == -46.6 and verts[0][1] == -799.3 and verts[0][2] == 498.8
    assert hors[1][0] == -697.8 and hors[1][2] == 654.9      # splinter fused in

def test_merge_runs_respects_gap_tol():
    runs = G.merge_runs([[[0, 0], [0, 500]], [[0, 700], [0, 1200]]], gap_tol=160.0)
    assert len(runs) == 2                                    # 200 gap > 160 -> two runs
    runs = G.merge_runs([[[0, 0], [0, 500]], [[0, 640], [0, 1200]]], gap_tol=160.0)
    assert len(runs) == 1 and runs[0]["coverage"] < 1.0      # bridged, ink < span

def test_merge_runs_separates_distinct_lines():
    runs = G.merge_runs([[[0, 0], [0, 900]], [[30, 0], [30, 900]]], off_tol=6.0)
    assert len(runs) == 2                                    # 30 mm apart: NOT one line


# ---- scoring pieces --------------------------------------------------------------------
def test_ends_near_walls_counts_each_endpoint_once():
    run = {"axis": "v", "c": -46.6, "lo": -799.3, "hi": 498.8}
    # top end is 101 mm below the wall bottom (600) -> touches; bottom end touches nothing
    assert G.ends_near_walls(run, [SW_WALLS[0]]) == 1
    assert G.ends_near_walls(run, []) == 0

def test_covered_by_walls_suppresses_redrawn_wall():
    wall_runs = G.merge_runs([[[0, 0], [0, 2000]]])
    run = {"axis": "v", "c": 3.0, "lo": 100, "hi": 1900}     # thin ink over the wall
    assert G.covered_by_walls(run, wall_runs) > 0.9
    far = {"axis": "v", "c": 300.0, "lo": 100, "hi": 1900}   # a different line entirely
    assert G.covered_by_walls(far, wall_runs) == 0.0

def test_find_pair_wants_gap_band_and_overlap():
    runs = G.merge_runs(SW_THIN)
    verts = [i for i, r in enumerate(runs) if r["axis"] == "v"]
    assert G.find_pair(verts[0], runs) == verts[1]           # 101.6 mm apart -> mates
    lone = G.merge_runs([[[0, 0], [0, 900]], [[400, 0], [400, 900]]])
    assert G.find_pair(0, lone) is None                      # 400 mm > pair_gap max
    short = G.merge_runs([[[0, 0], [0, 900]], [[100, 800], [100, 1900]]])
    assert G.find_pair(0, short) is None                     # overlap 100 < 50% shorter


# ---- promote: the acceptance behaviour --------------------------------------------------
def test_promote_rederives_all_four_owner_patched_faces_as_strong():
    cands, stats = G.promote(SW_THIN, SW_WALLS, manual_segs=SW_MANUAL)
    for axis, c in (("v", -46.6), ("v", 55.0), ("h", -799.3), ("h", -697.8)):
        cand = _cand_at(cands, axis, c)
        assert cand["tier"] == "strong", (axis, c, cand)
        assert cand["confirms_manual_patch"] is True, (axis, c)
    assert stats["candidates"] >= 4

def test_promote_scores_pair_contact_and_length():
    cands, _ = G.promote(SW_THIN, SW_WALLS)
    west = _cand_at(cands, "v", -46.6)
    assert west["evidence"]["pair_with_c"] == 55.0
    assert west["evidence"]["ends_near_wall"] >= 1           # continues the wall above
    assert west["score"] >= 4                                # pair(2) + contact + len>=1000

def test_promote_drops_bare_furniture_ink():
    # a lone 500 mm tick far from any wall, no mate: zero structural evidence
    cands, stats = G.promote([[[3000, 3000], [3500, 3000]]], SW_WALLS)
    assert cands == []
    assert stats["dropped_below_score"] == 1                 # counted, never silent

def test_promote_ignores_thin_ink_over_existing_walls():
    thin = [[[-46.6, 3000.0], [-46.6, 600.0]]]               # redraws an extracted wall
    cands, stats = G.promote(thin, SW_WALLS)
    assert cands == [] and stats["runs_kept"] == 0

def test_promote_min_len_filters_short_runs():
    cands, _ = G.promote([[[0, 0], [0, 200]], [[100, 0], [100, 200]]], SW_WALLS)
    assert cands == []                                       # 200 < min_len 400, pair or not

def test_promote_without_manual_marks_nothing_confirmed():
    cands, _ = G.promote(SW_THIN, SW_WALLS)
    assert all(c["confirms_manual_patch"] is False for c in cands)

def test_inside_footprint_strict_containment_only():
    rect = [(1000, 1000, 2000, 3000)]                        # a placed wardrobe bbox
    inner = {"axis": "v", "c": 1500.0, "lo": 1100, "hi": 2900}
    assert G.inside_footprint(inner, rect) is True           # interior detail line
    edge = {"axis": "v", "c": 1005.0, "lo": 1100, "hi": 2900}
    assert G.inside_footprint(edge, rect) is False           # the outline sits ON the edge
    behind = {"axis": "v", "c": 980.0, "lo": 1100, "hi": 2900}
    assert G.inside_footprint(behind, rect) is False         # glass wall BEHIND survives
    sticking_out = {"axis": "v", "c": 1500.0, "lo": -1000, "hi": 2900}
    assert G.inside_footprint(sticking_out, rect) is False   # ov 1900/3900 < 0.7 span_frac
    assert G.inside_footprint({"axis": "h", "c": 2000.0, "lo": 1100, "hi": 1900}, rect) is True

def test_promote_furn_rects_suppress_interior_and_starve_outline_pairs():
    # bed at x 60..1060 (w 1000) drawn as outline pair edges + a headboard strip 100 mm
    # inside one edge; with the footprint passed, the strip is suppressed and the outline
    # edge loses its only 40..250 mm mate -> no strong furniture candidate survives
    wall = [[[0, 0], [0, 2000]]]
    bed_outline = [[[60, 100], [60, 1700]], [[1060, 100], [1060, 1700]]]
    strip = [[[160, 100], [160, 1700]]]
    cands_without, _ = G.promote(bed_outline + strip, wall)
    assert any(c["axis"] == "v" and abs(c["c"] - 60) < 8 for c in cands_without)
    cands_with, stats = G.promote(bed_outline + strip, wall,
                                  furn_rects=[(60, 100, 1060, 1700)])
    assert stats["suppressed_inside_furniture"] == 1         # the strip
    assert not any(c["axis"] == "v" and abs(c["c"] - 60) < 8 and c["tier"] == "strong"
                   for c in cands_with)

def test_promote_headboard_pair_against_wall_is_documented_strong_noise():
    # documented noise case (docstring KNOWN NOISE): bed edge + headboard strip 100 mm
    # apart, 1600 mm long, ONE end zone abutting a wall scores pair(2)+contact(1)+len(1)
    # = 4 -> STRONG. That is the honest, documented behaviour -- the real cut is the
    # manifest footprint suppression (tested below), and the stub ships EMPTY so a
    # strong furniture pair never lands in a paste. A gap-spanning boundary must still
    # outrank it (both ends + pair).
    wall = [[[0, 0], [0, 2000]]]
    bed = [[[60, 100], [60, 1700]], [[160, 100], [160, 1700]]]
    glass = [[[300, -10], [300, 2010]], [[400, -10], [400, 2010]]]   # spans wall to wall
    walls = wall + [[[0, -10], [500, -10]], [[0, 2010], [500, 2010]]]
    cands, _ = G.promote(bed + glass, walls)
    g = _cand_at(cands, "v", 300)
    b = _cand_at(cands, "v", 60)
    assert g["score"] > b["score"]
    assert b["tier"] == "strong"          # pin the documented reality, not the wish

def test_tier_boundary_pinned_both_sides():
    # score 2 (pair only, short-ish) == weak; score 3 (pair + one wall contact) == strong
    walls = [[[0, 0], [0, 2000]]]
    pair_only = [[[3000, 3000], [3000, 3500]], [[3100, 3000], [3100, 3500]]]
    cands, _ = G.promote(pair_only, walls)
    assert {c["tier"] for c in cands} == {"weak"} and cands[0]["score"] == 2
    pair_touching = [[[300, 30], [300, 530]], [[400, 30], [400, 530]]]
    walls2 = [[[0, 0], [800, 0]]]        # perpendicular wall 30 mm below the pair's feet
    cands2, _ = G.promote(pair_touching, walls2)
    assert all(c["tier"] == "strong" and c["score"] == 3 for c in cands2)

def test_score_one_run_is_dropped_not_listed():
    # one end near a wall, no pair, short: score exactly 1 -> dropped (counted)
    walls = [[[0, 0], [800, 0]]]
    cands, stats = G.promote([[[300, 30], [300, 530]]], walls)
    assert cands == [] and stats["dropped_below_score"] == 1

def test_length_bonus_threshold_pinned():
    # same pair geometry, 990 vs 1010 mm long, far from walls: 2 vs 3
    short_pair = [[[3000, 0], [3000, 990]], [[3100, 0], [3100, 990]]]
    long_pair = [[[6000, 0], [6000, 1010]], [[6100, 0], [6100, 1010]]]
    cands, _ = G.promote(short_pair + long_pair, [])
    assert _cand_at(cands, "v", 3000)["score"] == 2
    assert _cand_at(cands, "v", 6000)["score"] == 3

def test_merge_runs_band_width_is_capped_against_hatch_drift():
    # fine-pitch hatching every 5 mm from c=0..50: consecutive gaps are all <= off_tol,
    # but chaining them into ONE run at a phantom c=25 would erase two distinct faces;
    # the band cap forces multiple runs and keeps positions near real ink
    hatch = [[[c, 0], [c, 900]] for c in range(0, 55, 5)]
    runs = G.merge_runs(hatch)
    assert len(runs) >= 4                                    # NOT one phantom line
    assert all(r["hi"] - r["lo"] == 900 for r in runs)

def test_merge_runs_default_gap_tol_pinned():
    # 200 mm break with DEFAULT params -> two runs (the shipped default, not a param)
    runs = G.merge_runs([[[0, 0], [0, 500]], [[0, 700], [0, 1200]]])
    assert len(runs) == 2

def test_thin_ink_in_a_wall_gap_is_not_wall_covered():
    # two collinear walls with a 1000 mm gap; thin ink IN the gap is the module's
    # headline sliding-door case -- bridged wall merging would mark it covered
    walls = [[[0, 0], [0, 2000]], [[0, 3000], [0, 5000]]]
    thin = [[[0, 2100], [0, 2900]], [[100, 2100], [100, 2900]]]   # pair in the gap
    cands, stats = G.promote(thin, walls)
    assert stats["dropped_wall_covered"] == 0
    c = _cand_at(cands, "v", 0)
    assert c["tier"] == "strong" and c["evidence"]["ends_near_wall"] == 2

def test_partially_covered_run_is_kept():
    # a run only 50% under a collinear wall is NEWS (the uncovered half), not noise
    walls = [[[0, 0], [0, 1000]]]
    thin = [[[0, 500], [0, 2500]], [[100, 500], [100, 2500]]]
    cands, stats = G.promote(thin, walls)
    assert stats["dropped_wall_covered"] == 0 and len(cands) == 2

def test_pair_gap_lower_edge_pinned():
    # double-struck lines 20 mm apart are one drawn face, not a face PAIR
    runs = G.merge_runs([[[0, 0], [0, 900]], [[20, 0], [20, 900]]], off_tol=6.0)
    assert len(runs) == 2
    assert G.find_pair(0, runs) is None                      # 20 < pair_gap lower 40

def test_find_pair_nearest_mate_wins():
    runs = G.merge_runs([[[0, 0], [0, 900]], [[100, 0], [100, 900]], [[240, 0], [240, 900]]])
    runs.sort(key=lambda r: r["c"])
    assert runs[G.find_pair(0, runs)]["c"] == 100.0          # not the 240 one

def test_matches_manual_requires_two_way_overlap():
    manual = [[[0, 600], [0, -799]]]                         # a 1399 mm owner patch
    honest = {"axis": "v", "c": 0.0, "lo": -799.3, "hi": 498.8}
    assert G.matches_manual(honest, manual) is True
    # a 15 m facade line that merely PASSES THROUGH the patched stretch is not a confirm
    facade = {"axis": "v", "c": 0.0, "lo": -799.3, "hi": 14000.0}
    assert G.matches_manual(facade, manual) is False

def test_candidate_and_stats_output_shape_pinned():
    # downstream consumers (overlay, stub emission, prints) key into these exact names
    cands, stats = G.promote(SW_THIN, SW_WALLS, manual_segs=SW_MANUAL)
    c = cands[0]
    assert set(c.keys()) == {"axis", "c", "span", "length_mm", "score", "tier",
                             "evidence", "confirms_manual_patch", "segments"}
    assert set(c["evidence"].keys()) == {"pair_with_c", "ends_near_wall", "pieces", "coverage"}
    assert set(stats.keys()) == {"thin_segments", "runs", "runs_kept", "candidates",
                                 "dropped_short", "dropped_wall_covered",
                                 "suppressed_inside_furniture", "dropped_below_score"}


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} glazing_candidates tests passed")
