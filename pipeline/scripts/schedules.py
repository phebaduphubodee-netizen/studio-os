"""
schedules.py — INTERIOR-AI auto-generated CD schedules (pure Python, stdlib only).

Builds the core construction-document schedules (KB §3/§5) STRAIGHT FROM THE SPEC,
so drawings and tables can never drift out of sync (the 'relational rule'):
  * DOOR schedule     — from room.door
  * FINISH schedule   — from spec["finishes"] or room-type DRAFT defaults
  * LIGHTING schedule — from the derived lighting layer (lighting.py), grouped by TYPE
  * FF&E schedule     — one row per spec item; dims model-derived, product fields DRAFT
                        until researched/verified (populate via the /ffe-research skill)

Emits a human-readable Markdown handoff (output/schedules_<type>.md) + one CSV per
schedule (importable). All finish/door/hardware values are DRAFT placeholders a
designer fills in — the schedule STRUCTURE + the model-linked counts/sizes are the
automated part.

    python pipeline/schedules.py [spec.json]
"""
import csv
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lighting

# DRAFT finish defaults by room type (floor / base / wall / ceiling). KB §3 + §5.
FINISH_DEFAULTS = {
    "living":  {"floor": "Engineered wood", "base": "Painted MDF, 4\"", "wall": "Paint, eggshell", "ceiling": "Paint, flat white"},
    "bedroom": {"floor": "Carpet", "base": "Painted MDF, 4\"", "wall": "Paint, eggshell", "ceiling": "Paint, flat white"},
    "dining":  {"floor": "Engineered wood", "base": "Painted MDF, 4\"", "wall": "Paint, eggshell", "ceiling": "Paint, flat white"},
    "kitchen": {"floor": "Porcelain tile / LVT", "base": "Tile / coved vinyl", "wall": "Paint, scrubbable + tile backsplash", "ceiling": "Paint, flat white"},
    "bathroom": {"floor": "Porcelain tile", "base": "Tile", "wall": "Tile (wet) / moisture-resistant paint", "ceiling": "Paint, mildew-resistant"},
    "office":  {"floor": "LVT / carpet tile", "base": "Painted MDF, 4\"", "wall": "Paint, eggshell", "ceiling": "Paint, flat white"},
}
FINISH_FALLBACK = {"floor": "TBD", "base": "TBD", "wall": "Paint", "ceiling": "Paint, flat white"}
_DRAFT = " (DRAFT)"


def _door_schedule(spec):
    cols = ["Tag", "Type", "Size (W x H)", "Material", "Finish", "Hardware set", "Location"]
    rows = []
    door = (spec.get("room") or {}).get("door")
    if door:
        w = float(door.get("w_in", 32))
        h = float(door.get("h_in", 80))
        rows.append([
            "D-01",
            "Interior single, swing",
            f'{w:.0f}" x {h:.0f}"',
            "Solid-core wood" + _DRAFT,
            "Paint" + _DRAFT,
            "Passage lever set" + _DRAFT,
            f'{door.get("wall", "?")} wall',
        ])
    return {"title": "DOOR SCHEDULE", "cols": cols, "rows": rows,
            "note": "Material/finish/hardware are DRAFT — designer specifies; size + location are from the model."}


def _finish_schedule(spec):
    cols = ["Room", "Floor", "Base", "Wall", "Ceiling"]
    r = spec.get("room") or {}
    rtype = r.get("type", "room")
    fin = spec.get("finishes") or FINISH_DEFAULTS.get(rtype, FINISH_FALLBACK)
    rows = [[rtype.capitalize(),
             fin.get("floor", "TBD") + _DRAFT,
             fin.get("base", "TBD") + _DRAFT,
             fin.get("wall", "TBD") + _DRAFT,
             fin.get("ceiling", "TBD") + _DRAFT]]
    return {"title": "FINISH SCHEDULE", "cols": cols, "rows": rows,
            "note": "DRAFT room-type defaults — replace with specified products + CSI Div-09 codes (KB §5)."}


def _lighting_schedule(spec, fixtures=None):
    cols = ["Tag", "Type", "Lamp (lm)", "CCT (K)", "CRI", "Mounting", "Layer", "Qty"]
    if fixtures is None:
        fixtures, _meta = lighting.plan_lighting(spec)
    type_rows, _tag_of = lighting.type_table(fixtures)
    rows = [[t["tag"], t["type"], str(t["lumens"]), str(t["cct_k"]), str(t["cri"]),
             t["mounting"], t["layer"], str(t["count"])] for t in type_rows]
    total = sum(t["count"] for t in type_rows)
    return {"title": "LIGHTING FIXTURE SCHEDULE", "cols": cols, "rows": rows,
            "note": f"{total} fixtures, {len(type_rows)} types — DRAFT auto-layout (KB §6.4); "
                    f"manufacturer/model + IES illuminance check still to be added."}


# FF&E (furnishings, CSI Division 12). One row per spec item; dimensions are
# MODEL-DERIVED (the relational rule) while product fields (mfr/model, finish,
# performance, price, lead) are DRAFT until a designer/vendor verifies them. Fields
# follow KB §5. Real-product FACTS only (specs/links) — never lift a vendor's images
# or spec prose; the placeable .skp geometry is license-gated SEPARATELY (docs/LICENSING.md).
_FFE_COLS = ["Tag", "Item", "Qty", "Manufacturer / Model", "Dimensions (W x D x H)",
             "Finish / Material", "Perf / Cert / Fire", "CSI", "Unit $", "Lead", "Notes"]


def _ffe_of(spec, item):
    """Researched FF&E record for a spec item, matched by name then kind (or {})."""
    ffe = spec.get("ffe") or {}
    return ffe.get(item.get("name")) or ffe.get(item.get("kind")) or {}


def _ffe_schedule(spec):
    rows = []
    for i, it in enumerate(spec.get("items") or [], 1):
        rec = _ffe_of(spec, it)
        draft = "" if rec.get("verified") else _DRAFT
        dims = " x ".join(f'{float(v):.0f}"' for v in (it.get("w"), it.get("d"), it.get("h"))
                          if v is not None) or "—"
        mm = " / ".join(x for x in (rec.get("manufacturer", ""), rec.get("model", "")) if x) or "TBD"
        pcf = " · ".join(x for x in (rec.get("performance", ""), rec.get("certifications", ""),
                                     rec.get("fire", "")) if x) or "TBD"
        rows.append([
            f"FF-{i:02d}",
            it.get("name", it.get("kind", "item")),
            str(rec.get("qty", it.get("qty", 1))),
            mm + draft,
            dims,                                     # model-derived — never DRAFT
            rec.get("finish", "TBD") + draft,
            pcf + draft,
            rec.get("csi", "12 --") + (draft if rec.get("csi") else ""),
            str(rec.get("unit_price", "TBD")) + draft,
            str(rec.get("lead", "TBD")) + draft,
            rec.get("notes", rec.get("link", "")),
        ])
    return {"title": "FF&E SCHEDULE (furnishings, CSI Div 12)", "cols": _FFE_COLS, "rows": rows,
            "note": "Product selections are DRAFT — designer/vendor verifies price/lead/specs + "
                    "fire/perf rating per jurisdiction before purchase (KB §5); dimensions are "
                    "model-derived (KB §3). Real-product FACTS only; placeable geometry (.skp) is "
                    "license-gated separately (docs/LICENSING.md). Populate via the /ffe-research skill."}


def build_schedules(spec, fixtures=None):
    return {"door": _door_schedule(spec),
            "finish": _finish_schedule(spec),
            "lighting": _lighting_schedule(spec, fixtures),
            "ffe": _ffe_schedule(spec)}


def _md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    if not rows:
        out.append("| " + " | ".join("—" for _ in cols) + " |")
    return "\n".join(out)


def to_markdown(scheds, spec):
    r = spec.get("room") or {}
    W, D = float(r.get("width_in", 0)), float(r.get("depth_in", 0))
    sqft = round((W * D) / 144.0) if W and D else "?"
    parts = [f"# Schedules — {r.get('type', 'room').upper()}  ({W/12:.1f}' x {D/12:.1f}', {sqft} sqft)",
             "",
             "_Auto-generated from the spec by `pipeline/schedules.py` (the relational rule, KB §3). "
             "All values marked DRAFT are placeholders for a designer; sizes/counts/locations are model-derived. "
             "Verify vs local code before any client deliverable._", ""]
    for key in ("door", "finish", "lighting", "ffe"):
        s = scheds[key]
        parts += [f"## {s['title']}", "", _md_table(s["cols"], s["rows"]), "", f"> {s['note']}", ""]
    return "\n".join(parts)


def _outdir():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(os.path.dirname(here), "output")
    os.makedirs(out, exist_ok=True)
    return out


def write(spec, outdir=None, name=None, fixtures=None):
    outdir = outdir or _outdir()
    name = name or (spec.get("room") or {}).get("type", "room")
    scheds = build_schedules(spec, fixtures)
    paths = []
    md_path = os.path.join(outdir, f"schedules_{name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(to_markdown(scheds, spec))
    paths.append(md_path)
    for key in ("door", "finish", "lighting", "ffe"):
        s = scheds[key]
        csv_path = os.path.join(outdir, f"schedule_{key}_{name}.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(s["cols"])
            w.writerows(s["rows"])
        paths.append(csv_path)
    return paths


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "specs", "living_demo.json")
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    scheds = build_schedules(spec)
    print(to_markdown(scheds, spec))
    written = write(spec)
    print("\n".join(f"  wrote: {p}" for p in written), file=sys.stderr)
