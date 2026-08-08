"""spec_r29 -> spec_r30.

THE PARTITION HAS NO OPENING. For thirty rounds this lane has drawn a frame —
head, two jambs, a mullion, a bottom rail, all prov M, all landing inside 0.2 px
of their measured landmarks — ON A SOLID WALL. The id mask says it plainly:
**53.4% of the partition zone (u140-410, v215-650) is `back_wall`.** The two
"opaque white slabs" that every critic and every gate has read as glass panels
are the bedroom's back wall, seen through a doorway that was never cut.

That zone is ~103,000 px, 11.4% of the frame, and in the target it is an entire
second room: a glass sliding leaf with a chair behind it, an oak-lined niche
with a warm strip and a shirt on a hanger, a white door with a black lever, and
parquet running through. Ours is a blank.

WHY IT SURVIVED THIRTY ROUNDS, and it is not that nobody looked. Every
instrument this lane owns compares OUR value at a place to the TARGET's value at
the same place, and answers in a currency the material lane can spend. A wall
where a room should be is not a value error — it is a MISSING OPENING — so the
ladder reported the zone as "too bright and too flat", which is true, and which
sends the next round to the palette. The C2 and C3 critics both filed items
about the partition reading as frosted or blank panels; both were triaged
towards material. The frame's own numbers were never wrong: the members are
measured, and a measured frame on a solid wall projects exactly like a measured
frame on an opening.

THE OPENING NEEDS NO NEW MEASUREMENT AND NO NEW GEOMETRY CODE. It is already
implied by four masses that were each measured separately, and it is their
INNER faces:

    jamb_L  x -4292..-4228        ->  clear x -4228
    jamb_R  x -2689..-2625        ->  clear x -2689
    rail_B  z     0..60           ->  clear z    60
    head    z  2372..2479         ->  clear z  2372

    CLEAR OPENING  1,539 x 2,312 mm, projecting to u 157.9-390.0, v 243.7-598.2

So `back_wall` — one 4,750 mm slab spanning the whole room — becomes three
boxes that stop at the frame it was hiding: a pier each side and a head over the
top. No boolean, no new mesh generator, no face-loop authoring. The wall was
never one object; it was one object because nobody had needed it to be two.

AND THE QUICK RUNG THEN SAID WHAT TO DO NEXT, which is why it ran before any of
it was decided. With the hole open, the room behind it is a dark grey void:
through the opening the target reads 0.586 where ours reads 0.109 (5.4x) on the
far wall and 0.483 against 0.050 (9.7x) on the white door, while the closet
FLOOR is already right (0.193 vs 0.230). A floor lit and walls unlit is a
missing emitter, not a missing material — the dressing room has its own light
and this lane never had a reason to notice, because until this round there was
nothing behind that frame at all.

So r30 also adds:

  * CLOSET_daylight — one broad soft area source (trn002_light.CLOSET). The
    target's dressing room is BRIGHTER than the bedroom: its far wall beats our
    lit bedroom wall at 0.48, which is a daylight signature, not a downlight,
    and through the left leaf the target shows sheers and a window. Position,
    size and colour are DECLARED; only the POWER is measured, bracketed against
    the closet back wall's own pixels.

  * closet_oak — the wardrobe niche. Measured in the image and DECLARED in
    depth, and the round is explicit about which is which. Its extent comes
    from the target's own hue: B/R drops from 0.79 to 0.24-0.59 across
    u 295-365 and holds down to v~572, against a neutral 0.78-0.81 on the door
    beside it, so the niche's PIXELS are measured to about a pixel. Its DEPTH
    is not, and cannot be from this camera: the panel's floor contact is
    occluded by the partition's own bottom rail (rail top v 585.8-590.9, and
    the oak's warm run continues past it into the bedroom's parquet, which is
    warm too — the first read of this boundary conflated the two and put the
    panel's foot at y=-1900, in front of the partition and 1.9 m the wrong side
    of the wall it hangs on). A HUE METRIC CANNOT SEPARATE TWO WARM THINGS, and
    the tell was that the answer was geometrically impossible, not that the
    metric looked noisy.
    So it is sized to project onto the measured box at a declared depth on the
    closet's back wall, and the declaration is the whole of the claim.

  * closet_floor / closet_back extended in x. At depth the opening's own view
    cone reaches x -2116, and both stopped at -2258, so the far right of the
    opening looked into empty space. Derived from the cone, not chosen.

WHAT IT STILL DOES NOT DO: no glass leaf, no LED strip in the niche, no shirt,
no door lever. The white door needs no object of its own — it is white paint on
a lit white wall and reads at the target's value once the light is right; its
lever and frame line are a declared gap. The shirt is free-form and belongs to
ACQUIRE (R8), never to a modelling round.
"""
import io
import json
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "spec_r29.json")
DST = os.path.join(HERE, "spec_r30.json")

PROV = (
    "D(the opening's edges are the INNER faces of four separately-measured "
    "frame members — jamb_L -4228, jamb_R -2689, rail_B top 60, head underside "
    "2372 — so nothing here is newly measured and nothing is typed. This piece "
    "is `back_wall` stopped at the frame it used to run behind.) / "
    "M(inherited: back_wall's own extents and its y 0..200, unchanged)")


def main():
    spec = json.load(io.open(SRC, encoding="utf-8"))
    spec["round"] = "r30"
    masses = spec["masses"]
    i = next(k for k, m in enumerate(masses) if m["name"] == "back_wall")
    bw = masses[i]
    if bw["s"][0] < 4000:
        raise SystemExit("back_wall is already split — r30 has been run")

    x0, x1 = bw["c"][0] - bw["s"][0] / 2, bw["c"][0] + bw["s"][0] / 2
    z0, z1 = bw["c"][2] - bw["s"][2] / 2, bw["c"][2] + bw["s"][2] / 2
    y, ty = bw["c"][1], bw["s"][1]
    # the frame members' OUTER faces — where the wall may still stand
    JL, JR = -4292.0, -2625.0
    HEAD_TOP = 2479.0

    def piece(name, xa, xb, za, zb, note):
        return {"name": name, "value": bw["value"],
                "c": [(xa + xb) / 2, y, (za + zb) / 2],
                "s": [xb - xa, ty, zb - za],
                "prov": PROV + " — " + note,
                "seen": bw.get("seen", "")}

    new = [
        piece("back_wall_L", x0, JL, z0, z1,
              "the pier between the room's left wall and the partition's L jamb"),
        piece("back_wall_R", JR, x1, z0, z1,
              "the pier from the partition's R jamb to the room corner; this is "
              "the piece that carries the PALETTE's reference-surface "
              "measurement (back wall -y face, n=65,014 px) — the measurement "
              "was of pixels, and those pixels are all in this piece"),
        piece("back_wall_head", JL, JR, HEAD_TOP, z1,
              "the head over the opening, from the frame head's top to the "
              "ceiling"),
    ]
    for p in new:
        if p["s"][0] <= 0 or p["s"][2] <= 0:
            raise SystemExit(f"{p['name']} has non-positive extent: {p['s']}")
    masses[i:i + 1] = new

    # ---- the room behind the hole -----------------------------------------
    by = {m["name"]: m for m in masses}
    CONE_X = -2050.0            # the opening's own view cone at closet depth
    for nm in ("closet_floor", "closet_back"):
        m = by[nm]
        x_lo = m["c"][0] - m["s"][0] / 2
        if m["c"][0] + m["s"][0] / 2 < CONE_X:
            m["s"][0] = CONE_X - x_lo
            m["c"][0] = (x_lo + CONE_X) / 2
            m["prov"] = (m.get("prov", "A") +
                         " / D(x extended to -2050: at closet depth the "
                         "opening's own view cone reaches x -2116, and this "
                         "mass stopped at -2258, so the far right of the "
                         "opening looked into empty space. Derived from the "
                         "cone, not chosen.)")

    OAK = dict(x0=-2996.5, x1=-2374.1, z0=0.0, z1=2008.0, y1=2390.0, thick=60.0)
    masses.append({
        "name": "closet_oak", "kind": "box", "value": 0.42,
        "c": [(OAK["x0"] + OAK["x1"]) / 2, OAK["y1"] - OAK["thick"] / 2,
              (OAK["z0"] + OAK["z1"]) / 2],
        "s": [OAK["x1"] - OAK["x0"], OAK["thick"], OAK["z1"] - OAK["z0"]],
        "prov": (
            "M(EXTENT IN THE IMAGE, to about a pixel: the target's B/R drops "
            "from 0.79 to 0.24-0.59 across u 295-365 and holds down to v~572, "
            "against a neutral 0.78-0.81 on the door beside it) / "
            "DECLARED(DEPTH — the panel's floor contact is OCCLUDED by the "
            "partition's own bottom rail, so this camera cannot measure how far "
            "back it is. It is placed on the closet's back wall and sized to "
            "project onto the measured box; every world number here follows "
            "from that declaration, not from a measurement.) / "
            "REFUTED-FIRST-READ(taking the warm run's own end at v=657 as the "
            "floor contact put this panel at y=-1900 — in front of the "
            "partition, 1.9 m the wrong side of the wall it hangs on. A HUE "
            "METRIC CANNOT SEPARATE TWO WARM THINGS, and the bedroom's parquet "
            "below the opening is warm too. What caught it was that the answer "
            "was impossible, not that the metric looked noisy.)"),
        "seen": ("u 295-365, v 327-572 in the target: an oak-lined wardrobe "
                 "niche about 2.0 m tall, with a warm strip at its head, a "
                 "shirt on a hanger and a shelf below. Only the LINING is built "
                 "this round — the strip, the shirt and the shelf are not."),
    })
    spec.setdefault("declared_gaps", {}).update({
        "closet_oak_depth": (
            "The niche's depth is unmeasurable from this camera — its floor "
            "contact is behind the partition's bottom rail. Placed on the "
            "closet back wall by declaration; the projected extent is measured "
            "and is what the frame is judged on."),
        "closet_niche_contents": (
            "The target's niche carries a warm LED strip at its head, a shirt "
            "on a wooden hanger, a shelf with a small box and a pair of "
            "glasses. None is built. The shirt is free-form and belongs to "
            "ACQUIRE (R8), never to a modelling round."),
        "partition_glass": (
            "The left leaf is glazed in the target — a faint veil and edge "
            "highlights over the chair behind it. No glass mass exists and the "
            "shader has no transmission channel. Not built this round: the "
            "opening had to exist before glass over it could mean anything."),
    })

    spec["STATUS"] = (
        "r30 = r29 with the partition OPENED. back_wall was one 4,750 mm slab "
        "running behind a measured frame; the id mask found it filling 53.4% of "
        "the partition zone, which is what thirty rounds of critics read as "
        "frosted glass panels. It is now three boxes stopping at the frame's "
        "outer faces. Nothing behind the opening is dressed this round — the "
        "quick rung exists to see what the hole reveals before that is decided.")

    io.open(DST, "w", encoding="utf-8").write(
        json.dumps(spec, ensure_ascii=False, indent=1))
    print("wrote", DST)
    for p in new:
        print(f"  {p['name']:16s} x {p['c'][0]-p['s'][0]/2:8.1f}..{p['c'][0]+p['s'][0]/2:8.1f}"
              f"  z {p['c'][2]-p['s'][2]/2:7.1f}..{p['c'][2]+p['s'][2]/2:7.1f}")


if __name__ == "__main__":
    main()
