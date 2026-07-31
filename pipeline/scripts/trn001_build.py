"""trn001_build.py — TRN-001 reproduction materializer (INSIDE Blender).

Walks the charter's element ladder (qa/reproduction-curriculum.md): round 1
camera + blockout, round 2 joinery, round 3 materials, and the light story
still to come. Invocation (pipeline/CLAUDE.md law: headless, factory startup,
data-API geometry only):

  blender -b --factory-startup --python pipeline/scripts/trn001_build.py -- \
      <spec.json> --out <dir> [--tag v001] [--quick] [--materials] [--idmask]

  --quick      R5 playblast rung (48 samples, half res per axis)
  --materials  dress the masses from trn001_materials instead of clay values
  --idmask     one emission colour per mass, 1 sample, black world — the
               instrument that caught a foreign object the spec-side checks
               could not see (2026-07-31)

Writes <out>/trn001_blockout_<tag>[_ql].png, a .blend beside it, and
<out>/trn001_projections_<tag>.json holding BOTH Blender's own
world_to_camera_view pixel positions of every solve landmark AND the pure-math
projection from trn001_geom — the two must agree; a mismatch is printed LOUDLY
so the solver can never drift from the render.
"""
import json
import math
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import trn001_geom as G          # noqa: E402
import trn001_light as LIGHT     # noqa: E402
import trn001_materials as MAT   # noqa: E402
import trn001_styling as STYLE   # noqa: E402
from quicklook import quick_params  # noqa: E402

FULL_SAMPLES = 128
RES = 2048


# ------------------------------------------------------------------ geometry --

def _mesh_from_outline(name, outline, z0, z1):
    """Extruded prism from a plan outline: side quads + n-gon caps (render-only
    blockout — not export geometry, so caps may be n-gons)."""
    n = len(outline)
    verts = [(x * G.MM, y * G.MM, z0 * G.MM) for x, y in outline] + \
            [(x * G.MM, y * G.MM, z1 * G.MM) for x, y in outline]
    faces = [[i, (i + 1) % n, (i + 1) % n + n, i + n] for i in range(n)]
    faces.append(list(range(n - 1, -1, -1)))            # bottom cap
    faces.append(list(range(n, 2 * n)))                 # top cap
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    return me


IDMASK = False
_ID_PALETTE = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1),
               (1, 0.5, 0), (0.5, 0, 1), (0, 0.5, 0), (0.5, 0.25, 0), (0, 0.5, 0.5),
               (0.75, 0.75, 0.75), (0.25, 0.25, 0.25), (1, 0.75, 0.8)]
_id_counter = {"i": 0}


def _clay(value):
    if IDMASK:
        i = _id_counter["i"]
        _id_counter["i"] += 1
        c = _ID_PALETTE[i % len(_ID_PALETTE)]
        mat = bpy.data.materials.new(f"M_TRN001_id_{i}")
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (*c, 1.0)
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], outn.inputs[0])
        print(f"idmask colour {i} {c} -> next mass")
        return mat
    key = f"M_TRN001_clay_{value:.2f}"
    mat = bpy.data.materials.get(key)
    if mat:
        return mat
    mat = bpy.data.materials.new(key)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (value, value, value, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
    return mat


def clear_default_scene():
    """--factory-startup ships a default Cube + Light + Camera. The cube sat
    invisibly (same clay grey) in front of the altar for THREE renders and a
    filtered bbox dump before the ID-mask instrument caught it (2026-07-31).
    Data-API removal, no bpy.ops."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def build_masses(spec, materials=None):
    col = bpy.context.scene.collection
    for m in G.masses(spec):
        cx, cy, cz = m["c"]
        sx, sy, sz = m["s"]
        outline = G.rounded_outline(cx, cy, sx, sy, m["radii"])
        me = _mesh_from_outline(f"SM_TRN001_{m['name']}", outline,
                                cz - sz / 2.0, cz + sz / 2.0)
        if IDMASK:
            print(f"idmask mass {m['name']}")
            me.materials.append(_clay(m["value"]))
        elif materials:
            key = MAT.material_for(m["name"])
            me.materials.append(materials[key])
        else:
            me.materials.append(_clay(m["value"]))
        ob = bpy.data.objects.new(f"SM_TRN001_{m['name']}", me)
        col.objects.link(ob)


# ------------------------------------------------------------------- camera --

def build_camera(cam):
    data = bpy.data.cameras.new("CAM_TRN001")
    data.lens = cam["focal_mm"]
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = G.SENSOR_MM
    data.shift_x = cam.get("shift_x", 0.0)
    data.shift_y = cam.get("shift_y", 0.0)
    ob = bpy.data.objects.new("CAM_TRN001", data)
    ob.location = (cam["x_mm"] * G.MM, cam["y_mm"] * G.MM, cam["z_mm"] * G.MM)
    ob.rotation_euler = (math.pi / 2, 0.0, -math.radians(cam["yaw_deg"]))
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


# -------------------------------------------------------------------- light --

def build_light(spec):
    """Rounds 1-3: a neutral FORM light — bright world + one soft sun — whose
    only job was to let geometry read. Round 4 replaces it with the measured
    story (trn001_light) the moment the spec carries a `light` block, so a
    round-1..3 spec still renders exactly as it did."""
    if spec.get("light"):
        LIGHT.build_world(spec)
        LIGHT.build_lights(spec)
        print("light story ON\n" + LIGHT.report(spec))
        return True
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 0.55
    sun = bpy.data.lights.new("SUN_TRN001", type="SUN")
    sun.energy = 2.0
    sun.angle = math.radians(8)
    ob = bpy.data.objects.new("SUN_TRN001", sun)
    ob.rotation_euler = (math.radians(55), 0.0, math.radians(-35))
    bpy.context.scene.collection.objects.link(ob)
    return False


# ------------------------------------------------------------------- render --

def setup_render(quick, out_png, spec=None):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    samples, (w, h) = (FULL_SAMPLES, (RES, RES))
    if quick:
        samples, (w, h) = quick_params(FULL_SAMPLES, (RES, RES))
    sc.cycles.samples = 1 if IDMASK else samples
    sc.cycles.use_denoising = not IDMASK
    if IDMASK and sc.world:
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    prefs = bpy.context.preferences.addons.get("cycles")
    device = "CPU"
    if prefs:
        cp = prefs.preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                cp.compute_device_type = kind
                cp.get_devices()
                for d in cp.devices:
                    d.use = True
                if any(d.use and d.type != "CPU" for d in cp.devices):
                    sc.cycles.device = "GPU"
                    device = kind
                    break
            except Exception:
                continue
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_png
    # Standard is a straight line with no shoulder: under it our halo clipped
    # 2.15% of the frame where the target clips 0.08%. AgX has the shoulder, so
    # a source can be bright without becoming a hole in the image.
    vt = "Standard"
    if spec is not None and spec.get("light") and not IDMASK:
        vt = LIGHT.apply_film(spec, sc)
    else:
        sc.view_settings.view_transform = "Standard"
    print(f"cycles device={device} samples={samples} res={w}x{h} view={vt}")  # keep: silent-CPU catch


def dump_projections(spec, cam_ob, path):
    """Blender's own projection of every solve landmark + the pure-math one.
    Disagreement > 1.5 px prints LOUDLY (the solver must match the render)."""
    from bpy_extras.object_utils import world_to_camera_view as w2cv
    sc = bpy.context.scene
    res = RES  # projections are always reported in full-res pixels
    out, bad = {}, []
    pure = G.project_all(spec["camera"], spec, res=res)
    for name, p in G.landmarks_3d(spec).items():
        import mathutils
        co = w2cv(sc, cam_ob, mathutils.Vector((p[0] * G.MM, p[1] * G.MM, p[2] * G.MM)))
        upx, vpx = co.x * res, (1.0 - co.y) * res
        pu = pure.get(name)
        d = None if pu is None else math.hypot(upx - pu[0], vpx - pu[1])
        out[name] = {"blender": [upx, vpx], "pure": list(pu) if pu else None,
                     "agree_px": d}
        if d is None or d > 1.5:
            bad.append((name, d))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    if bad:
        print(f"PROJECTION MISMATCH pure-vs-blender (>1.5px): {bad}")
    else:
        print(f"projections agree pure==blender for {len(out)} landmarks")


def main():
    global IDMASK
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec_path = argv[0]
    quick = "--quick" in argv
    IDMASK = "--idmask" in argv
    tag = argv[argv.index("--tag") + 1] if "--tag" in argv else "v001"
    # ABSOLUTE paths only past this line: Blender resolves a relative render
    # filepath against its own notion of cwd (smoke run landed in C:\_private).
    out_dir = os.path.abspath(argv[argv.index("--out") + 1])
    spec_path = os.path.abspath(spec_path)
    os.makedirs(out_dir, exist_ok=True)

    spec = G.load_spec(spec_path)
    clear_default_scene()
    materials = None
    if "--materials" in argv and not IDMASK:
        materials = MAT.build_materials(
            emission_override={"halo_led": LIGHT.halo_watt(spec)})
        print("materials ON\n" + MAT.palette_report())
    build_masses(spec, materials)
    if spec.get("styling") and not IDMASK:
        STYLE.build_styling(spec, materials)
        print("styling ON\n" + STYLE.report(spec))
    cam_ob = build_camera(spec["camera"])
    build_light(spec)

    suffix = "_ql" if quick else ""
    out_png = os.path.join(out_dir, f"trn001_blockout_{tag}{suffix}.png")
    setup_render(quick, out_png, spec)
    # depsgraph update so world_to_camera_view sees final transforms
    bpy.context.view_layer.update()
    dump_projections(spec, cam_ob, os.path.join(out_dir, f"trn001_projections_{tag}.json"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, f"trn001_{tag}.blend"))
    bpy.ops.render.render(write_still=True)  # 'render' op is headless-safe (unlike geometry ops)
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
