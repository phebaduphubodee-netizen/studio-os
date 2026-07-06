"""
placement_gate.py — the REAL 2D->3D reading gate.

For years the "self-verify overlay" was a picture a human eyeballed: nothing in code
checked that a placed piece of furniture actually lands on something drawn in the plan,
and nothing FAILED when it didn't. So the OWNER was the first (and only) verifier, which
is exactly why the 3D kept coming out wrong. This module makes the machine the first
verifier.

It re-derives the DETERMINISTIC furniture clusters straight from the plan
(plan_cluster.extract_clusters) and checks every placed LOOSE item against them:

  * MATCHED   — placed footprint aligns with a drawn cluster (IoU >= IOU_OK).           OK
  * DRIFT     — overlaps a drawn piece but size/position is off (IOU_DRIFT..IOU_OK).    REVIEW
  * ON_INK    — sits on drawn ink but not a clean cluster (e.g. a bed merged with a     REVIEW
                built-in) — plausible but the machine can't certify the exact bbox.
  * FLOATING  — placed where the plan has essentially NO furniture ink under it.        FAIL  <-- blocks
  * UNPLACED  — a drawn cluster no placed piece covers: MISSING furniture, or a         REVIEW
                dimension-label the clusterer mistook for a piece. A human must say which.

Verdict / exit code:
  FAIL   (exit 1) if any loose piece is FLOATING — an unambiguous "you built furniture the
                  plan does not have there". Nothing renders on a FAIL.
  REVIEW (exit 0, but prints a HUMAN-CONFIRM checklist) for drift / on-ink / unplaced /
                  unverified built-ins — the honest "we read this much; sign off on the rest".
  PASS   (exit 0) when every loose piece matches a drawn cluster and nothing is left unplaced.

The FAIL is deliberately narrow so the gate does not cry wolf; the REVIEW list is where the
irreducibly-human calls (identity of a cluster, wet-fixture symbols, exact facing) live —
made EXPLICIT and signed, instead of silently guessed or eyeballed.

    python placement_gate.py <plan.pdf> <manifest.json | scene-graph.json> [page] [close_mm]

Pure logic (footprint / iou / classify / gate) is import-testable without a PDF; only run()
touches fitz. Calibration triple mirrors plan_cluster / gen_floor2_specs (one source sheet).
"""
import hashlib
import json
import math
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- thresholds (tunable; documented so a reviewer can argue each) -------------------
IOU_OK = 0.45        # placed box vs drawn cluster: a clean match
IOU_DRIFT = 0.15     # below this = no real overlap with any cluster
INK_FLOAT_PX = 12    # furniture-ink pixels under a footprint below this = FLOATING (empty floor)
UNPLACED_MIN_EXT_MM = 250    # a leftover cluster smaller than this in either axis = ignore (tick/noise)
UNPLACED_MIN_AREA_M2 = 0.03  # ...or smaller area than this = ignore (a small stool IS real -> keep low)

# Free-standing furniture MUST land on a drawn piece (STRICT): a floating one is a hard FAIL.
# Strictness is decided by KIND, not by which JSON array a piece sits in — a bed dropped into
# builtins[] must still FAIL if it floats. Mirrors build_floor._FURN_KINDS (+ bench/stool/ottoman).
# Everything NOT in this set (wall casework, wet fixtures, headboards) is LENIENT: it may be drawn
# on the excluded thick-line wall layer, so 'no furniture-ink there' is UNVERIFIED (REVIEW), not a
# floor-on-empty FAIL.
FURN_KINDS = {"sofa", "loveseat", "coffee_table", "dining_table", "desk", "side_table",
              "nightstand", "chair", "dining_chair", "armchair", "bed", "bench", "stool",
              "table", "ottoman"}


def _is_strict(kind):
    return kind in FURN_KINDS


# Kinds whose drawn symbol carries a facing cue (a headboard / backrest strip) that facing_reader
# can cross-check against the hand-typed rot. Everything else has no reliable facing symbol.
_FACING_KINDS = {"bed", "sofa", "loveseat", "armchair", "chair"}
_CARDINALS = {"N", "S", "E", "W"}      # valid owner-signed facing values (facing_reader vocab)


# ---- pure geometry (no PDF) ----------------------------------------------------------
def footprint(it, offset=(0, 0)):
    """AXIS-ALIGNED plan-mm bbox of a placed spec item AS build_floor ACTUALLY RENDERS IT.

    build_floor.place_massing builds the piece filling w x d with centre pivot =
    (x + w/2, y + d/2), then rotates it by `rot` degrees about that pivot. So the centre
    matches x + w/2 exactly, and the axis-aligned half-extents of a w x d rectangle rotated
    by theta are (w/2)|cos| + (d/2)|sin| and (w/2)|sin| + (d/2)|cos|. This reduces to the
    plain (w,d)/(d,w) swap at 0/90/180/270 but stays CORRECT for the 'หันเฉียง' diagonal
    chairs too (a 45-deg piece has a larger bbox than either swap). Getting this wrong
    silently offsets every check, so it is derived from the renderer's own math on purpose.
    """
    w, d, rot = it["w"], it["d"], it.get("rot", 0)
    cx = it["x"] + offset[0] + w / 2.0
    cy = it["y"] + offset[1] + d / 2.0
    th = math.radians(rot)
    c, s = abs(math.cos(th)), abs(math.sin(th))
    ew = w * c + d * s
    ns = w * s + d * c
    return (cx - ew / 2.0, cy - ns / 2.0, cx + ew / 2.0, cy + ns / 2.0)


def cluster_bbox(c):
    return (c["x"], c["y"], c["x"] + c["w"], c["y"] + c["d"])


def iou(a, b):
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = ix1 - ix0, iy1 - iy0
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _best_cluster(fp, clusters):
    best_i, best_iou = None, 0.0
    for i, c in enumerate(clusters):
        v = iou(fp, cluster_bbox(c))
        if v > best_iou:
            best_i, best_iou = i, v
    return best_i, best_iou


def _centre(fp):
    return ((fp[0] + fp[2]) / 2.0, (fp[1] + fp[3]) / 2.0)


def _in_zone(pt, zone):
    return zone[0] <= pt[0] <= zone[2] and zone[1] <= pt[1] <= zone[3]


def classify_item(it, clusters, ink_count, zone, offset=(0, 0), strict=True):
    """Classify one placed item against the drawn clusters + furniture ink:
      matched  IoU >= IOU_OK
      drift    IOU_DRIFT <= IoU < IOU_OK
      else (no real cluster overlap):
        - centroid OUTSIDE the rasterised zone -> 'unverified'. The ink raster only covers the
          room zone, so a piece placed largely outside it has no ink to see; a FAIL must never
          fire there (false-block guard for furniture that laps past the outline).
        - ink under footprint >= INK_FLOAT_PX -> 'on_ink': sits on SOME drawing but not its own
          clean cluster (a displaced piece dumped onto other furniture lands here) -> REVIEW,
          which now BLOCKS the build until a human signs off.
        - else 'floating' if strict (free-standing furniture on empty floor = hard FAIL),
          else 'unverified' (wall/wet casework may be on the excluded thick-line layer).
    """
    fp = footprint(it, offset)
    bi, biou = _best_cluster(fp, clusters)
    if biou >= IOU_OK:
        status = "matched"
    elif biou >= IOU_DRIFT:
        status = "drift"
    elif not _in_zone(_centre(fp), zone):
        status = "unverified"
    elif ink_count(fp) >= INK_FLOAT_PX:
        status = "on_ink"
    else:
        status = "floating" if strict else "unverified"
    return {"name": it.get("name", it.get("kind", "?")), "kind": it.get("kind", "?"),
            "status": status, "iou": round(biou, 3), "cluster": bi, "fp": fp}


def unplaced_clusters(clusters, all_fps):
    """Clusters no placed footprint covers (best IoU to ANY placed piece < IOU_DRIFT) and
    big enough to be furniture rather than a dim-tick. These are MISSING pieces or
    label-text phantoms — a human decides which."""
    out = []
    for i, c in enumerate(clusters):
        cb = cluster_bbox(c)
        best = max((iou(fp, cb) for fp in all_fps), default=0.0)
        if best >= IOU_DRIFT:
            continue
        if min(c["w"], c["d"]) < UNPLACED_MIN_EXT_MM or c.get("area_m2", 0) < UNPLACED_MIN_AREA_M2:
            continue
        out.append({"id": c.get("id"), "x": c["x"], "y": c["y"], "w": c["w"], "d": c["d"],
                    "area_m2": c.get("area_m2"), "curve": c.get("curve"),
                    "best_iou": round(best, 3)})
    return out


def identity_check(loose, loose_r, clusters):
    """DOUBLE-CLAIM detector: flag when two placed pieces best-overlap the SAME drawn cluster
    (two pieces drawn on one blob, or one piece misidentified onto another's cluster). Computed
    from the gate's OWN re-derived best-match index (bi), NOT the generator's recorded 'cluster'
    claim, so it is renumber-proof (the scipy label id is volatile) and independent.

    Deliberately NOT a claim-vs-matched 'swap' check: the generator SNAPS a piece's footprint
    EQUAL to the cluster it records, so claim==matched by construction -> a generation-time
    wrong-anchor records the wrong id AND snaps to it (invisible to any claim-vs-id compare),
    while an id renumber between generate and gate would false-flag every snapped piece. A moved
    or hand-edited piece instead surfaces via its drift/floating STATUS, not here. The snapping
    generator also reserves each cluster, so on clean generated output double_claim never fires;
    it fires on a hand-edited scene-graph or a future non-dedup generator. Advisory -> REVIEW."""
    claimed_by = {}
    for r in loose_r:
        if r["status"] not in ("matched", "drift"):
            continue
        bi = r.get("cluster")
        if bi is None or not (0 <= bi < len(clusters)):
            continue
        claimed_by.setdefault(bi, []).append(r.get("name"))
    return [{"type": "double_claim", "cluster": clusters[bi]["id"], "names": names}
            for bi, names in claimed_by.items() if len(names) > 1]


def _sig_dist(cluster, entry):
    """Centre distance (max of |dx|,|dy|) between a cluster and a ledger entry, or None if the
    entry is malformed (missing coord) or fails the size/shape discriminators. Tolerance SCALES
    with the entry's size (rel of its larger extent, floored) so a big-blob dismissal cannot
    shadow a distinct furniture-sized cluster that merely shares its centre; a curve/organic
    mismatch (rectilinear door vs organic chair) also disqualifies. Missing keys -> None (skip),
    never a crash (the ledger is hand-edited)."""
    ex, ey, ew, ed = entry.get("x"), entry.get("y"), entry.get("w"), entry.get("d")
    if None in (ex, ey, ew, ed):
        return None
    tol = max(120.0, 0.15 * max(ew, ed))
    if abs(cluster["w"] - ew) > tol or abs(cluster["d"] - ed) > tol:
        return None                                  # size discriminator (scaled to the entry)
    if "curve" in entry and cluster.get("curve") is not None and bool(entry["curve"]) != bool(cluster["curve"]):
        return None                                  # shape discriminator (door=rect vs chair=organic)
    dcx = abs((cluster["x"] + cluster["w"] / 2.0) - (ex + ew / 2.0))
    dcy = abs((cluster["y"] + cluster["d"] / 2.0) - (ey + ed / 2.0))
    return max(dcx, dcy) if (dcx <= tol and dcy <= tol) else None


def _sig_match(cluster, entry):
    return _sig_dist(cluster, entry) is not None


def apply_dismissals(unplaced, dismissed_ledger):
    """Split unplaced clusters into (still_unplaced, dismissed). Each ledger entry dismisses AT
    MOST ONE cluster — its single NEAREST size/shape-consistent match — and each cluster is
    consumed once, so one human sign-off of a door/label CANNOT silently silence a second,
    genuine furniture cluster that happens to sit near it (that piece stays UNPLACED -> REVIEW).
    A dismissed cluster is a human-signed NON-furniture: the recurring 'is this drawn blob a
    piece?' question is answered once and persists across regenerations."""
    kept = list(unplaced)
    matched = []
    for e in dismissed_ledger:
        if not isinstance(e, dict):        # a hand-edited null/string/number entry -> skip, don't crash
            continue
        scored = [(d, c) for c in kept for d in (_sig_dist(c, e),) if d is not None]
        if not scored:
            continue
        _, best = min(scored, key=lambda dc: dc[0])   # nearest size/shape-consistent cluster only
        kept.remove(best)
        matched.append({**best, "reason": e.get("reason"), "by": e.get("by"), "date": e.get("date")})
    return kept, matched


def check_wall_grid(segments, checks, default_tol=120.0, default_min_len=1500.0):
    """Calibration SAFETY NET: assert the EXTRACTED wall geometry registers at the plan's WRITTEN
    grid dimensions, so a wrong (scale,ox,oy) triple FAILs loudly instead of the generator and
    gate silently agreeing with EACH OTHER while both are wrong (they share the triple, so their
    mutual IoU stays ~1.00 through a bad calibration).

    A check PASSES if a LONG structural wall (length >= min_len_mm) lies within tol_mm of the line.
    The min-length gate + far-from-origin lines (an origin line is scale-invariant -> useless)
    reliably catch a GROSS error (>~3% scale, a wrong page/plan): the long wall moves off the line
    and no short interior wall can stand in for it. HONEST BOUND -- this is a net, not a proof: on
    a dense plan a thick/interior LONG wall can coincidentally register, so a small residual window
    (roughly < ~2.5% scale / < ~80mm origin) can still PASS. The primary guarantee stays the
    calibration constant, verified <1% vs the written dims; this only backstops a gross regression.
    A POSITIVE fail is reliable (a gross error genuinely leaves no long wall at the line) -- it is
    the RECALL that is bounded, not the precision, so a hard-FAIL never false-blocks a correct read.

    segments = [[[x0,y0],[x1,y1]], ...] mm; checks = [{axis:'x'|'y', mm, tol_mm?, min_len_mm?,
    desc?}, ...]. A check with no 'mm' is skipped; a malformed segment is skipped. Returns the
    FAILED checks (empty list = calibration holds)."""
    fails = []
    for ch in checks:
        axis, mm = ch.get("axis"), ch.get("mm")
        if mm is None:
            continue                      # a check missing its target dim is ignored, not a crash
        tol = ch.get("tol_mm", default_tol)
        min_len = ch.get("min_len_mm", default_min_len)
        ok = False
        for seg in segments:
            try:
                (ax, ay), (bx, by) = seg[0], seg[1]
                dx, dy = bx - ax, by - ay
                L = math.hypot(dx, dy)
            except (TypeError, ValueError, IndexError):
                continue                  # skip a malformed segment rather than crash the gate
            if L < min_len:               # only LONG structural walls count
                continue
            if axis == "x" and abs(dx) <= abs(dy) and min(abs(ax - mm), abs(bx - mm)) <= tol:
                ok = True
                break
            if axis == "y" and abs(dy) <= abs(dx) and min(abs(ay - mm), abs(by - mm)) <= tol:
                ok = True
                break
        if not ok:
            fails.append({**ch, "found_long_wall": False})
    return fails


def _size_consistent(piece, entry, tol=0.20):
    """True if the entry carries no size, or its w/d match the piece within tol (orientation-
    agnostic). A size guard so a confirmed-facing entry cannot silently attach to a DIFFERENT
    piece that merely reused the same name after an edit."""
    ew, ed = entry.get("w"), entry.get("d")
    if ew is None or ed is None:
        return True
    try:
        a = sorted((float(piece["w"]), float(piece["d"])))
        b = sorted((float(ew), float(ed)))
    except (KeyError, TypeError, ValueError):
        return False
    return all(c > 0 and abs(s - c) / c <= tol for s, c in zip(a, b))


def confirmed_facing(piece, confirmed, size_tol=0.20):
    """The owner-signed cardinal facing for a piece, or None. Matches a confirmed-ledger entry
    by NAME (the generator names pieces deterministically) with a size sanity guard. This is the
    durable, structured, owner-signed store that ends the regression memory flagged — 'facing
    lived only as a default + a prose note, so a clean rebuild silently overwrote a correct read'.
    BOTH consumers read it: the gate (to SUPPRESS a signed piece's REVIEW facing-flag + SIGN todo)
    and the generator (to APPLY the signed facing OVER any geometric re-derivation, via
    facing_reader.rot_from_facing)."""
    name = piece.get("name")
    if name is None:
        return None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        fac = e.get("facing")
        if fac not in _CARDINALS:      # a truthy-but-non-cardinal typo ('south','N ',180) must NOT
            continue                   # suppress — the generator's rot_from_facing would apply nothing
        if e.get("name") == name and _size_consistent(piece, e, size_tol):
            return fac
    return None


def load_confirmed(led):
    """Pull the owner-signed 'confirmed' facing entries out of a parsed placement-review ledger
    dict (mirrors the 'dismissed' handling); drops non-dict typos. Returns [] on anything odd."""
    if not isinstance(led, dict):
        return []
    conf = led.get("confirmed", [])
    return [e for e in conf if isinstance(e, dict)] if isinstance(conf, list) else []


def facing_flags(loose, fsegs, offset=(0, 0), confirmed=None):
    """ADVISORY facing cross-check for seating/beds: compare each piece's HAND-TYPED rot to the
    facing READ from its drawn headboard/backrest strip (facing_reader). Facing is otherwise
    100% human-authored and 0% machine-checked — a 180-deg-wrong bed still scores IoU ~1.00,
    because a cardinal rotation barely changes the axis-aligned footprint. Returns only the
    clear DISAGREEMENTS; conservative by design (an unreadable/symmetric strip -> 'unknown',
    never a flag), so it adds signal without crying wolf. REVIEW-only, never FAIL.

    A piece whose facing the OWNER has already signed off (confirmed ledger) is SKIPPED — the
    adjudication is done, so the gate stops asking and the verdict converges toward PASS as the
    owner signs. This is the 'gate suppresses the SIGN todo once signed' half of the ledger."""
    try:
        import facing_reader as FR
    except ImportError:
        return []
    out = []
    for it in loose:
        if it.get("kind") not in _FACING_KINDS:
            continue                      # rot defaults to 0 (=S) when the generator omits it
        signed = confirmed_facing(it, confirmed)
        if signed is not None:
            # The owner signed this piece's facing. Suppress the read-vs-typed flag ONLY when the
            # piece's BUILT orientation (its rot) matches the signature. If a rebuild re-rolled the
            # rot so it now CONTRADICTS the owner's signed truth, that is exactly the regression the
            # ledger exists to catch -> emit a strong flag instead of silently dropping it. (The
            # generator-applies-the-sign wiring, rot_from_facing, is still pending, so nothing yet
            # forces rot == sign; this makes the gate the backstop until it lands.)
            claimed = FR.facing_from_rot(it.get("rot", 0))
            if claimed == signed:
                continue                  # built orientation agrees with the sign -> adjudicated
            out.append({"name": it.get("name"), "kind": it.get("kind"),
                        "verdict": "contradicts_signed", "claimed": claimed, "read": signed,
                        "confidence": 1.0})
            continue
        fp = footprint(it, offset)
        pad = 120.0
        bb = (fp[0] - pad, fp[1] - pad, fp[2] + pad, fp[3] + pad)
        local = [s for s in fsegs
                 if bb[0] <= (s[0][0] + s[1][0]) / 2.0 <= bb[2]
                 and bb[1] <= (s[0][1] + s[1][1]) / 2.0 <= bb[3]]
        try:
            chk = FR.check_piece(local, fp, it.get("rot", 0))
        except Exception:
            continue                      # advisory only: a facing_reader bug must NEVER abort the gate
        if chk["verdict"] in ("disagree", "ambiguous"):
            out.append({"name": it.get("name"), "kind": it.get("kind"), "verdict": chk["verdict"],
                        "claimed": chk["claimed"], "read": chk["read"],
                        "confidence": round(chk.get("confidence", 0.0), 2)})
    return out


def gate(loose, fixed, clusters, ink_count, zone, offset=(0, 0), dismissed=None, dropped=None):
    """Check one room. loose = spec items[]; fixed = built-ins + subroom fixtures (kept separate
    only for the report). STRICTNESS is decided per piece by KIND (see _is_strict), so free-
    standing furniture is checked strictly wherever it is listed. FAIL if ANY free-standing piece
    floats on empty floor. dismissed = the room's dismissals-ledger entries (door/label blobs
    already signed off). dropped = the clusterer's size-filtered components: a merged_blob is a
    region the clusterer could NOT resolve (a completeness BLIND SPOT), surfaced alongside the
    unplaced clusters so a real piece fused into wall/linework is not silently lost -> REVIEW
    (dismissable once a human confirms the region is only linework)."""
    loose_r = [classify_item(it, clusters, ink_count, zone, offset, _is_strict(it.get("kind"))) for it in loose]
    fixed_r = [classify_item(it, clusters, ink_count, zone, offset, _is_strict(it.get("kind"))) for it in fixed]
    every = loose_r + fixed_r
    unplaced_all = unplaced_clusters(clusters, [r["fp"] for r in every])
    merged = [{"id": None, "x": d["x"], "y": d["y"], "w": d["w"], "d": d["d"],
               "area_m2": d.get("area_m2"), "curve": bool(d.get("curve")), "fill": d.get("fill"),
               "reason": "merged_blob"}
              for d in (dropped or []) if d.get("reason") == "merged_blob"]
    kept_all, dismissed_matched = apply_dismissals(unplaced_all + merged, dismissed or [])
    unplaced = [c for c in kept_all if c.get("reason") != "merged_blob"]
    merged_kept = [c for c in kept_all if c.get("reason") == "merged_blob"]
    identity = identity_check(loose, loose_r, clusters)

    floating = [r for r in every if r["status"] == "floating"]
    review = [r for r in every if r["status"] in ("drift", "on_ink", "unverified")]
    if floating:
        verdict = "FAIL"
    elif review or kept_all or identity:
        verdict = "REVIEW"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "loose": loose_r, "fixed": fixed_r,
            "unplaced": unplaced, "merged": merged_kept, "dismissed": dismissed_matched,
            "identity": identity, "n_clusters": len(clusters)}


# ---- PDF-backed orchestration --------------------------------------------------------
def _ink_counter(res):
    """Closure: furniture-ink pixel count inside a plan-mm footprint, on the cluster raster."""
    ink = res["ink"]
    X0, Y0, X1, Y1 = res["zone"]
    RES = res["res"]
    W, H = res["W"], res["H"]

    def count(fp):
        x0, y0, x1, y1 = fp
        c0 = max(0, int((x0 - X0) / RES)); c1 = min(W, int((x1 - X0) / RES))
        r0 = max(0, int((Y1 - y1) / RES)); r1 = min(H, int((Y1 - y0) / RES))
        if c1 <= c0 or r1 <= r0:
            return 0
        return int(ink[r0:r1, c0:c1].sum())

    return count


def _room_zone(spec, offset, pad=150.0):
    """Cluster zone = the ROOM outline bbox (∪ subroom outlines), padded ~150mm.

    Deliberately NOT expanded to stray footprints: connected-component clustering is
    zone-sensitive — pulling a neighbouring room's ink into the frame can bridge/merge
    or drop a piece's cluster (the dressing chair vanished into a >3600mm blob when the
    zone reached into the adjacent room), and even a modest pad drags wall hatching just
    outside the outline in as spurious 'unplaced' noise. The pad is kept SMALL for a clean
    frame; the false-FAIL of furniture that laps past the outline is prevented instead by
    classify_item's centroid-in-zone guard (a piece whose centroid lands beyond the zone is
    UNVERIFIED, never FLOATING), so a tight zone cannot hard-fail a correctly-read piece."""
    xs, ys = [], []
    for p in spec["room"]["outline_mm"]:
        xs.append(p[0] + offset[0]); ys.append(p[1] + offset[1])
    for sr in spec.get("subrooms", []):
        for p in sr.get("outline_mm", []):
            xs.append(p[0] + offset[0]); ys.append(p[1] + offset[1])
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _pieces(spec):
    loose = list(spec.get("items", []))
    fixed = list(spec.get("builtins", []))
    for sr in spec.get("subrooms", []):
        fixed += sr.get("fixtures", [])
    return loose, fixed


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_calibration_check(doc, base):
    """If the manifest declares 'calibration_checks', assert the extracted walls register at the
    written grid dims (see check_wall_grid). Loads the manifest's walls_json (repo-relative or in
    the manifest dir). Returns the failed checks (empty if none declared or all pass)."""
    checks = doc.get("calibration_checks")
    if not checks:
        return []
    wj = doc.get("walls_json")
    segs = None
    for cand in ([wj, os.path.join(base, os.path.basename(wj))] if wj else []):
        if cand and os.path.exists(cand):
            try:
                _w = json.load(open(cand, encoding="utf-8"))
                segs = _w.get("segments") if isinstance(_w, dict) else None
            except (ValueError, OSError):
                segs = None
            if segs is not None:
                break
    if segs is None:
        return [{"axis": "?", "mm": 0, "desc": f"walls_json not found/unreadable ({wj})"}]
    return check_wall_grid(segs, checks)


def run(pdf, target, page=None, close_mm=None, calib=None):
    """Load a manifest (multi-room) or a single scene-graph, extract clusters per room,
    gate each, print a report, and return overall verdict + per-room results.

    page/close_mm/calib default from the manifest ('page','close_mm','calibration' fields)
    then to this sheet's values — so a different project can carry its own calibration and is
    NOT silently read in the wrong coordinate frame. The calibration used is logged."""
    from plan_cluster import extract_clusters, SCALE, OX, OY

    base = os.path.dirname(os.path.abspath(target))
    doc = json.load(open(target, encoding="utf-8"))
    page = doc.get("page", 1) if page is None else page
    close_mm = doc.get("close_mm", 18.0) if close_mm is None else close_mm
    if calib is None:
        calib = tuple(doc["calibration"]) if "calibration" in doc else (SCALE, OX, OY)
    print(f"gate calibration: scale={calib[0]} ox={calib[1]} oy={calib[2]}  page={page}  "
          f"close_mm={close_mm}  (verify this matches {os.path.basename(pdf)})")

    input_paths = [os.path.abspath(target)]
    rooms = []          # (room_id, spec, offset_mm, spec_path)
    if "furnish" in doc:                      # a floor manifest
        for f in doc["furnish"]:
            spec_path = f["spec"]
            if not os.path.isabs(spec_path) and not os.path.exists(spec_path):
                spec_path = os.path.join(base, os.path.basename(spec_path))
            spec = json.load(open(spec_path, encoding="utf-8"))
            rooms.append((f.get("id", spec["room"].get("type", "room")),
                          spec, tuple(f.get("offset_mm", [0, 0])), os.path.abspath(spec_path)))
            input_paths.append(os.path.abspath(spec_path))
    else:                                     # a single scene-graph
        rooms.append((doc["room"].get("type", "room"), doc, (0, 0), os.path.abspath(target)))

    # bind walls_json (a direct build input the calibration check reads) so a post-gate
    # re-extraction with a wrong triple invalidates the marker like a spec/manifest edit.
    wj = doc.get("walls_json")
    if wj:
        for cand in [wj, os.path.join(base, os.path.basename(wj))]:
            if os.path.exists(cand):
                input_paths.append(os.path.abspath(cand))
                break

    ledger_path = os.path.join(base, "placement-review.json")
    dismissed_all, confirmed_all = [], []
    if os.path.exists(ledger_path):
        input_paths.append(os.path.abspath(ledger_path))   # bind its hash regardless of validity
        try:
            _led = json.load(open(ledger_path, encoding="utf-8"))
            dismissed_all = _led.get("dismissed", []) if isinstance(_led, dict) else []
            if not isinstance(dismissed_all, list):
                dismissed_all = []
            dismissed_all = [e for e in dismissed_all if isinstance(e, dict)]   # drop null/str/num typos
            confirmed_all = load_confirmed(_led)               # owner-signed facings (persist across rebuilds)
            print(f"placement-review.json: {len(dismissed_all)} dismissal(s), "
                  f"{len(confirmed_all)} signed facing(s) on file")
        except (ValueError, OSError, AttributeError, TypeError):
            print("  [!] placement-review.json malformed -- ignoring dismissals/confirmations")

    results, worst = [], "PASS"
    order = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    for room_id, spec, offset, _sp in rooms:
        loose, fixed = _pieces(spec)
        zone = _room_zone(spec, offset)
        res = extract_clusters(pdf, page, zone, close_mm, calib=calib)
        dismissed_room = [e for e in dismissed_all if e.get("room") in (room_id, "*")]
        confirmed_room = [e for e in confirmed_all if e.get("room") in (room_id, "*")]
        r = gate(loose, fixed, res["items"], _ink_counter(res), zone, offset,
                 dismissed=dismissed_room, dropped=res.get("dropped"))
        r["room"] = room_id
        r["dropped"] = res.get("dropped", [])
        r["facing"] = facing_flags(loose, res["fsegs"], offset, confirmed=confirmed_room)
        if r["facing"] and order[r["verdict"]] < order["REVIEW"]:
            r["verdict"] = "REVIEW"        # a symbol-vs-typed facing disagreement needs a human
        results.append(r)
        if order[r["verdict"]] > order[worst]:
            worst = r["verdict"]

    calib_fails = _run_calibration_check(doc, base)
    if calib_fails and order["FAIL"] > order[worst]:
        worst = "FAIL"

    _report(results, worst, calib_fails)
    marker = _write_marker(target, worst, results, input_paths, calib_fails)
    print(f"wrote gate marker: {marker}  (build refuses on FAIL, on un-signed REVIEW, or when an "
          f"input hash no longer matches)")
    return worst, results


def _write_marker(target, worst, results, input_paths, calib_fails=None):
    """Persist the verdict next to the target so the Blender build (which lacks fitz/scipy) can
    enforce the gate. The marker is bound to the exact files it gated by CONTENT HASH: build
    refuses unless every input it needs (manifest + each furnished scene-graph) is present in
    'inputs' with a matching sha1. This kills three holes at once — a stale edit, a manifest
    offset/furnish change (specs untouched), and a marker written by gating a DIFFERENT target
    in the same directory. Hash beats mtime: immune to OneDrive re-sync touching mtimes."""
    marker = os.path.join(os.path.dirname(os.path.abspath(target)), "placement-gate.json")
    inputs = {}
    for p in input_paths:
        try:
            inputs[os.path.basename(p)] = _sha1(p)
        except OSError:
            pass
    payload = {
        "verdict": worst,
        "gated_target": os.path.basename(os.path.abspath(target)),
        "inputs": inputs,          # basename -> sha1 of every file the gate consumed
        "generated_epoch": time.time(),   # informational only; correctness uses hashes
        "calibration": ("FAIL" if calib_fails else "PASS"),
        "calibration_fails": calib_fails or [],
        "rooms": [{"room": r["room"], "verdict": r["verdict"],
                   "floating": [x["name"] for x in (r["loose"] + r["fixed"]) if x["status"] == "floating"],
                   "unplaced": len(r["unplaced"]),
                   "merged_regions": len(r.get("merged", [])),
                   "dismissed": len(r.get("dismissed", [])),
                   "identity_flags": len(r.get("identity", [])),
                   "facing_flags": len(r.get("facing", [])),
                   "long_thin": len(_long_thin(r)), "dropped_total": len(r.get("dropped", []))}
                  for r in results],
        "note": "Auto-written by placement_gate.py. Do not hand-edit; re-run the gate to refresh.",
    }
    json.dump(payload, open(marker, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return marker


# ---- reporting -----------------------------------------------------------------------
_MARK = {"matched": "OK   ", "drift": "DRIFT", "on_ink": "ON-INK",
         "floating": "FLOAT", "unverified": "UNVER"}


def _long_thin(r, min_span_mm=900.0, min_short_mm=50.0):
    """Dropped 'thin' components that could PLAUSIBLY be a slim real piece (a narrow console/ledge)
    rather than a dimension line — long on one axis (>=min_span) yet with real depth on the other
    (>=min_short, so a ~0-width leader/dimension line stays quiet). Surfaced so the size filter
    cannot silently swallow a genuine narrow piece. (merged_blob drops are handled as 'merged'
    regions in gate; tiny ticks stay quiet.)"""
    return [d for d in r.get("dropped", [])
            if d.get("reason") == "thin"
            and max(d.get("w", 0), d.get("d", 0)) >= min_span_mm
            and min(d.get("w", 0), d.get("d", 0)) >= min_short_mm]


def _report(results, worst, calib_fails=None):
    print("=" * 74)
    print("PLACEMENT GATE — does every placed piece land on something drawn in the plan?")
    print("=" * 74)
    for r in results:
        print(f"\n### room: {r['room']}   ({r['n_clusters']} drawn clusters)   -> {r['verdict']}")
        print("  LOOSE furniture (checked strictly against clusters):")
        for it in r["loose"]:
            print(f"    [{_MARK.get(it['status'],it['status']):6}] IoU {it['iou']:.2f}  {it['name']}")
        if r["fixed"]:
            print("  BUILT-INS / fixtures (label-derived, lenient):")
            for it in r["fixed"]:
                print(f"    [{_MARK.get(it['status'],it['status']):6}] IoU {it['iou']:.2f}  {it['name']}")
        if r["unplaced"]:
            print("  UNPLACED drawn clusters (missing furniture OR a label — CONFIRM each):")
            for c in r["unplaced"]:
                print(f"    [?]     {c['w']}x{c['d']}mm at ({c['x']},{c['y']})  "
                      f"area {c['area_m2']}m2  {'organic' if c['curve'] else 'rectilinear'}")
        for c in r.get("merged", []):
            print(f"    [REGION] {c['w']}x{c['d']}mm at ({c['x']},{c['y']}) un-clusterable (fill "
                  f"{c.get('fill')}) — confirm NO drawn piece hides in it (low fill = likely linework)")
        for d in _long_thin(r):
            print(f"    [THIN]   dropped {d['w']}x{d['d']}mm at ({d['x']},{d['y']}) — a narrow drawn "
                  f"piece the size filter discarded; confirm it is a tick/leader, not furniture")
        for c in r.get("dismissed", []):
            print(f"    [signed] {c['w']}x{c['d']}mm at ({c['x']},{c['y']}) dismissed as non-furniture "
                  f"({c.get('reason','?')}; {c.get('by','?')})")
        for f in r.get("identity", []):
            print(f"    [DUP?]   cluster {f['cluster']} claimed by {len(f['names'])} pieces: "
                  f"{', '.join(str(x) for x in f['names'])}")
        for f in r.get("facing", []):
            if f.get("verdict") == "contradicts_signed":
                print(f"    [FACE!]  '{f['name']}' built facing {f['claimed']} CONTRADICTS the owner-signed "
                      f"facing {f['read']} — a rebuild regressed a signed read; re-apply the signature")
            elif f.get("verdict") == "ambiguous":
                print(f"    [FACE?]  '{f['name']}' typed to face {f['claimed']}: only a FRONT-edge strip "
                      f"(footboard OR 180-flipped headboard?) — eyeball the orientation")
            else:
                print(f"    [FACE?]  '{f['name']}' typed to face {f['claimed']} but the drawn strip reads "
                      f"{f['read']} (conf {f['confidence']}, 90-deg off) — verify orientation")

    if calib_fails:
        print("\n" + "!" * 74)
        print("CALIBRATION CHECK FAILED — no LONG wall registers at a written grid dim:")
        for c in calib_fails:
            print(f"  - {c.get('axis')}={c.get('mm')}mm (+/-{c.get('tol_mm', 120)}, need a >="
                  f"{c.get('min_len_mm', 1500)}mm wall): none found   {c.get('desc','')}")
        print("  The (scale,ox,oy) triple is likely wrong — every coordinate is suspect. FIX FIRST.")
        print("!" * 74)

    # human-confirm checklist (the honest 'we read this much; sign the rest')
    todo = []
    for r in results:
        for it in r["loose"]:
            if it["status"] == "floating":
                todo.append(f"FIX  [{r['room']}] '{it['name']}' floats on empty floor (IoU {it['iou']:.2f}) — reposition or remove")
            elif it["status"] in ("drift", "on_ink"):
                todo.append(f"SIGN [{r['room']}] '{it['name']}' {it['status']} (IoU {it['iou']:.2f}) — confirm size/position")
        for it in r["fixed"]:
            if it["status"] in ("drift", "unverified"):
                todo.append(f"SIGN [{r['room']}] built-in '{it['name']}' unverified — confirm against BF label/wall")
        for f in r.get("identity", []):
            todo.append(f"SIGN [{r['room']}] two pieces resolve to drawn cluster {f['cluster']} "
                        f"({', '.join(str(x) for x in f['names'])}) — one is misidentified")
        for f in r.get("facing", []):
            if f.get("verdict") == "contradicts_signed":
                todo.append(f"FIX  [{r['room']}] '{f['name']}' built facing {f['claimed']} CONTRADICTS the "
                            f"owner-signed facing {f['read']} — the rebuild regressed the signed read; re-apply it")
            elif f.get("verdict") == "ambiguous":
                todo.append(f"SIGN [{r['room']}] '{f['name']}' facing: only a FRONT-edge strip (footboard or "
                            f"180-flip?) — eyeball which way it faces")
            else:
                todo.append(f"SIGN [{r['room']}] '{f['name']}' facing: typed {f['claimed']}, drawn symbol reads "
                            f"{f['read']} (90-deg off) — confirm which way it faces")
        for c in r["unplaced"]:
            todo.append(f"SIGN [{r['room']}] drawn {c['w']}x{c['d']}mm at ({c['x']},{c['y']}) has NO piece — "
                        f"is it furniture (add) or a label/door (add to placement-review.json)?")
        for c in r.get("merged", []):
            todo.append(f"SIGN [{r['room']}] un-clusterable region {c['w']}x{c['d']}mm at ({c['x']},{c['y']}) "
                        f"— confirm no drawn furniture hides in it (else add to placement-review.json)")
        for d in _long_thin(r):
            todo.append(f"SIGN [{r['room']}] narrow dropped {d['w']}x{d['d']}mm at ({d['x']},{d['y']}) — "
                        f"confirm it is a dimension tick/leader, not a slim piece")
    print("\n" + "-" * 74)
    if todo:
        print("HUMAN-CONFIRM CHECKLIST (nothing below was certified by the machine):")
        for t in todo:
            print("  - " + t)
    else:
        print("No open items — every placed piece matched a drawn cluster.")
    print("-" * 74)
    print(f"OVERALL: {worst}   " + {"FAIL": "(blocks the build — a piece floats on empty floor, or calibration failed)",
                                    "REVIEW": "(build BLOCKED until a human signs off: build with --accept-review)",
                                    "PASS": "(machine-certified)"}[worst])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    _pdf, _target = sys.argv[1], sys.argv[2]
    _page = int(sys.argv[3]) if len(sys.argv) > 3 else None       # else from manifest / default
    _close = float(sys.argv[4]) if len(sys.argv) > 4 else None
    _verdict, _ = run(_pdf, _target, _page, _close)
    sys.exit(1 if _verdict == "FAIL" else 0)
