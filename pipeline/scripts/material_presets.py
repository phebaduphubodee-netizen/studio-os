#!/usr/bin/env python3
"""material_presets.py — spec-selectable material presets (the owner's hand on materials).

WHY THIS EXISTS (2026-07-14, owner direction): the render palette must be chosen in the
SPEC (ownable, gateable, FF&E-groundable), not hardcoded in build_room and not repainted
by the Gemini pass. This module is the pure-python half: a preset table + a validator +
a resolver. build_room.py consumes it inside Blender; tests consume it without Blender
(same law as material_defaults.py — pure stdlib ON PURPOSE).

SPEC SURFACE (optional; absence == the legacy hardcoded palette, byte-identical):
    "materials": {
      "schema": "interior-ai/materials@0.1",
      "surfaces": {"floor"|"walls"|"feature_wall"|"millwork"|"glazing"|"fixtures": "<preset>"},
      "families": {"fabric"|"wood"|"neutral": "<preset>"},
      "elements": {"<item name or kind>": "<preset>"}   # per-piece override (retint / primitives)
    }
Unknown preset names / unknown keys raise ValueError — a typo must fail LOUD, never
silently render the default palette (the flattering-scorer family of bugs, material flavor).

TIERS (authority order, knowledge/materials/bsdf-material-presets.md:11-33):
  authoring bounds (pbr-material-behavior.md §2)  >  REFERENCE presets  >  design-intent.
Bounds are ENFORCED here at resolve time, so no preset can leave the plausible band:
  - dielectric albedo clamped to the 30–240 sRGB texel band (pbr-material-behavior.md:55)
    (metals and glass transmission tints are exempt — the band governs dielectric albedo);
  - roughness floored/ceiled to [0.03, 0.97] — never absolute 0.0/1.0
    (bsdf-material-presets.md:54-60, render-quality.md §3);
  - metalness stays binary 0.0/1.0 (bsdf-material-presets.md:61-63).
REFERENCE presets are starting points, NOT gates (bsdf-material-presets.md:29-31): they
may pick what a render shows; they must never FAIL a deliverable.

COLOR LAW: presets author sRGB (what a human reads off a swatch/hex); build_room's node
default_value wants LINEAR (the walnut pale-pink lesson, build_room.py:1128-1130).
srgb_to_linear() is the one conversion point. Presets copied verbatim from the LIVE
legacy palette author LINEAR directly (marked "space": "linear") so selecting them
reproduces today's render exactly.
"""

# ---------------------------------------------------------------------------
# color helpers (pure)
# ---------------------------------------------------------------------------

_SRGB_BAND_LO, _SRGB_BAND_HI = 30, 240      # texel band, pbr-material-behavior.md:55
ROUGH_FLOOR, ROUGH_CEIL = 0.03, 0.97        # never absolute 0.0/1.0


def hex_to_srgb01(hx):
    """'#RRGGBB' -> (r, g, b) floats 0..1 (still sRGB-encoded)."""
    hx = hx.lstrip("#")
    if len(hx) != 6:
        raise ValueError(f"bad hex color {hx!r}")
    return tuple(int(hx[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_to_linear(c):
    """One sRGB-encoded channel 0..1 -> linear (IEC 61966-2-1 piecewise EOTF)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(v):
    """The INVERSE of srgb_to_linear — linear 0..1 -> sRGB-encoded 0..1 (IEC 61966-2-1
    piecewise OETF). Added 2026-07-23: the 30-240 band is stated in sRGB TEXEL codes, so a
    colour authored LINEAR (which every bespoke builder does — see value_ladder.py) could
    not be checked against the studio's own bound without this direction. Its absence is
    half of why `albedo_plausible()` guards a different band in a different unit."""
    return v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


def clamp_albedo_band(rgb01):
    """Clamp an sRGB-encoded triple into the 30–240 texel band (dielectric albedo law)."""
    lo, hi = _SRGB_BAND_LO / 255.0, _SRGB_BAND_HI / 255.0
    return tuple(min(max(c, lo), hi) for c in rgb01)


def srgb_hex_to_linear_rgba(hx, clamp_band=True):
    """Author-facing helper: hex swatch -> LINEAR rgba for a Principled Base Color."""
    rgb = hex_to_srgb01(hx)
    if clamp_band:
        rgb = clamp_albedo_band(rgb)
    return tuple(srgb_to_linear(c) for c in rgb) + (1.0,)


# ---------------------------------------------------------------------------
# preset table
# ---------------------------------------------------------------------------
# factory: which build_room material factory renders it —
#   pbr | solid | painted | veneer | proc_wood | glass
# space: "srgb" (hex authored, converted+band-clamped at resolve) or "linear" (verbatim).
# trans_tint (glass only): authored LINEAR verbatim — it is a transmission tint, not a
# dielectric albedo, so neither the sRGB conversion nor the 30-240 band applies to it.
# tier:  REFERENCE (knowledge DR presets) | STUDIO (live gate-proven palette values)
#        | DESIGN-INTENT (studio-derived for a real FF&E pick; color pending SKU confirm).

PRESETS = {
    # -- REFERENCE tier: knowledge/materials/bsdf-material-presets.md:43-50 --------------
    "oak_wood_floor": dict(
        factory="pbr", slug="wood_floor", tint=None, variation=0.0, tier="REFERENCE",
        desc="warm oak plank PBR (CC0 texture set), polyurethane sheen",
        source="knowledge/materials/bsdf-material-presets.md:43"),
    "honed_marble": dict(
        factory="solid", space="srgb", hex="#EBEBEB", rough=0.55, tier="REFERENCE",
        desc="honed marble — matte/satin diffuse stone",
        source="knowledge/materials/bsdf-material-presets.md:44"),
    "polished_marble": dict(
        factory="solid", space="srgb", hex="#EBEBEB", rough=0.08, coat=0.05, tier="REFERENCE",
        desc="polished marble — low roughness, smudge-worn",
        source="knowledge/materials/bsdf-material-presets.md:45 (+ epsilon floor :54-60)"),
    "boucle_cream": dict(
        factory="solid", space="srgb", hex="#F5F0E9", rough=0.85, sheen=0.85, tier="REFERENCE",
        desc="cream bouclé upholstery — fuzzy fabric (high rough + high sheen)",
        source="knowledge/materials/bsdf-material-presets.md:46"),
    "brushed_brass": dict(
        factory="solid", space="srgb", hex="#B5A642", rough=0.40, metallic=1.0, tier="REFERENCE",
        desc="brushed brass hardware",
        source="knowledge/materials/bsdf-material-presets.md:47"),
    "polished_chrome": dict(
        factory="solid", space="srgb", hex="#F0F0F0", rough=0.04, metallic=1.0, tier="REFERENCE",
        desc="polished chrome — near-mirror",
        source="knowledge/materials/bsdf-material-presets.md:48 (+ epsilon floor :54-60)"),
    "clear_glass": dict(
        factory="glass", space="srgb", hex="#FFFFFF", rough=0.03, ior=1.52, spec=0.5,
        transmission=1.0, trans_tint=(0.92, 0.96, 0.94, 1.0), tier="REFERENCE",
        desc="clear architectural glass — Transmission 1.0, faint green thick-pane tint",
        source="knowledge/materials/bsdf-material-presets.md:49,64-65"),
    "warm_white_paint": dict(
        factory="painted", space="srgb", hex="#F5F3EE", rough=0.80, tier="REFERENCE",
        desc="matte warm-white interior wall paint (never pure white)",
        source="knowledge/materials/bsdf-material-presets.md:50"),

    # -- STUDIO tier: the LIVE legacy palette, verbatim LINEAR (selecting these renders ---
    # -- exactly what build_room hardcodes today; values from build_room.py:1120-1142) ----
    "walnut_feature": dict(
        factory="pbr", slug="wood_floor", tint=(0.40, 0.28, 0.20, 1.0), variation=0.06,
        tier="STUDIO", desc="walnut feature wall (tinted oak PBR, drift breaks repeats)",
        source="build_room.py _suite_materials (gate-proven palette)"),
    "walnut_veneer": dict(
        factory="veneer", space="linear", rgba=(0.105, 0.052, 0.026, 1.0), rough=0.45,
        tier="STUDIO", desc="rift-walnut veneer millwork, matte lacquer",
        source="build_room.py _suite_materials (gate-proven palette)"),
    "boucle_cream_studio": dict(
        factory="solid", space="linear", rgba=(0.84, 0.79, 0.71, 1.0), rough=0.92, sheen=0.8,
        tier="STUDIO", desc="cream bouclé (the live fab__ default)",
        source="build_room.py _suite_materials (gate-proven palette)"),
    "sanitary_white": dict(
        factory="solid", space="linear", rgba=(0.90, 0.91, 0.92, 1.0), rough=0.15,
        spec=0.6, coat=0.2, tier="STUDIO", desc="glossy white sanitaryware",
        source="build_room.py _suite_materials (gate-proven palette)"),
    "neutral_solid": dict(
        factory="solid", space="linear", rgba=(0.52, 0.50, 0.48, 1.0), rough=0.55,
        tier="STUDIO", desc="neutral grey-beige solid (furn__ default)",
        source="build_room.py _suite_materials (gate-proven palette)"),
    "glazing_default": dict(
        factory="glass", space="linear", rgba=(0.60, 0.76, 0.80, 1.0), rough=0.05, ior=1.45,
        spec=0.5, transmission=0.95, trans_tint=(0.86, 0.92, 0.93, 1.0), tier="STUDIO",
        desc="the live glass__ glazing (Transmission 0.95)",
        source="build_room.py _suite_materials (gate-proven palette)"),

    # -- DESIGN-INTENT tier: derived for REAL FF&E picks (PRJ-2026-002 ffe-schedule.md). --
    # -- Scatter identities follow pbr-material-behavior.md:102-106 (velvet != boucle != --
    # -- leather). COLORS are studio design-intent pending SKU color confirmation — the ---
    # -- vendor pages list multiple colorways and the schedule does not pin one. ----------
    "fabric_polyester_weave": dict(
        factory="solid", space="srgb", hex="#E8E2D6", rough=0.80, sheen=0.5,
        tier="DESIGN-INTENT",
        desc="warm off-white polyester weave (FFE-S01 Index Lamona sofa; colorway unconfirmed)",
        source="ffe-schedule.md FFE-S01 + pbr-material-behavior.md:102-106"),
    "velvet_sand": dict(
        factory="solid", space="srgb", hex="#C4A98F", rough=0.72, sheen=1.0,
        tier="DESIGN-INTENT",
        desc="warm sand velvet, directional sheen (FFE-S03 Index Teddy pair; colorway unconfirmed)",
        source="ffe-schedule.md FFE-S03 + pbr-material-behavior.md:102-106"),
    "birch_veneer": dict(
        factory="proc_wood", space="srgb", hex="#D9C29F", dark_hex="#B08D5F", rough=0.35,
        tier="DESIGN-INTENT",
        desc="light birch veneer, clear acrylic lacquer (FFE-S02 IKEA BORGEBY)",
        source="ffe-schedule.md FFE-S02"),
    "laminate_woodgrain": dict(
        factory="veneer", space="linear", rgba=(0.105, 0.052, 0.026, 1.0), rough=0.35,
        tier="DESIGN-INTENT",
        desc="woodgrain laminate door face, slight sheen (FFE-BS01 console; Formica-class)",
        source="ffe-schedule.md FFE-BS01"),
    "powder_coat_black": dict(
        factory="solid", space="srgb", hex="#262626", rough=0.45, tier="DESIGN-INTENT",
        desc="black powder-coated steel (paint film -> dielectric, Metallic 0)",
        source="ffe-schedule.md FFE-S01 legs + pbr-material-behavior.md:57"),

    # -- ELEMENT-1 palette (PRJ-2026-002 master suite, owner-signed D1/D2/D4/D6 2026-07-16). -
    # -- The de-wood anti-monopoly lever: LIGHT oak reads as the 30% secondary; a COOL wall +-
    # -- COOL microcement contrast keep Albers' warm-ground from washing the oak out; satin --
    # -- brass is the 10% accent. Source: 03_layout/element1-oak-signature-wall_DD-2026-07-16.md
    "oak_veneer": dict(
        factory="proc_wood", space="srgb", hex="#C7B896", dark_hex="#A5926B", rough=0.38,
        tier="DESIGN-INTENT",
        desc="light warm-oak veneer over MR core, satin film finish (D5-A; replaces the "
             "dark-walnut mono-timber the eye-render exposed). DESATURATED off the first "
             "build render, where a saturated amber flooded the enclosed room orange (LOOK 2026-07-16)",
        source="element1-oak-signature-wall_DD-2026-07-16.md D2/D3/D5"),
    "oak_veneer_photo": dict(
        # The SAME signed D5-A oak (#C7B896 satin 0.38) carried by a PHOTOGRAPHED veneer
        # instead of the procedural wave (P2g, D-024): the wave's bands flow continuously
        # across 90° arrises, which no real veneer lay-up can do — C2-r3 named that
        # mechanism unprompted and ranked it the frame's #1 defect. map_mean/rough_mean
        # are MEASURED on the cached 2k set (2026-08-10) so the signed colour stays the
        # albedo MEAN by construction — multiply (1.58, 2.26, 3.09), clipped pixels
        # 0.00%, p99 ≤ 0.78. tile_m = 1.83 from Poly Haven's own dimension metadata
        # (scale asserted at ingest, never assumed).
        factory="image_wood", space="srgb", hex="#C7B896", rough=0.38,
        slug="oak_veneer_01", tile_m=1.83,
        map_mean=(0.3604, 0.2117, 0.0988), rough_mean=0.5304,
        tier="DESIGN-INTENT",
        desc="signed light warm-oak (D5-A) as photographed CC0 veneer (Poly Haven "
             "oak_veneer_01), box-projected so grain breaks at panel arrises; "
             "mean-normalised to the signed #C7B896",
        source="element1-oak-signature-wall_DD-2026-07-16.md D5 + qa/open-decisions.json D-024"),
    "cool_plaster": dict(
        factory="painted", space="srgb", hex="#EAEDEF", rough=0.85, tier="DESIGN-INTENT",
        desc="matte COOL off-white limewash/plaster wall — the 60% ground kept cool so a "
             "warm wall doesn't wash the oak out (Albers, D1-A)",
        source="element1-oak-signature-wall_DD-2026-07-16.md D1-A"),
    "microcement_cool": dict(
        factory="painted", space="srgb", hex="#AEB2B2", rough=0.90, tier="DESIGN-INTENT",
        desc="cool matte microcement contrast (drawer fronts / dressing-tower back) — reads "
             "intentional against oak + black-alu glass (D6-A)",
        source="element1-oak-signature-wall_DD-2026-07-16.md D6-A"),
    "satin_brass": dict(
        factory="solid", space="srgb", hex="#C4A45C", rough=0.35, metallic=1.0,
        # BRUSHED is in this preset's own name and was never in its physics. Satin brass is
        # drawn in one direction, so its highlight is a STREAK along the grain; an isotropic
        # metal returns a round dot, which is the polished-ball look and reads as plastic.
        # The suite's whole 10% accent layer is this material (vault audit 2026-07-22).
        aniso=0.6,
        tier="DESIGN-INTENT",
        desc="satin/brushed brass hang-rail + hardware — satin hides humidity marks (D4-A; "
             "AELLA SB line, solid-vs-plated is a supplier query)",
        source="element1-oak-signature-wall_DD-2026-07-16.md D4-A"),
    # WHY #3A3C3E AND NOT "BLACK" (2026-07-16c) — kept here, NOT in `desc`: desc is fed verbatim to
    # the render-polish prompt via material_story(), so it must describe the MATERIAL, not our
    # reasoning about it. D7-B item 6 issued a BAND (#2A2C2E-#3A3C3E) precisely so "matte black"
    # could ship without a thresholds PR. Two things were wrong with what actually shipped (#1A1A1A):
    #   1. 26 sRGB is UNDER the 30-sRGB texel floor, so factory_args clamped it up to 30 — the
    #      authored number never reached a render, and a value-pin could not see that.
    #   2. The studio has TWO live albedo bands IN DIFFERENT UNITS, and item 6's arithmetic crossed
    #      them: >=30 sRGB (pbr-material-behavior.md:55) vs >=0.04 LINEAR (build_room's
    #      albedo_plausible). 0.04 linear is ~56.3 sRGB, so the issued band's LOW end (#2A2C2E = 42
    #      sRGB = 0.023 linear) does not clear both — item 6's "clears both live bands" is wrong
    #      there. Only >=57 sRGB satisfies both, i.e. the TOP of the issued band.
    # PRECISION ABOUT "clears": neither band FAILS a build. albedo_plausible only PRINTS
    # "!! albedo WARN" (the backer reaches it via the `solid` factory -> _solid), and the sRGB band
    # has no scorer wired. pbr-material-behavior.md:176-182 already logs this two-band mismatch as
    # OPEN. So the old value was not "illegal" — it warned on every render that used it, and sat
    # outside both bands while being silently clamped. This value simply needs no excuse.
    # ROUGHNESS 0.88 -> 0.82: 0.88 was the one authored number that DID reach every render. The DD
    # issued 0.75-0.85 (item 6) and 0.88 is outside it; 0.82 is mid-window. A backer this matte
    # kills the grazing sheen that separates a recess from a painted line.
    # It still READS black against oak: the darkening is done by GI/AO, which is the point — and a
    # 0,0,0 recess is the same black-hole defect the designer circled on our own render.
    "matte_black_ply": dict(
        factory="solid", space="srgb", hex="#3A3C3E", rough=0.82, tier="DESIGN-INTENT",
        desc="near-black slightly-cool matte backer behind the slat battens — the dark ground the "
             "shadow-gaps read against, so the module reads as slats and not as a flat panel "
             "(D2-A backing, delivered by AKUWALL's own black backing)",
        source="element1-oak-signature-wall_DD-2026-07-16.md D2-A backing + D7-B item 6"),

    # -- ELEMENT-2 palette (PRJ-2026-002 master suite WEST wall, 2026-07-17). The west wall is the
    # -- COOL counterpoint to the warm oak signature: a Caesarstone vanity counter + a frameless
    # -- makeup mirror (NO brass frame — PH-02, the two flanking windows are the luminance point).
    # -- Source: element2-west-wall_DD-2026-07-17.md.
    "caesarstone_quartz": dict(
        factory="solid", space="srgb", hex="#BFC3C4", rough=0.28, spec=0.5, coat=0.08,
        tier="DESIGN-INTENT",
        desc="cool engineered-quartz vanity counter (Caesarstone honed cool grey, Alpine Mist / "
             "Symphony Grey family) — durable, non-porous, the cool contrast under the makeup station",
        source="element2-west-wall_DD-2026-07-17.md D2-4 + caesarstone-engineered-stone-th.md"),
    "mirror_silver": dict(
        factory="solid", space="srgb", hex="#EAEDEE", rough=0.03, metallic=1.0,
        tier="DESIGN-INTENT",
        desc="frameless silvered makeup mirror (metallic near-mirror) — NO brass frame, the two "
             "flanking windows are the luminance point (PH-02 brightness-ordering)",
        source="element2-west-wall_DD-2026-07-17.md D2-3 + render-defects.md#L51"),
}


# ---------------------------------------------------------------------------
# CLOTH SURFACE SIGNATURE (pure data) — what separates a textile from a slab
# ---------------------------------------------------------------------------
# THE DEFECT THIS EXISTS FOR. `build_room._solid` is documented "Clean physically-
# plausible Principled material (NO TEXTURE)" (build_room._solid) and EVERY textile
# in the suite is built with it. So fabric was the only surface class in the build with a
# perfectly uniform albedo: the floor carries variation=0.05, the walls carry _painted's
# three non-uniformities, the millwork carries _veneer's grain — and the bed base, the
# coverlet, the bench, the towels and 63 hanging garments carried none. That is MA-05 in
# the studio's own taxonomy, "Plastic look — missing micro-imperfections", recorded there
# as "the corpus's canonical late-denoising-stage textural error"
# (knowledge/classifications/render-defects.md:69), and the red flag "flat single-colour
# surfaces without PBR normal maps" (knowledge/classifications/qa-dimensions.md:286-287).
# It is also element 3's signed D3-2 only half-built: that decision asks for
# "micro-imperfections (wrinkle/pilling) so it reads used, not synthetic-smooth"
# (element3-bed_DD-2026-07-18.md:92-94, from knowledge/styles/color-composition.md:189-190).
#
# WHY THESE ARE PARAMETERS AND NOT A PHOTO. Three spatial bands make cloth read as cloth:
# sub-mm fibre fuzz (that is what Sheen already IS), ~10-40 mm slub/crease/pilling, and
# 100 mm+ folds (drape.py solves those). Only the MIDDLE band was missing. A photographic
# weave map cannot supply it: at a real thread pitch the map is minified to tens of texels
# per pixel at room distance and Cycles averages it to a flat colour — measured, not
# assumed (probe 2026-07-22: an image pushed to fabric pitch returned an identical constant
# across Object/Generated/FLAT/BOX coordinates). It would also trip MA-02 (scale) and MA-03
# (tiling), and the fabric objects carry no UV at all (see the "carry no UV, the texture
# samples ONE flat texel" WARN in build_room._suite_materials). So the
# signature is PROCEDURAL and world-space, the same choice _veneer made when the round-1
# gate proved a plank PHOTO on millwork read as "flooring on the walls" while procedural
# grain helped (build_room._veneer's docstring).
# (Line-number citations into build_room are deliberately avoided here: the first draft
# carried three, and the same change that wrote them shifted two — pre-commit review catch.)
#
# TIER OF THESE NUMBERS. The vault has NO weave repeat size in metres, NO fabric bump
# strength and NO Blender-side sheen roughness — three confirmed GAPs. So every value here
# is [est] studio-default, bounded by the two things the vault DOES supply:
#   * sheen_rough: the only sourced band anywhere is Corona's fabric cards, Sheen Roughness
#     0.4-0.6 (knowledge/materials/texture-sets-discord.md:170-195, "Fabric = Sheen +
#     Falloff"). Unlike that file's Bump numbers — which it explicitly forbids porting
#     ("Bump is NOT 0-1 here … Do not paste those into a Blender bump Strength", :210-225) —
#     sheen roughness is a 0-1 quantity in both engines, so the band transfers.
#   * bump: set by LOOK, and the first cut was WRONG. It was written at 0.30 to stay in the
#     same order as the repo's proven wood bumps (_veneer 0.08, _painted 0.05, _proc_wood
#     0.10) — and the render at those values was INDISTINGUISHABLE from the flat slab it
#     replaced. That is not a tuning miss, it is physics: this room is lit by soft ambient
#     plus a wall wash, and under near-isotropic illumination tilting a normal barely
#     changes the shading integral, so a physically-honest 1.4 mm slub over 28 mm returns
#     ~1.5% and disappears. An amplitude bisect (render weave01 vs weaveLOUD, 2026-07-22)
#     bracketed it: 0.30 invisible, 0.85 clearly read but coarse enough that the bench
#     started reading as towelling. That bisect ran at ONE uniform value, so its verdicts
#     are per-FABRIC, not global: "coarse" was the BENCH — linen — which is why linen ships
#     0.65. The vocabulary therefore spans the whole bracket ON PURPOSE (velvet 0.30, plain
#     0.45, linen 0.65, terry 0.80, boucle 0.85): towelling IS terry's correct read and
#     loops are boucle's, while velvet ships at the "invisible" end because its identity is
#     directional sheen and relief on velvet is MA-01 scatter mismatch. No row is a safety
#     margin off a single global number — an earlier draft of this comment claimed "~70% of
#     the loud end", which is true only of the MEAN and of no material actually rendered.
#     So: bump is a RENDER GAIN, not a physical claim — relief_mm is the physical claim,
#     and it stays in the real 1-4 mm band cloth actually occupies.
# relief_mm is the Bump node's Distance (a real height in mm), stated rather than derived
# so nobody has to reverse a magic ratio to know what surface is being claimed.
#
# scatter identity is a studio QA rule, not decoration: "each material's scatter signature
# is distinct: leather rendered with velvet's fuzzy diffuse scattering = material mismatch
# -> regeneration" (knowledge/materials/pbr-material-behavior.md:102-106, MA-01). That is
# why linen, terry, boucle and velvet get DIFFERENT rows instead of one "fabric" row.
CLOTH_KINDS = {
    # slub_mm  = the meso band that actually resolves at eye distance (crease/slub/pill)
    # weave_mm = the thread-scale band; sub-pixel at room distance, it breaks the specular
    # relief_mm= Bump Distance, the claimed physical height of that relief
    # bump      = Bump Strength (0-1)
    # albedo_var= peak luminance drift of the multiply (the MA-03/MA-05 cure, cf floor 0.05)
    # sheen_rough = Principled Sheen Roughness (Corona band 0.4-0.6)
    "linen": dict(slub_mm=26.0, weave_mm=5.0, relief_mm=2.6, bump=0.65,
                  albedo_var=0.085, sheen_rough=0.50,
                  desc="stonewashed linen — long soft slubs, a dry matte break-up"),
    "terry": dict(slub_mm=14.0, weave_mm=4.0, relief_mm=3.2, bump=0.80,
                  albedo_var=0.100, sheen_rough=0.55,
                  desc="cotton terry — short dense pile, the loosest surface in the suite"),
    # `desc` is fed VERBATIM to the render-polish prompt through material_story(), so it
    # must describe the MATERIAL and never our reasoning about it — the rule this file
    # already states for PRESETS' desc (see the #3A3C3E note). Provenance and the
    # why-this-number argument live in `source`, which cloth_args() does not pass on.
    "boucle": dict(slub_mm=9.0, weave_mm=4.5, relief_mm=3.6, bump=0.85,
                   albedo_var=0.110, sheen_rough=0.45,
                   desc="wool boucle — looped nubs, a soft irregular surface",
                   source="bsdf-material-presets.md:46 'normal/displacement for loops' — "
                          "the studio's one sourced fabric row"),
    "velvet": dict(slub_mm=40.0, weave_mm=1.2, relief_mm=1.0, bump=0.30,
                   albedo_var=0.050, sheen_rough=0.40,
                   desc="velvet — a near-smooth pile with a directional sheen",
                   source="identity is SHEEN, not relief; over-bumping velvet is MA-01 "
                          "scatter mismatch (pbr-material-behavior.md:102-106)"),
    "plain": dict(slub_mm=22.0, weave_mm=3.0, relief_mm=1.8, bump=0.45,
                  albedo_var=0.065, sheen_rough=0.50,
                  desc="plain synthetic weave — flat, tight, the least tactile row"),
}

# Which PRESET wears which cloth signature. A preset absent here is not cloth.
PRESET_CLOTH = {
    "boucle_cream": "boucle",
    "boucle_cream_studio": "boucle",
    "fabric_polyester_weave": "plain",
    "velvet_sand": "velvet",
}


def cloth_args(kind):
    """The Principled/relief parameters for a cloth identity, in METRES for the build.

    Raises on an unknown kind for the usual reason: the silent fallback is the
    revert-by-omission channel (cf FIXTURE_MAT_OBJECT), and here the fallback would be
    a flat plastic slab that no test can see."""
    k = CLOTH_KINDS.get(str(kind))
    if k is None:
        raise ValueError(f"unknown cloth kind {kind!r} — known: {sorted(CLOTH_KINDS)}. "
                         f"Add a CLOTH_KINDS row rather than letting a textile fall back "
                         f"to the untextured _solid slab (MA-05).")
    return {"slub_m": k["slub_mm"] * 0.001, "weave_m": k["weave_mm"] * 0.001,
            "relief_m": k["relief_mm"] * 0.001, "bump": k["bump"],
            "albedo_var": k["albedo_var"], "sheen_rough": k["sheen_rough"],
            "kind": str(kind)}


def preset_cloth_kind(preset_name):
    """The cloth identity a preset wears, or None if the preset is not a textile."""
    return PRESET_CLOTH.get(_known(preset_name))


# ---------------------------------------------------------------------------
# build-layer helpers (pure) — routing + the ceiling-CCT override
# ---------------------------------------------------------------------------
# build_room lives in the bpy layer and cannot be imported under plain python, so the two bits
# of build-layer LOGIC that are worth pinning live here (pure, testable): the mill__ object ->
# material role router, and the light_warm parse+validate. build_room calls both.

def mill_object_role(objname):
    """Which material a `mill__*` object gets: 'brass' | 'microcement' | 'backing' | 'oak'.

    A millwork PART is named `mill__<name>__<pn>` and routes on its trailing part token <pn>. The
    plain-box FALLBACK is `mill__<name>` with NO second '__' — its remainder is the builtin's
    free-text (space-normalized) name, which must NOT be pattern-matched (a cabinet literally named
    'front console' would otherwise be painted microcement). So a name with no part token is oak.
    (Review 2026-07-16: the earlier `rsplit('__',1)[-1]` router mis-painted such fallback boxes.)"""
    if not objname.startswith("mill__"):
        return "oak"
    rest = objname[len("mill__"):]
    if "__" not in rest:
        return "oak"                                   # plain fallback box: name is not a part token
    pn = rest.rsplit("__", 1)[-1]
    if "." in pn and pn.rsplit(".", 1)[1].isdigit():
        # Blender DUPLICATE-NAME suffix (.001/.002): a name collision silently renames
        # the object, and the exact-match tokens below (towel/opal/blackalu) would fall
        # through to the oak default — the same silent-walnut channel the e5 task bar
        # fell down (review 2026-07-21; the startswith tokens survive it by accident).
        pn = pn.rsplit(".", 1)[0]
    if pn.startswith("rail") or pn.startswith("brass"):
        return "brass"                                 # brass rail (el-1) + el-4 ensuite tapware/fittings
    if pn.startswith("counter"):
        return "caesarstone"                           # element-2 Caesarstone vanity top (D2-4)
    if pn.startswith("mirror"):
        return "mirror"                                # element-2 frameless makeup mirror (D2-3)
    if pn == "opal":
        return "opal"                                  # element-5 luminous opal face (task strips/bar)
    if pn == "blackalu":
        return "blackalu"                              # element-5 black-alu luminaire body (D-E5-4/-5)
    if pn == "linen":
        # ELEMENT 8: the greige stonewashed linen signed in element 3 (D3-1/D3-4), finally
        # reachable BY NAME. EXACT-match like `towel` and for the same reason: the closed
        # fixture gate is one layer up and does not protect this router, so without this
        # branch every sham, folded stack and hanging garment falls through to the oak
        # default below and build_room's .get(_role, mill) ships soft goods in WALNUT.
        return "linen"
    if pn == "towel":
        # element-6 terry textiles (towels + bath mat, ONE token — D-E6-3). This branch is
        # REQUIRED, not decorative: the closed fixture_part_name gate is one layer UP and
        # does not protect this router — without this line every towel falls through to
        # the `return "oak"` below and build_room's .get(_role, mill) ships it in WALNUT
        # veneer with NO raise (the buildability verifier's catch, DD build-consequence 9).
        return "towel"
    if pn.startswith("cool"):
        return "microcement"                           # element-2 cool carcass/gables/toe (anti-monopoly)
    if "front" in pn or pn.startswith("towerback"):
        return "microcement"
    if pn.endswith("mineral"):
        # A terminal member that DECLARES mineral intent (millwork.terminal_part_name, named from
        # the spec's schedule). PRJ-2026-002 D7 = MINERAL RELEASE: BF14's south end is cool
        # microcement, the north end is oak into oak — a JOINT, because BF09-3 receives it — so
        # `postoak` falls through to oak below. The asymmetry IS the decision: one end is received,
        # the other released. This router is GLOBAL, so it must never read "a jamb is mineral" out
        # of a part's FUNCTION — only out of what the project's spec asked for.
        return "microcement"
    if pn.startswith("backer"):
        return "backing"                               # dark backer behind the slats (D2-A)
    return "oak"


# The CLOSED mat->object-name vocabulary for ensuite fixture parts (bathroom.py `mat`
# roles -> the SAME suite materials by NAME; consumed by build_room._add_ensuite via
# fixture_part_name). Every mat a massing module may emit MUST have a row here — the
# router refuses the rest. Until 2026-07-21 the router ended in a silent oak default:
# that default is how the e5 task bar rendered OAK (blackalu/opal had no branch, LOOK
# caught it 2026-07-20), and the director review predicted the e6 textile roles would
# repeat it as the 7th revert-by-omission. A new mat now RAISES at build time instead
# of quietly wearing oak.
FIXTURE_MAT_OBJECT = {
    "porcelain": "fix__{b}",              # cool white sanitaryware
    "glass":     "glass__{b}",            # frameless clear glass -> glazing material
    "stone":     "mill__{b}__counter",    # Caesarstone counter / tub deck
    "brass":     "mill__{b}__brass",      # satin-brass tapware/fittings
    "mirror":    "mill__{b}__mirror",     # silver frameless mirror
    "blackalu":  "mill__{b}__blackalu",   # element-5 luminaire body (task bar)
    "opal":      "mill__{b}__opal",       # element-5 luminous opal face
    "tray":      "mill__{b}__cool",       # shower tray/curb -> cool microcement
    "towel":     "mill__{b}__towel",      # element-6 greige-oatmeal terry (towels + bath mat)
    "mineral":   "mill__{b}__cool",       # element-7 bay wardrobe fronts/carcass -> the EXISTING
                                          #   microcement identity via the proven __cool token
                                          #   (same route as 'tray'; D-E7-3/-4 — zero oak, zero
                                          #   brass in the bay; no new material plumbing)
    "oak":       "mill__{b}",             # the ONE warm-oak gesture (default mill role)
}


def fixture_part_name(mat, base):
    """Object name for an ensuite fixture part, routing its `mat` role to a suite
    material by NAME (coherence: the render reuses the exact oak / caesarstone / brass /
    sanitary / glass materials instead of inventing a tone). CLOSED vocabulary — an
    unknown mat raises, because the silent fallback is precisely the revert-by-omission
    channel (see FIXTURE_MAT_OBJECT)."""
    fmt = FIXTURE_MAT_OBJECT.get(str(mat))
    if fmt is None:
        raise ValueError(
            f"fixture part {base!r}: unknown mat role {mat!r} — not in the closed "
            f"vocabulary {sorted(FIXTURE_MAT_OBJECT)}. Add a FIXTURE_MAT_OBJECT row "
            f"(and a suite material branch) instead of letting it default to oak.")
    return fmt.format(b=str(base).replace(" ", "_"))


_DEFAULT_LIGHT_WARM = (1.0, 0.82, 0.60)                 # gate-proven 2400 K amber (build_room legacy)


def parse_light_warm(spec):
    """spec['light_warm'] -> a validated (r,g,b) tuple in [0,1], or the DEFAULT amber when absent.

    A PRESENT value must be a 3-sequence of numbers each in [0,1] — anything else RAISES (fail loud
    at parse time, not a cryptic IndexError deep in the light loop, nor a silently truncated 4-tuple,
    nor an unclamped 2.0 channel; review 2026-07-16). No block -> the legacy amber, byte-identical."""
    lw = (spec or {}).get("light_warm")
    if lw is None:
        return _DEFAULT_LIGHT_WARM
    try:
        vals = [float(c) for c in lw]
    except (TypeError, ValueError):
        raise ValueError(f"light_warm must be a 3-number [r,g,b] sequence, got {lw!r}")
    if len(vals) != 3:
        raise ValueError(f"light_warm must have exactly 3 channels, got {len(vals)}: {lw!r}")
    if not all(0.0 <= c <= 1.0 for c in vals):
        raise ValueError(f"light_warm channels must be in [0,1], got {vals}")
    return tuple(vals)

ALLOWED_SURFACES = ("floor", "walls", "feature_wall", "millwork", "glazing", "fixtures")
ALLOWED_FAMILIES = ("fabric", "wood", "neutral")
_ALLOWED_TOP = ("schema", "note", "surfaces", "families", "elements")


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------

def resolve_materials(spec):
    """spec dict -> {"surfaces": {...}, "families": {...}, "elements": {...}} or None.

    None == no materials block == the legacy hardcoded palette (backward compatible).
    ValueError on ANY unknown key or preset name — fail loud, never a silent default.
    Type check runs BEFORE the falsy short-circuit: "materials": [] / false / "" / 0 are
    INVALID (a generator emitting the wrong shape must not silently render the default
    palette — review finding 2026-07-14); only absence, null and {} mean 'no selections'."""
    if not spec or "materials" not in spec:
        return None
    block = spec["materials"]
    if block is None or block == {}:
        return None
    if not isinstance(block, dict):
        raise ValueError(f"materials block must be an object, got {type(block).__name__}")
    for k in block:
        if k not in _ALLOWED_TOP:
            raise ValueError(f"materials: unknown key {k!r} (allowed: {_ALLOWED_TOP})")
    out = {"surfaces": {}, "families": {}, "elements": {}}
    for k, v in (block.get("surfaces") or {}).items():
        if k not in ALLOWED_SURFACES:
            raise ValueError(f"materials.surfaces: unknown surface {k!r} (allowed: {ALLOWED_SURFACES})")
        out["surfaces"][k] = _known(v)
    for k, v in (block.get("families") or {}).items():
        if k not in ALLOWED_FAMILIES:
            raise ValueError(f"materials.families: unknown family {k!r} (allowed: {ALLOWED_FAMILIES})")
        out["families"][k] = _known(v)
    for k, v in (block.get("elements") or {}).items():
        out["elements"][str(k)] = _known(v)
    return out


def _known(preset_name):
    if preset_name not in PRESETS:
        raise ValueError(f"unknown material preset {preset_name!r} "
                         f"(known: {', '.join(sorted(PRESETS))})")
    return preset_name


def element_preset(resolved, name, kind):
    """Per-piece preset for an item: exact `name` match wins, then `kind`. None if neither."""
    if not resolved:
        return None
    els = resolved.get("elements") or {}
    return els.get(str(name)) or els.get(str(kind))


# item kinds whose geometry is built by bespoke builders (_build_bed/_build_bench/_add_rug)
# whose parts carry ph_model/rug__ routing — an element preset CANNOT reach them today.
UNAPPLIABLE_KINDS = ("bed", "bench", "rug")


def bespoke_built(it):
    """True when build_room hands this ITEM to a bespoke builder the per-element preset
    path can never reach: the UNAPPLIABLE kinds (_build_bed/_build_bench/_add_rug), a
    lamped side_table (_build_nightstand — the element-3 latent flag), and the
    tub-chair stool (_build_tub_chair, whose parts carry ph_model and skip the material
    pass entirely). reconcile_elements refuses these so a materials.elements key can
    never silently no-op (scrutiny 2026-07-21 closed the two intercepted shapes)."""
    k = str(it.get("kind", ""))
    if k in UNAPPLIABLE_KINDS:
        return True
    if k == "side_table" and it.get("lamp"):
        return True
    if k == "stool" and it.get("style") == "tub_chair":
        return True
    return False


def element_appliable(preset_name):
    """(ok, why) — can this preset be applied PER-ELEMENT? Element application goes
    through the flat-colour retint path (imported models) or an em- solid material
    (primitive fallback), so it needs a flat dielectric colour: metals would lose
    Metallic, glass would lose Transmission, and a texture-set (pbr) preset has no
    flat colour at all — each of those must fail LOUD, not render a beige lie
    (review findings 9/15/16, 2026-07-14)."""
    a = factory_args(preset_name)
    if a["factory"] in ("pbr", "glass"):
        return False, (f"'{preset_name}' is a {a['factory']} preset — per-element "
                       f"application is flat-colour only (use a solid/painted/veneer/"
                       f"proc_wood preset, or a surface/family role instead)")
    if a.get("metallic") == 1.0:
        return False, (f"'{preset_name}' is a metal — the per-element retint path drops "
                       f"Metallic (solid metal would render as paint); not supported")
    return True, ""


def reconcile_elements(resolved, spec):
    """Prove every materials.elements key WILL bind and CAN apply, BEFORE building.

    Raises ValueError when a key matches no item (name or kind), when the matched
    item's kind is UNAPPLIABLE (bespoke builders the presets cannot reach), or when
    the preset itself is not element-appliable. This is the anti-silent-drop gate:
    material_story() reports every selection as the render's truth, so a selection
    that cannot land must abort the build, never ship a render whose story lies
    (review findings 1/3/4/8/9/14/18, 2026-07-14). Returns the matched {key: [item
    names]} map for logging. No-op (returns {}) when there are no element selections."""
    els = (resolved or {}).get("elements") or {}
    if not els:
        return {}
    items = list((spec or {}).get("items") or [])
    matched = {}
    for key in els:
        hits = [it for it in items
                if str(it.get("name") or it.get("kind", "")) == key
                or str(it.get("kind", "")) == key]
        if not hits:
            names = [str(it.get("name") or it.get("kind", "?")) for it in items]
            raise ValueError(f"materials.elements key {key!r} matches NO item by name or "
                             f"kind (items: {names}) — a selection that cannot bind must "
                             f"fail loud, not silently render the default palette")
        bad = [it for it in hits if bespoke_built(it)]
        if bad:
            raise ValueError(f"materials.elements key {key!r} targets "
                             f"'{bad[0].get('kind')}' (lamp={bool(bad[0].get('lamp'))}, "
                             f"style={bad[0].get('style')!r}) — built by a bespoke builder "
                             f"the preset cannot reach (see bespoke_built)")
        ok, why = element_appliable(els[key])
        if not ok:
            raise ValueError(f"materials.elements[{key!r}]: {why}")
        matched[key] = [str(it.get("name") or it.get("kind", "?")) for it in hits]
    return matched


def factory_args(preset_name):
    """Preset -> the concrete factory + LINEAR params build_room feeds its material
    factories. All authoring bounds are enforced HERE (band clamp, rough floor/ceil,
    binary metalness) so no caller can leak an implausible value into a render."""
    p = PRESETS[_known(preset_name)]
    a = {"factory": p["factory"], "preset": preset_name, "tier": p["tier"], "desc": p["desc"]}
    metallic = float(p.get("metallic", 0.0))
    if metallic not in (0.0, 1.0):
        raise ValueError(f"{preset_name}: metalness must be binary 0/1 (got {metallic})")
    if p["factory"] == "pbr":
        a["slug"] = p["slug"]
        a["tint"] = p.get("tint")
        a["variation"] = float(p.get("variation", 0.0))
        return a
    if p["factory"] == "image_wood":
        # explicit branch, not the generic tail: the whitelist below SILENTLY DROPS
        # unknown keys (its own comment says so), and slug/tile_m/map_mean are the
        # material — losing them quietly would render the fallback and look like a
        # texture bug. Same fail-shape the aniso note at that whitelist records.
        a["rgba"] = srgb_hex_to_linear_rgba(p["hex"], clamp_band=True)
        a["rough"] = min(max(float(p["rough"]), ROUGH_FLOOR), ROUGH_CEIL)
        a["metallic"] = 0.0
        a["slug"] = p["slug"]
        a["tile_m"] = float(p["tile_m"])
        a["map_mean"] = tuple(p["map_mean"])
        if "rough_mean" in p:
            a["rough_mean"] = float(p["rough_mean"])
        return a
    # dielectric albedo band applies to sRGB-authored non-metal, non-glass presets
    exempt = metallic == 1.0 or p["factory"] == "glass"
    if p.get("space") == "linear":
        a["rgba"] = tuple(p["rgba"])
    else:
        a["rgba"] = srgb_hex_to_linear_rgba(p["hex"], clamp_band=not exempt)
    if "dark_hex" in p:
        a["dark"] = srgb_hex_to_linear_rgba(p["dark_hex"], clamp_band=not exempt)
    a["rough"] = min(max(float(p["rough"]), ROUGH_FLOOR), ROUGH_CEIL) if "rough" in p else 0.5
    a["metallic"] = metallic
    # A key absent from this tuple is SILENTLY DROPPED — a preset can declare it, the
    # authoring bounds can pass it, and the render never sees it. `aniso` was added to
    # satin_brass on 2026-07-22 and would have vanished here. Extend this list whenever a
    # preset gains a channel.
    for k in ("sheen", "coat", "ior", "spec", "transmission", "aniso"):
        if k in p:
            a[k] = float(p[k])
    if "trans_tint" in p:
        a["trans_tint"] = tuple(p["trans_tint"])
    # CLOTH: a textile preset carries its surface signature so the build renders a weave
    # instead of a painted slab (see CLOTH_KINDS). The membership test is the preset's OWN
    # physics, not its name: in this table a non-metal `solid` with a Sheen weight IS a
    # textile — Sheen is the fibre-fuzz lobe and nothing else in the palette uses it. So a
    # future fabric preset cannot be added WITHOUT a cloth row; it raises here rather than
    # silently shipping the flat-plastic look this block exists to kill (the same fail-loud
    # shape as FIXTURE_MAT_OBJECT's closed vocabulary).
    if p["factory"] == "solid" and float(p.get("sheen", 0.0)) > 0.0 and metallic == 0.0:
        kind = PRESET_CLOTH.get(preset_name)
        if kind is None:
            raise ValueError(
                f"{preset_name!r} is a sheen-bearing solid (sheen={p['sheen']}) — i.e. a "
                f"TEXTILE — but has no PRESET_CLOTH row, so it would render as an "
                f"untextured slab (MA-05 'plastic look', "
                f"knowledge/classifications/render-defects.md:69). Add a PRESET_CLOTH "
                f"entry naming one of {sorted(CLOTH_KINDS)}.")
        a["cloth"] = cloth_args(kind)
    return a


# What build_room._suite_materials hardcodes for millwork SUB-PARTS and routes by part token
# (mill_object_role). No `surfaces` key selects these, so `resolved` never mentions them.
_MILL_SUBPART = (
    ("brass", "satin_brass", "millwork hardware"),
    ("microcement", "microcement_cool", "millwork mineral accents"),
    ("backing", "matte_black_ply", "slat backer"),
    ("caesarstone", "caesarstone_quartz", "vanity counter"),   # ELEMENT 2 (west vanity top)
    ("mirror", "mirror_silver", "makeup mirror"),              # ELEMENT 2 (frameless mirror)
)


def millwork_subpart_presets(spec):
    """Which sub-part presets a spec's BUILT-INS actually put on screen. Returns [(label, preset)].

    Without this, material_story tells the polish pass "millwork: oak" while the render shows brass
    hang-rails, cool-microcement drawer fronts and a mineral terminal jamb — and a repaint told the
    millwork is oak will happily 'correct' them to oak. The render's stated truth must not contradict
    the render: that is the same failure class as the slat backer that once rendered oak against a
    signed matte-black ply, one step downstream. ELEMENT 2 (2026-07-17): a `vanity` builtin puts a
    Caesarstone counter on screen (and, when its design carries a `mirror` block, a silver frameless
    mirror) — both mill__ objects the polish pass would otherwise warm/repaint (the review caught the
    cool counterpoint reverting to oak)."""
    roles = set()
    for b in (spec or {}).get("builtins") or []:
        if b.get("open"):
            roles.update(("brass", "microcement"))      # hang-rails + drawer fronts / tower back
        if b.get("kind") == "headboard":
            roles.add("backing")                        # the battens' dark ground
        if b.get("kind") == "vanity":
            roles.add("caesarstone")                    # the cool quartz counter (element 2 D2-4)
            roles.add("microcement")                    # cool drawer fronts + body/toe
            if (b.get("design") or {}).get("mirror"):
                roles.add("mirror")                     # the frameless makeup mirror (element 2 D2-3)
        sched = ((b.get("design") or {}).get("schedule")) or {}
        for k in ("post_south_material", "post_north_material"):
            if str(sched.get(k, "")).strip().lower() == "microcement":
                roles.add("microcement")                # e.g. PRJ-2026-002 D7's mineral release
    return [(label, preset) for role, preset, label in _MILL_SUBPART if role in roles]


def furniture_material_story_bits(spec):
    """The DECIDED FF&E materials that bespoke builders (_build_bed / _build_nightstand / _add_rug)
    put on screen but the preset families do NOT name — so material_story can STATE them and the
    Gemini polish pass cannot repaint them (the recurring element-2 trap: a cool counter reverting
    to oak; here the bed base repainted oak, the brass lamps dropped). DATA-driven from the spec
    items (D7: a decided element must not be revertible by an omission). Returns [str]."""
    bits = []
    items = (spec or {}).get("items") or []
    bed = next((it for it in items if it.get("kind") == "bed"), None)
    if bed and (bed.get("design") or {}).get("base_material") == "upholstered_greige_linen":
        # 2026-07-23: "a mid-greige plinth" was measured and it was not one — the plinth,
        # the foot throw and the bench all wear this cloth and rendered 121 / 155 / 178,
        # with the bench ABOVE the coverlet it stands in front of. The cloth is now the
        # ladder's DEEPEST rung, so the adjective changes with it rather than outliving it.
        bits.append("bed base + foot bench + foot throw: upholstered greige stonewashed linen "
                    "— matte, and the DEEPEST value in the room's soft goods: it grounds the "
                    "bed and keeps the foreground below the bedding behind it; NOT oak "
                    "(D1-A anti-monopoly), and NOT to be lifted toward the bedding")
    if any(it.get("kind") == "side_table" and it.get("lamp") for it in items):
        bits.append("nightstands: matte-dark low cabinets, each with a brass dome/'mushroom' table "
                    "lamp — the 10% brass accent, dim vs the garden windows (PH-02)")
    if any(it.get("kind") == "rug" for it in items):
        bits.append("rug: soft neutral poly-wool herringbone under the bed (demotes the oak floor "
                    "to the 30% layer, D1-A)")
    if any(it.get("kind") == "stool" and it.get("style") == "tub_chair" for it in items):
        bits.append("vanity tub-chair: upholstered greige stonewashed linen wrap-back seat "
                    "(SAME textile family as the bed base + bench) on slim dark legs — "
                    "NOT oak, NOT cream")
    return bits


def ensuite_material_story_bits(spec):
    """ELEMENT 4 (D-E4-1, element4-ensuite_DD-2026-07-18.md): the ensuite's decided
    materials, NAMED. Until 2026-07-21 the ensuite contributed NOTHING to material_story
    — its fixtures are subroom fixtures, not builtins, so no existing helper saw them —
    and the polish pass would read a room of unexplained white/grey/oak boxes and unify
    it toward the bedroom's warmth (the director review flagged this hole as the 7th
    revert-by-omission, aimed through the polish prompt). DATA-driven on the bathroom
    subroom + its fixture kinds. The GROUND bit discloses honestly that the clay control
    does NOT show the decided porcelain (the shell renders the bedroom's wall/floor
    materials); the finish lives here and in the Gemini pass, per the hybrid law."""
    bath = next((s for s in (spec or {}).get("subrooms") or []
                 if s.get("type") == "bathroom"), None)
    if not bath:
        return []
    kinds = {str(f.get("kind", "")) for f in bath.get("fixtures") or []}
    bits = ["ensuite ground (D-E4-1 reverse-Albers): large-format cool-grey porcelain "
            "tile on the wet floor + wet walls, cool microcement on dry walls — the clay "
            "control still shows the bedroom's plaster walls and oak floor running "
            "through the ensuite; FINISH that ground as cool porcelain, never warm/oak "
            "it (the vanity must stay the room's only warmth)"]
    frags = []
    if kinds & {"vanity_double", "vanity"}:
        frags.append("ONE low floating warm light-oak vanity (the ensuite's only oak, "
                     "~6%) under a cool Caesarstone counter + west ledge, twin white "
                     "porcelain vessel basins, satin-brass taps, full-width frameless "
                     "mirror above")
    if kinds & {"toilet", "bathtub"}:
        frags.append("white porcelain sanitaryware (WC; deck tub shell under a cool "
                     "stone deck with a satin-brass deck filler)")
    if kinds & {"shower", "glass_partition"}:
        frags.append("frameless clear-glass shower screen + wet/dry partition, cool "
                     "microcement tray/curb, satin-brass shower fittings")
    if frags:
        bits.append("ensuite fixtures: " + ", ".join(frags))
    # ELEMENT 6 (D-E6-2): the BARE ruling, gated on the ensuite's own casements existing
    # (both spec copies carry the DECIDED BARE note; a Gemini shower-curtain is the only
    # revert channel left — this line arms the polish prompt against it).
    if any(o.get("type") in ("window", "glass")
           for o in bath.get("openings") or []):
        bits.append("ensuite casements: BOTH shower casement windows are BARE black-alu "
                    "(D-E6-2 DECIDED) — the garden through them is the wet-side "
                    "coherence carrier; NO curtain, blind, or fabric at these windows "
                    "(never add a shower curtain)")
    # ELEMENT 6 (D-E6-3/-4/-5): the textiles, DERIVED from the accessories fixture's
    # design.census — the DD's ONE source for emitters + story bit + LOOK (review
    # 2026-07-21 caught the first cut hardcoding "2 bath towels": the 18in-fallback
    # census edit would have built ONE towel while this prose told the Gemini polish
    # to paint the second back). A censusless/zero fixture contributes NO counted
    # prose (the emitter RAISES on it — the story must not promise what cannot
    # build). Greige-vs-cream is TONAL (LOOK: greige must not read cream under the
    # warm lamps); the closing clause is the wet/dry law's anti-trope armour (D-E6-5).
    acc = next((f for f in bath.get("fixtures") or []
                if str(f.get("kind", "")) == "bath_accessories"), None)
    if acc is not None:
        census = ((acc.get("design") or {}).get("census")) or {}
        def _n(key):
            v = census.get(key, 0)
            return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else 0
        clauses = []
        if _n("bath_on_bar"):
            n = _n("bath_on_bar")
            clauses.append(f"{n} bath towel{'s' if n != 1 else ''} folded over the "
                           "satin-brass Purist bar on the west wall")
        if _n("hand_on_south_hook"):
            clauses.append("a hand towel on the south door-jamb hook")
        if _n("hand_on_counter"):
            clauses.append("a hand towel folded on the counter between the basins")
        if _n("robes_on_north_hook"):
            n = _n("robes_on_north_hook")
            clauses.append(f"{n} robe{'s' if n != 1 else ''} double-hung on the north "
                           "jamb hook")
        if _n("bath_mat"):
            clauses.append("ONE flat greige mat at the shower entry in the drawn dry "
                           "strip")
        if clauses:
            bits.append("ensuite textiles: greige-oatmeal TERRY (the suite's one linen "
                        "family extended; greige, NOT cream) — " + ", ".join(clauses)
                        + "; the oak vanity stays the room's only warmth; no towel "
                        "over the glass or tub edge")
    return bits


def casement_sheer_story_bits(spec):
    """ELEMENT 6 (D-E6-1, element6-textiles_DD-2026-07-21.md): the west casement
    sheers, NAMED so the Gemini polish pass cannot strip them (bare-glass 'cleanup'),
    park them, or dress the mirror pier between them (the revert-by-omission class,
    fabric flavor). Spec-gated on the casement_sheers block; alpha read from the same
    ONE source the build reads (curtains.render_state), defaulted softly here because
    this is prose — the BUILD path fails loud in casement_sheers.sheer_alpha."""
    cs = (spec or {}).get("casement_sheers")
    wins = (cs or {}).get("windows") or {}
    if not wins:
        return []
    alpha = ((spec.get("curtains") or {}).get("render_state") or {}).get("sheer_alpha", 0.38)
    return [f"casement sheers: {len(wins)} sill-length cool off-white linen-look sheer "
            f"panel(s) drawn inside the west casement reveals at alpha {alpha} (the "
            "suite's ONE sheer transmission — same fabric as the glass-L sheer); the "
            "garden windows stay the brightest source; the flanking opal strips stay "
            "unoccluded and the mirror pier stays BARE — no fabric, no holdbacks, no "
            "brass at the mirror"]


def lighting_story_bits(spec):
    """ELEMENT 5 (D-E5-9, element5-lighting_DD-2026-07-20.md §9): the DELIBERATE lit
    state, NAMED so the Gemini polish pass cannot repaint, flatten, or 'unify' it away
    (the repair prompt's palette_coherence would otherwise read the opal strips / lamp
    glow / graded wash as noise to clean — the recurring revert-by-omission class,
    this time aimed at LIGHT instead of a material). DATA-driven on the e5 block."""
    if ((spec or {}).get("lighting") or {}).get("schema") != "e5-layers@0.1":
        return []
    return ["lighting is DELIBERATE 3-layer (keep every pool and glow, do not flatten "
            "or unify): warm-white recessed pools; vertical opal task strips flanking "
            "the makeup mirror and a full-width opal task bar above the ensuite mirror "
            "(black-alu bodies, no brass at any mirror); a graded warm wash raking the "
            "oak slat headboard wall; a soft tub wash; the two brass dome table lamps "
            "GLOW warm (2850K) with a cast pool on each nightstand — dimmer than the "
            "garden windows, which stay the brightest source"]


def _bed_dims(spec):
    """(along, across, height, base_top) for the spec's bed, or None.

    The head axis is _build_bed's business, not this module's, so the LONGER run of the
    footprint is taken as head-to-foot. That is a guess, and it is deliberately biased:
    getting it wrong can only make the throw predicate answer for the other orientation,
    and the cost of the two errors is not symmetric. A false NO drops armour off a piece
    the build really made — the revert-by-omission this whole file exists to prevent. A
    false YES tells the polish not to remove something that is not there, which costs
    nothing. So when in doubt, speak."""
    for it in (spec or {}).get("items") or []:
        if str(it.get("kind", "")).lower() != "bed":
            continue
        try:
            w, d = float(it["w"]) * 0.001, float(it["d"]) * 0.001
            h = float(it["h"]) * 0.001
        except Exception:
            return None
        return max(w, d), min(w, d), h, h * 0.34      # base_h mirrors _build_bed
    return None


def styling_story_bits(spec, baked=()):
    """ELEMENT 8 (2026-07-22): the STYLING layer, NAMED so the Gemini polish pass cannot
    strip it back to the empty room the owner rejected.

    Every count DERIVES by re-running the same PURE layout the build runs — never a
    literal. That is the e6 lesson stated as code: the towel bit once hardcoded "2 bath
    towels" while the census said otherwise, and the polish would have painted back a
    towel the build had removed. Here a rail that stops being built silently drops out of
    the prose too, because the prose is a len() over the same source.

    GATED on the referent: a spec whose millwork produces no hang rail emits nothing
    rather than describing garments that do not exist.

    The bed's fabrics are cloth-solver output: their fold pitch, hem line and corner
    behaviour EMERGE, so no literal may stand in for them. The previous cut asserted
    "gathered folds at ~110mm pitch" — a true statement about a generator that had since
    been deleted, and a number nothing controls any more.

    Existence, though, IS decidable purely, and must be: whether a foot throw fits comes
    from `styling.foot_throw`, the SAME function `_build_bed` gates on, so the prose and
    the build cannot answer differently. `baked` (build_room._SOFT_BAKED) is accepted for
    callers that have it and is NOT consulted — the render-polish path
    (experiment_3leg.py:197) runs outside Blender and has none, and a bit that goes silent
    there would drop armour off a piece the build really made."""
    import millwork as _mw
    import wardrobe_bay as _wb
    import styling as _st

    rails, shelves = 0, 0
    _rc = None
    outline = ((spec or {}).get("room") or {}).get("outline_mm")
    if outline:
        pts = [(float(p[0]) * 0.001, float(p[1]) * 0.001) for p in outline]
        _rc = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    for b in (spec or {}).get("builtins") or []:
        try:
            W, D = float(b["w"]) * 0.001, float(b["d"]) * 0.001
            H = float(b["h"]) * 0.001 if b.get("h") else 2.8
            ax, sg, _src = _mw.mill_axis(float(b["x"]) * 0.001, float(b["y"]) * 0.001,
                                         W, D, _rc or (0.0, 0.0), (), b.get("face"))
            if ax is None:
                continue
            # MIRROR the build's own call (open_front from the builtin, not forced
            # True, and every builtin walked, not just the open ones). Forcing it made
            # the prose say "21 shelf part(s)" while the build dressed from 39 — the
            # prose-vs-build drift this armour exists to prevent, committed inside the
            # armour itself.
            for p in _mw.millwork_parts(str(b.get("kind", "")), W, D, H, ax, sg,
                                        floor_standing=(not b.get("mount_mm")),
                                        open_front=bool(b.get("open"))):
                rails += p[0].startswith("rail")
                shelves += p[0].startswith("shelf")
        except Exception:                      # a builtin this lane cannot lay out is not
            continue                           # an element-8 concern; the build lane owns it
    if any(s.get("type") == "wardrobe" for s in (spec or {}).get("subrooms") or []):
        for s in (spec or {}).get("subrooms") or []:
            if s.get("type") != "wardrobe":
                continue
            for p in _wb.bay_parts(s):
                rails += str(p.get("part", "")).startswith("rail")
                shelves += str(p.get("part", "")).startswith("shelf")
    bits = []
    if rails:
        bits.append(
        f"the suite is DRESSED, and the dressing is decided geometry — not set dressing "
        f"the polish may invent or remove: HANGING GARMENTS fill all {rails} satin-brass "
        f"hang rails (soft shells on wire hangers, three values from the suite's own "
        f"signed textiles — greige stonewashed linen, greige-oatmeal terry, matte-black "
        f"— hung shoulder-to-shoulder ACROSS the carcass depth, never along the rail), "
        f"and folded knit stacks sit on the open oak shelves ({shelves} shelf part(s) "
        f"available; a deliberate minority is left BARE so the joinery still reads as "
        f"joinery). NEVER empty a rail, never clear a shelf, never replace the garments "
        f"with doors or panels")
    _bed = _bed_dims(spec)
    if _bed:
        bits.append(
            "the bed's coverlet is SIMULATED CLOTH, not a slab and not a modelled skirt: "
            "it lies on the mattress, overhangs three sides and FALLS, so its folds, the "
            "roll at the mattress edge and its never-level hem are all solved rather than "
            "drawn — and its corners are cut ROUND, so the drape turns them as one soft "
            "cascade instead of a squared flap. The hem stops above the recessed plinth so "
            "element 3's shadow reveal survives (the build re-cuts the cloth until it "
            "does). Keep the folds, keep the uneven hem, keep the gap under the bed, keep "
            "the corner cascades; do NOT iron the fall into a flat skirt or a box")
    if _bed and _st.foot_throw(*_bed):
        # 2026-07-23: this used to end "It is the ONLY mid-tone in a frame otherwise filled
        # by one value of near-white". Both halves were retired by measurement — the frame
        # is no longer one value of near-white (that is what the tonal ladder fixed), and
        # the throw was never the only mid-tone: at HEAD it rendered 155.1 with the coverlet
        # at 164.8 and the bench at 178.2. Retiring the claim in build_room's comment while
        # leaving it HERE would have been strictly worse than not retiring it at all, since
        # this is the copy that actually reaches the image model.
        bits.append(
            "a GREIGE LINEN THROW lies across the foot of the bed and falls over the foot "
            "edge — the same greige as the bed base and the foot bench, no new colour, and "
            "at the DEEPEST value in the room's soft goods. That depth is its whole job: it "
            "is what keeps the bed from reading as one pale mass. Do NOT lighten it toward "
            "the bedding, do NOT flatten its fall back onto the mattress, do NOT remove it")
    if bits:
        bits.append(
        # 2026-07-23: "in the deepest value — the only dark object in the frame's upper
        # half" was false when written (the lumbar measured 188.6, seventh lightest of the
        # bed group's twelve measured pieces — the ten bed__ parts plus the bench seat and
        # the lumbar itself) and this change is what makes it obviously false. The lumbar
        # is an accent by TEXTURE and POSITION; terry is element 6's signed cloth, shared
        # with four ensuite pieces, so it is not re-valued to rescue a sentence.
        # The head's ladder is now a VALUE ladder too, and that is what is worth telling
        # the polish pass — it is the half it kept flattening.
        "the bed head is a THREE-HEIGHT ladder that is also a TONAL one: two upright euro "
        "shams against the oak slat wall in the duvet set's deeper greige, two plump "
        "sleeping pillows in front of them in the lightest cloth in the room, and ONE "
        "greige-oatmeal terry lumbar cushion off-centre — an accent of TEXTURE, not of "
        "value. Keep all three heights, keep the value steps between them, keep the "
        "asymmetry; do NOT level them into a matched pair, do NOT wash the shams up to the "
        "pillows, and do NOT crease, dent or rumple any of them (the room is made, not "
        "slept in)")
    return bits


def wardrobe_bay_story_bits(spec):
    """ELEMENT 7 (D-E7-8, element7-wardrobe-bay_DD-2026-07-21.md): the wardrobe bay's
    decided state, NAMED so the Gemini polish pass cannot repaint the mineral fronts
    wood-grain, paint a wall across the open south edge, furnish the deliberately bare
    floor, re-floor the walk-in, or 'clean up' the door-mouth stub. GATED on the bay's
    own referent (a type='wardrobe' subroom with wardrobe fixtures — a bay-less spec
    emits nothing); every counted/measured clause DERIVES from spec data (the S4
    prose-copy lesson). The openness clause looks the zone-open-south record up BY ID
    and RAISES if a wardrobe subroom lacks it — the cross-block pin (D-E7-2): the
    armour must never survive the record it describes being deleted."""
    bay = next((s for s in (spec or {}).get("subrooms") or []
                if s.get("type") == "wardrobe"), None)
    if not bay:
        return []
    masses = [f for f in bay.get("fixtures") or []
              if str(f.get("kind", "")) == "wardrobe"]
    if not masses:
        return []
    if not any(o.get("id") == "zone-open-south" for o in bay.get("openings") or ()):
        raise ValueError(
            "wardrobe_bay_story_bits: the wardrobe subroom lacks the 'zone-open-south' "
            "record — D-E7-2's armour cannot describe an openness the spec no longer "
            "declares; restore the record (the build lane raises on this too)")
    # review catch E7-F1: the bare-floor clause DERIVES from a live scan, never a
    # hardcoded 'bare' — if a decided item lands on the bay floor, RAISE (the polish
    # armour must not silently order it erased; the towel-census prose-copy lesson).
    import wardrobe_bay as _wb
    _intruders = _wb.bay_floor_intruders(spec)
    if _intruders:
        raise ValueError(
            f"wardrobe_bay_story_bits: the bay clear floor is no longer BARE — "
            f"{_intruders} intrude(s) on it (D-E7-10). The bare-floor armour would "
            f"tell the Gemini polish to erase them; decide the floor object as a NEW "
            f"element (re-run the 914 arithmetic) and update this clause, do not let "
            f"the armour lie.")
    # THE DRESSING GALLERY (owner redesign 2026-07-22): the clauses DERIVE per-mass from
    # spec data (open vs closed, mirror niche) so the polish armour follows the design and
    # can never re-order the dead grey scheme (the S4 prose-copy lesson).
    open_masses = [m for m in masses if m.get("open")]
    closed_masses = [m for m in masses if not m.get("open")]
    has_mirror = any(m.get("niche_mirror") for m in masses)
    head = (f"wardrobe bay = an OPEN oak-and-brass walk-in DRESSING ROOM (the enclosed "
            f"twin of the bedroom's BF09-3 dressing wall), {len(open_masses)} open "
            f"composed mass(es)")
    if closed_masses:
        head += f" + {len(closed_masses)} calm cool CLOSED anchor(s)"
    bits = [head + ": the open masses show HANGING GARMENTS on satin-brass rails, folded "
            "knits/bags/objects on OPEN light-oak shelves, and floating cool-microcement "
            "drawer towers — warm oak carcass glowing between the contents; "
            + ("the cool closed anchor is flat handleless microcement with one horizontal "
               "counter-datum shadow line (NOT a blank locker, NOT fluted, NOT wood-grain); "
               if closed_masses else "")
            + ("the HERO wall terminates in a MIRROR-BACKED open niche (the focal jewel — "
               "the mirror doubles the niche depth and sparkles the lit shelves); "
               if has_mirror else "")
            + "keep it OPEN and composed — do NOT flatten it into closed doors, do NOT "
            "strip the garments/shelves/rails, do NOT smooth it grey; the bay is OPEN to "
            "the bedroom on its south side (never paint a wall or doorway there); the "
            "floor is deliberately BARE and is the bedroom's oak floor CONTINUING through "
            "the walk-in (never tile, carpet, or furnish it)"]
    cut = next((o for o in bay.get("openings") or ()
                if o.get("id") == "door-ensuite-baycut"), None)
    if cut:
        r = cut.get("rect") or [0, 0, 0, 0]
        clear = abs(float(r[3]) - float(r[1])) or abs(float(r[2]) - float(r[0]))
        bits.append(f"the ensuite doorway in the bay's west wall is an OPEN ~{clear:.0f}mm "
                    "passage (sliding leaf exists but is deliberately not drawn) with a "
                    "shallow mouth stub at its south edge — keep the passage open and "
                    "keep the stub, it is the drawn slide-mouth rebate, not a defect")
    return bits


def textile_surface_story_bits(spec, resolved=None):
    """THE WEAVE, NAMED — so the Gemini polish pass cannot iron the suite's textiles back
    into the painted slabs they were until 2026-07-22 (MA-05 'plastic look',
    knowledge/classifications/render-defects.md:69).

    This is the armour half of the _woven change. Without it the render would carry a
    surface the prose never claims, and the polish prompt — which is told the room in
    words — would have every licence to smooth it: exactly the channel that repainted the
    cool counter oak and emptied the hang rails.

    DERIVED, never a literal, on two axes at once (the e6 lesson):
      * WHICH cloths are on screen comes from the same spec referents the BUILD routes on
        (a bed item, a tub-chair stool, a curtains block, the ensuite accessory census, an
        explicitly selected fabric family). A textile that stops being built drops out of
        the prose by construction.
      * WHAT each cloth looks like comes from CLOTH_KINDS[kind]['desc'] — the same table
        the build reads its slub pitch and bump from. Retune the vocabulary and the
        sentence retunes with it; there is no second copy to drift.
    A spec with no textiles emits nothing rather than describing cloth that isn't there."""
    wearers = {}                      # cloth kind -> what wears it (sorted, deduped)

    def wear(kind, label):
        cloth_args(kind)              # RAISES on a kind with no vocabulary row
        wearers.setdefault(kind, [])
        if label not in wearers[kind]:
            wearers[kind].append(label)

    items = (spec or {}).get("items") or []
    if any(it.get("kind") == "bed" for it in items):
        # D3-2: bedding IS stonewashed linen, and _build_bed dresses base, mattress,
        # duvet, pillows and coverlet from the one linen signature.
        wear("linen", "the bed base, bedding and the solver-draped coverlet")
    if any(it.get("kind") == "stool" and it.get("style") == "tub_chair" for it in items):
        wear("linen", "the vanity tub-chair")
    if (spec or {}).get("curtains"):
        # NAME THE LAYERS BY THE KEY THE BUILD ROUTES ON (build_room does mats[rb["type"]]),
        # never by a state adjective. The first cut said "the drawn curtain" for the linen
        # layer — and on the canonical spec the linen blackout is PARKED (render_state
        # blackout=parked, privacy=drawn), so the ~5.3 m surface actually drawn across the
        # glass is the PLAIN sheer. That sentence reaches the image model through
        # material_story's {material_story} slot, i.e. it would have told the polish pass
        # to treat the wrong panel as linen. A hardcoded state is also a second copy of a
        # value the build reads from one source — the prose-copy mutation this file guards
        # against elsewhere (casement_sheer_story_bits derives its alpha for that reason).
        wear("linen", "the opaque blackout curtain")
        wear("plain", "the sheer privacy panel")
    if (spec or {}).get("casement_sheers"):
        wear("plain", "the casement sheers")
    for s in (spec or {}).get("subrooms") or []:
        if s.get("type") != "bathroom":
            continue
        for f in s.get("fixtures") or []:
            # ROUTE ON THE SAME REFERENT THE BUILD DOES: bathroom.accessory_parts requires
            # kind == "bath_accessories" and a census that is a non-empty DICT (it RAISES
            # on anything else). The first cut accepted any fixture with a truthy
            # design.census, so it would have claimed terry for a fixture the build refuses
            # to make — prose that outlives its referent.
            if str(f.get("kind", "")) != "bath_accessories":
                continue
            census = (f.get("design") or {}).get("census")
            if isinstance(census, dict) and census:
                wear("terry", "the ensuite towels, robes and bath mat")
    fam = ((resolved or {}).get("families") or {}).get("fabric")
    if fam:
        k = preset_cloth_kind(fam)
        if k:
            wear(k, "the upholstery family")
    if not wearers:
        return []
    parts = [f"{', '.join(wearers[k])} = {CLOTH_KINDS[k]['desc']}"
             for k in sorted(wearers)]
    return ["every textile in this room is WOVEN, not painted: " + "; ".join(parts)
            + " — each carries a real slub/crease relief, a matching roughness break-up "
              "and a low-amplitude tonal drift, which is what makes cloth read as cloth "
              "instead of vinyl. KEEP that surface: do NOT smooth, gloss, iron flat or "
              "re-tint any of it, and do NOT swap a weave for a printed pattern"]


def tonal_ladder_story_bits(spec):
    """THE BED'S VALUE STRUCTURE, NAMED — so the polish pass cannot flatten it back.

    Same referent the BUILD routes on: `_build_bed` runs for an item of kind 'bed', so a
    spec without one says nothing rather than describing a ladder nobody rendered.

    The sentence itself is `value_ladder.story_line()` — derived from the tone table and
    the ladder the build reads, with no number retyped here. That matters more than usual
    for this bit: the whole defect it guards is a set of values that drifted apart from
    the words describing them, and an armour bit holding its own copy of those values
    would drift the same way (twice caught in review already: "2 bath towels", "21 shelf
    parts").

    IMPORTED LAZILY on purpose: value_ladder imports THIS module for the sRGB conversions
    and the 30-240 band, so a module-level import here would be a cycle."""
    if not any(it.get("kind") == "bed" for it in (spec or {}).get("items") or []):
        return []
    import value_ladder as _vl
    return [_vl.story_line()]


def material_story(resolved, spec=None, baked=()):
    """One prose sentence naming the ACTUAL selected materials — the truth the render
    shows, for the render-polish prompt's {material_story} slot (and rationale). Built
    from preset descriptions, so the prompt can never describe materials the spec did
    not choose.

    The spec-derived protective bits (millwork sub-parts, decided FF&E, ensuite
    palette + textiles, e5 lighting, e6 sheers) ride REGARDLESS of whether a
    `materials` block selected presets — until 2026-07-21 an early `if not resolved`
    return dropped ALL of them for a spec without the block (review catch: every
    element's anti-repaint armour hung on an unrelated block's presence — the
    decided-data-through-swallows class, story flavor). A spec with neither presets
    nor decided-element data still returns the legacy palette sentence verbatim."""
    bits = []
    if not resolved:
        bits.append("the existing studio palette: warm oak plank floor, matte "
                    "warm-white walls, walnut feature wall and millwork, cream "
                    "boucle upholstery")
    else:
        for role, label in (("floor", "floor"), ("walls", "walls"),
                            ("feature_wall", "feature wall"), ("millwork", "millwork"),
                            ("glazing", "glazing"), ("fixtures", "fixtures")):
            pn = resolved["surfaces"].get(role)
            if pn:
                bits.append(f"{label}: {PRESETS[pn]['desc']}")
        for fam, label in (("fabric", "upholstery"), ("wood", "wood furniture"),
                           ("neutral", "other furniture")):
            pn = resolved["families"].get(fam)
            if pn:
                bits.append(f"{label}: {PRESETS[pn]['desc']}")
        for el, pn in sorted((resolved.get("elements") or {}).items()):
            bits.append(f"{el}: {PRESETS[pn]['desc']}")
    for label, pn in millwork_subpart_presets(spec):
        bits.append(f"{label}: {PRESETS[pn]['desc']}")
    bits.extend(furniture_material_story_bits(spec))   # ELEMENT 3: bed base / lamps / rug (D7)
    bits.extend(ensuite_material_story_bits(spec))     # ELEMENT 4+6: ensuite palette + textiles
    bits.extend(lighting_story_bits(spec))             # ELEMENT 5: the deliberate 3-layer light
    bits.extend(casement_sheer_story_bits(spec))       # ELEMENT 6: the west casement sheers
    bits.extend(wardrobe_bay_story_bits(spec))         # ELEMENT 7: the open dressing gallery
    bits.extend(styling_story_bits(spec, baked))              # ELEMENT 8: the styling layer
    bits.extend(textile_surface_story_bits(spec, resolved))   # the WEAVE (2026-07-22)
    bits.extend(tonal_ladder_story_bits(spec))                # the VALUE ladder (2026-07-23)
    return "; ".join(bits) if bits else material_story(None)
