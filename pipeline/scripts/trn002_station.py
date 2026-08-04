"""trn002_station.py — TRN-002 round-1 station solve + room measurement.
PURE python (no bpy). Consumes the v004 line fits; emits the r1 spec.

  python pipeline/scripts/trn002_station.py <lines_v004.json> --out <spec.json>

DECLARED GAUGES (written here so the sweep that tests them has a single place
to vary; TRN-001 paid nine rounds for a room height nobody re-derived):
  G1  door leaf 2000 mm + lever axis 1030 mm  ->  camera z = 1305 mm
      (the camera-lens agent's anchor: two standards on ONE 3D vertical of the
       nook door; independent of any wall plane's depth)
  G2  wardrobe body depth 600 mm (standard casework; fixes the right
      structural wall / slot inner face at x=+600)
Everything else in the spec is MEASURED through the solved camera, and each
measured value below prints with the pixel it came from.
"""
import argparse
import json
import math
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
import trn002_geom as G  # noqa: E402

WH = (1080, 821)
CAM_Z = 1305.0          # G1
WARDROBE_D = 600.0      # G2


def line_of(fits, name):
    L = next(x for x in fits if x["name"] == name)
    if not L.get("ok"):
        raise SystemExit(f"line {name} did not fit")
    return L


def isect(L1, L2):
    a1, b1 = L1["n"]
    a2, b2 = L2["n"]
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        raise SystemExit(f"parallel: {L1['name']} x {L2['name']}")
    u = (-L1["c"] * b2 + L2["c"] * b1) / det
    v = (-a1 * L2["c"] + a2 * L1["c"]) / det
    return (u, v)


def v_at(L, u):
    a, b = L["n"]
    return -(L["c"] + a * u) / b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cam", default=None, help="camera_v004.json (pins)")
    a = ap.parse_args()
    data = json.load(open(a.lines, encoding="utf-8"))
    fits = data["lines"]
    blobs = [b for b in data.get("downlight_blobs", []) if b["v"] < 200 or b["u"] > 150]

    cam_pins = json.load(open(a.cam, encoding="utf-8")) if a.cam else {}
    pins = {"yaw_deg": cam_pins.get("yaw_deg", 20.0417),
            "focal_mm": cam_pins.get("focal_mm", 38.841),
            "shift_x": 0.0,
            "shift_y": cam_pins.get("shift_y", -0.002961)}
    v_h = cam_pins.get("horizon_v", 407.3)

    jn = line_of(fits, "junction_true")
    sill = line_of(fits, "sill")
    corner = line_of(fits, "corner_v")
    # ---- ceiling height from the wall's own ratio (depth cancels) ----------
    x_probe = 200.0
    v_c, v_f = v_at(jn, x_probe), v_at(sill, x_probe)
    ratio = (v_f - v_h) / (v_f - v_c)
    H_main = CAM_Z / ratio
    print(f"ratio anchor @u={x_probe:.0f}: v_ceil={v_c:.1f} v_floor={v_f:.1f} "
          f"v_h={v_h:.1f}  h/H={ratio:.4f}  ->  H_main={H_main:.0f} mm")

    # ---- station from the back-right corner anchor --------------------------
    cpx = isect(corner, jn)
    cam = G.station_from_anchor(pins, cpx, (0.0, 0.0, H_main), CAM_Z, WH)
    print(f"corner anchor px=({cpx[0]:.1f},{cpx[1]:.1f}) -> camera "
          f"({cam['x_mm']:.0f}, {cam['y_mm']:.0f}, {cam['z_mm']:.0f})")

    def bp(uv, plane, label):
        w = G.backproject(cam, uv, plane, WH)
        if w is None:
            print(f"  {label:28s} RAY MISSED")
            return None
        print(f"  {label:28s} px({uv[0]:7.1f},{uv[1]:7.1f}) {plane[0]}={plane[1]:<7.0f}"
              f" -> ({w[0]:8.1f},{w[1]:8.1f},{w[2]:8.1f})")
        return w

    print("\n== deep wall y=0 ==")
    art_t, art_b = line_of(fits, "art_top"), line_of(fits, "art_bot")
    art_l, art_r = line_of(fits, "art_L"), line_of(fits, "art_R")
    pht, phb = line_of(fits, "part_head_top"), line_of(fits, "part_head_bot")
    pfl, psr = line_of(fits, "part_frame_L"), line_of(fits, "part_slide_R")
    W = {}
    W["art_TL"] = bp(isect(art_l, art_t), ("y", 0.0), "art_TL")
    W["art_TR"] = bp(isect(art_r, art_t), ("y", 0.0), "art_TR")
    W["art_BL"] = bp(isect(art_l, art_b), ("y", 0.0), "art_BL")
    W["art_BR"] = bp(isect(art_r, art_b), ("y", 0.0), "art_BR")
    W["ph_TL"] = bp(isect(pfl, pht), ("y", 0.0), "partition head TL")
    W["ph_TR"] = bp((399.0, v_at(pht, 399.0)), ("y", 0.0), "partition head TR(u=399)")
    W["ph_bot_L"] = bp((160.0, v_at(phb, 160.0)), ("y", 0.0), "head bottom @u=160")
    W["sill_L"] = bp(isect(pfl, sill), ("y", 0.0), "sill @ frame L")
    W["slide_R"] = bp((277.0, 500.0), ("y", 0.0), "slider stile @v=500")
    W["corner_flr"] = bp((cpx[0], v_at(sill, cpx[0])), ("y", 0.0), "corner @ sill line")

    print("\n== wardrobe face x=0 ==")
    cd = line_of(fits, "ceil_diag")
    bt = line_of(fits, "band_top")
    W["slot_far"] = bp((cd["e0"][0], cd["e0"][1]), ("x", 0.0), "slot arris far end")
    W["slot_near"] = bp((cd["e1"][0], cd["e1"][1]), ("x", 0.0), "slot arris near end")
    W["band_far"] = bp((bt["e0"][0], bt["e0"][1]), ("x", 0.0), "band top far end")
    W["band_near"] = bp((bt["e1"][0], bt["e1"][1]), ("x", 0.0), "band top near end")
    for u_rev in (787.0, 855.0, 920.0, 985.0):
        W[f"rev_{u_rev:.0f}"] = bp((u_rev, 300.0), ("x", 0.0), f"reveal u={u_rev:.0f} @v=300")

    print("\n== raised slot / right wall x=+600 (G2) ==")
    ud = line_of(fits, "upper_diag")
    W["slot_ceil_a"] = bp((ud["e0"][0], ud["e0"][1]), ("x", WARDROBE_D), "upper_diag far")
    W["slot_ceil_b"] = bp((ud["e1"][0], ud["e1"][1]), ("x", WARDROBE_D), "upper_diag near")

    print("\n== nook door (plane x resolved from its own two standards) ==")
    dh = line_of(fits, "door_head")
    u_ref = 680.0
    v_head = v_at(dh, u_ref)
    v_lever = 451.0  # camera-lens agent probe @ x~680
    d_axis = (WH[0] * pins["focal_mm"] / G.SENSOR_MM) * (2000.0 - 1030.0) / (v_lever - v_head)
    fwd, right, _ = G.cam_basis(pins["yaw_deg"])
    f_px = WH[0] * pins["focal_mm"] / G.SENSOR_MM
    aa = (u_ref - WH[0] * 0.5) / f_px
    d = (fwd[0] + aa * right[0], fwd[1] + aa * right[1])
    # walk the axis-depth out along this pixel's ray to find the door plane x
    t = d_axis / (d[0] * fwd[0] + d[1] * fwd[1])
    x_door = cam["x_mm"] + t * d[0]
    y_door = cam["y_mm"] + t * d[1]
    print(f"  door plane axis-depth {d_axis:.0f} -> x_door={x_door:.1f} (y there {y_door:.1f})")
    W["door_head_near"] = bp((683.0, v_at(dh, 683.0)), ("x", x_door), "door head near")
    W["door_head_far"] = bp((620.5, v_at(dh, 620.5)), ("x", x_door), "door head far")

    print("\n== ceiling z=H_main: downlights ==")
    DL = []
    for b in blobs:
        w = bp((b["u"], b["v"]), ("z", H_main), f"downlight ({b['u']:.0f},{b['v']:.0f})")
        if w:
            DL.append([round(w[0], 1), round(w[1], 1)])

    print("\n== floor z=0: contacts ==")
    W["rug_corner"] = bp((260.0, 660.0), ("z", 0.0), "rug far-left corner")
    W["rug_nearL"] = bp((345.0, 817.0), ("z", 0.0), "rug left edge near")
    W["bed_base_nearL"] = bp((405.0, 790.0), ("z", 0.0), "bed base corner (round)")
    W["bed_base_footR"] = bp((578.0, 817.0), ("z", 0.0), "bed base foot edge")
    W["chair_foot_F"] = bp((178.0, 623.0), ("z", 0.0), "chair front leg foot")
    W["chair_foot_R"] = bp((244.0, 610.0), ("z", 0.0), "chair rear leg foot")
    W["bench_face"] = bp((906.0, 750.0), ("z", 400.0), "bench top edge z=400(assumed)")

    out = {
        "image": {"w": WH[0], "h": WH[1]},
        "camera": {**{k: round(v, 6) if isinstance(v, float) else v for k, v in cam.items()},
                   "_solved": "v004 VP pins + corner anchor + G1 gauge 2026-08-04"},
        "gauges": {"G1": "door leaf 2000 + lever 1030 -> cam z 1305",
                   "G2": f"wardrobe depth {WARDROBE_D:.0f}",
                   "H_main_mm": round(H_main, 1)},
        "world": {k: [round(c, 1) for c in v] for k, v in W.items() if v},
        "downlights_xy": DL,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
