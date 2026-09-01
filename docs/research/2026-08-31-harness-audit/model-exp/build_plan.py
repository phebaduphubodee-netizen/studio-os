"""Harness-audit modeling experiment: execute a parameterised furniture plan in Blender.

The plan JSON is authored by a fresh-context planner agent from a reference photo.
This interpreter speaks R8's YES-branch only — boxes with radii, extruded measured
profiles, mirrored instances — and R9's placement law: every position is derived
from a declared contact (rest_on + face anchors); nothing accepts a typed
coordinate, and unknown references raise instead of defaulting to the origin.

Run:  blender -b --factory-startup --python build_plan.py -- plan.json out_dir
"""
import bpy
import bmesh
import json
import math
import os
import sys

MM = 0.001


def die(msg):
    print(f"BUILD-FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def clear_scene():
    # --factory-startup ships a default cube; this repo has shipped frames it
    # corrupted, so the first act is always an explicit wipe.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for x in list(coll):
            coll.remove(x)


def make_box(name, size_mm, bevel_mm=0, bevel_segments=2, crown_mm=0, subsurf=0,
             taper_bottom_frac=None):
    sx, sy, sz = [max(v, 1.0) * MM for v in size_mm]
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if taper_bottom_frac is not None:
        f = max(0.05, min(1.0, float(taper_bottom_frac)))
        zmin = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            if abs(v.co.z - zmin) < 1e-6:
                v.co.x *= f
                v.co.y *= f
    if crown_mm and crown_mm > 0:
        top = [f for f in bm.faces if f.normal.z > 0.5]
        edges = {e for f in top for e in f.edges}
        bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=3, use_grid_fill=True)
        zmax = max(v.co.z for v in bm.verts)
        halfdiag = math.hypot(sx, sy) / 2
        # raise INTERIOR verts of the top face only — raising boundary verts
        # plants a visible pole on the front edge (comparator round-1 item 4)
        for v in bm.verts:
            if (abs(v.co.z - zmax) < 1e-6
                    and abs(v.co.x) < sx / 2 - 1e-9
                    and abs(v.co.y) < sy / 2 - 1e-9):
                d = math.hypot(v.co.x, v.co.y) / halfdiag
                v.co.z += crown_mm * MM * max(0.0, 1.0 - d * d)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    _finish(obj, bevel_mm, bevel_segments, subsurf)
    return obj


def make_profile(name, profile_mm, plane, depth_mm, bevel_mm=0, bevel_segments=2, subsurf=0):
    if len(profile_mm) < 3:
        die(f"{name}: profile needs >=3 points")
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = []
    for a, b in profile_mm:
        if plane == "xz":      # side silhouette, extruded across width (y)
            co = (a * MM, 0.0, b * MM)
        elif plane == "yz":    # front silhouette, extruded along x
            co = (0.0, a * MM, b * MM)
        else:
            die(f"{name}: unknown profile_plane {plane}")
        verts.append(bm.verts.new(co))
    face = bm.faces.new(verts)
    vec = (0, depth_mm * MM, 0) if plane == "xz" else (depth_mm * MM, 0, 0)
    r = bmesh.ops.extrude_face_region(bm, geom=[face])
    moved = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=vec, verts=moved)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    _finish(obj, bevel_mm, bevel_segments, subsurf)
    return obj


def _finish(obj, bevel_mm, bevel_segments, subsurf):
    if bevel_mm and bevel_mm > 0:
        m = obj.modifiers.new("bevel", "BEVEL")
        m.width = bevel_mm * MM
        m.segments = max(1, int(bevel_segments))
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(40)
    if subsurf:
        m = obj.modifiers.new("subsurf", "SUBSURF")
        m.levels = m.render_levels = min(2, int(subsurf))
        for p in obj.data.polygons:
            p.use_smooth = True


def bounds_world(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
    ev.to_mesh_clear()
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def face_val(rng, face, axis_name, comp_name):
    lo, hi = rng
    if face == "min":
        return lo
    if face == "max":
        return hi
    if face == "center":
        return (lo + hi) / 2
    die(f"{comp_name}: unknown {axis_name} face '{face}' (use min|max|center)")


def place_z(objs, placed, comp):
    name = comp["name"]
    ro = comp.get("rest_on", "floor")
    if ro == "floor":
        ztarget = 0.0
    elif placed[ro]["z"]:
        ztarget = bounds_world(objs[ro])[2][1]
    else:
        return False
    obj = objs[name]
    z0 = bounds_world(obj)[2][0]
    obj.location.z += ztarget - z0
    placed[name]["z"] = True
    return True


def place_axis(objs, placed, comp, axis):
    name = comp["name"]
    anchor = comp.get(f"{axis}_anchor")
    if anchor is None:
        die(f"{name}: missing {axis}_anchor — a position that can be derived "
            f"from a contact must never be typed, and never omitted either")
    ref = anchor.get("ref", "origin")
    if ref == "origin":
        ref_v = 0.0
    elif placed[ref][axis]:
        r = bounds_world(objs[ref])
        ref_v = face_val(r[0] if axis == "x" else r[1],
                         anchor.get("ref_face", "center"), axis, name)
    else:
        return False
    obj = objs[name]
    rng = bounds_world(obj)[0 if axis == "x" else 1]
    own_v = face_val(rng, anchor.get("own_face", "center"), axis, name)
    delta = ref_v + anchor.get("gap_mm", 0) * MM - own_v
    if axis == "x":
        obj.location.x += delta
    else:
        obj.location.y += delta
    placed[name][axis] = True
    return True


def mirror_component(objs, comp):
    src = comp.get("mirror_of")
    about = comp.get("mirror_about")
    if src not in objs:
        die(f"{comp['name']}: mirror_of names unknown component '{src}'")
    if about not in objs:
        die(f"{comp['name']}: mirror_about names unknown component '{about}'")
    (ax0, ax1), _, _ = bounds_world(objs[about])
    cx = (ax0 + ax1) / 2
    srco = objs[src]
    obj = srco.copy()
    obj.data = srco.data
    obj.name = comp["name"]
    bpy.context.collection.objects.link(obj)
    obj.matrix_world = srco.matrix_world.copy()
    # reflect about the plane x = cx
    from mathutils import Matrix
    refl = (Matrix.Translation((cx, 0, 0))
            @ Matrix.Scale(-1, 4, (1, 0, 0))
            @ Matrix.Translation((-cx, 0, 0)))
    obj.matrix_world = refl @ obj.matrix_world
    return obj


def add_material(objs, plan):
    mat = bpy.data.materials.new("charcoal")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.13, 0.14, 0.16, 1)
    bsdf.inputs["Roughness"].default_value = 0.85
    legmat = bpy.data.materials.new("leg_wood")
    legmat.use_nodes = True
    lb = legmat.node_tree.nodes["Principled BSDF"]
    lb.inputs["Base Color"].default_value = (0.09, 0.06, 0.04, 1)
    lb.inputs["Roughness"].default_value = 0.5
    for comp in plan["components"]:
        obj = objs.get(comp["name"])
        if obj is None:
            continue
        hint = (comp.get("material_hint") or "fabric").lower()
        obj.data.materials.clear() if obj.data.materials else None
        obj.data.materials.append(legmat if "wood" in hint or "leg" in hint else mat)


def add_stage_and_camera(objs):
    xs, ys, zs = [], [], []
    for o in objs.values():
        (x0, x1), (y0, y1), (z0, z1) = bounds_world(o)
        xs += [x0, x1]; ys += [y0, y1]; zs += [z0, z1]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(zs) - min(zs))

    mesh = bpy.data.meshes.new("floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=span * 4)
    bm.to_mesh(mesh); bm.free()
    floor = bpy.data.objects.new("floor", mesh)
    bpy.context.collection.objects.link(floor)
    floor.location = (cx, cy, 0)
    fm = bpy.data.materials.new("floor_mat"); fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.82, 0.80, 0.78, 1)
    floor.data.materials.append(fm)

    cam = bpy.data.cameras.new("cam")
    camo = bpy.data.objects.new("cam", cam)
    bpy.context.collection.objects.link(camo)
    az, el, dist = math.radians(-15), math.radians(12), span * 2.6
    camo.location = (cx + dist * math.cos(el) * math.sin(az),
                     cy - dist * math.cos(el) * math.cos(az),
                     max(zs) * 0.5 + dist * math.sin(el))
    from mathutils import Vector
    look = Vector((cx, cy, max(zs) * 0.45))
    direction = look - camo.location
    camo.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camo

    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 3.5
    suno = bpy.data.objects.new("sun", sun)
    bpy.context.collection.objects.link(suno)
    suno.rotation_euler = (math.radians(50), 0, math.radians(160))
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.9, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    bpy.context.scene.world = world


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    plan_path, out_dir = argv[0], argv[1]
    os.makedirs(out_dir, exist_ok=True)
    plan = json.load(open(plan_path, encoding="utf-8"))

    clear_scene()
    comps = plan["components"]
    all_names = {c["name"] for c in comps}
    for comp in comps:
        deps = [comp.get("rest_on", "floor"), comp.get("mirror_of"), comp.get("mirror_about")]
        for a in ("x_anchor", "y_anchor"):
            if isinstance(comp.get(a), dict):
                deps.append(comp[a].get("ref", "origin"))
        for d in deps:
            if d not in (None, "floor", "origin") and d not in all_names:
                die(f"{comp['name']}: references unknown component '{d}'")

    # PASS 1 — geometry for every non-mirror component, at the origin.
    objs = {}
    placed = {}
    for comp in comps:
        if comp.get("mirror_of"):
            continue
        op = comp.get("op")
        if op == "box_round":
            objs[comp["name"]] = make_box(comp["name"], comp["size_mm"],
                                          comp.get("bevel_mm", 0), comp.get("bevel_segments", 2),
                                          comp.get("crown_mm", 0), comp.get("subsurf", 0),
                                          comp.get("taper_bottom_frac"))
        elif op == "extrude_profile":
            objs[comp["name"]] = make_profile(comp["name"], comp["profile_mm"],
                                              comp.get("profile_plane", "xz"),
                                              comp["depth_mm"], comp.get("bevel_mm", 0),
                                              comp.get("bevel_segments", 2), comp.get("subsurf", 0))
        else:
            die(f"{comp['name']}: unknown op '{op}'")
        placed[comp["name"]] = {"x": False, "y": False, "z": False}

    # PASS 2 — fixed-point placement, PER AXIS: the contact graph only needs to be
    # acyclic per axis (legs carry the deck in z while the deck locates the legs
    # in x), which is how real assemblies constrain each other. Mirrors
    # materialise once their source is fully placed and the mirror plane is known.
    mirrors_todo = [c for c in comps if c.get("mirror_of")]
    progress = True
    while progress:
        progress = False
        for comp in comps:
            name = comp["name"]
            if comp.get("mirror_of") or name not in placed:
                continue
            st = placed[name]
            if not st["z"] and place_z(objs, placed, comp):
                progress = True
            if not st["x"] and place_axis(objs, placed, comp, "x"):
                progress = True
            if not st["y"] and place_axis(objs, placed, comp, "y"):
                progress = True
        for comp in list(mirrors_todo):
            src, about = comp["mirror_of"], comp["mirror_about"]
            if src in placed and all(placed[src].values()) and placed.get(about, {}).get("x"):
                objs[comp["name"]] = mirror_component(objs, comp)
                placed[comp["name"]] = {"x": True, "y": True, "z": True}
                mirrors_todo.remove(comp)
                progress = True
    stuck = [n for n, st in placed.items() if not all(st.values())] + [c["name"] for c in mirrors_todo]
    if stuck:
        die("placement could not settle (cyclic within one axis, or an unplaced ref): "
            + ", ".join(stuck))

    add_material(objs, plan)
    add_stage_and_camera(objs)

    scene = bpy.context.scene
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1100, 750
    scene.render.filepath = os.path.join(out_dir, "render.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "scene.blend"))

    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs.values():
        ev = o.evaluated_get(dg)
        m = ev.to_mesh()
        m.calc_loop_triangles()
        tris += len(m.loop_triangles)
        ev.to_mesh_clear()
    print(f"BUILD-OK components={len(objs)} tris={tris} render={scene.render.filepath}")


if __name__ == "__main__":
    main()
