---
name: qa-report
description: >
  Aggregates a render batch's scorecards against qa/thresholds.yaml into the
  human QA summary + repair queue for a project's 05_qa/ stage. Use when the
  user asks for a QA report, "score this batch", or what failed and why.
  Reads thresholds; NEVER edits them (PR-only file).
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
---

# /qa-report — scorecards + thresholds.yaml → 05_qa/qa-report.md

1. Read `qa/thresholds.yaml` (pillar → pass/warn bounds). It is read-only.
2. Collect scorecards: `05_qa/*.json` for the batch (per-artifact metric
   values; Phase 3 wires automatic scoring — until then scorecards may be
   hand-filled or produced by pipeline/scripts validators as they land).
3. For each artifact × pillar: classify pass / warn / fail per thresholds.
   Missing metric = "not scored" (never assume pass). Every number in the
   report traces to a scorecard file; no invented scores.
4. Write `05_qa/qa-report.md`:
   - Batch summary table: artifact → per-pillar status → verdict.
   - Warn list with metric values (soft-gate passes carry their warning).
   - Repair queue: hard failures grouped by fail action (reseed / material
     repair / relight / reject — the pillar→action map is blueprint §9.3,
     docs/STUDIO-OS_Implementation_Blueprint.md; thresholds.yaml holds only
     the numeric bounds), ordered by gate number — fail fast, spend late.
   - Escalations: anything failing after 3 repair iterations → human triage.
5. Post `R_` naming check on batch files (root CLAUDE.md convention);
   mismatches go in the report, renames only via scripts.
6. If thresholds seem wrong, propose a change in the report text — the file
   itself changes only via PR + golden-set regression.
