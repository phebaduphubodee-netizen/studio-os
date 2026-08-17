"""Probe: can SHRINKING THE BED or STRETCHING THE CLOTH reach the 80% duvet-share cut?

Owner question 2026-08-17: "แค่ลดขนาดก้อนเตียงเพื่อให้มันเข้ากับผ้า หรือขยายขาดผ้าเพื่อให้
มันคลุมเตียงไม่ได้หรือ"

p2r49 tested ONE lever (translation) and reported the free shelf exhausted. That was an
incomplete test and this probe is the rest of it. Everything below is measured on the
BUILT scene, not inferred from bounding boxes — the whole point of D-095 is that a
bbox cannot tell a spread cloth from a draped one.

  blender -b <built>.blend --python probe_duvet_levers.py
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r'c:/Users/teza_/OneDrive/Desktop/PlingPeat/pipeline/scripts')
import bedcloth_fit as fit                                        # noqa: E402

MATT = bpy.data.objects["bed__mattress"]
mw = [MATT.matrix_world @ v.co for v in MATT.data.vertices]
MX0, MY0 = min(c.x for c in mw), min(c.y for c in mw)
MX1, MY1 = max(c.x for c in mw), max(c.y for c in mw)
MTOP = max(c.z for c in mw)
RECT = (MX0, MY0, MX1 - MX0, MY1 - MY0)
print(f"PROBE mattress {RECT[2]*1000:.0f} (head-to-foot, x) x {RECT[3]*1000:.0f} "
      f"(width, y) mm, top {MTOP*1000:.0f}")

CLOTH = [o for o in bpy.data.objects
         if o.type == 'MESH' and o.name.startswith("bed__cloth__acq")]
DUVET = [o for o in CLOTH if o.data.materials and
         any(m and "duvet" in m.name for m in o.data.materials)]
SKIP = [fit.world_bbox(o) for o in fit.acquired_objs(exclude_prefix="bed__cloth__acq")]
print("PROBE cloth parts: " + ", ".join(
    f"{o.name}[{','.join(m.name for m in o.data.materials if m)}]" for o in CLOTH))
print("PROBE duvet-rung parts: " + ", ".join(o.name for o in DUVET))


def share(objs, rect, skip=SKIP, n=60):
    hs, pts = fit.plan_heights(objs, rect, MTOP, n=n, skip_bbs=skip)
    return (fit.duvet_share(hs, pts), pts,
            sum(1 for h in hs if h >= fit.DUVET_LOFT_MM))


s_all, pts, hit = share(CLOTH, RECT)
s_duv, _p, _h = share(DUVET, RECT)
cell = (RECT[2] / 60.0) * (RECT[3] / 60.0)
print(f"PROBE BASELINE  whole set {s_all*100:.1f}%   duvet parts alone "
      f"{s_duv*100:.1f}%  ({_h} of {pts} plan cells)")
print(f"PROBE duvet LOFTED FOOTPRINT over the mattress = {_h*cell:.3f} m2 "
      f"(mattress plan {RECT[2]*RECT[3]:.3f} m2)")

# ---- LEVER 1: SHRINK THE BED. The mattress rect narrows about its own centre; the
# cloth does not move. Nothing is rebuilt — this asks only "if the bed were this wide,
# what share would the SAME cloth cover?"
print("PROBE ---- lever 1: shrink the bed (cloth untouched)")
cy = MY0 + RECT[3] / 2.0
for w_mm in (1969, 1900, 1800, 1700, 1600, 1500, 1400, 1300, 1200):
    w = w_mm / 1000.0
    r = (MX0, cy - w / 2.0, RECT[2], w)
    sv, p, h = share(DUVET, r)
    bed_outer = w_mm + (2149 - 1969)
    print(f"PROBE   mattress width {w_mm:4d} mm (bed {bed_outer:4d}) -> duvet share "
          f"{sv*100:5.1f}%   {'CLEARS 80' if sv >= 0.80 else ''}")

# ---- LEVER 2: STRETCH THE CLOTH. Uniform, and across-the-width only. Scaled about
# the mattress centre so the cloth grows where it lies rather than sliding off.
print("PROBE ---- lever 2: stretch the cloth (bed untouched)")
import mathutils                                                  # noqa: E402
CX, CY = MX0 + RECT[2] / 2.0, MY0 + RECT[3] / 2.0
roots = []
for o in CLOTH:
    r = o
    while r.parent is not None:
        r = r.parent
    if r not in roots:
        roots.append(r)
base = {o.name: o.matrix_world.copy() for o in roots}


def restore():
    for o in roots:
        o.matrix_world = base[o.name].copy()
    bpy.context.view_layer.update()


def apply_scale(sx, sy, sz):
    piv = mathutils.Vector((CX, CY, MTOP))
    T = (mathutils.Matrix.Translation(piv)
         @ mathutils.Matrix.Diagonal((sx, sy, sz, 1.0))
         @ mathutils.Matrix.Translation(-piv))
    for o in roots:
        o.matrix_world = T @ base[o.name].copy()
    bpy.context.view_layer.update()


for tag, (sx, sy, sz) in (("uniform 1.10", (1.10, 1.10, 1.10)),
                          ("uniform 1.20", (1.20, 1.20, 1.20)),
                          ("uniform 1.37", (1.369, 1.369, 1.369)),
                          ("width only 1.20", (1.0, 1.20, 1.0)),
                          ("width only 1.37", (1.0, 1.369, 1.0)),
                          ("width only 1.60", (1.0, 1.60, 1.0)),
                          ("width only 2.00", (1.0, 2.00, 1.0))):
    apply_scale(sx, sy, sz)
    sv, p, h = share(DUVET, RECT)
    sa, _p2, _h2 = share(CLOTH, RECT)
    bb = fit.group_bbox(DUVET)
    over_x = max(0.0, (bb[3] - bb[0]) - RECT[2]) / 2.0
    drop = MTOP - bb[2]
    edge = max((fit.edge_mm(o) or 0.0) for o in DUVET)
    print(f"PROBE   {tag:16s} duvet {sv*100:5.1f}%  set {sa*100:5.1f}%  "
          f"overhang/end {over_x*1000:4.0f} mm  lowest point {drop*1000:4.0f} mm "
          f"below the mattress top  median edge {edge:.1f} mm"
          f"   {'CLEARS 80' if sv >= 0.80 else ''}")
restore()

# ---- LEVER 3: TURN THE DUVET 90 degrees about the mattress centre.
print("PROBE ---- lever 3: turn the duvet 90 degrees")
piv = mathutils.Vector((CX, CY, 0.0))
R = (mathutils.Matrix.Translation(piv)
     @ mathutils.Matrix.Rotation(1.5707963267948966, 4, 'Z')
     @ mathutils.Matrix.Translation(-piv))
for o in roots:
    o.matrix_world = R @ base[o.name].copy()
bpy.context.view_layer.update()
sv, p, h = share(DUVET, RECT)
sa, _p3, _h3 = share(CLOTH, RECT)
print(f"PROBE   turned 90     duvet {sv*100:5.1f}%  set {sa*100:5.1f}%"
      f"   {'CLEARS 80' if sv >= 0.80 else ''}")
restore()
print("PROBE done — nothing was saved.")
