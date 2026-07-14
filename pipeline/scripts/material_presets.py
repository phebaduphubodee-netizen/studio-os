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
}

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
        bad = [it for it in hits if str(it.get("kind", "")) in UNAPPLIABLE_KINDS]
        if bad:
            raise ValueError(f"materials.elements key {key!r} targets kind "
                             f"'{bad[0].get('kind')}' — built by a bespoke builder the "
                             f"preset cannot reach (UNAPPLIABLE_KINDS={UNAPPLIABLE_KINDS})")
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
    return "; ".join(bits) if bits else material_story(None)
