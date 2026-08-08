"""spec_r30 -> spec_r31.

TWO OBJECTS THIS REPO ALREADY HAD EVERY NUMBER FOR, AND NEITHER HAS EVER BEEN IN
A FRAME. Both were found by the r30 orphan-row ratchet — a four-line check for
PALETTE rows no mass wears — and neither needed a single new measurement.

------------------------------------------------------------- THE BLIND ------
`blind_slat` has: a mesh generator (`G.slat_stack`) whose docstring carries the
MEASUREMENTS (pitch 6.50 px between 89 peaks in the target's own column,
constant up the whole band, back-projecting to 29.4 mm on the wall plane;
extent y -2630..-910, z 730..2550, confirmed independently at the near edge
u=50 -> y -2631, 1 mm, and at the top v=125 -> z 2582 against 2550); a builder
path (`_slats`); a palette row with provenance; THREE tests in
test_trn002_geom; and an area light in trn002_light whose own comment says its
job is "to light ITS OWN SLATS ... and until r25 there were no slats."

ACROSS ALL THIRTY SPECS THERE HAS NEVER BEEN A `blind` MASS.

And the light settles where it goes without any new work: `BLIND_left_wall` sits
at (-4735, -1770, 1640) with size (1720, 1820), which IS the blind's measured
extent — the emitter was built from it. So the mass is that centre, that span,
and the chord the generator already defaults to. It stands 15 mm proud of the
left wall's inner face at x=-4750, which is exactly the 15 mm gap that light's
provenance records it firing into for every round of this lane.

-------------------------------------------------------- THE CHAIR -----------
`leg_dark`'s row says it is "the target's chair legs ... the darkest furniture
element in the frame after the TV." `chair_leg_1..4` exist in exactly ONE spec —
r12 — and their provenance reads:

    "audit 2026-08-05 (sighted local critic, R10b): M(three feet backprojected
     on z=0, twice across rounds 2 and 3)"

and the seat's:

    "seat underside measured 297.5 (was a solid block to the floor); centre
     moved to the foot centroid ~-720"

So a sighted audit MEASURED the feet, measured the seat's underside, split a
solid block into legs plus a seat, and moved the assembly 265 mm. Then r14
carries the r11 numbers again — solid block z 0..450, y -455, no legs — and so
does every spec after it, through r30.

**THE CORRECTION WAS NOT ARGUED WITH. IT WAS DROPPED.** r14 was generated from
r11's numbers rather than r12's, and nothing compares a spec to the one before
it, so eighteen rounds of gates reported a chair that had already been measured
and fixed. This is the class CLAUDE.md records as recurring six times — "a
design decision must never be revertible by an OMISSION" — and this is the
seventh. It is also why the orphan ratchet is worth more than the two objects
it found: `leg_dark` sat unworn for eighteen rounds and was the only trace left.

r31 restores r12's measured chair verbatim. Nothing here is re-derived, because
re-deriving it would replace a measurement with a fresh guess at the same thing.
"""
import io
import json
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "spec_r30.json")
R12 = os.path.join(HERE, "spec_r12.json")
DST = os.path.join(HERE, "spec_r31.json")

# BLIND_left_wall's loc/size ARE the blind's measured extent — see module docstring.
BLIND_C = [-4735.0, -1770.0, 1640.0]
BLIND_S = [34.0, 1720.0, 1820.0]
BLIND_PROV = (
    "M(pitch: 6.50 px between 89 peaks in the target's own column, constant up "
    "the whole band, backprojecting to 29.4 mm on the wall plane) / "
    "M(extent y -2630..-910, z 730..2550; near edge confirmed at u=50 -> "
    "y=-2631, 1 mm, top at v=125 -> z 2582 against 2550) / "
    "A(BOTTOM inherited, not re-measured — the periodic column runs on past the "
    "blind into the console below it) / "
    "DECLARED(chord 34 mm and tilt 25 deg: ~6.5 px per slat cannot resolve "
    "either, and they are chosen so chord*cos(tilt) sits just under the pitch, "
    "which is the one thing the pixels do say — the blind reads nearly closed) / "
    "NEVER BUILT UNTIL r31: generator, builder, palette row, three tests and an "
    "area light aimed at it all existed; the mass did not.")


def main():
    spec = json.load(io.open(SRC, encoding="utf-8"))
    r12 = {m["name"]: m for m in json.load(io.open(R12, encoding="utf-8"))["masses"]}
    spec["round"] = "r31"
    masses = spec["masses"]
    by = {m["name"]: m for m in masses}

    if "blind" in by:
        raise SystemExit("blind already present — r31 has been run")
    masses.append({
        "name": "blind", "kind": "slats", "value": 0.62,
        "c": list(BLIND_C), "s": list(BLIND_S), "prov": BLIND_PROV,
        "seen": ("the venetian blind on the left wall, visible beside and "
                 "behind the TV as a bright-bar / dark-gap band. It stands 15 mm "
                 "proud of the wall's inner face at x=-4750 — the same 15 mm gap "
                 "BLIND_left_wall's provenance records it firing into."),
    })

    # ---- restore r12's MEASURED chair, verbatim ----------------------------
    restored = []
    for name in ("chair_seat", "chair_back"):
        old, new = by[name], r12[name]
        if old["c"] == new["c"] and old["s"] == new["s"]:
            continue
        old["c"], old["s"] = list(new["c"]), list(new["s"])
        old["prov"] = new.get("prov", old.get("prov", "")) + (
            " -- RESTORED at r31. This measurement existed in spec_r12 and "
            "spec_r12 ONLY: r14 carries r11's numbers again and so does every "
            "spec through r30. It was never argued with, it was dropped, and "
            "eighteen rounds of gates reported a chair that had already been "
            "measured and fixed.")
        restored.append(name)
    legs = [n for n in r12 if n.startswith("chair_leg")]
    if not legs:
        raise SystemExit("spec_r12 has no chair legs — check the source")
    for n in sorted(legs):
        if n in by:
            continue
        m = json.loads(json.dumps(r12[n]))
        m["prov"] = m.get("prov", "") + (
            " -- RESTORED at r31; present in spec_r12 alone, absent r14..r30. "
            "`leg_dark` sat as an unworn PALETTE row for eighteen rounds and was "
            "the only trace left that this had ever been measured.")
        masses.append(m)
        restored.append(n)

    spec["STATUS"] = (
        "r31 = r30 plus two objects the repo already had every number for and "
        "had never put in a frame: the venetian blind (generator, builder, "
        "palette row, three tests and an area light aimed at it — no mass, in "
        "thirty specs) and the chair's measured legs and seat, which a sighted "
        "audit fixed in spec_r12 and r14 silently reverted. Both were found by "
        "the orphan-row ratchet, and neither needed a new measurement.")

    io.open(DST, "w", encoding="utf-8").write(
        json.dumps(spec, ensure_ascii=False, indent=1))
    print("wrote", DST)
    print(f"  blind  c={BLIND_C} s={BLIND_S}")
    print(f"  chair restored: {', '.join(restored)}")


if __name__ == "__main__":
    main()
