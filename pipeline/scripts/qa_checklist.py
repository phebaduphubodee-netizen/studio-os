"""
qa_checklist.py — INTERIOR-AI per-deliverable QA sign-off (the review GATE).

The friend/designer verifies THIS before any client sees the package. It is
SPEC-DERIVED, not a generic template: it lists the actual room + furniture
dimensions to confirm against the brief, every clearance WARN/FAIL the engine
flagged (so nothing hides), the DRAFT placeholders to replace, and the furniture
provenance/licensing questions (docs/LICENSING.md). Her sign-off converts a DRAFT
into a client-ready deliverable — that human gate is non-negotiable (BUILD-PLAN.md:
"Final spatial/scale QA by a human is NON-NEGOTIABLE on every deliverable").

    python pipeline/qa_checklist.py [spec.json]

Pure stdlib + clearance_check (no ezdxf / no Blender), so it always runs.
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clearance_check
import lighting


def _clearance_results(spec, fixtures=None):
    """Run the engine on the spec and return (results, verdict). Same logic as
    clearance_check.report but returns the structured list instead of printing."""
    r = spec["room"]
    room = clearance_check.Room(r["width_in"], r["depth_in"], r["ceiling_in"], door=r.get("door"))
    items = [clearance_check.Item(it.get("name", it.get("kind", "item")), it.get("kind", "item"),
                                  it["x"], it["y"], it["w"], it["d"])
             for it in spec.get("items", [])]
    res = clearance_check.check(room, items) + list(clearance_check.check_lighting(spec, fixtures))
    fails = sum(x["status"] == "FAIL" for x in res)
    warns = sum(x["status"] == "WARN" for x in res)
    verdict = "FAIL" if fails else ("REVIEW" if warns else "PASS")
    return res, verdict


def _dim_rows(spec):
    """One confirm-line per real dimension the designer checks against the brief."""
    r = spec["room"]
    W, D, H = float(r["width_in"]), float(r["depth_in"]), float(r["ceiling_in"])
    rows = [f"- [ ] Room **{r.get('type','room')}**: {W:.0f}\" x {D:.0f}\" "
            f"({W/12:.1f}' x {D/12:.1f}', ceiling {H:.0f}\"/{H/12:.1f}') — matches the brief?"]
    door = r.get("door")
    if door:
        rows.append(f"- [ ] Door: {float(door.get('w_in',32)):.0f}\" x {float(door.get('h_in',80)):.0f}\" "
                    f"on the {door.get('wall','?')} wall — right size/side?")
    for it in spec.get("items", []):
        nm = it.get("name") or it.get("kind") or "item"
        rows.append(f"- [ ] {nm}: {float(it['w']):.0f}\"W x {float(it['d']):.0f}\"D x "
                    f"{float(it.get('h',0)):.0f}\"H — real product size? placed correctly?")
    return rows


def build_markdown(spec, spec_path=None, fixtures=None):
    r = spec["room"]
    rtype = r.get("type", "room")
    W, D = float(r["width_in"]), float(r["depth_in"])
    sqft = round((W * D) / 144.0)
    if fixtures is None:
        fixtures, _ = lighting.plan_lighting(spec)
    res, verdict = _clearance_results(spec, fixtures)
    warns = [x for x in res if x["status"] == "WARN"]
    fails = [x for x in res if x["status"] == "FAIL"]

    P = []
    P.append(f"# QA CHECKLIST — {rtype.upper()}  ({W/12:.1f}' x {D/12:.1f}', {sqft} sqft)")
    P.append("")
    P.append(f"**Engine verdict: `{verdict}`**  ({len(fails)} FAIL · {len(warns)} WARN · DRAFT).  "
             "Sign the bottom **before any client sees this package.** The AI produced a "
             "dimensionally-checked DRAFT; a designer owns final spatial/scale/code judgment "
             "(BUILD-PLAN.md). Rules are Panero & Zelnik DRAFT — verify vs local (Thai) code.")
    if spec_path:
        P.append("")
        P.append(f"_Spec: `{os.path.basename(spec_path)}`_")
    P.append("")

    P.append("## 1 · Dimensions match the brief")
    P += _dim_rows(spec)
    P.append("")

    P.append("## 2 · Clearances & code (engine flags — resolve each)")
    if fails:
        P.append("**FAIL (must fix — a FAIL blocks the build):**")
        for x in fails:
            P.append(f"- [ ] ❌ {x['check']}: {x['detail']}")
    if warns:
        P.append("**WARN (review — usually a real conflict, sometimes OK):**")
        for x in warns:
            P.append(f"- [ ] ⚠️ {x['check']}: {x['detail']}")
    if not fails and not warns:
        P.append("- [x] No geometry FAIL/WARN raised by the engine (still confirm vs local code).")
    P.append("- [ ] Thai statutory floors in `dimensional_rules.v0.2.json` current vs `knowledge/codes-th/` (Authority); ergonomic values still DRAFT vs Panero & Zelnik.")
    P.append("")

    P.append("## 3 · Lighting (auto-layout DRAFT — KB §6)")
    trows, _ = lighting.type_table(fixtures)
    total = sum(t["count"] for t in trows)
    P.append(f"- [ ] {total} fixtures / {len(trows)} types auto-placed — count + positions sensible for the space?")
    P.append("- [ ] Illuminance / CCT / CRI vs the REAL fixtures the client will buy (draft photometrics used).")
    P.append("")

    P.append("## 4 · Finishes & schedules (DRAFT placeholders → real products)")
    P.append("- [ ] Finish schedule: replace DRAFT room-type defaults with specified products + CSI Div-09 codes.")
    P.append("- [ ] Door schedule: material / finish / hardware set specified.")
    P.append("- [ ] Schedules agree with the drawings (they are model-derived, but confirm nothing was hand-edited apart).")
    P.append("")

    P.append("## 5 · Furniture provenance & LICENSING (docs/LICENSING.md — do NOT skip)")
    P.append("For **every** placed furniture component, confirm the source is **client-deliverable-OK**:")
    P.append("- ✅ OK to ship: self-modeled · 3D Warehouse · FurniMesh · CC0")
    P.append("- ❌ personal-use ONLY (cannot ship to a client): BIMobject · Häfele (via BIMobject/PARTcommunity) · CADENAS")
    items = [it for it in spec.get("items", []) if it.get("kind") != "rug"]
    for it in items:
        nm = it.get("name") or it.get("kind") or "item"
        P.append(f"- [ ] {nm}: source = ____________  (box primitive = OK; a shared `.skp` keeps its ORIGINAL licence).")
    P.append("- [ ] Ship the **assembled room scene only** — never a standalone model or the raw catalog.")
    P.append("")

    P.append("## 6 · Editable SketchUp model")
    P.append("- [ ] `build_room.rb` opened in the friend's licensed SketchUp (one `load` line — see README / FOR-FRIEND.md).")
    P.append("- [ ] Model is native + editable (real Faces/Groups), dimensions match this checklist, no red console errors.")
    P.append("")

    P.append("## 7 · Anything the AI got wrong")
    P.append("- [ ] LAYOUT is an auto DRAFT — is the arrangement actually good design, not just legal clearance?")
    P.append("- [ ] Labels/names correct; scale reads 1/4\"=1'-0\" on the sheets; nothing mislabeled.")
    P.append("- [ ] Free-form notes: ______________________________________________")
    P.append("")

    P.append("## SIGN-OFF")
    P.append("- Reviewed by: __________________   Date: ____________")
    P.append("- [ ] **APPROVED for client** — dimensions, clearances, licensing, and finishes verified.")
    P.append("")
    P.append("_Generated by `pipeline/qa_checklist.py` from the validated spec._")
    return "\n".join(P)


def write(spec, outdir, name=None, spec_path=None, fixtures=None):
    name = name or (spec.get("room") or {}).get("type", "room")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "QA-CHECKLIST.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_markdown(spec, spec_path=spec_path, fixtures=fixtures))
    return path


if __name__ == "__main__":
    spec_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "living_demo.json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    print(build_markdown(spec, spec_path=spec_path))
