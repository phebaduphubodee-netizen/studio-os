#!/usr/bin/env python3
"""READ OUR OWN FILES FIRST — the rung that refuses to let this repo go looking
outside for something it has already written down.

OWNER ORDER 2026-08-17: he read the sentence "เราต้องการคนอ่านไฟล์ตัวเอง" in my own
report and answered "แก้ไขเรื่องนี้ซะ". This is that fix. It is a program because a
rule would be dropped — which is the very defect it is about.

THE INSTANCE THAT PRODUCED IT, and it happened the same hour the sentence was
written. He ordered a Deep Research on free asset sources. The DR came back naming
**FurniMesh** — free, commercial use, no attribution, 9,778 curated models in
GLB/OBJ/SKP/BLEND. `docs/LICENSING.md` had already ranked that source **FIRST**,
in these words:

    | **FurniMesh** | ✅ cleanest | ... the ONLY source legal to script-fetch. |

with an explicit automation carve-out ("Exception: FurniMesh may be fetched
directly"), and `furnimesh` is the first token in the permissive-licence set the
build enforces. There is no `furnimesh.py`. Shelf provenance on that day: 166
`trimble-gml` + 26 `3dwarehouse` + 3 `blenderkit` + **0 furnimesh** — the entire
shelf came from the source the same table marks "manual download only; ToS bans
scraping; ~100-dl cap + bans". We paid a subscription to be told what our own
licence table had said for weeks.

AND IT IS NOT THE FIRST TIME. The repo's own CLAUDE.md already carries the
corollary, written after the previous instance: *"our own files pointed at 3D
Warehouse from three directions and none of it was followed. When an outside
answer surprises you, check whether the repo was already implying it."* That was
prose, so nothing consumed it, and the same defect ran again eleven days later.
Sibling instances on file: `judge_lines` named six features and had zero
consumers (R11); `owner_questions_carried_forward` has zero readers;
`floor2-owner-decision-queue.md` went 36 days unopened; the vault audit found
28 of 155 rules NOT APPLIED; `value_probe` can measure a named object in a render
and is called from `rule_gate` zero times.

THE SHAPE, IN ONE LINE:

    A FACT ON DISK WITH NO READER IS NOT KNOWLEDGE. IT IS A COST.

WHAT THIS FILE DECIDES, AND WHAT IT ONLY REPORTS
------------------------------------------------
Two rules BLOCK, because both are grounded in an instance that has already been
paid for, and one line only PRINTS, because nothing here can yet ground a cut on
it. That split is deliberate: this repo has shipped nine scorers whose thresholds
were chosen to be satisfiable, and the honest move for a measurement that cannot
decide is to stop pretending it does.

  RULE 1  NO APPROVED SOURCE GOES UNREAD. Every source `docs/LICENSING.md` marks
          deliverable must either be USED (a fetcher, a shelf entry, or a tier
          row) or be DECLARED UNUSED IN ITS OWN NOTES CELL. Silence is refused.
          The table already contains the passing form, so no migration is
          needed: ambientCG reads "✅ (not yet used) ... **and deliberately not
          written yet**". FurniMesh's cell states a CAPABILITY and never states a
          status, which is exactly how a source stays invisible while being
          ranked first.

  RULE 2  A MONEY ASK MUST NAME WHAT IT READ. Any ask carrying `money: yes` must
          carry `read_first` — repo-relative paths that EXIST, at least one of
          them a source-of-truth file. An ask for money that never opened our own
          licence table is the defect with a price attached: ASK-001 and ASK-002
          asked him to pay for asset shelves while `docs/LICENSING.md` ranked a
          FREE one first, and both were routed to him without that file ever
          being named.

  LINE    REGISTERS WITH NO READER — files under `qa/` that no python file in
          this repo names. Printed, never blocking, because a register written
          for a human to read is legitimate and nothing here can tell that from
          an abandoned queue. It exists because the abandoned kind is on file
          three times over: `judge_lines` (six features, no values, zero
          consumers), `owner_questions_carried_forward` (zero readers), and
          `floor2-owner-decision-queue.md` (36 days unopened).

WHY `read_first` IS NOT SATISFIED BY A GREP THE BUILDER SAYS IT RAN. The paths
are checked for existence, exactly as `decisions_check` checks a `where` and
`asks_check` checks its own — "a decision in force nowhere was never taken", the
same test applied to a search. It cannot prove the file was understood. It can
prove the file was NAMED, and the instance this rung was written from is one
where naming it at all would have been enough.

LAYER LAW: pure Python, no `bpy`, no PIL, no network.
"""

import argparse
import json
import os
import re
import sys

LICENSING_REL = "docs/LICENSING.md"
ASKS_REL = "qa/owner-asks.json"
TIERS_REL = "qa/sourcing-tiers.json"
SHELF_RELS = ("assets/shared/warehouse", "assets/shared")
SCRIPTS_REL = "pipeline/scripts"

# A cell marks the source deliverable. "n/a"/"facts only"/"❌"/"⚠️" do not.
APPROVED = "✅"

# The DECLARED-UNUSED form the table already uses. Kept as markers rather than a
# key so the existing document passes unchanged — a rung that demands a migration
# on the day it lands is a rung that gets reverted.
UNUSED_MARKERS = (
    "not yet used", "not-yet-used", "no fetcher yet", "deliberately not written",
    "not used yet", "unused", "ยังไม่ได้ใช้", "ยังไม่ใช้",
)

# Files that count as OUR OWN ANSWER for rule 2. A `read_first` naming only the
# gate artifact of the round that raised the ask is the builder citing itself.
TRUTH_PREFIXES = ("docs/LICENSING.md", "docs/DECISIONS-", "qa/sourcing-tiers.json",
                  "knowledge/", "docs/strategy.md", "CLAUDE.md", "pipeline/CLAUDE.md")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


# ------------------------------------------------------------------ the table

def parse_sources(text):
    """[{name, deliverable, notes, approved}] from the LICENSING source table.

    Reads the ROW, not the file: a markdown table is the format this document
    already uses and the one a human keeps editing, so the parser bends to the
    document rather than the document to the parser.
    """
    out = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s.startswith("|") or s.startswith("|---") or "|-|" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        name = re.sub(r"[*`]", "", cells[0]).strip()
        if not name or name.lower() == "source":
            continue
        deliverable = cells[1]
        notes = cells[2] if len(cells) > 2 else ""
        out.append({"name": name, "deliverable": deliverable, "notes": notes,
                    "approved": APPROVED in deliverable})
    return out


def _slugs(name):
    """Search tokens for a source name, lowercased and punctuation-free.

    A source is named in prose ("SketchUp 3D Warehouse") and on disk in a slug
    ("3dwarehouse", "trimble-gml"), so matching is on the WORDS, not the string.
    """
    n = name.lower()
    n = n.split("(")[0]
    n = re.sub(r"\bincl\b.*", "", n)
    parts = [p for p in re.split(r"[^a-z0-9]+", n) if len(p) > 2]
    joined = "".join(parts)
    return {p for p in parts if p not in
            ("your", "own", "original", "models", "the", "route", "portal")} | \
           ({joined} if joined else set())


def used_tokens(root):
    """Every lowercase token that shows a source is ACTUALLY REACHABLE FROM CODE
    or is already on the shelf: HOST LITERALS in `pipeline/scripts/*.py`, shelf
    provenance values, and tier ids.

    HOSTS, NOT WORDS — AND THE RUNG LEARNED THIS BY FAILING ITSELF. The first
    version matched file names only, and reported Poly Haven unread because its
    fetcher is called `assets.py` and carries no trace of the source in its name.
    The obvious repair — scan the file CONTENT — made **this module pass its own
    check**, because its docstring says "furnimesh" eleven times. A checker
    satisfied by its own prose is the self-consistency failure R7b already paid
    for, arriving inside the fix written for it.

    So the question the tokens answer is narrowed to the one that cannot be
    satisfied by talking:

        A SOURCE IS READ WHEN SOMETHING HERE CAN REACH IT OR HAS REACHED IT —
        A HOST IN CODE, OR BYTES ON THE SHELF. PROSE THAT NAMES IT IS EXACTLY
        WHAT THIS RUNG EXISTS TO DISTRUST.

    `assets.py` carries `https://api.polyhaven.com`, `warehouse.py` carries
    `https://3dwarehouse.sketchup.com`, and no file anywhere carries a FurniMesh
    host. Not an allowlist (R9b): every source is asked the same question.
    """
    toks = set()
    sdir = os.path.join(root, SCRIPTS_REL)
    for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        if not f.endswith(".py"):
            continue
        try:
            with open(os.path.join(sdir, f), encoding="utf-8",
                      errors="ignore") as fh:
                src = fh.read().lower()
        except OSError:
            continue
        for host in re.findall(r"https?://([a-z0-9.-]+)", src):
            for p in re.split(r"[^a-z0-9]+", host):
                if len(p) > 2:
                    toks.add(p)
            toks.add(re.sub(r"[^a-z0-9]", "", host))
            toks.add(re.sub(r"[^a-z0-9]", "", host.split(".")[0]))
    for rel in SHELF_RELS:
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for cur, _dirs, files in os.walk(base):
            if "SOURCE.json" not in files:
                continue
            try:
                with open(os.path.join(cur, "SOURCE.json"), encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                continue
            for k in ("license_id", "source"):
                v = str(d.get(k) or "").lower()
                for p in re.split(r"[^a-z0-9]+", v):
                    if len(p) > 2:
                        toks.add(p)
                toks.add(re.sub(r"[^a-z0-9]", "", v))
    try:
        with open(os.path.join(root, TIERS_REL), encoding="utf-8") as fh:
            for t in (json.load(fh).get("tiers") or []):
                for p in re.split(r"[^a-z0-9]+", str(t.get("id", "")).lower()):
                    if len(p) > 2:
                        toks.add(p)
    except (OSError, ValueError):
        pass
    return toks


def source_state(src, toks):
    """('used'|'declared-unused'|'SILENT', evidence)."""
    blob = (src["deliverable"] + " " + src["notes"]).lower()
    hit = sorted(_slugs(src["name"]) & toks)
    if hit:
        return "used", ",".join(hit)
    for m in UNUSED_MARKERS:
        if m in blob:
            return "declared-unused", m
    return "SILENT", ""


# ------------------------------------------------------------------ the asks

def money_asks(asks_data):
    rows = (asks_data or {}).get("asks")
    if not isinstance(rows, list):
        return []
    return [a for a in rows if isinstance(a, dict)
            and str(a.get("money", "")).strip().lower().startswith("yes")
            and a.get("status") == "open"]


def read_first_paths(a):
    raw = a.get("read_first")
    if isinstance(raw, list):
        parts = [str(x) for x in raw]
    else:
        parts = str(raw or "").split(",")
    return [p.strip() for p in parts if p.strip()]


# ------------------------------------------------------------------ the line

def unread_registers(root, reg_dir="qa"):
    """[(relpath, reason)] — registers under `qa/` that NO python file names.

    THIS IS THE LINE, AND IT REPLACED A WORSE ONE. The first version counted
    modules nothing imports and returned 54 of them, most legitimately CLI-only
    by design — a number too noisy to prompt anything, which is the definition of
    a metric that cannot decide. The class that actually cost this repo is not an
    unimported module, it is a REGISTER WITH NO READER, and the instances are on
    file: `judge_lines` named six features, stored no values and had zero
    consumers; `owner_questions_carried_forward` in scene-graph.json has zero
    readers; `floor2-owner-decision-queue.md` exists solely to hold five of his
    questions and went 36 days unopened.

    Still a LINE and not a cut: a register can legitimately be written for a
    human to read (a gate artifact is), and nothing here can tell that from an
    abandoned queue. It prints so somebody looks.
    """
    base = os.path.join(root, reg_dir)
    if not os.path.isdir(base):
        return []
    names = []
    for cur, _dirs, files in os.walk(base):
        for f in files:
            if f.endswith((".json", ".md", ".yaml", ".yml")):
                rel = os.path.relpath(os.path.join(cur, f), root).replace("\\", "/")
                names.append((rel, f))
    body = []
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in
                   (".git", "assets", "_private", "node_modules", "__pycache__")
                   and not d.startswith(".")]
        for f in files:
            if f.endswith(".py"):
                try:
                    with open(os.path.join(cur, f), encoding="utf-8",
                              errors="ignore") as fh:
                        body.append(fh.read())
                except OSError:
                    pass
    blob = chr(10).join(body)
    out = []
    for rel, f in sorted(names):
        if rel not in blob and f not in blob:
            out.append((rel, "no .py in this repo names it"))
    return out


# ------------------------------------------------------------------ the rules

def check(licensing_text, asks_data, root=None, path_hint=LICENSING_REL):
    """Violations. Every one is on the builder's side."""
    root = root or _repo_root()
    v = []

    if licensing_text is None:
        return [f"no readable source table at {path_hint}. Without it, "
                f"'we searched' is unfalsifiable — and the instance this rung "
                f"exists for is a FREE source that table ranked first while the "
                f"whole shelf came from somewhere else."]

    toks = used_tokens(root)
    for src in parse_sources(licensing_text):
        if not src["approved"]:
            continue
        state, _ev = source_state(src, toks)
        if state == "SILENT":
            v.append(
                f"{path_hint} marks '{src['name']}' DELIVERABLE and nothing in "
                f"this repo consumes it — no fetcher, no shelf entry, no tier "
                f"row — and its own Notes cell never says it is unused. A source "
                f"our licence table approved and nobody read is how FurniMesh "
                f"stayed invisible while ranked FIRST, until a paid Deep "
                f"Research told us about it. Either wire it, or write the reason "
                f"in its Notes cell the way ambientCG's does.")

    for a in money_asks(asks_data):
        aid = a.get("id") or "<no id>"
        paths = read_first_paths(a)
        if not paths:
            v.append(
                f"{aid} asks him for MONEY and carries no `read_first`, so "
                f"nothing records which of OUR OWN files were opened before the "
                f"ask was routed. ASK-001 and ASK-002 asked him to pay for asset "
                f"shelves while docs/LICENSING.md ranked a FREE one first, and "
                f"neither ever named that file.")
            continue
        for rel in paths:
            if not os.path.exists(os.path.join(root, rel)):
                v.append(f"{aid}: `read_first` names {rel}, which does not "
                         f"exist. A file that was not read cannot have been "
                         f"read first — the same test a decision's `where` gets.")
        if not any(p.startswith(TRUTH_PREFIXES) for p in paths):
            v.append(
                f"{aid}: `read_first` names only {', '.join(paths)} — none of "
                f"them a source-of-truth file ({', '.join(TRUTH_PREFIXES[:3])}, "
                f"knowledge/…). Citing the gate artifact of the round that "
                f"raised the ask is the builder citing itself, which is the "
                f"self-consistency failure R7b already paid for.")
    return v


def report(licensing_text, root=None):
    """[(name, state, evidence)] for every approved source — pass or fail. A gate
    that only speaks when it fails teaches nobody what it measures."""
    root = root or _repo_root()
    toks = used_tokens(root)
    return [(s["name"],) + source_state(s, toks)
            for s in parse_sources(licensing_text) if s["approved"]]


def load_text(rel, root=None):
    try:
        with open(os.path.join(root or _repo_root(), rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def load_json(rel, root=None):
    try:
        with open(os.path.join(root or _repo_root(), rel), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(
        description="Did we read our own files before looking outside? Exits 1 "
                    "when an approved source has no reader or a money ask never "
                    "opened one.")
    ap.add_argument("--licensing", default=None)
    ap.add_argument("--asks", default=None)
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                   # pragma: no cover
        pass

    root = _repo_root()
    text = load_text(a.licensing or LICENSING_REL, root)
    asks = load_json(a.asks or ASKS_REL, root)

    print("READ OUR OWN FILES FIRST — approved sources and who reads them:")
    for name, state, ev in report(text, root):
        mark = {"used": "  used", "declared-unused": "  unused (declared)"}.get(
            state, "  !! SILENT")
        print(f"{mark:<22} {name}" + (f"   [{ev}]" if ev else ""))

    unread = unread_registers(root)
    print("")
    print(f"REGISTERS WITH NO READER (reported, not a cut — a register written "
          f"for a human is legitimate): {len(unread)} file(s) under qa/ that no "
          f".py in this repo names")
    for rel, _why in unread[:12]:
        print(f"  {rel}")
    if len(unread) > 12:
        print(f"  … and {len(unread) - 12} more")

    v = check(text, asks, root, a.licensing or LICENSING_REL)
    for s in v:
        print(f"\n  !! {s}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
