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

## Commands
- Scaffold a project: `python3 scripts/scaffold_project.py PRJ-2026-001 client-slug`
- Verify guard hooks:  `bash scripts/test_guards.sh`
- LFS audit:           `bash scripts/lfs_audit.sh`
- Phase 2+ render/QA commands will live in `pipeline/scripts/` — read
  `pipeline/CLAUDE.md` when working there.

## MCP inventory
- `vault` (stdio, read-only knowledge) — configure from `.mcp.json.example`.
- `comfyui`, `catalog`, `git` — Phase 2+; keep stubs commented until then.

## External research lane (NotebookLM)
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
