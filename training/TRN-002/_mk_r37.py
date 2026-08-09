#!/usr/bin/env python3
"""r37 — gate-23 items 2, 3 and 4. One is deleted, one is derived, one is refused.

  python training/TRN-002/_mk_r37.py

Ordered under the owner's build law (dimension -> objects complete -> light), and
under R10: before a frame is judged, every mass answers what it is, whether the
reference shows it, and whether it could be built.

ITEM 2 — `desk_pier` LEAVES THE FRAME. Its own `seen` field has said "NOT FOUND
at its built location" since r34, and the answer did not change when r35 moved
it 1.3 m: re-tested this round at the CURRENT position, the strongest luminance
step anywhere along its foot line (u 115..146, v 655..705) is **16-21 L**, and
it does not even sit at the foot line. Every real boundary measured in this same
frame this round runs **40-93 L** (the headboard arris 55-70, the wood block at
u=80 +93). So the floor contact this object claims is not in the picture at any
strength. R10's rule then applies literally: an object invented to satisfy a
structure is a declared assumption, and the absent thing is honest where the
wrong thing fabricates a reading. It becomes a DECLARED GAP, not a smaller pier
and not material absorbed into a neighbour.

ITEM 3b — `bed_headboard` HEIGHT, DERIVED, NEVER TYPED. The panel's top arris in
the target fits

    v = 0.121770 u + 395.663      rms 0.102 px over 48 columns, u 770..1010

The camera sits at z=1305 and this top is near z=900, so the camera is ABOVE the
top face and the UPPER silhouette can only be the top-BACK arris — that is
geometry, not a reading. The back plane is x=-1314, which is a CONTACT (the
front of `ward_band`, gap 0.0 mm, r34), so it is the one datum here that is not
in question. Back-projecting the fitted line onto it gives

    z_top = 882.95 mm   (sd 0.95 over the 48 columns)   built 915  ->  -32.1 mm

which agrees with gate-23's independent per-column estimate of ~30-33 mm.

ITEM 3b(ii) — THE DEPTH IS MEASURED AND IS *NOT* APPLIED HERE, ON PURPOSE.
A second line runs 3.05-3.32 px below the arris (rms 0.348 px over 44 columns),
and the panel's near end shows the same pair standing up: outer silhouette
u = -0.00245v + 1028.504 (rms 0.174 px, 26 rows -- which reproduces r35's
1027.62) and an inner arris u = -0.01571v + 1016.073 (rms 0.440 px). Read as the
two arrises of one narrow top/end face they give a depth of **92.7 mm** from the
end pair and **101.2 mm** from the top pair. The end pair is **6.8x more
sensitive per mm** (0.216 px/mm against 0.032), so it carries, and the top pair
corroborates to within 0.25 px of its own noise. The built **176 mm has no
measurement anywhere in its provenance**.

It is still not applied, and the reason is R9. `bed_platform`'s head-end face is
at x=-1490, which is exactly this panel's front face: they are IN CONTACT. Hold
the back at the wall and a 92.7 mm panel opens an **83.3 mm gap** between bed and
headboard; hold the front at the bed and the panel leaves the wall. **The number
is measured; which contact survives is a RELATIONSHIP that nobody has declared**,
and typing either coordinate is the defect R9 names. Carried to r38 as a contact
question, with the measurement already in hand.

ITEM 3a — `bench` DEPTH: REFUSED, AND THE REFUSAL IS A MEASUREMENT. 600 mm has
been an `A` since r1 and gate-23 booked it for this round. It cannot be closed
from this view and here is the number: of 59 columns across the mass, only 12
carry a rise of 60 L or more, and a straight line through them fits to
**rms 11.56 px** -- two orders worse than every fit this lane has accepted
(0.10-0.44 px). There is no arris there to measure, because a woven throw is
draped over the whole visible top. Solving the depth from that "line" returns
25.5 mm for an ottoman, which is what a derivation from a non-line returns.
So the depth stays declared, the far-ridge-proud defect stays open, and it is
booked to the lane that builds the throw -- the thing occluding the datum is an
object we have not built yet.

ITEM 4 — `seg`. `craft_check` has named these two every round since r34 and this
is the first round where the spec can answer: `bed_platform` R=300 at 5.37 m and
`bench` R=200 at 3.49 m each need 8 segments per quarter and carry 6.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "spec_r36.json")
DST = os.path.join(HERE, "spec_r37.json")

Z_TOP_HEADBOARD = 882.95          # DERIVED, see the module docstring
X_BACK_HEADBOARD = -1314.0        # the contact that made the derivation possible


def main():
    with open(SRC, encoding="utf-8") as f:
        spec = json.load(f)
    by = {m["name"]: m for m in spec["masses"] if "name" in m}

    # ---- item 2: the pier leaves -------------------------------------------------
    pier = by.get("desk_pier")
    if pier is None:
        raise SystemExit("desk_pier is already gone — r37 has been run")
    spec["masses"] = [m for m in spec["masses"] if m.get("name") != "desk_pier"]
    spec.setdefault("declared_gaps", {})["desk_pier"] = (
        "REMOVED at r37, not resized: whatever carries the far end of the 2995 mm "
        "worktop is NOT IN THIS PICTURE. Re-tested at the position r35 corrected it to "
        "(the earlier test was at a location 1.3 m away, so it could have been the "
        "location and not the object): the strongest luminance step anywhere along its "
        "foot line, u 115..146 scanning v 655..705, is 16-21 L and does not even fall at "
        "the foot line - against 40-93 L for every real boundary measured in this same "
        "frame this round (headboard arris 55-70, the wood block at u=80 +93). R10 then "
        "applies literally: an object invented to satisfy a structure is a declared "
        "assumption, and the absent thing is honest where the wrong thing fabricates a "
        "reading. REOPEN only on a datum for the console end panel's bottom, or an "
        "elevation from the owner - do NOT re-add a pier to hold the desk up.")

    # ---- item 3b: the headboard's roof stops being 915 ---------------------------
    hb = by["bed_headboard"]
    if hb["s"][2] != 915:
        raise SystemExit(f"headboard height is {hb['s'][2]}, not 915 — already run?")
    x_back = hb["c"][0] + hb["s"][0] / 2.0
    if abs(x_back - X_BACK_HEADBOARD) > 1e-6:
        raise SystemExit(f"the back face is at {x_back}, not the contact plane "
                         f"{X_BACK_HEADBOARD} the derivation stands on")
    hb["s"][2] = Z_TOP_HEADBOARD
    hb["c"][2] = Z_TOP_HEADBOARD / 2.0          # it stands on the floor: z 0..z_top
    hb["prov"] = (
        "D(z_top 882.95 DERIVED, never typed: top arris fitted v = 0.121770u + 395.663, "
        "rms 0.102 px over 48 columns u770-1010, back-projected onto the BACK plane "
        "x=-1314 - which is a contact, the front of ward_band at gap 0.0 mm. The upper "
        "silhouette can only be the top-BACK arris because the camera at z=1305 is above "
        "this top: that is geometry, not a reading. sd 0.95 mm across the 48 columns. "
        "The typed 915 was 32.1 mm high, and gate-23's per-column estimate of 30-33 mm "
        "was independent of this fit.) | "
        "OPEN r38 - DEPTH IS MEASURED BUT NOT APPLIED: the second line 3.05-3.32 px below "
        "the arris (rms 0.348 px, 44 columns) and the near end's arris pair (outer "
        "u=-0.00245v+1028.504 rms 0.174 px / inner u=-0.01571v+1016.073 rms 0.440 px, "
        "26 rows) give depth 101.2 and 92.7 mm; the end pair is 6.8x more sensitive per "
        "mm so it carries. Built 176 has no measurement in its provenance. NOT APPLIED "
        "because bed_platform's head face is at x=-1490 = this panel's front face: they "
        "are in contact, and a 92.7 panel held at the wall opens an 83.3 mm gap. Which "
        "contact survives is a RELATIONSHIP nobody has declared (R9). | "
        + hb["prov"])

    # ---- item 4: the segments craft_check has asked for since r34 -----------------
    for name in ("bed_platform", "bench"):
        m = by[name]
        if m.get("kind") != "oct":
            raise SystemExit(f"{name} is not an oct — seg would do nothing")
        m["seg"] = 8

    # ---- item 3a: the refusal is recorded as a measurement, not as a silence ------
    bench = by["bench"]
    bench["prov"] = (
        "A(depth 600 UNMEASURABLE from this view and REFUSED at r37 rather than typed: of "
        "59 columns across the mass only 12 carry a >=60 L rise and a straight line "
        "through them fits to rms 11.56 px, two orders worse than every fit this lane "
        "accepts (0.10-0.44 px). A woven throw is draped over the whole visible top, so "
        "the top arris is not an image feature; solving depth from that non-line returns "
        "25.5 mm. The far-top ridge standing ~55 px proud at u=860 (gate-23) is REAL and "
        "stays open - it is booked to the lane that builds the throw, because the object "
        "occluding the datum is one we have not built.) | " + bench["prov"])
    # The gate caught the first cut of this edit and it was right: writing the refusal
    # into `prov` while leaving 600 sitting in `s` is exactly the shape R10's corollary
    # names. This object is NOT invented — the ottoman is plainly in the target — so it
    # does not belong in `declared_gaps`; what is assumed is one of its DIMENSIONS, and
    # that has to be declared in the open, with its cost and its reversal.
    bench["why"] = (
        "DECLARED, not measured. The ottoman is really there (pale mass under a woven "
        "throw, u 653..950) but its depth in y has no datum in this view and no second "
        "feature to break the depth/height coupling the way the arch broke petcave's at "
        "r36. 600 mm is HELD at its r1 value rather than re-typed, so the number cannot "
        "drift while it is undetermined. WHAT IT COSTS, stated rather than hidden: at 600 "
        "the far-top ridge stands ~55 px proud of the target at u=860 (gate-23), so this "
        "declaration is known to be wrong in the direction of TOO DEEP. REVERSE BY: build "
        "the throw in the soft-goods lane, then re-fit the top boundary — the object "
        "occluding the datum is one we have not built yet.")

    spec["round"] = 37
    # DERIVED from `round`, not patched. The first cut read
    # `spec["id"].replace("r36", "r37")`, which found no "r36" and did nothing — r35, r36
    # and this file all carried `id = "TRN-002 r34"`, so three rounds of spec were labelled
    # with a fourth round's name and the "fix" was a silent no-op that read like a fix.
    # r34's and r35's files are frozen records and stay as they are; from here the label
    # cannot drift from the number it describes.
    spec["id"] = f"TRN-002 r{spec['round']}"
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    print(f"wrote {DST}")
    print(f"  desk_pier      REMOVED -> declared gap ({len(spec['declared_gaps'])} total)")
    print(f"  bed_headboard  z_top 915 -> {Z_TOP_HEADBOARD} (c_z {hb['c'][2]})")
    print(f"  bed_platform   seg -> 8      bench seg -> 8")
    print(f"  bench          depth 600 re-declared UNMEASURABLE with its failed fit")
    print(f"  masses {len(spec['masses'])} (was {len(spec['masses'])+1})")


if __name__ == "__main__":
    main()
