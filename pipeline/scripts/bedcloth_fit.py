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

from bedcloth_rules import (BURIED_SHARE, COVER_CUT, DUPLICATE_SHARE,  # noqa: F401
                            EXTRA_FRAC, FALL_CUT, FIELD_FRAC, POLY_FLOOR,
                            built_survives, choose_cover, classify_areas,
                            duplicate_of_placed, fineness, lies_on_the_bed,
                            limits_for, plan_scale, survives)


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


def acquired_objs(objs=None, exclude_prefix="bed__cloth__acq"):
    """The BOUGHT soft goods already standing in this frame.

    Membership is the value ladder's signed ACQUIRED_AS register — the same source
    `control_edges` uses and the same one `duplicate_of_placed` needs, so "what counts
    as already-dressed" is one fact and not two.
    """
    import value_ladder as _vl
    prefixes = {p for (p, _m) in _vl.ACQUIRED_AS.values()}
    out = []
    for o in (bpy.data.objects if objs is None else objs):
        if getattr(o, "type", None) != 'MESH':
            continue
        if exclude_prefix and o.name.startswith(exclude_prefix):
            continue
        if any(o.name.startswith(p) for p in prefixes):
            out.append(o)
    return out


def control_edges(objs=None, exclude_prefix="bed__cloth__acq"):
    """{object name: median world edge mm} for the acquired soft goods ALREADY
    ACCEPTED in this frame — the control `bedcloth_rules.fineness` compares a
    candidate cover against.

    IT LIVES HERE FOR THE REASON THIS WHOLE MODULE EXISTS. Ten lines of it sat
    inline in `_place_bed_cloth` from p2r45, which made the fineness cut a rule
    only the BUILD could ask: the bench measured every candidate's edge and could
    only RANK on it, because it had no control. So the audition went on nominating
    sets the build was then obliged to refuse — 0afd4c6f passed all three audition
    cuts and died at the build on a fourth the audition could not see. That is the
    module docstring's own defect ("a rule spread across the callers is a rule with
    one exemption per caller") reappearing in the rule written to fix it.

    Membership comes from `value_ladder.ACQUIRED_AS` — the signed register of which
    rungs are BOUGHT cloth — never from a list of names kept here (R9b: a rule that
    names the objects it applies to will always exempt the next one). The candidate
    cover itself is excluded by prefix: a cover cannot be its own control.
    """
    out = {}
    for o in acquired_objs(objs, exclude_prefix):
        e = edge_mm(o)
        if e:
            out[o.name] = e
    return out


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
          apply_rot=False, avoid=None, log=print):
    """Stage an imported candidate onto THIS bed. `news` is every object the import
    created; `rect` is the mattress plan (x, y, w, d); `limit`/`cover` are the
    ceiling and floor from `limits_for` (see `plan_scale`).

    Returns a dict, or {"reject": why} — a rejection is a fact about the file, not an
    exception, because a bench has to print it and move on.

    Order is load-bearing and every step was paid for by a measured mistake:
      1. PRUNE BEFORE FIT — routed through the generic fitter, a set was rejected at
         1.39x because the file's 2 m junk cube was read as the model's height.
      2. Fit and CENTRE on the mattress plan, both SOLVED ON THE COVER PART rather
         than on the file's bounding box — a set that ships with the bed it dresses
         was being refused for the bed's height and slid off the mattress by the
         bed's centre (p2r47; six of nine size-refusals were this).
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

    # THE FIT IS DERIVED FROM THE COVER, NEVER FROM THE WHOLE FILE (p2r47), and the
    # rule it replaces refused six of the nine sets it size-rejected for a height that
    # was never the cover's. `limits_for` says in its own words what the height ceiling
    # describes — "that drop plus the loft", i.e. what a COVER may be. It was being
    # applied to `group_bbox(field + extra)`, which for any set that ships with the bed
    # it dresses is the BED: 22897dd4 holds a 2018 x 1827 x 213 mm sheet of 74,136
    # triangles and was refused because the file around it stands 1243 mm tall, so the
    # ceiling collapsed to 0.576x and the cover's own 0.665x read as "too big". Same
    # shape as R9b one level over: a rule applied to a group it does not describe will
    # refuse the next one. The set still scales as ONE object — the author's internal
    # proportions are not ours to edit — but the scale is now solved on the part that
    # has to cover the mattress, and the file's own bed is removed where it always was,
    # by the buried test below.
    by_name, parts = {}, []
    for o in field:
        b = world_bbox(o)
        if not b:
            continue
        by_name[o.name] = o
        parts.append((o.name, (b[3] - b[0], b[4] - b[1], b[5] - b[2])))
    if not parts:
        return {"reject": "no measurable field part", "parts_total": len(meshes)}
    # THE DECISION IS PURE AND LIVES IN `bedcloth_rules` (layer law: rules are plain
    # Python, only the middle layer is Blender). This module supplies the bounding
    # boxes; it does not get its own copy of the choice.
    key, row, n_feasible = choose_cover(parts, limit, cover, max_scale)
    # `need <= s` RANKS THE PICK; IT NO LONGER REFUSES THE SET (p2r47). It is a
    # BOUNDING-BOX test, and this bench exists because a bounding box was the wrong
    # instrument: "a bounding box cannot tell a spread sheet from a crumpled one...
    # This measures the thing itself, by ray" (bedcloth_bench's own opening). The two
    # ray cuts downstream ask the same question better and at a stated tolerance —
    # `coverage >= 0.80` is "our mattress must not show" and `fall_sides >= 2` is "it
    # drapes" — while this proxy demanded a bbox spanning 100% of the mattress before
    # either could run. Measured on the shelf the day it changed: it refused FIVE
    # candidates at 1.011x, 1.046x, 1.066x, 1.087x and 1.125x, none of which was ever
    # rayed. The nearest missed by 20 mm on one axis. `max_scale` is untouched and
    # still binds the staging scale — nothing is stretched to fit; a set simply gets
    # staged AS AUTHORED and then has to survive the measurements that can see it.
    cover_obj = by_name[key]
    # the NAME is taken now, while the object is alive: the buried test below may
    # remove it, and a removed object's StructRNA raises on any attribute read
    cover_name = key
    native = dict(parts)[key]
    s, rot, fit_w, fit_d, plan_s, need = row
    roots = [o for o in news if o.parent is None] or news
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)
    bpy.context.view_layer.update()
    # CENTRE THE COVER ON THE MATTRESS, not the file's bounding box — same reason the
    # scale comes from the cover. A set that ships with its own bed frame has a group
    # centre that is the BED's, and centring on it slides the cloth off the mattress.
    bb = world_bbox(cover_obj) or group_bbox(keep)
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

    # DROP WHAT THE FRAME HAS ALREADY DRESSED (p2r47). A bedding set ships with its
    # own pillows; this bed's head pillows were acquired eleven rounds ago (D-025), so
    # the set's pair lands inside ours. `_place_bed_cloth` has SAID it buys "the duvet
    # + its turned-down top sheet... NOT the pillows" since p2r44 and nothing enforced
    # it; p2r47's audition shot rendered an 800 mm bolster standing through the
    # acquired head set. Geometric, never by name (R9b) — see `duplicate_of_placed`.
    dupes = []
    if avoid:
        abbs = [world_bbox(o) for o in avoid]
        for o in list(keep):
            share, is_dup = duplicate_of_placed(world_bbox(o), abbs)
            if is_dup:
                dupes.append((o.name, round(share, 3)))
        if dupes and len(dupes) < len(keep):
            dnames2 = {n for n, _s in dupes}
            gone = [o for o in keep if o.name in dnames2]
            for o in gone:
                keep.remove(o)
                (field if o in field else extra).remove(o)
            news = [o for o in news if o.name not in dnames2]
            roots = [o for o in roots if o.name not in dnames2]
            for o in gone:
                bpy.data.objects.remove(o, do_unlink=True)
            if not field:
                return {"reject": "every field part duplicates something already in "
                                  "the frame", "parts_total": len(meshes)}
        else:
            # dropping EVERYTHING would leave the bed bare, which is the failure this
            # rule is meant to prevent — report it and change nothing.
            dupes = [(n, s, "not dropped: it is the whole set") for n, s in dupes]

    # AND DROP WHAT IS NOT LYING ON THE BED AT ALL (p2r47). EXTRA means "a runner, a
    # folded top sheet" in `classify_areas`'s own words; a 545 mm bolster standing on
    # the corner is not that. Bounded by the declared loft, never a new number.
    standing = []
    for o in list(extra):
        b = world_bbox(o)
        ok, rise = lies_on_the_bed(None if not b else b[5], top_z)
        if not ok:
            standing.append((o.name, round(rise * 1000.0, 1)))
    if standing:
        snames = {n for n, _r in standing}
        gone = [o for o in keep if o.name in snames]
        for o in gone:
            keep.remove(o)
            extra.remove(o)
        news = [o for o in news if o.name not in snames]
        roots = [o for o in roots if o.name not in snames]
        for o in gone:
            bpy.data.objects.remove(o, do_unlink=True)

    cov, relief, sides = measure(keep, rect, top_z, base_z)
    if apply_rot and rot:
        piv = Vector((cx, cy, 0.0))
        T = (Matrix.Translation(piv) @ Matrix.Rotation(rot * 3.14159265358979 / 180.0,
                                                       4, 'Z')
             @ Matrix.Translation(-piv))
        for o in roots:
            o.matrix_world = T @ o.matrix_world
        bpy.context.view_layer.update()
    gb = group_bbox(keep)
    return {"field": field, "extra": extra, "keep": keep, "news": news,
            "roots": roots, "scale": s, "plan_scale": plan_s, "rot": rot,
            "need_scale": need, "fit": (fit_w, fit_d),
            "cover_name": cover_name,
            "cover_buried": cover_name not in {o.name for o in keep},
            "cover_candidates": len(parts), "cover_feasible": n_feasible,
            "native_mm": [round(v * 1000) for v in native],
            "set_native_mm": ([round((gb[3] - gb[0]) * 1000),
                               round((gb[4] - gb[1]) * 1000),
                               round((gb[5] - gb[2]) * 1000)] if gb else None),
            "coverage": cov, "relief_mm": relief, "fall_sides": sides,
            "parts_total": len(meshes), "parts_dropped": len(drop),
            "parts_buried": len(buried), "parts_duplicate": dupes,
            "parts_standing": standing,
            "height_mm": native[2] * s * 1000.0}
