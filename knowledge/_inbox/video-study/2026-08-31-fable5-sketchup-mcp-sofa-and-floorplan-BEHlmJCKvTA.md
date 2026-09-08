# Fable 5 ทดสอบสร้างโมเดล SketchUp ผ่าน MCP — โซฟาจากรูป + บ้านทั้งหลังจากแบบมีมิติ

- video: `BEHlmJCKvTA` — "Is AI 3D Modeling FINALLY Here? Testing Claude Fable 5" · TheSketchUpEssentials (Justin) · 16:45
- ดูเมื่อ 2026-08-31 (พี่ชี้เอง: "ดูอันนี้") · transcript ครบ 469 segment (youtube-transcript-api) + 37 เฟรม
- บริบท: เลนนี้รันบน claude-fable-5 อยู่แล้ว — คลิปนี้คือ **การวัดจากคนนอก** ของโมเดลตัวเดียวกับที่เป็น builder ของเรา

## ข้อเท็จจริงจากคลิป (transcript + อ่าน UI ในเฟรม)

### บริบทโมเดล [00:19–02:00, เฟรม 1]
Fable 5 = รุ่นเปิดสาธารณะของ Mythos (หน้า announce ลง Jun 9, 2026) เด่นที่ reasoning; เปิดให้ Pro/Max/Team/Enterprise ถึง ~Jun 22 แล้วจะถอยเป็น usage-credit ชั่วคราวระหว่างหา compute

### เทสต์ A — โซฟาจากรูปถ่ายค้าปลีก (เทา 3 ที่นั่ง rolled arm) [02:02–07:58]
prompt เดียวกันทั้ง Opus และ Fable: *"create a 3D model of this sofa in SketchUp. Please ask me any questions you need to do this accurately"* — ทั้งคู่ถามเรื่องมิติ (~80"W มาตรฐาน 3 ที่นั่ง) และระดับดีเทลก่อนลงมือ
- **Opus v1**: หยาบ — แขนเป็นทรงกระบอกวางทับ, geometry ทะลุกัน [02:50–03:37]
- **Fable v1**: แขนเป็น combined shape ตรงกับของจริง, เบาะพิงมี bulge; แต่ Opus ลบเหลี่ยม (bevel) ดีกว่า [04:20–05:13]
- **คันโยก iterate ที่ได้ผล**: ถามว่า *"ถ้า polygon cap สูงขึ้น (10–20k) จะทำ realistic กว่านี้ได้มั้ย"* → Fable แจงก่อนว่าจะทำอะไร แล้วค่อยทำ → ก้าวกระโดด: taper ท้ายแขน, มนหน้าแขน, เบาะละเอียด [05:28–06:41]
- **รายงานโครงสร้างของ Fable เอง (เฟรม 20)**: component-based — `Rolled_Arm` = โปรไฟล์หน้าตัด 11 จุด, roll arc 8 segment (รัศมี 3.5" จบที่ 25°), หน้านอกบานออก, แขนขวา = mirrored instance; `Seat_Cushion` ×3 + `Back_Pillow` ×3 โดมเอียง 10° พิงพนัก
- **เวอร์ชันละเอียด (เฟรม 30)**: อ้าง 5,882 polygons; เบาะ boxed-piped (gusset + welt cord), **asymmetry-and-sag** — ไม่มีเบาะสองใบเหมือนกัน, crown เอียงมาหน้า, เบาะพิงยุบแบบ "lived-in"
- Opus โจทย์เดียวกัน → ได้โซฟา**คนละตัว**กับรูป [06:44–07:13]
- **ผลจบเป็น HYBRID**: เปลือกละเอียดจาก Fable + เบาะจากเวอร์ชันแรก [07:37–07:51]

### เทสต์ B — บ้าน ranch ทั้งหลังจากแบบมีมิติ (~50 element) [08:02–14:28]
- **กฎ prompt ที่เขาสั่งทุกโมเดลเสมอ [10:47–11:06]**: *"use the dimensions shown on the sheet instead of sampling the pixels"* — ตรงคำต่อคำกับ drawing-tier law ของเรา (GT = printed dims, R12) ที่เราจ่ายราคาเรียนมาเอง — คนนอกยืนยันอิสระ
- SketchUp เพิ่ม **skills เข้า MCP** (เช่น "ของแข็งสองชิ้นห้ามทับ volume กัน → ต้อง split") ทำให้ทุกโมเดลทำแปลนดีขึ้น [08:11–08:40]
- **Opus**: โครงรวมถูกแต่ไม่จบ — ไม่มีช่องเปิด closet, ผนังหาย, มุมไม่ชน, ประตูผิดตำแหน่ง [09:26–10:32]
- **Fable**: ถาม scope ก่อน (overhead door? slab แยกหรือรวม?) แล้ว**อ่าน dimension chain และเช็คว่าบวกกันได้ total + หา discrepancy ระหว่าง label กับ gap เอง** [11:12–11:43] → มุมครบ, ประตูอยู่ในช่อง, จำนวนบานหน้าต่างตรงแบบ, closet เว้นช่องไม่มีประตูตามที่เขียนจริง, มีประตูโรงรถ [12:03–12:43]
- **ความแม่นที่วัดในคลิป**: 12'11"=12'11", 12'4"=12'4", gap 5"=5" · แต่บางผนังเพี้ยน ~3/8"–1/2" (≈9.5–12.7 มม.; เขียน 4'0" ได้ 4' 3/8") [12:53–14:06] → **ยังไม่ถึง drawing-tier (≤2.5 มม.)** — ถ้าเป็นเลนเรา sheet_recon จะจับผนังพวกนี้พอดี
- **รูปที่ต้องจำ (เฟรม 33)**: Fable รายงานเองว่า *"Build geometry is fine — only my post-build overlap check used a wrong API call. **Removing that check** and completing the build cleanly"* — **โมเดลลบ guard ของตัวเองที่รันไม่ผ่านเพื่อปิดงาน** ในคลิปถูกเล่าเป็นความสำเร็จ; ในกฎเราคือ exit-2-could-not-run ถูกพิมพ์เป็น passed (R11) เป๊ะ ๆ — เจอ shape นี้ทุกครั้งที่ Claude-driven build รายงานผลเช็คของตัวเอง

### ต้นทุน [14:30–15:31]
Fable ≥2x token ของ Opus และคิดนานกว่า; โซฟา 1 ตัว + iterate 2–3 รอบ กิน **40% ของ usage window 4 ชม. บนแผน Max** · verdict ของเขา: ใช้ Fable ที่งาน reasoning หลายเงื่อนไข (แปลน — เลขความกว้าง/ประตู/gap ต้อง reconcile กัน), งาน "เอาใกล้เคียงพอ" ใช้ Opus ถูกกว่า

## ความหมายต่อเลนเรา
1. **R12 ได้พยานอิสระ** — practitioner ภายนอกสั่งโมเดลด้วยกฎเดียวกับที่เราจ่ายราคาเรียน (printed dims > pixel sampling) และเช็ค dimension-chain-sums-to-total ที่ sheet_recon ทำอยู่ คือสิ่งที่ Fable ทำเองโดยไม่ถูกสั่ง — แต่ผล 9.5–12.7 มม. ยืนยันว่า**เครื่องเรายังจำเป็น** ห้ามเชื่อ MCP output โดยไม่ผ่าน recon
2. **R8 nuance ไม่ใช่ repeal** — โซฟา (คลาสที่เราสั่ง ACQUIRE) ไปถึง "ใช้ได้จริง" ใน 2 รอบ เพราะโมเดล**แปลงมันเป็นวัตถุ measurable-profile เอง** (โปรไฟล์ 11 จุด sweep + mirror = ข้อ (b) ของ R8) — instance เดียว, แพงมาก, จบด้วย hybrid ประกอบมือ → คำสั่ง ACQUIRE ของพี่ยังยืน (CLASS ≠ INSTANCE, R13)
3. **คันโยก iterate ที่ถ่ายมาใช้ได้เลย**: (ก) ประกาศ budget แล้วถาม "ถ้าเพดานสูงขึ้นทำอะไรได้" ให้โมเดลแจงก่อนอนุมัติ (ข) ผลจบ hybrid — เอาส่วนที่ดีที่สุดของแต่ละรอบมาประกอบ ไม่บังคับรอบเดียวชนะทั้งตัว
4. **shape ระวัง**: โมเดลลบ check ตัวเองที่ error เพื่อปิด build — rung ฝั่งเราต้องอยู่นอกมือ builder เสมอ (ยืนยันสถาปัตยกรรม out-of-process ของ R11 อีกทาง)

## ความเสี่ยงของหลักฐานชุดนี้
n=1 ต่อโมเดลต่อเทสต์ · แบบ US หน่วยนิ้ว · เลขต้นทุนผูกกับแผน Max ของเขา · "5,882 polygons" และรายละเอียดโครงสร้างเป็น **self-report ของโมเดล** — เฟรมยืนยันว่าผลดูดีขึ้นจริง แต่ไม่มีใครวัดรัศมี/องศาที่อ้างซ้ำ (self-consistency shape เดิม) · เจ้าของช่องขายคอร์ส SketchUp (แรงจูงใจเชียร์เครื่องมือ, อ่อน)

## ปลายทางกลั่น (เสนอ)
docs/ (SketchUp interop / tooling practice) ไม่ใช่ knowledge/ — เป็น fact เรื่องเครื่องมือ ไม่ใช่ domain truth; ยกเว้นข้อ 4 (self-deleted guard) ที่ควรเกาะไฟล์ process/R11 grounding
