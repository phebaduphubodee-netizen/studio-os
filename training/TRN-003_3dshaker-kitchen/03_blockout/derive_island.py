#!/usr/bin/env python3
"""derive_island.py - where the island actually is, once its HEIGHT stops being a guess.

THE OWNER SAID THE ISLAND LOOKED WRONG. He was right, and the axis was not the fault:
the slab's own edge line puts its direction 89.6 deg off the kitchen wall, which is
perpendicular to 0.4 deg. What was wrong is that I had ASSERTED the slab height at 900
(a standard bench), and a horizontal line's image fixes only the RATIO of (camera
height - line height) to distance. Assert the height too low and the whole island slides
towards the camera along the wall - which is exactly what it did: 1.65 m out of place,
sitting in front of the cooktop run instead of out in front of the oven bank, with a
450 mm "walkway" no kitchen would have.

THE HEIGHT WAS KNOWABLE AND I DID NOT ASK. The stools are SP01 Michelle BAR stools,
published seat height 745 mm. A 745 seat belongs under a 1040-1100 counter, not a 900
bench - 900 would leave 155 mm of knee room. Feeding 1050 back through the same line
gives a 1385 mm walkway to the oven bank, which is what a kitchen has.

So the object I had already used to SCALE the room also carried the answer to where the
island sits, and I used it for one and guessed the other.
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
SLAB_LINE = (-0.03109, 1270.75)          # B4, the slab's top front edge, sub-pixel fit


def world_on_line(u, h):
    """Where the point at image column u on the slab's front-top edge sits, if the slab
    top is at height h."""
    m, b = SLAB_LINE
    v = m * u + b
    dv = v - PPY
    if dv <= 0:
        return None
    D = F * (RS.CAM_H - h) / dv
    lat = (u - PPX) / F * D
    return C + D * FWD + lat * RGT


def report(h):
    pts = {u: world_on_line(u, h) for u in (0, 500, 900, 1080)}
    front_y = float(np.mean([p[1] for p in pts.values()]))
    bull = pts[1080]
    gap = bull[0] - RS.TALL_DEPTH
    print(f"slab top {h:6.0f} mm ->  front edge Y {front_y:7.0f}   bullnose X {bull[0]:7.0f}"
          f"   walkway to the oven bank {gap:6.0f} mm")
    return front_y, bull[0], pts


if __name__ == "__main__":
    print("stool seat height (SPEC, SP01 Michelle bar) :", RS.STOOL_SEAT, "mm")
    print("knee clearance a 745 seat needs             : 290-350 mm -> counter 1035-1095\n")
    for h in (900, 940, 1000, 1050, 1100):
        report(h)
    print()
    fy, bx, pts = report(1050)
    print("\nand the pieces along the island, from the same line:")
    for u, lab in ((1080, "bullnose (far end)"), (900, "far drum outer"),
                   (500, "near drum outer"), (0, "leaves the frame")):
        print(f"  u={u:5d}  {lab:20s} X={pts[u][0]:7.0f}  Y={pts[u][1]:7.0f}")
