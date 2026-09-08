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

THE THIRD STATE — A PICK THAT RETURNED NOTHING (added 2026-08-28)
A watched row with no distillation is a debt, above. But two of the first nine picks watched
on 2026-08-28 returned NO USABLE CONTENT — no captions, frames that are title cards and blank
transitions — and a pick that returns nothing IS a result. Forcing it to produce a knowledge
line would be writing into `knowledge/` from a source with nothing in it, which is worse than
the debt. So a row may carry `yield_none: {reason, recorded_in}` and stop being a debt.

It is priced so it cannot become the cheap way out of a hard distillation, because that is
exactly what it would become otherwise:
  * only on a `watched` row, and never together with `distilled_to` — a video cannot both
    have yielded something and yielded nothing;
  * the `reason` must be a SENTENCE (thin tokens — "n/a", "nothing", "pending" — are refused
    by name, the same rule the decision register and the spec-ratchet already use);
  * `recorded_in` must name a file that EXISTS and that MENTIONS THE VIDEO ID — the same
    bidirectional citation `distilled_to` gets. A no-yield finding that is written only in
    the ledger is not written down; it has to be in the study unit where the next person
    picking rows will actually read it.
  * the count PRINTS at every session open. If this state starts growing, it is visible.

WHAT IS ADVISORY (exit 2) — real debt, but it must never block a render
  unwatched `must` rows, and watched rows with nothing distilled and no recorded no-yield. **This rung is a session
  print, not a gate rung.** Learning to see is not a precondition for a frame leaving the
  building, and wiring it as one would earn it the same fate as every other rung nobody can
  satisfy on the day it ships.

HOLES HE NAMES (added 2026-08-28, and it is the reason this section exists)
The owner read the curriculum and said: *"ยังไม่เห็นมี video ที่เกี่ยวกับการจัดวางของตกแต่ง"* — no
video about the PLACEMENT of decor. He was right, and the measurement is exact: of 56 watched
rows, ZERO were about arranging objects on a surface. The four rows that were sat at priority
`should`/`reference`, and the watch pass ran `must` first.

**Nothing in this file could have told him that, and the per-G coverage line added below still
cannot.** G1 held 33 rows and 16 of them were watched — by every count in this program that
G-item was the best-covered one there is. The hole was INSIDE it: bed-making, rug SIZING,
closet ORGANISING, merchandising — every watched row was about an object class the studio
already builds, and not one showed somebody choosing objects and putting them down. **A
counter cannot find a hole in the category it is counting, because the category was written by
the same builder who chose what to worry about** (the R7b defect, one level up: an instrument
answers the question it was built to ask).

So the mechanism is NOT a better counter. It is that a hole HE names becomes a ROW —
`holes_named` — carrying his verbatim words, what was measured under them, and the rows queued
in answer; and it stays OPEN and PRINTS until those rows are both watched AND distilled. This
repo has already measured what happens otherwise: 21 asks routed to him and dropped, *"not
refused, dropped"*. His eye is the rung; this is only the ledger that stops its findings
evaporating.

A DECLARED GAP MUST NAME WHAT IT SEARCHED (added 2026-08-28, the same day, an hour later)
`gaps_youtube_cannot_close` rows say a thing cannot be learned from video and must be measured
or asked instead. **Three of them were filed that were already answered on this disk.** The
owner said so in one sentence — *"ผมเคยให้คุณไปดูงานเพื่อนผมแล้วมาตอบผมแล้ว"*, I already had you go
and look at my friend's work and report back — and he was right:

  * VG-15 was filed as *"Nobody states it anywhere, in any language"* about the number of objects
    per bay. `_private/deliv-001/friend-builtin-bed-study-2026-08-26/` had surveyed 51 frames of
    delivered work two days earlier and **45 of the 51 `contents_styling` fields carry a count**
    — *"One or two objects per cubby, nothing more"*, *"2 object groups, rest of shelf left
    empty"*, *"a tight row of ~10 books — the only dense object group"*.
  * VG-14 asked the owner to rule whether "unnatural" means sameness across bays. That study's
    own report already said *"Our paired surfaces are mirror-copied, not person-placed."*
  * A queued row called a celebrity closet *"R4b reference of record for a class we hold ZERO
    references of"*. The same study holds **50 frames showing built-in casework**, in his market.

THE SHAPE IS ONE THIS REPO HAS ALREADY NAMED AND PRICED: **a gap is a claim about the WORLD;
"we did not look" is a claim about US** (D-074, R13 — `not-attempted` is refused by name there
for exactly this). So a gap row now carries `searched`: what was actually checked before the
gap was declared, as paths that must EXIST. It is not a proof of diligence and does not pretend
to be — a liar can list a path without opening it. What it does is make the omission VISIBLE at
the moment of writing, which is the moment the three above were written without anyone noticing
that the local study corpus had never been opened.

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

# Refused BY NAME as a no-yield reason. A field that accepts a token accepts silence.
THIN_REASONS = ("", "-", "--", "n/a", "na", "none", "nothing", "no yield", "nil",
                "pending", "tbd", "todo", "?", "unknown", "empty", "skip", "skipped")
MIN_REASON_CHARS = 60


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

        yn = r.get("yield_none")
        if yn is not None:
            if not isinstance(yn, dict):
                fails.append(f"{tag}: yield_none must be an object carrying reason + "
                             f"recorded_in, not {type(yn).__name__}")
                yn = None
            else:
                if st != "watched":
                    fails.append(f"{tag}: yield_none on a row with status {st!r} — only a "
                                 f"video somebody actually watched can be known to have "
                                 f"returned nothing")
                if dist:
                    fails.append(f"{tag}: carries BOTH distilled_to and yield_none — a "
                                 f"video cannot have yielded something and nothing")
                reason = (yn.get("reason") or "").strip()
                if reason.lower().rstrip(".") in THIN_REASONS:
                    fails.append(f"{tag}: yield_none reason {reason!r} is a token, not a "
                                 f"reason — refused by name")
                elif len(reason) < MIN_REASON_CHARS:
                    fails.append(f"{tag}: yield_none reason is {len(reason)} chars — under "
                                 f"{MIN_REASON_CHARS} it is a label, and a label cannot say "
                                 f"WHAT was checked before the pick was written off")
                rec = (yn.get("recorded_in") or "").strip()
                if not rec:
                    fails.append(f"{tag}: yield_none with no recorded_in — a no-yield "
                                 f"finding written only in the ledger is not written down")
                else:
                    rp = os.path.join(repo, rec)
                    if not os.path.exists(rp):
                        fails.append(f"{tag}: yield_none recorded_in names a path that does "
                                     f"not exist: {rec}")
                    else:
                        try:
                            with open(rp, encoding="utf-8", errors="replace") as fh:
                                rbody = fh.read()
                        except OSError as e:
                            fails.append(f"{tag}: yield_none recorded_in unreadable "
                                         f"({e.__class__.__name__})")
                            rbody = vid
                        if vid not in rbody:
                            fails.append(
                                f"{tag}: yield_none recorded_in {rec} never mentions the "
                                f"video id — same bidirectional citation distilled_to gets")

        # ---- debt, never a fail
        if st == "unwatched" and r.get("priority") == "must":
            debts.append(("unwatched-must", vid, r.get("queued_at")))
        if st == "watched" and not dist and not yn:
            debts.append(("watched-not-distilled", vid, r.get("watched_at")))

    for g in (led.get("gaps_youtube_cannot_close") or []):
        gid = g.get("id") or "<no id>"
        searched = g.get("searched")
        if searched is None:
            debts.append(("gap-never-said-what-it-searched", gid, g.get("raised")))
            continue
        if not isinstance(searched, list) or not searched:
            fails.append(f"{gid}: `searched` must be a non-empty list of paths that were "
                         f"actually checked before this gap was declared")
            continue
        for s in searched:
            sp = os.path.join(repo, str(s))
            if not os.path.exists(sp):
                fails.append(f"{gid}: searched names {s!r}, which does not exist — a gap "
                             f"cannot cite a place nobody could have looked")

    for h in (led.get("holes_named") or []):
        hid = h.get("id") or "<no id>"
        if not (h.get("verbatim") or "").strip():
            fails.append(f"{hid}: a hole he named with no verbatim — his words are the row")
        if not (h.get("measured") or "").strip():
            fails.append(f"{hid}: no `measured` — a hole asserted but never counted is a "
                         f"claim about us, not a finding")
        answered = h.get("answered_by") or []
        if not answered:
            fails.append(f"{hid}: no `answered_by` rows — a hole with nothing queued against "
                         f"it is the dropped-ask shape this file was written to stop")
        for vid in answered:
            if vid not in seen:
                fails.append(f"{hid}: answered_by names {vid} which is not a row in this "
                             f"ledger")

    return fails, debts


def hole_state(led):
    """(hole, n_watched, n_distilled, n_total) per open hole. Pure."""
    by = {r.get("id"): r for r in (led.get("rows") or [])}
    out = []
    for h in (led.get("holes_named") or []):
        if h.get("closed_at"):
            continue
        ids = h.get("answered_by") or []
        rows = [by[i] for i in ids if i in by]
        w = sum(1 for r in rows if r.get("status") == "watched")
        d = sum(1 for r in rows if (r.get("distilled_to") or "").strip())
        out.append((h, w, d, len(ids)))
    return out


def g_coverage(led):
    """{G: (rows, watched, distilled)}. Pure. A G-item feeding nothing is visible here — but
    read the docstring: this counter did NOT find the hole of 2026-08-28 and cannot."""
    cov = {g: [0, 0, 0] for g in G_ITEMS}
    for r in (led.get("rows") or []):
        if r.get("status") == "dropped":
            continue
        for g in (r.get("g_items") or []):
            if g not in cov:
                continue
            cov[g][0] += 1
            if r.get("status") == "watched":
                cov[g][1] += 1
                if (r.get("distilled_to") or "").strip():
                    cov[g][2] += 1
    return {g: tuple(v) for g, v in cov.items()}


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
                     if r.get("status") == "watched" and not (r.get("distilled_to") or "")
                     and not r.get("yield_none")]
    no_yield = [r for r in rows if r.get("yield_none")]

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
    if no_yield:
        out.append("            ดูแล้วแต่ไม่ได้อะไรเลย {} เรื่อง — บันทึกไว้ว่าไม่ได้อะไร "
                   "(การหยิบที่ไม่ได้อะไรคือผลลัพธ์ ไม่ใช่หนี้)".format(len(no_yield)))
    if led.get("gaps_youtube_cannot_close"):
        out.append("            ช่องที่ YouTube ปิดให้ไม่ได้ {} ข้อ — อยู่ในไฟล์ "
                   "(ต้องวัดจาก anchor pool / ถามคนทำจริง)".format(
                       len(led["gaps_youtube_cannot_close"])))
    holes = hole_state(led)
    for h, w, dd, tot in holes:
        age = _age_days(h.get("named_at"), today)
        out.append('            **ช่องที่พี่ชี้เอง [{}{}]: "{}"** — คิวตอบ {} เรื่อง · '
                   "ดูแล้ว {} · กลั่นแล้ว {}{}".format(
                       h.get("id", "?"), f" {age}d" if age is not None else "",
                       (h.get("verbatim") or "")[:60], tot, w, dd,
                       "  → ปิดได้แล้ว" if (tot and dd == tot) else ""))
    cov = g_coverage(led)
    out.append("            ต่อ G: " + " · ".join(
        "{} {}/{}/{}".format(g, cov[g][0], cov[g][1], cov[g][2]) for g in G_ITEMS)
        + "   (แถว/ดูแล้ว/กลั่นแล้ว — ตัวนับนี้หาช่องที่อยู่ *ข้างใน* G ไม่เจอ ดู docstring)")
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
