---
type: construction-brief
project: 
tags:
  - stage/construction
---

# Construction Brief

> เอกสารสำหรับ brief ช่าง — อ่านเข้าใจง่าย ไม่ใช่ language designer
> สรุปเฉพาะข้อมูลสำคัญที่ช่างต้องรู้ ส่วน drawing แนบแยก

## Project info

- **โครงการ**: 
- **ที่อยู่**: 
- **เวลาทำงานอนุญาต**: [จ-ส 8:00-18:00]
- **ช่องทางขนของ**: [ลิฟต์ขนของ, เวลา XX-XX]
- **ผู้ดูแล (นิติฯ)**: 

## Drawing list (ที่ใช้)

- [ ] Floor plan — `[filename].dwg`
- [ ] Demolition plan — `[filename].dwg`
- [ ] Ceiling plan — `[filename].dwg`
- [ ] Electrical plan
- [ ] Plumbing plan
- [ ] AC plan
- [ ] Elevation wall — `wall-XX.dwg`
- [ ] Detail drawing
- [ ] Material schedule
- [ ] Furniture schedule

## Construction sequence

| Phase | Description | Duration | Dependencies |
|-------|-------------|----------|--------------|
| 1 | Demolition + cleaning | [N] days | - |
| 2 | Rough plumbing / electrical | [N] days | phase 1 |
| 3 | Floor leveling + waterproof | [N] days | phase 2 |
| 4 | Wall + ceiling structure | [N] days | phase 3 |
| 5 | Floor finishing | [N] days | phase 4 |
| 6 | Wall finishing + paint | [N] days | phase 5 |
| 7 | Built-in installation | [N] days | phase 6 |
| 8 | Sanitary + light fixture | [N] days | phase 7 |
| 9 | Soft fixture + furniture | [N] days | phase 8 |
| 10 | Cleaning + handover | [N] days | phase 9 |

## Key spec call-outs (ที่ช่างต้องระวัง)

ใส่จุดที่ "ไม่ตรง drawing → ทำใหม่หมด":

- [ ] Floor level: [ระดับเท่ากันทั้งห้อง, drop X mm เฉพาะ wet area]
- [ ] Wall flatness tolerance: ± 2 mm/m
- [ ] Tile grout color: 
- [ ] LED strip recess depth: 
- [ ] Built-in gap to ceiling: 
- [ ] [เพิ่ม...]

## Material handling

- **Floor protection**: ใช้ [material] ทั้ง project
- **Wall protection** (corner): ใช้ [material]
- **Material storage**: [where]
- **Damaged material policy**: [responsibility]

## Cleanliness rules

- ทุกวันสิ้นวัน clean ก่อนกลับ
- ทิ้งขยะที่ [where]
- ห้องน้ำส่วนกลาง: [allowed / not]

## Communication

- **Primary contact**: [designer name + phone]
- **Channel**: [LINE group / call]
- **Site report**: ทุกวันสิ้นวัน, ภาพถ่าย 5+ ภาพ
- **Variation**: ต้อง approve เป็นลายลักษณ์อักษร ก่อนทำ

## Quality control

- ตรวจงานทุก [3] วัน
- Punch list: ใน [[../09-punch-list]]
- Inspection by senior: ก่อน handover

## Payment milestones

| Phase | % | Trigger |
|-------|---|---------|
| 1 | 30% | Contract sign + start |
| 2 | 30% | 50% completion |
| 3 | 30% | 90% + punch list reviewed |
| 4 | 10% | Handover sign-off |

---

*Drawing reference: [[link to DWG files folder]]*
