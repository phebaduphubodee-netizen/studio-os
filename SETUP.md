# SETUP — Phase 0 (สัปดาห์ 1–2) · เป้าหมาย: M0.1 + M0.2

อ้างอิง: STUDIO-OS Implementation Blueprint v1.0 §13 (Phase 0) และ §14 (M0.1, M0.2)

## 0) เตรียมเครื่อง
ต้องมี: **Git**, **Git LFS**, **Python 3.10+**, **Claude Code**, บัญชี **GitHub** (private repo)

- Windows: แนะนำทำงานใน **WSL2 (Ubuntu)** — hooks เป็น bash/python3 จะทำงานตรงตามชุดนี้ทันที
  (ComfyUI/FLUX ใน Phase 2 รันบน Windows native ได้ตามปกติ ไม่เกี่ยวกับ repo นี้)
- ติดตั้ง LFS ครั้งแรกในเครื่อง: `git lfs install`
- เช็ค: `git --version && git lfs version && python3 --version && claude --version`

## 1) สร้าง repo (ลำดับสำคัญมาก — .gitattributes ต้องเข้าก่อนไฟล์ binary ใด ๆ)
```bash
unzip studio-os-starter.zip && cd studio-os-starter
git init -b main
git lfs install
git add .gitattributes            # ← ต้องเป็น commit แรก ๆ เสมอ
git add -A
git commit -m "STUDIO-OS Phase 0: foundation, guardrails, templates"
# สร้าง private repo บน GitHub แล้ว:
git remote add origin git@github.com:<you>/studio-os.git
git push -u origin main
```

## 2) พิสูจน์ guardrails = M0.1
```bash
bash scripts/test_guards.sh        # ต้องขึ้น "ALL GREEN" (10/10)
```
จากนั้นทดสอบของจริง: เปิด `claude` ในโฟลเดอร์นี้ แล้วลองสั่ง 3 อย่างนี้ —
1. "run `rm -rf /tmp/x` for me" → ต้องถูก hook block
2. "edit qa/thresholds.yaml, change brisque to 100" → ต้องถูก block
3. "append a note to docs/strategy.md" → ต้องผ่านปกติ
บันทึกผล (วันที่ + ผ่าน/ไม่ผ่าน) ลง `docs/strategy.md` หัวข้อ Security audit findings

## 3) ย้าย studio-vault v2.2 → knowledge/  (เริ่ม M1.1)
ทำตาม `knowledge/README.md`: **copy ตรง ๆ เข้าโฟลเดอร์ที่ map ไว้ ยังไม่ต้องจัดโครงใหม่ ยังไม่ต้อง index**
กฎหมาย/ข้อกำหนดไทย (พ.ร.บ.ควบคุมอาคาร, กฎกระทรวง, ระเบียบนิติฯ คอนโด) → `knowledge/codes-th/`
แล้ว commit: `git add knowledge && git commit -m "migrate studio-vault v2.2 content"`

## 4) ทดสอบ scaffold = M0.2
```bash
python3 scripts/scaffold_project.py PRJ-2026-001 test-run --client C-000
ls projects/PRJ-2026-001_test-run/          # ต้องเห็น 00_intake … 08_handover
cat projects/PRJ-2026-001_test-run/00_intake/_contract.md
git add -A && git commit -m "test scaffold" 
```
(โปรเจกต์ test ลบทิ้งได้ภายหลังผ่าน git — อย่าใช้ rm -rf เอง ให้ทำผ่าน git rm)

## 5) MCP ขั้นต่ำ (option ใน Phase 0, จำเป็นใน Phase 1)
```bash
cp .mcp.json.example .mcp.json     # เปิด vault server แบบ read-only
```

## เกณฑ์ผ่าน Phase 0 (จาก blueprint §14)
- [ ] M0.1: guard test ALL GREEN + ทดสอบสดใน Claude Code ทั้ง 3 เคสตามข้อ 2
- [ ] M0.2: clone ใหม่ < 2 นาที (ไม่รวม assets), binary เป็น LFS pointer, scaffold ทำงานคำสั่งเดียว
- [ ] studio-vault ถูก copy เข้า knowledge/ ครบ (นับไฟล์เทียบต้นทาง)

## ถัดไป → Phase 1 (สัปดาห์ 3–5)
Directory-level CLAUDE.md + retrieval index + skills 5 ตัวแรก + `codes-th` เป็น Authority tier
ดู blueprint §13 Phase 1 / milestones M1.1–M1.3
