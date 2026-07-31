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
    "grey_cartago_03":  (0.2664, 0.2489, 0.2317),
    "wood_floor":       (0.2189, 0.1185, 0.0557),
    "plastered_wall_03": (0.2495, 0.2061, 0.1679),
}

# Board-to-board / panel-to-panel tonal drift. The round-3 critic measured our
# floor at 1.9% variation between boards against the reference's 30.4% — every
# plank the identical tone, which is what makes a wood floor read as printed
# laminate. A large, anisotropic noise multiplied into the base colour gives
# neighbouring boards different values without touching the grain itself.
# (key -> (amplitude, noise scale, per-axis stretch))
TONE_NOISE = {
    "floor_oak":     (0.30, 2.2, (0.35, 1.0, 6.0)),
    "veneer_fascia": (0.16, 1.6, (0.5, 1.0, 3.0)),
    "veneer_pier":   (0.16, 1.6, (3.0, 1.0, 0.5)),
    "veneer_altar":  (0.16, 1.6, (3.0, 1.0, 0.5)),
}

# how hard each map's normal pushes; paint and stone are nearly flat in reality
NORMAL_STRENGTH = {"plastered_wall_03": 0.12, "marble_01": 0.15, "grey_cartago_03": 0.10}

# How much of the map's VARIATION each surface keeps (1.0 = the map as shot,
# 0.0 = flat). A map is evidence of how a material varies, not an instruction to
# wear that material's whole character: the CC0 wood is a WORN table, and at
# full strength it dresses fine cabinet veneer in knots and wear the target's
# millwork does not have. Painted plaster keeps almost none — a smooth painted
# wall really is nearly flat, and "add maps everywhere" would be the
# ground-truth study's lesson over-applied into a different wrong answer.
MAP_MIX = {
    "veneer_fascia": 0.90, "veneer_pier": 0.90, "veneer_altar": 0.90,
    "cavity": 0.40, "marble": 0.60, "floor_oak": 0.80, "paint_white": 0.06,
}

# GRAIN HAS A DIRECTION. The round-3 critic measured the reference fascia at
# 2.41 vertical/horizontal detail energy against our 1.57 — near-isotropic
# mottle, which is precisely why our veneer read as cast concrete rather than
# wood, and why the fascia and the altar measured as the SAME material (1.57 vs
# 1.54) when the delivered work uses two different veneers (2.41 vs 1.61).
# Box projection on object coords means a vertical face is textured by (x, z),
# so an anisotropic scale runs the grain along whichever axis is stretched:
# lengthwise on the rail, upright on the piers and the altar blocks.
MAP_ASPECT = {
    "veneer_fascia": (5.0, 1.0, 0.30),
    "veneer_pier":   (0.45, 1.0, 4.0),
    "veneer_altar":  (0.55, 1.0, 2.2),
    "cavity":        (0.30, 1.0, 5.0),
}

# name -> (linear albedo, roughness, metallic, map-set slug or None, map scale m)
PALETTE = {
    # wood_floor, not the worn table: it is the only set on disk whose grain is
    # LINEAR, which is the property that makes wood read as wood
    "veneer_fascia": ((0.24, 0.17, 0.11), 0.42, 0.0, "wood_floor", 1.7),
    "veneer_pier":  ((0.22, 0.16, 0.11), 0.42, 0.0, "wood_floor", 1.0),
    "veneer_altar": ((0.27, 0.22, 0.17), 0.45, 0.0, "wood_floor", 1.0),
    "cavity":       ((0.05, 0.04, 0.04), 0.70, 0.0, "wood_floor", 1.0),
    "lacquer_white": ((0.88, 0.88, 0.87), 0.20, 0.0, None, 0.0),
    # SCALE IS THE FIGURE. The critic's "small speckle" was not the stone, it was
    # me: scale is the size of ONE map pass in metres, so 8.0 showed the 1.4 m
    # slab a fifth of one tile, zoomed 5x past the figure the stone was shot at.
    # At ~1.9 the slab reads one full pass and the veining lands at its designed
    # size. (A candidate chosen instead on a large-figure SCORE turned out to be
    # a wall of stone TILES — the metric cannot tell veins from tile joints, and
    # I picked it without once opening the map. Look at the texture.)
    "marble":       ((0.77, 0.76, 0.75), 0.18, 0.0, "marble_01", 1.9),
    # the delivered inlay is pale champagne separating from the wood by VALUE,
    # not a hot yellow line: the critic measured ours 15x further from its own
    # veneer in R-B than the reference's
    "brass":        ((0.74, 0.70, 0.60), 0.30, 1.0, None, 0.0),
    "floor_oak":    ((0.72, 0.60, 0.44), 0.40, 0.0, "wood_floor", 2.0),
    # a painted wall must be the LEAST chromatic neutral in the room; ours was
    # 1.7x more chromatic than the stone where the reference is 0.53x
    "paint_white":  ((0.80, 0.80, 0.80), 0.65, 0.0, "plastered_wall_03", 4.0),
    # the concealed LED behind the slab (owner 2026-07-31) — an emitter, so its
    # albedo entry is the emission colour and EMISSION carries the strength
    "halo_led":     ((1.00, 0.955, 0.90), 0.50, 0.0, None, 0.0),
}

# emission strength (W/m^2-ish) for the materials that are light sources
EMISSION = {"halo_led": 16.0}

# A bookmatched slab is the one thing the CC0 library does not have: every
# marble set on it is a TILED floor, and both candidates put tile joints across
# the middle of the panel. Veining is therefore generated — continuous, non
# repeating, and controllable — as noise-distorted bands, which is what large
# sweeping figure actually is. (key -> dict of knobs)
PROCEDURAL = {
    # two vein families: a few big sweeping ones, and a finer web inside them
    "marble": {"scale": 2.6, "detail": 10.0, "roughness": 0.62, "distortion": 1.4,
               "vein_lo": 0.470, "vein_hi": 0.512, "vein_dark": 0.55,
               "fine_scale": 9.0, "fine_lo": 0.487, "fine_hi": 0.503,
               "fine_dark": 0.80, "stretch": (1.0, 1.0, 0.45)},
}


def _build_veined_stone(nt, bsdf, albedo, k):
    """Marble veining as THIN SINUOUS LINES, not clouds.

    A wave texture under heavy distortion makes soft blobs — it read as smoke.
    What produces veins is a noise field passed through a NARROW window: only
    where the field crosses a thin band does a vein appear, so the veins come
    out fine, branching and continuous, and an anisotropic coordinate stretch
    sweeps them diagonally the way a bookmatched slab runs.

    Grey and achromatic on purpose: the round-3 critic measured the delivered
    slab's veins at +0.2 R-B (pure value, no colour) against our image-mapped
    stone's +5.4 rusty veins."""
    texco = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = tuple(1.0 / a for a in k["stretch"])
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, 0.55)
    nt.links.new(texco.outputs["Object"], mapping.inputs["Vector"])

    def vein(scale, lo, hi, dark, on_top):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = k["detail"]
        n.inputs["Roughness"].default_value = k["roughness"]
        n.inputs["Distortion"].default_value = k["distortion"]
        nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
        r = nt.nodes.new("ShaderNodeValToRGB")
        r.color_ramp.interpolation = "B_SPLINE"
        e = r.color_ramp.elements
        e[0].position, e[0].color = lo, (1.0, 1.0, 1.0, 1.0)
        e[1].position, e[1].color = (lo + hi) / 2, (0.0, 0.0, 0.0, 1.0)
        e.new(hi).color = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
        mixn = nt.nodes.new("ShaderNodeMixRGB")
        mixn.blend_type = "MIX"
        mixn.inputs["Color2"].default_value = (*[c * dark for c in albedo], 1.0)
        if on_top is None:
            mixn.inputs["Color1"].default_value = (*albedo, 1.0)
        else:
            nt.links.new(on_top, mixn.inputs["Color1"])
        # ramp is white OFF-vein, black ON-vein -> invert into the mix factor
        inv = nt.nodes.new("ShaderNodeInvert")
        nt.links.new(r.outputs["Color"], inv.inputs["Color"])
        nt.links.new(inv.outputs["Color"], mixn.inputs["Fac"])
        return mixn.outputs["Color"]

    big = vein(k["scale"], k["vein_lo"], k["vein_hi"], k["vein_dark"], None)
    fine = vein(k["fine_scale"], k["fine_lo"], k["fine_hi"], k["fine_dark"], big)
    nt.links.new(fine, bsdf.inputs["Base Color"])


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
    if n.startswith("halo_"):
        return "halo_led"
    if n.startswith("brass_"):
        return "brass"
    if n.startswith("header_p"):
        return "veneer_fascia"          # grain runs lengthwise along the rail
    if n.startswith("tower_"):
        if n.endswith("_back"):
            return "cavity"
        return "veneer_pier"            # grain runs upright on the piers
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
        if key in EMISSION:
            for nm_ in ("Emission Color", "Emission"):
                if nm_ in bsdf.inputs:
                    bsdf.inputs[nm_].default_value = (*albedo, 1.0)
                    break
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = EMISSION[key]

        if key in PROCEDURAL:
            _build_veined_stone(nt, bsdf, albedo, PROCEDURAL[key])
            made[key] = mat
            continue

        maps = map_paths(slug)
        if maps:
            # box projection on OBJECT coords: no UVs exist on these meshes
            texco = nt.nodes.new("ShaderNodeTexCoord")
            mapping = nt.nodes.new("ShaderNodeMapping")
            asp = MAP_ASPECT.get(key, (1.0, 1.0, 1.0))
            mapping.inputs["Scale"].default_value = tuple(1.0 / (scale * a) for a in asp)
            nt.links.new(texco.outputs["Object"], mapping.inputs["Vector"])

            def img(path, non_colour):
                node = nt.nodes.new("ShaderNodeTexImage")
                node.image = bpy.data.images.load(path, check_existing=True)
                node.projection = "BOX"
                node.projection_blend = 0.0 if key == "marble" else 0.25
                if non_colour:
                    node.image.colorspace_settings.name = "Non-Color"
                nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
                return node

            if "base" in maps:
                # DESATURATE the map to its own luminance first, then tint by
                # the sampled albedo. Per-CHANNEL normalisation was the earlier
                # design and it produced the blue specks the round-3 critic
                # found on the two hero surfaces: the wood map's blue mean is
                # 0.008, so dividing by it applied ~14x gain to a channel that
                # holds almost nothing but compression noise. A scalar (the
                # luminance mean) cannot do that, and it also keeps the map to
                # its real job — the map carries the GRAIN, the sample carries
                # the COLOUR.
                mean = MAP_MEAN.get(slug, (1.0, 1.0, 1.0))
                lum_mean = 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]
                base_img = img(maps["base"], False)
                grey = nt.nodes.new("ShaderNodeMixRGB")
                grey.blend_type = "MIX"
                grey.inputs["Fac"].default_value = 1.0    # fully desaturated
                nt.links.new(base_img.outputs["Color"], grey.inputs["Color1"])
                bw = nt.nodes.new("ShaderNodeRGBToBW")
                nt.links.new(base_img.outputs["Color"], bw.inputs["Color"])
                nt.links.new(bw.outputs["Val"], grey.inputs["Color2"])

                gain = tuple(a / max(lum_mean, 1e-4) for a in albedo)
                mix = nt.nodes.new("ShaderNodeMixRGB")
                mix.blend_type = "MULTIPLY"
                mix.inputs["Fac"].default_value = 1.0
                mix.inputs["Color2"].default_value = (*gain, 1.0)
                nt.links.new(grey.outputs["Color"], mix.inputs["Color1"])
                # keep only part of the map's variation, blending back to flat
                damp = nt.nodes.new("ShaderNodeMixRGB")
                damp.blend_type = "MIX"
                damp.inputs["Fac"].default_value = MAP_MIX.get(key, 1.0)
                damp.inputs["Color1"].default_value = (*albedo, 1.0)
                nt.links.new(mix.outputs["Color"], damp.inputs["Color2"])
                out_col = damp.outputs["Color"]

                if key in TONE_NOISE:
                    amp, nscale, nasp = TONE_NOISE[key]
                    nmap = nt.nodes.new("ShaderNodeMapping")
                    nmap.inputs["Scale"].default_value = tuple(
                        1.0 / (nscale * a) for a in nasp)
                    nt.links.new(texco.outputs["Object"], nmap.inputs["Vector"])
                    noise = nt.nodes.new("ShaderNodeTexNoise")
                    noise.inputs["Detail"].default_value = 1.0
                    noise.inputs["Scale"].default_value = 1.0
                    nt.links.new(nmap.outputs["Vector"], noise.inputs["Vector"])
                    # map noise 0..1 onto (1-amp/2 .. 1+amp/2) and multiply
                    rng = nt.nodes.new("ShaderNodeMapRange")
                    rng.inputs["To Min"].default_value = 1.0 - amp / 2
                    rng.inputs["To Max"].default_value = 1.0 + amp / 2
                    nt.links.new(noise.outputs["Fac"], rng.inputs["Value"])
                    tone = nt.nodes.new("ShaderNodeMixRGB")
                    tone.blend_type = "MULTIPLY"
                    tone.inputs["Fac"].default_value = 1.0
                    nt.links.new(out_col, tone.inputs["Color1"])
                    nt.links.new(rng.outputs["Result"], tone.inputs["Color2"])
                    out_col = tone.outputs["Color"]

                nt.links.new(out_col, bsdf.inputs["Base Color"])
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
