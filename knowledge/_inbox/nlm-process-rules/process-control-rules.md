---
title: "Process control for a self-blind iterative worker — stop-loss, cheap gates, independent acceptance, benchmark-anchored eval"
source: notebooklm
notebook: fd94d3c8-cc71-4bdd-abb7-98a2f39b07b1  # "DR: process control for a self-blind iterative worker" (fresh DR notebook; 73 sources ready / 2 error)
turns: 1-4 (of 4)  # snapshot: qa-history.json (sibling, per lane convention)
date: 2026-07-28
tier: REFERENCE
status: staged — distilled into knowledge/brand-standards/iteration-control-and-review-gates.md (same commit)
privacy: generic process questions only; no client identity, project number, address, or dimension left the machine
context: fired from the owner's 2026-07-28 sustainability verdict ("คนทำมองไม่เห็นว่าตัวเองกำลังทำอะไรและไม่สามารถหยุดสิ่งที่กำลังทำไปในทางที่ผิดไว้ได้") — order "ทำ DR เกี่ยวกับกฏพวกนี้"
---

# Process control for a self-blind iterative worker — the DR

**Why this DR fired.** Vault-first recon (search-our-own-vault-first law): the vault
holds the profession's *client* sign-off gates — 4 gates, "before the heavy CD hours
are invested" (`knowledge/classifications/design-process-and-deliverables.md` §4,
REFERENCE) — and the repo holds *machine* stage gates (`_contract.md`). Neither says
anything about: stop-loss / iteration caps, cheap-first preview ladders, independent
acceptance when the BUILDER is the unreliable component, benchmark-anchored judgment
vs self-diff, or HITL oversight of autonomous agents. That whole band was a genuine
gap → NLM DR on a fresh notebook (contamination boundary), 4 asks of the ≤10 budget.

**[n]-marker posture** (same recorded posture as
`knowledge/_inbox/interior-render-critique-DR-2026-07-15.md`): per-[n] source-title
resolution is NOT exportable via the CLI (`qa_pairs` schema carries no marker→source
map). Citations below read "turn N"; notebook fd94d3c8 is the retained audit trail —
do NOT prune it. The full 75-source roster is in §Sources below; full verbatim
answers in the sibling `qa-history.json`.

---

## Turn 1 — the five bodies of practice (the main ask)

Framing the sources converge on: mature disciplines do not try to eliminate
fallibility — they build **systems of constraint** that isolate, detect, and
remediate errors at the earliest possible stage.

### 1. Film / VFX / animation
- **Playblast rule:** artists are prohibited from submitting to the render farm
  without first producing a playblast (rapid low-fidelity preview) and securing
  lead sign-off. Mechanism: full renders cost wall-clock hours; a playblast
  verifies timing/weight/plausibility in real time on a local GPU.
- **Sequential approval lock:** previz → layout → animation → sim → lighting →
  comp; once a supervisor signs a stage it is FROZEN — downstream may not modify
  upstream assumptions. Expensive passes run only on geometry guaranteed stable.
- **Dailies 15-second rule:** in dailies the artist gets ~15 seconds: what
  changed, why, what feedback is requested; a non-dispute etiquette rule bans
  arguing with feedback in the room.
- Failure modes: **the junior trap** (micro-iterations — a 2% light tweak —
  clogging review queues and render cycles) and **upstream asset drift** (unlocked
  stages let late timing changes invalidate all downstream caches).

### 2. Manufacturing (Toyota) / SPC
- **Andon cord:** every operator is empowered AND required to stop the whole line
  on any abnormality (jidoka). Stopping immediately preserves machine state for
  root-cause analysis; fixing at the station is orders of magnitude cheaper than
  post-assembly.
- **Poka-yoke:** mistake-proofing that makes the error physically impossible, not
  policed after the fact.
- **SPC stopping rules** (Western Electric / Nelson): plot the measurement; a
  single point beyond 3σ, or nine consecutive points on one side of the
  centerline, = special-cause variation → stop.
- Failure modes: **Andon suppression** (throughput-obsessed culture punishes line
  stops → workers hide defects and pass them downstream) and the **joint
  false-alarm cascade** (running all eight Nelson rules at once inflates false
  alarms to ~1 in 91 observations → alert fatigue → operators override the logic).

### 3. Software / systems engineering
- **Timeboxing + WIP limits; Definition of Done** as a non-negotiable checklist.
- **Independent V&V / acceptance:** the testing organization keeps technical,
  managerial, and financial independence from the developers; acceptance testing
  is performed by stakeholders, never the builders. The load-bearing number:
  builders catch only **30% to 50%** of their own defects; independent testers
  catch 70-90%. Mechanism: "familiarity blindness" — builders test the happy
  paths they assumed while designing.
- Failure modes: **gates without teeth** (nobody makes the Kill decision; weak
  work survives on momentum) and **DoD decay** (deadline pressure converts
  skipped checks into hidden compounding debt).

### 4. HITL oversight of autonomous AI agents
- **Risk-tiered checkpoint gating:** read-only / reversible actions run
  autonomously; irreversible actions (deploy, spend, delete) get a hard,
  non-bypassable human gate.
- **Hard stop-loss budgets:** caps on tool cycles / tokens / spend per task;
  breach = automatic halt + rollback + escalate.
- **Multi-signal escalation:** never trust the agent's self-reported confidence
  alone (notoriously miscalibrated — highest confidence on hallucinated output);
  combine structural loop detection + deterministic validators + user-sentiment.
- **Design for doubt:** vary how recommendations are presented (no uniform
  Approve button); schedule unassisted manual audits to keep the human sharp.
- Failure modes: **automation complacency** (a 95%-accurate agent turns its
  reviewer into a rubber stamp) and **approval-queue bloat / context collapse**
  (over-gating low-risk actions → 14,000-item queues; a reviewer without the
  reasoning path is an uninformed roadblock).

### 5. Evaluation discipline
- **Guarded golden set:** evaluate against a curated out-of-distribution set
  (50-100 real scenarios) isolated from anything the worker optimized on.
- **Calibrated judging:** position-bias swap tests; length-controlled scoring.
- **Multi-metric regularization:** score quality AGAINST cost (tokens, latency,
  calls) so a single metric cannot be gamed.
- Failure modes: **Goodhart's law** (optimize one unconstrained metric → the
  agent deletes the codebase to "reduce bugs") and **self-preference bias** (a
  judge rewards text it generated itself for its lower perplexity — the formal
  version of "judging my render against my previous render").

## Turn 2 (iterate) — how the human side stays sharp

Centaur pairing: machine handles volume/speed, human keeps contextual judgment +
accountability. Load-bearing bits for us: **confidence-based routing** (routine
work flows; ambiguous/irreversible work escalates), and the **decision-ready
context package** — an escalation hands over a clean before/after diff, the
reasoning, and estimated impact, never a raw log. "Design for doubt": intentional
friction at the gate (make the reviewer verify one named detail before Approve).

## Turn 3 (iterate) — when to KILL work (R&D termination)

Kill criteria differ by risk class (derivative work → financial/customer tests;
breakthrough work → strategic fit / new-capability tests). Stage-Gate Go/Kill
scorecards: strategic fit, market, differentiation, feasibility, reward-vs-risk.
**Red-flag early-warning signals:** no champion, low worker commitment, and —
directly relevant here — **frequent revisions to cost schedules and deviations in
timelines** are themselves termination signals, not noise.

## Turn 4 — concrete stop-loss parameters and the escalation package

- "Max iterations" alone is insufficient — agents can burn "$100 in 10 minutes"
  in a loop. Practice = layered caps: tool-execution cycles + token consumption +
  spend per task; breach → halt, rollback, escalate.
- **Financial tier gate** example: auto-approve under a threshold (e.g. $100),
  synchronous human gate above it. **TTL:** a pending approval expires (e.g.
  30 min) into a kill-switch — the agent never silently stalls or silently
  proceeds. (Vendor-practice example numbers — REFERENCE, never a gate value.)
- **Structural loop detection:** track repetitive identical tool calls and
  identical error-recovery loops (e.g. wrapping the same failure in try/except
  again instead of fixing the cause). Composite scoring may weight the LLM's raw
  self-confidence as low as 15%, filling the rest with semantic similarity to
  known-good examples + deterministic validators.
- **Escalation package:** condensed to **1,000 to 2,000 tokens**; clean visual
  diff of before/after; plain-language proposed action; reasoning; estimated
  impact; reversibility flag; audit id; "reject with edits" option (never binary).
- **Agent-written code review:** the human reviewer is approving a reasoning path
  they did not travel — otherwise the last human in the loop is a "**bottleneck
  pretending to be a checkpoint**". The package must add: falsifiable claims tied
  to specific diff hunks + passing tests, the **rejected alternatives** and why,
  and explicit non-goals (what was deliberately not handled).

## What the DR did NOT supply (recorded honestly)

- No universal N for "max consecutive failed attempts on one subtask" — the
  sources give budget-style layered caps and loop-detection *signals*, not a
  magic count. Any specific N (e.g. our 2-strike rule) is a STUDIO CHOICE inside
  the pattern, not a cited value.
- Nothing here is statutory; every number ($100, 30 min, 15 s, 3σ, 1/91,
  30-50%, 1,000-2,000 tokens) is practice-report tier. codes-th unaffected.

## Sources (75: 73 ready, 2 error) — roster snapshot 2026-07-28

Toyota Production System (Toyota official; Umbrex; SixSigma.us; Symestic jidoka),
Andon/psychological safety, Western Electric rules (Wikipedia; PPAP; MetricGate;
Six Sigma decision rules), SPC control limits (Symestic; iFactory AI aerospace),
VFX dailies unwritten rules (CG Lounge), Playblast (Foundry Learn), VFX pipeline
file management (Fastio), ABC of VFX, Houdini-vs-Maya sim workflows (Artivoxa),
MovieLabs "Scaling for the Super Bowl", Harvard 3D animation (Wiser), Fox Render
Farm, special-effects-animator SKILL.md (GitHub), Stage-Gate (Planisware;
Monday.com; Umbrex; Shiny NPD gate guide; Stage-Gate overview; Gupea
Agile+Stage-Gate), R&D termination (picmet "How Different R&D Project Types are
Terminated"), GAO-11-581 independent acquisition reviews, NIST high-integrity
software assurance framework + NIST 2022 report, NASA SOMA software assurance,
software V&V (Wikipedia; GovInfo), independent testing / acceptance testing
(Virtuoso QA ×2; GeeksforGeeks; Appsierra; Bug0), Definition of Done (Teaching
Agile; LogRocket; Iterators; Google published patterns; Scrum-master undone-work),
technical debt (Boldare; Catio; SIG; Agility at Scale), Agile glossary, HITL for
AI agents (DEV Community; Elementum; BotsCrew; Birdeye; Ampcus Cyber; Digital
Applied escalation design; 2026 guide; hands-on playbook; MDPI systematic review;
"Why Full Autonomy Is the Wrong Goal"), Tuck School "Even With Humans in the Loop,
Agentic AI Systems Struggle", UXmatters "Designing for Doubt", SERVSIG AI
complacency, clinical HITL (radiology co-pilot), "The last human in the
coding-agent loop is a bottleneck pretending to be a checkpoint", Goodhart's law
(Wikipedia; "when your AI finds the loophole"; MindStudio benchmark gaming),
AI model evaluation guide, arXiv "Towards More Standardized AI Evaluation",
Gremlin two-kinds-of-failure-testing, plus the DR's own synthesis document
("Systems of Constraint", ×2). Errored (never imported, never cited): 2 Medium
posts (DoD across ceremonies; benchmark contamination).
