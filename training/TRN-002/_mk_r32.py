"""spec_r31 -> spec_r32.  THE MATERIAL TABLE, RE-DERIVED THROUGH OUR OWN LIGHT.

WHAT THE ROUND IS TESTING, WRITTEN DOWN BEFORE THE RENDER: applying the k values
below should move SLOPE from 0.697 to 0.898 and SHAPE_FLAT from 0.3077 to 0.1703.
That is a FIRST-ORDER prediction — it assumes scaling an albedo scales its
object's rendered value and knows nothing about interreflection, shadowing or the
shader. If the render lands there, albedo is the lever and this is the fix. If it
lands short, the residual is light, and the number it falls short by is how much.

---------------------------------------------------------------- WHAT WAS WRONG
Two blind critics, on two frames, in two separate contexts, chose the same item:
*every object is the same white matte plastic*. The lane's own instrument now
says by how much and, for the first time, WHICH KNOB:

    SLOPE        0.697   our objects span 0.70 of the target's value range
    RHO         +0.810   the ORDER is broadly right — this is not a mix-up
    LIGHT_SPAN   0.925   within a material, our light modulates as hard as
                         the target's. THE LIGHT IS NOT THE COMPRESSOR.

LIGHT_SPAN is the load-bearing measurement and it rests on an identity, not a
model: **within one PALETTE row the albedo is the same number by construction**,
so any value difference between two objects wearing it is light with nothing else
it can be. Ours modulates oak, linen and bed upholstery at 0.77 / 0.92 / 0.99 of
the target's own within-material spread. The compression is therefore BETWEEN
materials, which is the albedo table.

------------------------------------------------------------ HOW k WAS DERIVED
Our render is the one image where the albedo is KNOWN exactly, so the irradiance
at each object is Y_ours / albedo, and the target's pixel read through OUR
irradiance gives the albedo the target's surface would need. Anchored on
`paint_white` — the phase-2 reference surface (n=65,014 px) and the only row in
the table not derived as a ratio to something else — so paint_white's own k is
1.000 by construction:

    k = (target_mean / ours_mean) / 1.10952

taken per material over its trustworthy id-mask rows, geometric means both sides.

THE ANCHOR MOVES THE LEVEL AND CANNOT MOVE THE TEST. Choosing `left_wall` alone
instead of paint_white's two-object mean multiplies every k by 1.26. That is a
LEVEL choice and it belongs to the light lane; SLOPE, RHO and every ratio between
two k values are untouched by it. Declared rather than hidden, because it is the
one arbitrary number in this derivation.

--------------------------------------------------- WHERE THE DERIVATION REFUSES
Two materials want MORE light than a dielectric can return, and the honest answer
is that their residual is not a material at all:

    upholstery_bed  k 1.083 -> albedo 0.943 = sRGB 248.5, past the studio's 240
    lacquer_white   k 1.198 -> albedo 0.910 = sRGB 244.7, past the studio's 240

Neither row is touched. This is the SECOND independent time the bed's upholstery
has returned an impossible albedo — its own provenance already says "the side
face reads 1.512x wall and CLIPS when converted (albedo 1.16-1.22) ... a
measurement that returns an impossible albedo is reporting the light, not the
surface", and that was from the target side alone. Reaching the same verdict from
the opposite direction, through our own irradiance, is what makes it a finding:
**THE TARGET PUTS MORE LIGHT ON THE BED AND ON THE ENTRY DOOR THAN OUR RIG DOES,
and no repaint can close it.** -> declared light ticket, r33.

`paint_white`'s own two objects are the other half of that ticket: back wall and
left wall are one material, so the target's 1.58x between them is pure light, and
ours renders them 1.01x apart. LIGHT_SPAN 0.022 on the room's largest material.
A frame whose walls do not differ is a frame with no direction in its light.

--------------------------------------------------------------- THE RULE APPLIED
Every material with at least one trustworthy measured object AND a reachable
result is re-derived. Nothing is held back by hand — a subset chosen by the
builder is the flattering-scorer this lane has already been caught by twice
(r23's seven-object bracket, r27's unpinned membership). Two consequences worth
naming out loud rather than quietly enjoying:

  * `frame_black` moves to 0.080, BELOW its own measured bracket (0.113-0.125,
    darkest-30% cores). Two measurements of one surface disagree; the render is
    the tiebreaker and the disagreement is recorded, not smoothed over.
  * `veneer_oak_h` and the retired `veneer_travertine` alias carry veneer_oak's
    tuple and move WITH it. A row that shares another's values and does not share
    its edits is how a grain-rotated panel drifts from the run it belongs to.

`veneer_oak` is the largest single move (k 0.626, five measured objects), and its
provenance predicted this: the value was taken "from the etagere panel (the
middle of the run's 4x lighting spread)" — one number chosen from the middle of a
4x range, which is the light being written into the material table exactly as the
module header warns against.
"""
import io
import json
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "spec_r31.json")
DST = os.path.join(HERE, "spec_r32.json")

# material -> (k, n objects it was measured over, within-material light span)
# k = (target_mean/ours_mean)/1.10952 on r31's id-mask rows. See module docstring.
K = {
    "veneer_oak":        (0.6264, 5, 0.765),
    "veneer_oak_h":      (0.6264, 0, None),    # shares veneer_oak's tuple
    "veneer_travertine": (0.6264, 0, None),    # retired alias, same tuple
    "upholstery_chair":  (0.6779, 1, None),
    "frame_black":       (0.6819, 1, None),
    "linen_white":       (0.8005, 4, 0.924),
    "woven_oat":         (0.8594, 1, None),
    "art_relief":        (0.8812, 1, None),
    "paint_ceiling":     (1.1719, 1, None),
    "lacquer_wardrobe":  (1.2342, 2, None),
    "floor_herringbone": (1.3545, 1, None),
}
# measured, reachable-refused: the albedo the k implies is outside the studio's
# dielectric band, so the residual is light. Recorded IN the spec, not just here.
REFUSED = {
    "upholstery_bed": (1.0825, 248.5),
    "lacquer_white":  (1.1976, 244.7),
}
SRGB_HI = 240.0


def _srgb(v):
    return 255.0 * (12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)


def main():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                    "pipeline", "scripts"))
    import trn002_materials as M

    spec = json.load(io.open(SRC, encoding="utf-8"))
    if spec.get("round") == "r32":
        raise SystemExit("spec_r31.json is already r32 — check the source")
    spec["round"] = "r32"

    over, log = {}, []
    for mat, (k, n, span) in sorted(K.items()):
        alb, rough, metal, slug, scale = M.PALETTE[mat]
        new = tuple(round(c * k, 4) for c in alb)
        hi = _srgb(max(new))
        if hi > SRGB_HI + 1e-9:
            raise SystemExit(
                f"{mat}: k={k} lands at sRGB {hi:.1f}, past the {SRGB_HI} ceiling — "
                f"it belongs in REFUSED, not in K. A generator that quietly ships an "
                f"impossible albedo is the defect this whole round is about")
        over[mat] = [list(new), rough, metal, slug, scale]
        log.append(f"  {mat:18s} k={k:.4f} n={n}  "
                   f"{tuple(round(c, 3) for c in alb)} -> {new}  "
                   f"sRGB {_srgb(max(alb)):.0f} -> {hi:.0f}")
    spec["materials"] = over

    spec["declared_gaps"] = list(spec.get("declared_gaps", [])) + [
        f"LIGHT TICKET (r32, measured twice from opposite directions): "
        f"{mat} wants k={k} through our own irradiance, which lands its albedo at "
        f"sRGB {hi} — past the studio's {SRGB_HI:.0f} dielectric ceiling. No repaint "
        f"can reach it: the target puts more light on this surface than our rig does."
        for mat, (k, hi) in sorted(REFUSED.items())] + [
        "LIGHT TICKET (r32): paint_white is ONE material on back wall and left wall. "
        "The target renders them 1.58x apart and we render them 1.01x apart "
        "(LIGHT_SPAN 0.022) — within one material that difference can only be light, "
        "and it is the largest material in the room. Our walls do not differ, so the "
        "room has no direction in its light."]

    spec["STATUS"] = (
        "r32 = r31 with the MATERIAL TABLE re-derived through our own irradiance. "
        "Predicted before rendering: SLOPE 0.697 -> 0.898, SHAPE_FLAT 0.3077 -> "
        "0.1703, LIGHT_SPAN ~unchanged at 0.925. Eleven rows move (nine materials, "
        "two of them aliases); two measured rows are REFUSED because the albedo they "
        "ask for is past the studio's dielectric ceiling, and those become light "
        "tickets rather than repaints.")

    io.open(DST, "w", encoding="utf-8").write(
        json.dumps(spec, ensure_ascii=False, indent=1))
    print("wrote", DST)
    print("\n".join(log))
    print(f"  REFUSED (light tickets): "
          f"{', '.join(f'{m} k={k}' for m, (k, _h) in sorted(REFUSED.items()))}")


if __name__ == "__main__":
    main()
