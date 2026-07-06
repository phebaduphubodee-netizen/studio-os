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
import os
import sys

# The owner hand-patches walls the thick-stroke extractor is BLIND to — the thin-line/glass features
# (e.g. the sliding-glass facade, drawn at <0.6 pt) that are the room's TRUE indoor/outdoor boundary.
# These live in the file in TWO places: the `manual_additions` RECORD (date/by/reason/segments) AND
# their coordinates spliced into the top-level `segments` array — the array build_floor.py EXTRUDES.
# A fresh extract omits both (the strokes are below is_wall_stroke's 0.6 pt gate), so a naive re-write
# SILENTLY EATS a real structural wall from the built geometry. merge_carried restores BOTH.
_CALIB_KEYS = ("scale_mm_per_pt", "origin_pt", "source_pdf", "page")


def _valid_seg(s):
    try:
        return len(s) == 2 and len(s[0]) == 2 and len(s[1]) == 2
    except (TypeError, IndexError):
        return False


def _seg_key(s):
    """Undirected key for dedup: a wall A->B is the same segment as B->A."""
    return tuple(sorted((tuple(s[0]), tuple(s[1]))))


def _calib_val(meta, k):
    v = meta.get(k) if isinstance(meta, dict) else None
    if k == "source_pdf" and isinstance(v, str):
        return v.replace("\\", "/").split("/")[-1]      # compare basenames (path-separator agnostic)
    return v


def merge_carried(new_meta, prior_meta):
    """Carry the owner's non-regenerable wall patches from a PRIOR output onto a freshly extracted meta
    so a re-extract never silently drops them. Restores the `manual_additions` RECORD verbatim AND
    re-injects its segments into the top-level `segments` array (undirected dedup, bump `n`) — because
    build_floor extrudes `segments`, so carrying only the record (the first, ineffective fix) still
    ate the wall from the built geometry.

    Refuses to re-inject on CALIBRATION DRIFT: the patched coordinates are absolute mm in the prior
    frame, so if scale/origin/source/page changed they would place walls at the wrong spot — warn and
    keep the record (for re-patching) instead of injecting stale coords. Returns (new_meta, notes): a
    list of human-readable lines (carried / re-injected / WARNING). Pure -> unit-testable without fitz."""
    notes = []
    if not isinstance(prior_meta, dict):
        return new_meta, notes
    ma = prior_meta.get("manual_additions")
    if not isinstance(ma, dict):
        return new_meta, notes
    new_meta["manual_additions"] = ma                       # the provenance record is always worth keeping
    drift = [k for k in _CALIB_KEYS if _calib_val(prior_meta, k) != _calib_val(new_meta, k)]
    if drift:
        notes.append(f"WARNING: kept the manual_additions record but did NOT re-inject its walls into "
                     f"segments — calibration/source changed ({', '.join(drift)}), so its mm coordinates "
                     f"are stale. Re-patch the walls against this extract, then update manual_additions.")
        return new_meta, notes
    notes.append("carried the manual_additions record")
    segs = ma.get("segments")
    if isinstance(segs, list) and segs:
        have = {_seg_key(s) for s in new_meta.get("segments", []) if _valid_seg(s)}
        added = [s for s in segs if _valid_seg(s) and _seg_key(s) not in have]
        if added:
            new_meta["segments"] = list(new_meta.get("segments", [])) + added
            new_meta["n"] = len(new_meta["segments"])
            notes.append(f"re-injected {len(added)} owner-patched wall segment(s) into segments "
                         f"(n={new_meta['n']}) so build_floor extrudes them")
    return new_meta, notes


# ---- pure geometry / filters (NO fitz -> unit-testable; the calibration + screens were
#      previously validated only empirically at build/gate time against the real PDF) --------
def map_pt(px, py, scale, x0, y0):
    """Paper point (page rotation already applied) -> real mm in the room-spec@0.2 frame:
    x EAST from the origin, y NORTH (paper y is down, so it flips). The (scale,x0,y0) triple is
    the one load-bearing constant, verified <1% vs the written dims (5500/5100/2850/2950/700)."""
    return ((px - x0) * scale, (y0 - py) * scale)


def is_wall_stroke(color, width, max_color_sum=0.3, min_width=0.6):
    """True only for a THICK BLACK stroke (a wall). Furniture/fixtures/dimension lines are
    thinner (0.12/0.48 pt) and light-grey (high sum(rgb)); a None colour (no stroke) is not a
    wall. Mirrors the original inline `col is None or sum(col) > 0.3 or w < 0.6` skip, inverted."""
    if color is None:
        return False
    return sum(color) <= max_color_sum and (width or 0) >= min_width


def keep_segment(x1, y1, x2, y2, x_range=(-1000, 21200), y_range=(-1600, 13300),
                 min_len=40.0, max_len=21000.0, max_off_axis=8.0):
    """True for a segment INSIDE the drawing frame (drops the sheet border/title block), of
    real length (drops specks + the full-page diagonal), and axis-aligned (drops slanted
    dimension ticks/leaders). Mirrors the original inline screens exactly."""
    if not (x_range[0] <= x1 <= x_range[1] and x_range[0] <= x2 <= x_range[1] and
            y_range[0] <= y1 <= y_range[1] and y_range[0] <= y2 <= y_range[1]):
        return False
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** 0.5
    if L < min_len or L > max_len:
        return False
    return min(abs(dx), abs(dy)) <= max_off_axis


def extract(pdf, page, scale, x0, y0):
    import fitz    # lazy: the pure helpers above stay importable/testable without PyMuPDF
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

    def to_mm(P):
        Q = fitz.Point(P) * m
        return map_pt(Q.x, Q.y, scale, x0, y0)

    walls = []
    for d in p.get_drawings():
        if not is_wall_stroke(d.get("color"), d.get("width") or 0):   # thick BLACK strokes only
            continue
        for it in d["items"]:
            for a, b in seglist(it):
                (x1, y1) = to_mm(a)
                (x2, y2) = to_mm(b)
                if not keep_segment(x1, y1, x2, y2):      # frame / length / axis-aligned screens
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
    # Preserve owner-authored, non-regenerable walls (manual_additions = hand-patched thin-line/glass
    # walls, in the record AND spliced into segments) from any prior output at this path — a re-extract
    # must never silently drop a real wall from the built geometry.
    prior = None
    if os.path.exists(out):
        try:
            prior = json.load(open(out, encoding="utf-8"))
        except (ValueError, OSError):
            prior = None
    meta, notes = merge_carried(meta, prior)
    tmp = out + ".tmp"                                       # atomic write: the file is now the sole
    json.dump(meta, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)   # on-disk home of the patches
    os.replace(tmp, out)
    xs = [c for s in meta["segments"] for c in (s[0][0], s[1][0])]
    ys = [c for s in meta["segments"] for c in (s[0][1], s[1][1])]
    print(f"wrote {out}: {meta['n']} wall segments  bbox mm "
          f"X[{min(xs):.0f}..{max(xs):.0f}] Y[{min(ys):.0f}..{max(ys):.0f}]")
    for note in notes:
        print(f"  {note}")


if __name__ == "__main__":
    main()
