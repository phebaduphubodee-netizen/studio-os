---
title: ASA มาตรฐานการเขียนแบบก่อสร้าง พ.ศ. 2554 — Layer/pen verification notes
tier: REFERENCE (raw verification trail; distilled → knowledge/classifications/thai-cad-layers-asa2554.md)
source: ASA (สมาคมสถาปนิกสยามฯ) standard PDF, 270 pp., downloaded 2026-07-06 from
  https://engfanatic.tumcivil.com/tumcivil_1/media/ASA/ASA_CAD_std_2554.pdf
  local copy: C:/Users/teza_/studio-datasets/standards/ASA_CAD_std_2554.pdf (outside repo, not committed)
verified_by: direct text extraction from the PDF's own บทที่ 6 ระบบ Layer tables (PDF pages 79–80,
  96, 98, 100–101, 109 — zero-indexed fitz pages), this session; rows below are CONDENSED
  transcriptions (descriptions glossed, columns reordered) — every layer/pen/color NUMBER was
  checked against the raw extracted text, but the wording is not a verbatim quote
status: DISTILLED 2026-07-06 (same session) → knowledge/classifications/thai-cad-layers-asa2554.md
---

# What was verified (and what the web research got slightly wrong)

The 2026-07-06 paired-2D/3D research record (docs/research/2026-07-06-paired-2d3d-backlearn.md)
carried the UNVERIFIED claim: "glass lives on A-GLAZ-FULL at pen 0.25 — deliberately thinner than
walls". Verified against the primary PDF:

**CONFIRMED rows (บทที่ 6, format: layer / pen mm / ACI color / ltype):**
- A-GLAZ-FULL 0.25/135 — ผนัง/แผงกั้นกระจกความสูงชนโครงสร้าง (curtain wall → A-WALL-CWMG)
- A-GLAZ-PRHT 0.25/115 — หน้าต่าง/แผงกั้นความสูงไม่ชนโครงสร้าง; A-GLAZ-SILL 0.18/54; A-GLAZ-SYMB 0.25/225; A-GLAZ-IDEN 0.25/15
- A-WALL-FULL-EXTR **0.35**/71 (ผนังภายนอก); A-WALL-FULL-INTR **0.25**/35 (ผนังภายใน)
- A-WALL-CWMG 0.25/155 (curtain wall + โครง); A-WALL-FIRE 0.35/11; A-WALL-CNTR 0.18/194 CHAIN
- A-DOOR-FULL 0.25/115 (กรอบบาน+แนววงสวิง); A-DOOR-PRHT 0.35/131
- A-FURN-FIXT 0.25/245 (built-in); A-FURN-FREE 0.25/215 (เคลื่อนย้ายได้); A-FURN-PLNT 0.25/115 (ต้นไม้ กระถางต้นไม้)
- A-FLOR-WDWK 0.25/35 (งานไม้ประกอบในที่ ตู้ เคาน์เตอร์); A-FLOR-OPNG 0.13/138 **DASHED** (ช่องเปิดในผังพื้น)
- I-FURN-FREE 0.35/131; I-FURN-SEAT 0.35/31; I-FURN-PLNT 0.25/115 (interior discipline)
- L-PLNT-TREE **0.5**/110 (ต้นไม้, landscape discipline); L-PLNT-BUSH 0.5/110; L-PLNT-TURF 0.13/138;
  L-PLNT-TREE-LINE 0.5/150 TREEL

**CORRECTION to the research claim:** glass (0.25) is thinner than EXTERIOR walls (0.35) but EQUAL
to interior walls (0.25) and EQUAL to furniture (0.25). A grade-level tree (L-PLNT-TREE 0.5) is
DRAWN THICKER than an interior wall. Pen width alone therefore CANNOT separate glass from interior
walls or furniture even on a fully ASA-compliant sheet — the semantic carrier is the LAYER NAME +
ACI COLOR, and the F5 floor-membership carrier is the DISCIPLINE prefix (A-/I- on-structure vs
L- at-grade). This *strengthens* the structural-evidence design of pipeline/scripts/
glazing_candidates.py (pair/wall-contact/length), which never trusted width alone.

**Practice note (real sheet observed):** the PRJ-2026-002 sheet plots walls at ~0.6–0.84 pt and
glass/furniture at 0.48 pt monochrome — i.e., real Thai drafters deviate from ASA pens and may
discard colors at plot time. If a sheet DOES keep per-layer stroke colors in the PDF, the ACI
mapping above recovers layer identity for free — check stroke-RGB diversity before assuming
monochrome (lead recorded in the distilled file).

Not extracted this pass (present in the PDF, distill on demand): full บทที่ 8 linetype/cut-plane
conventions (dashed above/below-plane rules), sheet-numbering, text styles.
