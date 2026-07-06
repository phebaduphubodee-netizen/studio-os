"""
raster_overlay.py — overlay the CURRENT scene-graph footprints on the TRUE PDF raster
(what the owner sees), high-DPI, so misalignment is unmistakable. Draws each placed piece
as a box + facing arrow in mm on top of the rendered sheet. Crops to master + sitting.
"""
import json
import sys
import numpy as np
import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

PDF = sys.argv[1]
LAYOUT = sys.argv[2]
OUTBASE = sys.argv[3]
SCALE, OX, OY = 26.45, 171.2, 596.5
DPI = 200
zoom = DPI / 72.0

doc = fitz.open(PDF)
p = doc[1]
pix = p.get_pixmap(dpi=DPI)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
Wpt, Hpt = pix.width / zoom, pix.height / zoom       # display-space page size (pt)
ext = [(0 - OX) * SCALE, (Wpt - OX) * SCALE, (OY - Hpt) * SCALE, (OY - 0) * SCALE]


def load(fn):
    return json.load(open(f"{LAYOUT}/{fn}", encoding="utf-8"))


master = load("scene-graph.master_bedroom.json")
sitting = load("scene-graph.sitting_room.json")


def pieces(spec):
    out = list(spec.get("builtins", [])) + list(spec.get("items", []))
    for sr in spec.get("subrooms", []):
        out += sr.get("fixtures", [])
    return out


ALL = [("M", it) for it in pieces(master)] + [("S", it) for it in pieces(sitting)]


import math
from matplotlib.patches import Polygon


def draw(ax):
    ax.imshow(img, extent=ext, origin="upper", aspect="equal", zorder=0)
    for tag, it in ALL:
        w, d, rot = it["w"], it["d"], it.get("rot", 0)
        cx, cy = it["x"] + w / 2, it["y"] + d / 2
        kind = it["kind"]
        col = {"bed": "#d01010", "sofa": "#d01010", "armchair": "#d06010", "bench": "#8040a0",
               "side_table": "#c08000", "tv_console": "#0090d0", "cabinet": "#0090d0",
               "wardrobe": "#108010", "headboard": "#108010", "vanity_double": "#00a0a0"}.get(kind, "#606060")
        # rotate the (w x d) rectangle about its centre by rot (CCW) — handles ANY angle
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
        pts = [(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in corners]
        ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor=col, lw=2.0, zorder=5))
        if kind in ("sofa", "armchair", "bed"):
            fx, fy = math.sin(a), -math.cos(a)          # front = -Y rotated by rot
            L = 0.3 * min(w, d) + 200
            ax.add_patch(FancyArrow(cx, cy, fx * L, fy * L, width=25,
                         head_width=160, head_length=140, color="#ff6a00", zorder=6, length_includes_head=True))
        ax.text(cx, cy + d / 2 + 60, kind, ha="center", va="bottom", fontsize=6, color=col, zorder=7)


for name, (x0, x1, y0, y1) in [("bed", (2000, 5600, -600, 2900)),
                               ("nw", (-500, 3400, 3000, 6300)),
                               ("west", (-500, 1400, -200, 3000)),
                               ("sofa", (5400, 10200, 3000, 6300)),
                               ("bath", (-500, 5850, 5700, 8800)),
                               ("full", (-600, 11000, -1200, 8800))]:
    fig, ax = plt.subplots(figsize=((x1 - x0) / 500.0, (y1 - y0) / 500.0), dpi=150)
    draw(ax)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_title(f"placed furniture (boxes) over TRUE sheet — {name}", fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{OUTBASE}_{name}.png", dpi=150)
    plt.close(fig)
    print("wrote", f"{OUTBASE}_{name}.png")
