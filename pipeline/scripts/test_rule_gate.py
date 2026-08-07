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


def test_a_gap_declared_against_one_AXIS_covers_that_mass():
    """r27 declares `right_wall_x` — the wall is measured, its x is not. A
    checker that only knew mass-level keys blocked a spec for declaring its gap
    MORE precisely than the check could read."""
    prov = "M(corner arris u731.5) in y; x UNMEASURED as of r27"
    v = RG.audit_spec(_spec(
        [{"name": "right_wall", "prov": prov, "seen": "u730"}],
        declared_gaps={"right_wall_x": "no evidence in frame"}))
    assert v == []


def test_an_axis_gap_does_not_cover_a_DIFFERENT_mass():
    prov = "M(corner arris u10) in y; x UNMEASURED as of r27"
    v = RG.audit_spec(_spec(
        [{"name": "left_wall", "prov": prov, "seen": "u10"}],
        declared_gaps={"right_wall_x": "no evidence in frame"}))
    assert len(v) == 1 and "left_wall" in v[0]


# --- R7: every critic answer owes a triage ---------------------------------

C3_ANSWER = "**1. bed**\n...\n**2. wardrobe**\n...\n**3. floor**\n"
C2_ANSWER = "## 1. bed\n...\n## 2. wardrobe\n...\n## 3. floor\n"


def _bundle(tmp_path, name="critique-trn002_mat_r26", **files):
    d = tmp_path / name
    d.mkdir()
    for fn, body in files.items():
        (d / fn.replace("__", ".")).write_text(body, encoding="utf-8")
    return str(d)


def test_an_untriaged_critic_answer_fails(tmp_path):
    b = _bundle(tmp_path, ANSWER_gemini25pro__md=C3_ANSWER, README__md="# bundle\n")
    v = RG.audit_bundle(b)
    assert len(v) == 1 and "C3#1, C3#2, C3#3" in v[0]


def test_a_partially_triaged_answer_names_only_the_missing_items(tmp_path):
    """The rule is item-level, so the check has to be. A file-level check
    reported eleven correctly-triaged rounds as untriaged."""
    b = _bundle(tmp_path, ANSWER_gemini25pro__md=C3_ANSWER,
                TRIAGE_gemini25pro__md="C3#1 accept, C3#3 refuted at 0.29")
    v = RG.audit_bundle(b)
    assert len(v) == 1 and "C3#2" in v[0] and "C3#1" not in v[0]


def test_a_comma_list_triages_every_id_in_it(tmp_path):
    b = _bundle(tmp_path, ANSWER_claude_local_c2__md=C2_ANSWER,
                TRIAGE_claude_local_c2__md="**C2#1,2,3** -> cloth lane")
    assert RG.audit_bundle(b) == []


def test_the_gate_artifact_counts_as_the_triage_surface(tmp_path):
    """Where the triage of record actually lives. Checking only the bundle dir
    is why this half of the gate found nothing for 27 rounds."""
    lane = tmp_path / "lane"
    lane.mkdir()
    (lane / "gate-14-r26.md").write_text("| C2#1 | ok |\nC2#2, C2#3 accepted",
                                         encoding="utf-8")
    b = _bundle(tmp_path, ANSWER_claude_local_c2__md=C2_ANSWER)
    assert RG.audit_bundle(b, str(lane)) == []


def test_a_gate_for_a_different_round_does_not_pay_this_round_s_debt(tmp_path):
    """Ids are not unique across rounds — gate #14 and gate #15 both carry a
    C2#12. Without this the newest gate silently clears every older bundle."""
    lane = tmp_path / "lane"
    lane.mkdir()
    (lane / "gate-15-r27.md").write_text("C2#1, C2#2, C2#3 all triaged",
                                         encoding="utf-8")
    b = _bundle(tmp_path, ANSWER_claude_local_c2__md=C2_ANSWER)
    v = RG.audit_bundle(b, str(lane))
    assert len(v) == 1 and "C2#1" in v[0]


def test_a_gate_that_names_the_bundle_binds_to_it(tmp_path):
    """A gate may triage the PREVIOUS round's answers; it declares that by
    naming the bundle dir. Without this binding, five correctly-triaged Gemini
    items were reported as debt."""
    lane = tmp_path / "lane"
    lane.mkdir()
    (lane / "gate-06-r15.md").write_text(
        "raw answers in `critique-trn002_mat_r14/ANSWER_gemini25pro.md`\n"
        "## C3 Gemini\n| 1 | a | ok |\n| 2 | b | ok |\n| 3 | c | ok |\n",
        encoding="utf-8")
    b = _bundle(tmp_path, "critique-trn002_mat_r14",
                ANSWER_gemini25pro__md=C3_ANSWER)
    assert RG.audit_bundle(b, str(lane)) == []


def test_the_table_notation_is_attributed_to_the_critic_named_above_it(tmp_path):
    lane = tmp_path / "lane"
    lane.mkdir()
    (lane / "gate-14-r26.md").write_text(
        "## C2 local\n| 1 | x | ok |\n\n## C3 Gemini\n| 1 | y | ok |\n",
        encoding="utf-8")
    b = _bundle(tmp_path, ANSWER_claude_local_c2__md="## 1. bed\n## 2. rug\n")
    v = RG.audit_bundle(b, str(lane))
    assert len(v) == 1 and "C2#2" in v[0] and "C2#1" not in v[0]


def test_gemini_cited_as_G_hash_is_the_same_critic_as_C3(tmp_path):
    """Gate #7 writes G#1 … G#4 and G(r15)#5. Three notations for one rule."""
    lane = tmp_path / "lane"
    lane.mkdir()
    (lane / "gate-07-r19.md").write_text("G#1 ok · G#2 ok · G(r15)#3 ok",
                                         encoding="utf-8")
    b = _bundle(tmp_path, "critique-trn002_mat_r19",
                ANSWER_gemini25pro__md=C3_ANSWER)
    assert RG.audit_bundle(b, str(lane)) == []


def test_an_unparseable_answer_does_not_cry_wolf(tmp_path):
    b = _bundle(tmp_path, ANSWER_gemini25pro__md="a wall of prose, no numbering")
    assert RG.audit_bundle(b) == []


def test_a_bundle_with_no_critic_answer_owes_nothing(tmp_path):
    b = _bundle(tmp_path, README__md="# pending")
    assert RG.audit_bundle(b) == []


# --- R7 debt resolution: which bundles still owe -----------------------------

def test_round_token_is_read_from_a_spec_or_a_bundle_name():
    assert RG.round_of("spec_r28.json") == "r28"
    assert RG.round_of("critique-trn002_mat_r27") == "r27"
    assert RG.round_of("critique-trn002_blockout_r1_quick") == "r1"
    assert RG.round_of("no-round-here") is None


def test_a_waiver_does_not_leak_across_a_name_prefix():
    """THE BUG THIS TEST EXISTS FOR. `x in text` let a waiver written for
    critique-trn002_blockout_r1_quick silently waive critique-trn002_blockout_r1
    — both bundles exist in this lane. A guard that quietly excuses work nobody
    excused is worse than no guard."""
    w = "waived 2026-08-07: critique-trn002_blockout_r1_quick — answers superseded"
    assert RG.is_waived("critique-trn002_blockout_r1_quick", w)
    assert not RG.is_waived("critique-trn002_blockout_r1", w)
    assert not RG.is_waived("critique-trn002_mat_r27", w)


def test_bundle_debt_skips_the_round_being_rendered(tmp_path):
    """A gate that blocks a render on a critique OF that render can never open."""
    for r in ("r27", "r28"):
        b = tmp_path / f"critique-trn002_mat_{r}"
        b.mkdir()
        (b / "ANSWER_gemini25pro.md").write_text(C3_ANSWER, encoding="utf-8")
    owing = RG.bundle_debt(str(tmp_path), "training/TRN-002/spec_r28.json")
    assert [os.path.basename(p) for p in owing] == ["critique-trn002_mat_r27"]


def test_bundle_debt_ignores_a_bundle_with_no_answer_and_sorts_oldest_first(tmp_path):
    for r, ans in (("r9", True), ("r23", True), ("r25", False)):
        b = tmp_path / f"critique-trn002_mat_{r}"
        b.mkdir()
        if ans:
            (b / "ANSWER_gemini25pro.md").write_text(C3_ANSWER, encoding="utf-8")
    owing = RG.bundle_debt(str(tmp_path), "spec_r28.json")
    assert [os.path.basename(p) for p in owing] == [
        "critique-trn002_mat_r9", "critique-trn002_mat_r23"]


def test_bundle_debt_honours_a_written_waiver(tmp_path):
    b = tmp_path / "critique-trn002_mat_r14"
    b.mkdir()
    (b / "ANSWER_gemini25pro.md").write_text(C3_ANSWER, encoding="utf-8")
    wf = tmp_path / "waivers.md"
    wf.write_text("critique-trn002_mat_r14 — bundle predates the rule", encoding="utf-8")
    assert RG.bundle_debt(str(tmp_path), "spec_r28.json", str(wf)) == []
    assert len(RG.bundle_debt(str(tmp_path), "spec_r28.json")) == 1


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
