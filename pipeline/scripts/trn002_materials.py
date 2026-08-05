"""trn002_materials.py — TRN-002 phase 2: material identity for the reproduction.

Same two-layer split as trn001_materials (LAYER LAW): a PURE half — which
material each mass wears (`material_for`) and what that material IS (`PALETTE`)
— importable and testable under plain python, and a bpy half that turns the
table into Principled node graphs.

WHAT THIS MODULE INHERITS RATHER THAN RE-LEARNS (all from trn001_materials,
each earned by a failed round there — read that file before changing any of it):
  * MAP_MEAN / ROUGH_MEAN normalisation. A map already carries a mid tone, so
    multiplying it by an albedo lands at albedo x mean. Normalising by the map's
    own mean makes the MAP carry variation and the SAMPLED value carry identity.
    TRN-001 shipped four rounds with the roughness half of this missing and the
    hero object's polish never reached a frame.
  * TONE_NOISE. Board-to-board drift. TRN-001 measured its floor at 1.9%
    plank-to-plank variation against a reference's 30.4% — identical tone on
    every plank is what makes wood read as printed laminate.
  * NORMAL_STRENGTH is per-MATERIAL, never per-map-slug: a floor plank carries a
    1-2 mm V-groove at every joint and a cabinet panel is spliced flush. Keying
    it by slug is one parameter carrying two things.
  * The albedo METHOD: sample the target patch and divide by a reference surface
    read under the SAME illumination, so the light cancels. Never read a value
    off a lit pixel and call it an albedo. And where a value error belongs to
    the LIGHT lane, correct HUE ONLY and leave luminance alone — otherwise the
    light's error is baked into the material table permanently.

WHAT IS DIFFERENT HERE: TRN-002's palette is dominated by a pale travertine-look
veneer run (console/desk/etagere), smoked-oak wardrobe fronts, white paint, and
a herringbone floor — and every mass in the frame is measured geometry, so a
material can be assigned by NAME with no guessing about which surface is which.

PALETTE VALUES ARE FILLED FROM THE PHASE-2 MEASUREMENT PASS. Any row still
carrying `prov="A"` in PALETTE_PROV is a declared assumption, not a measurement,
and must say so at every gate.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CC0 = os.path.join(REPO, "assets", "shared", "cc0", "textures")

# --------------------------------------------------------------- assignment --
# Mass name (or prefix) -> palette key. PURE: no bpy, no image, no I/O.
# Exact names win over prefixes; a mass with no rule raises rather than falling
# back to a default, because a silent default is a decision nobody made
# (the class this repo names "a default nobody set = a decision nobody made").
EXACT = {
    # The floor slab is now the JOINT plane: the planks ride 2 mm proud of it,
    # so what shows between them is this. The target's joints measure 1.83x
    # darker than the field, which is the number this row carries.
    "floor": "floor_joint",
    "floor_planks": "floor_herringbone",
    "back_wall": "paint_white", "left_wall": "paint_white",
    "right_wall": "paint_white", "door_wall": "paint_white",
    "ceil_main": "paint_ceiling",
    "ward_bulkhead": "lacquer_wardrobe", "ward_body": "lacquer_wardrobe",
    "ward_groove": "reveal_shadow",
    "door_leaf": "lacquer_white",
    "artwork": "art_relief",
    "part_head": "frame_black", "part_jamb_L": "frame_black",
    "part_jamb_R": "frame_black", "part_stile_M": "frame_black",
    "part_rail_B": "frame_black", "part_rail_top": "frame_black",
    "closet_floor": "floor_herringbone", "closet_back": "paint_white",
    "desk": "veneer_travertine", "console": "veneer_travertine",
    "desk_pier": "veneer_travertine",
    "shelf_col_base": "veneer_travertine", "shelf_col_back": "veneer_travertine",
    "tv": "screen_black",
    "rug": "rug_cream",
    "bed_platform": "upholstery_bed", "bed_headboard": "upholstery_bed",
    "bed_mattress": "linen_white",
    "duvet_top": "linen_white", "duvet_drape": "linen_white",
    "pillow_L": "linen_white", "pillow_R": "linen_white", "bolster": "linen_white",
    # NOT oak. At 8x the band shows fine vertical fibrous striations, irregular
    # linear porosity, a vertical butt joint and a MITRED RETURN at the left
    # corner — vein-cut travertine, the same signature as the console. It has
    # been called "the oak band" in every round doc and prompt since r2; the
    # name was a first-look guess that nobody re-examined once it was written
    # down. Same family as the left run, so it must be the same material key.
    "ward_band": "veneer_travertine",
    "nightstand": "veneer_travertine",
    "bench": "upholstery_bed",
    "petcave": "upholstery_bed",
    # ONE lamp. The two-mass version invented a post to hold a measured shade
    # up, and the owner spotted it in the first frame that had light on it.
    # The two old names are KEPT so every historical spec still builds — a
    # rename that silently breaks a past round destroys the ability to
    # reproduce it, and reproducing past rounds is how regressions are found.
    "lamp": "shade_black",
    "lamp_shade": "shade_black", "lamp_stem": "shade_black",
    "duvet_top": "linen_white", "duvet_drape": "linen_white",
    "shelf_col_base": "veneer_travertine",
    "chair_seat": "upholstery_chair", "chair_back": "upholstery_chair",
}
PREFIX = (
    ("rev_", "reveal_shadow"),
    ("dl_", "lens_warm"),
    # every etagere part, under any of the names it has carried across eleven
    # specs (shelf_col, shelf_col_mid/top/cap/board3..., shelf_board2...)
    ("shelf_", "veneer_travertine"),
    # historical names from earlier rounds, kept so every past spec still
    # renders — reproducing an old round is how a regression is caught
    ("ceil_", "paint_ceiling"),
    ("slot_fascia", "paint_white"),
    # the partition's members are PAIRS in the target: a fixed jamb/mullion and
    # the sliding leaf's own stile beside it. All the same powder-coated metal.
    ("leaf_stile", "frame_black"),
    ("mullion", "frame_black"),
    ("chair_leg", "leg_dark"),
)
# Retired names, mapped once so the eleven specs in this lane all build.
EXACT.update({
    "wardrobe": "lacquer_wardrobe",
    "fin_wall": "paint_white",
    "chair": "upholstery_chair",
    "desk_panel": "veneer_travertine",
})


def material_for(name):
    """Palette key for a mass. Raises on an unmapped mass — see module docstring."""
    if name in EXACT:
        return EXACT[name]
    for pre, key in PREFIX:
        if name.startswith(pre):
            return key
    raise KeyError(f"no material rule for mass '{name}' — assign one, never default")


# ------------------------------------------------------------------ palette --
# key -> (linear albedo RGB, roughness, metallic, map-set slug or None, map scale m)
# Every row's basis is in PALETTE_PROV below. Values measured relative to the
# white wall taken at 0.80 albedo (the trn001 method), which assumes the two
# surfaces see comparable illumination — TRUE for vertical surfaces at similar
# height, FALSE for the floor under ceiling fixtures (trn001 paid for that once:
# a sampled 0.72 floor albedo became a second ceiling and flattened the frame).
_M = "M(phase-2 pass, ratio to the back wall taken at 0.80 albedo)"
_A = "A(assumed — not measured from the target)"

# MAPPED ONLY WHERE THE TARGET SHOWS TEXTURE, and the measurement decides which.
# trn001's rule is "every material that has a real map set gets one", written
# after a study found this studio at 95% image-free against 50-66% in pro files.
# Applied blind here it was WRONG: the phase-2 pass measured each surface's own
# texture index, and the walls/ceiling come in at 0.03 — flat — against the
# floor's 0.29 and the travertine's 0.49. Carrying plastered_wall_03 on the
# paint turned smooth walls into raw stucco in the first frame. The rule is
# real; what it needs is the per-surface number, not the studio average.
PALETTE = {
    "paint_white":       ((0.799, 0.799, 0.799), 0.75, 0.0, None, 0.0),
    "paint_ceiling":     ((0.680, 0.638, 0.597), 0.80, 0.0, None, 0.0),
    "lacquer_wardrobe":  ((0.665, 0.651, 0.617), 0.52, 0.0, None, 0.0),
    "lacquer_white":     ((0.760, 0.755, 0.740), 0.45, 0.0, None, 0.0),
    # ONE travertine for the whole left run AND the headboard band. The four
    # objects sample 0.26x-1.05x of the wall, a 4x range — and that range is
    # LIGHTING, proven on a single continuous etagere panel where one spot
    # under the LED strip reads 2.24x another 0.6 m away on the SAME surface,
    # same material, same orientation. Giving each object its own albedo would
    # bake the light's job into the material table, the exact error trn001
    # recorded when it corrected a floor's VALUE instead of its hue.
    "veneer_travertine": ((0.578, 0.485, 0.361), 0.60, 0.0, "marble_01", 1.4),
    "floor_herringbone": ((0.503, 0.314, 0.168), 0.42, 0.0, "wood_floor", 0.66),
    "floor_joint":       ((0.275, 0.172, 0.092), 0.55, 0.0, None, 0.0),
    # The 2026-07-30 ground-truth study measured this studio at 95% image-free
    # materials against 50-66% in every photoreal reference file, with fabric
    # compensating by flat sheen. Every fabric here therefore carries a real
    # map, and the maps are what supply weave — not a roughness number.
    # Fabrics keep their maps for WEAVE (normal), but the rug's diffuse is
    # dropped: wool_boucle's colour variation rendered as a plaid on a rug the
    # target measures as plain. The bed platform's side face measures texture
    # 0.05 — "extraordinarily uniform", plausibly a matte leatherette rather
    # than a weave — so it loses its diffuse map too.
    "rug_cream":         ((0.828, 0.837, 0.823), 0.92, 0.0, "wool_boucle", 0.45),
    "upholstery_bed":    ((0.855, 0.871, 0.863), 0.90, 0.0, None, 0.0),
    "linen_white":       ((0.860, 0.855, 0.840), 0.95, 0.0, "rough_linen", 0.7),
    "upholstery_chair":  ((0.791, 0.768, 0.708), 0.90, 0.0, "rough_linen", 0.5),
    "frame_black":       ((0.117, 0.095, 0.078), 0.45, 0.0, None, 0.0),
    "screen_black":      ((0.051, 0.040, 0.028), 0.12, 0.0, None, 0.0),
    "shade_black":       ((0.045, 0.040, 0.035), 0.55, 0.0, None, 0.0),
    "art_relief":        ((0.780, 0.770, 0.750), 0.80, 0.0, None, 0.0),
    "reveal_shadow":     ((0.300, 0.290, 0.275), 0.85, 0.0, None, 0.0),
    "lens_warm":         ((1.000, 0.955, 0.900), 0.50, 0.0, None, 0.0),
    # the chair legs: near-black tapered timber in the reference, the darkest
    # furniture element in the frame after the TV.
    "leg_dark":          ((0.055, 0.048, 0.042), 0.40, 0.0, None, 0.0),
}

PALETTE_PROV = {
    "paint_white": _M + "; the declared REFERENCE surface (back wall -y face, "
                        "n=65,014 px). Its own illumination spread p05..p95 is "
                        "1.36x, which is the floor on every ratio below.",
    "paint_ceiling": _M + "; 0.811x wall, n=88,286. Warmer than the wall "
                          "(chroma 0.853/0.801/0.748) and NOT uniform: near "
                          "third 0.926x vs far third 0.723x = 1.28x within one "
                          "plane, which the LIGHT must produce, not this row.",
    "lacquer_wardrobe": _M + "; 0.816x wall, n=111,816, IQR very tight. "
                             "Illuminant-corrected B/R 0.926 = a slightly warm "
                             "off-white greige, ~7% warmer than the wall paint.",
    "lacquer_white": _A + " — the entry door leaf is never cleanly sampled "
                          "(it sits in the slot's shadow); taken as the wall "
                          "paint slightly warmed and smoother.",
    "veneer_travertine": _M + "; ONE material for console/desk/pier/etagere/band"
                              "/nightstand. Value from the etagere panel (the "
                              "middle of the run's 4x lighting spread). The "
                              "band was called OAK from r2 to r5 and is not: "
                              "at 8x it is vein-cut travertine with a mitred "
                              "return, same signature as the console.",
    "floor_herringbone": _M + "; 0.436x wall, n=30,694, the warmest and most "
                              "saturated surface in the room (corrected B/R "
                              "0.327). Map scale 0.66 m = the measured 132 mm "
                              "plank width x the map's ~5-plank tile.",
    "floor_joint": _M + "; the plank field divided by the measured joint "
                        "contrast (joints read 1.83x darker than the field — "
                        "the same signal the herringbone phase was fitted on).",
    "rug_cream": _M + "; sampled in BOTH conditions (lit front 1.154x wall, "
                      "shadowed band 0.938x = 1.23x apart) and the row carries "
                      "their midpoint — the spread is the light's to produce. "
                      "Corrected B/R 1.025 = essentially neutral.",
    "upholstery_bed": _M + "; the side face reads 1.512x wall and CLIPS when "
                           "converted (albedo 1.16-1.22), so the row is capped "
                           "at the foot face's honest 1.091x-derived value. A "
                           "measurement that returns an impossible albedo is "
                           "reporting the light, not the surface.",
    "linen_white": _M + "; four bedding samples spanning 1.35x (sheet at foot "
                        "1.292x wall to shaded duvet 0.954x); neutral warm-"
                        "white, same hue as the wall at higher value.",
    "upholstery_chair": _A + " — the chair is small and half-occluded; taken "
                             "as the headboard fabric (0.966x wall) which is "
                             "the nearest measured fabric in the frame.",
    "frame_black": _M + "; BRACKETED not single-valued: full strips read "
                        "0.150-0.191x wall, darkest-30% cores 0.113-0.125x. "
                        "Row uses the core. Corrected B/R 0.675 = a warm dark "
                        "grey-brown, NOT neutral black. Roughness matte: the "
                        "apparent specular tail (p99/med 4.6-6.9) collapses to "
                        "1.1-1.4 once JPEG ringing off the glass is excluded.",
    "screen_black": _M + " (upper bound); dark core 0.053x wall -> albedo ~0.04."
                         " The TV is the ONLY specular class in the frame "
                         "(p99/med 11.97, two broad soft bands), hence the low "
                         "roughness here while everything else is matte.",
    "shade_black": _M + "; the lamp shade sits at Ylin 0.008-0.020 with no rim "
                        "and no pool — it is a dark cone, and the lamp is OFF.",
    "art_relief": _A + " — the mount board reads near the wall value; the "
                       "artwork's relief is geometry the spec does not yet "
                       "carry (frame 20.9 mm, relief block ~450x650 in a "
                       "705x978 mat) and is a styling-round ticket.",
    "reveal_shadow": _M + " (upper bound); the wardrobe grooves read 0.710x "
                          "wall but are truly darker — they are UNRESOLVED at "
                          "this camera (equivalent width 1.05 mm, sigma does "
                          "not grow with scale), so they must be matched "
                          "photometrically, never tuned by eye.",
    "leg_dark": _A + " — read off the target's chair legs as a near-black stained timber; not sampled cleanly (they are 4-6 px wide), so the value is bracketed by the partition frame core (0.11) above and the TV core (0.05) below.",
    "lens_warm": _M + "; the four lens cores are the frame's only legitimately "
                      "clipped pixels (273 px, 0.03%).",
}

# ------------------------------------------------------------- bpy builders --
# Linear MEAN of each map set's diffuse, measured once outside Blender. The
# first four are trn001's constants (its canon); the fabrics were measured for
# this lane and the method cross-checks — recomputing trn001's three at 512px
# returns 0.4429/0.2168/0.2482 against its 0.4493/0.2189/0.2495.
MAP_MEAN = {
    "wood_floor": (0.2189, 0.1185, 0.0557),
    "plastered_wall_03": (0.2495, 0.2061, 0.1679),
    "marble_01": (0.4493, 0.3397, 0.1936),
    "grey_cartago_03": (0.2664, 0.2489, 0.2317),
    "rough_linen": (0.2842, 0.4077, 0.6136),
    "wool_boucle": (0.2415, 0.2034, 0.1634),
    "poly_wool_herringbone": (0.1925, 0.1801, 0.1654),
}
ROUGH_MEAN = {
    "wood_floor": 0.471, "plastered_wall_03": 0.911, "marble_01": 0.506,
    "wool_boucle": 0.657, "poly_wool_herringbone": 0.861,
    # rough_linen ships no roughness map in this pack — only AO. Left out
    # deliberately: keying it to the AO mean would be a different quantity
    # wearing the right variable's name.
}
# Materials that keep a map set for its NORMAL (weave, grain relief) but must
# NOT take its colour variation — measured texture near zero on that surface.
DIFFUSE_OFF = {"rug_cream"}
# Materials whose mesh carries REAL UVs and must use them instead of box
# projection. Only the herringbone floor: its planks each carry their own UV
# frame so the grain turns with the chevron, which is what a box projection —
# one orientation for the whole floor — structurally cannot do.
UV_MAPPED = {"floor_herringbone"}
# Emission strength per material. The four downlight lenses are the frame's
# only legitimately clipped pixels (273 px, 0.03%), so the LENS is supposed to
# blow — what must not appear is a ceiling pool, and the measurement killed
# that twice (glow back to background within 120-200 mm; the floor directly
# under a fixture is DARKER than a metre away). Making the lens an emissive
# SURFACE rather than a bright point is what separates the two: a surface that
# small blows its own pixels and lights almost nothing.
EMISSIVE = {"lens_warm": 34.0, "strip_led": 26.0}
MAP_FILE = {          # slug -> (diffuse, roughness or None, normal or None)
    "wood_floor": ("wood_floor_Diffuse_2k.jpg", "wood_floor_Rough_2k.jpg",
                   "wood_floor_nor_gl_2k.jpg"),
    "plastered_wall_03": ("plastered_wall_03_Diffuse_2k.jpg",
                          "plastered_wall_03_Rough_2k.jpg",
                          "plastered_wall_03_nor_gl_2k.jpg"),
    "marble_01": ("marble_01_Diffuse_2k.jpg", "marble_01_Rough_2k.jpg",
                  "marble_01_nor_gl_2k.jpg"),
    "rough_linen": ("rough_linen_Diffuse_2k.jpg", None,
                    "rough_linen_nor_gl_2k.jpg"),
    "wool_boucle": ("wool_boucle_Diffuse_2k.jpg", "wool_boucle_Rough_2k.jpg",
                    "wool_boucle_nor_gl_2k.jpg"),
    "poly_wool_herringbone": ("poly_wool_herringbone_Diffuse_2k.jpg",
                              "poly_wool_herringbone_Rough_2k.jpg",
                              "poly_wool_herringbone_nor_gl_2k.jpg"),
}
NORMAL_STRENGTH = {
    "floor_herringbone": 1.6,          # planks DO carry a joint micro-bevel
    "veneer_travertine": 0.10,         # spliced flush and sanded — not a floor
    "lacquer_wardrobe": 0.06,
    "paint_white": 0.12, "paint_ceiling": 0.12,
    "linen_white": 0.6, "upholstery_bed": 0.6, "rug_cream": 0.9,
    "upholstery_chair": 0.5,
}
TONE_NOISE = {
    "floor_herringbone": (0.30, 2.2, (0.35, 1.0, 6.0)),
    "veneer_travertine": (0.16, 1.6, (0.5, 1.0, 3.0)),
}


def build_materials(palette_override=None):
    """{palette key: bpy Material}. bpy-only — imported from the builder.

    Every mapped material is BOX-PROJECTED on object coordinates because these
    meshes carry no UVs by construction (authored quads, never unwrapped), and
    normalised by its map's own mean so the MAP carries variation while the
    MEASURED value carries identity. Both halves of that normalisation are
    applied — base colour AND roughness — because trn001 shipped four rounds
    with only the first, and its hero material's polish never reached a frame.
    """
    import bpy
    pal = dict(PALETTE)
    pal.update(palette_override or {})
    out = {}
    for key, (alb, rough, metal, slug, scale) in pal.items():
        m = bpy.data.materials.new(f"M_TRN002_{key}")
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*alb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if key in EMISSIVE:
            bsdf.inputs["Emission Color"].default_value = (*alb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = EMISSIVE[key]
        if not slug or slug not in MAP_FILE:
            out[key] = m
            continue
        diff_f, rough_f, nor_f = MAP_FILE[slug]
        coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        uv = key in UV_MAPPED
        s = 1.0 if uv else 1.0 / max(scale, 1e-6)
        mapping.inputs["Scale"].default_value = (s, s, s)
        nt.links.new(coord.outputs["UV" if uv else "Object"], mapping.inputs["Vector"])

        def _tex(fname, non_color):
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(os.path.join(CC0, slug, fname),
                                           check_existing=True)
            if not uv:
                t.projection = "BOX"
                t.projection_blend = 0.3
            t.extension = "REPEAT"
            if non_color:
                t.image.colorspace_settings.name = "Non-Color"
            nt.links.new(mapping.outputs["Vector"], t.inputs["Vector"])
            return t

        # DIFFUSE-OFF materials still get their weave/relief from the normal
        # map — the target's fabrics carry texture the eye reads as cloth while
        # measuring near-zero COLOUR variation, and those are different maps.
        if key in DIFFUSE_OFF:
            if nor_f:
                nt_tex = _tex(nor_f, True)
                nmapn = nt.nodes.new("ShaderNodeNormalMap")
                nmapn.inputs["Strength"].default_value = NORMAL_STRENGTH.get(key, 0.3)
                nt.links.new(nt_tex.outputs["Color"], nmapn.inputs["Color"])
                nt.links.new(nmapn.outputs["Normal"], bsdf.inputs["Normal"])
            out[key] = m
            continue
        # base colour: (map / map_mean) * albedo
        tex = _tex(diff_f, False)
        mean = MAP_MEAN[slug]
        div = nt.nodes.new("ShaderNodeVectorMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = mean
        nt.links.new(tex.outputs["Color"], div.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        mul.inputs[6].default_value = (*alb, 1.0)
        nt.links.new(div.outputs["Vector"], mul.inputs[7])
        base_out = mul.outputs[2]

        if key in TONE_NOISE:
            amp, nscale, stretch = TONE_NOISE[key]
            nmap = nt.nodes.new("ShaderNodeMapping")
            nmap.inputs["Scale"].default_value = stretch
            nt.links.new(coord.outputs["Object"], nmap.inputs["Vector"])
            noise = nt.nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = nscale
            nt.links.new(nmap.outputs["Vector"], noise.inputs["Vector"])
            tone = nt.nodes.new("ShaderNodeMix")
            tone.data_type = "RGBA"
            tone.blend_type = "MULTIPLY"
            tone.inputs["Factor"].default_value = amp
            nt.links.new(base_out, tone.inputs[6])
            nt.links.new(noise.outputs["Fac"], tone.inputs[7])
            base_out = tone.outputs[2]
        nt.links.new(base_out, bsdf.inputs["Base Color"])

        if rough_f and slug in ROUGH_MEAN:
            rt = _tex(rough_f, True)
            rdiv = nt.nodes.new("ShaderNodeMath")
            rdiv.operation = "DIVIDE"
            nt.links.new(rt.outputs["Color"], rdiv.inputs[0])
            rdiv.inputs[1].default_value = ROUGH_MEAN[slug]
            rmul = nt.nodes.new("ShaderNodeMath")
            rmul.operation = "MULTIPLY"
            nt.links.new(rdiv.outputs["Value"], rmul.inputs[0])
            rmul.inputs[1].default_value = rough
            nt.links.new(rmul.outputs["Value"], bsdf.inputs["Roughness"])

        if nor_f:
            nt_tex = _tex(nor_f, True)
            nmapn = nt.nodes.new("ShaderNodeNormalMap")
            nmapn.inputs["Strength"].default_value = NORMAL_STRENGTH.get(key, 0.3)
            nt.links.new(nt_tex.outputs["Color"], nmapn.inputs["Color"])
            nt.links.new(nmapn.outputs["Normal"], bsdf.inputs["Normal"])
        out[key] = m
    return out


def palette_report():
    """One line per material with its provenance — printed at every build so a
    gate artifact can never quote a measured-looking number that was assumed."""
    out = []
    for k in sorted(PALETTE):
        alb, rough, metal, slug, scale = PALETTE[k]
        out.append(f"  {k:20s} alb=({alb[0]:.3f},{alb[1]:.3f},{alb[2]:.3f}) "
                   f"r={rough:.2f} m={metal:.1f} map={slug or '-':18s} "
                   f"{PALETTE_PROV.get(k, 'PROV MISSING')}")
    return "\n".join(out)
