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
]

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

    lowered = cmd.lower()
    if any(tok in lowered for tok in ("rm ", "mv ", " > ", ">> ", "tee ")):
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
