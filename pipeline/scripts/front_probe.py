"""front_probe.py — measure an acquired asset's NATIVE FRONT by orthographic
elevation, the same procedure that measured the nine CC0 meshes in
MODEL_FRONT_DEG ("every mesh was imported headless and shot in orthographic
elevation from the SOUTH", build_room.py).

CLI-ONLY: run at ingest for every acquired asset that will pass through
`model_rot`. The consumer that CANNOT be skipped is `model_rot` itself — since
2026-08-26 it FAILS CLOSED on any model id with no row in
qa/model-front-registry.json, so an unprobed fronted asset stops the build
rather than rotating silently (the p2r75 nightstand defect: rot=90 applied to
an UNMEASURED front, closure "verified" from the builder's own crop, refuted by
the owner's eye the same day — docs/process-debate-2026-08-25.md).

WHAT IT DOES: imports one .glb/.gltf headless, frames it with an orthographic
camera from the four cardinals at eye-ish height, renders four elevations
(front_S/E/N/W.png). A SIGHTED reader (builder + crop, or the closure verifier)
then SIGNS which elevation shows the functional front (drawer face, pull,
opening) and writes the registry row:

    front azimuth (deg, +X=0, +Y=90):  S view shows front -> -90
                                       E view shows front ->   0
                                       N view shows front ->  90
                                       W view shows front -> 180
    no functional front (rotation-invariant) -> front_deg: null, with reason.

The AZIMUTH is what MODEL_FRONT_DEG stores; THE LAW in build_room.py converts:
    place_model.rot = spec_rot - 90 - front_deg

INVOCATION (headless, one process — pipeline/CLAUDE.md):
    blender -b --factory-startup --python pipeline/scripts/front_probe.py -- \
        <asset.glb> <out_dir>

LAYER NOTE: this file is the one Blender-layer step of the front law; the
registry it feeds and the checks that read it are pure (front_registry.py).
"""
import math
import os
import sys

import bpy


def _args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) < 2:
        print("usage: blender -b --factory-startup --python front_probe.py -- "
              "<asset.glb> <out_dir>")
        sys.exit(2)
    return argv[0], argv[1]


def _scene_reset():
    # --factory-startup still ships a default cube/light/camera; a probe shot
    # with a stranger's cube in frame is the corrupted-render class this repo
    # has already paid for. Empty the scene by data, not by ops.
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.lights,
                 bpy.data.cameras):
        for item in list(coll):
            coll.remove(item)


def _bbox_world():
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    from mathutils import Vector
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    return lo, hi


def main():
    asset, out_dir = _args()
    os.makedirs(out_dir, exist_ok=True)
    _scene_reset()
    ext = os.path.splitext(asset)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=asset)   # headless-safe (CLAUDE.md)
    else:
        print(f"front_probe: unsupported extension {ext} (glb/gltf only)")
        sys.exit(2)

    lo, hi = _bbox_world()
    cx, cy, cz = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    span = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    dist = span * 3.0

    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 32
    scn.render.resolution_x = scn.render.resolution_y = 800
    scn.render.film_transparent = False
    world = bpy.data.worlds.new("probe_world")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)
        bg.inputs[1].default_value = 1.0

    cam_data = bpy.data.cameras.new("probe_cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = span * 1.25
    cam_data.clip_end = dist * 4.0
    cam = bpy.data.objects.new("probe_cam", cam_data)
    scn.collection.objects.link(cam)
    scn.camera = cam

    # view name -> (location, euler XYZ). Default camera looks -Z; Rx(90)
    # brings the look to +Y, then Rz swings it to the cardinal.
    views = {
        "S": ((cx, cy - dist, cz), (math.pi / 2, 0.0, 0.0)),
        "E": ((cx + dist, cy, cz), (math.pi / 2, 0.0, math.pi / 2)),
        "N": ((cx, cy + dist, cz), (math.pi / 2, 0.0, math.pi)),
        "W": ((cx - dist, cy, cz), (math.pi / 2, 0.0, -math.pi / 2)),
    }
    for name, (loc, eul) in views.items():
        cam.location = loc
        cam.rotation_euler = eul
        scn.render.filepath = os.path.join(out_dir, f"front_{name}.png")
        bpy.ops.render.render(write_still=True)   # headless-safe op
        print(f"front_probe: wrote front_{name}.png")
    print(f"front_probe: bbox {[round(hi[i]-lo[i], 4) for i in range(3)]} m; "
          f"read the four elevations, then sign the azimuth into "
          f"qa/model-front-registry.json (S=-90 E=0 N=90 W=180, or null).")


if __name__ == "__main__":
    main()
