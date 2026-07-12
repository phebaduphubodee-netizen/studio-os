"""
floor_openings.py -- doors/windows/glass as REAL build geometry (pure logic, no Blender).

WHY (owner, 2026-07-10): "ตรงที่เป็นประตู, หน้าต่าง ถ้าไม่ใส่เข้า model 3D เวลา render ออกมามันก็ว่าง" --
build_floor's vocabulary was walls-only, so every door/window either rendered as a raw
VOID (a hole in the house) or, worse, a patched glass facade rendered as a SOLID wall.
This module gives the floor manifest an `openings_json` channel and the two pure
computations build_floor needs:

  clip_wall_segments   subtract each opening's span from the wall segments that cross
                       its rect, so the wall is CUT where the opening lives (a window
                       never gets walled over, a door head can carry a lintel);
  opening_boxes        the solid boxes an opening contributes back: glass pane
                       (sill..head, translucent), sill wall (0..sill) and lintel
                       (head..ceiling) for windows; lintel only for doors; full-height
                       glass for facade `glass` type; bare `opening` contributes nothing
                       (a cased passage is honestly a gap).

HEIGHTS ARE RENDER DEFAULTS, NOT MEASUREMENTS: sill/head per opening come from the
json; absent values fall back to DEFAULTS below, which are visual-communication
defaults (disclosed in the json meta), never construction dimensions -- the sheet's
elevations were not read. The owner adjusts per opening.

openings json schema:
  {"meta": {...}, "openings": [{"id", "type": "window|glass|door|opening",
    "rect": [x0,y0,x1,y1] plan-mm, "sill_mm"?, "head_mm"?, "note"?, "provenance"?}]}

Blender-free by design (unit-tested); build_floor.py is the only consumer.
"""
DEFAULTS = {
    "window": {"sill_mm": 900.0, "head_mm": 2200.0},
    "door": {"sill_mm": 0.0, "head_mm": 2000.0},
    "glass": {"sill_mm": 0.0, "head_mm": None},      # None head = to ceiling
    "sliding": {"sill_mm": 0.0, "head_mm": 2400.0},  # 2-panel sliding glass DOOR --
    #   two offset panels on two tracks (owner 2026-07-10: "ประตูเลื่อน ไม่ใช่แผ่นกระจก" --
    #   a monolithic pane reads as a fixed wall of glass, not an operable door)
    "railing": {"sill_mm": 0.0, "head_mm": 1000.0},  # balcony parapet/railing band
    "opening": {"sill_mm": 0.0, "head_mm": None},
}
SLIDING_OVERLAP_MM = 150.0


def _seg_axis(seg, tol=1.0):
    (x1, y1), (x2, y2) = seg
    if abs(y2 - y1) <= tol and abs(x2 - x1) > tol:
        return "h"
    if abs(x2 - x1) <= tol and abs(y2 - y1) > tol:
        return "v"
    return None


def clip_wall_segments(segments, openings, band_tol=40.0):
    """Subtract opening spans from wall segments. A segment is cut by an opening iff
    the segment's offset lies inside the opening rect's cross-band (+band_tol) and the
    spans overlap; the overlapped span is removed (the wall may split in two). Diagonal
    segments pass through untouched (openings here are axis-aligned). Returns
    (kept_segments, n_cuts)."""
    out, n_cuts = [], 0
    rects = [(o["rect"], o) for o in openings]
    queue = [[list(a), list(b)] for a, b in segments]
    for seg in queue:
        ax = _seg_axis(seg)
        if ax is None:
            out.append(seg)
            continue
        (x1, y1), (x2, y2) = seg
        if ax == "h":
            off, lo, hi = (y1 + y2) / 2.0, min(x1, x2), max(x1, x2)
        else:
            off, lo, hi = (x1 + x2) / 2.0, min(y1, y2), max(y1, y2)
        pieces = [(lo, hi)]
        cut_here = False
        for (rx0, ry0, rx1, ry1), _o in rects:
            if ax == "h":
                if not (ry0 - band_tol <= off <= ry1 + band_tol):
                    continue
                c0, c1 = rx0, rx1
            else:
                if not (rx0 - band_tol <= off <= rx1 + band_tol):
                    continue
                c0, c1 = ry0, ry1
            nxt = []
            for a, b in pieces:
                if c1 <= a or c0 >= b:
                    nxt.append((a, b))
                    continue
                cut_here = True
                if c0 > a:
                    nxt.append((a, c0))
                if c1 < b:
                    nxt.append((c1, b))
            pieces = nxt
        if cut_here:
            n_cuts += 1
        for a, b in pieces:
            if b - a < 1.0:
                continue
            out.append([[a, off], [b, off]] if ax == "h" else [[off, a], [off, b]])
    return out, n_cuts


def opening_boxes(opening, ceiling_mm):
    """The solid boxes one opening contributes: list of
    {"kind": "glass"|"wall", "rect": [x0,y0,x1,y1], "z0_mm", "z1_mm"}.
    window: sill wall (0..sill) + glass (sill..head) + lintel (head..ceiling)
    glass:  glass pane (sill..head or ceiling)
    door:   lintel (head..ceiling)
    opening: nothing (an honest gap)."""
    t = opening.get("type", "opening")
    d = DEFAULTS.get(t, DEFAULTS["opening"])
    sill = float(opening.get("sill_mm", d["sill_mm"]) or 0.0)
    head = opening.get("head_mm", d["head_mm"])
    head = float(head) if head is not None else float(ceiling_mm)
    r = [float(v) for v in opening["rect"]]
    boxes = []
    if t == "window":
        if sill > 0:
            boxes.append({"kind": "wall", "rect": r, "z0_mm": 0.0, "z1_mm": sill})
        boxes.append({"kind": "glass", "rect": r, "z0_mm": sill, "z1_mm": head})
        if head < ceiling_mm:
            boxes.append({"kind": "wall", "rect": r, "z0_mm": head,
                          "z1_mm": float(ceiling_mm)})
    elif t == "glass":
        boxes.append({"kind": "glass", "rect": r, "z0_mm": sill, "z1_mm": head})
    elif t == "sliding":
        # two panels, each just over half the run, on the two halves of the rect's
        # thickness (= two tracks), overlapping mid-run -- reads as an operable door
        x0, y0, x1, y1 = r
        if (x1 - x0) >= (y1 - y0):          # run along x, tracks split the y thickness
            mid, ty = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            p1 = [x0, y0, mid + SLIDING_OVERLAP_MM, ty]
            p2 = [mid - SLIDING_OVERLAP_MM, ty, x1, y1]
        else:                                # run along y
            mid, tx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
            p1 = [x0, y0, tx, mid + SLIDING_OVERLAP_MM]
            p2 = [tx, mid - SLIDING_OVERLAP_MM, x1, y1]
        boxes.append({"kind": "glass", "rect": p1, "z0_mm": sill, "z1_mm": head})
        boxes.append({"kind": "glass", "rect": p2, "z0_mm": sill, "z1_mm": head})
    elif t == "railing":
        boxes.append({"kind": "wall", "rect": r, "z0_mm": sill, "z1_mm": head})
    elif t == "door":
        if head < ceiling_mm:
            boxes.append({"kind": "wall", "rect": r, "z0_mm": head,
                          "z1_mm": float(ceiling_mm)})
    return boxes
