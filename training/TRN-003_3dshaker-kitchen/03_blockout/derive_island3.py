#!/usr/bin/env python3
"""derive_island3.py - the island slab is an OVAL, so measure it as one.

WHY A THIRD SCRIPT. derive_island.py read a DIRECTION off a straight line fitted across
this same oval and got a chord; derive_island2.py replaced that with the two bronze drums
and settled the AXIS. Neither measured the SHAPE. room_spec still carries ISL_W = 1250 as
an ASSERTED number and builds the slab as a BOX with a bevel, while the plate shows a
stadium/ellipse whose near end is a full semicircle.

THE INSTRUMENT. An ellipse lying in a known horizontal plane projects to an ellipse in the
image, and the inverse is exact: unproject the traced silhouette onto z = the slab's
underside and the curve becomes an ellipse again, IN THE PLANE WHERE IT IS ONE. Fitting
there is not fitting a straight line to a curve - it is the opposite of the mistake that
cost this lane a quarter turn.

WHAT IS TRACED. The slab's OUTER silhouette (the underside edge of the bullnose) against
the dark void under the cantilever, which only exists from about u=430 rightwards - to the
left the travertine body is behind the edge and there is no contrast. So the arc covers the
NEAR half only, and the far semi-axis is therefore NOT measured by this: it is reported as
an extrapolation and tagged as one.

CONSTRAINT: the ellipse centre's X is taken from derive_island2's drums, not fitted, and
the axes are taken as the room's X and Y (the drums put the long axis 2.7 deg off Y, which
is inside this method's own noise). So three unknowns - cy, a (half width in X), b (half
length in Y) - against several hundred traced points.
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
import room_spec as RS                                                   # noqa: E402

PLATE = os.path.join(HERE, "..", "01_reference", "plates", "REF-HERO.png")
CAM = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
S = CAM["solution"]
F = S["f_px"]; PPX, PPY = S["principal_point_px"]
YAW = math.radians(S["yaw_from_kitchen_wall_deg"])
FWD = np.array([-math.sin(YAW), -math.cos(YAW), 0.0])
RGT = np.array([FWD[1], -FWD[0], 0.0])
UP = np.array([0.0, 0.0, 1.0])
C = np.array([RS.CAM_TO_KITCHEN_WALL, RS.CAM_Y, RS.CAM_H])
Z_UNDER = RS.ISL_H - RS.ISL_SLAB_T          # the underside of the slab

U0, U1 = 430, 1078                          # where the void under the cantilever exists
VLO, VHI = 1240, 1420
BRIGHT = 110.0                              # slab vs the shadowed void beneath it


def proj(P):
    v = np.asarray(P, float) - C
    d = float(v @ FWD)
    return (PPX + F * float(v @ RGT) / d, PPY - F * float(v @ UP) / d)


def hit_z(u, v, z):
    d = RGT * (u - PPX) + UP * (-(v - PPY)) + FWD * F
    t = (z - C[2]) / d[2]
    return C + t * d


def trace_bottom(L):
    """Lowest bright pixel in each column that has darkness under it - sub-pixel."""
    pts = []
    for u in range(U0, U1 + 1):
        col = L[VLO:VHI, u]
        bright = col > BRIGHT
        best = None
        for k in range(len(col) - 9, 0, -1):
            if bright[k] and not bright[k + 1:k + 9].any():
                best = k
                break
        if best is None or best < 2:
            continue
        # sub-pixel: linear interpolation to the BRIGHT crossing
        a0, a1 = col[best], col[best + 1]
        frac = 0.0 if a0 == a1 else (a0 - BRIGHT) / (a0 - a1)
        pts.append((float(u), VLO + best + float(np.clip(frac, 0.0, 1.0))))
    return np.array(pts)


def main():
    im = Image.open(PLATE).convert("RGB")
    a = np.asarray(im).astype(float)
    L = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
    pts = trace_bottom(L)
    print(f"traced {len(pts)} columns of the slab's underside silhouette, u {U0}..{U1}")

    W = np.array([hit_z(u, v, Z_UNDER)[:2] for u, v in pts])
    cx = RS.ISL_CENTRE_X

    def resid(p):
        cy, aa, bb = p
        return ((W[:, 0] - cx) / aa) ** 2 + ((W[:, 1] - cy) / bb) ** 2 - 1.0

    r = least_squares(resid, [3800.0, 625.0, 1536.0],
                      bounds=([1000, 300, 600], [7000, 1400, 3500]), xtol=1e-14)
    cy, aa, bb = r.x
    # residual in MILLIMETRES, radially, not in the implicit units
    ang = np.arctan2((W[:, 1] - cy) / bb, (W[:, 0] - cx) / aa)
    onx = cx + aa * np.cos(ang); ony = cy + bb * np.sin(ang)
    dmm = np.hypot(W[:, 0] - onx, W[:, 1] - ony)
    print(f"\nELLIPSE in the z={Z_UNDER:.0f} mm plane, centre X pinned to the drums' {cx}")
    print(f"  centre Y      {cy:8.0f} mm")
    print(f"  half width X  {aa:8.0f} mm   -> width  {2*aa:6.0f}  "
          f"(room_spec ISL_W = {RS.ISL_W})")
    print(f"  half length Y {bb:8.0f} mm   -> length {2*bb:6.0f}  "
          f"(room_spec ISL_Y1-ISL_Y0 = {RS.ISL_Y1-RS.ISL_Y0})")
    print(f"  radial residual  mean {dmm.mean():5.1f} mm   p95 {np.percentile(dmm,95):5.1f}"
          f"   max {dmm.max():5.1f}")
    print(f"  near tip Y    {cy+bb:8.0f} mm   (room_spec ISL_Y1 = {RS.ISL_Y1})")
    print(f"  far  tip Y    {cy-bb:8.0f} mm   (room_spec ISL_Y0 = {RS.ISL_Y0})  "
          f"** EXTRAPOLATED, no traced points there **")

    # POSITIVE CONTROL: the two drums must sit inside this ellipse, and the fitted
    # near tip must reproject onto the pixel where the tip actually is.
    print("\npositive control")
    for i, dy in enumerate(RS.DRUM_Y):
        t = ((RS.ISL_CENTRE_X - cx) / aa) ** 2 + ((dy - cy) / bb) ** 2
        print(f"  drum{i} centre at Y={dy} -> ellipse value {t:.3f} "
              f"({'inside' if t < 1 else 'OUTSIDE'})")
    utip, vtip = proj((cx, cy + bb, Z_UNDER))
    print(f"  fitted near tip reprojects to u={utip:.1f} v={vtip:.1f}; the traced arc's "
          f"last column is u={pts[-1,0]:.0f} v={pts[-1,1]:.1f}")

    out = os.path.join(HERE, "island_ELLIPSE.png")
    d = ImageDraw.Draw(im, "RGBA")
    for u, v in pts[::4]:
        d.ellipse([u - 1.5, v - 1.5, u + 1.5, v + 1.5], fill=(255, 60, 60, 220))
    ring = [proj((cx + aa * math.cos(t), cy + bb * math.sin(t), Z_UNDER))
            for t in np.linspace(0, 2 * math.pi, 400)]
    d.line(ring + [ring[0]], fill=(60, 255, 120, 235), width=3)
    ring_top = [proj((cx + aa * math.cos(t), cy + bb * math.sin(t), RS.ISL_H))
                for t in np.linspace(0, 2 * math.pi, 400)]
    d.line(ring_top + [ring_top[0]], fill=(80, 180, 255, 200), width=2)
    d.rectangle([0, 0, 900, 40], fill=(0, 0, 0, 190))
    d.text((8, 12), f"red = traced silhouette   green = fitted ellipse at z={Z_UNDER:.0f}"
                    f"   blue = same ellipse at z={RS.ISL_H}", fill=(255, 255, 255))
    im.save(out)
    print("\n" + out)
    json.dump(dict(centre_x_mm=cx, centre_y_mm=cy, half_x_mm=aa, half_y_mm=bb,
                   plane_z_mm=Z_UNDER, n_points=len(pts),
                   radial_resid_mean_mm=float(dmm.mean()),
                   radial_resid_p95_mm=float(np.percentile(dmm, 95)),
                   u_range=[U0, U1],
                   far_tip_is_extrapolated=True),
              open(os.path.join(HERE, "island-ellipse.json"), "w"), indent=1)


main()
