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
# carry the SAME material in both frames (styling objects avoided by design).
#
# A patch may be ONE box (the same pixels in both frames) or a per-frame pair
# {"ours": box, "target": box}. THE PAIR IS NOT A CONVENIENCE — a narrow feature
# cannot be sampled by a shared box at all. Round 5 found the row labelled
# "veneer_dark (right stile)" sitting on the CUBBY BACK in BOTH frames: it read
# 0.0205 and 0.0186 linear where a lit stile reads above 0.05, so a cavity was
# being reported as a stile and the two cavity rows silently agreed with each
# other. The stiles are ~10 px wide and the two frames put them 6 px apart
# (target's outer band starts u1937, ours u1943), which is why the box has to be
# located per frame. Same failure class the project has already paid for twice:
# a bounding box that could not tell a vase from a plank, and a return band that
# could not tell a shallow box from a deep pocket. THE INSTRUMENT THAT SCORES
# THE WORK HAS TO BE CHECKED AGAINST THE WORK.
PATCHES = {
    # CLEARED 2026-08-01, after briefly being flagged as suspect. A first ID-mask
    # read resolved this box to brass_p1_bot, which would have meant the row was
    # comparing OUR BRASS INLAY against the target's veneer. The read was wrong,
    # not the patch: the ID pass wrote LINEAR emission and the PNG stores sRGB, so
    # a 0.2 step lands at 0.485 on disk and the decoder was matching encoded
    # values against linear ones. Re-read in linear space with unique per-mass
    # colours it resolves header_p1 95% / brass_p1_top 4% — the panel, correctly.
    # Kept as a note because the instinct to MOVE the patch on the first reading
    # would have broken a working row to satisfy a broken instrument.
    "veneer_dark (header face)": (900, 1200, 300, 360),
    "veneer_pier (R outer stile)": {"ours": (1946, 1956, 700, 900),
                                    "target": (1939, 1949, 700, 900)},
    "veneer_pier (R inner stile)": {"ours": (1686, 1696, 700, 900),
                                    "target": (1684, 1694, 700, 900)},
    "cavity (cubby interior)":   (1750, 1800, 700, 850),
    # 2026-08-01: this row USED to be "cavity (lower bay)" at (1750,1800,1150,1300),
    # on the reasoning that a second box further down would report the material
    # rather than a band. An ID-mask read showed both boxes land on the SAME mass
    # (tower_R_back), so the table carried two rows that were never independent —
    # a spread computed over them counts one surface twice. Repointed at the LEFT
    # tower's interior SIDE WALL, verified by ID mask to contain tower_L_sA and
    # nothing else, which also puts the lane's outstanding defect on the sheet:
    # that wall measures 2.05x the target's against a back panel that is exact.
    "cavity (L side wall)":      (315, 350, 990, 1020),
    "paint_white (left of bay)": (520, 600, 700, 1000),
    "paint_white (right of bay)": (1450, 1550, 700, 1000),
    "marble (clean field)":      (760, 900, 600, 750),
    "lacquer_white (plinth)":    (560, 700, 1560, 1590),
    "veneer_altar (step face)":  (500, 640, 1440, 1470),
    "floor_oak (mid)":           (700, 900, 1850, 1950),
}

# any patch narrower than this must be located per frame, never shared
NARROW_PX = 24


def _lin(img, box):
    u0, u1, v0, v1 = box
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    s = img.width / 2048.0
    blk = a[int(v0 * s):int(v1 * s), int(u0 * s):int(u1 * s)].reshape(-1, 3)
    lin = np.where(blk <= 0.04045, blk / 12.92, ((blk + 0.055) / 1.055) ** 2.4)
    return np.median(lin, axis=0)


def _boxes(spec):
    """A patch is one shared box, or a per-frame pair. Returns (ours, target)."""
    if isinstance(spec, dict):
        return spec["ours"], spec["target"]
    return spec, spec


def _check_narrow(name, spec):
    """A narrow feature sampled by a SHARED box is the round-5 defect. Refuse it
    rather than reporting a number that names the wrong surface."""
    if isinstance(spec, dict):
        return
    if spec[1] - spec[0] < NARROW_PX:
        raise ValueError(
            f"patch {name!r} is {spec[1] - spec[0]} px wide and shared between "
            f"frames; anything under {NARROW_PX} px must give a per-frame box "
            f"({{'ours': ..., 'target': ...}}) or it will sample two different "
            f"surfaces and report them as one material")


def compare(ours_path, target_path):
    ours, tgt = Image.open(ours_path), Image.open(target_path)
    rows = []
    for name, spec in PATCHES.items():
        _check_narrow(name, spec)
        ob, tb = _boxes(spec)
        o, t = _lin(ours, ob), _lin(tgt, tb)
        ratio = float(np.mean(o) / max(np.mean(t), 1e-6))
        # hue error is lighting-independent in a way brightness is not
        on, tn = o / max(np.mean(o), 1e-6), t / max(np.mean(t), 1e-6)
        rows.append({"patch": name,
                     "per_frame": isinstance(spec, dict),
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
