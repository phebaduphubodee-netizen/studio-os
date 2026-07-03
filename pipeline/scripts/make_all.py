"""
make_all.py — one-button pipeline:  brief/spec -> validate -> ALL deliverables.

    python pipeline/make_all.py pipeline/specs/living_demo.json   # from a spec
    python pipeline/make_all.py --brief living 14 16              # brief -> auto-layout -> deliverables
    python pipeline/make_all.py --brief living 14 16 --render     # + Cycles preview embedded in the package
    python pipeline/make_all.py <spec> --no-package               # loose files only (skip the folder)
    python pipeline/make_all.py <spec> --repair                   # + M3.3 closed-loop photoreal hero (PAID, ask-tier; implies --render)

Flow (the load-bearing order — VALIDATE BEFORE BUILD):
  1. brief -> spec        (layout_gen, if --brief)
  2. clearance GATE       (clearance_check) — a FAIL stops here; we never emit a
                           deliverable from a spec that fails dimensional checks.
  3. 2D "แบบ"             (plan_2d)        -> output/plan_<type>.dxf (+ .png)
  3b. RCP                 (rcp)            -> output/rcp_<type>.dxf (+ .png)
  3c. CD schedules        (schedules)      -> output/schedules_<type>.md (+ CSVs)
  3d. Interior elevations (elevations)     -> output/elev_<type>_<wall>.dxf (+ .png) x4
  4. Blender render/GLB   (build_room.py)  -> output/room_<type>.blend (+ .png with --render);
                           Blender is auto-found even off PATH; skipped with a hint if absent.
  5. Native SketchUp      (build_room.rb)  -> the friend runs it (one `load` line);
                           printed as a manual step (no SketchUp on this machine).
  6. ASSEMBLE package     (package)        -> output/deliverable_<type>/ : one sheet-set PDF
                           (cover -> plan -> RCP -> elevations -> schedules -> render) + the
                           editable DXF/.skp masters + spec + QA-CHECKLIST.md (the sign-off gate).
"""
import glob
import json
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clearance_check
import plan_2d
import layout_gen
import lighting
import rcp
import schedules
import elevations
import package


def _find_blender():
    """Locate Blender even when it is installed but NOT on PATH (the common Windows
    case: `C:\\Program Files\\Blender Foundation\\Blender X.Y\\blender.exe`). Order:
    $INTERIOR_BLENDER -> PATH -> known install globs. Returns a path or None."""
    env = os.environ.get("INTERIOR_BLENDER")
    if env and os.path.exists(env):
        return env
    onpath = shutil.which("blender")
    if onpath:
        return onpath
    globs = [
        r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender*\blender.exe",
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/usr/bin/blender", "/usr/local/bin/blender", "/snap/bin/blender",
    ]
    hits = []
    for g in globs:
        hits.extend(glob.glob(g))
    hits = [h for h in hits if os.path.exists(h)]
    hits.sort(reverse=True)   # prefer the newest versioned install
    return hits[0] if hits else None


def _spec_from_args(args):
    """Return (spec_path, name). Generates + writes a spec when given --brief."""
    out = plan_2d._outdir()
    if args and args[0] == "--brief":
        if len(args) < 4:
            sys.exit("usage: python make_all.py --brief <room_type> <width_ft> <depth_ft>")
        brief = {"room_type": args[1], "width_ft": float(args[2]), "depth_ft": float(args[3])}
        spec = layout_gen.generate(brief)
        name = brief["room_type"]
        spec_path = os.path.join(out, f"spec_{name}.json")
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"  [1] auto-layout -> {spec_path}  (layout_status={spec.get('layout_status')})")
        return spec_path, name
    if not args:
        sys.exit("usage: python make_all.py <spec.json>  |  --brief <type> <w> <d>")
    spec_path = args[0]
    spec = plan_2d.load_spec(spec_path)
    return spec_path, spec["room"].get("type", "room")


def main():
    # optional flags (order-independent) stripped before spec/brief parsing:
    #   --render      force a Cycles render so the package embeds the preview
    #   --no-package  emit loose files only (skip the assembled deliverable folder)
    raw = sys.argv[1:]
    do_repair = "--repair" in raw or "--repair-pro" in raw
    repair_tier = "pro" if "--repair-pro" in raw else "flash"
    do_render = "--render" in raw or do_repair   # repair beautifies the clay PNG, so force it
    do_package = "--no-package" not in raw
    do_critique = "--critique" in raw or "--critique-pro" in raw
    crit_model = "pro" if "--critique-pro" in raw else "flash"
    args = [a for a in raw if a not in ("--render", "--no-package", "--critique",
                                        "--critique-pro", "--repair", "--repair-pro")]

    spec_path, name = _spec_from_args(args)
    out = plan_2d._outdir()
    produced, skipped = [], []

    # 2) clearance GATE — geometry + lighting/IES completeness (KB §6) in one verdict.
    #    Derive the lighting layer ONCE here; it feeds the gate AND the RCP + schedule
    #    below, so all three see the identical fixtures (the relational rule, KB §3).
    room, items, spec = clearance_check.load_spec(spec_path)
    light_fixtures, _ = lighting.plan_lighting(spec)
    light_results = clearance_check.check_lighting(spec, light_fixtures)
    verdict = clearance_check.report(room, items, os.path.basename(spec_path), extra=light_results)
    if verdict == "FAIL":
        sys.exit("\n  STOP: clearance FAILED — fix the spec before generating deliverables.")

    # 3) 2D แบบ
    doc = plan_2d.build_dxf(spec)
    dxf = os.path.join(out, f"plan_{name}.dxf")
    doc.saveas(dxf)
    produced.append(dxf)
    png = plan_2d.export_preview(doc, os.path.join(out, f"plan_{name}.png"))
    produced.append(png) if png else skipped.append("2D preview PNG (pip install matplotlib)")

    # 3b) Reflected Ceiling Plan — reuses light_fixtures from the gate (same list -> the
    #     RCP, the schedule, and the IES check all agree by construction, KB §3).
    rcp_doc, fixtures, type_rows = rcp.build_dxf(spec, light_fixtures)
    rcp_dxf = os.path.join(out, f"rcp_{name}.dxf")
    rcp_doc.saveas(rcp_dxf)
    produced.append(f"{rcp_dxf}  ({len(fixtures)} fixtures, {len(type_rows)} types)")
    rcp_png = plan_2d.export_preview(rcp_doc, os.path.join(out, f"rcp_{name}.png"))
    produced.append(rcp_png) if rcp_png else skipped.append("RCP preview PNG (pip install matplotlib)")

    # 3c) CD schedules (door / finish / lighting) — same fixtures list as the RCP
    for p in schedules.write(spec, out, name, light_fixtures):
        produced.append(p)

    # 3d) Interior elevations — one per wall, heights straight from the spec (KB §3).
    #     Completes the drawing set (a CD set is not complete without elevations).
    for wall, edoc in elevations.build_all(spec):
        edxf = os.path.join(out, f"elev_{name}_{wall}.dxf")
        edoc.saveas(edxf)
        produced.append(edxf)
        epng = plan_2d.export_preview(edoc, os.path.join(out, f"elev_{name}_{wall}.png"))
        produced.append(epng) if epng else skipped.append(f"elevation {wall} PNG (pip install matplotlib)")

    # 4) Blender render / .blend — auto-find Blender even if it is off PATH; only actually
    #    render when asked (--render), since Cycles is slow. The package embeds the PNG if present.
    blender = _find_blender()
    if blender:
        cmd = [blender, "-b", "--factory-startup", "--python",
               os.path.join(HERE, "build_room.py"), "--", spec_path]
        if do_render:
            cmd.append("--render")
        print(f"  [4] Blender: {blender}" + ("  -> rendering (--render)" if do_render else "  -> .blend only (pass --render for a preview)"))
        rc = subprocess.run(cmd)
        (produced if rc.returncode == 0 else skipped).append(os.path.join(out, f"room_{name}.blend (Blender)"))
        if do_render:
            rpng = os.path.join(out, f"room_{name}.png")
            (produced if os.path.exists(rpng) else skipped).append(rpng + " (render)")
    else:
        skipped.append("Blender render/.blend (not found; set $INTERIOR_BLENDER or install blender.org/download)")

    # 4b) OPT-IN closed-loop repair (M3.3, repair_loop.py) — turn the clay CONTROL
    #     into a photoreal hero through Gates 1-4 + critique/repair. PAID (Gemini image
    #     + vision, ask-tier); default OFF. The winning candidate replaces the clay in
    #     the package. NOTE: the Gate-3 judge is ADVISORY until M3.2 calibration passes
    #     (judge_calibrate.py) — the loop runs, but trust its SHIP verdict accordingly.
    repair_render = None
    if do_repair:
        clay = os.path.join(out, f"room_{name}.png")
        if not os.path.exists(clay):
            skipped.append("repair loop (no clay PNG — Blender missing or render failed)")
        else:
            # A repair failure must NEVER cost the deliverable: this runs BEFORE
            # package assembly, and the real adapters can raise (e.g. hybrid_render
            # SystemExit on a missing GEMINI key / registry slot). Degrade to
            # packaging the clay so --repair never yields LESS than a plain run.
            try:
                import repair_loop
                rr = repair_loop.repair_loop(
                    name, clay, spec, spec_path, {"room_type": name},
                    render_fn=repair_loop._real_render_fn, judge_fn=repair_loop._real_judge_fn,
                    structure_fn=repair_loop._real_structure_fn, geometry_fn=repair_loop._real_geometry_fn,
                    sanity_fn=repair_loop._real_sanity_fn, registry_key="@render-hybrid",
                    outdir=out, qa_dir=os.path.join(out, "05_qa"), tier=repair_tier)
                inbox = os.path.relpath(rr["inbox_pointer"], HERE) if rr.get("inbox_pointer") else "-"
                if rr["outcome"] == repair_loop.RESOLVED:
                    repair_render = rr["final_candidate"]
                    produced.append(f"REPAIR: photoreal resolved at cycle {rr['accepted_cycle']} "
                                    f"-> {os.path.basename(repair_render)}  (review: {inbox})")
                else:
                    produced.append(f"REPAIR: {rr['outcome']} after {rr['cycles_used']} cycle(s) "
                                    f"-> packaging the clay instead  (triage: {inbox})")
            except (SystemExit, Exception) as e:  # noqa: BLE001 — never lose the deliverable
                skipped.append(f"repair loop failed ({type(e).__name__}: {e}) — packaging the clay instead")

    # 5) Native SketchUp = manual step (no SketchUp here)
    rb = os.path.join(HERE, "build_room.rb")

    # 6) ASSEMBLE the deliverable — loose files -> one reviewable folder + sheet-set PDF + QA gate.
    #    Embed the render ONLY if we JUST produced one this run (--render); passing False
    #    blocks a stale render from a different layout silently shipping (the illusion guard).
    folder = None
    if do_package:
        rp = os.path.join(out, f"room_{name}.png")
        # a resolved repair (photoreal) wins; else the clay only if we rendered it this run
        render_for_pkg = repair_render or (rp if (do_render and os.path.exists(rp)) else False)
        folder, pdf = package.build(spec, spec_path, name, fixtures=light_fixtures,
                                    render_png=render_for_pkg)
        produced.append(f"DELIVERABLE: {folder}")
        produced.append(pdf if pdf else "(!) SHEETSET.pdf skipped (needs matplotlib + ezdxf)")

    # 6b) HONEST CRITIQUE GATE (opt-in --critique) — an independent vision critic scores the
    #     artifacts a human/client actually LOOKS at (the plan PNG + the render), prompted to
    #     find what is WRONG. Non-blocking (human owns the call), but it refuses to let a
    #     "looks fine" go unchallenged — and it judges the rendered OUTPUT, not just the spec.
    crit_results = []
    if do_critique:
        import critique
        # score the image the package actually ships: the repaired photoreal hero if
        # a repair resolved, otherwise the clay render (not a stale/unshipped image)
        hero = repair_render or os.path.join(out, f"room_{name}.png")
        targets = [t for t in (png, hero) if t and os.path.exists(t)]
        crit_results = critique.run_batch(targets, model_key=crit_model)
        if crit_results:
            md = critique.to_markdown(crit_results)
            crit_md = os.path.join(folder or out, "CRITIQUE.md")
            with open(crit_md, "w", encoding="utf-8") as f:
                f.write(md)
            produced.append(f"CRITIQUE: {crit_md}  ({crit_model} vision critic)")

    print("\n=== make_all summary ===")
    print(f"  clearance: {verdict}")
    for p in produced:
        print(f"  PRODUCED: {p}")
    for s in skipped:
        print(f"  skipped:  {s}")
    if do_critique and crit_results:
        print("  --- independent critique (non-blocking) ---")
        for r in crit_results:
            print(f"  CRITIQUE: {r.get('_artifact')}: {r.get('verdict')} "
                  f"({r.get('overall_0_5','?')}/5) — {r.get('one_line','')}")
        bad = [r for r in crit_results if r.get("verdict") in critique.NOT_READY]
        if bad:
            print(f"  ⚠️  {len(bad)}/{len(crit_results)} artifact(s) judged NOT client-ready by the "
                  f"independent critic — see CRITIQUE.md. (DRAFT/placeholder, not a failure to hide.)")
    elif not do_critique:
        print("  (machine critique skipped — add --critique for an independent quality check of the render/plan)")
    print(f"  MANUAL (editable SketchUp): in SketchUp Pro -> Ruby Console -> "
          f"$INTERIOR_SPEC='{spec_path}'; load '{rb}'")
    if folder:
        print(f"  >>> REVIEW GATE: sign {os.path.join(folder, 'QA-CHECKLIST.md')} before any client use.")
    print("  (deliverables are DRAFT — human QA on scale + local code before any client use)")


if __name__ == "__main__":
    main()
