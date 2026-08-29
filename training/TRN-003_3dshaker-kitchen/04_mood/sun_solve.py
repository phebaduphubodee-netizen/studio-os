#!/usr/bin/env python3
"""SUPERSEDED 2026-08-29 - THIS FILE'S ANSWER IS REFUTED. Kept because the way it was
wrong is the lesson, and because a deleted file cannot warn anybody.

WHAT IT RETURNS: azimuth 21.58 deg, from four sunlight-band edges on the floor.
WHAT IS TRUE:    azimuth 92.3 +-0.5 deg, elevation 18.3 +-0.65, measured by GNOMON from
                 four bar-stool hoop legs. The measurement lives in
                 04_mood/palette-from-plate.json -> light.sun_measurement.

THREE THINGS WRONG HERE, and each one is a shape worth carrying:

1. IT AVERAGES A DISAGREEMENT. The four edges return 22.12 / 18.07 / 25.82 / 20.29 - a
   7.75 deg spread - and this file takes the mean and reports it with no refusal. Four
   lines that are supposed to be PARALLEL disagreeing by 7.75 deg is a finding, not a
   dataset. The gnomon's four legs agree to 0.55 deg, which is what agreement looks like.

2. ITS OWN rms SAYS NOT TO BELIEVE IT. The four edge fits carry rms 6.3-10.6 px. On the
   same plate and the same floor plane, a clean fit runs rms 0.11 px - and the positive
   control at that quality (the cabinet toe/floor junction, a world line along +Y whose
   true heading is 90.000 by construction) unprojects to 90.214 deg. rms is what tells
   you which fit to believe, and this file never looks at its own.

3. IT BREAKS THE 180 DEG AMBIGUITY WITH A SENTENCE. "the shadows fall away from the
   glazing, so the sun travels along +this heading" is an assertion. The gnomon broke it
   with pixels: along one ray the floor is CONTINUOUSLY dark from the base outward; along
   the opposite ray it is dark only in three short intervals sitting exactly at the other
   three legs' measured bases, and bright floor beyond the last one. A cast shadow is
   continuous and attached to its caster; a row of legs is not.

AND THE REFUTATION THAT NEEDED NO NEW MEASUREMENT AT ALL: at 21.58 deg, the plan run from
the glazing (y=-432) to a lit stool base at y=4219 is 12645 mm, of which 11759 mm is in
+X - so the ray must cross the glazing at x = -8615 mm, missing the glass by 8.4 m, FOR
EVERY ELEVATION. That is why renders at this azimuth put no beam in frame, and why the
previous round turned the azimuth into a dial instead of doubting the number. The lane had
the disproof in its own hands for a day and read it as a rendering problem.

--- the original docstring follows, unedited ---
"""
"""sun_solve.py - the sun's AZIMUTH read off the plate's own floor shadows.

The tutorial says "adjust its rotation to have the shadows in similar way as in our
reference" and turns the dial until it looks close. A direction is not something an
amount can confirm, so here it is measured instead: four sunlight-band edges on the
floor are fitted sub-pixel, un-projected onto the floor plane through the solved
camera, and their world headings averaged. Parallel shadow edges on a flat floor ARE
the sun's plan direction; nothing else about the room is needed.

Elevation is deliberately NOT guessed here. It is left as the single remaining unknown
for the render loop, because the plate gives no vertical-object-to-shadow-tip pair I
can identify with confidence, and inventing one would be the defect this studio has a
rule about.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "03_blockout"))
import room_spec as RS                                                   # noqa: E402

CAM = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
S = CAM["solution"]
F_PX = S["f_px"]; PPX, PPY = S["principal_point_px"]
YAW = math.radians(S["yaw_from_kitchen_wall_deg"])
FWD = np.array([-math.sin(YAW), -math.cos(YAW), 0.0])
RGT = np.array([FWD[1], -FWD[0], 0.0])
UP = np.array([0.0, 0.0, 1.0])
C = np.array([RS.CAM_TO_KITCHEN_WALL, RS.CAM_Y, RS.CAM_H])

SHADOW_EDGES = {                      # sub-pixel fits from edgefit.py, y = m*x + b
    "S1": (-0.22784, 1923.09), "S2": (-0.23880, 2084.64),
    "S3": (-0.23588, 1857.91), "S4": (-0.20058, 1859.92),
}


def to_floor(u, v):
    d = RGT * (u - PPX) + UP * (-(v - PPY)) + FWD * F_PX
    if abs(d[2]) < 1e-9:
        return None
    t = -C[2] / d[2]
    return C + t * d if t > 0 else None


def main():
    heads = []
    for name, (m, b) in SHADOW_EDGES.items():
        u0, u1 = 250.0, 1400.0
        P0, P1 = to_floor(u0, m * u0 + b), to_floor(u1, m * u1 + b)
        if P0 is None or P1 is None:
            print(f"{name}: behind the camera"); continue
        d = P1 - P0
        az = math.degrees(math.atan2(d[1], d[0])) % 180.0
        heads.append(az)
        print(f"{name}: floor {P0[0]:8.0f},{P0[1]:8.0f} -> {P1[0]:8.0f},{P1[1]:8.0f} mm"
              f"   heading {az:6.2f} deg  (len {np.linalg.norm(d[:2]):.0f} mm)")
    a = np.array(heads)
    mean = float(a.mean()); spread = float(a.max() - a.min())
    print(f"\nsun azimuth line  : {mean:.2f} deg in plan   (spread across 4 edges "
          f"{spread:.2f} deg)")
    print("the shadows fall away from the glazing, so the sun travels along +this heading")
    out = dict(azimuth_plan_deg=mean, spread_deg=spread, edges=heads,
               elevation_deg=None,
               note=("azimuth measured; elevation left open on purpose - see docstring"))
    json.dump(out, open(os.path.join(HERE, "sun-from-plate.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    main()
