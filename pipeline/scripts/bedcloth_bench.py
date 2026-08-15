"""BED-CLOTH ACQUISITION BENCH — measure every candidate set against THIS bed,
before any of them costs a build.

Run:  blender -b <built>.blend --python bedcloth_bench.py -- <cache_dir> <out.json>

WHY IT EXISTS: p2r31's first acquired leg rendered a bare white mattress with a
knotted rag on it, and the coverage guard inside the build passed it — because
that guard compared BOUNDING BOXES, and a bounding box cannot tell a spread
sheet from a crumpled one (R9b's own lesson: an AABB cannot tell interlocking
from intersecting). This measures the thing itself: rays cast DOWN over the
mattress plan, so "covered" means cloth is actually above that point.

Three numbers per candidate, all derived from the bed in the open .blend —
nothing typed:
  coverage   fraction of mattress plan grid points with cloth above them
  relief_mm  p90-p10 spread of cloth height over the mattress — a MADE bed is
             low and even; a slept-in crumple piles high in places
  fall_sides how many of the four flanks carry cloth below the mattress top
             (a duvet on a made bed falls over the sides)
"""
import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CACHE, OUT = argv[0], argv[1]

matt = bpy.data.objects["bed__mattress"]
base = bpy.data.objects.get("bed__base")
mw = [matt.matrix_world @ v.co for v in matt.data.vertices]
MX0, MY0 = min(c.x for c in mw), min(c.y for c in mw)
MX1, MY1 = max(c.x for c in mw), max(c.y for c in mw)
MTOP = max(c.z for c in mw)
bw = [base.matrix_world @ v.co for v in base.data.vertices] if base else mw
BZ = max(c.z for c in bw)          # base top = where a hem may reach
print(f"BENCH bed: mattress {(MX1-MX0)*1000:.0f} x {(MY1-MY0)*1000:.0f} mm, "
      f"top {MTOP*1000:.0f}, base top {BZ*1000:.0f}")

# strip the existing bedding so it cannot be measured as a candidate's cloth
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ("cloth__acq" in o.name or o.name in
                             ("bed__coverlet", "bed__duvet", "bed__throw")):
        bpy.data.objects.remove(o, do_unlink=True)

MAT_AREA = (MX1 - MX0) * (MY1 - MY0)
FALL = MTOP - BZ
SLOT_H = FALL + 0.32
LX0, LY0 = MX0 - 0.02, MY0 - 0.02          # the bed line, as the build uses it
LW, LD = (MX1 - MX0) + 0.04, (MY1 - MY0) + 0.04


def wbb(o):
    wc = [o.matrix_world @ v.co for v in o.data.vertices]
    if not wc:
        return None
    return (min(c.x for c in wc), min(c.y for c in wc), min(c.z for c in wc),
            max(c.x for c in wc), max(c.y for c in wc), max(c.z for c in wc))


def measure(objs):
    """coverage / relief / fall — by RAY, never by box."""
    verts, tris = [], []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        off = len(verts)
        verts.extend([o.matrix_world @ v.co for v in me.vertices])
        tris.extend([tuple(i + off for i in t.vertices) for t in me.loop_triangles])
    if not tris:
        return 0.0, 0.0, 0
    bvh = BVHTree.FromPolygons(verts, tris)
    N = 44
    hits, zs = 0, []
    for i in range(N):
        for j in range(N):
            x = MX0 + (MX1 - MX0) * (i + 0.5) / N
            y = MY0 + (MY1 - MY0) * (j + 0.5) / N
            loc, _, _, _ = bvh.ray_cast(Vector((x, y, MTOP + 1.2)),
                                        Vector((0, 0, -1)), 2.0)
            if loc is not None and loc.z > MTOP - 0.02:
                hits += 1
                zs.append(loc.z - MTOP)
    cov = hits / float(N * N)
    zs.sort()
    relief = ((zs[int(0.9 * (len(zs) - 1))] - zs[int(0.1 * (len(zs) - 1))])
              * 1000.0) if len(zs) > 4 else 0.0
    # flanks: cast INWARD-facing rays just outside each mattress edge, below top
    sides = 0
    for (ox, oy, dx, dy) in ((MX0 - 0.06, None, 1, 0), (MX1 + 0.06, None, -1, 0),
                             (None, MY0 - 0.06, 0, 1), (None, MY1 + 0.06, 0, -1)):
        got = 0
        for k in range(9):
            t = (k + 0.5) / 9.0
            if ox is None:
                px, py = MX0 + (MX1 - MX0) * t, oy
            else:
                px, py = ox, MY0 + (MY1 - MY0) * t
            pz = MTOP - 0.05
            loc, _, _, _ = bvh.ray_cast(Vector((px, py, pz)),
                                        Vector((dx, dy, 0)), 0.12)
            if loc is not None:
                got += 1
        if got >= 3:
            sides += 1
    return cov, relief, sides


rows = []
for slug in sorted(os.listdir(CACHE)):
    d = os.path.join(CACHE, slug)
    if not os.path.isdir(d):
        continue
    glbs = [f for f in os.listdir(d) if f.endswith(".glb")]
    if not glbs:
        continue
    path = os.path.join(d, glbs[0])
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=path)
    except Exception as e:                                    # noqa: BLE001
        rows.append({"slug": slug, "error": str(e)[:80]})
        continue
    news = [o for o in bpy.data.objects if o not in before]
    news_names = [o.name for o in news]
    meshes = [o for o in news if o.type == 'MESH']
    keep, drop = [], []
    for o in meshes:
        bb = wbb(o)
        if bb is None or not o.data.polygons:
            drop.append(o)
            continue
        pa = (bb[3] - bb[0]) * (bb[4] - bb[1])
        (keep if (pa >= MAT_AREA * 0.33 and len(o.data.polygons) >= 100)
         else drop).append(o)
    row = {"slug": slug, "file": glbs[0], "parts_total": len(meshes),
           "parts_kept": len(keep)}
    if len(keep) < 1:
        row["verdict"] = "no bed-scale cloth part survived the cut"
        rows.append(row)
        for o in news:
            bpy.data.objects.remove(o, do_unlink=True)
        continue
    bbs = [wbb(o) for o in keep]
    mn = [min(b[i] for b in bbs) for i in range(3)]
    mx = [max(b[i] for b in bbs) for i in (3, 4, 5)]
    mw_, md_, mh_ = mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]
    rot = 90.0 if ((mw_ > md_) != (LW > LD)) else 0.0
    fit_w, fit_d = (LD, LW) if rot else (LW, LD)
    s = min(fit_w / max(mw_, 1e-6), fit_d / max(md_, 1e-6),
            SLOT_H / max(mh_, 1e-6))
    roots = [o for o in news if o.parent is None] or news
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)
    bpy.context.view_layer.update()
    bbs = [wbb(o) for o in keep]
    mn = [min(b[i] for b in bbs) for i in range(3)]
    mx = [max(b[i] for b in bbs) for i in (3, 4, 5)]
    cx, cy = (MX0 + MX1) / 2.0, (MY0 + MY1) / 2.0
    dx, dy = cx - (mn[0] + mx[0]) / 2.0, cy - (mn[1] + mx[1]) / 2.0
    for o in roots:
        o.location = (o.location.x + dx, o.location.y + dy, o.location.z)
    bpy.context.view_layer.update()

    # ALIGN BY THE CLOTH'S OWN SLEEPING PLANE, not by the set's bottom. These
    # files usually ship their OWN mattress, so anchoring the bottom to our base
    # buries the covers inside our mattress — which is exactly what the first
    # acquired frame rendered: a white slab (the file's mattress) with the
    # blanket knotted on top. The plateau is the MEDIAN top surface over the
    # plan, which pillows and hanging folds cannot drag around.
    def _topmap(objs, n=32):
        verts, tris = [], []
        for o in objs:
            me = o.data
            me.calc_loop_triangles()
            off = len(verts)
            verts.extend([o.matrix_world @ v.co for v in me.vertices])
            tris.extend([tuple(i + off for i in t.vertices)
                         for t in me.loop_triangles])
        if not tris:
            return None, []
        bv = BVHTree.FromPolygons(verts, tris)
        out = []
        for i in range(n):
            for j in range(n):
                x = MX0 + (MX1 - MX0) * (i + 0.5) / n
                y = MY0 + (MY1 - MY0) * (j + 0.5) / n
                loc, _, _, _ = bv.ray_cast(Vector((x, y, MTOP + 3.0)),
                                           Vector((0, 0, -1)), 6.0)
                if loc is not None:
                    out.append((x, y, loc.z))
        return bv, out

    _, tops = _topmap(keep)
    if tops:
        zs0 = sorted(t[2] for t in tops)
        plateau = zs0[len(zs0) // 2]
        dz = (MTOP + 0.015) - plateau
        for o in roots:
            o.location = (o.location.x, o.location.y, o.location.z + dz)
        bpy.context.view_layer.update()

    # DROP WHAT IS BURIED — the set's own mattress and any layer the covers
    # hide. A part earns its place by being the TOPMOST surface somewhere.
    if len(keep) > 1:
        _, alltop = _topmap(keep)
        vis = {}
        for o in keep:
            _, otop = _topmap([o])
            seen = 0
            for (x, y, z) in otop:
                for (ax, ay, az) in alltop:
                    if abs(ax - x) < 1e-6 and abs(ay - y) < 1e-6:
                        if z >= az - 0.004:
                            seen += 1
                        break
            vis[o.name] = seen / float(max(len(otop), 1))
        buried = [o for o in keep if vis.get(o.name, 1.0) < 0.15]
        if buried and len(buried) < len(keep):
            for o in buried:
                keep.remove(o)
                bpy.data.objects.remove(o, do_unlink=True)
            row["parts_buried"] = len(buried)

    cov, relief, sides = measure(keep)
    row.update({"scale": round(s, 3), "rot": rot,
                "coverage": round(cov, 3), "relief_mm": round(relief, 1),
                "fall_sides": sides,
                "native_mm": [round(mw_ / s * 1000), round(md_ / s * 1000),
                              round(mh_ / s * 1000)]})
    rows.append(row)
    print(f"BENCH {slug:12s} kept {len(keep):2d}/{len(meshes):2d}  "
          f"scale {s:5.3f}  coverage {cov*100:5.1f}%  relief {relief:6.1f} mm  "
          f"fall {sides}/4")
    for _nm in news_names:
        _ob = bpy.data.objects.get(_nm)
        if _ob is not None:
            bpy.data.objects.remove(_ob, do_unlink=True)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(rows, fh, indent=1)
print(f"BENCH wrote {OUT} ({len(rows)} candidate(s))")
