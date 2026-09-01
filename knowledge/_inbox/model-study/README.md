# model-study — บทเรียนการปั้นที่ผ่าจากโมเดล BlenderKit ที่ซื้อ/โหลดจริง

ORD-2026-09-01-study-blenderkit-models · charter: `docs/blenderkit-study-2026-09-01.md`
· เครื่องมือ: `pipeline/scripts/model_study_probe.py`
  - `batch` → dump ต่อ asset ที่ `assets/shared/blenderkit/_study/<id>.probe.json`
    (71 ไฟล์, probe ครบ 2026-09-01, 0 fail) — **cache นี้ gitignored** (.gitignore:68,
    shelf ถือ mesh ที่ห้าม redistribute) สร้างใหม่ได้จาก asset id เสมอ
  - `stats` → `qa/blenderkit-study-stats.json` — **ตารางสถิติอยู่ในเรโป** เพราะเป็น
    การวัด ไม่ใช่ mesh; ทุกโน้ตอ้างตารางนี้ ถ้ามันอยู่แต่ใน cache หลักฐานของทุกกฎ
    จะหายไปตอน clone (และรุ่นแรกของตารางนี้เกิดจากสคริปต์ใน scratchpad = สร้างซ้ำไม่ได้)

กฎของโน้ตในโฟลเดอร์นี้:
- ทุกข้อเรียนต้องถือ**ตัวเลขจาก dump** (verts, verts/m², subsurf levels, node chain,
  ขนาด texture) — คำคุณศัพท์เปล่า ๆ ไม่ใช่บทเรียน
- ทุกโน้ตเทียบกับ**โค้ดของเราที่สร้างคลาสเดียวกัน** (file:line) — delta คือ curriculum
- REFERENCE tier จนกว่าจะถูกกลั่นเข้า `knowledge/` — และกฎที่จะขึ้นเป็น LIVE
  ต้องผ่านการพิสูจน์ในรอบ build จริงก่อน (R11: โครงสร้างที่อ่านได้ ≠ พิกเซลที่สวยแล้ว)
- ดัชนีของชุดโน้ต: `2026-09-01-INDEX.md`
