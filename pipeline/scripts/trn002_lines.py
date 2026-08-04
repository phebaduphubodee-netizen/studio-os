"""trn002_lines.py — TRN-002 line instrument: corridor subpixel edge fits,
VP solve, camera pins. PURE python (no bpy), numpy + PIL only.

The eyeball reads that seeded this tool contradicted each other three ways in
one sitting (a rounded console end read as a straight edge pointed at a VP no
room axis owns), so the rule here is: a human names WHICH edge and roughly
WHERE; the instrument decides the line, and a straightness guard refuses
curved features instead of averaging them into a lie.

  python pipeline/scripts/trn002_lines.py <target_image> <seeds.json> \
      --out <dir> [--tag v001]

seeds.json: {"seeds": [{"name", "p0": [u,v], "p1": [u,v],
                        "family": "x|y|v|?"}, ...]}
family is a HINT for reporting; the VP consistency check is what assigns
membership (a hint is never evidence).

Outputs (all under --out, which must live in _private for client imagery):
  lines_<tag>.json    fitted lines, ridge stats, per-line VP residuals
  overlay_<tag>.png   fitted lines drawn over the target (LOOK rung)
  camera_<tag>.json   horizon, VPs, f_px, focal_mm, yaw_deg, shift_y
                      (pitch-0 two-VP model; roll from the vertical family)

Camera model (matches trn001_geom.project conventions, landscape-aware):
  u = W/2 + f_px*(xc/depth) + W*shift_x
  v = H/2 - f_px*(dz/depth) + W*shift_y      f_px = W * focal_mm / 36.0
  x-family (along back wall, dir (1,0,0)):  u_A = cx + f_px*cot(yaw)
  y-family (room depth,      dir (0,1,0)):  u_B = cx - f_px*tan(yaw)
  => (u_A - cx)(u_B - cx) = -f_px^2 ; horizon v_h = H/2 + W*shift_y
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

SENSOR_MM = 36.0


# ------------------------------------------------------------ sampling ----

def to_gray(im):
    return np.asarray(im.convert("L"), dtype=np.float64)


def bilinear(g, x, y):
    h, w = g.shape
    x = np.clip(x, 0.0, w - 1.001)
    y = np.clip(y, 0.0, h - 1.001)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    return ((g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx) * (1 - fy)
            + (g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx) * fy)


def ridge_points(g, p0, p1, half=6.0, step=2.0, srate=0.25, mode="edge"):
    """March along the seed segment; at each station find the subpixel extremum
    across the corridor. mode: 'edge' = |directional derivative| peak (a value
    step); 'dark'/'light' = value extremum (a thin STROKE — picture-frame bar,
    shadow-gap reveal — which an edge detector sees as TWO peaks and drops as
    ambiguous). Returns (pts Nx2, weights N, ambiguous_frac). A station is
    AMBIGUOUS (dropped) when a second peak within 75% of the max sits >1.5 px
    away — a corridor holding two features is a corridor whose answer depends
    on the seed, which is the eyeball-error channel this tool exists to close."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    length = float(np.hypot(*d))
    if length < 8:
        return np.zeros((0, 2)), np.zeros(0), 1.0
    t_hat = d / length
    n_hat = np.array([-t_hat[1], t_hat[0]])
    n_st = max(int(length / step) + 1, 5)
    ss = np.arange(-half, half + 1e-9, srate)
    pts, wts, ambig = [], [], 0
    for i in range(n_st):
        c = p0 + t_hat * (length * i / (n_st - 1))
        xs = c[0] + ss * n_hat[0]
        ys = c[1] + ss * n_hat[1]
        prof = bilinear(g, xs, ys)
        if mode == "edge":
            mag = np.abs(np.gradient(prof, srate))
        elif mode == "dark":
            mag = prof.max() - prof
        else:  # light
            mag = prof - prof.min()
        j = int(np.argmax(mag))
        if j == 0 or j == len(ss) - 1:
            continue
        # second-peak ambiguity test (local maxima only, away from the best)
        loc = (mag[1:-1] >= mag[:-2]) & (mag[1:-1] >= mag[2:])
        idx = np.nonzero(loc)[0] + 1
        sep = 1.5 if mode == "edge" else 3.0
        idx = idx[np.abs(ss[idx] - ss[j]) > sep]
        if len(idx) and mag[idx].max() >= 0.75 * mag[j]:
            ambig += 1
            continue
        # parabolic subpixel refinement
        den = mag[j - 1] - 2 * mag[j] + mag[j + 1]
        off = 0.0 if abs(den) < 1e-12 else 0.5 * (mag[j - 1] - mag[j + 1]) / den
        s = ss[j] + np.clip(off, -1, 1) * srate
        pts.append(c + s * n_hat)
        wts.append(mag[j])
    pts = np.asarray(pts) if pts else np.zeros((0, 2))
    return pts, np.asarray(wts), ambig / max(n_st, 1)


def fit_line(pts, wts, iters=4):
    """IRLS total-least-squares line: returns (n_hat(2), c) with n.p + c = 0,
    rms of inliers, inlier mask (Tukey c=2.5px)."""
    w = wts.copy()
    keep = np.ones(len(pts), bool)
    n, c = None, None
    for _ in range(iters):
        if keep.sum() < 5:
            return None
        P = pts[keep]
        W = w[keep] / w[keep].sum()
        mu = (P * W[:, None]).sum(0)
        Q = (P - mu) * np.sqrt(W)[:, None]
        _, _, vt = np.linalg.svd(Q, full_matrices=False)
        n = vt[-1]
        c = -float(n @ mu)
        r = pts @ n + c
        tuk = np.clip(1 - (r / 2.5) ** 2, 0, None) ** 2
        keep = np.abs(r) < 2.5
        w = wts * tuk
    r = pts[keep] @ n + c
    rms = float(np.sqrt((r ** 2).mean())) if keep.sum() else float("inf")
    return n, c, rms, keep


def fit_seed(g, seed):
    pts, wts, ambig = ridge_points(g, seed["p0"], seed["p1"],
                                   half=float(seed.get("half", 6.0)),
                                   mode=seed.get("mode", "edge"))
    if len(pts) < 5:
        return {**seed, "ok": False, "why": f"ridge starved (n={len(pts)}, ambig={ambig:.2f})"}
    out = fit_line(pts, wts)
    if out is None:
        return {**seed, "ok": False, "why": "IRLS collapsed"}
    n, c, rms, keep = out
    # STRAIGHTNESS GUARD: split-half angle check. A curve fits one line with a
    # small rms if it is shallow; two half-fits disagreeing in angle expose it.
    order = np.argsort(pts[keep] @ np.array([-n[1], n[0]]))
    P = pts[keep][order]
    W = wts[keep][order]
    half = len(P) // 2
    angs = []
    for Ph, Wh in ((P[:half], W[:half]), (P[half:], W[half:])):
        o = fit_line(Ph, Wh, iters=2)
        if o is None:
            angs = None
            break
        angs.append(math.degrees(math.atan2(o[0][0], -o[0][1])) % 180.0)
    bend = None
    if angs:
        bend = abs(angs[0] - angs[1])
        bend = min(bend, 180 - bend)
    ends_t = pts[keep] @ np.array([-n[1], n[0]])
    e0 = pts[keep][np.argmin(ends_t)]
    e1 = pts[keep][np.argmax(ends_t)]
    return {**seed, "ok": True, "n": [float(n[0]), float(n[1])], "c": float(c),
            "rms": round(rms, 3), "n_pts": int(keep.sum()),
            "ambig_frac": round(ambig, 3),
            "bend_deg": None if bend is None else round(bend, 3),
            "e0": [round(float(e0[0]), 2), round(float(e0[1]), 2)],
            "e1": [round(float(e1[0]), 2), round(float(e1[1]), 2)],
            "angle_deg": round(math.degrees(math.atan2(-n[0], n[1])) % 180.0, 3)}


BEND_MAX = 0.8    # deg between half-fits before a feature is called curved
RMS_MAX = 1.2     # px
RMS_CAP = 2.0     # a per-seed rms_max may relax the default, never past this


def usable(L):
    rms_max = min(float(L.get("rms_max", RMS_MAX)), RMS_CAP)
    return (L.get("ok") and L["rms"] <= rms_max and L["n_pts"] >= 8
            and (L["bend_deg"] is None or L["bend_deg"] <= BEND_MAX))


# ------------------------------------------------------------ VP solve ----

def line_homog(L):
    return np.array([L["n"][0], L["n"][1], L["c"]])


def vp_from_lines(lines):
    """Homogeneous LSQ vanishing point of >=2 fitted lines."""
    A = np.stack([line_homog(L) for L in lines])
    _, _, vt = np.linalg.svd(A)
    v = vt[-1]
    if abs(v[2]) < 1e-9:
        return None  # point at infinity: caller handles
    return v[:2] / v[2]


def vp_residual(L, vp):
    """Angular residual in DEGREES: the angle between the fitted line and the
    line joining the fitted segment's midpoint to the candidate VP. A fixed
    pixel tolerance is meaningless at a 3000-px-distant VP — a 0.1 deg angular
    error already puts the line tens of px from the point."""
    mid = np.array([(L["e0"][0] + L["e1"][0]) / 2, (L["e0"][1] + L["e1"][1]) / 2])
    to_vp = np.asarray(vp) - mid
    d = float(np.hypot(*to_vp))
    if d < 1e-9:
        return 0.0
    s = abs(float(to_vp @ np.array(L["n"]))) / d
    return math.degrees(math.asin(min(s, 1.0)))


ANG_TOL = 0.35  # deg


def classify(lines, W, H, f_lo_px, f_hi_px, tol=ANG_TOL):
    """RANSAC over pairs of non-vertical lines -> two conjugate VPs on a level
    horizon. Verticals (angle within 2 deg of 90) are held out and used for
    the roll/pitch report. Returns dict or None."""
    cx = W / 2.0
    horiz = [L for L in lines if usable(L) and min(abs(L["angle_deg"] - 90), abs(L["angle_deg"] + 90)) > 2.0]
    best = None
    for i in range(len(horiz)):
        for j in range(i + 1, len(horiz)):
            # intersect the two lines directly
            v = np.cross(line_homog(horiz[i]), line_homog(horiz[j]))
            if abs(v[2]) < 1e-9:
                continue
            vp1 = v[:2] / v[2]
            if not (-6 * W < vp1[0] < 7 * W):
                continue
            inl1 = [L for L in horiz if vp_residual(L, vp1) < tol]
            rest = [L for L in horiz if L not in inl1]
            if len(inl1) < 3 or len(rest) < 1:
                continue
            # refit, then RE-COLLECT: a pair-seeded VP can sit just off-true and
            # misfile a borderline line into the other family for good (v002
            # filed the artwork's bottom edge as room-depth this way).
            for _ in range(2):
                vp1 = vp_from_lines(inl1)
                if vp1 is None:
                    break
                inl1 = [L for L in horiz if vp_residual(L, vp1) < tol]
            if vp1 is None or len(inl1) < 3:
                continue
            rest = [L for L in horiz if L not in inl1]
            if len(rest) < 1:
                continue
            # conjugate VP: fit among remaining lines, seeded pairwise too
            for k in range(len(rest)):
                for m in range(k, len(rest)):
                    if k == m:
                        if len(rest) > 1:
                            continue
                        # single candidate line: intersect it with vp1's horizon
                        Lk = line_homog(rest[k])
                        hz = np.array([0.0, 1.0, -vp1[1]])
                        v2 = np.cross(Lk, hz)
                        if abs(v2[2]) < 1e-9:
                            continue
                        vp2 = v2[:2] / v2[2]
                        inl2 = [rest[k]]
                    else:
                        v2 = np.cross(line_homog(rest[k]), line_homog(rest[m]))
                        if abs(v2[2]) < 1e-9:
                            continue
                        vp2 = v2[:2] / v2[2]
                        inl2 = [L for L in rest if vp_residual(L, vp2) < tol]
                        if len(inl2) < 2:
                            continue
                        for _ in range(2):
                            vp2 = vp_from_lines(inl2)
                            if vp2 is None:
                                break
                            inl2 = [L for L in rest if vp_residual(L, vp2) < tol]
                        if vp2 is None or len(inl2) < 2:
                            continue
                    prod = (vp1[0] - cx) * (vp2[0] - cx)
                    if prod >= 0:
                        continue  # same side: not conjugate
                    f_px = math.sqrt(-prod)
                    if not (f_lo_px <= f_px <= f_hi_px):
                        continue
                    dv = abs(vp1[1] - vp2[1])
                    if dv > 0.06 * W:
                        continue  # horizons disagree: not a level pair
                    score = len(inl1) + len(inl2) - 0.01 * dv
                    if best is None or score > best["score"]:
                        best = {"score": score, "vp_A": np.asarray(vp1).tolist(),
                                "vp_B": np.asarray(vp2).tolist(),
                                "inl_A": [L["name"] for L in inl1],
                                "inl_B": [L["name"] for L in inl2],
                                "f_px": f_px, "dv_horizon": dv}
    if best and best["vp_A"][0] < best["vp_B"][0]:
        best["vp_A"], best["vp_B"] = best["vp_B"], best["vp_A"]
        best["inl_A"], best["inl_B"] = best["inl_B"], best["inl_A"]
        best["f_px"] = math.sqrt(-(best["vp_A"][0] - cx) * (best["vp_B"][0] - cx))
    return best


# ---------------------------------------------------------- downlights ----

def downlight_blobs(im, v_max=260, luma_min=232):
    """Centroids of bright ceiling blobs (recessed downlight lenses). Pure
    threshold + flood label; returns [{u, v, px}] sorted by u. The centers are
    3D points on the ceiling plane — later instruments (row fits, spacing
    ratios) consume them; this only measures."""
    g = to_gray(im)[:v_max]
    m = g >= luma_min
    lbl = np.zeros(m.shape, dtype=int)
    cur = 0
    out = []
    for y0 in range(m.shape[0]):
        for x0 in range(m.shape[1]):
            if not m[y0, x0] or lbl[y0, x0]:
                continue
            cur += 1
            stack = [(y0, x0)]
            lbl[y0, x0] = cur
            pix = []
            while stack:
                y, x = stack.pop()
                pix.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] \
                            and m[ny, nx] and not lbl[ny, nx]:
                        lbl[ny, nx] = cur
                        stack.append((ny, nx))
            if len(pix) < 6:
                continue
            ys = np.array([p[0] for p in pix], float)
            xs = np.array([p[1] for p in pix], float)
            w = np.array([g[p] - luma_min + 1 for p in pix])
            out.append({"u": round(float((xs * w).sum() / w.sum()), 2),
                        "v": round(float((ys * w).sum() / w.sum()), 2),
                        "px": len(pix)})
    return sorted(out, key=lambda b: b["u"])


def camera_from_vps(best, lines, W, H):
    cx = W / 2.0
    u_A, v_A = best["vp_A"]
    u_B, v_B = best["vp_B"]
    f_px = best["f_px"]
    yaw = math.degrees(math.atan2(cx - u_B, f_px))
    v_h = (v_A * len(best["inl_A"]) + v_B * len(best["inl_B"])) / (len(best["inl_A"]) + len(best["inl_B"]))
    shift_y = (v_h - H / 2.0) / W
    verts = [L for L in lines if usable(L) and min(abs(L["angle_deg"] - 90), abs(L["angle_deg"] + 90)) <= 2.0]
    roll = None
    if verts:
        devs = [((L["angle_deg"] - 90 + 90) % 180) - 90 for L in verts]
        roll = float(np.median(devs))
    return {"W": W, "H": H, "f_px": round(f_px, 2),
            "focal_mm": round(f_px * SENSOR_MM / W, 3),
            "yaw_deg": round(yaw, 4),
            "horizon_v": round(v_h, 2), "shift_y": round(shift_y, 6),
            "shift_x": 0.0,
            "vp_A": [round(u_A, 1), round(v_A, 1)],
            "vp_B": [round(u_B, 1), round(v_B, 1)],
            "dv_horizon_px": round(best["dv_horizon"], 2),
            "family_A": sorted(best["inl_A"]), "family_B": sorted(best["inl_B"]),
            "vertical_dev_deg_median": None if roll is None else round(roll, 3),
            "n_verticals": len(verts),
            "note": "pitch=0 model; family_A = along-wall (x), family_B = depth (y). "
                    "shift_x assumed 0 (declared, untested)."}


# ------------------------------------------------------------- overlay ----

def draw_overlay(im, lines, path, cam=None):
    ov = im.convert("RGB").copy()
    d = ImageDraw.Draw(ov)
    W, H = ov.size
    for L in lines:
        if not L.get("ok"):
            continue
        col = (0, 220, 80) if usable(L) else (230, 40, 40)
        n = L["n"]
        t = (-n[1], n[0])
        mid = ((L["e0"][0] + L["e1"][0]) / 2, (L["e0"][1] + L["e1"][1]) / 2)
        ext = [(mid[0] - t[0] * 4000, mid[1] - t[1] * 4000),
               (mid[0] + t[0] * 4000, mid[1] + t[1] * 4000)]
        d.line(ext, fill=(140, 140, 255), width=1)
        d.line([tuple(L["e0"]), tuple(L["e1"])], fill=col, width=2)
        d.text((mid[0] + 3, mid[1] + 3), L["name"], fill=col)
    if cam:
        d.line([(0, cam["horizon_v"]), (W, cam["horizon_v"])], fill=(255, 160, 0), width=1)
        for vp in (cam["vp_A"], cam["vp_B"]):
            if 0 <= vp[0] <= W and 0 <= vp[1] <= H:
                d.ellipse([vp[0] - 4, vp[1] - 4, vp[0] + 4, vp[1] + 4], outline=(255, 0, 255), width=2)
    ov.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("seeds")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="v001")
    ap.add_argument("--focal-lo", type=float, default=16.0, help="mm eq lower bound")
    ap.add_argument("--focal-hi", type=float, default=60.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    im = Image.open(a.image)
    W, H = im.size
    g = to_gray(im)
    seeds = json.load(open(a.seeds, encoding="utf-8"))["seeds"]
    blobs = downlight_blobs(im)
    print(f"downlight blobs ({len(blobs)}): " + ", ".join(
        f"({b['u']:.0f},{b['v']:.0f})x{b['px']}" for b in blobs))
    lines = [fit_seed(g, s) for s in seeds]
    ok = [L for L in lines if L.get("ok")]
    good = [L for L in lines if usable(L)]
    print(f"fitted {len(ok)}/{len(lines)} seeds, {len(good)} pass guards "
          f"(rms<={RMS_MAX}, bend<={BEND_MAX}deg, n>=8)")
    for L in lines:
        if not L.get("ok"):
            print(f"  FAIL {L['name']:24s} {L['why']}")
        else:
            flag = "" if usable(L) else "  <-- GUARD"
            print(f"  {L['name']:24s} ang={L['angle_deg']:8.3f} rms={L['rms']:5.3f} "
                  f"bend={L['bend_deg']} n={L['n_pts']:3d} ambig={L['ambig_frac']:.2f}{flag}")
    with open(os.path.join(a.out, f"lines_{a.tag}.json"), "w", encoding="utf-8") as f:
        json.dump({"lines": lines, "downlight_blobs": blobs}, f, indent=1)

    best = classify(good, W, H, W * a.focal_lo / SENSOR_MM, W * a.focal_hi / SENSOR_MM)
    cam = None
    if best:
        cam = camera_from_vps(best, good, W, H)
        print("\ncamera (pitch-0 two-VP):")
        for k in ("focal_mm", "f_px", "yaw_deg", "horizon_v", "shift_y",
                  "vp_A", "vp_B", "dv_horizon_px", "vertical_dev_deg_median"):
            print(f"  {k:26s} = {cam[k]}")
        print(f"  family_A ({len(cam['family_A'])}): {cam['family_A']}")
        print(f"  family_B ({len(cam['family_B'])}): {cam['family_B']}")
        unassigned = [L["name"] for L in good
                      if L["name"] not in cam["family_A"] + cam["family_B"]
                      and min(abs(L["angle_deg"] - 90), abs(L["angle_deg"] + 90)) > 2.0]
        if unassigned:
            print(f"  UNASSIGNED horizontals (fit no family): {unassigned}")
        # downlight-pair cross-check: ceiling fixtures aligned with a room axis
        # give VP evidence no wall line can pollute (nothing leans on a seed)
        if len(blobs) >= 2:
            print("  blob-pair alignments (<0.6 deg):")
            for i in range(len(blobs)):
                for j in range(i + 1, len(blobs)):
                    b1, b2 = blobs[i], blobs[j]
                    dd = math.hypot(b2["u"] - b1["u"], b2["v"] - b1["v"])
                    if dd < 60:
                        continue
                    n = np.array([-(b2["v"] - b1["v"]), b2["u"] - b1["u"]])
                    n = n / np.hypot(*n)
                    Lp = {"n": n.tolist(), "c": -float(n @ [b1["u"], b1["v"]]),
                          "e0": [b1["u"], b1["v"]], "e1": [b2["u"], b2["v"]]}
                    for fam, vp in (("A", cam["vp_A"]), ("B", cam["vp_B"])):
                        r = vp_residual(Lp, vp)
                        if r < 0.6:
                            print(f"    ({b1['u']:.0f},{b1['v']:.0f})-({b2['u']:.0f},{b2['v']:.0f})"
                                  f"  -> vp_{fam}  ({r:.2f} deg)")
        with open(os.path.join(a.out, f"camera_{a.tag}.json"), "w", encoding="utf-8") as f:
            json.dump(cam, f, indent=1)
    else:
        print("\nNO consistent two-VP solution — seeds too thin or model wrong (check pitch).")
    draw_overlay(im, lines, os.path.join(a.out, f"overlay_{a.tag}.png"), cam)
    print(f"\noverlay -> {os.path.join(a.out, f'overlay_{a.tag}.png')}")


if __name__ == "__main__":
    main()
