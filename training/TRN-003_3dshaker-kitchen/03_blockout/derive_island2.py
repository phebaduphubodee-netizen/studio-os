#!/usr/bin/env python3
"""derive_island2.py - the island's AXIS, from the two bronze drums.

THE OWNER SAID IT TWICE AND HE WAS RIGHT BOTH TIMES. My first answer ("the axis is
fine, the height was wrong") was also wrong. The island is not perpendicular to the
kitchen wall. It is PARALLEL to it - a galley, bench along the wall and island beside
it - and its long axis points roughly at the camera.

HOW I GOT IT WRONG. I fitted a straight line to the slab's front edge and read a
direction off it. That slab is an OVAL. A straight fit across an oval returns a CHORD,
and a chord's slope is not the object's direction - it depends on which span you fit.
Two spans of the same edge gave slopes of -0.031 and -0.049, which should have stopped
me. Then I assigned that chord's vanishing point to a "family" by PROXIMITY - 7711 vs
the window transom's 7917 - when both numbers sit thousands of pixels off-frame, where
a 0.02 slope error moves the vanishing point by kilometres. Matching two ill-conditioned
numbers to each other is not a measurement, and five later numbers were derived from it.

WHAT SETTLES IT INSTEAD. The two drums are identical cylinders standing on the floor at
different depths. Equal-size objects at two depths give the axis directly:
  * the base of each drum gives its depth      D = f * camera_height / (v_base - horizon)
  * the silhouette width gives the same depth  w = 2R * f / D  (and so gives R)
  * the two centres then give the direction, with no curve to fit and no family to guess
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room_spec as RS

CAM = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
S = CAM["solution"]
F = S["f_px"]; PPX, PPY = S["principal_point_px"]
YAW = math.radians(S["yaw_from_kitchen_wall_deg"])
FWD = np.array([-math.sin(YAW), -math.cos(YAW), 0.0])
RGT = np.array([FWD[1], -FWD[0], 0.0])
C = np.array([RS.CAM_TO_KITCHEN_WALL, RS.CAM_Y, RS.CAM_H])

# read off z-drums.png (crop 430,1300 - 1010,1760, 25 px grid)
NEAR = dict(u_left=700.0, u_right=925.0, v_base=1722.0)
FAR = dict(u_left=505.0, v_base=1662.0)


def depth(v_base):
    return F * RS.CAM_H / (v_base - PPY)


def main():
    d1 = depth(NEAR["v_base"])
    d2 = depth(FAR["v_base"])
    w1 = NEAR["u_right"] - NEAR["u_left"]
    R = w1 * d1 / (2 * F)
    w2 = 2 * R * F / d2
    u1 = (NEAR["u_left"] + NEAR["u_right"]) / 2
    u2 = FAR["u_left"] + w2 / 2
    print(f"near drum  base v={NEAR['v_base']:.0f}  depth {d1:7.0f} mm  width {w1:.0f} px")
    print(f"far  drum  base v={FAR['v_base']:.0f}  depth {d2:7.0f} mm  width {w2:.0f} px (predicted)")
    print(f"drum radius from the near drum          : {R:6.0f} mm  (dia {2*R:.0f})")
    P = []
    for u, d in ((u1, d1), (u2, d2)):
        lat = (u - PPX) / F * d
        P.append(C + d * FWD + lat * RGT)
    P1, P2 = P
    v = P2 - P1
    print(f"\nnear drum world  X {P1[0]:7.0f}  Y {P1[1]:7.0f}")
    print(f"far  drum world  X {P2[0]:7.0f}  Y {P2[1]:7.0f}")
    print(f"drum spacing     {np.linalg.norm(v[:2]):.0f} mm")
    head = math.degrees(math.atan2(v[1], v[0])) % 180.0
    print(f"\nISLAND AXIS heading {head:.1f} deg    (kitchen wall = 90, glazing wall = 0)")
    print(f"  -> off the kitchen wall by {abs(90 - head):.1f} deg")
    u_vp = PPX + F * (float(v @ RGT) / float(v @ FWD))
    print(f"  -> vanishing point at u = {u_vp:.0f}   (kitchen wall VP {S['vp_A_px'][0]:.0f},"
          f" glazing VP {S['vp_B_px'][0]:.0f})")
    cx = (P1[0] + P2[0]) / 2
    print(f"\nisland centre-line at X = {cx:.0f} mm from the kitchen wall face")
    for w in (1150, 1250, 1350):
        print(f"  island {w} wide -> back face X {cx - w/2:6.0f} -> "
              f"walkway to the bench front (X={RS.BENCH_DEPTH}) = {cx - w/2 - RS.BENCH_DEPTH:5.0f} mm")


main()
