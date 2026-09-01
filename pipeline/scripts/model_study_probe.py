#!/usr/bin/env python3
"""model_study_probe.py — dump HOW a professionally-built asset is constructed,
from its native .blend, into one JSON per asset.

    # in-Blender half (one process per file, layer law):
    blender -b --factory-startup -Y <asset>.blend --python model_study_probe.py -- <out.json>
    # pure batch half (spawns the above over the whole cache, resumable):
    python pipeline/scripts/model_study_probe.py batch [--cache assets/shared/blenderkit] [--limit N]

WHY THIS EXISTS — owner idea 2026-09-01: "การจะทำให้การซื้อ subscription ได้ประโยชน์
สูงสุดเดือนนี้ คือคุณต้องไปทำการศึกษา model ใน blenderkit เพื่อที่หลังจาก sub หมดคุณจะ
ปั้นเองได้ และเข้าใจการออกแบบมากขึ้น". D-119 answers whether bought assets make the
FRAME better; nothing in that plan reads what is INSIDE the files. The month clock
says day 10 of 30 — after it, full-plan .blends stop being fetchable, but the 71
already on the shelf stay readable forever. What expires is the ACCESS, not the
LESSON, and the lesson is the part the harness audit (2026-08-31) says we lack:
two build rounds hit the R1 stop-loss with massing <2% off and still read
NO-DIFFERENT-PRODUCT — the bottleneck is the modelling VOCABULARY (what a cage
looks like, where folds come from, what a node tree does that a tint cannot), not
the model's eye. This probe harvests that vocabulary as data.

WHAT IT DUMPS (read-only; never saves, never mutates, mirrors scene_dump's law):
  * per OBJECT: type, dims, parent, poly/tri/quad/ngon counts, surface area,
    vertex density, UV layers, shape keys, vertex groups, smooth-shading share,
    the full modifier stack with the settings that carry the idiom
    (SUBSURF levels, BEVEL width/segments, SOLIDIFY thickness, ARRAY count,
    DISPLACE strength, geometry-nodes group name), curve bevel/taper, instancing.
  * per MATERIAL: node-type histogram, every image with its size/colorspace and
    the Principled input it feeds (traced through the link graph), procedural
    node chains, displacement wiring, mapping scale (texture density),
    principled scalar values actually set.
  * per IMAGE: name, size, packed or not.

WHY THESE FIELDS: they answer the four questions our hand-built rounds could not —
(1) is detail GEOMETRY or MAPS (subsurf+displace vs normal-map on a low cage)?
(2) are folds SIMULATED (dense tri soup, no modifiers), SCULPTED (dense quads,
multires/shape keys) or MODELLED (sparse quad cage + subsurf)? (3) what does a
fabric node tree contain that our _woven preset does not? (4) how dense is dense —
verts per m^2, a number to build to instead of a taste word.

LAYER LAW: the bpy half runs only under Blender; the batch half imports no bpy
and spawns one process per file with --factory-startup -Y (third-party files,
autorun OFF — same spawn contract as blenderkit.export_glb). A file that fails
to probe is a RESULT recorded in the batch log, never a crash of the batch.

Output: <cache>/_study/<asset_dir>.probe.json (the cache is gitignored; the
distilled study notes in knowledge/_inbox/model-study/ are what gets committed).
"""
import json
import math
import os
import sys

try:
    import bpy  # only under Blender
except ImportError:
    bpy = None


# ---------------------------------------------------------------- bpy half
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
REPO_QA = os.path.join(REPO, "qa")

MOD_PARAMS = {
    "SUBSURF": ("levels", "render_levels", "subdivision_type"),
    "MULTIRES": ("levels", "render_levels", "total_levels"),
    "BEVEL": ("width", "segments", "limit_method"),
    "SOLIDIFY": ("thickness", "offset"),
    "ARRAY": ("count",),
    "MIRROR": ("use_axis",),
    "DISPLACE": ("strength", "mid_level"),
    "SHRINKWRAP": ("wrap_method",),
    "CURVE": ("deform_axis",),
    "SIMPLE_DEFORM": ("deform_method", "angle"),
    "CLOTH": (),
    "COLLISION": (),
    "NODES": (),
}


def _mod_row(m):
    row = {"type": m.type, "name": m.name}
    for p in MOD_PARAMS.get(m.type, ()):
        try:
            v = getattr(m, p)
            row[p] = list(v) if hasattr(v, "__len__") and not isinstance(v, str) else (
                round(v, 5) if isinstance(v, float) else v)
        except Exception:
            pass
    if m.type == "NODES":
        try:
            row["node_group"] = m.node_group.name if m.node_group else None
            row["nodes"] = len(m.node_group.nodes) if m.node_group else 0
        except Exception:
            pass
    if m.type == "DISPLACE":
        try:
            row["texture"] = m.texture.type if m.texture else None
        except Exception:
            pass
    return row


def _mesh_row(ob):
    import numpy as np
    me = ob.data
    n_poly = len(me.polygons)
    row = {"verts": len(me.vertices), "polys": n_poly}
    if n_poly:
        lt = np.empty(n_poly, dtype=np.int32)
        me.polygons.foreach_get("loop_total", lt)
        row["tris"] = int((lt == 3).sum())
        row["quads"] = int((lt == 4).sum())
        row["ngons"] = int((lt > 4).sum())
        # AREA IS MEASURED IN WORLD SPACE, ON A TRANSFORMED COPY — never by
        # scaling the local area with an averaged scale factor. The first
        # version did the latter (mean of the three scale pair-products) and
        # it is wrong whenever the scale is non-uniform: on a box scaled
        # (1,1,2) the factor reads 1.667 while the top and bottom faces really
        # scale by 1.0, so a flat object's area is over-stated by up to 1.67x
        # and every verts_per_m2 derived from it is under-stated by the same
        # factor. `verts_per_m2` is the number the study notes tell the builder
        # to build TO, so an approximation there is a wrong target, not a
        # rounding detail. The copy is removed before returning; the .blend is
        # never saved (same read-only law as scene_dump).
        tmp = me.copy()
        try:
            tmp.transform(ob.matrix_world)
            ar = np.empty(len(tmp.polygons), dtype=np.float64)
            tmp.polygons.foreach_get("area", ar)
            row["area_m2"] = round(float(ar.sum()), 6)
        finally:
            bpy.data.meshes.remove(tmp)
        sm = np.empty(n_poly, dtype=bool)
        me.polygons.foreach_get("use_smooth", sm)
        row["smooth_share"] = round(float(sm.mean()), 3)
        if row["area_m2"] > 1e-9:
            row["verts_per_m2"] = round(row["verts"] / row["area_m2"], 1)
    row["uv_layers"] = len(me.uv_layers)
    row["vertex_groups"] = len(ob.vertex_groups)
    sk = me.shape_keys
    row["shape_keys"] = [k.name for k in sk.key_blocks] if sk else []
    row["mesh_users"] = me.users  # >1 = instanced data
    return row


def _principled_report(mat):
    """Trace what feeds each Principled input: a value, an image, or a chain."""
    out = {}
    nt = mat.node_tree
    principled = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]
    if not principled:
        return out

    def _src(sock, depth=0):
        if not sock.links or depth > 6:
            return None
        n = sock.links[0].from_node
        if n.type == "TEX_IMAGE":
            return "IMG:" + (n.image.name if n.image else "?")
        if n.type in ("TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MUSGRAVE",
                      "TEX_MAGIC", "TEX_CHECKER", "TEX_BRICK", "TEX_GRADIENT"):
            return "PROC:" + n.type[4:]
        if n.type == "NORMAL_MAP":
            inner = _src(n.inputs.get("Color"), depth + 1)
            return "NORMALMAP<" + str(inner) + ">"
        if n.type == "BUMP":
            inner = _src(n.inputs.get("Height"), depth + 1)
            return "BUMP<" + str(inner) + ">"
        for inp in n.inputs:
            got = _src(inp, depth + 1)
            if got:
                return n.type + "<" + got + ">"
        return n.type
    p = principled[0]
    for key in ("Base Color", "Roughness", "Metallic", "Normal", "Sheen Weight",
                "Sheen", "Transmission Weight", "Transmission", "Coat Weight",
                "Clearcoat", "Alpha", "Subsurface Weight", "Emission Strength"):
        sock = p.inputs.get(key)
        if sock is None:
            continue
        src = _src(sock)
        if src:
            out[key] = src
        else:
            try:
                v = sock.default_value
                v = [round(x, 4) for x in v] if hasattr(v, "__len__") else round(v, 4)
                out[key] = v
            except Exception:
                pass
    return out


def _material_row(mat):
    import collections
    row = {"name": mat.name, "users": mat.users, "use_nodes": mat.use_nodes}
    if not mat.use_nodes:
        return row
    nt = mat.node_tree
    hist = collections.Counter(n.type for n in nt.nodes)
    row["node_hist"] = dict(hist)
    row["principled"] = _principled_report(mat)
    # displacement wiring on the output node
    for n in nt.nodes:
        if n.type == "OUTPUT_MATERIAL" and n.inputs.get("Displacement") and \
                n.inputs["Displacement"].links:
            up = n.inputs["Displacement"].links[0].from_node
            row["displacement"] = up.type
            if up.type == "DISPLACEMENT":
                try:
                    row["displacement_scale"] = round(
                        up.inputs["Scale"].default_value, 5)
                except Exception:
                    pass
    # mapping scale = texture density decision
    for n in nt.nodes:
        if n.type == "MAPPING":
            try:
                row["mapping_scale"] = [round(v, 4) for v in
                                        n.inputs["Scale"].default_value]
            except Exception:
                pass
            break
    return row


def dump(out_path):
    doc = {"blend": bpy.data.filepath, "objects": [], "materials": [], "images": []}
    for ob in bpy.data.objects:
        loc = ob.matrix_world.translation
        rot = ob.matrix_world.to_euler()
        row = {
            "name": ob.name, "type": ob.type,
            "parent": ob.parent.name if ob.parent else None,
            "dims_mm": [round(d * 1000, 1) for d in ob.dimensions],
            "loc_mm": [round(v * 1000, 1) for v in loc],
            "rot_deg": [round(math.degrees(a), 2) for a in rot],
            # scale is dumped because without it a reader cannot tell whether a
            # dimension or an area came from geometry or from a transform — and
            # a non-uniform scale is exactly what breaks a naive area estimate
            "scale": [round(v, 5) for v in ob.matrix_world.to_scale()],
            "hide_render": ob.hide_render,
            "materials": [s.material.name for s in ob.material_slots if s.material],
            "modifiers": [_mod_row(m) for m in ob.modifiers],
        }
        if ob.type == "MESH":
            try:
                row["mesh"] = _mesh_row(ob)
            except Exception as e:  # a mesh that will not read is a finding
                row["mesh_error"] = str(e)[:120]
        elif ob.type == "CURVE":
            cu = ob.data
            row["curve"] = {
                "bevel_depth": round(cu.bevel_depth, 5),
                "bevel_object": cu.bevel_object.name if cu.bevel_object else None,
                "extrude": round(cu.extrude, 5),
                "resolution_u": cu.resolution_u,
                "splines": len(cu.splines),
                "points": sum(len(s.points) or len(s.bezier_points)
                              for s in cu.splines),
                "fill_mode": cu.fill_mode,
            }
        elif ob.type == "EMPTY" and ob.instance_type != "NONE":
            row["instance"] = {
                "type": ob.instance_type,
                "collection": ob.instance_collection.name
                if ob.instance_collection else None,
            }
        doc["objects"].append(row)
    for mat in bpy.data.materials:
        if mat.users:
            try:
                doc["materials"].append(_material_row(mat))
            except Exception as e:
                doc["materials"].append({"name": mat.name,
                                         "material_error": str(e)[:120]})
    for img in bpy.data.images:
        if img.users and img.name not in ("Render Result", "Viewer Node"):
            doc["images"].append({
                "name": img.name, "size": list(img.size),
                "packed": img.packed_file is not None,
                "colorspace": getattr(img.colorspace_settings, "name", "?"),
            })
    doc["totals"] = {
        "objects": len(doc["objects"]),
        "meshes": sum(1 for o in doc["objects"] if o["type"] == "MESH"),
        "curves": sum(1 for o in doc["objects"] if o["type"] == "CURVE"),
        "verts": sum(o.get("mesh", {}).get("verts", 0) for o in doc["objects"]),
        "materials": len(doc["materials"]),
        "images": len(doc["images"]),
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # newline="\n" on every writer: a text-mode write on Windows turns the
    # whole file CRLF, which made a one-row append to qa/open-decisions.json
    # read as a 3,700-line rewrite in the diff (caught by scrutinize before
    # that commit landed; same class as the sed -i that flipped a file)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
    print("PROBE WROTE " + out_path)


# ---------------------------------------------------------------- pure half
def batch(cache, limit=None, blender=None, out_dir=None):
    """Spawn one Blender per .blend in the cache; resumable; failures logged."""
    import glob as _glob
    import subprocess
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import glance
    exe = blender or glance.find_blender()
    if not exe:
        print("REFUSED: no Blender found (INTERIOR_BLENDER / PATH)")
        return 2
    out_dir = out_dir or os.path.join(cache, "_study")
    os.makedirs(out_dir, exist_ok=True)
    me = os.path.abspath(__file__)
    blends = []
    for d in sorted(_glob.glob(os.path.join(cache, "*", ""))):
        base = os.path.basename(os.path.normpath(d))
        if base.startswith("_"):
            continue
        cand = sorted(_glob.glob(os.path.join(d, "*.blend")))
        cand = [c for c in cand if not c.endswith(".blend1")]
        if cand:
            blends.append((base, cand[0]))
    if limit:
        blends = blends[:int(limit)]
    done = skipped = failed = 0
    failures = []
    for base, blend in blends:
        out = os.path.join(out_dir, base + ".probe.json")
        if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(blend):
            skipped += 1
            continue
        cmd = [exe, "-b", "--factory-startup", "-Y", blend, "--python", me,
               "--", out]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
            ok = p.returncode == 0 and os.path.exists(out)
        except subprocess.TimeoutExpired:
            ok = False
            p = None
        if ok:
            done += 1
            print(f"OK   {base}")
        else:
            failed += 1
            tail = (p.stdout or "")[-300:] if p else "TIMEOUT 420s"
            failures.append({"asset": base, "blend": blend, "tail": tail})
            print(f"FAIL {base}")
    summary = {"probed": done, "skipped_fresh": skipped, "failed": failed,
               "total_blends": len(blends), "failures": failures}
    with open(os.path.join(out_dir, "_batch_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({k: summary[k] for k in
                      ("probed", "skipped_fresh", "failed", "total_blends")}))
    return 0 if failed == 0 else 1


def stats(cache, out=None):
    """The per-class aggregate table every study note cites, REGENERATED FROM
    THE DUMPS by a script that lives in the repo.

    It exists as a subcommand and not as a scratchpad one-liner for one reason:
    the first version of this table WAS a scratchpad script, and eight notes
    then quoted its numbers as law. A figure whose generator is not in the repo
    cannot be re-derived, re-checked, or refuted after the fact — the same
    defect class as a metric quoted in prose with no reader (R11) and as the
    plan brief that re-printed a 15-round-stale correlation.

    It writes into `qa/` and NOT into the cache, because the cache is
    gitignored (.gitignore:68 — the shelf holds royalty-free meshes that may
    not be redistributed). The MEASUREMENTS are not the meshes: they carry no
    geometry, only counts and ratios, so they can and must live in git, or the
    evidence behind every rule disappears on the next clone.
    """
    import collections
    import glob as _glob
    import statistics

    study = os.path.join(cache, "_study")
    cls_of = {}
    for d in _glob.glob(os.path.join(cache, "*", "")):
        aid = os.path.basename(os.path.normpath(d))
        for sc in _glob.glob(os.path.join(d, "*.scale.json")):
            with open(sc, encoding="utf-8") as f:
                cls_of[aid] = json.load(f).get("class", "?")
            break

    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in sorted(_glob.glob(os.path.join(study, "*.probe.json"))):
        aid = os.path.basename(p)[: -len(".probe.json")]
        if aid.startswith("_"):
            continue
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        agg = per[cls_of.get(aid, "?")]
        agg["assets"].append(aid[:8])
        meshes = [o for o in doc["objects"] if o["type"] == "MESH" and "mesh" in o]
        agg["objects_per_asset"].append(doc["totals"]["objects"])
        agg["verts_per_asset"].append(doc["totals"]["verts"])
        agg["curves"].append(doc["totals"]["curves"])
        agg["images_per_asset"].append(len(doc["images"]))
        if meshes:
            subs = sum(1 for o in meshes
                       if any(m["type"] in ("SUBSURF", "MULTIRES")
                              for m in o["modifiers"]))
            agg["subsurf_share"].append(subs / len(meshes))
            q = sum(o["mesh"].get("quads", 0) for o in meshes)
            t = sum(o["mesh"].get("tris", 0) for o in meshes)
            n = sum(o["mesh"].get("ngons", 0) for o in meshes)
            if q + t + n:
                agg["quad_share"].append(q / (q + t + n))
                agg["ngon_share"].append(n / (q + t + n))
            dens = [o["mesh"]["verts_per_m2"] for o in meshes
                    if "verts_per_m2" in o["mesh"] and o["mesh"]["polys"] > 50]
            if dens:
                agg["median_verts_per_m2_significant_meshes"].append(
                    statistics.median(dens))
            agg["shapekey_meshes"].append(
                sum(1 for o in meshes if o["mesh"].get("shape_keys")))
        for mat in doc["materials"]:
            hist = mat.get("node_hist", {})
            if not hist:
                continue
            agg["_mat_n"].append(1)
            if hist.get("TEX_IMAGE", 0) == 0:
                agg["_mat_procedural_only"].append(1)
            pr = mat.get("principled", {})
            sheen = pr.get("Sheen Weight", pr.get("Sheen", 0))
            if isinstance(sheen, (int, float)) and sheen > 0:
                agg["_mat_sheen_set"].append(1)
            if "displacement" in mat:
                agg["_mat_displacement"].append(1)

    table = {}
    for cls, agg in sorted(per.items()):
        row = {"n_assets": len(agg["assets"]), "assets": agg["assets"]}
        for k, v in agg.items():
            if k == "assets" or k.startswith("_") or not v:
                continue
            row[k] = {"median": round(statistics.median(v), 3),
                      "min": round(min(v), 3), "max": round(max(v), 3)}
        nmat = len(agg["_mat_n"]) or 1
        row["materials_seen"] = len(agg["_mat_n"])
        row["mat_procedural_only_share"] = round(
            len(agg["_mat_procedural_only"]) / nmat, 3)
        row["mat_sheen_set_share"] = round(len(agg["_mat_sheen_set"]) / nmat, 3)
        row["mat_displacement_share"] = round(
            len(agg["_mat_displacement"]) / nmat, 3)
        table[cls] = row

    doc = {
        "_what": "Per-class construction statistics over the BlenderKit study "
                 "dumps. Regenerate with: python pipeline/scripts/"
                 "model_study_probe.py stats",
        "_source": "assets/shared/blenderkit/_study/*.probe.json (gitignored "
                   "cache; regenerate with `model_study_probe.py batch`)",
        "_order": "ORD-2026-09-01-study-blenderkit-models",
        "_caveat": "area_m2 (and every verts_per_m2 derived from it) is "
                   "world-space from 2026-09-01 onward; the first dumps used an "
                   "averaged-scale approximation (see _mesh_row's comment). "
                   "MEASURED before the numbers were kept: three of the most "
                   "heavily cited assets (03ede500, 0b960a0d, 17aff0ff) were "
                   "re-probed with the fix and all 19 meshes read a uniform "
                   "scale, so every density was bit-identical and 0 moved. That "
                   "is a SAMPLE, not the corpus — the full re-probe belongs to "
                   "STUDY-D11b, and any class whose numbers change there wins "
                   "over what this file says today.",
        "assets_probed": sum(r["n_assets"] for r in table.values()),
        "classes": table,
    }
    out = out or os.path.join(REPO_QA, "blenderkit-study-stats.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"STATS WROTE {out} — {doc['assets_probed']} assets, "
          f"{len(table)} classes")
    return 0


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    if bpy is not None:
        args = argv[argv.index("--") + 1:] if "--" in argv else []
        if not args:
            print("REFUSED: no out.json after --")
            sys.exit(2)
        dump(args[0])
        return
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--cache", default=os.path.join("assets", "shared", "blenderkit"))
    b.add_argument("--limit", type=int, default=None)
    b.add_argument("--blender", default=None)
    s = sub.add_parser("stats")
    s.add_argument("--cache", default=os.path.join("assets", "shared", "blenderkit"))
    s.add_argument("--out", default=None)
    a = ap.parse_args(argv[1:])
    if a.cmd == "stats":
        sys.exit(stats(a.cache, out=a.out))
    sys.exit(batch(a.cache, limit=a.limit, blender=a.blender))


if __name__ == "__main__":
    main()
