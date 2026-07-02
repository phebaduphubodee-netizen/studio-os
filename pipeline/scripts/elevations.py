"""
elevations.py — INTERIOR-AI interior elevation generator (ezdxf, engine-agnostic).

An interior elevation is a straight-on view of ONE wall: the wall rectangle (width x
ceiling height) with the furniture that sits against/near it projected at its real
height, the door opening (on its wall), and overall dimensions. Reads the SAME validated
spec as everything else, so heights/positions are correct by construction (KB §3).

Each item is drawn on its NEAREST wall. Rugs are skipped (flat on the floor). Output is
one ezdxf doc per wall via build_all(); the standalone CLI also writes DXF + a PNG grid.

    python pipeline/elevations.py [spec.json]

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
    sys.exit("elevations needs ezdxf -> run:  pip install ezdxf")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_2d  # reuse _outdir + export_preview

LAYERS = {"WALLS": 7, "FURNITURE": 5, "DOOR": 3, "DIMENSIONS": 1, "TEXT": 7, "TITLE": 7}
WALLS = ("south", "north", "west", "east")


def _nearest_wall(it, W, D):
    x, y, w, d = float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"])
    gaps = {"south": y, "north": D - (y + d), "west": x, "east": W - (x + w)}
    return min(gaps, key=gaps.get)


def _along(it, wall):
    """(start, end) of an item's footprint along the given wall's horizontal axis."""
    if wall in ("south", "north"):
        return float(it["x"]), float(it["x"]) + float(it["w"])
    return float(it["y"]), float(it["y"]) + float(it["d"])


def wall_elevation(spec, wall):
    """Return an ezdxf doc for one wall's elevation."""
    r = spec["room"]
    W, D, H = float(r["width_in"]), float(r["depth_in"]), float(r["ceiling_in"])
    L = W if wall in ("south", "north") else D              # along-wall length

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.IN
    for name, color in LAYERS.items():
        doc.layers.add(name, color=color)
    msp = doc.modelspace()

    # Wall face rectangle (L wide x H tall).
    msp.add_lwpolyline([(0, 0), (L, 0), (L, H), (0, H)], close=True, dxfattribs={"layer": "WALLS"})

    # Door opening, if this wall carries the door (materializers center it).
    door = r.get("door") or {}
    if door and (door.get("wall", "south") == wall):
        dw = float(door.get("w_in", 32))
        dh = float(door.get("h_in", 80))
        dl = (L - dw) / 2.0
        msp.add_lwpolyline([(dl, 0), (dl + dw, 0), (dl + dw, dh), (dl, dh)],
                           close=True, dxfattribs={"layer": "DOOR"})
        msp.add_text("DOOR", dxfattribs={"layer": "TEXT", "height": 3.0}
                     ).set_placement((dl + dw / 2.0, dh + 4), align=TextEntityAlignment.MIDDLE_CENTER)

    # Furniture assigned to this wall, drawn at (along-wall span) x (0..item height).
    for it in spec.get("items", []):
        if it.get("kind") == "rug":
            continue
        if _nearest_wall(it, W, D) != wall:
            continue
        a0, a1 = _along(it, wall)
        ht = float(it.get("h", 18))
        msp.add_lwpolyline([(a0, 0), (a1, 0), (a1, ht), (a0, ht)],
                           close=True, dxfattribs={"layer": "FURNITURE"})
        label = it.get("name") or it.get("kind") or "item"
        msp.add_text(label, dxfattribs={"layer": "TEXT", "height": 2.5}
                     ).set_placement(((a0 + a1) / 2.0, ht / 2.0), align=TextEntityAlignment.MIDDLE_CENTER)

    # Overall dimensions (length along the bottom, height up the left).
    dh1 = msp.add_linear_dim(base=(0, -16), p1=(0, 0), p2=(L, 0),
                             dimstyle="EZDXF", dxfattribs={"layer": "DIMENSIONS"})
    dh1.render()
    dv = msp.add_linear_dim(base=(-16, 0), p1=(0, 0), p2=(0, H), angle=90,
                            dimstyle="EZDXF", dxfattribs={"layer": "DIMENSIONS"})
    dv.render()

    msp.add_text(f"{wall.upper()} ELEVATION   {L/12:.1f}' wide x {H/12:.1f}' high   |   DRAFT",
                 dxfattribs={"layer": "TITLE", "height": 4.0}).set_placement((0, H + 12))
    return doc


def build_all(spec):
    """Return [(wall, doc), ...] for all four walls."""
    return [(wall, wall_elevation(spec, wall)) for wall in WALLS]


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "living_demo.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    name = spec["room"].get("type", "room")
    out = plan_2d._outdir()
    for wall, doc in build_all(spec):
        dxf = os.path.join(out, f"elev_{name}_{wall}.dxf")
        doc.saveas(dxf)
        png = plan_2d.export_preview(doc, os.path.join(out, f"elev_{name}_{wall}.png"))
        print(f"  {wall}: {dxf}" + (f" (+ {os.path.basename(png)})" if png else ""))
    print("  4 wall elevations generated from the spec — heights correct by construction (DRAFT).")
