#!/usr/bin/env python3
"""ergonomics_ref.py — cited ergonomic reference constants for the FUNCTION layer.

Distilled from knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md (NLM DR
notebook 5de4bb36, 2026-07-03: SMPTE, THX, Panero & Zelnik, Neufert, NKBA, ANSI/BIFMA)
+ residential-clearances.md. These are ergonomic/COMFORT values — codes-th statutory
floors ALWAYS outrank where they overlap. All metric (mm / deg). stdlib-only,
importable (feeds placement_logic.py and future FUNCTION rules).
"""

# --- TV / flat-screen viewing (SMPTE 30° = diag×1.6, THX 36° = ×1.4, THX 40° = ×1.2) ---
# The spec carries no screen size, so distance is a COMFORT BAND (~50–75 in across
# THX40→SMPTE), used as a soft WARN, not a hard gate.
TV_VIEW_DIST_MM = (1500, 4500)
TV_VERT_ANGLE_MAX_DEG = 35            # absolute max off seated eye level (>15° = neck strain)
TV_MOUNT_H_LIVING_MM = (1016, 1118)   # screen centre AFF, seated
TV_MOUNT_H_BEDROOM_MM = 1270          # reclined, tilt 10–15°

# --- standard mattress sizes, W×L (Panero & Zelnik). Spec bed footprints include the
# frame, so the tolerance is generous — this catches GROSS mis-scale only (GS-02). ---
BED_SIZES_MM = {
    "twin": (991, 1905), "full": (1372, 1905),
    "queen": (1524, 2032), "king": (1930, 2032),
}
BED_SIZE_TOL_MM = 150

# --- furniture heights (mm). Note: a chair/sofa spec `h` is the BACKREST, not the seat,
# so seat-height 400–450 is NOT checkable here (would need a seat_h field). ---
TABLE_H_MM = {
    "coffee_table": (300, 460), "round_table": (300, 460),
    "side_table": (380, 480), "end_table": (380, 480), "nightstand": (380, 700),
    "dining_table": (700, 780), "desk": (700, 780),
}
WARDROBE_DEPTH_MM = (450, 650)        # a functional hanging wardrobe (600 typical)

# --- RELATIONS (mm) — heights that are a relation to another piece, not a band of
# their own (P2i; R9's law arriving in this layer: a band answers "is this a legal
# table", the relation answers "can the sleeper reach it" — TABLE_H_MM["nightstand"]
# = (380,700) happily passes a deck 80 mm below the mattress top, C2#10).
# Value = nightstand DECK TOP minus MATTRESS TOP (spec `h` of each; a bed item's `h`
# is the mattress plane in build_room._build_bed).
# DECLARED ASSUMPTION (DRW-2 ladder, lowest rung — recorded loudly so nobody
# upgrades it by forgetting): no sourced numeric relation exists. Vault holds only
# absolutes (TH bedroom-services staging note: premium nightstands 500–550 mm);
# the Design Systems corpus returned NOT IN SOURCES (NLM a5a43395, conversation
# b39e68d6 turn 1, 2026-08-18 — Human Dimension has bed heights and clearances but
# night-table height "alignments relative to the mattress are not
# anthropometrically dimensioned"). Band encodes the reach argument the row was
# filed on: below the mattress plane a reclined hand loses the deck (−80 was the
# filed defect), level-to-slightly-above serves; above ~150 the deck crowds the
# sleeper's head space.
NIGHTSTAND_TOP_VS_MATTRESS_MM = (-50, 150)

# --- circulation (Neufert) ---
WALKWAY_MIN_MM = 600
WALKWAY_COMFORT_MM = (800, 900)
DOOR_LEAF_MM = (800, 900)

# --- bathroom fixture spacing (mm) — NKBA/Neufert/P&Z, from bathroom-kitchen-planning.md.
# REFERENCE only: the clearance GATE is suite_clearance + codes-th (ฉ.39). placement_logic
# checks the functional LOGIC (use-frequency ordering + wet/dry zoning), not these numbers. ---
BATH_CLEAR_FRONT_MM = 762          # NKBA clear floor in front of WC/basin/shower/tub
BATH_BASIN_TO_WC_MM = 508          # NKBA basin centreline → WC / sidewall
BATH_WC_TO_WET_MM = 457            # NKBA WC centreline → shower/tub barrier
BATH_BASIN_TO_BASIN_MM = 914       # NKBA centreline-to-centreline, double vanity

# --- kitchen work-triangle (NKBA; feeds placement_logic.kitchen_work_triangle) ---
KITCHEN_TRIANGLE_LEG_MM = (1219, 2743)   # each sink–cooktop–fridge leg
KITCHEN_TRIANGLE_PERIM_MAX_MM = 7925     # total perimeter
KITCHEN_AISLE_SINGLE_MM = 1067           # single-cook aisle (needs run grouping; not yet a rule)
KITCHEN_AISLE_MULTI_MM = 1219            # multi-cook aisle (ditto)


def nearest_bed_size(w, d):
    """Best-matching standard mattress for a footprint (orientation-agnostic) +
    whether it is within tolerance. Returns (name, (W,L), within_tol:bool, worst_mm)."""
    a, b = sorted((float(w), float(d)))
    best = None
    for name, (bw, bl) in BED_SIZES_MM.items():
        sw, sl = sorted((bw, bl))
        worst = max(abs(a - sw), abs(b - sl))
        if best is None or worst < best[3]:
            best = (name, (bw, bl), worst <= BED_SIZE_TOL_MM, worst)
    return best
