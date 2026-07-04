# Persona-driven design layer — BUILT (2026-07-04)

Status: **BUILT + tested (25/25) + grounded (NLM DR) + adversarially scrutinized.** This is
the next layer of the functional-correctness / explainability work (see
`docs/functional-correctness-layer.md`, memory `[[rationale-layer]]`). Supersedes the
2026-07-03 QUEUED note; the in-flight `persona-to-element-model` workflow's Design synthesis
never completed (its 4 investigation maps were recovered from the journal and are the basis
below).

## The owner's idea (verbatim intent)
It is not enough to explain *why each element is in the work*. The design must first say
**WHO the client is and what their lifestyle is → and from that, why each element exists.**
Owner's example: a chill work-from-home person who takes morning coffee on the balcony (→ a
coffee nook) and reads before bed (→ a reading provision). Every element must trace back to a
real human activity of *this* client.

## The model — a causal chain (runs opposite to a geometry spec)
```
WHO + lifestyle  →  ACTIVITIES / rituals  →  a REQUIREMENT per activity  →  ELEMENT(s) that fulfil it
   (persona)         morning coffee, read     "a place for coffee"           balcony nook, reading chair
```
An element's "why it's here" becomes **"serves activity X (client trait Y)"**, not "declared
in spec". **Two-way coverage is the killer feature:**
- **GAP** — a stated activity with NO serving element → the design misses the person's life.
- **ORPHAN** — a lifestyle element serving NO stated activity → "why is this here?"

This is grounded, not invented: an NLM Deep Research (2026-07-04, notebook `053ff5e6`, 241
sources) independently reproduced this exact chain — NCIDQ/IDFX *programming*, Karlen &
Fleming *Space Planning Basics* (8-step), Peña & Parshall *Problem Seeking*, Space Syntax
adjacencies — and a canonical **12-activity taxonomy** matching ours 1:1. Distilled to
`knowledge/programming/architectural-programming-and-activity-taxonomy.md` (staged
`knowledge/_inbox/nlm-programming-2026-07-04.md`).

## What was BUILT (all in `pipeline/scripts/`)
1. **`activity_taxonomy.py`** — the DETERMINISTIC half. Two lookups:
   - `KIND_ACTIVITY` (kind → [activity]), built ON TOP of `placement_logic`'s existing kind
     role-sets (BED_KINDS, SEATING_KINDS, BATH_* families, TV families) so it can never drift
     from the FUNCTION gate; extended with dining/desk/wardrobe/storage.
   - `ACTIVITIES` (the 12-activity set; each carries `baseline` + `needs`/`zone`/`adjacency`).
   - `element_activities(el)` with a strict precedence: an explicit **`serves` tag WINS**
     (author-declared) → else UNION of the deterministic kind-default with any **SOFT name
     signal** (a Thai/EN keyword: "อ่านหนังสือ"→read, "เครื่องแป้ง"→groom) → else a
     polymorphic/untagged kind is **AMBIGUOUS** (`[]`, flagged, never guessed).
2. **`persona.py`** — schema + loader + `derive_requirements` + the home-aware two-way
   coverage checker + `report()→(results,verdict)` + `presence_context()` for rationale +
   `to_markdown()` for the deliverable.
3. **`specs/persona_condo_demo.json`** — the FICTIONAL demo persona (owner's example),
   `_fictional: true`, shareable (examples convention).
4. **`rationale.py`** — PRESENCE axis upgraded: with a persona, `presence_why` becomes
   "serves activity X — the client does Y (persona …)" grounded `persona`; a baseline element
   is grounded `activity`; an unjustified lifestyle element is flagged POSSIBLE ORPHAN (NOT
   grounded); the persona-less path is byte-identical to before.
5. **`test_persona.py`** — 25 tests (taxonomy, name-signal, serves-override, gap/orphan/
   ambiguous/baseline, home-aware aggregation, honesty boundary, degrade-never-throw, the real
   demo result, rationale integration + no-regression).

## The honesty split (the integrity of the layer)
- **DETERMINISTIC:** activity→requirement (a taxonomy lookup) and element→activity (kind map).
- **JUDGMENT:** persona free-text ("I read before bed") → an activity id (`read`). This is
  done ONCE, at persona-authoring time (LLM/human-assisted) and RECORDED on the persona as a
  structured `activity` field CITED to the source line. `persona.py` CONSUMES those structured
  activities — it never re-infers an activity from prose. A ritual with prose but no `activity`
  tag is FLAGGED "un-mapped (a judgment is owed)", never silently guessed.

## Coverage semantics (honest, degrade-never-throw)
- **HOME-AWARE:** `check(spec | [specs], persona)`. An activity is a GAP only when NO room in
  the home serves it (a bedroom is not faulted for lacking a kitchen). Orphans are per element.
- **baseline vs lifestyle:** sleep/groom/bathe/dress_store/store/dine/cook are BASELINE (a
  dwelling needs them regardless of stated lifestyle → a baseline element is never an orphan).
  work/read/relax/coffee_ritual/entertain/exercise/hobby are LIFESTYLE (an element serving one
  is justified only if the persona does it, else ORPHAN).
- **SEVERITY:** GAP/ORPHAN/AMBIGUOUS = WARN → deliverable **REVIEW**, never a render-blocking
  FAIL. A persona is inherently incomplete and a missing reading nook is a designer's call, not
  a safety breach like a FUNCTION FAIL. No persona → **UNWIRED** (never a silent pass, never a
  false gap). Rows share `{status, check, detail}` with `persona:` prefixes → drops into the
  same gate/deliverable machinery as clearance + placement.

## Demo result (`persona_condo_demo` × [living_condo, bedroom_suite])
- **coffee_ritual [must_have] → GAP** (no balcony nook) — the owner's exact point.
- **work [ritual] → GAP** (no WFH desk).
- **read [must_have] → MET** — via the name signal on "เก้าอี้อ่านหนังสือ", which `kind:
  armchair` alone would miss.
- **relax / entertain → MET** across both rooms (home-aware aggregation).
- All baseline (sleep/groom/bathe/dress) MET; 0 orphans; verdict **REVIEW**.

## Where it slots into 00→08 (the missing "programming pass")
- **Stage 00 intake** (`brief.json`): add a `persona`/lifestyle block (the schema below). The
  studio's PARKED vault template already had these fields (Household / Daily routine / WFH /
  entertains / Hidden needs) — the active pipeline dropped them; this restores them, machine-
  readable. `brief.json` is additive-friendly. **REAL persona = client data → local only,
  C-NNN not a name, band numerics before any outbound call** (`.claude/rules/client-privacy.md`).
- **Stage 01 brief** (`requirements.md`): `derive_requirements` emits the activity→requirement
  rows — the "program of requirements" the maps found MISSING (today's rows are only statutory/
  ergonomic/furniture). This is the Karlen-&-Fleming Criteria-Matrix step.
- **Stage 02/03 concept+layout**: the coverage check runs as an ADVISORY REVIEW; `concept.md`
  §1 adjacency can cite a *lifestyle* source alongside geometry/code.
- **Explainability**: `rationale.py` presence axis (BUILT).
- **Deliverable**: `persona.to_markdown` is a COVERAGE section; `report()` rows ride the QA
  checklist with `persona:` prefixes (wiring into `suite_package` is the next opt-in step).

## Persona schema (`studio-os/persona@0.1`)
`occupants[]`, `work_pattern{wfh, …}`, `values[]`, `daily_rituals[{ritual, activity, cite}]`,
`hobbies[{hobby, activity, cite}]`, `entertaining{frequency, activity}`, `must_have[]`/
`nice_to_have[]` (str or `{want, activity, cite}`), `deal_breakers[]`. The `activity` field is
the recorded judgment (free-text→activity), cited to the client's own line.

## Honest limitations (documented, not hidden)
- **Zone fidelity:** the @0.2 spec carries no window/orientation, so (like `placement_logic`
  refusing to model windows) coverage verifies an activity is served *somewhere in the home*,
  not that it sits in its ideal zone. In the demo, `read` is MET by a *living-room* reading
  chair though the persona reads *in bed* — honest MET at the home level, not bedside-verified.
- **`serves` tag is opt-in:** polymorphic kinds without a tag or name signal stay AMBIGUOUS
  (WARN "tag serves") — surfaced, not guessed.
- **Advisory only:** never blocks a render. If the owner later wants must-have gaps to hard-
  block, that is a one-line escalation in `persona.report`.

## Grounding (both DRs done + distilled)
- **DR#1** (programming + activity taxonomy, notebook `053ff5e6`, 241 sources) → `knowledge/programming/architectural-programming-and-activity-taxonomy.md`.
- **DR#2** (persona/UCD + two-way coverage + POE, notebook `e0eab101`, 247 sources) → `knowledge/programming/persona-ucd-two-way-coverage-and-poe.md`. It independently names the **"Two-Way Coverage Check"** with **"Gaps"** and **"Orphans"** as established (bipartite demand↔supply) method — the layer is grounded, not invented.

## Adversarial scrutiny (done — 3 lenses, 16 raised, 9 confirmed + fixed)
Notable: the baseline-exemption was all-or-nothing per element, so a **fused `headboard_tv`
(sleep+relax)** hid its unstated `relax` orphan — the SAME fused-vs-standalone blind spot the
FUNCTION layer exists to expose. Fixed (orphan now judged per lifestyle-activity, `entertain`
excluded). Also fixed: degrade-never-throw holes on non-dict elements/subrooms (persona +
rationale), a non-dict `rationale` field crash, a soft name-signal "met" now labelled SOFT, an
"entertaining: never" false GAP, priority-label mislabelling, unknown-`serves` typo now surfaced.
Tests grew 25→36; full pipeline suite green (persona 36, rationale 14, placement 46, repair 22,
clearance 83).

## Wired
- `rationale.py` presence axis (persona-grounded, per-element).
- `suite_package.py` discovers a persona (`find_persona_for`: `spec.persona` path/dict or a
  sibling `persona.json`) and threads it into `RATIONALE.md` — per-element, valid per-room.

## Still open / next
- Project-level (home) COVERAGE deliverable: run `persona.report([all room specs], persona)`
  when a project has its full set of specs (the per-room deliverable deliberately does NOT emit
  GAP rows, which need the whole home — it would false-gap "no kitchen in the bedroom").
- Stage 00/01: add the persona block to `brief.json` + emit the programming rows into
  `requirements.md` (the "programming pass").
- POE (DR#2) is the future rung: a persona's rituals become the checklist a finished home is scored against.
- A real (non-demo) persona flows only through the local, anonymized C-NNN path (privacy).
