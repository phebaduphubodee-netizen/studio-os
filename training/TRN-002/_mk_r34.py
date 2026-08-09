"""spec_r33 -> spec_r34.  THE WARDROBE RE-DERIVED ON THE PLANE IT ACTUALLY STANDS ON.

WHAT THE ROUND IS TESTING, WRITTEN DOWN BEFORE THE RENDER
--------------------------------------------------------
The owner's build law (2026-08-08): dimension -> objects complete -> light,
because light is SOLVED from geometry and tuning it first MIGRATES the geometry
error into the light and material tables, where it stops being visible. This
round is that law applied to the one mass that was most wrong and never checked:
`closet_oak` declared its front face at y=2330. The measurement pass put it at
y=1130 -- wrong by about 1,200 mm -- and the proof is a floor line: on the
declared plane, z=0 projects to v=554.97 at u=326, and the image at v 555 is
unbroken cabinet wood with no boundary of any kind. The real wardrobe/floor
contact is at v=574.33.

PREDICTIONS, BEFORE THE RENDER, SO THE ROUND CAN FAIL:

  1. THE OAK NICHE WILL GO BRIGHTER, PROBABLY A LOT. `CLOSET_daylight` sits at
     y=400 and was bracketed to 40 W against the closet BACK WALL's white paint
     while the oak stood 1,930 mm from it. The oak now stands 730 mm from it.
     Gate #19 already measured that niche at 1.42x the target with the panel
     FAR away; nearer and recessed it can only rise. THIS IS NOT A REASON TO
     RETUNE THE LIGHT THIS ROUND -- it is the prediction that tests whether the
     1.42x was ever an albedo problem. If the niche comes back at ~1.4x again
     after a 2.6x change in distance, the light is not what is setting it.

  2. THE CLOSET BACK WALL AND WHITE DOOR WILL GO DARKER. The same card now has
     a 2.5 m tall wardrobe standing between it and most of the back wall. Those
     two regions are the anchors its 40 W was set against (1.03x / 0.88x), so
     they are the two numbers that say how much of that bracket was standing in
     for missing geometry.

  3. THE RECESS SHOULD DO WHAT THE ALBEDO COULD NOT. Gate #19's finding was
     "our flat panel cannot self-shadow". The niche is now a real cavity --
     ~250 mm deep with a return on its right. If the niche interior does NOT
     develop a gradient, the cavity is not the mechanism.

  4. THE WARDROBE'S LEFT EDGE SHOULD STAY HIDDEN. Every horizontal edge in the
     niche terminates at u 292.8 in the target -- that is the partition
     mullion's occluding contour, not the wardrobe's own edge. Our built
     mullion ends at u 277, sixteen pixels short, so this round rebuilds it to
     the measured pair. If a strip of wardrobe shows left of u 293, the
     occluder is still wrong.

WHAT IS MEASURED HERE AND WHAT IS DECLARED
------------------------------------------
MEASURED (this session, sub-pixel, backprojected through the r1 camera):
  front plane y=1130 (floor contact v=574.33 over 65 columns, sd 14.4)
  right edge  u 366.5 -> the oak/white-door step, at the SAME u across five
              heights v 360..520, which is what a vertical arris on a constant-y
              plane must do under this camera
  stile inner u 362.3 -> the niche return's near arris, also constant in v
  LED line    v = 0.02579*u + 315.994, 65 columns, rms 0.124 px -> z 1952.4 on
              y=1130 with sd 0.2 mm across the run
  shelf top   z 822.9 (measurement note, 70 columns, rms 0.095 px)
  plinth      106.2 +/- 1.0 mm
  height      >= 2506: the partition head's underside occludes this plane there,
              so every value above it renders identically from this camera
  mullion     the pair, from part_stile_M's own `seen`: 47.9 / 42.4 gap / 52.7

DECLARED, each with a reason and a gap key:
  carcass depth 300 mm = a ~250 mm niche plus a 50 mm back. The niche depth is
      a BOUND (100-350) from the return band, not a value. THE VAULT'S GARMENT
      CHART CONSTRAINS THE WIDTH, NOT THE DEPTH -- a hung shirt spans 550 mm at
      the shoulder (knowledge/ergonomics/casework-fixture-clearances-th-
      practice.md:47, PAPERROOM) against a measured 602 mm clear opening. An
      earlier draft of this file read that same 550 as a DEPTH and declared a
      600 mm carcass: a shared number is not a shared quantity.
      CROSS-CHECK THAT WAS NOT ENGINEERED: the niche's clear height falls
      out of two independent measurements -- the shelf's top at 822.9 and the
      LED line at v 324.5 -- as 1,131 mm to the strip's underside, against the
      same chart's hung-shirt height of 1,100 mm. Neither number was chosen to
      make that work. AND QUOTE ONE SURFACE, SAYING WHICH: the same cavity is
      1,137 mm to the head's underside and 1,129 mm if the strip is read on the
      front plane rather than at its declared setback. Three numbers for one
      quantity is this repo's own smell, so the figure of record is SHELF TOP
      TO STRIP UNDERSIDE = 1,131 mm -- the strip is what a hanger would hit.
  niche depth (a 100-350 bound, built at 250), strip setback, and the top of
      the unit -- UNMEASURABLE from this camera and declared as such. The
      plinth is built FLUSH with a shadow-gap groove; that choice came from the
      image at 10x and from R9b refusing the recessed version's cantilever,
      NOT from the tone, and it is recorded that way.

WHAT THIS ROUND DOES NOT DO
---------------------------
It does not touch the light. Not one wattage, not one aim. That is the whole
point of the ordering law: a light re-derived against geometry that is still
moving is a number that fits a room which will not exist.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "pipeline" / "scripts"))
import trn002_geom as G  # noqa: E402

spec = json.loads((HERE / "spec_r33.json").read_text(encoding="utf-8"))
CAM = spec["camera"]
WH = (spec["image"]["w"], spec["image"]["h"])

# --------------------------------------------------------------- measured px --
# Nothing below is a world coordinate. Every world number in this file is
# BACKPROJECTED from one of these, on a NAMED plane, which is the only way this
# lane has ever produced a number it could defend.
U_MULL_CONTOUR = 292.8   # every horizontal edge in the niche terminates here
U_STRIP_L, U_STRIP_R = 298.5, 362.5   # the bright run, peak Y > 0.70
U_STILE_INNER = 362.3    # the return's near arris; constant across v 360..440
U_WARD_RIGHT = 366.5     # oak -> white door; constant across v 360..520
STRIP_M, STRIP_B = 0.02579, 315.994   # v = m*u + b, 65 columns, rms 0.124 px

Y_FRONT = 1130.0         # the wardrobe's front plane (floor contact)
Z_SHELF_TOP = 822.9
H_PLINTH = 106.2

# ------------------------------------------------------------ declared, with --
# ------------------------------------------------------------ a reason each  --
# THE NICHE IS SHALLOW, AND I HAD DECLARED IT DEEP. The first draft of this file
# put the carcass at 600 mm from a garment chart's "width-depth 550" -- reasoning
# about a hanging WARDROBE. Looking at the crop settles what the numbers were
# arguing about: it is a DISPLAY niche with one shirt in it, and the return band
# beside the stile is only ~5 px wide. Refitted over the 50 rows where nothing
# hangs in front of it (v 332-355 and 440-465): far edge u 356.13, near edge
# u 361.08, band 4.95 px -> depth ~200 mm. Scatter is real and stated: the far
# edge's sd is 4.03 px, so the honest bound is 100-350 mm and 250 is declared
# inside it. The chart still earns its place, but for the WIDTH: a 550 mm
# shoulder in a 602 mm clear opening.
D_NICHE = 250.0
D_BACKPANEL = 50.0
D_CARCASS = D_NICHE + D_BACKPANEL
# PLINTH: FLUSH BOARD + SHADOW-GAP GROOVE, not a recessed toe. The measurement
# said in writing that tone rules out a PROUD board and separates nothing else,
# so both readings were live. Two things chose between them, in this order:
#   (1) THE IMAGE. At 10x the band shows a crisp dark LINE at its top and a face
#       below it that catches light much as the cabinet front does. A 20 mm toe
#       recess would put the whole band in a softer, more uniform shadow.
#   (2) CONSTRUCTABILITY, via R9b. Built as a recessed box the plinth became the
#       body's ONLY support and the body oversailed it by 20 mm — a cantilever
#       that is perfectly real joinery and that an AABB cannot tell from a
#       floating mass. The guard was RIGHT to refuse it, and the honest response
#       to a guard that cannot distinguish two things is to build the one that
#       is unambiguous, not to widen the guard. Recorded as a tiebreak on
#       BUILDABILITY, not on the reference, in declared_gaps.closet_plinth_depth.
GROOVE_T, GROOVE_D = 8.0, 8.0
T_SHELF = 30.0           # measured upper bound was 31.2 (a luminance ramp, not an arris)
Z_TOP = 2600.0           # measured occlusion bound 2506; anything above renders the same
STRIP_Y0, STRIP_D, STRIP_T = 1180.0, 26.0, 6.0   # setback UNMEASURABLE


def x_on_front(u):
    """u -> x on the wardrobe's front plane. Independent of v under this camera,
    which is exactly why the right edge reading the same u at five heights is
    evidence and not a coincidence."""
    return G.backproject(CAM, (u, 400.0), ("y", Y_FRONT), WH)[0]


X_WARD_R = x_on_front(U_WARD_RIGHT)
X_STILE_IN = x_on_front(U_STILE_INNER)
X_MULL_CONTOUR = x_on_front(U_MULL_CONTOUR)
# The left edge is OCCLUDED, so it is declared -- 60 mm past the contour, so the
# rebuilt mullion still covers it and no false gap renders.
X_WARD_L = X_MULL_CONTOUR - 60.0

# THE STRIP IS SOLVED ON ITS OWN PLANE, ALL THREE AXES, and the first version of
# this file did not: it took the ends from y=1130 and the height from y=1193, so
# the built ends reprojected 1.2 and 1.6 px away from the pixels they came from.
# Small, and exactly the error class this lane keeps paying for -- one object
# whose numbers were read on two different planes. A DECLARED setback is a
# declaration about the whole object, not about one of its axes.
Y_STRIP_MID = STRIP_Y0 + STRIP_D / 2.0
U_MID = 0.5 * (U_STRIP_L + U_STRIP_R)
V_STRIP = STRIP_M * U_MID + STRIP_B


def on_strip_plane(u, v):
    return G.backproject(CAM, (u, v), ("y", Y_STRIP_MID), WH)


X_STRIP_L = on_strip_plane(U_STRIP_L, STRIP_M * U_STRIP_L + STRIP_B)[0]
X_STRIP_R = on_strip_plane(U_STRIP_R, STRIP_M * U_STRIP_R + STRIP_B)[0]
Z_STRIP_MID = on_strip_plane(U_MID, V_STRIP)[2]
Z_HEAD = Z_STRIP_MID + STRIP_T / 2.0     # underside of the box above the niche

OAK = 0.42
_M_PLANE = ("M(front plane y=1130: the wardrobe's floor contact fitted at "
            "v=574.33 over 65 columns, sd 14.4 mm. The DECLARED y=2330 is "
            "refuted by its own consequence -- on that plane z=0 projects to "
            "v=554.97 at u=326 and the image there is unbroken cabinet wood)")

NEW = [
    {   # ---------------------------------------------------------- carcass --
        "name": "closet_body", "kind": "box", "value": OAK,
        # Top is the SHELF's underside, not its top. The first draft ran the body
        # to 822.9 and the shelf 792.9..822.9, so the shelf sat buried in the
        # body's last 30 mm instead of resting on it — and my own assembly check
        # missed it by asserting `body top == shelf top`, which was the bug
        # written as the test.
        "c": [(X_WARD_L + X_WARD_R) / 2, Y_FRONT + D_CARCASS / 2,
              (H_PLINTH + Z_SHELF_TOP - T_SHELF) / 2],
        "s": [X_WARD_R - X_WARD_L, D_CARCASS, Z_SHELF_TOP - T_SHELF - H_PLINTH],
        "prov": _M_PLANE + " / M(right edge u=366.5, the oak/white-door step, "
                "read at the SAME u at v 360/400/440/480/520 -- a vertical "
                "arris on a constant-y plane is u-invariant under this camera, "
                "so five agreeing heights is the check, not a repeat) / "
                "D(left edge OCCLUDED by the partition mullion, whose contour "
                "lands at u 292.8; set 60 mm past it) / D(depth 600: a hung "
                "shirt is 550 mm deep per "
                "knowledge/ergonomics/casework-fixture-clearances-th-practice.md:47 "
                "and the target shows one hanging in this unit -- see "
                "declared_gaps.closet_body_depth)",
        "why": "the closed lower half of the dressing-room wardrobe. Below "
               "z~900 the target shows NO return beside the front stile "
               "(u 356-362 is dark at v 360-440 and gone by v 470), which is "
               "what a flush cabinet front looks like and what a recess does "
               "not.",
        "seen": "u 293..366, v ~468..570 -- the oak below the shelf, Ylin "
                "0.47-0.50 and uniform, bounded below by the plinth's dark "
                "band and right by the white door at u 367.",
    },
    {   # ------------------------------------------------------------- head --
        "name": "closet_head", "kind": "box", "value": OAK,
        "c": [(X_WARD_L + X_WARD_R) / 2, Y_FRONT + D_CARCASS / 2,
              (Z_HEAD + Z_TOP) / 2],
        "s": [X_WARD_R - X_WARD_L, D_CARCASS, Z_TOP - Z_HEAD],
        "prov": _M_PLANE + " / M(the unit is continuous oak from the LED line "
                "at z 1952 up to v~247, where the partition head's underside "
                "cuts it off -- that contour meets this plane at z 2506..2526 "
                "across u 300..355, so the unit runs to AT LEAST 2506) / "
                "D(top 2600: UNMEASURABLE above the occlusion, and every value "
                "above 2530 renders identically from this camera -- see "
                "declared_gaps.closet_head_top)",
        "why": "the box above the niche opening. It is what the LED strip is "
               "fixed to and what makes the opening an opening.",
        "seen": "u 293..366, v ~250..322 -- warm oak brightening downward from "
                "Ylin 0.27 at the head's cut-off to 0.46 just above the LED "
                "line, B/R 0.53-0.66 throughout.",
    },
    {   # -------------------------------------------- right stile == return --
        "name": "closet_stile_R", "kind": "box", "value": OAK,
        "c": [(X_STILE_IN + X_WARD_R) / 2, Y_FRONT + D_CARCASS / 2,
              (Z_SHELF_TOP + Z_HEAD) / 2],
        "s": [X_WARD_R - X_STILE_IN, D_CARCASS, Z_HEAD - Z_SHELF_TOP],
        "prov": "M(inner edge u=362.3 -- the right-hand limit of the dark band "
                "at u 356..362, which holds the SAME u at v 360/380/400/420 "
                "while the band's LEFT edge wanders 355.3->357.8; a wandering "
                "edge is a garment silhouette, a fixed one is an arris) / "
                "M(outer edge u=366.5, with the stile therefore 33.4 mm wide) "
                "/ D(depth: full carcass, so this one member is both the front "
                "stile and the niche's right internal return)",
        "why": "the stile beside the niche, and the return the light dies "
               "against. It is why the target shows a dark 6-px band there and "
               "our flat panel showed none.",
        "seen": "u 363..366 as the lit front face (Ylin 0.37-0.47) with its own "
                "shadowed return at u 356..362 (Ylin 0.14-0.28), v 360..440.",
    },
    {   # ------------------------------------------------------ niche back  --
        "name": "closet_niche_back", "kind": "box", "value": OAK,
        "c": [(X_WARD_L + X_STILE_IN) / 2,
              Y_FRONT + D_CARCASS - D_BACKPANEL / 2,
              (Z_SHELF_TOP + Z_HEAD) / 2],
        "s": [X_STILE_IN - X_WARD_L, D_BACKPANEL, Z_HEAD - Z_SHELF_TOP],
        "prov": "M-weak(niche depth ~200 mm: the dark return band beside the "
                "stile refitted sub-pixel over the 50 rows where nothing hangs "
                "in front of it -- far edge u 356.13, near edge u 361.08, band "
                "4.95 px. The far edge's sd is 4.03 px, so this is a BOUND of "
                "100-350 mm and not a value) / D(250 mm, inside that bound. "
                "The earlier reading of this same band as 245-462 mm was "
                "contaminated by the shirt's silhouette at the rows it used. "
                "See declared_gaps.closet_niche_back_y)",
        "why": "discharges the recess gap gate #19 opened -- 'our flat panel "
               "cannot self-shadow, 1.41x too bright'. A cavity can. This is "
               "the mass that makes that testable instead of arguable.",
        "seen": "u 293..355, v 354..462 -- but MOSTLY OCCLUDED by the hanging "
                "shirt (Ylin 0.57-0.64, B/R 0.84, i.e. neutral where the oak "
                "is warm). What is visible of it is the strip's wash.",
    },
    {   # ----------------------------------------------------------- shelf  --
        "name": "closet_shelf", "kind": "box", "value": 0.50,
        "c": [(X_WARD_L + X_STILE_IN) / 2, Y_FRONT + D_NICHE / 2,
              Z_SHELF_TOP - T_SHELF / 2],
        "s": [X_STILE_IN - X_WARD_L, D_NICHE, T_SHELF],
        "prov": "M(top front arris fitted over 70 columns u295-364, "
                "v 469.46..468.50, rms 0.095 px, three disjoint column groups "
                "agreeing to 1.9 mm; backprojected on the front plane y=1130 "
                "-> z 822.9) / D(thickness 30: the measured 31.2 is an UPPER "
                "BOUND only -- the lower edge is a 4-px luminance ramp, a cast "
                "shadow rather than an arris)",
        "why": "the niche floor. It is also what sets the niche's clear height, "
               "and that height is the round's one unengineered cross-check: "
               "1131 mm clear from this surface to the strip's underside, "
               "against a hung shirt's 1100 mm.",
        "seen": "u 293..362, v 468..469 as the front arris, with its top "
                "surface receding above it into shadow at v 444..462 (Ylin "
                "0.30-0.35) -- a horizontal surface below eye level shows its "
                "far edge HIGHER in frame, which is the check that this is a "
                "shelf and not a line on a flat panel.",
    },
    {   # ---------------------------------------------------------- plinth  --
        "name": "closet_plinth", "kind": "box", "value": 0.30,
        "c": [(X_WARD_L + X_WARD_R) / 2, Y_FRONT + D_CARCASS / 2, H_PLINTH / 2],
        "s": [X_WARD_R - X_WARD_L, D_CARCASS, H_PLINTH],
        "prov": "M(base band: top edge over 60 columns u296-355 rms 0.133 px, "
                "bottom over 50 columns rms 0.193 px, on the contact plane "
                "y=+1128.3 -> height 106.2 +/- 1.0; refitted independently "
                "today over 60 columns at rms 0.159 px -> 104.6 +/- 0.1, two "
                "fits agreeing to 1.6 mm) / D(FLUSH with the carcass front, "
                "the dark top line built as a shadow-gap groove rather than as "
                "a toe recess. Recess DEPTH is UNMEASURABLE at 0.16 px per "
                "10 mm inside a line whose FWHM is 1.6-2.6 px, so 0 mm and "
                "100 mm are the same picture. Chosen on the image at 10x and "
                "on buildability, NOT on tone. See "
                "declared_gaps.closet_plinth_depth)",
        "why": "a cabinet meets a floor with something, and this one does it "
               "with a base board and a shadow gap. NOTE THE CATEGORY: this is "
               "joinery on a cabinet, NOT the `wall_floor_junction` a critic "
               "asked for -- "
               "all three bedroom walls are 100% occluded at their base and "
               "that entry cannot be answered from this frame at all.",
        "seen": "u 296..355, v 560..574 -- the dark band above the floor "
                "contact, darkest Ylin 0.29-0.32 against 0.47-0.50 on the "
                "cabinet front above it.",
    },
    {   # ------------------------------------------- the shadow gap itself --
        "name": "rev_plinth_gap", "kind": "box", "value": 0.10,
        "c": [(X_WARD_L + X_WARD_R) / 2, Y_FRONT + GROOVE_D / 2,
              H_PLINTH - GROOVE_T / 2],
        "s": [X_WARD_R - X_WARD_L, GROOVE_D, GROOVE_T],
        "prov": "M(the line's POSITION: the top of the base band, fitted over "
                "60 columns at rms 0.159 px -> z 104.6-106.2) / D(section "
                "8 x 8 mm, carried from this lane's five existing `rev_` "
                "grooves, which are 6 x 8 mm. A gap this fine is UNRESOLVED at "
                "this camera -- the band's own FWHM is 1.6-2.6 px -- so it is "
                "matched photometrically by the `reveal_shadow` material, "
                "never sized by eye)",
        "why": "the dark line at the top of the plinth, which at 10x is the "
               "sharpest thing in that band and is what says `separate board` "
               "rather than `same panel, darker`. It wears reveal_shadow by "
               "the existing `rev_` prefix rule -- the lane's idiom for a "
               "negative detail too fine to model as a void, and the same "
               "reason the wardrobe's own grooves are thin dark slivers at the "
               "face rather than notches.",
        "seen": "u 296..355, v ~561 -- one to two pixels, the steepest "
                "bright-to-dark gradient anywhere in the base band.",
    },
    {   # -------------------------------------------------------- LED strip --
        "name": "led_strip", "kind": "box", "value": 0.95,
        "c": [(X_STRIP_L + X_STRIP_R) / 2, STRIP_Y0 + STRIP_D / 2, Z_STRIP_MID],
        "s": [X_STRIP_R - X_STRIP_L, STRIP_D, STRIP_T],
        "prov": "M(the line itself: sub-pixel peak per column, 65 columns, fit "
                "v = 0.02579*u + 315.994 at rms 0.124 px, peak Ylin "
                "0.72..0.964 -- the brightest thing in this quarter of the "
                "frame and it does not clip) / M(its ends: the bright run "
                "starts at u 298.5 and the mullion's contour is at 292.8, so "
                "the left end is VISIBLE and real, not cut off; the right end "
                "at 362.5 lands 1.6 mm from the stile's measured inner face, "
                "i.e. it runs the niche's full clear width, 500.0 mm) / "
                "D(setback and section UNMEASURABLE -- a 26 x 6 mm section "
                "under the head's front edge. The MEASURED quantity is the "
                "line's image position, which fixes z only once a y is "
                "declared: z 1952.4 on y=1130, 1991 on y=1680. See "
                "declared_gaps.led_strip_y)",
        "why": "the niche's own light, and it has been on the missing list "
               "since gate #19. Its PALETTE row was deleted at r30 for being "
               "unreachable -- correctly, since no mass wore it. Deleting a "
               "declaration does not build the object; this round builds the "
               "object and re-declares the material, in that order.",
        "seen": "u 298..362, v 324-325 -- a 1-2 px line at Ylin 0.94-0.96 with "
                "a warm wash below it (0.72 at v 330, RGB 0.82/0.71/0.56) and "
                "the oak above brightening toward it.",
    },
    {   # ------------------------------------- the partition mullion, as two --
        "name": "leaf_stile_R", "kind": "box", "value": 0.25,
        "c": [-3501.8 + 47.9 / 2, 0.0, 1186.0], "s": [47.9, 60.0, 2372.0],
        "prov": "M(the sliding leaf's own stile: 149 rows v250-442, sd "
                "0.072/0.097 px -> width 47.9, left edge x -3501.8 on y=0)",
        "why": "half of what one 72 mm mass has been standing for. The target "
               "shows TWO dark bars with a bright 42.4 mm gap between them "
               "(luma 170-177 against the bars' 80-92), spanning 144.5 mm in "
               "total -- twice the modelled member and in the wrong place.",
        "seen": "u 271.29..278.75, band v 320-440.",
    },
    {
        "name": "mullion_M", "kind": "box", "value": 0.25,
        "c": [-3357.3 - 52.7 / 2, 0.0, 1186.0], "s": [52.7, 60.0, 2372.0],
        "prov": "M(the fixed mullion: u 285.11..293.00 -> x -3410.0..-3357.3, "
                "52.7 mm wide on y=0)",
        "why": "THE OCCLUDER. Its right edge at x -3357.3 projects to u 293.00, "
               "and u 292.8 is exactly where every horizontal edge in the "
               "niche terminates in the target. The modelled member ended at "
               "u 277 -- sixteen pixels short -- so with the wardrobe now on "
               "its true plane, the old mullion would have exposed a strip of "
               "cabinet the reference does not show.",
        "seen": "u 285.11..293.00, band v 320-440.",
    },
]

DROP = {"closet_oak", "part_stile_M"}
spec["masses"] = [m for m in spec["masses"] if m.get("name") not in DROP] + NEW

# A split is a CHECKABLE claim, which is the whole reason it is allowed to
# discharge a drop -- rule_gate verifies every heir exists in this round.
spec["renamed"] = {
    "closet_oak": ["closet_body", "closet_head", "closet_stile_R",
                   "closet_niche_back", "closet_shelf", "closet_plinth",
                   "rev_plinth_gap", "led_strip"],
    "part_stile_M": ["leaf_stile_R", "mullion_M"],
}

spec["declared_gaps"].update({
    "closet_body_depth": (
        "300 mm, DECLARED as niche 250 + a 50 mm back. The camera cannot see "
        "behind the unit and nothing deeper is claimed. WHAT THE VAULT ACTUALLY "
        "CONSTRAINS HERE IS WIDTH, NOT DEPTH: a hung shirt spans 550 mm at the "
        "shoulder (knowledge/ergonomics/casework-fixture-clearances-th-"
        "practice.md:47) and the measured clear opening is 602 mm, so the "
        "garment the target shows fits with 52 mm to spare. The first draft of "
        "this spec used the same 550 as a DEPTH and declared a 600 mm carcass "
        "— reasoning about a hanging wardrobe when the reference shows a "
        "display niche."),
    "closet_head_top": (
        "2600 mm, DECLARED. The partition head's underside occludes this plane "
        "at z 2506..2526, so the unit is measured to run to AT LEAST 2506 and "
        "no camera in this frame can say more. Every value above ~2530 renders "
        "identically; 2600 was chosen as a built height, not as a measurement."),
    "closet_niche_back_y": (
        "Niche depth is a BOUND, not a value: 100-350 mm, built at 250. The "
        "probe is the dark return band beside the stile, and it only works on "
        "the rows where nothing hangs in front of it — refitted over v 332-355 "
        "and v 440-465 it gives a 4.95 px band, i.e. ~200 mm, with the far "
        "edge's sd at 4.03 px which is where the 100-350 comes from. TWO "
        "EARLIER READINGS OF THIS SAME BAND WERE WRONG IN OPPOSITE DIRECTIONS "
        "and both for the same reason — rows contaminated by the shirt: an "
        "earlier pass derived 462 mm and was refuted, and my own first pass "
        "today derived 245 mm from rows where the band's far edge is the "
        "garment's silhouette. The tell was there both times: a real arris "
        "holds its u across rows and a silhouette does not."),
    "closet_plinth_depth": (
        "Recess depth unmeasurable: 0.16 px per 10 mm inside a dark line whose "
        "FWHM is 1.6-2.6 px, so 0 mm and 100 mm are the same picture. Tone "
        "rules out a PROUD board and nothing else -- a recessed plinth and a "
        "flush board with a shadow-gap groove above it are not separable by "
        "measurement here. BUILT AS THE FLUSH BOARD, and the tiebreak is "
        "recorded because it did NOT come from the reference: (1) at 10x the "
        "band shows a crisp dark LINE at its top over a face that catches "
        "light much as the cabinet front does, which is what a groove looks "
        "like and not what a 20 mm toe recess looks like; and (2) the recessed "
        "version made the plinth the body's ONLY support with a 20 mm "
        "oversail, and R9b refused it. That refusal is CORRECT even though the "
        "cantilever is real joinery: an AABB cannot separate a designed "
        "oversail from a floating mass, and the response to a guard that "
        "cannot distinguish two things is to build the unambiguous one, never "
        "to widen the guard. If the reference is ever shown to demand the "
        "recess, the guard is what has to change, and it will need a declared "
        "support relationship rather than a looser tolerance."),
    "led_strip_y": (
        "The strip's setback is unmeasurable. What is measured is the LINE's "
        "position in the image (rms 0.124 px over 65 columns), and a line in an "
        "image fixes z only once y is declared: the same pixels read z 1952.4 "
        "on y=1130 and z 1991 on y=1680. Declared at the head's front edge."),
    "garments": (
        "ACQUISITION ATTEMPTED THIS ROUND (owner order 2026-08-08, the lane's "
        "first) AND IT FAILED AT A PLACE NOBODY HAD LOOKED. The sourcing half "
        "worked: 3D Warehouse has the exact object — a white shirt on a wooden "
        "hanger, which is what the target's niche contains — fetched under "
        "Trimble GML into the gitignored cache, and `asset_scale.py` was "
        "written to satisfy the standing scale-assertion rule and put it at "
        "715 mm tall, inside the garment band. IT IS AN 11.7 mm CUTOUT. The "
        "bounds check passed it, because thickness is not scale; a planar "
        "refusal now closes that and rejects it. Two further candidates: a "
        "hanging-clothes SET at 2303 mm (out of band, it is a rack) and a "
        "hooks row at 1449 mm wide (wrong object). "
        "AND THE REAL BLOCKER IS NOT THE SHIRT: `trn002_build.py` HAS NO glTF "
        "IMPORT PATH AT ALL. This lane can fetch an asset and assert it and "
        "cannot consume it — `build_room.py` has the ingest and this builder "
        "never got one. That is why 26 assets sit unused in assets/shared/. "
        "R8 stop-loss is one round, so this is a declared gap and the next "
        "step is a named piece of work with a size, not another search."),
    "etagere_objects": (
        "NOT MEASURED, and deferred rather than guessed. Adjudicated in "
        "writing at gate-18-r29.md:148-149 as boxes (books, tray) plus a "
        "lathed vase; the boxes are BUILD under R8 and the dried branches are "
        "ACQUIRE, which the paragraph above shows this builder cannot yet "
        "consume. Nothing here is blocked on a decision — only on a "
        "measurement pass this round did not spend, because r34's budget went "
        "to the wardrobe plane."),
    "far_room": (
        "NOT BUILDABLE, and this is a measurement rather than a deferral. The "
        "partition has TWO bays showing TWO different things and one mass "
        "(`closet_back`) has been standing for both. The RIGHT bay is the "
        "walk-through and the floor runs through it -- that is what this "
        "round's wardrobe stands in. The LEFT bay is a daylit sheer curtain "
        "with vertical folds, and nothing behind it can be fitted: no window, "
        "no table, no chair. Building any of them would be building to the "
        "manifest's wording rather than to the reference. The frame around the "
        "opening IS measured and already built (head top 2479.3 +/- 0.4, "
        "soffit 2370.5, bays 695.6 / 685.6, overall 1684.2; verifier mean "
        "reprojection error 0.22 px over 34 checks)."),
    "mirror": (
        "PENDING OWNER. The manifest lists a mirror; there is none in the "
        "reference. Reflecting 24 bay rays about y=0 shows a plane mirror "
        "there would be OBLIGED to show the bedroom's herringbone at v 540-580 "
        "and the white rug over u 181-498 -- the bay shows straight parallel "
        "planks and receding soffit geometry instead. The entry's whole "
        "provenance is C3#11 at r23, and by R7b law that critic was sent our "
        "own render alone, where an assumed blank `closet_back` panel rendered "
        "blown white. The critic described OUR FRAME correctly; the word was "
        "then filed as a fact about the target. Removing it is an edit to a "
        "claim about the reference, so it waits for a signature."),
    "wall_floor_junction": (
        "PENDING OWNER, and unanswerable as written. All three bedroom walls "
        "are 100% occluded at their base -- left u 17..72 behind the console, "
        "back u 72..731, right u 731..1128 -- so there is no column in this "
        "frame where a bedroom wall meets a floor. The two pixel bands the "
        "critic named are r27's pixels: in the target one is a pier, a rail "
        "and two chair legs, the other is entirely bed. `closet_plinth` in "
        "this round is NOT this entry; it is joinery on a cabinet."),
})

# ------------------------------------------------------- landmarks, not a script --
# The projection check for this wardrobe first lived in a scratchpad file, which
# means it would have run exactly once. `landmarks_3d` / `landmarks_px` are the
# lane's shipped mechanism for the same question and `dump_projections` reads
# them on EVERY build (trn002_build.py:479) — so the new edges go there instead,
# and the metric of record grows from 18 landmarks to 22 rather than a check
# existing somewhere nobody runs. Same law the reachability audit is built on.
#
# HONEST ABOUT WHAT EACH ONE TESTS: a horizontal edge is measured in v and a
# vertical arris in u, so a landmark on a horizontal edge has its u DERIVED from
# the world point and only its v is evidence. Named accordingly.
def _shelf_v(u):      # 70-column fit, v 469.46 at u=295 -> 468.50 at u=364
    return 469.46 - (469.46 - 468.50) * (u - 295.0) / (364.0 - 295.0)


def _plinth_v(u):     # 60-column fit, rms 0.159 px
    return -0.04412 * u + 575.381


def _strip_v(u):      # 65-column fit, rms 0.124 px
    return STRIP_M * u + STRIP_B


spec["landmarks_3d"].update({
    # both coordinates are evidence: a vertical arris crossed with a fitted edge
    "niche_shelf_stile": [X_STILE_IN, Y_FRONT, Z_SHELF_TOP],
    # v is the evidence; u follows from the world x
    "niche_strip_L": [X_STRIP_L, STRIP_Y0 + STRIP_D / 2, Z_STRIP_MID],
    "niche_strip_R": [X_STRIP_R, STRIP_Y0 + STRIP_D / 2, Z_STRIP_MID],
    "ward_plinth_top": [x_on_front(355.0), Y_FRONT, H_PLINTH],
})
spec["landmarks_px"].update({
    "niche_shelf_stile": [U_STILE_INNER, round(_shelf_v(U_STILE_INNER), 2)],
    "niche_strip_L": [U_STRIP_L, round(_strip_v(U_STRIP_L), 2)],
    "niche_strip_R": [U_STRIP_R, round(_strip_v(U_STRIP_R), 2)],
    "ward_plinth_top": [355.0, round(_plinth_v(355.0), 2)],
})

spec["id"] = "TRN-002 r34"
spec["round"] = 34
spec["STATUS"] = (
    "r34 = the wardrobe re-derived on the plane it stands on. `closet_oak` "
    "declared its front face at y=2330; the floor contact puts it at y=1130, "
    "wrong by ~1200 mm, and on the declared plane z=0 lands on unbroken "
    "cabinet wood. It becomes six masses -- body, head, right stile/return, "
    "niche back, shelf (top z 822.9 measured), recessed plinth (106.2 "
    "measured) -- plus `led_strip`, the first emissive mass in this lane, on a "
    "line fitted to rms 0.124 px over 65 columns. `part_stile_M` becomes the "
    "measured mullion PAIR, because its right edge is the occluding contour "
    "that hides the wardrobe's own left edge and the modelled member fell 16 "
    "px short of it. THE LIGHT IS NOT TOUCHED: predictions 1-4 in this file's "
    "docstring are written down before the render precisely so the light's "
    "next round has something it can fail against."
)

out = HERE / "spec_r34.json"
out.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out.name}")
print(f"  front plane y = {Y_FRONT}")
print(f"  x  {X_WARD_L:9.2f} .. {X_WARD_R:9.2f}   (width {X_WARD_R - X_WARD_L:.2f})")
print(f"  stile inner x = {X_STILE_IN:9.2f}  (stile {X_WARD_R - X_STILE_IN:.2f} wide)")
print(f"  mullion contour on this plane x = {X_MULL_CONTOUR:.2f} -> left edge "
      f"{X_WARD_L:.2f}, margin {X_MULL_CONTOUR - X_WARD_L:.1f} mm")
print(f"  strip x {X_STRIP_L:9.2f} .. {X_STRIP_R:9.2f}  (len "
      f"{X_STRIP_R - X_STRIP_L:.1f})   v={V_STRIP:.2f} -> z {Z_STRIP_MID:.1f}")
print(f"  niche clear height = {Z_STRIP_MID - STRIP_T / 2 - Z_SHELF_TOP:.1f} mm "
      f"(hung shirt 1100)")
print(f"  masses {len(spec['masses'])} (was 71)")
