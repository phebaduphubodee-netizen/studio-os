# Thai CAD layer semantics — ASA มาตรฐานการเขียนแบบก่อสร้าง พ.ศ. 2554 (บทที่ 6 ระบบ Layer)

**Source (verified against the primary PDF, 2026-07-06):** สมาคมสถาปนิกสยามฯ (ASA), มาตรฐานการ
เขียนแบบก่อสร้าง ฉบับปี พ.ศ. 2554, บทที่ 6 — layer tables quoted verbatim in
`knowledge/_inbox/asa-cad-std-2554-verification.md` (raw trail + local PDF path).
**Tier:** professional standard (NOT statutory — codes-th still outranks for law).
**Why this file exists:** the 2D→3D reader's F4/F5 failure classes (thin glass boundaries,
which-floor membership) are encoded by Thai drafting convention in LAYER + COLOR + DISCIPLINE,
not in what the thick-stroke geometry shows. This is the citable symbol→meaning table.

## The load-bearing rows (pen mm / ACI color)

| Meaning | Layer | Pen | Color | Note |
|---|---|---|---|---|
| ผนังภายนอก (เต็มความสูง) | A-WALL-FULL-EXTR | **0.35** | 71 | the THICKEST wall pen |
| ผนังภายใน (เต็มความสูง) | A-WALL-FULL-INTR | 0.25 | 35 | same pen as glass + furniture |
| ผนัง/แผงกระจกชนโครงสร้าง | A-GLAZ-FULL | 0.25 | 135 | the TRUE-boundary glass wall |
| หน้าต่าง/แผงกั้นไม่ชนโครงสร้าง | A-GLAZ-PRHT | 0.25 | 115 | |
| Curtain wall + โครง | A-WALL-CWMG | 0.25 | 155 | explicitly split from A-GLAZ-FULL |
| ประตู (กรอบ+วงสวิง) | A-DOOR-FULL | 0.25 | 115 | swing arc lives here |
| เฟอร์นิเจอร์ built-in | A-FURN-FIXT | 0.25 | 245 | |
| เฟอร์นิเจอร์ลอยตัว | A-FURN-FREE | 0.25 | 215 | |
| ต้นไม้/กระถาง **บนอาคาร** | A-FURN-PLNT | 0.25 | 115 | planter ON structure = furniture |
| ต้นไม้ **ระดับพื้นดิน** | L-PLNT-TREE | **0.5** | 110 | landscape discipline, at grade |
| ช่องเปิดในผังพื้น | A-FLOR-OPNG | 0.13 | 138 | **DASHED** linetype |
| ธรณีใต้หน้าต่าง | A-GLAZ-SILL | 0.18 | 54 | |

## What the reader may and may not infer

1. **Pen width does NOT identify glass.** Glass (0.25) = interior wall (0.25) = furniture
   (0.25); only exterior walls (0.35) stand out, and a grade-level tree (0.5) is *thicker*
   than an interior wall. A width-only "thin = glazing" rule is wrong by standard — promotion
   must rest on structural evidence (see `pipeline/scripts/glazing_candidates.py`: pair /
   wall-contact / length), with width only as the coarse first sieve.
2. **F5 floor membership is a DISCIPLINE prefix.** ต้นไม้ that belongs to the ground is
   L-PLNT-* (landscape); a planter that sits on this floor's slab is A-FURN-PLNT / I-FURN-PLNT.
   A tree symbol inside an upper-floor plan is therefore *presumptively at grade* (drawn
   through the view) unless the sheet gives planter evidence — demote + flag, never auto-place
   (this is exactly the v4 garden-trees miss).
3. **Color is a recoverable layer channel — a narrowing one, not a unique key.** ACI colors
   repeat across rows (115 alone serves A-GLAZ-PRHT, A-DOOR-FULL and A-FURN-PLNT), so color
   maps a stroke to a SMALL candidate set, which geometry then disambiguates (a 115 arc in a
   wall gap is a door swing; a 115 scalloped circle is a plant). A PDF plotted with colors
   intact still leaks most of the layer structure; before assuming a monochrome sheet (like
   PRJ-2026-002, which plots everything dark), histogram the stroke RGBs.
4. **Real sheets deviate from ASA pens.** The observed real sheet uses ~0.6–0.84 pt for cut
   walls and 0.48 pt for glass/furniture. Treat ASA pens as the *relative ordering* prior
   (exterior wall > interior wall = glass = furniture > sills/annotation), never as absolute
   thresholds; calibrate per sheet from its own histogram.
5. **Dashed = not-in-plane.** A-FLOR-OPNG (ช่องเปิด) is the standard's own dashed layer —
   dashes on a plan mark above/below-cut-plane or void, supporting low-ink-coverage demotion
   of dashed runs (glazing_candidates exposes `coverage` per run for this).

Related: `plan-reading-conventions.md` (furniture-symbol facing + line-weight reading),
`docs/research/2026-07-06-paired-2d3d-backlearn.md` §4 (the full symbol codification table).
