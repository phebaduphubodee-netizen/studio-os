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
        if UNMEASURABLE.search(prov) and name not in gaps and not m.get("why"):
            out.append(
                f"{name}: its own provenance says the measurement was not "
                f"possible, yet a number was typed. R10 corollary: the moment a "
                f"measurement pass reports UNMEASURABLE, typing a value for it is "
                f"the defect. Declare it in `declared_gaps` or justify it in `why`.")
    return out


def audit_bundle(bundle_dir):
    """R7 — every critic item gets a WRITTEN triage. Returns [violation str]."""
    out = []
    if not os.path.isdir(bundle_dir):
        return [f"bundle dir not found: {bundle_dir}"]
    answers = sorted(glob.glob(os.path.join(bundle_dir, "ANSWER_*.md")))
    if not answers:
        return out                      # no critic has filed yet; nothing owed
    readme = ""
    rp = os.path.join(bundle_dir, "README.md")
    if os.path.exists(rp):
        with open(rp, encoding="utf-8") as f:
            readme = f.read()
    for a in answers:
        stem = os.path.basename(a)[len("ANSWER_"):-len(".md")]
        has_file = os.path.exists(os.path.join(bundle_dir, f"TRIAGE_{stem}.md"))
        has_section = re.search(rf"{re.escape(stem)}.{{0,40}}triage|triage.{{0,40}}"
                                rf"{re.escape(stem)}", readme, re.I | re.S)
        if not (has_file or has_section):
            out.append(
                f"{os.path.basename(a)} has no triage. R7: every returned item "
                f"gets a written accept+lane or a refutation carrying a "
                f"MEASUREMENT — never taste. Write TRIAGE_{stem}.md or a "
                f"'{stem} triage' section in the bundle README.")
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


def check(spec, bundle_dir=None, inbox_root=None, require_seen=False):
    v = audit_spec(spec, require_seen)
    if bundle_dir:
        v += audit_bundle(bundle_dir)
    if inbox_root:
        v += audit_learning(spec, inbox_root)
    return v


def enforce(spec, bundle_dir=None, inbox_root=None, hard=True, require_seen=False):
    """Print and, if hard, refuse to continue. Called by the builder."""
    v = check(spec, bundle_dir, inbox_root, require_seen)
    if not v:
        print(f"RULE GATE: {len(spec.get('masses', []))} masses, all justified")
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
    ap.add_argument("--inbox", default=None)
    ap.add_argument("--soft", action="store_true", help="report, do not exit 1")
    ap.add_argument("--require-seen", action="store_true",
                    help="R10 q2: every mass must point at itself in the reference")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    v = enforce(spec, a.bundle, a.inbox, hard=not a.soft,
                require_seen=a.require_seen)
    sys.exit(0 if not v else 0)


if __name__ == "__main__":
    main()
