"""trn001_materials.py — TRN-001 round 3: material identity for the blockout.

Two layers, split so the decisions are testable without Blender (LAYER LAW):
  * PURE — which material each mass wears (`material_for`) and what that
    material IS (`PALETTE`): linear albedo, roughness, metallic, and which CC0
    map set dresses it. Importable under plain python.
  * bpy — `build_materials()` turns that table into Principled node graphs,
    projecting each map set by BOX PROJECTION on object coordinates, because
    these meshes carry no UVs by construction (authored quads, no unwrap).

Albedos were SAMPLED from the target, not chosen: patches on flat unshadowed
areas were read in linear space and divided by the white wall's own reading
(taken as ~0.80 albedo) to back out the lighting the target was rendered under.
That makes the palette a measurement with a stated assumption, not a taste.

The 2026-07-30 ground-truth study measured our whole studio at 95% image-free
materials against 50-66% in every pro file, and found our fabric compensating
with flat sheen where the pros cap at 0.4 and let maps do the work. This module
is that lesson applied: every material that has a real map set gets one.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CC0 = os.path.join(REPO, "assets", "shared", "cc0", "textures")

SHEEN_CEILING = 0.4          # ground-truth study: pro files never run higher

# Linear MEAN of each CC0 diffuse map, measured once with PIL outside Blender.
# Without this the tint multiply double-darkens: a map already carries a mid
# tone, so multiplying it by an albedo lands at albedo x mean, not albedo.
# Normalising by the mean makes the map contribute VARIATION and the sampled
# albedo contribute IDENTITY — which is the whole point of the split.
MAP_MEAN = {
    "wood_table_worn":  (0.0891, 0.0296, 0.0080),
    "marble_01":        (0.4493, 0.3397, 0.1936),
    "wood_floor":       (0.2189, 0.1185, 0.0557),
    "plastered_wall_03": (0.2495, 0.2061, 0.1679),
}

# how hard each map's normal pushes; paint and stone are nearly flat in reality
NORMAL_STRENGTH = {"plastered_wall_03": 0.12, "marble_01": 0.15}

# How much of the map's VARIATION each surface keeps (1.0 = the map as shot,
# 0.0 = flat). A map is evidence of how a material varies, not an instruction to
# wear that material's whole character: the CC0 wood is a WORN table, and at
# full strength it dresses fine cabinet veneer in knots and wear the target's
# millwork does not have. Painted plaster keeps almost none — a smooth painted
# wall really is nearly flat, and "add maps everywhere" would be the
# ground-truth study's lesson over-applied into a different wrong answer.
MAP_MIX = {
    "veneer_dark": 0.45, "veneer_altar": 0.55, "cavity": 0.30,
    "marble": 0.80, "floor_oak": 0.70, "paint_white": 0.12,
}

# name -> (linear albedo, roughness, metallic, map-set slug or None, map scale m)
PALETTE = {
    "veneer_dark":  ((0.24, 0.17, 0.11), 0.42, 0.0, "wood_table_worn", 1.6),
    "veneer_altar": ((0.27, 0.22, 0.17), 0.45, 0.0, "wood_table_worn", 1.1),
    "cavity":       ((0.05, 0.04, 0.04), 0.70, 0.0, "wood_table_worn", 1.6),
    "lacquer_white": ((0.85, 0.84, 0.83), 0.22, 0.0, None, 0.0),
    # 8 m so ONE pass of the stone covers the whole slab: the target is a single
    # bookmatched panel, and a tiling repeat reads as travertine tiles instead
    "marble":       ((0.77, 0.75, 0.73), 0.18, 0.0, "marble_01", 8.0),
    "brass":        ((0.72, 0.55, 0.26), 0.28, 1.0, None, 0.0),
    "floor_oak":    ((0.72, 0.60, 0.44), 0.40, 0.0, "wood_floor", 2.0),
    "paint_white":  ((0.80, 0.79, 0.78), 0.65, 0.0, "plastered_wall_03", 4.0),
}


def material_for(mass_name):
    """Mass name (from trn001_geom.masses) -> palette key. PURE.

    Deliberately explicit rather than clever: a mis-routed prefix would dress a
    whole element in the wrong material, and that is the kind of error a render
    hides behind plausibility."""
    n = mass_name
    if n == "floor":
        return "floor_oak"
    if n in ("back_wall", "ceiling", "side_wall_L"):
        return "paint_white"
    if n == "marble":
        return "marble"
    if n.startswith("brass_"):
        return "brass"
    if n.startswith("header_p"):
        return "veneer_dark"
    if n.startswith("tower_"):
        if n.endswith("_back") or "_shelf" in n:
            return "cavity" if n.endswith("_back") else "veneer_dark"
        return "veneer_dark"
    if n.startswith("plinth"):
        return "lacquer_white"
    if n in ("step", "centre_box") or n.startswith("pedestal_"):
        return "veneer_altar"
    return "paint_white"


def map_paths(slug):
    """{channel: path} for a CC0 set, only the channels actually on disk. PURE."""
    if not slug:
        return {}
    base = os.path.join(CC0, slug)
    out = {}
    for chan, needle in (("base", "Diffuse"), ("rough", "Rough"), ("normal", "nor_gl")):
        for res in ("2k", "1k"):
            p = os.path.join(base, f"{slug}_{needle}_{res}.jpg")
            if os.path.exists(p):
                out[chan] = p
                break
    return out


def palette_report():
    """One line per material, saying whether it is map-dressed or flat — the
    number the ground-truth study says to watch."""
    rows, dressed = [], 0
    for key, (_, _, _, slug, _) in sorted(PALETTE.items()):
        m = map_paths(slug)
        dressed += 1 if m else 0
        rows.append(f"  {key:14s} maps={','.join(sorted(m)) or 'NONE (analytic)'}")
    rows.append(f"  -> {dressed}/{len(PALETTE)} materials carry image maps "
                f"({100 * dressed // len(PALETTE)}%; pro files measure 50-66%)")
    return "\n".join(rows)


# ------------------------------------------------------------------ bpy side --

def build_materials():
    """Create every palette material as a Blender node graph. Returns
    {key: bpy Material}. Only called from inside Blender."""
    import bpy

    made = {}
    for key, (albedo, rough, metal, slug, scale) in PALETTE.items():
        mat = bpy.data.materials.new(f"M_TRN001_{key}")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*albedo, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if "Sheen Weight" in bsdf.inputs:
            bsdf.inputs["Sheen Weight"].default_value = min(
                SHEEN_CEILING, bsdf.inputs["Sheen Weight"].default_value)

        maps = map_paths(slug)
        if maps:
            # box projection on OBJECT coords: no UVs exist on these meshes
            texco = nt.nodes.new("ShaderNodeTexCoord")
            mapping = nt.nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (1.0 / scale,) * 3
            nt.links.new(texco.outputs["Object"], mapping.inputs["Vector"])

            def img(path, non_colour):
                node = nt.nodes.new("ShaderNodeTexImage")
                node.image = bpy.data.images.load(path, check_existing=True)
                node.projection = "BOX"
                node.projection_blend = 0.25
                if non_colour:
                    node.image.colorspace_settings.name = "Non-Color"
                nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
                return node

            if "base" in maps:
                # the map carries the GRAIN, the sampled albedo carries the
                # IDENTITY: divide the map by its own measured mean so the
                # product lands on the albedo instead of albedo x mean
                mean = MAP_MEAN.get(slug, (1.0, 1.0, 1.0))
                gain = tuple(a / max(m, 1e-4) for a, m in zip(albedo, mean))
                mix = nt.nodes.new("ShaderNodeMixRGB")
                mix.blend_type = "MULTIPLY"
                mix.inputs["Fac"].default_value = 1.0
                mix.inputs["Color2"].default_value = (*gain, 1.0)
                nt.links.new(img(maps["base"], False).outputs["Color"], mix.inputs["Color1"])
                # keep only part of the map's variation, blending back to flat
                damp = nt.nodes.new("ShaderNodeMixRGB")
                damp.blend_type = "MIX"
                damp.inputs["Fac"].default_value = MAP_MIX.get(key, 1.0)
                damp.inputs["Color1"].default_value = (*albedo, 1.0)
                nt.links.new(mix.outputs["Color"], damp.inputs["Color2"])
                nt.links.new(damp.outputs["Color"], bsdf.inputs["Base Color"])
            if "rough" in maps:
                nt.links.new(img(maps["rough"], True).outputs["Color"],
                             bsdf.inputs["Roughness"])
            if "normal" in maps:
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = NORMAL_STRENGTH.get(slug, 0.8)
                nt.links.new(img(maps["normal"], True).outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        made[key] = mat
    return made
