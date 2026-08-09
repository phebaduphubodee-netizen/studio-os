"""Tests for decisions_check — the log of what was decided in the owner's name.

These replace a suite written an hour earlier for the opposite design (a
blocking queue). Owner order 2026-08-08: "เอาผมออกจาก gate เลย ไม่ต้องรอผม". The
old tests asserted that an unanswered ask HALTS the lane; keeping any of them
would have kept the rung he removed, so `test_no_row_may_be_pending` is now the
test that would fail if the queue ever grew back.

The negative controls are the ways this log can lie, which are different from
the ways the queue could: a decision logged but not carried out, a decision with
no way back, and the builder signing his name.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decisions_check as DC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _row(**kw):
    d = {"id": "D-9", "unit": "TRN-002", "decided_round": 34,
         "decided_date": "2026-08-08", "decided_by": "builder",
         "question": "cap เท่าไร", "in_effect": "42/55",
         "where": "CLAUDE.md", "because": "เลนเพิ่งเจอความผิดใหญ่",
         "reverse_by": "สองตัวเลขใน caps json",
         "owner_override": None, "override_date": None}
    d.update(kw)
    return d


def _log(rows):
    return {"decisions": rows}


# --- the log has to exist ------------------------------------------------------

def test_no_log_is_itself_the_violation():
    v = DC.check(None, "TRN-002", REPO)
    assert len(v) == 1
    assert "no readable decision log" in v[0]


def test_malformed_json_loads_as_none_rather_than_raising(tmp_path):
    p = tmp_path / "d.json"
    p.write_text("{not json", encoding="utf-8")
    assert DC.load(str(p)) is None


def test_a_json_list_is_not_a_log(tmp_path):
    p = tmp_path / "d.json"
    p.write_text("[]", encoding="utf-8")
    assert DC.load(str(p)) is None


# --- 1. no row may be pending: the queue must not grow back --------------------

def test_a_clean_builder_decision_passes():
    assert DC.check(_log([_row()]), "TRN-002", REPO) == []


def test_no_row_may_be_pending():
    # THE test of the owner's order. If a future round reintroduces a waiting
    # state, this fails before the render that would have waited on it.
    v = DC.check(_log([_row(decided_by="pending")]), "TRN-002", REPO)
    assert any("there is no pending state" in s for s in v)
    assert any("ไม่ต้องรอผม" in s for s in v)


def test_a_null_decider_is_missing_not_merely_odd():
    v = DC.check(_log([_row(decided_by=None)]), "TRN-002", REPO)
    assert any("missing decided_by" in s for s in v)


def test_owner_is_a_legal_decider():
    row = _row(decided_by="owner", owner_override="เอาผมออกจาก gate",
               override_date="2026-08-08")
    assert DC.check(_log([row]), "TRN-002", REPO) == []


# --- 2. `where` must name a path that exists -----------------------------------

def test_a_decision_in_force_nowhere_was_never_taken():
    v = DC.check(_log([_row(where="qa/does-not-exist.json")]), "TRN-002", REPO)
    assert len(v) == 1
    assert "written down instead of taken" in v[0]


def test_where_may_name_several_files():
    row = _row(where="CLAUDE.md, docs/LICENSING.md")
    assert DC.check(_log([row]), "TRN-002", REPO) == []


def test_one_bad_path_among_several_is_still_caught():
    row = _row(where="CLAUDE.md, qa/nope.json")
    v = DC.check(_log([row]), "TRN-002", REPO)
    assert len(v) == 1 and "qa/nope.json" in v[0]


# --- 3. reversibility is the whole safety property now -------------------------

def test_a_decision_with_no_way_back_is_a_violation():
    v = DC.check(_log([_row(reverse_by="")]), "TRN-002", REPO)
    assert any("missing reverse_by" in s for s in v)


def test_a_decision_with_no_reasoning_is_a_violation():
    v = DC.check(_log([_row(because=None)]), "TRN-002", REPO)
    assert any("missing because" in s for s in v)


def test_a_decision_that_does_not_say_what_is_true_now_is_a_violation():
    v = DC.check(_log([_row(in_effect="")]), "TRN-002", REPO)
    assert any("missing in_effect" in s for s in v)


# --- 4. an owner-decided row is locked to him ----------------------------------

def test_the_builder_may_not_sign_the_owners_name():
    v = DC.check(_log([_row(decided_by="owner")]), "TRN-002", REPO)
    assert len(v) == 1
    assert "may not sign for him" in v[0]


def test_an_override_cannot_be_relabelled_as_the_builders_call():
    row = _row(decided_by="builder", owner_override="ไม่เอาแบบนี้",
               override_date="2026-08-08")
    v = DC.check(_log([row]), "TRN-002", REPO)
    assert any("the row is his" in s for s in v)


def test_an_override_with_no_date_cannot_be_told_from_a_backfill():
    row = _row(decided_by="owner", owner_override="ไม่เอา", override_date=None)
    v = DC.check(_log([row]), "TRN-002", REPO)
    assert any("back-fill" in s for s in v)


# --- unit isolation and ordering ------------------------------------------------

def test_a_closed_lanes_decisions_are_not_re_litigated():
    bad = _row(id="D-0", unit="TRN-001", where="qa/gone.json")
    assert DC.check(_log([bad]), "TRN-002", REPO) == []


def test_in_force_puts_owner_rulings_first_then_newest():
    rows = [_row(id="A", decided_round=10),
            _row(id="B", decided_round=34),
            _row(id="C", decided_round=5, decided_by="owner",
                 owner_override="x", override_date="d")]
    got = [d["id"] for d in DC.in_force(_log(rows), "TRN-002")]
    assert got == ["C", "B", "A"]


def test_one_line_names_the_reversal_because_that_is_the_safety_property():
    line = DC.one_line(_row())
    assert "42/55" in line and "สองตัวเลขใน caps json" in line


# --- the real file ---------------------------------------------------------------

def test_the_repos_own_log_parses_and_is_honest():
    data = DC.load(os.path.join(REPO, DC.DECISIONS_REL))
    assert data is not None, "the committed log must be readable"
    assert DC.check(data, "TRN-002", REPO) == []


def test_the_real_log_has_no_pending_row_anywhere():
    data = DC.load(os.path.join(REPO, DC.DECISIONS_REL))
    for d in DC.rows_for(data):
        assert d.get("decided_by") in DC.DECIDERS, \
            f"{d.get('id')} is waiting for somebody, which the owner abolished"


def test_the_owners_order_is_recorded_verbatim_on_the_row_it_created():
    data = DC.load(os.path.join(REPO, DC.DECISIONS_REL))
    rows = [d for d in DC.rows_for(data) if d.get("decided_by") == "owner"]
    assert rows, "the order that removed his rung must itself be an owner row"
    assert any("ไม่ต้องรอผม" in (d.get("owner_override") or "") for d in rows)


def test_every_real_row_is_serialisable_and_carries_the_override_scaffold():
    data = DC.load(os.path.join(REPO, DC.DECISIONS_REL))
    for d in DC.rows_for(data):
        for k in ("owner_override", "override_date"):
            assert k in d, f"{d.get('id')} cannot record an override"
        assert json.dumps(d, ensure_ascii=False)
