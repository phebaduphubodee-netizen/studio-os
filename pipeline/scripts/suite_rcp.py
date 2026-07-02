"""
suite_rcp.py — INTERIOR-AI v0.2 Reflected Ceiling Plan: METRIC + POLYGON (ezdxf).

The v0.1 rcp.py draws a rectangular ceiling in inches. This v0.2 module draws the RCP for
a room-spec@0.2 (L-shaped outline in mm, ensuite sub-room) in the SAME orientation as the
metric floor plan (they overlay), using the metric lighting layer (suite_lighting):

  * the outline polygon on the CEILING layer, with the entry-door gap kept so it aligns
    with suite_plan's floor plan
  * each sub-room (ensuite) outline on the ceiling (it has its own dropped ceiling)
  * every fixture as a tagged symbol (downlight = circle+cross, pendant = circle+dot,
    accent = circle+stub) + a TYPE legend

Fixture positions/tags are identical to the lighting schedule because both derive from
suite_lighting.plan_lighting + lighting.type_table (the relational rule, KB §3).

    python pipeline/suite_rcp.py [spec.json]      # -> output/suitercp_<type>.dxf (+ .png)

Needs ezdxf; the PNG preview also needs matplotlib.
"""
import json
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
    sys.exit("suite_rcp needs ezdxf -> run:  pip install ezdxf")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lighting          # type_table (tagging)
import suite_lighting    # metric polygon lighting layer
import suite_plan        # reuse export_white_png + _metric_dimstyle conventions
import plan_2d           # reuse _outdir

# ACI colours chosen for legibility on a WHITE sheet (match suite_plan's palette).
LAYERS = {"CEILING": 8, "SUBCEIL": 8, "LIGHT-AMBIENT": 5, "LIGHT-TASK": 3,
          "LIGHT-ACCENT": 1, "TAG": 2, "TITLE": 7, "LEGEND": 7}
_LAYER_OF = {"ambient": "LIGHT-AMBIENT", "task": "LIGHT-TASK", "accent": "LIGHT-ACCENT"}
SYMR = 80.0     # fixture symbol radius (mm)
TXT = 150.0     # tag text height (mm)


def _draw_fixture(msp, f, tag):
    x, y = float(f["x"]), float(f["y"])
    layer = _LAYER_OF.get(f.get("layer"), "LIGHT-AMBIENT")
    msp.add_circle((x, y), SYMR, dxfattribs={"layer": layer})
    if f.get("layer") == "task":                        # pendant: centre dot
        msp.add_circle((x, y), SYMR * 0.25, dxfattribs={"layer": layer})
    elif f.get("layer") == "accent":                    # accent: directional stub
        msp.add_line((x, y), (x + SYMR + 60, y), dxfattribs={"layer": layer})
    else:                                               # downlight: cross
        msp.add_line((x - SYMR, y), (x + SYMR, y), dxfattribs={"layer": layer})
        msp.add_line((x, y - SYMR), (x, y + SYMR), dxfattribs={"layer": layer})
    msp.add_text(tag, dxfattribs={"layer": "TAG", "height": TXT, "style": "THAI"}
                 ).set_placement((x + SYMR + 30, y + SYMR + 30), align=TextEntityAlignment.BOTTOM_LEFT)


def _door_gap_polyline(msp, outline, door, layer):
    """Draw the outline as segments, leaving a gap on the edge that carries the entry
    door so the RCP aligns with the floor plan's door opening. Falls back to a closed
    polyline if the door can't be matched to an edge."""
    if not door:
        msp.add_lwpolyline(outline, close=True, dxfattribs={"layer": layer})
        return
    dx, dy, dwid = float(door["x"]), float(door["y"]), float(door.get("w", 900))
    wall = door.get("wall", "south")
    n = len(outline)
    drew_gap = False
    for i in range(n):
        ax, ay = outline[i]; bx, by = outline[(i + 1) % n]
        horiz = abs(by - ay) < 1.0
        vert = abs(bx - ax) < 1.0
        on_edge = ((wall in ("south", "north") and horiz and abs(ay - dy) < 1.0
                    and min(ax, bx) - 1 <= dx <= max(ax, bx) + 1) or
                   (wall in ("east", "west") and vert and abs(ax - dx) < 1.0
                    and min(ay, by) - 1 <= dy <= max(ay, by) + 1))
        if on_edge and not drew_gap:
            if horiz:
                lo, hi = sorted([dx, dx + dwid])
                msp.add_line((ax, ay), (lo, ay), dxfattribs={"layer": layer})
                msp.add_line((hi, ay), (bx, by), dxfattribs={"layer": layer})
            else:
                lo, hi = sorted([dy, dy + dwid])
                msp.add_line((ax, ay), (ax, lo), dxfattribs={"layer": layer})
                msp.add_line((ax, hi), (bx, by), dxfattribs={"layer": layer})
            drew_gap = True
        else:
            msp.add_line((ax, ay), (bx, by), dxfattribs={"layer": layer})
    if not drew_gap:   # door didn't match any edge -> just close the outline
        msp.add_lwpolyline(outline, close=True, dxfattribs={"layer": layer})


def build_dxf(spec, fixtures=None):
    """Build the metric RCP DXF. Pass `fixtures` (from suite_lighting.plan_lighting) to
    GUARANTEE it matches a schedule built from the same list; else derive here."""
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    if "THAI" not in doc.styles:
        doc.styles.new("THAI", dxfattribs={"font": "Tahoma.ttf"})
    msp = doc.modelspace()

    r = spec["room"]
    outline = [tuple(p) for p in r["outline_mm"]]

    # outline on the CEILING layer, door gap kept (aligns to the floor plan)
    _door_gap_polyline(msp, outline, spec.get("door"), "CEILING")
    for sr in spec.get("subrooms", []):
        so = [tuple(p) for p in sr["outline_mm"]]
        msp.add_lwpolyline(so, close=True, dxfattribs={"layer": "SUBCEIL"})

    if fixtures is None:
        fixtures, _ = suite_lighting.plan_lighting(spec)
    type_rows, tag_of = lighting.type_table(fixtures)
    for f in fixtures:
        _draw_fixture(msp, f, tag_of[id(f)])

    W = max(p[0] for p in outline); D = max(p[1] for p in outline)
    _legend(msp, type_rows, W, D)
    _title_block(msp, spec, outline, W, D)
    return doc, fixtures, type_rows


def _legend(msp, type_rows, W, D):
    top = D + 300.0 + (len(type_rows) + 1) * 260.0
    msp.add_text("LIGHTING LEGEND", dxfattribs={"layer": "LEGEND", "height": 200, "style": "THAI"}
                 ).set_placement((0, top))
    ty = top - 320.0
    for t in type_rows:
        line = (f"{t['tag']}  {t['type']}  -  {t['lumens']}lm / {t['cct_k']}K / CRI{t['cri']}  "
                f"({t['layer']})  x{t['count']}")
        msp.add_text(line, dxfattribs={"layer": "LEGEND", "height": 150, "style": "THAI"}
                     ).set_placement((0, ty))
        ty -= 240.0


def _title_block(msp, spec, outline, W, D):
    r = spec["room"]
    sqm = suite_plan._shoelace_sqm(outline)
    rtype = r.get("type", "room").replace("_", " ").upper()
    lines = [
        f"REFLECTED CEILING PLAN: {rtype}   bounding {W/1000:.1f} x {D/1000:.1f} m   ~{sqm:.1f} sqm   (ceiling {float(r.get('ceiling_mm',2800))/1000:.1f} m)",
        "Oriented to match the floor plan   |   SCALE 1:50   |   DRAFT — auto-layout lighting, verify vs local code",
        "INTERIOR-AI  (dimensions in millimetres; lumen-method downlights — a designer refines)",
    ]
    ty = -700.0
    for ln in lines:
        msp.add_text(ln, dxfattribs={"layer": "TITLE", "height": 200, "style": "THAI"}).set_placement((0, ty))
        ty -= 320.0


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    doc, fixtures, type_rows = build_dxf(spec)
    name = spec["room"].get("type", "room")
    out = plan_2d._outdir()
    dxf = os.path.join(out, f"suitercp_{name}.dxf")
    doc.saveas(dxf)
    png = suite_plan.export_white_png(doc, os.path.join(out, f"suitercp_{name}.png"))
    print(f"  wrote RCP DXF: {dxf}  ({len(fixtures)} fixtures, {len(type_rows)} types)")
    print(f"  wrote RCP preview: {png}" if png else "  (preview skipped: pip install matplotlib)")
    print("  metric polygon RCP — fixtures + tags match the lighting schedule by construction (KB §3).")
