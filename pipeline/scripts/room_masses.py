#!/usr/bin/env python3
"""room_masses.py — adapt a ROOM spec (items/builtins) to rule_gate's mass grammar. PURE stdlib.

WHY THIS EXISTS (D-021, 2026-08-10)
------------------------------------
`rule_gate` is imported by trn002_build.py and nothing else. The render path that
produces the DELIVERABLE frame — build_room.py — calls no gate at all, so a
DELIV-001 frame renders past every rule this repo has written, and P1 would then
score it with a standard nothing enforced.

Wiring it is not a one-line change, and the measurement is why. Run against
master-suite.CANONICAL.spec.json, rule_gate.check returns two violations and BOTH
say "I cannot see this spec": `spec carries no masses at all`, and no coverage
manifest. TRN-002 specs carry `masses`; room specs carry `items` + `builtins`.
Different schema, same question.

WHAT THIS TRANSLATES, AND WHAT IT REFUSES TO INVENT
----------------------------------------------------
The room spec is NOT un-provenanced — that was the surprise. All eleven objects
in the canonical spec carry their authority in `note`, in the CAD vocabulary
rather than TRN-002's M/D/A letters: seven cite ink coordinates from the drawing
("INK x2654.5-3152.8 y625.8-1625.6"), three cite an owner signature with a date,
and the builtins carry a structured `bf` field naming their element in the DD/CD
set.

So this module TRANSLATES a source that is already recorded. It never
manufactures one. The ladder, most authoritative first:

    ink coordinates in the note   -> M(ink: ...)      measured off the drawing
    an elementN-*.json is named   -> M(<file>)        measured, in a read of record
    a `bf` element id             -> D(<BF>)          derived from the DD set
    an owner signature + date     -> A(...) + `why`   owner says it EXISTS; the
                                                      dimensions are not sourced,
                                                      so it is a DECLARED
                                                      assumption, which is what
                                                      R10 asks for
    none of the above             -> NO PROV          and R10 fires, correctly

That last line is the whole point. An object whose note says only where it sits
and what it is next to has not said where its numbers came from, and R10's
corollary is that an object invented to satisfy a structure is a declared
assumption rather than a measurement.

SCOPE, derived from the rule's premise rather than chosen to avoid noise (R9b):
this adapts OBJECTS — the things R10 asks to justify their own existence. The
room shell (outline, wall thickness, ceiling) is architecture read from the DXF,
not a discretionary object, and it is not adapted here. `require_seen` stays OFF
for this lane: R10 question 2 is "point at it in the REFERENCE", and DELIV-001 is
the owner's own client bedroom — there is no reference image and there never will
be one. The authority that replaces it is the source-of-truth order the repo
already carries (Thai code dir > client contract > studio standards) and the DXF
re-derivation's ruling that dims are authoritative.
"""
import os
import re

# ink evidence: an explicit INK marker, or an ink read/true/match verb
INK = re.compile(r"\bINK[- ]?(?:TRUED?|READ|MATCHED?)\b|\bINK\b|\bink[- ]?(?:read|true)", re.I)
INK_COORDS = re.compile(r"INK\s+x[\d.]+", re.I)
ELEMENT_FILE = re.compile(r"\b(element\d[\w.-]*\.json)\b", re.I)
OWNER_SIGN = re.compile(r"owner[- ]?(?:sign\w*|confirm\w*)|OWNER-CONFIRMED", re.I)
OWNER_DATE = re.compile(r"owner[^.;()]{0,24}?(\d{2}-\d{2}(?:-\d{2,4})?|\d{4}-\d{2}-\d{2})", re.I)


def prov_from(obj):
    """The recorded source for THIS object's numbers, in rule_gate's grammar.

    Returns (prov, why) — prov is None when the object's own record names no
    source, which is a violation and must stay one.
    """
    note = obj.get("note") or ""
    bf = obj.get("bf")

    m = INK_COORDS.search(note)
    if m:
        tail = note[m.start():m.start() + 90].replace("\n", " ").strip()
        return f"M(ink: {tail})", None
    if INK.search(note):
        return f"M(ink read of record: {note[:70].strip()})", None

    m = ELEMENT_FILE.search(note)
    if m:
        return f"M({m.group(1)})", None

    if bf:
        return (f"D({bf} from the DD/CD set — the element id carries this "
                f"object's dimensions)", None)

    m = OWNER_DATE.search(note)
    if m:
        # The owner said it exists. Nothing here says where w/d/h came from, so
        # this is an ASSUMPTION with a stated reason — exactly R10's declared
        # assumption, not a measurement dressed as one.
        return (f"A(owner decision {m.group(1)}; dimensions not sourced in the "
                f"spec)", note[:160].strip())
    if OWNER_SIGN.search(note):
        return (f"A(owner-signed, undated in the spec; dimensions not sourced)",
                note[:160].strip())
    return None, None


def _mass(obj, group):
    w = obj.get("w")
    d = obj.get("d")
    h = obj.get("h")
    x = obj.get("x")
    y = obj.get("y")
    prov, why = prov_from(obj)
    m = {"name": obj.get("name") or "<unnamed>",
         "kind": obj.get("kind") or group,
         "_group": group}
    if None not in (x, y, w, d):
        m["c"] = [x, y, (h or 0) / 2.0]
        m["s"] = [w, d, h or 0]
    if prov:
        m["prov"] = prov
    if why:
        m["why"] = why
    return m


def masses(spec):
    """Every OBJECT the room spec declares, as rule_gate masses. Order is stable."""
    out = []
    for group in ("builtins", "items"):
        for obj in spec.get(group) or []:
            if isinstance(obj, dict):
                out.append(_mass(obj, group))
    return out


def is_room_spec(spec):
    """True when this spec declares objects in the room grammar.

    A spec with neither key is not a room spec and this adapter says so rather
    than adapting it to an empty list — an empty mass list would read to the gate
    as a spec with nothing in it, which is a mute wearing the shape of a pass.
    """
    return isinstance(spec, dict) and bool(spec.get("items") or spec.get("builtins"))


def as_gate_spec(spec, spec_path=None):
    """The room spec re-expressed in the grammar rule_gate.audit_spec reads."""
    out = {"id": os.path.basename(str(spec_path)) if spec_path else
           (spec.get("schema") or "room-spec"),
           "masses": masses(spec)}
    gaps = spec.get("declared_gaps")
    if isinstance(gaps, dict):
        out["declared_gaps"] = gaps
    return out
