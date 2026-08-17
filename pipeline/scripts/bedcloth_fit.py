"""bedcloth_fit.py — ONE staging pipeline for an acquired bed-cloth set, shared by
the build and by every tool that auditions candidates for it. Layer 2 (needs `bpy`).

WHY IT EXISTS, and it is the third instance of a shape this repo has already named
twice. `_place_bed_cloth` (the build), `bedcloth_bench` (measures every cached
candidate) and `bedcloth_shoot` (renders the survivors for the eye) each carried
their own copy of: which parts of the file are cloth, how to scale it, where to put
it, and what to measure. The copies drifted, and the drift decided a purchase:

  * p2r32 corrected the PART CUT in the build — one question ("does this part cover
    a third of the mattress?") was doing two jobs, so the FIELD test was also
    throwing away every accessory cloth, including one set's 374 x 1600 mm turned
    runner. The build got `field >= 0.33` plus `extra >= 0.05`. **The bench and the
    shoot were never told**, so from p2r32 to p2r41 every candidate was auditioned
    with its runners and top sheets deleted, and the eye judged bare duvets.
  * The bench COMPUTES a rotation (to decide the scale that would fit after turning
    the set) and then never applies it, so it measures coverage on an unrotated set
    scaled as if it had been turned.
  * Neither tool ran the size rule the spec declares (`model_requirements.covers`,
    `max_scale`), which is what refused the asset p2r31 actually bought.

R9b's law is about objects and this is the same law about code: **a rule spread
across the callers is a rule with one exemption per caller.** The audition and the
build now stage a candidate through the same function, so "what the eye judged" and
"what the frame renders" cannot be two different objects again.

WHAT IS *NOT* HERE, on purpose: the sidecar/scale assertion (the DOOR, `_model_path`),
the `model_fit` plan rung, the coverage cut, the value-ladder re-dress and the shading
normaliser. Those are the BUILD's policy about whether to accept a set and how to
finish it. An audition tool must be able to stage a candidate the build would refuse —
that is what an audition is for — and it must never be able to change the staging.
"""
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from bedcloth_rules import (BURIED_SHARE, COVER_CUT, EXTRA_FRAC,  # noqa: F401
                            FALL_CUT, FIELD_FRAC, POLY_FLOOR, built_survives,
                            classify_areas, fineness, limits_for, plan_scale,
                            survives)


def edge_mm(o):
    """Median EDGE LENGTH of a mesh in WORLD millimetres, or None.

    The number no rung in this repo measured until p2r45, and the one that separates
    the meshes the critics accept from the mesh they call carved plastic: in the
    p2r44 frame the acquired pillows measure 4.5 and 10.3 mm and the acquired cover
    measures 43.2. It is read in world space on purpose — a fine mesh scaled up to
    cover a bed is a coarse mesh, and the file's own units are not the question."""
    me = getattr(o, "data", None)
    if me is None or not len(me.edges):
        return None
    M = o.matrix_world
    v = me.vertices
    ls = sorted(((M @ v[e.vertices[0]].co) - (M @ v[e.vertices[1]].co)).length
                for e in me.edges)
    return ls[len(ls) // 2] * 1000.0


def world_bbox(o):
    wc = [o.matrix_world @ v.co for v in o.data.vertices]
    if not wc:
        return None
    return (min(c.x for c in wc), min(c.y for c in wc), min(c.z for c in wc),
            max(c.x for c in wc), max(c.y for c in wc), max(c.z for c in wc))


def _bvh(objs):
    verts, tris = [], []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        off = len(verts)
        verts.extend([o.matrix_world @ v.co for v in me.vertices])
        tris.extend([tuple(i + off for i in t.vertices) for t in me.loop_triangles])
    if not tris:
        return None
    return BVHTree.FromPolygons(verts, tris)


def top_map(objs, rect, top_z, n=32):
    """Ray DOWN over the mattress plan: (x, y, z_or_None) per grid point.

    Rays, never bounding boxes — R9b one level up: a box cannot tell a spread sheet
    from a crumpled one, and the box version of this guard passed a set covering 60%
    of the bed."""
    bv = _bvh(objs)
    rx, ry, rw, rd = rect
    if bv is None:
        return []
    out = []
    for i in range(n):
        for j in range(n):
            x = rx + rw * (i + 0.5) / n
            y = ry + rd * (j + 0.5) / n
            loc, _, _, _ = bv.ray_cast(Vector((x, y, top_z + 3.0)),
                                       Vector((0, 0, -1)), 6.0)
            out.append((x, y, None if loc is None else loc.z))
    return out


def classify(meshes, mat_area, field_frac=FIELD_FRAC, extra_frac=EXTRA_FRAC,
             poly_floor=POLY_FLOOR):
    """(field, extra, drop) objects, by the pure rule in `bedcloth_rules`."""
    items, by_key = [], {}
    for n, o in enumerate(meshes):
        bb = world_bbox(o)
        area = None if bb is None else (bb[3] - bb[0]) * (bb[4] - bb[1])
        items.append((n, area, len(o.data.polygons)))
        by_key[n] = o
    f, e, d = classify_areas(items, mat_area, field_frac, extra_frac, poly_floor)
    return ([by_key[k] for k in f], [by_key[k] for k in e], [by_key[k] for k in d])


def group_bbox(objs):
    bbs = [world_bbox(o) for o in objs]
    bbs = [b for b in bbs if b]
    if not bbs:
        return None
    return (min(b[0] for b in bbs), min(b[1] for b in bbs), min(b[2] for b in bbs),
            max(b[3] for b in bbs), max(b[4] for b in bbs), max(b[5] for b in bbs))


def measure(objs, rect, top_z, base_z, n=40):
    """coverage / relief_mm / fall_sides for a staged set.

    coverage    fraction of mattress plan grid points with cloth above the mattress
    relief_mm   p90-p10 spread of that cloth's height — a MADE bed is low and even
    fall_sides  how many of the four flanks carry cloth below the mattress top; a
                duvet on a made bed falls over its sides, and this is the number
                p2r31 printed and read past while ranking on coverage alone
    """
    rx, ry, rw, rd = rect
    bv = _bvh(objs)
    if bv is None:
        return 0.0, 0.0, 0
    hits, zs = 0, []
    for i in range(n):
        for j in range(n):
            x = rx + rw * (i + 0.5) / n
            y = ry + rd * (j + 0.5) / n
            loc, _, _, _ = bv.ray_cast(Vector((x, y, top_z + 1.2)),
                                       Vector((0, 0, -1)), 2.0)
            if loc is not None and loc.z > top_z - 0.02:
                hits += 1
                zs.append(loc.z - top_z)
    cov = hits / float(n * n)
    zs.sort()
    relief = ((zs[int(0.9 * (len(zs) - 1))] - zs[int(0.1 * (len(zs) - 1))]) * 1000.0
              if len(zs) > 4 else 0.0)
    sides = 0
    for (ox, oy, dx, dy) in ((rx - 0.06, None, 1, 0), (rx + rw + 0.06, None, -1, 0),
                             (None, ry - 0.06, 0, 1), (None, ry + rd + 0.06, 0, -1)):
        got = 0
        for k in range(9):
            t = (k + 0.5) / 9.0
            px, py = ((rx + rw * t, oy) if ox is None else (ox, ry + rd * t))
            loc, _, _, _ = bv.ray_cast(Vector((px, py, top_z - 0.05)),
                                       Vector((dx, dy, 0)), 0.12)
            if loc is not None:
                got += 1
        if got >= 3:
            sides += 1
    return cov, relief, sides


def stage(news, rect, top_z, base_z, limit, cover=None, max_scale=1.0,
          apply_rot=False, log=print):
    """Stage an imported candidate onto THIS bed. `news` is every object the import
    created; `rect` is the mattress plan (x, y, w, d); `limit`/`cover` are the
    ceiling and floor from `limits_for` (see `plan_scale`).

    Returns a dict, or {"reject": why} — a rejection is a fact about the file, not an
    exception, because a bench has to print it and move on.

    Order is load-bearing and every step was paid for by a measured mistake:
      1. PRUNE BEFORE FIT — routed through the generic fitter, a set was rejected at
         1.39x because the file's 2 m junk cube was read as the model's height.
      2. Fit and CENTRE on the mattress plan.
      3. ALIGN BY THE CLOTH'S OWN SLEEPING PLANE, never by the set's bottom: these
         files ship their own mattress, so a bottom anchor buries the covers inside
         ours — a white slab with a knot of cloth on it, which is what the first
         acquired frame rendered. The plateau is the MEDIAN top over the plan, which
         pillows and hanging folds cannot drag.
      4. DROP WHAT IS BURIED (that is what removes the file's own mattress).
      5. Measure by RAY.
    Rotation is applied LAST and only if asked, because the build measures coverage
    before turning the set and the audition must not measure a different object.
    """
    rx, ry, rw, rd = rect
    mat_area = rw * rd
    meshes = [o for o in news if o.type == 'MESH']
    field, extra, drop = classify(meshes, mat_area)
    if not field:
        return {"reject": f"no part covers {FIELD_FRAC * 100:.0f}% of the mattress "
                          f"in plan — this is not a bed cover",
                "parts_total": len(meshes)}
    keep = field + extra
    # FILTER THE LISTS FIRST, FREE SECOND — a removed object's StructRNA raises on
    # any attribute read, so every list that outlives a removal is rebuilt while its
    # members are still alive.
    dnames = {o.name for o in drop}
    news = [o for o in news if o.name not in dnames]
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)

    bb = group_bbox(keep)
    native = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
    s, rot, fit_w, fit_d, plan_s, need = plan_scale(native, limit, cover, max_scale)
    if need is not None and need > s + 1e-9:
        return {"reject": f"to cover {cover[0]*1000:.0f} x {cover[1]*1000:.0f} mm "
                          f"this {native[0]*1000:.0f} x {native[1]*1000:.0f} mm set "
                          f"needs {need:.3f}x, past the {s:.3f}x this bed allows",
                "parts_total": len(meshes), "need_scale": need, "allowed": s,
                "native_mm": [round(v * 1000) for v in native]}
    roots = [o for o in news if o.parent is None] or news
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)
    bpy.context.view_layer.update()
    bb = group_bbox(keep)
    cx, cy = rx + rw / 2.0, ry + rd / 2.0
    dx, dy = cx - (bb[0] + bb[3]) / 2.0, cy - (bb[1] + bb[4]) / 2.0
    for o in roots:
        o.location = (o.location.x + dx, o.location.y + dy, o.location.z)
    bpy.context.view_layer.update()

    tops = [t for t in top_map(keep, rect, top_z) if t[2] is not None]
    if tops:
        zs = sorted(t[2] for t in tops)
        dz = (top_z + 0.015) - zs[len(zs) // 2]
    else:
        dz = base_z - bb[2]
    for o in roots:
        o.location = (o.location.x, o.location.y, o.location.z + dz)
    bpy.context.view_layer.update()

    buried = []
    if len(keep) > 1:
        allmap = {(round(t[0], 6), round(t[1], 6)): t[2]
                  for t in top_map(keep, rect, top_z) if t[2] is not None}
        for o in keep:
            own = [t for t in top_map([o], rect, top_z) if t[2] is not None]
            if not own:
                buried.append(o)
                continue
            seen = sum(1 for t in own
                       if t[2] >= allmap.get((round(t[0], 6), round(t[1], 6)),
                                             -1e9) - 0.004)
            if seen / float(len(own)) < BURIED_SHARE:
                buried.append(o)
        if buried and len(buried) < len(keep):
            bnames = {o.name for o in buried}
            for o in buried:
                keep.remove(o)
                (field if o in field else extra).remove(o)
            news = [o for o in news if o.name not in bnames]
            roots = [o for o in roots if o.name not in bnames]
            for o in buried:
                bpy.data.objects.remove(o, do_unlink=True)
            if not field:
                return {"reject": "every field part is BURIED — this set does not "
                                  "dress a bed", "parts_total": len(meshes)}
        else:
            buried = []

    cov, relief, sides = measure(keep, rect, top_z, base_z)
    if apply_rot and rot:
        piv = Vector((cx, cy, 0.0))
        T = (Matrix.Translation(piv) @ Matrix.Rotation(rot * 3.14159265358979 / 180.0,
                                                       4, 'Z')
             @ Matrix.Translation(-piv))
        for o in roots:
            o.matrix_world = T @ o.matrix_world
        bpy.context.view_layer.update()
    return {"field": field, "extra": extra, "keep": keep, "news": news,
            "roots": roots, "scale": s, "plan_scale": plan_s, "rot": rot,
            "need_scale": need, "fit": (fit_w, fit_d),
            "native_mm": [round(v * 1000) for v in native],
            "coverage": cov, "relief_mm": relief, "fall_sides": sides,
            "parts_total": len(meshes), "parts_dropped": len(drop),
            "parts_buried": len(buried), "height_mm": native[2] * s * 1000.0}
