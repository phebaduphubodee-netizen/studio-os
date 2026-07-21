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
- 2026-07-15 (pair step BUILT + review-hardened): `pipeline/scripts/precut_pair.py` turns the
  labeled worksheet into the pilot: designer-labeled delivered anchors × our render lane (room
  from OUR filenames = provenance; anchor room ONLY from designer text — the two refusals hold) →
  `_private/benchmark/pilot-pairs.{md,json}` + `pilot-anchor-paths.json`. Every pair in BOTH
  orders; tripwires ride along (known-REWORK leg C must LOSE, anchor-vs-itself must TIE —
  expectations below the table, never on it); dups + photo-suspects never pair; a sheet carrying
  verdicts/notes is never overwritten, and `benchmark_precut.py` refuses to regenerate over a
  labeled worksheet (`--force-worksheet` to override). Label grammar (either surface): project-row
  `| Y | bedroom |`, or per-anchor `=> Y bedroom` / `=> N` (per-anchor wins; a bare `=> Y`
  inherits the row's room). Real-data state: WAITING — 560 pairable anchors, 0 labeled; the sheet
  ships the how-to. Honest gaps surfaced, not guessed: kitchen has no render lane yet; sitting has
  1 render; rooms with <2 anchors flagged `below_parity_minimum`.
  - A 7-lens adversarial review (privacy/refusals/parsing/determinism/data-loss/test-honesty/
    protocol) hardened it before commit. Fixes that landed: (PRIVACY) the md shows anchors by
    I-coded **ref**, never the Discord basename — uploader-controlled filenames can carry a client
    name; stdout surfaces unusable labels by ref/count only, never raw label text; anchor paths
    moved to a spoiler-free `pilot-anchor-paths.json` so resolving a path no longer walks the
    designer through the tripwire answers. (REFUSAL) the ambiguous Thai word `นั่งเล่น`/
    `ห้องนั่งเล่น` (covers both sitting AND living, and we run both lanes) is now SURFACED for
    disambiguation, never silently routed; a project-row label on the machine-made `UNCODED`
    bucket (unrelated clients) is refused → label those individually. (DATA-LOSS) both overwrite
    guards tolerate a dropped leading/trailing pipe + BOM (GFM-legal shapes that the exact
    cell-count checks were blind to, and would have erased a judged sheet / labeled worksheet);
    the benchmark guard fails **safe** (refuse) on an unreadable/locked/placeholder worksheet
    instead of treating it as empty. Tests: 37 in `test_precut_pair.py` incl. mutation probes for
    the ambiguity guard and the stdout privacy guard (the old stdout test was a tautology that
    could not fail — now it plants a client name and asserts absence).
- 2026-07-15 (BLIND re-curation BUILT + review-hardened): a census of the raw pilot found the
  forced-choice was measuring ARTEFACTS, not sellability — our renders are ~1 MP, the delivered
  anchors 4K–22 MP; one anchor was a **portrait vanity DETAIL** vignette (shot-type mismatch); one
  carried a **burned-in studio watermark + room caption** (un-blindable by pixels); and the raw
  judging HTML embedded full `file://` paths (client name + ours-vs-delivered role one hover away).
  `pipeline/scripts/pilot_blindpack.py` (+ `test_pilot_blindpack.py`, 22 tests) re-curates it:
  EXCLUDE the watermark + portrait anchors; resolution-normalise every image to ≤1280 px opaque
  JPEG copies (`imgs/imgNNN.jpg`); real mapping lives ONLY in the spoiler `pilot-blind-key.json`;
  **two-phase gate** — the finished pairs (both A/B orders) are judged & LOCKED before the phase-2
  tripwires (a **clay massing of our own bedroom** must LOSE — a FLOOR-only proxy, NOT protocol
  tripwire #1 which stays OUTSTANDING until a leg-C/sitting anchor exists; anchor-vs-itself must
  TIE) unlock. Outputs under `_private/benchmark/pilot-blind/` (gitignored, I-coded).
  - Effect on scope: **excluding the watermarked living anchor dropped living from 2 clean anchors
    to 1 (below parity_minimum=2) → BEDROOM is the only gate-eligible room type; living is
    advisory.** Real state: 14 phase-1 rows (12 bedroom meet-parity, 2 living advisory) + 4 tripwire.
  - HONEST LIMITS recorded in the key, not hidden: (1) phase-1 is NOT role-blind to an *analyst* —
    every row is one-ours-one-anchor, so co-occurrence forms a complete bipartite graph that
    separates the sets; our two MasterSuite shots are the same bedroom + a shared warm-wood look +
    a 6×-vs-4× frequency tell. Blindness here neutralises the LAZY tells (resolution / watermark /
    path / filename), not active inference. (2) If the **author judges their own renders**, phase-1
    is not blind at all — value is then artifact-neutralisation + the forced-choice format. (3)
    Display SIZE is equalised, perceived SHARPNESS is not fully (4K→1280 keeps more true detail
    than a native 1 MP render). (4) Every anchor's `delivery_signal` is still 'proposed,
    unconfirmed' — `meets_anchor_parity` means enough anchors EXIST, not confirmed DELIVERED.
  - 6-lens adversarial review (blindness/determinism/data-integrity/tripwire-honesty/protocol/
    test-honesty) → 17 findings (2 HIGH, 8 MED, 7 LOW); the honesty/disclosure/hardening findings
    landed: exclusion now FAILS LOUD on an unmatched ref (no silent no-op admitting a watermark);
    the guard gained an allowlist over the injected data + letter-bearing sub-word denylist; the md
    dropped its ref→opaque map (it de-blinded ours by elimination); the two-phase lock + clay
    phase-2 isolation are now pinned by tests. **OPEN (owner decision, not auto-fixed): WHO judges**
    — an independent designer (phase-1 blindness meaningful, modulo the bipartite residual) vs the
    owner-author (phase-1 blindness moot; the pilot then measures self-honest forced-choice).
