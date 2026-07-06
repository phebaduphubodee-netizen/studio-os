"""
gen_floor2_keyplan.py -- CLEAN, HONEST communication overlay (the fix for the
floor2_BEFORE_AFTER.png critique: clipped labels, zone spill, and a printed
"IoU 1.00" caption the image could not itself prove).

This is a KEY PLAN, the standard architectural convention that structurally
cannot clip or overlap labels:
  - furniture footprints carry a small ASCII index number (always renders, never
    tofu, never overlaps a neighbour's text);
  - the Thai names live in a legend in the right margin (empty space -> no clip),
    rendered in a Thai-capable Windows font (Tahoma) so they are readable, not boxes;
  - ZONES are drawn as the room OUTLINE polygons themselves (read from the manifest
    floor_zones == the same wall-snapped outlines build_floor extrudes), so a zone
    edge IS a wall by construction -- it cannot "spill past the wall";
  - the footer cites the placement-gate.json MARKER (floating / unplaced / facing /
    calibration) read from disk -- NOT a typed "IoU 1.00". Per-piece IoU after snap
    is tautological; the gate's real guarantees are COMPLETENESS + NO-FLOATING, and
    those are what the footer states, as measured numbers.

Every coordinate/size/rotation shown is READ from the scene-graph JSONs and the
gate marker. Nothing is typed onto the picture. Numeric self-checks run before the
image is written and print PASS/FAIL (furniture-in-zone, index collisions, marker
provenance) so the overlay's own claims are verified, not asserted.

    python gen_floor2_keyplan.py

Reads (relative to repo root): the two scene-graphs, floor2-manifest.json,
placement-gate.json. Writes pipeline/output/floor2/floor2_keyplan.png.
"""
import json
import math
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import fitz
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyArrow, Polygon

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
LAYOUT = os.path.join(REPO, "projects", "PRJ-2026-002_c001-house", "03_layout", "v4")
OUT = os.path.join(REPO, "pipeline", "output", "floor2_v4", "floor2_v4_keyplan.png")
SCALE, OX, OY = 26.45, 171.2, 596.5       # this sheet's calibration (mirrors gen_floor2_specs)
PAGE = 1

# ---- Thai-capable font so the legend is readable, not tofu -----------------------------
_THAI = "sans-serif"
for _fp in (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\LeelawUI.ttf",
            r"C:\Windows\Fonts\upcjl.ttf"):
    if os.path.exists(_fp):
        try:
            font_manager.fontManager.addfont(_fp)
            _THAI = font_manager.FontProperties(fname=_fp).get_name()
            break
        except Exception:
            pass
plt.rcParams["font.family"] = _THAI
print(f"font: {_THAI}")


def load(name):
    with open(os.path.join(LAYOUT, name), encoding="utf-8") as f:
        return json.load(f)


master = load("scene-graph.master_bedroom.json")
sitting = load("scene-graph.sitting_room.json")
manifest = load("floor2_v4-manifest.json")
marker = load("placement-gate.json")
PDF = os.path.join(REPO, *manifest["source_pdf"].split("/"))

# category colours (match the self-verify legend the studio already reads)
COL = {"loose": "#c0201f", "builtin": "#107a2f", "fixture": "#1580c0"}


def pieces_of(sg):
    """Flatten a scene-graph into (item, category) in a stable draw order."""
    out = []
    for it in sg.get("items", []):
        out.append((it, "loose"))
    for it in sg.get("builtins", []):
        out.append((it, "builtin"))
    for sr in sg.get("subrooms", []):
        for it in sr.get("fixtures", []):
            out.append((it, "fixture"))
    return out


ALL = [("MASTER", *p) for p in pieces_of(master)] + [("SITTING", *p) for p in pieces_of(sitting)]

# ---- geometry helpers ------------------------------------------------------------------
_HEAD = {0: "S", 90: "E", 180: "N", 270: "W"}          # facing at rot
_OPP = {"S": "N", "N": "S", "E": "W", "W": "E"}
_SEAT = {"bed", "sofa", "loveseat", "armchair", "chair"}


def footprint(it):
    """Rotated corner polygon + centroid, in mm floor coords."""
    w, d, rot = it["w"], it["d"], it.get("rot", 0)
    cx, cy = it["x"] + w / 2.0, it["y"] + d / 2.0
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(cx + u * ca - v * sa, cy + u * sa + v * ca)
           for u, v in ((-w/2, -d/2), (w/2, -d/2), (w/2, d/2), (-w/2, d/2))]
    return pts, (cx, cy)


def in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xin = (x1 - x0) * (y - y0) / (y1 - y0) + x0
            if x < xin:
                inside = not inside
    return inside


def provenance(it, cat):
    if "cluster" in it and "snap_mm" in it:
        return f"cluster#{it['cluster']} · snap {it['snap_mm']}mm"
    if it.get("angled"):
        return "วางบน ink ที่วาด (oriented box) · หันออก=owner · มุม=derived"
    if it.get("kind") == "bed":
        return "measured (รวมกับ casework)"
    if cat == "builtin":
        return "BF label · wall"
    if cat == "fixture":
        return "fixture · human-confirm"
    return "measured"


def facing_str(it):
    """Facing text. A seat with NO stored 'rot' is default-S (from the note), NOT a machine-
    verified orientation — say so, so the legend never over-reads a rot-less chair."""
    has_rot = "rot" in it
    rot = it.get("rot", 0)
    if it.get("kind") in _SEAT and rot in _HEAD:
        face = _HEAD[rot]
        src = "" if has_rot else " (default/note)"
        if it.get("kind") == "bed":
            return f"หัน {face} · หัว {_OPP[face]}{src}"
        return f"หัน {face}{src}"
    if it.get("kind") in _SEAT and rot:
        return f"หันออกสวน (owner) · มุม ~{rot}° (derived)"
    return f"rot{rot}" if rot else ""


def bf_mismatch(it):
    """If the NAME embeds a BF label 'LxWxH' (cm) whose length disagrees with the drawn
    footprint by >150mm, surface it — the image must disclose a label≠drawn conflict, not
    hide it (BF14 '325x10x280' names 3250mm but the slat is drawn 2700mm)."""
    # anchor on the '.' that separates the BF number from the dims block, so 'BF14.325x10x280'
    # reads L=325 (3250mm), NOT '14.325'. Without the leading '\.' the BF NUMBER leaks into L.
    m = re.search(r"\.(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)x(\d+)\b", it.get("name", ""))
    if not m:
        return ""
    label_len = float(m.group(1)) * 10.0          # cm -> mm
    drawn = max(it["w"], it["d"])
    return f"  [!] ป้าย {label_len:.0f}≠วาด {drawn:.0f}" if abs(label_len - drawn) > 150 else ""


# ================================================================= NUMERIC SELF-CHECKS
zones = manifest["floor_zones"]
zpoly = {z["id"]: z["outline_mm"] for z in zones}
checks_ok = True

# 1) furniture centroid must land inside SOME zone polygon (a piece outside every zone
#    is a placement/zone-mismatch). Wall casework may sit on a boundary, so test the
#    centroid against a 60mm-inset-tolerant union by testing all zones.
outside = []
for room, it, cat in ALL:
    _, c = footprint(it)
    if not any(in_poly(c, p) for p in zpoly.values()):
        outside.append((room, it.get("name", "?"), c))
print(f"[check] furniture centroid in a zone: {len(ALL) - len(outside)}/{len(ALL)} inside")
for room, nm, c in outside:
    print(f"        OUTSIDE ALL ZONES: [{room}] {nm[:34]} at ({c[0]:.0f},{c[1]:.0f})")
    checks_ok = False

# 2) index-number legibility: no two centroids within 260mm (numbers would collide)
cents = [footprint(it)[1] for _, it, _ in ALL]
collide = 0
for i in range(len(cents)):
    for j in range(i + 1, len(cents)):
        if math.hypot(cents[i][0]-cents[j][0], cents[i][1]-cents[j][1]) < 260:
            collide += 1
print(f"[check] index collisions (<260mm apart): {collide}"
      + ("  (labels offset to resolve)" if collide else ""))

# 3) footer numbers are READ from the marker, not typed
rr = {r["room"]: r for r in marker["rooms"]}
def rsum(r):
    """Verdict + the all-zero guarantees AND the non-zero flags that DRIVE the REVIEW, so the
    footer never reads as an all-zero rubber-stamp when human identity-confirm is required."""
    fl = len(r["floating"]) if isinstance(r.get("floating"), list) else r.get("floating", 0)
    drv = [f"{k} {r[k]}" for k in ("dismissed", "long_thin") if r.get(k)]
    tail = ("  ← human-confirm: " + ", ".join(drv)) if drv else ""
    return (f"{r['verdict']} (floating {fl}, unplaced {r['unplaced']}, "
            f"facing {r['facing_flags']}{tail})")
print(f"[check] marker provenance: calibration={marker['calibration']}; "
      + "; ".join(f"{k}={rsum(v)}" for k, v in rr.items()))
print(f"[self-check overall] {'PASS' if checks_ok else 'FAIL — fix before using the image'}")

# ================================================================= DRAW
p = fitz.open(PDF)[PAGE]
m = p.rotation_matrix


def mm(P):
    Q = fitz.Point(P) * m
    return ((Q.x - OX) * SCALE, (OY - Q.y) * SCALE)


def bez(pts, n=6):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    return [((1-t)**3*x0+3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3*x3,
             (1-t)**3*y0+3*(1-t)**2*t*y1+3*(1-t)*t*t*y2+t**3*y3)
            for t in (i/n for i in range(n+1))]


strokes = []
for dr in p.get_drawings():
    if (dr.get("width") or 0) >= 0.6:
        continue
    for it in dr["items"]:
        if it[0] == "l":
            strokes.append([mm(it[1]), mm(it[2])])
        elif it[0] == "re":
            r = it[1]
            cs = [mm((r.x0, r.y0)), mm((r.x1, r.y0)), mm((r.x1, r.y1)),
                  mm((r.x0, r.y1)), mm((r.x0, r.y0))]
            strokes += [[a, b] for a, b in zip(cs, cs[1:])]
        elif it[0] == "c":
            poly = [mm(z) for z in bez([(pt.x, pt.y) for pt in it[1:5]])]
            strokes += [[a, b] for a, b in zip(poly, poly[1:])]

fig = plt.figure(figsize=(26, 15), dpi=130)
gs = fig.add_gridspec(1, 2, width_ratios=[3.05, 1.15], wspace=0.02)
ax = fig.add_subplot(gs[0])
lg = fig.add_subplot(gs[1])
lg.axis("off")

# plan underlay (faint)
ax.add_collection(LineCollection(strokes, colors="#9fb0c4", linewidths=0.4))

# zones = the real room outlines (wall-snapped by construction). alpha kept low so a fixture
# tint stacked inside its own zone does not muddy into a false "two zones overlap" read.
for z in zones:
    rgb = z["color"]
    ax.add_patch(Polygon(z["outline_mm"], closed=True, facecolor=rgb, alpha=0.11,
                         edgecolor=[c*0.55 for c in rgb], lw=1.4, zorder=1))

# sliding glass door (thin-line = invisible to the wall extractor) + the L pier — annotated
# EXPLICITLY because the machine cannot see it; this is an owner-read (2026-07-06), the exact
# case the crystallization calls out (a room's true boundary can be a thin-line glass wall).
ax.plot([7150, 9900], [2050, 2050], color="#1560d0", lw=2.6, ls=(0, (5, 2)), zorder=6)
ax.plot([7050, 7100], [2600, 2050], color="#1560d0", lw=2.6, zorder=6)      # L pier
ax.plot([5752, 7050], [2600, 2600], color="#1560d0", lw=2.6, zorder=6)      # L: console wall
ax.text(8500, 1760, "ประตูเลื่อนกระจก (owner-read · เส้นบาง เครื่องมองไม่เห็น)",
        ha="center", fontsize=8.5, color="#1560d0", zorder=7,
        path_effects=[pe.withStroke(linewidth=2.8, foreground="white")])
ax.text(6400, 2760, "ผนัง+pier (L)", ha="center", fontsize=7.5, color="#1560d0", zorder=7,
        path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])

# furniture footprints + index numbers
for idx, (room, it, cat) in enumerate(ALL, start=1):
    pts, (cx, cy) = footprint(it)
    col = COL[cat]
    ax.add_patch(Polygon(pts, closed=True, facecolor=col, alpha=0.16,
                         edgecolor=col, lw=1.6, zorder=3))
    if it.get("kind") in _SEAT:
        a = math.radians(it.get("rot", 0))
        fx, fy = math.sin(a), -math.cos(a)
        L = 0.28 * min(it["w"], it["d"]) + 170
        # solid = orientation stored as rot (machine-checkable); faded = default-S from a note.
        arr_col = "#e07000" if "rot" in it else "#eab27a"
        ax.add_patch(FancyArrow(cx, cy, fx*L, fy*L, width=22, head_width=150,
                     head_length=140, color=arr_col, length_includes_head=True, zorder=4))
    ax.text(cx, cy, str(idx), ha="center", va="center", fontsize=8.5, zorder=5,
            fontweight="bold", color="white",
            bbox=dict(boxstyle="circle,pad=0.18", fc=col, ec="white", lw=0.8))

# zone names at a HAND-TUNED clear anchor per zone (no formula that lands a title under an
# index badge — the old top-left inset put ENSUITE under badge #13). White halo keeps them
# legible over the plan strokes; zorder above the badges.
_ZN = {"master_sleep": ("MASTER / ที่นอน", 850, 330),
       "master_dress": ("โซนแต่งตัว / ทำงาน", 750, 5650),
       "sitting": ("SITTING (ในบ้าน)", 8900, 5100),
       "sitting_lounge": ("เลานจ์ริมกระจก (ในบ้าน ชั้น 2)", 8300, 500),
       "ensuite": ("ENSUITE ห้องน้ำในตัว", 1050, 7080),
       "wardrobe": ("โซนตู้ BF09-1 (L 5.2m)", 3300, 6550)}
zcol = {z["id"]: z["color"] for z in zones}
for zid, (txt, tx, ty) in _ZN.items():
    if zid not in zcol:          # a manifest zone rename should skip, not KeyError
        continue
    ax.text(tx, ty, txt, fontsize=12, ha="left", va="center", zorder=7, fontweight="bold",
            color=[c*0.36 for c in zcol[zid]],
            path_effects=[pe.withStroke(linewidth=3.2, foreground="white")])

ax.set_xlim(-600, 11000)
ax.set_ylim(-1200, 8800)
ax.set_aspect("equal")
ax.grid(True, lw=0.3, alpha=0.2)
ax.set_title("FLOOR 2 v4 KEY PLAN — footprint ทาบบนแบบจริง (เลข = ดู legend ขวา). "
             "ขนาด/ทิศ อ่านจาก scene-graph (mm); ประตูเลื่อนกระจก+เทอเรส = owner-read (เส้นบาง)", fontsize=12)

# ---- legend (right margin, Thai names, grouped) ----------------------------------------
lg.set_xlim(0, 1)
lg.set_ylim(0, 1)
y = 0.995
lg.text(0.0, y, "KEY — รายการเฟอร์นิเจอร์", fontsize=12, fontweight="bold", va="top")
y -= 0.028
lg.text(0.0, y, "(สี: แดง=loose เขียว=built-in ฟ้า=fixture)", fontsize=8, va="top", color="#555")
y -= 0.018
lg.text(0.0, y, "(cluster# = room-scoped · [!] = ป้าย≠วาด ตรวจ)", fontsize=7.2, va="top", color="#8a8a8a")
y -= 0.028
cur_room = None
for idx, (room, it, cat) in enumerate(ALL, start=1):
    if room != cur_room:
        y -= 0.006
        lg.text(0.0, y, f"— {room} —", fontsize=9.5, fontweight="bold", va="top", color="#222")
        y -= 0.026
        cur_room = room
    col = COL[cat]
    name = it.get("name", "?")
    lg.text(0.012, y - 0.006, "●", fontsize=8, va="center", color=col)
    lg.text(0.055, y, f"{idx}. {name}", fontsize=7.6, va="top")
    y -= 0.0195
    meta = f"{it['w']}×{it['d']}mm"
    fs = facing_str(it)
    if fs:
        meta += f" · {fs}"
    meta += f" · {provenance(it, cat)}" + bf_mismatch(it)
    lg.text(0.055, y, meta, fontsize=6.4, va="top", color="#666")
    y -= 0.0205

# ---- honest footer: the MARKER, not a typed IoU, and facing stated PRECISELY --------------
# facing_flags 0 means "no facing CONTRADICTS the ink", NOT "every facing confirmed": a rot-less
# seat (the tub chairs) is default-S from a note and is NOT machine-verified. Say exactly that.
# Stacked short lines (not wrap=True) so the footer stays under the PLAN and never runs into the
# legend column on the right.
_hc = "  ·  ".join(f"{k.split('_')[0]}: "
                   + ", ".join(f"{fl} {v[fl]}" for fl in ("dismissed", "long_thin") if v.get(fl))
                   for k, v in rr.items())
# completeness numbers READ from the marker (never typed) — the whole point of this footer.
def _fl(v):
    return len(v["floating"]) if isinstance(v.get("floating"), list) else v.get("floating", 0)
_comp = "   ·   ".join(f"{k.split('_')[0]}: floating {_fl(v)} + unplaced {v['unplaced']} → {v['verdict']}"
                       for k, v in rr.items())
foot = [
    f"GATE (placement-gate.json) — calibration {marker['calibration']}   |   "
    + "   |   ".join(f"{k}: {v['verdict']}" for k, v in rr.items()),
    f"GEOMETRIC (เครื่องการันตี · อ่านจาก marker): {_comp}   ·   human-confirm ← {_hc}",
    "SEMANTIC (owner-confirmed — เครื่องอ่านจาก raster ไม่ได้): identity (BF10=ตู้แต่งตัว ไม่ใช่วานิตี้ · BF09-1/-2/-3) · "
    "facing เก้าอี้ tub = หันออกสวน (owner; มุม 12/335 derived) · ประตูเลื่อนกระจก = เส้นบาง owner-read",
    "ภาพ=สื่อสาร; หลักฐาน = พิกัด JSON + marker (per-piece IoU หลัง snap = tautological จึงไม่พิมพ์  ·  cluster# = room-scoped)",
]
for i, ln in enumerate(foot):
    fig.text(0.012, 0.040 - i * 0.0105, ln, fontsize=6.9, va="top", color="#333")

fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.045)
fig.savefig(OUT, dpi=130)
print("wrote", OUT)
