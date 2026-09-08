# README-walls — floor2-walls-mm.json ชุดไหนคือความจริง (2026-08-04)

ไฟล์ชื่อเดียวกันมี **สามชุด** ใน stage นี้ ต่างสถานะกันโดยเจตนา — แต่ก่อนวันนี้
ไม่มีป้ายบอก ณ จุดใช้งาน (outside-review 2026-08-04 ข้อ 5 + triage วัดยืนยัน)

| copy | เนื้อหา | สถานะ |
|------|---------|-------|
| `floor2-walls-mm.json` (ระดับ `03_layout/`) | 992 segments — machine extract ล้วน (md5 `6899e281…`) | **RETIRED v3 BASELINE** — ขาด 4 หน้าผนัง SW-corner ที่ owner ยืนยัน (เส้น 0.48pt ต่ำกว่า gate 0.6pt ของ `pdf_extract_walls`) **ห้ามเปิดงานใหม่จากชุดนี้** |
| `v4/floor2-walls-mm.json` | 1014 segments = 992 เดิม (bit-identical, ลำดับเดิม) + 22 segments ใน `manual_additions` (owner-confirmed SW corner, พิกัดจาก vector จริงใน PDF ไม่ใช่กะด้วยตา) (md5 `550225f7…`) | **SOURCE OF TRUTH ปัจจุบัน** — consumer ที่ active ทุกตัวอ่านชุดนี้ (test_cross_signal / test_zone_flag / test_facade_reader / เลน `v4/floor2_v4-manifest.json`); gate pin `v4/placement-gate.json` ตรง bytes ปัจจุบัน |
| `v5/floor2-walls-mm.json` | bit-identical กับ root | **BLIND CONTROL** — machine-inert (v5 manifest ไม่มี `walls_json` key) การที่มัน reproduce root ได้เป๊ะคือหลักฐานว่า extractor deterministic — นั่นคือหน้าที่ของมัน |

## กฎใช้งาน

- งานใหม่ทุกชิ้นอ่าน **`v4/floor2-walls-mm.json`** ผ่าน `v4/floor2_v4-manifest.json`
- **อย่ารัน `build_floor.py` ด้วย root `floor2-manifest.json`**: จะ extrude ผนัง v3
  ที่ขาด 4 หน้า และ gate pin ของเลนนั้น self-consistent — **ไม่มี alarm ใดเตือน**
  (defect ตระกูล R9: ไฟล์ที่ถูก copy คือ coordinate ที่ถูก type — ถูกต้อง ณ วัน copy
  แล้วเงียบ ๆ ผิดเมื่อการแก้ตามไปไม่ครบ)

## ทำไมไม่ stamp ลงในไฟล์ v3 ตรง ๆ

`03_layout/placement-gate.json` pin sha1 ของทั้ง `floor2-manifest.json` (`65e91839…`)
และ `floor2-walls-mm.json` (`89548257…`) — เลน v3 ถูกเก็บเป็น baseline แช่แข็งตาม
RESTART-PROMPT (ดู `v4/DIFF-v4-vs-v3.md`) การแก้ bytes ใด ๆ ทำ pin แตกและทำลาย
integrity ของ baseline — ป้ายจึงอยู่ที่ README นี้ ณ จุดใช้งานแทน

## บันทึกแก้เอกสาร (2026-08-04)

`v5/floor2_v5-blind-read.md` และ `v5/floor2_v5-manifest.json` เคยอธิบายเหตุผลที่ไม่อ่าน
root ว่า "root carries v4 owner manual_additions" — **วัดแล้วไม่จริง** (root md5 ==
v5, ไม่มี key `manual_additions`) แก้พร้อม correction inline แล้วทั้งสองจุด
blindness protocol เองไม่เสีย — เหตุผลที่จดไว้เท่านั้นที่ผิด
