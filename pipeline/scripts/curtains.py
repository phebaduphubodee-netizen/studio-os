"""
curtains.py — procedural CURTAIN layout. Pure Python (NO bpy).

Same contract as millwork.py: pure geometry that the materializer (build_room.py)
turns into meshes, unit-testable with plain `python` (test_curtains.py).

!! UNITS: INPUT is the room-spec (millimetres); OUTPUT ribbons are METRES, matching
what build_room extrudes directly. Do not feed this module metres.

WHY THIS MODULE EXISTS (2026-07-17)
-----------------------------------
The canonical master-suite spec has carried `curtain_track` (owner-traced path) and
`curtains` (owner-decided: 3 legs of the glass-L, 2 layers, 250 pocket measured from
ink) since 2026-07-16 — and NO renderer ever read either block, so every render
showed bare glass where the owner decided fabric. That omission was then MEASURED as
a design finding (commit 3ce5f5e: the "pale band" beside the curtain mouth was the
missing curtain, not a composition defect). Lesson applied here: a design decision
must not be revertible by an omission — the spec data now has a consumer.

WHAT IS DERIVED vs WHAT IS CONVENTION
-------------------------------------
DERIVED (from spec data, fail-loud when it disagrees with itself):
  * glass runs: `room.openings` glass panes chained into coplanar runs;
  * each curtain leg: an axis-aligned `curtain_track.path_mm` segment matched to the
    glass run it dresses (parallel, within one pocket width, extents overlapping);
  * drawn extent = glass ∩ track (the corner mitres belong to the NEIGHBOUR leg —
    exactly how an L-corner pair meets); park zone = the off-glass track remainder;
  * layer depth order inside the pocket from `curtains.layers` (glass side vs room
    side, envelope = stack_depth); a make-up that cannot fit the pocket RAISES —
    this reproduces the vault's ">=250 for opaque+sheer" rule from geometry.
CONVENTION (render-tier defaults, marked, owner-vetoable — NOT measurements):
  * fold wavelength / parked stack fraction / sampling density (module constants);
  * hem clearance + top edge embedded in the ceiling slab (recessed-track read).
    Real heights are RCP/supplier tier — the spec's curtains.still_owner says so;
    nothing here invents a pelmet drop.
"""
import math

import softgoods as sg

MM = 0.001   # mm -> m

# --- pocket layout (mm; the pocket WIDTH itself always comes from the spec) --------------
GAP_GLASS_MM = 20.0   # closest approach of the glass-side layer's envelope to the glass
GAP_ROOM_MM = 10.0    # closest approach of the room-side layer's envelope to the pocket edge
LAYER_GAP_MM = 5.0    # air between adjacent layers' swept envelopes

# --- render conventions (CONVENTION tier — the NLM curtain DR refused fold geometry as
# outside-corpus twice, so these are honest defaults, not grounded values) ----------------
HEM_CLEAR_M = 0.015          # hem floats off the floor
TOP_EMBED_M = 0.03           # top edge pokes INTO the ceiling slab: recessed-track read,
                             # raw fabric edge hidden without inventing an RCP pelmet
WAVELEN_MM = {"s_fold": 150.0, "3_pleat": 100.0}    # drawn fold wavelength per heading
STACK_FRACTION = {"s_fold": 0.18, "3_pleat": 0.14}  # parked stack length / drawn span
PTS_PER_FOLD = 12            # plan-polyline samples per fold (smooth sine at render scale)
TOL_JOIN_MM = 25.0           # coplanar panes closer than this chain into ONE glass run
MATCH_MIN_OVERLAP = 0.30     # min (track∩glass)/glass extent to accept a leg match

GLASS_TYPES = ("glass", "window", "sliding")
_LEG_NAME = {("y", 1): "west", ("y", -1): "east", ("x", 1): "south", ("x", -1): "north"}


def _point_in_poly(x, y, poly):
    """Ray-cast point-in-polygon (plan mm). Used only to decide which side of a glass
    plane is the ROOM — never for tolerancing."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xt = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xt > x:
                inside = not inside
    return inside


def _axis_seg(x0, y0, x1, y1, what):
    """An axis-aligned plan segment -> (axis, plane, lo, hi). axis = the coordinate the
    segment RUNS along ('y' = a vertical wall in plan, 'x' = a horizontal one)."""
    if abs(x0 - x1) < 1e-6:
        return ("y", x0, min(y0, y1), max(y0, y1))
    if abs(y0 - y1) < 1e-6:
        return ("x", y0, min(x0, x1), max(x0, x1))
    raise ValueError(f"{what} is not axis-aligned: ({x0},{y0})->({x1},{y1}) — "
                     "a diagonal here means the data is not the rectilinear plan we read")


def _glass_runs(openings):
    """Chain the spec's glass openings into coplanar RUNS (one run = one continuous
    glass wall, e.g. the 3 south panes -> one x0..5500 run)."""
    segs = []
    for o in openings or ():
        if o.get("type") not in GLASS_TYPES:
            continue
        x0, y0, x1, y1 = [float(v) for v in o["rect"]]
        if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
            continue                      # degenerate rect: nothing to dress
        segs.append(_axis_seg(x0, y0, x1, y1, f"glass opening {o.get('id')}"))
    runs = []
    for axis, plane, lo, hi in sorted(segs):
        for r in runs:
            if (r["axis"] == axis and abs(r["plane"] - plane) <= TOL_JOIN_MM
                    and lo <= r["hi"] + TOL_JOIN_MM and hi >= r["lo"] - TOL_JOIN_MM):
                r["lo"], r["hi"] = min(r["lo"], lo), max(r["hi"], hi)
                break
        else:
            runs.append({"axis": axis, "plane": plane, "lo": lo, "hi": hi})
    return runs


def _track_segments(path_mm):
    """curtain_track.path_mm -> axis-aligned segments (the owner-traced run)."""
    pts = [(float(x), float(y)) for x, y in path_mm]
    segs = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
            continue
        axis, plane, lo, hi = _axis_seg(x0, y0, x1, y1, "curtain_track leg")
        segs.append({"axis": axis, "plane": plane, "lo": lo, "hi": hi})
    if not segs:
        raise ValueError("curtain_track.path_mm has no usable segments")
    return segs


def _overlap(a_lo, a_hi, b_lo, b_hi):
    return max(0.0, min(a_hi, b_hi) - max(a_lo, b_lo))


MIN_DEPTH_SCALE = 0.3   # an obstacle squeezing the layers below this = pocket blocked


def _layer_offsets(layers, pocket, usable=None, squeezed_by=None):
    """Stack the layers into the pocket, glass side first. Each layer's swept envelope
    is stack_depth wide (amplitude = depth/2). RAISES when the make-up cannot fit the
    DECLARED pocket — the geometric form of the vault's 'opaque+sheer needs >=250'
    rule: a pocket_mm that cannot hold its own layers is data lying about itself.

    `usable` < pocket happens only when a real OBSTACLE (e.g. a built-in standing
    inside the pocket band because of a known spec residual) narrows the free depth:
    then the layer envelopes are COMPRESSED proportionally to fit, and the caller
    discloses it — the render world must never show fabric inside a wall, and the
    declared pocket stays the ink truth for the real build."""
    def side(l):
        p = str(l.get("position", "")).lower()
        g = ("back" in p) or ("glass" in p)
        r = ("front" in p) or ("room" in p)
        if g == r:   # neither marker, or BOTH — ambiguous either way
            raise ValueError(f"curtain layer '{l.get('role')}': position must name "
                             f"exactly one of the glass/back or room/front side, "
                             f"got {l.get('position')!r}")
        return 0 if g else 1
    ordered = sorted(layers, key=side)
    depths = []
    for l in ordered:
        depth = float(l.get("stack_depth_mm", 0))
        if depth <= 0:
            raise ValueError(f"curtain layer '{l.get('role')}' has no stack_depth_mm")
        depths.append(depth)
    gaps = GAP_GLASS_MM + GAP_ROOM_MM + LAYER_GAP_MM * (len(ordered) - 1)
    need = gaps + sum(depths)
    if need > pocket + 1e-6:
        raise ValueError(f"curtain make-up needs {need:.0f} mm but the pocket is "
                         f"{pocket:.0f} — this pairing does not fit (do not shrink a "
                         "layer to force it; the pocket width is ink-measured)")
    scale = 1.0
    if usable is not None and usable < need - 1e-6:
        scale = (usable - gaps) / sum(depths)
        if scale < MIN_DEPTH_SCALE:
            raise ValueError(f"obstacle '{squeezed_by}' leaves {usable:.0f} mm of the "
                             f"{pocket:.0f} pocket — below the compression floor; the "
                             "pocket is effectively blocked, fix the geometry")
    edge = GAP_GLASS_MM
    out = []
    for l, depth in zip(ordered, depths):
        amp = depth * scale / 2.0
        centre = edge + amp
        edge = centre + amp + LAYER_GAP_MM
        out.append((l, centre, amp))
    return out, scale


def _leg_free_depth(leg, pocket, obstacles):
    """How much of the pocket band is actually FREE of solid pieces along this leg's
    fabric run (drawn ∪ park). Returns (usable_mm, blocking_name). A piece that
    STRADDLES the glass plane raises — fabric cannot exist there at all."""
    d_lo, d_hi = leg["drawn"]
    lo, hi = (min(d_lo, leg["park"][0]), max(d_hi, leg["park"][1])) if leg["park"] \
        else (d_lo, d_hi)
    usable, blocker = pocket, None
    for name, bx, by, bw, bd in obstacles:
        if leg["axis"] == "y":
            o_lo, o_hi, f0, f1 = by, by + bd, bx, bx + bw
        else:
            o_lo, o_hi, f0, f1 = bx, bx + bw, by, by + bd
        if _overlap(lo, hi, o_lo, o_hi) <= 1.0:
            continue
        s0 = leg["sign"] * (f0 - leg["plane"])
        s1 = leg["sign"] * (f1 - leg["plane"])
        near, far = min(s0, s1), max(s0, s1)
        if far <= 0.0:          # entirely behind the glass plane: not in the room
            continue
        if near < 0.0:          # straddles the glass plane itself
            raise ValueError(f"'{name}' straddles the {leg['name']} leg's glass plane "
                             "— no curtain can hang there; fix the geometry")
        if near < usable:
            usable, blocker = near, name
    return usable, blocker


def _obstacles(spec):
    """Solid footprints that can narrow a pocket: built-ins + loose items (rugs are
    floor covering, not walls — excluded)."""
    out = []
    for b in spec.get("builtins") or ():
        out.append((str(b.get("name", "builtin")), float(b["x"]), float(b["y"]),
                    float(b["w"]), float(b["d"])))
    for it in spec.get("items") or ():
        if it.get("kind") == "rug":
            continue
        out.append((str(it.get("name", it.get("kind", "item"))), float(it["x"]),
                    float(it["y"]), float(it["w"]), float(it["d"])))
    return out


def _wave(lo, hi, lam, amp):
    """Sine polyline for one ribbon: [(t, offset_mm)] with offset in [-amp, +amp]."""
    span = hi - lo
    steps = max(2, int(round(span / lam * PTS_PER_FOLD)))
    return [(lo + span * i / steps,
             amp * math.sin(2.0 * math.pi * (span * i / steps) / lam))
            for i in range(steps + 1)]


def curtain_ribbons(spec):
    """spec (mm) -> fabric ribbons (METRES) for build_room to extrude.

    Returns [] when the spec has no `curtains` block (opt-in, like millwork's
    open:true — a spec without curtain data renders exactly as before). Each ribbon:
      {name, leg, role, type, state, n_folds, over_glass_park,
       pts: [(x_m, y_m), ...],  # plan polyline of the hanging fabric
       z0, z1}                   # metres; z1 sits above the ceiling plane (hidden top)
    """
    c = (spec or {}).get("curtains")
    if not c:
        return []
    room = spec.get("room") or {}
    outline = [(float(x), float(y)) for x, y in room.get("outline_mm") or []]
    if len(outline) < 3:
        raise ValueError("curtains present but room.outline_mm is missing/degenerate")
    pocket = float(c.get("pocket_mm", 0))
    if pocket <= 0:
        raise ValueError("curtains.pocket_mm missing or zero")
    layers = c.get("layers") or []
    if not layers:
        raise ValueError("curtains.layers missing — no make-up to hang")
    track = (spec.get("curtain_track") or {}).get("path_mm")
    if not track:
        raise ValueError("curtains present but curtain_track.path_mm is missing — "
                         "the run of each panel comes from the owner-traced track")
    runs = _glass_runs(room.get("openings"))
    if not runs:
        raise ValueError("curtains present but room.openings has no glass to dress")

    legs = []
    for seg in _track_segments(track):
        cand = [r for r in runs
                if r["axis"] == seg["axis"]
                and abs(r["plane"] - seg["plane"]) <= pocket + TOL_JOIN_MM
                and _overlap(seg["lo"], seg["hi"], r["lo"], r["hi"])
                >= MATCH_MIN_OVERLAP * (r["hi"] - r["lo"])]
        if not cand:
            raise ValueError(f"curtain_track leg {seg} matches no glass run — the "
                             "trace claims a curtain where the spec has no glass")
        if len(cand) > 1:
            raise ValueError(f"curtain_track leg {seg} matches {len(cand)} glass runs "
                             "— ambiguous; split the track or the openings")
        r = cand[0]
        axis, plane = r["axis"], r["plane"]
        drawn_lo = max(r["lo"], seg["lo"])
        drawn_hi = min(r["hi"], seg["hi"])
        if drawn_hi - drawn_lo <= 1.0:
            raise ValueError(f"curtain_track leg {seg} overlaps glass run {r} by "
                             "<=1 mm — nothing to dress")
        mid = (drawn_lo + drawn_hi) / 2.0
        probe = pocket / 2.0
        p_pos = (plane + probe, mid) if axis == "y" else (mid, plane + probe)
        p_neg = (plane - probe, mid) if axis == "y" else (mid, plane - probe)
        in_pos = _point_in_poly(p_pos[0], p_pos[1], outline)
        in_neg = _point_in_poly(p_neg[0], p_neg[1], outline)
        if in_pos == in_neg:
            raise ValueError(f"cannot resolve the room side of glass run {r} — "
                             "probe points are both inside or both outside the outline")
        sign = 1 if in_pos else -1
        # park zone = the off-glass track remainder (fabric PARKS off the glass — the
        # owner's stated intent for the track being longer than the glass)
        before = (seg["lo"], drawn_lo)
        after = (drawn_hi, seg["hi"])
        park = max((before, after), key=lambda z: z[1] - z[0])
        park = park if (park[1] - park[0]) > 1.0 else None
        legs.append({"name": _LEG_NAME[(axis, sign)], "axis": axis, "plane": plane,
                     "sign": sign, "drawn": (drawn_lo, drawn_hi), "park": park,
                     "glass": (r["lo"], r["hi"])})

    want = int(c.get("count", len(legs)))
    if want != len(legs):
        raise ValueError(f"curtains.count says {want} panel(s) but the track+glass "
                         f"geometry yields {len(legs)} leg(s) "
                         f"({[l['name'] for l in legs]}) — the spec disagrees with "
                         "itself; fix the data, do not render a lie")

    states = _render_states(c, layers)
    park_ends = ((c.get("render_state") or {}).get("park_end_over_glass") or {})
    known_legs = {leg["name"] for leg in legs}
    for k, v in park_ends.items():
        # fail loud on BOTH halves (review 2026-07-17: a typo'd leg key silently
        # reverted the owner's re-park to the code default)
        if k not in known_legs:
            raise ValueError(f"park_end_over_glass names unknown leg {k!r} "
                             f"(legs: {sorted(known_legs)})")
        if v not in ("lo", "hi"):
            raise ValueError(f"park_end_over_glass.{k}: expected 'lo'|'hi', got {v!r}")
    obstacles = _obstacles(spec)

    # pass 1: per-leg free depth + layer offsets. The pocket is ink-truth, but the
    # RENDER world may carry a known spec residual (e.g. BF14 parked 53 east of its
    # ink position, #9c) that narrows the free depth — fabric must never render inside
    # a wall, so the envelopes compress to the actual free depth, DISCLOSED via
    # pocket_used_mm/squeezed_by on the ribbon.
    per_leg = []
    for i, leg in enumerate(legs):
        usable, blocker = _leg_free_depth(leg, pocket, obstacles)
        offsets, scale = _layer_offsets(layers, pocket, usable=usable,
                                        squeezed_by=blocker)
        per_leg.append((usable, blocker, offsets, scale))

    # pass 2: L-corner mitres (needs every leg's drawn envelope + states)
    layer_states = {i: [(centre, amp,
                         states[str(l.get("role") or l.get("type") or "layer")]
                         == "drawn")
                        for l, centre, amp in per_leg[i][2]]
                    for i in range(len(legs))}
    _mitre_corners(legs, layer_states)

    ribbons = []
    for leg, (usable, blocker, offsets, scale) in zip(legs, per_leg):
        d_lo, d_hi = leg["drawn"]
        span = d_hi - d_lo
        for l, centre, amp in offsets:
            role = str(l.get("role") or l.get("type") or "layer")
            fold = l.get("fold")
            if fold not in WAVELEN_MM:
                raise ValueError(f"curtain layer '{role}': unknown fold {fold!r} "
                                 f"(known: {sorted(WAVELEN_MM)})")
            n_folds = max(3, int(round(span / WAVELEN_MM[fold])))
            state = states[role]
            over_glass = False
            if state == "drawn":
                lo, hi = d_lo, d_hi
                lam = span / n_folds
            else:
                stack = STACK_FRACTION[fold] * span
                if leg["park"]:
                    z_lo, z_hi = leg["park"]
                    stack = min(stack, z_hi - z_lo)
                    # stack sits at the park-zone end ADJACENT to the glass, where the
                    # fabric actually draws from
                    lo, hi = ((z_lo, z_lo + stack) if z_lo >= d_hi - 1e-6
                              else (z_hi - stack, z_hi))
                else:
                    # no off-glass track (a corner-to-corner glass wall): the stack
                    # sits IN FRONT of glass at one end of the (mitre-trimmed) run —
                    # physically honest, disclosed; keys/values validated upfront
                    end = park_ends.get(leg["name"], "lo")
                    lo, hi = ((d_lo, d_lo + stack) if end == "lo"
                              else (d_hi - stack, d_hi))
                    over_glass = True
                lam = (hi - lo) / n_folds
            pts = []
            for t, off in _wave(lo, hi, lam, amp):
                coord = leg["plane"] + leg["sign"] * (centre + off)
                pts.append(((coord * MM, t * MM) if leg["axis"] == "y"
                            else (t * MM, coord * MM)))
            ribbons.append({
                "name": f"curtain__{leg['name']}_{role}",
                "leg": leg["name"], "role": role,
                "type": str(l.get("type", "opaque")),
                "state": state, "n_folds": n_folds, "over_glass_park": over_glass,
                "centre_off_mm": centre, "amp_mm": amp, "plane_mm": leg["plane"],
                "pocket_used_mm": usable, "depth_scale": scale,
                "squeezed_by": blocker if scale < 1.0 else None,
                "pts": pts,
                "z0": HEM_CLEAR_M,
                "z1": float(room.get("ceiling_mm", 2800)) * MM + TOP_EMBED_M,
            })
    return ribbons


# --- the hanging lattice (LOOK round-2 #4) --------------------------------------------
# This module predates the e8 softgoods law, and the render finally said so: the east
# sheer's hem read as "a row of detached triangular spikes, one per pleat" — a vertical
# blind — because each ribbon was extruded as a 2-ring PRISM: the track's sine carried
# at constant amplitude from ceiling to a dead-level hem, at a metronomically constant
# pitch. That is the exact "fluted acrylic panel" corrugation softgoods.py names. The
# law ("the fold pitch must be irregular, the hem must never be level") is applied HERE,
# in the vertical dimension, without touching the owner-signed plan layout: the TOP ring
# is the track's own wave byte-for-byte, and everything the law adds decays to zero at
# the ribbon's two ENDS so the L-corner mitre meets are preserved.
RIBBON_RINGS = 8             # vertical rings hem→ceiling (smooth-shaded, 8 is plenty)
HEM_WANDER_M = 0.032         # hem rises up to this above HEM_CLEAR — never below it
PRIMARY_DECAY = 0.30         # how much of the track wave the free hem gives up
SECONDARY_FRAC = 0.38        # irregular multi-wavelength crease share at the hem
END_TAPER = 0.05             # run-fraction over which hem-law terms fade at the ends
_SEC_WAVES = ((3.1, 0.5), (7.3, 0.33), (13.7, 0.22))   # incommensurate — never a beat
_MOD_WAVES = ((1.7, 0.6), (4.3, 0.4))                  # slow per-station depth drift
# Hem wander needs energy at TWO scales, and the second LOOK pass is why: with only
# slow waves (2.3 / 5.9 cycles over a 5.5 m run of ~37 folds) adjacent pleats land at
# near-identical heights, so the hem still read as a row of matched spikes — just a
# slowly breathing one. The per-ribbon third wave at ~0.47 x n_folds (added in
# ribbon_mesh; incommensurate with the pleat pitch, so it never locks to it) is what
# makes NEIGHBOURING tips end at different heights.
_HEM_WAVES = ((2.3, 0.35), (5.9, 0.35))
_HEM_PLEAT_FRAC = 0.47       # pleat-scale wander frequency, as a fraction of n_folds
_HEM_PLEAT_AMP = 0.55        # its share of the wander (sum clamps to [-1, 1])
_LEG_OF = {v: k for k, v in _LEG_NAME.items()}          # leg name -> (axis, sign)


def _ribbon_salt(name):
    """Deterministic per-ribbon stream (hash() is process-seeded — never use it)."""
    return sum(ord(ch) for ch in str(name)) % 97


def ribbon_mesh(rb, nv=RIBBON_RINGS):
    """One hanging ribbon -> (verts, faces): a (stations x rings) quad lattice.

    Vertical structure per ring depth t (0 = suspension, 1 = hem):
      * the track wave loses PRIMARY_DECAY x t of its amplitude, modulated smoothly
        per station, so pleat depths stop being identical;
      * an incommensurate secondary crease grows in as SECONDARY_FRAC x t^1.3;
      * the summed offset is CLAMPED to the layer's own +/-amp envelope, so the
        fabric can never leave the pocket the layer stack was validated against;
      * the hem interpolates toward z0 + a smooth wander in [0, HEM_WANDER_M] —
        never level, never below the declared floor clearance.
    All three terms taper to zero within END_TAPER of each end: the mitre-trimmed
    extents are where two legs MEET, and a wandering end would open the corner."""
    axis, sign = _LEG_OF[rb["leg"]]
    amp = float(rb["amp_mm"]) * MM
    centre = float(rb["centre_off_mm"]) * MM
    plane = float(rb["plane_mm"]) * MM
    pts = rb["pts"]
    z0, z1 = float(rb["z0"]), float(rb["z1"])
    salt = _ribbon_salt(rb["name"])
    n = len(pts)
    if n < 2 or nv < 2 or amp <= 0:
        raise ValueError(f"ribbon_mesh({rb.get('name')!r}): degenerate lattice "
                         f"({n} stations, {nv} rings, amp {amp})")
    hem_waves = _HEM_WAVES + ((max(2.0, float(rb.get("n_folds", 8)) * _HEM_PLEAT_FRAC),
                               _HEM_PLEAT_AMP),)
    verts = []
    for i, p in enumerate(pts):
        coord, run = (p[0], p[1]) if axis == "y" else (p[1], p[0])
        b = (sign * (coord - plane) - centre) / amp          # track wave, in [-1, 1]
        u = i / (n - 1.0)
        taper = min(1.0, min(u, 1.0 - u) / END_TAPER) if END_TAPER > 0 else 1.0
        mod = 0.5 * (1.0 + max(-1.0, min(1.0, sg._crease(u, salt + 1, _MOD_WAVES))))
        sec = sg._crease(u, salt, _SEC_WAVES)
        wand = HEM_WANDER_M * 0.5 * (1.0 + max(-1.0, min(1.0, sg._crease(
            u, salt + 2, hem_waves)))) * taper
        for j in range(nv + 1):
            t = j / float(nv)
            val = b * (1.0 - PRIMARY_DECAY * t * mod * taper) \
                + SECONDARY_FRAC * (t ** 1.3) * sec * taper
            val = max(-1.0, min(1.0, val))
            off = plane + sign * (centre + amp * val)
            z = z1 + (z0 + wand - z1) * t
            verts.append((off, run, z) if axis == "y" else (run, off, z))
    faces = []
    for i in range(n - 1):
        for j in range(nv):
            a = i * (nv + 1) + j
            c = (i + 1) * (nv + 1) + j
            faces.append((a, c, c + 1, a + 1))
    return verts, faces


def _render_states(c, layers):
    """Per-ROLE drawn|parked. Default (day scene): sheer layers drawn — showing glass
    softly veiled is the sheer's whole job — opaque layers parked off the glass.
    `curtains.render_state` overrides per role. EVERYTHING here fails loud (review
    2026-07-17: `type` and duplicate roles used to pass silently — a typo'd type
    parked the sheer, i.e. rendered bare glass with no sound):
      * layer `type` must be 'opaque'|'sheer' (it picks BOTH the state default and
        the fabric material);
      * duplicate roles would collapse into one state/name — refused;
      * an unknown render_state role key or value is refused."""
    roles = {}
    for l in layers:
        r = str(l.get("role") or l.get("type") or "layer")
        if r in roles:
            raise ValueError(f"curtains.layers: duplicate role {r!r} — roles name "
                             "the layers; two layers cannot share one")
        t = str(l.get("type", ""))
        if t not in ("opaque", "sheer"):
            raise ValueError(f"curtain layer {r!r}: type must be 'opaque'|'sheer' "
                             f"(it selects the state default AND the fabric), "
                             f"got {l.get('type')!r}")
        roles[r] = l
    states = {r: ("drawn" if str(l.get("type")) == "sheer" else "parked")
              for r, l in roles.items()}
    rs = c.get("render_state") or {}
    for k, v in rs.items():
        if k.startswith("_") or k in ("park_end_over_glass", "fabric_rgba_linear",
                                      "sheer_alpha"):
            continue
        if k not in roles:
            raise ValueError(f"curtains.render_state names unknown layer role {k!r} "
                             f"(layers: {sorted(roles)})")
        if v not in ("drawn", "parked"):
            raise ValueError(f"curtains.render_state.{k}: expected 'drawn'|'parked', "
                             f"got {v!r}")
        states[k] = v
    return states


def _mitre_corners(legs, layer_states):
    """Resolve the L-corners where two perpendicular glass runs meet (review
    2026-07-17: drawn = glass∩track truncated each RETURN at the track's schematic
    corner, leaving a ~144 mm floor-to-ceiling bare-glass band beside the curtain
    mouth — the exact pale-band class this module exists to kill).

    CONVENTION (recorded, owner-vetoable): at a shared corner the leg with the
    SHORTER drawn run — the return — EXTENDS along its own glass into the corner
    (the sheet's S1/S2 draw arrows run the return curtains into their corners),
    stopping GAP_GLASS short of the neighbour's glass plane; the LONGER leg TRIMS
    back to the neighbour's outermost DRAWN fabric envelope (+LAYER_GAP) so the
    two panels MEET instead of crossing. layer_states: {leg_index: [(centre, amp,
    drawn?)]} for the envelope of what actually hangs."""
    for i, A in enumerate(legs):
        for j, B in enumerate(legs):
            if i == j or A["axis"] == B["axis"]:
                continue
            b_lo, b_hi = B["glass"]
            if not (b_lo - TOL_JOIN_MM <= A["plane"] <= b_hi + TOL_JOIN_MM):
                continue                      # B's glass does not reach this corner
            span_a = A["drawn"][1] - A["drawn"][0]
            span_b = B["drawn"][1] - B["drawn"][0]
            extend = span_a < span_b or (span_a == span_b and A["axis"] == "y")
            for end in ("lo", "hi"):
                g_end = A["glass"][0] if end == "lo" else A["glass"][1]
                if abs(g_end - B["plane"]) > TOL_JOIN_MM:
                    continue                  # A's glass does not terminate on B here
                if extend:
                    val = B["plane"] + B["sign"] * GAP_GLASS_MM
                else:
                    drawn_env = [c + a for c, a, d in layer_states[j] if d]
                    off = (max(drawn_env) + LAYER_GAP_MM) if drawn_env else GAP_GLASS_MM
                    val = B["plane"] + B["sign"] * off
                d_lo, d_hi = A["drawn"]
                if end == "lo":
                    d_lo = max(A["glass"][0], min(d_lo, val)) if extend \
                        else max(d_lo, val)
                else:
                    d_hi = min(A["glass"][1], max(d_hi, val)) if extend \
                        else min(d_hi, val)
                if d_hi - d_lo <= 1.0:
                    raise ValueError(f"mitre at the {A['name']}/{B['name']} corner "
                                     "leaves no drawn run — geometry conflict")
                A["drawn"] = (d_lo, d_hi)
