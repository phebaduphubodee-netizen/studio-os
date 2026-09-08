#!/usr/bin/env python3
"""r36 item 1 — the pet cave's roof stops being a typed number.

  python training/TRN-002/_mk_r36.py

WHAT WAS WRONG. `petcave` is the largest mass in the lower third of the frame
and its height was 550 mm, typed at round 1 and never revisited in 35 rounds.
Its own provenance said so in plain words: `A(x, z, and all three sizes still
assumed - unchanged from r1)`. r35 finally measured the top ridge in the target
and found our roof projecting 80-96 px high. Gate #23 set this round's first
item: DECLARE the front plane against the measured mouth datum WITH BOUNDS,
DERIVE z from the measured line, and never type z.

THE MEASUREMENT, re-taken this round rather than inherited. Ten columns across
the top boundary of the pale mass in the lower right, sub-pixel edge where
luminance steps by more than 40 L (scan v 690..790):

    u    940     955     970     985    1000    1015    1030    1045    1060    1075
    v 755.410 738.863 730.931 727.732 725.525 722.755 720.781 718.892 717.383 715.709

A straight line through all ten fits to rms 4.97 px with a clean sign pattern
and an 11.9 px residual at u=940 — so THE TEN ARE NOT ONE EDGE. Restricted to
u>=985 the same line fits to **rms 0.401 px over 7 columns**. The three columns
to the left lie on a different, much steeper boundary (940->955 is -1.103 px/px
against -0.134 for the straight run) that breaks away at u~977.

WHOSE EDGE IS THE LEFT PART, and why it matters more than it looks. The record
has carried, since r29, a "boucle silhouette edge at u~950" cited as
CORROBORATION for this object's y. Three findings retire it:

  1. It was compared against the SHARP CORNER's projection (u=935) of a mass
     that has no sharp corner. The built oct's own leftmost silhouette is at
     u=970.46, so the rounding does not close a 15 px gap, it opens a 19 px one
     on the other side.
  2. If u~951 were this object's vertical arris, the object is IMPOSSIBLE, and
     scale-invariantly so: linking the arch's plane and the ridge's plane
     through that corner puts the arch's crown at 1.097x the roof height, and
     because moving an object along the camera rays scales crown and roof
     together, no distance and no size fixes it. (At the built oct's own
     silhouette the ratio is 0.998; at the sharp corner it is 1.18.)
  3. Built at every shell thickness in the whole legal bracket, this object
     covers only 5-6 of the ten columns and its left silhouette never goes left
     of u=989. The pale mass from 951 to ~990 is not the pet cave in ANY variant.

So the left columns are the neighbouring mass, and the `seen` field's "body
u 951..1080" was two objects read as one.

THE SOLVE — `trn002_geom.shell_closure`. Height and depth are one unknown from
one view (the same pixels give z 296 / 449 / 601 on three candidate planes).
What breaks the tie is that this object carries a SECOND measured feature on a
perpendicular plane — the arch, fitted at r29 over 76 back-projected points —
and the arch is a HOLE IN THIS OBJECT, so its crown is under this roof and its
jamb is inside this face. That makes the two ends of the range measurements:

    t = 0.0 mm   arch tangent to the far face, all material over the crown
                 -> far plane -5314.9, z_top 398.1
    t = 143.6    roof grazes the crown, all material beside the jamb
                 -> far plane -5171.4, z_top 349.5

DECLARED, and it is one sentence: THE SHELL IS THE SAME THICKNESS OVER THE
CROWN AS BESIDE THE JAMB. It solves to t = 36.3 mm — and that number is its own
R10 question-3 check, because a moulded boucle shell is a few tens of mm and a
solve returning 4 mm or 300 mm would have been telling us the model is wrong.

STILL DECLARED, so the output is not read as measured: the arch's own plane,
x=-2100, assumed since r1 and unchanged. The arch fit's RADIUS scales with it
(its SHAPE does not), and z_top moves -0.38 mm per +1 mm of that plane. The
object now hangs on exactly ONE declared scalar. It used to hang on two, and
the two disagreed by 53 mm — the roof was measured BELOW the crown of its own
mouth, and only the never-measured 550 hid it.

WHAT ELSE THE SAME SENTENCE FIXES, listed so it can be reversed as one thing:
  * depth in y  = 2*(radius + t): the mouth stays centred in y, which is r29's
    own derivation ("the cave hangs off the mouth"), so the far plane moving
    sets the depth.
  * width in x  = pocket depth + t: the back wall was 250 mm against a 36 mm
    shell. The pocket's 450 mm is itself DECLARED (nothing sees that far in),
    so the width inherits that gap and says so.
  * plan corner = bounded by the derivation to less than t. The flat face has
    to reach out to the arch's far jamb, and after the closure that jamb is only
    t from the object's edge. cut 250 -> t/2. This is a DERIVED CEILING on a
    declared number, not a measurement of it.

AND A SEPARATE DEFECT FOUND WHILE DOING IT. The pocket's `face` tuple — the
hole the surround strips are authored to fill — was typed as the mouth centre
+/- the CUT (250) where `oct_mesh` drops the quad at +/- (half-depth - cut)
(200). Both strips overhung the host by 50 mm and hung in air. `arch_pocket`'s
docstring promises the seam is "watertight by construction rather than by
tolerance", and the construction was reading a hand-typed field that no
generator ever emitted. It is now derived by `open_face_quad`, and
`pocket_face_violations` refuses the next one.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "pipeline", "scripts"))

import trn002_geom as G                                       # noqa: E402

SRC = os.path.join(HERE, "spec_r35.json")
DST = os.path.join(HERE, "spec_r36.json")

# --- measured this round: the top boundary of the lower-right pale mass -------
# (u, sub-pixel v) where luminance steps >40 L, scanning v 690..790.
RIDGE_PX = [(940, 755.410), (955, 738.863), (970, 730.931), (985, 727.732),
            (1000, 725.525), (1015, 722.755), (1030, 720.781), (1045, 718.892),
            (1060, 717.383), (1075, 715.709)]
RIDGE_FROM_U = 985.0      # left of this the boundary belongs to another mass


def main():
    with open(SRC, encoding="utf-8") as f:
        spec = json.load(f)
    cam, wh = spec["camera"], (spec["image"]["w"], spec["image"]["h"])
    by = {m["name"]: m for m in spec["masses"]}
    cave, mouth_mass = by.get("petcave"), by.get("petcave_mouth")
    if cave is None or mouth_mass is None:
        raise SystemExit("petcave / petcave_mouth not found in r35")
    if cave["s"][2] != 550:
        raise SystemExit(f"petcave height is {cave['s'][2]}, not the typed 550 "
                         f"— r36 has already been run, or the object moved")
    pocket = mouth_mass["pocket"]

    # the ridge line, and the two fits that show why the left columns are cut
    m_all, b_all, rms_all = G.fit_line_uv(RIDGE_PX)
    ridge_pts = [p for p in RIDGE_PX if p[0] >= RIDGE_FROM_U]
    m, b, rms = G.fit_line_uv(ridge_pts)
    if rms > 1.0:
        raise SystemExit(f"the adopted ridge does not fit a line (rms {rms:.3f} px)")
    # back-project points ON the fit, not the raw edges: the line is the
    # measurement, the individual pixels are its samples.
    ridge_uv = [(u, m * u + b) for u, _ in ridge_pts]

    sol = G.shell_closure(cam, wh, pocket, ridge_uv)
    t, z_top = sol["t_mm"], sol["z_top_mm"]
    if sol["closure_residual_mm"] > 1e-6:
        raise SystemExit(f"closure did not close: {sol['closure_residual_mm']} mm")

    x_face = cave["c"][0] - cave["s"][0] / 2.0            # -2100, declared, unchanged
    width = float(pocket["depth_mm"]) + t                 # back wall == the shell
    depth = 2.0 * (float(pocket["radius_mm"]) + t)        # mouth centred in y
    cut = t / 2.0                                         # ceiling is t (see below)
    if cut >= sol["max_plan_cut_mm"]:
        raise SystemExit("plan corner would eat the material holding the far jamb")

    cave["c"] = [x_face + width / 2.0, float(pocket["y_centre_mm"]), z_top / 2.0]
    cave["s"] = [width, depth, z_top]
    cave["cut"] = cut
    lo, hi = sol["bound_z_mm"]
    cave["prov"] = (
        f"D(z_top {z_top:.2f} DERIVED, never typed: the measured ridge line "
        f"v = {m:.5f}u + {b:.3f} (rms {rms:.3f} px, {len(ridge_pts)} columns "
        f"u>={RIDGE_FROM_U:.0f}) back-projected onto the far plane, which is the "
        f"MEASURED arch datum y={pocket['y_centre_mm']} + R {pocket['radius_mm']} "
        f"+ shell {t:.2f}. Height and depth are ONE unknown from one view (z "
        f"296/449/601 on three candidate planes); what brackets it is that the "
        f"arch is a hole IN this object, so its crown is under this roof and its "
        f"jamb inside this face: z_top is BOUNDED by measurement to "
        f"[{lo:.1f}, {hi:.1f}] mm. The typed 550 was {550 - hi:.0f} mm outside "
        f"that bound. Roof and crown+shell agree to "
        f"{sol['closure_residual_mm']:.0e} mm) "
        f"/ DECLARED(one sentence picks the point inside the bracket: the shell "
        f"is the same thickness over the crown as beside the jamb -> t={t:.2f} mm, "
        f"a plausible moulded boucle shell, which is the solve checking itself. "
        f"The same sentence sets depth 2(R+t)={depth:.1f} with the mouth centred "
        f"in y per r29, width = pocket depth + t = {width:.1f}, and CAPS the plan "
        f"corner below t — the flat face must still reach the far jamb, so cut "
        f"250 -> {cut:.2f}) "
        f"/ A(x face {x_face:.0f}, unchanged from r1 and now this object's ONLY "
        f"declared scalar; the arch fit's radius scales with it, its shape does "
        f"not, and z_top moves -0.38 mm per +1 mm of it. r35 had TWO independent "
        f"declared planes and they disagreed by 53 mm: the roof measured below "
        f"the crown of its own mouth) "
        f"/ RETIRED(r29's CORROBORATED clause, the boucle silhouette at u~950. "
        f"It compared the SHARP corner u=935 of a mass whose built silhouette is "
        f"u=970.46; a rigid object with a vertical arris there needs crown/roof "
        f"= 1.097, which is scale-invariant and so unfixable by any distance; and "
        f"this object at every shell in the bracket covers only 5-6 of the ten "
        f"measured columns and never reaches left of u=989)")
    cave["seen"] = (
        f"YES, and NARROWER than the record claimed. The arch mouth is the "
        f"frame's darkest region at u 1004-1079, v 754-820 (4,284 px, Ylin "
        f"0.0003) and its left jamb holds u=1004.00 sd 0.00 over 34 rows. The "
        f"top ridge reads u 985-1075, v 727.7-715.7, straight to {rms:.3f} px. "
        f"Both run off the right and bottom frame edges. NOT THIS OBJECT: the "
        f"pale mass at u 951-990 and the steep boundary breaking away at u~977 "
        f"— the previous `seen` said 'body u 951..1080' and that was two objects "
        f"read as one, which is what let a 550 mm height look supported.")
    cave["audit"] = "FIX"

    pocket["face"] = list(G.open_face_quad(cave["c"], cave["s"], cave["cut"]))
    mouth_mass["prov"] = (
        f"{mouth_mass['prov']} / r36: the surround's `face` is now DERIVED by "
        f"`open_face_quad` from the host it names, not typed. The typed tuple "
        f"was the mouth centre +/- the CUT (250) where `oct_mesh` drops the quad "
        f"at +/- (half-depth - cut) (200), so both strips overhung the host by "
        f"50 mm and hung in air — a seam whose docstring promises it is "
        f"watertight by construction while one side of it was hand-typed into "
        f"the JSON with no generator behind it. `pocket_face_violations` now "
        f"refuses the next one.")

    bad = G.pocket_face_violations(spec)
    if bad:
        raise SystemExit("pocket/host seam still disagrees:\n  " + "\n  ".join(bad))

    spec["declared_gaps"]["petcave_height"] = (
        f"BOUNDED, not free: measurement alone puts the roof in "
        f"[{lo:.1f}, {hi:.1f}] mm and one declared sentence (uniform shell) picks "
        f"{z_top:.2f}. What stays unmeasurable is the object's DISTANCE — one view "
        f"cannot separate size from range, so the whole solve rides on the arch's "
        f"declared plane x={x_face:.0f} at -0.38 mm of height per mm of plane.")
    spec["declared_gaps"]["petcave_depth"] = (
        f"UNMEASURABLE from this view: the object runs off the bottom and right "
        f"frame edges, so it has no visible floor contact and no far end. Depth "
        f"{depth:.1f} follows from the declared uniform shell plus r29's "
        f"mouth-centred derivation, not from a pixel.")
    spec["declared_gaps"]["petcave_class"] = (
        "OPEN, and named rather than modelled away: six blind critics have each "
        "bound this object to something different, and R8 puts a free-form shell "
        "in ACQUIRE, not in a hand-built prism. What r36 settles is its SIZE, "
        "which is answerable from its own arch; what it does not settle is "
        "whether a flat-topped rounded box is the right class at all.")

    spec["round"] = 36
    spec["renamed"] = {}
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)

    print(f"r36 item 1 — petcave roof DERIVED, not typed")
    print(f"  ridge  all 10 columns: rms {rms_all:.3f} px  ->  NOT one edge")
    print(f"         u>={RIDGE_FROM_U:.0f} ({len(ridge_pts)} cols): rms {rms:.3f} px  <- adopted")
    print(f"  shell  t = {t:.2f} mm     far plane y = {sol['y_far_mm']:.1f}")
    print(f"  roof   z_top = {z_top:.2f} mm   was 550 (typed r1, never measured)")
    print(f"         bound [{lo:.1f}, {hi:.1f}] mm; 550 sits {550 - hi:.0f} mm outside it")
    print(f"  mass   c={[round(v, 2) for v in cave['c']]} "
          f"s={[round(v, 2) for v in cave['s']]} cut={cut:.2f}")
    print(f"  seam   face derived {[round(v, 2) for v in pocket['face']]} "
          f"(was [-5714.8, -5214.8, 550.0], overhanging 50 mm each side)")


if __name__ == "__main__":
    main()
