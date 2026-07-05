"""
plan_cluster.py — DETERMINISTIC furniture extraction from the vector plan.

Instead of eyeballing, rasterize the furniture-stroke layer, morphologically CLOSE
(bridge a piece's own internal gaps but NOT the gaps between separate pieces), and run
scipy connected-components. Each component = one drawn furniture piece with an EXACT
mm bounding box. Emits a candidate list + a numbered verification overlay so every piece
is accounted for (completeness) and correctly sized (positions) with zero hand-typing.

    python plan_cluster.py <pdf> <page> <x0 y0 x1 y1 mm> <close_mm> <out.json> <out.png> [mask.json]

The clustering core is exposed as extract_clusters() so the placement GATE
(placement_gate.py) can re-derive the SAME drawn bboxes it checks placements against —
the clusters stop being a picture nobody reads and become the ground truth of the gate.
"""
import json
import sys
import numpy as np
import scipy.ndimage as ndi
import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# Calibration for this project's sheet (26.45 mm/pt, verified <1% vs written dims).
# Duplicated in pdf_extract_walls.py / gen_floor2_specs.py / placement_gate.py — one
# source sheet, one triple. If the page/export changes, change it in one place per file.
SCALE, OX, OY = 26.45, 171.2, 596.5
RES = 6.0  # mm per pixel


def _mm_mapper(page, calib=None):
    """paper-point -> mm (page-rotation aware), matching the wall/overlay extractors.
    calib = (scale, ox, oy); defaults to this sheet's triple. Passing it per-project stops
    a second plan being silently read in the wrong coordinate frame."""
    scale, ox, oy = calib if calib else (SCALE, OX, OY)
    m = page.rotation_matrix

    def mm(P):
        Q = fitz.Point(P) * m
        return ((Q.x - ox) * scale, (oy - Q.y) * scale)

    return mm


def _bez(pts, n=8):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    return [((1-t)**3*x0+3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3*x3,
             (1-t)**3*y0+3*(1-t)**2*t*y1+3*(1-t)*t*t*y2+t**3*y3) for t in
            (i/n for i in range(n+1))]


def _rasterize(segs, zone, W, H):
    X0, Y0, X1, Y1 = zone
    fig = plt.figure(figsize=(W/100.0, H/100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.axis("off")
    if segs:
        ax.add_collection(LineCollection(segs, colors="black", linewidths=1.0))
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, 0]
    plt.close(fig)
    return buf < 128        # True where a stroke is (row 0 = top = max y)


def _zero_mask(arr, rects, zone, W, H):
    X0, Y0, X1, Y1 = zone
    for x0, y0, x1, y1 in rects:
        c0 = max(0, int((x0 - X0) / RES)); c1 = min(W, int((x1 - X0) / RES))
        r0 = max(0, int((Y1 - y1) / RES)); r1 = min(H, int((Y1 - y0) / RES))
        arr[r0:r1, c0:c1] = False
    return arr


def extract_clusters(pdf, page, zone, close_mm, masks=None, calib=None):
    """DETERMINISTIC furniture clusters for <zone> (x0,y0,x1,y1 in mm) on <page>.

    Returns a dict:
      items : [ {id,x,y,w,d,area_m2,curve,fill}, ... ]  (x,y = lower-left mm corner)
      fsegs : the furniture stroke segments (for the overlay)
      ink   : bool HxW raster of furniture ink (row0 = top = Y1) AFTER masking
      zone, res, W, H  (W,H = the ACTUAL raster shape, so consumers clamp correctly)
    Same math the CLI used, so plan_cluster.py's output and the gate agree by construction.
    calib = (scale,ox,oy) per project; defaults to this sheet's triple.
    """
    masks = masks or []
    X0, Y0, X1, Y1 = zone
    doc = fitz.open(pdf)
    p = doc[page]
    mm = _mm_mapper(p, calib)

    fsegs, csegs = [], []
    for d in p.get_drawings():
        w = d.get("width") or 0
        if w >= 0.6:
            continue                                   # walls excluded
        for it in d["items"]:
            if it[0] == "l":
                fsegs.append([mm(it[1]), mm(it[2])])
            elif it[0] == "re":
                r = it[1]
                cs = [mm((r.x0, r.y0)), mm((r.x1, r.y0)), mm((r.x1, r.y1)), mm((r.x0, r.y1)), mm((r.x0, r.y0))]
                fsegs += [[a, b] for a, b in zip(cs, cs[1:])]
            elif it[0] == "qu":
                q = it[1]
                cs = [mm(q.ul), mm(q.ur), mm(q.lr), mm(q.ll), mm(q.ul)]
                fsegs += [[a, b] for a, b in zip(cs, cs[1:])]
            elif it[0] == "c":
                poly = [mm(z) for z in _bez([(pt.x, pt.y) for pt in it[1:5]])]
                seg = [[a, b] for a, b in zip(poly, poly[1:])]
                fsegs += seg
                csegs += seg

    Wc = int((X1 - X0) / RES)
    Hc = int((Y1 - Y0) / RES)
    ink_raw = _rasterize(fsegs, zone, Wc, Hc)
    H, W = ink_raw.shape          # ACTUAL raster shape (Agg may differ by 1px from Wc/Hc)
    ink = _zero_mask(ink_raw, masks, zone, W, H)
    curveink = _zero_mask(_rasterize(csegs, zone, Wc, Hc), masks, zone, W, H)

    # CLOSE: bridge a piece's internal gaps (< close_mm) but keep separate pieces apart
    r = max(1, int(round(close_mm / RES)))
    st = ndi.generate_binary_structure(2, 2)
    closed = ndi.binary_closing(ink, structure=st, iterations=r)
    lab, n = ndi.label(closed, structure=st)

    def px2mm(col, row):
        return X0 + col * RES, Y1 - row * RES          # row0 = top = Y1

    comps = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        area_px = len(xs)
        if area_px < 25:
            continue
        x_lo, _ = px2mm(xs.min(), 0)
        x_hi, _ = px2mm(xs.max(), 0)
        _, y_hi = px2mm(0, ys.min())
        _, y_lo = px2mm(0, ys.max())
        wmm, dmm = x_hi - x_lo, y_hi - y_lo
        if wmm < 150 or dmm < 150:                     # noise / dim ticks
            continue
        if wmm > 3600 and dmm > 3600:                  # merged blob — skip (retune close)
            continue
        reg = (lab == i)
        curvy = int((reg & curveink).sum())
        fill = area_px / max((xs.max()-xs.min()+1)*(ys.max()-ys.min()+1), 1)
        comps.append({"id": i, "x": round(x_lo), "y": round(y_lo),
                      "w": round(wmm), "d": round(dmm), "area_m2": round(area_px*RES*RES/1e6, 2),
                      "curve": curvy > 30, "fill": round(fill, 2)})

    comps.sort(key=lambda c: (-c["w"]*c["d"]))
    return {"items": comps, "fsegs": fsegs, "ink": ink, "zone": zone,
            "res": RES, "W": W, "H": H}


def _main(argv):
    pdf, page = argv[1], int(argv[2])
    zone = tuple(float(argv[i]) for i in range(3, 7))
    close_mm = float(argv[7])
    outjson, outpng = argv[8], argv[9]
    masks = json.load(open(argv[10], encoding="utf-8")) if len(argv) > 10 else []

    res = extract_clusters(pdf, page, zone, close_mm, masks)
    comps, fsegs = res["items"], res["fsegs"]
    print(f"raster {res['W']}x{res['H']}px  close_r={max(1, int(round(close_mm/RES)))}px")
    json.dump({"zone": list(zone), "close_mm": close_mm, "n": len(comps), "items": comps},
              open(outjson, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"kept {len(comps)} furniture components")

    X0, Y0, X1, Y1 = zone
    fig, ax = plt.subplots(figsize=(20, 20*(Y1-Y0)/(X1-X0)), dpi=110)
    ax.add_collection(LineCollection(fsegs, colors="#b9c6da", linewidths=0.5))
    for k, c in enumerate(comps, 1):
        col = "#c02020" if c["curve"] else "#1560c0"
        ax.add_patch(plt.Rectangle((c["x"], c["y"]), c["w"], c["d"], fill=False, edgecolor=col, lw=1.8))
        ax.text(c["x"]+c["w"]/2, c["y"]+c["d"]/2, f'{k}\n{c["w"]}x{c["d"]}',
                ha="center", va="center", fontsize=7, color=col, weight="bold")
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3, alpha=0.3)
    ax.set_title(f"DETERMINISTIC furniture clusters ({len(comps)}) — red=organic(chair/fixture) "
                 f"blue=rectilinear(cabinet/table). size in mm.", fontsize=10)
    plt.tight_layout()
    plt.savefig(outpng, dpi=110)
    print("wrote", outpng)


if __name__ == "__main__":
    if len(sys.argv) < 10:
        raise SystemExit(__doc__)
    _main(sys.argv)
