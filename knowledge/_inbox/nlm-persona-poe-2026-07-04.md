# NLM Deep Research — persona-based residential design & post-occupancy evaluation (2026-07-04)

**Tier:** REFERENCE (distilled into `knowledge/programming/persona-ucd-two-way-coverage-and-poe.md`; grounds the ADVISORY persona-coverage layer, which never gates a deliverable).
**Notebook:** `e0eab101-5c80-4aca-b0ad-81053d068d5b` — "DR: Persona-based residential design & post-occupancy evaluation".
**Conversation:** final answer = **turn 1** (single-shot; no `--iterate`).
**DR corpus:** 312 sources fired, **247 ready / 65 errored**. Grounding valid.
**Transcript:** `nlm-persona-poe-2026-07-04-qa-history.json` (this dir; verbatim).
**Marker note:** `[n]` unresolved (no answer→title map); provenance carried at the concept/authority level — the answer names User-Centred Design, the **Two-Way Coverage Check (bipartite demand↔supply)**, Post-Occupancy Evaluation (functional/behavioral/technical; Indicative/Investigative/Diagnostic), and standard IEQ metrics (PMV, STC/dBA, lux, CO₂/PM2.5, EUI). Some values are foreign standards (e.g. 1200 mm elderly corridor, 300–500 lx workspace) — `codes-th` outranks any statutory overlap.

## Why this matters (independent validation of the built layer)
This DR describes the persona-driven design layer we built as ESTABLISHED methodology, not an invention:
- **Client Persona** translates a household's qualitative lifestyle into quantitative spatial parameters, across exactly our schema dimensions: **Occupants/lifecycle, Work patterns (hybrid/WFH), Daily rituals, Hobbies, Values, Entertaining habits.**
- Goal: *"every layout boundary, material choice, and furniture specification corresponds directly to a documented occupant requirement, eliminating superficial decisions"* — this is precisely `rationale.py`'s persona-grounded PRESENCE axis + the no-orphan doctrine.
- **The Two-Way Coverage Check** — *"rooted in bipartite graph theory... maps demand (documented occupant activities/rituals) to supply (physical spaces/furniture assets)"* — is exactly `persona.check()`. It names the two anomalies with OUR terms:
  - **Gaps (Unmet Needs):** a documented activity with no supporting space/element → occupants make ad-hoc inefficient adjustments (retrofitted AC; hallway clutter from omitted hobby storage).
  - **Orphans (Unused Spaces):** an element built but serving no documented activity → wasted capital/area (monumental stairs nobody uses; *"over-allocation of individual orphan desks for a hybrid worker who actually needs collaborative space"*).
  - *"reallocate resources away from Orphan elements to resolve critical Gaps before construction."*

## Post-Occupancy Evaluation (POE) — the feedback loop (future work)
Assess (after ≥12 months) whether the built home supports the occupants' routines. Three dimensions: **Functional** (do layouts/furniture support workflows), **Behavioral** (privacy, territoriality, belonging), **Technical** (integrity + IEQ). Three depths: **Indicative** (walkthrough/interview), **Investigative** (questionnaires vs standards), **Diagnostic** (sensors + feedback). Metrics: thermal (20–25 °C, 30–55 % RH, PMV), acoustic (dBA, STC), visual (lux, daylight factor; 300–500 lx task), IAQ (CO₂ <1000 ppm, PM2.5), EUI (kWh/m²/yr).

*POE is the empirical loop that would eventually close on real projects — out of scope for the current advisory layer, but the natural next rung (a persona's rituals become the checklist a POE scores against).*

## Consumed by
- `pipeline/scripts/persona.py` — the two-way coverage checker (`check`/`report`) IS the "Two-Way Coverage Check"; GAP/ORPHAN are the named anomalies; the persona schema fields match the DR's persona dimensions.
- `pipeline/scripts/rationale.py` — the persona-grounded PRESENCE axis ("every element corresponds to a documented occupant requirement").
