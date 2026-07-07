"""
benchmark_reader.py -- the backwards-learning scorecard: score a plan-reader's structured
output against PAIRED ground truth (the 3D/photo side of a 2D+3D pair), per semantic
failure class, with NO owner in the loop.

    python benchmark_reader.py <gt.json> <pred.json> [report.md]

WHY (docs/research/2026-07-06-paired-2d3d-backlearn.md SS3): the pipeline's bottleneck is
that the owner is the SOLE verifier of semantic reads (identity/facing/zoning). Paired
corpora make the 3D the answer key for what the 2D meant, so semantic accuracy becomes a
SCORED, regressable number. This module is the scoring ENGINE only -- corpus adapters
(FloorPlanCAD SVG, CubiCasa5K SVG, BMA Thai pairs) land separately and emit this schema;
until an adapter exists for a corpus, nothing here pretends to cover it (no silent pass:
a metric with no eligible items reports n=0 and verdict UNWIRED).

SCHEMA (both gt.json and pred.json; every field beyond id/kind/x/y/w/d optional):
  {"elements": [{"id", "kind", "x","y","w","d", "rot", "indoor": bool, "floor": bool}],
   "openings": [{"type": "door|sliding|window|opening", "x","y","w","d"}]}
x/y = min corner mm, w/d = extent mm, rot = degrees (build_floor convention: front(rot) =
(sin, -cos), pivot = centre) -- the SAME shape room-spec items use, so our own generator
output is directly scoreable.

METRIC DESIGN (each maps to one research failure class):
  detection    match pred<->GT elements by axis-aligned footprint IoU >= 0.5, greedy on
               best-IoU-first (geometry is machine-solved, so matching is nearly bijective;
               misses/phantoms are reported as completeness, SEPARATE from semantics --
               a bad detector must not pollute the semantic scores computed on matches).
  F1 identity  per-kind precision/recall/F1 over matched pairs + full confusion pairs;
               kinds normalised through KIND_SYNONYMS so 'tv_console'=='tv_cabinet'.
               Reported PER-CLASS, never only macro (published symbol-spotting tails sit
               at 0.0 PQ inside healthy macro averages -- SymPoint, FloorPlanCAD).
  F2 facing    on matched pairs whose GT kind is facing-asymmetric AND GT carries rot:
               angular error buckets exact(<=5deg) / cardinal(<=45) / flipped(180+-45) /
               wrong; headline = cardinal-correct fraction. Symmetric kinds are excluded
               a priori (a round stool has no facing to get wrong).
  F3 indoor    binary accuracy on matched pairs where GT carries `indoor`.
  F4 openings  pred<->GT openings matched by centre distance <= open_tol (openings are
               thin; IoU is brittle at zero width): detection P/R + subtype accuracy on
               matches + subtype confusion (door vs sliding vs window vs bare opening).
  F5 floor     binary accuracy on elements where GT carries `floor` (True = belongs to
               this storey; False = drawn-through ink such as grade-level trees).

Scores are 0..1 fractions. `verdict` per metric: PASS >= pass_bar (default .9 -- an
aspiration bar for regression tracking, not a shipping gate), REVIEW below it, UNWIRED
when the pair carries no eligible data. Pure logic end-to-end -> unit-testable.
"""
import json
import math
import sys

from placement_gate import footprint, iou   # the gate's own bbox + IoU math: one source

IOU_MATCH = 0.5
OPEN_TOL = 300.0          # mm centre distance for opening matching
PASS_BAR = 0.9

# facing-asymmetric kinds (F2 is only defined where the symbol HAS a front; extend as
# corpora demand -- an unknown kind is simply not scored, never guessed)
FACING_KINDS = {"bed", "sofa", "loveseat", "armchair", "chair", "bench", "tv_panel",
                "tv_console", "desk", "toilet", "wardrobe", "cabinet"}
KIND_SYNONYMS = {"tv_cabinet": "tv_console", "couch": "sofa", "night_stand": "side_table",
                 "nightstand": "side_table", "closet": "wardrobe"}


def norm_kind(k):
    k = (k or "").strip().lower()
    return KIND_SYNONYMS.get(k, k)


# ---- input sanitation (adapters and generators emit imperfect JSON; one malformed
#      element must cost THAT element -- reported -- never the whole corpus run) ---------
_CARDINAL_ROT = {"S": 0, "E": 90, "N": 180, "W": 270}    # facing_reader convention


def sanitize_elements(elements):
    """(clean, malformed). rot is coerced to float; numeric strings pass, the repo's
    cardinal letters map via the build_floor convention (S=0/E=90/N=180/W=270), and
    None/unparseable rot is DROPPED from the element (later scored as unreported --
    never defaulted to an angle). An element whose x/y/w/d cannot make a footprint
    goes to `malformed` (id kept, reported on the card)."""
    clean, malformed = [], []
    for e in elements or []:
        e = dict(e)
        if "rot" in e:
            r = e["rot"]
            if isinstance(r, str):
                r = _CARDINAL_ROT.get(r.strip().upper(), r)
            try:
                e["rot"] = float(r)
            except (TypeError, ValueError):
                e.pop("rot")
        try:
            [float(e[k]) for k in ("x", "y", "w", "d")]
        except (KeyError, TypeError, ValueError):
            malformed.append(e.get("id"))
            continue
        clean.append(e)
    return clean, malformed


# ---- matching --------------------------------------------------------------------------
def match_elements(gt, pred, iou_min=IOU_MATCH):
    """Greedy best-IoU-first one-to-one matching of element lists.
    Returns (pairs, gt_missed, pred_phantom); pairs = [(gt_el, pred_el, iou)].
    Ties on IoU prefer a SAME-KIND partner: co-located equal-footprint elements (a
    nightstand pair flanking a bed) must not cross-pair and manufacture identity
    confusions when a zero-error assignment exists. Kind plays no other role here."""
    cand = []
    for i, g in enumerate(gt):
        fg = footprint(g)
        for j, p in enumerate(pred):
            v = iou(fg, footprint(p))
            if v >= iou_min:
                kind_mismatch = 0 if norm_kind(g.get("kind")) == norm_kind(p.get("kind")) else 1
                cand.append((-v, kind_mismatch, i, j))
    cand.sort()
    used_g, used_p, pairs = set(), set(), []
    for nv, _km, i, j in cand:
        if i in used_g or j in used_p:
            continue
        used_g.add(i)
        used_p.add(j)
        pairs.append((gt[i], pred[j], -nv))
    missed = [g for i, g in enumerate(gt) if i not in used_g]
    phantom = [p for j, p in enumerate(pred) if j not in used_p]
    return pairs, missed, phantom


# ---- per-class metrics -----------------------------------------------------------------
def score_detection(pairs, missed, phantom):
    n_gt = len(pairs) + len(missed)
    n_pred = len(pairs) + len(phantom)
    return {"n_gt": n_gt, "n_pred": n_pred, "matched": len(pairs),
            "recall": len(pairs) / n_gt if n_gt else None,
            "precision": len(pairs) / n_pred if n_pred else None,
            "missed_ids": [g.get("id") for g in missed],
            "phantom_ids": [p.get("id") for p in phantom]}


def score_identity(pairs):
    """Per-kind P/R/F1 + confusion pairs, on matched elements only."""
    per = {}
    confusion = {}
    correct = 0
    for g, p, _v in pairs:
        gk, pk = norm_kind(g.get("kind")), norm_kind(p.get("kind"))
        row = per.setdefault(gk, {"gt": 0, "pred": 0, "hit": 0})
        row["gt"] += 1
        per.setdefault(pk, {"gt": 0, "pred": 0, "hit": 0})["pred"] += 1
        if gk == pk:
            row["hit"] += 1
            correct += 1
        else:
            confusion[f"{gk}->{pk}"] = confusion.get(f"{gk}->{pk}", 0) + 1
    for k, row in per.items():
        pr = row["hit"] / row["pred"] if row["pred"] else None
        rc = row["hit"] / row["gt"] if row["gt"] else None
        row["precision"], row["recall"] = pr, rc
        row["f1"] = (2 * pr * rc / (pr + rc)) if pr and rc and (pr + rc) else 0.0
    return {"n": len(pairs), "hits": correct,
            "accuracy": correct / len(pairs) if pairs else None,
            "per_kind": per, "confusion": confusion}


def angle_diff(a, b):
    d = abs((float(a) - float(b)) % 360.0)
    return min(d, 360.0 - d)


def score_facing(pairs, facing_kinds=FACING_KINDS):
    """Angular-error buckets on facing-asymmetric matched pairs that carry GT rot.
    A pred that OMITS rot on such a pair buckets as 'unreported' -- counted in n and
    NOT cardinal-correct. Defaulting a missing rot to 0 would hand a facing-blind
    reader a near-perfect score, since rot=0 is the most common ground truth (the
    exact flattering-scorer failure the M3.2 calibration run exposed)."""
    buckets = {"exact": 0, "cardinal": 0, "flipped": 0, "wrong": 0, "unreported": 0}
    scored = []
    for g, p, _v in pairs:
        if norm_kind(g.get("kind")) not in facing_kinds or g.get("rot") is None:
            continue
        if p.get("rot") is None:
            b, d = "unreported", None
        else:
            d = angle_diff(g["rot"], p["rot"])
            if d <= 5:
                b = "exact"
            elif d <= 45:
                b = "cardinal"
            elif abs(d - 180) <= 45:
                b = "flipped"
            else:
                b = "wrong"
        buckets[b] += 1
        scored.append((g.get("id"), None if d is None else round(d, 1), b))
    n = sum(buckets.values())
    ok = buckets["exact"] + buckets["cardinal"]
    return {"n": n, "hits": ok, "cardinal_correct": ok / n if n else None,
            "buckets": buckets, "per_element": scored}


def _score_binary(pairs, field):
    """Binary accuracy on matched pairs where GT carries the field with a real value
    (GT null = 'annotator could not tell' -> not eligible, mirrors score_facing).
    A pred that omits the field, or carries null, is scored as True -- generators
    rarely emit indoor/floor flags and their silence means 'ordinary: this floor,
    indoor', so GT False MUST mark that silence wrong, never skip or credit it."""
    n = ok = 0
    wrong = []
    for g, p, _v in pairs:
        if field not in g or g[field] is None:
            continue
        n += 1
        pv = p.get(field, True)
        if pv is None:
            pv = True
        if bool(pv) == bool(g[field]):
            ok += 1
        else:
            wrong.append(g.get("id"))
    return {"n": n, "hits": ok, "accuracy": ok / n if n else None, "wrong_ids": wrong}


def sanitize_openings(openings):
    """(clean, malformed_count). An opening without a numeric x/y cannot be located --
    it is counted malformed, never guessed at (0,0). Null w/d degrade to 0 (a point
    opening still matches by centre distance)."""
    clean, bad = [], 0
    for o in openings or []:
        o = dict(o)
        try:
            o["x"], o["y"] = float(o["x"]), float(o["y"])
        except (KeyError, TypeError, ValueError):
            bad += 1
            continue
        for k in ("w", "d"):
            try:
                o[k] = float(o.get(k) or 0)
            except (TypeError, ValueError):
                o[k] = 0.0
        clean.append(o)
    return clean, bad


def score_openings(gt_open, pred_open, tol=OPEN_TOL):
    """Centre-distance matching + subtype accuracy (door/sliding/window/opening)."""
    def centre(o):
        return (o["x"] + o.get("w", 0) / 2.0, o["y"] + o.get("d", 0) / 2.0)
    cand = []
    for i, g in enumerate(gt_open):
        gc = centre(g)
        for j, p in enumerate(pred_open):
            pc = centre(p)
            d = math.hypot(gc[0] - pc[0], gc[1] - pc[1])
            if d <= tol:
                cand.append((d, i, j))
    cand.sort()
    used_g, used_p, pairs = set(), set(), []
    for d, i, j in cand:
        if i in used_g or j in used_p:
            continue
        used_g.add(i)
        used_p.add(j)
        pairs.append((gt_open[i], pred_open[j]))
    sub_ok = sum(1 for g, p in pairs if (g.get("type") or "").lower() == (p.get("type") or "").lower())
    confusion = {}
    for g, p in pairs:
        gt_t, pd_t = (g.get("type") or "?").lower(), (p.get("type") or "?").lower()
        if gt_t != pd_t:
            confusion[f"{gt_t}->{pd_t}"] = confusion.get(f"{gt_t}->{pd_t}", 0) + 1
    n_gt, n_pred = len(gt_open), len(pred_open)
    return {"n_gt": n_gt, "n_pred": n_pred, "matched": len(pairs),
            "recall": len(pairs) / n_gt if n_gt else None,
            "precision": len(pairs) / n_pred if n_pred else None,
            "subtype_accuracy": sub_ok / len(pairs) if pairs else None,
            "subtype_confusion": confusion}


# ---- assembly ---------------------------------------------------------------------------
def _verdict(score, n, pass_bar=PASS_BAR):
    if not n:
        return "UNWIRED"           # no eligible data in this pair: say so, never pass
    return "PASS" if (score or 0) >= pass_bar else "REVIEW"


LOW_N = 20      # below this, a verdict is statistically provisional and says so


def score_pair(gt_doc, pred_doc, pass_bar=PASS_BAR):
    """Full scorecard for one (gt, pred) document pair. Malformed inputs cost the
    element and are REPORTED on the card; low-n metrics carry low_n=True so a PASS
    on two elements cannot silently read as 'verified'."""
    gt_el, gt_bad = sanitize_elements(gt_doc.get("elements", []))
    pred_el, pred_bad = sanitize_elements(pred_doc.get("elements", []))
    pairs, missed, phantom = match_elements(gt_el, pred_el)
    det = score_detection(pairs, missed, phantom)
    f1 = score_identity(pairs)
    f2 = score_facing(pairs)
    f3 = _score_binary(pairs, "indoor")
    gt_op, gt_op_bad = sanitize_openings(gt_doc.get("openings", []))
    pred_op, pred_op_bad = sanitize_openings(pred_doc.get("openings", []))
    f4 = score_openings(gt_op, pred_op)
    f5 = _score_binary(pairs, "floor")

    def row(m, score, n):
        return {**m, "verdict": _verdict(score, n, pass_bar), "low_n": bool(n) and n < LOW_N}

    card = {
        "malformed": {"gt_elements": gt_bad, "pred_elements": pred_bad,
                      "gt_openings": gt_op_bad, "pred_openings": pred_op_bad},
        "detection": row(det, min((x for x in (det["recall"], det["precision"]) if x is not None),
                                  default=None),
                         det["n_gt"] + det["n_pred"]),
        "F1_identity": row(f1, f1["accuracy"], f1["n"]),
        "F2_facing": row(f2, f2["cardinal_correct"], f2["n"]),
        "F3_indoor": row(f3, f3["accuracy"], f3["n"]),
        "F4_openings": row(f4, min((x for x in (f4["recall"], f4["precision"], f4["subtype_accuracy"])
                                    if x is not None), default=None) if f4["matched"] else
                           (0.0 if (f4["n_gt"] or f4["n_pred"]) else None),
                           f4["n_gt"] + f4["n_pred"]),
        "F5_floor": row(f5, f5["accuracy"], f5["n"]),
    }
    return card


def aggregate(cards):
    """Sum INTEGER counts across many pairs (a corpus run) and recompute the headline
    fractions from those sums -- never reconstructed from rounded accuracies, so cards
    that round-tripped through JSON with reduced float precision aggregate exactly."""
    agg = {"pairs": len(cards)}
    ng = sum(c["detection"]["n_gt"] for c in cards)
    np_ = sum(c["detection"]["n_pred"] for c in cards)
    nm = sum(c["detection"]["matched"] for c in cards)
    agg["detection"] = {"n_gt": ng, "n_pred": np_, "matched": nm,
                        "recall": nm / ng if ng else None,
                        "precision": nm / np_ if np_ else None}
    for f in ("F1_identity", "F3_indoor", "F5_floor"):
        nn = sum(c[f]["n"] for c in cards)
        hit = sum(c[f]["hits"] for c in cards)
        agg[f] = {"n": nn, "accuracy": hit / nn if nn else None}
    n2 = sum(c["F2_facing"]["n"] for c in cards)
    ok2 = sum(c["F2_facing"]["hits"] for c in cards)
    agg["F2_facing"] = {"n": n2, "cardinal_correct": ok2 / n2 if n2 else None}
    og = sum(c["F4_openings"]["n_gt"] for c in cards)
    op = sum(c["F4_openings"]["n_pred"] for c in cards)
    om = sum(c["F4_openings"]["matched"] for c in cards)
    agg["F4_openings"] = {"n_gt": og, "n_pred": op, "matched": om,
                          "recall": om / og if og else None,
                          "precision": om / op if op else None}
    return agg


def render_report(card, title="backwards-benchmark scorecard"):
    L = [f"# {title}", ""]
    mal = card.get("malformed", {})
    if any(mal.values()):
        L.append(f"- **malformed inputs (excluded, counted)**: {mal}")
    for k, m in card.items():
        if k == "malformed":
            continue
        head = m["verdict"] + (" (low n -- provisional)" if m.get("low_n") else "")
        nums = {kk: vv for kk, vv in m.items()
                if isinstance(vv, (int, float)) and not isinstance(vv, bool)
                and kk != "verdict"}
        L.append(f"- **{k}**: {head}  " +
                 "  ".join(f"{kk}={vv:.3f}" if isinstance(vv, float) else f"{kk}={vv}"
                           for kk, vv in nums.items()))
        for extra in ("confusion", "subtype_confusion"):
            if m.get(extra):
                L.append(f"    - {extra}: {m[extra]}")
    L.append("")
    L.append("UNWIRED = this pair carries no data for the metric (an adapter gap, "
             "not a pass). PASS bar is a regression aspiration, not a shipping gate.")
    return "\n".join(L)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    gt = json.load(open(sys.argv[1], encoding="utf-8"))
    pred = json.load(open(sys.argv[2], encoding="utf-8"))
    card = score_pair(gt, pred)
    print(render_report(card))
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as fh:
            fh.write(render_report(card) + "\n")
        print(f"\nwrote {sys.argv[3]}")


if __name__ == "__main__":
    main()
