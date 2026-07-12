#!/usr/bin/env python3
"""rationale.py — PER-ELEMENT design-rationale (explainability) layer.

For every element in a room-spec, emit a cited answer to "why is this here / why THIS
placement / why THIS size / why THIS material". HONESTY-FIRST: every line traces to a
REAL source (a spec field, a FUNCTION rule result, a clearance/codes-th cite, an
ergonomics_ref constant). A choice that is actually a HARDCODED renderer default (all
materials/patterns today, per build_room.py + material_defaults.py) is labelled as such
IN WORDS — never dressed up as a design reason. An axis no rule constrains is marked
spec-authored, never silently "grounded". This is the explainability half of the
FUNCTION layer: an element must be not just CORRECT (placement_logic) but JUSTIFIABLE.

Reuses the deterministic emitters already in the pipeline (invents no reasons):
  - placement_logic.check(spec)  -> FUNCTION findings (GS-xx, ergonomic bands)
  - suite_clearance.check(spec)  -> statutory/ergonomic clearance rows (codes-th)
  - ergonomics_ref               -> the cited comfort constants
  - material_defaults            -> what build_room actually renders (shared, drift-guarded)
Findings carry no element id, so we RE-DERIVE attribution with the same finders
(find_bed/find_tv/...) + keyword-map the clearance rows. No sentence is invented; a
rule's own detail IS the "why".

    python pipeline/scripts/rationale.py [spec.json]   # prints RATIONALE.md to stdout
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                     # standalone run; suite_package already does this
    sys.path.insert(0, HERE)

import placement_logic as PL
import suite_clearance as SC
import ergonomics_ref as ergo
import material_defaults as matdef
import activity_taxonomy as AT
import persona as PER          # persona-driven PRESENCE axis (optional; None-safe)


def _repo_root():
    # pipeline/scripts -> pipeline -> repo root
    return os.path.dirname(os.path.dirname(HERE))


# ---------------------------------------------------------------- cites (canon)
# Format matches dimensional_rules.v0.2.json: "<clause> — <knowledge path> (tier)".
# Statutory cites travel INSIDE the clearance detail already; we reuse those verbatim.
C_GS = "docs/functional-correctness-layer.md (designer M3.2 review, GS-xx)"
C_BED = ("Panero & Zelnik standard mattress — "
         "knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md (REFERENCE tier; codes-th outranks)")
C_WARD = ("Neufert hanging-depth 450–650 — "
          "knowledge/ergonomics/residential-clearances.md (REFERENCE tier)")
C_TABLE = ("Panero table-height norm — "
           "knowledge/ergonomics/residential-clearances.md (REFERENCE tier)")
C_MAT = ("pipeline/scripts/material_defaults.py + build_room.py _suite_materials — HARDCODED studio "
         "render default, keyed by kind→name-prefix; tuned by past A/B render gates, NOT by this spec "
         "or a client concept")
C_PERSONA = ("persona.py coverage (activity_taxonomy) — element traced to a client activity the "
             "persona STATES; cited to the persona's own line")
C_ACTIVITY = ("activity_taxonomy.py — element serves a BASELINE dwelling activity (a home needs it "
              "regardless of stated lifestyle)")


# ----------------------------------------------------------------- why-axis helper
def _axis(text, cite, grounded):
    return {"text": text, "cite": cite, "grounded": grounded}


_REAL = {"function", "clearance", "code", "ergonomic", "concept",
         "persona", "activity"}   # a real design source (persona/activity = presence grounded to a client need)

# Active persona presence-context (set by report() for the duration of one report; None =
# no persona -> the presence axis behaves exactly as before). Module-scoped so the per-axis
# helpers stay signature-compatible; report() sets it under try/finally, never leaks.
_PCTX = None


def _rollup(*axes):
    tags = [a["grounded"] for a in axes]
    if all(t in _REAL for t in tags):
        return "true"
    if any(t in _REAL for t in tags):
        return "partial"
    return "default"


# ----------------------------------------------------------------- clearance map
def _clearance_index(spec):
    """Best-effort keyword map of suite_clearance rows onto elements/room. Rows we
    can't attribute stay ROOM-level (never dropped, never mis-assigned)."""
    try:
        rows = SC.check(spec)
    except Exception:                       # a clearance bug must never break rationale
        return {"bed": [], "bath": [], "door": [], "room": []}
    idx = {"bed": [], "bath": [], "door": [], "room": []}
    for r in rows:
        n = str(r.get("check", "")).lower()
        if "bed" in n or "circulation" in n:
            idx["bed"].append(r)
        elif "bath" in n or "fixture" in n or "ensuite" in n or "lux" in n:
            idx["bath"].append(r)
        elif "door" in n:
            idx["door"].append(r)
        else:
            idx["room"].append(r)          # area / narrow-side / ceiling / corridor
    return idx


def _fmt_rows(rows, cap=2):
    """A few clearance rows as a cited sub-clause (statutory cite is inside .detail)."""
    picked = [r for r in rows if r["status"] in ("PASS", "FAIL", "WARN")][:cap]
    return "; ".join(f"[{r['status']}] {r['detail']}" for r in picked)


# ----------------------------------------------------------------- per-axis logic
def _persona_presence(el):
    """Persona-grounded PRESENCE (only reached when a persona pctx is active). Upgrades
    'declared in spec' to 'serves activity X (the client does Y)'. Returns an axis or None
    (None = fall through to the honest spec fallback, e.g. an ambiguous element). Never
    throws — a persona-layer hiccup must not break rationale."""
    try:
        ea = AT.element_activities(el)
        acts = ea["activities"]
        if not acts:
            return None                        # ambiguous -> undetermined; spec fallback stays honest
        lifestyle = _PCTX.get("lifestyle", {}) if _PCTX else {}
        hit = [a for a in acts if a in lifestyle]
        if hit:
            srcs = "; ".join(lifestyle[a] for a in hit)
            return _axis(f"serves {', '.join(hit)} — the client {srcs} "
                         f"(persona {_PCTX.get('persona_id', 'persona')}; activity via {ea['source']}).",
                         C_PERSONA, "persona")
        base = [a for a in acts if a in AT.BASELINE_ACTIVITIES]
        if base:
            return _axis(f"serves the baseline dwelling need '{base[0]}' — a home requires it "
                         f"regardless of stated lifestyle (activity via {ea['source']}).",
                         C_ACTIVITY, "activity")
        return _axis(f"serves {acts} but the persona never states that activity — POSSIBLE ORPHAN "
                     f"(why is this here? cut it or justify it).",
                     "persona coverage (orphan — flagged, NOT grounded)", "spec")
    except Exception:
        return None


def _presence_axis(el, group, note):
    kind = el.get("kind", "") or ""
    # statutory-implied presence (WC/basin make the room a bathroom -> mr39 governs)
    if group == "fixtures" and kind in (PL.BATH_WC_KINDS | PL.BATH_BASIN_KINDS):
        return _axis(f"a {kind} is a required sanitary fixture; its presence makes the room a "
                     f"bathroom governed by ฉ.39 (area / ventilation / lux).",
                     "ฉ.39 — knowledge/codes-th/mr39-fire-sanitation-ventilation.md", "code")
    # persona-grounded presence — the element traces to a client activity (only when a
    # persona is active; None-safe, so this is a no-op for the default persona-less path)
    if _PCTX is not None:
        pax = _persona_presence(el)
        if pax is not None:
            return pax
    # spec author's note documents a real decision about this element (PROSE, not a rule)
    key = kind.split("_")[0]
    if note and key and key.lower() in note.lower():
        return _axis("declared in spec; the spec author's note documents this decision "
                     "(prose changelog, not a validated rule).",
                     "spec.note (author prose) + spec file", "note")
    return _axis("declared in the room spec by the author — no machine-derived reason for its "
                 "presence (a design choice, not a computed one).",
                 "spec file (author declaration)", "spec")


def _placement_axis(el, group, kind, fmap, cmap):
    fins = fmap.get(id(el), [])
    if fins:
        txt = "; ".join(f"[{f['status']}] {f['detail']}" for f in fins)
        extra = ""
        if kind == "bed" and cmap["bed"]:
            extra = " | statutory/ergo framing: " + _fmt_rows(cmap["bed"])
        elif group == "fixtures" and cmap["bath"]:
            extra = " | clearance: " + _fmt_rows(cmap["bath"])
        return _axis(txt + extra, C_GS, "function")
    # no FUNCTION rule engaged this element — be honest, cite fit-only clearance
    if kind == "bed" and cmap["bed"]:
        return _axis("bed position: " + _fmt_rows(cmap["bed"]), "codes-th / dimensional_rules", "clearance")
    if group == "fixtures" and cmap["bath"]:
        return _axis("fixture position: " + _fmt_rows(cmap["bath"]), "codes-th / dimensional_rules", "clearance")
    return _axis("no FUNCTION or clearance RULE constrains this element's exact position; it is "
                 "spec-authored geometry, checked only for fit/overlap.",
                 "spec geometry (fit-checked, not rule-derived)", "spec")


def _dimension_axis(el, kind):
    w = float(el.get("w", 0) or 0)
    d = float(el.get("d", 0) or 0)
    h = float(el.get("h", 0) or 0)
    if kind == "bed" and w and d:
        name, (bw, bl), ok, worst = ergo.nearest_bed_size(w, d)
        verdict = "matches" if ok else "is OFF"
        return _axis(f"{w:.0f}×{d:.0f} mm {verdict} the {name} standard mattress "
                     f"({bw}×{bl}, worst Δ{worst:.0f} mm, tol ±{ergo.BED_SIZE_TOL_MM}).",
                     C_BED, "ergonomic")
    if kind == "wardrobe" and (w or d):
        dep = min(w, d)
        lo, hi = ergo.WARDROBE_DEPTH_MM
        ok = lo <= dep <= hi
        return _axis(f"depth {dep:.0f} mm {'within' if ok else 'OUTSIDE'} the {lo}–{hi} mm functional "
                     f"hanging-depth norm.", C_WARD, "ergonomic")
    if kind in ergo.TABLE_H_MM and h:
        lo, hi = ergo.TABLE_H_MM[kind]
        ok = lo <= h <= hi
        return _axis(f"height {h:.0f} mm {'within' if ok else 'OUTSIDE'} the {lo}–{hi} mm norm for a "
                     f"{kind}.", C_TABLE, "ergonomic")
    return _axis(f"{w:.0f}×{d:.0f}×{h:.0f} mm is spec-authored; no ergonomic dimension rule covers "
                 f"kind '{kind}' (clearance validates fit, not size choice).",
                 "spec geometry (no ergonomic rule for this kind)", "spec")


def _cite_resolves(cite):
    """cite-or-drop: a spec material cite must point at a real file under knowledge/ or docs/."""
    path = str(cite).split("—")[-1].split("(")[0].strip()
    if not path or (not path.startswith("knowledge/") and not path.startswith("docs/")):
        return False
    return os.path.exists(os.path.join(_repo_root(), path.replace("/", os.sep)))


def _material_axis(el, group):
    # HONESTY: today the spec carries NO material field and build_room ignores the spec
    # anyway (material_defaults describes exactly what it renders). If a future spec grows
    # a cite-resolving material field, read it here and ground it to 'concept'.
    rat = el.get("rationale")
    rat = rat if isinstance(rat, dict) else {}   # a non-dict rationale (prose/list) must degrade, not crash
    mat = rat.get("material")
    cite = (rat.get("cite") or {}).get("material") if isinstance(rat.get("cite"), dict) else None
    if mat and cite and _cite_resolves(cite):
        why = (rat.get("why") or {}).get("material", "per spec material field")
        return _axis(f"'{mat}' — {why}.", cite, "concept")
    if mat and not (cite and _cite_resolves(cite)):
        return _axis(f"spec names material '{mat}' but its cite is missing/unresolved — per "
                     f"knowledge/CLAUDE.md cite-or-drop, this does NOT ship as grounded.",
                     "UNCITED spec material (flagged, not grounded)", "default")
    human, slug = matdef.default_material(el.get("kind"), group)
    return _axis(f"renders as {human} — this is the STUDIO RENDER DEFAULT for this kind (build_room "
                 f"mat '{slug}'). It is NOT tied to a client concept, brief, or this spec; there is no "
                 f"material field. Needs a concept material palette to justify.",
                 C_MAT, "default")


# ----------------------------------------------------------------- FUNCTION map
def _function_map(spec):
    """Map each FUNCTION finding onto the element it judges, by re-running the same
    finders placement_logic used (findings carry no element id). id()-keyed; for @0.2
    (metric) the normalized objects ARE the caller's, so ids match."""
    nspec = PL._normalize(spec)
    bed = PL.find_bed(nspec)
    tv, _tv_status = PL.find_tv(nspec)
    fmap = {}

    def push(el, fin):
        if el is not None:
            fmap.setdefault(id(el), []).append(fin)

    for f in PL.check(spec)["findings"]:
        rid = f["rule"]
        if rid.startswith("tv_"):
            push(tv, f)
        elif rid == "door_vs_bed_head":
            push(bed, f)
        elif rid == "furniture_dimensions":
            pass    # per-element dimension is emitted natively by _dimension_axis
        elif rid == "bathroom_logic":
            for sr in spec.get("subrooms", []):
                for fx in sr.get("fixtures", []):
                    push(fx, f)
        elif rid == "seating_faces_focal":
            for el in PL._iter_elements(nspec):
                if el.get("kind") in PL.SEATING_KINDS:
                    push(el, f)
        elif rid == "bed_has_nightstand":
            push(bed, f)          # the finding is about the bed's (missing) bedside table
        elif rid == "dining_table_pendant":
            for el in (nspec.get("items") or []):
                if el.get("kind") in PL.DINING_MISKIND_KINDS and PL._DINING_NAME_RE.search(
                        str(el.get("name") or "")):
                    push(el, f)   # the mis-kinded table that loses its pendant
        elif rid == "basin_has_storage":
            for sr in nspec.get("subrooms", []):
                for fx in sr.get("fixtures", []):
                    if fx.get("kind") in PL.BARE_BASIN_KINDS:
                        push(fx, f)
    return fmap


# ----------------------------------------------------------------- public API
def _tag(group, i):
    return {"builtins": f"BI-{i + 1:02d}", "items": "FF&E", "fixtures": "FIX"}[group]


def report(spec, persona=None):
    """-> {"elements":[record...], "room":[clearance rows], "summary":{...}}.
    Never throws: any sub-failure degrades that axis to an honest 'spec/default'.
    When `persona` is given, an element's PRESENCE 'why' upgrades from 'declared in spec'
    to 'serves activity X (the client does Y)' — grounded to the persona's own words."""
    global _PCTX
    _prev = _PCTX
    try:
        _PCTX = PER.presence_context(persona) if persona is not None else None
    except Exception:
        _PCTX = None
    try:
        return _report_body(spec)
    finally:
        _PCTX = _prev


def _report_body(spec):
    note = spec.get("note", "") or ""
    cmap = _clearance_index(spec)
    try:
        fmap = _function_map(spec)
    except Exception:
        fmap = {}

    records = []

    def emit(el, group, i):
        if not isinstance(el, dict):
            return                              # a junk (non-dict) element degrades out, never crashes
        kind = el.get("kind", "?")
        presence = _presence_axis(el, group, note)
        placement = _placement_axis(el, group, kind, fmap, cmap)
        dimension = _dimension_axis(el, kind)
        material = _material_axis(el, group)
        records.append({
            "element": el.get("name") or kind,
            "tag": _tag(group, i),
            "kind": kind,
            "presence_why": presence,
            "placement_why": placement,
            "dimension_why": dimension,
            "material_why": material,
            "grounded": _rollup(presence, placement, dimension, material),
        })

    for i, b in enumerate(spec.get("builtins") or []):
        emit(b, "builtins", i)
    for i, it in enumerate(spec.get("items") or []):
        emit(it, "items", i)
    for sr in spec.get("subrooms") or []:
        if not isinstance(sr, dict):
            continue
        for i, fx in enumerate(sr.get("fixtures") or []):
            emit(fx, "fixtures", i)

    summary = {"true": 0, "partial": 0, "default": 0}
    for rec in records:
        summary[rec["grounded"]] += 1
    return {"elements": records, "room": cmap["room"], "summary": summary}


def to_markdown(spec, name="", persona=None):
    rep = report(spec, persona)
    s = rep["summary"]
    L = [f"# DESIGN RATIONALE — {name or spec.get('room', {}).get('type', 'room')}",
         "",
         "Per-element, cited answer to *why here / why this placement / why this size / why this "
         "material*. Honesty-first: every line traces to a real source; a hardcoded render default "
         "says so. Source-of-truth order: knowledge/codes-th > client contract > studio standards > "
         "ergonomic references (higher tier wins; the winning tier is named).",
         "",
         f"**Grounding: {s['true']} fully-grounded · {s['partial']} partial · {s['default']} default.**",
         "",
         "> Every element is capped at **partial** at best while materials remain hardcoded studio "
         "> render defaults (no spec material field, no concept palette). That is the honest headline: "
         "> the render is dimensionally/functionally grounded but chromatically a placeholder. Fully "
         "> grounding an element needs a cited material choice from the concept stage.",
         ""]
    for rec in rep["elements"]:
        L.append(f"## {rec['tag']} · {rec['element']}  (`{rec['kind']}`) — **{rec['grounded'].upper()}**")
        for axis, lbl in (("presence_why", "PRESENCE"), ("placement_why", "PLACEMENT"),
                          ("dimension_why", "DIMENSION"), ("material_why", "MATERIAL")):
            a = rec[axis]
            L.append(f"- **{lbl}** ({a['grounded']}): {a['text']}")
            L.append(f"  - cite: `{a['cite']}`")
        L.append("")
    if rep["room"]:
        L.append("## ROOM ENVELOPE (statutory, from suite_clearance / codes-th)")
        for r in rep["room"]:
            L.append(f"- [{r['status']}] {r['check']}: {r['detail']}")
    return "\n".join(L)


if __name__ == "__main__":
    import json
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "specs", "bedroom_suite.json")
    spec = json.load(open(p, encoding="utf-8"))
    print(to_markdown(spec, os.path.basename(p)))
    sys.exit(0)
