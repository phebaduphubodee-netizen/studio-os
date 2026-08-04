# NLM ask queue (lane-down fallback + batch material)

When the NLM lane is DOWN mid-run (auth expired / quota / network — see
CLAUDE.md "External research lane"), the run continues vault-only and appends
the unanswered question here. Re-ask after `notebooklm login` or the next day,
then clear the entry. Questions must already be privacy-clean (generic, no
client specifics) — the same rule as a live ask.

Format: `- [ ] <question> — <notebook id> — queued <date> — <why it came up>`

## Queue

- [ ] Deep-read paper **SEIG — "Thinking in Blender: Staged Executable Inverse
  Graphics with Vision-Language Models"** (Cornell; https://arxiv.org/html/2606.02580)
  — งานที่ใกล้เลน reproduction ของเราที่สุดเท่าที่เคยพบ: สร้างฉาก Blender แก้ไขได้
  จากภาพเดียว แบ่งเฟส init→geometry→material→lighting แต่ละเฟสมี
  generator-verifier loop + round budget (geometry 5 รอบ, เฟสอื่น 2-3)
  สิ่งที่ต้องสกัด: (1) เกณฑ์ตัดสิน "เฟสปิด" ต่อเฟส และ round budget — ชนกับ R1
  stop-loss ของเรา เลขต่างกันตรงไหน เพราะอะไร (2) รูปประโยค verifier feedback
  ที่ actionable ต่อรอบ — เทียบ `templates/cold-critic-prompt.md`/R7 มีอะไรที่
  พวกเขา force ให้ verifier ตอบแล้วเราไม่ได้ force (3) instrument ที่ใช้วัด
  (PSNR/DINO/CLIP ต่อเฟส) — ตัวไหนยืมเป็น C0 ได้กับ target ในเครื่อง
  (4) ทำไม monolithic baseline (VIGA) แพ้ 5/6 metric — หลักฐานเชิงปริมาณหนุน
  การแบ่งเฟสของ TRN lane (5) failure modes ที่ผู้เขียนรายงานเอง
  กติกา: ทุกตัวเลข/claim ต้องมี section/URL กำกับ ไม่มี = quarantine ตาม
  DISTILLATION-LEDGER — notebook ใหม่: `nlm-seig-staged-inverse-graphics` —
  queued 2026-08-04 — มาจาก landscape scan ของ C2 (Cowork session): หัวข้อที่ 7
  ของชุดเสนอ 2026-08-04; รอบ 5 ของ TRN-002 จะเปิดด้วยคำถาม C1-pattern ซึ่งข้อ (2)
  ของ paper นี้ชนตรงที่สุด

- [ ] **Inspection blindness / habituation ใน visual QA** — กลไก (change
  blindness, satisfaction of search, low-prevalence effect, label-induced
  blindness) + countermeasures ที่มี effect size (inversion/flip, per-zone
  scan, 2AFC vs rating, double-read yield, time-away decay) — คำถาม 8 ข้อ +
  scope discipline เต็มใน `docs/research/2026-08-04-dr-queue-triage.md` §1.
  หลักฐานลงแล้ว **2 sweeps / 32 findings / 4 เลนส์** ใน
  `docs/research/2026-08-04-inspection-blindness-evidence.md` (เลขกอริลลา
  CONFIRMED จาก abstract; sweep 2 จับ citation ผิดของ sweep 1 ได้หนึ่งตัว —
  แก้แล้ว) — เหลือ residual: full-text ของเลขที่ยังติด [Q], exposure-count
  curve, time-away decay, label-withholding.
  Vehicle: scite Smart-Citation pass หลังโควตารีเซ็ต 2026-08-17;
  NLM DR เฉพาะ residual ถ้า scite ยังตอบไม่ครบ — notebook ใหม่ (ถ้าต้องยิง):
  `nlm-inspection-blindness` — queued 2026-08-04 — ชุดเสนอ C2 หัวข้อ 1;
  **มัดรวมกับ SEIG entry ข้างบน (consumer เดียวกัน: คำถาม C1-pattern ของ
  รอบ 5) ยิงพร้อมกันที่จุดเปลี่ยน blockout→materials อย่างช้าสุดก่อน
  parameterise STRANGER SWEEP เป็นกฎมี test**. กติกา quarantine: ตัวเลขไม่มี
  section/URL = ไม่เข้า vault

- [ ] **มวลผ้านวม/หมอนแบบวัดได้ (bedding mass / drape feedstock)** — tog/fill
  weight/fill power → settled loft (mm), fold compression factor, drop
  conventions, pillow ILD/slump ใต้น้ำหนักหัว, gsm+bending rigidity → Blender
  mass/bending mapping, baffle-box → billow wavelength — คำถาม 8 ข้อเต็มใน
  triage doc §2. **premise "ต่อยอด nlm-cloth-closedtube" ถูกหักล้าง** (unit
  นั้น garment-sim ล้วน + DISTILLED แล้ว, ledger:172) → unit ใหม่:
  `nlm-bedding-mass` (cross-link closed-tube เฉพาะ solver mechanics; ห้าม
  `--iterate` — ใช้ explicit asks) — queued 2026-08-04 — ชุดเสนอ C2 หัวข้อ 2;
  r5 R1-halt ตัดสิน duvet เป็น R8 drapery โอน "reads as folded fabric" เข้า
  เฟสผ้า = trigger 2+4 ติดแล้ว. Fire: ตอนเปิดเฟส cloth/materials ก่อน bake
  แรก; ขาวัด anchor corpus (drop/stack/slump — local ฟรี) ยิงก่อนได้ทุก
  session. รับใช้ทั้ง sim และ ACQUIRE sizing (Peat แชร์ pillow collection บน
  3D Warehouse ไว้แล้ว). กติกา quarantine เดียวกัน

- [ ] **ค่าสี/สะท้อนแสงจริงของ palette ครีม-โอ๊ค-ดำ** — TOA/Beger/Jotun cream
  codes + LRV (~75-90 band) + สูตร LRV→Y→sRGB มีแหล่งอ้าง, oak veneer
  sRGB/roughness จาก scan-based libraries, powder-coat 60° GU → roughness,
  brass complex-IOR/F0, ΔE batch tolerance — คำถาม 7 ข้อเต็มใน triage doc §3.
  repo ประกาศ gap นี้เองสามที่ (color-composition.md:238,
  residential-materials.md:187, render-defaults.md §7) และ **ผลวิจัย = ไฟล์
  `--brand-palette` ที่ gate `brand_delta_e00` รอมาตลอด** + PR-promotion ของ
  bsdf-material-presets.md — notebook ใหม่: `nlm-palette-anchors` — queued
  2026-08-04 — ชุดเสนอ C2 หัวข้อ 3 (คนละมุมกับ nlm-veneer-figure — VERIFIED
  distinct). Fire: ตอนเปิดเฟส MATERIALS ของ TRN-002 ก่อน build รอบแรก; ขาวัด
  as-rendered ranges จาก anchors = local. **URL-mandatory ใน prompt** (ledger
  จับ DR กุค่าคลาสนี้มาแล้ว): ตัวเลขไม่มี URL = quarantine

- [ ] **Lighting ภาพห้องนอนที่ขายได้ — ครึ่ง practice ที่เหลือ** (ครึ่ง
  lumen/CCT ตอบแล้วใน knowledge/lighting/): ช่างภาพเปิด/หรี่ไฟชั้นไหนใน hero
  shot, dusk vs daylight, flambient/HDR, cove lm/m norms, ชั้นไหน dominate
  ภาพขาย, ทวนเลข single-source ที่ไฟล์เรา flag เอง (3:1, 20:1, 108-215 lux,
  CRI≥90), bedside practical + sconce mounting bands — คำถาม 7 ข้อเต็มใน
  triage doc §4. **ไม่ใช่ DR ใหม่** — ask notebook `79476082` (Steffy/
  Livingston/ERCO/IES, 315 sources) สำหรับ verification+cove และ `a5a43395`
  (มี Shulman+Birn) สำหรับ photographer-balance — queued 2026-08-04 — ชุดเสนอ
  C2 หัวข้อ 4; สี่รอบ downlight-count ปิดเป็น clay-artifact แล้ว (ไม่ใช่ gap
  ความรู้). Fire: ตอนเปิดเฟส LIGHT ของ TRN-002 (เจ้าของ debt ใน spec
  `downlight_table`); ขาวัด practical:ambient จาก anchor pool = local ยิงก่อน
  ได้. คำตอบลง GAP list ของ residential-lighting.md ไม่เปิด unit ใหม่;
  statutory: mr39 = LAW เหนือทุกคำตอบ

- [ ] **ภาษากล้องของ interior sales photography** — per-room-type focal/
  height/shift presets สำหรับโปรเจกต์ไม่มี target — คำถาม 8 ข้อเต็มใน triage
  doc §5. **ลำดับพาหนะ: วัดก่อนวิจัย** — (1) กวาด 704 anchors ด้วย
  trn002_lines.py+trn002_station.py (มีแล้ว พิสูจน์สองครั้ง; local; ตรวจ
  ค่าคงที่ eye 1.15m [n=1] กับ shift_y −0.10 [n=0] เป็นครั้งแรก; per-room-type
  รอ designer กรอก room_type — เครื่องห้าม assign) (2) practitioner ask ขนาน
  (3) NLM DR ใหม่เฉพาะ why/when ที่ corpus ตอบไม่ได้ — เลขเลนส์เข้า ledger
  render-quality.md §4 ห้าม merge เป็น corroboration; ห้าม re-ask a5a43395
  (camera turns spent, ledger 81/127) — notebook ใหม่ (deferred):
  `nlm-camera-language` — queued 2026-08-04 — ชุดเสนอ C2 หัวข้อ 5. Fire: ขาวัด
  = idle slot หลัง TRN-002 ปิด; DR = กล้อง no-target ตัวแรก (โปรเจกต์ถัดไป
  04_visualization หรือ beauty pass ใหม่ของ PRJ-2026-002)

- 2026-08-04 **REROUTE, not a queued question** — ข้อ 6 ของชุดเสนอ C2 (asset
  source map + แบรนด์เฟอร์นิเจอร์ไทย) ไม่เข้าคิว NLM: ~70% ตอบแล้ว และเช็คลิสต์
  ของผู้เสนอพลาด prior DR ที่ใกล้กว่า —
  `docs/research/2026-07-11-furniture-sourcing-DR.md` จัดอันดับร้านไทยตาม
  published dimensions พร้อมลิสต์ 6 แบรนด์ที่ยังไม่เช็ค (SB/Modernform/Koncept/
  Boonthavorn/Winner/IKEA TH) ไว้แล้ว; DR กุ licence/ราคาในคลาสนี้มาแล้วสองครั้ง
  (structural, ไม่ใช่ preference) → เส้นทางที่ถูก: practitioner ask ผ่าน owner +
  WebFetch ทวนต่อแบรนด์ตาม tracer pattern 07-11, stage เป็น extension ผ่าน
  `_inbox/2026-08-01-sourcing-rule-change-knowledge-correction.md`; claim 07-12
  "ไม่มีร้านไทยแจก 3D" = hypothesis ยังไม่เคย verify ต่อแบรนด์. Fire: R8
  acquisition fail เป็น DECLARED GAP หรือ FF&E cycle ถัดไปชน Thai SKU. รายละเอียด
  เต็ม: triage doc §6

- 2026-08-01 **AUDIT GAP, not a queued question** — `scripts/inbox_audit.py`
  `classify()` whitelists `knowledge/_inbox/nlm-design-systems/` by name, but
  CLAUDE.md prescribes `_inbox/nlm-<topic>/` generally. Every DR staged by the
  documented process therefore lands in UNCLASSIFIED + PROVENANCE-ORPHAN:
  nlm-backlit-stone, nlm-cloth-closedtube, nlm-process-rules, nlm-veneer-figure
  (4 units, 8 of the audit's 11 integrity failures). The staging is correct and
  the CLASSIFIER is behind the convention. NOT FIXED HERE: inbox_audit.py is
  uncommitted-modified by a parallel session and belongs to that lane.
