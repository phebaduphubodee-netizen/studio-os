#!/usr/bin/env python3
"""value_floor.py — DOES THE FRAME HAVE A VALUE FLOOR, AND DOES ITS LIGHT HAVE A SIDE?

The two questions a sighted panel answered about p2r77 on 2026-08-26 that no rung in
this repo could ask, both restated as numbers any leg of an A/B can be scored on:

  1. VALUE FLOOR — "not one mass in the room reads dark, so the whole render floats as
     pale midtone mush". Measured as the share of 40-px BLOCK MEANS below a threshold,
     not the share of pixels: a slat groove or a drawer gap is a dark LINE, and a frame
     full of dark lines still has no dark MASS. The panel's own reading on the shipped
     frame: 2.4% of blocks under L60 and 9.9% under L80, against delivered anchors at
     18.1%/23.6% and 8.3%/16.6%.

  2. LIGHT HAS A SIDE — "mirrored halves of the room tell contradictory light-direction
     stories". Measured by sampling MIRROR PAIRS about the frame's own vertical axis and
     reporting the signed left-right difference per pair. On p2r77 the pairs disagreed:
     the pillow pair was brighter on the side AWAY from the window while the nightstand
     pair leaned the other way, which is the signature of a room lit by area fill from
     everywhere rather than by a key from somewhere.

WHY IT IS ITS OWN FILE AND NOT A LINE IN A GATE: this is the rung that decides an
A/B leg. `--pair A.png B.png` prints both frames' numbers side by side and names which
leg has more dark mass and which leg's light has a consistent side; the amplitude
bracket for the key sun is scored with it, and the numbers go in the gate artifact.

Stdlib + PIL only (this is layer 3, an image reader, never imported by gate/rule code).
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    from PIL import Image
except ImportError:                                          # pragma: no cover
    Image = None


def _luma(path):
    if Image is None:
        raise SystemExit("value_floor: PIL is required (layer-3 reader)")
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    # Rec.709 on display-encoded values — the same convention the panel used, so the
    # numbers here are comparable to the ones in its report rather than nearly so.
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        row = out[y]
        for x in range(w):
            r, g, b = px[x, y]
            row[x] = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return out, w, h


def block_means(lum, w, h, block=40):
    """Mean luminance per block. Blocks, not pixels: a dark LINE is not a dark MASS."""
    bs = []
    for by in range(0, h - block + 1, block):
        for bx in range(0, w - block + 1, block):
            s = 0.0
            for y in range(by, by + block):
                row = lum[y]
                for x in range(bx, bx + block):
                    s += row[x]
            bs.append(s / (block * block))
    return bs


def floor_report(path, block=40, thresholds=(60.0, 80.0)):
    lum, w, h = _luma(path)
    # scale the block to the frame so a quick playblast and a full frame are asking
    # about the same PHYSICAL patch of room, not the same pixel count
    b = max(8, int(round(block * w / 2400.0)))
    bs = block_means(lum, w, h, b)
    n = len(bs) or 1
    flat = [v for row in lum for v in row]
    flat.sort()

    def pct(p):
        return flat[min(len(flat) - 1, max(0, int(p / 100.0 * len(flat))))]

    rep = {"file": path, "size": [w, h], "block_px": b, "n_blocks": n}
    for t in thresholds:
        rep[f"blocks_under_L{int(t)}"] = round(100.0 * sum(1 for v in bs if v < t) / n, 2)
    rep["darkest_block"] = round(min(bs), 1) if bs else None
    rep["p1"] = round(pct(1), 1)
    rep["p50"] = round(pct(50), 1)
    rep["p99"] = round(pct(99), 1)
    rep["range_p99_over_p1"] = round(pct(99) / max(pct(1), 1e-6), 2)
    return rep


# Mirror pairs are given in FRACTIONS of the frame so one set of coordinates works at
# any resolution — a playblast and the deliverable ask the same question.
DEFAULT_PAIRS = {
    "pillow":     (0.36, 0.40, 0.44, 0.50),
    "duvet":      (0.30, 0.60, 0.42, 0.70),
    "headboard":  (0.34, 0.20, 0.44, 0.30),
    "nightstand": (0.19, 0.44, 0.25, 0.52),
    "floor":      (0.06, 0.70, 0.13, 0.80),
    "slatwall":   (0.20, 0.05, 0.26, 0.20),
}


def _region_mean(lum, w, h, box):
    x0, y0, x1, y1 = box
    xs, xe = int(x0 * w), int(x1 * w)
    ys, ye = int(y0 * h), int(y1 * h)
    vals = [lum[y][x] for y in range(max(0, ys), min(h, ye))
            for x in range(max(0, xs), min(w, xe))]
    return sum(vals) / len(vals) if vals else None


def side_report(path, pairs=None):
    """Signed LEFT-minus-RIGHT luminance for each mirror pair, plus whether the frame
    agrees with itself about which side the light is on."""
    lum, w, h = _luma(path)
    pairs = pairs or DEFAULT_PAIRS
    out = {}
    for name, box in pairs.items():
        x0, y0, x1, y1 = box
        left = _region_mean(lum, w, h, (x0, y0, x1, y1))
        right = _region_mean(lum, w, h, (1.0 - x1, y0, 1.0 - x0, y1))
        if left is None or right is None:
            continue
        out[name] = {"left": round(left, 1), "right": round(right, 1),
                     "L_minus_R": round(left - right, 1)}
    signs = [1 if v["L_minus_R"] > 2 else (-1 if v["L_minus_R"] < -2 else 0)
             for v in out.values()]
    nz = [s for s in signs if s]
    out["_consistent"] = bool(nz) and all(s == nz[0] for s in nz)
    out["_pairs_with_a_side"] = len(nz)
    out["_pairs_measured"] = len(signs)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("images", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    reports = []
    for p in a.images:
        r = {"floor": floor_report(p), "side": side_report(p)}
        reports.append(r)
    if a.json:
        print(json.dumps(reports, ensure_ascii=False, indent=1))
        return 0
    print(f"{'frame':46s} {'<L60':>6s} {'<L80':>6s} {'darkest':>8s} "
          f"{'p1':>6s} {'p99/p1':>7s} {'side':>18s}")
    for r in reports:
        f, s = r["floor"], r["side"]
        nm = f["file"].split("/")[-1].split("\\")[-1]
        side = ("consistent" if s["_consistent"] else "SPLIT") + \
               f" {s['_pairs_with_a_side']}/{s['_pairs_measured']}"
        print(f"{nm[:46]:46s} {f['blocks_under_L60']:6.2f} {f['blocks_under_L80']:6.2f} "
              f"{f['darkest_block']:8.1f} {f['p1']:6.1f} {f['range_p99_over_p1']:7.2f} "
              f"{side:>18s}")
    for r in reports:
        nm = r["floor"]["file"].split("\\")[-1].split("/")[-1]
        pairs = ", ".join(f"{k} {v['L_minus_R']:+.0f}"
                          for k, v in r["side"].items() if not k.startswith("_"))
        print(f"  {nm[:44]:44s} {pairs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
