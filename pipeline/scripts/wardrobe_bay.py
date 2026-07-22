"""
wardrobe_bay.py — ELEMENT 7 (PRJ-2026-002): the wardrobe-bay subroom's closed mineral
joinery. Pure Python (NO bpy), plan-mm in/out, unit-tested — the casement_sheers
precedent: own file, own RAISE contract, consumed by build_room's subroom loop.

WHY THIS MODULE EXISTS (2026-07-21, element7-wardrobe-bay_DD-2026-07-21.md)
---------------------------------------------------------------------------
Subroom fixtures used to reach ONLY bathroom.fixture_parts; kind='wardrobe' fell
through its dispatch to a silent [] and the fix__ white-slab fallback — the bay's
three masses (BF09-1 L + BF09-2) have rendered as blank boxes since the subroom
landed, behind a phantom south wall no camera ever saw. This module routes them to
REAL joinery (millwork.millwork_parts' closed tall run — reuse, never
re-implementation) and carries the element's RAISE contract so no decided datum can
be silently reverted (the swallow law, 831fc1b):

  * a wardrobe subroom WITHOUT the zone-open-south record RAISES (D-E7-2: deleting
    the record must not silently re-seal the bay behind the phantom wall);
  * a fixture kind this module does not own RAISES (nothing falls through to the
    bathroom lane — routing is BY SUBROOM TYPE in build_room, D-E7-3 merge ruling);
  * ABSENT divider stations RAISE (the drawn carcass stations are DECIDED ink data;
    an explicit [] is the decided no-stations statement, e.g. BF09-2);
  * a station outside its run, an unknown design key, or a fixture yielding zero
    parts RAISES;
  * ambiguous massing (square bbox — no derivable front) RAISES.

FRONT FACES ARE DERIVED, NEVER DECLARED (D-E7-4, the swap-survives-green pre-arm):
the front is the depth-axis side with the LARGER free gap to the subroom outline —
north leg fronts SOUTH (2145.8 vs 54.3), east leg fronts WEST (1904.1 vs -4.0),
BF09-2 fronts EAST (1846.5 vs 152.0). A geometry edit that flips a gap flips the
face and the tests go red.

Every part's mat is 'mineral' — the CLOSED FIXTURE_MAT_OBJECT vocabulary routes it
to mill__{b}__cool -> mill_object_role 'cool' -> the EXISTING microcement identity
(#AEB2B2; BF09-3's drawer fronts, BF14's south jamb, BF11's body). No bay part can
reach the silent-oak default. Internals are joinery-tier and deliberately NOT built
(D-E7-5): the closed-module part vocabulary is carcass/plinth/door/filler ONLY.
"""
import millwork

MM = 0.001                     # mm -> m at the millwork boundary (build_room's constant)

KINDS = frozenset({"wardrobe"})

# [est] module convention (D-E7-4): a station segment narrower than this is a leafless
# scribe/filler panel (the drawn 73.0 west sliver), never a sliver leaf. DECLARED here —
# a hardcoded 73 would silently reclassify a real bay if a station ever moved.
MIN_BAY_MM = 300.0

ZONE_OPEN_ID = "zone-open-south"

# closed key set for a bay fixture's design block — an unknown key RAISES instead of
# being silently ignored (the typo'd-key -> auto-fit swallow the DD critic predicted).
_DESIGN_KEYS = frozenset({
    "element", "decision", "divider_stations_mm", "front_stop_mm", "ref", "note",
    "fabricator_note", "label_conflict",
})


def _fail(msg):
    raise ValueError(f"wardrobe_bay: {msg}")


def _bbox(outline):
    xs = [float(p[0]) for p in outline]
    ys = [float(p[1]) for p in outline]
    return min(xs), min(ys), max(xs), max(ys)


def front_axis_sign(fx, sr_bbox):
    """(axis, sign) for millwork_parts, DERIVED: depth axis = the short bbox side; the
    front is the depth side with the LARGER free gap to the subroom outline. sign=+1
    means the front is at the HIGH end of the depth axis (millwork's convention)."""
    x, y = float(fx["x"]), float(fx["y"])
    w, d = float(fx["w"]), float(fx["d"])
    if abs(w - d) < 1e-6:
        _fail(f"fixture {fx.get('name')!r}: square bbox {w}x{d} — no derivable front "
              f"(depth axis ambiguous); a decided face must not be guessed")
    bx0, by0, bx1, by1 = sr_bbox
    if w < d:                                   # depth runs along x
        lo_gap = x - bx0                        # free floor west of the mass
        hi_gap = bx1 - (x + w)                  # free floor east of it
    else:
        lo_gap = y - by0
        hi_gap = by1 - (y + d)
    # review catch E7-CODE-2: an equal-gap tie (a mass centred on its depth axis)
    # is exactly as front-ambiguous as the square bbox above — RAISE, never guess.
    if abs(hi_gap - lo_gap) < 1e-6:
        _fail(f"fixture {fx.get('name')!r}: depth-axis gaps tie ({lo_gap:.1f} vs "
              f"{hi_gap:.1f}) — no derivable front; a decided face must not be "
              f"guessed")
    return ("x" if w < d else "y"), (1 if hi_gap > lo_gap else -1)


def _segments(fx, run_lo, run_hi):
    """[(seg_lo, seg_hi, kind)] along the run axis in mm; kind in {'run','filler','blind'}.
    Boundaries = the DRAWN divider stations (spec data, ink) + an optional front_stop
    beyond which the mass is BLIND carcass (the east leg's drawn front-stop at the
    L-corner, D-E7-4)."""
    design = fx.get("design") or {}
    unknown = set(design) - _DESIGN_KEYS
    if unknown:
        _fail(f"fixture {fx.get('name')!r}: unknown design key(s) {sorted(unknown)} — "
              f"closed set {sorted(_DESIGN_KEYS)} (a typo'd key must not silently "
              f"revert the drawn stations to an auto-fit rhythm)")
    if "divider_stations_mm" not in design:
        _fail(f"fixture {fx.get('name')!r}: design.divider_stations_mm is ABSENT — the "
              f"drawn carcass stations are decided ink data; state them (an explicit "
              f"[] is the decided no-stations statement)")
    stations = [float(s) for s in design["divider_stations_mm"]]
    if stations != sorted(stations):
        _fail(f"fixture {fx.get('name')!r}: stations not ascending: {stations}")
    for s in stations:
        if not (run_lo + 1e-6 < s < run_hi - 1e-6):
            _fail(f"fixture {fx.get('name')!r}: station {s} outside its run "
                  f"({run_lo}..{run_hi}) — a moved mass must re-state its stations")
    stop = design.get("front_stop_mm")
    if stop is not None:
        stop = float(stop)
        if not (run_lo + 1e-6 < stop <= run_hi + 1e-6):
            _fail(f"fixture {fx.get('name')!r}: front_stop {stop} outside its run "
                  f"({run_lo}..{run_hi})")
        if stations and stop <= stations[-1] + 1e-6:
            _fail(f"fixture {fx.get('name')!r}: front_stop {stop} not beyond the last "
                  f"station {stations[-1]}")
    fronted_hi = run_hi if stop is None else stop
    cuts = [run_lo] + stations + [fronted_hi]
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        segs.append((a, b, "filler" if (b - a) < MIN_BAY_MM else "run"))
    if stop is not None and run_hi - stop > 1e-6:
        segs.append((stop, run_hi, "blind"))
    return segs


def _fixture_parts(fx, sr_bbox, tag):
    """One wardrobe mass -> [{name, mat, x, y, z, dx, dy, dz}] (mm, absolute)."""
    x0, y0 = float(fx["x"]), float(fx["y"])
    w, d = float(fx["w"]), float(fx["d"])
    h = float(fx.get("h", 2800.0))
    # review catch E7-CODE-1: below millwork's TALL_H the tall-run branch silently
    # falls through to the LOW worktop branch — non-empty parts, so the zero-parts
    # RAISE never fires and a decided closed-leaf wardrobe renders as a desk. The
    # bay's vocabulary is the CLOSED TALL RUN only; anything shorter fails loud.
    if h * MM < millwork.TALL_H:
        _fail(f"fixture {fx.get('name')!r}: h {h:.0f}mm is below millwork.TALL_H "
              f"({millwork.TALL_H / MM:.0f}mm) — the bay owns full-height closed "
              f"wardrobes only; a low mass here would silently leave the decided "
              f"leaf vocabulary for the worktop branch")
    # review catch E7-F2: a fixture-level open flag is NOT owned by this module —
    # open dressing joinery is BF09-3's signature (millwork open_front, D-E7-4/5).
    # Swallowing the flag would render a decided-open mass CLOSED with no warning.
    if fx.get("open"):
        _fail(f"fixture {fx.get('name')!r}: carries open:true — wardrobe_bay builds "
              f"CLOSED mineral fronts only (D-E7-4/-5); an open bay mass is a NEW "
              f"design decision, not a flag (BF09-3's open_front is never borrowed)")
    axis, sign = front_axis_sign(fx, sr_bbox)
    if axis == "x":
        run_lo, run_hi, depth_mm = y0, y0 + d, w
    else:
        run_lo, run_hi, depth_mm = x0, x0 + w, d
    out = []

    def emit(nm, lx_mm, ly_mm, lz_mm, dx_mm, dy_mm, dz_mm):
        out.append({"name": f"{tag}_{nm}", "mat": "mineral",
                    "x": round(x0 + lx_mm, 1), "y": round(y0 + ly_mm, 1),
                    "z": round(lz_mm, 1),
                    "dx": round(dx_mm, 1), "dy": round(dy_mm, 1), "dz": round(dz_mm, 1)})

    for si, (a, b, seg_kind) in enumerate(_segments(fx, run_lo, run_hi)):
        seg_len = b - a
        seg_off = a - run_lo                     # local offset along the run, mm
        if seg_kind in ("filler", "blind"):
            # a leafless mineral slab: the 73.0 scribe (filler) / the drawn-front-stop
            # L-corner carcass (blind) — full depth, full height, no joinery cues.
            nm = "filler" if seg_kind == "filler" else "carcass_blind"
            if axis == "x":
                emit(f"{nm}{si}", 0.0, seg_off, 0.0, depth_mm, seg_len, h)
            else:
                emit(f"{nm}{si}", seg_off, 0.0, 0.0, seg_len, depth_mm, h)
            continue
        # a fronted segment: millwork's closed tall run (metres, bbox-local)
        if axis == "x":
            W_m, D_m = depth_mm * MM, seg_len * MM
        else:
            W_m, D_m = seg_len * MM, depth_mm * MM
        parts = millwork.millwork_parts("wardrobe", W_m, D_m, h * MM, axis, sign,
                                        floor_standing=True)
        if not parts:
            _fail(f"fixture {fx.get('name')!r}: segment {si} ({seg_len:.1f}mm) yielded "
                  f"zero millwork parts — a decided front must not silently vanish")
        for (nm, lx, ly, lz, dx, dy, dz) in parts:
            if axis == "x":
                emit(f"{nm}_s{si}", lx / MM, seg_off + ly / MM, lz / MM,
                     dx / MM, dy / MM, dz / MM)
            else:
                emit(f"{nm}_s{si}", seg_off + lx / MM, ly / MM, lz / MM,
                     dx / MM, dy / MM, dz / MM)
    if not out:
        _fail(f"fixture {fx.get('name')!r}: zero parts emitted — the white-slab "
              f"fallback must never swallow a decided wardrobe")
    return out


def _rects_overlap(a, b):
    """a, b = (x0, y0, x1, y1) — do the two axis-aligned rects share area?"""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def bay_floor_intruders(spec):
    """PURE. Top-level spec items/builtins whose footprint intrudes on the bay's
    clear floor — the bay outline bbox MINUS the three wardrobe-mass rects (D-E7-10:
    the floor is deliberately BARE). Returns a list of intruder names (empty today).
    The bare-floor STORY ARMOUR derives from THIS scan, never a hardcoded 'bare'
    string (review catch E7-F1: a static clause is the prose-copy shape — it would
    tell the Gemini polish to erase a decided item while every test stayed green).
    A wardrobe subroom is REQUIRED so the scan cannot silently pass on a bay-less
    spec that still has the story referent."""
    bay = next((s for s in (spec or {}).get("subrooms") or []
                if s.get("type") == "wardrobe"), None)
    if not bay:
        return []
    bx = _bbox(bay["outline_mm"])
    masses = [(float(f["x"]), float(f["y"]),
               float(f["x"]) + float(f["w"]), float(f["y"]) + float(f["d"]))
              for f in bay.get("fixtures") or [] if str(f.get("kind")) == "wardrobe"]
    out = []
    for coll in ("items", "builtins"):
        for o in (spec or {}).get(coll) or []:
            if not all(k in o for k in ("x", "y", "w", "d")):
                continue
            r = (float(o["x"]), float(o["y"]),
                 float(o["x"]) + float(o["w"]), float(o["y"]) + float(o["d"]))
            if not _rects_overlap(r, bx):
                continue
            # inside the bay bbox: an intruder UNLESS it is one of the masses' own
            # footprint (the masses live as subroom fixtures, not here, but guard
            # anyway) — a real floor object is anything overlapping clear floor.
            if any(_rects_overlap(r, m) and r == m for m in masses):
                continue
            out.append(str(o.get("name", coll)))
    return out


def bay_parts(sr):
    """The wardrobe-bay subroom -> flat part list for build_room (mm, absolute).

    RAISE contract (see module docstring): subroom type, zone-open-south presence,
    fixture kinds, stations, design keys, zero-parts — all fail LOUD."""
    if (sr or {}).get("type") != "wardrobe":
        _fail(f"bay_parts expects a type='wardrobe' subroom, got "
              f"{(sr or {}).get('type')!r}")
    if not any(o.get("id") == ZONE_OPEN_ID for o in sr.get("openings") or ()):
        _fail(f"subroom {sr.get('name')!r} lacks the {ZONE_OPEN_ID!r} opening record — "
              f"D-E7-2: without it the phantom south wall silently re-seals the bay; "
              f"restore the record, never build around its absence")
    fixtures = sr.get("fixtures") or []
    if not fixtures:
        _fail(f"subroom {sr.get('name')!r} has no fixtures — a wardrobe bay with "
              f"nothing in it is not this subroom")
    sr_bbox = _bbox(sr["outline_mm"])
    out = []
    for i, fx in enumerate(fixtures):
        kind = str(fx.get("kind", ""))
        if kind not in KINDS:
            _fail(f"fixture {fx.get('name')!r}: kind {kind!r} is not owned by "
                  f"wardrobe_bay ({sorted(KINDS)}) — nothing in a wardrobe subroom "
                  f"may fall through to another lane")
        bf = str(fx.get("bf") or f"m{i}").replace(" ", "").replace("__", "-")
        # review catch E7-CODE-6: separate bf and index — bare concatenation lets
        # distinct (bf, i) pairs alias ('X1',0 vs 'X',10 -> 'bayX10'), and identical
        # part names ride Blender's .001 rename channel.
        out.extend(_fixture_parts(fx, sr_bbox, f"bay{bf}-{i}"))
    return out
