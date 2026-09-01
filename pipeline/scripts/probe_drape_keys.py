"""MUTATION PROBE for drape.py's keyframe-shape guards (Blender-side).

Same law as `mutation_probe.py`: a green check proves nothing until you have
watched it go RED. That file drives pytest against one plan reader; these three
guards live inside a Blender bake, so they need their own probe.

WHAT IT GUARDS, AND WHY THE CHECK IT REPLACED COULD NOT. `drape.py` keyframes
three things -- the cloth's effector gravity ramp, each tuck HAND's travel, and
the dent presser's press. The check that stood there asserted `keyframe_insert`'s
RETURN VALUE, which is True in exactly the case that goes wrong: the call
succeeds and lands the key BEZIER, so a two-key 0 -> 1 ramp eases in AND out
instead of travelling at a constant rate. Measured 2026-08-31 on the shipping
duvet, that shape is worth RMS 7.014 mm / max 30.10 mm on the SETTLED result,
against a null control (the same module run twice) of 0.000000 mm. `_assert_keys`
now reads the built curve back and holds it to `RAMP_INTERP`; this probe is what
proves it can actually fail.

ONE DELIBERATE DIFFERENCE FROM `mutation_probe.py`: the mutation is never written
to disk. Each mutant is the real `drape.py` source with one line injected,
compiled into a throwaway module in memory -- so there is no backup file, no
restore step, and nothing a killed process can leave behind in the tree.

PREFLIGHT IS NOT OPTIONAL (mutation_probe.py's own second rule): the unmutated
bake must PASS first. A broken Blender or a bad harness would otherwise raise on
every leg and read as 3/3 RED -- the flattering-scorer shape wearing the probe's
own uniform.

Run:  blender -b --factory-startup --python pipeline/scripts/probe_drape_keys.py
Exit 0 only when preflight is GREEN and all three mutants go RED.
"""
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy   # noqa: E402

SRC = open(os.path.join(HERE, "drape.py"), encoding="utf-8").read()

# Each mutant forces LINEAR onto the curve the guard beside it is meant to hold
# to RAMP_INTERP. The anchor must match EXACTLY once or the probe aborts rather
# than mutate something it could not locate.
MUTANTS = [
    ("gravity ramp", "sheet",
     '                             f"({_ok1}/{_ok2}) \u2014 do not bake as if ramped")',
     '\n'
     '        _fc0 = obj.animation_data.action.fcurve_ensure_for_datablock(\n'
     '            obj, \'modifiers["drape"].settings.effector_weights.gravity\',\n'
     '            index=0)\n'
     '        for _kp in _fc0.keyframe_points:\n'
     '            _kp.interpolation = "LINEAR"'),

    ("tuck hand", "sheet",
     '            _em.keyframe_insert("location", frame=int(_tend))',
     '\n'
     '            _fc0 = _em.animation_data.action.fcurve_ensure_for_datablock(\n'
     '                _em, "location", index=0)\n'
     '            for _kp in _fc0.keyframe_points:\n'
     '                _kp.interpolation = "LINEAR"'),

    ("dent presser", "dent",
     '    presser.keyframe_insert("location", frame=int(press_frame))',
     '\n'
     '    _fc0 = presser.animation_data.action.fcurve_ensure_for_datablock(\n'
     '        presser, "location", index=0)\n'
     '    for _kp in _fc0.keyframe_points:\n'
     '        _kp.interpolation = "LINEAR"'),
]


def _mutant(tag, anchor, patch):
    """drape.py with `patch` injected after `anchor`, as an in-memory module."""
    if SRC.count(anchor) != 1:
        raise SystemExit(f"probe_drape_keys: anchor for {tag} matched "
                         f"{SRC.count(anchor)} times, expected exactly 1 -- "
                         f"refusing to mutate what it cannot locate")
    mod = types.ModuleType(tag)
    mod.__file__ = os.path.join(HERE, tag + ".py")
    sys.modules[tag] = mod
    exec(compile(SRC.replace(anchor, anchor + patch, 1), mod.__file__, "exec"),
         mod.__dict__)
    return mod


def _fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _sheet(nx=10, ny=10, w=1.0, d=1.0, z=0.6):
    verts, faces = [], []
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            verts.append((-w / 2 + w * ix / nx, -d / 2 + d * iy / ny, z))
    for iy in range(ny):
        for ix in range(nx):
            a = iy * (nx + 1) + ix
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return verts, faces


def _box(loc, sc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.scale = sc
    bpy.context.view_layer.update()
    return ob


def _bake_sheet_with(mod, name):
    """A tucked bake -- the ONLY configuration in which the ramp ever fires
    (build_room.py gates it on `_tucks`), so an untucked probe would exercise a
    path the lane never ships."""
    _fresh()
    verts, faces = _sheet()
    mat = _box((0, 0, 0.2), (0.8, 0.8, 0.2))
    tucks = [([i for i, p in enumerate(verts) if abs(p[1]) <= 0.12],
              (0.006, 0.0, -0.006), 40)]
    mod.bake_sheet(name, verts, faces, [mat], frames=45, fabric="linen",
                   gravity_ramp=40, tucks=tucks, min_motion=0.0)


def _dent_with(mod):
    """The presser must START in contact. Target top sits at z=0.33 (centre 0.30,
    half-height 0.03); the presser's half-height is 0.025, so its centre goes at
    0.355 and it travels 10 mm down into the seat -- the same 10 mm press the
    docstring's own probe measured a 5 mm dent under. A presser parked above the
    seat presses on nothing, and `dent_soft_body` says so rather than returning
    zero, which is how the first version of this harness got caught."""
    _fresh()
    tgt = _box((0, 0, 0.30), (0.6, 0.6, 0.06))
    prs = _box((0, 0, 0.355), (0.15, 0.15, 0.05))
    mod.dent_soft_body(tgt, prs, 0.010)


def main():
    import drape

    try:
        _bake_sheet_with(drape, "preflight")
        _dent_with(drape)
    except Exception as exc:
        print(f"PREFLIGHT FAILED on unmutated drape.py: {exc}")
        print("Every mutant below would go RED for that reason and not for the "
              "guard. Fix the environment before reading any result.")
        return 2
    print("PREFLIGHT GREEN -- unmutated bake and dent both pass")

    red = 0
    for label, kind, anchor, patch in MUTANTS:
        mod = _mutant("drape_mut_" + label.replace(" ", "_"), anchor, patch)
        try:
            _bake_sheet_with(mod, "mutant") if kind == "sheet" else _dent_with(mod)
        except mod.DrapeError as exc:
            red += 1
            print(f"  RED   {label}: {str(exc)[:88]}")
            continue
        except Exception as exc:
            print(f"  ERROR {label}: raised {type(exc).__name__}, not DrapeError"
                  f" -- the guard is not what stopped it: {exc}")
            continue
        print(f"  GREEN {label}: the guard did NOT fire on a LINEAR curve -- it "
              f"cannot fail for the property it names")

    print(f"{red}/{len(MUTANTS)} keyframe-shape guards are proven able to go red.")
    return 0 if red == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
