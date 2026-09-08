"""spec_r28 -> spec_r29 (+ the two TV bracket legs).

THE DARKS. The target holds 1.914% of its pixels below Ylin 0.02; ours holds
0.007% — 270x — and at the 1st percentile the target sits at 0.0039 against our
0.0491, i.e. OUR DARKEST 1% IS 12.6x BRIGHTER THAN THEIRS. That is not a mood
difference, it is the frame's whole value structure, and the owner graded every
version F while it was true.

Where the missing black actually is, measured by connected component and then
identified by eye against the reference (top regions, Ylin<0.06, ours on the
SAME pixels):

    10,135 px  u1-91    v309-622  the TV wall           tgt 0.021  ours 0.249
     6,308 px  u148-402 v228-633  the glass partition   tgt 0.038  ours 0.258
     4,264 px  u1003-79 v754-820  the PET CAVE MOUTH    tgt 0.0003 ours 0.233
     1,368 px  u807-986 v727-756  under the bed base    tgt 0.016  ours 0.499

This round takes the two whose mechanism is PROVEN rather than guessed.

--------------------------------------------------------------------- ONE ----
THE TV IS 7.6x TOO BRIGHT AND ITS ALBEDO IS NOT THE LEVER. Our TV renders at
Ylin p50 0.281 over 8,989 px against the target's 0.037. The camera sits 86.3
degrees off that panel's normal — computed from the solved camera and the mass's
own +x face — and a dielectric at 86.3 degrees returns Fresnel R = 0.689
WHATEVER ITS BASE COLOUR IS. `screen_black`'s 0.040 albedo contributes about
0.02 of the 0.281; the rest is the room, mirrored.

This is why four rounds of wattage bracketing (r23-r26) could not have touched
it: the panel is showing a REFLECTION, and a reflection scales with the thing
reflected, so brightening or dimming the room moves the TV and the wall
together. It is also why the material pass never caught it — every value in
PALETTE was measured by the trn001 ratio method, which divides a lit pixel by a
reference surface under the same light. That method has a DIFFUSE model inside
it. Pointed at a grazing specular surface it returns a number that is not an
albedo and cannot be made into one.

THE BRACKET THEN REFUTED THE SECOND HALF OF THAT REASONING, and the refutation
is kept because it is worth more than the fix. This file first said "roughness
is not the lever — it widens the lobe, it does not reduce grazing reflectance",
and brackets legs a/b were built to test the dielectric lobe alone. Measured, at
quick price, as p50 over the TV's own pixels against the target's 0.0409:

    r28 control        IOR 1.45  r 0.12   0.2756   6.75x
    leg b   level 0.15 IOR 1.45  r 0.12   0.2512   6.15x   the knob cannot reach
    leg a              IOR 1.00  r 0.12   0.0129   0.32x   overshoots, and lies
    leg c              IOR 1.45  r 0.45   0.1221   2.99x
    leg d              IOR 1.45  r 0.90   0.0409   1.00x   <- ships

Leg b is the whole argument: Blender takes a Schlick form, F = F0 + (1-F0)
(1-cos0)^5, and at 86.3 degrees (1-cos0)^5 = 0.716, so F0 is worth 2% of the
answer. Cutting the specular level to 0.15 moved the pixel 9%. And the claim
about roughness was wrong because it confused two quantities: total reflectance
at 86 degrees is pinned near 0.72 by geometry and nothing moves it, but what
lands in the frame is the RADIANCE from the mirror direction, and a rough lobe
replaces one bright wall with the average of a hemisphere. IOR 1.0 stays a
bracket end and never a shipped value — it is a physical lie that happens to
land nearby.

-------------------------------------------------------------------- TWO ----
THE TARGET'S BLACK IS A PLACE, NOT A SURFACE. Its blackest region, 4,284 px at
Ylin 0.0003, is the mouth of the pet cave. No albedo in this room reaches that:
the darkest row in PALETTE is 0.040 and it renders at 0.035-0.070, which is
arithmetic, not tuning. A cavity is geometry, and NOT ONE INSTRUMENT IN THIS
LANE CAN ASK WHETHER THE FRAME CONTAINS ANYWHERE LIGHT DOES NOT GO — every one
of them measures a per-surface photometric ratio.

The mouth is measured, and well. Its top edge back-projects (on the cave's -x
face plane) to a circle: centre (y -5464.8, z 199.6), R 149.9 mm, residual rms
2.77 mm over 76 points, and a straight line fits 9.7x worse — so it is an arc,
not a chamfer. Its left springing point is confirmed a SECOND and independent
way: the black region's left boundary holds u=1004.00 with sd 0.00 over 34
rows, which on this plane is a constant y, and that y lands on the circle's own
left extreme to 0.6 mm.

AND THE MOUTH RELOCATES THE CAVE. Centred on the assumed body, the measured
mouth would sit 15 mm from the cave's far edge, which no cat cave does. The
petcave carries prov A in every dimension ("identity open") and the mouth is now
M, so the derivation runs the right way round: the cave hangs off its mouth.
y -5750 -> -5464.8. INDEPENDENTLY CORROBORATED: the target's own boucle
silhouette edge sits at u~950 over v730-760; the old position projects that
corner to u=1000.6 (50 px away), the mouth-derived one to u=935 — 15 px, and
inside the error of an oct's rounded corner, which pulls a silhouette in.

WHAT IS STILL ASSUMED, LOUDLY: the arc's RADIUS SCALES WITH THE PLANE it was
back-projected onto, and that plane is the cave's assumed -x face. The SHAPE (an
arc, not a line) survives any choice of plane; the SIZE does not. The pocket's
DEPTH is a declaration outright — nothing in this frame sees far enough into the
cave to measure it.

------------------------------------------------------- AND IT WAS BUILT WRONG
The cavity's first build drew it 2 mm PROUD of the cave's face instead of THROUGH
it, on the theory that a sub-pixel offset would read the same. The host is
SOLID, so a ray entering the mouth travelled 2 mm and hit the face behind it:
450 mm of cavity rendered as a 2 mm groove. The number that names it is worth
keeping — swapping the lining's albedo 0.863 -> 0.020, a factor of 40, moved the
region by 1% (p50 0.348 -> 0.344). A SURFACE THAT DOES NOT RESPOND TO ITS OWN
MATERIAL IS NOT BEING RENDERED, and that test costs nothing to run whenever a
new object lands in a frame.
Fixed the way this pipeline already required and I had read past: the host drops
its own -x quad (`open_face`) and the cavity authors the face back AROUND its
opening — openings are authored quad face loops, never booleans
(pipeline/CLAUDE.md). Rebuilt: the mouth region goes from 0.0% of its pixels
below Ylin 0.02 to 79.3%, against the target's 85.1%.

AND THE WHITE-LINER TEST SURVIVED THE BUG, which is the only reason it is worth
anything: it was re-run on the fixed geometry before the value was believed.
"""
import io
import json
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "spec_r28.json")

# ---- the measured mouth, on the cave's -x face plane ------------------------
MOUTH_Y = -5464.8       # circle centre, 76-point fit, rms 2.77 mm
MOUTH_Z = 199.6         # springing
MOUTH_R = 149.9         # half-width == rise; left extreme confirmed to 0.6 mm
FACE_X = -2100.0        # the cave's assumed -x face — the radius scales with it
DEPTH = 450.0           # DECLARED: unseeable from this camera

PROV_MOUTH = (
    "M(top edge fitted over 76 back-projected points as a circle on x=-2100: "
    "centre y=-5464.8 z=199.6, R=149.9, residual rms 2.77 mm, max 6.17; a LINE "
    "fits 9.7x worse, so it is an arc. Left springing confirmed independently: "
    "the black region's left boundary holds u=1004.00 sd 0.00 over 34 rows = a "
    "constant y on this plane, landing on the circle's own left extreme to 0.6 "
    "mm) / A(the RADIUS scales with the back-projection plane, which is the "
    "petcave's ASSUMED -x face; the arc SHAPE does not) / DECLARED(depth 450 mm "
    "and the 2 mm proud offset — no boolean is available, openings are authored "
    "face loops in this pipeline and a geometry bpy.ops dies headless)")

PROV_CAVE = (
    "D(y from its own MOUTH: the measured arch centres at y=-5464.8, and on the "
    "old assumed body that mouth would sit 15 mm from the cave's far edge. The "
    "mass was prov A in every dimension and the mouth is M, so the cave hangs "
    "off the mouth, not the other way round. was -5750.) / CORROBORATED(the "
    "target's boucle silhouette edge reads u~950 over v730-760; the old y "
    "projects that corner to u=1000.6 = 50 px out, the derived y to u=935 = 15 "
    "px, inside the error of an oct's rounded corner) / A(x, z, and all three "
    "sizes still assumed — unchanged from r1)")

# ---- the TV bracket ---------------------------------------------------------
# LOUD end first, then read where the target falls between the legs — this
# lane's own amplitude-bisect law. Leg A removes the dielectric lobe outright
# (IOR 1.0); leg B keeps it at 30% of default. The target's TV is not dead flat
# (p99/p50 = 12.4, "two broad soft bands"), so the answer is expected between
# them and the bracket is built to say WHERE, not to be right first try.
TV_LEGS = {
    "a": {"screen_black": [1.0, 0.0]},
    "b": {"screen_black": [1.45, 0.15]},
}


def main():
    spec = json.load(io.open(SRC, encoding="utf-8"))
    spec["round"] = "r29"

    by = {m["name"]: m for m in spec["masses"]}
    cave = by["petcave"]
    cave["c"][1] = MOUTH_Y
    cave["prov"] = PROV_CAVE

    if "petcave_mouth" in by:
        raise SystemExit("petcave_mouth already present — r29 has been run")
    spec["masses"].append({
        "name": "petcave_mouth",
        "kind": "pocket",
        "value": 0.62,
        "prov": PROV_MOUTH,
        "pocket": {
            "face_x_mm": FACE_X, "y_centre_mm": MOUTH_Y,
            "spring_z_mm": MOUTH_Z, "radius_mm": MOUTH_R,
            "base_z_mm": 0.0, "depth_mm": DEPTH, "proud_mm": 2.0,
        },
        "seen": ("u 1004-1079, v 754-820 in the target = 4,284 px at Ylin "
                 "0.0003, the darkest region in the frame. Ours renders 0.233 "
                 "there. The mouth is 60% off-frame to the right; what is "
                 "measured is its left jamb, its crown, and the arc between."),
    })

    # R10: the object justifies itself before it is built.
    spec.setdefault("declared_gaps", {})["petcave_mouth_depth"] = (
        "450 mm, declared. Nothing in this frame sees into the cave far enough "
        "to measure how deep it is; what the depth controls is how black the "
        "cavity renders, so it is bracketable against the target's 0.0003 "
        "rather than guessable.")

    dst = os.path.join(HERE, "spec_r29.json")
    io.open(dst, "w", encoding="utf-8").write(
        json.dumps(spec, ensure_ascii=False, indent=1))
    print("wrote", dst)

    for leg, fres in TV_LEGS.items():
        s = json.loads(json.dumps(spec))
        s["round"] = f"r29{leg}"
        s["fresnel"] = fres
        p = os.path.join(HERE, f"spec_r29{leg}.json")
        io.open(p, "w", encoding="utf-8").write(
            json.dumps(s, ensure_ascii=False, indent=1))
        print("wrote", p, fres)


if __name__ == "__main__":
    main()
