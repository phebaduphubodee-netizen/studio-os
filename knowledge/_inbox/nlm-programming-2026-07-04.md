# NLM Deep Research — architectural programming & residential activity taxonomy (2026-07-04)

**Tier:** REFERENCE (NotebookLM DR — distilled into `knowledge/programming/architectural-programming-and-activity-taxonomy.md`; used only by the ADVISORY persona-coverage layer, which never gates a deliverable).
**Notebook:** `053ff5e6-17a0-4f39-ab80-e84a6ec4068d` — "DR: Architectural programming & residential activity taxonomy".
**Conversation:** final answer = **turn 1** (single-shot; no `--iterate`, per the "tight-brief → omit iterate" lesson so it did not drift off residential programming).
**DR corpus:** 343 sources fired, **241 ready / 102 errored**. Grounding valid.
**Transcript:** `nlm-programming-2026-07-04-qa-history.json` (this dir; verbatim answer).
**Marker note:** `[n]` in the answer are NotebookLM answer-local citations into the 241-source corpus; the CLI exposes no answer→title map, so provenance is carried at the AUTHORITY level — every claim below names its authority: **NCIDQ/IDFX** (programming as a graded competency), **Karlen & Fleming, _Space Planning Basics_** (the 8-step pre-design procedure), **Peña & Parshall, _Problem Seeking_** (Function/Form/Economy/Time determinants), **Neufert _Architects' Data_ + NKBA** (FF&E footprints), **Space Syntax** (adjacency/circulation), **Ajzen, Theory of Planned Behavior** (activity-comfort framing). These named authorities ARE the resolved citations.

## Question (verbatim)
> In residential interior design, what is the established methodology of architectural PROGRAMMING (activity-based space planning)? Detail the process by which a designer turns a client's lifestyle and daily routines into a program of requirements: the causal chain from at-home ACTIVITIES to spatial/functional REQUIREMENTS to furniture/ELEMENTS to ADJACENCIES between zones. Also provide a canonical TAXONOMY of at-home residential activities … and, for each activity, the furniture and spatial zone it typically requires plus its preferred adjacencies … Cite authorities such as Karlen and Fleming Space Planning Basics, Neufert Architects Data, and NCIDQ programming standards.

## Answer highlights (turn 1 — verbatim in the qa-history.json)

**Programming = a systematic pre-design phase** that identifies/analyses/documents a project's functional problems BEFORE design solutions (NCIDQ core competency; IDFX weights Pre-Design 15% + Programming & Adjacencies 16%).

**The causal chain (this is exactly the persona layer's model):**
1. **Activities** — identify the occupants' daily actions/habits (comfort = physical control over the environment while doing them; Ajzen).
2. **Requirements** — activities dictate spatial/functional requirements; a space lacking the acoustic privacy / clearance / lighting an activity needs creates "friction" that disrupts the routine.
3. **Elements (FF&E)** — requirements determine the furniture/fixtures and their anthropometric footprints (Neufert, NKBA).
4. **Adjacencies** — elements/zones linked via Space Syntax (circulation + adjacency demand).

**Karlen & Fleming 8-step procedure:** (1) multi-tiered interview (Executive/Managerial/Operations — the Operations level = *daily routines, storage, equipment footprints*); (2) behavioural observation + existing-asset inventory; (3) verify shell/site/solar/plumbing/code; (4) organise data; (5) research unknowns; (6) analyse relationships → *functional affinities* + *scheduling affinities* (multi-use) + environmental alignment; (7) diagram — **the Criteria Matrix** cross-references every room × requirements (sqft, adjacency, plumbing, daylight) → bubble/adjacency diagrams; (8) summarise the program for client approval before schematic design.

**Canonical taxonomy — TWELVE primary activities** (zone · FF&E · adjacencies), from the answer:
1. **Sleeping** — Private · bed, nightstands, dressing chest · adj. primary bath/dressing/linen; east morning sun, low noise.
2. **Working** — Private/Focus · desk, ergonomic task chair, file cabinet, credenza · adj. foyer/powder; diffuse north light, acoustic isolation.
3. **Reading** — Intimate/Quiet · lounge chair, ottoman, side table, floor lamp · adj. bedroom/living corner/library; shielded acoustic corner + directional task light.
4. **Dining** — Public/Social · dining table, chairs, sideboard/buffet · adj. kitchen, lounge, powder.
5. **Cooking** — Service · range, fridge, sink, dishwasher, island · adj. dining, garage, trash; 12–26 ft work triangle.
6. **Coffee / tea rituals** — Intimate/Gathering · bistro table, two accent chairs, bar/espresso console · adj. kitchen/bedroom/library; **east-facing sunrise exposure**.
7. **Lounging / relaxing** — Public/Social · sofa/sectional, lounge chairs, coffee table, media console · adj. dining/terrace/foyer; western daylight.
8. **Entertaining guests** — Public · modular seating, bar carts, dining extenders, credenzas · adj. living, deck, guest powder.
9. **Grooming / bathing** — Private · shower, tub, WC, lavatory vanity, linen · adj. bedroom/dressing/hall; exhaust ventilation + task light.
10. **Dressing / storage** — Private · wardrobe armoire, closet shelves, bench · adj. bedroom/bath/laundry.
11. **Exercise** — Private/Semi-private · treadmill, yoga mat, weight bench · adj. bath/outdoor/utility; fresh-air supply, damping floor.
12. **Hobbies (craft/art)** — varies · craft worktop, task seat, storage bins · adj. utility/office/garage; high-CRI light, resistant surfaces.

## Consumed by
- `pipeline/scripts/activity_taxonomy.py` — `ACTIVITIES` (the 12-activity set + each activity's requirement: needs / zone / adjacency) and `KIND_ACTIVITY`. This DR CONFIRMS the taxonomy was not invented — it matches the established set 1:1 (we split grooming/bathing into `groom`+`bathe` and add a generic `store` beyond `dress_store`).
- `pipeline/scripts/persona.py` — the causal chain (activity → requirement → element) + the Criteria-Matrix idea (a room × requirement grid) is the persona-coverage report.

## Remaining gap → DR#2 (fired 2026-07-04)
Persona-based / user-centred method (building + applying a client persona) and POST-OCCUPANCY EVALUATION (measuring whether a built home supports its occupants' rituals; the UNMET-need vs ORPHAN-space framing that grounds the two-way coverage check). → `nlm-persona-poe-2026-07-04.md` (pending).
