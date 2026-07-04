# Architectural programming & residential activity taxonomy

**Tier:** REFERENCE (distilled from NLM DR 2026-07-04, notebook `053ff5e6`, 241 sources —
staged at `knowledge/_inbox/nlm-programming-2026-07-04.md` + qa-history). Authority order
still holds: `codes-th/` > client contract > studio standards > this reference. Nothing here
gates a deliverable; it grounds the ADVISORY persona-coverage layer.

**Authorities named in the source answer:** NCIDQ / IDFX (programming as a graded
competency); Karlen & Fleming, *Space Planning Basics* (the 8-step pre-design procedure);
Peña & Parshall, *Problem Seeking* (Function / Form / Economy / Time); Neufert *Architects'
Data* + NKBA (FF&E footprints); Space Syntax (adjacency & circulation); Ajzen, *Theory of
Planned Behavior* (activity comfort = physical control while performing a routine).

## The programming causal chain
Architectural **programming** is the systematic pre-design phase that identifies and
documents a project's functional problems *before* a design solution is drawn. Its core
chain is the spine of the persona-driven design layer:

```
WHO + lifestyle  →  ACTIVITIES / rituals  →  a REQUIREMENT per activity  →  ELEMENT(s) (FF&E)  →  ADJACENCIES
   (persona)         daily actions/habits     spatial + functional need      furniture footprint     zone links
```

- **Activities → Requirements:** an activity dictates a spatial/functional requirement
  (clearance, acoustic privacy, light). A space that lacks it creates *friction* that
  disrupts the routine.
- **Requirements → Elements:** the requirement determines the FF&E and its anthropometric
  footprint (Neufert / NKBA).
- **Elements → Adjacencies:** zones are linked by circulation + adjacency demand (Space
  Syntax); a **Criteria Matrix** cross-references every room × requirement (area, adjacency,
  plumbing, daylight) — the diagnostic grid the persona-coverage report mirrors.

Karlen & Fleming's 8 steps: multi-tiered interview (Executive / Managerial / **Operations =
daily routines, storage, equipment**) → behavioural observation + asset inventory → verify
shell/site/code → organise data → research unknowns → analyse *functional* + *scheduling*
affinities → diagram (Criteria Matrix → bubble/adjacency) → summarise the program for
approval before schematic design.

## Canonical residential activity taxonomy (12 primary activities)
Zone · typical FF&E · preferred adjacencies (+ environmental note). This is the reference
basis for `pipeline/scripts/activity_taxonomy.py::ACTIVITIES`.

| # | Activity | Zone | FF&E (elements) | Adjacencies / environment |
|---|----------|------|-----------------|---------------------------|
| 1 | Sleeping | Private | bed, nightstands, dressing chest | primary bath / dressing / linen; **E morning sun**, low noise |
| 2 | Working (WFH) | Private / focus | desk, task chair, file cabinet, credenza | foyer / powder; diffuse **N light**, acoustic isolation |
| 3 | Reading | Intimate / quiet | lounge chair, ottoman, side table, floor lamp | bedroom / living corner / library; shielded corner + **task light** |
| 4 | Dining | Public / social | dining table, chairs, sideboard/buffet | **kitchen**, lounge, powder |
| 5 | Cooking | Service | range, fridge, sink, dishwasher, island | dining, garage, trash; 12–26 ft work triangle |
| 6 | Coffee / tea ritual | Intimate / gathering | bistro table, 2 accent chairs, bar/espresso console | kitchen / bedroom / library; **E-facing sunrise** |
| 7 | Lounging / relaxing | Public / social | sofa/sectional, lounge chairs, coffee table, media console | dining / terrace / foyer; W daylight |
| 8 | Entertaining guests | Public | modular seating, bar cart, dining extenders, credenza | living, deck, guest powder |
| 9 | Grooming / bathing | Private | shower, tub, WC, lavatory vanity, linen | bedroom / dressing / hall; exhaust vent + task light |
| 10 | Dressing / storage | Private | wardrobe armoire, closet shelves, bench | bedroom / bath / laundry |
| 11 | Exercise | Private / semi | treadmill, yoga mat, weight bench | bath / outdoor / utility; fresh air, damping floor |
| 12 | Hobbies (craft/art) | Varies | craft worktop, task seat, storage bins | utility / office / garage; high-CRI light |

**Implementation note:** `activity_taxonomy.py` splits #9 into `groom` (basin/WC) and `bathe`
(shower/tub) to match the pipeline's existing bathroom kind-families, and adds a generic
`store` alongside `dress_store`. Zone/adjacency are ADVISORY narrative in the code — the
pipeline's @0.2 spec carries no window/orientation data, so (as with `placement_logic`
refusing to model windows) the coverage checker verifies that an activity is *served
somewhere in the home*, not that it sits in its ideal zone. That location-fidelity gap is
documented honestly, not hidden.
