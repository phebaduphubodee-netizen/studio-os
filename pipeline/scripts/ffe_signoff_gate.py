"""
ffe_signoff_gate.py — the OWNER-SIGN gate: a sourced pick enters the client BOM only once a
trained human has confirmed its live SKU (+ price).

Decision of record (docs/research/2026-07-11-furniture-sourcing-DR.md, finding (b)/(c) + TRACER):
no matching method auto-picks a product accurately enough (best domain model ~58% top-1), and
reliable SELECTION needs a TRAINED reviewer (89.5% vs a naive 32.5%). So sourcing is
candidate-generation + OWNER SIGNATURE, the same two-layer law as walls/glazing/facing: the machine
proposes a dimension-ranked shortlist; the owner signs the pick. This gate makes that signature
first-class and STICKY, mirroring placement_gate.py's confirmed[] ledger:

  * The signature lives in a `sourcing-signoff.json` ledger keyed by the candidate's CANONICAL KEY
    (retailer SKU / IKEA article #, else a composite of source+brand+model+dims — the DR's
    rot-proof anchor), NOT the ffe JSON's `verified` boolean. So a re-research that regenerates
    candidates cannot silently erase an owner's confirmation, and a bare flag-flip with no
    provenance is not mistaken for a real sign-off.
  * A valid sign requires a real `by` (NOT the OWNER-CONFIRM-PENDING template) + a `date` + the
    confirmed `sku` (the anti-link-rot anchor). `price_thb` is recorded but is a promotional
    snapshot the freshness lane (b) re-validates — its absence is advisory, not disqualifying.
  * LAST usable matching entry wins (the owner APPENDS corrections; a trailing typo never erases an
    earlier valid sign) — the same append-a-correction semantic as placement_gate.confirmed_rot.
  * A signature that binds NO current sourceable pick is an ORPHAN — surfaced as REVIEW (the owner
    signed a SKU the candidates no longer carry: a rotted link or a swapped pick), never dropped.

Only SOURCEABLE roles are gated (via ffe_partition_gate) — a fabricated built-in is workshop-made,
never catalog-sourced, so it has nothing to sign. resolve_verified() is the accessor the
sourceability moat consults so a ledger sign turns its verified-tier REVIEW into PASS with NO edit
to the ffe JSON (backward-compatible: no ledger -> the inline `verified` boolean is honoured as before).

How a human signs: `examples/sourcing-signoff.example.json` is the gold-standard template. Run
`--keys` to print each sourceable pick's canonical key (copy the composite one into a ledger `key`;
a retailer-SKU pick just needs {sku, by, date}). A sku is matched globally-unique and
dot/case/source-tolerant, so '003.540.63' vs '00354063' and 'IKEA' vs 'IKEA Thailand' all bind.

Pure logic throughout; check() adds file load. Mirrors sourceability_gate.py's shape.

    python ffe_signoff_gate.py <ffe-candidates.json> [sourcing-signoff.json]
    python ffe_signoff_gate.py <ffe-candidates.json> --keys      # list keys to sign
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

try:
    import ffe_partition_gate as _PART
except Exception:  # pragma: no cover - only if the sibling module is missing
    _PART = None

_PENDING = "OWNER-CONFIRM-PENDING"           # the unsigned template marker (mirrors confirmed_facade)
# A retailer id inside a product link: a dotted IKEA article (003.540.63) or a >=5-digit SKU run.
_ARTICLE_RE = re.compile(r"\b(\d{3}\.\d{3}\.\d{2})\b")
_SKU_RE = re.compile(r"(\d{5,})")


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")


def _norm_id(v):
    """A SKU / article / retailer id reduced to a bare alphanumeric token — dots, dashes, spaces and
    case stripped — so IKEA's dotted '003.540.63' and the undotted '00354063' URL run collapse to ONE
    token. A real retailer id is globally unique, so a signature binds on THIS, cross-source (an owner
    who writes source 'IKEA' vs the candidate's 'IKEA Thailand' still binds). None for empty."""
    if v in (None, ""):
        return None
    t = re.sub(r"[^a-z0-9]", "", str(v).lower())
    return t or None


def _retailer_id(link):
    """A stable retailer id parsed from a product URL, or None. Prefers a dotted IKEA article, else
    the LONGEST >=5-digit run in the path (the Index/HomePro numeric SKU). Query strings are dropped
    first so a tracking `?id=` never masquerades as the SKU."""
    if not isinstance(link, str) or not link.strip():
        return None
    path = link.split("?", 1)[0].split("#", 1)[0]
    m = _ARTICLE_RE.search(path)
    if m:
        return m.group(1)
    runs = _SKU_RE.findall(path)
    return max(runs, key=len) if runs else None


def canonical_key(cand):
    """The rot-proof human-readable DISPLAY/storage key for a candidate (DR finding (c)). Precedence:
      1. an explicit `canonical_key` field (verbatim), else `sku`/`article` (namespaced by source);
      2. a retailer id parsed from `link` (IKEA article # / Index SKU), namespaced by source;
      3. the composite fallback the DR prescribes when GTIN/SKU coverage is low: source|brand|model|WxDxH.
    The id in cases 1-2 is separator-normalised (via _norm_id) so a re-fetch or re-export yields the
    SAME key. MATCHING is NOT done on this string — it is done by cand_id / cand_composite, which are
    format- and source-tolerant; this is only what the report prints and the ledger `key` field copies."""
    if not isinstance(cand, dict):
        return None
    src = _slug(cand.get("source_th") or cand.get("manufacturer"))
    ck = cand.get("canonical_key")
    if isinstance(ck, (str, int)) and str(ck).strip():
        return str(ck).strip().lower()
    for f in ("sku", "article"):
        v = cand.get(f)
        if isinstance(v, (str, int)) and str(v).strip():
            return f"{src}:{_norm_id(v)}"
    rid = _retailer_id(cand.get("link"))
    if rid:
        return f"{src}:{_norm_id(rid)}"
    d = cand.get("dimensions_mm") or {}
    dims = "x".join(str(d[k]) for k in ("w", "d", "h") if d.get(k) not in (None, ""))
    return f"{src}|{_slug(cand.get('manufacturer'))}|{_slug(cand.get('model'))}|{dims}"


def cand_id(cand):
    """The globally-unique retailer id token (normalised) for a candidate, or None if it has only a
    composite key. A signature binds on THIS regardless of source spelling or article dot-format."""
    if not isinstance(cand, dict):
        return None
    for f in ("sku", "article"):
        if str(cand.get(f) or "").strip():
            return _norm_id(cand.get(f))
    rid = _retailer_id(cand.get("link"))
    return _norm_id(rid) if rid else None


def cand_composite(cand):
    """The composite key for a SKU-less candidate (needs the full source|brand|model|dims namespace —
    there is no unique id), or None when the candidate HAS an id (bind by id instead) OR when the
    composite would be DEGENERATE (no model AND no dims). A degenerate composite must NOT be a bindable
    bucket: otherwise one signature would bind every unnamed pick from a source. Such a candidate stays
    'pending' until it carries a model / dim / SKU, rather than being silently signed by a stray key."""
    if not isinstance(cand, dict) or cand_id(cand) is not None:
        return None
    d = cand.get("dimensions_mm") or {}
    has_dim = any(d.get(k) not in (None, "") for k in ("w", "d", "h"))
    if not str(cand.get("model") or "").strip() and not has_dim:
        return None
    return canonical_key(cand)


def _entry_id(entry):
    """The normalised retailer id an entry binds, or None. A bare `sku`/`article`, or the id tail of a
    'source:id' `key` (NOT a composite '…|…' key). Cross-source by construction (a real id is unique)."""
    if not isinstance(entry, dict):
        return None
    for f in ("sku", "article"):
        if str(entry.get(f) or "").strip():
            return _norm_id(entry.get(f))
    k = str(entry.get("key") or "").strip()
    if k and "|" not in k:
        return _norm_id(k.split(":", 1)[1] if ":" in k else k)
    return None


def _entry_composite(entry):
    """The composite key an entry binds: an explicit '…|…' `key` (verbatim, lower-cased), else
    re-derived from the entry's own source/model/dims. None if it carries no composite anchor. Copying
    a SKU-less pick's printed composite key into `key` is how such a pick is signed without ffe edits."""
    if not isinstance(entry, dict):
        return None
    k = str(entry.get("key") or "").strip().lower()
    if "|" in k:
        return k
    if str(entry.get("model") or "").strip() or entry.get("dimensions_mm"):
        ck = canonical_key(entry)
        return ck if (ck and "|" in ck) else None
    return None


def entry_anchor(entry):
    """A readable anchor for report/orphan messages: the entry's id, else its composite, else a hint."""
    return _entry_id(entry) or _entry_composite(entry) or "(no key/sku)"


def _cand_source(cand):
    for f in ("source_th", "manufacturer"):
        if str((cand or {}).get(f) or "").strip():
            return _slug(cand.get(f))
    return ""


def _entry_source(entry):
    """The source slug an entry declares — an explicit `source`/`source_th`/`manufacturer`, else the
    namespace of a 'source:id' `key`. '' when the entry names no source."""
    for f in ("source", "source_th", "manufacturer"):
        if str((entry or {}).get(f) or "").strip():
            return _slug(entry.get(f))
    k = str((entry or {}).get("key") or "").strip()
    if ":" in k and "|" not in k:
        return _slug(k.split(":", 1)[0])
    return ""


def _source_compatible(cs, es):
    """True if a candidate source slug and an entry source slug may share an ID match: either side
    empty (the owner omitted source and trusts the globally-unique id), or one contains the other
    ('ikea' vs 'ikea-thailand'). This RE-TIGHTENS the cross-source id match just enough to block a
    coincidental cross-RETAILER id collision (an IKEA 5-digit code == an Index one) from binding a
    product the owner never signed — the one fail-toward-PASS vector, while keeping the abbreviation
    tolerance the review asked for."""
    if not cs or not es:
        return True
    return cs in es or es in cs


def sign_status(entry):
    """Classify a ledger entry: 'valid' | 'pending' | 'incomplete' | 'inert'.
      inert      — not a dict (carries no signature intent at all).
      pending    — the OWNER-CONFIRM-PENDING template, or no real `by`: machine-INERT, never signs.
      incomplete — a real signer but missing the SKU anchor (no `sku`/`article`/`key`, the anti-rot
                   anchor that is the whole point) or missing the `date` -> surfaced, cannot bind.
      valid      — real `by` + a `date` + a confirmed sku/article/key. price_thb is advisory (a
                   promotional snapshot the freshness lane re-validates), so its absence never
                   disqualifies. Only a 'valid' entry ever binds a candidate (resolve_signoff)."""
    if not isinstance(entry, dict):
        return "inert"
    by = str(entry.get("by") or "").strip()
    if not by or _PENDING in by:
        return "pending"
    has_id = any(str(entry.get(f) or "").strip() for f in ("sku", "article", "key"))
    if not has_id or not str(entry.get("date") or "").strip():
        return "incomplete"
    return "valid"


def load_signoff(led):
    """Pull the `signed` list out of a parsed sourcing-signoff ledger dict; drop non-dict typos.
    Accepts either {"signed": [...]} or a bare list. [] on anything odd (mirrors
    placement_gate.load_confirmed)."""
    if isinstance(led, list):
        return [e for e in led if isinstance(e, dict)]
    if not isinstance(led, dict):
        return []
    signed = led.get("signed", [])
    return [e for e in signed if isinstance(e, dict)] if isinstance(signed, list) else []


def resolve_signoff(cand, signoff):
    """The VALID owner-signed entry that binds this candidate, or None. A candidate WITH a retailer id
    binds by normalised id (cross-source, dot-tolerant — fixes the IKEA '003.540.63' vs '00354063'
    split and an abbreviated `source`); a SKU-less candidate binds by its composite key; a degenerate
    candidate (cand_composite None) binds nothing. LAST usable matching entry wins (append-a-
    correction). Only 'valid' entries bind — pending/incomplete/inert can neither sign nor erase an
    earlier valid sign (last-USABLE-wins, mirrors placement_gate.confirmed_rot)."""
    cid = cand_id(cand)
    ccomp = cand_composite(cand)
    if cid is None and ccomp is None:
        return None
    cs = _cand_source(cand)
    best = None
    for e in signoff or []:
        if sign_status(e) != "valid":
            continue
        if cid is not None and _entry_id(e) == cid and _source_compatible(cs, _entry_source(e)):
            best = e
        elif ccomp is not None and _entry_composite(e) == ccomp:
            best = e
    return best


def resolve_verified(cand, signoff=None):
    """Effective verified state of a candidate + its provenance — the accessor the sourceability
    moat consults. (True, prov) when a VALID ledger signature binds it (prov.source='ledger') OR the
    ffe JSON already marks it verified:true (prov.source='inline', backward-compatible). (False, None)
    otherwise. A ledger sign therefore flips a verified:false pick to verified WITHOUT editing the
    ffe JSON, and with no ledger the legacy inline boolean is honoured exactly as before."""
    e = resolve_signoff(cand, signoff)
    if e is not None:
        return True, {"source": "ledger", "by": e.get("by"), "date": e.get("date"),
                      "sku": e.get("sku") or e.get("article") or e.get("key"),
                      "price_thb": e.get("price_thb")}
    # bool(), NOT `is True`: legacy inline verified may be 1 / "true" — the no-ledger path in
    # sourceability_gate uses bool(), so this must too, or merely auto-loading a (non-binding) ledger
    # would flip such a pick's verdict. (Fixes the reviewer's truthy-non-True back-compat break.)
    if bool(cand.get("verified")):
        return True, {"source": "inline"}
    return False, None


def _sourceable_roles(ffe_doc):
    """Roles routed to the sourcing queue. Uses the partition gate when available; falls back to a
    csi-division read so this gate still runs if the sibling module is absent."""
    items = (ffe_doc or {}).get("items", []) or []
    if _PART is not None:
        rows = [_PART.classify_role(r) for r in items]
        return [(r, row) for r, row in zip(items, rows) if row["route"] == "sourceable"]
    out = []
    for r in items:
        c = next((x for x in (r.get("candidates") or []) if x.get("selected")),
                 (r.get("candidates") or [None])[0])
        div = (str((c or {}).get("csi") or "")[:2])
        if div in {"10", "11", "12", "22", "23", "26", "27"}:
            out.append((r, {"tag": r.get("tag"), "route": "sourceable"}))
    return out


def report(ffe_doc, signoff):
    """(rows, verdict) over the SOURCEABLE selected picks. Per pick:
       signed          — a valid ledger signature binds it. PASS-eligible.
       verified_inline — ffe verified:true but NO ledger signature (a flag with no audit trail):
                         honoured, but advised to add a signature. PASS-eligible, flagged.
       client_ref      — a client-supplied reference item (e.g. the client's own TV): still needs a
                         human acknowledgement (kept as a REVIEW row so it is not silently excused —
                         auto-excusing on a substring would be its own flattering hole), but LABELLED
                         so no one hunts a SKU the studio isn't buying.
       pending         — verified:false and unsigned: the owner has not confirmed the live SKU. REVIEW.
       no_pick         — the sourceable role has no selected candidate to sign. REVIEW.
    Plus TWO ledger-side surfaces (a signature must never silently drop): ORPHANS (a valid sign that
    binds no current pick — rotted key / swapped pick) and MALFORMED (an incomplete sign — a real
    signer missing the sku/date anchor). Both -> REVIEW. Verdict:
       UNWIRED — there is NO sourceable pick to gate (all-fabricated / empty / wrong file) AND no
                 ledger surface: nothing was confirmed, so NEVER a vacuous green PASS (mirrors
                 sourceability_gate's zero-sourced discipline).
       REVIEW  — any pending / no_pick / client_ref pick, or any orphan / malformed sign.
       PASS    — every sourceable pick is signed or inline-verified and every sign binds cleanly."""
    rows = []
    n_picks = 0
    for role, prow in _sourceable_roles(ffe_doc):
        n_picks += 1
        cands = role.get("candidates") or []
        sel = [c for c in cands if c.get("selected")]
        cand = sel[0] if sel else None
        tag, rolename = role.get("tag"), role.get("role")
        if cand is None:
            rows.append({"tag": tag, "role": rolename, "status": "no_pick",
                         "detail": "sourceable role with no selected candidate — pick one before sign-off"})
            continue
        key = canonical_key(cand)
        verified, prov = resolve_verified(cand, signoff)
        label = f"{cand.get('manufacturer', '?')} {cand.get('model', '?')}  [{key}]"
        if prov and prov.get("source") == "ledger":
            price = f", price {prov['price_thb']}" if prov.get("price_thb") else " (price uncaptured — freshness re-validates)"
            rows.append({"tag": tag, "role": rolename, "status": "signed", "key": key,
                         "detail": f"{label} — signed by {prov.get('by')} on {prov.get('date')}{price}"})
        elif verified:
            rows.append({"tag": tag, "role": rolename, "status": "verified_inline", "key": key,
                         "detail": f"{label} — verified:true inline (no signature; add one for the audit trail)"})
        elif prow.get("client_supplied"):
            rows.append({"tag": tag, "role": rolename, "status": "client_ref", "key": key,
                         "detail": f"{label} — CLIENT-SUPPLIED reference (client brings it; the studio is not "
                                   "buying it). Acknowledge/sign to clear, or exclude from the client BOM."})
        else:
            rows.append({"tag": tag, "role": rolename, "status": "pending", "key": key,
                         "detail": f"{label} — awaiting owner sign-off (confirm live SKU + price)"})

    # ledger-side surfaces. 'Bound' is computed with the SAME id+source / composite rule resolve_signoff
    # uses (so an entry that binds a pick — even a superseded earlier correction — is never mis-reported
    # orphan, and the source-compat guard is applied identically here).
    picks = []
    for role, _prow in _sourceable_roles(ffe_doc):
        c = next((x for x in (role.get("candidates") or []) if x.get("selected")), None)
        if c is not None:
            picks.append((cand_id(c), _cand_source(c), cand_composite(c)))

    def _binds_a_pick(e):
        eid, es, ecomp = _entry_id(e), _entry_source(e), _entry_composite(e)
        for cid, cs, ccomp in picks:
            if cid is not None and eid == cid and _source_compatible(cs, es):
                return True
            if ccomp is not None and ecomp is not None and ecomp == ccomp:
                return True
        return False

    ledger_rows = []
    for e in signoff or []:
        st = sign_status(e)
        if st == "valid" and not _binds_a_pick(e):
            ledger_rows.append({"tag": "—", "status": "orphan", "key": entry_anchor(e),
                                "detail": f"signature by {e.get('by')} ({entry_anchor(e)}) binds no current "
                                          "sourceable pick — rotted key or a swapped pick; re-confirm"})
        elif st == "incomplete":                       # a real attempt missing its anchor -> SURFACE it
            ledger_rows.append({"tag": "—", "status": "malformed", "key": entry_anchor(e),
                                "detail": f"malformed signature by {e.get('by') or '?'} ({entry_anchor(e)}) — "
                                          "missing sku/date anchor; cannot bind. Add sku + date to activate."})

    verdict = "PASS"
    if n_picks == 0 and not ledger_rows:
        verdict = "UNWIRED"                            # nothing sourceable to gate -> never a green PASS
    elif any(r["status"] in ("pending", "no_pick", "client_ref") for r in rows) or ledger_rows:
        verdict = "REVIEW"
    return rows + ledger_rows, verdict


def load_signoff_beside(ffe_path):
    """Locate + load the signoff ledger beside an ffe-candidates.json: an explicit
    doc['sourcing_signoff'] path first, else 'sourcing-signoff.json' in the same dir. Returns the
    `signed` list ([] if none / malformed — honest, never a crash)."""
    base = os.path.dirname(os.path.abspath(ffe_path))
    try:
        doc = json.load(open(ffe_path, encoding="utf-8"))
    except (ValueError, OSError):
        doc = {}
    cands = []
    ref = doc.get("sourcing_signoff") if isinstance(doc, dict) else None
    if ref:
        cands += [ref, os.path.join(base, os.path.basename(ref))]
    cands.append(os.path.join(base, "sourcing-signoff.json"))
    for c in cands:
        if c and os.path.exists(c):
            try:
                return load_signoff(json.load(open(c, encoding="utf-8")))
            except (ValueError, OSError):
                return []
    return []


def check(ffe_path):
    """Load an ffe-candidates.json + its adjacent sourcing-signoff.json and gate. Returns
    (verdict, rows)."""
    doc = json.load(open(ffe_path, encoding="utf-8"))
    signoff = load_signoff_beside(ffe_path)
    rows, verdict = report(doc, signoff)
    return verdict, rows


_MARK = {"signed": "SIGNED", "verified_inline": "INLINE", "pending": "PEND  ",
         "no_pick": "NOPICK", "client_ref": "CLIENT", "orphan": "ORPHAN", "malformed": "MALFRM"}


def format_report(rows, verdict, name):
    out = ["=" * 74,
           "FF&E OWNER-SIGN GATE — has a trained human confirmed each sourced pick's live SKU?",
           "=" * 74, f"### {name}   -> {verdict}"]
    for r in rows:
        out.append(f"    [{_MARK.get(r['status'], r['status']):6}] {r.get('tag', '—')}: {r['detail']}")
    if not rows:
        out.append("    (no sourceable picks to sign — all fabricated / nothing selected)")
    out.append("-" * 74)
    out.append(f"OVERALL: {verdict}   " + {
        "REVIEW": "(a sourced pick is unsigned/unpicked, or a signature has detached or is malformed — confirm before the client BOM)",
        "PASS": "(every sourced pick is owner-signed or inline-verified; sign-offs all bind)",
        "UNWIRED": "(no sourceable pick to gate here — nothing was confirmed; never a silent pass)"}[verdict])
    return "\n".join(out)


def print_keys(ffe_doc):
    """List each SOURCEABLE selected pick's canonical key so an owner can copy it into a ledger
    entry's `key` field — the reliable way to sign a SKU-less (composite-keyed) pick without editing
    the ffe JSON. The retailer-id picks can instead be signed with just {sku:<id>}."""
    out = ["# canonical keys for the sourcing sign-off ledger (copy `key` into sourcing-signoff.json)"]
    for role, _prow in _sourceable_roles(ffe_doc):
        c = next((x for x in (role.get("candidates") or []) if x.get("selected")), None)
        if c is None:
            continue
        cid = cand_id(c)
        anchor = f"sku {cid}" if cid else f'key "{canonical_key(c)}"'
        out.append(f"  {role.get('tag'):10} {canonical_key(c)}   (sign with: {anchor})")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Owner sign-off gate over an ffe-candidates.json")
    ap.add_argument("ffe", help="path to ffe-candidates.json")
    ap.add_argument("signoff", nargs="?", default=None, help="path to sourcing-signoff.json (default: adjacent)")
    ap.add_argument("--keys", action="store_true", help="list each sourceable pick's canonical key for signing")
    args = ap.parse_args()
    if not os.path.exists(args.ffe):
        print(f"ERROR: not found: {args.ffe}", file=sys.stderr)
        return 2
    doc = json.load(open(args.ffe, encoding="utf-8"))
    if args.keys:
        print(print_keys(doc))
        return 0
    signoff = load_signoff(json.load(open(args.signoff, encoding="utf-8"))) if args.signoff else load_signoff_beside(args.ffe)
    rows, verdict = report(doc, signoff)
    print(format_report(rows, verdict, os.path.basename(args.ffe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
