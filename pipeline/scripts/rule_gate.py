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
ROUND_TOKEN = re.compile(r"_(r\d+[a-z]?)$", re.I)


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
TABLE_ROW = re.compile(r"^\s*\|\s*(\d{1,2})\s*\|")
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


def audit_bundle(bundle_dir, lane_dir=None):
    """R7 — every critic ITEM gets a WRITTEN triage. Returns [violation str]."""
    out = []
    if not os.path.isdir(bundle_dir):
        return [f"bundle dir not found: {bundle_dir}"]
    answers = sorted(glob.glob(os.path.join(bundle_dir, "ANSWER_*.md")))
    if not answers:
        return out                      # no critic has filed yet; nothing owed
    surfaces = [_gate_text(bundle_dir, lane_dir)]
    for extra in ("README.md",) + tuple(
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


def check(spec, bundle_dir=None, inbox_root=None, require_seen=False,
          lane_dir=None):
    v = audit_spec(spec, require_seen)
    if bundle_dir:
        v += audit_bundle(bundle_dir, lane_dir)
    if inbox_root:
        v += audit_learning(spec, inbox_root)
    return v


def enforce(spec, bundle_dir=None, inbox_root=None, hard=True, require_seen=False,
            lane_dir=None):
    """Print and, if hard, refuse to continue. Called by the builder."""
    v = check(spec, bundle_dir, inbox_root, require_seen, lane_dir)
    if not v:
        # Name what was checked, not just that nothing failed. A gate that
        # prints the same success line whether or not it ran a half of itself
        # is indistinguishable from a mute — which is exactly what the R7 half
        # was for every render of this lane until this line was written.
        ran = ["R10 spec"] + (["R7 triage"] if bundle_dir else []) + \
              (["charter distillation"] if inbox_root else [])
        print(f"RULE GATE: {len(spec.get('masses', []))} masses, all justified "
              f"[checked: {', '.join(ran)}]")
        if not bundle_dir:
            print("RULE GATE: !! R7 triage NOT checked (no bundle dir given)")
        return []
    print(f"\nRULE GATE: {len(v)} violation(s)")
    for s in v:
        print(f"  !! {s}")
    if hard:
        raise SystemExit("RULE GATE FAILED (R10 / R7 / charter)")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--bundle", default=None)
    ap.add_argument("--lane", default=None,
                    help="lane dir holding gate-*.md, where the triage of "
                         "record actually lives (e.g. training/TRN-002)")
    ap.add_argument("--inbox", default=None)
    ap.add_argument("--soft", action="store_true", help="report, do not exit 1")
    ap.add_argument("--require-seen", action="store_true",
                    help="R10 q2: every mass must point at itself in the reference")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    v = enforce(spec, a.bundle, a.inbox, hard=not a.soft,
                require_seen=a.require_seen, lane_dir=a.lane)
    # Was `0 if not v else 0` — the CLI could not exit nonzero, so no caller,
    # hook or CI step could ever have failed on it. --soft is the way to ask
    # for a report and keeps its promise of exit 0; the default is a gate.
    sys.exit(0 if a.soft else (1 if v else 0))


if __name__ == "__main__":
    main()
