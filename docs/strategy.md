# STUDIO-OS Strategy Document (human-curated — the WHY layer)
## Architecture decisions
- 2026-07: Adopted STUDIO-OS blueprint v1.0. Hybrid monorepo + ICM stages.
## Known technical debt
- (none yet)
## Security audit findings
- 2026-07-02 M0.1 audit (Windows 11 native, Git Bash + Windows Python 3.12):
  - `bash scripts/test_guards.sh` → **ALL GREEN 10/10** (after the two fixes below).
  - Live tests in Claude Code: (1) `rm -rf /tmp/x` → BLOCKED by guard_bash hook (stderr message
    surfaced to model); (2) Edit `qa/thresholds.yaml` brisque→100 → BLOCKED by permissions deny
    layer; (3) append to `docs/strategy.md` → allowed (this entry). PostToolUse audit trail
    confirmed live at `logs/write-audit.log`.
  - FIXED (machine): `python3` resolved to the Microsoft-Store stub, so every hook failed open.
    Fix: copied `python.exe` → `python3.exe` in `%LOCALAPPDATA%\Programs\Python\Python312`
    (user-local, reversible; alternative is WSL2 per SETUP §0).
  - FIXED (guard_paths.py): Windows bypass — an absolute `file_path` whose drive-letter case
    differed from `CLAUDE_PROJECT_DIR` (`c:\` vs `C:\`), or MSYS `/c/` notation, escaped the
    project-root prefix strip, leaving protected paths editable. Live session confirmed Claude
    Code passes lowercase `c:\`, so the bypass was the active configuration. Patched `norm()`
    with `canon()`: separator + MSYS-drive unification and case-folding on Windows only
    (POSIX semantics unchanged). Re-tested: all 4 Windows-form cases behave correctly.
  - OPEN: hook matchers cover tool `Bash` only — on Windows the PowerShell tool bypasses
    guard_bash entirely. Proposal (settings.json is PR-only, do not hot-edit): change both
    PreToolUse matchers to `"Bash|PowerShell"` and teach guard_bash.py the PowerShell
    equivalents (`Remove-Item -Recurse -Force`, `Set-Content`/`Out-File` to protected paths).
  - NOTE: hooks fail open on malformed stdin by design (e.g. BOM-prefixed JSON from a
    PowerShell 5.1 pipe). Acceptable while the permissions deny list covers the same paths —
    that second layer held in live test 2.
## Session learnings (agents append after major tasks)
- 2026-07-03: INTERIOR-AI salvage port (user-directed). Carried the durable lessons:
  (1) LLM emits a validated SPEC only — never geometry code; one fixed tested generator
  (now pipeline/scripts/, unvalidated here — smoke test = next pipeline task).
  (2) Render direction of record: HYBRID — 3D render as structural control + Gemini
  image pass (~$0.04/img, paid tier for commercial rights) — chosen over local FLUX,
  which this machine cannot run anyway (6 GB VRAM). (3) Dimensional correctness is the
  studio's real edge; clearance engine seeds Gate 0 but its rules JSON must be
  reconciled against codes-th (Authority outranks Panero defaults where they conflict).
  (4) ODA DWG converter is a non-commercial-EULA landmine — dwg_ingest.py's tiering or
  DXF-only. (5) licensing: ship assembled Combined-Work scenes only (docs/LICENSING.md).
  NOT ported: outputs (owner-judged poor), friend/client raw data (privacy), old
  .claude config (superseded). SECURITY FLAG for the human: an R2 secret once touched
  a transcript via a synced .env in the predecessor projects — rotate that Cloudflare
  R2 key. Also NLM notebook "Design Systems and Integration Protocols Interface"
  (118 sources) queried → 5 REFERENCE summaries staged in _inbox/nlm-design-systems.
- 2026-07-03: M1.2 closed via PR #2 (merged). codes-th now holds the Authority values
  from กฎกระทรวง ฉ.55 (รวมถึง ฉ.68/2563) + ฉ.39 (รวมถึง ฉ.63/2551) + Act overview, every
  value cited (ข้อ + PDF page), source PDFs in _inbox/codes-th-sources (LFS, ASA library).
  The sanitary-fixture table was visually verified against rendered PDF pages (poppler)
  after text extraction proved column-ambiguous — pattern to reuse: extract text for
  values, render pages to VERIFY tables. Eval now 25 questions at 23/25 (codes 5/5 top-1);
  knowledge-manager answers planning questions with correct line citations. Registered
  gaps: ข้อบัญญัติ กทม. 2544, พ.ร.บ.อาคารชุด/ระเบียบนิติฯ, corridor-width interpretation
  (within-unit vs common, ข้อ 21). Hooks PR #1 also merged today — restart session then
  live-test the PowerShell matcher. Poppler + Node LTS now installed on this machine.
- 2026-07-02 (overnight run): Phase 1 core landed on Windows native.
  M1.1: BM25 retrieval (scripts/vault_search.py, stdlib-only, Thai char-bigrams)
  + knowledge-manager agent + 20-question eval at 20/20 (qa/reports/M1.1-…md —
  read its overfit caveats before re-tuning). M1.3: four directory CLAUDE.mds;
  root stays ≈70 lines. Five blueprint skills live; intake-parse e2e-proven on
  the test project including a prompt-injection quarantine fixture that now
  lives permanently in projects/PRJ-2026-001_test-run/00_intake/.
  Security: hooks PR branch fix/hook-powershell-matcher (guard matcher +
  PowerShell patterns, 30 test cases green) awaits push + PR + merge + session
  restart. NOT done: M1.2 codes-th corpus — needs the actual Thai statute
  texts (พ.ร.บ./กฎกระทรวง PDFs or authoritative sources), which are not on
  this machine; the _inbox DR summary is not Authority-grade source. GitHub
  remote awaits the user's one-time `gh auth login`. Node LTS install may
  need a UAC confirmation (vault MCP via npx; .mcp.json activated).
- 2026-07-02: Ported an AI-access layer into `tools/` (Gemini DR + image, Perplexity, ChatGPT),
  domain-cleaned from BRAINDEAD/INTERIOR-AI (their scripts hard-coded a BTC prompt — stripped).
  Keys live in a gitignored `.env` (Gemini/OpenAI/Perplexity only; no crypto keys). AI-access
  permissions went in `.claude/settings.local.json`, NOT the PR-only `settings.json`.
- 2026-07-02 (later): studio-vault v2.2 arrived in Downloads and was migrated to
  `knowledge/studio-vault/` unmodified, 44/44 files verified (commit 4b5736b). Two safety renames:
  the vault's own CLAUDE.md → `_vault-CLAUDE-v2.2.md` (a directory CLAUDE.md would auto-load its
  old orchestration rules into STUDIO-OS sessions) and its .gitignore → `_vault-gitignore.txt`.
  The vault is operational knowledge (pricing, checklists, client/material/supplier templates,
  old slash commands) — no codes/ergonomics/lighting content, so those knowledge/ dirs still fill
  in Phase 1 (M1.2 Thai Authority corpus). Old vault commands are Phase 1 skill-porting source.
  Blueprint v1.0 now lives at docs/STUDIO-OS_Implementation_Blueprint.md; the 11-report ID-project
  corpus (source PDFs) is staged in knowledge/_inbox/id-project-corpus/ as LFS objects (72ad58d).
  ALL Phase 0 exit criteria are now met.
- 2026-07-02: Phase 0 closed on Windows native (M0.1 + M0.2) — details in Security audit findings.
  studio-vault v2.2 was NOT yet on this machine at close time (searched Desktop, Documents,
  Downloads, BRAINDEAD, INTERIOR-AI) — resolved later same day, see entry above. Interim: 8
  design-domain DR docs from INTERIOR-AI staged into `knowledge/_inbox/interior-ai/` via the
  sanctioned ingestion path; the thai-building-code DR waits there for human review before any
  of it may enter codes-th/ (PR-only). Machine facts for Phase 2 planning: GPU is an RTX 3060
  Laptop 6GB VRAM — FLUX.1-dev local (needs 16–24GB) is NOT feasible here; plan cloud GPU or an
  API/smaller-model fallback. Repo lives inside OneDrive — watch for sync/file-lock artifacts;
  moving out of OneDrive (or to WSL2) is the safer long-term home.
- 2026-07-02: Added the `ffe-research` skill (back-office FF&E product research). It writes
  `03_layout/ffe-candidates.json` (the "furniture candidates with real dimensions" Stage 03 needs)
  and `scripts/ffe_schedule.py` renders a driftless `ffe-schedule.md` from it (JSON = source of
  truth). Client BOM stays with the human-triggered `bom-generate` skill (Stage 07). Dimensions are
  stored in the candidate JSON here (unlike INTERIOR-AI, which pulled them from a 3D model) because
  in STUDIO-OS the candidate list IS the dimension source the layout consumes. Gold-standard
  fixture: `examples/ffe-candidates.example.json`.
