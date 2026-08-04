"""trn002_build.py — TRN-002 blockout materializer (Blender headless).

  blender -b --factory-startup --python pipeline/scripts/trn002_build.py -- \
      <spec.json> --out <render.png> [--quick]

Round-1 scope: every mass is a clay box straight from the spec (the spec's
numbers are MEASURED through the solved camera — see trn002_station.py), a
neutral form light, and two verification rungs before any pixel is trusted:
  1. PROJECTION DUMP — pure-math projection vs Blender's world_to_camera_view
     for every landmark (>1.5 px disagreement prints LOUDLY), plus the pixel
     error against the MEASURED landmark table (the round metric of record).
  2. R9b PLACEMENT GATE — placement_dump + placement_check on the built scene,
     FAIL-loud (floating / overhang / off-axis; no allowlist).
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trn002_geom as G  # noqa: E402

MM = 0.001
FULL_SAMPLES = 128


def _clay(value):
    name = f"M_clay_{value:.2f}"
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (value, value, value, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    return m


def _box(name, c, s, value):
    x, y, z = (v * MM for v in c)
    sx, sy, sz = (v * MM / 2 for v in s)
    vs = [(x + dx * sx, y + dy * sy, z + dz * sz)
          for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4), (1, 5, 7, 3),
          (0, 4, 5, 1), (2, 3, 7, 6)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_clay(value))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _oct(name, c, s, cut, value):
    """Rounded-plan prism: four true ARC corners of radius `cut` mm, 6 segments
    each. Round 2 shipped this as a single 45-degree chamfer and the C3 critic
    read it as a faceted octagon, not a curve — a chamfer is not a radius, and
    'มุมโค้ง' is geometry the blockout owes (C2's point, accepted). Name kept
    so specs don't churn."""
    import math as _m
    x, y, z = (v * MM for v in c)
    sx, sy = s[0] * MM / 2, s[1] * MM / 2
    z0, z1 = z - s[2] * MM / 2, z + s[2] * MM / 2
    r = min(cut * MM, sx * 0.95, sy * 0.95)
    SEG = 6
    ring = []
    for ccx, ccy, a0 in ((x + sx - r, y - sy + r, -90.0), (x + sx - r, y + sy - r, 0.0),
                         (x - sx + r, y + sy - r, 90.0), (x - sx + r, y - sy + r, 180.0)):
        for i in range(SEG + 1):
            a = _m.radians(a0 + 90.0 * i / SEG)
            ring.append((ccx + r * _m.cos(a), ccy + r * _m.sin(a)))
    n = len(ring)
    vs = [(px, py, z0) for px, py in ring] + [(px, py, z1) for px, py in ring]
    fs = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    fs += [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_clay(value))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_camera(cam):
    data = bpy.data.cameras.new("CAM_TRN002")
    data.lens = cam["focal_mm"]
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = G.SENSOR_MM
    data.shift_x = cam.get("shift_x", 0.0)
    data.shift_y = cam.get("shift_y", 0.0)
    ob = bpy.data.objects.new("CAM_TRN002", data)
    ob.location = (cam["x_mm"] * MM, cam["y_mm"] * MM, cam["z_mm"] * MM)
    ob.rotation_euler = (math.pi / 2, 0.0, -math.radians(cam["yaw_deg"]))
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def build_light():
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 0.55
    sun = bpy.data.lights.new("SUN_TRN002", type="SUN")
    sun.energy = 2.0
    sun.angle = math.radians(8)
    ob = bpy.data.objects.new("SUN_TRN002", sun)
    ob.rotation_euler = (math.radians(55), 0.0, math.radians(-35))
    bpy.context.scene.collection.objects.link(ob)


def setup_render(spec, out_png, quick):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    W, H = spec["image"]["w"], spec["image"]["h"]
    samples = FULL_SAMPLES
    if quick:
        W, H, samples = W // 2, H // 2, 64
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    rn = spec.get("render") or {}
    for k, dflt in (("diffuse_bounces", 4), ("max_bounces", 12),
                    ("glossy_bounces", 4), ("sample_clamp_indirect", 10.0)):
        setattr(sc.cycles, k, type(dflt)(rn.get(k, dflt)))
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
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = out_png
    sc.view_settings.view_transform = "Standard"
    print(f"cycles device={device} samples={samples} res={W}x{H} "
          f"diff_bounce={sc.cycles.diffuse_bounces}")  # keep: silent-CPU catch


def dump_projections(spec, cam_ob, path):
    from bpy_extras.object_utils import world_to_camera_view as w2cv
    import mathutils
    sc = bpy.context.scene
    W, H = spec["image"]["w"], spec["image"]["h"]
    cam = spec["camera"]
    measured = spec.get("landmarks_px", {})
    out, bad, errs = {}, [], []
    print("\nlandmark             pure(u,v)        w2cv(u,v)        vs measured px")
    for name, p in spec["landmarks_3d"].items():
        pure = G.project(cam, p, (W, H))
        co = w2cv(sc, cam_ob, mathutils.Vector((p[0] * MM, p[1] * MM, p[2] * MM)))
        blend = (co.x * W, (1.0 - co.y) * H)
        row = {"pure": pure, "blender": blend}
        d_pb = math.hypot(pure[0] - blend[0], pure[1] - blend[1]) if pure else 1e9
        if d_pb > 1.5:
            bad.append(f"{name}: pure {pure} vs blender {blend} ({d_pb:.2f}px)")
        msg = ""
        if name in measured and pure:
            mu, mv = measured[name]
            e = math.hypot(pure[0] - mu, pure[1] - mv)
            errs.append(e)
            row["err_px"] = round(e, 2)
            msg = f"err={e:6.2f}"
        out[name] = row
        print(f"  {name:18s} ({pure[0]:7.1f},{pure[1]:7.1f}) "
              f"({blend[0]:7.1f},{blend[1]:7.1f})  {msg}")
    if errs:
        errs.sort()
        print(f"\nmetric of record: n={len(errs)} mean={sum(errs)/len(errs):.2f}px "
              f"median={errs[len(errs)//2]:.2f}px max={max(errs):.2f}px @1080")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    if bad:
        raise SystemExit("PROJECTION MODEL DISAGREES WITH BLENDER:\n  " + "\n  ".join(bad))


def placement_gate(out_json):
    import placement_check as PC
    import placement_dump as PD
    bpy.context.view_layer.update()
    objs = PD.dump()
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"unit": "mm", "objects": objs}, f, indent=1, ensure_ascii=False)
    found = [f for f in PC.check(objs) if f["sev"] == "FAIL"]
    n_adv = len(PC.check(objs)) - len(found)
    print(f"PLACEMENT: {len(objs)} objects, {len(found)} FAIL, {n_adv} advisory")
    if found:
        for f in found:
            print(f"  !! {f['kind']} {f['object']}: {f['detail']}")
        raise SystemExit("PLACEMENT GATE FAILED (R9b)")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec_path = argv[0]
    # ABSOLUTE, ONCE, FOR EVERY WRITER. Blender resolves a drive-less relative
    # path against the DRIVE ROOT while Python resolves against the CWD — the
    # exact split that let TRN-001's id_mask write client pixels to C:\_private
    # outside the repo. One resolution here, all writers inherit it.
    out_png = os.path.abspath(argv[argv.index("--out") + 1])
    quick = "--quick" in argv
    spec = G.load_spec(spec_path)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials):
        for ob in list(coll):
            coll.remove(ob)

    for m in spec["masses"]:
        if m.get("kind") == "oct":
            _oct(m["name"], m["c"], m["s"], m.get("cut", 200), m["value"])
        else:
            _box(m["name"], m["c"], m["s"], m["value"])
    cam_ob = build_camera(spec["camera"])
    build_light()
    setup_render(spec, out_png, quick)

    base = os.path.splitext(out_png)[0]
    bpy.context.view_layer.update()
    dump_projections(spec, cam_ob, base + ".projections.json")
    placement_gate(base + ".placement.json")

    bpy.ops.wm.save_as_mainfile(filepath=base + ".blend")
    bpy.ops.render.render(write_still=True)
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
