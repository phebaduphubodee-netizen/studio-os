"""WHOLE-BED AUDITION RULES — pure geometry, no bpy (layer law: bedcloth_rules is the
precedent; the Blender side lives in wholebed_bench.py).

WHY THIS EXISTS (p2r51). p2r49 measured that no free CLOTH SET makes this bed: the
best of 22 reaches 43.2% duvet share against the 0.80 delivered-minimum cut, and the
best cover is 86 mm too narrow to reach either flank of the 1820 mm mattress. p2r50
then measured the other half in IMAGE space: our bare mattress flank is 254,849 px
where seven delivered frames read none-or-sliver, unanimously, blind. A WHOLE BED
brings its own mattress, so our box LEAVES the frame rather than needing covering —
the defect's surface area goes to zero by construction, not by drape. The cache holds
whole-bed candidates that no bench has ever auditioned, because bedcloth_bench asks
"which cloth covers OUR mattress" and a whole bed is out of scope by construction
(the p2r49 gate records this as "the scope was the defect").

THE INK THIS AUDITION SERVES (R12 SHEET-FIRST — crop archived beside the bench run):
the drawing of record draws the bed as a MADE BED: one clean 2000 x 2149 mm rectangle,
duvet to the edges, two pillows at the EAST head, a turned-back corner, NO footboard —
the foot bench sits 54 mm off the foot face. So a candidate with a tall footboard
contradicts the ink, and a candidate whose own headboard cannot be separated collides
with the sheet-drawn headboard band (SR-18) that R12 keeps built.

Every function is pure over PART dicts: {"name": str, "lo": (x,y,z), "hi": (x,y,z),
"tris": int}. All lengths in METRES here (Blender world units); mm only in reports.
"""

# A bed-anchor part's long horizontal axis, metres. Wide enough for a california king
# with side rails, narrow enough to exclude a room backdrop.
ANCHOR_LONG_M = (1.55, 3.30)
# The anchor must present real plan area — a duvet lying on a bed qualifies; a lamp
# cable does not. Fraction of the DRAWN bed plan (2.000 x 2.149 = 4.298 m2).
ANCHOR_PLAN_FRAC = 0.30
# Keep parts whose plan bbox comes within this of the anchor's plan bbox. Nightstands
# in bed-set files sit 60-300 mm off the frame; pendant lamps hang inside the plan.
NEAR_M = 0.05
# A part whose bottom starts this far above the anchor top is hanging decor
# (e63ab045 ships two Flos pendants), never part of the bed.
ABOVE_M = 0.60
# Backdrop wall: taller than this and thinner than this is scenery, not furniture.
WALL_TALL_M = 1.40
WALL_THIN_M = 0.09
# Head-end detection: compare the two 25% end bands of the long axis by their tallest
# geometry; the head is where pillows and headboards stand.
END_BAND = 0.25
# A separable own-headboard part: standing in the head band, rising above the
# sleeping plane by more than a leaning pillow does (pillows top out ~+0.25..0.45;
# headboards start ~+0.5 — the first batch run deleted e63ab045's entire pillow
# bank at 0.35, which is how this number was learned), THIN along the head axis,
# and WIDE across the bed (an individual pillow is never more than half the bed).
HB_ABOVE_PLANE_M = 0.45
HB_BAND_M = 0.40
HB_THIN_M = 0.30
HB_WIDE_FRAC = 0.50
# The ink's no-footboard test: highest geometry in the foot band may not rise more
# than this above the sleeping plane (a rolled duvet edge passes; a footboard fails).
FOOT_ABOVE_PLANE_M = 0.18
# Never stretch (R8 / model_requirements law, same constant bedcloth carries).
MAX_SCALE = 1.0
# Candidate frame may not fall short of the drawn footprint by more than this per
# axis fraction — a 1.6 m bed in a 2.149 m slot is a different bed, not a fit.
MIN_FILL = 0.88


def size(part):
    return tuple(part["hi"][i] - part["lo"][i] for i in range(3))


def plan_area(part):
    s = size(part)
    return s[0] * s[1]


def plan_gap(a, b):
    """Largest per-axis clearance between two parts' PLAN bboxes (0 if they overlap)."""
    gx = max(a["lo"][0] - b["hi"][0], b["lo"][0] - a["hi"][0], 0.0)
    gy = max(a["lo"][1] - b["hi"][1], b["lo"][1] - a["hi"][1], 0.0)
    return max(gx, gy)


def unit_factor(parts, drawn_long_m=2.149):
    """Which uniform factor lands the file in metres-at-bed-scale.

    SketchUp exports arrive in metres, inches-as-metres, or centimetres-as-metres
    (the shelf's own fa59acea reads 1053 m across). Try the factors the exporters
    actually produce; pick the one whose LARGEST plan extent lands within a bed-set
    scene band (1.5-12 m: one bed up to a small showroom row). Ambiguity or no fit
    is a reject, never a guess (R8: scale is asserted, never assumed).
    """
    if not parts:
        return None, "no parts"
    ext = max(max(size(p)[0], size(p)[1]) for p in parts)
    fits = [f for f in (1.0, 0.0254, 0.01, 0.001) if 1.5 <= ext * f <= 12.0]
    if not fits:
        return None, f"no unit factor lands {ext:.3f} in a 1.5-12 m scene band"
    if len(fits) > 1:
        # prefer the factor that puts the largest BED-CANDIDATE part inside the
        # anchor band; still ambiguous -> reject.
        good = []
        for f in fits:
            for p in parts:
                s = size(p)
                if ANCHOR_LONG_M[0] <= max(s[0], s[1]) * f <= ANCHOR_LONG_M[1] \
                        and plan_area(p) * f * f >= ANCHOR_PLAN_FRAC * 2.0 * drawn_long_m:
                    good.append(f)
                    break
        if len(good) == 1:
            return good[0], f"factor {good[0]} (disambiguated by anchor band)"
        return None, f"ambiguous unit factors {fits}"
    return fits[0], f"factor {fits[0]}"


def pick_anchor(parts, drawn_plan_m2=4.298):
    """The part the bed is organised around: largest plan area whose long axis sits
    in the anchor band. None -> the file holds no bed at this scale."""
    best = None
    for p in parts:
        s = size(p)
        long_ax = max(s[0], s[1])
        if not (ANCHOR_LONG_M[0] <= long_ax <= ANCHOR_LONG_M[1]):
            continue
        if plan_area(p) < ANCHOR_PLAN_FRAC * drawn_plan_m2:
            continue
        if best is None or plan_area(p) > plan_area(best):
            best = p
    return best


def strip(parts, anchor):
    """(keep, dropped) where dropped is [(part, why)]. Scenery and neighbours leave;
    everything organised around the anchor stays. Geometric, never by name (R9b)."""
    keep, dropped = [], []
    for p in parts:
        if p is anchor:
            keep.append(p)
            continue
        s = size(p)
        h = s[2]
        thin = min(s[0], s[1])
        if h >= WALL_TALL_M and thin <= WALL_THIN_M:
            dropped.append((p, "backdrop wall/plane"))
            continue
        if p["lo"][2] >= anchor["hi"][2] + ABOVE_M:
            dropped.append((p, "hanging decor above the bed"))
            continue
        if plan_gap(p, anchor) > NEAR_M:
            dropped.append((p, "off-bed neighbour (nightstand/showroom)"))
            continue
        keep.append(p)
    return keep, dropped


def head_end(parts, axis=0):
    """'lo' or 'hi': which end of `axis` carries the tall head geometry.

    Ties (flat platform beds with no pillows) return None — the bench then refuses
    to guess and reports orientation UNRESOLVED, because a bed placed head-west by
    a coin flip is exactly the class of defect R9 exists to stop.
    """
    lo = min(p["lo"][axis] for p in parts)
    hi = max(p["hi"][axis] for p in parts)
    span = hi - lo
    if span <= 0:
        return None
    band = span * END_BAND
    top_lo = max((p["hi"][2] for p in parts if p["lo"][axis] < lo + band), default=0.0)
    top_hi = max((p["hi"][2] for p in parts if p["hi"][axis] > hi - band), default=0.0)
    if abs(top_lo - top_hi) < 0.06:
        return None
    return "lo" if top_lo > top_hi else "hi"


def sleeping_plane(samples):
    """Median of top-surface z samples over the central plan — the candidate's own
    sleeping plane, derived, never typed."""
    zs = sorted(samples)
    return zs[len(zs) // 2] if zs else None


def headboard_parts(parts, plane_z, head_x, head="hi", bed_w=None):
    """Separable own-headboard parts: REACHING INTO the head band, rising well above
    the sleeping plane, THIN along the head axis, and WIDE across the bed. All four
    together, because the first batch run proved each alone is wrong: 0.35-over-plane
    alone deleted a pillow bank; band-reach alone tagged nightstand wings. Returns
    (separable, fused) — fused=True when tall+wide head geometry belongs to a part
    that is also the bed body (one-mesh beds must not pass silently)."""
    if bed_w is None:
        bed_w = max((p["hi"][1] for p in parts), default=0.0) - \
            min((p["lo"][1] for p in parts), default=0.0)
    sep, fused_any = [], False
    for p in parts:
        s = size(p)
        if head == "hi":
            reaches = p["hi"][0] > head_x - HB_BAND_M
        else:
            reaches = p["lo"][0] < head_x + HB_BAND_M
        tall = p["hi"][2] > plane_z + HB_ABOVE_PLANE_M
        wide = s[1] >= HB_WIDE_FRAC * bed_w
        thin = s[0] <= HB_THIN_M
        if reaches and tall and wide:
            if thin:
                sep.append(p)
            else:
                fused_any = True
    return sep, fused_any


def foot_over_plane(parts, plane_z, foot_x, head="hi"):
    """Highest rise above the sleeping plane in the foot band (metres). The ink
    draws no footboard and the bench sits 54 mm away — this is the number that
    test reads."""
    worst = 0.0
    for p in parts:
        in_band = (p["hi"][0] - foot_x <= HB_BAND_M) if head == "hi" \
            else (foot_x - p["lo"][0] <= HB_BAND_M)
        if in_band:
            worst = max(worst, p["hi"][2] - plane_z)
    return worst


def plan_scale_whole(native_len, native_w, fit_len=2.000, fit_w=2.149):
    """Uniform scale for the ASSEMBLED bed against the drawn footprint.

    s caps at MAX_SCALE (never stretch); fill reports how much of the drawn
    footprint the scaled bed actually occupies — MIN_FILL below is a different
    bed, not a fit. Returns (s, fill_len, fill_w)."""
    if native_len <= 0 or native_w <= 0:
        return None, 0.0, 0.0
    s = min(MAX_SCALE, fit_len / native_len, fit_w / native_w)
    return s, s * native_len / fit_len, s * native_w / fit_w


# ---------------------------------------------------------------- integration --
# P2r-52 (D-106 -> D-107): the INTEGRATION strip — the debts the audition
# enumerated on the winning candidate, written as geometry rather than as mesh
# names (R9b), and verified against an id-coloured render of the file before the
# predicates were frozen (the "shelf+box vs plaid" pair was an inference until
# the look settled it: the full-width burl panel is ONE mesh, the "wings" its two
# visible ends; the below-plane pair are the side shelf boards; the plaid is a
# lying-flat accent band on the pillow bank).

# A second headboard plane: thinner along the head axis than any real bedding
# and spanning most of the bed. The audition's own headboard strip requires
# TALL (plane + 0.45); this panel tops out under that, which is exactly how it
# survived to integration.
HEAD_PANEL_THIN_M = 0.06
HEAD_PANEL_WIDE_FRAC = 0.70
# A dead side board: a thin shelf whose useful surface ends BELOW the sleeping
# plane (R10: a surface nobody can use from the bed is a fabricated object) and
# whose plan is board-sized, never platform-sized.
DEAD_BOARD_THIN_M = 0.04
DEAD_BOARD_PLAN_M2 = 0.20
# A lying-flat accent on the pillow bank: presented height under its own
# smallest plan dimension = a draped band, not a standing pillow. Real pillows
# in this file measure z >= 1.1x their depth; the accent measures 0.6x.
# Bedding is exempted FIRST by plan share of the anchor.
BEDDING_PLAN_FRAC = 0.35


def head_panel_parts(parts, plane_z, head_x, head="hi", bed_w=None, anchor=None):
    """Duplicate headboard planes at the head: reach the head band, THIN along
    the head axis, spanning most of the bed across, standing above the plane.
    The sheet-drawn band (SR-18) is the headboard of record (R12); any
    full-width panel the candidate parks there duplicates owner millwork."""
    if bed_w is None:
        bed_w = max((p["hi"][1] for p in parts), default=0.0) - \
            min((p["lo"][1] for p in parts), default=0.0)
    out = []
    for p in parts:
        if p is anchor:
            continue
        s = size(p)
        if head == "hi":
            reaches = p["hi"][0] > head_x - HB_BAND_M
        else:
            reaches = p["lo"][0] < head_x + HB_BAND_M
        if (reaches and s[0] <= HEAD_PANEL_THIN_M
                and s[1] >= HEAD_PANEL_WIDE_FRAC * bed_w
                and p["hi"][2] > plane_z + 0.05):
            out.append(p)
    return out


def dead_side_boards(parts, plane_z, anchor=None):
    """Attached shelf boards whose top ends below the sleeping plane: a surface
    that cannot be reached from the bed and does not exist in the drawing
    (R10 — the absent thing is honest; a dead surface fabricates a reading)."""
    out = []
    for p in parts:
        if p is anchor:
            continue
        s = size(p)
        if (p["hi"][2] < plane_z - 0.05
                and min(s[0], s[1]) <= DEAD_BOARD_THIN_M
                and plan_area(p) <= DEAD_BOARD_PLAN_M2):
            out.append(p)
    return out


def flat_accents_on_bank(parts, plane_z, anchor=None, drawn_plan_m2=4.298):
    """Lying-flat decor bands on the pillow bank: above the plane, too small to
    be the bedding field, presented height under their own smallest plan
    dimension. A standing pillow is taller than it is deep; a draped accent
    band is not. Bedding (the duvet field) is exempted first by plan share."""
    out = []
    for p in parts:
        if p is anchor:
            continue
        s = size(p)
        if p["hi"][2] <= plane_z + 0.03:
            continue                      # at or under the plane: mattress/frame
        if plan_area(p) >= BEDDING_PLAN_FRAC * drawn_plan_m2:
            continue                      # the bedding field itself
        if s[2] < min(s[0], s[1]):
            out.append(p)
    return out


def frame_cluster(parts, anchor, pad_m=0.02):
    """The parts the SCALE is fitted on: the anchor plus anything whose plan
    lies inside the anchor's plan bbox (padded). Bedding drape that overhangs
    the frame and attached side furniture that widens it stay OUT of the
    denominator — the audition's own fill note: 'the integration hook must fit
    on the FRAME cluster, not the file bbox'."""
    cluster = [anchor]
    for p in parts:
        if p is anchor:
            continue
        if (p["lo"][0] >= anchor["lo"][0] - pad_m and p["hi"][0] <= anchor["hi"][0] + pad_m
                and p["lo"][1] >= anchor["lo"][1] - pad_m and p["hi"][1] <= anchor["hi"][1] + pad_m):
            cluster.append(p)
    return cluster


def verdict(row):
    """The audition's hard filters, applied to a measured row (mm/px-free: all
    booleans derived upstream). Returns (ok, [reasons])."""
    why = []
    if not row.get("anchor_found"):
        why.append("no bed-scale anchor part at any unit factor")
    if row.get("orientation") == "unresolved":
        why.append("head end unresolvable — placement would be a coin flip (R9)")
    fill_l, fill_w = row.get("fill_len", 0.0), row.get("fill_w", 0.0)
    if fill_l < MIN_FILL or fill_w < MIN_FILL:
        why.append(f"fills {fill_l:.2f}x{fill_w:.2f} of the drawn footprint (< {MIN_FILL})")
    foot = row.get("foot_over_plane_m")
    if foot is None:
        # could-not-measure must never read as clean (the repo's exit-2 law)
        why.append("foot rise UNMEASURED (no sleeping plane after placement)")
    elif foot > FOOT_ABOVE_PLANE_M:
        why.append(f"footboard {foot*1000:.0f} mm over the plane — the ink draws none")
    if row.get("headboard_fused"):
        why.append("own headboard fused with the bed — collides with the sheet-drawn band (SR-18)")
    return (not why), why
