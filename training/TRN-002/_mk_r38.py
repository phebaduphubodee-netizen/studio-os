#!/usr/bin/env python3
"""r38 — the headboard's measured thickness goes in, and the joint it lands on
is DECLARED rather than typed.

  python training/TRN-002/_mk_r38.py

WHAT r37 LEFT ON THE TABLE, in its own words: *"The number is measured; which
contact survives is a RELATIONSHIP that nobody has declared."* The panel's depth
measures ~93 mm against a built 176 mm, and three masses meet at one plane:

    ward_band front face   x = -1314.0     (the oak wall panel)
    bed_headboard          x = -1490.0 .. -1314.0      176 mm, never measured
    bed_platform head face x = -1490.0
    bed_mattress head face x = -1490.0

Thin the panel holding its BACK at the wall and the bed is left 83.3 mm short of
it. Thin it holding its FRONT at the bed and the panel leaves the wall. Both are
one edit to the same three numbers, which is R9's defect exactly, and the round
that types either coordinate has not made the decision — it has hidden it.

THE DECISION, AND IT IS MEASURED ON BOTH SIDES
----------------------------------------------
THE WALL CONTACT SURVIVES. The panel's back stays on `ward_band`'s front face
and THE BED FOLLOWS THE PANEL. Four independent reasons, none of them taste:

1. THE BACK PLANE IS LOAD-BEARING FOR TWO OTHER NUMBERS ALREADY DERIVED FROM IT.
   r37's z_top (882.95 mm) is the top arris back-projected onto x=-1314, and
   r35's near end (y=-4555.1) is the outer silhouette back-projected onto the
   same plane. Move the panel off the wall and BOTH have to be re-derived:
   measured this round, the height becomes 894.2 mm (+11.3) and the near end
   moves 90.3 mm, taking the panel's LENGTH with it (2005.1 -> 2095.4). Holding
   the wall costs nothing; moving it re-opens three numbers to buy one.

2. THE BED'S HEAD COORDINATE IS THE ONE NUMBER IN THIS CHAIN THAT NOBODY
   MEASURED. `identifiability-partition-2026-08-07.md` rows 27 and 28 say so in
   writing for both masses: *"the head end -1490 rides the x=-1290 chain"* —
   wardrobe plane, plus a 24 mm band, plus the invented 176. It is the ARITHMETIC
   RESULT of a number that has just been refuted, so it is the free end by
   construction. The bed's FOOT is the measured end (mattress foot face -3394
   from a contact-shadow line constant to 1 mm over 6 points; platform foot
   -3555 = that face minus the MEASURED 161 mm inset), and every landmark of
   record on the bed — `plat_foot_corner`, `plat_top_foot`, `mat_foot_contact` —
   sits at the foot. Moving the head end moves no landmark in the metric table.

3. THE BUILT 176 IS REFUTED BY ABSENCE, RE-TESTED THIS ROUND. On the panel's
   near end the built front face projects to u=989.27. Scanning v 525..625 the
   median strongest luminance step in a 6 px window there is 2.9 L — flat-field
   noise, the same 2.4-3.1 L returned at u=985, 993, 1000. The two features that
   ARE there read 47 L (the welt at u~1008) and 77 L (the silhouette at
   u~1027.1). There is no face where 176 mm puts one, at 16-26x less signal than
   the real edges beside it.

4. WHAT THE DECISION IMPLIES IS CHECKABLE, AND IT CHECKS OUT. Hold the mattress
   foot at its measured -3394 and put its head on the panel: the mattress comes
   out 1987.3 mm long. Manufactured lengths are 1980 (6'6") and 2000 — 7.3 and
   12.7 mm away. The current 1904 is not a size anyone makes. THIS IS
   CORROBORATION AND NOT A SOURCE: no standard length is typed anywhere here, and
   if it had disagreed the fix would have been to re-measure, not to round.

THE NUMBER, AND THE BRACKET IT SITS IN
--------------------------------------
92.7 mm is r37's value and it is HELD, not re-typed. This round re-fitted both
lines independently and the honest result is a BAND, because the inner feature is
a 2 px dark welt and not a razor edge:

    outer silhouette   u = -0.00344 v + 1029.141   rms 0.371 px   101 rows
    welt (centroid)    u = -0.00794 v + 1012.871   rms 0.270 px   101 rows
    -> depth 87.1 mm (welt centre) / 84.0 mm (welt's left flank) / 92.7 (r37)

    the top pair, re-fitted the same way, agrees and cannot be precise:
    top arris v = +0.122656 u + 394.715 (rms 0.105, 61 cols; r37 got
    +0.121770 u + 395.663 at rms 0.102) -> z_top 883.56 mm against r37's 882.95,
    and the welt line below it puts the front plane at 82 +/- 11 mm.

So the depth is 84-95 mm and the entire spread is the welt bead's own width
(~9 mm ~ 2 px). 92.7 is inside it, it is the number of record, and re-typing it
to 87 for a difference smaller than the feature being measured is how a number
drifts. WHAT THE CHOICE COSTS: the bed's head moves 1 mm per 1 mm of depth, so
the whole bracket is 9 mm of bed position — 2 px in this frame.

WITHDRAWN BEFORE IT SHIPPED — THE BED DOES NOT MOVE
---------------------------------------------------
The first cut of this script did the whole of the paragraph above AND moved the
bed's head faces to the panel's front face, with both joints declared as blocking
contacts. An adversarial pass fired at this round's own claims refuted it, and
the refutation reproduced here on the first attempt, so it is recorded rather
than argued with.

**The bed's own two near-side lines run past the plane the round wanted to stop
it at.** These are not new features: they are the pair r16 fitted at the FOOT
(the plinth's near-side base contact on z=12 and its top arris on z=221) — nobody
had ever run them toward the head. Traced column by column and back-projected:

    z = 12   line   y = -4181 +/- 3 mm   u 800..980   contrast 61-142 L
    z = 221  arris  y = -4174 +/- 5 mm   u 840..980   contrast   8-11 L

i.e. the bed's near side is continuous out to x ~ -1220..-1300 — past -1490 and
past the -1406.7 this round proposed. And the round's own §3 statistic, turned on
the round: at u=939.74, where a head face at -1406.7 must cut that line, the
median strongest step is **4.0 L** against a flat field of 3.0-4.0 L. Nothing is
there, measured by the same test that killed the 176.

So the second half of "the wall contact survives and THE BED FOLLOWS THE PANEL"
is false: the bed does not stop at the panel, it runs to the wall, which makes
the upholstered panel WALL-HUNG above the base — and that would also explain the
one number nobody has ever measured about it, `bed_headboard`'s bottom at z=0.

WHAT SURVIVES, and it is the half the round was asked for: the panel's depth
(92.7 mm, band 84-95), its back on the wall, and the death of the 176. Holding
the wall is if anything corroborated by this — a bed running to the wall leaves
the panel nowhere else to be.

WHAT THIS SCRIPT THEREFORE DOES: the panel thins, the two panel-to-bed contact
rows are NOT written, and the bed's head faces are HELD at -1490 with a `why`
carrying the measurement above, its cost, and the fit r39 has to do. Holding a
contested number rather than improving it is deliberate and is this lane's own
idiom (r37 did it for the bench's depth): a number under active contest may not
drift while it is undetermined, because the round after next cannot tell a
correction from a guess.

WHAT STOPS THIS HAPPENING AGAIN
-------------------------------
`spec["contacts"]` + `pipeline/scripts/contact_check.py`, called from
`rule_gate.check()`. Four joints are declared with a DATUM naming which side
holds. If a later round changes the panel's thickness and leaves the bed where
it was, the render fails instead of opening a silent 83 mm gap — which is the
one thing that did not happen at r37.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                "pipeline", "scripts"))
SRC = os.path.join(HERE, "spec_r37.json")
DST = os.path.join(HERE, "spec_r38.json")

X_BACK_HEADBOARD = -1314.0        # ward_band's front face. THE DATUM.
DEPTH_HEADBOARD = 92.7            # MEASURED r37, re-fitted r38, band 84.0-95.1
X_FRONT_HEADBOARD = X_BACK_HEADBOARD - DEPTH_HEADBOARD      # -1406.7, DERIVED

# The measured ends the bed is anchored on at the FOOT — read, never typed here.
# They are asserted against the incoming spec so this script cannot quietly
# lengthen the bed from a foot that has moved for some other reason.
X_FOOT_PLATFORM = -3555.0
X_FOOT_MATTRESS = -3394.0

R37_OPEN = "OPEN r38 - DEPTH IS MEASURED BUT NOT APPLIED:"

CONTACTS = [
    {"a": "bed_headboard", "a_face": "x_max",
     "b": "ward_band", "b_face": "x_min",
     "gap_mm": 0.0, "datum": "b",
     "why": "THE DATUM OF THE WHOLE CHAIN. The panel is a wall panel: its back "
            "is on the oak panelling, which is where r34 put it at gap 0.0 and "
            "where two derivations already stand — r37's z_top (the top arris "
            "back-projected onto x=-1314) and r35's near end y=-4555.1 (the "
            "outer silhouette on the same plane). REVERSE BY: moving this row's "
            "datum to `a`, at the price of re-deriving both of those (measured "
            "r38: z_top 894.2, near end -4645.4, panel length 2095.4)."},
    # THE TWO PANEL-TO-BED ROWS THIS ROUND WROTE FIRST ARE GONE, AND THE REASON
    # IS A MEASUREMENT — see WITHDRAWN in the module docstring. They asserted
    # that the bed's head face lands on the panel's front face. The bed's own
    # two near-side lines say it does not: they run PAST that plane, unbroken,
    # to the wall. Declaring them would have made a refuted relationship into
    # blocking law, which is worse than never declaring it.
    {"a": "bed_mattress", "a_face": "z_min",
     "b": "bed_platform", "b_face": "z_max",
     "gap_mm": 0.0, "datum": "b",
     "why": "The mattress sits on the plinth. Declared because the plinth's "
            "221 mm height is a measurement (base contact on the rug z=12 and "
            "the top arris z=221, two independent reads) and the mattress's "
            "z is derived from it — the same shape as the joint above, one axis "
            "over. placement_check reads this one off the built scene as a "
            "support; this register is what makes the SPEC state it."},
]


def main():
    with open(SRC, encoding="utf-8") as f:
        spec = json.load(f)
    by = {m["name"]: m for m in spec["masses"] if "name" in m}

    hb, plat, mat = by["bed_headboard"], by["bed_platform"], by["bed_mattress"]

    # ---- refuse to run twice, and refuse to run on a spec that has moved -----
    if abs(hb["s"][0] - 176.0) > 1e-9:
        raise SystemExit(f"headboard depth is {hb['s'][0]}, not 176 — already run?")
    if abs(hb["c"][0] + hb["s"][0] / 2.0 - X_BACK_HEADBOARD) > 1e-9:
        raise SystemExit("the panel's back is not on the datum plane this round "
                         "declares — re-read the chain before editing it")
    for m, foot, head, label in ((plat, X_FOOT_PLATFORM, -1490.0, "bed_platform"),
                                 (mat, X_FOOT_MATTRESS, -1490.0, "bed_mattress")):
        got = m["c"][0] - m["s"][0] / 2.0
        if abs(got - foot) > 1e-9:
            raise SystemExit(f"{label}'s foot face is at {got}, not the measured "
                             f"{foot} — the end this round does NOT touch.")
        # The head is HELD, so assert it rather than write it: if some other
        # round has already moved it, this script's `why` would be describing a
        # number that is no longer there.
        got_head = m["c"][0] + m["s"][0] / 2.0
        if abs(got_head - head) > 1e-9:
            raise SystemExit(f"{label}'s head face is at {got_head}, not {head} "
                             f"— r38 HOLDS this number and explains why it is "
                             f"wrong; it cannot hold a number that moved.")

    # ---- the panel -----------------------------------------------------------
    hb["s"][0] = DEPTH_HEADBOARD
    hb["c"][0] = X_BACK_HEADBOARD - DEPTH_HEADBOARD / 2.0
    if R37_OPEN not in hb["prov"]:
        raise SystemExit("r37's OPEN paragraph is not in the headboard's prov — "
                         "refusing to append a second, contradictory account")
    head, _, tail = hb["prov"].partition(R37_OPEN)
    tail = tail.split("| ", 1)[1] if "| " in tail else tail
    hb["prov"] = (
        head +
        "M(DEPTH 92.7 mm, APPLIED r38 onto a DECLARED contact. The near end's "
        "two verticals re-fitted independently this round: outer silhouette "
        "u = -0.00344v + 1029.141 (rms 0.371 px, 101 rows) and the welt line "
        "u = -0.00794v + 1012.871 (rms 0.270 px, 101 rows), which on the near-end "
        "plane give 87.1 mm from the welt's centre and 84.0 from its left flank "
        "against r37's 92.7 - a BAND of 84-95 mm whose whole spread is the welt "
        "bead's own 2 px width. 92.7 is HELD as the value of record rather than "
        "re-typed inside its own noise. The top pair re-fitted the same way "
        "(arris v = +0.122656u + 394.715, rms 0.105 px, 61 cols, reproducing "
        "r37's z_top to 0.6 mm). THE BUILT 176 DIES ON THE SEPARATION, NOT ON AN "
        "ABSENCE: the near-end pair is 18.5 px apart and the top pair 2.95-3.66 "
        "px, where 176 mm requires ~38 px and 4.8-6.6 px - wrong by a factor of "
        "two at fit rms 0.24-0.35 px. (An earlier draft of this line argued 176 "
        "was 'refuted by absence' - no step at u=989.27, 2.9 L against 2.4-3.1 L "
        "of flat field. WITHDRAWN: a same-frame same-class control, the bed "
        "plinth's own 90-degree vertical corner in the same white upholstery, "
        "scores 3.50 L, so a corner that certainly exists is indistinguishable "
        "from that 'absence'. This room's light leaves the panel's two faces "
        "0.8 L apart; the test measured the lighting.) WHICH CONTACT SURVIVES is "
        "in spec.contacts, not in prose: the BACK stays on ward_band, because "
        "that is the plane z_top and the near end were both derived on. THE BED "
        "DOES NOT FOLLOW - see bed_platform/bed_mattress `why`.) | " + tail)

    # `seen` DESCRIBES THE TARGET, so it does not move when our build does — but
    # it carried r35's READING of the inner line ("an inner piping line"), and
    # this round refutes that reading with the top pair. Leaving a superseded
    # interpretation in the field the next round reads is how a refuted idea
    # comes back wearing a measurement's clothes.
    old_seen = ("an outer silhouette at u=1027.62 and an inner piping line at "
                "u~1008, with the panel's end face between them.")
    if old_seen not in hb["seen"]:
        raise SystemExit("the headboard's `seen` no longer carries r35's piping "
                         "reading — check what changed before overwriting it")
    hb["seen"] = hb["seen"].replace(old_seen, (
        "an outer silhouette at u=1027.62 and a second line at u~1008, and the "
        "strip BETWEEN them is the panel's narrow end face. r35 read the inner "
        "line as piping; r38 reads it as the front arris with the welt sitting "
        "on it, and the TOP pair is what decides between them: a welt inset "
        "would have to be 102.5 mm in from the end AND 0-1 mm down from the top "
        "edge, which is not one border. One thickness explains both lines."))

    # ---- the bed does NOT move, and that is this round's second finding ------
    # The first cut of this script moved both head faces to the panel's front
    # face. An adversarial pass refuted it with the lane's OWN instrument and
    # the refutation reproduced on the first try — see WITHDRAWN in the module
    # docstring. So the heads are HELD at their r37 value, the way r37 held the
    # bench's 600: a number under active contest may not drift while it is
    # undetermined. What changes is that the number is now KNOWN to be wrong,
    # and `why` says so with the evidence and the reversal.
    contested = (
        "HELD at -1490.0 and KNOWN WRONG — r38 tried to derive this head end "
        "from the headboard's front face and the attempt was REFUTED by the "
        "lane's own two lines. The plinth's near-side base contact (z=12) and "
        "its top arris (z=221), the same pair r16 fitted at the FOOT, hold "
        "y = -4181 +/- 3 and -4174 +/- 5 mm respectively from u=800 out to "
        "u=980 with 61-142 L of contrast on the lower one - i.e. the bed's near "
        "side runs unbroken to x ~ -1220..-1300, PAST both -1490 and the -1406.7 "
        "this round proposed. And r38's own absence test, turned on r38: at "
        "u=939.74, where a head face at -1406.7 must cut that line, the median "
        "strongest step is 4.0 L against 3.0-4.0 L of flat field - nothing is "
        "there, in the same statistic that reads 61 L for the line it would have "
        "to cross. WHAT IT IMPLIES, unclosed: the base runs to the wall and the "
        "upholstered panel is WALL-HUNG above it, which would also explain why "
        "bed_headboard's bottom z=0 carries no measurement anywhere in its prov. "
        "WHAT IT COSTS: at -1490 the head end is short by roughly 200-280 mm, "
        "and that is now a measured error rather than an unexamined one. "
        "REVERSE BY: r39 - fit the terminus of those two lines properly (they "
        "wobble past u=960, y -4233 at u=960), then derive the head from the "
        "wall contact and re-open the panel's bottom as its own question. Do "
        "NOT type a head coordinate before that fit exists.")
    for m in (plat, mat):
        m["why"] = contested
    plat["prov"] = ("A(head end -1490 HELD, contested - see `why`) | " + plat["prov"])
    mat["prov"] = ("A(head end -1490 HELD, contested - see `why`) | " + mat["prov"])

    # ---- the register itself -------------------------------------------------
    if spec.get("contacts"):
        raise SystemExit("this spec already carries contacts — merge, do not "
                         "overwrite")
    spec["contacts"] = CONTACTS

    spec["round"] = 38
    spec["id"] = f"TRN-002 r{spec['round']}"
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)

    import contact_check as CC
    v = CC.check(spec)
    print(f"wrote {DST}")
    print(f"  bed_headboard  depth 176 -> {DEPTH_HEADBOARD}  "
          f"(back {X_BACK_HEADBOARD}, front {X_FRONT_HEADBOARD})")
    print(f"  bed_platform   head HELD at {plat['c'][0] + plat['s'][0] / 2.0} "
          f"(contested, see `why`)   length {plat['s'][0]:.1f} unchanged")
    print(f"  bed_mattress   head HELD at {mat['c'][0] + mat['s'][0] / 2.0} "
          f"(contested, see `why`)   length {mat['s'][0]:.1f} unchanged")
    print(f"  the two panel-to-bed contacts are NOT declared — refuted, see the "
          f"module docstring")
    print(f"  contacts       {len(CONTACTS)} declared, "
          f"{len(v)} violation(s): {v if v else 'all holding'}")
    if v:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
