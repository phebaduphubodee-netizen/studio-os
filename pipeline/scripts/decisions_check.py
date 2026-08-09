#!/usr/bin/env python3
"""The decision LOG — what the builder decided in the owner's name, and how to
undo each one. Nothing here waits for anybody.

OWNER ORDER 2026-08-08, which this file exists to obey rather than to soften:

    "เอาผมออกจาก gate เลย ไม่ต้องรอผม
     สุดท้ายทุกขั้นตอนที่ render ออกมาผมก็นั่งดูทุกรูปตลอดอยู่แล้ว"

An hour before it, this module was the opposite thing: a queue of pending
questions that FAILED THE NEXT RENDER if he had not answered within a round. It
was built off a real count — 21 gate artifacts, 2 with a recorded verdict, 19
without, and not one of the 19 ever stopping the lane — and off a diagnosis that
was only half right.

THE HALF I HAD: the closing phrase `พร้อมให้ตัดสิน` sat where a question belongs,
so the ask felt already made.

THE HALF HIS SENTENCE SUPPLIED, which is the load-bearing one: **he reads
RENDERS, not documents.** The nineteen unanswered gates were never nineteen acts
of ignoring me. They were nineteen asks filed in a channel he does not use.
Building a blocker on top of that would have halted the lane over a message he
was never going to see — the defect made mandatory. A queue whose consumer never
visits it does not become correct by acquiring an enforcement clause.

So the rung is gone. The owner is not a step; he overrules from the image,
whenever he likes, and the lane never waits. What remains is the thing that
actually protects him, now that nothing pauses for his signature:

    EVERY DECISION MADE IN HIS NAME IS WRITTEN DOWN BEFORE THE RENDER THAT
    DEPENDS ON IT, SAYS WHAT IS TRUE IN THE REPO BECAUSE OF IT, AND NAMES THE
    ONE EDIT THAT UNDOES IT.

Four rules, each enforcing a clause of that sentence:

  1. NO ROW MAY BE PENDING.        `decided_by` is "builder" or "owner". There
                                   is no third value, because a third value is
                                   a queue, and a queue is what he just
                                   abolished. If I opened it, I decided it.

  2. `where` MUST NAME A PATH      A decision "in effect" nowhere is a decision
     THAT EXISTS.                  that was never made. This is R10's test —
                                   point at it or it does not exist — applied
                                   to decisions instead of to masses, and it is
                                   the only check here that can catch me
                                   writing a resolution I did not carry out.

  3. `reverse_by` IS REQUIRED.     With no blocking rung, reversibility is the
                                   entire safety property. A decision I cannot
                                   describe undoing in one line is a decision I
                                   have not understood.

  4. AN OWNER-DECIDED ROW IS       Once `owner_override` carries his words,
     LOCKED TO HIM.                `decided_by` must read "owner". Re-deciding
                                   it means deleting what he said, in a diff.

WHAT THIS COSTS, stated because it should not have to be rediscovered: R3's
reason for existing was that builders catch only 30-50% of their own defects,
and the owner's rung was the answer to that. Removing it does not remove the
statistic. The load moves onto C2 (fresh-context local) and C3 (Gemini), which
are now the only rungs between a defect and a delivered frame — so a round that
skips them is no longer cutting a corner, it is running with nothing.

NOT PREVENTION, VISIBILITY, and now more so: nothing pauses for a signature, so
the whole control is that these rows print in the render path — his channel —
every single time. A row nobody surfaces is the silence this replaced.

LAYER LAW: pure Python, no `bpy`.
CLI-ONLY: no importer outside `rule_gate.py` and this module's tests.
"""

import argparse
import json
import os
import sys

DECISIONS_REL = "qa/open-decisions.json"

REQUIRED = ("id", "unit", "decided_round", "decided_date", "decided_by",
            "question", "in_effect", "where", "because", "reverse_by")

DECIDERS = ("builder", "owner")


def load(path=None, repo_root=None):
    """The log, or None. Never raises — a malformed log in the render path must
    produce a violation that NAMES the file, not a traceback. A crash reads as a
    broken tool and gets worked around; a violation gets fixed."""
    p = path or os.path.join(repo_root or ".", DECISIONS_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def rows_for(data, unit=None):
    """Decision rows, optionally filtered to one unit. TRN-001 closed at round
    20; its decisions are history and must not be re-litigated by a live lane."""
    rows = data.get("decisions") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    out = [d for d in rows if isinstance(d, dict)]
    if unit is not None:
        out = [d for d in out if d.get("unit") == unit]
    return out


def _paths(where):
    """`where` may name more than one file — a cap lives in one place, a licence
    call in two. Split on comma so the existence check reaches all of them."""
    if not isinstance(where, str):
        return []
    return [p.strip() for p in where.split(",") if p.strip()]


def check(data, unit, repo_root=None, path_hint=DECISIONS_REL):
    """Violations for `unit`. Empty means every decision taken in the owner's
    name is written down, in force somewhere real, and reversible."""
    if data is None:
        return [f"no readable decision log at {path_hint}. With the owner out "
                f"of the gate (2026-08-08) this file is the ONLY record of what "
                f"was decided in his name — losing it does not make the "
                f"decisions go away, it makes them invisible."]

    root = repo_root or os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    v = []

    for d in rows_for(data, unit):
        did = d.get("id") or "<no id>"

        missing = [k for k in REQUIRED if d.get(k) in (None, "", [], {})]
        if missing:
            v.append(f"{did}: decision log row is missing "
                     f"{', '.join(missing)}. Nothing waits for the owner now, "
                     f"so the written record is the whole of his protection.")

        by = d.get("decided_by")
        if by is not None and by not in DECIDERS:
            v.append(f"{did}: `decided_by` is '{by}'. It must be "
                     f"{' or '.join(DECIDERS)} — there is no pending state, "
                     f"because a pending state is a queue and the owner "
                     f"abolished the queue: \"ไม่ต้องรอผม\".")

        # R10's test, applied to a decision instead of a mass: point at where it
        # is in force, or it was never made. This is the one check here that can
        # catch the builder logging a resolution it did not carry out.
        for p in _paths(d.get("where")):
            if not os.path.exists(os.path.join(root, p)):
                v.append(f"{did}: `where` names {p}, which does not exist. A "
                         f"decision in effect nowhere is a decision that was "
                         f"written down instead of taken.")

        if d.get("owner_override"):
            if by != "owner":
                v.append(f"{did} carries the owner's own words but is marked "
                         f"decided_by='{by}'. Once he has ruled, the row is "
                         f"his; re-deciding it means deleting what he said.")
            if not d.get("override_date"):
                v.append(f"{did} is owner-overridden with no `override_date`, "
                         f"so nothing can tell a ruling from a back-fill.")
        elif by == "owner":
            v.append(f"{did} claims decided_by='owner' with no "
                     f"`owner_override` text. The builder may not sign for him "
                     f"— that is the one thing removing his rung did NOT change.")
    return v


def in_force(data, unit=None):
    """Rows in force, owner rulings first, then newest. This is what prints in
    the render path — the owner's actual channel, per his 2026-08-08 order."""
    rows = rows_for(data, unit)
    return sorted(rows, key=lambda d: (not d.get("owner_override"),
                                       -(d.get("decided_round") or 0)))


def one_line(d):
    who = "OWNER" if d.get("owner_override") else "ผมตัดสิน"
    return (f"  {d.get('id')} [{who} r{d.get('decided_round')}] "
            f"{d.get('in_effect')}  ← กลับทาง: {d.get('reverse_by')}")


def main():
    ap = argparse.ArgumentParser(
        description="Print what was decided in the owner's name, and how to "
                    "undo each one. Exits 1 if the log is dishonest.")
    ap.add_argument("--unit", default=None, help="e.g. TRN-002")
    ap.add_argument("--file", default=None)
    ap.add_argument("--full", action="store_true", help="question + reasoning")
    a = ap.parse_args()

    data = load(a.file)
    v = check(data, a.unit)
    rows = in_force(data, a.unit) if data else []

    # Every line below is Thai, and a cp1252 console cannot encode it: this
    # function raised UnicodeEncodeError on its first line and exited 1 with the
    # log unprinted. That is not cosmetic — R3 removed the owner's rung and put
    # this printout IN THE RENDER PATH as the replacement, so a crash here is a
    # decision log that silently stops reaching the only channel he reads.
    # `critique_call.py` documents the identical failure (it exited 1 AFTER
    # succeeding, twice); same fix, and the answer's exact words are the artefact.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"DECISIONS IN FORCE ({a.unit or 'all units'}) — "
          f"เปลี่ยนได้ทุกข้อ ทุกเมื่อ ไม่มีข้อไหนรอคุณอยู่:")
    for d in rows:
        print(one_line(d))
        if a.full:
            print(f"      ถาม: {d.get('question')}")
            print(f"      เพราะ: {d.get('because')}")
            if d.get("owner_override"):
                print(f"      คุณสั่ง: {d['owner_override']}")
    if not rows:
        print("  (none)")
    for s in v:
        print(f"  !! {s}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
