"""
test_pdf_extract_walls.py — unit tests for the PURE wall-extraction logic (no fitz/PDF).

The calibration triple (26.45 mm/pt, origin 171.2/596.5) and the thick-black / frame /
axis-aligned screens gate the correctness of EVERY downstream wall coordinate, but used to be
validated only empirically at build/gate time against the real PDF. These pin the transform +
filters so a regression (a flipped y-sign, a widened wall-width threshold, a dropped screen)
FAILs loudly. They do NOT claim the constant is physically correct — that stays the <1%
verification vs the written dims, done against the real sheet.
"""
import pdf_extract_walls as W

SCALE, X0, Y0 = 26.45, 171.2, 596.5


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ---- map_pt (the calibration transform) ----------------------------------------------
def test_map_pt_origin_maps_to_zero():
    x, y = W.map_pt(X0, Y0, SCALE, X0, Y0)
    assert approx(x, 0.0) and approx(y, 0.0)


def test_map_pt_matches_a_written_dim():
    # 5500 mm / 26.45 mm-per-pt = 207.94 pt EAST of the origin -> ~5500 mm, y unchanged
    x, y = W.map_pt(X0 + 5500 / SCALE, Y0, SCALE, X0, Y0)
    assert abs(x - 5500) < 1e-6 and approx(y, 0.0)


def test_map_pt_y_flips_so_up_the_page_is_north():
    # paper y is DOWN; a point ABOVE the origin (smaller py) must read as +y (north)
    _x, y = W.map_pt(X0, Y0 - 100, SCALE, X0, Y0)
    assert y > 0
    _x2, y2 = W.map_pt(X0, Y0 + 100, SCALE, X0, Y0)   # below origin -> south (negative)
    assert y2 < 0


# ---- is_wall_stroke (thick black only) -----------------------------------------------
def test_thick_black_is_a_wall():
    assert W.is_wall_stroke((0.0, 0.0, 0.0), 0.6) is True
    assert W.is_wall_stroke((0.0, 0.0, 0.0), 1.2) is True


def test_thin_stroke_is_not_a_wall():
    assert W.is_wall_stroke((0.0, 0.0, 0.0), 0.48) is False   # furniture/dim line weight


def test_light_grey_is_not_a_wall():
    assert W.is_wall_stroke((0.5, 0.5, 0.5), 0.9) is False    # sum 1.5 > 0.3


def test_no_stroke_colour_is_not_a_wall():
    assert W.is_wall_stroke(None, 0.9) is False
    assert W.is_wall_stroke((0.0, 0.0, 0.0), None) is False   # width None -> 0 -> not thick


# ---- keep_segment (frame / length / axis-aligned) ------------------------------------
def test_real_axis_aligned_wall_is_kept():
    assert W.keep_segment(0, 0, 5000, 0) is True             # a 5m horizontal wall
    assert W.keep_segment(0, 0, 0, 3000) is True             # a 3m vertical wall


def test_segment_outside_frame_is_dropped():
    assert W.keep_segment(25000, 0, 25000, 3000) is False    # sheet border / title block (x>21200)
    assert W.keep_segment(0, -5000, 0, -3000) is False       # below the frame (y<-1600)


def test_short_dim_tick_is_dropped():
    assert W.keep_segment(0, 0, 30, 0) is False              # 30mm < min_len 40


def test_over_max_length_is_dropped_but_long_wall_kept():
    # inside the frame but longer than max_len (the full-page span class) -> dropped
    assert W.keep_segment(-1000, 0, 20500, 0) is False       # length 21500 > 21000
    # ...while a genuine 20m wall within the limits is kept
    assert W.keep_segment(0, 0, 20000, 0) is True


def test_off_axis_slanted_line_is_dropped():
    assert W.keep_segment(0, 0, 100, 100) is False           # min(|dx|,|dy|)=100 > 8 -> not axis-aligned
    assert W.keep_segment(0, 0, 5000, 6) is True             # 6mm skew is within the 8mm tolerance


# ---- merge_carried (never silently drop owner-authored, non-regenerable walls) --------
def _calibrated(**kw):
    base = {"scale_mm_per_pt": 26.45, "origin_pt": [171.2, 596.5], "source_pdf": "p.pdf", "page": 1,
            "n": 1, "segments": [[[0, 0], [5000, 0]]]}
    base.update(kw)
    return base


def test_merge_carried_reinjects_manual_segments_into_segments():
    # THE real objective: the manual wall must land in top-level `segments` (what build_floor extrudes),
    # not merely in the manual_additions record. A fresh extract omits it (thin stroke) -> re-inject.
    fresh = _calibrated()
    prior = _calibrated(manual_additions={"segments": [[[-47, 600], [-47, -799]]]})
    merged, notes = W.merge_carried(fresh, prior)
    assert [[-47, 600], [-47, -799]] in merged["segments"], merged["segments"]
    assert merged["n"] == 2 and merged["manual_additions"] == prior["manual_additions"]
    assert any("re-injected" in s for s in notes), notes


def test_merge_carried_dedups_already_present_segment():
    seg = [[-47, 600], [-47, -799]]
    fresh = _calibrated(n=1, segments=[seg])
    prior = _calibrated(manual_additions={"segments": [[[-47, -799], [-47, 600]]]})  # same wall, reversed
    merged, _notes = W.merge_carried(fresh, prior)
    assert merged["segments"] == [seg] and merged["n"] == 1              # undirected dedup, not double-added


def test_merge_carried_skips_reinjection_on_calibration_drift():
    fresh = _calibrated()
    prior = _calibrated(scale_mm_per_pt=30.0, manual_additions={"segments": [[[-47, 600], [-47, -799]]]})
    merged, notes = W.merge_carried(fresh, prior)
    assert merged["segments"] == [[[0, 0], [5000, 0]]] and merged["n"] == 1   # stale coords NOT injected
    assert "manual_additions" in merged and any("WARNING" in s for s in notes), notes  # record kept, warned


def test_merge_carried_source_pdf_basename_is_not_drift():
    # a full path vs a stored basename is the SAME drawing -> must not count as drift and skip injection
    fresh = _calibrated(source_pdf="c:/x/y/p.pdf")
    prior = _calibrated(source_pdf="p.pdf", manual_additions={"segments": [[[-47, 600], [-47, -799]]]})
    merged, notes = W.merge_carried(fresh, prior)
    assert merged["n"] == 2 and any("re-injected" in s for s in notes), notes


def test_merge_carried_no_manual_additions_is_noop():
    fresh = _calibrated()
    merged, notes = W.merge_carried(fresh, _calibrated())               # prior has no manual_additions
    assert merged == _calibrated() and notes == []


def test_merge_carried_handles_missing_or_nondict_prior():
    assert W.merge_carried({"n": 0, "segments": []}, None) == ({"n": 0, "segments": []}, [])
    assert W.merge_carried({"n": 0, "segments": []}, "corrupt") == ({"n": 0, "segments": []}, [])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} pdf_extract_walls tests passed")
