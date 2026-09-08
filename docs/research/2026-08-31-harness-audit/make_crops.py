"""Build the B-experiment reader bundles: RAW and RECOLOR crops of the floor-2 furniture plan.

RECOLOR arm = the video's dims-vs-walls separation lever, implemented for THIS sheet's
ink classes by pen weight (walls 0.84pt -> black, furniture 0.48-0.6 -> blue,
text/dims/thin 0.12-0.24 -> red). Deterministic replay of page vector drawings.
Crops are identical pixel windows in both arms so the arm is the only variable.
"""
import fitz
from PIL import Image
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "..", "..", "..", "projects", "PRJ-2026-002_c001-house",
                   "00_intake", "raw-local",
                   "The City สาทร - สุขสวัสดิ์_Plan funiture 02.pdf")
PAGE = 1  # floor 2

# pixel boxes measured on the 2.3x overview render (page2_overview.png)
CROPS = {
    "ms_overview": {"zoom": 4.5, "box23": (274, 589, 1397, 1562)},
    "bay_zoom":    {"zoom": 7.0, "box23": (411, 603, 1123, 1233)},
    "bed_zoom":    {"zoom": 7.0, "box23": (274, 1028, 986, 1562)},
}

def colour_for_width(w):
    if w is None:
        return None
    if w >= 0.7:
        return (0, 0, 0)          # walls
    if w >= 0.3:
        return (0, 0, 0.85)       # furniture / glazing conventions
    return (0.85, 0, 0)           # text glyphs, dims, thin annotation


def build_recolor_doc(src_doc):
    """Replay page vectors into DISPLAY space (rotation applied via rotation_matrix)
    on a rotation-0 page whose size equals the displayed page, so renders of the
    replay and of the source page are pixel-aligned for identical crop windows."""
    page = src_doc[PAGE]
    m = page.rotation_matrix  # maps unrotated drawing coords -> displayed coords
    out = fitz.open()
    np_ = out.new_page(width=page.rect.width, height=page.rect.height)
    shape = np_.new_shape()
    n_items = 0

    def tp(p):
        return fitz.Point(p) * m

    for d in page.get_drawings():
        stroke = colour_for_width(d.get("width"))
        fill = d.get("fill")
        for item in d["items"]:
            kind = item[0]
            if kind == "l":
                shape.draw_line(tp(item[1]), tp(item[2]))
            elif kind == "c":
                shape.draw_bezier(tp(item[1]), tp(item[2]), tp(item[3]), tp(item[4]))
            elif kind == "re":
                shape.draw_quad(item[1].quad * m)
            elif kind == "qu":
                shape.draw_quad(item[1] * m)
            n_items += 1
        shape.finish(color=stroke if d["type"] in ("s", "fs") else None,
                     fill=fill if d["type"] in ("f", "fs") else None,
                     width=d.get("width") or 0.3,
                     even_odd=d.get("even_odd", False),
                     closePath=d.get("closePath", False))
    shape.commit()
    print(f"replayed {n_items} vector items")
    return out


def render_crops(doc, page_index, tag, outdir):
    os.makedirs(outdir, exist_ok=True)
    page = doc[page_index]
    for name, spec in CROPS.items():
        z = spec["zoom"]
        pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
        full = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        s = z / 2.3
        x0, y0, x1, y1 = [int(round(v * s)) for v in spec["box23"]]
        crop = full.crop((x0, y0, x1, y1))
        p = os.path.join(outdir, f"{name}.png")
        crop.save(p)
        print(tag, name, crop.size, "->", p)


def main():
    src = fitz.open(PDF)
    render_crops(src, PAGE, "RAW", os.path.join(HERE, "bundle-A-raw"))
    rec = build_recolor_doc(src)
    render_crops(rec, 0, "RECOLOR", os.path.join(HERE, "bundle-B-recolor"))


if __name__ == "__main__":
    main()
