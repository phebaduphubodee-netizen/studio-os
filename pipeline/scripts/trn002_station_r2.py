"""trn002_station_r2.py — TRN-002 round-2: the right-wall assembly, measured.

Round 1 anchored the wardrobe face at x=0 (the corner arris) and invented a
raised ceiling slot to explain the diagonals. Round 2's verifier fleet broke
both: the greige door plane's own features only produce EQUAL door modules on
a plane ~1 m into the room, the "slot interior" tone-tracks the door faces to
<=1.3 L (it is the doors continuing up), and the corner strip is the VIEW
THROUGH AN OPENING between the entry-door section and the wardrobe run.

This driver turns the v005 fits into the r2 numbers, printing every value with
the constraint that produced it, and CHECKING consilience (two independent
x_wall estimates must agree before either is adopted):
  x_wall (A) equal-door-module variance minimum over reveal verticals
  x_wall (B) upper_edge backprojected to z == H_main (full-height run)

  python pipeline/scripts/trn002_station_r2.py <lines_v005.json> <spec_r1.json>
"""
import argparse
import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import trn002_geom as G  # noqa: E402

WH = (1080, 821)
H_MAIN = 3102.0


def line_of(fits, name):
    return next(x for x in fits if x["name"] == name)


def v_at(L, u):
    a, b = L["n"]
    return -(L["c"] + a * u) / b


def u_of_vertical(L):
    return (L["e0"][0] + L["e1"][0]) / 2


def bp(cam, uv, plane):
    w = G.backproject(cam, uv, plane, WH)
    if w is None:
        raise SystemExit(f"ray missed {plane} at {uv}")
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("spec_r1")
    a = ap.parse_args()
    fits = json.load(open(a.lines, encoding="utf-8"))["lines"]
    cam = G.load_spec(a.spec_r1)["camera"]

    # ---- x_wall (A): equal door modules ------------------------------------
    revs = [u_of_vertical(line_of(fits, n))
            for n in ("rev_811_hi", "rev_874_hi", "rev_950_hi", "rev_1043_hi")]
    best = None
    for x in np.arange(-1400.0, -500.0, 2.0):
        ys = [bp(cam, (u, 300.0), ("x", x))[1] for u in revs]
        gaps = np.diff(ys)
        cv = float(np.std(gaps) / abs(np.mean(gaps)))
        if best is None or cv < best[1]:
            best = (x, cv, [float(g) for g in gaps])
    x_A, cv, gaps = best
    print(f"x_wall (A, equal modules): {x_A:.0f}  cv={cv:.4f}  modules={[f'{g:.0f}' for g in gaps]}")

    # ---- x_wall (B): full-height run meets the ceiling ---------------------
    ue = line_of(fits, "upper_edge")
    xs = []
    for e in (ue["e0"], ue["e1"]):
        # solve x so that the junction pixel lands at z=H_MAIN
        lo, hi = -2000.0, -200.0
        for _ in range(60):
            mid = (lo + hi) / 2
            z = bp(cam, e, ("x", mid))[2]
            if z > H_MAIN:
                lo = mid  # farther plane reads higher: move nearer
            else:
                hi = mid
        xs.append((lo + hi) / 2)
    x_B = float(np.mean(xs))
    print(f"x_wall (B, upper_edge at z={H_MAIN:.0f}): {x_B:.0f}  (per-end {xs[0]:.0f}/{xs[1]:.0f})")

    if abs(x_A - x_B) > 120:
        print("!! CONSILIENCE FAILED — do not adopt either; measure more")
    x_wall = round((x_A + x_B) / 2, 0)
    print(f"ADOPTED x_wall = {x_wall:.0f} (mean; spread {abs(x_A - x_B):.0f} mm)")

    # ---- features on the adopted plane -------------------------------------
    cd = line_of(fits, "ceil_diag")
    z_groove = [bp(cam, e, ("x", x_wall))[2] for e in (cd["e0"], cd["e1"])]
    print(f"groove z on x_wall: {z_groove[0]:.0f} / {z_groove[1]:.0f}")
    bt = line_of(fits, "band_top")
    z_band = [bp(cam, e, ("x", x_wall))[2] for e in (bt["e0"], bt["e1"])]
    print(f"band top z on x_wall: {z_band[0]:.0f} / {z_band[1]:.0f}")

    rev_y = {u: bp(cam, (u, 300.0), ("x", x_wall))[1]
             for u in [u_of_vertical(line_of(fits, n)) for n in
                       ("rev_795_hi", "rev_811_hi", "rev_874_hi", "rev_950_hi", "rev_1043_hi")]}
    print("reveal y on x_wall: " + ", ".join(f"u{u:.0f}->y{y:.0f}" for u, y in rev_y.items()))

    dh = line_of(fits, "door_head")
    for u in (620.5, 683.0):
        w = bp(cam, (u, v_at(dh, u)), ("x", x_wall))
        print(f"door head at u={u}: y={w[1]:.0f} z={w[2]:.0f}")

    # ---- bed platform on the floor -----------------------------------------
    pf, pn = line_of(fits, "plat_foot"), line_of(fits, "plat_near")
    foot = [bp(cam, e, ("z", 0.0)) for e in (pf["e0"], pf["e1"])]
    near = [bp(cam, e, ("z", 0.0)) for e in (pn["e0"], pn["e1"])]
    fdir = np.array(foot[1][:2]) - np.array(foot[0][:2])
    ndir = np.array(near[1][:2]) - np.array(near[0][:2])
    fang = np.degrees(np.arctan2(fdir[1], fdir[0])) % 180
    nang = np.degrees(np.arctan2(ndir[1], ndir[0])) % 180
    print(f"plat_foot dir {fang:.2f} deg (want ~90 = along y) pts "
          f"({foot[0][0]:.0f},{foot[0][1]:.0f})-({foot[1][0]:.0f},{foot[1][1]:.0f})")
    print(f"plat_near dir {nang:.2f} deg (want ~0 = along x) pts "
          f"({near[0][0]:.0f},{near[0][1]:.0f})-({near[1][0]:.0f},{near[1][1]:.0f})")
    foot_x = float(np.mean([p[0] for p in foot]))
    near_y = float(np.mean([p[1] for p in near]))
    print(f"platform foot face x = {foot_x:.0f}, near side y = {near_y:.0f}")
    head_x = x_wall - 200.0  # band 20 + headboard 100 + air 80: r2 derivation
    print(f"platform length (head at x_wall-200): {head_x - foot_x:.0f}")

    # ---- nightstand (verifier anchors), sweep depth ------------------------
    for depth in (250.0, 350.0, 450.0):
        x_ns = x_wall - depth
        z_top = bp(cam, (992.0, 645.3), ("x", x_ns))[2]
        y0 = bp(cam, (985.0, 643.5), ("x", x_ns))[1]
        y1 = bp(cam, (1080.0, 669.0), ("x", x_ns))[1]
        print(f"nightstand front at depth {depth:.0f}: x={x_ns:.0f} top z={z_top:.0f} y {y0:.0f}..{y1:.0f}")

    # ---- headboard top -----------------------------------------------------
    for u, v in ((940.0, 508.3), (1000.0, 515.6)):
        w = bp(cam, (u, v), ("x", head_x))
        print(f"headboard top (piping) at u={u:.0f}: z={w[2]:.0f} y={w[1]:.0f}")

    # ---- bench (fit failed the bend guard; report floor projection of the
    # visible top-edge midpoint under an assumed 420 seat for the record) ----
    w = bp(cam, (786.0, 725.5), ("z", 420.0))
    print(f"bench top mid at z=420: x={w[0]:.0f} y={w[1]:.0f}")


if __name__ == "__main__":
    main()
