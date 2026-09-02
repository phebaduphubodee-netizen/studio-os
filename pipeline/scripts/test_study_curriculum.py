"""test_study_curriculum.py — the refusals of the daily-study checker, held.

WHY THESE TESTS EXIST, in his words (2026-09-01): "สิ่งที่ผมกลัวคือคุณชอบข้ามงาน
ในงาน (สรุปว่าเสร็จแล้ว เรียนเสร็จแล้ว ทำได้แล้ว แต่พอผมเป็นเช็คก็เจอว่ามันห่วย)".
`study_curriculum.check()` is the machine answer to that fear, so the thing that
must never rot is its ABILITY TO REFUSE. A guard proven once in a shell and never
again is the shape this repo keeps rebuilding: the rung that was declared
mandatory and then printed as a suggestion.

Every test below is a NEGATIVE CONTROL — it constructs the defect and asserts the
checker names it. The positive control is `test_live_ledger_is_clean`: the real
file must pass, or the refusals above are just noise nobody can act on.
"""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import study_curriculum as sc  # noqa: E402


@pytest.fixture()
def led():
    return sc.load()


def _unit(doc, uid):
    return next(u for u in doc["units"] if u["id"] == uid)


def _fenced(doc, n=0):
    return [u for u in doc["units"]
            if (u.get("fetch") or {}).get("fence_gate")][n]


def test_live_ledger_is_clean(led):
    """POSITIVE CONTROL: the shipped curriculum passes its own checker."""
    assert sc.check(led) == []


def test_builder_may_not_close_a_unit(led):
    bad = copy.deepcopy(led)
    u = _unit(bad, "STUDY-D11-madebed")
    u.update(status="done", judged_by="builder",
             exam_evidence="docs/blenderkit-study-2026-09-01.md")
    fails = sc.check(bad)
    assert any("may not grade the learner" in f for f in fails), fails


def test_done_with_no_judge_is_refused(led):
    bad = copy.deepcopy(led)
    u = _unit(bad, "STUDY-D11-madebed")
    u.update(status="done", exam_evidence="docs/blenderkit-study-2026-09-01.md")
    u.pop("judged_by", None)
    assert any("may not grade the learner" in f for f in sc.check(bad))


def test_done_needs_evidence_that_exists(led):
    bad = copy.deepcopy(led)
    u = _unit(bad, "STUDY-D12-curtains")
    u.update(status="done", judged_by="verifier-agent",
             exam_evidence="knowledge/_inbox/model-study/NOT-A-REAL-FILE.md")
    assert any("does not exist" in f for f in sc.check(bad))


def test_done_with_empty_evidence_is_refused(led):
    bad = copy.deepcopy(led)
    u = _unit(bad, "STUDY-D12-curtains")
    u.update(status="done", judged_by="verifier-agent", exam_evidence="")
    assert any("exam_evidence is empty" in f for f in sc.check(bad))


def test_a_unit_without_a_pre_registered_exam_is_refused(led):
    bad = copy.deepcopy(led)
    _unit(bad, "STUDY-D14-rug").pop("exam")
    assert any("no pre-registered exam" in f for f in sc.check(bad))


def test_practice_rep_cannot_be_closed_by_a_text_verifier(led):
    """A rep is judged on PIXELS; a fresh-context reader of JSON cannot see a
    render, so only c2/c3/owner may close one."""
    bad = copy.deepcopy(led)
    rep = next(u for u in bad["units"] if "-rep-" in u["id"])
    rep.update(status="done", judged_by="verifier-agent",
               exam_evidence="docs/blenderkit-study-2026-09-01.md")
    assert any("only c2/c3/owner" in f for f in sc.check(bad))


def test_practice_rep_closes_on_c2(led):
    bad = copy.deepcopy(led)
    rep = next(u for u in bad["units"] if "-rep-" in u["id"])
    rep.update(status="done", judged_by="c2",
               exam_evidence="docs/blenderkit-study-2026-09-01.md")
    assert not any(rep["id"] in f for f in sc.check(bad))


def test_fenced_unit_may_not_move_while_its_gate_is_open(led):
    """The p2r86 contamination, refused by name: a paid fetch in a class whose
    free baseline has not run."""
    bad = copy.deepcopy(led)
    _fenced(bad).update(status="in-progress")
    assert any("fenced by" in f for f in sc.check(bad))


def test_fence_pointing_at_nothing_is_refused(led):
    """R13's `obeyed_where` test applied to fences — a gate that names no unit
    can never open and reads exactly like a closed one."""
    bad = copy.deepcopy(led)
    _fenced(bad)["fetch"]["fence_gate"] = "STUDY-D99-does-not-exist"
    assert any("names no unit" in f for f in sc.check(bad))


def test_skip_needs_a_recorded_reason(led):
    bad = copy.deepcopy(led)
    _unit(bad, "STUDY-D15-seating")["status"] = "skipped"
    assert any("skipped without a recorded reason" in f for f in sc.check(bad))


def test_skipped_is_not_counted_as_studied(led):
    """A skip is a legitimate outcome; it is not a lesson. The session-open line
    must not let one read as the other."""
    bad = copy.deepcopy(led)
    u = _unit(bad, "STUDY-D15-seating")
    u.update(status="skipped", skip_reason="probe test")
    before = [l for l in sc.report_lines() if "เรียนแล้ว" in l][0]
    n_before = before.split("เรียนแล้ว ")[1].split("/")[0]

    import json
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(bad, f, ensure_ascii=False)
        line = [l for l in sc.report_lines(path=path) if "เรียนแล้ว" in l][0]
    finally:
        os.unlink(path)
    assert line.split("เรียนแล้ว ")[1].split("/")[0] == n_before
    assert "ข้ามโดยบันทึกเหตุ 1" in line


def test_unreadable_ledger_prints_unknown_not_zero():
    lines = sc.report_lines(path="qa/definitely-not-here.json")
    assert any("unknown" in l for l in lines)
    assert not any("เรียนแล้ว 0" in l for l in lines)


# --------------------------------------------------------------------------
# PACE UNCAPPED 2026-09-02 ("งั้นแก้แผนให้เรียนกี่เรื่องก็ได้ต่อวัน"). The calendar
# is gone; what replaces it is a queue plus one number that can go red. These
# tests hold that number's ability to go red — a burn rate that cannot fail is
# the same thing as the schedule it replaced.
# --------------------------------------------------------------------------
def _write(doc):
    import json
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False)
    return path


def test_pacing_declaration_missing_is_refused(led):
    """Without it the next session reads `suggested_date` and quietly goes back to
    one unit per day — R13: an order is a row, and a row that is absent is not obeyed."""
    bad = copy.deepcopy(led)
    bad["clock"].pop("pacing")
    assert any("any-number-per-day" in f for f in sc.check(bad))


def test_a_paid_unit_with_no_order_is_refused(led):
    bad = copy.deepcopy(led)
    u = next(u for u in bad["units"]
             if u.get("deadline") and u["status"] in sc.OPEN_STATUSES)
    u["order"] = None
    assert any(u["id"] in f and "cannot be queued" in f for f in sc.check(bad))


def test_burn_rate_goes_red_when_paid_units_outnumber_the_days_left(led):
    """NEGATIVE CONTROL for the one line that can fail: with more paid units open
    than days of access remaining, one-a-day no longer reaches the end and the
    reader must say so."""
    import datetime
    bad = copy.deepcopy(led)
    for u in bad["units"]:                       # every paid unit still to do
        if u.get("deadline"):
            u["status"] = "pending"
    near = datetime.date.fromisoformat(bad["clock"]["last_day"]) - datetime.timedelta(days=2)
    path = _write(bad)
    try:
        lines = sc.report_lines(path=path, today=near)
    finally:
        os.unlink(path)
    assert any("BURN RATE" in l for l in lines)
    assert any(l.startswith("  !!") and "ไปไม่ถึงแล้ว" in l for l in lines)


def test_burn_rate_stays_quiet_when_there_is_room(led):
    """POSITIVE CONTROL: the same line must NOT cry on the real file today, or it
    becomes noise and stops being read."""
    lines = sc.report_lines()
    assert any("BURN RATE" in l for l in lines)
    assert not any("ไปไม่ถึงแล้ว" in l for l in lines)


def test_the_queue_is_ordered_and_not_a_calendar(led):
    """`ถัดไป` must follow `order`, and must not depend on today's date."""
    import datetime
    a = sc.report_lines(today=datetime.date(2026, 9, 3))
    b = sc.report_lines(today=datetime.date(2026, 9, 10))
    nxt = lambda ls: [l for l in ls if l.strip().startswith("ถัดไป")]
    assert nxt(a) and nxt(a) == nxt(b), "the queue moved because the calendar moved"
    orders = [int(l.split("#")[1].split(":")[0]) for l in nxt(a)]
    assert orders == sorted(orders)
