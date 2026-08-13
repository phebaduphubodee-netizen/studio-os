# DR (NLM ask): bed-cloth state — batting loft, tucked-fold irregularity, stack-on-cushion dent

- **Tier:** REFERENCE (research answer, not domain truth). Nothing here gates a
  deliverable until distilled into `knowledge/`.
- **Provenance:** NotebookLM notebook `ae3dd665` (blender-cloth-corner-drape
  corpus), asked 2026-08-13 on the queued question from `nlm-queue.md` (first
  attempt 2026-08-12 stranded with an empty answer — retried on the autonomous
  tick and answered in full; raw turn in
  `knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json`, refreshed this
  commit). Question generic — no client data.
- **What it arms:** the owner's verdict #2 from the p2r26 image ("สภาพผ้าต่าง ๆ
  บนเตียงยังดูแปลก") + C2-r27#1's three named sites (no batting loft · sheet
  fold ruler-straight across the bed · corner balloon/overflow) + the BENCH
  folded-stack site that has waited for a new mechanism since r23 (R1 forbids
  re-turning crease_wander).

## Ranked levers for our sites

1. **BENCH STACK DENT (the waiting mechanism):** convert the bench cushion to a
   deformable target with **Soft Body** — goal stiffness ~0.5 via a painted
   vertex group (core holds, surface yields), edges pull/push ~0.8 — so the
   folded stack DENTS the cushion instead of sitting on rigid plastic. This is
   the physics C2 filed four rounds running ("ผ้าพับวางบนเบาะนุ่มต้องยุบ") and
   the first mechanism for it that is not a knob re-turn.
2. **BATTING LOFT (duvet/coverlet all-over undulation):** the full frame is
   sim-coarse-render-fine (SurfaceDeform + post-sim Solidify ~10 mm) — heavier
   pipeline change; the REACHABLE half first: **procedural quilting/loft via
   displacement driven by a distance-function thickness** on the render mesh
   (no re-sim). Displacement on a subdivided cage is already R8b-lawful.
3. **TUCKED-SHEET FOLD IRREGULARITY:** three techniques — (a) asymmetric
   initial state (rotate the sheet before the drape; the 45-70° figure smells
   like a loose-drape number, verify before using on a MADE bed), (b) **Hook
   modifiers on hem vertex groups parented to animated empties** = the hand
   that tucks, localized asymmetric folds, (c) **gravity ramp** keyframed
   0.0→1.0 over ~40 of 120-150 frames so tucks slide and settle instead of
   bouncing rigid.
4. **Empirical chaos bands (for tests):** real re-draped fabric varies **±15%
   drape coefficient, ±25% fold/node dimensions, ±3 fold count** between
   identical trials — a believability band a symmetry test can be written
   against (same family as the aperiodicity test that closed the sine-hem).

## Caveats

- The corpus has NO physical constants for fold crease radius or stack-edge
  bulge (said explicitly) — the folded-stack GEOMETRY question stays partly
  open; the dent mechanism above does not depend on it.
- All numeric bands are model-cited REFERENCE values pending original-source
  verification at distillation ([n] markers unresolved from the CLI — same
  caveat class as DRW-4).
- Soft Body on the cushion + hooks/empties must be checked against the
  headless data-API law (no geometry bpy.ops) before build — modifiers and
  keyframes are data-API, but verify the effector-weight keyframe path.
