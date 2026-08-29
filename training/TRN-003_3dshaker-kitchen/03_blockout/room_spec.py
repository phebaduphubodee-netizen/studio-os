#!/usr/bin/env python3
"""room_spec.py - the blockout, as declared real-world millimetres.

WORLD FRAME (mm, Z up)
  origin  = the inside corner where the GLAZING wall meets the KITCHEN wall, at floor
  +X      = along the glazing wall, from that corner TOWARDS the camera (image left)
  +Y      = along the kitchen wall, from that corner TOWARDS the camera (image right)
  so the room the camera sees occupies +X, +Y and the two vanishing points are the
  -X and -Y directions.

Every number here is either MEASURED (from the plate, via the camera solve), SPEC (a
real product dimension I looked up), or ASSERTED (a standard I chose). The tag is on
each line, because the video's whole modelling rule is "block out paying attention to
the real world dimensions" - and a number nobody can tell apart from a measurement is
the defect this repo already has a rule about.
"""

# ============= RE-DERIVED 2026-08-29 after the owner said it TWICE ==================
# He said the island looked wrong. My first answer - "the axis is fine, the height was
# wrong" - was itself wrong, and it came with a confident-looking number. He said it
# again. The island is PARALLEL to the kitchen wall: measured 87.3 deg, i.e. 2.7 deg off
# parallel, where I had it at 90 deg off. I had it a full quarter turn out.
#
# WHAT SETTLED IT: the two bronze drums. Identical cylinders on the floor at two depths.
# Base height gives each one's depth, silhouette width gives the radius and confirms the
# depth, and the two centres give the axis - no curve to fit, no family to guess. See
# derive_island2.py. The drum outlines land exactly on the real drums in
# island_MEASURED.png.
#
# WHY MY FIRST MEASUREMENT LIED: I fitted a straight line to the slab's front edge and
# called its slope a direction. The slab is an OVAL - a straight fit across it returns a
# CHORD, whose slope depends on which span you fit (two spans gave -0.031 and -0.049,
# which should have stopped me). I then matched that chord's vanishing point to a
# "family" by PROXIMITY, 7711 against the transom's 7917, when both sit thousands of
# pixels off-frame where a 0.02 slope error moves the vanishing point by kilometres.
#
# AND THE STOOL IS THE LOW ONE. A 936 slab over a 745 seat leaves 154 mm of knee room.
# SP01 Michelle also comes as a LOW bar stool, 815 overall / 645 seat, which gives 254.
# That re-scales the whole room by 0.9601, and the Wolf oven then measures 771 against a
# published 762 (was 803). One misread product spec had moved every number by 4%.
CAM_H = 1421.0                      # DERIVED  SP01 Michelle LOW stool, 815 mm overall
CAM_TO_KITCHEN_WALL = 6971.0
CAM_Y = 11801.0
CEILING = 3514
BENCH_H = 900
UPPERS_BOTTOM = 1616                # DERIVED  A1/A5 line pair
UPPERS_DEPTH = 350
BENCH_DEPTH = 650
TALL_DEPTH = 700
PLINTH = 130

BENCH_Y0, BENCH_Y1 = 0, 2804        # DERIVED  u=610 (corner) .. u=1030 (oak step)
TALL_Y0, TALL_Y1 = 2804, 5300
OVEN_Y0, OVEN_Y1 = 2804, 3565       # DERIVED  771 mm (Wolf 30in double oven = 762)
FRIDGE_Y0, FRIDGE_Y1 = 3565, 4442

# ---- island: LONG AXIS ALONG Y, i.e. parallel to the kitchen wall ------------------
ISL_CENTRE_X = 2318                 # DERIVED from the drums
ISL_W = 1250                        # ASSERTED  gives a 1094 mm walkway to the bench
ISL_X0, ISL_X1 = ISL_CENTRE_X - ISL_W // 2, ISL_CENTRE_X + ISL_W // 2
ISL_Y0, ISL_Y1 = 2256, 5328         # DERIVED  near tip lands on the bullnose at u=1080
ISL_H = 899                         # DERIVED  drum top 827 + a 72 mm slab
ISL_SLAB_T = 72
ISL_STONE_Y1 = 3250                 # travertine volume is the FAR half, drums the near
DRUM_Y = (3481, 4420)               # DERIVED  938 mm apart
DRUM_R = 231                        # DERIVED  462 dia

STOOL_W, STOOL_D, STOOL_H = 470, 460, 815     # SPEC  SP01 Michelle bar stool LOW
STOOL_SEAT = 645
STOOL_X = 3250                      # on the camera side of the island
STOOL_Y = [2900, 3450]

GLASS_Y = -432
GLASS_X0, GLASS_X1 = 0, 8000
TRANSOM_Z = 2352

WALKWAY_MM = ISL_X0 - BENCH_DEPTH   # 1043 - and something checks it now.
# The comment here said 1094 until 2026-08-29. It was a real number from an earlier
# island centre and it stayed after the centre moved, which is the small version of the
# whole defect this lane just paid for: a value that stops tracking the thing it
# describes reads exactly like one that still does. clearance_check now scores this gap
# as REVIEW - 1043 sits BELOW NKBA's 1067 mm one-cook aisle and well below P&Z's
# 1219 for opposing counters (knowledge/ergonomics/residential-clearances.md).


def boxes():
    """(name, (x0,y0,z0), (x1,y1,z1)) - the guide boxes, fSpy's '3D guide' at scale."""
    b = []
    b.append(("floor", (0, GLASS_Y, -20), (8000, 6500, 0)))
    b.append(("kitchen_wall", (-150, GLASS_Y, 0), (0, 6000, CEILING)))
    b.append(("glazing_wall", (0, GLASS_Y - 150, 0), (8000, GLASS_Y, CEILING)))
    b.append(("ceiling", (0, GLASS_Y, CEILING), (8000, 6500, CEILING + 150)))
    b.append(("bench", (0, BENCH_Y0, PLINTH), (BENCH_DEPTH, BENCH_Y1, BENCH_H)))
    b.append(("splashback", (0, BENCH_Y0, BENCH_H), (25, BENCH_Y1, UPPERS_BOTTOM)))
    b.append(("uppers", (0, BENCH_Y0, UPPERS_BOTTOM), (UPPERS_DEPTH, BENCH_Y1, CEILING)))
    b.append(("tall_bank", (0, TALL_Y0, PLINTH), (TALL_DEPTH, TALL_Y1, CEILING)))
    b.append(("island_stone", (ISL_X0 + 140, ISL_Y0, PLINTH),
              (ISL_X1 - 140, ISL_STONE_Y1, ISL_H - ISL_SLAB_T)))
    for i, dy in enumerate(DRUM_Y):
        b.append((f"drum{i}", (ISL_CENTRE_X - DRUM_R, dy - DRUM_R, 0),
                  (ISL_CENTRE_X + DRUM_R, dy + DRUM_R, ISL_H - ISL_SLAB_T)))
    b.append(("island_slab", (ISL_X0, ISL_Y0, ISL_H - ISL_SLAB_T), (ISL_X1, ISL_Y1, ISL_H)))
    for i, y in enumerate(STOOL_Y):
        b.append((f"stool{i}", (STOOL_X - STOOL_D / 2, y - STOOL_W / 2, 0),
                  (STOOL_X + STOOL_D / 2, y + STOOL_W / 2, STOOL_H)))
    return b


def guide_lines():
    """The world lines that the fitted image lines are supposed to land on."""
    return {
        "A1_upper_top":   [(UPPERS_DEPTH, BENCH_Y0, CEILING), (UPPERS_DEPTH, BENCH_Y1, CEILING)],
        "A5_splash_top":  [(UPPERS_DEPTH, BENCH_Y0, UPPERS_BOTTOM), (UPPERS_DEPTH, BENCH_Y1, UPPERS_BOTTOM)],
        "A6_bench_front": [(BENCH_DEPTH, BENCH_Y0, BENCH_H), (BENCH_DEPTH, BENCH_Y1, BENCH_H)],
        "A3_tall_plinth": [(TALL_DEPTH, TALL_Y0, PLINTH), (TALL_DEPTH, TALL_Y1, PLINTH)],
        "A7_oak_top":     [(TALL_DEPTH, TALL_Y0, CEILING), (TALL_DEPTH, TALL_Y1, CEILING)],
        "B1_win_transom": [(GLASS_X0, GLASS_Y, TRANSOM_Z), (GLASS_X1, GLASS_Y, TRANSOM_Z)],
        "B4_island_top":  [(ISL_X0, ISL_Y1, ISL_H), (ISL_X1, ISL_Y1, ISL_H)],
    }
