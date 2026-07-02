"""
suite_elevations.py — INTERIOR-AI v0.2 interior elevations: METRIC + POLYGON (ezdxf).

The v0.1 elevations.py draws one elevation per wall of a rectangular room in inches.
This v0.2 module draws one elevation per EDGE of a room-spec@0.2 outline polygon (mm):
the L-shaped suite has 6 walls, each gets a straight-on view = the wall rectangle
(edge length x ceiling height) with the built-ins / furniture that sit against that wall
projected at their real heights, plus the door / any windows as openings.

Geometry (the load-bearing part):
  * outward wall normal from the polygon winding (CCW -> outward = (dy,-dx));
  * each item is assigned to the wall it SITS AGAINST = the edge it projects onto with
    the smallest perpendicular distance from the item centre (so a piece is drawn on one
    elevation, the correct one, never all four — the v0.1 nearest-wall rule generalised
    to a polygon);
  * an item's along-wall span = the projection of its footprint corners onto the edge.

Heights come straight from the spec, so the elevation is correct by construction (KB §3).
Windows are drawn from an optional spec["windows"] / room["windows"] list (x,y,w,wall,
sill_mm,head_mm); with none supplied nothing is invented (the furniture plan carries no
window schedule — that gap is flagged for the DWG, not fabricated).

    python pipeline/suite_elevations.py [spec.json]   # -> output/suiteelev_<type>_<n>.dxf (+ .png)

Needs ezdxf; the PNG preview also needs matplotlib.
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    sys.exit("suite_elevations needs ezdxf -> run:  pip install ezdxf")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite_plan   # reuse _metric_dimstyle + export_white_png
import plan_2d      # reuse _outdir

LAYERS = {"WALLS": 7, "BUILTIN": 30, "FURNITURE": 5, "FIXTURE": 6,
          "DOOR": 3, "WINDOW": 4, "DIM": 1, "TEXT": 7, "TITLE": 7}
TXT = 150.0
MIN_EDGE = 600.0   # skip sub-600mm outline segments (jogs, not real walls)
# A real interior elevation shows what is ON / AGAINST the wall (built-ins, wall units,
# wall-hugging furniture) — NOT free-standing pieces marooned in the room. Projecting a
# centre-of-room sofa onto its "nearest" wall (the v0.2 bug) drew a sofa floating on a blank
# wall = meaningless. A piece is drawn only if its nearest face sits within WALL_ADJ_MM of the
# wall; built-ins (wall units by definition) always draw.
WALL_ADJ_MM = 500.0


def _signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def _edges(outline):
    """Return [(P1, P2, along_unit, out_normal_unit, length), ...] with OUTWARD normals."""
    ccw = _signed_area(outline) > 0
    out = []
    n = len(outline)
    for i in range(n):
        p1 = outline[i]; p2 = outline[(i + 1) % n]
        dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        ax, ay = dx / L, dy / L
        # CCW: interior is left of the directed edge -> outward normal is the right normal
        nx, ny = (ay, -ax) if ccw else (-ay, ax)
        out.append((p1, p2, (ax, ay), (nx, ny), L))
    return out


def _proj_u(pt, p1, a):
    return (pt[0] - p1[0]) * a[0] + (pt[1] - p1[1]) * a[1]


def _perp(pt, p1, nrm):
    return (pt[0] - p1[0]) * nrm[0] + (pt[1] - p1[1]) * nrm[1]


def _corners(it):
    x, y, w, d = float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"])
    return [(x, y), (x + w, y), (x + w, y + d), (x, y + d)]


def _assign_items(spec, edges):
    """Map each item/built-in to the index of the wall it sits against — the wall you
    would draw it on in a real elevation. Selection priority (so the drawn along-wall
    width matches the piece's labelled major dimension, never contradicting it):
      1) wall ORIENTATION matches the piece's long axis (a 200x3250 run belongs on a
         wall parallel to its 3250 side, where it reads 3.25 m — not as a 0.2 m sliver);
      2) the footprint actually projects onto the edge span (overlap);
      3) smallest interior perpendicular distance (the closest such wall).
    """
    pieces = ([dict(b, _grp="builtin") for b in spec.get("builtins", [])] +
              [dict(it, _grp="item") for it in spec.get("items", [])])
    assign = {i: [] for i in range(len(edges))}
    for pc in pieces:
        if pc.get("kind") == "rug":
            continue
        cx = float(pc["x"]) + float(pc["w"]) / 2.0
        cy = float(pc["y"]) + float(pc["d"]) / 2.0
        long_axis_x = float(pc["w"]) >= float(pc["d"])   # piece runs along x?
        best, best_d = None, None
        for ei, (p1, p2, a, nrm, L) in enumerate(edges):
            # a wall whose OUTWARD NORMAL is mostly +/-y runs horizontally (along x)
            wall_runs_x = abs(nrm[1]) >= abs(nrm[0])
            orient_match = (wall_runs_x == long_axis_x)
            us = [_proj_u(c, p1, a) for c in _corners(pc)]
            u0, u1 = min(us), max(us)
            overlaps = u1 > 0 and u0 < L
            d = abs(_perp((cx, cy), p1, nrm))
            score = (0 if orient_match else 1, 0 if overlaps else 1, d)
            if best is None or score < best_d:
                best, best_d = ei, score
        if best is None:
            continue
        # Only draw the piece if it actually sits against this wall (built-ins always do).
        # This is the fix for the "free-standing sofa floating on a blank elevation" bug.
        p1b, _p2b, _ab, nrmb, _Lb = edges[best]
        near_face = min(abs(_perp(c, p1b, nrmb)) for c in _corners(pc))
        if pc.get("_grp") == "builtin" or near_face <= WALL_ADJ_MM:
            assign[best].append(pc)
    return assign


def edge_elevation(spec, edges, ei, items):
    """ezdxf doc for the elevation of edge `ei`."""
    r = spec["room"]
    H = float(r.get("ceiling_mm", 2800))
    p1, p2, a, nrm, L = edges[ei]

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    if "THAI" not in doc.styles:
        doc.styles.new("THAI", dxfattribs={"font": "Tahoma.ttf"})
    dimstyle = suite_plan._metric_dimstyle(doc)
    msp = doc.modelspace()

    # wall face
    msp.add_lwpolyline([(0, 0), (L, 0), (L, H), (0, H)], close=True, dxfattribs={"layer": "WALLS"})

    # items against this wall, drawn at (along-wall span) x (0..height). Sorted left->right so
    # the stagger index tracks position: adjacent runs get labels at different heights and
    # don't pile up (the v0.2 "all labels centred at mid-height" collision).
    ordered = sorted(items, key=lambda p: min(_proj_u(c, p1, a) for c in _corners(p)))
    for k, pc in enumerate(ordered):
        us = [_proj_u(c, p1, a) for c in _corners(pc)]
        u0 = max(0.0, min(us)); u1 = min(L, max(us))
        if u1 - u0 < 1.0:
            continue
        ht = float(pc.get("h", 400))
        layer = "BUILTIN" if pc.get("_grp") == "builtin" else "FURNITURE"
        msp.add_lwpolyline([(u0, 0), (u1, 0), (u1, ht), (u0, ht)], close=True, dxfattribs={"layer": layer})
        label = pc.get("name") or pc.get("kind") or "item"
        ly = ht * (0.72 - 0.22 * (k % 3))   # 3 staggered heights so neighbours never collide
        msp.add_text(label, dxfattribs={"layer": "TEXT", "height": 95, "style": "THAI"}
                     ).set_placement((u0 + 80, ly), align=TextEntityAlignment.MIDDLE_LEFT)

    # door + windows that live on this edge (opening rectangles)
    _openings(msp, spec, p1, p2, a, L)

    # overall dims (length along the bottom, height up the left)
    dh = msp.add_linear_dim(base=(0, -450), p1=(0, 0), p2=(L, 0), dimstyle=dimstyle,
                            dxfattribs={"layer": "DIM"}); dh.render()
    dv = msp.add_linear_dim(base=(-450, 0), p1=(0, 0), p2=(0, H), angle=90, dimstyle=dimstyle,
                            dxfattribs={"layer": "DIM"}); dv.render()

    lab = _dir_label(nrm)
    msp.add_text(f"ELEVATION {ei+1} ({lab})   {L/1000:.2f} m wide x {H/1000:.2f} m high   |   DRAFT",
                 dxfattribs={"layer": "TITLE", "height": 200, "style": "THAI"}).set_placement((0, H + 350))
    return doc


def _openings(msp, spec, p1, p2, a, L):
    """Draw the entry door + any windows whose wall segment == this edge."""
    def on_this_edge(ox, oy, wall):
        horiz = abs(p2[1] - p1[1]) < 1.0
        vert = abs(p2[0] - p1[0]) < 1.0
        if wall in ("south", "north") and horiz and abs(oy - p1[1]) < 50.0:
            return True
        if wall in ("east", "west") and vert and abs(ox - p1[0]) < 50.0:
            return True
        return False

    door = spec.get("door")
    if door and on_this_edge(float(door["x"]), float(door["y"]), door.get("wall", "south")):
        u = _proj_u((float(door["x"]), float(door["y"])), p1, a)
        w = float(door.get("w", 900)); h = float(door.get("h", 2000))
        u0, u1 = sorted([u, u + w]); u0 = max(0.0, u0); u1 = min(L, u1)
        msp.add_lwpolyline([(u0, 0), (u1, 0), (u1, h), (u0, h)], close=True, dxfattribs={"layer": "DOOR"})
        msp.add_text("DOOR", dxfattribs={"layer": "TEXT", "height": 120, "style": "THAI"}
                     ).set_placement(((u0 + u1) / 2.0, h + 120), align=TextEntityAlignment.MIDDLE_CENTER)

    for wdw in (spec.get("windows") or spec["room"].get("windows") or []):
        if not on_this_edge(float(wdw["x"]), float(wdw["y"]), wdw.get("wall", "")):
            continue
        u = _proj_u((float(wdw["x"]), float(wdw["y"])), p1, a)
        w = float(wdw.get("w", 1000))
        sill = float(wdw.get("sill_mm", 900)); head = float(wdw.get("head_mm", 2100))
        u0, u1 = sorted([u, u + w]); u0 = max(0.0, u0); u1 = min(L, u1)
        msp.add_lwpolyline([(u0, sill), (u1, sill), (u1, head), (u0, head)], close=True,
                           dxfattribs={"layer": "WINDOW"})
        msp.add_text(wdw.get("name", "window"), dxfattribs={"layer": "TEXT", "height": 110, "style": "THAI"}
                     ).set_placement(((u0 + u1) / 2.0, (sill + head) / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)


def _dir_label(nrm):
    ang = math.degrees(math.atan2(nrm[1], nrm[0]))
    for lo, hi, lab in [(-45, 45, "E"), (45, 135, "N"), (135, 180, "W"), (-180, -135, "W"), (-135, -45, "S")]:
        if lo <= ang < hi:
            return lab
    return "?"


def build_all(spec):
    """Return [(index, dir_label, doc), ...] for every real (>= MIN_EDGE) outline wall."""
    outline = [tuple(p) for p in spec["room"]["outline_mm"]]
    edges = _edges(outline)
    assign = _assign_items(spec, edges)
    out = []
    for ei, e in enumerate(edges):
        if e[4] < MIN_EDGE:
            continue
        out.append((ei, _dir_label(e[3]), edge_elevation(spec, edges, ei, assign[ei])))
    return out


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    name = spec["room"].get("type", "room")
    out = plan_2d._outdir()
    made = build_all(spec)
    for ei, lab, doc in made:
        dxf = os.path.join(out, f"suiteelev_{name}_{ei+1}_{lab}.dxf")
        doc.saveas(dxf)
        png = suite_plan.export_white_png(doc, os.path.join(out, f"suiteelev_{name}_{ei+1}_{lab}.png"))
        print(f"  elev {ei+1} ({lab}): {os.path.basename(dxf)}" + (f" (+ {os.path.basename(png)})" if png else ""))
    print(f"  {len(made)} metric wall elevations — heights straight from the spec (DRAFT).")
    print("  (windows drawn only from spec['windows'] — none invented; that gap needs the DWG.)")
