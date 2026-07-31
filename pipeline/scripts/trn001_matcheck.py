"""trn001_matcheck.py — the materials round's NUMERIC TRACK. PURE (no bpy).

Charter rule 6 wants at least one measured number per round. For geometry that
was landmark reprojection error; for materials it is this: sample the SAME
patch of the same surface in our frame and in the target, in linear light, and
report the ratio per material.

What the number can and cannot say, stated up front so the gate does not
over-read it: our light rig is a neutral form light and the target was lit with
a designed rig, so a ratio is NOT expected to be 1.0 — the LIGHT round owns
that. What it does catch is a material whose ratio sits far off its neighbours,
i.e. one surface wrong relative to the rest of the palette, which is exactly
the failure a beauty render hides.

  python pipeline/scripts/trn001_matcheck.py <ours.png> <target.png> [--json out]
"""
import argparse
import json

import numpy as np
from PIL import Image

# patch = (u0, u1, v0, v1) in 2048-space, chosen on flat unoccluded areas that
# carry the SAME material in both frames (styling objects avoided by design)
PATCHES = {
    "veneer_dark (header face)": (900, 1200, 300, 360),
    "veneer_dark (right stile)": (1900, 1940, 700, 900),
    "cavity (cubby interior)":   (1750, 1800, 700, 850),
    "paint_white (left of bay)": (520, 600, 700, 1000),
    "paint_white (right of bay)": (1450, 1550, 700, 1000),
    "marble (clean field)":      (760, 900, 600, 750),
    "lacquer_white (plinth)":    (560, 700, 1560, 1590),
    "veneer_altar (step face)":  (500, 640, 1440, 1470),
    "floor_oak (mid)":           (700, 900, 1850, 1950),
}


def _lin(img, box):
    u0, u1, v0, v1 = box
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    s = img.width / 2048.0
    blk = a[int(v0 * s):int(v1 * s), int(u0 * s):int(u1 * s)].reshape(-1, 3)
    lin = np.where(blk <= 0.04045, blk / 12.92, ((blk + 0.055) / 1.055) ** 2.4)
    return np.median(lin, axis=0)


def compare(ours_path, target_path):
    ours, tgt = Image.open(ours_path), Image.open(target_path)
    rows = []
    for name, box in PATCHES.items():
        o, t = _lin(ours, box), _lin(tgt, box)
        ratio = float(np.mean(o) / max(np.mean(t), 1e-6))
        # hue error is lighting-independent in a way brightness is not
        on, tn = o / max(np.mean(o), 1e-6), t / max(np.mean(t), 1e-6)
        rows.append({"patch": name,
                     "ours": [round(float(c), 4) for c in o],
                     "target": [round(float(c), 4) for c in t],
                     "value_ratio": round(ratio, 3),
                     "hue_err": round(float(np.max(np.abs(on - tn))), 3)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ours")
    ap.add_argument("target")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    rows = compare(a.ours, a.target)
    print(f"{'patch':28s} {'ours(lin)':22s} {'target(lin)':22s} ratio  hue_err")
    for r in rows:
        o = "(" + ",".join(f"{c:.3f}" for c in r["ours"]) + ")"
        t = "(" + ",".join(f"{c:.3f}" for c in r["target"]) + ")"
        print(f"{r['patch']:28s} {o:22s} {t:22s} {r['value_ratio']:5.2f}  {r['hue_err']:.3f}")
    ratios = [r["value_ratio"] for r in rows]
    spread = max(ratios) / max(min(ratios), 1e-6)
    print(f"\nvalue-ratio spread across the palette = {spread:.2f}x  "
          f"(1.0 = every material sits the same distance from the target; a "
          f"large spread means one surface is wrong RELATIVE to the rest, which "
          f"is the part the light round cannot fix)")
    print(f"worst hue error = {max(r['hue_err'] for r in rows):.3f}")
    if a.json:
        json.dump({"rows": rows, "spread": round(spread, 3)},
                  open(a.json, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
