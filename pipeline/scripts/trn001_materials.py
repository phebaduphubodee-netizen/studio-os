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

# Linear MEAN of each CC0 ROUGHNESS map, measured the same way MAP_MEAN was.
# Needed for the same reason and it was missed for four rounds: the rough map was
# linked STRAIGHT to the shader, so PALETTE's roughness column was dead for every
# material that has one. The marble asked for 0.18 and rendered at 0.506 — the
# hero object's polish never reached a single frame — while paint asked 0.65 and
# got 0.911 and the cavity asked 0.70 and got 0.471. Normalising by the mean makes
# the map contribute VARIATION and the specified value contribute LEVEL, which is
# exactly what MAP_MEAN already does for base colour; the cure existed in this
# file and had simply never been carried across to the next input.
ROUGH_MEAN = {
    "marble_01": 0.506,
    "plastered_wall_03": 0.911,
    "wood_floor": 0.471,
}

# how hard each map's normal pushes; paint and stone are nearly flat in reality
# Resolved by material KEY first, then by map slug. Keyed by slug alone it was
# ONE PARAMETER CARRYING TWO THINGS — the same shape found in tower.d_mm on the
# same day: every veneer shares the `wood_floor` slug with the actual floor, so a
# cabinet panel and a floor plank were forced to wear the same micro-bevel relief.
#
# The DR fired 2026-08-01 (notebook 2638a889, conv 579867c3) names that relief as
# THE tell: pre-finished flooring carries a 1-2 mm V-groove around every plank to
# disguise subfloor lippage, while cabinet panels are spliced flush and sanded to
# a single seamless plane — "if your render includes linear micro-shadows catching
# the light at the joint lines... the eye instantly recognizes the boundary
# markers of individual floor planks". Ours ran the floor's normal at the 0.8
# default on all three veneers and the cubby lining.
NORMAL_STRENGTH = {
    "plastered_wall_03": 0.12, "marble_01": 0.15, "grey_cartago_03": 0.10,
    # per-material: fine veneer is a flush, sanded plane, not a plank floor
    "veneer_fascia": 0.10, "veneer_pier": 0.10, "veneer_altar": 0.10,
    "cavity": 0.10,
}

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
    # NOT cooled with the other two veneers, though the fix list said to carry it
    # with them: measured, this albedo's hue is ALREADY the target's. Normalised,
    # ours (1.227, 1.000, 0.773) against the target patch's (1.228, 0.978, 0.794)
    # is a hue distance of 0.022, where the stiles measure 0.327. matcheck's 0.106
    # on this row is the RENDERED patch, and that surface is blown — this frame
    # desaturates as it brightens (measured exponent -0.35 on paint), so 0.106 is
    # a VALUE symptom wearing a hue costume. Cooling it would pay for the light's
    # error inside the material table, permanently.
    # ROUND 4: the delivered altar measures 2.26 horizontal-to-vertical grain
    # energy against our 0.38 — round 3 reasoned "upright on the piers AND the
    # altar blocks" and the reference supports that for the piers (0.57 target
    # vs 0.45 ours) but not for the altar. Given at the fascia's own ratio
    # strength (16.7:1), because the first cut at 4:1 only reached 0.75.
    "veneer_altar":  (4.0, 1.0, 0.30),
    "cavity":        (0.30, 1.0, 5.0),
}

def grain_axis(key):
    """Which world axis a surface's figure runs along: the STRETCHED one. PURE,
    so the reference's verdict is pinned as a property rather than as the two
    numbers that happen to produce it.

    Worth stating because round 4 got it wrong first: a 90-degree turn of the
    texture coordinate was tried, on the reasoning that the map's own planks run
    along its v axis and no stretch could rotate them. The frame refuted it —
    the grain ratio went 0.38 -> 0.98, not to the 2.26 the reference measures.
    The turn only swaps WHICH texture axis carries each world axis; the stretch
    per world axis is untouched, so the figure still reads along the same one.
    Which is also why the fascia already reads correctly at 16.7:1 while the
    altar sat at 4:1 — the axis was right, the ratio was too weak."""
    ax, _, az = MAP_ASPECT.get(key, (1.0, 1.0, 1.0))
    return "z" if az >= ax else "x"


# name -> (linear albedo, roughness, metallic, map-set slug or None, map scale m)
PALETTE = {
    # wood_floor, not the worn table: it is the only set on disk whose grain is
    # LINEAR, which is the property that makes wood read as wood
    # THE DELIVERED MILLWORK IS SMOKED GREY OAK; OURS WAS HONEY OAK, TWICE.
    # Two instruments sharing no assumption agree. (1) At MATCHED VALUE the
    # target's two woods are 1.499x apart in R/B and ours only 1.104x — and our
    # 1.104x is exactly what these two triples predict (1.091), so nothing but
    # albedo contributes hue here and the delivered joinery is genuinely two
    # species where ours was one wood rendered twice. (2) Binned across the whole
    # luminance range, our header face reads R/B 3.18-3.29 against the target's
    # 2.37-2.47, FLAT in both frames — flat across luminance is the signature of
    # a material, not of a light.
    # Both moves are HUE-ONLY: luminance is preserved to 0.01% (fascia
    # 0.18055 -> 0.18053) and 0.14% (pier 0.16915 -> 0.16938), because the value
    # error on these surfaces belongs to the light lane and must not be paid for
    # twice. Direction is measured; the exact triples are display-referred
    # estimates and should be bracketed the way halo_w and the kelvin were.
    "veneer_fascia": ((0.221, 0.174, 0.126), 0.42, 0.0, "wood_floor", 1.7),
    "veneer_pier":  ((0.182, 0.169, 0.136), 0.42, 0.0, "wood_floor", 1.0),
    "veneer_altar": ((0.27, 0.22, 0.17), 0.45, 0.0, "wood_floor", 1.0),
    # 2026-08-01: the cubby lining was a near-black (0.05) chosen when the cavity
    # was 82 mm deep — at that depth almost anything reads dark, so the value was
    # never really under test. With the pocket built to its measured 276.5 mm the
    # back panel became measurable and the near-black is REFUTED: our cavity MOUTH
    # runs 1.42x too BRIGHT while our back panel reads 0.36-0.68x of the target's
    # across both towers, and more incident light returning less means the albedo
    # is too low, by a factor near the 3.6x that separated it from the veneer.
    # Hue agrees — ours rendered R/G 1.49 against the target's 1.15-1.37, and the
    # old triple was WARMER (1.25) than the veneer it sits beside (1.08).
    "cavity":       ((0.182, 0.169, 0.136), 0.70, 0.0, "wood_floor", 1.0),
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
    # ROUND 4 FOUND ROUND 3's ASSUMPTION. Every albedo in this table was backed
    # out by dividing the target patch by the white wall's reading and taking the
    # wall as 0.80 — which silently assumes the two surfaces receive the SAME
    # illuminance. Under a flat form light they did, so the sample was self-
    # consistent; under downlights it is false, because a horizontal floor
    # collects far more from a ceiling fixture than a vertical wall does. The
    # sample said 0.72 — an albedo brighter than most white paint, on the largest
    # surface in the room — and our own vault has the physical value:
    # knowledge/lighting/lumen-method-and-fixture-placement.md:150, "ceiling ~80%,
    # walls ~50%, floor ~20%". At 0.72 the floor was a second ceiling, bouncing
    # every gradient flat: the frame measured 22:1 against the target's 141:1,
    # cavities 2.6x too bright, and the floor's own 37.6% falloff reduced to 2.5%.
    # Set to pale-oak LRV with the sampled HUE preserved, then confirmed in frame
    # (the floor must still read ~0.94 of the wall — that it does is the proof
    # the illuminance ratio, not the albedo, was carrying that reading).
    "floor_oak":    ((0.42, 0.35, 0.26), 0.40, 0.0, "wood_floor", 2.0),
    # a painted wall must be the LEAST chromatic neutral in the room; ours was
    # 1.7x more chromatic than the stone where the reference is 0.53x
    "paint_white":  ((0.80, 0.80, 0.80), 0.65, 0.0, "plastered_wall_03", 4.0),
    # the concealed LED behind the slab (owner 2026-07-31) — an emitter, so its
    # albedo entry is the emission colour and EMISSION carries the strength
    "halo_led":     ((1.00, 0.955, 0.90), 0.50, 0.0, None, 0.0),
    # ROUND 4 — the downlight the camera can see. The target's two lens discs
    # read at 1.0 (they are the frame's only legitimately clipped pixels: 0.08%
    # of it), so the lens is SUPPOSED to blow; what must not is the halo.
    "lens_warm":    ((1.00, 0.955, 0.90), 0.50, 0.0, None, 0.0),
    "trim_metal":   ((0.52, 0.52, 0.53), 0.35, 1.0, None, 0.0),
    # ROUND 5 styling. The vase is the darkest object in the delivered frame —
    # it is what the detector found it BY, thresholding below 0.16 luminance —
    # so its albedo has to sit under the cavity's, not at some generic "dark".
    "vase_dark":    ((0.035, 0.030, 0.030), 0.22, 0.0, None, 0.0),
    "bronze_dark":  ((0.35, 0.27, 0.16), 0.38, 1.0, None, 0.0),
    "wax_white":    ((0.86, 0.84, 0.79), 0.55, 0.0, None, 0.0),
}

# emission strength (W/m^2-ish) for the materials that are light sources
EMISSION = {"halo_led": 16.0, "lens_warm": 40.0}

# A bookmatched slab is the one thing the CC0 library does not have: every
# marble set on it is a TILED floor, and both candidates put tile joints across
# the middle of the panel. Veining is therefore generated — continuous, non
# repeating, and controllable — as noise-distorted bands, which is what large
# sweeping figure actually is. (key -> dict of knobs)
PROCEDURAL = {
    "marble": {
        "detail": 8.0, "roughness": 0.55, "distortion": 1.6,
        # ANISOTROPY IS WHAT TURNS A CONTOUR INTO A VEIN. At 2.2:1 the level
        # sets stayed closed; the delivered slab runs one dominant system, so
        # the field is compressed ~9x across the vein direction and tilted about
        # Y (the axis that actually rotates a pattern on a panel standing in the
        # x-z plane — the old code turned it about Z, which barely moves it).
        "stretch": (1.0, 1.0, 0.12), "tilt": 0.62,
        # HOW MANY veins is set by scale x the compression, not by scale alone —
        # the first cut ran 2.2 against a 9x squeeze, i.e. a feature every 50 mm,
        # which is ~40 streaks across the panel and reads as watered silk. The
        # delivered slab carries a handful of systems, so the product is aimed at
        # a vein roughly every 300 mm instead.
        "scale": 0.42, "width": 0.034, "width_var": 0.85, "width_scale": 0.6,
        # vein VALUE is measured, not chosen: on the slab patch the delivered
        # stone runs a p95/p5 spread of 1.23 and our first cut at dark 0.46 ran
        # 1.42 — veins too heavy, which is what makes stone read as printed
        "dark": 0.58, "sharp": 1.7,
        # secondary feathering, held OFF the clean fields by its own mask
        "fine_scale": 1.6, "fine_width": 0.015, "fine_var": 0.85,
        "fine_dark": 0.78, "mask_scale": 0.55, "mask_lo": 0.50, "mask_hi": 0.78,
        # Stone is not chalk. The vault carries the roughness bands (honed
        # 0.4-0.7, polished 0.0-0.15) and one line saying SSS is used "sparingly
        # for high-end realism" — the sparing amount is the point: enough that
        # light entering the surface comes back out slightly offset, which is
        # what separates marble from painted plaster, not enough to make an
        # 18 mm slab glow like alabaster.
        "sss_weight": 0.14, "sss_radius_mm": (3.6, 3.0, 2.6),
        # the veining multiplies albedo DOWN, so the built slab drifts below the
        # albedo that was sampled off the target. Same disease MAP_MEAN cures for
        # image maps; measured back in frame rather than assumed.
        "albedo_gain": 1.32,
    },
}


def _build_veined_stone(nt, bsdf, albedo, k):
    """Marble veining as a DIRECTIONAL system of varying-width veins.

    The previous generator passed a noise field through a narrow ramp window,
    and that is exactly why two independent cold critics called the result a
    contour map: **the level sets of a smooth scalar field are closed loops.**
    A fixed window on a fixed field can only ever return closed curves of one
    width — a topographic map is literally the same construction. No amount of
    tuning the window escapes that, which is why it survived a whole round.

    Three changes make veins instead of contours, each answering something the
    reference shows:
      * ANISOTROPY. Compressing the field ~9x across one axis stretches those
        closed loops into long streaks, and tilting about Y (the axis that
        actually rotates a pattern on a panel standing in the x-z plane — the
        old code turned it about Z, which barely moves it) lays them on the
        delivered slab's diagonal.
      * WIDTH AS A LIVE INPUT. Distance-to-the-centre-line divided by a width
        that is itself a noise gives a vein that swells and thins along its own
        length. A ramp cannot do this; its window is a constant.
      * CLEAN FIELDS. The secondary feathering is multiplied by a large-scale
        mask, so it clusters near the primary system and leaves the open white
        areas the reference has between vein systems.

    Grey and achromatic on purpose: the round-3 critic measured the delivered
    slab's veins at +0.2 R-B (pure value, no colour) against our image-mapped
    stone's +5.4 rusty ones."""
    # TWO mapping nodes, and the ORDER is the whole point. One node applies
    # Scale THEN Rotation, so the compression axis is pinned in object space
    # before the rotation is ever reached and the veins come out running along a
    # world axis whatever the tilt says — which is exactly what the first attempt
    # rendered: horizontal streaks under a 35-degree tilt. Rotating FIRST and
    # compressing SECOND puts the narrow axis on the diagonal, so the veins run
    # on the delivered slab's diagonal instead.
    texco = nt.nodes.new("ShaderNodeTexCoord")
    turn = nt.nodes.new("ShaderNodeMapping")
    turn.inputs["Rotation"].default_value = (0.0, k.get("tilt", 0.0), 0.0)
    nt.links.new(texco.outputs["Object"], turn.inputs["Vector"])
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = tuple(1.0 / a for a in k["stretch"])
    nt.links.new(turn.outputs["Vector"], mapping.inputs["Vector"])

    def _noise(scale, detail, distortion, vector=None):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = k["roughness"]
        n.inputs["Distortion"].default_value = distortion
        nt.links.new(vector or mapping.outputs["Vector"], n.inputs["Vector"])
        return n

    def _math(op, a, b=None, clamp=False):
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = op
        m.use_clamp = clamp
        if hasattr(a, "default_value") or not isinstance(a, (int, float)):
            nt.links.new(a, m.inputs[0])
        else:
            m.inputs[0].default_value = a
        if b is not None:
            if isinstance(b, (int, float)):
                m.inputs[1].default_value = b
            else:
                nt.links.new(b, m.inputs[1])
        return m.outputs[0]

    def vein_mask(scale, width, var, width_scale, extra_mask=None):
        """1.0 on the vein centre-line, falling to 0 at its (varying) edge."""
        field = _noise(scale, k["detail"], k["distortion"])
        # half-width = width * (1 - var + 2*var*noise)  -> swells and thins
        wnoise = _noise(width_scale, 2.0, 0.0)
        w = _math("MULTIPLY", wnoise.outputs["Fac"], 2.0 * var)
        w = _math("ADD", w, 1.0 - var)
        w = _math("MULTIPLY", w, width)
        w = _math("MAXIMUM", w, 1e-4)
        d = _math("SUBTRACT", field.outputs["Fac"], 0.5)
        d = _math("ABSOLUTE", d)
        v = _math("DIVIDE", d, w)
        v = _math("SUBTRACT", 1.0, v, clamp=True)
        # a linear fall from centre-line to edge is a smear; real veining has a
        # crisp core with a narrow bleed, which is what the exponent buys
        if k.get("sharp", 1.0) != 1.0:
            v = _math("POWER", v, k["sharp"], clamp=True)
        if extra_mask is not None:
            v = _math("MULTIPLY", v, extra_mask, clamp=True)
        return v

    def apply(v, dark, on_top, base):
        mixn = nt.nodes.new("ShaderNodeMixRGB")
        mixn.blend_type = "MIX"
        mixn.inputs["Color2"].default_value = (*[c * dark for c in base], 1.0)
        if on_top is None:
            mixn.inputs["Color1"].default_value = (*base, 1.0)
        else:
            nt.links.new(on_top, mixn.inputs["Color1"])
        nt.links.new(v, mixn.inputs["Fac"])
        return mixn.outputs["Color"]

    # the veining only ever multiplies albedo DOWN, so the built slab drifts
    # below the albedo sampled off the target unless it is given the loss back
    gain = k.get("albedo_gain", 1.0)
    base = tuple(min(0.95, c * gain) for c in albedo)

    primary = vein_mask(k["scale"], k["width"], k["width_var"], k["width_scale"])
    col = apply(primary, k["dark"], None, base)

    mask_n = _noise(k["mask_scale"], 2.0, 0.0)
    mask = _math("SUBTRACT", mask_n.outputs["Fac"], k["mask_lo"])
    mask = _math("DIVIDE", mask, max(k["mask_hi"] - k["mask_lo"], 1e-4))
    mask = _math("MAXIMUM", mask, 0.0)
    mask = _math("MINIMUM", mask, 1.0)
    fine = vein_mask(k["fine_scale"], k["fine_width"], k["fine_var"],
                     k["width_scale"] * 2.0, extra_mask=mask)
    col = apply(fine, k["fine_dark"], col, base)
    nt.links.new(col, bsdf.inputs["Base Color"])

    # subsurface, set by input NAME and skipped loudly if this Blender spells it
    # differently — a silently-missing translucency is the "reverted by an
    # omission" shape, and it would look exactly like a tuning choice
    w = k.get("sss_weight")
    if w:
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = w
            nt.links.new(col, bsdf.inputs["Subsurface Color"]) \
                if "Subsurface Color" in bsdf.inputs else None
            if "Subsurface Radius" in bsdf.inputs:
                bsdf.inputs["Subsurface Radius"].default_value = tuple(
                    r * 0.001 for r in k.get("sss_radius_mm", (1.0, 1.0, 1.0)))
            if "Subsurface Scale" in bsdf.inputs:
                bsdf.inputs["Subsurface Scale"].default_value = 1.0
        else:
            print("  MARBLE: no 'Subsurface Weight' input on this Principled "
                  "BSDF — stone is rendering WITHOUT translucency")


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
    if n.endswith("_lens"):
        return "lens_warm"
    if n.endswith("_trim"):
        return "trim_metal"
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

def build_materials(emission_override=None):
    """Create every palette material as a Blender node graph. Returns
    {key: bpy Material}. Only called from inside Blender.

    emission_override lets the LIGHT round dial an emitter from the spec without
    editing this table — the halo's strength is a lighting decision, and leaving
    it here would have made it revertible by an omission (this project's most
    expensive recurring class)."""
    import bpy

    emis = dict(EMISSION)
    for k, v in (emission_override or {}).items():
        if v is not None:
            emis[k] = float(v)
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
        if key in emis:
            for nm_ in ("Emission Color", "Emission"):
                if nm_ in bsdf.inputs:
                    bsdf.inputs[nm_].default_value = (*albedo, 1.0)
                    break
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emis[key]

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
                rmean = ROUGH_MEAN.get(slug)
                rsrc = img(maps["rough"], True).outputs["Color"]
                if rmean:
                    # scale the map so its MEAN lands on the specified roughness,
                    # keeping the map's variation and the table's level
                    sc = nt.nodes.new("ShaderNodeMath")
                    sc.operation = "MULTIPLY"
                    sc.use_clamp = True
                    sc.inputs[1].default_value = rough / rmean
                    nt.links.new(rsrc, sc.inputs[0])
                    rsrc = sc.outputs["Value"]
                nt.links.new(rsrc, bsdf.inputs["Roughness"])
            if "normal" in maps:
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = NORMAL_STRENGTH.get(
                    key, NORMAL_STRENGTH.get(slug, 0.8))
                nt.links.new(img(maps["normal"], True).outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        made[key] = mat
    return made
