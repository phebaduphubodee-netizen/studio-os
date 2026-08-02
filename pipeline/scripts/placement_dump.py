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


def dump(scene=None):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for ob in (scene or bpy.context.scene).objects:
        rec = {
            "name": ob.name,
            "type": ob.type,
            "hidden_render": bool(ob.hide_render),
            # degrees, so a human reading the JSON can see "3.7" and not "0.0645"
            "rot_deg": [round(a * 180.0 / 3.141592653589793, 4)
                        for a in ob.rotation_euler],
            "parent": ob.parent.name if ob.parent else None,
        }
        if ob.type == "MESH":
            aabb = _world_aabb(ob, dg)
            if aabb:
                rec.update(aabb)
                rec["polys"] = len(ob.evaluated_get(dg).data.polygons)
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
    meshes = sum(1 for o in objs if o["type"] == "MESH")
    print(f"placement_dump: {len(objs)} objects ({meshes} mesh) -> {argv[0]}")


if __name__ == "__main__":
    main()
