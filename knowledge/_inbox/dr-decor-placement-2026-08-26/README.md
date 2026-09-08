# DR unit — decor placement + styling composition grammar

- **Date:** 2026-08-26 · **Lane:** NLM Deep Research (owner-initiated: "ทำ DR เกี่ยวกับการจัดวางของตกแต่งและ model ต่าง ๆ ในงาน")
- **Notebook:** `adee1655-35f6-47c8-8c62-44d2577ac261` — "DR: decor placement + styling composition grammar 2026-08-26"
- **Sources:** 140 imported → 125 ready / 15 error. DR slot 1/20 (24h). Asks: 6 (main + 5 drills), budget ≤10 held.
- **Tier:** REFERENCE. Distilled → `knowledge/styles/decor-placement-grammar.md` (same commit).
- **Pre-DR gap sweep:** 4-agent fan-out over knowledge/ · docs+qa · pipeline instruments · prior DRs confirmed
  the vault knows the BED to the millimetre and 60/30/10, but held no numeric rules for arranging decor
  relative to furniture/each other. Questions aimed only at gaps; nothing here duplicates
  `bed-styling-grammar.md`, the 08-17 DR set, or `color-composition.md`.

## Files in this unit
| file | content |
|---|---|
| `qa-history.json` | full 7-turn transcript (canonical answers; turn 1≈turn 2 = retry duplicate) |
| `sources-manifest.json` | full source list of the notebook (titles = attribution for [n] markers) |
| `ask-02-provenance-check.md` | first provenance pass — exposed the CIRCULAR citation (see lesson) |
| `ask-03-independent-sources.md` | citations forced past the synthesis report; per-claim tier verdicts |
| `ask-04-story-to-list-method.md` | 5 documented story→object-list methods; bed-side allocation ABSENT |
| `ask-05-style-membership.md` | 8-class style-membership matrix (warm contemporary tropical minimal) |
| `ask-06-room-completeness.md` | zone-by-zone inventory; NO whole-room count exists; shelf-grid grammar |

## LESSON — the DR cites its own synthesis report (new trap, same family as flattering-scorer)
NotebookLM Deep Research writes a synthesis report titled with OUR research question and imports it as a
source. The first provenance ask (`ask-02`) answered "all numbers stated verbatim in your sources" — quoting
that report. **"Verbatim in the sources" is circular when the source is the DR's own synthesis.** The tell:
the report's own table carried EMPTY provenance cells. Every future DR provenance check must name-exclude
the synthesis document and demand independent titles + quotes (`ask-03` pattern).

## Tier verdicts (from ask-03, per claim)
- **CITED (≥2 independent sources, quoted):** rug numbers (18–24″ extension · 12–18″ wall clearance ·
  bench +12″); wall-art numbers (2/3–3/4 furniture width · 57–60″ centre · 6–10″ above headboard);
  odd-rule 3/5/7 with surface mapping; decorative triangle / tallest-at-back; medium element = ½–⅔ of tall.
- **SINGLE source:** surface occupancy 60/40 (Roomtodo); shelf ≥25% empty + books ≤⅓ (Tip Top);
  identical-items 2/3-in-a-row bounds (Creek Line House); bench all-legs-on-rug (Aosom).
- **SYNTH-ONLY (report's own estimate — declared assumption, test starting point, never cite as convention):**
  per-surface vacancy % table; low element 0.15–0.25 ratio; the 3-register inventory count matrix
  (individual rows ARE independently supported — see ask-03 §c).
- **ABSENT from literature (stays ours to decide):** which bed side belongs to which resident (story
  decision per ORD-2026-08-25c); whole-room total object count; volumetric scaling for mismatched shapes;
  art clearance over >48″ headboards (sources split).

## Consumption map (who reads this — no queue without a consumer)
1. **ORD-2026-08-25c story-driven styling** (NOT-OBEYED, open): ask-04's five documented methods ground
   steps 1→3; "bed-side = story decision" is now a cited absence, not a guess. Vignette rules feed step 4.
2. **STY-2 / ORD-2026-08-23** (missing half): ask-05's 8-class matrix IS the style_verdict criteria content
   the mechanism slot has been waiting for.
3. **D7 (`qa/deliverable-standard.json` ≥12 loose objects):** confirmed uncited; sources are per-zone.
   PROPOSED (owner/lane call, not edited here): replace with zone checklist from ask-06.
4. **`qa/blenderkit-month-classes.json`** wall_art + plant bands: cited bands now exist (art 2/3–3/4 of
   furniture width; plants floor 900–1500 mm h / pot Ø300–450, tabletop 300–600 / Ø150–250, shelf
   150–300 / Ø100–150). Add WITH these citations before first fetch — not edited here (qa/ lane owns it).
5. **C2 standing item "shelves empty / staged 3-items-in-7-bays":** shelf-grid grammar (X-pattern,
   ≥25% empty per shelf, ≤3 identical) is the first instrument-able answer.
6. **Critic-debt rows on styling density/nightstand contents:** zone counts in ask-06.
