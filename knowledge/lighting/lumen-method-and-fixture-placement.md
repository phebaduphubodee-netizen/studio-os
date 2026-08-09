# Lumen Method · IES Illuminance · Fixture Placement (REFERENCE)
# วิธีลูเมน · ค่าความสว่าง IES · การจัดวางโคมไฟ

> PROVENANCE: promoted 2026-07-04 from `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md`
> §6 (Lighting design). That KB was itself built 2026-06-30 by cross-checking **two
> independent Deep-Research runs** — Gemini 2.5 Pro + Google Search, and a NotebookLM
> DR over ~290 web sources (raw audit trail:
> `knowledge/_inbox/interior-ai/2026-06-30-gemini-DR-lighting.md` +
> the nlm-DR history). Tier: **REFERENCE — strong-but-unaudited**, NOT Authority.
> Confidence is marked per value below (cross-vendor-confirmed vs single-source)
> from the KB's §9 verification ledger.
>
> This file promotes the parts §6 that were previously UNPROMOTED and that
> `knowledge/lighting/residential-lighting.md` explicitly lists as GAPs: the
> **numeric layering ratios**, the **per-room IES illuminance table**, **per-zone
> CCT + CRI floor**, **fixture placement/spacing rules**, and the **lumen method**.
> `residential-lighting.md` remains the companion for CCT-mixing rules, TM-30,
> dimming protocols, and render light-coherence QA vocabulary.

## อำนาจกฎหมาย / Authority cross-ref — กฎหมายชนะ / law wins

Statutory **lux floors** (50–300 lux by area type) are LAW and live in
`knowledge/codes-th/mr39-fire-sanitation-ventilation.md` table 3. Every design
illuminance in this file is a COMFORT/QUALITY target that must never fall below
the statutory floor; on conflict `codes-th/` wins and the artifact says so.
Any statutory ceiling/room geometry a lighting layout assumes is governed by
`knowledge/codes-th/mr55-residential-dimensions.md`. None of the numbers below
are statutory — do not treat them as code.

---

## 1. Layered lighting model + numeric ratios (§6.1)

Modern ambient/task/accent/decorative descends from **Richard Kelly's** three
elements (*single-source: NLM; Livingston, per KB §9*):

- **Ambient** (Kelly "Ambient Luminescence") — soft, shadowless general fill
  (downlights, cove/indirect).
- **Task + Accent** (Kelly "Focal Glow") — directional. *Task* = high intensity
  for an activity (under-cabinet, desk, reading).
- **Decorative** (Kelly "Play of Brilliants") — sparkle (chandeliers, exposed
  filament); primarily aesthetic.

**Numeric ratios** (these fill the ratio GAP stated in `residential-lighting.md`):

| Ratio | Value | Purpose | Confidence |
|---|---|---|---|
| Accent : ambient | **~3 : 1** | an accent must read ~3× the ambient level to register as a focal point | single-source (Gemini) |
| Task surface : surround | keep within **3 : 1** | limits visual clutter / eye fatigue | single-source (Gemini) |

> These are the numeric layering ratios `residential-lighting.md` flags as a GAP.
> Single-source — verify before any value gates a client deliverable.

---

## 2. IES residential illuminance targets (§6.2)

Indicative IES residential **maintained** targets (already de-rated for light
loss). **1 footcandle ≈ 10.76 lux.** *Single-source (Gemini DR); verify vs the
current IES Recommended Practice edition before client use.* These fill the
per-room lux GAP in `residential-lighting.md` — but they are REFERENCE, and the
statutory floor (Authority block above) still wins.

| Room | Task | fc | lux |
|---|---|---|---|
| Living | general / circulation | 10–20 | 108–215 |
| Living | reading (at chair) | 30–50 | 323–538 |
| Kitchen | general | 30–50 | 323–538 |
| Kitchen | counters / sink / range | 50–80 | 538–861 |
| Dining | ambiance (dimmers) | 10–20 | 108–215 |
| Dining | at table | 30–50 | 323–538 |
| Bedroom | general | 10–20 | 108–215 |
| Bedroom | bedside reading | 30–50 | 323–538 |
| Bathroom | general | 20–30 | 215–323 |
| Bathroom | vanity/grooming (vertical on face) | 50–80 | 538–861 |
| Home office | desk / paper task | 50–75 | 538–807 |

> ⚠ **CORRECTION 2026-08-08 — two rows of this table are attached to the wrong
> task.** A 315-source corpus (`knowledge/lighting/lighting-value-attribution-corrections.md`,
> rows c and d) reads **10–20 fc / 108–215 lux** as *hotel-bedroom READING*, not
> bedroom general — IES bedroom ambient is **6–15 fc ≈ 65–162 lux** — and finds
> **30–50 fc / 323–538 lux** to be the *kitchen general* standard, with reading
> areas at 20–50 fc and a bedroom reading task up to ~40 fc ≈ 430 lux. Both
> numbers are real; the ROW LABELS are what is in question. Read that file
> before quoting either row for a bedroom.

> Pipeline note: the **general/circulation** band of this table is already
> encoded (living/bedroom/dining 10–20, kitchen 30–50, bathroom 20–30 fc) in
> `pipeline/scripts/dimensional_rules.v0.1.json → lighting.general_illuminance_fc`,
> which `lighting.py` sizes the ambient downlight count to and
> `clearance_check.check_lighting` verifies against. Task-area levels come from
> local task fixtures, not the ambient layer.

---

## 3. Light quality — CCT per zone + CRI floor (§6.3)

- **CCT (Kelvin):** 2700–3000K warm (living/bed/dining = cozy); 3000–4000K
  neutral/cool (kitchen/bath/office = task acuity); 5000K+ daylight usually too
  sterile for residential. *Consistent with `residential-lighting.md`'s
  NLM-sourced 2200–3000K residential band; this adds the per-room split, which
  that file lists as a GAP. Single-source for the per-room split.*
- **CRI ≥ 90** = residential professional floor (*single-source: Gemini*).
  ⚠ **DISPUTED 2026-08-08:** a 315-source corpus gives **82 CRI** as the stated
  minimum for occupied interiors and treats **> 80** as already "high colour
  rendering", and does not support ≥ 90 as a general requirement — see
  `knowledge/lighting/lighting-value-attribution-corrections.md` row (e). The
  encoded `lighting.cri_min = 90` is UNCHANGED pending an owner decision, because
  moving it changes what `clearance_check.py` passes.
- **TM-30 currency flag:** CRI (8–15 pastel samples) is the legacy metric; the
  modern standard is **ANSI/IES TM-30-20** (99 samples → Rf fidelity + Rg gamut).
  Use CRI≥90 as the simple floor, prefer TM-30 Rf/Rg where the fixture sheet
  gives it. Full TM-30 / R9 / CCT-mixing rules: `residential-lighting.md`.
  `dimensional_rules.v0.1.json → lighting.cri_min = 90` encodes the floor.

---

## 4. Fixtures + placement / spacing rules (§6.4)

*Geometric placement rules — single-source (Gemini). NOT yet enforced by
`clearance_check` (only illuminance/CCT/CRI/layering are); these are the target
for a future placement-rule check.*

- **Recessed downlights (ambient):** spacing ≈ **ceiling height ÷ 2** (≈4 ft on
  an 8 ft ceiling); first row **½ the spacing** from the wall (≈ H ÷ 4) to avoid
  the "cave effect."
- **Dining pendant:** bottom **30–36"** above the table (+~3" per extra foot of
  ceiling); fixture diameter **½–⅔ of table width**.
- **Wall-wash / accent:** setback from wall ≈ **wall height ÷ 3**; space fixtures
  ≈ equal to the setback.
- **Kitchen task:** fixtures over the counter **centre-line**, not behind the
  user (avoid body-shadow).
- **Vocabulary:** recessed downlight · pendant · chandelier · wall sconce ·
  track · under-cabinet · cove. ("lamp" = the bulb; "luminaire/fixture" = the
  whole unit.)

---

## 5. Daylighting (§6.5)

- **Sidelighting** (windows; light-shelves bounce light deeper) · **toplighting**
  (skylights/clerestory = more even, orientation-independent).
- Always **control glare + heat gain** (shades, overhangs, reflective blinds),
  especially S/W façades (relevant for Thai orientation).

---

## 6. The Lumen Method — fixture count to hit a target (§6.6)

**N = (E × A) / (Φ × CU × LLF)** *(cross-vendor-confirmed formula, per KB §9.)*

| Symbol | Meaning | Typical |
|---|---|---|
| **E** | target maintained illuminance (fc, from §2) | per §2 table |
| **A** | workplane area (ft²) | room-derived |
| **Φ** | initial lumens per luminaire | mfr sheet |
| **CU** | coefficient of utilization (0–1; by Room Cavity Ratio + surface reflectances) | **0.65** default |
| **LLF** | light-loss factor (lamp depreciation × dirt × ballast) | **0.70–0.85**, use **0.80** |

**Worked example (from KB §6.6):** 12'×15' office (A = 180 ft²), target **50 fc**,
fixture **3200 lm**, CU **0.65**, LLF **0.80** →
N = (50 × 180) / (3200 × 0.65 × 0.80) = 9000 / 1664 = 5.41 → **6 fixtures**.

**Typical surface reflectances** (feed CU; link wall reflectance to the material
spec / Binggeli LRV): ceiling ~80%, walls ~50%, floor ~20%.

> Pipeline note: `pipeline/scripts/lighting.py` implements exactly this — it SIZES
> the ambient downlight count by N = E·A/(Φ·CU·LLF) to the §2 IES band midpoint,
> reading `dimensional_rules.v0.1.json → lighting` for E (`general_illuminance_fc`),
> CU (`cu_default 0.65`) and LLF (`llf_default 0.80`). Same targets that
> `clearance_check.check_lighting` verifies, so the auto-layout passes its own check.

---

## 7. GAPs / do-not-invent

1. Per-room **task-lighting CCT** and numeric **Rf/Rg/R9** targets — not given
   (see `residential-lighting.md` GAP list; do not backfill).
2. Placement rules (§4) are **not yet a gate** — enforced only as guidance until
   a `clearance_check` placement predicate is added via PR.
3. All illuminance / CU / LLF / ratio numbers are **single-source** (Gemini DR) —
   re-verify vs current IES RP before any value gates a client deliverable.
   The statutory `codes-th/` floor always outranks these.

## Cross-refs
- `knowledge/lighting/residential-lighting.md` — CCT bands + mixing rules,
  TM-30/R9, dimming protocols (0-10V/DALI/DMX512), render light-coherence QA.
- `knowledge/codes-th/mr39-fire-sanitation-ventilation.md` — statutory lux floors (LAW).
- `knowledge/rendering/render-defaults.md` — the §8 render/camera companion.
- `pipeline/scripts/lighting.py`, `pipeline/scripts/dimensional_rules.v0.1.json`,
  `pipeline/scripts/clearance_check.py` (`check_lighting`) — the code that consumes this.
