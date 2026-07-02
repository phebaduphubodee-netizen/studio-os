"""
rcp.py — INTERIOR-AI Reflected Ceiling Plan generator (ezdxf, engine-agnostic).

A reflected ceiling plan shows the ceiling as if mirrored on the floor, so it is drawn
in the SAME orientation as the floor plan (they overlay). Reads the SAME validated spec,
derives the lighting layer (lighting.py), and draws each fixture as a tagged symbol +
a type legend -> DXF (+ PNG preview). Fixture positions/tags are identical to the
lighting schedule (the relational rule, KB §3) because both come from lighting.py.

    python pipeline/rcp.py [spec.json]

Needs ezdxf (already used by plan_2d); PNG preview also needs matplotlib.
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
    sys.exit("rcp needs ezdxf -> run:  pip install ezdxf")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lighting
import plan_2d  # reuse _outdir + export_preview (same DXF->PNG path)

LAYERS = {
    "CEILING": 8, "LIGHT-AMBIENT": 5, "LIGHT-TASK": 3, "LIGHT-ACCENT": 1,
    "TAG": 2, "TITLE": 7, "LEGEND": 7,
}
_LAYER_OF = {"ambient": "LIGHT-AMBIENT", "task": "LIGHT-TASK", "accent": "LIGHT-ACCENT"}


def _draw_fixture(msp, f, tag):
    """Symbol per design layer: downlight = circle+cross; pendant = circle+dot;
    accent = circle+stub. Tag text sits up-right of the fixture."""
    x, y = float(f["x"]), float(f["y"])
    layer = _LAYER_OF.get(f.get("layer"), "LIGHT-AMBIENT")
    r = 4.0
    msp.add_circle((x, y), r, dxfattribs={"layer": layer})
    if f.get("layer") == "task":                       # pendant: center dot
        msp.add_circle((x, y), 1.0, dxfattribs={"layer": layer})
    elif f.get("layer") == "accent":                   # accent: directional stub
        msp.add_line((x, y), (x + r + 3, y), dxfattribs={"layer": layer})
    else:                                              # downlight: cross
        msp.add_line((x - r, y), (x + r, y), dxfattribs={"layer": layer})
        msp.add_line((x, y - r), (x, y + r), dxfattribs={"layer": layer})
    msp.add_text(tag, dxfattribs={"layer": "TAG", "height": 4.0}
                 ).set_placement((x + r + 1.5, y + r + 1.5), align=TextEntityAlignment.BOTTOM_LEFT)


def build_dxf(spec, fixtures=None):
    """Build the RCP DXF. Pass `fixtures` (from lighting.plan_lighting) to GUARANTEE the
    RCP matches a lighting schedule built from the same list; if None, derive them here."""
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.IN
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    msp = doc.modelspace()

    r = spec["room"]
    W, D = float(r["width_in"]), float(r["depth_in"])
    door = r.get("door") or {"w_in": 32}
    dw = float(door.get("w_in", 32))
    door_l, door_r = (W - dw) / 2.0, (W + dw) / 2.0

    # Room outline on the CEILING layer (door gap kept so it aligns with the floor plan).
    msp.add_lwpolyline([(0, 0), (0, D), (W, D), (W, 0)], dxfattribs={"layer": "CEILING"})
    msp.add_line((0, 0), (door_l, 0), dxfattribs={"layer": "CEILING"})
    msp.add_line((door_r, 0), (W, 0), dxfattribs={"layer": "CEILING"})

    if fixtures is None:
        fixtures, _ = lighting.plan_lighting(spec)
    type_rows, tag_of = lighting.type_table(fixtures)
    for f in fixtures:
        _draw_fixture(msp, f, tag_of[id(f)])

    _legend(msp, type_rows, W, D)
    _title_block(msp, spec, W, D)
    return doc, fixtures, type_rows


def _legend(msp, type_rows, W, D):
    # DXF y is up, so render top-down: title highest, then rows descending (A above B).
    top = D + 14.0 + (len(type_rows) + 1) * 7.0
    msp.add_text("LIGHTING LEGEND", dxfattribs={"layer": "LEGEND", "height": 5.0}).set_placement((0, top))
    ty = top - 8.0
    for t in type_rows:
        line = f"{t['tag']}  {t['type']}  -  {t['lumens']}lm / {t['cct_k']}K / CRI{t['cri']}  ({t['layer']})  x{t['count']}"
        msp.add_text(line, dxfattribs={"layer": "LEGEND", "height": 3.5}).set_placement((0, ty))
        ty -= 6.0


def _title_block(msp, spec, W, D):
    r = spec["room"]
    lines = [
        f"REFLECTED CEILING PLAN: {r.get('type', 'room').upper()}   {W/12:.1f}' x {D/12:.1f}'   (ceiling {float(r.get('ceiling_in',96))/12:.1f}')",
        "Oriented to match the floor plan  |  SCALE 1/4\" = 1'-0\"  |  DRAFT - verify vs local code",
        "INTERIOR-AI  (dimensions in inches; auto-layout lighting - a designer refines)",
    ]
    ty = -28.0
    for ln in lines:
        msp.add_text(ln, dxfattribs={"layer": "TITLE", "height": 4.0}).set_placement((0, ty))
        ty -= 7.0


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "living_demo.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    doc, fixtures, type_rows = build_dxf(spec)
    name = spec["room"].get("type", "room")
    out = plan_2d._outdir()
    dxf_path = os.path.join(out, f"rcp_{name}.dxf")
    doc.saveas(dxf_path)
    print(f"  wrote RCP DXF: {dxf_path}  ({len(fixtures)} fixtures, {len(type_rows)} types)")
    preview = plan_2d.export_preview(doc, os.path.join(out, f"rcp_{name}.png"))
    print(f"  wrote RCP preview: {preview}" if preview else
          "  (preview skipped - pip install matplotlib for a PNG)")
    print("  RCP fixtures + tags match the lighting schedule by construction (KB §3).")
    print("  (v0.1 DRAFT lighting layout - illuminance check is the next step, KB §10 #2)")
