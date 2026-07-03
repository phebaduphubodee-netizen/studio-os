# Brand-Color & Identity Verification — มาตรฐานวิธีตรวจสีแบรนด์และโลโก้ (METHOD standard)

> PROVENANCE: distilled from the DR report
> `knowledge/_inbox/id-project-corpus/Automated Production QA Scoring Systems.pdf`
> pp. 8–9 (method + perception bands), p. 12 (Matrix 1, Brand QA row).
> Date 2026-07-03. Tier: REFERENCE (studio METHOD standard, not law, not a gate).
> The PDF's own citation markers (⁵⁵, ⁵⁷, ⁵⁸, ⁶¹ …) resolve only inside that
> report; they are reproduced here as-is for traceability.

> ## ⚠ BOXED WARNING — ตัวเลขเกณฑ์ใช้ไม่ได้ / numeric band bounds are UNRECOVERABLE
>
> The source PDF's threshold expressions were exported as truncated equation
> images: every right-hand operand is blank in the file itself (verified by
> re-rendering the embedded images, 2026-07-03). Recovered fragments only:
> band-2 lower bound `1.0 −` (p.9 table) and Matrix 1 soft-gate fragment
> `2.0 < x ≤ [blank]` (p.12) — which do not even agree with each other on
> where the warning band starts. **The METHOD below is durable; every numeric
> gate value must be independently re-sourced (CIE/ISO literature or golden-set
> calibration) and adopted via a `qa/thresholds.yaml` PR before anything is
> allowed to pass/fail on it.** Do not backfill numbers from model memory.

**Authority cross-ref:** nothing in this file is statutory. Any legal
requirement (e.g. signage, safety colors) is governed by `knowledge/codes-th/`,
which outranks this file. Gate values live only in `qa/thresholds.yaml`
(PR-only); this file defines the procedure, never the numbers.

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

CIEDE2000 details worth knowing when implementing (pdf p.8, marker 58):

- Decomposes distance into Lightness (ΔL′), Chroma (ΔC′), Hue (ΔH′) with
  location-dependent weighting functions and a hue-rotation term correcting
  the problematic blue region around the 275° hue angle.
- Parametric weighting factors default to 1 under standard illumination.
- Not perfectly continuous: a minor discontinuity exists when two hues are
  exactly 180° apart, bounded by **0.274** for pairs under 5 CIELAB units
  apart (pdf pp.8–9, marker 58) — irrelevant at pass-band magnitudes, worth a
  unit test if scores cluster near a gate.

## 3. Three-band gate — แนวคิดเกณฑ์ 3 ระดับ (CONCEPT ONLY; bounds MISSING-IN-SOURCE)

The source defines a three-band ΔE00 disposition (pdf p.9, markers 58, 61).
**Band boundaries are blank in the source — see BOXED WARNING.**

| Band | ΔE00 range | Visual perception | Pipeline status |
|---|---|---|---|
| 1 | `< ` **[MISSING-IN-SOURCE]** | Imperceptible difference to the human eye | Perfect compliance; passes **hard gate** |
| 2 | `1.0 – ` **[upper bound MISSING-IN-SOURCE]** | Just Noticeable Difference (JND) under close observation | Acceptable; passes **soft gate** with warning logs |
| 3 | `> ` **[MISSING-IN-SOURCE]** | Clearly perceptible color shift | Non-compliant; fails **hard gate** |

- Recovered fragments: band-2 lower bound **1.0** (p.9); Matrix 1 Brand QA row
  (p.12) shows hard gate `≤ [blank]`, soft gate `2.0 < x ≤ [blank]` — an
  internal 1.0-vs-2.0 spread inside the source itself. Neither fragment is a
  usable gate.
- GAP: no adoptable numeric bounds anywhere in the corpus. Re-source from CIE
  colorimetric literature + calibrate on `qa/golden-set/`, then propose via
  `qa/thresholds.yaml` PR. Until merged, Brand QA runs **report-only**
  (log ΔE00, gate nothing).

## 4. HDR / WCG exception — ใช้ ΔE ITP แทนเมื่อเป็น HDR

- In Wide Color Gamut + High Dynamic Range workflows, CIEDE2000 **underpredicts**
  color errors (Automated Production QA Scoring Systems.pdf p.9, marker 58).
- There, score with the **ΔE ITP** metric, derived from the **ICtCp** color
  space, scaled so that a value of **1 = one JND in HDR luminance** (pdf p.9,
  marker 58).
- Studio note: current deliverables are SDR sRGB renders → §2 applies; revisit
  the moment an HDR deliverable (video walkthrough, HDR hero) enters the
  pipeline. GAP: source gives no ΔE ITP band table at all — bands must be
  built from scratch at adoption time.

## 5. Logo geometric integrity — ความถูกต้องเชิงเรขาคณิตของโลโก้ (SIFT/ORB)

Color conformance alone is insufficient; Brand QA also checks geometry
(Automated Production QA Scoring Systems.pdf p.9, markers 55, 44):

- Extract keypoints from the generated logo with **SIFT** (Scale-Invariant
  Feature Transform) or **ORB** (Oriented FAST and Rotated BRIEF) and match
  against the **reference vector file**.
- Any affine or projective distortion that alters **aspect ratio, kerning, or
  relative spacing of typography** beyond strict tolerances → **immediate
  rejection** (hard fail, no soft band).
- GAP: "strict tolerances" is not quantified in the source (no max keypoint
  reprojection error, no match-ratio floor). Re-source or calibrate on
  golden-set logo crops before wiring into a gate.

## Gaps — ช่องว่างที่ต้อง re-source ก่อนใช้เป็นเกณฑ์

- All ΔE00 band bounds (§3) — blank in source; internal 1.0/2.0 spread.
- ΔE ITP band table for HDR (§4) — absent entirely.
- SIFT/ORB numeric tolerances (§5) — "strict tolerances" only, no values.
- Segmentation-model choice and minimum sample count per brand region — not
  specified in the source.
- Adoption path for every one of the above: independent source + golden-set
  calibration + `qa/thresholds.yaml` PR. This file never carries the numbers.
