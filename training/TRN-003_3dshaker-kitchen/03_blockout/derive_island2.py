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

# SILHOUETTE COLUMNS, sub-pixel. CORRECTED 2026-08-29 (second pass, then confirmed by an
# independent adversarial re-measure that reproduced every number and supplied the positive
# control the first read never had).
#
# u_right WAS 925.0 AND THERE IS NO EDGE THERE. Mean |grad_u| over eleven 40-row bands from
# v=1320 to v=1760, searched across u in [900,950]: the strongest gradient anywhere in that
# window is 0.4-2.3 grey levels per px. At u=891 in the same bands: 4.2-83.2. The raw row at
# v=1360 reads L=13 at u=890, 177 at u=895, then flat 178..184 all the way to u=960 - a
# 165-level step at 891 and nothing at 925. The number was read off a 25 px grid by eye.
#
# WHAT IT COST: the drum came out 231 mm in radius instead of ~197, i.e. 15-19% too fat in
# every frame this lane has produced, and the same over-wide silhouette moved the island's
# centre-line. The three OTHER pixel readings in this block reproduce within 2 px
# (FAR u_left 505 -> 506.98, NEAR u_left 700 -> 702.00), which is the positive control that
# makes the 34 px miss a finding rather than instrument noise.
#
# The vertical-silhouette check that should have caught it: a vertical cylinder under a
# level camera has vertical silhouettes, and the corrected right edge holds 890.95 / 891.25
# / 891.64 / 891.50 / 892.27 across five row bands spanning the drum's whole 365 px height
# (slope +0.002 px per row). 925 holds nothing to check.
NEAR = dict(u_left=702.00, u_right=890.95, v_base=1722.0)
FAR = dict(u_left=506.98, v_base=1662.0)
# STILL NOT MEASURED HERE, and it matters: the FAR drum's silhouette WIDTH. The code below
# PREDICTS it from the near drum's radius, and poses.json then stores that prediction as if
# it were a reading - which is why recurrence.solve reports width_agreement = 0.0000%, an
# exact zero, on both instances. A self-check between a number and the number it was
# computed from is not a check. An independent read of the far right silhouette wanders
# 173.3 / 175.8 / 178.8 / 182.7 / 183.5 px across five row bands (5.6% spread) because it is
# a ~15 px ramp into a bright sliver of background, not a step - so the honest statement is
# that the far drum corroborates the near one to about 6%, not to 0%.
FAR_W_MEASURED = 178.7      # MEASURED, sd across row bands ~5.6% - weak, and said so


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
