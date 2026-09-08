#!/usr/bin/env python3
"""fit_and_overlay.py - place the camera, then DRAW THE BOX ON THE PHOTO.

This is fSpy's "3D guide -> box, and see whether the edges sit on the image" step, and
it is the only honest check the camera solve has. Rotation, focal length and eye height
came out of the line fits; the two remaining unknowns are where the camera stands in
plan, and they are solved here by least squares against the same fitted image lines.

    python fit_and_overlay.py            # solve position, write overlay.png
    python fit_and_overlay.py --free     # also let a few room dimensions move
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_spec as RS                                                  # noqa: E402

CAM = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
S = CAM["solution"]
PLATE = os.path.join(HERE, "..", "01_reference", "plates", "REF-HERO.png")
W, H = CAM["image"]["w"], CAM["image"]["h"]
FPX = S["f_px"]
PPX, PPY = S["principal_point_px"]
ZC = __import__("room_spec").CAM_H  # was S["camera_height_mm"]
YAW = math.radians(S["yaw_from_kitchen_wall_deg"])

FIT = {k: (v["m"], v["b"]) for k, v in CAM["evidence"]["family_A_kitchen_wall_lines"].items()}
FIT.update({k: (v["m"], v["b"]) for k, v in CAM["evidence"]["family_B_glazing_island_lines"].items()})

FORWARD = np.array([-math.sin(YAW), -math.cos(YAW), 0.0])
RIGHT = np.array([FORWARD[1], -FORWARD[0], 0.0])
UP = np.array([0.0, 0.0, 1.0])


def project(P, C):
    """world mm -> image px. Level camera, so the basis is constant."""
    v = np.asarray(P, float) - C
    d = float(v @ FORWARD)
    if d <= 1.0:
        return None
    return (PPX + FPX * float(v @ RIGHT) / d, PPY - FPX * float(v @ UP) / d)


def residuals(params, free_spec=False):
    Cx, Cy = params[0], params[1]
    if free_spec:
        RS.CEILING, RS.UPPERS_BOTTOM, RS.TALL_DEPTH, RS.TRANSOM_Z = params[2:6]
    C = np.array([Cx, Cy, ZC])
    out = []
    for name, (P0, P1) in RS.guide_lines().items():
        if name not in FIT:
            continue
        m, b = FIT[name]
        for t in np.linspace(0.05, 0.95, 7):
            P = np.array(P0, float) * (1 - t) + np.array(P1, float) * t
            uv = project(P, C)
            if uv is None:
                out.append(1e4); continue
            u, v = uv
            out.append(v - (m * u + b))
    return np.array(out)


def draw(C, out_png, spec_note=""):
    im = Image.open(PLATE).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for name, (m, b) in FIT.items():                       # the fitted image evidence
        d.line([(0, b), (W, m * W + b)], fill=(255, 40, 160, 110), width=2)
    E = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4),
         (0, 4), (1, 5), (2, 6), (3, 7)]
    col = {"floor": (90, 90, 90), "kitchen_wall": (120, 200, 255),
           "glazing_wall": (120, 255, 200), "ceiling": (150, 150, 150)}
    for name, lo, hi in RS.boxes():
        c = col.get(name, (255, 230, 60))
        vs = [(x, y, z) for z in (lo[2], hi[2]) for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
        pts = [project(v, C) for v in vs]
        for a, bb in E:
            if pts[a] and pts[bb]:
                d.line([pts[a], pts[bb]], fill=c + (235,), width=2)
    d.rectangle([0, 0, 560, 46], fill=(0, 0, 0, 170))
    d.text((8, 8), f"cam ({C[0]:.0f}, {C[1]:.0f}, {C[2]:.0f}) mm   "
                   f"{S['lens_mm_on_36mm']:.0f}mm   {spec_note}", fill=(255, 255, 255))
    im.save(out_png)
    return out_png


if __name__ == "__main__":
    import room_spec as RS2
    free = "--free" in sys.argv
    if "--fixed" in sys.argv:
        C = np.array([RS2.CAM_TO_KITCHEN_WALL, RS2.CAM_Y, RS2.CAM_H])
        res = residuals([C[0], C[1]], False)
        print(f"camera  = ({C[0]:.0f}, {C[1]:.0f}, {C[2]:.0f}) mm  [derived, not fitted]")
        print(f"resid   rms = {np.sqrt(np.mean(res**2)):.2f} px   max = {np.abs(res).max():.2f} px")
        print(draw(C, os.path.join(HERE, "overlay.png"), "derived spec"))
        raise SystemExit
    x0 = [4200.0, 6200.0] + ([RS.CEILING, RS.UPPERS_BOTTOM, RS.TALL_DEPTH, RS.TRANSOM_Z] if free else [])
    lo = [500.0, 500.0] + ([2600.0, 1300.0, 500.0, 1800.0] if free else [])
    hi = [20000.0, 20000.0] + ([4200.0, 1900.0, 1100.0, 3200.0] if free else [])
    r = least_squares(residuals, x0, bounds=(lo, hi), args=(free,), xtol=1e-12, ftol=1e-12)
    C = np.array([r.x[0], r.x[1], ZC])
    if free:
        RS.CEILING, RS.UPPERS_BOTTOM, RS.TALL_DEPTH, RS.TRANSOM_Z = r.x[2:6]
    res = residuals(r.x, free)
    print(f"camera  = ({C[0]:.0f}, {C[1]:.0f}, {C[2]:.0f}) mm")
    print(f"resid   rms = {np.sqrt(np.mean(res**2)):.2f} px   max = {np.abs(res).max():.2f} px")
    if free:
        print(f"ceiling={RS.CEILING:.0f}  uppers_bottom={RS.UPPERS_BOTTOM:.0f}  "
              f"tall_depth={RS.TALL_DEPTH:.0f}  transom_z={RS.TRANSOM_Z:.0f}")
    names = list(RS.guide_lines())
    per = res.reshape(-1, 7)
    for n, row in zip([n for n in names if n in FIT], per):
        print(f"  {n:16s} mean {row.mean():+7.1f} px   max |{np.abs(row).max():6.1f}|")
    print(draw(C, os.path.join(HERE, "overlay.png"),
               "free-spec" if free else "spec as declared"))
    json.dump({"cam_mm": list(C), "rms_px": float(np.sqrt(np.mean(res**2)))},
              open(os.path.join(HERE, "solved-position.json"), "w"), indent=1)
