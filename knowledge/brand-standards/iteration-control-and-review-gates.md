# Iteration control & review gates — studio standing rules / กฎคุมรอบงานและด่านตรวจ

> PROVENANCE: distilled 2026-07-28 from
> `knowledge/_inbox/nlm-process-rules/process-control-rules.md` (NotebookLM DR,
> notebook fd94d3c8-cc71-4bdd-abb7-98a2f39b07b1, turns 1-4, 73 sources ready;
> full transcript in the sibling `qa-history.json`). Tier **REFERENCE** — these
> are practice-report groundings, not statutory values; no number below may gate
> a deliverable by itself. Fired from the owner's 2026-07-28 sustainability
> verdict: the worker (the agent) cannot see what it is doing and cannot stop a
> wrong direction — so the process must be designed AROUND that blindness, the
> way engineering designs around any unreliable component.
>
> STATUS: rules PROPOSED, grounded, awaiting the owner's adoption call before any
> hook/config wiring. Nothing here is enforced yet.

The DR's one-line synthesis: mature disciplines do not try to make the worker
infallible — they build **systems of constraint** that catch errors at the
earliest, cheapest stage. Every rule below names the practice it copies, the
mechanism, and the failure mode that practice itself warns about.

## R1 — Stop-loss: บังคับหยุดหลัง 2 รอบพังบน mechanism เดียว

**Rule.** Per task: at most **2 full build+render cycles** on one mechanism
without an owner-visible pass. The 2nd failure forces STOP → escalate with a
gate artifact (R2). Repeating the same fix-shape twice (retuning the same number,
re-wrapping the same failure) is itself a halt signal even inside one cycle.

**Grounding.** Toyota jidoka / **Andon** cord: any operator stops the whole line
on abnormality, because fixing at the station is orders of magnitude cheaper
than downstream. HITL practice: layered hard caps (tool cycles, tokens, spend) —
breach = halt + escalate, never push through. Structural loop detection flags
"identical error-recovery loops" (patching the same failure again instead of
changing mechanism). R&D termination research: frequent revisions and timeline
deviations are themselves kill signals, not noise. The DR gives no universal N —
**N=2 is a studio choice** inside the layered-caps pattern (this room's evidence:
the round-3 cloth saga needed 3 full-price failures before the mechanism change;
this rule would have cut failure #3).

**Failure mode to watch (from the sources).** **Andon suppression**: if stopping
is punished or feels expensive, the worker hides defects and passes them
downstream. Pulling the cord must always read as the CORRECT move, never as an
admission to be avoided.

## R2 — ด่านตรวจ = context package มาตรฐาน ราคา 30 วินาทีของ owner

**Rule.** Every stop (scheduled gate or R1 stop-loss) hands the owner ONE
standardized artifact: **before/after image pair (clean visual diff) + ≤3 lines**
— (1) what changed, (2) my own judgment, (3) what I am unsure of — plus, when a
direction was chosen, the **rejected alternatives** and why, and explicit
non-goals (what this pass deliberately did not touch). No raw logs, no walls of
prose. Work on that lane BLOCKS until the verdict — an unanswered gate is never
silently passed.

**Grounding.** VFX dailies: the artist gets ~15 seconds — what changed, why,
what feedback is requested. HITL escalation design: a decision-ready package
condensed to **1,000 to 2,000 tokens** with plain-language action, reasoning,
impact, reversibility flag, and a reject-with-edits option; anything less
context-rich turns the reviewer into an uninformed roadblock ("context
collapse"). Agent-written-work review: without falsifiable claims tied to the
actual diff, the last human in the loop is a
"**bottleneck pretending to be a checkpoint**".

**Failure mode to watch.** **The junior trap / approval-queue bloat**:
micro-iteration gates (a 2% tweak per ask) clog the owner's queue and train him
to skim. Batch meaningful deltas; gate on decisions, not keystrokes.

## R3 — "เสร็จ" เป็นคำตัดสินของ owner เท่านั้น

**Rule.** The builder never declares done. Reports end "พร้อมให้ตัดสิน" (ready
for verdict), listing what is NOT yet verified. A round closes only on the
owner's verdict against the R2 artifact.

**Grounding.** Independent V&V: the acceptance tester keeps technical and
managerial independence from the builder; acceptance testing is performed by
stakeholders, never the builders. The load-bearing number: builders catch only
**30% to 50%** of their own defects (independent testers: 70-90%) — mechanism is
"familiarity blindness", the builder tests the happy paths they assumed while
designing. This session's evidence matches: two consecutive "closed" declarations
were each followed by the owner finding defects in frames already looked at.

**Failure mode to watch.** **Gates without teeth**: if no Kill/redirect verdict
is ever issued, weak work survives on momentum. The gate must be allowed to say
no.

## R4 — LOOK เทียบ benchmark ไม่ใช่เทียบงานตัวเอง

**Rule.** Every LOOK judgment places the crop NEXT TO the corresponding crop
from delivered, sold work (the friend's corpus — 704 render anchors already cut,
LOCAL-ONLY per its privacy law). The question is "does this survive next to a
sold render?", never "is this better than my previous attempt?". Where a numeric
proxy exists (a score, a mask count), the picture outranks the number.

**Grounding.** Guarded golden set: evaluate against a curated external set the
worker never optimized on; judging your own output against your own prior output
is the documented **self-preference bias** (a judge rewards text it generated
itself). **Goodhart's law**: any single unconstrained metric gets gamed — the
DR's example agent "reduces bugs" by deleting the codebase; ours pass bbox/hem
guards with a contained cloth explosion.

**Failure mode to watch.** Benchmark leakage: if the anchor crops start steering
the build directly (copying instead of judging), the golden set stops measuring
generalization. Anchors judge; they do not dictate.

## R5 — บันไดความคมราคาถูกก่อนเสมอ (playblast rule)

**Rule.** No full-frame render may be the FIRST look at a change. Ladder:
changed-object quick-look (cropped camera, low samples, seconds) → single-frame
check → full pair only when the quick-look passes. Signed stages stay frozen
(existing signed-design law): a pass that would move a signed decision upstream
must stop and gate first (R2), not smuggle.

**Grounding.** The VFX **playblast** rule: nothing reaches the render farm
without a cheap preview plus lead sign-off — full renders cost wall-clock hours,
a playblast verifies plausibility in real time. Sequential approval lock:
expensive passes run only on geometry guaranteed stable; unlocked upstream edits
invalidate every downstream cache. This room's evidence: three failed cloth
bakes each paid full build+render (~5 min) for information a 20-second
single-object preview carried.

**Failure mode to watch.** Preview-only convergence: a change judged ONLY at low
fidelity can lie (this build's own amplitude-bisect law — honest bump amplitude
rendered as nothing). The ladder ends at full fidelity before a gate closes; the
cheap rungs exist to kill bad work early, not to certify good work.

## R6 — งบเป็น metric ที่สอง เสมอ

**Rule.** Every lane reports quality AND spend (cycles, renders, tokens). Fleets
(multi-agent review) fire pre-commit or on explicit order only; default is solo.
Guard sets stay SMALL and loud — a new guard must name the defect class it
catches that existing guards cannot, or it is not added.

**Grounding.** Multi-metric outcome regularization: score task quality against
token/latency/call cost so no single axis can be maximized blindly; agents in a
loop can burn "$100 in 10 minutes". SPC's **joint false-alarm cascade**: running
all eight Nelson rules at once inflates false alarms to ~1 in 91 → alert fatigue
→ humans override the whole system. Composite escalation scoring weights the
agent's raw self-confidence as low as 15% — the system is DESIGNED assuming the
worker's self-assessment is the least reliable signal available.

**Failure mode to watch.** **Automation complacency** on the cheap side: if the
budget metric always reads fine, it stops being read. Spend gets reported at
every gate, not only when it hurts.

## How these sit with existing law

- R1/R2 extend the LOOK permanent rule (ดูไปทำไปเหมือน designer จริงๆ) with a
  hard budget and a standard hand-off artifact; LOOK stays the in-loop eye,
  R1/R2 bound what a wrong eye can cost.
- R3 formalizes what the owner's verdict rounds already are in practice.
- R4 operationalizes the standing sellability law (แพ้งานส่งจริง = ขายไม่ได้)
  into the per-crop judgment loop.
- R5 generalizes the existing "camera must SEE the decision" + signed-design
  freeze into a cost ladder.
- Client-gate vocabulary (the profession's 4 sign-off gates,
  `knowledge/classifications/design-process-and-deliverables.md` §4) is the
  CLIENT-facing analogue; these rules are the BUILD-side counterpart.

## Cross-refs

- `knowledge/_inbox/nlm-process-rules/process-control-rules.md` — staged source
  (notebook fd94d3c8, turns 1-4; full answers in sibling qa-history.json).
- `knowledge/classifications/design-process-and-deliverables.md` §4 — client
  sign-off gates (the human-process analogue that already existed in the vault).
- `knowledge/classifications/qa-dimensions.md` — render-critique protocol the R4
  benchmark judgment feeds.
- `docs/strategy.md` — why-decision record; adoption entry to be appended when
  the owner rules on wiring.
