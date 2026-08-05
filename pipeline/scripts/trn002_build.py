"""trn002_build.py — TRN-002 materializer (Blender headless).

  blender -b --factory-startup --python pipeline/scripts/trn002_build.py -- \
      <spec.json> --out <render.png> [--quick] [--materials]

  --quick      R5 playblast rung (half res per axis, 64 samples)
  --materials  dress the masses from trn002_materials instead of clay values,
               and light the set from the spec's `light` block instead of the
               neutral form light. Phase 2 (blockout closed 2026-08-04); a
               blockout spec with no `light` block still renders exactly as it
               did, because the form light is kept as the fallback.

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
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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


def _surface(value, mat):
    """The one place a mass's shading is decided: a dressed material when the
    materials pass is on, the clay value otherwise. Kept as a single function so
    the two paths can never diverge per shape-kind (a box dressed and an oct
    left clay is exactly the kind of split nobody sees in a thumbnail)."""
    return mat if mat is not None else _clay(value)


def _box(name, c, s, value, mat=None):
    vs, fs = G.box_mesh(c, s)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _oct(name, c, s, cut, value, axis="z", tilt_deg=0.0, mat=None):
    """Rounded prism: four true ARC corners of radius `cut` mm, 6 segments each.
    Round 2 shipped this as a single 45-degree chamfer and the C3 critic read it
    as a faceted octagon, not a curve — a chamfer is not a radius. Name kept so
    specs don't churn.

    axis: which axis the prism is EXTRUDED along — "z" (default: rounding in
    plan) or "y" (rounding in the x-z SECTION: a lying cylinder when cut is
    ~half the section). Earned in r3b: the bolster was built plan-rounded and
    three blind critics could not read a lying cylinder in it, because the
    roundness was in the wrong plane.

    tilt_deg: rotation about the y-axis through the bottom-BACK edge
    (x_max, z_min) — tips the top toward +x while the back edge keeps its
    mattress contact. Earned in r3b: a "lying" pillow that still stands at 90
    degrees reads as a capsule, whatever its dimensions say.
    """
    vs, fs = G.oct_mesh(c, s, cut, axis=axis, tilt_deg=tilt_deg)
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _herringbone(name, z_mm, thick_mm, value, mat=None, **kw):
    """The measured herringbone as REAL planks, one mesh, sitting a hair proud
    of a darker base so the gaps read as joints. The floor map alone cannot do
    this: it lays parallel planks, and the target's floor is a 45-degree
    chevron whose w, L and phase were all fitted from its own joint lines."""
    kw = dict(kw)
    # 1.192 m puts exactly ONE of the map's own boards across one 132.1 mm
    # plank: the wood_floor map lays its boards at 227/2048 = 0.11084 of a tile,
    # and 132.1 / 0.11084 = 1191.8. At the previous 0.9 each plank carried ~1.3
    # of the map's boards, so a "plank" was a plank and a bit — the grain
    # crossed its own joint, which is what a real parquet never does.
    uv_scale = kw.pop("uv_scale", 1.192)
    quads = G.herringbone(**kw)
    z0, z1 = z_mm * MM, (z_mm + thick_mm) * MM
    vs, fs, uvs = [], [], []
    for q in quads:
        b = len(vs)
        vs += [(x * MM, y * MM, z1) for x, y in q]
        vs += [(x * MM, y * MM, z0) for x, y in q]
        fs.append((b, b + 1, b + 2, b + 3))                       # top
        # PER-PLANK UVs, and they are the whole point. The joints themselves are
        # SUB-PIXEL at this camera (2 mm at ~4 m through f_px 1165 is 0.58 px),
        # exactly like the wardrobe reveal the pattern pass declared
        # geometrically unresolved — so a herringbone cannot be sold by its
        # grooves here. What IS resolvable is each plank's 132 mm width (~38 px)
        # and the direction of its grain, and that only changes per plank if
        # each plank carries its own UV frame. One box projection over the whole
        # floor gives every plank identical grain, which is a parquet-printed-
        # on-lino look no amount of joint tuning can fix.
        ex = ((q[1][0] - q[0][0]), (q[1][1] - q[0][1]))
        ln = (ex[0] ** 2 + ex[1] ** 2) ** 0.5 or 1.0
        ux, uy = ex[0] / ln, ex[1] / ln
        for (px, py) in q:
            dx, dy = (px - q[0][0]) * MM, (py - q[0][1]) * MM
            along = (dx * ux + dy * uy) / uv_scale      # along the plank's length
            across = (-dx * uy + dy * ux) / uv_scale    # across its width
            # U <- ACROSS, V <- ALONG. The map's boards run along its V axis, so
            # feeding the plank's length into U laid the grain ACROSS every
            # plank — the one orientation a parquet floor never has.
            uvs.append((across, along))
        for k in range(4):
            k2 = (k + 1) % 4
            fs.append((b + k, b + 4 + k, b + 4 + k2, b + k2))     # side
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        if len(poly.vertices) == 4 and poly.vertices[0] % 8 == 0 and \
                poly.vertices[0] // 8 * 4 + 3 < len(uvs) and \
                all(v - poly.vertices[0] < 4 for v in poly.vertices):
            base_uv = poly.vertices[0] // 8 * 4
            for j, li in enumerate(poly.loop_indices):
                uvl.data[li].uv = uvs[base_uv + j]
    me.materials.append(_surface(value, mat))
    ob = bpy.data.objects.new(f"SM_TRN002_{name}", me)
    bpy.context.scene.collection.objects.link(ob)
    print(f"herringbone: {len(quads)} planks, {len(vs)} verts")
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


def build_light(spec=None):
    """Blockout rounds 1-5: a neutral FORM light — bright world + one soft sun —
    whose only job was to let geometry read. Phase 2 replaces it with the
    measured story (trn002_light) the moment the spec carries a `light` block,
    so every blockout spec still renders exactly as it did.

    The form light is also the reason four blind critics counted 6-7 downlights
    in a 4-downlight room: a flat world washes bright pools that read as
    fixtures. Killing those is a named phase-2 ticket, and it is killed HERE."""
    if spec and spec.get("light"):
        import trn002_light as LIGHT
        LIGHT.build_world(spec)
        LIGHT.build_lights(spec)
        return
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

    # R10 RULE GATE, before a single vertex is made. It sits here rather than in
    # a checklist because the only rules this repo has ever actually kept are
    # the ones that are programs in a path someone already runs — the placement
    # gate below has never been skipped, while "write the triage" and "distil
    # the learning" drifted the moment nobody was watching. `--no-rule-gate`
    # exists for bisecting an old spec, and prints loudly that it was used.
    import rule_gate as RULES
    if "--no-rule-gate" in argv:
        print("!! RULE GATE BYPASSED by --no-rule-gate")
    else:
        # require_seen is ON: after the object-justification audit every mass
        # can point at itself in the reference, so the strict form is now the
        # cheap one. It is the only check that catches an invented object whose
        # derivation is impeccable — lamp_stem's prov ("rest_on nightstand top
        # 481, carries shade") was a perfectly well-formed contact for a thing
        # that is not in the room.
        RULES.enforce(spec, inbox_root=os.path.join(REPO, "knowledge", "_inbox"),
                      require_seen=True)

    materials = None
    if "--materials" in argv:
        import trn002_materials as MAT
        materials = MAT.build_materials(palette_override=spec.get("materials"))
        print("materials ON\n" + MAT.palette_report())

    def mat_of(name):
        if materials is None:
            return None
        import trn002_materials as MAT
        return materials[MAT.material_for(name)]

    built = {}
    for m in spec["masses"]:
        if m.get("kind") == "herringbone":
            built[m["name"]] = _herringbone(
                m["name"], m["c"][2], m["s"][2], m["value"],
                mat=mat_of(m["name"]), **(m.get("lattice") or {}))
        elif m.get("kind") == "oct":
            built[m["name"]] = _oct(m["name"], m["c"], m["s"], m.get("cut", 200),
                                    m["value"], axis=m.get("axis", "z"),
                                    tilt_deg=m.get("tilt_deg", 0.0),
                                    mat=mat_of(m["name"]))
        else:
            built[m["name"]] = _box(m["name"], m["c"], m["s"], m["value"],
                                    mat=mat_of(m["name"]))
    # "parent": <mass> declares an assembly IN the scene — placement_check groups
    # by Blender hierarchy ("the scene's own declaration of what moves together"),
    # so a shade over its stem is judged as one lamp, not as a slab teetering on a
    # post. Meshes carry world coords with identity transforms, so no inverse
    # matrix is needed.
    for m in spec["masses"]:
        if m.get("parent"):
            built[m["name"]].parent = built[m["parent"]]
    cam_ob = build_camera(spec["camera"])
    build_light(spec)
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
