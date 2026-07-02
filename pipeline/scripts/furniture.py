"""
furniture.py — parametric furniture as simple primitive boxes (INCHES).

Pure Python (NO bpy): each builder returns a list of boxes
  (name, x, y, z, dx, dy, dz)   # inches; x,y = SW corner of the whole item
that a materializer (build_room.py) turns into geometry. This keeps furniture
RECOGNIZABLE in renders (a sofa reads as a sofa, not a gray box) without any
external CC0 asset download — and because it returns plain data, it is unit-testable
with plain `python`. Real CC0 GLTF assets can later override a kind via a library map;
until then these primitives are the zero-dependency fallback.

Convention: an item's "front" faces -Y (toward the south wall / the viewer). Backs,
headboards, etc. sit on the +Y (far) side. A future spec `facing` field can rotate this.
"""

LEG = 2.0          # default leg cross-section (in)


def parts(kind, name, x, y, w, d, h):
    """Return the list of primitive boxes for one furniture item (inches)."""
    return _BUILDERS.get(kind, _block)(name, x, y, w, d, h)


def _block(name, x, y, w, d, h):
    return [(name, x, y, 0.0, w, d, h)]


def _sofa(name, x, y, w, d, h):
    arm = min(8.0, w * 0.18)
    back = min(8.0, d * 0.25)
    seat_h = h * 0.45
    inner_w = max(w - 2 * arm, 1.0)
    seat_d = max(d - back, 1.0)
    parts = [
        (f"{name}:base", x + arm, y, 0.0, inner_w, d, seat_h),                       # seat base
        (f"{name}:back", x + arm, y + d - back, 0.0, inner_w, back, h),              # backrest (far/+Y)
        (f"{name}:arm_L", x, y, 0.0, arm, d, h * 0.72),
        (f"{name}:arm_R", x + w - arm, y, 0.0, arm, d, h * 0.72),
    ]
    # split SEAT cushions + BACK pillows so it reads plush, not a solid block.
    n = max(1, int(round(inner_w / 26.0)))            # ~26in per cushion
    gap = 1.0
    cw = (inner_w - gap * (n - 1)) / n
    for i in range(n):
        cx = x + arm + i * (cw + gap)
        parts.append((f"{name}:seat{i}", cx + 0.5, y + 1.0, seat_h, max(cw - 1, 1.0),
                      max(seat_d - 2, 1.0), seat_h * 0.45))                          # seat cushion
        parts.append((f"{name}:pillow{i}", cx + 2.0, y + d - back - 3.0, seat_h + seat_h * 0.45,
                      max(cw - 4, 1.0), 5.0, max(h - seat_h - seat_h * 0.45 - 2, 3.0)))  # back pillow
    return parts


def _table(name, x, y, w, d, h):
    t = min(2.0, max(h * 0.1, 0.75))
    legs = _four_legs(name, x, y, w, d, h - t, LEG)
    return [(f"{name}:top", x, y, h - t, w, d, t)] + legs


def _chair(name, x, y, w, d, h):
    seat_h = h * 0.45
    back = min(2.0, d * 0.15)
    t = 1.5
    legs = _four_legs(name, x, y, w, d, seat_h, LEG)
    return legs + [
        (f"{name}:seat", x, y, seat_h, w, d, t),
        (f"{name}:back", x, y + d - back, seat_h, w, back, h - seat_h),             # backrest (far/+Y)
    ]


def _bed(name, x, y, w, d, h):
    frame_h = h * 0.35
    matt_h = h * 0.25
    head = min(4.0, d * 0.12)
    matt_top = frame_h + matt_h
    mw = max(w - 4, 1.0)
    md = max(d - head, 1.0)
    pil_d = min(16.0, md * 0.22)                        # pillow zone at the head (+Y)
    pw = max(mw / 2 - 3, 1.0)
    return [
        (f"{name}:frame", x, y, 0.0, w, d, frame_h),
        (f"{name}:mattress", x + 2, y, frame_h, mw, md, matt_h),
        # duvet: a soft top layer covering the foot 3/4, leaving the pillow zone
        (f"{name}:duvet", x + 1, y, matt_top, max(w - 2, 1.0), max(md - pil_d - 2, 1.0), 2.5),
        (f"{name}:pillow_L", x + 4, y + d - head - pil_d, matt_top, pw, pil_d, 5.0),
        (f"{name}:pillow_R", x + w - 4 - pw, y + d - head - pil_d, matt_top, pw, pil_d, 5.0),
        (f"{name}:headboard", x, y + d - head, 0.0, w, head, h),                    # headboard (far/+Y)
    ]


def _four_legs(name, x, y, w, d, leg_h, leg):
    return [
        (f"{name}:leg1", x, y, 0.0, leg, leg, leg_h),
        (f"{name}:leg2", x + w - leg, y, 0.0, leg, leg, leg_h),
        (f"{name}:leg3", x, y + d - leg, 0.0, leg, leg, leg_h),
        (f"{name}:leg4", x + w - leg, y + d - leg, 0.0, leg, leg, leg_h),
    ]


_BUILDERS = {
    "sofa": _sofa,
    "loveseat": _sofa,
    "coffee_table": _table,
    "dining_table": _table,
    "desk": _table,
    "side_table": _table,
    "nightstand": _table,
    "chair": _chair,
    "dining_chair": _chair,
    "armchair": _chair,
    "bed": _bed,
    # tv_console, rug, cabinet, etc. -> _block (a clean box is the right primitive)
}
