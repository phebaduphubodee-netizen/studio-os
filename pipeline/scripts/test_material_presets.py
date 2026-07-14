#!/usr/bin/env python3
"""Tests for material_presets.py — the spec-selectable material layer.

Run: python -m pytest test_material_presets.py -q   (cwd = pipeline/scripts)

Pins follow the U7 frozen-constants pattern: preset VALUES are asserted exactly, so a
silent re-derive/retune fails the suite instead of silently changing what a client
render shows. Mutation each test kills is named in its docstring.
"""
import pytest

import material_presets as mp


# ---------------------------------------------------------------------------
# color math
# ---------------------------------------------------------------------------

def test_srgb_to_linear_endpoints_and_midpoint():
    """Kills a mutant that skips the piecewise EOTF (plain /255 or gamma-2.2 shortcut):
    0 -> 0, 1 -> 1, and 0.5 sRGB must land at the IEC value ~0.2140, not 0.5."""
    assert mp.srgb_to_linear(0.0) == 0.0
    assert abs(mp.srgb_to_linear(1.0) - 1.0) < 1e-12
    assert abs(mp.srgb_to_linear(0.5) - 0.21404114) < 1e-6
    # linear segment: below the 0.04045 knee it is c/12.92, not the power curve
    assert abs(mp.srgb_to_linear(0.04) - 0.04 / 12.92) < 1e-12


def test_hex_to_srgb01_and_bad_hex_raises():
    """Kills a mutant that swallows malformed hex (silent black would render a hole)."""
    assert mp.hex_to_srgb01("#FF0000") == (1.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        mp.hex_to_srgb01("#F00")


def test_albedo_band_clamp():
    """The 30-240 sRGB texel band (pbr-material-behavior.md:55) is enforced: pure white
    clamps to 240/255, pure black to 30/255. Kills a mutant that drops the clamp."""
    lo, hi = 30 / 255.0, 240 / 255.0
    assert mp.clamp_albedo_band((1.0, 1.0, 1.0)) == (hi, hi, hi)
    assert mp.clamp_albedo_band((0.0, 0.0, 0.0)) == (lo, lo, lo)
    assert mp.clamp_albedo_band((0.5, 0.5, 0.5)) == (0.5, 0.5, 0.5)


# ---------------------------------------------------------------------------
# preset table invariants (authoring bounds — bounds outrank REFERENCE presets)
# ---------------------------------------------------------------------------

def test_every_preset_resolves_and_metalness_is_binary():
    """factory_args must succeed for EVERY preset, and metalness must be 0 or 1
    everywhere (pbr-material-behavior.md:57). Kills a mid-grey-metal preset sneaking in."""
    for name in mp.PRESETS:
        a = mp.factory_args(name)
        assert a["factory"] in ("pbr", "solid", "painted", "veneer", "proc_wood", "glass")
        if a["factory"] != "pbr":
            assert a.get("metallic", 0.0) in (0.0, 1.0), name


def test_roughness_never_absolute():
    """Roughness floor/ceil [0.03, 0.97] (bsdf-material-presets.md:54-60, render-quality
    §3): polished chrome (authored 0.04) and any 0.0-authored row must come out >= 0.03."""
    for name in mp.PRESETS:
        a = mp.factory_args(name)
        if "rough" in a:
            assert 0.03 <= a["rough"] <= 0.97, (name, a["rough"])


def test_dielectric_albedo_stays_in_band_metal_and_glass_exempt():
    """Band applies to dielectric albedo only: boucle_cream (#F5F0E9, R=245 authored)
    must clamp to <=240/255 linearized; chrome (metal) and clear_glass keep full white.
    Kills the mutant that clamps everything (grey glass) or nothing (glowing fabric)."""
    hi_lin = mp.srgb_to_linear(240 / 255.0)
    boucle = mp.factory_args("boucle_cream")["rgba"]
    assert all(c <= hi_lin + 1e-9 for c in boucle[:3])
    # chrome is authored AT the band edge (240) — clamp would be identity there, so the
    # exemption is proven on glass (#FFFFFF stays 1.0); chrome pins the authored value.
    chrome = mp.factory_args("polished_chrome")["rgba"]
    assert abs(chrome[0] - hi_lin) < 1e-9
    glass = mp.factory_args("clear_glass")["rgba"]
    assert abs(glass[0] - 1.0) < 1e-9


def test_studio_presets_reproduce_legacy_palette_exactly():
    """U7-style pin: the STUDIO presets are the LIVE legacy palette VERBATIM — selecting
    them must render exactly today's values (build_room.py _suite_materials). A retune
    here silently changes shipped-look reproduction; this pin makes it loud."""
    assert mp.factory_args("walnut_veneer")["rgba"] == (0.105, 0.052, 0.026, 1.0)
    assert mp.factory_args("walnut_veneer")["rough"] == 0.45
    fab = mp.factory_args("boucle_cream_studio")
    assert fab["rgba"] == (0.84, 0.79, 0.71, 1.0)
    assert (fab["rough"], fab["sheen"]) == (0.92, 0.8)
    gl = mp.factory_args("glazing_default")
    assert gl["rgba"] == (0.60, 0.76, 0.80, 1.0)
    assert (gl["transmission"], gl["ior"]) == (0.95, 1.45)
    assert gl["trans_tint"] == (0.86, 0.92, 0.93, 1.0)
    feat = mp.factory_args("walnut_feature")
    assert (feat["tint"], feat["variation"]) == ((0.40, 0.28, 0.20, 1.0), 0.06)
    fix = mp.factory_args("sanitary_white")
    assert (fix["rgba"], fix["rough"], fix["spec"], fix["coat"]) == \
        ((0.90, 0.91, 0.92, 1.0), 0.15, 0.6, 0.2)
    assert mp.factory_args("neutral_solid")["rgba"] == (0.52, 0.50, 0.48, 1.0)


def test_reference_preset_values_pinned():
    """U7-style pin on the knowledge-derived rows (bsdf-material-presets.md:43-50):
    silent drift of a REFERENCE value into code fails here, not in a client render."""
    assert mp.PRESETS["boucle_cream"]["hex"] == "#F5F0E9"
    assert mp.PRESETS["warm_white_paint"]["hex"] == "#F5F3EE"
    assert mp.PRESETS["brushed_brass"]["hex"] == "#B5A642"
    assert mp.PRESETS["brushed_brass"]["metallic"] == 1.0
    assert mp.PRESETS["clear_glass"]["ior"] == 1.52
    assert mp.PRESETS["clear_glass"]["transmission"] == 1.0


# ---------------------------------------------------------------------------
# resolve_materials — fail LOUD, never a silent default
# ---------------------------------------------------------------------------

def _spec(materials):
    return {"schema": "interior-ai/room-spec@0.2", "materials": materials}


def test_no_block_resolves_none():
    """Absence == legacy palette. Kills a mutant that fabricates defaults for every spec
    (which would change every existing render's provenance)."""
    assert mp.resolve_materials({}) is None
    assert mp.resolve_materials(None) is None
    assert mp.resolve_materials({"room": {}}) is None
    # explicit null / empty object are the only in-key spellings of 'no selections'
    assert mp.resolve_materials({"materials": None}) is None
    assert mp.resolve_materials({"materials": {}}) is None


def test_falsy_non_dict_block_raises():
    """Review finding 2026-07-14: "materials": [] / false / "" / 0 used to short-circuit
    to the legacy palette BEFORE the type check — a generator emitting the wrong shape
    silently rendered defaults while the experiment concluded 'palette barely moved'.
    Kills the `if not block: return None` first-line mutant."""
    for bad in ([], False, "", 0, "oak"):
        with pytest.raises(ValueError, match="must be an object"):
            mp.resolve_materials({"materials": bad})


def test_reconcile_elements_unknown_key_raises():
    """Anti-silent-drop gate: an element key matching no item (typo'd Thai name) must
    raise, never no-op while material_story still asserts the preset to Gemini."""
    sel = mp.resolve_materials(_spec({"elements": {"โซฟา 3 ทีนั่ง": "velvet_sand"}}))
    spec = {"items": [{"name": "โซฟา 3 ที่นั่ง", "kind": "sofa"}]}  # note the missing ่
    with pytest.raises(ValueError, match="matches NO item"):
        mp.reconcile_elements(sel, spec)


def test_reconcile_elements_unappliable_kind_raises():
    """bed/bench/rug are built by bespoke builders (ph_model/rug__ routing) the presets
    cannot reach — the item loop intercepts them BEFORE the element lookup. A selection
    there must abort the build, not silently render legacy fabric (review 2026-07-14)."""
    sel = mp.resolve_materials(_spec({"elements": {"bed": "velvet_sand"}}))
    spec = {"items": [{"name": "เตียง", "kind": "bed"}]}
    with pytest.raises(ValueError, match="bespoke builder"):
        mp.reconcile_elements(sel, spec)


def test_reconcile_elements_metal_glass_pbr_presets_refused():
    """Per-element application is flat-dielectric only: metals lose Metallic, glass
    loses Transmission, pbr has no flat colour — each renders a beige lie if allowed
    through the retint path (review findings 9/15/16)."""
    spec = {"items": [{"name": "โต๊ะ", "kind": "coffee_table"}]}
    for preset in ("brushed_brass", "clear_glass", "oak_wood_floor"):
        sel = mp.resolve_materials(_spec({"elements": {"โต๊ะ": preset}}))
        with pytest.raises(ValueError):
            mp.reconcile_elements(sel, spec)


def test_reconcile_elements_happy_path_binds_by_name_and_kind():
    sel = mp.resolve_materials(_spec({"elements": {
        "เก้าอี้ 1": "velvet_sand", "coffee_table": "birch_veneer"}}))
    spec = {"items": [{"name": "เก้าอี้ 1", "kind": "armchair"},
                      {"name": "โต๊ะกลาง", "kind": "coffee_table"}]}
    bound = mp.reconcile_elements(sel, spec)
    assert bound == {"เก้าอี้ 1": ["เก้าอี้ 1"], "coffee_table": ["โต๊ะกลาง"]}
    # and the no-elements case is a no-op, never a crash
    assert mp.reconcile_elements(mp.resolve_materials(_spec({"surfaces": {}})), spec) == {}
    assert mp.reconcile_elements(None, spec) == {}


def test_unknown_preset_raises():
    """THE anti-silent-default pin: a typo'd preset must raise, not fall back — the
    flattering-scorer family, materials flavor (render shows default, report says spec)."""
    with pytest.raises(ValueError, match="unknown material preset"):
        mp.resolve_materials(_spec({"surfaces": {"floor": "oak_wood_flor"}}))


def test_unknown_surface_family_and_top_key_raise():
    with pytest.raises(ValueError, match="unknown surface"):
        mp.resolve_materials(_spec({"surfaces": {"ceiling": "warm_white_paint"}}))
    with pytest.raises(ValueError, match="unknown family"):
        mp.resolve_materials(_spec({"families": {"metal": "brushed_brass"}}))
    with pytest.raises(ValueError, match="unknown key"):
        mp.resolve_materials(_spec({"surfacez": {}}))


def test_resolve_happy_path_and_element_lookup():
    """Element lookup: exact NAME beats kind; kind is the fallback; miss -> None."""
    sel = mp.resolve_materials(_spec({
        "schema": "interior-ai/materials@0.1",
        "surfaces": {"floor": "oak_wood_floor"},
        "families": {"fabric": "fabric_polyester_weave"},
        "elements": {"เก้าอี้อาร์มแชร์ 1": "velvet_sand", "coffee_table": "birch_veneer"},
    }))
    assert sel["surfaces"]["floor"] == "oak_wood_floor"
    assert mp.element_preset(sel, "เก้าอี้อาร์มแชร์ 1", "armchair") == "velvet_sand"
    assert mp.element_preset(sel, "โต๊ะกลาง", "coffee_table") == "birch_veneer"
    assert mp.element_preset(sel, "โซฟา 3 ที่นั่ง", "sofa") is None
    assert mp.element_preset(None, "x", "sofa") is None


def test_material_story_names_only_what_the_spec_chose():
    """The polish prompt's {material_story} slot must be the TRUTH: it names selected
    presets' descriptions and nothing else. Kills a mutant that pads the story with the
    default palette (Gemini would then 'preserve' materials the render doesn't show)."""
    sel = mp.resolve_materials(_spec({
        "surfaces": {"floor": "birch_veneer"},
        "elements": {"sofa": "fabric_polyester_weave"},
    }))
    story = mp.material_story(sel)
    assert "birch veneer" in story
    assert "polyester weave" in story
    assert "walnut" not in story          # nothing the spec did not choose
    # and the no-block story describes the legacy palette (for legacy-control dispatch)
    assert "walnut" in mp.material_story(None)


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
