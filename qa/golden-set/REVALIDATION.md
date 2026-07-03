# Judge re-validation procedure (M3.2, blueprint §9.4)

An uncalibrated judge is a BROKEN TEST, not a lenient one.

## Triggers — re-run calibration whenever ANY of these changes
1. Judge model version changes (critique.py `MODELS` map — e.g. gemini-2.5-flash
   → any newer flash/pro). Model updates silently shift score distributions.
2. The rubric in critique.py changes (dimension list, wording, or the
   "be stingy" framing).
3. The pass bound in qa/thresholds.yaml `client_qa.judge_score` changes (PR lane).
4. Every 90 days even with no known change (silent server-side model drift).

## Procedure
1. (Optional, recommended when rolls are thin) add fresh rolls on golden-set
   images: `python pipeline/scripts/critique.py assets/qa/golden-set/GS-XX.png
   --kind render --out <somewhere>` and merge into machine-scores.json — means
   over rolls are the machine score (judge variance ±0.5: singles never decide).
2. `python pipeline/scripts/judge_calibrate.py` → qa/reports/judge-calibration-<date>.md
3. PASS (ρ ≥ 0.8 AND κ ≥ 0.8): record the report path in docs/strategy.md; the
   judge may gate.
4. FAIL: the judge gates NOTHING until fixed. Fix order: (a) multi-roll count ↑,
   (b) rubric wording, (c) model pin/downgrade. Then GOTO 1. Never "fix" by
   moving the pass bound to meet the judge — thresholds move only by PR with
   design rationale.

## Growing the set
New scored renders append via `python pipeline/scripts/golden_set_curate.py`
(existing GS-IDs are stable; new images get new IDs). Owner labels the new IDs
blind (LABELING.md) before the next calibration counts them.

## Labeled-set integrity
labels.json is ground truth — append-only per image; changing an old label
requires a dated note in the file (`"relabel_note"`) saying why taste changed.
