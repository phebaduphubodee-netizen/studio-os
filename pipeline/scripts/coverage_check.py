"""coverage_check.py — the MISSING-object half of R10. PURE (no bpy).

    python pipeline/scripts/coverage_check.py --spec <spec.json> --manifest <manifest.json>

WHY THIS FILE EXISTS
--------------------
`rule_gate.audit_spec` asks, of every mass in the spec: *does this thing deserve
to exist?* That direction caught a bare post that "carries shade" and a 775 mm
fin standing free on the floor. It is one direction of one question, and the
other direction has never had an instrument at all:

    **which object that the reference SHOWS has no mass in our scene?**

The score of that omission, from this lane's own record:

  - the partition had NO OPENING for thirty rounds, and every instrument read the
    region as "too bright and too flat" — which was TRUE — and sent the round to
    the materials lane
  - `blind` had a mesh generator with a measured pitch, a builder, a PALETTE row,
    three tests, and its own area light. It never once appeared as a mass in any
    of thirty specs
  - `chair_leg_1..4` existed in spec_r12 and vanished at r14. Eighteen rounds, no
    instrument noticed, because nothing counted objects

The mechanism is not carelessness and it is not laziness. Every instrument in
this lane compares OUR VALUE AT A POINT with THE TARGET'S VALUE AT THE SAME
POINT. A missing object is not an error of value. It is an error of INVENTORY,
and an inventory error is invisible to every per-pixel comparison — the windows
that fall on the wall that should have been an opening report a perfect match
with the wall that is there.

That blindness is not local folklore. The published image-quality literature says
the same thing about windowed metrics (SSIM and its family are computed over a
sliding window; a large missing object averages away), and the inverse-graphics
literature says it about staged reconstruction: SEIG ("Thinking in Blender",
He, Luo, Ma & Averbuch-Elor, Cornell, arXiv 2606.02580) gives its INITIALISATION
stage a verifier whose only job is **object presence**, scoped so that it "judges
only the active factor … while ignoring errors assigned to other stages", and
selects among sampled scaffolds "the candidate with the most complete object
coverage". Their reported failure mode is ours verbatim: *"errors introduced in
early stages may propagate throughout the pipeline, leading to local minima from
which later stages cannot easily recover."* Thirty rounds of material and light
work on a wall that should have been a doorway is that sentence, paid for.

WHAT THIS CHECKS
----------------
A MANIFEST lists what the reference shows. For every entry, the spec must answer
in one of exactly two ways:

    BUILT   — a mass exists for it (by name, by name-prefix, or by an explicit
              `built_as` list in the manifest entry)
    ABSENT  — the spec's `declared_gaps` carries the id, WITH a reason

Anything else is UNCOVERED and fails. "Unresolved" is not a third state that can
be left lying around: an object either got built or got declared, and a declared
gap is a decision the owner can see and overrule. The absent thing is honest; the
un-mentioned thing is the defect.

THE RATCHET
-----------
`absent_baseline` in the manifest is the set of ids allowed to be ABSENT today.
It may SHRINK and may never GROW. Without it, `declared_gaps` becomes the licence
it was written to prevent — anything inconvenient gets declared away and the
check passes forever. This is the same shape as the `ORPHAN_ROWS` ratchet that
already works in this lane, and it is here for the same reason: a list that can
grow is not a constraint.

WHAT IT DOES NOT DO, on purpose
-------------------------------
It cannot see the reference. It cannot tell whether the manifest is COMPLETE —
an object nobody wrote down is invisible to it exactly as it is invisible to
every other instrument here. That is why `--require-manifest` fails closed on a
missing or empty manifest rather than reporting "0 violations": a mute check and
a passing check are indistinguishable from the outside, and this lane has already
lost one debt instrument to precisely that.
"""
import argparse
import json
import sys


MIN_EXTENT_MM = 1.0


def _mass_names(spec):
    """Names of masses that could plausibly BE something.

    A mass with a zero (or sub-millimetre) extent resolves a manifest entry
    while occupying no space and casting no shadow. Measured 2026-08-08: seven
    0x0x0 masses named after the seven UNCOVERED entries, dropped at the world
    origin with a fabricated `seen` string, passed the whole gate — R10
    justification, coverage, and require_seen. "Something exists with this name"
    is not the question this check asks; "the reference shows it and we built
    it" is. A degenerate mass answers the first and not the second.

    Not a tolerance to tune: 1 mm is below anything this lane can measure (its
    finest fits land at +/-0.6 mm on a 526 mm module) and far below anything a
    frame can show.
    """
    out = []
    for m in spec.get("masses", []):
        n = m.get("name")
        if not n:
            continue
        s = m.get("s")
        if isinstance(s, (list, tuple)) and len(s) == 3:
            try:
                if min(abs(float(x)) for x in s) < MIN_EXTENT_MM:
                    continue
            except (TypeError, ValueError):
                pass
        out.append(n)
    return out


def resolve(entry, names, gaps):
    """Return (state, detail) for one manifest entry.

    state is "BUILT", "ABSENT", or "UNCOVERED". An entry may name the masses that
    realise it via `built_as` — needed because an object in a photograph
    ("the chair") is often several masses in a spec ("chair_leg_1..4", "chair_seat"),
    and forcing the manifest to speak the spec's naming would make the manifest a
    restatement of the build instead of a reading of the reference.
    """
    eid = entry["id"]
    want = entry.get("built_as") or []
    e_prefix = bool(entry.get("prefix"))
    if want:
        hit = [n for n in want if n in names]
        if hit:
            return "BUILT", f"masses {hit}"
        # A `built_as` that names nothing is worse than none: it reads as a claim
        # that the object was built. Fall through to the gap check, then fail.
    else:
        # EXACT by default; prefix matching is opt-in per entry.
        #
        # The first draft of this function prefix-matched by default, and its own
        # negative control killed it: a scene carrying `blind_light` — the area
        # light named after the blind — resolved the manifest entry `blind` to
        # BUILT. That is not a hypothetical. The real lane had exactly that light,
        # with a comment saying its job was to graze slats that did not exist, and
        # the whole point of this check is to notice the slats are missing. A
        # namesake is not the object, so a match that accepts one is a check that
        # would have passed the defect it was written for.
        hit = [n for n in names if n == eid]
        if not hit and e_prefix:
            hit = [n for n in names if n.startswith(eid + "_")]
        if hit:
            return "BUILT", f"masses {hit}"
    reason = gaps.get(eid)
    if isinstance(reason, str) and reason.strip():
        return "ABSENT", reason.strip()
    if eid in gaps:
        return "UNCOVERED", "declared_gaps carries the id with an EMPTY reason"
    return "UNCOVERED", "no mass and no declared gap"


def _gaps(spec):
    """`declared_gaps` as {id: reason}, and a note if the spec lost its reasons.

    r32 turned this field from a dict into a LIST, by round-tripping it through
    `list(spec.get("declared_gaps", []))` — which on a dict yields its KEYS and
    silently drops all ten reasons. The names survived; the decisions did not.
    A bare name is not a declared gap under R10: the reason is the entire content
    of the declaration, because it is what the owner reads and can overrule.

    So the list form is accepted (a spec that exists must be auditable) and every
    entry in it is reported as reason-less rather than counted as a declaration.
    """
    g = spec.get("declared_gaps")
    if isinstance(g, dict):
        return g, None
    if isinstance(g, list):
        return {k: "" for k in g if isinstance(k, str)}, (
            f"`declared_gaps` is a LIST of {len(g)} names with no reasons — a gap "
            f"without a reason is a name, not a decision (r32 lost ten reasons to "
            f"`list(dict)`). Nothing in it can satisfy a manifest entry.")
    return {}, None


def audit(spec, manifest):
    """Return (rows, violations). Pure; no I/O, no exit."""
    names = _mass_names(spec)
    gaps, shape_note = _gaps(spec)
    entries = manifest.get("entries") or []
    # PRESENCE of the key, not truthiness of the list. `absent_baseline: []` is a legal
    # SHRINK to zero, and with `and baseline` guarding the test below, emptying the list
    # simultaneously satisfied the ratchet AND switched off the only check policing new
    # declared_gaps — the cheapest possible bypass, found by an adversarial pass on
    # 2026-08-08. An empty ratchet must mean "nothing may be absent", never "anything may".
    has_baseline = "absent_baseline" in manifest
    baseline = set(manifest.get("absent_baseline") or [])

    rows, violations = [], []
    if shape_note:
        violations.append(shape_note)

    # ONE MASS MAY NOT REALISE TWO OBJECTS. Pointing every unbuilt entry's
    # `built_as` at a mass that is already in the scene resolved all seven to
    # BUILT with a manifest-only edit and no new geometry (measured 2026-08-08).
    # Full correspondence is semantic and stays out of reach here — but a mass
    # claimed twice is a claim that cannot be true either way, and it is the
    # shape the cheap version of that fraud takes. KNOWN LIMIT, stated rather
    # than papered over: a `built_as` naming ONE unrelated mass still passes.
    claimed = {}
    for e in entries:
        for m in e.get("built_as") or []:
            claimed.setdefault(m, []).append(e.get("id", "?"))
    for m, ids in sorted(claimed.items()):
        if len(ids) > 1:
            violations.append(
                f"mass `{m}` is claimed by {len(ids)} manifest entries "
                f"({', '.join(sorted(ids))}) — one mass cannot be two objects the "
                f"reference shows separately")

    seen_ids = set()
    for e in entries:
        eid = e.get("id", "")
        if not eid:
            violations.append("manifest entry with no `id`")
            continue
        if eid in seen_ids:
            violations.append(f"manifest lists `{eid}` twice")
        seen_ids.add(eid)
        state, detail = resolve(e, names, gaps)
        rows.append({"id": eid, "what": e.get("what", ""), "state": state, "detail": detail})
        if state == "UNCOVERED":
            violations.append(
                f"UNCOVERED `{eid}` ({e.get('what', 'no description')}): {detail} — "
                f"the reference shows it; build it or declare it a gap with a reason")
        elif state == "ABSENT" and has_baseline and eid not in baseline:
            # The ratchet. A NEW absence is a decision, and a decision that
            # appears only as a new key in declared_gaps is a decision nobody made.
            violations.append(
                f"NEW ABSENCE `{eid}` is not in `absent_baseline` — an object may "
                f"leave the frame, but not quietly: add it to the baseline in the "
                f"same edit that declares the gap, so the list is auditable")

    for gone in sorted(baseline - {r["id"] for r in rows if r["state"] == "ABSENT"}):
        if gone in seen_ids:
            rows.append({"id": gone, "what": "", "state": "RATCHET-CLOSED",
                         "detail": "was an allowed absence and is now built — "
                                   "drop it from `absent_baseline`"})
    return rows, violations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--require-manifest", action="store_true",
                    help="fail when the manifest is missing or empty (a mute check "
                         "and a passing check look identical from outside)")
    ap.add_argument("--soft", action="store_true", help="report, exit 0")
    a = ap.parse_args()

    spec = json.loads(open(a.spec, encoding="utf-8").read())
    try:
        manifest = json.loads(open(a.manifest, encoding="utf-8").read())
    except FileNotFoundError:
        msg = f"COVERAGE: no manifest at {a.manifest}"
        if a.require_manifest and not a.soft:
            sys.exit(msg + " — refusing to report coverage nobody declared")
        print(msg + " (advisory)")
        return

    rows, violations = audit(spec, manifest)
    if not rows and a.require_manifest and not a.soft:
        sys.exit("COVERAGE: manifest is empty — a coverage claim with no entries "
                 "is the mute that this check exists to prevent")

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    tally = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    print(f"COVERAGE: {len(rows)} manifest entries — "
          + ", ".join(f"{v} {k}" for k, v in sorted(tally.items())))
    for r in rows:
        if r["state"] != "BUILT":
            print(f"  [{r['state']}] {r['id']}: {r['detail']}")
    if violations:
        print(f"COVERAGE VIOLATIONS ({len(violations)}):")
        for v in violations:
            print("  - " + v)
        if not a.soft:
            sys.exit(1)


if __name__ == "__main__":
    main()
