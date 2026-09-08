"""
exterior.py — procedural EXTERIOR-view layout: the garden environment (HDRI as spec
DATA) + the Juliet guard rail outside an operable glass opening. Pure Python (NO bpy).

Same contract as curtains.py / millwork.py: pure geometry that the materializer
(build_room.py) turns into meshes/world settings, unit-testable with plain `python`
(test_exterior.py).

!! UNITS: INPUT is the room-spec (millimetres); OUTPUT rail boxes are METRES,
matching what build_room's add_box consumes directly. Do not feed this module metres.

WHY THIS MODULE EXISTS (2026-07-17b, option B after the curtain build)
----------------------------------------------------------------------
The owner's photo (recorded in the canonical spec's glz-south-w / glz-slider notes,
2026-07-17 correction #11b) shows floor-to-ceiling clear glass onto a TROPICAL GARDEN
with a BLACK-METAL JULIET RAIL outside the operable slider. Until this module, every
render lit that glass with a studio-interior HDRI (brown_photostudio_02) — the room
said "photo studio" where the owner's photo says "garden" — and no renderer had any
notion of the rail. Same law as curtains.render_state: the view is a decision, it
becomes spec DATA with a consumer, so it can never be reverted by an omission.

WHAT IS DERIVED vs WHAT IS CONVENTION
-------------------------------------
DERIVED (from spec data, fail-loud when it disagrees with itself):
  * the rail's wall, outward side and run: the named `room.openings` glass rect +
    the room outline decide the facade plane and which side is OUTSIDE;
  * bar count: bars pack the clear span until the clear gap <= gap_max_mm.
DEPICTED, NOT DESIGNED (the rail EXISTS in the owner's photo — we are not inventing
a guard for a building we design; we are drawing one the photo shows):
  * all dimensions ([est] render-tier, owner to nudge): a furniture plan carries no
    elevation, and knowledge/codes-th/mr55-residential-dimensions.md has stair rails
    (ข้อ 24-26) + roof-deck parapets (ข้อ 50) only — NO balcony-rail height. VAULT
    GAP: no statutory value is invented here; the spec block carries the [est]s.
CONVENTION (render-tier, module constants):
  * square bar/member sections (the photo's bar profile is not readable), the small
    below-slab drop of the uprights (facade fixing), the bottom-rail seat height.
"""
import math
import re

from curtains import _axis_seg, _point_in_poly   # ONE definition of the plan helpers

MM = 0.001   # mm -> m

GLASS_TYPES = ("glass", "window", "sliding")     # same family curtains.py dresses

# below-slab drop of uprights/bars: a Juliet rail bolts to the facade OUTSIDE the
# slab edge; without the drop the rail floats when seen through floor-level glass
DROP_BELOW_FLOOR_MM = 50.0
BOTTOM_SEAT_MM = 30.0        # bottom rail's underside above interior floor level

# sanity windows for the spec's [est] dims — outside these the data is lying about
# itself, not nudging (a 300 guard is not a guard; a 3 m standoff is a balcony)
_RANGE = {
    "height_mm": (800.0, 1400.0),
    "standoff_mm": (20.0, 400.0),
    "side_margin_mm": (0.0, 400.0),
    "member_mm": (15.0, 80.0),
    "bar_mm": (8.0, 40.0),
    "gap_max_mm": (60.0, 200.0),
}


def _ext(spec):
    """spec.exterior, key-validated. The unknown-key law one level ABOVE the hdri /
    juliet_rail whitelists (review 2026-07-17b): a typo'd BLOCK name — `hdris`,
    `juliet_rai` — is otherwise indistinguishable from opt-out, so both consumers
    silently return their absent-case value and the decided garden/rail reverts by
    omission. Both consumers route through here, so this closes the boundary this
    module owns. Legacy specs (no exterior) → {} → no keys → no raise."""
    ext = (spec or {}).get("exterior") or {}
    bad = {k for k in ext if not k.startswith("_")} - {"hdri", "juliet_rail"}
    if bad:
        raise ValueError(f"spec.exterior: unknown key(s) {sorted(bad)} — a typo'd "
                         "block name (e.g. 'hdris', 'juliet_rai') would silently "
                         "revert the decided garden/rail; expected 'hdri'/'juliet_rail'")
    return ext


# Blender view-transform LOOK names for tone grading — the contrast family (AgX
# prefix optional so the same name serves AgX or Filmic) + "None"/"" (no look).
# resolve_hdri validates a spec-declared `look` against this so a SHAPE typo
# ("Agx - ...", missing dash) fails LOUD here rather than in the renderer.
#
# WHAT THIS REGEX CANNOT DO, stated because it used to claim otherwise: `look` is
# a DYNAMIC enum NAMESPACED BY `view_transform`, and this is a pure module with no
# scene access, so it never sees the one property that decides whether a name is
# valid. The "AgX - " prefix being optional means it blesses BOTH namespaces
# unconditionally — under AgX (which build_room always selects) 7 of the 15
# strings it accepts do not exist. So this is a spelling check, not a validity
# check, and the authoritative rung is the READBACK at the assignment in
# build_room.py: assign, read `view_settings.look` back, and say so when it did
# not take. A validator that cannot see the namespace must not be the thing a
# "fails LOUD" promise rests on.
_LOOK_RE = re.compile(
    r"^(None|(AgX - )?(Very High|High|Medium High|Base|Medium Low|Low|Very Low) "
    r"Contrast)$")


def resolve_hdri(spec):
    """spec.exterior.hdri -> validated {slug, strength, rot_deg, exposure, look},
    or None when the spec declares no exterior environment (opt-in, like curtains).
    Every declared field fails LOUD — a typo'd strength must not silently render
    the studio default (that is exactly the revert-by-omission this module kills)."""
    h = _ext(spec).get("hdri")
    if h is None:
        return None
    # unknown keys fail LOUD (curtain-review lesson: a typo'd key — "strenght" —
    # must not silently fall back to a default); doc-only keys are whitelisted
    bad = {k for k in h if not k.startswith("_")} \
        - {"slug", "strength", "rot_deg", "exposure", "look", "license", "why"}
    if bad:
        raise ValueError(f"exterior.hdri: unknown key(s) {sorted(bad)} — a typo here "
                         "would silently render a default over a decided view")
    slug = h.get("slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError(f"exterior.hdri.slug must be a lowercase Poly Haven slug "
                         f"([a-z0-9_]), got {slug!r}")
    out = {"slug": slug}
    for key, default, lo, hi in (("strength", 1.0, 0.02, 5.0),
                                 ("rot_deg", 0.0, -360.0, 360.0),
                                 ("exposure", 0.0, -3.0, 3.0)):
        v = h.get(key, default)
        try:
            v = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"exterior.hdri.{key}: need a number, got {h.get(key)!r}")
        if not (lo <= v <= hi) or not math.isfinite(v):
            raise ValueError(f"exterior.hdri.{key}={v} outside sane range "
                             f"[{lo}, {hi}] — fix the data, do not render a guess")
        out[key] = v
    look = h.get("look", "")
    if look is not None and not isinstance(look, str):
        raise ValueError(f"exterior.hdri.look must be a string, got {look!r}")
    look = look or ""
    # a non-empty look must be a real Blender look NAME. Downstream _hdri_world
    # assigns it inside a version-tolerant try/except:pass, so a typo'd value would
    # otherwise render with the DEFAULT look at exit 0 — the one declared field whose
    # bad value was swallowed. Validate the VALUE here (pure layer, no bpy).
    if look and not _LOOK_RE.match(look):
        raise ValueError(f"exterior.hdri.look={look!r} is not a known Blender look "
                         "name (e.g. 'AgX - Medium High Contrast', 'Medium High "
                         "Contrast', 'None'); a typo would silently render the default "
                         "look — fix it or use '' for no look")
    out["look"] = look
    return out


def _find_opening(spec, oid):
    room = (spec or {}).get("room") or {}
    for o in room.get("openings") or ():
        if o.get("id") == oid:
            return o
    raise ValueError(f"exterior.juliet_rail.opening={oid!r} matches no room.openings "
                     f"id (known: {[o.get('id') for o in room.get('openings') or ()]})")


def juliet_rail_parts(spec):
    """spec (mm) -> (parts, meta). parts = [(name, x, y, z, dx, dy, dz)] in METRES
    for build_room.add_box; meta discloses the derived numbers (bar count, actual
    gap, rail centreline) for the build log + tests. Returns ([], None) when the
    spec has no juliet_rail block (opt-in)."""
    jr = _ext(spec).get("juliet_rail")
    if jr is None:
        return [], None
    bad = {k for k in jr if not k.startswith("_")} \
        - set(_RANGE) - {"opening", "finish", "provenance"}
    if bad:
        raise ValueError(f"exterior.juliet_rail: unknown key(s) {sorted(bad)} — a "
                         "typo'd dim key would silently keep the value it meant to nudge")
    room = (spec or {}).get("room") or {}
    outline = [(float(x), float(y)) for x, y in room.get("outline_mm") or []]
    if len(outline) < 3:
        raise ValueError("juliet_rail present but room.outline_mm is missing/degenerate")
    wall_thk = float(room.get("wall_thk_mm", 100))

    oid = jr.get("opening")
    if not oid:
        raise ValueError("exterior.juliet_rail.opening missing — the rail must name "
                         "the glass opening it guards")
    o = _find_opening(spec, oid)
    if o.get("type") not in GLASS_TYPES:
        raise ValueError(f"juliet_rail opening {oid!r} has type {o.get('type')!r} — "
                         f"a guard rail outside a non-glass opening is a data error "
                         f"(glass types: {GLASS_TYPES})")
    x0, y0, x1, y1 = [float(v) for v in o["rect"]]
    axis, plane, lo, hi = _axis_seg(x0, y0, x1, y1, f"juliet_rail opening {oid}")
    if hi - lo <= 1.0:
        raise ValueError(f"juliet_rail opening {oid!r} is degenerate ({hi - lo:.1f} mm)")

    dims = {}
    for key, (rlo, rhi) in _RANGE.items():
        v = jr.get(key)
        if v is None:
            raise ValueError(f"exterior.juliet_rail.{key} missing — the rail dims are "
                             "spec DATA ([est], owner-nudgeable), not module defaults")
        v = float(v)
        if not (rlo <= v <= rhi):
            raise ValueError(f"exterior.juliet_rail.{key}={v} outside sane range "
                             f"[{rlo}, {rhi}]")
        dims[key] = v

    # which side of the glass plane is OUTSIDE: probe both sides of the run midpoint
    # against the room outline (same convention as curtains.py, opposite sign)
    mid = (lo + hi) / 2.0
    probe = max(wall_thk, 50.0)
    p_pos = (plane + probe, mid) if axis == "y" else (mid, plane + probe)
    p_neg = (plane - probe, mid) if axis == "y" else (mid, plane - probe)
    in_pos = _point_in_poly(p_pos[0], p_pos[1], outline)
    in_neg = _point_in_poly(p_neg[0], p_neg[1], outline)
    if in_pos == in_neg:
        raise ValueError(f"cannot resolve the outside of opening {oid!r} — probe "
                         "points are both inside or both outside the outline")
    sign_out = -1 if in_pos else 1

    member = dims["member_mm"]; bar = dims["bar_mm"]
    run_lo = lo - dims["side_margin_mm"]
    run_hi = hi + dims["side_margin_mm"]
    span = run_hi - run_lo
    clear = span - 2.0 * member
    if clear <= dims["gap_max_mm"]:
        raise ValueError(f"juliet_rail run {span:.0f} mm leaves no bar field between "
                         "its posts — the opening/margins are lying")
    # bars pack until every clear gap <= gap_max  (n bars -> n+1 gaps)
    n_bars = max(1, math.ceil((clear - dims["gap_max_mm"]) /
                              (bar + dims["gap_max_mm"])))
    gap = (clear - n_bars * bar) / (n_bars + 1)

    # all members share one centreline: standoff = clear air between the wall's
    # OUTER face and the rail's nearest face
    outer_face = plane + sign_out * wall_thk
    centre = outer_face + sign_out * (dims["standoff_mm"] + member / 2.0)
    z_lo = -DROP_BELOW_FLOOR_MM
    z_top = dims["height_mm"]

    def box(name, a0, a1, depth_mm, zb, zt):
        """A rail member: [a0,a1] along the run axis, `depth_mm` across it, centred
        on the rail centreline, z zb..zt (all mm in -> metres out)."""
        d0 = centre - depth_mm / 2.0
        if axis == "x":     # wall runs along x -> depth is in y
            xx, yy = a0, d0
            dx, dy = a1 - a0, depth_mm
        else:               # wall runs along y -> depth is in x
            xx, yy = d0, a0
            dx, dy = depth_mm, a1 - a0
        return (name, xx * MM, yy * MM, zb * MM,
                dx * MM, dy * MM, (zt - zb) * MM)

    tag = f"juliet__{oid}"
    parts = [
        box(f"{tag}_post_lo", run_lo, run_lo + member, member, z_lo, z_top),
        box(f"{tag}_post_hi", run_hi - member, run_hi, member, z_lo, z_top),
        box(f"{tag}_top", run_lo, run_hi, member, z_top - member, z_top),
        box(f"{tag}_bottom", run_lo + member, run_hi - member, member,
            BOTTOM_SEAT_MM, BOTTOM_SEAT_MM + member),
    ]
    b0 = run_lo + member
    for i in range(n_bars):
        a0 = b0 + gap * (i + 1) + bar * i
        parts.append(box(f"{tag}_bar_{i:02d}", a0, a0 + bar, bar,
                         BOTTOM_SEAT_MM + member, z_top - member))
    meta = {"opening": oid, "axis": axis, "sign_out": sign_out,
            "n_bars": n_bars, "gap_mm": gap, "span_mm": span,
            "centreline_mm": centre, "outer_face_mm": outer_face}
    return parts, meta
