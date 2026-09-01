#!/usr/bin/env python3
"""round_receipt.py — WHAT THIS ROUND ACTUALLY RAN, as a file an order can be asserted against.

Owner order 2026-08-27 ("ลุยยาว ๆ", item F). The census that forced it: across 37 rows in
`qa/owner-orders.json` there are 82 `obeyed_assert` entries, and **3 of them (3.7%) name an
ARTEFACT**. Fifty-five match a definition, a constant, a comment or a docstring — they prove
a file still exists and nothing whatever about behaviour. **Twenty of the 37 rows are held up
by nothing a pipeline run could ever change.**

THE SHARPEST INSTANCE IS THE ORDER R11 CAME FROM. `ORD-2026-08-09-every-mechanism-opens-the-
picture` — *"ผมขอบังคับให้ทุกกลไก ทุกขั้นตอนต้องมองรูปจริง"* — is asserted by a grep for a
symbol. The rule that every mechanism must open the picture is itself proven by reading a
name in a source file. And `ORD-2026-08-22-process-review-actions` reads obeyed on a grep for
`DEFAULT_MODE = EEVEE` inside `glance.py`, a tool whose output directory holds zero files: the
constant proves the module was not deleted, never that the look was ever taken.

WHAT THIS FILE IS. One JSON written by the render path at the end of every round, naming each
rung, whether it RAN, its exit code, and the finding it produced. An order about a RECURRING
ACTION ("judge every render", "run gen-diff every round", "the sheet is checked first") can
then be asserted against evidence that only exists if the action happened.

WHAT IT IS NOT, said plainly so it is not oversold the way its predecessors were: it records
what the render path REPORTS about itself. It is a receipt, not an audit — it cannot catch a
rung that lies about its own exit code, and it says nothing about whether the frame is any
good. It closes exactly one gap: the difference between "the code is still here" and "the
code ran, and here is what it said".

PURE (no bpy, no PIL): build_room fills a dict as it goes and calls `write` once.
"""

import datetime
import json
import os

RECEIPT_REL = "qa/round-receipt-latest.json"
SCHEMA = "round-receipt@1"

# The rungs a full round is expected to speak for. A rung that is absent from a receipt is
# NOT the same as a rung that ran and found nothing, and keeping the roster here means the
# receipt can say which of the two happened — the same law every gate in this repo carries.
EXPECTED = (
    "rule_gate", "id_mask", "existence_check", "carry_check", "dim_check",
    "sheet_recon", "deliverable_check", "value_probe", "bed_pixels", "p2_exit",
    "delta", "gen_diff",
)


def new(round_name, quick=False, frame=True):
    return {"schema": SCHEMA, "round": round_name, "quick": bool(quick),
            "frame": bool(frame),
            "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(
                timespec="seconds"),
            "rungs": {}}


# EXIT 2 IS THIS REPO'S "COULD NOT RUN" CODE and ten of the rungs written into
# this receipt define it in their own docstrings (delta, p2_exit, transform_check,
# edge_highlight, sheet_recon, dim_check, deliverable_check, bed_pixels,
# existence_check, carry_check). R11 states the law the code has to obey:
# "could not look" must never print like "looked and it was fine".
COULD_NOT_RUN = 2


def note(receipt, rung, ran, exit_code=None, **findings):
    """Record one rung. `ran` is whether it EXECUTED, not whether it passed — a rung that
    ran and refused the frame is evidence that the rung is wired; a rung that could not run
    is the thing this repo keeps mistaking for a pass.

    EXIT 2 OVERRULES `ran`, HERE AND NOT AT THE CALL SITE. Callers were deciding `ran`
    from "subprocess.run returned a CompletedProcess", which is true for a rung that
    announced it could not measure — so `qa/round-receipt-latest.json` shipped
    `"delta": {"ran": true, "exit": 2}`, and both readers of this module (`summary`
    and `proof_tokens`) look only at `ran`, so the contradiction sat in the row with
    nobody reading it. Fixing the one call site would have been an allowlist: R9b's
    lesson is that a rule naming the objects it applies to always exempts the next one,
    so the contract lives with the field. The row keeps `exit` AND gains
    `could_not_run`, because silently rewriting a caller's argument is its own kind of
    swallowing — the receipt should say that the two disagreed, not hide that they did.
    """
    row = {"ran": bool(ran)}
    if exit_code is not None:
        row["exit"] = int(exit_code)
        if int(exit_code) == COULD_NOT_RUN and row["ran"]:
            row["ran"] = False
            row["could_not_run"] = ("exit 2 is this rung's own COULD-NOT-RUN code; "
                                    "the caller passed ran=True")
    row.update({k: v for k, v in findings.items() if v is not None})
    receipt["rungs"][rung] = row
    return receipt


def missing(receipt):
    """Expected rungs with no row at all — neither ran nor declined."""
    return [r for r in EXPECTED if r not in receipt.get("rungs", {})]


def summary(receipt):
    rungs = receipt.get("rungs", {})
    ran = [k for k, v in rungs.items() if v.get("ran")]
    notrun = [k for k, v in rungs.items() if not v.get("ran")]
    miss = missing(receipt)
    out = [f"RECEIPT {receipt.get('round')}: {len(ran)} rung(s) ran, "
           f"{len(notrun)} declined, {len(miss)} never reported"]
    if notrun:
        out.append("  did not run: " + ", ".join(sorted(notrun)))
    if miss:
        out.append("  NEVER REPORTED (neither ran nor declined): " + ", ".join(miss))
    return "\n".join(out)


def proof_tokens(receipt):
    """Flat `rung:ran` tokens for the last FULL round — the half an order asserts against.

    THE FIRST VERSION SHIPPED WITHOUT THESE AND THE GATE CAUGHT IT IN ONE RUN. An order
    was asserted with the pattern `"gen_diff"`, which matches the JSON KEY whether the
    rung ran, declined, or exploded — so the row's assertion held while its status said
    not-obeyed, and `orders_check` refused the build for exactly that inconsistency. A
    pattern that matches a key name is the same defect as a pattern that matches a
    constant, one file further along: it proves the receipt has a slot for the thing, not
    that the thing happened.

    A token appears ONLY for a rung that actually ran in a full-fidelity round, so
    `gen_diff:ran` is unforgeable by formatting and greppable by a one-line pattern.
    """
    src = receipt.get("last_full") or {}
    return sorted(f"{k}:ran" for k, v in (src.get("rungs") or {}).items()
                  if v.get("ran"))


def write(receipt, repo_root, rel=RECEIPT_REL):
    """Write the receipt, and keep a per-round copy beside it so the latest file can never
    be the only evidence that a round happened.

    THE LAST FULL ROUND IS CARRIED FORWARD, and that is a correctness requirement rather
    than a convenience. An order that says "judge EVERY render" (R7b) or "gen-diff every
    round" (ORD-2026-08-13) is about DELIVERABLE renders: R5 says the cheap playblast rung
    must stay cheap, so those rungs correctly decline on a quick frame. Asserting such an
    order against the latest receipt alone would flip it to not-obeyed every time someone
    ran a playblast — a rung that cries wolf after normal, correct work gets switched off,
    which is the failure R13 warns about by name.
    """
    path = os.path.join(repo_root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if receipt.get("frame") and not receipt.get("quick"):
        receipt["last_full"] = {"round": receipt.get("round"),
                                "written_utc": receipt.get("written_utc"),
                                "rungs": receipt.get("rungs", {})}
    else:
        prev = load(repo_root, rel) or {}
        if prev.get("last_full"):
            receipt["last_full"] = prev["last_full"]
    receipt["proof"] = proof_tokens(receipt)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1, ensure_ascii=False)
    hist = os.path.join(repo_root, "qa", "round-receipts")
    try:
        os.makedirs(hist, exist_ok=True)
        stem = str(receipt.get("round") or "round").replace(os.sep, "_")[:120]
        with open(os.path.join(hist, stem + ".json"), "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=1, ensure_ascii=False)
    except OSError:                                          # pragma: no cover
        pass                                                 # the latest file is the contract
    return path


def load(repo_root, rel=RECEIPT_REL):
    try:
        with open(os.path.join(repo_root, rel), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":                                   # pragma: no cover
    import sys
    r = load(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if r is None:
        print("no round receipt on disk — no round has reported since this rung shipped")
        sys.exit(2)
    print(summary(r))
