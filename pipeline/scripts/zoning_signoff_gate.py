"""
zoning_signoff_gate.py — the OWNER-SIGN gate for SEMANTIC plan geometry (zoning lines).

This is ffe_signoff_gate.py's pattern, applied to the other half of the two-layer law. Same shape,
same vocabulary, ONE studio signing mechanism:

    ffe_signoff_gate                     zoning_signoff_gate
    ----------------------------------   ------------------------------------------------
    a sourced pick (a SKU)               a virtual edge (a zoning line the sheet never draws)
    canonical_key = source:sku | comp.   canonical_key = <sheet>|<axis>:<f_lo>:<f_hi>:<lo>:<hi>
    sourcing-signoff.json                zoning-signoff.json
    entry {sku|key, by, date}            entry {key, by, date}          <- SAME sign_status()
    the OWNER writes the ledger          the OWNER writes the ledger
    the gate READS it                    the gate READS it

WHY THIS EXISTS (round 5). Round 4 bound the owner's signature to the geometry it NAMED — a
`--owner-signature "... | edges=h:4970:5069:3120:7720 | ..."` string plus a bijection check against
the `--owner-edge` argv. The reviewer broke it in one line: the AGENT authored BOTH SIDES of that
bijection. A self-consistent signature naming a bogus edge (h:3905:4005:3120:7720 — a line the owner
never saw) passed the bijection, exited 0, and wrote a 17.5 m2 "owner-signed" room. Worse, the three
AGENT-PROVISIONAL edges were laundered to owner-signed simply by re-passing them as --owner-edge and
naming them in the forged string. The signature was bound to ARGV, not to the OWNER.

An owner signature must be an artefact the OWNER produced and the agent can only READ. So:

  * The signature lives in a `zoning-signoff.json` LEDGER, keyed by the edge's CANONICAL KEY. Not in
    argv, not in a flag, not in prose the caller composes at run time.
  * The key is SHEET-NAMESPACED (source pdf stem + page) and GEOMETRIC (the snapped ink-face
    coordinates, 0.1 mm). A signature is therefore NON-TRANSFERABLE across sheets AND across lines:
    move the edge one face and the key changes and the entry no longer binds.
  * A valid sign needs a real `by` (NOT the OWNER-CONFIRM-PENDING template), a `date`, and the `key`
    — sign_status() is IMPORTED from ffe_signoff_gate, so "what counts as a signature" has exactly
    ONE definition in this studio.
  * LAST valid matching entry wins (the owner APPENDS corrections; a trailing typo never erases an
    earlier valid sign) — same append-a-correction semantic as ffe_signoff_gate / placement_gate.
  * An entry that binds NO written edge on this sheet is an ORPHAN: surfaced (never dropped, never
    silently satisfied), and it is what makes the artefact's audit block capable of being FALSE.

WHAT THIS DOES NOT DO — READ THIS BEFORE TRUSTING IT. The agent has write access to the filesystem.
The ledger is a plain JSON file in the repo tree. Nothing here is cryptographic. The ONLY thing
standing between an agent and a forged owner entry is the PreToolUse guard hook (.claude/hooks/
guard_paths.py + guard_bash.py), which blocks Write/Edit/MultiEdit and shell mutation of any
`*-signoff.json`. That hook is a real, firing control for the agent's tool surface — and it is NOT a
cryptographic boundary. See the RESIDUAL TRUST section at the bottom of this file.

    python zoning_signoff_gate.py <zoning-signoff.json> --sheet <id>      # inspect a ledger
"""
import argparse
import hashlib
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ONE definition of "is this a signature": imported, never re-implemented.
#   valid == real `by` (not the OWNER-CONFIRM-PENDING template) + a `date` + a key anchor.
from ffe_signoff_gate import sign_status, load_signoff  # noqa: E402

LEDGER_BASENAME = "zoning-signoff.json"
SCHEMA = "interior-ai/zoning-signoff@0.1"


def sheet_id(pdf_path, page):
    """The sheet a signature is scoped to: the source pdf's stem + the page. A signature for the
    living zone of THIS plan can never bind an edge on another sheet or another page."""
    stem = os.path.splitext(os.path.basename(str(pdf_path)))[0]
    stem = re.sub(r"\s+", "-", stem.strip()).lower()
    return f"{stem}:p{int(page)}"


def edge_spec_canon(ve):
    """The SNAPPED edge, as a canonical spec string at 0.1 mm. `ve` is the dict parse_virtual_edge
    returns — i.e. the coordinates have ALREADY been snapped onto real ink faces, so the owner may
    type the printed datum (4970) and the agent may type the same, and both land on the same key."""
    return "%s:%.1f:%.1f:%.1f:%.1f" % (ve["axis"], ve["face_lo"], ve["face_hi"],
                                       ve["gap_lo"], ve["gap_hi"])


def canonical_key(sheet, ve):
    """<sheet>|<axis>:<face_lo>:<face_hi>:<lo>:<hi> — what the owner copies into the ledger, and the
    ONLY thing a written edge is matched on. Sheet-namespaced (no cross-sheet replay) and geometric
    (no cross-line replay)."""
    return norm_key(f"{sheet}|{edge_spec_canon(ve)}")


def norm_key(k):
    """Whitespace/case normalisation ONLY. Deliberately NOT a fuzzy match: ffe_signoff_gate's
    load-bearing bug was an over-tolerant key (a source abbreviation collapsed two products into one
    bindable bucket). A zoning key is machine-generated on both sides, so it needs no tolerance —
    and tolerance here would mean one signature binding a line the owner never saw."""
    return re.sub(r"\s+", "", str(k or "")).lower()


def entry_key(entry):
    """The canonical key an entry binds, or None."""
    if not isinstance(entry, dict):
        return None
    k = entry.get("key")
    return norm_key(k) if str(k or "").strip() else None


def entry_sheet(entry):
    """The sheet an entry is scoped to — parsed from its own key. An entry whose key carries no
    sheet namespace is NOT scoped and binds nothing (it would be a season ticket)."""
    k = entry_key(entry)
    return k.split("|", 1)[0] if k and "|" in k else None


def load_ledger(path):
    """(entries, sha256, err). Missing/malformed -> ([], None, reason). Never raises: a ledger the
    gate cannot read is a ledger that signs NOTHING, which is the fail-safe direction."""
    if not path:
        return [], None, "no --owner-ledger given"
    if not os.path.exists(path):
        return [], None, f"ledger not found: {path}"
    try:
        raw = open(path, "rb").read()
        doc = json.loads(raw.decode("utf-8"))
    except (ValueError, OSError) as e:
        return [], None, f"ledger unreadable ({e.__class__.__name__}): {path}"
    return load_signoff(doc), hashlib.sha256(raw).hexdigest(), None


def resolve_edge(key, entries):
    """The VALID owner entry binding this canonical key, or None. LAST valid match wins."""
    best = None
    for e in entries or []:
        if sign_status(e) != "valid":
            continue                       # pending / incomplete / inert can neither sign nor erase
        if entry_key(e) == norm_key(key):
            best = e
    return best


def orphans(entries, bound_keys, sheet):
    """VALID entries scoped to THIS sheet that bind none of the edges actually written. The owner
    signed a line the agent did not use: a REVIEW surface, never dropped, never a silent pass."""
    bound = {norm_key(k) for k in bound_keys}
    return [e for e in entries or []
            if sign_status(e) == "valid" and entry_sheet(e) == sheet
            and entry_key(e) not in bound]


def malformed(entries):
    """Entries that TRIED to sign (a real signer) but carry no usable key/date anchor. Surfaced —
    a broken signature must never look like an absent one."""
    return [e for e in entries or [] if sign_status(e) == "incomplete"]


def signoff_block(ledger_path, sha, entries, bound, sheet):
    """The audit block stamped into the room-spec. Every field here VARIES with the run — there is
    deliberately no always-true boolean. (Round 4 stamped `bijection_verified: true` in every
    artefact on disk, because a failed bijection refused the write: a CONSTANT dressed as an audit
    result, which made a FORGED room look MORE audited than an unbound one.)"""
    orph = orphans(entries, [b["key"] for b in bound], sheet)
    mal = malformed(entries)
    return {
        "mechanism": ("OWNER-AUTHORED LEDGER (zoning_signoff_gate.py, the ffe_signoff_gate pattern). "
                      "The owner writes the ledger; this reader only READS it and matches canonical "
                      "keys. There is no --owner-signature: a signature the caller composes at run "
                      "time is authored by the caller, not the owner."),
        "ledger_path": ledger_path,
        "ledger_sha256": sha,
        "sheet": sheet,
        "n_ledger_entries": len(entries or []),
        "edges_bound": bound,
        "orphan_entries": [{"key": entry_key(e), "by": e.get("by"), "date": e.get("date"),
                            "note": e.get("note")} for e in orph],
        "malformed_entries": [{"key": entry_key(e), "by": e.get("by"), "date": e.get("date")}
                              for e in mal],
        "orphans_present": bool(orph),          # CAN be true in a written artefact
        "malformed_present": bool(mal),         # CAN be true in a written artefact
        "residual_trust": ("The ledger is a FILE. This gate proves an edge's canonical key is IN it; "
                           "it does NOT prove a human put it there. That is enforced OUTSIDE this "
                           "process by the PreToolUse guard hooks, which block agent writes to any "
                           "*-signoff.json. A ledger the agent can write is theatre."),
    }


# ---------------------------------------------------------------------------- standalone inspection
def format_report(path, sheet, entries, sha, err):
    out = ["=" * 78,
           "ZONING OWNER-SIGN LEDGER — who signed which semantic line, on which sheet",
           "=" * 78, f"ledger : {path}", f"sha256 : {sha}", f"sheet  : {sheet or '(any)'}"]
    if err:
        out.append(f"ERROR  : {err}")
        return "\n".join(out)
    if not entries:
        out.append("  (EMPTY — nothing is owner-signed. Every virtual edge is agent-provisional.)")
    for e in entries:
        st = sign_status(e)
        scope = "" if not sheet else ("" if entry_sheet(e) == sheet else "   <-- OTHER SHEET")
        out.append(f"  [{st.upper():10}] {entry_key(e)}{scope}")
        out.append(f"               by={e.get('by')!r} date={e.get('date')!r} "
                   f"zone={e.get('zone')!r}")
        if e.get("note"):
            out.append(f"               note={e['note']}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inspect an owner-authored zoning sign-off ledger")
    ap.add_argument("ledger")
    ap.add_argument("--sheet", default=None, help="sheet id to scope orphan detection to")
    a = ap.parse_args(argv)
    entries, sha, err = load_ledger(a.ledger)
    print(format_report(a.ledger, a.sheet, entries, sha, err))
    return 2 if err else 0


if __name__ == "__main__":
    raise SystemExit(main())

# =====================================================================================
# RESIDUAL TRUST — read this before calling any of the above "unforgeable".
# =====================================================================================
# The agent runs with write access to this filesystem. Therefore:
#
#   WHAT IS CLOSED. The signature is no longer authored in argv. A forged --owner-edge whose key is
#   not in the ledger is REFUSED, and re-passing an agent-provisional edge as --owner-edge no longer
#   launders it. The agent's own tool surface (Write / Edit / MultiEdit / Bash / PowerShell) is
#   blocked from mutating *-signoff.json by the PreToolUse guard hooks — the SAME layer that already
#   protects qa/thresholds.yaml and knowledge/codes-th/. That hook fires; see test_guards.sh.
#
#   WHAT IS NOT CLOSED. The hook is an ALLOWLIST-shaped tripwire on tool calls, not a filesystem ACL:
#     * a python SCRIPT (not `python -c`) that the agent writes and then runs can open the ledger
#       'w' — guard_bash inspects the COMMAND STRING, not what the process does;
#     * an MCP/other tool outside the Bash|Write matcher is out of scope;
#     * the ledger's FIRST entry was typed by an agent (me) transcribing the owner's adjudication.
#       Nothing cryptographic distinguishes that transcription from a fabrication.
#   WHAT WOULD ACTUALLY CLOSE IT, in ascending strength:
#     1. Move the ledger OUTSIDE the agent's writable tree (a path the sandbox mounts read-only).
#     2. HASH-CHAIN the entries and keep the head hash somewhere the agent cannot reach (the owner's
#        own notes / a signed commit / a second machine). Then a rewrite is DETECTABLE even if it is
#        not preventable.
#     3. A real signature: the owner signs the entry with a private key the agent never holds
#        (minisign / gpg / an ssh key). Then forgery is not merely detectable, it is infeasible.
#   Until one of those lands, the honest claim is: "the agent cannot forge this WITH ITS TOOLS", not
#   "the agent cannot forge this".
