"""
cross_signal.py -- Tier-1 self-doubt check: flag when TWO INDEPENDENT reads of the SAME
scene CONTRADICT each other. Self-contradiction is checkable with NO ground truth (that is
the whole point): if the facing read and the wall geometry disagree, or the zone label and
the drawn position disagree, at least one read is wrong -- and we can say so without an owner.

DESIGN LAWS honoured (see the suite brief):
  * TWO-LAYER. We DOUBT semantic reads; we never write a value, never re-label a kind, never
    auto-correct. Every record is advisory / REVIEW. An owner signature (facing_source /
    zone_source == "owner-signed" on the piece, OR placement_gate.confirmed_rot /
    confirmed_zone against an optional params["confirmed"] ledger) ALWAYS wins and SUPPRESSES
    the doubt (adjudicated) -- the v4 tub chairs, owner-signed to face the south glass, are
    never flagged.
  * OWNER-FREE / PURE. check_room + every check_* is (loaded dicts) -> list[record]. No disk,
    no prompt, no argparse. Deterministic (sorted outputs, no now()/random).
  * HONEST COVERAGE. check_coverage() reports, per check, ELIGIBLE (had the inputs it needs)
    vs SKIPPED (did not) so a caller can tell READ from UNWIRED from ABSENT -- silence is
    never a silent pass.
  * CONSERVATIVE (mirrors placement_gate.facing_flags). When the glass-vs-wall status of the
    edge a seat faces is UNKNOWN (no wall/glazing evidence), or a facing rot is absent, we
    ABSTAIN (emit nothing) rather than cry wolf. A false positive on the flagship real case
    (the tub chairs) is a hard failure, so every flag is a genuine, defensible contradiction.

PURE-LOGIC top level: stdlib + placement_gate + zone_flag only (their top levels are
stdlib-only; fitz/bpy/numpy are lazy inside them). No fitz/bpy/numpy imported here.

Public API:
  check_room(spec, walls=None, glazing_cands=None, params=None) -> list[record]
  check_coverage(spec, walls=None, glazing_cands=None) -> {check: {eligible, reason, n}}
  DEFAULTS  -- documented thresholds

record schema (the shared self-doubt record):
  {signal, severity, confidence, room, subjects[], detail, why, resolve_by}
"""
import math

import placement_gate as PG
import zone_flag as ZF

SCHEMA = "interior-ai/cross-signal@0.1"

# ---- thresholds (documented; a reviewer can argue each) -------------------------------
DEFAULTS = dict(
    seat_wall_clear_mm=350.0,   # a seat's FRONT AABB edge within this of an outline edge = "hard
    #                             against" that edge (a seat pushed up to a wall). Larger -> the
    #                             room is open in front -> not a wall-facer (the sofa 2m off its
    #                             wall is never flagged).
    seat_back_open_mm=600.0,    # the OPPOSITE (back) clearance must exceed this = the room is open
    #                             BEHIND the seat, so a better orientation was available (a seat
    #                             in a tight alcove with a wall behind too is NOT flagged).
    edge_wall_cover_frac=0.5,   # collinear wall segments covering >= this fraction of an outline
    #                             edge's span => that edge is a SOLID WALL (not a doorway/opening).
    edge_wall_tol_mm=150.0,     # mm; collinearity band matching a wall segment to an outline edge
    #                             (mirrors zone_flag.facade_wall_tol / check_wall_grid tol).
    companion_reach_mm=1500.0,  # a seat whose AABB gap to a work/dining surface is <= this counts
    #                             as "sitting at" it (a chair pulled up to a desk).
    tv_face_reach_mm=5000.0,    # seating/bed whose AABB gap to a TV is <= this can count as facing
    #                             it (a sofa across a living room is ~2-4m off its TV).
    tv_face_dot=0.5,            # the seat's FRONT unit-vector . unit(seat->TV) must exceed this
    #                             (~<60 deg cone) to count as "oriented toward" the TV.
    indoor_pad=150.0,           # mirrors zone_flag.indoor_pad: a centroid within this of the
    #                             outline still reads INSIDE the room.
    indoor_area_frac=0.5,       # mirrors zone_flag.indoor_area_frac: footprint >= this fraction
    #                             inside the outline = indoor (owner-containment firewall).
)

# ---- kind vocabularies (lower-cased match) --------------------------------------------
# Seating with a back/front the owner orients on purpose -- the kinds a "faces a wall" doubt
# is meaningful for. bench is included per the brief (a backed bench) but the conservative
# close-wall + open-behind + solid-non-glass guards keep it from crying wolf.
SEATING_KINDS = {"chair", "dining_chair", "armchair", "sofa", "loveseat", "bench"}
# Things that legitimately "sit at" a work/dining surface.
SEAT_FOR_TABLE = {"chair", "dining_chair", "armchair", "stool", "bench"}
# Things that legitimately face a TV (a bedroom TV faces the BED, not only seating).
FACERS_FOR_TV = SEATING_KINDS | {"bed"}
WORK_SURFACE_KINDS = {"desk", "dining_table", "writing_desk", "work_desk", "study_desk"}
TV_KINDS = {"tv_panel", "tv_console", "television", "tv", "tv_unit"}
_TV_TOKENS = ("ทีวี", "โทรทัศน์")   # Thai TV words (unambiguous); latin "tv" matched as a token

# WET plumbed fixtures (the brief's list). A DRY room they land in is a read error.
WET_FIXTURES = {"toilet", "wc", "water_closet", "basin", "lavatory", "shower",
                "bathtub", "bidet", "urinal"}
# Kitchen appliances (the brief's list + close synonyms). A DRY (non-kitchen) room is wrong.
KITCHEN_APPLIANCES = {"stove", "hob", "range", "cooktop", "oven", "sink", "range_hood",
                      "refrigerator", "fridge", "dishwasher"}
# Room types the studio treats as DRY living space (a wet/kitchen fixture there is wrong).
DRY_ROOM_TYPES = {"living_room", "sitting_room", "bedroom", "master_bedroom", "bedroom_suite",
                  "dining_room", "office", "study", "family_room", "lounge"}


# ---- tiny geometry helpers ------------------------------------------------------------
def _front(rot):
    """front(rot) = (sin, -cos) per the build_floor / placement_gate facing convention:
    rot 0 -> (0,-1) SOUTH (toward min-y facade), 90 -> EAST, 180 -> NORTH, 270 -> WEST."""
    th = math.radians(rot)
    return (math.sin(th), -math.cos(th))


def _centre(fp):
    return ((fp[0] + fp[2]) / 2.0, (fp[1] + fp[3]) / 2.0)


def _bbox(outline):
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return (min(xs), min(ys), max(xs), max(ys))


def _aabb_gap(a, b):
    """Min Euclidean gap between two axis-aligned bboxes (0 if they overlap/touch)."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def _kind(piece):
    k = piece.get("kind")
    return k.strip().lower() if isinstance(k, str) else ""


def _name(piece):
    return piece.get("name") or piece.get("kind") or "?"


def _is_tv(piece):
    """A TV focal piece: a TV kind, or a piece whose NAME flags it as a TV (BF13's Thai name
    'ชั้นวางทีวี' carries ทีวี; a latin 'TV' is matched as a delimited token so 'tv' inside
    another word does not false-match). Only the NAME is consulted, NOT the note -- notes
    routinely REFERENCE a TV ('sofa faces the TV') and must never re-type the referrer. Seating
    and beds are never TVs (a hard guard against exactly that mis-type)."""
    k = _kind(piece)
    if k in SEATING_KINDS or k == "bed":
        return False
    if k in TV_KINDS:
        return True
    name = piece.get("name") or ""
    if any(tok in name for tok in _TV_TOKENS):
        return True
    toks = name.lower().replace("/", " ").replace("(", " ").replace(")", " ").split()
    return any(t == "tv" or t.startswith("tv-") or t.startswith("tv_") for t in toks)


def _owner_signed_facing(piece, confirmed):
    """True iff the piece's FACING is owner-adjudicated -> suppress a facing doubt. Two sources,
    either wins: the persisted provenance marker the generator writes onto the applied piece
    (facing_source == 'owner-signed'), OR a matching signature in an optional confirmed ledger
    (placement_gate.confirmed_rot). Mirrors the two-layer law: the owner's call always wins."""
    if piece.get("facing_source") == "owner-signed":
        return True
    if confirmed and PG.confirmed_rot(piece, confirmed) is not None:
        return True
    return False


def _owner_signed_zone(piece, confirmed):
    """The owner-signed zone for a piece, or None. Same two sources as facing: the persisted
    zone_source provenance marker (used by placement_gate.scene_zone_decision) or a confirmed
    ledger sign. An owner-signed zone ALWAYS wins (two-layer law) -> suppresses check (c)."""
    if piece.get("zone_source") == "owner-signed":
        z = PG._norm_zone(piece.get("zone"))
        if z is not None:
            return z
    if confirmed:
        cz = PG.confirmed_zone(piece, confirmed)
        if cz is not None:
            return cz
    return None


def _room_category(rtype):
    """Classify a room type into wet / kitchen / utility / dry, or None when UNKNOWN (can't be
    classified -> check (e) ABSTAINS there, never guesses a compatibility)."""
    t = (rtype or "").strip().lower()
    if not t:
        return None
    if any(k in t for k in ("bath", "toilet", " wc", "wc_", "powder", "ensuite", "shower",
                            "lavatory", "washroom")) or t == "wc":
        return "wet"
    if any(k in t for k in ("kitchen", "pantry", "scullery")):
        return "kitchen"
    if any(k in t for k in ("laundry", "utility")):
        return "utility"
    if t in DRY_ROOM_TYPES:
        return "dry"
    if any(k in t for k in ("bedroom", "living", "sitting", "dining", "office", "study",
                            "family", "lounge")):
        return "dry"
    return None


def _edge_wall_cover(edge, walls, tol, frac_unused=None):
    """Fraction of an outline bbox edge covered by collinear wall segments. `edge` is
    ('h', y, lo, hi) for a horizontal (south/north) edge over x in [lo,hi], or ('v', x, lo, hi)
    for a vertical (east/west) edge over y in [lo,hi]. Returns a fraction in [0,1], or None when
    `walls` is None (UNKNOWN -> the caller ABSTAINS; distinct from 0.0 = looked, edge is OPEN).
    Reuses zone_flag._axis_seg / _span_cover_frac -- geometry is not re-derived here."""
    if walls is None:
        return None
    axis, c, lo, hi = edge
    ivs = []
    for s in walls:
        a = ZF._axis_seg(s)
        if a is None or a[0] != axis:
            continue
        if abs(a[1] - c) <= tol:
            ivs.append((a[2], a[3]))
    return ZF._span_cover_frac(ivs, lo, hi)


def _edge_glazed(edge, glazing_cands):
    """True iff a STRONG glazing candidate lies along the faced `edge` (any axis), covering it --
    the seat faces GLASS (a view), so the caller ABSTAINS. This GENERALISES the south-facade
    exoneration to E/W/N edges: a seat facing corroborated glass on ANY edge is facing the view,
    never a wall-facer (the original south-only guard would falsely accuse a genuine view-facer on
    a non-south facade). Perp tolerance is generous (a facade glazing line legitimately sits up to
    a slab-lip inside/outside the outline edge -- the real south facade line is ~1150mm off y_s).
    Reuses the same STRONG-glazing bar (score >= facade_tier_min) + span-overlap as
    zone_flag.facade_corroborated, so 'is this edge glass' is decided ONE way across the suite."""
    if not glazing_cands:
        return False
    axis, c, lo, hi = edge
    tier_min = ZF.DEFAULTS["facade_tier_min"]
    perp = ZF.DEFAULTS["facade_search_south"]        # a facade line may sit a slab-lip off the edge
    ovl = ZF.DEFAULTS["facade_overlap_frac"]
    span = hi - lo
    if span <= 0:
        return False
    for g in glazing_cands:
        if not isinstance(g, dict) or g.get("axis") != axis:
            continue
        sc = g.get("score")
        if not isinstance(sc, (int, float)) or sc < tier_min:
            continue
        gc = g.get("c")
        if not isinstance(gc, (int, float)) or abs(gc - c) > perp:
            continue
        gs = g.get("span")
        if not (isinstance(gs, (list, tuple)) and len(gs) >= 2
                and isinstance(gs[0], (int, float)) and isinstance(gs[1], (int, float))):
            continue
        if max(0.0, min(hi, gs[1]) - max(lo, gs[0])) / span >= ovl:
            return True
    return False


def _rec(check, severity, confidence, room, subjects, detail, why, resolve_by):
    return {"signal": f"cross_signal:{check}", "severity": severity,
            "confidence": round(float(confidence), 2), "room": room,
            "subjects": list(subjects), "detail": detail, "why": why,
            "resolve_by": resolve_by}


# ---- scene extraction -----------------------------------------------------------------
def _main_pieces(spec):
    """Loose items + built-ins of the MAIN room (subroom fixtures excluded)."""
    return list(spec.get("items", []) or []) + list(spec.get("builtins", []) or [])


def _containers(spec):
    """Yield (room_type, outline, room_name, pieces) for the main room and each subroom, so a
    fixture is always judged against the room it actually lives in (a toilet in a subroom of
    type 'bathroom' is FINE; the same toilet in the main sitting_room is a read error)."""
    room = spec.get("room", {}) or {}
    yield (room.get("type"), room.get("outline_mm", []) or [], room.get("type"),
           _main_pieces(spec))
    for sr in spec.get("subrooms", []) or []:
        yield (sr.get("type"), sr.get("outline_mm", []) or [],
               sr.get("name") or sr.get("type"), list(sr.get("fixtures", []) or []))


# ---- (a) facing_vs_kind: a seat faces a solid wall (เก้าอี้หันผนัง) -------------------
def check_facing_vs_kind(spec, walls, glazing_cands, params):
    """Flag a SEATING piece whose FRONT is hard against a SOLID wall with the room open behind
    it -- its typed facing (rot) contradicts the wall geometry. CONSERVATIVE:
      - abstain when the seat's rot is absent (facing unknown -> never guess);
      - SUPPRESS when the facing is owner-signed (two-layer law -- the tub chairs);
      - a seat facing the CORROBORATED south glass is facing the VIEW -> never a flag;
      - abstain when the faced edge's glass-vs-wall status is UNKNOWN (no wall/glazing evidence).
    Runs on the MAIN room only (glazing/wall facade evidence is the main room's south edge)."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    confirmed = (params or {}).get("confirmed")
    room = (spec.get("room") or {}).get("type")
    outline = (spec.get("room") or {}).get("outline_mm") or []
    out = []
    if len(outline) < 3:
        return out
    xmin, ymin, xmax, ymax = _bbox(outline)

    for piece in _main_pieces(spec):
        if _kind(piece) not in SEATING_KINDS:
            continue
        rot = PG._norm_rot(piece.get("rot"))
        if rot is None:                       # facing unknown -> ABSTAIN (never guess a facing)
            continue
        if _owner_signed_facing(piece, confirmed):
            continue                          # owner adjudicated the facing -> suppress
        fp = PG.footprint(piece)
        fx, fy = _front(rot)
        # which outline-bbox edge does the FRONT point at, and the front/back clearances to it
        if abs(fx) >= abs(fy):
            if fx > 0:                        # faces EAST (xmax)
                side, edge = "east", ("v", xmax, ymin, ymax)
                front_clear, back_clear = xmax - fp[2], fp[0] - xmin
            else:                             # faces WEST (xmin)
                side, edge = "west", ("v", xmin, ymin, ymax)
                front_clear, back_clear = fp[0] - xmin, xmax - fp[2]
        else:
            if fy < 0:                        # faces SOUTH (ymin) -- the facade edge
                side, edge = "south", ("h", ymin, xmin, xmax)
                front_clear, back_clear = fp[1] - ymin, ymax - fp[3]
            else:                             # faces NORTH (ymax)
                side, edge = "north", ("h", ymax, xmin, xmax)
                front_clear, back_clear = ymax - fp[3], fp[1] - ymin

        if front_clear > p["seat_wall_clear_mm"]:
            continue                          # room open in FRONT -> not a wall-facer
        if back_clear < p["seat_back_open_mm"]:
            continue                          # a wall behind too (alcove) -> not clearly wrong
        if _edge_glazed(edge, glazing_cands):
            continue                          # faces corroborated GLASS on this edge = the VIEW -> correct

        cover = _edge_wall_cover(edge, walls, p["edge_wall_tol_mm"])
        if cover is None or cover < p["edge_wall_cover_frac"]:
            continue                          # UNKNOWN or OPEN edge -> ABSTAIN (no solid wall proven)

        conf = round(min(0.85, 0.55 + 0.3 * cover), 2)
        out.append(_rec(
            "facing_vs_kind", "HIGH", conf, room, [_name(piece)],
            f"{_name(piece)} ({_kind(piece)}) faces the {side} wall at "
            f"{round(front_clear)}mm with the room open ({round(back_clear)}mm) behind it",
            "the typed facing (rot) points the seat's FRONT into a solid wall "
            f"({int(round(cover * 100))}% wall-covered edge) while the open room is behind it -- "
            "the facing read and the wall geometry disagree (เก้าอี้หันผนัง)",
            "confirm on the sheet which way the seat faces; if it really faces the wall keep it "
            "and sign the rot (confirmed_rot) to adjudicate, else re-read/re-place the seat"))
    return out


# ---- (b) function_vs_placement: a surface/focal piece with its companion absent -------
def check_function_vs_placement(spec, walls, glazing_cands, params):
    """A piece whose FUNCTION implies a companion that is absent -- two reads (what it IS vs how
    it is placed) disagree:
      - a desk / dining_table with NO seat within reach -> 'nothing to sit at' (MEDIUM);
      - a TV focal piece with NO seating/bed oriented toward it -> 'nothing faces it' (LOW,
        advisory: a console TV nobody faces can be legit). Only fires when the room HAS seating,
        else abstains (a display-only room is not a contradiction)."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    room = (spec.get("room") or {}).get("type")
    pieces = _main_pieces(spec)
    seats = [q for q in pieces if _kind(q) in SEAT_FOR_TABLE]
    facers = [q for q in pieces if _kind(q) in FACERS_FOR_TV]
    out = []

    # (b1) work/dining surface with nothing to sit at
    for piece in pieces:
        if _kind(piece) not in WORK_SURFACE_KINDS:
            continue
        fp = PG.footprint(piece)
        near = any(_aabb_gap(fp, PG.footprint(s)) <= p["companion_reach_mm"]
                   for s in seats if s is not piece)
        if near:
            continue
        out.append(_rec(
            "function_vs_placement", "MEDIUM", 0.55, room, [_name(piece)],
            f"{_name(piece)} ({_kind(piece)}) has no seat within "
            f"{round(p['companion_reach_mm'])}mm",
            "a work/dining surface implies something to sit at, but no chair/stool/bench is "
            "placed within reach -- the read either dropped a seat or mis-typed the surface",
            "add/place the missing seat, or re-read the surface's kind if it is not a "
            "desk/dining table"))

    # (b2) TV focal piece with nothing oriented toward it
    tvs = [q for q in pieces if _is_tv(q)]
    if tvs and facers:                         # abstain if the room has no seating/bed at all
        for tv in tvs:
            tfp = PG.footprint(tv)
            tc = _centre(tfp)
            faced = False
            for s in facers:
                rot = PG._norm_rot(s.get("rot"))
                if rot is None:
                    continue
                sfp = PG.footprint(s)
                if _aabb_gap(sfp, tfp) > p["tv_face_reach_mm"]:
                    continue
                sc = _centre(sfp)
                vx, vy = tc[0] - sc[0], tc[1] - sc[1]
                dist = math.hypot(vx, vy)
                if dist <= 0:
                    faced = True
                    break
                fx, fy = _front(rot)
                if (fx * vx + fy * vy) / dist >= p["tv_face_dot"]:
                    faced = True
                    break
            if faced:
                continue
            out.append(_rec(
                "function_vs_placement", "LOW", 0.4, room, [_name(tv)],
                f"{_name(tv)} reads as a TV but no seating/bed is oriented toward it",
                "a TV is a focal piece; no seat or bed faces it within a viewing cone -- either "
                "the seating faces the wrong way or this piece is not really a TV",
                "confirm the piece is a TV and that a seat faces it; if it is a console nobody "
                "faces, note it so the doubt is adjudicated"))
    return out


# ---- (c) zone_vs_geometry: a non-indoor label on a piece drawn INSIDE the room --------
def check_zone_vs_geometry(spec, walls, glazing_cands, params):
    """A piece whose MACHINE zone is below_grade / outdoor_same_floor while its centroid sits
    INSIDE the room outline (indoor-immune, per zone_flag) -- the zone label and the drawn
    position contradict. Strong (near confident-wrong) -> HIGH. SUPPRESSED when the zone is
    owner-signed (two-layer law: the owner may deliberately call an inside-drawn void
    below-grade; their signature wins). Judged per container against its own outline."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    confirmed = (params or {}).get("confirmed")
    out = []
    for rtype, outline, rname, pieces in _containers(spec):
        if len(outline) < 3:
            continue
        for piece in pieces:
            if _owner_signed_zone(piece, confirmed) is not None:
                continue                       # owner adjudicated the zone -> suppress
            mz = PG._norm_zone(piece.get("zone"))
            if mz not in ("below_grade", "outdoor_same_floor"):
                continue
            fp = PG.footprint(piece)
            c = _centre(fp)
            inside = (ZF.point_in_poly(c, outline)
                      or ZF.dist_point_to_poly(c, outline) <= p["indoor_pad"]
                      or ZF.rect_area_frac_inside(fp, outline) >= p["indoor_area_frac"])
            if not inside:
                continue
            out.append(_rec(
                "zone_vs_geometry", "HIGH", 0.8, rtype, [_name(piece)],
                f"{_name(piece)} is labelled '{mz}' yet is drawn INSIDE {rname}",
                "the machine zone label (below-grade / outdoor) contradicts the drawn geometry "
                "(the piece's centroid/footprint is inside the room outline, indoor-immune) -- "
                "the F3 wound: a same-floor indoor piece mislabelled as beyond the glass",
                "re-read the zone, or if it truly is below-grade/outdoor sign confirmed_zone so "
                "the owner call sticks; if it is an ordinary indoor piece clear the zone label"))
    return out


# ---- (d) facade_vs_wall: glass claimed where a solid wall runs -------------------------
def check_facade_vs_wall(spec, walls, glazing_cands, params):
    """A strong glazed-facade candidate on the south edge WHILE a solid wall also runs along
    that edge (facade_corroborated -> reason 'south_edge_walled', glazing_c present) -- the
    glazing read and the wall read disagree ('glass claimed where a wall is'). MEDIUM. Needs
    BOTH glazing candidates and walls to detect (else facade_corroborated cannot see the
    contradiction)."""
    room = (spec.get("room") or {}).get("type")
    outline = (spec.get("room") or {}).get("outline_mm") or []
    if len(outline) < 3:
        return []
    y_s, xlo, xhi = ZF.facade_datum(outline)
    ok, ev = ZF.facade_corroborated(y_s, xlo, xhi, glazing_cands, walls, params)
    if ok or ev.get("reason") != "south_edge_walled" or ev.get("glazing_c") is None:
        return []
    cover = ev.get("wall_cover")
    return [_rec(
        "facade_vs_wall", "MEDIUM", 0.55, room, [f"{room} south edge"],
        f"a strong glazing line (c={round(ev.get('glazing_c'), 1)}) sits on the south edge of "
        f"{room}, but a wall covers {int(round((cover or 0) * 100))}% of that edge",
        "the glazing candidate reads GLASS on the south edge while the extracted walls read a "
        "SOLID WALL there -- the two reads disagree on what the south edge is",
        "confirm on the sheet whether the south edge is glass or wall; sign confirmed_facade "
        "true/false to adjudicate, and fix the wall extract or the glazing scan accordingly")]


# ---- (e) ffe_vs_room: an incompatible fixture/appliance for the room type --------------
def check_ffe_vs_room(spec, walls, glazing_cands, params):
    """A fixture/appliance incompatible with the room type it is drawn in -- the piece-identity
    read and the room-type read disagree:
      - a WET fixture (toilet/basin/shower/bathtub/bidet/urinal/...) in a DRY room -> HIGH;
      - a kitchen appliance (stove/hob/range/sink/...) in a DRY room -> HIGH.
    Judged per container against its OWN room type (a toilet in a 'bathroom' subroom is fine).
    ABSTAINS on an UNKNOWN room type (never guesses compatibility)."""
    out = []
    for rtype, _outline, rname, pieces in _containers(spec):
        cat = _room_category(rtype)
        if cat != "dry":                       # only a KNOWN dry room can host an incompatibility
            continue
        for piece in pieces:
            k = _kind(piece)
            if k in WET_FIXTURES:
                out.append(_rec(
                    "ffe_vs_room", "HIGH", 0.85, rtype, [_name(piece)],
                    f"{_name(piece)} ({k}) is a WET fixture but sits in {rname} (a dry room)",
                    "a plumbed wet fixture in a living/sleeping/dining/work room contradicts the "
                    "room type -- almost certainly a mis-read kind or a mis-assigned room",
                    "re-read the fixture kind, or move it to its ensuite/bathroom; if the room "
                    "type is wrong, fix room.type"))
            elif k in KITCHEN_APPLIANCES:
                out.append(_rec(
                    "ffe_vs_room", "HIGH", 0.8, rtype, [_name(piece)],
                    f"{_name(piece)} ({k}) is a kitchen appliance but sits in {rname} (a dry room)",
                    "a kitchen appliance in a living/sleeping/dining/work room contradicts the "
                    "room type -- likely a mis-read kind or a mis-assigned room",
                    "re-read the appliance kind, or move it to the kitchen; if the room type is "
                    "wrong, fix room.type"))
    return out


# ---- public API -----------------------------------------------------------------------
_CHECKS = (check_facing_vs_kind, check_function_vs_placement, check_zone_vs_geometry,
           check_facade_vs_wall, check_ffe_vs_room)

_SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def check_room(spec, walls=None, glazing_cands=None, params=None):
    """Run every cross-signal check over ONE room-spec dict. Pure: (loaded dicts) -> sorted
    list[record]. `walls` = [[[x1,y1],[x2,y2]],...] (optional), `glazing_cands` = [{axis,c,score,
    span},...] (optional, the shape zone_flag consumes). params may carry threshold overrides and
    an optional 'confirmed' owner ledger (list) for signature suppression. Deterministic order:
    severity band, then signal, room, subjects."""
    if not isinstance(spec, dict):
        return []
    records = []
    for chk in _CHECKS:
        try:
            records.extend(chk(spec, walls, glazing_cands, params))
        except Exception:
            # a bug in one check must NEVER abort the whole doubt pass (advisory instrument)
            continue
    records.sort(key=lambda r: (_SEV_ORDER.get(r["severity"], 9), r["signal"],
                                str(r["room"]), ",".join(r["subjects"])))
    return records


def check_coverage(spec, walls=None, glazing_cands=None):
    """Honest coverage: per check, was it ELIGIBLE (had the inputs it needs to possibly fire) or
    SKIPPED (did not)? So a caller can tell READ from UNWIRED from ABSENT -- silence is never a
    silent pass. `n` = how many subjects the check could look at."""
    if not isinstance(spec, dict):
        spec = {}
    room = spec.get("room", {}) or {}
    outline = room.get("outline_mm") or []
    pieces = _main_pieces(spec)
    all_pieces = [pc for _t, _o, _n, ps in _containers(spec) for pc in ps]

    seats_with_rot = [q for q in pieces
                      if _kind(q) in SEATING_KINDS and PG._norm_rot(q.get("rot")) is not None]
    have_wall_evidence = walls is not None or bool(glazing_cands)
    surfaces = [q for q in pieces if _kind(q) in WORK_SURFACE_KINDS]
    tvs = [q for q in pieces if _is_tv(q)]
    zoned = [q for q in all_pieces
             if PG._norm_zone(q.get("zone")) in ("below_grade", "outdoor_same_floor")]
    classifiable = [t for t, _o, _n, _p in _containers(spec) if _room_category(t) == "dry"]

    cov = {}
    cov["facing_vs_kind"] = {
        "eligible": bool(seats_with_rot) and have_wall_evidence and len(outline) >= 3,
        "n": len(seats_with_rot),
        "reason": ("ready" if (seats_with_rot and have_wall_evidence and len(outline) >= 3)
                   else "no seat-with-rot" if not seats_with_rot
                   else "no wall/glazing evidence (glass-vs-wall unknown -> abstain)"
                   if not have_wall_evidence else "no outline")}
    cov["function_vs_placement"] = {
        "eligible": bool(surfaces or tvs), "n": len(surfaces) + len(tvs),
        "reason": "ready" if (surfaces or tvs) else "no work-surface or TV focal piece"}
    cov["zone_vs_geometry"] = {
        "eligible": bool(zoned) and len(outline) >= 3, "n": len(zoned),
        "reason": ("ready" if (zoned and len(outline) >= 3)
                   else "no piece carries a non-indoor zone label" if not zoned
                   else "no outline")}
    cov["facade_vs_wall"] = {
        "eligible": walls is not None and bool(glazing_cands) and len(outline) >= 3,
        "n": 1 if len(outline) >= 3 else 0,
        "reason": ("ready" if (walls is not None and glazing_cands and len(outline) >= 3)
                   else "needs BOTH walls and glazing candidates")}
    n_dry_pieces = sum(len(p) for t, _o, _n, p in _containers(spec)
                       if _room_category(t) == "dry")
    cov["ffe_vs_room"] = {
        "eligible": bool(classifiable) and n_dry_pieces > 0, "n": n_dry_pieces,
        "reason": ("ready" if (classifiable and n_dry_pieces) else
                   "no classifiable dry room to judge" if not classifiable
                   else "classifiable dry room but no fixtures to judge")}
    return cov
