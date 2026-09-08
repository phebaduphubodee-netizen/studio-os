"""
wall_detect.py -- BLIND wall detection from plan ink: the pdf_extract_walls doctrine
(classify wall strokes on the SHEET side, then keep them out of the furniture ink) ported
to the geometry-only SVG lane, plus the double-line DRAWING convention that makes walls
observable on the synth sheet in the first place.

WHY: wall_aware_lane + symbol_unit_lane (2026-07-10) put the whole wall tier at
ORACLE-WALLS -- the barrier consumed gt['wall_lines'] because the oriented synth sheet
carries NO wall ink at all (svg_plan_reader.read_ink parses geometry only; the PDF lane's
0.6 pt thick-stroke gate "has NO signal here", svg_plan_reader line 22). A wall that is
never drawn cannot be detected blind. This module supplies both halves:

  DRAW  (append_wall_ink): gt wall centerlines -> TWO parallel <line> strokes offset
        +/-WALL_T_MM/2 along the normal -- the standard architectural double-line wall,
        the same visual convention pdf_extract_walls keys on for real sheets (there via
        stroke thickness; here, with a width-blind ink parser, via the double line).
        Sheet-side only: gt wall_lines reach the DRAWING exactly like gt rot reaches the
        F2 back-strips (f2_facing_lane precedent, disclosed closed loop).
  DETECT (detect_walls): ink segments -> wall-classified segment indices + merged
        centerlines, GEOMETRY ONLY. A wall is a pair of near-parallel, near-co-terminous
        lines at a face gap in [GAP_MIN_MM, GAP_MAX_MM]:
          - closed-rectangle outline members (furniture) are excluded up front via the
            caller-supplied ring index (f2_facing_lane._ring_member_idx doctrine -- a
            rect's opposite edges are otherwise a legal parallel pair at 150-250mm);
          - the co-terminous screen (LEN_RATIO_MIN + ALIGN_TOL_MM both ends) is what
            keeps F2 back-strips alive: a strip near a wall face is parallel in-window,
            but its ends never align with the wall line's ends;
          - everything rejected/accepted is COUNTED (stats), and the lane measures the
            misclassification cost downstream (strips eaten, true wall segs missed) --
            detector errors are the point of the blind tier, never asserted away.

CLOSED-LOOP HONESTY (disclose wherever quoted): the thresholds are tuned to OUR drawn
convention (T=100mm, exact offsets). On production sheets the constants need re-deriving
per sheet family -- what transfers is the DOCTRINE (classify wall strokes geometrically,
mask them out of symbol ink, use them as a split barrier), which is exactly how the PDF
lane already treats thick strokes. Detection quality vs gt is MEASURED per scene
(coverage_vs_gt), never assumed perfect.

Pure geometry + stdlib: no reader imports, no numpy -- unit-testable in isolation.
"""
import math

WALL_T_MM = 100.0          # drawn wall thickness: faces at centerline +/- T/2
GAP_MIN_MM = 50.0          # accepted face-to-face window; the lower bound rejects
GAP_MAX_MM = 250.0         #   collinear/duplicate strokes, the upper bound spans common
                           #   real wall thicknesses (interior ~100, exterior ~200)
ANGLE_TOL_DEG = 5.0        # near-parallel tolerance (bucketing prefilter)
GAP_DEV_MM = 15.0          # max gap DIVERGENCE across the pair's run: a double line is
                           #   drawn by constant offset, so |gap(end1) - gap(end2)| ~ 0;
                           #   a 5deg-tilted end-aligned stroke diverges L*tan(5deg)
                           #   (85mm at 1m) and must not pass (adversarial review)
LEN_RATIO_MIN = 0.85       # a double line is drawn by OFFSET: both faces near-equal
ALIGN_TOL_MM = 5.0         # ...and CO-TERMINOUS at both ends. Tight by doctrine: a double
                           #   line is drawn by offsetting one centerline, so its faces
                           #   align exactly (here and in CAD tools alike), while two
                           #   NEIGHBOURS' back-strips at a wall-like gap are offset by
                           #   their placement (observed 12.7mm, scene_00002 pilot) --
                           #   60mm let that pair through and ate both strips
MIN_LINE_MM = 80.0         # ignore shorter strokes (specks). Micro gt walls BELOW this
                           #   exist in the corpus (pilot: 11/30 scenes) and are
                           #   undetectable BY CONSTRUCTION -- counted separately
                           #   (walls_zero_micro, fn_micro), never lumped with misses
MERGE_LAT_MM = 20.0        # centerline merge: same line within this lateral offset
MERGE_GAP_MM = 30.0        # ...and touching/overlapping within this longitudinal gap
_GRID_MM = 400.0           # midpoint spatial hash cell; a co-terminous pair's midpoints
                           #   sit within sqrt(ALIGN^2+GAP_MAX^2) < 300mm of each other


# ---- drawing (sheet side) -----------------------------------------------------------------
def wall_face_lines(wall_lines, t=WALL_T_MM):
    """gt centerline dicts -> list of (faceA, faceB) endpoint pairs (mm floats, unrounded);
    degenerate segments (length < 0.5mm) are skipped and counted, never silently dropped."""
    faces, skipped = [], 0
    for w in (wall_lines or []):
        x1, y1 = float(w["x1"]), float(w["y1"])
        x2, y2 = float(w["x2"]), float(w["y2"])
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 0.5:
            skipped += 1
            continue
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        h = t / 2.0
        faces.append((((x1 + nx * h, y1 + ny * h), (x2 + nx * h, y2 + ny * h)),
                      ((x1 - nx * h, y1 - ny * h), (x2 - nx * h, y2 - ny * h))))
    return faces, skipped


def append_wall_ink(svg, wall_lines, t=WALL_T_MM):
    """Append the double-line wall ink to an existing SVG string (before </svg>), the same
    wrapper pattern f2_facing_lane.oriented_svg uses for strips. Returns
    (svg, expected_segs, n_skipped): expected_segs = the appended endpoints EXACTLY as
    formatted (%.1f, matching synth_plan_2d), in append order, so the caller can identity-
    pin read_ink's tail slice against them. A face that rounds to zero length is skipped
    and counted (read_ink drops zero-length segs, which would silently shift the slice)."""
    faces, skipped = wall_face_lines(wall_lines, t)
    lines, expected = [], []
    for fa, fb in faces:
        for (ax, ay), (bx, by) in (fa, fb):
            ra = (float(f"{ax:.1f}"), float(f"{ay:.1f}"))
            rb = (float(f"{bx:.1f}"), float(f"{by:.1f}"))
            if ra == rb:
                skipped += 1
                continue
            lines.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}"/>')
            expected.append((ra, rb))
    if not lines:
        return svg, [], skipped
    return svg.replace("</svg>", "\n".join(lines + ["</svg>"])), expected, skipped


# ---- ring-pair veto (detector side) ----------------------------------------------------------
# Same ring GEOMETRY as f2_facing_lane._ring_member_idx (two horizontals sharing an
# x-extent + verticals joining their corners, coincident sides collected), but a
# DIFFERENT use: a segment inside a closed rectangle is SYMBOL-OUTLINE ink, and a wall
# is an OPEN double line -- so a candidate pair whose members are BOTH outline ink is
# furniture geometry (a rect's own opposite edges; two aligned twins' facing edges; a
# 2000x80 curtain's long sides), never a wall. Ring x line and line x line stay
# pairable: that is what keeps double-wall cavity faces detectable (the cavity closes an
# exact 140mm rectangle of wall-face ink, scene_00023 pilot forensic). Three dead ends
# are pinned in tests/comments: excluding ALL ring members from pairing ate real walls
# (walls_zero forensic); a furniture-size screen turned the detector into an accidental
# thin-decor stripper (fp 2 -> 3,081, blind>oracle paradox, pilot 2026-07-10); and a
# same-ring-only veto let two aligned twins' facing edges pair at a wall-like gap.
def ring_groups(segs, tol=0.6):
    """Closed axis-aligned rectangles in the ink -> list of member-index sets (one set
    per rectangle, coincident sides included)."""
    def k(v):
        return round(float(v), 1)
    hs, vs = {}, {}
    for i, s in enumerate(segs):
        (x0, y0), (x1, y1) = s
        if abs(y1 - y0) <= tol and abs(x1 - x0) > tol:
            a, b = sorted((x0, x1))
            hs.setdefault((k(a), k(b)), []).append((k(0.5 * (y0 + y1)), i))
        elif abs(x1 - x0) <= tol and abs(y1 - y0) > tol:
            a, b = sorted((y0, y1))
            vs.setdefault((k(a), k(b)), []).append((k(0.5 * (x0 + x1)), i))
    groups = []
    for (xa, xb), rows in hs.items():
        if len(rows) < 2:
            continue
        for i1 in range(len(rows)):
            for i2 in range(i1 + 1, len(rows)):
                (ya, ia), (yb, ib) = rows[i1], rows[i2]
                if ya == yb:
                    continue
                lo, hi = (ya, yb) if ya < yb else (yb, ya)
                sides = vs.get((lo, hi), [])
                left = [ix for xv, ix in sides if xv == xa]
                right = [ix for xv, ix in sides if xv == xb]
                if left and right:
                    groups.append({ia, ib} | set(left) | set(right))
    return groups


# ---- detection (ink side, geometry only) ---------------------------------------------------
class _Seg:
    __slots__ = ("i", "x1", "y1", "x2", "y2", "ux", "uy", "L", "mx", "my", "ang")

    def __init__(self, i, s):
        (self.x1, self.y1), (self.x2, self.y2) = s
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        self.L = math.hypot(dx, dy)
        self.ux, self.uy = (dx / self.L, dy / self.L) if self.L > 0 else (1.0, 0.0)
        self.mx, self.my = (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0
        self.ang = math.degrees(math.atan2(dy, dx)) % 180.0
        self.i = i


def _angle_diff(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def _pair_centerline(A, B):
    """The double-line test for one ordered pair; returns (centerline, score) or None.
    score = (|gap - WALL_T_MM|, alignment error, |length diff|) -- a wall's TRUE partner
    face scores ~(0, 0, 0) and beats any furniture edge, which is what makes the
    mutual-best screen below work. A is the reference line; the test is symmetric enough
    that the caller only checks each unordered pair once.

    The gap is tested at BOTH of B's endpoints, same side, not at the midpoint: a
    <=5deg-tilted end-aligned stroke passes a midpoint-only gap test with align_err 0
    while its ends diverge L*tan(5deg) laterally (adversarial review 2026-07-10,
    geometry lens -- unreachable on the axis-aligned synth but live on any production
    port), and a stroke CROSSING A's line can average into the window."""
    if _angle_diff(A.ang, B.ang) > ANGLE_TOL_DEG:
        return None
    if min(A.L, B.L) / max(A.L, B.L) < LEN_RATIO_MIN:
        return None
    nx, ny = -A.uy, A.ux
    d1 = (B.x1 - A.x1) * nx + (B.y1 - A.y1) * ny
    d2 = (B.x2 - A.x1) * nx + (B.y2 - A.y1) * ny
    if d1 * d2 <= 0:                               # crosses (or touches) A's line
        return None
    if not (GAP_MIN_MM <= abs(d1) <= GAP_MAX_MM and GAP_MIN_MM <= abs(d2) <= GAP_MAX_MM):
        return None
    if abs(abs(d1) - abs(d2)) > GAP_DEV_MM:        # constant-offset faces only
        return None
    lat = (abs(d1) + abs(d2)) / 2.0
    t1 = (B.x1 - A.x1) * A.ux + (B.y1 - A.y1) * A.uy
    t2 = (B.x2 - A.x1) * A.ux + (B.y2 - A.y1) * A.uy
    lo, hi = (t1, t2) if t1 <= t2 else (t2, t1)
    align_err = max(abs(lo), abs(hi - A.L))
    if align_err > ALIGN_TOL_MM:
        return None
    if t1 <= t2:
        bs, be = (B.x1, B.y1), (B.x2, B.y2)
    else:
        bs, be = (B.x2, B.y2), (B.x1, B.y1)
    cl = (((A.x1 + bs[0]) / 2.0, (A.y1 + bs[1]) / 2.0),
          ((A.x2 + be[0]) / 2.0, (A.y2 + be[1]) / 2.0))
    return cl, (abs(lat - WALL_T_MM), align_err, abs(A.L - B.L))


def _merge_centerlines(cls):
    """Union-find merge of raw pair centerlines that lie on the same line (angle <= 2deg,
    lateral offset <= MERGE_LAT_MM) and touch/overlap longitudinally (gap <= MERGE_GAP_MM).
    Each group re-emits ONE segment spanning the group's extent along its longest member."""
    segs = [_Seg(i, c) for i, c in enumerate(cls)]
    parent = list(range(len(segs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def same_line(A, B):
        if _angle_diff(A.ang, B.ang) > 2.0:
            return False
        nx, ny = -A.uy, A.ux
        if abs((B.mx - A.x1) * nx + (B.my - A.y1) * ny) > MERGE_LAT_MM:
            return False
        t1 = (B.x1 - A.x1) * A.ux + (B.y1 - A.y1) * A.uy
        t2 = (B.x2 - A.x1) * A.ux + (B.y2 - A.y1) * A.uy
        lo, hi = min(t1, t2), max(t1, t2)
        return not (hi < -MERGE_GAP_MM or lo > A.L + MERGE_GAP_MM)

    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            if find(i) != find(j) and same_line(segs[i], segs[j]):
                parent[find(i)] = find(j)

    groups = {}
    for i in range(len(segs)):
        groups.setdefault(find(i), []).append(segs[i])
    out = []
    for members in groups.values():
        ax = max(members, key=lambda s: s.L)          # the group's axis line
        ts = []
        for s in members:
            for px, py in ((s.x1, s.y1), (s.x2, s.y2)):
                ts.append((px - ax.x1) * ax.ux + (py - ax.y1) * ax.uy)
        t0, t1 = min(ts), max(ts)
        out.append({"x1": round(ax.x1 + t0 * ax.ux, 1), "y1": round(ax.y1 + t0 * ax.uy, 1),
                    "x2": round(ax.x1 + t1 * ax.ux, 1), "y2": round(ax.y1 + t1 * ax.uy, 1)})
    out.sort(key=lambda c: (c["x1"], c["y1"], c["x2"], c["y2"]))
    return out


def detect_walls(segs_mm, ring_sets=None):
    """Ink segments (mm) -> {"wall_idx": set of classified segment indices,
    "centerlines": [{x1,y1,x2,y2}...] merged, "stats": {...}}. Consumes GEOMETRY ONLY --
    no gt field ever reaches this function. ring_sets defaults to ring_groups(segs_mm)
    (closed rects from the same ink); two segments closing the SAME rectangle never
    pair. Pass ring_sets=[] to disable the veto in tests."""
    if ring_sets is None:
        ring_sets = ring_groups(segs_mm)
    ring_of = {}
    for gid, members in enumerate(ring_sets):
        for i in members:
            ring_of.setdefault(i, set()).add(gid)
    stats = {"n_segs": len(segs_mm), "n_short": 0, "n_ring_members": len(ring_of),
             "pairs_checked": 0, "pairs_ring_vetoed": 0, "pairs_geo_ok": 0,
             "pairs_nonmutual_rejected": 0, "pairs_accepted": 0}
    cand = []
    for i, s in enumerate(segs_mm):
        g = _Seg(i, s)
        if g.L < MIN_LINE_MM:
            stats["n_short"] += 1
            continue
        cand.append(g)

    # spatial hash on midpoints: a co-terminous pair's midpoints sit within ~300mm
    grid = {}
    for g in cand:
        grid.setdefault((int(g.mx // _GRID_MM), int(g.my // _GRID_MM)), []).append(g)

    # phase 1: geometric candidates (ring-pair veto first -- outline x outline ink is
    # furniture geometry, never a wall)
    geo, seen = {}, set()
    for (cx, cy), cell in grid.items():
        neigh = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neigh.extend(grid.get((cx + dx, cy + dy), ()))
        for A in cell:
            for B in neigh:
                if B.i <= A.i:
                    continue
                key = (A.i, B.i)
                if key in seen:
                    continue
                seen.add(key)
                stats["pairs_checked"] += 1
                if A.i in ring_of and B.i in ring_of:   # outline ink x outline ink
                    stats["pairs_ring_vetoed"] += 1
                    continue
                got = _pair_centerline(A, B)
                if got is None:
                    continue
                stats["pairs_geo_ok"] += 1
                geo[key] = got

    # phase 2: MUTUAL-BEST screen, run in ROUNDS. A real double line is two strokes
    # drawn by offsetting ONE centerline: each face's best partner (gap closest to T,
    # best-aligned) is the other face, score ~(0,0,0). A furniture edge flush along a
    # wall may pass phase 1 against a wall FACE (the 513-fp wardrobe-niche class, pilot
    # 2026-07-10), but that face always prefers its own partner -- non-mutual, rejected
    # and counted. ROUNDS because a single pass breaks exact-score ties by dict
    # insertion order and can orphan a whole wall (double wall at spacing 2*T/2: the
    # cross pair scores exactly (0,0,0) too; the shared face picks one side and the
    # other wall's PERFECT own-pair goes non-mutual -- adversarial review 2026-07-10,
    # geometry lens, reproduced). Re-running the same screen over still-unmatched faces
    # recovers every such unforced orphan; ties are broken by (score, lower index) so
    # the outcome is deterministic and order-independent.
    wall_idx, raw_cls = set(), []
    remaining = dict(geo)
    while remaining:
        best = {}
        for (i, j), (cl, score) in remaining.items():
            key = (score, j)
            if i not in best or key < best[i]:
                best[i] = (score, j)
            key = (score, i)
            if j not in best or key < best[j]:
                best[j] = (score, i)
        accepted = []
        for (i, j), (cl, score) in remaining.items():
            if best[i][1] == j and best[j][1] == i:
                accepted.append((i, j, cl))
        if not accepted:
            stats["pairs_nonmutual_rejected"] += len(remaining)
            break
        for i, j, cl in accepted:
            stats["pairs_accepted"] += 1
            wall_idx.add(i)
            wall_idx.add(j)
            raw_cls.append(cl)
        remaining = {(i, j): v for (i, j), v in remaining.items()
                     if i not in wall_idx and j not in wall_idx}

    centerlines = _merge_centerlines(raw_cls) if raw_cls else []
    stats["wall_segs"] = len(wall_idx)
    stats["raw_centerlines"] = len(raw_cls)
    stats["centerlines"] = len(centerlines)
    return {"wall_idx": wall_idx, "centerlines": centerlines, "stats": stats}


# ---- detector quality vs gt (report side only -- never feeds the pred) ---------------------
def _cover_intervals(target, sources, lat_tol, ang_tol):
    """Union length of `target` (a _Seg) covered by near-parallel `sources` within
    lat_tol of its line, plus the total: (covered_len, target_len)."""
    ivals = []
    nx, ny = -target.uy, target.ux
    for s in sources:
        if _angle_diff(target.ang, s.ang) > ang_tol:
            continue
        d1 = abs((s.x1 - target.x1) * nx + (s.y1 - target.y1) * ny)
        d2 = abs((s.x2 - target.x1) * nx + (s.y2 - target.y1) * ny)
        if max(d1, d2) > lat_tol:
            continue
        t1 = (s.x1 - target.x1) * target.ux + (s.y1 - target.y1) * target.uy
        t2 = (s.x2 - target.x1) * target.ux + (s.y2 - target.y1) * target.uy
        lo, hi = max(min(t1, t2), 0.0), min(max(t1, t2), target.L)
        if hi > lo:
            ivals.append((lo, hi))
    ivals.sort()
    covered, end = 0.0, -1e18
    for lo, hi in ivals:
        if lo > end:
            covered += hi - lo
            end = hi
        elif hi > end:
            covered += hi - end
            end = hi
    return covered, target.L


def coverage_vs_gt(centerlines, wall_lines, lat_tol=60.0, ang_tol=6.0):
    """Length-weighted detector quality vs the gt centerlines (REPORT side only):
    recall_len = gt length covered by detected lines / total gt length;
    precision_len = detected length covered by gt lines / total detected length.
    Zero-coverage walls are SPLIT by length -- a wall shorter than MIN_LINE_MM is
    undetectable BY CONSTRUCTION (both drawn faces are skipped as short strokes), and
    lumping those with real misses of long walls would let a genuine detector
    regression hide inside the micro-wall narrative (adversarial review 2026-07-10):
      walls_zero_micro  L <  MIN_LINE_MM (accepted-by-construction)
      walls_zero_real   L >= MIN_LINE_MM (REAL misses -- inspect)
      zero_max_len      longest zero-covered wall (mm)
    Degenerate gt segs are skipped."""
    gts = []
    for w in (wall_lines or []):
        s = _Seg(0, ((float(w["x1"]), float(w["y1"])), (float(w["x2"]), float(w["y2"]))))
        if s.L >= 0.5:
            gts.append(s)
    dets = []
    for c in (centerlines or []):
        s = _Seg(0, ((float(c["x1"]), float(c["y1"])), (float(c["x2"]), float(c["y2"]))))
        if s.L >= 0.5:
            dets.append(s)
    gt_cov = gt_tot = 0.0
    zero_micro = zero_real = 0
    zero_max = 0.0
    for g in gts:
        c, L = _cover_intervals(g, dets, lat_tol, ang_tol)
        gt_cov += c
        gt_tot += L
        if c < 1e-9:
            if L < MIN_LINE_MM:
                zero_micro += 1
            else:
                zero_real += 1
            zero_max = max(zero_max, L)
    det_cov = det_tot = 0.0
    for d in dets:
        c, L = _cover_intervals(d, gts, lat_tol, ang_tol)
        det_cov += c
        det_tot += L
    return {"n_gt_walls": len(gts), "n_det": len(dets),
            "walls_zero": zero_micro + zero_real,
            "walls_zero_micro": zero_micro, "walls_zero_real": zero_real,
            "zero_max_len": round(zero_max, 1),
            "gt_len": round(gt_tot, 1), "gt_covered": round(gt_cov, 1),
            "det_len": round(det_tot, 1), "det_covered": round(det_cov, 1),
            "recall_len": (gt_cov / gt_tot) if gt_tot else None,
            "precision_len": (det_cov / det_tot) if det_tot else None}
