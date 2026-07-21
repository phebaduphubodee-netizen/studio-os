# Thai CAD layer semantics — ASA มาตรฐานการเขียนแบบก่อสร้าง พ.ศ. 2554 (บทที่ 6 ระบบ Layer)

**Source (verified against the primary PDF, 2026-07-06):** สมาคมสถาปนิกสยามฯ (ASA), มาตรฐานการ
เขียนแบบก่อสร้าง ฉบับปี พ.ศ. 2554, บทที่ 6 ระบบ Layer — verification trail (raw extraction +
local PDF path) in `knowledge/_inbox/asa-cad-std-2554-verification.md`, rows at `:21-30`,
extracted from PDF pages 79–80, 96, 98, 100–101, 109 (zero-indexed). Cited below as
*trail :N* (same file, that line).
**Transcription caveat (inherited from the trail, `:7-10`):** every layer name / pen / ACI
number below was checked against the PDF's raw extracted text, but the *descriptions* are
glossed and the columns reordered — the wording is **not** a verbatim quote of the standard;
the trail calls its own rows CONDENSED transcriptions of บทที่ 6 (trail :8-9), not the whole
chapter.
**Tier:** professional standard (NOT statutory — codes-th still outranks for law).
**Why this file exists:** the 2D→3D reader's F4/F5 failure classes (thin glass boundaries,
which-floor membership) are encoded by Thai drafting convention in LAYER + COLOR + DISCIPLINE,
not in what the thick-stroke geometry shows. This is the citable symbol→meaning table.

## The load-bearing rows (pen mm / ACI color)

All rows from `knowledge/_inbox/asa-cad-std-2554-verification.md:21-30`.

### A- discipline (architectural)

| Meaning | Layer | Pen | Color | Note |
|---|---|---|---|---|
| ผนังภายนอก (เต็มความสูง) | A-WALL-FULL-EXTR | **0.35** | 71 | the THICKEST wall pen |
| ผนังภายใน (เต็มความสูง) | A-WALL-FULL-INTR | 0.25 | 35 | same pen as glass + furniture |
| [our read: ผนังกันไฟ] | A-WALL-FIRE | **0.35** | 11 | same pen as an exterior wall |
| [our read: เส้นศูนย์กลางผนัง] | A-WALL-CNTR | 0.18 | 194 | **CHAIN** linetype |
| ผนัง/แผงกระจกชนโครงสร้าง | A-GLAZ-FULL | 0.25 | 135 | the TRUE-boundary glass wall |
| หน้าต่าง/แผงกั้นไม่ชนโครงสร้าง | A-GLAZ-PRHT | 0.25 | 115 | |
| Curtain wall + โครง | A-WALL-CWMG | 0.25 | 155 | explicitly split from A-GLAZ-FULL |
| [our read: ธรณีใต้หน้าต่าง] | A-GLAZ-SILL | 0.18 | 54 | |
| [our read: สัญลักษณ์งานกระจก] | A-GLAZ-SYMB | 0.25 | 225 | [our read: annotation, not fabric] |
| [our read: หมายเลข/รหัสงานกระจก] | A-GLAZ-IDEN | 0.25 | 15 | [our read: annotation, not fabric] |
| ประตู (กรอบ+วงสวิง) | A-DOOR-FULL | 0.25 | 115 | swing arc lives here |
| [our read: ประตูความสูงไม่ชนโครงสร้าง] | A-DOOR-PRHT | **0.35** | 131 | door pen ≠ A-DOOR-FULL's 0.25 |
| เฟอร์นิเจอร์ built-in | A-FURN-FIXT | 0.25 | 245 | |
| เฟอร์นิเจอร์ลอยตัว (เคลื่อนย้ายได้) | A-FURN-FREE | 0.25 | 215 | |
| ต้นไม้/กระถาง | A-FURN-PLNT | 0.25 | 115 | [our read: A- prefix ⇒ planter ON structure] |
| งานไม้ประกอบในที่ ตู้ เคาน์เตอร์ | A-FLOR-WDWK | 0.25 | 35 | built-in woodwork/counters |
| ช่องเปิดในผังพื้น | A-FLOR-OPNG | 0.13 | 138 | **DASHED** linetype |

**`[our read: …]` = OURS, not the standard's.** For the bracketed rows the trail gives a layer
name, a pen and an ACI number but **no** Thai gloss (trail :22, :24, :25) — the meaning is read
off the layer suffix. Every PEN and ACI number in the table is confirmed against the trail; the
unbracketed Meaning cells reproduce the trail's own glosses (trail :21-27, where a row carries
one).

### I- discipline (interior)

The trail lists the I- rows without a Thai gloss (`:28`); the meanings below read the
suffixes against their identically-suffixed A- counterparts (FREE = ลอยตัว/movable,
PLNT = ต้นไม้/กระถาง). SEAT has no A- counterpart — "seating" is read off the suffix alone.

| Meaning | Layer | Pen | Color | Note |
|---|---|---|---|---|
| เฟอร์นิเจอร์ลอยตัว (interior sheet) | I-FURN-FREE | **0.35** | 131 | furniture at the EXTERIOR-WALL pen |
| ที่นั่ง (interior sheet) | I-FURN-SEAT | **0.35** | 31 | ditto |
| ต้นไม้/กระถาง (interior sheet) | I-FURN-PLNT | 0.25 | 115 | on-structure planter |

### L- discipline (landscape) — the F5 at-grade tier

| Meaning | Layer | Pen | Color | Note |
|---|---|---|---|---|
| ต้นไม้ **ระดับพื้นดิน** | L-PLNT-TREE | **0.5** | 110 | landscape discipline, at grade |
| [our read: ไม้พุ่ม] | L-PLNT-BUSH | **0.5** | 110 | same pen AND same color as L-PLNT-TREE |
| [our read: สนาม/หญ้า] | L-PLNT-TURF | 0.13 | 138 | |
| [our read: แนวต้นไม้] | L-PLNT-TREE-LINE | **0.5** | 150 | **TREEL** linetype |

Same convention: the trail glosses only L-PLNT-TREE (ต้นไม้, trail :29); BUSH / TURF / TREE-LINE
carry pen + ACI + linetype but no gloss (trail :29-30), so their Meaning cells are our
suffix-read.

## What the reader may and may not infer

1. **Pen width does NOT identify glass — and 0.35 does not identify an exterior wall.** On an A-
   sheet glass (0.25) = interior wall (0.25) = A- furniture (0.25). At the heavy end, 0.35 on an
   A- sheet is shared by **A-WALL-FULL-EXTR, A-WALL-FIRE and A-DOOR-PRHT** (trail :23-25): it
   narrows a stroke to a 3-row set, it does not name an exterior wall. And a grade-level tree
   (0.5) is *thicker* than an interior wall. A width-only "thin = glazing" rule is wrong by
   standard — promotion must rest on structural evidence (see
   `pipeline/scripts/glazing_candidates.py`: pair / wall-contact / length), with width only as
   the coarse first sieve. The pen ordering itself is discipline-dependent — see rule 4 before
   using it at all.
2. **F5 floor membership is a DISCIPLINE prefix.** ต้นไม้ that belongs to the ground is
   L-PLNT-* (landscape); a planter that sits on this floor's slab is A-FURN-PLNT / I-FURN-PLNT.
   A tree symbol inside an upper-floor plan is therefore *presumptively at grade* (drawn
   through the view) unless the sheet gives planter evidence — demote + flag, never auto-place
   (this is exactly the v4 garden-trees miss).
3. **Color is a recoverable layer channel — a narrowing one, not a unique key.** ACI colors
   repeat across rows (see the collision table below), so color maps a stroke to a SMALL
   candidate set, which geometry then disambiguates (a 115 arc in a wall gap is a door swing;
   a 115 scalloped circle is a plant). A PDF plotted with colors intact still leaks most of
   the layer structure; before assuming a monochrome sheet, histogram the stroke RGBs
   (trail :41-44).
4. **RULE CORRECTION — the pen prior is broken *inside* A-, and broken again *across*
   disciplines.** There is no clean ordering *exterior wall (0.35) > interior wall = glass =
   furniture (0.25) > sills/annotation (0.18/0.13)* to lean on — not even on an A- sheet:
   - **Inside the A- discipline.** 0.35 ∈ {A-WALL-FULL-EXTR, A-WALL-FIRE, A-DOOR-PRHT} (trail
     :23-25) — a fire wall and a partial-height door carry the exterior-wall pen. And annotation
     is not confined to the thin pens: A-GLAZ-SYMB (0.25/225) and A-GLAZ-IDEN (0.25/15) sit at
     the same 0.25 as interior wall, glass and furniture (trail :22).
   - **Across disciplines.** I-FURN-FREE and I-FURN-SEAT are **0.35** (trail :28) — the same pen
     as A-WALL-FULL-EXTR. So *if the sheet carries I- layers*, a 0.35 stroke does **not** imply
     "wall".

   Resolve the DISCIPLINE — and check whether annotation layers are present — before applying any
   width prior at all. Derived from the rows above; the standard states the pens and colours, it
   states no ordering rule, on any sheet type.
5. **Real sheets deviate from ASA pens.** A real Thai construction sheet observed in-studio
   plots cut walls at ~0.6–0.84 pt and glass/furniture at 0.48 pt, monochrome — i.e. drafters
   deviate from ASA pens and may discard colors at plot time (trail :40-44). Treat
   ASA pens as a *relative ordering* prior **within a resolved discipline**, never as absolute
   thresholds; calibrate per sheet from its own histogram.
6. **Dashed = the opening layer, among the rows extracted.** A-FLOR-OPNG is the one dashed layer
   in the extracted rows, and the trail glosses it ช่องเปิดในผังพื้น = *opening / void in the floor
   plan* (trail :27). That supports low-ink-coverage demotion of dashed runs (glazing_candidates
   exposes `coverage` per run for this). The standard's full linetype / cut-plane conventions live
   in บทที่ 8, which the 2026-07-06 pass did not extract (trail :46-47) — so do not treat the three
   linetypes below as the standard's complete set, and do not assume what บทที่ 8 says a dashed
   line means in general.

## ACI color collisions (color narrows, never uniquely keys)

Facts, read straight off the rows (trail :21-30). **Pen does not break any of these five ties —
over the rows extracted so far**: every colliding pair below also shares its pen. This is the
complete collision set of the ~24 extracted rows, which the trail itself calls CONDENSED
transcriptions of บทที่ 6 (trail :8-9), not the whole chapter — the standard may collide further
rows we have not read.

| ACI | Layers sharing it | Pen(s) |
|---|---|---|
| 115 | A-GLAZ-PRHT, A-DOOR-FULL, A-FURN-PLNT, I-FURN-PLNT | all 0.25 |
| 35 | A-WALL-FULL-INTR, A-FLOR-WDWK | both 0.25 |
| 131 | A-DOOR-PRHT, I-FURN-FREE | both 0.35 — **cross-discipline** |
| 110 | L-PLNT-TREE, L-PLNT-BUSH | both 0.5 |
| 138 | A-FLOR-OPNG, L-PLNT-TURF | both 0.13 |

**Reader heuristic (OURS, not the standard's — the standard supplies no disambiguation rule):**
colour maps a stroke to the small candidate set above; geometry has to finish the job (a 115 arc
in a wall gap reads as a door swing, a 115 scalloped circle as a plant). Two cautions: for ACI 110
the standard gives L-PLNT-TREE and L-PLNT-BUSH an *identical* pen AND colour, so no layer-channel
evidence separates them at all; and for ACI 138 it names DASHED on A-FLOR-OPNG but names **no
linetype for L-PLNT-TURF** — absence of a named linetype is not a statement that the layer is
solid, so do not build a DASHED-vs-solid test on it without checking บทที่ 8.

## Linetypes named in the บทที่ 6 rows extracted so far

| Linetype | Layer | Trail's gloss |
|---|---|---|
| DASHED | A-FLOR-OPNG 0.13/138 | ช่องเปิดในผังพื้น = opening / void in the floor plan (trail :27) |
| CHAIN | A-WALL-CNTR 0.18/194 | *none given* (trail :24) |
| TREEL | L-PLNT-TREE-LINE 0.5/150 | *none given* (trail :30) |

**Reader heuristic (OURS, off the suffixes — the trail glosses neither row):** CHAIN on
A-WALL-CNTR reads as a wall centreline — a *reference* line, not fabric; never promote it to
geometry. TREEL on L-PLNT-TREE-LINE reads as a line of trees, at grade (L- = the at-grade
discipline, rule 2).

## Open extraction TODO (against the primary PDF, not this repo)

The 2026-07-06 pass read บทที่ 6 only. That pass did not extract (trail :46-47): **บทที่ 8**
linetype / cut-plane conventions (which the trail describes as the dashed above-/below-plane
rules), **sheet numbering**, and **text styles**. Rule 6 above is therefore provisional on the
linetype question.

Related: `knowledge/classifications/plan-reading-conventions.md` (furniture-symbol facing +
line-weight reading),
`docs/research/2026-07-06-paired-2d3d-backlearn.md` §4 (the full symbol codification table).
