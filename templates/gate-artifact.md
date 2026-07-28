# Gate artifact — R2 standard hand-off (one per stop)

<!-- RULE (knowledge/brand-standards/iteration-control-and-review-gates.md R2,
adopted 2026-07-28): every stop — scheduled gate or R1 stop-loss — hands the
owner exactly this, nothing more. The lane BLOCKS until his verdict. Grounding:
VFX dailies (~15 s per artist) + HITL context package (1,000-2,000 tokens,
visual diff, reversibility, reject-with-edits). Fill ALL fields; "unsure" may
never be empty — an empty unsure field is the round-2/3 failure shape (two
"closed" declarations, four defects each). Spend (R6) is always reported. -->

## <lane / element> — <date> — gate #<n>

**ภาพ:** ก่อน `<path>` | หลัง `<path>` (คู่เดียว; quick-look ได้ถ้ายังไม่ปิด gate,
ปิด gate ต้อง full-fidelity + แผง look_bench ข้างงานส่งจริง)

1. **แก้อะไร:** <one line — the decision/mechanism, not the keystrokes>
2. **ผมตัดสินว่า:** <pass/kill + why, one line; ถ้าเลือกทางใดทางหนึ่ง ให้บอกทางที่ทิ้งไปและเหตุผลสั้นๆ>
3. **ไม่แน่ใจ:** <the thing I most want his eye on — NEVER empty>

**Spend:** <build+render cycles this gate / cumulative this lane> · **Reversible:** <yes/no+how>
**ขอ verdict:** ไปต่อ / แก้ตามนี้ / ฆ่าทิ้ง
