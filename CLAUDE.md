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
- `notebooklm` CLI is installed + authenticated on this machine. Design corpora:
  `a5a43395` (Design Systems, 118 sources), `79476082` (lighting/rendering).
- Fire it when the vault has a gap; vault (knowledge-manager) stays first for
  anything already ingested. Answers are REFERENCE tier: stage in `_inbox/`
  with notebook/turn attribution, distill into `knowledge/` before any value
  gates a deliverable. codes-th citations always outrank NLM answers.
- PRIVACY: generic questions only — never client names, addresses, dimensions,
  or plan details in a query (same rule as web search).
- Pitfalls: `ask --new` is advertised but broken — the NOTEBOOK is the only
  conversation boundary; `--json` output has warning lines before the JSON
  (skip to first `{`); history schema = `qa_pairs[{turn,question,answer}]`.
  For firing full DRs with new sources, use the import-safe wrapper at
  `Desktop/BRAINDEAD/scripts/notebooklm_dr.py`.

## Current phase
Phase 0 → 1: foundation, guardrails, studio-vault migration into `knowledge/`.
Roadmap: blueprint §13. Active milestones: M0.1 (guardrails proven),
M0.2 (repo + LFS + templates), then M1.1–M1.3.
