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

## 8. สิ่งที่นักออกแบบแสงพูดเอง / What lighting practitioners say on camera — including a challenge to §4

> PROVENANCE: promoted 2026-08-28 from
> `knowledge/_inbox/video-study/2026-08-28-lighting-and-composition-aRWwOhjbvfs.md`,
> `knowledge/_inbox/video-study/2026-08-28-lighting-plan-process-and-the-grid-argument-4ORbpY6d9Zk.md`,
> `knowledge/_inbox/video-study/2026-08-28-luminance-ratios-and-the-led-dado-reK_jQ1UtaY.md`,
> `knowledge/_inbox/video-study/2026-08-28-trim-margins-lighting-physics-and-rug-pile-KQZKc8PLV2A.md`,
> `knowledge/_inbox/video-study/2026-08-28-trade-details-rail-curtain-track-downlight-iJYto0muSd4.md`,
> `knowledge/_inbox/video-study/2026-08-28-what-a-real-project-hands-over-w2Gw5rzFKjA.md` and
> `knowledge/_inbox/video-study/2026-08-28-two-long-form-a-designer-lecture-and-a-live-render-clinic-9eImuRVG4qM.md`.
> Source video ids: `aRWwOhjbvfs` (design director, John Cullen Lighting) · `4ORbpY6d9Zk`
> (architect drawing lighting plans) · `qbZoZiZg6I4` · `reK_jQ1UtaY` (lighting engineer) ·
> `EBFzvBbFeaM` · `t3F0dwsBFjw` (electrician) · `7-G5784wZN0` · `pBy70zgtPIU` · `DquOzbuc4vM`
> · `9eImuRVG4qM` · `3Nfpr5gM3Pw`. Tier REFERENCE.

### 8.1 §4's SPACING RULE IS CONTESTED BY THE PROFESSION IT CAME FROM — read this before using it

§4 states *"spacing ≈ ceiling height ÷ 2"* as a placement rule. Four practitioners in this
study qualify or reject it:

| Position | Source |
|---|---|
| **≤ 4 ft apart, ≥ 2 ft off the wall** | an electrician, as a trade default for even coverage |
| **ceiling height ÷ 2**, *"a good rule of thumb"* — and he DERIVES it from overlapping cones, then adds *"of course that's going to be informed by the actual light fixture that you choose"* | an architect |
| *"divide the room ceiling height in half… measure 3 ft out, 30 in out from the edges of the walls, light the corners — **it's all nonsense**"* | a designer specialising in recessed layouts |
| *"**please no more grids of downlights on the ceiling**… the grid layout produces a very flat and lifeless effect, **everything is lit with the same intensity**"* | a luxury lighting design director |

**The synthesis, and it is what §4 is missing:** a spacing formula answers *"how do I light a
floor evenly"*, and **an evenly lit floor is not the design goal.** The grid persists because
*"the lights run straight down one bay, it's not complicated"* — an installation convenience.
Two independent sources also state the count rule: **you cannot know how many fixtures you
need until the fixture's lumens, beam spread and CRI are chosen**, so the count is DERIVED from
the specification, never from the grid.

Consequences both sources state flatly: **never one source and one type in a room**; mix
fixture types and AIM them (gimbals); and **decide what NOT to light** — *"by lighting too many
features you're at risk of having a washed out effect."*

### 8.2 CONCEAL THE SOURCE — five independent professionals, four disciplines
| Source | Wording |
|---|---|
| lighting design director | *"if you are lighting a shelving unit… with the light being the brightest part of the unit, it's what you notice… shouldn't you be focusing on the items displayed on the shelves instead? **Concealing light is what a lighting designer spends a lot of their time doing**"* |
| cabinet lighting installer | *"**I don't want to see the LED**… it's supposed to be out of sight, out of mind… a pet peeve of mine is being able to see the lens" |
| carpenter routing a dado | the channel is sunk so the **diffuser finishes flush** with the timber |
| Thai designer | a concealed **LED uplight above the headboard**, and hidden LED under a handrail |
| interior designer, at Harvard | *"the light source, **hid behind a sort of metal valance**, is a very important reason for why this building is so sensual and successful. **If you just put a lamp in it, or recessed lights… it would not feel the way that concealed source of light makes you feel**"* |

And the fixture requirement that follows: a luminaire must be **baffled** — the lamp recessed
inside its housing — because *"if the source of light is flush on the ceiling or floor it's
likely to be very glary."* Note this is compatible with a modern thin recessed can, whose
HOUSING is flush while the lamp sits up inside it.

### 8.3 GEOMETRY FACTS A MODEL CAN BE CHECKED AGAINST
- **A recessed fixture is flush.** The thin LED class is *"only as thick as the drywall they
  mount into"*, held by spring clips — on the order of 12.5 mm of housing, not a protrusion.
  A fixture hanging tens of millimetres below the ceiling it is recessed into is not a shallow
  can, a deep can, or a surface fixture; it is a class that does not exist.
- **Wall standoff changes the behaviour, not just the level:** closer than ~610 mm produces
  **wall grazing** — *"sharp light that picks out contours and defects"* — instead of **wall
  washing**. A useful pair of names for two different intentions.
- **The LED channel** (see also `knowledge/materials/millwork-casework.md` §9): a
  **12.7 × 12.7 mm (½″) aluminium profile** with an opaque or frosted lens, dadoed dead flush
  or hidden behind a **12.7-19 mm light rail**; a **6.4 mm (¼″)** profile for tight details; and
  a **45° corner profile mounted 89 mm (3½″) behind the face** when the light must be thrown
  rather than dropped.
- **The ceiling can be the source.** *"we could have this ceiling act as a sort of luminous
  plane… adjustable mono points that are really starting to wash this ceiling with light — and
  if this is a wood ceiling this creates a nice ambient light surface to light up the room."*
  The only proposal in the study that answers *"bright with no visible source"* **without
  putting a fixture in the shot**.
- **A flat ceiling is fixed in two parts** — relief plus a graze: *"if you would add just a
  little bit of **bump on the ceiling, or displacement**, and then allow some sort of light to
  just **create a gradient**…"*

### 8.4 THE ARITHMETIC UNDER §6
§6 gives the lumen method for a fixture COUNT. These give the level at a POINT, which is what
a render can be checked against:

| Law | Formula |
|---|---|
| inverse square | **E = I / d²** — E in lux (lm/m²), I in candela, d in metres |
| cosine | **E = (I / d²) · cos θ** — **d is the DIAGONAL**, cos θ = mounting height / diagonal |

*"every time you double the distance, the light received at the surface drops by a quarter."*
Worked: 1000 cd at 2.4 m directly below = **173.6 lux**; 1500 cd at 2.4 m high and 1.8 m across
→ d = 3.0 m, cos θ = 0.8, E = **133.3 lux**. **Contributions from every fixture ADD at a
point**, which is how a grid's uniformity is actually evaluated.

> This turns a lighting change from *turn a knob and re-render* into *solve, then render* —
> R5's cheap-rung law applied to light — and it yields what a WALL receives, which is the input
> the luminance ratios in §8.5 need.

### 8.5 LUMINANCE RATIOS — a four-zone structure, extending §1's two ratios
§1 gives accent : ambient ≈ 3:1 and task : surround within 3:1. A lighting engineer gives the
full **workplace** structure, measured as SURFACE luminance in cd/m²:

**task 1:1 · immediate surrounding 3:1 · surrounding 5:1 · background (walls, beyond 0.5 m)
10:1**

The failure mode he opens with is the one a downlight-only room produces: *"when you're using
downlights or luminaires which have **low luminance**, then it might occur that **the top of the
walls and the ceiling being too dark**."*

**These are workplace numbers and must not be lifted into a bedroom.** What transfers is the
STRUCTURE: a designed room has a deliberate luminance hierarchy several times wide, and a frame
whose whole content sits inside ~1.5:1 is flat by definition whatever its exposure.

### 8.6 CCT — §3 IS QUALIFIED BY A DISAGREEMENT AND A COUPLING
| Value | Context | Source |
|---|---|---|
| **3000 K** | *"best for bedrooms, living rooms"* | US electrical practice; and an archviz artist for living areas |
| **2200-2700 K** | *"for a residential environment… usually the most appropriate — it will give you a luxurious feel"* | luxury residential lighting design |

The spread is real — a trade default against a luxury-design default up to 800 K warmer — and
*"'warm white' is not specific enough to ensure consistent colour between different suppliers."*

**And the coupling that decides it is not a preference:** an electrician reports **3000 K on
brown walls reading PINK** until the fixtures were changed to 4000 K. A room whose dominant
surface is a brown material cannot choose its CCT in isolation. A second coupling comes from
photography: interior fixtures must be chosen **against the daylight in the same frame**, or the
result is a visible white-balance clash.

Mixing is allowed: *"it is acceptable and often desirable to mix colour temperatures if it's
done in a methodical way."*

### 8.7 A LIGHT CANNOT BEAT THE SUN
*"you cannot really see the daylight inside of the shot because you're **overwhelming it with
the light that's inside**… **no lamp, no light bulb can be stronger than the sun**."*

A physical sanity check for any frame mixing a daylight opening with interior fixtures, and it
constrains the ratio from the opposite side to a dim-the-daylight fix.

### 8.8 THE DOCUMENTS THIS ALL BELONGS TO
Two independent sources — one US, one Thai — say the same thing: a lighting layout is a
**drawing**, not a scattering.

- A **reflected ceiling plan (RCP)** is a required sheet of any construction set, placed
  immediately after the floor plans, and a **lighting schedule** listing every fixture with its
  specifications is a required schedule.
- A Thai designer states the same scope and adds a **socket plan**, kept as sheets **separate
  from the furniture plan** *"otherwise the detail becomes a mess"*, and names what the plan
  must carry: *"where each light is, how high, how it is mounted, what type of fixture."*
- **Switching groups are part of the design**: which fixtures come on together, and where the
  switches are relative to how a person enters and leaves — *"dim for TV at night, everything
  on for guests"* is two named scenes from one rig.
- The sequencing rule, stated by an architect: *"if the electrical contractor is already asking
  for lighting layouts, **you've left it a bit late**. You can start planning your lighting as
  soon as you have an idea of the **furniture arrangements** and some idea of the **finishes**."*

## Cross-refs
- `knowledge/lighting/residential-lighting.md` — CCT bands + mixing rules,
  TM-30/R9, dimming protocols (0-10V/DALI/DMX512), render light-coherence QA.
- `knowledge/codes-th/mr39-fire-sanitation-ventilation.md` — statutory lux floors (LAW).
- `knowledge/rendering/render-defaults.md` — the §8 render/camera companion.
- `pipeline/scripts/lighting.py`, `pipeline/scripts/dimensional_rules.v0.1.json`,
  `pipeline/scripts/clearance_check.py` (`check_lighting`) — the code that consumes this.
