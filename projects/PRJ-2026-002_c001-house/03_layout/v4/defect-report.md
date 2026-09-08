# floor2 defect gate -- PASS

- floor2_defect_gate v1.2 on floor2_v4-manifest.json; pieces 26, defects 5 (FAIL 0 / REVIEW 0 / signed 5)

## answer key -- สิ่งที่ owner เคยจับด้วยตา เทียบกับที่ gate จับ
- BF14 ทะลุ BF09-3 -- owner จับ 2026-07-07; FIXED 2026-07-10 ตามคิว owner 07-07 ("BF14 trim to y2650"): ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- อ่างล้างหน้าคู่ ทะลุ WC -- owner จับ 2026-07-07; FIXED 2026-07-10 ตามคิว owner 07-07 ("vanity nudge to x650"): ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- กำแพงในโมเดลไม่ครบ -- owner จับด้วยตา 2026-07-10: จับได้ -> `a9a01347d66e`, `05bd38d31834`, `415fed34d04e`
- BF09-1 (ขา E) ทับประตู dressing<->sitting -- owner จับ 2026-07-07; RESOLVED 2026-07-10r2: ช่อง s2 y[3400,4622], BF09-1 ยืดถึง y4674 = พ้นวงกบ 52mm; ตรวจได้ด้วยเครื่องแล้ว. UPDATE 2026-07-11: owner 's2 ไม่ใช่บานเลื่อน' -> reclassify sliding->opening (ช่องเปิด); การเคลียร์วงกบยังจริง (BF09-1 พ้นขอบช่อง 52mm ไม่ว่าจะมีบานหรือไม่): ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- markup รอบ2: 'ในแบบมีกำแพงระหว่างสองชิ้นนี้' + 'ไม่มีประตู' -- party wall y[2800,5698] เติมกลับแล้ว (กำแพง+ช่อง s2); ขอบต้องเลิกโหว่: ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- markup รอบ2: ช่องผนังเหนือ sitting ไม่ใช่ประตู -- declare เป็นหน้าต่าง w5; ห้ามมีช่อง undeclared เหลือแถวนี้: ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- markup รอบ2 วงเล็ก: กระจก pier หาย -- g1 + envelope edge ต้องปิด: ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- markup รอบ2 วงล่าง: มุม SE party->ผนังใต้โหว่ -- เติม 0.48pt ink กลับแล้ว: ไม่อยู่ในข้อมูลปัจจุบัน (ยืนยันด้วยการสแกน ไม่ใช่ความเงียบ)
- extraction-loss check C4a (วัดเฉพาะ clip/merge loss -- fresh ink มาจาก extractor ตัวเดียวกับ walls-json จึง CIRCULAR โดยธรรมชาติ, ห้ามอ่านเป็น 'กำแพงครบ'): missing 0 runs / 0 mm; ตัววัด 'กำแพงไม่ครบ' ที่อิสระจริงคือ C4b ด้านบน
- doorway candidates in scope: 6 (declare แล้ว 6, ไม่ declare = REVIEW C3_undeclared_doorway ทุกช่อง -- v1.1 เคยอ่านทุกช่องเป็นประตูจริงโดยปริยาย ซึ่ง markup รอบ 2 พิสูจน์ว่าผิด); ข้อจำกัดที่เปิดเผย: C3 เห็นเฉพาะช่องบานเดี่ยว 550-1300mm -- บานคู่/บานเลื่อนกว้างกว่านั้นจะโผล่เป็นขอบไม่มีกำแพงใน C4b แทน
- openings declared: 10
- envelope edges (C4c, แนวที่ C4b มองไม่เห็น): declared 5, เปิดโหว่ 0 run

1. **[SIGNED] C2_out_of_room** -- ตู้เสื้อผ้า BF09-1 ขาตะวันออก (L 5.2m)
   - 'ตู้เสื้อผ้า BF09-1 ขาตะวันออก (L 5.2m)' โผล่นอก 'master_bedroom/โซนตู้เสื้อผ้า (wardrobe bay)' 1176 mm -- เลื่อนกลับเข้า outline หรือแก้ outline ถ้าห้องผิด (owner call)
   - fingerprint `c35b348275f5` (signed: owner (transcribed))
2. **[SIGNED] C2_out_of_room** -- ตู้เสื้อผ้า BF09-2 (150x60x280)
   - 'ตู้เสื้อผ้า BF09-2 (150x60x280)' โผล่นอก 'master_bedroom/โซนตู้เสื้อผ้า (wardrobe bay)' 670 mm -- เลื่อนกลับเข้า outline หรือแก้ outline ถ้าห้องผิด (owner call)
   - fingerprint `82a588cc3271` (signed: owner (transcribed))
3. **[SIGNED] C4b_room_edge_unwalled** -- master_bedroom
   - ขอบห้อง 'master_bedroom' ด้าน h@-450 ช่วง [0,5500] (5500 mm) ไม่มีกำแพงในโมเดล -- ถ้าเป็นช่องเปิด/กระจกจริง เซ็น dismiss ครั้งเดียวจบ; ถ้าไม่ใช่ = กำแพงหายจาก build
   - fingerprint `a9a01347d66e` (signed: owner (transcribed))
4. **[SIGNED] C4b_room_edge_unwalled** -- master_bedroom/โซนตู้เสื้อผ้า (wardrobe bay)
   - ขอบห้อง 'master_bedroom/โซนตู้เสื้อผ้า (wardrobe bay)' ด้าน h@5850 ช่วง [3254,5552] (2298 mm) ไม่มีกำแพงในโมเดล -- ถ้าเป็นช่องเปิด/กระจกจริง เซ็น dismiss ครั้งเดียวจบ; ถ้าไม่ใช่ = กำแพงหายจาก build
   - fingerprint `05bd38d31834` (signed: owner (transcribed))
5. **[SIGNED] C4b_room_edge_unwalled** -- sitting_room
   - ขอบห้อง 'sitting_room' ด้าน h@0 ช่วง [5752,10650] (4898 mm) ไม่มีกำแพงในโมเดล -- ถ้าเป็นช่องเปิด/กระจกจริง เซ็น dismiss ครั้งเดียวจบ; ถ้าไม่ใช่ = กำแพงหายจาก build
   - fingerprint `415fed34d04e` (signed: owner (transcribed))

PROPOSAL-ONLY: gate เสนอวิธีแก้ ไม่แตะ scene-graph; เซ็น dismiss ใน defect-review.json ด้วย fingerprint; FAIL ที่ไม่เซ็น = บล็อก build

engine: floor2_defect_gate v1.2
