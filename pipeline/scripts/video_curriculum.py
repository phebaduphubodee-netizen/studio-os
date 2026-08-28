#!/usr/bin/env python3
"""video_curriculum.py — the reader for `qa/video-curriculum.json`.

    python pipeline/scripts/video_curriculum.py            # the session-open lines
    python pipeline/scripts/video_curriculum.py --check    # exit 1 on a lie, 2 on debt

WHY A LEDGER AND A READER, AND NOT A LIST OF LINKS
--------------------------------------------------
The owner asked (2026-08-28) for YouTube videos "เพื่อให้คุณนั่นแหละดูและเรียนรู้การเป็น
interior designer". The obvious delivery is a markdown list of good links. This repo has
measured what happens to that artefact four separate times and given it a name: **a queue
whose consumer never visits it.** 357 critic items filed / ~22 built. 61 DR units / 39
write-only. 21 gate artifacts / 2 with a verdict. Six skills that fired for two days and
then went 54 days unused with nothing in the repo able to tell. A list of 30 links, however
good the links are, is the fifth instance already written down.

So the watchlist is a ROW, and the row carries the two things a link cannot:

  * `status` — did anyone actually watch it. `unwatched` is the honest default and it AGES.
  * `distilled_to` — where the learning LANDED. The reproduction curriculum was amended on
    2026-08-05 for exactly this: six rounds "produced hundreds of measured numbers and not
    one line entered knowledge/". **Measuring is not learning, and watching is not learning
    either.** A watched row with nothing distilled is a debt, and it prints as one.

WHAT IS A LOUD FAIL (exit 1) — the bookkeeping lying about itself
  1. a `watched` row with no `notes` file on disk. A watch that left no note did not happen;
     nothing important lives only in conversation.
  2. a `distilled_to` naming a path that does not exist, or that exists but never mentions
     the video id. Bidirectional, the same test `inbox_audit.py` applies to the _inbox
     ledger: a successor that cannot be shown to carry the source is not a successor.
  3. a `dropped` row with no `drop_reason`; a duplicate id; a url that does not match its
     own id; a `g_item` outside G1..G10; a status outside the enum.

WHAT IS ADVISORY (exit 2) — real debt, but it must never block a render
  unwatched `must` rows, and watched rows with nothing distilled. **This rung is a session
  print, not a gate rung.** Learning to see is not a precondition for a frame leaving the
  building, and wiring it as one would earn it the same fate as every other rung nobody can
  satisfy on the day it ships.

WHAT IT DOES NOT CLAIM. It cannot tell whether the watching taught anything — only whether
it happened and whether anything was written down. The eye that judges whether the lesson
landed is C2/C3/his (R7d: the builder does not convict on its own look).
"""
import argparse
import datetime
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = os.path.join(REPO, "qa", "video-curriculum.json")

STATUSES = ("unwatched", "watched", "dropped")
PRIORITIES = ("must", "should", "reference")
G_ITEMS = tuple("G%d" % i for i in range(1, 11))
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def load(path=LEDGER):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _age_days(stamp, today=None):
    """Whole days since an ISO date. Unparseable returns None rather than 0 — an age we
    cannot compute must not print as 'fresh'."""
    if not stamp:
        return None
    try:
        d = datetime.date.fromisoformat(str(stamp)[:10])
    except ValueError:
        return None
    today = today or datetime.date.today()
    return (today - d).days


def check(led, repo=REPO):
    """Returns (fails, debts). Pure apart from reading the successor files a row names."""
    fails, debts = [], []
    rows = led.get("rows") or []
    seen = {}
    for r in rows:
        vid = r.get("id")
        tag = f"{vid or '<no id>'} ({(r.get('title') or '')[:40]})"

        if not vid or not ID_RE.match(str(vid)):
            fails.append(f"{tag}: id is not an 11-character YouTube id")
            continue
        if vid in seen:
            fails.append(f"{tag}: duplicate id — already in the ledger")
            continue
        seen[vid] = r

        if r.get("url") != f"https://www.youtube.com/watch?v={vid}":
            fails.append(f"{tag}: url does not match its own id — a row that points "
                         f"somewhere else is not a row about this video")

        st = r.get("status")
        if st not in STATUSES:
            fails.append(f"{tag}: status {st!r} is not one of {STATUSES}")
        if r.get("priority") not in PRIORITIES:
            fails.append(f"{tag}: priority {r.get('priority')!r} is not one of {PRIORITIES}")

        gi = r.get("g_items") or []
        if not gi:
            fails.append(f"{tag}: no g_items — a video that feeds nothing has no reason "
                         f"to be in the curriculum")
        for g in gi:
            if g not in G_ITEMS:
                fails.append(f"{tag}: g_item {g!r} is outside G1..G10")

        if st == "dropped" and not (r.get("drop_reason") or "").strip():
            fails.append(f"{tag}: dropped with no drop_reason — a drop must name what was "
                         f"checked (inbox_audit's rule, same reason)")

        if st == "watched":
            notes = (r.get("notes") or "").strip()
            if not notes:
                fails.append(f"{tag}: status=watched with no notes path — a watch that left "
                             f"no note did not happen")
            elif not os.path.exists(os.path.join(repo, notes)):
                fails.append(f"{tag}: notes path does not exist: {notes}")
            if not r.get("watched_at"):
                fails.append(f"{tag}: status=watched with no watched_at date")

        dist = (r.get("distilled_to") or "").strip()
        if dist:
            p = os.path.join(repo, dist)
            if not os.path.exists(p):
                fails.append(f"{tag}: distilled_to names a path that does not exist: {dist}")
            else:
                try:
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        body = fh.read()
                except OSError as e:
                    fails.append(f"{tag}: distilled_to unreadable ({e.__class__.__name__})")
                    body = ""
                if vid not in body:
                    fails.append(
                        f"{tag}: distilled_to {dist} never mentions the video id — the "
                        f"successor cannot be shown to carry the source (bidirectional "
                        f"citation, inbox_audit's rule)")
            if st != "watched":
                fails.append(f"{tag}: distilled_to is set but status is {st!r} — nothing "
                             f"can be distilled from a video nobody watched")

        # ---- debt, never a fail
        if st == "unwatched" and r.get("priority") == "must":
            debts.append(("unwatched-must", vid, r.get("queued_at")))
        if st == "watched" and not dist:
            debts.append(("watched-not-distilled", vid, r.get("watched_at")))

    return fails, debts


def report_lines(path=LEDGER, repo=REPO, today=None):
    """The session-open block. Unreadable prints UNKNOWN, never nothing — same law as
    every other section of the brief."""
    try:
        led = load(path)
    except Exception as e:
        return ["", f"VIDEO CURRICULUM unknown — {os.path.relpath(path, repo)} could not be "
                    f"read ({e.__class__.__name__}). That is unknown, not zero."]

    rows = led.get("rows") or []
    fails, debts = check(led, repo=repo)
    by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in STATUSES}
    watched = by_status["watched"]
    unwatched_must = [r for r in rows
                      if r.get("status") == "unwatched" and r.get("priority") == "must"]
    not_distilled = [r for r in rows
                     if r.get("status") == "watched" and not (r.get("distilled_to") or "")]

    ages = [a for a in (_age_days(r.get("queued_at"), today) for r in unwatched_must)
            if a is not None]
    oldest = max(ages) if ages else None

    out = ["", "VIDEO CURRICULUM {} เรื่อง — ดูแล้ว {} · ยังไม่ได้ดู {} · ตัดออก {} "
                "(qa/video-curriculum.json)".format(
                    len(rows), watched, by_status["unwatched"], by_status["dropped"])]
    if oldest is not None:
        out.append(f"            must ที่ยังไม่ได้ดู {len(unwatched_must)} เรื่อง — "
                   f"เก่าสุด {oldest} วัน")
    elif unwatched_must:
        out.append(f"            must ที่ยังไม่ได้ดู {len(unwatched_must)} เรื่อง")
    if not_distilled:
        out.append("            **ดูแล้วแต่ยังไม่ได้กลั่นลง knowledge/ {} เรื่อง** — "
                   "ดูแล้วไม่ใช่เรียนแล้ว (reproduction-curriculum 2026-08-05)".format(
                       len(not_distilled)))
    for r in unwatched_must[:3]:
        out.append("              [{}] {} — {}".format(
            ",".join(r.get("g_items") or []), (r.get("channel") or "?")[:22],
            (r.get("title") or "")[:58]))
    if led.get("gaps_youtube_cannot_close"):
        out.append("            ช่องที่ YouTube ปิดให้ไม่ได้ {} ข้อ — อยู่ในไฟล์ "
                   "(ต้องวัดจาก anchor pool / ถามคนทำจริง)".format(
                       len(led["gaps_youtube_cannot_close"])))
    if fails:
        out.append(f"            !! {len(fails)} integrity failure(s) — บัญชีโกหก, "
                   f"รัน video_curriculum.py --check")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="print the integrity report and set the exit code")
    ap.add_argument("--json", action="store_true", help="machine output")
    ap.add_argument("--ledger", default=LEDGER)
    args = ap.parse_args(argv)

    try:
        led = load(args.ledger)
    except Exception as e:
        print(f"COULD NOT RUN: {e}", file=sys.stderr)
        return 2

    fails, debts = check(led)

    if args.json:
        print(json.dumps({"fails": fails, "debts": debts,
                          "rows": len(led.get("rows") or [])}, ensure_ascii=False, indent=1))
    elif args.check:
        for f in fails:
            print("FAIL  " + f)
        for kind, vid, when in debts:
            print(f"debt  {kind}  {vid}  since {when}")
        print(f"\n{len(led.get('rows') or [])} rows · {len(fails)} failure(s) · "
              f"{len(debts)} debt(s)")
    else:
        for line in report_lines(args.ledger):
            print(line)

    if fails:
        return 1
    return 2 if debts else 0


if __name__ == "__main__":
    sys.exit(main())
