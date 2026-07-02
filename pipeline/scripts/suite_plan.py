"""
suite_plan.py — INTERIOR-AI v0.2 floor-plan generator: METRIC + POLYGON footprint.

The v0.1 pipeline only did a single rectangular room in inches. Real work (e.g. the
friend's master-bedroom suite in raw/reference/image.png) is an L-shaped, multi-zone,
METRIC plan with an ensuite sub-room and built-in millwork. This module reads a
room-spec@0.2 (all millimetres, y-up, origin bottom-left) and draws a dimensioned
metric floor plan:

  * polygon OUTLINE walls (any shape, not just W x D)
  * SUB-ROOMS (e.g. ensuite) with their own walls + door + fixtures
  * BUILT-IN millwork runs (wardrobe / headboard-TV) as tagged rectangles
  * loose FURNITURE + the entry door swing
  * overall + per-leg DIMENSIONS in mm, and a metric title block (area via shoelace,
    ceiling in m, SCALE 1:50)

    python pipeline/suite_plan.py [spec.json]      # -> output/suiteplan_<type>.dxf (+ .png)

Authored 1:1 in MILLIMETRES (doc.units = MM); a dedicated metric dimstyle sizes the dim
text/arrows for a ~10 m drawing. Needs ezdxf; the PNG preview also needs matplotlib.
This is v0.2 — still a DRAFT a designer refines; positions here are approximated from a
plan image and must be confirmed against the real DWG.

2026-07-01: NCS/AIA layer names + plotted LINE WEIGHTS + a metric GRAPHIC SCALE BAR
(verified standards, research/2026-07-01-plan-read-write-tools-DR.md §7c), matching
plan_2d.py so the whole CD set reads as one professional drawing set.
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
    sys.exit("suite_plan needs ezdxf -> run:  pip install ezdxf")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_2d  # reuse _outdir

# NCS/AIA layer -> (ACI colour for a WHITE sheet, plotted line weight in 1/100 mm).
# Line-weight hierarchy: cut exterior walls heaviest, interior partitions a touch lighter,
# casework/millwork medium, furniture + fixtures light, annotation extra-light.
L_WALL, L_SUBWALL, L_BUILTIN = "A-WALL-FULL", "A-WALL", "A-CASE"
L_FURN, L_FIXT, L_DOOR = "A-FURN", "A-FLOR-FIXT", "A-DOOR"
L_DIM, L_TEXT, L_TITLE = "A-ANNO-DIMS", "A-ANNO-TEXT", "A-ANNO-TEXT"
LAYERS = {
    L_WALL:    (7, 50),    # exterior / full-height walls   0.50 mm
    L_SUBWALL: (8, 40),    # interior partition walls        0.40 mm
    L_BUILTIN: (30, 35),   # built-in millwork / casework    0.35 mm
    L_FURN:    (5, 25),    # loose furniture                 0.25 mm
    L_FIXT:    (6, 25),    # plumbing / fixtures             0.25 mm
    L_DOOR:    (3, 30),    # doors + swing                   0.30 mm
    L_DIM:     (1, 18),    # dimension lines                 0.18 mm (extra-light)
    L_TEXT:    (7, 25),    # labels, title block, scale bar  0.25 mm
}
TXT = 150.0   # mm text height for labels


def _shoelace_sqm(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0 / 1e6   # mm^2 -> m^2


def _metric_dimstyle(doc):
    """A dimstyle sized for a ~10 000 mm drawing (v0.1's inch defaults are invisible here)."""
    name = "MET"
    ds = doc.dimstyles.get(name) if name in doc.dimstyles else doc.dimstyles.new(name)
    a = ds.dxf
    a.dimtxt = 180      # text height (mm)
    a.dimasz = 140      # arrow size
    a.dimexe = 70       # extension line past the dim line
    a.dimexo = 150      # offset of the extension line from the measured point
    a.dimgap = 55       # gap around the text
    a.dimdec = 0        # whole millimetres
    a.dimtad = 1        # text above the dim line
    a.dimlfac = 1.0     # already in mm
    return name


def _rect(msp, x, y, w, d, layer):
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + d), (x, y + d)],
                       close=True, dxfattribs={"layer": layer})


def _label(msp, text, cx, cy, height=TXT, layer=L_TEXT):
    msp.add_text(str(text), dxfattribs={"layer": layer, "height": height, "style": "THAI"}
                 ).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)


def _door_swing(msp, x, y, w, wall):
    """Draw a leaf + 90deg swing arc for a door on the given wall side."""
    if wall == "south":       # horizontal wall (y const), swing up into the room
        msp.add_line((x, y), (x, y + w), dxfattribs={"layer": L_DOOR})
        msp.add_arc(center=(x, y), radius=w, start_angle=0, end_angle=90, dxfattribs={"layer": L_DOOR})
    elif wall == "north":
        msp.add_line((x, y), (x, y - w), dxfattribs={"layer": L_DOOR})
        msp.add_arc(center=(x, y), radius=w, start_angle=270, end_angle=360, dxfattribs={"layer": L_DOOR})
    elif wall == "east":      # vertical wall (x const), swing into the room (-x, +y)
        msp.add_line((x, y), (x, y + w), dxfattribs={"layer": L_DOOR})
        msp.add_arc(center=(x, y), radius=w, start_angle=90, end_angle=180, dxfattribs={"layer": L_DOOR})
    else:                     # west
        msp.add_line((x, y), (x, y + w), dxfattribs={"layer": L_DOOR})
        msp.add_arc(center=(x, y), radius=w, start_angle=0, end_angle=90, dxfattribs={"layer": L_DOOR})


def build_dxf(spec):
    r = spec["room"]
    outline = [tuple(p) for p in r["outline_mm"]]
    ceiling = float(r.get("ceiling_mm", 2800))
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    W, D = max(xs), max(ys)

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$LWDISPLAY"] = 1            # show line weights (so the hierarchy is visible)
    for name, (color, lw) in LAYERS.items():
        doc.layers.add(name, color=color, lineweight=lw)
    # A Thai-capable text style so Thai labels render (in CAD and in the matplotlib preview,
    # which honors the style's TTF). Tahoma ships on Windows and covers Thai.
    if "THAI" not in doc.styles:
        doc.styles.new("THAI", dxfattribs={"font": "Tahoma.ttf"})
    dimstyle = _metric_dimstyle(doc)
    msp = doc.modelspace()

    # 1) outer polygon walls
    msp.add_lwpolyline(outline, close=True, dxfattribs={"layer": L_WALL})

    # 2) entry door
    door = spec.get("door")
    if door:
        _door_swing(msp, float(door["x"]), float(door["y"]), float(door.get("w", 900)), door.get("wall", "south"))

    # 3) sub-rooms (ensuite): walls + door + fixtures
    for sr in spec.get("subrooms", []):
        so = [tuple(p) for p in sr["outline_mm"]]
        msp.add_lwpolyline(so, close=True, dxfattribs={"layer": L_SUBWALL})
        sxs = [p[0] for p in so]; sys_ = [p[1] for p in so]
        _label(msp, sr.get("th") or sr.get("name", "room"),
               sum(sxs) / len(sxs), max(sys_) - 250, height=TXT, layer=L_TEXT)
        sd = sr.get("door")
        if sd:
            _door_swing(msp, float(sd["x"]), float(sd["y"]), float(sd.get("w", 800)), sd.get("wall", "east"))
        for fx in sr.get("fixtures", []):
            _rect(msp, float(fx["x"]), float(fx["y"]), float(fx["w"]), float(fx["d"]), L_FIXT)
            _label(msp, fx.get("name", fx.get("kind", "")),
                   float(fx["x"]) + float(fx["w"]) / 2, float(fx["y"]) + float(fx["d"]) / 2,
                   height=110, layer=L_FIXT)

    # 4) built-in millwork
    for b in spec.get("builtins", []):
        _rect(msp, float(b["x"]), float(b["y"]), float(b["w"]), float(b["d"]), L_BUILTIN)
        _label(msp, b.get("name", b.get("kind", "built-in")),
               float(b["x"]) + float(b["w"]) / 2, float(b["y"]) + float(b["d"]) / 2, height=120, layer=L_BUILTIN)

    # 5) loose furniture
    for it in spec.get("items", []):
        _rect(msp, float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"]), L_FURN)
        _label(msp, it.get("name") or it.get("kind", "item"),
               float(it["x"]) + float(it["w"]) / 2, float(it["y"]) + float(it["d"]) / 2, height=120, layer=L_FURN)

    # 6) dimensions (overall width + the two depth legs of the L)
    m = 700.0
    right_y0 = min(p[1] for p in outline if p[0] >= W - 1)   # bottom of the right (shallow) leg
    dims = [
        ((0, -m), (0, 0), (W, 0), 0),                        # overall width along the bottom
        ((-m, 0), (0, 0), (0, D), 90),                       # left (deep) leg
        ((W + m, right_y0), (W, right_y0), (W, D), 90),      # right (shallow) leg
    ]
    for base, p1, p2, ang in dims:
        dim = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle=dimstyle,
                                 dxfattribs={"layer": L_DIM})
        dim.render()

    _title_block(msp, spec, outline, W, D, ceiling)
    _scale_bar(msp, x0=0.0, y0=-2100.0)
    return doc


def _title_block(msp, spec, outline, W, D, ceiling):
    sqm = _shoelace_sqm(outline)
    rtype = spec["room"].get("type", "room").replace("_", " ").upper()
    lines = [
        f"{rtype}   bounding {W/1000:.1f} x {D/1000:.1f} m   ~{sqm:.1f} sqm   (ceiling {ceiling/1000:.1f} m)",
        "SCALE 1:50   |   DRAFT MASSING v0.2 — outline = APPROX. bounding envelope; real walls / windows / exact positions",
        "NOT yet traced from the DWG (redacted-dwg). NOT a construction set — furniture + built-in SIZES are DWG-extracted; positions approximate.",
        "INTERIOR-AI  (dimensions in millimetres; NCS layers + line weights)",
    ]
    ty = -1000.0
    for ln in lines:
        msp.add_text(ln, dxfattribs={"layer": L_TITLE, "height": 200, "style": "THAI"}).set_placement((0, ty))
        ty -= 320.0


def _scale_bar(msp, x0, y0, metres=5):
    """A metric graphic scale bar (drawn in real mm), so measurements stay true even if the
    sheet is photocopied or printed at a non-standard size (verified standard, §7c)."""
    length = metres * 1000
    msp.add_line((x0, y0), (x0 + length, y0), dxfattribs={"layer": L_TEXT})
    for mm in range(0, metres + 1):
        x = x0 + mm * 1000
        msp.add_line((x, y0), (x, y0 + 150.0), dxfattribs={"layer": L_TEXT})
        msp.add_text(str(mm), dxfattribs={"layer": L_TEXT, "height": 150, "style": "THAI"}
                     ).set_placement((x, y0 + 200.0), align=TextEntityAlignment.BOTTOM_CENTER)
    msp.add_text("METRES   (graphic scale — 1:50)",
                 dxfattribs={"layer": L_TEXT, "height": 150, "style": "THAI"}
                 ).set_placement((x0, y0 - 200.0), align=TextEntityAlignment.TOP_LEFT)


def export_white_png(doc, path):
    """White-background PNG (black linework) via ezdxf's matplotlib backend."""
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        from ezdxf.addons.drawing.properties import LayoutProperties
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    # Thai-capable font so Thai labels don't render as tofu boxes (Windows ships Tahoma /
    # Leelawadee UI; both cover Thai). Falls back to DejaVu Sans if none are present.
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Tahoma", "Leelawadee UI", "TH Sarabun New", "DejaVu Sans"]
    lp = LayoutProperties.from_layout(doc.modelspace())
    lp.set_colors("#FFFFFF")
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(
        doc.modelspace(), finalize=True, layout_properties=lp)
    ax.set_axis_off()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    name = spec["room"].get("type", "room")
    out = plan_2d._outdir()
    doc = build_dxf(spec)
    dxf = os.path.join(out, f"suiteplan_{name}.dxf")
    doc.saveas(dxf)
    png = export_white_png(doc, os.path.join(out, f"suiteplan_{name}.png"))
    print(f"  wrote {dxf}" + (f" (+ {os.path.basename(png)})" if png else " (PNG skipped: pip install matplotlib)"))
    print("  v0.2 metric polygon plan — NCS layers + line weights + metric scale bar (DRAFT, positions approximated).")
