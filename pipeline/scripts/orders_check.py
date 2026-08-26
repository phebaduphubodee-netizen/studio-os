#!/usr/bin/env python3
"""THE ORDERS OF RECORD — `qa/owner-orders.json`, and the rung that makes an
owner order something THE MACHINE HOLDS instead of something the builder
remembers.

WHY IT EXISTS, in the owner's own count (2026-08-16). He ordered the bed cloth
ACQUIRED rather than hand-simulated on 2026-08-14, and again on 2026-08-15
("เอาผ้าที่ปั้นเองออก แล้วเอาโมเดลเตียงที่หามาใส่ให้ดู"). On 2026-08-16 the
builder filed D-072 — `decided_by: "builder"` — putting the hand-built cloth
back as the default, and the next round went on tuning its numbers. Ten decision
rows in the register decide the same subject (r12, r17, r28, r29, r31, r32, r35,
r36, r41, r43) against an R8 stop-loss that says TWO.

Not one rung in this repo noticed, and the reason is exact rather than moral:

    HIS WORDS WERE IN THE REGISTER THE WHOLE TIME — IN A FIELD NO CHECKER READS.

`decisions_check` rule 4 locks a row to the owner once `owner_override` carries
his words. D-052 and D-054 quote his order in the `question` field and leave
`owner_override` null, so the lock never armed, `decided_by` stayed "builder",
and the row remained re-decidable by the same builder who wrote it. The lock was
built; the order was filed outside it. `build_room.py` states the case at its
sharpest — line 1651 says "the bed cloth is ACQUIRED, not simulated … owner
order 2026-08-14" and line 1668 reads `_BED_CLOTH_ACQ = False`. The order is
quoted in a comment seventeen lines above the code that disobeys it.

So an order is now a ROW, and a row is checkable:

  1. VERBATIM MUST REPRODUCE.   `recorded_at` names a file that still contains
                                his exact words. An order I cannot point at is
                                an order I am paraphrasing — R10's "point at it
                                or it does not exist", applied to what he said.

  2. AN ORDER MUST NAME WHERE   `obeyed_where` is the same test `decisions_check`
     IT IS OBEYED, AND THE      applies to `where`: an order in force nowhere was
     PLACE MUST EXIST.          never carried out.

  3. THE REPO IS ASSERTED       `obeyed_assert` greps the actual file for the
     AGAINST THE CODE, NOT      state the order commands. This is the rung that
     AGAINST A PARAGRAPH.       reads `_BED_CLOTH_ACQ = False` and fails, where
                                every declaration-reading rung read the comment
                                above it and passed. Unreadable file = violation,
                                never a pass: could-not-look must not print like
                                looked-and-it-was-fine (R11's exit-2 law).

  4. NO BUILDER DECISION MAY    A decision row on a governed subject declares
     CONTRADICT A STANDING      `obeys` or `contradicts`. `contradicts` with
     ORDER.                     `decided_by: "builder"` is refused BY NAME. He
                                may change his own mind — that is an owner row
                                with new words and a later date. The builder may
                                not do it for him with a measurement.

  5. AN ORDER IN PROSE IS NOT   A row whose text reports an order ("พี่สั่ง",
     AN ORDER TO THE MACHINE.   "คำสั่งพี่", …) and takes no stance is the exact
                                shape of D-052. Refused by name.

  6. THE STOP-LOSS IS A         R1 says two rounds, R8 says two shape iterations,
     COUNTER, NOT A SENTENCE.   and nothing in this repo counted. Decisions per
                                subject are counted here; three on a subject he
                                has already ruled on is the lane re-deciding what
                                he decided, which is what actually happened ten
                                times.

WHAT THIS RUNG IS NOT: it does not wait for him, ask him anything, or block on
anything he owes — R3 stands ("เอาผมออกจาก gate เลย ไม่ต้องรอผม"). Every
violation here is the BUILDER's side: an order quoted and not carried out, a
subject re-decided, a contradiction filed under the builder's own name. The
owner never appears in the failing half.

LAYER LAW: pure Python, no `bpy`, no PIL, no network.
"""

import argparse
import datetime
import json
import os
import re
import sys

ORDERS_REL = "qa/owner-orders.json"

REQUIRED = ("id", "date", "recorded_at", "commands", "subject", "standing")

# `verbatim` is NOT in REQUIRED, and the exception is deliberate. Some of his
# orders survive only as a paraphrase in a builder's note — the 2026-08-08
# build-order rule is one. The wrong repair is to reconstruct a sentence in his
# voice and store it as his; the right one is an empty `verbatim` plus
# `verbatim_absent_because`, so the row still governs and nobody can quote it
# back to him as something he said.

# THE THIRD STATE, and the reason it is not a loophole. A fan-out over this
# repo's own history on 2026-08-16 found EIGHT orders in the shape the bed cloth
# made famous — R11 declared "structurally inapplicable" on the only lane being
# built; the R1 cap declared not-applicable with no DELIV-001 row ever added to
# the caps file; "delete every hand-built loose piece" narrowed to one class;
# his "สเกลดูแปลก" verdict parked behind `_ADULT_SCALE = False`; the same for
# `_DUVET_TUCKS`; gen-diff, his own idea approved with "ลุย", run twice and then
# silently absent for thirteen rounds. THE COMMON SHAPE IS ONE SENTENCE:
#
#     AN ORDER CARRIED OUT AS AN OPT-IN IS AN ORDER THAT WAS NOT CARRIED OUT,
#     BECAUSE NOBODY TYPES THE FLAG.
#
# A machine that hard-fails every one of those on the day it ships halts the
# lane, gets switched off, and joins them. So an order may be recorded
# NOT-OBEYED — loudly, with a date so its age prints, and with exactly one of:
#   `blocked_by`   an OPEN row in qa/owner-asks.json — something only HE can
#                  unblock (money, his eye, a signature). Honest.
#   `restart_by`   a named, concrete builder action. This is a DEBT, printed at
#                  every gate and every session open until it is paid.
# What it may never be is silent, and what it may never do is print as obeyed.
STATUSES = ("obeyed", "not-obeyed")

# The phrases that REPORT an order. Deliberately tight, and one omission is
# load-bearing: "พี่ overrule" is this repo's standard closing line ("he can
# overrule from the image"), present on rows that cite no order at all — a
# marker list that catches it would fire on six innocent rows and be switched
# off within a week, which is how a guard dies.
ORDER_MARKERS = ("พี่สั่ง", "คำสั่งพี่", "คำสั่งของพี่", "คำสั่งเจ้าของ",
                 "เจ้าของสั่ง", "พี่บอกว่า", "owner order", "owner ordered",
                 "ตามคำสั่งพี่")

# Three builder decisions on one subject he has already ruled on. R1 says two
# cycles per mechanism, R8 says two shape iterations and that a third means the
# class was misclassified. The bed cloth got ten.
STOP_LOSS = 3

# --- THE VISUAL-CLOSURE LAW (2026-08-26, debate proposal 1, owner-approved) ---
# What it ends, in one night's count: gate-P2r75 printed all five of his items
# "ลงพิกเซลครบ" with every rung green — the closer typed the fix, read its own
# crop of its own quick render, wrote "verified", and the register printed
# obeyed. Hours later he refuted three closures from the frame, and the item
# that failed was the ONE of five with no obeyed_assert at all. A visual order
# therefore closes on PIXELS SOMEONE ELSE POINTED AT, never on the closer's
# prose: `visual: true` rows claiming "obeyed" must carry `closure_verdicts` —
# files written by a fresh-context sighted verifier who received ONLY the
# owner's sentence and the full-fidelity frame, and answered with an annotated
# crop (arrow on the satisfying pixels) or NOT-VISIBLE. His own words on the
# frame close a row too (they ARE a verdict; record them in the file). A
# verdict later `overturned` by a MEASUREMENT no longer supports the closure —
# the same night this landed, the verifier read the nightstands' blank framed
# BACKS as drawer fronts and the front probe overturned it: the eye finds WHAT,
# the measurement finds WHICH WAY (R7b's law, applied to the verifier itself).
VISUAL_RATCHET_FROM = "2026-08-26"
# The closing phrase of the self-judged era, refused by name in gate artifacts
# the way "พร้อมให้ตัดสิน" already is. Gates print BUILT + evidence; the owner
# or the verifier says closed.
BANNED_CLOSURE_PHRASES = ("ลงพิกเซลครบ",)


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def load(path=None, repo_root=None):
    """The ledger, or None. Never raises — an unreadable ledger in the render
    path must produce a violation that NAMES the file, not a traceback. A crash
    reads as a broken tool and gets worked around; a violation gets fixed."""
    p = path or os.path.join(repo_root or _repo_root(), ORDERS_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def orders(data, standing_only=False, subject=None, unit=None):
    rows = (data or {}).get("orders")
    if not isinstance(rows, list):
        return []
    out = [o for o in rows if isinstance(o, dict)]
    if standing_only:
        out = [o for o in out if o.get("standing")]
    if subject is not None:
        out = [o for o in out if o.get("subject") == subject]
    if unit is not None:
        # An order with no `units` key governs every lane — his orders are about
        # the studio, not about a directory. Scoping is opt-in and explicit.
        out = [o for o in out if not o.get("units") or unit in o["units"]]
    return out


def _paths(where):
    if not isinstance(where, str):
        return []
    return [p.strip() for p in where.split(",") if p.strip()]


def _read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _norm(s):
    """Whitespace-collapsed, for quote matching only. A quote that survives a
    line-wrap in one file and not another is still his sentence; a quote whose
    WORDS changed is not, and this does not hide that."""
    return re.sub(r"\s+", " ", (s or "")).strip()


def _bare(s):
    """Every space removed. THAI HAS NO INTER-WORD SPACES, so a line wrap inside
    one of his sentences puts a space in the middle of a WORD — "ผมขอบังคับ\\n
    ให้ทุกกลไก" unwraps to "ผมขอบังคับ ให้ทุกกลไก", which is not what he typed
    and is also not a change to what he said. Whitespace-collapsing alone
    reported his 2026-08-09 order as missing from the file it is quoted in.
    Compared last, so a real edit to his words still fails."""
    return re.sub(r"\s+", "", (s or ""))


def _find(text, needle):
    """(line number, True) if the words are in the text, else (None, False)."""
    if not text or not needle:
        return None, False
    if needle in text:
        return text[:text.index(needle)].count("\n") + 1, True
    nt, nn = _norm(text), _norm(needle)
    if nn and nn in nt:
        return None, True          # found, but only after unwrapping
    bt, bn = _bare(text), _bare(needle)
    if bn and bn in bt:
        return None, True          # found across a line break inside a word
    return None, False


# ------------------------------------------------------------------ the ledger

def check_orders(data, repo_root=None, path_hint=ORDERS_REL):
    """Violations in the ORDERS file itself: an order I cannot point at, an
    order in force nowhere, an order the code does not actually carry out."""
    if data is None:
        return [f"no readable orders ledger at {path_hint}. His orders are the "
                f"one input to this lane that the builder may not re-decide; "
                f"losing the file does not make them go away, it makes them "
                f"unenforceable."]
    root = repo_root or _repo_root()
    v, seen = [], set()

    for o in orders(data):
        oid = o.get("id") or "<no id>"
        if oid in seen:
            v.append(f"{oid}: duplicate order id. Two rows with one id means "
                     f"`obeys`/`contradicts` on a decision points at both.")
        seen.add(oid)

        missing = [k for k in REQUIRED if o.get(k) in (None, "", [], {})
                   and not (k == "standing" and o.get(k) is False)]
        if missing:
            v.append(f"{oid}: order row is missing {', '.join(missing)}.")
            continue

        # 1. HIS WORDS MUST STILL REPRODUCE WHERE THE ROW SAYS THEY ARE.
        hits, unread = [], []
        for rel in _paths(o.get("recorded_at")):
            txt = _read(root, rel)
            if txt is None:
                unread.append(rel)
                continue
            line, ok = _find(txt, o.get("verbatim"))
            if ok:
                hits.append(f"{rel}:{line}" if line else rel)
        if not o.get("verbatim"):
            if not o.get("verbatim_absent_because"):
                v.append(f"{oid} stores no `verbatim` and no "
                         f"`verbatim_absent_because`. An order with no words "
                         f"and no account of why is a rule the builder wrote "
                         f"and attributed upward.")
        elif not hits:
            where = ", ".join(_paths(o.get("recorded_at"))) or "(nowhere)"
            v.append(f"{oid}: the words this order stores do not appear in "
                     f"{where}"
                     + (f" (unreadable: {', '.join(unread)})" if unread else "")
                     + ". An order I cannot point at is an order I am "
                       "paraphrasing, and a paraphrase is the builder's "
                       "sentence wearing his name.")

        # 2. AN ORDER IN FORCE NOWHERE WAS NEVER CARRIED OUT.
        st = o.get("status", "obeyed")
        if st not in STATUSES:
            v.append(f"{oid}: status {st!r} is not one of "
                     f"{', '.join(STATUSES)}.")
        if st == "obeyed" and not o.get("obeyed_where"):
            v.append(f"{oid}: claims to be obeyed and names no `obeyed_where`.")
        for rel in _paths(o.get("obeyed_where")):
            if not os.path.exists(os.path.join(root, rel)):
                v.append(f"{oid}: `obeyed_where` names {rel}, which does not "
                         f"exist. Same test as a decision's `where`: an order "
                         f"obeyed nowhere was written down instead of obeyed.")

        # 3. THE ASSERTION AGAINST THE CODE — the rung that reads the line
        #    instead of the comment above it.
        broken = _assert_violations(oid, o, root)
        if st == "obeyed":
            v += broken
        elif not broken and o.get("obeyed_assert") and not o.get("visual"):
            # A VISUAL row is exempt from this pessimism check on purpose: its
            # source asserts prove the code was typed, and the p2r75 night
            # proved that is not the same fact as the frame changing — a
            # visual row goes not-obeyed on a NOT-VISIBLE verdict while every
            # grep it carries still holds, and that state is the honest one.
            v.append(f"{oid} is filed NOT-OBEYED while every assertion it "
                     f"carries holds. Say it is obeyed, or the record is "
                     f"pessimistic in a way that makes the honest rows unreadable.")

        # 3b. NOT-OBEYED HAS TO NAME A ROUTE BACK, AND A DATE TO AGE FROM.
        if st == "not-obeyed":
            if not o.get("not_obeyed_because"):
                v.append(f"{oid} is NOT-OBEYED with no `not_obeyed_because`.")
            if not o.get("since"):
                v.append(f"{oid} is NOT-OBEYED with no `since` date, so nothing "
                         f"can print how long his order has gone uncarried-out "
                         f"— and age is the only pressure this state carries.")
            blocked, restart = o.get("blocked_by"), o.get("restart_by")
            if not (blocked or restart):
                v.append(f"{oid} is NOT-OBEYED with neither `blocked_by` (an "
                         f"open ask only HE can clear) nor `restart_by` (a "
                         f"named builder action). An order with no route back "
                         f"is a dropped order wearing a status.")
            if blocked and not _ask_is_open(root, blocked):
                v.append(f"{oid} is blocked_by {blocked}, which is not an OPEN "
                         f"row in qa/owner-asks.json. 'Waiting on him' has to "
                         f"name the thing he is actually holding, or it is the "
                         f"builder's own decision to disobey wearing his name.")

        # 7. A VISUAL ORDER CLOSES ON POINTED-AT PIXELS, NEVER ON THE CLOSER'S
        #    PROSE (the p2r75 night: five "closed" items, three refuted by his
        #    eye in hours, the failing one the only one with no assert).
        if o.get("visual"):
            if st == "obeyed":
                v += _verdict_violations(oid, o, root)
        elif o.get("scope") == "instance-list" and "visual" not in o \
                and str(o.get("date", "")) >= VISUAL_RATCHET_FROM:
            v.append(f"{oid}: an itemized instance-list order filed after "
                     f"{VISUAL_RATCHET_FROM} must declare `visual` true/false "
                     f"explicitly — an opt-in flag nobody types is an order "
                     f"that was not carried out (R13's own sentence).")

        # 4. ONLY HE MAY RETIRE HIS OWN ORDER.
        if not o.get("standing"):
            rb = o.get("retired_by")
            if not rb:
                v.append(f"{oid} is marked not standing with no `retired_by`. "
                         f"An order does not lapse; it is retired by him, in a "
                         f"row that carries his words.")
            elif not str(rb).startswith("D-"):
                v.append(f"{oid}: `retired_by` is {rb!r}, which is not a "
                         f"decision row id. Retirement is a decision he made, "
                         f"and it has to be findable.")

    # THE CLOSURE GRAMMAR travels with the ledger check so every caller gets it
    # (rule_gate.owner_channel calls check_orders directly, not check()).
    v += check_gate_grammar(root)
    return v


def _verdict_violations(oid, o, root):
    """The visual-closure rungs. FAILS CLOSED: an unreadable verdict file is a
    check that did not run, and 'could not look' must never print like 'looked
    and it was fine' (R11's exit-2 law, applied to the verifier's own record)."""
    v = []
    cvs = o.get("closure_verdicts") or []
    if not cvs:
        v.append(f"{oid} is a VISUAL order claiming obeyed with no "
                 f"`closure_verdicts`. Source-greps prove the code was typed, "
                 f"not that the frame changed — his words on the frame, or a "
                 f"blind sighted verifier's arrowed crop, are the only closure "
                 f"evidence for an order about what he SEES.")
        return v
    for rel in _paths(",".join(cvs) if isinstance(cvs, list) else cvs):
        p = os.path.join(root, rel)
        try:
            with open(p, encoding="utf-8") as f:
                vd = json.load(f)
        except (OSError, ValueError):
            v.append(f"{oid}: closure verdict {rel} is unreadable — UNKNOWN, "
                     f"not obeyed.")
            continue
        if vd.get("overturned"):
            v.append(f"{oid}: verdict {rel} was OVERTURNED by a measurement "
                     f"({str(vd['overturned'])[:90]}…) and no longer supports "
                     f"the closure. Re-run the verifier on the frame that "
                     f"carries the fix.")
        elif vd.get("verdict") != "VISIBLE":
            v.append(f"{oid}: verdict {rel} says {vd.get('verdict')!r} — the "
                     f"verifier could not point at pixels satisfying his "
                     f"sentence, so the row may not print obeyed. His words: "
                     f"\"{_norm(vd.get('owner_sentence'))[:60]}\"")
    return v


def check_gate_grammar(root, since=VISUAL_RATCHET_FROM):
    """Gate artifacts written from `since` onward may not close a visual item
    in prose: the closing phrase of the self-judged era is refused by name,
    exactly the way 'พร้อมให้ตัดสิน' was retired. A gate says BUILT and shows
    evidence; the owner or the verifier says closed."""
    import glob as _glob
    v = []
    for p in _glob.glob(os.path.join(root, "projects", "*",
                                     "04_visualization", "gate-*.md")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})\.md$", os.path.basename(p))
        if not m or m.group(1) < since:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        except (OSError, UnicodeDecodeError):
            v.append(f"gate artifact {os.path.basename(p)} is unreadable — "
                     f"could not check its closure grammar.")
            continue
        for phrase in BANNED_CLOSURE_PHRASES:
            if phrase in txt:
                v.append(f"gate artifact {os.path.basename(p)} closes in "
                         f"prose ({phrase!r}) — refused by name since "
                         f"{since}. Print BUILT + evidence; closure belongs "
                         f"to his words or a sighted verdict file "
                         f"(closure_verdicts).")
    return v


def _ask_is_open(root, ask_id):
    """Is `ask_id` an OPEN row in the ask ledger? Cross-module by design: the
    two files are the two directions of one channel, and 'blocked on him' is
    only true if the thing he is holding is written down where he can see it."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import asks_check as ASK
        data = ASK.load(repo_root=root)
    except Exception:                                   # pragma: no cover
        return False
    return any(a.get("id") == ask_id and a.get("status") == "open"
               for a in ASK.asks(data))


def _assert_violations(oid, o, root):
    """Grep the repo for the state the order commands. FAILS CLOSED: a file that
    cannot be read is a check that did not run, and 'could not look' must never
    print like 'looked and it was fine' (R11's exit-2 law, applied to text)."""
    v = []
    for a in (o.get("obeyed_assert") or []):
        rel, pat = a.get("file"), a.get("pattern")
        why = a.get("why") or ""
        if not rel or not pat:
            v.append(f"{oid}: an `obeyed_assert` entry names no file/pattern, "
                     f"so it asserts nothing while looking like a check.")
            continue
        txt = _read(root, rel)
        if txt is None:
            v.append(f"{oid}: could not read {rel} to check whether the repo "
                     f"obeys this order. That is UNKNOWN, not obeyed.")
            continue
        try:
            found = re.search(pat, txt, re.M) is not None
        except re.error as e:
            v.append(f"{oid}: `obeyed_assert` pattern for {rel} will not "
                     f"compile ({e}) — a check that cannot run is not a check.")
            continue
        if a.get("absent"):
            if found:
                v.append(f"{oid}: {rel} still matches /{pat}/, which this order "
                         f"forbids. {why}")
        elif not found:
            v.append(f"{oid}: {rel} does not match /{pat}/ — THE REPO DOES NOT "
                     f"OBEY THIS ORDER. {why} His words: \"{o.get('verbatim')}\"")
    return v


# --------------------------------------------------------------- the decisions

def _blob(d):
    return " ".join(str(d.get(k) or "") for k in
                    ("question", "in_effect", "because", "reverse_by"))


def governed(data, unit=None):
    """{subject: [order, ...]} for standing orders only."""
    out = {}
    for o in orders(data, standing_only=True, unit=unit):
        out.setdefault(o.get("subject"), []).append(o)
    return out


def check_decisions(data, decisions, unit=None, repo_root=None):
    """Violations in the DECISION register, judged against his standing orders.

    Every one of these is the builder's side of the bargain. Nothing here can
    fail because the owner has not answered something.

    TWO DESIGN CHOICES THAT KEEP THIS RUNG ALIVE, both learned from guards this
    repo has had to switch off:

      * A row is judged against an order only if it was FILED AFTER IT. A stance
        demanded of a row written before the order existed is an anachronism,
        and a guard that demands the impossible gets deleted.
      * A SUPERSEDED row is history, not a live contradiction. Rows never leave
        this ledger, so without that the register would carry a permanent
        violation nothing could clear — which is the same as no violation.
    """
    if data is None or decisions is None:
        return []                        # the missing-file violation is above
    root = repo_root or _repo_root()
    rows = [d for d in (decisions.get("decisions") or [])
            if isinstance(d, dict) and (unit is None or d.get("unit") == unit)]
    gov = governed(data, unit=unit)
    by_id = {o.get("id"): o for o in orders(data)}
    ratchet = (data or {}).get("_subject_ratchet_from")
    v, counts = [], {}

    for d in rows:
        did = d.get("id") or "<no id>"
        subj = d.get("subject")
        stance_obeys = d.get("obeys")
        stance_contra = d.get("contradicts")
        stance = stance_obeys or stance_contra or d.get("owner_override")
        superseded = d.get("superseded_by")

        # 5. AN ORDER IN PROSE IS NOT AN ORDER TO THE MACHINE — D-052's shape.
        #    Ratcheted: rows filed from `_subject_ratchet_from` onward fail,
        #    older ones are counted and printed. The test suite runs it against
        #    the REAL D-052 as a negative control, so "it would have caught it"
        #    is a measurement rather than a claim.
        marks = [m for m in ORDER_MARKERS if m in _blob(d)]
        if marks and not stance:
            # NO RATCHET KEY MEANS EVERY ROW, not no rows. A missing config key
            # that silently disables a rung is the shape this whole file exists
            # to end; fail closed and let the noise say the key is gone.
            if ratchet is None or did >= ratchet:
                v.append(f"{did} reports an owner order in prose ({marks[0]!r}) "
                         f"and takes no stance on it. That is exactly how D-052 "
                         f"and D-054 stored his bed-cloth order: his words in "
                         f"the `question` field, `owner_override` null, the row "
                         f"left re-decidable by the builder who wrote it. File "
                         f"the order in {ORDERS_REL} and name it in `obeys`.")
            # older rows are BACKFILL DEBT — see prose_debt(), printed not failed

        # A STANCE IS ONE ORDER ID, AND A MALFORMED ONE IS REPORTED, NOT RAISED.
        # Written 2026-08-17 after a row filed `obeys` as a LIST of two ids and
        # this loop died on `unhashable type: 'list'` — a blocking gate module
        # taken out by a TypeError. `score_exit_policy` already records why that
        # is the dangerous shape: python exits 1 on an uncaught exception and 1
        # is this tool's code for "ran and found violations", so a crashed rung
        # reads exactly like a completed one. Two orders on one row is also a
        # real question the row has not answered — which one governs the subject
        # if they ever diverge — so it is refused rather than quietly reduced.
        for oid in [x for x in (stance_obeys, stance_contra) if x]:
            if not isinstance(oid, str):
                v.append(f"{did} files a stance as {type(oid).__name__} "
                         f"({oid!r}). A stance is ONE order id: if two orders "
                         f"govern this row, say which one decides the subject "
                         f"and record the other in `because`.")
                continue
            if oid not in by_id:
                v.append(f"{did} names order {oid}, which is not in "
                         f"{ORDERS_REL}. A stance on an order nobody recorded "
                         f"is a stance on nothing.")

        # 4. THE BUILDER MAY NOT OVERRULE HIM WITH A MEASUREMENT.
        if stance_contra and not superseded:
            o = by_id.get(stance_contra)
            if d.get("decided_by") != "owner":
                v.append(f"{did} contradicts {stance_contra} and is "
                         f"decided_by='{d.get('decided_by')}'. HE ORDERED: "
                         f"\"{(o or {}).get('verbatim', '?')}\" — only he "
                         f"reverses that, from the image, in a row carrying new "
                         f"words and a later date. A measured advantage on one "
                         f"component is not a reversal; it is a second thing to "
                         f"acquire.")
            elif not d.get("owner_override"):
                v.append(f"{did} contradicts {stance_contra} as an owner row "
                         f"but carries no `owner_override` text. The builder "
                         f"may not sign for him.")

        # A row on a governed subject has to say which way it goes — but only
        # if the order was already given when the row was filed.
        if subj and subj in gov and not stance:
            after = [o for o in gov[subj]
                     if str(d.get("decided_date") or "") >= str(o.get("date"))]
            if after:
                oids = ", ".join(o.get("id") for o in after)
                v.append(f"{did}: subject '{subj}' is governed by a standing "
                         f"order ({oids}) and this row names neither `obeys` "
                         f"nor `contradicts`. A decision that does not know it "
                         f"is governed is how the tenth one gets taken.")

        if subj:
            counts.setdefault(subj, []).append(d)

    # 6. THE STOP-LOSS AS A COUNTER — and it counts ROUNDS SPENT NOT OBEYING.
    #    It fires only while the order is actually broken, so carrying the order
    #    out clears it. A counter that can never be cleared is a counter that
    #    gets commented out, which is how this repo lost guards before.
    for subj, ds in sorted(counts.items()):
        for o in gov.get(subj, []):
            if not _assert_violations(o.get("id"), o, root):
                continue                 # this order is obeyed; nothing to count
            mine = [d for d in ds
                    if d.get("decided_by") != "owner"
                    and str(d.get("decided_date") or "") >= str(o.get("date"))]
            if len(mine) >= STOP_LOSS:
                v.append(f"STOP-LOSS: '{subj}' carries {len(mine)} builder "
                         f"decisions ({', '.join(d.get('id') for d in mine)}) "
                         f"taken since {o.get('id')} was given, and that order "
                         f"is STILL NOT OBEYED. R1 allows two cycles per "
                         f"mechanism and R8 says a third means the CLASS was "
                         f"misclassified, not that the shape needs more tuning. "
                         f"Carry the order out — deciding it a "
                         f"{len(mine) + 1}th time is the defect, not the fix.")
    return v


def prose_debt(data, decisions, unit=None):
    """Row ids that quote an order in prose with no stance and pre-date the
    ratchet. PRINTED, never blocking — each one is an order the machine still
    cannot hold, and the count going up is the thing to notice."""
    ratchet = (data or {}).get("_subject_ratchet_from")
    out = []
    for d in ((decisions or {}).get("decisions") or []):
        if not isinstance(d, dict) or (unit is not None and d.get("unit") != unit):
            continue
        did = str(d.get("id") or "")
        if d.get("obeys") or d.get("contradicts") or d.get("owner_override"):
            continue
        if any(m in _blob(d) for m in ORDER_MARKERS):
            if not (ratchet and did >= ratchet):
                out.append(did)
    return out


def subject_tally(decisions, unit=None):
    """[(subject, n, ids)] worst first — printed so a subject being re-decided
    is visible before it reaches the stop-loss, on EVERY subject, governed or
    not. The counter that only counts governed subjects cannot see the next
    thing he has not gotten around to ordering."""
    rows = [d for d in ((decisions or {}).get("decisions") or [])
            if isinstance(d, dict) and (unit is None or d.get("unit") == unit)]
    t = {}
    for d in rows:
        if d.get("subject"):
            t.setdefault(d["subject"], []).append(d.get("id"))
    return sorted(((s, len(ids), ids) for s, ids in t.items()),
                  key=lambda r: (-r[1], r[0]))


def unsubjected(decisions, unit=None, ratchet_from=None):
    """Rows carrying no `subject`. THE RATCHET: rows filed from `ratchet_from`
    onward must carry one, older rows are backfill debt that PRINTS. Copied from
    the spec-ratchet (DRW-5) because it is the shape that actually shipped —
    a migration demanded all at once is a migration abandoned."""
    rows = [d for d in ((decisions or {}).get("decisions") or [])
            if isinstance(d, dict) and (unit is None or d.get("unit") == unit)]
    debt, new = [], []
    for d in rows:
        if d.get("subject"):
            continue
        did = str(d.get("id") or "")
        if ratchet_from and did >= ratchet_from:
            new.append(did)
        else:
            debt.append(did)
    return new, debt


# ------------------------------------------------------------------- reporting

def check(data, decisions, unit=None, repo_root=None, path_hint=ORDERS_REL):
    v = check_orders(data, repo_root, path_hint)
    v += check_decisions(data, decisions, unit, repo_root)
    new, _ = unsubjected(decisions, unit,
                         (data or {}).get("_subject_ratchet_from"))
    for did in new:
        v.append(f"{did}: filed after the subject ratchet opened and carries no "
                 f"`subject`, so no counter can see it. A decision that cannot "
                 f"be counted is a decision that can be taken ten times.")
    return v


def obedience(data, repo_root=None, today=None):
    """[(order, ok, detail)] — what the repo actually does about each standing
    order, recomputed from the files every run. Three states, never two: a
    NOT-OBEYED order reports its age and what it is waiting on, because the way
    these die is by looking like the obeyed ones from a distance."""
    root = repo_root or _repo_root()
    today = today or datetime.date.today()
    out = []
    for o in orders(data, standing_only=True):
        bad = _assert_violations(o.get("id"), o, root)
        n = len(o.get("obeyed_assert") or [])
        if o.get("status") == "not-obeyed":
            try:
                age = (today - datetime.date.fromisoformat(
                    str(o.get("since")))).days
                aged = f"{age}d"
            except (ValueError, TypeError):
                aged = "age unknown"
            waiting = o.get("blocked_by") or o.get("restart_by") or "nothing named"
            out.append((o, False, f"NOT OBEYED [{aged}] — {waiting}"))
            continue
        detail = (f"{n} assertion(s) hold" if not bad and n
                  else "NO ASSERTION — obedience is only declared" if not n
                  else f"{len(bad)} BROKEN")
        out.append((o, not bad, detail))
    return out


def one_line(o, ok=None, detail=""):
    mark = "" if ok is None else ("  ✓ " if ok else "  !! ")
    return (f"  {o.get('id')} [{o.get('date')}] \"{_norm(o.get('verbatim'))[:70]}\"\n"
            f"      → {o.get('commands')}{mark}{detail}")


def main():
    ap = argparse.ArgumentParser(
        description="His standing orders, and whether the repo obeys them. "
                    "Exits 1 when an order is quoted and not carried out.")
    ap.add_argument("--unit", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--decisions", default=None)
    ap.add_argument("--subjects", action="store_true",
                    help="print the per-subject decision counter")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                   # pragma: no cover
        pass

    root = _repo_root()
    data = load(a.file)
    try:
        with open(a.decisions or os.path.join(root, "qa/open-decisions.json"),
                  encoding="utf-8") as f:
            dec = json.load(f)
    except (OSError, ValueError):
        dec = None

    v = check(data, dec, a.unit, root, a.file or ORDERS_REL)
    print("คำสั่งพี่ที่ยังมีผล — ผมทำตามหรือยัง (STANDING ORDERS, and whether "
          "the repo obeys them):")
    for o, ok, detail in obedience(data):
        print(one_line(o, ok, detail))
    if not orders(data, standing_only=True):
        print("  (none)")

    if a.subjects:
        print("\nDECISIONS PER SUBJECT (the stop-loss counter):")
        for s, n, ids in subject_tally(dec, a.unit)[:15]:
            flag = "  <-- STOP-LOSS" if n >= STOP_LOSS else ""
            print(f"  {n:>2}  {s}  ({', '.join(ids)}){flag}")
        new, debt = unsubjected(dec, a.unit,
                                (data or {}).get("_subject_ratchet_from"))
        print(f"  subject backfill debt: {len(debt)} row(s) no counter can see"
              + (f"; {len(new)} NEW row(s) missing one" if new else ""))

    for s in v:
        print(f"  !! {s}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
