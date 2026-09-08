# ตัวเลขแสงที่ติดผิดที่ / Lighting values attached to the wrong quantity — correction record

> PROVENANCE: distilled 2026-08-08 from
> `knowledge/_inbox/nlm-2026-08-08-corpus-asks/NLM_lighting_ask.md` — NotebookLM
> notebook `79476082-dfe5-4842-8daf-d78c9249f939` ("INTERIOR-AI design lighting
> rendering", 315 sources), single ask, attribution in
> `knowledge/_inbox/nlm-2026-08-08-corpus-asks/qa-history.json`.
> **TIER: REFERENCE.** This file corrects the ATTRIBUTION of REFERENCE numbers
> using another REFERENCE answer. No value here is Authority and none may gate a
> deliverable on its own; `knowledge/codes-th/` outranks every line.

## Why this file exists, and why it is a table rather than an edit

Five lighting numbers in this vault were checked against a 315-source corpus and
**four came back attached to the wrong quantity.** Not invented — every one is a
real published figure. Each was simply carried into a slot it does not describe,
which is the failure mode a citation cannot catch: the number is right, the
source is real, and the sentence around it is wrong.

They are NOT silently overwritten here, for two reasons.

1. **A REFERENCE answer does not get to overwrite a REFERENCE answer by fiat.**
   Both sides are DR output. What is defensible is recording BOTH readings with
   their sources and saying which one the studio will act on — which is what the
   table does.
2. **Three of them are live in code.** `pipeline/scripts/element5_lighting.py:661,667`
   and `pipeline/scripts/build_room.py:3808` treat **3:1** as a focal-ratio FLOOR,
   and `pipeline/scripts/dimensional_rules.v0.2.json → lighting.cri_min = 90` is
   loaded by `clearance_check.py` and `lighting.py`. Changing those changes how
   every future frame is lit and judged. **That is a render-affecting decision and
   therefore an owner gate (R3), not a distillation edit.** The correction is
   recorded now so the decision can be made on numbers; the knobs are not moved.

## The table

| # | value | our tier said it was | the corpus says it is | source named |
|---|---|---|---|---|
| a | **3 : 1** | accent : ambient ratio | **task area : its immediate surround**, to prevent eye strain. Accent : ambient is **5 : 1** | Gary Gordon, *Interior Lighting for Designers*, 5th ed.; 5:1 from *Cultural Expressions in Lighting Design* |
| b | **20 : 1** | max luminance ratio within the field of view | **fenestration : adjacent interior surface** (or luminaire : adjacent). Field of view is **< 40:1** | *Interior Lighting for Designers*, 5th ed. |
| c | **108–215 lux** (10–20 fc) | bedroom GENERAL ambient | **hotel-bedroom READING**. IES bedroom ambient is **6–15 fc ≈ 65–162 lux** | *IES Recommended Lighting Levels Guide*; *Lighting Solutions for Residential Projects* |
| d | **323–538 lux** (30–50 fc) | bedside reading | the **kitchen general** standard. Reading areas are **20–50 fc ≈ 215–538 lux**; bedroom reading task up to **40 fc ≈ 430 lux** | *Lighting Solutions for Residential Projects* |
| e | **CRI ≥ 90** | residential professional floor | **82 CRI** is the stated minimum for occupied interiors; **> 80** already counts as "high colour rendering". ≥ 90 is not supported as a general requirement | *Interior Lighting for Designers*, 5th ed.; *Colour and Lighting in Interiors* |

Row (d) is the weakest of the five: the corpus **does not address** 323–538 lux
for bedside reading either way, so this is an absence of support, not a
contradiction. Recorded as unsupported rather than wrong.

## What this means for the two ratios that read as one thing

(a) and (b) share a shape worth naming, because it is the same shape twice: a
ratio is meaningless without **both** of its terms, and in each case the vault
kept the number and swapped a term. `3 : 1` and `5 : 1` are both true — of
different pairs of surfaces. A luminance ratio recorded without naming what is
being divided by what is not a value, it is a digit.

## Sites carrying the affected numbers (pointer, not a rewrite)

- `knowledge/lighting/lumen-method-and-fixture-placement.md` §2 table rows
  *Bedroom general* and *Bedroom bedside reading*; §3 **CRI ≥ 90**
- `knowledge/lighting/residential-lighting.md` — CRI floor pointer, and the
  design-illuminance pointer block
- `knowledge/rendering/cycles-lighting-camera-presets.md` — accent : ambient
  ≈ 3 : 1 and the 20 : 1 ceiling
- `knowledge/brand-standards/render-quality.md` — accent : ambient ~3 : 1

## Open, and deliberately not closed here

- **The owner gate:** does the focal-ratio floor in `element5_lighting.py` move
  from 3:1 to 5:1, and does `cri_min` move from 90 to 82? Both change output.
- The corpus that answered this (`79476082`) is a different notebook from
  `a5a43395`, which is the one carrying **11 of the studio's own documents** among
  its sources. This answer is therefore not self-reference — but every value ever
  staged from `a5a43395` still owes that audit.
