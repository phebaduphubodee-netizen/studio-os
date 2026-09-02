#!/usr/bin/env python3
"""study_curriculum.py — reader of qa/blenderkit-study-curriculum.json, printed at
every session open by plan_status.

WHY A READER EXISTS (the repo's own arithmetic): a curriculum carried as a file
with no consumer is the queue-with-no-consumer defect — measured five times
before this file was written (357/22 critic items, 61/39 DR units, 21/2 gate
verdicts, the six 54-day skills, the 08-15 audit that was itself unconsumed).
ORD-2026-09-01-study-blenderkit-models is a DAILY program ("ผมจะสั่งให้คุณเรียน
ทุกวัน จนกว่าจะถึงวันหมด") against a hard clock (full-plan access ends
2026-09-21).

PACE AMENDED 2026-09-02 ("งั้นแก้แผนให้เรียนกี่เรื่องก็ได้ต่อวัน"): the daily-ness
stands, the RATE is uncapped. What the one-per-day calendar was doing wrong is worth
keeping written down, because the shape recurs: it bundled a PERISHABLE step (the paid
fetch, which dies with the subscription) with a PERMANENT one (the note and its
opposing verification, which runs off 1.3 MB of probe dumps forever), so the
subscription was being spent at the speed of note-writing — and the last paid unit sat
on the expiry date itself with zero slack.

So this reader no longer asks "what was scheduled for today". `order` is a priority,
`deadline` is real and only paid units carry one, and the line that can FAIL is the
BURN RATE: paid units still open against days of access left. A calendar that nobody
can miss is not a schedule; a burn rate that goes red is.

Advisory only — learning never blocks a frame (same law as video_curriculum).
Unreadable prints UNKNOWN, never nothing, never zero.
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(REPO, "qa", "blenderkit-study-curriculum.json")

OPEN_STATUSES = ("pending", "in-progress", "blocked")
DONE_STATUSES = ("done", "skipped")  # skipped needs a recorded reason to count


def load(path=LEDGER):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clock_day(led, today=None):
    first = datetime.date.fromisoformat(led["clock"]["first_paid"])
    today = today or datetime.date.today()
    # same arithmetic as blenderkit.py status ("day 10 of 30" on 2026-09-01)
    return (today - first).days, today


# DONE IS NOT THE LEARNER'S SENTENCE (owner, 2026-09-01: "สิ่งที่ผมกลัวคือคุณชอบ
# ข้ามงานในงาน (สรุปว่าเสร็จแล้ว เรียนเสร็จแล้ว ทำได้แล้ว แต่พอผมเป็นเช็คก็เจอว่ามันห่วย)"
# — and the repo has already measured him right: builders catch 30-50% of their own
# defects (R3), the builder's eye went 0-for-367 as a judge (R7d), and a gate once
# wrote "มีลิ้นชัก+มือจับ" over pixels that held neither). So `done` here is a claim
# the checker refuses unless somebody who is not the learner signed it.
ALLOWED_JUDGES = ("verifier-agent", "instrument", "c2", "c3", "owner")
REP_JUDGES = ("c2", "c3", "owner")  # a practice rep is an exam; fresh-context
                                    # text-verifiers cannot see a render


def check(led):
    """Row-level defects, R13-style. A unit may not close on the learner's own word:
    done requires the pre-registered exam, evidence paths that exist, and a judge
    that is not 'builder' — rep units only close on c2/c3/owner."""
    fails = []
    units = led.get("units", [])
    all_ids = {u["id"] for u in units}
    done_ids = {u["id"] for u in units if u.get("status") in DONE_STATUSES}
    for u in units:
        if u.get("status") == "skipped" and not u.get("skip_reason"):
            fails.append(f"{u['id']}: skipped without a recorded reason")
        # the fence must have a reader (critic gap, 2026-09-01): a fenced unit
        # that moves while its gate unit is not done is a violation BY NAME.
        gate = (u.get("fetch") or {}).get("fence_gate")
        if gate and gate not in all_ids:
            # a fence pointing at a unit that does not exist can never open,
            # and reads exactly like a closed one — R13's `obeyed_where` test
            # applied to fences: a gate that names nothing was never a gate
            fails.append(f"{u['id']}: fence_gate {gate!r} names no unit in this "
                         "file — a fence nothing can open is not a fence")
        elif gate and gate not in done_ids and u.get("status") not in (
                "pending", "blocked"):
            fails.append(f"{u['id']}: fenced by {gate} which is not done — "
                         "a paid fetch behind an open fence is the p2r86 "
                         "contamination again; the unit may not move")
        if not u.get("exam"):
            fails.append(f"{u['id']}: no pre-registered exam — เฉลยต้องล็อกก่อนวัด "
                         "(harness-audit law); a unit with no exam can only be "
                         "closed by taste, which is the thing he said he fears")
        if u.get("status") == "done":
            judge = (u.get("judged_by") or "").strip().lower()
            if judge in ("", "builder", "self", "me"):
                fails.append(f"{u['id']}: done with judged_by={judge!r} — "
                             "the learner may not grade the learner (his words, "
                             "2026-09-01); name one of "
                             f"{'/'.join(ALLOWED_JUDGES)}")
            elif judge not in ALLOWED_JUDGES:
                fails.append(f"{u['id']}: judged_by={judge!r} is not a judge this "
                             f"file names ({'/'.join(ALLOWED_JUDGES)})")
            if "-rep-" in u["id"] and judge not in REP_JUDGES:
                fails.append(f"{u['id']}: a practice rep is an exam — only "
                             f"{'/'.join(REP_JUDGES)} may close it, got {judge!r}")
            ev = u.get("exam_evidence") or ""
            # the file's convention is ONE comma-separated string. A list is the shape a
            # writer reaches for first and it used to reach `.split` and raise, taking
            # session open down with a traceback — a type error must be a NAMED refusal.
            if isinstance(ev, (list, tuple)):
                fails.append(f"{u['id']}: exam_evidence is a {type(ev).__name__}; this "
                             "file stores it as one comma-separated string — join it")
                ev = ",".join(str(x) for x in ev)
            elif not isinstance(ev, str):
                fails.append(f"{u['id']}: exam_evidence is a {type(ev).__name__}, "
                             "not a comma-separated string")
                ev = ""
            if not ev:
                fails.append(f"{u['id']}: done but exam_evidence is empty — "
                             "a study that landed nowhere was not done")
            else:
                for p in ev.split(","):
                    p = p.strip()
                    if p and ("/" in p or "\\" in p) and not os.path.exists(
                            os.path.join(REPO, p)):
                        fails.append(f"{u['id']}: exam_evidence {p} does not exist")
    # the pace is an ORDER (R13: an order is a row, not a sentence), so its absence
    # from the file is a defect rather than a default — without this the next session
    # reads a `suggested_date` column and quietly goes back to one unit per day.
    pace = (led.get("clock") or {}).get("pacing") or {}
    if pace.get("rule") != "any-number-per-day":
        fails.append("clock.pacing.rule is not 'any-number-per-day' — the owner "
                     "uncapped the rate on 2026-09-02 ('งั้นแก้แผนให้เรียนกี่เรื่องก็ได้ต่อวัน'); "
                     "a file that does not say so will be read as a one-per-day calendar again")
    for u in led.get("units", []):
        if u.get("status") in OPEN_STATUSES and u.get("deadline") and not u.get("order"):
            fails.append(f"{u['id']}: carries a paid deadline but no order — it cannot be "
                         "queued, and an unqueued paid unit is the one that gets left behind")
    return fails


def report_lines(path=LEDGER, today=None):
    try:
        led = load(path)
    except Exception as e:
        return ["", f"BLENDERKIT STUDY unknown — {os.path.relpath(path, REPO)} could not "
                    f"be read ({e.__class__.__name__}). That is unknown, not zero."]
    day, today = clock_day(led, today)
    units = led.get("units", [])
    # STUDIED and SKIPPED are counted apart, and it is not cosmetic: a single
    # "done" count that swallows skips reads as more learning than happened —
    # the same shape as the coverage manifest that passed an object because it
    # was DECLARED rather than built (R11). A skip is a legitimate outcome; it
    # is not a lesson.
    studied = sum(1 for u in units if u.get("status") == "done")
    skipped = sum(1 for u in units if u.get("status") == "skipped")
    last = datetime.date.fromisoformat(led["clock"]["last_day"])
    days_left = (last - today).days
    head = (f"BLENDERKIT STUDY (ORD-2026-09-01) วัน {day} ของ 30 — เรียนแล้ว "
            f"{studied}/{len(units)} หน่วย")
    if skipped:
        head += f" · ข้ามโดยบันทึกเหตุ {skipped}"
    out = ["", head + f" · สิทธิ์ full-plan เหลือ {max(days_left, 0)} วัน"]
    # NEXT UP by priority, not by date — any number of these may be taken today
    pend = sorted((u for u in units if u.get("status") in OPEN_STATUSES),
                  key=lambda u: (u.get("order") or 999, u["id"]))
    done_ids = {u["id"] for u in units if u.get("status") in DONE_STATUSES}
    for u in pend[:4]:
        gate = (u.get("fetch") or {}).get("fence_gate")
        tag = "  [ต้องจ่าย]" if u.get("deadline") else ""
        if gate and gate not in done_ids:
            tag += f"  [ยังติด fence {gate}]"
        out.append(f"  ถัดไป #{u.get('order')}: {u['id']} — {u['title'][:52]}{tag}")
    if len(pend) > 4:
        out.append(f"  … อีก {len(pend) - 4} หน่วยในคิว (qa/blenderkit-study-curriculum.json)")

    # THE LINE THAT CAN FAIL. Free units keep forever; paid ones die with the
    # subscription, so this is the only number that carries a real deadline.
    paid_open = [u for u in units if u.get("deadline") and u.get("status") in OPEN_STATUSES]
    if paid_open:
        out.append(f"  BURN RATE: หน่วยที่ต้องใช้สิทธิ์และยังไม่ปิด {len(paid_open)} · "
                   f"เหลือ {max(days_left, 0)} วัน · ต้องปิดเฉลี่ย "
                   f"{len(paid_open) / max(days_left, 1):.1f} หน่วย/วัน")
        if len(paid_open) > max(days_left, 0):
            out.append(f"  !! หน่วยที่ต้องจ่าย {len(paid_open)} > วันที่เหลือ {max(days_left, 0)} — "
                       f"อัตราหนึ่งหน่วยต่อวันไปไม่ถึงแล้ว ต้องรวบ fetch ของหลายหน่วยในวันเดียว "
                       f"(ครึ่งที่หมดอายุคือการดึง ไม่ใช่การเขียนโน้ต)")
    if days_left < 0:
        open_left = [u for u in units if u.get("status") in OPEN_STATUSES]
        out.append(f"  สิทธิ์หมดแล้ว ({led['clock']['last_day']}) — หน่วยที่ไม่จบ "
                   f"{len(open_left)} หน่วยเป็นบันทึก ไม่ใช่หนี้ที่ตามได้อีก")
    for debt in led.get("_lane_debts", []):
        out.append(f"  !! lane debt: {debt[:150]}")
    for f in check(led):
        out.append(f"  !! {f}")
    return out


def main(argv=None):
    for line in report_lines():
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
