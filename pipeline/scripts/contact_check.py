#!/usr/bin/env python3
"""contact_check.py — a contact that lives only in prose is not a contact. PURE (no bpy).

    python pipeline/scripts/contact_check.py --spec <spec.json> [--soft]

WHAT EARNED IT, exactly, and it is one round old
------------------------------------------------
TRN-002 r37 measured the headboard panel's thickness at ~93 mm against a built
176 mm, and then could not apply it. Three masses meet in one chain:

    ward_band front face  x = -1314   (the oak wall panel)
    bed_headboard         x = -1490 .. -1314        176 mm, never measured
    bed_platform head     x = -1490   } both the platform and the mattress
    bed_mattress head     x = -1490   } have their head end EXACTLY there

Nothing in the spec said WHY they were all at -1490. The identifiability audit
(2026-08-07) had already found the answer and written it as prose: *"the head
end -1490 rides the x=-1290 chain"* — that is, the bed's head coordinate was the
ARITHMETIC RESULT of a wall plane plus a band thickness plus a headboard
thickness, and one of those three numbers was invented. Kill the 176 and the
bed's -1490 stays perfectly legal, perfectly typed, and 83 mm from the panel it
is supposed to be touching. Nothing fails, because a coordinate is always a
legal coordinate — CLAUDE.md R9, in the exact words that rule was written in.

WHY NO EXISTING GUARD IN THIS REPO CATCHES IT
---------------------------------------------
`placement_check.py` reads the BUILT scene and is the strongest instrument here,
but its three verdicts are FLOATING / OVERHANG / OFF-AXIS, all resolved against
an AABB's supports. A bed and a headboard 83 mm apart in x are BOTH standing on
the floor: neither floats, neither overhangs, neither is tipped, and the gap
between them is not interpenetration either. It sails through. Its own docstring
names the missing piece and asks for it by name — *"that takes real contact
geometry, or a declared `rest_on` for every object rather than only the styling
props"*. This module is the spec-side half of that: `placement.py` already
solves DECLARED contacts for the styling block of TRN-001, and this checks
declared contacts for a lane whose masses are still authored as `c`/`s`.

`rule_gate.audit_spec` cannot see it either: it reads the `prov` TAG of each
mass, and the tags here are honest — the bed's x really was derived. R10's
question is *does this object deserve to exist*; this one is *does the
relationship this number came from still hold*.

THE CHECK, AND WHAT MAKES A ROW REAL
------------------------------------
A row in `spec["contacts"]` is a claim that two named faces meet:

    {"a": "bed_platform", "a_face": "x_max",
     "b": "bed_headboard", "b_face": "x_min",
     "gap_mm": 0.0, "datum": "b",
     "why": "the bed is pushed up to the panel; the panel is the datum"}

`datum` names which side does NOT move — the other one is derived from it. It is
required, and it is the whole point: a contact with no datum is two numbers that
happen to be equal, and the next edit will pick the wrong one to keep.

Every row is verified four ways, and each refusal is a defect this lane has
actually shipped:

  1. BOTH FACES ON ONE AXIS. `x_max` against `z_min` is not a contact; it is a
     typo that would pass a naive equality test on two coincidentally equal mm.
  2. THE FACES COINCIDE, to `TOL_MM`, at the declared `gap_mm`.
  3. THE MASSES DO NOT OVERLAP along that axis. Two faces can be equal while the
     masses interpenetrate by 300 mm — the equality is then an accident of the
     centre arithmetic, not a joint.
  4. THEY OVERLAP ON THE OTHER TWO AXES. Coplanar faces that never meet are a
     contact in name only — the same test `decisions_check` applies to a
     decision whose `where` names a path that does not exist: *a contact that
     touches nowhere was never made.*

WHAT IT CANNOT SEE, said before anyone trusts it
------------------------------------------------
  * It is SPEC-SIDE and blind to the built scene. A mesh generator that ignores
    `c`/`s` — a tilt, a cloth bake, an imported asset — can satisfy every row
    here and still put geometry somewhere else. `placement_dump` +
    `placement_check` remain the rung that reads what was actually built; this
    one refuses to let the two halves of a joint be authored from two
    independent numbers, which is the half an AABB cannot judge.
  * It checks the rows that EXIST. A contact nobody declared is not checked, and
    that is a real hole — so `undeclared()` reports, as an ADVISORY, every
    vertical butt joint the geometry already contains (48 of them in TRN-002
    r37) against the few that are declared. Advisory and not blocking, for the
    documented reason: 44 of those 48 are wall/millwork joints that no round has
    had a reason to reason about, and a gate that fails on all of them would be
    muted within one round.
  * It knows nothing about whether the contact is TRUE of the reference. It
    knows the spec is internally consistent about it. Whether the bed really
    touches the headboard is a measurement, and the measurement is in the round
    record — this only guarantees that when the panel's thickness moves again,
    the bed moves with it or the gate fails.
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                       # noqa: BLE001
    pass

# A joint in millwork is a contact, not a hover. Same figure and same reason as
# placement_check.CONTACT_TOL_MM: below what any camera in this studio resolves
# at room scale, above float noise from a metre-scale matrix multiply.
TOL_MM = 1.0

FACES = {
    "x_min": (0, -1), "x_max": (0, +1),
    "y_min": (1, -1), "y_max": (1, +1),
    "z_min": (2, -1), "z_max": (2, +1),
}
AXIS_NAME = "xyz"


def face_value(mass, face):
    """The mm coordinate of a named face of a `c`/`s` mass."""
    i, sgn = FACES[face]
    return float(mass["c"][i]) + sgn * float(mass["s"][i]) / 2.0


def extent(mass, i):
    """(lo, hi) of a mass along axis i, in mm."""
    c, s = float(mass["c"][i]), float(mass["s"][i]) / 2.0
    return (c - s, c + s)


def _overlap(a, b):
    return min(a[1], b[1]) - max(a[0], b[0])


def _by_name(spec):
    return {m["name"]: m for m in spec.get("masses", [])
            if m.get("name") and "c" in m and "s" in m}


def check(spec, tol_mm=TOL_MM):
    """[violation str] — every declared contact that does not hold in the spec."""
    by = _by_name(spec)
    rows = spec.get("contacts")
    if rows is None:
        return []
    if not isinstance(rows, list):
        return ["`contacts` is present but is not a list — a register that "
                "cannot be walked is not a register."]
    out = []
    seen = set()
    for n, row in enumerate(rows):
        tag = f"contacts[{n}]"
        if not isinstance(row, dict):
            out.append(f"{tag}: not an object.")
            continue
        a, b = row.get("a"), row.get("b")
        fa, fb = row.get("a_face"), row.get("b_face")
        tag = f"contacts[{n}] {a}.{fa} -> {b}.{fb}"
        if a == b:
            out.append(f"{tag}: a mass cannot be in contact with itself.")
            continue
        for name in (a, b):
            if name not in by:
                out.append(f"{tag}: `{name}` is not a mass with c/s in this "
                           f"spec, so this joint has nothing to be checked "
                           f"against.")
        if a not in by or b not in by:
            continue
        for f in (fa, fb):
            if f not in FACES:
                out.append(f"{tag}: `{f}` is not one of {sorted(FACES)}.")
        if fa not in FACES or fb not in FACES:
            continue
        if FACES[fa][0] != FACES[fb][0]:
            out.append(f"{tag}: the two faces are on different axes "
                       f"({AXIS_NAME[FACES[fa][0]]} and "
                       f"{AXIS_NAME[FACES[fb][0]]}) — that is not a joint.")
            continue
        key = (a, fa, b, fb)
        if key in seen:
            out.append(f"{tag}: declared twice.")
            continue
        seen.add(key)
        datum = row.get("datum")
        if datum not in ("a", "b"):
            out.append(f"{tag}: `datum` must be \"a\" or \"b\" — it names the "
                       f"side that does NOT move. Without it the next edit has "
                       f"no way to know which of two equal numbers to keep, "
                       f"which is the defect this register exists for.")
        if not str(row.get("why", "")).strip():
            out.append(f"{tag}: no `why`. A contact is a claim about the room, "
                       f"and an unexplained claim is the shape R10 refuses.")
        i = FACES[fa][0]
        gap = float(row.get("gap_mm", 0.0) or 0.0)
        if gap < 0:
            out.append(f"{tag}: `gap_mm` is {gap} — a negative gap is an "
                       f"overlap, and an overlap is not declared here.")
        va, vb = face_value(by[a], fa), face_value(by[b], fb)
        d = abs(va - vb)
        if abs(d - gap) > tol_mm:
            out.append(f"{tag}: the faces are {d:.3f} mm apart but the row "
                       f"declares {gap:.3f} mm ({d - gap:+.3f} mm). "
                       f"{a}.{fa}={va:.3f}, {b}.{fb}={vb:.3f}.")
        ea, eb = extent(by[a], i), extent(by[b], i)
        ov_axis = _overlap(ea, eb)
        if ov_axis > tol_mm:
            out.append(f"{tag}: the two masses overlap by {ov_axis:.1f} mm "
                       f"along {AXIS_NAME[i]}, so these faces being equal is "
                       f"arithmetic, not a joint.")
        for j in range(3):
            if j == i:
                continue
            o = _overlap(extent(by[a], j), extent(by[b], j))
            if o <= tol_mm:
                out.append(f"{tag}: the masses do not overlap along "
                           f"{AXIS_NAME[j]} ({o:.1f} mm), so the faces are "
                           f"coplanar and never meet. A contact that touches "
                           f"nowhere was never made.")
    return out


def butt_contacts(spec, tol_mm=TOL_MM):
    """[(a, b, axis)] — every VERTICAL butt joint the geometry already contains.

    Vertical (x/y) only, and deliberately: a z coincidence is 'everything stands
    on the floor', which is what `placement_check` already reads off the built
    scene and reports as supports. What that instrument cannot see is a joint in
    plan — which is the one that broke."""
    ms = [m for m in spec.get("masses", []) if m.get("name")
          and "c" in m and "s" in m]
    out = set()
    for p in range(len(ms)):
        for q in range(p + 1, len(ms)):
            a, b = ms[p], ms[q]
            for i in (0, 1):
                ea, eb = extent(a, i), extent(b, i)
                if _overlap(ea, eb) > tol_mm:
                    continue                    # they interpenetrate, not butt
                if min(abs(x - y) for x in ea for y in eb) > tol_mm:
                    continue
                if all(_overlap(extent(a, j), extent(b, j)) > tol_mm
                       for j in range(3) if j != i):
                    # NAME-SORTED, so the pair is the same tuple whichever way
                    # the spec happens to list its masses. A joint is symmetric;
                    # only a declared row has an `a` and a `b`.
                    n1, n2 = sorted((a["name"], b["name"]))
                    out.add((n1, n2, AXIS_NAME[i]))
    return sorted(out)


def undeclared_pairs(spec, tol_mm=TOL_MM):
    """[(a, b, axis)] — vertical butt joints in the geometry with no row."""
    have = set()
    for row in spec.get("contacts") or []:
        if isinstance(row, dict) and row.get("a") and row.get("b"):
            have.add(frozenset((row["a"], row["b"])))
    return [t for t in butt_contacts(spec, tol_mm)
            if frozenset((t[0], t[1])) not in have]


def undeclared(spec, tol_mm=TOL_MM):
    """[one line] — ADVISORY: how many joints the geometry has against how many
    are declared.

    ONE LINE, NOT FORTY-EIGHT, and the reason is the channel. This gate's output
    is printed into the render path because that is where the owner reads
    (`rule_gate.enforce`, and the decision log below it). Forty-eight
    wall-and-millwork joint names would bury the rows that need reading, and an
    advisory nobody finishes reading is the mute this repo keeps rediscovering.
    The names are one command away and the line says so — a cap that announces
    itself is not a silent cap."""
    found = butt_contacts(spec, tol_mm)
    if not found:
        return []
    missing = undeclared_pairs(spec, tol_mm)
    if not missing:
        return [f"all {len(found)} vertical butt joints in the geometry carry a "
                f"`contacts` row"]
    return [f"{len(missing)} of {len(found)} vertical butt joints in the "
            f"geometry carry no `contacts` row — mostly wall and millwork "
            f"joints no round has had a reason to reason about. Names: "
            f"`python pipeline/scripts/contact_check.py --spec <spec> --list`"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--tol", type=float, default=TOL_MM)
    ap.add_argument("--soft", action="store_true", help="report, do not exit 1")
    ap.add_argument("--list", action="store_true",
                    help="print every vertical butt joint the geometry has")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    rows = spec.get("contacts") or []
    v = check(spec, a.tol)
    if a.list:
        declared = {frozenset((r.get("a"), r.get("b")))
                    for r in rows if isinstance(r, dict)}
        for x, y, ax in butt_contacts(spec, a.tol):
            mark = "  " if frozenset((x, y)) in declared else "??"
            print(f" {mark} {x} | {y}  ({ax})")
    for s in undeclared(spec, a.tol):
        print(f"~~ {s}")
    if v:
        print(f"\nCONTACT CHECK: {len(v)} violation(s) of {len(rows)} declared")
        for s in v:
            print(f"  !! {s}")
    else:
        print(f"CONTACT CHECK: {len(rows)} declared contact(s), all holding")
    sys.exit(0 if a.soft else (1 if v else 0))


if __name__ == "__main__":
    main()
