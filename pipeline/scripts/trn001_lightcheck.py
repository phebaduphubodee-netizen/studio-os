"""trn001_lightcheck.py — the LIGHT round's numeric track. PURE (no bpy).

Rounds 1-3 each had one measured number (landmark reprojection px, then
material value-ratio). Light gets this. The 2026-07-30 ground-truth study
measured our whole studio's #1 gap as a NUMBER — photoreal reference files run
a light energy range of 191:1 to 2500:1 with a warm key on top, ours ran 10:1
with a cool fill on top — so the light round must be judged on ratios, never on
"looks brighter".

Three readings, each answering a question a LOOK cannot:

  LADDER   named patches sampled in linear light in both frames. Absolute values
           are NOT comparable (different exposure); what IS comparable is each
           frame's own internal ratio ladder, normalised to a chosen reference
           patch. A frame whose ladder is compressed relative to the target is
           flat, and by exactly how much.
  HALO     a horizontal scan across the concealed-light glow: peak, the distance
           it takes to fall to half, and how much of it CLIPS. A blown halo
           reads as "bright" to the eye and as lost information to this.
  LENSES   bright disks in the ceiling band = recessed downlights, reported in
           pixels so trn001_measure can turn them into millimetres.

  python pipeline/scripts/trn001_lightcheck.py <ours.png> <target.png> [--json f]
  python pipeline/scripts/trn001_lightcheck.py --lenses <img.png>
"""
import argparse
import json
from collections import deque

import numpy as np
from PIL import Image

RES = 2048

# Regions are chosen for LIGHT, not material: each one answers "how much light
# reaches this part of the room", and all avoid the target's styling objects
# (which our frame does not have yet) by construction.
PATCHES = {
    "ceiling_left":     (60, 300, 40, 140),
    "ceiling_mid":      (900, 1200, 60, 160),
    "wall_return_left": (30, 150, 500, 900),
    "wall_bay_left":    (520, 600, 700, 1000),
    "wall_bay_right":   (1450, 1550, 700, 1000),
    "halo_left_core":   (700, 730, 500, 900),
    "marble_centre":    (900, 1100, 700, 900),
    "header_face":      (900, 1200, 300, 360),
    "cubby_interior_R": (1750, 1800, 700, 850),
    "plinth_face":      (560, 700, 1560, 1590),
    "floor_far_left":   (120, 300, 1700, 1780),
    "floor_near":       (700, 1100, 1930, 2000),
}

# the ladder is reported RELATIVE to this patch, so a pure exposure difference
# between two frames cancels and only the SHAPE of the light is compared
REF_PATCH = "wall_bay_right"


def _linear(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _lum(lin):
    return lin @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _box(lin, img_w, box):
    u0, u1, v0, v1 = box
    s = img_w / float(RES)
    return lin[int(v0 * s):int(v1 * s), int(u0 * s):int(u1 * s)].reshape(-1, 3)


def ladder(path):
    """Per-patch linear luminance + the frame's own range statistics."""
    img = Image.open(path)
    lin = _linear(img)
    lum = _lum(lin)
    rows = {}
    for name, box in PATCHES.items():
        blk = _box(lin, img.width, box)
        y = blk @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        rows[name] = {"lum": float(np.median(y)),
                      "rgb": [float(c) for c in np.median(blk, axis=0)]}
    ref = max(rows[REF_PATCH]["lum"], 1e-6)
    for r in rows.values():
        r["rel"] = r["lum"] / ref
    vals = [r["lum"] for r in rows.values()]
    return {
        "patches": rows,
        "patch_range": max(vals) / max(min(vals), 1e-6),
        "frame_p1": float(np.percentile(lum, 1)),
        "frame_p50": float(np.percentile(lum, 50)),
        "frame_p99": float(np.percentile(lum, 99)),
        "frame_range_p99_p1": float(np.percentile(lum, 99) / max(np.percentile(lum, 1), 1e-6)),
        "clipped_frac": float(np.mean(np.max(np.asarray(img.convert("RGB"))
                                             .astype(np.float32) / 255.0, axis=2) >= 0.999)),
    }


def halo_profile(path, v_scan, u_from, u_to):
    """Scan horizontally across the glow. Returns peak, half-fall distance in
    PIXELS (trn001_measure converts to mm on the slab plane) and clip width.

    Half-fall is measured from the peak down to halfway to the row's own FLOOR,
    not to half the peak: the first version used half the peak, and when round
    4's rig raised the room's ambient the row simply never reached that level
    inside the window, so a glow that had not changed reported as spreading
    further (72 -> 98 px). A profile measure that moves when the BACKGROUND
    moves is measuring the background."""
    img = Image.open(path)
    s = img.width / float(RES)
    lum = _lum(_linear(img))
    row = lum[int(v_scan * s), int(min(u_from, u_to) * s):int(max(u_from, u_to) * s)]
    if u_from > u_to:
        row = row[::-1]
    peak = float(row.max())
    i_peak = int(np.argmax(row))
    floor = float(np.percentile(row, 5))
    half = floor + (peak - floor) / 2.0
    j = i_peak
    while j < len(row) - 1 and row[j] > half:
        j += 1
    return {"v": v_scan, "peak": peak, "peak_u": u_from + i_peak / s,
            "half_fall_px": (j - i_peak) / s,
            "clip_px": float(np.sum(row >= 0.999) / s),
            "floor": floor}


FLOOR_STRIP = (1690, 1790, 100, 1100, 16)   # v0, v1, u0, u1, columns


def floor_tilt(path, strip=FLOOR_STRIP):
    """Split one band of open floor into board-wide columns and separate the two
    things that can vary across it: a light GRADIENT moves the whole strip
    together (end-to-end tilt), board-to-board variation splits neighbours
    (neighbour jump). Written because the ladder's floor patch read 1.64x too
    bright and the honest first guess — that round 3's board tonal drift still
    was not landing — was REFUTED here: the target's strip is a smooth 37.6%
    ramp with a 3.4% neighbour jump, so the miss was light, not material."""
    v0, v1, u0, u1, n = strip
    img = Image.open(path)
    s = img.width / float(RES)
    lum = _lum(_linear(img))
    cols = []
    for i in range(n):
        ua = u0 + (u1 - u0) * i / n
        ub = u0 + (u1 - u0) * (i + 1) / n
        cols.append(float(np.median(lum[int(v0 * s):int(v1 * s),
                                        int(ua * s):int(ub * s)])))
    c = np.array(cols) / max(np.mean(cols), 1e-9)
    k = max(1, n // 4)
    return {"cols": [round(float(x), 3) for x in c],
            "neighbour_jump": float(np.mean(np.abs(np.diff(c)))),
            "tilt": float(abs(c[:k].mean() - c[-k:].mean()))}


def lenses(path, v_max=400, min_px=20):
    """Bright disks in the ceiling band = downlight lenses."""
    img = Image.open(path)
    s = img.width / float(RES)
    lum = _lum(_linear(img))[:int(v_max * s), :]
    mask = lum > max(float(np.percentile(lum, 99.9)), 0.80)
    seen = np.zeros_like(mask)
    out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        q, pts = deque([(y0, x0)]), []
        seen[y0, x0] = True
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                            and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
        if len(pts) < min_px:
            continue
        p = np.array(pts, dtype=np.float32)
        # a lens is round; a reveal/edge highlight is a thin sliver — reject it
        w, h = p[:, 1].ptp() + 1, p[:, 0].ptp() + 1
        out.append({"u": float(p[:, 1].mean() / s), "v": float(p[:, 0].mean() / s),
                    "w_px": float(w / s), "h_px": float(h / s), "n": len(pts),
                    "round": bool(w >= 2 * h) is False or w / max(h, 1) < 6.0})
    return sorted(out, key=lambda d: d["u"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ours", nargs="?")
    ap.add_argument("target", nargs="?")
    ap.add_argument("--lenses", metavar="IMG")
    ap.add_argument("--scan", nargs=4, type=float, metavar=("V", "U0", "U1", "DIR"),
                    help="halo scan row and u-range (DIR unused, kept for symmetry)")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    if a.lenses:
        for d in lenses(a.lenses):
            kind = "lens " if d["round"] else "sliver"
            print(f"{kind} u={d['u']:7.1f} v={d['v']:7.1f} "
                  f"{d['w_px']:5.1f}x{d['h_px']:4.1f}px n={d['n']}")
        return

    o, t = ladder(a.ours), ladder(a.target)

    # ABSOLUTE FIRST, and here is why. Every rel_err this tool printed was
    # divided by REF_PATCH in each frame, so when the reference itself sits
    # 0.795x of the target's, EVERY row is inflated by 1.26x — which is exactly
    # how the plinth got reported as a 1.26x defect when it is 1.006x absolute,
    # and how a bay that is 0.82x SHORT got read as over-lit. Absolute is
    # legitimate here precisely when the two frames' medians agree, so the tool
    # now says whether they do instead of assuming it.
    med_ratio = o["frame_p50"] / max(t["frame_p50"], 1e-6)
    ref_abs = o["patches"][REF_PATCH]["lum"] / max(t["patches"][REF_PATCH]["lum"], 1e-6)
    print(f"exposure check: frame median ours/target = {med_ratio:.3f} "
          f"({'ABSOLUTE COMPARISON VALID' if abs(med_ratio - 1) < 0.05 else 'MEDIANS DISAGREE — absolute rows are exposure-contaminated'})")
    print(f"reference patch '{REF_PATCH}' is itself {ref_abs:.3f}x of target — "
          f"every rel_err below is scaled by {1 / max(ref_abs, 1e-6):.2f}x by that alone\n")

    print(f"{'patch':20s} {'ours lin':>9s} {'tgt lin':>9s}  {'ABS':>7s} | "
          f"{'ours rel':>9s} {'tgt rel':>9s}  rel_err")
    for name in PATCHES:
        ro, rt = o["patches"][name], t["patches"][name]
        err = ro["rel"] / max(rt["rel"], 1e-6)
        absr = ro["lum"] / max(rt["lum"], 1e-6)
        print(f"{name:20s} {ro['lum']:9.4f} {rt['lum']:9.4f}  {absr:6.2f}x | "
              f"{ro['rel']:9.3f} {rt['rel']:9.3f}  {err:6.2f}x")
    print(f"\n{'':20s} {'OURS':>12s} {'TARGET':>12s}")
    for k in ("patch_range", "frame_range_p99_p1", "frame_p1", "frame_p50",
              "frame_p99", "clipped_frac"):
        print(f"{k:20s} {o[k]:12.4f} {t[k]:12.4f}")
    fo, ft = floor_tilt(a.ours), floor_tilt(a.target)
    print(f"\n{'floor strip':20s} {'OURS':>12s} {'TARGET':>12s}")
    for k in ("tilt", "neighbour_jump"):
        print(f"{k:20s} {fo[k]:11.1%} {ft[k]:11.1%}")

    print(f"\nrelative to '{REF_PATCH}'. A rel_err far from 1.00 is a part of the "
          f"room getting the wrong SHARE of the light; a patch_range below the "
          f"target's is a flat rig, which no exposure change can fix.")

    if a.scan:
        v, u0, u1, _ = a.scan
        ho, ht = halo_profile(a.ours, v, u0, u1), halo_profile(a.target, v, u0, u1)
        print(f"\nhalo scan v={v:.0f}  u {u0:.0f}->{u1:.0f}")
        for tagname, hh in (("ours", ho), ("target", ht)):
            print(f"  {tagname:7s} peak {hh['peak']:.4f} at u={hh['peak_u']:7.1f}  "
                  f"half-fall {hh['half_fall_px']:6.1f}px  clip {hh['clip_px']:5.1f}px  "
                  f"floor {hh['floor']:.4f}")

    if a.json:
        json.dump({"ours": o, "target": t}, open(a.json, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
