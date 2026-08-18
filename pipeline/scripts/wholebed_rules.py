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
    return (not why), why
