#!/usr/bin/env python3
"""transform_check.py — DOES A MODIFIER WIDTH IN THIS SCENE STILL MEAN MILLIMETRES?
PURE (no bpy), reads a `scene-dump@2` written by `scene_dump.py`.

    python pipeline/scripts/transform_check.py <room_*.scene.json>

exit 0 = every mesh carrying a local-space modifier stands at scale 1
exit 1 = a mesh carries a local-space modifier AND a scale that is not 1 — its
         solidify / bevel / array widths are silently multiplied by that scale
exit 2 = COULD NOT RUN (dump unreadable, no meshes, or a dump written before the
         `scale` key existed). Never a pass.

WHY THIS EXISTS
---------------
Learned 2026-08-29 from `1i6woUR4iQA` (Vertex Arcade, "Make ANY FURNITURE in
Blender in 15 Minutes"), whose closing line names three things and the third is
APPLY THE TRANSFORMS. He says it at 02:38, repeats it at 08:56 while unwrapping,
and ends the video on it — because Solidify, Bevel, Mirror, Array, Screw and Skin
all evaluate their widths in the object's LOCAL space.

THE FAILURE IS INVISIBLE TO EVERY OTHER RUNG IN THIS REPO, and that is the whole
argument for a twelfth key in the dump. `dimensions` and `bound_box` report WORLD
size and stay correct under any scale, so an object at scale 2 renders an 18 mm
solidify as 36 mm while `placement_check`, `carry_check`, `dim_check` and the
p2_exit crops all read it as perfect. A wrong wall thickness that passes every
AABB test is exactly the shape this repo keeps paying for: a legal number that
encodes a result rather than a relationship (R9), measured by instruments that
were built to ask a different question (R7b).

IT IS GREEN TODAY, AND THAT IS THE REASON IT EXISTS RATHER THAN A REASON NOT TO.
Measured on room_bedroom_suite_eye_p2r90_ql.blend: 496 meshes, 0 at non-unit
scale, 244 BEVEL modifiers, 0 of them on a scaled object. The invariant holds —
by `_bake_transform_to_mesh` (build_room.py), a hand-rolled Ctrl+A wired at all
three glTF import sites. But that function's 45-line docstring argues its case
ENTIRELY IN TEXTURE SPACE (the 850 mm fabric tile that was landing at 7.1 mm) and
never once mentions a modifier. So 244 bevel widths mean millimetres today as a
SIDE EFFECT NOBODY WROTE DOWN, `bpy.ops.object.transform_apply` appears zero times
repo-wide, and until this rung there was nothing that could notice the day a
fourth importer, or a refactor of that bake, quietly stopped holding it up.

A rung that is allowed to be strict is one that costs nothing on the day it ships.
This one convicts zero objects in the scene of record, so it hard-fails with no
ledger and no third state. If a future round needs an exception it may add one
then, with a reason and a restart — the way `carry_check` does.

POSITIVE CONTROL, EVERY RUN (the P2-exit clause (2b) law: a rung whose PASS is "we
found nothing" must show its detector firing on the same kind of data in the same
run). `_positive_control()` builds two synthetic records — one clean, one a
bevelled box at scale 1.4 — and asserts this file's own predicate convicts the
second and clears the first. If the control does not fire, the run exits 2: a
detector that cannot be shown to detect has not looked.
"""
import json
import os
import sys

# The modifiers whose numbers are read in LOCAL space. Not an allowlist of
# OBJECTS (R9b: "a rule that names the objects it applies to will always exempt
# the next one") — it is the closed set of Blender modifier types whose width /
# offset / count arithmetic is scale-sensitive, so a new object class is covered
# the day it is built rather than the day someone remembers to add it.
LOCAL_SPACE_MODS = ("SOLIDIFY", "BEVEL", "MIRROR", "ARRAY", "SCREW", "SKIN",
                    "WIREFRAME")

# 1e-4 = 0.01%. `scene_dump` rounds scale to 6 dp, and a matrix decomposition of
# an identity-transformed object lands within ~1e-7, so this band is three orders
# clear of float noise and still catches any scale a human or an importer set.
TOL = 1e-4


def offends(rec):
    """(bool, worst_axis_scale) — does this record's scale corrupt its modifiers?

    A record with no `local_space_mods` cannot be corrupted by scale no matter
    how it stands, and a record with no modifiers listed but a wild scale is a
    LEGITIMATE state (a scaled reference plane, a scaled empty-shaped mesh): the
    defect is the PAIR, never the scale alone. Saying so here rather than in the
    caller is what keeps the positive control honest — it exercises the same
    predicate the render does."""
    mods = rec.get("local_space_mods") or []
    if not mods:
        return False, 1.0
    sc = rec.get("scale")
    if sc is None:
        return False, 1.0                    # handled by the CAN-I-RUN gate
    worst = max((float(v) for v in sc), key=lambda v: abs(v - 1.0))
    return abs(worst - 1.0) > TOL, worst


def _positive_control():
    """Fire the detector on data whose answer is known. Returns True if the
    detector both CONVICTS the planted defect and CLEARS the clean twin — one of
    those alone is not a control (a predicate that returns True for everything
    would pass the first half)."""
    planted = {"name": "_control_scaled_bevelled_box",
               "scale": [1.4, 1.4, 1.4], "local_space_mods": ["BEVEL"]}
    clean = {"name": "_control_clean_box",
             "scale": [1.0, 1.0, 1.0], "local_space_mods": ["BEVEL"]}
    unscaled_but_no_mods = {"name": "_control_scaled_plain_mesh",
                            "scale": [3.0, 1.0, 1.0], "local_space_mods": []}
    return (offends(planted)[0]
            and not offends(clean)[0]
            and not offends(unscaled_but_no_mods)[0])


def load(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    objs = doc.get("objects") if isinstance(doc, dict) else doc
    if not isinstance(objs, list):
        raise ValueError("no `objects` list in this dump")
    return objs


def main(argv):
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                   # noqa: BLE001
            pass
    if len(argv) != 1:
        print("usage: transform_check.py <room_*.scene.json>", file=sys.stderr)
        return 2
    path = argv[0]

    if not _positive_control():
        print("COULD NOT RUN: the positive control did not fire — this file's own "
              "predicate failed to convict a bevelled box planted at scale 1.4, so "
              "a clean report from it would mean nothing.", file=sys.stderr)
        return 2

    try:
        objs = load(path)
    except Exception as e:                                  # noqa: BLE001
        print(f"COULD NOT RUN: {os.path.basename(path)} — {e}", file=sys.stderr)
        return 2
    if not objs:
        print("COULD NOT RUN: this dump holds no mesh objects.", file=sys.stderr)
        return 2

    # CAN-I-RUN, and it is a separate question from "did I find anything". A dump
    # written before the `scale` key existed is not a scene with no scaled
    # objects; it is a scene nobody looked at. Absence of the key must never
    # print like absence of the defect.
    # A RECORD THAT CANNOT TESTIFY IS NOT A RECORD THAT PASSED. The first version of
    # this gate was ALL-OR-NOTHING (`if not with_scale`), so a dump where ONE mesh
    # carried a local-space modifier and no `scale` dropped that mesh from both the
    # numerator and the denominator and then printed "every mesh ... stands at scale 1"
    # — a claim about every mesh, made after silently excusing the only one it could
    # not read. `offends()` already says this case is "handled by the CAN-I-RUN gate";
    # this is what makes that true.
    unjudged = [o for o in objs
                if o.get("scale") is None and (o.get("local_space_mods") or [])]
    if unjudged:
        print(f"COULD NOT RUN: {len(unjudged)} mesh(es) carry a local-space modifier "
              f"and no `scale` — they cannot be judged and must not be excused: "
              f"{', '.join(o.get('name', '?') for o in unjudged[:6])}"
              f"{' …' if len(unjudged) > 6 else ''}", file=sys.stderr)
        return 2
    with_scale = [o for o in objs if o.get("scale") is not None]
    if not with_scale:
        print(f"COULD NOT RUN: no record in {os.path.basename(path)} carries a "
              f"`scale` — this dump predates the key. Re-run the build; a dump "
              f"that cannot testify about scale is not a scene without scale.",
              file=sys.stderr)
        return 2

    carriers = [o for o in with_scale if (o.get("local_space_mods") or [])]
    bad = []
    for o in carriers:
        hit, worst = offends(o)
        if hit:
            bad.append((o["name"], worst, o.get("local_space_mods")))

    print(f"positive control FIRED (planted bevelled box at scale 1.4 convicted, "
          f"clean twin cleared)")
    print(f"{len(objs)} meshes · {len(with_scale)} carry a scale · "
          f"{len(carriers)} carry a local-space modifier "
          f"({', '.join(LOCAL_SPACE_MODS)})")

    if not bad:
        print("every mesh whose modifiers are read in local space stands at "
              "scale 1 — solidify/bevel/array widths in this scene mean millimetres")
        return 0

    print(f"!! {len(bad)} mesh(es) carry a local-space modifier AND a non-unit "
          f"scale. Their modifier widths are multiplied by that scale, and every "
          f"AABB-reading rung in this repo reads them as correct:")
    for nm, worst, mods in sorted(bad, key=lambda t: -abs(t[1] - 1.0))[:40]:
        print(f"   {nm[:56]:56s} scale {worst:.4f}  {'+'.join(mods)}")
    if len(bad) > 40:
        print(f"   … and {len(bad) - 40} more")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
