"""
zone_flag.py -- F3/F5: PROPOSE an indoor / outdoor_same_floor / below_grade CLASS for a
drawn element, using only machine-derivable geometry, so the machine can FLAG the exact
call the owner had to make by hand.

    (pure logic here; the fitz extraction + gate wiring live in placement_gate.run())

THE WOUND THIS CLOSES (PRJ-2026-002 floor-2, the "F3" incident): a south area was read as
an OUTDOOR terrace with tree-planters; the owner corrected it to an INDOOR floor-2 lounge
behind a south GLASS facade, with the garden trees being GROUND BELOW (y<0), seen through /
below the glass -- NOT floor-2 objects. The correction survived only as owner-redrawn
geometry, never a durable machine proposal. This module lets the machine PROPOSE the class;
placement_gate.confirmed_zone makes the owner's final call durable (the CALL stays owner --
two-layer law: geometry is machine-solved, indoor/outdoor is owner-signed truth).

HONESTY CONTRACT (mirrors glazing_candidates.py): this module only PROPOSES a class as
ADVISORY metadata. It NEVER writes indoor/floor into a piece and NEVER decides the class for
a piece the owner drew INSIDE the room. A proposal is a REVIEW candidate, never a FAIL, never
an auto-applied label. Only an owner sign (placement_gate.resolve_zone) may set a piece's zone.

THE RULE (numbered; every element DEFAULTS to indoor, a non-indoor class is proposed only past
a corroboration gate that can NEVER demote an owner-contained piece):

  0. FACADE DATUM + CORROBORATION (once per room). The datum is PINNED to the room's own
     south (min-y) outline edge y_s -- owner-drawn, never the inferred glazing line (the
     glazing line only CORROBORATES that the edge is glass, it never moves the datum). The
     edge is an authorised facade iff (a) a STRONG horizontal glazing candidate lies just
     south of y_s spanning the edge, AND (b) the edge is OPEN -- no long thick wall runs along
     it. A solid-south-wall room fails (b) and ABSTAINS: no proposals at all.
  1. INDOOR IMMUNITY (the false-positive firewall, decided by owner containment ONLY,
     independent of the datum). A centroid inside the outline (dilated indoor_pad) OR a
     footprint >= indoor_area_frac inside -> indoor, emit nothing. No datum/corroboration
     error can ever demote a contained piece -- that is exactly what keeps a chair drawn hard
     against the glass from being mislabelled outdoor.
  2. BEYOND-ROOM GATE (only if corroborated AND not indoor-immune): the footprint must be
     >= out_area_frac on the facade-exterior (south) side. Belt-and-suspenders vs a lapping piece.
  3. BELOW vs OUTDOOR: centroid south of the datum beyond y_below_margin -> below_grade
     (False,False); else -> outdoor_same_floor (False,True). The humble DEFAULT beyond the
     glass is below_grade, not terrace -- the terrace mislabel WAS the wound, and there is no
     floor-2 parapet loop enclosing the south exterior. curve (organic planting ink), a glazing
     line between the element and the datum, and "never placed in any scene-graph" only
     STRENGTHEN confidence; they are never gates.
  4. SIZE/NOISE gate (reused from placement_gate.unplaced_clusters): a south component below
     min_ext_mm / min_area_m2 gets no proposal -- a dimension tick south of the facade cannot
     masquerade as a below_grade element (the CubiCasa "fence counted as living area" failure).

Class -> benchmark_reader (indoor, floor):
  indoor -> (True,True); outdoor_same_floor -> (False,True); below_grade -> (False,False).
A silent / unknown element maps to (True,True) to match benchmark_reader._score_binary's
"silence = ordinary this-floor-indoor" semantics.
"""
import math

SCHEMA = "interior-ai/zone-flag@0.1"

INDOOR = "indoor"
OUTDOOR = "outdoor_same_floor"
BELOW = "below_grade"
ZONES = (INDOOR, OUTDOOR, BELOW)
ZONE_TO_FLAGS = {INDOOR: (True, True), OUTDOOR: (False, True), BELOW: (False, False)}

DEFAULTS = dict(
    indoor_pad=150.0,          # mm; a centroid within this of the outline still reads indoor
    #                            (wall_thk 100 + draw jitter; the nearest indoor piece is ~585mm in)
    indoor_area_frac=0.5,      # >=50% of a footprint inside the outline -> indoor-immune
    y_below_margin=150.0,      # mm; centroid must be >150mm SOUTH of the datum to count below
    #                            (absorbs facade jitter + calib residual; the two populations are ~1090mm apart)
    out_area_frac=0.7,         # >=70% of the footprint south OR a confidently-below centroid -> beyond-room
    mostly_south_frac=0.9,     # >=90% of the footprint south = FULLY beyond the glass (STRONG gate; a deep
    #                            canopy that laps the glass line falls short of this and is only LOW/MEDIUM)
    facade_search_south=1500.0,# mm; a corroborating glazing line may sit this far south of y_s
    #                            (real slab lip |-1151.6 - 0| = 1151.6; 1500 admits it + its pair, < min room depth)
    facade_overlap_frac=0.5,   # the glazing candidate x-span must cover >=50% of the edge span
    facade_tier_min=3,         # only STRONG glazing candidates (score>=3) corroborate a facade
    facade_wall_tol=120.0,     # mm; collinearity band for "wall runs along the edge" (mirrors check_wall_grid)
    edge_cover_frac=0.6,       # edge is CLOSED (walled) if collinear walls cover >=60% of its span (on the
    #                            UNIONED coverage, so a wall decomposed into ~200mm segments still counts)
    min_ext_mm=250.0,          # reused from placement_gate.UNPLACED_MIN_EXT_MM
    min_area_m2=0.03,          # reused from placement_gate.UNPLACED_MIN_AREA_M2
)


# ---- pure geometry -------------------------------------------------------------------
def _centre(fp):
    return ((fp[0] + fp[2]) / 2.0, (fp[1] + fp[3]) / 2.0)


def point_in_poly(pt, poly):
    """Even-odd ray cast: is pt strictly-ish inside the closed polygon `poly` [[x,y],...]."""
    x, y = pt
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        if (yi > y) != (yj > y):
            xin = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xin:
                inside = not inside
        j = i
    return inside


def _dist_point_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dist_point_to_poly(pt, poly):
    """Min distance from pt to any edge of the polygon (0 if the point lies on an edge)."""
    x, y = pt
    n = len(poly)
    best = float("inf")
    j = n - 1
    for i in range(n):
        d = _dist_point_seg(x, y, poly[j][0], poly[j][1], poly[i][0], poly[i][1])
        if d < best:
            best = d
        j = i
    return best


def _poly_area(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _clip_poly_halfplane(poly, ax, ay, bx, by):
    """Sutherland-Hodgman: keep the part of `poly` on the LEFT of directed edge a->b.
    Exact for a CONVEX clip polygon (the room outlines here are convex rectangles)."""
    out = []
    n = len(poly)
    for i in range(n):
        cx, cy = poly[i]
        px, py = poly[i - 1]
        # cross > 0 => point is left of a->b
        cc = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        cp = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        if cc >= 0:
            if cp < 0:
                out.append(_line_intersect(px, py, cx, cy, ax, ay, bx, by))
            out.append((cx, cy))
        elif cp >= 0:
            out.append(_line_intersect(px, py, cx, cy, ax, ay, bx, by))
    return out


def _line_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return (x1, y1)
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _ccw(poly):
    """Return the polygon wound counter-clockwise (positive signed area)."""
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return poly if s >= 0 else poly[::-1]


def rect_area_frac_inside(fp, outline):
    """Fraction of the axis-aligned footprint rect fp=(x0,y0,x1,y1) whose area falls inside the
    (convex, CCW-normalised) outline polygon. SH-clip the rect by each outline edge, then shoelace."""
    x0, y0, x1, y1 = fp
    rect = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    area = (x1 - x0) * (y1 - y0)
    if area <= 0 or len(outline) < 3:      # a degenerate/empty outline encloses no area (never "all inside")
        return 0.0
    poly = _ccw([(p[0], p[1]) for p in outline])
    clipped = rect
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        clipped = _clip_poly_halfplane(clipped, ax, ay, bx, by)
        if len(clipped) < 3:
            return 0.0
    return min(1.0, _poly_area(clipped) / area)


def rect_frac_south_of(fp, y_s):
    """Fraction of the footprint rect's AREA that lies south of (y < y_s) the datum line.
    Since fp is axis-aligned, area-fraction == the vertical-span fraction."""
    x0, y0, x1, y1 = fp
    h = y1 - y0
    if h <= 0:
        return 0.0
    below = max(0.0, min(y1, y_s) - y0)
    return max(0.0, min(1.0, below / h))


# ---- facade inference ----------------------------------------------------------------
def facade_datum(outline):
    """The room's SOUTH (min-y) outline edge as (y_s, xlo, xhi). v1 detects the south-glazed
    facade (the real, verified case); a room with no south glass never corroborates and abstains."""
    ys = [p[1] for p in outline]
    xs = [p[0] for p in outline]
    return (min(ys), min(xs), max(xs))


def _axis_seg(seg):
    """(x1,y1),(x2,y2) -> ('h', y, xlo, xhi) or ('v', x, ylo, yhi); None if slanted/malformed
    (a hand-edited walls JSON with a None/str coordinate must SKIP, never crash the gate)."""
    try:
        (x1, y1), (x2, y2) = seg[0], seg[1]
    except (TypeError, ValueError, IndexError):
        return None
    if not all(isinstance(v, (int, float)) for v in (x1, y1, x2, y2)):
        return None
    if abs(y1 - y2) <= abs(x1 - x2) and abs(x1 - x2) > 0:
        return ("h", (y1 + y2) / 2.0, min(x1, x2), max(x1, x2))
    if abs(x1 - x2) < abs(y1 - y2):
        return ("v", (x1 + x2) / 2.0, min(y1, y2), max(y1, y2))
    return None


def _span_cover_frac(intervals, lo, hi):
    """Union length of `intervals` clamped to [lo,hi], divided by (hi-lo)."""
    span = hi - lo
    if span <= 0:
        return 0.0
    clam = sorted((max(lo, a), min(hi, b)) for a, b in intervals if min(hi, b) > max(lo, a))
    cov = 0.0
    cur_lo = cur_hi = None
    for a, b in clam:
        if cur_hi is None or a > cur_hi:
            if cur_hi is not None:
                cov += cur_hi - cur_lo
            cur_lo, cur_hi = a, b
        else:
            cur_hi = max(cur_hi, b)
    if cur_hi is not None:
        cov += cur_hi - cur_lo
    return cov / span


def facade_corroborated(y_s, xlo, xhi, glazing_cands, wall_segs, params=None):
    """(ok, evidence). The south edge is an authorised glazed facade iff a STRONG horizontal
    glazing candidate sits just south of y_s spanning the edge (glass present) AND no long thick
    wall runs along the edge (edge OPEN). Returns evidence incl. the corroborating glazing c."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    span = xhi - xlo
    # (a) a strong glazing line, just south of y_s (within search band), covering the edge. Every
    # field is validated (a hand-edited glazing-candidates.json must SKIP a bad entry, never crash).
    glaz_c = None
    for c in glazing_cands or []:
        if not isinstance(c, dict) or c.get("axis") != "h":
            continue
        sc = c.get("score")
        if not isinstance(sc, (int, float)) or sc < p["facade_tier_min"]:
            continue
        cc = c.get("c")
        if not isinstance(cc, (int, float)):
            continue
        if not (y_s - p["facade_search_south"] <= cc <= y_s + p["y_below_margin"]):
            continue
        gs = c.get("span")
        if (not isinstance(gs, (list, tuple)) or len(gs) < 2
                or not isinstance(gs[0], (int, float)) or not isinstance(gs[1], (int, float))):
            continue
        ov = max(0.0, min(xhi, gs[1]) - max(xlo, gs[0]))
        if span > 0 and ov / span >= p["facade_overlap_frac"]:
            # nearest-to-datum wins as the named corroborator (the actual facade line)
            if glaz_c is None or abs(cc - y_s) < abs(glaz_c - y_s):
                glaz_c = cc
    if glaz_c is None:
        return (False, {"corroborated": False, "reason": "no_strong_south_glazing", "glazing_c": None})
    # (b) edge OPEN: reject if collinear walls cover >= edge_cover_frac of the span. The length test
    # is on the UNIONED coverage, NOT each raw segment — the real wall extract decomposes one 4900mm
    # wall into ~200mm pieces, so a per-segment min-length gate would let every walled-south room
    # falsely corroborate. A handful of short corner stubs still union to a small fraction -> open.
    wall_ivs = []
    for s in wall_segs or []:
        a = _axis_seg(s)
        if a is None or a[0] != "h":
            continue
        if abs(a[1] - y_s) <= p["facade_wall_tol"]:
            wall_ivs.append((a[2], a[3]))
    wall_cover = _span_cover_frac(wall_ivs, xlo, xhi)
    if wall_cover >= p["edge_cover_frac"]:
        return (False, {"corroborated": False, "reason": "south_edge_walled",
                        "glazing_c": glaz_c, "wall_cover": round(wall_cover, 2)})
    return (True, {"corroborated": True, "glazing_c": glaz_c, "wall_cover": round(wall_cover, 2)})


def _glazing_between(cy, y_s, glazing_cands, tier_min):
    """A strong horizontal glazing line strictly between the element centroid and the datum
    (glaz_c in (cy, y_s)) = machine evidence the element is truly BEYOND the glass."""
    for c in glazing_cands or []:
        if c.get("axis") == "h" and c.get("score", 0) >= tier_min:
            cc = c.get("c")
            if cc is not None and cy < cc < y_s:
                return True
    return False


# ---- element classifier --------------------------------------------------------------
def classify_element(el, outline, facade, glazing_cands, params=None):
    """Classify ONE element. el = {ref, fp, w, d, area_m2?, curve?, unplaced?}. `facade` is the
    (y_s, xlo, xhi, corroborated, glazing_c) tuple/dict from facade_corroborated. Returns a dict
    {ref, zone, indoor, floor, confidence, alt, signals} or None when the element gets NO proposal
    (indoor-immune, room abstains, size-noise, or not beyond the facade). indoor pieces DO return a
    dict with zone=indoor + emit=False so a caller can prove them; only non-indoor is a REVIEW proposal."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    fp = el["fp"]
    c = _centre(fp)
    w, d = el.get("w"), el.get("d")
    if w is None or d is None:
        w, d = (fp[2] - fp[0]), (fp[3] - fp[1])
    area_m2 = el.get("area_m2")
    if area_m2 is None:
        area_m2 = w * d / 1e6
    curve = bool(el.get("curve"))
    unplaced = bool(el.get("unplaced"))
    y_s = facade["y_s"]

    # (1) INDOOR IMMUNITY -- owner containment only, independent of datum/corroboration
    inside = (point_in_poly(c, outline)
              or dist_point_to_poly(c, outline) <= p["indoor_pad"]
              or rect_area_frac_inside(fp, outline) >= p["indoor_area_frac"])
    if inside:
        return {"ref": el.get("ref"), "zone": INDOOR, "indoor": True, "floor": True,
                "confidence": "STRONG", "alt": None, "emit": False,
                "signals": {"in_room": True, "c_y": round(c[1], 1), "y_s": y_s,
                            "curve": curve, "corroborated": facade.get("corroborated")}}

    # room abstains unless the facade is corroborated
    if not facade.get("corroborated"):
        return None

    # (2) BEYOND-ROOM GATE -- an element is a candidate if it is MAJORITY south OR its centroid is
    # confidently BELOW the datum. The second clause is essential: a DEEP below-grade canopy legitimately
    # laps the glass in plan (top edge north of y_s), so its area-fraction-south can be < out_area_frac
    # even though its centroid sits well south — requiring both would silently drop it (an F3 re-open).
    frac_south = rect_frac_south_of(fp, y_s)
    below = c[1] < (y_s - p["y_below_margin"])
    if not (frac_south >= p["out_area_frac"] or below):
        return None

    # (4) SIZE / NOISE gate (before any proposal)
    if min(w, d) < p["min_ext_mm"] or area_m2 < p["min_area_m2"]:
        return None

    # (3) BELOW vs OUTDOOR + confidence. STRONG is reserved for an UNPLACED cluster (ink the designer
    # did NOT place as furniture) sitting FULLY beyond the glass (>=mostly_south) with organic/glazing
    # evidence — i.e. the garden tree. A PLACED piece proud of the glass (a real bay-window seat / niche
    # projection is geometrically identical to a below-grade object) or an element that only LAPS the
    # glass stays LOW: honestly ambiguous, the exact call the owner-sign arbitrates. curve alone never
    # earns STRONG (an indoor cushion reads curve=True too).
    glaz_between = _glazing_between(c[1], y_s, glazing_cands, p["facade_tier_min"])
    mostly_south = frac_south >= p["mostly_south_frac"]
    if below:
        zone = BELOW
        if unplaced and mostly_south and (curve or glaz_between):
            conf, alt = "STRONG", None
        elif unplaced and (mostly_south or glaz_between):
            conf, alt = "MEDIUM", OUTDOOR
        else:
            conf, alt = "LOW", OUTDOOR       # placed-and-proud, or a lapping blob — owner arbitrates
    else:
        zone, conf, alt = OUTDOOR, "MEDIUM", None
    indoor_f, floor_f = ZONE_TO_FLAGS[zone]
    return {"ref": el.get("ref"), "zone": zone, "indoor": indoor_f, "floor": floor_f,
            "confidence": conf, "alt": alt, "emit": True,
            "signals": {"in_room": False, "c_y": round(c[1], 1), "y_s": y_s,
                        "frac_south": round(frac_south, 2), "curve": curve,
                        "glazing_between": glaz_between, "unplaced": unplaced,
                        "glazing_c": facade.get("glazing_c")}}


def zone_proposals(elements, outline, glazing_cands, wall_segs, params=None):
    """Classify a list of elements against one room. Returns
      {corroborated, facade, proposals:[non-indoor advisory dicts], indoor:[indoor dicts], abstained:bool}.
    `outline` = room.outline_mm (absolute mm, offset already applied by the caller).
    `elements` = [{ref, fp, w, d, area_m2?, curve?, unplaced?}, ...] (fp = renderer-true bbox)."""
    y_s, xlo, xhi = facade_datum(outline)
    ok, ev = facade_corroborated(y_s, xlo, xhi, glazing_cands, wall_segs, params)
    facade = {"y_s": y_s, "xlo": xlo, "xhi": xhi, "corroborated": ok, **ev}
    proposals, indoor = [], []
    for el in elements:
        r = classify_element(el, outline, facade, glazing_cands, params)
        if r is None:
            continue
        (proposals if r.get("emit") else indoor).append(r)
    return {"corroborated": ok, "facade": facade, "proposals": proposals,
            "indoor": indoor, "abstained": not ok}
