"""
bluehouse_plan_reader.py — read the WALL layer out of a Bluehouse Design vector floor-plan
PDF and emit wall-segments-mm@0.1, ready for build_floor.py.

    python bluehouse_plan_reader.py <plan.pdf> <page> <out.json>
        [--scale MM_PER_PT] [--seed X,Y] [--zone-name NAME] [--min-gap MM]

WHY A SIBLING MODULE. pdf_extract_walls.py is CALIBRATED AND IN USE for PRJ-2026-002 (1:75,
scale 26.45): its default constants are simultaneously that project's live calibration and the
pinned contract of its 16 tests. This module touches none of that — it IMPORTS its pure helpers
(map_pt, keep_segment, merge_carried, _seg_key, _valid_seg) and supplies its own predicate,
its own scale and its own origin.

THE BLUEHOUSE WALL PREDICATE (verified on the source sheet, see test file for the pins):
a path is a wall BAND iff
    1. type == "s"                        stroke only
    2. sum(color) <= 0.05                 pure black
    3. round(width, 2) == 0.84            the wall-outline pen  <- LOAD-BEARING
    4. exactly ONE item, and it is "qu"   a lone closed quad = one wall band
    5. 95 <= thin_dim * scale <= 106 mm   the drawn 100 mm wall thickness, screened in MM
                                          (so a 1:100 sheet, where the same wall prints at
                                          2.8 pt instead of 5.6 pt, still passes)
    6. axis-aligned                       (assert; a skewed quad raises)

Criterion 3 is NOT redundant with 5: this sheet carries a lone quad in the w=0.12 class that is
also ~100 mm thick (a kitchen cabinet panel). A thickness-only rule ingests it as a wall.
Criterion 4 is what buys BAND IDENTITY: a plain lineweight rule (is_wall_stroke) shatters each
band into 4 unrelated edges AND additionally admits the black w=0.72 class (leaders, title-block
rules). Bands are what let us emit a face PAIR and detect openings.

WHAT THIS MODULE DOES NOT DO — read `honesty` in the emitted JSON, and the module docstring's
LIMITS section at the bottom of this file. In particular: wall ink alone does NOT close a room
on this drawing convention. Openings are emitted as UNSIGNED candidates and are machine-inert
until an owner signs them.
"""
import argparse
import collections
import json
import math
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_extract_walls import map_pt, merge_carried, _seg_key, _valid_seg  # noqa: E402

SCHEMA = "interior-ai/wall-segments-mm@0.1"
PT_MM = 25.4 / 72.0                      # 0.352777... mm per point at 1:1

# --- predicate constants (Bluehouse pen table). Named, not magic. -------------------------
WALL_PEN_PT = 0.84                       # the wall-outline lineweight
BORDER_PEN_PT = 1.44                     # the sheet border; its absence means "not this exporter"
MAX_COLOR_SUM = 0.05                     # pure black
WALL_MM_LO, WALL_MM_HI = 95.0, 106.0     # the drawn 100 mm wall, screened in MM
AXIS_TOL_PT = 0.15
# Was 0.05, and it hard-REFUSED 16 real plan pages before a single gate check ran. That is not a
# rotated-wall problem, it is EXPORTER FLOATING-POINT NOISE. Skew distribution over all 4,865
# wall-pen quads in the corpus (post rotation_matrix, per-quad max over its 4 edges) is BIMODAL with
# an EMPTY BAND between the modes:
#     < 0.001 pt .... 4,758 quads   (axis-aligned)
#     0.05-0.15 pt ...... 13 quads  (only the values {0.0599, 0.06, 0.0601, 0.12, 0.1201})
#     0.15-1.32 pt ....... 0 quads  <- the gap is REAL, not a threshold artefact
#     >= 1.32 pt ........ 94 quads  (genuine diagonals: 87 at 45.000 deg, 6 at 44.464, 1 at 44.956)
# Worst noise 0.120056 pt; smallest genuine rotation 1.320007 pt. 0.15 sits 1.25x above the noise and
# 8.8x below the smallest real rotation. The hard refuse is KEPT -- rotated walls really are
# unsupported; it now fires on rotation instead of on round-off.
# BLAST RADIUS IS STRUCTURAL, not a corpus coincidence: only a page carrying a quad with skew in
# (0.05, 0.15] can change verdict. Exactly 9 pages qualify -- 4 true plans (newly accepted) and 5
# แบบขยาย BF-10..BF-15 sheets, which now REACH the gate and are refused by it (T1+T2+S1+E, depth 4).
SQUARE_ASPECT = 1.15                     # below this a band is a corner block: belongs to both axes
DEFAULT_MIN_GAP_MM = 400.0               # smaller than any door leaf; below this a gap is noise

# --- BOUNDARY-INK (part C) constants. The wall pen STOPS at every opening on this convention;
# the enclosure's runs there (sliding glass, windows, door infills) are on OTHER pens.
# THE 0.42 LESSON (2026-07-14). This block used to declare PANEL_PEN_PT = 0.42 and match it
# EXACTLY. That was sheet 012's pen table wearing the costume of a convention: across the 27
# gate-accepted corpus pages the boundary ink is drawn at 0.12 (I-24-056), 0.38/0.48 (Pandora,
# whose sheets contain NO 0.42 ink at all), 0.54, 0.6, 0.72, even 1.44 threshold strokes --
# measured, _private/plan-gate/pen-forensics.json. Every opening on those offices' sheets read
# as an ink-less VOID, and 22 of 27 accepted pages closed nothing. Pen WIDTH is not the class.
# The class is GEOMETRIC: pure-black stroke ink, inside a wall run's face pair, not a dimension
# tick, not the sheet frame. Only the wall pen itself is excluded (it already has its own
# class), and the pens that actually back each opening are REPORTED -- per sheet in the notes,
# per opening in `ink_pens` -- so a wrong pen can be SEEN downstream, never silently assumed.
LEAF_PEN_PT = 0.30                       # sliding-LEAF detail lines drawn INSIDE a slider
#   (still 012's pen table, deliberately: the leaf pen only TYPES a slider vs a window. A wrong
#    leaf pen mistypes an opening; it cannot fabricate closure. Generalize it the day a second
#    office's slider is actually measured, not before.)
WALL_CAVITY_TOL_MM = 60.0                # two parallel runs whose FACING faces are this close
#   AND whose long extents OVERLAP are the LEAVES of ONE composite wall. Pandora draws a 200 mm
#   wall as two abutting 100 mm leaves (gap 0 mm); 304149's cavity wall needs > 2 mm. A window
#   there is ONE rect spanning both leaves: it aligns to NEITHER leaf alone, so before composite
#   pairs existed every such opening read as a hole.
#   THE EXTENT CLAUSE IS LOAD-BEARING (2026-07-14 review, MAJOR x2 confirmed). The first version
#   merged on face COORDINATES alone and argued "the nearest two real walls are a corridor
#   >= 800 mm apart" -- FALSE on the very corpus it cited: unrelated parallel walls in different
#   parts of a plan land within 60 mm in the THIN coordinate by coincidence (51 mm face-steps,
#   jogged walls), and transitive chaining minted 301-701 mm pseudo-wall bands whose "leaves"
#   never coexist anywhere along the axis. Real double-leaf walls are COEXTENSIVE; requiring the
#   leaves' long intervals to actually overlap keeps every honest composite on the corpus
#   (27/27 pages emit identical opening sets) and refuses the coincidence chains.
MAX_COMPOSITE_MM = 300.0                 # widest honest composite measured: ~201 mm + leaf. The
#   coincidence chains reached 701 mm. Same ceiling as MAX_BACKING_THICK_MM, same law: a band a
#   rect could hide 3 rooms of furniture in is not a wall.
STUB_BACKER_OVERSHOOT_MM = 100.0         # a gap SHORTER than CLOSE_TOL_MM (no door leaf is that
#   narrow) may be cut open only by ink that TERMINATES at its jambs. Measured corpus band: the
#   59 honest stub openings' backers overshoot <= 4.2 mm (frame members, thresholds); the one
#   dishonest backer -- a 2551 mm crossing polyline over a 99 mm stub on Pandora p8, dimension/
#   grid-shaped ink -- overshoots 2451 mm. 100 mm sits 24x above the honest worst and 24x below
#   the fabrication. Crossing ink over a stub is NOT an opening; the stub stays a bridged,
#   LOGGED infill (fail toward wall, disclosed), never a fabricated cut.
TICK_MAX_MM = 200.0                      # a lone 'l' shorter than this is a dimension tick
#   (the sheet's ticks are 122 mm; nothing else in the class is under 300 mm -> 3x margin)
ENV_MARGIN_MM = 1000.0                   # envelope inflate; rejects the sheet/clip frame
BAND_ALIGN_TOL_MM = 12.0                 # ~1/8 of a 100 mm wall
GLAZING_COVER_FRAC = 0.60                # a gap is BACKED iff panel ink covers >=60% of its span
CLOSE_TOL_MM = DEFAULT_MIN_GAP_MM        # DECLARED closure tolerance: a gap below this with NO ink
#   is an undrawn stub (exporter/drafting omission) and is infilled -- and LOGGED, every one, with
#   its size. Above it, a gap is an OPENING or an honest VOID; it is NEVER bridged.
GRID_MM = 25.0                           # flood-fill cell (a 100 mm wall is 4 cells: no diagonal leak)
SNAP_TOL_MM = 20.0                       # polygon vertices snap back onto real ink faces
# GRID > SNAP_TOL IS LOAD-BEARING (round 3). It was 25 < 30, so EVERY contour vertex was within
# snapping distance of a face no matter where the solid actually was, the snap was UNCONDITIONAL,
# and test_every_room_vertex_lands_on_a_real_wall_FACE was a TAUTOLOGY -- it could not fail even
# for a fabricated wall. The flood contour lies within step/2 = 12.5 mm of the true solid boundary
# (cell centres decide occupancy), so 20 mm still snaps every REAL face; a boundary further than
# 20 mm from any ink face is now LEFT WHERE IT IS and the vertex pin fires on it.
assert SNAP_TOL_MM < GRID_MM, (
    "SNAP_TOL_MM >= GRID_MM makes the polygon snap unconditional: every vertex would land on a "
    "face by construction and the vertex pin could never fail. See round 3, FATAL 3(a).")
VIRTUAL_SNAP_TOL_MM = 0.5                # a signed virtual edge is SNAPPED onto the ink face it
#   validated against; anything beyond this is REPORTED as a snap delta, never silently accepted.
MAX_UNSIGNED_VIRTUAL_MM = 0.5            # --room-out write gate: virtual perimeter above this
MAX_UNSIGNED_UNBACKED_MM = 1.0           # (or unbacked above this) needs an OWNER SIGNATURE
MAX_UNSIGNED_INFILL_MM = 0.5             # D4: bridged undrawn stubs were credited as BACKED at
#   full gap length and counted in NEITHER gate. 0.0 mm on this sheet, so not lying yet. Now a
#   first-class gate number: a room that only closes over bridged stubs needs an owner too.
MAX_BACKING_THICK_MM = 300.0             # a rect may only BACK an edge it is thin across; see
#   audit_sides. Above this the rect runs along the edge's cross axis and its END is not a FACE.
LEAF_MIN_PATHS = 2                       # >=2 leaf-pen paths inside an opening => it is a SLIDER

# Scales a Thai residential sheet is plausibly plotted at. Physics: mm_per_pt = PT_MM * denom.
CANDIDATE_DENOMS = (20, 25, 30, 40, 50, 75, 100, 125, 150, 200)

# --- THE PAPER (see sheet_shrink). The office DRAWS on A3 and sometimes EXPORTS at A4 -- the whole
# page, title block included, shrinks by 1/sqrt(2) while the title block goes on printing the A3
# original's scale. 116 of 898 corpus pages are such exports.
SHEET_BORDER_PT = (1122.45, 773.85)             # the A3 design sheet's 1.44 pt border, MEASURED
SHEET_SHRINK_STEPS = (1.0, 1.0 / math.sqrt(2))  # A3->A3, A3->A4. Nothing else is exported.
SHEET_SHRINK_TOL = 0.004    # observed spread WITHIN a step: 0.006%. Nearest other step: 29% away.
SHEET_ANISO_TOL = 0.004     # x and y must shrink TOGETHER, or the page was stretched, not reduced.
SHEET_BORDER_TOL_PT = 2.0   # how close a 1.44 pt rect must be to the page's biggest to BE the border

# --- WALL STEP (round 2). Two 40 mm wall-pen quads at the building's NW outer corner wrap the
# 100 mm wall into a ~140 mm column/step. Round 1's 95-106 window dropped them SILENTLY. They are
# real ink, so they are now CLASSIFIED (segment class "wall_step"), not widened into the wall
# class: a bare thickness widening to 145 mm would also admit joinery panels on other sheets.
# The class is guarded by ADJACENCY -- a step must touch a real wall band, so a free-floating
# 40 mm sliver (a furniture panel) is still rejected.
STEP_MM_LO, STEP_MM_HI = 35.0, 50.0
STEP_ADJ_TOL_MM = 3.0

# =====================================================================================
# PAGE-TYPE GATE (round 2). Round 1 FAILED OPEN: it emitted build_floor-ready "floor plans"
# for 7 furniture-joinery sheets of this same PDF, and its title-block cross-check rubber-
# stamped them. Emission now requires POSITIVE evidence that the page is a floor plan.
# Every check is reported (gate_checks in the json); a single failure REFUSES the page.
# =====================================================================================
PLAN_DENOMS = (50, 75, 100, 125, 150, 200)   # a WHOLE-FLOOR plan is not plotted at 1:25/1:15
PLAN_TITLE_WORD = re.compile(r"\bPLAN\b", re.I)
NOT_PLAN_WORD = re.compile(r"\b(DETAIL|ELEVATION|SECTION)\b", re.I)
# Thai, matched on the CONSONANT SKELETON (see thai_skeleton): this PDF's text layer splits
# combining vowels/tone marks off their consonants, so a literal string compare is unreliable.
# ROUND 3 -- measured over the whole 898-page studio corpus (20 PDFs / 15 projects), not one PDF.
# THE OFFICE DOES NOT TITLE ITS PLANS "แปลนพื้น". It titles them แปลนเฟอร์นิเจอร์ (furniture),
# แปลนผนัง (wall), แปลนไฟฟ้า (electrical), "PLAN เฟอร์นิเจอร์", "FURNITURE PLAN 1". Requiring the
# FLOOR-plan skeleton แปลนพน admitted only the 3 sheets whose title happens to be in LATIN -- so the
# reader had never once been RUN on a Thai-titled sheet, and every downstream number it has ever
# reported (F1, "closes a room") was measured on a sample the gate itself selected.
THAI_PLAN_SKEL = "แปลน"            # "plan" -- ANY plan sheet. The VETO below is what makes this safe.
THAI_FLOORPLAN_SKEL = "แปลนพน"     # แปลนพื้น "floor plan": a strict subset, kept for callers/tests.
THAI_NOT_PLAN_SKELS = ("แบบขยาย", "รปดาน", "รปตด")  # enlarged detail / elevation / section
#   The OLD comment here said: "bare แปลน appears in the BODY of 6 of the 7 joinery sheets, so
#   matching แปลน would fail open". That is a PAGE_TEXT trap, and it was mis-applied to the TITLE.
#   MEASURED on the corpus's positional DRAWING TITLE field: bare แปลน appears in 62 PLAN titles and
#   37 DETAIL titles -- and ALL 37 are "แบบขยายแปลน<room>" (an ENLARGED plan of one room). After the
#   แบบขยาย veto: 62 plan / 0 non-plan. ORDER IS LOAD-BEARING: veto first, then accept.
THAI_NOT_BUILDABLE_SKELS = ("ฝาเพดาน",)   # ฝ้าเพดาน = reflected ceiling plan.
#   Argued from what build_floor CONSUMES (0.84 pt wall poche -> bands -> rooms): MEASURED, 6 of the
#   7 RCP pages carry ZERO 0.84 pt wall quads (every other plan class has a median of 31-117). An RCP
#   draws the ceiling grid, not the poche, and shows no openings -- build_floor would emit a sealed
#   box. Vetoed as a PAGE TYPE. แปลนไฟฟ้า (electrical) is NOT vetoed: 4/4 of its pages DO carry the
#   poche (median 31), so it is a structurally valid source of the same walls.

# --- EXTENT (T3). THE CLASS AN ANSWER KEY BUILT ON "does the title say แปลน" CANNOT SEE. ---------
# This module emits wall-segments-mm for build_floor: its product is a FLOOR. But 9 corpus sheets are
# titled แปลนเฟอร์นิเจอร์ <ROOM NAME> -- a per-room ENLARGEMENT, the same thing the 374 แบบขยาย sheets
# are, under a title the designer spelled differently. 934076 p7 'แปลนเฟอร์นิเจอร์ ห้องนอน 3,4' is a
# 12.0 x 4.8 m strip: two bedrooms and their baths, clipped at a party wall. It has walls, a stated
# 1:50, a 57.6 m2 footprint and ink on four sides -- SO EVERY GEOMETRIC GATE CHECK PASSES ON IT.
# Only the title can tell a room from a storey, and its PDF contains no whole-storey plan at all, so
# without this check that bedroom becomes THE floor of that project. This is round 1's failure at a
# smaller radius: round 1 emitted a floor for a cabinet; round 3 would emit one for a bedroom.
# MEASURED: the single skeleton token หอง selects exactly those 9 and none of the 53 storey plans.
ROOM_EXTENT_SKEL = "หอง"             # ห้อง "room"
MIN_PLAN_BANDS = 12                  # p3=45, p4=17; the joinery sheets top out at 8
FOOTPRINT_MIN_SIDE_MM, FOOTPRINT_MAX_SIDE_MM = 2500.0, 60000.0
FOOTPRINT_MIN_AREA_M2 = 10.0
SIDE_INK_MIN_FRAC = 0.05             # each side of the footprint must carry SOME wall ink
WALL_MM_PLAUSIBLE_LO, WALL_MM_PLAUSIBLE_HI = 80.0, 260.0   # 100/150/200/250 mm walls

_THAI_MARKS = (set(range(0x0E31, 0x0E32)) | set(range(0x0E34, 0x0E3B))
               | set(range(0x0E47, 0x0E4F))
               # FONT-PRIVATE Thai marks. The office's CAD font emits tone marks into the Unicode
               # PRIVATE USE AREA instead of U+0E47-0E4E, so the range above never saw them.
               # MEASURED in the corpus's drawing titles: U+F70E = ์ (thanthakhat, 98 hits, e.g.
               # เฟอร์นิเจอร์) and U+F70B = ้ (mai tho, 12 hits, e.g. รูปด้าน). NOT cosmetic:
               # skeleton('รูปด้าน') left the PUA mark wedged between ด and า, so the ELEVATION veto
               # skeleton 'รปดาน' never matched and THE VETO SILENTLY DID NOT FIRE on 5 elevation
               # sheets. Stripping the PUA range REPAIRS a veto that was reported as working.
               | set(range(0xF700, 0xF720)))


class RefuseSheet(Exception):
    """The page is not a Bluehouse vector CAD floor plan. Silence is the correct output."""


def thai_skeleton(s):
    """Thai text, reduced to its CONSONANT SKELETON: NFC-normalised, combining vowels/tone marks
    and whitespace removed, upper-cased. This PDF emits 'แปลนพื้นชั้น 1' as separate glyph runs and
    a naive equality test on the composed string is brittle; the skeleton survives that.
        'แปลนพื้นชั้น 1' -> 'แปลนพนชน1'   'แบบขยาย BF-01' -> 'แบบขยายBF-01'"""
    s = unicodedata.normalize("NFC", s or "")
    return "".join(c for c in s if ord(c) not in _THAI_MARKS and not c.isspace()).upper()


# =====================================================================================
# PURE HELPERS (no fitz, no PDF -> unit-testable)
# =====================================================================================
def is_wall_band(dtype, color, width, n_items, item_op):
    """Criteria 1-4 of the predicate: the CLASS test. Thickness (5) is applied separately
    because it needs the scale, which is itself detected from the members of this class."""
    if dtype != "s":
        return False
    if color is None or sum(color) > MAX_COLOR_SUM:
        return False
    if round(width or 0, 2) != WALL_PEN_PT:
        return False
    return n_items == 1 and item_op == "qu"


def thickness_ok(thin_pt, scale):
    """Criterion 5, in MM so it survives a different plot scale."""
    return WALL_MM_LO <= thin_pt * scale <= WALL_MM_HI


def geometry_snap(thin_dims_pt, denoms=CANDIDATE_DENOMS):
    """(modal_thin_pt, [denominators at which that thickness would be a ~100 mm wall]).

    THIS IS A VETO, NOT A SOURCE. Round 1 had a `detect_scale()` that RETURNED a scale from this
    snap alone — i.e. it inferred the plot scale from an ASSUMED 100 mm wall. A 200 mm party wall
    at 1:50 snaps to "1:25" and the whole building is silently emitted at half size. That function
    is DELETED, not deprecated: an API that can fail open must not remain callable.

    The only consumer is resolve_scale(), where a snap that DISAGREES with the title block
    refuses the sheet instead of picking a winner."""
    if not thin_dims_pt:
        return None, []
    modal = collections.Counter(round(t, 2) for t in thin_dims_pt).most_common(1)[0][0]
    return modal, [d for d in denoms if WALL_MM_LO <= modal * PT_MM * d <= WALL_MM_HI]


def parse_titleblock_denom(text):
    """The '1 : NN' string. CROSS-CHECK ONLY, never authoritative — the title block LIES on
    A3-art-exported-to-A4 pages (uniform 0.7071 shrink; it still prints 1:50 while the true
    scale is ~1:70.7). Returns the modal denominator found, or None."""
    found = [int(m.group(1)) for m in re.finditer(r"1\s*[:：]\s*(\d{2,3})\b", text or "")]
    if not found:
        return None
    return collections.Counter(found).most_common(1)[0][0]


def titleblock_field(spans, label, dx_max=20.0, dy_max=25.0):
    """The VALUE of a title-block field, read POSITIONALLY: the nearest text span below the
    field's label and left-aligned with it. spans: [(x, y, text)] in page coords, y DOWN.

    Why positional and not a page-wide keyword search: the joinery sheets carry the word 'แปลน'
    in their body (the joinery's own plan view). Only the title block says what the SHEET is."""
    labels = [(x, y) for x, y, t in spans if (t or "").strip().upper().startswith(label.upper())]
    best = None
    for lx, ly in labels:
        for x, y, t in spans:
            dy = y - ly
            if 0 < dy <= dy_max and abs(x - lx) <= dx_max:
                if best is None or dy < best[0]:
                    best = (dy, (t or "").strip())
    return best[1] if best else None


def parse_scale_field(text):
    """'1 : 50  ' -> 50. Anything that is not a 1:NN ratio -> None (title blocks whose SCALE row
    is empty return the NEXT row's text, e.g. 'ISSUED / REVISION' -- that is not a scale)."""
    m = re.search(r"1\s*[:：]\s*(\d{2,3})\b", text or "")
    return int(m.group(1)) if m else None


def title_is_floor_plan(drawing_title, page_text=None):
    """(ok, why). POSITIVE evidence, read ONLY from the title-block DRAWING TITLE field.

    `page_text` is accepted and IGNORED (both call sites still pass it). It used to be a fallback --
    `if THAI_FLOORPLAN_SKEL in thai_skeleton(page_text): return True` -- and it FAILED OPEN, so it is
    DELETED, not deprecated. MEASURED: it passed T1 on 3 'รายการประกอบแบบ' (specification-index)
    sheets, whose BODY quotes แปลนพื้น while the sheet is not a plan at all; only the geometry checks
    downstream stopped them. A page-wide keyword search cannot say what a SHEET IS. Deleting it costs
    ZERO recall (measured: no plan page depended on it).

    ORDER IS LOAD-BEARING: veto, then accept. The accept skeleton is bare แปลน, which also matches
    the joinery blow-ups 'แบบขยายแปลน<room>' -- the แบบขยาย veto is the ONLY thing between them and
    emission, so it must run first, and it must be PUA-robust (see _THAI_MARKS)."""
    dt = (drawing_title or "").strip()
    if not dt:
        return False, "no DRAWING TITLE field in the title block"
    skel = thai_skeleton(dt)
    for bad in THAI_NOT_PLAN_SKELS:
        if thai_skeleton(bad) in skel:
            return False, f"DRAWING TITLE {dt!r} is a detail/elevation/section sheet, not a plan"
    if NOT_PLAN_WORD.search(dt):
        return False, f"DRAWING TITLE {dt!r} names a detail/elevation/section"
    for bad in THAI_NOT_BUILDABLE_SKELS:
        if thai_skeleton(bad) in skel:
            return False, (f"DRAWING TITLE {dt!r} is a reflected ceiling plan: it carries no wall "
                           f"poche and no openings, so there is nothing for build_floor to build")
    if PLAN_TITLE_WORD.search(dt):
        return True, f"DRAWING TITLE {dt!r} names a PLAN"
    if THAI_PLAN_SKEL in skel:
        return True, f"DRAWING TITLE {dt!r} names a Thai plan (แปลน) and no veto matched"
    return False, f"DRAWING TITLE {dt!r} is not a plan title (no PLAN / แปลน)"


def plan_extent(drawing_title):
    """'storey' | 'room'. WHAT the plan is a plan OF -- see ROOM_EXTENT_SKEL.

    Deliberately separate from title_is_floor_plan: a room enlargement IS a plan (T1 is right to say
    yes), it is just not a FLOOR, which is the only thing this module knows how to emit. Keeping the
    two apart keeps the per-check kill counts honest -- a room refusal names itself instead of hiding
    inside 'not a plan title'."""
    return "room" if ROOM_EXTENT_SKEL in thai_skeleton(drawing_title or "") else "storey"


def extent_is_a_storey(drawing_title, title_ok):
    """(ok, why) for gate check T3. Only has an opinion once T1 has said 'this is a plan at all'."""
    if not title_ok:
        return True, "not evaluated (T1 already refused this page)"
    if plan_extent(drawing_title) == "room":
        return False, (f"DRAWING TITLE {drawing_title!r} names a ROOM: this is a per-room "
                       f"ENLARGEMENT, not a storey. This reader emits a FLOOR for build_floor, and "
                       f"a bedroom is not a floor. REFUSING as a floor source.")
    return True, f"DRAWING TITLE {drawing_title!r} is a plan of a storey, not of one room"


def sheet_shrink(border_wh):
    """(shrink, why). How much SMALLER the exported page is than the A3 sheet the office DRAWS on.
    Raises RefuseSheet rather than inventing a factor.

    THE BUG THIS CLOSES, measured over 898 pages: the office draws on A3 and sometimes exports the
    PDF at A4 -- a uniform 1/sqrt(2) photographic reduction of the whole page, TITLE BLOCK INCLUDED.
    The title block therefore still prints the A3 original's scale while the ink is 0.7071x smaller,
    so a real 100 mm wall reads 70.9 mm and S1 refused the page. S1 WAS NOT BROKEN: it was correctly
    refusing a sheet whose title block was lying to it. The missing piece was the paper, not the wall.
    (`parse_titleblock_denom`'s docstring has warned about exactly this since round 1. Nobody acted.)

    Border geometry, all 898 pages -- three values, no continuum:
        1122.4-1122.5 x 773.8-773.9 pt   662 pages   A3, the design sheet
                793.7 x 547.2 pt         116 pages   sx=0.707115 sy=0.707113  anisotropy 0.000002
                absent                   120 pages   G0 refuses these anyway

    WHY THIS IS NOT ROUND 1 WEARING A HAT. Round 1's deleted detect_scale() read a BUILDING dimension
    whose true value is the very thing the reader is trying to learn. This reads a DRAFTING FRAME of
    fixed, known, building-INDEPENDENT size -- the same 1122.45 x 773.85 pt on every A3 sheet this
    office exports, whatever is drawn inside it. The title block still names the denominator; the
    shrink only says how much smaller the paper got. And the wall veto still vetoes a WRONG shrink: a
    mis-read border moves the modal wall off 100 mm and S1 refuses.

    FAIL-CLOSED THREE WAYS: no border -> refuse. Anisotropic -> refuse (the page was STRETCHED, so
    mm-per-pt is not one number). A reduction that is not a known paper step -> refuse, DO NOT
    INTERPOLATE. "The wall came out plausible" is not evidence: WALL_MM_PLAUSIBLE spans 80-260 mm and
    a 15% scale error hides inside it comfortably."""
    if not border_wh:
        raise RefuseSheet("no sheet border found: the page's paper size cannot be established, so "
                          "the title block's scale cannot be trusted (an A4 export of A3 art still "
                          "prints the A3 scale). REFUSING.")
    w, h = border_wh
    sx, sy = w / SHEET_BORDER_PT[0], h / SHEET_BORDER_PT[1]
    if abs(sx - sy) > SHEET_ANISO_TOL:
        raise RefuseSheet(f"the sheet border is ANISOTROPIC (x {sx:.4f}x, y {sy:.4f}x): the page was "
                          f"stretched, not photographically reduced, so mm-per-pt is not one number. "
                          f"REFUSING.")
    s = (sx + sy) / 2.0
    for step in SHEET_SHRINK_STEPS:
        if abs(s - step) <= SHEET_SHRINK_TOL:
            return step, (f"sheet border {w:.1f}x{h:.1f} pt = {step:.4f}x the A3 design sheet "
                          f"({SHEET_BORDER_PT[0]:.1f}x{SHEET_BORDER_PT[1]:.1f} pt)"
                          + ("" if step == 1.0 else " -- A3 ART EXPORTED TO A4: the title block "
                                                     "states the A3 scale, so it must be corrected"))
    raise RefuseSheet(
        f"the sheet border is {s:.4f}x the A3 design sheet -- not a known paper step "
        f"{[round(x, 4) for x in SHEET_SHRINK_STEPS]}. REFUSING to interpolate a shrink: an unknown "
        f"reduction means an unknown scale, and a 15% scale error hides inside the "
        f"{WALL_MM_PLAUSIBLE_LO:.0f}-{WALL_MM_PLAUSIBLE_HI:.0f} mm plausible-wall window.")


def resolve_scale(thin_dims_pt, tb_denom, shrink=1.0, denoms=CANDIDATE_DENOMS):
    """FAIL-CLOSED scale. Round 1 inferred the scale from an ASSUMED 100 mm wall thickness, so a
    200 mm wall at 1:50 snapped to '1:25' and the building was silently emitted at half size; a
    disagreeing title block only appended a note and fell through to the write.

    Now: THE TITLE BLOCK WINS, and geometry is a VETO, never a source.
      * no stated scale                       -> REFUSE
      * stated scale is not a plan scale      -> REFUSE
      * geometry snaps to a DIFFERENT denom   -> REFUSE (do not pick a winner)
      * geometry snaps to nothing AND the wall would be implausible at the stated scale -> REFUSE

    `shrink` (from sheet_shrink) is how much smaller the PAGE is than the A3 sheet the title block's
    denominator refers to. The snap is done in DESIGN-sheet points so the 100 mm hypothesis stays
    exact; the returned scale is mm per PAGE point, which is what the geometry is measured in.

    WHY THE 100 mm HYPOTHESIS IS NOT WIDENED (measured, and the opposite of what it looks like it
    should be): 3,006 wall quads over the 53 storey plans are 85.7% 100 mm, modal 98.4-101.6 mm on 51
    of 53 pages. There is no 150 mm class and no 250 mm class; the suspected "200 mm hospital party
    wall" DOES NOT EXIST -- the hospital's walls measure 98.4-101.6 mm at 1:150. And widening the
    family MANUFACTURES the ambiguity that disarms this veto: 11.34 pt with a stated 1:50 snaps to
    hits=[25] under the single-100 hypothesis (tb not in hits -> REFUSED, correctly, as the half-size
    trap it is), but to hits=[25, 50] under {100,150,200,250} -- tb IS in hits -> ACCEPTED. The same
    ink is simultaneously a 200 mm wall at a true 1:50 and a 100 mm wall at a true 1:25, and nothing
    in the ink can tell them apart. Widening the family buys 1 page and sells the veto.

    Returns (scale_mm_per_pt, denom, modal_thin_pt, note)."""
    if not thin_dims_pt:
        raise RefuseSheet("no wall-pen quads to check a scale against")
    if tb_denom is None:
        raise RefuseSheet("the title block states NO scale. A plan sheet without a stated scale "
                          "cannot be calibrated from geometry alone (that is how round 1 emitted "
                          "a building at half size). REFUSING.")
    if tb_denom not in PLAN_DENOMS:
        raise RefuseSheet(f"the title block says 1:{tb_denom}, which is not a floor-plan scale "
                          f"(plan scales: {list(PLAN_DENOMS)}). This is a detail/joinery sheet.")
    if not shrink:
        raise RefuseSheet("no sheet shrink resolved; refusing to assume the page is at design size")
    # Snap in DESIGN-sheet points; report mm per PAGE point.
    modal, hits = geometry_snap([t / shrink for t in thin_dims_pt], denoms)
    modal = modal * shrink if modal is not None else None      # back to PAGE pt, the caller's unit
    scale = PT_MM * tb_denom / shrink
    if hits and tb_denom not in hits:
        raise RefuseSheet(
            f"SCALE DISAGREEMENT: the title block says 1:{tb_denom}, but the modal wall-pen "
            f"thickness {modal} pt is a 100 mm wall only at 1:{hits} "
            f"(at 1:{tb_denom} it would be {modal * scale:.0f} mm). REFUSING to pick a winner: "
            f"either the sheet was rescaled on export or this is not a wall class. "
            f"(Round 1 picked the GEOMETRY here and emitted the building at half size.)")
    if not hits:
        mm = modal * scale
        if not (WALL_MM_PLAUSIBLE_LO <= mm <= WALL_MM_PLAUSIBLE_HI):
            raise RefuseSheet(
                f"the title block says 1:{tb_denom}, at which the modal wall-pen thickness "
                f"{modal} pt is {mm:.0f} mm -- not a plausible wall "
                f"({WALL_MM_PLAUSIBLE_LO:.0f}-{WALL_MM_PLAUSIBLE_HI:.0f} mm). REFUSING.")
        note = (f"scale 1:{tb_denom} from the TITLE BLOCK; the wall geometry does not snap to any "
                f"denominator on its own, but {mm:.0f} mm is a plausible wall at the stated scale.")
        return scale, tb_denom, modal, note
    note = (f"scale 1:{tb_denom} stated by the TITLE BLOCK and CONFIRMED by the wall geometry "
            f"(modal {modal} pt = {modal * scale:.1f} mm).")
    return scale, tb_denom, modal, note


def is_wall_step(step_rect, wall_rects, tol=STEP_ADJ_TOL_MM):
    """A 35-50 mm wall-pen quad is a STEP (a thickening of a wall: the NW corner column) iff it
    TOUCHES a real wall band -- shares a face and overlaps it on the other axis. A free-floating
    40 mm sliver is furniture and stays out."""
    sx0, sy0, sx1, sy1 = step_rect
    for (wx0, wy0, wx1, wy1) in wall_rects:
        x_touch = min(abs(sx0 - wx1), abs(sx1 - wx0), abs(sx0 - wx0), abs(sx1 - wx1)) <= tol
        y_touch = min(abs(sy0 - wy1), abs(sy1 - wy0), abs(sy0 - wy0), abs(sy1 - wy1)) <= tol
        x_over = min(sx1, wx1) - max(sx0, wx0) > tol
        y_over = min(sy1, wy1) - max(sy0, wy0) > tol
        if (x_touch and y_over) or (y_touch and x_over):
            return True
    return False


def side_ink_fraction(bands, axis, pos, lo, hi, tol=150.0):
    """Fraction of one side of the footprint that carries wall ink."""
    if hi <= lo:
        return 0.0
    ivs = []
    for b in bands:
        if axis == "h":
            if min(abs(b[1] - pos), abs(b[3] - pos)) > tol:
                continue
            ivs.append((b[0], b[2]))
        else:
            if min(abs(b[0] - pos), abs(b[2] - pos)) > tol:
                continue
            ivs.append((b[1], b[3]))
    return _union_len(ivs) / (hi - lo)


def envelope_checks(bands):
    """Coarse PLAUSIBILITY floor on the wall ink: enough bands, a habitable footprint, and some
    wall ink on all four sides of it.

    HONESTY: this is the WEAKEST of the three gate signals and it is NOT the discriminator. On
    this PDF the real plan page has the WORST side-ink coverage of any candidate page (9%: its
    poche is a chain of stubs), while a joinery sheet reaches 93% on one side. It can only refuse
    the obviously-not-a-building; the title-block and scale checks do the real work."""
    if not bands:
        return [{"id": "E0", "name": "wall bands exist", "ok": False, "detail": "0 bands"}]
    x0 = min(b[0] for b in bands)
    y0 = min(b[1] for b in bands)
    x1 = max(b[2] for b in bands)
    y1 = max(b[3] for b in bands)
    w, h = x1 - x0, y1 - y0
    area = w * h / 1e6
    sides = {"south": side_ink_fraction(bands, "h", y0, x0, x1),
             "north": side_ink_fraction(bands, "h", y1, x0, x1),
             "west": side_ink_fraction(bands, "v", x0, y0, y1),
             "east": side_ink_fraction(bands, "v", x1, y0, y1)}
    worst = min(sides.values())
    return [
        {"id": "E1", "name": "enough wall bands for an enclosure",
         "ok": len(bands) >= MIN_PLAN_BANDS,
         "detail": f"{len(bands)} bands (need >= {MIN_PLAN_BANDS})"},
        {"id": "E2", "name": "habitable footprint",
         "ok": (FOOTPRINT_MIN_SIDE_MM <= w <= FOOTPRINT_MAX_SIDE_MM
                and FOOTPRINT_MIN_SIDE_MM <= h <= FOOTPRINT_MAX_SIDE_MM
                and area >= FOOTPRINT_MIN_AREA_M2),
         "detail": f"{w:.0f} x {h:.0f} mm = {area:.1f} m2 "
                   f"(sides {FOOTPRINT_MIN_SIDE_MM:.0f}-{FOOTPRINT_MAX_SIDE_MM:.0f} mm, "
                   f"area >= {FOOTPRINT_MIN_AREA_M2:.0f} m2)"},
        {"id": "E3", "name": "wall ink on all four sides of the footprint",
         "ok": worst >= SIDE_INK_MIN_FRAC,
         "detail": "  ".join(f"{k}={v:.2f}" for k, v in sides.items())
                   + f"  (worst {worst:.2f} >= {SIDE_INK_MIN_FRAC})"},
    ]


def plan_gate(drawing_title, page_text, tb_denom, bands):
    """The PAGE-TYPE GATE. Returns the full check list; the caller REFUSES if any check fails.

    NOTE read_bands() builds its OWN copy of T1/T2/T3 (it needs the page's spans and geometry). The
    two lists must stay in step -- a check added here alone would never execute on the corpus."""
    ok_t, why_t = title_is_floor_plan(drawing_title, page_text)
    ok_x, why_x = extent_is_a_storey(drawing_title, ok_t)
    checks = [
        {"id": "T1", "name": "title block names a PLAN", "ok": ok_t, "detail": why_t},
        {"id": "T3", "name": "the plan is of a STOREY, not of one room", "ok": ok_x,
         "detail": why_x},
        {"id": "T2", "name": "stated scale is a plan scale",
         "ok": tb_denom in PLAN_DENOMS,
         "detail": (f"title block says 1:{tb_denom}" if tb_denom else "no scale stated")
                   + f" (plan scales {list(PLAN_DENOMS)})"},
    ]
    return checks + envelope_checks(bands)


def band_axis(x0, y0, x1, y1):
    """'h' if the band's long axis is east-west, 'v' if north-south. A near-square band is a
    CORNER BLOCK: it is returned as 'sq' and participates in BOTH axes when merging runs."""
    w, h = abs(x1 - x0), abs(y1 - y0)
    if h == 0 or w == 0:
        return "h" if w >= h else "v"
    if max(w, h) / min(w, h) < SQUARE_ASPECT:
        return "sq"
    return "h" if w > h else "v"


def band_long_edges(x0, y0, x1, y1):
    """The TWO LONG EDGES of a band, as segments. build_floor.build_walls extrudes every segment
    as an independent thin slab with no topology, and its stated convention is that the drawing's
    double-lined walls become two parallel faces. So a 100 mm wall must be emitted as its two
    FACES, 100 mm apart. A single centreline would build a 24 mm ribbon instead of a wall.
    The 2 short end-caps are deliberately DROPPED (they pass keep_segment, so they would be
    accidentally kept, not accidentally excluded)."""
    if band_axis(x0, y0, x1, y1) == "v":
        return [[[x0, y0], [x0, y1]], [[x1, y0], [x1, y1]]]
    return [[[x0, y0], [x1, y0]], [[x0, y1], [x1, y1]]]


def _round_rect(r, nd=1):
    return tuple(round(v, nd) for v in r)


def merge_runs(bands, tol=1.0):
    """Collapse collinear, abutting/overlapping BANDS into RUNS.

    Bands are not a graph: the exporter emits one quad per wall stretch, so a single physical
    wall arrives as several abutting quads (plus square corner blocks). Openings can only be
    found once the pieces of one wall are one interval, so this is a prerequisite for part B,
    not a cosmetic tidy-up.

    Groups by (axis, thin-face-low, thin-face-high) rounded to `tol`; a 'sq' corner block joins
    BOTH the h and the v group so it can bridge a run (on the source sheet the east wall's
    100x100 jamb block is exactly what closes the run below the window gap).
    Returns {(axis, lo, hi): [(long_lo, long_hi), ...]} with intervals sorted and merged."""
    groups = collections.defaultdict(list)
    for (x0, y0, x1, y1) in bands:
        ax = band_axis(x0, y0, x1, y1)
        for a in (("h", "v") if ax == "sq" else (ax,)):
            if a == "h":                         # thin axis is y; long axis is x
                key = ("h", round(y0 / tol) * tol, round(y1 / tol) * tol)
                groups[key].append((x0, x1))
            else:                                # thin axis is x; long axis is y
                key = ("v", round(x0 / tol) * tol, round(x1 / tol) * tol)
                groups[key].append((y0, y1))
    runs = {}
    for key, ivs in groups.items():
        ivs.sort()
        merged = [list(ivs[0])]
        for lo, hi in ivs[1:]:
            if lo <= merged[-1][1] + tol:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        runs[key] = [tuple(m) for m in merged]
    return runs


def find_gaps(runs, min_gap=DEFAULT_MIN_GAP_MM):
    """Openings: the holes BETWEEN two collinear runs of the same wall.

    This is the whole reason part B exists. Wall ink on this convention stops at every door and
    every window — the glazing is drawn on a separate thin pen. A reader that emits only the ink
    hands build_floor an outline with metre-scale holes in it and still passes every wall-recall
    metric you can write. Returns a list of dicts (axis, face lo/hi, gap lo/hi, length)."""
    out = []
    for (axis, flo, fhi), ivs in sorted(runs.items()):
        for a, b in zip(ivs, ivs[1:]):
            g0, g1 = a[1], b[0]
            if g1 - g0 >= min_gap:
                out.append({"axis": axis, "face_lo": round(flo, 1), "face_hi": round(fhi, 1),
                            "gap_lo": round(g0, 1), "gap_hi": round(g1, 1),
                            "length_mm": round(g1 - g0, 1)})
    out.sort(key=lambda g: -g["length_mm"])
    return out


def gap_segments(gap):
    """The two face-segments that would BRIDGE an opening, if an owner signs it as solid/glazed.
    Same two-parallel-faces convention as band_long_edges."""
    flo, fhi, g0, g1 = gap["face_lo"], gap["face_hi"], gap["gap_lo"], gap["gap_hi"]
    if gap["axis"] == "h":
        return [[[g0, flo], [g1, flo]], [[g0, fhi], [g1, fhi]]]
    return [[[flo, g0], [flo, g1]], [[fhi, g0], [fhi, g1]]]


# =====================================================================================
# PART C — BOUNDARY INK: the second pen, the openings, and the CLOSED polygon
# =====================================================================================
def is_boundary_ink(dtype, color, width):
    """Class test for boundary ink (criteria 1-2 of the boundary predicate): a pure-black
    STROKE on any pen EXCEPT the wall pen. Width is carried and reported, never matched
    against a pen table -- see the 0.42 lesson at the constants block. The geometric half of
    the predicate (ticks, envelope, band alignment) lives in classify_panels."""
    if dtype != "s" or color is None or sum(color) > MAX_COLOR_SUM:
        return False
    return round(width or 0, 2) != WALL_PEN_PT


def is_dimension_tick(n_items, item_op, long_mm):
    """Criterion 3: a LONE 'l' shorter than TICK_MAX_MM is half of a dimension-chain '+' cross.
    Length, not position, is what separates them: 16 of the 108 crosses sit INSIDE the envelope
    on interior chains, so an inside/outside test alone would keep them."""
    return n_items == 1 and item_op == "l" and long_mm < TICK_MAX_MM


def rect_in(inner, outer):
    return (inner[0] >= outer[0] and inner[1] >= outer[1]
            and inner[2] <= outer[2] and inner[3] <= outer[3])


def run_keys(runs):
    """The (axis, face_lo, face_hi) keys of every merged wall run — the bands' face pairs."""
    return sorted(runs.keys())


def _ivs_overlap(a, b):
    """True iff two sorted interval lists share at least one point of positive length."""
    i = j = 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if hi > lo:
            return True
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return False


def _ivs_overlap_span(a, b):
    """Bounding span (lo, hi) of the overlap between two sorted interval lists."""
    lo = hi = None
    i = j = 0
    while i < len(a) and j < len(b):
        s, e = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if e > s:
            lo = s if lo is None else min(lo, s)
            hi = e if hi is None else max(hi, e)
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return (lo, hi)


def composite_run_keys(runs, cavity_tol=WALL_CAVITY_TOL_MM):
    """Face pairs of COMPOSITE walls, from ADJACENT parallel leaf PAIRS that (1) face each other
    within `cavity_tol`, (2) actually COEXIST somewhere along the axis (long extents overlap),
    and (3) stay within MAX_COMPOSITE_MM. Takes the runs DICT (key -> long intervals) because
    the extent test is load-bearing -- see WALL_CAVITY_TOL_MM. Pairs only, no transitive chains:
    a triple-leaf wall emits its two adjacent pairs, each honest on its own. A merged pair that
    duplicates an EXISTING plain key is dropped (the plain run already aligns everything the
    pair would, and the duplicate made via_composite lie -- review 2026-07-14, MINOR).

    Returns [((axis, face_lo, face_hi), (overlap_lo, overlap_hi)), ...]: the face pair PLUS the
    span where the leaves actually stack, which band_aligned uses to refuse ink that sits on
    the pair's axis but where only one (or neither) leaf exists."""
    plain = set(runs)
    out = []
    for axis in ("h", "v"):
        pairs = sorted((flo, fhi) for a, flo, fhi in runs if a == axis)
        for (alo, ahi), (blo, bhi) in zip(pairs, pairs[1:]):
            if blo - ahi > cavity_tol:
                continue
            if bhi - alo > MAX_COMPOSITE_MM:
                continue
            iva = runs[(axis, alo, ahi)]
            ivb = runs[(axis, blo, bhi)]
            if not _ivs_overlap(iva, ivb):
                continue
            key = (axis, alo, max(ahi, bhi))
            if key in plain:
                continue
            out.append((key, _ivs_overlap_span(iva, ivb)))
    return out


def band_aligned(rect, runs, tol=BAND_ALIGN_TOL_MM, composite=()):
    """Criterion 5: the path's span on some run's THIN axis lies inside that run's face pair.
    Keeps glazing/jamb/stile ink (it lives IN a wall run's gap, collinear with the wall);
    rejects the swinging door leaves, which stick out PERPENDICULAR to their wall.
    A path that fits NO single leaf is tried against the COMPOSITE pairs (double-leaf walls):
    Pandora's window rects span both 100 mm leaves of a 200 mm wall and fit neither alone.
    A composite match additionally requires the path to touch the span where the two leaves
    actually COEXIST -- ink elsewhere on the pair's axis is over one leaf at most and must
    earn plain alignment or be rejected (the extent clause, see WALL_CAVITY_TOL_MM)."""
    x0, y0, x1, y1 = rect
    for (axis, flo, fhi) in runs:
        lo, hi = (y0, y1) if axis == "h" else (x0, x1)
        if lo >= flo - tol and hi <= fhi + tol:
            return (axis, flo, fhi)
    for (axis, flo, fhi), (elo, ehi) in composite:
        lo, hi = (y0, y1) if axis == "h" else (x0, x1)
        llo, lhi = (x0, x1) if axis == "h" else (y0, y1)
        if (lo >= flo - tol and hi <= fhi + tol
                and elo is not None and lhi >= elo - tol and llo <= ehi + tol):
            return (axis, flo, fhi)
    return None


def classify_panels(paths, runs, env):
    """paths: [{"rect": (x0,y0,x1,y1) mm, "n_items", "op", "w"}] of the BOUNDARY-INK class.
    `runs` is the merge_runs DICT (composite pairing needs the long extents).
    Returns (boundary, rejected) — boundary entries carry the run they align to (a COMPOSITE
    pair when no single leaf fits, flagged via_composite) and their pen width `w`."""
    comp = composite_run_keys(runs)
    comp_set = {k for k, _ext in comp}
    keys = run_keys(runs)
    boundary, rejected = [], []
    for p in paths:
        r = p["rect"]
        long_mm = max(r[2] - r[0], r[3] - r[1])
        if is_dimension_tick(p["n_items"], p["op"], long_mm):
            rejected.append({**p, "why": "dimension tick"})
            continue
        if not rect_in(r, env):
            rejected.append({**p, "why": "outside envelope (sheet/clip frame)"})
            continue
        run = band_aligned(r, keys, composite=comp)
        if run is None:
            rejected.append({**p, "why": "not band-aligned (perpendicular door leaf)"})
            continue
        boundary.append({**p, "run": run, "via_composite": run in comp_set})
    return boundary, rejected


def all_gaps(runs):
    """EVERY hole between collinear runs of one wall — no minimum. find_gaps() filters by
    min_gap for the human report; closure has to see the small ones too, because those are
    exactly the undrawn stubs it must infill (and log)."""
    out = []
    for (axis, flo, fhi), ivs in sorted(runs.items()):
        for a, b in zip(ivs, ivs[1:]):
            out.append({"axis": axis, "face_lo": round(flo, 1), "face_hi": round(fhi, 1),
                        "gap_lo": round(a[1], 1), "gap_hi": round(b[0], 1),
                        "length_mm": round(b[0] - a[1], 1)})
    return out


def gap_rect(g):
    """The gap as a plan rect [x0,y0,x1,y1] — the wall's own footprint over the hole. This is
    the rect floor_openings.py consumes (opening['rect'])."""
    if g["axis"] == "h":
        return [g["gap_lo"], g["face_lo"], g["gap_hi"], g["face_hi"]]
    return [g["face_lo"], g["gap_lo"], g["face_hi"], g["gap_hi"]]


def _union_len(ivs):
    if not ivs:
        return 0.0
    ivs = sorted(ivs)
    tot, cs, ce = 0.0, ivs[0][0], ivs[0][1]
    for a, b in ivs[1:]:
        if a > ce:
            tot += ce - cs
            cs, ce = a, b
        else:
            ce = max(ce, b)
    return tot + (ce - cs)


def _run_backs_gap(prun, key):
    """True iff the run a path aligned to CONTAINS the gap's face pair (same axis).
    Equality for a plain run; a COMPOSITE pair (the outermost faces of a double-leaf wall)
    contains each leaf's own gaps, so ink spanning the wall backs both leaves' holes.
    Ink on a DIFFERENT wall still backs nothing -- containment, not proximity."""
    if not prun or prun[0] != key[0]:
        return False
    return prun[1] <= key[1] + 0.11 and key[2] <= prun[2] + 0.11


def gap_coverage(g, boundary):
    """Fraction of a gap's long-axis span covered by band-aligned boundary ink whose run
    BACKS this gap (the same wall, or the composite wall this gap's leaf belongs to)."""
    key = (g["axis"], g["face_lo"], g["face_hi"])
    L = g["length_mm"]
    if L <= 0:
        return 0.0
    ivs = []
    for p in boundary:
        if not _run_backs_gap(p["run"], key):
            continue
        r = p["rect"]
        lo, hi = (r[0], r[2]) if g["axis"] == "h" else (r[1], r[3])
        a, b = max(lo, g["gap_lo"]), min(hi, g["gap_hi"])
        if b > a:
            ivs.append((a, b))
    return _union_len(ivs) / L


def gap_pen_mm(g, boundary):
    """{pen_pt: mm-of-ink} backing this gap, largest first. The class no longer filters on
    width (the 0.42 lesson), so the width EVIDENCE must stay visible: an opening backed only
    by 0.12-pt hairline reads differently to a reviewer than one backed by a glazing pen.
    Overlapping paths are summed as drawn -- this is ink mm, not coverage."""
    key = (g["axis"], g["face_lo"], g["face_hi"])
    out = {}
    for p in boundary:
        if not _run_backs_gap(p["run"], key):
            continue
        r = p["rect"]
        lo, hi = (r[0], r[2]) if g["axis"] == "h" else (r[1], r[3])
        a, b = max(lo, g["gap_lo"]), min(hi, g["gap_hi"])
        if b > a:
            w = p.get("w")
            out[w] = out.get(w, 0.0) + (b - a)
    return {str(w): round(mm, 1)
            for w, mm in sorted(out.items(), key=lambda kv: -kv[1])}


def gap_composite_mm(g, boundary):
    """mm of this gap's backing that arrived through a COMPOSITE pair (via_composite paths).
    The composite mechanism is the newest and most permissive door into the boundary class, so
    an opening that exists ONLY through it must say so downstream -- same evidence law as
    gap_pen_mm (review 2026-07-14: the flag used to die at the sheet-level note)."""
    key = (g["axis"], g["face_lo"], g["face_hi"])
    mm = 0.0
    for p in boundary:
        if not p.get("via_composite") or not _run_backs_gap(p["run"], key):
            continue
        r = p["rect"]
        lo, hi = (r[0], r[2]) if g["axis"] == "h" else (r[1], r[3])
        a, b = max(lo, g["gap_lo"]), min(hi, g["gap_hi"])
        if b > a:
            mm += b - a
    return round(mm, 1)


def gap_ink_intervals(g, boundary):
    """The intervals of a gap's long axis that panel ink ACTUALLY covers (union, clipped to the
    gap). `gap_coverage` is exactly union_len(these) / g.length_mm -- this returns WHERE."""
    key = (g["axis"], g["face_lo"], g["face_hi"])
    ivs = []
    for p in boundary:
        if not _run_backs_gap(p["run"], key):
            continue
        r = p["rect"]
        lo, hi = (r[0], r[2]) if g["axis"] == "h" else (r[1], r[3])
        a, b = max(lo, g["gap_lo"]), min(hi, g["gap_hi"])
        if b > a:
            ivs.append((a, b))
    if not ivs:
        return []
    ivs.sort()
    out = [list(ivs[0])]
    for a, b in ivs[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def gap_ink_rects(g, boundary):
    """The BACKED sub-rects of an opening: the wall band's own footprint (face_lo..face_hi across),
    but only over the spans where panel ink is actually drawn.

    THE AUDIT WAS FABRICATING (round 3, FATAL 2). audit_sides was handed `gap_rect(g)` -- the
    opening's FULL footprint -- as backing of kind "opening", regardless of that opening's own
    ink_coverage. O01 on the source sheet has ink_coverage 0.616: 250 mm of BLANK PAPER inside a
    650 mm window was credited as backed, by the very instrument built to catch fabrication (the
    10th recurrence of the flattering scorer, and the 2nd one INSIDE the audit). It would launder
    up to (1 - GLAZING_COVER_FRAC) = 40% of EVERY opening.

    Now an opening backs only the millimetres it inks. The rest is unbacked, and it shows."""
    r = gap_rect(g)
    out = []
    for a, b in gap_ink_intervals(g, boundary):
        out.append([a, r[1], b, r[3]] if g["axis"] == "h" else [r[0], a, r[2], b])
    return out


def audit_sides(outline, backing, tol=BAND_ALIGN_TOL_MM + GRID_MM):
    """For EVERY side of the derived polygon, what ink actually backs it.

    This is the anti-flattering-scorer. `closed=True` only says the flood did not escape; it
    says nothing about whether a side is a real wall. This function walks each edge and reports
    the mm of it that lie on a face of a wall-poche band / a boundary-ink opening / a closure
    infill / an OWNER-SIGNED VIRTUAL edge — and the mm backed by NOTHING. It can fail, loudly.

    backing: [(rect, kind)] with kind in {wall_poche, opening, closure_infill, signed_virtual}.

    THE CORNER-CREDIT BUG (found by test_audit_sides_REPORTS_an_unbacked_edge, round 2). The
    original match test was `min(|f0-pos|, |f1-pos|) <= tol` on the rect's cross-axis extent. For
    a rect that runs ALONG the edge's cross axis -- e.g. a 3 m horizontal wall whose END lands on
    a vertical edge's x -- that end reads as a "face", and the perpendicular wall was credited as
    backing the edge for the 100 mm where they touch at the corner. Up to 100 mm per corner of
    pure fabrication, laundered as ink, inside the very audit that exists to catch fabrication.
    The 9th recurrence of the flattering scorer in this project, and it recurred INSIDE the
    instrument built to stop it.

    The fix: a rect may only back an edge if it is THIN across it (a wall band is <= 300 mm thick;
    a 3 m run is not a face). Corner blocks stay eligible on both axes, which is correct -- they
    are real ink at the corner."""
    order = ["wall_poche", "opening", "closure_infill", "signed_virtual"]
    out = []
    n = len(outline)
    for i in range(n):
        (ax_, ay), (bx, by) = outline[i], outline[(i + 1) % n]
        vertical = abs(bx - ax_) < 1e-6
        lo, hi = (min(ay, by), max(ay, by)) if vertical else (min(ax_, bx), max(ax_, bx))
        L = hi - lo
        if L <= 0:
            continue
        pos, claimed = ax_ if vertical else ay, []
        per = {}
        for kind in order:
            ivs = []
            for rect, k in backing:
                if k != kind:
                    continue
                f0, f1 = (rect[0], rect[2]) if vertical else (rect[1], rect[3])
                if f1 - f0 > MAX_BACKING_THICK_MM:
                    continue            # runs ALONG the cross axis: its END is not a FACE
                if min(abs(f0 - pos), abs(f1 - pos)) > tol:
                    continue
                s0, s1 = (rect[1], rect[3]) if vertical else (rect[0], rect[2])
                a, b = max(s0, lo), min(s1, hi)
                if b > a:
                    ivs.append((a, b))
            # a mm of edge is credited to the FIRST kind that covers it (poche wins over infill)
            fresh = []
            for a, b in ivs:
                seg = [(a, b)]
                for ca, cb in claimed:
                    nxt = []
                    for s, e in seg:
                        if cb <= s or ca >= e:
                            nxt.append((s, e))
                            continue
                        if ca > s:
                            nxt.append((s, ca))
                        if cb < e:
                            nxt.append((cb, e))
                    seg = nxt
                fresh += seg
            claimed += fresh
            if fresh:
                per[kind] = round(_union_len(fresh), 1)
        backed = round(_union_len(claimed), 1)
        out.append({"edge": [[ax_, ay], [bx, by]],
                    "axis": "v" if vertical else "h", "length_mm": round(L, 1),
                    "backed_mm": backed, "unbacked_mm": round(L - backed, 1),
                    "backing": per})
    return out


def openings_on_outline(outline, openings, tol=BAND_ALIGN_TOL_MM + GRID_MM):
    """The openings that lie ON this room's polygon -- i.e. the ones this room can see out of.

    ROUND 3, FATAL 1. The room-spec was emitted as {"outline_mm", "ceiling_mm"} and the openings
    were DROPPED, so the living zone -- whose 3200 mm south slider and 2900 mm east slider this
    reader correctly measured out of the ink -- rendered as five meshes: a floor and four blank
    walls. A SEALED SHOEBOX. The openings must travel WITH the outline or the room is not the room
    the plan draws.

    Same eligibility test as audit_sides: the opening's rect must be THIN across the edge (it is a
    wall band, not a run along it) and its face must sit on the edge; its span must overlap the
    edge. Emits the opening dict + the edge it landed on."""
    out, n = [], len(outline)
    for o in openings:
        r = [float(v) for v in o["rect"]]
        for i in range(n):
            (ax_, ay), (bx, by) = outline[i], outline[(i + 1) % n]
            vertical = abs(bx - ax_) < 1e-6
            lo, hi = (min(ay, by), max(ay, by)) if vertical else (min(ax_, bx), max(ax_, bx))
            pos = ax_ if vertical else ay
            f0, f1 = (r[0], r[2]) if vertical else (r[1], r[3])
            if f1 - f0 > MAX_BACKING_THICK_MM:
                continue                          # runs ALONG the cross axis: not this edge's face
            if min(abs(f0 - pos), abs(f1 - pos)) > tol:
                continue
            s0, s1 = (r[1], r[3]) if vertical else (r[0], r[2])
            if min(s1, hi) - max(s0, lo) <= 1.0:
                continue
            out.append({**o, "on_edge": [[ax_, ay], [bx, by]]})
            break
    return out


def ink_faces(bands):
    """Every wall FACE coordinate on the sheet, per axis. The only coordinates a virtual edge
    is allowed to use."""
    return (sorted({b[0] for b in bands} | {b[2] for b in bands}),
            sorted({b[1] for b in bands} | {b[3] for b in bands}))


def parse_virtual_edge(spec, bands, tol=SNAP_TOL_MM):
    """'h:4970:5069:3120:7720' -> a wall the SHEET DOES NOT DRAW, that an owner is signing.

    A zoning line (living vs. circulation in an open plan) is a SEMANTIC call and the two-layer
    law reserves it to the owner. What this reader CAN enforce is that every number in it is a
    real ink face: face_lo/face_hi must be existing wall faces on the thin axis, and lo/hi must
    be existing wall faces on the long axis. A virtual edge floating at an invented coordinate
    is refused. It is still NOT INK, it is still counted as virtual in the side audit, and it
    still forces ink_backed=False.

    ROUND 3, FATAL 3(b) -- IT VALIDATED BUT DID NOT SNAP. The old body checked each number against
    the nearest ink face within `tol` and then USED THE NUMBER THE HUMAN TYPED. So `h:4995:...`
    -- 25 mm off the real 4969.9 face -- was ACCEPTED, the flood solid went in 25 mm off, the
    polygon snap (which was unconditional, see SNAP_TOL_MM) quietly pulled the OUTLINE back, and
    the room grew by 25 mm with unbacked_perimeter still reading 0.2 mm. A validator that does not
    bind the value it validated is a rubber stamp.

    Now: the coordinate is SNAPPED ONTO the face it validated against, and every non-zero
    correction is REPORTED (snap_deltas_mm, and `snapped` -> a REVIEW note in the emitted json).
    A signed edge can no longer sit anywhere except on ink."""
    try:
        axis, f0, f1, lo, hi = spec.split(":")
        f0, f1, lo, hi = float(f0), float(f1), float(lo), float(hi)
    except ValueError:
        raise RefuseSheet(f"--virtual-edge {spec!r}: want AXIS:FACE_LO:FACE_HI:LO:HI "
                          f"(e.g. h:4970:5069:3120:7720)")
    if axis not in ("h", "v"):
        raise RefuseSheet(f"--virtual-edge {spec!r}: axis must be h or v")
    fx, fy = ink_faces(bands)
    thin, long_ = (fy, fx) if axis == "h" else (fx, fy)
    snapped, deltas = {}, {}
    for v, cands, what in ((f0, thin, "face_lo"), (f1, thin, "face_hi"),
                           (lo, long_, "lo"), (hi, long_, "hi")):
        near = min(cands, key=lambda c: abs(c - v)) if cands else None
        if near is None or abs(near - v) > tol:
            raise RefuseSheet(
                f"--virtual-edge {spec!r}: {what}={v} is not a wall face on this sheet "
                f"(nearest ink face {near}). A virtual edge may only be signed onto real ink "
                f"coordinates — an invented number is a fabricated wall.")
        snapped[what] = round(near, 1)                     # <- BIND to the face, do not trust the typing
        deltas[what] = round(near - v, 1)
    f0, f1 = snapped["face_lo"], snapped["face_hi"]
    lo, hi = snapped["lo"], snapped["hi"]
    if hi <= lo or f1 <= f0:
        raise RefuseSheet(f"--virtual-edge {spec!r}: degenerate")
    moved = {k: d for k, d in deltas.items() if abs(d) > VIRTUAL_SNAP_TOL_MM}
    return {"axis": axis, "face_lo": f0, "face_hi": f1,
            "gap_lo": lo, "gap_hi": hi, "length_mm": round(hi - lo, 1),
            "ink_coverage": 0.0,
            "snap_deltas_mm": deltas,
            "snapped": bool(moved),
            "snap_note": (
                "SNAPPED onto the ink faces it validated against: %s. The typed coordinate was "
                "NOT used. (Round 2 validated and then used the typed number, so a 25 mm-off "
                "signature grew the room by 25 mm with unbacked still reading 0.2 mm.)"
                % ", ".join(f"{k} moved {d:+.1f} mm" for k, d in moved.items())) if moved else
                "typed coordinates already sat on ink faces (no snap correction needed)"}


# =====================================================================================
# ROUND 5, D1 -- THE OWNER SIGNATURE WAS FORGEABLE BY THE AGENT. IT IS NOW A LEDGER.
#
# Round 4 bound the signature to the geometry it NAMED: a free-text --owner-signature carrying an
# `edges=` clause, plus a bijection check against the --owner-edge argv and a prose-coherence check
# on any x=/y= in the note. The reviewer broke it in one line: THE AGENT AUTHORED BOTH SIDES OF THE
# BIJECTION. Two attacks were RUN and both SUCCEEDED:
#
#   ATTACK A  --owner-edge h:3905:4005:3120:7720
#             --owner-signature "... | edges=h:3905:4005:3120:7720 | note=... y=3905 ..."
#             -> self-consistent. Bijection PASSES. Prose coherence PASSES. EXIT 0, WRITTEN,
#                17.5 m2 "owner-signed" -- a zoning line the owner never saw.
#   ATTACK B  the three AGENT-PROVISIONAL edges re-passed as --owner-edge and named in one forged
#             signature -> virtual_agent_provisional_mm 1984.3 -> 0, owner_authorised_mm 4600.5 ->
#             6584.8. EXIT 0. The agent's guesses laundered into owner geometry.
#   AND ink_provenance.owner_signature_binding.bijection_verified was `True` in EVERY artefact on
#   disk (a failed bijection refused the write) -- a CONSTANT dressed as an audit result.
#
# ROOT CAUSE: the signature was bound to ARGV, not to the OWNER. Nothing in the loop was authored by
# anyone but the agent. A grammar cannot fix that; only PROVENANCE can.
#
# THE FIX (the pattern this repo already proved in ffe_signoff_gate.py, 2026-07-11): the OWNER writes
# an append-only LEDGER; the gate matches a CANONICAL KEY against it; the agent can only READ it.
#   * --owner-signature is GONE. Passing it is an error that points at the ledger.
#   * --owner-edge is authorised IFF its canonical key -- sheet-namespaced, snapped onto real ink at
#     0.1 mm -- is in the ledger under a VALID entry (real `by` + `date` + `key`; sign_status is
#     IMPORTED from ffe_signoff_gate so the studio has ONE definition of a signature).
#   * ATTACK A now dies because the bogus edge's key is not in the ledger; ATTACK B dies because the
#     agent's three edges have no entries. Neither can be fixed by anything the agent can TYPE.
#   * The ledger itself is protected from the agent by the PreToolUse guard hooks. That -- not this
#     file -- is what makes the signature unforgeable-with-the-agent's-tools. See
#     zoning_signoff_gate.py's RESIDUAL TRUST block for what is still open.
# =====================================================================================
import zoning_signoff_gate as ZSG  # noqa: E402  (canonical key + ledger; ONE signing mechanism)

OWNER_SIG_DEAD = (
    "--owner-signature IS GONE (round 5). A signature the CALLER composes at run time is authored "
    "by the caller, not by the owner: the agent authored both sides of round 4's bijection, and a "
    "self-consistent signature naming a bogus edge (h:3905:4005:3120:7720) wrote a 17.5 m2 "
    "'owner-signed' room. The owner now writes a LEDGER and this reader only READS it.\n"
    "  Use: --owner-ledger <zoning-signoff.json> --owner-edge <AXIS:FACE_LO:FACE_HI:LO:HI>\n"
    "  To find the key an owner must sign: add --ledger-keys (prints the canonical key; it is "
    "NOT a signature and writing it into the ledger is the OWNER's act, not the agent's).")


def edge_key(ve):
    """The identity of an edge, AFTER snapping. Two edges are the same edge iff this matches."""
    return (ve["axis"], round(ve["face_lo"], 1), round(ve["face_hi"], 1),
            round(ve["gap_lo"], 1), round(ve["gap_hi"], 1))


def _stub_backers(g, boundary, tol=None):
    """The boundary paths allowed to back a SUB-CLOSE_TOL gap: same-run (or composite) ink whose
    span TERMINATES within `tol` of the gap's jambs. A 2551 mm polyline crossing a 99 mm stub is
    dimension/grid-shaped ink, not a drawn opening -- it backs nothing here (Pandora p8, the one
    measured fabrication; see STUB_BACKER_OVERSHOOT_MM for the 24x margins)."""
    if tol is None:
        tol = STUB_BACKER_OVERSHOOT_MM
    key = (g["axis"], g["face_lo"], g["face_hi"])
    out = []
    for p in boundary:
        if not _run_backs_gap(p["run"], key):
            continue
        r = p["rect"]
        lo, hi = (r[0], r[2]) if g["axis"] == "h" else (r[1], r[3])
        if min(hi, g["gap_hi"]) <= max(lo, g["gap_lo"]):
            continue
        if max(0.0, g["gap_lo"] - lo) + max(0.0, hi - g["gap_hi"]) <= tol:
            out.append(p)
    return out


def resolve_gaps(gaps, boundary, close_tol=CLOSE_TOL_MM, cover=GLAZING_COVER_FRAC):
    """Every gap becomes exactly one of:
       OPENING — ink backs >= `cover` of its span: a real door/window/glass. NEVER bridged as
                 wall; emitted for floor_openings so it is CUT and re-glazed. A gap SHORTER
                 than `close_tol` (no door leaf is that narrow — frame members, thresholds)
                 opens only on JAMB-TERMINATED ink: since the class widened to every non-wall
                 pen, a long line CROSSING a stub could otherwise cut a wall open (review
                 2026-07-14, MAJOR, measured live on Pandora p8).
       INFILL  — shorter than the DECLARED closure tolerance, no (jamb-terminated) ink: an
                 undrawn stub. Bridged with wall, and LOGGED with its size — and when crossing
                 ink was REFUSED above, logged with that evidence too.
       VOID    — long, and no ink of any class. NOT an opening and NOT a wall. It stays open,
                 and the room does not close through it. This is the honest failure channel."""
    infill, openings, voids = [], [], []
    for g in gaps:
        c = gap_coverage(g, boundary)
        rec = {**g, "ink_coverage": round(c, 3)}
        if g["length_mm"] >= close_tol:
            if c >= cover:
                rec["ink_pens"] = gap_pen_mm(g, boundary)
                rec["composite_backed_mm"] = gap_composite_mm(g, boundary)
                openings.append(rec)
            else:
                voids.append(rec)
            continue
        jamb = _stub_backers(g, boundary)
        cj = gap_coverage(g, jamb)
        if cj >= cover:
            rec["ink_coverage"] = round(cj, 3)
            rec["ink_pens"] = gap_pen_mm(g, jamb)
            rec["composite_backed_mm"] = gap_composite_mm(g, jamb)
            openings.append(rec)
        else:
            if c > 0 and cj < c:
                # the refusal is EVIDENCE, not a silent drop: what crossed, and how much
                rec["crossing_ink_refused"] = True
                rec["crossing_ink_pens"] = gap_pen_mm(g, boundary)
            infill.append(rec)
    return infill, openings, voids


# --------------------------------------------------------------- occupancy + flood + contour
def _cells_of(rect, gx0, gy0, nx, ny, step):
    i0 = max(0, int((rect[0] - gx0) / step))
    i1 = min(nx - 1, int((rect[2] - gx0) / step))
    j0 = max(0, int((rect[1] - gy0) / step))
    j1 = min(ny - 1, int((rect[3] - gy0) / step))
    for i in range(i0, i1 + 1):
        cx = gx0 + (i + 0.5) * step
        if not (rect[0] <= cx <= rect[2]):
            continue
        for j in range(j0, j1 + 1):
            cy = gy0 + (j + 0.5) * step
            if rect[1] <= cy <= rect[3]:
                yield (i, j)


def flood_region(solid_rects, seed, env, step=GRID_MM):
    """4-connected flood from an OWNER-SUPPLIED seed over the free cells of the envelope.
    Returns (filled_cells, grid_origin, nx, ny, leaked). `leaked` is True iff the fill reached
    the envelope border — i.e. the boundary has a hole and the "room" is the outdoors."""
    gx0, gy0, gx1, gy1 = env
    nx = int(math.ceil((gx1 - gx0) / step))
    ny = int(math.ceil((gy1 - gy0) / step))
    solid = set()
    for r in solid_rects:
        solid.update(_cells_of(r, gx0, gy0, nx, ny, step))
    si = int((seed[0] - gx0) / step)
    sj = int((seed[1] - gy0) / step)
    if not (0 <= si < nx and 0 <= sj < ny):
        raise RefuseSheet(f"seed {seed} is outside the envelope {env}")
    if (si, sj) in solid:
        raise RefuseSheet(f"seed {seed} lands INSIDE wall ink — move it into open floor")
    filled, stack, leaked = {(si, sj)}, [(si, sj)], False
    while stack:
        i, j = stack.pop()
        if i in (0, nx - 1) or j in (0, ny - 1):
            leaked = True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (i + di, j + dj)
            if not (0 <= n[0] < nx and 0 <= n[1] < ny):
                continue
            if n in solid or n in filled:
                continue
            filled.add(n)
            stack.append(n)
    return filled, (gx0, gy0), nx, ny, leaked


def trace_contours(filled, origin, step=GRID_MM):
    """Boundary loops of a filled cell set, CCW, as mm polygons (one per connected boundary;
    the longest is the outer ring, any others are holes = free-standing columns)."""
    gx0, gy0 = origin
    edges = {}
    for (i, j) in filled:
        x0, y0 = gx0 + i * step, gy0 + j * step
        x1, y1 = x0 + step, y0 + step
        for (di, dj), (a, b) in (((0, -1), ((x0, y0), (x1, y0))),
                                 ((1, 0), ((x1, y0), (x1, y1))),
                                 ((0, 1), ((x1, y1), (x0, y1))),
                                 ((-1, 0), ((x0, y1), (x0, y0)))):
            if (i + di, j + dj) not in filled:
                edges.setdefault(a, []).append(b)
    loops = []
    while edges:
        start = next(iter(edges))
        pt, loop = start, [start]
        while True:
            nxts = edges.get(pt)
            if not nxts:
                break
            nxt = nxts.pop()
            if not nxts:
                del edges[pt]
            pt = nxt
            if pt == start:
                break
            loop.append(pt)
        if len(loop) >= 4:
            loops.append(loop)
    loops.sort(key=lambda L: -abs(_shoelace(L)))
    return loops


def _shoelace(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def simplify_collinear(poly, tol=1e-6):
    out = []
    n = len(poly)
    for i in range(n):
        px, py = poly[i - 1]
        cx, cy = poly[i]
        nx, ny = poly[(i + 1) % n]
        if abs((cx - px) * (ny - cy) - (cy - py) * (nx - cx)) > tol:
            out.append((cx, cy))
    return out


def snap_polygon(poly, xs, ys, tol=SNAP_TOL_MM):
    """Pull every vertex back onto a REAL ink face. The flood grid quantises to `step`; the
    faces are the truth. A coordinate with no face within `tol` is left alone (and that is
    visible in the output, because it will not be a round ink number)."""
    def snap(v, cands):
        if not cands:
            return v
        best = min(cands, key=lambda c: abs(c - v))
        return best if abs(best - v) <= tol else v
    return [(round(snap(x, xs), 1), round(snap(y, ys), 1)) for x, y in poly]


def derive_room_polygon(bands, solid_rects, seed, step=GRID_MM):
    """The milestone: a CLOSED polygon whose every side is a wall/opening face that exists in
    ink. Flood the free floor from an owner seed, take the boundary of what it reached, snap it
    to the ink faces. Raises nothing; returns a dict whose `closed` is False if the fill leaked
    (a hole in the boundary) — a metric that CAN fail."""
    bx0 = min(b[0] for b in bands) - ENV_MARGIN_MM
    by0 = min(b[1] for b in bands) - ENV_MARGIN_MM
    bx1 = max(b[2] for b in bands) + ENV_MARGIN_MM
    by1 = max(b[3] for b in bands) + ENV_MARGIN_MM
    filled, origin, nx, ny, leaked = flood_region(solid_rects, seed, (bx0, by0, bx1, by1), step)
    loops = trace_contours(filled, origin, step)
    if not loops:
        return {"closed": False, "why": "flood produced no contour", "outline_mm": None,
                "_filled": filled, "_origin": origin}
    xs = sorted({b[0] for b in bands} | {b[2] for b in bands})
    ys = sorted({b[1] for b in bands} | {b[3] for b in bands})
    outer = simplify_collinear(snap_polygon(simplify_collinear(loops[0]), xs, ys))
    if _shoelace(outer) < 0:
        outer = outer[::-1]
    holes = [simplify_collinear(snap_polygon(simplify_collinear(L), xs, ys)) for L in loops[1:]]
    area = abs(_shoelace(outer)) / 1e6
    return {"closed": not leaked,
            "why": ("the flood reached the envelope border: the boundary has a HOLE and this "
                    "'room' is the outdoors" if leaked else "flood contained by boundary ink"),
            "outline_mm": [[x, y] for x, y in outer],
            "n_vertices": len(outer),
            "area_m2": round(area, 2),
            "holes_mm": [[[x, y] for x, y in h] for h in holes],
            "grid_mm": step, "seed_mm": [round(seed[0], 1), round(seed[1], 1)],
            "cells_filled": len(filled), "_filled": filled, "_origin": origin}


def _cell(pt, origin, step=GRID_MM):
    return (int((pt[0] - origin[0]) / step), int((pt[1] - origin[1]) / step))


def type_openings(openings, filled, origin, leaf_rects, step=GRID_MM, probe=200.0):
    """Give each opening the (id, type, rect) floor_openings.py actually consumes.

    TYPE IS SEMANTIC, so the rule is MECHANICAL and DECLARED, and every emitted type carries
    signed=false. The two signals are both ink:
      * which SIDES of the wall are interior floor (from the flood): exactly one -> the opening
        is in the ENVELOPE (glazed); both -> it is an interior partition (a door).
      * the LEAF pen inside the opening rect: >=2 leaf detail lines -> a SLIDING leaf assembly;
        none -> a fixed window.
    No length threshold is used, and none of this is a measurement of sill/head — build_floor's
    heights are disclosed render defaults."""
    out = []
    for i, g in enumerate(sorted(openings, key=lambda g: (g["axis"], g["face_lo"], g["gap_lo"]))):
        r = gap_rect(g)
        mid = ((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0)
        if g["axis"] == "h":
            a = _cell((mid[0], g["face_lo"] - probe), origin, step)
            b = _cell((mid[0], g["face_hi"] + probe), origin, step)
        else:
            a = _cell((g["face_lo"] - probe, mid[1]), origin, step)
            b = _cell((g["face_hi"] + probe, mid[1]), origin, step)
        ia, ib = a in filled, b in filled
        n_leaf = sum(1 for lr in leaf_rects
                     if r[0] - 50 <= (lr[0] + lr[2]) / 2.0 <= r[2] + 50
                     and r[1] - 50 <= (lr[1] + lr[3]) / 2.0 <= r[3] + 50)
        if ia != ib:                                   # envelope: floor on ONE side only
            t = "sliding" if n_leaf >= LEAF_MIN_PATHS else "window"
            side = "envelope"
        elif ia and ib:                                # floor on BOTH sides: a partition
            t = "door"
            side = "interior partition"
        else:                                          # not on this room's boundary at all
            t = "sliding" if n_leaf >= LEAF_MIN_PATHS else "door"
            side = "off-room (neither side is this room's floor)"
        out.append({"id": f"O{i:02d}", "type": t, "rect": [round(v, 1) for v in r],
                    "length_mm": g["length_mm"], "axis": g["axis"],
                    "ink_coverage": g["ink_coverage"], "ink_pens": g.get("ink_pens"),
                    "composite_backed_mm": g.get("composite_backed_mm", 0.0),
                    "leaf_pen_paths": n_leaf,
                    "context": side, "signed": False,
                    "provenance": "bluehouse_plan_reader part C: gap in the wall-poche run, "
                                  "backed by >=%.0f%% band-aligned boundary ink (pens/mm: %s%s)"
                                  % (GLAZING_COVER_FRAC * 100, g.get("ink_pens"),
                                     "; %.1f mm via a composite double-leaf pair"
                                     % g["composite_backed_mm"]
                                     if g.get("composite_backed_mm") else "")})
    return out


def outline_from_seed(bands, seed):
    """Cast 4 axis rays from a seed point and return the nearest wall FACE in each direction.

    This is the ONLY room-outline derivation in this module and it is deliberately timid. It
    reports, per side, the face it hit or None. It NEVER closes a side it did not hit — a side
    with no wall ink across it comes back as an `open_side`, and the caller must not pretend
    otherwise. (On the source sheet 3 of the 4 sides of the main living zone come back open.
    Any outline that looks tidy there was inferred by a human, not measured by this function.)

    Returns {"seed", "west","east","south","north", "open_sides", "inner_wh"}."""
    sx, sy = seed
    west = max((b[2] for b in bands if b[2] <= sx and b[1] < sy < b[3]), default=None)
    east = min((b[0] for b in bands if b[0] >= sx and b[1] < sy < b[3]), default=None)
    south = max((b[3] for b in bands if b[3] <= sy and b[0] < sx < b[2]), default=None)
    north = min((b[1] for b in bands if b[1] >= sy and b[0] < sx < b[2]), default=None)
    sides = {"west": west, "east": east, "south": south, "north": north}
    open_sides = sorted(k for k, v in sides.items() if v is None)
    inner = None
    if not open_sides:
        inner = [round(east - west, 1), round(north - south, 1)]
    return {"seed": [round(sx, 1), round(sy, 1)],
            **{k: (round(v, 1) if v is not None else None) for k, v in sides.items()},
            "open_sides": open_sides, "inner_wh_mm": inner}


# =====================================================================================
# PDF-FACING (needs fitz)
# =====================================================================================
def page_spans(page):
    """[(x, y, text)] for every text span on the page, in page coords (y DOWN)."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            for s in line.get("spans", []):
                out.append((s["bbox"][0], s["bbox"][1], s["text"]))
    return out


def titleblock_scale_denom(spans, page_text):
    """The STATED scale, read out of the TITLE BLOCK's own SCALE field — positionally, not by
    grepping the page. The joinery sheets print '1:25' captions under every view; the sheet's
    scale is the one in the title block, and that is the only one that may calibrate a build.

    On this exporter the field is: label span 'SCALE :' with the value span directly beneath it
    ('1 : 50  '). If there is no such field, we return None and the caller REFUSES — we do NOT
    fall back to the page-wide modal 1:NN, because on a detail sheet that modal is a caption and
    would fail open exactly where this gate exists to fail closed.

    NOTE the label is 'SCALE :' with the colon: plain 'SCALE' also prefix-matches the boilerplate
    'SCALED  DIMENSIONS. CONTRACTOR TO VERIFY...' disclaimer, which parses to no ratio at all."""
    val = titleblock_field(spans, "SCALE :")
    d = parse_scale_field(val)
    if d is not None:
        return d, f"title-block SCALE field {val!r}"
    return None, ("no SCALE field in the title block (page-wide '1:NN' strings are view captions "
                  "and are NOT accepted as the sheet scale)")


def read_bands(pdf, page_no):
    """Return (bands_pt, steps_pt, scale, denom, modal, tb_denom, gate_checks, notes).

    THE PAGE-TYPE GATE LIVES HERE and it is the reason nothing downstream can fail open. Round 1
    emitted build_floor-ready "floor plans" for 7 cabinet-joinery sheets of this same PDF. Every
    check below is EVALUATED AND REPORTED, and a single failure raises RefuseSheet with the whole
    report — so a refusal says which evidence was missing, not merely 'no'."""
    import fitz
    doc = fitz.open(pdf)
    if page_no >= len(doc):
        raise RefuseSheet(f"page {page_no} out of range (doc has {len(doc)})")
    page = doc[page_no]
    m = page.rotation_matrix
    drawings = page.get_drawings()

    # The sheet border: the page's LARGEST w=1.44 rect. Already scanned for G0; now also MEASURED,
    # because its size is what says whether this page is the A3 the title block's scale refers to or
    # a 0.7071x A4 export of it (see sheet_shrink).
    border_wh = None
    for d in drawings:
        if round(d.get("width") or 0, 2) != BORDER_PEN_PT:
            continue
        r = d.get("rect")
        if r is None:
            continue
        wh = (abs(r.x1 - r.x0), abs(r.y1 - r.y0))
        if border_wh is None or wh[0] * wh[1] > border_wh[0] * border_wh[1]:
            border_wh = wh
    have_border = border_wh is not None
    candidates = []          # (rect_pt, thin_pt) for every wall-PEN quad, pre-thickness screen
    for d in drawings:
        items = d.get("items") or []
        if not is_wall_band(d.get("type"), d.get("color"), d.get("width") or 0,
                            len(items), items[0][0] if items else None):
            continue
        q = items[0][1]
        pts = [fitz.Point(p) * m for p in (q.ul, q.ur, q.lr, q.ll)]
        for i in range(4):                                    # criterion 6
            a, b = pts[i], pts[(i + 1) % 4]
            if min(abs(a.x - b.x), abs(a.y - b.y)) > AXIS_TOL_PT:
                raise RefuseSheet(
                    f"wall quad is not axis-aligned (edge skew "
                    f"{min(abs(a.x - b.x), abs(a.y - b.y)):.3f} pt > {AXIS_TOL_PT}); "
                    f"rotated walls are not supported by this reader")
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        r = (min(xs), min(ys), max(xs), max(ys))
        candidates.append((r, min(r[2] - r[0], r[3] - r[1])))

    spans = page_spans(page)
    page_text = page.get_text()
    drawing_title = titleblock_field(spans, "DRAWING TITLE")
    tb, tb_why = titleblock_scale_denom(spans, page_text)

    ok_t, why_t = title_is_floor_plan(drawing_title, page_text)
    ok_x, why_x = extent_is_a_storey(drawing_title, ok_t)
    checks = [
        {"id": "G0", "name": "Bluehouse vector CAD sheet (wall pen + sheet border present)",
         "ok": bool(candidates) and have_border,
         "detail": f"{len(candidates)} black w={WALL_PEN_PT} lone-quad path(s); "
                   f"w={BORDER_PEN_PT} sheet border "
                   + (f"{border_wh[0]:.1f}x{border_wh[1]:.1f} pt" if have_border else "MISSING")},
        {"id": "T1", "name": "title block names a PLAN", "ok": ok_t, "detail": why_t},
        {"id": "T3", "name": "the plan is of a STOREY, not of one room", "ok": ok_x,
         "detail": why_x},
        {"id": "T2", "name": "the title block STATES a plan scale",
         "ok": tb in PLAN_DENOMS,
         "detail": (f"1:{tb} from the {tb_why}" if tb else tb_why)
                   + f"  (plan scales {list(PLAN_DENOMS)})"},
    ]

    # --- THE PAPER. Which sheet size is the title block's scale actually stated FOR? (sheet_shrink)
    shrink = None
    try:
        shrink, shrink_why = sheet_shrink(border_wh)
        checks.append({"id": "P1", "name": "the page is a known paper step off the A3 design sheet",
                       "ok": True, "detail": shrink_why})
    except RefuseSheet as e:
        checks.append({"id": "P1", "name": "the page is a known paper step off the A3 design sheet",
                       "ok": False, "detail": str(e)})

    # --- SCALE. Title block wins; geometry is a VETO. A disagreement REFUSES; it does not note.
    scale = denom = modal = None
    try:
        scale, denom, modal, snote = resolve_scale([t for _, t in candidates], tb, shrink or 1.0)
        checks.append({"id": "S1", "name": "scale is stated AND not contradicted by the geometry",
                       "ok": shrink is not None, "detail": snote if shrink is not None else
                       "not evaluated: the page's paper size is unresolved (see P1)"})
    except RefuseSheet as e:
        checks.append({"id": "S1", "name": "scale is stated AND not contradicted by the geometry",
                       "ok": False, "detail": str(e)})
    if shrink is None:
        scale = denom = modal = None      # never build on a scale whose paper is unknown

    bands_pt, steps_pt, off = [], [], []
    if scale is not None:
        bands_pt = [r for r, thin in candidates if thickness_ok(thin, scale)]
        bands_mm_for_step = to_mm_bands(bands_pt, scale, 0.0, 0.0)
        for r, thin in candidates:
            if thickness_ok(thin, scale):
                continue
            mm = thin * scale
            rect_mm = to_mm_bands([r], scale, 0.0, 0.0)[0]
            if STEP_MM_LO <= mm <= STEP_MM_HI and is_wall_step(rect_mm, bands_mm_for_step):
                steps_pt.append(r)
            else:
                off.append((r, round(mm, 1)))
        checks += envelope_checks(to_mm_bands(bands_pt, scale, 0.0, 0.0))
    else:
        checks.append({"id": "E*", "name": "envelope sanity",
                       "ok": False, "detail": "not evaluated: no trustworthy scale"})

    failed = [c for c in checks if not c["ok"]]
    if failed:
        report = "\n".join(f"    [{'ok ' if c['ok'] else 'FAIL'}] {c['id']} {c['name']}: "
                           f"{c['detail']}" for c in checks)
        raise RefuseSheet(
            f"page {page_no} is NOT a floor plan (or is not calibratable). "
            f"{len(failed)} of {len(checks)} gate checks failed:\n{report}\n"
            f"  Emission requires POSITIVE evidence on every check. Nothing was written.")

    notes = [f"PAGE GATE: {len(checks)}/{len(checks)} checks passed "
             f"(title {drawing_title!r}; {[c['id'] for c in checks]}).",
             next(c["detail"] for c in checks if c["id"] == "S1")]
    notes.append(f"wall-pen lone quads: {len(candidates)} = {len(bands_pt)} wall bands "
                 f"({WALL_MM_LO:.0f}-{WALL_MM_HI:.0f} mm) + {len(steps_pt)} wall_step "
                 f"({STEP_MM_LO:.0f}-{STEP_MM_HI:.0f} mm, adjacent to a real band) + "
                 f"{len(off)} unexplained {[m for _, m in off]} mm. "
                 f"Round 1 dropped the wall_step class SILENTLY; it is now emitted and counted.")
    if off:
        notes.append(f"REVIEW: {len(off)} wall-pen quad(s) fit NO class and were dropped: "
                     f"{[m for _, m in off]} mm thick. They are real ink. Inspect before trusting.")
    if not bands_pt:
        raise RefuseSheet("no wall-pen quad survived the 100 mm thickness screen")
    return bands_pt, steps_pt, scale, denom, modal, tb, checks, notes


def read_pen_paths(pdf, page_no, pen_pt=None):
    """Pure-black stroked paths as {"rect_pt", "n_items", "op", "w"}.
    pen_pt=None -> the BOUNDARY-INK class: every black stroke EXCEPT the wall pen (the pen
    table varies per office -- the 0.42 lesson -- so width is carried, not matched).
    pen_pt=<pt> -> exactly that pen (the LEAF pen, typing only).
    No geometric screening here — the geometric sub-classifier is pure and lives above."""
    import fitz
    doc = fitz.open(pdf)
    page = doc[page_no]
    m = page.rotation_matrix
    out = []
    for d in page.get_drawings():
        c = d.get("color")
        w = round(d.get("width") or 0, 2)
        if pen_pt is None:
            if not is_boundary_ink(d.get("type"), c, w):
                continue
        else:
            if d.get("type") != "s" or c is None or sum(c) > MAX_COLOR_SUM:
                continue
            if w != round(pen_pt, 2):
                continue
        r = d["rect"] * m
        items = d.get("items") or []
        out.append({"rect_pt": (min(r.x0, r.x1), min(r.y0, r.y1), max(r.x0, r.x1), max(r.y0, r.y1)),
                    "n_items": len(items), "op": items[0][0] if items else None, "w": w})
    return out


def to_mm_rect(r_pt, scale, x0, y0):
    ax, ay = map_pt(r_pt[0], r_pt[3], scale, x0, y0)
    bx, by = map_pt(r_pt[2], r_pt[1], scale, x0, y0)
    return (round(min(ax, bx), 1), round(min(ay, by), 1),
            round(max(ax, bx), 1), round(max(ay, by), 1))


def to_mm_bands(bands_pt, scale, x0, y0):
    """Paper-pt rects -> mm rects (x0,y0,x1,y1), x east / y NORTH (map_pt flips y)."""
    out = []
    for (px0, py0, px1, py1) in bands_pt:
        ax, ay = map_pt(px0, py1, scale, x0, y0)      # paper bottom -> mm south
        bx, by = map_pt(px1, py0, scale, x0, y0)      # paper top    -> mm north
        out.append(_round_rect((min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))))
    return sorted(out)


def build(pdf, page_no, scale_override=None, seed=None, zone_name=None,
          min_gap=DEFAULT_MIN_GAP_MM, signed_voids=(), signed_by=None, virtual_edges=(),
          owner_edges=(), owner_ledger=None, owner_signature=None):
    bands_pt, steps_pt, scale, denom, modal, tb, gate_checks, notes = read_bands(pdf, page_no)
    if scale_override:
        raise RefuseSheet(
            "--scale is GONE. It existed to overrule a scale the reader had guessed from an "
            "assumed wall thickness; the scale now comes from the title block and a geometry "
            "disagreement REFUSES the sheet. A hand-typed mm/pt would re-open exactly the "
            "fail-open path this round closed.")

    # ORIGIN: derived from the walls themselves, not fitted to a dimension string. The building's
    # SOUTH-WEST OUTER corner. It must be the SW (not NW) corner because map_pt emits y NORTH:
    # feeding it the NW corner puts the whole building at negative y.
    x0 = min(r[0] for r in bands_pt)
    y0 = max(r[3] for r in bands_pt)

    bands = to_mm_bands(bands_pt, scale, x0, y0)
    steps = to_mm_bands(steps_pt, scale, x0, y0)
    segments = [[[round(a[0], 1), round(a[1], 1)], [round(b[0], 1), round(b[1], 1)]]
                for r in bands for a, b in band_long_edges(*r)]
    seg_class = ["wall_poche"] * len(segments)
    # WALL STEPS: real wall-pen ink, 40 mm thick, touching a real band (the west-wall jamb notch).
    # Emitted as their own class, and SOLID for the flood, but deliberately NOT fed to merge_runs:
    # a 40 mm quad would open its own 40 mm-thick "run" and invent gaps that are not openings.
    step_segments = [[[round(a[0], 1), round(a[1], 1)], [round(b[0], 1), round(b[1], 1)]]
                     for r in steps for a, b in band_long_edges(*r)]
    segments += step_segments
    seg_class += ["wall_step"] * len(step_segments)

    runs = merge_runs(bands)

    # ---------------------------------------------------------------- PART C: boundary ink
    env = (min(b[0] for b in bands) - ENV_MARGIN_MM, min(b[1] for b in bands) - ENV_MARGIN_MM,
           max(b[2] for b in bands) + ENV_MARGIN_MM, max(b[3] for b in bands) + ENV_MARGIN_MM)
    panels = [{"rect": to_mm_rect(p["rect_pt"], scale, x0, y0),
               "n_items": p["n_items"], "op": p["op"], "w": p["w"]}
              for p in read_pen_paths(pdf, page_no)]
    leaf_rects = [to_mm_rect(p["rect_pt"], scale, x0, y0)
                  for p in read_pen_paths(pdf, page_no, LEAF_PEN_PT)]
    boundary, rejected = classify_panels(panels, runs, env)
    pen_hist = collections.Counter(p["w"] for p in boundary)
    n_comp = sum(1 for p in boundary if p.get("via_composite"))
    notes.append(f"boundary ink: {len(panels)} black non-wall-pen paths -> {len(boundary)} "
                 f"band-aligned enclosure paths, pens {dict(sorted(pen_hist.items()))}"
                 + (f", {n_comp} aligned to a composite double-leaf wall" if n_comp else "")
                 + f" ({len(rejected)} rejected: ticks / sheet frame / perpendicular door "
                 f"leaves); {len(leaf_rects)} {LEAF_PEN_PT}-pt leaf paths.")

    infill, opening_gaps, voids = resolve_gaps(all_gaps(runs), boundary)
    # VOIDS get stable ids. An owner may SIGN one -- "yes, the wall continues behind the stair,
    # the sheet just doesn't draw it" -- and only then does it become solid. The COORDINATES are
    # still 100% ink (the run's faces, the gap's ends); the only human input is the DECISION.
    # Unsigned, a void stays a hole and the flood escapes through it. That is the point.
    for i, g in enumerate(sorted(voids, key=lambda g: (g["axis"], g["face_lo"], g["gap_lo"]))):
        g["id"] = f"V{i:02d}"
    signed_voids = set(signed_voids or ())
    if (signed_voids or virtual_edges or owner_edges) and not signed_by:
        raise RefuseSheet("--sign-void / --virtual-edge need --signed-by: an unsigned virtual wall "
                          "is a fabricated wall. (Two-layer law: geometry is machine-solved, "
                          "semantics owner-only.)")
    if owner_signature is not None:
        raise RefuseSheet(OWNER_SIG_DEAD)
    if owner_edges and not owner_ledger:
        raise RefuseSheet("--owner-edge needs --owner-ledger: an OWNER-SIGNED edge with no OWNER "
                          "LEDGER is just an agent-provisional edge wearing a hat. Use "
                          "--virtual-edge for agent-provisional edges.\n" + OWNER_SIG_DEAD)
    # D1 (round 6): the ledger the reader will TRUST must be one the agent's tools CANNOT WRITE.
    # guard_paths/guard_bash protect writes to the basename `zoning-signoff.json` only; a reader that
    # consumed --owner-ledger <any-path> let the agent write my-ledger.json and point here (the
    # forge-lens hole). Bind consumption to the protected basename so the two ends agree: the only
    # ledger this reads is the one the hooks defend. A different-named file cannot become a signature.
    if owner_ledger and os.path.basename(owner_ledger) != ZSG.LEDGER_BASENAME:
        raise RefuseSheet(
            "--owner-ledger must be named %r (got %r). The owner sign-off ledger is the ONE file the "
            "agent's tools are forbidden to write (guard_paths/guard_bash defend that basename). A "
            "ledger under any other name is a file the agent CAN write -- i.e. a forgeable signature. "
            "Consumption is bound to the protected basename on purpose."
            % (ZSG.LEDGER_BASENAME, os.path.basename(owner_ledger)))
    bad = signed_voids - {g["id"] for g in voids}
    if bad:
        raise RefuseSheet(f"--sign-void {sorted(bad)}: no such void on this sheet "
                          f"(voids found: {sorted(g['id'] for g in voids) or 'none'})")
    virtual = [dict(g, provenance="agent-provisional") for g in voids if g["id"] in signed_voids]
    voids = [g for g in voids if g["id"] not in signed_voids]
    # TWO KINDS OF VIRTUAL EDGE, and they must never be confused (round 3). The owner adjudicated
    # ONE line on this sheet (the living<->dining zoning line); the other three are the agent's own
    # provisional calls. A room-spec that flattened both into "signed_virtual" would let an agent
    # guess ride on an owner signature.
    #
    # D1 (round 5): AN EDGE IS OWNER-SIGNED IFF ITS CANONICAL KEY IS IN THE OWNER'S LEDGER.
    # The agent cannot type its way to a signature: there is nothing to type. The key is derived
    # from the SNAPPED ink geometry and the SHEET, and it must already be in a file the agent's
    # tools cannot write. sign_status (what counts as a signature at all) is ffe_signoff_gate's.
    sheet = ZSG.sheet_id(pdf, page_no)
    led_entries, led_sha, led_err = ZSG.load_ledger(owner_ledger)
    if owner_edges and led_err:
        raise RefuseSheet(
            "--owner-edge was passed but the OWNER LEDGER is unusable: %s. An unreadable ledger "
            "signs NOTHING (fail-safe). No edge may be written as owner-signed." % led_err)

    owner_ves, bound = [], []
    for i, spec in enumerate(owner_edges or ()):
        ve = parse_virtual_edge(spec, bands)          # ink-face validation + SNAP, as ever
        key = ZSG.canonical_key(sheet, ve)
        entry = ZSG.resolve_edge(key, led_entries)
        if entry is None:
            raise RefuseSheet(
                "NOT IN THE OWNER'S LEDGER: --owner-edge %s.\n"
                "    canonical key : %s\n"
                "    ledger        : %s  (%d entr%s)\n"
                "    keys signed   : %s\n"
                "  This edge is being written as OWNER-SIGNED, but the OWNER never signed it. In "
                "round 4 the caller could simply COMPOSE a signature naming this edge and the "
                "bijection would pass -- because the AGENT authored both sides of it. The signature "
                "now lives in a ledger the OWNER writes and this reader only READS.\n"
                "  If this line is real, the OWNER (not the agent) adds the canonical key above to "
                "%s. If it is the reader's own closure crutch, pass it as --virtual-edge: it stays "
                "AGENT-PROVISIONAL and the room is stamped adopted=false. That is the honest answer, "
                "and it is not a bug."
                % (spec, key, owner_ledger, len(led_entries),
                   "y" if len(led_entries) == 1 else "ies",
                   sorted(ZSG.entry_key(e) for e in led_entries
                          if ZSG.sign_status(e) == "valid") or "NONE",
                   owner_ledger))
        ve["id"] = f"OE{i:02d}"
        ve["spec"] = spec
        ve["provenance"] = "owner-signed"
        ve["owner_key"] = key
        ve["owner_entry"] = {k: entry.get(k) for k in ("by", "date", "zone", "note")}
        owner_ves.append(ve)
        bound.append({"id": ve["id"], "spec": spec, "key": key, "length_mm": ve["length_mm"],
                      "by": entry.get("by"), "date": entry.get("date"), "zone": entry.get("zone"),
                      "note": entry.get("note")})
    sig = (ZSG.signoff_block(owner_ledger, led_sha, led_entries, bound, sheet)
           if owner_ledger and not led_err else None)
    if sig and sig["orphans_present"]:
        notes.append("REVIEW: the owner's ledger signs %d line(s) on this sheet that this run did "
                     "NOT write: %s. A signature that binds nothing is never silently dropped."
                     % (len(sig["orphan_entries"]),
                        [o["key"] for o in sig["orphan_entries"]]))
    if sig and sig["malformed_present"]:
        notes.append("REVIEW: the owner's ledger has %d MALFORMED entr(y/ies) (a real signer, no "
                     "key/date anchor): %s. A broken signature must not look like an absent one."
                     % (len(sig["malformed_entries"]), sig["malformed_entries"]))
    for ve in owner_ves:
        virtual.append(ve)
    for i, spec in enumerate(virtual_edges or ()):
        ve = parse_virtual_edge(spec, bands)
        ve["id"] = f"E{i:02d}"
        ve["spec"] = spec
        ve["provenance"] = "agent-provisional"
        ve["owner_key"] = None
        ve["owner_entry"] = None
        virtual.append(ve)
    snapped = [v for v in virtual if v.get("snapped")]
    if snapped:
        notes.append("REVIEW: %d signed virtual edge(s) did NOT sit on ink and were SNAPPED onto "
                     "the faces they validated against: %s. The typed coordinate was not used."
                     % (len(snapped), "; ".join("%s %s -> %s" % (v["id"], v["spec"],
                                                                 v["snap_deltas_mm"])
                                                for v in snapped)))
    virtual_segments = []
    for g in virtual:
        for s in gap_segments(g):
            virtual_segments.append([[round(s[0][0], 1), round(s[0][1], 1)],
                                     [round(s[1][0], 1), round(s[1][1], 1)]])
    # INFILL: undrawn stubs, bridged as real wall AND logged, every one, with its size.
    infill_segments = []
    for g in infill:
        for s in gap_segments(g):
            infill_segments.append([[round(s[0][0], 1), round(s[0][1], 1)],
                                    [round(s[1][0], 1), round(s[1][1], 1)]])
    segments += infill_segments
    seg_class += ["closure_infill"] * len(infill_segments)
    segments += virtual_segments
    seg_class += ["signed_virtual"] * len(virtual_segments)
    closure_log = [{"axis": g["axis"], "rect": [round(v, 1) for v in gap_rect(g)],
                    "length_mm": g["length_mm"], "ink_coverage": g["ink_coverage"],
                    **({"crossing_ink_refused": True,
                        "crossing_ink_pens": g["crossing_ink_pens"]}
                       if g.get("crossing_ink_refused") else {}),
                    "action": ("BRIDGED as wall (below the declared %.0f mm closure tolerance; "
                               "its only ink CROSSES the stub without terminating at the jambs "
                               "-- refused as backing, pens/mm: %s)"
                               % (CLOSE_TOL_MM, g["crossing_ink_pens"]))
                              if g.get("crossing_ink_refused") else
                              ("BRIDGED as wall (below the declared %.0f mm closure tolerance, "
                               "and carrying no jamb-terminated ink of any class)" % CLOSE_TOL_MM)}
                   for g in sorted(infill, key=lambda g: -g["length_mm"])]

    gaps = find_gaps(runs, min_gap)
    glazing = []
    for i, g in enumerate(gaps):
        for s in gap_segments(g):
            glazing.append({"seg": [[round(s[0][0], 1), round(s[0][1], 1)],
                                    [round(s[1][0], 1), round(s[1][1], 1)]],
                            "gap_id": f"G{i:02d}", "length_mm": g["length_mm"],
                            "axis": g["axis"]})

    # ---- CLOSURE: flood the free floor from the owner seed; the boundary of what it reaches
    # IS the room. Openings and infills are SOLID for the flood (a door still bounds a room);
    # voids are not, so a room that only "closes" over an undrawn 3 m hole cannot pass.
    room = None
    openings_out = []
    if seed is not None:
        solid = [list(b) for b in bands] + [list(s) for s in steps] \
            + [gap_rect(g) for g in infill] \
            + [gap_rect(g) for g in opening_gaps] + [gap_rect(g) for g in virtual]
        room = derive_room_polygon(bands, solid, seed)
        filled, forigin = room.pop("_filled"), room.pop("_origin")
        openings_out = type_openings(opening_gaps, filled, forigin, leaf_rects)
        if room.get("outline_mm"):
            # AN OPENING BACKS ONLY THE MILLIMETRES IT INKS (round 3, FATAL 2). Not gap_rect(g)
            # -- that credited a 0.616-coverage window as 100% wall.
            backing = [(list(b), "wall_poche") for b in bands] \
                + [(list(s), "wall_poche") for s in steps] \
                + [(r, "opening") for g in opening_gaps for r in gap_ink_rects(g, boundary)] \
                + [(gap_rect(g), "closure_infill") for g in infill] \
                + [(gap_rect(g), "signed_virtual") for g in virtual]
            sides = audit_sides([tuple(p) for p in room["outline_mm"]], backing)
            room["sides"] = sides
            room["perimeter_mm"] = round(sum(s["length_mm"] for s in sides), 1)
            room["unbacked_perimeter_mm"] = round(sum(s["unbacked_mm"] for s in sides), 1)
            room["virtual_perimeter_mm"] = round(
                sum(s["backing"].get("signed_virtual", 0.0) for s in sides), 1)
            # D4 (latent): closure_infill was credited as BACKED at full gap length and counted in
            # NEITHER gate number -- so a bridged, undrawn stub was invisible to ink_backed and to
            # the write gate. It is 0.0 mm on this sheet, so it was not lying YET. It is now its
            # own line, it is in ink_backed, and it is in the write gate.
            room["infill_perimeter_mm"] = round(
                sum(s["backing"].get("closure_infill", 0.0) for s in sides), 1)
            P = max(room["perimeter_mm"], 1e-6)
            room["virtual_fraction"] = round(room["virtual_perimeter_mm"] / P, 4)
            room["unbacked_fraction"] = round(room["unbacked_perimeter_mm"] / P, 4)
            room["infill_fraction"] = round(room["infill_perimeter_mm"] / P, 4)
            room["ink_backed"] = (room["unbacked_perimeter_mm"] < MAX_UNSIGNED_UNBACKED_MM
                                  and room["virtual_perimeter_mm"] < MAX_UNSIGNED_VIRTUAL_MM
                                  and room["infill_perimeter_mm"] < MAX_UNSIGNED_INFILL_MM)
            room["unbacked_note"] = (
                "unbacked = polygon perimeter backed by NO ink of any class. An OPENING credits "
                "only the span its panel ink actually draws (its ink_coverage), so a partially "
                "drawn window leaves real blank paper here. Round 2 reported 0.2 mm because it "
                "credited every opening's FULL length.")
        room["zone"] = zone_name or "unnamed"
        room["signed_virtual_walls"] = [
            {"id": g["id"], "rect": [round(v, 1) for v in gap_rect(g)],
             "length_mm": g["length_mm"], "signed_by": signed_by,
             "provenance": g.get("provenance", "agent-provisional"),
             "owner_key": g.get("owner_key"),
             "owner_entry": g.get("owner_entry"),
             "spec": g.get("spec"),
             "snap_deltas_mm": g.get("snap_deltas_mm"),
             "snap_note": g.get("snap_note"),
             "action": ("NOT INK. THE OWNER signed this as a wall/zoning line the sheet does not "
                        "draw." if g.get("provenance") == "owner-signed" else
                        "NOT INK, and NOT owner-signed: an AGENT-PROVISIONAL edge. It closes the "
                        "flood so the room can be measured; it is not a wall until an owner says "
                        "so.")}
            for g in virtual]
        # ROUND 5: the always-true audit field is GONE. `bijection_verified: True` was in EVERY
        # artefact on disk (a failed bijection refused the write), so it audited nothing and made a
        # FORGED room look MORE audited than an unbound one. What is stamped now VARIES with the
        # run: the ledger's sha256, the entries that actually bound, and orphans_present /
        # malformed_present -- both of which CAN be true in a written artefact.
        room["owner_signoff"] = sig
        room["virtual_owner_signed_mm"] = round(
            sum(g["length_mm"] for g in virtual if g.get("provenance") == "owner-signed"), 1)
        room["virtual_agent_provisional_mm"] = round(
            sum(g["length_mm"] for g in virtual if g.get("provenance") != "owner-signed"), 1)
        room["closure_infills"] = closure_log
        room["unbacked_voids"] = [
            {"id": g["id"], "axis": g["axis"], "rect": [round(v, 1) for v in gap_rect(g)],
             "length_mm": g["length_mm"], "ink_coverage": g["ink_coverage"],
             "action": "LEFT OPEN — longer than the %.0f mm closure tolerance and backed by NO "
                       "ink. Not a wall, not an opening. If this side of the room needed to "
                       "close, it did not." % CLOSE_TOL_MM}
            for g in sorted(voids, key=lambda g: -g["length_mm"])]
    else:
        openings_out = type_openings(opening_gaps, set(), (0.0, 0.0), leaf_rects)

    xs = [c for s in segments for c in (s[0][0], s[1][0])]
    ys = [c for s in segments for c in (s[0][1], s[1][1])]
    bbox = [[round(min(xs), 1), round(min(ys), 1)], [round(max(xs), 1), round(max(ys), 1)]]
    run_mm = sum(max(r[2] - r[0], r[3] - r[1]) for r in bands)

    meta = {
        "schema": SCHEMA,
        "source_pdf": os.path.basename(pdf),
        "page": page_no,
        "scale_mm_per_pt": round(scale, 5),
        "origin_pt": [round(x0, 2), round(y0, 2)],
        "frame": "mm; x east, y north from the building SW outer corner (derived from the wall bbox)",
        "n": len(segments),
        "segments": segments,
        # build_floor reads `segments` (topology-free slabs) and knows nothing of classes; this
        # parallel array keeps the two INK CLASSES distinguishable for any consumer that cares
        # (glass wants a different material than plaster).
        "segment_classes": seg_class,
        "provenance": {
            "reader": "bluehouse_plan_reader.py",
            "predicate": ("stroke-only AND sum(color)<=%.2f AND width==%.2f pt AND a LONE 'qu' item "
                          "AND %.0f<=thin_dim*scale<=%.0f mm AND axis-aligned"
                          % (MAX_COLOR_SUM, WALL_PEN_PT, WALL_MM_LO, WALL_MM_HI)),
            "emission": "the TWO LONG EDGES of each band (end-caps dropped); build_floor extrudes "
                        "each segment as an independent slab, so a 100 mm wall must be two faces",
            "scale_source": ("the TITLE BLOCK states 1:%s; the modal wall-pen thin-dim %.2f pt "
                             "= %.1f mm at that scale, which the geometry VETO accepted"
                             % (denom, modal, modal * scale)),
            "titleblock_denom": tb,
            "page_gate": gate_checks,
            "n_bands": len(bands),
            "n_wall_steps": len(steps),
            "n_segments": len(segments),
            "n_runs": sum(len(v) for v in runs.values()),
            "total_wall_run_mm": round(run_mm, 1),
            "bbox_mm": bbox,
            "notes": notes,
        },
        "honesty": {
            "the_gate_is_what_makes_this_safe": (
                "Round 1 emitted build_floor-ready 'floor plans' for 7 CABINET-JOINERY sheets of "
                "this same PDF and its title-block cross-check rubber-stamped them. Emission now "
                "requires positive evidence on every check in provenance.page_gate. The three "
                "signals are NOT equally strong: T1 (the title-block DRAWING TITLE) and T2/S1 "
                "(the stated plan scale, with the geometry as a VETO) do the real work. E1-E3 "
                "(envelope sanity) are a coarse floor only -- E3's side-ink test passes the real "
                "plan page with just 0.09 against a 0.05 threshold, because this sheet's poche is "
                "a chain of stubs, while a joinery sheet reaches 0.93 on one side. Do not read E3 "
                "as evidence of a building."),
            "bbox_is_not_a_metric": (
                "provenance.bbox_mm matches the sheet's printed overall dimension strings to the "
                "millimetre. It did so in round 1 too, when the emitted geometry was a dozen "
                "freestanding 100 mm fins on a slab. It is the hull of a sparse point cloud and it "
                "cannot fail. The metric that can fail is room_closure.sides (the per-side ink "
                "audit) plus unbacked_perimeter_mm / virtual_perimeter_mm / ink_backed."),
            "wall_ink_does_not_close_the_rooms": (
                "This convention stops the wall pen at every door and window; the glazing/door "
                "leaves are drawn on a separate thin pen that this predicate deliberately excludes. "
                "`segments` is therefore an OPEN outline with real holes in it. See "
                "glazing_candidates / openings. Wall-recall metrics pass anyway; do not read a "
                "high recall as a buildable room."),
            "openings_are_unsigned": (
                "glazing_candidates are machine-INERT: manual_additions.by is OWNER-CONFIRM-PENDING, "
                "and merge_carried refuses to inject an unsigned record into `segments`. Whether an "
                "opening is a window, a door or solid infill is a SEMANTIC call and is owner-only."),
            "no_topology": (
                "Bands are merged into collinear RUNS (enough to find openings) but corners are not "
                "resolved. `room_closure` (part C) DOES produce a closed polygon, by flooding the "
                "free floor from an OWNER-SUPPLIED seed — it is not a corner-resolution graph."),
            "types_are_unsigned": (
                "Every emitted opening carries signed=false. Window vs sliding vs door is decided by "
                "a declared MECHANICAL rule (which sides of the wall are floor; whether the leaf pen "
                "draws sliding leaves inside the hole), not by a measurement. Sill/head heights are "
                "NOT on this sheet; floor_openings' defaults are disclosed render defaults."),
            "closure_is_logged_not_assumed": (
                "Gaps shorter than the DECLARED %.0f mm closure tolerance AND carrying no ink are "
                "bridged as wall; every one is listed in room_closure.closure_infills with its size. "
                "Anything longer is either an opening (backed by ink) or an unbacked VOID, which is "
                "left open and listed in room_closure.unbacked_voids. A tolerance that swallowed a "
                "metre-scale hole would be a lie; this one cannot." % CLOSE_TOL_MM),
        },
    }
    if room is not None:
        meta["room_closure"] = room
    if openings_out:
        meta["openings_typed"] = openings_out

    if seed is not None:
        oc = outline_from_seed(bands, seed)
        oc["zone"] = zone_name or "unnamed"
        oc["derivation"] = "4 axis rays from an OWNER-SUPPLIED seed to the nearest wall face"
        if oc["open_sides"]:
            oc["status"] = "OPEN — NOT A ROOM"
            oc["warning"] = (
                "Side(s) %s have no wall ink across them, so this zone does NOT close on walls "
                "alone. This reader will not invent a boundary. Resolve by signing the relevant "
                "glazing_candidates (an opening in a real wall) or by supplying the boundary as an "
                "owner semantic call (e.g. a zone edge that is a wall END, not a wall)."
                % ", ".join(oc["open_sides"]))
        else:
            oc["status"] = "CLOSED on wall ink"
        meta["outline_candidate"] = oc

    if glazing:
        meta["glazing_candidates"] = glazing
        meta["openings"] = gaps
        meta["manual_additions"] = {
            "by": "OWNER-CONFIRM-PENDING",
            "reason": ("%d opening(s) detected as gaps between collinear wall runs. Each is a "
                       "window, a door or solid infill — a SEMANTIC call this reader must not make. "
                       "Keep only the segments that are SOLID, then sign `by` to activate them."
                       % len(gaps)),
            "segments": [g["seg"] for g in glazing],
        }
    return meta, notes


def owner_key_lines(pdf, page_no, specs):
    """(sheet_id, [(spec, canonical_key, length_mm)]) for --ledger-keys. It parses and SNAPS each
    spec exactly as build() will, so the key printed here is byte-identical to the key the gate
    will look up. This function WRITES NOTHING: producing a key is not producing a signature."""
    bands_pt, _steps_pt, scale, *_rest = read_bands(pdf, page_no)
    x0 = min(r[0] for r in bands_pt)
    y0 = max(r[3] for r in bands_pt)
    bands = to_mm_bands(bands_pt, scale, x0, y0)
    sheet = ZSG.sheet_id(pdf, page_no)
    rows = []
    for spec in specs or ():
        ve = parse_virtual_edge(spec, bands)
        rows.append((spec, ZSG.canonical_key(sheet, ve), ve["length_mm"]))
    return sheet, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bluehouse plan wall reader -> wall-segments-mm@0.1")
    ap.add_argument("pdf")
    ap.add_argument("page", type=int, help="0-indexed page")
    ap.add_argument("out", help="output json (put it under _private/ — client-derived)")
    ap.add_argument("--seed", default=None, metavar="X,Y",
                    help="mm point inside a zone; emits a ray-cast outline_candidate for it")
    ap.add_argument("--zone-name", default=None)
    ap.add_argument("--min-gap", type=float, default=DEFAULT_MIN_GAP_MM)
    ap.add_argument("--room-out", default=None,
                    help="also write a room-spec@0.2 with the CLOSED outline (needs --seed "
                         "and --ceiling-mm)")
    ap.add_argument("--openings-out", default=None,
                    help="also write the openings json floor_openings.py/build_floor consume")
    ap.add_argument("--ceiling-mm", type=float, default=None,
                    help="REQUIRED for --room-out. A ceiling height is NOT on a plan sheet: this "
                         "is an OWNER/render input and is recorded as such in the spec.")
    ap.add_argument("--sign-void", action="append", default=[], metavar="Vnn",
                    help="OWNER call: treat this unbacked void as a wall the sheet fails to draw. "
                         "Its coordinates still come from the ink (the run's faces, the gap's "
                         "ends); only the DECISION is human. Needs --signed-by.")
    ap.add_argument("--signed-by", default=None, help="who signed the --sign-void calls")
    ap.add_argument("--virtual-edge", action="append", default=[],
                    metavar="AXIS:FACE_LO:FACE_HI:LO:HI",
                    help="AGENT-PROVISIONAL edge: a wall the sheet does NOT draw, that the agent "
                         "needs in order to close a flood. Every one of the 4 numbers must be a "
                         "real ink face (and is SNAPPED onto it) or it is refused. It is counted "
                         "as VIRTUAL, not ink, in the side audit. Needs --signed-by.")
    ap.add_argument("--owner-edge", action="append", default=[],
                    metavar="AXIS:FACE_LO:FACE_HI:LO:HI",
                    help="OWNER-SIGNED edge (same geometry rules as --virtual-edge, different "
                         "PROVENANCE). Authorised IFF its canonical key is in --owner-ledger. "
                         "The owner signs LINES, not lists: everything passed via --virtual-edge "
                         "stays agent-provisional.")
    ap.add_argument("--owner-ledger", default=None, metavar="zoning-signoff.json",
                    help="The OWNER-AUTHORED sign-off ledger (zoning_signoff_gate.py; the same "
                         "pattern as ffe_signoff_gate.py's sourcing-signoff.json). The OWNER writes "
                         "it; this reader only READS it and matches canonical keys against it. The "
                         "agent's tools are blocked from writing it by the PreToolUse guard hooks.")
    ap.add_argument("--ledger-keys", action="store_true",
                    help="Print the CANONICAL KEY of each --owner-edge and exit, so the OWNER can "
                         "copy it into the ledger. Printing a key is NOT signing it.")
    ap.add_argument("--owner-signature", default=None, metavar="DEAD",
                    help="REMOVED (round 5). " + OWNER_SIG_DEAD.splitlines()[0])
    ap.add_argument("--write-provisional", action="store_true",
                    help="NOT A SIGNATURE. Write the room-spec even though part of its perimeter "
                         "is covered by no signature (agent-provisional edges / blank paper / "
                         "bridged stubs). The spec is stamped adopted=false, every unsigned edge "
                         "is named in it, and it must not be treated as owner-adopted geometry.")
    a = ap.parse_args(argv)
    if a.room_out and (a.seed is None or a.ceiling_mm is None):
        ap.error("--room-out needs --seed (a point in the zone) and --ceiling-mm (owner input; "
                 "the plan does not carry a ceiling height)")
    if a.owner_signature is not None:
        print("REFUSED: " + OWNER_SIG_DEAD, file=sys.stderr)
        return 2
    if a.ledger_keys:
        try:
            sheet, rows = owner_key_lines(a.pdf, a.page, a.owner_edge)
        except RefuseSheet as e:
            print(f"REFUSED (page {a.page}): {e}", file=sys.stderr)
            return 2
        print(f"# canonical keys for the OWNER's zoning sign-off ledger (sheet {sheet})")
        print("# The OWNER copies a key below into zoning-signoff.json with by/date. Printing a "
              "key is NOT signing it: this reader cannot write that file.")
        for spec, key, length in rows:
            print(f"  {spec:28s} {length:8.1f} mm   key: {key}")
        if not rows:
            print("  (pass --owner-edge to see its key)")
        return 0

    seed = tuple(float(v) for v in a.seed.split(",")) if a.seed else None
    try:
        meta, notes = build(a.pdf, a.page, None, seed, a.zone_name, a.min_gap,
                            a.sign_void, a.signed_by, a.virtual_edge,
                            a.owner_edge, a.owner_ledger)
    except RefuseSheet as e:
        print(f"REFUSED (page {a.page}): {e}", file=sys.stderr)
        print("No output written. A wrong floor plan is worse than no floor plan.", file=sys.stderr)
        return 2

    prior = None
    if os.path.exists(a.out):
        try:
            prior = json.load(open(a.out, encoding="utf-8"))
        except (ValueError, OSError):
            prior = None
    meta, carry_notes = merge_carried(meta, prior)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, a.out)

    p = meta["provenance"]
    (bx0, by0), (bx1, by1) = p["bbox_mm"]
    print(f"wrote {a.out}")
    print("  PAGE GATE (all must pass; a single FAIL refuses the page and writes nothing):")
    for c in p["page_gate"]:
        print(f"    [{'ok ' if c['ok'] else 'FAIL'}] {c['id']} {c['name']}: {c['detail']}")
    print(f"  {p['n_bands']} wall bands + {p['n_wall_steps']} wall steps -> {meta['n']} segments")
    print(f"  scale {meta['scale_mm_per_pt']} mm/pt   origin_pt {meta['origin_pt']}   "
          f"total wall run {p['total_wall_run_mm']:.0f} mm")
    print(f"  bbox mm X[{bx0:.0f}..{bx1:.0f}] Y[{by0:.0f}..{by1:.0f}]  <- NOT a success metric: "
          f"this is the hull of a sparse stub cloud, and it matched the printed overalls even in "
          f"round 1, when the emitted 'walls' were a dozen freestanding fins.")
    for n in notes + carry_notes:
        print(f"  {n}")
    if meta.get("openings"):
        print(f"  {len(meta['openings'])} OPENING(S) — the wall ink does NOT close:")
        for g in meta["openings"]:
            print(f"    {g['axis']} face {g['face_lo']}..{g['face_hi']}  "
                  f"gap {g['gap_lo']}..{g['gap_hi']}  = {g['length_mm']:.0f} mm")
        print("  -> emitted as UNSIGNED glazing_candidates (machine-inert until an owner signs).")
    if meta.get("outline_candidate"):
        oc = meta["outline_candidate"]
        print(f"  outline_candidate [{oc['zone']}]: {oc['status']}")
        print(f"    W={oc['west']} E={oc['east']} S={oc['south']} N={oc['north']}"
              f"  inner={oc['inner_wh_mm']}")
        if oc["open_sides"]:
            print(f"    OPEN SIDES: {', '.join(oc['open_sides'])} — no wall ink there.")

    rc = meta.get("room_closure")
    if rc:
        print(f"\n  ROOM CLOSURE [{rc['zone']}]: closed={rc['closed']}  ({rc['why']})")
        if rc.get("outline_mm"):
            print(f"    polygon {rc['n_vertices']} vertices, {rc['area_m2']} m2, "
                  f"{len(rc.get('holes_mm') or [])} interior hole(s)")
        for c in rc["closure_infills"]:
            print(f"    INFILL  {c['length_mm']:7.1f} mm  rect {c['rect']}  (ink {c['ink_coverage']})")
        for v in rc["signed_virtual_walls"]:
            print(f"    VIRTUAL {v['id']:5s} {v['length_mm']:7.1f} mm  rect {v['rect']}  "
                  f"NOT INK — {v['provenance'].upper()}"
                  + (f"  LEDGER by={v['owner_entry']['by']!r} {v['owner_entry']['date']}"
                     if v.get("owner_entry") else "")
                  + ("  [SNAPPED onto ink]" if v.get("snap_deltas_mm")
                     and any(abs(d) > VIRTUAL_SNAP_TOL_MM
                             for d in v["snap_deltas_mm"].values()) else ""))
        for v in rc["unbacked_voids"]:
            print(f"    VOID    {v['id']} {v['length_mm']:7.1f} mm  rect {v['rect']}  LEFT OPEN")
        if rc.get("sides"):
            print(f"    SIDE AUDIT  unbacked {rc['unbacked_perimeter_mm']} mm | "
                  f"virtual {rc['virtual_perimeter_mm']} mm | 100%-ink={rc['ink_backed']}")
            for s in rc["sides"]:
                bits = " ".join(f"{k}={v:.0f}" for k, v in s["backing"].items())
                flag = "  <-- UNBACKED" if s["unbacked_mm"] > 1.0 else ""
                print(f"      {s['axis']} {str(s['edge']):34s} L={s['length_mm']:7.1f}  "
                      f"{bits}  unbacked={s['unbacked_mm']}{flag}")
    for o in meta.get("openings_typed", []):
        print(f"    OPENING {o['id']} {o['type']:8s} {o['length_mm']:7.1f} mm  rect {o['rect']}  "
              f"ink {o['ink_coverage']}  leaf {o['leaf_pen_paths']}  [{o['context']}]")

    if a.openings_out:
        oj = {"meta": {"schema": "interior-ai/openings@0.1",
                       "source": "bluehouse_plan_reader.py part C (boundary ink)",
                       "source_pdf": os.path.basename(a.pdf), "page": a.page,
                       "types_unsigned": "type is a declared mechanical rule, not a measurement; "
                                         "sill/head are floor_openings render defaults",
                       "frame": meta["frame"]},
              "openings": meta.get("openings_typed", [])}
        _write(a.openings_out, oj)
        print(f"  wrote {a.openings_out}  ({len(oj['openings'])} openings)")

    if a.room_out:
        if not rc or not rc.get("closed") or not rc.get("outline_mm"):
            print("  REFUSING to write --room-out: the boundary did not close. "
                  "A room-spec with an invented wall is worse than no room-spec.", file=sys.stderr)
            return 3

        # ---------------------------------------------------------------- THE INK GATE (round 3)
        # FATAL 4: the only write gate used to be `if not closed`. ink_backed,
        # unbacked_perimeter_mm and virtual_perimeter_mm were computed, emitted, and then NEVER
        # CONSULTED -- so three different signed north lines (y=3905 / 4970 / 6790) each produced
        # a "closed, auto-derived" room (17.50 / 22.40 / 29.56 m2) and all three were written,
        # with nothing in the file marking which millimetres were measured and which were signed.
        # A gate that is computed and not read is not a gate.
        vp = rc.get("virtual_perimeter_mm", 0.0)
        up = rc.get("unbacked_perimeter_mm", 0.0)
        ip = rc.get("infill_perimeter_mm", 0.0)
        vp_owner = rc.get("virtual_owner_signed_mm", 0.0)
        vp_agent = rc.get("virtual_agent_provisional_mm", 0.0)
        # D2: A SIGNATURE COVERS ONLY WHAT IT NAMES. Everything else is UNCOVERED, and no amount
        # of prose in --owner-signature can cover it. Agent-provisional closure edges, blank paper,
        # and bridged undrawn stubs are all UNCOVERED by construction.
        uncovered = round(vp_agent + up + ip, 1)
        sig = rc.get("owner_signoff")
        if (vp > MAX_UNSIGNED_VIRTUAL_MM or up > MAX_UNSIGNED_UNBACKED_MM
                or ip > MAX_UNSIGNED_INFILL_MM) and not (sig and sig["edges_bound"]):
            print(f"  REFUSING to write --room-out: this room's perimeter is NOT 100% ink.\n"
                  f"    perimeter        {rc.get('perimeter_mm')} mm\n"
                  f"    VIRTUAL (signed) {vp} mm  ({rc.get('virtual_fraction', 0) * 100:.1f}%)  "
                  f"> {MAX_UNSIGNED_VIRTUAL_MM} mm\n"
                  f"    UNBACKED (paper) {up} mm  ({rc.get('unbacked_fraction', 0) * 100:.1f}%)  "
                  f"> {MAX_UNSIGNED_UNBACKED_MM} mm\n"
                  f"  A signed zoning line is an OWNER call, not a measurement. Supply "
                  f"--owner-signature \"...\" to adopt this room; the signature and the virtual/"
                  f"unbacked fractions are stamped into the spec.", file=sys.stderr)
            return 4

        # ------------------------------------------------------- D2: WHAT THE SIGNATURE CANNOT COVER
        # The owner signed the north zoning line. He did NOT sign the BF01 extension, he did NOT
        # sign the two SW corner stubs, and he cannot sign blank paper. If the room only closes
        # because of those, then THE ROOM CANNOT BE WRITTEN WITHOUT AN OWNER DECISION. We say so.
        if uncovered > MAX_UNSIGNED_VIRTUAL_MM and not a.write_provisional:
            prov = [v for v in rc["signed_virtual_walls"]
                    if v.get("provenance") != "owner-signed"]
            print(f"  REFUSING to write --room-out: {uncovered} mm of this room's perimeter is "
                  f"NOT COVERED BY ANY SIGNATURE.\n"
                  f"    owner-signed (AUTHORISED) {vp_owner} mm  -- named by the signature and "
                  f"verified against the geometry\n"
                  f"    agent-provisional         {vp_agent} mm  -- NOT signed by anyone\n"
                  f"    unbacked (blank paper)    {up} mm\n"
                  f"    closure infill (bridged)  {ip} mm\n"
                  + "".join(f"      {v['id']}  {v['spec']}  {v['length_mm']} mm\n" for v in prov)
                  + f"  A LEDGER ENTRY authorises ONLY THE EDGE ITS KEY NAMES. These edges have no "
                  f"entry, and there is nothing the agent can TYPE that gives them one.\n"
                  f"  THIS ROOM CANNOT BE WRITTEN WITHOUT AN OWNER DECISION on the edges above. "
                  f"Either the OWNER (not the agent) adds their canonical keys to the ledger — run "
                  f"--ledger-keys to print them — or, to write the room anyway as an explicitly "
                  f"NOT-ADOPTED measurement artefact, pass --write-provisional. "
                  f"--write-provisional IS NOT A SIGNATURE: it stamps adopted=false and names "
                  f"every unsigned edge in the spec.",
                  file=sys.stderr)
            return 5

        adopted = uncovered <= MAX_UNSIGNED_VIRTUAL_MM

        room_ops = openings_on_outline([tuple(p) for p in rc["outline_mm"]],
                                       meta.get("openings_typed", []))
        spec = {
            "schema": "interior-ai/room-spec@0.2",
            "units": "mm",
            "version": "012p3-auto-v2",
            "note": ("AUTO-DERIVED from the vector ink of %s p%d by bluehouse_plan_reader.py "
                     "(wall poche + boundary ink + flood closure). NO dimension was typed in: "
                     "every outline coordinate is a wall FACE that exists on the sheet. "
                     "ceiling_mm is an OWNER input (a plan sheet has no ceiling height). "
                     "This room is NOT 100%% ink -- read ink_provenance before believing any "
                     "number in it. CLIENT DATA -- local only."
                     % (os.path.basename(a.pdf), a.page)),
            # room.openings travels WITH the outline: build_room cuts + glazes them. Without this
            # the room renders as a floor and four blank walls (round 3, FATAL 1).
            # ink_pens/composite_backed_mm ride along (o.get: a future signed-void record may
            # lack them): the reviewer auditing ONE room must see a hairline-backed or
            # composite-only opening IN room.openings, not only in the provenance block.
            "room": {"outline_mm": rc["outline_mm"], "ceiling_mm": a.ceiling_mm,
                     "openings": [{k: o.get(k) for k in ("id", "type", "rect", "length_mm",
                                                         "axis", "ink_coverage", "ink_pens",
                                                         "composite_backed_mm", "signed")}
                                  for o in room_ops]},
            "builtins": [], "items": [],
            "ink_provenance": {
                "ink_backed": rc.get("ink_backed"),
                "perimeter_mm": rc.get("perimeter_mm"),
                "virtual_perimeter_mm": vp,
                "virtual_fraction": rc.get("virtual_fraction"),
                "virtual_owner_signed_mm": rc.get("virtual_owner_signed_mm"),
                "virtual_agent_provisional_mm": rc.get("virtual_agent_provisional_mm"),
                "unbacked_perimeter_mm": up,
                "unbacked_fraction": rc.get("unbacked_fraction"),
                "infill_perimeter_mm": ip,
                "infill_fraction": rc.get("infill_fraction"),
                "owner_signoff": sig,
                "owner_authorised_mm": vp_owner,
                "NOT_covered_by_any_signature_mm": uncovered,
                "adopted": adopted,
                "adoption_status": (
                    "OWNER-ADOPTED: every non-ink millimetre of this perimeter is named by the "
                    "owner's signature." if adopted else
                    "NOT ADOPTED. %.1f mm of this perimeter is covered by NO signature "
                    "(agent-provisional %.1f mm + blank paper %.1f mm + bridged stubs %.1f mm). "
                    "Written under --write-provisional, which IS NOT A SIGNATURE. This room is a "
                    "measurement artefact awaiting an owner decision on the edges listed in "
                    "virtual_walls with provenance=agent-provisional. Do not render it as an "
                    "owner-approved room and do not score anything against it."
                    % (uncovered, vp_agent, up, ip)),
                "signed_by": a.signed_by,
                "gate": ("D1 (round 5): an edge is OWNER-SIGNED iff its CANONICAL KEY is in the "
                         "OWNER-AUTHORED ledger (zoning_signoff_gate.py, the ffe_signoff_gate "
                         "pattern). There is no --owner-signature: a signature the caller composes "
                         "at run time is authored by the caller. Agent-provisional edges, blank "
                         "paper and bridged stubs are NEVER covered by a ledger entry; if any of "
                         "them exceeds %.1f mm the room is refused unless --write-provisional "
                         "stamps it adopted=false."
                         % MAX_UNSIGNED_VIRTUAL_MM),
                "virtual_walls": rc["signed_virtual_walls"],
                "sides": rc.get("sides"),
                "WARNING": ("A signed virtual edge is NOT a measured wall. OWNER-SIGNED edges "
                            "(id OE**) carry an owner_key that resolves to a ledger entry; "
                            "AGENT-PROVISIONAL edges (id E**) are the reader's own closure crutch "
                            "and carry none. Do not let a downstream consumer treat either as ink."),
            },
            "provenance": {"closure": {k: rc[k] for k in
                                       ("closed", "why", "area_m2", "grid_mm", "seed_mm")},
                           "closure_infills": rc["closure_infills"],
                           "unbacked_voids": rc["unbacked_voids"],
                           "openings": meta.get("openings_typed", []),
                           "openings_on_this_room": [o["id"] for o in room_ops],
                           "ceiling_mm_source": "OWNER INPUT (--ceiling-mm); not read from the sheet"},
        }
        _write(a.room_out, spec)
        print(f"  wrote {a.room_out}  (room-spec@0.2, {rc['n_vertices']} vertices, "
              f"{rc['area_m2']} m2, {len(room_ops)} opening(s): "
              f"{', '.join(o['id'] + ':' + o['type'] for o in room_ops) or 'NONE'})")
        print(f"    INK GATE  virtual {vp} mm ({rc.get('virtual_fraction', 0) * 100:.1f}%) | "
              f"unbacked {up} mm ({rc.get('unbacked_fraction', 0) * 100:.1f}%) | "
              f"infill {ip} mm")
        if sig:
            print(f"    LEDGER    {sig['ledger_path']}  sha256={sig['ledger_sha256'][:16]}…  "
                  f"({sig['n_ledger_entries']} entr"
                  f"{'y' if sig['n_ledger_entries'] == 1 else 'ies'})")
            for b in sig["edges_bound"]:
                print(f"      BOUND   {b['id']} {b['spec']} = {b['length_mm']} mm  -> by="
                      f"{b['by']!r} {b['date']} zone={b['zone']!r}")
            print(f"      orphans_present={sig['orphans_present']}  "
                  f"malformed_present={sig['malformed_present']}")
            for o in sig["orphan_entries"]:
                print(f"      ORPHAN  {o['key']} (by {o['by']}) binds no edge written here")
        else:
            print("    LEDGER    none — NOTHING on this perimeter is owner-signed")
        print(f"    SIGNED    owner-authorised {vp_owner} mm (ledger-bound)")
        print(f"    ADOPTION  adopted={adopted}  |  NOT covered by any signature: {uncovered} mm")
    return 0


def _write(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


if __name__ == "__main__":
    raise SystemExit(main())

# =====================================================================================
# LIMITS (what this reader does NOT do)
# =====================================================================================
# - It does not produce a closed room polygon, and on the source sheet it CANNOT: the main
#   living zone has no wall ink on 3 of its 4 sides (two are metre-scale openings, one is a
#   wall END rather than a wall). outline_from_seed reports those as open_sides and stops.
# - It does not classify openings. Window vs door vs solid infill is owner-only.
# - It does not resolve corners, merge runs into a graph, or emit centrelines.
# - It reads AXIS-ALIGNED walls only; a skewed wall quad raises RefuseSheet rather than
#   being silently squared off.
# - The (black, 0.84, lone-quad, ~100 mm) predicate is pinned on ONE sheet. The 0.84 wall pen
#   was seen on other Bluehouse projects, but the quad structure and the 100 mm thickness were
#   only verified here. It is a pen-table convention, not a law.
# - Scale detection assumes the plotted wall is ~100 mm. A sheet whose thinnest wall pen quad
#   is a 200 mm party wall would snap to the wrong denominator (it would refuse, not lie —
#   but it would refuse a legitimate sheet).
