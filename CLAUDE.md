# STUDIO-OS — Root Instructions

AI interior design studio monorepo (Thai residential: condos, houses, townhomes).
Claude Code is the orchestrator; the filesystem is the state machine; deterministic
hooks are law. Full architecture: STUDIO-OS Implementation Blueprint v1.0 (docs/).

## OPEN EVERY SESSION WITH THIS — owner order 2026-08-09
```
python pipeline/scripts/plan_status.py
```
Prints WHERE WE ARE in `qa/deliverable-plan.json` (the plan of record for reaching
client-deliverable work), the next named work items with their files, what is
waiting on the owner, and whether a REVIEW is overdue. **Report it to him at the
top of the session, before anything else.**
- **AFTER EVERY COMMIT THAT CLOSES WORK, review the plan and propose changes to it:**
  `plan_status.py --review --verdicts '{"P1":"keep: …","P2":"change: …"}'`. It
  REFUSES unless every remaining phase carries **keep / change / drop plus a
  reason** — a review that changes nothing must say so in those words. **The plan
  is allowed to be wrong; dropping a phase for a recorded reason is a correct
  outcome, not a failure.**
- Why it is a program and not a document: on 2026-08-09 this repo measured the same
  defect three times — **357 critic items filed / ~22 built · ~61 DR units / 39
  write-only · 21 gate artifacts / 2 with an owner verdict.** Every one is a queue
  whose consumer never visits it. A plan carried as prose would have been the
  fourth instance.

## Repository topology
- `knowledge/`  — domain truth: Thai codes (`codes-th/`), ergonomics, materials,
  lighting, styles, classifications, brand-standards. Read + cite file paths.
  Never write here except through the `_inbox/` ingestion flow.
- `clients/`    — client profiles + episodes. PRIVACY-SENSITIVE
  (see `.claude/rules/client-privacy.md`).
- `projects/`   — one dir per project: `PRJ-YYYY-NNN_slug/00_intake … 08_handover`.
  Every stage has `_contract.md` (inputs / process / outputs / gate). A stage is
  DONE only when its outputs exist and its gate passes. Read the contract first.
- `assets/`     — heavy binaries on Git LFS. Do not recursively read or grep here.
- `pipeline/`   — ComfyUI workflow JSON, prompt registry, validator + dispatch scripts.
- `qa/`         — `thresholds.yaml` (change via PR only), `golden-set/`, `reports/`.
- `docs/`       — `reference-map.md` (auto-generated, never hand-edit),
  `strategy.md` (human-curated why-decisions; append learnings after major tasks).
- `templates/`, `examples/` — scaffolds and gold-standard few-shot artifacts.

## Hard boundaries (enforced by hooks — do not attempt, propose via PR instead)
- Never modify: `qa/thresholds.yaml`, `knowledge/codes-th/**`,
  `.claude/settings.json`, `.gitattributes`.
- Never run destructive shell: `rm -rf`, force-push, `chmod 777`, `curl | sh`,
  hard reset to remote.
- Client data stays local: no client names, addresses, or floor plans in web
  searches or external tool calls.
- Generation/render tasks never write into `knowledge/` or `clients/`.

## Conventions
- Metric-first (mm / m / m²). Source-of-truth order: `knowledge/codes-th/` >
  client contract > studio standards > general references. Cite the winning source.
- Naming: `Prefix_Base_Variant_Suffix` — `SM_` static mesh, `M_` material,
  `T_` texture, `HDRI_`, renders `R_PRJ###_Room_CamNN_vNN`, depth/seg maps `D_`/`S_`.
  Rename only via scripts, never raw moves.
- Stage outputs are files in the stage directory; nothing important lives only
  in conversation.
- Be terse. Summaries over dumps. Delegate heavy reads (catalogs, long PDFs)
  to subagents that return short structured summaries.
- Use `/clear` between unrelated tasks; `/compact <focus>` when a thread wanders.

## Iteration control — ADOPTED 2026-07-28 (owner order; full text + grounding:
## knowledge/brand-standards/iteration-control-and-review-gates.md)
- R1 STOP-LOSS: max 2 full build+render cycles per mechanism without a pass →
  forced stop + gate. Repeating the same fix-shape twice = halt signal.
  Stopping is always the CORRECT move (Andon law), never an admission.
- R2 GATE: every stop writes `templates/gate-artifact.md` (image pair + 3 lines
  + spend) as the ROUND'S RECORD. Gate on decisions, not keystrokes (no
  micro-iteration spam). **"The lane BLOCKS on an unanswered gate" is REVOKED**
  — see R3.
- R3 DONE — **THE OWNER IS OUT OF THE GATE, owner order 2026-08-08:** *"เอาผม
  ออกจาก gate เลย ไม่ต้องรอผม สุดท้ายทุกขั้นตอนที่ render ออกมาผมก็นั่งดูทุกรูป
  ตลอดอยู่แล้ว"*. **The builder closes rounds. Nothing waits for his signature,
  ever.** He overrules from the image, at any time, and an overruled decision is
  then locked to him.
  - **WHY, and it is not impatience.** The count that preceded the order: 21
    gate artifacts across two lanes, **2** with a recorded owner verdict, **19**
    without — and not one of the 19 ever stopped the lane, against R2's own
    words. The first reading was that the closing phrase `พร้อมให้ตัดสิน` sat
    where a question belongs, so the ask felt already made (retired for that
    reason, and the phrase stays retired). **His sentence supplied the
    load-bearing half: he reads RENDERS, not documents.** The nineteen were
    nineteen asks filed in a channel he does not use. Enforcing that channel —
    which is what the builder built an hour earlier — would have halted the lane
    over messages he was never going to see. **A queue whose consumer never
    visits it does not become correct by acquiring an enforcement clause.**
  - **WHAT REPLACES THE RUNG:** `qa/open-decisions.json` +
    `pipeline/scripts/decisions_check.py`, called from `rule_gate.check()`. It
    blocks on NOTHING the owner owes. It fails the render when the BUILDER's
    side slips: a row with no decider (`pending` is refused by name), a `where`
    naming a path that does not exist (**a decision in force nowhere was never
    taken** — R10's test applied to decisions), a missing `reverse_by`, or an
    `owner_override` relabelled as the builder's call. Every gate run PRINTS
    the log, one line per decision naming its reversal, **into the render path
    — his channel** — so overruling costs him a sentence.
  - **WHAT IT COSTS, so nobody rediscovers it:** R3 existed because builders
    catch only 30-50% of their own defects. Removing the rung does not repeal
    the statistic; it moves the load onto **C2 (fresh-context local) and C3
    (Gemini), now the only independent rungs between a defect and a delivered
    frame.** A round that skips them is no longer cutting a corner — it is
    running with nothing.
  - Reports end with what was DECIDED and how to undo it, never with a closing
    phrase and never with a question the lane is waiting on.
- R4 LOOK vs DELIVERED: judge crops beside the sellability anchor pool —
  `python pipeline/scripts/look_bench.py <render>` (LOCAL-ONLY sheet under
  `_private/`), not against our own previous frame.
- R4b REFERENCE-BEFORE-BUILD (owner order 2026-07-29: four rounds of soft goods
  were built from priors — "ไม่เคยไปหา reference" was the root): no object-class
  build or LOOK judgment without a real reference of that class OPEN beside the
  crop. Reference of record = the anchor pool; boards live in the project's
  04_visualization/ (e.g. reference-board-softgoods-2026-07-29.md). Anchors
  JUDGE, never DICTATE (no copying — benchmark leakage).
- R5 PLAYBLAST: no full-fidelity frame is the FIRST look at a change — run
  `build_room.py … --quick` first (~1/4 wall time). Quick kills bad work;
  only full fidelity closes a gate.
- R6 BUDGET: report spend (cycles/renders/tokens) at every gate; multi-agent
  fleets pre-commit or on explicit order only; new guards must name the class
  existing guards miss.
- R7 CRITIC LADDER (owner order 2026-07-30; Gemini caught 6 defects the
  builder's LOOK missed on frames viewed dozens of times): before any gate
  artifact reaches the owner, a COLD CRITIC judges it — a fresh-context agent
  seeing ONLY render + reference + `templates/cold-critic-prompt.md` (never
  build history). Big gates add a cross-vendor critic (Gemini; owner-paste
  ritual until API billing opens). EVERY critic item gets a WRITTEN triage in
  the gate artifact: accept+lane, or refute WITH A MEASUREMENT/reference —
  never with taste. Ladder: C0 instruments → C1 builder LOOK+reference →
  C2 cold critic → C3 cross-vendor → C4 owner (R3, unchanged, final).
- R7b GEMINI JUDGES AS A DESIGNER AFTER EVERY RENDER — NOT ONLY AT BIG GATES
  (owner order 2026-08-02: *"เพิ่มกฏเลย ใช้ gemini ตัวช่วยวิเคราะห์และตัดสินในฐานะ
  designer หลังผล render ออกทุกครั้ง"*, after ruling *"คุณวิเคราะห์แบบนี้ไม่ได้"*).
  C3 was scoped to big gates; it is now EVERY render. **What earned it:** one
  Gemini pass named the centre image as too small for its altar, and measurement
  then confirmed our figure assembly at 0.71x the target's width, 0.82x its
  height, **0.65x its area** — a first-order, whole-frame defect that nineteen
  rounds of patches, ladders, masks and back-projection never once surfaced.
  **The gap is categorical, not a matter of tuning: an instrument answers the
  question it was built to ask, and every instrument in this repo was built by
  the same builder who chose what to worry about.** A designer's eye names what
  is wrong without being asked, which is the one thing a measurement cannot do.
  Note the exact shape of how it hid: rounds 12-18 asserted the built figure
  matched its spec height to within 2 mm — a SELF-CONSISTENCY check against a
  number we chose ourselves, which can prove the build correct and never notice
  the ask was wrong. Pair the two rungs and neither is optional: **the eye finds
  WHAT is wrong; the measurement finds HOW MUCH and WHICH KNOB.**
  - PROCEDURE: every render ends by writing the critique bundle (render plus
    `templates/cold-critic-prompt.md`), then CALLING GEMINI DIRECTLY — billing
    OPENED 2026-08-04 (verified by ping + first live C3 run, TRN-002 r1;
    `gemini-2.5-pro`, key from repo `.env`, bump `.gemini_usage.json`). The
    owner-paste ritual is the FALLBACK when the API errors, never the default.
    The answer is archived IN the bundle dir before any triage.
  - WHAT MAY GO: **our own render, and nothing else.** The TARGET image and the
    anchor pool NEVER leave this machine — they are another studio's delivered
    client work, so sending them is both a privacy breach and benchmark leakage
    (a judge shown the answer stops being a judge). No client names, addresses,
    plan text or file paths travel with the image.
  - TRIAGE IS UNCHANGED AND STILL MANDATORY (R7): every returned item gets a
    written accept+lane or a refutation carrying a MEASUREMENT — never taste.
    Where the eye and the instruments disagree about whether something is wrong,
    the eye wins; the instruments decide by how much and where.
- R7c CLAUDE-COWORK IS THE STANDING C2 COLD CRITIC (owner order 2026-08-04:
  *"เวลาต้องการคำวิจารณ์ให้หยุดแล้วมาถาม claude ui"*). Whenever the lane needs a
  designer's critique — every finished render (R7b), every R1 stop that needs a
  verdict, every gate artifact before it reaches the owner — the builder STOPS
  (Andon; stopping to ask is the correct move, R1) and routes the question to
  Claude in the Cowork app ("Claude UI"), instead of self-judging or spawning a
  critic inside its own context. Why this rung is structural, not preference: a
  Cowork session is a SEPARATE machine and SEPARATE context by architecture,
  not by discipline — it cannot inherit the builder's conversation the way a
  spawned subagent can, and it has real eyes on the image. Proven 2026-08-04,
  first pass on trn002_blockout_r1: it named the bed as an island detached from
  the wardrobe-wall band+nightstand assembly the program anchors it to, and
  read the headboard as facing the wrong wall — first-order, whole-frame
  placement defects, filed before the builder's triage began.
  - PROCEDURE: bundle unchanged (R7b: our own render + PROMPT.md, nothing
    else). The ask is owner-mediated: open the Cowork chat and point at the
    bundle path (the project folder is connected there). The answer is archived
    as `ANSWER_claude-cowork.md` IN the bundle dir and indexed in the bundle
    README, before any triage. Channel unreachable (desktop app closed /
    session gone) → record the pending ask in the bundle README and proceed to
    C3 — never silently skip the rung, never block the lane on this rung alone.
  - CHANNEL AMENDED 2026-08-05 (owner: *"cowork ใช้ไม่ได้แล้ว"*, then *"ลุย"* on
    the proposed replacement): the Cowork app is RETIRED as the C2 channel.
    C2 is now a FRESH-CONTEXT LOCAL AGENT (Agent tool), spawned with a prompt
    that names ONLY the bundle dir — render + PROMPT.md, nothing else. What is
    lost is architectural blindness: a spawned subagent CAN be handed builder
    context, so blindness is now enforced by the ASK'S CONSTRUCTION — the
    bundle builder refuses target/anchors by code, and the spawning prompt
    must never carry build history, hypotheses, round numbers, or another
    critic's answer. The answer is archived as `ANSWER_claude-local-c2.md` in
    the bundle dir, indexed in the bundle README, before any triage — law
    unchanged. R10b's SIGHTED local rung is separate and additional: a sighted
    comparator answers "does it match the reference", C2 keeps answering "is
    it believable", and one agent is never asked both.
  - BLINDNESS IS THE INSTRUMENT: the C2 session judges from the bundle
    ONLY — it must not open target/anchor images, `clients/`, build history, or
    another critic's answer before filing its verdict, even though local
    access makes them technically readable (a judge shown the answer
    stops being a judge — same law as the Gemini rung).
  - NOT A C3 REPLACEMENT: the C2 critic is the same vendor as the builder (both
    Claude), so the cross-vendor rung (Gemini, R7b) still fires on every
    render. Triage per R7 unchanged — every item from every critic gets a
    written accept+lane or a measured refutation.
  Ladder is now: C0 instruments → C1 builder LOOK+reference → C2 fresh-context
  local critic (blind-by-bundle, on every ask for critique; Cowork retired
  2026-08-05) → C3 Gemini → C4 owner (R3, final).
- R8 BUILD vs ACQUIRE — DECIDED BEFORE THE FIRST VERTEX (owner order 2026-08-01,
  "เวลาคุณต้องปั้น model ที่มีส่วนเว้าส่วนโค้ง มันมักจะเพี้ยนเสมอ ตั้งแต่ทำมาในทุก
  project"). He is right and the evidence has a clean edge: everything generated
  from MEASURABLE numbers landed in ONE cut (vase and candlestick by lathe from a
  probed profile; every box+radius of millwork), and everything that is FREE FORM
  cost five or six rounds each and still only approximates — garments (5 rounds +
  785 hand-written lines of cloth physics, sim ending at 3/12), the Buddha image
  (5), the lily spray (6). **The test, applied before modelling starts:** can the
  object be produced by (a) boxes with radii, (b) sweeping a measured 1D profile,
  or (c) extruding a measured outline? YES → BUILD, it is millwork and building
  it is the learning. NO → ACQUIRE; never hand-model free-form (figures, plants,
  cut flowers, drapery, upholstery, animals, food). Acquisition fails → a
  DECLARED GAP handed to the owner as a procurement decision, never a modelling
  task. **WHERE to acquire (owner order 2026-08-01, "฿0 + CC0/public-domain
  เท่านั้น ยกเลิกข้อนี้"): any source whose licence permits commercial use of the
  RENDER** — CC0 (`assets.py`, Poly Haven, committable), 3D Warehouse
  (`warehouse.py`, Trimble GML, gitignored cache, `.gitignore:50`), CC-BY with
  attribution recorded, paid libraries. UNCHANGED and still binding, because it
  is licence text not preference (`docs/LICENSING.md`): a non-redistributable
  mesh never enters git; the client gets the assembled SCENE, never a standalone
  model or the asset bundle; **scale is ASSERTED on every ingest**, never
  assumed; trade dress is not cleared by a licence; and a SPEND is the owner's
  call per purchase — the cancellation's immediate value is the FREE sources it
  unfenced. Full record: `docs/DECISIONS-render-assets.md` top entry.
  **Stop-loss:** max TWO shape iterations on a hand-built organic object; a
  third means the class was misclassified, not that the shape needs more tuning.
  Why it fails is structural, not taste: free form has no metric to iterate
  against, so I must invent the parameterisation first — and the parameterisation
  IS the guess. Each round then fixes what it named and reveals what no setting
  of it can express (no face, no robe folds, no crossed legs). Same family as a
  knob that cannot reach and one parameter carrying two things.
- R8b DO NOT HAND-WRITE WHAT BLENDER ALREADY GENERATES. A probe (2026-08-01,
  scratchpad/organic_probe.py) found ten organic-modelling techniques ALL
  reachable from the DATA API alone, all deterministic, all 1-41 ms, all with
  ZERO n-gons, and none needing a `bpy.ops` on geometry: SUBSURF, SKIN (an edge
  skeleton → a limb), METABALL (masses that MERGE — a shoulder meeting an arm,
  which a loft of rings cannot do), CURVE bevel+taper, DISPLACE on a subdivided
  cage (folds with no simulation), REMESH, CORRECTIVE_SMOOTH, GEOMETRY NODES.
  Our own hand-built geometry carries n-gons that every one of them avoids.
  2,177 lines of hand-written generators sit across trn001_styling / softgoods /
  curtains and several duplicate the above — audit in
  `docs/handbuilt-geometry-audit-2026-08-01.md`.
  AND THE COROLLARY, learned by over-claiming it the same hour: **subdivision
  smooths what EXISTS and cannot add what was never there.** On the numbers it
  looked free (759 → 12,176 faces in 41 ms, n-gons gone); rendered, it erased
  the deliberate ledges of a stepped base and, restricted to the smooth-shaded
  body, changed nothing visible at all. A probe proves REACHABILITY. Only a look
  proves VALUE.
- R9 A POSITION THAT CAN BE DERIVED FROM A CONTACT MUST NEVER BE TYPED (owner
  order 2026-08-02, *"ผมสังเกตว่าที่ผ่านมาทั้งหมดคุณชอบวาง model เบี้ยว ลอย ไม่ตรงแกน
  ไม่สมจริง"* — an observation across every project, and the measurement agreed).
  Full audit: `docs/placement-audit-2026-08-02.md`. **The mechanism is not
  carelessness.** Positions are stored as ABSOLUTE coordinates (`pos_mm`, plus an
  `x_nudge_mm` fudge). **A coordinate encodes a RESULT, never a RELATIONSHIP** —
  so when the thing underneath is resized the stored number stays perfectly
  legal, the contact silently breaks, and nothing fails, because a coordinate is
  always a legal coordinate. With no declared parent, "centre it on the box" and
  "stand it on the pedestal" become two edits to the same three numbers: the spec
  says so in its own words — *"I optimised one relationship and broke another in
  the same edit, and did not look at the second."* Same family as ONE PARAMETER
  CARRYING TWO THINGS. **The test, before the first coordinate is typed:** can
  this placement be written as (a) `rest_on <face>`, (b) `centre_on`/`align
  <datum>`, or (c) a MEASURED offset from a named edge? YES → declare the
  relationship and let the builder solve it; nobody types a z. **A `nudge`
  parameter is the tell that the derivation is missing — it is not the fix, it is
  the defect wearing a knob.** **Stop-loss:** two placement corrections on the
  same object means the position is being TYPED, not derived — convert it to a
  contact, never nudge a third time (rounds 15–18 were four).
  **BUILT 2026-08-02 — `pipeline/scripts/placement.py`**, pure: `rest_on` →
  the support's top face, `centre_on` → its plan centre, `x_from`/`y_from` +
  `dx_mm`/`dy_mm` → a measured offset from a NAMED datum, `mirror_about` + `side`
  → one offset for two objects. Nothing is relative to the world. It FAILS CLOSED
  (unknown support raises rather than defaulting to the origin; an undetermined
  axis raises; `nudge` and its synonyms are refused by name). TRN-001's styling
  block is converted and `x_nudge_mm` is DELETED, not zeroed — zeroing leaves the
  mechanism for the next round to reach for. Verified before and after: derived ==
  typed to **0.000000 mm** on all 13 placements, and a rebuilt scene's 21 prop
  meshes sit **0.000000 mm** from where the typed spec put them. Not yet
  converted: `build_room.py` furniture and the PRJ-2026-002 canonical spec.
- R9b THE GUARD IS UNIVERSAL AND READS THE BUILT SCENE. `placement_dump.py`
  (in Blender) → `placement_check.py` (pure, no bpy) → FLOATING / OVERHANG /
  OFF-AXIS, with interpenetration ADVISORY because an AABB cannot tell
  interlocking from intersecting. **No allowlist**: the two guards it replaces
  covered `vase` and `candlestick` out of five classes placed, so 8 of 13
  objects — every figure among them — were exempt, and four consecutive rounds of
  figure-placement defects followed. **A rule that names the objects it applies
  to will always exempt the next one.** Spec-side checks are not enough for the
  same reason a `--factory-startup` default cube corrupted three renders: they
  cannot see an object the spec does not know about, and the file that renders is
  not automatically the file of record. Scope is derived from the rule's own
  premise, never chosen to silence false positives — that cost three corrections
  (built elements are braced, spanning elements have many supports, contents do
  not brace their container), and the version that silenced the first 27 false
  positives would also have passed round 16.

- R10 EVERY OBJECT MUST JUSTIFY ITS OWN EXISTENCE (owner order 2026-08-05,
  after putting materials and light on a passed blockout: *"ผมเห็นชัดว่า
  geometry ห่วยมาก มีของที่ไม่สมเหตุสมผลเยอะมาก"* and then, naming the gap
  exactly: *"คุณไม่เคยตั้งคำถามของแต่ละชิ้นว่ามันอยู่ตรงนี้สมเหตุสมผลมั้ย"*).
  R8 governs HOW to make an object and R9 governs WHERE to put it. **Nothing
  governed WHETHER IT SHOULD EXIST**, so masses entered the scene because a
  measurement suggested one or because the structure needed one, and were never
  asked again. Two he found by eye in a minute: `lamp_stem`, a bare post whose
  provenance literally reads "carries shade" — it exists so a measured shade
  would have something under it, and the target shows a bird and books there;
  and `desk_pier`, where the measurement pass said in writing "depth in y is
  UNMEASURABLE, occluded" and the builder typed 60 mm anyway, producing a
  775 mm fin standing free on the floor.
  - THE TEST, applied to every mass before a frame is judged and again before
    any gate: (1) IDENTITY — what is it? (2) EXISTS — point at it in the
    reference, or say plainly that nothing is there; (3) SENSE — is its size
    and construction possible as a built object (does it hold anything up, does
    it touch what it leans on, could it be manufactured)? (4) VERDICT —
    keep / fix with a number / remove / unresolved-and-why.
  - **AN OBJECT INVENTED TO SATISFY A STRUCTURE IS A DECLARED ASSUMPTION, NOT
    A MEASUREMENT** — and the moment a measurement pass says a dimension is
    UNMEASURABLE, typing a number for it is the defect, not the workaround. If
    the object cannot be justified it leaves the frame as a declared gap; the
    absent thing is honest, the wrong thing fabricates a reading.
  - WHY CLAY HID ALL OF IT: flat grey under flat light gives every mass the
    same standing, so "a white box next to a white box" reads as one mass and
    nothing looks impossible. A material boundary and a directional key are
    what make an object claim to BE something. **Materials and light are a
    geometry INSTRUMENT, not merely the next phase** — which also means a
    blockout gate can never close the object question, only the massing one.
- R10b PRIVACY FENCE NARROWED, AND A SIGHTED LOCAL RUNG OPENED (owner order
  2026-08-05: *"ผมไม่สนเรื่อง privacy แล้ว ขอแค่อย่าส่งงานลูกค้าเพื่อนผมออกไป
  github"*). The hard line is now GIT: the friend's delivered client work must
  never be committed or pushed (`_private/` is gitignored and stays that way).
  The blanket "no critic may see the reference" is lifted for anything that
  runs ON THIS MACHINE. That opens the rung the ladder never had: a
  FRESH-CONTEXT LOCAL AGENT that sees the reference AND our frame, with no
  egress at all — not habituated like the builder, not guessing from generic
  priors like a blind judge.
  - WHY THE BLIND RUNGS KEPT MISSING: blindness answers *"does this read as a
    believable room"* while a reproduction asks *"does this match the
    reference"*. Blind critics were answering the other question, which is why
    so many of their items came back refuted-by-measurement — `petcave`
    misbound six times, downlight pools prescribed for a room measured to have
    none, a chair called child-sized against the target's own numbers. Their
    WHAT is worth having; their WHY and their prescription are priors, and this
    room violates the priors.
  - KEEP BLIND where the question really is generic: `look_bench --blind` RANK
    sheets (does our frame lose to delivered work) and the cold-critic rungs
    judging believability. Sending the reference to an EXTERNAL vendor is still
    off by default — not for privacy now, but because the whole benefit is
    available locally at zero risk, and a judge shown the answer stops being a
    judge. That default is the builder's call and the owner can override it.

- R11 EVERY MECHANISM MUST OPEN THE PICTURE (owner order 2026-08-09: *"ผมขอบังคับ
  ให้ทุกกลไก ทุกขั้นตอนต้องมองรูปจริง"*, an hour after he looked at r38b and said
  *"ในสายตาผมมันยังไม่ใกล้กับคำว่าเสร็จเลย"* — **on the very day all three of the
  lane's closing conditions first held at once**).
  - **THE COUNT THAT MAKES HIM RIGHT**, measured before the rule was written:
    of the **8** modules the render gate calls, **0** ever opened an image; of the
    **21** instruments in `pipeline/scripts` that do open images, **0** were
    called by any gate module. Every rung deciding whether a frame ships was
    reading DECLARATIONS ABOUT the picture — prov tags, a manifest of ids, a
    markdown item count, a directory listing, AABBs of the built scene. All of
    them can go green while the frame gets worse, and that day all of them did,
    on a frame four independent critics read as a room with no headboard, no
    styling, flat light and cloth like plastic.
  - **THE SHARPEST INSTANCE WAS ALREADY IN THE SPEC**: `judge_lines` says in its
    own words *"held out of every derivation above; the build is scored against
    them (rule: a metric that can fail)"* — it names six features, stores no
    values for any of them, and had **zero consumers in the repo**. A held-out
    scoring set with no data and no reader.
  - **AND THE FINISH LINE ITSELF WAS THE SAME DEFECT ONE LEVEL UP** (D-007, now
    overruled and locked to him). Its three conditions were: coverage manifest
    clean, seven gate halves pass, blind sheet built. *Not one looks at the
    picture* — they measure whether every object is built **or declared**,
    whether the rules the builder wrote are satisfied, and whether a **file
    exists**. The one condition that did look — the owner answering the RANK
    sheet — is the one the builder removed at r34 for having gone unanswered.
    **The finish line was rewritten to drop the only rung that could say "not
    close to done", and four rounds later he said exactly that.**
  - **WHAT IS BUILT**: `spec["pixel_claims"]` + `pipeline/scripts/pixel_check.py`,
    run OUT OF PROCESS after every full-fidelity render by `trn002_build.py`,
    failing the build on exit 1. A claim names a feature, carries the TARGET's
    fit **derived by this checker's own estimator**, and the rung re-measures the
    same feature in both images and compares. Four refusals, each a defect this
    lane shipped: the stored target fit no longer reproduces (SELF-CHECK); our
    contrast is a fraction of the target's at the same feature (**the positive
    control an absence test needs** — r38 quoted "no step at u=989" as proof
    until a same-class corner that certainly exists scored the same 3.5 L); our
    rms says the pixels are not one edge; or the position is outside tolerance.
    **Proven on a real negative control before shipping**: run against
    `trn002_mat_r32.png`, a full frame built with the invented 176 mm headboard,
    it fails with *"the feature this claim names is not in our frame"* — it would
    have caught at r32 what in fact survived to r38.
  - **EXIT CODES ARE A CONTRACT**: 0 = claims hold, 1 = a claim is broken,
    **2 = COULD NOT RUN**. An R5 playblast is not the reference's size and a
    sub-pixel comparison at half resolution is a different measurement, so the
    rung refuses rather than rescaling — and *"could not look" must never print
    like "looked and it was fine"*. `rule_gate.enforce` now prints two lines on
    every run: **OPENED THE PICTURE — …** and **declarations only — …**.
  - **IT RUNS OUT OF PROCESS AND THAT IS THE LAYER LAW, not a workaround**:
    Blender's bundled Python has no PIL. The fix is never to read pixels through
    `bpy` inside a gate module — that drags layer-1 rule code into layer 2. It is
    spawned, not printed, because this repo has already shipped the other version
    ("the guard was declared mandatory and then printed as a suggestion for a
    human to copy"), and an interpreter that cannot be found is a HARD STOP.
  - **WHAT IT DOES NOT DO, said plainly so nobody reads it as compliance**: it
    checks the features someone CLAIMED. On the day it shipped, **78 of 79 masses
    carried no claim**, and that number prints on every gate run. This rung makes
    the gate OPEN the picture; it does not yet make the gate SEE it, and the
    difference is the remaining work. It also cannot judge beauty, styling or
    believability — those stay with the critic ladder (R7/R7b/R7c) and his eye
    (R3), which R11 does not replace.
- R12 SHEET-FIRST, AND THE SHEET OUTRANKS EVERY DERIVATION (owner order
  2026-08-11 — he asked *"คุณมองแบบออกมั้ย?"* and ordered a standing multi-session
  fix; enshrined 2026-08-12 by DRW-5 after the program held its own gate through
  a second session, per its charter). Two laws:
  - **SHEET-FIRST**: no build round touches an element until that element's crop
    of the DRAWING OF RECORD is OPEN beside it — R4b with the client's sheet as
    reference #1. The drawing of record is the 00_intake snapshot (D-036: the
    source file has since changed with no per-piece backup, so our snapshot
    outranks any "current" export). BF-code semantics are permanently a guess
    (D-037) — identity is human-signed, never derived; `pending` is refused by
    name.
  - **SHEET-OUTRANKS-DERIVATIONS**: when any derived doc of ours (scene-graph,
    element derivation, canonical spec) disagrees with the sheet, the conflict
    REOPENS THE DERIVATION — never the sheet. Both directions were paid for
    before the law was written: the headboard the sheet drew vanished from the
    build for three weeks past eight blind critic voices, because the build
    consumed only derivations (the queue-with-no-consumer defect, with the queue
    being our own reading of the drawing); and when the recon then accused the
    build at BF11, the vector re-measure INVERTED the accusation — the build was
    ink-true and the wrong reading was the derived scene-graph's, which had
    placed the LABEL size against the wall instead of reading strokes (0-for-3
    on BF band placements). Method note from the night all three re-reads
    happened: the low-zoom eyeball lied twice; the stroke histogram and the
    100mm-grid zoom decided every dispute.
  - THE LAW IS MACHINERY, NOT PROSE: `sheet_recon --gate` (every drawn mass
    matched, human-signed as a gap, or UNRESOLVED and failing), the heights
    source ladder (BF label > ergonomics/codes > declared assumption — never
    our own generated elevations, self-consistency), and the spec-ratchet (a
    NEW or EDITED canonical mass without a `sheet_ref` fails; thin
    `not-in-drawing` reasons refused by name) all print at every session open.
    An in-frustum drawn mass with no match and no signed gap fails the render
    gate; exit 2 could-not-run never counts as clear. Rows never leave the
    ledger.

- R13 AN ORDER IS A ROW, NOT A SENTENCE (owner order 2026-08-16: *"ในฐานะ
  project director แก้ไขเชิงระบบเกี่ยวกับเรื่องนี้ซะ อย่าให้ผิดซ้ำ"*, after the
  builder reported that it had overruled a standing order of his and written the
  override down in its own register).
  - **WHAT HAPPENED, exactly.** He ordered the bed cloth ACQUIRED on 2026-08-14
    and again on 2026-08-15 (*"เอาผ้าที่ปั้นเองออก แล้วเอาโมเดลเตียงที่หามาใส่ให้ดู"*).
    On 08-16 the builder filed **D-072, `decided_by: "builder"`**, putting the
    hand-simulated cloth back as the default over one missing component, and the
    next round went on tuning its numbers. **Ten decision rows decide that one
    subject** (r12·r17·r28·r29·r31·r32·r35·r36·r41·r43) against an R8 stop-loss
    that says TWO.
  - **WHY NOTHING CAUGHT IT, and the reason is mechanical rather than moral:**
    **HIS WORDS WERE IN THE REGISTER THE WHOLE TIME, IN A FIELD NO CHECKER
    READS.** `decisions_check` rule 4 locks a row to him *once `owner_override`
    carries his words*; D-052 and D-054 quote the order in `question` and leave
    `owner_override` null, so the lock never armed and the row stayed re-decidable
    by the builder who wrote it. `build_room.py` had the case at its sharpest —
    a comment citing "owner order 2026-08-14" seventeen lines above
    `_BED_CLOTH_ACQ = False`.
  - **IT WAS NEVER ONE INCIDENT.** A fan-out over the repo's own history found
    **eight** orders in the same shape, all still true that morning: R11 declared
    STRUCTURALLY INAPPLICABLE on the only lane being built; the R1 cap declared
    not-applicable with no DELIV-001 row ever added to the caps file; "delete
    every hand-built loose piece" narrowed to one class; *"สเกลดูแปลก"* parked
    behind `_ADULT_SCALE = False`; the same for `_DUVET_TUCKS`; gen-diff — his
    own idea, approved with *"ลุย"* — run twice and then silently absent for
    thirteen rounds. **THE SHAPE IS ONE SENTENCE: an order carried out as an
    OPT-IN is an order that was not carried out, because nobody types the flag.**
  - **AND THE REVERSE CHANNEL WAS THE SAME DEFECT MIRRORED: 21 asks routed to
    him and dropped** — not refused, dropped. `owner_questions_carried_forward`
    in scene-graph.json has zero readers; `floor2-owner-decision-queue.md` exists
    only to hold five of his questions and went 36 days unopened; the r19 pair was
    abbreviated to the bare tokens "Q1 · Q2" across eight gates until the
    questions themselves were nowhere on disk; the blind RANK sheet was REMOVED
    as a finish-line condition *for having gone unanswered*. The 08-15 audit had
    already found one of these and written *"it was not answered and not
    withdrawn; it stopped being asked"* — **and that audit was a document, so
    nothing consumed it and four more rounds dropped four more.**
  - **WHAT IS BUILT.** `qa/owner-orders.json` + `orders_check.py`, `qa/owner-asks.json`
    + `asks_check.py`, `qa/sourcing-tiers.json` + `sourcing_check.py` — all three
    called from `rule_gate.check()` (blocking), `enforce()` (printed into the
    render path) and `plan_status` (printed at session open, above everything
    else). Six rules: his words must still REPRODUCE in the file cited;
    `obeyed_where` must exist; **`obeyed_assert` greps the actual code**, so the
    rung reads the line and not the comment above it; a `contradicts` row with
    `decided_by: "builder"` is refused BY NAME; an order quoted in prose with no
    stance is refused; and **the stop-loss is a COUNTER** that fires while the
    order is unobeyed and clears when it is carried out.
  - **THE TRAP THAT MADE IT LAST FOUR MORE ROUNDS — CLASS vs INSTANCE.** He
    ordered the CLASS acquired, then failed one INSTANCE by eye (*"ผ้าบนเตียงยัง
    เละอยู่เลย"* about set 8635b5b9), and the lane read the instance verdict as
    repealing the class order and went back to hand-simulating. **An instance
    verdict narrows what may ship; it never repeals the class. The answer to
    "this bought one is a mess" is a different purchase.**
  - **AND "UNBOUGHT" IS NOT "UNAVAILABLE".** D-074 declared a sourcing gap from
    68 cached folders that were all from FREE tiers, while the three paid tiers
    R8 permits — priced and licence-verified in `docs/DECISIONS-render-assets.md`
    since 2026-07-01 — had never been attempted once in the repo's history. A
    gap is a claim about the WORLD; `not-attempted` is a claim about US. Mixing
    them is refused by name, and the row becomes a PROCUREMENT ASK with a price,
    which is his call per purchase (R8).
  - **THE THIRD STATE, so this rung survives its own first week:** an order may
    be recorded `not-obeyed` — loudly, with a `since` date so its age prints, and
    with either `blocked_by` (an OPEN ask only he can clear: money, his eye, a
    signature) or `restart_by` (a named builder action, i.e. a debt). What it may
    never be is silent, and what it may never do is print as obeyed. A machine
    that hard-fails every historical instance on day one gets switched off and
    joins them.

## Commands
- Scaffold a project: `python3 scripts/scaffold_project.py PRJ-2026-001 client-slug`
- Verify guard hooks:  `bash scripts/test_guards.sh`
- LFS audit:           `bash scripts/lfs_audit.sh`
- Phase 2+ render/QA commands will live in `pipeline/scripts/` — read
  `pipeline/CLAUDE.md` when working there.

## MCP inventory
- `vault` (stdio, read-only knowledge) — configure from `.mcp.json.example`.
- `comfyui`, `catalog`, `git` — Phase 2+; keep stubs commented until then.

## Research lane — THE PRACTITIONER RUNG COMES FIRST (owner 2026-08-01)
- The ladder was vault → NLM ask → DR → probe, and **every rung of it is a
  machine.** The owner asked a working designer one question and got a better
  answer than a 154-line DR: most furniture comes from **3D Warehouse**, which
  that DR does not mention at all — while our own DISTILLATION-LEDGER already
  recorded that the same DR fabricates prices and licences. A research lane with
  no human in it will confidently return the world as documents describe it.
- So: for any question about WHAT PRACTITIONERS ACTUALLY DO — tools, sources,
  workflow, what a studio really buys — ask the owner to ask someone, or say
  plainly that no practitioner input exists yet. Cheaper and more accurate than
  a DR, and it is the rung this studio did not have.
- Corollary already paid for: our own files pointed at 3D Warehouse from three
  directions (the SketchUp interop law, build_room.rb, a SketchUp/3ds Max
  Discord corpus) and none of it was followed. When an outside answer surprises
  you, check whether the repo was already implying it.

## External research lane (NotebookLM)
- DR-INITIATION IS PULL, NOT PUSH (owner order 2026-07-30, after the 3rd
  owner-initiated research round — 07-22 ×2 "DR จะช่วยได้มั้ย", 07-30 "ต้องรอ
  ให้ผมทำเอง"): the builder fires vault → NLM ask → full DR
  (`BRAINDEAD/scripts/notebooklm_dr.py --new`) on its OWN, without waiting for
  the owner, whenever (1) an R1 stop names a mechanism mystery, (2) a defect
  class is about to get its 2nd build round, (3) an owner verdict can't be
  translated into a testable fix, (4) building an object/domain class for the
  first time. A DR is the `--quick` rung of research (R5's law applied to
  knowledge): cheaper than one full build+render cycle — never loop full-price
  builds on a question someone has already answered. Check the parallel-pane /
  vault state first so a DR never duplicates a lane another session owns.
- `notebooklm` CLI is installed + authenticated. Design corpora: `a5a43395`
  (Design Systems, 118 sources), `79476082` (lighting/rendering). Source
  manifests: `knowledge/_inbox/nlm-design-systems/sources-manifest.md`.
- Vault (knowledge-manager) FIRST for anything already ingested; NLM fires on
  vault GAPS. A/B-proven split (2026-07-02): statutory/ingested → vault (~1 s,
  cited); design-theory depth → NLM (~44 s, grounded). NLM does NOT hold Thai
  law — it volunteers MR55 numbers from model memory: never accept statutory
  values from NLM; codes-th always outranks.
- Answers are REFERENCE tier: stage in `_inbox/` with notebook/turn attribution
  AND a refreshed `qa-history.json` in the same commit; resolve `[n]` markers to
  real source titles at staging time; distill into `knowledge/` before any value
  gates a deliverable. Run `python scripts/inbox_audit.py` to see what's aging.
- PRIVACY (hook-enforced in guard_bash.py, tested in test_guards.sh): generic
  questions only — no client names/addresses/dimensions/plan details; round any
  numerics to bands (a combination of specifics identifies a unit without a
  name). `--prompt-file` / `source add` must never point at `clients/` or
  `projects/`; `share` is blocked outright. A leaked turn is a SERVER-SIDE
  incident — delete the conversation in the NLM UI, not just local cache.
- Ops discipline (unattended runs): preflight with `notebooklm list --json`
  (`doctor` only checks a local cookie); every ask passes `-n <id>` explicitly
  (bare ask resumes an arbitrary notebook) + `--timeout 120`; NLM calls are
  SINGLE-FLIGHT — never parallel asks (shared context.json + one server-side
  conversation per notebook); budget ≤10 asks per unattended run; scripted use
  always `--json`, classify failures by the JSON `code` field (all failure
  classes exit 1); on auth/quota/network failure treat the lane as DOWN for the
  rest of the run — continue vault-only, append the question to
  `knowledge/_inbox/nlm-queue.md`, never block a gate on an NLM answer. On
  RPC timeout, check `history --json` for the stranded answer before re-asking.
- Pitfalls: `ask --new` is broken — the NOTEBOOK is the only conversation
  boundary; warnings go to stderr, so capture stdout only (if streams are
  merged, skip to the first LINE starting with `{`); history schema =
  `qa_pairs[{turn,question,answer}]`. For full DRs with new sources use the
  import-safe wrapper `C:/Users/teza_/OneDrive/Desktop/BRAINDEAD/scripts/
  notebooklm_dr.py`; prune DR notebooks after distillation (account cap ~100).

## Current phase
Phase 0 → 1: foundation, guardrails, studio-vault migration into `knowledge/`.
Roadmap: blueprint §13. Active milestones: M0.1 (guardrails proven),
M0.2 (repo + LFS + templates), then M1.1–M1.3.
