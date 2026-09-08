# OWNER ORDER — 2026-08-27 · the builder calls its own skills

## His words, verbatim

> **"เอาหมด ลุยยาว ๆ"**

> **"มีข้อแม้ว่าทั้งหมดนี้คุณต้องเป็นคนเรียกใช้เองเมื่อต้องใช้"**

## What was in front of him

A director-level list of skills worth building, then a self-audit of that list at his
question *"ดีที่สุดแล้วหรือยัง สิ่งที่เสนอมา"*. The audit found five defects in the first
proposal, three of which changed the answer:

1. **The wrong mechanism.** The `acquire` skill was proposed for a failure whose fix is a
   GUARD: `blenderkit.py fetch` never consulted the free-baseline protocol at all — the
   check existed only as a `print` inside `status`. R11 names that exact shape.
2. **A factual error that inverted a conclusion.** The six skills of 2026-07-02 were not
   "never used": they produced `concept.md` (07-02), `ffe-candidates.json` (07-04) and
   `bom.md` (07-02) and then stopped. They did not die of neglect — **the work changed
   shape** from a stage pipeline to a single-frame render loop that no skill described.
   Stage skills are therefore dormant-and-correct, not missing; they come due at the
   real-client run (ORD-2026-08-22).
3. **Two omissions stronger than half the list**: the C2 critic had no agent definition
   (its blindness was retyped by hand every round, and had leaked once), and
   `camera-composition` was missing entirely despite carrying the strongest measured
   evidence in the lane (D-152: his own camera took the exit clause from 6/4 fail to 8/2
   QUALIFIES with no object changed).
4. **An acceptance test with no instrument** — "evidence it was called within 3 rounds"
   with nothing in the repo able to count an invocation. R13's "obedience there is only
   declared", one level up.
5. **No statement of what it displaces.** None of it is on the P2 critical path.

The revised list was ordered by ENFORCEMENT STRENGTH rather than by topic: guard → agent
definition → hook → skills (only where the failure is "don't know how to make it good").

## What his condition adds, and why it is the load-bearing half

The list would have shipped seven roster entries into the same directory whose existing
entries had gone 54 days and 86 rounds unused. **His condition is the consumer clause**:
the roster is not a menu to be offered, it is a set of moves to be MADE, at the moment
the work matches, unasked.

Because a behavioural order with no reader is exactly the defect R13 was written for, the
order's own obedience test is now a counter, not a promise: `pipeline/scripts/skill_usage.py`
stamps every Skill/Agent call from a hook, `plan_status` prints each entry's call count
and last-used age at every session open, and this order stays **not-obeyed** — loudly,
with its age showing — until the log carries a real craft-skill call.

## Scope

CLASS order, standing. It governs every skill and agent in the roster, including ones
added later. An instance verdict about one skill narrows what may ship; it never repeals
the class (R13).

## Reversal

He says so. Mechanically: drop `lines += skill_lines()` from `plan_status.py` and the
roster goes quiet again.
