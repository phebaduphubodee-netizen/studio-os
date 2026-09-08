#!/usr/bin/env python3
"""ONE source of truth for the client/project identifiers that must never leave this machine.

Imported by BOTH guards, which is the whole point:
  * guard_egress.py -- WebFetch / WebSearch / Artifact / external MCP tools
  * guard_bash.py   -- shell sinks (the URLs and request bodies inside a command)

The 2026-07-13 adversarial review found the SAME leak -- an identifier sitting in a URL query
string -- blocked on the web path and wide open on the shell path, because each guard carried its
own half-remembered copy of the rules. A shared list is the fix; a second copy is the bug.

WHAT IS DELIBERATELY *NOT* HERE
-------------------------------
A BARE, opaque client id (`C-001`) with no "client" word and no path around it. It is
shape-identical to a furniture SKU / model code (`armchair C-203`, a Hafele `.../C-100/` product
URL), and FF&E research against supplier catalogues is a core studio workflow -- blocking it would
false-block real work every day, and an opaque id carries no name, address or dimension with it.
A MEASURED TRADE, not an oversight: it also means `curl "https://hook/?d=C-001"` still passes.

A client's NAME, ADDRESS, or a room's REAL DIMENSIONS in plain prose are not here either: they are
not enumerable from this repo. These patterns are a TRIPWIRE, not a boundary. The real control for
a determined adversary is network-egress denial at the sandbox layer.
"""
import re

_SEP = r"[-_\s]?"  # an id paraphrased as "PRJ 2026 002" or "C_001" is still the id

# Repo paths + project/client identifiers. Screened on EVERY sink, shell and web alike.
IDENTIFIERS = [
    (r"(?i)\bclients[/\\]+C" + _SEP + r"\d{3}",
     "a clients/ path (a real client's folder)"),
    (r"(?i)\b_private[/\\]+[\w.\-]",
     "a _private/ path (the designer's own client work: local-only, owner call 2026-07-12)"),
    (r"(?i)\bprojects[/\\]+PRJ" + _SEP + r"\d{4}" + _SEP + r"\d{3}",
     "a projects/PRJ-... path"),
    (r"(?i)(00_intake|01_brief)[/\\]+",
     "an intake/brief stage path (client-supplied documents)"),
    (r"(?i)\bPRJ" + _SEP + r"\d{4}" + _SEP + r"\d{3}\b",
     "a project identifier (PRJ-YYYY-NNN)"),
    (r"(?i)\bclients?\b.{0,24}?\bC" + _SEP + r"\d{3}\b",
     "a client identifier (C-NNN) next to the word 'client'"),
    (r"(?i)\bC" + _SEP + r"\d{3}\b.{0,24}?\bclients?\b",
     "a client identifier (C-NNN) next to the word 'client'"),
    (r"(?i)ลูกค้า.{0,24}?\bC" + _SEP + r"\d{3}\b",
     "a client identifier (C-NNN) next to the Thai word for 'client'"),
]

# A LOCAL absolute path handed to a WEB tool is never a legitimate web call -- it is a local file
# being fed to something that talks to the internet. Screened on the web/publish sinks only: inside
# a shell command a local path is not a leak, it is what a shell is FOR.
LOCAL_PATHS = [
    (r"(?i)\b[a-z]:[\\/]+(users|onedrive)",
     "a local Windows filesystem path"),
    (r"(?i)(^|[^a-z0-9])/[a-z]/(users|onedrive)\b",
     "a local Windows filesystem path (MSYS form)"),
]

_CACHE = {}


def find_leak(text, groups):
    """Scan `text` against the given pattern groups. -> (matched_text, description) or None."""
    if not text:
        return None
    for group in groups:
        for pattern, what in group:
            rx = _CACHE.get(pattern)
            if rx is None:
                rx = _CACHE[pattern] = re.compile(pattern)
            m = rx.search(text)
            if m:
                return m.group(0), what
    return None
