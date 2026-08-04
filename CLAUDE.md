# STUDIO-OS — Root Instructions

AI interior design studio monorepo (Thai residential: condos, houses, townhomes).
Claude Code is the orchestrator; the filesystem is the state machine; deterministic
hooks are law. Full architecture: STUDIO-OS Implementation Blueprint v1.0 (docs/).

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
- R2 GATE: every stop hands the owner `templates/gate-artifact.md` (image pair +
  3 lines + spend). The lane BLOCKS on an unanswered gate. Gate on decisions,
  not keystrokes (no micro-iteration spam).
- R3 DONE: only the owner closes a round. Reports end "พร้อมให้ตัดสิน", never
  "เสร็จ" (builders catch 30-50% of their own defects).
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
