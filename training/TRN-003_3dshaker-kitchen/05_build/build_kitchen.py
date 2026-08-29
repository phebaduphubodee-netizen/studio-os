#!/usr/bin/env python3
"""build_kitchen.py - the 3D Shaker workflow, stages 2-5, run for real.

    blender -b --factory-startup -P build_kitchen.py -- --stage mood --quick

STAGES, in the tutorial's own order, and the ORDER IS THE LESSON:
  blockout : geometry only, flat clay, no light decisions yet
  mood     : ONE override material + an overcast HDRI + a sun, and NOTHING else.
             Colour, exposure and shadow contrast are settled here, on grey, before a
             single texture exists.
  split    : the override divides into a handful of tonal families (lighter / white /
             black / wood / metal / plants) - still no textures.
  texture  : real maps. Reflections before colour, always.

Everything dimensional comes from ../03_blockout/room_spec.py, which is derived from the
plate through the solved camera. Nothing here types a position a contact could give.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "03_blockout"))
import room_spec as RS                                                  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
HDRI = os.path.join(REPO, "assets", "shared", "cc0", "hdris",
                    "kloofendal_overcast_puresky_4k.hdr")

MM = 0.001
AVG_LINEAR = (0.3657, 0.2993, 0.2254)     # plate average-blur #A39583, as linear
SUN_AZIMUTH_PLAN = 21.58                  # MEASURED from the plate's floor shadows
SKIP = {}
LENS_OVERRIDE = 0.0


def wipe():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
              bpy.data.worlds, bpy.data.images, bpy.data.curves):
        for d in list(c):
            c.remove(d)


def coll(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def box(name, lo, hi, collection):
    lo = Vector([v * MM for v in lo])
    hi = Vector([v * MM for v in hi])
    me = bpy.data.meshes.new(name)
    vs = [(x, y, z) for z in (lo.z, hi.z) for y in (lo.y, hi.y) for x in (lo.x, hi.x)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def cyl(name, cx, cy, z0, z1, r, collection, verts=48):
    me = bpy.data.meshes.new(name)
    vs, fs = [], []
    for z in (z0, z1):
        for i in range(verts):
            a = 2 * math.pi * i / verts
            vs.append(((cx + r * math.cos(a)) * MM, (cy + r * math.sin(a)) * MM, z * MM))
    for i in range(verts):
        j = (i + 1) % verts
        fs.append((i, j, verts + j, verts + i))
    fs.append(tuple(range(verts)))
    fs.append(tuple(range(2 * verts - 1, verts - 1, -1)))
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def tube(name, pts, r, collection, bevel_res=5):
    """A swept circle along a polyline - R8 calls this BUILD, not ACQUIRE."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r * MM
    cu.bevel_resolution = bevel_res
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1.0)
    ob = bpy.data.objects.new(name, cu)
    collection.objects.link(ob)
    return ob


def build_room():
    shell = coll("Shell")
    mill = coll("Millwork")
    loose = coll("Loose")
    ext = coll("Exterior")
    G = RS.GLASS_Y
    # the camera stands ~12.3 m back along +Y and ~7.3 m off the kitchen wall, so the
    # room has to be that big. The walls BEHIND the camera are modelled on purpose: the
    # tutorial says so, and they are what fills the shadow side of every surface.
    X1, Y1 = 12600, 17000
    box("floor", (-400, G - 400, -60), (X1, Y1, 0), shell)
    box("ceiling", (-400, G - 400, RS.CEILING), (X1, Y1, RS.CEILING + 200), shell)
    box("wall_kitchen", (-180, G - 400, 0), (0, Y1, RS.CEILING), shell)
    box("wall_behind", (-180, Y1, 0), (X1, Y1 + 180, RS.CEILING), shell)
    box("wall_right", (X1, G, 0), (X1 + 180, Y1 + 180, RS.CEILING), shell)
    box("glazing_head", (-180, G - 60, RS.CEILING - 240), (X1, G + 60, RS.CEILING), shell)
    box("glazing_transom", (-180, G - 40, RS.TRANSOM_Z - 45),
        (X1, G + 40, RS.TRANSOM_Z + 45), shell)
    glass = box("glass", (-180, G - 12, 0), (X1, G + 12, RS.CEILING - 240), shell)
    # VERTICAL MULLIONS. Without them a 12.6 m opening throws one undifferentiated
    # wash and the floor has no pattern at all - which is exactly what the first sun
    # renders showed. The plate's floor rectangles are panes, not leaves.
    x = -180
    while x < X1:
        box("mullion_%d" % x, (x, G - 45, 0), (x + 62, G + 45, RS.CEILING - 240), shell)
        x += 2150

    box("bench", (0, RS.BENCH_Y0, RS.PLINTH), (RS.BENCH_DEPTH, RS.BENCH_Y1, RS.BENCH_H), mill)
    box("bench_plinth", (60, RS.BENCH_Y0, 0),
        (RS.BENCH_DEPTH - 60, RS.BENCH_Y1, RS.PLINTH), mill)
    box("splashback", (0, RS.BENCH_Y0, RS.BENCH_H), (28, RS.BENCH_Y1, RS.UPPERS_BOTTOM), mill)
    box("uppers", (0, RS.BENCH_Y0, RS.UPPERS_BOTTOM),
        (RS.UPPERS_DEPTH, RS.BENCH_Y1, RS.CEILING), mill)
    box("tall_bank", (0, RS.TALL_Y0, RS.PLINTH), (RS.TALL_DEPTH, RS.TALL_Y1, RS.CEILING), mill)
    box("tall_plinth", (60, RS.TALL_Y0, 0),
        (RS.TALL_DEPTH - 60, RS.TALL_Y1, RS.PLINTH), mill)
    box("oven_stack", (RS.TALL_DEPTH - 30, RS.OVEN_Y0 + 40, 900),
        (RS.TALL_DEPTH + 14, RS.OVEN_Y1 - 40, 2150), mill)

    # THE ISLAND IS TWO THINGS, not one block: a travertine volume at the near end and a
    # cantilevered slab carried on two bronze drums at the far end. Building it as one
    # long box is what made it read as a wall.
    box("island_stone", (RS.ISL_STONE_X0, RS.ISL_Y0 + 140, RS.PLINTH),
        (RS.ISL_X1, RS.ISL_Y1 - 140, RS.ISL_H - 70), mill)
    slab = box("island_slab", (RS.ISL_X0, RS.ISL_Y0, RS.ISL_H - 70),
               (RS.ISL_X1, RS.ISL_Y1, RS.ISL_H), mill)
    bev = slab.modifiers.new("bullnose", "BEVEL")
    bev.width = 0.033
    bev.segments = 6
    bev.limit_method = "ANGLE"
    ymid = (RS.ISL_Y0 + RS.ISL_Y1) / 2
    for i, x in enumerate(RS.DRUM_X):
        cyl("island_drum%d" % i, x, ymid, 0, RS.ISL_H - 70, RS.DRUM_R, mill)

    for i, x in enumerate(RS.STOOL_X):
        y = RS.STOOL_Y
        w = RS.STOOL_W / 2.0
        d = RS.STOOL_D / 2.0
        h = RS.STOOL_H
        s = RS.STOOL_SEAT
        hoop = [(x - w * .78, y + d * .8, 0), (x - w * .78, y + d * .8, s + 40),
                (x - w * .52, y + d * .8, h - 24), (x, y + d * .8, h),
                (x + w * .52, y + d * .8, h - 24), (x + w * .78, y + d * .8, s + 40),
                (x + w * .78, y + d * .8, 0)]
        tube("stool%d_hoop" % i, hoop, 11, loose)
        for sx in (-1, 1):
            tube("stool%d_leg%d" % (i, sx), [(x + sx * w * .78, y - d * .8, 0),
                                             (x + sx * w * .72, y - d * .8, s)], 11, loose)
            tube("stool%d_rail%d" % (i, sx), [(x + sx * w * .78, y - d * .8, 300),
                                              (x + sx * w * .78, y + d * .8, 300)], 9, loose)
        box("stool%d_seat" % i, (x - w * .82, y - d * .84, s - 14),
            (x + w * .82, y + d * .84, s), loose)

    if not SKIP.get("sheer"):
        build_curtain(shell)
    if not SKIP.get("canopy"):
        build_canopy(ext)
    return glass


def build_curtain(collection):
    G = RS.GLASS_Y
    n, x0, x1 = 340, -100, 12400
    top, bot = RS.CEILING - 250, 18
    me = bpy.data.meshes.new("sheer")
    vs, fs = [], []
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        wave = 55.0 * math.sin(t * math.pi * 2 * 26) + 18.0 * math.sin(t * math.pi * 2 * 61)
        for k, z in enumerate((top, bot)):
            slack = 1.0 if k == 0 else 1.28
            vs.append((x * MM, (G + 190 + wave * slack) * MM, z * MM))
    for i in range(n):
        a = 2 * i
        fs.append((a, a + 2, a + 3, a + 1))
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new("sheer", me)
    collection.objects.link(ob)
    ob.modifiers.new("thick", "SOLIDIFY").thickness = 0.0015
    return ob


def build_canopy(collection):
    """A tree, to the only precision this frame needs from it: chop the sun into
    leaf-sized pieces. The tutorial copies real trees in for exactly this and names the
    collection Trees/Shadows - the geometry exists to cast, not to be seen."""
    import random
    random.seed(7)
    me = bpy.data.meshes.new("canopy")
    vs, fs = [], []
    # THE FIRST CANOPY CAST NOTHING. It topped out at 5.4 m and sat 0.8-4.4 m outside;
    # a 12 deg sun reaching the window at z=3 was already at z=8.3 by the far edge of
    # that volume, so every ray came over the top. Geometry that exists to cast a shadow
    # has to be in the path, and the path is set by the sun angle, not by where a tree
    # would look right.
    for _ in range(4200):
        cx = random.uniform(-6000, 14000)
        cy = RS.GLASS_Y - random.uniform(500, 3200)
        cz = random.uniform(1400, 9500)
        r = random.uniform(45, 130)
        b = len(vs)
        vs += [(cx - r, cy - r * .3, cz), (cx + r, cy - r * .3, cz),
               (cx + r * .4, cy + r * .3, cz + r * 1.3),
               (cx - r * .4, cy + r * .3, cz + r * 1.3)]
        fs.append((b, b + 1, b + 2, b + 3))
    me.from_pydata([(v[0] * MM, v[1] * MM, v[2] * MM) for v in vs], [], fs)
    me.update()
    ob = bpy.data.objects.new("canopy", me)
    collection.objects.link(ob)
    return ob


def build_camera():
    import json
    cam = json.load(open(os.path.join(HERE, "..", "02_camera", "solved-camera.json")))
    S = cam["solution"]
    d = bpy.data.cameras.new("cam")
    d.sensor_fit = "HORIZONTAL"
    d.sensor_width = 36.0
    d.lens = LENS_OVERRIDE or S["lens_mm_on_36mm"]
    d.shift_y = (S["principal_point_px"][1] - cam["image"]["h"] / 2.0) / cam["image"]["w"]
    ob = bpy.data.objects.new("cam", d)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (RS.CAM_TO_KITCHEN_WALL * MM, RS.CAM_Y * MM, RS.CAM_H * MM)
    ob.rotation_euler = (math.radians(90.0), 0.0,
                         math.radians(S["blender_rotation_euler_deg"][2]))
    bpy.context.scene.camera = ob
    sc = bpy.context.scene
    sc.render.resolution_x = cam["image"]["w"]
    sc.render.resolution_y = cam["image"]["h"]
    return ob


def build_world(strength=1.0, saturation=1.0, rot_z_deg=0.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = saturation
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(HDRI)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot_z_deg)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def build_sun(elevation_deg, irradiance, warm=0.06):
    """Azimuth is MEASURED from the plate. Elevation and power are the two dials."""
    L = bpy.data.lights.new("Sun", "SUN")
    L.energy = irradiance
    L.angle = math.radians(0.526)
    L.color = (1.0, 1.0 - warm * 0.45, 1.0 - warm * 1.6)
    ob = bpy.data.objects.new("Sun", L)
    coll("Sun").objects.link(ob)
    az = math.radians(SUN_AZIMUTH_PLAN)
    el = math.radians(elevation_deg)
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), -math.sin(el)))
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ob.location = (4.0, 2.0, 8.0)
    return ob


def override_material(color=AVG_LINEAR, rough=0.4, ior=1.5):
    m = bpy.data.materials.new("Material_Lighting")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    p.inputs["Metallic"].default_value = 0.0
    p.inputs["Roughness"].default_value = rough
    p.inputs["IOR"].default_value = ior
    return m


def glass_material():
    m = bpy.data.materials.new("Glass")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (1, 1, 1, 1)
    p.inputs["Roughness"].default_value = 0.0
    p.inputs["IOR"].default_value = 1.28
    if "Transmission Weight" in p.inputs:
        p.inputs["Transmission Weight"].default_value = 1.0
    else:
        p.inputs["Transmission"].default_value = 1.0
    return m


def sheer_material():
    m = bpy.data.materials.new("Sheer")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.66, 0.58, 0.46, 1.0)
    p.inputs["Roughness"].default_value = 0.85
    out = nt.nodes["Material Output"]
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.86, 0.75, 0.55, 1.0)
    add = nt.nodes.new("ShaderNodeAddShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.45
    nt.links.new(p.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(trans.outputs[0], mix.inputs[1])
    nt.links.new(add.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def canopy_material():
    m = bpy.data.materials.new("Canopy")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.09, 0.14, 0.045, 1.0)
    p.inputs["Roughness"].default_value = 0.75
    return m


def apply(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def render_settings(quick, exposure, view="AgX"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "GPU"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = kind
                break
            except Exception:
                continue
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = True
    except Exception as e:
        print("GPU setup skipped:", e)
    sc.cycles.samples = 48 if quick else 800
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 16 if quick else 40
    sc.cycles.diffuse_bounces = 16 if quick else 40
    sc.cycles.glossy_bounces = 16 if quick else 40
    sc.cycles.transmission_bounces = 16 if quick else 40
    sc.cycles.transparent_max_bounces = 32
    if quick:
        sc.render.resolution_percentage = 50
    try:
        sc.view_settings.view_transform = view
    except TypeError:
        sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "None"
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "16"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="mood")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "mood.png"))
    ap.add_argument("--sun-el", type=float, default=26.0)
    ap.add_argument("--sun-w", type=float, default=8.1)
    ap.add_argument("--hdri-strength", type=float, default=1.0)
    ap.add_argument("--hdri-sat", type=float, default=1.35)
    ap.add_argument("--hdri-rot", type=float, default=0.0)
    ap.add_argument("--exposure", type=float, default=2.25)
    ap.add_argument("--rough", type=float, default=0.4)
    ap.add_argument("--save-blend", default="")
    ap.add_argument("--no-canopy", action="store_true")
    ap.add_argument("--no-sheer", action="store_true")
    ap.add_argument("--no-glass", action="store_true")
    ap.add_argument("--lens", type=float, default=0.0)
    ap.add_argument("--sun-az", type=float, default=-999.0)
    ap.add_argument("--no-sun", action="store_true")
    o = ap.parse_args(argv)

    global LENS_OVERRIDE
    LENS_OVERRIDE = o.lens
    SKIP["canopy"] = o.no_canopy
    SKIP["sheer"] = o.no_sheer
    wipe()
    glass = build_room()
    if o.no_glass:
        bpy.data.objects.remove(glass, do_unlink=True)
        glass = None
    build_camera()
    build_world(o.hdri_strength, o.hdri_sat, o.hdri_rot)
    global SUN_AZIMUTH_PLAN
    if o.sun_az > -900:
        SUN_AZIMUTH_PLAN = o.sun_az
    if not o.no_sun:
        build_sun(o.sun_el, o.sun_w)

    ov = override_material(rough=o.rough)
    if o.stage in ("blockout", "mood"):
        # THE OVERRIDE IS A LIGHTING INSTRUMENT, AND IT FIGHTS TRANSMISSIVE THINGS.
        # A material override replaces EVERY material, so the window glass becomes an
        # opaque grey slab and the room goes black. That is the tutorial at 10:57 - "you
        # can see that glass in our windows block the lighting so let's disable it for
        # now" - and at 13:08 he drops the curtain too, to read the mood against the
        # reference without a sheer in the way. Both come back at the material-split
        # stage with shaders of their own.
        bpy.context.view_layer.material_override = ov
        for nm in ("glass", "sheer"):
            if nm in bpy.data.objects:
                obj = bpy.data.objects[nm]
                obj.hide_render = True
                if nm == "glass":
                    glass = None
    if glass is not None:
        apply(glass, glass_material())
    for ob in bpy.data.objects:
        if ob.name == "sheer":
            apply(ob, sheer_material())
        elif ob.name == "canopy":
            apply(ob, canopy_material())
    if glass is not None:
        glass.visible_diffuse = False
        glass.visible_glossy = False
        glass.visible_shadow = False

    render_settings(o.quick, o.exposure)
    os.makedirs(os.path.dirname(o.out), exist_ok=True)
    bpy.context.scene.render.filepath = o.out
    if o.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=o.save_blend)
    bpy.ops.render.render(write_still=True)
    print("WROTE", o.out)


main()
