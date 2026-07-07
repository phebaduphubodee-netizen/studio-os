"""
floorplancad_adapter.py -- FloorPlanCAD v2 SVG annotations -> backwards-benchmark gt.json
(the first corpus adapter for benchmark_reader.py; research record
docs/research/2026-07-06-paired-2d3d-backlearn.md SS3 "vector-semantics tier").

    python floorplancad_adapter.py <in.svg> <out.json>
    python floorplancad_adapter.py --batch <svg-dir> <out-dir>   # + manifest.jsonl + summary.md
    python floorplancad_adapter.py --selftest <out-dir>          # score gt-vs-gt (must be perfect)

WHY THIS CORPUS FIRST: FloorPlanCAD is the only large benchmark that TYPES sliding doors
and names curtain wall / railing as classes -- exactly the F4 thin-line wound (the sliding
glass door invisible to the thick-stroke wall extractor). Its SVGs are vector primitives
like our PDF extractor's input, so scores transfer.

WHAT THE RAW ANNOTATION LOOKS LIKE (verified on the real corpus, not from papers):
  - each primitive carries semantic-id (int) + instance-id (int; -1 = stuff/uncountable)
  - viewBox is normalised to 100x100 per sheet -> REAL scale varies per file; dimension
    TEXTS (unannotated ink) carry mm values, so scale is recovered per file by matching
    dim text values to parallel nearby dim-line lengths (mode-cluster of ratios).
  - CAD layer names survive (inkscape:label) -- kept as provenance on every record.

RAW ID MAP -- DATA-GROUNDED 2026-07-06 by a 300-file survey of test-00 (layer-name
cross-tab + per-instance geometry), because the raw SVG numbering is NOT the ordering
published in downstream repos (CADTransformer's anno_list puts wall=33; the raw SVGs put
wall=1, curtain wall=2, and swap sink/air-conditioner relative to that list):
  survey evidence highlights: 1 on WALL/wall layers 100% instance=-1; 2 on A-GLAZ/nbbj
  curtain-wall layers; 21 on kongtiao/HVAC layers (air conditioner, NOT sink); 23 on
  LVTRY/kitchen-bath layers at 50% arc share (sink); 18 instances median 2.1m x 0.56m
  (wardrobe depth); 30/31/32 on STAIR/EVTR/escalator layers; 33 railing; 34 CINEMA_CHAIR;
  35 parking. Ids 6/7/8 (folding/revolving/rolling door) never appeared in the sample --
  published long-tail classes -- their names are INFERRED BY ORDER between confirmed
  neighbours and flagged `order_inferred` so a corpus run reports if they ever occur.

HONESTY CONTRACT (matches benchmark_reader): FloorPlanCAD carries NO rotation, indoor or
floor-membership GT -> emitted elements have no rot/indoor/floor keys, so F2/F3/F5 score
UNWIRED on this corpus -- never fabricated. Unknown semantic-ids, transform-bearing
primitives (rare, ~1 per file), unparseable paths and zero-extent (degenerate) instances
are COUNTED AND REPORTED, never silently dropped. curtain wall + railing go to a
`glazing_lines` channel (not yet scored by benchmark_reader -- staged for the F4
room-closure metric; extra keys are ignored by score_pair, verified by --selftest).

SCRUTINY 2026-07-06 (12 confirmed findings folded back in): true arc extents via W3C
F.6.5 sampling (chord-only bboxes under-covered sinks/toilets up to 66% and made
two-half-arc circles zero-area); calibration hardened against tick-fragment/sheet-border
mispairing and overprinted duplicate texts (support now counted in DISTINCT dim lines;
candidate lines must be >=2.5x font-size long); zero-extent elements dropped + counted
(IoU can never match a zero-area box, even to itself); benchmark_reader now REFUSES
mixed-unit pairs and requires an explicit open_tol for non-mm units.
"""
import glob
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

ADAPTER_VERSION = "floorplancad_adapter v1.1"
SVG_NS = "{http://www.w3.org/2000/svg}"
INK_NS = "{http://www.inkscape.org/namespaces/inkscape}"

# ---- raw semantic-id map (see header for grounding) --------------------------------------
RAW_CLASSES = {
    1: "wall", 2: "curtain_wall",
    3: "single_door", 4: "double_door", 5: "sliding_door",
    6: "folding_door", 7: "revolving_door", 8: "rolling_door",   # order-inferred (unseen)
    9: "window", 10: "bay_window", 11: "blind_window", 12: "opening_symbol",
    13: "sofa", 14: "bed", 15: "chair", 16: "table", 17: "tv_cabinet",
    18: "wardrobe", 19: "cabinet", 20: "gas_stove", 21: "air_conditioner",
    22: "refrigerator", 23: "sink", 24: "bath", 25: "bathtub", 26: "washing_machine",
    27: "squat_toilet", 28: "urinal", 29: "toilet", 30: "stairs", 31: "elevator",
    32: "escalator", 33: "railing", 34: "row_chairs", 35: "parking_spot",
}
ORDER_INFERRED_IDS = {6, 7, 8}
OPENING_TYPE = {                       # benchmark F4 subtype vocabulary: door|sliding|window|opening
    "single_door": "door", "double_door": "door", "folding_door": "door",
    "revolving_door": "door", "rolling_door": "door", "sliding_door": "sliding",
    "window": "window", "bay_window": "window", "blind_window": "window",
    "opening_symbol": "opening",
}
GLAZING_KINDS = {"curtain_wall", "railing"}    # F4 thin-line channel (stuff -> segments)
COUNT_ONLY_KINDS = {"wall", "row_chairs", "parking_spot"}   # stuff: counted, not emitted

# calibration acceptance band: sheet is 100 units, so scale s mm/unit puts the sheet at
# 100*s mm; real sheets span ~3 m (single room) to ~500 m (mall/site) -> s in [30, 5000]
SCALE_MIN, SCALE_MAX = 30.0, 5000.0
CALIB_MIN_SUPPORT = 3          # accepted dim matches needed before a scale is trusted
CALIB_MIN_FRACTION = 0.4       # ...and they must be >=40% of all candidate ratios
DIM_VALUE_MIN, DIM_VALUE_MAX = 100.0, 99999.0    # mm values dims plausibly carry
DIM_ANGLE_TOL = 6.0            # deg: text parallel to its dim line
DIM_DIST_FACTOR = 3.0          # max perpendicular text-anchor..line distance, x font-size

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|" + _NUM.pattern)


# ---- SVG path walking --------------------------------------------------------------------
def _tokens(d):
    for m in _CMD.finditer(d or ""):
        yield m.group(1) if m.group(1) else float(m.group(0))


_ARITY = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "A": 7}
_ARC_SAMPLES = 16      # sag error <= r*(1-cos(360/16/2 deg)) ~= 1.9% of radius, worst case


def _arc_extent_points(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2):
    """Points along an SVG elliptical arc (W3C SVG 1.1 F.6.5 endpoint->centre
    conversion), sampled at <=_ARC_SAMPLES steps across the ACTUAL swept angle.
    The first shipped adapter kept only the chord endpoints -- scrutiny 2026-07-06
    proved that under-covers arc-heavy symbols (sinks/toilets/urinals) by up to 66%
    and collapses circles drawn as two half-arcs to zero area. Sampling bounds the
    bbox error at ~2% of radius, deterministically. Degenerate radii -> chord ([])."""
    rx, ry = abs(rx), abs(ry)
    if rx < 1e-12 or ry < 1e-12 or (x1 == x2 and y1 == y2):
        return []
    phi = math.radians(phi_deg % 360.0)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p = cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1.0:                      # radii too small: scale up per spec
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    if den < 1e-12:
        return []
    coef = math.sqrt(max(0.0, num / den))
    if bool(large) == bool(sweep):
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2.0
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2.0
    th1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    th2 = math.atan2((-y1p - cyp) / ry, (-x1p - cxp) / rx)
    dth = th2 - th1
    if sweep and dth < 0:
        dth += 2 * math.pi
    elif not sweep and dth > 0:
        dth -= 2 * math.pi
    pts = []
    for k in range(1, _ARC_SAMPLES):
        t = th1 + dth * k / _ARC_SAMPLES
        pts.append((cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp,
                    cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp))
    return pts


def walk_path(d):
    """Yield (point, flag) for every point a path touches, in order; flag is 'move'
    (pen-up reposition), 'draw' (drawn-to endpoint) or 'ctrl' (extent-only point:
    Bezier control points -- the curve stays inside its hull, so bbox over-covers
    slightly -- and sampled arc-sweep points from _arc_extent_points, error <=~2% of
    radius). Arc radii/flags are consumed positionally, never misread as coordinates
    (the classic bbox corruption when naively pairing numbers); flags must be
    whitespace/comma-separated (the compact '0110'-style flag syntax never occurs in
    this corpus -- verified 0/73k paths). Z closes the subpath with a 'draw' back to
    its start. Malformed trailing args are dropped. [] for empty/unparseable d."""
    out = []
    toks = list(_tokens(d))
    i, cmd = 0, None
    cx = cy = sx = sy = 0.0
    while i < len(toks):
        t = toks[i]
        if isinstance(t, str):
            cmd = t
            i += 1
            if cmd in ("Z", "z"):
                if (cx, cy) != (sx, sy):
                    out.append(((sx, sy), "draw"))
                cx, cy = sx, sy
            continue
        if cmd is None:
            break
        C = cmd.upper()
        n = _ARITY.get(C)
        if n is None or i + n > len(toks) or any(isinstance(v, str) for v in toks[i:i + n]):
            break                      # malformed tail: stop, keep what we have
        args = toks[i:i + n]
        i += n
        rel = cmd.islower()
        if C == "M":
            cx = args[0] + (cx if rel else 0)
            cy = args[1] + (cy if rel else 0)
            sx, sy = cx, cy
            out.append(((cx, cy), "move"))
            cmd = "l" if rel else "L"      # implicit lineto after moveto
        elif C == "L" or C == "T":
            cx = args[0] + (cx if rel else 0)
            cy = args[1] + (cy if rel else 0)
            out.append(((cx, cy), "draw"))
        elif C == "H":
            cx = args[0] + (cx if rel else 0)
            out.append(((cx, cy), "draw"))
        elif C == "V":
            cy = args[0] + (cy if rel else 0)
            out.append(((cx, cy), "draw"))
        elif C in ("C", "S", "Q"):
            ox, oy = (cx, cy) if rel else (0.0, 0.0)
            pts = [(args[k] + ox, args[k + 1] + oy) for k in range(0, n, 2)]
            for p in pts[:-1]:
                out.append((p, "ctrl"))
            cx, cy = pts[-1]
            out.append(((cx, cy), "draw"))
        elif C == "A":
            ex = args[5] + (cx if rel else 0)
            ey = args[6] + (cy if rel else 0)
            for p in _arc_extent_points(cx, cy, args[0], args[1], args[2],
                                        args[3], args[4], ex, ey):
                out.append((p, "ctrl"))    # true swept extent; segments still get chord
            cx, cy = ex, ey
            out.append(((cx, cy), "draw"))
    return out


def path_segments(d):
    """Straight drawn segments ((x1,y1),(x2,y2)) of a path; curves/arcs contribute the
    chord from the last pen position to their endpoint. Moves break the chain; control
    points are extent-only and never anchor a segment. For the glazing channel."""
    segs, pen = [], None
    for (pt, flag) in walk_path(d):
        if flag == "move":
            pen = pt
        elif flag == "draw":
            if pen is not None and pt != pen:
                segs.append((pen, pt))
            pen = pt
    return segs


def shape_points(el, tag):
    """Extent points for non-path drawing primitives."""
    g = el.get
    try:
        if tag == "circle":
            cx, cy, r = float(g("cx") or 0), float(g("cy") or 0), float(g("r") or 0)
            return [(cx - r, cy - r), (cx + r, cy + r)]
        if tag == "ellipse":
            cx, cy = float(g("cx") or 0), float(g("cy") or 0)
            rx, ry = float(g("rx") or 0), float(g("ry") or 0)
            return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
        if tag == "rect":
            x, y = float(g("x") or 0), float(g("y") or 0)
            w, h = float(g("width") or 0), float(g("height") or 0)
            return [(x, y), (x + w, y + h)]
        if tag == "line":
            return [(float(g("x1") or 0), float(g("y1") or 0)),
                    (float(g("x2") or 0), float(g("y2") or 0))]
        if tag in ("polyline", "polygon"):
            vals = [float(v) for v in _NUM.findall(g("points") or "")]
            return list(zip(vals[::2], vals[1::2]))
    except (TypeError, ValueError):
        return []
    return []


# ---- per-file parse ----------------------------------------------------------------------
DRAW_TAGS = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}


def parse_svg(svg_path):
    """One pass over the SVG -> raw pools. Nothing is interpreted yet; every skip is
    counted so the gt.json can report it."""
    tree = ET.parse(svg_path)
    root = tree.getroot()
    inst_pool = defaultdict(lambda: {"pts": [], "layers": Counter(), "n_prims": 0,
                                     "n_text": 0})
    glazing, walls, dim_texts, dim_segs = [], [], [], []
    counts = {"stuff": Counter(), "unannotated": Counter(), "unknown_ids": Counter(),
              "transforms_skipped": 0, "malformed_prims": 0, "mixed_instances": 0,
              "instanced_stuff": 0}
    inst_seen_sem = {}
    containers = [(root, "<root>")]
    containers += [(g, g.get(INK_NS + "label") or g.get("id") or "?")
                   for g in root.iter(SVG_NS + "g")]
    for gnode, layer in containers:
        for el in gnode:
            if el.tag == SVG_NS + "g":
                continue               # nested group: visited via its own container entry
            tag = el.tag.replace(SVG_NS, "")
            sem_raw = el.get("semantic-id")
            if tag == "text":
                if sem_raw is None:
                    _collect_dim_text(el, layer, dim_texts)
                    counts["unannotated"]["text"] += 1
                else:
                    try:
                        key = (int(sem_raw), el.get("instance-id"))
                        inst_pool[key]["n_text"] += 1    # anchor NOT bbox'd (ink only)
                    except ValueError:
                        counts["unknown_ids"][sem_raw] += 1
                continue
            if tag not in DRAW_TAGS:
                continue
            if el.get("transform"):
                counts["transforms_skipped"] += 1     # ~1/file; skipping beats mis-placing
                continue
            if sem_raw is None:
                counts["unannotated"][tag] += 1
                if tag == "path":
                    dim_segs.extend(path_segments(el.get("d")))
                elif tag == "line":
                    p = shape_points(el, tag)
                    if len(p) == 2:
                        dim_segs.append((p[0], p[1]))
                continue
            try:
                sem = int(sem_raw)
            except ValueError:
                counts["unknown_ids"][sem_raw] += 1
                continue
            kind = RAW_CLASSES.get(sem)
            if kind is None:
                counts["unknown_ids"][str(sem)] += 1
                continue
            inst = el.get("instance-id")
            no_inst = inst is None or inst == "-1"
            if kind in GLAZING_KINDS:
                segs = (path_segments(el.get("d")) if tag == "path"
                        else _shape_segs(el, tag))
                for (a, b) in segs:
                    glazing.append({"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1],
                                    "kind": kind, "layer": layer})
                continue
            if kind == "wall":
                # oracle wall channel: export geometry for BOTH stuff (-1) and
                # instanced wall prims (excluding instanced walls leaves oracle gaps);
                # counters preserved exactly as the count-only branch produced them.
                # Path/line-family prims only: rect/circle/ellipse walls yield no
                # segments through _shape_segs (same limitation as the glazing branch)
                for (a, b) in (path_segments(el.get("d")) if tag == "path"
                               else _shape_segs(el, tag)):
                    walls.append({"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1],
                                  "layer": layer})
                counts["stuff"][kind] += 1
                if not no_inst:
                    counts["instanced_stuff"] += 1
                continue
            if no_inst or kind in COUNT_ONLY_KINDS:
                counts["stuff"][kind] += 1
                if not no_inst:        # instanced wall/row_chairs/parking: never an element
                    counts["instanced_stuff"] += 1
                continue
            pts = walk_path(el.get("d")) if tag == "path" else None
            pool_pts = ([p for p, _m in pts] if pts is not None
                        else shape_points(el, tag))
            if not pool_pts:
                counts["malformed_prims"] += 1
                continue
            if inst in inst_seen_sem and inst_seen_sem[inst] != sem:
                counts["mixed_instances"] += 1
            inst_seen_sem.setdefault(inst, sem)
            row = inst_pool[(sem, inst)]
            row["pts"].extend(pool_pts)
            row["layers"][layer] += 1
            row["n_prims"] += 1
    return inst_pool, glazing, walls, dim_texts, dim_segs, counts


def _shape_segs(el, tag):
    p = shape_points(el, tag)
    if tag == "line" and len(p) == 2:
        return [(p[0], p[1])]
    if tag in ("polyline", "polygon") and len(p) >= 2:
        return list(zip(p, p[1:]))
    return []            # circles/ellipses in a glazing class: no straight segment


_ROT = re.compile(r"rotate\(\s*([-+]?\d+\.?\d*)")


def _collect_dim_text(el, layer, out):
    txt = "".join(el.itertext()).strip().replace(",", "")
    if not re.fullmatch(r"\d+(?:\.\d+)?", txt):
        return
    val = float(txt)
    if not (DIM_VALUE_MIN <= val <= DIM_VALUE_MAX):
        return
    try:
        x, y = float(el.get("x") or 0), float(el.get("y") or 0)
    except (TypeError, ValueError):
        return
    m = _ROT.search(el.get("transform") or "")
    ang = float(m.group(1)) if m else 0.0
    try:
        fs = float(el.get("font-size") or 2.0)
    except (TypeError, ValueError):
        fs = 2.0
    out.append({"value": val, "x": x, "y": y, "angle": ang, "fs": fs, "layer": layer})


# ---- per-file scale calibration ----------------------------------------------------------
def _seg_angle(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def _ang_diff(u, v):
    d = abs(u - v) % 180.0
    return min(d, 180.0 - d)


DIM_SEG_MIN_FS = 2.5      # a dim line is at least this many font-sizes long: kills the
                          # tick/stub fragments the nearest-line rule otherwise locks onto


def calibrate(dim_texts, dim_segs):
    """mm-per-unit from dimension texts vs parallel nearby unannotated segments.
    Hardened after scrutiny proved 6 confidently-wrong accepted scales (2.4x-37.8x):
      - overprinted duplicate texts (same value at the same anchor) collapse to ONE text;
      - a candidate line must be parallel (<=DIM_ANGLE_TOL), within DIM_DIST_FACTOR*
        font-size, span the anchor's projection (25% margin) AND be >=DIM_SEG_MIN_FS
        font-sizes long -- CAD tick fragments (~0.8u) fail that, real dim lines pass;
      - per-candidate ratio must already sit in [SCALE_MIN, SCALE_MAX];
      - the winning +-5% mode cluster must cover >=CALIB_MIN_SUPPORT *DISTINCT* segments
        (N texts leaning on one sheet-border line = one measurement, not N).
    Wrong pairings scatter, true dim pairs concentrate. Returns (scale|None, report)."""
    seen, texts = set(), []
    for t in dim_texts:
        k = (t["value"], round(t["x"], 2), round(t["y"], 2))
        if k not in seen:
            seen.add(k)
            texts.append(t)
    votes = []                         # (ratio, distinct-segment key)
    for t in texts:
        ta = t["angle"] % 180.0
        best = None                    # nearest qualifying segment only: 1 vote per text
        for (a, b) in dim_segs:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L <= 1e-9 or L < DIM_SEG_MIN_FS * t["fs"]:
                continue
            if _ang_diff(_seg_angle(a, b), ta) > DIM_ANGLE_TOL:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            dx, dy = t["x"] - a[0], t["y"] - a[1]
            proj = dx * ux + dy * uy
            if proj < -0.25 * L or proj > 1.25 * L:
                continue
            perp = abs(dx * -uy + dy * ux)
            if perp > DIM_DIST_FACTOR * t["fs"]:
                continue
            r = t["value"] / L
            if not (SCALE_MIN <= r <= SCALE_MAX):
                continue
            if best is None or perp < best[0]:
                key = tuple(sorted((tuple(round(v, 4) for v in a),
                                    tuple(round(v, 4) for v in b))))
                best = (perp, r, key)
        if best is not None:
            votes.append((best[1], best[2]))
    report = {"n_dim_texts": len(dim_texts), "n_texts_unique": len(texts),
              "n_ratio_candidates": len(votes), "support": 0,
              "distinct_segments": 0, "spread_pct": None}
    if not votes:
        return None, report
    votes.sort(key=lambda v: v[0])
    ratios = [v[0] for v in votes]
    best_lo = best_hi = 0
    lo = 0
    for hi in range(len(ratios)):      # largest window with hi/lo ratio <= 1.10 (+-5%)
        while ratios[hi] > ratios[lo] * 1.10:
            lo += 1
        if hi - lo > best_hi - best_lo:
            best_lo, best_hi = lo, hi
    cluster = ratios[best_lo:best_hi + 1]
    distinct = len({votes[i][1] for i in range(best_lo, best_hi + 1)})
    scale = cluster[len(cluster) // 2]
    report["support"] = len(cluster)
    report["distinct_segments"] = distinct
    report["spread_pct"] = round(100.0 * (cluster[-1] - cluster[0]) / scale, 2)
    if (distinct < CALIB_MIN_SUPPORT or len(cluster) < CALIB_MIN_FRACTION * len(votes)
            or not (SCALE_MIN <= scale <= SCALE_MAX)):
        return None, report
    return scale, report


# ---- assembly ----------------------------------------------------------------------------
def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


DOOR_MM_MIN, DOOR_MM_MAX = 500.0, 2500.0   # a median single/sliding door outside this
                                           # band means the ACCEPTED scale is wrong


def convert(svg_path, split=None):
    """SVG -> gt document (dict). Coordinates in mm when calibrated (units='mm'),
    otherwise raw svg units (units='svg-unit', scale null) -- flagged, never guessed.
    Second anchor: if the accepted scale puts the file's median single/sliding door
    outside [DOOR_MM_MIN, DOOR_MM_MAX] the calibration is REVOKED (drops to svg units,
    reason recorded in calib.rejected_by) -- scrutiny found a residual family of
    confident tick-pairing scales that only a physical cross-check catches."""
    inst_pool, glazing, walls, dim_texts, dim_segs, counts = parse_svg(svg_path)
    scale, calib = calibrate(dim_texts, dim_segs)

    def assemble(sc):
        s = sc if sc is not None else 1.0
        elements, openings = [], []
        order_seen = Counter()
        degenerate = []
        for (sem, inst), row in sorted(inst_pool.items(),
                                       key=lambda kv: (kv[0][0], str(kv[0][1]))):
            if not row["pts"]:
                continue               # text-only instance: nothing locatable
            kind = RAW_CLASSES[sem]
            if sem in ORDER_INFERRED_IDS:
                order_seen[kind] += 1
            x, y, w, d = _bbox(row["pts"])
            rec = {"id": f"s{sem:02d}_i{inst}",
                   "x": round(x * s, 1), "y": round(y * s, 1),
                   "w": round(w * s, 1), "d": round(d * s, 1),
                   "layer": row["layers"].most_common(1)[0][0],
                   "n_prims": row["n_prims"]}
            if kind in OPENING_TYPE:
                rec["type"] = OPENING_TYPE[kind]
                rec["subtype_raw"] = kind
                openings.append(rec)  # zero-extent ok here: openings match by centre
            elif rec["w"] == 0 or rec["d"] == 0:
                # a zero-area box can never IoU-match, even against itself (selftest
                # proved it on real sinks drawn as pure line-work) -- drop AND report
                degenerate.append(rec["id"])
            else:
                rec["kind"] = kind
                elements.append(rec)
        doors = sorted(max(o["w"], o["d"]) for o in openings
                       if o["subtype_raw"] in ("single_door", "sliding_door"))
        door_med = doors[len(doors) // 2] if doors else None
        return elements, openings, order_seen, degenerate, door_med

    elements, openings, order_inferred_seen, degenerate_dropped, door_med = assemble(scale)
    if (scale is not None and door_med is not None
            and not (DOOR_MM_MIN <= door_med <= DOOR_MM_MAX)):
        calib = dict(calib, rejected_by=f"door-band: median door {round(door_med)}mm "
                                        f"outside [{DOOR_MM_MIN:.0f},{DOOR_MM_MAX:.0f}]")
        scale = None
        elements, openings, order_inferred_seen, degenerate_dropped, door_med = assemble(None)
    s = scale if scale is not None else 1.0
    return {
        "meta": {
            "source": "floorplancad-v2", "adapter": ADAPTER_VERSION,
            "file": os.path.basename(svg_path), "split": split,
            "units": "mm" if scale is not None else "svg-unit",
            "scale_mm_per_unit": scale, "calib": calib,
            "stuff_counts": dict(counts["stuff"]),
            "unannotated": dict(counts["unannotated"]),
            "unknown_ids": dict(counts["unknown_ids"]),
            "transforms_skipped": counts["transforms_skipped"],
            "malformed_prims": counts["malformed_prims"],
            "mixed_instances": counts["mixed_instances"],
            "instanced_stuff": counts["instanced_stuff"],
            "degenerate_dropped": degenerate_dropped,
            "order_inferred_ids_seen": dict(order_inferred_seen),
            "door_mm_median": (round(door_med, 0)
                               if door_med is not None and scale is not None else None),
        },
        "elements": elements,
        "openings": openings,
        "glazing_lines": [
            {**g, "x1": round(g["x1"] * s, 1), "y1": round(g["y1"] * s, 1),
             "x2": round(g["x2"] * s, 1), "y2": round(g["y2"] * s, 1)}
            for g in glazing
        ],
        "wall_lines": [
            {**w, "x1": round(w["x1"] * s, 1), "y1": round(w["y1"] * s, 1),
             "x2": round(w["x2"] * s, 1), "y2": round(w["y2"] * s, 1)}
            for w in walls
        ],
    }


# ---- batch + selftest ---------------------------------------------------------------------
def run_batch(svg_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(svg_dir, "*.svg")))
    if not files:
        raise SystemExit(f"no .svg under {svg_dir}")
    split = os.path.basename(os.path.normpath(svg_dir))
    man_path = os.path.join(out_dir, "manifest.jsonl")
    kind_totals, subtype_totals = Counter(), Counter()
    n_cal = n_fail = n_degen = 0
    door_meds, unknown_all = [], Counter()
    inferred_all = Counter()
    with open(man_path, "w", encoding="utf-8") as man:
        for k, fp in enumerate(files):
            base = os.path.splitext(os.path.basename(fp))[0]
            try:
                doc = convert(fp, split=split)
            except Exception as e:     # one broken file must cost ONE manifest row,
                n_fail += 1            # never the rest of the corpus run
                man.write(json.dumps({"file": base, "ok": False,
                                      "error": f"{type(e).__name__}: {e}"}) + "\n")
                continue
            out_fp = os.path.join(out_dir, base + ".gt.json")
            with open(out_fp, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, ensure_ascii=False)
            m = doc["meta"]
            for e in doc["elements"]:
                kind_totals[e["kind"]] += 1
            for o in doc["openings"]:
                subtype_totals[o["subtype_raw"]] += 1
            unknown_all.update(m["unknown_ids"])
            inferred_all.update(m["order_inferred_ids_seen"])
            n_degen += len(m["degenerate_dropped"])
            if m["scale_mm_per_unit"] is not None:
                n_cal += 1
                if m["door_mm_median"] is not None:
                    door_meds.append(m["door_mm_median"])
            man.write(json.dumps({
                "file": base, "ok": True, "units": m["units"],
                "scale_mm_per_unit": m["scale_mm_per_unit"],
                "calib_support": m["calib"]["support"],
                "n_elements": len(doc["elements"]), "n_openings": len(doc["openings"]),
                "n_glazing": len(doc["glazing_lines"]),
                "n_wall": len(doc["wall_lines"]),
                "transforms_skipped": m["transforms_skipped"],
                "degenerate": len(m["degenerate_dropped"]),
                "unknown_ids": m["unknown_ids"],
                "door_mm_median": m["door_mm_median"]}) + "\n")
            if (k + 1) % 500 == 0:
                print(f"  {k + 1}/{len(files)}")
    door_meds.sort()
    summary = [
        "# FloorPlanCAD -> gt.json batch summary", "",
        f"- source dir: `{svg_dir}`  files: {len(files)}  parse-failed: {n_fail}",
        f"- calibrated to mm: {n_cal}/{len(files) - n_fail} "
        f"({100.0 * n_cal / max(1, len(files) - n_fail):.1f}%) -- uncalibrated files keep "
        "svg units (units flag) and must not join mm-tolerance scoring",
        f"- corpus median of per-file median door width: "
        f"{door_meds[len(door_meds) // 2] if door_meds else None} mm "
        "(sanity anchor for the id map: plausible band 600-2500)",
        f"- element instances by kind: {dict(kind_totals.most_common())}",
        f"- openings by raw subtype: {dict(subtype_totals.most_common())}",
        f"- degenerate (zero-extent) instances dropped + reported per-file: {n_degen}",
        f"- unknown semantic-ids: {dict(unknown_all) or 'none'}",
        f"- order-inferred ids seen (folding/revolving/rolling door -- names unverified "
        f"if nonzero, eyeball the paired PNG before trusting): {dict(inferred_all) or 'none'}",
        "", f"adapter: {ADAPTER_VERSION}",
    ]
    sum_path = os.path.join(out_dir, "summary.md")
    with open(sum_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary) + "\n")
    print("\n".join(summary))
    print(f"\nwrote {man_path}\nwrote {sum_path}")


def run_selftest(out_dir):
    """Score every gt against ITSELF: detection/F1/F4 must be perfect, F2/F3/F5 must be
    UNWIRED (no rot/indoor/floor in this corpus). Anything else = adapter emits a schema
    benchmark_reader misreads -> fail loudly here, not mid-benchmark."""
    import benchmark_reader as B
    files = sorted(glob.glob(os.path.join(out_dir, "*.gt.json")))
    if not files:
        raise SystemExit(f"no *.gt.json under {out_dir}")
    bad = 0
    cards = []
    for fp in files:
        doc = json.load(open(fp, encoding="utf-8"))
        # svg-unit files: benchmark refuses to guess a tolerance for non-mm units.
        # gt-vs-gt centre distances are 0 so ANY tol passes; 3.0 units documents the
        # corpus-typical equivalent of 300mm (median scale ~100 mm/unit).
        tol = None if doc["meta"]["units"] == "mm" else 3.0
        card = B.score_pair(doc, doc, open_tol=tol)
        cards.append(card)
        problems = []
        for metric in ("detection", "F1_identity", "F4_openings"):
            v = card[metric]["verdict"]
            n_has = (card[metric].get("n_gt", card[metric].get("n", 0)) or 0)
            if n_has and v != "PASS":
                problems.append(f"{metric}={v}")
        for metric in ("F2_facing", "F3_indoor", "F5_floor"):
            if card[metric]["verdict"] != "UNWIRED":
                problems.append(f"{metric}={card[metric]['verdict']} (expected UNWIRED)")
        if any(card["malformed"].values()):
            problems.append(f"malformed={card['malformed']}")
        if problems:
            bad += 1
            print(f"SELFTEST-FAIL {os.path.basename(fp)}: {'; '.join(problems)}")
    agg = B.aggregate(cards)
    print(f"selftest: {len(files)} files, {bad} failures; aggregate: "
          f"det recall={agg['detection']['recall']}, F1 acc={agg['F1_identity']['accuracy']}, "
          f"F4 recall={agg['F4_openings']['recall']}")
    if bad:
        raise SystemExit(f"{bad} selftest failures")
    print("selftest PASS: adapter output is benchmark_reader-clean")


def main(argv):
    if len(argv) >= 3 and argv[1] == "--batch":
        run_batch(argv[2], argv[3] if len(argv) > 3 else argv[2] + "-gt")
    elif len(argv) >= 2 and argv[1] == "--selftest":
        run_selftest(argv[2])
    elif len(argv) >= 3:
        doc = convert(argv[1])
        with open(argv[2], "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        m = doc["meta"]
        print(f"{m['file']}: {len(doc['elements'])} elements, {len(doc['openings'])} "
              f"openings, {len(doc['glazing_lines'])} glazing segs, units={m['units']}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
