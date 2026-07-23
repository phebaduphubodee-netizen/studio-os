#!/usr/bin/env python3
"""id_mask.py — render an OBJECT-ID mask, pixel-aligned with a scene's beauty frame.

    blender -b <scene>.blend --python pipeline/scripts/id_mask.py -- <out.png> <substr> ...

Objects whose name CONTAINS any substring get a unique palette colour; everything else
renders black (id 0 = "not measured"). Writes <out>.png plus <out>.json = {id: name},
which `value_probe.py` consumes.

WHY A SECOND RENDER AND NOT A COMPOSITOR PASS. The IndexOB pass would ride along free,
but every non-EXR output path in Blender runs the scene's view transform, and this scene
is pinned to AgX — an id divided by 255 and pushed through a film curve is not an id any
more. A flat-emission pass at 1 sample with 0 bounces is 2.5 s on this machine and is
EXACT by construction, which is worth more than the seconds.

WHY IT IS SAFE TO RUN ON A DELIVERABLE .blend: it opens the file, mutates the in-memory
scene and never saves. It writes exactly one PNG and one JSON, both to the path given.

The mask is only as honest as its alignment: it renders the CAMERA AND RESOLUTION already
in the .blend and refuses to touch either. A mask from a different camera measures
nothing, so `value_probe` re-checks the frame size before it decodes anything.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_probe as _vp                    # palette codec — ONE definition, both halves


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _emission(name, srgb255):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = tuple(_srgb_to_linear(c / 255.0) for c in srgb255) + (1.0,)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
    return m


def build_mask(out_png, filters):
    targets = sorted((o for o in bpy.data.objects
                      if o.type == 'MESH' and any(f in o.name for f in filters)),
                     key=lambda o: o.name)
    if not targets:
        raise _vp.ProbeError(f"id_mask: no mesh object matches {filters!r} — a probe that "
                             f"measures nothing must say so, not render a black frame")
    if len(targets) > _vp.MAX_ID:
        raise _vp.ProbeError(f"id_mask: {len(targets)} objects match {filters!r} but the "
                             f"palette holds {_vp.MAX_ID}. Narrow the filter")

    void = _emission("idmask__void", (0, 0, 0))
    mats, names = {}, {}
    for i, ob in enumerate(targets, start=1):
        mats[ob.name] = _emission(f"idmask__{i}", _vp.id_to_srgb(i))
        names[i] = ob.name
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        ob.data.materials.clear()
        ob.data.materials.append(mats.get(ob.name, void))

    scn = bpy.context.scene
    w = scn.world or bpy.data.worlds.new("idmask__world")
    scn.world = w
    w.use_nodes = True
    w.node_tree.nodes.clear()
    bg = w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0, 0, 0, 1)
    bg.inputs["Strength"].default_value = 0.0
    w.node_tree.links.new(bg.outputs["Background"],
                          w.node_tree.nodes.new("ShaderNodeOutputWorld").inputs["Surface"])

    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 1
    scn.cycles.use_adaptive_sampling = False
    scn.cycles.use_denoising = False           # a denoiser INVENTS in-between colours
    scn.cycles.max_bounces = 0                 # emission only: no bounce can tint an id
    scn.cycles.transparent_max_bounces = 0
    scn.render.film_transparent = False
    # EXACT round-trip: no film curve, no look, no exposure, no gamma.
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.look = 'None'
    scn.view_settings.exposure = 0.0
    scn.view_settings.gamma = 1.0
    scn.render.filter_size = 0.01              # near-box: an anti-aliased silhouette blends
    #                                            two ids and belongs to neither
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_depth = '8'
    scn.render.filepath = out_png
    # CAMERA AND RESOLUTION ARE NOT TOUCHED — alignment with the beauty frame is the whole
    # contract, and a probe that re-solves its own camera measures a different picture.
    bpy.ops.render.render(write_still=True)

    # THE SIDECAR CARRIES A FINGERPRINT, NOT JUST NAMES. Frame SHAPE is not an alignment
    # check in this build: `build_room._res` is (2000, 1400) for every non-hero camera, so a
    # mask rendered from `west_vanity` decodes cleanly against the `eye` beauty frame and
    # mis-attributes every pixel while reading as evidence. The `source` block below pins
    # what the mask was actually rendered from, and value_probe RAISES when the beauty PNG
    # it is handed did not come from the same build.
    cam = scn.camera
    src = {
        "blend": os.path.splitext(os.path.basename(bpy.data.filepath))[0] or "<unsaved>",
        "camera": cam.name if cam else None,
        "matrix": [[round(v, 6) for v in row] for row in (cam.matrix_world if cam else [])],
        "lens": round(cam.data.lens, 4) if cam and cam.data.type == 'PERSP' else None,
        "shift": [round(cam.data.shift_x, 6), round(cam.data.shift_y, 6)] if cam else None,
        "res": [scn.render.resolution_x, scn.render.resolution_y,
                scn.render.resolution_percentage],
        "meshes": len([o for o in bpy.data.objects if o.type == 'MESH']),
    }
    with open(os.path.splitext(out_png)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump({"source": src, "ids": {str(k): v for k, v in names.items()}},
                  fh, indent=1)
    return names


if __name__ == "__main__":                     # pragma: no cover
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2:
        print("id_mask: usage -- <out.png> <name-substr> [<name-substr> ...]")
        sys.stdout.flush()
        os._exit(2)
    try:
        got = build_mask(argv[0], argv[1:])
    except BaseException as e:                 # headless Blender swallows and EXITS 0
        import traceback
        traceback.print_exc()
        print(f"ID MASK FAILED: {e}")
        sys.stdout.flush()
        os._exit(1)
    print(f"ID MASK OK {argv[0]} ({len(got)} objects)")
    sys.stdout.flush()
