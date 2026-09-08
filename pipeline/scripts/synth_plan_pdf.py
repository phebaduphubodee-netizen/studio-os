"""
synth_plan_pdf.py -- build tiny synthetic Bluehouse-convention PDFs, so the PAGE-TYPE GATE and
the FAIL-CLOSED SCALE can be tested on cases the client sheet does not contain.

The client PDF has no scale DISAGREEMENT on it: its two plan pages both say 1:50 and both measure
1:50. Round 1's bug (infer the scale from an assumed 100 mm wall; a 200 mm wall at 1:50 snaps to
"1:25" and the building is emitted at HALF SIZE) therefore cannot be demonstrated on the real
sheet at all -- which is exactly how it survived. So we synthesise it.

    python synth_plan_pdf.py OUTDIR      # writes good.pdf, halfscale.pdf, noscale.pdf

  good.pdf       a valid 1:50 plan: 100 mm walls, an 8 x 6 m envelope. The GATE MUST ACCEPT IT.
                 (Without this control, "the gate refuses everything" would also pass.)
  halfscale.pdf  identical, but the walls are drawn 200 mm thick while the title block still says
                 1:50. Geometry snaps to 1:25. The reader MUST REFUSE, not pick a winner.
  noscale.pdf    a valid plan with the SCALE field deleted. MUST REFUSE (no stated scale).

These are SYNTHETIC. No client geometry, no client text. Safe to commit.
"""
import os
import sys

PT_MM = 25.4 / 72.0


def _sheet(doc, wall_mm, denom, title="FLOOR PLAN", scale_field=True, shrink=1.0):
    """`shrink` = the A3->A4 photographic reduction (1/sqrt(2)) the office's exporter applies to the
    WHOLE page, title block included, while the title block goes on printing the A3 scale. The reader
    reads it back off the BORDER, so the border must be the office's real one -- see SHEET_BORDER_PT.
    An arbitrary border (this was fitz.Rect(20,20,1171,822) = 1151x802 pt) is not a stand-in for the
    office's sheet, it is a different sheet, and a synthetic fixture that lies about the paper cannot
    defend the code that reads the paper."""
    page = doc.new_page(width=1191 * shrink, height=842 * shrink)   # A3 landscape (or its A4 export)
    import fitz
    sc = PT_MM * denom                                   # mm per pt at DESIGN size (what the TB says)
    t = wall_mm / sc * shrink                            # the wall's PLOTTED thickness, in PAGE points

    shp = page.new_shape()                               # the 1.44-pt sheet border == SHEET_BORDER_PT
    shp.draw_rect(fitz.Rect(34.275 * shrink, 34.075 * shrink,
                            1156.725 * shrink, 807.925 * shrink))   # 1122.45 x 773.85 pt at shrink=1
    shp.finish(color=(0, 0, 0), width=1.44, fill=None)
    shp.commit()

    # An 8000 x 6000 mm envelope, each side broken into 4 abutting quads (as the exporter does).
    # In PAGE points: the reduction is photographic, so the ink shrinks with the paper.
    W, H = 8000.0 / sc * shrink, 6000.0 / sc * shrink
    ox, oy = 200.0 * shrink, 200.0 * shrink
    bands = []
    for k in range(4):
        bands.append((ox + k * W / 4, oy, ox + (k + 1) * W / 4, oy + t))            # south
        bands.append((ox + k * W / 4, oy + H - t, ox + (k + 1) * W / 4, oy + H))    # north
        bands.append((ox, oy + k * H / 4, ox + t, oy + (k + 1) * H / 4))            # west
        bands.append((ox + W - t, oy + k * H / 4, ox + W, oy + (k + 1) * H / 4))    # east
    for (x0, y0, x1, y1) in bands:
        s = page.new_shape()
        s.draw_quad(fitz.Quad((x0, y0), (x1, y0), (x0, y1), (x1, y1)))   # 'qu', the exporter's op
        s.finish(color=(0, 0, 0), width=0.84, fill=None)                 # stroke-only, wall pen
        s.commit()

    # The title block, in the same LABEL-above-VALUE layout the real sheets use. NOTE it prints the
    # DESIGN scale (`denom`) even when the page is an A4 export -- that is the whole bug being
    # modelled: the exporter shrinks the paper and the title block does not notice.
    page.insert_text((1028.5 * shrink, 612 * shrink), "DRAWING TITLE : ", fontsize=6 * shrink)
    page.insert_text((1028.5 * shrink, 627 * shrink), title, fontsize=6 * shrink)
    if scale_field:
        page.insert_text((1028.5 * shrink, 640 * shrink), "SCALE :", fontsize=6 * shrink)
        page.insert_text((1028.5 * shrink, 650 * shrink), f"1 : {denom}  ", fontsize=6 * shrink)
    return page


def write_all(outdir):
    import fitz
    os.makedirs(outdir, exist_ok=True)
    paths = {}
    import math
    for name, kw in (("good", dict(wall_mm=100.0, denom=50)),
                     ("halfscale", dict(wall_mm=200.0, denom=50)),
                     ("noscale", dict(wall_mm=100.0, denom=50, scale_field=False)),
                     # A3 art exported to A4: same building, same title block, 0.7071x the paper.
                     ("a4export", dict(wall_mm=100.0, denom=50, shrink=1 / math.sqrt(2)))):
        doc = fitz.open()
        _sheet(doc, **kw)
        p = os.path.join(outdir, name + ".pdf")
        doc.save(p)
        doc.close()
        paths[name] = p
    return paths


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for k, v in write_all(out).items():
        print(f"{k:10s} {v}")
