#!/usr/bin/env python3
"""PreToolUse guard for Write/Edit/MultiEdit tool calls.

Blocks file mutations to protected paths (defense in depth alongside the
permissions deny list). Exit 2 = block with reason on stderr.
"""
import json
import os
import sys

PROTECTED = (
    "qa/thresholds.yaml",
    "knowledge/codes-th/",
    ".claude/settings.json",
    ".claude/hooks/",     # THE LAW LAYER MUST GUARD ITSELF. Measured 2026-07-12: an agent could
                          # simply EDIT this file to delete the rule below, which would make every
                          # claim about the owner ledger false. settings.json was already protected;
                          # the hooks it POINTS AT were not. (Tripwire, not a boundary — see the
                          # honest-scope note in guard_bash.py: a determined agent edits the hook
                          # BEFORE it fires, or never routes through Bash/Write at all.)
    ".gitattributes",
)

# OWNER-AUTHORED SIGN-OFF LEDGERS (2026-07-12). The two-layer law says SEMANTIC facts — identity,
# facing, indoor/outdoor, which SKU is really being bought, where a zoning line goes — are OWNER-ONLY,
# and an owner signature is what makes a correction STICK. Round 4 of the plan reader proved that a
# signature the AGENT composes at run time is no signature at all: the agent authored both sides of
# the check and wrote a 17.5 m² "owner-signed" room off a zoning line the owner never saw.
#
# So the signature lives in a ledger the OWNER writes and the agent may only READ. An agent that can
# append to the ledger has not been gated, it has been decorated — THIS is the line that makes the
# gate real, and it belongs here, in the law layer, not in a docstring.
#
# Matched on BASENAME (these files live under _private/ and per-project dirs, not one fixed path).
# `*-signoff.example.json` templates stay writable: they sign nothing.
PROTECTED_BASENAMES = (
    "zoning-signoff.json",      # bluehouse_plan_reader / zoning_signoff_gate — semantic plan geometry
    "sourcing-signoff.json",    # ffe_signoff_gate — the confirmed live SKU behind a client BOM
)


def canon(p: str) -> str:
    """Windows paths are case-insensitive and arrive in mixed forms
    (C:\\x, c:/x, MSYS /c/x) — unify them so prefix-stripping can't be
    bypassed by a casing or drive-notation mismatch."""
    p = os.path.normpath(p).replace("\\", "/")
    if os.name == "nt":
        if len(p) > 2 and p[0] == "/" and p[1].isalpha() and p[2] == "/":
            p = p[1] + ":" + p[2:]
        p = p.lower()
    return p


def norm(path: str, cwd: str) -> str:
    if not path:
        return ""
    p = path if os.path.isabs(path) else os.path.join(cwd, path)
    p = canon(p)
    root = canon(os.environ.get("CLAUDE_PROJECT_DIR", cwd)).rstrip("/")
    if p.startswith(root + "/"):
        p = p[len(root) + 1 :]
    return p


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    cwd = data.get("cwd") or os.getcwd()
    tool_input = data.get("tool_input") or {}
    target = norm(tool_input.get("file_path", ""), cwd)
    if not target:
        return 0
    if os.path.basename(target) in PROTECTED_BASENAMES:
        print(
            f"BLOCKED by guard_paths: '{target}' is an OWNER-AUTHORED SIGN-OFF LEDGER. "
            "The owner writes it; the agent may only READ it. A signature the agent can write "
            "is not a signature — it is theatre. If a line/SKU genuinely needs signing, print "
            "its canonical key and ASK THE OWNER to add the entry.",
            file=sys.stderr,
        )
        return 2
    for p in PROTECTED:
        if target == p.rstrip("/") or target.startswith(p):
            print(
                f"BLOCKED by guard_paths: '{target}' is protected. "
                "Change it via a pull request with human review, not a direct edit.",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
