"""Tests for bluehouse_plan_reader.

    python -m pytest pipeline/scripts/test_bluehouse_plan_reader.py -q

ROUND 2 REWRITE. Round 1's headline pin was a TAUTOLOGY:

    (bx0, by0) == (0.0, 0.0)          # "the bbox starts at the origin"

The origin is DEFINED as min-x / max-y of the very bands the bbox is taken over, so that assert
cannot fail -- not for a real plan, not for a cabinet elevation, not for a random point cloud. It
is deleted. Its neighbours (bbox == the printed 7820 x 9720 overalls) are kept but DEMOTED and
labelled: they were TRUE in round 1, when the emitted geometry was a dozen freestanding 100 mm
fins on a slab. A bbox is the hull of a point cloud; it is not evidence of a building.

What replaces it -- assertions that CAN fail, and two of which DID fail while this file was
being written:
  * PRINTED-STRING CROSS-CHECK: measured face-to-face distances are matched against dimension
    strings scraped from the sheet's own text layer at test time. Nothing is hardcoded from the
    hand takeoff, and a calibration error moves the measurement off the string.
  * CLOSURE THAT CAN FAIL: the living zone does NOT close without owner-signed virtual edges.
    test_closure_FAILS_without_the_signed_virtual_edges pins the failure.
  * THE GATE: the reader is run over all 18 pages of the real PDF; exactly 2 may be accepted.
  * NOTHING IS SILENTLY DROPPED: every wall-pen quad is accounted for as band | step | reported.
  * PART C got unit tests at last (round 1 shipped it on one end-to-end run).
"""
import inspect
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest

from bluehouse_plan_reader import (
    GLAZING_COVER_FRAC, GRID_MM, PT_MM, RefuseSheet, SNAP_TOL_MM, THAI_FLOORPLAN_SKEL,
    audit_sides, band_aligned, band_axis, band_long_edges, classify_panels, composite_run_keys,
    derive_room_polygon, envelope_checks, extent_is_a_storey, find_gaps, flood_region,
    gap_composite_mm, gap_coverage, gap_ink_rects, gap_pen_mm,
    gap_rect, gap_segments, geometry_snap, is_boundary_ink, is_dimension_tick, is_wall_band,
    is_wall_step, merge_runs, run_keys, type_openings,
    openings_on_outline, outline_from_seed, parse_scale_field, parse_titleblock_denom,
    parse_virtual_edge, plan_extent, plan_gate, read_bands, resolve_gaps, resolve_scale,
    sheet_shrink, snap_polygon, thai_skeleton, thickness_ok, titleblock_field, title_is_floor_plan,
    to_mm_bands, trace_contours, type_openings, CANDIDATE_DENOMS, WALL_MM_LO, WALL_MM_HI,
)
import math
from floor_openings import clip_wall_segments, opening_boxes
from pdf_extract_walls import _seg_key, merge_carried

SCALE_50 = PT_MM * 50            # 17.63888... mm/pt


# ================================================================= the class predicate (1-4)
def test_is_wall_band_accepts_the_bluehouse_wall_pen():
    assert is_wall_band("s", (0.0, 0.0, 0.0), 0.84, 1, "qu")


@pytest.mark.parametrize("dtype,color,width,n,op,why", [
    ("f",  (0, 0, 0),          0.84, 1, "qu", "fill-only is not a stroke"),
    ("fs", (0, 0, 0),          0.84, 1, "qu", "fill+stroke = a text glyph outline, not a wall"),
    ("s",  None,               0.84, 1, "qu", "no stroke colour"),
    ("s",  (0.4, 0.4, 0.4),    0.84, 1, "qu", "grey furniture pen"),
    ("s",  (0.0, 0.0, 0.0),    0.42, 1, "qu", "the GLAZING pen, not the wall pen"),
    ("s",  (0.0, 0.0, 0.0),    0.24, 1, "qu", "the hatch/poche pen"),
    ("s",  (0.0, 0.0, 0.0),    0.72, 1, "qu", "leaders / title-block rules"),
    ("s",  (0.0, 0.0, 0.0),    1.44, 1, "qu", "the sheet border"),
    ("s",  (0.0, 0.0, 0.0),    0.84, 2, "qu", "not a LONE item -> a compound path, not a band"),
    ("s",  (0.0, 0.0, 0.0),    0.84, 1, "l",  "a bare line, not a closed band"),
    ("s",  (0.0, 0.0, 0.0),    0.84, 1, "re", "a rect item is not the quad the exporter emits"),
])
def test_is_wall_band_rejects(dtype, color, width, n, op, why):
    assert not is_wall_band(dtype, color, width, n, op), why


def test_width_criterion_is_load_bearing_not_redundant_with_thickness():
    """The real sheet carries a lone quad in the w=0.12 class that is ALSO ~100 mm thick (a
    kitchen cabinet panel at paper x465-471). A thickness-only rule ingests it as a wall."""
    thin_pt = 5.76           # the cabinet panel's measured thin dim: 101.6 mm at 1:50
    assert thickness_ok(thin_pt, SCALE_50), "criterion 5 alone would accept it as a wall"
    assert not is_wall_band("s", (0, 0, 0), 0.12, 1, "qu"), "criterion 3 is what rejects it"


def test_thickness_screen_is_in_mm_so_it_survives_a_different_plot_scale():
    at_1_50 = 5.64                      # the real modal thin-dim on the source sheet
    at_1_100 = at_1_50 / 2              # same 100 mm wall, plotted half-size
    assert thickness_ok(at_1_50, PT_MM * 50)
    assert thickness_ok(at_1_100, PT_MM * 100)
    assert not thickness_ok(at_1_100, PT_MM * 50), "a pt-based screen would break here"


# ================================================================= FAIL-CLOSED SCALE
def test_geometry_snap_is_a_veto_not_a_source():
    """geometry_snap REPORTS which denominators a thickness could be a 100 mm wall at. It does
    not return a scale, because it cannot: the same measurement is a 100 mm wall at 1:50 and a
    200 mm wall at 1:100, and only the sheet knows which."""
    modal, hits = geometry_snap([5.64] * 34 + [5.70] * 9 + [2.28] * 2)
    assert modal == 5.64 and hits == [50]
    assert geometry_snap([]) == (None, [])


def test_THE_ROUND_1_BUG_a_200mm_wall_at_1_50_snaps_to_1_25():
    """The exact failure mode. 11.34 pt is a 200 mm wall at 1:50. Round 1's detect_scale() saw
    only 'that snaps cleanly at 1:25' and returned 1:25 -- emitting the building at HALF SIZE,
    silently. The snap still says 25; what changed is that nobody may act on it alone."""
    modal, hits = geometry_snap([11.34] * 20)
    assert hits == [25], "the trap is real: the geometry does snap, cleanly, to the wrong scale"
    assert round(11.34 * PT_MM * 50) == 200, "and at the TRUE scale it is a 200 mm party wall"
    with pytest.raises(RefuseSheet, match="SCALE DISAGREEMENT"):
        resolve_scale([11.34] * 20, 50)       # title block says 1:50 -> REFUSE, do not halve


def test_resolve_scale_the_title_block_wins_when_geometry_agrees():
    scale, denom, modal, note = resolve_scale([5.64] * 30, 50)
    assert denom == 50 and scale == pytest.approx(17.63889, abs=1e-4)
    assert "TITLE BLOCK" in note and "CONFIRMED" in note


def test_resolve_scale_refuses_a_sheet_with_no_stated_scale():
    with pytest.raises(RefuseSheet, match="states NO scale"):
        resolve_scale([5.64] * 30, None)


def test_resolve_scale_refuses_a_detail_scale():
    """1:25 is not a floor-plan scale. This alone refuses every joinery sheet in the PDF."""
    with pytest.raises(RefuseSheet, match="not a floor-plan scale"):
        resolve_scale([11.34] * 5, 25)


def test_resolve_scale_accepts_a_wall_that_snaps_to_nothing_but_is_plausible():
    """A 150 mm wall at 1:50 (8.5 pt) snaps to no denominator in the 95-106 window. The title
    block still rules; the sheet is only refused if the stated scale makes the wall absurd."""
    scale, denom, modal, note = resolve_scale([8.5] * 20, 50)
    assert denom == 50 and "does not snap" in note
    with pytest.raises(RefuseSheet, match="not a plausible wall"):
        resolve_scale([40.0] * 20, 50)        # would be a 705 mm "wall"


def test_no_detect_scale_function_survives():
    """The fail-open API is DELETED, not deprecated. If it comes back, this test fails."""
    import bluehouse_plan_reader as r
    assert not hasattr(r, "detect_scale"), "detect_scale() inferred a scale from an ASSUMED wall"


# ================================================================= THE PAGE-TYPE GATE
def test_title_block_scale_field_is_read_positionally():
    """The scale is the value span directly BELOW the title block's 'SCALE :' label -- not any
    1:NN string on the page. (The label must carry the colon; see the real-PDF disclaimer-trap
    pin below for why.)"""
    spans = [(1028.5, 635.8, "SCALE :"), (1028.5, 645.4, "1 : 50  "),
             (1026.8, 656.7, "ISSUED / REVISION")]
    assert parse_scale_field(titleblock_field(spans, "SCALE :")) == 50
    no_scale = [(1028.5, 635.8, "SCALE :"), (1028.5, 645.4, "ISSUED / REVISION")]
    assert parse_scale_field(titleblock_field(no_scale, "SCALE :")) is None, \
        "an empty SCALE row must NOT return the next row as a scale"


def test_parse_scale_field_rejects_a_non_ratio():
    assert parse_scale_field("ISSUED / REVISION") is None
    assert parse_scale_field(None) is None
    assert parse_scale_field("1 : 50  ") == 50


def test_title_is_floor_plan_accepts_a_PLAN_title():
    assert title_is_floor_plan("FURNITURE PLAN 1", "")[0]


def test_title_is_floor_plan_vetoes_the_joinery_sheets():
    """'แบบขยาย BF-01' = enlarged joinery detail. These are the 7 sheets round 1 turned into
    floor plans."""
    ok, why = title_is_floor_plan("แบบขยาย BF-01", "")
    assert not ok and "detail/elevation/section" in why


def test_bare_THAI_plan_word_IS_evidence_in_the_TITLE_but_the_veto_runs_first():
    """ROUND 3. The old test here asserted bare แปลน is NEVER evidence, citing "แปลน appears in the
    BODY of 6 of the 7 joinery sheets". That trap is real but it is a PAGE_TEXT trap, and the gate
    was applying it to the positional TITLE field -- where, measured over 898 corpus pages, แปลน
    appears in 62 plan titles and 0 non-plan titles once the แบบขยาย veto has run.

    So bare แปลน in the DRAWING TITLE now ACCEPTS -- and this test pins the only thing that makes
    that safe: the veto runs FIRST. Reorder title_is_floor_plan so the accept precedes the veto and
    the second assertion goes red, because 'แบบขยายแปลนห้องน้ำ' (the enlarged bathroom plan) would
    be emitted to build_floor as a storey."""
    ok, why = title_is_floor_plan("แปลนเฟอร์นิเจอร์ ชั้น 1", "")
    assert ok, "a Thai furniture plan is a plan; the office does not title its plans แปลนพื้น"

    ok, why = title_is_floor_plan("แบบขยายแปลนห้องน้ำ", "")
    assert not ok, "VETO-FIRST: an ENLARGED plan of one bathroom must never reach build_floor"
    assert "detail/elevation/section" in why


def test_the_page_text_fallback_is_GONE_and_cannot_resurrect():
    """It FAILED OPEN. `if THAI_FLOORPLAN_SKEL in thai_skeleton(page_text)` passed T1 on 3
    'รายการประกอบแบบ' (specification-index) sheets, whose BODY quotes every sheet title in the set
    -- including แปลนพื้น -- while the sheet itself is a text page. A page-wide keyword search cannot
    say what a SHEET IS.

    NOTE the test this replaces asserted `title_is_floor_plan("NOT A PLAN TITLE", split)[0]` with the
    message "the Thai fallback must fire". It never fired: "NOT A PLAN TITLE" contains the substring
    PLAN, so the LATIN branch returned True and the assertion passed for a reason it did not name.
    It stayed green after the fallback was deleted. That is a test that could not fail -- the exact
    shape this repo keeps re-inventing. Use a title with NO plan word in it, so only the fallback
    could ever satisfy the assertion."""
    ok, why = title_is_floor_plan("รายการประกอบแบบ", "แปลนพื้นชั้น 1   แปลนพื้นชั้น 2")
    assert not ok, "the sheet's BODY quoting แปลนพื้น must NOT make the sheet a floor plan"
    assert "not a plan title" in why


def test_thai_skeleton_survives_split_combining_marks_AND_font_private_marks():
    """The PDF text layer splits vowel/tone marks off their consonants -- and this office's CAD font
    emits them into the Unicode PRIVATE USE AREA (U+F70E = thanthakhat, U+F70B = mai tho) instead of
    U+0E47-0E4E, where the old _THAI_MARKS range could not see them.

    That was NOT cosmetic. skeleton('รูปด้าน') left the PUA mark wedged between ด and า, so the
    ELEVATION veto skeleton 'รปดาน' did not match and THE VETO SILENTLY DID NOT FIRE on 5 elevation
    sheets -- while the gate reported the veto as working. Drop U+F700-F71F from _THAI_MARKS and the
    last assertion goes red."""
    composed = "แปลนพื้นชั้น 1"
    split = "แปลนพ" + "ื้" + "น"      # marks adrift
    assert THAI_FLOORPLAN_SKEL in thai_skeleton(composed)
    assert THAI_FLOORPLAN_SKEL in thai_skeleton(split)

    pua_elev = "รูปดาน"          # 'รูปด้าน' as the real title block emits it
    assert thai_skeleton("รปดาน") in thai_skeleton(pua_elev), "PUA marks must not break the skeleton"
    ok, why = title_is_floor_plan(pua_elev, "")
    assert not ok and "detail/elevation/section" in why, "the ELEVATION veto must fire through PUA"


def test_T3_a_plan_of_ONE_ROOM_is_not_a_FLOOR_and_is_refused():
    """THE CLASS A TITLE-BASED ANSWER KEY CANNOT SEE. This module emits wall-segments for
    build_floor: its product is a FLOOR. 9 corpus sheets are titled แปลนเฟอร์นิเจอร์ <ROOM> -- a
    per-room ENLARGEMENT under a title the designer spelled differently from แบบขยาย.

    They are not caught by geometry: the live one (a 12.0 x 4.8 m strip = two bedrooms and their
    baths) has walls, a stated 1:50, a 57.6 m2 footprint and ink on four sides, so G0/T1/T2/S1/E ALL
    PASS on it. Its PDF contains no whole-storey plan at all, so without T3 that bedroom becomes THE
    floor of that project. Delete T3 and this goes red; scoring the gate on "does the title say
    แปลน" cannot go red at all, which is why the check exists and the metric did not find it."""
    for room_title in ("แปลนเฟอร์นิเจอร์ ห้องนอน 3,4", "แปลนเฟอร์นิเจอร์ ห้องรับแขก",
                       "แปลนเฟอร์นิเจอร์ห้องพระ"):
        ok_t, _ = title_is_floor_plan(room_title, "")
        assert ok_t, "T1 is RIGHT to call it a plan -- it is one. T3 is what says it is not a FLOOR."
        assert plan_extent(room_title) == "room"
        ok_x, why = extent_is_a_storey(room_title, ok_t)
        assert not ok_x and "per-room ENLARGEMENT" in why

    for storey_title in ("แปลนเฟอร์นิเจอร์ ชั้น 1", "แปลนพื้น", "FURNITURE PLAN 1", "แปลนผนัง"):
        ok_t, _ = title_is_floor_plan(storey_title, "")
        assert plan_extent(storey_title) == "storey"
        assert extent_is_a_storey(storey_title, ok_t)[0], f"{storey_title} is a storey, not a room"


def test_T3_is_wired_into_the_gate_that_the_corpus_actually_runs():
    """read_bands() builds its OWN check list; plan_gate() is not called by it. A T3 added to only
    one of them would be a check that never executes on a real page. Pin both lists carrying it."""
    src = inspect.getsource(read_bands)
    assert '"id": "T3"' in src, "T3 must be in read_bands' own check list, not just plan_gate's"
    ids = [c["id"] for c in plan_gate("แปลนเฟอร์นิเจอร์ ห้องนอน 1", "", 50, [])]
    assert "T3" in ids
    t3 = next(c for c in plan_gate("แปลนเฟอร์นิเจอร์ ห้องนอน 1", "", 50, []) if c["id"] == "T3")
    assert t3["ok"] is False


def test_the_reflected_ceiling_plan_is_refused_because_it_has_no_WALL_POCHE():
    """แปลนฝ้าเพดาน is a real plan, and the reader must still refuse it: MEASURED, 6 of its 7 pages
    carry ZERO 0.84 pt wall quads (every other plan class has a median of 31-117). An RCP draws the
    ceiling grid, not the poche, and shows no openings -- build_floor would emit a sealed box.

    The counterexample that keeps this from becoming "veto anything unfamiliar": แปลนไฟฟ้า
    (electrical) IS accepted -- 4/4 of its pages DO carry the poche (median 31 wall quads), so it is
    a structurally valid source of the same walls."""
    ok, why = title_is_floor_plan("แปลนฝ้าเพดาน", "")
    assert not ok and "reflected ceiling plan" in why
    assert title_is_floor_plan("แปลนไฟฟ้าแสงสว่าง", "")[0], \
        "electrical plans DO carry the wall poche -- do not veto what you have not measured"


def test_envelope_checks_refuse_a_cabinet_elevation():
    """3 lone bands, 900 mm apart: a cabinet, not a building."""
    bands = [(0.0, 0.0, 900.0, 100.0), (0.0, 600.0, 900.0, 700.0), (0.0, 0.0, 100.0, 700.0)]
    checks = {c["id"]: c["ok"] for c in envelope_checks(bands)}
    assert checks["E1"] is False and checks["E2"] is False


def test_envelope_checks_are_the_WEAKEST_signal_and_this_is_pinned():
    """HONESTY PIN. E3 (wall ink on all four sides) would pass a sheet with 12 bands in a ring
    and nothing else. It passes the real plan page with only 0.09. It is a floor, not evidence."""
    ring = [(0.0, 0.0, 6000.0, 100.0), (0.0, 5900.0, 6000.0, 6000.0),
            (0.0, 0.0, 100.0, 6000.0), (5900.0, 0.0, 6000.0, 6000.0)] * 3
    checks = {c["id"]: c["ok"] for c in envelope_checks(ring)}
    assert all(checks.values()), "a bare ring of 12 bands satisfies every envelope check"


def test_parse_titleblock_denom_is_page_wide_and_therefore_NOT_used_for_scale():
    """Kept only because merge_carried-era callers import it. It reads the MODAL 1:NN anywhere on
    the page, which on a joinery sheet is a view caption. The gate uses the title-block FIELD."""
    assert parse_titleblock_denom("1:50 ... 1:50 ... 1:100") == 50
    assert parse_titleblock_denom("no scale here") is None


# ================================================================= the WALL STEP class
def test_is_wall_step_requires_adjacency_to_a_real_wall():
    """The 40 mm quads round 1 dropped silently. A step is a THICKENING of a wall, so it must
    touch one; a free-floating 40 mm sliver is furniture and stays out."""
    wall = [(0.0, 0.0, 100.0, 3000.0)]
    assert is_wall_step((100.0, 2900.0, 140.0, 3000.0), wall), "abuts the wall's east face"
    assert not is_wall_step((4000.0, 2900.0, 4040.0, 3000.0), wall), "a free-floating sliver"


def test_a_step_is_not_widened_into_the_wall_class():
    """We CLASSIFY the 40 mm quads rather than widening the 95-106 mm window to 35-106. A bare
    widening would also admit the 40 mm joinery panels that cover the detail sheets."""
    assert not thickness_ok(2.28, SCALE_50), "40 mm stays out of the WALL class"


# ================================================================= emission (A)
def test_band_long_edges_emits_two_parallel_faces_not_a_centreline():
    segs = band_long_edges(0.0, 0.0, 5000.0, 100.0)
    assert segs == [[[0.0, 0.0], [5000.0, 0.0]], [[0.0, 100.0], [5000.0, 100.0]]]
    assert abs(segs[0][0][1] - segs[1][0][1]) == 100.0, "the faces are 100 mm apart"


def test_band_long_edges_drops_the_end_caps():
    segs = band_long_edges(0.0, 0.0, 5000.0, 100.0)
    caps = {_seg_key([[0.0, 0.0], [0.0, 100.0]]), _seg_key([[5000.0, 0.0], [5000.0, 100.0]])}
    assert not ({_seg_key(s) for s in segs} & caps)


def test_band_long_edges_vertical():
    assert band_long_edges(3020.0, 250.0, 3120.0, 3485.0) == [
        [[3020.0, 250.0], [3020.0, 3485.0]], [[3120.0, 250.0], [3120.0, 3485.0]]]


def test_band_axis():
    assert band_axis(0, 0, 5000, 100) == "h"
    assert band_axis(0, 0, 100, 5000) == "v"
    assert band_axis(0, 0, 100, 100) == "sq", "a corner block belongs to both axes"


# ================================================================= runs + openings (B)
def test_merge_runs_joins_abutting_collinear_bands():
    runs = merge_runs([(0.0, 0.0, 1000.0, 100.0), (1000.0, 0.0, 2500.0, 100.0)])
    assert runs[("h", 0.0, 100.0)] == [(0.0, 2500.0)]


def test_merge_runs_keeps_a_real_gap_apart():
    runs = merge_runs([(0.0, 0.0, 1000.0, 100.0), (4000.0, 0.0, 5000.0, 100.0)])
    assert runs[("h", 0.0, 100.0)] == [(0.0, 1000.0), (4000.0, 5000.0)]


def test_a_square_corner_block_bridges_a_run_on_both_axes():
    runs = merge_runs([(7720.0, 100.0, 7820.0, 1000.0), (7720.0, 1000.0, 7820.0, 1100.0)])
    assert runs[("v", 7720.0, 7820.0)] == [(100.0, 1100.0)]


def test_find_gaps_finds_the_opening_between_two_collinear_runs():
    gaps = find_gaps({("h", 0.0, 100.0): [(0.0, 3570.0), (6770.0, 7820.0)]}, min_gap=400.0)
    assert len(gaps) == 1 and gaps[0]["length_mm"] == 3200.0


def test_find_gaps_ignores_sub_door_noise():
    assert find_gaps({("h", 0.0, 100.0): [(0.0, 1000.0), (1050.0, 2000.0)]}, min_gap=400.0) == []


def test_gap_segments_bridge_both_faces():
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 3570.0, "gap_hi": 6770.0,
         "length_mm": 3200.0}
    assert gap_segments(g) == [[[3570.0, 0.0], [6770.0, 0.0]], [[3570.0, 100.0], [6770.0, 100.0]]]


def test_gap_rect_is_the_walls_own_footprint_over_the_hole():
    g = {"axis": "v", "face_lo": 7720.0, "face_hi": 7820.0, "gap_lo": 1100.0, "gap_hi": 4000.0,
         "length_mm": 2900.0}
    assert gap_rect(g) == [7720.0, 1100.0, 7820.0, 4000.0]


def test_outline_from_seed_REFUSES_to_close_a_side_with_no_wall_ink():
    bands = [(0, 0, 100, 3000), (3000, 0, 3100, 3000)]          # west + east only
    oc = outline_from_seed(bands, (1500, 1500))
    assert oc["open_sides"] == ["north", "south"]
    assert oc["inner_wh_mm"] is None, "must NOT fabricate a depth for an open zone"


# ================================================================= PART C (round 1 shipped this
# with ZERO unit tests, on one end-to-end run. That was the top item on its own self-assessment.)
def test_is_dimension_tick_uses_LENGTH_not_position():
    """16 of the 108 dimension-tick crosses sit INSIDE the envelope, on interior chains, so an
    inside/outside test would keep them. Length is what separates them."""
    assert is_dimension_tick(1, "l", 122.0), "a 122 mm lone line is half of a '+' tick"
    assert not is_dimension_tick(1, "l", 3200.0), "a 3.2 m lone line is a glazing panel"
    assert not is_dimension_tick(2, "l", 122.0), "a compound path is not a tick"


def test_band_aligned_keeps_glazing_and_rejects_a_swinging_door_leaf():
    runs = [("h", 0.0, 100.0)]
    assert band_aligned((3570.0, 0.0, 6770.0, 100.0), runs) == ("h", 0.0, 100.0)
    assert band_aligned((3570.0, 0.0, 4440.0, 870.0), runs) is None, "the leaf sticks out 870 mm"


def test_classify_panels_splits_ink_from_ticks_and_frame():
    env = (-500.0, -500.0, 8500.0, 10000.0)
    runs = {("h", 0.0, 100.0): [(0.0, 8000.0)]}   # the merge_runs DICT: composites need extents
    paths = [{"rect": (3570.0, 0.0, 6770.0, 100.0), "n_items": 4, "op": "l"},   # glazing
             {"rect": (2000.0, -60.0, 2000.0, 62.0), "n_items": 1, "op": "l"},  # dim tick
             {"rect": (-900.0, -900.0, 9000.0, 11000.0), "n_items": 1, "op": "re"},  # frame
             {"rect": (3570.0, 0.0, 4440.0, 870.0), "n_items": 2, "op": "c"}]   # door leaf
    boundary, rejected = classify_panels(paths, runs, env)
    assert len(boundary) == 1 and boundary[0]["rect"][0] == 3570.0
    assert {r["why"] for r in rejected} == {"dimension tick", "outside envelope (sheet/clip frame)",
                                            "not band-aligned (perpendicular door leaf)"}


def test_gap_coverage_only_counts_ink_on_the_SAME_run():
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 0.0, "gap_hi": 1000.0,
         "length_mm": 1000.0}
    same = [{"rect": (0.0, 0.0, 800.0, 100.0), "run": ("h", 0.0, 100.0)}]
    other = [{"rect": (0.0, 9620.0, 800.0, 9720.0), "run": ("h", 9620.0, 9720.0)}]
    assert gap_coverage(g, same) == pytest.approx(0.8)
    assert gap_coverage(g, other) == 0.0, "ink on the far wall must not back this gap"


def test_resolve_gaps_is_a_three_way_split_and_a_long_unbacked_hole_stays_OPEN():
    """The honest failure channel. A 3.2 m hole with no ink is NOT bridged, at any tolerance."""
    gaps = [{"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 0.0, "gap_hi": 3200.0,
             "length_mm": 3200.0},                                        # long, no ink -> VOID
            {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 4000.0, "gap_hi": 4150.0,
             "length_mm": 150.0},                                         # short, no ink -> INFILL
            {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 5000.0, "gap_hi": 5900.0,
             "length_mm": 900.0}]                                         # ink -> OPENING
    boundary = [{"rect": (5000.0, 0.0, 5900.0, 100.0), "run": ("h", 0.0, 100.0)}]
    infill, openings, voids = resolve_gaps(gaps, boundary)
    assert len(infill) == 1 and len(openings) == 1 and len(voids) == 1
    assert voids[0]["length_mm"] == 3200.0, "a metre-scale unbacked hole is never infilled"
    assert len(infill) + len(openings) + len(voids) == len(gaps), "every gap is accounted for"


def test_the_O01_threshold_is_fragile_and_this_test_says_so():
    """O01 on the real sheet has ink coverage 0.616 against a 0.60 threshold -- 1.6 points of
    margin. At 0.65 it becomes an unbacked VOID instead of a 650 mm window. Pinned, not tuned."""
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 0.0, "gap_hi": 1000.0,
         "length_mm": 1000.0}
    boundary = [{"rect": (384.0, 0.0, 1000.0, 100.0), "run": ("h", 0.0, 100.0)}]
    assert gap_coverage(g, boundary) == pytest.approx(0.616, abs=1e-3)
    assert GLAZING_COVER_FRAC == 0.60
    assert resolve_gaps([g], boundary)[1], "at 0.60 it is an opening"
    assert not resolve_gaps([g], boundary, cover=0.65)[1], "at 0.65 it is not"


def test_boundary_ink_is_a_GEOMETRIC_class_not_012s_pen_table():
    """THE 0.42 LESSON. PANEL_PEN_PT = 0.42 was sheet 012's pen table: the Pandora sheets have
    NO 0.42 ink anywhere (their boundary pens are 0.38/0.48), I-24-056 draws its openings at
    0.12, and so 22 of 27 gate-accepted corpus pages closed NOTHING -- every opening read as an
    ink-less void. The class is black-stroke + NOT-the-wall-pen; width is reported evidence,
    never a filter."""
    for w in (0.12, 0.38, 0.42, 0.48, 0.54, 1.44):
        assert is_boundary_ink("s", (0, 0, 0), w), f"a {w}-pt black stroke is boundary ink"
    assert not is_boundary_ink("s", (0, 0, 0), 0.84), "the wall pen keeps its own class"
    assert not is_boundary_ink("s", (1.0, 0.2, 0.2), 0.42), "colored ink is not (yet) in class"
    assert not is_boundary_ink("f", (0, 0, 0), 0.42), "a fill is not stroke ink"
    assert not is_boundary_ink("s", None, 0.42), "no color record, no class"
    import bluehouse_plan_reader as R
    assert not hasattr(R, "PANEL_PEN_PT") and not hasattr(R, "is_panel_pen"), \
        "the 0.42 pen table must not resurrect under its old name"


def test_a_window_spanning_BOTH_leaves_of_a_double_leaf_wall_is_boundary_ink():
    """Pandora draws a 200 mm wall as two abutting 100 mm leaves. The window rect spans both,
    so it fits NEITHER leaf's face pair alone -- before composite pairs existed it was rejected
    as 'not band-aligned' and the opening read as a hole the flood escaped through."""
    runs = {("h", 0.0, 100.0): [(0.0, 8000.0)], ("h", 100.0, 199.0): [(0.0, 8000.0)]}
    comp = composite_run_keys(runs)
    assert comp == [(("h", 0.0, 199.0), (0.0, 8000.0))]
    keys = run_keys(runs)
    win = (3570.0, 0.0, 6770.0, 199.0)
    assert band_aligned(win, keys) is None, "no single leaf fits -- this is the old miss"
    assert band_aligned(win, keys, composite=comp) == ("h", 0.0, 199.0)
    leaf = (3570.0, 0.0, 4440.0, 870.0)
    assert band_aligned(leaf, keys, composite=comp) is None, \
        "a swinging door leaf still sticks out perpendicular and is still rejected"


def test_composite_pairs_need_a_cavity_not_a_corridor():
    """60 mm merges the leaves of one wall (Pandora abuts at 0 mm; 304149's cavity is wider
    than 2 mm). It must NOT merge two rooms' walls across a corridor, must NOT mint a band
    wider than a real wall, and a lone leaf is no composite."""
    ext = [(0.0, 8000.0)]
    runs = {("h", 0.0, 100.0): ext, ("h", 150.0, 250.0): ext,
            ("h", 1200.0, 1300.0): ext, ("v", 0.0, 100.0): ext}
    assert composite_run_keys(runs) == [(("h", 0.0, 250.0), (0.0, 8000.0))], \
        "a 50 mm cavity is one wall; a 950 mm corridor is two; a lone leaf is no composite"
    fat = {("h", 0.0, 100.0): ext, ("h", 150.0, 400.0): ext}
    assert composite_run_keys(fat) == [], \
        "a 400 mm 'wall' is wider than MAX_COMPOSITE_MM: a band furniture can hide in is not a wall"
    # this case is blocked by the TOL alone (width 290 clears the cap): it is the one that goes
    # RED when WALL_CAVITY_TOL_MM is widened -- the corridor case above is ALSO cap-blocked, so
    # without this a tol mutation would be invisible (two vetoes masking each other)
    near = {("h", 0.0, 100.0): ext, ("h", 190.0, 290.0): ext}
    assert composite_run_keys(near) == [], "a 90 mm gap between coextensive leaves is not a cavity"


def test_two_walls_that_NEVER_COEXIST_along_the_axis_are_not_one_wall():
    """THE EXTENT CLAUSE (review 2026-07-14, MAJOR x2 -- found independently by two lenses).
    The first composite merge used face coordinates alone; on the real corpus that chained
    unrelated parallel walls (51 mm face-steps between different rooms' walls) into 301-701 mm
    pseudo-wall bands, inside which ANY black ink -- furniture edges, counters -- became
    boundary ink for EVERY chained leaf's gaps. Real double-leaf walls are COEXTENSIVE; walls
    with disjoint long extents are strangers however close their thin coordinates land."""
    disjoint = {("h", 0.0, 100.0): [(0.0, 4000.0)], ("h", 150.0, 250.0): [(6000.0, 9000.0)]}
    assert composite_run_keys(disjoint) == [], \
        "west-wing wall + east-wing wall at a 50 mm face-step are NOT one double-leaf wall"
    # and no transitive chaining: three coextensive leaves make TWO adjacent pairs, never one
    # triple-width band (the old chain reached 701 mm on the corpus)
    triple = {("h", 0.0, 100.0): [(0.0, 5000.0)], ("h", 130.0, 230.0): [(0.0, 5000.0)],
              ("h", 260.0, 360.0): [(0.0, 5000.0)]}
    assert composite_run_keys(triple) == \
        [(("h", 0.0, 230.0), (0.0, 5000.0)), (("h", 130.0, 360.0), (0.0, 5000.0))]
    # a composite that duplicates an EXISTING plain key is dropped: the plain run already
    # aligns everything the pair would, and the duplicate made via_composite LIE (168
    # mislabeled panels on 6 corpus pages before this)
    nested = {("h", 0.0, 100.0): [(0.0, 5000.0)], ("h", 0.0, 200.0): [(0.0, 5000.0)]}
    assert composite_run_keys(nested) == []
    # ink OUTSIDE the overlap span does not ride the composite: one leaf there is just a wall
    part = {("h", 0.0, 100.0): [(0.0, 9000.0)], ("h", 100.0, 199.0): [(0.0, 3000.0)]}
    comp = composite_run_keys(part)
    assert comp == [(("h", 0.0, 199.0), (0.0, 3000.0))]
    keys = run_keys(part)
    inside = (1000.0, 0.0, 2000.0, 199.0)
    outside = (5000.0, 0.0, 6000.0, 199.0)
    assert band_aligned(inside, keys, composite=comp) == ("h", 0.0, 199.0)
    assert band_aligned(outside, keys, composite=comp) is None, \
        "at x=5000 only ONE leaf exists: 199 mm-deep ink there is furniture, not a window"


def test_composite_ink_backs_BOTH_leaves_gaps_but_not_the_far_wall():
    """One window rect aligned to the composite pair must back the gap in EACH leaf's run
    (each leaf has its own hole where the wall pen stopped), and must still back nothing on a
    different wall -- containment, not proximity."""
    span = {"gap_lo": 0.0, "gap_hi": 1000.0, "length_mm": 1000.0}
    g_left = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, **span}
    g_right = {"axis": "h", "face_lo": 100.0, "face_hi": 199.0, **span}
    g_far = {"axis": "h", "face_lo": 9620.0, "face_hi": 9720.0, **span}
    g_vert = {"axis": "v", "face_lo": 0.0, "face_hi": 100.0, **span}
    ink = [{"rect": (0.0, 0.0, 800.0, 199.0), "run": ("h", 0.0, 199.0), "w": 0.48}]
    assert gap_coverage(g_left, ink) == pytest.approx(0.8)
    assert gap_coverage(g_right, ink) == pytest.approx(0.8)
    assert gap_coverage(g_far, ink) == 0.0, "ink on the far wall must not back this gap"
    assert gap_coverage(g_vert, ink) == 0.0, "an h-run's ink must not back a v gap"


def test_an_opening_REPORTS_the_pens_that_back_it():
    """The class no longer filters on width, so the width evidence must be VISIBLE: an opening
    whose only backing is 0.12-pt hairline must say so in its own record, largest ink first.
    The hairline is deliberately FIRST in the fixture: with the sort deleted, insertion order
    would win and the 'largest first' half of this test could never fail (review 2026-07-14)."""
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 5000.0, "gap_hi": 5900.0,
         "length_mm": 900.0}
    boundary = [{"rect": (5000.0, 0.0, 5450.0, 100.0), "run": ("h", 0.0, 100.0), "w": 0.12},
                {"rect": (5000.0, 0.0, 5900.0, 100.0), "run": ("h", 0.0, 100.0), "w": 0.48}]
    _infill, openings, _voids = resolve_gaps([g], boundary)
    assert openings and list(openings[0]["ink_pens"].items()) == \
        [("0.48", 900.0), ("0.12", 450.0)], "largest ink FIRST, as an ordered fact"
    assert list(gap_pen_mm(g, boundary).items()) == [("0.48", 900.0), ("0.12", 450.0)]
    assert openings[0]["composite_backed_mm"] == 0.0, \
        "plain-run backing reports zero composite mm -- the field exists either way"
    # and the honest channel is untouched: no ink of any pen still means VOID
    bare = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 0.0, "gap_hi": 3200.0,
            "length_mm": 3200.0}
    _i, o, v = resolve_gaps([bare], boundary)
    assert not o and v and "ink_pens" not in v[0], "a void reports no pens -- it has none"


def test_a_crossing_line_cannot_cut_a_stub_open():
    """THE PANDORA p8 FABRICATION (review 2026-07-14, MAJOR, measured live). A 99 mm wall stub
    was 'backed' at coverage 1.0 by a single 2551 mm polyline that CROSSES it -- dimension/grid
    ink, not a drawn opening -- and the coverage branch ran before the stub branch, so the wall
    was cut open. Corpus truth: 59 honest sub-400 mm openings all have jamb-terminated backers
    (overshoot <= 4.2 mm); the one crossing backer overshoots 2451 mm. A stub opens only on ink
    that terminates at its jambs; refused crossing ink is LOGGED, never silently dropped."""
    stub = {"axis": "v", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 5000.0, "gap_hi": 5099.4,
            "length_mm": 99.4}
    crossing = [{"rect": (0.0, 3800.0, 0.0, 6350.6), "run": ("v", 0.0, 100.0), "w": 0.38}]
    infill, openings, voids = resolve_gaps([stub], crossing)
    assert not openings and not voids and len(infill) == 1, \
        "a stub crossed by a long line is a BRIDGED stub, not a cut"
    assert infill[0]["crossing_ink_refused"] is True
    assert infill[0]["crossing_ink_pens"] == {"0.38": 99.4}, \
        "the refusal carries its evidence: what crossed, clipped to the gap"
    # the SAME stub with a jamb-terminated backer is a real opening (frame member / threshold)
    jamb = [{"rect": (0.0, 4999.0, 0.0, 5100.0), "run": ("v", 0.0, 100.0), "w": 0.38}]
    infill2, openings2, _v2 = resolve_gaps([stub], jamb)
    assert not infill2 and len(openings2) == 1 and openings2[0]["ink_pens"] == {"0.38": 99.4}, \
        "corpus: 59 of 60 sub-400mm openings are real -- jamb-terminated ink still cuts"
    # gaps at/above CLOSE_TOL are untouched by the stub rule: the golden sheet's 1110 mm stair
    # gap is backed by a full-length edge line (overshoot 0) and long-gap coverage still rules
    door = {"axis": "v", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 5000.0, "gap_hi": 5900.0,
            "length_mm": 900.0}
    _i3, openings3, _v3 = resolve_gaps([door], crossing)
    assert len(openings3) == 1, "long gaps keep the plain >=60% coverage rule"


def test_an_opening_that_exists_only_through_a_COMPOSITE_pair_says_so():
    """The composite mechanism is the newest, most permissive door into the boundary class --
    so its share of every opening's backing must be VISIBLE downstream (review 2026-07-14:
    via_composite used to die at a sheet-level note; 50 of 256 corpus openings exist only
    through it and were indistinguishable from plain-backed ones)."""
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 3570.0, "gap_hi": 6770.0,
         "length_mm": 3200.0}
    win = [{"rect": (3570.0, 0.0, 6770.0, 199.0), "run": ("h", 0.0, 199.0), "w": 0.48,
            "via_composite": True}]
    _i, openings, _v = resolve_gaps([g], win)
    assert len(openings) == 1
    assert openings[0]["composite_backed_mm"] == 3200.0
    assert gap_composite_mm(g, win) == 3200.0
    ops = type_openings(openings, set(), (0.0, 0.0), [])
    assert ops[0]["composite_backed_mm"] == 3200.0, "the evidence rides INTO the emitted record"
    assert "composite double-leaf pair" in ops[0]["provenance"]


def test_flood_region_LEAKS_through_a_hole_and_says_so():
    """The closure metric must be able to fail. A box with a 1 m hole in it is not a room."""
    box = [(0, 0, 100, 3000), (3000, 0, 3100, 3000), (0, 0, 3100, 100), (0, 2900, 3100, 3000)]
    env = (-1000.0, -1000.0, 4100.0, 4000.0)
    _, _, _, _, leaked = flood_region(box, (1500, 1500), env)
    assert not leaked, "the intact box contains the flood"
    holed = [b for b in box if b != (0, 0, 3100, 100)] + [(0, 0, 1000, 100), (2000, 0, 3100, 100)]
    _, _, _, _, leaked2 = flood_region(holed, (1500, 1500), env)
    assert leaked2, "a 1 m hole in the south wall must LEAK -- the 'room' is the outdoors"


def test_flood_refuses_a_seed_inside_a_wall():
    with pytest.raises(RefuseSheet, match="INSIDE wall ink"):
        flood_region([(0, 0, 100, 3000)], (50, 1500), (-500.0, -500.0, 3000.0, 3000.0))


def test_trace_contours_and_snap_return_the_box_it_flooded():
    box = [(0, 0, 100, 3000), (3000, 0, 3100, 3000), (0, 0, 3100, 100), (0, 2900, 3100, 3000)]
    env = (-500.0, -500.0, 3600.0, 3500.0)
    filled, origin, _, _, _ = flood_region(box, (1500, 1500), env)
    loops = trace_contours(filled, origin)
    xs = sorted({b[0] for b in box} | {b[2] for b in box})
    ys = sorted({b[1] for b in box} | {b[3] for b in box})
    poly = set(snap_polygon(loops[0], xs, ys))
    assert {(100.0, 100.0), (3000.0, 100.0), (3000.0, 2900.0), (100.0, 2900.0)} <= poly


def test_audit_sides_REPORTS_an_unbacked_edge():
    """THE anti-flattering-scorer, and it CAUGHT A REAL BUG when it was written.

    A polygon can be closed and still have a side backed by nothing. Here the south wall is real
    ink, the north is an owner-signed virtual edge, and the EAST AND WEST ARE NOTHING AT ALL.

    Before the fix, east came back with 200 of its 2000 mm "backed": the south and north rects
    RUN ALONG x and their ENDS land on x=3000, and the match test read an end as a face. The
    audit built to catch fabricated walls was itself crediting 100 mm of fabrication per corner."""
    outline = [(0.0, 0.0), (3000.0, 0.0), (3000.0, 2000.0), (0.0, 2000.0)]
    backing = [([0.0, 0.0, 3000.0, 100.0], "wall_poche"),          # south: real
               ([0.0, 1900.0, 3000.0, 2000.0], "signed_virtual")]  # north: NOT ink
    sides = audit_sides(outline, backing)
    south = next(s for s in sides if s["edge"] == [[0.0, 0.0], [3000.0, 0.0]])
    north = next(s for s in sides if s["edge"] == [[3000.0, 2000.0], [0.0, 2000.0]])
    east = next(s for s in sides if s["edge"] == [[3000.0, 0.0], [3000.0, 2000.0]])
    assert south["backing"] == {"wall_poche": 3000.0} and south["unbacked_mm"] == 0.0
    assert north["backing"] == {"signed_virtual": 3000.0}, "a signed wall is NOT ink"
    assert east["unbacked_mm"] == 2000.0, "the east side is backed by NOTHING and must say so"
    assert east["backing"] == {}, "no corner-touch may be laundered into backing"


def test_audit_sides_still_credits_a_real_corner_block():
    """The thinness rule must not throw the baby out: a 100x100 corner block is thin on BOTH
    axes and is real ink, so it legitimately backs whichever edge it sits on."""
    outline = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]
    sides = audit_sides(outline, [([1000.0, 0.0, 1100.0, 100.0], "wall_poche")])
    east = next(s for s in sides if s["edge"] == [[1000.0, 0.0], [1000.0, 1000.0]])
    assert east["backing"] == {"wall_poche": 100.0}


def test_audit_sides_credits_poche_before_infill_so_a_side_cannot_be_double_counted():
    outline = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]
    backing = [([0.0, 0.0, 1000.0, 100.0], "wall_poche"),
               ([0.0, 0.0, 1000.0, 100.0], "closure_infill")]      # same span, twice
    south = audit_sides(outline, backing)[0]
    assert south["backing"] == {"wall_poche": 1000.0} and south["backed_mm"] == 1000.0


def test_parse_virtual_edge_REFUSES_an_invented_coordinate():
    """An owner may sign a wall the sheet does not draw. They may NOT invent where it is: all
    four numbers must be existing wall faces."""
    bands = [(3020.0, 0.0, 3120.0, 3485.0), (0.0, 4970.0, 7720.0, 5069.0)]
    ve = parse_virtual_edge("h:4970:5069:3120:7720", bands)
    assert ve["length_mm"] == 4600.0 and ve["ink_coverage"] == 0.0
    assert ve["snapped"] is False
    with pytest.raises(RefuseSheet, match="not a wall face"):
        parse_virtual_edge("h:4970:5069:3120:6543", bands)     # 6543 is on no wall face
    with pytest.raises(RefuseSheet, match="want AXIS"):
        parse_virtual_edge("garbage", bands)


# ====================================================== ROUND 3, FATAL 2: the audit was FABRICATING
def test_audit_sides_does_NOT_credit_the_blank_half_of_a_half_drawn_opening():
    """FATAL 2. audit_sides was handed gap_rect(g) -- the opening's FULL footprint -- as backing,
    regardless of that opening's ink_coverage. A 1000 mm hole with 600 mm of glazing ink was
    credited as 1000 mm of wall. Up to 40% of EVERY opening laundered as ink, INSIDE the audit
    built to catch exactly that. Now an opening backs only the mm it inks."""
    outline = [(0.0, 0.0), (2000.0, 0.0), (2000.0, 1000.0), (0.0, 1000.0)]
    gap = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 1000.0, "gap_hi": 2000.0,
           "length_mm": 1000.0}
    boundary = [{"rect": (1000.0, 20.0, 1600.0, 30.0), "run": ("h", 0.0, 100.0)}]   # 600 of 1000
    assert gap_coverage(gap, boundary) == pytest.approx(0.6)
    ink = gap_ink_rects(gap, boundary)
    assert ink == [[1000.0, 0.0, 1600.0, 100.0]], "only the INKED span backs the wall"
    backing = [([0.0, 0.0, 1000.0, 100.0], "wall_poche")] + [(r, "opening") for r in ink]
    south = audit_sides(outline, backing)[0]
    assert south["backing"] == {"wall_poche": 1000.0, "opening": 600.0}
    assert south["unbacked_mm"] == 400.0, "the 400 mm of blank paper must SHOW"
    # the round-2 behaviour, for the record: crediting gap_rect() gives a perfect, false, 0.0
    old = audit_sides(outline, [([0.0, 0.0, 1000.0, 100.0], "wall_poche"),
                                (gap_rect(gap), "opening")])[0]
    assert old["unbacked_mm"] == 0.0, "this is the bug it had: it read as fully backed"


# ========================================== ROUND 3, FATAL 3: pins that could not fail, and now can
def test_the_polygon_snap_is_CONDITIONAL_because_GRID_exceeds_SNAP_TOL():
    """FATAL 3(a). GRID_MM=25 < SNAP_TOL_MM=30 made snap_polygon unconditional: the flood contour
    lies within step/2 of the solid, so EVERY vertex was inside snapping distance of a face no
    matter where the solid actually was -- and test_every_room_vertex_lands_on_a_real_wall_FACE
    was a TAUTOLOGY. The ordering is now itself a pin.

    ROUND 4, D3 -- THIS PIN WAS *ITSELF* A TAUTOLOGY AND DID NOT BIND THE CONSTANT IT PROTECTS.
    MEASURED: restore `def snap_polygon(..., tol=30.0)` (leaving SNAP_TOL_MM=20, so the module
    assert stays quiet) and the whole suite still reported 89 passed, 0 failed. Why: the old probe
    sat 60 mm off the face and the mutation wall 40 mm off, and BOTH are outside tol=20 AND
    tol=30, so neither probe could tell 20 from 30. A pin whose probes do not straddle the
    boundary it defends is decoration.

    The probes now land INSIDE the discriminating band 20 < d <= 30, which is the ONLY band in
    which the two constants disagree.
    """
    assert GRID_MM > SNAP_TOL_MM
    # THE FUNCTION'S ACTUAL DEFAULT, not just the module constant: FATAL 3(a) was reintroduced by
    # hardcoding a literal in the signature while the constant stayed innocent at 20.
    assert inspect.signature(snap_polygon).parameters["tol"].default == SNAP_TOL_MM, \
        "snap_polygon's tol default must BE the constant, not a literal that can drift from it"
    xs, ys = [0.0, 1000.0], [0.0, 1000.0]
    assert snap_polygon([(1005.0, 0.0)], xs, ys) == [(1000.0, 0.0)], "a near vertex still snaps"
    # 25 mm off the 1000 face: INSIDE the old tol(30), OUTSIDE the live tol(20). This is the probe
    # that actually binds the constant -- it goes RED the moment tol climbs back over 25.
    assert snap_polygon([(1025.0, 0.0)], xs, ys) == [(1025.0, 0.0)], \
        ("a vertex 25 mm off the face is LEFT WHERE IT IS. If this snapped to 1000, SNAP_TOL has "
         "regressed past GRID/2 + the contour error and the vertex pin is unconditional again.")
    assert snap_polygon([(1060.0, 0.0)], xs, ys) == [(1060.0, 0.0)], \
        "a vertex further than SNAP_TOL from any face is LEFT WHERE IT IS -- so the pin can fire"


def test_the_VERTEX_PIN_CAN_FAIL_a_fabricated_wall_is_caught():
    """THE MUTATION. Same bands, same seed -- but the room is closed on a FABRICATED rect sitting
    at no ink face. The derived polygon KEEPS that coordinate, and `every vertex is a wall face`
    now FAILS on it. Under round 2's SNAP_TOL(30) > GRID(25) the vertex was silently pulled onto
    3000 and the pin passed.

    ROUND 4, D3: the fabricated wall was at 2960 -- 40 mm off the real 3000 face -- which survives
    the snap under tol=20 AND under tol=30, so this "mutation" test passed under the very bug it
    claimed to prove was fixed. It is now at 2975: 25 mm off, i.e. INSIDE the regressed tol(30)
    and OUTSIDE the live tol(20). Regress the constant and this test goes RED, because the snap
    quietly launders the fabricated wall onto the real face and `not all_on_faces(fabricated)`
    stops being true."""
    bands = [(0.0, 0.0, 3100.0, 100.0),        # south
             (0.0, 2000.0, 3100.0, 2100.0),    # north
             (0.0, 0.0, 100.0, 2100.0),        # west
             (3000.0, 0.0, 3100.0, 2100.0)]    # east  -> faces x: 0, 100, 3000, 3100
    honest = derive_room_polygon(bands, [list(b) for b in bands], (1500.0, 1000.0))
    fabricated = derive_room_polygon(
        bands, [list(b) for b in bands[:3]] + [[2975.0, 0.0, 3100.0, 2100.0]], (1500.0, 1000.0))
    faces_x = {b[0] for b in bands} | {b[2] for b in bands}

    def all_on_faces(room):
        return all(any(abs(x - f) < 0.5 for f in faces_x) for x, _ in room["outline_mm"])

    assert all_on_faces(honest), "the honest room passes the pin"
    assert not all_on_faces(fabricated), \
        "the fabricated 2975 wall must SURVIVE into the outline so the vertex pin catches it"
    assert any(abs(x - 2975.0) <= GRID_MM for x, _ in fabricated["outline_mm"])


def test_a_signed_edge_OFF_THE_FACE_is_SNAPPED_onto_it_and_the_delta_is_REPORTED():
    """FATAL 3(b). parse_virtual_edge VALIDATED against a real face and then used the number the
    human TYPED. Signing 4980 (10 mm off the real 4970 face) moved the wall, the room grew, and
    unbacked_perimeter still read 0.2 mm because the (unconditional) polygon snap cleaned up after
    it. A validator that does not BIND the value it validated is a rubber stamp."""
    bands = [(3020.0, 0.0, 3120.0, 3485.0), (0.0, 4970.0, 7720.0, 5069.0)]
    ve = parse_virtual_edge("h:4980:5069:3120:7720", bands)
    assert ve["face_lo"] == 4970.0, "the coordinate is BOUND to the ink face, not to the typing"
    assert ve["snapped"] is True and ve["snap_deltas_mm"]["face_lo"] == -10.0
    assert "SNAPPED" in ve["snap_note"]


def test_a_signed_edge_BEYOND_the_snap_tolerance_is_REFUSED_outright():
    """25 mm off a real face -- the review's exact mutation. With SNAP_TOL_MM=20 it is now past
    tolerance and REFUSED. Round 2 (tol 30) accepted it and grew the room silently."""
    bands = [(3020.0, 0.0, 3120.0, 3485.0), (0.0, 4970.0, 7720.0, 5069.0)]
    with pytest.raises(RefuseSheet, match="not a wall face"):
        parse_virtual_edge("h:4995:5069:3120:7720", bands)


# ========================================== ROUND 3, FATAL 1: the room-spec dropped its own openings
def test_openings_on_outline_finds_the_openings_a_room_can_see_out_of():
    """FATAL 1. The room-spec was {"outline_mm","ceiling_mm"} and the openings were DROPPED, so the
    living zone rendered as floor + 4 blank walls -- a SEALED SHOEBOX -- even though the reader had
    measured its 3200 slider and its 2900 slider out of the ink."""
    outline = [(0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0), (0.0, 3000.0)]
    ops = [{"id": "O00", "type": "sliding", "rect": [1000.0, -100.0, 4000.0, 0.0]},   # on south
           {"id": "O01", "type": "door", "rect": [4000.0, 500.0, 4100.0, 1400.0]},    # on east
           {"id": "O02", "type": "door", "rect": [1000.0, 1400.0, 1900.0, 1500.0]}]   # interior
    got = openings_on_outline(outline, ops)
    assert [o["id"] for o in got] == ["O00", "O01"], "an interior partition is NOT this room's edge"
    assert got[0]["on_edge"] == [[0.0, 0.0], [4000.0, 0.0]]


def test_type_openings_reads_the_flood_not_a_length_threshold():
    """Envelope (floor on ONE side) -> glazed; partition (floor on BOTH) -> door. The 0.30 leaf
    pen inside the hole is what separates a slider from a fixed window."""
    origin, step = (0.0, 0.0), 25.0
    inside = {(i, j) for i in range(4, 40) for j in range(8, 40)}     # floor NORTH of y=100 only
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 200.0, "gap_hi": 900.0,
         "length_mm": 700.0, "ink_coverage": 1.0}
    win = type_openings([g], inside, origin, leaf_rects=[])[0]
    sld = type_openings([g], inside, origin,
                        leaf_rects=[(300.0, 20.0, 800.0, 30.0), (300.0, 60.0, 800.0, 70.0)])[0]
    assert win["type"] == "window" and win["context"] == "envelope"
    assert sld["type"] == "sliding" and sld["leaf_pen_paths"] == 2
    assert win["signed"] is False, "type is a mechanical rule, not a measurement"
    assert set(win) >= {"id", "type", "rect"}, "the keys floor_openings.py consumes"


# ================================================================= floor_openings CONSUMPTION
def test_openings_are_consumable_by_floor_openings_without_a_KeyError():
    """Round 1 emitted {axis, face_lo, face_hi, gap_lo, gap_hi, length_mm}. floor_openings.py
    wants {id, type, rect} -> KeyError, and a signed opening could never reach the wall-cut/glass
    machinery. This test is the contract."""
    inside = {(i, j) for i in range(4, 40) for j in range(8, 40)}
    g = {"axis": "h", "face_lo": 0.0, "face_hi": 100.0, "gap_lo": 200.0, "gap_hi": 900.0,
         "length_mm": 700.0, "ink_coverage": 1.0}
    ops = type_openings([g], inside, (0.0, 0.0), leaf_rects=[])
    walls = [[[0.0, 50.0], [3000.0, 50.0]]]
    kept, n_cuts = clip_wall_segments(walls, ops)          # would KeyError on the old schema
    assert n_cuts == 1, "the wall is CUT where the opening lives"
    assert sorted(round(min(a[0], b[0])) for a, b in kept) == [0, 900]
    boxes = opening_boxes(ops[0], ceiling_mm=3000.0)
    assert [b["kind"] for b in boxes] == ["wall", "glass", "wall"], "sill + pane + lintel"


# ================================================================= carry
def test_unsigned_glazing_candidates_are_machine_inert():
    prior = {"manual_additions": {"by": "OWNER-CONFIRM-PENDING", "reason": "2 openings",
                                  "segments": [[[0, 0], [3200, 0]]]}}
    new = {"scale_mm_per_pt": SCALE_50, "segments": [[[0, 0], [100, 0]]], "n": 1}
    out, notes = merge_carried(new, prior)
    assert out["n"] == 1 and len(out["segments"]) == 1, "kept as a record, NOT injected"
    assert any("UNSIGNED" in n for n in notes)


def test_a_signed_opening_does_get_injected():
    prior = {"manual_additions": {"by": "owner:peat 2026-07-12", "segments": [[[0, 0], [3200, 0]]]},
             "scale_mm_per_pt": SCALE_50, "origin_pt": [1, 2], "source_pdf": "a.pdf", "page": 3}
    new = {"scale_mm_per_pt": SCALE_50, "origin_pt": [1, 2], "source_pdf": "a.pdf", "page": 3,
           "segments": [[[0, 0], [100, 0]]], "n": 1}
    assert merge_carried(new, prior)[0]["n"] == 2


# ================================================================= SYNTHETIC PDFs (committable:
# no client geometry). The client sheet contains NO scale disagreement -- both its plan pages say
# 1:50 AND measure 1:50 -- so round 1's half-size bug cannot be demonstrated on it at all. That is
# how it survived. We synthesise the disagreement instead.
@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    pytest.importorskip("fitz")
    from synth_plan_pdf import write_all
    return write_all(str(tmp_path_factory.mktemp("synth")))


def test_synthetic_GOOD_plan_is_ACCEPTED(synth):
    """THE CONTROL. Without it, 'the gate refuses everything' would pass every refusal test."""
    from bluehouse_plan_reader import build
    meta, _ = build(synth["good"], 0)
    assert meta["provenance"]["n_bands"] == 16
    assert meta["scale_mm_per_pt"] == pytest.approx(17.63889, abs=1e-4)
    assert all(c["ok"] for c in meta["provenance"]["page_gate"])


def test_synthetic_HALF_SCALE_sheet_is_REFUSED(synth):
    """200 mm walls, title block still says 1:50. Round 1 emitted this at HALF SIZE."""
    from bluehouse_plan_reader import build
    with pytest.raises(RefuseSheet, match="SCALE DISAGREEMENT"):
        build(synth["halfscale"], 0)


def test_synthetic_NO_SCALE_sheet_is_REFUSED(synth):
    from bluehouse_plan_reader import build
    with pytest.raises(RefuseSheet, match="states NO scale"):
        build(synth["noscale"], 0)


def test_the_reader_refuses_to_be_handed_a_scale(synth):
    """--scale is gone. A hand-typed mm/pt is the fail-open path, wearing a hat."""
    from bluehouse_plan_reader import build
    with pytest.raises(RefuseSheet, match="--scale is GONE"):
        build(synth["good"], 0, scale_override=17.63889)


def test_synthetic_A4_EXPORT_reads_the_SAME_building_as_the_A3(synth):
    """THE ANTI-HALF-SIZE TRIPWIRE, in a form that can be committed (no client geometry).

    a4export.pdf is good.pdf photographically reduced by 1/sqrt(2) -- the whole page, TITLE BLOCK
    INCLUDED -- while the title block goes on printing the A3 original's '1 : 50'. That is exactly
    what the office's exporter does to 116 of the corpus's 898 pages.

    Both sheets are the SAME 8000 x 6000 mm building. If the sheet shrink is not read off the border,
    the A4 one reads 5657 x 4243 mm and the gate's own scoreboard CANNOT TELL: measured, a wrong fix
    (widen WALL_MM_LO so 70.9 mm counts as a wall) scores identically on accepted-count, recall and
    false-accepts while emitting the building at 0.7071x. Recall and false-accepts are blind to a
    scale error. Only an ABSOLUTE dimension is not. This is that dimension."""
    def extent_mm(path):
        bands_pt, _st, scale, denom, _m, _tb, _c, _n = read_bands(path, 0)
        bands = to_mm_bands(bands_pt, scale, 0.0, 0.0)
        return (max(b[2] for b in bands) - min(b[0] for b in bands),
                max(b[3] for b in bands) - min(b[1] for b in bands), scale, denom)

    w3, h3, sc3, d3 = extent_mm(synth["good"])
    w4, h4, sc4, d4 = extent_mm(synth["a4export"])
    assert d3 == d4 == 50, "both title blocks state 1:50 -- the denominator is NOT what changes"
    assert abs(sc4 / sc3 - math.sqrt(2)) < 0.01, (
        "mm-per-PAGE-pt must be sqrt(2)x larger on the A4 export: same building, smaller paper")
    assert abs(w3 - 8000) < 15 and abs(h3 - 6000) < 15, f"A3 reads {w3:.0f}x{h3:.0f}, want 8000x6000"
    assert abs(w4 - 8000) < 15 and abs(h4 - 6000) < 15, (
        f"the A4 export reads {w4:.0f}x{h4:.0f} mm -- the same building the A3 reads as "
        f"{w3:.0f}x{h3:.0f}. A ratio near 0.7071 means the sheet shrink was never applied.")


# ============================================================== THE PAPER (A3 art exported to A4)
def test_sheet_shrink_recognises_the_two_paper_steps():
    """The office DRAWS on A3 and sometimes EXPORTS at A4 -- the whole page, title block included,
    shrinks 1/sqrt(2) while the title block goes on printing the A3 original's scale. 116 of the
    corpus's 898 pages are such exports, and S1 was refusing all of them for the RIGHT reason: at the
    stated scale their 100 mm walls read 70.9 mm. The wall was never wrong. The PAPER was."""
    s, why = sheet_shrink((1122.45, 773.85))
    assert s == 1.0 and "1.0000x the A3 design sheet" in why
    s, why = sheet_shrink((793.7, 547.2))                    # the measured A4 export
    assert abs(s - 1 / math.sqrt(2)) < 1e-6 and "A3 ART EXPORTED TO A4" in why


def test_sheet_shrink_is_FAIL_CLOSED_and_never_interpolates():
    """"The wall came out plausible" is NOT evidence: WALL_MM_PLAUSIBLE spans 80-260 mm, and a 15%
    scale error hides inside that window comfortably. So an unknown reduction REFUSES."""
    with pytest.raises(RefuseSheet, match="no sheet border"):
        sheet_shrink(None)
    with pytest.raises(RefuseSheet, match="not a known paper step"):
        sheet_shrink((950.0, 655.0))          # 0.846x -- a real reduction, but not a paper step
    with pytest.raises(RefuseSheet, match="ANISOTROPIC"):
        sheet_shrink((793.7, 700.0))          # stretched: mm-per-pt is not one number


def test_resolve_scale_needs_the_shrink_and_a_dropped_arg_is_caught():
    """A 100 mm wall on an A4 export is 4.02 pt. At the title block's stated 1:50 that is 70.9 mm --
    not a wall -- so the un-shrunk call must REFUSE. Pass the shrink and the same ink calibrates."""
    with pytest.raises(RefuseSheet):
        resolve_scale([4.02] * 20, 50, 1.0)
    scale, denom, modal, note = resolve_scale([4.02] * 20, 50, 1 / math.sqrt(2))
    assert denom == 50 and abs(scale - 24.945) < 0.01, "mm per PAGE pt, not per design pt"
    assert abs(modal * scale - 100.3) < 1.0, "the wall is 100 mm once the paper is accounted for"


def test_widening_the_wall_family_would_DISARM_the_half_size_veto():
    """THE FIX THAT LOOKS RIGHT AND IS NOT. It is tempting to answer 'the wall might be 200 mm' by
    widening the hypothesis set to {100,150,200,250}. MEASURED: that MANUFACTURES the ambiguity that
    disarms this veto. 11.34 pt with a stated 1:50 is SIMULTANEOUSLY a 200 mm wall at a true 1:50 and
    a 100 mm wall at a true 1:25 -- the ink is identical, and nothing in it can tell them apart.

    Under the single-100 hypothesis the snap says "1:25 only", disagrees with the title block, and
    REFUSES -- which is exactly right, because this is the half-size trap round 1 fell into. Under
    the widened family the snap says "1:25 or 1:50", the title block's 50 is IN the set, and the
    sheet is ACCEPTED. It buys 1 corpus page and sells the veto. (Also: there IS no 200 mm wall in
    this corpus -- 85.7% of 3,006 wall quads are 100 mm, and the suspected 200 mm hospital party wall
    measures 98.4-101.6 mm at 1:150.)"""
    assert geometry_snap([11.34] * 20)[1] == [25], "single-100: this ink is a wall ONLY at 1:25"
    with pytest.raises(RefuseSheet, match="SCALE DISAGREEMENT"):
        resolve_scale([11.34] * 20, 50, 1.0)

    widened = [d for d in CANDIDATE_DENOMS
               if any(WALL_MM_LO <= 11.34 * PT_MM * d / (t / 100.0) <= WALL_MM_HI
                      for t in (100, 150, 200, 250))]
    assert 50 in widened and 25 in widened, (
        "the widened family admits BOTH -- so the title block's 50 would pass the veto and the "
        "half-size sheet would build. This assertion documents WHY the family stays at 100.")


# ================================================================= ACCEPTANCE PINS (real sheet)
PDF = ("_private/discord/MY-DATA-PEAT/โปรเจ็ก/012_I-24-004-Kนุช-บ้าน-Villa-Valley-สุระ-2/"
       "files/654446_I-24-004-K._VillaValley_2-_-01.pdf")
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PDF_ABS = os.path.join(_REPO, PDF)
real_pdf = pytest.mark.skipif(not os.path.exists(_PDF_ABS),
                              reason="client PDF not present (gitignored)")

# --- THE ANTI-HALF-SIZE TRIPWIRE. The SAME condo unit, drawn once, exported twice: A3 and A4.
# THIS IS THE ONLY TEST IN THE SUITE THAT CAN CATCH A SCALE ERROR, and the gate's own scoreboard
# provably cannot. MEASURED: a WRONG fix (widen WALL_MM_LO 95->65 so 70.9 mm counts as a wall)
# scores IDENTICALLY on every number the gate reports -- 27 accepted, STOREY recall 50.9%,
# false-accepts 0 -- while emitting this 8.0 x 8.0 m unit as 5657 x 5656 mm. Recall and
# false-accepts are BLIND to a building at 1/sqrt(2) size. Only an ABSOLUTE dimension is not.
A3_TWIN = ("_private/discord/MY-DATA-PEAT/update/004_I-24-043-Pandora-Condo/"
           "files/519482_I-24-043-Pandora-PDF-_11.pdf", 5)
A4_TWIN = ("_private/discord/MY-DATA-PEAT/โปรเจ็ก/024_I-24-043-PandoraCondo/"
           "files/679283_I-24-043-pandora-A1--01.pdf", 20)
_twins_here = all(os.path.exists(os.path.join(_REPO, p)) for p, _ in (A3_TWIN, A4_TWIN))
twin_pdfs = pytest.mark.skipif(not _twins_here, reason="client PDFs not present (gitignored)")


@twin_pdfs
def test_the_A4_export_and_the_A3_original_agree_on_the_SAME_unit():
    """Same project, same unit, two exports. If the paper is handled right they are the same
    building; if it is not, one of them is 0.7071x the other and nothing else in the suite notices.

    Measured: PASS at delta 1 mm / 3 mm. On the wrong fix: FAILS at delta 2342 mm / 2345 mm."""
    def extent_mm(pdf, page):
        bands_pt, _steps, scale, _d, _m, _tb, _c, _n = read_bands(os.path.join(_REPO, pdf), page)
        bands = to_mm_bands(bands_pt, scale, 0.0, 0.0)
        return (max(b[2] for b in bands) - min(b[0] for b in bands),
                max(b[3] for b in bands) - min(b[1] for b in bands))

    w3, h3 = extent_mm(*A3_TWIN)
    w4, h4 = extent_mm(*A4_TWIN)
    assert abs(w4 - w3) <= 5.0 and abs(h4 - h3) <= 5.0, (
        f"the A4 export reads {w4:.0f}x{h4:.0f} mm but the A3 original reads {w3:.0f}x{h3:.0f} mm. "
        f"A ratio near {1 / math.sqrt(2):.4f} means the sheet shrink was not applied.")
    assert 7000 < w3 < 9000, "sanity: this unit is ~8 m across; if it is not, BOTH sheets are wrong"

# the living zone, from the ink. Used only to SEED and to SIGN -- never to build.
LIVING_SEED = (6000.0, 2000.0)
# THE OWNER SIGNED ONE LINE (2026-07-12), not four. The north edge of the living zone is a ZONING
# LINE across an open plan (living <-> dining) -- it is not a wall and no wall ink exists there.
# The other three virtual edges are the AGENT's own closure crutches and stay agent-provisional.
LIVING_OWNER_EDGE = ["h:4970:5069:3120:7720"]
# D1 (round 5): THE SIGNATURE IS NO LONGER SOMETHING THE CALLER CAN TYPE. Round 4's free-text
# --owner-signature carried an `edges=` clause and the gate verified a bijection against argv -- but
# THE AGENT AUTHORED BOTH SIDES OF THAT BIJECTION, so a self-consistent signature naming a bogus
# y=3905 edge passed and wrote a 17.5 m2 "owner-signed" room. The signature now lives in an
# OWNER-AUTHORED LEDGER (the ffe_signoff_gate.py pattern) that this reader can only READ, and that
# the PreToolUse guard hooks stop the agent's tools from writing.
LIVING_LEDGER = os.path.join(_REPO, "_private", "_takeoff-012", "zoning-signoff.json")
# the ONE line the owner really signed, as its canonical key (sheet-namespaced, snapped to ink)
LIVING_OWNER_KEY = ("654446_i-24-004-k._villavalley_2-_-01:p3|h:4969.9:5069.4:3120.0:7720.5")
LIVING_VIRTUAL = ["v:3020:3120:3485:5069", "h:0:100:3120:3270", "v:3020:3120:0:250"]
real_ledger = pytest.mark.skipif(not os.path.exists(LIVING_LEDGER),
                                 reason="owner ledger not present (client-derived, gitignored)")


@pytest.fixture(scope="module")
def sheet():
    from bluehouse_plan_reader import build
    meta, _ = build(_PDF_ABS, 3, seed=LIVING_SEED, zone_name="living",
                    virtual_edges=LIVING_VIRTUAL, signed_by="TEST (not an owner)",
                    owner_edges=LIVING_OWNER_EDGE, owner_ledger=LIVING_LEDGER)
    return meta


@real_pdf
def test_THE_GATE_over_every_page_of_the_real_pdf():
    """Round 1 emitted build_floor-ready 'floor plans' for SEVEN cabinet-joinery sheets of this
    PDF. Exactly two pages of the eighteen are floor plans. Run all of them."""
    import fitz
    from bluehouse_plan_reader import build
    n = fitz.open(_PDF_ABS).page_count
    accepted, refused = [], {}
    for p in range(n):
        try:
            build(_PDF_ABS, p)
            accepted.append(p)
        except RefuseSheet as e:
            refused[p] = str(e)
    assert n == 18
    assert accepted == [3, 4], f"only the two FURNITURE PLAN sheets may pass; got {accepted}"
    for p in (5, 6, 8, 9, 10, 13, 16):          # the 7 round 1 turned into floor plans
        assert p in refused, f"p{p} is a joinery sheet and MUST be refused"
        assert "T1" in refused[p] and "แบบขยาย" in refused[p]
    assert "no DRAWING TITLE field" in refused[0]


@real_pdf
def test_scale_comes_from_the_title_block_and_the_geometry_only_confirms_it(sheet):
    assert sheet["provenance"]["titleblock_denom"] == 50
    assert sheet["scale_mm_per_pt"] == pytest.approx(25.4 / 72.0 * 50, abs=1e-4)
    assert "TITLE BLOCK" in sheet["provenance"]["scale_source"]


@real_pdf
def test_the_SCALED_DIMENSIONS_disclaimer_trap_is_real_on_this_sheet():
    """MEASURED, on the real page: the label must be 'SCALE :' WITH the colon. Plain 'SCALE' also
    prefix-matches the boilerplate 'SCALED  DIMENSIONS. CONTRACTOR TO VERIFY...' note, and on this
    sheet's actual layout that match wins -- returning the disclaimer's next line, which is not a
    scale at all. A reader that then fell back to geometry would be calibrating off a typo."""
    import fitz
    from bluehouse_plan_reader import page_spans
    spans = page_spans(fitz.open(_PDF_ABS)[3])
    assert parse_scale_field(titleblock_field(spans, "SCALE :")) == 50
    trapped = titleblock_field(spans, "SCALE")
    assert "DISCREPANCIES" in trapped and parse_scale_field(trapped) is None


@real_pdf
def test_the_thai_matcher_actually_fires_on_THIS_sheets_real_title_text():
    """The task warned the PDF splits Thai combining marks. MEASURED: on this sheet it does NOT
    -- 'แปลนพื้นชั้น 1' comes out of the text layer composed, and a literal substring test would
    have worked. Reported rather than dressed up. The skeleton matcher fires either way, and it
    is what powers the แบบขยาย VETO that refuses the joinery sheets."""
    import fitz
    text = fitz.open(_PDF_ABS)[3].get_text()
    assert "แปลนพื้น" in text, "the composed literal IS present: the split-marks bug does not bite"
    assert THAI_FLOORPLAN_SKEL in thai_skeleton(text)
    assert title_is_floor_plan("A TITLE THAT IS NOT A PLAN", text)[0], "the Thai path fires"


@real_pdf
def test_NOTHING_is_silently_dropped_every_wall_pen_quad_is_accounted_for(sheet):
    """Round 1 dropped 2 real wall-pen quads (a 40 mm jamb step on the west wall) SILENTLY,
    inside a thickness screen. Now every quad is a band, a step, or a REPORTED anomaly."""
    p = sheet["provenance"]
    assert p["n_bands"] == 43
    assert p["n_wall_steps"] == 2, "the 40 mm jamb step is CLASSIFIED, not dropped"
    note = next(n for n in p["notes"] if "wall-pen lone quads" in n)
    assert "45 = 43 wall bands" in note and "0 unexplained" in note
    assert sheet["segment_classes"].count("wall_step") == 4, "2 steps -> 2 faces each"
    assert not any("REVIEW" in n and "fit NO class" in n for n in p["notes"])


@real_pdf
def test_the_wall_step_is_where_the_ink_is(sheet):
    """The dropped quads are an L at the west-wall door jamb: 40 x 99.5 at x100.5, and
    100.5 x 40 at x0. Both TOUCH a real band -- that adjacency is what admits them."""
    steps = [s for s, c in zip(sheet["segments"], sheet["segment_classes"]) if c == "wall_step"]
    xs = {round(p[0]) for s in steps for p in s}
    ys = {round(p[1]) for s in steps for p in s}
    assert {0, 100, 141} <= xs
    assert {7760, 7800, 7899} <= ys


@real_pdf
def test_measured_openings_match_dimension_strings_PRINTED_ON_THE_SHEET(sheet):
    """NOT a tautology and NOT a bbox: each measured gap is compared against the sheet's own text
    layer, scraped at test time. Nothing here is hardcoded from the hand takeoff. A calibration
    error of even 0.5% moves a 3200 mm slider 16 mm off its string and fails this."""
    import fitz
    import re
    text = fitz.open(_PDF_ABS)[3].get_text()
    printed = {int(m) for m in re.findall(r"\b(\d{3,4})\b", text)}
    measured = [g["length_mm"] for g in sheet["openings"]]
    hits = {p for p in printed for L in measured if abs(L - p) <= 1.0}
    assert {3200, 2900, 1110, 970, 870} <= hits, \
        f"printed strings corroborated by a measured gap: {sorted(hits)}"


@real_pdf
def test_BF01_length_matches_its_printed_string(sheet):
    """The partition is drawn 3235.3 mm long and the sheet prints '3235'. A face-to-face
    measurement against a printed string -- this is what the bbox pin should always have been."""
    import fitz
    text = fitz.open(_PDF_ABS)[3].get_text()
    assert "3235" in text
    bf01 = [s for s in sheet["segments"]
            if abs(s[0][0] - 3020.5) < 1 and abs(s[1][1] - s[0][1] - 3235.3) < 2]
    assert bf01, "BF01 vertical band at x=3020.5, length 3235"


@real_pdf
def test_closure_FAILS_without_the_signed_virtual_edges():
    """THE anti-flattering-scorer pin, and the one that matters most. `closed: true` went true
    the moment enough virtual edges were signed -- it would go true for a fabricated room too.
    So: with the SAME seed and NO signatures, the flood must ESCAPE. The sheet's wall poche
    encloses nothing; the interior of this house is topologically continuous with the outdoors."""
    from bluehouse_plan_reader import build
    meta, _ = build(_PDF_ABS, 3, seed=LIVING_SEED, zone_name="living")
    rc = meta["room_closure"]
    assert rc["closed"] is False
    assert "HOLE" in rc["why"] and "outdoors" in rc["why"]


@real_pdf
def test_the_room_closes_but_NOT_ON_INK_and_the_audit_says_which_sides(sheet):
    """The honest headline. 4 sides; the EAST is 100% ink (the 2900 slider the old reader could
    not see); the NORTH is 85% fabricated. ink_backed is FALSE and must stay false until an owner
    signs the zoning line."""
    rc = sheet["room_closure"]
    assert rc["closed"] is True and rc["n_vertices"] == 4
    assert rc["area_m2"] == pytest.approx(22.4, abs=0.05)
    assert rc["ink_backed"] is False, "30% of this perimeter is NOT ink. Never let this go True."
    assert rc["virtual_perimeter_mm"] == pytest.approx(5714.9, abs=1.0)
    assert rc["virtual_fraction"] == pytest.approx(0.302, abs=0.005)
    # ROUND 3, FATAL 2. Round 2 asserted `unbacked < 1.0 mm ("grid-snap residue only")` -- and that
    # was a LIE the audit told itself: it credited O01's FULL 649.8 mm even though the sheet only
    # inks 61.6% of it. The honest number is the 249.8 mm of blank paper inside that window.
    assert rc["unbacked_perimeter_mm"] == pytest.approx(249.8, abs=1.0), \
        "the half-drawn window's blank paper, no longer laundered as wall"
    assert len(rc["sides"]) == 4
    east = next(s for s in rc["sides"] if s["axis"] == "v" and s["edge"][0][0] > 7000)
    north = next(s for s in rc["sides"] if s["axis"] == "h" and s["edge"][0][1] > 4000)
    south = next(s for s in rc["sides"] if s["axis"] == "h" and s["edge"][0][1] < 200)
    assert "signed_virtual" not in east["backing"], "the east side is 100% real ink"
    assert east["backing"]["opening"] == pytest.approx(2900.0, abs=1.0)
    assert east["unbacked_mm"] == 0.0
    assert north["backing"]["signed_virtual"] / north["length_mm"] > 0.85, "the north is invented"
    assert south["unbacked_mm"] == pytest.approx(249.8, abs=1.0), \
        "ALL of the unbacked perimeter is on the south edge, in O01"
    assert south["backing"]["opening"] == pytest.approx(3599.2, abs=2.0), \
        "3199.4 (slider, ink 1.0) + 399.8 of the 649.8 window (ink 0.616) -- NOT 3849.2"


@real_pdf
def test_the_OWNER_signed_ONE_line_and_the_other_three_stay_AGENT_PROVISIONAL(sheet):
    """The owner adjudicated the north zoning line on 2026-07-12. They did NOT sign the BF01
    extension or the two SW corner stubs -- those are the agent's closure crutches. A room-spec
    that flattened both into 'signed_virtual' would let an agent guess ride an owner signature."""
    rc = sheet["room_closure"]
    walls = {w["id"]: w for w in rc["signed_virtual_walls"]}
    assert set(walls) == {"OE00", "E00", "E01", "E02"}
    assert walls["OE00"]["provenance"] == "owner-signed"
    assert walls["OE00"]["owner_key"] == LIVING_OWNER_KEY
    assert walls["OE00"]["owner_entry"]["by"] == "OWNER"
    assert walls["OE00"]["owner_entry"]["date"] == "2026-07-12"
    assert all(walls[i]["provenance"] == "agent-provisional" for i in ("E00", "E01", "E02"))
    assert all(walls[i]["owner_key"] is None for i in ("E00", "E01", "E02"))
    assert all(walls[i]["owner_entry"] is None for i in ("E00", "E01", "E02"))
    assert rc["virtual_owner_signed_mm"] == pytest.approx(4600.5, abs=1.0)
    assert rc["virtual_agent_provisional_mm"] == pytest.approx(1984.3, abs=1.0)


@real_pdf
def test_room_out_REFUSES_all_THREE_north_lines_without_an_owner_signature(tmp_path):
    """FATAL 4. The only write gate was `if not closed`. ink_backed / unbacked_perimeter_mm /
    virtual_perimeter_mm were computed, emitted, and NEVER CONSULTED -- so three DIFFERENT signed
    north lines each produced a 'closed, auto-derived' room and all three were written to disk.
    Now: a perimeter that is not 100% ink needs an OWNER SIGNATURE, and the signature + the virtual
    fraction are stamped into the spec."""
    from bluehouse_plan_reader import main
    out = str(tmp_path / "r.json")
    args = ["--seed", "6000,2000", "--room-out", out, "--ceiling-mm", "3000",
            "--signed-by", "TEST"]
    for north in ("h:3905:4005:3120:7720", "h:4970:5069:3120:7720", "h:6790:6890:3120:7720"):
        rc = main([_PDF_ABS, "3", str(tmp_path / "w.json"), *args, "--virtual-edge", north,
                   *sum([["--virtual-edge", v] for v in LIVING_VIRTUAL], [])])
        assert rc != 0, f"{north} was WRITTEN with no owner signature"
        assert not os.path.exists(out), "nothing may reach disk"
    # with the signature, the adopted room is written -- and it CARRIES the signature
    # D2: even WITH the owner's signature the room is REFUSED, because the signature names the
    # north line ONLY and 2234.1 mm of this perimeter (3 agent-provisional edges + blank paper) is
    # covered by NOTHING. That is the honest answer: the room cannot be written without an owner
    # decision on those edges. --write-provisional is NOT a signature; it stamps adopted=false.
    signed = ["--owner-edge", LIVING_OWNER_EDGE[0], "--owner-ledger", LIVING_LEDGER,
              *sum([["--virtual-edge", v] for v in LIVING_VIRTUAL], [])]
    assert 5 == main([_PDF_ABS, "3", str(tmp_path / "w.json"), *args, *signed]), \
        "an owner signature does NOT cover agent-provisional edges"
    assert not os.path.exists(out)
    rc = main([_PDF_ABS, "3", str(tmp_path / "w.json"), *args, *signed, "--write-provisional"])
    assert rc == 0
    spec = json.load(open(out, encoding="utf-8"))
    ip = spec["ink_provenance"]
    assert ip["adopted"] is False, "3 unsigned agent edges: this room is NOT owner-adopted"
    assert ip["NOT_covered_by_any_signature_mm"] == pytest.approx(2234.1, abs=1.0)
    assert ip["owner_authorised_mm"] == pytest.approx(4600.5, abs=1.0)
    so = ip["owner_signoff"]
    assert [b["key"] for b in so["edges_bound"]] == [LIVING_OWNER_KEY]
    assert so["edges_bound"][0]["by"] == "OWNER"
    assert len(so["ledger_sha256"]) == 64, "the artefact pins WHICH ledger authorised it"
    # the round-4 field `bijection_verified` was True in every artefact ever written (a failed
    # bijection refused the write) -- a constant dressed as an audit result. It is GONE.
    assert "bijection_verified" not in json.dumps(so)
    assert "owner_signature" not in ip
    assert ip["ink_backed"] is False
    assert ip["virtual_fraction"] == pytest.approx(0.302, abs=0.005)
    assert ip["unbacked_fraction"] == pytest.approx(0.0132, abs=0.002)
    assert ip["virtual_owner_signed_mm"] == pytest.approx(4600.5, abs=1.0)
    assert ip["virtual_agent_provisional_mm"] == pytest.approx(1984.3, abs=1.0)


@real_pdf
def test_the_room_spec_CARRIES_ITS_OPENINGS_it_is_not_a_sealed_shoebox(tmp_path):
    """FATAL 1, end-to-end. The living zone's own 3200 mm south slider, 650 mm window and 2900 mm
    east slider must travel WITH the outline, in the schema build_room/floor_openings consume."""
    from bluehouse_plan_reader import main
    out = str(tmp_path / "room.json")
    assert 0 == main([_PDF_ABS, "3", str(tmp_path / "w.json"), "--seed", "6000,2000",
                      "--room-out", out, "--ceiling-mm", "3000", "--signed-by", "TEST",
                      "--owner-edge", LIVING_OWNER_EDGE[0],
                      "--owner-ledger", LIVING_LEDGER, "--write-provisional",
                      *sum([["--virtual-edge", v] for v in LIVING_VIRTUAL], [])])
    ops = json.load(open(out, encoding="utf-8"))["room"]["openings"]
    # O09 -> O10 (2026-07-14): the geometric boundary-ink class finds an 11th opening on the
    # sheet (the stair gap, backed by its full-length 0.72-pt edge line -- see
    # test_every_gap_on_the_sheet_is_explained), so every id after O07 shifts by one. The
    # room's OWN three openings are geometrically identical to the old pin.
    assert [(o["id"], o["type"], round(o["length_mm"])) for o in ops] == \
        [("O00", "sliding", 3199), ("O01", "window", 650), ("O10", "sliding", 2900)]
    # the same records floor_openings consumes -> real cut geometry, not a decoration
    boxes = [b for o in ops for b in opening_boxes(o, ceiling_mm=3000.0)]
    assert sum(1 for b in boxes if b["kind"] == "glass") == 5, "2+2 slider leaves + 1 window pane"


@real_pdf
def test_every_room_vertex_lands_on_a_real_wall_FACE(sheet):
    """The polygon may not float. Every vertex must be a wall face that exists on the sheet."""
    from bluehouse_plan_reader import build
    faces_x, faces_y = set(), set()
    for s, c in zip(sheet["segments"], sheet["segment_classes"]):
        if c != "wall_poche":
            continue
        for (x, y) in s:
            faces_x.add(round(x, 1))
            faces_y.add(round(y, 1))
    for (x, y) in sheet["room_closure"]["outline_mm"]:
        assert any(abs(x - f) < 0.5 for f in faces_x), f"x={x} is on no wall face"
        assert any(abs(y - f) < 0.5 for f in faces_y), f"y={y} is on no wall face"


@real_pdf
def test_every_gap_on_the_sheet_is_explained(sheet):
    """No gap may be quietly ignored. Each is an OPENING (backed by ink), a logged INFILL (short
    and unbacked) or a reported VOID (long and unbacked -- left OPEN, which is the honest one).

    RE-PINNED under the geometric boundary-ink class (2026-07-14). This sheet used to report
    TWO 1110 mm stair holes; the 0.42-pt pen table was blind to the 0.72-pt stair-edge line the
    designer drew across the interior one (x=1300.7, the run's face is 1301.0 -- full-length,
    coverage 1.0; inspected on the rendered sheet, it is the stair's boundary against the hall).
    That gap is now an OPENING carrying its pen evidence. The WEST stair hole has no ink of any
    pen and STAYS a void: the honest-failure channel did not get widened away, it is exercised
    one line down."""
    rc = sheet["room_closure"]
    assert len(sheet["openings_typed"]) == 11
    assert len(rc["closure_infills"]) == 0
    assert [v["length_mm"] for v in rc["unbacked_voids"]] == [1110.2], \
        "the WEST 1110 mm stair hole carries no ink of ANY pen: LEFT OPEN, not bridged"
    assert all(v["ink_coverage"] == 0.0 for v in rc["unbacked_voids"])
    stair = [o for o in sheet["openings_typed"] if abs(o["length_mm"] - 1110.2) < 0.1]
    assert len(stair) == 1 and stair[0]["ink_pens"] == {"0.72": 1110.2}, \
        "the flipped stair gap must SHOW its evidence: one full-length 0.72-pt edge line"


@real_pdf
def test_the_real_openings_json_feeds_floor_openings(sheet):
    """End-to-end contract: the emitted openings drive the actual wall-cut/glass machinery."""
    ops = sheet["openings_typed"]
    assert {o["type"] for o in ops} == {"sliding", "window", "door"}
    assert all({"id", "type", "rect"} <= set(o) for o in ops)
    kept, n_cuts = clip_wall_segments(sheet["segments"], ops)   # KeyError on the round-1 schema
    # 10 -> 14 (2026-07-14): all four extra cuts belong to the new stair-gap opening O08 -- and
    # that decomposition is PINNED, not prose (review: a redistribution where O08 cuts nothing
    # and another opening double-cuts passed the bare n_cuts==14).
    assert n_cuts == 14, f"the openings must CUT the walls; cut {n_cuts}"
    stair_less = [o for o in ops if abs(o["length_mm"] - 1110.2) >= 0.1]
    assert len(stair_less) == len(ops) - 1, "exactly one stair-gap opening to attribute"
    _, n10 = clip_wall_segments(sheet["segments"], stair_less)
    assert n10 == 10, "the 4 extra cuts must ALL belong to the stair-gap O08"
    boxes = [b for o in ops for b in opening_boxes(o, ceiling_mm=3000.0)]
    assert len(boxes) == 17
    # 4 sliders x 2 leaves = 8 panes, + 1 window pane; the window also gets a sill and a lintel,
    # and each of the 6 doors (incl. the stair-gap O08) gets a lintel.
    assert sum(1 for b in boxes if b["kind"] == "glass") == 9
    assert sum(1 for b in boxes if b["kind"] == "wall") == 8


# ====== ROUND 5, D1: the signature was FORGEABLE BY THE AGENT (it was bound to ARGV, not the OWNER)
@real_pdf
@real_ledger
def test_ATTACK_A_a_SELF_CONSISTENT_forged_signature_naming_a_BOGUS_edge_is_REFUSED(tmp_path):
    """THE ROUND-4 KILL. The agent writes a signature that names the very edge it is passing --
    y=3905, a line the owner never saw -- and the round-4 bijection PASSES, because the agent
    authored both sides of it. It exited 0 and wrote a 17.5 m2 "owner-signed" room.

    Round 5: the edge's CANONICAL KEY is not in the owner's ledger. There is no string the agent can
    type that puts it there."""
    from bluehouse_plan_reader import main
    out = str(tmp_path / "r.json")
    base = [_PDF_ABS, "3", str(tmp_path / "w.json"), "--seed", "6000,2000", "--room-out", out,
            "--ceiling-mm", "3000", "--signed-by", "TEST",
            "--owner-edge", "h:3905:4005:3120:7720"]
    # (a) the round-4 attack vector, verbatim: a self-consistent free-text signature. The FLAG IS
    #     DEAD -- there is nowhere left to put a run-time-composed signature.
    assert 0 != main(base + ["--owner-signature",
                             "OWNER-SIGNED 2026-07-12 | who=OWNER | edges=h:3905:4005:3120:7720 "
                             "| note=north zoning line at y=3905; living<->dining, open plan"])
    assert not os.path.exists(out)
    # (b) the same bogus edge against the REAL owner ledger -> its key is not signed.
    assert 0 != main(base + ["--owner-ledger", LIVING_LEDGER])
    assert not os.path.exists(out), "a bogus zoning line was written as OWNER-SIGNED"
    # (c) and it cannot be smuggled in by pointing the reader at a ledger the AGENT wrote: the
    #     ledger is only as good as the guard hook that stops the agent writing it (see
    #     test_guards.sh). What the READER guarantees is only this: key not in ledger -> refusal.
    forged = tmp_path / "zoning-signoff.json"
    forged.write_text(json.dumps({"signed": [
        {"key": "654446_i-24-004-k._villavalley_2-_-01:p3|h:3905.2:3999.4:3120.0:7720.5",
         "by": "OWNER", "date": "2026-07-12"}]}), encoding="utf-8")
    assert 0 == main(base + ["--owner-ledger", str(forged), "--write-provisional",
                             *sum([["--virtual-edge", v] for v in LIVING_VIRTUAL], [])]), \
        "a ledger IS the trust root: if the agent can write one, it is theatre -- that is what the " \
        "guard hook exists for, and this test PINS that the reader alone does not close it"
    spec = json.load(open(out, encoding="utf-8"))
    # ...and even then the artefact NAMES the ledger it trusted, by path and by hash. A forgery is
    # at least ATTRIBUTABLE: it cannot hide behind a string in argv that nobody can diff.
    assert spec["ink_provenance"]["owner_signoff"]["ledger_path"] == str(forged)
    assert len(spec["ink_provenance"]["owner_signoff"]["ledger_sha256"]) == 64


@real_pdf
@real_ledger
def test_ATTACK_B_the_agents_OWN_provisional_edges_cannot_be_LAUNDERED_to_owner_signed(tmp_path):
    """THE OTHER ROUND-4 KILL. Re-pass the three AGENT-PROVISIONAL edges (BF01 extension + the two
    SW corner stubs, 1984.3 mm) as --owner-edge, name them in one forged signature, and round 4
    wrote the room with virtual_agent_provisional_mm 1984.3 -> 0 and owner_authorised_mm
    4600.5 -> 6584.8. Exit 0.

    Round 5: none of the three has a ledger entry. The owner signed ONE line."""
    from bluehouse_plan_reader import main
    out = str(tmp_path / "r.json")
    base = [_PDF_ABS, "3", str(tmp_path / "w.json"), "--seed", "6000,2000", "--room-out", out,
            "--ceiling-mm", "3000", "--signed-by", "TEST",
            "--owner-edge", LIVING_OWNER_EDGE[0],
            *sum([["--owner-edge", v] for v in LIVING_VIRTUAL], [])]
    assert 0 != main(base + ["--owner-ledger", LIVING_LEDGER]), \
        "the agent's own closure crutches were laundered into owner geometry"
    assert not os.path.exists(out)
    # the honest path: they stay --virtual-edge, and the room is written adopted=false
    ok = [_PDF_ABS, "3", str(tmp_path / "w.json"), "--seed", "6000,2000", "--room-out", out,
          "--ceiling-mm", "3000", "--signed-by", "TEST",
          "--owner-edge", LIVING_OWNER_EDGE[0], "--owner-ledger", LIVING_LEDGER,
          *sum([["--virtual-edge", v] for v in LIVING_VIRTUAL], []), "--write-provisional"]
    assert 0 == main(ok)
    ip = json.load(open(out, encoding="utf-8"))["ink_provenance"]
    assert ip["adopted"] is False
    assert ip["virtual_agent_provisional_mm"] == pytest.approx(1984.3, abs=1.0), \
        "the 1984.3 mm the round-4 attack laundered to zero must STAY agent-provisional"
    assert ip["owner_authorised_mm"] == pytest.approx(4600.5, abs=1.0), "NOT 6584.8"


@real_pdf
def test_the_free_text_owner_signature_flag_is_DEAD_on_every_path(tmp_path):
    """A signature the caller composes at run time is authored by the caller. The flag must not
    survive anywhere -- not in main(), not in build()."""
    from bluehouse_plan_reader import main, build
    out = str(tmp_path / "r.json")
    assert 2 == main([_PDF_ABS, "3", str(tmp_path / "w.json"), "--seed", "6000,2000",
                      "--room-out", out, "--ceiling-mm", "3000", "--signed-by", "TEST",
                      "--owner-signature", "OWNER-SIGNED 2026-07-12 | who=OWNER | "
                      "edges=h:4970:5069:3120:7720 | note=y=4969.9"])
    assert not os.path.exists(out)
    with pytest.raises(RefuseSheet, match="IS GONE"):
        build(_PDF_ABS, 3, owner_signature="anything at all")


@real_pdf
def test_an_owner_edge_with_NO_ledger_is_just_an_agent_edge_wearing_a_hat():
    from bluehouse_plan_reader import build
    with pytest.raises(RefuseSheet, match="needs --owner-ledger"):
        build(_PDF_ABS, 3, seed=LIVING_SEED, signed_by="TEST",
              owner_edges=LIVING_OWNER_EDGE, owner_ledger=None)
    # a ledger path that does not exist SIGNS NOTHING -- it must never fail open
    with pytest.raises(RefuseSheet, match="unusable"):
        build(_PDF_ABS, 3, seed=LIVING_SEED, signed_by="TEST",
              owner_edges=LIVING_OWNER_EDGE, owner_ledger="/nope/zoning-signoff.json")


@real_pdf
def test_THE_FORGE_HOLE_a_differently_named_ledger_is_REFUSED(tmp_path):
    """Round 6, the forge lens: guard_paths/guard_bash defend the basename `zoning-signoff.json`,
    but the reader used to consume --owner-ledger <ANY path> -- so an agent could Write my-ledger.json
    (a name its tools ARE allowed to write), fill it with a self-authored entry, and point the reader
    at it. Consumption must be bound to the protected basename or the hook defends nothing.
    A well-formed, VALID ledger under the wrong NAME must still be refused -- it is the name, not the
    content, that the hook can defend."""
    import json as _json, zoning_signoff_gate as Z
    from bluehouse_plan_reader import build
    entries, _sha, err = Z.load_ledger(LIVING_LEDGER)
    assert err is None  # copy the REAL owner entry verbatim, only the filename differs
    forged = tmp_path / "my-ledger.json"
    forged.write_text(_json.dumps({"schema": Z.SCHEMA, "signed": entries}), encoding="utf-8")
    with pytest.raises(RefuseSheet, match="must be named"):
        build(_PDF_ABS, 3, seed=LIVING_SEED, signed_by="TEST",
              owner_edges=LIVING_OWNER_EDGE, owner_ledger=str(forged))


@real_pdf
@real_ledger
def test_the_owner_ledger_holds_EXACTLY_ONE_real_entry_and_it_is_the_north_zoning_line():
    """Nothing else goes in it. If this test ever sees a second entry, someone signed something --
    and if that someone was an agent, the guard hook failed."""
    import zoning_signoff_gate as Z
    entries, sha, err = Z.load_ledger(LIVING_LEDGER)
    assert err is None and len(sha) == 64
    valid = [e for e in entries if Z.sign_status(e) == "valid"]
    assert len(entries) == 1 and len(valid) == 1, f"the owner signed ONE line; ledger has {entries}"
    (e,) = valid
    assert Z.entry_key(e) == LIVING_OWNER_KEY
    assert e["by"] == "OWNER" and e["date"] == "2026-07-12" and e["zone"] == "living"
    assert "4969.9" in e["note"] and "open plan" in e["note"].lower()


# ================================ ROUND 4, D4: the floor shell extruded a wall the plan never drew
@real_pdf
def test_D4_the_walls_json_TAGS_its_virtual_edges_so_the_floor_shell_can_refuse_them(sheet):
    """THE PHANTOM WALL. build_floor read wj["segments"] wholesale and never looked at
    segment_classes -- so the 8 `signed_virtual` segments (the owner-signed north ZONING line
    across an OPEN PLAN, plus the 3 agent stubs) were extruded into the whole-floor shell as real
    walls. The plan draws nothing there. build_floor now extrudes INK CLASSES ONLY.

    This pins the contract build_floor depends on: the classes exist, they are parallel to the
    segments, and the virtual ones are separable."""
    segs, classes = sheet["segments"], sheet["segment_classes"]
    assert len(segs) == len(classes), "the class list must be parallel or the filter is a lottery"
    ink = {"wall_poche", "wall_step"}
    virtual = [s for s, c in zip(segs, classes) if c not in ink]
    assert {c for c in classes} == {"wall_poche", "wall_step", "signed_virtual"}
    assert len(virtual) == 8, "4 virtual edges x 2 faces = the 8 phantom segments"
    # the zoning line itself: a 4600 mm run at y=4969.9 that NO wall band touches
    assert [[3120.0, 4969.9], [7720.5, 4969.9]] in virtual
    # WHY it is virtual: the y=4969.9 FACE is real ink (parse_virtual_edge would refuse a
    # coordinate that was not), but the sheet only DRAWS 669.9 of the zoning line's 4600.5 mm.
    # The other 3930.6 mm is blank paper across an open plan. THAT is the wall build_floor was
    # inventing, and it is the single largest fabricated run on the shell.
    covered = 0.0
    for (a, b), c in zip(segs, classes):
        if c == "wall_poche" and abs(a[1] - 4969.9) < 0.5 and abs(b[1] - 4969.9) < 0.5:
            lo, hi = sorted((a[0], b[0]))
            covered += max(0.0, min(hi, 7720.5) - max(lo, 3120.0))
    assert covered == pytest.approx(669.9, abs=1.0)
    assert 4600.5 - covered == pytest.approx(3930.6, abs=1.0), \
        "3930.6 mm of 'wall' that the plan does not draw"


def test_D4_closure_infill_is_now_a_GATE_number_not_a_free_pass():
    """LATENT, and fixed before it lied. A closure_infill (an undrawn stub, BRIDGED as wall) was
    credited as `backed` at its FULL gap length and counted in NEITHER gate number -- so a room
    that only closed because the reader bridged its holes could still read ink_backed. It is 0.0 mm
    on this sheet; that is luck, not design."""
    from bluehouse_plan_reader import MAX_UNSIGNED_INFILL_MM, audit_sides
    outline = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]
    backing = [([0.0, 0.0, 1000.0, 100.0], "wall_poche"),
               ([0.0, 900.0, 1000.0, 1000.0], "wall_poche"),
               ([0.0, 0.0, 100.0, 1000.0], "wall_poche"),
               ([900.0, 0.0, 1000.0, 700.0], "wall_poche"),
               ([900.0, 700.0, 1000.0, 1000.0], "closure_infill")]   # a 300 mm bridged stub
    sides = audit_sides(outline, backing)
    infill = round(sum(s["backing"].get("closure_infill", 0.0) for s in sides), 1)
    assert infill == pytest.approx(300.0, abs=1.0), "the bridge must be VISIBLE as its own class"
    assert infill > MAX_UNSIGNED_INFILL_MM, "and it must be able to trip the gate"
    assert round(sum(s["unbacked_mm"] for s in sides), 1) == 0.0, \
        "the old bug: bridging made it read as fully backed, and nothing counted the bridge"


@real_pdf
def test_the_bbox_is_reported_but_is_NOT_the_metric(sheet):
    """Round 1's headline. It is TRUE -- and it was true when the emitted geometry was a dozen
    freestanding fins. Kept as a calibration smoke-test, demoted from evidence, and the honesty
    block in the json says so."""
    (bx0, by0), (bx1, by1) = sheet["provenance"]["bbox_mm"]
    assert bx1 == pytest.approx(7820, abs=1.0)
    assert by1 == pytest.approx(9720, abs=1.0)
    assert "bbox_is_not_a_metric" in sheet["honesty"]
    # the round-1 pin `(bx0, by0) == (0.0, 0.0)` is DELETED: the origin is DEFINED as the min-x /
    # max-y of these same bands, so it could not fail. It is arithmetic, not a measurement.


@real_pdf
def test_no_answer_key_constant_appears_in_the_reader_source():
    """The hand takeoff (4800 x 4600, 3600, 2800) must never be a constant in the reader."""
    import re
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "bluehouse_plan_reader.py"), encoding="utf-8").read()
    code = "\n".join(line.split("#")[0] for line in src.splitlines())
    for bad in ("4800", "4600", "3600", "2800"):
        assert not re.search(r"\b%s\b" % bad, code), f"answer-key constant {bad} in the reader"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
