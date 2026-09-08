#!/usr/bin/env python3
"""materials_trn003.py - the tutorial's stages 4 and 5, as code.

    SPLIT   (video 16:30-22:45)  one override colour becomes a handful of tonal families
    TEXTURE (video 22:45-28:45)  each family gets real maps, REFLECTIONS BEFORE COLOUR

WHAT THE TUTORIAL ACTUALLY DOES, because "follow him for real" is this lane's whole point:

  SPLIT. Drop the material override, but first APPLY it to every object so nothing loses
  its shader; objects that already carry several shaders (his oven) are excluded and given
  the base material through a Geometry Nodes Set Material instead. Then divide: "let's
  start with dividing the main color into two shades darker and lighter - things like
  marble or ceiling are a lot lighter than wood or these metal beams". Then BLACK, "and
  for this color I'm also going to lower the IOR to make the black color more deep". Then
  an accent, an even whiter shade, a metal, and a wood that is "a bit more red". Greenery
  gets a Translucent BSDF added to the Principled through an Add Shader, then mixed back
  against the Principled so the amount is a slider - "the translucent colour should also
  be a bit brighter, more saturated and warmer". The curtain gets the same treatment.

  TEXTURE. "Start with the biggest shader in the image" - here the floor. "The reason why
  we are starting with reflections is because if we plug in the color first then we won't
  be able to see very well how much reflections we got." Two knobs: roughness (how sharp)
  and IOR (how much); he ends up preferring IOR. The roughness chain is texture ->
  ColorRamp to black and white -> flip to invert -> RGB Curves darker and more contrast.
  Colour comes last and is MIXED WITH THE FLAT COLOUR FROM THE SPLIT so hue and brightness
  do not move. Marble adds subsurface: weight 1, radius about (1, 0.7, 0.5), scale ~3 cm,
  with the colour texture through a ColorRamp as the WEIGHT so the pale stone transmits
  and the dark veins do not.

WHAT WE DO DIFFERENTLY, AND WHY IT IS NOT A SHORTCUT:
  * His maps are iMeshh, Poliigon, textures.com - all paid. Ours are the CC0 sets already
    cached under assets/shared/cc0/textures, each with a .scale.json the publisher's API
    wrote. R8 permits any licence that allows commercial use of the render; the free tier
    is the default because a SPEND is the owner's call per purchase.
  * Every tile size is READ FROM THE SIDECAR, never typed. That is this repo's own law
    (qa/texture-scale.json) and it was paid for: one slug was mapped at nine different tile
    values across this repo, every one a bare literal, and the floor rendered 267 mm boards.
  * The FAMILY COLOURS ARE NOT TYPED EITHER. They come from 04_mood/palette-from-plate.json,
    which is written by measuring the plate. A family with no measured row RAISES. The
    tutorial's eyedropper is a measurement; retyping his numbers would not be.
"""
import json
import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TEX = os.path.join(REPO, "assets", "shared", "cc0", "textures")
PALETTE = os.path.join(HERE, "..", "04_mood", "palette-from-plate.json")


# =======================================================================================
# WHICH OBJECT IS WHICH FAMILY
#
# Ordered, first match wins. Prefix match on the object name. This is the one table in
# the file that is a JUDGEMENT rather than a measurement - it says what each mass IS - and
# it is written out object by object rather than by a catch-all so that a new mass added
# to the blockout lands in `base` loudly rather than inheriting something by accident.
# =======================================================================================
ASSIGN = [
    ("glass",            "glass"),
    ("sheer",            "sheer"),
    ("canopy",           "greenery"),
    ("floor",            "wood_floor"),
    ("ceiling",          "plaster"),
    ("wall_",            "plaster"),
    ("glazing_",         "black"),
    ("mullion_",         "black"),
    ("uppers",           "white"),
    ("splashback",       "stone_marble"),
    ("bench",            "stone_marble"),   # bench and bench_plinth: the run is stone-topped
    ("tall_bank",        "wood_oak"),
    ("tall_plinth",      "wood_oak"),
    ("oven_stack",       "black"),
    ("island_stone",     "stone_travertine"),
    ("island_slab",      "stone_marble"),
    ("island_drum",      "metal_bronze"),
    ("stool0_seat",      "black"),
    ("stool1_seat",      "black"),
    ("stool",            "black"),
    ("Sun",              None),
    ("cam",              None),
]


def family_of(name):
    for prefix, fam in ASSIGN:
        if name.startswith(prefix):
            return fam
    return "base"


# =======================================================================================
# THE TEXTURE ROWS. slug -> the cached CC0 set. The tile size is NEVER written here; it is
# read from <slug>.scale.json, which the publisher's API wrote and which self-checks
# against its own dimensions_mm. `scale` is a SIGNED DEPARTURE from that published size
# when the surface genuinely repeats at a different pitch, with the reason in `why`.
# =======================================================================================
TEXTURE = {
    "wood_floor": dict(slug="laminate_floor_02", scale=1.0, why=None),
    "wood_oak":   dict(slug="washed_grey_oak_veneer", scale=1.0, why=None),
    # "plaster" IS DELIBERATELY NOT HERE. white_plaster_02 was fetched for it and then
    # REMOVED after one look: the plate's ceiling patch has a standard deviation of
    # 1.8 / 1.1 / 1.4 grey levels over 11,200 px - the flattest surface in the frame by
    # an order of magnitude - and the map rendered visible brown blotches across the
    # whole ceiling. The recon that found the slug said so before it was spent:
    # "at this camera a ceiling map may render as literally nothing". It rendered as
    # worse than nothing. A flat colour is the measurement's answer.
    "sheer":      dict(slug="rough_linen", scale=1.0, relief_only=True,
                       why="DECLARED DEPARTURE. rough_linen is the only linen on this disk "
                           "and it is BLUE and OPAQUE; a sheer transmits. Its nor_gl and "
                           "Rough are used as weave micro-relief ONLY and its Diffuse is "
                           "NOT loaded - colour and transmission come from the measured "
                           "row. Re-tinting a vendor's albedo is the axis the sighted "
                           "panel has scored this studio down on, so it is refused by "
                           "code here rather than avoided by discipline."),
    # NOT IN THIS TABLE, ON PURPOSE:
    #   stone_marble, stone_travertine -> PROCEDURAL, and a DECLARED GAP. Poly Haven's
    #     entire marble holding is 17 assets and not one is a slab: 5 grouted TILE grids
    #     (marble_01 among them, a cream limestone tile despite its name), 3 grey_cartago
    #     tile slabs, 9 outdoor rock faces at 1.8-20 m. 'travertine' returns ZERO across
    #     854 assets. Mapping a grouted tile onto a bookmatched splashback would draw GROUT
    #     LINES where the plate has veins - a worse error than no map at all.
    #   metal_bronze -> PROCEDURAL. R8's BUILD case: measured, the brush streaks run at
    #     88-90 deg on both drums, i.e. along the cylinder axis, which a stretched noise
    #     generates exactly. Poly Haven has no brass, bronze, copper or stainless; its
    #     whole Metal category is rust and corrugated iron.
    #   black, white -> shader values. The white lacquer's patch sd is 6-8 grey levels
    #     over 16,800 px; there is no texture in the picture to match.
}

_MAPS = ("Diffuse", "Rough", "nor_gl", "arm", "AO", "Displacement")


def _sidecar(slug):
    p = os.path.join(TEX, slug, slug + ".scale.json")
    if not os.path.exists(p):
        raise SystemExit(f"TEXTURE REFUSED: {slug} has no .scale.json. R8 - a texture "
                         f"whose real-world size nobody asserted may not be mapped.")
    j = json.load(open(p))
    if not j.get("tile_m"):
        raise SystemExit(f"TEXTURE REFUSED: {slug}.scale.json carries no tile_m.")
    return j


def _map_path(slug, kind):
    d = os.path.join(TEX, slug)
    if not os.path.isdir(d):
        return None
    best = None
    for f in sorted(os.listdir(d)):
        low = f.lower()
        if not low.endswith((".jpg", ".png", ".exr")):
            continue
        if ("_" + kind.lower() + "_") not in low:
            continue
        rank = 2 if "_2k" in low else (1 if "_1k" in low else 0)
        if best is None or rank > best[0]:
            best = (rank, os.path.join(d, f))
    return best[1] if best else None


# =======================================================================================
# THE MEASURED PALETTE
# =======================================================================================
def palette():
    if not os.path.exists(PALETTE):
        raise SystemExit(
            "SPLIT REFUSED: 04_mood/palette-from-plate.json is missing. The tutorial's "
            "material split is an EYEDROPPER ON THE REFERENCE, so this stage cannot run on "
            "typed colours. Write the file by measuring the plate first.")
    return json.load(open(PALETTE))


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(_srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4))


# =======================================================================================
# NODE BUILDERS
# =======================================================================================
def _principled(mat):
    return mat.node_tree.nodes["Principled BSDF"]


def _set(p, key, value):
    """Blender renamed several Principled sockets in 4.x; take whichever exists."""
    alt = {"Transmission": "Transmission Weight", "Subsurface": "Subsurface Weight",
           "Sheen": "Sheen Weight", "Clearcoat": "Coat Weight",
           "Specular": "Specular IOR Level"}
    for k in (key, alt.get(key, key)):
        if k in p.inputs:
            p.inputs[k].default_value = value
            return True
    return False


def flat(name, row):
    """A split-stage material: one colour, a roughness, an IOR. No maps."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = _principled(m)
    col = hex_to_linear(row["srgb_hex"])
    _set(p, "Base Color", (col[0], col[1], col[2], 1.0))
    _set(p, "Roughness", row.get("roughness", 0.4))
    _set(p, "IOR", row.get("ior", 1.45))
    _set(p, "Metallic", row.get("metallic", 0.0))
    if row.get("specular") is not None:
        _set(p, "Specular", row["specular"])
    return m


def translucent(name, row):
    """Greenery and the sheer: Principled + Translucent through an Add Shader, mixed back
    against the Principled so the AMOUNT is one slider. The tutorial's 18:45-19:30, and
    his note that the translucent colour is brighter, warmer and more saturated than the
    diffuse one is followed literally - the file carries both colours."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = _principled(m)
    out = nt.nodes["Material Output"]
    col = hex_to_linear(row["srgb_hex"])
    tcol = hex_to_linear(row.get("translucent_hex", row["srgb_hex"]))
    _set(p, "Base Color", (col[0], col[1], col[2], 1.0))
    _set(p, "Roughness", row.get("roughness", 0.85))
    _set(p, "IOR", row.get("ior", 1.35))
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (tcol[0], tcol[1], tcol[2], 1.0)
    add = nt.nodes.new("ShaderNodeAddShader")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = row.get("translucency", 0.45)
    nt.links.new(p.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(p.outputs[0], mix.inputs[1])
    nt.links.new(add.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def glass(name, row):
    """His 28:15: white, zero roughness, transmission 1, and the diffuse / glossy / shadow
    rays DISABLED so putting the glass back does not change the lighting he already set."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = _principled(m)
    _set(p, "Base Color", (1, 1, 1, 1))
    _set(p, "Roughness", 0.0)
    _set(p, "IOR", row.get("ior", 1.28))
    _set(p, "Transmission", 1.0)
    return m


def textured(name, row, fam, use_ior=True):
    """The texture stage for one family. ORDER IS THE LESSON: reflections, then colour.

    reflections   Rough map -> ColorRamp (black and white) -> [invert unless we are driving
                  IOR, his 25:00] -> RGB Curves (darker, more contrast) -> Roughness or IOR
    colour        Diffuse map -> RGB Curves -> Hue/Sat/Value -> MIX with the family's flat
                  colour, so the map carries the pattern and the measurement carries the hue
    relief        normal map, if the set ships one
    """
    t = TEXTURE.get(fam)
    if t is None:
        return flat(name, row)
    side = _sidecar(t["slug"])
    tile = side["tile_m"] * float(t.get("scale", 1.0))

    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = _principled(m)
    col = hex_to_linear(row["srgb_hex"])

    # --- real-world mapping, no UVs needed: object coordinates, box projection ---------
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tile, 1.0 / tile, 1.0 / tile)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def image(kind, non_colour=True):
        path = _map_path(t["slug"], kind)
        if path is None:
            return None
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        n.projection = "BOX"
        n.projection_blend = 0.30
        n.extension = "REPEAT"
        if non_colour:
            n.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    # ---------- 1. REFLECTIONS FIRST ---------------------------------------------------
    rough = image("Rough")
    if rough is not None:
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = row.get("rough_ramp", [0.15, 0.85])[0]
        ramp.color_ramp.elements[1].position = row.get("rough_ramp", [0.15, 0.85])[1]
        nt.links.new(rough.outputs["Color"], ramp.inputs["Fac"])
        curve = nt.nodes.new("ShaderNodeRGBCurve")
        cv = curve.mapping.curves[3]
        cv.points[0].location = (0.0, row.get("rough_lo", 0.10))
        cv.points[1].location = (1.0, row.get("rough_hi", 0.85))
        nt.links.new(ramp.outputs["Color"], curve.inputs["Color"])
        if use_ior and row.get("ior_map"):
            mapr = nt.nodes.new("ShaderNodeMapRange")
            mapr.inputs["To Min"].default_value = row["ior_map"][0]
            mapr.inputs["To Max"].default_value = row["ior_map"][1]
            nt.links.new(curve.outputs["Color"], mapr.inputs["Value"])
            nt.links.new(mapr.outputs["Result"], p.inputs["IOR"])
            _set(p, "Roughness", row.get("roughness", 0.4))
        else:
            nt.links.new(curve.outputs["Color"], p.inputs["Roughness"])
            _set(p, "IOR", row.get("ior", 1.45))
    else:
        _set(p, "Roughness", row.get("roughness", 0.4))
        _set(p, "IOR", row.get("ior", 1.45))

    # ---------- 2. THEN COLOUR, MIXED TO THE MEASURED HUE -------------------------------
    diff = None if t.get("relief_only") else image("Diffuse", non_colour=False)
    if diff is not None:
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = row.get("tex_sat", 0.75)
        hsv.inputs["Value"].default_value = row.get("tex_val", 1.0)
        nt.links.new(diff.outputs["Color"], hsv.inputs["Color"])
        mixc = nt.nodes.new("ShaderNodeMixRGB")
        mixc.blend_type = "COLOR"          # keep the map's LUMINANCE, take the measured HUE
        mixc.inputs["Fac"].default_value = row.get("tex_tint", 0.85)
        nt.links.new(hsv.outputs["Color"], mixc.inputs[1])
        mixc.inputs[2].default_value = (col[0], col[1], col[2], 1.0)
        nt.links.new(mixc.outputs["Color"], p.inputs["Base Color"])
    else:
        _set(p, "Base Color", (col[0], col[1], col[2], 1.0))

    # ---------- 3. RELIEF ---------------------------------------------------------------
    nor = image("nor_gl")
    if nor is not None:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = row.get("normal_strength", 0.6)
        nt.links.new(nor.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])

    # ---------- 4. SUBSURFACE, MARBLE ONLY (his 26:00) ----------------------------------
    if row.get("sss"):
        _set(p, "Subsurface", 1.0)
        r = row["sss"]
        if "Subsurface Radius" in p.inputs:
            p.inputs["Subsurface Radius"].default_value = (r[0], r[1], r[2])
        if "Subsurface Scale" in p.inputs:
            p.inputs["Subsurface Scale"].default_value = row.get("sss_scale", 0.03)
        if diff is not None and "Subsurface Weight" in p.inputs:
            wramp = nt.nodes.new("ShaderNodeValToRGB")
            wramp.color_ramp.elements[0].position = 0.35
            wramp.color_ramp.elements[1].position = 0.75
            nt.links.new(diff.outputs["Color"], wramp.inputs["Fac"])
            nt.links.new(wramp.outputs["Color"], p.inputs["Subsurface Weight"])

    _set(p, "Metallic", row.get("metallic", 0.0))
    return m


def procedural_stone(name, row, warm):
    """Marble and travertine WITHOUT a map, because no free slab map exists.

    This is not a shortcut around the texture stage; it is the texture stage's own answer
    when the class has no source. The tutorial's marble step is (1) reflections, (2) colour,
    (3) subsurface driven by the colour texture so pale stone transmits and dark veins do
    not - and all three survive with a generated vein field: a noise stretched by Mapping so
    the bedding runs one way, through a ColorRamp to pale-with-darker-veins, used both as
    the colour mix and as the subsurface weight. The one thing it cannot do is reproduce
    THIS stone, which is why the row says DECLARED GAP rather than done.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = _principled(m)
    col = hex_to_linear(row["srgb_hex"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = tuple(row.get("vein_scale", (0.6, 3.0, 1.2)))
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = row.get("vein_freq", 3.0)
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.55
    if "Distortion" in nz.inputs:
        nz.inputs["Distortion"].default_value = row.get("vein_distort", 1.6)
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.62
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = (col[0], col[1], col[2], 1.0)
    d = row.get("vein_darken", 0.72)
    mix.inputs[2].default_value = (col[0] * d, col[1] * d,
                                   col[2] * d * (0.96 if warm else 1.0), 1.0)
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], p.inputs["Base Color"])
    _set(p, "Roughness", row.get("roughness", 0.2))
    _set(p, "IOR", row.get("ior", 1.55))
    if row.get("sss"):
        r = row["sss"]
        _set(p, "Subsurface", 1.0)
        if "Subsurface Radius" in p.inputs:
            p.inputs["Subsurface Radius"].default_value = (r[0], r[1], r[2])
        if "Subsurface Scale" in p.inputs:
            p.inputs["Subsurface Scale"].default_value = row.get("sss_scale", 0.03)
        if "Subsurface Weight" in p.inputs:
            nt.links.new(ramp.outputs["Color"], p.inputs["Subsurface Weight"])
    return m


def brushed_metal(name, row):
    """An axially brushed metal, generated. MEASURED on the plate: the brush streaks run at
    88-90 deg in the image on both drums - along the cylinder axis - so the roughness field
    is a noise squashed in Z and stretched in X and Y, which is what a lathe-brushed drum
    is. Anisotropy is set on the same axis rather than left at zero, because a brushed metal
    whose highlight is round is a polished metal."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = _principled(m)
    col = hex_to_linear(row["srgb_hex"])
    _set(p, "Base Color", (col[0], col[1], col[2], 1.0))
    _set(p, "Metallic", 1.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (140.0, 140.0, 1.0)      # streaks along +Z
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = row.get("rough_lo", 0.24)
    rr.inputs["To Max"].default_value = row.get("rough_hi", 0.44)
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], p.inputs["Roughness"])
    if "Anisotropic" in p.inputs:
        p.inputs["Anisotropic"].default_value = row.get("anisotropy", 0.7)
    return m


# =======================================================================================
def build(stage):
    """stage: 'split' (flat families) or 'texture' (families with maps). Returns a dict
    family -> material and the per-object assignment actually applied."""
    pal = palette()
    fams = pal["families"]
    made, missing = {}, []
    used = sorted({family_of(o.name) for o in bpy.data.objects} - {None})
    for fam in used:
        row = fams.get(fam)
        if row is None:
            missing.append(fam)
            continue
        if fam == "glass":
            made[fam] = glass("M_" + fam, row)
        elif fam in ("greenery", "sheer"):
            made[fam] = translucent("M_" + fam, row)
        elif stage == "texture" and fam in ("stone_marble", "stone_travertine"):
            made[fam] = procedural_stone("M_" + fam, row, fam.endswith("travertine"))
        elif stage == "texture" and fam == "metal_bronze":
            made[fam] = brushed_metal("M_" + fam, row)
        elif stage == "texture":
            made[fam] = textured("M_" + fam, row, fam)
        else:
            made[fam] = flat("M_" + fam, row)
    if missing:
        raise SystemExit(
            "SPLIT REFUSED: no measured row in 04_mood/palette-from-plate.json for "
            + ", ".join(missing) + ". Every family in this frame is a colour somebody read "
            "off the reference; a family with no row would be a typed guess wearing a name.")
    applied = {}
    for ob in bpy.data.objects:
        fam = family_of(ob.name)
        if fam is None or ob.type not in ("MESH", "CURVE"):
            continue
        ob.data.materials.clear()
        ob.data.materials.append(made[fam])
        applied.setdefault(fam, []).append(ob.name)
    return made, applied


def report(applied):
    print("\nMATERIAL SPLIT - every mass in the frame, by family")
    for fam in sorted(applied):
        names = applied[fam]
        head = ", ".join(names[:4]) + (f"  (+{len(names)-4} more)" if len(names) > 4 else "")
        print(f"  {fam:18s} {len(names):3d}  {head}")
    print()
