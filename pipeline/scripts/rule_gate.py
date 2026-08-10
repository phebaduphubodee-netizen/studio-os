"""rule_gate.py — makes the prose rules FAIL LOUD. PURE (no bpy).

    python pipeline/scripts/rule_gate.py --spec <spec.json> [--bundle <dir>]
                                          [--ledger qa/reproduction-curriculum.md]

WHY THIS FILE EXISTS (owner order 2026-08-05: *"แก้ไขความเข้มงวดในการบังคับใช้
กฏหน่อย"*).

Look at which rules in this repo actually held and which quietly did not:

  R9b placement gate  HELD   — it is a function inside trn002_build.py that
                               raises SystemExit, so no frame can be rendered
                               past it.
  mesh winding        HELD    once a test existed. Before that it was wrong for
                               five rounds and no critic, gate or LOOK could
                               have seen it.
  R7 written triage   DRIFTED — enforced by the builder remembering.
  R10 justification   ABSENT  — which is how a bare post that "carries shade"
                               and a 60 mm fin standing free on the floor
                               reached a frame the owner then had to catch.
  charter distillation SILENT — the charter's second paragraph says the product
                               is the LEARNING, not the copy. Six rounds
                               produced hundreds of measurements and nothing
                               entered knowledge/. Nothing gated on it.

The pattern is not subtle: **a rule is real exactly to the extent that it is a
program that fails in a path someone already has to run.** Everything else is a
note to a builder who has already read it and will still forget, because the
moment of forgetting does not feel like forgetting — it feels like typing a
reasonable number for a dimension nobody could measure.

So this module turns the prose into checks, and `trn002_build.py` calls it
before it will render anything.

WHAT IT DOES NOT DO, on purpose: it cannot tell whether a justification is
TRUE. `why: "carries the shade"` passes the syntax and is exactly the reasoning
that produced the defect. What the gate buys is that the assumption must be
WRITTEN DOWN, in the spec, next to the number — where a critic, the owner, or
the next audit can read it. Making the invisible visible is the whole
mechanism; judgement stays a human rung.
"""
import argparse
import glob
import json
import os
import re
import sys

# A mass may carry an assumed dimension. It may not carry one SILENTLY.
#
# AND THE GATE HAS TO SEPARATE TWO THINGS IT WOULD OTHERWISE CONFLATE — the
# same law this lane keeps applying to its other instruments. There is a real
# difference between:
#   (a) an OBJECT whose existence is assumed        "A(identity open)"
#   (b) a measured object with ONE assumed dimension "M(top 937) / A(bottom 485 occluded)"
# (b) is R10 already working: the assumption is named, bounded and beside the
# number. Failing it would train the reader to mute the gate, which is how the
# previous debt instrument in this repo died. Only (a) is a violation.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _utf8_stdout():
    """Windows consoles default to cp1252; every violation string here carries
    em-dashes and most carry Thai. A gate whose message is mojibake is a gate
    nobody reads — the same failure as a mute, one layer down."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


MEASURED_PART = re.compile(r"\bM\b|\bM\(|\bM-px|\bD\b|\bD\(", re.I)
BARE_ASSUMPTION = re.compile(r"^\s*A\s*$|^\s*A\s*\(\s*\)\s*$", re.I)
ASSUMED_PART = re.compile(r"\bA\b|\bA\(|A-swept|assumed", re.I)
UNMEASURABLE = re.compile(r"unmeasur|cannot be measured|not measurable", re.I)


def audit_spec(spec, require_seen=False):
    """R10 — every object justifies its own existence. Returns [violation str].

    `require_seen` turns on R10 question 2: every mass must say WHERE IT IS IN
    THE REFERENCE (`seen`: a pixel region) or state that it is not visible and
    why. This is the check that would have caught `lamp_stem`, whose prov
    claims a perfectly legitimate contact — "rest_on nightstand top 481,
    carries shade" — while the object itself appears nowhere in the reference.
    A well-formed derivation for an object that should not exist still reads as
    measured, so provenance ALONE cannot catch an invented object; only
    pointing at it in the reference can. Off until the fields are populated,
    because a check that fails on 52 masses at once gets muted."""
    out = []
    masses = spec.get("masses", [])
    if not masses:
        return ["spec carries no masses at all"]
    gaps = spec.get("declared_gaps", {})
    # A gap may be declared against the MASS ("duvet") or against one DIMENSION
    # of a measured mass ("right_wall_x"). The second form is R10 working as
    # written — the object is measured, one axis is not — and a checker that
    # only knew the first form would have blocked r27 for declaring its gap
    # more precisely than the check could read.
    AXIS = ("x", "y", "z", "w", "h", "d", "depth", "width", "height")
    gap_names = set(gaps)
    for g in gaps:
        head, _, tail = g.rpartition("_")
        if head and tail in AXIS:
            gap_names.add(head)
    for m in masses:
        name = m.get("name", "<unnamed>")
        prov = m.get("prov")
        if not prov:
            out.append(f"{name}: no `prov` — every mass states where its numbers "
                       f"came from (M measured / D derived from a contact / A assumed)")
            continue
        grounded = bool(MEASURED_PART.search(prov))
        if BARE_ASSUMPTION.match(prov) and not m.get("why"):
            out.append(
                f"{name}: prov is the bare letter 'A'. That records that a number "
                f"was assumed and nothing about WHAT or WHY. R10: write the "
                f"assumption out, or give the mass a `why`.")
        elif not grounded and ASSUMED_PART.search(prov) and not m.get("why"):
            out.append(
                f"{name}: NOTHING about this object is measured or derived "
                f"(prov: {prov.split(';')[0][:70]}) and it has no `why`. R10: an "
                f"object that exists because the builder needed one there is a "
                f"declared assumption — say what it is FOR, in the spec, beside "
                f"the number, where a critic can read it.")
        if require_seen and not m.get("seen"):
            out.append(
                f"{name}: no `seen` — R10 question 2 is 'point at it in the "
                f"reference'. Give a pixel region, or 'NOT VISIBLE: <reason>'. "
                f"A correct-looking derivation cannot distinguish a real object "
                f"from one invented to hold another object up.")
        if UNMEASURABLE.search(prov) and name not in gap_names and not m.get("why"):
            out.append(
                f"{name}: its own provenance says the measurement was not "
                f"possible, yet a number was typed. R10 corollary: the moment a "
                f"measurement pass reports UNMEASURABLE, typing a value for it is "
                f"the defect. Declare it in `declared_gaps` or justify it in `why`.")
    return out


# R7 is an ITEM-level rule, so checking it at FILE level is the repo's own named
# failure shape (a guard whose granularity does not match its rule's). The old
# version asked "does a TRIAGE_ file exist beside this ANSWER_ file" — and the
# answer was no for every bundle in the lane, while the triage of record sat in
# the GATE ARTIFACT at finer granularity than the check could see: one row per
# item, each refutation carrying its measurement. A file-level check would have
# cried wolf on eleven correctly-triaged rounds, which is how the previous debt
# instrument in this repo died.
#
# So: count the ITEMS a critic filed, find every id the builder wrote a triage
# row for — in a TRIAGE_ file, the bundle README, or the round's gate artifact —
# and name the ids that are missing. A violation now points at work, not at a
# filename.
#
# Both critics number the same way, verified against the r21-r27 answers:
#     C2 (local)   "## 7. The wood assembly on the left wall is not identifiable"
#     C3 (Gemini)  "**4. รายละเอียดพื้นผิว (Material) ขาดความสมจริง**"
ITEM_HEAD = re.compile(r"^[ \t]{0,3}(?:#{1,6}[ \t]*)?\*{0,2}(\d{1,2})[.)][ \t]", re.M)
# A render-MODE suffix may follow the round token. `_(r\d+[a-z]?)$` was anchored
# hard to the end, so `critique-trn002_mat_r34_quick` yielded no token at all and
# 23 correctly-triaged items reported as untriaged — R5 puts a `--quick` frame
# first, so EVERY playblast bundle hit this. The mode list is explicit rather
# than `_\w+` on purpose: a loose tail would start binding bracket variants
# (`_r30w110`) to the wrong round, and this function's own docstring records
# that a mis-binding is how one round's triage pays another's debt.
ROUND_TOKEN = re.compile(r"_(r\d+[a-z]?)(?:_(?:quick|full|draft))?$", re.I)


def _critic_tag(stem):
    """ANSWER_<stem>.md -> the tag its items are cited by in a triage row."""
    s = stem.lower()
    if "gemini" in s or "c3" in s:
        return "C3"
    if "c2" in s or "local" in s or "cowork" in s:
        return "C2"
    return None


def _item_count(text):
    """Items 1..n present as top-level headings. A stray '2026.' cannot inflate
    this, because only the contiguous run FROM 1 counts."""
    seen = {int(x) for x in ITEM_HEAD.findall(text)}
    n = 0
    while n + 1 in seen:
        n += 1
    return n


# The gates triage in TWO notations, and a checker that knew only the newer one
# reported six correctly-triaged items as untriaged on its first run — the
# cry-wolf failure this check exists to avoid, caught by testing it against the
# real gates before wiring it:
#   gates #6-#8   a table under a critic heading, first cell a bare number
#                 "## C3 Gemini 2.5 Pro" ... "| 1 | เครื่องนอนแข็ง… | ✓ รับ |"
#   gates #9-#15  the id inline, unambiguous  "**C2#3,7,13,18 + C3#4** …"
# A triage table row: the FIRST CELL is the item id. Tolerates markdown emphasis
# and a short letter prefix, because both are how this lane actually writes them
# and neither changes the meaning:
#     | 1 |          | **1** |          | **G1** |
# The r32 bundle used the second and third forms for all 24 of its items, and the
# strict version read the whole 13 KB document as empty — 24 false violations
# that blocked the next render. Attribution is unchanged and still comes from the
# nearest heading naming a critic, which is what keeps this tolerant of FORM
# without becoming tolerant of ABSENCE.
TABLE_ROW = re.compile(r"^\s*\|\s*[*_]{0,2}\s*[A-Za-z]{0,2}\s*(\d{1,2})\s*[*_]{0,2}\s*\|")
SAYS_C3 = re.compile(r"\bC3\b|gemini", re.I)
SAYS_C2 = re.compile(r"\bC2\b|cowork|local[- ]c2|claude-local", re.I)
# Gate #7 cites Gemini as G#1 … G#4 and G(r15)#5. Three notations for one rule
# across ten gates is itself a finding, but a checker that knows only the
# newest one converts the builder's own correct work into a violation — and a
# gate that fails on correct work is the one that gets muted.
ALIAS = {"C3": r"(?:C3|G(?:\(r\d+[a-z]?\))?)", "C2": r"(?:C2)"}


def _triaged_ids(text, tag):
    """Ids the builder wrote a triage row for, in any of the three notations."""
    ids = set()
    pat = ALIAS.get(tag, re.escape(tag))
    for run in re.findall(rf"\b{pat}\s*#\s*(\d{{1,2}}(?:\s*,\s*\d{{1,2}})*)", text):
        ids.update(int(p) for p in re.split(r"\s*,\s*", run))
    # Table form: a bare-number row belongs to the critic named by the nearest
    # heading above it. Ambiguous lines (both critics named) leave the attribution
    # unchanged rather than guessing.
    cur = None
    for line in text.splitlines():
        row = TABLE_ROW.match(line)
        if row:
            if cur == tag:
                ids.add(int(row.group(1)))
            continue
        c3, c2 = bool(SAYS_C3.search(line)), bool(SAYS_C2.search(line))
        if c3 != c2:
            cur = "C3" if c3 else "C2"
    return ids


def _gate_text(bundle_dir, lane_dir):
    """The gate artifact(s) that triage THIS bundle.

    Ids are not unique across rounds (gate #14 and gate #15 both carry a
    C2#12), so a lane-wide scan would let one round's triage pay another's
    debt. Two bindings, both exact:
      * the gate filename carries the bundle's round token (gate-10-r23.md), or
      * the gate NAMES the bundle directory, which is how a gate that triages
        the previous round's answers declares it ("เก็บคำตอบดิบไว้ที่
        `_private/.../critique-trn002_mat_r14/ANSWER_gemini25pro.md`").
    The second binding was added after the first version reported five
    correctly-triaged Gemini items as untriaged.
    """
    if not lane_dir or not os.path.isdir(lane_dir):
        return ""
    base = os.path.basename(os.path.normpath(bundle_dir))
    m = ROUND_TOKEN.search(base)
    tok = m.group(1).lower() if m else None
    parts = []
    surfaces = sorted(glob.glob(os.path.join(lane_dir, "gate-*.md")) +
                      glob.glob(os.path.join(lane_dir, "triage-*.md")))
    for p in surfaces:
        with open(p, encoding="utf-8") as f:
            body = f.read()
        named = base in body
        tokked = tok and re.search(rf"[-_]{tok}([-_.]|$)", os.path.basename(p), re.I)
        if named or tokked:
            parts.append(body)
    return "\n".join(parts)


# --- R7c: was the blind rung actually blind? ---------------------------------
# Nothing in this gate ever asked. It counts whether every critic ITEM got a
# triage row, which is the accounting half of R7; the BLINDNESS half — R7c's
# whole reason for replacing the Cowork rung with a bundle-scoped local agent —
# was carried by the builder pointing the agent at the right directory.
#
# It broke on r35. C2 and C3 fired in parallel into one dir, so C3's answer was
# on disk while the C2 agent read the folder it had been given. The agent
# reported it never opened the file, and its 21 items do not track C3's 5. That
# is compliance; R7c chose architecture on purpose, and a rule kept by the
# judge's manners is not the rule that was written.
#
# The ask is now a directory that provably holds a render and PROMPT.md and
# nothing else (`critique_bundle.c2_ask_dir`). This check refuses a bundle whose
# C2 answer arrived without one.
#
# The twelve bundles below FILED BEFORE THAT DIR EXISTED. They are seeded by
# name, exactly as the coverage ratchet was, so that the list can only grow
# through a diff someone else can read — and so this check bites on r36 rather
# than retroactively condemning work it could not have changed. r35_quick is on
# the list and is the round that bought the rule.
BLIND_ASK_SEEDED = {
    "critique-trn002_mat_r18", "critique-trn002_mat_r21", "critique-trn002_mat_r23",
    "critique-trn002_mat_r24", "critique-trn002_mat_r25", "critique-trn002_mat_r26",
    "critique-trn002_mat_r27", "critique-trn002_mat_r29", "critique-trn002_mat_r30_full",
    "critique-trn002_mat_r32", "critique-trn002_mat_r34_quick",
    "critique-trn002_mat_r35_quick",
}
C2_ASK_DIR = "c2-ask"


def audit_blind_ask(bundle_dir):
    """R7c — a C2 answer must come from an ask dir holding ONLY render+PROMPT."""
    base = os.path.basename(os.path.normpath(bundle_dir))
    c2 = [p for p in glob.glob(os.path.join(bundle_dir, "ANSWER_*.md"))
          if _critic_tag(os.path.basename(p)[len("ANSWER_"):-len(".md")]) == "C2"]
    if not c2 or base in BLIND_ASK_SEEDED:
        return []
    ask = os.path.join(bundle_dir, C2_ASK_DIR)
    if not os.path.isdir(ask):
        return [f"{base}: a C2 answer was filed with no `{C2_ASK_DIR}/` dir. R7c "
                f"makes the blind rung blind BY CONSTRUCTION — build the ask with "
                f"`critique_bundle.c2_ask_dir(<bundle>)` and point the agent at it, "
                f"never at the bundle root (which holds the other rungs' answers)."]
    names = sorted(os.listdir(ask))
    pngs = [n for n in names if n.lower().endswith(".png")]
    extra = [n for n in names if n not in set(pngs) | {"PROMPT.md", "README.md"}]
    if len(pngs) != 1 or "PROMPT.md" not in names or extra:
        return [f"{base}: `{C2_ASK_DIR}/` is not blind — {len(pngs)} render(s), "
                f"PROMPT.md {'present' if 'PROMPT.md' in names else 'MISSING'}, "
                f"extra {extra}. A judge shown another judge's answer stops being "
                f"a judge (R7c)."]
    return []


def audit_bundle(bundle_dir, lane_dir=None):
    """R7 — every critic ITEM gets a WRITTEN triage. Returns [violation str]."""
    out = []
    if not os.path.isdir(bundle_dir):
        return [f"bundle dir not found: {bundle_dir}"]
    answers = sorted(glob.glob(os.path.join(bundle_dir, "ANSWER_*.md")))
    if not answers:
        return out                      # no critic has filed yet; nothing owed
    surfaces = [_gate_text(bundle_dir, lane_dir)]
    # `TRIAGE.md` as well as `TRIAGE_<critic>.md`. The glob was `TRIAGE_*.md`
    # only, so a bundle carrying ONE combined triage file — which is what the
    # r32 round wrote, 13 KB of it, citing item ids — read to this gate as if
    # nothing had been triaged at all, and it refused the next render for 24
    # items that had all been answered. A guard that fails on correct work is
    # the one that gets switched off, and this lane has already lost an
    # instrument that way. Both filenames are legitimate; accept both.
    for extra in ("README.md", "TRIAGE.md") + tuple(
            os.path.basename(p) for p in glob.glob(
                os.path.join(bundle_dir, "TRIAGE_*.md"))):
        p = os.path.join(bundle_dir, extra)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                surfaces.append(f.read())
    triage = "\n".join(surfaces)
    for a in answers:
        stem = os.path.basename(a)[len("ANSWER_"):-len(".md")]
        tag = _critic_tag(stem)
        if tag is None:                 # unknown critic: fall back to file level
            if not os.path.exists(os.path.join(bundle_dir, f"TRIAGE_{stem}.md")):
                out.append(f"ANSWER_{stem}.md: no TRIAGE_{stem}.md, and the "
                           f"critic tag could not be derived from the filename "
                           f"to look for item rows.")
            continue
        with open(a, encoding="utf-8") as f:
            n = _item_count(f.read())
        if not n:
            continue                    # unparseable answer: do not cry wolf
        missing = sorted(set(range(1, n + 1)) - _triaged_ids(triage, tag))
        if missing:
            out.append(
                f"ANSWER_{stem}.md filed {n} items; {len(missing)} have no "
                f"triage row: {tag}#" + f", {tag}#".join(str(i) for i in missing) +
                f". R7: every returned item gets a written accept+lane or a "
                f"refutation carrying a MEASUREMENT — never taste. Cite the id "
                f"({tag}#N) in the round's gate artifact, the bundle README, or "
                f"TRIAGE_{stem}.md.")
    return out


def audit_learning(spec, inbox_root):
    """The charter — the copies are not the deliverable, the LEARNING is.

    A reproduction round that measured things owes a distillation. This checks
    only that the lane HAS an _inbox entry; it cannot check that the entry is
    good, and it deliberately does not try."""
    lane = re.sub(r"[^a-z0-9]", "", spec.get("id", "").lower())
    if not lane:
        return []
    # match on the normalised lane id so TRN-002 finds trn002-reference-study;
    # the first version globbed the raw id and reported "no distillation" for a
    # file written ten minutes earlier — a gate that cries wolf gets muted.
    for d in glob.glob(os.path.join(inbox_root, "*")):
        if lane in re.sub(r"[^a-z0-9]", "", os.path.basename(d).lower()):
            if glob.glob(os.path.join(d, "*.md")):
                return []
    return [f"no distillation for {spec.get('id')} under {inbox_root}. The "
            f"charter says the copies are NOT deliverables and the product is "
            f"the LEARNING; six rounds once produced hundreds of measurements "
            f"and not one line of knowledge/, because nothing gated on it."]


# --- R10, the other direction: the object that is NOT here --------------------
# `audit_spec` asks of every mass "do you deserve to exist". `coverage_check`
# asks the inverse — which object the reference SHOWS has no mass at all — and
# it has been able to answer since 2026-08-08. It was wired into NOTHING: run by
# hand it exits 1 naming `wall_floor_junction` on both r31 and r32, while every
# render in between went through a gate that printed "all masses justified".
#
# That is this repo's third repetition of one defect: id_mask.py sat unconnected
# for 12 rounds, the R7 triage half ran for 27 rounds without executing, and now
# a coverage detector was built the same week the spec it indicts was written.
# An instrument outside the path someone already runs is a document.

def _load_manifest(manifest_path):
    """The manifest as a dict, or None. Never raises — callers that MUST have it
    (audit_coverage) report the absence as a violation; callers that merely use
    it for extra context (audit_continuity) degrade to less discharge, never to
    less checking."""
    if not manifest_path or not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def audit_coverage(spec, manifest_path):
    """Fail-closed on the manifest. A coverage claim nobody declared is a mute.

    Returns [] only when a manifest EXISTS and every entry resolves. A missing
    manifest is a violation rather than a pass, for the reason coverage_check's
    own `--require-manifest` gives: from outside, a check with nothing to check
    and a check that found nothing look identical.
    """
    if not manifest_path:
        return ["no coverage manifest path given: R10's missing-object half "
                "cannot run, and a silent skip is what let the partition go "
                "thirty rounds with no opening"]
    if not os.path.isfile(manifest_path):
        return [f"no coverage manifest at {manifest_path}. The lane must write "
                f"down what the reference SHOWS before a frame can claim to "
                f"reproduce it — an object nobody wrote down is invisible to "
                f"every instrument here, including this one"]
    try:
        import coverage_check as COV
    except ImportError as e:  # pragma: no cover - import path accident
        return [f"coverage_check is not importable ({e}) — refusing to render "
                f"past a gate whose half is missing"]
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError) as e:
        return [f"coverage manifest at {manifest_path} is unreadable ({e})"]
    rows, violations = COV.audit(spec, manifest)
    if not rows and not violations:
        return [f"coverage manifest at {manifest_path} has no entries — an "
                f"empty manifest is the mute this check exists to prevent"]
    return violations


def baseline_ratchet(manifest_path, manifest=None, previous=None):
    """`absent_baseline` MAY SHRINK AND MAY NEVER GROW — as a program, not as prose.

    The manifest states that law in its own file and coverage_check repeats it in its
    docstring, and NOTHING ENFORCED IT: `audit()` only tests membership, so a builder who
    finds seven objects inconvenient can declare seven gaps and add seven ids to the
    baseline in the same edit, and every future round passes. That is the shape of the
    exemption this lane has already paid for twice — a list that can grow is not a
    constraint, which is the sentence coverage_check's own docstring uses.

    The previous value comes from git, because the ratchet needs a history and the working
    tree is not one. An UNTRACKED manifest therefore fails: a ratchet with no committed
    predecessor cannot tell shrinkage from growth, and passing in that state would make the
    first commit of the baseline unauditable — which is exactly when it matters most.

    `previous` is for tests; production reads it from `git show HEAD:<path>`. It is a
    SEPARATE question from `audit_coverage` — "does the spec cover the manifest" versus
    "has the exemption list grown" — and lives in its own function so neither test suite
    has to construct the other's fixture.
    """
    import subprocess
    if manifest is None:
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, ValueError) as e:
            return [f"coverage manifest at {manifest_path} is unreadable ({e})"]
    now = set(manifest.get("absent_baseline") or [])
    rel = os.path.relpath(os.path.abspath(manifest_path), REPO_ROOT).replace("\\", "/")
    if previous is None:
        try:
            p = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO_ROOT,
                               capture_output=True, text=True, encoding="utf-8",
                               timeout=30)
        except Exception as e:  # pragma: no cover - git missing
            return [f"cannot read the committed coverage manifest to check the "
                    f"ratchet ({e})"]
        if p.returncode != 0:
            return [f"`{rel}` is not committed, so `absent_baseline` has no predecessor "
                    f"and the may-shrink-never-grow law cannot be checked. Commit the "
                    f"manifest first — a ratchet with no history is a list, and this "
                    f"lane's record is that a list which can grow is not a constraint"]
        try:
            previous = json.loads(p.stdout)
        except ValueError as e:
            return [f"the committed `{rel}` is not readable JSON ({e})"]
    out = []

    # THE ENTRIES LIST RATCHETS THE OTHER WAY, and it was unguarded entirely.
    # `absent_baseline` growing is the builder widening its exemptions; the
    # ENTRY LIST shrinking is the builder deleting the question. Measured
    # 2026-08-08: removing the seven inconvenient lines from the manifest passed
    # the whole gate with exit 0 — strictly cheaper than declaring a gap, and
    # invisible to a ratchet that only watched the baseline. The manifest is a
    # READING OF THE REFERENCE: an entry leaves only because the reference does
    # not show that object after all, which is a claim about the target, not a
    # build decision — so it costs the same owner sign-off.
    now_e = {e.get("id") for e in (manifest.get("entries") or []) if e.get("id")}
    was_e = {e.get("id") for e in (previous.get("entries") or []) if e.get("id")}
    signoff = manifest.get("absent_baseline_signoff") or {}
    lost = sorted(e for e in (was_e - now_e)
                  if not (isinstance(signoff.get(e), str) and signoff[e].strip()))
    if lost:
        out.append(
            f"the coverage manifest LOST entries {lost} with no owner sign-off. "
            f"The entry list may only GROW: it records what the reference shows, "
            f"and deleting a line is a claim that the target does not show that "
            f"object — the owner's call, not the builder's. Same field as a "
            f"baseline widening: `absent_baseline_signoff: {{\"{lost[0]}\": "
            f"\"<reason + date>\"}}`")

    was = set(previous.get("absent_baseline") or [])
    # THE DEADLOCK THIS FIELD RESOLVES (found by an adversarial pass the hour this landed):
    # coverage_check's NEW-ABSENCE message instructs the builder to "add it to the baseline
    # in the same edit that declares the gap", and the first version of this ratchet refused
    # exactly that edit. The two halves gave mutually exclusive instructions, so no manifest
    # entry could EVER be discharged except by building it — and the four dishonest routes
    # (a built_as pointing anywhere, a namesake mass, a shortened entries list, an emptied
    # baseline) all still passed. A gate that blocks only the honest route is worse than no
    # gate: it teaches the builder that honesty is the expensive path.
    #
    # So growth is possible, and it costs an OWNER SIGNATURE — the repo's existing two-layer
    # law (guard_paths' owner-authored sign-off ledgers; the plan lane's semantic-facts-are-
    # owner-only rule). The builder may not widen its own exemption list; the owner may, and
    # the note says why, in a diff.
    grown = sorted(now - was)
    unsigned = [g for g in grown
                if not (isinstance(signoff.get(g), str) and signoff[g].strip())]
    if unsigned:
        out.append(
            f"`absent_baseline` GREW by {unsigned} with no owner sign-off. An object "
            f"may leave the frame, but the list of objects ALLOWED to be absent is not "
            f"the builder's to widen. Either build it, or have the owner add "
            f"`absent_baseline_signoff: {{\"{unsigned[0]}\": \"<reason + date>\"}}` to "
            f"the manifest (R2/R3). Adding it silently is the builder excusing the builder")
    return out


# KNOWN LIMITS OF THE COVERAGE HALF, kept here because a guard whose blind spots are
# undocumented is trusted for coverage it does not have. Closed 2026-08-08 after an
# adversarial pass found four bypasses that all reached exit 0:
#   CLOSED  a zero-size namesake mass          -> coverage_check.MIN_EXTENT_MM
#   CLOSED  emptying absent_baseline           -> coverage_check tests key PRESENCE
#   CLOSED  deleting the manifest entry        -> the entries ratchet above
#   PARTIAL a built_as pointing anywhere       -> a mass claimed by TWO entries is
#           refused, but a built_as naming ONE unrelated existing mass still passes.
#           Real correspondence is semantic (is this mass actually that object?) and
#           no cheap check reaches it. This is the honest residual.


def audit_craft(spec):
    """ADVISORY, and loud. Returns [note] — never fed to the violation list.

    craft_check says in its own docstring that it cannot see occlusion, so a
    corner hidden behind the bed is charged the same as one in the open. It
    therefore reports and does not veto — the same call R9b already made for
    interpenetration, where an AABB cannot tell interlocking from intersecting.
    Advisory is not silent: the count is printed and the roster names it, so it
    cannot become the kind of half that runs for 27 rounds unnoticed.
    """
    try:
        import craft_check as CRAFT
    except ImportError as e:  # pragma: no cover - import path accident
        return [f"craft_check is not importable ({e})"]
    rows, short = CRAFT.audit_silhouette(spec)
    if not rows and short:
        return short  # e.g. no solved camera — say so rather than report 0
    if not short:
        return []
    return [f"{len(short)} silhouette shortfall(s) of {len(rows)} rounded "
            f"masses (advisory — occlusion is not modelled):"] + \
           ["  " + s for s in short]


# --- Continuity: a measurement may be superseded, never dropped by omission ---
# chair_leg_1..4 were measured at r12 and are absent from r14 through r30 and
# from all thirteen r30 variants; r31 restored them. Eighteen rounds, and the
# lane's own commit says why in one sentence: *nothing compares a spec to the
# one before it.* Every other rule here keys on something the builder ASSERTED —
# a prov tag, a gap reason, a triage row. A deleted mass asserts nothing, so no
# assertion-keyed rule can ever see this class. It needs a diff.

SPEC_ROUND = re.compile(r"^spec_r(\d+)\.json$", re.I)


def previous_spec_path(spec_path):
    """The largest PLAIN round below this one that exists on disk, or None.

    Not `N-1`: spec_r13.json was never written, so a literal sibling lookup
    no-ops exactly where the chair-leg drop happened. And not any sibling
    matching `r30*`: r30 has thirteen bracket VARIANTS (spec_r30w110.json …)
    which are experiments off the line of record, not the line itself. So
    variants are excluded by pattern and the largest plain round below N wins.
    """
    if not spec_path:
        return None
    base = os.path.basename(str(spec_path))
    m = SPEC_ROUND.match(base)
    if not m:
        return None
    n = int(m.group(1))
    d = os.path.dirname(os.path.abspath(str(spec_path))) or "."
    best, best_path = -1, None
    for name in os.listdir(d):
        mm = SPEC_ROUND.match(name)
        if not mm:
            continue
        k = int(mm.group(1))
        if k < n and k > best:
            best, best_path = k, os.path.join(d, name)
    return best_path


def _gap_reasons(spec):
    """`declared_gaps` as {id: reason}. Mirrors coverage_check._gaps.

    The list form (r32 round-tripped the dict through `list()` and lost ten
    reasons) yields empty reasons, so a bare name cannot discharge anything
    here either — same law, same reason: the reason IS the declaration.
    """
    g = spec.get("declared_gaps")
    if isinstance(g, dict):
        return {k: (v if isinstance(v, str) else "") for k, v in g.items()}
    if isinstance(g, list):
        return {k: "" for k in g if isinstance(k, str)}
    return {}


def _aggregate_cover(manifest):
    """mass name -> the manifest entry id that claims it, from `built_as`.

    An object in a photograph is often several masses ("the chair" is
    chair_seat + chair_back + chair_leg_1..4), and coverage_check already has a
    field that says so. Continuity reuses it rather than inventing a second
    convention: a gap declared for the ENTRY discharges the masses that entry
    names, and nothing else.

    NOT a prefix match, deliberately. `declared_gaps["chair"]` covering
    `chair_leg_*` by string prefix is the exact defect this whole rule exists
    for — four measured chair legs left at r14 and were wrong for eighteen
    rounds. The relationship has to be DECLARED to count.
    """
    out = {}
    for e in (manifest or {}).get("entries") or []:
        eid = e.get("id")
        for m in e.get("built_as") or []:
            if isinstance(m, str) and eid:
                out[m] = eid
    return out


def audit_continuity(spec, spec_path, prev_spec=None, manifest=None):
    """Diff against the previous round. Returns [violation str].

    ONE class, and it is invisible to every other check in this file:
      DROPPED — a mass present last round and gone now, with no declared gap

    A DOWNGRADE rule lived here for one afternoon and was deleted the same day.
    It fired when a prov carried an `M(`/`D(` tag last round and none now, which
    sounds right and is not: it keys on NOTATION, not on evidence. Twelve of its
    thirteen lifetime events were at r12 — the round that IMPROVED provenance,
    rewriting `M(top mid backprojection at z=420)` into `audit 2026-08-05
    (R10b): far face -4882 -> -5450, measured at the spec's OWN z`. It convicted
    the most careful measurement round in the lane's history, 92% false.
    Deleting it costs no coverage, which was checked before it was removed:
    `audit_spec` already fails `A(bedding norm)` AND `A(seat 450 vanity norm)`
    with "NOTHING about this object is measured", and correctly passes the r12
    rewrite. The class DOWNGRADE uniquely caught was empty.

    `prev_spec` / `manifest` are injectable for tests; production resolves both.
    """
    if prev_spec is None:
        p = previous_spec_path(spec_path)
        if not p:
            return []
        try:
            with open(p, encoding="utf-8") as f:
                prev_spec = json.load(f)
        except (OSError, ValueError) as e:
            return [f"previous spec {p} is unreadable ({e}) — continuity "
                    f"cannot be checked, and an unchecked diff is how a "
                    f"measured object left the scene for eighteen rounds"]
    prev = {m.get("name"): m for m in prev_spec.get("masses", []) if m.get("name")}
    now = {m.get("name"): m for m in spec.get("masses", []) if m.get("name")}
    gaps = _gap_reasons(spec)
    renamed = spec.get("renamed") if isinstance(spec.get("renamed"), dict) else {}
    covered_by = _aggregate_cover(manifest)
    out = []
    for name in sorted(set(prev) - set(now)):
        # TWO honest ways for a name to disappear, and they are different facts.
        #
        # `declared_gaps[name]` = the OBJECT left the frame, with a reason the
        # owner can overrule. `renamed[name]` = the object is still here under
        # another name — and that claim is VERIFIED against the current spec,
        # not taken on trust. A rename that points at a mass which does not
        # exist is a worse defect than the drop it was covering, so it fails
        # louder. This is the difference between a discharge and a permission
        # slip: r30 split back_wall into back_wall_L/R, which is legitimate and
        # takes one line to say; a free-text excuse field would have taken the
        # same line and proved nothing.
        heir = renamed.get(name)
        heirs = [heir] if isinstance(heir, str) and heir else \
                [h for h in heir if isinstance(h, str)] if isinstance(heir, list) else []
        if heirs:
            missing = [h for h in heirs if h not in now]
            if not missing:
                continue
            out.append(
                f"RENAME UNVERIFIED `{name}` -> {', '.join(heirs)}: "
                f"{', '.join(missing)} does not exist in this round's masses. A "
                f"rename is CHECKABLE; that is the whole reason it is allowed to "
                f"discharge a drop, and a claim that fails its own check is a "
                f"worse defect than the drop it was covering")
            continue
        reason = gaps.get(name, "")
        if reason.strip():
            continue
        # ...or the gap was declared for the manifest ENTRY this mass realises.
        # `declared_gaps["duvet"]` covering duvet_top + duvet_drape is legitimate
        # and the COVERAGE half of this same run already accepts it; without this
        # the two halves contradict each other on one spec, which is how a
        # builder learns to stop reading the gate.
        agg = covered_by.get(name)
        if agg and gaps.get(agg, "").strip():
            continue
        was = (prev[name].get("prov") or "").strip()
        measured = " Its provenance last round was a MEASUREMENT." \
            if MEASURED_PART.search(was) else ""
        out.append(
            f"DROPPED `{name}`: present last round, absent now, and "
            f"`declared_gaps` carries no reason for it.{measured} An object may "
            f"leave the frame — but as a decision the owner can read, never by "
            f"omission (chair_leg_1..4 left this way and were wrong for "
            f"eighteen rounds). Prov was: {was[:120] or '(none)'}")
    return out


# --- R7 debt resolution -------------------------------------------------------
# PURE, and it lives here rather than in the builder for the reason the layer law
# gives (pipeline/CLAUDE.md): rule/gate code must run under plain python. It sat
# in trn002_build.py for one afternoon and in that time acquired a real bug that
# no test could reach — a waiver written for `critique-trn002_blockout_r1_quick`
# silently waived `critique-trn002_blockout_r1`, because the match was `x in
# text`. Both bundles exist in this lane. A guard that quietly excuses work
# nobody excused is worse than no guard.

ROUND_OF = re.compile(r"(r\d+[a-z]?)(?=\.|$|_)", re.I)


def round_of(path):
    """'spec_r28.json' / 'critique-trn002_mat_r27' -> 'r28' / 'r27'."""
    m = ROUND_OF.search(os.path.basename(str(path)))
    return m.group(1).lower() if m else None


def is_waived(name, waiver_text):
    """BOUNDED name match. Never a substring test — see the note above."""
    return re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])",
                     waiver_text or "") is not None


def bundle_debt(bundle_root, spec_path, waivers_path=None):
    """Bundle dirs that have a critic ANSWER and still owe a triage, oldest first.

    The round being rendered is EXCLUDED by construction: its critics have not
    run yet, and a gate that blocks a render on a critique OF that render can
    never open. The check therefore carries exactly one round of latency — which
    is the latency the rule always had. r26's C2#14 said the wardrobe bays were
    "arbitrarily unequal", nobody triaged it, and the next round the owner found
    that bay built 259 mm short with his own eye.
    """
    this_round = round_of(spec_path)
    waived = ""
    if waivers_path and os.path.exists(waivers_path):
        with open(waivers_path, encoding="utf-8") as f:
            waived = f.read()
    owing = []
    for d in glob.glob(os.path.join(bundle_root, "critique-*")):
        base = os.path.basename(d)
        tok = round_of(base)
        if not tok or tok == this_round or is_waived(base, waived):
            continue
        if glob.glob(os.path.join(d, "ANSWER_*.md")):
            owing.append((int(re.search(r"\d+", tok).group()), tok, d))
    return [d for _, _, d in sorted(owing)]



# --- R9: NOT SHIPPED AS A GATE. Diagnostic only, and here is why -------------
# The prose draft proposed a floor: `D(N) <= 0.95*D(N-1) OR O(N) <= O(N-1)-1`,
# with D a median relative distance over a frozen scalar panel. Its author sent
# it back for the OR (closing one open item clears the floor however far the
# picture moved), rewrote it without the OR, and then ran it against this lane's
# own published history. IT NEVER FIRES:
#
#     round     D    verdict
#      r23  0.3031   FIRST
#      r24  0.2168   CLEARS  -28.5%
#      r25  0.1914   CLEARS  -11.7%
#      r26  0.1630   CLEARS  -14.8%
#      r27  0.1510   CLEARS   -7.4%
#
# Per row, the reason is plain and it is the twelfth flattering scorer in this
# repo rather than a tuning problem:
#
#     row            r23     r24     r25     r26     r27    r23->r27
#     clipped_pct  81.471  20.500   1.735   2.647   2.676     0.03x
#     p99           0.398   0.217   0.191   0.011   0.012     0.03x
#     p50           0.131   0.005   0.108   0.025   0.039     0.30x
#     LEVEL         0.046   0.153   0.171   0.163   0.151     3.28x WORSE
#     SHAPE         0.303   0.276   0.317   0.199   0.200     0.66x
#
# The median descends every round because ONE row collapsed from 82x off target
# to 2.7x, and that row's scale is an artifact of its target being 0.034. Under
# it, LEVEL got 3.3x WORSE across four rounds and no gate said so. THE ROWS ARE
# NOT COMMENSURABLE, so no aggregate over them means anything: `max` is captured
# by the same row, and "no row may worsen" ends the unit at r26 and would have
# killed r24 and r26, which were the two good rounds.
#
# Two alternatives were tried and both fail. A defensible single floor is NOT
# solved, and shipping a third scorer for a repo already burned eleven times by
# scorers would be the disease. So:
#
#   * `distance` and `yield_report` are DIAGNOSTIC. They print the per-row table
#     every round. That alone is worth having: it is the instrument that would
#     have shown LEVEL degrading for four rounds while the headline improved.
#   * `cap_check` DOES gate, because counting rounds needs no aggregate.
#
# What would solve it, for whoever picks this up: a per-row TOLERANCE declared
# with the panel before round 1 (how much of this row's distance is noise), so
# "worsened" becomes a claim with a number behind it instead of any change of
# sign. That is a measurement task, not a rule-writing task, and it is exactly
# the work this repo keeps skipping in favour of writing the rule.
YIELD_FLOOR = 0.05          # informational: the descent the draft asked for


def distance(scalars, targets):
    """D - median relative distance over a FROZEN panel. DIAGNOSTIC ONLY; see the
    note above for why this number must not carry a verdict."""
    ds = []
    for k, t in targets.items():
        if k in scalars and scalars[k] is not None:
            ds.append(abs(scalars[k] - t) / (abs(t) if t else 1.0))
    if not ds:
        raise ValueError("no panel rows present - D is undefined, not zero")
    ds.sort()
    n = len(ds)
    return ds[n // 2] if n % 2 else 0.5 * (ds[n // 2 - 1] + ds[n // 2])


def per_row(scalars, targets):
    """The table that matters. Every panel row's own distance, unaggregated."""
    return {k: abs(scalars[k] - t) / (abs(t) if t else 1.0)
            for k, t in targets.items() if k in scalars and scalars[k] is not None}


def yield_report(ledger, targets):
    """Per-round D plus per-row distances and which rows WORSENED. No verdict."""
    out, prev = [], None
    for row in ledger:
        rows = per_row(row["scalars"], targets)
        worse = sorted(k for k in rows if prev and k in prev and rows[k] > prev[k])
        out.append({"round": row["round"], "D": distance(row["scalars"], targets),
                    "rows": rows, "worsened": worse})
        prev = rows
    return out


def cap_check(ledger_row, rounds_done, full_frames_done):
    """R10-proposed: a unit declares its cap BEFORE round 1. No row -> no render."""
    if not ledger_row:
        return ["no ledger row: a unit declares cap_rounds and cap_full_frames "
                "before its first render. TRN-001, the only unit this curriculum "
                "has closed, cost 20 rounds and 37 full frames; TRN-002 passed "
                "135% of that with no rule anywhere that noticed."]
    out = []
    for key, done in (("cap_rounds", rounds_done),
                      ("cap_full_frames", full_frames_done)):
        cap = ledger_row.get(key)
        if cap is None:
            out.append(f"ledger row declares no {key}")
        elif done > cap:
            out.append(f"{key} exceeded: {done} > {cap}. Only the owner extends a "
                       f"cap (R3), once per unit, with the new number and its "
                       f"reason written in the ledger row BEFORE the next render.")
    return out


# --- R1, finally as a program ------------------------------------------------
# `cap_check` above has had four passing tests and no caller since the day it was
# written, and the reason was never the code: it needs `cap_rounds` /
# `cap_full_frames` and no unit had ever declared them. The curriculum ledger's
# `rounds | full frames` column holds ACTUALS, is markdown nothing parses, and
# carries no TRN-002 row at all. The three pieces below are what turn a declared
# number into an enforced one: a file the owner writes, a loader, and counts
# taken from disk so neither number can be typed.
CAPS_REL = "qa/curriculum-caps.json"


def load_caps(unit, path=None):
    """Owner-declared caps for a unit, or None. Never raises: a malformed or
    missing caps file must not crash the render — it must make `cap_check` say
    'no ledger row', which is already a violation with a better message."""
    p = path or os.path.join(REPO_ROOT, CAPS_REL)
    try:
        with open(p, encoding="utf-8") as f:
            return (json.load(f).get("units") or {}).get(unit)
    except (OSError, ValueError, AttributeError):
        return None


def count_rounds(lane_dir, spec=None):
    """The larger of: canonical spec files on disk, and the spec's own `round`.

    Bracket variants (spec_r30w110.json) are one round's EXPERIMENTS, not
    rounds — this lane has thirteen on r30 alone and counting them would burn a
    quarter of the budget on one afternoon's wattage sweep. So only
    spec_r<N>.json is counted.

    BUT THE FILE COUNT ALONE UNDER-REPORTS, measured the hour this landed:
    TRN-002 is at round 34 and has 31 canonical specs, because some rounds
    never produced one (r13 does not exist). A cap fed the file count would
    have handed the unit three free rounds. The spec's own `round` field is the
    other reading, and it is SELF-REPORTED, which is what counting from disk
    was meant to avoid.

    So take the MAX and neither reading can be gamed alone: under-declare the
    round and the file count floors it; skip a spec file and the declaration
    floors it. Fail-closed in both directions is cheaper than deciding which
    number to trust.
    """
    on_disk = 0
    if lane_dir and os.path.isdir(lane_dir):
        on_disk = sum(1 for f in os.listdir(lane_dir) if SPEC_ROUND.match(f))
    declared = (spec or {}).get("round")
    return max(on_disk, declared if isinstance(declared, int) else 0)


def _png_size(path):
    """(w, h) from the IHDR, or None. Stdlib only — the layer law keeps Pillow
    out of gate code, and a 24-byte read is cheaper than an image decode."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"))
    except OSError:
        return None


def count_full_frames(render_dir, wh):
    """PNGs at the spec's OWN image size. COUNTED BY PIXELS, NOT BY FILENAME.

    The distinction is worth the function. 137 of this lane's PNGs do not carry
    the `_quick` token and exactly 44 are full frames — the other 93 are crops,
    comparison sheets and excerpts of the target. A filename-based count was the
    first thing tried and it was wrong by 3x, which would have retired the unit
    on a budget it had not spent.
    """
    if not render_dir or not os.path.isdir(render_dir) or not wh:
        return 0
    return sum(1 for f in os.listdir(render_dir)
               if f.lower().endswith(".png")
               and _png_size(os.path.join(render_dir, f)) == tuple(wh))


def manifest_for(lane_dir, manifest_path=None):
    """Derive the coverage manifest from the lane, so nobody has to remember it.

    An explicit path wins. Otherwise the lane's own `coverage-manifest.json` is
    used WHETHER OR NOT IT EXISTS — the non-existent case is a violation, not a
    skip. Deriving beats passing: the R7 half was mute for 27 rounds because it
    ran only `if bundle_dir:` and the one call site passed none.
    """
    if manifest_path:
        return manifest_path
    if lane_dir:
        return os.path.join(lane_dir, "coverage-manifest.json")
    return None


# R11 — WHICH RUNGS OPEN THE PICTURE. Owner order 2026-08-09: *"ผมขอบังคับให้ทุก
# กลไก ทุกขั้นตอนต้องมองรูปจริง"*. Measured the same day, before this line existed:
# of the 8 modules this gate calls, 0 ever opened an image, and of the 21
# instruments in pipeline/scripts that do, 0 were called by any of them. Every
# rung deciding whether a frame ships was reading DECLARATIONS ABOUT the picture.
# The set below is not decoration: `enforce` prints the two groups separately on
# every run, so a gate that did not look at the frame says so in the render path,
# which is the channel the owner actually reads.
PIXEL_RUNGS = {"R11 pixels"}


def check(spec, bundle_dir=None, inbox_root=None, require_seen=False,
          lane_dir=None, spec_path=None, manifest_path=None, roster=None,
          advisories=None, render_dir=None, caps_path=None,
          decisions_path=None, frame_path=None, target_path=None):
    """Return [violation str]. `roster` and `advisories`, when given lists, are
    filled in so the caller can report WHAT RAN — see enforce()."""
    def note(name, ran_, why=""):
        if roster is not None:
            roster.append((name, ran_, why))

    v = audit_spec(spec, require_seen)
    note("R10 spec", True)

    # R9, one level up from a position: a RELATIONSHIP that only two equal
    # numbers record is not recorded at all. Blocking, and it belongs on the
    # blocking side rather than beside audit_craft because a broken row is not a
    # matter of degree — the spec is asserting a joint that its own numbers
    # refuse. r37 is the case: the headboard's invented 176 mm died and the
    # bed's head coordinate, derived from it, stayed perfectly legal 83 mm away.
    try:
        import contact_check as CONTACT
    except ImportError as e:  # pragma: no cover - import path accident
        v.append(f"contact_check is not importable ({e}) — refusing to render "
                 f"past a gate whose half is missing")
        note("R9 contacts", False, "module not importable")
    else:
        v += CONTACT.check(spec)
        rows = spec.get("contacts") or []
        note("R9 contacts", True, f"{len(rows)} declared")

    if bundle_dir:
        v += audit_bundle(bundle_dir, lane_dir)
        note("R7 triage", True)
        v += audit_blind_ask(bundle_dir)
        note("R7c blind ask", True)
    else:
        note("R7 triage", False, "no bundle dir given")
        note("R7c blind ask", False, "no bundle dir given")

    if inbox_root:
        v += audit_learning(spec, inbox_root)
        note("charter distillation", True)
    else:
        note("charter distillation", False, "no inbox root given")

    mpath = manifest_for(lane_dir, manifest_path)
    v += audit_coverage(spec, mpath)
    note("R10 coverage", True, mpath or "")
    if mpath and os.path.isfile(mpath):
        v += baseline_ratchet(mpath)
        note("absent_baseline ratchet", True)
    else:
        note("absent_baseline ratchet", False, "no manifest to ratchet")

    # The roster must not say a half RAN when it could not. `previous_spec_path`
    # returns None for two different reasons and the first version reported both
    # as "first of its line" — so renaming a spec to spec_r33a.json silently
    # disabled the diff while the roster affirmed it. That is the mute this
    # field was added to prevent, reproduced inside the fix for it.
    manifest = _load_manifest(mpath)
    canonical = bool(spec_path and SPEC_ROUND.match(os.path.basename(str(spec_path))))
    prev = previous_spec_path(spec_path)
    v += audit_continuity(spec, spec_path, manifest=manifest)
    if not spec_path:
        note("continuity", False, "no spec path given")
    elif not canonical:
        note("continuity", False,
             f"`{os.path.basename(str(spec_path))}` is not a canonical "
             f"spec_r<N>.json — no round to diff against")
    elif not prev:
        note("continuity", True, "no earlier round on disk — first of its line")
    else:
        note("continuity", True, f"vs {os.path.basename(prev)}")

    # R1 STOP-LOSS. Unwired for 34 rounds — not because the code was missing but
    # because the numbers lived nowhere a program could read. Both counts come
    # off disk so a builder cannot report its own spend.
    unit = os.path.basename(os.path.normpath(lane_dir)) if lane_dir else None
    if unit:
        img = spec.get("image") or {}
        wh = (img.get("w"), img.get("h")) if img.get("w") and img.get("h") else None
        caps = load_caps(unit, caps_path)
        rounds = count_rounds(lane_dir, spec)
        frames = count_full_frames(render_dir, wh)
        v += cap_check(caps, rounds, frames)
        # FAIL CLOSED on the count, not just on the cap. Without a render dir
        # `frames` is 0, which passes any cap — a mute dressed as compliance,
        # and the exact shape that left R7 silent for 27 rounds. If a unit has
        # declared a frame cap, not being able to count frames is a violation.
        # The first version of this guard tested `not render_dir` — TRUTHINESS of
        # a string — and the call site in trn002_build.py was passing
        # `<...>/renders/critique/renders`, a path that does not exist. A
        # non-empty string that names nothing sailed past the test, frames counted
        # 0, and 0 passes a cap of 55. Measured 2026-08-09: the call-site path
        # yields 0 full frames and the real one yields 44. So the guard reproduced
        # the mute it was written three lines earlier to prevent, and the roster
        # line said "44 full frames" only when a human ran the CLI, which resolves
        # the dir differently. A dir that cannot be read is a count that did not
        # run, whatever the argument looked like.
        countable = bool(render_dir) and os.path.isdir(render_dir)
        if caps and caps.get("cap_full_frames") is not None and not countable:
            v.append(f"{unit} declares cap_full_frames={caps['cap_full_frames']} "
                     f"but the render dir is unreadable ({render_dir!r}), so "
                     f"frames counted as 0 and the cap could not bite. A count "
                     f"that cannot run must not read as a count that passed.")
        note("R1 cap", True, f"{unit}: {rounds} rounds, {frames} full frames"
             + ("" if countable else f" — NO READABLE RENDER DIR ({render_dir!r})"))
    else:
        note("R1 cap", False, "no lane dir given, so no unit to look up")

    # THE DECISION LOG. This half does NOT block on the owner and must never be
    # made to — he removed his own rung on 2026-08-08 ("เอาผมออกจาก gate เลย ไม่
    # ต้องรอผม"), because he reads renders rather than documents and a gate
    # waiting on him was waiting in a channel he does not use. What it checks is
    # the builder's side of that bargain: a call made in his name has to be
    # written down, in force somewhere real, and reversible in one named edit.
    if unit:
        try:
            import decisions_check as DEC
        except ImportError as e:  # pragma: no cover - import path accident
            v.append(f"decisions_check is not importable ({e}) — refusing to "
                     f"render past a gate whose half is missing")
            note("decision log", False, "module not importable")
        else:
            data = DEC.load(decisions_path
                            or os.path.join(REPO_ROOT, DEC.DECISIONS_REL))
            v += DEC.check(data, unit, REPO_ROOT,
                           path_hint=decisions_path or DEC.DECISIONS_REL)
            rows = DEC.in_force(data, unit) if data else []
            mine = sum(1 for d in rows if not d.get("owner_override"))
            note("decision log", True,
                 f"{len(rows)} in force ({mine} taken in the owner's name)")
    else:
        note("decision log", False, "no lane dir given, so no unit")

    # R11 — THE ONE RUNG THAT OPENS THE PICTURE. It can only run where a frame
    # exists, which is AFTER the render, so `trn002_build` calls the gate a
    # second time with the frame it just wrote. Pre-render the rung is absent and
    # the roster says so by name rather than staying quiet about it.
    try:
        import pixel_check as PIX
    except ImportError as e:  # pragma: no cover - import path accident
        v.append(f"pixel_check is not importable ({e}) — refusing to call this a "
                 f"gate while its only rung that looks at the frame is missing")
        note("R11 pixels", False, "module not importable")
    else:
        claims = spec.get("pixel_claims") or []
        if frame_path and target_path:
            v += PIX.check(spec, frame_path, target_path)
            note("R11 pixels", True,
                 f"{len(claims)} claim(s) on {os.path.basename(str(frame_path))}")
        else:
            note("R11 pixels", False,
                 "no frame given — this run of the gate did NOT open the picture"
                 + (f" ({len(claims)} claims are waiting for one)" if claims else ""))

    if advisories is not None:
        advisories += audit_craft(spec)
        try:
            import contact_check as CONTACT
        except ImportError:  # pragma: no cover - reported as a violation above
            pass
        else:
            advisories += CONTACT.undeclared(spec)
        try:
            import pixel_check as PIX
        except ImportError:  # pragma: no cover
            pass
        else:
            advisories += PIX.unclaimed(spec)
    return v


def enforce(spec, bundle_dir=None, inbox_root=None, hard=True, require_seen=False,
            lane_dir=None, spec_path=None, manifest_path=None, render_dir=None,
            caps_path=None, decisions_path=None, frame_path=None,
            target_path=None):
    """Print and, if hard, refuse to continue. Called by the builder."""
    _utf8_stdout()
    roster, advisories = [], []
    v = check(spec, bundle_dir, inbox_root, require_seen, lane_dir,
              spec_path=spec_path, manifest_path=manifest_path,
              roster=roster, advisories=advisories,
              render_dir=render_dir, caps_path=caps_path,
              decisions_path=decisions_path, frame_path=frame_path,
              target_path=target_path)
    # Name what was checked, not just that nothing failed — and name what was
    # NOT, on the pass path AND the fail path. A gate that prints the same
    # success line whether or not it ran a half of itself is indistinguishable
    # from a mute, which is exactly what the R7 half was for 27 rounds.
    ran = [n for n, ok, _ in roster if ok]
    skipped = [(n, why) for n, ok, why in roster if not ok]
    if advisories:
        print("RULE GATE (advisory, not blocking):")
        for s in advisories:
            print(f"  ~~ {s}")
    # R11 — SAY WHICH HALF LOOKED AT THE PICTURE, EVERY RUN. Owner order
    # 2026-08-09. Printing one undifferentiated "checked: ..." list is what let a
    # gate made entirely of declaration-readers go green on a frame four critics
    # called unfinished: the roster read like coverage.
    saw = [n for n in ran if n in PIXEL_RUNGS]
    blind = [n for n in ran if n not in PIXEL_RUNGS]
    if not v:
        print(f"RULE GATE: {len(spec.get('masses', []))} masses, all justified")
    else:
        print(f"\nRULE GATE: {len(v)} violation(s)")
        for s in v:
            print(f"  !! {s}")
    print(f"RULE GATE: OPENED THE PICTURE — {', '.join(saw) if saw else 'NOTHING'}")
    print(f"RULE GATE: declarations only — {', '.join(blind)}")
    for name, why in skipped:
        print(f"RULE GATE: !! {name} NOT checked ({why})")

    # PRINT THE DECISION LOG ON EVERY RUN, pass or fail. With no rung waiting
    # for the owner, visibility is the entire control — and the render path is
    # the one channel he actually uses ("ผมก็นั่งดูทุกรูปตลอดอยู่แล้ว"). One line
    # per decision, each naming its reversal, so overruling costs him a sentence.
    unit = os.path.basename(os.path.normpath(lane_dir)) if lane_dir else None
    if unit:
        try:
            import decisions_check as DEC
            data = DEC.load(decisions_path
                            or os.path.join(REPO_ROOT, DEC.DECISIONS_REL))
            rows = DEC.in_force(data, unit) if data else []
        except ImportError:  # pragma: no cover - reported as a violation above
            rows = []
        if rows:
            print(f"\nDECISIONS IN FORCE ({unit}) — เปลี่ยนได้ทุกข้อ ทุกเมื่อ "
                  f"ไม่มีข้อไหนรอคุณอยู่:")
            for d in rows:
                print(DEC.one_line(d))

    # WHERE ARE WE IN THE PLAN — printed into the render path on every run, for
    # the same reason the decision log is: that is the channel he actually uses.
    #
    # NOT BLOCKING, and the distinction is the whole point. `decisions_check`
    # blocks because a decision with no reversal is a defect IN THE FRAME'S
    # provenance. An overdue plan review is not — halting a render over owed
    # paperwork is the enforcement clause R3 revoked, one level up. So this
    # prints loudly and stops nothing.
    #
    # It is wired HERE because scripts/reachability_check.py caught `plan_status`
    # as a NEW unwired instrument minutes after it was written: its only consumer
    # was a paragraph in CLAUDE.md telling a reader to run it. That is the exact
    # defect the plan file was created to name — a queue whose consumer never
    # visits it — committed by the file that names it. The guard was right.
    try:
        import plan_status as PLAN
        plan = PLAN.load()
    except Exception as e:  # pragma: no cover - a missing plan must not stop a render
        print(f"PLAN: could not be read ({e}) — that is unknown, not fine")
    else:
        cur = PLAN.current(plan)
        done, total = PLAN.progress(plan)
        due, why = PLAN.review_due(plan)
        where = f"{cur['id']} — {cur['title']}" if cur else "ALL PHASES CLOSED"
        print(f"\nPLAN {plan.get('unit', '?')}: {where}  ({done}/{total} items)")
        for pid, w in PLAN.next_work(plan, n=2):
            print(f"PLAN   next: [{pid}/{w['id']}] {w['what'][:88]}")
        if due:
            print(f"PLAN   !! REVIEW OVERDUE — {why}; "
                  f"run plan_status.py --review (keep/change/drop per phase)")

    if v and hard:
        raise SystemExit("RULE GATE FAILED "
                         "(R10 / R7 / R2 / charter / coverage / continuity)")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--bundle", default=None)
    ap.add_argument("--lane", default=None,
                    help="lane dir holding gate-*.md, where the triage of "
                         "record actually lives (e.g. training/TRN-002)")
    ap.add_argument("--inbox", default=None)
    ap.add_argument("--manifest", default=None,
                    help="coverage manifest; defaults to "
                         "<lane>/coverage-manifest.json")
    ap.add_argument("--soft", action="store_true", help="report, do not exit 1")
    ap.add_argument("--require-seen", action="store_true",
                    help="R10 q2: every mass must point at itself in the reference")
    ap.add_argument("--renders", default=None,
                    help="dir of this unit's renders, for R1's full-frame count "
                         "(defaults to the reproduction bundle for a TRN unit)")
    ap.add_argument("--decisions", default=None,
                    help="owner decision registry (defaults to "
                         "qa/open-decisions.json)")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    # DERIVED, not required, for the same reason manifest_for is: a count that
    # only runs when the caller remembers to ask is a count that stops running.
    render_dir = a.renders
    if render_dir is None and a.lane:
        unit = os.path.basename(os.path.normpath(a.lane))
        guess = os.path.join(REPO_ROOT, "_private", "benchmark", "reproduction",
                             unit, "renders")
        render_dir = guess if os.path.isdir(guess) else None
    v = enforce(spec, a.bundle, a.inbox, hard=not a.soft,
                require_seen=a.require_seen, lane_dir=a.lane,
                spec_path=a.spec, manifest_path=a.manifest,
                render_dir=render_dir, decisions_path=a.decisions)
    # Was `0 if not v else 0` — the CLI could not exit nonzero, so no caller,
    # hook or CI step could ever have failed on it. --soft is the way to ask
    # for a report and keeps its promise of exit 0; the default is a gate.
    sys.exit(0 if a.soft else (1 if v else 0))


if __name__ == "__main__":
    main()
