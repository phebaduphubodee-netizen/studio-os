# Gate artifact — R2 round RECORD (one per stop; it does not block)

<!-- RULE (knowledge/brand-standards/iteration-control-and-review-gates.md R2,
adopted 2026-07-28): every stop — scheduled gate or R1 stop-loss — writes
exactly this, nothing more. Grounding: VFX dailies (~15 s per artist) + HITL
context package (1,000-2,000 tokens, visual diff, reversibility,
reject-with-edits). Fill ALL fields; "unsure" may never be empty — an empty
unsure field is the round-2/3 failure shape (two "closed" declarations, four
defects each). Spend (R6) is always reported.

**"The lane BLOCKS until his verdict" IS REVOKED, 2026-08-08** (owner: *"เอาผม
ออกจาก gate เลย ไม่ต้องรอผม"*). This file is a RECORD. Write it, then keep going.
See CLAUDE.md R3 for what replaced the rung and what removing it costs.

AMENDED 2026-08-07, from an outside structural audit of this repo. Three
fields were added and one habit was removed, each for a measured reason:

  * VERDICT — `grep -l "VERDICT\|C4" training/TRN-002/gate-*.md` returned ONE
    file out of ten. The 2026-08-07 reading was that the owner's rung had been
    displaced by the builder's own closing line drifting from "ถ้าไม่ค้านผมเดิน
    ตามนี้เลย" (gate #9) to "คิวถัดไปที่ผมเห็น เรียงตามที่ผมจะเลือกเอง" (gate #14)
    to "ที่เหลือข้างบนผมเลือกเองแล้ว" (gate #15).
    **SUPERSEDED 2026-08-08 — the drift was real and the diagnosis was wrong.**
    The final count came to 2 verdicts in 21 gates, and the owner's explanation
    was not that the builder had usurped him but that he **reads renders, not
    documents**: the asks were landing in a channel he does not use. So the
    field is gone rather than restored, and this template no longer proposes
    that anyone wait. The builder's ranking is now simply the plan, recorded.

  * RANK — the charter's finish line (qa/reproduction-curriculum.md) has never
    been answered once in 46 rounds across two lanes, while five blind sheets
    sit built on disk with their answer keys beside them. It is the cheapest
    unpaid debt in the repo: one sitting, about five minutes.

  * SPEND in TIME — R6 asks for "cycles/renders/tokens" and every Spend line
    in this lane's ten gates is a render count. Renders are under 9% of lane
    wall-clock. Governing the cheapest input and not measuring the two
    expensive ones is why "is the next round worth funding" has never been an
    askable question.

  * DISTILLATION — the charter says the copies are not the deliverable, the
    LEARNING is. Thirteen rounds closed without one line entering knowledge/,
    including every round after the rule making it a gate condition was
    written. rule_gate.audit_learning checks that a file EXISTS; only this
    field can say what was added this round. -->

## <lane / element> — <date> — gate #<n>

**ภาพ:** ก่อน `<path>` | หลัง `<path>` (คู่เดียว; quick-look ได้ถ้ายังไม่ปิด gate,
ปิด gate ต้อง full-fidelity + แผง look_bench ข้างงานส่งจริง)

1. **แก้อะไร:** <one line — the decision/mechanism, not the keystrokes>
2. **ผมตัดสินว่า:** <pass/kill + why, one line; ถ้าเลือกทางใดทางหนึ่ง ให้บอกทางที่ทิ้งไปและเหตุผลสั้นๆ>
3. **ไม่แน่ใจ:** <the thing I most want his eye on — NEVER empty>

**C2 cold critic (R7):** <top defects from the fresh-eyes report + triage each:
✓รับ→เลนไหน / ✗หักล้าง→การวัด/spec/reference ที่ใช้หักล้าง — ห้ามหักล้างด้วยรสนิยม>
**C3 (gate ใหญ่):** <Gemini verdict + triage, or "not fired — minor gate">

<!-- EVERY item gets a row, cited by id (C2#7 / C3#3), or rule_gate refuses the
next render. The check is item-level because the rule is: r26's C2#14 said the
wardrobe bays were "arbitrarily unequal", nobody wrote a row for it, and the
next round the owner found that bay built 259 mm short with his own eye. -->

**RANK (charter finish line):** <`look_bench.py <full frame> --blind` sheet path
+ the owner's A–F ordering + where ours placed. ผ่าน = ของเราไม่รั้งท้าย และเหตุผล
ที่ให้กับช่องของเราต้องเป็น "ข้อบกพร่อง" ไม่ใช่ "รสนิยม". ยังไม่ได้ถาม = เขียนว่า
NOT ASKED และนับเป็นหนี้ ห้ามเว้นว่าง>

**เข้า knowledge/ รอบนี้:** <path ของไฟล์ที่เขียน หรือเหตุผลที่รอบนี้ไม่มีอะไรถ่ายทอดได้
— ห้ามเว้นว่าง สิ่งที่วัดแล้วไม่ได้เขียน คือสิ่งที่รอบหน้าจะวัดใหม่>

**Spend:** <builds/renders> · <นาที wall-clock ของเลนรอบนี้> · <token ถ้ามี> ·
สะสมทั้งเลน <…> · **Reversible:** <yes/no+how>

**คิวที่ผมเสนอ (คำแนะนำ ไม่ใช่คำสั่ง):** <ranked, พร้อมเหตุผลต่อข้อ>

**ตัดสินรอบนี้:** <the ids in `qa/open-decisions.json` this round ADDED or
CHANGED, one line each: what is now true, and the one edit that undoes it.
ไม่มีอะไรใหม่ → เขียนว่า "ไม่มี" — ห้ามเว้นว่าง>

<!-- THIS FIELD ASKS NOTHING, AND THAT IS THE POINT, 2026-08-08.

It has now been wrong twice in two directions, which is worth recording because
the second wrong was a reaction to the first. Originally it read
"ไปต่อ / แก้ตามนี้ / ฆ่าทิ้ง / ปิดเลน" — a menu naming no fork, pasted unchanged into
nine gates, none of them answered. Counted across the lane: 21 gate artifacts,
2 with a recorded owner verdict, 19 without, and not one of the 19 ever stopping
the lane. The builder's fix was to make the ask BLOCKING. Owner, within the
hour: "เอาผมออกจาก gate เลย ไม่ต้องรอผม สุดท้ายทุกขั้นตอนที่ render ออกมาผมก็นั่งดู
ทุกรูปตลอดอยู่แล้ว".

His reason is the part to keep: HE READS RENDERS, NOT DOCUMENTS. Nineteen
unanswered gates were nineteen asks filed in a channel he does not use, and
making that channel mandatory would have halted the lane over messages he was
never going to see.

So a gate artifact is a RECORD, not a request. It never blocks. The decisions
live in `qa/open-decisions.json`, checked by `pipeline/scripts/decisions_check.py`
from inside `rule_gate.check()`, which fails the render only on the BUILDER's
side of the bargain: a row with no decider, a `where` naming a path that does
not exist, a missing `reverse_by`, or an owner ruling relabelled as the
builder's call. Every gate run prints the log into the render path — his
channel — one line per decision, each naming its reversal. -->
