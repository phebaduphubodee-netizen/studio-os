"""Tests for plan_status — the plan's consumer.

The negative controls are the ways a plan-tracker becomes the thing it was built
to prevent: a review that is satisfied by reading, a phase that is done because
its work was performed rather than because its test passed, a stale hint that
outranks the data, and an unknown git state that prints like a clean one.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_status as PS  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _plan(**kw):
    p = {
        "unit": "DELIV-001",
        "goal": "a sendable frame",
        "current_phase": "P0",
        "standing_corrections": [],
        "phases": [
            {"id": "P0", "title": "instruments", "goal": "g0", "status": "open",
             "work": [{"id": "P0a", "what": "fix scale", "where": "a.py", "status": "todo"},
                      {"id": "P0b", "what": "catalog", "where": "b.json", "status": "todo"}],
             "exit_test": "the standard fails our best frame", "exit_result": None},
            {"id": "P1", "title": "baseline", "goal": "g1", "status": "blocked",
             "work": [{"id": "P1a", "what": "render", "where": "c.py", "status": "todo"}],
             "exit_test": "reproduces the prediction", "exit_result": None},
        ],
        "reviews": [],
        "last_review_commit": None,
    }
    p.update(kw)
    return p


# --- it knows where we are -----------------------------------------------------

def test_current_phase_is_the_first_not_done():
    p = _plan()
    assert PS.current(p)["id"] == "P0"
    p["phases"][0]["status"] = "done"
    assert PS.current(p)["id"] == "P1"


def test_a_stale_current_phase_hint_does_not_outrank_the_data():
    """`current_phase` is a convenience field. If it disagrees with the statuses,
    the statuses win — a hint that outranks the data is how a plan starts lying."""
    p = _plan(current_phase="P1")
    p["phases"][0]["status"] = "open"
    assert PS.current(p)["id"] == "P0"


def test_next_work_names_the_file_each_item_touches():
    p = _plan()
    nxt = PS.next_work(p, n=3)
    assert [w["id"] for _, w in nxt] == ["P0a", "P0b", "P1a"]
    assert all(w.get("where") for _, w in nxt)


def test_done_work_is_skipped():
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "done"
    assert PS.next_work(p, n=1)[0][1]["id"] == "P0b"


def test_progress_counts_work_items_not_phases():
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "done"
    assert PS.progress(p) == (1, 3)


# --- review cannot be satisfied by reading -------------------------------------

def test_review_refuses_when_a_remaining_phase_has_no_verdict():
    p = _plan()
    with pytest.raises(ValueError) as e:
        PS.record_review(p, {"P0": "keep: still right"}, commit="abc")
    assert "P1" in str(e.value)


def test_review_refuses_a_verdict_with_no_reason():
    p = _plan()
    with pytest.raises(ValueError) as e:
        PS.record_review(p, {"P0": "keep:", "P1": "keep: fine"}, commit="abc")
    assert "no reason" in str(e.value)


def test_review_refuses_a_word_that_is_not_keep_change_drop():
    p = _plan()
    with pytest.raises(ValueError) as e:
        PS.record_review(p, {"P0": "ok: looks good", "P1": "keep: fine"}, commit="abc")
    assert "not keep/change/drop" in str(e.value)


def test_a_review_that_changes_nothing_must_say_so_in_those_words():
    p = _plan()
    PS.record_review(p, {"P0": "keep: exit test still the right one",
                         "P1": "keep: unchanged"}, commit="abc")
    assert p["reviews"][-1]["changed"] == []
    assert "nothing changed" in p["reviews"][-1]["note"]


def test_a_review_records_which_phases_changed():
    p = _plan()
    PS.record_review(p, {"P0": "keep: fine",
                         "P1": "drop: the frame it produces is not the deliverable"},
                     commit="abc")
    assert p["reviews"][-1]["changed"] == ["P1"]
    assert p["last_review_commit"] == "abc"


def test_a_closed_phase_forces_a_review_until_one_is_recorded():
    p = _plan()
    p["phases"][0]["status"] = "done"
    due, why = PS.review_due(p)
    assert due and "closed" in why
    PS.record_review(p, {"P1": "keep: next"}, commit="abc")
    assert p["phases"][0]["_reviewed"] is True


def test_unknown_git_state_is_reported_as_unknown_not_as_zero(monkeypatch):
    """'could not look' must never print like 'looked and there was nothing' —
    the same law pixel_check's exit code 2 was written for."""
    monkeypatch.setattr(PS, "_git", lambda *a: None)
    p = _plan()
    due, why = PS.review_due(p)
    assert due is False and "unknown" in why and "not zero" in why


# --- the ritual that re-armed itself on completion -------------------------------
# record_review stamps last_review_commit = HEAD, and then the review's own edit
# to the plan has to be COMMITTED — landing at HEAD+1 and making a review due
# again, forever. Live since the plan's first commit: the only way to read "not
# due" was to leave the plan of record uncommitted, so every session opened on a
# REVIEW DUE that the previous session had in fact just done.

def _git_stub(shas, files_by_sha):
    def g(*a):
        if a[0] == "rev-list" and "--count" not in a:
            return "\n".join(shas)
        if a[0] == "show":
            return "\n".join(files_by_sha.get(a[-1], []))
        return None
    return g


def test_a_plan_only_commit_does_not_arm_the_review(monkeypatch):
    # The review writing itself down is not work closing.
    monkeypatch.setattr(PS, "_git", _git_stub(
        ["aaa"], {"aaa": ["qa/deliverable-plan.json"]}))
    p = _plan()
    p["last_review_commit"] = "old"
    assert PS.commits_since_review(p) == 0
    assert PS.review_due(p)[0] is False


def test_a_code_commit_still_arms_the_review(monkeypatch):
    monkeypatch.setattr(PS, "_git", _git_stub(
        ["aaa"], {"aaa": ["pipeline/scripts/rule_gate.py"]}))
    p = _plan()
    p["last_review_commit"] = "old"
    assert PS.commits_since_review(p) == 1
    assert PS.review_due(p)[0] is True


def test_a_commit_touching_the_plan_AND_code_still_counts(monkeypatch):
    # P0f's commits edited the plan alongside the code they closed. Those are
    # work, and exempting them would be the mute this fix exists to remove.
    monkeypatch.setattr(PS, "_git", _git_stub(
        ["aaa"], {"aaa": ["qa/deliverable-plan.json",
                          "pipeline/scripts/build_room.py"]}))
    p = _plan()
    p["last_review_commit"] = "old"
    assert PS.commits_since_review(p) == 1


def test_unreadable_file_list_is_unknown_not_zero(monkeypatch):
    # Same law as above: a commit whose contents git would not name must not be
    # silently counted as "not work".
    def g(*a):
        return "\n".join(["aaa"]) if a[0] == "rev-list" else None
    monkeypatch.setattr(PS, "_git", g)
    p = _plan()
    p["last_review_commit"] = "old"
    assert PS.commits_since_review(p) is None


# --- the report ----------------------------------------------------------------

def test_report_names_the_phase_the_exit_test_and_the_next_files():
    p = _plan()
    out = PS.report(p)
    assert "WE ARE AT   P0" in out
    assert "the standard fails our best frame" in out
    assert "a.py" in out and "DO NEXT" in out


def test_report_surfaces_owner_actions_without_blocking():
    p = _plan(standing_corrections=[
        {"id": "SC-3", "do": "five questions for the designer friend",
         "owner_action_required": True}])
    out = PS.report(p)
    assert "WAITING ON THE OWNER" in out and "does not block" in out


def test_check_exits_1_only_when_a_review_is_due(tmp_path, monkeypatch):
    monkeypatch.setattr(PS, "_git", lambda *a: None)
    f = tmp_path / "plan.json"
    p = _plan()
    f.write_text(json.dumps(p), encoding="utf-8")
    assert PS.main(["--plan", str(f), "--check"]) == 0
    p["phases"][0]["status"] = "done"
    f.write_text(json.dumps(p), encoding="utf-8")
    assert PS.main(["--plan", str(f), "--check"]) == 1


def test_review_without_verdicts_is_refused_at_the_cli(tmp_path):
    f = tmp_path / "plan.json"
    f.write_text(json.dumps(_plan()), encoding="utf-8")
    assert PS.main(["--plan", str(f), "--review"]) == 2


# --- and the real file ---------------------------------------------------------

def test_the_repos_own_plan_loads_and_reports():
    p = PS.load()
    assert p["unit"] == "DELIV-001"
    assert [x["id"] for x in p["phases"]] == ["P0", "P1", "P2", "P3", "P4", "P5"]
    out = PS.report(p)
    assert "WE ARE AT   P0" in out


def test_every_work_item_in_the_real_plan_names_a_file():
    """A work item with no `where` is a wish. The debt ledger's own closing rule
    is that fix_where must resolve; the plan holds itself to the same test."""
    for ph in PS.load()["phases"]:
        for w in ph["work"]:
            assert w.get("where"), f"{ph['id']}/{w['id']} names no file"


def test_every_phase_in_the_real_plan_has_an_exit_test_that_looks_at_something():
    for ph in PS.load()["phases"]:
        assert ph.get("exit_test"), f"{ph['id']} has no exit test"
        assert len(ph["exit_test"]) > 40, f"{ph['id']}'s exit test is too thin to fail"


# --- the plan's consumer must itself have a consumer -----------------------------

def test_the_render_gate_imports_plan_status():
    """scripts/reachability_check.py caught this file as a NEW unwired instrument
    minutes after it was written: its only consumer was a paragraph in CLAUDE.md
    telling a reader to run it. That is the defect the plan exists to name, so the
    wiring is pinned rather than trusted."""
    src = open(os.path.join(REPO, "pipeline", "scripts", "rule_gate.py"),
               encoding="utf-8").read()
    assert "import plan_status" in src
    assert "PLAN.next_work" in src and "PLAN.review_due" in src


def test_the_gate_does_not_BLOCK_on_an_overdue_review():
    """decisions_check blocks because a decision with no reversal is a defect in
    the frame's provenance. An overdue plan review is not — halting a render over
    owed paperwork is the enforcement clause R3 revoked, one level up."""
    src = open(os.path.join(REPO, "pipeline", "scripts", "rule_gate.py"),
               encoding="utf-8").read()
    tail = src[src.index("WHERE ARE WE IN THE PLAN"):]
    block = tail[:tail.index("if v and hard")]
    assert "REVIEW OVERDUE" in block
    assert "v.append" not in block and "raise SystemExit" not in block
