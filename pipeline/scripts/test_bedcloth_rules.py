"""Tests for bedcloth_rules.py — the decisions a bed cover has to pass.

Both rules here have already decided a purchase wrongly, so each one gets a test
that FAILS on the version that shipped, not only one that passes on the fix. The
numbers are the master-suite bed's own (mattress 1820 x 1969, top 600, base top
204, so fall 396) — a rule that cannot be checked against the bed it was written
for is prose.
"""
import pytest

import bedcloth_rules as BR

# the master-suite bed, in metres
RECT = (0.0, 0.0, 1.820, 1.969)
TOP_Z, BASE_Z = 0.600, 0.204
LIMIT, COVER = BR.limits_for(RECT, TOP_Z, BASE_Z)
# the slot rule this round retired: min(bed outer line, mattress + 40 mm)
RETIRED_SLOT = (min(1.800, 1.820 + 0.04), min(1.949, 1.969 + 0.04), 0.396 + 0.32)


def test_limits_derive_from_the_bed_and_the_ceiling_clears_the_mattress():
    assert COVER == (1.820, 1.969)
    assert LIMIT[0] == pytest.approx(1.820 + 2 * 0.396)
    assert LIMIT[1] == pytest.approx(1.969 + 2 * 0.396)
    assert LIMIT[2] == pytest.approx(0.396 + 0.32)
    assert LIMIT[0] > COVER[0] and LIMIT[1] > COVER[1], (
        "a ceiling below the floor is the defect this round found")


def test_the_retired_slot_was_smaller_than_the_mattress_it_had_to_cover():
    """THE p2r41 FINDING, pinned so it cannot come back. The old rule's plan slot
    measures 1800 x 1949 against a mattress of 1820 x 1969 — it shrank every
    candidate below the thing it was bought to cover."""
    assert RETIRED_SLOT[0] < COVER[0]
    assert RETIRED_SLOT[1] < COVER[1]


def test_a_real_duvet_keeps_its_drape_under_the_new_rule_and_lost_it_under_the_old():
    """8635b5b9 as authored: 2184 x 2331 x 626 mm — 180 mm of cloth past each
    flank of an 1820 mm mattress, which is what makes cloth read as cloth."""
    native = (2.184, 2.331, 0.626)
    s_new, rot, _, _, _, need = BR.plan_scale(native, LIMIT, COVER)
    assert rot == 0.0
    assert s_new == pytest.approx(1.0), "authored size is the target, not a ceiling"
    assert need == pytest.approx(0.845, abs=0.002)
    assert need <= s_new, "it covers the mattress without being stretched"
    # the same asset under the retired rule, which is a TARGET
    s_old = min(RETIRED_SLOT[0] / native[0], RETIRED_SLOT[1] / native[1],
                RETIRED_SLOT[2] / native[2])
    assert s_old == pytest.approx(0.824, abs=0.002)
    overhang_new = (native[0] * s_new - COVER[0]) / 2 * 1000
    overhang_old = (native[0] * s_old - COVER[0]) / 2 * 1000
    assert overhang_new > 170, "the cover hangs past the mattress"
    assert overhang_old < 5, "the retired rule pulled the hem back onto the mattress"


def test_a_set_too_small_to_cover_is_rejected_rather_than_stretched():
    """ub806591a, the asset p2r31 actually bought: 1505 x 1600 mm."""
    s, _, _, _, _, need = BR.plan_scale((1.505, 1.600, 0.30), LIMIT, COVER)
    assert need > s, "it must be refused, not scaled up past max_scale"
    assert need == pytest.approx(1.231, abs=0.002)


def test_a_whole_room_scene_is_rejected_because_covering_it_would_shrink_the_cover():
    """The cache holds bedroom SCENES (bd_a: 8129 x 13719 mm). The ceiling forces
    them so small that they can no longer cover the mattress, which is the honest
    refusal: nothing here is a bed cover."""
    s, _, _, _, _, need = BR.plan_scale((8.129, 13.719, 2.5), LIMIT, COVER)
    assert need > s


def test_max_scale_is_a_ceiling_even_when_the_room_allows_more():
    s, _, _, _, _, _ = BR.plan_scale((1.0, 1.0, 0.1), LIMIT, COVER, max_scale=1.0)
    assert s == 1.0, "an asset is never stretched, however much room there is"


def test_rotation_is_derived_from_both_boxes_and_reorients_the_cover_test():
    native = (2.331, 2.184, 0.626)          # the same set, authored the other way
    s, rot, _, _, _, need = BR.plan_scale(native, LIMIT, COVER)
    assert rot == 90.0
    assert need == pytest.approx(0.845, abs=0.002), (
        "turning the set must not change whether it covers the bed")


# ------------------------------------------------------------ part classification

def test_the_cover_is_chosen_from_the_parts_and_the_bed_in_the_file_does_not_decide():
    """p2r47, on 22897dd4's own measurements. The file is a whole bedding SET: a
    2018 x 1827 x 213 mm sheet of 74,136 triangles, a 2596 x 1681 x 660 mm spread,
    and a bed standing 1243 mm tall. Solved on the file's bounding box the height
    ceiling (fall 396 + loft 320 = 716 mm) collapses the allowed scale to 0.576x and
    the sheet's own 0.665x reads as 'too big'; solved on the sheet it is 1.0x."""
    parts = [("sheet", (2.018, 1.827, 0.213)),
             ("spread", (2.596, 1.681, 0.660)),
             ("bed", (2.738, 3.345, 1.243))]
    key, row, feasible = BR.choose_cover(parts, LIMIT, COVER, max_scale=1.0)
    assert key == "sheet", "the 74k-triangle sheet is the cover; the bed is not"
    assert row[0] == pytest.approx(1.0), "staged as authored, not shrunk by the bed"
    assert feasible == 1, "and it is the only part that can cover this mattress"
    # and the refused version, reconstructed: the file's own box
    s_file, _, _, _, _, need_file = BR.plan_scale((2.738, 3.345, 1.243), LIMIT, COVER)
    assert need_file > s_file, "this is the refusal the whole set used to get"


def test_the_outermost_cloth_wins_when_more_than_one_part_can_cover():
    parts = [("inner", (1.9, 2.0, 0.2)), ("outer", (2.2, 2.3, 0.3))]
    key, _row, feasible = BR.choose_cover(parts, LIMIT, COVER)
    assert key == "outer" and feasible == 2


def test_with_nothing_feasible_the_closest_part_is_still_chosen_and_still_measured():
    """d4698c95 needs 1.046x and 9dc70a0e needs 1.011x — 20 mm on one axis of a bed
    the client's drawing makes 2149 mm wide. Both used to be refused sight unseen;
    both are now staged as authored so the rays can answer."""
    parts = [("cover", (1.740, 1.978, 0.324)), ("pillow", (0.6, 0.5, 0.2))]
    key, row, feasible = BR.choose_cover(parts, LIMIT, COVER)
    assert feasible == 0
    assert key == "cover", "the closest part is the file's cover"
    assert row[5] == pytest.approx(1.046, abs=0.002)
    assert row[0] == pytest.approx(1.0), "still staged AS AUTHORED, never stretched"


def test_a_sets_own_pillow_landing_inside_the_acquired_one_is_a_duplicate():
    """p2r47's audition shot: d4698c95 ships its own pillows, this bed's head set was
    acquired eleven rounds ago, and an 800 mm bolster rendered standing THROUGH it.
    Geometric, never by name (R9b) — the uploader's names are the one thing this repo
    has already been burned by trusting."""
    ours = (0.0, 0.0, 0.60, 0.60, 0.45, 1.05)          # an acquired sham at the head
    theirs = (0.05, 0.05, 0.62, 0.55, 0.40, 1.00)      # the set's own, on top of it
    share, dup = BR.duplicate_of_placed(theirs, [ours])
    assert dup and share > 0.9


def test_a_duvet_merely_touching_a_pillow_is_not_a_duplicate():
    """R9b calls AABB interpenetration ADVISORY because a box cannot tell interlocking
    from intersecting, so the threshold is a THIRD of the part's own volume. A cover
    tucked against a sham overlaps it a little and must survive."""
    ours = (0.0, 0.0, 0.60, 0.60, 0.45, 1.05)
    duvet = (0.0, 0.0, 0.20, 1.82, 1.97, 0.65)
    share, dup = BR.duplicate_of_placed(duvet, [ours])
    assert not dup and share < BR.DUPLICATE_SHARE


def test_nothing_placed_means_nothing_is_a_duplicate():
    assert BR.duplicate_of_placed((0, 0, 0, 1, 1, 1), []) == (0.0, False)
    assert BR.duplicate_of_placed(None, [(0, 0, 0, 1, 1, 1)]) == (0.0, False)


def test_choose_cover_with_no_parts_says_so_rather_than_guessing():
    assert BR.choose_cover([], LIMIT, COVER) == (None, None, 0)


def test_an_accessory_cloth_is_kept_and_not_counted_as_the_cover():
    """p2r32's correction, pinned: the turned-down runner (374 x 1600 mm = 16.7% of
    this mattress in plan) is EXTRA, not junk. The pre-p2r32 cut deleted it, and the
    audition tools kept that cut until p2r41."""
    mat = 1.820 * 1.969
    field, extra, drop = BR.classify_areas(
        [("cover", 2.184 * 2.331, 4000),
         ("runner", 0.374 * 1.600, 800),
         ("label", 0.02 * 0.02, 400),
         ("junk_block", 4.0, 12)], mat)
    assert field == ["cover"]
    assert extra == ["runner"]
    assert sorted(drop) == ["junk_block", "label"]


def test_the_poly_floor_alone_removes_the_uploaders_junk():
    mat = 1.0
    _, _, drop = BR.classify_areas([("slab", 5.0, 12)], mat)
    assert drop == ["slab"], "a 12-poly 5 m block is junk however big its plan is"


# ------------------------------------------------------------------ the three cuts

def test_survives_is_decided_by_the_two_RAY_cuts_and_names_which_one_failed():
    assert BR.survives(0.845, 1.0, 0.902, 2)["survives"]
    assert not BR.survives(0.845, 1.0, 0.71, 2)["survives"]     # our mattress shows
    assert not BR.survives(0.845, 1.0, 0.90, 0)["survives"]     # does not drape


def test_size_is_reported_and_no_longer_decides_because_it_is_a_bounding_box():
    """p2r47. `need_scale` used to refuse a set outright; it refused five candidates
    at 1.011x-1.125x, none of which was ever rayed. It is still MEASURED and still
    printed — a set needing 1.231x is a fact worth reading — but the verdict belongs
    to the two cuts that can see the object."""
    stretched = BR.survives(1.231, 1.0, 0.90, 2)
    assert stretched["size_ok"] is False, "the number is still measured and reported"
    assert stretched["survives"], "and the rays, not the box, decide"


def test_a_cover_too_small_still_dies_by_ray_so_nothing_was_loosened():
    """The clause that replaces the box: a set that cannot reach the mattress fails
    coverage, and one that cannot reach past its flanks fails drape. Demoting the box
    removed an early-out, not a standard."""
    assert not BR.survives(1.9, 1.0, 0.42, 0)["survives"]
    assert not BR.survives(1.9, 1.0, 0.95, 1)["survives"]


def test_the_build_applied_two_of_the_three_cuts_and_p2r44_walked_through_the_gap():
    """THE p2r45 FINDING, pinned. `_place_bed_cloth` tested model_fit and
    `coverage < 0.80` inline and printed `fall_sides` next to nothing at all, so a
    set draping ONE flank passed the build while the audition that chose it applies
    a cut of two. These are p2r44's own built numbers."""
    shipped = BR.survives(0.855, 0.911, 0.812, 1)
    assert shipped["covered"], "coverage cleared the cut it was tested against"
    assert not shipped["drapes"], "and the clause the build never called refuses it"
    assert not shipped["survives"]
    # the retired build-side test, reconstructed: coverage alone lets it through
    assert 0.812 >= BR.COVER_CUT


# --------------------------------------------------------------- mesh fineness

def test_a_cover_coarser_than_the_pillows_beside_it_is_refused():
    """p2r44's frame, measured in world mm on the built scene: the acquired cover
    is 43.2 mm and the acquired pillows in the same bed are 4.5 and 10.3. No
    threshold is typed — the coarsest accepted cloth in the frame IS the cut."""
    fine = BR.fineness(43.2, {"bed__headset0__acq0": 10.3,
                              "bed__headset0__acq1": 4.5})
    assert fine["ran"]
    assert fine["control"] == "bed__headset0__acq0", "the COARSEST control binds"
    assert fine["control_mm"] == 10.3
    assert fine["ratio"] == pytest.approx(4.194, abs=0.01)
    assert fine["fine_enough"] is False


def test_the_pillows_themselves_pass_the_rule_that_refuses_the_cover():
    """A rule that also condemned the meshes no critic has ever filed would be
    measuring something other than what it names."""
    assert BR.fineness(10.3, {"a": 10.3})["fine_enough"] is True
    assert BR.fineness(4.5, {"a": 10.3})["fine_enough"] is True


def test_no_control_is_the_third_state_and_never_a_pass():
    """R11's exit-code contract, one level down: could-not-look must not print like
    looked-and-it-was-fine."""
    for row in (BR.fineness(43.2, {}), BR.fineness(43.2, None),
                BR.fineness(43.2, {"a": 0.0}), BR.fineness(None, {"a": 10.3})):
        assert row["ran"] is False
        assert row["fine_enough"] is None, "not True, and not False either"


def test_built_survives_blocks_on_each_clause_by_name():
    ok = BR.built_survives(0.902, 2, 9.0, {"pillow": 10.3}, share=0.91)
    assert ok["survives"] and ok["blocked_by"] == []
    drape = BR.built_survives(0.812, 1, 9.0, {"pillow": 10.3}, share=0.91)
    assert drape["blocked_by"] == ["drape"]
    half = BR.built_survives(0.940, 4, 9.0, {"pillow": 10.3}, share=0.45)
    assert half["blocked_by"] == ["made"], (
        "p2r47's frame: 94% coverage, 4/4 flanks, and a bed a blind critic read as "
        "half made — the whole point of D-095 is that the first two cannot see it")
    blind = BR.built_survives(0.902, 2, 9.0, {"pillow": 10.3}, share=None)
    assert blind["blocked_by"] == ["made"], (
        "a cut that could not run still blocks — it does not pass by default")
    both = BR.built_survives(0.812, 1, 9.0, {"pillow": 10.3}, share=0.45)
    assert both["blocked_by"] == ["drape", "made"]


def test_fineness_is_measured_and_reported_and_no_longer_blocks():
    """p2r49 (D-096, plan row P2r-17). D-094 measured the cut's own control — the
    acquired pillows at 4.5 and 10.3 mm — drawing the SAME critic complaint as the
    cover it judges, so it cannot separate the two things it is asked to decide
    between. It keeps measuring; it stops deciding."""
    coarse = BR.built_survives(0.902, 2, 43.2, {"pillow": 10.3}, share=0.91)
    assert coarse["fine_enough"] is False, "still measured, still reported"
    assert coarse["fineness"]["ratio"] > 4.0
    assert "fineness" not in coarse["blocked_by"]
    assert coarse["survives"] is True, "a coarse mesh that MAKES the bed now ships"
    cannot = BR.built_survives(0.902, 2, 43.2, {}, share=0.91)
    assert cannot["fineness"]["ran"] is False
    assert cannot["survives"] is True, (
        "and a fineness that COULD NOT RUN no longer sinks a frame either — the "
        "clause that replaced it is the one that has to be answerable")


def test_made_bed_is_the_third_clause_and_needs_an_outside_cut():
    """The cut is passed IN, never stored in the rule, so the file that records where
    the number was read off is the file that carries it."""
    assert BR.made_bed(0.95, None)["ran"] is False
    assert BR.made_bed(None, 0.80)["ran"] is False
    assert BR.made_bed(0.95, 0.80)["made"] is True
    row = BR.made_bed(0.45, 0.80)
    assert row["made"] is False and abs(row["shortfall"] - 0.35) < 1e-9


def test_duvet_share_counts_bare_plan_in_the_denominator():
    """A bare patch of mattress is not made, it is bare — so points with NO cloth
    over them must count against the share, not be dropped from it."""
    hs = [120.0, 120.0, 120.0]          # three lofted points
    assert abs(BR.duvet_share(hs, 3) - 1.0) < 1e-9
    assert abs(BR.duvet_share(hs, 6) - 0.5) < 1e-9, "three of six plan points bare"


def test_loft_curve_publishes_the_threshold_s_own_sensitivity():
    """p2r47's set, from `lies_on_the_bed`'s own measurements: the sheet tops out at
    7.5 mm and the duvet at 146.4. Every line between 20 and 140 returns the same
    answer, which is the fact that makes 30 mm not a knob."""
    hs = [7.5] * 55 + [146.4] * 45
    curve = BR.loft_shares(hs, 100)
    assert curve[10.0] == 0.45 and curve[120.0] == 0.45, "insensitive across the band"
    assert curve[5.0] == 1.00, "below the sheet's own height everything counts"


def test_fineness_is_a_comparison_so_it_re_aims_itself():
    """No number in the rule means nothing to tune: the same 20 mm cover passes
    beside a 25 mm control and fails beside a 10 mm one."""
    assert BR.fineness(20.0, {"a": 25.0})["fine_enough"] is True
    assert BR.fineness(20.0, {"a": 10.0})["fine_enough"] is False


def test_coverage_alone_would_have_ranked_the_failure_first():
    """p2r31 ranked on coverage. A cloth too small to reach past the mattress covers
    its plan most efficiently, so the ranking actively preferred the failure. This
    pins the shape of that mistake: high coverage, no drape, still refused."""
    flat_but_covering = BR.survives(0.019, 0.024, 1.00, 0)
    real_cloth = BR.survives(0.845, 1.0, 0.902, 2)
    assert flat_but_covering["covered"] and not flat_but_covering["survives"]
    assert real_cloth["survives"]
