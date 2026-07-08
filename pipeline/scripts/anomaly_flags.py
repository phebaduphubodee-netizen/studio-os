"""anomaly_flags.py -- Tier-1 self-doubt check: flag a read that violates a PRIOR.

A piece whose CLAIMED kind (owner-signed identity, two-layer law) is contradicted by its own
geometry -- an impossible size/aspect for that kind, or an abnormal COUNT of a kind in one room
(3 nightstands, 2 toilets, 2 beds) -- is DOUBTED here. The module NEVER re-labels a piece, never
writes a value, never auto-corrects: it emits an advisory REVIEW record ("this piece is signed
'bed' but its 400x400 footprint is impossible for a bed -- check identity or dimensions") and
leaves the call to the owner. That is the whole two-layer law: geometry is machine-solved, kind /
identity is owner truth; the machine may only point at a contradiction between the two.

    check_room(spec, priors=None, params=None) -> list[record]     (pure: loaded dict -> records)
    check_coverage(spec, priors=None, params=None) -> coverage dict (honest READ/UNWIRED/ABSENT)

TWO evidence sources, so the module is USEFUL with NO corpus artifact (there is none locally yet):

  * BUILT-IN sane bounds (BUILTIN_BOUNDS, COUNT_MAX below) -- coarse, documented, ergonomics-
    derived per-kind mm ranges + per-kind expected-max counts. Deliberately GENEROUS: a violation
    is therefore GROSS (a bed shorter than 1.2 m, a wardrobe at 1:8) -> HIGH size / MEDIUM aspect.
    These ALWAYS run; they catch the impossible cases without any corpus. Kinds that legitimately
    span huge ranges (cabinet, headboard) are OMITTED rather than false-flagged -- an omitted kind
    is honestly reported in coverage as "no bound", never a silent clean pass.

  * PRIOR bands (when `priors` is a kind_priors artifact, schema interior-ai/kind-priors@0.1) --
    tight corpus quantile bands. A footprint FAR outside its claimed kind's band -> MEDIUM size.
    Precise, corpus-grounded. UNWIRED (never "clean") when no priors are supplied.

CONSERVATIVE by design (mirrors placement_gate.facing_flags): when a dimension is missing/ambiguous
or the kind has no bound, ABSTAIN (emit nothing) rather than cry wolf. Every flag is a defensible
contradiction. TWO-LAYER SUPPRESSION: a piece whose kind the owner has SIGNED (placement_gate.
confirmed_kind, passed via params['confirmed']) is adjudicated -> its anomaly flags are suppressed,
and an over-count explained by owner signatures is suppressed too. An owner signature ALWAYS wins.

Pure-logic / stdlib top level (+ `import placement_gate`, whose top is stdlib-only). No fitz/bpy/
numpy, no disk I/O, no randomness, no Date.now -- outputs are sorted + deterministic.
"""
import math

import placement_gate as PG

SCHEMA = "interior-ai/anomaly-flags@0.1"
MODULE = "anomaly_flags"

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# ---- BUILT-IN sane bounds (mm), coarse + GENEROUS so any violation is genuinely gross --------
# Per kind: (min_short, max_short, min_long, max_long, max_aspect).  short = min(w,d), long =
# max(w,d), aspect = long/short.  Derived from interior ergonomics common sense, NOT a corpus:
#   * a bed is never < ~1.2 m on its long side, nor absurdly narrow;
#   * a nightstand / side_table is small (<~1 m) and near-square;
#   * a wardrobe run can be long (a wall of units) but never 1:8 slim.
# Bounds are wide on purpose: they must NOT flag any legitimately-drawn real piece (verified on the
# PRJ-2026-002 v4 sitting_room + master_bedroom, both correct reads), only the impossible ones.
# Kinds that legitimately span extreme ranges are DELIBERATELY ABSENT (reported as "no bound", never
# a false pass): cabinet (a 4.1 m TV-shelf run at 300 deep is real), headboard (a 3.25 m x 100 slat).
BUILTIN_BOUNDS = {
    #             min_short max_short min_long max_long max_aspect
    "bed":          (700,   2600,   1200,   3000,   2.5),
    "nightstand":   (150,    950,    200,   1000,   3.0),
    "side_table":   (150,   1000,    200,   1200,   3.0),
    # sofa max_short is DELIBERATELY generous (3000): an L-/U-sectional entered as a single
    # bounding box legitimately has a large SHORT side (both legs inside the AABB) -- a common Thai
    # living-room config. A straight sofa never reaches it; a genuinely-wrong tiny/huge sofa still
    # trips min_short 600 / max_long 4000 / aspect. (Was 1500 -> false-fired HIGH on L-sofas.)
    "sofa":         (600,   3000,   1100,   4000,   4.5),
    "loveseat":     (600,   1200,    900,   2200,   3.5),
    "armchair":     (350,   1200,    350,   1300,   2.2),
    "chair":        (300,    800,    300,    900,   2.2),
    "dining_chair": (300,    800,    300,    900,   2.2),
    "console":      (200,    800,    500,   2600,   6.0),
    "bench":        (250,   1000,    500,   2200,   4.5),
    "tv_console":   (250,    900,    500,   3200,   7.0),
    "desk":         (400,   1100,    700,   2600,   4.5),
    "coffee_table": (300,   1100,    400,   1800,   3.5),
    "dining_table": (600,   1600,    800,   4000,   4.5),
    "wardrobe":     (300,   1100,    400,   3800,   7.5),
    "vanity_double":(300,    800,    800,   3400,   7.0),
    "vanity":       (300,    800,    400,   1600,   3.5),
    "toilet":       (250,    900,    450,   1000,   2.8),
    "bathtub":      (550,   1300,   1300,   2200,   3.2),
    "shower":       (600,   1700,    600,   1900,   2.4),
    "stool":        (200,    800,    200,    900,   2.2),
    "ottoman":      (250,    900,    250,   1100,   2.5),
}

# Per-kind expected MAX count within one container (the main room = builtins + items, or one
# subroom's fixtures[]).  Only kinds whose duplication is a GENUINE anomaly are listed -- pieces
# that legitimately repeat (side_table end tables, wardrobe runs, cabinets) are intentionally NOT
# counted.  (max, severity, confidence).  toilet/bathtub over-count is nearly always wrong -> HIGH;
# a second bed (twin room) or a third nightstand is a softer, defensible doubt -> MEDIUM.
COUNT_MAX = {
    "bed":        (1, "MEDIUM", 0.60),
    "nightstand": (2, "MEDIUM", 0.60),
    "toilet":     (1, "HIGH",   0.85),
    "bathtub":    (1, "HIGH",   0.80),
}

# how far outside a tight corpus band counts as "FAR outside" -> a MEDIUM prior-band size doubt.
# 10-90 quantile bands already exclude ~20% of legit pieces, so being just-outside is NOT alarming;
# we require a wide margin beyond the band edge before crying wolf.
PRIOR_FAR = 0.40   # flag only if below band_lo*(1-PRIOR_FAR) or above band_hi*(1+PRIOR_FAR)


# ---- record + helpers ------------------------------------------------------------------------
def _rec(check, severity, confidence, room, subjects, detail, why, resolve_by):
    return {"signal": f"{MODULE}:{check}", "severity": severity,
            "confidence": round(float(confidence), 3), "room": room,
            "subjects": list(subjects), "detail": detail, "why": why,
            "resolve_by": resolve_by}


def _dims(piece):
    """(short, long, aspect) intrinsic to the piece (its own w x d, NOT a rotated AABB -- a bed
    rotated 45 deg is still a bed-sized bed).  None if either extent is missing/non-positive
    (ABSTAIN -- a piece we cannot measure is never flagged)."""
    try:
        w = float(piece.get("w"))
        d = float(piece.get("d"))
    except (TypeError, ValueError):
        return None
    if w <= 0 or d <= 0:
        return None
    lo, hi = sorted((w, d))
    return (lo, hi, hi / lo)


def _name(piece):
    return piece.get("name") or piece.get("kind") or "?"


def _containers(spec):
    """[(room_label, [pieces])].  The main room = builtins + items (counted together -- the
    counted kinds never appear as built-ins); each subroom contributes its fixtures[] as its OWN
    container, so toilets are counted per-bathroom (a 2-bathroom suite is never a false 2-toilet
    flag)."""
    if not isinstance(spec, dict):
        return []
    room = (spec.get("room") or {})
    main_label = room.get("type") or "room"
    main = list(spec.get("builtins") or []) + list(spec.get("items") or [])
    out = [(main_label, [p for p in main if isinstance(p, dict)])]
    for sr in (spec.get("subrooms") or []):
        if not isinstance(sr, dict):
            continue
        label = sr.get("name") or sr.get("type") or "subroom"
        out.append((label, [p for p in (sr.get("fixtures") or []) if isinstance(p, dict)]))
    return out


def _signed_kind(piece, confirmed):
    """The owner-signed kind for this piece (placement_gate.confirmed_kind), or None.  The single
    two-layer authority: if the owner signed this identity, the machine's prior-based doubt about
    it is adjudicated."""
    if not confirmed:
        return None
    try:
        return PG.confirmed_kind(piece, confirmed)
    except Exception:
        return None


def _is_kind_signed(piece, confirmed):
    """True iff the owner has signed THIS piece's current kind (identity adjudicated)."""
    sk = _signed_kind(piece, confirmed)
    return sk is not None and sk == PG._norm_kind(piece.get("kind"))


# ---- prior-band (corpus) helpers -------------------------------------------------------------
def _prior_band(priors, kind):
    """The kind's band dict from a kind_priors artifact, or None.  Tolerant of a missing/oddly
    shaped priors doc (returns None -> the prior lane simply does not fire)."""
    if not isinstance(priors, dict):
        return None
    kinds = priors.get("kinds")
    if not isinstance(kinds, dict):
        return None
    b = kinds.get(kind)
    return b if isinstance(b, dict) else None


def _far_outside(val, band):
    """True if val is FAR (> PRIOR_FAR beyond the edge) outside [band_lo, band_hi]."""
    try:
        lo, hi = float(band[0]), float(band[1])
    except (TypeError, ValueError, IndexError):
        return False
    return val < lo * (1.0 - PRIOR_FAR) or val > hi * (1.0 + PRIOR_FAR)


# ---- the three checks ------------------------------------------------------------------------
def _check_size(room, piece, kind, lo, hi, priors):
    """size_implausible.  HIGH when outside the coarse built-in bounds (grossly impossible for the
    claimed kind); else MEDIUM when a corpus prior band exists and the footprint is FAR outside it.
    At most one size record per piece (gross HIGH supersedes the softer prior MEDIUM)."""
    b = BUILTIN_BOUNDS.get(kind)
    if b is not None:
        min_s, max_s, min_l, max_l, _asp = b
        bad = []
        if lo < min_s:
            bad.append(f"short side {lo:.0f}mm < {min_s}mm")
        if lo > max_s:
            bad.append(f"short side {lo:.0f}mm > {max_s}mm")
        if hi < min_l:
            bad.append(f"long side {hi:.0f}mm < {min_l}mm")
        if hi > max_l:
            bad.append(f"long side {hi:.0f}mm > {max_l}mm")
        if bad:
            return _rec(
                "size_implausible", "HIGH", 0.90, room, [_name(piece)],
                f"'{_name(piece)}' is typed '{kind}' but its {lo:.0f}x{hi:.0f}mm footprint is "
                f"impossible for a {kind} ({'; '.join(bad)}; sane {kind} long side "
                f"{min_l}-{max_l}mm)",
                "the CLAIMED identity (kind) and the drawn/entered dimensions are two independent "
                "reads and they contradict -- either the label is wrong or a dimension was "
                "mis-read/mis-typed",
                "check the piece on the sheet: re-read its dimensions, or owner-sign the correct "
                "kind -- the module never re-labels it for you")
    # prior-band (corpus) lane -- only if built-in bounds passed / kind has no built-in bound
    band = _prior_band(priors, kind)
    if band is not None:
        lo_band, hi_band = band.get("lo_mm"), band.get("hi_mm")
        far = []
        if isinstance(lo_band, (list, tuple)) and _far_outside(lo, lo_band):
            far.append(f"short {lo:.0f}mm outside band {lo_band}")
        if isinstance(hi_band, (list, tuple)) and _far_outside(hi, hi_band):
            far.append(f"long {hi:.0f}mm outside band {hi_band}")
        if far:
            return _rec(
                "size_implausible", "MEDIUM", 0.55, room, [_name(piece)],
                f"'{_name(piece)}' typed '{kind}' is far outside the corpus size band for a "
                f"{kind} ({'; '.join(far)})",
                "the footprint sits well beyond the tight corpus quantile band for this claimed "
                "kind -- a softer identity/dimension doubt than a gross-bounds violation",
                "confirm the dimensions or the identity against the sheet")
    return None


def _check_aspect(room, piece, kind, lo, hi, aspect, priors):
    """aspect_implausible (MEDIUM).  A footprint far too elongated for the claimed kind (a
    'wardrobe' at 1:8, a 'nightstand' at 1:6).  Built-in max-aspect always; prior aspect band far-
    outside when priors exist."""
    b = BUILTIN_BOUNDS.get(kind)
    if b is not None:
        max_asp = b[4]
        if aspect > max_asp:
            return _rec(
                "aspect_implausible", "MEDIUM", 0.60, room, [_name(piece)],
                f"'{_name(piece)}' typed '{kind}' has aspect {aspect:.1f}:1, implausible for a "
                f"{kind} (max ~{max_asp:.0f}:1)",
                "a {k}'s proportions are ergonomically bounded; this footprint is far too "
                "elongated for the claimed kind".format(k=kind),
                "confirm the dimensions, or re-identify the piece -- a long-thin blob may be "
                "linework mis-clustered as furniture, not a real {k}".format(k=kind))
    band = _prior_band(priors, kind)
    if band is not None:
        asp_band = band.get("aspect")
        if isinstance(asp_band, (list, tuple)) and _far_outside(aspect, asp_band):
            return _rec(
                "aspect_implausible", "MEDIUM", 0.55, room, [_name(piece)],
                f"'{_name(piece)}' typed '{kind}' has aspect {aspect:.1f}:1, far outside the "
                f"corpus aspect band {asp_band} for a {kind}",
                "the proportion sits well beyond the corpus aspect band for this claimed kind",
                "confirm the dimensions or the identity against the sheet")
    return None


def _check_counts(room, pieces, confirmed):
    """count_anomaly.  More of a kind in one container than plausibly fits.  An over-count that is
    fully explained by owner kind-signatures is suppressed (the owner confirmed every one); only
    the UNSIGNED surplus is a doubt (unsigned_count > max)."""
    out = []
    by_kind = {}
    for p in pieces:
        k = PG._norm_kind(p.get("kind"))
        if k is None:
            continue
        by_kind.setdefault(k, []).append(p)
    for kind in sorted(by_kind):
        if kind not in COUNT_MAX:
            continue
        max_n, sev, conf = COUNT_MAX[kind]
        group = by_kind[kind]
        total = len(group)
        if total <= max_n:
            continue
        unsigned = [p for p in group if not _is_kind_signed(p, confirmed)]
        if len(unsigned) <= max_n:
            continue                    # over-count explained by owner signatures -> adjudicated
        out.append(_rec(
            "count_anomaly", sev, conf, room, sorted(_name(p) for p in group),
            f"{total} '{kind}' in {room} (expected at most {max_n})",
            f"more {kind}s than a {room} plausibly holds -- one may be a mis-identified piece, a "
            f"duplicate, or a drawn blob mis-clustered as a {kind}",
            f"re-identify the extra {kind}(s) on the sheet, or owner-sign the kinds if the count "
            f"is truly intended (an owner-signed count is suppressed)"))
    return out


# ---- public API ------------------------------------------------------------------------------
def check_room(spec, priors=None, params=None):
    """Flag prior-violating reads in one room spec (schema interior-ai/room-spec@0.2).  Pure:
    (loaded dicts) -> sorted list[record].  `priors` = a loaded kind_priors artifact or None;
    `params` may carry {'confirmed': <ledger confirmed[]>} for two-layer suppression + optional
    'bounds'/'count_max' overrides.  Never writes, never re-labels -- advisory REVIEW only."""
    params = params or {}
    confirmed = params.get("confirmed") or []
    records = []
    for room, pieces in _containers(spec):
        for p in pieces:
            if _is_kind_signed(p, confirmed):
                continue               # two-layer law: owner-signed identity -> adjudicated
            kind = PG._norm_kind(p.get("kind"))
            if kind is None:
                continue               # ABSTAIN: unlabelled piece has no prior to violate
            dims = _dims(p)
            if dims is None:
                continue               # ABSTAIN: unmeasurable
            lo, hi, aspect = dims
            r = _check_size(room, p, kind, lo, hi, priors)
            if r is not None:
                records.append(r)
            r = _check_aspect(room, p, kind, lo, hi, aspect, priors)
            if r is not None:
                records.append(r)
        records += _check_counts(room, pieces, confirmed)
    records.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), r["signal"],
                                str(r["room"]), tuple(r["subjects"]), r["detail"]))
    return records


def check_coverage(spec, priors=None, params=None):
    """Honest coverage: what did the module actually look at?  A short flag-list must NEVER read as
    'clean' when it means 'did not look'.  Reports, per lane, READ / UNWIRED / ABSENT, plus which
    kinds had NO built-in bound (skipped, not a pass) and whether corpus priors were wired.

    built-in size/aspect/count = READ when there were eligible measured pieces, else ABSENT.
    prior-band precision      = READ if `priors` supplied, else UNWIRED (gross built-in bounds
                                only, band-precision unwired -- never a silent clean pass)."""
    params = params or {}
    confirmed = params.get("confirmed") or []
    measured = 0
    no_bound = set()
    counted_containers = 0
    for room, pieces in _containers(spec):
        counted_containers += 1
        for p in pieces:
            if _is_kind_signed(p, confirmed):
                continue
            kind = PG._norm_kind(p.get("kind"))
            if kind is None or _dims(p) is None:
                continue
            measured += 1
            if kind not in BUILTIN_BOUNDS:
                no_bound.add(kind)
    builtin_status = "READ" if measured else "ABSENT"
    prior_wired = _prior_band(priors, "__probe__") is not None or (
        isinstance(priors, dict) and isinstance(priors.get("kinds"), dict))
    return {
        "schema": SCHEMA,
        "size_implausible": {"status": builtin_status, "measured_pieces": measured},
        "aspect_implausible": {"status": builtin_status, "measured_pieces": measured},
        "count_anomaly": {"status": "READ" if counted_containers else "ABSENT",
                          "containers": counted_containers},
        "prior_band": {
            "status": "READ" if prior_wired else "UNWIRED",
            "note": ("corpus priors wired -- band-precision READ" if prior_wired else
                     "corpus priors absent -- gross built-in bounds only, band-precision unwired")},
        "no_bound_kinds": sorted(no_bound),
        "no_bound_note": ("these kinds have NO built-in bound (checked-nothing, not a clean pass); "
                          "cabinet/headboard etc. legitimately span extreme ranges"),
    }
