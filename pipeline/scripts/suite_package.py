"""
suite_package.py — INTERIOR-AI v0.2 deliverable assembler (METRIC suite).

Assembles the room-spec@0.2 suite into ONE reviewable metric package:

    output/deliverable_<type>/
      <type>_SHEETSET.pdf   # cover (+ clearance verdict) -> metric floor plan -> schedules
      suiteplan_<type>.dxf  # editable metric CAD master (1:1 mm)
      <type>.spec.json      # the exact v0.2 spec
      QA-CHECKLIST.md       # metric, Thai-code-aware sign-off gate
      README.md

Reuses the v0.1 sheet machinery (package.py: title block, white-DXF-on-sheet, cover) so the
output matches the rest of the project, and the SAME metric clearance verdict (suite_clearance)
feeds the cover + QA (the relational rule). Elevations / RCP / 3D for the polygon are later phases.

    python pipeline/suite_package.py [spec.json]

Needs ezdxf + matplotlib (same as package.py).
"""
import datetime
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan_2d
import package
import suite_plan
import suite_clearance
import suite_lighting     # metric polygon lighting layer (the shared fixtures)
import suite_rcp          # metric polygon RCP
import suite_elevations   # per-edge metric elevations

SCALE = "1:50"


def _schedules(spec):
    """(door, millwork, furniture) schedules straight from the v0.2 spec (metric)."""
    r = spec["room"]
    door = spec.get("door") or {}
    door_rows = []
    if door:
        door_rows.append(["D-01", f'{door.get("wall","?")} wall',
                          f'{float(door.get("w",0)):.0f} x {float(door.get("h",0)):.0f} mm', "Entry, swing"])
    for i, sr in enumerate(spec.get("subrooms", []), start=2):
        sd = sr.get("door")
        if sd:
            door_rows.append([f"D-0{i}", sr.get("name", "sub"),
                              f'{float(sd.get("w",0)):.0f} x {float(sd.get("h",door.get("h",2000))):.0f} mm', "Interior"])
    door = {"title": "DOOR SCHEDULE", "cols": ["Tag", "Location", "Size (W x H)", "Type"], "rows": door_rows,
            "note": "Sizes from the model; leaf/hardware are DRAFT (designer specifies)."}

    mrows = [[f"BI-{i+1:02d}", b.get("name", b.get("kind", "millwork")),
              f'{float(b["w"]):.0f} x {float(b["d"]):.0f} x {float(b.get("h",2800)):.0f} mm', "1"]
             for i, b in enumerate(spec.get("builtins", []))]
    mill = {"title": "BUILT-IN / MILLWORK SCHEDULE", "cols": ["Tag", "Item", "Size (L x D x H)", "Qty"], "rows": mrows,
            "note": "Built-in millwork (wardrobes / headboard-TV). Sizes model-derived; finish DRAFT."}

    frows = [[it.get("name", it.get("kind", "item")),
              f'{float(it["w"]):.0f} x {float(it["d"]):.0f} x {float(it.get("h",0)):.0f} mm', "1"]
             for it in spec.get("items", []) if it.get("kind") != "platform"]
    furn = {"title": "FURNITURE (FF&E)", "cols": ["Item", "Size (W x D x H)", "Qty"], "rows": frows,
            "note": "Loose furniture. Confirm real product sizes + licensing/provenance (see QA)."}
    return [door, mill, furn]


def _sched_sheet(fig, spec):
    tops = (0.90, 0.66, 0.42)
    for s, top in zip(_schedules(spec), tops):
        ax = fig.add_axes([0.05, top - 0.20, 0.90, 0.19]); ax.set_axis_off()
        ax.text(0, 1.02, s["title"], fontsize=10, fontweight="bold", transform=ax.transAxes)
        rows = s["rows"] or [["—"] * len(s["cols"])]
        tab = ax.table(cellText=rows, colLabels=s["cols"], loc="upper center", cellLoc="left")
        tab.auto_set_font_size(False); tab.set_fontsize(7.5 if len(rows) <= 6 else 6.5); tab.scale(1, 1.3)
        for (rr, _cc), cell in tab.get_celld().items():
            cell.set_linewidth(0.4)
            if rr == 0:
                cell.set_text_props(fontweight="bold"); cell.set_facecolor("0.92")
        ax.text(0, -0.02, s["note"], fontsize=6.5, color="0.4", va="top", transform=ax.transAxes)
    fig.text(0.05, 0.163, "Metric (mm). All schedules model-derived from the v0.2 spec — DRAFT, verify vs DWG + local code.",
             fontsize=6.5, color="0.4")


def _qa_md(spec, res, verdict, spec_path, sourceability=None):
    r = spec["room"]; outline = [tuple(p) for p in r["outline_mm"]]
    area = suite_clearance._shoelace(outline) / 1e6
    W = max(p[0] for p in outline); D = max(p[1] for p in outline)
    warns = [x for x in res if x["status"] == "WARN"]; fails = [x for x in res if x["status"] == "FAIL"]
    P = [f"# QA CHECKLIST — {r.get('type','room').replace('_',' ').upper()} (metric)",
         f"bounding {W/1000:.1f} x {D/1000:.1f} m · ~{area:.1f} m² · ceiling {float(r.get('ceiling_mm',0))/1000:.1f} m",
         "",
         f"**Engine verdict: `{verdict}`** ({len(fails)} FAIL · {len(warns)} WARN · DRAFT). "
         "Sign before any client sees this. Positions are APPROXIMATED from the plan image — "
         "confirm vs the friend's real DWG first.", ""]
    P.append("## 1 · Geometry vs the real plan/DWG")
    P.append(f"- [ ] Overall bounding {W:.0f} x {D:.0f} mm (L-shape) matches the DWG? (width read from a clipped dim)")
    P.append(f"- [ ] Ceiling {float(r.get('ceiling_mm',0)):.0f} mm; ensuite ceiling correct?")
    for it in spec.get("items", []) + spec.get("builtins", []):
        nm = it.get("name") or it.get("kind", "item")
        P.append(f"- [ ] {nm}: {float(it['w']):.0f} x {float(it['d']):.0f} mm — position + size vs DWG?")
    P.append("")
    P.append("## 2 · Thai code (knowledge/codes-th/mr55-residential-dimensions.md — Authority; supersedes the 2026-06-30 thai-building-code DR)")
    if fails:
        P.append("**FAIL:**"); P += [f"- [ ] ❌ {x['check']}: {x['detail']}" for x in fails]
    if warns:
        P.append("**WARN:**"); P += [f"- [ ] ⚠️ {x['check']}: {x['detail']}" for x in warns]
    P.append("- [ ] Rules verified vs the ratchakitcha text (กฎกระทรวง 55) — DRAFT until then.")
    P.append("- [ ] ⚠️ Permit drawings need an **architect's seal** (interior design = controlled profession, พ.ร.บ.สถาปนิก 2543) → the friend signs.")
    P.append("")
    P.append("## 3 · Furniture provenance & licensing")
    P.append("- ✅ friend confirmed: self-modeled + 3D Warehouse (both OK to ship). Ship the ASSEMBLED SCENE only, never a standalone Warehouse model.")
    P.append("- [ ] Confirmed each component's source again for this deliverable.")
    P.append("")
    if sourceability is not None:
        sv = sourceability.get("verdict", "UNWIRED")
        ffe_present = sourceability.get("ffe_present", False)
        P.append("## 4 · Sourceability & deliverable bundle (sourceability_gate — the moat)")
        P.append(f"- **Sourceability verdict: `{sv}`** — every rendered SOURCED piece must bind (`ffe_tag`) "
                 "to a real, right-sized, supplied, verified Thai product. FABRICATED built-ins are joiner-made.")
        if sv == "UNWIRED":
            P.append("- [ ] ⚠️ No FF&E file for this project — furniture is NOT sourced-confirmed. This "
                     "deliverable is **CONCEPT ONLY** until `ffe-candidates.json` + `ffe_tag` bindings exist.")
        elif sv == "FAIL":
            P.append("- [ ] ❌ A sourced piece is unbound / wrong-size / has no supplier — the render shows "
                     "furniture the client cannot buy. Fix the binding before delivery (see rows above).")
        elif sv == "REVIEW":
            P.append("- [ ] ⚠️ Sourced picks are DRAFT (`verified:false`) — confirm price/lead/specs with the "
                     "vendor, then set `verified:true`.")
        if ffe_present:
            P.append("- [ ] `ffe-schedule.md` + `ffe-candidates.json` are bundled in this folder "
                     "(regenerate via `scripts/ffe_schedule.py`; the JSON is the source of truth).")
        P.append("- [ ] Client **BOM** attached (Stage-07 `bom-generate`, human-triggered) — a render ships "
                 "WITH its FF&E schedule + BOM, never alone.")
        P.append("- [ ] Render prompt NAMES each selected real product (generative-hallucination guard, check-5).")
        P.append("")
    P.append("## SIGN-OFF")
    P.append("- Reviewed by: __________  Date: ______   - [ ] APPROVED for client")
    if spec_path:
        P.append(""); P.append(f"_Spec: `{os.path.basename(spec_path)}` · generated by suite_package.py_")
    return "\n".join(P)


def build(spec, spec_path, name=None, outdir=None, date=None, render_png=None):
    name = name or spec["room"].get("type", "room")
    base = outdir or plan_2d._outdir()
    folder = os.path.join(base, f"deliverable_{name}")
    os.makedirs(folder, exist_ok=True)
    date = date or datetime.date.today().isoformat()

    # 3D preview render (Blender build_room.py). Embed ONLY a render that exists — default
    # looks for output/room_<name>.png (produced fresh by the Blender pass), else no sheet.
    if render_png is None:
        cand = os.path.join(base, f"room_{name}.png")
        render_png = cand if os.path.exists(cand) else None
    if render_png and os.path.exists(render_png):
        shutil.copy2(render_png, os.path.join(folder, f"room_{name}.png"))

    r = spec["room"]; outline = [tuple(p) for p in r["outline_mm"]]
    W = max(p[0] for p in outline); D = max(p[1] for p in outline)
    sqm = suite_clearance._shoelace(outline) / 1e6
    tb = {"project": package.PROJECT,
          "room": f"{r.get('type','room').replace('_',' ').upper()}  {W/1000:.1f} x {D/1000:.1f} m  (~{sqm:.0f} m²)",
          "date": date, "status": "DRAFT"}

    res, verdict = suite_clearance.check(spec), None
    # FUNCTION layer (placement_logic) rides the SAME cover verdict + QA-CHECKLIST as the
    # metric clearance gate — the M3.2 answer: the render judge scores beauty and is blind
    # to a TV with no controllable position (fused into a headboard/feature wall) or a bed
    # with its head on the door wall. Rows share the {status,check,detail} shape (checks
    # prefixed 'function:'); a FUNCTION FAIL escalates the deliverable verdict. A bug in the
    # layer must never block the deliverable -> degrade silently to clearance-only.
    try:
        import placement_logic
        res = list(res) + placement_logic.report(spec)[0]
    except Exception:  # noqa: BLE001
        pass
    # SOURCEABILITY layer (sourceability_gate, the moat, strategy 2026-07-06): the render must
    # VISUALIZE a sourceable spec. Rows ride the SAME cover verdict + QA-CHECKLIST — a sourced
    # piece unbound / wrong-size / unsupplied FAILs the deliverable; verified:false -> WARN. Plus
    # the deliverable-bundle rule: a render is not a deliverable without its FF&E schedule + BOM.
    # A bug here must never block the deliverable -> degrade silently to clearance+function only.
    s_verdict, ffe_present, ffe_doc, ffe_path = "UNWIRED", False, None, None
    try:
        import sourceability_gate
        ffe_doc, ffe_path = sourceability_gate.load_ffe(spec_path, spec)
        s_results, s_verdict = sourceability_gate.report(spec, ffe_doc)
        ffe_present = ffe_doc is not None
        res = list(res) + sourceability_gate.report_rows(s_results) \
                        + sourceability_gate.bundle_rows(s_verdict, ffe_present, bool(render_png))
    except Exception:  # noqa: BLE001
        pass
    fails = sum(x["status"] == "FAIL" for x in res); warns = sum(x["status"] == "WARN" for x in res)
    verdict = "FAIL" if fails else ("REVIEW" if warns else "PASS")

    # spec + DXF masters + QA + README. Derive the lighting layer ONCE and thread it to
    # the RCP so the RCP, its legend, and any lighting schedule agree by construction.
    with open(os.path.join(folder, f"{name}.spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    fixtures, _lmeta = suite_lighting.plan_lighting(spec)
    suite_doc = suite_plan.build_dxf(spec)
    rcp_doc, _fx, _rows = suite_rcp.build_dxf(spec, fixtures)
    elev_docs = suite_elevations.build_all(spec)          # [(edge_index, dir_label, doc)]
    suite_doc.saveas(os.path.join(folder, f"suiteplan_{name}.dxf"))
    rcp_doc.saveas(os.path.join(folder, f"suitercp_{name}.dxf"))
    for ei, lab, edoc in elev_docs:
        edoc.saveas(os.path.join(folder, f"suiteelev_{name}_{ei+1}_{lab}.dxf"))
    with open(os.path.join(folder, "QA-CHECKLIST.md"), "w", encoding="utf-8") as f:
        f.write(_qa_md(spec, res, verdict, spec_path,
                       sourceability={"verdict": s_verdict, "ffe_present": ffe_present}))
    # deliverable BUNDLE (sourceability): when the project has an FF&E file, ship the FF&E
    # schedule + candidates INSIDE the deliverable — a render is not a deliverable without its
    # schedule + BOM. Best-effort: a generation error must never block the deliverable.
    if ffe_present and ffe_path:
        try:
            shutil.copy2(ffe_path, os.path.join(folder, "ffe-candidates.json"))
            repo_scripts = os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts")
            if repo_scripts not in sys.path:
                sys.path.insert(0, repo_scripts)
            import ffe_schedule
            with open(os.path.join(folder, "ffe-schedule.md"), "w", encoding="utf-8") as f:
                f.write(ffe_schedule.render(ffe_doc))
        except Exception:  # noqa: BLE001
            pass
    # DESIGN RATIONALE — the per-element cited "why here / why this placement / size /
    # material" companion to the QA checklist. Honesty-first: it labels every hardcoded
    # material default as such. If a PERSONA is discoverable for this spec, the presence
    # axis upgrades from "declared in spec" to "serves activity X (the client does Y)" —
    # per-element, so it is valid for a single-room deliverable (home-level GAP coverage is
    # the project-level persona report, not a per-room one). A rationale/persona bug must
    # NEVER block the deliverable (same discipline as the FUNCTION merge) -> degrade silently.
    try:
        import rationale
        persona_obj = None
        try:
            import persona as _persona
            persona_obj = _persona.find_persona_for(spec, spec_path) or None
        except Exception:  # noqa: BLE001
            persona_obj = None
        with open(os.path.join(folder, "RATIONALE.md"), "w", encoding="utf-8") as f:
            f.write(rationale.to_markdown(spec, os.path.basename(spec_path), persona=persona_obj))
    except Exception:  # noqa: BLE001
        pass
    # native-SketchUp generator (the editable-3D route) — the friend runs one `load` line
    rb_src = os.path.join(HERE, "build_room.rb")
    if os.path.exists(rb_src):
        shutil.copy2(rb_src, os.path.join(folder, "build_room.rb"))
    n_elev = len(elev_docs)
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# {package.PROJECT} deliverable — {tb['room']} (metric, v0.2)\n\n"
                f"Assembled {date}. **DRAFT** — positions read from the friend's 1:75 furniture plan where "
                f"legible, else approximated; overall footprint / ceilings / windows still to confirm vs the DWG. "
                f"Sign `QA-CHECKLIST.md` before any client use.\n\n"
                f"- `{name}_SHEETSET.pdf` — the CD set: cover · floor plan (1:50) · RCP · {n_elev} wall elevations · schedules\n"
                f"- `suiteplan_{name}.dxf`, `suitercp_{name}.dxf`, `suiteelev_{name}_*.dxf` — editable metric CAD masters (1:1 mm; open in any DXF app)\n"
                f"- `{name}.spec.json` — the room-spec@0.2 everything derives from\n"
                f"- `RATIONALE.md` — per-element cited *why* (placement / size / material); flags every hardcoded material default\n"
                f"- `build_room.rb` — builds the **native, editable** 3D model inside SketchUp Pro "
                f"(Window ▸ Ruby Console → `$INTERIOR_SPEC='.../{name}.spec.json'; load '.../build_room.rb'`)\n")

    # PDF (reuse package.py sheet machinery). Full CD set for the polygon suite:
    #   cover -> floor plan -> RCP -> N wall elevations -> schedules.
    backend = package._pdf_backend()
    pdf_path = None
    if backend:
        plt, PdfPages, Rectangle, ezdxf_bits = backend
        # sheets carry a (sheet_no, title, kind, payload_doc)
        sheets = [("G-000", "COVER / SHEET INDEX", "cover", None),
                  ("A-101", "FLOOR PLAN (metric)", "dxf", suite_doc),
                  ("A-102", "REFLECTED CEILING PLAN", "dxf", rcp_doc)]
        for k, (ei, lab, edoc) in enumerate(elev_docs):
            sheets.append((f"A-2{k+1:02d}", f"INTERIOR ELEVATION {ei+1} ({lab})", "dxf", edoc))
        sheets.append(("A-601", "SCHEDULES (DOOR / MILLWORK / FF&E)", "sched", None))
        if render_png and os.path.exists(render_png):
            sheets.append(("A-701", "3D PREVIEW (Blender massing)", "render", render_png))
        index = [(no, nm) for no, nm, _k, _p in sheets]
        pdf_path = os.path.join(folder, f"{name}_SHEETSET.pdf")
        with PdfPages(pdf_path) as pdf:
            for pi, (no, nm, kind, payload) in enumerate(sheets, start=1):
                fig, frame = package._new_sheet(plt, Rectangle)
                scale = SCALE if kind == "dxf" else "—"
                if kind == "cover":
                    package._cover_sheet(fig, frame, tb, index, res, verdict,
                                         dims_unit="millimetres", rules_src="Thai code (กฎกระทรวง 55, DR)",
                                         dxf_unit="1:1 mm", plot_scale="1:50")
                elif kind == "dxf":
                    package._draw_doc_on_ax(package._drawing_axes(fig), payload, ezdxf_bits)
                elif kind == "sched":
                    _sched_sheet(fig, spec)
                elif kind == "render":
                    package._render_sheet(fig, frame, payload)
                package._title_block(frame, Rectangle, tb, no, nm, scale, pi, len(sheets))
                pdf.savefig(fig); plt.close(fig)
    return folder, pdf_path


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "specs", "bedroom_suite.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    folder, pdf = build(spec, spec_path, spec["room"].get("type", "room"))
    print(f"\n=== metric deliverable: {folder} ===")
    for fn in sorted(os.listdir(folder)):
        print(f"  {fn}")
    print(f"  sheet set: {pdf if pdf else '(needs matplotlib + ezdxf)'}")
