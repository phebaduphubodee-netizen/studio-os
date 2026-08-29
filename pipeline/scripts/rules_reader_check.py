"""rules_reader_check.py — DOES ANYTHING ACTUALLY READ THE RULE. PURE (no bpy, no PIL).

    python pipeline/scripts/rules_reader_check.py [--update-baseline]

WHY THIS FILE EXISTS
--------------------
2026-08-29. An island was built a quarter turn out of true, leaving a NEGATIVE
420 mm walkway — two solids in the same place — and after the correction it left
1094 mm, which is short of this studio's own comfort figure. Both verdicts were
already on this disk, in two places, months old:

    pipeline/scripts/dimensional_rules.v0.2.json  ->  kitchen_NKBA, 7 keys
    knowledge/ergonomics/residential-clearances.md ->  "opposing counters — single
                                                        cook, no circulation
                                                        behind: 1219 mm"

Neither had a reader. `clearance_check.py` LOADS that JSON at import and had never
looked at the kitchen block. The audit that morning:

    **51 of 75 rule keys had no reader in any script in this repo.**
    Whole blocks at zero: kitchen_NKBA 7/7, bathroom 6/6, anthropometric_basics 5/5,
    doors_and_openings 4/4.

This is the repo's oldest defect wearing a new hat. CLAUDE.md already records it at
three other layers — 357 critic items filed against ~22 built, 61 DR units with 39
write-only, 21 gate artifacts with 2 owner verdicts, six skills that fired for two
days and then went 54 days unused — and names the shape: **a queue whose consumer
never visits it does not become correct by acquiring more entries.** A rules file is
a queue. Adding a number to it feels like building a guard and is not one.

WHAT THIS CHECKS
----------------
Every leaf key in the rules JSON, against every `.py` in the script dirs, looking
for the key as a quoted string. Three states:

    READ        a non-test script quotes it
    TEST-ONLY   only a test_*.py quotes it  -> counted as UNREAD
    UNREAD      nothing quotes it

TEST-ONLY IS UNREAD ON PURPOSE. A rule that only a test consults is a rule no gate
consults, which is the exact defect this file is about, one level in. A green test
suite over a rule nothing enforces is the most convincing possible way to be wrong.

THE RATCHET
-----------
`qa/rules-reader-baseline.json` holds the ids allowed to be unread today. It may
SHRINK and may never GROW. Two things therefore fail:

  * a key that HAD a reader and lost one (someone deleted the only consumer), and
  * **a NEW key added to the rules file with no reader.** That is the load-bearing
    half. Without it, writing a number into the rules file stays the cheapest way
    to feel like a guard was built. R13's sentence, one layer down: an order
    carried out as an opt-in is an order that was not carried out, because nobody
    types the flag — and a rule with no reader is a rule nobody types.

WHAT IT CANNOT DO, said plainly. It greps for a quoted key, so a key named in a
comment or a docstring counts as read. It cannot tell a reader that RUNS from one
sitting behind a branch nothing takes. It is a floor, not a proof: it makes the
number of unread rules visible and monotone, and visible-and-monotone is what the
other four instances of this defect never had.
"""
import argparse
import glob
import json
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
RULES = os.path.join(HERE, "dimensional_rules.v0.2.json")
BASELINE = os.path.join(REPO, "qa", "rules-reader-baseline.json")
SCAN_GLOBS = ("pipeline/scripts/*.py", "scripts/*.py")


def leaf_keys(rules):
    """(block, key) for every rule the file actually states.

    Only two levels deep: the file's own shape is block -> key -> {in, cm, note}.
    Keys starting with `_` are metadata (`_meta`, `_note`, `_ref`) and are not rules.
    """
    out = []
    for blk, node in rules.items():
        if blk.startswith("_") or not isinstance(node, dict):
            continue
        for key in node:
            if not key.startswith("_"):
                out.append((blk, key))
    return out


def sources(repo=REPO):
    """{path: text} for every script that could plausibly consume a rule."""
    out = {}
    for g in SCAN_GLOBS:
        for p in glob.glob(os.path.join(repo, g)):
            base = os.path.basename(p)
            if base == "rules_reader_check.py":
                continue          # this file names every key; it consumes none
            try:
                out[p] = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                pass
    return out


def audit(rules, src):
    """Return rows [{id, state, readers}] — pure, no I/O, no exit."""
    rows = []
    for blk, key in leaf_keys(rules):
        pat = re.compile(r"""["']""" + re.escape(key) + r"""["']""")
        prod, test = [], []
        for p, text in src.items():
            if not pat.search(text):
                continue
            (test if os.path.basename(p).startswith("test_") else prod).append(
                os.path.basename(p))
        if prod:
            state = "READ"
        elif test:
            state = "TEST-ONLY"
        else:
            state = "UNREAD"
        rows.append({"id": f"{blk}.{key}", "state": state,
                     "readers": sorted(prod) or sorted(test)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default=RULES)
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--update-baseline", action="store_true",
                    help="rewrite the baseline to today's unread set. REFUSES to grow "
                         "it — use only after wiring a rule up")
    ap.add_argument("--soft", action="store_true", help="report, exit 0")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    rules = json.loads(open(a.rules, encoding="utf-8").read())
    rows = audit(rules, sources())
    unread = {r["id"] for r in rows if r["state"] != "READ"}
    total = len(rows)

    try:
        base = set(json.loads(open(a.baseline, encoding="utf-8").read())["unread"])
        have_base = True
    except (OSError, KeyError, ValueError):
        base, have_base = set(), False

    print(f"RULES READERS: {total - len(unread)} of {total} rule keys have a reader "
          f"({len(unread)} unread)")
    by_block = {}
    for r in rows:
        if r["state"] != "READ":
            by_block.setdefault(r["id"].split(".")[0], []).append(r["id"].split(".")[1])
    for blk, keys in sorted(by_block.items()):
        n_blk = sum(1 for r in rows if r["id"].startswith(blk + "."))
        mark = "  <- WHOLE BLOCK" if len(keys) == n_blk else ""
        print(f"  {blk}: {len(keys)}/{n_blk} unread{mark}")
    for r in rows:
        if r["state"] == "TEST-ONLY":
            print(f"  [TEST-ONLY] {r['id']} — read by {r['readers']} and nothing else; "
                  f"a rule only a test consults is a rule no gate consults")

    if a.update_baseline:
        grew = sorted(unread - base) if have_base else []
        if grew:
            print("REFUSING to update the baseline — it would GROW by "
                  f"{len(grew)}: {', '.join(grew[:6])}"
                  f"{' …' if len(grew) > 6 else ''}. Wire the rule up, or delete it "
                  f"from the rules file. A ratchet that can loosen is not a ratchet")
            return 1
        os.makedirs(os.path.dirname(a.baseline), exist_ok=True)
        with open(a.baseline, "w", encoding="utf-8") as f:
            json.dump({"_why": "Rule keys allowed to have no reader. May SHRINK, never "
                               "GROW. See pipeline/scripts/rules_reader_check.py.",
                       "_recorded": "2026-08-29",
                       "unread": sorted(unread)}, f, indent=1)
        print(f"baseline written: {len(unread)} allowed unread")
        return 0

    if not have_base:
        print(f"RULES READERS: no baseline at {a.baseline} — run --update-baseline once "
              f"to record today's {len(unread)} as the ceiling")
        return 0 if a.soft else 2

    grew = sorted(unread - base)
    closed = sorted(base - unread)
    for c in closed:
        print(f"  [CLOSED] {c} now has a reader — drop it from the baseline")
    if grew:
        print(f"RULES READERS VIOLATIONS ({len(grew)}):")
        for g in grew:
            print(f"  - `{g}` has no reader and is not in the baseline. Either a "
                  f"consumer was deleted, or a NEW rule was added without one — and a "
                  f"rule nothing reads is a number, not a guard")
        return 0 if a.soft else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
