"""Prove that normalising an imported object's `rotation_mode` does not move it.

    blender -b --factory-startup --python pipeline/scripts/probe_import_rotation.py

WHY THIS PROBE EXISTS. `mesh_import.import_file` converts every imported object to
'XYZ' rotation mode, because `bpy.ops.import_scene.gltf` leaves them at
'QUATERNION' -- and on a QUATERNION object `rotation_euler` is a DEAD ATTRIBUTE:
it reads (0, 0, 0) however the object is really turned, and writing it stores the
number and moves nothing. Both halves were live in this repo. `placement_dump`
read it for R9's OFF-AXIS rung, so every acquired asset reported zero tilt; and
`trn001_styling` wrote an asset's plan yaw into it, so the log printed a placed,
scaled asset that had never been turned.

The conversion is only safe if assigning the mode CONVERTS the existing rotation
rather than discarding it. Getting that wrong would silently re-orient every
acquired asset in the repo, which is a worse defect than the one being fixed --
so it is measured here rather than assumed, with a repo-built POSITIVE CONTROL in
the same scene so a probe that measures nothing cannot read as a probe that
measured zero.

Exit 0 only when the imported object does not move, its euler then reads the
angles it was exported with, and a subsequent `rotation_euler` write reaches the
matrix.
"""
import math
import os
import sys
import tempfile

import bpy   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ANGLES = (20.0, -13.0, 35.0)      # deg; deliberately all three axes, mixed signs
TOL_M = 1e-6                      # float32 epsilon is ~6e-8; anything larger moved


def _mat_delta(a, b):
    return max(abs(x - y) for r1, r2 in zip(a, b) for x, y in zip(r1, r2))


def main():
    tmp = tempfile.mkdtemp(prefix="probe_import_rotation_")
    path = os.path.join(tmp, "rot.gltf")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add()
    src = bpy.context.object
    src.rotation_euler = tuple(math.radians(a) for a in ANGLES)
    src.scale = (1.3, 0.7, 1.1)          # non-uniform: a scale/rotation mix-up shows
    src.location = (0.4, -0.9, 2.2)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    # POSITIVE CONTROL: a repo-built object, which is already XYZ and must stay put.
    bpy.ops.mesh.primitive_cube_add(location=(4, 0, 0))
    ctl = bpy.context.object
    ctl.name = "control"
    ctl.rotation_euler = (math.radians(20), 0, 0)
    # `matrix_world` is STALE until the depsgraph is evaluated. Without this line
    # the control captured an unrotated matrix and then "drifted" by sin(20 deg)
    # = 0.342 m through no fault of the code under test -- and the probe still
    # printed PROBE OK, because the control was printed and never asserted on.
    # A control that cannot fail the run is not a control.
    bpy.context.view_layer.update()
    ctl_before = ctl.matrix_world.copy()

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    imported = [o for o in bpy.data.objects if o not in before]
    if not imported:
        print("PROBE FAILED: nothing was imported -- the probe measured nothing")
        return 2
    modes = {o.name: o.rotation_mode for o in imported}
    print(f"imported {len(imported)} object(s), modes: {modes}")
    if all(m == "XYZ" for m in modes.values()):
        print("PROBE INCONCLUSIVE: the importer already returned XYZ, so this run "
              "cannot show that the conversion preserves anything")
        return 2

    truth = {o.name: o.matrix_world.copy() for o in imported}
    worst = 0.0
    for o in imported:
        o.rotation_mode = "XYZ"
        bpy.context.view_layer.update()
        worst = max(worst, _mat_delta(o.matrix_world, truth[o.name]))
    deg = [round(math.degrees(a), 3) for a in imported[0].rotation_euler]
    print(f"worst matrix_world drift over the conversion: {worst:.3e} m")
    print(f"euler after conversion: {deg}  (exported at {list(ANGLES)})")

    bpy.context.view_layer.update()
    ctl_drift = _mat_delta(ctl.matrix_world, ctl_before)
    print(f"positive control (repo-built, already XYZ) drift: {ctl_drift:.3e} m")

    # the write that used to do nothing
    imported[0].rotation_euler.z = math.radians(90.0)
    bpy.context.view_layer.update()
    got_z = math.degrees(imported[0].matrix_world.to_euler().z)
    print(f"after writing rotation_euler.z = 90 deg, matrix reads z = {got_z:.2f} deg")

    ok = True
    if ctl_drift > TOL_M:
        print(f"FAIL: the CONTROL moved ({ctl_drift:.3e} m). It is repo-built and "
              f"already XYZ, so nothing here should touch it — this run measures "
              f"the harness, not the conversion, and its other numbers mean nothing")
        ok = False
    if worst > TOL_M:
        print(f"FAIL: the object MOVED ({worst:.3e} > {TOL_M:.0e}) -- assigning the "
              f"mode discards the rotation, and the conversion is unsafe")
        ok = False
    if max(abs(g - a) for g, a in zip(deg, ANGLES)) > 1e-3:
        print(f"FAIL: euler reads {deg}, expected {list(ANGLES)}")
        ok = False
    if abs(got_z - 90.0) > 1e-3:
        print(f"FAIL: the rotation_euler write did not reach the matrix "
              f"({got_z:.2f} deg) -- the dead attribute is still dead")
        ok = False
    print("PROBE OK: conversion preserves the rotation and revives the channel"
          if ok else "PROBE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
