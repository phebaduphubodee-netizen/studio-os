#!/usr/bin/env python3
"""UNBOUGHT IS NOT UNAVAILABLE — the rung that refuses to let "we have not
bought one" print as "one does not exist".

WHAT IT IS FOR, with the instance that produced it. On 2026-08-16 the lane
declared a SOURCING GAP for the bed cloth (D-074) and handed it to the owner as
a procurement decision. The survey behind it was real and careful: 68 cached
folders, 58 not bed covers at all, 8 failing a measured cut, 2 surviving. Every
one of those 68 came from a FREE tier. The three paid tiers R8 permits — 3dsky
at $5-15 a model, BlenderKit at $118.80/yr, Chocofur at ~EUR 25 a pack, all
with prices and licences verified in `docs/DECISIONS-render-assets.md` since
2026-07-01 — have never been attempted once. The gap was measured against the
half of the world we had already searched, and the lane's answer to it was to go
back to hand-modelling the object, which is the class R8 forbids.

THE DISTINCTION THIS FILE ENFORCES, because it is the whole defect:

    A GAP IS A CLAIM ABOUT THE WORLD.  "not-attempted" IS A CLAIM ABOUT US.

A declaration that mixes them is refused by name, and the row is converted into
what it actually is: a PROCUREMENT ASK with a price, which R8 says is his call
per purchase. That ask does not block anything (R3 — nothing waits for him). It
is routed into the plan's owner channel and printed in the render path, WITH ITS
AGE, because the failure mode for asks in this repo is not refusal — it is that
they stop being asked. `docs/DECISIONS-render-assets.md` has carried
"Status: DEFERRED — founder will decide later (2026-07-01)" for forty-six days,
and the r27 procurement ask was restated eight times and then simply vanished
from r33 onward.

LAYER LAW: pure Python, no `bpy`, no PIL, no network.
"""

import argparse
import datetime
import json
import os
import sys

TIERS_REL = "qa/sourcing-tiers.json"

# A row is a gap declaration if it says so in a field or in its own prose. The
# prose half exists for the same reason the order-marker scan does in
# `orders_check`: D-074 declared its gap in a sentence, and a checker that only
# reads a key it hoped somebody would set is a checker that never fires.
GAP_MARKERS = ("SOURCING GAP", "sourcing gap", "declared gap", "DECLARED GAP",
               "ประกาศเป็น SOURCING GAP", "declared_gap")

STATUS_HEADS = ("searched", "not-attempted", "refused", "n/a")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def load(path=None, repo_root=None):
    p = path or os.path.join(repo_root or _repo_root(), TIERS_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def tiers(data):
    t = (data or {}).get("tiers")
    return [x for x in t if isinstance(x, dict)] if isinstance(t, list) else []


def paid_tiers(data):
    return [t for t in tiers(data) if t.get("owner_decision")]


def _blob(d):
    """`in_effect` ONLY, and the narrowing is load-bearing. A gap is DECLARED in
    what is now true because of the row; `because` is where the rule gets cited
    as reasoning ("R8 says a failed purchase is a declared gap"), and scanning
    it made D-067 — a row stating that its class was ALREADY acquired — read as
    a gap declaration. A marker that fires on the reasoning instead of the
    result is a marker that gets switched off."""
    return str(d.get("in_effect") or "")


def is_gap(d):
    if d.get("superseded_by"):
        return False        # history; rows never leave, but they stop governing
    if d.get("kind") == "procurement-ask":
        # RECLASSIFIED. The row's own words still say "DECLARED GAP" because
        # that is what it said when it was written, and rewriting history to
        # please a checker is worse than the checker being wrong. The `kind`
        # key outranks the prose, and it is a HIGHER bar, not an escape: an ask
        # must carry a price, a measured spec, and a channel that exists.
        return False
    # THE R10 SPEC KEY IS NOT A SOURCING SENTENCE. `declared_gaps.<mass>` is
    # the object-existence register (R10: "the absent thing is honest"), and
    # the "declared_gap" marker matching INSIDE that key is a substring
    # accident, not a declaration about the market — D-014 removes a hand-built
    # desk pier and cites `declared_gaps.desk_pier`, and this scan read that as
    # a claim that a purchase was never tried. Masking the KEY FORM only (the
    # plural key followed by a dot) is scope derived from the rule's own
    # premise (R9b), not a silence chosen to pass: a prose "declared gap"
    # about an asset class still fires.
    blob = _blob(d).replace("declared_gaps.", "")
    return d.get("kind") == "sourcing-gap" or any(m in blob
                                                  for m in GAP_MARKERS)


def check(data, decisions, unit=None, repo_root=None, path_hint=TIERS_REL):
    """Violations. Every one is the builder's side: a gap claimed wider than the
    search that produced it, or an ask filed with no price and no channel."""
    if data is None:
        return [f"no readable sourcing-tier roster at {path_hint}. Without it "
                f"'nothing exists' is unfalsifiable — it means 'nothing exists "
                f"in the tiers I happened to search', and this repo has already "
                f"paid for that sentence once."]
    root = repo_root or _repo_root()
    v = []

    if data.get("paid_permitted") is not True:
        v.append("qa/sourcing-tiers.json says paid sources are not permitted. "
                 "He cancelled that fence himself on 2026-08-01 — "
                 "\"฿0 + CC0/public-domain เท่านั้น ยกเลิกข้อนี้\" — and only he "
                 "can put it back.")

    ids = [t.get("id") for t in tiers(data)]
    paid = [t.get("id") for t in paid_tiers(data)]

    rows = [d for d in ((decisions or {}).get("decisions") or [])
            if isinstance(d, dict) and (unit is None or d.get("unit") == unit)]

    for d in rows:
        did = d.get("id") or "<no id>"
        gap = is_gap(d)
        ask = d.get("kind") == "procurement-ask" and not d.get("superseded_by")
        if not (gap or ask):
            continue

        got = d.get("tiers")
        if not isinstance(got, dict):
            v.append(f"{did} declares a sourcing gap with no `tiers` record, so "
                     f"nobody can tell which half of the world it searched. "
                     f"D-074 was measured against 68 free-tier folders and "
                     f"written as if it were measured against the market.")
            continue

        missing = [i for i in ids if i not in got]
        if missing:
            v.append(f"{did}: `tiers` says nothing about {', '.join(missing)}. "
                     f"A tier with no entry is a tier nobody looked at, and "
                     f"silence about it reads as coverage.")

        for tid, status in got.items():
            if tid not in ids:
                v.append(f"{did}: `tiers` names '{tid}', which is not a tier in "
                         f"{TIERS_REL}.")
            elif not any(str(status).startswith(h) for h in STATUS_HEADS):
                v.append(f"{did}: tier '{tid}' carries status {status!r}. Use "
                         f"{'/'.join(STATUS_HEADS)} — a free-text status is a "
                         f"status nothing can count.")

        unattempted = [t for t in paid
                       if str(got.get(t, "")).startswith("not-attempted")]
        if gap and unattempted:
            v.append(f"{did} is filed as a GAP while {', '.join(unattempted)} "
                     f"read 'not-attempted'. THAT IS NOT A GAP, IT IS AN UNMADE "
                     f"PURCHASE: R8 permits paid libraries and says a spend is "
                     f"his call per purchase, so file this as "
                     f"kind='procurement-ask' with a price and route it to him. "
                     f"'We have not bought one' printing as 'one does not "
                     f"exist' is how this lane talked itself back into "
                     f"hand-modelling the class R8 forbids.")

        if ask:
            for k in ("ask_price", "ask_spec", "ask_routed_at"):
                if not d.get(k):
                    v.append(f"{did} is a procurement ask with no `{k}`. An ask "
                             f"he cannot price, cannot check against a "
                             f"measurement, or cannot find is an ask that will "
                             f"be dropped — which is what happened to the r27 "
                             f"ask after eight restatements.")
            for rel in str(d.get("ask_routed_at") or "").split(","):
                rel = rel.strip()
                if rel and not os.path.exists(os.path.join(root, rel)):
                    v.append(f"{did}: `ask_routed_at` names {rel}, which does "
                             f"not exist. An ask routed nowhere was never made "
                             f"— the same test a decision's `where` gets.")
    return v


def open_asks(decisions, unit=None, today=None):
    """[(row, age_days)] for procurement asks with no recorded answer, oldest
    first. AGE is the point: an ask does not get refused here, it gets
    forgotten, so the number that has to be visible is how long it has been
    waiting."""
    today = today or datetime.date.today()
    out = []
    for d in ((decisions or {}).get("decisions") or []):
        if not isinstance(d, dict) or d.get("kind") != "procurement-ask":
            continue
        if unit is not None and d.get("unit") != unit:
            continue
        if d.get("ask_answered"):
            continue
        try:
            when = datetime.date.fromisoformat(str(d.get("decided_date")))
            age = (today - when).days
        except ValueError:
            age = None
        out.append((d, age))
    return sorted(out, key=lambda r: -(r[1] or 0))


def one_line(d, age):
    aged = f"{age}d" if age is not None else "age unknown"
    return (f"  {d.get('id')} [{aged}] {d.get('ask_spec')}\n"
            f"      ราคา: {d.get('ask_price')}  → {d.get('ask_routed_at')}")


def main():
    ap = argparse.ArgumentParser(
        description="Sourcing tiers, and whether a declared gap actually "
                    "searched them. Exits 1 when an unmade purchase is filed "
                    "as an absence.")
    ap.add_argument("--unit", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--decisions", default=None)
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

    print("SOURCING TIERS (R8 — a gap is only a gap once all of these are "
          "searched):")
    for t in tiers(data):
        mark = "  [ของพี่ตัดสิน]" if t.get("owner_decision") else ""
        print(f"  {t.get('id'):<18} {t.get('cost'):<28} {t.get('name')}{mark}")

    asks = open_asks(dec, a.unit)
    if asks:
        print("\nการซื้อที่รอพี่ตัดสิน (ไม่มีอะไรบล็อกเลนอยู่ — R3):")
        for d, age in asks:
            print(one_line(d, age))

    v = check(data, dec, a.unit, root, a.file or TIERS_REL)
    for s in v:
        print(f"  !! {s}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
