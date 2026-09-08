"""WHOLE-BED CANDIDATE DUMP — every part of a candidate file, at its asserted unit
factor, with the per-part SURFACE facts the anchor rules need (in Blender; the
rules that read the dump live in wholebed_rules.py and are pure).

Run:  blender -b --factory-startup -Y --python wholebed_dump.py -- \
          <cache_dir> <out.json> slug[,slug...]

WHY IT EXISTS (p2r58, D-120): the bench's anchor was "largest plan area in the
bed band", which is the FRAME on every upholstered bed, and the bench then
projected THE FRAME through the fit scale and asked whether it was a standard
MATTRESS size. To write the mattress rule as geometry (R9b: never by name) the
builder needs each part's bbox AND whether its top is a continuous flat surface
— a bbox alone cannot tell a mattress slab from the seam-piping mesh that shares
its footprint (Obsidian's 'Base Seams' spans 2144 x 1950 mm and holds no
surface at all). This dump is the R5 playblast of the bench: no room, no render,
one import per candidate, so the rule can be iterated on the JSON rather than on
20-minute bench runs.

Per part: name, lo, hi (metres, unit factor applied), tris, and over the
central 70% of ITS OWN plan bbox, against a BVH of THAT PART ONLY:
  cover   — fraction of downward rays that hit it (a slab ~1.0; piping ~0)
  top_med — median hit z (the part's own top surface)
  relief  — p90 - p10 of hit z (a mattress is flat; a duvet has folds)
"""
import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mesh_import as MI    # noqa: E402
import wholebed_rules as R  # noqa: E402

GRID = 12


def world_bbox(ob):
    import math
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w))
        hi = Vector(map(max, hi, w))
    return tuple(lo), tuple(hi)


def part_dict(ob):
    lo, hi = world_bbox(ob)
    try:
        ob.data.calc_loop_triangles()
        tris = len(ob.data.loop_triangles)
    except Exception:
        tris = 0
    return {"name": ob.name, "lo": lo, "hi": hi, "tris": tris, "_ob": ob}


def surface_facts(p, grid=GRID):
    """cover / top_med / relief of one part against ITS OWN BVH (metres).

    Shared by the bench (wholebed_bench.py imports this) so the mattress rule
    reads the same three numbers at audition time that it was calibrated on
    here — one probe, two callers (the bedcloth_fit law)."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    ob = p["_ob"]
    bm = bmesh.new()
    m = ob.to_mesh()
    m.transform(ob.matrix_world)
    bm.from_mesh(m)
    ob.to_mesh_clear()
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    lo, hi = p["lo"], p["hi"]
    x0 = lo[0] + 0.15 * (hi[0] - lo[0]); x1 = hi[0] - 0.15 * (hi[0] - lo[0])
    y0 = lo[1] + 0.15 * (hi[1] - lo[1]); y1 = hi[1] - 0.15 * (hi[1] - lo[1])
    z_from = hi[2] + 0.5
    zs = []
    for i in range(grid):
        for j in range(grid):
            x = x0 + (i + 0.5) * (x1 - x0) / grid
            y = y0 + (j + 0.5) * (y1 - y0) / grid
            hit = tree.ray_cast(Vector((x, y, z_from)), Vector((0, 0, -1)),
                                (hi[2] - lo[2]) + 1.0)
            if hit[0] is not None:
                zs.append(hit[0].z)
    n = grid * grid
    if not zs:
        return {"cover": 0.0, "top_med": None, "relief": None}
    zs.sort()
    return {"cover": round(len(zs) / n, 3),
            "top_med": round(zs[len(zs) // 2], 4),
            "relief": round(zs[int(0.9 * (len(zs) - 1))] - zs[int(0.1 * (len(zs) - 1))], 4)}


def dump_one(slug, cache):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    row = {"slug": slug}
    d = os.path.join(cache, slug)
    models = MI.model_files(d)
    if not models:
        row["reject"] = "no importable model in cache dir"
        return row
    row["model"] = models[0]
    try:
        new = MI.import_file(os.path.join(d, models[0]))
    except Exception as e:
        row["reject"] = f"import failed: {type(e).__name__}: {e}"
        return row
    roots = [o for o in new if o.parent is None]
    bpy.context.view_layer.update()
    parts = [part_dict(o) for o in new if o.type == "MESH"]
    if not parts:
        row["reject"] = "import produced no meshes"
        return row
    f, why = R.unit_factor(parts)
    row["unit_factor"], row["unit_note"] = f, why
    if f is None:
        row["reject"] = f"scale unresolvable: {why}"
        return row
    if f != 1.0:
        for o in roots:
            o.scale = tuple(s * f for s in o.scale)
        bpy.context.view_layer.update()
        parts = [part_dict(o) for o in new if o.type == "MESH"]
    out = []
    for p in parts:
        facts = surface_facts(p)
        out.append({"name": p["name"],
                    "lo": [round(v, 4) for v in p["lo"]],
                    "hi": [round(v, 4) for v in p["hi"]],
                    "tris": p["tris"], **facts})
    row["parts"] = out
    return row


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cache, out = argv[0], argv[1]
    slugs = [s for s in argv[2].split(",") if s]
    rows = []
    for slug in slugs:
        print(f"WBDUMP {slug} ...", flush=True)
        try:
            row = dump_one(slug, cache)
        except Exception as e:
            import traceback
            row = {"slug": slug, "reject": f"CRASH {type(e).__name__}: {e}",
                   "trace": traceback.format_exc()[-2000:]}
        rows.append(row)
        print(f"WBDUMP {slug:16s} -> {row.get('reject') or str(len(row.get('parts', []))) + ' parts'}",
              flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"rows": rows}, fh, indent=1)
    print(f"WBDUMP COMPLETE {len(rows)} -> {out}", flush=True)


if __name__ == "__main__":
    main()
