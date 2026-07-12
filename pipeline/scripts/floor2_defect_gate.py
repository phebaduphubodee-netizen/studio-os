"""
floor2_defect_gate.py -- the floor-level DEFECT gate the floor2 build never had.

WHY (owner, 2026-07-10): floor2 v4 sits paused because the layout is still wrong and the
owner refuses to chase defects by eye -- that is the machine's job. The existing gates do
not cover this class: placement_gate checks completeness/no-floating/on-ink (2D read vs
sheet), clearance/placement_logic run on single-ROOM specs -- nothing checks the assembled
FLOOR scene-graph for pieces colliding, escaping their room, blocking a doorway, or walls
missing from the build. Every defect the owner caught by eye on v4 is in exactly that hole:
BF14 slat vs BF09-3 wardrobe (real interpenetration), ensuite vanity vs WC, BF09-1 run over
a doorway, and "walls in the model are incomplete". Those four owner catches are this
gate's ANSWER KEY: a version of this gate that does not machine-catch all four is wrong.

TWO-LAYER LAW (unchanged): everything here is GEOMETRY -- overlap depths, containment,
gap spans, stroke coverage. The gate never reads a dimension label, never guesses identity
or intent. Ambiguous findings (a doorway candidate, an intended overlap such as a counter
over a base cabinet) are REVIEW: the owner signs them in defect-review.json and the
signature STICKS across re-runs (same pattern as placement-review.json). FAIL is reserved
for unsigned hard geometry (deep interpenetration, out-of-room, missing built walls).

CHECKS
  C1 collision     pairwise footprint interpenetration across ALL placed pieces (items +
                   builtins + subroom fixtures, rot handled by placement_gate.footprint --
                   the renderer's own math). Touching <= C1_TOUCH_MM is furniture reality;
                   deeper is REVIEW, past C1_FAIL_MM it is FAIL unless signed.
  C2 containment   every piece inside its room/subroom polygon (+wall-thickness slack).
                   A piece assigned to a room but poking out of it is how "vanity in the
                   WC zone" class errors are born.
  C3 doorway       doorways are GAPS (550..1300 mm) in collinear wall runs -- detected from
                   the SAME wall set the build extrudes, plus the fresh sheet ink. A piece
                   covering a gap is REVIEW ("is this a real door?" is the owner's call;
                   the geometry "this run blocks it" is ours). v1.2: candidates are matched
                   against the DECLARED openings (manifest openings_json). Undeclared
                   candidate -> C3_undeclared_doorway REVIEW (a gap the gate would silently
                   excuse in C4b is exactly the flattering hole -- v1.1 read every gap as a
                   legit doorway; owner markup 2026-07-10 round 2 proved one such "doorway"
                   was a WINDOW and another a missing wall+sliding-door). Declared window/
                   glass/railing -> not a passage: no blocked/swing checks (a desk in front
                   of a window is normal). Declared sliding/opening -> blocked check only,
                   no swing (nothing hinges). An opening carrying owner_confirm_pending
                   stays REVIEW until the owner signs its identity.
  C4c envelope     manifest envelope_edges: wall lines OUTSIDE the rectangular room
                   outlines (fins, piers, party runs past outline spans) declared from
                   measured sheet ink after owner catches. Each must be covered by built
                   walls or declared opening rects within PERIM_OFF_MM -- an uncovered run
                   is FAIL (build regression on an owner-caught spot), because C4b's
                   rectangles cannot see these edges at all.
  C4 wall coverage every thick stroke on the sheet (pdf_extract_walls, same calibration)
                   clipped to the build's clip_zones must be covered by a wall the build
                   actually extrudes. build_floor.build_walls keeps a segment only when its
                   MIDPOINT lies in a clip zone -- a long run whose midpoint falls outside
                   vanishes WHOLE from the render (a measured cause of "walls incomplete",
                   not a guess). Each missing run is attributed to its cause:
                   clipped_out (in walls-json, dropped by the midpoint rule) vs absent
                   (never extracted / not in the json). Phantom walls (built but no ink)
                   are REVIEW, with the owner's manual_additions exempted by record.

PROPOSAL-ONLY: the gate emits a machine fix proposal per defect (move vector, trim, wall
segments to add) but NEVER applies one. The owner reviews the numbered overlay + report,
signs or approves; application is a separate explicit step.

    python floor2_defect_gate.py <floor-manifest.json> [--no-pdf]

Outputs (next to the manifest): defect-gate.json, defect-overlay.png, defect-report.md.
defect-review.json (same dir) holds owner signatures; absent = nothing signed.
"""
import hashlib
import json
import math
import os
import sys

try:  # legible Thai on a cp1252 Windows console (same guard as clearance_check)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from placement_gate import footprint

GATE_VERSION = "floor2_defect_gate v1.2"

C1_TOUCH_MM = 10.0     # AABB contact this shallow is drawing/rounding reality, not a defect
C1_FAIL_MM = 40.0      # unsigned interpenetration deeper than this on BOTH axes' min = FAIL
C2_SLACK_MM = 125.0    # room outline slack: wall_thk (100) + drawing tolerance
DOOR_GAP_MM = (550.0, 1300.0)   # single-leaf doorway band
DOOR_FLANK_MM = 250.0  # a gap needs real wall on BOTH sides to be a doorway candidate
DOOR_BAND_MM = 120.0   # wall-band half-thickness for the gap rectangle
DOOR_BLOCK_MM = 100.0  # a piece covering >= this much of the gap span blocks the doorway
WALL_OFF_MM = 60.0     # collinearity: perpendicular offset for two segs to be the same wall
WALL_MISS_MM = 250.0   # an uncovered ink run at least this long counts as a missing wall
PHANTOM_COVER = 0.5    # a built seg with less ink coverage than this fraction is a phantom


# ---- geometry primitives -------------------------------------------------------------------
def _inter_depth(a, b):
    """(ix, iy) interpenetration depths of two AABBs; positive on both = real overlap."""
    ix = min(a[2], b[2]) - max(a[0], b[0])
    iy = min(a[3], b[3]) - max(a[1], b[1])
    return ix, iy


def _is_cardinal(rot):
    return rot is None or abs(float(rot)) % 90.0 in (0.0, 90.0)


def _obb_corners(it, offset=(0, 0)):
    """The piece's TRUE rotated rectangle corners (renderer pivot = centre), for exact
    overlap on diagonal pieces. footprint()'s AABB is deliberately conservative -- correct
    for clearance but it INFLATES a rot-8 tub chair by ~80mm and manufactures collisions
    with a table the owner aimed it around (observed on v4 live: 108mm 'overlap', most of
    it inflation). Cardinal rots keep the AABB fast path (identical there)."""
    w, d = float(it["w"]), float(it["d"])
    cx = float(it["x"]) + offset[0] + w / 2.0
    cy = float(it["y"]) + offset[1] + d / 2.0
    th = math.radians(float(it.get("rot") or 0))
    c, s = math.cos(th), math.sin(th)
    out = []
    for px, py in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        out.append((cx + px * c - py * s, cy + px * s + py * c))
    return out


def _sat_depth(pa, pb):
    """Separating-axis penetration depth of two convex quads; 0.0 when separated.
    Axes = both rects' edge normals; depth = the minimal axis overlap (the true minimal
    translation to separate, for rectangles)."""
    best = float("inf")
    for poly in (pa, pb):
        for i in range(4):
            ex, ey = poly[(i + 1) % 4][0] - poly[i][0], poly[(i + 1) % 4][1] - poly[i][1]
            L = math.hypot(ex, ey)
            if L < 1e-9:
                continue
            nx, ny = -ey / L, ex / L
            a0 = min(x * nx + y * ny for x, y in pa)
            a1 = max(x * nx + y * ny for x, y in pa)
            b0 = min(x * nx + y * ny for x, y in pb)
            b1 = max(x * nx + y * ny for x, y in pb)
            ov = min(a1, b1) - max(a0, b0)
            if ov <= 0:
                return 0.0
            best = min(best, ov)
    return best


def _point_in_poly(x, y, poly):
    """Even-odd rule; poly = [[x,y],...] closed implicitly."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def _dist_to_poly_edge(x, y, poly):
    best = float("inf")
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        best = min(best, math.hypot(x - (ax + t * dx), y - (ay + t * dy)))
    return best


def _piece_boundary_pts(piece, step_mm=150.0):
    """Points along the piece's TRUE rectangle boundary (OBB corners + edge samples).
    Corners alone miss an L-room's notch cutting through a piece's MIDDLE (all 4 corners
    inside, the waist outside -- review 2026-07-10); AABB corners on a rotated piece sit
    OUTSIDE the true shape and would false-FAIL containment."""
    corners = _obb_corners(piece["raw"], piece["off"])
    pts = []
    for i in range(4):
        ax_, ay_ = corners[i]
        bx_, by_ = corners[(i + 1) % 4]
        n = max(1, int(math.hypot(bx_ - ax_, by_ - ay_) / step_mm))
        for k in range(n):
            t = k / n
            pts.append((ax_ + t * (bx_ - ax_), ay_ + t * (by_ - ay_)))
    return pts


def _outside_by(piece, poly):
    """How far (mm) the piece's worst boundary point sits OUTSIDE the polygon."""
    worst = 0.0
    for x, y in _piece_boundary_pts(piece):
        if not _point_in_poly(x, y, poly):
            worst = max(worst, _dist_to_poly_edge(x, y, poly))
    return worst


def _inside_by(piece, poly):
    """How deep (mm) the piece's deepest boundary point sits INSIDE the polygon."""
    worst = 0.0
    for x, y in _piece_boundary_pts(piece):
        if _point_in_poly(x, y, poly):
            worst = max(worst, _dist_to_poly_edge(x, y, poly))
    return worst


def _axis_of(seg, tol=1.0):
    """'h' / 'v' / None(diagonal). seg = [[x1,y1],[x2,y2]]."""
    (x1, y1), (x2, y2) = seg
    if abs(y2 - y1) <= tol and abs(x2 - x1) > tol:
        return "h"
    if abs(x2 - x1) <= tol and abs(y2 - y1) > tol:
        return "v"
    return None


def _seg_aos(seg):
    """(axis, offset, (lo, hi)) for an axis-aligned segment, else None."""
    ax = _axis_of(seg)
    if ax is None:
        return None
    (x1, y1), (x2, y2) = seg
    if ax == "h":
        return "h", (y1 + y2) / 2.0, (min(x1, x2), max(x1, x2))
    return "v", (x1 + x2) / 2.0, (min(y1, y2), max(y1, y2))


def _merge_spans(spans, join_tol=1.0):
    """Union of 1-D spans; spans closer than join_tol merge. Callers pass a MIX of
    tuples and lists (band spans, doorway spans) -- normalize before sorting, or
    python3 refuses to order tuple vs list."""
    out = []
    for lo, hi in sorted((float(s[0]), float(s[1])) for s in spans):
        if out and lo <= out[-1][1] + join_tol:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


def _subtract_spans(base, covers):
    """base span minus union(covers) -> leftover sub-spans."""
    lo, hi = base
    left = [[lo, hi]]
    for clo, chi in _merge_spans(covers):
        nxt = []
        for a, b in left:
            if chi <= a or clo >= b:
                nxt.append([a, b])
                continue
            if clo > a:
                nxt.append([a, clo])
            if chi < b:
                nxt.append([chi, b])
        left = nxt
    return [(a, b) for a, b in left if b - a > 1e-6]


def _clip_seg_to_rect(seg, rect):
    """Axis-aligned-friendly Liang-Barsky clip; returns clipped seg or None."""
    (x1, y1), (x2, y2) = seg
    X0, Y0, X1, Y1 = rect
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - X0), (dx, X1 - x1), (-dy, y1 - Y0), (dy, Y1 - y1)):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return [[x1 + t0 * dx, y1 + t0 * dy], [x1 + t1 * dx, y1 + t1 * dy]]


def _mid_in_zones(seg, zones):
    """build_floor.build_walls' EXACT keep rule: segment midpoint inside any clip zone."""
    if not zones:
        return True
    mx, my = (seg[0][0] + seg[1][0]) / 2.0, (seg[0][1] + seg[1][1]) / 2.0
    return any(z[0] <= mx <= z[2] and z[1] <= my <= z[3] for z in zones)


# ---- scene loading -------------------------------------------------------------------------
def load_pieces(manifest, repo_root):
    """Flatten every placed piece across the floor's scene-graphs.
    Returns (pieces, rooms): pieces = [{room, sub, name, kind, cls, fp, raw}],
    rooms = [{name, poly, pieces_idx}] (subrooms are rooms of their own for containment)."""
    pieces, rooms = [], []
    for fu in manifest.get("furnish", []):
        spec_path = fu["spec"]
        if not os.path.isabs(spec_path):
            spec_path = os.path.join(repo_root, spec_path)
        sg = json.load(open(spec_path, encoding="utf-8"))
        off = tuple(fu.get("offset_mm", (0, 0)))
        rname = fu.get("id") or os.path.basename(spec_path)
        room_poly = (sg.get("room") or {}).get("outline_mm")
        r_idx = len(rooms)
        rooms.append({"name": rname, "poly": room_poly, "pieces_idx": [], "top": True})

        def add(it, cls, sub=None, room_idx=r_idx):
            i = len(pieces)
            pieces.append({"room": rname, "sub": sub, "name": it.get("name") or it.get("bf")
                           or it.get("kind") or f"piece{i}", "kind": it.get("kind"),
                           "cls": cls, "fp": footprint(it, off), "raw": it, "off": off,
                           "room_idx": room_idx})
            rooms[room_idx]["pieces_idx"].append(i)

        for it in sg.get("items", []) or []:
            add(it, "loose")
        for b in sg.get("builtins", []) or []:
            add(b, "builtin")
        for sr in sg.get("subrooms", []) or []:
            s_idx = len(rooms)
            rooms.append({"name": f"{rname}/{sr.get('name')}", "poly": sr.get("outline_mm"),
                          "pieces_idx": [], "top": False})
            for fx in sr.get("fixtures", []) or []:
                add(fx, "fixture", sub=sr.get("name"), room_idx=s_idx)
    return pieces, rooms


# ---- signatures (owner dismissals stick) ---------------------------------------------------
def defect_fp(check, names, coords):
    key = json.dumps([check, sorted(names), [round(c) for c in coords]], ensure_ascii=False)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def load_signatures(gate_dir):
    p = os.path.join(gate_dir, "defect-review.json")
    if not os.path.exists(p):
        return {}
    doc = json.load(open(p, encoding="utf-8"))
    return {s["fingerprint"]: s for s in doc.get("signed", [])
            if s.get("fingerprint") and s.get("by")}


# ---- C1 collision --------------------------------------------------------------------------
def check_collisions(pieces):
    defects = []
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a, b = pieces[i], pieces[j]
            ix, iy = _inter_depth(a["fp"], b["fp"])
            if ix <= 0 or iy <= 0:
                continue
            # depth = the true minimal PUSH-OUT, not the raw axis overlap: under
            # containment (a thin panel speared by furniture) the overlap equals the
            # thin extent (<=10mm reads as a touch) while the real separation move is
            # hundreds of mm -- the axis-overlap prescreen silenced exactly that case
            # (adversarial review 2026-07-10, reproduced: 10mm glass panel, zero records)
            push_x = min(a["fp"][2] - b["fp"][0], b["fp"][2] - a["fp"][0])
            push_y = min(a["fp"][3] - b["fp"][1], b["fp"][3] - a["fp"][1])
            depth = min(push_x, push_y)
            if depth <= C1_TOUCH_MM:
                continue
            if not (_is_cardinal(a["raw"].get("rot")) and _is_cardinal(b["raw"].get("rot"))):
                # diagonal piece(s): the AABB pre-screen over-fires by the rot inflation
                # -- settle with the exact rotated rectangles (SAT). KNOWN LIMIT: SAT's
                # min-axis-overlap saturates at the thin extent under containment, so a
                # DIAGONAL thin panel speared whole is under-graded (cardinal pairs use
                # the push-out metric above and are exact).
                depth = _sat_depth(_obb_corners(a["raw"], a["off"]),
                                   _obb_corners(b["raw"], b["off"]))
                if depth <= C1_TOUCH_MM:
                    continue
            names = [a["name"], b["name"]]
            zone = (max(a["fp"][0], b["fp"][0]), max(a["fp"][1], b["fp"][1]),
                    min(a["fp"][2], b["fp"][2]), min(a["fp"][3], b["fp"][3]))
            # proposal: translate the smaller piece the minimal distance apart. For a
            # diagonal pair the AABB ix/iy overstate the move -- the SAT depth is the
            # true minimal separation, so that is what the proposal quotes.
            small = a if (a["fp"][2] - a["fp"][0]) * (a["fp"][3] - a["fp"][1]) <= \
                         (b["fp"][2] - b["fp"][0]) * (b["fp"][3] - b["fp"][1]) else b
            axis = "x" if push_x <= push_y else "y"
            sgn = -1 if (small["fp"][0] + small["fp"][2]) <= (a["fp"][0] + a["fp"][2]
                        + b["fp"][0] + b["fp"][2]) / 2.0 else 1
            move = depth + C1_TOUCH_MM
            defects.append({
                "check": "C1_collision", "severity": "FAIL" if depth >= C1_FAIL_MM else "REVIEW",
                "names": names, "rooms": sorted({a["room"], b["room"]}),
                "overlap_mm": [round(ix, 1), round(iy, 1)], "depth_mm": round(depth, 1),
                "zone": [round(v, 1) for v in zone],
                "fingerprint": defect_fp("C1", names, zone),
                "proposal": f"ย้าย '{small['name']}' ตามแกน {axis} "
                            f"{'-' if sgn < 0 else '+'}{move:.0f} mm ให้พ้นกัน (ทะลุจริง "
                            f"{depth:.0f} mm; เซ็นยอมรับได้ถ้าตั้งใจซ้อน เช่น ท็อปเคาน์เตอร์)",
            })
    return defects


# ---- C2 containment ------------------------------------------------------------------------
def check_containment(pieces, rooms):
    """Escape (a piece leaving its own room) is FAIL; INTRUSION (a piece of room A deep
    inside a DIFFERENT top-level room B) is REVIEW -- membership-only checking missed a
    piece parked wholly inside the neighbouring room (review 2026-07-10). Subrooms are
    inside their parent by construction and are never intrusion targets of their own
    parent's pieces. The escape fingerprint quantizes outside_mm/100 so an OUTLINE edit
    that changes the escape re-opens a signed defect instead of hiding under it."""
    defects = []
    top_rooms = [r for r in rooms if r.get("top")]
    for r in rooms:
        if not r["poly"]:
            continue
        for i in r["pieces_idx"]:
            p = pieces[i]
            out = _outside_by(p, r["poly"])
            if out > C2_SLACK_MM:
                defects.append({
                    "check": "C2_out_of_room", "severity": "FAIL",
                    "names": [p["name"]], "rooms": [r["name"]],
                    "outside_mm": round(out, 1), "zone": [round(v, 1) for v in p["fp"]],
                    "fingerprint": defect_fp("C2", [p["name"], r["name"],
                                                    f"q{int(out // 100)}"], p["fp"]),
                    "proposal": f"'{p['name']}' โผล่นอก '{r['name']}' {out:.0f} mm -- "
                                f"เลื่อนกลับเข้า outline หรือแก้ outline ถ้าห้องผิด (owner call)",
                })
    for p in pieces:
        for r in top_rooms:
            if not r["poly"] or r["name"].startswith(p["room"]) or \
                    p["room"].startswith(r["name"]):
                continue        # own room / parent-child: not an intrusion target
            inside = _inside_by(p, r["poly"])
            if inside <= C2_SLACK_MM:
                continue
            defects.append({
                "check": "C2_intrudes_other_room", "severity": "REVIEW",
                "names": [p["name"]], "rooms": [p["room"], r["name"]],
                "inside_mm": round(inside, 1), "zone": [round(v, 1) for v in p["fp"]],
                "fingerprint": defect_fp("C2I", [p["name"], r["name"]], p["fp"]),
                "proposal": f"'{p['name']}' (สังกัด '{p['room']}') ล้ำเข้าห้อง "
                            f"'{r['name']}' {inside:.0f} mm -- ตรวจว่าตั้งใจ (เช่น ตู้ทะลุผนัง) "
                            f"หรือวางผิดห้อง",
            })
    return defects


# ---- C3 doorway gaps -----------------------------------------------------------------------
def wall_bands(segs):
    """Group axis-aligned segs into collinear bands: (axis, offset) -> merged spans.
    Binning is ORDER-INDEPENDENT: segs are sorted by offset and clustered by
    consecutive-gap > WALL_OFF_MM (first-key-wins binning was order-dependent -- the
    same wall set in a different json order produced different bands; review 2026-07-10).
    A chain of near-offsets can still span > WALL_OFF_MM total (single-linkage --
    documented, the drawing's double-line faces sit ~100mm apart and stay separate)."""
    items = []
    for s in segs:
        aos = _seg_aos(s)
        if aos is not None:
            items.append(aos)
    items.sort(key=lambda t: (t[0], t[1], t[2]))
    bands = {}
    cur_key, last_off = None, None
    for ax, off, span in items:
        if cur_key is None or cur_key[0] != ax or off - last_off > WALL_OFF_MM:
            cur_key = (ax, off)
            bands[cur_key] = []
        bands[cur_key].append(span)
        last_off = off
    return {k: _merge_spans(v, join_tol=WALL_OFF_MM) for k, v in bands.items()}


def doorway_candidates(segs):
    """Gaps 550..1300mm between collinear wall runs with real flank on both sides.
    Double-lined walls draw TWO parallel faces -> the same physical doorway appears once
    per face band; candidates within 2*DOOR_BAND_MM offset with overlapping gap spans are
    merged into ONE (observed live: every real doorway duplicated, 41 raw candidates)."""
    cands = []
    for (ax, off), spans in wall_bands(segs).items():
        for k in range(len(spans) - 1):
            gap = spans[k + 1][0] - spans[k][1]
            if not (DOOR_GAP_MM[0] <= gap <= DOOR_GAP_MM[1]):
                continue
            if (spans[k][1] - spans[k][0]) < DOOR_FLANK_MM or \
               (spans[k + 1][1] - spans[k + 1][0]) < DOOR_FLANK_MM:
                continue
            lo, hi = spans[k][1], spans[k + 1][0]
            rect = ((lo, off - DOOR_BAND_MM, hi, off + DOOR_BAND_MM) if ax == "h"
                    else (off - DOOR_BAND_MM, lo, off + DOOR_BAND_MM, hi))
            cands.append({"axis": ax, "offset": round(off, 1), "gap_mm": round(gap, 1),
                          "span": [round(lo, 1), round(hi, 1)],
                          "rect": [round(v, 1) for v in rect]})
    merged = []
    for c in sorted(cands, key=lambda c: (c["axis"], c["offset"], c["span"][0])):
        dup = next((m for m in merged if m["axis"] == c["axis"]
                    and abs(m["offset"] - c["offset"]) <= 2 * DOOR_BAND_MM
                    and min(m["span"][1], c["span"][1]) > max(m["span"][0], c["span"][0])),
                   None)
        if dup is None:
            merged.append(c)
        else:  # widen the kept candidate's rect over both faces
            dup["rect"] = [min(dup["rect"][0], c["rect"][0]), min(dup["rect"][1], c["rect"][1]),
                           max(dup["rect"][2], c["rect"][2]), max(dup["rect"][3], c["rect"][3])]
    return merged


def _opening_for(cand_rect, openings):
    """The declared opening (openings_json entry) whose rect overlaps this doorway
    candidate's rect the most, or None. Overlap must be REAL on both axes -- touching
    is not a match (an opening on a far wall must never excuse a gap here; same class
    of hole as the C4b axis-only exclusion, review 2026-07-10)."""
    best = None
    for o in (openings or []):
        r = o.get("rect")
        if not r or len(r) != 4:
            continue
        ix, iy = _inter_depth(cand_rect, [float(v) for v in r])
        if ix > 0 and iy > 0 and (best is None or ix * iy > best[0]):
            best = (ix * iy, o)
    return best[1] if best else None


def check_doorways(pieces, built_segs, fresh_segs=None, zones=None, openings=None):
    """zones = manifest clip_zones: candidates whose rect touches NO zone are dropped
    (counted by the caller via len). The fresh sheet-ink covers the WHOLE page -- without
    the scope filter, 17 of 22 candidates on the real v4 run were out-of-scope rooms,
    inflating the owner-facing count and feeding C4b's exclusion pool (review 2026-07-10).
    openings = declared openings (openings_json): identity comes from the declaration,
    geometry from the gap -- see the C3 v1.2 note in the module docstring."""
    def in_scope(rect):
        if not zones:
            return True
        return any(min(rect[2], z[2]) > max(rect[0], z[0])
                   and min(rect[3], z[3]) > max(rect[1], z[1]) for z in zones)
    cands = [c for c in doorway_candidates(built_segs) if in_scope(c["rect"])]
    for c in doorway_candidates(fresh_segs or []):
        r = c["rect"]
        if not in_scope(r):
            continue
        if not any(_inter_depth(r, m["rect"])[0] > 0 and _inter_depth(r, m["rect"])[1] > 0
                   and m["axis"] == c["axis"] for m in cands):
            c["source"] = "sheet-ink"
            cands.append(c)
    defects = []
    seen_ids = set()
    for c in cands:
        r = c["rect"]
        op = _opening_for(r, openings)
        typ = (op or {}).get("type")
        c["declared"] = (f"{op.get('id', '?')}:{typ}" if op else None)
        if op is None:
            defects.append({
                "check": "C3_undeclared_doorway", "severity": "REVIEW",
                "names": [f"{c['axis']}@{c['offset']}"], "rooms": [],
                "doorway": c, "zone": list(r),
                "fingerprint": defect_fp("C3U", [c["axis"]], r),
                "proposal": f"ช่องกว้าง {c['gap_mm']:.0f} mm ที่ {c['axis']}@{c['offset']} "
                            f"ช่วง {c['span']} ไม่ถูก declare ใน openings-json -- ช่องนี้คืออะไร "
                            f"(ประตู/หน้าต่าง/ช่องเปิด/กำแพงหาย)? declare หรือเซ็น dismiss; "
                            f"ห้ามอ่านความเงียบเป็นประตูจริง (markup รอบ 2 2026-07-10: "
                            f"ช่องแบบนี้เคยเป็นหน้าต่าง 1 จุด กำแพง+บานเลื่อนหาย 1 จุด)",
            })
        elif op.get("owner_confirm_pending") and op.get("id") not in seen_ids:
            seen_ids.add(op.get("id"))
            defects.append({
                "check": "C3_opening_unconfirmed", "severity": "REVIEW",
                "names": [f"{op.get('id', '?')} ({typ})"], "rooms": [],
                "doorway": c, "zone": [float(v) for v in op["rect"]],
                "fingerprint": defect_fp("C3P", [str(op.get("id")), str(typ)],
                                         [float(v) for v in op["rect"]]),
                "proposal": f"opening '{op.get('id')}' declare เป็น {typ} จากหมึกบนแผ่น "
                            f"แต่ยังรอ owner ยืนยัน identity -- ยืนยัน/แก้ type แล้วลบ "
                            f"owner_confirm_pending ออกจาก openings-json",
            })
        if typ in ("window", "glass", "railing"):
            continue   # not a passage: furniture in front is normal (owner 2026-07-10, BF11)
        gap_axis = 0 if c["axis"] == "h" else 1
        gap = c["gap_mm"]
        # swing squares: gap x gap on BOTH sides of the wall band (leaf side unknown --
        # geometry flags, the owner knows the hinge). Declared sliding/opening: no leaf
        # hinges, so no swing square at all.
        swing = typ in (None, "door")
        if c["axis"] == "h":   # gap runs along x; swing squares above/below the band
            sq = [(r[0], r[1] - gap, r[2], r[1]), (r[0], r[3], r[2], r[3] + gap)]
        else:                  # gap runs along y; swing squares left/right of the band
            sq = [(r[0] - gap, r[1], r[0], r[3]), (r[2], r[1], r[2] + gap, r[3])]
        for p in pieces:
            ix, iy = _inter_depth(r, p["fp"])
            along = (ix if gap_axis == 0 else iy) if (ix > 0 and iy > 0) else 0.0
            if along >= DOOR_BLOCK_MM:
                defects.append({
                    "check": "C3_door_blocked", "severity": "REVIEW",
                    "names": [p["name"]], "rooms": [p["room"]],
                    "doorway": c, "covered_mm": round(along, 1), "zone": list(r),
                    "fingerprint": defect_fp("C3", [p["name"]], r),
                    "proposal": f"'{p['name']}' คลุมช่องเปิด {c['gap_mm']:.0f} mm ที่ "
                                f"{c['axis']}@{c['offset']} ช่วง {c['span']} อยู่ {along:.0f} mm -- "
                                f"ตัด run ให้จบก่อนช่อง หรือเลื่อนพ้นช่อง; ถ้าไม่ใช่ประตูจริง เซ็น dismiss",
                })
                continue
            # not covering the gap itself: does it sit in a swing square?
            if not swing:
                continue
            for s in sq:
                sx, sy = _inter_depth(s, p["fp"])
                if sx >= DOOR_BLOCK_MM and sy >= DOOR_BLOCK_MM:
                    defects.append({
                        "check": "C3_swing_obstructed", "severity": "REVIEW",
                        "names": [p["name"]], "rooms": [p["room"]],
                        "doorway": c, "intrusion_mm": [round(sx, 1), round(sy, 1)],
                        "zone": list(s),
                        "fingerprint": defect_fp("C3S", [p["name"]], s),
                        "proposal": f"'{p['name']}' ล้ำวงสวิงประตู {c['gap_mm']:.0f} mm ที่ "
                                    f"{c['axis']}@{c['offset']} ช่วง {c['span']} "
                                    f"({sx:.0f}x{sy:.0f} mm) -- ประตูอาจเปิดชน; ถ้าบานเปิดฝั่งตรงข้าม/"
                                    f"เป็นบานเลื่อน เซ็น dismiss",
                    })
                    break
    return defects, cands


# ---- C4 wall coverage ----------------------------------------------------------------------
def coverage_missing(fresh_segs, built_segs, all_json_segs, zones):
    """Missing = sheet ink (clipped to zones) not covered by any BUILT wall.
    Cause attribution: clipped_out (an unclipped walls-json seg covers it -- the midpoint
    rule dropped it) vs absent (nothing in the json covers it). Returns (missing, stats)."""
    built_b = wall_bands(built_segs)
    json_b = wall_bands(all_json_segs)
    missing = []
    total_ink = covered_ink = 0.0
    for s in fresh_segs:
        clips = []
        for z in (zones or [None]):
            c = _clip_seg_to_rect(s, z) if z else s
            if c is not None:
                clips.append(c)
        for cseg in clips:
            aos = _seg_aos(cseg)
            if aos is None:
                continue
            ax, off, span = aos
            total_ink += span[1] - span[0]
            covers = [sp for (bax, boff), sps in built_b.items() if bax == ax
                      and abs(boff - off) <= WALL_OFF_MM for sp in sps]
            left = _subtract_spans(span, covers)
            covered_ink += (span[1] - span[0]) - sum(b - a for a, b in left)
            for a, b in left:
                if b - a < WALL_MISS_MM:
                    continue
                jcov = [sp for (jax, joff), sps in json_b.items() if jax == ax
                        and abs(joff - off) <= WALL_OFF_MM for sp in sps]
                in_json = sum(min(b, hi) - max(a, lo) for lo, hi in jcov
                              if min(b, hi) > max(a, lo)) >= 0.5 * (b - a)
                rect = ((a, off - WALL_OFF_MM, b, off + WALL_OFF_MM) if ax == "h"
                        else (off - WALL_OFF_MM, a, off + WALL_OFF_MM, b))
                missing.append({"axis": ax, "offset": round(off, 1),
                                "span": [round(a, 1), round(b, 1)],
                                "len_mm": round(b - a, 1),
                                "cause": "clipped_out(midpoint-rule)" if in_json else
                                         "absent(not-in-walls-json)",
                                "rect": [round(v, 1) for v in rect]})
    # merge collinear-adjacent missing runs so one wall reads as ONE defect
    merged = []
    for m in sorted(missing, key=lambda m: (m["axis"], m["offset"], m["span"][0])):
        if merged and merged[-1]["axis"] == m["axis"] \
                and abs(merged[-1]["offset"] - m["offset"]) <= WALL_OFF_MM \
                and m["span"][0] <= merged[-1]["span"][1] + WALL_OFF_MM \
                and merged[-1]["cause"] == m["cause"]:
            merged[-1]["span"][1] = max(merged[-1]["span"][1], m["span"][1])
            merged[-1]["len_mm"] = round(merged[-1]["span"][1] - merged[-1]["span"][0], 1)
            r0, m0 = merged[-1]["rect"], m["rect"]
            merged[-1]["rect"] = [min(r0[0], m0[0]), min(r0[1], m0[1]),
                                  max(r0[2], m0[2]), max(r0[3], m0[3])]
        else:
            merged.append(m)
    stats = {"ink_mm": round(total_ink, 1), "covered_mm": round(covered_ink, 1),
             "coverage": round(covered_ink / total_ink, 4) if total_ink else None,
             "missing_runs": len(merged),
             "missing_mm": round(sum(m["len_mm"] for m in merged), 1)}
    return merged, stats


def check_walls(manifest, repo_root, use_pdf=True):
    """C4 wiring: built set = walls-json segs kept by build_floor's OWN midpoint rule;
    fresh set = re-extracted thick strokes (skippable with --no-pdf -> UNWIRED, counted)."""
    wj_path = manifest["walls_json"]
    if not os.path.isabs(wj_path):
        wj_path = os.path.join(repo_root, wj_path)
    wj = json.load(open(wj_path, encoding="utf-8"))
    all_segs = [s for s in wj["segments"] if _seg_aos(s) is not None]
    zones = manifest.get("clip_zones")
    built = [s for s in all_segs if _mid_in_zones(s, zones)]
    manual = []
    ma = wj.get("manual_additions")
    if isinstance(ma, dict):
        manual = [s for s in (ma.get("segments") or []) if _seg_aos(s) is not None]
    if not use_pdf:
        return built, None, [], {"skipped": "pdf lane disabled (--no-pdf) -- C4 UNWIRED",
                                 "built_segs": len(built)}, []
    import pdf_extract_walls as PW
    pdf = wj.get("source_pdf") or manifest.get("source_pdf")
    cand = [pdf, os.path.join(repo_root, "projects/PRJ-2026-002_c001-house/00_intake/raw-local", pdf)]
    pdf_path = next((p for p in cand if p and os.path.exists(p)), None)
    if pdf_path is None:
        return built, None, [], {"skipped": f"source pdf not found: {pdf} -- C4 UNWIRED",
                                 "built_segs": len(built)}, []
    scale = wj["scale_mm_per_pt"]
    x0, y0 = wj["origin_pt"]
    fresh = [s for s in PW.extract(pdf_path, wj.get("page", manifest.get("page", 1)),
                                   scale, x0, y0) if _seg_aos(s) is not None]
    missing, stats = coverage_missing(fresh, built, all_segs, zones)
    stats["built_segs"] = len(built)
    stats["fresh_segs"] = len(fresh)
    # phantom: built wall with no ink support (manual additions exempt by record)
    fresh_b = wall_bands(fresh)
    man_keys = {json.dumps([round(v, 1) for p in s for v in p]) for s in manual}
    phantoms = []
    for s in built:
        if json.dumps([round(v, 1) for p in s for v in p]) in man_keys:
            continue
        ax, off, span = _seg_aos(s)
        if span[1] - span[0] < WALL_MISS_MM:
            continue
        covers = [sp for (fax, foff), sps in fresh_b.items() if fax == ax
                  and abs(foff - off) <= WALL_OFF_MM for sp in sps]
        cov = (span[1] - span[0]) - sum(b - a for a, b in _subtract_spans(span, covers))
        if cov < PHANTOM_COVER * (span[1] - span[0]):
            phantoms.append({"seg": s, "covered_frac": round(cov / (span[1] - span[0]), 2)})
    return built, fresh, missing, stats, phantoms


# ---- C4b room-perimeter coverage (the NON-circular "walls incomplete" detector) -------------
PERIM_OFF_MM = 160.0    # outline-to-wall-face tolerance: outline is nominal, faces sit +-~100
PERIM_MISS_MM = 400.0   # an unwalled outline run at least this long is worth the owner's eye


def check_room_perimeter(rooms, built_segs, doorways):
    """Every edge of every room/subroom outline (OWNER-confirmed geometry -- an input
    INDEPENDENT of the wall extractor, unlike C4a which compares the extractor to itself)
    must be covered by a built wall band within PERIM_OFF_MM, doorway gaps excluded.
    An uncovered run is where the rendered model visibly has no wall on a room edge --
    the exact thing the owner reports as 'walls incomplete'. REVIEW, not FAIL: a run can
    be a legitimate wide opening (walk-in bay mouths) or glass -- the owner signs those
    ONCE and they stay signed."""
    bands = wall_bands(built_segs)
    # doorway exemptions carry (axis, RAW offset, span): the exclusion below compares the
    # offset, not just the axis -- axis-only matching let sheet-ink doorways 12.7m away
    # (out-of-scope rooms) silently excuse in-scope unwalled edges (adversarial review
    # 2026-07-10, reproduced live: 9.3m / 45% of real unwalled edge suppressed -- the
    # flattering hole's 6th per-lane recurrence, caught pre-delivery)
    door_list = [(c["axis"], float(c["offset"]),
                  (c["rect"][0], c["rect"][2]) if c["axis"] == "h"
                  else (c["rect"][1], c["rect"][3])) for c in doorways]
    defects = []
    for r in rooms:
        poly = r["poly"]
        if not poly:
            continue
        n = len(poly)
        for i in range(n):
            seg = [list(poly[i]), list(poly[(i + 1) % n])]
            aos = _seg_aos(seg)
            if aos is None:      # diagonal outline edge: not checkable against axis bands
                continue
            ax, off, span = aos
            if span[1] - span[0] < PERIM_MISS_MM:
                continue
            covers = [sp for (bax, boff), sps in bands.items() if bax == ax
                      and abs(boff - off) <= PERIM_OFF_MM for sp in sps]
            covers += [sp for (dax, doff, sp) in door_list if dax == ax
                       and abs(doff - off) <= PERIM_OFF_MM + DOOR_BAND_MM]
            for a, b in _subtract_spans(span, covers):
                if b - a < PERIM_MISS_MM:
                    continue
                rect = ((a, off - PERIM_OFF_MM, b, off + PERIM_OFF_MM) if ax == "h"
                        else (off - PERIM_OFF_MM, a, off + PERIM_OFF_MM, b))
                defects.append({
                    "check": "C4b_room_edge_unwalled", "severity": "REVIEW",
                    "names": [r["name"]], "rooms": [r["name"]],
                    "edge": {"axis": ax, "offset": round(off, 1),
                             "span": [round(a, 1), round(b, 1)],
                             "len_mm": round(b - a, 1)},
                    "zone": [round(v, 1) for v in rect],
                    "fingerprint": defect_fp("C4b", [r["name"], ax], rect),
                    "proposal": f"ขอบห้อง '{r['name']}' ด้าน {ax}@{off:.0f} ช่วง "
                                f"[{a:.0f},{b:.0f}] ({b - a:.0f} mm) ไม่มีกำแพงในโมเดล -- "
                                f"ถ้าเป็นช่องเปิด/กระจกจริง เซ็น dismiss ครั้งเดียวจบ; "
                                f"ถ้าไม่ใช่ = กำแพงหายจาก build",
                })
    return defects


def check_envelope_edges(edges, built_segs, openings):
    """C4c: wall lines the rectangular room outlines CANNOT see (fins into the room,
    piers, party runs past an outline span) -- declared in the manifest as
    envelope_edges: [{axis, offset, span, room?, note?}], every entry measured from
    sheet ink after an owner catch (markup round 2, 2026-07-10: the fin-end pier glass
    and the SE party-corner were exactly such holes; C4b never looked there). Coverage =
    built wall bands within PERIM_OFF_MM of the offset, plus declared opening rects
    whose thin-axis midline sits within the same tolerance (a glass panel or window IS
    the envelope there). An uncovered run >= PERIM_MISS_MM is FAIL, not REVIEW: these
    edges exist because the owner already caught them once -- regressing one is never
    ambiguous."""
    bands = wall_bands(built_segs)
    defects = []
    for e in (edges or []):
        ax, off = e["axis"], float(e["offset"])
        span = (float(e["span"][0]), float(e["span"][1]))
        covers = [sp for (bax, boff), sps in bands.items() if bax == ax
                  and abs(boff - off) <= PERIM_OFF_MM for sp in sps]
        for o in (openings or []):
            r = o.get("rect")
            if not r or len(r) != 4:
                continue
            x0, y0, x1, y1 = (float(v) for v in r)
            if ax == "h" and abs((y0 + y1) / 2.0 - off) <= PERIM_OFF_MM:
                covers.append((min(x0, x1), max(x0, x1)))
            elif ax == "v" and abs((x0 + x1) / 2.0 - off) <= PERIM_OFF_MM:
                covers.append((min(y0, y1), max(y0, y1)))
        for a, b in _subtract_spans(span, covers):
            if b - a < PERIM_MISS_MM:
                continue
            rect = ((a, off - PERIM_OFF_MM, b, off + PERIM_OFF_MM) if ax == "h"
                    else (off - PERIM_OFF_MM, a, off + PERIM_OFF_MM, b))
            label = e.get("note") or f"{ax}@{off:.0f}"
            defects.append({
                "check": "C4c_envelope_edge_open", "severity": "FAIL",
                "names": [label], "rooms": [e.get("room", "")],
                "edge": {"axis": ax, "offset": round(off, 1),
                         "span": [round(a, 1), round(b, 1)], "len_mm": round(b - a, 1)},
                "zone": [round(v, 1) for v in rect],
                "fingerprint": defect_fp("C4c", [label, ax], rect),
                "proposal": f"envelope edge '{label}' ({ax}@{off:.0f}) ช่วง [{a:.0f},{b:.0f}] "
                            f"({b - a:.0f} mm) ไม่มีกำแพง/opening ปิดในโมเดล -- ขอบนี้ owner "
                            f"เคยจับแล้วครั้งหนึ่ง: เติม segment/opening กลับ หรือแก้ "
                            f"envelope_edges ถ้าแนวเปลี่ยนโดยเจตนา",
            })
    return defects


# ---- answer key (owner catches -> machine catches, owner-visible) ---------------------------
def evaluate_answer_key(defects, key_entries):
    """The owner's eye-catches are the gate's acceptance test, and the mapping must be
    VISIBLE in the report, not asserted in a docstring (review 2026-07-10). Entries live
    in the manifest as defect_answer_key: [{catch, expect: present|absent, check,
    names_any, zone_within?}]. A 'present' catch with no matching defect = MISS (the gate
    lost a known defect -> the run itself FAILS); an 'absent' catch matching = REAPPEARED
    (FAIL). zone_within [x0,y0,x1,y1] scopes the match to defects whose zone overlaps it
    -- without it, an 'absent' entry on a check that also fires elsewhere (e.g. another
    signed C4b edge across the floor) would false-REAPPEAR, and a 'present' entry could
    ride on an unrelated flag (markup round 2, 2026-07-10)."""
    def zoverlap(d, zw):
        z = d.get("zone")
        if not z or len(z) != 4:
            return False
        ix, iy = _inter_depth([float(v) for v in z], [float(v) for v in zw])
        return ix > 0 and iy > 0
    rows = []
    for e in (key_entries or []):
        matches = [d for d in defects
                   if d["check"].startswith(e.get("check", ""))
                   and (not e.get("names_any")
                        or any(n in " ".join(d["names"]) for n in e["names_any"]))
                   and (not e.get("zone_within") or zoverlap(d, e["zone_within"]))]
        if e.get("expect", "present") == "present":
            status = "CAUGHT" if matches else "MISS"
        else:
            status = "REAPPEARED" if matches else "RESOLVED-ABSENT"
        rows.append({"catch": e.get("catch"), "expect": e.get("expect", "present"),
                     "status": status,
                     "fingerprints": [d["fingerprint"] for d in matches]})
    return rows


# ---- assembly ------------------------------------------------------------------------------
def run_gate(manifest_path, use_pdf=True):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "..", ".."))
    man = json.load(open(manifest_path, encoding="utf-8"))
    gate_dir = os.path.dirname(os.path.abspath(manifest_path))
    pieces, rooms = load_pieces(man, repo_root)
    signatures = load_signatures(gate_dir)

    openings = []
    op_path = man.get("openings_json")
    if op_path:
        op_abs = op_path if os.path.isabs(op_path) else os.path.join(repo_root, op_path)
        if os.path.exists(op_abs):
            openings = json.load(open(op_abs, encoding="utf-8")).get("openings", [])

    defects = []
    defects += check_collisions(pieces)
    defects += check_containment(pieces, rooms)
    built, fresh, missing, wstats, phantoms = check_walls(man, repo_root, use_pdf=use_pdf)
    d3, door_cands = check_doorways(pieces, built, fresh, zones=man.get("clip_zones"),
                                    openings=openings)
    defects += d3
    defects += check_room_perimeter(rooms, built, door_cands)
    defects += check_envelope_edges(man.get("envelope_edges"), built, openings)
    for m in missing:
        defects.append({
            "check": "C4_missing_wall",
            "severity": "FAIL" if m["cause"].startswith("clipped_out") else "REVIEW",
            "names": [f"wall {m['axis']}@{m['offset']}"], "rooms": [],
            "zone": m["rect"], "detail": m,
            "fingerprint": defect_fp("C4", [m["cause"]], m["rect"]),
            "proposal": (f"กำแพง {m['axis']}@{m['offset']} ช่วง {m['span']} ({m['len_mm']:.0f} mm) "
                         + ("อยู่ใน walls-json แต่ถูกกฎ midpoint ตัดทิ้งทั้งเส้น -- ขยาย clip_zone "
                            "หรือ split เส้นให้ midpoint เข้า zone"
                            if m["cause"].startswith("clipped_out") else
                            "ไม่อยู่ใน walls-json -- เพิ่ม segment นี้ (พิกัดพร้อมใช้ใน detail.rect) "
                            "หลัง owner ยืนยันว่าเป็นกำแพง/กระจกจริง")),
        })
    for ph in phantoms:
        defects.append({
            "check": "C4_phantom_wall", "severity": "REVIEW",
            "names": [f"built-wall {ph['seg']}"], "rooms": [],
            "zone": [ph["seg"][0][0], ph["seg"][0][1], ph["seg"][1][0], ph["seg"][1][1]],
            "detail": ph, "fingerprint": defect_fp("C4P", ["phantom"],
                                                   ph["seg"][0] + ph["seg"][1]),
            "proposal": "กำแพงนี้ถูก build แต่ไม่มีหมึกหนารองรับบน sheet -- ตรวจว่าจริงหรือหลงเหลือ",
        })

    for d in defects:
        sig = signatures.get(d["fingerprint"])
        if sig:
            d["signed"] = {"by": sig["by"], "date": sig.get("date"),
                           "reason": sig.get("reason")}
            d["severity"] = "SIGNED"
    unsigned_fail = [d for d in defects if d["severity"] == "FAIL"]
    review = [d for d in defects if d["severity"] == "REVIEW"]
    answer_key = evaluate_answer_key(defects, man.get("defect_answer_key"))
    key_broken = [r for r in answer_key if r["status"] in ("MISS", "REAPPEARED")]
    verdict = "FAIL" if (unsigned_fail or key_broken) else ("REVIEW" if review else "PASS")

    out = {
        "gate": GATE_VERSION, "verdict": verdict, "manifest": os.path.basename(manifest_path),
        "counts": {"pieces": len(pieces), "rooms": len(rooms), "defects": len(defects),
                   "fail": len(unsigned_fail), "review": len(review),
                   "signed": sum(1 for d in defects if d["severity"] == "SIGNED")},
        "answer_key": answer_key,
        "wall_coverage": wstats, "doorway_candidates": door_cands,
        "openings": {"declared": len(openings),
                     "pending_confirm": [o.get("id") for o in openings
                                         if o.get("owner_confirm_pending")]},
        "envelope_edges": {"declared": len(man.get("envelope_edges") or []),
                           "open_runs": sum(1 for d in defects
                                            if d["check"] == "C4c_envelope_edge_open")},
        "defects": sorted(defects, key=lambda d: ({"FAIL": 0, "REVIEW": 1, "SIGNED": 2}
                                                  [d["severity"]], d["check"])),
        "note": "PROPOSAL-ONLY: gate เสนอวิธีแก้ ไม่แตะ scene-graph; เซ็น dismiss ใน "
                "defect-review.json ด้วย fingerprint; FAIL ที่ไม่เซ็น = บล็อก build",
    }
    return out, pieces, rooms, built, fresh, missing


# ---- overlay -------------------------------------------------------------------------------
def render_overlay(out, pieces, rooms, built, missing, png_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.collections import LineCollection
    thai = None
    for cand in (r"C:\Windows\Fonts\tahoma.ttf",):
        if os.path.exists(cand):
            thai = font_manager.FontProperties(fname=cand)
    fig, ax = plt.subplots(figsize=(16, 12), dpi=110)
    if built:
        ax.add_collection(LineCollection([[tuple(a), tuple(b)] for a, b in built],
                                         colors="#9a9a9a", linewidths=1.4))
    for r in rooms:
        if r["poly"]:
            xs = [p[0] for p in r["poly"]] + [r["poly"][0][0]]
            ys = [p[1] for p in r["poly"]] + [r["poly"][0][1]]
            ax.plot(xs, ys, color="#3b7a3b", lw=0.8, ls=":")
    for p in pieces:
        x0, y0, x1, y1 = p["fp"]
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                                   edgecolor="#4a6fb5", lw=0.9))
    for k, d in enumerate(out["defects"], 1):
        z = d.get("zone")
        if not z:
            continue
        col = {"FAIL": "#d7191c", "REVIEW": "#ff8c00", "SIGNED": "#888888"}[d["severity"]]
        ax.add_patch(plt.Rectangle((z[0], z[1]), max(z[2] - z[0], 40), max(z[3] - z[1], 40),
                                   fill=False, edgecolor=col, lw=2.2))
        ax.annotate(str(k), (z[0], z[3]), color=col, fontsize=11, weight="bold")
    lines = [f"{k}. [{d['severity']}] {d['check']}: {', '.join(d['names'])[:60]}"
             for k, d in enumerate(out["defects"], 1)]
    ax.text(1.01, 0.99, "\n".join(lines[:40]), transform=ax.transAxes, va="top",
            fontsize=8, fontproperties=thai)
    ax.set_aspect("equal")
    ax.autoscale()
    ax.set_title(f"floor2 defect gate -- verdict {out['verdict']} "
                 f"(FAIL {out['counts']['fail']} / REVIEW {out['counts']['review']} / "
                 f"signed {out['counts']['signed']})")
    plt.tight_layout()
    plt.savefig(png_path, bbox_inches="tight")
    plt.close(fig)


def render_report(out):
    L = [f"# floor2 defect gate -- {out['verdict']}",
         "", f"- {out['gate']} on {out['manifest']}; pieces {out['counts']['pieces']}, "
         f"defects {out['counts']['defects']} (FAIL {out['counts']['fail']} / REVIEW "
         f"{out['counts']['review']} / signed {out['counts']['signed']})"]
    ak = out.get("answer_key") or []
    if ak:
        L.append("")
        L.append("## answer key -- สิ่งที่ owner เคยจับด้วยตา เทียบกับที่ gate จับ")
        for r in ak:
            mark = {"CAUGHT": "จับได้", "MISS": "**หลุด -- gate ผิดเอง**",
                    "RESOLVED-ABSENT": "ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)",
                    "REAPPEARED": "**โผล่กลับมา**"}[r["status"]]
            fps = (" -> " + ", ".join(f"`{f}`" for f in r["fingerprints"])) \
                if r["fingerprints"] else ""
            L.append(f"- {r['catch']}: {mark}{fps}")
    ws = out.get("wall_coverage") or {}
    if ws.get("coverage") is not None:
        L.append(f"- extraction-loss check C4a (วัดเฉพาะ clip/merge loss -- fresh ink มาจาก "
                 f"extractor ตัวเดียวกับ walls-json จึง CIRCULAR โดยธรรมชาติ, ห้ามอ่านเป็น "
                 f"'กำแพงครบ'): missing {ws['missing_runs']} runs / {ws['missing_mm']:.0f} mm; "
                 f"ตัววัด 'กำแพงไม่ครบ' ที่อิสระจริงคือ C4b ด้านบน")
    elif ws.get("skipped"):
        L.append(f"- wall coverage: {ws['skipped']}")
    cands = out.get("doorway_candidates", [])
    n_decl = sum(1 for c in cands if c.get("declared"))
    L.append(f"- doorway candidates in scope: {len(cands)} (declare แล้ว {n_decl}, "
             f"ไม่ declare = REVIEW C3_undeclared_doorway ทุกช่อง -- v1.1 เคยอ่านทุกช่องเป็น"
             f"ประตูจริงโดยปริยาย ซึ่ง markup รอบ 2 พิสูจน์ว่าผิด); ข้อจำกัดที่เปิดเผย: C3 เห็นเฉพาะ"
             f"ช่องบานเดี่ยว 550-1300mm -- บานคู่/บานเลื่อนกว้างกว่านั้นจะโผล่เป็นขอบไม่มีกำแพงใน C4b แทน")
    ops = out.get("openings") or {}
    if ops:
        pend = ops.get("pending_confirm") or []
        L.append(f"- openings declared: {ops.get('declared', 0)}"
                 + (f" (รอ owner ยืนยัน identity: {', '.join(pend)})" if pend else ""))
    ee = out.get("envelope_edges") or {}
    if ee.get("declared"):
        L.append(f"- envelope edges (C4c, แนวที่ C4b มองไม่เห็น): declared {ee['declared']}, "
                 f"เปิดโหว่ {ee['open_runs']} run")
    L.append("")
    for k, d in enumerate(out["defects"], 1):
        L.append(f"{k}. **[{d['severity']}] {d['check']}** -- {', '.join(d['names'])}")
        L.append(f"   - {d['proposal']}")
        L.append(f"   - fingerprint `{d['fingerprint']}`"
                 + (f" (signed: {d['signed']['by']})" if d.get("signed") else ""))
    L += ["", out["note"], "", f"engine: {out['gate']}"]
    return "\n".join(L)


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    use_pdf = "--no-pdf" not in argv
    manifest_path = argv[1]
    out, pieces, rooms, built, fresh, missing = run_gate(manifest_path, use_pdf=use_pdf)
    gate_dir = os.path.dirname(os.path.abspath(manifest_path))
    with open(os.path.join(gate_dir, "defect-gate.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    report = render_report(out)
    with open(os.path.join(gate_dir, "defect-report.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    try:
        render_overlay(out, pieces, rooms, built, missing,
                       os.path.join(gate_dir, "defect-overlay.png"))
    except Exception as e:   # a failed PICTURE must not hide a scored gate run
        print(f"overlay failed: {type(e).__name__}: {e}")
    print(report)
    print(f"\nwrote {gate_dir}\\defect-gate.json + defect-report.md + defect-overlay.png")


if __name__ == "__main__":
    main(sys.argv)
