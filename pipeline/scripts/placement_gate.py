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
import glob
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
_CARDINALS = {"N", "S", "E", "W"}      # valid owner-signed CARDINAL facing values (facing_reader vocab)
_CARD_ROT = {"S": 0, "E": 90, "N": 180, "W": 270}   # cardinal facing letter -> rotation (mirrors facing_reader)


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
    """The owner-signed CARDINAL facing LETTER for a piece, or None. Matches a confirmed-ledger entry
    by NAME (the generator names pieces deterministically) with a size sanity guard.

    SUPERSEDED for the live suppress/apply paths by confirmed_rot (which returns a ROT and also
    understands a non-cardinal numeric {"rot": ...}). This cardinal-LETTER accessor is retained as
    the stable API + its focused cardinal tests; confirmed_rot is what facing_flags (gate) and
    resolve_rot (generators) actually call, so a signature is honoured identically whether it is a
    cardinal letter or a numeric angle.

    LAST usable matching entry wins: the owner's paste workflow APPENDS corrections, so an appended
    correction beats every earlier entry — valid or typo — while a trailing malformed entry never
    erases an earlier valid sign. Same ordering semantic as confirmed_kind (shared-matcher law)."""
    name = piece.get("name")
    if name is None:
        return None
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        fac = e.get("facing")
        if fac not in _CARDINALS:      # a truthy-but-non-cardinal typo ('south','N ',180) must NOT
            continue                   # count — the generator's rot_from_facing would apply nothing
        if e.get("name") == name and _size_consistent(piece, e, size_tol):
            best = fac                 # LAST usable match wins (append-a-correction workflow)
    return best


def _norm_rot(r):
    """r -> int degrees in [0,360), or None if unparseable. Rounds (v4 stores rot to 1 dp)."""
    try:
        return int(round(float(r))) % 360
    except (TypeError, ValueError):
        return None


def confirmed_rot(piece, confirmed, size_tol=0.20):
    """The owner-signed ROTATION (int degrees, [0,360)) for a piece, or None. The rot-aware
    generalisation of confirmed_facing: a confirmed[] entry may carry EITHER a cardinal 'facing'
    letter (S/E/N/W) OR an explicit numeric 'rot' (ANY angle — the non-cardinal case, e.g. the
    terrace tub chairs at 12/335 that a cardinal facing cannot express). Matched by NAME + the SAME
    size guard as confirmed_facing. Precedence: an explicit numeric 'rot' wins over a 'facing' letter
    when both are present (more precise); a malformed 'rot' falls back to the cardinal 'facing'.
    LAST usable matching entry wins: the owner's paste workflow APPENDS corrections, so an appended
    correction beats every earlier entry — valid or typo — while a trailing malformed entry never
    erases an earlier valid sign. Same ordering semantic as confirmed_kind (shared-matcher law). So the
    generator and gate stay in lock-step on 'what did the owner sign'. This is the matcher BOTH the
    gate (facing_flags, to suppress/raise) and the generators (resolve_rot, to APPLY) use."""
    name = piece.get("name")
    if name is None:
        return None
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        if e.get("name") != name or not _size_consistent(piece, e, size_tol):
            continue
        r = _norm_rot(e.get("rot")) if e.get("rot") is not None else None
        if r is not None:
            best = r                   # explicit numeric rot wins within the entry (incl. non-cardinal)
            continue
        card = _CARD_ROT.get(e.get("facing"))
        if card is not None:
            best = card
        # an entry that matched name+size but carries no usable value is SKIPPED — it can neither
        # apply nor ERASE an earlier valid sign (last-USABLE-wins, not last-entry-wins)
    return best


def resolve_rot(name, hand_rot, w, d, confirmed):
    """GENERATOR helper: the effective rotation (degrees) for a facing piece. An owner-signed rot
    (via confirmed_rot — cardinal 'facing' OR numeric 'rot', including NON-cardinal) OVERRIDES the
    hand-typed/hand-read hand_rot. Single-source with the gate (confirmed_rot is exactly what
    facing_flags checks), so the generator and gate can never disagree on what the owner signed.

    Returns (rot, source): source is 'owner-signed' when a signature was found and applied (even if
    it equals hand_rot — provenance for the audit trail), else None. With no matching signature the
    hand_rot is returned unchanged and NO provenance is emitted, so a scene-graph regenerated against
    a ledger with no confirmed[] stays byte-identical to the pre-wiring generator (backward-compatible)."""
    if not confirmed:
        return hand_rot, None
    signed = confirmed_rot({"name": name, "w": w, "d": d}, confirmed)
    if signed is None:
        return hand_rot, None
    return signed, "owner-signed"


def _norm_kind(k):
    """k -> stripped kind string, or None if unusable. kind is owner-signed IDENTITY: only a
    non-empty string counts; None/''/numbers are typos a later appended entry corrects. Exact
    (case-sensitive) — KIND_SYNONYMS normalization is the benchmark lane's business, not the
    ledger's."""
    if isinstance(k, str):
        k = k.strip()
        if k:
            return k
    return None


def confirmed_kind(piece, confirmed, size_tol=0.20):
    """The owner-signed KIND (identity) for a piece, or None. Matched by the SAME name+size join
    as confirmed_rot (exact name + orientation-agnostic ±20% size guard; a sizeless entry always
    matches), LAST usable matching entry wins (append-a-correction workflow). This is the matcher
    BOTH the gate (kind_flags, to suppress/raise) and the generators (resolve_kind, to APPLY) use
    — they can never disagree on what the owner signed."""
    name = piece.get("name")
    if name is None:
        return None
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        if e.get("name") != name or not _size_consistent(piece, e, size_tol):
            continue
        k = _norm_kind(e.get("kind"))
        if k is not None:
            best = k
    return best


def resolve_kind(name, hand_kind, w, d, confirmed):
    """GENERATOR helper mirroring resolve_rot: an owner-signed kind OVERRIDES the hand-read kind.
    Returns (kind, source): source='owner-signed' when a signature was found and applied (even if
    it equals hand_kind — provenance), else None with hand_kind unchanged and NOTHING emitted, so
    a regen against a ledger with no kind signs stays byte-identical.

    IDENTITY ONLY: callers MUST resolve kind AFTER cluster matching — a signature re-labels a
    piece, it never re-routes which drawn blob the piece snaps to (geometry stays machine-layer)."""
    if not confirmed:
        return hand_kind, None
    signed = confirmed_kind({"name": name, "w": w, "d": d}, confirmed)
    if signed is None:
        return hand_kind, None
    return signed, "owner-signed"


# ---- owner-signed ZONE (indoor / outdoor_same_floor / below_grade) --------------------
# Mirrors the confirmed_kind trio. zone is the OWNER's indoor/outdoor/below call — the two-layer
# law's hardest semantic (identity, facing, indoor-vs-outdoor are owner truth): the machine may
# PROPOSE a class via zone_flag.zone_proposals, but the CALL is owner-signed and durable here. It
# closes the one owner-only field the ledger previously could not make stick (the terrace->lounge
# correction had survived only as owner-redrawn geometry, never a re-appliable signature). TWO
# scoping lanes: NAME-scoped (a placed piece, joined by name+size like kind/rot) and GEO-scoped
# (an UNNAMED drawn cluster like a below-grade tree that lives only in plan_cluster output, joined
# geometrically via _sig_dist — the same matcher the dismissed[] ledger uses). _ZONE_TO_FLAGS
# mirrors zone_flag.ZONE_TO_FLAGS (kept local so this pure-logic layer imports without fitz).
_ZONES = ("indoor", "outdoor_same_floor", "below_grade")
_ZONE_TO_FLAGS = {"indoor": (True, True), "outdoor_same_floor": (False, True),
                  "below_grade": (False, False)}


def _norm_zone(z):
    """z -> an exact _ZONES member (stripped) or None. Owner-signed SEMANTIC value: only a known
    class counts; None/''/typo/number -> None so a later appended entry corrects it (mirrors
    _norm_kind). 'outdoor'/'south'/'terrace' are typos here, not classes — they normalise to None."""
    if isinstance(z, str):
        z = z.strip()
        if z in _ZONES:
            return z
    return None


def zone_to_flags(zone):
    """(indoor, floor) booleans for a zone class; unknown/silence -> (True,True) to match
    benchmark_reader._score_binary's 'silence = ordinary this-floor-indoor' semantics."""
    return _ZONE_TO_FLAGS.get(_norm_zone(zone), (True, True))


def scene_zone_decision(item, below_grade_z_mm=None):
    """PURE, bpy-free scene-layer directive for a loose spec item — the GENERATOR helper that lets an
    owner-signed zone actually change the rendered scene (build_room.build_suite / build_floor.build_furniture
    call this; both import bpy, so the DECISION must live here where the top level is stdlib-only).

    TWO-LAYER LAW: only an OWNER SIGNATURE may remove or relocate a piece — a machine-advisory zone
    (zone_flag proposal) NEVER does. So we act ONLY when item['zone_source']=='owner-signed'; any item
    missing that provenance -> 'place' regardless of item.get('zone'). This mirrors how the scene layer
    consumes the already-RESOLVED it['rot']/it['kind'] rather than re-reading the ledger — the ledger
    stays out of Blender.

    The decision key is the FLOOR flag zone_to_flags(zone)[1]: floor True (indoor OR outdoor_same_floor,
    i.e. any same-elevation piece) -> place at the authored z; floor False (below_grade, the sole
    (False,False) class) -> skip (owner-signed 'ground below, NOT a floor-2 object'), or relocate_z if a
    caller opts in with below_grade_z_mm (reserved for a future terrain-aware build; unused today, because
    the enclosed floor-2 scene has no below-grade terrain — a mesh at z<0 would float invisibly under the
    slab). Returns {'action','z_mm','reason'} with action in the closed set {'place','skip','relocate_z'};
    callers branch only on action. `indoor` is advisory metadata (materials/enclosure) — never a directive."""
    if not isinstance(item, dict) or item.get("zone_source") != "owner-signed":
        return {"action": "place", "z_mm": None, "reason": "unsigned: two-layer default (place)"}
    _ind, floor = zone_to_flags(item.get("zone"))
    if floor:
        return {"action": "place", "z_mm": None, "reason": "floor-2 object (same elevation)"}
    if below_grade_z_mm is None:
        return {"action": "skip", "z_mm": None,
                "reason": "below_grade: owner-signed ground-below, NOT a floor-2 object"}
    return {"action": "relocate_z", "z_mm": int(below_grade_z_mm),
            "reason": "below_grade -> ground level (caller opted in)"}


def _entry_name(e):
    """A ledger entry's name normalised to a real name or None: an empty/whitespace 'name' is NOT
    a name (it must NOT route a geo-scoped zone entry into the name lane, where a stray '' would
    hard-FAIL as a detached signature). Mirrors the _norm_* 'usable value or None' discipline."""
    n = e.get("name") if isinstance(e, dict) else None
    if isinstance(n, str):
        n = n.strip()
        return n or None
    return n


def confirmed_zone(piece, confirmed, size_tol=0.20):
    """The owner-signed ZONE for a NAMED placed piece, or None. Matched by the SAME name+size join
    as confirmed_kind (exact name + orientation-agnostic +/-20% size guard; a sizeless entry always
    matches), LAST usable matching entry wins (append-a-correction workflow). Entries carrying NO
    usable name belong to the geo lane (confirmed_zone_cluster) and are SKIPPED here so the two lanes
    never cross-fire — a name-scoped sign can only ever bind a named piece."""
    name = piece.get("name")
    if name is None:
        return None
    best = None
    for e in confirmed or []:
        if not isinstance(e, dict) or _entry_name(e) is None:
            continue
        if _entry_name(e) != name or not _size_consistent(piece, e, size_tol):
            continue
        z = _norm_zone(e.get("zone"))
        if z is not None:
            best = z
    return best


def confirmed_zone_cluster(cluster, confirmed):
    """The owner-signed ZONE for an UNNAMED drawn cluster (e.g. a below-grade tree), or None. GEO
    join: consider ONLY entries with no usable name AND a valid zone; among those the NEAREST
    size/shape-consistent match wins (_sig_dist — the exact matcher apply_dismissals uses). So an
    owner can sign 'that organic blob south of the glass is below_grade' and it binds by GEOMETRY,
    surviving the volatile plan_cluster id, and detaches (REVIEW orphan) if a re-extraction moves it."""
    best, best_d = None, None
    for e in confirmed or []:
        if not isinstance(e, dict) or _entry_name(e) is not None:
            continue
        z = _norm_zone(e.get("zone"))
        if z is None:
            continue
        d = _sig_dist(cluster, e)
        if d is None:
            continue
        if best_d is None or d < best_d:
            best, best_d = z, d
    return best


def resolve_zone(name, hand_zone, w, d, confirmed):
    """GENERATOR helper mirroring resolve_kind: an owner-signed zone OVERRIDES the hand/proposed
    zone for a NAMED piece. Returns (zone, source): source='owner-signed' when applied (even if
    equal — provenance), else (hand_zone, None) with NOTHING emitted, so a regen against a ledger
    with no zone signs stays byte-identical. Resolve AFTER geometry: a zone sign RE-LABELS a piece,
    it never re-routes which drawn blob it snaps to (geometry stays machine-layer)."""
    if not confirmed:
        return hand_zone, None
    signed = confirmed_zone({"name": name, "w": w, "d": d}, confirmed)
    if signed is None:
        return hand_zone, None
    return signed, "owner-signed"


def zone_flags(loose, proposals, confirmed=None):
    """Owner-signed ZONE regression backstop — the zone analog of kind_flags. proposals =
    {name: proposed_zone} (the machine read; default 'indoor' when a name is absent). For every
    loose piece with a SIGNED zone: SUPPRESS when the built/proposed zone equals the sign
    (adjudicated -> converges toward PASS), else raise 'contradicts_signed_zone'. A missing/garbage
    proposal defaults to 'indoor', so a below_grade sign on a machine-indoor piece still surfaces —
    silence cannot silence a sign. REVIEW-only, never FAIL (the indoor/outdoor CALL is owner truth).
    There is NO unsigned geometric branch here (the machine read lives in zone_flag, advisory)."""
    out = []
    for it in loose or []:
        signed = confirmed_zone(it, confirmed)
        if signed is None:
            continue
        built = (_norm_zone(it.get("zone"))
                 or _norm_zone((proposals or {}).get(it.get("name"))) or "indoor")
        if built == signed:
            continue
        out.append({"name": it.get("name"), "kind": it.get("kind"),
                    "verdict": "contradicts_signed_zone", "claimed": built, "read": signed,
                    "confidence": 1.0})
    return out


def reconcile_zone(pieces, clusters, confirmed, size_tol=0.20):
    """Two-lane zone-signature reconcile (mirrors reconcile_confirmed). Returns (matched,
    name_orphaned, geo_orphaned). A NAME-scoped zone entry must bind a placed piece (name+size); a
    name orphan is a DETACHED signature -> the hard-error path (like a detached facing sign, it
    would silently re-roll). A GEO-scoped zone entry must bind a drawn cluster (_sig_match); a geo
    orphan is REVIEW-only (the owner annotated a blob this extraction no longer produces — surfaced,
    never silent). Entries with no valid zone are ignored (they are kind/rot/facing signs)."""
    matched, name_orphaned, geo_orphaned = [], [], []
    for e in confirmed or []:
        if not isinstance(e, dict) or _norm_zone(e.get("zone")) is None:
            continue
        ename = _entry_name(e)
        if ename is not None:
            hit = any(it.get("name") == ename and _size_consistent(it, e, size_tol) for it in pieces)
            (matched if hit else name_orphaned).append(e)
        else:
            hit = any(_sig_match(cl, e) for cl in clusters)
            (matched if hit else geo_orphaned).append(e)
    return matched, name_orphaned, geo_orphaned


def entry_is_inert(e):
    """True when a confirmed[] entry carries NO usable payload (no numeric/cardinal rot AND no
    usable kind AND no usable zone): it can bind a piece by name+size yet apply nothing. Reported
    honestly by the generator instead of hiding behind a reassuring 'N loaded' count."""
    if not isinstance(e, dict):
        return True
    return (_norm_rot(e.get("rot")) is None
            and _CARD_ROT.get(e.get("facing")) is None
            and _norm_kind(e.get("kind")) is None
            and _norm_zone(e.get("zone")) is None)


def load_confirmed(led):
    """Pull the owner-signed 'confirmed' facing entries out of a parsed placement-review ledger
    dict (mirrors the 'dismissed' handling); drops non-dict typos. Returns [] on anything odd."""
    if not isinstance(led, dict):
        return []
    conf = led.get("confirmed", [])
    return [e for e in conf if isinstance(e, dict)] if isinstance(conf, list) else []


def reconcile_confirmed(pieces, confirmed, size_tol=0.20):
    """Match every owner-signed confirmed[] entry to the placed pieces it is meant to govern, using
    the SAME name + size join the gate (confirmed_rot) and the generators (resolve_rot) use — so all
    three agree on which signatures are live. Returns (matched, orphaned): two lists of confirmed
    entries. An entry is MATCHED when some placed piece shares its name AND passes the size guard;
    ORPHANED when it matches NO piece — i.e. the owner signed a facing for a piece that no longer
    exists under that name+size, because a rename or a size edit silently DETACHED the signature.

    An orphan is the sharpest silent re-roll: resolve_rot then falls back to the hand-read facing and
    the piece re-rolls, while a reassuring 'N signatures loaded' count hides it (this already bit once,
    when the tub chairs were renamed off 'ระเบียง'). Callers turn a non-empty `orphaned` into a hard
    build error so the owner is TOLD a sign no longer binds instead of trusting a facing that reverted."""
    matched, orphaned = [], []
    for e in confirmed or []:
        if not isinstance(e, dict):
            continue
        name = e.get("name")
        hit = any(it.get("name") == name and _size_consistent(it, e, size_tol) for it in pieces)
        (matched if hit else orphaned).append(e)
    return matched, orphaned


def reconcile_rooms(room_loose, confirmed_all, size_tol=0.20):
    """GATE-side signature reconcile — the run()-lane backstop. The generator already hard-FAILs
    a detached signature at BUILD time (gen_floor2_v4_specs.assert_signatures_applied), but a
    HAND-EDITED scene-graph the marker trusts never passes through the generator, so the gate
    must re-derive 'does every owner sign still bind a piece' itself. room_loose = [(room_id,
    loose_items)] — LOOSE pieces ONLY (built-ins/fixtures never consult the ledger; a sign that
    merely name-matches one must ORPHAN, not read as live). Pool scoping mirrors the generator's
    four-pool structure exactly (gen_floor2_v4_specs.py main): a room-scoped sign sees ONLY its
    room's pool; a '*' sign sees the UNION (so it is not false-orphaned in the room it doesn't
    live in); an unknown/missing room sees an EMPTY pool (a typo'd room must orphan loudly,
    never be silently skipped by both filters). Returns (matched, orphaned) confirmed entries."""
    union = [it for _rid, loose in room_loose for it in loose]
    by_room = {}
    for rid, loose in room_loose:
        by_room.setdefault(rid, []).extend(loose)
    matched, orphaned = [], []
    for e in confirmed_all or []:
        if not isinstance(e, dict):
            continue
        room = e.get("room")
        pool = union if room == "*" else by_room.get(room, [])
        m, _o = reconcile_confirmed(pool, [e], size_tol)
        (matched if m else orphaned).append(e)
    return matched, orphaned


def facing_flags(loose, fsegs, offset=(0, 0), confirmed=None):
    """ADVISORY facing cross-check for seating/beds: compare each piece's HAND-TYPED rot to the
    facing READ from its drawn headboard/backrest strip (facing_reader). Facing is otherwise
    100% human-authored and 0% machine-checked — a 180-deg-wrong bed still scores IoU ~1.00,
    because a cardinal rotation barely changes the axis-aligned footprint. Returns only the
    clear DISAGREEMENTS; conservative by design (an unreadable/symmetric strip -> 'unknown',
    never a flag), so it adds signal without crying wolf. REVIEW-only, never FAIL.

    A piece whose facing the OWNER has already signed off (confirmed ledger) is checked in ROT space
    for EVERY kind (the generator applies a sign to any kind, so the gate must verify any kind): the
    flag is SUPPRESSED when the built rot matches the sign (adjudication done -> converges toward
    PASS), else 'contradicts_signed' is raised — the regression backstop. The UNSIGNED geometric
    strip-read is the facing-kind-only part (it needs a drawn headboard/backrest symbol)."""
    # facing_reader is needed ONLY for the geometric strip-read (2) and the cosmetic cardinal-letter
    # labels; the owner-signed backstop (1) is pure rot arithmetic (confirmed_rot/_norm_rot). Keep the
    # import OPTIONAL so an unimportable facing_reader degrades gracefully to rot<deg> labels + skips
    # the geometric read, but NEVER disables the regression backstop (which was the whole point of the
    # ledger). _lbl gives the cardinal letter when FR is present + the rot is cardinal, else 'rot<deg>'.
    try:
        import facing_reader as FR
    except ImportError:
        FR = None

    def _lbl(r):
        if r is None:
            return None
        return (FR.facing_from_rot(r) if FR else None) or f"rot{r}"

    out = []
    for it in loose:
        # (1) OWNER-SIGNED check — runs for EVERY loose kind. The generator (resolve_rot) applies an
        # owner sign to ANY kind (bench / side_table / console too), so the gate must verify ANY kind,
        # else a re-rolled or hand-edited signed non-facing piece slips through. Compared in ROT space
        # so a non-cardinal sign (an angled chair at 12/335) is handled; claimed/read show the cardinal
        # letter when cardinal, else a 'rot<deg>' label. A MALFORMED built rot NEVER suppresses (it
        # cannot be shown to match) -> a garbage orientation can't silence an owner's signature.
        signed_rot = confirmed_rot(it, confirmed)
        if signed_rot is not None:
            built_rot = _norm_rot(it.get("rot", 0))
            if built_rot is not None and built_rot == signed_rot:
                continue                  # built orientation agrees with the sign -> adjudicated
            out.append({"name": it.get("name"), "kind": it.get("kind"),
                        "verdict": "contradicts_signed", "claimed": _lbl(built_rot),
                        "read": _lbl(signed_rot),
                        "confidence": 1.0})
            continue
        # (2) UNSIGNED geometric cross-check — needs a drawn headboard/backrest SYMBOL (facing_reader),
        # so facing kinds only. rot defaults to 0 (=S) when the generator omits it.
        if FR is None or it.get("kind") not in _FACING_KINDS:
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


def kind_flags(loose, confirmed=None):
    """Owner-signed IDENTITY backstop — the kind analog of facing_flags branch (1). For every
    loose piece with a signed kind: SUPPRESS when the built kind equals the sign (adjudicated),
    else raise 'contradicts_signed_kind' — the regression backstop. There is NO unsigned branch:
    no geometric identity read exists (identity is owner-only semantic truth; the gate's
    identity_check stays a double-claim detector only). A piece whose built kind is missing or
    malformed can never be shown to match -> flagged, so silence cannot silence a signature."""
    out = []
    for it in loose or []:
        signed = confirmed_kind(it, confirmed)
        if signed is None:
            continue
        built = _norm_kind(it.get("kind"))
        if built is not None and built == signed:
            continue
        out.append({"name": it.get("name"), "kind": built, "verdict": "contradicts_signed_kind",
                    "claimed": built, "read": signed, "confidence": 1.0})
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


# The REQUIRED pre-owner review overlay artifacts. raster_overlay.render_read_overlay writes
# <out_base>_<room>.png per room + <out_base>_full.png + <out_base>.md; out_base is
# 'review-read-vs-sheet' next to the manifest (raster_overlay.main default, raster_overlay.py
# ~line 322, AND the v4 generator's hardcoded call, gen_floor2_v4_specs.py ~line 449).
OVERLAY_PREFIX = "review-read-vs-sheet"


def overlay_inputs(base_dir):
    """Overlay files present next to the gated target: sorted absolute paths. ONLY the
    review-read-vs-sheet* convention — other review-*.png in a layout dir are ad-hoc session
    artifacts and must NOT churn the marker."""
    return sorted(os.path.abspath(p)
                  for p in glob.glob(os.path.join(base_dir, OVERLAY_PREFIX + "*"))
                  if os.path.isfile(p))


def overlay_required(man_dir, marker_inputs):
    """BUILD-side required-set for overlay freshness: {basename: path} of every overlay file
    that must hash-match the marker. UNION of (files present now) and (overlay names the marker
    recorded), so: regenerated/edited after gating -> hash mismatch -> refuse; DELETED after
    gating -> path missing -> hash None -> refuse; appeared after gating -> no marker hash ->
    refuse; absent-in-both -> quiet. Same present-and-matching-or-absent-in-both rule the
    placement-review.json ledger already gets in build_floor.require_placement_gate."""
    now = {os.path.basename(p): p for p in overlay_inputs(man_dir)}
    names = set(now) | {n for n in (marker_inputs or {}) if n.startswith(OVERLAY_PREFIX)}
    return {n: now.get(n, os.path.join(man_dir, n)) for n in sorted(names)}


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


# ---- ZONE (indoor / outdoor / below-grade) advisory pass -----------------------------
ZONE_SOUTH_SCAN = 2100.0       # mm; how far south of the facade datum the exterior-object pass
#                                scans for below-grade clusters (verified to surface the garden tree)
ZONE_OBJECT_MAX_EXT = 3500.0   # mm; a south cluster larger than this is boundary / dimension
#                                LINEWORK, not a discrete below-grade OBJECT — counted honestly in
#                                exterior_linework_n, never proposed as an object (mirrors the gate's
#                                merged_blob discipline: a room-spanning blob is not a piece).


def _zone_room(spec, offset, glazing_cands, wall_segs, confirmed_room, south_items, dismissed_room):
    """ADVISORY zone pass for one room (PURE logic; the fitz south-band extraction is done by run()
    and handed in as south_items). Classifies placed pieces (proves indoor / catches a signed-
    outdoor piece) plus object-scale exterior clusters (below-grade candidates). REVIEW-only, never
    FAIL, never auto-applied — the indoor/outdoor CALL is owner semantic truth (two-layer law); the
    machine only PROPOSES. A south cluster the owner has already GEO-signed (confirmed_zone_cluster)
    is adjudicated and suppressed from the open list, so one sign stops the nag (burden paid once).
    Returns (r_zone, r_zone_flags, obj_clusters, open_proposals)."""
    import zone_flag as ZF
    outline = [[p[0] + offset[0], p[1] + offset[1]] for p in spec["room"]["outline_mm"]]
    loose, fixed = _pieces(spec)
    placed_els = [{"ref": it.get("name"), "fp": footprint(it, offset),
                   "w": it.get("w"), "d": it.get("d"),
                   "curve": (it.get("shape") == "round"), "unplaced": False}
                  for it in (loose + fixed) if "w" in it and "d" in it]
    # exterior south clusters: drop dismissed ones, then split OBJECTS from room-spanning LINEWORK
    south_norm = [{"id": c.get("id"), "x": c["x"], "y": c["y"], "w": c["w"], "d": c["d"],
                   "area_m2": c.get("area_m2"), "curve": c.get("curve"), "fill": c.get("fill")}
                  for c in (south_items or [])]
    kept_after_dismiss, _dis = apply_dismissals(south_norm, dismissed_room or [])
    obj_clusters, linework_n = [], 0
    for c in kept_after_dismiss:
        if max(c["w"], c["d"]) > ZONE_OBJECT_MAX_EXT:     # boundary/dimension linework, not an object
            linework_n += 1
            continue
        obj_clusters.append(c)                            # size FLOOR applied by classify_element
    cluster_els = [{"ref": {"x": c["x"], "y": c["y"], "w": c["w"], "d": c["d"], "curve": c.get("curve")},
                    "fp": cluster_bbox(c), "w": c["w"], "d": c["d"],
                    "area_m2": c.get("area_m2"), "curve": c.get("curve"), "unplaced": True}
                   for c in obj_clusters]
    res = ZF.zone_proposals(placed_els + cluster_els, outline, glazing_cands, wall_segs)
    proposals_by_name = {p["ref"]: p["zone"] for p in res["proposals"] if isinstance(p["ref"], str)}
    # the zone pass classifies loose AND fixed (built-ins), so the signed-zone backstop + adjudication
    # must see loose+fixed too — else an owner zone sign on a PRESENT builtin reads as detached and the
    # build hard-FAILs (a two-layer-law breach: FAIL on owner adjudication of a real piece).
    placed = loose + fixed
    placed_by_name = {it.get("name"): it for it in placed}
    r_zone_flags = zone_flags(placed, proposals_by_name, confirmed=confirmed_room)
    # adjudicate: a piece/cluster the owner has already signed is settled -> off the open REVIEW list
    open_props = []
    for p in res["proposals"]:
        ref = p.get("ref")
        if isinstance(ref, dict):                       # GEO lane: an unnamed drawn cluster
            signed = confirmed_zone_cluster(ref, confirmed_room or [])
        else:                                           # NAME lane: a placed piece
            signed = confirmed_zone(placed_by_name.get(ref, {"name": ref}), confirmed_room or [])
        p["signed_zone"] = signed
        if signed is not None:
            continue                                    # adjudicated
        open_props.append(p)
    r_zone = {
        "corroborated": res["corroborated"],
        "facade_glazing_c": res["facade"].get("glazing_c"),
        "proposals": res["proposals"],
        "open_proposals_n": len(open_props),
        "below_grade_n": sum(1 for p in res["proposals"] if p["zone"] == "below_grade"),
        "exterior_linework_n": linework_n,
        # corroborated facade but NOTHING surfaced south = the invisibility risk (the tree drifting
        # out of the scan band) — surfaced as a note rather than a quiet green room.
        "exterior_unscanned": bool(res["corroborated"] and not (south_items or [])),
    }
    return r_zone, r_zone_flags, obj_clusters, open_props


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
    wall_segs = []
    if wj:
        for cand in [wj, os.path.join(base, os.path.basename(wj))]:
            if os.path.exists(cand):
                input_paths.append(os.path.abspath(cand))
                try:
                    _w = json.load(open(cand, encoding="utf-8"))
                    wall_segs = _w.get("segments", []) if isinstance(_w, dict) else []
                except (ValueError, OSError):
                    wall_segs = []
                break

    # bind glazing-candidates.json (the thin-line facade DETECTOR's output) so the zone-advisory
    # pass's facade line is marker-enforced: re-deriving the facade after this gate run hash-
    # mismatches and refuses the build, exactly like a spec/wall edit. Absent -> the zone pass
    # simply abstains (no facade corroboration), never crashes.
    glazing_cands = []
    for cand in [os.path.join(base, "glazing-candidates.json")]:
        if os.path.exists(cand):
            input_paths.append(os.path.abspath(cand))
            try:
                _g = json.load(open(cand, encoding="utf-8"))
                glazing_cands = _g.get("candidates", []) if isinstance(_g, dict) else []
            except (ValueError, OSError):
                glazing_cands = []

    # bind the REQUIRED pre-owner review overlay so overlay freshness is marker-enforced: the
    # owner signs off a REVIEW by SCANNING review-read-vs-sheet*; regenerating the overlay AFTER
    # this gate run (a generator rerun) hash-mismatches and refuses the build exactly like the
    # spec edit that caused it. Order of operations is deliberate: overlay is a generator
    # artifact produced BEFORE gating; a post-gate overlay is by definition un-gated.
    ov_paths = overlay_inputs(base)
    input_paths.extend(ov_paths)
    if not ov_paths:
        print("  [!] no review-read-vs-sheet* overlay next to the target -- overlay freshness "
              "NOT bound (fine for targets without an owner-review lane)")

    ledger_path = os.path.join(base, "placement-review.json")
    dismissed_all, confirmed_all = [], []
    ledger_malformed = False
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
                  f"{len(confirmed_all)} signed entr(y/ies) on file (facing/kind)")
        except (ValueError, OSError, AttributeError, TypeError):
            ledger_malformed = True
            print("  [!] placement-review.json malformed -- ignoring dismissals/confirmations")

    import zone_flag as _ZF                 # pure module (no fitz); the south-band extraction is run() lane
    results, worst = [], "PASS"
    rooms_loose = []                     # (room_id, loose) pools for the facing/kind signature backstop
    rooms_south = []                     # (room_id, obj_clusters) for the zone-signature GEO backstop
    rooms_zone_pieces = []               # loose+fixed pools for the zone-signature NAME backstop (the
    #                                      zone pass classifies built-ins too, so its reconcile must)
    order = {"PASS": 0, "REVIEW": 1, "FAIL": 2}
    for room_id, spec, offset, _sp in rooms:
        loose, fixed = _pieces(spec)
        rooms_loose.append((room_id, loose))
        zone = _room_zone(spec, offset)
        res = extract_clusters(pdf, page, zone, close_mm, calib=calib)
        dismissed_room = [e for e in dismissed_all if e.get("room") in (room_id, "*")]
        confirmed_room = [e for e in confirmed_all if e.get("room") in (room_id, "*")]
        r = gate(loose, fixed, res["items"], _ink_counter(res), zone, offset,
                 dismissed=dismissed_room, dropped=res.get("dropped"))
        r["room"] = room_id
        r["dropped"] = res.get("dropped", [])
        r["facing"] = facing_flags(loose, res["fsegs"], offset, confirmed=confirmed_room)
        r["kind"] = kind_flags(loose, confirmed=confirmed_room)
        # ZONE advisory pass (indoor/outdoor/below-grade). The default room zone stops ~150mm south
        # of the outline, so a below-grade element (the garden tree at y<0) is CLIPPED OUT and the
        # gate would report a clean all-indoor room — the exact F3 wound looking green. So when the
        # south edge corroborates a glazed facade, run a SEPARATE south-band extraction (never widen
        # _room_zone — it is tuned against cluster merges) and classify what surfaces. REVIEW-only.
        _south_kept, _open = [], []
        try:
            outline_abs = [[p[0] + offset[0], p[1] + offset[1]] for p in spec["room"]["outline_mm"]]
            _ys, _xlo, _xhi = _ZF.facade_datum(outline_abs)
            _corr, _ = _ZF.facade_corroborated(_ys, _xlo, _xhi, glazing_cands, wall_segs)
            south_items = []
            if _corr:
                _band = (_xlo, _ys - ZONE_SOUTH_SCAN, _xhi, _ys + _ZF.DEFAULTS["y_below_margin"])
                south_items = extract_clusters(pdf, page, _band, close_mm, calib=calib)["items"]
            r["zone"], r["zone_flags"], _south_kept, _open = _zone_room(
                spec, offset, glazing_cands, wall_segs, confirmed_room, south_items, dismissed_room)
        except Exception as _e:
            # ADVISORY ONLY: a zone-pass bug (or an extraction hiccup) must NEVER abort the gate or
            # change a geometry verdict — mirrors facing_flags' try guard. Degrade to no proposals.
            r["zone"] = {"corroborated": False, "proposals": [], "open_proposals_n": 0,
                         "below_grade_n": 0, "exterior_linework_n": 0, "exterior_unscanned": False,
                         "error": str(_e)}
            r["zone_flags"] = []
        rooms_south.append((room_id, _south_kept))
        rooms_zone_pieces.append(loose + fixed)
        if (r["facing"] or r["kind"] or r["zone_flags"] or _open or r["zone"]["exterior_unscanned"]) \
                and order[r["verdict"]] < order["REVIEW"]:
            r["verdict"] = "REVIEW"        # a signed-semantic (facing/kind/zone) disagreement or an
            #                                open below-grade candidate needs a human — never a FAIL
        results.append(r)
        if order[r["verdict"]] > order[worst]:
            worst = r["verdict"]

    # signature-reconcile BACKSTOP: the generator hard-FAILs a detached sign at build time
    # (assert_signatures_applied), but a hand-edited scene-graph never passes through the
    # generator — re-derive it here from the specs actually gated. MANIFEST LANE ONLY: ledger
    # 'room' values are manifest furnish ids ('sitting_room'); a single scene-graph's room type
    # ('bedroom_suite') does not match them, so reconciling there would false-orphan every sign.
    if "furnish" in doc and ledger_malformed:
        # honesty: an UNREADABLE ledger is unreported -- reconciling against the defaulted
        # confirmed_all=[] would mint a zero-orphan claim for signatures nobody could read
        sig_reconcile = {"checked": False,
                         "note": "placement-review.json malformed -- signatures unreadable"}
        print("  [!] signature reconcile SKIPPED (placement-review.json malformed -- "
              "signatures unreadable)")
    elif "furnish" in doc:
        _sm, _so = reconcile_rooms(rooms_loose, confirmed_all)
        sig_reconcile = {"checked": True, "matched": len(_sm),
                         "orphaned_names": [e.get("name") for e in _so]}
        print(f"signature reconcile (gate backstop): {len(_sm)} matched, {len(_so)} orphaned")
        if _so:
            if order["FAIL"] > order[worst]:
                worst = "FAIL"
            print("!" * 74)
            print("DETACHED OWNER SIGNATURE(S): these confirmed[] entries bind NO loose piece in")
            print("the gated scene-graphs (a rename/resize/hand-edit detached them) — the signed")
            print("value would silently re-roll. Fix the ledger or the scene-graph, then re-gate:")
            for e in _so:
                print(f"  - {e.get('name')!r} (room={e.get('room')!r} w={e.get('w')} "
                      f"d={e.get('d')} sign={e.get('rot', e.get('facing'))})")
            print("!" * 74)
    else:
        # honesty: unreported, never a defaulted zero-orphan claim
        sig_reconcile = {"checked": False,
                         "note": "single scene-graph target: ledger rooms are manifest-scoped"}
        if confirmed_all:
            print("  [i] signature reconcile SKIPPED (single scene-graph target; ledger rooms "
                  "are manifest-scoped) -- gate the manifest to get the backstop")

    # ZONE-signature reconcile (two-lane, mirrors the facing/kind backstop). Manifest lane only —
    # same room-scoping reason as sig_reconcile. A NAME-scoped confirmed_zone binding no placed
    # piece is a DETACHED signature -> hard error (the signed indoor/outdoor call would silently
    # revert, exactly like a detached facing). A GEO-scoped zone sign (an unnamed cluster like the
    # tree) binding no drawn cluster is REVIEW: the owner annotated a blob this extraction no longer
    # produces — surfaced, never silent.
    zone_reconcile = {"checked": False, "note": "not a manifest target or ledger unreadable"}
    if "furnish" in doc and not ledger_malformed:
        _union_pieces = [it for pieces in rooms_zone_pieces for it in pieces]   # loose+fixed (name lane)
        _union_south = [c for _rid, sc in rooms_south for c in sc]              # exterior clusters (geo lane)
        _zm, _zno, _zgo = reconcile_zone(_union_pieces, _union_south, confirmed_all)
        zone_reconcile = {"checked": True, "matched": len(_zm),
                          "name_orphans": [e.get("name") for e in _zno],
                          "geo_orphans": len(_zgo)}
        if _zno:
            if order["FAIL"] > order[worst]:
                worst = "FAIL"
            print("!" * 74)
            print("DETACHED ZONE SIGNATURE(S): a NAME-scoped confirmed_zone binds NO loose piece —")
            print("the signed indoor/outdoor call would silently revert. Fix ledger/scene-graph:")
            for e in _zno:
                print(f"  - {e.get('name')!r} (room={e.get('room')!r} zone={e.get('zone')!r})")
            print("!" * 74)
        elif _zgo:
            if order["REVIEW"] > order[worst]:
                worst = "REVIEW"
            print(f"zone reconcile: {len(_zm)} matched, {len(_zgo)} GEO-orphan (REVIEW) — an owner "
                  f"below-grade annotation binds no drawn cluster in this extraction")

    calib_fails = _run_calibration_check(doc, base)
    if calib_fails and order["FAIL"] > order[worst]:
        worst = "FAIL"

    _report(results, worst, calib_fails)
    marker = _write_marker(target, worst, results, input_paths, calib_fails, sig_reconcile,
                           zone_reconcile)
    print(f"wrote gate marker: {marker}  (build refuses on FAIL, on un-signed REVIEW, or when an "
          f"input hash no longer matches)")
    return worst, results


def _write_marker(target, worst, results, input_paths, calib_fails=None, sig_reconcile=None,
                  zone_reconcile=None):
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
        "signature_reconcile": sig_reconcile if sig_reconcile is not None else {"checked": False},
        "zone_reconcile": zone_reconcile if zone_reconcile is not None else {"checked": False},
        "rooms": [{"room": r["room"], "verdict": r["verdict"],
                   "floating": [x["name"] for x in (r["loose"] + r["fixed"]) if x["status"] == "floating"],
                   "unplaced": len(r["unplaced"]),
                   "merged_regions": len(r.get("merged", [])),
                   "dismissed": len(r.get("dismissed", [])),
                   "identity_flags": len(r.get("identity", [])),
                   "facing_flags": len(r.get("facing", [])),
                   "kind_flags": len(r.get("kind", [])),
                   "zone_flags": len(r.get("zone_flags", [])),
                   "zone_below_grade": r.get("zone", {}).get("below_grade_n", 0),
                   "zone_open": r.get("zone", {}).get("open_proposals_n", 0),
                   "zone_exterior_linework": r.get("zone", {}).get("exterior_linework_n", 0),
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
        for f in r.get("kind", []):
            print(f"    [KIND!]  '{f['name']}' built kind '{f['claimed']}' CONTRADICTS the owner-signed "
                  f"kind '{f['read']}' — a rebuild regressed a signed identity; regenerate to re-apply it")

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
        for f in r.get("kind", []):
            todo.append(f"FIX  [{r['room']}] '{f['name']}' built kind '{f['claimed']}' CONTRADICTS the "
                        f"owner-signed kind '{f['read']}' — regenerate so the signed identity is re-applied")
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
