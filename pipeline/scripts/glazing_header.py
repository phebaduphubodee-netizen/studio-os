"""
glazing_header.py — the PELMET the curtain hangs behind: procedural header boards on
the curtain track's own legs. Pure Python (NO bpy), same contract as curtains.py /
exterior.py / millwork.py — geometry here, meshes in build_room.py, unit-tested with
plain `python` (test_glazing_header.py).

!! UNITS: INPUT is the room-spec (millimetres); OUTPUT boxes are METRES, matching what
build_room's add_box consumes directly. Do not feed this module metres.

WHY THIS MODULE EXISTS (2026-09-02, P2r-38)
-------------------------------------------
Six of six sighted judges across two frames, plus C2 (three items) and C3 (one), read
the right third of the eye frame as "a featureless bright field" where "the sheer hangs
from nothing" — "no track, no pelmet, no header tape, no hooks". The lane's first
instinct was to build the window FRAME behind the glass. That was measured and refuted
before a line was written:

    glazing              931 px   0.022% of frame
    juliet_black_steel     0 px   0.000%   (built, wired, and `in_frustum: true` on
                                            every one of its 16 parts — occluded)
    curtain_sheer    794,756 px  18.397%

The fabric is drawn corner-to-corner, so everything BEHIND it is worth ~0 px and the
Juliet rail is the measured positive control for exactly that (built, in frustum, zero
pixels). The header is the one item on the panel's list that is NOT behind the fabric:
the track line is the pocket's ROOM edge, so a board hung there sits in FRONT of every
layer and is occluded by nothing.

AND IT IS THE HALF NO CURTAIN STATE CAN FIX. Census over all 706 `curtain_sheer`
columns of p2r93b: 455 run off the TOP FRAME EDGE, and of the 251 that do not, 233
(92.8%) have `ceiling_paint` in the pixel immediately above with ZERO rows between —
a junction whose step is +0.054 and the WRONG SIGN (the ceiling is darker than the
fabric). Parking the fabric moves it sideways; it never gives it a top.

WHAT IS DERIVED vs WHAT IS DECLARED
-----------------------------------
DERIVED (from spec data, fail-loud when it disagrees with itself):
  * the legs, from `curtains.curtain_legs` — the SAME trimmed track-vs-glass
    intersection the fabric hangs on. This module does not re-derive them from
    `curtain_track.path_mm`: two derivations of one geometry agree the day they are
    written and diverge on the first edit, with nothing failing when they do.
  * the run: the union of each leg's drawn span and its park zone, so the board covers
    the fabric wherever that fabric is allowed to be — including after a re-park.
  * the plane: the pocket's room edge = leg plane + sign x pocket, from
    `curtains.pocket_mm` (250, ink 247.6-250.8 across three legs).
  * the top: `room.ceiling_mm`. The board hangs FROM the ceiling; it never floats.
DECLARED ASSUMPTION, `[est]`, render-tier — and this module is the reason
`curtains.still_owner` had to be amended in the same commit rather than quietly
overruled. That key reads, verbatim: "heights (head/pelmet height - no z on a furniture
plan), track hardware/fabric SKU, and the physical curtain-track cross-section are
SILENT on this tier - supplier/RCP questions, do not invent."  A furniture plan carries
no elevation, so the DROP and the SECTION cannot be read from the drawing of record and
are not invented silently here: they are named, defaulted, overridable per build, and
printed into the render path so the owner can overrule them from the image (R3), the
same treatment `exterior.juliet_rail` gives a rail it can see but cannot dimension.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import curtains as _curtains

MM = 0.001

# ---------------------------------------------------------------- [est] CONVENTION --
# DROP: how far the board hangs below the ceiling. Must clear an S-fold carrier + hook
# (the make-up the spec signs) and must be deep enough to READ at the eye camera. 150
# is the bracket's low end; `--pelmet-drop=` moves it and the gate prints the value.
DROP_MM = 150.0
# SECTION: a plausible board. Sits PROUD of the pocket into the room, so it can never
# touch the front layer (the blackout's room face is 10 mm inside the pocket edge) and
# never consumes pocket depth `curtains._layer_offsets` has already allocated.
THICK_MM = 18.0
# The board's own bottom return — the stiffener that stops a 150 mm board reading as a
# paper strip. It runs BACK toward the glass, so it can only occupy pocket depth the
# fabric does not; the module CAPS it at the measured free gap and reports the cap
# rather than trusting this number (see `_return_cap`). Zero disables it outright.
RETURN_MM = 30.0
# Air the return must leave between itself and the front layer's swept envelope. A
# return that merely touches the fabric is a contact this repo has shipped before.
RETURN_CLEAR_MM = 4.0
# Below this, a return is joinery nobody can see and geometry that can only collide.
RETURN_MIN_MM = 8.0


class HeaderError(ValueError):
    """A header that cannot be derived. Raised, never warned: a pelmet placed by a
    guess is the 'typed position' R9 exists to forbid."""


def _return_cap(layers, pocket):
    """How far the bottom return may run back toward the glass, in mm, DERIVED.

    The pocket is not free space: `curtains._layer_offsets` has already allocated it,
    glass side first, and the only depth left room-side of the frontmost layer is that
    function's own `GAP_ROOM_MM` air. On the canonical spec that is exactly 10.0 mm, so
    the 30 mm return this module would otherwise have typed lands 18 mm INSIDE the
    blackout's swept envelope — a solid board through the fabric, which nothing in the
    render would have failed on and which the matmask would have shown as pelmet
    pixels where cloth belongs.

    So the number is measured off the layer stack instead of chosen, and when the
    answer is "there is no room", the return is DROPPED and said so — an absent
    stiffener is honest, a stiffener inside the curtain fabricates a reading (R10).
    """
    offs, _scale = _curtains._layer_offsets(layers, pocket)
    _l, centre, amp = offs[-1]              # frontmost = room side, by _layer_offsets' own order
    free = pocket - (centre + amp)
    return max(0.0, free - RETURN_CLEAR_MM), free


def header_parts(spec, drop_mm=None, thick_mm=None, return_mm=None):
    """spec (mm) -> ([part, ...], meta) with parts in METRES.

    part = {name, x, y, z, dx, dy, dz} — an axis-aligned box, add_box's own signature.
    Returns ([], meta) when the spec carries no curtains block (opt-in, exactly like
    curtain_ribbons: a spec without curtain data renders as it did before).
    """
    g = _curtains.curtain_legs(spec)
    if g is None:
        return [], {"legs": 0, "why": "spec carries no curtains block"}

    drop = float(DROP_MM if drop_mm is None else drop_mm)
    thick = float(THICK_MM if thick_mm is None else thick_mm)
    back = float(RETURN_MM if return_mm is None else return_mm)
    if drop <= 0:
        raise HeaderError(f"pelmet drop must be positive, got {drop}")
    if thick <= 0:
        raise HeaderError(f"pelmet section must be positive, got {thick}")

    ceil = float((spec.get("room") or {}).get("ceiling_mm") or 0.0)
    if ceil <= 0:
        raise HeaderError("room.ceiling_mm missing or zero — the header hangs FROM the "
                          "ceiling; without it the board would float (R9b: a mass with "
                          "no support is the defect, not the workaround)")
    pocket = float(g["pocket"])
    cap, free = _return_cap(g["layers"], pocket)
    back_asked = back
    back = min(back, cap)
    if back < RETURN_MIN_MM:
        back = 0.0
    parts = []
    rows = []
    for leg in g["legs"]:
        lo, hi = leg["drawn"]
        if leg["park"]:
            # cover the fabric wherever it is ALLOWED to be, not merely where it is
            # today — a re-park (render_state.park_end_over_glass) must not slide the
            # stack out from under its own header.
            lo = min(lo, leg["park"][0])
            hi = max(hi, leg["park"][1])
        if hi - lo <= 1.0:
            raise HeaderError(f"leg {leg['name']!r} spans {hi - lo:.1f} mm — nothing to head")
        # the pocket's ROOM edge, then PROUD into the room by the section. `sign` is
        # +1 when the room is on the +plane side, so `sign` carries the direction and
        # nothing here needs to know which compass leg it is looking at.
        edge = leg["plane"] + leg["sign"] * pocket
        f0 = edge
        f1 = edge + leg["sign"] * thick
        z0 = ceil - drop
        rows.append({"leg": leg["name"], "run_mm": hi - lo, "plane_mm": edge,
                     "z0_mm": z0, "z1_mm": ceil})

        def _box(tag, a_lo, a_hi, b_lo, b_hi, zz0, zz1):
            b_lo, b_hi = min(b_lo, b_hi), max(b_lo, b_hi)
            if leg["axis"] == "y":       # leg runs along y; `plane` is an x
                x0, x1, y0, y1 = b_lo, b_hi, a_lo, a_hi
            else:                        # leg runs along x; `plane` is a y
                x0, x1, y0, y1 = a_lo, a_hi, b_lo, b_hi
            parts.append({"name": f"pelmet__{leg['name']}_{tag}",
                          "x": x0 * MM, "y": y0 * MM, "z": zz0 * MM,
                          "dx": (x1 - x0) * MM, "dy": (y1 - y0) * MM,
                          "dz": (zz1 - zz0) * MM})

        _box("fascia", lo, hi, f0, f1, z0, ceil)
        if back > 0:
            # the return runs BACK toward the glass along the board's bottom edge —
            # into the pocket, whose room edge is `edge`, so it can only ever occupy
            # depth the fabric does not use (the front layer's room face is inside it).
            _box("return", lo, hi, edge, edge - leg["sign"] * back, z0, z0 + thick)

    meta = {"legs": len(g["legs"]), "drop_mm": drop, "thick_mm": thick,
            "return_mm": back, "return_asked_mm": back_asked,
            "return_cap_mm": cap, "pocket_free_room_side_mm": free,
            "return_dropped": back == 0.0 and back_asked > 0.0,
            "ceiling_mm": ceil, "pocket_mm": pocket,
            "n_parts": len(parts), "rows": rows,
            "est": "drop/section/return are DECLARED ASSUMPTIONS (render-tier): a "
                   "furniture plan carries no elevation and curtains.still_owner names "
                   "pelmet height and track cross-section as supplier/RCP questions. "
                   "Owner overrules from the image (R3); --pelmet-drop= moves it."}
    return parts, meta
