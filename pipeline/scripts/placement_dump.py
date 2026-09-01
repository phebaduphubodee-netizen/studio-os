#!/usr/bin/env python3
"""placement_dump.py — dump every object's WORLD bounds from a BUILT scene.

    blender -b <scene>.blend --python pipeline/scripts/placement_dump.py -- <out.json>

WHY THIS EXISTS. The owner, 2026-08-02: *"ผมสังเกตว่าที่ผ่านมาทั้งหมดคุณชอบวาง model
เบี้ยว ลอย ไม่ตรงแกน ไม่สมจริง"* — an observation across every project, and the
measurement agreed. What it found was not carelessness but a mechanism: positions
are stored as ABSOLUTE coordinates, so a coordinate stays legal-looking after the
thing it was resting on moves, and nothing fails. See CLAUDE.md R9.

WHY IT READS THE BUILT SCENE AND NOT THE SPEC. Three reasons this repo has already
paid for:
  * a spec-side check CANNOT see an object the spec does not know about — a
    `--factory-startup` default cube corrupted three renders and no projection
    check noticed;
  * "the file that renders is not automatically the file of record" — a spec
    carried a pre-solve camera for three rounds while every frame rendered from a
    private copy holding the solved one, and nothing failed;
  * a modifier changes what is actually THERE. Bounds are read from the EVALUATED
    depsgraph, so solidify/subsurf/array are included. Judging the cage would be
    judging a different object from the one that renders.

LAYER LAW. This file only DUMPS. Every judgement lives in `placement_check.py`,
which imports no bpy and runs under plain python — so the rules are testable
without Blender and cannot drift into the materialiser.

SAFE ON A DELIVERABLE .blend: opens, reads the evaluated depsgraph, writes one
JSON, never saves and never mutates.
"""
import json
import sys

import bpy                                              # noqa: E402
from mathutils import Vector                            # noqa: E402

MM = 1000.0                                             # scene metres -> mm


def _world_aabb(ob, dg):
    """World-space AABB of the EVALUATED object, in mm, or None if it has no
    geometry. bound_box is in LOCAL space — it must go through matrix_world, and
    an object with a rotation has a local box that does not describe what the
    camera sees."""
    ev = ob.evaluated_get(dg)

    # `bound_box` IS ONLY TRUSTWORTHY FOR A MESH. Measured on Blender 5.1.2 for a
    # bevelled CURVE built exactly as build_room builds a wardrobe hanger (three
    # POLY points spanning 400 mm, bevel_depth 1.8 mm):
    #     bound_box -> (-1.200, -1.000, 0.720) .. (1.200, 1.000, 2.915)
    #     to_mesh   -> (-0.201, -0.002, 1.719) .. (0.201,  0.002, 1.917)
    # The box is off by nearly 3 m in x and y. Feeding that to the placement rules
    # is WORSE than the MESH-only blindness it replaced: every hanger would collide
    # with everything (false INTERPENETRATION) while its huge box touched something
    # and so escaped FLOATING — a guard reporting confidently from a wrong number.
    # So a non-mesh is measured from the geometry the renderer actually makes.
    if ob.type != "MESH":
        try:
            me = ev.to_mesh()
        except Exception:                               # noqa: BLE001
            return None
        try:
            if me is None or not me.vertices:
                return None
            pts = [ev.matrix_world @ v.co for v in me.vertices]
            return {
                "min": [min(p[i] for p in pts) * MM for i in range(3)],
                "max": [max(p[i] for p in pts) * MM for i in range(3)],
            }
        finally:
            ev.to_mesh_clear()

    try:
        bb = ev.bound_box
    except Exception:                                   # noqa: BLE001
        return None
    if bb is None:
        return None
    pts = [ev.matrix_world @ Vector(c) for c in bb]
    if not pts:
        return None
    return {
        "min": [min(p[i] for p in pts) * MM for i in range(3)],
        "max": [max(p[i] for p in pts) * MM for i in range(3)],
    }


# TYPES THAT PUT REAL GEOMETRY IN THE FRAME. This used to be the single literal
# "MESH", and that word was a TYPE ALLOWLIST sitting one layer upstream of a guard
# whose own headline is that it carries no allowlist. `build_room.py` builds every
# wardrobe hanger as a CURVE with a bevel_depth -- delivered, rendered pixels --
# and a CURVE record was emitted with no `min`/`max`, so `placement_check._mesh()`
# dropped it without a word and `carry_check` never saw it either. R9b in one
# line: a rule that names the objects it applies to will always exempt the next
# one. Everything here has an evaluated bound_box; nothing needs to be a MESH.
GEOMETRY_TYPES = ("MESH", "CURVE", "SURFACE", "FONT", "META")


def _poly_count(ev):
    """Evaluated polygon count for anything in GEOMETRY_TYPES. A CURVE's `data` is
    a Curve and has no `.polygons`, so it is converted -- the same conversion the
    renderer does."""
    data = getattr(ev, "data", None)
    polys = getattr(data, "polygons", None)
    if polys is not None:
        return len(polys)
    try:
        me = ev.to_mesh()
    except Exception:                                   # noqa: BLE001
        return None
    try:
        return len(me.polygons)
    finally:
        ev.to_mesh_clear()


def dump(scene=None):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for ob in (scene or bpy.context.scene).objects:
        # ROTATION COMES FROM THE MATRIX, NOT FROM `rotation_euler`. That attribute
        # is only the live channel while `rotation_mode == 'XYZ'`, and
        # `bpy.ops.import_scene.gltf` leaves every object it imports at
        # 'QUATERNION' -- on which `rotation_euler` reads (0, 0, 0) however the
        # object is really turned. Probed on Blender 5.1.2 with a repo-built
        # control in the same scene: the control reported its 20 deg correctly
        # while an imported cube turned (20, 0, 35) reported (0, 0, 0). Every
        # acquired asset in this repo arrives that way, so R9's OFF-AXIS rung was
        # blind on exactly the population R8 tells us to prefer. `matrix_world`
        # is mode-independent and cannot be blinded again.
        rec = {
            "name": ob.name,
            "type": ob.type,
            "hidden_render": bool(ob.hide_render),
            "rotation_mode": ob.rotation_mode,
            # degrees, so a human reading the JSON can see "3.7" and not "0.0645"
            "rot_deg": [round(a * 180.0 / 3.141592653589793, 4)
                        for a in ob.matrix_world.to_euler()],
            "parent": ob.parent.name if ob.parent else None,
        }
        if ob.type in GEOMETRY_TYPES:
            aabb = _world_aabb(ob, dg)
            if aabb:
                rec.update(aabb)
                rec["polys"] = _poly_count(ob.evaluated_get(dg))
        out.append(rec)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        raise SystemExit("placement_dump: need an output .json path")
    objs = dump()
    with open(argv[0], "w", encoding="utf-8") as f:
        json.dump({"blend": bpy.data.filepath, "unit": "mm", "objects": objs},
                  f, indent=1, ensure_ascii=False)
    geo = sum(1 for o in objs if o["type"] in GEOMETRY_TYPES)
    bounded = sum(1 for o in objs if "min" in o)
    # THE DENOMINATOR PRINTS. Without it, a guard that silently dropped every
    # unbounded record read exactly like a guard that found nothing wrong.
    print(f"placement_dump: {len(objs)} objects ({geo} with geometry, "
          f"{bounded} bounded) -> {argv[0]}")
    if bounded < geo:
        print(f"  {geo - bounded} geometry object(s) produced no bounds — they "
              f"are invisible to every downstream rung; that is a finding, not a "
              f"formatting detail")


if __name__ == "__main__":
    main()
