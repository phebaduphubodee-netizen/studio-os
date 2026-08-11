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
    the same law pixel_check's exit code 2 was written for.

    The scenario moved when the trigger did (2026-08-10). With NO review ever
    recorded, git is not consulted at all any more: the answer is every work item
    already marked done, which is determinate. The law still binds in the case
    where git IS the source — a plan that cannot be read at the last review."""
    monkeypatch.setattr(PS, "_git", lambda *a: None)
    p = _plan()
    p["last_review_commit"] = "old"
    for ph in p["phases"]:
        ph["_reviewed"] = True
    due, why = PS.review_due(p)
    assert due is False and "unknown" in why and "not zero" in why


def test_with_no_review_ever_recorded_closed_work_arms_it_without_git(monkeypatch):
    """And the other half: never-reviewed is not the same as unknown. Nothing
    needs to be read for it, so an unreadable git must not suppress it."""
    monkeypatch.setattr(PS, "_git", lambda *a: None)
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "done"
    due, why = PS.review_due(p)
    assert due and p["phases"][0]["work"][0]["id"] in why


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


def test_a_code_commit_still_counts_as_a_commit(monkeypatch):
    monkeypatch.setattr(PS, "_git", _git_stub(
        ["aaa"], {"aaa": ["pipeline/scripts/rule_gate.py"]}))
    p = _plan()
    p["last_review_commit"] = "old"
    assert PS.commits_since_review(p) == 1


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


# --- the SECOND instance of the self-re-arming review ---------------------------
# The path-based fix above held for exactly one round. The review that followed it
# committed the plan AND its gate artifact, and re-armed on the round that had just
# been done — because the rule was stated in terms of WHICH FILES a commit touched,
# and a rule that names the files it applies to always misses the next file. The
# trigger is now the plan's own record of what closed, diffed against git.

def _plan_stub(before):
    """git that answers `show <rev>:<plan>` with a plan snapshot."""
    def g(*a):
        if a[0] == "show" and str(a[-1]).endswith("qa/deliverable-plan.json"):
            return None if before is None else json.dumps(before)
        return None
    return g


def test_the_review_that_wrote_itself_down_does_not_arm_the_next_one(monkeypatch):
    p = _plan()
    for ph in p["phases"]:
        ph["_reviewed"] = True
    p["last_review_commit"] = "old"
    monkeypatch.setattr(PS, "_git", _plan_stub(p))       # nothing closed since
    assert PS.work_closed_since_review(p) == []
    assert PS.review_due(p)[0] is False


def test_a_work_item_closing_arms_the_review_and_is_named(monkeypatch):
    before = _plan()
    after = json.loads(json.dumps(before))
    for ph in after["phases"]:
        ph["_reviewed"] = True
    after["last_review_commit"] = "old"
    ph0 = after["phases"][0]
    ph0["work"][0]["status"] = "done"
    monkeypatch.setattr(PS, "_git", _plan_stub(before))
    closed = PS.work_closed_since_review(after)
    assert closed == [f"{ph0['id']}/{ph0['work'][0]['id']}"]
    due, why = PS.review_due(after)
    assert due and closed[0] in why, "the trigger must name what closed"


def test_an_unreadable_previous_plan_is_unknown_not_nothing_closed(monkeypatch):
    p = _plan()
    for ph in p["phases"]:
        ph["_reviewed"] = True
    p["last_review_commit"] = "old"
    monkeypatch.setattr(PS, "_git", _plan_stub(None))
    assert PS.work_closed_since_review(p) is None
    assert "unknown" in PS.review_due(p)[1]


def test_a_closed_phase_still_arms_regardless_of_work_items(monkeypatch):
    p = _plan()
    p["phases"][0]["status"] = "done"
    p["last_review_commit"] = "old"
    monkeypatch.setattr(PS, "_git", _plan_stub(p))
    assert PS.review_due(p)[0] is True


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
    """It asserted `WE ARE AT   P0` and broke the day P0 closed — a test pinned to
    a SNAPSHOT of the lane rather than to the report's contract, so the only way to
    keep it green is to edit it every time work lands. Pin the invariant instead:
    the header names whichever phase `current` resolves to."""
    p = PS.load()
    assert p["unit"] == "DELIV-001"
    ids = [x["id"] for x in p["phases"]]
    # P0..P5 is the spine and its ORDER is the invariant; the plan may grow
    # named programs after it (DRW, 2026-08-11 owner order) — an exact-list
    # assert here was this test's own docstring defect one line down.
    assert ids[:6] == ["P0", "P1", "P2", "P3", "P4", "P5"]
    out = PS.report(p)
    cur = PS.current(p)
    assert f"WE ARE AT   {cur['id']}" in out and cur["id"] in ids


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


# --- a status the machine cannot read ---------------------------------------------
# Written after inventing `part-done` on a work item that had genuinely half landed.
# The review trigger counts items that became `done`, so an unknown status is a row
# that can hold real work and never arm the ritual meant to follow it.

def test_an_unknown_status_is_named_not_tolerated():
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "part-done"
    bad = PS.unreadable_statuses(p)
    assert bad and bad[0][1] == "part-done"
    out = PS.report(p)
    assert "part-done" in out and "split it" in out


def test_the_real_plan_uses_only_statuses_the_machine_can_read():
    assert PS.unreadable_statuses(PS.load()) == []


def test_a_clean_plan_prints_no_status_warning():
    assert PS.unreadable_statuses(_plan()) == []
    assert "does not name" not in PS.report(_plan())


# --- the review's own record answers "what has closed since" ----------------------
# Stamping HEAD had an ordering flaw no git-based version escapes: record_review runs
# BEFORE the commit carrying the closures that triggered it, so the plan at that
# commit lacks them and the next run counts them again — the self-re-arming review a
# third time, one level down.

def test_the_review_records_what_was_closed_at_the_time():
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "done"
    PS.record_review(p, {"P0": "keep: a", "P1": "keep: b"}, commit="abc")
    assert p["reviews"][-1]["done_at_review"] == ["P0/P0a"]


def test_closures_in_the_same_commit_as_the_review_do_not_re_arm_it(monkeypatch):
    monkeypatch.setattr(PS, "_git", lambda *a: None)   # git must not be consulted
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "done"
    PS.record_review(p, {"P0": "keep: a", "P1": "keep: b"}, commit="abc")
    for ph in p["phases"]:
        ph["_reviewed"] = True
    assert PS.work_closed_since_review(p) == []
    assert PS.review_due(p)[0] is False


def test_the_next_closure_arms_it_again(monkeypatch):
    monkeypatch.setattr(PS, "_git", lambda *a: None)
    p = _plan()
    p["phases"][0]["work"][0]["status"] = "done"
    PS.record_review(p, {"P0": "keep: a", "P1": "keep: b"}, commit="abc")
    for ph in p["phases"]:
        ph["_reviewed"] = True
    p["phases"][0]["work"][1]["status"] = "done"
    assert PS.work_closed_since_review(p) == ["P0/P0b"]
    assert PS.review_due(p)[0] is True


def test_git_output_is_decoded_as_utf8_not_the_locale_codec():
    """The plan of record is written in Thai. `text=True` decodes with the LOCALE
    codec — cp1252 here — so `git show <rev>:<plan>` raised inside subprocess's
    reader thread and _git returned None for every call touching real content. It
    failed safe and never worked."""
    import inspect
    code = [ln for ln in inspect.getsource(PS._git).splitlines()
            if "subprocess.run" in ln or "decode(" in ln or "stdout" in ln]
    assert not any("text=True" in ln for ln in code),         "the locale codec cannot read this repo's own data"
    assert any('decode("utf-8"' in ln for ln in code)
    # and the behaviour, on the actual Thai file that broke it
    assert PS._git("show", f"HEAD:{PS.PLAN_REL}") is not None
