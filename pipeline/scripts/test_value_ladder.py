"""Tests for value_ladder.py — the suite's soft goods as a TONAL LADDER.

These pin the LAW, not the numbers. The module exists because six pieces of one bed
rendered inside 7.1 sRGB codes of each other while every builder held its own colour
tuple, so the tests must be able to tell a ladder from a repaint:
  - one hue, several values (no piece may drift to its own colour);
  - every value inside the studio's own 30-240 dielectric band;
  - adjacent rungs far enough apart that the eye can rank them;
  - and the whole thing RAISES rather than warning, because a silently-repainted signed
    textile is this studio's recurring wound.

Swap-and-demand-red: several tests MUTATE the shipped data and require the module to go
red. A guard nobody has watched fail is not a guard.

Pure python — no bpy, no Blender.
"""
import copy

import pytest

import material_presets as mp
import value_ladder as vl


@pytest.fixture
def pristine():
    """Restore the module's data after a test mutates it."""
    tones, mats, ladder, hue = (copy.deepcopy(vl.TONES), copy.deepcopy(vl.MATERIAL_TONE),
                                copy.deepcopy(vl.LADDER), vl.HUE)
    yield
    vl.TONES, vl.MATERIAL_TONE, vl.LADDER, vl.HUE = tones, mats, ladder, hue


# --------------------------------------------------------------------------- the shipped data

def test_shipped_data_validates():
    """The module validates itself on import; this states it as a test so a red here
    names the file rather than blowing up every importer with an ImportError."""
    assert vl.validate() is True


def test_every_tone_inside_the_studio_albedo_band():
    """knowledge/materials/pbr-material-behavior.md:55 — non-metals sit strictly between
    30 and 240 sRGB. The bespoke bed path never applied it: the pillows shipped at 0.90
    linear = sRGB 243.5, and `albedo_plausible()` could not see it because it guards
    0.04-0.94 in a different unit."""
    for mat in vl.MATERIAL_TONE:
        for code in vl.codes(mat):
            assert vl.SRGB_BAND_LO <= code <= vl.SRGB_BAND_HI, (mat, vl.codes(mat))


def test_band_is_not_a_second_copy_of_the_studio_bound():
    """Two copies of a bound is how one goes stale — the band comes FROM material_presets."""
    assert (vl.SRGB_BAND_LO, vl.SRGB_BAND_HI) == (mp._SRGB_BAND_LO, mp._SRGB_BAND_HI)


def test_the_old_shipped_pillow_tone_would_now_fail(pristine):
    """The exact value that shipped for four elements must be rejected by name."""
    vl.TONES["pillowcase"] = 0.90
    with pytest.raises(vl.LadderError, match="over the studio dielectric ceiling"):
        vl.validate()


def test_a_tone_under_the_floor_fails(pristine):
    vl.TONES["upholstery"] = 0.001
    with pytest.raises(vl.LadderError, match="under the studio floor"):
        vl.validate()


# --------------------------------------------------------------------------- one hue

def test_every_material_is_the_same_hue():
    """MONOCHROMATIC, by construction: color-composition.md §1 (สีเดียวหลายน้ำหนัก) is the
    one harmony that adds contrast without adding a colour, and the palette is closed.
    The old tuples drifted anyway — the pillows were authored markedly cooler and greyer
    than the base, which is how signed 'greige-oatmeal' rendered as cream."""
    ratios = set()
    for mat in vl.MATERIAL_TONE:
        r, g, b, _a = vl.rgba(mat)
        ratios.add((round(g / r, 6), round(b / r, 6)))
    assert len(ratios) == 1, ratios


def test_the_hue_is_warm_greige_not_a_neutral_grey():
    """Greige is warm: r > g > b. A neutral grey here would be the 'reads cream/grey'
    defect wearing the ladder's clothes."""
    r, g, b, _a = vl.rgba("bed_coverlet")
    assert r > g > b


def test_hue_is_element_3s_signed_base_colour():
    """The family hue is D3-1's own (0.46, 0.43, 0.39) — the ladder re-values the signed
    linen, it does not re-colour it."""
    assert vl.HUE == pytest.approx((1.0, 0.43 / 0.46, 0.39 / 0.46))


# --------------------------------------------------------------------------- the tone table

def test_unknown_material_raises_rather_than_defaulting():
    """A typo must not silently fall back to a default tone — a shared default is exactly
    how the bed became one value."""
    with pytest.raises(vl.LadderError, match="no tone for material"):
        vl.rgba("bed_bolster")


def test_an_authored_tone_nothing_wears_raises(pristine):
    """The revert-by-omission shape: a decision in the data that no object renders."""
    vl.TONES["canopy"] = 0.4
    with pytest.raises(vl.LadderError, match="no material wears them"):
        vl.validate()


def test_a_material_pointing_at_a_missing_tone_raises(pristine):
    vl.MATERIAL_TONE["bed_base"] = "plinth"
    with pytest.raises(vl.LadderError, match="does not exist"):
        vl.validate()


def test_the_shams_are_not_the_pillowcase():
    """The shipped defect, pinned: the euro shams wore the PILLOW material, so element 8's
    three-rank head ladder rendered as three heights of ONE value (sham0 199.6 vs
    pillowsoft0 200.6). Height without value is not a ladder. A sham belongs to the duvet
    SET — one fabric, as bedding is actually sold."""
    sham = next(n for n, obj, _v in vl.LADDER if obj == "bed__sham0")
    pillow = vl.MATERIAL_TONE["bed_pillow"]
    assert sham != pillow
    assert vl.TONES[sham] < vl.TONES[pillow]


def test_the_upholstery_is_the_deepest_cloth():
    """The bed base, the foot bench and the foot throw all wear it, and it is what puts a
    dark into the right two-thirds of the frame, which at HEAD had none above the floor."""
    assert vl.TONES["upholstery"] == min(vl.TONES.values())


def test_the_pillowcase_is_the_lightest_cloth_and_still_inside_the_band():
    assert vl.TONES["pillowcase"] == max(vl.TONES.values())
    assert max(vl.codes("bed_pillow")) <= vl.SRGB_BAND_HI


def test_base_bench_tub_chair_and_the_suite_token_share_one_tone():
    """D3-4 bundles the bench with the base, the spec's tub-chair decision says its
    upholstery matches them "EXACTLY", and styling's linen token is the same identity.

    NAME THE MATERIAL THE BUILDER ACTUALLY USES. The first cut of this test asserted about
    `m_mill_linen` and called that "the tub chair" — but `_build_tub_chair` builds
    `stool_uph`, which at the time still held its own private tuple. The test passed and the
    claim was false: armour that checks the wrong object is worse than no armour, because it
    reads as coverage. Caught by the pre-commit review, inside the change written to kill
    exactly this."""
    worn = ("bed_base", "bench_seat", "m_mill_linen", "stool_uph")
    assert {vl.MATERIAL_TONE[m] for m in worn} == {"upholstery"}
    src = _build_room_src()
    for mat in worn:
        assert f'_woven("{mat}"' in src or f'_woven("{mat}",' in src,             f"{mat} is in the tone table but no builder woves it"


def _build_room_src():
    import pathlib
    return pathlib.Path(__file__).with_name("build_room.py").read_text(encoding="utf-8")


def _build_room_code():
    """build_room.py with `#` comment bodies stripped. The retired literals are QUOTED in
    the comments that retired them — that is the record, not a regression — so a pin that
    forbids them has to look at code, or it forbids explaining itself."""
    out = []
    for line in _build_room_src().splitlines():
        h = line.find("#")
        # crude but sufficient here: a lone `#` inside a string literal would truncate the
        # line, and build_room has none on the lines these pins read.
        out.append(line if h < 0 else line[:h])
    return chr(10).join(out)


# --------------------------------------------------------------------------- the ladder

def test_ladder_rungs_are_all_real_tones():
    for name, _obj, _v in vl.LADDER:
        assert name in vl.TONES


def test_a_collapsed_rung_pair_raises(pristine):
    """Two rungs the eye cannot separate are one rung."""
    vl.LADDER = (("upholstery", "bed__throw", 100.0),
                 ("upholstery", "bench__seat", 104.0),
                 ("pillowcase", "bed__pillowsoft0", 198.0))
    with pytest.raises(vl.LadderError, match="under MIN_STEP"):
        vl.validate()


def test_a_short_span_raises(pristine):
    """83.6 codes is what the bed spanned at HEAD, and it read as one mass."""
    vl.LADDER = (("upholstery", "bed__throw", 150.0),
                 ("coverlet", "bed__coverlet", 165.0),
                 ("pillowcase", "bed__pillowsoft0", 180.0))
    with pytest.raises(vl.LadderError, match="under MIN_SPAN"):
        vl.validate()


def test_several_rungs_may_share_one_cloth():
    """The frame separates bed__base, bed__throw and bench__seat by 59 codes while all
    three wear the identical upholstery linen — they face different ways in different
    light. Ranking CLOTHS would have missed that; chasing it with three albedos would
    have been three lies about one fabric."""
    from collections import Counter
    shared = [c for c, n in Counter(n for n, _o, _v in vl.LADDER).items() if n > 1]
    assert shared, "the ladder no longer exercises the shared-cloth case"
    objs = [o for n, o, _v in vl.LADDER if n == shared[0]]
    assert len(set(objs)) == len(objs)


def test_the_foot_bench_renders_below_the_coverlet():
    """Foreground darker than what is behind it is the depth cue (Block's foreground
    layering). At HEAD it was inverted — the bench (178.2) shouted over the coverlet
    (164.8) it sits in front of."""
    tgt = {o: v for _n, o, v in vl.LADDER}
    assert tgt["bench__seat"] < tgt["bed__coverlet"]


def test_head_ladder_never_ranks_the_duvet_fold():
    """The fold is the duvet's own hem — same cloth, same tone. Ranking a piece against
    itself would pass forever and mean nothing."""
    assert "fold" not in {name for name, _o, _v in vl.LADDER}
    assert not any("fold" in obj for _n, obj, _v in vl.LADDER)


# --------------------------------------------------------------------------- check_render

def _on_target():
    return {obj: target for _n, obj, target in vl.LADDER}


def test_check_render_clean_when_every_rung_lands():
    assert vl.check_render(_on_target()) == []


def test_check_render_flags_a_rung_that_misses_its_target():
    m = _on_target()
    m["bed__throw"] += vl.TOLERANCE + 5
    out = vl.check_render(m)
    assert any("throw" in v and "target" in v for v in out)


def test_check_render_flags_a_missing_object():
    """The probe not seeing a piece is a finding, not a pass. An occluded or renamed
    object must never read as 'no violation'. (Example migrated bed__coverlet ->
    bed__pillowsoft0 at p2r52, when the coverlet's absence became DECLARED (D-107,
    the whole-bed winner has no spread layer) — the rule is unchanged and the
    declaration path has its own test.)"""
    m = _on_target()
    del m["bed__pillowsoft0"]
    out = vl.check_render(m)
    assert any("no measurement" in v for v in out)


def test_the_declared_coverlet_absence_notes_rather_than_fails():
    """p2r52: the whole-bed winner is duvet-over-fitted-mattress — no spread
    exists in the file (D-107). The rung reports the declaration; it does not
    fail the frame, and it does not go silent either."""
    m = _on_target()
    del m["bed__coverlet"]
    out = vl.check_render(m)
    assert any("ABSENT BY DECLARATION D-107" in v for v in out), out
    assert not any("bed__coverlet" in v and "no measurement" in v for v in out)


def test_check_render_catches_a_squeeze_that_per_rung_tolerance_alone_would_pass():
    """Each rung within +-TOLERANCE of its own target and yet two of them one code
    apart: the relational check is not implied by the per-rung check.

    RENAMED p2r42, and the rename is the finding. This test was called "catches an
    inversion" and its numbers never encoded one — 73+8=81 and 90-8=82 are still in
    the designed order. It passed because the old check sorted by TARGET and measured
    RENDERED gaps, so a squeeze and an inversion came out of one branch under one
    name. Splitting them (COLLAPSE vs ORDER) is what showed the test was measuring
    the other thing; the real inversion is now pinned separately below."""
    m = _on_target()
    ranked = sorted(vl.LADDER, key=lambda r: r[2])
    # the pair has to be on DIFFERENT tones — same-tone siblings are one cloth by
    # design and their gap is a NOTE, not a palette failure (see the next test)
    lo, hi = next((a, b) for a, b in zip(ranked, ranked[1:]) if a[0] != b[0])
    m[lo[1]] = lo[2] + vl.TOLERANCE
    m[hi[1]] = m[lo[1]] + 1.0          # squeezed, NOT crossed
    assert abs(m[hi[1]] - hi[2]) <= vl.TOLERANCE, "both rungs stay on target"
    out = vl.check_render(m)
    assert any(v.startswith("COLLAPSE:") for v in out), out
    assert not any(v.startswith("ORDER:") for v in out), "nothing crossed anything"


def test_two_objects_of_the_SAME_cloth_reading_alike_is_a_note_not_a_failure():
    """D3-4 signs the foot bench as the same cloth as the bed base, and the foot
    throw wears it too. Ten codes between two objects cut from one fabric is
    something no tone can deliver, so it prints as a composition finding."""
    m = _on_target()
    same = next((a, b) for a, b in zip(sorted(vl.LADDER, key=lambda r: r[2]),
                                       sorted(vl.LADDER, key=lambda r: r[2])[1:])
                if a[0] == b[0])
    m[same[1][1]] = m[same[0][1]] + 2.0
    out = vl.check_render(m)
    assert not any(v.startswith("COLLAPSE:") for v in out), out
    assert any("SAME cloth" in v for v in out), out


def test_the_narrowing_still_catches_the_defect_the_ladder_was_built_for():
    """THE TEST THAT MAKES THE NARROWING A CORRECTION AND NOT A LOOPHOLE. The
    founding defect (2026-07-23) was six pieces of the head inside 7.1 codes, and
    the one the owner rejected by eye at p2r41 was duvet 208.3 against pillow
    217.2. Both are CROSS-TONE, so both still fail."""
    head = {obj: 200.0 for _n, obj, _v in vl.LADDER}
    assert any(v.startswith("COLLAPSE:") for v in vl.check_render(head))
    r41 = _on_target()
    r41["bed__duvet"], r41["bed__pillowsoft0"] = 208.3, 217.2
    assert any(v.startswith("COLLAPSE:") for v in vl.check_render(r41))


def test_check_render_catches_a_real_inversion_with_every_gap_wide_open():
    """Two rungs SWAPPED, far enough apart that no collapse fires. Only the ORDER
    half can see this, which is why it is its own check."""
    m = _on_target()
    m["bed__base"], m["bed__coverlet"] = 142.0, 73.0
    out = vl.check_render(m)
    assert any(v.startswith("ORDER:") for v in out)
    assert not any(v.startswith("COLLAPSE:") for v in out)


def test_check_render_flags_a_collapsed_span():
    m = {obj: 170.0 for _n, obj, _v in vl.LADDER}
    out = vl.check_render(m)
    assert any(v.startswith("SPAN:") for v in out)


# --------------------------------------------------------------------------- the armour

def test_story_line_derives_every_number_from_the_data(pristine):
    """Prose-vs-build drift is the class that mutated out of revert-by-omission: an
    armour bit that HARDCODES what the build computes will keep saying it after the
    build stops doing it. Change the data, the sentence must change."""
    before = vl.story_line()
    vl.TONES["accent"] = 0.35
    vl.MATERIAL_TONE["bed_accent"] = "accent"
    after = vl.story_line()
    assert before != after
    assert str(len(vl.TONES)) in after


def test_story_line_names_every_cloth_exactly_once_deepest_first():
    """The first cut of this sentence said "5 cloths" and then listed 4, because it walked
    the LADDER (which repeats a cloth three times and omits the unranked sheet). A count
    that disagrees with its own list is the prose-vs-build drift class, committed inside
    the armour — which is exactly where the last two reviews found it."""
    line = vl.story_line()
    named = vl.cloths_by_tone()
    assert sorted(named) == sorted(vl.TONES)
    assert ", ".join(named) in line.replace(" -> ", ", ")
    assert f"{len(vl.TONES)} cloths" in line
    for cloth in vl.TONES:
        assert cloth in line


def test_cloths_by_tone_is_ordered_deepest_first():
    named = vl.cloths_by_tone()
    assert [vl.TONES[n] for n in named] == sorted(vl.TONES.values())


# --------------------------------------------------------------------------- the conversion

def test_linear_to_srgb_round_trips():
    for code in range(0, 256, 5):
        c = code / 255.0
        assert mp.linear_to_srgb(mp.srgb_to_linear(c)) == pytest.approx(c, abs=1e-9)


def test_linear_to_srgb_matches_the_band_edges():
    """The band is stated in texel codes; the conversion is what lets a LINEAR-authored
    colour be checked against it at all."""
    assert mp.linear_to_srgb(mp.srgb_to_linear(30 / 255)) * 255 == pytest.approx(30.0)
    assert mp.linear_to_srgb(mp.srgb_to_linear(240 / 255)) * 255 == pytest.approx(240.0)


# --------------------------------------------------------------------------- anti-repaint

def test_build_room_no_longer_types_its_own_textile_tuples():
    """The colours LEFT the builders. If a future edit re-types one beside a paragraph
    arguing for it, this goes red — which is the only way the last six elements' worth of
    revert-by-omission got caught at all."""
    src = _build_room_code()          # CODE, not comments: the retired tuples are quoted
    #                                   in the comments that retired them, and a pin that
    #                                   forbids them everywhere forbids explaining itself.
    for dead in ("(0.46, 0.43, 0.39, 1.0)", "(0.87, 0.85, 0.81, 1.0)",
                 "(0.80, 0.77, 0.71, 1.0)", "(0.90, 0.88, 0.84, 1.0)",
                 "(0.80, 0.77, 0.72, 1.0)",
                 "(0.40, 0.37, 0.33, 1.0)",   # the tub chair's fifth copy
                 "(0.24, 0.19, 0.14, 1.0)"):  # the stool's private leg tone
        assert dead not in src, f"build_room.py re-types the retired tuple {dead}"


def test_build_room_asks_the_ladder_for_every_bed_material():
    import pathlib
    src = pathlib.Path(__file__).with_name("build_room.py").read_text(encoding="utf-8")
    for mat in vl.MATERIAL_TONE:
        assert f'_vl.rgba("{mat}")' in src, f"build_room.py never asks for {mat}"


# --------------------------------------------------------------------------- frame scoping

def test_targets_are_only_scored_on_the_frame_they_were_solved_on():
    """The per-rung numbers were inverted from measurements of ONE camera's light — the
    same cloth renders 59 codes apart on that camera alone. Scoring them elsewhere would
    report defects that are not defects, and an instrument that cries wolf gets muted."""
    off = {obj: target for _n, obj, target in vl.LADDER}
    off["bed__coverlet"] += 40          # would fail the target check on FRAME
    off["bed__sham0"] += 40             # keep the ORDER intact while doing it
    on_frame = vl.check_render(off, frame=vl.FRAME)
    elsewhere = vl.check_render(off, frame="ensuite_mirror")
    # "tolerance", not "target": the off-frame NOTE itself says "targets NOT scored", and
    # matching the looser word would have made this test pass for the wrong reason.
    assert any("tolerance" in v for v in on_frame)
    assert not any("tolerance" in v for v in elsewhere)
    assert any(v.startswith("NOTE:") for v in elsewhere)


def test_order_and_span_are_enforced_on_every_frame():
    """'The bed must not read as one mass' is a claim about every view that shows it."""
    flat = {obj: 170.0 for _n, obj, _v in vl.LADDER}
    out = vl.check_render(flat, frame="wardrobe_bay_entry")
    assert any(v.startswith("COLLAPSE:") for v in out)
    assert any(v.startswith("SPAN:") for v in out)


def test_a_piece_out_of_shot_is_a_finding_on_frame_and_a_note_elsewhere():
    m = {obj: target for _n, obj, target in vl.LADDER}
    del m["bench__seat"]
    assert any("no measurement" in v for v in vl.check_render(m, frame=vl.FRAME))
    off = vl.check_render(m, frame="west_vanity")
    assert not any("no measurement" in v for v in off)
    assert any("not visible" in v for v in off)


def test_band_check_follows_the_hue_and_does_not_assume_red_is_brightest(pristine):
    """A re-hue that is not warm-descending (a cool greige, b > g) must still be checked on
    its own brightest and darkest channels. Assuming red/blue would ship a tone outside the
    band with validate() green."""
    vl.HUE = (0.80, 0.90, 1.00)          # deliberately cool: blue is the ceiling now
    vl.TONES["pillowcase"] = 0.86        # 0.86 * 1.00 -> sRGB 239 is fine...
    assert vl.validate() is True
    vl.TONES["pillowcase"] = 0.90        # ...but 0.90 * 1.00 -> 243.5 is not
    try:
        with pytest.raises(vl.LadderError, match="over the studio dielectric ceiling"):
            vl.validate()
    finally:
        vl.HUE = (1.0, 0.43 / 0.46, 0.39 / 0.46)


# --------------------------------------------------------------------------- frame vocabulary

def test_known_frames_match_the_canonical_spec_cameras():
    """KNOWN_FRAMES is a second copy of a list that lives in the spec, so it gets a
    canonical-FILE test rather than a promise. A camera added to the spec and not here
    would RAISE at probe time on a frame that legitimately exists."""
    import json, os
    spec = json.load(open(os.path.join(os.path.dirname(__file__),
        "../../projects/PRJ-2026-002_c001-house/03_layout/master-suite.CANONICAL.spec.json"),
        encoding="utf-8"))
    variants = {k for k in (spec.get("eye_camera_variants") or {}) if not k.startswith("_")}
    assert vl.KNOWN_FRAMES == frozenset(variants | {vl.FRAME}), (
        sorted(vl.KNOWN_FRAMES ^ frozenset(variants | {vl.FRAME})))


def test_an_unknown_frame_raises_instead_of_silently_disabling_the_targets():
    """A typo would otherwise switch all seven per-rung checks OFF and still print CLEAN —
    the flattering-instrument shape, and why build_room hard-exits on a bad --eyecam."""
    m = {obj: target for _n, obj, target in vl.LADDER}
    with pytest.raises(vl.LadderError, match="unknown frame"):
        vl.check_render(m, frame="byd_hero")
    assert vl.check_render(m, frame=vl.FRAME) == []


# --------------------------------------------------------------------------- head binding

def test_head_cloth_maps_every_pillow_bank_stem_the_build_emits():
    """The stems come from styling.pillow_bank; a piece it emits with no cloth here would
    have inherited one silently, which is how the shams ended up wearing the pillowcase."""
    import styling
    parts = styling.pillow_bank(
        {"x": 0.0, "y": 0.0, "z": 0.6, "dx": 2.0, "dy": 2.15, "dz": 0.045}, "x", 1)
    stems = {p["name"].split("__")[1].rstrip("01")
             for p in parts if p["name"].startswith("bed__")}
    assert stems == set(vl.HEAD_CLOTH), (stems, set(vl.HEAD_CLOTH))


def test_head_cloth_puts_the_shams_under_the_pillows():
    """Defect 1, pinned at the binding rather than at the tone table: reverting
    HEAD_CLOTH["sham"] to "bed_pillow" must go red HERE, because the tone table alone
    cannot see which object wears what."""
    sham = vl.MATERIAL_TONE[vl.HEAD_CLOTH["sham"]]
    pillow = vl.MATERIAL_TONE[vl.HEAD_CLOTH["pillowsoft"]]
    assert vl.TONES[sham] < vl.TONES[pillow]


def test_build_room_builds_the_head_mapping_from_the_data_not_a_literal():
    """The line this replaces WAS the defect, and it was a literal inside _build_bed that
    no test could reach."""
    src = _build_room_code()
    assert "_vl.HEAD_CLOTH" in src
    for dead in ('{"sham": pill_m, "pillowsoft": pill_m}',
                 '{"sham": duvt_m, "pillowsoft": pill_m}'):
        assert dead not in src, f"_build_bed re-types the head mapping: {dead}"


def test_the_duvet_fold_wears_the_duvet_not_the_pillowcase():
    """Round 3 (2026-07-28) rebuilt the duvet as SIMULATED cloth whose fold is part of
    its own lattice (softgoods.folded_sheet) — so the fold cannot wear a different
    material any more BY CONSTRUCTION, and this test's job shifts: pin that the sim
    mechanism is actually in place (the fold is a folded_sheet, the bake wears duvt_m)
    and that no box named duvet_fold quietly returns (the old two-box island read the
    owner called 'ก้อนอะไรซักอย่างอยู่บนผ้าปู')."""
    src = _build_room_code()
    assert 'emit("bed__duvet_fold"' not in src, \
        "the duvet fold box is back — the fold must stay cloth of bed__duvet itself"
    assert "def _duvet" in src, "bed__duvet is no longer a simulated sheet"
    # the whole builder closure, up to the search ladder that bakes it
    blk = src.split("def _duvet", 1)[1].split("search_bake", 1)[0]
    assert 'bake_sheet("bed__duvet"' in blk, blk[:200]
    assert "duvt_m" in blk, "the duvet bake stopped wearing duvt_m"
    assert "pill_m" not in blk, "the duvet bake wears the pillowcase again"
    assert "folded_sheet" in blk, \
        "the duvet's feedstock lost its turned-back fold (folded_sheet)"


def test_two_cloths_at_the_same_value_raise(pristine):
    """"FIVE cloths" is a claim the armour ships. Two authored identically would be four
    cloths wearing five names, and every other check here would stay green."""
    vl.TONES["coverlet"] = vl.TONES["sheet"]
    with pytest.raises(vl.LadderError, match="authored at the same value"):
        vl.validate()


def test_an_object_ranked_twice_raises(pristine):
    """One measurement cannot honestly satisfy two rungs — and a duplicate also inflates
    the piece count story_line() reports to the polish pass."""
    vl.LADDER = vl.LADDER + (("pillowcase", "bed__pillowsoft0", 260.0),)
    with pytest.raises(vl.LadderError, match="more than once in the ladder"):
        vl.validate()


def test_a_rung_naming_an_object_nothing_builds_raises(pristine):
    """The ladder is the design and the build is the render. A rung on a piece that no
    longer exists goes quietly unmeasured — check_render only says so if somebody runs a
    probe, and the whole point of validate() is to catch it before anyone has to."""
    vl.LADDER = vl.LADDER[:-1] + (("pillowcase", "bed__bolster", 197.0),)
    with pytest.raises(vl.LadderError, match="nothing in the build emits"):
        vl.validate()


def test_built_objects_are_the_names_build_room_actually_emits():
    """BUILT_OBJECTS is a second copy of names that live in build_room, so it gets a
    source pin rather than a promise."""
    src = _build_room_code()
    for obj in vl.BUILT_OBJECTS:
        assert f'"{obj}"' in src, f"{obj} is in BUILT_OBJECTS but build_room never names it"


def test_every_ladder_object_is_emitted_by_the_build_or_the_head_bank():
    """The shipped ladder, checked the same way validate() checks a mutated one."""
    import styling
    parts = styling.pillow_bank(
        {"x": 0.0, "y": 0.0, "z": 0.6, "dx": 2.0, "dy": 2.15, "dz": 0.045}, "x", 1)
    names = {p["name"] for p in parts} | set(vl.BUILT_OBJECTS)
    for _c, obj, _t in vl.LADDER:
        assert obj in names, f"ladder ranks {obj}, which nothing emits"


def test_story_line_does_not_claim_the_swatch_order_is_the_frames_order():
    """duvet_set is a DEEPER swatch than coverlet and renders 18-36 codes ABOVE it. A
    prompt that called the swatch order 'the frame's order' would instruct the polish pass
    to invert the two biggest cloths in the picture."""
    line = vl.story_line()
    assert "AS SWATCHES" in line
    assert "frame's own order differs" in line


def test_off_frame_order_is_a_collapse_alarm_not_the_styling_gate():
    """Cross-camera light moves pieces ~10 codes in opposite directions (measured:
    coverlet +9.7, sham +5.8 between the two verified cameras), so the full MIN_STEP off
    the solved frame forces ~1-code tone margins that flake on any edit — and a check
    that is red for unactionable reasons gets muted. Off-frame, an 8-code squeeze passes;
    a genuine collapse (the original defect measured 0.2-7.1 codes) still fails."""
    # match the "ORDER:" violation PREFIX — the off-frame NOTE line also contains the
    # word ORDER ("ORDER and SPAN still are"), and matching it made this test fail its
    # own first assertion for the wrong reason.
    def order_fired(viol):
        return any(v.startswith("COLLAPSE:") for v in viol)
    m = {obj: target for _n, obj, target in vl.LADDER}
    squeeze = dict(m)
    squeeze["bed__sham0"] = squeeze["bed__coverlet"] + 8.0
    assert not order_fired(vl.check_render(squeeze, frame="bed_hero"))
    assert order_fired(vl.check_render(squeeze, frame=vl.FRAME))
    collapse = dict(m)
    collapse["bed__sham0"] = collapse["bed__coverlet"] + 4.0
    assert order_fired(vl.check_render(collapse, frame="bed_hero"))


# ------------------------------------------------------------ ACQUIRED_AS (p2r42)
# What these pin: p2r38 bought the bench and the head cushions, `place_model` named
# them `<tag>__acq<N>`, and three of the ladder's seven rungs read "no measurement"
# on every build from p2r38 to p2r41 while the cloths were still correctly on their
# tones. The build printed it and shipped anyway. The owner found it by eye.

def _wears_after_the_p2r38_acquisitions():
    return {
        "bed__base": ["bed_base"],
        "bed__throw": ["bed_throw"],
        "bed__coverlet": ["bed_coverlet"],
        "bed__duvet": ["bed_duvet"],
        "bench__acq0": ["acq_bench_seat"],          # retinted in place, renamed to the rung
        "bed__headset0__acq0": ["bed_duvet"],       # the standing sham
        "bed__headset0__acq1": ["bed_pillow"],      # the lying pillowcase
        "bed__headset1__acq0": ["bed_duvet"],
        "bed__headset1__acq1": ["bed_pillow"],
    }


def _measured_after_the_p2r38_acquisitions():
    return {"bed__base": 65.7, "bed__throw": 93.2, "bench__acq0": 110.0,
            "bed__coverlet": 142.0, "bed__headset0__acq0": 164.1,
            "bed__duvet": 177.1, "bed__headset0__acq1": 192.0,
            "bed__headset1__acq0": 163.0, "bed__headset1__acq1": 191.0}


def test_a_rung_renamed_by_an_acquisition_is_scored_not_reported_missing():
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    out = vl.check_render(m, wears=w)
    assert not any("has no measurement" in v for v in out), out
    assert any("scored on bench__acq0" in v for v in out)
    assert any("scored on bed__headset0__acq0" in v for v in out)


def test_without_the_wears_block_the_rung_says_so_and_never_guesses():
    """A sidecar written before p2r42 carries no `wears`. The rung must report that
    it cannot tell a rename from a deletion, not pick a plausible mesh."""
    out = vl.check_render(_measured_after_the_p2r38_acquisitions(), wears=None)
    assert any("no `wears` block" in v for v in out)
    assert not any("scored on" in v for v in out)


def test_an_acquired_rung_is_reported_against_its_point_target_and_not_failed_on_it():
    """154 was solved on a BUILT 0.80x0.44 standing king sham. A bought cushion is a
    different shape under the same light, so the point target is REPORTED (it is
    still information) and not enforced."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    m["bed__headset0__acq0"] = 250.0                 # wildly off the 154 target
    hard = [v for v in vl.check_render(m, wears=w) if not v.startswith("NOTE:")]
    assert not any("target 154.0" in v for v in hard), hard


def test_an_acquired_rung_is_still_failed_when_it_collapses_into_its_neighbour():
    """The point target does not survive a swap; 'two pieces read as one cloth' does."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    m["bed__headset0__acq0"] = m["bed__coverlet"] + 2.0
    assert any(v.startswith("COLLAPSE:") for v in vl.check_render(m, wears=w))


def test_an_ambiguous_acquisition_fails_rather_than_picking_one():
    """Two meshes under the same tag on the same cloth cannot both be one rung."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    w["bed__headset0__acq1"] = ["bed_duvet"]         # now BOTH wear the sham cloth
    m["bed__headset0__acq1"] = 165.0
    out = vl.check_render(m, wears=w)
    assert any("ambiguous" in v for v in out), out


def test_an_undeclared_rung_cannot_be_resolved_through_an_acquisition():
    """A rung with no ACQUIRED_AS row must not be silently taken by a renamed
    mesh — the pairing is a design fact and has to be written down. (This test
    used bed__duvet until p2r44 and bed__base until p2r52; each migrated the
    hour its rung became a real acquisition, which is itself the rule working.
    `bed__throw` carries it now — absent by D-083, and if an acquisition ever
    ships a runner it must be DECLARED here before it can resolve; asked via
    resolve_acquired directly because check_render would land on the D-083
    declaration after the failed lookup, by design.)"""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    m.pop("bed__throw", None)
    w["bed__throw__acq0"] = ["bed_base"]
    m["bed__throw__acq0"] = 91.0
    got, why = vl.resolve_acquired("bed__throw", m, w)
    assert got is None and "not declared as an acquirable rung" in why


def test_the_whole_bed_frame_takes_the_base_rung():
    """p2r52 (D-106/D-107): the hand-built bed leaves the scene with the frame
    hook, and the acquired platform — named bed__frame__acq0, dressed in the
    base linen — takes the upholstery rung. The mattress beside it wears
    bed_mattress and must NOT be swept into the same rung."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    del m["bed__base"]
    w["bed__frame__acq0"] = ["bed_base"]
    m["bed__frame__acq0"] = 75.0
    w["bed__frame__acq1"] = ["bed_mattress"]
    m["bed__frame__acq1"] = 230.0
    assert vl.resolve_acquired("bed__base", m, w)[0] == "bed__frame__acq0"


def test_the_bought_bed_cloth_resolves_to_its_two_rungs():
    """p2r44: his order put the cloth on the acquire path, and the ladder went
    silent on three of seven rungs the same round. The FIELD parts wear the
    coverlet cloth and the parts lying on them wear the duvet cloth — the split
    the part cut already made, read back rather than guessed a second time."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    for k in ("bed__coverlet", "bed__duvet"):
        m.pop(k, None)
    w["bed__cloth__acq0"] = ["bed_coverlet"]
    m["bed__cloth__acq0"] = 150.0
    w["bed__cloth__acq1"] = ["bed_duvet"]
    m["bed__cloth__acq1"] = 168.0
    assert vl.resolve_acquired("bed__coverlet", m, w)[0] == "bed__cloth__acq0"
    assert vl.resolve_acquired("bed__duvet", m, w)[0] == "bed__cloth__acq1"


def test_an_absence_that_was_decided_is_not_an_absence_that_was_missed():
    """"I could not measure it" and "it is not there and we said so" are
    different sentences. bed__throw is gone by decision D-083 (the acquired set
    falls to the bed line itself, 0 mm left to hang a runner in), so the rung
    reports the declaration and the build does not fail on it."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    m.pop("bed__throw", None)
    out = vl.check_render(m, wears=w)
    assert any("ABSENT BY DECLARATION D-083" in v for v in out), out
    assert not any("bed__throw" in v and "has no measurement" in v for v in out)


def test_a_declared_absence_still_has_to_name_a_decision_row():
    for obj, (dec, why) in vl.DECLARED_ABSENT.items():
        assert dec.startswith("D-"), obj
        assert len(why) > 40, obj


def test_a_retinted_material_matches_its_rung_through_the_acq_prefix():
    """A retint keeps the uploader's material OBJECT, so build_room renames it to
    `acq_<rung>` and Blender may suffix a duplicate. Both must resolve."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    w["bench__acq0"] = ["acq_bench_seat.001"]
    assert vl.resolve_acquired("bench__seat", m, w)[0] == "bench__acq0"


def test_the_acquired_bench_does_not_have_to_hold_the_built_benchs_place_in_the_order():
    """The p2r42 case in one line: the bought ottoman renders BELOW the throw because
    the built bench it replaces sat in different light. That is not an inversion of
    anything we can still see, and it must not block a frame."""
    m, w = _measured_after_the_p2r38_acquisitions(), _wears_after_the_p2r38_acquisitions()
    m["bench__acq0"] = 81.8                          # under the throw's 93.2
    assert not any(v.startswith("ORDER:") for v in vl.check_render(m, wears=w))
