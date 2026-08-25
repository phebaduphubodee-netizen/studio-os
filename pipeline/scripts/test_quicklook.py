"""R5 playblast-ladder armour (quicklook.py + its build_room consumption).

Why these pins exist: R5's whole value is that the cheap rung is (a) actually
cheap, (b) never overwrites the deliverable pair, and (c) actually WIRED — a
design decision must never be revertible by an omission, and a ladder rung that
build_room stopped consuming would revert R5 with every test green.
"""
import pathlib

import quicklook

SRC = (pathlib.Path(__file__).parent / "build_room.py").read_text(encoding="utf-8")


# ---- the rung is strictly cheaper ------------------------------------------------

def test_quick_is_strictly_cheaper_on_the_deliverable_pair():
    for samples, res in ((256, (2000, 1400)), (400, (2400, 1500)), (128, (1600, 1000))):
        qs, (qw, qh) = quicklook.quick_params(samples, res)
        assert qs < samples
        assert qw * qh <= res[0] * res[1] * 0.3   # ≤ ~1/4 the pixels (0.5 per axis)


def test_quick_never_exceeds_a_deliverable_already_cheaper_than_the_rung():
    # a hypothetical 16-sample deliverable must not be made MORE expensive
    qs, _ = quicklook.quick_params(16, (400, 300))
    assert qs == 16


def test_quick_never_returns_a_degenerate_frame():
    _, (w, h) = quicklook.quick_params(48, (20, 20))
    assert w >= 16 and h >= 16


# ---- the rung is wired (anti-omission armour, source-slice style) ----------------

def test_build_room_parses_the_quick_flag_and_forces_a_render():
    main = SRC.split('if __name__ == "__main__"', 1)[1]
    flag = main.split('"--quick"', 1)[1].split('if "--hero"', 1)[0]
    assert '_spec["_quick"] = True' in flag
    assert '_spec["render"] = True' in flag       # a quick-look that renders nothing is a no-op


def test_suite_path_applies_the_rung_and_renames_the_output():
    # slice: from the deliverable sample choice to the render call in build_suite.
    # The READER-side gate is pinned too (mutant-proven at review 2026-07-28:
    # renaming spec.get("_quick") left every pin green while --quick silently
    # became a full-price render OVERWRITING the deliverable pair).
    suite = SRC.split("_samples = 400 if hero else 256", 1)[1].split("render(name, samples=_samples", 1)[0]
    assert 'if spec.get("_quick"):' in suite                 # reader key == writer key
    assert "quicklook.quick_params(_samples, _res)" in suite
    assert 'name += "_" + quicklook.QUICK_SUFFIX' in suite   # never overwrite the deliverable pair


def test_reserved_ql_suffix_is_refused_before_build():
    # review 2026-07-28: `--suffix=ql --render` at full fidelity would write the
    # SAME output name as `--quick` — the one collision the _ql scheme promises
    # cannot happen. The refusal must sit in main AFTER the eyecam suffix merge.
    main = SRC.split('if __name__ == "__main__"', 1)[1]
    guard = main.split("_sfx_final", 1)[1]
    assert "quicklook.QUICK_SUFFIX" in guard
    assert "os._exit(1)" in guard.split("try:", 1)[0]         # hard exit, headless-safe


def test_rect_path_applies_the_rung_to_both_save_and_render():
    rect = SRC.split('name = r.get("type", "room")', 1)[1].split("built '", 1)[0]
    assert 'if spec.get("_quick"):' in rect                  # reader key == writer key
    assert "quicklook.quick_params(_qs, _qr)" in rect
    assert "save(name, samples=_qs, res=_qr)" in rect
    assert "render(name, samples=_qs, res=_qr)" in rect      # render must consume the SAME rung


def test_cloth_styling_parts_route_through_the_solver():
    """ROUND 5 armour (lives here because build_room.py source is already loaded):
    a styling part that declares `cloth` MUST reach drape.bake_sheet with its
    declared pins — dropping the branch silently reverts every garment to the
    analytic read the owner refused three times, with all green."""
    seg = SRC.split("def _emit_style_part", 1)[1].split("def _add_styling", 1)[0]
    assert 'p.get("cloth")' in seg
    assert "drape.bake_sheet" in seg
    assert 'pin=cl["pin"]' in seg
    assert "self_collide=True" in seg
    # the HYBRID fallback (owner "(ก2)"): ladder exhausted -> the analytic twin is
    # emitted LOUDLY; deleting this branch would turn every unstable piece back
    # into a build failure (or worse, a shipped shred) with all green
    assert 'cl.get("analytic")' in seg
    assert "ANALYTIC fallback" in seg
    assert '_smooth_mesh_obj(p["name"], an["verts"], an["faces"]' in seg


def test_light_story_scales_are_unity_when_off_and_focal_when_on():
    """Lane-A armour: story OFF must be byte-identical to the signed CD state
    (every scale exactly 1.0); story ON must dim ambient BELOW the focal layers
    so the vault's ~3:1 accent:ambient ratio is reachable (lumen-method file:48).
    Lane-B additions (ground-truth study): the story must DEMOTE the cool fill
    (the measured no-key signature — our strongest source was the fill) and
    PROMOTE the env (same-genre file feeds ~3.6x our energy)."""
    import element5_lighting as e5
    off = e5.story_scales(False)
    assert all(v == 1.0 for v in off.values())
    on = e5.story_scales(True)
    assert on["ambient"] < 0.5
    assert on["fill"] < 0.5 < 1.0 < on["hdri"], "story must demote fill, promote env"
    assert 1.0 < e5.STORY_FSTOP < 9.0, "story aperture opens toward the measured f/1.4-2.4"
    # per-zone: the dressing zone stays brighter than the room (task+display),
    # and unknown zones fall back to the room ambient
    assert e5.ambient_scale(on, "โซนตู้เสื้อผ้า (wardrobe bay)") > on["ambient"]
    assert e5.ambient_scale(on, "bedroom") == on["ambient"]
    assert on["spots"] / on["ambient"] >= 3.0
    assert on["lamps"] > 1.0


def test_lane_c_geometry_reaches_the_frame():
    """Round-6 lane C armour (the revert-by-omission class): the pure layers grew
    joinery/asymmetry that build_room must CONSUME — a materializer that quietly
    keeps handling only the old part names reverts the lane with every test green."""
    for pin in (
        # nightstand joinery: toe shadow + carcass/drawer with the reveal between them
        '"nightstand__toe"', 'f"nightstand__{name}"',
        # the lamp is the spun-brass DOME + glowing bulb (P2 redesign replaced
        # the emission-gradient shade; this pin went stale and sat red until
        # p3r2 — updated to the mechanism that actually ships, 2026-08-11)
        '_dome_h = min(dz, r * 0.62)', '"nightstand__lamp_bulb"',
        # duvet feedstock enters asymmetric (C2#4 mirror corners)
        'cell=0.042, salt=7'):
        assert pin in SRC, pin


def test_light_story_reaches_every_consumer():
    """The flag must scale ALL layers — a layer that misses the dimmer keeps the
    wash and silently reverts the story (the revert-by-omission class)."""
    for pin in ('_e5.ambient_scale(_sc, f["zone"])', '* _sc["strips"]', '* _sc["bar"]',
                '* _sc["spots"]', 'story_scales(_LIGHT_STORY)["lamps"]',
                '"--light-story" in _post_dashdash()',
                'view_settings.exposure -= 0.10',
                # visible luminaires (C2: "แสงไม่มีที่มา") — every plan position
                # must carry its recessed trim, downlights AND wall-wash spots
                '_recessed_trim(f"dl{i}"', '_recessed_trim(s["name"]',
                # lane B (ground-truth study): fill demotes, env promotes, aperture
                # opens, real photometric beams land on cans AND wash spots
                'story_scales(_LIGHT_STORY)["fill"]',
                '["hdri"]',
                # e5 amendment (gate #8): the cove pelmet + sconce pair must be
                # BUILT, and the sconce beams carry the wall-luminaire profile
                'e5_cove_pelmet', '_ies_beam(ld, "1.IES"', '_sc.get("cove"',
                # B2: the coverlet feedstock enters per-corner biased (the owed debt)
                'sim_surface=True, salt=5',
                # lane D: the bench carries life — books + an ACQUIRED folded throw
                # (p2r72, D-137: the last solver-baked cloth left the frame; the
                # throw now enters through _model_path/place_model and is re-dressed
                # in the duvet's own handle, so no new colour ever enters this way)
                'deco__bench_book', '_BENCH_THROW_MODEL',
                'bpy.data.materials.get("bed_duvet")',
                '_e5.STORY_FSTOP if _LIGHT_STORY else 9.0',
                '_ies_beam(ld, "5.ies"', '_ies_beam(ld, "7.IES"',
                # ...and the profile must stay NORMALIZED (raw Fac re-powers the
                # rig — the b1 rung measured mean 84->166 with clipping whites)
                'mul.inputs[1].default_value = float(norm)'):
        assert pin in SRC, pin


def _assert_every_sheen_write_is_capped():
    """EVERY write of Sheen Weight is a literal or is clamped to _SHEEN_CAP.

    THIS REPLACES A TEST THAT PASSED WHILE THE RULE WAS BROKEN. The old assertion
    was `'min(sheen, _SHEEN_CAP)' in SRC` — a SOURCE-STRING existence check. The
    string existed (in `_woven`), so the test was green for the whole lane while
    `_solid` and `_retint_upholstery` wrote the socket uncapped and
    `acq_bench_seat` shipped sheen 0.45 on 9.68% of the frame's pixels.
    Measured 2026-08-24 by a value-anchored sweep of all 84 built materials.

    A check anchored on ONE spelling of the rule is an allowlist one level down:
    it names the site it covers and exempts the next site. So this counts the
    WRITES instead, and fails when a new one appears uncapped."""
    import re
    writes = re.findall(r'_set\(\s*\w+\s*,\s*"Sheen Weight"\s*,\s*([^)]+)\)', SRC)
    assert writes, "no Sheen Weight write found — the pattern moved, fix this test"
    bad = [w.strip() for w in writes
           if "_SHEEN_CAP" not in w and not re.fullmatch(r"[\d.]+", w.strip())]
    assert not bad, (
        "uncapped Sheen Weight write(s): %r — clamp at the write site, not at the "
        "caller. _SHEEN_CAP is a rule and rules that are only declared get written "
        "past." % bad)


def test_lane_b_fabric_maps_reach_the_bed_textiles():
    """Ground-truth lane B armour: the CC0 linen set must be OFFERED to every bed
    textile + the bench (maps=), the sheen cap must guard the _solid call, and the
    A/B flag must be parseable — any of these silently dropped reverts the lane."""
    assert SRC.count('maps="rough_linen"') >= 6      # 5 bed cloths + bench seat
    _assert_every_sheen_write_is_capped()
    assert '"--fabric-maps" in _post_dashdash()' in SRC
    assert '_FABRIC_MAPS' in SRC
    for pin in ('subsurf=p.get("subsurf", 0)', 'subsurf=_p.get("subsurf", 0)'):
        assert pin in SRC, pin                        # SUBSURF reaches both mesh paths
