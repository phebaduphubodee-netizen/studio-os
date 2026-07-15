# Sellability benchmark — the delivered-work bar

**The owner's law (2026-07-15): if a render cannot stand next to the studio's own DELIVERED,
PAID work, it is not sellable.** Beauty-parity with delivered work is a NECESSARY condition,
never a sufficient one — the corpus itself proves the second half: a paying client issued a
revision list on a render that had already been DELIVERED (beauty passed; function did not —
that list is where the three furnishing-completeness WARN rules came from).

## Why a PAIRWISE bar, not a score threshold

Measured, not assumed: M3.2 ran a rubric judge over 26 renders the designer graded 26/26
REWORK — the judge was lenient on every one (rank correlation ρ=0.428 against the designer,
ceiling ~0.63; κ literally 0.000 because the corpus contained ZERO ship-grade anchors).
An absolute "score ≥ X" bar inherits that leniency. A forced-choice — *this render vs a
delivered render of the same room type* — asks the judge a question it is far harder to
flatter, and the delivered pool finally supplies the SHIP-grade anchors the κ measurement
never had.

## The gate (three ANDed conditions to sell)

1. **Beauty parity** — pairwise forced-choice vs ≥2 delivered anchors of the same room type.
   LOSE against the anchor ⇒ FAIL (ไม่ขาย). Judged in BOTH A/B orders; an order-dependent
   verdict is a judge defect, not a result.
2. **Function** — placement_logic / furnishing-completeness gates (already wired pre-render).
3. **Sourceability** — the render visualizes a buyable spec (owner north-star; gate exists,
   ffe_tag population pending).

## Anchor pool + curation states

Candidates live in `_private/benchmark/candidates.json` (gitignored — client work): 1,144
render-sized images across ~30 real projects, machine-scanned 2026-07-15. States:

- `candidate` — in the manifest, no delivery evidence attached. **All 1,144 are here.**
- `delivered-final` — promoted only with EVIDENCE (posted in a delivery/revision thread,
  4K/render dimensions, not a phone photo — 4000×3000-class images are site photos), deduped.
- `paired` — matched to one of our render lanes by room type; only these gate anything.

A benchmark curated from drafts is a bar set low — curation is part of the instrument.

## Anti-flattering tripwires (run BEFORE trusting any verdict)

- **A known-REWORK render must LOSE**: the 3-leg experiment's C leg (1.5) vs any anchor.
  If it wins, the harness is broken — that is the tripwire firing, not good news.
- **Anchor vs itself must tie** (or split 50/50 across repeats).
- **Order swap must not flip verdicts** (position bias).
- Expected first honest result: our current best legs LOSE most pairs. 26/26 REWORK says the
  bar is above us today; a first run that says otherwise indicts the judge, not the work.

## Privacy — LOCAL-ONLY is a standing OWNER DECISION, not a default awaiting sign-off

The owner ruled on 2026-07-12: this pool is usable as an eval set **on this machine only** —
no external API of any kind (no cloud judge, no NLM, no web search), never committed, clients
referred to by project code (I-24-XXX) only, never a personal name — not even inside a quoted
filename. Pairwise A/B against an anchor inherently puts the anchor image in the prompt, so a
**Gemini-judged beauty-parity gate is OFF THE TABLE under the standing decision**. The judge
for this benchmark is therefore the DESIGNER (human grading) — which is not a workaround, it
is the original point: designer-graded ground truth is the calibration the lenient LLM judge
lacked. If the owner ever revises the egress decision, the tripwires below still apply to any
machine judge before its verdicts count.

## Status

- 2026-07-15: manifest built (1,144 candidates); protocol written; **UNWIRED — gates nothing
  yet** (wired-gates-never-silent-pass law: this doc existing is not the gate existing).
- 2026-07-15 (pre-cut LANDED): `pipeline/scripts/benchmark_precut.py` triages the 1,144 into the
  smallest clean pool of residential render-anchors a designer must bucket — and refuses the two
  calls a machine cannot make honestly. Outputs `_private/benchmark/{precut.json,precut-worksheet.md}`
  (gitignored, I-CODED). Real-data result: **704 distinct residential render-anchors** across ~25
  I-coded projects (pool 815 pre-dedup; excluded 164 site-photos + 158 commercial + 7 too-small;
  111 advisory dup-merges; accounting 815+7+164+158=1144, nothing silently dropped).
  - The site-photo cut is ASPECT-aware (4:3 ∧ ≥3000px ∧ no render-engine name), NOT max-dimension:
    a naive `max≥3000` filter would have dropped 429 real renders (181 are 16:9, 170 named
    `Enscape_*`). It drops only the 164 true 4:3 phone/site photos.
  - What the machine REFUSES (designer-only, blank worksheet columns): **room_type** (needs pixels
    → banned from any LLM by the LOCAL-ONLY law) and **is_delivered** (thread-context evidence).
    A pre-cut that guessed either would be the flattering-scorer wearing a triage vest.
  - Hardened by a 32-agent adversarial review (7 lenses × refute-verify): 25 findings → 7 survived,
    all low. Fixes applied: per-item exclusion + photo-suspect audit serialized (so the "never
    silently gone" promise is literal, not aggregate); the one un-I-coded egress field scrubbed;
    dedup dup_of chains flattened; D5-Render token corrected; commercial keyword list deduped.
- Next (needs the DESIGNER, not the machine): from the worksheet, confirm `is_delivered` + assign
  `room_type` for the richest projects until **2-3 room types each have ≥2 delivered anchors** →
  designer-grade a 10-pair pilot (tripwires above run first) → only then wire beauty-parity as
  advisory REVIEW, promote to FAIL after κ re-measurement (this time with real SHIP anchors).
