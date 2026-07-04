# Judge-honesty diagnostic — why the M3.2 FAIL is half measurement, half real (2026-07-04)

Companion to `judge-calibration-2026-07-04.md` and
`judge-calibration-2026-07-03-designer-notes.md`. Purpose: put on the record,
precisely, **what each failing metric does and does not prove** — because older
notes flatten the whole FAIL into "the LLM judge is too lenient," and only half
of that is what the numbers actually say.

Verified by computation 2026-07-04 (workflow survey); see memory
`judge-kappa-degenerate`.

## The headline

| metric | value | bound | what it ACTUALLY means |
|---|---|---|---|
| Cohen's κ (SHIP/REWORK) | 0.000 | ≥0.8 | **DEGENERATE — a measurement artifact, NOT a leniency reading.** κ is uninformative on this data set; it cannot pass and cannot fail meaningfully. |
| Spearman ρ (ranking) | 0.428 | ≥0.8 | **The genuine signal.** The judge's *ordering* of images only weakly agrees with the designer's. This is the real, improvable gap. |

**Both bounds are missed, so M3.2 is correctly a FAIL** (an uncalibrated judge is
a broken test, don't gate production on it). But the two misses are not the same
kind of fact, and treating κ=0 as evidence of leniency is wrong.

## Why κ = 0.000 is degenerate, not leniency

The designer labelled **all 26** golden images REWORK (scores 0.0–3.0, mean 1.75,
**zero SHIP**). So the SHIP positive class is **empty** — designer SHIP rate
`pb = 0`.

Cohen's κ = (p₀ − pₑ) / (1 − pₑ), where
- p₀ = observed agreement, pₑ = chance agreement = pₐ·pb + (1−pₐ)·(1−pb),
- pₐ = machine SHIP rate, pb = designer SHIP rate.

With **pb = 0**: pₑ = (1−pₐ), and because the designer says REWORK on every image,
machine and designer agree exactly when the machine also says REWORK, so
p₀ = (1−pₐ) as well. Therefore

> κ = ((1−pₐ) − (1−pₐ)) / (1 − (1−pₐ)) = 0 / pₐ = **0**, identically, for any
> machine pass-count ≥ 1.

(The only other branch — machine passes 0 — makes p₀ = pₑ = 1 and the code
guards the 0/0 as a meaningless 1.0.) This is exactly what
`pipeline/scripts/judge_calibrate.py` computes. **κ can NEVER meaningfully pass an
all-REWORK ground truth set** — you cannot calibrate a binary SHIP/REWORK
classifier when the ground truth has only one class. κ=0 here says "the labels
have one class," not "the judge is lenient."

## Where the leniency claim IS true (and where its evidence really comes from)

The judge *is* too lenient — but that is shown by **two other signals, not κ**:

1. **SHIP-rate gap.** The machine marked several images ≥4.0 (its SHIP band)
   while the designer would ship **0/26**. GS-11 5.0, GS-18 4.75, GS-17 4.75 all
   sit in the machine's SHIP zone; the designer REWORKs them at 2.0/1.5/2.0.
2. **Rank inversions.** The machine's top-scored images are among the designer's
   worst — a qualitative face of the same weak ρ.

So "the prior 5/5 SHIP was a lenient judge, not verified client-readiness" is a
correct statement — it just rests on the SHIP-rate divergence and the rank
inversions, **not** on κ. Keep the two apart in the record.

## ρ = 0.428 is the real, bounded gap

- ρ is rank correlation over the ordinal 0–5 scores — **no SHIP class needed**, so
  unlike κ it is directly improvable.
- Ceiling analysis (memory `judge-kappa-degenerate`): re-weighting the 8 already
  stored photoreal sub-scores tops out at **~0.63 (< 0.8)**; best single per-dim
  is `room_context` at +0.628. The model's holistic overall (0.428) is actually
  **worse** than a plain mean of its own sub-scores (0.502).
- Root cause: the designer's real penalties — fused TV, camera height
  (1.5 → 1.0–1.2 m), material real-scale (laminate 2.40×1.20 m seams, SPC plank
  scale), ensuite wet/dry — are **not rubric dimensions in `critique.py`**. No
  reweight of the existing axes reaches 0.8; closing ρ needs the rubric extended
  to those FUNCTION-layer axes and a re-score.

## What compensates while the judge stays uncalibrated

The deterministic **FUNCTION / persona layer** (`placement_logic.py`,
`ergonomics_ref.py`, `persona.py`, wired as a pre-render gate) is the standing
workaround: it enforces the human-usage rules the lenient photoreal judge is
blind to (TV placement, furniture real-scale, bathroom wet/dry, door-vs-bed-head)
without needing the judge to be right. It does not *fix* the judge — it routes
around it.

---

## OWNER QUEUE — blocked on owner decision / budget (do NOT self-approve)

1. **≥1 real designer SHIP label** — the only way to make κ non-degenerate. Blind-
   label the camera-height-fixed renders already on disk (candidate GS-27..30).
   ⚠️ note the machine currently SHIPs the **h150 / 1.5 m** render — the exact
   height the designer called too high — so an honest new label set is likely to
   *widen* the gap before it narrows.
2. **PAID rubric re-score** (~26–52 Gemini vision calls, owner budget) with the
   `critique.py` rubric **extended to the FUNCTION-layer axes** — required before
   ρ can approach 0.8. Nothing free reaches it.
3. **Governance — enshrine `labels.json` as permanent ground truth?** All-REWORK
   ⇒ κ stays degenerate until the set spans some genuinely shippable images;
   ρ + the SHIP-rate gap are already conclusive. Owner call.
4. **Governance — judge path:** (a) expand the rubric + recalibrate, and/or
   (b) keep the judge as a photoreal **pre-filter** with the designer as the real
   gate (architecture already routes RESOLVED → human `_inbox`). Owner call.
5. **Governance guardrail — do NOT silently swap the acceptance-metric aggregate**
   (holistic → sub-score mean, even though 0.502 > 0.428). That redefines a
   proven test; same governance class as `qa/thresholds.yaml` — PR + owner sign-off
   only.

## Sources
- `qa/reports/judge-calibration-2026-07-04.md` (the 26-row table, ρ/κ values).
- `qa/reports/judge-calibration-2026-07-03-designer-notes.md` (the designer rubric).
- `pipeline/scripts/judge_calibrate.py` (the κ/ρ computation).
- memory `judge-kappa-degenerate` (the 2026-07-04 computational verification).
