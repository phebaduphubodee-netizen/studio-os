#!/usr/bin/env python3
"""palette_solve.py - turn the plate's PHOTOGRAPHED colours into ALBEDOS, by rendering.

    python 04_mood/palette_solve.py 05_build/out/p5_texture.png            # report
    python 04_mood/palette_solve.py 05_build/out/p5_texture.png --apply    # and write back

THE PROBLEM THIS EXISTS FOR. The tutorial's material split is an eyedropper on the
reference (16:30-22:45), and every number that comes off a photograph is ILLUMINANT x
ALBEDO. The plate's ceiling reads 208,189,163 - strongly warm - because the light is warm;
the ceiling is white. Type that triple into a Base Color and the render applies the warm
light to an already-warm surface and the frame goes pink. That is exactly what
p5_texture.png did, and palette-from-plate.json's own header predicted it.

THE FIX IS A SOLVE, NOT A JUDGEMENT. Render, measure the same surface in our frame and in
the plate, and divide the albedo by the ratio. One or two iterations converge because the
relationship is very nearly linear in albedo for a diffuse surface.

THREE THINGS THAT MAKE IT A MEASUREMENT RATHER THAN A KNOB:

 1. THE PATCH IS DERIVED, NOT TYPED. Every box is a world rectangle on a named face of a
    named mass, projected through the solved camera. This repo has twice shipped a gate
    whose "crop" was a typed pixel box that had drifted off its own subject - once passing
    a rug check on 0.8% rug - and the fix both times was a sentence. Here the box cannot
    drift off the object without the object moving.

 2. IT READS THE SHADOW LOBE, NOT THE MEAN. Our sun and the plate's sun do not put their
    beams in the same places, so a mean over a patch compares our sunlit fraction against
    theirs. The dark lobe of each patch (Otsu, then the median of the lower side - the same
    split shadow_delta uses) is the AMBIENT-lit reading, and ambient is what an albedo
    solve wants. A patch with no separable lobes is REFUSED, not averaged.

 3. IT SAYS OUT LOUD THAT IT IS A CALIBRATION. Once the albedo is fitted so our patch
    matches the plate's patch, "our patch matches the plate" is true BY CONSTRUCTION and
    proves nothing about the frame. The things that can still fail are elsewhere:
    shadow_delta's lit-minus-shadow on one material, the critics, and every surface with no
    row here. This file must never be cited as evidence that the frame is right.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "03_blockout"))
sys.path.insert(0, HERE)
import room_spec as RS                                                    # noqa: E402
import shadow_delta as SD                                                 # noqa: E402

PLATE = os.path.join(HERE, "..", "01_reference", "plates", "REF-HERO.png")
PALETTE = os.path.join(HERE, "palette-from-plate.json")
CAM = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
S = CAM["solution"]
F = S["f_px"]
PPX, PPY = S["principal_point_px"]
YAW = math.radians(S["yaw_from_kitchen_wall_deg"])
FWD = np.array([-math.sin(YAW), -math.cos(YAW), 0.0])
RGT = np.array([FWD[1], -FWD[0], 0.0])
UP = np.array([0.0, 0.0, 1.0])
C = np.array([RS.CAM_TO_KITCHEN_WALL, RS.CAM_Y, RS.CAM_H])

# How much of a per-channel disagreement this file is willing to call an ALBEDO error.
# Beyond it the difference is the LIGHT and is reported instead of absorbed.
CHROMA_OWN = 0.10


def proj(P):
    v = np.asarray(P, float) - C
    d = float(v @ FWD)
    if d <= 1.0:
        return None
    return (PPX + F * float(v @ RGT) / d, PPY - F * float(v @ UP) / d)


# ---------------------------------------------------------------------------------------
# WORLD PATCHES. Four corners of a rectangle on a named face of a named mass. The comment
# on each says WHICH face, because a patch on the wrong face of the right object is the
# same defect as a patch on the wrong object.
# ---------------------------------------------------------------------------------------
def patches():
    p = {}
    Z = RS.CEILING
    # the ceiling patch has to be NEAR the camera or it projects above the top of the
    # frame: at y 3000-5200 the derived box came out with v = -79, i.e. off the plate.
    p["plaster"] = [(600, 8000, Z), (2600, 8000, Z), (2600, 10500, Z), (600, 10500, Z)]
    p["white"] = [(RS.UPPERS_DEPTH, 700, 2100), (RS.UPPERS_DEPTH, 2500, 2100),
                  (RS.UPPERS_DEPTH, 2500, 3200), (RS.UPPERS_DEPTH, 700, 3200)]
    # stone_marble stops at y=2200, not 2500: at 2500 the box's right end ran past the
    # uppers/tall junction (u=1018) and swallowed a slice of the black oven, which is what
    # gave this patch a spurious dark lobe on the first run.
    p["stone_marble"] = [(RS.SPLASH_T, 900, RS.BENCH_H + 120),
                         (RS.SPLASH_T, 2200, RS.BENCH_H + 120),
                         (RS.SPLASH_T, 2200, RS.UPPERS_BOTTOM - 80),
                         (RS.SPLASH_T, 900, RS.UPPERS_BOTTOM - 80)]
    # wood_oak sits HIGH on the fridge leaf, above the black pull, for the same reason.
    p["wood_oak"] = [(RS.TALL_DEPTH, 3700, 2500), (RS.TALL_DEPTH, 4300, 2500),
                     (RS.TALL_DEPTH, 4300, 3100), (RS.TALL_DEPTH, 3700, 3100)]
    p["black"] = [(RS.TALL_DEPTH + RS.OVEN_PROUD, RS.OVEN_Y0 + 120, 1150),
                  (RS.TALL_DEPTH + RS.OVEN_PROUD, RS.OVEN_Y1 - 120, 1150),
                  (RS.TALL_DEPTH + RS.OVEN_PROUD, RS.OVEN_Y1 - 120, 1900),
                  (RS.TALL_DEPTH + RS.OVEN_PROUD, RS.OVEN_Y0 + 120, 1900)]
    # the travertine patch is on the FAR half of the body: the two stools stand at Y 2900
    # and 3450 with their frames right across the near half.
    XT = RS.ISL_X1 - RS.ISL_STONE_INSET
    p["stone_travertine"] = [(XT, RS.ISL_Y0 + 120, 300), (XT, RS.ISL_Y0 + 560, 300),
                             (XT, RS.ISL_Y0 + 560, 700), (XT, RS.ISL_Y0 + 120, 700)]
    # and the floor patch has to be FAR from it, for the mirror-image reason: at
    # y 6200-8200 three of its four corners fell outside the frame.
    p["wood_floor"] = [(3300, 5000, 0), (4500, 5000, 0), (4500, 6100, 0), (3300, 6100, 0)]
    return p


def box_of(quad, shrink=0.18):
    uv = [proj(q) for q in quad]
    if any(x is None for x in uv):
        return None
    us = [a for a, _ in uv]
    vs = [b for _, b in uv]
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    du, dv = (u1 - u0) * shrink, (v1 - v0) * shrink
    b = (int(u0 + du), int(v0 + dv), int(u1 - du), int(v1 - dv))
    if b[2] - b[0] < 12 or b[3] - b[1] < 12:
        return None
    return b


def ambient_level(path, box):
    """Both readings of one patch: the whole-patch median and, when the patch really is
    bimodal, the DARK lobe's median. The caller picks, and it must pick the SAME ONE in
    both images - comparing the plate's shadow lobe against our whole patch is comparing
    two different quantities and would have returned a 4x ratio here (it did, on the first
    run: the plate's wood_oak box caught the fridge's black handle and read 24,18,10 while
    ours read 201,155,117)."""
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    sub = im[box[1]:box[3], box[0]:box[2]]
    if sub.size < 400:
        return None
    out = dict(whole=np.median(sub.reshape(-1, 3), axis=0),
               n=int(sub.shape[0] * sub.shape[1]), shadow=None,
               sd=float(np.mean(np.std(sub.reshape(-1, 3), axis=0))))
    g = (sub.max(axis=2) + sub.min(axis=2)) * 0.5
    m = SD.two_modes(g.ravel())
    if m is not None and not m.get("clipped"):
        sel = g <= m["threshold"]
        if sel.sum() >= 200:
            out["shadow"] = np.median(sub[sel], axis=0)
    return out


def to_lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(np.asarray(c, float), 0.0, 1.0)
    s = np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
    return np.clip(np.round(s * 255.0), 0, 255).astype(int)


def hex_of(rgb255):
    return "#%02X%02X%02X" % tuple(int(v) for v in rgb255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--damping", type=float, default=1.0)
    ap.add_argument("--overlay", default="")
    o = ap.parse_args()

    if Image.open(PLATE).size != Image.open(o.render).size:
        print("exit 2 - COULD NOT RUN. The render is not the plate's size, so every "
              "derived patch box lands on different content in the two images.",
              file=sys.stderr)
        return 2

    pal = json.load(open(PALETTE))
    print(f"{'family':18s} {'plate (ambient)':>17s} {'ours':>17s} {'ratio R,G,B':>20s}"
          f"   {'albedo now':>9s} -> {'albedo next':>11s}   mode")
    rows, ok, chromas = [], 0, []
    for fam, quad in patches().items():
        row = pal["families"].get(fam)
        if row is None:
            continue
        b = box_of(quad)
        if b is None:
            print(f"{fam:18s} patch is off-frame or too small - REFUSED")
            continue
        a = ambient_level(PLATE, b)
        c = ambient_level(o.render, b)
        if a is None or c is None:
            print(f"{fam:18s} patch too small to read - REFUSED")
            continue
        # SAME QUANTITY IN BOTH, OR NEITHER.
        if a["shadow"] is not None and c["shadow"] is not None:
            ra, rc, mode = a["shadow"], c["shadow"], "shadow-lobe"
        else:
            ra, rc, mode = a["whole"], c["whole"], "whole-patch"
        a = dict(rgb=ra, mode=mode)
        c = dict(rgb=rc, mode=mode)
        la, lc = to_lin(a["rgb"]), to_lin(c["rgb"])
        ratio = np.where(la > 1e-4, lc / np.maximum(la, 1e-4), 1.0)
        raw = ratio.copy()
        ratio = np.clip(ratio, 0.25, 4.0)
        if np.any(raw != ratio):
            # A RATIO AT THE CLAMP MEANS THE MODEL IS WRONG, NOT THAT THE ALBEDO IS FAR
            # OUT. Scaling a diffuse albedo cannot move a surface by 4x when the surface
            # is bright for some other reason. On the first run this fired on `black`:
            # the plate's oven reads 14,14,14 and ours read 186,159,129, because our oven
            # face is a flat glossy plane aimed at the window and is MIRRORING it. Dividing
            # its albedo would have driven an already-near-black colour to #191919 and
            # changed nothing in the frame. Refuse and name the real cause.
            print(f"{fam:18s} ratio {np.array2string(raw, precision=2)} hits the clamp - "
                  f"REFUSED. A 4x difference on a diffuse surface is not an albedo error; "
                  f"look for specular, for the wrong face, or for a patch on two things.")
            continue
        # ---- SPLIT THE RATIO INTO A LEVEL AND A COLOUR, AND ONLY OWN THE LEVEL ---------
        # A per-channel albedo divide will absorb ANY difference, including one that is not
        # the albedo's fault. On the first run it proposed a floor albedo of #ABBCF0 and a
        # marble of #98A7B5 - a blue kitchen - because our LIGHT is warmer than the plate's
        # and the solve was quietly paying for that out of the surfaces. A blue albedo under
        # an orange light does render grey, and it is wrong the moment the light moves.
        # So: the geometric mean of the ratio is the LEVEL and belongs to the albedo; what
        # is left is CHROMA and belongs to the light. The level is applied; the chroma is
        # applied only up to CHROMA_OWN and the remainder is REPORTED as a light-colour
        # error, which is a thing somebody can go and fix at the sun and the world.
        level = float(np.exp(np.mean(np.log(np.clip(ratio, 1e-3, None)))))
        chroma = ratio / level
        chroma_err = float(np.max(np.abs(chroma - 1.0)))
        applied = level * np.clip(chroma, 1 - CHROMA_OWN, 1 + CHROMA_OWN)
        cur = to_lin([int(row["srgb_hex"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)])
        nxt = np.clip(cur / (applied ** o.damping), 0.01, 0.95)
        nhex = hex_of(to_srgb(nxt))
        flag = "" if chroma_err <= CHROMA_OWN else f"  <- LIGHT COLOUR off {chroma_err:.0%}"
        print(f"{fam:18s} {str([int(v) for v in a['rgb']]):>17s} "
              f"{str([int(v) for v in c['rgb']]):>17s} "
              f"{np.array2string(ratio, precision=2, floatmode='fixed'):>20s}"
              f"   {row['srgb_hex']:>9s} -> {nhex:>11s}   {a['mode']}{flag}")
        rows.append((fam, b, nhex, [float(v) for v in ratio]))
        chromas.append(chroma)
        if max(abs(ratio - 1.0)) < 0.06:
            ok += 1
    if chromas:
        m = np.mean(np.array(chromas), axis=0)
        print(f"\nLIGHT COLOUR, measured across {len(chromas)} families and NOT paid for "
              f"out of the albedos: our light is {np.array2string(m, precision=3)} times "
              f"the plate's, per channel, after the level is removed.")
        print(f"  -> our light is {'WARMER' if m[0] > m[2] else 'COOLER'} than the plate's "
              f"by {abs(m[0] / max(m[2], 1e-6) - 1):.0%} on R/B. Fix it at the sun colour "
              f"and the world saturation, not here.")
    print(f"\n{ok}/{len(rows)} families are within 6% of the plate's ambient reading.")
    print("THIS IS A CALIBRATION, NOT A CHECK. After it converges, 'our patch matches the "
          "plate' is true by construction. What can still fail is shadow_delta, the "
          "critics, and every surface with no row here.")

    if o.overlay:
        im = Image.open(PLATE).convert("RGB")
        d = ImageDraw.Draw(im)
        for fam, b, _, _ in rows:
            d.rectangle(b, outline=(255, 60, 60), width=3)
            d.text((b[0] + 4, b[1] + 4), fam, fill=(255, 255, 0))
        im.save(o.overlay)
        print("overlay ->", o.overlay)

    if o.apply:
        for fam, _, nhex, ratio in rows:
            pal["families"][fam]["srgb_hex"] = nhex
            pal["families"][fam]["albedo_solved"] = True
            pal["families"][fam]["solve_ratio"] = [round(v, 4) for v in ratio]
            pal["families"][fam]["solved_against"] = os.path.basename(o.render)
        json.dump(pal, open(PALETTE, "w"), indent=1)
        print("\nwrote", PALETTE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
