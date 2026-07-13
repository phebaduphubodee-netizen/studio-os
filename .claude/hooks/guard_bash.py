#!/usr/bin/env python3
"""PreToolUse guard for Bash tool calls.

Reads the hook JSON from stdin. Exit 2 blocks the tool call and the stderr
message is fed back to the model so it can reconsider. Exit 0 allows.

This is the LAW layer (blueprint §11.1). Security never lives in CLAUDE.md.
"""
import json
import re
import sys

BLOCKED = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "recursive force delete (rm -rf)"),
    (r"\bgit\s+push\b.*(--force|-f)\b", "force push"),
    (r"\bgit\s+reset\s+--hard\b.*\borigin\b", "hard reset to remote"),
    (r"\bchmod\s+777\b", "world-writable chmod"),
    (r"\bcurl\b[^|;&]*\|\s*(ba|z|da)?sh\b", "piping remote script into a shell"),
    (r"\bwget\b[^|;&]*\|\s*(ba|z|da)?sh\b", "piping remote script into a shell"),
    (r">\s*\.env\b", "overwriting .env"),
    (r"\bmkfs\.", "filesystem format"),
    (r"\bdd\s+if=", "raw disk write (dd)"),
    (r"\bgit\s+filter-branch\b", "history rewrite"),
    (r"\bshutdown\b|\breboot\b", "system power command"),
    # PowerShell equivalents (hook matcher covers Bash|PowerShell; PS is case-insensitive)
    (r"(?i)\b(remove-item|rm|ri|del|erase)\b[^|;]*\s-(recurse|r)\b[^|;]*\s-(force|fo?)\b",
     "recursive force delete (Remove-Item -Recurse -Force)"),
    (r"(?i)\b(remove-item|rm|ri|del|erase)\b[^|;]*\s-(force|fo?)\b[^|;]*\s-(recurse|r)\b",
     "recursive force delete (Remove-Item -Force -Recurse)"),
    (r"(?i)\b(iex|invoke-expression)\b[^|;]*\b(iwr|invoke-webrequest|invoke-restmethod|curl|wget)\b",
     "executing downloaded script (iex + web request)"),
    (r"(?i)\b(iwr|invoke-webrequest|invoke-restmethod)\b[^;]*\|\s*(iex|invoke-expression)\b",
     "piping web content into Invoke-Expression"),
    (r"(?i)\b(stop-computer|restart-computer)\b", "system power command"),
    (r"(?i)\b(format-volume|clear-disk|initialize-disk)\b", "disk format/initialize"),
    # NotebookLM external-research lane (CLAUDE.md): client data must never reach
    # Google. Generic asks pass; these are the realistic leak vectors (red-teamed
    # 2026-07-02 — all five passed the guard before these patterns existed).
    (r"(?i)\bnotebooklm\b[^\"'|;&]*\bshare\b",
     "notebooklm share (external exposure — no studio use case; unblock via PR)"),
    (r"(?i)\bnotebooklm\b(?=.*(--prompt-file|source\s+add|add-research))"
     r"(?=.*(clients[/\\]|projects[/\\]|_private[/\\]|00_intake|01_brief))",
     "uploading client/project files to NotebookLM"),
    (r"(?i)(clients[/\\]|projects[/\\]|_private[/\\])[^|;&]*\|[^|;&]*\bnotebooklm\b",
     "piping client/project file content into NotebookLM"),
    (r"(?i)\bnotebooklm\b[^|;&]*(\$\(|`)",
     "command substitution into a NotebookLM query (unreviewable content)"),
    (r"(?i)\bnotebooklm\b.*\b(PRJ-\d{4}-\d{3}|C-\d{3})\b",
     "client/project identifier in a NotebookLM command"),
    # NotebookLM was never the only way out. Every EXTERNAL SINK below ships bytes off this
    # machine (cloud judge, image API, DR tools, raw HTTP), and _private/ holds a real
    # designer's CLIENT work (2026-07-12 owner call: local-only, never leaves the machine).
    # The old rules guarded clients/|projects/ against notebooklm ONLY — so `critique.py
    # _private/<client render>.png` or `curl -F file=@clients/...` walked straight through.
    # This closes sink x path for ALL of them. Reading these paths LOCALLY stays free.
    # UPLOAD forms only — `curl -o projects/x.zip` (a download INTO the repo) is legitimate and
    # must keep working; `curl -F file=@_private/...` (a client file going OUT) must not.
    # Each pattern demands a REAL path (a separator + at least one path character) after the
    # directory name: without that, a mere mention of the word `_private` next to a `|` in a
    # grep/sed script false-blocks — which it did, on the first command run after this landed.
    (r"(?i)\b(curl|wget|invoke-webrequest|invoke-restmethod|iwr)\b[^|;&]*"
     r"(-F\b|--form\b|-d\b|--data(-binary|-raw)?\b|-T\b|--upload-file\b|-(In)?File\b|-Body\b|@)"
     r"[^|;&]*(clients|projects|_private)[/\\][\w.\-/\\]+",
     "uploading a client/private file to an external endpoint"),
    (r"(?i)\b(critique|hybrid_render|gemini_\w+|chatgpt_\w+|perplexity_\w+)\.py\b"
     r"[^|;&]*(clients|_private)[/\\][\w.\-/\\]+",
     "passing client/private files to a cloud-model script (critique/render/DR call an API)"),
    (r"(?i)(clients|_private)[/\\][\w.\-/\\]+[^|;&]*\|[^|;&]*"
     r"\b(curl|wget|invoke-webrequest|invoke-restmethod|iwr)\b",
     "piping client/private file content into an HTTP request"),
    # python IS this pipeline's own language (critique.py, hybrid_render, the DR tools are all
    # python, and python3 is partly allow-listed) — so an inline interpreter reading a client file
    # AND opening a network connection is the MOST realistic accidental exfil, not curl. Requires
    # BOTH a client/private path and a network indicator, so `python -c "json.load(open('_private/
    # x'))"` (a legitimate LOCAL read) stays allowed.
    (r"(?i)\b(python3?|node|ruby|perl)\b[^|;&]*\s-(c|e)\b"
     r"(?=[^|;&]*(clients|_private)[/\\])"
     r"(?=[^|;&]*(urlopen|urllib|requests|httpx?|socket|smtplib|ftplib|https?://|\.post\(|upload))",
     "inline interpreter reading a client/private file and opening a network connection"),
    # file-copy / raw-socket sinks that are not HTTP at all
    (r"(?i)\b(scp|rsync|rclone|sftp|nc|ncat|netcat)\b[^|;&]*(clients|_private)[/\\][\w.\-/\\]+",
     "copying a client/private file to a remote host (scp/rsync/rclone/nc)"),
    # OWNER-AUTHORED SIGN-OFF LEDGERS (2026-07-12) — the shell half of the guard_paths rule.
    # SEMANTIC facts (where a zoning line goes; which SKU is really being bought) are OWNER-ONLY, and
    # the owner's signature is what makes the call STICK. Round 4 of the plan reader proved a
    # signature the AGENT composes at run time is worthless: it authored both sides of the check and
    # wrote a 17.5 m² "owner-signed" room off a line the owner never saw. So the signature moved into
    # a ledger the OWNER writes — and blocking Write/Edit alone would be pointless while `echo ... >
    # zoning-signoff.json` or `python -c "open(led,'w')"` walked straight through.
    # READING is untouched (`cat`/`python reader.py --owner-ledger led.json` must keep working); only
    # a ledger appearing as the TARGET of a mutation is blocked.
    (r"(?i)(>>?|\b(tee|mv|move-item|cp|copy-item|rm|remove-item|del|new-item|rename-item|"
     r"set-content|add-content|out-file|clear-content)\b)[^|;&]*"
     r"\b(zoning|sourcing)-signoff\.json\b",
     "writing an OWNER-AUTHORED sign-off ledger (*-signoff.json). The owner signs; the agent reads. "
     "Print the canonical key and ask the owner to add the entry"),
    # An inline interpreter's INTENT is not statically decidable (`open(p)` vs `open(p,'w')` is one
    # character), so any `python -c` naming a ledger is refused outright — fail-safe, and cheap:
    # read it with `cat` or the Read tool, which cannot mutate anything.
    # NB the tail is `.*`, not `[^|;&]*`: the FIRST version of this rule used the no-separator class
    # copied from the exfil patterns and a real forgery walked straight through it, because inline
    # python is FULL of semicolons (`import json;d=json.load(...)`). Caught by test_guards.sh.
    (r"(?i)\b(python3?|node|ruby|perl)\b[^|&]*\s-(c|e)\b.*\b(zoning|sourcing)-signoff\.json\b",
     "inline interpreter naming an OWNER-AUTHORED sign-off ledger (its write-intent is undecidable "
     "from the command string). Read it with `cat`; only the owner appends to it"),
]

# HONEST SCOPE (2026-07-12 review): this is a best-effort TRIPWIRE against the agent naively or
# accidentally shipping client/_private data off the machine — it catches the sinks a helpful
# assistant actually reaches for. It is NOT a boundary against a determined adversary: an
# allowlist of sink commands cannot be completed by hand (base64-then-paste, a python module that
# reads its path from a variable, an MCP/WebFetch tool outside Bash scope, etc. all remain).
# The real control is network-egress denial at the sandbox layer; treat these patterns as
# defence-in-depth, not a guarantee.

# Paths that must never be touched via shell redirection/moves either.
PROTECTED_PATH_HINTS = [
    "qa/thresholds.yaml",
    "knowledge/codes-th",
    ".claude/settings.json",
    ".gitattributes",
]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # never brick the session on malformed hook input
    cmd = (data.get("tool_input") or {}).get("command", "") or ""

    for pattern, reason in BLOCKED:
        if re.search(pattern, cmd):
            print(
                f"BLOCKED by guard_bash: {reason}. "
                f"This action is prohibited by studio policy. Command: {cmd[:200]}",
                file=sys.stderr,
            )
            return 2

    lowered = cmd.lower().replace("\\", "/")
    if any(tok in lowered for tok in ("rm ", "mv ", " > ", ">> ", "tee ",
                                      "remove-item", "move-item", "copy-item", "rename-item",
                                      "set-content", "add-content", "out-file", "clear-content",
                                      "new-item")):
        for p in PROTECTED_PATH_HINTS:
            if p.lower() in lowered:
                print(
                    f"BLOCKED by guard_bash: shell mutation of protected path '{p}'. "
                    "Propose changes via PR instead.",
                    file=sys.stderr,
                )
                return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
