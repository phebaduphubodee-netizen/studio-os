"""
ffe_partition_gate.py — the SCOPING gate: split an FF&E schedule into FABRICATED vs SOURCEABLE.

Decision of record (docs/research/2026-07-11-furniture-sourcing-DR.md, finding (d) + the TRACER
reframe): built-in joinery is custom-FABRICATED (MADE by the workshop, priced by run+labor at
quote) and is NOT externally sourced; only LOOSE furniture + bought fixtures are sourced from a
catalog. The DR empirically validated the studio's owner-signed law for sourcing too: sourcing is
candidate-generation + owner-signature, never full-auto. This gate is step 1 of that pipeline — it
partitions the ffe-candidates.json roles so the downstream lanes run on the RIGHT set:

  * FABRICATED -> workshop BOM. NOT sourced, NOT price/stock-freshness-validated, NOT owner-sign
                 gated (a null unit_price on a built-in wardrobe is CORRECT, not a failure).
  * SOURCEABLE -> the sourcing queue: freshness re-validation (b) + owner sign-off (c) apply here.

The partition key is the candidate's `csi` MasterFormat code, which the ffe-research skill already
populates on every candidate (it "already tags built-ins csi 06/09 vs loose csi 12/22/26" — the DR
TRACER). We read the DIVISION (first two digits) so a sub-code drift (12 52 vs 12 58) never
mis-routes. The csi is cross-checked against three corroborating signals the built-ins also carry
(a `FFE-B*` tag, a "built-in"/millwork role, a studio-vault/projects-relative source instead of a
retailer link); when the structured csi and the corroboration DISAGREE the role is routed to REVIEW
— surfaced for a human, NEVER silently trusted to one signal (the recurring flattering-scorer trap:
a single self-agreeing signal is not a decision).

Verdict (routing, not a safety block -> never FAIL):
  PASS   — every role classifies cleanly and its csi agrees with its corroboration.
  REVIEW — some role has no/unknown csi, or its csi diverges from the built-in/retailer signals, or
           it has zero researched candidates. A human confirms the route before sourcing runs.

Pure logic (division / classify / partition / aggregate) is import-testable with no files; check()
adds file load. Mirrors sourceability_gate.py's shape on purpose (same idioms, same repo).

    python ffe_partition_gate.py <ffe-candidates.json> [--out ffe-partition.json]
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# CSI MasterFormat DIVISIONS (first two digits) -> sourcing route.
# FABRICATED = made by a joiner / installed as a fixed finish -> workshop BOM, priced at quote.
FABRICATED_DIVISIONS = {
    "05",  # Metals — custom fabricated metalwork (rare here; grouped with made-to-order)
    "06",  # Wood, Plastics & Composites — architectural woodwork / casework / built-in millwork
    "09",  # Finishes — wall panelling, feature walls, applied finishes (installed, not a product)
}
# SOURCEABLE = bought as a finished product from a catalog -> freshness + owner sign-off apply.
SOURCEABLE_DIVISIONS = {
    "10",  # Specialties (accessories, mirrors, signage)
    "11",  # Equipment (appliances, audio-visual / TVs)
    "12",  # Furnishings (loose furniture — seating, casegoods, beds, benches)
    "22",  # Plumbing (sanitaryware, faucets, tubs, WCs)
    "23",  # HVAC (split-unit air conditioners)
    "26",  # Electrical — decorative / portable lighting
    "27",  # Communications
}

# Markers of a MADE-TO-ORDER / joiner-fabricated pick (corroborate the csi division). These are
# deliberately about FABRICATION, not installation: the bare word "built-in" is EXCLUDED because it
# also describes an install type for a BOUGHT fixture (a "built-in/drop-in" bathtub is a real SKU),
# which would false-flag. The signals here mean the item is genuinely custom-made / priced at quote.
_FAB_WORDS = ("custom fabrication", "fabricated to order", "fabrication quote", "fabricated (",
              "millwork", "joiner", "carcass", "priced by run", "made to order (custom",
              "carpentry")
# A studio built-in feature code (BF11, BF10.250, F02…) in a tag/model/notes = a fabrication marker.
# Two digits required so a stray "f0…" in prose can't trip it; the blob is already lower-cased.
_BF_CODE_RE = re.compile(r"\bb?f\d\d")
# Electronics normally brought by the client — sourceable but NOT the studio's to buy; advisory only.
_CLIENT_SUPPLIED_WORDS = ("client-supplied", "client supplied", "client-provided", "owner-supplied")


def _division(csi):
    """The two-digit CSI division of a code string ('06 41 00' -> '06', '12-52-00' -> '12'),
    or None if there is no leading two-digit token. Tolerates space/dash separators and a bare
    concatenated code ('064100' -> '06')."""
    if not isinstance(csi, str):
        return None
    tok = csi.strip().replace("-", " ").split()
    head = tok[0] if tok else ""
    return head[:2] if len(head) >= 2 and head[:2].isdigit() else None


def _pick(role):
    """The candidate that represents this role: the selected one, else the sole candidate, else
    the first, else None. csi is per-candidate but constant across a role's candidates in practice,
    so the representative pick's csi is the role's csi."""
    cands = role.get("candidates") or []
    sel = [c for c in cands if c.get("selected")]
    if sel:
        return sel[0]
    return cands[0] if cands else None


def _role_csi(role):
    c = _pick(role)
    return (c or {}).get("csi")


def _text_blob(role, cand):
    """Lower-cased join of every field that can carry client-supplied language, INCLUDING the role
    NAME (FFE-L06's role literally says 'CLIENT-SUPPLIED'). Used for the client_supplied advisory."""
    c = cand or {}
    parts = [role.get("tag"), role.get("role"), role.get("best_pick_reason"),
             c.get("manufacturer"), c.get("model"), c.get("notes"),
             c.get("material_finish"), c.get("source_th")]
    return " ".join(p for p in parts if isinstance(p, str)).lower()


def _fab_blob(cand):
    """Lower-cased join of the pick's OWN structured description — manufacturer / model / notes /
    material / source / lead. Deliberately EXCLUDES the role NAME and best_pick_reason: those are
    free prose that routinely reference OTHER options' built-in codes ('chosen over the built-in
    BF12 bench'), which must not flip a genuinely-bought pick to REVIEW (the reviewer's false-positive
    vector). A real custom-fab pick carries its fabrication language in these structured fields."""
    c = cand or {}
    parts = [c.get("manufacturer"), c.get("model"), c.get("notes"),
             c.get("material_finish"), c.get("source_th"), c.get("lead_time")]
    return " ".join(p for p in parts if isinstance(p, str)).lower()


def _fabrication_signal(role, cand):
    """Does the SELECTED pick read as MADE-TO-ORDER / joiner-fabricated (vs a bought SKU)? A strong,
    fabrication-specific signal (not the weak install word 'built-in') — any one is enough:
      * an `FFE-B*` tag (the studio's built-in tag family: FFE-BM/BS/BL…), OR
      * fabrication language (custom fabrication / carcass / millwork / carpentry…) in the pick's own
        structured fields, or a BF## feature code in the STRUCTURED id (tag / model) — never free prose, OR
      * a studio-vault source or a repo-relative link (a built-in drafted from the vault, not a shop), OR
      * a null price whose lead time is a fabrication quote (priced by run+labor, no SKU).
    The caller only ACTS on it when it disagrees with the csi division (-> REVIEW), never silently."""
    tag = (role.get("tag") or "")
    if tag.upper().startswith("FFE-B"):
        return True
    if any(w in _fab_blob(cand) for w in _FAB_WORDS):
        return True
    structured_id = f"{tag} {(cand or {}).get('model') or ''}".lower()   # BF-code only in the id fields
    if _BF_CODE_RE.search(structured_id):
        return True
    src = ((cand or {}).get("source_th") or "").lower()
    link = ((cand or {}).get("link") or "").strip().lower()
    if "vault" in src or "studio" in src:
        return True
    if link and not link.startswith(("http://", "https://")):
        return True
    price = (cand or {}).get("unit_price_thb")
    lead = ((cand or {}).get("lead_time") or "").lower()
    if price in (None, "") and ("fabricat" in lead or "quote" in lead):
        return True
    return False


def _looks_retailer(cand):
    """Corroborating signal that a candidate is a bought product: a real http retailer link.
    (A studio-vault built-in links to a projects/ path, so this is False for it.)"""
    link = ((cand or {}).get("link") or "").strip().lower()
    return link.startswith(("http://", "https://"))


def _client_supplied(role, cand):
    return any(w in _text_blob(role, cand) for w in _CLIENT_SUPPLIED_WORDS)


def classify_role(role):
    """Route one FF&E role to 'fabricated' | 'sourceable' | 'review', csi-first with corroboration.

    csi division decides the route; the built-in / retailer signals only override it INTO review
    when they contradict it (a possible mis-tag a human must adjudicate) — a single signal never
    silently wins. A role with no/unknown csi is 'review' (never guessed). Returns a dict carrying
    the route, the evidence, and a `divergent` flag so the report can explain every REVIEW."""
    cand = _pick(role)
    csi = _role_csi(role)
    div = _division(csi)
    n_cand = len(role.get("candidates") or [])
    fab = _fabrication_signal(role, cand)
    rt = _looks_retailer(cand)
    base = {"tag": role.get("tag"), "room": role.get("room"), "role": role.get("role"),
            "csi": csi, "division": div, "n_candidates": n_cand,
            "fabrication_signal": fab, "retailer_signal": rt,
            "client_supplied": _client_supplied(role, cand), "divergent": False}

    if n_cand == 0:
        return {**base, "route": "review", "reason": "no candidates researched yet — nothing to route"}

    if div in FABRICATED_DIVISIONS:
        if rt and not fab:
            return {**base, "route": "review", "divergent": True,
                    "reason": f"csi {csi} = fabricated division {div}, but the pick is a retailer product "
                              "with no fabrication signal — confirm made-vs-bought"}
        return {**base, "route": "fabricated",
                "reason": f"csi {csi} (division {div}) = joiner-made / installed finish -> workshop BOM"}

    if div in SOURCEABLE_DIVISIONS:
        if fab:
            return {**base, "route": "review", "divergent": True,
                    "reason": f"csi {csi} = sourceable division {div}, but the selected pick reads as "
                              "MADE-TO-ORDER / fabricated (custom-fab, carcass, BF-code or priced-at-quote) "
                              "— confirm made-vs-bought (a fabricated item has no live SKU to sign)"}
        return {**base, "route": "sourceable",
                "reason": f"csi {csi} (division {div}) = bought product -> sourcing queue"
                          + ("  [client-supplied: reference only]" if base["client_supplied"] else "")}

    # unknown / missing csi -> never guessed; leaned label is advisory only
    lean = "fabricated" if (fab and not rt) else ("sourceable" if (rt and not fab) else "unknown")
    return {**base, "route": "review",
            "reason": f"csi {csi!r} has no recognised division — cannot route by structure "
                      f"(corroboration leans {lean}); a human must classify"}


def partition(ffe_doc):
    """(rows, summary, verdict) for a whole ffe-candidates doc. rows = per-role classify_role
    dicts; summary buckets the tags by route; verdict is REVIEW if any role needs a human, else
    PASS. Never FAIL — the partition is a routing decision, not a safety property that blocks."""
    items = (ffe_doc or {}).get("items", []) or []
    rows = [classify_role(r) for r in items]
    summary = {"fabricated": [], "sourceable": [], "review": []}
    for r in rows:
        summary[r["route"]].append(r["tag"])
    if not rows:
        verdict = "EMPTY"          # no roles to partition -> never a vacuous 'clean' PASS (stub/wrong file)
    elif summary["review"]:
        verdict = "REVIEW"
    else:
        verdict = "PASS"
    return rows, summary, verdict


def sourceable_tags(ffe_doc):
    """The tags routed to the sourcing queue — the exact set freshness (b) + owner sign-off (c)
    operate on. A convenience for the downstream lanes so they never re-derive the split."""
    rows, _s, _v = partition(ffe_doc)
    return [r["tag"] for r in rows if r["route"] == "sourceable"]


def check(ffe_path):
    """Load an ffe-candidates.json and partition it. Returns (verdict, rows, summary)."""
    doc = json.load(open(ffe_path, encoding="utf-8"))
    rows, summary, verdict = partition(doc)
    return verdict, rows, summary


_MARK = {"fabricated": "MADE ", "sourceable": "BUY  ", "review": "REVIEW"}


def format_report(rows, summary, verdict, name):
    out = ["=" * 74,
           "FF&E PARTITION GATE — split MADE (workshop) vs BOUGHT (sourcing queue)",
           "=" * 74, f"### {name}   -> {verdict}",
           f"  fabricated (workshop BOM): {len(summary['fabricated'])}   "
           f"sourceable (sourcing queue): {len(summary['sourceable'])}   "
           f"review: {len(summary['review'])}"]
    for route, title in (("fabricated", "FABRICATED — made by the workshop (not externally sourced):"),
                         ("sourceable", "SOURCEABLE — bought products (freshness + owner sign-off apply):"),
                         ("review", "REVIEW — a human must confirm the route:")):
        group = [r for r in rows if r["route"] == route]
        if not group:
            continue
        out.append(f"  {title}")
        for r in group:
            flag = "  (!) DIVERGENT" if r.get("divergent") else ""
            out.append(f"    [{_MARK[route]}] {r['tag']}  {r.get('role', '')}{flag}")
            if route == "review":
                out.append(f"             {r['reason']}")
    out.append("-" * 74)
    out.append(f"OVERALL: {verdict}   " + {
        "REVIEW": "(some role's route is unconfirmed — resolve before sourcing runs)",
        "PASS": "(every role routed cleanly; sourceable set is ready for freshness + sign-off)",
        "EMPTY": "(no FF&E roles to partition — an empty/stub file; nothing was routed, never a silent pass)"}[verdict])
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Partition an ffe-candidates.json into fabricated vs sourceable")
    ap.add_argument("ffe", help="path to ffe-candidates.json")
    ap.add_argument("--out", default=None, help="write the partition as JSON (default: none; --out - for stdout)")
    args = ap.parse_args()

    if not os.path.exists(args.ffe):
        print(f"ERROR: not found: {args.ffe}", file=sys.stderr)
        return 2
    verdict, rows, summary = check(args.ffe)
    print(format_report(rows, summary, verdict, os.path.basename(args.ffe)))
    if args.out:
        payload = {"source": os.path.basename(args.ffe), "verdict": verdict,
                   "summary": summary, "rows": rows}
        if args.out == "-":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
