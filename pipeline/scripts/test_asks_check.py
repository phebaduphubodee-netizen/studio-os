"""Tests for asks_check — the ledger that makes "it stopped being asked"
impossible to do quietly.

The negative controls are the twenty-one real ways an ask died in this repo: it
was abbreviated to a token nobody could answer, it was deleted from the file
that held it, it was marked closed on a ground that had since been cancelled, or
it simply stopped appearing in the gates. None of them was a refusal.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asks_check as AC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TODAY = datetime.date(2026, 8, 16)


def _ask(**kw):
    a = {"id": "ASK-x", "ask": "ซื้อผ้ามั้ย", "first_routed": "2026-08-01",
         "where": "CLAUDE.md", "status": "open", "money": "no"}
    a.update(kw)
    return a


def _led(rows, **kw):
    d = {"asks": rows}
    d.update(kw)
    return d


def test_no_ledger_is_itself_the_violation():
    v = AC.check(None, REPO)
    assert len(v) == 1 and "no readable ask ledger" in v[0]


def test_a_clean_open_ask_passes():
    assert AC.check(_led([_ask()]), REPO) == []


def test_there_is_no_fourth_state():
    v = AC.check(_led([_ask(status="deferred")]), REPO)
    assert any("no fourth state" in s for s in v)
    assert any("silence" in s for s in v)


def test_answered_without_his_words_is_the_builder_remembering_for_him():
    v = AC.check(_led([_ask(status="answered")]), REPO)
    assert any("His answer is the artefact" in s for s in v)


def test_withdrawn_without_a_reason_is_indistinguishable_from_dropped():
    v = AC.check(_led([_ask(status="withdrawn")]), REPO)
    assert any("Withdrawing is" in s for s in v)


def test_withdrawing_with_a_reason_is_allowed_and_often_right():
    a = _ask(status="withdrawn",
             withdrawn_reason="answered from the client's drawing instead")
    assert AC.check(_led([a]), REPO) == []


def test_an_ask_may_not_leave_the_file():
    # The r27 procurement ask, the floor2 queue, Q1/Q2: each simply stopped
    # appearing. The floor makes that a diff nobody can take by accident.
    v = AC.check(_led([_ask()], _count_floor=3), REPO)
    assert any("AN ASK DOES NOT LEAVE THIS FILE" in s for s in v)


def test_an_ask_routed_nowhere_was_never_made():
    v = AC.check(_led([_ask(where="qa/nope.json")]), REPO)
    assert any("never made" in s for s in v)


def test_an_ask_may_not_block_the_lane():
    v = AC.check(_led([_ask(blocking=True)]), REPO)
    assert any("ไม่ต้องรอผม" in s for s in v)


def test_age_is_computed_and_sorted_oldest_first():
    rows = [_ask(id="A", first_routed="2026-08-15"),
            _ask(id="B", first_routed="2026-07-01")]
    got = AC.open_asks(_led(rows), TODAY)
    assert [a["id"] for a, _ in got] == ["B", "A"]
    assert got[0][1] == 46


def test_an_unparseable_date_ages_as_unknown_not_as_zero():
    got = AC.open_asks(_led([_ask(first_routed="soon")]), TODAY)
    assert got[0][1] is None
    assert "?d" in AC.one_line(*got[0])


def test_the_gate_line_says_unknown_when_the_file_cannot_be_read():
    assert "unknown, not zero" in AC.gate_line(None)


def test_money_asks_are_counted_separately_because_only_he_can_clear_them():
    rows = [_ask(id="A", money="yes — $15"), _ask(id="B", money="no")]
    assert AC.tally(_led(rows), TODAY)["money"] == 1


# --- the real file ------------------------------------------------------------

def test_the_repos_own_ask_ledger_is_honest():
    data = AC.load(repo_root=REPO)
    assert data is not None
    assert AC.check(data, REPO) == []


def test_the_dropped_asks_this_session_found_are_all_in_it():
    """Twenty-one were measured. The ledger may grow; it may not shrink below
    what was found, which is what `_count_floor` pins."""
    data = AC.load(repo_root=REPO)
    assert len(AC.asks(data)) >= 21


def test_the_oldest_open_ask_is_the_paid_asset_tier():
    """46 days, and it is the one whose closure ground he cancelled himself."""
    data = AC.load(repo_root=REPO)
    oldest = AC.open_asks(data, TODAY)[0][0]
    assert oldest["id"] == "ASK-002"
    assert str(oldest["money"]).startswith("yes")
