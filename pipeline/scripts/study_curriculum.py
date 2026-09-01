#!/usr/bin/env python3
"""study_curriculum.py — reader of qa/blenderkit-study-curriculum.json, printed at
every session open by plan_status.

WHY A READER EXISTS (the repo's own arithmetic): a curriculum carried as a file
with no consumer is the queue-with-no-consumer defect — measured five times
before this file was written (357/22 critic items, 61/39 DR units, 21/2 gate
verdicts, the six 54-day skills, the 08-15 audit that was itself unconsumed).
ORD-2026-09-01-study-blenderkit-models is a DAILY program ("ผมจะสั่งให้คุณเรียน
ทุกวัน จนกว่าจะถึงวันหมด") against a hard clock (full-plan access ends
2026-09-21); a missed day must therefore PRINT as debt at session open, because
the money already spent does not come back for it.

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
            if not ev:
                fails.append(f"{u['id']}: done but exam_evidence is empty — "
                             "a study that landed nowhere was not done")
            else:
                for p in ev.split(","):
                    p = p.strip()
                    if p and ("/" in p or "\\" in p) and not os.path.exists(
                            os.path.join(REPO, p)):
                        fails.append(f"{u['id']}: exam_evidence {p} does not exist")
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
    todays = [u for u in units if u.get("date") == today.isoformat()]
    for u in todays:
        out.append(f"  วันนี้: {u['id']} — {u['title']} [{u.get('status')}]")
    debt = [u for u in units
            if u.get("status") in OPEN_STATUSES and u.get("date", "9999") < today.isoformat()]
    for u in debt:
        out.append(f"  !! ค้าง [{u['date']}] {u['id']} — {u['title'][:60]}")
    if not todays and days_left >= 0 and not debt:
        out.append("  (วันนี้ไม่มีหน่วยตามตาราง — ตารางอยู่ที่ qa/blenderkit-study-curriculum.json)")
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
