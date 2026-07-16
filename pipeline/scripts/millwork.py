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
DRAWER_REV = 0.006  # reveal between stacked drawer faces
FLOAT_Z   = 0.450   # the drawer stack FLOATS — air/shadow reveal below it (D3-A)
MAX_SPAN  = 0.900   # open-shelf span before a divider is needed (Ask1/NLM load rule)

TALL_H     = 1.6    # >= this is a door run; below it is a worktop piece
RUN_RATIO  = 1.6    # long:short below this is a squat block, not a run -> stays a plain box
MIN_LEAF_W = 0.18   # never emit sliver leaves


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


def millwork_parts(kind, W, D, H, axis, sign, floor_standing=True, open_front=False, design=None):
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
        # left sub-bay = double short-hang
        l0, lw = CARC_T, max(bay_mid - 2 * CARC_T, 0.0)
        part("shelf_sh", l0, lw, 0.0, depth, z_shelf, CARC_T)
        for i, rz in enumerate((1.05, 2.05)):
            part(f"rail_short{i}", l0 + 0.04, max(lw - 0.08, 0.0), depth * 0.45, RAIL_D, rz, RAIL_D)
        # right sub-bay = single full-hang (rail at 1.85 m -> ~1.75 m clear drop)
        r0 = bay_mid + CARC_T
        rw = max(bay_w - (CARC_T if tower_w else 0.0) - r0, 0.0)
        part("shelf_fh", r0, rw, 0.0, depth, z_shelf, CARC_T)
        part("rail_full", r0 + 0.04, max(rw - 0.08, 0.0), depth * 0.45, RAIL_D, 1.85, RAIL_D)

        if tower_w:
            # [2] floating-drawer + open-shelf tower — microcement fronts + a microcement back,
            # both INSET between the two gables (t_off/t_w) so no cross-material face coincides.
            t_off = bay_w + CARC_T
            t_w = tower_w - 2 * CARC_T
            part("towerback", t_off, t_w, depth - CARC_T, CARC_T, z_lo, (H - CARC_T) - z_lo)
            n_dr = 3
            for i in range(n_dr):
                z_i = FLOAT_Z + i * DRAWER_H
                part(f"drawer_box{i}", t_off, t_w, 0.02, depth - 0.04, z_i + 0.01, DRAWER_H - 0.02)
                part(f"drawer_front{i}", t_off, t_w, 0.0, 0.02, z_i, DRAWER_H - DRAWER_REV)
            for i, z in enumerate((FLOAT_Z + n_dr * DRAWER_H + 0.10,
                                   FLOAT_Z + n_dr * DRAWER_H + 0.60)):
                part(f"shelf_tw{i}", t_off, t_w, 0.0, depth, z, CARC_T)

            # [3] corner display niche — open oak shelves
            n_off = bay_w + tower_w + CARC_T
            n_w = niche_w - 2 * CARC_T
            for i, z in enumerate((0.40, 1.05, 1.70)):
                part(f"shelf_ni{i}", n_off, max(n_w, 0.0), 0.0, depth, z, CARC_T)
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


def model_fit(mw, md, mh, w, d, h):
    """PURE. Can a mesh with native bbox (mw, md, mh) be UNIFORMLY scaled into the spec slot
    (w, d, h) without lying about it? Returns (scale, ok, reason). Metres, rot-free BY DESIGN.

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
    return s, True, "ok"
