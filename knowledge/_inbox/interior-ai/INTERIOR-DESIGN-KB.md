# INTERIOR-DESIGN-KB.md — Professional ground truth for the pipeline
<!-- Built 2026-06-30 from 2 independent Deep Research runs (Gemini 2.5 Pro + Google Search; NotebookLM DR over 290 auto-discovered web sources). Raw outputs: research/2026-06-30-gemini-DR-*.md + research/2026-06-30-nlm-DR-history.json. This file is the DISTILLED, cross-checked knowledge base; the raw files are the audit trail. -->

**Purpose.** A textbook-grade reference so the pipeline produces *what a real interior-design deliverable must contain* — not pretty-but-wrong output. This is the knowledge layer behind the project's one real differentiator (dimensional + professional correctness).

## 0. Verification posture (read first — law of "don't build an illusion")
- **Source = 2 AI Deep-Research tools.** AI DR fabricates citations/numbers; treat everything here as **strong-but-unaudited** until it matters for a client.
- **What IS well-triangulated:** the **canonical book list** below was named *independently by both vendors* (Ching, Karlen & Fleming, Panero & Zelnik, Gordon, Steffy, Binggeli) — these are real, standard texts (high confidence they exist). Core numbers (lux levels, CCT ranges, the lumen-method formula) are **mutually consistent** across the two runs.
- **What to re-verify before any client-facing use:** specific illuminance numbers vs the *current* IES edition; any code/clearance value vs **local code** (the project already flags `dimensional_rules` as DRAFT); page numbers (none were claimed — good).
- **One genuine currency flag:** CRI vs **TM-30** — see §6.3.

---

## 1. Canonical sources (the bookshelf to acquire)
| Source | Authority for | Confirmed by |
| :-- | :-- | :-- |
| **Ching, F.D.K. — *Interior Design Illustrated*** | Graphic standards; how to draw/read plans, elevations, sections, details | Both |
| **Karlen & Fleming — *Space Planning Basics*** | Programming + schematic process; the 8-step method | Both |
| **Panero & Zelnik — *Human Dimension & Interior Space*** | Anthropometrics/ergonomics → **clearances, circulation, fixture sizing** (this is the data behind `clearance_check.py`) | Both |
| **Gary Gordon — *Interior Lighting for Designers*** | The *art/process* of layered lighting | Both |
| **Gary Steffy — *Architectural Lighting Design*** | Lighting technical + daylighting/controls integration | Both |
| **Corky Binggeli — *Materials for Interior Environments*** | Material performance specs + **Light Reflectance Values (LRV)** (feeds lighting calcs) | Both |
| **IES — *The IES Lighting Handbook* (10th ed.) / IES Recommended Practices** | THE standard for illuminance targets + lighting science | Both |
| Nielson & Taylor — *Interiors: An Introduction* | Whole-profession overview (elements, FF&E, color) | Gemini |
| Christine Piotrowski — *Professional Practice for Interior Designers* | Business/process/contracts of practice | NLM |
| Jason Livingston — *Designing with Light* | Lighting psychology; Richard Kelly's framework | NLM |
| Pharr, Jakob & Humphreys — *Physically Based Rendering: From Theory to Implementation* | The technical "bible" of rendering (advanced) | Gemini |

---

## 2. The professional process — 6 phases + deliverables
1. **Programming / brief** *(analytical, not creative)* — interviews, site survey, FF&E inventory, budget, **code review (IBC/ADA)**. Karlen's **8-step method**: interview → observe → set architectural parameters → organize → research unknowns → analyze affinities → diagram (bubble/block) → summarize into the **Program**.
   *Deliverables:* written Program, goals, user profiles, spatial + **adjacency matrix**, functional/technical reqs, code synopsis.
2. **Schematic design** — translate program → big-idea layout.
   *Deliverables:* bubble/adjacency diagrams, **schematic (single-line) floor plans**, concept sketches, **mood/concept boards**.
3. **Design development** — resolve everything to specifics.
   *Deliverables:* developed dimensioned plans, **Reflected Ceiling Plan (RCP)**, key elevations, character renderings, **Material & Finish schedule**, FF&E selections + preliminary budget.
4. **Construction documentation (CDs)** — the legally-binding build instructions (see §3).
5. **Bidding / tendering** — addenda, RFIs, bid analysis, contract.
6. **Contract administration** — site visits, submittal/shop-drawing review, RFIs, **punch list**, closeout.

> For our pipeline, the sellable wedge lives in **phases 3–4 (DD + CDs)** — the dimensioned, scheduled, spec'd output. Phases 1–2 stay human (programming + the "big idea").

---

## 3. Anatomy of a complete CD set (the completeness target)
A "complete" construction-document set = a **cross-referenced relational whole**, not loose drawings:
- **Cover sheet** — project info, drawing index, code data.
- **Construction/floor plans** — dimensioned; partitions, doors, power/data, keynotes.
- **RCP** — all ceiling elements: fixtures, diffusers, sprinklers, smoke detectors, height/material changes, **switching**.
- **Interior elevations** — vertical dims, millwork, outlet/switch placement.
- **Sections** — cuts showing assembly/material layers.
- **Details** — large-scale junctions (counter-to-wall, railing, etc.).
- **Schedules (tables):** **Door** (no., type, size, material, finish, hardware set) · **Finish** (floor/base/wall/ceiling per room) · **Lighting Fixture** (tag, symbol, mfr, model, lamping, voltage).
- **Specifications** — written volume, **CSI MasterFormat**; *legally takes precedence over drawings on conflict*.

**The relational rule (key for an AI generator):** every door on a plan → a Door-schedule row; every fixture symbol → a Lighting-schedule row; every room → a Finish-schedule row; every millwork item → an elevation/section. Generate schedules *from the model*, never by hand, so they can't drift out of sync.

---

## 4. Space planning & clearances (anthropometric ground truth)
*Authority: Panero & Zelnik; Karlen & Fleming. The US/ADA figures below are the anthropometric REFERENCE encoded by `clearance_check.py` (the US/imperial path).*
> ⚠️ **Jurisdiction (2026-07-01):** the LIVE pipeline for the real (Thai) jobs runs **Thai-code** numbers via `suite_clearance.py` (ceiling ≥ 2.60 m, corridor 1.0 m, door 0.80×1.90 m, bedroom ≥ 8 m²/≥ 2.5 m) — authority = `research/2026-06-30-thai-building-code-DR.md` + `docs/BUILD-PLAN.md §v0.2`. Treat the US/ADA figures below as reference/rationale (or for US work), NOT as the numbers the Thai suite enforces; always verify vs local code before a client deliverable.
- Hallway/circulation **≥ 36"** residential (**44"** commercial egress).
- Clear doorway **≥ 32"**.
- **ADA is non-negotiable** where it applies — travel/egress, toilet clearances, reach ranges, turning circles.
- Balance operational efficiency with **universal design** + biophilia (evidence-based design).

---

## 5. Materials & FF&E specification
- **CSI MasterFormat divisions:** finishes → **Division 09**; furnishings → **Division 12**. (Paint tag "PT-1" should link to **09 91 00 – Painting**.)
- **FF&E spec sheet must carry:** manufacturer + model, **dimensions (L×W×H)**, material/finish, **performance** (e.g. fabric **double-rub** abrasion rating, tile slip resistance), **certifications** (LEED, FSC), and **fire ratings** (**CAL 117**, **ASTM E84**). *(fire/perf data — NLM single-source; verify per jurisdiction.)*
- **Millwork / casework** = architectural scope (not FF&E), governed by **AWI** standards in three grades: **Economy / Custom / Premium**. *(NLM single-source.)*

---

## 6. Lighting design

### 6.1 The layered model
Modern ambient/task/accent/decorative descends from **Richard Kelly's** three elements *(NLM; Livingston)*:
- **Ambient Luminescence** → **Ambient**: soft, shadowless general light (downlights, cove/indirect).
- **Focal Glow** → **Task + Accent**: directional. *Task* = high-intensity for an activity (under-cabinet, desk, reading); *Accent* should be **~3× the ambient level** to read as a focal point.
- **Play of Brilliants** → **Decorative**: sparkle (chandeliers, exposed filament) — primarily aesthetic.
- Keep a **3:1 contrast** between task surface and surround to avoid visual clutter/fatigue.

### 6.2 Recommended illuminance (indicative IES residential — verify vs current edition)
1 footcandle ≈ 10.76 lux. These are *maintained* targets (already de-rated for light loss).

| Room | Task | fc | lux |
| :-- | :-- | :-- | :-- |
| Living | general / circulation | 10–20 | 108–215 |
| Living | reading (at chair) | 30–50 | 323–538 |
| Kitchen | general | 30–50 | 323–538 |
| Kitchen | counters / sink / range | 50–80 | 538–861 |
| Dining | ambiance (use dimmers) | 10–20 | 108–215 |
| Dining | at table | 30–50 | 323–538 |
| Bedroom | general | 10–20 | 108–215 |
| Bedroom | bedside reading | 30–50 | 323–538 |
| Bathroom | general | 20–30 | 215–323 |
| Bathroom | vanity/grooming (vertical on face) | 50–80 | 538–861 |
| Home office | desk / paper task | 50–75 | 538–807 |

### 6.3 Light quality — CCT and CRI / ⚠️ TM-30
- **CCT (Kelvin):** **2700–3000K** warm (living/bed/dining = cozy); **3000–4000K** neutral/cool (kitchen/bath/office = task acuity); **5000K+** daylight (usually too sterile for residential).
- **CRI ≥ 90** is the residential professional standard *(Gemini)*.
- ⚠️ **Currency flag:** CRI uses only 8–15 pastel samples and is the *legacy* metric. The **modern standard is ANSI/IES TM-30-20** — 99 real-world Color Evaluation Samples, giving **Rf (fidelity)** + **Rg (gamut)**. *(NLM single-source but correct; use CRI≥90 as the simple floor, prefer TM-30 Rf/Rg where fixture data provides it.)*

### 6.4 Fixtures + placement/spacing rules
- **Recessed downlights (ambient):** spacing ≈ **ceiling height ÷ 2** (≈4 ft on an 8 ft ceiling); first row **½ the spacing** from the wall (≈2 ft) to avoid the "cave effect."
- **Dining pendant:** bottom **30–36"** above table (+~3" per extra foot of ceiling); fixture diameter **½–⅔ of table width**.
- **Wall-wash / accent:** setback from wall ≈ **wall height ÷ 3**; space fixtures ≈ equal to the setback.
- **Kitchen task:** fixtures over the counter **center-line**, not behind the user (avoid body-shadow).
- Fixture vocabulary: recessed downlight · pendant · chandelier · wall sconce · track · under-cabinet · cove. ("lamp" = the bulb; "luminaire/fixture" = the whole unit.)

### 6.5 Daylighting
- **Sidelighting** (windows; light-shelves bounce light deeper) · **toplighting** (skylights/clerestory = more even, orientation-independent).
- Always **control glare + heat gain** (shades, overhangs, reflective blinds), esp. S/W facades.

### 6.6 The Lumen Method (number of fixtures to hit a target)
**N = (E × A) / (Φ × CU × LLF)**
- **E** = target maintained illuminance (fc, from §6.2) · **A** = workplane area (ft²) · **Φ** = initial lumens per luminaire (mfr sheet) · **CU** = coefficient of utilization (0–1; from mfr table by Room Cavity Ratio + surface reflectances) · **LLF** = light-loss factor (~0.70–0.85; lamp depreciation × dirt × ballast).
- **Worked example:** 12'×15' office (A=180 ft²), target **50 fc**, fixture **3200 lm**, CU **0.65**, LLF **0.80** → N = (50×180)/(3200×0.65×0.80) = 9000/1664 = 5.41 → **6 fixtures**.
- Typical surface reflectances: ceiling ~80%, walls ~50%, floor ~20% (these feed CU; link wall reflectance to the material spec / Binggeli LRV).

---

## 7. Color & mood (brief — design element, human-kept)
- **Warm hues** (red/orange/yellow) stimulate (red ↑ appetite → dining); **cool hues** (blue/green) calm/focus; **neutrals** support (white=airy, brown=grounding, black=drama, gray=balance). Light **value** governs spaciousness (light=airy, dark=intimate).
- **Light × color interact:** warm light enriches reds/oranges but dulls blues + can make skin sallow; cool light pops blues/greens. Brightness sets saturation. → never judge a finish color independent of its light source. *(NLM.)*

---

## 8. Rendering (photoreal pipeline)
*Note: this renders OUR dimensionally-correct model — it is the opposite of text-to-image tools (RoomGPT/Imagen) that invent a new room. Scale accuracy is the foundation realism factor.*

### 8.1 PBR materials (+ typical values)
Energy-conserving, physically-based. Per surface:
- **Albedo / base color** — shadowless diffuse color. Dielectrics sit ~**30–240** (sRGB 0–255); avoid pure 0/255.
- **Metalness** — effectively binary **0.0** (dielectric) / **1.0** (metal); mid only for rust/dust. Raw metal → albedo near black, color comes from specular.
- **Roughness** — 0.0 mirror-sharp → 1.0 fully diffuse. ("Glossiness" = 1 − roughness; know which the engine uses.)
- **Normal map** — RGB → per-pixel surface detail without geometry.
- **Specular / IOR** — dielectric default **IOR ≈ 1.5** (plastic); water 1.33, glass ~1.52.

### 8.2 Lighting for render
- **HDRI / Image-Based Lighting** — 360° high-range image = realistic ambient + reflections.
- **Sun & Sky** (Cycles Nishita, V-Ray Sun/Sky) — physical daylight by lat/long + date/time → correct shadows + color temp.
- **Area lights** — physical size → soft shadows (bigger source = softer). Use real lumens + Kelvin + **`.ies` photometric profiles** where available.
- **Global Illumination** — indirect bounce; without it shadows go pure-black. The realism workhorse.

### 8.3 Camera & composition
- **Focal length** interiors **24–50mm** (wide enough, low distortion); ~35–50mm = natural.
- **Eye level** camera Z ≈ **4'6"–5'6" (1.35–1.65 m)**.
- **Two-point perspective is the architectural standard** — sensor plane parallel to verticals so **all vertical lines stay vertical** (camera roll 0, no up/down tilt). Three-point only for deliberate drama.
- Apply rule-of-thirds / leading lines.

### 8.4 Realism factors (good → photoreal)
- **Scale accuracy** (non-negotiable; our differentiator) · correct **UV/texture scale** (grain matches plank width) · **bevel every edge** (~1–2 mm so edges catch light) · **imperfection** (micro-scratches, dust, smudges, slight asymmetry via roughness/grunge maps).

### 8.5 Engines
- Offline path-tracers (hero stills): **Cycles** (our Blender engine), **V-Ray** (studio standard), **Corona** (easy, archviz-loved).
- Real-time: **Enscape** (CAD/BIM walkthroughs), **Lumion** (animations/entourage).

### 8.6 Post
Never ship straight out of the engine: exposure/contrast, color grade/white balance, sharpening, subtle lens effects; pro workflow renders **AOV passes** (reflection/shadow/AO/denoise) for control without re-rendering.

---

## 9. ⚠️ Cross-vendor verification ledger
- **Confirmed by both vendors (high confidence):** 6-phase process; the 6 core textbooks; layered lighting; CCT bands; lumen-method formula; CSI/MasterFormat existence; two-point-perspective + ~5 ft eye level + 24–50 mm; PBR parameter set; scale-accuracy-as-foundation.
- **Single-source (use, but verify before client work):** exact lux/fc numbers (Gemini) · CU/LLF default values · TM-30-20, AWI grades, CAL 117/ASTM E84, CSI division numbers, Richard Kelly attribution (NLM).
- **Not claimed (good):** no page numbers, no fabricated DOIs.
- **Known nuance:** IES has shifted from a single "Handbook" toward **Recommended Practices** + the digital Lighting Library + TM-30; treat "IES Lighting Handbook 10th ed." as the anchor but expect RP-series citations in current practice.

---

## 10. Pipeline upgrades this implies (mapped to current files)
Concrete, prioritized — these turn the KB into code:
1. **Spec schema (`pipeline/specs/*.json`) — add a lighting layer:** per room `function` → IES `target_fc`; a `fixtures[]` list (`type`, `lumens Φ`, `cct_k`, `cri`/`tm30_rf`, `xy`), and surface reflectances (ceiling/wall/floor). — **✅ DONE (2026-06-30, loop closed):** `lighting.py` now SIZES the ambient downlight count by the **lumen method** (N = E·A/(Φ·CU·LLF)) to the IES band midpoint from `dimensional_rules.json` (living 9→16.7fc, kitchen 16→39.6fc — both PASS `check_lighting` now, was over-lit). Fixtures[] derived (auto or `spec["lighting"]` override); `schedules.py` reads optional `spec["finishes"]`. Remaining (minor): per-SPEC `target_fc`/reflectance overrides (today they come from the rules file + CU/LLF defaults).
2. **`clearance_check.py` — extend with lighting + completeness checks:** Lumen-Method check (computed avg fc vs IES target → PASS/WARN/FAIL); CCT/CRI sanity (flag CCT>4000K in living/bed, CRI<90); layering check (primary rooms need ≥ ambient+task); placement rules (downlight spacing=H/2, pendant 30–36", wall-wash setback=H/3). — **✅ DONE (2026-06-30):** `clearance_check.check_lighting(spec, fixtures)` does the lumen-method avg-fc vs IES band + per-type CCT-band + CRI-floor + layering checks; targets live in `dimensional_rules.json["lighting"]`; folded into the gate verdict via `report(..., extra=...)` (WARN-level → REVIEW, never blocks). ⚠️ It surfaced a real issue: the §6.4 auto-grid OVER-lights (~30fc living vs 10–20 target) — the loop-closing fix is #1's `target_fc` (size the ambient layer to the IES band). Placement-rule checks (spacing/setback) NOT yet added.
3. **New generator — RCP + schedules:** a Reflected Ceiling Plan output, and **auto-generated Door / Finish / Lighting schedules built from the spec** (the relational rule in §3) so drawings + tables never drift. — **✅ DONE (2026-06-30):** `pipeline/lighting.py` (DRAFT lighting layer, §6.4 placement) + `pipeline/rcp.py` (RCP DXF+PNG) + `pipeline/schedules.py` (Door/Finish/Lighting → Markdown+CSV); wired into `make_all.py`; fixtures derived ONCE and threaded to both RCP + schedule so they agree by construction. Verified end-to-end on `living_demo.json` (+ dining/override specs).
4. **`build_room.py` (render) — encode realism defaults:** enforce **two-point camera** (roll 0, vertical-corrected), **eye level ~1.6 m**, **24–50 mm** focal length; **auto-bevel ~1 mm**; texture-scale sanity (already partly in `build_room.rb`); PBR albedo plausibility flag (30–240). — **✅ DONE (2026-06-30):** level two-point camera @ 1.6 m / 28 mm with vertical lens-shift (no tilt), `albedo_plausible()` flag (0.04–0.94), per-material roughness, 1 mm edge-bevel modifier, + soft world ambient fill (§8.2) and pinned AgX/Filmic view transform (§8.6). **Verified vs official Blender docs by a 4-verifier workflow (wf_b76afaf9)** — all bpy API confirmed for Blender 3.6 + 4.x; it caught + fixed a backwards `shift_y` sign and a no-op `sun.location`. ✅ **RENDER-VERIFIED on Blender 5.1.2 (first real render, 2026-06-30):** installed Blender + ran it — the whole `build_room.py` runs clean on 5.1 (newer than the doc-checked 3.6/4.x), two-point verticals confirmed correct in the output. Actually rendering caught what the doc-check couldn't — the scene was over-exposed/flat (open-top room floods with sun) → fixed (world fill 0.4→0.12 + exposure −1.2). First image: `output/room_living.png`. Furniture is still `furniture.py` box primitives (real furniture = the friend's `.skp` catalog in `build_room.rb`).
5. **FF&E / material objects — add spec fields:** mfr/model/dims/finish + performance (double-rub, slip), certs, fire rating; tag→CSI-section link (e.g. PT-1 → 09 91 00). — **✅ DONE (2026-07-01):** `schedules.py._ffe_schedule` emits an FF&E schedule (one row per spec item; dims model-derived, product fields DRAFT until `verified:true`) carrying the §5 fields (mfr/model, finish, perf/cert/fire, CSI Div 12); `package.py` adds the A-602 FF&E sheet; `.claude/skills/ffe-research/` is the back-office research + PDF-parse skill that fills the spec's `ffe` block (adapted from Alpaca's MIT `product-research`/`product-spec-pdf-parser`).
6. **`dimensional_rules` — fold in §4 clearances + §6.4 lighting placement** as the DRAFT rule source (still verify vs local code before client use).

> Sequenced for EV: ~~#3 (schedules/RCP)~~ ✅ · ~~#2 (lighting completeness check)~~ ✅ · ~~#1 (lighting loop closed)~~ ✅ · ~~#4 (render realism defaults)~~ ✅. ~~#5 (FF&E/material spec fields)~~ ✅ (2026-07-01, FF&E schedule + A-602 sheet + `/ffe-research` skill). **Next: #6** (fold §4/§6.4 into `dimensional_rules`). Optional polish: render-verify on an actual Blender install; lighting placement-rule checks; task-layer auto-placement for kitchens/offices.
