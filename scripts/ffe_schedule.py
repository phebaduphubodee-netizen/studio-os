#!/usr/bin/env python3
"""ffe_schedule.py — render an FF&E schedule (markdown) from an ffe-candidates.json.

The JSON is the SINGLE SOURCE OF TRUTH; this script regenerates the human-readable schedule
so the two can never drift (the driftless/relational rule — CLAUDE.md). Written by the
`ffe-research` skill; also consumed later by the human-triggered `bom-generate` skill (Stage 07).

Stdlib only. Metric-first (mm), currency THB by default.

Usage:
    python scripts/ffe_schedule.py projects/PRJ-2026-001_slug/03_layout/ffe-candidates.json
    python scripts/ffe_schedule.py <candidates.json> --out <schedule.md>

Schema (ffe-candidates.json):
{
  "project_id": "PRJ-2026-001",
  "currency": "THB",
  "unit_system": "mm",
  "items": [
    {
      "tag": "FFE-101",              # stable schedule tag
      "room": "Living",
      "role": "Sofa (3-seat)",
      "candidates": [
        {
          "manufacturer": "Index Living Mall", "model": "…", "qty": 1,
          "dimensions_mm": {"w": 2000, "d": 950, "h": 800, "seat_h": 450},
          "material_finish": "performance fabric, dune",
          "performance": "100k double-rub",     # fabric double-rub / tile slip / etc.
          "certifications": "", "fire": "",       # jurisdiction-specific — human verifies
          "csi": "12 52 00",                      # CSI Div 12 furnishings; finishes -> Div 09
          "unit_price_thb": 18900, "lead_time": "in stock",
          "source_th": "Index Living Mall",       # HomePro / Index / SB / IKEA-TH / import
          "link": "https://…",
          "notes": "veneer legs not solid — flag to client",
          "verified": false,                      # true ONLY after human confirms w/ vendor
          "unverified_specs": ["unit_price_thb", "lead_time"],
          "selected": true                        # the pick that feeds the layout scene-graph
        }
      ]
    }
  ]
}
"""
import argparse
import json
import sys
from pathlib import Path


def _dims(c: dict) -> str:
    d = c.get("dimensions_mm") or {}
    if not d:
        return "TBD"
    core = [str(d[k]) for k in ("w", "d", "h") if d.get(k) is not None]
    base = "×".join(core) + " mm" if core else "TBD"
    if d.get("seat_h") is not None:
        base += f" (seat {d['seat_h']})"
    return base


def _money(v) -> str:
    if v is None or v == "":
        return "TBD"
    try:
        return f"{int(round(float(v))):,}"
    except (TypeError, ValueError):
        return str(v)


def _pick(item: dict):
    """Return the selected candidate, else the sole candidate, else None."""
    cands = item.get("candidates") or []
    sel = [c for c in cands if c.get("selected")]
    if len(sel) == 1:
        return sel[0], None
    if len(sel) > 1:
        return sel[0], "MULTIPLE selected — using first; fix `selected` in JSON"
    if len(cands) == 1:
        return cands[0], "no `selected` flag — using sole candidate"
    if not cands:
        return None, "NO candidates researched yet"
    return None, f"{len(cands)} candidates, none selected — pick one (set selected:true)"


def render(data: dict) -> str:
    pid = data.get("project_id", "PRJ-????-???")
    cur = data.get("currency", "THB")
    items = data.get("items", [])

    any_unverified = False
    out = []
    out.append(f"# FF&E Schedule — {pid}")
    out.append("")
    out.append("> **DRAFT — back-office research artifact.** Every row is DRAFT until a human "
               "confirms price/lead/specs with the vendor (`verified: true`). Regenerate with "
               "`python scripts/ffe_schedule.py <this dir>/ffe-candidates.json`; edit the JSON, "
               "never this file. The client-facing BOM is produced separately by the "
               "human-triggered `bom-generate` skill (Stage 07).")
    out.append("")

    # group items by room, preserving first-seen order
    rooms: dict = {}
    for it in items:
        rooms.setdefault(it.get("room", "—"), []).append(it)

    grand_total = 0.0
    grand_known = True

    for room, room_items in rooms.items():
        out.append(f"## {room}")
        out.append("")
        out.append("| Tag | Item | Mfr / Model | Qty | Dims (mm) | Finish/Material | CSI | "
                   f"Unit ({cur}) | Ext ({cur}) | Lead | Source | Verified | Notes |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        room_total = 0.0
        room_known = True
        for it in room_items:
            tag = it.get("tag", "—")
            role = it.get("role", "—")
            cand, warn = _pick(it)
            if cand is None:
                out.append(f"| {tag} | {role} | — | — | — | — | — | — | — | — | — | ❗ | "
                           f"**{warn}** |")
                room_known = False
                continue
            qty = cand.get("qty", 1)
            unit = cand.get("unit_price_thb")
            ext = None
            try:
                ext = float(unit) * float(qty)
                room_total += ext
            except (TypeError, ValueError):
                room_known = False
            verified = cand.get("verified", False)
            if not verified:
                any_unverified = True
            vmark = "✅" if verified else "DRAFT"
            mfr = " / ".join(x for x in (cand.get("manufacturer"), cand.get("model")) if x) or "TBD"
            notes = cand.get("notes", "") or ""
            unv = cand.get("unverified_specs") or []
            if unv:
                notes = (notes + " " if notes else "") + f"⚠ unverified: {', '.join(unv)}"
            if warn:
                notes = (notes + " " if notes else "") + f"⚠ {warn}"
            src = cand.get("source_th", cand.get("link", "TBD")) or "TBD"
            out.append(
                f"| {tag} | {role} | {mfr} | {qty} | {_dims(cand)} | "
                f"{cand.get('material_finish','TBD')} | {cand.get('csi','—')} | "
                f"{_money(unit)} | {_money(ext)} | {cand.get('lead_time','TBD')} | "
                f"{src} | {vmark} | {notes.strip() or '—'} |"
            )
        subtotal = f"{cur} {_money(room_total)}" + ("" if room_known else " + TBD items")
        out.append("")
        out.append(f"**{room} subtotal (selected picks):** {subtotal}")
        out.append("")
        grand_total += room_total
        grand_known = grand_known and room_known

    out.append("---")
    gt = f"{cur} {_money(grand_total)}" + ("" if grand_known else " + TBD items")
    out.append(f"**Estimated total (selected picks, DRAFT):** {gt}")
    out.append("")
    out.append("_Legend:_ **DRAFT** = specs not vendor-confirmed · ✅ = human-verified · "
               "❗ = no pick yet · CSI Div 12 = furnishings, Div 09 = finishes.")
    if any_unverified:
        out.append("")
        out.append("> ⚠ This schedule contains unverified specs. Do NOT present figures to a client "
                   "until the designer confirms them (DR-002 human-QA gate).")

    recon = data.get("layout_reconciliation") or []
    if recon:
        out.append("")
        out.append("## ⚠ Layout reconciliation — selected pick vs drawn footprint")
        out.append("")
        out.append("A selected product exceeds the layout footprint the scene-graph drew (the "
                   "ffe-research ±15% rule). Resolve before these dims flow into Stage-03 drawings.")
        out.append("")
        out.append("| Tag | Fit issue | Designer action |")
        out.append("|---|---|---|")
        for r in recon:
            out.append(f"| {r.get('tag','—')} | {r.get('issue','')} | {r.get('action','')} |")

    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Render an FF&E schedule from ffe-candidates.json")
    ap.add_argument("candidates", help="path to ffe-candidates.json")
    ap.add_argument("--out", default=None, help="output .md path (default: ffe-schedule.md beside input)")
    args = ap.parse_args()

    src = Path(args.candidates)
    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return 1
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {src}: {e}", file=sys.stderr)
        return 1

    md = render(data)
    out = Path(args.out) if args.out else src.with_name("ffe-schedule.md")
    out.write_text(md, encoding="utf-8")
    n = len(data.get("items", []))
    print(f"Wrote {out}  ({n} item{'s' if n != 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
