"""Dress THIS bed with each candidate and shoot it — the owner's own method (his

CLI-ONLY: run by hand to shoot owner-eye bed-cloth candidates for bedcloth_bench; named in qa/open-decisions.json:1130 — triage 2026-08-25.
designer friend judges every 3D Warehouse model by eye for style fit), with the
machine doing only the parts an eye should not have to do: pruning junk, aligning the
sleeping plane, and reporting coverage.

Run: blender -b <built>.blend --python bedcloth_shoot.py -- <cache> <out_dir> slug,...

STAGING COMES FROM `bedcloth_fit`, THE BUILD'S OWN MODULE (p2r41). It used to be a
third private copy of those rules, and it was the pre-p2r32 copy: parts under 33% of
the mattress plan were deleted, so the eye judged every candidate with its runners and
top sheets missing — including the set whose runner the build then rendered. What the
eye is shown and what the frame renders now come out of one function.

The rotation IS applied here (the build turns the set after it measures coverage), so
the photograph shows the set the way it will actually sit on the bed.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedcloth_fit as fit  # noqa: E402
import mesh_import as MI    # noqa: E402  (one dispatch, all formats — never gltf-only)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CACHE = os.path.abspath(argv[0])
# ABSOLUTE, and it is not tidiness: Blender resolves a relative render.filepath
# against the DRIVE ROOT, so the first run of this file wrote its candidate shots to
# C:\_private\... instead of into the repo's own gitignored dir. A tool whose output
# lands somewhere nobody looks is the same defect as a queue with no consumer.
OUTDIR = os.path.abspath(argv[1])
SLUGS = argv[2].split(",")

matt = bpy.data.objects["bed__mattress"]
mw = [matt.matrix_world @ v.co for v in matt.data.vertices]
MX0, MY0 = min(c.x for c in mw), min(c.y for c in mw)
MX1, MY1 = max(c.x for c in mw), max(c.y for c in mw)
MTOP = max(c.z for c in mw)
RECT = (MX0, MY0, MX1 - MX0, MY1 - MY0)
base = bpy.data.objects.get("bed__base")
bw = [base.matrix_world @ v.co for v in base.data.vertices] if base else mw
BZ = max(c.z for c in bw)
LIMIT, COVER = fit.limits_for(RECT, MTOP, BZ)

# strip the bedding the build shipped; the candidates replace it
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ("cloth__acq" in o.name or o.name in
                             ("bed__coverlet", "bed__duvet", "bed__throw")):
        bpy.data.objects.remove(o, do_unlink=True)

# WHAT THE FRAME HAS ALREADY DRESSED, read AFTER the strip above so the cloth being
# replaced is not in it. A candidate part landing inside one of these is that object
# bought twice — the set's own pillows on top of ours (D-025). Same signed register
# as the fineness control; see `bedcloth_rules.duplicate_of_placed`.
AVOID = fit.acquired_objs()
print("SHOOT already dressed (candidate parts overlapping these are dropped): "
      + (", ".join(o.name for o in AVOID) if AVOID else "nothing"))

# ONE cloth material for every candidate, so the COMPARISON is of SHAPE, not of
# whatever colour each uploader baked in (the same reason the build re-dresses)
cm = bpy.data.materials.get("bed_duvet") or bpy.data.materials.new("bed_duvet")

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1000, 750
sc.render.resolution_percentage = 100
sc.cycles.samples = 24

os.makedirs(OUTDIR, exist_ok=True)
for slug in SLUGS:
    d = os.path.join(CACHE, slug)
    models = MI.model_files(d)          # any importable format, best first
    if not models:
        print(f"SHOOT {slug}: no importable model — skipped")
        continue
    news = MI.import_file(os.path.join(d, models[0]))
    names = [o.name for o in news]
    st = fit.stage(news, RECT, MTOP, BZ, LIMIT, cover=COVER,
                   apply_rot=True, avoid=AVOID)
    if "reject" in st:
        print(f"SHOOT {slug}: {st['reject']} — skipped")
    else:
        for o in st["keep"]:
            o["ph_model"] = True
            o.data.materials.clear()
            o.data.materials.append(cm)
        out = os.path.join(OUTDIR, f"bedcand_{slug[:12]}.png")
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print(f"SHOOT {slug}: {len(st['field'])} field + {len(st['extra'])} on-it "
              f"part(s), scale {st['scale']:.3f}, rot {st['rot']:.0f}, cover "
              f"{st['coverage']*100:.1f}%, fall {st['fall_sides']}/4 -> {out}")
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
