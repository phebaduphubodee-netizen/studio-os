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

def test_survives_requires_all_three_and_names_which_one_failed():
    assert BR.survives(0.845, 1.0, 0.902, 2)["survives"]
    assert not BR.survives(1.231, 1.0, 0.90, 2)["survives"]     # stretched
    assert not BR.survives(0.845, 1.0, 0.71, 2)["survives"]     # our mattress shows
    assert not BR.survives(0.845, 1.0, 0.90, 0)["survives"]     # does not drape


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
    ok = BR.built_survives(0.902, 2, 9.0, {"pillow": 10.3})
    assert ok["survives"] and ok["blocked_by"] == []
    drape = BR.built_survives(0.812, 1, 9.0, {"pillow": 10.3})
    assert drape["blocked_by"] == ["drape"]
    coarse = BR.built_survives(0.902, 2, 43.2, {"pillow": 10.3})
    assert coarse["blocked_by"] == ["fineness"]
    blind = BR.built_survives(0.902, 2, 43.2, {})
    assert blind["blocked_by"] == ["fineness"], (
        "a cut that could not run still blocks — it does not pass by default")
    shipped = BR.built_survives(0.812, 1, 43.2, {"pillow": 10.3})
    assert shipped["blocked_by"] == ["drape", "fineness"], (
        "p2r44's built frame, refused by both new clauses")


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
