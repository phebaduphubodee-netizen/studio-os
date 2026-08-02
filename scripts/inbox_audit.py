#!/usr/bin/env python3
"""inbox_audit.py — measure which staged knowledge units actually LANDED in knowledge/.

    python scripts/inbox_audit.py            # the debt report
    python scripts/inbox_audit.py --all      # don't cap the ranked table
    python scripts/inbox_audit.py --json     # machine-readable

WHAT THIS REPLACES, AND WHY (2026-07-13 rewrite — read before "simplifying" it back)
-----------------------------------------------------------------------------------
The old version walked knowledge/_inbox and printed `640 file(s) staged, oldest 2475d`.
Every part of that headline was wrong in a way that made it useless:

  * IT COUNTED FILES, NOT KNOWLEDGE. 508 of those 640 are attachment binaries (png/jpg/
    ies/rar) hanging off Discord threads, most of them gitignored. The instrument was
    reporting a JPEG of a curtain as distillation debt.
  * IT COUNTED PROVENANCE AS DEBT. The three primary statutory PDFs under codes-th-sources/
    are the citation anchor for the codes-th Authority tier. They can never be "distilled
    away". They inflated the number forever.
  * ITS AGE WAS A FICTION. `oldest 2475d` was an .IES file whose mtime (2019-10-02) is the
    timestamp the light manufacturer stamped inside a ZIP. git first saw it 2026-07-03.
    The headline age was wrong by ~225x, so every "aging" flag it printed was noise.
  * IT NEVER OPENED THE LEDGER AND NEVER OPENED THE SUCCESSORS. It could not tell a
    distilled unit from an untouched one. The number could only go up — and a number that
    can only go up gets ignored, which is exactly what happened for 11 days.
  * ITS SECOND METRIC WAS SATURATED. "promoted dir(s) still empty" reads 0 permanently:
    one stub .md makes a dir green forever, and a dir being non-empty says nothing about
    whether any staged VALUE landed in it.
  * IT LISTED codes-th AS A DISTILLATION DESTINATION — inviting precisely what house law
    forbids (a DR/NLM answer becoming a statutory value).

The rewrite measures instead of asserting. The core anti-flattering check is L4/PIN-MISS:
a ledger row may claim DISTILLED only if the distinctive strings it names as pins are
actually GREPPABLE in the successor it names. A successor that mentions the topic but
dropped the values fails L4 and is downgraded to PARTIAL. Backlinks and ledger rows are
NECESSARY but NOT SUFFICIENT — that is the whole lesson of the 2026-07-03 corpus run,
whose 11 authored files all passed "the ledger says so" and 10/10 failed verification.

DOCTRINE PRESERVED FROM v1: this prints the debt; a HUMAN decides. It is not a gate on
the debt count. It exits 1 only on integrity failures (a lie in the bookkeeping), never
merely because debt exists.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover - older interpreters
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_REL = "knowledge/_inbox"
INBOX = os.path.join(ROOT, "knowledge", "_inbox")
LEDGER_REL = "knowledge/_inbox/DISTILLATION-LEDGER.md"

# Dirs a staged unit may legitimately be promoted INTO. codes-th is deliberately absent:
# it is Authority tier, hook-blocked, and enters only by reviewed PR from a primary legal
# source. Listing it here would invite a DR-sourced statutory value, which is forbidden.
DESTINATIONS = ["ergonomics", "lighting", "materials", "styles", "classifications",
                "brand-standards", "rendering", "programming", "studio-vault"]
FORBIDDEN_SUCCESSOR_PREFIX = "knowledge/codes-th/"

# Where a promotion may also legitimately land (a build law belongs in the pipeline's
# instructions, a business thesis in the why-decisions doc — neither is domain truth).
NON_KNOWLEDGE_SUCCESSOR_DIRS = ("docs/", "pipeline/", ".claude/")

AGING_DAYS = 14

# --- PROVENANCE-KEEP: a HARD-CODED allowlist, never a tag in the data. -------------------
# The threat this defends against: a future run tags its own debt "provenance" and walks
# away. There is no `provenance: true` frontmatter, no marker file, and no ledger field
# that can grant this class. The only way to add one is to edit THIS list, which shows up
# in a diff. Provenance is per-FILE; you cannot mark a directory provenance.
PROVENANCE_PATTERNS = [
    re.compile(r"^knowledge/_inbox/codes-th-sources/[^/]+\.pdf$"),      # primary statutory PDFs
    re.compile(r"^knowledge/_inbox/.*qa-history\.json$"),               # NLM turn transcripts
    re.compile(r"^knowledge/_inbox/nlm-design-systems/sources-manifest\.md$"),
]
# RAISED 9 -> 16 on 2026-08-01, deliberately, which is the only way this number may move.
# The freeze was "3 codes-th PDFs + 5 qa-history.json + 1 sources-manifest". Seven more
# qa-history.json have landed since, and each is a real NLM/DR turn transcript staged by
# the documented flow (CLAUDE.md: an answer is staged "with notebook/turn attribution AND a
# refreshed qa-history.json in the same commit") — not debt wearing a provenance tag:
#   interior-render-critique-DR-2026-07-15 · nlm-element1-curtain-2026-07-16 ·
#   nlm-element1-dressing-wall-2026-07-16 · nlm-backlit-stone · nlm-cloth-closedtube ·
#   nlm-process-rules · nlm-veneer-figure
# Three of those seven are ALSO reported as PROVENANCE-ORPHAN, and that is the honest
# outcome, not a contradiction: being a genuine primary source and being uncited are
# different facts, and this constant answers only the first.
EXPECTED_PROVENANCE = 16

# INFRA is pinned by FULL PATH (review 2026-07-13: a basename match let any stash hide a
# staged file by naming it `nlm-queue.md` / `_index.md`). Only .gitkeep stays name-matched —
# an empty-dir marker is infra wherever it sits and can carry no knowledge.
INFRA_PATHS = {
    "knowledge/_inbox/DISTILLATION-LEDGER.md",
    "knowledge/_inbox/nlm-queue.md",
    "knowledge/_inbox/discord/MY-DATA-PEAT/EXTERNAL-LINKS.md",
    "knowledge/_inbox/discord/MY-DATA-PEAT/_index.md",
}

# '' (extensionless) is deliberately NOT here: an extensionless file outside a discord
# payload dir must land in UNCLASSIFIED and fail loudly, not vanish as an "attachment"
# (review 2026-07-13 — the two extensionless Thai CDN files live under files/ and are
# caught by the payload-dir rule before extensions are ever consulted).
ATTACHMENT_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".rar", ".zip", ".ies",
                   ".xlsx", ".xls", ".skp", ".mp4", ".dwg", ".max", ".psd"}

# OWED is not a synonym for UNTOUCHED and the difference is the point:
#   UNTOUCHED = nobody has even looked at this unit.
#   OWED      = somebody looked, found real value, and nobody has promoted it yet.
# Collapsing the two would let a considered decision and a blind spot read the same.
VERDICTS = {"DISTILLED", "PARTIAL", "DROPPED", "OWED", "PROVENANCE-KEEP"}

# A ledger row may claim PROVENANCE-KEEP only for units on THIS list (review 2026-07-13:
# without it, the verdict was an unchecked one-line debt-exit — ':: PROVENANCE-KEEP :: -'
# moved any unit out of every band, precisely the tag-your-way-out the file-level
# allowlist doctrine forbids). Adding a unit here is a code edit that shows in a diff.
LEDGER_PROVENANCE_UNITS = {
    # raw engine output kept as the audit anchor for a correction table that overturned
    # 4 of its license verdicts (docs/strategy.md cites it as "[G] — never cite directly")
    "knowledge/_inbox/interior-ai/2026-07-01-plan-read-write-tools-gemini-DR.md",
    # fabrication-flagged DR (docs/DECISIONS-render-assets.md, the 2026-07-01
    # furniture-pack entry: "DR fabricates these; real money at stake") kept only as
    # the evidence trail for that refutation — its factual content must stay unpromoted.
    # Cited by DATE, not by line: that file is a newest-first log, so a new decision at
    # the top shifts every line citation into it (2026-08-01 moved this one by 55).
    "knowledge/_inbox/interior-ai/2026-07-01-asset-sourcing-DR.md",
}

# Mechanical floor under pin quality (review 2026-07-13: three stopwords passed as a
# DISTILLED proof). Not a semantic judge — just a floor that makes vacuous pins loud.
PIN_STOPWORDS = {"the", "and", "design", "interior", "thai", "mm", "cm", "m", "wood",
                 "wall", "floor", "room", "file", "image", "png", "pdf", "reference",
                 "content", "channel", "discord", "knowledge"}
# 2, not 3: 'R9' (CRI red index) and 'EQ' (dimension-string token) are real, distinctive
# values from the corpus — the stopword list, not raw length, is what blocks topic words.
PIN_MIN_LEN = 2


# ---------------------------------------------------------------- classification --------
def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def classify(path_rel):
    """Every staged file gets exactly one class. UNCLASSIFIED is a LOUD FAIL, by design:
    a stash the classifier does not recognise must not silently vanish from the debt."""
    name = os.path.basename(path_rel)
    ext = os.path.splitext(name)[1].lower()

    for pat in PROVENANCE_PATTERNS:
        if pat.match(path_rel):
            return "PROVENANCE-KEEP"
    if path_rel in INFRA_PATHS or name == ".gitkeep":
        return "INFRA"

    # discord: a thread dir is the unit; everything else under it is payload
    if "/discord/" in path_rel:
        if "/files/" in path_rel or "/_external-fetched/" in path_rel:
            return "ATTACHMENT"
        if name == "thread.md":
            return "UNIT-ANCHOR"
        if name == "raw.json":
            return "ATTACHMENT"
        return "UNCLASSIFIED"

    if path_rel.startswith("knowledge/_inbox/id-project-corpus/") and ext == ".pdf":
        return "UNIT-ANCHOR"
    if path_rel.startswith("knowledge/_inbox/interior-ai/") and ext == ".md":
        return "UNIT-ANCHOR"
    # ANY nlm-<topic>/ directory, not just nlm-design-systems (fixed 2026-08-01). The NLM
    # lane in CLAUDE.md creates one directory per ask — nlm-veneer-figure, nlm-backlit-stone,
    # nlm-cloth-closedtube, nlm-process-rules — all with the same shape: the answer .md plus a
    # qa-history.json anchor. Only the FIRST such directory was ever named here, so four
    # lanes' worth of staged answers were landing in UNCLASSIFIED and taking their
    # qa-history.json siblings down with them as PROVENANCE-ORPHANs: eight of the eleven
    # integrity failures were this one missing generalisation. A classifier that recognises
    # one instance of a pattern and not the pattern is the same defect as a rule written for
    # one input and never applied to the next.
    if re.match(r"^knowledge/_inbox/nlm-[^/]+/[^/]+\.md$", path_rel):
        return "UNIT-ANCHOR"
    # loose staged answers at the _inbox root
    if re.match(r"^knowledge/_inbox/[^/]+\.md$", path_rel):
        return "UNIT-ANCHOR"

    if ext in ATTACHMENT_EXTS:
        return "ATTACHMENT"
    return "UNCLASSIFIED"


def unit_id(anchor_rel):
    """The unit's identity. For a discord thread it is the DIRECTORY (the thread), because
    the thread — not the file — is the thing you distill or drop."""
    if anchor_rel.endswith("/thread.md"):
        return anchor_rel[: -len("/thread.md")]
    return anchor_rel


def scan():
    """Classify every staged file and derive the unit set. Also detects ORPHANED-PAYLOAD:
    a discord thread dir holding raw.json / files/ payload but NO thread.md anchor. Without
    this, deleting one thread.md (or an ingest bug that never writes it) made the whole
    thread — payload and all — vanish from the debt as 'attachments, never debt'
    (review 2026-07-13, reproduced live)."""
    classes, units, orphans = {}, {}, set()
    payload_dirs = set()
    for dirpath, _, files in os.walk(INBOX):
        for f in files:
            r = rel(os.path.join(dirpath, f))
            k = classify(r)
            classes.setdefault(k, []).append(r)
            if k == "UNIT-ANCHOR":
                units[unit_id(r)] = r
            if "/discord/" in r and "/_external-fetched/" not in r:
                # the thread dir owning this payload: .../<category>/<NNN_thread>/(files/)?x
                m = re.match(r"^(.*?/discord/[^/]+/[^/]+/[^/]+)/", r)
                if m and (f == "raw.json" or "/files/" in r):
                    payload_dirs.add(m.group(1))
    for d in payload_dirs:
        if d not in units:
            orphans.add(d)
    return classes, units, sorted(orphans)


# ---------------------------------------------------------------- git ages ---------------
def git_add_dates():
    """Age is measured from the GIT FIRST-ADD date, never from mtime (see the docstring:
    mtime made the old instrument report a 2019-stamped vendor .IES as 6.8-year-old debt)."""
    try:
        # -c core.quotepath=false: without it git octal-quotes every non-ASCII path in
        # --name-only output ("\340\270\225..."), so all 43 Thai-named anchors miss the
        # dates dict and silently read UNCOMMITTED — measured live 2026-07-13.
        # No -M: with rename detection, --diff-filter=A drops the add-record of a renamed
        # file entirely and its age becomes permanently unmeasurable; without it a rename
        # merely RESETS the age (a new add-record) — a measurable value beats a lost one.
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "log", "--diff-filter=A",
             "--format=C|%at", "--name-only", "--", INBOX_REL],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        ).stdout
    except Exception:
        return {}
    dates, ts = {}, None
    for line in out.splitlines():
        if line.startswith("C|"):
            ts = int(line[2:])
        elif line.strip() and ts is not None:
            p = line.strip()
            # keep the EARLIEST add for a path (git log is newest-first)
            dates[p] = ts if p not in dates else min(dates[p], ts)
    return dates


def age_days(anchor_rel, dates, now):
    ts = dates.get(anchor_rel)
    if ts is None:
        return None  # untracked: staged knowledge that is not even in the repo
    return (now - datetime.datetime.fromtimestamp(ts)).days


# ---------------------------------------------------------------- backlinks --------------
# The bare-token branch must ADMIT ')' — staged dirs are named things like
# `012_ระแนงสำเร็จรูป-(Wall)` — and normalize_citation() then strips only the trailing
# closers that have no matching opener (the standard URL-in-prose trick). Excluding ')'
# from the token class truncated that path at '(Wall' and manufactured a fake dangle.
CITE_RE = re.compile(r"`(knowledge/_inbox/[^`]+)`|(?<![`\w])(knowledge/_inbox/[^\s`,;\"']+)")
# a citation may legitimately carry a line/page suffix (`…/foo.md:21-30`) and, inside
# backticks, may be WRAPPED across markdown lines. Both are citations, not dangles.
LINE_SUFFIX_RE = re.compile(r":\d+(?:[-–]\d+)?$")


def normalize_citation(p):
    """Reduce a cited token to the PATH it names, or None if it is not a checkable path.

    Three shapes bit the first cut of this checker, and each would have printed a loud
    failure at an innocent file — an instrument that cries wolf gets muted, which is how
    the old one died:
      * `foo.md:21-30`  — a line-range citation. The path is foo.md.
      * a backticked path WRAPPED across two markdown lines (staged filenames contain
        spaces: 'Automated Vision QA for Interiors.pdf'). Collapse the whitespace.
      * an ABBREVIATED path ('catalogue/001_…') — a human shorthand, not a claim about a
        file. Not checkable; skip it rather than fake a failure.
    """
    # a wrapped citation inside a markdown blockquote carries the "> " of the next line
    p = re.sub(r"\s*\n\s*>?\s*", " ", p)
    p = re.sub(r"\s+", " ", p).strip().rstrip(".,;:")
    # strip only UNBALANCED trailing closers: "(see knowledge/_inbox/foo)" sheds its ')',
    # but "…/012_ระแนงสำเร็จรูป-(Wall)" keeps its own — the paren is part of the dir name
    while p and p[-1] in ")]":
        opener = "(" if p[-1] == ")" else "["
        if p.count(opener) < p.count(p[-1]):
            p = p[:-1].rstrip(".,;:")
        else:
            break
    if "…" in p or "..." in p or "*" in p:
        return None
    p = LINE_SUFFIX_RE.sub("", p)
    return p or None


def promoted_files():
    """Files that may CLAIM a staged unit as a source: the promoted knowledge tier, plus the
    two legitimate non-knowledge homes (docs/, pipeline/). knowledge/_inbox itself excluded —
    staging citing staging proves nothing."""
    out = []
    for base in ["knowledge", "docs", "pipeline"]:
        for dp, dns, fs in os.walk(os.path.join(ROOT, base)):
            dns[:] = [d for d in dns if d not in ("_inbox", "__pycache__", ".git")]
            for f in fs:
                if f.endswith((".md", ".json", ".py")):
                    out.append(rel(os.path.join(dp, f)))
    return out


def backlink_map(files):
    """staged-path -> [citing files]. Backtick-quoted paths are matched greedily inside the
    backticks: staged filenames contain SPACES ('Interior Design Knowledge Structuring.pdf')
    and Thai characters, and a naive \\S+ regex truncates at the space and manufactures a
    fake dangling citation."""
    m = {}
    for f in files:
        try:
            txt = open(os.path.join(ROOT, f), encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for a, b in CITE_RE.findall(txt):
            p = normalize_citation(a or b)
            if p:
                m.setdefault(p, []).append(f)
    return m


# ---------------------------------------------------------------- the ledger -------------
LEDGER_BLOCK = re.compile(r"```ledger\n(.*?)```", re.S)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def _cites_unit(cited_path, unit):
    """`.../001_Tile` must not be credited with citations of `.../001_Tile-v2` — the match
    is exact, or a path strictly beneath the unit dir."""
    return cited_path == unit or cited_path.startswith(unit + "/")


def parse_ledger():
    """The ledger must SPEAK IN PATHS or it cannot be checked.

    Machine-readable rows live in a fenced ```ledger block, one row per staged unit:

        <unit path> :: <verdict> :: <successor path | -> :: <pin ;; pin ;; pin> :: <rationale>

    `::` is the field separator because staged paths contain spaces AND Thai text; `;;`
    separates pins. A PIN is a distinctive literal string from the staged unit (a number, a
    rule name, a table row) — never a topic word. Pins are what make DISTILLED a measurement
    instead of an assertion.
    """
    p = os.path.join(ROOT, LEDGER_REL)
    if not os.path.exists(p):
        return [], "MISSING"
    txt = open(p, encoding="utf-8", errors="replace").read()
    blocks = LEDGER_BLOCK.findall(txt)
    if not blocks:
        return [], "NOT-MACHINE-READABLE"
    rows = []
    for blk in blocks:
        for line in blk.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # maxsplit=4: a rationale legitimately containing '::' must not shift fields
            parts = [x.strip() for x in line.split("::", 4)]
            if len(parts) < 5:
                rows.append({"raw": line, "malformed": True})
                continue
            rows.append({
                "unit": parts[0], "verdict": parts[1].upper(),
                "successor": [s.strip() for s in parts[2].split(";;") if s.strip() and s.strip() != "-"],
                "pins": [s.strip() for s in parts[3].split(";;") if s.strip() and s.strip() != "-"],
                "rationale": parts[4], "malformed": False,
            })
    return rows, "OK"


def _read(p):
    try:
        return open(os.path.join(ROOT, p), encoding="utf-8", errors="replace").read()
    except Exception:
        return None


def provenance_is_anchored(f, blinks):
    """A provenance file earns its keep by being the citation anchor for something. A raw NLM
    turn transcript (`X-qa-history.json`) anchors the ANSWER it was produced with (`X.md`) —
    promoted files cite the answer, not the transcript. Counting the transcript as an orphan
    because nobody links the JSON directly would be the checker being pedantic instead of
    right. So: a qa-history is anchored iff its sibling answer is cited."""
    if blinks.get(f):
        return True
    if f.endswith("qa-history.json"):
        sib = f.replace("-qa-history.json", ".md")
        if blinks.get(sib):
            return True
        # nlm-design-systems/qa-history.json anchors every answer in its own dir
        d = os.path.dirname(f) + "/"
        if any(p.startswith(d) and p != f and cs for p, cs in blinks.items()):
            return True
    return False


def check_ledger(rows, units, blinks):
    """The six mechanical checks. Each is a LOUD FAIL — the ledger is bookkeeping, and wrong
    bookkeeping is worse than none because it buys unearned confidence."""
    fails, banded = [], {}
    seen = set()
    for r in rows:
        if r.get("malformed"):
            fails.append(("LEDGER-MALFORMED", r["raw"][:100], "row needs 5 `::`-separated fields"))
            continue
        u = r["unit"]
        # a later row must never silently overwrite an earlier verdict — an appended
        # flattering row cancelling an honest OWED is exactly a lie in the bookkeeping
        if u in seen:
            fails.append(("LEDGER-DUPLICATE", u,
                          "two rows grade the same unit — the later one would silently win"))
            continue
        seen.add(u)
        if r["verdict"] not in VERDICTS:
            fails.append(("LEDGER-BAD-VERDICT", u, f"{r['verdict']} not in {sorted(VERDICTS)}"))
            continue
        # L1 — grading a file that is not there
        if u not in units and not os.path.exists(os.path.join(ROOT, u)):
            fails.append(("LEDGER-GHOST", u, "ledger row for a unit that does not exist on disk"))
            continue
        # a row keyed at .../thread.md instead of the thread DIR exists on disk but grades
        # nothing — the real unit would silently read UNTOUCHED (review 2026-07-13)
        if u not in units:
            fails.append(("LEDGER-NOT-A-UNIT", u,
                          "path exists but is not a unit id (a discord unit is the thread "
                          "DIRECTORY, not thread.md; attachments are never units)"))
            continue
        if r["verdict"] in ("DROPPED", "OWED"):
            rat = r["rationale"]
            if not rat or rat == "-":
                fails.append((f"{r['verdict']}-WITHOUT-RATIONALE", u,
                              "a conscious drop must say what was checked; a declared debt must "
                              "say what is owed and where it goes"))
            elif len(rat) < 40:
                fails.append(("THIN-RATIONALE", u,
                              f"{r['verdict']} rationale is {len(rat)} chars — 'junk' is not "
                              f"'what was checked'; name the payload and the check"))
            banded[u] = r["verdict"]
            continue
        if r["verdict"] == "PROVENANCE-KEEP":
            # NOT a free exit: the verdict is honoured only for units on the hard-coded
            # allowlist. Anything else claiming it is precisely the tag-your-way-out-of-debt
            # move the file-level PROVENANCE doctrine forbids.
            if u not in LEDGER_PROVENANCE_UNITS:
                fails.append(("PROVENANCE-UNGRANTED", u,
                              "PROVENANCE-KEEP is granted by LEDGER_PROVENANCE_UNITS in "
                              "inbox_audit.py (a code edit that shows in a diff), never by "
                              "a ledger row"))
                banded[u] = "PARTIAL"
                continue
            if not r["rationale"] or r["rationale"] == "-":
                fails.append(("PROVENANCE-WITHOUT-RATIONALE", u,
                              "say what this file anchors and why it stays"))
            banded[u] = "PROVENANCE-KEEP"
            continue
        # DISTILLED / PARTIAL must name a successor and pins
        if not r["successor"]:
            fails.append(("LEDGER-NO-SUCCESSOR", u, f"{r['verdict']} needs >=1 successor path"))
            continue
        ok = True
        for s in r["successor"]:
            # L6 — the authority violation the old instrument's TARGETS list invited
            if s.startswith(FORBIDDEN_SUCCESSOR_PREFIX):
                fails.append(("AUTHORITY-VIOLATION", u,
                              f"successor {s} is codes-th (Authority tier: PR-only, primary legal source only)"))
                ok = False
                continue
            # a successor must live in a legitimate promotion home. Staging citing staging
            # proves nothing, a scratch/script file is not a promotion, and '..' or an
            # absolute path escapes the repo (review 2026-07-13: none of this was checked)
            legit = (s.startswith("knowledge/") and not s.startswith("knowledge/_inbox/")) or \
                    s.startswith(NON_KNOWLEDGE_SUCCESSOR_DIRS)
            if os.path.isabs(s) or ".." in s.split("/") or not legit:
                fails.append(("ILLEGAL-SUCCESSOR", u,
                              f"{s} is not a promotion home (knowledge/ minus _inbox, or "
                              f"{'/'.join(d.rstrip('/') for d in NON_KNOWLEDGE_SUCCESSOR_DIRS)})"))
                ok = False
                continue
            body = _read(s)
            # L2 — a successor that does not exist
            if body is None:
                fails.append(("DANGLING-SUCCESSOR", u, f"successor does not exist: {s}"))
                ok = False
                continue
            # HTML comments are invisible in rendered markdown — a citation or pin hidden
            # there satisfies nothing a reader can see, so it satisfies nothing here either
            body = HTML_COMMENT_RE.sub("", body)
            # L3 — a successor that does not claim the unit. Kills "point at a topically
            # similar file": the link must be bidirectional.
            if u not in body:
                fails.append(("UNCITED-SUCCESSOR", u,
                              f"{s} does not cite `{u}` — the backlink must be bidirectional"))
                ok = False
        if r["verdict"] == "DISTILLED" and len(r["pins"]) < 3:
            fails.append(("LEDGER-THIN-PINS", u, f"DISTILLED needs >=3 pins, has {len(r['pins'])}"))
            ok = False
        # a floor under pin quality: three stopwords must never constitute a DISTILLED proof
        for pin in r["pins"]:
            if len(pin) < PIN_MIN_LEN or pin.lower() in PIN_STOPWORDS:
                fails.append(("GENERIC-PIN", u,
                              f"pin {pin!r} is a stopword/too short — a pin is a distinctive "
                              f"literal value, never a topic word"))
                ok = False
        # L4 — THE ANTI-FLATTERING CORE. A pin that is not greppable in the successor means
        # the value did not land, whatever the ledger says. Matching is CASE-INSENSITIVE —
        # "Linear Workflow" landing as "linear workflow" is presentation, not content — but
        # nothing looser: a value reformatted into a band ("2200K" → "2200–3000 K") is a
        # transformation and stays a miss.
        # a pin need only land in ONE named successor
        landed = set()
        for s in r["successor"]:
            body = HTML_COMMENT_RE.sub("", _read(s) or "").lower()
            for pin in r["pins"]:
                if pin.lower() in body:
                    landed.add(pin)
        missing_pins = [p for p in r["pins"] if p not in landed]
        if missing_pins:
            for p in missing_pins:
                fails.append(("PIN-MISS", u, f"pin not found in any named successor: {p!r}"))
            ok = False
        banded[u] = r["verdict"] if ok else "PARTIAL"
    # L5 — a unit on disk that nobody has even written a row for
    for u in units:
        if u not in seen:
            band = "LEDGER-GAP" if any(_cites_unit(b, u) for b in blinks) else "UNTOUCHED"
            banded[u] = band
    return fails, banded


def _ever_existed(p):
    """Did this path exist in ANY commit? Unknown (no git, no answer) reads as True, so a
    missing discriminator makes the audit report MORE, never less — a debt instrument must
    not go quiet when it loses a sense."""
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "log", "--all", "--oneline",
             "--diff-filter=A", "--", p],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
    except Exception:                                   # noqa: BLE001
        return True
    if out.returncode != 0:
        return True
    return bool(out.stdout.strip())


def check_antecedents(blinks):
    """R1 — every knowledge/_inbox path a PROMOTED file cites must exist. This is the check
    that caught two live rots the old ledger declared closed: it had grepped pipeline source
    only, and the dead `_inbox/interior-ai/research/...` paths were sitting in the very
    knowledge files it was bragging about.

    A CITATION IS NOT THE ONLY REASON A PATH APPEARS IN A FILE (fixed 2026-08-01). This check
    convicted `knowledge/_inbox/sheets`, cited by `pipeline/scripts/test_look_bench.py` — and
    that file names the path in a list of destinations look_bench must REFUSE to write to. It
    is a counter-example, the opposite of a citation, and the check could not tell the two
    apart. Same family as a metric that cannot separate two things it was trusted to separate.

    The discriminator is git history, and it is the check's own definition made honest: a
    DANGLING antecedent means a citation that ROTTED — the unit was there and went away. A
    path that has never existed in any commit was never a unit, so nothing rotted; it is a
    string someone wrote. Only the first is debt."""
    out = []
    for p, citers in sorted(blinks.items()):
        if os.path.exists(os.path.join(ROOT, p)):
            continue
        if not _ever_existed(p):
            continue                                    # fictional example, never a unit
        out.append(("DANGLING-ANTECEDENT", p, "cited by " + ", ".join(sorted(set(citers))[:3])))
    return out


# ---------------------------------------------------------------- report -----------------
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="do not cap the ranked debt table")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.datetime.now()

    classes, units, orphans = scan()
    n_files = sum(len(v) for v in classes.values())
    prov = classes.get("PROVENANCE-KEEP", [])
    unclassified = classes.get("UNCLASSIFIED", [])

    dates = git_add_dates()
    files = promoted_files()
    blinks = backlink_map(files)
    rows, ledger_state = parse_ledger()
    fails, banded = check_ledger(rows, units, blinks)
    fails += check_antecedents(blinks)

    # frozen constant: the provenance set cannot grow quietly
    if len(prov) != EXPECTED_PROVENANCE:
        fails.append(("PROVENANCE-DRIFT", f"{len(prov)} files",
                      f"expected {EXPECTED_PROVENANCE}; provenance is a hard-coded allowlist — "
                      f"if this is a real new primary source, edit PROVENANCE_PATTERNS deliberately"))
    for f in prov:
        if not provenance_is_anchored(f, blinks):
            fails.append(("PROVENANCE-ORPHAN", f, "nothing cites it, and nothing cites the answer it "
                                                  "anchors — an anchor nobody drops is not an anchor"))
    for u in unclassified:
        fails.append(("UNCLASSIFIED", u, "the classifier does not recognise this file — a new stash "
                                          "cannot make debt disappear by being unrecognised"))
    for o in orphans:
        fails.append(("ORPHANED-PAYLOAD", o,
                      "a discord thread dir with payload but NO thread.md anchor — its whole "
                      "content would silently vanish from the debt as 'attachments'"))
    if ledger_state != "OK":
        fails.append(("LEDGER-NOT-MACHINE-READABLE",
                      f"{len(rows)}/{len(units)} rows parsed",
                      "the ledger has no ```ledger block: every unit counts as UNLEDGERED"))

    bands = {}
    for u in units:
        bands.setdefault(banded.get(u, "UNTOUCHED"), []).append(u)

    # the aging advisory is part of the exit-code contract in BOTH output modes —
    # a scripted consumer must see the same 0/1/2 a human does
    aging = [u for u in bands.get("UNTOUCHED", [])
             if (age_days(units[u], dates, now) or 0) >= AGING_DAYS]
    exit_code = 1 if fails else (2 if aging else 0)

    if a.json:
        print(json.dumps({
            "units": {u: {"band": banded.get(u, "UNTOUCHED"),
                          "age_days": age_days(units[u], dates, now),
                          "backlinked": any(_cites_unit(b, u) for b in blinks)}
                      for u in sorted(units)},
            "classes": {k: len(v) for k, v in sorted(classes.items())},
            "failures": [{"kind": k, "where": w, "detail": d} for k, w, d in fails],
            "aging_untouched": sorted(aging),
            "exit_code": exit_code,
        }, ensure_ascii=False, indent=1))
        return exit_code

    n_units = len(units)
    n_back = len([u for u in units if any(_cites_unit(b, u) for b in blinks)])
    ages = [age_days(units[u], dates, now) for u in bands.get("UNTOUCHED", [])]
    ages = [x for x in ages if x is not None]
    oldest_untouched = max(ages) if ages else 0

    print("=== knowledge/_inbox distillation debt ===")
    print(f"  {n_units} knowledge units staged | {n_back} backlinked | "
          f"{len(bands.get('UNTOUCHED', []))} UNTOUCHED | oldest untouched {oldest_untouched}d (git-add)")
    print(f"  ({n_files} files on disk = {n_units} unit anchors + "
          f"{len(classes.get('ATTACHMENT', []))} attachments + {len(prov)} provenance + "
          f"{len(classes.get('INFRA', []))} infra — attachments are NEVER debt)")
    print("  age = git first-add date. mtime is NOT used: the mtime-oldest file is a 2019-stamped")
    print("  vendor .IES inside a downloaded ZIP, which this repo first saw 2026-07-03.")

    if fails:
        print("\n=== LOUD FAILURES (integrity of the bookkeeping — fix before trusting any band) ===")
        for k, w, d in fails:
            print(f"  {k}: {w}\n      {d}")

    print("\n=== bands ===")
    for b in ["DISTILLED", "PARTIAL", "OWED", "DROPPED", "PROVENANCE-KEEP", "LEDGER-GAP", "UNTOUCHED"]:
        n = len(bands.get(b, []))
        note = {
            "DISTILLED": "  (every declared pin measured present in the named successor)",
            "PARTIAL": "  (a successor exists but not every pin landed)",
            "OWED": "  (real value, nobody has promoted it yet — DECLARED debt)",
            "DROPPED": "  (consciously dropped, with a rationale)",
            "LEDGER-GAP": "  (a successor cites it, but no ledger row — bookkeeping debt, cheap)",
            "UNTOUCHED": "  (no successor AND no ledger row — nobody has even looked)",
        }.get(b, "")
        print(f"  {b:<16} {n:>3}{note}")

    DEBT_BANDS = {"UNTOUCHED": 0, "OWED": 1, "PARTIAL": 2, "LEDGER-GAP": 3}
    debt = [(u, banded.get(u)) for u in units if banded.get(u) in DEBT_BANDS]
    debt.sort(key=lambda t: (DEBT_BANDS[t[1]], -(age_days(units[t[0]], dates, now) or 0)))
    if debt:
        print("\n=== ranked debt (band first, then age — a band beats a count) ===")
        cap = len(debt) if a.all else 25
        for u, b in debt[:cap]:
            ad = age_days(units[u], dates, now)
            ads = "UNCOMMITTED" if ad is None else f"{ad}d"
            print(f"  {ads:>11}  {b:<11} {u.replace(INBOX_REL + '/', '')}")
        if len(debt) > cap:
            print(f"  … and {len(debt) - cap} more (--all)")

    print("\n=== promoted destinations (inbound = staged units each dir claims as a source) ===")
    for d in DESTINATIONS:
        inbound = len({p for p, cs in blinks.items()
                       for c in cs if c.startswith(f"knowledge/{d}/")})
        print(f"  knowledge/{d}: {inbound} inbound")
    print("  (codes-th is NOT a destination: Authority tier, PR-only, primary legal sources only)")

    print("\n  staging is not knowledge: distill or consciously drop — don't let it ride.")
    if fails:
        print(f"  {len(fails)} integrity failure(s) — the bookkeeping is lying somewhere. exit 1")
    elif aging:
        print(f"  {len(aging)} unit(s) past {AGING_DAYS}d untouched — advisory. exit 2")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
