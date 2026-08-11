"""map_census_mask.py — render a per-MATERIAL id mask, pixel-aligned with the
beauty frame (P2r-6's layer-2 half).

    called in-process by build_room._score_deliverable AFTER save(), or:
    blender -b <scene>.blend --python pipeline/scripts/map_census_mask.py -- <out.png>

WHY PER-MATERIAL AND NOT PER-OBJECT: the census question is "what share of the
VISIBLE FRAME carries image-mapped materials" (the 4.9% vs 50-66% gap SC-4
measured and nothing in the repo could print). Materials number ~46 in this
scene against 611 objects (palette holds 215), and the replacement is done PER
SLOT, so a multi-material object keeps its per-face attribution.

THE MUTATE-NEVER-SAVE LAW (id_mask.py's contract, kept): this module mutates
the in-memory scene — every slot swapped to a flat emission id — and never
saves. In-process use is only legal AFTER save(); build_room calls it from
_score_deliverable, which runs after both save() and render(). Camera and
resolution are NOT touched: alignment with the beauty frame is the contract.

id 0 stays reserved: a black pixel is "nothing was there" (background through
glass, void), never a measured material. Objects with no material get the
reserved name "(no material)" — a named surface in the shortfall list, not a
silent drop.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_probe as _vp


def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _emission(name, srgb255):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = tuple(
        _srgb_to_linear(c / 255.0) for c in srgb255) + (1.0,)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
    return m


NO_MATERIAL = "(no material)"


def _has_image(mat):
    if not (mat and mat.use_nodes):
        return False
    return any(nd.type == "TEX_IMAGE" for nd in mat.node_tree.nodes)


def build_material_mask(out_png):
    out_png, out_json = _vp.mask_paths(out_png)
    mesh_obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    mat_names = sorted({(s.material.name if s.material else NO_MATERIAL)
                        for o in mesh_obs for s in o.material_slots}
                       | {NO_MATERIAL for o in mesh_obs if not o.material_slots})
    if not mat_names:
        raise _vp.ProbeError("map_census_mask: no materials on any mesh — a census "
                             "of nothing must say so, not render a black frame")
    if len(mat_names) > _vp.MAX_ID:
        raise _vp.ProbeError(f"map_census_mask: {len(mat_names)} materials exceed "
                             f"the palette's {_vp.MAX_ID}")
    has_img = {}
    for o in mesh_obs:
        for s in o.material_slots:
            nm = s.material.name if s.material else NO_MATERIAL
            if nm not in has_img:
                has_img[nm] = _has_image(s.material)
    has_img.setdefault(NO_MATERIAL, False)

    ids = {i: nm for i, nm in enumerate(mat_names, start=1)}
    emis = {nm: _emission(f"census__{i}", _vp.id_to_srgb(i))
            for i, nm in ids.items()}
    for o in mesh_obs:
        if not o.material_slots:
            o.data.materials.append(emis[NO_MATERIAL])
            continue
        for s in o.material_slots:
            nm = s.material.name if s.material else NO_MATERIAL
            s.material = emis[nm]

    scn = bpy.context.scene
    w = scn.world or bpy.data.worlds.new("census__world")
    scn.world = w
    w.use_nodes = True
    w.node_tree.nodes.clear()
    bg = w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0, 0, 0, 1)
    bg.inputs["Strength"].default_value = 0.0
    w.node_tree.links.new(
        bg.outputs["Background"],
        w.node_tree.nodes.new("ShaderNodeOutputWorld").inputs["Surface"])
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 1
    scn.cycles.use_adaptive_sampling = False
    scn.cycles.use_denoising = False           # a denoiser INVENTS in-between colours
    scn.cycles.max_bounces = 0                 # emission only: no bounce can tint an id
    scn.cycles.transparent_max_bounces = 0
    scn.render.film_transparent = False
    scn.view_settings.view_transform = 'Standard'   # exact round-trip, no film curve
    scn.view_settings.look = 'None'
    scn.view_settings.exposure = 0.0
    scn.view_settings.gamma = 1.0
    scn.render.filter_size = 0.01              # near-box: AA blends two ids into neither
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_depth = '8'
    scn.render.filepath = out_png
    bpy.ops.render.render(write_still=True)

    cam = scn.camera
    src = {
        "blend": os.path.splitext(os.path.basename(bpy.data.filepath))[0] or "<unsaved>",
        "camera": cam.name if cam else None,
        "res": [scn.render.resolution_x, scn.render.resolution_y,
                scn.render.resolution_percentage],
        "materials": len(mat_names),
    }
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"schema": "matmask@1", "source": src,
                   "ids": {str(k): v for k, v in ids.items()},
                   "has_image": has_img}, fh, indent=1, ensure_ascii=False)
    print(f"MAT MASK OK {out_png} ({len(mat_names)} materials)")
    return ids


if __name__ == "__main__":                     # pragma: no cover
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        print("usage: blender -b scene.blend --python map_census_mask.py -- out.png")
        sys.exit(2)
    try:
        build_material_mask(argv[0])
    except _vp.ProbeError as e:
        print(f"MAT MASK FAILED: {e}")
        sys.stdout.flush()
        os._exit(1)
