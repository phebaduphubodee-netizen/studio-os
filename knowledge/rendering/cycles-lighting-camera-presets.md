# ค่าตั้งต้นแสง · กล้อง · สี (Blender Cycles) / Cycles Lighting · Camera · Colour-Management Presets — REFERENCE starting values

> PROVENANCE: promoted 2026-07-13 from `knowledge/_inbox/interior-ai/2026-07-01-photoreal-render-technique-DR.md`
> (the "Lighting for Photorealistic Interiors", "Camera and Composition", "Color
> Management for a Luxury Feel" and "Minimal Scene Dressing for Realism" findings).
> **Single-source Deep-Research report — tier REFERENCE, strong-but-unaudited.**
> Secondary citation, for the repo's OWN tuning record only (no value in §1–§8 is
> promoted from it): `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` — cited
> once, in §2's OPEN note, for the world-ambient-fill tuning history.
> These are STARTING points for the Cycles clay pass (`build_room.py`) and the
> render-request scope it is authored against — **NOT a gate, NOT authoring law.**
> The lighting/camera/colour companion to `knowledge/materials/bsdf-material-presets.md`
> (the materials third of the same DR) and the per-value detail under
> `knowledge/rendering/render-defaults.md` §2–§3, §6.
>
> CITATION CONVENTION: the staged DR is cited `DR:NN` = a literal line in that
> file (it is the frozen citation anchor). Sibling `knowledge/` files are cited by
> **section / stable code** (§, `PH-03`, rule number) and never by line number —
> their line numbers move as they are edited.

## ลำดับอำนาจ / Authority + precedence — READ BEFORE USING A NUMBER

- **Studio gate evidence and wired defect classes outrank this reference.**
  Precedent: `render-defaults.md` §3 ("Studio deviations (gate evidence wins)").
  Where a value below collides with a wired rule, **the wired rule wins**. There
  are **two** live collisions: (1) the ≥2-CCT check, reconciled in §3 below; and
  (2) **partially**, the DR's 24–35 mm lens band against the **50 mm** member of
  the studio snap set (§5). Read §3 before implementing anything in §2.
- **Design-side lighting bounds are NOT set here.** Per-zone CCT bands, the
  CCT-mixing prohibition and the ambient/task/accent roles live in
  `knowledge/lighting/residential-lighting.md`; illuminance targets and layering
  ratios in `knowledge/lighting/lumen-method-and-fixture-placement.md`. This file
  gives *render-side Blender values*; those files give the *design bounds those
  values must sit inside*. On conflict, the bounds win.
- The IES figures below reach us **second-hand through the DR** (a US body's
  handbook, quoted by the DR — not read against IES directly). They are
  REFERENCE, and they are **not Thai law**. Any statutory illuminance or geometry
  a render depicts is governed by `knowledge/codes-th/`.
- Camera lens/height already have **gate-proven studio values**
  (`render-defaults.md` §3, `render-quality.md` §4). The DR's camera **height**
  corroborates them; its **lens band partially conflicts** with them. Neither
  replaces them (§5).

---

## 1. ชั้นแสงสามระดับ → Blender primitives / The layered triad, mapped

The DR frames the layered approach as "a direct countermeasure to the flat,
sterile look common in CG", and attributes it to the IES Lighting Handbook and
Gary Gordon's *Interior Lighting for Designers* (**DR:14**). The three layers
themselves are listed at **DR:16–19**. The roles are
already law-side in `residential-lighting.md`; what is new here is the **mapping
to Cycles primitives**:

| ชั้น / Layer | Blender primitive (DR) | Source |
|---|---|---|
| **Ambient** — general fill, safe navigation | low-strength **HDRI / IBL** — "often best achieved with a low-strength HDRI/IBL" | DR:17 |
| **Task** — directed light for an activity | **spotlights or smaller area lights** — "typically represented by" | DR:18 |
| **Accent / Focal** — highlights features, artwork, objects | **IES-profile** downlight / sconce (manufacturer `.ies`, e.g. Philips, Erco); Blender's **IES Light node** | DR:19, DR:31 |

- The accent layer is the DR's named crucial step "to avoid a flat look" (DR:19).
  This is the same wound the wired defect **PH-01** ("flat single-uniform-source
  lighting", `knowledge/classifications/render-defects.md`) detects — the triad is
  the upstream countermeasure, not a new rule.
- **Softness:** use **large, low-intensity** area lights rather than small bright
  ones, to mimic real bounced/diffused light; area lights must be "sufficiently
  large to create soft shadows" (DR:34).
- **Contrast:** per Gordon, visual interest comes from the light/shadow contrast —
  "Don't be afraid of dark areas" (DR:35). Bounded by §4.

---

## 2. ค่าตัวเลขฝั่งเรนเดอร์ / Numeric render-side values (Cycles)

The DR heads this block **"Blender 5.x Cycles Lighting Values"** (DR:21) — the
version the studio actually renders on. Methodology, stated by the DR: **start
from real-world wattage, then adjust for light size and scene scale** (DR:26).

| Parameter | Value (as the DR states it) | Hedge in source — inherit it | Source |
|---|---|---|---|
| **HDRI selection** (ambient fill) | a **high-quality, overcast or soft-sun** HDRI. Stated purpose: "to provide realistic, soft ambient light **and accurate reflections**" — i.e. two purposes, the second is reflections | stated flatly | DR:22 |
| **HDRI / IBL Strength** (ambient fill) | **0.5 – 1.5** | "Keep it low, **typically** in the range of" | DR:23 |
| HDRI role | a **subtle fill that grounds the scene** — explicitly **NOT the primary light source** | stated flatly | DR:23 |
| **Key light type** | `Area Light`, set to **Quad or Disk** | stated flatly | DR:25 |
| **Key light power** — large area light simulating a **sheer-curtained window** | **100 – 300 W** | "**might be**"; "depends on the light size and scene scale" | DR:26 |
| **Recessed downlight** (as an accent) | **8 – 15 W** | "**might be**" | DR:26 |
| Interior practical (from a lamp in the model) | real-world watts, "e.g. **10 W LED**" | given as an example, not a band | DR:131 |
| **Warm white** — practicals | **2700 – 3000 K** — "the standard for high-end residential and hospitality" | stated flatly. **Scope caveat — read it:** at DR:28 this band sits under the **Key Light**'s "Color Temperature (Kelvin)" heading (DR:24 → DR:27 → DR:28), i.e. the DR *also* offers 2700–3000 K as an option for the **primary** source. The scoping to **practicals** comes from DR:29 ("warmer interior practical lights (2700K)") and DR:131 (`interior_fill` lights = `random(2700, 3000)K`) | DR:28, DR:29, DR:131 |
| **Daylight through a window** | **5000 K** (cool, direct sun) → **6500 K+** (overcast sky) | "can range from" | DR:29 |
| Cool key ("sun" area light) | **~4500 K**, DR rule-engine form `random(4500, 5500) K` | "A **good strategy is**…" | DR:29, DR:130 |
| CCT generally | "This is critical for warmth. **Avoid pure white.**" | stated flatly | DR:27 |

> **The DR's stated purpose for the cool/warm split:** "This **color contrast**
> adds realism and depth" (DR:29) — the interplay between a cooler ambient/key
> light and warmer practicals is what the DR names as the cure for the sterile-CG
> look (DR:33). **Do not implement that as two electric fixtures in one zone — see §3.**

- The warm-white row's scope caveat **does not disturb §3's reconciliation**: that
  reconciliation rests on the DR's *rule-engine* form (DR:130 cool key
  `random(4500,5500)K` / DR:131 warm `interior_fill`), which does scope warm to the
  practicals. The caveat only records that the DR's prose *additionally* allows
  2700–3000 K as a key-light colour — an option, not the pairing §3 reconciles.

**OPEN (do not swap blind):** `build_room.py` already sets a soft **world ambient
fill** (that phrase is `render-defaults.md` §7's — but §7 carries **no number**).
The knob has **two branches, not one value**: Strength **0.12** on the default
cool-sky fill (`pipeline/scripts/build_room.py:230`) and **0.30** on the warm-suite
fill (`pipeline/scripts/build_room.py:225`). The 0.12 was **tuned down from 0.4**
against an over-exposed open-top room; that is recorded verbatim at
`knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md:182` — "the scene was
over-exposed/flat (open-top room floods with sun) → fixed (world fill 0.4→0.12 +
exposure −1.2)". Whether that knob is the same quantity as the DR's **HDRI
environment Strength 0.5–1.5** is *not established by this source*. Do not
substitute one number for the other without a test render.

---

## 3. การประนีประนอมกฎ ≥2 CCT กับ PH-03 / Reconciling the ≥2-CCT check against defect PH-03 — **READ THIS**

The DR's scene check is stated unscoped and scene-global:

> "**Check:** At least two different color temperatures must be used." (DR:132; cf. DR:33)

Taken literally, that check **manufactures a wired defect.** Three live rules say so:

| Wired rule | What it says | Where |
|---|---|---|
| **PH-03** | "CCT clash within one zone" — a clinical **4000 K** daylight source fighting a warm residential **2700 K** incandescent source **within the same localized zone** = a detected defect | `knowledge/classifications/render-defects.md`, defect code **PH-03** |
| Studio photoreal **rule 1** | "no 4000 K vs 2700 K clash in one zone" — *fixed by prompt in registry v003* | `knowledge/brand-standards/render-quality.md`, "The six rules" §1 |
| CCT mixing rule | CCTs must stay logically consistent across the space; mixing conflicting CCTs in the same localized zone = a **severe compositional error**. Residential = **2200–3000 K**; **4000–5700 K is reserved for commercial** | `knowledge/lighting/residential-lighting.md`, §"CCT per zone" + §"CCT mixing rules" |

**The collision is real and it is sharper than "two temperatures are fine":** the
DR's key at **4500–5500 K** sits *above* the residential band and *inside* the band
`residential-lighting.md` §"CCT per zone" explicitly reserves for **commercial** —
and its partner practical is **2700 K**, i.e. almost exactly PH-03's forbidden pair.

**Studio reconciliation (this is the studio's scoping, NOT a rule the DR states):**

1. **The wired defect wins.** PH-03 and `residential-lighting.md` are law-side for
   this studio; the DR is REFERENCE. Where they conflict, the DR loses.
2. **The ≥2-CCT check may only be satisfied ACROSS layers of different kind —
   a daylight aperture vs electric practicals — never by two electric luminaires
   of different CCT inside one localized zone.** The DR's own framing supports
   this reading (its cool source is a **"sun" area light** (DR:29) and its rule
   fires only when `lighting_style` = **"Daylight"** (DR:128)) — but the DR
   **never states the scoping as a rule**, and its check as written does not carry
   it. That is the promotion's correction, and the reason a literal implementation
   would trip PH-03.
3. **Never emit 4500–5500 K as an electric-luminaire CCT in a residential zone.**
   That is both an FF&E spec error (the commercial band — `residential-lighting.md`
   §"CCT per zone") and a render defect (PH-03). The DR's `random(4500,5500)K` is
   admissible **only** as the daylight/sun source under a Daylight lighting style.
4. If the scene has **no daylight aperture** (evening interior), the ≥2-CCT check
   **must not fire at all** — a single warm residential CCT family (2200–3000 K)
   is the correct answer, and forcing a second temperature to satisfy the check
   would author PH-03 deliberately.

> Net: the DR is right that *flat single-temperature light reads as CG* (that is
> PH-01), and right that *contrast is the cure*. It is the **scope** of the
> contrast — daylight-vs-practical, not fixture-vs-fixture-in-one-zone — that the
> studio's wired rules already own, and that the DR omits.

---

## 4. อัตราส่วนความส่องสว่าง / Luminance ratio ceiling

| Ratio | Value | Scope (inherit it) | Source |
|---|---|---|---|
| **Brightest : darkest** (luminance ratio) | **no greater than 20 : 1** | "For **general spaces**, the IES recommends" — a DR-quoted IES figure, second-hand | DR:35 |

- This is a **ceiling on overall contrast range**. It is **not** the same quantity
  as the **accent : ambient ≈ 3 : 1** and **task : surround within 3 : 1** ratios in
  `knowledge/lighting/lumen-method-and-fixture-placement.md` (§"Numeric ratios") —
  those are focal/comfort targets between two named layers. Neither figure
  overrides the other; they measure different things, and both are single-source.
- It bounds §1's "don't be afraid of dark areas" (DR:35): dark is permitted, up to
  20 : 1 across a general space.

---

## 5. กล้อง — hero shot / Camera

| Parameter | Value (DR) | Source | Studio status |
|---|---|---|---|
| **Focal length** | **24 – 35 mm** full-frame. <24 mm → "distracting distortion"; >35 mm "may not capture the scope of the room" | DR:54 | **PARTIAL CONFLICT — gate-proven studio value wins:** subject-size lens snap **26 / 28 / 35 / 50 mm** (`render-quality.md` §4, `camera_config.py`). This is a **fourth REFERENCE authoring band, NOT corroboration** — see the ledger note below. |
| **Camera height** | **1.0 – 1.2 m** — "a **typical** height"; "**often** the height of a seated person or the mid-point of the main furniture group" | DR:55 | **Corroborates** the gate-proven `--eye` camera ≈ **1.15 m** (`render-defaults.md` §3, lowered on M3.2 designer evidence). Independent agreement, not a new value. |
| **Level camera** | pitch/roll **= 0**, no converging verticals — "which looks amateur" | DR:55, DR:139 | Already encoded as `build_room.py`'s level camera + negative `shift_y` (no tilt) — `render-quality.md` §6, `render-defaults.md` §3. Cited, not restated. |
| **Aperture (hero)** | **f/8 – f/16** | DR:56–57 | **NEW BAND — see the reconciliation below.** |
| **Composition** | **Rule of thirds** for the main seating group / focal point off-centre; **leading lines** (rug edge, flooring direction) | DR:58 | Corroborates `render-defaults.md` §3 and `styles/color-composition.md` §5–§6. |

**The 24–35 mm band is a FOURTH lens band for the ledger — do not read it as
corroboration of our snap set.** `render-quality.md` §4 keeps that ledger and
states the discipline plainly: *"Lens bands now in promoted knowledge — do not
read these as one band."* A **numerically identical 24–35 mm figure was retracted
there on 2026-07-13** for having been over-read as corroboration of our lens
choice. (That one is a QA-detector *implied-FOV* threshold; the DR's 24–35 mm **is**
a genuine authoring claim, so it is a different figure — but it walks into the same
trap, and it belongs in that ledger, not in a "corroborates" column.) Its actual
effect on the snap set:

- it **supports 26 / 28 / 35 mm**;
- it **does not support 50 mm** — DR:54's "Narrower than 35mm may not capture the
  scope of the room" **rules the 50 mm snap member out**. 50 mm also sits inside
  `render-defaults.md`'s **24–50 mm** authoring band (per `render-quality.md` §4's
  ledger), which the DR band does not.

The **26 / 28 / 35 / 50 mm** snap set stands on studio gate evidence
(`render-quality.md` §4), which outranks a REFERENCE source for the studio's own
outputs. This is the second live collision named in the authority block.

### 5.1 ค่ารูรับแสงสามชุด / Three aperture settings — which wins for a hero shot

The studio now holds three f-stop settings — **two continuous bands and one
discrete pair**. They are **scoped by shot type and do not actually compete**:

| Shot type | f-stop | Source |
|---|---|---|
| **Hero shot of a whole space** (seating group; foreground table *and* background sharp) | **f/8 – f/16** (a continuous range: DR:140 emits `random(8, 16)`) | DR:56–57 — **this is the hero default** |
| Whole-massing / infinite depth of field | **f/8 or f/11** — a **discrete pair, NOT a range** | `knowledge/classifications/prompt-dimensions.md`, "OPTICS lexicon" § → "Aperture pair" bullet — already promoted. That file's provenance block records the pair-not-range form as a **deliberately tightened citation** (IPE p.5); do not re-open it as a range |
| **Lived-in detail**, isolating one object (cabinet pull, linen weave) | ≈ f/2.8 | `knowledge/brand-standards/render-quality.md` §4; `knowledge/styles/color-composition.md` §5 — already promoted |

- **For a hero shot, f/8–f/16 wins.** The DR is explicit that shallow DoF "is an
  artistic choice used to isolate a single object, but is **less common** for an
  overall 'hero' shot of a space" (DR:57). f/2.8 remains correct **for the detail
  shot it was promoted for** — it was never a hero-shot value.
- **The two deep-DoF figures are not the same shape.** The DR's is a *continuous*
  band, **f/8–f/16**; the massing value is a *discrete pair*, **f/8 or f/11**. The
  DR's continuous band **contains** those two discrete points — but there is **no
  continuous f/8–f/11 sub-band**, and nothing in either source forces a choice
  between f/8 and f/11.
- The DR hedges the premise itself: hero shots "**often** aim for a deep depth of
  field … mimicking how the human eye perceives the room" (DR:56).

---

## 6. การจัดการสี / Colour management

| Setting | Value | Source |
|---|---|---|
| **View transform** | **AgX** (not Filmic) for **Blender 4.x and newer** — wider dynamic range, handles extreme brightness/saturation "more gracefully than Filmic", preventing highlight burnout at a bright window | DR:63 |
| **Look (contrast)** | **"Medium High Contrast"** (or "High Contrast") — adds "punch and separation" | DR:65, DR:142 |
| **Exposure** | **no value promotable.** The DR states plainly: "There is **no single correct value**; it is an **artistic adjustment**" — set it *after* the physical light values | DR:64 |

- **The transform (AgX) is already promoted** (`render-defaults.md` §6, encoded in
  `build_room.py`). **The Look is what lands here.**
- ⚠️ **Strength mismatch inside the source — inherit the weaker one.** The DR's
  *findings* section hedges: a Medium High Contrast look "**can be a good starting
  point**" (DR:65). Its *pipeline* section states it flatly: "Automatically set
  Color Management to `AgX` and Look to `Medium High Contrast` **for all
  photorealistic render jobs**" (DR:142). **This file promotes the Look as a
  starting default and does not set a gate for it** — the hedged finding (DR:65)
  is the honest reading.
- Stated negative: "**Avoid a flat, low-contrast image**" (DR:65).

---

## 7. การจัดฉากขั้นต่ำ / Minimal scene dressing — candidate WARN rules (NOT WIRED)

The DR's stated purpose (attributed to Nielson & Taylor's *Interiors*, DR:68):
prevent "an empty CG shell" without clutter.

| Element | Rule as the DR states it | Strength in source | Source |
|---|---|---|---|
| **Rug** | an area rug is **essential to anchor a seating group** — defines the space, adds texture/colour | required | DR:71 |
| **Curtains** | **floor-to-ceiling sheer or linen**; add softness and **diffuse window light** | required where windows exist | DR:72, DR:146 |
| **Plant** | a single well-modelled plant (**Fiddle Leaf Fig, Monstera**) — organic element | **suggest only** — the DR's own check "**can suggest** adding a plant … if the scene lacks any 'Organic'-tagged assets" | DR:74, DR:147 |
| **Coffee-table props** | "Keep it simple": a stack of **two or three books**, a **small tray**, and **one** sculptural object or small vase | guidance | DR:76 |
| **Art** | a **single, large, abstract** piece on a primary wall as focal point | guidance | DR:77 |
| **Throw blanket** | casually draped on a sofa/chair — breaks up straight lines | guidance | DR:79 |

**Pipeline form (verbatim scope from DR:146–147):** for a `living_room`, flag a
**warning** if `scene.contains(rug) == false` **or** `scene.contains(curtains) == false`
*(the curtain arm only when windows exist)*; a plant is a **suggestion**, not a warning.

**Wiring status (checked 2026-07-13):** `pipeline/scripts/placement_logic.py`
carries **no rug / curtain / plant rule** — its only `rug` references are an
eye-camera aim filter and a dining false-WARN fix. These are therefore stated as
**candidate WARN rules, UNWIRED**, shaped to drop into that file's existing
furnishing-completeness WARN tier. **Do not cite them as enforced.** Note the
strength split above: **rug + curtains = WARN; plant = suggest; books/tray/art/
throw = guidance with no check in the source.** Promoting the guidance rows into
checks would be inventing rules the DR does not state.

---

## 8. ขอบเขตของกฎ / The scope these values are authored against

The DR's rule engine does **not** fire unconditionally — it is keyed on
render-request fields (DR:120–124), and dropping that scope is how a starting
value becomes a false rule:

- **Lighting rule** fires only for `mood` = **"Warm Luxury"** AND `lighting_style` =
  **"Daylight"** (DR:128). Every §2 value above is authored inside that scope.
  Other stated moods: "Bright & Airy", "Moody & Dramatic"; other lighting styles:
  "Evening Interior", "Studio" — **the DR gives no values for these.**
- **Camera rule** fires for `camera_angle` = **"Hero Seating Group"** (DR:136).
  Other stated angles: "Kitchen Island Detail", "Architectural One-Point
  Perspective" — **no values given.**

---

## GAPs / do-not-invent

- **No values for the non-Daylight lighting styles** (Evening Interior, Studio) or
  the non-Warm-Luxury moods, and **none for the non-hero camera angles**. The DR
  names these buckets and fills none of them. Do not interpolate.
- **This DR gives no task-lighting CCT and no per-room CCT** (living / dining /
  kitchen / bedroom / bath / corridor). It states the warm band and the daylight
  band only. Do not derive a per-room value from it; the CCT bands are owned by
  `knowledge/lighting/residential-lighting.md`.
- **The 20:1 luminance ratio and the 2700–3000 K band are single-source REFERENCE**
  (and IES is quoted second-hand). Verify before either gates a client deliverable.
- **Exposure has no number** (DR:64) — do not manufacture one.
- The DR's material/BSDF third is **out of scope for this file** — see
  `knowledge/materials/bsdf-material-presets.md`, which is the companion promoted
  from the same source.

## Cross-refs
- `knowledge/rendering/render-defaults.md` §2, §3, §6 — the render-side lighting/camera/post summary this file details with numbers.
- `knowledge/materials/bsdf-material-presets.md` — the materials third of the same DR (companion).
- `knowledge/lighting/residential-lighting.md` — **owner** of the CCT bands + the same-zone mixing prohibition (§3 above defers to it).
- `knowledge/lighting/lumen-method-and-fixture-placement.md` — illuminance targets + the 3:1 layering ratios (distinct from the 20:1 ceiling, §4).
- `knowledge/classifications/render-defects.md` — PH-01 (flat light), PH-03 (CCT clash) — the wired defects §1 and §3 answer to.
- `knowledge/brand-standards/render-quality.md` — the 6-rule studio photoreal standard + gate evidence (lens snap, f/2.8 detail shot).
- `knowledge/classifications/prompt-dimensions.md` — the **f/8 or f/11** massing aperture pair (a discrete pair, not a range).
- `pipeline/scripts/build_room.py`, `camera_config.py`, `placement_logic.py` — the code that consumes (or would consume) these.
- `knowledge/_inbox/interior-ai/2026-07-01-photoreal-render-technique-DR.md` — source.
- `knowledge/_inbox/interior-ai/INTERIOR-DESIGN-KB.md` — the world-ambient-fill tuning record cited in §2's OPEN note (repo history, not a promoted value).
