"""
millwork.py — procedural BUILT-IN joinery + the model-fit gate. Pure Python (NO bpy).

Same contract as furniture.py: builders return a list of boxes
  (name, x, y, z, dx, dy, dz)
that a materializer (build_room.py) turns into geometry — so this is unit-testable with plain
`python`, and the CAD invariant is provable rather than assumed (see test_millwork.py).

!! UNITS: METRES. furniture.py next door works in INCHES. Do not mix them. Every constant,
argument and returned box in this module is metres; build_room converts mm -> m before calling.

WHY THIS MODULE EXISTS (2026-07-12)
-----------------------------------
Built-ins were ONE `add_box` each. The pro critic's "the wardrobe is a texture-mapped box with
basic hardware" was therefore a literal description of the code, not an aesthetic opinion — and no
purchase fixes it: built-in millwork is bespoke geometry at project mm, and there is no CC0
wardrobe in existence anyway (docs/DECISIONS-render-assets.md, 2026-07-12). So we generate it, and
the generator then serves every future project's built-ins.

WHAT THE REPAINT ACTUALLY READS is the SHADOW LINE, not the geometry width. A real 3 mm joinery
reveal is ~1 px at render scale — but a 3 mm gap that is 20 mm DEEP casts a dark line that
survives downsampling into the Gemini control image. So every cue here is a real, dimensionally
honest recess: leaves standing proud of a set-back carcass, a recessed toe-kick, a handleless top
pull-gap, battens on a backer. We never fatten a dimension to make it visible; we give it depth so
it casts. (That is also why hardware is NOT modelled protruding: a bar handle would stick out past
the plan-measured bbox, and the pull-gap is both the honest warm-minimal detail and bbox-safe.)
"""
import math

# --- joinery constants (metres) -----------------------------------------------------------------
T_DOOR   = 0.020    # door-leaf thickness: leaves stand proud of the carcass by this
REVEAL   = 0.003    # shadow gap between leaves (a real joinery reveal)
PLINTH_H = 0.080    # toe-kick height
PLINTH_R = 0.018    # toe-kick set-back from the door face
PULL_H   = 0.030    # handleless top pull-gap — this IS the hardware (warm-minimal brief)
LEAF_W   = 0.550    # target door-leaf width; the leaf COUNT is derived from the run
SLAT_W   = 0.045    # batten width (headboard slat wall) — DEFAULT; a builtin's design block overrides
SLAT_GAP = 0.022    # batten gap
SLAT_PR  = 0.018    # batten proudness off the backer
TOP_T    = 0.040    # worktop thickness (low / desk millwork)
TOP_REC  = 0.030    # carcass set-back under the worktop lip

# --- open dressing-wall constants (an OPEN wardrobe: NO leaves, you see INTO it) -----------------
# element-1 (PRJ-2026-002 BF09-3, owner-signed D3/D4/D6 2026-07-16). Same shadow-line law as the
# door run: every cue is a real recess/proudness that casts, never a fattened dimension.
CARC_T    = 0.018   # carcass panel thickness (back / gables / shelves / top)
RAIL_D    = 0.030   # brass hang-rail section (round rail modelled square; Ø25-28 D4-A)
SHELF_LIFT = 0.102  # rod-to-shelf-above clearance (hanger lift-off; Ask1 ergonomics)
DRAWER_H  = 0.240   # floating-drawer face height
DRAWER_REV = 0.010  # reveal between stacked drawer faces — 6mm was cabinet-true but
#                     rendered invisible at the deliverable camera distance (round-6
#                     lane C, C2#14 read the stack as sealed boxes); 10mm is still a
#                     handleless shadow line, and now it survives the frame
FLOAT_Z   = 0.450   # the drawer stack FLOATS — air/shadow reveal below it (D3-A)

# ELEMENT-3 nightstand joinery + dome-lamp stack (round-6 lane C). PUBLISHED so the
# bpy layer derives the shade's emission-gradient window from the SAME numbers that
# place the shade — the old hand-copied 0.035/0.17/0.15 in build_room was the
# hardcode-drift class waiting to fire on exactly this rescale.
LAMP_BASE_H  = 0.040   # brass base height
LAMP_STEM_H  = 0.200   # stem height
LAMP_SHADE_H = 0.190   # drum shade height
# THE DOME AND ITS BULB — one definition, because two produced a light OUTSIDE its own
# shade. build_room materialises the shade envelope above as a spun dome of height
# min(dz, r * LAMP_DOME_H_OVER_R) with its rim at the envelope's oz, and a bulb spanning
# oz+LAMP_BULB_DZ0 .. oz+LAMP_BULB_DZ1 under it. Those three numbers used to live only in
# build_room, while element5_lighting derived the practical's z from a HARDCODED PROBE
# cabinet (0.5, 0.5, 0.52) that exists nowhere in the spec. D-115 then re-slotted the real
# cabinet 501 -> 400 mm and the two halves parted company: the shade apex fell to 704.3 mm
# while the point light stayed at 715.0 mm — 10.7 mm ABOVE the dome it is supposed to be
# inside. Both lamps in every frame since p2r57 carry a blown-out white ellipse burned on
# TOP of the brass, the slats above them glow, and the deck under them stays dead grey.
# R9's law is why it is here and not there: a position derivable from a contact must never
# be typed, and a probe constant IS a typed position wearing a derivation's name.
LAMP_DOME_H_OVER_R = 0.62   # mushroom proportion: dome height / shade radius
LAMP_BULB_DZ0      = 0.005  # bulb bottom, relative to the shade envelope's oz — POSITIVE
                            # since p2r72: the old -0.005 hung the glass 5 mm below the
                            # rim (C2-p2r62#1 "stem สว่างใต้โป๊ะ"); the rim now hides the
                            # envelope with margin instead of by luck
LAMP_BULB_DZ1      = 0.045  # bulb top
NS_TOE_H     = 0.035   # nightstand toe-shadow height
NS_TOE_R     = 0.022   # toe set-back from every face (symmetric — rot-honesty)
NS_DRAWER_H  = 0.185   # top-drawer face height
NS_REV       = 0.006   # reveal between carcass and drawer face
MAX_SPAN  = 0.900   # open-shelf span before a divider is needed (Ask1/NLM load rule)

TALL_H     = 1.6    # >= this is a door run; below it is a worktop piece
RUN_RATIO  = 1.6    # long:short below this is a squat block, not a run -> stays a plain box
MIN_LEAF_W = 0.18   # never emit sliver leaves

SCRIBE_TOL = 0.005  # how far the SCRIBED north terminus may drift from its issued nominal (see
                    # slat_schedule_setout). 5 mm: a real scribe eats the sub-mm difference between
                    # a nominal plan dim and the ink; a bigger drift means the spec's run and the
                    # issued schedule are two different walls, and that must fail loud.


FACE_AXIS = {"N": ("y", 1), "S": ("y", -1), "E": ("x", 1), "W": ("x", -1)}
_FACE_ALIAS = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}

# A wall-hung PANEL is not a worktop piece. Without this screen the low-run branch caps a slim TV
# panel with a 40 mm worktop lip and sets its SCREEN 30 mm behind the plan face — and since the clay
# is the beauty pass's structural control, that teaches the repaint a floating shelf where the plan
# says a television. Kept as data (not an `H < x` rule) because a 800 mm-tall TV panel and a 750 mm
# desk are the same height; only the KIND and the wall-mounting tell them apart.
PANEL_KINDS = {"tv_panel", "tv", "panel", "shelf", "floating_shelf", "mirror", "artwork"}


def normalize_face(face):
    """'s' / 'south' / ' S ' -> 'S'. Returns None for a genuinely absent face. Raises on a
    non-empty value we cannot read — an unrecognised declaration must NOT quietly demote to the
    heuristic while build_room prints "declare a face" at an owner who just did."""
    if face is None or (isinstance(face, str) and not face.strip()):
        return None
    key = str(face).strip().upper()
    key = _FACE_ALIAS.get(key, key)
    if key not in FACE_AXIS:
        raise ValueError(f"millwork: unreadable built-in face {face!r} "
                         f"(expected one of N/S/E/W or north/south/east/west)")
    return key


def mill_axis(x0, y0, W, D, room_ctr, item_ctrs=(), face=None):
    """Which axis is the built-in's DEPTH, and which way does its FRONT face?

    Returns (axis, sign, source): axis in ('x','y'), sign +1 when the front is at the HIGH end of
    that axis, and source in ('declared','items','centroid'). Returns (None, 0, None) when the
    piece is too chunky to be a run — we do not pretend a squat block has door leaves.

    FACING IS SEMANTIC, NOT GEOMETRIC. This repo's two-layer law puts identity and facing on the
    OWNER's side of the line, and it is load-bearing here: a wardrobe whose leaves face the wall
    is worse than a box, because the clay is the beauty pass's structural control and it would
    teach the repaint that the wardrobe opens into the plaster. So a spec-declared `face`
    ('N'|'S'|'E'|'W') is AUTHORITATIVE and defines the depth axis outright.

    UNDECLARED, we INFER — and the caller must SAY it inferred (undeclared = standing REVIEW, the
    same declaration discipline the floor-2 gate runs on). The inference is NOT the room centroid:
    a built-in faces the side of the room it SERVES, which is the side with the furniture. The
    centroid is wrong exactly where it matters — PRJ-2026-002's wardrobe sits on the
    bedroom/dressing boundary of an L-shaped SUITE, and the outline's vertex-centroid lands in the
    dressing zone, which would have opened the wardrobe away from the bed it serves. (That bug was
    caught by test_millwork, not by looking at a render — which is the point of a pure layer.)"""
    if min(W, D) <= 1e-6:
        return None, 0, None
    face = normalize_face(face)
    if face is not None:                        # owner-declared: authoritative, no ratio screen
        ax, sg = FACE_AXIS[face]
        # ...but SAY SO if the declared face opens the piece along its LONG axis (a 3.3 m wardrobe
        # you open from its 600 mm end). The owner still wins — we never override a signature — but
        # the caller must be able to flag it rather than build it silently.
        long_axis = "x" if W >= D else "y"
        cross_run = (ax == long_axis and max(W, D) / min(W, D) >= RUN_RATIO)
        return ax, sg, ("declared-cross-run" if cross_run else "declared")
    if max(W, D) / min(W, D) < RUN_RATIO:
        return None, 0, None
    axis = "x" if W < D else "y"
    lo = (x0 if axis == "x" else y0)
    hi = lo + (W if axis == "x" else D)
    i = 0 if axis == "x" else 1
    hi_n = sum(1 for c in item_ctrs if c[i] > hi)
    lo_n = sum(1 for c in item_ctrs if c[i] < lo)
    if hi_n != lo_n:
        return axis, (1 if hi_n > lo_n else -1), "items"
    ctr = (lo + hi) / 2.0                        # no items to read -> fall back to the centroid
    room = room_ctr[0] if axis == "x" else room_ctr[1]
    return axis, (1 if room >= ctr else -1), "centroid"


TERMINAL_MATERIALS = ("oak", "microcement")   # the vocabulary a schedule may name for a terminal
                                              # member; the router understands exactly these


def terminal_part_name(stem, material):
    """A terminal member's part NAME carries its MATERIAL intent, because the object name is the only
    channel the material router reads (material_presets.mill_object_role).

    Taken from the SPEC, never decided here. The router is GLOBAL and project-agnostic, so a rule
    like "a jamb is microcement" would silently repaint every future project's jamb with
    PRJ-2026-002's D7 decision — the same class of bug as the fallback box a name-pattern router
    mis-painted (review 2026-07-16). Naming the INTENT instead of the FUNCTION keeps the decision in
    the project's spec: `postoak` and `jamboak` fall through to oak like any other carcass part, and
    only a schedule that ASKS for mineral gets it.

    EXPLICIT OR NOTHING — there is deliberately no default. `material or "oak"` would mean a schedule
    that merely FORGETS the key renders PRJ-2026-002's D7 as an oak jamb: option A, the one the DD
    rejected, silently, with no error and a render that looks entirely plausible. A design decision
    must not be revertible by an omission (review 2026-07-16c)."""
    if material is None or (isinstance(material, str) and not material.strip()):
        raise ValueError(f"millwork: an issued schedule must DECLARE each terminal member's material "
                         f"({stem}) as one of {TERMINAL_MATERIALS} — omitting it would silently "
                         f"render oak, which is a DESIGN decision reverting by accident")
    m = str(material).strip().lower()
    if m not in TERMINAL_MATERIALS:
        raise ValueError(f"millwork: terminal member material {material!r} is not one of "
                         f"{TERMINAL_MATERIALS} — a typo must fail loud, not silently render oak")
    return stem + ("mineral" if m == "microcement" else "oak")


def slat_schedule_setout(sched, run, H, sw, sg):
    """PURE. An ISSUED slat schedule -> the set-out along the run, in metres. No Blender, no bbox.

    A slat wall can be built two ways and they are NOT the same wall. The AUTO-FIT (millwork_parts'
    default) divides the run by the module and redistributes the remainder into every gap: it always
    closes, but the gap is then whatever the arithmetic says, and both ends die in a half-gap of air.
    An ISSUED SCHEDULE is a joiner's cutting list — a fixed slat COUNT at the true module, bracketed
    by real terminal members, closing on the wall. PRJ-2026-002 BF14 is the second kind, and the
    difference is not academic: auto-fit renders 81 slats at pitch 40.12 where the issue says 77 at
    a true 40 with two 79.6 posts (element1-oak-signature-wall_DD-2026-07-16.md, D2-A-MODULE).

    DATUM = THE LOW END OF THE RUN AXIS. "South" and "north" are the SCHEDULE's words, true for BF14
    because its run goes along +y from y-450 (south) to y2800 (north). This function has no compass —
    it sets out from along_off 0, which `part()` maps to the builtin's y0 for a depth-on-x piece. A
    schedule attached to a wall whose low end is not its south would be mis-named, not mis-built.

    Returns (members, backer_off, backer_len, z0, dz):
      members    [(name, along_off, along_len)] low -> high: the south jamb, slat0..n-1, the terminus
      backer_*   the FIELD backer's span — the field ONLY, so it never interpenetrates the
                 full-depth terminal members (the cross-material z-fight caught in review 2026-07-16).
                 The caller backs each TERMINAL's reveal separately; see millwork_parts.
      z0, dz     the members' floor reveal and cut length (D7-B item 5: the shaft floats on one
                 dark line). The field backer runs FULL height behind the battens

    DATUM SOUTH, SCRIBE NORTH (the DD's own instruction). The south is the functional end — the
    curtain must clear the mouth dead-on. So the schedule sets out from y0 and the north terminus is
    whatever run REMAINS: "the +0.2 asymmetry and all accumulated build error die in the north
    scribe against BF09-3, an already-built face." This is also what keeps the build honest against
    the spec, whose `d` is a nominal integer (3250) while the schedule closes on the ink (3250.2) —
    a literal 79.6 north post would overrun the bbox by 0.2 mm and `part()` would SILENTLY DROP it,
    i.e. the render would lose a member and look fine.

    Every number the schedule STATES is checked, not trusted: field_mm, cut_length_mm and
    post_north_mm are re-derived and must agree, so a spec edited without re-issuing the schedule
    RAISES instead of quietly rendering a different wall. All of them are REQUIRED — an optional
    cross-check is not a safety net, it is a safety net a schedule can decline (review 2026-07-16c):
    the numbers that would catch the mistake are exactly the ones a careless edit drops."""
    def _num(key, lo, hi):
        if key not in sched:
            raise ValueError(f"millwork: slat schedule is missing '{key}' — an issued schedule "
                             f"must state it; there is no safe default for a cutting list")
        v = float(sched[key])
        if not (lo <= v <= hi):
            raise ValueError(f"millwork: slat schedule {key}={v} mm is out of range [{lo}, {hi}]")
        return v / 1000.0

    if "slats" not in sched:
        raise ValueError("millwork: slat schedule is missing 'slats'")
    n_raw = sched["slats"]
    n = int(n_raw)
    if n != n_raw or isinstance(n_raw, bool):    # 77.9 -> int() would TRUNCATE to 77 and the
        raise ValueError(f"millwork: slat schedule slats={n_raw!r} must be a whole number — "
                         f"int() would silently truncate it and field_mm, re-derived from the "
                         f"truncated count, would agree with itself and pass")
    if n < 2:
        raise ValueError(f"millwork: slat schedule needs >= 2 slats, got {n!r}")
    rev = _num("reveal_mm", 1.0, 100.0)
    jamb = _num("post_south_mm", 5.0, 500.0)

    field = n * sw + (n - 1) * sg            # 77 x 27 + 76 x 13 = 3067.0 — butted, NOT centred in a
    want = _num("field_mm", 10.0, 100000.0) * 1000.0   # pitch: it starts AND ends flush on a slat face
    if abs(field * 1000.0 - want) > 0.05:
        raise ValueError(f"millwork: slat schedule field_mm={want} disagrees with its own module "
                         f"({n} x {sw * 1000:.1f} + {n - 1} x {sg * 1000:.1f} = {field * 1000:.1f} mm). "
                         f"Re-issue the schedule; do not render a wall nobody specified")

    dz = H - 2.0 * rev                       # cut length: the shaft floats on one dark line, top+bottom
    if dz <= 1e-6:
        raise ValueError(f"millwork: slat reveal {rev * 1000:.1f} mm leaves no cut length in H={H}")
    want = _num("cut_length_mm", 10.0, 100000.0) * 1000.0
    if abs(dz * 1000.0 - want) > 0.05:
        raise ValueError(f"millwork: slat schedule cut_length_mm={want} disagrees with "
                         f"H - 2 x reveal = {dz * 1000:.1f} mm")

    term = run - (jamb + rev + field + rev)  # SCRIBED — never a literal, see the docstring
    if term <= 1e-6:
        raise ValueError(f"millwork: the issued slat schedule needs "
                         f"{(jamb + rev + field + rev) * 1000:.1f} mm but the wall run is only "
                         f"{run * 1000:.1f} mm — nothing is left to scribe the north terminus into")
    want = _num("post_north_mm", 5.0, 500.0) * 1000.0
    if abs(term * 1000.0 - want) > SCRIBE_TOL * 1000.0:
        raise ValueError(f"millwork: the north terminus scribes to {term * 1000:.1f} mm but the "
                         f"schedule issues {want} mm ({abs(term * 1000.0 - want):.1f} mm out, "
                         f"tolerance {SCRIBE_TOL * 1000:.0f}). The wall run ({run * 1000:.1f} mm) "
                         f"and the schedule are two different walls — re-issue one of them")

    members = [(terminal_part_name("jamb", sched.get("post_south_material")), 0.0, jamb)]
    f0 = jamb + rev
    for i in range(n):
        members.append((f"slat{i}", f0 + i * (sw + sg), sw))
    members.append((terminal_part_name("post", sched.get("post_north_material")),
                    f0 + field + rev, term))
    return members, jamb, rev + field + rev, rev, dz


def millwork_parts(kind, W, D, H, axis, sign, floor_standing=True, open_front=False,
                   design=None, niche_mirror=False):
    """PURE. Lay out a built-in's parts in bbox-LOCAL metres. Returns a list of
    (part_name, x, y, z, dx, dy, dz) with 0 <= x and x+dx <= W (likewise y/D and z/H).

    `axis` is the DEPTH axis ('x' or 'y') — the run is along the other one. `sign` is +1 if the
    FRONT (the face the room sees) is at the HIGH end of the depth axis. Returns [] when the shape
    is not millwork-like, and the caller keeps the plain box.

    `open_front=True` (a builtin's `open` flag) builds an OPEN dressing wall — brass hang-rail,
    floating microcement-front drawers, open oak shelves, NO door leaves — instead of the closed
    door run. `design` (a builtin's `design` block) overrides the slat rhythm on a headboard
    (slat_face_mm / slat_gap_mm / slat_depth_mm). Both are OPT-IN: the default call renders exactly
    what it did before (closed leaves, DEFAULT slat constants) — the pinned tests depend on it.

    CAD-SAFE BY CONSTRUCTION: `part()` DROPS any box that would leave the bbox, so a degenerate
    built-in gets FEWER parts — never a part outside its plan-measured footprint. This is the same
    invariant, enforced the same way, as _build_bed.emit() in build_room.py: the plan footprint is
    authoritative and geometry may not silently grow it."""
    # FIRST statement on purpose: only the headboard branch reads `schedule`, so on any other kind an
    # issued cutting list — slat count, field, the D7 terminal materials — was silently DISCARDED and
    # a different wall rendered, with no warning (review 2026-07-16c). Ahead of the degenerate-bbox
    # and PANEL_KINDS screens too, both of which return early and would swallow it just as quietly.
    if (design or {}).get("schedule") is not None and kind != "headboard":
        raise ValueError(f"millwork: a slat schedule is only meaningful on a headboard slat wall, "
                         f"not on kind={kind!r} — an issued cutting list must never be silently "
                         f"discarded")
    depth = W if axis == "x" else D
    run = D if axis == "x" else W
    out = []
    if depth <= 1e-6 or run <= 1e-6 or H <= 1e-6:
        return out
    # A PANEL is never joinery: a TV, a mirror, a floating shelf has no leaves, no toe-kick and no
    # worktop — its FACE *is* the plan face. Return [] and the caller keeps its flush box, which is
    # the truth. (Caught in review: without this, specs/living_room's 1400x100 tv_panel came out
    # capped by a 40 mm worktop lip with its SCREEN set 30 mm behind the plan face — and the clay is
    # the beauty pass's structural control, so that teaches the repaint a shelf where a TV belongs.)
    if kind in PANEL_KINDS:
        return out

    def part(nm, along_off, along_len, depth_off, depth_len, z, dz):
        """`depth_off` is measured INWARD from the FRONT face, so no caller has to reason about
        which way the piece faces — this function is the only place that knows."""
        if along_len <= 1e-6 or depth_len <= 1e-6 or dz <= 1e-6:
            return
        if along_off < -1e-9 or along_off + along_len > run + 1e-9:
            return
        if depth_off < -1e-9 or depth_off + depth_len > depth + 1e-9:
            return
        if z < -1e-9 or z + dz > H + 1e-9:
            return
        near = (depth - depth_off - depth_len) if sign > 0 else depth_off
        if axis == "x":
            out.append((nm, near, along_off, z, depth_len, along_len, dz))
        else:
            out.append((nm, along_off, near, z, along_len, depth_len, dz))

    # ELEMENT 2 — OPEN DISPLAY BOOKSHELF (PRJ-2026-002 west wall, ex-TV, owner decision B
    # 2026-07-17). NOT a wardrobe (open:true would build the dressing-wall joinery) and NOT a
    # closed tall run: a FREESTANDING open grid you see THROUGH — oak shelf boards on a COOL
    # (microcement) carcass, NO back panel, so the wall/curtain/garden read behind it and the
    # south bay stands its display against the SW glass. Vertical dividers keep every bay span
    # <= MAX_SPAN; the gaps + the cool-vs-oak split are what a repaint reads as "open display".
    if kind == "bookshelf":
        if run < 2 * CARC_T or depth <= 1e-6 or H <= 3 * CARC_T:
            return []                                    # too small to compose — keep the box
        n_bay = max(1, int(round(run / 0.60)))           # ~600 bays (-> 3 across an 1800 run)
        while (run - CARC_T) / n_bay > MAX_SPAN + 1e-9 and n_bay < 20:
            n_bay += 1                                    # never exceed the open-shelf load span
        pitch_v = (run - CARC_T) / n_bay                  # gable/divider centre spacing
        for i in range(n_bay + 1):                        # 2 gables + (n_bay-1) dividers, COOL
            part(f"cool_vert{i}", min(i * pitch_v, run - CARC_T), CARC_T, 0.0, depth, 0.0, H)
        n_shelf = max(2, int(round(H / 0.345)))           # ~345 clear (books + display mix)
        dz_shelf = (H - CARC_T) / n_shelf
        for j in range(n_shelf + 1):                      # incl. base + top; OAK boards -> oak
            sz = min(j * dz_shelf, H - CARC_T)
            for b in range(n_bay):
                part(f"shelf{j}_{b}", b * pitch_v + CARC_T, pitch_v - CARC_T, 0.0, depth, sz, CARC_T)
        return out

    # ELEMENT 2 — LOW MAKEUP VANITY (PRJ-2026-002 BF11, owner-confirmed LOW seated vanity
    # 2026-07-17). A Caesarstone COUNTER over two drawer banks that FLANK a seated kneehole (the
    # void the tub-chair pulls into). counter -> caesarstone, drawer fronts -> microcement,
    # body/toe -> cool; the frameless mirror is a SEPARATE wall panel between the two windows
    # (build_room._add_vanity_mirror, from this builtin's design.mirror). Owner premise: the two
    # west casement windows sit ABOVE this low counter.
    if kind == "vanity":
        if run < 3 * CARC_T or depth <= 1e-6 or H < 0.40:
            return []
        ct = min(TOP_T, H * 0.25)                         # Caesarstone counter slab
        part("counter", 0.0, run, 0.0, depth, H - ct, ct)
        d = design or {}
        khw = float(d.get("kneehole_width_m", min(1.40, run * 0.44)))
        khc = float(d.get("kneehole_center_frac", 0.5))
        # FAIL LOUD on implausible kneehole values, like the headboard branch (_slat_mm/_num): a
        # metre/mm slip (1400 vs 1.40 m), a frac-vs-mm confusion (3549 vs 0.51), or a sign-flip must
        # not silently build a seat-less sideboard or a counter floating with no drawer banks to
        # carry it (review 2026-07-17: the vanity branch was the only new design-block reader that
        # violated the module's fail-loud contract).
        if not (0.0 < khw < run):
            raise ValueError(f"millwork vanity: kneehole_width_m={khw} must be 0 < w < run "
                             f"({run:.3f} m) — an oversize/negative kneehole leaves the counter "
                             f"with no drawer banks to support it")
        if not (0.05 <= khc <= 0.95):
            raise ValueError(f"millwork vanity: kneehole_center_frac={khc} must be in [0.05, 0.95] "
                             f"— an off-run centre builds a seat-less sideboard")
        kh_lo = min(max(0.0, khc * run - khw / 2.0), run)
        kh_hi = min(kh_lo + khw, run)
        if not (kh_hi - kh_lo > 2 * CARC_T):
            raise ValueError(f"millwork vanity: the kneehole collapsed to {kh_hi - kh_lo:.3f} m — "
                             f"no seat fits; check kneehole_width_m / kneehole_center_frac")
        toe = 0.06                                        # recessed toe-kick
        rec = min(0.04, depth * 0.3)                      # counter overhang / body set-back
        for bi, (b0, b1) in enumerate(((0.0, kh_lo), (kh_hi, run))):
            bw = b1 - b0
            if bw <= 2 * CARC_T:
                continue                                  # the kneehole eats this side -> no bank
            part(f"cool_body{bi}", b0, bw, rec, depth - rec, toe, (H - ct) - toe)
            part(f"cool_toe{bi}", b0, bw, rec, depth - rec, 0.0, toe)
            n_dr = max(2, int(round((H - ct - toe) / 0.22)))   # ~220 drawer faces
            fh = (H - ct - toe) / n_dr
            for i in range(n_dr):
                part(f"drawer_front{bi}_{i}", b0, bw, 0.0, 0.02, toe + i * fh, fh - DRAWER_REV)
        return out

    # A SLAT WALL (bed-head battens, "ผนังระแนงหัวเตียง"). The GAPS between battens are what a
    # repaint reads as a slat wall; a flat box reads as a painted wall, which is exactly what the
    # beauty pass kept giving back.
    if kind == "headboard":
        # the design block sets the rhythm (BF14 D2-A = 40 mm face / 20 mm gap / 22 mm deep, 66%
        # solid); absent one, the DEFAULT constants. A present-but-IMPLAUSIBLE value (<=0 or > a
        # sane 500 mm — a sign-flip or metre/mm slip) RAISES rather than silently rendering wrong
        # geometry (42k slivers, an overlapping ribbed slab, or a silent box). Same discipline as
        # normalize_face: a bad declaration must fail loud, not degrade to a guess (review 2026-07-16).
        d = design or {}

        def _slat_mm(key, default_m):
            v = d.get(key)
            if v is None:
                return default_m
            v = float(v)
            if not (3.0 <= v <= 500.0):
                raise ValueError(f"millwork: {key}={v} mm is not a plausible slat dimension "
                                 f"(expected 3 <= mm <= 500) — a metre/mm slip (0.04), a sign-flip "
                                 f"(-40) or an extra zero (4000) must fail loud, not render a wrong "
                                 f"slat wall")
            return v / 1000.0
        sw  = _slat_mm("slat_face_mm",  SLAT_W)
        sg  = _slat_mm("slat_gap_mm",   SLAT_GAP)
        spr = _slat_mm("slat_depth_mm", SLAT_PR)
        pr = min(spr, depth * 0.5)

        # An ISSUED SCHEDULE (a joiner's cutting list) OUTRANKS the auto-fit — it is the difference
        # between the wall we designed and a wall the arithmetic happened to land on. Opt-in: absent
        # a `schedule` block this falls through to the auto-fit below, byte-identical (pinned).
        sched = d.get("schedule")
        if sched is not None:
            members, bk_off, bk_len, z0, dz = slat_schedule_setout(sched, run, H, sw, sg)
            # the FIELD's backer runs full height behind the battens: it is what shows in their reveal.
            part("backer", bk_off, bk_len, pr, depth - pr, 0.0, H)
            for nm, off, ln in members:
                if nm.startswith("slat"):
                    part(nm, off, ln, 0.0, pr, z0, dz)       # battens stand proud of the backer
                else:
                    # TERMINAL MEMBERS are the wall's full thickness, not proud battens: the south
                    # jamb is the curtain mouth's west shoulder and the north terminus is scribed
                    # into BF09-3 (D7 / D2-A-MODULE). Full depth is why the field backer stops short.
                    part(nm, off, ln, 0.0, depth, z0, dz)
                    # ...and stopping short left each terminal's floor/ceiling reveal as a HOLE
                    # THROUGH THE WALL. Raycast in the first shipped render: under the jamb the
                    # "shadow gap" looked straight out to the full-height east glass and rendered as
                    # a DAYLIGHT slot; under the post it read as lit plaster 347 mm behind. So the
                    # single dark line BF14 floats on broke bright at exactly the two ends D7 is
                    # about (review 2026-07-16c). Back them with the same dark backer at the same
                    # set-back, so every reveal reads identically. These ABUT the member in z (never
                    # overlap it) so the cross-material z-fight stays avoided. Names are ROUTER-SAFE
                    # and run-positional, not compass: `backer*` -> backing, and nothing here may end
                    # in "mineral" or it would route to microcement — which the DD forbids in a
                    # reveal ("reveal interiors get the dark backer, NOT trowelled mineral").
                    end = "lo" if off < run * 0.5 else "hi"
                    part(f"backer_{end}_base", off, ln, pr, depth - pr, 0.0, z0)
                    part(f"backer_{end}_head", off, ln, pr, depth - pr, z0 + dz, H - (z0 + dz))
            return out

        part("backer", 0.0, run, pr, depth - pr, 0.0, H)     # matte-black ply backer (D2-A)
        n = int(run // (sw + sg))                            # sw+sg > 0 (validated) -> no zero-div
        if n < 2:
            return []                                    # too short to read as slats — keep the box
        pitch = run / n                                  # redistribute so the battens end flush
        for i in range(n):
            part(f"slat{i}", i * pitch + (pitch - sw) / 2.0, sw, 0.0, pr, 0.0, H)
        return out

    # AN OPEN DRESSING WALL (BF09-3): NO leaves — a 3-mass asymmetric composition you see INTO.
    # [1] a brass hang-rail bay · [2] a floating-drawer + open-shelf TOWER (the divider that keeps
    # every shelf span <= MAX_SPAN) · [3] a display niche wrapping the corner. The GAPS + the
    # microcement drawer fronts + the brass rail are what a repaint reads as "open, sourceable
    # joinery", where a door run reads as a closed box. Part NAMES carry material intent to
    # build_room (_suite_materials routes 'rail*' -> brass, '*front*'/'towerback' -> microcement,
    # the rest -> oak). Owner-signed D3-A/D4-A/D6-A, element1-oak-signature-wall_DD-2026-07-16.md.
    if open_front:
        if run < 3 * CARC_T or depth <= 1e-6:
            return []                                    # too small to compose — keep the box
        tower_w = min(MAX_SPAN, run * 0.28)              # the drawer/shelf divider tower
        niche_w = min(MAX_SPAN, run * 0.28)              # the corner display niche (span <= MAX_SPAN)
        bay_w = run - tower_w - niche_w                  # the hang bay takes the rest (asymmetric)
        if bay_w < 0.40:                                 # not enough run for 3 masses -> one open bay
            tower_w = niche_w = 0.0
            bay_w = run
        # structure (oak): a recessed toe-kick, a top, the vertical gables, and an oak back over
        # every bay EXCEPT the tower (the tower gets a microcement back, D6-A — drawn side-by-side
        # so the two materials never interpenetrate or share a coincident face; review 2026-07-16).
        z_lo = 0.0
        if floor_standing:
            plr = min(PLINTH_R, depth * 0.5)
            part("plinth", 0.0, run, plr, depth - plr, 0.0, min(PLINTH_H, H))
            z_lo = PLINTH_H
        part("top", 0.0, run, 0.0, depth, H - CARC_T, CARC_T)
        if tower_w:
            part("back", 0.0, bay_w, depth - CARC_T, CARC_T, 0.0, H)                      # bay back
            part("back_niche", bay_w + tower_w, niche_w, depth - CARC_T, CARC_T, 0.0, H)  # niche back
            gpos = [0.0, bay_w, bay_w + tower_w, run - CARC_T]
        else:
            part("back", 0.0, run, depth - CARC_T, CARC_T, 0.0, H)
            gpos = [0.0, run - CARC_T]
        for gi, gx in enumerate(gpos):
            part(f"gable{gi}", min(gx, run - CARC_T), CARC_T, 0.0, depth, 0.0, H)

        # [1] hang-rail bay — split by a mid-gable into a DOUBLE short-hang zone (two stacked rails,
        # shirts/short garments) + a SINGLE full-hang zone (one lower rail, long garments), each with
        # a top shelf. Two zones ENCODE the signed short-hang(1000-1150)+full-hang(1600-1750) (D4-A)
        # AND keep every bay shelf span <= MAX_SPAN. Rails ~mid-depth so garments hang into the open.
        z_shelf = H - 0.30
        bay_mid = bay_w * 0.5
        part("gable_bay", min(bay_mid, run - CARC_T), CARC_T, 0.0, depth, 0.0, H)   # splits the bay
        # CELL ARITHMETIC (P2r-8, measured off the built scene 2026-08-11): every
        # cell's internals were sized `span - 2*CARC_T` as if BOTH flanking gable
        # thicknesses lay inside the span — but each span already starts at its
        # left gable's inner face, so only the RIGHT boundary needs clearing, and
        # only when a gable's slab actually starts there. The result was a
        # systematic 18 mm slot at every cell's right edge (drawer tower 7.0778
        # vs gable face 7.0958; bay-1-0 tower 4.553 vs 4.5706 — C2-r12#10's
        # "dark shadow slot beside the white drawer stack"). Internals now end AT
        # the cell's true boundary; carcass members touching carcass is how the
        # LEFT side already stood, so no new coincident-face class is introduced.
        # The plan item prescribed a filler strip — superseded for a recorded
        # reason (gate #17): these units are custom-drawn to the cell, so the gap
        # was an arithmetic slip, not a module remainder a filler would close.
        # left sub-bay = double short-hang; cell = [CARC_T, bay_mid]
        l0, lw = CARC_T, max(bay_mid - CARC_T, 0.0)
        part("shelf_sh", l0, lw, 0.0, depth, z_shelf, CARC_T)
        for i, rz in enumerate((1.05, 2.05)):
            part(f"rail_short{i}", l0 + 0.04, max(lw - 0.08, 0.0), depth * 0.45, RAIL_D, rz, RAIL_D)
        # right sub-bay = single full-hang (rail at 1.85 m -> ~1.75 m clear drop);
        # cell ends where the next slab STARTS: at bay_w with a tower (gable1
        # begins there), at run - CARC_T without one (the end gable's slab —
        # the old `bay_w - 0` form ran the shelf INTO that end gable)
        r0 = bay_mid + CARC_T
        rw = max((bay_w if tower_w else bay_w - CARC_T) - r0, 0.0)
        part("shelf_fh", r0, rw, 0.0, depth, z_shelf, CARC_T)
        part("rail_full", r0 + 0.04, max(rw - 0.08, 0.0), depth * 0.45, RAIL_D, 1.85, RAIL_D)
        # p2r27 (owner order 2026-08-12, "ลุย" on the dead volume): the full-hang
        # cell's rail at 1.85 leaves ~0.6-0.7 m of bare carcass under the hung
        # garments — both the owner and C2-r26#9 read it as undesigned volume,
        # and the R12 check confirmed the plan ink stops at the carcass, so the
        # fit-out is ours to design. A LOW SHELF at 0.42 m fills it the way a
        # real full-hang cell is finished (boot/basket shelf under the drop):
        # 0.42 clears the longest garment this cell can hang (rail 1.85 − adult
        # 0.78 shell → cuffs ~1.0) with air to spare, and the shelf's token
        # starts with "shelf" so styling's wardrobe-shelf dressing may stack it
        # (a bare one stays inside the signed "deliberate minority BARE").
        part("shelf_fl", r0, rw, 0.0, depth, 0.42, CARC_T)

        if tower_w:
            # [2] floating-drawer + open-shelf tower — microcement fronts + a microcement back,
            # both INSET between the two gables (t_off/t_w) so no cross-material face coincides.
            # tower cell = [bay_w + CARC_T, bay_w + tower_w] (gable2's slab
            # starts at bay_w + tower_w): one CARC_T inside the span, not two
            t_off = bay_w + CARC_T
            t_w = tower_w - CARC_T
            part("towerback", t_off, t_w, depth - CARC_T, CARC_T, z_lo, (H - CARC_T) - z_lo)
            n_dr = 3
            for i in range(n_dr):
                z_i = FLOAT_Z + i * DRAWER_H
                part(f"drawer_box{i}", t_off, t_w, 0.02, depth - 0.04, z_i + 0.01, DRAWER_H - 0.02)
                # fronts carry a real handleless SIDE reveal (2 mm/side) so the
                # microcement face never lands coplanar on an oak gable face
                part(f"drawer_front{i}", t_off + 0.002, t_w - 0.004, 0.0, 0.02,
                     z_i, DRAWER_H - DRAWER_REV)
            for i, z in enumerate((FLOAT_Z + n_dr * DRAWER_H + 0.10,
                                   FLOAT_Z + n_dr * DRAWER_H + 0.60)):
                part(f"shelf_tw{i}", t_off, t_w, 0.0, depth, z, CARC_T)  # spans the true cell

            # [3] corner display niche — open oak shelves
            n_off = bay_w + tower_w + CARC_T
            n_w = niche_w - 2 * CARC_T
            for i, z in enumerate((0.40, 1.05, 1.70)):
                part(f"shelf_ni{i}", n_off, max(n_w, 0.0), 0.0, depth, z, CARC_T)
            if niche_mirror:
                # THE FOCAL JEWEL (owner redesign 2026-07-22): a mirror at the niche
                # BACK, just proud of the oak back_niche, doubling the niche depth and
                # sparkling the lit shelves. It fills the niche back FULL-HEIGHT (so it
                # doubles as a full-length dressing mirror), but the open oak shelves
                # (shelf_ni at z0.40/1.05/1.70) cross in FRONT of it, breaking the
                # reflection into bands so it reads as a mirrored NICHE, not a clean
                # pass-through plane — LOOK-verified 2026-07-22 (no GI black-hole, no
                # coplanar z-fight: the 6mm standoff clears the oak back). Routed by the
                # 'mirror' token. depth_off is inward from the FRONT, so the oak back
                # sits at depth - CARC_T; the mirror is the 6mm just in front of it.
                part("niche_mirror", n_off, max(n_w, 0.0), depth - CARC_T - 0.006, 0.006,
                     0.0, H)
        return out

    # A TALL DOOR RUN (wardrobe / full-height cabinet): leaves proud of a set-back carcass, a
    # recessed toe-kick, and a handleless pull-gap at the top. Three real shadow lines.
    if H >= TALL_H:
        t = min(T_DOOR, depth * 0.5)
        part("carcass", 0.0, run, t, depth - t, 0.0, H)
        z_lo = 0.0
        if floor_standing:
            pr = min(PLINTH_R, depth * 0.5)
            part("plinth", 0.0, run, pr, depth - pr, 0.0, min(PLINTH_H, H))
            z_lo = PLINTH_H
        door_h = H - z_lo - PULL_H
        if door_h <= 0.10:
            return out
        n = max(1, int(round(run / LEAF_W)))
        leaf = (run - (n + 1) * REVEAL) / n
        while leaf < MIN_LEAF_W and n > 1:
            n -= 1
            leaf = (run - (n + 1) * REVEAL) / n
        if leaf <= 1e-6:
            return out
        for i in range(n):
            part(f"door{i}", REVEAL + i * (leaf + REVEAL), leaf, 0.0, t, z_lo, door_h)
        return out

    # A wall-hung LOW piece is not a worktop piece either: a floating shelf has nothing to overhang.
    # (A wall-hung TALL cabinet is real joinery and keeps its leaves — the TALL branch above already
    # drops only the plinth, which is right: a floating cabinet has no floor to kick.)
    if not floor_standing:
        return []

    # A LOW RUN (built-in desk / vanity / sideboard): an overhanging worktop over a set-back
    # carcass. The lip's shadow is what separates "a built-in desk" from "a block".
    tt = min(TOP_T, H * 0.5)
    rec = min(TOP_REC, depth * 0.5)
    part("top", 0.0, run, 0.0, depth, H - tt, tt)
    part("carcass", 0.0, run, rec, depth - rec, 0.0, H - tt)
    return out


def vanity_mirror_box(spec):
    """PURE. The frameless makeup mirror (ELEMENT 2 D2-3) for the FIRST vanity builtin whose `design`
    carries a `mirror` block. Returns (object_name, x_mm, y_mm, sill_mm, w_mm, d_mm, h_mm) or None
    (opt-in: no block -> no mirror). RAISES on a malformed block (a decided element must not render a
    guess). Kept PURE + here (build_room is bpy-only) so the canonical spec's mirror is unit-testable
    and a spec edit that drops/mistypes it is caught by a test, not only silently at render."""
    v = next((b for b in (spec or {}).get("builtins") or ()
              if b.get("kind") == "vanity" and (b.get("design") or {}).get("mirror")), None)
    if not v:
        return None
    m = v["design"]["mirror"]
    try:
        x_mm, y_mm, sill_mm, w_mm, d_mm, h_mm = (
            float(m[k]) for k in ("x_mm", "y_mm", "sill_mm", "w_mm", "d_mm", "h_mm"))
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"vanity design.mirror is malformed ({e}) — a decided element must not "
                         "render a guess; fix the spec block") from e
    if w_mm <= 0 or d_mm <= 0 or h_mm <= 0:
        raise ValueError(f"vanity design.mirror has a non-positive dimension "
                         f"(w={w_mm}, d={d_mm}, h={h_mm})")
    return ("mill__bf11vanity__mirror", x_mm, y_mm, sill_mm, w_mm, d_mm, h_mm)


def nightstand_lamp_parts(w_m, d_m, h_m, lamp=True):
    """PURE (metres, footprint-LOCAL: origin at the cabinet's SW-bottom corner). The part boxes
    for an ELEMENT-3 bedside nightstand + an optional dome/'mushroom' table lamp, for
    build_room._build_nightstand to bevel + material. Returns [(part, ox, oy, oz, dx, dy, dz)].

    Kept PURE + here (the curtains.py / vanity_mirror_box law: build_room is bpy-only) so the
    geometry is unit-tested and the footprint invariant is PROVEN, not assumed:
      - the CABINET fills the whole (w, d) footprint (toe-shadow + carcass + drawer face with
        a wrapped reveal since round-6 lane C — still a solid low mass, NOT the spindly
        `_table` primitive the side tables used to get — which read as a flimsy console,
        not a ~500 mm-square bedside cabinet with a lamp);
      - the LAMP (brass base + stem + dome shade) sits ON TOP (oz >= h_m), centred, and every
        lamp part stays WITHIN the footprint in x/y (a lamp wider than its stand is a render lie).
    Containment is not a runtime guard but a sizing INVARIANT: the widest lamp part (the shade)
    has half-width 0.34*min(w,d), which is <= 0.5*min(w,d) <= half of EITHER axis — so a centred
    shade cannot overhang, for ANY positive aspect ratio (proven in test_millwork over extremes).
    Only a non-positive dimension is a real error, and that fails loud below."""
    if w_m <= 0 or d_m <= 0 or h_m <= 0:
        raise ValueError(f"nightstand has a non-positive dim (w={w_m}, d={d_m}, h={h_m})")
    # CABINETMAKER SPLIT (round-6 lane C, C2#7 "sealed boxes"): a real bedside cabinet
    # is toe-shadow + carcass + a drawer face with a reveal — three shadow lines the
    # solid block never had. The split stays SYMMETRIC about both axes (the piece's
    # rot-honesty contract) because toe inset and reveal wrap all four faces. A piece
    # too small to hold the joinery keeps the old solid body (degenerate -> FEWER
    # parts, never a part outside the footprint).
    if min(w_m, d_m) > 6 * NS_TOE_R and h_m > NS_TOE_H + NS_DRAWER_H + NS_REV + 0.06:
        parts = [
            ("toe",    NS_TOE_R, NS_TOE_R, 0.0,
             w_m - 2 * NS_TOE_R, d_m - 2 * NS_TOE_R, NS_TOE_H),
            ("body",   0.0, 0.0, NS_TOE_H,
             w_m, d_m, h_m - NS_TOE_H - NS_DRAWER_H - NS_REV),
            ("drawer", 0.0, 0.0, h_m - NS_DRAWER_H, w_m, d_m, NS_DRAWER_H),
        ]
    else:
        parts = [("body", 0.0, 0.0, 0.0, w_m, d_m, h_m)]
    if lamp:
        cx, cy = w_m / 2.0, d_m / 2.0
        # LAMP SCALE (round-6 lane C, Gemini + C2: "โคมเล็กจิ๋วเกินไปมาก" vs the 2.15m
        # bed): shade 0.27 -> 0.34 of min(w,d) (~340mm dia on the 500 cabinet, the
        # bedside-lamp mass of the bedroom reference), heights up in proportion. The
        # containment invariant is untouched: 0.34 <= 0.5*min <= half of either axis.
        br = min(w_m, d_m) * 0.17                       # brass base half-width
        tr = min(w_m, d_m) * 0.028                      # stem half-width — SCALED (a fixed 0.028 m
        #                                                 stem overhangs a sub-28 mm top; review 07-18)
        sr = min(w_m, d_m) * 0.34                       # dome shade half-width (the widest part)
        base_h, stem_h, shade_h = LAMP_BASE_H, LAMP_STEM_H, LAMP_SHADE_H
        parts.append(("lamp_base",  cx - br, cy - br, h_m,                2 * br, 2 * br, base_h))
        parts.append(("lamp_stem",  cx - tr, cy - tr, h_m + base_h,       2 * tr, 2 * tr, stem_h))
        parts.append(("lamp_shade", cx - sr, cy - sr, h_m + base_h + stem_h - 0.02,
                      2 * sr, 2 * sr, shade_h))
    return parts


def nightstand_lamp_emitter_z(w_m, d_m, h_m):
    """PURE (metres): absolute z of the practical point light for a lamped nightstand of
    this size — the CENTRE OF THE BULB THIS SAME MODULE SIZES, never a constant.

    Returns None when no lamp part exists, so a caller cannot mistake "there is no lamp"
    for "the lamp is at zero" (R11's exit-code law, applied to a number).

    WHY IT IS A FUNCTION AND NOT A NUMBER: see LAMP_DOME_H_OVER_R above. The emitter and
    the shade must move together whenever the cabinet resizes, and the only way to
    guarantee that is to derive both from one call to `nightstand_lamp_parts`.
    """
    shade = next((p for p in nightstand_lamp_parts(w_m, d_m, h_m, lamp=True)
                  if p[0] == "lamp_shade"), None)
    if shade is None:
        return None
    _, _ox, _oy, oz, dx, _dy, _dz = shade
    return oz + (LAMP_BULB_DZ0 + LAMP_BULB_DZ1) / 2.0


def nightstand_lamp_dome_apex_z(w_m, d_m, h_m):
    """PURE (metres): absolute z of the built dome's apex — the ceiling the emitter must
    stay under. Exists so a test can state the invariant the frame broke, rather than
    re-deriving build_room's dome maths in the test file (a test that recomputes the
    thing under test is the flattering scorer this defect already shipped once:
    `test_lamp_glow_z_derives_from_the_built_shade` asserted the code equalled its own
    probe constant, so it passed on every frame with the bulb outside the shade)."""
    shade = next((p for p in nightstand_lamp_parts(w_m, d_m, h_m, lamp=True)
                  if p[0] == "lamp_shade"), None)
    if shade is None:
        return None
    _, _ox, _oy, oz, dx, _dy, dz = shade
    return oz + min(dz, (dx * 0.5) * LAMP_DOME_H_OVER_R)


def tub_chair_curved(w_m, d_m, h_m, seat_h_m=0.43, rot_deg=0.0, opening_deg=110.0):
    """PURE (metres): the CURVED tub-chair layout — centre/radii/arc-span/legs as DATA for
    build_room's from_pydata materializer (the curtain-wave law: when a piece's identity IS
    a curve, the mesh must be the curve, not boxes — owner 2026-07-20 'ยังไม่ค่อยสวย' on the
    boxy first pass; the box massing was the WRONG PRIMITIVE, superseding it, not layering
    bevels on it, is the fix that stays inside the element-3 clay-ceiling ruling).

    Geometry: an annular wrap SHELL (one continuous arc) opening toward the spec FRONT
    (THE ONE FACING CONVENTION: front azimuth = rot−90°, so ANY rot now works — the
    cardinal-only limit died with the boxes), a round seat cushion inside it, 4 tapered
    round legs under the shell ring. Containment: the circle is inscribed in min(w,d) and
    centred in the footprint. seat_h 0.43 [est studio render-tier] (no vault row; h = the
    drawn label's overall rim height).

    RIM PROFILE (owner feedback 2026-07-22 'เก้าอี้ยังดูไม่สวย' on the render): a UNIFORM
    rim height read as a plain ceramic BUCKET, not an upholstered tub chair. The rim now
    SWEEPS — highest at the BACK (opposite the opening, the real backrest = h_m) dropping
    to low ARMS at the opening ends (`arm_h` = seat + a hand-rest rise) — the tub-chair
    silhouette. build_room applies the cos profile per arc vertex (arm→back→arm); this
    function returns the two heights + the arc midpoint so the mesh layer stays dumb.
    The seat CUSHION sits PROUD (dome_m above the rim-low plane, inset from the shell) so
    it reads as a pad in the wrap, not a flush disc (the bucket look)."""
    if w_m <= 0 or d_m <= 0 or h_m <= 0 or seat_h_m <= 0:
        raise ValueError(f"tub_chair: non-positive dim (w={w_m}, d={d_m}, h={h_m}, seat={seat_h_m})")
    if seat_h_m >= h_m:
        raise ValueError(f"tub_chair: seat {seat_h_m} must sit below the rim h {h_m}")
    if not (30.0 <= opening_deg <= 180.0):
        raise ValueError(f"tub_chair: opening {opening_deg}° outside 30-180 — not a tub")
    R = min(w_m, d_m) / 2.0 - 0.005
    shell_t = min(0.045, R * 0.18)
    leg_h = max(0.05, seat_h_m - 0.15)                   # shell drops just below the cushion
    arm_h = min(seat_h_m + 0.11, h_m - 0.02)             # the low front arms (hand-rest rise)
    alpha = math.radians(rot_deg - 90.0)                 # front azimuth (+X=0, CCW)
    half = math.radians(opening_deg) / 2.0
    th0 = alpha + half                                   # shell wraps the complement CCW
    th1 = alpha + 2.0 * math.pi - half
    wrap = th1 - th0
    legs = []
    for i in range(4):
        th = th0 + wrap * (i + 0.5) / 4.0
        lr = R - shell_t / 2.0
        legs.append({"x": lr * math.cos(th), "y": lr * math.sin(th),
                     "r_top": 0.018, "r_bot": 0.011, "h": leg_h})
    return {
        "cx": w_m / 2.0, "cy": d_m / 2.0, "R": R,
        "shell": {"r_out": R, "r_in": R - shell_t, "z0": leg_h - 0.02,
                  "z1_back": h_m, "z1_arm": arm_h, "th0": th0, "th1": th1},
        # cushion: a proud domed pad inset from the shell, top ~30mm above the seat plane
        "seat": {"r": R - shell_t - 0.010, "z0": leg_h - 0.02, "z1": seat_h_m,
                 "dome_r": R - shell_t - 0.010, "dome_z": seat_h_m + 0.030},
        "legs": legs,
    }


# --- the model-fit gate --------------------------------------------------------------------------
# A uniform scale CANNOT honour w, d AND h at once unless the mesh's aspect already matches the
# slot's. build_room.place_model fitted the FOOTPRINT and let height fall where it may, SILENTLY —
# which is why the real scanned CC0 `Ottoman_01`, squeezed into a 504 x 1002 mm bench slot,
# rendered as the "dark leather blob" the pro critic scored as "a simple box shape on legs". That
# was never a mesh-QUALITY failure; it was this scale bug. Buying a better bed without fixing this
# would just squash a better bed.
#
# We do not fix it by DISTORTING (a non-uniform scale is a lie about a real product's proportions,
# and this studio's whole value prop is that the render shows a sourceable, buildable thing), and
# we do not fix it by OVERFLOWING the plan bbox. We fix it by REFUSING: a mesh whose aspect does
# not match the slot is the WRONG MESH for that slot. Say so out loud, fall back to the procedural
# primitive, and let a human re-source. An honest box beats a squashed real chair.
MIN_FILL = 0.62                 # the mesh must fill >= 62% of EACH plan-footprint axis
H_LO, H_HI = 0.65, 1.30         # resulting height vs the spec's declared height

# Below this, a plan rectangle is "square enough" that its long axis is not a fact
# about the object. Turning a near-square mesh to match a near-square slot would
# be re-aiming a chair's FRONT on the strength of a 3% difference in its bbox.
SQUARE_ENOUGH = 1.15


def orient_to_slot(mw, md, w, d, rot=0.0):
    """PURE. (turn_deg, fit_w, fit_d, why) — should this mesh be turned a quarter
    turn before it is fitted, and what slot should it then be fitted to?

    WHY THIS IS NEEDED, MEASURED (p2r37). r33 offered a real bench mesh (622 x 433
    mm) to this room's bed-end bench slot (498 x 1000 mm) and `model_fit` refused
    it at 35% fill. The refusal is arithmetically right and answers the wrong
    question: the slot is long on Y and every bench ever exported is long on its
    own X, so the mesh does not need to be a different bench, it needs to be
    turned. Turned, the same mesh fills 71.5% and passes. Three cached candidates
    pass this way; none passed before.

    WHY IT IS SAFE ONLY FOR NON-TRANSPOSING ROTATIONS, and this guard is derived
    from `model_fit`'s own docstring rather than chosen: a spec item's w/d are the
    piece's LOCAL, UN-ROTATED dims, and the generator PRE-SWAPS them for a cardinal
    90/270 so that fit-then-rotate lands the world AABB back on the drawn bbox.
    Turning here as well would double-apply that pre-swap and start rejecting
    correctly placed furniture — the exact failure that docstring warns about. At
    rot 0 and 180 the footprint does not transpose, so no pre-swap was applied and
    there is nothing to double. VERIFIED against the built scene: the stool
    (rot 270, spec 510 x 546) lands 546 mm on world x — the pre-swap holds — while
    the bench (no rot) lands exactly its declared 498 x 1000.

    A turn costs the item's FRONT a quarter turn, which is free for a bench and is
    not free for a chair. That is why the caller adds `turn` to `rot` and prints
    it: a facing that changed must be visible, never inferred from a render.
    """
    if min(mw, md, w, d) <= 1e-9:
        return 0.0, w, d, "degenerate bbox — no orientation to derive"
    transposing = round(float(rot or 0.0) / 90.0) % 2 == 1
    if transposing:
        return 0.0, w, d, (f"rot {float(rot or 0.0):.0f} transposes the footprint, so this "
                           f"item's w/d were PRE-SWAPPED by the generator; turning "
                           f"here would double-apply that swap")
    ar_m = max(mw, md) / min(mw, md)
    ar_s = max(w, d) / min(w, d)
    if ar_m < SQUARE_ENOUGH or ar_s < SQUARE_ENOUGH:
        return 0.0, w, d, (f"square enough to have no long axis worth matching "
                           f"(mesh {ar_m:.2f}:1, slot {ar_s:.2f}:1, floor "
                           f"{SQUARE_ENOUGH})")
    if (mw > md) == (w > d):
        return 0.0, w, d, "mesh and slot already agree on which axis is long"
    return 90.0, d, w, (f"mesh is long on {'x' if mw > md else 'y'} and the slot is "
                        f"long on {'x' if w > d else 'y'} — turned 90 deg and "
                        f"fitted to the swapped slot, which lands the world "
                        f"footprint back inside the declared rect")


def model_fit(mw, md, mh, w, d, h, model_slot=None, item_slot=None):
    """PURE. Can a mesh with native bbox (mw, md, mh) be UNIFORMLY scaled into the spec slot
    (w, d, h) without lying about it? Returns (scale, ok, reason). Metres, rot-free BY DESIGN.

    CLASS IS CHECKED FIRST, AND UNTIL 2026-08-10 IT WAS NOT CHECKED AT ALL. Everything
    below this paragraph is geometry, and geometry cannot tell an armchair from a
    nightstand. Measured on the live shelf against this room's own slots, every one of
    these was a FIT: ArmChair_01 into a side-table slot at 0.591, Ottoman_01 into the
    same slot at 0.566, coffee_table_round_01 into the bed base at 1.537. The class was
    available the whole time — `asset_catalog` computes a `slot` for every model and its
    own docstring says the acquire step reads it. Nothing read it.

    The two slot strings are passed IN rather than looked up here, so this module stays
    stdlib-pure and the caller owns where the classes come from (the catalog for the
    mesh, the same word vocabulary for the spec kind).

    A CLASS THAT CANNOT BE RESOLVED IS REPORTED, NEVER ASSUMED TO MATCH. An unknown
    slot on either side leaves the geometric verdict standing and says in the reason
    that the class was not checked — "could not look" must not read like "looked and
    it matched".

    WHAT THIS STILL DOES NOT CATCH, said plainly because it is the next question and
    not a solved one: a class match at an extreme SCALE. ArmChair_01 is seating and so
    is a vanity stool, so the pair survives this gate at scale 0.601 — a 40% smaller
    armchair, whose seat would sit around 270 mm off the floor. A scale band cannot be
    honestly set from here: `ergonomics_ref` records in its own comment that seat height
    is not checkable from a spec (`h` is the backrest), and the spec's slot dimensions
    come from the drawing, which outranks a general comfort band. So the scale is
    REPORTED on every placement and the band is a declared gap, not a number invented
    to look like a rule.

    ROT DOES NOT BELONG HERE, and the reason is a schema fact, not a caution.
    **A spec item's `w`/`d` are the piece's OWN, LOCAL, UN-ROTATED dims** — the generator pre-swaps
    them for a cardinal quarter-turn precisely so that the renderer's fit-then-rotate lands the
    world AABB back on the drawn cluster bbox (`gen_floor2_v4_specs.to_spec`: *"For a CARDINAL
    90/270 the axis-aligned footprint swaps, so we pre-swap to keep the footprint == (wx,hy)"*;
    `placement_gate.footprint` reads the same schema). So the slot a mesh must fit IS the
    unrotated (w, d), and rotation happens afterwards, about the footprint centre. Swapping the
    target axes here would DOUBLE-APPLY the generator's pre-swap and start rejecting correctly
    placed furniture.

    (An earlier cut of this file claimed build_room carried "two contradictory angle conventions".
    That was WRONG and is retracted. There is exactly ONE convention — front = (sin rot, -cos rot),
    i.e. front = -Y at rot 0, rotated CCW — stated identically in `facing_reader._FACING`,
    `placement_logic._front_vec`, `cross_signal`, `build_floor.add_oriented_box` and
    `build_room._head_dir`; and MODEL_FRONT_DEG = -90 is that same rot-0 front, spelled as an
    azimuth. All nine CC0 meshes were MEASURED to import facing -Y (headless ortho probe), which
    is why place_model's raw-rot pass-through is correct. See build_room.MODEL_FRONT_DEG.)"""
    if min(mw, md, mh) <= 1e-6 or min(w, d, h) <= 1e-6:
        return 0.0, False, "degenerate bbox"
    if model_slot and item_slot and model_slot != item_slot:
        return 0.0, False, (f"class mismatch — a '{model_slot}' mesh offered for a "
                            f"'{item_slot}' slot. No scale makes it the right object")
    s = min(w / mw, d / md)                  # never exceed the plan footprint (the CAD invariant)
    fill = min((mw * s) / w, (md * s) / d)
    h_ratio = (mh * s) / h
    if fill < MIN_FILL:
        return s, False, (f"aspect mismatch — fills only {fill * 100:.0f}% of the plan footprint "
                          f"(mesh {mw * 1000:.0f}x{md * 1000:.0f} vs slot "
                          f"{w * 1000:.0f}x{d * 1000:.0f} mm)")
    if not (H_LO <= h_ratio <= H_HI):
        return s, False, (f"height mismatch — fits to {mh * s * 1000:.0f} mm vs the spec's "
                          f"{h * 1000:.0f} mm ({h_ratio:.2f}x)")
    if not (model_slot and item_slot):
        return s, True, (f"ok at scale {s:.3f} — CLASS NOT CHECKED "
                         f"(mesh slot {model_slot or 'unknown'}, "
                         f"slot for kind {item_slot or 'unknown'}): the bbox fits and "
                         f"nothing confirmed it is the right kind of object")
    return s, True, f"ok at scale {s:.3f}, class '{item_slot}'"
