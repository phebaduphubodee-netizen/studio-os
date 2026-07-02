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
    ".gitattributes",
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
