# Gate artifact — R2 standard hand-off (one per stop)

<!-- RULE (knowledge/brand-standards/iteration-control-and-review-gates.md R2,
adopted 2026-07-28): every stop — scheduled gate or R1 stop-loss — hands the
owner exactly this, nothing more. The lane BLOCKS until his verdict. Grounding:
VFX dailies (~15 s per artist) + HITL context package (1,000-2,000 tokens,
visual diff, reversibility, reject-with-edits). Fill ALL fields; "unsure" may
never be empty — an empty unsure field is the round-2/3 failure shape (two
"closed" declarations, four defects each). Spend (R6) is always reported.

AMENDED 2026-08-07, from an outside structural audit of this repo. Three
fields were added and one habit was removed, each for a measured reason:

  * VERDICT — `grep -l "VERDICT\|C4" training/TRN-002/gate-*.md` returned ONE
    file out of ten. The owner's rung did not go missing; it was displaced by
    the builder's own closing line drifting from "ถ้าไม่ค้านผมเดินตามนี้เลย"
    (gate #9) to "คิวถัดไปที่ผมเห็น เรียงตามที่ผมจะเลือกเอง" (gate #14) to
    "ที่เหลือข้างบนผมเลือกเองแล้ว" (gate #15) — against CLAUDE.md:50, "The lane
    BLOCKS on an unanswered gate." A gate that proposes its own next round is
    not a gate. The queue is now the owner's to order, and the builder's
    ranking is advice with a heading that says so.

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

**ขอ verdict:** ไปต่อ / แก้ตามนี้ / ฆ่าทิ้ง / ปิดเลน
<!-- The round does not close and the next one does not open until this line is
answered by the owner (R3). If the channel is down, write "OWNER UNREACHABLE
<date>" here — never a builder default. -->
