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
ISL_CENTRE_X = 2347                 # DERIVED from the drums (2318 until 2026-08-29,
                                    # when the near drum's right silhouette was found
                                    # to have been read 34 px wide - see derive_island2)
ISL_W = 1250                        # ASSERTED - AND NOT MEASURABLE FROM THIS PLATE.
                                    # 2026-08-29: tried to measure it by tracing the
                                    # slab silhouette and unprojecting onto the slab
                                    # plane. REFUSED: the camera sits at z=1421 and
                                    # the slab at z=827-899, so the ray grazes that
                                    # plane - moving the assumed height by the slab
                                    # thickness alone (72 mm) moves the unprojected
                                    # X by 512 mm. A depth read through a nearly
                                    # parallel plane is not a measurement. Two spans
                                    # of the traced edge also returned +2.87 and
                                    # +25.35 deg, which is the chord refusal again.
                                    # THE ROUTE THAT WOULD SETTLE IT: gh-21 shows the
                                    # same island from a second station where the
                                    # width is across the view, not along it. That
                                    # needs a second camera solve and is a round of
                                    # its own.
ISL_X0, ISL_X1 = ISL_CENTRE_X - ISL_W // 2, ISL_CENTRE_X + ISL_W // 2
ISL_Y0, ISL_Y1 = 2256, 5328         # DERIVED  near tip lands on the bullnose at u=1080
ISL_H = 899                         # DERIVED  drum top 827 + a 72 mm slab
ISL_SLAB_T = 72
SLAB_BULLNOSE_R = 10                # ASSERTED  the slab's rounded arris. The number was
                                    # 33 in the builder, untagged and unsourced, and I
                                    # nearly re-tagged it MEASURED by copying it across.
                                    # On a 72 mm slab a 33 mm arris top AND bottom leaves
                                    # 6 mm of flat face and Blender's bevel then eats
                                    # 35 mm off the extent - spec_agreement caught that.
                                    # 10 mm is a plain assertion until somebody measures
                                    # the arris off a crop.
ISL_STONE_Y1 = 3250                 # travertine volume is the FAR half, drums the near
DRUM_Y = (3465, 4403)               # DERIVED  939 mm apart (derive_island2 prints 939)
DRUM_R = 194                        # DERIVED  389 dia. WAS 231, i.e. every frame this
                                    # lane has produced rendered the drums 19% too fat.
                                    # The near drum's silhouette is 188.93 px wide, not
                                    # the 225 that was typed; the far drum, read
                                    # independently, corroborates to 3.3%.

STOOL_W, STOOL_D, STOOL_H = 470, 460, 815     # SPEC  SP01 Michelle bar stool LOW
STOOL_SEAT = 645
STOOL_TUBE_R = 11                   # MEASURED  frame tube radius off the plate's stool
STOOL_RAIL_R = 9                    # MEASURED  the thinner stretcher
STOOL_RAIL_Z = 300                  # ASSERTED  stretcher height
STOOL_X = 3250                      # on the camera side of the island
STOOL_Y = [2900, 3450]

GLASS_Y = -432
GLASS_X0, GLASS_X1 = 0, 8000
TRANSOM_Z = 2460                    # DERIVED 2026-08-29. Was 2352 and untagged. The
                                    # fitted transom line (family B, rms 1.1 px)
                                    # unprojected onto the glazing plane y=GLASS_Y
                                    # reads z = 2460.3 mm with a SPREAD OF 1.0 mm
                                    # across 1.9 m of that plane - i.e. the line
                                    # really is horizontal there, which is the
                                    # check. At 2352 the transom projected 38 px
                                    # below its own fitted line and the residual
                                    # sat in the table unread.

# ---- the shell and the fabrication details, MOVED HERE 2026-08-29 ------------------
# They were typed inside 05_build/build_kitchen.py, whose own docstring says "Everything
# dimensional comes from ../03_blockout/room_spec.py". It said that while the builder held
# fourteen dimensions of its own, none of them tagged, none of them visible to the plan, the
# overlay or the clearance check. A second transcription of a spec is not a spec; it is the
# next drift. (The one that had already happened: the builder still asked for RS.DRUM_X and
# RS.ISL_STONE_X0 a full day after the island was turned onto its true axis, so the build
# could not import at all and every frame in 05_build/out/ was made by the wrong island.)
WALL_T = 180                        # ASSERTED  a rendered wall only has to be opaque
SHELL_X1 = 12600                    # ASSERTED  the camera stands 6971 off the kitchen wall,
SHELL_Y1 = 17000                    # ASSERTED  and 11801 down the room; the shell has to
                                    #           enclose it, INCLUDING the walls BEHIND the
                                    #           camera - the tutorial is explicit at 06:45
                                    #           that they are what fills the shadow side.
GLAZE_HEAD_T = 240                  # ASSERTED  head/soffit depth over the glazing
TRANSOM_T = 90                      # ASSERTED  transom bar depth, 45 either side
MULLION_PITCH = 2150                # ASSERTED  pane width; the plate's floor rectangles are
MULLION_W = 62                      # ASSERTED  panes, not leaves - without them a 12.6 m
                                    #           opening throws one undifferentiated wash
FRAME_D = 90                        # ASSERTED  window frame depth; INNER FACE ON THE
                                    #           DATUM y=GLASS_Y, not straddling it
GLASS_SET = 34                      # ASSERTED  the sealed unit sits this far outboard of
GLASS_T = 22                        # ASSERTED  the frame's inner face, and is this thick
SPLASH_T = 25                       # ASSERTED  splashback thickness
PLINTH_INSET = 60                   # ASSERTED  toe recess under bench and tall bank
ISL_STONE_INSET = 140               # ASSERTED  the slab overhangs the travertine body
OVEN_PROUD = 14                     # ASSERTED  oven face stands this proud of the door line
OVEN_RECESS = 30                    # ASSERTED  and its own box starts this far back
OVEN_Z0, OVEN_Z1 = 900, 2150        # DERIVED   two ovens stacked in the tall bank
OVEN_SIDE_INSET = 40                # ASSERTED  reveal either side of the appliance
CURTAIN_STANDOFF = 190              # ASSERTED  sheer hangs this far in front of the glass
CURTAIN_TOP_DROP = 250              # ASSERTED  below the ceiling

WALKWAY_MM = ISL_X0 - BENCH_DEPTH   # 1072 with the corrected drums - and it CANNOT
                                    # decide the code question. NKBA's one-cook aisle
                                    # is 1067 mm and the walkway lands 5 mm over it,
                                    # while the inputs are worth nothing like 5 mm:
                                    # moving both drum base rows together by the +-10
                                    # px they are actually worth swings the walkway
                                    # from 1026 to 1194, and three independent routes
                                    # to the centre-line give 1049 / 1072 / 1142. And
                                    # ISL_W, which the walkway also depends on, is
                                    # declared NOT MEASURABLE from this plate ten
                                    # lines above. So the honest verdict is: the
                                    # walkway is 1050-1150 mm and whether it clears
                                    # NKBA is UNDECIDABLE HERE. A verdict sized
                                    # smaller than its own inputs' noise is the
                                    # defect, not the number.
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
        # "B4_island_top" IS WITHDRAWN, 2026-08-29. It paired the island's near END edge
        # with a fitted image line of slope -0.031. Traced on the plate, the slab's front
        # edge runs the OTHER WAY - about +0.060 - so the stored fit is not on the feature
        # it is named for, and it was the worst fit in the file (rms 3.92 px) besides. It
        # was one of only TWO lines defining family B, and with the derived camera it
        # missed by 72 px while all five family-A lines landed within 9.4. A guide line
        # that names the wrong world feature does not measure anything; chasing its
        # residual would have moved the island to fit a mistake. The island is pinned by
        # the two drums instead (derive_island2), which is a better instrument anyway.
        # WHAT THIS COSTS: family B is now the transom alone, so vp_B has no redundancy
        # left. Dropping B4 from the camera solve moves f by 0.5% (4248 vs 4225 px), which
        # is why the camera is NOT re-solved in this round - but it needs a second real
        # family-B line before anyone calls the solve redundant again.
    }
