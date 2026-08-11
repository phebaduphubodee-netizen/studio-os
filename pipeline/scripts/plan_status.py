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

# A STATUS THE MACHINE CANNOT READ IS PROGRESS THE MACHINE CANNOT SEE. Written after
# inventing `part-done` on a work item that had genuinely half landed: the review
# trigger counts items that became `done`, so a status outside this set makes real
# work invisible to the ritual that is supposed to follow it. The fix for a half-done
# item is to SPLIT it — an item that cannot be done or not-done is two items.
WORK_STATUSES = ("todo", "done", "blocked", "dropped")
PHASE_STATUSES = ("open", "done", "blocked", "dropped")


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
    """git stdout, or None when it could not be read — decoded as UTF-8, explicitly.

    THE THIRD INSTANCE OF ONE DEFECT IN ONE DAY, and this one was in code written an
    hour earlier. `text=True` decodes with the LOCALE codec, which on this machine is
    cp1252; the plan of record and half the specs in this repo are written in Thai, so
    `git show <rev>:qa/deliverable-plan.json` raised UnicodeDecodeError inside
    subprocess's reader thread and this function returned None for every call that
    touched real content. The new review trigger then reported, correctly and
    uselessly, "git could not read the plan at the last review" — it failed SAFE and
    it never worked.

    The other two instances the same day: `deliverable_check` DIED printing a Thai
    object name through a cp1252 console, and its exit code 1 read as "ran and does
    not qualify". THE PATTERN IS WORTH THE PARAGRAPH: this repo's data is Thai, and
    every boundary that accepts a default encoding is a latent failure that presents
    as "the tool found nothing" rather than as an error."""
    try:
        r = subprocess.run(["git", "-C", REPO] + list(args), capture_output=True,
                           timeout=15)
        if r.returncode != 0:
            return None
        return r.stdout.decode("utf-8", errors="replace").strip()
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
    not answer — which is reported as unknown, never as zero.

    REPORTED, NOT THE TRIGGER, since 2026-08-10 — see `work_closed_since_review`.
    """
    last = plan.get("last_review_commit")
    return _work_commits("HEAD" if last is None else f"{last}..HEAD")


def unreadable_statuses(plan):
    """[(where, status)] for every status this module's vocabulary does not name.

    Reported, never silently tolerated. The trigger for a review is "a work item
    became done"; a status it does not know is a row that can hold real, landed
    work and never arm anything."""
    bad = []
    for ph in (plan or {}).get("phases", []):
        st = ph.get("status")
        if st not in PHASE_STATUSES:
            bad.append((str(ph.get("id")), st))
        for w in ph.get("work", []):
            ws = w.get("status")
            if ws not in WORK_STATUSES:
                bad.append((f"{ph.get('id')}/{w.get('id')}", ws))
    return bad


def _done_work_ids(plan):
    return {f"{ph.get('id')}/{w.get('id')}" for ph in (plan or {}).get("phases", [])
            for w in ph.get("work", []) if w.get("status") == "done"}


def _plan_at(rev):
    """The plan file as of `rev`. None when git cannot answer or it will not parse
    — never an empty plan, because an empty plan reads as "nothing was done yet"
    and would arm a review for every item already closed."""
    txt = _git("show", f"{rev}:{PLAN_REL.replace(os.sep, '/')}")
    if txt is None:
        return None
    try:
        return json.loads(txt)
    except ValueError:
        return None


def work_closed_since_review(plan):
    """Work-item ids whose status became `done` since the last recorded review.
    None means git could not answer.

    THE SECOND INSTANCE OF THE SELF-RE-ARMING REVIEW, and the first fix is why it
    is worth writing down. `record_review` stamps HEAD, its own edit to the plan
    lands at HEAD+1, and a review was due again forever. That was fixed by not
    counting PLAN-ONLY commits — a rule stated in terms of WHICH FILES a commit
    touched. The very next review round produced a commit touching the plan AND
    its gate artifact, and the review re-armed on the round that had just done it.

    A rule that names the files it applies to will always miss the next file
    (R9b's law, arrived at here from the other end). So the proxy is retired: the
    condition the owner actually stated is "after every commit that CLOSES WORK",
    and whether work closed is not a guess about paths — the plan records it, item
    by item, and git holds what it said last time. Diffing that is exact.

    The cost is stated plainly: code that lands without ticking its item no longer
    arms a review. By the plan's own bookkeeping no work closed, so that is a
    plan-integrity failure rather than a review the trigger missed — and the old
    behaviour was worse in the direction that actually happened, arming on any
    commit at all. Three of the last eight reviews recorded that they changed
    nothing.
    """
    reviews = plan.get("reviews") or []
    if reviews and "done_at_review" in reviews[-1]:
        # THE EXACT SOURCE, and it removes git from the question. Stamping HEAD had an
        # ordering flaw the git version could not escape: `record_review` runs BEFORE
        # the commit that carries the closures it was triggered by, so the plan at
        # that commit does not contain them and the next run counts them a second
        # time — the self-re-arming review for a third time, one level down. What
        # closed is a fact about the plan, so the plan records it.
        return sorted(_done_work_ids(plan) - set(reviews[-1]["done_at_review"]))
    last = plan.get("last_review_commit")
    if last is None:
        return sorted(_done_work_ids(plan))
    before = _plan_at(last)                 # reviews recorded before this change
    if before is None:
        return None
    return sorted(_done_work_ids(plan) - _done_work_ids(before))


def review_due(plan):
    """(due, why). A review is due when work has closed since the last one — that
    is the owner's condition, 'every time work finishes, after commit'."""
    if any(p.get("status") == "done" and not p.get("_reviewed") for p in plan.get("phases", [])):
        return True, "a phase closed and has not been reviewed"
    closed = work_closed_since_review(plan)
    if closed is None:
        return False, ("git could not read the plan at the last review, so what "
                       "closed is unknown (not zero)")
    if not closed:
        return False, "no work item has closed since the last review"
    return True, f"{len(closed)} work item(s) closed since the last review: " \
                 f"{', '.join(closed)}"


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
        # What was closed AT THE MOMENT OF THE REVIEW. The next review is due when
        # this set grows — a fact about the plan, answered by the plan, with no
        # commit ordering and no git in it. See work_closed_since_review.
        "done_at_review": sorted(_done_work_ids(plan)),
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
    # The standard is passed so image_row doors can actually RE-RUN. Without it
    # they return NOT RUN, and the opener printed "!! DEBT-09: marked built ...
    # no standard loaded" on a row whose door resolves fine — a false alarm at
    # the top of every session is how a warning column gets ignored.
    try:
        import deliverable_check as _DCH
        _std = _DCH.load_standard()
    except Exception:                                   # noqa: BLE001
        _std = None
    bad = DEBT.check(led, plan_phases=phases, standard=_std)
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

    bad = unreadable_statuses(plan)
    if bad:
        lines.append("")
        lines.append(f"!! {len(bad)} status(es) this file's vocabulary does not name — "
                     f"work in these rows is invisible to the review trigger:")
        for where, st in bad:
            lines.append(f"     {where}: {st!r} (known: {', '.join(WORK_STATUSES)})")
        lines.append("     an item that is neither done nor not-done is TWO items — split it.")

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
