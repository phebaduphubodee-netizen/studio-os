# M3.2 Designer-feedback analysis — 2026-07-03

Companion to `judge-calibration-2026-07-03.md`. The golden set was labeled by a
practicing interior designer (owner's peer). **All 26 = REWORK, scores 0–3
(mean 1.75), zero SHIP.** M3.2 = FAIL (Spearman ρ 0.428, Cohen κ 0.000).

κ is degenerate (one human class) — the informative signals are: (1) the designer
would ship 0/26 while the machine marked several ≥4 SHIP, and (2) ρ=0.428 = even
the *ranking* only weakly agrees. The machine's top-scored images (GS-11 5.0,
GS-18 4.75, GS-17 4.75) are among the designer's worst (2.0, 1.5, 2.0).

## Why they diverge — different axes, not noise
The LLM judge rewards **photoreal believability** (looks like a real photo). The
designer REWORKs almost entirely on **design correctness** — and even PRAISES the
realism/lighting on several (GS-02 "render ดูเหมือนจริง", GS-06 "depth of field
ดี", GS-09 "แสงสวย"). So the judge isn't "wrong about realism"; it's blind to the
axes the designer gates on. The judge's rubric is missing the designer's rubric.

## The designer's rubric, reverse-engineered from the notes
1. **สัดส่วน/สเกล (proportion & real-world scale)** — the dominant reason.
   - GS-02 furniture "polygon เหลี่ยม", หมอนอิงเล็ก, ที่นั่งสูงกว่าปกติ, ไม่สมส่วน
   - GS-06 พื้นไม้ SPC ผิดสัดส่วน; เฟอร์นิเจอร์ต้องเข้ากับตัวบ้าน
   - GS-03 ไม่มีรอยต่อลามิเนต — **ของจริงแผ่นละ 2.40×1.20 ม.** (concrete metric)
   - GS-19 กรอบรูปเล็กไป; GS-04/GS-01 สัดส่วนเพี้ยน
2. **ตำแหน่ง/ฟังก์ชันตามการใช้งานมนุษย์ (placement logic)**
   - TV recurring: GS-11 "ไม่ควรอยู่ข้างเตียง", GS-24 "อยู่หัวเตียง เงยคอดู?", GS-23 "ผิดเหมือนเดิม"
   - GS-01 ประตูกับหัวเตียงชนผนังเดียวกัน → ย้ายหัวเตียงไปผนังซ้าย
   - GS-05 ห้องน้ำ: สลับโถส้วม/อ่างตามความถี่ใช้; แยกโซนเปียก-แห้ง
   - GS-20 armchair เอาออก; GS-26 (บวก) armchair เฉียงรับ sofa = ถูกต้อง
3. **มุมกล้องต้องมีเหตุผล (camera rationale + height)**
   - GS-04/GS-05/GS-22 มุมนำสายตาไปผนังเปล่า / ไม่เห็นอะไร / ไม่มีประโยชน์
   - GS-15 กล้องสูงไป → **ดีไซเนอร์ใช้ความสูง 1.0–1.2 ม.** (concrete metric)
4. **สิ่งแปลกปลอม / hallucination artifacts**
   - GS-01 ก้อนดำหน้าภาพ + กรอบรูปโผล่ไม่มีเหตุผล; GS-21 คานดำ "ทำมาทำไม"
   - GS-17 "ช่องแคบ ๆ ไว้ให้หนูทำรัง" ← the ensuite narrow-side **Gate-0 already
     flagged REVIEW/needs-human-verify**. A designer independently caught it =
     clearance_check validated on a real eye.
5. **วัสดุ/ความสมจริง (material realism)** — GS-03 laminate seams, GS-25 ผนังหัวเตียง
   เรียบ/วัสดุซ้ำซาก, GS-02 polygon look.
6. **Progress acknowledged (2.5–3, still REWORK)** — GS-06/09/13/16/25/26. The
   designer sees the trajectory; nothing is yet client-shippable.

## Actionable, checkable wins (deterministic — don't need the LLM judge)
- **Camera height → 1.0–1.2 m** (designer's stated value; our eye-cam sits higher).
  Gate-evidenced build_room/camera change → re-gate.
- **TV placement rule** (not beside/above a bed) → layout validator predicate.
- **Furniture / laminate / floor real-world scale** (laminate 2.40×1.20 m; SPC
  plank scale) → material texture scale + furniture-spec scale check.
- **GS-17 narrow gap** — already caught by Gate-0; keep as human-verify.

## Decision owed to owner
- Enshrine this labels.json as permanent ground truth? (all-REWORK ⇒ κ degenerate;
  a future set spanning some genuinely shippable images would give a non-degenerate
  κ — but ρ + the SHIP-rate gap are already conclusive that the judge is too lenient.)
- Judge path: (a) expand the rubric to score proportion/placement/camera-rationale
  then re-calibrate, and/or (b) keep the judge as a photoreal pre-filter with the
  designer as the real gate (architecture already routes RESOLVED → human _inbox).
- Honest correction to the record: prior "5/5 SHIP" (PRJ-002) reflected a lenient
  judge, **not** verified client-readiness. A practicing designer REWORKs all of it.
