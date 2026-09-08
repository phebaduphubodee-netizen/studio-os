# Style panel — the ONE written question, fixed before any candidate is seen

This file is part of the D-119 criteria freeze (its bytes are hashed together with
D-119's `in_effect` and `qa/blenderkit-month-classes.json` at the first paid download;
`blenderkit.py status` prints MATCH / CHANGED). It exists because the p2r57 gate records
the style panel as "3 agents (~203k tokens)" with no prompt on disk — a judgment whose
question is written after the candidates are seen is the builder's taste wearing a panel.

## Protocol (same shape as the R4B sighted-reader panel, 2026-08-17)
- THREE fresh-context agents, spawned with ONLY this file, the unlabeled anchor crops,
  and the candidate thumbnails. No build history, no round number, no other judge's
  answer, no "which one is ours/paid/free".
- ANCHORS: 4-6 bedroom crops from the delivered-work pool (`_private/`, R4: reference of
  record) that the builder tags Japandi/contemporary-minimal BEFORE the run. They JUDGE,
  never DICTATE (no copying — R4b).
- CANDIDATES: thumbnails only, filenames replaced by letters, free and paid shuffled
  together. The judge never learns the tier.
- Each judge answers the one question below per candidate, in JSON matching
  `verdict.schema.json`. A candidate PASSES the panel when >= 2 of 3 answer `inside`.

## The question (verbatim, do not edit after the freeze)
> Beside these anchor crops of finished bedrooms, would this object sit in the same room
> without reading as a style clash — `inside` the envelope, `edge` (defensible but a
> different register), or `outside` (carved/ornate/period/novelty/child/office)?
> Give one sentence of reason naming the feature that decided it (profile, ornament,
> material, proportion), never a preference.

## What the judge must NOT be asked
- whether it is "better", "nicer", "more expensive-looking" (preference, not envelope)
- whether it matches a drawing or a spec dimension (that is dim_check's question)
- anything that reveals free vs paid
