#!/usr/bin/env python3
"""make_plan.py — the plan view this lane never drew, on both islands.

    python training/TRN-003_3dshaker-kitchen/03_blockout/make_plan.py

Writes two plans from the SAME numbers the build consumes:

    PLAN_as-built-WRONG.png   the island as it was actually built, a quarter turn out
    PLAN_corrected.png        the island as the drums measure it

and runs the two new rungs over both, so the file is a NEGATIVE CONTROL and not a
demonstration. A guard written the day after an incident has to be pointed at the
state that produced the incident, or all it proves is that it agrees with today's
numbers (D-056).

The wrong island's geometry is not invented for this file. `derive_island.py` — the
first, wrong correction — printed a walkway of **-420 mm** for a slab lying across
the room. Negative 420 mm is not a tight kitchen; it is the counter run and the
island occupying the same 420 mm of floor. Nothing in the lane said a word.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "pipeline", "scripts"))

import room_spec as RS                      # noqa: E402
import planview                             # noqa: E402
import clearance_check as cc                # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Camera in the world frame of room_spec: x = distance off the kitchen wall,
# y = along it. Heading from the solved euler — Blender's XYZ euler with rot_x=90
# leaves the camera looking along +Y, so forward = (-sin g, cos g) with g = 149.15.
G = math.radians(149.15)
CAM = dict(x=RS.CAM_TO_KITCHEN_WALL, y=RS.CAM_Y,
           heading_deg=math.degrees(math.atan2(math.cos(G), -math.sin(G))) % 360.0,
           fov_deg=19.29)

# Masses that matter in plan. The wall/ceiling slabs are dropped: they would set the
# drawing extent to the whole shell and shrink the thing being judged.
PLAN_KINDS = {
    "bench": "bench", "tall_bank": "tall_bank", "island_slab": "island",
    "island_stone": "island", "drum0": "drum", "drum1": "drum",
    "stool0": "stool", "stool1": "stool", "uppers": "uppers",
}


def plan_boxes(island="corrected"):
    """(plan dicts, clearance Items) from room_spec, with the island laid either way."""
    out, items = [], []
    for name, (x0, y0, z0), (x1, y1, z1) in RS.boxes():
        if name not in PLAN_KINDS:
            continue
        if island == "wrong" and name in ("island_slab", "island_stone"):
            # The slab as built: long side 3072 ACROSS the room, near edge 420 mm
            # inside the 650 mm counter run.
            L = RS.ISL_Y1 - RS.ISL_Y0
            W = RS.ISL_W
            cy = (RS.ISL_Y0 + RS.ISL_Y1) / 2.0
            inset = 140.0 if name == "island_stone" else 0.0
            x0, x1 = RS.BENCH_DEPTH - 420.0, RS.BENCH_DEPTH - 420.0 + L
            y0, y1 = cy - W / 2.0 + inset, cy + W / 2.0 - inset
            if name == "island_stone":
                x1 = x0 + (RS.ISL_STONE_Y1 - RS.ISL_Y0)
        kind = PLAN_KINDS[name]
        out.append(dict(name=name, x0=x0, y0=y0, x1=x1, y1=y1,
                        fill=[236, 214, 208] if kind == "island" else None))
        items.append(cc.Item(name, kind, x0 / cc.MM_PER_IN, y0 / cc.MM_PER_IN,
                             (x1 - x0) / cc.MM_PER_IN, (y1 - y0) / cc.MM_PER_IN,
                             z0 / cc.MM_PER_IN, z1 / cc.MM_PER_IN))
    return out, items


def walkway(boxes):
    """The gap between the counter run's front face and the island's near face."""
    bench = next(b for b in boxes if b["name"] == "bench")
    isl = next(b for b in boxes if b["name"] == "island_slab")
    gap = isl["x0"] - bench["x1"]
    y = (isl["y0"] + isl["y1"]) / 2.0
    verdict = "FAIL" if gap < 914 else ("WARN" if gap < 1219 else "PASS")
    label = (f"walkway {gap:.0f} mm" if gap >= 0 else
             f"walkway {gap:.0f} mm — SOLIDS OVERLAP")
    return dict(a=(bench["x1"], y), b=(isl["x0"], y), mm=gap, verdict=verdict,
                label=label), gap


def run(tag, island, title):
    boxes, items = plan_boxes(island)
    g, gap = walkway(boxes)
    out = os.path.join(HERE, f"PLAN_{tag}.png")
    planview.draw(boxes, out, camera=CAM, gaps=[g], title=title, px_w=1500)
    isl = next(b for b in boxes if b["name"] == "island_slab")
    head = planview.long_axis(isl)[0]
    print(f"\n=== {tag} ===")
    print(f"  island long axis heading  {head:6.1f}°   "
          f"(the kitchen wall runs at 90°)")
    print(f"  walkway bench -> island    {gap:6.0f} mm")
    room = cc.Room(8000 / cc.MM_PER_IN, 6500 / cc.MM_PER_IN, RS.CEILING / cc.MM_PER_IN,
                   rtype="kitchen")
    res = [r for r in cc.check(room, items)
           if r["status"] != "PASS" and ("aisle" in r["check"] or "overlap" in r["check"]
                                         or "island clearance" in r["check"])]
    for r in res[:6]:
        print(f"  [{r['status']}] {r['check']}: {r['detail']}")
    print(f"  plan -> {os.path.relpath(out, REPO)}")
    return head


def drum_block():
    """The two bronze drums as PIXEL READINGS, not as a heading.

    R9's law reaching the rotation axis: a number that can be derived must not be
    typed. `pose_check` calls `recurrence.solve` on this block and computes the
    reference heading itself, so the number in the gate and the number in the
    measurement cannot drift apart — and recurrence's own self-check (base-row
    depth against silhouette-width depth) has to pass before the pose row can.
    Readings are off z-drums.png on a 25 px grid; see derive_island2.py.
    """
    import recurrence as RC
    cam = dict(f_px=4236.0, ppx=720.0, ppy=1031.0, height_mm=RS.CAM_H,
               yaw_deg=30.85, origin=[RS.CAM_TO_KITCHEN_WALL, RS.CAM_Y])
    c = RC.Camera(**cam)
    d_near = c.depth_from_base(1722.0)
    R = 225.0 * d_near / (2 * c.f)
    w_far = 2 * R * c.f / c.depth_from_base(1662.0)
    return dict(camera=cam, size_mm=2 * R,
                _what="the two bronze drums on the island base, off z-drums.png",
                instances=[dict(u_centre=505.0 + w_far / 2.0, v_base=1662.0, w_px=w_far),
                           dict(u_centre=(700.0 + 925.0) / 2.0, v_base=1722.0,
                                w_px=225.0)])


def main():
    heads = {tag: run(tag, isl, title) for tag, isl, title in (
        ("as-built-WRONG", "wrong",
         "TRN-003 kitchen — THE ISLAND AS BUILT (a quarter turn out)"),
        ("corrected", "corrected",
         "TRN-003 kitchen — the island as the two drums measure it"))}

    poses = {"_what": "Island orientation, ours vs the plate. The reference axis is "
                      "measured by RECURRENCE — two identical bronze drums at two "
                      "depths — not by fitting the slab's oval edge.",
             "poses": [
                 dict(id="island_slab", ours=heads["corrected"],
                      ref_recurrence=drum_block(), fold=2,
                      method="recurrence", tol_deg=5.0,
                      evidence="the heading is DERIVED by pose_check from the drum "
                               "pixels, never typed; overlay island_MEASURED.png"),
             ]}
    pf = os.path.join(HERE, "poses.json")
    with open(pf, "w", encoding="utf-8") as f:
        json.dump(poses, f, indent=1, ensure_ascii=False)

    print("\n=== pose_check, corrected ===")
    pc = os.path.join(REPO, "pipeline", "scripts", "pose_check.py")
    subprocess.run([sys.executable, pc, "--poses", pf])

    print("\n=== pose_check, as built (the negative control) ===")
    poses["poses"][0]["ours"] = heads["as-built-WRONG"]
    tmp = os.path.join(HERE, ".poses_asbuilt.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(poses, f, indent=1, ensure_ascii=False)
    rc = subprocess.run([sys.executable, pc, "--poses", tmp]).returncode
    os.unlink(tmp)
    print(f"  exit {rc} — a quarter turn is a FAIL, printed as a number")


if __name__ == "__main__":
    main()
