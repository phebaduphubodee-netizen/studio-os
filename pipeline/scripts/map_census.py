"""map_census.py — the MAP-COVERAGE census, pure half (P2r-6).

Reads the per-material id mask (`map_census_mask.py`'s output) and prints THE
PHASE'S OWN HEADLINE NUMBER: % of visible frame area whose material carries
image maps. SC-4's ground-truth study measured us at 4.9% (material-side)
against 50-66% in delivered .blend files, and until this file nothing in the
repo could print that number from a frame.

REPORTING LINE, NOT A CUT (the plan's own close condition): the number prints
on every gate run beside the study band, and the shortfall prints as a NAMED
list of surfaces — silence and vacuous zeros are the two shapes this repo's
instruments have lied in, so a frame with no mask prints NOT RUN, never 0%.

    python pipeline/scripts/map_census.py pipeline/output/room_x.matmask.png
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

STUDY_BAND = (50.0, 66.0)     # % of frame, delivered-work band (SC-4 study)


def mask_sidecar(render_png):
    """The census mask path a render owns: room_x.png -> room_x.matmask.png."""
    return os.path.splitext(render_png)[0] + ".matmask.png"


def decode_ids(arr):
    """(H, W, 3) uint8 -> (H, W) int id plane. Palette levels are exact
    multiples of 51, so nearest-level per channel is integer arithmetic."""
    q = ((arr.astype(np.int32) + 25) // 51)
    return q[..., 0] * 36 + q[..., 1] * 6 + q[..., 2]


def census(mask_png):
    """Returns the census dict, or None when the mask pair is absent
    (caller prints NOT RUN — absence must never read as 0%)."""
    meta_path = os.path.splitext(mask_png)[0] + ".json"
    if not (os.path.exists(mask_png) and os.path.exists(meta_path)):
        return None
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    ids = {int(k): v for k, v in meta["ids"].items()}
    has_img = meta["has_image"]
    plane = decode_ids(np.asarray(Image.open(mask_png).convert("RGB")))
    total = plane.size
    counts = np.bincount(plane.ravel(), minlength=max(ids) + 1)
    unknown = int(counts[0])
    rows = []
    for i, nm in ids.items():
        px = int(counts[i]) if i < len(counts) else 0
        rows.append({"material": nm, "share_pct": 100.0 * px / total,
                     "has_image": bool(has_img.get(nm, False))})
    rows.sort(key=lambda r: -r["share_pct"])
    covered = sum(r["share_pct"] for r in rows if r["has_image"])
    return {
        "covered_pct": round(covered, 2),
        "unmeasured_pct": round(100.0 * unknown / total, 2),
        "band": STUDY_BAND,
        "rows": rows,
    }


def report_lines(c, top=6):
    """The gate print. One headline line + the named shortfall."""
    lo, hi = c["band"]
    inside = lo <= c["covered_pct"] <= hi
    lines = [f"MAP-COVERAGE {c['covered_pct']}% of frame on image-mapped "
             f"materials (study band {lo:.0f}-{hi:.0f}% — "
             f"{'inside' if inside else 'below' if c['covered_pct'] < lo else 'above'}; "
             f"reporting line, not a cut)"]
    short = [r for r in c["rows"] if not r["has_image"] and r["share_pct"] >= 0.5]
    if short:
        lines.append("  uncovered by share: " + " · ".join(
            f"{r['material']} {r['share_pct']:.1f}%" for r in short[:top]))
    if c["unmeasured_pct"] > 0.5:
        lines.append(f"  unmeasured (id 0 / background): {c['unmeasured_pct']}%")
    return lines


def main():
    if len(sys.argv) != 2:
        print("usage: map_census.py <room_x.matmask.png>")
        return 2
    c = census(sys.argv[1])
    if c is None:
        print("MAP-COVERAGE census NOT RUN — no mask pair beside the render "
              "(rerun the build; absence is not 0%)")
        return 2
    for ln in report_lines(c):
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
