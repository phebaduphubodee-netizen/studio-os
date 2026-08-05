"""Tests for rule_gate — the module that turns prose rules into failures.

A guard that cannot fail is decoration, and a guard that fires on correct work
gets muted. Both halves are tested here, because this repo has already lost a
debt instrument to the second failure mode.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule_gate as RG  # noqa: E402


def _spec(masses, **kw):
    return dict({"id": "TRN-002", "masses": masses}, **kw)


# --- R10: the object-existence half ----------------------------------------

def test_a_measured_mass_passes():
    v = RG.audit_spec(_spec([{"name": "wall", "prov": "M(corner arris u731.5)"}]))
    assert v == []


def test_a_mass_with_no_provenance_at_all_fails():
    v = RG.audit_spec(_spec([{"name": "mystery", "prov": ""}]))
    assert len(v) == 1 and "no `prov`" in v[0]


def test_a_bare_A_fails():
    v = RG.audit_spec(_spec([{"name": "closet_back", "prov": "A"}]))
    assert len(v) == 1 and "bare letter" in v[0]


def test_a_wholly_assumed_object_fails():
    v = RG.audit_spec(_spec([{"name": "petcave", "prov": "A(identity open)"}]))
    assert len(v) == 1 and "NOTHING about this object is measured" in v[0]


def test_a_declared_why_clears_it():
    v = RG.audit_spec(_spec([{"name": "petcave", "prov": "A(identity open)",
                              "why": "a real object in the reference corner; "
                                     "its class is the owner's call"}]))
    assert v == []


def test_a_measured_object_with_one_named_assumed_dimension_PASSES():
    """The separation this gate owes. 'M(top 937) / A(bottom 485 occluded)' is
    R10 already working: the assumption is named, bounded, and sits beside the
    number. Failing it would train the reader to mute the gate."""
    v = RG.audit_spec(_spec([{"name": "ward_band",
                              "prov": "M(top 937.1 on -1290) / A(bottom 485 occluded)"}]))
    assert v == []


def test_typing_a_number_the_measurement_called_unmeasurable_fails():
    v = RG.audit_spec(_spec([{"name": "desk_pier",
                              "prov": "M(face y=-3445) but depth unmeasurable, occluded"}]))
    assert any("UNMEASURABLE" in s for s in v)


def test_declaring_the_gap_clears_the_unmeasurable_check():
    v = RG.audit_spec(_spec([{"name": "desk_pier",
                              "prov": "M(face) depth unmeasurable"}],
                            declared_gaps={"desk_pier": "depth is a stated gap"}))
    assert v == []


# --- R10 question 2: point at it in the reference --------------------------

def test_require_seen_catches_an_object_with_a_perfect_derivation():
    """lamp_stem's provenance is a legitimate contact — 'rest_on nightstand top
    481, carries shade' — for an object that appears nowhere in the reference.
    Provenance alone cannot catch an invented object."""
    m = [{"name": "lamp_stem", "prov": "D(rest_on nightstand top 481, carries shade)"}]
    assert RG.audit_spec(_spec(m)) == []                      # prov looks fine
    v = RG.audit_spec(_spec(m), require_seen=True)
    assert len(v) == 1 and "point at it in the reference" in v[0]


def test_not_visible_with_a_reason_is_an_acceptable_answer():
    m = [{"name": "closet_back", "prov": "A(closet depth)",
          "why": "encloses the dressing area behind the glass",
          "seen": "NOT VISIBLE: behind the partition, only its glow reaches the frame"}]
    assert RG.audit_spec(_spec(m), require_seen=True) == []


# --- R7: every critic answer owes a triage ---------------------------------

def test_an_untriaged_critic_answer_fails(tmp_path):
    (tmp_path / "ANSWER_gemini25pro.md").write_text("findings", encoding="utf-8")
    (tmp_path / "README.md").write_text("# bundle\n", encoding="utf-8")
    v = RG.audit_bundle(str(tmp_path))
    assert len(v) == 1 and "no triage" in v[0]


def test_a_triage_file_clears_it(tmp_path):
    (tmp_path / "ANSWER_gemini25pro.md").write_text("findings", encoding="utf-8")
    (tmp_path / "TRIAGE_gemini25pro.md").write_text("accepted", encoding="utf-8")
    assert RG.audit_bundle(str(tmp_path)) == []


def test_a_triage_section_in_the_readme_clears_it(tmp_path):
    (tmp_path / "ANSWER_claude-cowork.md").write_text("findings", encoding="utf-8")
    (tmp_path / "README.md").write_text("## claude-cowork triage\n1. accepted",
                                        encoding="utf-8")
    assert RG.audit_bundle(str(tmp_path)) == []


def test_a_bundle_with_no_critic_answer_owes_nothing(tmp_path):
    (tmp_path / "README.md").write_text("# pending", encoding="utf-8")
    assert RG.audit_bundle(str(tmp_path)) == []


# --- the charter: the product is the learning ------------------------------

def test_a_lane_with_no_distillation_fails(tmp_path):
    v = RG.audit_learning(_spec([]), str(tmp_path))
    assert len(v) == 1 and "distillation" in v[0]


def test_the_lane_id_matches_a_directory_whose_name_is_punctuated_differently(tmp_path):
    """TRN-002 must find trn002-reference-study. The first version globbed the
    raw id and reported 'no distillation' for a file written ten minutes
    earlier; a gate that cries wolf gets muted."""
    d = tmp_path / "trn002-reference-study"
    d.mkdir()
    (d / "study.md").write_text("findings", encoding="utf-8")
    assert RG.audit_learning(_spec([]), str(tmp_path)) == []


def test_enforce_raises_when_hard():
    try:
        RG.enforce(_spec([{"name": "x", "prov": "A"}]), hard=True)
    except SystemExit:
        return
    raise AssertionError("enforce(hard=True) must refuse to continue")
