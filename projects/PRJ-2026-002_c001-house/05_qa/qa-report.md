# Stage 05 — QA report · PRJ-2026-002 · batch 001 · 2026-07-02
Thresholds: qa/thresholds.yaml v1 (read-only; no change proposed this batch).
Scorecards: 05_qa/scorecard_R_PRJ002_MasterSuite_Cam01_v01_roll{1,2}.json
(mirror: qa/reports/PRJ-2026-002/). Judge-variance rule: multi-roll mean, ±0.5.

## Batch summary — R_PRJ002_MasterSuite_Cam01_v01.png (hybrid pro tier, registry v004)
| Pillar (thresholds key) | Bound | Value | Status |
|---|---|---|---|
| client_qa.judge_score | pass ≥ 4 /5 | mean 4.75 (rolls 4.5 SHIP, 5.0 SHIP) | **PASS** |
| prompt_qa.soft_tifa_mean | ≥ 0.85 | no scorer wired (Phase 3) | not scored |
| image_qa.brisque | ≤ 30 | no scorer wired (Phase 3) | not scored |
| material_qa.* | per key | no scorer wired (Phase 3) | not scored |
| lighting_qa.source_triangulation_deg | ≤ 5° | no scorer wired (Phase 3) | not scored |
| camera_qa.homography_residual_px | ≤ 2 px | no scorer wired; nearest proxy = overlay eyeball PASS (batch-manifest SC-4, advisory only) | not scored |
| consistency_qa.warp_error | warn 10% | single-view batch — n/a | n/a |
| brand_qa.delta_e00 | ≤ 1.0 | client C-001 has no brand palette on file | n/a |
| revision_qa.background_lpips_delta | ≤ 0.05 | no post-edit/upscale this batch | n/a |

Verdict basis: the only wired pillar (LLM-judge rubric) passes with margin; every
unwired pillar is declared NOT SCORED per skill rule (never assumed pass).
Per-dimension judge means: palette 5, lighting 5, composition 5, furniture_realism 4,
room_context 5, styling_and_life 5, proportion 5, photoreal 4.5 (4→5 across rolls).

## Warn list
- (soft) photoreal_believability roll-split 4/5 — mean 4.5; within ±0.5 variance;
  roll-2 defect notes: flat far-left dark wall, wood-grain repetition on wardrobe
  doors. Same family as the known clay-side 0.5-gap (strip-light uniformity /
  grain variation) — candidate fix is build_room clay-side, GATE-EVIDENCED ONLY
  (phase-status memory), not a repair-queue item for this batch.

## Repair queue
Empty — no hard failures. Repair iterations used: 0 of 3.

## Escalations
None.

## Naming check (root CLAUDE.md convention)
- assets/projects/PRJ-2026-002/renders/R_PRJ002_MasterSuite_Cam01_v01.png ✓
- maps/R_PRJ002_MasterSuite_Cam01_v01_control-clay.png · _overlay.png ✓ (control
  artifacts share the render stem; D_/S_ not applicable on the hybrid path)

## Gate status
**Machine gates: PASS.** → _inbox/R_PRJ002_MasterSuite_Cam01_v01.md staged.
**AWAITING HUMAN APPROVAL PER IMAGE** (final gate — not covered by the best-case
override; 00_intake/gate-override.md scopes itself to exclude this). On approval:
write settings to clients/C-001 episode (registry v004@production + pro tier +
golden-hour slot set = the approved configuration).
