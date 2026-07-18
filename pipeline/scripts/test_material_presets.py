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
