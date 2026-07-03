"""
suite_clearance.py — INTERIOR-AI v0.4.2 clearance engine: METRIC + POLYGON + Thai code
                     + Gate 0 geometry (blueprint §9.2, M3.1).

v0.2 embedded its own DR-derived Thai rules; v0.3 (M3.1 unification slice, 2026-07-02)
loads the statutory floors from dimensional_rules.v0.2.json `thai_code_minimums` —
ONE cited rule source for every engine (three miscitations fixed at that point).
v0.3.1 (scrutiny fixes, qa/reports/2026-07-02-scrutiny-019a67f.md): ข้อ 22 checked on
its own basis (clear height can prove compliance a fortiori, never a breach); ข้อ 20
net-area + narrow side enforced with honest tiers; boundary-inclusive in-bounds.
v0.4 (Gate 0 full, 2026-07-02): exact maximal-clear-rectangle leg decomposition for
the ข้อ 20 / ข้อ 21 width trichotomies; circulation bottleneck via L∞ envelope
erosion + BFS; exact quarter-disc door-swing arcs; in-bounds vs the NET room;
ฉ.39 wet-room floors. Ergonomic walkway floors (Panero, dimensional_rules
circulation): < 610 pinch -> FAIL (buildability, not statute); < 910 -> WARN.
v0.4.1 (adversarial scrutiny of v0.4, qa/reports/2026-07-02-gate0-full.md):
  * AS-BUILT WALLS: build_room.py extrudes every wall OUTWARD by wall_thk_mm, so a
    sub-room's wall band eats into the parent room. Statutory PASS proofs (ข้อ 20/21
    legs, net area, in-bounds, circulation, swings) now carve the keep-out =
    footprint + wall band; FAIL proofs use the raw outline (charitable basis) —
    neither statutory direction over-claims. Doorways gap the band for movement.
  * ฉ.39 tiers: combined (1.5 m²) vs separated (0.9 m² + 900 mm width) resolved from
    fixtures/names; unknown -> dual-tier honesty (FAIL only below both floors).
  * Wet-typed MAIN rooms get the ฉ.39 checks + 2000 clear-height basis (ข้อ 22 wet
    row is พื้นถึงเพดาน); ข้อ 22 ระเบียง tier 2200; สำนักงาน/ห้องอาหาร 3000 tier
    surfaces as WARN only (in-unit interpretation unresolved).
  * ข้อ 20 net area computed exactly on the cell grid (sub-rooms outside the outline
    or overlapping each other no longer produce a false statutory FAIL).
  * ข้อ 21 for อาคารอยู่อาศัยรวม: the vault ties 1500 to COMMON corridors; in-unit
    condo corridors are a recorded vault gap -> < 1500 is WARN naming that question,
    never "breach under every reading". Unknown building type never FAILs.
  * Circulation: envelope starts sampled across the whole doorway (an entry console
    off-centre no longer zeroes the bottleneck); target reach requires line-of-sight
    (no more "reached" through a thin wall); a bed on a platform ledge is reachable
    by stepping on the platform (target = bed ∪ its platform). The doorway leaf
    width itself is deliberately NOT an envelope cap — doors are permitted pinch
    points with their own 800 mm studio floor.
  * Door swings: leaf arcs that cross the room boundary (door too close to a
    perpendicular wall) -> WARN (cannot open 90°); furniture/sub-room walls -> FAIL.
  * rot honored for 90/270 (w/d swap about the footprint centre, matching
    build_room); non-axis rotations are disclosed per item, checked as unrotated.
v0.4.2 (pure-geometry scrutiny lens, third run — the first two died on infra):
  * LOS reach is now EXACT (Liang-Barsky segment-vs-rect) — 25 mm point sampling
    stepped over blockers thinner than the step and PASSed a bed sealed behind a
    10 mm glass partition (false-PASS, the class the LOS fix existed to kill);
  * doorway envelope starts add the exact midpoint of every clear interval of
    the start line — the 50 mm stride alone quantized the entry aperture and
    under-reported bottlenecks by up to ~50 mm (false-WARN/false-FAIL flips);
  * slide-fit tolerance (_KISS = 0.25 mm): a gap exactly equal to an ergonomic
    floor now measures AT the floor (610 reads 610, not 609);
  * known limit documented in _keepout_cells (reentrant-corner door strip).
Swing convention: door (x, y) = leaf-segment start measured along +x on south/north
walls, +y on east/west; "-left" hinges at the segment start (lower coordinate),
"-right" at the far end; "in-" opens to the wall-owner's inside, "out-" outside.
Engine stays engine-agnostic IP: pure Python, PASS / WARN / FAIL, no CAD/3D needed.
Recorded, still NOT here: turning circles + knee/toe (need catalog seat/desk
metadata), clearance_check.py unification (still IRC/inch).

    python pipeline/scripts/suite_clearance.py [spec.json]
"""
import json
import os
import re
import sys
from bisect import bisect_right
from collections import deque

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_RULES_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "dimensional_rules.v0.2.json")


def _load_rules():
    """Statutory floors from the ONE cited source (dimensional_rules v0.2,
    thai_code_minimums) + ergonomic walkway floors from its circulation section.
    Values in mm; each statutory value carries its legal cite. Door minimums are
    a STUDIO floor (no general statutory interior-door min — ฉ.55 ข้อ 31 is fire
    doors), kept at the v0.2 thresholds for gate stability."""
    with open(_RULES_JSON, encoding="utf-8") as fh:
        doc = json.load(fh)
    tcm = doc["thai_code_minimums"]
    circ = doc["circulation"]

    def v(key):
        return tcm[key]["value"]

    def cite(key):
        return tcm[key]["cite"].split(" — ")[0]

    return {
        "ceiling_min_habitable": v("floor_to_floor_habitable_min_mm"),
        "ceiling_min_habitable_cite": cite("floor_to_floor_habitable_min_mm") + " (ระยะดิ่ง พื้นถึงพื้น)",
        "ceiling_min_balcony": v("balcony_floor_to_floor_min_mm"),
        "ceiling_min_balcony_cite": cite("balcony_floor_to_floor_min_mm") + " (ระเบียง)",
        "ceiling_office_dining": v("office_dining_floor_to_floor_min_mm"),
        "ceiling_office_dining_cite": cite("office_dining_floor_to_floor_min_mm") + " (สำนักงาน/ห้องเรียน/ห้องอาหาร)",
        "ceiling_min_bath": v("bathroom_floor_to_ceiling_min_mm"),
        "ceiling_min_bath_cite": cite("bathroom_floor_to_ceiling_min_mm"),
        "bath_comb_min_m2": v("bathroom_combined_area_min_m2"),
        "bath_sep_min_m2": v("bathroom_separated_area_min_m2"),
        "bath_sep_min_w": v("bathroom_separated_width_min_mm"),
        "bath_cite": cite("bathroom_combined_area_min_m2"),
        "bedroom_area_min_mm2": v("bedroom_area_min_m2") * 1e6,
        "bedroom_area_cite": cite("bedroom_area_min_m2"),
        "bedroom_width_min": v("bedroom_narrow_side_min_mm"),
        "bedroom_width_cite": cite("bedroom_narrow_side_min_mm"),
        "corridor_min": v("corridor_in_house_min_mm"),
        "corridor_cite": cite("corridor_in_house_min_mm") + " (บ้านเดี่ยว/ทาวน์เฮาส์ ภายในหน่วย)",
        "corridor_shared_min": v("corridor_collective_min_mm"),
        "corridor_shared_cite": cite("corridor_collective_min_mm") + " (อาคารอยู่อาศัยรวม — vault ties this to COMMON corridors)",
        "door_w_min": 800,
        "door_h_min": 1900,
        "door_cite": "studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors)",
        # ergonomic walkway floors (Panero via dimensional_rules circulation — ไม่ใช่กฎหมาย)
        "walkway_main": circ["main_walkway_min"]["cm"] * 10.0,        # 910
        "walkway_pinch": circ["minimum_passage_pinch"]["cm"] * 10.0,  # 610
    }


RULES_TH = _load_rules()
_WET = ("bath", "ensuite", "toilet", "wc", "shower", "powder",
        "ห้องน้ำ", "ส้วม", "อาบน้ำ")
_REACH = 300.0        # mm — arm's-reach tolerance from envelope edge to a target
_ENVELOPE_MAX = 2400  # mm — circulation bottleneck search ceiling (reported as >=)
_KISS = 0.25          # mm — slide-fit tolerance: an envelope exactly equal to a
                      # gap counts as passing (gap == 610 reads 610, not 609)


def _shoelace(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _point_in_poly(x, y, poly):
    """Ray-casting point-in-polygon (poly = list of (x,y), any winding)."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _on_edge(x, y, poly, eps=0.5):
    """Point lies ON a polygon edge (within eps mm). Ray-casting counts max-x/max-y
    boundaries as outside; flush-to-wall furniture is legal, so boundary = inside."""
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        seg2 = dx * dx + dy * dy
        if seg2 == 0:
            continue
        t = ((x - x1) * dx + (y - y1) * dy) / seg2
        if t < -1e-9 or t > 1 + 1e-9:
            continue
        px, py = x1 + t * dx, y1 + t * dy
        if (x - px) ** 2 + (y - py) ** 2 <= eps * eps:
            return True
    return False


def _inside_or_on(x, y, poly):
    return _point_in_poly(x, y, poly) or _on_edge(x, y, poly)


def _bbox(it):
    """Axis-aligned as-built footprint. rot 90/270 swaps w/d about the footprint
    centre (matching build_room's rotation about the centre); rot 0/180 unchanged;
    other angles fall back to the unrotated rect (disclosed by the caller)."""
    x, y, w, d = float(it["x"]), float(it["y"]), float(it["w"]), float(it["d"])
    rot = float(it.get("rot", 0) or 0) % 180.0
    if abs(rot - 90.0) < 1e-6:
        cx, cy = x + w / 2.0, y + d / 2.0
        return (cx - d / 2.0, cy - w / 2.0, cx + d / 2.0, cy + w / 2.0)
    return (x, y, x + w, y + d)


def _corners(it):
    x0, y0, x1, y1 = _bbox(it)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _bbox(a); bx0, by0, bx1, by1 = _bbox(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def _rects_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _rect_inflate(r, t):
    return (r[0] - t, r[1] - t, r[2] + t, r[3] + t)


def _rect_subtract(a, b):
    """a minus b -> up to 4 rects (empty pieces dropped)."""
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    if ix0 >= ix1 or iy0 >= iy1:
        return [a]
    out = []
    if a[1] < iy0:
        out.append((a[0], a[1], a[2], iy0))
    if iy1 < a[3]:
        out.append((a[0], iy1, a[2], a[3]))
    if a[0] < ix0:
        out.append((a[0], iy0, ix0, iy1))
    if ix1 < a[2]:
        out.append((ix1, iy0, a[2], iy1))
    return out


def _strictly_in_rect(px, py, r, eps=0.5):
    return r[0] + eps < px < r[2] - eps and r[1] + eps < py < r[3] - eps


# ---------------------------------------------------------------------------
# rectilinear geometry core (Gate 0 full, v0.4)
# ---------------------------------------------------------------------------

def _is_rectilinear(poly):
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
            return False
    return True


def _cell_grid(outline, holes=(), solids=(), extra_xs=(), extra_ys=()):
    """Coordinate-compressed cell decomposition of a rectilinear region.
    free[i][j] <=> cell centre inside `outline`, outside every `holes` polygon and
    not strictly inside any `solids` rect. Exact when all vertices/edges are on
    the grid (cell centres never touch an edge)."""
    xs = sorted({round(float(p[0]), 3) for p in outline}
                | {round(float(p[0]), 3) for h in holes for p in h}
                | {round(float(v), 3) for r in solids for v in (r[0], r[2])}
                | {round(float(v), 3) for v in extra_xs})
    ys = sorted({round(float(p[1]), 3) for p in outline}
                | {round(float(p[1]), 3) for h in holes for p in h}
                | {round(float(v), 3) for r in solids for v in (r[1], r[3])}
                | {round(float(v), 3) for v in extra_ys})
    free = []
    for i in range(len(xs) - 1):
        cx = (xs[i] + xs[i + 1]) / 2.0
        col = []
        for j in range(len(ys) - 1):
            cy = (ys[j] + ys[j + 1]) / 2.0
            ok = (_point_in_poly(cx, cy, outline)
                  and not any(_point_in_poly(cx, cy, h) for h in holes)
                  and not any(r[0] < cx < r[2] and r[1] < cy < r[3] for r in solids))
            col.append(ok)
        free.append(col)
    return xs, ys, free


def _free_area(xs, ys, free):
    return sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j])
               for i in range(len(xs) - 1) for j in range(len(ys) - 1) if free[i][j])


def _maximal_rects(xs, ys, free):
    """ALL maximal axis-aligned clear rectangles of the cell region (a rect is
    maximal when no one-strip extension in any direction stays clear)."""
    nx, ny = len(xs) - 1, len(ys) - 1
    P = [[0] * (ny + 1) for _ in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            P[i + 1][j + 1] = P[i][j + 1] + P[i + 1][j] - P[i][j] + (1 if free[i][j] else 0)

    def allfree(i0, i1, j0, j1):
        return (P[i1][j1] - P[i0][j1] - P[i1][j0] + P[i0][j0]) == (i1 - i0) * (j1 - j0)

    out = []
    for i0 in range(nx):
        for i1 in range(i0 + 1, nx + 1):
            for j0 in range(ny):
                for j1 in range(j0 + 1, ny + 1):
                    if not allfree(i0, i1, j0, j1):
                        continue
                    if i0 > 0 and allfree(i0 - 1, i0, j0, j1):
                        continue
                    if i1 < nx and allfree(i1, i1 + 1, j0, j1):
                        continue
                    if j0 > 0 and allfree(i0, i1, j0 - 1, j0):
                        continue
                    if j1 < ny and allfree(i0, i1, j1, j1 + 1):
                        continue
                    out.append((xs[i0], ys[j0], xs[i1], ys[j1]))
    return out


def _subroom_cells(sr):
    """A sub-room footprint (raw interior outline) as a list of cell rects."""
    poly = [tuple(p) for p in sr["outline_mm"]]
    if not _is_rectilinear(poly):
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        return [(min(xs), min(ys), max(xs), max(ys))]   # conservative bbox
    xs, ys, free = _cell_grid(poly)
    return [(xs[i], ys[j], xs[i + 1], ys[j + 1])
            for i in range(len(xs) - 1) for j in range(len(ys) - 1) if free[i][j]]


def _keepout_cells(sr, thk, door_gap):
    """AS-BUILT solid of a sub-room: interior footprint + wall band (build_room
    extrudes walls OUTWARD by thk — Minkowski of the cell union with a thk square,
    exact for rectilinear footprints). door_gap=True cuts the doorway strip out of
    the band so movement/swing checks can pass through the actual opening."""
    cells = [_rect_inflate(c, thk) for c in _subroom_cells(sr)]
    if door_gap:
        # KNOWN LIMIT (geometry lens #5, unweaponized): a door starting exactly at
        # a reentrant corner of an L-shaped sub-room lets the strip carve <= thk
        # of the PERPENDICULAR leg's wall band — a dead-end alcove; no verdict
        # flip constructible (swing still hits the remaining band). Attributing
        # band cells to their source wall would fix it; not worth the machinery.
        sd = sr.get("door")
        seg = _door_segment(sd) if sd else None
        if seg:
            if abs(seg[1] - seg[3]) < 1e-9:   # leaf along x -> gap crosses in y
                strip = (seg[0], seg[1] - thk - 2.0, seg[2], seg[3] + thk + 2.0)
            else:
                strip = (seg[0] - thk - 2.0, seg[1], seg[2] + thk + 2.0, seg[3])
            cells = [p for c in cells for p in _rect_subtract(c, strip)]
    return cells


def _room_thk(r, sr=None):
    base = float(r.get("wall_thk_mm") or 100.0)
    if sr is not None and sr.get("wall_thk_mm"):
        return float(sr["wall_thk_mm"])
    return base


def _leg_widths(outline, holes=(), solids=(), bed_rect=None):
    """(min_leg, best_leg, bed_leg) of the free region, or None if not computable."""
    ex = (bed_rect[0], bed_rect[2]) if bed_rect else ()
    ey = (bed_rect[1], bed_rect[3]) if bed_rect else ()
    xs, ys, free = _cell_grid(outline, holes, solids, ex, ey)
    rects = _maximal_rects(xs, ys, free)
    if not rects:
        return None

    def narrow(r):
        return min(r[2] - r[0], r[3] - r[1])

    legs = sorted(narrow(r) for r in rects)
    bed_leg = None
    if bed_rect is not None:
        inside = [narrow(r) for r in rects
                  if r[0] <= bed_rect[0] + 0.5 and r[1] <= bed_rect[1] + 0.5
                  and r[2] >= bed_rect[2] - 0.5 and r[3] >= bed_rect[3] - 0.5]
        bed_leg = max(inside) if inside else None
    return {"min_leg": legs[0], "best_leg": legs[-1], "bed_leg": bed_leg}


def _leg_analysis(outline, subrooms, room, bed_rect=None):
    """Two-basis leg decomposition of the net room. 'outer' carves the AS-BUILT
    keep-out (footprint + wall band — build_room extrudes outward): statutory PASS
    proofs use it. 'inner' carves only the raw outlines (most charitable basis):
    statutory FAIL proofs use it. Furniture is ignored — ข้อ 20/21 bind the room
    geometry, not the layout. None when the geometry is not rectilinear."""
    holes = [[tuple(p) for p in sr["outline_mm"]] for sr in subrooms]
    if not _is_rectilinear(outline) or any(not _is_rectilinear(h) for h in holes):
        return None
    keep = [c for sr in subrooms
            for c in _keepout_cells(sr, _room_thk(room, sr), door_gap=False)]
    outer = _leg_widths(outline, (), keep, bed_rect)
    inner = _leg_widths(outline, holes, (), bed_rect)
    if outer is None or inner is None:
        return None
    return {"outer": outer, "inner": inner}


# ---------------------------------------------------------------------------
# circulation (envelope erosion + BFS) and door swings
# ---------------------------------------------------------------------------

# door-leaf axis + inward normal, keyed by the wall of the OWNER of the door
# (room walls for the entry door; the sub-room's own walls for sub-room doors)
_WALL_AXIS = {"south": ("x", +1), "north": ("x", -1),
              "west": ("y", +1), "east": ("y", -1)}


def _door_segment(door):
    """Leaf segment as a degenerate rect. Convention: (x, y) = segment start,
    leaf runs along +x on south/north walls, +y on east/west walls."""
    x, y, w = float(door["x"]), float(door["y"]), float(door["w"])
    wall = str(door.get("wall", "")).lower()
    if wall not in _WALL_AXIS:
        return None
    axis, _ = _WALL_AXIS[wall]
    return (x, y, x + w, y) if axis == "x" else (x, y, x, y + w)


def _door_starts(door):
    """Envelope start candidates across the WHOLE doorway (an obstacle in front
    of part of the opening must not zero the bottleneck — the person enters
    through the clear part). Returns fn(W, solids) -> points just inside: a
    50 mm stride PLUS the exact midpoint of every clear interval of the start
    line between the W/2-inflated solids — stride-only quantized the aperture
    and under-reported bottlenecks by up to ~50 mm (geometry-lens finding #3)."""
    x, y, w = float(door["x"]), float(door["y"]), float(door["w"])
    wall = str(door.get("wall", "")).lower()
    axis, inw = _WALL_AXIS[wall]

    def fn(W, solids=()):
        h = W / 2.0
        d = h + 2.0
        lo, hi = (x, x + w) if axis == "x" else (y, y + w)
        line = (y + inw * d) if axis == "x" else (x + inw * d)
        ts = {w / 2.0}
        t = 25.0
        while t < w:
            ts.add(t)
            t += 50.0
        blocked = []
        for s in solids:
            i0 = (s[0] - h + _KISS, s[1] - h + _KISS, s[2] + h - _KISS, s[3] + h - _KISS)
            if axis == "x":
                if i0[1] < line < i0[3] and i0[2] > lo and i0[0] < hi:
                    blocked.append((max(i0[0], lo), min(i0[2], hi)))
            else:
                if i0[0] < line < i0[2] and i0[3] > lo and i0[1] < hi:
                    blocked.append((max(i0[1], lo), min(i0[3], hi)))
        cur = lo
        for a, b in sorted(blocked):
            if a > cur:
                ts.add((cur + a) / 2.0 - lo)
            cur = max(cur, b)
        if cur < hi:
            ts.add((cur + hi) / 2.0 - lo)
        ts = {t for t in ts if 0.0 < t < w}
        if axis == "x":
            return [(x + t, y + inw * d) for t in sorted(ts)]
        return [(x + inw * d, y + t) for t in sorted(ts)]
    return fn


def _solid_model(outline, subrooms, obstacle_rects, room):
    """Everything a walking envelope may not overlap, as mm rects: obstacles,
    sub-room keep-outs (as-built walls, doorways gapped), outside-the-outline
    cells, and a frame around the outline bbox."""
    xs, ys, free = _cell_grid(outline)
    solids = list(obstacle_rects)
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if not free[i][j]:
                solids.append((xs[i], ys[j], xs[i + 1], ys[j + 1]))
    for sr in subrooms:
        solids += _keepout_cells(sr, _room_thk(room, sr), door_gap=True)
    x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
    M = 10000.0
    solids += [(x0 - M, y0 - M, x1 + M, y0), (x0 - M, y1, x1 + M, y1 + M),
               (x0 - M, y0 - M, x0, y1 + M), (x1, y0 - M, x1 + M, y1 + M)]
    return solids, (x0, y0, x1, y1)


def _seg_hits_rect(x0, y0, x1, y1, rect, eps=0.25):
    """Segment strictly crosses the rect INTERIOR (rect shrunk by eps so a flush
    touch stays legal). Exact Liang-Barsky — point sampling stepped over blockers
    thinner than the step (geometry-lens finding #4, false-PASS through a 10 mm
    partition)."""
    bx0, by0, bx1, by1 = rect[0] + eps, rect[1] + eps, rect[2] - eps, rect[3] - eps
    if bx0 >= bx1 or by0 >= by1:
        return False
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - bx0), (dx, bx1 - x0), (-dy, y0 - by0), (dy, by1 - y0)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            if t > t0:
                t0 = t
        else:
            if t < t1:
                t1 = t
        if t0 - t1 > 1e-12:
            return False
    return t1 - t0 > 1e-12


def _los_clear(from_pt, target_rect, solids):
    """Straight line from from_pt to the nearest point of target_rect crosses no
    solid (solids overlapping the target itself are ignored — e.g. the platform
    under a bed). Blocks 'reached through a thin wall' false positives."""
    tx = min(max(from_pt[0], target_rect[0]), target_rect[2])
    ty = min(max(from_pt[1], target_rect[1]), target_rect[3])
    return not any(_seg_hits_rect(from_pt[0], from_pt[1], tx, ty, s)
                   for s in solids if not _rects_overlap(s, target_rect))


def _envelope_reaches(solids, bbox, W, starts, target_rect, tol):
    """True when a WxW axis-aligned envelope (tracked by its centre) can travel
    from ANY start point to within (W/2 + tol) of target_rect — with line of
    sight to it — avoiding all solids. L∞ erosion: inflate every solid by W/2,
    multi-source BFS over the free cells of the rect arrangement. Exact for
    axis-aligned geometry."""
    h = W / 2.0 - _KISS   # slide-fit: gap == W passes (finding #2, exact-kiss)
    inf = [(s[0] - h, s[1] - h, s[2] + h, s[3] + h) for s in solids]
    tinf = (target_rect[0] - h - tol, target_rect[1] - h - tol,
            target_rect[2] + h + tol, target_rect[3] + h + tol)
    xs = sorted({round(v, 3) for r in inf for v in (r[0], r[2])}
                | {round(tinf[0], 3), round(tinf[2], 3)}
                | {round(p[0], 3) for p in starts}
                | {round(bbox[0], 3), round(bbox[2], 3)})
    ys = sorted({round(v, 3) for r in inf for v in (r[1], r[3])}
                | {round(tinf[1], 3), round(tinf[3], 3)}
                | {round(p[1], 3) for p in starts}
                | {round(bbox[1], 3), round(bbox[3], 3)})
    nx, ny = len(xs) - 1, len(ys) - 1
    if nx <= 0 or ny <= 0:
        return False
    free = []
    for i in range(nx):
        cx = (xs[i] + xs[i + 1]) / 2.0
        col = []
        for j in range(ny):
            cy = (ys[j] + ys[j + 1]) / 2.0
            col.append(not any(r[0] < cx < r[2] and r[1] < cy < r[3] for r in inf))
        free.append(col)

    seen = [[False] * ny for _ in range(nx)]
    q = deque()
    for sp in starts:
        si = min(max(bisect_right(xs, sp[0]) - 1, 0), nx - 1)
        sj = min(max(bisect_right(ys, sp[1]) - 1, 0), ny - 1)
        if free[si][sj] and not seen[si][sj]:
            seen[si][sj] = True
            q.append((si, sj))
    if not q:
        return False

    def hits_target(i, j):
        if not (xs[i] < tinf[2] and tinf[0] < xs[i + 1]
                and ys[j] < tinf[3] and tinf[1] < ys[j + 1]):
            return False
        # closest point of the cell to the target, then require line of sight
        px = min(max((target_rect[0] + target_rect[2]) / 2.0, xs[i]), xs[i + 1])
        py = min(max((target_rect[1] + target_rect[3]) / 2.0, ys[j]), ys[j + 1])
        return _los_clear((px, py), target_rect, solids)

    while q:
        i, j = q.popleft()
        if hits_target(i, j):
            return True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny and not seen[a][b] and free[a][b]:
                seen[a][b] = True
                q.append((a, b))
    return False


def _bottleneck(solids, bbox, starts_fn, target_rect, tol=_REACH, wmax=_ENVELOPE_MAX):
    """Widest envelope (mm, 1 mm resolution) that can travel door -> target.
    0 = unreachable even by a hairline envelope; wmax = 'at least wmax'."""
    def ok(W):
        return _envelope_reaches(solids, bbox, float(W), starts_fn(float(W), solids),
                                 target_rect, tol)
    if not ok(1):
        return 0
    if ok(wmax):
        return wmax
    lo, hi = 1, wmax
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return lo


def _swing_geom(door, into):
    """(hinge, radius, quadrant_rect) of the quarter-disc a door leaf sweeps,
    or None when wall/swing are missing. `into=+1` sweeps to the wall-owner's
    inside, -1 to the other side. '-left' hinges at the segment start (lower
    coordinate along the leaf axis), '-right' at the far end."""
    wall = str(door.get("wall", "")).lower()
    swing = str(door.get("swing", "")).lower()
    if wall not in _WALL_AXIS or not swing.endswith(("left", "right")):
        return None
    x, y, w = float(door["x"]), float(door["y"]), float(door["w"])
    axis, inw = _WALL_AXIS[wall]
    side = inw * into
    left = swing.endswith("left")
    if axis == "x":
        hx = x if left else x + w
        qx = (hx, hx + w) if left else (hx - w, hx)
        qy = (y, y + w) if side > 0 else (y - w, y)
        return (hx, y), w, (qx[0], qy[0], qx[1], qy[1])
    hy = y if left else y + w
    qy = (hy, hy + w) if left else (hy - w, hy)
    qx = (x, x + w) if side > 0 else (x - w, x)
    return (x, hy), w, (qx[0], qy[0], qx[1], qy[1])


def _swing_hit(geom, rect, eps=0.5):
    """Does `rect` intrude into the swept quarter-disc? Exact: clip the rect to
    the quadrant, then closest-point-to-hinge distance vs the leaf radius."""
    (hx, hy), r, q = geom
    cx0, cy0 = max(rect[0], q[0]), max(rect[1], q[1])
    cx1, cy1 = min(rect[2], q[2]), min(rect[3], q[3])
    if cx0 >= cx1 - 1e-9 or cy0 >= cy1 - 1e-9:
        return False
    nx = min(max(hx, cx0), cx1)
    ny = min(max(hy, cy0), cy1)
    return (nx - hx) ** 2 + (ny - hy) ** 2 < (r - eps) ** 2


def _outside_cells(poly):
    """Cells of the polygon's bbox that lie OUTSIDE the polygon + a frame around
    the bbox — the 'wall side' obstacles for swing WARN checks."""
    xs, ys, free = _cell_grid(poly)
    cells = [(xs[i], ys[j], xs[i + 1], ys[j + 1])
             for i in range(len(xs) - 1) for j in range(len(ys) - 1) if not free[i][j]]
    x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
    M = 10000.0
    cells += [(x0 - M, y0 - M, x1 + M, y0), (x0 - M, y1, x1 + M, y1 + M),
              (x0 - M, y0 - M, x0, y1 + M), (x1, y0 - M, x1 + M, y1 + M)]
    return cells


# furniture pairs that are SUPPOSED to sit on/next to each other -> not a conflict
_OK_OVERLAP = {frozenset({"bed", "platform"}), frozenset({"bed", "nightstand"}),
               frozenset({"platform", "nightstand"}), frozenset({"platform", "bench"}),
               frozenset({"sofa", "coffee_table"}), frozenset({"sofa", "armchair"})}


def check(spec):
    out = []
    def add(status, name, detail): out.append({"status": status, "check": name, "detail": detail})

    r = spec["room"]
    outline = [tuple(p) for p in r["outline_mm"]]
    subrooms = spec.get("subrooms", [])
    ceiling = float(r["ceiling_mm"]) if r.get("ceiling_mm") else None
    area = _shoelace(outline)
    rtype = str(r.get("type", "")).lower()
    wet_room = any(k in rtype for k in _WET)
    balcony = ("balcony" in rtype) or ("ระเบียง" in rtype)
    office_dining = any(k in rtype for k in ("office", "สำนักงาน", "classroom",
                                             "ห้องเรียน", "dining_room", "ห้องอาหาร"))
    all_rectilinear = (_is_rectilinear(outline)
                       and all(_is_rectilinear([tuple(p) for p in sr["outline_mm"]])
                               for sr in subrooms))

    # 1) vertical clearances. ข้อ 22's habitable 2600 (and ระเบียง 2200) are
    # ระยะดิ่ง = FLOOR-TO-FLOOR; spec ceiling_mm is CLEAR height: clear >= min
    # proves compliance a fortiori, clear < min proves NOTHING -> WARN. Wet rooms
    # are the exception in the statute itself: ฉ.39 ข้อ 9 and ข้อ 22's ห้องน้ำ row
    # are both พื้นถึงเพดาน -> clear height IS the statute basis, decisive.
    if wet_room:
        smin = RULES_TH["ceiling_min_bath"]
        if ceiling is None:
            add("FAIL", "ceiling height (room)", "room.ceiling_mm missing — provide the clear height")
        else:
            add("PASS" if ceiling >= smin else "FAIL", "ceiling height (room, wet)",
                f"clear {ceiling:.0f} mm vs {smin} min ({RULES_TH['ceiling_min_bath_cite']} — "
                f"ห้องน้ำ–ส้วม พื้นถึงเพดาน; ข้อ 22 wet row agrees)")
    else:
        cmin = RULES_TH["ceiling_min_balcony"] if balcony else RULES_TH["ceiling_min_habitable"]
        ccite = RULES_TH["ceiling_min_balcony_cite"] if balcony else RULES_TH["ceiling_min_habitable_cite"]
        measured = None
        f2f = r.get("floor_to_floor_mm")
        if f2f is not None:
            try:
                f2fv = float(f2f)
            except (TypeError, ValueError):
                f2fv = None
            if f2fv is None:
                add("FAIL", "ระยะดิ่ง (room, floor-to-floor)", f"floor_to_floor_mm invalid: {f2f!r}")
            else:
                measured = f2fv
                add("PASS" if f2fv >= cmin else "FAIL", "ระยะดิ่ง (room, floor-to-floor)",
                    f"{f2fv:.0f} mm vs {cmin} min ({ccite})")
            if ceiling is not None:
                add("PASS", "clear ceiling (informational)",
                    f"clear {ceiling:.0f} mm recorded — statute checked on floor-to-floor above")
            else:
                add("FAIL", "ceiling height (room)", "room.ceiling_mm missing — provide the clear height")
        elif ceiling is None:
            add("FAIL", "ceiling height (room)",
                "room.ceiling_mm missing — cannot check ข้อ 22 even as a clear-height proxy")
        elif ceiling >= cmin:
            measured = ceiling
            add("PASS", "ceiling height (room)",
                f"clear {ceiling:.0f} mm >= {cmin} floor-to-floor min -> compliant a fortiori ({ccite})")
        else:
            add("WARN", "ceiling height (room)",
                f"clear {ceiling:.0f} mm < {cmin} floor-to-floor min — clear height cannot prove "
                f"a ข้อ 22 breach; provide room.floor_to_floor_mm to verify ({ccite})")
        if office_dining and measured is not None and measured < RULES_TH["ceiling_office_dining"]:
            add("WARN", "ระยะดิ่ง (office/dining tier)",
                f"{measured:.0f} mm < {RULES_TH['ceiling_office_dining']} — ข้อ 22 sets 3.00 m for "
                f"สำนักงาน/ห้องเรียน/ห้องอาหาร; whether an in-unit study/dining space takes that "
                f"tier is unresolved — verify the use classification "
                f"({RULES_TH['ceiling_office_dining_cite']})")

    for sr in subrooms:
        sname = sr.get("name", "sub")
        wet = any(k in (str(sname) + str(sr.get("th", ""))).lower() for k in _WET)
        if not sr.get("ceiling_mm"):
            add("FAIL", f"ceiling ({sname})", "ceiling_mm missing — provide the clear height")
        else:
            sc = float(sr["ceiling_mm"])
            if wet:
                smin = RULES_TH["ceiling_min_bath"]
                add("PASS" if sc >= smin else "FAIL", f"ceiling ({sname})",
                    f"{sc:.0f} mm vs {smin} min ({RULES_TH['ceiling_min_bath_cite']} — พื้นถึงเพดาน)")
            elif sc >= RULES_TH["ceiling_min_habitable"]:
                add("PASS", f"ceiling ({sname})",
                    f"clear {sc:.0f} mm >= {RULES_TH['ceiling_min_habitable']} floor-to-floor min "
                    f"-> compliant a fortiori")
            else:
                add("WARN", f"ceiling ({sname})",
                    f"clear {sc:.0f} mm < {RULES_TH['ceiling_min_habitable']} floor-to-floor min — "
                    f"cannot prove breach from clear height")
        if wet:
            _bath_checks(add, sname, [tuple(p) for p in sr["outline_mm"]],
                         sr.get("fixtures", []))
    if wet_room:
        _bath_checks(add, rtype or "room", outline,
                     spec.get("items", []) + spec.get("builtins", []))

    # 2) entry door size
    door = spec.get("door")
    if door:
        dw, dh = float(door.get("w", 0)), float(door.get("h", 0))
        add("PASS" if dw >= RULES_TH["door_w_min"] else "FAIL", "door width",
            f"{dw:.0f} mm vs {RULES_TH['door_w_min']} min ({RULES_TH['door_cite']})")
        add("PASS" if dh >= RULES_TH["door_h_min"] else "FAIL", "door height",
            f"{dh:.0f} mm vs {RULES_TH['door_h_min']} min ({RULES_TH['door_cite']})")

    # 3) ฉ.55 ข้อ 20 (bedrooms) / ข้อ 21 (corridors). Tier honesty: statutory FAIL
    # only on the charitable basis (raw outlines), statutory PASS only on the
    # as-built basis (keep-out incl. wall band), WARN in between.
    typed_bedroom = bool(re.search(r"(^|[^a-z])bed(room)?($|[^a-z])", rtype)) or "นอน" in rtype
    bed_item = any(it.get("kind") == "bed" for it in spec.get("items", []))
    is_corridor = any(k in rtype for k in ("corridor", "hall", "ทางเดิน", "โถง"))
    sub_area = sum(_shoelace([tuple(p) for p in sr["outline_mm"]]) for sr in subrooms)
    beds = [it for it in spec.get("items", []) if it.get("kind") == "bed"]
    bed_rect = _bbox(beds[0]) if beds else None
    legs = _leg_analysis(outline, subrooms, r, bed_rect) if all_rectilinear else None

    if all_rectilinear:
        keep = [c for sr in subrooms for c in _keepout_cells(sr, _room_thk(r, sr), door_gap=False)]
        holes = [[tuple(p) for p in sr["outline_mm"]] for sr in subrooms]
        net_low = _free_area(*_cell_grid(outline, (), keep))     # as-built (walls carve too)
        net_high = _free_area(*_cell_grid(outline, holes))       # charitable (raw outlines)
    else:
        net_low = net_high = None

    if typed_bedroom or bed_item:
        viol = "FAIL" if typed_bedroom else "WARN"
        how = "" if typed_bedroom else (f" [heuristic: type '{rtype}' is not bedroom-named "
                                        f"but a bed item is present — verify the room type]")
        amin = RULES_TH["bedroom_area_min_mm2"]
        if net_low is not None:
            if net_low >= amin:
                add("PASS", "bedroom area (net of sub-rooms)",
                    f"{net_low/1e6:.1f} m² net as-built (outline {area/1e6:.1f}; sub-rooms + wall "
                    f"bands carved exactly) vs {amin/1e6:.0f} m² min ({RULES_TH['bedroom_area_cite']}){how}")
            elif net_high < amin:
                add(viol, "bedroom area (net of sub-rooms)",
                    f"{net_high/1e6:.1f} m² net even on the charitable basis (raw sub-room outlines) "
                    f"vs {amin/1e6:.0f} m² min ({RULES_TH['bedroom_area_cite']}){how}")
            else:
                add("WARN", "bedroom area (net of sub-rooms)",
                    f"net area straddles the floor: {net_low/1e6:.1f} m² as-built vs "
                    f"{net_high/1e6:.1f} m² on raw outlines, min {amin/1e6:.0f} m² — verify wall "
                    f"thickness on plan ({RULES_TH['bedroom_area_cite']}){how}")
        else:
            net = area - sub_area   # lower bound: subtraction can only over-carve
            if net >= amin:
                add("PASS", "bedroom area (net of sub-rooms)",
                    f"{net/1e6:.1f} m² net (lower bound, outline {area/1e6:.1f} − sub-rooms "
                    f"{sub_area/1e6:.1f}) vs {amin/1e6:.0f} m² min ({RULES_TH['bedroom_area_cite']}){how}")
            else:
                add("WARN", "bedroom area (net of sub-rooms)",
                    f"{net/1e6:.1f} m² by subtraction (a lower bound — non-rectilinear geometry "
                    f"prevents an exact net) vs {amin/1e6:.0f} m² min — verify on plan "
                    f"({RULES_TH['bedroom_area_cite']}){how}")

        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        narrow = min(bw, bh)
        wmin = RULES_TH["bedroom_width_min"]
        true_rect = len(outline) == 4 and abs(area - bw * bh) < 1.0
        if narrow < wmin:
            # bbox min-dim >= every true leg width, so bbox < min PROVES the breach
            add(viol, "bedroom narrow side",
                f"{narrow:.0f} mm vs {wmin} min ({RULES_TH['bedroom_width_cite']}){how}")
        elif true_rect and not subrooms:
            add("PASS", "bedroom narrow side",
                f"{narrow:.0f} mm vs {wmin} min ({RULES_TH['bedroom_width_cite']}){how}")
        elif legs is None:
            add("WARN", "bedroom narrow side (unproven)",
                f"bbox {narrow:.0f} mm >= {wmin}, but the geometry is not rectilinear — this "
                f"engine cannot prove the true narrow side; verify >= {wmin} on the plan "
                f"({RULES_TH['bedroom_width_cite']}){how}")
        elif legs["outer"]["min_leg"] >= wmin:
            add("PASS", "bedroom narrow side (leg-proof, as-built)",
                f"min clear leg width {legs['outer']['min_leg']:.0f} mm >= {wmin} with sub-room "
                f"wall bands carved — every maximal clear rectangle is >= {wmin} narrow, so the "
                f"strictest reading of ด้านแคบที่สุด is satisfied ({RULES_TH['bedroom_width_cite']}){how}")
        elif legs["inner"]["best_leg"] < wmin:
            add(viol, "bedroom narrow side (leg-proof)",
                f"no clear zone >= {wmin} mm wide exists even on raw sub-room outlines (widest "
                f"leg {legs['inner']['best_leg']:.0f} mm) — breach under every reading of "
                f"ด้านแคบที่สุด ({RULES_TH['bedroom_width_cite']}){how}")
        else:
            o = legs["outer"]
            where = (f"; the sleeping zone sits in a {o['bed_leg']:.0f} mm leg"
                     if o["bed_leg"] else "")
            add("WARN", "bedroom narrow side (interpretation)",
                f"as-built legs measure {o['min_leg']:.0f}–{o['best_leg']:.0f} mm{where}: the "
                f"narrowest leg is under {wmin} but wider zones exist — how ด้านแคบที่สุด applies "
                f"to a carved room is not resolved in the vault; human call, or widen the "
                f"{o['min_leg']:.0f} mm leg to {wmin} to make it decisive "
                f"({RULES_TH['bedroom_width_cite']}){how}")

    if is_corridor:
        # ข้อ 21 trichotomy mirrors ข้อ 20. Tier split per the vault: 1000 binds
        # ภายในหน่วย of บ้านเดี่ยว/ทาวน์โฮม; the 1500 tier is recorded for the
        # COMMON corridors of อาคารอยู่อาศัยรวม — whether it also binds an in-unit
        # condo corridor is a vault gap, so that direction can only WARN.
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        bbox_narrow = min(max(xs) - min(xs), max(ys) - min(ys))
        building = str(r.get("building", "")).lower()
        shared = any(k in building for k in ("รวม", "condo", "apartment", "หอพัก", "dorm",
                                             "office", "สำนักงาน", "พาณิชย์", "commercial",
                                             "สาธารณะ", "public"))
        house = any(k in building for k in ("house", "บ้าน", "town", "ทาวน์"))
        cmin1, cite1 = RULES_TH["corridor_min"], RULES_TH["corridor_cite"]
        cmin2, cite2 = RULES_TH["corridor_shared_min"], RULES_TH["corridor_shared_cite"]
        w_pass = legs["outer"]["min_leg"] if legs else None    # as-built, proves compliance
        w_fail = legs["inner"]["best_leg"] if legs else bbox_narrow  # charitable, proves breach
        if shared:
            if w_pass is not None and w_pass >= cmin2:
                add("PASS", "corridor width (ข้อ 21)",
                    f"min clear leg width {w_pass:.0f} mm >= {cmin2} as-built — satisfies the "
                    f"strictest tier ({cite2})")
            else:
                shown = w_pass if w_pass is not None else bbox_narrow
                extra = ("" if shown >= cmin1 else
                         f"; it is also under the {cmin1} บ้านเดี่ยว tier ({cite1})")
                add("WARN", "corridor width (ข้อ 21)",
                    f"{shown:.0f} mm < {cmin2}: the vault ties the 1500 tier to COMMON corridors "
                    f"of อาคารอยู่อาศัยรวม — whether it binds an IN-UNIT condo corridor is a "
                    f"recorded vault gap; resolve in codes-th before gating on it{extra} ({cite2})")
        elif house:
            if w_pass is not None and w_pass >= cmin1:
                add("PASS", "corridor width (ข้อ 21)",
                    f"min clear leg width {w_pass:.0f} mm >= {cmin1} as-built ({cite1})")
            elif w_fail < cmin1:
                add("FAIL", "corridor width (ข้อ 21)",
                    f"no clear run >= {cmin1} mm exists even on the charitable basis (widest leg "
                    f"{w_fail:.0f} mm) ({cite1})")
            else:
                lo = w_pass if w_pass is not None else bbox_narrow
                add("WARN", "corridor width (ข้อ 21)",
                    f"legs measure {lo:.0f}–{w_fail:.0f} mm vs {cmin1}: a niche/alcove or wall "
                    f"band narrows the minimum without necessarily narrowing the walking run — "
                    f"verify the run width on plan ({cite1})")
        else:
            if w_pass is not None and w_pass >= cmin2:
                add("PASS", "corridor width (ข้อ 21)",
                    f"min clear leg width {w_pass:.0f} mm >= {cmin2} as-built — satisfies both "
                    f"tiers ({cite1}; {cite2})")
            else:
                shown = w_pass if w_pass is not None else bbox_narrow
                hint = (f"if this is a บ้านเดี่ยว/ทาวน์โฮม corridor it breaches ข้อ 21 ({cmin1}); "
                        if w_fail < cmin1 else "")
                add("WARN", "corridor width (ข้อ 21)",
                    f"{shown:.0f} mm with room.building unset: {hint}the {cmin2} tier ({cite2}) "
                    f"is recorded for common corridors — set room.building to decide ({cite1})")

    if not (typed_bedroom or bed_item or is_corridor or wet_room):
        add("PASS", "floor area (informational)",
            f"{area/1e6:.1f} m² — not detected as a bedroom (by type/items heuristic); if it IS "
            f"one, ฉ.55 ข้อ 20 applies (>= {RULES_TH['bedroom_area_min_mm2']/1e6:.0f} m² net, "
            f"narrow side >= {RULES_TH['bedroom_width_min']} mm); unit-level ฉ.55 ข้อ 19 "
            f"(20 m²) binds the whole unit, not this room")

    # 4) furniture + built-ins inside the NET room: outside the outline, or
    # strictly inside a sub-room's AS-BUILT keep-out (footprint + wall band),
    # is a FAIL; flush against the band is legal.
    keepout_nogap = [c for sr in subrooms
                     for c in _keepout_cells(sr, _room_thk(r, sr), door_gap=False)]
    placed = [dict(it, _grp="item") for it in spec.get("items", [])] + \
             [dict(b, _grp="builtin") for b in spec.get("builtins", [])]
    for it in placed:
        nm = it.get("name") or it.get("kind", "item")
        rot = float(it.get("rot", 0) or 0)
        if abs(rot % 90.0) > 1e-6:
            add("WARN", f"in-bounds: {nm}",
                f"rot {rot:.0f}° is not axis-aligned — checked as the unrotated footprint; "
                f"verify placement on plan")
        pts = _corners(it)
        pts.append((sum(p[0] for p in pts) / 4.0, sum(p[1] for p in pts) / 4.0))
        out_poly = [p for p in pts if not _inside_or_on(p[0], p[1], outline)]
        in_keep = [p for p in pts
                   if any(_strictly_in_rect(p[0], p[1], c) for c in keepout_nogap)]
        if out_poly:
            add("FAIL", f"in-bounds: {nm}", f"{len(out_poly)} point(s) outside the room polygon")
        elif in_keep:
            add("FAIL", f"in-bounds: {nm}",
                f"{len(in_keep)} point(s) inside a sub-room's as-built keep-out (footprint + "
                f"wall band) — move it, or model it as that sub-room's fixture")
        else:
            add("PASS", f"in-bounds: {nm}", "inside the net room")

    # 5) overlaps between placed pieces (excluding designed adjacencies)
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            a, b = placed[i], placed[j]
            if frozenset({a.get("kind"), b.get("kind")}) in _OK_OVERLAP:
                continue
            kinds = (a.get("kind"), b.get("kind"))
            if ("rug" in kinds and kinds[0] != kinds[1]
                    and a["_grp"] == "item" and b["_grp"] == "item"):
                continue          # loose furniture ON a rug is the intent, not a conflict
            if _overlap(a, b):
                add("WARN", f"overlap: {a.get('name', a.get('kind'))} / {b.get('name', b.get('kind'))}",
                    "footprints intersect (ok if stacked/against a wall)")

    # 6) sub-room fixtures: inside their sub-room + pairwise overlaps
    for sr in subrooms:
        so = [tuple(p) for p in sr["outline_mm"]]
        fxs = sr.get("fixtures", [])
        for fx in fxs:
            outc = [c for c in _corners(fx) if not _inside_or_on(c[0], c[1], so)]
            add("PASS" if not outc else "WARN",
                f"fixture in {sr.get('name','sub')}: {fx.get('name', fx.get('kind'))}",
                "inside" if not outc else "extends past the sub-room wall")
        for i in range(len(fxs)):
            for j in range(i + 1, len(fxs)):
                a, b = fxs[i], fxs[j]
                if frozenset({a.get("kind"), b.get("kind")}) in _OK_OVERLAP:
                    continue
                if _overlap(a, b):
                    add("WARN",
                        f"overlap in {sr.get('name','sub')}: "
                        f"{a.get('name', a.get('kind'))} / {b.get('name', b.get('kind'))}",
                        "fixture footprints intersect")

    # 7) Gate 0 circulation: widest walking envelope from the entry door to the
    # primary use point (bed ∪ its platform / sofa) and every sub-room door.
    # Furniture (except rugs) + as-built sub-room walls (doorways open) are solid.
    # Floors are ERGONOMIC (dimensional_rules circulation, Panero) — buildability,
    # not statute. The doorway leaf width is NOT an envelope cap by design (doors
    # are permitted pinch points with their own 800 mm studio floor).
    wp, wm = RULES_TH["walkway_pinch"], RULES_TH["walkway_main"]
    if door and str(door.get("wall", "")).lower() in _WALL_AXIS:
        obstacle_rects = [_bbox(o) for o in placed if o.get("kind") != "rug"]
        solids, bx = _solid_model(outline, subrooms, obstacle_rects, r)
        starts_fn = _door_starts(door)
        targets = []
        sofas = [it for it in spec.get("items", []) if it.get("kind") == "sofa"]
        if beds:
            trect = _bbox(beds[0])
            for it in spec.get("items", []):
                if (it.get("kind") == "platform" and float(it.get("h", 0) or 0) <= 250
                        and _overlap(it, beds[0])):
                    p = _bbox(it)   # stepping onto a low platform reaches the bed
                    trect = (min(trect[0], p[0]), min(trect[1], p[1]),
                             max(trect[2], p[2]), max(trect[3], p[3]))
            targets.append((beds[0].get("name", "bed"), trect))
        elif sofas:
            targets.append((sofas[0].get("name", "sofa"), _bbox(sofas[0])))
        for sr in subrooms:
            sd = sr.get("door")
            seg = _door_segment(sd) if sd else None
            if seg:
                targets.append((f"{sr.get('name','sub')} door", seg))
        for nm, trect in targets:
            W = _bottleneck(solids, bx, starts_fn, trect)
            label = f"circulation: entry -> {nm}"
            if W <= 0:
                add("FAIL", label,
                    "no clear path — target unreachable without crossing furniture or walls")
            elif W < wp:
                add("FAIL", label,
                    f"bottleneck {W} mm < {wp:.0f} minimum passage pinch "
                    f"(dimensional_rules circulation — ergonomic buildability floor, not statute)")
            elif W < wm:
                add("WARN", label,
                    f"bottleneck {W} mm — passable but below the {wm:.0f} main-walkway "
                    f"ergonomic target (dimensional_rules circulation)")
            else:
                shown = f">={W}" if W >= _ENVELOPE_MAX else f"{W}"
                add("PASS", label,
                    f"bottleneck {shown} mm >= {wm:.0f} main walkway (ergonomic; "
                    f"reach tolerance {_REACH:.0f} mm)")
    else:
        add("WARN", "circulation",
            "no entry door (with a known wall) in the spec — Gate 0 circulation not checked")

    # 8) Gate 0 door-swing arcs: exact quarter-disc tests. Furniture / sub-room
    # walls in the arc -> FAIL (the leaf physically cannot open). The room's own
    # boundary in the arc -> WARN (leaf stops before 90° on a perpendicular wall).
    def _swing_check(label, geom, fail_obs, warn_obs):
        hits = sorted({nm for nm, rect in fail_obs if _swing_hit(geom, rect)})
        if hits:
            add("FAIL", f"door swing: {label}",
                "leaf arc intersects: " + ", ".join(hits[:4]))
        elif any(_swing_hit(geom, rect) for rect in warn_obs):
            add("WARN", f"door swing: {label}",
                "leaf reaches the room boundary before 90° — door opens only partially "
                "against a perpendicular wall; verify that is acceptable")
        else:
            add("PASS", f"door swing: {label}", "quarter-disc sweep is clear")

    room_fail_obs = [(o.get("name") or o.get("kind", "item"), _bbox(o))
                     for o in placed if o.get("kind") != "rug"]
    for sr in subrooms:
        room_fail_obs += [(f"{sr.get('name','sub')} (sub-room walls)", c)
                          for c in _keepout_cells(sr, _room_thk(r, sr), door_gap=True)]
    room_warn_obs = _outside_cells(outline)
    if door:
        sw = str(door.get("swing", "")).lower()
        geom = _swing_geom(door, +1) if sw.startswith("in") else None
        if geom:
            _swing_check("entry", geom, room_fail_obs, room_warn_obs)
        else:
            add("WARN", "door swing: entry",
                "swing missing/out-swinging — arc not checked (out-swing leaves the room spec)")
    for sr in subrooms:
        sd = sr.get("door")
        if not sd:
            continue
        nm = sr.get("name", "sub")
        sw = str(sd.get("swing", "")).lower()
        so = [tuple(p) for p in sr["outline_mm"]]
        if sw.startswith("out"):
            geom = _swing_geom(sd, -1)
            if geom:
                _swing_check(nm, geom, room_fail_obs, room_warn_obs)
                continue
        elif sw.startswith("in"):
            geom = _swing_geom(sd, +1)
            if geom:
                fx_obs = [(f.get("name") or f.get("kind", "fixture"), _bbox(f))
                          for f in sr.get("fixtures", []) if f.get("kind") != "rug"]
                _swing_check(f"{nm} (into sub-room)", geom, fx_obs, _outside_cells(so))
                continue
        add("WARN", f"door swing: {nm}",
            "swing not specified — leaf arc not checked (add door.swing in/out-left/right)")

    return out


def _bath_checks(add, label, outline_poly, fixtures):
    """ฉ.39 ข้อ 9 tiers for one wet space. Combined (ห้องน้ำ+ส้วมรวม): area >= 1.5 m².
    Separated (แยกห้อง): area >= 0.9 m² AND internal width >= 900 mm. The tier is
    resolved from fixtures/names; unknown -> FAIL only below BOTH floors, PASS only
    above both, WARN in between naming the combined-vs-separated question."""
    area_m2 = _shoelace(outline_poly) / 1e6
    kinds = {str(f.get("kind", "")).lower() for f in fixtures}
    txt = (str(label) + " " + " ".join(str(f.get("name", "")) for f in fixtures)).lower()
    has_wc = bool(kinds & {"wc", "toilet"}) or "ส้วม" in txt or "ชักโครก" in txt
    has_wash = (bool(kinds & {"shower", "tub", "bathtub"})
                or "อาบน้ำ" in txt or "ฝักบัว" in txt or "อ่างอาบ" in txt)
    a15, a09, w900 = RULES_TH["bath_comb_min_m2"], RULES_TH["bath_sep_min_m2"], RULES_TH["bath_sep_min_w"]
    cite = RULES_TH["bath_cite"]
    xs = [p[0] for p in outline_poly]; ys = [p[1] for p in outline_poly]
    bbox_narrow = min(max(xs) - min(xs), max(ys) - min(ys))
    lw = _leg_widths(outline_poly) if _is_rectilinear(outline_poly) else None
    width = lw["min_leg"] if lw else bbox_narrow
    width_provable = lw is not None

    if has_wc and has_wash:
        add("PASS" if area_m2 >= a15 else "FAIL", f"bath area ({label})",
            f"{area_m2:.2f} m² vs {a15} m² min ({cite} — ห้องน้ำ+ส้วมรวมกัน; fixtures show both)")
    elif has_wc or has_wash:
        which = "ห้องส้วมแยก" if has_wc else "ห้องอาบน้ำแยก"
        add("PASS" if area_m2 >= a09 else "FAIL", f"bath area ({label})",
            f"{area_m2:.2f} m² vs {a09} m² min ({cite} — แยกห้อง: {which})")
        if width_provable:
            add("PASS" if width >= w900 else "FAIL", f"bath width ({label})",
                f"{width:.0f} mm internal vs {w900} min ({cite} — แยกห้อง กว้างภายใน)")
        elif width < w900:
            add("FAIL", f"bath width ({label})",
                f"bbox {width:.0f} mm < {w900} — bbox bounds every width from above ({cite})")
        else:
            add("WARN", f"bath width ({label})",
                f"bbox {width:.0f} mm >= {w900} but the outline is not rectilinear — verify the "
                f"internal width on plan ({cite})")
    else:
        if area_m2 < a09:
            add("FAIL", f"bath area ({label})",
                f"{area_m2:.2f} m² < {a09} m² — below BOTH ฉ.39 tiers (combined {a15} / "
                f"separated {a09}) ({cite})")
        elif area_m2 >= a15 and width_provable and width >= w900:
            add("PASS", f"bath area ({label})",
                f"{area_m2:.2f} m² >= {a15} and width {width:.0f} >= {w900} — satisfies both "
                f"ฉ.39 tiers (fixtures unknown) ({cite})")
        else:
            add("WARN", f"bath area ({label})",
                f"{area_m2:.2f} m² / width {width:.0f} mm with no fixture data — combined "
                f"({a15} m²) vs separated ({a09} m² + {w900} mm) tier unresolved; add fixtures "
                f"or verify on plan ({cite})")


def report(spec, label=""):
    res = check(spec)
    icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX"}
    print(f"\n=== suite clearance {label} (metric, Thai code, Gate 0) ===")
    for r in res:
        print(f"  [{icon[r['status']]}] {r['check']}: {r['detail']}")
    fails = sum(x["status"] == "FAIL" for x in res)
    warns = sum(x["status"] == "WARN" for x in res)
    verdict = "FAIL" if fails else ("REVIEW" if warns else "PASS")
    print(f"  -> {verdict}  ({fails} fail, {warns} warn)")
    print("  (statutory floors from dimensional_rules.v0.2.json thai_code_minimums, cited to knowledge/codes-th.")
    print("   ENFORCED: ceiling ข้อ 22 tiers (habitable/ระเบียง; wet = พื้นถึงเพดาน 2000 with ฉ.39) + ฉ.39 bath")
    print("   area/width tiers; ข้อ 20 net-area + narrow side and ข้อ 21 corridor width with AS-BUILT wall bands")
    print("   (PASS on as-built, FAIL only on the charitable basis, WARN between); in-bounds vs net room;")
    print("   overlaps; circulation bottleneck + door-swing arcs (Gate 0; ergonomic floors 610/910 = Panero,")
    print("   not statute). Door 800/1900 = STUDIO floor. NOT yet: turning circles, knee/toe (need catalog);")
    print("   clearance_check.py unification still open.)")
    return res, verdict


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    report(spec, os.path.basename(spec_path))
