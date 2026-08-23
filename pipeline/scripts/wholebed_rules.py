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


def plan_overlap_frac(p, anchor):
    """Fraction of p's PLAN area lying over the anchor's plan bbox (0..1).

    The premise it carries (p2r54): A PART OF THE BED LIES ON THE BED. Bedding
    covers the mattress, pillows lean on it, a foot throw crosses it — every
    made-bed layer puts most of its plan over the frame. Furniture that RIDES
    ALONG in the file (flanking cabinets, a backdrop headboard wall) stands on
    the floor BESIDE or BEHIND the frame, so most of its plan lies off it.
    Measured on the candidate that forced the rule (81d895fd, native m):
    duvet 0.86, foot throw 0.79, pillows ~1.0 / closet bodies 0.02, backdrop
    wall panels 0.10-0.24. The gap between the two families is wide."""
    ax0, ax1 = max(p["lo"][0], anchor["lo"][0]), min(p["hi"][0], anchor["hi"][0])
    ay0, ay1 = max(p["lo"][1], anchor["lo"][1]), min(p["hi"][1], anchor["hi"][1])
    inter = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    a = plan_area(p)
    return (inter / a) if a > 0 else 0.0


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
    """The part the bed is ORGANISED around: largest plan area whose long axis
    sits in the anchor band. None -> the file holds no bed at this scale.

    It is the FRAME on every upholstered bed, and it is the right part for
    strip / orientation / field premises ("a part of the bed lies ON the bed").
    It is NOT the bed's size: the spec slot is a mattress size, and the
    mattress is pick_mattress (D-120) — the bench fitted this part into the
    mattress slot for four rounds and refused real king beds for it."""
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


# ------------------------------------------------ the mattress (P2r-58, D-120) --
# INSTRUMENT WRONG, SIXTH TIME IN THE D-109 CLASS (the anchor names the wrong
# part). pick_anchor returns the part the bed is ORGANISED around — the largest
# plan in the bed band — which on every upholstered bed is the FRAME (Metropol
# 'Bed Frame' 1842 x 2033, Obsidian 'Base' 2023 x 2179, Bolzan 'body bed'
# 1842 x 2144). The bench then fitted THAT part into the spec's slot, which is
# a MATTRESS size (2000 x 1800, D-114), shrank every frame by its own rails
# (0.84 / 0.85 / 0.91), and asked whether the shrunken FRAME was a standard
# MATTRESS. Metropol's mattress measures 1786 x 1980 native — the Thai 6 ft
# king to within 14 / 20 mm, at scale 1.0 — and was refused as "no standard
# size". A frame is not a mattress; the slot is a mattress slot; the rule
# below names the mattress by GEOMETRY so the size and the scale read it.
#
# THE PREMISE: the mattress is THE SLAB BETWEEN THE FRAME AND THE BEDDING —
# it lies on the frame's plan, rests above the frame's bottom (cloth falls
# past it; a platform sits on the floor), is slab-thick, and presents a
# CONTINUOUS FLAT TOP. The last clause needs a probe, not a bbox: measured on
# eleven cached candidates (wholebed_dump.py, 2026-08-23) the seam-piping
# meshes that share a slab's footprint hold no surface (cover 0.00-0.14), and
# authors delete the hidden faces of a real mattress under its bedding (Bolzan
# 'mattres' cover 0.25, Loca Loft 0.50), so the cover floor sits between the
# two families. Folds separate bedding from a slab (blankets relief 24-60 mm;
# mattresses and fitted sheets 0-19), half-bed throws fail the span (0.28-0.57
# of the frame's short axis vs 0.64-1.0 for mattresses), thin plates fail the
# thickness band (base plates 35-59 mm), and a draped duvet fails the floor
# term (its hem reaches 0-12 mm above the frame's bottom). Among survivors the
# LOWEST top is the mattress (a sheet or flat quilt LIES ON it, never under
# it); ties within MATT_TOP_TIE_M go to the largest plan. A part with no probe
# facts can never qualify — could-not-measure must not read as a mattress.
MATT_OVERLAP_MIN = 0.80        # lies on the frame's plan
MATT_ABOVE_FLOOR_M = 0.05      # rests above the frame's bottom (hook's term)
MATT_THICK_M = (0.10, 0.45)    # a slab, not a plate and not a draped stack
MATT_COVER_MIN = 0.15          # seams 0.00-0.14 / hidden-face mattresses 0.25+
MATT_RELIEF_M = 0.02           # flat top: mattresses 0-19 mm, blankets 24+
MATT_SPAN_FRAC = 0.60          # spans the frame's axes: throws <= 0.57
MATT_TOP_TIE_M = 0.01


def _has_facts(p):
    return (p.get("cover") is not None and p.get("relief") is not None
            and p.get("top_med") is not None)


def _stacked_above(q, p, tol=0.02):
    """q sits ENTIRELY above p's top — a mattress on a slat deck or a divan
    base. Cloth lying on a mattress fails this test by construction: it drapes
    over the sides, so its bbox bottom is far below the slab's top. That is
    what separates 'p is a deck under the mattress' (p is excluded) from
    'p is the mattress under a coverlet' (p is kept)."""
    return (plan_overlap_frac(q, p) >= MATT_OVERLAP_MIN
            and q["lo"][2] >= p["hi"][2] - tol)


def pick_mattress(parts, anchor, drawn_plan_m2=3.6):
    """(part, note) — the mattress slab by geometry, or (None, why).

    `parts` carry bbox + the probe facts (cover / top_med / relief, metres;
    wholebed_dump.surface_facts). `anchor` is pick_anchor's organising part;
    it competes too, but only when something of the bed stands UNDER it
    (starts >= MATT_ABOVE_FLOOR_M below its bottom, on its plan) — Ikea's
    'Bedsheets' out-planned its own frame by 1% and became the anchor; the
    frame beneath is what makes it a mattress and not a platform.

    Among qualifying slabs: a slab with ANOTHER slab stacked entirely above it
    is a deck or an inner base, never the mattress (a 100 mm slat deck inside
    the rails would otherwise win on 'lowest top'); then the LOWEST top (cloth lies on
    the mattress); ties within MATT_TOP_TIE_M go to the slab CONTAINED in the
    other's plan (the cloth that covers a mattress out-plans it — a hotel
    coverlet wider than the slab must not win the tie), else the larger plan.

    A file with no qualifying slab returns (None, reason): a one-mesh bed
    (Tierra) or a mattress split across meshes. The caller must then record
    the size as UNMEASURED — never fall back to the frame (R10: typing a number
    for an unmeasurable dimension is the defect)."""
    if anchor is None:
        return None, "no anchor"
    a_lo_z = anchor["lo"][2]
    a_s = size(anchor)
    cands, probed = [], 0
    for p in parts:
        if not _has_facts(p):
            continue
        probed += 1
        s = size(p)
        if plan_overlap_frac(p, anchor) < MATT_OVERLAP_MIN:
            continue
        if not (MATT_THICK_M[0] <= s[2] <= MATT_THICK_M[1]):
            continue
        if p["cover"] < MATT_COVER_MIN or p["relief"] > MATT_RELIEF_M:
            continue
        if s[0] < MATT_SPAN_FRAC * a_s[0] or s[1] < MATT_SPAN_FRAC * a_s[1]:
            continue
        if p is anchor:
            under = [q for q in parts if q is not p
                     and q["lo"][2] <= p["lo"][2] - MATT_ABOVE_FLOOR_M
                     and plan_overlap_frac(q, p) >= MATT_OVERLAP_MIN]
            if not under:
                continue
        elif p["lo"][2] < a_lo_z + MATT_ABOVE_FLOOR_M:
            continue
        cands.append(p)
    if probed == 0:
        return None, "no part carries probe facts (cover/top_med/relief) — unprobed"
    if not cands:
        return None, ("no slab between frame and bedding qualifies — a one-mesh "
                      "bed, or a mattress split across meshes")
    decks = [p for p in cands if any(q is not p and _stacked_above(q, p) for q in cands)]
    tops = [p for p in cands if p not in decks] or cands
    low = min(p["top_med"] for p in tops)
    tied = [p for p in tops if p["top_med"] <= low + MATT_TOP_TIE_M]
    if len(tied) > 1:
        inner = [p for p in tied
                 if any(q is not p and plan_overlap_frac(p, q) >= 0.95 for q in tied)]
        if inner:
            tied = inner
    best = max(tied, key=plan_area)
    note = f"{len(cands)} candidate slab(s); lowest top {low * 1000:.0f} mm"
    if decks:
        note += f"; {len(decks)} deck(s) under another slab excluded"
    return best, note


def mattress_scale(m_len, m_w, fit_len=2.000, fit_w=1.800):
    """Uniform scale that lands the MATTRESS in the spec's slot, never above
    MAX_SCALE (R8 / D-101: shrink is a transform, stretch is a fake bed).
    The frame then overhangs the slot by its own rails — that overhang is
    reported, and the owner's order is to move the surroundings to it
    (2026-08-22: "หาขนาดมาตรฐานแล้วปรับของรอบ ๆ ให้มาชิด"), never to shrink
    the bed into the mattress slot. Returns s or None."""
    if m_len <= 0 or m_w <= 0:
        return None
    return min(MAX_SCALE, fit_len / m_len, fit_w / m_w)


# The bare-mattress test is +-50 mm (knowledge/ergonomics/tv-viewing-and-
# furniture-dimensions.md:45 and :124 — "the same +-~50 mm bare-mattress test
# as the US table; built ACQ clusters include the frame, so the machine judges
# those at +-150"). ergonomics_ref.BED_SIZE_TOL_MM = 150 is the CLUSTER
# tolerance (dim_check reads a plan union that includes the frame; D-116).
# The bench's number is now the bare slab, so the bare rule applies here —
# the 150 would let a 1,671 mm EU-160 mattress print as a US queen (1,524).
# Deviations between the two lines are the OWNER's discretion from the image
# (D-110), never a number the builder widens.
MATT_STD_TOL_MM = 50


def best_uniform_fit(m_w_mm, m_len_mm, sizes, max_scale=None, steps=200):
    """(s, name, worst_mm) — the uniform scale in [0.80, MAX_SCALE] that
    brings a W x L mattress CLOSEST to any standard in `sizes` ({name:(W,L)}),
    orientation-agnostic. Reported beside the slot-fit so a row can say "no
    uniform scale reaches a standard" rather than leaving the reader to
    wonder whether a different scale would have passed. PURE."""
    if m_w_mm <= 0 or m_len_mm <= 0 or not sizes:
        return None, None, None
    top = MAX_SCALE if max_scale is None else max_scale
    a0, b0 = sorted((float(m_w_mm), float(m_len_mm)))
    best = (None, None, None)
    for i in range(steps + 1):
        sc = 0.80 + (top - 0.80) * i / steps
        a, b = a0 * sc, b0 * sc
        for name, (bw, bl) in sizes.items():
            sw, sl = sorted((bw, bl))
            worst = max(abs(a - sw), abs(b - sl))
            if best[2] is None or worst < best[2]:
                best = (round(sc, 4), name, worst)
    return best


# THE DRAWN BED IS THE WIDEST FRAME THE SHEET ALLOWS (R12). With the scale read
# off the mattress, nothing shrinks a wide frame into the slot any more (the
# old cluster fit did that by construction — and refused real king beds for
# it). The cap is the DRAWN bed rectangle (sheet-recon SR-07, 7' x 6.5'), read
# from qa/sheet-recon.json by the bench, never typed: the slot (mattress) sits
# inside it, and the HARD frame may reach it but not pass it. It is the frame
# and not the cluster because the ink draws the bed's edge and the owner's
# clause moves the surroundings to the FRAME — a sheet draping 118 mm down each
# flank (Metropol) or a duvet foot (81d895fd, +71) is cloth over the gap, not a
# wider bed. Cloth and carry-on extents are REPORTED (cluster_overhang_mm,
# neighbour_clearance_mm), never the verdict. Tolerance = the ink read's own.
MADE_BED_INK_TOL_M = 0.010


def made_bed_within_ink(made_w_m, made_len_m, ink_w_m, ink_len_m,
                        tol=MADE_BED_INK_TOL_M):
    """(ok, over_w_mm, over_len_mm) — how far a staged extent (the FRAME, per
    verdict) reaches past the drawn bed rectangle, per axis (0 inside). PURE."""
    over_w = max(0.0, made_w_m - ink_w_m - tol) * 1000.0
    over_l = max(0.0, made_len_m - ink_len_m - tol) * 1000.0
    return (over_w <= 0.0 and over_l <= 0.0), int(round(over_w)), int(round(over_l))


def neighbour_gaps(frame_lo, frame_hi, others, far_m=1.5, run_m=0.05):
    """Per side (N = +y, S = -y, W = foot = -x, E = head = +x), the gap in mm
    from the staged FRAME's face to the nearest thing standing beside it — the
    number the owner's "move the surroundings to the bed" clause needs (D-114
    override). NEGATIVE = it overlaps the frame by that much, however deep.

    Which side a thing is ON is the side it penetrates LEAST (argmax of the
    four face gaps), provided it overlaps the frame's run along the other axis
    by at least `run_m`. Two wrong answers paid for that sentence: a 100 mm
    look-past-the-face window named the wardrobe 687 mm away on a side where
    a night table sat 126 mm INTO the frame, and a centre-of-plan test put the
    foot bench — which the frame overhung by 177 mm — on the N side because its
    centre lay a float above the frame's. A band part 1 mm past the head face
    is an E neighbour, never an S one.

    `others` = [(name, lo, hi)] of scene meshes — not the candidate's own parts
    — already filtered to the bed's height band by the caller (floor, rug and
    ceiling are not neighbours). Things farther than `far_m` are not reported;
    per side the DEEPEST (smallest) gap is kept. PURE."""
    fx0, fy0 = frame_lo[0], frame_lo[1]
    fx1, fy1 = frame_hi[0], frame_hi[1]
    out = {"N": None, "S": None, "W": None, "E": None}
    for name, lo, hi in others:
        gaps = {"N": lo[1] - fy1, "S": fy0 - hi[1], "W": fx0 - hi[0], "E": lo[0] - fx1}
        side = max(gaps, key=gaps.get)
        g = gaps[side]
        if g > far_m:
            continue
        if side in ("N", "S"):
            run = min(hi[0], fx1) - max(lo[0], fx0)
        else:
            run = min(hi[1], fy1) - max(lo[1], fy0)
        if run < run_m:
            continue
        g_mm = int(round(g * 1000.0))
        if out[side] is None or g_mm < out[side]["gap_mm"]:
            out[side] = {"gap_mm": g_mm, "object": name}
    return out


# THE FRAME, by geometry (review of D-120: pick_anchor is cloth on 4 of 11
# candidates — Ikea's sheet, two quilts, the in-frame bed's draped sheet — so
# the ink cap, the overhang and the clearance were reading a quilt's drape as
# "the frame"; Cloudrest's base 70 mm past the drawn bed read INSIDE). The
# frame is the HARD STACK under and around the mattress: parts that do not
# rise above the mattress top by more than a rim, lie on its plan, and are
# either HOLLOW (a rail ring, a slat frame — cover under MATT_COVER_MIN) or a
# FLAT SLAB whose top sits BELOW the mattress top (a base, a deck; the
# mattress itself). Cloth lying ON the mattress has its top at or above the
# mattress top and is excluded — that, not thickness, is what keeps a foot
# sheet or a flat blanket out of the frame's width. Per axis a part counts
# only if it spans most of the mattress on the OTHER axis (a rail runs the
# length; a 576 mm foot strip does not set the width). Known over-read: a
# draped quilt's SEAM mesh (hollow, low) adds ~60 mm/side on two of the
# eleven cached files (Slate, Cloudrest) — reported with the part names.
FRAME_RIM_M = 0.10
FRAME_SPAN_FRAC = 0.60


def frame_extent(parts, mattress):
    """((lo_x, lo_y), (hi_x, hi_y), [names]) of the hard frame around
    `mattress`, or None when no hard part qualifies (the mattress alone is
    then the frame's extent — a mattress on the floor)."""
    if mattress is None:
        return None
    m_top = mattress["top_med"]
    m_s = size(mattress)
    hard = []
    for p in parts:
        if p is mattress:
            hard.append(p)
            continue
        if not _has_facts(p) and p.get("cover") is None:
            continue
        if p["hi"][2] > m_top + FRAME_RIM_M:
            continue
        if plan_overlap_frac(p, mattress) < 0.5 and plan_overlap_frac(mattress, p) < 0.5:
            continue
        hollow = (p.get("cover") or 0.0) < MATT_COVER_MIN
        flat = (p.get("relief") is not None and p["relief"] <= MATT_RELIEF_M
                and p.get("top_med") is not None and p["top_med"] <= m_top - 0.02)
        if hollow or flat:
            hard.append(p)
    lo_x = min(p["lo"][0] for p in hard if size(p)[1] >= FRAME_SPAN_FRAC * m_s[1])
    hi_x = max(p["hi"][0] for p in hard if size(p)[1] >= FRAME_SPAN_FRAC * m_s[1])
    lo_y = min(p["lo"][1] for p in hard if size(p)[0] >= FRAME_SPAN_FRAC * m_s[0])
    hi_y = max(p["hi"][1] for p in hard if size(p)[0] >= FRAME_SPAN_FRAC * m_s[0])
    return (lo_x, lo_y), (hi_x, hi_y), [p["name"] for p in hard]


def overhang_staged_mm(frame_lo, frame_hi, fx0, fy0, fx1, fy1):
    """How far the STAGED frame reaches past the slot rectangle, from where it
    actually stands (the head butts the built band, which this room's spec
    emits INSIDE the slot — 60 mm of the 2000 belongs to the band, so a foot
    measured from extents alone under-reads by that much). Positive = past the
    slot; 0 inside. Integers in mm."""
    return {"foot": int(round(max(0.0, fx0 - frame_lo[0]) * 1000)),
            "head": int(round(max(0.0, frame_hi[0] - fx1) * 1000)),
            "side_S": int(round(max(0.0, fy0 - frame_lo[1]) * 1000)),
            "side_N": int(round(max(0.0, frame_hi[1] - fy1) * 1000))}


def mattress_fill(proj_w_mm, proj_len_mm, slot_w_mm, slot_len_mm):
    """The MATTRESS itself against the slot, per axis (capped at 1). The field
    rule reads the soft mass and passed a 1336 mm 'full' mattress under a
    1641 mm quilt at 0.91 — the bed-too-small premise applied to the slab is
    this number, held to the same MIN_FILL (one ink, one premise)."""
    if slot_w_mm <= 0 or slot_len_mm <= 0:
        return 0.0, 0.0
    return (min(1.0, proj_w_mm / slot_w_mm), min(1.0, proj_len_mm / slot_len_mm))


def overhang_mm(ext_len_m, ext_w_m, fit_len=2.000, fit_w=1.800):
    """How far a staged extent reaches PAST the slot: foot (all of the length
    overhang, since the head butts the band) and per side (centred). Zero
    when inside. Integers in mm."""
    foot = max(0.0, ext_len_m - fit_len) * 1000.0
    side = max(0.0, (ext_w_m - fit_w) / 2.0) * 1000.0
    return {"foot": int(round(foot)), "side_each": int(round(side))}


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


# The flatness test alone cannot tell a lying accent band from a lying pillow —
# f52472c1's plaid presents 0.60 of its smallest plan dimension, 81d895fd's
# flattest pillow 0.79, and that gap is too narrow to carry a rule. What
# separates the measured families is WHERE THEY LIE: the pillow BANK presses
# against the head (81d895fd's four pillows end 0.02-0.23 m from the head
# edge), an accent band lies out on the bedding field (the plaid's near edge is
# 0.70 m from the head). The first cut of this rule had no head term at all and
# ate two of 81d895fd's pillows at integration — the same single-candidate
# calibration the field's thin-panel exemption paid for the same hour (R9b in
# threshold form). 0.45 sits in the measured gap.
FLAT_ACCENT_HEAD_M = 0.45


def flat_accents_on_bank(parts, plane_z, anchor=None, drawn_plan_m2=4.298,
                         head_x=None, head="hi"):
    """Lying-flat decor bands ON THE FIELD, away from the pillow bank: above
    the plane, too small to be the bedding field, presented height under their
    own smallest plan dimension, and lying farther than FLAT_ACCENT_HEAD_M
    from the head edge (the bank presses against the head; an accent band lies
    out on the bedding). With no head_x the head term is skipped — the
    pre-p2r54 behaviour, kept only so old callers fail loudly in tests rather
    than silently pass a band. Bedding (the duvet field) is exempted first by
    plan share."""
    out = []
    for p in parts:
        if p is anchor:
            continue
        s = size(p)
        if p["hi"][2] <= plane_z + 0.03:
            continue                      # at or under the plane: mattress/frame
        if plan_area(p) >= BEDDING_PLAN_FRAC * drawn_plan_m2:
            continue                      # the bedding field itself
        if s[2] >= min(s[0], s[1]):
            continue                      # presents its depth: a pillow, kept
        if head_x is not None:
            d_head = (head_x - p["hi"][0]) if head == "hi" else (p["lo"][0] - head_x)
            if d_head < FLAT_ACCENT_HEAD_M:
                continue                  # pressed against the head: the bank
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


# ------------------------------------------------- the made-bed field (P2r-53) --
# ORD-2026-08-18-bed-too-small: the owner failed p2r52's bed from the image
# ("ผมว่าเตียงมันเล็กเกินไป") and the measurement agreed. The drawn 7'x6.5'
# rectangle IS the made bed — duvet to the edges, the same ink read this audition
# archived — but MIN_FILL judged the WHOLE kept bed, so f52472c1's integral hard
# wings (platform 3159 native around a true-king 1827 mattress) carried a narrow
# bed through the width test: at the wing-capped scale 0.68 the mattress lands at
# 1243 mm of the drawn 2149 (0.58) and the bedding field at 1541 (0.72). What was
# missing is one sentence: THE SOFT MASS THAT VISUALLY IS THE BED — mattress,
# bedding, pillow bank — MUST REACH THE DRAWN RECTANGLE. Hard parts keep the
# inside-the-rect duty they already had (the cluster fit); this rule adds the
# soft half. Same constant as MIN_FILL: one ink, one premise.
SOFT_ABOVE_ANCHOR_M = 0.01
# A thin STANDING panel rising above the anchor is hard furniture (the burl head
# panel survives to integration exactly this way); bedding is never plate-thin
# in one plan axis while standing several times its own thickness tall.
SOFT_PANEL_THIN_M = 0.06
MIN_FIELD_FILL = MIN_FILL


# A made-bed layer puts at least half its plan over the frame (plan_overlap_frac's
# own premise). CALIBRATION DEBT PAID p2r54: without this predicate the field
# admitted 81d895fd's 163 mm-thick backdrop headboard WALL — a floor-standing
# panel 2,759 mm wide, 590 mm past the frame each side — because the thin-panel
# exemption below was frozen at 60 mm against ONE candidate's burl panel (R9b's
# sentence, in threshold form: a rule calibrated on the object it applies to
# will exempt the next one). That panel's width WAS the bench's 'field 2149,
# fill 1.00' — the first-ever field pass was the wall, not the bed. It also
# admitted f0938871's fused hard FRAME (976 mm tall) as field width. Both
# corrected rows: qa/blenderkit-search-log.json wholebed_2026_08_18.
FIELD_MIN_OVERLAP = 0.5


def made_field(parts, anchor):
    """The parts forming the MADE-BED FIELD: everything rising above the
    anchor's top face that LIES ON THE BED (plan overlap >= FIELD_MIN_OVERLAP),
    except thin standing panels. Selection heuristic for the bench, where no
    roles exist yet; the integration hook passes its own role-resolved parts
    straight to field_fill instead."""
    top = anchor["hi"][2]
    out = []
    for p in parts:
        if p is anchor:
            continue
        if p["hi"][2] <= top + SOFT_ABOVE_ANCHOR_M:
            continue
        s = size(p)
        thin = min(s[0], s[1])
        if thin <= SOFT_PANEL_THIN_M and s[2] > 3 * thin:
            continue
        if plan_overlap_frac(p, anchor) < FIELD_MIN_OVERLAP:
            continue
        out.append(p)
    return out


def carry_ons(parts, plane_z, anchor):
    """Furniture riding along in the candidate's file: non-anchor parts whose
    plan mostly lies OFF the frame (plan_overlap_frac < FIELD_MIN_OVERLAP).
    Returns [(part, why)].

    Two families, one premise, two printed reasons: BELOW the plane they are
    flanking cabinets (this room's nightstands are owner millwork the sheet
    draws — R12; a candidate's own bedside units duplicate them the way its
    own headboard duplicates the band); rising TO or OVER the plane they are
    backdrop panelling (81d895fd ships a two-layer fabric headboard WALL wider
    than the bed). BOUNDARY, said plainly: a candidate whose side drape is a
    SEPARATE mesh hanging fully off the frame would be eaten by this rule —
    and the field check downstream would then FAIL LOUDLY on the missing
    width, never silently ship a stripped bed. No such candidate exists in
    the 20 stagings measured to date (every duvet mesh overlaps its frame
    0.79+)."""
    out = []
    for p in parts:
        if p is anchor:
            continue
        if plan_overlap_frac(p, anchor) >= FIELD_MIN_OVERLAP:
            continue
        if p["hi"][2] < plane_z - 0.05:
            out.append((p, "flanking cabinet riding along in the file — the "
                           "sheet draws this room's nightstands (R12)"))
        else:
            out.append((p, "backdrop panelling riding along in the file — the "
                           "band is the headboard of record (R12)"))
    return out


def field_fill(field_parts, fit_len=2.000, fit_w=2.149, axis_len=0):
    """Fill of the field's plan union against the drawn rectangle, at the
    CURRENT scale of the parts (call after fitting). Returns (fill_len,
    fill_w); (0.0, 0.0) when no field exists — could-not-measure must never
    read as clean (the exit-2 law)."""
    if not field_parts or fit_len <= 0 or fit_w <= 0:
        return 0.0, 0.0
    al, aw = axis_len, 1 - axis_len
    lo_l = min(p["lo"][al] for p in field_parts)
    hi_l = max(p["hi"][al] for p in field_parts)
    lo_w = min(p["lo"][aw] for p in field_parts)
    hi_w = max(p["hi"][aw] for p in field_parts)
    return min(1.0, (hi_l - lo_l) / fit_len), min(1.0, (hi_w - lo_w) / fit_w)


def field_verdict(ffl, ffw, signed=None):
    """Three-state outcome for the staged made-bed field (the integration
    hook's side of ORD-2026-08-18-bed-too-small):

      "pass"    — the field reaches the drawn rectangle; nothing to say.
      "interim" — the field falls short AND a SIGNED deficit rides in the spec
                  (a dict naming decision + ask). The build proceeds LOUDLY:
                  the deficit prints at every gate, ages with its ask, and the
                  frame is not shippable as the drawn bed. This is the R13
                  third state — the free shelf was measured to exhaustion
                  (18 in-room stagings + 2 showroom probes, widest field
                  1,910 mm of a drawn 2,149) and what clears it is a purchase
                  only the owner can make. NOT an opt-out: the signature is a
                  register row, printed, never a flag someone forgets to type.
      "fail"    — the field falls short and nothing signed says so. Hard stop.

    `signed` must carry non-empty 'decision' and 'ask' keys to count."""
    if ffl >= MIN_FIELD_FILL and ffw >= MIN_FIELD_FILL:
        return "pass"
    if isinstance(signed, dict) and signed.get("decision") and signed.get("ask"):
        return "interim"
    return "fail"


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
    ffl, ffw = row.get("field_fill_len"), row.get("field_fill_w")
    if ffl is None or ffw is None:
        why.append("made-bed field UNMEASURED — a row from before the size rule "
                   "existed; re-bench it (ORD-2026-08-18-bed-too-small)")
    elif ffl < MIN_FIELD_FILL or ffw < MIN_FIELD_FILL:
        why.append(f"made-bed field fills {ffl:.2f}x{ffw:.2f} of the drawn "
                   f"rectangle (< {MIN_FIELD_FILL}) — the bed reads smaller than "
                   f"the ink draws it (ORD-2026-08-18-bed-too-small)")
    # FRONT DOOR (ORD-2026-08-22-front-door-dims): the projected mattress must be
    # SOME standard bed's size. The field rule asks "does it reach the slot"; this
    # asks "is it a real bed at all" — the p2r52 winner answered yes to neither and
    # was refused by nothing. Keys ride the bench (anchor_projected_mm/anchor_std);
    # a staged row without them is from before this rule and must re-bench.
    std = row.get("anchor_std")
    if std is None:
        why.append("projected-anchor standard size UNMEASURED — a row from before "
                   "the front-door rule existed; re-bench it "
                   "(ORD-2026-08-22-front-door-dims)")
    elif std.get("unmeasured"):
        # D-120: the size anchor is the MATTRESS, found by geometry. A file
        # where none qualifies gets no number typed for it (R10) — the front
        # door is not answered, and not-answered is a refusal, never a pass.
        why.append(f"mattress size UNMEASURABLE — {std['unmeasured']}; the front "
                   f"door cannot be answered for this file "
                   f"(ORD-2026-08-22-front-door-dims, D-120)")
    elif std.get("tol_mm") is None or std.get("part") is None or std.get("slot_mm") is None:
        # a pre-D-120 row: the FRAME projected at the cluster's +-150. It must
        # not read as a bare-mattress pass (the chunkA Bolzan row did).
        why.append("front door measured on the FRAME at +-150 — a row from before "
                   "D-120 (no tol_mm/part/slot_mm); re-bench it")
    elif not std.get("within"):
        na = std.get("nearest_any") or {}
        bu = std.get("best_uniform") or {}
        tail = ""
        if na.get("name") and na.get("name") != std.get("name") and na.get("worst_mm") is not None \
                and na["worst_mm"] <= std.get("tol_mm", MATT_STD_TOL_MM):
            tail += (f"; it IS a {na['name']} (within {na['worst_mm']} mm) — a standard "
                     f"other than the slot's: change the spec's w/d (D-114 reverse_by) "
                     f"or a different purchase")
        elif bu.get("scale") is not None:
            tail += (f"; best uniform scale {bu.get('scale')} reaches {bu.get('name')} "
                     f"within {bu.get('worst_mm')} mm")
        why.append(f"projected mattress {row.get('anchor_projected_mm')} mm is "
                   f"{std.get('worst_mm')} mm from the slot's standard {std.get('name')} "
                   f"{std.get('slot_mm')} (bare-mattress tol +-{std.get('tol_mm')}){tail} "
                   f"— ORD-2026-08-22-front-door-dims")
    mf = row.get("mattress_fill")
    if std is not None and not std.get("unmeasured") and std.get("part") is not None:
        if mf is None:
            why.append("mattress-vs-slot fill UNMEASURED — re-bench (D-120)")
        elif mf[0] < MIN_FILL or mf[1] < MIN_FILL:
            why.append(f"the mattress itself fills {mf[0]:.2f}x{mf[1]:.2f} of the slot "
                       f"(< {MIN_FILL}) — a smaller bed under wider bedding "
                       f"(ORD-2026-08-18-bed-too-small applied to the slab, D-120)")
    # THE INK CAP (D-120): the staged FRAME must stay inside the drawn bed rect.
    fr, ink = row.get("frame_staged_mm"), row.get("ink_bed_mm")
    if fr is None or ink is None:
        why.append("frame vs drawn bed rectangle UNMEASURED — no staged frame "
                   "extent or no SR bed row read; could-not-look never counts as "
                   "inside (R12, D-120)")
    else:
        ok, ow, ol = made_bed_within_ink(fr[0] / 1000.0, fr[1] / 1000.0,
                                         ink[0] / 1000.0, ink[1] / 1000.0)
        if not ok:
            why.append(f"frame {fr[0]}x{fr[1]} mm passes the drawn bed rectangle "
                       f"{ink[0]}x{ink[1]} (SR-07) by {ow} mm across / {ol} mm long "
                       f"— the sheet draws the widest bed this room takes (R12)")
    return (not why), why
