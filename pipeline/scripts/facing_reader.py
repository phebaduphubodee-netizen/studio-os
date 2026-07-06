"""
facing_reader.py -- machine cross-check of a piece's hand-typed facing vs. the
DRAWN symbol geometry (pure geometry; NO fitz/PDF/matplotlib -> unit-testable).

WHY: in a 2D->3D furniture reading the occupant's facing is hand-typed as an
integer `rot`, but the plan symbol already encodes it: a bed's headboard strip /
a sofa's backrest strip is drawn as line(s) running PARALLEL to, and set a little
INSIDE, the BACK edge -- the edge OPPOSITE the way the occupant faces. This module
reads that strip and returns "agree/disagree/unknown" so a wrong rot can be flagged
BEFORE the owner is the sole verifier. It is ADVISORY and CONSERVATIVE: a bare
rectangle (no strip) MUST read "unknown", never a false "disagree".

CONVENTION (matches furniture.py / placement_logic._front_vec exactly):
  facing unit vector F(rot) = (sin(rad(rot)), -cos(rad(rot)))
    rot   0 -> (0,-1) SOUTH,  90 -> (1,0) EAST,
        180 -> (0, 1) NORTH, 270 -> (-1,0) WEST.
  Cardinal facing name: {0:"S", 90:"E", 180:"N", 270:"W"}; non-cardinal -> None.
  Bbox edges by compass: N=+y (top), S=-y (bottom), E=+x (right), W=-x (left).
  BACK/HEAD edge (where the strip is drawn) = opposite(facing).
    e.g. rot 270 faces WEST -> headboard on the EAST edge.

METHOD (read_facing): for each edge, sum the length of segments that (a) run
PARALLEL to it (a N/S edge wants horizontal strokes |dy|<=|dx|*PARALLEL_TOL; an
E/W edge wants vertical) AND (b) whose perpendicular position falls in an inner
band inner_lo..inner_hi of the perpendicular extent, measured INWARD from that
edge, with the parallel run clipped to the bbox span. Normalise each edge by its
own length so a longer edge is not favoured. back_edge = global argmax, kept ONLY
if it dominates its OPPOSITE edge (score >= dom_ratio*opposite, a zero opposite
counts as dominated) and score >= min_score; else None. facing = opposite(back).

TUNING (defaults chosen for ~mm plans, documented per the caller's request):
  inner_lo=0.05  A real headboard/backrest is thin: ~50-200mm inset on a ~2000mm
                 piece = 0.025..0.10 of the extent. The prompt's 0.08 rejected a
                 realistically-thin strip drawn ~150mm in (0.075); 0.05 admits it
                 while STILL excluding the outermost outline line (offset ~0), so
                 the outline never scores.  (A strip inset <5% is missed -> the
                 read degrades to "unknown", which is the safe direction.)
  inner_hi=0.45  Kept < 0.50 on purpose: opposite bands (measured inward from
                 either side) then never overlap, so a single line down the
                 CENTRE of a symbol cannot score two opposite edges at once.
  dom_ratio=1.6  back edge must beat its opposite by 60%+; a symmetric piece with
                 strokes on both the back AND front edge washes out -> None.
  min_score=0.35 a strip must cover >=35% of its edge (normalised) to count --
                 filters stray drawer/cushion/rug ticks.
CAVEAT for the caller: a decorative line parallel to and inset from a NON-back
edge (deep drawer front, seat-cushion seam, framed rug edge) can spoof an edge;
the dominance + min_score gates absorb the common cases, but wire this as REVIEW
signal, never a hard FAIL, and trust "unknown" as a genuine "cannot tell".
"""
import math

PARALLEL_TOL = 0.30          # |perp slope| tolerance for "parallel to edge"
_FACING = {0: "S", 90: "E", 180: "N", 270: "W"}
_OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}


def facing_from_rot(rot):
    """Cardinal facing letter for a cardinal rot, else None (non-cardinal)."""
    try:
        r = int(round(float(rot))) % 360
    except (TypeError, ValueError):
        return None
    return _FACING.get(r)


def opposite(edge):
    """Opposite compass letter (N<->S, E<->W); None passes through."""
    return _OPP.get(edge)


def _overlap(a0, a1, b0, b1):
    """Length of the 1-D overlap of [a0,a1] and [b0,b1] (0 if disjoint)."""
    return max(0.0, min(a1, b1) - max(a0, b0))


def _edge_scores(segments, bbox, inner_lo, inner_hi):
    """Return {N,S,E,W: normalised inner-band parallel-stroke length}."""
    x0, y0, x1, y1 = bbox
    w = float(x1 - x0)
    h = float(y1 - y0)
    if w <= 0 or h <= 0:
        return {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}
    # inner bands (perpendicular position ranges), measured inward from each edge
    s_band = (y0 + inner_lo * h, y0 + inner_hi * h)          # from S edge (y0), up
    n_band = (y1 - inner_hi * h, y1 - inner_lo * h)          # from N edge (y1), down
    w_band = (x0 + inner_lo * w, x0 + inner_hi * w)          # from W edge (x0), right
    e_band = (x1 - inner_hi * w, x1 - inner_lo * w)          # from E edge (x1), left
    raw = {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}
    for seg in segments:
        (sx0, sy0), (sx1, sy1) = seg[0], seg[1]
        dx, dy = sx1 - sx0, sy1 - sy0
        adx, ady = abs(dx), abs(dy)
        if adx == 0 and ady == 0:
            continue
        if ady <= adx * PARALLEL_TOL:                       # horizontal -> N/S edges
            perp = 0.5 * (sy0 + sy1)                        # its y position
            run = _overlap(min(sx0, sx1), max(sx0, sx1), x0, x1)   # clip to bbox span
            if run <= 0:
                continue
            if n_band[0] <= perp <= n_band[1]:
                raw["N"] += run
            if s_band[0] <= perp <= s_band[1]:
                raw["S"] += run
        elif adx <= ady * PARALLEL_TOL:                     # vertical -> E/W edges
            perp = 0.5 * (sx0 + sx1)                        # its x position
            run = _overlap(min(sy0, sy1), max(sy0, sy1), y0, y1)
            if run <= 0:
                continue
            if e_band[0] <= perp <= e_band[1]:
                raw["E"] += run
            if w_band[0] <= perp <= w_band[1]:
                raw["W"] += run
    return {"N": raw["N"] / w, "S": raw["S"] / w,           # normalise by edge length
            "E": raw["E"] / h, "W": raw["W"] / h}


def read_facing(segments, bbox, inner_lo=0.05, inner_hi=0.45,
                dom_ratio=1.6, min_score=0.35):
    """Read the occupant facing from the drawn back-strip geometry.

    Returns {"back_edge","facing","confidence","scores"}; back_edge/facing are
    None when no edge dominates its opposite by dom_ratio at >= min_score."""
    scores = _edge_scores(segments, bbox, inner_lo, inner_hi)
    best = max(scores, key=scores.get)
    s = scores[best]
    opp = scores[opposite(best)]
    dominant = s >= min_score and (opp <= 0.0 or s >= dom_ratio * opp)
    if not dominant:
        return {"back_edge": None, "facing": None, "confidence": 0.0, "scores": scores}
    margin = 1.0 if opp <= 0.0 else max(0.0, (s - opp) / (s + opp))
    conf = round(min(1.0, s) * margin, 3)
    return {"back_edge": best, "facing": opposite(best), "confidence": conf, "scores": scores}


def check_piece(segments, bbox, rot):
    """Cross-check hand-typed `rot` against the drawn strip. ADVISORY.

    verdict "agree"     -> read facing == claimed (both cardinal),
            "disagree"  -> a 90-deg PERPENDICULAR inconsistency the symbol genuinely contradicts,
            "ambiguous" -> a 180-deg flip: the SOLE dominant strip sits on the claimed-FRONT edge.
                           Geometry cannot tell a footboard/rug in front of a correctly-faced
                           piece from an inverted headboard -- so this is NOT a false 'disagree',
                           but it is NOT silent either: 180 is the commonest facing error, so the
                           caller surfaces it as a soft 'eyeball the orientation' REVIEW prompt.
            "unknown"   -> claimed non-cardinal OR no dominant strip read (nothing to say)."""
    claimed = facing_from_rot(rot)
    rf = read_facing(segments, bbox)
    read = rf["facing"]
    if claimed is None or read is None:
        verdict = "unknown"
    elif read == claimed:
        verdict = "agree"
    elif rf["back_edge"] == claimed:
        verdict = "ambiguous"     # 180 flip: strip on the claimed-front edge (footboard vs inverted headboard)
    else:
        verdict = "disagree"      # 90-deg off: the symbol truly contradicts the typed facing
    return {"claimed": claimed, "read": read, "verdict": verdict,
            "confidence": rf["confidence"], "back_edge": rf["back_edge"],
            "scores": rf["scores"]}
