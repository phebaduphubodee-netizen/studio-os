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
        assert a["factory"] in ("pbr", "solid", "painted", "veneer", "proc_wood",
                                "image_wood", "glass")
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


# ---------------------------------------------------------------------------
# element-1 palette (PRJ-2026-002 master suite, owner-signed 2026-07-16)
# ---------------------------------------------------------------------------

def test_element1_presets_resolve_through_their_factories():
    """The four build-layer presets must resolve to real factory args without raising —
    a typo here would only surface as a mid-render crash inside Blender."""
    expect = {"oak_veneer": "proc_wood", "cool_plaster": "painted",
              "microcement_cool": "painted", "satin_brass": "solid"}
    for name, fac in expect.items():
        a = mp.factory_args(name)
        assert a["factory"] == fac, f"{name} -> {a['factory']}, wanted {fac}"


def test_satin_brass_is_a_real_metal():
    """The hang-rail accent must stay Metallic 1.0 — the binary-metalness gate would raise
    on anything else, and a dielectric 'brass' renders as yellow paint, not metal."""
    a = mp.factory_args("satin_brass")
    assert a["metallic"] == 1.0
    assert mp.PRESETS["satin_brass"]["tier"] == "DESIGN-INTENT"


def test_oak_is_LIGHT_not_the_walnut_it_replaces():
    """The whole anti-monopoly lever is that oak_veneer is LIGHTER than the walnut mass the
    eye-render exposed. Pin luminance ordering so a retune can't quietly darken it back."""
    oak = mp.factory_args("oak_veneer")["rgba"]
    walnut = mp.factory_args("walnut_veneer")["rgba"]
    lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    assert lum(oak) > lum(walnut) * 1.5, "oak must read clearly lighter than walnut"


def test_cool_surfaces_are_actually_cool():
    """Albers D1-A: the 60% wall ground must be COOL so it doesn't wash the oak out. Cool =
    blue channel >= red. Contrast this with the WARM legacy warm_white_paint it replaces —
    if a retune warms cool_plaster past warm_white, the lever is silently gone."""
    for name in ("cool_plaster", "microcement_cool"):
        r, g, b = mp.factory_args(name)["rgba"][:3]
        assert b >= r, f"{name} must be cool (blue {b:.3f} >= red {r:.3f})"
    warm = mp.factory_args("warm_white_paint")["rgba"]
    assert warm[0] > warm[2], "the legacy wall it replaces really is warm (red > blue)"


def test_element1_preset_values_are_pinned_exactly():
    """U7 frozen-constants discipline: the client render's palette VALUES are pinned, so a silent
    retune (e.g. re-darkening the oak, warming the plaster) fails the suite instead of quietly
    changing what the owner signed off on."""
    P = mp.PRESETS
    assert (P["oak_veneer"]["hex"], P["oak_veneer"]["dark_hex"], P["oak_veneer"]["rough"]) == ("#C7B896", "#A5926B", 0.38)
    assert (P["cool_plaster"]["hex"], P["cool_plaster"]["rough"]) == ("#EAEDEF", 0.85)
    assert (P["microcement_cool"]["hex"], P["microcement_cool"]["rough"]) == ("#AEB2B2", 0.90)
    assert (P["satin_brass"]["hex"], P["satin_brass"]["rough"], P["satin_brass"]["metallic"]) == ("#C4A45C", 0.35, 1.0)
    assert (P["matte_black_ply"]["hex"], P["matte_black_ply"]["rough"]) == ("#3A3C3E", 0.82)


def test_the_slat_backer_is_LEGAL_in_both_live_bands_not_merely_pinned():
    """The backer shipped #1A1A1A (26 sRGB) while the DD had issued a BAND (#2A2C2E-#3A3C3E)
    specifically so 'matte black' could ship without a thresholds PR. Two things were wrong and a
    value-pin could see neither:

    1. 26 sRGB is under the 30-sRGB texel floor, so factory_args CLAMPED it up — the authored number
       never reached a render, and the pin above was pinning a value the pipeline discarded.
    2. The studio has TWO live albedo bands IN DIFFERENT UNITS and the DD's arithmetic crossed them:
       >=30 sRGB (pbr-material-behavior.md:55) vs >=0.04 LINEAR (build_room.albedo_plausible). 0.04
       linear is ~56.3 sRGB, so the issued band's low end (#2A2C2E = 42 sRGB = 0.023 linear) does NOT
       clear both, and the clamp floor of 30 sRGB (0.013 linear) does not either. Only the TOP of the
       issued band clears both. (Neither band FAILS a build — albedo_plausible only prints
       "!! albedo WARN"; pbr-material-behavior.md:176-182 logs the mismatch as OPEN. The old value
       warned on every render that used it. "Warned", not "illegal".)

    So pin the PROPERTY, not the number: whatever the backer is, it must survive its own pipeline
    unclamped and sit inside both bands. A 0,0,0 recess is the same black-hole defect the designer
    circled on our own render — the darkening is GI/AO's job, which is the point."""
    a = mp.factory_args("matte_black_ply")
    raw = mp.srgb_hex_to_linear_rgba(mp.PRESETS["matte_black_ply"]["hex"], clamp_band=False)
    assert tuple(a["rgba"]) == pytest.approx(tuple(raw)), \
        "the authored backer must survive the band clamp UNCHANGED, or the render shows a colour " \
        "nobody chose"
    for c in a["rgba"][:3]:
        assert c >= 0.04, f"backer linear {c:.4f} trips build_room.albedo_plausible's 0.04 floor"
    r, g, b = (int(mp.PRESETS["matte_black_ply"]["hex"][i:i + 2], 16) for i in (1, 3, 5))
    assert min(r, g, b) >= 30, "and it must clear the 30-sRGB texel floor without being clamped there"
    assert b > g > r, "slightly COOL (B>G>R) — it is the ground the warm oak reads against (D7-B item 6)"
    assert 0.75 <= a["rough"] <= 0.85, \
        "D7-B item 6 issued roughness 0.75-0.85. 0.88 shipped — outside it, and unlike the hex it " \
        "was NOT clamped, so it is the one authored value that DID reach every render"


# ---------------------------------------------------------------------------
# build-layer helpers (pure): mill_object_role + parse_light_warm
# ---------------------------------------------------------------------------

def test_mill_object_role_routes_structured_parts():
    """The open-wall + slat parts route by their trailing PART TOKEN."""
    assert mp.mill_object_role("mill__ตู้__rail_full") == "brass"
    assert mp.mill_object_role("mill__ตู้__rail_short0") == "brass"
    assert mp.mill_object_role("mill__ตู้__drawer_front1") == "microcement"
    assert mp.mill_object_role("mill__ตู้__towerback") == "microcement"
    assert mp.mill_object_role("mill__BF14__backer") == "backing"
    assert mp.mill_object_role("mill__ตู้__back") == "oak"          # oak back panel, NOT microcement
    assert mp.mill_object_role("mill__ตู้__back_niche") == "oak"
    assert mp.mill_object_role("mill__ตู้__drawer_box0") == "oak"   # the box is oak; only the FRONT is cement
    assert mp.mill_object_role("mill__ตู้__gable0") == "oak"


def test_material_story_names_the_subpart_materials_the_render_actually_shows():
    """The polish prompt's {material_story} is the render's STATED truth. It read `surfaces` only, so
    it said "millwork: oak" while the render showed brass hang-rails, cool-microcement drawer fronts
    and D7's mineral jamb — and a repaint told the millwork is oak will 'correct' them BACK to oak.
    Same failure class as the backer that once rendered oak against a signed matte-black ply, one step
    downstream: the prompt must not contradict the picture."""
    resolved = {"surfaces": {"millwork": "oak_veneer"}, "families": {}, "elements": {}}
    spec = {"builtins": [
        {"kind": "headboard", "design": {"schedule": {"post_south_material": "microcement",
                                                      "post_north_material": "oak"}}},
        {"kind": "wardrobe", "open": True},
    ]}
    story = mp.material_story(resolved, spec)
    assert "brass" in story.lower(), "the hang-rails are ON SCREEN and unmentioned"
    assert "microcement" in story.lower(), "so are the mineral accents / the D7 jamb"
    assert "backer" in story.lower(), "so is the slat backer"
    # a spec with no built-ins says nothing extra — this stays truthful, not chatty
    plain = mp.material_story(resolved, {"builtins": []})
    assert "brass" not in plain.lower() and "backer" not in plain.lower()
    # and no spec at all behaves exactly as before (every existing caller)
    assert mp.material_story(resolved) == mp.material_story(resolved, None)


def test_millwork_subpart_presets_only_reports_what_is_on_screen():
    assert mp.millwork_subpart_presets(None) == []
    assert mp.millwork_subpart_presets({"builtins": [{"kind": "cabinet"}]}) == []
    # a CLOSED door run puts no brass/microcement on screen — only an open:true wall does
    assert mp.millwork_subpart_presets({"builtins": [{"kind": "wardrobe"}]}) == []
    got = dict((p, l) for l, p in mp.millwork_subpart_presets({"builtins": [{"kind": "headboard"}]}))
    assert got == {"matte_black_ply": "slat backer"}, "a plain slat wall has a backer and nothing else"
    # an OAK-terminated schedule must NOT claim mineral accents
    oak_only = mp.millwork_subpart_presets({"builtins": [
        {"kind": "headboard", "design": {"schedule": {"post_south_material": "oak",
                                                      "post_north_material": "oak"}}}]})
    assert all(p != "microcement_cool" for _, p in oak_only)


def test_a_terminal_member_routes_on_DECLARED_INTENT_not_on_being_a_jamb():
    """D7 = the mineral release: BF14's SOUTH end is cool microcement, its NORTH end is oak into oak
    (a joint — BF09-3 receives it). Both directions are pinned, and the OAK one is the load-bearing
    pin: it passes today only by FALLING THROUGH, which nothing else distinguishes from an accidental
    miss — and a silent miss is exactly how the slat backer once rendered oak against a signed
    matte-black ply.

    The token says `mineral`, not `jamb`, ON PURPOSE. This router is GLOBAL and project-agnostic, so
    a rule reading 'a jamb is microcement' would repaint every future project's jamb with
    PRJ-2026-002's D7 decision. millwork.terminal_part_name builds the token from the SPEC, so the
    project's decision stays in the project's spec."""
    assert mp.mill_object_role("mill__BF14__jambmineral") == "microcement"
    assert mp.mill_object_role("mill__BF14__postoak") == "oak"
    # ...and with the REAL 75-byte Thai object name build_room actually emits (Blender does not
    # truncate it, so the route is reachable — verified headless 2026-07-16c)
    assert mp.mill_object_role("mill__ผนังระแนงหัวเตียง_BF14__jambmineral") == "microcement"
    assert mp.mill_object_role("mill__ผนังระแนงหัวเตียง_BF14__postoak") == "oak"
    # a future project's OAK jamb must NOT inherit D7
    assert mp.mill_object_role("mill__BF99__jamboak") == "oak"
    assert mp.mill_object_role("mill__BF99__postmineral") == "microcement"


def test_millwork_and_the_router_agree_on_the_terminal_vocabulary():
    """The part token is an implicit contract across two files. Pin it from BOTH ends so a rename in
    millwork.py cannot silently revert D7 to oak."""
    import millwork as mw
    for material, want in (("microcement", "microcement"), ("oak", "oak")):
        for stem in ("jamb", "post"):
            token = mw.terminal_part_name(stem, material)
            assert mp.mill_object_role(f"mill__BF14__{token}") == want, \
                f"millwork emits {token!r} for {material} but the router paints it something else"
    with pytest.raises(ValueError):
        mw.terminal_part_name("jamb", "walnut")      # a typo must fail loud, never silently oak


def test_mill_object_role_does_NOT_paint_a_fallback_box_by_its_name():
    """THE ROUTER BUG (review 2026-07-16): a plain-box fallback is `mill__<free-text name>` with no
    part token. Its name must NEVER be pattern-matched, or a cabinet literally named 'front console'
    gets painted cool microcement, and a 'rail' or 'towerback' name gets brass/microcement."""
    assert mp.mill_object_role("mill__front_console") == "oak"
    assert mp.mill_object_role("mill__rail_shelf_unit") == "oak"
    assert mp.mill_object_role("mill__towerback_cabinet") == "oak"
    assert mp.mill_object_role("mill__wardrobe") == "oak"
    assert mp.mill_object_role("floor") == "oak"                     # not even a mill object


def test_parse_light_warm_default_and_valid():
    """No block -> the legacy 2400 K amber (byte-identical to before). A valid 3-tuple passes."""
    assert mp.parse_light_warm({}) == (1.0, 0.82, 0.60)
    assert mp.parse_light_warm({"light_warm": [1.0, 0.9, 0.8]}) == (1.0, 0.9, 0.8)
    assert mp.parse_light_warm(None) == (1.0, 0.82, 0.60)


@pytest.mark.parametrize("bad", [[1.0, 0.9], [1.0, 0.9, 0.8, 0.7], [2.0, 0.9, 0.8],
                                 [-0.1, 0.9, 0.8], "warm", 0.9, [1.0, "x", 0.8]])
def test_parse_light_warm_fails_loud_on_malformed(bad):
    """Review 2026-07-16: a wrong-length / out-of-range / non-numeric light_warm used to be
    silently truncated, unclamped, or crash with a cryptic IndexError deep in the light loop. It
    must RAISE at parse time so build()'s top-level guard fails the render loudly."""
    with pytest.raises((ValueError, TypeError)):
        mp.parse_light_warm({"light_warm": bad})


# ---------------------------------------------------------------------------
# ELEMENT 2 — west wall materials: Caesarstone counter + frameless mirror (2026-07-17)
# ---------------------------------------------------------------------------

def test_mill_object_role_routes_element2_parts():
    """The vanity/bookshelf parts route by their trailing PART TOKEN, same as element 1."""
    assert mp.mill_object_role("mill__vanity__counter") == "caesarstone"   # Caesarstone top
    assert mp.mill_object_role("mill__bf11vanity__mirror") == "mirror"     # frameless mirror
    assert mp.mill_object_role("mill__book__cool_vert0") == "microcement"  # cool bookshelf gables
    assert mp.mill_object_role("mill__vanity__cool_body0") == "microcement"
    assert mp.mill_object_role("mill__vanity__cool_toe1") == "microcement"
    assert mp.mill_object_role("mill__vanity__drawer_front0_2") == "microcement"
    assert mp.mill_object_role("mill__book__shelf3_2") == "oak"            # OAK shelf boards
    # a plain fallback box whose free-text name merely CONTAINS these words is NOT mis-painted
    assert mp.mill_object_role("mill__cool mirror console") == "oak"


def test_element2_presets_resolve_through_their_factories():
    for name, fac in (("caesarstone_quartz", "solid"), ("mirror_silver", "solid")):
        a = mp.factory_args(name)
        assert a["factory"] == fac, f"{name} -> {a['factory']}, wanted {fac}"


def test_the_makeup_mirror_is_a_real_metal_and_the_counter_is_a_cool_dielectric():
    """The mirror must stay Metallic 1.0 (a dielectric 'mirror' renders as grey paint, not a
    reflection). The Caesarstone counter is a COOL dielectric stone (blue >= red) — the west wall's
    cool counterpoint to the warm oak, and it must NOT read metallic."""
    mir = mp.factory_args("mirror_silver")
    assert mir["metallic"] == 1.0
    caesar = mp.factory_args("caesarstone_quartz")
    assert caesar.get("metallic", 0.0) in (0.0, 0)
    r, g, b = caesar["rgba"][:3]
    assert b >= r, f"Caesarstone must read cool (blue {b:.3f} >= red {r:.3f})"


def test_element2_preset_values_are_pinned_exactly():
    """Freeze the west-wall material VALUES so a retune can't silently warm the counter or dull the
    mirror away from what the DD decided."""
    P = mp.PRESETS
    assert (P["caesarstone_quartz"]["hex"], P["caesarstone_quartz"]["rough"]) == ("#BFC3C4", 0.28)
    assert (P["mirror_silver"]["hex"], P["mirror_silver"]["rough"], P["mirror_silver"]["metallic"]) \
        == ("#EAEDEE", 0.03, 1.0)


def test_material_story_names_the_vanity_caesarstone_and_mirror():
    """The render-polish {material_story} prompt says 'these are real specified products — do NOT
    restyle/recolour'. If it omits the on-screen Caesarstone counter + silver mirror, the polish pass
    warms the cool counter (killing element 2's cool counterpoint) or repaints the frameless mirror
    into a wood panel — the cardinal revert-by-omission the function exists to prevent (review
    2026-07-17). Pin that BOTH are named for the canonical spec."""
    import json, os
    p = os.path.join(os.path.dirname(__file__), "..", "..", "projects",
                     "PRJ-2026-002_c001-house", "03_layout", "master-suite.CANONICAL.spec.json")
    with open(p, encoding="utf-8") as fh:
        spec = json.load(fh)
    story = mp.material_story(mp.resolve_materials(spec), spec).lower()
    assert "caesarstone" in story or "quartz" in story, f"material_story omits the counter: {story!r}"
    assert "mirror" in story, f"material_story omits the makeup mirror: {story!r}"
    # and the subpart helper fires the vanity roles directly
    labels = {lab for lab, _ in mp.millwork_subpart_presets(spec)}
    assert {"vanity counter", "makeup mirror"} <= labels, f"vanity subparts missing: {labels}"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])


# --- ELEMENT 3: the bed base / lamps / rug must be NAMED in material_story (D7 anti-revert) -------
def test_furniture_material_story_names_the_decided_ffe():
    """The bespoke-built FF&E (upholstered bed base, brass lamps, rug) must be STATED so the polish
    pass cannot repaint the base oak or drop the lamps — the recurring element-2 revert-by-omission."""
    import json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    story = mp.material_story(mp.resolve_materials(spec), spec)
    assert "bed base" in story and "greige" in story, "bed base linen must be named (not repaintable to oak)"
    assert ("mushroom" in story or "dome" in story) and "brass" in story, "brass dome lamps must be named"
    assert "poly-wool" in story, "the rug must be named"


def test_furniture_bits_are_opt_in_per_item():
    assert mp.furniture_material_story_bits({}) == []
    assert mp.furniture_material_story_bits({"items": []}) == []
    # a bed WITHOUT the upholstered base_material flag contributes no base bit
    assert mp.furniture_material_story_bits({"items": [{"kind": "bed"}]}) == []
    # a plain side_table (no lamp) is not a nightstand
    assert mp.furniture_material_story_bits({"items": [{"kind": "side_table"}]}) == []


# ---------------------------------------------------------------- element-5 seams (scrutiny 2026-07-21)

def test_mill_object_role_e5_luminaire_tokens():
    assert mp.mill_object_role("mill__vanity_taskbar_opal__opal") == "opal"
    assert mp.mill_object_role("mill__vanity_taskbar_body__blackalu") == "blackalu"


def test_lighting_story_bits_schema_gated():
    assert mp.lighting_story_bits({}) == []
    assert mp.lighting_story_bits({"lighting": {"schema": "other"}}) == []
    bits = mp.lighting_story_bits({"lighting": {"schema": "e5-layers@0.1"}})
    assert bits and "opal task bar" in bits[0] and "do not flatten" in bits[0]


def test_bespoke_built_refuses_intercepted_items():
    assert mp.bespoke_built({"kind": "side_table", "lamp": {"kind": "dome"}})
    assert mp.bespoke_built({"kind": "stool", "style": "tub_chair"})
    assert not mp.bespoke_built({"kind": "stool"})
    assert not mp.bespoke_built({"kind": "side_table"})


# --- fixture_part_name: the CLOSED mat vocabulary (director review 2026-07-21 fix a) --------------

def test_fixture_part_name_routes_the_whole_closed_vocabulary():
    """Every row of FIXTURE_MAT_OBJECT routes to a name whose prefix/part-token lands on the
    intended suite material (via mill_object_role for the mill__ rows)."""
    assert mp.fixture_part_name("porcelain", "wc bowl") == "fix__wc_bowl"
    assert mp.fixture_part_name("glass", "shower_screen") == "glass__shower_screen"
    assert mp.fixture_part_name("oak", "vanity_cabinet") == "mill__vanity_cabinet"
    for mat, role in (("stone", "caesarstone"), ("brass", "brass"), ("mirror", "mirror"),
                      ("blackalu", "blackalu"), ("opal", "opal"), ("tray", "microcement"),
                      ("towel", "towel")):    # ELEMENT 6: the terry token's b-branch (D-E6-3)
        name = mp.fixture_part_name(mat, "p")
        assert mp.mill_object_role(name) == role, f"{mat} -> {name} -> {mp.mill_object_role(name)}"


def test_fixture_part_name_raises_on_unknown_mat():
    """The silent oak default was the revert-by-omission channel: blackalu/opal fell through it
    2026-07-20 (the task bar rendered OAK) and the e6 textile roles were predicted to be the 7th.
    An unknown mat must fail LOUD at build time, never quietly wear oak. ('towel' left this
    list 2026-07-21 — its red test was the e6 build's forced touch-point, DD consequence 10.)"""
    for bad in ("linen", "fabric", "terry", "", None, "OAK"):
        with pytest.raises(ValueError, match="closed"):
            mp.fixture_part_name(bad, "towel_stack")


# --- ELEMENT 4: the ensuite must be NAMED in material_story (director review 2026-07-21 fix c) ----

def test_material_story_names_the_ensuite_palette():
    """The ensuite contributed NOTHING to material_story (its fixtures are subroom fixtures, not
    builtins) — the polish pass would unify the cool room toward the bedroom's warmth. Pin that the
    canonical spec's story now carries the D-E4-1 ground + the fixture palette."""
    import json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    story = mp.material_story(mp.resolve_materials(spec), spec).lower()
    assert "porcelain" in story, "ensuite porcelain ground/sanitaryware must be named"
    assert "ensuite" in story and "only oak" in story, "the vanity-as-only-oak rule must be stated"
    assert "wet/dry partition" in story, "the frameless glass must be named"


def test_ensuite_bits_are_data_driven_on_the_bathroom_subroom():
    assert mp.ensuite_material_story_bits({}) == []
    assert mp.ensuite_material_story_bits({"subrooms": [{"type": "wardrobe"}]}) == []
    ground_only = mp.ensuite_material_story_bits({"subrooms": [{"type": "bathroom"}]})
    assert len(ground_only) == 1 and "porcelain" in ground_only[0]
    full = mp.ensuite_material_story_bits({"subrooms": [{"type": "bathroom", "fixtures": [
        {"kind": "vanity_double"}, {"kind": "toilet"}, {"kind": "shower"}]}]})
    assert len(full) == 2 and "only oak" in full[1] and "shower" in full[1]


# --- ELEMENT 6 (D-E6-1..-5): sheers + BARE casements + textiles in the story ----------

def test_casement_sheer_bit_is_gated_on_the_spec_block():
    assert mp.casement_sheer_story_bits({}) == []
    assert mp.casement_sheer_story_bits({"casement_sheers": {}}) == []
    assert mp.casement_sheer_story_bits({"casement_sheers": {"windows": {}}}) == []
    bits = mp.casement_sheer_story_bits({
        "casement_sheers": {"windows": {"glz-west-win1": {"state": "drawn"},
                                        "glz-west-win2": {"state": "drawn"}}},
        "curtains": {"render_state": {"sheer_alpha": 0.38}}})
    assert len(bits) == 1
    assert "0.38" in bits[0], "the sheers' alpha must be named (probe: alpha-0.38)"
    assert "opal strips" in bits[0] and "unoccluded" in bits[0]
    assert "mirror pier" in bits[0] and "BARE" in bits[0]


def test_ensuite_bare_casements_bit_gated_on_the_openings():
    """D-E6-2 probe: the BARE line rides only when the ensuite subroom + its casement
    openings exist — never on a bathroom without windows."""
    no_win = mp.ensuite_material_story_bits({"subrooms": [{"type": "bathroom",
        "openings": [{"type": "door"}]}]})
    assert not any("BARE" in b for b in no_win)
    with_win = mp.ensuite_material_story_bits({"subrooms": [{"type": "bathroom",
        "openings": [{"type": "window", "id": "glz-ensuite-win1"}]}]})
    bare = [b for b in with_win if "BARE" in b]
    assert len(bare) == 1 and "shower curtain" in bare[0] and "coherence carrier" in bare[0]


_E6_CENSUS = {"bath_on_bar": 2, "hand_on_south_hook": 1, "hand_on_counter": 1,
              "robes_on_north_hook": 2, "bath_mat": 1}


def _acc_spec(census):
    fx = {"kind": "bath_accessories"}
    if census is not None:
        fx["design"] = {"census": census}
    return {"subrooms": [{"type": "bathroom", "fixtures": [fx]}]}


def test_ensuite_textiles_bit_gated_on_the_accessories_fixture():
    no_acc = mp.ensuite_material_story_bits({"subrooms": [{"type": "bathroom",
        "fixtures": [{"kind": "toilet"}]}]})
    assert not any("terry" in b.lower() for b in no_acc)
    with_acc = mp.ensuite_material_story_bits(_acc_spec(_E6_CENSUS))
    tex = [b for b in with_acc if "terry" in b.lower()]
    assert len(tex) == 1
    assert "no towel over the glass or tub edge" in tex[0], "D-E6-5 wording missing"
    assert "NOT cream" in tex[0], "the NOT-cream tonal rule must be stated (LOOK anchor)"
    assert "only warmth" in tex[0]
    assert "2 bath towels" in tex[0] and "2 robes" in tex[0]


def test_ensuite_textiles_bit_derives_from_the_census_one_source():
    """Review catch 2026-07-21 (two lenses, verified): the first cut HARDCODED the
    counts, so the DD's own 18in fallback (census bath_on_bar -> 1) would render one
    towel while the prose told the Gemini polish to paint the second back. The census
    is the ONE source (D-E6-3): edits must change the prose; a censusless fixture
    (the emitter RAISES on it) must contribute NO counted prose."""
    fallback = dict(_E6_CENSUS, bath_on_bar=1, robes_on_north_hook=1,
                    hand_on_counter=0)
    tex = [b for b in mp.ensuite_material_story_bits(_acc_spec(fallback))
           if "terry" in b.lower()][0]
    assert "1 bath towel" in tex and "2 bath towels" not in tex
    assert "1 robe" in tex and "2 robes" not in tex
    assert "counter" not in tex, "a zero-count clause must be omitted"
    assert not any("terry" in b.lower()
                   for b in mp.ensuite_material_story_bits(_acc_spec(None))), \
        "censusless fixture must not yield counted prose (the build RAISES on it)"
    assert not any("terry" in b.lower()
                   for b in mp.ensuite_material_story_bits(_acc_spec(
                       {k: 0 for k in _E6_CENSUS})))


def test_mill_object_role_survives_blender_duplicate_suffix():
    """Review catch 2026-07-21: Blender silently renames a colliding object to
    name.001 — the exact-match tokens (towel/opal/blackalu) then fell through to the
    oak default, the SAME silent-walnut channel the e5 task bar fell down."""
    assert mp.mill_object_role("mill__acc_bath_towel0__towel.001") == "towel"
    assert mp.mill_object_role("mill__vanity_taskbar_opal__opal.002") == "opal"
    assert mp.mill_object_role("mill__vanity_taskbar_body__blackalu.001") == "blackalu"
    assert mp.mill_object_role("mill__x__towel.abc") == "oak"   # not a Blender suffix


def test_material_story_bits_survive_a_spec_without_a_materials_block():
    """Review catch 2026-07-21: the `if not resolved` early return dropped EVERY
    protective bit (BARE casements, terry, sheers, e5 lighting) for a spec without a
    materials block — all the anti-repaint armour hung on an unrelated block."""
    import copy, json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    bare = copy.deepcopy(spec)
    del bare["materials"]
    story = mp.material_story(mp.resolve_materials(bare), bare)
    assert "existing studio palette" in story, "legacy palette sentence must lead"
    for marker in ("casement sheers", "BARE black-alu", "greige-oatmeal TERRY",
                   "no towel over the glass or tub edge", "lighting is DELIBERATE"):
        assert marker in story, f"protective bit lost without the materials block: {marker}"
    # a spec with neither presets nor decided-element data = the legacy sentence verbatim
    assert mp.material_story(None) == ("the existing studio palette: warm oak plank "
                                       "floor, matte warm-white walls, walnut feature "
                                       "wall and millwork, cream boucle upholstery")


def test_material_story_canonical_carries_the_e6_lines():
    """The canonical spec's story must now name sheers + BARE casements + terry — the
    three e6 lines the Gemini polish pass would otherwise revert (strip the sheers,
    hang a shower curtain, warm the towels to cream)."""
    import json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    story = mp.material_story(mp.resolve_materials(spec), spec)
    assert "casement sheers" in story and "0.38" in story
    assert "BARE black-alu" in story and "shower curtain" in story
    assert "greige-oatmeal TERRY" in story
    assert "no towel over the glass or tub edge" in story


# ---------------------------------------------------------------------------
# CLOTH SURFACE SIGNATURE (the _woven layer, 2026-07-22)
# ---------------------------------------------------------------------------

def test_every_cloth_kind_is_complete_and_in_band():
    """Kills a mutant that adds a half-filled CLOTH_KINDS row. Every row must carry the
    six channels the build reads, and each must sit in a band that is physically a
    TEXTILE: a weave finer than its own slub, a relief measured in millimetres not
    centimetres, and a sheen roughness inside the only sourced band the vault has
    (Corona fabric cards 0.4-0.6, texture-sets-discord.md:170-195)."""
    assert mp.CLOTH_KINDS, "the cloth vocabulary must not be empty"
    for kind, row in mp.CLOTH_KINDS.items():
        for key in ("slub_mm", "weave_mm", "relief_mm", "bump", "albedo_var",
                    "sheen_rough", "desc"):
            assert key in row, f"{kind}: missing {key}"
        assert row["weave_mm"] < row["slub_mm"], (
            f"{kind}: the thread band must be FINER than the slub band, else the two "
            f"noise fields collapse into one and the surface reads as static")
        # relief_mm is the PHYSICAL claim and stays in the band real cloth occupies.
        assert 0.3 <= row["relief_mm"] <= 4.0, f"{kind}: relief_mm out of cloth band"
        # bump is a RENDER GAIN, not physics — the ceiling is a typo guard, and it sits
        # where the 2026-07-22 amplitude bisect put the useful range (0.30 invisible under
        # this room's soft light, 0.85 read but coarse). Do not read it as a measurement.
        assert 0.0 < row["bump"] <= 0.9, f"{kind}: bump outside the LOOK-bracketed range"
        # the albedo MULTIPLY darkens the SIGNED mean tone by ~albedo_var/2, so this
        # ceiling is the real constraint: 0.15 == a 7.5% shift, past what may be spent
        # silently on an owner-signed colour.
        assert 0.0 < row["albedo_var"] <= 0.15, (
            f"{kind}: albedo_var this high shifts an owner-SIGNED colour too far")
        assert 0.4 <= row["sheen_rough"] <= 0.6, (
            f"{kind}: sheen_rough outside the only sourced band the vault holds")


def test_cloth_args_converts_to_metres_and_raises_on_unknown():
    """The build consumes METRES. Kills a mutant that leaks millimetres into the shader
    (a 28x oversize slub = MA-02 texture-scale error), and one that lets an unknown kind
    fall back to a flat slab instead of raising."""
    a = mp.cloth_args("linen")
    assert abs(a["slub_m"] - 0.026) < 1e-9 and abs(a["weave_m"] - 0.005) < 1e-9
    assert abs(a["relief_m"] - 0.0026) < 1e-9
    assert a["kind"] == "linen"
    with pytest.raises(ValueError):
        mp.cloth_args("hessian")


def test_scatter_identities_are_actually_distinct():
    """MA-01 (pbr-material-behavior.md:102-106): each fabric's scatter signature must be
    distinct, so one vocabulary row copy-pasted onto another is a defect. Kills a mutant
    that makes velvet and boucle share numbers."""
    sigs = {k: (r["slub_mm"], r["weave_mm"], r["relief_mm"], r["bump"])
            for k, r in mp.CLOTH_KINDS.items()}
    assert len(set(sigs.values())) == len(sigs), f"duplicate scatter signatures: {sigs}"
    # the two the vault names explicitly must not converge: boucle is LOOPS (most relief),
    # velvet is PILE whose identity is sheen (least relief)
    assert mp.CLOTH_KINDS["boucle"]["relief_mm"] > mp.CLOTH_KINDS["velvet"]["relief_mm"]


def test_every_sheen_bearing_solid_preset_is_cloth():
    """THE OMISSION GUARD, proven rather than asserted. A sheen-bearing solid IS a textile
    in this palette, so factory_args must hand the build a cloth block for every one of
    them — otherwise that fabric silently ships as an untextured slab (MA-05), which is
    this studio's recurring wound wearing a new hat. Kills a mutant that drops the raise."""
    seen = 0
    for name, p in mp.PRESETS.items():
        # MIRROR factory_args' condition exactly, metallic test included — if this drifts
        # from the guard, one of them is lying about what counts as a textile.
        if (p["factory"] != "solid" or float(p.get("sheen", 0.0)) <= 0.0
                or float(p.get("metallic", 0.0)) != 0.0):
            continue
        seen += 1
        a = mp.factory_args(name)
        assert a.get("cloth"), f"{name} is a textile preset with no cloth block"
        assert a["cloth"]["kind"] in mp.CLOTH_KINDS
    assert seen >= 4, f"expected the palette's textile presets, found {seen}"


def test_a_new_fabric_preset_without_a_cloth_row_raises():
    """Swap-and-demand-red (the dd-gate mechanic): adding a fabric preset while FORGETTING
    its cloth row must fail LOUD at build time, not render flat. Kills a mutant that
    silently defaults."""
    mp.PRESETS["_probe_fabric"] = dict(
        factory="solid", space="srgb", hex="#D8D2C6", rough=0.8, sheen=0.6,
        tier="STUDIO", desc="probe", source="test")
    try:
        with pytest.raises(ValueError, match="no PRESET_CLOTH row"):
            mp.factory_args("_probe_fabric")
    finally:
        del mp.PRESETS["_probe_fabric"]


def test_non_cloth_presets_carry_no_cloth_block():
    """Kills a mutant that hands a cloth block to stone/metal/glass/paint, which would
    put a fabric weave on a marble counter."""
    for name in ("honed_marble", "satin_brass", "clear_glass", "warm_white_paint",
                 "sanitary_white", "neutral_solid", "powder_coat_black"):
        assert "cloth" not in mp.factory_args(name), f"{name} must not be cloth"


def test_textile_story_bit_derives_from_spec_referents():
    """The bit must name only cloth the build actually makes. Kills a mutant that
    hardcodes the sentence: remove the bed and the linen clause must go with it."""
    assert mp.textile_surface_story_bits({}) == []
    bits = mp.textile_surface_story_bits({"items": [{"kind": "bed"}]})
    assert bits and "WOVEN, not painted" in bits[0]
    assert "bed base" in bits[0] and "stonewashed linen" in bits[0]
    assert "terry" not in bits[0], "no ensuite in this spec — terry must not be claimed"
    # the ensuite census is the terry referent, exactly as the e6 bit derives it
    # the ensuite census is the terry referent — and the fixture shape here MUST be the one
    # bathroom.accessory_parts actually accepts (kind 'bath_accessories', census a non-empty
    # DICT; it RAISES on anything else). The first version of this fixture used
    # kind 'accessories' with a LIST census — a shape the build rejects — so the test
    # certified prose for a fixture that could never be built.
    with_bath = mp.textile_surface_story_bits({
        "items": [{"kind": "bed"}],
        "subrooms": [{"type": "bathroom",
                      "fixtures": [{"kind": "bath_accessories",
                                    "design": {"census": {"bath_towel": 2}}}]}]})
    assert "terry" in with_bath[0] and "ensuite towels" in with_bath[0]


def test_terry_bit_refuses_a_fixture_shape_the_build_would_reject():
    """Kills a mutant that claims terry off any truthy design.census. bathroom.py routes on
    kind == 'bath_accessories' with a DICT census and raises otherwise, so a bit that fires
    on kind 'accessories' or a list census is prose describing cloth the build never makes."""
    for bad in ({"kind": "accessories", "design": {"census": {"bath_towel": 2}}},
                {"kind": "bath_accessories", "design": {"census": [{"item": "towel"}]}},
                {"kind": "bath_accessories", "design": {"census": {}}}):
        bits = mp.textile_surface_story_bits({"items": [{"kind": "bed"}],
                                              "subrooms": [{"type": "bathroom",
                                                            "fixtures": [bad]}]})
        assert bits and "terry" not in bits[0], f"terry claimed off a rejected shape: {bad}"


def test_curtain_layers_are_named_by_type_not_by_a_state_adjective():
    """The canonical suite parks its linen blackout and draws the sheer, so a bit that calls
    the linen layer 'the drawn curtain' tells the polish pass the wrong panel is linen.
    Kills that mutant: the label must name the LAYER (what build_room routes on), never its
    state — and it must not silently disagree with curtains.render_state."""
    bits = mp.textile_surface_story_bits({"items": [{"kind": "bed"}],
                                          "curtains": {"render_state": {"blackout": "parked",
                                                                        "privacy": "drawn"}}})
    assert bits
    assert "drawn curtain" not in bits[0], "prose asserts a curtain STATE it does not derive"
    assert "blackout" in bits[0] and "sheer" in bits[0]


# ---------------------------------------------------------------------------
# BUILD-SIDE PIN for the weave (source-text, the studio's mechanic for the bpy layer —
# same shape as test_wardrobe_bay / test_casement_sheers / test_drape_feedstock).
# ---------------------------------------------------------------------------

def _build_room_src():
    import os
    with open(os.path.join(os.path.dirname(__file__), "build_room.py"), encoding="utf-8") as fh:
        return fh.read()


# every textile the suite builds by NAME through a bespoke builder or the palette
_WOVEN_NAMED = (
    "bed_base", "bed_mattress", "bed_duvet", "bed_pillow", "bed_coverlet",
    "bench_seat", "stool_uph", "curtain_opaque", "fabric_boucle",
    "m_mill_towel", "m_mill_linen", "sofa_boucle", "sofa_base",
    "cush_terra", "cush_sage",
)


def test_every_named_textile_is_built_woven_not_solid():
    """THE ARMOUR'S MISSING HALF, and the reason this test exists: a reviewer reverted three
    `_woven` call sites to `_solid` and the whole suite stayed GREEN while
    textile_surface_story_bits kept telling the polish pass "every textile in this room is
    WOVEN". Decided data that silently stops being built, with prose still asserting it, is
    this studio's recurring wound — and the pure layer cannot see it, because the routing
    lives in build_room's bpy layer. So pin the SOURCE, both halves: the _woven call must be
    there AND the _solid call must not (without the negative, a revert only has to rename)."""
    src = _build_room_src()
    for name in _WOVEN_NAMED:
        assert f'_woven("{name}"' in src, (
            f'{name} is no longer built WOVEN — it would ship as an untextured slab (MA-05) '
            f'while the story bit still claims a weave')
        assert f'_solid("{name}"' not in src, (
            f'{name} was reverted to the untextured _solid factory')


def test_the_sheer_body_is_woven():
    """_curtain_sheer names its material from a PARAMETER, so the by-name pin above cannot
    see it — pin the function BODY instead (the test_casement_sheers body-pin shape)."""
    src = _build_room_src()
    body = src.split("def _curtain_sheer", 1)[1].split("\ndef ", 1)[0]
    assert "_woven(" in body and "_solid(" not in body, (
        "the sheer reverted to _solid — the one fabric the light passes THROUGH would "
        "render as tinted glass")


def test_preset_cloth_branch_stays_ABOVE_the_solid_fallthrough():
    """Existence is not enough: the E7 lesson is that an un-pinned branch can drift BELOW
    the dispatch it must precede, and then every textile preset falls through to the
    untextured slab with nothing red. Pin the ORDER."""
    src = _build_room_src()
    body = src.split("def _material_from_preset", 1)[1].split("\ndef ", 1)[0]
    i_cloth = body.find('a.get("cloth")')
    i_solid = body.find("return _solid(")
    assert i_cloth != -1, "the cloth branch is gone from _material_from_preset"
    assert i_solid != -1, "the _solid fallthrough is gone — this pin needs re-deriving"
    assert i_cloth < i_solid, (
        "the cloth branch drifted BELOW the _solid fallthrough: every textile preset now "
        "renders as an untextured slab")


def test_textile_story_prose_derives_from_the_vocabulary_not_a_copy():
    """The e6 prose-copy lesson: the sentence must be built from CLOTH_KINDS[...]['desc'],
    so retuning the vocabulary retunes the armour. Kills a mutant that pastes the text."""
    original = mp.CLOTH_KINDS["linen"]["desc"]
    mp.CLOTH_KINDS["linen"]["desc"] = "MARKER-XYZ"
    try:
        bits = mp.textile_surface_story_bits({"items": [{"kind": "bed"}]})
        assert "MARKER-XYZ" in bits[0], "the story bit holds a second copy of the prose"
    finally:
        mp.CLOTH_KINDS["linen"]["desc"] = original


def test_canonical_story_names_the_weave():
    """The canonical suite must tell the polish pass its textiles are woven — without this
    line the render carries a surface the prose never claims and the repaint may iron it
    flat (the channel that repainted the cool counter oak)."""
    import json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    story = mp.material_story(mp.resolve_materials(spec), spec)
    assert "WOVEN, not painted" in story
    assert "do NOT smooth, gloss, iron flat" in story
    assert "stonewashed linen" in story and "terry" in story


# ---------------------------------------------------------------- the VALUE ladder (2026-07-23)

def test_tonal_ladder_bit_is_gated_on_a_bed_the_build_would_actually_make():
    """Same referent the BUILD routes on (_build_bed fires for kind == 'bed'). A spec with
    no bed must not describe a ladder nobody rendered."""
    assert mp.tonal_ladder_story_bits({}) == []
    assert mp.tonal_ladder_story_bits({"items": []}) == []
    assert mp.tonal_ladder_story_bits({"items": [{"kind": "rug"}]}) == []
    assert len(mp.tonal_ladder_story_bits({"items": [{"kind": "bed"}]})) == 1


def test_tonal_ladder_prose_derives_from_the_tone_table_not_a_copy():
    """The whole defect this guards is values that drifted apart from the words describing
    them. An armour bit holding its own copy of those values would drift the same way —
    twice caught in review already ("2 bath towels", "21 shelf parts"). Kills a mutant
    that pastes the sentence."""
    import value_ladder as vl
    before = mp.tonal_ladder_story_bits({"items": [{"kind": "bed"}]})[0]
    vl.TONES["MARKER-XYZ"] = 0.33
    vl.MATERIAL_TONE["bed_marker"] = "MARKER-XYZ"
    try:
        after = mp.tonal_ladder_story_bits({"items": [{"kind": "bed"}]})[0]
        assert "MARKER-XYZ" in after, "the story bit holds a second copy of the tone table"
        assert after != before
    finally:
        del vl.TONES["MARKER-XYZ"]
        del vl.MATERIAL_TONE["bed_marker"]


def test_canonical_story_names_the_tonal_ladder():
    """Without this line the polish pass is told the cloths and NOT their value structure,
    and 'greige stonewashed linen' alone is an instruction it can satisfy at any lightness
    — which is how the bed spent five elements as one near-white mass."""
    import json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    story = mp.material_story(mp.resolve_materials(spec), spec)
    assert "tonal ladder" in story
    assert "told apart by VALUE" in story
    assert "do NOT" in story and "single cream" in story


def test_the_bed_base_bit_no_longer_calls_the_deepest_cloth_a_mid_tone():
    """Measured: plinth 121.1, throw 155.1, bench 178.2 — with the bench ABOVE the coverlet
    it stands in front of. 'a mid-greige plinth below the crisp bedding' described none of
    that, and prose that outlives its measurement is the class this file keeps catching."""
    bits = mp.furniture_material_story_bits(
        {"items": [{"kind": "bed", "design": {"base_material": "upholstered_greige_linen"}}]})
    assert len(bits) == 1
    assert "mid-greige plinth" not in bits[0]
    assert "DEEPEST value" in bits[0]
