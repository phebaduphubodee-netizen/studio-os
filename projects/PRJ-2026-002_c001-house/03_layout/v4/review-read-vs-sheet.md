# REVIEW — machine read vs true sheet (สแกน overlay แล้ว ยืนยัน/แก้ทีละแถว)

- ลูกศร**เขียว** = เจ้าของเซ็นแล้ว (อยู่ใน ledger — rebuild ทอยใหม่ไม่ได้, gate จับถ้าเบี่ยง)
- ลูกศร**ส้ม** = hand-read ยังไม่เซ็น — จุดที่ต้องใช้ตาดู (ถูกแล้วก็เซ็นได้เลย ↓ จะได้เขียวถาวร)
- เส้นประ**น้ำเงิน** = ขอบเขตห้องที่เครื่องอ่าน — เถียงได้ (เช่น แนวประตูกระจก / เขตใน-นอก)
- ชิ้นที่**วาดในแบบแต่ไม่มีกรอบสี** = เครื่องอ่านไม่เห็น (ตกหล่น เคสแบบ BF09-2) — ชี้ตำแหน่งบอกได้เลย

## A — master_bedroom

| badge | ชิ้น | kind (identity = human call) | rot | facing |
|-------|------|------|-----|--------|
| A1 | ผนังระแนงหัวเตียง BF14 (325x10x280) | headboard (builtin) | 0 (หัน S) | – |
| A2 | ตู้เสื้อผ้าเหนือเตียง BF09-3 (330x60x280) | wardrobe (builtin) | 0 (หัน S) | – |
| A3 | โต๊ะทำงาน built-in BF11 (320x60x280) | cabinet (builtin) | 0 (หัน S) | – |
| A4 | ตู้/ชั้น BF10 (250x60x280) | cabinet (builtin) | 0 (หัน S) | – |
| A5 | เตียง 7'x6.5' หัวตะวันออก | bed (loose) | 270 (หัน W) | ● hand-read — ตรวจ/เซ็น |
| A6 | ม้านั่งปลายเตียง (bench) | bench (loose) | 0 (หัน S) | – |
| A7 | โต๊ะข้างเตียง เหนือ (มีโคมไฟ) | side_table (loose) | 0 (หัน S) | – |
| A8 | โต๊ะข้างเตียง ใต้ (มีโคมไฟ) | side_table (loose) | 180 (หัน N) | – |
| A9 | เก้าอี้ทำงาน (หันเข้าโต๊ะ W) | armchair (loose) | 270 (หัน W) | ● hand-read — ตรวจ/เซ็น |
| A10 | ตู้ทีวีสูง ผนังตะวันตก | tv_console (loose) | 0 (หัน S) | – |
| A11 | อ่างล้างหน้าคู่ (ในห้องน้ำ) | vanity_double (fixture) | 0 (หัน S) | – |
| A12 | โถสุขภัณฑ์ WC | toilet (fixture) | 0 (หัน S) | – |
| A13 | อ่างอาบน้ำ (bathtub) | bathtub (fixture) | 0 (หัน S) | – |
| A14 | ฝักบัว (shower) | shower (fixture) | 0 (หัน S) | – |
| A15 | ตู้เสื้อผ้า BF09-1 ขาเหนือ (L 5.2m) | wardrobe (fixture) | 0 (หัน S) | – |
| A16 | ตู้เสื้อผ้า BF09-1 ขาตะวันออก (L 5.2m) | wardrobe (fixture) | 0 (หัน S) | – |
| A17 | ตู้เสื้อผ้า BF09-2 (150x60x280) | wardrobe (fixture) | 0 (หัน S) | – |

## B — sitting_room

| badge | ชิ้น | kind (identity = human call) | rot | facing |
|-------|------|------|-----|--------|
| B1 | ตู้โชว์ BF12-1 (157.5x40x280) | cabinet (builtin) | 0 (หัน S) | – |
| B2 | ตู้สูง BF12-2 (70x40x280) | cabinet (builtin) | 0 (หัน S) | – |
| B3 | ชั้นวางทีวี ผนังตะวันออก BF13 (410x30x50) | cabinet (builtin) | 0 (หัน S) | – |
| B4 | โซฟา 3 ที่นั่ง | sofa (loose) | 90 (หัน E) | ● hand-read — ตรวจ/เซ็น |
| B5 | เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน) | armchair (loose) | 8 | ✓ owner-signed |
| B6 | เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน) | armchair (loose) | 332 | ✓ owner-signed |
| B7 | โต๊ะกลม (ระหว่างเก้าอี้) | side_table (loose) | 0 (หัน S) | – |
| B8 | โต๊ะกลม (ข้างโซฟา) | side_table (loose) | 0 (หัน S) | – |
| B9 | โต๊ะวางกล้วยไม้ (console) | console (loose) | 0 (หัน S) | – |

## เซ็น facing (แถวส้ม) — ถูกแล้ว = วาง stub ตามเดิม / ผิด = แก้ `rot` ก่อนวาง

วางลง `confirmed[]` ใน `placement-review.json` แล้ว regenerate — rebuild จะ re-apply ค่านี้แทนการทอยใหม่; orphan gate จะ FAIL ถ้าลายเซ็นหลุดจากชิ้น:

**A5** — เตียง 7'x6.5' หัวตะวันออก:
```json
{"room": "master_bedroom", "name": "เตียง 7'x6.5' หัวตะวันออก", "rot": 270, "w": 2134, "d": 1981, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**A9** — เก้าอี้ทำงาน (หันเข้าโต๊ะ W):
```json
{"room": "master_bedroom", "name": "เก้าอี้ทำงาน (หันเข้าโต๊ะ W)", "rot": 270, "w": 510, "d": 546, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B4** — โซฟา 3 ที่นั่ง:
```json
{"room": "sitting_room", "name": "โซฟา 3 ที่นั่ง", "rot": 90, "w": 2202, "d": 1008, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

## เซ็น kind (identity, แถว loose) — ถูกแล้ว = วาง stub ตามเดิม / ผิด = แก้ค่า `kind` ก่อนวาง

วางลง `confirmed[]` ใน `placement-review.json` แล้ว regenerate — identity จะติดถาวร (rebuild เปลี่ยนเองไม่ได้, gate ยก contradicts_signed_kind ถ้าเบี่ยง). วางเฉพาะแถวที่ ตรวจด้วยตาแล้วจริง; แก้ทีหลัง = APPEND entry ใหม่ชื่อ+ขนาดเดิม (ตัวหลังชนะ):

**A5** — เตียง 7'x6.5' หัวตะวันออก:
```json
{"room": "master_bedroom", "name": "เตียง 7'x6.5' หัวตะวันออก", "kind": "bed", "w": 2134, "d": 1981, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**A6** — ม้านั่งปลายเตียง (bench):
```json
{"room": "master_bedroom", "name": "ม้านั่งปลายเตียง (bench)", "kind": "bench", "w": 504, "d": 1002, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**A7** — โต๊ะข้างเตียง เหนือ (มีโคมไฟ):
```json
{"room": "master_bedroom", "name": "โต๊ะข้างเตียง เหนือ (มีโคมไฟ)", "kind": "side_table", "w": 300, "d": 300, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**A8** — โต๊ะข้างเตียง ใต้ (มีโคมไฟ):
```json
{"room": "master_bedroom", "name": "โต๊ะข้างเตียง ใต้ (มีโคมไฟ)", "kind": "side_table", "w": 300, "d": 294, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**A9** — เก้าอี้ทำงาน (หันเข้าโต๊ะ W):
```json
{"room": "master_bedroom", "name": "เก้าอี้ทำงาน (หันเข้าโต๊ะ W)", "kind": "armchair", "w": 510, "d": 546, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**A10** — ตู้ทีวีสูง ผนังตะวันตก:
```json
{"room": "master_bedroom", "name": "ตู้ทีวีสูง ผนังตะวันตก", "kind": "tv_console", "w": 600, "d": 2046, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B4** — โซฟา 3 ที่นั่ง:
```json
{"room": "sitting_room", "name": "โซฟา 3 ที่นั่ง", "kind": "sofa", "w": 2202, "d": 1008, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B5** — เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน):
```json
{"room": "sitting_room", "name": "เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)", "kind": "armchair", "w": 680, "d": 640, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B6** — เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน):
```json
{"room": "sitting_room", "name": "เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)", "kind": "armchair", "w": 660, "d": 640, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B7** — โต๊ะกลม (ระหว่างเก้าอี้):
```json
{"room": "sitting_room", "name": "โต๊ะกลม (ระหว่างเก้าอี้)", "kind": "side_table", "w": 600, "d": 600, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B8** — โต๊ะกลม (ข้างโซฟา):
```json
{"room": "sitting_room", "name": "โต๊ะกลม (ข้างโซฟา)", "kind": "side_table", "w": 600, "d": 600, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

**B9** — โต๊ะวางกล้วยไม้ (console):
```json
{"room": "sitting_room", "name": "โต๊ะวางกล้วยไม้ (console)", "kind": "console", "w": 1002, "d": 402, "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
```

หมายเหตุ identity: คอลัมน์ kind เซ็นเข้า ledger ได้แล้ว (confirmed_kind) — วาง stub จากส่วน 'เซ็น kind' ข้างบน; แก้ทีหลัง = APPEND entry ใหม่ (ชื่อ+ขนาดเดิม, ตัวหลังชนะ). ชิ้น builtin/fixture ไม่มี stub (generator ไม่ apply sign) — แก้ identity ของพวกนั้น = บอกเลข badge + ชนิดที่ถูก แล้วเราแก้ generator ให้
