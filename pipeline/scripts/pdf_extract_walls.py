"""
pdf_extract_walls.py — pull the WALL layer out of a vector floor-plan PDF as mm line
segments, ready to extrude in Blender (build_floor.py).

    python pdf_extract_walls.py <plan.pdf> <page> <out.json> [scale_mm_per_pt x0_pt y0_pt]

Why: the DXF export of this project is only reduced/mirrored key-plan copies (unusable for
coordinates); the dimensioned PDF sheet is the real drawing. Its walls are the THICK BLACK
strokes (width >= 0.6 pt) — furniture/fixtures/dimension lines are thinner (0.12/0.48) and
light-grey. We keep only the thick black, axis-aligned segments, drop the sheet border /
title block, and map paper points -> real mm.

CALIBRATION (this project, page 1 "PLAN FURNITURE FLOOR 2", 1:75 on A3):
  scale = 26.45 mm/pt   (verified against the written dims 5500/5100/2850/2950/700 — all <1%)
  origin x0_pt = 171.2  -> x_mm 0 at the master WEST exterior wall
  origin y0_pt = 596.5  -> y_mm 0 at the master SOUTH glazing (y up = north)
So the output frame matches the room-spec@0.2 files (master SW interior ~ (0,0)).
"""
import json
import sys

import fitz


def extract(pdf, page, scale, x0, y0):
    doc = fitz.open(pdf)
    p = doc[page]
    m = p.rotation_matrix

    def seglist(it):
        if it[0] == "l":
            return [(it[1], it[2])]
        if it[0] == "re":
            r = it[1]
            return [((r.x0, r.y0), (r.x1, r.y0)), ((r.x1, r.y0), (r.x1, r.y1)),
                    ((r.x1, r.y1), (r.x0, r.y1)), ((r.x0, r.y1), (r.x0, r.y0))]
        if it[0] == "qu":
            q = it[1]
            return [(q.ul, q.ur), (q.ur, q.lr), (q.lr, q.ll), (q.ll, q.ul)]
        return []

    def mm(P):
        Q = fitz.Point(P) * m
        return ((Q.x - x0) * scale, (y0 - Q.y) * scale)

    walls = []
    for d in p.get_drawings():
        col = d.get("color")
        w = d.get("width") or 0
        if col is None or sum(col) > 0.3 or w < 0.6:      # thick BLACK strokes only
            continue
        for it in d["items"]:
            for a, b in seglist(it):
                (x1, y1) = mm(a)
                (x2, y2) = mm(b)
                if not (-1000 <= x1 <= 21200 and -1000 <= x2 <= 21200 and
                        -1600 <= y1 <= 13300 and -1600 <= y2 <= 13300):
                    continue                              # drop sheet border / title block
                dx, dy = x2 - x1, y2 - y1
                L = (dx * dx + dy * dy) ** 0.5
                if L < 40 or L > 21000:
                    continue
                if min(abs(dx), abs(dy)) > 8:             # keep axis-aligned (drops dim ticks)
                    continue
                walls.append([[round(x1, 1), round(y1, 1)], [round(x2, 1), round(y2, 1)]])
    return walls


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    pdf, page, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 26.45
    x0 = float(sys.argv[5]) if len(sys.argv) > 5 else 171.2
    y0 = float(sys.argv[6]) if len(sys.argv) > 6 else 596.5
    walls = extract(pdf, page, scale, x0, y0)
    meta = {"schema": "interior-ai/wall-segments-mm@0.1", "source_pdf": pdf.split("/")[-1],
            "page": page, "scale_mm_per_pt": scale, "origin_pt": [x0, y0],
            "frame": "mm; x east from master west wall, y north from master south glazing",
            "n": len(walls), "segments": walls}
    json.dump(meta, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    xs = [c for s in walls for c in (s[0][0], s[1][0])]
    ys = [c for s in walls for c in (s[0][1], s[1][1])]
    print(f"wrote {out}: {len(walls)} wall segments  bbox mm "
          f"X[{min(xs):.0f}..{max(xs):.0f}] Y[{min(ys):.0f}..{max(ys):.0f}]")


if __name__ == "__main__":
    main()
