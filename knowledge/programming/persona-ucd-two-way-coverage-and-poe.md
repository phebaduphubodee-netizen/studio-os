# Persona-driven (user-centred) residential design, two-way coverage & POE

**Tier:** REFERENCE (distilled from NLM DR 2026-07-04, notebook `e0eab101`; 312 sources fired,
247 ready / 65 errored). Staged sources:
`knowledge/_inbox/nlm-persona-poe-2026-07-04.md` (attribution wrapper) and
`knowledge/_inbox/nlm-persona-poe-2026-07-04-qa-history.json:9` (verbatim answer, turn 1 — the
citation anchor for every value below; all "qa-history turn 1" refs below point at that answer
body).
`knowledge/codes-th/` outranks any statutory overlap (the DR volunteers foreign values — 1200 mm
corridor, 300–500 lx — which are NOT Thai authority). Grounds the ADVISORY persona-coverage
layer; gates nothing. Nothing in this file is a statutory value.

Companion to `knowledge/programming/architectural-programming-and-activity-taxonomy.md` (the
activity→requirement side). This file is the PERSONA → coverage → evaluation side.

## User-Centred Design (UCD) + the client persona
UCD marks a shift from relying on designer intuition toward frameworks that empirically link
occupant behaviour to spatial interventions. The **client persona** translates a household's
qualitative lifestyle into quantitative spatial parameters. The DR names a **mixed-methods**
build; the source's list is open ("includes") — *"semi-structured interviews, on-site
observations of the client's current living conditions, spatial site analysis, standardized
questionnaires, and even digital trace data"*
(qa-history turn 1, "Building the Client Persona"). Persona dimensions (this is the
`studio-os/persona@0.1` schema):

| Dimension | Drives |
|---|---|
| Occupants + lifecycle stage | household composition, physical capabilities, family-lifecycle projection (the DR's examples: honeymoon phase, child-rearing, or aging-in-place) → decides whether the layout is *statically optimised* or *dynamically flexible* for multi-generational living |
| Work pattern (hybrid / WFH) | hybrid occupancy is **bimodal** — it *"often clusters on peak days (Tuesday–Thursday)"* — so the persona needs BOTH a dedicated acoustically-isolated focus zone AND flexible shared space; specifies STC-rated partitions + localised task light |
| Daily rituals | high-frequency time-bound routines (cooking, cleaning sequences) → room-flow logic + ergonomic dimensions (cooking → work triangle; counter height derived from the **primary user's elbow height**, see §Persona → mm below) |
| Hobbies / cognitive activities | dedicated zoning + storage — and, in the DR's own case study (*Jack Arch House*: occupants were aeromodellers with an appreciation for structural geometry/craftsmanship), the hobby drove **structure and material**, not just storage: an exposed brick jack-arch ceiling system + custom-integrated geometric furniture |
| Values / beliefs / identity | sustainability strategy; a sacred/altar zone; worldview alignment |
| Entertaining habits | fluid communal↔private transitions without disrupting quiet zones |

**Principle:** *every layout boundary, material, and furniture spec must correspond to a
documented occupant requirement — eliminating superficial decisions.* This is the persona-
grounded PRESENCE axis in `pipeline/scripts/rationale.py` and the no-orphan doctrine.

## Persona → quantitative parameter ("persona → mm")
The persona exists to *"translate a household's qualitative lifestyle into precise, quantitative
spatial parameters"*. These are the derivations the source actually names — quoted, so the
promotion carries values and not just topics (qa-history turn 1). All are REFERENCE
tier — a design-literature DR — and **none is a statutory value**.

| Persona trait | Derivation named by the source | Authority note |
|---|---|---|
| **Cooking / culinary habits** | *"culinary habits directly drive the kitchen work triangle and dictate countertop heights based on the primary user's elbow height to prevent musculoskeletal strain"* | The source names the **derivation basis**, and gives **no offset figure** — do not invent one. Compare the studio's fixed standard-adult worktop row, 85–90 cm, at `knowledge/ergonomics/casework-fixture-clearances-th-practice.md:121`: the persona rule is to derive the height from the *primary user's* elbow height rather than take a fixed standard. |
| **Hybrid worker** (occupancy *"often clusters on peak days (Tuesday–Thursday)"* → bimodal) | *"designers must balance dedicated, acoustically isolated focus zones with flexible shared spaces"*; specify **STC** (Sound Transmission Class) partitions + localised task lighting | The same source's ORPHAN example is the failure mode of ignoring this: over-allocated individual *"orphan desks"* for a hybrid worker who actually needs collaborative space. |
| **Elderly occupant / aging-in-place** | *"1200mm wide corridors, flush floor transitions, and zero-threshold showers"* | ⚠ **FOREIGN REFERENCE — not Thai authority.** The DR names no jurisdiction. `knowledge/codes-th/` is the sole source of Thai statutory dimensions and outranks this row; treat as advisory design intent only. |
| **Values / beliefs** | the source hedges — this *"might manifest in"* a net-zero sustainability strategy **or** the integration of a sacred zone, the DR's example being *"the specific integration of a sacred mandir within a multi-utility den"* | The DR names **no jurisdiction**. No dimension given by the source. |
| **Entertaining habits** | *"frequency, scale, and flow of social interactions"* → fluid transitions between communal living areas and private zones, so guests are accommodated without disrupting the home's quiet areas | No dimension given by the source. |

## The Two-Way Coverage Check (bipartite demand ↔ supply)
An established audit that maps **demand** (documented activities/rituals) to **supply**
(physical spaces/furniture). It surfaces two anomalies — the core of `persona.check()`:

- **GAP (Unmet Need):** a documented activity with NO supporting space/element. Real-world
  cost: occupants make ad-hoc, inefficient adjustments (retrofitted AC where thermal comfort
  was neglected; hallway clutter where a hobby's storage was omitted).
- **ORPHAN (Unused Space):** an element built but serving NO documented activity → wasted
  capital + square footage (monumental stairs nobody uses; *"neglected communal spaces lacking
  visual privacy"*; *over-allocated "orphan desks" for a hybrid worker who actually needs
  collaborative space*).

Value: reallocate resources away from orphans to resolve gaps **before construction**. Our
implementation adds a third honest state — **AMBIGUOUS** (a polymorphic element whose activity
can't be determined → "tag `serves`", never guessed) — and exempts **baseline** dwelling needs
(sleep/wash/store/eat) from the orphan test (they justify themselves).

## Post-Occupancy Evaluation (POE) — the feedback loop (future rung)
Once the home is inhabited (*"typically for 12 months or more"*), evaluate whether it supports
the occupants' routines.
- **Dimensions:** Functional (room sizes/layouts/furniture actually support domestic
  workflows) · Behavioral (social well-being, interaction, privacy, territoriality, sense of
  belonging) · Technical (structural integrity + IEQ).
- **Depths:** Indicative (quick walkthrough + structured interview) · Investigative (detailed
  occupant questionnaire compared against performance standards) · Diagnostic (calibrated
  physical monitoring sensors paired with occupant feedback).

**Diagnostic POE — instrument per IEQ axis, and its metric.** The DR answers *methods* and
*metrics* together; both halves are below (qa-history turn 1, "methods and metrics"):

| IEQ axis | Instrument (method) | Metric / target |
|---|---|---|
| Thermal comfort | automated temperature + relative-humidity **data loggers**, or a **globe thermometer** | 20–25 °C air temp; 30–55 % RH; often calculated as **PMV** (Predicted Mean Vote) |
| Acoustic comfort | **calibrated sound-level meter** | dBA + **STC** — verifies speech privacy and ambient-noise minimisation |
| Visual comfort | **handheld lux meter** | lux + **daylight factor** %; glare control; task light "e.g. 300–500 lx for workspaces" — ⚠ FOREIGN reference figure, not Thai authority |
| Indoor air quality | **NDIR** (non-dispersive infrared) CO₂ sensor; particulate sensing | CO₂ **< 1000 ppm** (stated for cognitive + sleep health); PM2.5 |
| Energy use intensity | **smart energy sub-meter** | EUI in kWh/m²/yr, checked against the design-stage model |

POE is out of scope for the current advisory layer but is the natural next rung: a persona's
rituals become the checklist a POE scores the finished home against — closing an empirical,
loop-based design cycle.
