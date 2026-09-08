"""Tests for coverage_check — the missing-object half of R10.

Both halves are tested, for the reason the sibling test file already states: a
guard that cannot fire is decoration, and a guard that fires on correct work gets
muted. The negative controls here are the ones that matter — this lane's three
real omissions (an opening, a blind, four chair legs) are reproduced as cases, so
the check is measured against the defects it claims to catch rather than against
made-up ones.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_check as CC  # noqa: E402


def _spec(names, gaps=None):
    return {"masses": [{"name": n} for n in names], "declared_gaps": gaps or {}}


def _man(entries, baseline=None):
    m = {"entries": entries}
    if baseline is not None:
        m["absent_baseline"] = baseline
    return m


# --- the three real omissions this lane paid for ---------------------------

def test_the_opening_that_hid_for_thirty_rounds_is_caught():
    spec = _spec(["back_wall", "jamb_L", "jamb_R", "head", "rail_B"])
    man = _man([{"id": "partition_opening", "what": "doorway through the partition"}])
    rows, v = CC.audit(spec, man)
    assert rows[0]["state"] == "UNCOVERED"
    assert len(v) == 1 and "partition_opening" in v[0]


def test_the_blind_with_everything_except_a_mass_is_caught():
    # generator, builder, palette row, three tests, its own area light — and no mass.
    spec = _spec(["window_frame", "sill", "blind_light"])
    rows, v = CC.audit(spec, _man([{"id": "blind", "what": "horizontal slat blind"}]))
    assert rows[0]["state"] == "UNCOVERED" and len(v) == 1


def test_chair_legs_vanishing_between_rounds_is_caught():
    present = _spec(["chair_seat", "chair_leg_1", "chair_leg_2"])
    gone = _spec(["chair_seat"])
    man = _man([{"id": "chair_leg", "what": "four dark chair legs", "prefix": True}])
    assert CC.audit(present, man)[1] == []
    assert len(CC.audit(gone, man)[1]) == 1


# --- the positive half: correct work must pass -----------------------------

def test_a_built_object_passes_by_exact_name():
    assert CC.audit(_spec(["bed"]), _man([{"id": "bed", "what": "bed"}]))[1] == []


def test_prefix_matching_is_opt_in_per_entry():
    spec = _spec(["wardrobe_door_1", "wardrobe_door_2"])
    man = _man([{"id": "wardrobe_door", "what": "doors", "prefix": True}])
    assert CC.audit(spec, man)[1] == []


def test_a_namesake_does_not_count_as_the_object():
    # `blind_light` is the area light named after the blind. Without opt-in prefix
    # matching it must NOT satisfy the entry for the blind itself.
    spec = _spec(["blind_light"])
    assert len(CC.audit(spec, _man([{"id": "blind", "what": "slat blind"}]))[1]) == 1


def test_built_as_lets_the_manifest_speak_the_reference_not_the_spec():
    # "the chair" in a photograph is five masses in a spec; the manifest must not
    # be forced into the build's vocabulary or it stops being a reading of the image.
    spec = _spec(["seat_pan", "back_rest", "leg_fl"])
    man = _man([{"id": "chair", "what": "chair at the desk",
                 "built_as": ["seat_pan", "back_rest", "leg_fl"]}])
    assert CC.audit(spec, man)[1] == []


def test_a_declared_gap_with_a_reason_passes():
    spec = _spec(["bed"], gaps={"garments": "free-form, R8 ACQUIRE lane"})
    man = _man([{"id": "garments", "what": "clothes on the rail"}],
               baseline=["garments"])
    rows, v = CC.audit(spec, man)
    assert v == [] and rows[0]["state"] == "ABSENT"


# --- the ways a check like this gets neutered ------------------------------

def test_an_empty_reason_does_not_count_as_a_declaration():
    spec = _spec(["bed"], gaps={"mirror": "   "})
    rows, v = CC.audit(spec, _man([{"id": "mirror", "what": "mirror"}]))
    assert rows[0]["state"] == "UNCOVERED" and "EMPTY reason" in rows[0]["detail"]


def test_a_new_absence_outside_the_baseline_is_a_violation():
    # Otherwise declared_gaps becomes the licence it was written to prevent.
    spec = _spec(["bed"], gaps={"rug": "removed, too slow to build"})
    man = _man([{"id": "rug", "what": "rug"}], baseline=["garments"])
    v = CC.audit(spec, man)[1]
    assert len(v) == 1 and "NEW ABSENCE" in v[0]


def test_built_as_that_names_nothing_is_not_a_pass():
    spec = _spec(["bed"])
    man = _man([{"id": "chair", "what": "chair", "built_as": ["seat_pan"]}])
    assert CC.audit(spec, man)[1][0].startswith("UNCOVERED")


def test_a_duplicated_manifest_id_is_reported():
    spec = _spec(["bed"])
    man = _man([{"id": "bed", "what": "bed"}, {"id": "bed", "what": "bed again"}])
    v = CC.audit(spec, man)[1]
    assert any("twice" in x for x in v)


def test_an_entry_with_no_id_is_reported():
    assert CC.audit(_spec(["bed"]), _man([{"what": "something"}]))[1] == \
        ["manifest entry with no `id`"]


def test_a_baseline_entry_that_got_built_is_flagged_for_removal():
    # The ratchet must also close: an allowed absence that is now built has to
    # leave the baseline, or the list slowly becomes permission rather than debt.
    spec = _spec(["mirror"], gaps={})
    man = _man([{"id": "mirror", "what": "mirror"}], baseline=["mirror"])
    rows, v = CC.audit(spec, man)
    assert v == []
    assert any(r["state"] == "RATCHET-CLOSED" for r in rows)


def test_a_list_shaped_declared_gaps_is_reported_and_satisfies_nothing():
    # r32's spec-maker did list(dict) on declared_gaps: the ten KEYS survived and
    # all ten reasons were dropped. The names still look like declarations.
    spec = {"masses": [{"name": "bed"}], "declared_gaps": ["mirror", "rug"]}
    man = _man([{"id": "mirror", "what": "mirror"}], baseline=["mirror"])
    rows, v = CC.audit(spec, man)
    assert any("LIST" in x for x in v)
    assert rows[0]["state"] == "UNCOVERED"


def test_a_dict_shaped_declared_gaps_reports_no_shape_problem():
    spec = _spec(["bed"], gaps={"mirror": "reason"})
    man = _man([{"id": "mirror", "what": "mirror"}], baseline=["mirror"])
    assert CC.audit(spec, man)[1] == []


def test_an_empty_manifest_reports_nothing_and_that_is_the_point():
    # Pure audit() is silent here BY DESIGN; the CLI's --require-manifest is what
    # refuses. The test pins the split so nobody "fixes" it in the wrong layer.
    assert CC.audit(_spec(["bed"]), _man([])) == ([], [])
