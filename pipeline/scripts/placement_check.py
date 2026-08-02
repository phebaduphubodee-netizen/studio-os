#!/usr/bin/env python3
"""placement_check.py — is every object in a BUILT scene actually standing on
something, inside it, and straight? PURE: no bpy, runs under plain python.

    blender -b <scene>.blend --python pipeline/scripts/placement_dump.py -- p.json
    python pipeline/scripts/placement_check.py p.json

WHY THIS EXISTS — the owner, 2026-08-02, across every project: *"คุณชอบวาง model
เบี้ยว ลอย ไม่ตรงแกน ไม่สมจริง"*. He is right, and the measurement found a mechanism
rather than carelessness (CLAUDE.md R9, docs/placement-audit-2026-08-02.md):

  * positions are stored as ABSOLUTE coordinates. A coordinate encodes a RESULT,
    never a RELATIONSHIP — so when the thing underneath is resized, the stored
    number stays perfectly legal and the contact silently breaks. Nothing fails,
    because a coordinate is always a legal coordinate.
  * the guards that did exist were written per-instance, after each burn, and
    allowlisted by class name: two of them covered `vase` and `candlestick` out of
    five classes actually placed, so 8 of 13 objects — including every figure —
    were exempt. Four consecutive rounds of figure-placement defects followed.

**SO THIS CHECK CARRIES NO ALLOWLIST.** Scope is geometric, not by name: every
mesh object that renders. A rule that names the objects it applies to will always
exempt the next one.

WHAT IT CAN AND CANNOT SEE — stated up front, because a metric that cannot separate
two things it is trusted to separate is a defect this repo has recorded more than
once (a bounding box could not tell a vase from a flat plank).

  AABBs are what a scene can be asked for cheaply, and they are SOUND for:
    - does this touch anything at all           (FLOATING)
    - does its footprint sit inside its support (OVERHANG)
    - is it tipped                              (OFF-AXIS)
  They are NOT geometry. Two objects whose boxes overlap may interlock legally
  (a lid on a pot, a leg through a rail). So INTERPENETRATION is reported as
  ADVISORY and never fails the run. Promoting it would train the reader to mute
  the whole instrument, which is how the previous debt instrument died.
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                       # noqa: BLE001
    pass

# --- tolerances, in mm, and each one is a claim about the real world -----------
# A join in millwork is a contact, not a hover. 1 mm is below what any camera in
# this studio resolves at room scale, and above float noise from a metre-scale
# matrix multiply.
CONTACT_TOL_MM = 1.0
# How far a footprint may hang past its support before it reads as unbuilt. The
# owner's own correction that started this: a base was letting what stood on it
# overhang by 69 mm, "which no piece of millwork does".
OVERHANG_TOL_MM = 2.0
# Tipping. Anything a builder MEANT to tilt declares it; this catches the
# accidental fraction of a degree that comes from a bad matrix.
AXIS_TOL_DEG = 0.05
# Advisory only: how deeply boxes must overlap on every axis before it is worth
# a human looking. Below this, two adjacent parts simply share a face.
DEEP_OVERLAP_MM = 5.0


def _mesh(objs):
    return [o for o in objs
            if o.get("type") == "MESH" and not o.get("hidden_render")
            and "min" in o and "max" in o]


def ground_z(objs):
    """The scene's floor: the lowest point any rendered mesh reaches. Derived, not
    assumed to be 0 — a scene may be built on a slab, or below datum."""
    ms = _mesh(objs)
    return min(o["min"][2] for o in ms) if ms else 0.0


def _plan_overlap(a, b):
    """(dx, dy) overlap of two AABB footprints. Negative = separated."""
    return (min(a["max"][0], b["max"][0]) - max(a["min"][0], b["min"][0]),
            min(a["max"][1], b["max"][1]) - max(a["min"][1], b["min"][1]))


def touches(a, b, tol=CONTACT_TOL_MM):
    """Do two AABBs touch or overlap on every axis, within tol? This is the honest
    form of 'is it held up by anything' — it does not care WHICH face."""
    for i in range(3):
        if min(a["max"][i], b["max"][i]) - max(a["min"][i], b["min"][i]) < -tol:
            return False
    return True


def supports_of(ob, objs, tol=CONTACT_TOL_MM):
    """Objects whose TOP meets this object's BOTTOM, with plan overlap. A support
    is a face you stand on — not merely a neighbour."""
    out = []
    for o in objs:
        if o is ob:
            continue
        if abs(o["max"][2] - ob["min"][2]) > tol:
            continue
        dx, dy = _plan_overlap(ob, o)
        if dx > tol and dy > tol:
            out.append(o)
    return out


def root_of(name, parent):
    """The top of an object's parent chain. A parented group is ONE placed thing:
    Blender's hierarchy is the scene's own declaration of what moves together, so
    it is used instead of a name convention. Cycle-safe."""
    seen = set()
    while parent.get(name) and parent[name] not in seen:
        seen.add(name)
        name = parent[name]
    return name


def group(objs):
    """{root name: [member objects]} over the rendered meshes. An unparented
    object is its own group, which is correct for our built millwork — each mass
    is placed individually — and for an acquired asset the import hierarchy binds
    its parts into the single object a human would point at."""
    parent = {o["name"]: o.get("parent") for o in objs}
    out = {}
    for o in _mesh(objs):
        out.setdefault(root_of(o["name"], parent), []).append(o)
    return out


def bbox_of(members):
    return {"min": [min(m["min"][i] for m in members) for i in range(3)],
            "max": [max(m["max"][i] for m in members) for i in range(3)]}


def is_freestanding(box, others, sup, tol=CONTACT_TOL_MM):
    """Is this thing held up by what it stands on ALONE?

    TWO CORRECTIONS, BOTH EARNED BY RUNNING IT.

    (1) The first version asked "is the footprint inside its support" of every
    object and convicted 27 pieces of correct construction and zero props — a
    ceiling meeting a downlight trim, a header spanning two towers, and most
    instructively a plinth overhanging its own toe-kick, which is what a toe-kick
    IS. A BUILT element is held by more than the thing under it: a wall behind, a
    neighbour beside, a second support at the far end. Only a freestanding thing
    must sit inside its support, because nothing else is holding it up.

    (2) Then it still missed the very defect it was written for. A figure is
    several meshes that touch each other, so no part of it was ever
    "freestanding" and the whole class stayed exempt — the guard would have
    passed round 16. Fixed by grouping (see `group`) and by counting only LATERAL
    contact: something RESTING ON this object does not hold it up, and something
    it stands on is its support. Only a neighbour at the same height means it is
    braced by something other than its base.

    Written down because the shape recurs: a rule whose scope is chosen to
    silence false positives will silence the true one too, unless the scope is
    derived from the rule's own premise."""
    for o in others:
        if not touches(box, o, tol):
            continue
        if o["name"] in sup:
            continue
        # purely vertical contact (it sits on us, or we sit on it) is not bracing
        z_over = min(box["max"][2], o["max"][2]) - max(box["min"][2], o["min"][2])
        if z_over <= tol:
            continue
        # (3) NOR ARE ITS CONTENTS. The vase escaped the check because the flowers
        # standing IN it are a lateral contact — and a thing wholly inside your own
        # footprint cannot be holding you up. Bracing requires the neighbour to
        # reach OUTSIDE you: that is what a wall behind a plinth does and what a
        # stem in a vase does not.
        inside = (o["min"][0] >= box["min"][0] - tol and o["max"][0] <= box["max"][0] + tol
                  and o["min"][1] >= box["min"][1] - tol and o["max"][1] <= box["max"][1] + tol)
        if inside:
            continue
        return False
    return True


def check(objs, contact_tol=CONTACT_TOL_MM, overhang_tol=OVERHANG_TOL_MM,
          axis_tol=AXIS_TOL_DEG, deep=DEEP_OVERLAP_MM):
    """Findings for one dumped scene. Pure — takes the parsed dump, returns a list.

    Severity is a promise about the evidence, not about how bad it looks:
      FAIL     the AABB is sufficient to prove it (floating, overhang, off-axis)
      ADVISORY the AABB only SUGGESTS it and geometry could exonerate it
    """
    ms = _mesh(objs)
    gz = ground_z(objs)
    groups = group(objs)
    out = []

    # OFF-AXIS is per OBJECT: a tipped part inside an otherwise level assembly is
    # still a tipped part, and grouping would hide it.
    for ob in ms:
        rx, ry = (ob.get("rot_deg") or [0, 0, 0])[:2]
        if max(abs(rx), abs(ry)) > axis_tol:
            out.append({"sev": "FAIL", "kind": "OFF-AXIS", "object": ob["name"],
                        "detail": f"tipped rx={rx:.3f}deg ry={ry:.3f}deg — a tilt "
                                  f"nobody declared is a matrix error, not a design"})

    # FLOATING and OVERHANG are per GROUP: the thing a human would point at.
    for root, members in groups.items():
        box = bbox_of(members)
        box["name"] = root
        mine = {m["name"] for m in members}
        others = [o for o in ms if o["name"] not in mine]
        bottom = box["min"][2]
        on_ground = abs(bottom - gz) <= contact_tol
        sup = [o for o in others
               if abs(o["max"][2] - box["min"][2]) <= contact_tol
               and min(box["max"][0], o["max"][0]) - max(box["min"][0], o["min"][0]) > contact_tol
               and min(box["max"][1], o["max"][1]) - max(box["min"][1], o["min"][1]) > contact_tol]
        label = root if len(members) == 1 else f"{root} (+{len(members) - 1} parts)"

        # --- FLOATING: held up by nothing at all.
        if not on_ground and not sup:
            if not any(touches(box, o, contact_tol) for o in others):
                gap = min((box["min"][2] - o["max"][2] for o in others
                           if o["max"][2] <= box["min"][2]), default=bottom - gz)
                out.append({"sev": "FAIL", "kind": "FLOATING", "object": label,
                            "detail": f"bottom at z={bottom:.1f}mm touches nothing; "
                                      f"nearest surface below is {gap:.1f}mm away"})
            # else: touching something but not STANDING on it — wall-mounted,
            # hung, let into a reveal. Legitimate, not this check's business.
            continue

        # --- OVERHANG: a FREESTANDING thing on ONE support that hangs off it.
        #
        # WHY len(sup) == 1, AND IT IS THE RULE'S OWN PREMISE. "Its footprint must
        # sit inside its support" is only true when ONE thing holds it up. The
        # third false positive this check produced was the ceiling: it rests on
        # ten wall pieces at 2805.0 mm, no single one of which contains a
        # 6.0 x 4.5 m slab, so picking the "most generous" support convicted a
        # correctly built ceiling of hanging 3011 mm past a downlight trim. An
        # element carried by SEVERAL supports is SPANNING, and containment is the
        # wrong question to ask of it.
        #
        # DECLARED BLIND SPOT, not a silent one: a spanning element that really is
        # unsupported at one end will not be caught here. That needs coverage of
        # the footprint by the UNION of supports, which an AABB cannot express.
        if len(sup) == 1 and is_freestanding(box, others, {sup[0]["name"]}, contact_tol):
            s = sup[0]
            over = max(s["min"][0] - box["min"][0], box["max"][0] - s["max"][0],
                       s["min"][1] - box["min"][1], box["max"][1] - s["max"][1])
            if over > overhang_tol:
                out.append({"sev": "FAIL", "kind": "OVERHANG", "object": label,
                            "detail": f"hangs {over:.1f}mm past `{s['name']}`, the "
                                      f"only thing holding it up"})

    # --- INTERPENETRATION, advisory. See the module docstring on why.
    for i, a in enumerate(ms):
        for b in ms[i + 1:]:
            ov = [min(a["max"][k], b["max"][k]) - max(a["min"][k], b["min"][k])
                  for k in range(3)]
            if all(v > deep for v in ov):
                out.append({"sev": "ADVISORY", "kind": "INTERPENETRATION",
                            "object": a["name"],
                            "detail": f"boxes overlap `{b['name']}` by "
                                      f"{ov[0]:.0f}x{ov[1]:.0f}x{ov[2]:.0f}mm — "
                                      f"an AABB cannot tell interlocking from "
                                      f"intersecting; LOOK before believing it"})
    return out


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dump", help="JSON written by placement_dump.py")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--advisory", action="store_true",
                    help="also print the ADVISORY interpenetration list")
    a = ap.parse_args(argv)

    d = load(a.dump)
    objs = d.get("objects", d if isinstance(d, list) else [])
    found = check(objs)
    fails = [f for f in found if f["sev"] == "FAIL"]
    adv = [f for f in found if f["sev"] == "ADVISORY"]

    if a.json:
        print(json.dumps({"fails": fails, "advisory": adv}, indent=1,
                         ensure_ascii=False))
        return 1 if fails else 0

    n = len(_mesh(objs))
    print(f"placement check: {n} rendered mesh objects, ground z="
          f"{ground_z(objs):.1f}mm  [{os.path.basename(a.dump)}]")
    for f in fails:
        print(f"  !! {f['kind']:<9} {f['object']}\n     {f['detail']}")
    if a.advisory or not fails:
        for f in adv:
            print(f"  ~  {f['kind']:<9} {f['object']}\n     {f['detail']}")
    if not fails:
        print(f"  -> OK: everything stands on something, inside it, and straight "
              f"({len(adv)} advisory overlap(s) not shown as failures)")
        return 0
    print(f"  -> {len(fails)} FAIL, {len(adv)} advisory. A position that can be "
          f"DERIVED from a contact must never be TYPED (CLAUDE.md R9).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
