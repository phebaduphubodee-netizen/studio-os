#!/usr/bin/env python3
"""derive_plan.py - turn image columns into millimetres along the kitchen wall.

Once the camera is solved, a VERTICAL EDGE in the photo is a measurement: it fixes the
Y of the cabinet joint it belongs to. This is the same move as fSpy's reference length,
applied over and over - and it is checkable, because two of the joints it measures are
appliances whose real widths are published.
"""
import math

F = 4236.0
PPX = 720.0
YAW = math.radians(30.85)
FX, FY = -math.sin(YAW), -math.cos(YAW)      # forward
RX, RY = FY, -FX                              # right

# scale: camera height from the SP01 Michelle stool (915 mm, hoop apex over its own feet)
V_BASE, V_TOP, HORIZON = 1706.0, 1319.0, 1031.0
ZC_STOOL = 915.0 * (V_BASE - HORIZON) / (V_BASE - V_TOP)
ZC = 1500.0                                   # DECLARED: stool 1596, island 1466, oak 1379
CEILING = 2.6189 * ZC - 210.5
CX = 6765.0 * (ZC / 1379.0)                   # perpendicular distance to the kitchen wall


def s_for_u(u, X):
    """How far along Y (towards the camera) a point on plane X sits, for image column u."""
    k = (u - PPX) / F
    a = CX - X
    # (RX*(-a) + RY*(-s)) / (FX*(-a) + FY*(-s)) = k   with (-a) meaning X - CX
    num0, num1 = -RX * a, -RY
    den0, den1 = -FX * a, -FY
    return (k * den0 - num0) / (num1 - k * den1)


def report():
    print(f"stool-derived camera height : {ZC_STOOL:7.0f} mm")
    print(f"declared camera height      : {ZC:7.0f} mm   -> ceiling {CEILING:.0f} mm")
    print(f"camera to kitchen wall      : {CX:7.0f} mm\n")
    UPPERS_D, TALL_D = 350.0, 700.0
    marks = [("uppers left end (corner)", 610, UPPERS_D),
             ("uppers/oak step",         1030, TALL_D),
             ("oven | fridge joint",     1210, TALL_D),
             ("frame right edge",        1440, TALL_D)]
    ys = {}
    for name, u, X in marks:
        s = s_for_u(u, X)
        ys[name] = s
        print(f"{name:26s} u={u:5d}  X={X:4.0f}  s={s:8.0f} mm from camera")
    print()
    print(f"oven stack width  = {ys['uppers/oak step'] - ys['oven | fridge joint']:6.0f} mm"
          f"   (Wolf 30in double oven = 762)")
    print(f"fridge visible    = {ys['oven | fridge joint'] - ys['frame right edge']:6.0f} mm"
          f"   (Sub-Zero 36in column = 914, and it runs past the frame)")
    print(f"bench run length  = {ys['uppers left end (corner)'] - ys['uppers/oak step']:6.0f} mm"
          f"   (corner to the oak bank)")
    return ys


if __name__ == "__main__":
    report()
