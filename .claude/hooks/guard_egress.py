#!/usr/bin/env python3
"""PreToolUse guard for every NON-SHELL way bytes leave this machine.

(Was guard_web.py, 2026-07-13. Renamed when its scope grew past the two web tools: a file called
"guard_web" that also screens artifact publishing and MCP calls is a lie the next reader pays for.)

Covers        | Clean call ->        | Why
--------------|----------------------|--------------------------------------------------------
WebFetch      | ALLOW, no prompt     | This is the point. `.claude/settings.json` carries
WebSearch     |                      | `ask: [WebSearch, WebFetch]`, and an `ask` rule outranks
              |                      | every `allow` from every source, so a deep-research run
              |                      | stopped at EVERY source and waited for a click. (The
              |                      | user-level allowlist had grown 300+ WebFetch(domain:...)
              |                      | entries that could never fire: proof the review that gate
              |                      | bought was a rubber stamp.) A PreToolUse `allow` decision
              |                      | bypasses the permission system, so the run goes unattended
              |                      | -- but only after this file has READ the URL and prompt.
--------------|----------------------|--------------------------------------------------------
Artifact      | ABSTAIN (exit 0)     | Publishing is OUTWARD-FACING. Nobody asked for it to stop
external MCP  |                      | prompting, and auto-approving it would be a loosening the
              |                      | owner never requested. So these are screened but NEVER
              |                      | auto-allowed: a leak is BLOCKED, and a clean call is simply
              |                      | handed back to the normal permission rules untouched.

The `ask: [WebSearch, WebFetch]` entries in settings.json are the LOAD-BEARING FALLBACK for when
this hook does not run at all (missing python3, a syntax error here, a settings source that failed
to load). They look dead now. They are not. Deleting them turns any hook failure into a silent
unscreened allow. test_guards.sh fails if they disappear.

HONEST SCOPE: a TRIPWIRE, not a boundary -- see leak_patterns.py for what it deliberately cannot
and does not catch (plain-prose names/addresses/dimensions; a bare opaque C-001).
"""
import json
import os
import re
import sys

# A guard that CRASHES fails OPEN. On a Thai-locale Windows box stderr can be cp874, which cannot
# encode an em-dash, so one stray non-ASCII character in a block message would turn a BLOCK into an
# exit-1 pass. Every printed string below is plain ASCII; this is the second lock.
for _stream in (sys.stderr, sys.stdout):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leak_patterns import IDENTIFIERS, LOCAL_PATHS, find_leak  # noqa: E402

WEB_TOOLS = ("WebFetch", "WebSearch")
ALLOWED_SCHEMES = ("http://", "https://")

# MCP servers that never leave this machine. Screening their queries would false-block real work
# (the vault IS knowledge/; asking it about a client is not egress). Anything NOT on this list --
# including a server added tomorrow -- is treated as external and screened. Fail-safe by default.
LOCAL_MCP_SERVERS = ("vault", "comfyui", "catalog", "git")

MAX_ARTIFACT_BYTES = 2_000_000


def _block(what: str, matched: str, sink: str) -> int:
    print(
        f"BLOCKED by guard_egress: this {sink} call carries {what} (matched {matched!r}). "
        "CLAUDE.md: client data stays local. No client names, addresses, plan details or "
        "client/project paths may reach an external sink. Ask the question generically, round any "
        "dimension to a band, and never hand a repo path to a tool that talks to the internet.",
        file=sys.stderr,
    )
    return 2


def _ask(reason: str) -> int:
    """Explicit ASK (exit 0). Used on any internal failure, so the hook fails CLOSED even if the
    committed `ask` fallback is someday removed."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason,
    }}))
    return 0


def _strings(obj):
    """Every string anywhere in a tool_input, however nested."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _strings(v)


def _decoded(text: str) -> str:
    """Scan raw AND percent-decoded: the remote server decodes %2F back into a path separator, so
    `clients%2FC-001` is a real leak that the raw text hides."""
    try:
        from urllib.parse import unquote
        dec = unquote(text)
    except Exception:
        return text
    return text if dec == text else text + "\n" + dec


# --------------------------------------------------------------------------- web (allow or block)
def _web(tool: str, ti: dict) -> int:
    if tool == "WebFetch":
        url = str(ti.get("url", "")).strip()
        if url and not url.lower().startswith(ALLOWED_SCHEMES):
            print(
                f"BLOCKED by guard_egress: WebFetch URL scheme is not http(s): {url[:120]!r}. "
                "file:// / data: / ftp: URLs are how a LOCAL file gets shipped to a remote reader. "
                "Fetch the web with WebFetch; read local files with Read.",
                file=sys.stderr,
            )
            return 2
        text = "\n".join([url, str(ti.get("prompt", ""))])
    else:
        parts = [str(ti.get("query", ""))]
        for key in ("allowed_domains", "blocked_domains"):
            v = ti.get(key)
            if isinstance(v, list):
                parts += [str(x) for x in v]
        text = "\n".join(parts)

    hit = find_leak(_decoded(text), (IDENTIFIERS, LOCAL_PATHS))
    if hit:
        return _block(hit[1], hit[0], tool)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "guard_egress: no client/project identifiers in the query, "
                                        "URL or prompt; http(s) only.",
        },
        "suppressOutput": True,
    }))
    return 0


# ----------------------------------------------------------------- artifact (block or stand aside)
def _artifact(ti: dict, cwd: str) -> int:
    meta = "\n".join(str(ti.get(k, "")) for k in ("file_path", "description", "title", "url"))
    hit = find_leak(_decoded(meta), (IDENTIFIERS,))
    if hit:
        return _block(hit[1], hit[0], "Artifact publish")

    fp = ti.get("file_path")
    if not fp:
        return 0  # e.g. action:"list" -- nothing is being published

    # The PATH proves nothing: the client data is INSIDE the html. Screening only tool_input would
    # be theatre, so read what is actually about to be hosted on claude.ai.
    path = fp if os.path.isabs(fp) else os.path.join(cwd or os.getcwd(), fp)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            body = fh.read(MAX_ARTIFACT_BYTES)
    except OSError as e:
        # UNREADABLE == UNSCREENED. Abstaining here would mean a file this guard never looked at
        # could be published under an allow-rule with nobody in the loop. Ask instead. (Caught by
        # the suite the first time it ran: the fixture sat at a path python could not open, the
        # guard shrugged, and a leaky artifact sailed through as "clean".)
        return _ask(f"guard_egress: cannot read {fp!r} to screen it before publishing "
                    f"({type(e).__name__}); asking rather than publishing something unread.")

    hit = find_leak(_decoded(body), (IDENTIFIERS,))
    if hit:
        return _block(hit[1], hit[0], "Artifact publish")
    return 0  # clean -> no opinion. Publishing keeps its normal permission prompt.


# ---------------------------------------------------------------------- mcp (block or stand aside)
def _mcp(tool: str, ti: dict) -> int:
    parts = tool.split("__")
    server = parts[1] if len(parts) > 2 else ""
    if server in LOCAL_MCP_SERVERS:
        return 0
    hit = find_leak(_decoded("\n".join(_strings(ti))), (IDENTIFIERS,))
    if hit:
        return _block(hit[1], hit[0], f"MCP ({server})")
    return 0


def main() -> int:
    try:
        # RAW BYTES, decoded as UTF-8 by us. json.load(sys.stdin) uses the Windows LOCALE codec,
        # which turned a Thai "ลูกค้า C-001" into mojibake and silently defeated the client-id rule
        # before any regex ran. Claude Code always sends hook JSON as UTF-8.
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        return _ask("guard_egress: could not parse hook input; asking to be safe.")

    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    try:
        if tool in WEB_TOOLS:
            return _web(tool, ti)
        if tool == "Artifact":
            return _artifact(ti, cwd)
        if tool.startswith("mcp__"):
            return _mcp(tool, ti)
        return 0  # not a sink this guard owns
    except Exception as e:
        return _ask(f"guard_egress crashed ({type(e).__name__}); asking to be safe.")


if __name__ == "__main__":
    sys.exit(main())
