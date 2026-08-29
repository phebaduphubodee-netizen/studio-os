#!/usr/bin/env python3
"""island_check.py - draw ONLY the island, two ways, on the plate.

The owner says the island looks laid the wrong way. A box that is 90 deg out can still
land one edge correctly, so this draws BOTH hypotheses on the plate and lets the
picture decide:
  A = long axis along X  (parallel to the glazed wall, pointing AT the kitchen wall)
  B = long axis along Y  (parallel to the kitchen wall / the bench run)
Same footprint area, same height, same centre.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_spec as RS

CAM = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
S = CAM["solution"]
F = S["f_px"]; PPX, PPY = S["principal_point_px"]
YAW = math.radians(S["yaw_from_kitchen_wall_deg"])
FWD = np.array([-math.sin(YAW), -math.cos(YAW), 0.0])
RGT = np.array([FWD[1], -FWD[0], 0.0])
UP = np.array([0.0, 0.0, 1.0])
C = np.array([RS.CAM_TO_KITCHEN_WALL, RS.CAM_Y, RS.CAM_H])


def proj(P):
    v = np.asarray(P, float) - C
    d = float(v @ FWD)
    if d <= 1.0:
        return None
    return (PPX + F * float(v @ RGT) / d, PPY - F * float(v @ UP) / d)


E = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4),
     (0, 4), (1, 5), (2, 6), (3, 7)]


def draw_box(d, lo, hi, col, w=3):
    vs = [(x, y, z) for z in (lo[2], hi[2]) for y in (lo[1], hi[1]) for x in (lo[0], hi[0])]
    pts = [proj(v) for v in vs]
    for a, b in E:
        if pts[a] and pts[b]:
            d.line([pts[a], pts[b]], fill=col, width=w)


def main():
    cx = (RS.ISL_X0 + RS.ISL_X1) / 2.0
    cy = (RS.ISL_Y0 + RS.ISL_Y1) / 2.0
    L, W = 3200.0, 1250.0
    for tag, (lx, ly), col in (("A_along_X", (L, W), (255, 220, 40)),
                               ("B_along_Y", (W, L), (60, 200, 255))):
        im = Image.open(os.path.join(HERE, "..", "01_reference", "plates", "REF-HERO.png")).convert("RGB")
        d = ImageDraw.Draw(im, "RGBA")
        lo = (cx - lx / 2, cy - ly / 2, 0.0)
        hi = (cx + lx / 2, cy + ly / 2, RS.ISL_H)
        draw_box(d, lo, hi, col + (255,))
        d.rectangle([0, 0, 700, 40], fill=(0, 0, 0, 190))
        d.text((8, 12), f"island hypothesis {tag}   footprint {lx:.0f} x {ly:.0f} mm at "
                        f"({cx:.0f},{cy:.0f})", fill=(255, 255, 255))
        out = os.path.join(HERE, f"island_{tag}.png")
        im.save(out)
        print(out)


main()
