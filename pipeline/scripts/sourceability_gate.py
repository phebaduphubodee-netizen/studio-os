"""
sourceability_gate.py — the MOAT gate: a render must VISUALIZE a sourceable spec.

Decision of record (docs/strategy.md, 2026-07-06 "sourceability-first"): a beautiful render
whose furniture cannot be bought/built in the real Thai market is not neutral — it is
NEGATIVE (the client can't buy it, feels misled, repeat work dies). So furniture is SELECTED
from real products (03_layout/ffe-candidates.json) BEFORE rendering; this gate proves the
scene-graph the renderer builds is backed by that sourceable spec. Sibling to the Gate-0
clearance check and the FUNCTION gate — it runs pre-render AND pre-deliverable, ALONGSIDE the
statutory clearance (codes-th still outranks), never above it.

Every placed element is split by CLASS:
  * SOURCED    = loose items[]  +  sanitary/appliance fixtures (toilet, basin, tub, fridge…)
                 -> bought from a catalog -> subject to the four machine checks below.
  * FABRICATED = builtins[]  +  millwork fixtures (vanity carcass, built-in wardrobe…)
                 -> made by a joiner -> NOT catalog-sourced. A deep buildability check
                 (casework clearances) is UNWIRED: listed honestly, never silent-passed.

Four machine checks per SOURCED element (check 5, render-parity, is the honest hard half —
a generative render can't be pixel-forced to a SKU, so it is handled by prompt-naming +
always bundling the schedule/BOM, not here):
  1. binding parity  — ffe_tag resolves to an FF&E role with a selected:true candidate.  FAIL if not.
  2. dimension parity— selected candidate dimensions_mm match the footprint within ±15%.  FAIL if not.
                       (automates the 2026-07-04 FFE-S01 lesson: a 600mm-spec sofa vs the
                        buyable 860mm product is a size lie the render would show.)
  3. real supplier   — selected candidate has source_th + link.                            FAIL if not.
  4. verified tier   — for CLIENT DELIVERY the candidate must be verified:true.  verified:false
                       -> REVIEW (renderable for concept; deliverable stamped "not sourced-confirmed").

Verdict:
  UNWIRED — no FF&E file for this project: sourcing cannot be checked. NEVER a silent PASS.
  FAIL    — any sourced element hard-fails (unbound / wrong size / no supplier). Blocks render.
  REVIEW  — sourced + supplied + right-sized, but a pick is not verified-confirmed yet.
  PASS    — every sourced element is bound, right-sized, from a real supplier, verified.

Pure logic (classify / resolve / dims / checks / aggregate) is import-testable with no files;
check() adds file location + raw-JSON load (reads spec["items"] dicts directly, so an ffe_tag
added to the scene-graph survives — clearance_check's Item objects would drop it).

    python sourceability_gate.py <scene-graph.json> [ffe-candidates.json]
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# The owner-sign gate (docs/research/2026-07-11-furniture-sourcing-DR.md): a `sourcing-signoff.json`
# ledger can turn a verified:false pick into verified WITHOUT editing the ffe JSON. Optional import so
# this gate still loads if the sibling module is absent (then only the inline `verified` boolean counts).
try:
    import ffe_signoff_gate as _SIGNOFF
except Exception:
    _SIGNOFF = None


def _verified_with_prov(cand, signoff):
    """(verified_bool, provenance|None). A VALID ledger signature (prov source='ledger', carrying
    by/date) OR the inline verified boolean (source='inline'). With no ledger (signoff falsy) this is
    exactly (bool(cand['verified']), …) — backward-compatible. The provenance is threaded into the
    result detail so a ledger-DRIVEN pass is visibly distinct from an inline verified:true pass (a
    signature must SURFACE, never silently flip the verdict) — this gate's report is what make_all
    prints, and it does not run the dedicated sign gate."""
    if signoff and _SIGNOFF is not None:
        return _SIGNOFF.resolve_verified(cand, signoff)
    v = bool(cand.get("verified"))
    return v, ({"source": "inline"} if v else None)

# Fixtures that are BOUGHT (sanitaryware + appliances) rather than joiner-made. A fixture whose
# kind is NOT in this set (vanity carcass, built-in wardrobe, counter) is millwork -> fabricated.
SANITARY_APPLIANCE_KINDS = {
    "toilet", "wc", "water_closet", "basin", "washbasin", "lavatory", "sink",
    "tub", "bathtub", "shower", "bidet", "urinal",
    "fridge", "refrigerator", "freezer", "washer", "washing_machine", "dryer",
    "oven", "stove", "range", "cooktop", "hob", "hood", "range_hood", "dishwasher",
    "microwave", "water_heater", "aircon", "ac", "air_conditioner",
}

TOL = 0.15   # ±15% dimension parity — matches the ffe-research skill's own footprint tolerance


def classify_element(el, array):
    """'sourced' (bought) or 'fabricated' (joiner-made). items[] are always loose-bought;
    builtins[] are always joiner-made; a fixture depends on its KIND (sanitary/appliance =
    bought, millwork carcass = made). A fixture with a MISSING/empty kind is routed to
    'sourced' so it SURFACES (a binding REVIEW/FAIL trace) instead of silently escaping the
    gate into the un-checked FABRICATED bucket — real millwork always carries an explicit kind."""
    if array == "items":
        return "sourced"
    if array == "builtins":
        return "fabricated"
    k = (el.get("kind") or "").strip().lower()
    if not k:
        return "sourced"
    return "sourced" if k in SANITARY_APPLIANCE_KINDS else "fabricated"


def elements(spec):
    """Yield (element_dict, array_label) for every placed piece across items / builtins /
    subroom fixtures. array_label drives classification."""
    for it in spec.get("items", []) or []:
        yield it, "items"
    for it in spec.get("builtins", []) or []:
        yield it, "builtins"
    for sr in spec.get("subrooms", []) or []:
        for it in sr.get("fixtures", []) or []:
            yield it, "fixtures"


def resolve_candidate(ffe_tag, ffe_doc):
    """The selected:true candidate for an ffe_tag, or None (no tag / tag not found / role
    present but nothing selected / empty candidates). The tag joins on the ROLE-level `tag`
    (e.g. 'FFE-S01'), then picks the candidate marked selected."""
    if not ffe_tag or not isinstance(ffe_doc, dict):
        return None
    for role in ffe_doc.get("items", []) or []:
        if role.get("tag") == ffe_tag:
            sel = [c for c in (role.get("candidates", []) or []) if c.get("selected")]
            return sel[0] if sel else None
    return None


def dims_ok(item_wd, cand_dims, tol=TOL):
    """Orientation-agnostic footprint parity within tol. Compares the sorted (min,max) extents
    so a candidate recorded with w/d swapped from the scene-graph piece still matches (same
    footprint), while a genuine size error — the FFE-S01 600 vs 860mm depth — is caught in
    either orientation. Missing/garbage dims -> False (a size we can't confirm is not a match)."""
    if not isinstance(cand_dims, dict):
        return False
    try:
        a = sorted((float(item_wd["w"]), float(item_wd["d"])))
        b = sorted((float(cand_dims["w"]), float(cand_dims["d"])))
    except (KeyError, TypeError, ValueError):
        return False
    for s, c in zip(a, b):
        if c <= 0 or abs(s - c) / c > tol:
            return False
    return True


def _supplier_ok(cand):
    return bool((cand.get("source_th") or "").strip()) and bool((cand.get("link") or "").strip())


def check_sourced(el, ffe_doc, signoff=None):
    """The four machine checks on one SOURCED element. binding/dimension/supplier failing ->
    FAIL (hard: the render would show a piece no buyable product backs, or the wrong size, or
    from no real supplier). verified:false ALONE -> REVIEW (renderable concept, deliverable
    stamped). Returns {name, kind, cls, ffe_tag, status, failed[], detail}.

    `signoff` (the sourcing-signoff ledger, optional) lets an owner signature satisfy the verified
    tier without editing the ffe JSON; with no ledger the inline verified boolean is used as before."""
    name = el.get("name", el.get("kind", "?"))
    tag = el.get("ffe_tag")
    cand = resolve_candidate(tag, ffe_doc)
    if cand is None:
        if not tag:
            # NO ffe_tag: the binding is not wired yet for this piece. That is a "not done"
            # state, not a "done wrong" state -> REVIEW (concept-renderable, deliverable flagged),
            # NOT a hard FAIL. Otherwise every real project (where ffe_tag is a documented
            # not-yet-built feature) would have no reachable non-FAIL verdict and an advancing
            # deliverable would flip REVIEW->FAIL purely because the binding step hasn't shipped.
            return {"name": name, "kind": el.get("kind"), "cls": "sourced", "ffe_tag": None,
                    "status": "REVIEW", "failed": ["binding"],
                    "detail": "no ffe_tag — not yet bound to a sourceable product (binding pending)"}
        # a tag IS present but resolves to no selected candidate -> a LYING binding -> hard FAIL.
        return {"name": name, "kind": el.get("kind"), "cls": "sourced", "ffe_tag": tag,
                "status": "FAIL", "failed": ["binding"],
                "detail": f"ffe_tag {tag!r} resolves to no selected FF&E candidate"}
    failed = []
    if not dims_ok(el, cand.get("dimensions_mm")):
        failed.append("dimension")
    if not _supplier_ok(cand):
        failed.append("supplier")
    verified, prov = _verified_with_prov(cand, signoff)
    if not verified:
        failed.append("verified")
    hard = [f for f in failed if f != "verified"]
    status = "FAIL" if hard else ("REVIEW" if failed else "PASS")
    cd = cand.get("dimensions_mm") or {}
    detail = f"{tag} -> {cand.get('manufacturer', '?')} {cand.get('model', '?')} ({cd.get('w')}x{cd.get('d')}mm)"
    if prov and prov.get("source") == "ledger":
        detail += f"  [owner-signed by {prov.get('by')} on {prov.get('date')}]"   # surface the ledger flip
    if failed:
        detail += "  [" + ", ".join(failed) + "]"
    return {"name": name, "kind": el.get("kind"), "cls": "sourced", "ffe_tag": tag,
            "status": status, "failed": failed, "detail": detail}


def check_fabricated(el):
    """Joiner-made — NOT catalog-sourced, so it can never sourcing-FAIL. The deep buildability
    check (drawer deductions / hinge count / curtain-pocket depth vs
    knowledge/ergonomics/casework-fixture-clearances-th-practice.md) is UNWIRED: reported
    honestly, never silent-passed, never drives the verdict."""
    return {"name": el.get("name", el.get("kind", "?")), "kind": el.get("kind"),
            "cls": "fabricated", "status": "FABRICATED", "failed": [],
            "detail": "joiner-made — buildability check UNWIRED (not catalog-sourced)"}


def report(spec, ffe_doc, signoff=None):
    """(results, verdict). UNWIRED when no FF&E file (sourcing cannot be checked — never a
    silent PASS). Else FAIL if any SOURCED element hard-fails, REVIEW if any is REVIEW, PASS if
    every sourced element is bound+sized+supplied+verified. Fabricated elements are listed but
    never drive the verdict. `signoff` (optional sourcing-signoff ledger) lets an owner signature
    satisfy the verified tier; None -> the inline verified boolean, backward-compatible."""
    results = []
    for el, array in elements(spec):
        if classify_element(el, array) == "fabricated":
            results.append(check_fabricated(el))
        elif ffe_doc is None:
            results.append({"name": el.get("name", el.get("kind", "?")), "kind": el.get("kind"),
                            "cls": "sourced", "ffe_tag": el.get("ffe_tag"), "status": "UNWIRED",
                            "failed": [], "detail": "no FF&E file — sourcing unverified"})
        else:
            results.append(check_sourced(el, ffe_doc, signoff))

    if ffe_doc is None:
        return results, "UNWIRED"
    sourced = [r for r in results if r.get("cls") == "sourced"]
    if not sourced:
        # an FF&E file exists but NOTHING here is catalog-sourced (all-millwork / empty /
        # loose furniture misrouted into builtins[]) -> nothing was verified, so never emit a
        # green PASS. UNWIRED honestly says "no sourced piece to check here".
        return results, "UNWIRED"
    if any(r["status"] == "FAIL" for r in sourced):
        verdict = "FAIL"
    elif any(r["status"] == "REVIEW" for r in sourced):
        verdict = "REVIEW"
    else:
        verdict = "PASS"
    return results, verdict


def report_rows(results):
    """QA-CHECKLIST rows for suite_package, shaped like the FUNCTION rows ({status, check,
    detail}, check prefixed 'sourceability:'). Emits a row per non-PASS sourced element so the
    cover verdict + checklist pick sourcing up for free. status is mapped to the checklist's
    vocabulary: FAIL->FAIL, REVIEW->WARN."""
    rows = []
    for r in results:
        if r.get("cls") != "sourced" or r["status"] in ("PASS", "UNWIRED"):
            continue
        rows.append({"status": "FAIL" if r["status"] == "FAIL" else "WARN",
                     "check": f"sourceability: {r['name']}", "detail": r["detail"]})
    return rows


def bundle_rows(verdict, ffe_present, has_render):
    """Deliverable-bundle rule (strategy 2026-07-06): a render is NOT a deliverable without
    its FF&E schedule + client BOM. Returns QA-CHECKLIST {status, check, detail} rows.
    A render with NO FF&E file is concept-only (WARN — escalates the deliverable to REVIEW);
    the always-visible checklist section carries the standing 'ship render + schedule + BOM
    together' reminder, so this only emits the exception rows."""
    rows = []
    if has_render and not ffe_present:
        rows.append({"status": "WARN", "check": "sourceability: deliverable bundle",
                     "detail": "render present but NO FF&E file — CONCEPT ONLY, not client-sourced; "
                               "add ffe-candidates.json (+ ffe_tag bindings) and the client BOM before delivery"})
    return rows


def load_ffe(spec_path, spec):
    """Locate the FF&E file: an explicit spec['ffe_candidates'] path first, else
    'ffe-candidates.json' beside the spec. Returns (ffe_doc | None, path | None); a present but
    malformed file -> (None, None) (UNWIRED, honest) rather than a crash."""
    base = os.path.dirname(os.path.abspath(spec_path))
    cands = []
    ref = spec.get("ffe_candidates") if isinstance(spec, dict) else None
    if ref:
        cands += [ref, os.path.join(base, os.path.basename(ref))]
    cands.append(os.path.join(base, "ffe-candidates.json"))
    for c in cands:
        if c and os.path.exists(c):
            try:
                return json.load(open(c, encoding="utf-8")), c
            except (ValueError, OSError):
                return None, None
    return None, None


def signoff_beside(ffe_path):
    """The sourcing-signoff ledger beside an ffe file, or [] (no ledger / sign module absent). Shared
    by check() and suite_package so the deliverable seam consults an owner signature IDENTICALLY to
    the CLI — a valid ledger must not be honoured in one entry point and silently ignored in another."""
    if ffe_path and _SIGNOFF is not None:
        return _SIGNOFF.load_signoff_beside(ffe_path)
    return None


def check(spec_path):
    """Load a raw scene-graph + its FF&E file and gate it. Returns (verdict, results) — note
    the order is (verdict, results) to match how make_all consumes the gate."""
    spec = json.load(open(spec_path, encoding="utf-8"))
    ffe_doc, ffe_path = load_ffe(spec_path, spec)
    signoff = signoff_beside(ffe_path)
    results, verdict = report(spec, ffe_doc, signoff)
    return verdict, results


_MARK = {"PASS": "OK   ", "REVIEW": "REVIEW", "FAIL": "FAIL ", "UNWIRED": "UNWIR", "FABRICATED": "FAB  "}


def format_report(results, verdict, name):
    out = ["=" * 74,
           "SOURCEABILITY GATE — is every rendered piece a real, buyable/buildable product?",
           "=" * 74, f"### {name}   -> {verdict}"]
    sourced = [r for r in results if r.get("cls") == "sourced"]
    fab = [r for r in results if r.get("cls") == "fabricated"]
    out.append("  SOURCED (bought — gated):")
    for r in sourced:
        out.append(f"    [{_MARK.get(r['status'], r['status']):6}] {r['name']}: {r['detail']}")
    if fab:
        out.append("  FABRICATED (joiner-made — buildability UNWIRED, not gated):")
        for r in fab:
            out.append(f"    [{_MARK['FABRICATED']}] {r['name']} ({r['kind']})")
    if verdict == "UNWIRED":
        out.append("  (!) No FF&E file found — sourcing UNVERIFIED. Add ffe-candidates.json + ffe_tag "
                   "bindings to enforce the moat. NOT a pass.")
    out.append("  check-5 render-parity (not machine-verifiable here): the render prompt MUST name "
               "each selected real product; the deliverable MUST bundle the FF&E schedule + BOM.")
    out.append("-" * 74)
    out.append(f"OVERALL: {verdict}   " + {
        "FAIL": "(blocks render — a sourced piece is unbound / wrong-size / has no supplier)",
        "REVIEW": "(renderable for concept; deliverable stamped 'furniture not sourced-confirmed')",
        "PASS": "(every sourced piece is bound, right-sized, real-supplier, verified)",
        "UNWIRED": "(no FF&E file — sourcing unchecked; never a silent pass)"}[verdict])
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    _spec_path = sys.argv[1]
    if len(sys.argv) > 2:
        _spec = json.load(open(_spec_path, encoding="utf-8"))
        _ffe = json.load(open(sys.argv[2], encoding="utf-8"))
        _results, _verdict = report(_spec, _ffe)
    else:
        _verdict, _results = check(_spec_path)
    print(format_report(_results, _verdict, os.path.basename(_spec_path)))
    sys.exit(1 if _verdict == "FAIL" else 0)
