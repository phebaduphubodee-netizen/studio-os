"""
package.py — INTERIOR-AI deliverable ASSEMBLER (loose files -> one reviewable set).

Turns the per-generator outputs (floor plan, RCP, 4 elevations, schedules, preview
render) into ONE package a designer/client can actually open, check, and refine:

    output/deliverable_<name>/
      <name>_SHEETSET.pdf     # cover -> plan -> RCP -> elevations -> schedules -> render
      plan_<name>.dxf         # editable CAD masters (regenerated here, self-contained)
      rcp_<name>.dxf
      elev_<name>_<wall>.dxf  (x4: south/north/west/east)
      schedules_<name>.md + schedule_{door,finish,lighting,ffe}_<name>.csv
      room_<name>.png         # preview render — ONLY when freshly rendered (make_all --render)
      <name>.spec.json        # the exact validated spec that produced everything
      build_room.rb           # native-SketchUp generator (the editable-model route)
      QA-CHECKLIST.md         # the sign-off gate (qa_checklist.py)
      README.md               # what each file is + the one-line SketchUp load step

The multi-page PDF is built with matplotlib (already a dependency via
plan_2d.export_preview) — NO new packages. Every sheet carries the SAME title block
(project / room / sheet no / scale / date / DRAFT status), so the output reads as one
construction-document set instead of 8 disconnected files.

Every drawing is rendered from the SAME validated spec and the SAME derived lighting
layer (fixtures passed through), so the sheet set can never drift from the schedules or
the clearance verdict (the relational rule, KB §3).

⚠️ SCALE HONESTY: the PDF sheets are fit-to-page previews — NOT plotted to a fixed
architectural scale — so they are marked NTS and the FIGURED DIMENSIONS govern. The DXF
masters are authored 1:1 in real inches; open a DXF in CAD and plot at 1/4"=1'-0" for a
truly-scaled print. (Claiming a fixed plot scale on an auto-fitted preview would be a lie.)

    python pipeline/package.py [spec.json]

Requires ezdxf (a hard dependency of the whole pipeline — plan_2d/rcp/elevations all need
it). The SHEETSET.pdf additionally needs matplotlib; if matplotlib is absent, the folder +
DXF masters + schedules + spec + QA checklist still assemble and only the PDF is skipped.
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
import clearance_check
import lighting
import plan_2d
import rcp
import schedules
import qa_checklist

try:
    import elevations
    _HAVE_ELEV = True
except Exception:
    _HAVE_ELEV = False

PROJECT = "INTERIOR-AI"
# The PDF is a fit-to-page preview, so its drawing sheets are NTS and the figured
# dimensions govern. The DXF masters are 1:1 real inches -> plot at DXF_PLOT_SCALE in CAD.
SHEET_SCALE = "NTS — dims govern"
DXF_PLOT_SCALE = "1/4\" = 1'-0\""


# --------------------------------------------------------------------------- PDF
# The matplotlib + ezdxf sheet machinery is optional; guard the import so the rest
# of the package (folder, DXFs handled separately, schedules, QA) still assembles.
def _pdf_backend():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        # Thai-capable font so Thai in matplotlib text (schedule tables, cover flag list)
        # doesn't render as tofu boxes; Tahoma/Leelawadee ship on Windows and cover Latin too.
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = ["Tahoma", "Leelawadee UI", "TH Sarabun New", "DejaVu Sans"]
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.patches import Rectangle
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        from ezdxf.addons.drawing.properties import LayoutProperties
        return plt, PdfPages, Rectangle, (RenderContext, Frontend, MatplotlibBackend, LayoutProperties)
    except Exception:
        return None


def _draw_doc_on_ax(ax, doc, ezdxf_bits):
    """Render an ezdxf modelspace onto a given matplotlib Axes on a WHITE sheet.

    ezdxf/AutoCAD modelspace defaults to a BLACK background, which flips ACI color 7
    (the WALLS / TEXT / dimension layers) to white — invisible on a white drawing sheet.
    Force a white background so color-7 linework renders black, like a real plotted sheet."""
    RenderContext, Frontend, MatplotlibBackend, LayoutProperties = ezdxf_bits
    lp = LayoutProperties.from_layout(doc.modelspace())
    lp.set_colors("#FFFFFF")   # white bg -> foreground (color 7) becomes black
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(
        doc.modelspace(), finalize=True, layout_properties=lp)
    ax.set_axis_off()


def _title_block(frame, Rectangle, tb, sheet_no, sheet_name, scale, page_i, page_n):
    """Consistent bottom-right title block on every sheet (fig-fraction coords 0..1)."""
    x0, y0, x1, y1 = 0.545, 0.028, 0.972, 0.150
    frame.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=1.0, zorder=5))
    rows = [
        ("PROJECT", tb["project"]),
        ("ROOM", tb["room"]),
        ("SHEET", f"{sheet_no}    {sheet_name}"),
        ("SCALE", scale),
        ("DATE / STATUS", f"{tb['date']}    {tb['status']}"),
    ]
    n = len(rows)
    for i, (label, val) in enumerate(rows):
        ry = y1 - (i + 0.5) * (y1 - y0) / n
        frame.text(x0 + 0.010, ry, label, fontsize=5.5, va="center", ha="left",
                   color="0.35", family="monospace", zorder=6)
        frame.text(x0 + 0.140, ry, str(val), fontsize=7.5, va="center", ha="left",
                   fontweight="bold", zorder=6)
    frame.text(x1 - 0.008, y0 + 0.008, f"{page_i}/{page_n}", fontsize=6,
               va="bottom", ha="right", color="0.4", zorder=6)


def _new_sheet(plt, Rectangle):
    fig = plt.figure(figsize=(11, 8.5))          # landscape US-letter
    frame = fig.add_axes([0, 0, 1, 1]); frame.set_axis_off()
    frame.set_xlim(0, 1); frame.set_ylim(0, 1)
    frame.add_patch(Rectangle((0.02, 0.02), 0.96, 0.96, fill=False, lw=1.3, zorder=5))
    return fig, frame


def _drawing_axes(fig):
    """Drawing region above the title-block strip; transparent so the border shows."""
    ax = fig.add_axes([0.045, 0.17, 0.91, 0.78])
    ax.patch.set_alpha(0.0)
    return ax


def _cover_sheet(fig, frame, tb, index, res, verdict,
                 dims_unit="inches", rules_src="Panero & Zelnik",
                 dxf_unit="1:1 real inches", plot_scale=None):
    plot_scale = plot_scale or DXF_PLOT_SCALE
    frame.text(0.06, 0.90, PROJECT, fontsize=15, fontweight="bold")
    frame.text(0.06, 0.855, "CONSTRUCTION-DOCUMENT SET (DRAFT)", fontsize=10, color="0.3")
    frame.text(0.06, 0.79, tb["room"], fontsize=20, fontweight="bold")
    frame.text(0.06, 0.75, f"Date {tb['date']}   ·   dimensions in {dims_unit}   ·   PDF is a fit-to-page review set (NTS)",
               fontsize=9, color="0.3")

    # sheet index — adaptive row pitch so a long set (plan+RCP+N elevations+schedules+
    # render) always ends ABOVE the disclaimer block at y=0.34 (never overlaps it).
    frame.text(0.06, 0.66, "SHEET INDEX", fontsize=10, fontweight="bold")
    iy = 0.62
    pitch = min(0.035, (0.62 - 0.40) / max(1, len(index)))
    fs = 9 if pitch >= 0.030 else 8
    for no, nm in index:
        frame.text(0.08, iy, no, fontsize=fs, family="monospace")
        frame.text(0.20, iy, nm, fontsize=fs)
        iy -= pitch

    # clearance summary (so the reviewer sees status at a glance)
    fails = [x for x in res if x["status"] == "FAIL"]
    warns = [x for x in res if x["status"] == "WARN"]
    frame.text(0.58, 0.66, f"DIMENSIONAL CHECK:  {verdict}", fontsize=11, fontweight="bold",
               color=("#b00020" if verdict == "FAIL" else ("#8a6d00" if verdict == "REVIEW" else "#1b5e20")))
    frame.text(0.58, 0.625, f"{len(fails)} FAIL · {len(warns)} WARN", fontsize=9, color="0.3")
    ly = 0.585
    for x in (fails + warns)[:10]:
        mark = "XX" if x["status"] == "FAIL" else "!!"
        # not monospace: check names can contain Thai, and DejaVu Sans Mono has no Thai glyphs
        frame.text(0.58, ly, f"[{mark}] {x['check']}", fontsize=7.5)
        ly -= 0.028
    if len(fails + warns) > 10:
        frame.text(0.58, ly, f"... +{len(fails+warns)-10} more (see QA-CHECKLIST.md)", fontsize=7.5, color="0.4")

    # Kept left of the title block (x<0.53) and above it (y>0.15) with explicit line
    # breaks so it never overruns into the title-block box.
    frame.text(0.06, 0.34,
               "DRAFT — dimensionally-checked by the pipeline;\n"
               "a designer signs off spatial / scale / code before\n"
               "client use (see QA-CHECKLIST.md). Clearance rules are\n"
               f"{rules_src} DRAFT — verify vs local (Thai) code.",
               fontsize=8.5, color="0.3", va="top", ha="left", linespacing=1.5)
    frame.text(0.06, 0.20,
               f"SCALE — these PDF sheets are fit-to-page (NTS): use the FIGURED\n"
               f"DIMENSIONS, do not scale off the print. For a scaled plot, open a\n"
               f"DXF master ({dxf_unit}) in CAD and plot at {plot_scale}.",
               fontsize=8, color="0.35", va="top", ha="left", linespacing=1.5)


def _schedules_sheet(fig, spec, name, fixtures):
    scheds = schedules.build_schedules(spec, fixtures)
    order = ("door", "finish", "lighting")
    # three stacked table regions between the title strip and the top margin
    tops = (0.90, 0.66, 0.42)
    CAP = 8   # data rows that fit a fixed region; beyond this we show a POINTER row, never
              # silently drop rows — the full schedule always lives in the .md + per-key CSV.
    for key, top in zip(order, tops):
        s = scheds[key]
        ax = fig.add_axes([0.05, top - 0.20, 0.90, 0.19]); ax.set_axis_off()
        ax.text(0, 1.02, s["title"], fontsize=10, fontweight="bold", transform=ax.transAxes)
        allrows = s["rows"] or [["—"] * len(s["cols"])]
        truncated = len(allrows) > CAP
        if truncated:
            hidden = len(allrows) - (CAP - 1)
            rows = allrows[:CAP - 1] + [[f"… +{hidden} more rows"] + [""] * (len(s["cols"]) - 1)]
        else:
            rows = allrows
        tab = ax.table(cellText=rows, colLabels=s["cols"], loc="upper center", cellLoc="left")
        tab.auto_set_font_size(False)
        tab.set_fontsize(7.5 if len(rows) <= 6 else 6.3)
        tab.scale(1, 1.35 if len(rows) <= 6 else 1.12)
        for (rr, _cc), cell in tab.get_celld().items():
            cell.set_linewidth(0.4)
            if rr == 0:
                cell.set_text_props(fontweight="bold"); cell.set_facecolor("0.92")
        note = s["note"] + (f"  — PREVIEW truncated to fit; ALL rows in schedule_{key}_{name}.csv" if truncated else "")
        ax.text(0, -0.02, note, fontsize=6.5, color="0.4", va="top", transform=ax.transAxes)
    fig.text(0.05, 0.163, f"Complete schedules (every row) — schedules_{name}.md + schedule_*_{name}.csv (authoritative).",
             fontsize=6.5, color="0.4")


def _ffe_sheet(fig, spec, name):
    """Dedicated full-width page for the FF&E schedule — 11 wide columns and the single most
    client-actionable table (what to buy). One row per spec item; product fields are DRAFT until
    researched/verified (populate via the /ffe-research skill). Full rows in schedule_ffe_<name>.csv."""
    s = schedules._ffe_schedule(spec)
    ax = fig.add_axes([0.04, 0.10, 0.92, 0.78]); ax.set_axis_off()
    ax.text(0, 1.01, s["title"], fontsize=11, fontweight="bold", transform=ax.transAxes)
    allrows = s["rows"] or [["—"] * len(s["cols"])]
    CAP = 18   # rows that fit a full page; beyond this show a POINTER row, never silently drop.
    truncated = len(allrows) > CAP
    if truncated:
        hidden = len(allrows) - (CAP - 1)
        rows = allrows[:CAP - 1] + [[f"… +{hidden} more rows"] + [""] * (len(s["cols"]) - 1)]
    else:
        rows = allrows
    tab = ax.table(cellText=rows, colLabels=s["cols"], loc="upper center", cellLoc="left")
    tab.auto_set_font_size(False)
    tab.set_fontsize(6.0)
    tab.scale(1, 1.25)
    for (rr, _cc), cell in tab.get_celld().items():
        cell.set_linewidth(0.4)
        if rr == 0:
            cell.set_text_props(fontweight="bold"); cell.set_facecolor("0.92")
    note = s["note"] + (f"  — PREVIEW truncated; ALL rows in schedule_ffe_{name}.csv" if truncated else "")
    ax.text(0, -0.03, note, fontsize=6.5, color="0.4", va="top", transform=ax.transAxes, wrap=True)


def _render_sheet(fig, frame, render_png):
    if render_png and os.path.exists(render_png):
        ax = _drawing_axes(fig); ax.set_axis_off()
        try:
            import matplotlib.pyplot as plt
            ax.imshow(plt.imread(render_png)); ax.set_aspect("equal")
            return True
        except Exception:
            pass
    frame.text(0.5, 0.55, "PREVIEW RENDER PENDING", fontsize=16, fontweight="bold",
               ha="center", color="0.5")
    frame.text(0.5, 0.50, "Run  make_all --render  (Blender) to embed the Cycles preview here.",
               fontsize=9, ha="center", color="0.5")
    return False


def _build_pdf(spec, name, tb, fixtures, res, verdict, render_png, pdf_path):
    backend = _pdf_backend()
    if backend is None:
        return None
    plt, PdfPages, Rectangle, ezdxf_bits = backend

    # Assemble the drawing docs (reuse the existing builders unchanged).
    plan_doc = plan_2d.build_dxf(spec)
    rcp_doc, _fx, _tr = rcp.build_dxf(spec, fixtures)
    elev_docs = elevations.build_all(spec) if _HAVE_ELEV else []

    # Sheet list -> (sheet_no, sheet_name, kind, payload)
    sheets = [("G-000", "COVER / SHEET INDEX", "cover", None),
              ("A-101", "FLOOR PLAN", "dxf", plan_doc),
              ("A-102", "REFLECTED CEILING PLAN", "dxf", rcp_doc)]
    for i, (wall, edoc) in enumerate(elev_docs):
        sheets.append((f"A-20{i+1}", f"INTERIOR ELEVATION — {wall.upper()}", "dxf", edoc))
    sheets.append(("A-601", "SCHEDULES (DOOR / FINISH / LIGHTING)", "sched", None))
    sheets.append(("A-602", "FF&E SCHEDULE (FURNISHINGS)", "ffe", None))
    sheets.append(("A-701", "PREVIEW RENDER", "render", None))

    index = [(no, nm) for (no, nm, _k, _p) in sheets]
    page_n = len(sheets)

    with PdfPages(pdf_path) as pdf:
        for page_i, (no, nm, kind, payload) in enumerate(sheets, start=1):
            fig, frame = _new_sheet(plt, Rectangle)
            scale = SHEET_SCALE if kind == "dxf" else "—"
            if kind == "cover":
                _cover_sheet(fig, frame, tb, index, res, verdict)
            elif kind == "dxf":
                _draw_doc_on_ax(_drawing_axes(fig), payload, ezdxf_bits)
            elif kind == "sched":
                _schedules_sheet(fig, spec, name, fixtures)
            elif kind == "ffe":
                _ffe_sheet(fig, spec, name)
            elif kind == "render":
                _render_sheet(fig, frame, render_png)
            _title_block(frame, Rectangle, tb, no, nm, scale, page_i, page_n)
            pdf.savefig(fig)
            plt.close(fig)
    return pdf_path


# ---------------------------------------------------------------------- assemble
def _readme(name, tb, has_pdf, has_render, n_elev):
    L = [f"# {PROJECT} deliverable — {tb['room']}", "",
         f"Assembled {tb['date']}. **DRAFT** — a designer signs off `QA-CHECKLIST.md` before any client use.", ""]
    L.append("## Contents")
    elev_seg = f" · {n_elev} elevations" if n_elev else ""
    if has_pdf:
        L.append(f"- `{name}_SHEETSET.pdf` — the drawing set (cover · floor plan · RCP{elev_seg} · schedules · render). "
                 f"Fit-to-page preview (NTS) — dimensions govern; plot the DXF masters for a scaled print.")
    dxf_line = f"- `plan_{name}.dxf`, `rcp_{name}.dxf`"
    dxf_line += (f", `elev_{name}_*.dxf`" if n_elev else "") + " — editable CAD masters, 1:1 real inches (open in any DXF app)."
    L.append(dxf_line)
    L.append(f"- `schedules_{name}.md` + `schedule_*.csv` — door / finish / lighting / FF&E schedules.")
    if has_render:
        L.append(f"- `room_{name}.png` — Cycles preview render.")
    L.append(f"- `{name}.spec.json` — the exact validated spec everything was generated from.")
    L.append("- `build_room.rb` — builds the **native, editable** model inside SketchUp Pro.")
    L.append("- `QA-CHECKLIST.md` — the sign-off gate (verify before the client sees this).")
    L.append("")
    L.append("## Open the editable SketchUp model (~1 min)")
    L.append("In SketchUp Pro → **Window ▸ Ruby Console**, paste (use `/` not `\\`):")
    L.append("```ruby")
    L.append(f"$INTERIOR_SPEC = 'C:/path/to/{name}.spec.json'")
    L.append("load 'C:/path/to/build_room.rb'")
    L.append("```")
    L.append("Full walkthrough: `docs/FOR-FRIEND.md`.")
    return "\n".join(L)


def _validate_spec(spec):
    """Fail LOUDLY and EARLY on a malformed spec — before writing any file. We never
    silently default a missing geometry key: a 0-width item would ship a wrong drawing,
    which is exactly the illusion this project must not produce. Mirrors the
    room-spec@0.1 contract the rest of the pipeline already assumes."""
    r = spec.get("room")
    if not isinstance(r, dict):
        raise ValueError("bad spec: 'room' is missing or not an object")
    for k in ("width_in", "depth_in", "ceiling_in"):
        if k not in r:
            raise ValueError(f"bad spec: room is missing required key '{k}'")
    for i, it in enumerate(spec.get("items", [])):
        miss = [k for k in ("x", "y", "w", "d") if k not in it]
        if miss:
            nm = it.get("name") or it.get("kind") or f"#{i}"
            raise ValueError(f"bad spec: item '{nm}' missing {miss} (room-spec@0.1 needs x/y/w/d per item)")


def build(spec, spec_path, name=None, fixtures=None, outdir=None, render_png=False, date=None):
    """Assemble the full deliverable folder. Returns (folder, pdf_path_or_None).

    Self-contained: regenerates the DXFs + schedules into the folder, so it works
    standalone (not only inside make_all). Pass `fixtures` to reuse make_all's derived
    lighting layer (keeps every artifact on the same fixtures — the relational rule)."""
    _validate_spec(spec)   # clear early error instead of a deep KeyError mid-assembly
    name = name or (spec.get("room") or {}).get("type", "room")
    base_out = outdir or plan_2d._outdir()
    folder = os.path.join(base_out, f"deliverable_{name}")
    os.makedirs(folder, exist_ok=True)

    if fixtures is None:
        fixtures, _ = lighting.plan_lighting(spec)
    if date is None:
        date = datetime.date.today().isoformat()

    r = spec["room"]
    W, D = float(r["width_in"]), float(r["depth_in"])
    tb = {"project": PROJECT,
          "room": f"{r.get('type','room').upper()}  {W/12:.1f}' x {D/12:.1f}'  ({round(W*D/144.0)} sqft)",
          "date": date, "status": "DRAFT"}

    produced = []

    # 1) the exact spec (provenance — everything derives from this one artifact)
    spec_copy = os.path.join(folder, f"{name}.spec.json")
    with open(spec_copy, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    produced.append(spec_copy)

    # 2) editable CAD masters (regenerate here so the folder stands alone)
    try:
        plan_2d.build_dxf(spec).saveas(os.path.join(folder, f"plan_{name}.dxf"))
        rcp.build_dxf(spec, fixtures)[0].saveas(os.path.join(folder, f"rcp_{name}.dxf"))
        if _HAVE_ELEV:
            for wall, edoc in elevations.build_all(spec):
                edoc.saveas(os.path.join(folder, f"elev_{name}_{wall}.dxf"))
        produced.append(f"DXF masters (plan + rcp + {'4 elevations' if _HAVE_ELEV else 'no elevations: ezdxf?'})")
    except Exception as e:
        produced.append(f"(!) DXF masters skipped: {e}")

    # 3) schedules (md + csv), on the SAME fixtures
    for p in schedules.write(spec, folder, name, fixtures):
        produced.append(p)

    # 4) native-SketchUp generator (the editable-model route)
    rb_src = os.path.join(HERE, "build_room.rb")
    if os.path.exists(rb_src):
        shutil.copy2(rb_src, os.path.join(folder, "build_room.rb"))
        produced.append(os.path.join(folder, "build_room.rb"))

    # 5) preview render — copy in ONLY a render that matches this spec. render_png:
    #    False (DEFAULT) -> never embed. A render belongs in the package only when produced
    #             from THIS spec THIS run, so we never auto-grab a stray output/room_*.png that
    #             might be a DIFFERENT layout (the illusion guard). Get one via `make_all --render`.
    #    path  -> use that file if it exists (make_all passes the fresh render here)
    #    None  -> opt-in convenience: auto-look for output/room_<name>.png (may mismatch; caller's risk)
    #    ⚠️ Do NOT change the build() default to None — that re-enables the stale-render footgun.
    if render_png is False:
        render_candidate = None
    elif render_png is None:
        render_candidate = os.path.join(base_out, f"room_{name}.png")
    else:
        render_candidate = render_png
    has_render = bool(render_candidate) and os.path.exists(render_candidate)
    dest_png = os.path.join(folder, f"room_{name}.png")
    if has_render:
        shutil.copy2(render_candidate, dest_png)
        produced.append(dest_png)
    elif os.path.exists(dest_png):
        os.remove(dest_png)   # don't let a stale render from a prior run linger in the folder

    # 6) QA checklist (the sign-off gate) — same fixtures/spec
    qa_path = qa_checklist.write(spec, folder, name, spec_path=spec_path, fixtures=fixtures)
    produced.append(qa_path)

    # 7) the sheet-set PDF (needs matplotlib + ezdxf)
    r_room = clearance_check.Room(r["width_in"], r["depth_in"], r["ceiling_in"], door=r.get("door"))
    r_items = [clearance_check.Item(it.get("name", it.get("kind", "item")), it.get("kind", "item"),
                                    it["x"], it["y"], it["w"], it["d"]) for it in spec.get("items", [])]
    res = clearance_check.check(r_room, r_items) + list(clearance_check.check_lighting(spec, fixtures))
    fails = sum(x["status"] == "FAIL" for x in res)
    warns = sum(x["status"] == "WARN" for x in res)
    verdict = "FAIL" if fails else ("REVIEW" if warns else "PASS")
    pdf_path = os.path.join(folder, f"{name}_SHEETSET.pdf")
    pdf = _build_pdf(spec, name, tb, fixtures, res, verdict,
                     render_candidate if has_render else None, pdf_path)
    if pdf:
        produced.append(pdf)
    else:
        produced.append("(!) SHEETSET.pdf skipped — needs matplotlib + ezdxf (pip install matplotlib ezdxf)")

    # 8) README
    readme = os.path.join(folder, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write(_readme(name, tb, has_pdf=bool(pdf), has_render=has_render,
                        n_elev=(4 if _HAVE_ELEV else 0)))
    produced.append(readme)

    return folder, pdf


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "specs", "living_demo.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    name = spec["room"].get("type", "room")
    folder, pdf = build(spec, spec_path, name)
    print(f"\n=== deliverable assembled: {folder} ===")
    for fn in sorted(os.listdir(folder)):
        print(f"  {fn}")
    print(f"\n  sheet set: {pdf if pdf else '(PDF skipped — install matplotlib + ezdxf)'}")
    print("  (DRAFT — sign QA-CHECKLIST.md before any client use)")
