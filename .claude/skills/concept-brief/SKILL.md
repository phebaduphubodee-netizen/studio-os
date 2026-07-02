---
name: concept-brief
description: >
  Stage 02 concept author. From a human-confirmed brief.json (+ client
  profile), writes the zoning / style-direction / mood-narrative concept
  document that Stage 02's contract requires, grounded in the studio's own
  design principles with vault citations. Use when the user asks for a
  concept, style direction, zoning proposal, or "start stage 02".
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

# /concept-brief — brief.json → 02_concept/concept.md

1. Preconditions: `00_intake/brief.json` exists and Stage 01 outputs exist
   (or the human explicitly waives). Read `02_concept/_contract.md`.
2. Assemble the five-role context package (projects/CLAUDE.md):
   - Authority: budget ceiling + fixed constraints from brief.json; any
     applicable codes-th value (search first — if codes-th is empty for the
     topic, write "codes-th pending M1.2" rather than inventing values).
   - Exemplar: `python3 scripts/vault_search.py "design principles"` and pull
     the studio's principles + a matching examples/ artifact if one exists.
   - Rubric: the gate criteria from the contract + vault checklist Stage 2–3.
3. Author `02_concept/concept.md`:
   - Zoning: rooms → functions → adjacencies (mm/m², reference the plan).
   - Style direction: named style + its restrictive edges ("Japandi forbids
     ornamental moulding" class of rules); flag contradictions NOW, not at
     render time. 60/30/10 palette stated as three concrete finishes.
   - Mood narrative: 5–10 sentences, client-facing tone.
   - Citations: every studio-standard claim → vault path (cite-or-drop).
4. Self-check against the rubric before finishing; list any unmet item.
5. Gate: human review. MARS parallel reviewers arrive Phase 4 — until then
   end by asking the human to approve or annotate the concept.
