# Skills
Format: skills/<name>/SKILL.md with frontmatter (description, allowed-tools;
disable-model-invocation: true for sensitive ops like the future
bom-generate and client-deliver).

## Present
- The blueprint-§13 five (added 2026-07-02, Phase 1):
  `intake-parse` (00_intake → brief.json + inventory.md; e2e-tested on
  PRJ-2026-001_test-run incl. prompt-injection quarantine),
  `concept-brief` (brief → 02_concept/concept.md, vault-cited),
  `qa-report` (scorecards × thresholds.yaml → 05_qa report + repair queue),
  `usd-validate` + `material-lint` (convention/PBR text checks now; usd-core
  and render-time QA arrive Phases 2–3).
- `ffe-research/` — back-office FF&E product research → `03_layout/ffe-candidates.json`
  + `scripts/ffe_schedule.py` renders the driftless `ffe-schedule.md`. Feeds Stage 03 (Layout)
  and, via the human-triggered `bom-generate`, Stage 07. Added 2026-07-02 (ahead of the blueprint
  five — it's back-office research, and the `tools/` AI layer makes it immediately useful).
