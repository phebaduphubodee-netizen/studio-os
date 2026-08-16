#!/usr/bin/env python3
"""AN ASK MAY NOT SIMPLY STOP BEING ASKED — `qa/owner-asks.json`, the outbound
half of the channel `orders_check` holds the inbound half of.

THE COUNT THAT PRODUCED IT (2026-08-16, fan-out over the gate artifacts, the
plan, the decision register and docs/): TWENTY-ONE questions were routed to the
owner and then dropped. Not refused — dropped. The shapes repeat:

  * `owner_questions_carried_forward` in scene-graph.json: a machine-readable
    owner queue with ZERO readers anywhere in the repo.
  * `floor2-owner-decision-queue.md`: a file whose only purpose is to hold five
    of his questions, untouched for 36 days, read by nothing.
  * The r19 pair, restated in eight consecutive gates as the bare tokens
    "Q1 · Q2" until the questions themselves were no longer written down
    anywhere — an ask abbreviated past the point where it could be answered.
  * The procurement ask of r27: restated eight times, then zero from r33. The
    repo's own audit found this one and wrote the sentence exactly — "It was
    not answered and not withdrawn; it stopped being asked" — and that audit was
    a DOCUMENT, so nothing consumed it and four more rounds dropped four more.
  * The blind RANK sheet: REMOVED as a finish-line condition at r34 for having
    gone unanswered. It was the only condition that looked at the picture, and
    four rounds later he said the frame was nowhere near done.

THREE STATES AND NO FOURTH: open / answered (his words + the date) / withdrawn
(with a reason, by the builder, who is allowed to decide an ask is not worth his
attention — but must say so). Silence is not a state.

NOTHING HERE BLOCKS ANYTHING. R3, 2026-08-08: "เอาผมออกจาก gate เลย ไม่ต้องรอผม".
He reads renders, so this ledger PRINTS in the render path and at session open
with each ask's AGE IN DAYS, and the age is the metric because the failure was
never his silence — it was ours.

LAYER LAW: pure Python, no `bpy`, no PIL, no network.
"""

import argparse
import datetime
import json
import os
import sys

ASKS_REL = "qa/owner-asks.json"
STATES = ("open", "answered", "withdrawn")
REQUIRED = ("id", "ask", "first_routed", "where", "status")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def load(path=None, repo_root=None):
    p = path or os.path.join(repo_root or _repo_root(), ASKS_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def asks(data):
    rows = (data or {}).get("asks")
    return [a for a in rows if isinstance(a, dict)] if isinstance(rows, list) else []


def _age(a, today):
    try:
        return (today - datetime.date.fromisoformat(str(a.get("first_routed")))).days
    except (ValueError, TypeError):
        return None


def open_asks(data, today=None):
    """[(ask, age_days)] oldest first."""
    today = today or datetime.date.today()
    out = [(a, _age(a, today)) for a in asks(data) if a.get("status") == "open"]
    return sorted(out, key=lambda r: -(r[1] if r[1] is not None else 0))


def check(data, repo_root=None, path_hint=ASKS_REL):
    """Violations — all on the builder's side. An ask he has not answered is
    never one of them."""
    if data is None:
        return [f"no readable ask ledger at {path_hint}. Twenty-one asks were "
                f"dropped while this file did not exist; losing it puts the "
                f"count back to zero and the dropping back to invisible."]
    root = repo_root or _repo_root()
    rows = asks(data)
    v, seen = [], set()

    floor = data.get("_count_floor")
    if isinstance(floor, int) and len(rows) < floor:
        v.append(f"the ask ledger holds {len(rows)} rows against a floor of "
                 f"{floor}. AN ASK DOES NOT LEAVE THIS FILE — it is answered or "
                 f"withdrawn with a reason, and the row stays. Deleting one is "
                 f"the exact motion this ledger exists to make impossible.")

    for a in rows:
        aid = a.get("id") or "<no id>"
        if aid in seen:
            v.append(f"{aid}: duplicate ask id.")
        seen.add(aid)

        missing = [k for k in REQUIRED if not a.get(k)]
        if missing:
            v.append(f"{aid}: ask row is missing {', '.join(missing)}.")
            continue

        st = a.get("status")
        if st not in STATES:
            v.append(f"{aid}: status {st!r} is not one of {', '.join(STATES)}. "
                     f"There is no fourth state, because the fourth state is "
                     f"silence and silence is what this file replaces.")
        if st == "answered" and not (a.get("answer") and a.get("answered_date")):
            v.append(f"{aid} is marked answered with no `answer` text or no "
                     f"`answered_date`. His answer is the artefact; a status "
                     f"without it is the builder remembering on his behalf.")
        if st == "withdrawn" and not a.get("withdrawn_reason"):
            v.append(f"{aid} is withdrawn with no reason. Withdrawing is "
                     f"allowed and often right — dropping is not, and without a "
                     f"reason the two are indistinguishable.")

        # R10's test, applied to an ask: point at where it was routed.
        for rel in str(a.get("where") or "").split(","):
            rel = rel.strip()
            if rel and not os.path.exists(os.path.join(root, rel)):
                v.append(f"{aid}: `where` names {rel}, which does not exist. An "
                         f"ask routed nowhere was never made.")

        if a.get("blocking"):
            v.append(f"{aid} claims to block the lane. Nothing waits for him — "
                     f"\"ไม่ต้องรอผม\" (2026-08-08). An ask that halts a render "
                     f"is the rung he abolished, growing back.")
    return v


def one_line(a, age):
    aged = f"{age:>3}d" if age is not None else "  ?d"
    money = "  [เงิน]" if str(a.get("money", "")).startswith("yes") else ""
    return f"  {a.get('id')} [{aged}]{money} {str(a.get('ask'))[:150]}"


def tally(data, today=None):
    rows = asks(data)
    op = [a for a in rows if a.get("status") == "open"]
    ages = [x for x in (_age(a, today or datetime.date.today()) for a in op)
            if x is not None]
    return {"open": len(op),
            "answered": sum(1 for a in rows if a.get("status") == "answered"),
            "withdrawn": sum(1 for a in rows if a.get("status") == "withdrawn"),
            "oldest": max(ages) if ages else 0,
            "money": sum(1 for a in op if str(a.get("money", "")).startswith("yes"))}


def gate_line(data, today=None):
    if data is None:
        return ("ASKS: qa/owner-asks.json could not be read — that is unknown, "
                "not zero.")
    t = tally(data, today)
    return (f"ASKS ที่ยังค้างพี่อยู่: {t['open']} ข้อ "
            f"({t['money']} ข้อเป็นเรื่องเงิน) · เก่าสุด {t['oldest']} วัน · "
            f"ตอบแล้ว {t['answered']} · ถอนแล้ว {t['withdrawn']} — "
            f"ไม่มีข้อไหนบล็อกเลนอยู่")


def main():
    ap = argparse.ArgumentParser(
        description="What I asked him, how old it is, and whether anything was "
                    "dropped rather than answered or withdrawn.")
    ap.add_argument("--file", default=None)
    ap.add_argument("--all", action="store_true", help="answered/withdrawn too")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                   # pragma: no cover
        pass
    data = load(a.file)
    print(gate_line(data))
    for row, age in open_asks(data):
        print(one_line(row, age))
    if a.all:
        for row in asks(data):
            if row.get("status") != "open":
                print(f"  {row.get('id')} [{row.get('status').upper()}] "
                      f"{str(row.get('ask'))[:110]}")
                print(f"      {row.get('withdrawn_reason') or row.get('answer')}")
    for s in check(data, a.file and os.path.dirname(a.file) or None):
        print(f"  !! {s}")
    return 1 if check(data) else 0


if __name__ == "__main__":
    sys.exit(main())
