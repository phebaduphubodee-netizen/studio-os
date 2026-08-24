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


# --- R9 diagnostic + R10 cap -------------------------------------------------

PANEL = {"clipped_pct": 0.034, "p99": 0.7153, "p50": 0.3724, "LEVEL": 1.000,
         "SHAPE": 0.0}
# This lane's own published rows, gates #10-#15.
HISTORY = [
    ("r23", {"clipped_pct": 2.804, "p99": 1.0000, "p50": 0.3237, "LEVEL": 1.046, "SHAPE": 0.3031}),
    ("r24", {"clipped_pct": 0.731, "p99": 0.8704, "p50": 0.3742, "LEVEL": 0.847, "SHAPE": 0.2761}),
    ("r25", {"clipped_pct": 0.093, "p99": 0.8522, "p50": 0.3323, "LEVEL": 0.829, "SHAPE": 0.3165}),
    ("r26", {"clipped_pct": 0.124, "p99": 0.7232, "p50": 0.3818, "LEVEL": 0.837, "SHAPE": 0.1989}),
    ("r27", {"clipped_pct": 0.125, "p99": 0.7238, "p50": 0.3869, "LEVEL": 0.849, "SHAPE": 0.2000}),
]
LEDGER = [{"round": r, "scalars": s} for r, s in HISTORY]


def test_a_target_of_zero_uses_the_raw_value_not_a_division():
    assert RG.distance({"SHAPE": 0.2}, {"SHAPE": 0.0}) == 0.2


def test_D_is_undefined_when_no_panel_row_is_present():
    try:
        RG.distance({"other": 1.0}, PANEL)
    except ValueError:
        return
    assert False, "an empty panel must raise, never return 0.0"


def test_the_aggregate_D_descends_on_every_round_of_this_lane():
    """The reason D is DIAGNOSTIC and not a gate. It never fires, because one
    row collapsed from 82x off target to 2.7x and carries the median."""
    ds = [r["D"] for r in RG.yield_report(LEDGER, PANEL)]
    assert ds == sorted(ds, reverse=True), ds


def test_LEVEL_got_worse_across_the_same_rounds_the_aggregate_called_progress():
    rows = RG.yield_report(LEDGER, PANEL)
    assert rows[-1]["rows"]["LEVEL"] > 3 * rows[0]["rows"]["LEVEL"]


def test_the_per_row_report_names_rows_that_worsened_while_D_fell():
    """r27: D falls 7.4% while four of five rows move away from target. This is
    the whole value of the diagnostic."""
    rows = RG.yield_report(LEDGER, PANEL)
    assert rows[-1]["D"] < rows[-2]["D"]
    assert set(rows[-1]["worsened"]) == {"SHAPE", "clipped_pct", "p50", "p99"}


def test_no_ledger_row_means_round_one_may_not_render():
    v = RG.cap_check(None, 0, 0)
    assert len(v) == 1 and "before its first render" in v[0]


def test_a_cap_that_is_declared_and_not_exceeded_passes():
    assert RG.cap_check({"cap_rounds": 20, "cap_full_frames": 40}, 19, 37) == []


def test_an_exceeded_cap_names_the_rule_that_extends_it():
    v = RG.cap_check({"cap_rounds": 20, "cap_full_frames": 40}, 27, 25)
    assert len(v) == 1 and "cap_rounds exceeded: 27 > 20" in v[0] and "R3" in v[0]


def test_a_ledger_row_missing_a_cap_field_is_a_violation():
    v = RG.cap_check({"cap_rounds": 20}, 1, 1)
    assert len(v) == 1 and "cap_full_frames" in v[0]


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


# --- the notations this lane actually writes (added 2026-08-08) --------------
#
# The r32 bundle carried a 13 KB triage covering all 24 of its items and the gate
# read it as empty, then refused the next render for 24 items that had all been
# answered. Three separate format assumptions caused it, and each is pinned below.
# A guard that fails on correct work is the one that gets switched off.

def test_a_combined_TRIAGE_md_is_read_not_only_TRIAGE_critic_md(tmp_path):
    b = _bundle(tmp_path, ANSWER_gemini25pro__md=C3_ANSWER,
                TRIAGE__md="C3#1 accept\nC3#2 accept\nC3#3 refuted at 0.29\n")
    assert RG.audit_bundle(b) == []


def test_a_bold_table_row_counts(tmp_path):
    b = _bundle(tmp_path, ANSWER_gemini25pro__md=C3_ANSWER,
                TRIAGE__md="## C3 — Gemini\n\n| # | item | triage |\n|---|---|---|\n"
                           "| **1** | a | accept |\n| **2** | b | accept |\n"
                           "| **3** | c | refuted, 0.29 |\n")
    assert RG.audit_bundle(b) == []


def test_a_letter_prefixed_table_row_counts_under_its_critic_heading(tmp_path):
    # The r32 triage numbered Gemini's items G1..G6 rather than C3#1..C3#6.
    b = _bundle(tmp_path, ANSWER_gemini25pro__md=C3_ANSWER,
                TRIAGE__md="## C3 — Gemini 2.5 Pro, cross-vendor\n\n"
                           "| # | item | triage |\n|---|---|---|\n"
                           "| **G1** | a | accept |\n| **G2** | b | accept |\n"
                           "| **G3** | c | refuted, 0.29 |\n")
    assert RG.audit_bundle(b) == []


def test_tolerating_the_FORM_does_not_tolerate_ABSENCE(tmp_path):
    # The whole risk of loosening a parser is that it starts passing empty work.
    # Same table, one row short: the missing item must still be named.
    b = _bundle(tmp_path, ANSWER_gemini25pro__md=C3_ANSWER,
                TRIAGE__md="## C3 — Gemini\n\n| # | item | triage |\n|---|---|---|\n"
                           "| **G1** | a | accept |\n| **G3** | c | refuted |\n")
    v = RG.audit_bundle(b)
    assert len(v) == 1 and "C3#2" in v[0]


# --- R10's other half: the object that is NOT here ---------------------------
# coverage_check could name `wall_floor_junction` on r31 and r32 and was wired
# into nothing, so every render went through. These pin the wire, not the maths
# (test_coverage_check.py owns the maths).

def _manifest(tmp_path, entries, baseline=None, name="coverage-manifest.json"):
    p = tmp_path / name
    body = {"entries": entries}
    if baseline is not None:
        body["absent_baseline"] = baseline
    p.write_text(json.dumps(body), encoding="utf-8")
    return str(p)


def test_a_lane_with_no_manifest_FAILS_rather_than_passing_quietly(tmp_path):
    # The mute is the failure mode this whole file exists to prevent: from
    # outside, "nothing to check" and "nothing wrong" print the same thing.
    v = RG.audit_coverage(_spec([{"name": "wall", "prov": "M(1)"}]),
                          str(tmp_path / "coverage-manifest.json"))
    assert len(v) == 1 and "no coverage manifest at" in v[0]


def test_coverage_with_no_manifest_path_at_all_is_a_violation():
    v = RG.audit_coverage(_spec([]), None)
    assert len(v) == 1 and "cannot run" in v[0]


def test_an_empty_manifest_is_the_mute_it_exists_to_prevent(tmp_path):
    v = RG.audit_coverage(_spec([{"name": "wall", "prov": "M(1)"}]),
                          _manifest(tmp_path, []))
    assert len(v) == 1 and "no entries" in v[0]


def test_an_object_the_reference_shows_and_the_spec_lacks_blocks(tmp_path):
    m = _manifest(tmp_path, [{"id": "wall_floor_junction", "what": "skirting"}])
    v = RG.audit_coverage(_spec([{"name": "wall", "prov": "M(1)"}]), m)
    assert len(v) == 1 and "wall_floor_junction" in v[0]


def test_a_built_object_and_a_declared_gap_both_discharge(tmp_path):
    m = _manifest(tmp_path, [{"id": "mirror"}, {"id": "led_strip"}])
    spec = _spec([{"name": "mirror", "prov": "M(1)"}],
                 declared_gaps={"led_strip": "no emissive path yet — gate #19"})
    assert RG.audit_coverage(spec, m) == []


def test_the_manifest_is_DERIVED_from_the_lane_so_no_call_site_can_forget_it(tmp_path):
    # R7 was mute for 27 rounds because check() ran it only `if bundle_dir:`
    # and the one call site passed none. Deriving beats passing.
    assert RG.manifest_for(str(tmp_path)).endswith("coverage-manifest.json")
    assert RG.manifest_for(str(tmp_path), "/explicit/x.json") == "/explicit/x.json"
    assert RG.manifest_for(None) is None


# --- Continuity: dropped by omission -----------------------------------------

def test_the_chair_leg_class_is_caught(tmp_path):
    prev = _spec([{"name": "chair_leg_1", "prov": "M(three feet backprojected)"}])
    now = _spec([])
    v = RG.audit_continuity(now, None, prev_spec=prev)
    assert len(v) == 1
    assert "DROPPED `chair_leg_1`" in v[0]
    assert "was a MEASUREMENT" in v[0]


def test_an_object_may_leave_the_frame_as_a_written_decision(tmp_path):
    prev = _spec([{"name": "lamp_stem", "prov": "M(1)"}])
    now = _spec([], declared_gaps={"lamp_stem": "removed: a bare post that only "
                                                "existed to carry a shade (R10)"})
    assert RG.audit_continuity(now, None, prev_spec=prev) == []


def test_a_gap_with_no_reason_does_not_discharge_a_drop():
    # r32 turned declared_gaps into a list and lost ten reasons. A bare name is
    # not a decision here either.
    prev = _spec([{"name": "lamp_stem", "prov": "M(1)"}])
    now = _spec([], declared_gaps=["lamp_stem"])
    v = RG.audit_continuity(now, None, prev_spec=prev)
    assert len(v) == 1 and "DROPPED" in v[0]


def test_a_VERIFIED_rename_discharges_a_drop():
    prev = _spec([{"name": "back_wall", "prov": "M(1)"}])
    now = _spec([{"name": "back_wall_L", "prov": "M(1)"},
                 {"name": "back_wall_R", "prov": "M(2)"}],
                renamed={"back_wall": ["back_wall_L", "back_wall_R"]})
    assert RG.audit_continuity(now, None, prev_spec=prev) == []


def test_a_rename_that_points_at_nothing_fails_louder_than_the_drop():
    prev = _spec([{"name": "back_wall", "prov": "M(1)"}])
    now = _spec([{"name": "something_else", "prov": "M(1)"}],
                renamed={"back_wall": "back_wall_L"})
    v = RG.audit_continuity(now, None, prev_spec=prev)
    assert len(v) == 1 and "RENAME UNVERIFIED" in v[0]


# --- why there is no DOWNGRADE rule ------------------------------------------
# One lived here for an afternoon and was deleted the same day: 12 of its 13
# lifetime events fired at r12, the round that IMPROVED provenance by rewriting
# `M(...)` tags into prose audit notes carrying subpixel numbers. It keyed on
# NOTATION, not on evidence. These two tests are what made the delete safe, and
# they stay so that nobody re-adds it without re-checking the premise.

def test_audit_spec_ALREADY_catches_a_real_downgrade_so_continuity_need_not():
    for prov in ("A(bedding norm)", "A(seat 450 vanity norm; C2 range 450-480)"):
        v = RG.audit_spec(_spec([{"name": "bolster", "prov": prov,
                                  "seen": "u 1..2, v 1..2"}]))
        assert len(v) == 1 and "NOTHING about this object is measured" in v[0], prov


def test_a_prose_measurement_is_not_a_regression_and_nothing_convicts_it():
    # The exact r12 rewrite, verbatim. The deleted rule called this a downgrade.
    prev = _spec([{"name": "chair_back",
                   "prov": "D(on seat; back top = old chair top 780 < desk 875)"}])
    now = _spec([{"name": "chair_back", "seen": "u 1..2, v 1..2",
                  "prov": "audit 2026-08-05 (sighted local critic, R10b): "
                          "top 780 -> 774 (measured)."}])
    assert RG.audit_continuity(now, None, prev_spec=prev) == []
    assert RG.audit_spec(now) == []


def test_a_new_object_is_not_a_continuity_violation():
    prev = _spec([{"name": "wall", "prov": "M(1)"}])
    now = _spec([{"name": "wall", "prov": "M(1)"}, {"name": "skirting", "prov": "M(2)"}])
    assert RG.audit_continuity(now, None, prev_spec=prev) == []


def test_the_first_round_of_a_line_has_nothing_to_compare_and_says_nothing():
    assert RG.audit_continuity(_spec([]), None) == []


# --- previous_spec_path: the two hazards that make N-1 wrong -----------------

def test_the_previous_round_skips_a_number_that_was_never_written(tmp_path):
    # spec_r13.json does not exist. A literal N-1 lookup no-ops exactly where
    # the chair-leg drop happened.
    for n in (11, 12, 14):
        (tmp_path / f"spec_r{n}.json").write_text("{}", encoding="utf-8")
    got = RG.previous_spec_path(str(tmp_path / "spec_r14.json"))
    assert os.path.basename(got) == "spec_r12.json"


def test_bracket_variants_are_not_the_line_of_record(tmp_path):
    # r30 has thirteen of these; none of them is "the previous round".
    for n in ("29", "30", "30w110", "30w240"):
        (tmp_path / f"spec_r{n}.json").write_text("{}", encoding="utf-8")
    assert os.path.basename(
        RG.previous_spec_path(str(tmp_path / "spec_r30.json"))) == "spec_r29.json"
    # and a variant itself has no line of record to compare against
    assert RG.previous_spec_path(str(tmp_path / "spec_r30w110.json")) is None


def test_the_earliest_round_has_no_predecessor(tmp_path):
    (tmp_path / "spec_r1.json").write_text("{}", encoding="utf-8")
    assert RG.previous_spec_path(str(tmp_path / "spec_r1.json")) is None


# --- The roster: a half that did not run must say so -------------------------

def test_the_roster_names_every_half_that_did_NOT_run():
    roster = []
    RG.check(_spec([{"name": "wall", "prov": "M(1)"}]), roster=roster)
    skipped = {n for n, ok, _ in roster if not ok}
    assert {"R7 triage", "charter distillation"} <= skipped
    assert "R10 spec" in {n for n, ok, _ in roster if ok}


def test_craft_is_advisory_and_never_reaches_the_violation_list():
    # craft_check cannot see occlusion and says so; over-reporting is correct,
    # vetoing on it is not. Same call R9b made for interpenetration.
    spec = _spec([{"name": "bench", "prov": "M(1)", "kind": "oct", "cut": 200,
                   "seg": 2, "c": [0, 0, 0]}],
                 camera={"x_mm": 3000, "y_mm": 0, "z_mm": 0})
    adv = []
    v = RG.check(spec, advisories=adv)
    assert any("silhouette shortfall" in a for a in adv)
    assert not any("silhouette" in s for s in v)


# --- the ratchet: "may shrink, may never grow" as a program ------------------
# It was prose in three places (the manifest, coverage_check's docstring, the lane's own
# plan) and enforced nowhere: audit() only tested membership, so declaring seven gaps and
# adding seven ids to the baseline in one edit passed forever after.

def _mf(tmp_path, baseline):
    p = tmp_path / "coverage-manifest.json"
    p.write_text(json.dumps({"entries": [{"id": "x"}], "absent_baseline": baseline}),
                 encoding="utf-8")
    return str(p)


def test_a_baseline_that_grew_is_refused(tmp_path):
    v = RG.baseline_ratchet(_mf(tmp_path, ["a", "b"]), previous={"absent_baseline": ["a"]})
    assert len(v) == 1 and "GREW by ['b']" in v[0]


def test_a_baseline_that_shrank_is_the_whole_point(tmp_path):
    assert RG.baseline_ratchet(_mf(tmp_path, ["a"]),
                               previous={"absent_baseline": ["a", "b"]}) == []


def test_an_unchanged_baseline_passes(tmp_path):
    assert RG.baseline_ratchet(_mf(tmp_path, ["a", "b"]),
                               previous={"absent_baseline": ["b", "a"]}) == []


def test_swapping_one_exemption_for_another_still_counts_as_growth(tmp_path):
    # Same LENGTH, different content: a size check would pass this, and it is exactly how
    # an inconvenient object gets quietly swapped in for one that was built.
    v = RG.baseline_ratchet(_mf(tmp_path, ["a", "c"]),
                            previous={"absent_baseline": ["a", "b"]})
    assert len(v) == 1 and "'c'" in v[0]


def test_an_uncommitted_manifest_cannot_be_ratcheted_and_says_so(tmp_path):
    # No `previous` and a path git has never seen: a ratchet with no history is a list.
    v = RG.baseline_ratchet(_mf(tmp_path, ["a"]))
    assert len(v) == 1 and "not committed" in v[0]


# --- Phase 0 repairs: the bypasses an adversarial pass drove through ----------

def test_a_declared_aggregate_covers_the_masses_its_entry_names():
    # declared_gaps['duvet'] covering duvet_top + duvet_drape is legitimate, and
    # the COVERAGE half of the same run already accepts it. Without this the two
    # halves contradict each other on one spec.
    man = {"entries": [{"id": "duvet", "built_as": ["duvet_top", "duvet_drape"]}]}
    prev = _spec([{"name": "duvet_top", "prov": "M(1)"},
                  {"name": "duvet_drape", "prov": "M(2)"}])
    now = _spec([], declared_gaps={"duvet": "REMOVED from the frame at r10, owner saw it"})
    assert RG.audit_continuity(now, None, prev_spec=prev, manifest=man) == []


def test_an_aggregate_gap_does_NOT_cover_masses_its_entry_never_named():
    # The prefix-match version of this would let `chair` swallow chair_leg_1..4 —
    # the exact defect the whole rule exists for.
    man = {"entries": [{"id": "chair", "built_as": ["chair_seat"]}]}
    prev = _spec([{"name": "chair_leg_1", "prov": "M(three feet backprojected)"}])
    now = _spec([], declared_gaps={"chair": "not in frame"})
    v = RG.audit_continuity(now, None, prev_spec=prev, manifest=man)
    assert len(v) == 1 and "DROPPED `chair_leg_1`" in v[0]


def test_a_zero_size_namesake_mass_cannot_resolve_an_entry(tmp_path):
    # Seven 0x0x0 masses named after the seven entries passed the whole gate.
    m = _manifest(tmp_path, [{"id": "mirror"}])
    spec = _spec([{"name": "mirror", "c": [0, 0, 0], "s": [0, 0, 0],
                   "prov": "M(px) placeholder", "seen": "u 1..2, v 1..2"}])
    v = RG.audit_coverage(spec, m)
    assert len(v) == 1 and "UNCOVERED `mirror`" in v[0]


def test_a_real_sized_mass_still_resolves_its_entry(tmp_path):
    m = _manifest(tmp_path, [{"id": "mirror"}])
    spec = _spec([{"name": "mirror", "c": [0, 0, 0], "s": [600, 12, 900],
                   "prov": "M(px)", "seen": "u 1..2, v 1..2"}])
    assert RG.audit_coverage(spec, m) == []


def test_one_mass_may_not_realise_two_entries(tmp_path):
    m = _manifest(tmp_path, [{"id": "mirror", "built_as": ["floor"]},
                             {"id": "led_strip", "built_as": ["floor"]}])
    spec = _spec([{"name": "floor", "c": [0, 0, 0], "s": [5000, 5000, 20],
                   "prov": "M(px)", "seen": "u 1..2, v 1..2"}])
    v = RG.audit_coverage(spec, m)
    assert any("claimed by 2 manifest entries" in s for s in v)


def test_deleting_a_manifest_entry_is_refused_without_a_signoff(tmp_path):
    now = {"entries": [{"id": "a"}], "absent_baseline": []}
    was = {"entries": [{"id": "a"}, {"id": "wall_floor_junction"}], "absent_baseline": []}
    (tmp_path / "coverage-manifest.json").write_text(json.dumps(now), encoding="utf-8")
    v = RG.baseline_ratchet(str(tmp_path / "coverage-manifest.json"), now, previous=was)
    assert len(v) == 1 and "LOST entries ['wall_floor_junction']" in v[0]


def test_an_owner_signed_entry_removal_is_allowed(tmp_path):
    now = {"entries": [{"id": "a"}], "absent_baseline": [],
           "absent_baseline_signoff": {"wall_floor_junction":
                                       "owner 2026-08-09: the target has no junction detail"}}
    was = {"entries": [{"id": "a"}, {"id": "wall_floor_junction"}], "absent_baseline": []}
    (tmp_path / "coverage-manifest.json").write_text(json.dumps(now), encoding="utf-8")
    assert RG.baseline_ratchet(str(tmp_path / "coverage-manifest.json"), now, previous=was) == []


# --- D-021: the room lane, where nine of thirteen rungs have no referent ---------

# `check_room` reads the LIVE ledgers (qa/owner-orders.json, qa/open-decisions.json)
# for the orders rung, so these two must assert about the rung they name and not
# about the length of the whole list. They were written as exact-list assertions and
# went red on 2026-08-17 the moment a REAL owner order was filed not-obeyed and its
# stop-loss fired — i.e. the rung under test was fine and the test was measuring the
# repo's current honesty. Pinning a unit test to the live ledger is the same shape as
# a metric that moves when something unrelated changes; the fix is to name the
# violation being asserted, never to quieten the gate so an assertion survives.
def _about(v, *needles):
    return [s for s in v if any(n in s for n in needles)]


def test_check_room_runs_R10_and_blocks_an_unjustified_object():
    v = RG.check_room({"masses": [{"name": "mystery", "prov": ""}]})
    assert len(_about(v, "no `prov`")) == 1


def test_check_room_does_NOT_fail_on_a_missing_coverage_manifest():
    # The whole reason check() could not be pointed at this lane. That manifest
    # is a READING OF THE REFERENCE, and client work has no reference — blocking
    # on the absence of an artefact that could never be correct to make is how a
    # guard gets switched off.
    v = RG.check_room({"masses": [{"name": "bed", "prov": "M(ink x1)"}]})
    assert _about(v, "coverage manifest", "coverage-manifest", "`prov`") == []


def test_every_inapplicable_rung_is_DECLARED_with_a_reason():
    # Not skipped. A rung that did not run must never read like one that passed —
    # the same law this phase repaired in audit_craft and in exit code 2.
    roster = []
    RG.check_room({"masses": [{"name": "bed", "prov": "M(ink x1)"}]}, roster=roster)
    names = {n for n, _, _ in roster}
    assert "R10 spec" in names
    for rung, _why in RG.ROOM_LANE_NOT_APPLICABLE:
        assert rung in names, rung
    inapplicable = {n for n, _ in RG.ROOM_LANE_NOT_APPLICABLE}
    for name, ran, why in roster:
        if ran:
            continue
        # TWO KINDS OF NOT-RUNNING, and they must not be spelled the same. A rung
        # in the declared list is STRUCTURALLY inapplicable here; anything else
        # that did not run COULD NOT run (P2r-9 with no full spec is the first
        # of that kind) and has to say which, because "does not apply" reads as
        # settled and "could not run" is an unknown.
        if name in inapplicable:
            assert why.startswith("not applicable to this lane:") and len(why) > 40
        else:
            assert not why.startswith("not applicable"), (name, why)
            assert len(why) > 30, (name, why)


def test_the_pixel_rung_says_WHY_it_can_never_apply_here():
    why = dict((n, w) for n, w in RG.ROOM_LANE_NOT_APPLICABLE)["R11 pixels"]
    assert "no target" in why and "deliverable_check" in why


# --- P0f: reachability, applied to SPEC KEYS ------------------------------------
# reachability_check.py covers .py modules; nothing covered the spec, and that is
# where `judge_lines` lived — a key claiming "the build is scored against them"
# that stored no value and had no reader, for its whole life. Six of the canonical
# spec's 21 top-level keys had no production reader when this was measured.
#
# THE CONVENTION, which the spec already carried in two places (`_pixel_claims_note`,
# `camera._solved`): a leading underscore DECLARES a note. Everything else is an
# input and must be read by something.
#
# HONEST LIMIT: the search is repo-wide, so another dict using the same key name
# would let a dead spec key pass. It can therefore only UNDER-report — it will
# never fail a key that is genuinely wired, and it does catch the blatant case
# that produced judge_lines: a name nothing in the repo ever subscripts.

def _unread_spec_keys(spec):
    """Top-level keys that no program subscripts and that are not declared notes."""
    import glob as _g
    import re as _re
    src = []
    for p in _g.glob(os.path.join(RG.REPO_ROOT, "pipeline", "scripts", "*.py")):
        if os.path.basename(p).startswith("test_"):
            continue
        with open(p, encoding="utf-8", errors="ignore") as f:
            src.append(f.read())
    blob = "\n".join(src)
    return [k for k in spec
            if not k.startswith("_")
            and not _re.search(r"""[\[\(]\s*["']""" + _re.escape(k) + r"""["']""", blob)]


def test_the_spec_key_guard_can_fail():
    # A guard that cannot fail is decoration. Negative control: a key no program
    # could possibly subscript must be reported.
    assert _unread_spec_keys({"masses": [], "zzz_no_reader_anywhere": 1}) == \
        ["zzz_no_reader_anywhere"]


def test_a_declared_note_is_exempt_from_the_spec_key_guard():
    assert _unread_spec_keys({"_zzz_no_reader_anywhere": 1}) == []


def test_every_non_underscore_spec_key_is_read_by_some_program():
    spec_p = os.path.join(RG.REPO_ROOT, "training", "TRN-002", "spec_r38.json")
    if not os.path.isfile(spec_p):          # lane archived: nothing to assert
        return
    with open(spec_p, encoding="utf-8") as f:
        spec = json.load(f)
    dead = _unread_spec_keys(spec)
    assert dead == [], (
        f"top-level spec key(s) {dead} are read by no program and are not "
        f"declared notes. Either wire a reader or prefix with '_' — an input "
        f"nothing consumes is the shape judge_lines had for its whole life.")


# --- P0f: exit 2 (COULD NOT RUN) was a bare `pass` on a full-fidelity frame ---
# The comment above it reasoned that only full fidelity closes a gate, and the
# code never tested `quick`. R11's own law, broken inside R11's implementation.

def test_a_clean_pixel_run_is_ok():
    assert RG.pixel_exit_policy(0, False) == ("ok", "")


def test_could_not_run_STOPS_a_full_fidelity_frame():
    action, msg = RG.pixel_exit_policy(2, False)
    assert action == "stop" and "COULD NOT RUN" in msg


def test_could_not_run_is_only_a_note_on_a_playblast():
    # Half resolution per axis is a different measurement; refusing to rescale
    # is the checker being correct, not the build failing.
    action, msg = RG.pixel_exit_policy(2, True)
    assert action == "note" and "playblast" in msg


def test_a_broken_claim_stops_either_way():
    assert RG.pixel_exit_policy(1, True)[0] == "stop"
    assert RG.pixel_exit_policy(1, False)[0] == "stop"


# --- bed_pixels' policy: the same three codes, and one narrower meaning for 1 ---
# The absolute defect is a printed line rather than a violation (it is true of
# all 15 masked frames this lane has), so exit 1 here means the number ROSE or
# the rung went BLIND — the builder's side, not the bed's outcome.

def test_a_clean_bed_run_is_ok():
    assert RG.bed_exit_policy(0, False) == ("ok", "")


def test_bed_could_not_run_STOPS_a_full_fidelity_frame():
    action, msg = RG.bed_exit_policy(2, False)
    assert action == "stop" and "COULD NOT RUN" in msg


def test_bed_could_not_run_is_only_a_note_on_a_playblast():
    action, msg = RG.bed_exit_policy(2, True)
    assert action == "note" and "playblast" in msg


def test_a_regression_stops_a_deliverable_and_only_notes_a_playblast():
    """The playblast half is not leniency: at half resolution the mask is not the
    baseline's camera, so there is no comparison to fail."""
    assert RG.bed_exit_policy(1, False)[0] == "stop"
    assert RG.bed_exit_policy(1, True)[0] == "note"


# --- P0f: audit_craft returned a bare [] for "clean" AND for "never measured" ---
# R11's own sentence, applied to an advisory rung: "could not look" must never
# print like "looked and it was fine". The docstring also claimed the roster
# named this rung; the caller passed no note() at all, in any version.

_CAM = {"x_mm": 0, "y_mm": -3000, "z_mm": 1300}


def test_craft_says_DID_NOT_RUN_when_the_spec_has_no_rounded_mass():
    # Used to return [] — indistinguishable from a clean measurement.
    ran, notes = RG.audit_craft(_spec([{"name": "wall"}], camera=_CAM))
    assert ran is False
    assert len(notes) == 1 and "DID NOT RUN" in notes[0]


def test_craft_says_DID_NOT_RUN_with_no_solved_camera():
    ran, notes = RG.audit_craft(_spec([{"name": "wall"}]))
    assert ran is False and "DID NOT RUN" in notes[0]


def test_craft_confirms_positively_when_it_measured_and_found_nothing():
    # The other half of the same defect: a clean measurement must SAY it measured.
    m = {"name": "post", "kind": "oct", "cut": 8.0, "seg": 64, "c": [0, 0, 500]}
    ran, notes = RG.audit_craft(_spec([m], camera=_CAM))
    assert ran is True
    assert len(notes) == 1 and "0 shortfalls" in notes[0] and "1 rounded mass" in notes[0]


def test_craft_still_reports_a_real_shortfall():
    m = {"name": "post", "kind": "oct", "cut": 120.0, "seg": 2, "c": [0, 0, 500]}
    ran, notes = RG.audit_craft(_spec([m], camera=_CAM))
    assert ran is True and "shortfall" in notes[0] and len(notes) == 2


def test_the_roster_names_the_craft_rung(tmp_path):
    # It never did. The docstring said otherwise for as long as it existed.
    roster, adv = [], []
    RG.check(_spec([{"name": "wall", "prov": "M(u1)"}], camera=_CAM),
             roster=roster, advisories=adv)
    assert any(name == "craft silhouette" for name, _, _ in roster)


# --- P0f: the sign-off was a string check, and a string check is a free pass ---
# `isinstance(v, str) and v.strip()` guarded BOTH halves of the ratchet. The
# message beside it asks for "<reason + date>", so the format was printed at the
# builder on every fire and enforced never. One character discharged it.

def _sign(tmp_path, value):
    now = {"entries": [{"id": "a"}], "absent_baseline": [],
           "absent_baseline_signoff": {"wall_floor_junction": value}}
    was = {"entries": [{"id": "a"}, {"id": "wall_floor_junction"}], "absent_baseline": []}
    (tmp_path / "coverage-manifest.json").write_text(json.dumps(now), encoding="utf-8")
    return RG.baseline_ratchet(str(tmp_path / "coverage-manifest.json"), now, previous=was)


def test_a_one_character_signoff_no_longer_discharges_a_lost_entry(tmp_path):
    assert len(_sign(tmp_path, "x")) == 1


def test_pasting_the_messages_own_placeholder_back_is_refused(tmp_path):
    # The cheapest possible bypass: the guard prints the template and accepts it.
    assert len(_sign(tmp_path, "<reason + date>")) == 1


def test_pending_is_refused_by_name_as_it_is_in_decisions_check(tmp_path):
    assert len(_sign(tmp_path, "pending")) == 1


def test_a_date_with_no_reason_is_not_a_signoff(tmp_path):
    assert len(_sign(tmp_path, "2026-08-10")) == 1


def test_a_reason_with_no_date_is_not_a_signoff(tmp_path):
    # Undated, so it cannot be placed in the record or matched to a diff.
    assert len(_sign(tmp_path, "the target has no junction detail")) == 1


def test_a_dated_reason_still_passes(tmp_path):
    assert _sign(tmp_path, "owner 2026-08-09: the target has no junction detail") == []


def test_the_growth_half_uses_the_same_rule_as_the_loss_half(tmp_path):
    # Both halves read the same field and one used to be checkable while the
    # other was not; they are now one function so they cannot drift apart.
    now = {"entries": [{"id": "a"}], "absent_baseline": ["b"],
           "absent_baseline_signoff": {"b": "x"}}
    (tmp_path / "coverage-manifest.json").write_text(json.dumps(now), encoding="utf-8")
    v = RG.baseline_ratchet(str(tmp_path / "coverage-manifest.json"), now,
                            previous={"entries": [{"id": "a"}], "absent_baseline": []})
    assert len(v) == 1 and "GREW" in v[0]


def test_adding_a_manifest_entry_is_always_free(tmp_path):
    now = {"entries": [{"id": "a"}, {"id": "b"}], "absent_baseline": []}
    was = {"entries": [{"id": "a"}], "absent_baseline": []}
    (tmp_path / "coverage-manifest.json").write_text(json.dumps(now), encoding="utf-8")
    assert RG.baseline_ratchet(str(tmp_path / "coverage-manifest.json"), now, previous=was) == []


def test_the_roster_admits_continuity_did_NOT_run_on_a_non_canonical_name(tmp_path):
    # Renaming spec_r33.json to spec_r33a.json used to disable the diff silently
    # while the roster reported it as RAN, "first of its line".
    p = tmp_path / "spec_r33a.json"
    p.write_text(json.dumps(_spec([])), encoding="utf-8")
    roster = []
    RG.check(_spec([{"name": "wall", "prov": "M(1)"}]), spec_path=str(p), roster=roster)
    cont = [(ok, why) for n, ok, why in roster if n == "continuity"]
    assert cont and cont[0][0] is False and "not a canonical" in cont[0][1]


# --- R1, now that it is wired ------------------------------------------------
# cap_check itself has had tests since the day it was written. What had NO tests,
# and is the whole reason R1 went unenforced for 34 rounds, is everything AROUND
# it: where the numbers come from, and whether check() calls it at all.

def _png(path, w, h):
    """Minimal valid PNG header — count_full_frames reads IHDR, never decodes."""
    import struct
    ihdr = b"IHDR" + struct.pack(">II", w, h) + b"\x08\x06\x00\x00\x00"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + ihdr)


def _caps(tmp, **units):
    p = tmp / "caps.json"
    p.write_text(json.dumps({"units": units}), encoding="utf-8")
    return str(p)


def test_full_frames_are_counted_by_PIXELS_not_by_filename(tmp_path):
    # The measured reason this matters: 137 of TRN-002's PNGs lack the `_quick`
    # token and only 44 are full frames. A filename count was wrong by 3x.
    _png(tmp_path / "trn002_r1.png", 1080, 821)
    _png(tmp_path / "trn002_r2.png", 1080, 821)
    _png(tmp_path / "trn002_r3_quick.png", 540, 410)
    _png(tmp_path / "_zoom_partition.png", 400, 400)      # no _quick, not a frame
    _png(tmp_path / "contactbands_tgt.png", 1050, 391)    # no _quick, not a frame
    assert RG.count_full_frames(str(tmp_path), (1080, 821)) == 2


def test_a_non_png_or_truncated_file_is_not_a_frame(tmp_path):
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    (tmp_path / "broken.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert RG.count_full_frames(str(tmp_path), (1080, 821)) == 0
    assert RG._png_size(str(tmp_path / "broken.png")) is None


def test_rounds_take_the_max_of_disk_and_the_specs_own_number(tmp_path):
    # TRN-002 is at round 34 with 31 canonical specs (r13 never existed). Either
    # reading alone is gameable; the max is not.
    for n in (1, 2, 5):
        (tmp_path / f"spec_r{n}.json").write_text("{}", encoding="utf-8")
    (tmp_path / "spec_r30w110.json").write_text("{}", encoding="utf-8")  # a variant
    assert RG.count_rounds(str(tmp_path)) == 3                    # variant excluded
    assert RG.count_rounds(str(tmp_path), {"round": 34}) == 34    # declaration floors it
    assert RG.count_rounds(str(tmp_path), {"round": 2}) == 3      # disk floors it back


def test_check_actually_calls_cap_check_and_the_cap_bites(tmp_path):
    lane = tmp_path / "TRN-XXX"
    lane.mkdir()
    rd = tmp_path / "renders"
    rd.mkdir()
    for i in range(4):
        _png(rd / f"f{i}.png", 1080, 821)
    caps = _caps(tmp_path, **{"TRN-XXX": {"cap_rounds": 9, "cap_full_frames": 3}})
    spec = _spec([{"name": "wall", "prov": "M(1)"}])
    spec["image"] = {"w": 1080, "h": 821}
    spec["round"] = 5
    v = RG.check(spec, lane_dir=str(lane), render_dir=str(rd), caps_path=caps)
    assert any("cap_full_frames exceeded: 4 > 3" in s for s in v), v
    assert not any("cap_rounds exceeded" in s for s in v), v


def test_an_undeclared_unit_may_not_render(tmp_path):
    lane = tmp_path / "TRN-UNDECLARED"
    lane.mkdir()
    spec = _spec([{"name": "wall", "prov": "M(1)"}])
    spec["image"] = {"w": 1080, "h": 821}
    v = RG.check(spec, lane_dir=str(lane), render_dir=str(tmp_path),
                 caps_path=_caps(tmp_path))
    assert any("no ledger row" in s for s in v), v


def test_a_missing_render_dir_is_a_VIOLATION_not_a_free_pass(tmp_path):
    # 0 frames passes any cap. A count that cannot run must not read as a count
    # that passed — the shape that left the R7 half silent for 27 rounds.
    lane = tmp_path / "TRN-XXX"
    lane.mkdir()
    caps = _caps(tmp_path, **{"TRN-XXX": {"cap_rounds": 99, "cap_full_frames": 3}})
    spec = _spec([{"name": "wall", "prov": "M(1)"}])
    spec["image"] = {"w": 1080, "h": 821}
    v = RG.check(spec, lane_dir=str(lane), caps_path=caps)
    assert any("could not bite" in s for s in v), v


def test_a_broken_caps_file_does_not_crash_the_render(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert RG.load_caps("TRN-002", str(bad)) is None
    assert RG.load_caps("TRN-002", str(tmp_path / "absent.json")) is None
    # ...and the absence surfaces as cap_check's own message, not a traceback
    assert any("no ledger row" in s for s in RG.cap_check(None, 0, 0))


def test_the_live_caps_file_declares_TRN_002_and_the_lane_is_inside_it():
    caps = RG.load_caps("TRN-002")
    assert caps, "qa/curriculum-caps.json must declare TRN-002 or R1 is a document again"
    lane = os.path.join(RG.REPO_ROOT, "training", "TRN-002")
    rd = os.path.join(RG.REPO_ROOT, "_private", "benchmark", "reproduction",
                      "TRN-002", "renders")
    rounds = RG.count_rounds(lane, {"round": 34})
    assert rounds <= caps["cap_rounds"], f"R1: {rounds} rounds vs cap {caps['cap_rounds']}"
    if os.path.isdir(rd):
        frames = RG.count_full_frames(rd, (1080, 821))
        assert frames <= caps["cap_full_frames"], (
            f"R1: {frames} full frames vs cap {caps['cap_full_frames']}")


# --- the round token must survive a render-mode suffix -------------------------
# r35: `critique-trn002_mat_r34_quick` produced NO token, so `_gate_text` found
# no gate artifact and reported all 23 triaged items as untriaged. R5 renders a
# `--quick` frame before any full one, so every playblast bundle was affected.

def test_round_token_survives_a_render_mode_suffix():
    for base, want in (("critique-trn002_mat_r34_quick", "r34"),
                       ("critique-trn002_mat_r34_full", "r34"),
                       ("critique-trn002_mat_r34", "r34"),
                       ("critique-trn002_blockout_r5c", "r5c")):
        m = RG.ROUND_TOKEN.search(base)
        assert m and m.group(1).lower() == want, f"{base} -> {m and m.group(1)}"


def test_a_bracket_variant_still_binds_to_nothing():
    # The loose fix (`_\w+`) would have bound r30's wattage sweep to some round.
    # A wrong binding lets one round's triage pay another's debt, which is the
    # failure `_gate_text`'s docstring was written about.
    assert RG.ROUND_TOKEN.search("critique-trn002_mat_r30w110") is None


def test_the_r34_bundle_now_finds_its_own_gate_artifact():
    import os
    lane = os.path.join(RG.REPO_ROOT, "training", "TRN-002")
    bundle = "critique-trn002_mat_r34_quick"
    if not os.path.isfile(os.path.join(lane, "gate-22-r34.md")):
        return  # artifact not present in this checkout
    txt = RG._gate_text(bundle, lane)
    assert "C3#1" in txt and "C2#3" in txt, "the round binding is broken again"


# --- R7c: the gate never asked whether the blind rung was blind ----------------
# It counted triage rows and nothing else. r35 fired C2 and C3 in parallel into
# one directory; the C2 agent read a folder that held C3's answer. The seeded
# list below is what keeps this from condemning twelve rounds it could not have
# changed — and it can only grow through a diff.

def _ask_bundle(tmp_path, name, c2=True, ask=None):
    import os
    d = tmp_path / name
    d.mkdir()
    (d / "PROMPT.md").write_text("judge this", encoding="utf-8")
    (d / (name.replace("critique-", "") + ".png")).write_bytes(
        b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    if c2:
        (d / "ANSWER_claude-local-c2.md").write_text("### 1. x\n", encoding="utf-8")
    if ask is not None:
        a = d / RG.C2_ASK_DIR
        a.mkdir()
        for n in ask:
            (a / n).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32
                                if n.endswith(".png") else b"x")
    return str(d)


def test_a_c2_answer_with_no_ask_dir_is_a_violation(tmp_path):
    v = RG.audit_blind_ask(_ask_bundle(tmp_path, "critique-trn002_mat_r36"))
    assert len(v) == 1 and RG.C2_ASK_DIR in v[0]


def test_a_blind_ask_dir_clears_it(tmp_path):
    d = _ask_bundle(tmp_path, "critique-trn002_mat_r36",
                ask=["trn002_mat_r36.png", "PROMPT.md", "README.md"])
    assert RG.audit_blind_ask(d) == []


def test_another_critics_answer_inside_the_ask_dir_is_a_violation(tmp_path):
    d = _ask_bundle(tmp_path, "critique-trn002_mat_r36",
                ask=["trn002_mat_r36.png", "PROMPT.md", "ANSWER_gemini25pro.md"])
    v = RG.audit_blind_ask(d)
    assert len(v) == 1 and "ANSWER_gemini25pro.md" in v[0]


def test_the_twelve_seeded_bundles_are_not_condemned_retroactively(tmp_path):
    assert RG.audit_blind_ask(
        _ask_bundle(tmp_path, "critique-trn002_mat_r35_quick")) == []
    assert len(RG.BLIND_ASK_SEEDED) == 12


def test_a_bundle_with_no_c2_answer_owes_nothing(tmp_path):
    """C3-only bundles exist (r14, r15) and this rule is not about them."""
    assert RG.audit_blind_ask(
        _ask_bundle(tmp_path, "critique-trn002_mat_r36", c2=False)) == []


def test_the_gate_runs_the_blind_ask_check_and_says_so(tmp_path):
    """The R7 half was mute for 27 rounds because `check()` never called it.
    The roster is what makes a mute visible, so pin the entry, not just the
    function."""
    d = _ask_bundle(tmp_path, "critique-trn002_mat_r36")
    roster = []
    v = RG.check({"masses": []}, bundle_dir=d, roster=roster)
    assert any(n == "R7c blind ask" and ran for n, ran, _ in roster)
    assert any(RG.C2_ASK_DIR in x for x in v)


def test_the_gate_and_the_bundle_builder_agree_on_what_blind_means(tmp_path):
    """Two definitions of one contract drift. This is the wire between them:
    a dir the builder calls blind must pass the gate, and the gate's refusal
    must name the same file the builder's does."""
    import critique_bundle as CB
    import os
    import pytest
    d = tmp_path / "critique-trn002_mat_r36"
    d.mkdir()
    (d / "PROMPT.md").write_text("judge this", encoding="utf-8")
    (d / "trn002_mat_r36.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 32)
    (d / "ANSWER_claude-local-c2.md").write_text("### 1. x\n", encoding="utf-8")
    ask = CB.c2_ask_dir(str(d), "trn002_mat_r36.png")
    assert RG.audit_blind_ask(str(d)) == []
    open(os.path.join(ask, "ANSWER_gemini25pro.md"), "w").write("x")
    assert "ANSWER_gemini25pro.md" in RG.audit_blind_ask(str(d))[0]
    with pytest.raises(CB.RefusedError):
        CB.assert_blind(ask)


# --- R1's frame cap was counting a directory that does not exist ---------------
# The fail-closed guard tested `not render_dir` — the truthiness of a string —
# and the render path was handing it `<lane>/renders/critique/renders`. A
# non-empty string that names nothing passed the test, frames counted 0, and 0
# passes every cap. Measured on the real tree 2026-08-09: that path yields 0
# full frames, the real one yields 44.

def _caps_file(tmp_path):
    import json
    p = tmp_path / "caps.json"
    p.write_text(json.dumps({"units": {"TRN-002": {"cap_rounds": 42,
                                                   "cap_full_frames": 55}}}),
                 encoding="utf-8")
    (tmp_path / "TRN-002").mkdir(exist_ok=True)
    return str(p)


def test_a_render_dir_that_does_not_exist_is_not_a_count_that_passed(tmp_path):
    assert RG.cap_check({"cap_rounds": 42, "cap_full_frames": 55}, 35, 0) == [],         "the cap itself is happy with 0 frames — which is the whole problem"
    roster = []
    got = RG.check({"masses": [], "image": {"w": 1080, "h": 821}},
                   lane_dir=str(tmp_path / "TRN-002"),
                   caps_path=_caps_file(tmp_path),
                   render_dir=str(tmp_path / "nope" / "renders"), roster=roster)
    assert any("cap could not bite" in s for s in got), got
    assert any(n == "R1 cap" and "NO READABLE RENDER DIR" in why
               for n, _, why in roster), roster


def test_a_readable_render_dir_still_counts(tmp_path):
    caps = _caps_file(tmp_path)
    rd = tmp_path / "renders"
    rd.mkdir()
    got = RG.check({"masses": [], "image": {"w": 1080, "h": 821}},
                   lane_dir=str(tmp_path / "TRN-002"), caps_path=caps,
                   render_dir=str(rd))
    assert not any("cap could not bite" in s for s in got), got


def test_the_lane_call_site_points_at_a_directory_that_exists():
    """The bug was in the CALL SITE, so pin the call site, not only the guard."""
    import os
    import re
    p = os.path.join(RG.REPO_ROOT, "pipeline", "scripts", "trn002_build.py")
    src = open(p, encoding="utf-8").read()
    m = re.search(r"render_dir=([^\n)]+)", src)
    assert m, "no render_dir argument at the lane's gate call site"
    assert "os.path.join(BUNDLE_ROOT" not in m.group(1), (
        "BUNDLE_ROOT already ends in renders/critique — joining 'renders' onto "
        "it names a path that has never existed, and 0 frames passes any cap")


def test_the_room_lane_runs_his_orders_too():
    """R13's own first test, and it is about this file rather than about a spec.

    `check_room` exists because nine rungs genuinely cannot run on client work —
    they need a reference, a manifest or a round series this lane does not have.
    The owner-channel rungs need none of that: they read ledgers and grep code.
    Leaving them in `check()` only would have made the rung built to stop "an
    order inert on the only lane being built" inert on the only lane being
    built."""
    roster = []
    RG.check_room({"masses": []}, roster=roster, spec={})
    names = [n for n, _ran, _why in roster]
    assert "owner orders" in names
    assert "sourcing" in names
    assert "owner asks" in names


def test_the_room_lane_reports_a_broken_order_as_a_violation():
    v = RG.check_room({"masses": []}, roster=[], spec={}, unit="DELIV-001")
    # the live ledger is clean, so this asserts the WIRING, not a failure
    assert isinstance(v, list)
    import orders_check as OC
    data = OC.load(repo_root=RG.REPO_ROOT)
    broken = dict(data)
    broken["orders"] = [dict(data["orders"][0],
                             obeyed_assert=[{"file": "CLAUDE.md",
                                             "pattern": "^_NOPE_XYZ$",
                                             "why": "w"}])]
    assert any("DOES NOT OBEY THIS ORDER" in s
               for s in OC.check_orders(broken, RG.REPO_ROOT))


def test_owner_channel_runs_the_same_rungs_for_both_of_its_callers():
    """R13's rungs must not depend on WHICH gate function called them.

    Found 2026-08-23. `owner_channel`'s four rungs — orders, sourcing,
    repo_first, asks — were indented inside its own `if decisions is None and
    unit:` lazy load. That guard is about whether the DECISION REGISTER still
    needs loading; it is not a condition on the rungs. So they fired for the
    caller that supplies no decisions (`check_room`, the DELIV-001 lane) and
    not for the caller that loads the register itself and passes it in
    (`check`, reached from `enforce`) — and the roster came back EMPTY, so the
    run did not even print that four rungs had been skipped.

    The test that existed, `test_the_room_lane_runs_his_orders_too`, exercised
    `check_room` only: the single caller the accidental guard happened to
    admit. It passed on every one of those days. This one pins every shape a
    caller can present, which is the property that was actually broken.
    """
    import decisions_check as DEC
    data = DEC.load(os.path.join(RG.REPO_ROOT, DEC.DECISIONS_REL))
    assert data, "the live decision register must be readable for this test"

    def rungs(decisions, unit):
        roster = []
        RG.owner_channel(unit, None,
                         lambda n, ran, why="": roster.append((n, ran, why)),
                         decisions)
        return {n for n, _ran, _why in roster}

    expected = {"owner orders", "sourcing", "repo_first", "owner asks"}
    assert expected <= rungs(None, "DELIV-001")   # what check_room passes
    assert expected <= rungs(data, "DELIV-001")   # what check passes
    assert expected <= rungs(data, "TRN-002")     # the reproduction lane
    assert expected <= rungs(None, None)          # no lane: repo-wide ledgers


def test_no_rung_reaches_one_entry_point_and_not_the_other():
    """THE GENERAL GUARD for the defect this file has now shipped three times.

    A rung wired into `check()` alone is a rung the production lane does not
    have: `build_room` calls `check_room` and nothing else. Three instances, all
    live on the same morning of 2026-08-23 —

      * `owner_channel`'s four R13 rungs, inert from `check()` (an indent);
      * the DECISION LOG, R3's entire replacement for the owner's own gate rung,
        which had never run OR PRINTED on DELIV-001 — 103 rows in force, 96 of
        them taken in his name, and the printing IS the control R3 kept;
      * the CRITIC-DEBT ledger, which was worse than skipped — absent from
        `check_room`'s roster AND from ROOM_LANE_NOT_APPLICABLE, so the block
        build_room prints every build named it neither way.

    The invariant is not "both entry points run everything" — nine rungs
    genuinely need a reference, a manifest or a round series client work does not
    have. It is that the room lane must either RUN a rung or NAME it, and that
    "did not run" must never be indistinguishable from "ran and was clean".
    """
    import contextlib
    import io as _io
    import room_masses as RM

    spec = json.load(open(os.path.join(
        RG.REPO_ROOT, "projects/PRJ-2026-002_c001-house/03_layout/"
                      "master-suite.CANONICAL.spec.json"), encoding="utf-8"))

    repro, room = [], []
    with contextlib.redirect_stdout(_io.StringIO()):
        RG.check({"id": "TRN-002", "masses": []}, roster=repro)
        RG.check_room(RM.as_gate_spec(spec, "x"), roster=room, spec=spec,
                      unit="DELIV-001")

    named = {n for n, _ran, _why in room} | {n for n, _why in RG.ROOM_LANE_NOT_APPLICABLE}
    missing = {n for n, _ran, _why in repro} - named
    assert not missing, (
        f"{sorted(missing)} run in check() and are neither run nor declared by "
        f"check_room — so a DELIV-001 render neither performs them nor prints "
        f"that it skipped them. Wire the rung into check_room, or add it to "
        f"ROOM_LANE_NOT_APPLICABLE with a reason that is true.")

    stale = {n for n, _why in RG.ROOM_LANE_NOT_APPLICABLE} - {n for n, _r, _w in repro}
    assert not stale, (
        f"{sorted(stale)} are declared not-applicable to the room lane but no "
        f"longer exist in check() — an exemption for a rung nobody has is how "
        f"the list stops describing anything")


def test_every_blocking_scene_dump_rung_is_actually_spawned_by_the_render():
    """THE SECOND HALF of the guard above, for the rungs rule_gate never sees.

    `test_no_rung_reaches_one_entry_point_and_not_the_other` covers rungs inside
    rule_gate's roster. It cannot see the four checks build_room spawns as
    SUBPROCESSES — existence_check, dim_check, sheet_recon, placement_check — and
    that is exactly where the defect was hiding on 2026-08-24: qa/coverage-map.json
    declared `sheet_recon (R12)` a BLOCKING scene-dump rung, plan_status printed
    that map at every session open, and `git log -S "sheet_recon.py" --
    build_room.py rule_gate.py` returned zero commits for the entire history. The
    render dutifully wrote `camera.floor_poly_mm` into every scene dump FOR that
    rung's frustum test and then never ran it. Thirteen days.

    The invariant: a rung this repo's own map calls BLOCKING at the scene-dump
    stage is either genuinely spawned by the render, or carries a dated
    `room_lane_debt` saying it is not. What it may never be is silently declared.

    THE EXEMPTION IS DATA, NEVER A NAME IN THIS TEST — R9b's lesson, in its own
    words: "A rule that names the objects it applies to will always exempt the
    next one." The two guards it names were written around `vase` and
    `candlestick` and left 8 of 13 objects unguarded.

    The spawn test is `"<script>.py")` — an argv element with its closing paren,
    not a bare mention. build_room carried two COMMENTS naming sheet_recon while
    never spawning it, and the owner-order assertion that was supposed to catch
    this was a bare text search those comments would have satisfied.
    """
    import re as _re

    cmap = json.load(open(os.path.join(RG.REPO_ROOT, "qa", "coverage-map.json"),
                          encoding="utf-8"))
    src = open(os.path.join(RG.REPO_ROOT, "pipeline", "scripts", "build_room.py"),
               encoding="utf-8").read()

    undeclared, stale, unscripted = [], [], []
    for r in cmap.get("rungs", []):
        if r.get("stage") != "scene-dump" or not r.get("blocking"):
            continue
        script = r["name"].split()[0] + ".py"
        if not os.path.exists(os.path.join(RG.REPO_ROOT, "pipeline", "scripts", script)):
            unscripted.append((r["name"], script))
            continue
        spawned = _re.search(r'"%s"\)' % _re.escape(script), src) is not None
        debt = r.get("room_lane_debt") or {}
        if spawned:
            if debt:
                stale.append(r["name"])
            continue
        if debt.get("since") and debt.get("why") and debt.get("restart_by"):
            continue
        undeclared.append((r["name"], script))

    assert not unscripted, (
        f"{unscripted}: the map names a scene-dump rung whose script does not "
        f"exist under pipeline/scripts. Either the row is stale or this test's "
        f"name->file derivation has drifted; both are worth a look.")
    assert not undeclared, (
        f"{undeclared} are declared BLOCKING at the scene-dump stage in "
        f"qa/coverage-map.json and are NOT spawned by build_room.py. This is the "
        f"sheet_recon state: a rung the map says stops a render, that no render "
        f"runs. Spawn it in _score_deliverable, or give the row a "
        f"`room_lane_debt` with since/why/restart_by so the hole is dated and "
        f"printed instead of implied.")
    assert not stale, (
        f"{stale} carry a `room_lane_debt` but ARE spawned by build_room.py — "
        f"delete the debt. An exemption that outlives the hole it described is "
        f"how the map stops describing anything.")


def test_the_deliverable_standard_loads_without_pil():
    """The gate's copy of the standard path must not drift, and must not need PIL.

    Found 2026-08-23, on the first render after the critic-debt rung was wired
    into `check_room`: `deliverable_check` does `from PIL import Image` at module
    scope, Blender's bundled Python has no PIL, so `load_standard()` — which is
    `open()` plus `json.load()` and needs no imaging whatever — was unreachable
    on the ONLY lane that renders. Every image door then returned NOT RUN and
    two of those were filed as ledger VIOLATIONS, failing the build.

    So the path is duplicated here deliberately, and this pins the copy.
    """
    import deliverable_check as DC
    assert RG.DELIVERABLE_STANDARD_REL == DC.STANDARD_REL, (
        "rule_gate's copy of the deliverable-standard path has drifted from "
        "deliverable_check.STANDARD_REL — the copy exists only to avoid the PIL "
        "import, not to become a second source of truth")
    assert RG._deliverable_standard() == DC.load_standard()


def test_a_standard_that_cannot_load_does_not_read_as_a_dishonest_ledger():
    """COULD-NOT-VERIFY and DISHONEST are different findings, and only the second
    may stop a render.

    Without the split the debt rung was red on every render — and debt_check's own
    file says a rung that is red on every render is a rung somebody switches off.
    The rows must still be reported; they must not be counted against the ledger.
    """
    import debt_check as DEBT
    led = DEBT.load()
    assert led is not None, "the live critic-debt ledger must be readable"

    without = DEBT.check(led, plan_phases=DEBT._plan_phases(), standard=None)
    unverified = [x for x in without if DEBT.NO_STANDARD in x]
    assert unverified, ("this test is decoration unless the live ledger has at "
                        "least one closed row with an image door")

    roster, v = [], []
    v += RG.ledger_rungs("DELIV-001", None,
                         lambda n, ran, why="": roster.append((n, ran, why)))[0]
    assert not [x for x in v if DEBT.NO_STANDARD in x], (
        "a row that could not be re-verified was filed as a blocking violation")
    assert "critic debt" in {n for n, _r, _w in roster}
