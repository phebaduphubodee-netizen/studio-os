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
- 2026-07-02: Ported an AI-access layer into `tools/` (Gemini DR + image, Perplexity, ChatGPT),
  domain-cleaned from BRAINDEAD/INTERIOR-AI (their scripts hard-coded a BTC prompt — stripped).
  Keys live in a gitignored `.env` (Gemini/OpenAI/Perplexity only; no crypto keys). AI-access
  permissions went in `.claude/settings.local.json`, NOT the PR-only `settings.json`.
- 2026-07-02: Added the `ffe-research` skill (back-office FF&E product research). It writes
  `03_layout/ffe-candidates.json` (the "furniture candidates with real dimensions" Stage 03 needs)
  and `scripts/ffe_schedule.py` renders a driftless `ffe-schedule.md` from it (JSON = source of
  truth). Client BOM stays with the human-triggered `bom-generate` skill (Stage 07). Dimensions are
  stored in the candidate JSON here (unlike INTERIOR-AI, which pulled them from a 3D model) because
  in STUDIO-OS the candidate list IS the dimension source the layout consumes. Gold-standard
  fixture: `examples/ffe-candidates.example.json`.
