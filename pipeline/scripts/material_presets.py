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
    for k in ("sheen", "coat", "ior", "spec", "transmission"):
        if k in p:
            a[k] = float(p[k])
    if "trans_tint" in p:
        a["trans_tint"] = tuple(p["trans_tint"])
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
        bits.append("bed base + foot bench: upholstered greige stonewashed linen — matte, a mid-"
                    "greige plinth below the crisp bedding; NOT oak (D1-A anti-monopoly)")
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
    return bits


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


def material_story(resolved, spec=None):
    """One prose sentence naming the ACTUAL selected materials — the truth the render
    shows, for the render-polish prompt's {material_story} slot (and rationale). Built
    from preset descriptions, so the prompt can never describe materials the spec did
    not choose."""
    if not resolved:
        return ("the existing studio palette: warm oak plank floor, matte warm-white walls, "
                "walnut feature wall and millwork, cream boucle upholstery")
    bits = []
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
    bits.extend(ensuite_material_story_bits(spec))     # ELEMENT 4: the ensuite's decided palette
    bits.extend(lighting_story_bits(spec))             # ELEMENT 5: the deliberate 3-layer light
    return "; ".join(bits) if bits else material_story(None)
