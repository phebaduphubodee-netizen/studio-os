"""casement_sheers.py — inside-reveal casement sheer panels. Pure Python (NO bpy).

Same contract as curtains.py: pure geometry that the materializer (build_room.py
_add_casement_sheers) extrudes, unit-testable with plain `python`.

!! UNITS: INPUT is the room-spec (millimetres); OUTPUT ribbons are METRES.

WHY THIS MODULE EXISTS (ELEMENT 6, D-E6-1, element6-textiles_DD-2026-07-21.md)
------------------------------------------------------------------------------
The two west casement windows (glz-west-win1/2) are punched openings in masonry —
a different species from the floor-to-ceiling glass-L that curtains.py dresses:
  * extending curtains.py would match 3 coplanar x0 glass runs (gaps 2447/1501 mm
    >> TOL_JOIN 25) -> RAISE at curtains.py:273-275;
  * curtains.py hardcodes floor-to-ceiling z (:391-392) — these sheers are
    SILL-LENGTH, z derives from each opening's OWN sill_mm/head_mm;
  * a park derivation would re-derive (and move) the BUILT west blackout's park.
So the casement sheers get their own pure module, their own spec block, and reuse
the suite's ONE sheer identity by consuming the `curtain_sheer` material BY NAME
in the consumer (never a second sheer material).

DERIVED vs CONVENTION
---------------------
DERIVED (fail-loud): each panel's run from its opening's rect; its drop from the
opening's sill_mm/head_mm; the room side by point-in-poly probe; alpha exists and
is in-bounds at spec.curtains.render_state.sheer_alpha (CROSS-BLOCK — a spec that
drops/renames the curtains block must RAISE, not strand the sheers).
CONVENTION (render-tier [est], owner-vetoable — the D-E6-1 GAP list: fullness,
rod offset, hem gap are vault GAPs): the module constants below. The wave
amplitude DERIVES from the declared fullness (arc-length approximation), so it is
not a second free constant.

STATE LAW: drawn-only. 'parked' RAISES until a park is DESIGNED — the east park
derivation (largest off-glass remainder) cannot exist inside a ~600 reveal whose
rod spans only glass (park would be None by construction), and a jamb stack eats
the ~500 clear core (D-E6-1 [AMENDED — confrontation]).
"""
import math

MM = 0.001   # mm -> m

# --- render conventions (CONVENTION tier, honest [est] — vault GAPs, D-E6-1) -------------
HEM_ABOVE_SILL_MM = 15.0    # hem floats just above the sill (sill-length drop)
ROD_OFFSET_MM = 50.0        # default rod plane room-side of the glass (spec-overridable)
FULLNESS = 1.8              # flat micro-wave fullness (fabric length / span)
WAVELEN_MM = 80.0           # micro-wave wavelength (finer than the glass-L's 100-150)
PTS_PER_WAVE = 10           # plan-polyline samples per wave
SIDE_CLEAR_MM = 10.0        # panel edge clearance to each jamb

GLASS_TYPES = ("glass", "window", "sliding")   # the curtains.py vocabulary, shared


def amp_mm(wavelen=WAVELEN_MM, fullness=FULLNESS):
    """Wave amplitude DERIVED from the declared fullness via the sine arc-length
    approximation  L/S ~= sqrt(1 + (a*k)^2 / 2),  k = 2*pi/wavelen  — one declared
    convention (FULLNESS), not two."""
    if fullness <= 1.0:
        raise ValueError(f"fullness must exceed 1.0 (flat fabric), got {fullness}")
    return wavelen / (2.0 * math.pi) * math.sqrt(2.0 * (fullness ** 2 - 1.0))


def _point_in_poly(x, y, poly):
    """Ray-cast point-in-polygon (plan mm) — the curtains.py room-side probe."""
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


def _wave(lo, hi, lam, amp):
    """Sine polyline [(t, offset_mm)], offset in [-amp, +amp]."""
    span = hi - lo
    steps = max(2, int(round(span / lam * PTS_PER_WAVE)))
    return [(lo + span * i / steps,
             amp * math.sin(2.0 * math.pi * (span * i / steps) / lam))
            for i in range(steps + 1)]


def sheer_alpha(spec):
    """The suite's ONE sheer transmission: spec.curtains.render_state.sheer_alpha.

    CROSS-BLOCK dependency, fail-loud on every half (D-E6-1 build-consequence 2):
    the casement sheers reuse the east system's `curtain_sheer` material BY NAME,
    so their alpha IS this value — a spec that drops or renames the curtains block
    must RAISE here, never strand the sheers on a silent default (the
    decided-data-through-swallows class)."""
    c = (spec or {}).get("curtains")
    if not c:
        raise ValueError(
            "casement_sheers present but the `curtains` block is missing — the ONE "
            "suite sheer transmission lives at curtains.render_state.sheer_alpha; a "
            "dropped/renamed curtains block must RAISE, not strand the sheers")
    rs = c.get("render_state") or {}
    if "sheer_alpha" not in rs:
        raise ValueError(
            "curtains.render_state.sheer_alpha missing — the casement sheers take "
            "their transmission from the east system (ONE sheer identity); add the "
            "value there, do not default here")
    alpha = float(rs["sheer_alpha"])
    if not 0.05 <= alpha <= 0.9:
        raise ValueError(
            f"curtains.render_state.sheer_alpha={alpha}: outside 0.05-0.9 — below is "
            "an invisible sheer, above is a solid (the build_room:1054-1060 band)")
    return alpha


def sheer_ribbons(spec):
    """spec (mm) -> sill-length sheer ribbons (METRES) for build_room to extrude.

    Returns [] when the spec has no `casement_sheers` block (opt-in, like curtains).
    Each ribbon: {name, window, state, plane_mm, sign, axis, rod_offset_mm, amp_mm,
    span_mm, pts: [(x_m, y_m), ...], z0, z1} — z0/z1 derive from the opening's OWN
    sill_mm/head_mm (sill-length; NEVER floor-to-ceiling)."""
    cs = (spec or {}).get("casement_sheers")
    if not cs:
        return []
    alpha = sheer_alpha(spec)          # cross-block pin: raises BEFORE any layout
    room = spec.get("room") or {}
    outline = [(float(x), float(y)) for x, y in room.get("outline_mm") or []]
    if len(outline) < 3:
        raise ValueError("casement_sheers present but room.outline_mm is "
                         "missing/degenerate — no room side to resolve")
    wins = cs.get("windows")
    if not isinstance(wins, dict) or not wins:
        raise ValueError("casement_sheers.windows missing/empty — the block must "
                         "name the openings it dresses")
    rod_off = float(cs.get("rod_offset_mm", ROD_OFFSET_MM))
    if rod_off <= 0:
        raise ValueError(f"casement_sheers.rod_offset_mm={rod_off}: must be positive "
                         "(the fabric hangs room-side of the glass)")
    by_id = {o.get("id"): o for o in room.get("openings") or []}
    amp = amp_mm()
    ribbons = []
    for oid in sorted(wins):
        w = wins[oid] or {}
        op = by_id.get(oid)
        if op is None:
            raise ValueError(
                f"casement_sheers names unknown opening {oid!r} (room.openings ids: "
                f"{sorted(k for k in by_id if k)}) — a typo'd id must RAISE, never "
                "silently render bare glass")
        if op.get("type") not in GLASS_TYPES:
            raise ValueError(f"casement_sheers.{oid}: opening type {op.get('type')!r} "
                             f"is not glass ({GLASS_TYPES}) — nothing to veil")
        state = w.get("state")
        if state != "drawn":
            raise ValueError(
                f"casement_sheers.{oid}: state must be 'drawn', got {state!r} — the "
                "block is drawn-only: no park exists inside a punched reveal whose "
                "rod spans only the glass (parking is a future DESIGN decision, "
                "D-E6-1), and an unknown state must not silently veil/strip a window")
        if op.get("sill_mm") is None or op.get("head_mm") is None:
            raise ValueError(
                f"casement_sheers.{oid}: opening carries no sill_mm/head_mm — the "
                "sheer's drop DERIVES from them (sill-length, D-E6-1); never default "
                "to floor-to-ceiling")
        sill, head = float(op["sill_mm"]), float(op["head_mm"])
        if head - sill <= HEM_ABOVE_SILL_MM:
            raise ValueError(f"casement_sheers.{oid}: head {head:.0f} <= sill "
                             f"{sill:.0f} + hem {HEM_ABOVE_SILL_MM:.0f} — no drop")
        x0, y0, x1, y1 = [float(v) for v in op["rect"]]
        if abs(x0 - x1) < 1e-6 and abs(y0 - y1) < 1e-6:
            raise ValueError(f"casement_sheers.{oid}: degenerate rect — nothing to dress")
        if abs(x0 - x1) < 1e-6:
            axis, plane, lo, hi = "y", x0, min(y0, y1), max(y0, y1)
        elif abs(y0 - y1) < 1e-6:
            axis, plane, lo, hi = "x", y0, min(x0, x1), max(x0, x1)
        else:
            raise ValueError(f"casement_sheers.{oid}: rect is not axis-aligned — "
                             "not the rectilinear plan we read")
        span_lo, span_hi = lo + SIDE_CLEAR_MM, hi - SIDE_CLEAR_MM
        if span_hi - span_lo <= 1.0:
            raise ValueError(f"casement_sheers.{oid}: opening span {hi - lo:.0f} mm "
                             "leaves no run after jamb clearance")
        mid = (lo + hi) / 2.0
        probe = rod_off + amp + 1.0
        p_pos = (plane + probe, mid) if axis == "y" else (mid, plane + probe)
        p_neg = (plane - probe, mid) if axis == "y" else (mid, plane - probe)
        in_pos = _point_in_poly(p_pos[0], p_pos[1], outline)
        in_neg = _point_in_poly(p_neg[0], p_neg[1], outline)
        if in_pos == in_neg:
            raise ValueError(f"casement_sheers.{oid}: cannot resolve the room side — "
                             "probe points are both inside or both outside the outline")
        sign = 1 if in_pos else -1
        pts = []
        for t, off in _wave(span_lo, span_hi, WAVELEN_MM, amp):
            coord = plane + sign * (rod_off + off)
            pts.append(((coord * MM, t * MM) if axis == "y" else (t * MM, coord * MM)))
        ribbons.append({
            "name": "sheer__" + str(oid).replace("-", "_"),
            "window": oid, "state": state, "alpha": alpha,
            "plane_mm": plane, "sign": sign, "axis": axis,
            "rod_offset_mm": rod_off, "amp_mm": amp,
            "span_mm": (span_lo, span_hi),
            "pts": pts,
            "z0": (sill + HEM_ABOVE_SILL_MM) * MM,
            "z1": head * MM,
        })
    return ribbons
