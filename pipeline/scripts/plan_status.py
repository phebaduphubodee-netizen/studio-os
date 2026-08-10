"""WHERE ARE WE, WHAT IS NEXT — the consumer for qa/deliverable-plan.json.

Owner order 2026-08-09: remind me every session which phase we are at, propose what
to do next, and review — and propose CHANGES to — the plan every time work closes.

The reason this is a program and not a markdown file is the finding that produced
the plan in the first place. Session 2026-08-09 measured the same defect three
times: 357 critic items filed / ~22 built; ~61 DR units / 39 write-only; 21 gate
artifacts / 2 with an owner verdict. Each is a queue whose consumer never visits
it. A plan carried as prose would have been the fourth. So the plan is data and
this file is the consumer that runs unasked.

Pure python — no bpy, no PIL, no network. Runs anywhere python does.

    python pipeline/scripts/plan_status.py                 # the session opener
    python pipeline/scripts/plan_status.py --check         # exit 1 if a review is overdue
    python pipeline/scripts/plan_status.py --review --verdicts '{"P1":"keep: ..."}'

REVIEW IS NOT READING. `--review` refuses unless every remaining phase carries a
verdict of keep / change / drop WITH a reason. A review that changes nothing must
say so in those words — the point is that the plan is allowed to be wrong, and
dropping a phase for a recorded reason is a correct outcome.
"""
import argparse
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLAN_REL = os.path.join("qa", "deliverable-plan.json")
VERDICTS = ("keep", "change", "drop")


def load(path=None):
    p = path or os.path.join(REPO, PLAN_REL)
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def save(plan, path=None):
    p = path or os.path.join(REPO, PLAN_REL)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


# --------------------------------------------------------------- reading state

def current(plan):
    """The phase we are in: the first that is not done. `current_phase` is a hint,
    never the authority — a stale hint is how a plan starts lying about itself."""
    for ph in plan.get("phases", []):
        if ph.get("status") != "done":
            return ph
    return None


def remaining(plan):
    return [p for p in plan.get("phases", []) if p.get("status") != "done"]


def next_work(plan, n=3):
    """The next named items, in order, across phases — each with the file it touches."""
    out = []
    for ph in plan.get("phases", []):
        if ph.get("status") == "done":
            continue
        for w in ph.get("work", []):
            if w.get("status") in (None, "todo", "doing"):
                out.append((ph["id"], w))
                if len(out) >= n:
                    return out
    return out


def owner_actions(plan):
    return [c for c in plan.get("standing_corrections", []) if c.get("owner_action_required")]


def progress(plan):
    ws = [w for ph in plan.get("phases", []) for w in ph.get("work", [])]
    done = [w for w in ws if w.get("status") == "done"]
    return len(done), len(ws)


# --------------------------------------------------------------- review gating

def _git(*args):
    try:
        r = subprocess.run(["git", "-C", REPO] + list(args), capture_output=True,
                           text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


PLAN_REL = "qa/deliverable-plan.json"


def _work_commits(rev_range):
    """Commits in `rev_range` that changed something OTHER than the plan file.

    THE LOOP THIS CLOSES (found 2026-08-10, live since the plan's first commit):
    `record_review` stamps `last_review_commit = HEAD`, and then the review's own
    edit to this file has to be COMMITTED — which lands at HEAD+1 and makes a
    review due again, forever. The ritual re-armed itself on completion, so the
    only way to read "not due" was to leave the plan of record uncommitted. Every
    session since has opened on a REVIEW DUE that the previous session had in
    fact just done.

    A plan-only commit is the review writing itself down; it is not work closing.
    The docstring below already said the condition is "work has closed", so this
    is the check finally measuring what it always claimed to."""
    out = _git("rev-list", "--no-merges", rev_range)
    if out is None:
        return None
    n = 0
    for sha in [s for s in out.split() if s]:
        files = _git("show", "--pretty=", "--name-only", sha)
        if files is None:
            return None
        touched = [f for f in files.split("\n") if f.strip()]
        if any(f.strip() != PLAN_REL for f in touched):
            n += 1
    return n


def commits_since_review(plan):
    """WORK commits landed since the last recorded review. None means git could
    not answer — which is reported as unknown, never as zero."""
    last = plan.get("last_review_commit")
    return _work_commits("HEAD" if last is None else f"{last}..HEAD")


def review_due(plan):
    """(due, why). A review is due when work has closed since the last one — that
    is the owner's condition, 'every time work finishes, after commit'."""
    if any(p.get("status") == "done" and not p.get("_reviewed") for p in plan.get("phases", [])):
        return True, "a phase closed and has not been reviewed"
    n = commits_since_review(plan)
    if n is None:
        return False, "git could not be read, so commit count is unknown (not zero)"
    if plan.get("last_review_commit") is None:
        return (n > 0), f"{n} commit(s) and no review has ever been recorded"
    return (n > 0), f"{n} commit(s) since the last review"


def record_review(plan, verdicts, note="", commit=None):
    """Append a review. Refuses unless every remaining phase has a verdict with a
    reason — the whole mechanism is that a review must produce DECISIONS."""
    need = {p["id"] for p in remaining(plan)}
    missing = sorted(need - set(verdicts))
    if missing:
        raise ValueError(f"review refused — no verdict for: {', '.join(missing)}. "
                         f"Every remaining phase needs keep/change/drop and a reason.")
    bad = []
    for pid, v in verdicts.items():
        head, _, reason = str(v).partition(":")
        if head.strip().lower() not in VERDICTS:
            bad.append(f"{pid}: '{head.strip()}' is not keep/change/drop")
        elif not reason.strip():
            bad.append(f"{pid}: verdict carries no reason")
    if bad:
        raise ValueError("review refused — " + "; ".join(bad))

    head = commit or _git("rev-parse", "HEAD") or "unknown"
    changed = [k for k, v in verdicts.items() if str(v).partition(":")[0].strip().lower() != "keep"]
    plan.setdefault("reviews", []).append({
        "commit": head,
        "verdicts": verdicts,
        "changed": changed,
        "note": note or ("nothing changed this review" if not changed else ""),
    })
    plan["last_review_commit"] = head
    for p in plan.get("phases", []):
        if p.get("status") == "done":
            p["_reviewed"] = True
    return plan


# --------------------------------------------------------------- critic debt

def debt_lines(plan):
    """The critic-debt ledger in three lines: what is owed, what is due NOW, and
    what no instrument can see.

    A missing or unreadable ledger prints as UNKNOWN, never as nothing. Silence
    and zero look identical from outside, and that confusion is the whole disease
    this file was written against."""
    try:
        import debt_check as DEBT
    except ImportError as e:                            # pragma: no cover
        return ["", f"CRITIC DEBT unknown — debt_check is not importable ({e})"]
    led = DEBT.load()
    if led is None:
        return ["", "CRITIC DEBT unknown — qa/critic-debt.json could not be read. "
                    "That is unknown, not zero."]
    out = ["", DEBT.one_line(led)]
    phases = [p["id"] for p in plan.get("phases", [])]
    cur = current(plan)
    due = DEBT.due_now(led, phases, cur["id"]) if cur else []
    if due:
        out.append(f"            DUE NOW at {cur['id']}: {', '.join(due)} — "
                   f"their due phase has arrived.")
    bad = DEBT.check(led, plan_phases=phases)
    for s in bad[:3]:
        out.append(f"            !! {s}")
    return out


# --------------------------------------------------------------- the report

def report(plan):
    lines = []
    cur = current(plan)
    done, total = progress(plan)
    lines.append("=" * 68)
    lines.append(f"PLAN  {plan.get('unit', '?')} — {plan.get('goal', '')[:120]}")
    lines.append("=" * 68)
    if cur is None:
        lines.append("ALL PHASES CLOSED. The goal is either met or the plan was wrong.")
    else:
        idx = [p["id"] for p in plan["phases"]].index(cur["id"]) + 1
        lines.append(f"WE ARE AT   {cur['id']} ({idx} of {len(plan['phases'])}) — {cur['title']}")
        lines.append(f"            {cur['goal']}")
        lines.append(f"PROGRESS    {done}/{total} work items closed")
        lines.append(f"EXIT TEST   {cur['exit_test']}")

    nxt = next_work(plan)
    if nxt:
        lines.append("")
        lines.append("DO NEXT")
        for pid, w in nxt:
            lines.append(f"  [{pid}/{w['id']}] {w['what']}")
            lines.append(f"          -> {w.get('where', '?')}")

    oa = owner_actions(plan)
    if oa:
        lines.append("")
        lines.append("WAITING ON THE OWNER (the lane does not block on these)")
        for c in oa:
            lines.append(f"  {c['id']}: {c['do']}")

    # THE CRITIC DEBT, printed unasked at the top of every session — the same
    # reason this file exists at all. 357 items were filed and ~22 built because
    # the queue had no consumer; a ledger with no consumer would be the fifth
    # instance, not the fix.
    lines += debt_lines(plan)

    due, why = review_due(plan)
    lines.append("")
    lines.append(f"REVIEW      {'DUE — ' + why if due else 'not due — ' + why}")
    if due:
        lines.append("            run: plan_status.py --review --verdicts '{\"P1\":\"keep: ...\"}'")
        lines.append("            every remaining phase needs keep/change/drop AND a reason.")
    if plan.get("trn002", {}).get("status") == "proposed":
        lines.append(f"OPEN        TRN-002: {plan['trn002']['recommendation'][:100]}...")
    lines.append("=" * 68)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", default=None, help="path to deliverable-plan.json")
    ap.add_argument("--check", action="store_true", help="exit 1 if a review is overdue")
    ap.add_argument("--review", action="store_true", help="record a review")
    ap.add_argument("--verdicts", default=None, help='JSON {"P1":"keep: reason", ...}')
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)

    plan = load(a.plan)

    if a.review:
        if not a.verdicts:
            print("--review needs --verdicts. A review that records no decision is "
                  "the thing this file exists to prevent.", file=sys.stderr)
            return 2
        try:
            plan = record_review(plan, json.loads(a.verdicts), a.note)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        save(plan, a.plan)
        print("review recorded.")
        print(report(plan))
        return 0

    print(report(plan))
    if a.check:
        due, _ = review_due(plan)
        return 1 if due else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
