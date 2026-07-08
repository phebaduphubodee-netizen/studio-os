# self-audit -- PRJ-2026-002_c001-house

**doubt-score 23**  (5 open, 0 owner-resolved)  CRITICAL 0 · HIGH 0 · MEDIUM 2 · LOW 3

> The doubt-score reads meaningfully ONLY with the coverage line below: a low score under thin coverage means *did not look*, not *clean*.

## Ranked doubts (where I am least certain, worst first)
1. **[MEDIUM] facade_candidate** @sitting_room — glazed-facade candidate in sitting_room (score 5, glazed_facade, len 4898mm)
   - why: a strong thin-line run along the room's south edge looks like a glazed facade / window wall, but glass-vs-wall is an owner call
   - resolve: set facade true|false in confirm_facade_stub, sign `by`, and merge into placement-review.json confirmed[]
2. **[MEDIUM] zone_open** @sitting_room — 1 zone_open flag(s) in sitting_room
   - why: an open below-grade / outdoor zone PROPOSAL the machine refuses to auto-decide -- is this element indoor-this-floor or below grade / outside?
   - resolve: sign the zone on the piece (confirmed_zone) to resolve; STRONG/MEDIUM/LOW confidence lives in the gate stdout, not the marker
3. **[LOW] glazing_unresolved** — 294 unresolved global glazing-line candidates (246 strong) -- the raw pile facade_reader distils per-room
   - why: each is a thin-line run that MIGHT be glass; the pile is a review artifact (furniture double-lines can score 'strong'), not per-room truth
   - resolve: confirm real glass runs and copy their segments into the walls JSON manual_additions with a signed `by`; ignore the rest
4. **[LOW] long_thin** @master_bedroom — 1 long_thin flag(s) in master_bedroom
   - why: a narrow dropped component that MIGHT be a slim real piece (a shelf/ledge), not a dimension tick
   - resolve: confirm on the sheet; if a real piece, add it to the spec
5. **[LOW] zone_exterior_linework** @sitting_room — 1 zone_exterior_linework flag(s) in sitting_room
   - why: a candidate that may be exterior linework drawn through the storey
   - resolve: confirm indoor/outdoor and sign it

## Coverage (which of my doubt-sources actually reported)
- **placement_gate**: READ  verdict=REVIEW  calibration=PASS
- **facade**: READ  candidates=1  resolved=0
- **glazing**: READ  
- **sourceability**: UNWIRED  reviewed=2  errored=0  fail=0  review=0  unwired_elements=15
- **persona**: UNWIRED   — no persona.json for this project -- GAP/ORPHAN coverage cannot be computed (not a pass)

READ = reported; ABSENT = artifact/input not present; UNWIRED = ran but no eligible data (never a pass); ERROR = source failed (a blind spot in the audit itself). CRITICAL = confident-WRONG (regression/build-blocker), not doubt; HIGH/MEDIUM/LOW = open doubt.
