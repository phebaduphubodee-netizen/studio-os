# Persona-driven (user-centred) residential design, two-way coverage & POE

**Tier:** REFERENCE (distilled from NLM DR 2026-07-04, notebook `e0eab101`, 247 sources —
staged at `knowledge/_inbox/nlm-persona-poe-2026-07-04.md` + qa-history). `codes-th/` outranks
any statutory overlap (the DR volunteers foreign values — 1200 mm corridor, 300–500 lx — which
are NOT Thai authority). Grounds the ADVISORY persona-coverage layer; gates nothing.

Companion to `architectural-programming-and-activity-taxonomy.md` (the activity→requirement
side). This file is the PERSONA → coverage → evaluation side.

## User-Centred Design (UCD) + the client persona
UCD replaces designer intuition with frameworks that empirically link occupant behaviour to
spatial decisions. The **client persona** translates a household's qualitative lifestyle into
quantitative spatial parameters, built via interviews + on-site observation + questionnaires.
Persona dimensions (this is the `studio-os/persona@0.1` schema):

| Dimension | Drives |
|---|---|
| Occupants + lifecycle stage | static vs flexible / aging-in-place specs (e.g. zero-threshold) |
| Work pattern (hybrid / WFH) | acoustic focus zone vs flexible shared space; task light |
| Daily rituals | room-flow logic + ergonomic dimensions (cooking → work triangle, counter height) |
| Hobbies / cognitive activities | dedicated zoning + storage |
| Values / beliefs / identity | sustainability strategy; a sacred/altar zone; worldview alignment |
| Entertaining habits | fluid communal↔private transitions without disrupting quiet zones |

**Principle:** *every layout boundary, material, and furniture spec must correspond to a
documented occupant requirement — eliminating superficial decisions.* This is the persona-
grounded PRESENCE axis in `rationale.py` and the no-orphan doctrine.

## The Two-Way Coverage Check (bipartite demand ↔ supply)
An established audit that maps **demand** (documented activities/rituals) to **supply**
(physical spaces/furniture). It surfaces two anomalies — the core of `persona.check()`:

- **GAP (Unmet Need):** a documented activity with NO supporting space/element. Real-world
  cost: occupants make ad-hoc, inefficient adjustments (retrofitted AC where thermal comfort
  was neglected; hallway clutter where a hobby's storage was omitted).
- **ORPHAN (Unused Space):** an element built but serving NO documented activity → wasted
  capital + square footage (monumental stairs nobody uses; *over-allocated "orphan desks" for
  a hybrid worker who actually needs collaborative space*).

Value: reallocate resources away from orphans to resolve gaps **before construction**. Our
implementation adds a third honest state — **AMBIGUOUS** (a polymorphic element whose activity
can't be determined → "tag `serves`", never guessed) — and exempts **baseline** dwelling needs
(sleep/wash/store/eat) from the orphan test (they justify themselves).

## Post-Occupancy Evaluation (POE) — the feedback loop (future rung)
After ≥12 months, evaluate whether the built home supports the occupants' routines.
- **Dimensions:** Functional (layouts/furniture support workflows) · Behavioral (privacy,
  territoriality, belonging) · Technical (integrity + IEQ).
- **Depths:** Indicative (walkthrough/interview) · Investigative (questionnaire vs standard) ·
  Diagnostic (calibrated sensors + feedback).
- **Metrics:** thermal 20–25 °C / 30–55 % RH (PMV); acoustic dBA / STC; visual lux + daylight
  factor (300–500 lx task); IAQ CO₂ <1000 ppm + PM2.5; EUI kWh/m²/yr.

POE is out of scope for the current advisory layer but is the natural next rung: a persona's
rituals become the checklist a POE scores the finished home against — closing an empirical,
loop-based design cycle.
