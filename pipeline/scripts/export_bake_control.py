"""export_bake_control.py — the three instrument-judged controls of STUDY-D11b
(ingest repair), written as ONE evidence file the curriculum can point at:
qa/blenderkit-study-controls.json.

  (ก) EXPORT BAKE  — positive control. The same vendor .blend is exported twice:
      with the LEGACY script (export_apply=True at the viewport SUBSURF level,
      what blenderkit.py did until 2026-09-02) and with the CURRENT script
      (levels raised to render_levels first). Both GLBs are probed by import and
      every object's face count is compared with the PREDICTION from the native
      dump — Catmull-Clark on an n-gon of n sides yields n quads at level 1 and
      x4 per further level; the GLB triangulates every quad into two. The
      control PASSES only when the legacy export reproduces the viewport
      prediction AND the current export reproduces the render prediction, per
      object, exactly. "Face count rose" alone is not a verdict — a doubled
      count is also "rose", and would mean the fix raised the wrong level.
  (ข) APPEND ROUTE — positive control. One asset probed three ways (native
      .blend / append via bpy.data.libraries.load / GLB import). PASS when the
      append route carries the vendor's modifier stack and node-tree types
      unchanged and the GLB route measurably does not (the whole reason the
      route exists: day-10 INDEX §TOP-10 rules 3-4).
  (ค) NEGATIVE     — a shelf entry with neither .blend nor .glb is REFUSED by
      the batch planner and probe_one, and no dump file is written for it.

PURE HALF (tested without Blender in test_export_bake_control.py): the legacy
script text, `predict_tris`, `export_verdict`, `append_verdict`,
`negative_verdict`. Only `run()` spawns Blender, one process at a time, waiting
for any other blender.exe to finish first (PACING fence of the study).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))
EVIDENCE = os.path.join(REPO, "qa", "blenderkit-study-controls.json")

# The export script as it stood before 2026-09-02: no level raise. Kept here
# verbatim so the control reproduces the defect on demand instead of trusting a
# GLB that happens to be on the shelf. test_export_bake_control pins that every
# line of it is still present in blenderkit.EXPORT_SCRIPT (the fix ADDED the
# raise; it did not change the export call).
LEGACY_EXPORT_SCRIPT = """import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
try:
    bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
except Exception:
    pass
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True)
"""

FACE_MULTIPLYING = {"SUBSURF", "MULTIRES", "MIRROR", "ARRAY", "SOLIDIFY",
                    "BEVEL", "BOOLEAN", "SCREW", "SKIN", "WIREFRAME",
                    "TRIANGULATE", "DECIMATE", "REMESH", "NODES", "MASK",
                    "BUILD", "EDGE_SPLIT", "WELD"}


def _tris_after(quads, tris, ngons, level):
    """Triangles the GLB will hold for a mesh after `level` Catmull-Clark
    subdivisions (None when the count cannot be derived from the dump)."""
    if level == 0:
        if ngons:
            return None       # an n-gon triangulates to n-2; n is not dumped
        return tris + 2 * quads
    if ngons:
        return None           # level-1 yields n quads per n-gon; n unknown
    faces_l1 = 4 * quads + 3 * tris
    return 2 * faces_l1 * (4 ** (level - 1))


def predict_tris(native_dump):
    """PURE. Per MESH object with exactly one SUBSURF/MULTIRES modifier and no
    other face-multiplying modifier: predicted GLB triangle count at the
    viewport level and at the render level. Everything else is listed under
    `unpredictable` with the reason, never silently dropped."""
    pred, unpred = {}, {}
    for o in native_dump.get("objects", []):
        if o.get("type") != "MESH" or "mesh" not in o:
            continue
        m = o["mesh"]
        mods = o.get("modifiers", [])
        subs = [x for x in mods if x.get("type") in ("SUBSURF", "MULTIRES")]
        others = [x["type"] for x in mods
                  if x.get("type") in FACE_MULTIPLYING
                  and x.get("type") not in ("SUBSURF", "MULTIRES")]
        if others:
            unpred[o["name"]] = "other face-multiplying modifiers: " + ",".join(others)
            continue
        if len(subs) > 1:
            unpred[o["name"]] = "stacked subsurf"
            continue
        lv = subs[0].get("levels", 0) if subs else 0
        lr = subs[0].get("render_levels", 0) if subs else 0
        tv = _tris_after(m.get("quads", 0), m.get("tris", 0), m.get("ngons", 0), lv)
        tr = _tris_after(m.get("quads", 0), m.get("tris", 0), m.get("ngons", 0), lr)
        if tv is None or tr is None:
            unpred[o["name"]] = "n-gons in base mesh (n not dumped)"
            continue
        pred[o["name"]] = {"levels": lv, "render_levels": lr,
                           "base_polys": m.get("polys", 0),
                           "viewport_tris": tv, "render_tris": tr}
    return {"predictable": pred, "unpredictable": unpred}


def _glb_tris(glb_dump):
    return {o["name"]: o["mesh"].get("tris", 0) for o in glb_dump.get("objects", [])
            if o.get("type") == "MESH" and "mesh" in o}


def _total_polys(dump):
    return sum(o.get("mesh", {}).get("polys", 0) for o in dump.get("objects", []))


def export_verdict(native_dump, legacy_dump, current_dump):
    """PURE. Per predictable object: legacy GLB tris must equal the viewport
    prediction, current GLB tris must equal the render prediction. Objects
    whose name the importer did not preserve are reported, not guessed."""
    p = predict_tris(native_dump)
    lt, ct = _glb_tris(legacy_dump), _glb_tris(current_dump)
    rows, fails, unmatched = [], [], []
    raised = 0
    for name, pr in p["predictable"].items():
        if name not in lt or name not in ct:
            unmatched.append(name)
            continue
        row = {"object": name, **pr, "legacy_tris": lt[name],
               "current_tris": ct[name],
               "legacy_ok": lt[name] == pr["viewport_tris"],
               "current_ok": ct[name] == pr["render_tris"]}
        if pr["render_levels"] > pr["levels"]:
            raised += 1
        if not (row["legacy_ok"] and row["current_ok"]):
            fails.append(name)
        rows.append(row)
    tot_l, tot_c = _total_polys(legacy_dump), _total_polys(current_dump)
    return {
        "control": "export-bake",
        "pass": bool(rows) and not fails and not unmatched and raised > 0
        and tot_c > tot_l,
        "objects_checked": len(rows), "objects_raised": raised,
        "failed_objects": fails, "unmatched_objects": unmatched,
        "unpredictable": p["unpredictable"],
        "total_polys": {"native_base": _total_polys(native_dump),
                        "legacy_glb": tot_l, "current_glb": tot_c,
                        "ratio_current_over_legacy":
                        round(tot_c / tot_l, 3) if tot_l else None},
        "rows": rows,
    }


def _node_types(dump):
    s = set()
    for m in dump.get("materials", []):
        s.update((m.get("node_hist") or {}).keys())
    return s


def _modifier_count(dump):
    return sum(len(o.get("modifiers", [])) for o in dump.get("objects", []))


def append_verdict(native_dump, append_dump, glb_dump):
    """PURE. The append route must carry modifiers and node types unchanged;
    the GLB route must measurably lose them (else the route buys nothing and
    the control cannot claim it does)."""
    nm, am, gm = (_modifier_count(d) for d in (native_dump, append_dump, glb_dump))
    nt, at, gt = (_node_types(d) for d in (native_dump, append_dump, glb_dump))
    ni = native_dump.get("totals", {}).get("images", 0)
    ai = append_dump.get("totals", {}).get("images", 0)
    gi = glb_dump.get("totals", {}).get("images", 0)
    nmat = native_dump.get("totals", {}).get("materials", 0)
    amat = append_dump.get("totals", {}).get("materials", 0)
    gmat = glb_dump.get("totals", {}).get("materials", 0)
    rep = append_dump.get("append", {}) or {}
    ok_append = (am == nm and at == nt and amat == nmat and ai == ni)
    lost_by_glb = (gm < nm) or (not nt <= gt) or (gi < ni)
    return {
        "control": "append-route",
        "pass": ok_append and lost_by_glb,
        "modifiers": {"native": nm, "append": am, "glb_import": gm},
        "node_types": {"native": sorted(nt), "append": sorted(at),
                       "glb_import": sorted(gt),
                       "lost_by_glb": sorted(nt - gt),
                       "added_by_glb_importer": sorted(gt - nt)},
        "materials": {"native": nmat, "append": amat, "glb_import": gmat},
        "images": {"native": ni, "append": ai, "glb_import": gi},
        "append_report": {k: rep.get(k) for k in
                          ("appended", "skipped", "missing", "renamed")},
    }


def negative_verdict(plan_refused, probe_rc, dump_exists, wrong_kind_rc,
                     wrong_kind_dump_exists):
    """PURE. Refused by the planner, refused by probe_one (rc 2), and no dump
    on disk in either case."""
    return {
        "control": "negative-neither-file",
        "pass": bool(plan_refused) and probe_rc == 2 and not dump_exists
        and wrong_kind_rc == 2 and not wrong_kind_dump_exists,
        "planner_refused": plan_refused,
        "probe_one_missing_rc": probe_rc, "dump_written": dump_exists,
        "probe_one_wrong_kind_rc": wrong_kind_rc,
        "wrong_kind_dump_written": wrong_kind_dump_exists,
    }


# ------------------------------------------------------------------ spawn half
def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _export(exe, blend, script_text, glb, scratch, tag):
    import blenderkit as BK
    import model_study_probe as P
    script = os.path.join(scratch, f"_export_{tag}.py")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(script_text)
    P.wait_for_idle_blender()
    t0 = time.time()
    p = subprocess.run(BK.export_cmd(exe, blend, script, glb), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=1800)
    ok = p.returncode == 0 and os.path.exists(glb) and os.path.getsize(glb) > 0
    line = [ln for ln in (p.stdout or "").splitlines() if ln.startswith("EXPORT_GLB")]
    print(f"{'OK  ' if ok else 'FAIL'} export[{tag}] {os.path.basename(glb)} "
          f"{round(time.time() - t0, 1)}s {line}")
    if not ok:
        raise RuntimeError(f"export {tag} failed: {(p.stdout or '')[-400:]}")
    return {"glb": glb, "bytes": os.path.getsize(glb), "seconds": round(time.time() - t0, 1),
            "stdout_line": line[0] if line else None}


def run(export_asset_dir, append_asset_dir, scratch, out=EVIDENCE, blender=None):
    import blenderkit as BK
    import blend_append as BA
    import model_study_probe as P
    exe = blender or BK.find_blender()
    os.makedirs(scratch, exist_ok=True)
    ev = {"written": time.strftime("%Y-%m-%dT%H:%M:%S"), "blender": exe,
          "controls": {}}

    # (ก) export bake --------------------------------------------------------
    blend = BA.pick_blend(export_asset_dir)
    base = os.path.basename(os.path.normpath(export_asset_dir))
    legacy_glb = os.path.join(scratch, base + ".legacy.glb")
    current_glb = os.path.join(scratch, base + ".render.glb")
    e1 = _export(exe, blend, LEGACY_EXPORT_SCRIPT, legacy_glb, scratch, "legacy")
    e2 = _export(exe, blend, BK.EXPORT_SCRIPT, current_glb, scratch, "current")
    dumps = {}
    for tag, path, kind in (("native", blend, "blend"), ("legacy", legacy_glb, "glb"),
                            ("current", current_glb, "glb")):
        o = os.path.join(scratch, f"{base}.{tag}.probe.json")
        if P.probe_one(path, o, kind=kind, blender=exe) != 0:
            raise RuntimeError(f"probe {tag} failed")
        dumps[tag] = _load(o)
    v = export_verdict(dumps["native"], dumps["legacy"], dumps["current"])
    v.update({"asset": base, "blend": blend, "legacy_export": e1,
              "current_export": e2,
              "shelf_glb_bytes": next((os.path.getsize(os.path.join(export_asset_dir, f))
                                       for f in os.listdir(export_asset_dir)
                                       if f.endswith(".glb")), None)})
    ev["controls"]["export_bake"] = v
    print(f"EXPORT-BAKE {'PASS' if v['pass'] else 'FAIL'} "
          f"{v['objects_checked']} objects, ratio {v['total_polys']}")

    # (ข) append route --------------------------------------------------------
    blend2 = BA.pick_blend(append_asset_dir)
    base2 = os.path.basename(os.path.normpath(append_asset_dir))
    glb2 = os.path.join(scratch, base2 + ".render.glb")
    _export(exe, blend2, BK.EXPORT_SCRIPT, glb2, scratch, "current2")
    d2 = {}
    for tag, path, kind in (("native", blend2, "blend"), ("append", blend2, "append"),
                            ("glb", glb2, "glb")):
        o = os.path.join(scratch, f"{base2}.{tag}.probe.json")
        if P.probe_one(path, o, kind=kind, blender=exe) != 0:
            raise RuntimeError(f"probe {tag} failed")
        d2[tag] = _load(o)
    a = append_verdict(d2["native"], d2["append"], d2["glb"])
    a.update({"asset": base2, "blend": blend2})
    ev["controls"]["append_route"] = a
    print(f"APPEND-ROUTE {'PASS' if a['pass'] else 'FAIL'} modifiers {a['modifiers']} "
          f"lost_by_glb {a['node_types']['lost_by_glb']}")

    # (ค) negative -------------------------------------------------------------
    tmp = tempfile.mkdtemp(prefix="neg_", dir=scratch)
    try:
        os.makedirs(os.path.join(tmp, "zzzz-empty"))
        with open(os.path.join(tmp, "zzzz-empty", "SOURCE.json"), "w") as f:
            f.write("{}")
        items, refused = P.plan(tmp)
        dump_missing = os.path.join(tmp, "missing.probe.json")
        rc_missing = P.probe_one(os.path.join(tmp, "zzzz-empty", "nope.blend"),
                                 dump_missing, blender=exe, wait=False)
        dump_wrong = os.path.join(tmp, "wrong.probe.json")
        rc_wrong = P.probe_one(legacy_glb, dump_wrong, kind="append", blender=exe,
                               wait=False)
        n = negative_verdict(refused, rc_missing, os.path.exists(dump_missing),
                             rc_wrong, os.path.exists(dump_wrong))
        n["planner_items"] = items
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ev["controls"]["negative"] = n
    print(f"NEGATIVE {'PASS' if n['pass'] else 'FAIL'} {n['planner_refused']}")

    ev["pass_all"] = all(c["pass"] for c in ev["controls"].values())
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ev, f, indent=1, ensure_ascii=False)
    print(f"CONTROLS {'PASS' if ev['pass_all'] else 'FAIL'} -> {out}")
    return 0 if ev["pass_all"] else 1


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("export_asset_dir")
    ap.add_argument("append_asset_dir")
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", default=EVIDENCE)
    ap.add_argument("--blender", default=None)
    a = ap.parse_args(argv)
    return run(a.export_asset_dir, a.append_asset_dir, a.scratch, a.out, a.blender)


if __name__ == "__main__":
    sys.exit(main())
