#!/usr/bin/env python3
"""model_study_probe.py — dump HOW a professionally-built asset is constructed,
from its native .blend, into one JSON per asset.

    # in-Blender half (one process per file, layer law):
    blender -b --factory-startup -Y <asset>.blend --python model_study_probe.py -- <out.json>
    # the same, for a GLB-only shelf entry (factory scene + import_scene.gltf):
    blender -b --factory-startup -Y --python model_study_probe.py -- <out.json> --glb <asset>.glb
    # the same, appending every object of a .blend into a factory scene (D11b-ข path):
    blender -b --factory-startup -Y --python model_study_probe.py -- <out.json> --append <asset>.blend
    # pure batch half (spawns the above over the whole cache, resumable):
    python pipeline/scripts/model_study_probe.py batch [--cache assets/shared/blenderkit] [--limit N]
        [--force] [--only ID,ID] [--no-wait]

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

THREE SOURCES, NAMED IN EVERY DUMP (`source` field, STUDY-D11b 2026-09-02):
  * `blend`      — the vendor's native file. The only source whose modifier
                   stack, node trees and subsurf levels are the vendor's own.
  * `glb-import` — a factory scene + import_scene.gltf on the shelf's GLB. This
                   is what 13 shelf entries have and what the frame actually
                   consumes, so it is a legitimate subject — but its numbers
                   are post-bake: modifiers are gone (baked at whatever level
                   the export used), node trees are the importer's rebuild of
                   the glTF PBR set (procedural chains, ColorRamps and Bump
                   nodes cannot survive), images are the packed textures. A
                   reader who quotes a glb-import density as "how the vendor
                   built it" is quoting the exporter, and the `source` field is
                   there so that mistake has to be made on purpose.
  * `append`     — a factory scene + bpy.data.libraries.load(link=False) of
                   every object in the .blend (blend_append.py, the D11b-ข path
                   a hero asset takes into a build). Same data as `blend`, in
                   a scene we own; probing it proves the append path keeps
                   what the GLB path loses, with numbers.

A shelf entry with NEITHER a .blend NOR a .glb is REFUSED by the batch (listed
in `_batch_summary.json["refused"]`, no dump written) — an empty dump would
print in `stats` as an asset with 0 objects, i.e. a measurement of nothing.

WAITS FOR AN IDLE BLENDER: the study program's pacing law is one Blender
process at a time on this machine (render lanes own it first). Every spawn
polls the process table and waits while another blender.exe is running; the
wait is printed, never silent, and --no-wait exists for a machine that is ours.

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
            # PER MATERIAL SLOT — faces and world area. Added 2026-09-02 (STUDY-D17)
            # because the dump recorded which materials an object DECLARES and never
            # which faces actually WEAR them, and those are different claims: an
            # object with two fabric slots may be two-tone, or may have one slot
            # nobody painted. The note that needed it could only say "2 slots" and
            # had to leave "did we discard a second fabric" unanswered. The polygon
            # order of the copy matches the original, so material_index is read off
            # `me` and paired with the world areas from `tmp`.
            mi = np.empty(n_poly, dtype=np.int32)
            me.polygons.foreach_get("material_index", mi)
            slots = [s.material.name if s.material else None
                     for s in ob.material_slots]
            per = []
            for i in range(max(len(slots), int(mi.max()) + 1 if n_poly else 0)):
                sel = mi == i
                per.append({"slot": i,
                            "material": slots[i] if i < len(slots) else None,
                            "faces": int(sel.sum()),
                            "area_m2": round(float(ar[sel].sum()), 6)})
            row["per_slot"] = per
            row["slots_with_no_face"] = [q["material"] for q in per if not q["faces"]]
            # FACE-AREA DISPERSION. Added 2026-09-02 (STUDY-D17 round 2) because a study
            # note concluded "we spread polygons evenly across the whole cloth while the
            # pros concentrate theirs" from a single MEAN face size — and a mean carries
            # no information about how faces are distributed inside one mesh. A mesh that
            # is dense at a seam and coarse elsewhere has the same mean as a uniform one.
            # p90/p10 is the spread a mean hides; cv is its scale-free form.
            pos = ar[ar > 0]
            if pos.size:
                q10, q50, q90 = (float(v) for v in np.percentile(pos, [10, 50, 90]))
                row["face_area_mm2"] = {
                    "p10": round(q10 * 1e6, 4), "p50": round(q50 * 1e6, 4),
                    "p90": round(q90 * 1e6, 4),
                    "p90_over_p10": (round(q90 / q10, 2) if q10 > 0 else None),
                    "cv": round(float(pos.std() / pos.mean()), 3) if pos.mean() else None,
                }
        finally:
            bpy.data.meshes.remove(tmp)
        sm = np.empty(n_poly, dtype=bool)
        me.polygons.foreach_get("use_smooth", sm)
        row["smooth_share"] = round(float(sm.mean()), 3)
        if row["area_m2"] > 1e-9:
            row["verts_per_m2"] = round(row["verts"] / row["area_m2"], 1)
    row["uv_layers"] = len(me.uv_layers)
    # names, not only a count: a second layer called "Lightmap"/"Bake" is a
    # different construction decision from a second layer called "seams"
    row["uv_layer_names"] = [u.name for u in me.uv_layers]
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
    # "Emission Color" joins the list 2026-09-02 (STUDY-D18). Emission Strength alone
    # cannot answer "does this surface glow": 1.0 is Blender's DEFAULT, so a lamp whose
    # bulb material reads Strength 1.0 with a BLACK emission colour emits nothing, and a
    # study that reads only the strength would report every Principled material in the
    # file as an emitter. Two lamps in this unit sit exactly there.
    for key in ("Base Color", "Emission Color", "Roughness", "Metallic", "Normal",
                "Sheen Weight",
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
    # BUMP_ONLY / DISPLACEMENT / BOTH — the setting that decides whether a
    # Displacement node moves vertices or only shades; a socket wired to a
    # material left on BUMP_ONLY is a texture-space bump wearing a
    # displacement's name. Blender ≥4.1: on the material; older: on cycles.
    dm = getattr(mat, "displacement_method", None)
    if dm is None:
        dm = getattr(getattr(mat, "cycles", None), "displacement_method", None)
    row["displacement_method"] = dm
    # ColorRamp stops: a two-stop ramp is a threshold, a five-stop ramp is a
    # hand-painted tone curve — the vocabulary the fabric trees carry
    ramps = []
    for n in nt.nodes:
        if n.type == "VALTORGB":
            try:
                el = n.color_ramp.elements
                ramps.append({
                    "name": n.name,
                    "interp": n.color_ramp.interpolation,
                    "stops": [[round(e.position, 4)] +
                              [round(c, 4) for c in e.color] for e in el],
                })
            except Exception:
                pass
    if ramps:
        row["valtorgb"] = ramps
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


def _world_bbox_mm(ob):
    """min/max of the object's bound_box corners in world space, mm. Unlike
    `dimensions` this survives a rotated or parented object, and unlike loc it
    says where the mass IS rather than where its origin was left."""
    mw = ob.matrix_world
    pts = [mw @ __import__("mathutils").Vector(c) for c in ob.bound_box]
    lo = [round(min(p[i] for p in pts) * 1000, 1) for i in range(3)]
    hi = [round(max(p[i] for p in pts) * 1000, 1) for i in range(3)]
    return {"min": lo, "max": hi}


def _clear_factory_scene():
    """DATA-API removal of the factory Cube/Light/Camera so an imported or
    appended asset is the only thing a dump can see. Never `bpy.ops`."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras):
        for datum in list(coll):
            if datum.users == 0:
                coll.remove(datum)


def _load_glb(glb_path):
    """Factory scene + import_scene.gltf — the one headless-safe op the asset
    path already relies on (build_room.py's glTF import, pipeline/CLAUDE.md)."""
    _clear_factory_scene()
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    except Exception:
        pass
    res = bpy.ops.import_scene.gltf(filepath=glb_path)
    if "FINISHED" not in res:
        raise RuntimeError(f"import_scene.gltf returned {res}")


def _load_append(blend_path):
    """Factory scene + blend_append.append_objects (bpy.data.libraries.load)."""
    _clear_factory_scene()
    sys.path.insert(0, HERE)
    import blend_append
    return blend_append.append_objects(blend_path)


def dump(out_path, glb=None, append=None):
    src = "glb-import" if glb else ("append" if append else "blend")
    doc = {"source": src, "blend": bpy.data.filepath, "objects": [],
           "materials": [], "images": [],
           "blender": ".".join(str(v) for v in bpy.app.version)}
    if glb:
        _load_glb(glb)
        doc["glb"] = glb
    elif append:
        rep = _load_append(append)
        doc["blend"] = append
        doc["append"] = rep
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
            "world_bbox_mm": _world_bbox_mm(ob),
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
    # SERIALISE FIRST, WRITE SECOND, RENAME LAST: json.dump streams, so an
    # unserialisable value half-way through leaves a truncated file at the
    # out path that a caller checking os.path.exists() reads as a dump. The
    # first append-route run did exactly that (an Object in the report) and
    # Blender still exited 0 — a truncated dump must never exist at `out`.
    text = json.dumps(doc, indent=1)
    tmp = out_path + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, out_path)
    print("PROBE WROTE " + out_path)


# ---------------------------------------------------------------- pure half
def plan(cache, only=None):
    """PURE. What the batch would probe: [(asset_dir, kind, path)] with kind in
    {'blend', 'glb'} (a .blend wins over a GLB — it is the vendor's file), plus
    the REFUSED list: shelf dirs with neither. `only` = iterable of dir-name
    prefixes to restrict to. Dirs starting with '_' are the cache's own."""
    import glob as _glob
    only = [o.strip() for o in only] if only else None
    items, refused = [], []
    for d in sorted(_glob.glob(os.path.join(cache, "*", ""))):
        base = os.path.basename(os.path.normpath(d))
        if base.startswith("_"):
            continue
        if only and not any(base.startswith(o) for o in only):
            continue
        blends = [c for c in sorted(_glob.glob(os.path.join(d, "*.blend")))
                  if not c.endswith(".blend1")]
        glbs = sorted(_glob.glob(os.path.join(d, "*.glb")))
        if blends:
            items.append((base, "blend", blends[0]))
        elif glbs:
            items.append((base, "glb", glbs[0]))
        else:
            refused.append({"asset": base, "reason": "no .blend and no .glb"})
    return items, refused


def needs_probe(out, src, force=False):
    """PURE. Re-probe when forced, when no dump exists, or when the source is
    newer than the dump. A dump that predates a field added to the dumper is
    what --force is for; mtime cannot see that."""
    if force or not os.path.exists(out):
        return True
    return os.path.getmtime(out) <= os.path.getmtime(src)


def blender_pids(tasklist_text):
    """PURE. PIDs of blender.exe rows in `tasklist /FI "IMAGENAME eq
    blender.exe" /FO CSV /NH` output; [] on the 'No tasks' line."""
    pids = []
    for line in tasklist_text.splitlines():
        cells = [c.strip().strip('"') for c in line.split('","')]
        if len(cells) >= 2 and cells[0].lower() == "blender.exe":
            try:
                pids.append(int(cells[1]))
            except ValueError:
                pass
    return pids


def other_blender_pids():
    """Which blender.exe processes are running now (Windows: tasklist; else
    pgrep). Failure to ask reads as 'none' — a wait can only be as good as its
    process table, and a machine with no tasklist has no render lane to wait on."""
    import subprocess
    try:
        if os.name == "nt":
            p = subprocess.run(["tasklist", "/FI", "IMAGENAME eq blender.exe",
                                "/FO", "CSV", "/NH"], capture_output=True,
                               text=True, timeout=20)
            return blender_pids(p.stdout or "")
        p = subprocess.run(["pgrep", "-x", "blender"], capture_output=True,
                           text=True, timeout=20)
        return [int(x) for x in (p.stdout or "").split() if x.isdigit()]
    except Exception:
        return []


def wait_for_idle_blender(max_wait_s=7200, poll_s=15, pids_fn=other_blender_pids,
                          sleep_fn=None, log=print):
    """Block while another blender.exe runs (pacing law: one Blender at a
    time; the render lanes own it first). Returns seconds waited. Refuses with
    RuntimeError past max_wait_s so a stuck render never silently eats a
    study day — the wait is printed every poll, never silent."""
    import time
    sleep_fn = sleep_fn or time.sleep
    waited = 0
    while True:
        pids = pids_fn()
        if not pids:
            return waited
        if waited >= max_wait_s:
            raise RuntimeError(f"blender busy for {waited}s (pids {pids}); "
                               f"refusing to start a second Blender")
        if waited == 0 or waited % (poll_s * 8) == 0:
            log(f"WAIT blender busy (pids {pids}) — {waited}s so far")
        sleep_fn(poll_s)
        waited += poll_s


def probe_cmd(exe, me, kind, path, out):
    """PURE. The spawn line per source kind. `--python-exit-code 1` because
    Blender's default is to print a script's traceback and EXIT 0 — the
    first append-route run raised inside json.dump and the caller's
    returncode check read it as success."""
    head = [exe, "-b", "--factory-startup", "-Y", "--python-exit-code", "1"]
    if kind == "blend":
        return head + [path, "--python", me, "--", out]
    if kind == "glb":
        return head + ["--python", me, "--", out, "--glb", path]
    if kind == "append":
        return head + ["--python", me, "--", out, "--append", path]
    raise ValueError(kind)


def dump_ok(out):
    """PURE. A dump counts only if it exists AND parses AND carries the
    totals block — existence alone let a truncated file through."""
    try:
        with open(out, encoding="utf-8") as f:
            d = json.load(f)
        return isinstance(d, dict) and "totals" in d and "objects" in d
    except (OSError, ValueError):
        return False


def batch(cache, limit=None, blender=None, out_dir=None, force=False, only=None,
          wait=True):
    """Spawn one Blender per shelf entry (.blend, else GLB); resumable;
    failures logged; entries with neither are REFUSED, not dumped empty."""
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
    items, refused = plan(cache, only=only)
    for r in refused:
        print(f"REFUSED {r['asset']}: {r['reason']}")
    if limit:
        items = items[:int(limit)]
    done = skipped = failed = 0
    failures, waited_total = [], 0
    by_kind = {"blend": 0, "glb": 0}
    for base, kind, src in items:
        out = os.path.join(out_dir, base + ".probe.json")
        if not needs_probe(out, src, force):
            skipped += 1
            continue
        if wait:
            waited_total += wait_for_idle_blender()
        cmd = probe_cmd(exe, me, kind, src, out)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=420)
            ok = p.returncode == 0 and dump_ok(out)
        except subprocess.TimeoutExpired:
            ok = False
            p = None
        if ok:
            done += 1
            by_kind[kind] += 1
            print(f"OK   {base} ({kind})")
        else:
            failed += 1
            tail = (p.stdout or "")[-300:] if p else "TIMEOUT 420s"
            failures.append({"asset": base, "kind": kind, "path": src,
                             "tail": tail})
            print(f"FAIL {base} ({kind})")
    summary = {"probed": done, "probed_by_kind": by_kind,
               "skipped_fresh": skipped, "failed": failed,
               "total_entries": len(items), "refused": refused,
               "forced": bool(force), "waited_for_blender_s": waited_total,
               "failures": failures}
    with open(os.path.join(out_dir, "_batch_summary.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({k: summary[k] for k in
                      ("probed", "probed_by_kind", "skipped_fresh", "failed",
                       "total_entries", "waited_for_blender_s")}
                     | {"refused": len(refused)}))
    return 0 if failed == 0 else 1


def probe_one(path, out, kind=None, blender=None, wait=True, _run=None):
    """Probe ONE file (a .blend natively, a .glb by import, or a .blend by
    append with kind='append') into `out`. Refuses (2) when the path is not a
    probe-able file — no dump is written for nothing. Returns 1 when Blender
    failed OR the dump does not parse (`_run` is the spawn, injectable so the
    truncated-dump reading is testable without Blender)."""
    import subprocess
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import glance
    run = _run or subprocess.run
    exe = blender or glance.find_blender()
    if not exe:
        print("REFUSED: no Blender found (INTERIOR_BLENDER / PATH)")
        return 2
    if not os.path.isfile(path):
        print(f"REFUSED: {path} is not a file — nothing to probe, no dump written")
        return 2
    ext = os.path.splitext(path)[1].lower()
    kind = kind or ("glb" if ext == ".glb" else "blend" if ext == ".blend" else None)
    if kind is None or (kind == "glb" and ext != ".glb") or \
            (kind in ("blend", "append") and ext != ".blend"):
        print(f"REFUSED: {path} is not a .blend/.glb (kind={kind})")
        return 2
    if wait:
        wait_for_idle_blender()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    # absolute paths across the spawn: the bpy side resolves a relative
    # --append/--glb path against Blender's cwd, not the caller's
    cmd = probe_cmd(exe, os.path.abspath(__file__), kind, os.path.abspath(path),
                    os.path.abspath(out))
    p = run(cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=420)
    ok = p.returncode == 0 and dump_ok(out)
    print(("OK   " if ok else "FAIL ") + f"{path} ({kind}) -> {out}")
    if not ok:
        print((p.stdout or "")[-600:])
        print((p.stderr or "")[-400:])
    return 0 if ok else 1


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
    # GLB-IMPORT DUMPS ARE KEPT OUT OF THE CONSTRUCTION TABLE. Their modifier
    # stacks are empty because the exporter baked them, and their node trees
    # are the importer's rebuild — averaging them into `subsurf_share` or
    # `mat_procedural_only_share` would report the glTF format's limits as the
    # vendors' habits. They get their own geometry-only table below.
    per_glb = collections.defaultdict(lambda: collections.defaultdict(list))
    sources = collections.Counter()
    for p in sorted(_glob.glob(os.path.join(study, "*.probe.json"))):
        aid = os.path.basename(p)[: -len(".probe.json")]
        if aid.startswith("_"):
            continue
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        src = doc.get("source", "blend")
        sources[src] += 1
        cls = cls_of.get(aid, "?")
        meshes = [o for o in doc["objects"] if o["type"] == "MESH" and "mesh" in o]
        if src != "blend":
            g = per_glb[cls]
            g["assets"].append(aid[:8])
            g["objects_per_asset"].append(doc["totals"]["objects"])
            g["verts_per_asset"].append(doc["totals"]["verts"])
            g["images_per_asset"].append(len(doc["images"]))
            dens = [o["mesh"]["verts_per_m2"] for o in meshes
                    if "verts_per_m2" in o["mesh"] and o["mesh"]["polys"] > 50]
            if dens:
                g["median_verts_per_m2_significant_meshes"].append(
                    statistics.median(dens))
            continue
        agg = per[cls]
        agg["assets"].append(aid[:8])
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

    table_glb = {}
    for cls, agg in sorted(per_glb.items()):
        row = {"n_assets": len(agg["assets"]), "assets": agg["assets"]}
        for k, v in agg.items():
            if k == "assets" or not v:
                continue
            row[k] = {"median": round(statistics.median(v), 3),
                      "min": round(min(v), 3), "max": round(max(v), 3)}
        table_glb[cls] = row

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
                   "The day-10 sample (03ede500, 0b960a0d, 17aff0ff: 19 "
                   "meshes, uniform scale, 0 moved) was then FALSIFIED as a "
                   "corpus claim by the STUDY-D11b full re-probe of all 71 "
                   ".blend entries (batch --force, 2026-09-01 21:36, 0 failed): "
                   "2 of 17 classes moved on verts_per_m2 — clock_small median "
                   "527,102 -> 863,951 (+64%, non-uniform object scale on a "
                   "miniature) and book_stack median 2,328 -> 2,517 (+8%, min "
                   "1,277 -> 2,070). Every other class was bit-identical. The "
                   "day-10 notes were corrected to these numbers with the delta "
                   "recorded beside each (INDEX §3, lamp note).",
        "assets_probed": sum(r["n_assets"] for r in table.values()),
        "dumps_by_source": dict(sources),
        "classes": table,
        "_glb_import_caveat": "classes_glb_import holds shelf entries that "
                              "exist only as GLB (probed via import_scene.gltf). "
                              "Geometry counts are POST-BAKE (modifiers applied "
                              "by the exporter at whatever level it used); no "
                              "modifier, node-tree or sheen field is reported "
                              "because those are the importer's rebuild, not "
                              "the vendor's construction.",
        "classes_glb_import": table_glb,
    }
    out = out or os.path.join(REPO_QA, "blenderkit-study-stats.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"STATS WROTE {out} — {doc['assets_probed']} assets, "
          f"{len(table)} classes")
    return 0


def parse_bpy_args(args):
    """PURE. `<out.json> [--glb P | --append P]` → (out, glb, append) or a
    string naming the refusal."""
    if not args:
        return "REFUSED: no out.json after --"
    out, glb, append = args[0], None, None
    i = 1
    while i < len(args):
        if args[i] == "--glb" and i + 1 < len(args):
            glb = args[i + 1]
            i += 2
        elif args[i] == "--append" and i + 1 < len(args):
            append = args[i + 1]
            i += 2
        else:
            return f"REFUSED: unknown probe arg {args[i]!r}"
    if glb and append:
        return "REFUSED: --glb and --append are two different sources; pick one"
    for p in (glb, append):
        if p and not os.path.isfile(p):
            return f"REFUSED: {p} does not exist — no dump written"
    return out, glb, append


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    if bpy is not None:
        args = argv[argv.index("--") + 1:] if "--" in argv else []
        parsed = parse_bpy_args(args)
        if isinstance(parsed, str):
            print(parsed)
            sys.exit(2)
        out, glb, append = parsed
        dump(out, glb=glb, append=append)
        return
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--cache", default=os.path.join("assets", "shared", "blenderkit"))
    b.add_argument("--limit", type=int, default=None)
    b.add_argument("--blender", default=None)
    b.add_argument("--force", action="store_true",
                   help="re-probe even when the dump is newer than the source")
    b.add_argument("--only", default=None,
                   help="comma list of asset-dir prefixes to restrict to")
    b.add_argument("--no-wait", action="store_true",
                   help="do not wait for other blender.exe processes to end")
    o = sub.add_parser("probe", help="probe ONE .blend or .glb into out.json")
    o.add_argument("path")
    o.add_argument("out")
    o.add_argument("--kind", choices=("blend", "glb", "append"), default=None)
    o.add_argument("--blender", default=None)
    o.add_argument("--no-wait", action="store_true")
    s = sub.add_parser("stats")
    s.add_argument("--cache", default=os.path.join("assets", "shared", "blenderkit"))
    s.add_argument("--out", default=None)
    a = ap.parse_args(argv[1:])
    if a.cmd == "stats":
        sys.exit(stats(a.cache, out=a.out))
    if a.cmd == "probe":
        sys.exit(probe_one(a.path, a.out, kind=a.kind, blender=a.blender,
                           wait=not a.no_wait))
    only = a.only.split(",") if a.only else None
    sys.exit(batch(a.cache, limit=a.limit, blender=a.blender, force=a.force,
                   only=only, wait=not a.no_wait))


if __name__ == "__main__":
    main()
