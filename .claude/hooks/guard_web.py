#!/usr/bin/env python3
"""PreToolUse guard for WebFetch / WebSearch — the DR lane's egress law.

WHY THIS EXISTS
---------------
`.claude/settings.json` carries `ask: ["WebSearch", "WebFetch"]`. An `ask` rule
outranks every `allow` rule from every settings source, so each source a deep-
research run touches stopped the run dead and waited for a human click. The
owner's user-level allowlist has since accreted 300+ `WebFetch(domain:...)`
entries that can never fire — visible proof that the "review" that gate bought
was a rubber stamp, one bored click at a time.

The gate was there for a real rule (CLAUDE.md): *client data stays local — no
client names, addresses, or floor plans in web searches or external tool calls.*
So this hook does not simply delete the gate; it replaces a human who says yes to
everything with a machine that reads every URL, prompt and query first:

  * BLOCK (exit 2) anything carrying client/project-identifying material, or any
    non-http(s) URL scheme (file://, data:, ftp: — the shapes that ship a local
    file out).
  * ALLOW everything else with NO prompt, so a DR fan-out runs unattended.

HONEST SCOPE — read before trusting this
----------------------------------------
Same class of instrument as guard_bash.py: a TRIPWIRE, not a boundary. It pins
the mechanical leaks (a repo path, a PRJ id, a file:// URL pasted into a fetch).
It CANNOT, and does not try to, catch:
  * a client's NAME, ADDRESS or a room's REAL DIMENSIONS typed as plain prose
    ("88 sqm condo Sukhumvit soi 24") — not enumerable from this repo. The human
    gate it replaces could not reliably catch these either (it was clicking yes).
  * a BARE, opaque client id `C-001` with no "client" word and no path around it —
    deliberately allowed, because it is shape-identical to a furniture SKU / model
    code (`armchair C-203`, a Hafele `.../C-100/` URL) and FF&E research is the
    exact DR use case this hook exists to unblock. Blocking those would kill the
    fan-out and the guard would be ripped out. An opaque id with no name/address
    attached is low-value to leak; the false-block cost is high. See LEAKS below.
  * OTHER egress tools: this hook's matcher is WebFetch|WebSearch only. Bash `curl`
    is (partly) covered by guard_bash.py; the Artifact publish tool, and MCP tools
    like mcp__scite__* that ship a query to a third-party API, are NOT covered by
    any guard. A per-tool matcher cannot be completed by hand — the real control is
    sandbox-layer network-egress denial; treat this as defence-in-depth.

WHERE IT LIVES
--------------
`.claude/hooks/` — the law layer, and registered in the COMMITTED .claude/settings.json.
Two properties follow, and both are the reason this file was promoted here (2026-07-13)
out of scripts/, where the agent had to author it because guard_paths.py (correctly)
forbids an agent from writing law files into .claude/hooks/:
  1. SELF-GUARDED. guard_paths.py protects `.claude/hooks/**` from the Write/Edit tool,
     so a later agent cannot quietly weaken the LEAKS patterns below.
  2. A REPO INVARIANT. It travels with a clone. While it lived in the gitignored
     settings.local.json, the web screen was a property of ONE machine.

THE `ask` RULE IS THE LOAD-BEARING FALLBACK — DO NOT DELETE IT
-------------------------------------------------------------
.claude/settings.json still carries `ask: ["WebSearch", "WebFetch"]`. It looks dead now
that this hook auto-allows every clean call. It is NOT. It is what governs when this hook
does not run at all: python3 missing, a syntax error in this file, a settings source that
did not load. Delete it and any hook failure becomes a SILENT UNSCREENED ALLOW instead of
a prompt. Note also that no permission rule can content-screen a query — only a hook can —
so this hook cannot be replaced by "just fixing the ask rules". Do not simplify either away.
"""
import json
import re
import sys
from urllib.parse import unquote

# A guard that CRASHES is a guard that fails OPEN: a non-2 exit lets the tool call proceed to the
# normal permission rules. On a Thai-locale Windows box stderr can be cp874, which cannot encode an
# em-dash — so a single stray non-ASCII character in a block message would silently turn a BLOCK into
# an exit-1 pass. Every printed string below is therefore plain ASCII, and this is the second lock.
for _stream in (sys.stderr, sys.stdout):
    try:
        _stream.reconfigure(errors="replace")  # py3.7+; no-op if already lenient
    except Exception:
        pass

# --- what may never leave this machine ------------------------------------------------
# Each pattern demands a REAL identifier IN A LEAKY CONTEXT, not a bare English word:
# "clients" / "projects" alone appear all over the public web, and a guard that cries wolf
# on those (or on furniture SKUs) gets ripped out within a day, taking the real rules with it.
# Separator classes are [/\\] AFTER unquote() (see _text), so %2F/%5C are already decoded;
# ids allow an optional [-_\s] between segments so a paraphrase ("PRJ 2026 002") is still caught.
_SEP = r"[-_\s]?"
LEAKS = [
    # Repo PATHS — unambiguous: a client/project folder structure in a web call.
    (r"(?i)\bclients[/\\]+C" + _SEP + r"\d{3}",
     "a clients/ path (a real client's folder)"),
    (r"(?i)\b_private[/\\]+[\w.\-]",
     "a _private/ path (the designer's own client work: local-only, owner call 2026-07-12)"),
    (r"(?i)\bprojects[/\\]+PRJ" + _SEP + r"\d{4}" + _SEP + r"\d{3}",
     "a projects/PRJ-... path"),
    (r"(?i)(00_intake|01_brief)[/\\]+",
     "an intake/brief stage path (client-supplied documents)"),
    # A PROJECT id is distinctive (the "PRJ" prefix + two numeric groups rarely collides with a
    # public code), so catch it bare, in any separator form. A same-shape public tender/grant id
    # is a rare, accepted false-block.
    (r"(?i)\bPRJ" + _SEP + r"\d{4}" + _SEP + r"\d{3}\b",
     "a project identifier (PRJ-YYYY-NNN)"),
    # A CLIENT id C-NNN is shape-identical to a furniture SKU, so a BARE C-203 is intentionally
    # ALLOWED (see the honest-scope note). It is blocked only when the word client/ลูกค้า sits
    # within a short window — that context is what marks it as a client id rather than a product.
    (r"(?i)\bclients?\b.{0,24}?\bC" + _SEP + r"\d{3}\b",
     "a client identifier (C-NNN) next to the word 'client'"),
    (r"(?i)\bC" + _SEP + r"\d{3}\b.{0,24}?\bclients?\b",
     "a client identifier (C-NNN) next to the word 'client'"),
    (r"(?i)ลูกค้า.{0,24}?\bC" + _SEP + r"\d{3}\b",
     "a client identifier (C-NNN) next to the Thai word for 'client'"),
    # A local absolute path handed to a web tool is never a legit web call. Cover doubled
    # separators (JSON/shell echoes: C:\\Users) and the MSYS /c/users form (no colon).
    (r"(?i)\b[a-z]:[\\/]+(users|onedrive)",
     "a local Windows filesystem path"),
    (r"(?i)(^|[^a-z0-9])/[a-z]/(users|onedrive)\b",
     "a local Windows filesystem path (MSYS form)"),
]

ALLOWED_SCHEMES = ("http://", "https://")


def _text(tool_name: str, ti: dict) -> str:
    """Every field the tool actually ships outward, concatenated for scanning — raw AND
    percent-decoded, because the remote server decodes %2F/%5C back into path separators our
    classes would otherwise miss (clients%2FC-001 -> clients/C-001)."""
    parts = []
    if tool_name == "WebFetch":
        parts += [str(ti.get("url", "")), str(ti.get("prompt", ""))]
    elif tool_name == "WebSearch":
        parts += [str(ti.get("query", ""))]
        for key in ("allowed_domains", "blocked_domains"):
            v = ti.get(key)
            if isinstance(v, list):
                parts += [str(x) for x in v]
    raw = "\n".join(parts)
    try:
        decoded = unquote(raw)
    except Exception:
        decoded = raw
    return raw if decoded == raw else raw + "\n" + decoded


def _ask(reason: str) -> int:
    """Emit an explicit ASK decision (exit 0). Used on any internal failure so the hook fails
    CLOSED — safe even after the committed `ask` fallback is (someday) removed."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        },
    }))
    return 0


def _decide(tool: str, data: dict) -> int:
    ti = data.get("tool_input") or {}
    text = _text(tool, ti)

    if tool == "WebFetch":
        url = str(ti.get("url", "")).strip()
        if url and not url.lower().startswith(ALLOWED_SCHEMES):
            print(
                f"BLOCKED by guard_web: WebFetch URL scheme is not http(s): {url[:120]!r}. "
                "file:// / data: / ftp: URLs are how a LOCAL file gets shipped to a remote "
                "reader. Fetch the web with WebFetch; read local files with Read.",
                file=sys.stderr,
            )
            return 2

    for pattern, what in LEAKS:
        m = re.search(pattern, text)
        if m:
            print(
                f"BLOCKED by guard_web: this {tool} call carries {what} "
                f"(matched {m.group(0)!r}). CLAUDE.md: client data stays local. No client "
                "names, addresses, plan details or client/project paths in web searches or "
                "external tool calls. Ask the question generically, round any dimension to a "
                "band, and never pass a repo path to a web tool.",
                file=sys.stderr,
            )
            return 2

    # Clean -> allow outright. This is the line that ends per-source clicking during a DR run:
    # a PreToolUse `allow` decision bypasses the permission system, so the committed
    # `ask: [WebFetch, WebSearch]` rule no longer stops every single fetch.
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "guard_web: no client/project identifiers in the query, "
                                        "URL or prompt; http(s) only.",
        },
        "suppressOutput": True,
    }))
    return 0


def main() -> int:
    try:
        # Read RAW BYTES and decode UTF-8 ourselves. `json.load(sys.stdin)` uses the locale codec
        # on Windows (cp874/cp1252), which mangles any non-ASCII payload BEFORE the regexes run --
        # a Thai "ลูกค้า C-001" arrived as 24 mojibake bytes and slipped past the client-id rule.
        # Claude Code always sends hook JSON as UTF-8; decode it as such regardless of console locale.
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        # Malformed hook input on a WebFetch|WebSearch call (this hook's only matcher): don't
        # guess, ASK. Fails closed independently of the committed `ask` fallback.
        return _ask("guard_web: could not parse hook input; asking to be safe.")
    tool = data.get("tool_name", "")
    if tool not in ("WebFetch", "WebSearch"):
        return 0  # no opinion — let the normal permission rules decide
    try:
        return _decide(tool, data)
    except Exception as e:
        # A CRASH must not fail OPEN. A bare `return 0` would fall through to the committed `ask`
        # rule today, but the whole point of this hook is to let the owner delete that rule — so
        # make the safe fallback explicit and self-contained.
        return _ask(f"guard_web crashed ({type(e).__name__}); asking to be safe.")


if __name__ == "__main__":
    sys.exit(main())
