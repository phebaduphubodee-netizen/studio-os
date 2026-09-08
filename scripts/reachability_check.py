#!/usr/bin/env python3
"""reachability_check.py — an instrument nothing calls is a defect. PURE stdlib.

    python scripts/reachability_check.py [--all] [--json] [--write-baseline]

WHY THIS FILE EXISTS (owner, 2026-08-08: *"หรือต้องแก้ที่การบังคับใช้กฏ และการเริ่ม
session แบบเห็นภาพกว้างว่ามีเครื่องมืออะไรให้ใช้บ้าง?"*)

The studio's dominant activity is building instruments. Measured the day this file was
written: **143 non-test instruments, 55 unreachable from any path anyone runs, and 29 of
those 55 carry their own passing test suite.** Built, pinned, green, and in no path.

The three that make the point, each verified by grep rather than by impression:

  cap_check        R1's STOP-LOSS — the first rule the owner adopted, the one that says
                   stopping is always the correct move. It is a working function in
                   rule_gate.py with four tests. `check()` does not call it. Nothing does.
                   → WIRED 2026-08-08. Kept here in the past tense because it is the
                     clearest case this file has: the code was never the missing part.
                     What it needed was a NUMBER only the owner may set, living somewhere
                     a program could read. 34 rounds passed with the function green.
  critique_bundle  builds the bundle every critic rung (C2, C3) consumes. One mention, in
                   a sentence in training/README.md.
  self_audit       the doubt instrument. Appears only inside other modules' comments.

And twice in six hours on 2026-08-08: `coverage_check.py` could name `wall_floor_junction`
on r31 and r32 and was wired into nothing, and `craft_check.py` alongside it.

THE LAW THIS APPLIES, WHICH THE REPO ALREADY WROTE FOR RULES
------------------------------------------------------------
`rule_gate.py` opens with: *"a rule is real exactly to the extent that it is a program that
fails in a path someone already has to run."* The same sentence is true of INSTRUMENTS, and
nothing had ever applied it to them. A catalogue of tools injected at session start is the
other option, and this repo has already measured that channel at zero: CLAUDE.md has said
"Cite the winning source" since its FIRST COMMIT — 34 days, 360 commits — and the TRN-002
builder cites knowledge/ zero times across 4,311 lines. Documents get skimmed; a red suite
does not.

WHAT COUNTS AS REACHED
----------------------
A module is REACHED when an entry point imports it, or invokes `<name>.py` on a command
line, transitively. Entry points are DERIVED, not hand-listed, wherever that is possible:

  * anything a shell script under scripts/ invokes
  * every .claude/hooks/*.py (the law layer — the harness runs these)
  * every module named in a `## Commands` block of any CLAUDE.md
  * plus BUILD_MAINS below: the render/build entry points a human runs by hand

BUILD_MAINS is the one hand-written list, and it is the knob to be honest about: widening
it makes more things "reachable" without wiring anything. It is deliberately short, it
names only files whose `__main__` a person actually types, and adding to it shows in a diff.

A module may also declare `CLI-ONLY:` in its first 40 lines, naming who runs it and when.
That is the honest exit for `dwg_ingest`, `ffe_schedule`, `upscale` — tools a human invokes
directly, which are not defects. The declaration is greppable and lands in a diff, which is
the same standard every other debt-exit in this repo is held to.

WHAT THIS CHECK CANNOT SEE — declared before anyone finds it
-------------------------------------------------------------
IT WORKS AT MODULE GRANULARITY, so an unwired FUNCTION inside a wired module is invisible
to it. That is not a corner case: **`cap_check` was exactly that**, and it was the headline
example in this file's own docstring — living in `rule_gate.py`, reached by every render,
and never called by `check()`. The instrument written here to catch unwired instruments
could not catch the one that motivated it. Saying so is the point: a guard whose blind spot
is undocumented will be trusted for coverage it does not have.

**CLOSED 2026-08-08, and the blind spot is NOT** — `cap_check` is wired (owner declared
TRN-002's caps at 42 / 55 in `qa/curriculum-caps.json`; `check()` now calls it with counts
taken off disk). The granularity limit is unchanged and the next unwired function will be
just as invisible. What changed is one instance, not the category, and the header of
`qa/reachability-baseline.txt` still tracks function-level debt by hand.

Function-level reachability is not a bigger regex, it is a different check (most helpers in
a module are legitimately internal, so the naive version would drown in false positives).

WHAT KEPT IT UNWIRED IS THE PART WORTH REMEMBERING, because it was never a code problem:
`cap_check` needed `cap_rounds` / `cap_full_frames` for the unit and **no unit had ever
declared them**, R3 makes that number the owner's, and the curriculum ledger that was
supposed to hold it is a markdown table nothing parses — with no TRN-002 row in it at all.
A working function with four passing tests sat outside every path for 34 rounds because its
input lived somewhere no program could reach. **A rule is real exactly to the extent that it
is a program that fails in a path someone already has to run** — and that requires its DATA
to be reachable too, not just its code.

THE RATCHET, AND WHY SEEDING IT IS NOT THE THING I WARNED ABOUT
---------------------------------------------------------------
`qa/reachability-baseline.txt` holds today's 55. It MAY SHRINK AND MAY NEVER GROW, checked
against `git HEAD` — the same mechanism as `absent_baseline` in the coverage manifest.

Seeding a baseline is usually the flattering move, and on the coverage manifest it would be:
there, seeding would excuse objects for work about to be done. Here the list records a
PRE-EXISTING inventory that will not be paid off in one commit, and the only thing the seed
buys is that the check can land at all. What it cannot do is let the next unwired instrument
in quietly — which is the entire failure being fixed.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIRS = ["pipeline/scripts", "scripts"]
BASELINE_REL = "qa/reachability-baseline.txt"

# The one hand-written list. Short on purpose — see the docstring.
BUILD_MAINS = [
    "trn001_build", "trn002_build", "build_room", "build_floor", "make_all",
    "scaffold_project", "hybrid_render",
]

CLI_ONLY = re.compile(r"^\s*#?\s*CLI-ONLY:", re.M)
COMMANDS_BLOCK = re.compile(r"^##+\s*Commands\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)


def modules():
    """name -> path, for every non-test, non-underscore script."""
    out = {}
    for base in SCRIPT_DIRS:
        for p in sorted(glob.glob(os.path.join(ROOT, base, "*.py"))):
            n = os.path.basename(p)[:-3]
            if n.startswith("_"):
                continue
            out[n] = os.path.relpath(p, ROOT).replace("\\", "/")
    return out


def _read(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


# A LINE THAT ACTUALLY RUNS SOMETHING. The first version of `references` counted
# any occurrence of `<name>.py` anywhere in the text, and it took one afternoon
# to produce a false green: `asset_scale.py`'s docstring CITES `dwg_ingest.py`
# while explaining why the scale assertion had to be written, and that citation
# alone moved `dwg_ingest` from UNREACHED to reached. This checker exists to say
# "nothing calls this", so a prose mention counting as a call is the exact defect
# it was built to find, one level up — the fifteenth flattering scorer in this
# repo's ledger and the second one of mine in a day.
# The interpreter has to be named, in one form or another, on the same line.
RUNS_IT = re.compile(r"python|sys\.executable|--python\b|\bblender\b", re.I)


def references(text, names):
    """Modules this text imports or invokes on a command line.

    An IMPORT is unambiguous. A `<name>.py` is only an invocation when the same
    line names an interpreter — otherwise it is someone talking about the file,
    which is the opposite of running it.
    """
    hit = set()
    lines = text.splitlines()
    for n in names:
        if re.search(r"(?:^|\n)\s*(?:import\s+%s\b|from\s+%s\s+import)" % (n, n), text):
            hit.add(n)
            continue
        pat = re.compile(r"%s\.py\b" % re.escape(n))
        for i, ln in enumerate(lines):
            if not pat.search(ln):
                continue
            # a shell continuation puts the interpreter on an earlier line
            ctx = " ".join(lines[max(0, i - 2):i + 1])
            if RUNS_IT.search(ctx):
                hit.add(n)
                break
    return hit


def entry_points(mods):
    """DERIVED where possible. Returns (set, {name: why}) so the report can show the why."""
    names, why = set(), {}

    def add(ns, reason):
        for n in ns:
            if n in mods and n not in names:
                names.add(n)
                why[n] = reason

    for sh in sorted(glob.glob(os.path.join(ROOT, "scripts", "*.sh"))):
        rel = os.path.relpath(sh, ROOT).replace("\\", "/")
        add(references(_read(rel), mods), "invoked by " + rel)
    for h in sorted(glob.glob(os.path.join(ROOT, ".claude", "hooks", "*.py"))):
        rel = os.path.relpath(h, ROOT).replace("\\", "/")
        n = os.path.basename(h)[:-3]
        if n in mods:
            add([n], "law layer: " + rel)
        add(references(_read(rel), mods), "used by hook " + rel)
    for cm in sorted(glob.glob(os.path.join(ROOT, "**", "CLAUDE.md"), recursive=True)):
        rel = os.path.relpath(cm, ROOT).replace("\\", "/")
        for m in COMMANDS_BLOCK.findall(_read(rel)):
            add(references(m, mods), "documented command in " + rel)
    add(BUILD_MAINS, "build/render entry point (BUILD_MAINS)")
    return names, why


def reachable(mods):
    entries, why = entry_points(mods)
    src = {n: _read(p) for n, p in mods.items()}
    seen, stack = set(entries), list(entries)
    while stack:
        cur = stack.pop()
        for d in references(src.get(cur, ""), mods):
            if d not in seen:
                seen.add(d)
                stack.append(d)
    return seen, why


def declared_cli_only(mods):
    out = set()
    for n, p in mods.items():
        head = "\n".join(_read(p).splitlines()[:40])
        if CLI_ONLY.search(head):
            out.add(n)
    return out


def audit():
    """Returns (report dict, violations [str]). Pure apart from reading the tree + git."""
    mods = modules()
    real = {n: p for n, p in mods.items() if not n.startswith("test_")}
    tests = {n for n in mods if n.startswith("test_")}
    reach, why = reachable(mods)
    cli = declared_cli_only(real)

    unreached = sorted(n for n in real if n not in reach and n not in cli)
    baseline = read_baseline()
    new = [n for n in unreached if n not in baseline]
    # A name in the baseline that is now wired (or gone) must LEAVE the baseline, or the
    # list stops being a debt and becomes decoration.
    closed = sorted(b for b in baseline if b not in unreached)

    violations = []
    for n in new:
        has_test = ("test_%s" % n) in tests
        violations.append(
            "UNREACHED `%s`%s: no entry point imports or invokes it, and it does not "
            "declare `CLI-ONLY:`. Wire it into a path someone already runs, or declare "
            "who runs it by hand. An instrument outside every path is a document — "
            "cap_check (R1's stop-loss) was one for 34 rounds — a working function "
            "with passing tests, waiting on a number that lived where no program "
            "could read it."
            % (n, " (it HAS a passing test suite, which is the trap: green and unreached "
                  "look identical from outside)" if has_test else ""))
    violations += baseline_ratchet(unreached, baseline)
    report = {
        "instruments": len(real), "reached": len(real) - len(unreached) - len(cli),
        "cli_only": sorted(cli), "unreached": unreached,
        "unreached_with_tests": sorted(n for n in unreached if ("test_%s" % n) in tests),
        "new_since_baseline": new, "closed_since_baseline": closed,
        "entry_points": {n: why[n] for n in sorted(why)},
    }
    return report, violations


def read_baseline(text=None):
    if text is None:
        text = _read(BASELINE_REL)
    return {l.strip() for l in text.splitlines()
            if l.strip() and not l.lstrip().startswith("#")}


def baseline_ratchet(unreached, baseline, previous=None):
    """May shrink, never grow — checked against git HEAD, not the working tree."""
    if previous is None:
        try:
            p = subprocess.run(["git", "show", "HEAD:" + BASELINE_REL], cwd=ROOT,
                               capture_output=True, text=True, encoding="utf-8",
                               timeout=30)
        except Exception as e:  # pragma: no cover - git missing
            return ["cannot read the committed baseline to check the ratchet (%s)" % e]
        if p.returncode != 0:
            return []  # first landing: the seed commit IS the predecessor for the next run
        previous = read_baseline(p.stdout)
    grew = sorted(set(baseline) - set(previous))
    if grew:
        return ["`%s` GREW by %s — the unreached list may only SHRINK. Wire the instrument "
                "or declare it CLI-ONLY; adding it to the baseline is the builder excusing "
                "the builder." % (BASELINE_REL, grew)]
    return []


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="list every unreached instrument")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write-baseline", action="store_true",
                    help="seed/refresh qa/reachability-baseline.txt from today's tree")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    report, violations = audit()

    if a.write_baseline:
        body = ("# instruments not reachable from any entry point, as of the commit that\n"
                "# wrote this file. MAY SHRINK, MAY NEVER GROW (scripts/reachability_check.py).\n"
                "# Wire one into a path, or declare `CLI-ONLY: <who runs it, when>` in its\n"
                "# header, then delete its line here.\n"
                + "\n".join(report["unreached"]) + "\n")
        with open(os.path.join(ROOT, BASELINE_REL), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(body)
        print("wrote %s with %d entries" % (BASELINE_REL, len(report["unreached"])))
        return 0

    if a.json:
        print(json.dumps(dict(report, violations=violations), ensure_ascii=False, indent=1))
        return 1 if violations else 0

    n_un = len(report["unreached"])
    print("=== instrument reachability ===")
    print("  %d instruments | %d reached | %d CLI-ONLY (declared) | %d UNREACHED"
          % (report["instruments"], report["reached"], len(report["cli_only"]), n_un))
    print("  of the unreached, %d carry their own passing test suite — green and in no path"
          % len(report["unreached_with_tests"]))
    if report["closed_since_baseline"]:
        print("\n  CLOSED since the baseline (delete these lines from %s):" % BASELINE_REL)
        for n in report["closed_since_baseline"]:
            print("    - " + n)
    if a.all and report["unreached"]:
        print("\n=== unreached ===")
        for n in report["unreached"]:
            mark = "T" if n in report["unreached_with_tests"] else " "
            print("  [%s] %s" % (mark, n))
    if violations:
        print("\n=== VIOLATIONS (%d) ===" % len(violations))
        for v in violations:
            print("  !! " + v)
        print("\n  an instrument that no path calls is a document. exit 1")
        return 1
    print("\n  no NEW unreached instrument, and the baseline did not grow.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
