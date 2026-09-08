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
  F6 glazing   FLAG-recall / FLAG-precision of the reader's glazed-facade / glazing-line
               DOUBT flags against the GT `glazing_lines` channel (curtain_wall/railing).
               Segments match by axis + perpendicular offset + on-axis span overlap (thin
               lines, like openings, are wrong to IoU). recall = of the truly-glazed lines,
               how many did the reader FLAG (did I doubt at the right places); precision =
               of the lines I flagged, how many are real glass (is my doubt trustworthy).
               Per-GT-kind recall too, so railings aren't hidden under curtain-wall volume.
               This is the corpus half of the doubt-calibration instrument (its live-project
               half, self_audit.py, ranks OPEN doubt where no GT exists).

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
GLAZE_PERP_TOL = 250.0    # mm perpendicular offset for glazing-line matching (~wall thick)
GLAZE_OVERLAP = 0.5       # fraction of the shorter segment that must overlap on-axis
GLAZE_PARALLEL_SIN = 0.342  # |sin(angle)| <= this (~20deg) for two lines to count parallel
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
    """Centre-distance matching + subtype accuracy (door/sliding/window/opening).
    Also reports per-GT-type recall (`per_type_gt`): the corpus headline 'how many
    SLIDING doors does the reader even locate' must be readable directly, not
    reconstructed from overall recall that the (far more numerous) hinged doors
    dominate -- same never-only-macro rule as F1's per-kind table."""
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
    per_type = {}
    for i, g in enumerate(gt_open):
        row = per_type.setdefault((g.get("type") or "?").lower(), {"n_gt": 0, "matched": 0})
        row["n_gt"] += 1
        row["matched"] += 1 if i in used_g else 0
    for row in per_type.values():
        row["recall"] = row["matched"] / row["n_gt"]
    n_gt, n_pred = len(gt_open), len(pred_open)
    return {"n_gt": n_gt, "n_pred": n_pred, "matched": len(pairs),
            "recall": len(pairs) / n_gt if n_gt else None,
            "precision": len(pairs) / n_pred if n_pred else None,
            "subtype_accuracy": sub_ok / len(pairs) if pairs else None,
            "subtype_confusion": confusion, "per_type_gt": per_type}


# ---- F6 glazing-line flag calibration --------------------------------------------------
def sanitize_glazing(lines):
    """(clean, malformed_count). A glazing line needs numeric x1/y1/x2/y2 to be located;
    one without is counted malformed, never guessed. `kind` is optional (GT carries
    curtain_wall/railing; a pred rarely knows glass-subtype -- that is an owner call, so
    subtype is scored only where BOTH sides carry it, never defaulted)."""
    clean, bad = [], 0
    for s in lines or []:
        s = dict(s)
        try:
            s["x1"], s["y1"] = float(s["x1"]), float(s["y1"])
            s["x2"], s["y2"] = float(s["x2"]), float(s["y2"])
        except (KeyError, TypeError, ValueError):
            bad += 1
            continue
        clean.append(s)
    return clean, bad


def _seg_aos(s):
    """(axis, offset, (lo, hi)) for a near-axis-aligned segment. Dominant axis decides
    orientation; a diagonal is bucketed by its longer projection. This alone would let two
    PERPENDICULAR 45deg diagonals share axis+offset+span and false-match, so score_glazing
    ADDITIONALLY gates on direction parallelism (see _seg_unit / GLAZE_PARALLEL_SIN)."""
    x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
    if abs(x2 - x1) >= abs(y2 - y1):
        return "h", (y1 + y2) / 2.0, (min(x1, x2), max(x1, x2))
    return "v", (x1 + x2) / 2.0, (min(y1, y2), max(y1, y2))


def _seg_unit(s):
    dx, dy = s["x2"] - s["x1"], s["y2"] - s["y1"]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _span_overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def score_glazing(gt_lines, pred_lines, perp_tol=GLAZE_PERP_TOL, overlap_frac=GLAZE_OVERLAP):
    """FLAG-recall / FLAG-precision of glazing-line doubt flags vs GT. Two segments match
    iff same axis, roughly PARALLEL direction (|sin angle| <= GLAZE_PARALLEL_SIN, so a
    perpendicular diagonal cannot alias onto a real run), |offset difference| <= perp_tol,
    and on-axis overlap covering >= overlap_frac of the SHORTER segment. Greedy
    best-overlap-first, one-to-one.

    recall    = matched / n_gt   (of the truly-glazed lines, how many the reader FLAGGED)
    precision = matched / n_pred (of the flagged lines, how many are real glass)
    per_kind  = per-GT-kind recall (curtain_wall vs railing) so the rarer kind isn't hidden
                under the commoner one's volume -- the same never-only-macro rule as F1/F4.

    KNOWN LIMIT (documented, not a bug): matching uses the SHORTER segment so that a real
    reader emitting ONE long facade run legitimately matches a GT drawn as many short
    railing ticks. The cost is that a degenerate 'whole wall is glass' single flag over a
    tiny GT run also matches and reads precision 1.0. Count-based precision cannot see that
    over-coverage; the real reader (svg_plan_reader promote runs) does not emit such flags,
    and F6 is a regression-tracking diagnostic, never a shipping gate -- so this is an
    accepted blind spot, called out rather than closed by a max()-gate that would wrongly
    tank recall on the far more common long-run-vs-fragmented-GT case."""
    g = [(_seg_aos(s), s, _seg_unit(s)) for s in gt_lines]
    p = [(_seg_aos(s), s, _seg_unit(s)) for s in pred_lines]
    cand = []
    for i, ((ga, go, gs), _gs, gu) in enumerate(g):
        glen = gs[1] - gs[0]
        for j, ((pa, po, ps), _ps, pu) in enumerate(p):
            cross = abs(gu[0] * pu[1] - gu[1] * pu[0])       # |sin| between the two lines
            if pa != ga or cross > GLAZE_PARALLEL_SIN or abs(po - go) > perp_tol:
                continue
            ov = _span_overlap(gs, ps)
            plen = ps[1] - ps[0]
            need = overlap_frac * max(1.0, min(glen, plen))
            if ov >= need:
                cand.append((-ov, i, j))
    cand.sort()
    used_g, used_p, pairs = set(), set(), []
    for nov, i, j in cand:
        if i in used_g or j in used_p:
            continue
        used_g.add(i)
        used_p.add(j)
        pairs.append((i, j))
    per_kind = {}
    for i, (_aos, s, _u) in enumerate(g):
        k = (s.get("kind") or "?").lower()
        row = per_kind.setdefault(k, {"n_gt": 0, "matched": 0})
        row["n_gt"] += 1
        row["matched"] += 1 if i in used_g else 0
    for row in per_kind.values():
        row["recall"] = row["matched"] / row["n_gt"] if row["n_gt"] else None
    n_gt, n_pred = len(gt_lines), len(pred_lines)
    return {"n_gt": n_gt, "n_pred": n_pred, "matched": len(pairs),
            "recall": len(pairs) / n_gt if n_gt else None,
            "precision": len(pairs) / n_pred if n_pred else None,
            "per_kind_gt": per_kind}


# ---- assembly ---------------------------------------------------------------------------
def _verdict(score, n, pass_bar=PASS_BAR):
    if not n:
        return "UNWIRED"           # no eligible data in this pair: say so, never pass
    return "PASS" if (score or 0) >= pass_bar else "REVIEW"


LOW_N = 20      # below this, a verdict is statistically provisional and says so


def score_pair(gt_doc, pred_doc, pass_bar=PASS_BAR, open_tol=None):
    """Full scorecard for one (gt, pred) document pair. Malformed inputs cost the
    element and are REPORTED on the card; low-n metrics carry low_n=True so a PASS
    on two elements cannot silently read as 'verified'.

    UNITS GUARD: OPEN_TOL is millimetres. Docs may carry meta.units ('mm' or an
    adapter's raw-unit flag such as 'svg-unit'). Mixing units across the pair raises;
    non-mm units require the CALLER to pass an explicit open_tol in those units --
    silently applying a 300mm tolerance to a 100-unit-normalised sheet would match
    openings across the whole drawing (a rubber stamp, found by scrutiny 2026-07-06)."""
    units_gt = (gt_doc.get("meta") or {}).get("units")
    units_pred = (pred_doc.get("meta") or {}).get("units")
    if units_gt and units_pred and units_gt != units_pred:
        raise ValueError(f"unit mismatch: gt={units_gt} pred={units_pred} -- refusing to score")
    units = units_gt or units_pred
    if open_tol is None:
        if units not in (None, "mm"):
            raise ValueError(f"units '{units}': pass an explicit open_tol in those units "
                             f"(the default OPEN_TOL={OPEN_TOL} is mm)")
        open_tol = OPEN_TOL
    gt_el, gt_bad = sanitize_elements(gt_doc.get("elements", []))
    pred_el, pred_bad = sanitize_elements(pred_doc.get("elements", []))
    pairs, missed, phantom = match_elements(gt_el, pred_el)
    det = score_detection(pairs, missed, phantom)
    f1 = score_identity(pairs)
    f2 = score_facing(pairs)
    f3 = _score_binary(pairs, "indoor")
    gt_op, gt_op_bad = sanitize_openings(gt_doc.get("openings", []))
    pred_op, pred_op_bad = sanitize_openings(pred_doc.get("openings", []))
    f4 = score_openings(gt_op, pred_op, tol=open_tol)
    f5 = _score_binary(pairs, "floor")
    # F6 perp tol keys off UNITS (not off open_tol's value, which is tunable on mm sheets):
    # mm/None -> the mm default; a non-mm sheet reuses the explicit tol the caller had to
    # pass to clear the units guard above.
    glaze_perp = GLAZE_PERP_TOL if units in (None, "mm") else open_tol
    gt_gl, gt_gl_bad = sanitize_glazing(gt_doc.get("glazing_lines", []))
    pred_gl, pred_gl_bad = sanitize_glazing(pred_doc.get("glazing_lines", []))
    f6 = score_glazing(gt_gl, pred_gl, perp_tol=glaze_perp)

    def row(m, score, n):
        return {**m, "verdict": _verdict(score, n, pass_bar), "low_n": bool(n) and n < LOW_N}

    card = {
        "malformed": {"gt_elements": gt_bad, "pred_elements": pred_bad,
                      "gt_openings": gt_op_bad, "pred_openings": pred_op_bad,
                      "gt_glazing": gt_gl_bad, "pred_glazing": pred_gl_bad},
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
        "F6_glazing": row(f6, min((x for x in (f6["recall"], f6["precision"])
                                   if x is not None), default=None) if f6["matched"] else
                          (0.0 if (f6["n_gt"] or f6["n_pred"]) else None),
                          f6["n_gt"] + f6["n_pred"]),
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
    per_type = {}
    for c in cards:
        for t, row in (c["F4_openings"].get("per_type_gt") or {}).items():
            agg_row = per_type.setdefault(t, {"n_gt": 0, "matched": 0})
            agg_row["n_gt"] += row["n_gt"]
            agg_row["matched"] += row["matched"]
    for row in per_type.values():
        row["recall"] = row["matched"] / row["n_gt"] if row["n_gt"] else None
    agg["F4_openings"] = {"n_gt": og, "n_pred": op, "matched": om,
                          "recall": om / og if og else None,
                          "precision": om / op if op else None,
                          "per_type_gt": per_type}
    gg = sum(c["F6_glazing"]["n_gt"] for c in cards)
    gp = sum(c["F6_glazing"]["n_pred"] for c in cards)
    gm = sum(c["F6_glazing"]["matched"] for c in cards)
    per_kind = {}
    for c in cards:
        for k, row in (c["F6_glazing"].get("per_kind_gt") or {}).items():
            agg_row = per_kind.setdefault(k, {"n_gt": 0, "matched": 0})
            agg_row["n_gt"] += row["n_gt"]
            agg_row["matched"] += row["matched"]
    for row in per_kind.values():
        row["recall"] = row["matched"] / row["n_gt"] if row["n_gt"] else None
    agg["F6_glazing"] = {"n_gt": gg, "n_pred": gp, "matched": gm,
                         "recall": gm / gg if gg else None,
                         "precision": gm / gp if gp else None,
                         "per_kind_gt": per_kind}
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
