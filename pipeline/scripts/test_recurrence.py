"""test_recurrence.py — seeded suite for recurrence.py.

THE POSITIVE CONTROL COMES FIRST and it is round-trip: place two identical objects
at KNOWN world positions, project them with the same pinhole arithmetic, hand the
pixels back, and require the recovered heading and spacing to match what was put in.
A direction estimator that has never been run on an answer it knows is a direction
estimator nobody has tested — this repo has shipped that version before.

Then the real frame: the two bronze drums of TRN-003, whose pixel readings are in
`03_blockout/derive_island2.py`, must reproduce the 87.3 deg that overturned a
day of work.

Pure Python, no test framework:  python pipeline/scripts/test_recurrence.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recurrence as rc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


# ------------------------------------------------------- POSITIVE CONTROL (synthetic)
CAM = rc.Camera(f_px=4236.0, ppx=720.0, ppy=1031.0, height_mm=1421.0,
                yaw_deg=30.85, origin=(6971.0, 11801.0))


def project(cam, x, y, size_mm):
    """World floor point -> (u_centre, v_base, w_px). The inverse of what solve does."""
    dx, dy = x - cam.origin[0], y - cam.origin[1]
    depth = dx * cam.fwd[0] + dy * cam.fwd[1]
    lat = dx * cam.rgt[0] + dy * cam.rgt[1]
    return dict(u_centre=cam.ppx + cam.f * lat / depth,
                v_base=cam.ppy + cam.f * cam.h / depth,
                w_px=size_mm * cam.f / depth)


TRUE = [(2400.0, 3600.0), (2400.0, 4600.0)]        # two objects 1000 mm apart along +Y
inst = [project(CAM, x, y, 462.0) for x, y in TRUE]
r = rc.solve(CAM, inst, size_mm=462.0, name="synthetic")
check("POSITIVE CONTROL: the recovered heading is the one that was put in (90 deg)",
      abs(r["heading_deg"] - 90.0) < 0.05, f"{r['heading_deg']:.4f}")
check("...and the spacing round-trips to 1000 mm",
      abs(r["spacing_mm"] - 1000.0) < 1.0, f"{r['spacing_mm']:.2f}")
check("...and each world position round-trips to under a millimetre",
      all(math.hypot(g["x"] - t[0], g["y"] - t[1]) < 1.0
          for g, t in zip(r["instances"], TRUE)),
      [(round(g["x"], 1), round(g["y"], 1)) for g in r["instances"]])

# A direction the pipeline would have got WRONG: 0 deg, across the room.
inst2 = [project(CAM, x, y, 462.0) for x, y in ((1800.0, 4000.0), (3800.0, 4000.0))]
r2 = rc.solve(CAM, inst2, size_mm=462.0)
check("a row laid across the room recovers 0 deg, not 90",
      abs(r2["heading_deg"]) < 0.05 or abs(r2["heading_deg"] - 180) < 0.05,
      f"{r2['heading_deg']:.4f}")

# ------------------------------------------------------------- the self-check refuses
bad = [dict(inst[0]), dict(inst[1])]
bad[1]["w_px"] *= 1.25                       # the "same" object 25% wider at depth
try:
    rc.solve(CAM, bad, size_mm=462.0, name="mismatched")
    msg = ""
except rc.Unsupported as e:
    msg = str(e)
check("THE SELF-CHECK: two objects whose widths and bases disagree are REFUSED",
      "apart" in msg, msg)
check("...and the refusal names all three causes, not just one",
      "same object" in msg and "occluded" in msg, msg)
check("...and says an estimator that cannot fail is not an estimator",
      "not an estimator" in msg, msg)

# a base on the horizon has no depth
try:
    rc.solve(CAM, [dict(u_centre=700, v_base=1031.0), inst[1]])
    hz = ""
except rc.Unsupported as e:
    hz = str(e)
check("a contact row at the horizon is refused, not divided by zero",
      "not on the floor" in hz, hz)

try:
    rc.solve(CAM, [inst[0]])
    one = ""
except rc.Unsupported as e:
    one = str(e)
check("one instance is a position, not a direction", "at least two" in one, one)

# three instances that are not actually a row
try:
    rc.solve(CAM, [project(CAM, 2400, 3600, 462.0), project(CAM, 2900, 4100, 462.0),
                   project(CAM, 2400, 4600, 462.0)], size_mm=462.0, name="not a row")
    col = ""
except rc.Unsupported as e:
    col = str(e)
check("three instances off their own line are refused as not a repeated row",
      "not a repeated row" in col, col)

# ------------------------------------------------------------------ THE REAL DRUMS
# CORRECTED 2026-08-29, and this block was a live instance of the defect it tests for.
#
# It used to hardcode NEAR = (700 + 925)/2 with w_px = 225 and then assert "the drum
# diameter comes out near the 462 mm in room_spec". Both numbers were wrong and the test
# was pinning them: u = 925 is not an edge on the plate (the strongest gradient anywhere
# in u in [900,950] is 0.4-2.3 grey levels per px; at u = 891 it is 4.2-83.2), the near
# drum is 188.9 px wide not 225, and room_spec now says DRUM_R = 194, i.e. 389 mm dia.
# A test that asserts a refuted number does not merely fail to help - it makes the fix
# look like the regression.
#
# It also built the FAR instance by COMPUTING its width from the near drum's radius, which
# is exactly the circularity this module's own self-check exists to catch: fed that pair,
# solve() reported width_agreement = 0.0000%, an exact zero, because the quantity being
# checked had been manufactured from the quantity it was checked against. Both widths are
# now independent readings, and the agreement is a real 3.4%.
#
# THE READINGS AND THE EXPECTED SIZE NOW COME FROM room_spec ITSELF rather than being
# retyped here, so this test cannot drift away from the lane again.
_TRN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                    "training", "TRN-003_3dshaker-kitchen", "03_blockout")
sys.path.insert(0, _TRN)
try:
    import room_spec as _RS
    import derive_island2 as _DI2
except Exception as e:                                   # the lane is optional for CI
    print(f"  [--] the real-drum block needs training/TRN-003 ({e}) - skipped")
    _RS = None

if _RS is not None:
    DRUM_CAM = rc.Camera(f_px=4236.0, ppx=720.0, ppy=1031.0, height_mm=_RS.CAM_H,
                         yaw_deg=30.85,
                         origin=(_RS.CAM_TO_KITCHEN_WALL, _RS.CAM_Y))
    near_w = _DI2.NEAR["u_right"] - _DI2.NEAR["u_left"]
    NEAR = dict(u_centre=(_DI2.NEAR["u_left"] + _DI2.NEAR["u_right"]) / 2.0,
                v_base=_DI2.NEAR["v_base"], w_px=near_w)
    FAR = dict(u_centre=_DI2.FAR["u_left"] + _DI2.FAR_W_MEASURED / 2.0,
               v_base=_DI2.FAR["v_base"], w_px=_DI2.FAR_W_MEASURED)
    R = near_w * DRUM_CAM.depth_from_base(NEAR["v_base"]) / (2 * DRUM_CAM.f)
    rd = rc.solve(DRUM_CAM, [FAR, NEAR], size_mm=2 * R, name="bronze drums")
    check("THE REAL DRUMS reproduce the ~87 deg heading that overturned the build",
          86.0 < rd["heading_deg"] < 88.0, f"{rd['heading_deg']:.2f}")
    check("...and their spacing lands on the 930-990 mm the lane measured",
          930 < rd["spacing_mm"] < 990, f"{rd['spacing_mm']:.0f}")
    check("...and the diameter agrees with room_spec's OWN DRUM_R, not a typed number",
          abs(2 * R - 2 * _RS.DRUM_R) < 12, f"{2*R:.0f} vs spec {2*_RS.DRUM_R}")
    check("...and the far drum's width is an INDEPENDENT reading, so the self-check "
          "can actually fail (0.0000% would mean it cannot)",
          0.0005 < rd["instances"][0]["width_agreement"] < 0.05,
          f"{rd['instances'][0]['width_agreement']:.4f}")
    check("...and the implied vanishing column is nowhere near family B's 7814",
          rd["vp_u"] < 0, f"{rd['vp_u']:.0f}")

bad_rows = [r for r in RESULTS if not r[1]]
for name, ok, detail in RESULTS:
    print(f"  [{'ok' if ok else 'XX'}] {name}")
    if not ok and detail:
        print(f"        got: {detail}")
print(f"\n{len(RESULTS) - len(bad_rows)}/{len(RESULTS)} passed")
sys.exit(1 if bad_rows else 0)
