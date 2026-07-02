"""
plan_2d.py — INTERIOR-AI 2D dimensioned floor plan ("แบบ") generator.

Layer-3 deliverable, engine-agnostic (no Blender, no SketchUp). Reads the SAME
validated spec and emits a dimensioned DXF (editable CAD master) straight from the
exact coordinates — plus a PNG/PDF preview if matplotlib is present. Research
(2026-06-30) showed this from-coordinates route is the cheapest, fully-headless way
to produce the construction "แบบ": LayOut can't run headless, and we already hold
the exact numbers, so there is nothing to "extract" — dimensions read straight from
the coordinate deltas and are therefore correct by construction.

2026-07-01: upgraded to professional drafting convention (DR + verified standards,
research/2026-07-01-plan-read-write-tools-DR.md §7c):
  * NCS / AIA layer names with plotted LINE WEIGHTS (walls heaviest -> dims lightest)
  * TWO-TIER bottom dimensioning (inner = wall segments + door opening, outer = overall)
  * a GRAPHIC SCALE BAR on the sheet (measurements survive photocopy / rescale)
These are what make a generated plan read as professional rather than draft.

    python pipeline/plan_2d.py pipeline/specs/living_demo.json

Needs ezdxf:  pip install ezdxf   (the PNG/PDF preview also needs matplotlib)
DXF is authored 1:1 in INCHES (real-world); plot scale is a title-block note.
"""
import json
import os
import sys

try:  # keep Thai ("แบบ") + output legible on a cp1252 Windows console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    sys.exit("plan_2d needs ezdxf -> run:  pip install ezdxf")

# NCS/AIA layer -> (AutoCAD Color Index, plotted line weight in 1/100 mm).
# Line-weight hierarchy per verified standard (floor-plan cut plane): cut structural
# walls heaviest (0.50mm), doors/casework medium (0.30mm), windows 0.25mm, furniture
# light (0.25mm), annotation/dimensions extra-light (0.18mm). Values are restricted to
# ezdxf's valid DXF line-weight enum (…,18,25,30,35,40,50,…).
LAYERS = {
    "A-WALL-FULL": (7, 50),    # full-height structural walls  0.50 mm
    "A-DOOR":      (3, 30),    # doors + swing                 0.30 mm
    "A-GLAZ":      (4, 25),    # windows / glazing (if present) 0.25 mm
    "A-FURN":      (5, 25),    # furniture / FF&E              0.25 mm
    "A-ANNO-DIMS": (1, 18),    # dimension lines               0.18 mm (extra-light)
    "A-ANNO-TEXT": (7, 25),    # labels, title block, notes    0.25 mm
}


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_dxf(spec):
    doc = ezdxf.new("R2010", setup=True)   # setup=True => standard dimstyles incl 'EZDXF'
    doc.units = ezdxf.units.IN
    doc.header["$LWDISPLAY"] = 1            # show line weights (so the hierarchy is visible)
    for name, (color, lw) in LAYERS.items():
        doc.layers.add(name, color=color, lineweight=lw)
    msp = doc.modelspace()

    r = spec["room"]
    W = float(r["width_in"])
    D = float(r["depth_in"])
    door = r.get("door") or {"w_in": 32}     # `or` also catches an explicit JSON null
    dw = float(door.get("w_in", 32))
    if dw >= W:
        raise ValueError(f"door width {dw}\" >= wall width {W}\" - cannot place a centered door (check the spec)")
    door_l = (W - dw) / 2.0
    door_r = (W + dw) / 2.0

    # Walls: W, N, E run as one open polyline; the south (y=0) edge is split for the door.
    msp.add_lwpolyline([(0, 0), (0, D), (W, D), (W, 0)], dxfattribs={"layer": "A-WALL-FULL"})
    msp.add_line((0, 0), (door_l, 0), dxfattribs={"layer": "A-WALL-FULL"})
    msp.add_line((door_r, 0), (W, 0), dxfattribs={"layer": "A-WALL-FULL"})
    # Door leaf + 90deg swing arc (hinge at the left jamb).
    msp.add_line((door_l, 0), (door_l, dw), dxfattribs={"layer": "A-DOOR"})
    msp.add_arc(center=(door_l, 0), radius=dw, start_angle=0, end_angle=90,
                dxfattribs={"layer": "A-DOOR"})

    # Furniture footprints + centered labels (rugs omitted — they clutter a plan).
    for it in spec.get("items", []):
        if it.get("kind") == "rug":
            continue
        x, y = float(it["x"]), float(it["y"])
        w, d = float(it["w"]), float(it["d"])
        msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + d), (x, y + d)],
                           close=True, dxfattribs={"layer": "A-FURN"})
        label = it.get("name") or it.get("kind") or "item"   # lazy: never index a missing key
        msp.add_text(label,
                     dxfattribs={"layer": "A-ANNO-TEXT", "height": 3.0}
                     ).set_placement((x + w / 2.0, y + d / 2.0),
                                     align=TextEntityAlignment.MIDDLE_CENTER)

    _dimension_south(msp, W, door_l, door_r)   # 2-tier bottom dims (inner segments + outer overall)
    # Vertical overall depth (single tier — a plain room has no interior offsets to break out).
    d2 = msp.add_linear_dim(base=(-18, 0), p1=(0, 0), p2=(0, D), angle=90,
                            dimstyle="EZDXF", dxfattribs={"layer": "A-ANNO-DIMS"})
    d2.render()

    _title_block(msp, spec, W, D)
    _scale_bar(msp, x0=0.0, y0=-72.0)
    return doc


def _dimension_south(msp, W, door_l, door_r):
    """Two concentric tiers on the south (door) wall, straight from coordinates:
    INNER = individual segments incl. the door opening; OUTER = overall width.
    (The 3rd tier — a structural grid — only applies to multi-room plans.)"""
    # Inner tier: wall / opening segments, chained on one dimension line.
    for a, b in [(0.0, door_l), (door_l, door_r), (door_r, W)]:
        if b - a <= 0:
            continue
        di = msp.add_linear_dim(base=(0, -10), p1=(a, 0), p2=(b, 0),
                                dimstyle="EZDXF", dxfattribs={"layer": "A-ANNO-DIMS"})
        di.render()
    # Outer tier: overall width, set below the inner string.
    do = msp.add_linear_dim(base=(0, -24), p1=(0, 0), p2=(W, 0),
                            dimstyle="EZDXF", dxfattribs={"layer": "A-ANNO-DIMS"})
    do.render()


def _title_block(msp, spec, W, D):
    r = spec["room"]
    sqft = round((W * D) / 144.0)
    lines = [
        f"ROOM: {r.get('type', 'room').upper()}   {W / 12:.1f}' x {D / 12:.1f}'  ({sqft} sqft)",
        "SCALE 1/4\" = 1'-0\"   |   DRAFT - verify vs local code",
        "INTERIOR-AI  (dimensions in inches; NCS layers + line weights)",
    ]
    ty = -40.0
    for ln in lines:
        msp.add_text(ln, dxfattribs={"layer": "A-ANNO-TEXT", "height": 4.0}).set_placement((0, ty))
        ty -= 7.0


def _scale_bar(msp, x0, y0, feet=8, step_ft=2):
    """A graphic scale bar drawn in real inches, so measurements stay true even if the
    sheet is photocopied or printed at a non-standard size (verified standard, §7c)."""
    length_in = feet * 12
    msp.add_line((x0, y0), (x0 + length_in, y0), dxfattribs={"layer": "A-ANNO-TEXT"})
    for f in range(0, feet + 1, step_ft):
        x = x0 + f * 12
        msp.add_line((x, y0), (x, y0 + 4.0), dxfattribs={"layer": "A-ANNO-TEXT"})
        msp.add_text(str(f), dxfattribs={"layer": "A-ANNO-TEXT", "height": 3.0}
                     ).set_placement((x, y0 + 5.0), align=TextEntityAlignment.BOTTOM_CENTER)
    msp.add_text("FEET   (graphic scale — 1/4\" = 1'-0\")",
                 dxfattribs={"layer": "A-ANNO-TEXT", "height": 3.0}
                 ).set_placement((x0, y0 - 5.0), align=TextEntityAlignment.TOP_LEFT)


def export_preview(doc, path):
    """PNG/PDF via ezdxf's matplotlib add-on, if matplotlib is installed."""
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _outdir():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(os.path.dirname(here), "output")
    os.makedirs(out, exist_ok=True)
    return out


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "living_demo.json")
    spec = load_spec(spec_path)
    doc = build_dxf(spec)
    name = spec["room"].get("type", "room")
    dxf_path = os.path.join(_outdir(), f"plan_{name}.dxf")
    doc.saveas(dxf_path)
    print(f"  wrote DXF: {dxf_path}")
    preview = export_preview(doc, os.path.join(_outdir(), f"plan_{name}.png"))
    print(f"  wrote preview: {preview}" if preview else
          "  (preview skipped - pip install matplotlib for a PNG)")
    print("  2D แบบ generated from coordinates - dimensions correct by construction.")
    print("  NCS layers + line weights + 2-tier dims + graphic scale bar (v0.2 DRAFT).")
    print("  (verify scale + local code before client use)")
