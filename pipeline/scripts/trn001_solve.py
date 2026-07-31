"""trn001_solve.py — TRN-001 camera solve: PURE python (no bpy), scipy.

The --quick rung of camera matching (R5 applied to perspective): a least-squares
fit of the 6 camera unknowns (x, y, z, yaw, focal, shift_y) against measured
target-image landmark pixels, at ~zero cost, BEFORE any render is spent.
Dimensions stay FIXED during a solve — if the residual pattern says a dimension
is wrong (paired left/right residuals pointing outward = element too narrow,
etc.), the human adjusts the spec and re-solves; the solver never invents mm.

  python pipeline/scripts/trn001_solve.py <spec.json> <target_landmarks.json> \
      [--write <solved_spec.json>]

target_landmarks.json: {"landmarks": [{"name","u","v","confidence"}, ...]}
(2048-space, reconciled from the independent measurers). Confidence weights the
fit. Landmarks the geometry model does not carry (occlusion-dependent ones)
are ignored with a note.
"""
import argparse
import json
import math
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import trn001_geom as G  # noqa: E402

RES = 2048
PARAMS = ("x_mm", "y_mm", "z_mm", "yaw_deg", "focal_mm", "shift_y")
BOUNDS_LO = (-3000.0, -9000.0, 600.0, -30.0, 14.0, -0.5)
BOUNDS_HI = (+3000.0, -1200.0, 2200.0, +30.0, 60.0, +0.5)


def solve(spec, targets, pins=None):
    """pins = {param: value} — parameters held OUT of the fit (e.g. shift_y=0
    when the VP horizon evidence is stronger than the landmark cloud; frees the
    solve from the z<->shift_y vertical degeneracy of pitch-0 cameras)."""
    pins = pins or {}
    free = [p for p in PARAMS if p not in pins]
    names = [t["name"] for t in targets]
    known = G.landmarks_3d(spec)
    used = [t for t in targets if t["name"] in known]
    skipped = sorted(set(names) - set(t["name"] for t in used))
    if skipped:
        print(f"note: {len(skipped)} LOOK-only landmarks not in the solve: {skipped}")
    if pins:
        print(f"pinned: {pins}")

    uv = np.array([[t["u"], t["v"]] for t in used])
    wts = np.repeat(np.sqrt([max(t.get("confidence", 1.0), 0.05) for t in used]), 2)

    def mkcam(x):
        cam = dict(zip(free, x))
        cam.update(pins)
        cam["shift_x"] = spec["camera"].get("shift_x", 0.0)
        return cam

    def resid(x):
        cam = mkcam(x)
        rows = []
        for t, tgt in zip(used, uv):
            pr = G.project(cam, known[t["name"]], res=RES)
            if pr is None:
                rows.extend([1e4, 1e4])
            else:
                rows.extend([pr[0] - tgt[0], pr[1] - tgt[1]])
        return np.array(rows) * wts

    lo = [BOUNDS_LO[PARAMS.index(p)] for p in free]
    hi = [BOUNDS_HI[PARAMS.index(p)] for p in free]
    x0 = [min(max(spec["camera"][p], l), h) for p, l, h in zip(free, lo, hi)]
    fit = least_squares(resid, x0, bounds=(lo, hi), loss="soft_l1", f_scale=8.0)
    cam = mkcam(fit.x)

    print("\nsolved camera:")
    for p in PARAMS:
        print(f"  {p:9s} = {cam[p]:10.2f}")
    print("\nper-landmark residuals (px @2048 | local world-mm equivalent):")
    errs = []
    for t in used:
        p3 = known[t["name"]]
        pr = G.project(cam, p3, res=RES)
        du, dv = pr[0] - t["u"], pr[1] - t["v"]
        d = math.hypot(du, dv)
        errs.append(d)
        # local image sensitivity: px per mm of world x / world z at this point
        px_dx = (G.project(cam, (p3[0] + 10, p3[1], p3[2]), res=RES)[0] - pr[0]) / 10
        px_dz = (G.project(cam, (p3[0], p3[1], p3[2] + 10), res=RES)[1] - pr[1]) / 10
        mmx = du / px_dx if abs(px_dx) > 1e-9 else float("nan")
        mmz = dv / px_dz if abs(px_dz) > 1e-9 else float("nan")
        print(f"  {t['name']:18s} du={du:+7.1f} dv={dv:+7.1f}  |{d:6.1f}|  "
              f"~mm: x{mmx:+7.0f} z{mmz:+7.0f}  conf={t.get('confidence', 1):.2f}")
    print(f"\nmean={np.mean(errs):.1f}px  median={np.median(errs):.1f}px  "
          f"max={np.max(errs):.1f}px  (frame = {RES}px)")
    return cam, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("targets")
    ap.add_argument("--write", default=None, help="write spec with solved camera")
    ap.add_argument("--pin", action="append", default=[],
                    help="name=value: hold a camera param out of the fit")
    a = ap.parse_args()
    spec = G.load_spec(a.spec)
    targets = json.load(open(a.targets, encoding="utf-8"))["landmarks"]
    pins = {}
    for p in a.pin:
        k, v = p.split("=")
        pins[k] = float(v)
    cam, _ = solve(spec, targets, pins=pins)
    if a.write:
        spec["camera"].update({k: float(v) for k, v in cam.items()})
        with open(a.write, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=1)
        print(f"wrote {a.write}")


if __name__ == "__main__":
    main()
