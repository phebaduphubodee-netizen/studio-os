# Brand-Color & Identity Verification — มาตรฐานวิธีตรวจสีแบรนด์และโลโก้ (METHOD standard)

> PROVENANCE: distilled from the DR report
> `knowledge/_inbox/id-project-corpus/Automated Production QA Scoring Systems.pdf`
> pp. 8–9 (method + perception bands), p. 12 (Matrix 1, Brand QA row).
> Date 2026-07-03. Tier: REFERENCE (studio METHOD standard, not law, not a gate).
> The PDF's own citation markers (⁵⁵, ⁵⁷, ⁵⁸, ⁶¹ …) resolve only inside that
> report; they are reproduced here as-is for traceability.

> ## ⚠ BOXED WARNING — เกณฑ์ตัวเลข "ไม่ได้" มาจาก PDF ฉบับนี้ / this source's band bounds are UNRECOVERABLE
>
> The source PDF's threshold expressions were exported as truncated equation
> images: every right-hand operand is blank in the file itself (verified by
> re-rendering the embedded images, 2026-07-03; the p.9 band table's "ΔE00 Score
> Range" column and the p.12 Matrix-1 Brand QA row's two THRESHOLD CELLS (Hard
> Gate / Soft Gate) are blank in the text layer too). Recovered fragments only:
> band-2 lower bound `1.0 −` (p.9 table) and
> Matrix 1 soft-gate fragment `2.0 < x ≤ [blank]` (p.12). **The METHOD below is
> durable; the NUMBERS are not in this source.** The studio's ΔE00 bands are
> adopted independently of this PDF — `qa/thresholds.yaml:19`
> (`delta_e00: { pass_max: 1.0, warn_max: 2.0 }`) — and this file must never be
> cited as their source. Do not backfill any further numbers from model memory;
> gate values change only via a `qa/thresholds.yaml` PR.

**Authority cross-ref:** nothing in this file is statutory. Any legal
requirement (e.g. signage, safety colors) is governed by `knowledge/codes-th/`,
which outranks this file. Gate values live only in `qa/thresholds.yaml`
(PR-only); this file defines the procedure, never the numbers.
The Brand QA pillar row of the QA taxonomy is also covered in
`knowledge/classifications/qa-dimensions.md`.

## Scope — ขอบเขต

Binds automated Brand QA whenever a client logo, brand color, or brand asset
appears in a studio output (renders with branded goods, moodboards, client-deck
graphics). Brand guidelines demand colorimetric and geometric conformance, not
"looks similar to the human eye" (Automated Production QA Scoring Systems.pdf
p.8, marker 55).

## 1. Core rule — ห้ามเทียบสีใน RGB / never compare brand colors in RGB

- RGB comparison is inadequate for Brand QA: the RGB space is **perceptually
  non-uniform** and highly dependent on the dynamic range and calibration of
  the display hardware (Automated Production QA Scoring Systems.pdf p.8,
  marker 57).
- Perceptual basis: retinal cone density gives higher tolerance for variation
  near 560 nm (green) than near 400 nm (blue); MacAdam ellipses on the
  chromaticity diagram map these thresholds — equal RGB distances are not
  equal perceived differences (pdf p.8, marker 61).
- Studio rule: all brand-color scoring runs in **CIELAB** with the
  **CIEDE2000 (ΔE00)** difference formula (pdf p.8, marker 57).

## 2. Method — ขั้นตอนตรวจ (segment → sample → CIELAB D65 → ΔE00)

Pipeline procedure as given by the source (Automated Production QA Scoring
Systems.pdf p.9, marker 59), color-managed under a framework such as
OpenColorIO:

1. **Segment / แยกวัตถุแบรนด์:** isolate the brand asset (logo, brand-color
   region) with a segmentation model.
2. **Sample / เก็บพิกเซล:** sample pixel values from the isolated region.
3. **Convert / แปลงสี:** convert samples to CIELAB assuming a standardized
   illuminant — **D65**.
4. **Score / คำนวณ:** compute the **ΔE00** distance against the master brand
   guideline values.

CIEDE2000 details worth knowing when implementing (pdf pp.8–9, markers 58–59):

- Decomposes distance into Lightness (ΔL′), Chroma (ΔC′), Hue (ΔH′) with
  location-dependent weighting functions and a hue-rotation term correcting
  the problematic blue region around the 275° hue angle.
- Parametric weighting factors are adjusted based on specific viewing conditions,
  "though they default to 1 for standard illumination" (pdf p.8, marker **59** —
  marker 58 covers only the preceding weighting-function / ΔL′ΔC′ΔH′ / 275°
  hue-rotation sentence).
- Not perfectly continuous: a minor discontinuity exists when two hues are
  exactly 180° apart, bounded by **0.274** for pairs under 5 CIELAB units
  apart (pdf pp.8–9, marker 58) — irrelevant at pass-band magnitudes, worth a
  unit test if scores cluster near a gate.

## 3. Three-band gate — เกณฑ์ 3 ระดับ (bounds MISSING-IN-SOURCE; studio bands adopted elsewhere)

The source defines a three-band ΔE00 disposition (pdf p.9, markers 58, 61).
**Its band boundaries are blank — see BOXED WARNING.** The "studio adopted"
column below does NOT come from this PDF; it is `qa/thresholds.yaml:19`,
reproduced here only so a reader knows the live bands exist.

| Band | ΔE00 range (this PDF) | studio adopted (`qa/thresholds.yaml:19`) | Visual perception (pdf p.9) | Pipeline status (pdf p.9) |
|---|---|---|---|---|
| 1 | `< ` **[MISSING-IN-SOURCE]** | ≤ 1.0 → pass | Imperceptible difference to the human eye | Perfect compliance; passes **hard gate** |
| 2 | `1.0 – ` **[upper bound MISSING-IN-SOURCE]** | 1.0 – 2.0 → warn | Just Noticeable Difference (JND) under close observation | Acceptable; passes **soft gate** with warning logs |
| 3 | `> ` **[MISSING-IN-SOURCE]** | > 2.0 → fail (non-compliant) | Clearly perceptible color shift | Non-compliant; fails **hard gate** |

- Recovered fragments: band-2 lower bound **1.0** (p.9 table; that band's
  Pipeline Status cell reads "Acceptable; Passes Soft Gate with warning logs⁵⁸");
  Matrix 1 Brand QA row (p.12) shows hard gate `≤ [blank]`, soft gate
  `2.0 < x ≤ [blank]`. Both LEFT-hand operands are present in the source and
  both mark where the soft/warn band BEGINS — and they disagree: **1.0 on p.9 vs
  2.0 on p.12**. That is an internal inconsistency inside this one source, and it
  does not depend on the blanks (the blanks are the two bands' UPPER bounds).
  Caveat: because those upper bounds are missing, the intended scheme cannot be
  reconstructed from this PDF; neither fragment is a usable gate on its own.
- Studio bands (NOT from this PDF): `qa/thresholds.yaml:19` carries
  `delta_e00: { pass_max: 1.0, warn_max: 2.0 }   # >2.0 = non-compliant`
  (blueprint §9.3 initial defaults, `qa/thresholds.yaml:1`; PR-only file).
  They are implemented in `pipeline/scripts/delta_e00.py:23-24`
  (`BRAND_PASS_MAX = 1.0` / `BRAND_WARN_MAX = 2.0`), a full CIEDE2000 scorer
  validated against the Sharma, Wu & Dalal (2005) Table 1 reference values in
  `pipeline/scripts/test_delta_e00.py`.
- Gate wiring: `brand_delta_e00` is a declared **gate3_client** check
  (`pipeline/scripts/repair_loop.py:84`, `wired=True`, fail action
  `correct_palette`). It scores only when an approved brand palette is supplied
  (`--brand-palette`); with no palette it records **UNWIRED** — "no brand
  palette supplied — not scored", never a silent pass
  (`pipeline/scripts/repair_loop.py:152-156`, asserted in
  `pipeline/scripts/test_repair_loop.py:238`). So a client with no brand palette
  on file gets no Brand QA verdict because the PALETTE is missing, not because
  the bands are.

## 4. HDR / WCG exception — ใช้ ΔE ITP แทนเมื่อเป็น HDR

- The source hedges: "as pipelines transition to Wide Color Gamut (WCG) and High
  Dynamic Range (HDR) workflows, CIEDE2000 **can** underpredict errors"
  (Automated Production QA Scoring Systems.pdf p.9). Read it as a conditional,
  not a law — that sentence carries no citation marker of its own; marker 58 sits
  on the adjoining ΔE ITP sentence.
- "In these specific environments", the source says, pipelines use the **ΔE ITP**
  metric, derived from the **ICtCp** color space, which "scales specifically so
  that a value of 1 indicates a just noticeable difference in HDR luminance"
  (pdf p.9, marker 58).
- Studio note: current deliverables are SDR sRGB renders → §2 applies; revisit
  the moment an HDR deliverable (video walkthrough, HDR hero) enters the
  pipeline. GAP: the source gives no ΔE ITP band table at all, and
  `qa/thresholds.yaml` `brand_qa` carries only `delta_e00` — any ΔE ITP band
  would have to be sourced elsewhere and adopted via a thresholds PR.

## 5. Logo geometric integrity — ความถูกต้องเชิงเรขาคณิตของโลโก้ (SIFT/ORB)

Color conformance alone is insufficient; Brand QA also checks geometry
(Automated Production QA Scoring Systems.pdf p.9, markers 55, 44):

- Extract keypoints from the generated logo with **SIFT** (Scale-Invariant
  Feature Transform) or **ORB** (Oriented FAST and Rotated BRIEF) and match
  against the **reference vector file**.
- Any affine or projective distortion that alters **aspect ratio, kerning, or
  relative spacing of typography** beyond strict tolerances → **immediate
  rejection** (pdf p.9, marker 44).
- GAP: "strict tolerances" is not quantified in the source (no max keypoint
  reprojection error, no match-ratio floor). Re-source or calibrate on
  golden-set logo crops before wiring into a gate.

## Gaps — ช่องว่างที่ต้อง re-source ก่อนใช้เป็นเกณฑ์

- All ΔE00 band bounds (§3) — blank in THIS SOURCE (the studio's live bands come
  from `qa/thresholds.yaml:19`, not from this PDF; do not cite this file for them).
- ΔE ITP band table for HDR (§4) — absent entirely from the source.
- SIFT/ORB numeric tolerances (§5) — "strict tolerances" only, no values.
- Segmentation-model choice and minimum sample count per brand region — not
  specified in the source.
- Adoption path for the items still open above: independent source + golden-set
  calibration + `qa/thresholds.yaml` PR. This file never carries the numbers.
