# Skills
Format: skills/<name>/SKILL.md with frontmatter (description, allowed-tools;
disable-model-invocation: true for sensitive ops like the future
bom-generate and client-deliver).

## THE ONE RULE THIS DIRECTORY LIVES OR DIES BY (owner order 2026-08-27)
*"มีข้อแม้ว่าทั้งหมดนี้คุณต้องเป็นคนเรียกใช้เองเมื่อต้องใช้"* — **the builder calls these
itself, at the moment the work matches, without being asked.**

Why it had to be said, in numbers: the first five skills plus `ffe-research` were written
2026-07-02, produced `concept.md`, `ffe-candidates.json` and `bom.md` within two days,
and then **never fired again — 54 days and 86 render rounds.** Nothing noticed, because
nothing could: a skill leaves no trace when it is NOT used, and the roster prints
identically either way. That is this repo's own recurring defect (a queue whose consumer
never visits it) landing on the layer that was supposed to prevent it.

So the roster now has a consumer: `pipeline/scripts/skill_usage.py` stamps every Skill
and Agent call from a hook and `plan_status` prints, at every session open, how many
calls each entry has and how long since its last one. **A skill nobody calls prints as
such until it is either called or retired.** Never used ≥14 days is a prompt to do one or
the other — not a number to look past.

## Present
- **Craft skills — the ones that exist because JUDGEMENT cannot be a guard** (2026-08-27):
  `camera-composition` (framing / what the frame must contain / DoF — the lever that
  crossed the P2 exit clause at D-152), `styling-narrative` (story → object list → counts
  → placement → pixels; serves three open owner orders), `lighting-design` (rig solved
  from the room, not tuned by eye).
- **Stage skills — the blueprint-§13 set** (2026-07-02, Phase 1): `intake-parse`
  (00_intake → brief.json + inventory.md; e2e-tested on PRJ-2026-001_test-run incl.
  prompt-injection quarantine), `concept-brief` (brief → 02_concept/concept.md,
  vault-cited), `qa-report` (scorecards × thresholds.yaml → 05_qa report + repair queue).
  These are **dormant, not dead**: they fire on stage-shaped work, and the lane has been a
  single-frame render loop since July. They come due again at the real-client run
  (ORD-2026-08-22).
- `ffe-research/` — back-office FF&E product research → `03_layout/ffe-candidates.json`
  + `scripts/ffe_schedule.py` renders the driftless `ffe-schedule.md`. Feeds Stage 03 (Layout)
  and, via the human-triggered `bom-generate`, Stage 07. Added 2026-07-02 (ahead of the blueprint
  five — it's back-office research, and the `tools/` AI layer makes it immediately useful).

## Retired
`usd-validate` and `material-lint` moved to `docs/retired-skills/` on 2026-08-27: the repo
holds zero `.usda` and zero `.mtlx` files and `pipeline/workflows/` is empty, so both
described a pipeline that never existed here. Reasoning and the route back:
`docs/retired-skills/RETIRED.md`.

## What is NOT a skill, and why the distinction is load-bearing
Pick the mechanism from the shape of the failure, not from convenience:

| the failure | the mechanism |
|---|---|
| forgot to do it | a **guard** that fails closed (e.g. `blenderkit.py` now refuses a paid fetch in a class with no free baseline) |
| must not see something | an **agent definition** with a fixed ask (`.claude/agents/cold-critic-c2.md`) |
| must happen every time, automatically | a **hook** |
| don't know how to make it good | a **skill** |
| everyone knows but nobody reads it | not a document — see all of the above |

A skill wrapping a script that already runs adds a layer and buys nothing.
