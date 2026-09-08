#!/usr/bin/env python3
"""r35 — delete the lamp that was never there, build the cone that is.

  python training/TRN-002/_mk_r35.py

WHAT THIS ROUND DOES, and it is one thing: `lamp` was a 220 x 220 x 640.7 mm
black mass standing on the nightstand, and the reference shows LIT OAK WALL in
that volume (L 136-145 across v 510-570, brighter than the oak beside it at
108-127; the known-black bird reads L 61). Its own provenance justified the body
as "OCCLUDED by the bird sculpture and book stack" — the bird is at v 600-630
and the books below it, i.e. under most of the span they were said to hide.

What is really there is a black conical shade, and the reference measures it
well: the left flank fits u = -0.84893v + 1488.422 to **rms 0.170 px over 24
rows**. That the line DRIFTS is what identifies it — under this lane's yaw-only
camera a cylinder or an arris holds its u at every height, so a steady slant is
a cone flank. Rim closes at v 507; apex at v 483, u 1078.4, hard on the frame
edge.

THE ONE THING THAT CANNOT BE MEASURED, and therefore is not typed: depth. One
view cannot separate a shade's distance from its size. It is DECLARED against a
named datum — the nightstand's own measured centre plane, x = -1465 — and the
declaration is cheap because the bound is tight:

    x = -1640 : height 82.4, radius 84.4, apex z 1066.6
    x = -1465 : height 87.4, radius 89.6, apex z 1051.9      <- declared
    x = -1290 : height 92.5, radius 94.8, apex z 1037.3

Over the nightstand's full half-depth the object moves by about 6%. And the
apex back-projects to y = -4949.1 against the nightstand's centre at -4950,
which is a 1 mm agreement between two quantities solved from different inputs.

Sanity, R10 question 3: the rim lands at z 965, which is 484 mm above the
nightstand top at 481 — the ordinary height of a bedside pendant.

WHAT IS DECLARED, NOT MEASURED, AND SAYS SO IN ITS OWN prov:
  * `pendant_cord` — no suspension is VISIBLE above the apex (u 1068-1080,
    v 400-478 is uniform wall, min L 130-135). That is not evidence of absence:
    the shade's 179 mm diameter spans 40.7 px, so 4.4 mm/px, and a 3 mm cord is
    0.68 px — SUB-PIXEL, and a JPEG would erase it. Something must hold the
    shade up, and a cord is the smallest thing that can. The honest alternative,
    recorded here rather than hidden: this could equally be a wall-mounted
    swing-arm whose arm is entirely off-frame to the right. Unresolved.
  * `nightstand` y-width — LEFT UNTOUCHED ON PURPOSE. The spec says 700 mm and
    its own prov records a 426 mm arris, and this round measured why they
    disagree: the left end does NOT hold its u (sigma 3.26 px over 45 rows), so
    it is an occluding contour, not the slab's end. The right end is clipped by
    the frame. NEITHER END IS MEASURABLE, so neither number is a measurement and
    replacing 700 with 426 would swap one typed number for another.

REFUSED THIS ROUND: the bird. R8 forbids hand-modelling animals, so it is
ACQUIRE or a declared gap, never a modelling task.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "spec_r34.json")
DST = os.path.join(HERE, "spec_r35.json")

# --- measured, from the reference ---------------------------------------------
FIT_M, FIT_B = -0.84893, 1488.422   # left flank, rms 0.170 px, 24 rows
APEX_UV = (1078.39, 483.0)
RIM_UV = (1058.01, 507.0)
X_DATUM = -1465.0                   # DECLARED: the nightstand's own centre plane

# --- solved on that one plane, all three axes (r34's law: one object, one plane)
APEX = (-1465.0, -4949.1, 1051.9)
RIM_Z = 964.5
RADIUS = 89.6
HEIGHT = APEX[2] - RIM_Z            # 87.4

CEIL_Z = 3152.0 - 100.0 / 2.0       # ceil_main's underside
CORD_D = 3.0


def main():
    with open(SRC, encoding="utf-8") as f:
        spec = json.load(f)

    masses = [m for m in spec["masses"] if m["name"] != "lamp"]
    if len(masses) == len(spec["masses"]):
        raise SystemExit("`lamp` not found in r34 — has this already been run?")

    masses.append({
        "name": "pendant_shade",
        "kind": "cone",
        "seg": 24,
        "c": [APEX[0], APEX[1], (APEX[2] + RIM_Z) / 2.0],
        "s": [RADIUS * 2, RADIUS * 2, HEIGHT],
        "value": 0.05,
        "seen": "u1058-1080, v483-508 — the black conical silhouette, apex at "
                "the top, clipped by the frame's right edge",
        "prov": (f"M-px left flank u = {FIT_M}v + {FIT_B}, rms 0.170 px over 24 "
                 f"rows v483-506 (it DRIFTS, so a cone: a cylinder or an arris "
                 f"holds u under a yaw-only camera); apex {APEX_UV}, rim closes "
                 f"v{RIM_UV[1]:.0f}. All three axes solved on ONE plane "
                 f"/ DECLARED(depth x={X_DATUM}, the nightstand's measured "
                 f"centre plane — one view cannot separate a shade's distance "
                 f"from its size; bound +-175 mm moves height/radius by 6%)"),
        "why": ("the bedside shade. It REPLACES `lamp`, which stood a 640.7 mm "
                "black body on the nightstand in a volume the reference shows "
                "as lit oak wall (L 136-145 vs 108-127 beside it; the black "
                "bird reads 61). Its rim lands 484 mm above the nightstand top, "
                "the ordinary height for a bedside pendant"),
    })

    masses.append({
        "name": "pendant_cord",
        "c": [APEX[0], APEX[1], (CEIL_Z + APEX[2]) / 2.0],
        "s": [CORD_D, CORD_D, CEIL_Z - APEX[2]],
        "value": 0.05,
        "seen": (f"NOT VISIBLE: the reference cannot resolve it either way. At "
                 f"4.4 mm/px (the shade's 179 mm spans 40.7 px) a {CORD_D} mm "
                 f"cord is 0.68 px, and JPEG erases a sub-pixel line. Checked "
                 f"anyway: u1068-1080 v400-478 is uniform wall, min L 130-135, "
                 f"no dark line — which is what a 0.68 px cord LOOKS like, so "
                 f"it is not evidence of absence"),
        "prov": (f"DECLARED, not measured, and it cannot be either way: no "
                 f"suspension is visible above the apex (u1068-1080 v400-478 is "
                 f"uniform wall, min L 130-135) but at 4.4 mm/px a {CORD_D} mm "
                 f"cord is 0.68 px and a JPEG erases it. Runs from ceil_main's "
                 f"underside z={CEIL_Z} to the measured apex z={APEX[2]}"),
        "why": ("the shade's support. Something must hold it up and a cord is "
                "the smallest thing that can — the minimum invention, the same "
                "tiebreak r34 used on the plinth. UNRESOLVED ALTERNATIVE, "
                "recorded rather than hidden: a wall-mounted swing arm entirely "
                "off-frame to the right fits every measurement equally well. "
                "This is NOT the `lamp_stem` shape: that post was contradicted "
                "by pixels showing empty wall, this one is below the "
                "reference's resolution in both directions"),
    })

    # --- the headboard contradicts its OWN recorded pixel ----------------------
    # `seen` records the near end's outer silhouette at u=1027.62 (re-measured
    # this round: u 1027.5 on every row v525-625, so it HOLDS and is an arris,
    # agreeing to 0.56 px). `prov` then back-projected it onto the FRONT face
    # plane x=-1490. AN OUTER SILHOUETTE IS THE OUTERMOST CORNER, which for this
    # box is the BACK face x=-1314 — so the built panel's silhouette lands at
    # u=1066.95, 39.3 px right of the pixel it was measured from, and the panel
    # runs 189.9 mm long. That surplus is what buries the oak wall band: at
    # (1040,560) four masses stack and the nearest is this one, so the target's
    # oak (152,125,97) renders as our upholstery (173,167,157).
    #
    # This is TRN-001's rounded-mass SILHOUETTE trap in its flat form — there, a
    # curved end's outline sits at y=-(d-r) rather than on the face plane. Same
    # error, no curvature required: A SILHOUETTE IS NEVER ON THE NEAR FACE.
    #
    # CROSS-CHECK, and it does not fully close: `seen` also notes an inner
    # vertical at u~1008 which it read as piping. If that is instead the
    # front-face/end arris — i.e. the end face is visible between the two — it
    # solves to y=-4650.1 against this fix's -4555.1, agreeing to 95 mm. The
    # inner reading is "~1008" by eye, never sub-pixel fitted, so the 95 mm is
    # carried as OPEN rather than averaged away. Fit it in r36 before trusting
    # this end to better than 100 mm.
    Y_NEAR = -4555.1
    for m in masses:
        if m["name"] == "bed_headboard":
            y0, y1 = m["c"][1] - m["s"][1] / 2, m["c"][1] + m["s"][1] / 2
            assert abs(y0 - (-4745.0)) < 1.0, f"near end moved: {y0}"
            m["s"][1] = y1 - Y_NEAR
            m["c"][1] = (Y_NEAR + y1) / 2
            m["prov"] = (f"M-px outer silhouette u=1027.62 (holds u on every row "
                         f"v525-625, so an ARRIS) assigned to the OUTERMOST "
                         f"CORNER x=-1314, not the front face — r35 correction, "
                         f"the panel was 189.9 mm long and buried the oak band. "
                         f"OPEN: the inner vertical u~1008 read as the front/end "
                         f"arris gives -4650.1, a 95 mm disagreement, unfitted. "
                         f"| r34 and earlier: ") + (m.get("prov") or "")
            break
    else:
        raise SystemExit("bed_headboard not found")

    spec["round"] = 35
    spec["masses"] = masses
    spec["renamed"] = {"lamp": ["pendant_shade", "pendant_cord"]}
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    print(f"r35: {len(masses)} masses (r34 had 79); "
          f"`lamp` deleted, pendant_shade + pendant_cord added")
    print(f"  shade  c={masses[-2]['c']} s={masses[-2]['s']}")
    print(f"  cord   c={masses[-1]['c']} s={masses[-1]['s']}")


if __name__ == "__main__":
    main()
