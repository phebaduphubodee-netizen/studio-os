"""existence_check.py — R10 AS ROWS: does every object in the frame justify its own
existence, and can it be BUILT and USED?

PURE, NO `bpy` (pipeline/CLAUDE.md layer law). It reads a scene dump and a ledger and
returns violation strings; it never opens Blender and never edits anything.

WHY IT EXISTS, and the count is the argument. R8 governs HOW an object is made and R9
governs WHERE it goes. R10 was written on 2026-08-05 because nothing governed WHETHER
IT SHOULD EXIST — and twelve days later, at p2r47, TWO independent critics filed three
defects of exactly that class against one frame:

  * the foot bench "is TWO stacked upholstered cushions ... a soft block sitting on
    another soft block has nothing to transfer load to the legs and would splay";
  * the drawer fronts "have no pulls, no finger reveal, and no visible way to open
    them ... which fails the 'could this be built and used' test";
  * "no switch plate anywhere, including beside the bed for the sconces; no sockets;
    no skirting or shadow-gap where wall meets floor on ANY wall."

The round's own triage accepted all three with the same sentence — *no instrument in
this repo can see this* — and it was right. Everything that iterates masses on this
lane asks whether a mass has a PROVENANCE TAG (`audit_spec`), whether it FITS its slot
(`model_fit`), what it is MADE OF (`fineness`, `map_census`), or whether it is standing
on something at all (`placement_check`, AABBs only, whose own docstring says "They are
NOT geometry"). None of them asks whether the thing could exist.

THREE DESIGN RULES, each paid for by a defect already in this repo's ledger:

1. THE OBJECT LIST IS DERIVED FROM THE BUILT SCENE, NEVER KEPT HERE. R9b: "a rule that
   names the objects it applies to will always exempt the next one" — the guard it
   replaced covered 2 of 5 placed classes and every figure was exempt. Assemblies come
   from `sheet_recon.assemblies_from_dump`, the repo's EXISTING definition of "one
   object", so this module does not add a second one (the drift `bedcloth_fit` was
   written to end). An in-frustum assembly with no row is a VIOLATION; nothing can be
   exempt by being forgotten.

2. IDENTITY IS SIGNED, CONSEQUENCES ARE MEASURED. R12's law — identity is human-signed,
   never derived, and `pending` is refused by name — because no program can look at a
   box and know it is a drawer. So the ledger DECLARES what a thing is and whether it
   opens; this module then checks every consequence of that declaration against the
   dump: a named support must exist, a claimed reveal must MEASURE, a row that says
   `remove` must correspond to an object that is actually gone.

3. AN ABSENCE CLAIM NEEDS A POSITIVE CONTROL. R11's own record: r38 quoted "no step at
   u=989" as proof until a same-class corner that certainly exists scored the same
   3.5 L. So `reveal_mm` is not a checkbox — the gap is measured in the dump and
   compared to the declared number, which means the rung can only pass if it can see a
   reveal that is there. `--selftest` runs that control explicitly.

WHAT IT DELIBERATELY DOES NOT DO. It cannot tell whether a declared identity is TRUE —
the same limit `audit_spec` states about provenance tags ("`why: carries the shade`
passes the syntax and is exactly the reasoning that produced the defect"). What it
changes is that the claim now has to be WRITTEN, is counted, ages in public, and its
consequences are checkable. The eye still finds what is wrong (R7b); this makes the
finding survive the round it was found in.

  python pipeline/scripts/existence_check.py <scene.json> [--ledger qa/object-existence.json]
  python pipeline/scripts/existence_check.py --selftest

Exit: 0 clean · 1 a blocking violation · 2 COULD NOT RUN (R11's contract — "could not
look" must never print like "looked and it was fine").
"""
import json
import os
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER_REL = os.path.join("qa", "object-existence.json")

VERDICTS = ("keep", "fix", "remove", "unresolved")
# `pending` is refused BY NAME, the same way `decisions_check` refuses it: a row that
# says "pending" is a row nobody has to answer, and this repo has 21 dropped asks that
# started as one.
REFUSED_VERDICTS = ("pending", "tbd", "todo", "later", "?")
# An EXISTS answer has to point at something. The three legal shapes are R10's own
# question 2 — "point at it in the reference, or say plainly that nothing is there" —
# plus the sheet, which R12 makes the reference of record on this lane.
EXISTS_PREFIXES = ("sheet:", "reference:", "not-in-drawing:")
THIN_REASON_MIN = 12          # same spirit as sheet_recon's not-in-drawing minimum
# Below this footprint an assembly is a fitting, not a mass — but it still needs a row;
# the number only decides how loudly a MISSING row prints, never whether one is needed.
SMALL_M2 = 0.01


def _norm(s):
    return " ".join(str(s or "").split())


def load_ledger(path=None):
    p = path or os.path.join(REPO, LEDGER_REL)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_dump(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("objects") or []


def assemblies(objects):
    """The repo's OWN grouping, imported rather than reimplemented (see rule 1)."""
    import sheet_recon
    return sheet_recon.assemblies_from_dump(objects)


def in_frame(a):
    """True / False / None(unknown). UNKNOWN COUNTS AS IN-FRAME, deliberately: the
    vacuous-zero law this repo wrote for `sheet_recon` — absence of evidence must never
    read as clearance."""
    return a.get("in_frustum") is not False


def touches(a, b, tol_mm=25.0):
    """Do two assemblies' plan footprints overlap and their z-spans meet?

    The support test is deliberately CRUDE and says so: it asks whether the named
    carrier is in contact at all, not whether the joint is sound. `placement_check`'s
    own docstring draws the same line ("AABBs ... are NOT geometry"). What it can
    refuse is the case this rung exists for — a support that is named and is NOT THERE,
    or is nowhere near the thing it is said to carry, which is R3's `where` test
    ("a decision in force nowhere was never taken") applied to load paths.
    """
    ax0, ay0, aw, ad = a["rect_mm"]
    bx0, by0, bw, bd = b["rect_mm"]
    if (ax0 > bx0 + bw + tol_mm or bx0 > ax0 + aw + tol_mm
            or ay0 > by0 + bd + tol_mm or by0 > ay0 + ad + tol_mm):
        return False
    lo = max(a["zmin_m"], b["zmin_m"]) * 1000.0
    hi = min(a["zmax_m"], b["zmax_m"]) * 1000.0
    return hi >= lo - tol_mm


def measured_reveal_mm(asm, token):
    """The smallest vertical gap between adjacent parts of THIS assembly whose names
    carry `token`, in mm — or None when fewer than two such parts exist.

    IT IS A MEASUREMENT AND NOT A PRESENCE COUNT, which is the whole difference from
    the door that burned this repo before. `DEBT-10`'s record: `match: "handle"` with
    min_count 1 "was already satisfied by `door_handle`, the ENTRANCE door's lever ...
    A substring match is a door onto whatever happens to share a syllable." The token
    here is scoped to ONE human-signed assembly and it selects the parts to MEASURE
    BETWEEN; a wrong selection makes the number wrong and the row fail, it does not
    make the row pass. And a claim of `reveal_mm` can only be satisfied if the checker
    can actually see a gap of that size — the positive control R11 demands.
    """
    recs = [r for r in asm["part_recs"] if token in r["name"] and "aabb" in r]
    if len(recs) < 2:
        return None
    spans = sorted(((r["aabb"][0][2] * 1000.0, r["aabb"][1][2] * 1000.0)
                    for r in recs), key=lambda s: s[0])
    gaps = [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)]
    gaps = [g for g in gaps if g > -1e-6]
    return min(gaps) if gaps else None


def _age_days(iso, today=None):
    try:
        y, m, d = (int(v) for v in str(iso).split("-"))
    except Exception:                                          # noqa: BLE001
        return None
    return ((today or date.today()) - date(y, m, d)).days


def check(objects, ledger, today=None):
    """(violations, notes, summary). Violations BLOCK; notes print."""
    v, notes = [], []
    rows = ledger.get("objects") or []
    req = ledger.get("required_elements") or []

    asms = assemblies(objects)
    by_name = {a["name"]: a for a in asms}
    # A PREFIX RESOLVES TO ITS LARGEST COMPONENT so the geometric checks below still
    # RUN for a prefix row instead of being silently skipped — "a rung that did not run
    # must never read like a rung that passed" applies to this file too.
    for a in sorted(asms, key=lambda r: r["footprint_m2"]):
        by_name.setdefault(a["name"].split("@")[0], a)
        if a["footprint_m2"] >= by_name[a["name"].split("@")[0]]["footprint_m2"]:
            by_name[a["name"].split("@")[0]] = a
    live = set(by_name)
    framed = [a for a in asms if in_frame(a)]

    # ---- the ledger's own honesty, before it is asked about anything -------------
    seen = {}
    for i, r in enumerate(rows):
        key = _norm(r.get("assembly"))
        if not key:
            v.append(f"object-existence row #{i} has no `assembly` — a row that names "
                     f"nothing cannot be matched to anything")
            continue
        if key in seen:
            v.append(f"object-existence: {key!r} carries two rows; one object, one "
                     f"verdict, or nobody can say which verdict is in force")
        seen[key] = r

    for key, r in sorted(seen.items()):
        vd = _norm(r.get("verdict")).lower()
        if vd in REFUSED_VERDICTS:
            v.append(f"object-existence {key}: verdict {vd!r} is refused BY NAME — "
                     f"one of {', '.join(VERDICTS)}, or the row is a queue nobody "
                     f"has to visit")
            continue
        if vd not in VERDICTS:
            v.append(f"object-existence {key}: verdict {vd!r} is not one of "
                     f"{', '.join(VERDICTS)}")
            continue
        if not _norm(r.get("identity")):
            v.append(f"object-existence {key}: no `identity` — R10 question 1 is "
                     f"'what is it', and a row that cannot answer it is not a row")
        ex = _norm(r.get("exists"))
        if not ex.startswith(EXISTS_PREFIXES):
            v.append(f"object-existence {key}: `exists` must start with one of "
                     f"{', '.join(EXISTS_PREFIXES)} — {ex[:40]!r} points at nothing")
        elif ex.startswith("not-in-drawing:") and len(ex.split(":", 1)[1].strip()) < THIN_REASON_MIN:
            v.append(f"object-existence {key}: 'not-in-drawing' with a {len(ex.split(':', 1)[1].strip())}-"
                     f"character reason is refused — say what it is and why it is there")

        # ---- SENSE: the load path ------------------------------------------------
        held = _norm(r.get("held_by"))
        if vd in ("keep", "fix"):
            if not held:
                v.append(f"object-existence {key}: `held_by` is missing — R10 question "
                         f"3 asks whether it could stand up, and an unanswered load "
                         f"path is how a soft block ended up on a soft block")
            elif held not in ("floor", "wall", "ceiling", "hangs", "self"):
                if held not in live:
                    v.append(f"object-existence {key}: held_by {held!r} is not in the "
                             f"built scene — a support that is named and absent is a "
                             f"load path nobody took (R3's `where` test)")
                elif key in by_name and not touches(by_name[key], by_name[held]):
                    v.append(f"object-existence {key}: held_by {held!r} exists but "
                             f"does not touch it — the named carrier is somewhere "
                             f"else in the room")

        # ---- SENSE: can it be used ----------------------------------------------
        if r.get("operable"):
            ob = r.get("opens_by") or {}
            if not isinstance(ob, dict) or not ob:
                v.append(f"object-existence {key}: declared operable with no "
                         f"`opens_by` — a drawer that cannot be opened is the p2r47 "
                         f"item, and 'it has no handle' is only acceptable when the "
                         f"mechanism that replaces the handle is named")
            elif "pull" in ob:
                if _norm(ob["pull"]) not in live:
                    v.append(f"object-existence {key}: opens_by.pull names "
                             f"{ob['pull']!r}, which is not in the built scene")
            elif "push_to_open" in ob:
                if not _norm(ob["push_to_open"]).startswith("D-"):
                    v.append(f"object-existence {key}: push-to-open must cite the "
                             f"decision row that signed it (D-nnn); an invisible "
                             f"mechanism asserted with no signature is indistinguish"
                             f"able from having forgotten the handle")
            elif "reveal_mm" in ob:
                token = _norm(ob.get("between"))
                if not token:
                    v.append(f"object-existence {key}: opens_by.reveal_mm needs "
                             f"`between` — which parts the gap is between, or nothing "
                             f"can measure it")
                elif key in by_name:
                    got = measured_reveal_mm(by_name[key], token)
                    want = float(ob["reveal_mm"])
                    if got is None:
                        v.append(f"object-existence {key}: opens_by claims a "
                                 f"{want:.0f} mm reveal between {token!r} parts and "
                                 f"the dump has fewer than two of them — COULD NOT "
                                 f"MEASURE, which is not a pass")
                    elif abs(got - want) > 2.0:
                        v.append(f"object-existence {key}: claims a {want:.0f} mm "
                                 f"reveal, the built scene measures {got:.1f} mm")
                    else:
                        notes.append(f"  reveal {key}: claimed {want:.0f} mm, "
                                     f"measured {got:.1f} mm — the gap is really there")
            else:
                v.append(f"object-existence {key}: opens_by must carry one of "
                         f"`pull`, `reveal_mm` or `push_to_open`; "
                         f"{sorted(ob)!r} names no mechanism")

        # ---- VERDICT bookkeeping -------------------------------------------------
        if vd == "fix" and not _norm(r.get("fix_by")):
            v.append(f"object-existence {key}: verdict 'fix' with no `fix_by` — a fix "
                     f"nobody named is a wish")
        if vd == "remove" and key in live:
            v.append(f"object-existence {key}: verdict 'remove' and it is STILL IN "
                     f"THE BUILT SCENE — a decision recorded and not carried out")
        if vd == "unresolved":
            if not _norm(r.get("since")):
                v.append(f"object-existence {key}: 'unresolved' with no `since` — an "
                         f"open question with no age is one nobody has to close")
            else:
                age = _age_days(r.get("since"), today)
                notes.append(f"  UNRESOLVED {key}: {r.get('why') or ''} "
                             f"({age} day(s))" if age is not None else
                             f"  UNRESOLVED {key}: {r.get('why') or ''}")

    # ---- NO OBJECT MAY BE EXEMPT BY BEING FORGOTTEN, AND IT IS A RATCHET ---------
    # R13's own warning, taken seriously: "a machine that hard-fails every historical
    # instance on day one gets switched off and joins them". On the day this shipped
    # the frame held 44 in-frame assemblies and the ledger could not have covered them
    # all at once. So the BACKLOG prints and may only SHRINK — `baseline_unrowed` is
    # the high-water mark and every build compares against it — while any NEW object
    # arriving without a row fails immediately, because it pushes the count above the
    # line. Same shape as `baseline_ratchet` and the spec-ratchet, for the same reason.
    # A ROW MAY COVER A PREFIX FAMILY, and the reason is that assembly names carry
    # COORDINATES. `sheet_recon` disambiguates the spatial components of one name
    # prefix as `skirt@5485,-140` — so a skirting run that moves by a millimetre gets a
    # NEW name, the row that described it goes stale, and the backlog rises for a
    # change nobody made. A bare-prefix row (`skirt`) therefore covers every component
    # of that prefix, while an exact row (`mill@3254,4621`) still wins where the
    # components really are different objects — two wardrobes are not one row.
    missing = [a for a in framed
               if a["name"] not in seen and a["name"].split("@")[0] not in seen]
    base = ledger.get("baseline_unrowed")
    for a in sorted(missing, key=lambda x: -x["footprint_m2"]):
        notes.append(f"  NO R10 ROW: {a['name']} ({len(a['parts'])} part(s), "
                     f"{a['footprint_m2']:.3f} m2) — in the frame, unjustified")
    if base is None:
        v.append("object-existence: the ledger declares no `baseline_unrowed`, so the "
                 "backlog has no ratchet and could grow unnoticed — set it to the "
                 "count this build reports and it can only fall from there")
    elif len(missing) > int(base):
        v.append(f"object-existence: {len(missing)} in-frame object(s) carry no R10 "
                 f"row, against a baseline of {int(base)}. The backlog RATCHETS: an "
                 f"object new to the frame must arrive with its justification, and "
                 f"these are the ones without one — "
                 + ", ".join(a["name"] for a in sorted(
                     missing, key=lambda x: -x["footprint_m2"])[:6]))

    # ---- REQUIRED-BUT-ABSENT ELEMENTS -------------------------------------------
    for i, e in enumerate(req):
        nm = _norm(e.get("element"))
        if not nm:
            v.append(f"object-existence required_elements[#{i}] has no `element`")
            continue
        if not _norm(e.get("why_required")):
            v.append(f"object-existence required '{nm}': no `why_required` — a rule "
                     f"about what MUST exist has to say why, or it is a preference")
        present = _norm(e.get("present_as"))
        gap = _norm(e.get("gap"))
        if present:
            hits = [a for a in asms if a["name"] == present
                    or a["name"].startswith(present)]
            if not hits:
                v.append(f"object-existence required '{nm}': present_as {present!r} "
                         f"names nothing in the built scene — the element is declared "
                         f"present and is not")
            else:
                n = sum(len(a["parts"]) for a in hits)
                need = int(e.get("min_parts") or 1)
                if n < need:
                    v.append(f"object-existence required '{nm}': {n} part(s) built, "
                             f"{need} required by its own row")
                else:
                    notes.append(f"  required {nm}: {n} part(s) as {present}")
        elif gap:
            if len(gap) < THIN_REASON_MIN:
                v.append(f"object-existence required '{nm}': a {len(gap)}-character "
                         f"gap reason is refused")
            else:
                notes.append(f"  required {nm}: DECLARED GAP — {gap}")
        else:
            v.append(f"object-existence required '{nm}': neither `present_as` nor "
                     f"`gap` — silence is the one state this row may not be in")

    summary = {"assemblies": len(asms), "in_frame": len(framed),
               "rows": len(seen), "unrowed": len(missing),
               "baseline_unrowed": base,
               "unresolved": sum(1 for r in seen.values()
                                 if _norm(r.get("verdict")).lower() == "unresolved"),
               "required": len(req)}
    return v, notes, summary


def one_line(summary):
    return (f"R10 existence: {summary['rows']} row(s) over {summary['in_frame']} "
            f"in-frame object(s) ({summary['assemblies']} built), "
            f"{summary['unrowed']} with no row (baseline "
            f"{summary['baseline_unrowed']}), {summary['unresolved']} unresolved, "
            f"{summary['required']} required-element row(s)")


def selftest():
    """The POSITIVE CONTROL, run as its own command (R11: an absence rung that cannot
    demonstrate it sees a present one is not evidence)."""
    asm = {"name": "t", "rect_mm": (0, 0, 100, 100), "zmin_m": 0.0, "zmax_m": 1.0,
           "parts": ["a_front0", "a_front1"], "footprint_m2": 0.01,
           "part_recs": [{"name": "a_front0", "aabb": [[0, 0, 0.0], [0.1, 0.1, 0.240]]},
                         {"name": "a_front1", "aabb": [[0, 0, 0.250], [0.1, 0.1, 0.490]]}]}
    got = measured_reveal_mm(asm, "front")
    assert got is not None and abs(got - 10.0) < 1e-6, got
    none = measured_reveal_mm(asm, "nothing_matches_this")
    assert none is None
    print(f"SELFTEST reveal: two fronts 10.0 mm apart measure {got:.1f} mm; a token "
          f"matching nothing returns None (could-not-measure, not a pass). OK")
    return 0


def main():
    a = [x for x in sys.argv[1:]]
    if "--selftest" in a:
        return selftest()
    if not a:
        print("usage: existence_check.py <scene.json> [--ledger <path>]")
        return 2
    dump_path = a[0]
    led = None
    if "--ledger" in a:
        led = a[a.index("--ledger") + 1]
    try:
        objects = load_dump(dump_path)
    except OSError as e:
        print(f"R10 existence: COULD NOT RUN — {e}")
        return 2
    try:
        ledger = load_ledger(led)
    except (OSError, ValueError) as e:
        print(f"R10 existence: COULD NOT RUN — ledger unreadable ({e}). A gate whose "
              f"ledger is missing has not passed; it has not looked.")
        return 2
    v, notes, summary = check(objects, ledger)
    print(one_line(summary))
    for n in notes:
        print(n)
    for x in v:
        print(f"  !! {x}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
