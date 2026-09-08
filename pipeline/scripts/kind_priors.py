"""kind_priors.py -- deterministic per-kind size/aspect bands for the benchmark lane.

    python kind_priors.py --derive <out.json> <gt-dir> [<gt-dir> ...] \
        [--source NAME] [--max-dispersion X]

Bands are derived from TRAIN-split gt.json only (units=='mm' files), scored on the test
split -- legitimate train/test separation. suggest_kind emits a kind ONLY when the
footprint falls inside exactly ONE kind's band (unique membership); any ambiguity
(0 or >=2 candidates) returns None and the element stays kind-less. The benchmark
scores a kind-less matched pair as WRONG (norm_kind(None)->'' in benchmark_reader),
never skipped -- unreported is the honest failure mode, a guess is a false-accept.

MULTI-CORPUS (2026-07-14): more than one priors artifact may be live at once (FloorPlanCAD
drawn-symbol bands + Structured3D real-furniture bands). Every consumer takes ONE doc or a
LIST of docs (as_docs normalizes). Each doc keeps its OWN unique-membership structure --
corpora are never merged into one candidate set (a drawn-symbol band and a real-furniture
band are different populations; pooling them would manufacture ambiguity in one direction
and fake uniqueness in the other). Corroboration across docs is STRICTER than any single
doc: at least one doc must uniquely agree AND no doc may uniquely disagree.

--max-dispersion X (derive, opt-in): REFUSE any kind whose 10-90 quantile ratio on either
footprint side exceeds X -- such a class is not ONE size population (measured on
Structured3D: 'sofa' spans 22.7x on the short side because instance labels include cushion/
section fragments; 'cabinet' spans base units to full-height closets). A refused kind is
recorded in excluded_degenerate with its ratios -- dropped-and-counted, never silent. The
flag is opt-in and OFF by default so the committed FloorPlanCAD artifact stays
byte-reproducible.

BENCHMARK / SUGGESTION LANE ONLY: identity in owner projects is owner-signed semantic
truth. This module must never be imported by placement_gate, gen_floor2_v4_specs,
raster_overlay, or build_floor.

SCOPE (v2): SIZE/ASPECT bands, PLUS an optional per-kind CURVE signature that only
DISAMBIGUATES a size tie -- it never overrides a unique size hit and never guesses. gt.json
elements carry no curve field, so a grounded curve signature is derived from a TRAIN-side
reader run (derive_curve_priors.py) that pairs each pred element's `curve` bool with its
IoU-matched GT kind; merge_curve_signatures() folds the per-kind curve fraction into a
size-priors doc. A kind with < MIN_CURVE_SUPPORT matched train pairs gets NO signature
(curve stays unusable for it -- honest, never fabricated). suggest_kind(curve=...) then drops
a size-candidate ONLY when its train curve class is CONFIDENTLY OPPOSITE the element's curve
flag; a tie resolves to a kind only when that leaves exactly one candidate (else unreported).
The probe finding this implements: chair/toilet are ~100% curved, elevator ~0% -- so curve
breaks the small-furniture size overlap (chair vs table) that left F1 at 0.4% on size alone.
"""
import glob
import json
import os
import sys
from datetime import date

from floorplancad_adapter import ADAPTER_VERSION

SCHEMA = "interior-ai/kind-priors@0.2"       # @0.2 adds the optional per-kind curve signature
KNOWN_SCHEMAS = {"interior-ai/kind-priors@0.1", SCHEMA}   # @0.1 (size-only) still loads
Q_LO, Q_HI = 0.10, 0.90
PAD_MM = 50.0            # covers cluster-AABB dilation: pred dims are morphology bboxes
                        # rounded to int mm, +-2*res ~ +-12 mm typical
ASPECT_PAD = 1.15
MIN_SUPPORT = 50
# curve signature (v2): thresholds are on a kind's TRAIN curve fraction (matched pred `curve`
# bool vs GT kind). A kind counts as CURVED >= HI, BOXY <= LO, else AMBIGUOUS (never used to
# disambiguate). Conservative gap between LO and HI so a marginal kind stays out of the decision.
CURVE_HI = 0.60
CURVE_LO = 0.20
MIN_CURVE_SUPPORT = 20  # matched train pairs a kind needs before its curve signature is trusted


def _quantile(sorted_vals, q):
    """Positional quantile of a PRE-SORTED ascending list (the sorted_vals name is the
    contract, not a hint -- quantiling an unsorted list yields garbage bands)."""
    return sorted_vals[int(round(q * (len(sorted_vals) - 1)))]


def derive(gt_dirs, min_support=MIN_SUPPORT, source="floorplancad", max_dispersion=None):
    """Per-kind size/aspect bands from TRAIN gt.json (units=='mm' only). Openings are
    NEVER sampled (door widths ~999 mm would collide with furniture bands); svg-unit
    files are skipped AND counted (their raw dims are ~100x off).

    source     -- provenance prefix (which corpus these bands describe).
    max_dispersion -- opt-in single-population gate: refuse (into excluded_degenerate)
    any kind whose raw lo_q90/lo_q10 or hi_q90/hi_q10 exceeds it. None (default) keeps
    derive byte-identical to the pre-flag behaviour (no new meta key, no new doc key) so
    the committed FloorPlanCAD artifact remains reproducible."""
    samples = {}                    # kind -> list of (lo, hi, aspect)
    n_files_total = n_files_mm = n_files_skipped_units = 0
    n_elements_sampled = n_elements_malformed = n_elements_unlabelled = 0
    adapters_seen = set()           # gt-file self-declared adapter versions (non-FPC provenance)
    for d in gt_dirs:
        for fp in sorted(glob.glob(os.path.join(d, "*.gt.json"))):
            n_files_total += 1
            with open(fp, encoding="utf-8") as fh:
                doc = json.load(fh)
            if (doc.get("meta") or {}).get("units") != "mm":
                n_files_skipped_units += 1          # raw svg-unit dims poison bands ~100x
                continue
            n_files_mm += 1
            a = (doc.get("meta") or {}).get("adapter")
            if a:
                adapters_seen.add(str(a))
            for e in doc.get("elements", []):       # elements ONLY, never openings
                if not isinstance(e, dict):
                    n_elements_malformed += 1
                    continue
                if e.get("kind") is None:
                    # UNLABELLED, not malformed (review finding 2026-07-14: 371k Structured3D
                    # decor objects carry no kind by design -- calling them 'malformed'
                    # misstated corpus health). Also stops a literal kind=None from being
                    # sampled as a band key.
                    n_elements_unlabelled += 1
                    continue
                try:
                    w, dd = float(e["w"]), float(e["d"])
                    kind = e["kind"]
                except (KeyError, TypeError, ValueError):
                    n_elements_malformed += 1
                    continue
                if w <= 0 or dd <= 0:
                    n_elements_malformed += 1
                    continue
                lo, hi = sorted((w, dd))
                samples.setdefault(kind, []).append((lo, hi, hi / lo))
                n_elements_sampled += 1

    date_str = str(date.today())
    # provenance adapter part: the FPC prefix keeps the historical ADAPTER_VERSION import
    # (byte-compat with the committed artifact); any other source cites the gt files' own
    # self-declared adapter string(s).
    adapter_str = (ADAPTER_VERSION if source == "floorplancad"
                   else ("+".join(sorted(adapters_seen)) or "unknown-adapter"))
    kinds, excluded, degenerate = {}, {}, {}
    for kind in sorted(samples):
        rows = samples[kind]
        n = len(rows)
        if n < min_support:
            excluded[kind] = n
            continue
        # THREE separate lists, each sorted ascending BEFORE quantiling (_quantile indexes
        # positionally and assumes pre-sorted input)
        los = sorted(r[0] for r in rows)
        his = sorted(r[1] for r in rows)
        asp = sorted(r[2] for r in rows)
        lo_q10, lo_q90 = _quantile(los, Q_LO), _quantile(los, Q_HI)
        hi_q10, hi_q90 = _quantile(his, Q_LO), _quantile(his, Q_HI)
        as_q10, as_q90 = _quantile(asp, Q_LO), _quantile(asp, Q_HI)
        if max_dispersion is not None:
            lo_disp = (lo_q90 / lo_q10) if lo_q10 > 0 else float("inf")
            hi_disp = (hi_q90 / hi_q10) if hi_q10 > 0 else float("inf")
            if max(lo_disp, hi_disp) > max_dispersion:
                # not ONE size population (fragments / mixed class) -- a band over it would
                # both false-flag and destroy every other kind's unique membership.
                degenerate[kind] = {"n": n, "lo_disp": round(lo_disp, 2),
                                    "hi_disp": round(hi_disp, 2)}
                continue
        provenance = (f"{source} "
                      + "+".join(os.path.basename(os.path.normpath(g)) for g in gt_dirs)
                      + f", units=mm gt.json, n={n} instances, "
                      + f"adapter {adapter_str}, derived {date_str}")
        kinds[kind] = {
            "n": n,
            "lo_mm": [lo_q10 - PAD_MM, lo_q90 + PAD_MM],
            "hi_mm": [hi_q10 - PAD_MM, hi_q90 + PAD_MM],
            "aspect": [max(1.0, as_q10 / ASPECT_PAD), as_q90 * ASPECT_PAD],
            "raw": {"lo_q10": lo_q10, "lo_q90": lo_q90, "hi_q10": hi_q10,
                    "hi_q90": hi_q90, "aspect_q10": as_q10, "aspect_q90": as_q90},
            "provenance": provenance,
        }
    params = {"q_lo": Q_LO, "q_hi": Q_HI, "pad_mm": PAD_MM,
              "aspect_pad": ASPECT_PAD, "min_support": min_support}
    doc = {
        "schema": SCHEMA,
        "meta": {
            "derived_from": [os.path.abspath(d) for d in gt_dirs],
            "date": date_str,
            "n_files_total": n_files_total,
            "n_files_mm": n_files_mm,
            "n_files_skipped_units": n_files_skipped_units,
            "n_elements_sampled": n_elements_sampled,
            "n_elements_malformed": n_elements_malformed,
            "params": params,
        },
        "kinds": kinds,
        "excluded_low_support": excluded,
    }
    if max_dispersion is not None:
        # both keys appear ONLY when the gate ran (byte-compat: default derive output is
        # unchanged; an empty dict here still says "the gate ran and refused nothing")
        params["max_dispersion"] = max_dispersion
        doc["excluded_degenerate"] = degenerate
    if n_elements_unlabelled:
        # only-when-nonzero keeps the fully-labelled FloorPlanCAD artifact byte-identical
        doc["meta"]["n_elements_unlabelled"] = n_elements_unlabelled
    if source != "floorplancad":
        doc["meta"]["source"] = source
    return doc


def _curve_class(band):
    """CURVED / BOXY from a kind's train curve signature, or None (ambiguous / absent /
    under-supported). None means curve gives no confident evidence for this kind."""
    c = band.get("curve")
    if not c or c.get("n", 0) < MIN_CURVE_SUPPORT:
        return None
    f = c.get("frac")
    if f is None:
        return None
    if f >= CURVE_HI:
        return "curved"
    if f <= CURVE_LO:
        return "boxy"
    return None


def suggest_kind(w_mm, d_mm, priors, curve=None):
    """Emit a kind ONLY when size+curve resolve to exactly ONE. A UNIQUE size-band hit emits
    directly (curve never overrides it -- back-compatible with the size-only lane). On a size
    TIE (>=2 candidates), if the element's `curve` bool is known, drop every candidate whose
    train curve class is CONFIDENTLY OPPOSITE (a curved element drops BOXY kinds, a boxy element
    drops CURVED kinds); if that leaves exactly one, emit it, else None. Any residual ambiguity,
    or a non-positive/non-numeric dim, returns None -- the element stays kind-less (scored WRONG,
    never a guess). curve=None (no curve info) reproduces the size-only behaviour exactly."""
    try:
        w, dd = float(w_mm), float(d_mm)
    except (TypeError, ValueError):
        return None
    if w <= 0 or dd <= 0:
        return None
    lo, hi = sorted((w, dd))
    aspect = hi / lo
    cands = [k for k, b in sorted(priors["kinds"].items())
             if b["lo_mm"][0] <= lo <= b["lo_mm"][1]
             and b["hi_mm"][0] <= hi <= b["hi_mm"][1]
             and b["aspect"][0] <= aspect <= b["aspect"][1]]
    if len(cands) == 1:
        return cands[0]                               # unique size membership IS the confidence rule
    if len(cands) >= 2 and curve is not None:
        opposite = "boxy" if curve else "curved"      # a curved element cannot be a BOXY kind
        kept = [k for k in cands if _curve_class(priors["kinds"][k]) != opposite]
        if len(kept) == 1:
            return kept[0]                            # curve UNIQUELY resolved the size tie
    return None


def as_docs(priors):
    """Normalize a priors argument to a LIST of docs: None -> [], one doc dict -> [doc],
    list/tuple -> list. STRICT on shape: any entry that is not a dict with a dict 'kinds'
    raises ValueError -- a dead/garbage doc must surface as an ERROR in the caller's
    coverage line (self_audit review finding 2026-07-13), never dissolve into a silently
    smaller doc set."""
    if priors is None:
        return []
    entries = list(priors) if isinstance(priors, (list, tuple)) else [priors]
    for d in entries:
        if not (isinstance(d, dict) and isinstance(d.get("kinds"), dict)):
            raise ValueError(f"not a usable kind-priors doc: {type(d).__name__} "
                             f"(schema {d.get('schema')!r})" if isinstance(d, dict)
                             else f"not a usable kind-priors doc: {type(d).__name__}")
    return entries


def build_prior_context(pieces, priors):
    """CORROBORATION-lane injector: {piece_name: {"prior_kind": <suggestion>}} for
    confidence.assess_room(context=...) -- the "kind matching a UNIQUE prior band" corroboration
    tier (0.70) documented there, now actually fed.

    `priors` = one doc OR a list of docs (as_docs). Each doc is consulted with its OWN
    unique-membership structure. The cross-doc rule is STRICTLY tighter than any single doc:
      * CORROBORATE (inject the claimed string) only when >=1 doc uniquely agrees AND no doc
        uniquely disagrees -- an independent corpus actively suggesting a DIFFERENT kind is
        counter-evidence, and counter-evidence must never be outvoted into a 0.70
        (single-doc behaviour is unchanged: one doc cannot both agree and disagree).
      * otherwise the first unique disagreeing suggestion (doc order = caller's discovery
        order, deterministic) is injected raw and visible; ambiguity everywhere injects
        NOTHING.

    Semantics per piece (conservative -- ambiguity injects NOTHING, and there is no downgrade
    path: a disagreeing suggestion is injected raw and visible, but confidence's equality check
    simply reads it as not-corroborating):
      * suggestion = suggest_kind(w, d, doc) per doc -- the CORPUS-vocabulary unique-band hit,
        or None.
      * vocabulary bridge: agreement is judged through the PRIOR lane's map
        (anomaly_flags.PRIOR_KIND_ALIASES), so a claimed 'armchair' whose footprint uniquely hits
        the corpus 'chair' band IS agreement -> the CLAIMED string is injected (confidence
        compares by equality and must read this as corroboration).
      * a claimed kind in anomaly_flags.PRIOR_EXEMPT_KINDS is NEVER corroborated (repo semantics
        broader than the corpus symbol class -- corroborating repo 'cabinet' off the freestanding
        corpus cabinet band is the same population error as false-flagging it): no injection.
      * CASE: decisions here are made on the LOWERCASED claimed kind, because the downstream
        equality check (confidence._kind_confidence) lowercases both sides -- deciding
        case-sensitively would let a hand-typed 'Cabinet' slip past the exemption as a
        "disagreement" injection and still read as corroborated downstream (review finding,
        2026-07-13). AGREEMENT is a suggestion equal to the band key OR to the lowercased
        claim itself -- a doc whose own vocabulary carries the claimed kind (a future corpus
        keyed 'armchair' rather than alias-target 'chair') agrees by saying the claim's own
        name (review finding, 2026-07-14: routing that through the disagreement branch
        injected a string that lowercase-equals the claim and read as corroborated). With
        both names counted as agreement, the disagreement branch provably injects only
        suggestions that differ from the lowercased claim.
      * unnamed pieces are skipped (context is keyed by name); duplicate names collapse to the
        LAST piece walked (callers keep names unique -- flag_localization relies on that already).

    Pure: dicts in -> dict out; no disk, no owner. `pieces` = iterable of piece dicts (callers
    typically pass [p for p, _sub in confidence._all_pieces(spec)])."""
    import anomaly_flags as AF     # lazy: keeps this module import-light for the reader lane

    docs = as_docs(priors)         # raises on a garbage doc -> caller reports ERROR, not WIRED
    ctx = {}
    for piece in pieces:
        if not isinstance(piece, dict):
            continue
        name = piece.get("name")
        if name is None:
            continue
        sugs = [suggest_kind(piece.get("w"), piece.get("d"), d) for d in docs]
        if all(s is None for s in sugs):
            continue
        kind = piece.get("kind")
        k_low = kind.strip().lower() if isinstance(kind, str) else None
        if k_low and k_low in AF.PRIOR_EXEMPT_KINDS:
            continue                                   # exempt: never corroborate, never inject
        band_key = AF.prior_band_kind(k_low) if k_low else None
        agree_names = {band_key, k_low} - {None}          # a doc may speak either vocabulary
        agrees = any(s in agree_names for s in sugs if s is not None)
        disagrees = [s for s in sugs if s is not None and s not in agree_names]
        if agrees and not disagrees:
            ctx[str(name)] = {"prior_kind": kind.strip()}   # agreement (exact or via alias)
        elif disagrees:
            # >=1 doc uniquely suggests something else (or the piece is kind-less):
            # visible disagreement -- equality fails downstream, never corroborates
            ctx[str(name)] = {"prior_kind": disagrees[0]}
    return ctx


def accumulate_curve(pairs):
    """(gt_kind, pred_curve_bool) iterable -> {kind: {"n": int, "curve": int}}. Pure; the
    reader-run/matching that produces the pairs lives in derive_curve_priors.py (no reader
    import here -- svg_plan_reader imports THIS module)."""
    stats = {}
    for k, cv in pairs:
        if not k:
            continue
        row = stats.setdefault(k, {"n": 0, "curve": 0})
        row["n"] += 1
        if cv:
            row["curve"] += 1
    return stats


def merge_curve_signatures(priors, curve_stats, min_support=MIN_CURVE_SUPPORT, source=None):
    """Return a NEW priors doc (schema @0.2) with a per-kind curve signature added wherever
    train support clears min_support. Kinds below support get NO signature -- curve stays
    unusable for them (honest, never fabricated). Pure: no reader run, no I/O."""
    doc = json.loads(json.dumps(priors))              # deep copy, no aliasing into the input
    doc["schema"] = SCHEMA
    added = 0
    for k, band in doc["kinds"].items():
        st = curve_stats.get(k)
        if st and st["n"] >= min_support and st["n"] > 0:
            band["curve"] = {"frac": round(st["curve"] / st["n"], 3), "n": st["n"],
                             "curve_n": st["curve"]}
            added += 1
        else:
            band.pop("curve", None)                   # re-merge must not keep a stale signature
    doc.setdefault("meta", {})["curve"] = {
        "source": source, "min_support": min_support, "curve_hi": CURVE_HI, "curve_lo": CURVE_LO,
        "kinds_with_signature": added,
        "kinds_curve_supported": sorted(k for k, st in curve_stats.items() if st["n"] >= min_support),
        "n_pairs": sum(st["n"] for st in curve_stats.values()),
    }
    return doc


def load(path):
    """Load a priors doc, failing LOUDLY at startup (never a per-sheet error row) if the
    file is not a kind-priors artifact. Accepts @0.1 (size-only) and @0.2 (curve-capable)."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("schema") not in KNOWN_SCHEMAS:
        raise SystemExit(f"not a kind-priors file: {path} (schema {doc.get('schema')!r})")
    return doc


def main(argv):
    if len(argv) >= 4 and argv[1] == "--derive":
        rest = argv[2:]
        source, max_dispersion = "floorplancad", None
        if "--source" in rest:
            i = rest.index("--source")
            if i + 1 >= len(rest):
                raise SystemExit(__doc__)        # flag without a value: usage, not a traceback
            source = rest[i + 1]
            del rest[i:i + 2]
        if "--max-dispersion" in rest:
            i = rest.index("--max-dispersion")
            if i + 1 >= len(rest):
                raise SystemExit(__doc__)
            try:
                max_dispersion = float(rest[i + 1])
            except ValueError:
                raise SystemExit(__doc__)
            del rest[i:i + 2]
        if len(rest) < 2:
            raise SystemExit(__doc__)
        out, gt_dirs = rest[0], rest[1:]
        doc = derive(gt_dirs, source=source, max_dispersion=max_dispersion)
        parent = os.path.dirname(out)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, out)
        m = doc["meta"]
        print(f"wrote {out}")
        unl = (f" unlabelled {m['n_elements_unlabelled']}"
               if "n_elements_unlabelled" in m else "")
        print(f"schema {doc['schema']}  files mm {m['n_files_mm']}/{m['n_files_total']} "
              f"(skipped-units {m['n_files_skipped_units']})  "
              f"elements sampled {m['n_elements_sampled']} "
              f"malformed {m['n_elements_malformed']}{unl}")
        print(f"{'kind':<16}{'n':>7}  {'lo_mm':>16}{'hi_mm':>18}{'aspect':>16}")
        for k in sorted(doc["kinds"], key=lambda z: -doc["kinds"][z]["n"]):
            b = doc["kinds"][k]
            lo = f"[{b['lo_mm'][0]:.0f},{b['lo_mm'][1]:.0f}]"
            hi = f"[{b['hi_mm'][0]:.0f},{b['hi_mm'][1]:.0f}]"
            asp = f"[{b['aspect'][0]:.2f},{b['aspect'][1]:.2f}]"
            print(f"{k:<16}{b['n']:>7}  {lo:>16}{hi:>18}{asp:>16}")
        print(f"excluded_low_support: {doc['excluded_low_support']}")
        if "excluded_degenerate" in doc:
            print(f"excluded_degenerate (dispersion > {max_dispersion}): "
                  f"{json.dumps(doc['excluded_degenerate'], sort_keys=True)}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
