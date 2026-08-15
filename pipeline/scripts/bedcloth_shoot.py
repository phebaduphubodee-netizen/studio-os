"""Dress THIS bed with each candidate and shoot it — the owner's own method
(his designer friend judges every 3D Warehouse model by eye for style fit),
with the machine doing only the parts an eye should not have to do: pruning
junk, aligning the sleeping plane, and reporting coverage.

Run: blender -b <built>.blend --python bedcloth_shoot.py -- <cache> <out_dir> slug,slug,...
"""
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CACHE, OUTDIR, SLUGS = argv[0], argv[1], argv[2].split(",")

matt = bpy.data.objects["bed__mattress"]
mw = [matt.matrix_world @ v.co for v in matt.data.vertices]
MX0, MY0 = min(c.x for c in mw), min(c.y for c in mw)
MX1, MY1 = max(c.x for c in mw), max(c.y for c in mw)
MTOP = max(c.z for c in mw)
base = bpy.data.objects.get("bed__base")
bw = [base.matrix_world @ v.co for v in base.data.vertices] if base else mw
BZ = max(c.z for c in bw)
MAT_AREA = (MX1 - MX0) * (MY1 - MY0)
SLOT_H = (MTOP - BZ) + 0.32
LW, LD = (MX1 - MX0) + 0.04, (MY1 - MY0) + 0.04

# strip the bedding the build shipped; the candidates replace it
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ("cloth__acq" in o.name or o.name in
                             ("bed__coverlet", "bed__duvet", "bed__throw")):
        bpy.data.objects.remove(o, do_unlink=True)

# one cloth material for every candidate, so the COMPARISON is of SHAPE, not of
# whatever colour each uploader baked in (the same reason the build re-dresses)
cm = bpy.data.materials.get("bed_duvet") or bpy.data.materials.new("bed_duvet")

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1000, 750
sc.render.resolution_percentage = 100
sc.cycles.samples = 24


def wbb(o):
    wc = [o.matrix_world @ v.co for v in o.data.vertices]
    if not wc:
        return None
    return (min(c.x for c in wc), min(c.y for c in wc), min(c.z for c in wc),
            max(c.x for c in wc), max(c.y for c in wc), max(c.z for c in wc))


def topmap(objs, n=32):
    verts, tris = [], []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        off = len(verts)
        verts.extend([o.matrix_world @ v.co for v in me.vertices])
        tris.extend([tuple(i + off for i in t.vertices) for t in me.loop_triangles])
    if not tris:
        return []
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
    return out


for slug in SLUGS:
    d = os.path.join(CACHE, slug)
    glbs = [f for f in os.listdir(d) if f.endswith(".glb")]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(d, glbs[0]))
    news = [o for o in bpy.data.objects if o not in before]
    names = [o.name for o in news]
    keep = []
    for o in [x for x in news if x.type == 'MESH']:
        bb = wbb(o)
        if bb is None or not o.data.polygons:
            continue
        if ((bb[3] - bb[0]) * (bb[4] - bb[1]) >= MAT_AREA * 0.33
                and len(o.data.polygons) >= 100):
            keep.append(o)
    if not keep:
        print(f"SHOOT {slug}: nothing bed-scale — skipped")
        continue
    bbs = [wbb(o) for o in keep]
    mn = [min(b[i] for b in bbs) for i in range(3)]
    mx = [max(b[i] for b in bbs) for i in (3, 4, 5)]
    mw_, md_, mh_ = mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]
    rot = 90.0 if ((mw_ > md_) != (LW > LD)) else 0.0
    fit_w, fit_d = (LD, LW) if rot else (LW, LD)
    s = min(fit_w / mw_, fit_d / md_, SLOT_H / mh_)
    roots = [o for o in news if o.parent is None] or news
    for o in roots:
        o.scale = tuple(v * s for v in o.scale)
    bpy.context.view_layer.update()
    bbs = [wbb(o) for o in keep]
    mn = [min(b[i] for b in bbs) for i in range(3)]
    mx = [max(b[i] for b in bbs) for i in (3, 4, 5)]
    for o in roots:
        o.location = (o.location.x + (MX0 + MX1) / 2 - (mn[0] + mx[0]) / 2,
                      o.location.y + (MY0 + MY1) / 2 - (mn[1] + mx[1]) / 2,
                      o.location.z)
    bpy.context.view_layer.update()
    tops = topmap(keep)
    if tops:
        zs = sorted(t[2] for t in tops)
        dz = (MTOP + 0.015) - zs[len(zs) // 2]
        for o in roots:
            o.location = (o.location.x, o.location.y, o.location.z + dz)
        bpy.context.view_layer.update()
    if rot:
        from mathutils import Matrix
        piv = Vector(((MX0 + MX1) / 2, (MY0 + MY1) / 2, 0.0))
        T = (Matrix.Translation(piv) @ Matrix.Rotation(rot * 3.14159265 / 180.0,
                                                       4, 'Z')
             @ Matrix.Translation(-piv))
        for o in roots:
            o.matrix_world = T @ o.matrix_world
        bpy.context.view_layer.update()
    for o in keep:
        o["ph_model"] = True
        o.data.materials.clear()
        o.data.materials.append(cm)
    out = os.path.join(OUTDIR, f"bedcand_{slug[:12]}.png")
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f"SHOOT {slug}: kept {len(keep)} part(s), scale {s:.3f} -> {out}")
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
