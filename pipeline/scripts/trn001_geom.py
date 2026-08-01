"""trn001_geom.py — TRN-001 reproduction blockout: PURE geometry model, no bpy.

LAYER LAW (pipeline/CLAUDE.md): rules/spec/solve = pure python; only the
materializer (trn001_build.py, run inside Blender) imports bpy. This module is
the ONE source of truth for the blockout's masses and named landmark points —
the camera solver (plain python) and the Blender builder both import it, so the
solve and the render can never disagree about where a corner is.

Scene: generic prayer-room feature wall (reproduction study TRN-001,
qa/reproduction-curriculum.md — committed files carry the TRN-id and generic
descriptions only; the target mapping lives under _private/).

World frame: mm. Feature-wall FACE is the plane y=0 with the ROOM at y<0, so a
camera at negative y with Blender euler (90°, 0, -yaw) looks +Y at the wall and
world +x = frame right (checked against Blender's own world_to_camera_view by
the builder, which dumps its projections for the solver to cross-verify).
z up, floor z=0. yaw_deg positive = camera panned toward the RIGHT side of the
wall. Verticals stay vertical (pitch 0); framing height comes from shift_y.
"""
import json
import math

MM = 0.001  # mm -> Blender metres


# ---------------------------------------------------------------- masses ----

def _box(name, cx, cy, cz, sx, sy, sz, value, radii=None):
    """Axis-aligned mass. cx/cy/cz = CENTER (mm); sx/sy/sz = full size (mm).
    radii = optional plan-view corner radii (front-left, front-right, back-left,
    back-right; 'front' = room side, y<0) for an extruded rounded-rect.
    value = clay grey so masses separate in the LOOK overlay."""
    return {"name": name, "c": (cx, cy, cz), "s": (sx, sy, sz),
            "value": value, "radii": radii or (0.0, 0.0, 0.0, 0.0)}


def rounded_outline(cx, cy, sx, sy, radii, seg=8):
    """Plan-view outline [(x, y)] of a rect centred at (cx, cy), size (sx, sy),
    with per-corner radii (front-left, front-right, back-left, back-right);
    'front' = -y (the room side). Counter-clockwise seen from +z.

    PURE and here (not in the bpy layer) so the clamp below is testable: a
    radius can never exceed HALF THE SHORTER SIDE, which is why an 18 mm-thick
    drawer face cannot carry a 120 mm plan curve — the curve has to live on a
    mass with the depth to hold it (2026-07-31: caught by reading the clamp,
    after a test had pinned the requested radius instead of the built one)."""
    hx, hy = sx / 2.0, sy / 2.0
    r_fl, r_fr, r_bl, r_br = [max(0.0, min(r, hx, hy)) for r in radii]
    corners = [(-hx, -hy, r_fl, math.pi, 1.5 * math.pi),
               (+hx, -hy, r_fr, 1.5 * math.pi, 2.0 * math.pi),
               (+hx, +hy, r_br, 0.0, 0.5 * math.pi),
               (-hx, +hy, r_bl, 0.5 * math.pi, math.pi)]
    pts = []
    for x, y, r, a0, a1 in corners:
        if r <= 0:
            pts.append((cx + x, cy + y))
            continue
        ccx, ccy = x - math.copysign(r, x), y - math.copysign(r, y)
        for i in range(seg + 1):
            a = a0 + (a1 - a0) * i / seg
            pts.append((cx + ccx + r * math.cos(a), cy + ccy + r * math.sin(a)))
    return pts


def effective_radii(mass):
    """The radii a mass will ACTUALLY be built with, after the clamp."""
    hx, hy = mass["s"][0] / 2.0, mass["s"][1] / 2.0
    return tuple(max(0.0, min(r, hx, hy)) for r in mass["radii"])


def _tower_masses(side, cx, t, z_top, plinth_h):
    """Round-2 joinery: an OPEN CARCASS tower — two side panels, a back panel,
    top and bottom boards, shelf boards, and a recessed toe base on whichever
    tower stands on the floor. Authored boards, never a boolean-carved solid
    (pipeline law: booleans make n-gons a SketchUp recipient would see).
    Shelf heights come from the spec as measured z values, per side, because
    the target's two towers do NOT share a shelf ladder."""
    out = []
    w, d = t["w_mm"], t["d_mm"]
    # TWO depths, not one (2026-08-01). d_mm is how far the carcass stands PROUD
    # of the wall face; pocket_mm is how much further the CAVITY continues BEHIND
    # it, into the wall. Rounds 1-4 had a single parameter for both, so proving
    # the proud depth (100 mm, confirmed again today to 1.7 mm) looked like it
    # had also settled the cavity — and it had not. Cavity = d + pocket.
    pk = t.get("pocket_mm", 0.0)
    b = t.get("board_mm", 18)
    st = t.get("shelf_t_mm", 30)
    carcass, cavity = 0.28, 0.13
    on_plinth = (side == "L" and t.get("left_on_plinth"))
    z_floor = plinth_h if on_plinth else 0.0
    # The floor-standing tower reads as FLOATING: its lit face stops ~99 mm
    # above the floor and bare floor shows beneath (measured 2026-07-31 by
    # luminance, not assumed) — so the toe is a deep recess, and above it a
    # solid base block whose top is the lowest cubby's floor.
    toe_h = 0.0 if on_plinth else t.get("toe_h_mm", 0.0)
    z_base = z_floor + toe_h
    base_top = t.get("base_top_mm") if not on_plinth else None
    if base_top is None:
        base_top = z_base + b
    if toe_h > 0:
        ts = t.get("toe_setback_mm", 20)
        out.append(_box(f"tower_{side}_toe", cx, -(d - ts) / 2, z_floor + toe_h / 2,
                        w, d - ts, toe_h, 0.18))
    z0 = base_top
    out.append(_box(f"tower_{side}_base", cx, -d / 2, (z_base + base_top) / 2,
                    w, d, base_top - z_base, carcass))
    out.append(_box(f"tower_{side}_back", cx, pk + b / 2, (z0 + z_top) / 2,
                    w, b, z_top - z0, cavity))
    side_d, side_y = d + pk + b, (pk + b - d) / 2
    for tag, xoff in (("sA", -(w - b) / 2), ("sB", +(w - b) / 2)):
        out.append(_box(f"tower_{side}_{tag}", cx + xoff, side_y, (z0 + z_top) / 2,
                        b, side_d, z_top - z0, carcass))
    inner_w, inner_y, inner_d = w - 2 * b, -(d - pk) / 2, d + pk
    out.append(_box(f"tower_{side}_top", cx, inner_y, z_top - b / 2,
                    inner_w, inner_d, b, carcass))
    for i, sz in enumerate(t.get(f"shelves_{side}_z", [])):
        out.append(_box(f"tower_{side}_shelf{i}", cx, inner_y, sz + st / 2,
                        inner_w, inner_d, st, carcass))
    return out


def _recess_masses(rc, m, x0, x1, z0, z1):
    """THE SLAB IS RECESSED INTO THE WALL (owner, 2026-07-31: "ไฟที่ต้องซ่อนใน
    กำแพงคือแผ่นหินอ่อนอยู่ลึกลงไป ไม่ใช้อยู่ด้านหน้ากำแพง"). The wall's front
    layer runs from the room face (y=0) back to the recess depth, with a
    rectangular opening; the stone sits at the BACK of that opening and the LED
    hides just inside the returns, so nothing but the wash is ever in view.

    Four boxes around the opening rather than a boolean hole — a boolean would
    make the n-gons the export law forbids."""
    dep = rc["depth_mm"]
    ycen, ydep = dep / 2.0, dep
    g = rc.get("gap_mm", 20.0)
    mcx = m.get("cx_mm", 0.0)
    ox0, ox1 = mcx - m["w_mm"] / 2 - g, mcx + m["w_mm"] / 2 + g
    oz0 = m["bot_z_mm"] - g
    oz1 = m["bot_z_mm"] + m["h_mm"] + g
    v = 0.80
    return [
        _box("recess_jambL", (x0 + ox0) / 2, ycen, (z0 + z1) / 2, ox0 - x0, ydep, z1 - z0, v),
        _box("recess_jambR", (ox1 + x1) / 2, ycen, (z0 + z1) / 2, x1 - ox1, ydep, z1 - z0, v),
        _box("recess_head", (ox0 + ox1) / 2, ycen, (oz1 + z1) / 2, ox1 - ox0, ydep, z1 - oz1, v),
        _box("recess_sill", (ox0 + ox1) / 2, ycen, (z0 + oz0) / 2, ox1 - ox0, ydep, oz0 - z0, v),
    ]


def _wall_layer_masses(openings, x0, x1, z0, z1, dep, v=0.80):
    """The wall's front layer as a TILING around N openings that must not
    overlap in x — piers between them, a head above and a sill below each.

    Generalises _recess_masses, which could only ever cut ONE hole. The tower
    cavities pocket into the same wall the marble does, so a single-hole wall
    layer silently BLOCKED them: the jamb box spanning out to the wall edge runs
    straight through both towers. Same shape as every other defect this project
    has lost to an omission — the wall had no way to know a second opening
    existed, so it quietly filled it in."""
    ops = sorted(openings, key=lambda o: o[0])
    for a, b in zip(ops, ops[1:]):
        if b[0] < a[1]:
            raise ValueError(f"wall openings overlap in x: {a} and {b}")
    out, cursor = [], x0
    for i, (ox0, ox1, oz0, oz1) in enumerate(ops):
        ox0, ox1 = max(ox0, x0), min(ox1, x1)
        if ox1 <= ox0:
            continue
        if ox0 - cursor > 1e-6:
            out.append(_box(f"wall_pier{i}", (cursor + ox0) / 2, dep / 2,
                            (z0 + z1) / 2, ox0 - cursor, dep, z1 - z0, v))
        if z1 - oz1 > 1e-6:
            out.append(_box(f"wall_head{i}", (ox0 + ox1) / 2, dep / 2,
                            (oz1 + z1) / 2, ox1 - ox0, dep, z1 - oz1, v))
        if oz0 - z0 > 1e-6:
            out.append(_box(f"wall_sill{i}", (ox0 + ox1) / 2, dep / 2,
                            (z0 + oz0) / 2, ox1 - ox0, dep, oz0 - z0, v))
        cursor = ox1
    if x1 - cursor > 1e-6:
        out.append(_box("wall_pierN", (cursor + x1) / 2, dep / 2, (z0 + z1) / 2,
                        x1 - cursor, dep, z1 - z0, v))
    return out


def wall_front_depth(u):
    """How deep the feature wall's front layer runs — the DEEPEST thing that
    pockets into it. Lives here, in one place, because a test or a builder that
    recomputes it from recess.depth_mm alone goes stale the moment something
    else pockets deeper (which is exactly how the towers got filled in)."""
    rc = u.get("recess")
    t = u.get("tower", {})
    pk = t.get("pocket_mm", 0.0)
    return max(rc["depth_mm"] if rc else 0.0,
               pk + t.get("board_mm", 18) if pk else 0.0)


def stone_back_y(u):
    """The y of the marble's BACK face. The wall body must start at or behind
    it: the stone is set INTO the recess, so a wall that starts at the recess
    depth (70) contains the stone (70..88) outright, with coincident front
    faces. That was live from the moment the recess landed — the hero object
    was winning a BVH coin flip, and it lost the flip the day a second box was
    added behind it. Coplanar faces are not a style question."""
    m = u["marble"]
    face_y = -m["proud_mm"]
    return face_y + m.get("thick_mm", m["proud_mm"])


def marble_opening(rc, m):
    """The marble's hole in the wall, as (x0, x1, z0, z1)."""
    g = rc.get("gap_mm", 20.0)
    mcx = m.get("cx_mm", 0.0)
    return (mcx - m["w_mm"] / 2 - g, mcx + m["w_mm"] / 2 + g,
            m["bot_z_mm"] - g, m["bot_z_mm"] + m["h_mm"] + g)


def tower_openings(u, z_top):
    """The two tower cavities' holes in the wall, as (x0, x1, z0, z1) — empty
    when the towers do not pocket, so a pre-2026-08-01 spec is untouched."""
    t, h = u["tower"], u["header"]
    if not t.get("pocket_mm"):
        return []
    hcx, w = h.get("cx_mm", 0.0), t["w_mm"]
    z_bot = t.get("base_top_mm") or 0.0
    out = []
    for sgn in (-1, 1):
        cx = hcx + sgn * (h["len_mm"] / 2 - w / 2)
        out.append((cx - w / 2, cx + w / 2, z_bot, z_top))
    return out


def _header_masses(h, x_in):
    """Round-2 joinery: the band is THREE faced panels split on the tower inner
    faces (the joints the reference shows), separated by a shadow reveal, each
    carrying a brass rectangle inset from its own panel edges."""
    out = []
    hcx, L = h.get("cx_mm", 0.0), h["len_mm"]
    z1, bh, dep = h["top_z_mm"], h["band_h_mm"], h["depth_mm"]
    z0 = z1 - bh
    rev = h.get("reveal_mm", 4.0)
    joints = h.get("joints_x_mm", [hcx - x_in, hcx + x_in])
    bounds = [hcx - L / 2] + sorted(joints) + [hcx + L / 2]
    br = h.get("brass") or {}
    inset, bw, proud = br.get("inset_mm", 45.0), br.get("width_mm", 6.0), br.get("proud_mm", 2.0)
    for i in range(len(bounds) - 1):
        x0 = bounds[i] + (rev / 2 if i else 0.0)
        x1 = bounds[i + 1] - (rev / 2 if i + 2 < len(bounds) else 0.0)
        pw, pcx = x1 - x0, (x0 + x1) / 2
        out.append(_box(f"header_p{i}", pcx, -dep / 2, (z0 + z1) / 2, pw, dep, bh, 0.45))
        if not br or pw <= 2 * inset + 2 * bw or bh <= 2 * inset + 2 * bw:
            continue
        by, bd = -(dep + proud / 2), proud
        iz0, iz1 = z0 + inset, z1 - inset
        ix0, ix1 = x0 + inset, x1 - inset
        out.append(_box(f"brass_p{i}_top", pcx, by, iz1 - bw / 2, ix1 - ix0, bd, bw, 0.62))
        out.append(_box(f"brass_p{i}_bot", pcx, by, iz0 + bw / 2, ix1 - ix0, bd, bw, 0.62))
        for tag, bx in (("l", ix0 + bw / 2), ("r", ix1 - bw / 2)):
            out.append(_box(f"brass_p{i}_{tag}", bx, by, (iz0 + iz1) / 2,
                            bw, bd, iz1 - iz0 - 2 * bw, 0.62))
    return out


def downlight_positions(spec):
    """[(name, x_mm, y_mm, measured)] — the ONE source of fixture positions, so
    the housings the camera sees and the lights that emit can never drift apart.

    The in-frame row is a MEASUREMENT, not a layout choice: the two lenses in
    the target were found as bright disks and back-projected onto the ceiling
    plane, and both landed at y = -605 mm off the wall to within 0.5 mm — two
    fixtures on one line, which is what a wall-wash row is.

    Everything beyond that row is INFERRED and says so: the frame only shows
    the ceiling back to y ~= -880 (camera z 1150, 49.3 deg vertical fov), so no
    further row can be measured from this image. The continuation uses the
    measured COLUMN pitch as the row pitch — a square grid, the default a
    lighting layout falls back to — and exists only to supply the room's ambient
    at the level the measured ladder demands."""
    lt = spec.get("light") or {}
    dl = lt.get("downlights") or {}
    xs = list(dl.get("x_mm") or [])
    if not xs:
        return []
    y0 = float(dl["row_y_mm"])
    rows = [(y0, True)]
    pitch = dl.get("fill_pitch_mm")
    if pitch is None and len(xs) > 1:
        pitch = abs(max(xs) - min(xs))          # square grid off the measured pair
    depth = spec["room"]["room_depth_mm"]
    y = y0 - (pitch or 0.0)
    while pitch and y > -depth:
        rows.append((y, False))
        y -= pitch
    out = []
    for ri, (yy, measured) in enumerate(rows):
        for ci, x in enumerate(xs):
            out.append((f"dl_r{ri}c{ci}", float(x), float(yy), measured))
    return out


def _downlight_masses(spec):
    """A recessed downlight the camera can SEE: a trim flange with a lit lens
    inside it. PRJ-2026-002's lane A learned this the expensive way — a room lit
    by sources with no visible origin reads as lit by nothing — and the target
    shows both trims plainly.

    The flange is an annulus, which a boolean would carve and the export law
    forbids. So it is built as two solids instead: the lens disk sits 1 mm BELOW
    the trim's underside, which hides the middle of the trim's bottom cap and
    leaves exactly the visible ring. Same trick as the recess returns — the
    shape you want, made of the shapes you are allowed to author."""
    lt = spec.get("light") or {}
    dl = lt.get("downlights") or {}
    pos = downlight_positions(spec)
    if not pos:
        return []
    ceil = spec["room"]["ceiling_mm"]
    lens_d = float(dl.get("lens_dia_mm", 88.0))
    trim_d = float(dl.get("trim_dia_mm", 112.0))
    drop = float(dl.get("trim_drop_mm", 12.0))
    out = []
    for name, x, y, _measured in pos:
        z_t = ceil - drop
        out.append(_box(f"{name}_trim", x, y, z_t + drop / 2, trim_d, trim_d, drop,
                        0.35, radii=(trim_d / 2,) * 4))
        out.append(_box(f"{name}_lens", x, y, z_t + 4.0, lens_d, lens_d, 10.0,
                        1.0, radii=(lens_d / 2,) * 4))
    return out


def _plinth_masses(p):
    """Round-2 joinery: handleless push-open drawer bank over a recessed toe.

    The bank is the body: N FULL-DEPTH drawer prisms (so the two outer ones can
    carry the real plan curve — see rounded_outline's clamp) separated by
    shadow-gap reveals, and each gap is BACKED by a set-back strip so a reveal
    reads as a groove instead of a see-through slot. The outer plane and the
    rounded ends therefore stay exactly where round 1's camera solve fitted
    them."""
    out = []
    cx, L, h, d, r = p.get("cx_mm", 0.0), p["len_mm"], p["h_mm"], p["d_mm"], p["r_mm"]
    toe_h = p.get("toe_h_mm", 0.0)
    toe_set = p.get("toe_setback_mm", 40.0)
    n = int(p.get("drawers", 0))
    if toe_h > 0:
        out.append(_box("plinth_toe", cx, -(d - toe_set) / 2, toe_h / 2,
                        L - 2 * r, d - toe_set, toe_h, 0.30))
    zc, zh = (toe_h + h) / 2, h - toe_h
    if n <= 1:
        out.append(_box("plinth", cx, -d / 2, zc, L, d, zh, 0.85, radii=(r, r, 0, 0)))
        return out
    rev = p.get("reveal_mm", 4.0)
    rev_d = p.get("reveal_depth_mm", 20.0)
    # MEASURED reveal centres win over equal division: the target's two end
    # faces are wider than the middle three because they carry the curve, so an
    # equal split would be a tidier piece than the one that was built.
    cuts = p.get("reveal_x_mm")
    if cuts:
        cuts = sorted(cuts)[:n - 1]
    else:
        fw = (L - rev * (n - 1)) / n
        cuts = [cx - L / 2 + (i + 1) * fw + i * rev + rev / 2 for i in range(n - 1)]
    edges = [cx - L / 2] + list(cuts) + [cx + L / 2]
    for i in range(n):
        x0 = edges[i] + (rev / 2 if i else 0.0)
        x1 = edges[i + 1] - (rev / 2 if i + 1 < n else 0.0)
        name = "plinth" if i == 0 else f"plinth_face{i}"
        out.append(_box(name, (x0 + x1) / 2, -d / 2, zc, x1 - x0, d, zh, 0.85,
                        radii=(r if i == 0 else 0.0, r if i == n - 1 else 0.0, 0, 0)))
        if i:
            out.append(_box(f"plinth_reveal{i}", edges[i], -(d - rev_d) / 2, zc,
                            rev, d - rev_d, zh, 0.55))
    return out


def masses(spec):
    """Spec dict -> list of mass dicts. Every dimension read here is mm.
    Room sits at y<0; positive spec depths are applied toward the room.
    Joinery detail is OPT-IN per element (spec keys present) so a round-1
    blockout stays reproducible byte-for-byte."""
    u = spec["unit"]
    room = spec["room"]
    out = []

    ceil = room["ceiling_mm"]
    depth = room["room_depth_mm"]
    wall_len = room["back_wall_len_mm"]
    # The unit is built INTO the left corner — in the target the ceiling/wall
    # junction line runs out and dies exactly on the unit's top-left corner. So
    # the corner DERIVES from the unit rather than carrying its own number:
    # a hard-coded wall position went stale the moment round 3 re-derived the
    # carcass wider and further left, and left the wall cutting 185 mm into it
    # (owner spotted it: "ทำไมกำแพงซ้ายขยับเข้ามา"). Same class as every other
    # decision this project has lost to an omission — so it is now impossible
    # to change the unit without the room following.
    if room.get("wall_follows_unit", True):
        unit_left = u["header"].get("cx_mm", 0.0) - u["header"]["len_mm"] / 2
        wall_off = -(unit_left + wall_len / 2)
    else:
        wall_off = room.get("unit_center_offset_mm", 0.0)

    # room shell (floor, back wall, ceiling, left side wall at frame-left = -x).
    # When the feature wall carries a RECESS, the wall body is pushed back by
    # the recess depth and a front layer with the opening is added below, so the
    # room face still reads at y=0 while the stone sits inside the wall.
    rc = u.get("recess")
    # The wall's front layer must be at least as deep as the DEEPEST thing that
    # pockets into it. The marble keeps its own measured 70 mm reveal via a back
    # plate, so deepening the layer for the towers cannot move the stone.
    rdep = wall_front_depth(u)
    body_y0 = max(rdep, stone_back_y(u)) if rc else rdep
    out.append(_box("floor", -wall_off, -depth / 2, -50, wall_len, depth, 100, 0.65))
    out.append(_box("back_wall", -wall_off, body_y0 + 50, ceil / 2, wall_len, 100, ceil, 0.80))
    out.append(_box("ceiling", -wall_off, -depth / 2, ceil + 50, wall_len, depth, 100, 0.82))
    lx = -wall_off - wall_len / 2
    out.append(_box("side_wall_L", lx - 50, -depth / 2, ceil / 2, 100, depth, ceil, 0.80))
    # ROUND 4: close the box. Rounds 1-3 lit an open three-sided set, which is
    # why the ladder measured our ceiling as bright as our walls (1.21 vs the
    # target's 0.73 relative) and our blacks lifted 2.7x — with no room to bounce
    # in, every surface can only take light straight from the source, and light
    # that should have come back off a wall left the scene instead. The two
    # closing surfaces are both outside the frame (the right wall stands beyond
    # the unit, the front wall 250 mm behind the camera station), so they change
    # no silhouette the camera was fitted to — they only give the light somewhere
    # to come from. Opt-in, so a round-1..3 spec still renders byte-identically.
    if room.get("close_box"):
        rx = -wall_off + wall_len / 2
        out.append(_box("side_wall_R", rx + 50, -depth / 2, ceil / 2, 100, depth, ceil, 0.80))
        out.append(_box("front_wall", -wall_off, -depth - 50, ceil / 2, wall_len, 100, ceil, 0.80))

    # header band across the top (one solid, or three faced panels + brass)
    h = u["header"]
    hcx = h.get("cx_mm", 0.0)
    t = u["tower"]
    x_in = h["len_mm"] / 2 - t["w_mm"]
    if h.get("joints_x_mm") or h.get("brass"):
        out.extend(_header_masses(h, x_in))
    else:
        out.append(_box("header", hcx, -h["depth_mm"] / 2,
                        h["top_z_mm"] - h["band_h_mm"] / 2,
                        h["len_mm"], h["depth_mm"], h["band_h_mm"], 0.45))

    # towers (-> header underside); the LEFT tower stands on the plinth when
    # the spec says so (target reads asymmetric), the right on the floor
    tz = h["top_z_mm"] - h["band_h_mm"]
    for side, sgn in (("L", -1), ("R", 1)):
        cx = hcx + sgn * (h["len_mm"] / 2 - t["w_mm"] / 2)
        if t.get(f"shelves_{side}_z"):
            out.extend(_tower_masses(side, cx, t, tz, u["plinth"]["h_mm"]))
            continue
        z0t = u["plinth"]["h_mm"] if (side == "L" and t.get("left_on_plinth")) else 0.0
        out.append(_box(f"tower_{side}", cx, -t["d_mm"] / 2, (tz + z0t) / 2,
                        t["w_mm"], t["d_mm"], tz - z0t, 0.28))

    m = u["marble"]
    if rc:
        wx0, wx1 = -wall_off - wall_len / 2, -wall_off + wall_len / 2
        tops = tower_openings(u, tz)
        if not tops:
            out.extend(_recess_masses(rc, m, wx0, wx1, 0.0, ceil))
        else:
            mo = marble_opening(rc, m)
            out.extend(_wall_layer_masses([mo] + tops, wx0, wx1, 0.0, ceil, rdep))
            # the stone's reveal is a MEASUREMENT (70 mm); it stays 70 mm no
            # matter how deep the towers made the wall, so the marble opening
            # gets its own back plate at exactly that depth.
            bp0 = stone_back_y(u)
            if rdep - bp0 > 1e-6:
                out.append(_box("recess_backplate", (mo[0] + mo[1]) / 2,
                                (bp0 + rdep) / 2, (mo[2] + mo[3]) / 2,
                                mo[1] - mo[0], rdep - bp0,
                                mo[3] - mo[2], 0.80))

    # A THIN slab held OFF the wall, not a thick panel stuck to it — the
    # standoff cavity is where the concealed light lives, and modelling the slab
    # as a solid the full depth of the standoff left the LED buried inside the
    # stone with nowhere for its light to go (caught 2026-07-31). proud_mm stays
    # the FRONT face, so the camera solve's marble landmarks are untouched.
    thick = m.get("thick_mm", m["proud_mm"])
    # proud_mm = the stone's FRONT face relative to the room-side wall plane.
    # POSITIVE = proud of the wall; NEGATIVE = set back INTO it, which is what
    # this piece does — the whole point of the concealed detail.
    face_y = -m["proud_mm"]
    out.append(_box("marble", m.get("cx_mm", 0.0), face_y + thick / 2,
                    m["bot_z_mm"] + m["h_mm"] / 2,
                    m["w_mm"], thick, m["h_mm"], 0.75))

    # white drawer plinth with rounded front corners; cx_mm because the target
    # reads ASYMMETRIC (plinth runs on under the left tower to the unit's outer
    # edge; the left tower stands ON it while the right tower stands on floor)
    p = u["plinth"]
    if p.get("drawers") or p.get("toe_h_mm"):
        out.extend(_plinth_masses(p))
    else:
        out.append(_box("plinth", p.get("cx_mm", 0.0), -p["d_mm"] / 2, p["h_mm"] / 2,
                        p["len_mm"], p["d_mm"], p["h_mm"], 0.85,
                        radii=(p["r_mm"], p["r_mm"], 0, 0)))

    # altar stack: wide step -> centre box -> side pedestals (all on plinth top)
    s = u["step"]
    out.append(_box("step", s.get("cx_mm", 0.0), -s["d_mm"] / 2,
                    p["h_mm"] + s["h_mm"] / 2,
                    s["len_mm"], s["d_mm"], s["h_mm"], 0.58,
                    radii=(s["r_mm"], s["r_mm"], 0, 0)))
    b = u["box"]
    bcx = b.get("cx_mm", 0.0)
    z0 = p["h_mm"] + s["h_mm"]
    out.append(_box("centre_box", bcx, -b["d_mm"] / 2,
                    z0 + b["h_mm"] / 2,
                    b["w_mm"], b["d_mm"], b["h_mm"], 0.40,
                    radii=(b["r_mm"], b["r_mm"], 0, 0)))
    # The side pedestals are symmetric about the CENTRE BOX, not about the room
    # centreline — measured 2026-07-31 at 705.1 / 704.3 mm from the box centre
    # after the owner spotted that ours sat unequal. Anchoring them to x=0 while
    # the box sits off-centre guarantees the asymmetry he saw.
    q = u["pedestal"]
    for side, sgn in (("L", -1), ("R", 1)):
        out.append(_box(f"pedestal_{side}", bcx + sgn * q["cx_mm"], -q["d_mm"] / 2,
                        z0 + q["h_mm"] / 2, q["w_mm"], q["d_mm"], q["h_mm"], 0.48,
                        radii=(q["r_mm"], q["r_mm"], 0, 0)))

    # CONCEALED LIGHTING (owner, 2026-07-31: "แผ่นด้านหลังพระ จริง ๆ คือไฟซ่อน
    # เข้าไป"). The slab is not a lit panel — it stands off the wall and an LED
    # strip hides in the gap behind its edge, so the wall around it takes the
    # wash and the source is never in view. Built as four strips set BEHIND the
    # slab face and inset from its edge, which is what makes them invisible.
    if m.get("halo"):
        halo = m["halo"]
        mcx = m.get("cx_mm", 0.0)
        t_ = halo.get("strip_mm", 22.0)
        # The strip is mounted on the RETURN of the recess, tucked just inside
        # the opening so the wall's own edge hides it, and it faces back at the
        # stone. setback = how far inside the opening it sits.
        setback = halo.get("setback_mm", 20.0)
        gp = rc.get("gap_mm", 20.0) if rc else 20.0
        ycen, ydep = setback + t_ / 2, t_
        ox0, ox1 = mcx - m["w_mm"] / 2 - gp, mcx + m["w_mm"] / 2 + gp
        oz0 = m["bot_z_mm"] - gp
        oz1 = m["bot_z_mm"] + m["h_mm"] + gp
        out.append(_box("halo_top", (ox0 + ox1) / 2, ycen, oz1 - t_ / 2,
                        ox1 - ox0, ydep, t_, 1.0))
        out.append(_box("halo_bot", (ox0 + ox1) / 2, ycen, oz0 + t_ / 2,
                        ox1 - ox0, ydep, t_, 1.0))
        for tag, hx in (("l", ox0 + t_ / 2), ("r", ox1 - t_ / 2)):
            out.append(_box(f"halo_{tag}", hx, ycen, (oz0 + oz1) / 2,
                            t_, ydep, oz1 - oz0 - 2 * t_, 1.0))

    out.extend(_downlight_masses(spec))
    return out


# ------------------------------------------------------------- landmarks ----

def landmarks_3d(spec):
    """Named fixed 3D points (mm) used by the camera solve. Only true corners —
    occlusion-dependent points (marble_*_low, tower bases) are LOOK-only and
    deliberately absent. Front faces sit at negative y.

    SILHOUETTE CONVENTION for rounded-corner masses (matches what the numeric
    measurers could actually probe in the target): the left/right extreme of a
    rounded end is the arc's outermost 3D extent (x = ±L/2 at y = -(d - r)),
    NOT the rounding-onset point — from an oblique camera the silhouette
    tangent sits within ~r of that, far closer than the onset corner.
    header_bot_* is the visible JUNCTION of the tower inner-front edge with the
    header underside, which lives on the TOWER front plane (header is deeper)."""
    u = spec["unit"]
    h, t, m = u["header"], u["tower"], u["marble"]
    p, s, b = u["plinth"], u["step"], u["box"]
    zb = h["top_z_mm"] - h["band_h_mm"]
    hcx = h.get("cx_mm", 0.0)
    x_in = h["len_mm"] / 2 - t["w_mm"]          # tower inner face offset from hcx
    z0 = p["h_mm"] + s["h_mm"]
    pcx, scx = p.get("cx_mm", 0.0), s.get("cx_mm", 0.0)
    bcx, mcx = b.get("cx_mm", 0.0), m.get("cx_mm", 0.0)
    return {
        "header_top_left":  (hcx - h["len_mm"] / 2, -h["depth_mm"], h["top_z_mm"]),
        "header_top_right": (hcx + h["len_mm"] / 2, -h["depth_mm"], h["top_z_mm"]),
        "header_bot_left":  (hcx - x_in, -t["d_mm"], zb),
        "header_bot_right": (hcx + x_in, -t["d_mm"], zb),
        "marble_top_left":  (mcx - m["w_mm"] / 2, -m["proud_mm"], m["bot_z_mm"] + m["h_mm"]),
        "marble_top_right": (mcx + m["w_mm"] / 2, -m["proud_mm"], m["bot_z_mm"] + m["h_mm"]),
        "plinth_top_left":  (pcx - p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), p["h_mm"]),
        "plinth_top_right": (pcx + p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), p["h_mm"]),
        "plinth_bot_left":  (pcx - p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), 0.0),
        "plinth_bot_right": (pcx + p["len_mm"] / 2, -(p["d_mm"] - p["r_mm"]), 0.0),
        "box_top_left":     (bcx - b["w_mm"] / 2, -(b["d_mm"] - b["r_mm"]), z0 + b["h_mm"]),
        "box_top_right":    (bcx + b["w_mm"] / 2, -(b["d_mm"] - b["r_mm"]), z0 + b["h_mm"]),
        "step_top_left":    (scx - s["len_mm"] / 2, -(s["d_mm"] - s["r_mm"]), p["h_mm"] + s["h_mm"]),
        "step_top_right":   (scx + s["len_mm"] / 2, -(s["d_mm"] - s["r_mm"]), p["h_mm"] + s["h_mm"]),
        **{f"plinth_top_rev{i}": (x, -p["d_mm"], p["h_mm"])
           for i, x in enumerate(p.get("reveal_x_mm", []))},
    }


# ------------------------------------------------------------ projection ----

SENSOR_MM = 36.0  # full-frame width, horizontal fit; square render shares it


def cam_basis(yaw_deg):
    """forward/right/up world vectors for pitch-0 camera, +yaw = pan right."""
    yw = math.radians(yaw_deg)
    fwd = (math.sin(yw), math.cos(yw), 0.0)
    right = (math.cos(yw), -math.sin(yw), 0.0)
    return fwd, right, (0.0, 0.0, 1.0)


def project(cam, pt, res=2048):
    """Pinhole projection matching the builder's Blender camera
    (euler XYZ = (90°, 0, -yaw), shift-framed). Returns (u_px, v_px), origin
    top-left, v down. Sign conventions are cross-verified against Blender's
    world_to_camera_view dump on every build (trn001_build writes both)."""
    fwd, right, _ = cam_basis(cam["yaw_deg"])
    dx, dy, dz = (pt[0] - cam["x_mm"], pt[1] - cam["y_mm"], pt[2] - cam["z_mm"])
    depth = dx * fwd[0] + dy * fwd[1]
    if depth <= 1.0:
        return None
    xc = dx * right[0] + dy * right[1]
    k = cam["focal_mm"] / SENSOR_MM
    u = res * (0.5 + k * xc / depth + cam.get("shift_x", 0.0))
    v = res * (0.5 - k * dz / depth + cam.get("shift_y", 0.0))
    return (u, v)


def project_all(cam, spec, res=2048):
    return {n: project(cam, p, res) for n, p in landmarks_3d(spec).items()}


def first_hit(cam, pt, spec, skip=(), tol=1e-3):
    """Walk the ray from the camera toward `pt` and name the first mass that
    BLOCKS it. Returns (mass_name, t) or (None, None) if the point is visible.

    A mass counts as blocking only if the ray LEAVES it before reaching the
    point (exit t < 1 - tol). That is what makes the test usable on a surface
    sample: the box the point sits on, and the box it sits inside, both still
    contain the ray at t=1 and so are not mistaken for occluders. `tol` is in
    ray-length units — on this camera's ~4 m rays the default is about 4 mm.

    THE PLANE-IS-NOT-THE-SURFACE GUARD, made available instead of remembered.
    backproject() answers where a ray meets an infinite plane and knows nothing
    about extent or occlusion, so it will hand back a confident millimetre for a
    point no camera can see. That has now cost this project three times: a vase
    placed inside a pedestal, a bounding box that could not tell a vase from a
    plank, and a cubby back panel sampled straight through the side panel that
    hides it — where the giveaway was a luminance far too BRIGHT for 276 mm of
    depth. Any of the three would have been caught by asking this first.

    AABB test: masses with corner radii are treated as their full boxes, which
    can only over-report occlusion (conservative), never miss it."""
    c = (cam["x_mm"], cam["y_mm"], cam["z_mm"])
    d = tuple(pt[i] - c[i] for i in range(3))
    best, best_t = None, None
    for m in masses(spec) if isinstance(spec, dict) else spec:
        if m["name"] in skip:
            continue
        t0, t1 = 0.0, float("inf")
        for i in range(3):
            lo = m["c"][i] - m["s"][i] / 2
            hi = m["c"][i] + m["s"][i] / 2
            if abs(d[i]) < 1e-12:
                if not (lo - 1e-6 <= c[i] <= hi + 1e-6):
                    t0 = 1e9
                    break
                continue
            a, b = (lo - c[i]) / d[i], (hi - c[i]) / d[i]
            if a > b:
                a, b = b, a
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                break
        # blocks only if the ray is fully through this box before the point
        if t0 <= t1 and t1 < 1.0 - tol and (best_t is None or t0 < best_t):
            best, best_t = m["name"], t0
    return best, best_t


def backproject(cam, uv, plane, res=2048):
    """Inverse of project(): a measured target pixel + the PLANE it is known to
    lie on -> world mm. plane = (axis, value), axis in 'x'|'y'|'z'.

    This is what a solved camera buys: once the station is fitted, any pixel a
    probe can find on a face whose plane is known reads back as a real
    dimension — no proportion-guessing. Returns None when the ray is parallel
    to the plane or the hit lies behind the camera (never a silent bad number).
    """
    fwd, right, _ = cam_basis(cam["yaw_deg"])
    k = cam["focal_mm"] / SENSOR_MM
    a = (uv[0] / res - 0.5 - cam.get("shift_x", 0.0)) / k
    b = (0.5 + cam.get("shift_y", 0.0) - uv[1] / res) / k
    d = (fwd[0] + a * right[0], fwd[1] + a * right[1], b)
    c = (cam["x_mm"], cam["y_mm"], cam["z_mm"])
    i = "xyz".index(plane[0])
    if abs(d[i]) < 1e-12:
        return None
    t = (plane[1] - c[i]) / d[i]
    if t <= 0:
        return None
    return tuple(c[j] + t * d[j] for j in range(3))


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
