"""
confidence.py -- the ROOT fix for "ship a WRONG answer CONFIDENTLY".

Today confidence is scattered and dishonest about SILENCE. facing_flags emits a flat
1.0 (geometric); zone_flag proposals emit STRONG/MEDIUM/LOW; but a KIND read carries NO
confidence at all, and -- the real wound -- a DEFAULTED semantic read ships SILENTLY as
if certain: a facing-kind piece with `rot` omitted is ASSUMED south (rot 0); a piece with
no `zone` is ASSUMED indoor; a hand-typed kind with nothing corroborating is trusted whole.
None of those assumptions is visible, so the machine says a wrong answer with a straight face.

This module gives every SEMANTIC read (kind / facing / zone) of every piece ONE calibrated
confidence on a shared scale, and a THRESHOLD (SAY_UNSURE_THRESHOLD) below which the machine
must SAY "not sure" instead of shipping the assumption silently. It is the base-read calibrator
that cross_signal / rebuild_diff / anomaly all reuse -- they hunt contradictions/regressions;
this one makes the quiet ASSUMPTIONS audible.

TWO-LAYER LAW (why this is advisory, never a write). Geometry is machine-solved; the SEMANTIC
call (identity/kind, facing, indoor-vs-outdoor zone) is OWNER-signed. This module may DOUBT a
read and PROPOSE the owner verify it; it NEVER writes a value, re-labels a kind, or auto-fixes.
An owner signature (placement_gate.confirmed_kind / confirmed_rot / confirmed_zone) ALWAYS wins
-> confidence 1.0 -> the doubt is SUPPRESSED (adjudicated). REVIEW-only, never FAIL.

CALIBRATION SCALE (documented, defensible; the ONE scale field_confidence returns):
  1.00  OWNER-SIGNED     a confirmed_* signature governs this field -> certain by decree.
  0.70  CORROBORATED     an INDEPENDENT machine read agrees: a facing_reader backrest-strip
                         read (context facing_agrees), a piece geometrically CONTAINED in the
                         room outline (zone -> indoor), or a kind matching a UNIQUE prior band
                         (context prior_kind).
  0.55  PROVENANCE       a hand-read carrying a trail: an explicit `rot` on a facing piece, a
                         `facing_source`, a note asserting the facing, a `bf` schedule code
                         (owner-authoritative built-in identity), or an explicit hand-set zone.
                         A deliberate human read -- above the say-unsure line, but not certain.
  0.30  ASSUMED/DEFAULT  the WOUND: NO evidence. rot omitted -> assumed south; zone absent and
                         containment unverifiable -> assumed indoor; kind hand-typed with nothing
                         corroborating. Below threshold -> the machine must SAY it is unsure.

CONSERVATISM (law 4, modelled on placement_gate.facing_flags). We ABSTAIN, never cry wolf:
facing is assessed ONLY for facing-kinds (a round table has no facing); a piece geometrically
contained in the room reads indoor at 0.70 (a nightstand near an exterior wall is NOT flagged
just for being near an edge -- only a piece whose centroid falls OUTSIDE the outline, with no
sign, is a genuine zone doubt); and an owner signature always suppresses. The flagship real case
(v4 sitting room): the tub chairs' facing is owner-signed -> 1.0 -> NO say-unsure record; the
sofa's explicit rot 90 + "faces EAST" note -> 0.55 (provenance) -> above threshold, silent-OK;
a rot-less unsigned chair -> 0.30 -> a record fires ("assumed south-facing, unverified").

HONEST COVERAGE (law 3). assess_coverage never lets "0 records" mean "did not look": it reports,
per field, how many reads were owner-signed vs corroborated vs provenance vs ASSUMED, so a caller
sees the calibration STATE. A room with pieces -> READ; a room with none -> ABSENT (distinct).

PURE / stdlib top level. Imports: math, placement_gate, zone_flag (their tops are stdlib-only;
fitz/bpy/numpy stay lazy inside them). No disk I/O, no argparse, deterministic, sorted output.
"""
import math

import placement_gate as PG
import zone_flag as ZF

SCHEMA = "interior-ai/confidence@0.1"

# ---- the shared calibration scale (documented above) ---------------------------------
CONF_OWNER = 1.0
CONF_CORROBORATED = 0.70
CONF_PROVENANCE = 0.55
CONF_ASSUMED = 0.30

# The line below which a read must SAY "not sure" instead of shipping silently. Set at 0.50 so
# a PROVENANCE read (0.55, a deliberate hand-read with a trail) is above the line -- silent-OK --
# while a corroborated/owner read is comfortably clear and a bare ASSUMPTION (0.30) is below.
# The sofa boundary (0.55 vs 0.50) is pinned by test_boundary_provenance_is_above_threshold.
SAY_UNSURE_THRESHOLD = 0.50

# facing is only MEANINGFUL for directional pieces -- mirror placement_gate._FACING_KINDS so a
# round side table is never flagged for a facing it does not have (conservatism).
FACING_KINDS = set(PG._FACING_KINDS)

_FIELDS = ("kind", "facing", "zone")

DEFAULTS = dict(
    indoor_pad=ZF.DEFAULTS["indoor_pad"],           # mm; centroid within this of the outline reads contained
    indoor_area_frac=ZF.DEFAULTS["indoor_area_frac"],  # >= this footprint fraction inside -> contained
    facade_proximity_mm=1200.0,                     # centroid within this of the south (min-y) edge = "near facade"
    #                                                 (severity lever only: bumps a FIRED facing/zone doubt to MEDIUM)
)

# note keywords that count as a hand ASSERTION of facing / zone (weak provenance, not certainty)
_FACING_WORDS = ("face", "faces", "facing", "หัน")
_ZONE_WORDS = ("indoor", "outdoor", "below grade", "below-grade", "below_grade",
               "terrace", "ระเบียง", "lounge", "ground below")
# a NEGATED note ("does NOT face the terrace", "ไม่ได้หัน...") states what the piece is NOT -- it
# does not tell us which way it DOES face / where it IS, so it is not clean provenance. Dropping
# its credit lets the read fall through to ASSUMED and the doubt FIRES: the safe (more-doubt)
# direction for a say-unsure instrument -- silence must never be bought with a negation.
_NEGATIONS = ("ไม่", "not ", "n't", "never", "no ")


def _s(v):
    return v.lower() if isinstance(v, str) else ""


def _note_asserts(piece, words):
    n = _s(piece.get("note"))
    if any(neg in n for neg in _NEGATIONS):
        return False
    return any(w in n for w in words)


# ---- the ONE shared calibration -----------------------------------------------------
def field_confidence(piece, field, confirmed=None, context=None):
    """Calibrated confidence (0..1) + a basis string for ONE semantic field of ONE piece.

    field in {"kind","facing","zone"}. Resolution is highest-evidence-first, so a stronger
    signal never gets masked by a weaker one:
        owner-signed (1.0) > corroborated (0.70) > provenance (0.55) > assumed/default (0.30).

    context (optional dict, all keys optional) carries the CORROBORATION a caller has already
    computed so this stays pure:
        prior_kind        : a kind_priors unique-band suggestion (kind corroboration)
        facing_agrees     : True if a facing_reader strip-read agrees with the typed rot
        zone_corroborated : True if the piece is geometrically contained in the room outline
    assess_room fills context per piece; other callers (cross_signal, ...) share this one scale.
    Pure: no disk, no mutation of piece/context; a missing context degrades to provenance/assumed
    (never crashes) so field_confidence is callable standalone."""
    ctx = context or {}
    if field == "kind":
        return _kind_confidence(piece, confirmed, ctx)
    if field == "facing":
        return _facing_confidence(piece, confirmed, ctx)
    if field == "zone":
        return _zone_confidence(piece, confirmed, ctx)
    raise ValueError(f"unknown field: {field!r}")


def _kind_confidence(piece, confirmed, ctx):
    if PG.confirmed_kind(piece, confirmed) is not None:
        return CONF_OWNER, "owner-signed"
    prior = ctx.get("prior_kind")
    if prior is not None and _s(prior) == _s(piece.get("kind")) and _s(prior):
        return CONF_CORROBORATED, "matches a unique kind-priors band"
    if piece.get("bf"):                       # owner-authoritative built-in schedule code = identity provenance
        return CONF_PROVENANCE, f"bf schedule code {piece.get('bf')}"
    return CONF_ASSUMED, "hand-typed identity, no owner sign + no prior-band corroboration"


def _facing_confidence(piece, confirmed, ctx):
    if PG.confirmed_rot(piece, confirmed) is not None:
        return CONF_OWNER, "owner-signed"
    if ctx.get("facing_agrees") is True:
        return CONF_CORROBORATED, "facing_reader backrest-strip read agrees"
    if piece.get("facing_source"):
        return CONF_PROVENANCE, f"facing_source={piece.get('facing_source')}"
    if "rot" in piece and piece.get("rot") is not None:
        return CONF_PROVENANCE, "explicit rot authored"
    if _note_asserts(piece, _FACING_WORDS):
        return CONF_PROVENANCE, "note asserts a facing"
    return CONF_ASSUMED, "rot omitted -> assumed south-facing, unverified"


def _zone_confidence(piece, confirmed, ctx):
    if PG.confirmed_zone(piece, confirmed) is not None:
        return CONF_OWNER, "owner-signed"
    if ctx.get("zone_corroborated") is True:
        return CONF_CORROBORATED, "contained in room outline -> indoor"
    if PG._norm_zone(piece.get("zone")) is not None:
        return CONF_PROVENANCE, f"hand-set zone={PG._norm_zone(piece.get('zone'))}"
    if _note_asserts(piece, _ZONE_WORDS):
        return CONF_PROVENANCE, "note asserts a zone"
    return CONF_ASSUMED, "zone absent + containment unverified -> assumed indoor"


# ---- geometry helpers (containment / facade proximity) used to build per-piece context ---
def _piece_geo(piece, outline, params):
    """(contained, near_facade) for a piece against the room outline. contained = centroid inside
    the polygon OR within indoor_pad of it OR >= indoor_area_frac of the footprint inside (the same
    indoor-immunity test zone_flag uses). near_facade = centroid within facade_proximity_mm of the
    south (min-y) edge -- a SEVERITY lever only, never a gate. Pure; never raises on an odd outline."""
    try:
        fp = PG.footprint(piece)
    except Exception:
        return False, False
    cx = (fp[0] + fp[2]) / 2.0
    cy = (fp[1] + fp[3]) / 2.0
    if not outline or len(outline) < 3:
        return False, False
    contained = ZF.point_in_poly((cx, cy), outline)
    if not contained:
        try:
            if ZF.dist_point_to_poly((cx, cy), outline) <= params["indoor_pad"]:
                contained = True
        except Exception:
            pass
    if not contained:
        try:
            if ZF.rect_area_frac_inside(fp, outline) >= params["indoor_area_frac"]:
                contained = True
        except Exception:
            pass
    try:
        y_s = ZF.facade_datum(outline)[0]
        near_facade = 0.0 <= (cy - y_s) <= params["facade_proximity_mm"] or cy < y_s
    except Exception:
        near_facade = False
    return contained, near_facade


def _all_pieces(spec):
    """Every semantic piece in the room, tagged (piece, subroom_or_None). builtins + loose items +
    each subroom's fixtures. Deterministic order (as authored)."""
    out = []
    for it in spec.get("builtins", []) or []:
        out.append((it, None))
    for it in spec.get("items", []) or []:
        out.append((it, None))
    for sr in spec.get("subrooms", []) or []:
        for it in sr.get("fixtures", []) or []:
            out.append((it, sr.get("name") or sr.get("type")))
    return out


def _eligible_fields(piece):
    """Which semantic fields are MEANINGFUL for this piece (honest coverage: facing on a table is
    not 'clean', it is N/A). kind + zone always apply; facing only for directional kinds."""
    fields = ["kind", "zone"]
    if piece.get("kind") in FACING_KINDS:
        fields.append("facing")
    return fields


def _tier(score):
    if score >= CONF_OWNER:
        return "owner_signed"
    if score >= CONF_CORROBORATED:
        return "corroborated"
    if score >= CONF_PROVENANCE:
        return "provenance"
    return "assumed"


def _severity(field, near_facade):
    """Severity for a FIRED say-unsure record (score below threshold). A fully-unsupported KIND is
    MEDIUM (identity is the owner's to arbitrate); a defaulted FACING/ZONE is MEDIUM when the piece
    sits near the facade -- the exact indoor/outdoor/below call the owner arbitrates (the F3 wound) --
    else LOW advisory."""
    if field == "kind":
        return "MEDIUM"
    return "MEDIUM" if near_facade else "LOW"


def _detail(field, piece, basis, subroom):
    name = piece.get("name", piece.get("kind", "?"))
    where = f" [{subroom}]" if subroom else ""
    if field == "kind":
        val = piece.get("kind")
        return f"kind='{val}' on '{name}'{where} shipped as certain, but {basis}"
    if field == "facing":
        rot = piece.get("rot", "0 (omitted)")
        return f"facing of '{name}'{where} (rot {rot}) shipped as certain, but {basis}"
    val = PG._norm_zone(piece.get("zone")) or "indoor (default)"
    return f"zone='{val}' on '{name}'{where} shipped as certain, but {basis}"


_WHY = {
    "kind": "identity is owner-only semantic truth and there is NO machine identity read; a "
            "hand-typed kind with no owner signature and no unique prior-band match is an "
            "unverified guess dressed as certainty",
    "facing": "which way a piece faces barely changes its axis-aligned footprint, so a wrong "
              "facing passes every geometric gate; with rot omitted the read DEFAULTS to south "
              "and ships silently -- the assumption is invisible",
    "zone": "indoor-vs-outdoor-vs-below is the two-layer law's hardest semantic; a piece whose "
            "containment cannot be corroborated defaults to 'indoor' and ships silently -- the "
            "exact F3 terrace/lounge wound",
}
_RESOLVE = {
    "kind": "confirm the piece identity on the sheet and sign confirmed_kind (or bind a "
            "kind-priors band); silence is not verification",
    "facing": "confirm the facing on the sheet and sign confirmed_rot/confirmed_facing (an "
              "explicit rot alone is a hand-read, not a verified one)",
    "zone": "confirm indoor / outdoor_same_floor / below_grade and sign confirmed_zone; do not "
            "let the indoor default stand unverified",
}


def _record(field, severity, score, room, piece, basis, subroom):
    return {
        "signal": f"confidence:{field}",
        "severity": severity,
        "confidence": round(1.0 - score, 2),      # how sure THIS is an under-verified read
        "room": room,
        "subjects": [piece.get("name", piece.get("kind", "?"))],
        "detail": _detail(field, piece, basis, subroom),
        "why": _WHY[field],
        "resolve_by": _RESOLVE[field],
    }


def _piece_context(piece, outline, params, context):
    """Merge caller-supplied per-piece context (context[piece_name]) with the geometry we derive."""
    contained, near_facade = _piece_geo(piece, outline, params)
    ctx = {"zone_corroborated": contained, "near_facade": near_facade}
    ext = (context or {}).get(piece.get("name"))
    if isinstance(ext, dict):
        ctx.update(ext)                            # a caller may inject prior_kind / facing_agrees
    return ctx, near_facade


def assess_room(spec, confirmed=None, context=None, params=None):
    """For every eligible semantic field of every piece, compute field_confidence and emit ONE
    say-unsure record for each field BELOW SAY_UNSURE_THRESHOLD that was nonetheless shipped as if
    certain. record['confidence'] = 1 - field_confidence (how sure we are it is under-verified).

    ADVISORY / REVIEW only (two-layer law): an owner signature yields 1.0 and is SUPPRESSED (never
    emitted). Conservative: facing only for directional kinds; a geometrically-contained piece reads
    indoor (0.70) and is not flagged just for sitting near an edge. Deterministic: records sorted by
    (severity band, field, name). confirmed = placement_gate.load_confirmed(review) (owner ledger).
    context (optional) = {piece_name: {prior_kind?, facing_agrees?}} extra corroboration per piece."""
    params = {**DEFAULTS, **(params or {})}
    room = (spec.get("room") or {}).get("type")
    outline = (spec.get("room") or {}).get("outline_mm") or []
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    records = []
    for piece, subroom in _all_pieces(spec):
        ctx, near_facade = _piece_context(piece, outline, params, context)
        for field in _eligible_fields(piece):
            score, basis = field_confidence(piece, field, confirmed, ctx)
            if score < SAY_UNSURE_THRESHOLD:
                sev = _severity(field, near_facade)
                records.append(_record(field, sev, score, room, piece, basis, subroom))
    records.sort(key=lambda r: (sev_order[r["severity"]], r["signal"],
                                str(r["subjects"][0] if r["subjects"] else "")))
    return records


def assess_coverage(spec, confirmed=None, context=None, params=None):
    """HONEST COVERAGE: never let '0 records' read as a clean pass. Reports, per field and overall,
    how many reads were owner_signed / corroborated / provenance / assumed(below-threshold-flagged),
    plus the eligible-field count -- so self_audit shows the CALIBRATION STATE beside the doubt list.

    status READ (a room with pieces was assessed) vs ABSENT (no pieces -> nothing to look at). Uses
    the SAME per-piece context as assess_room, so the tallies and the emitted records always agree."""
    params = {**DEFAULTS, **(params or {})}
    outline = (spec.get("room") or {}).get("outline_mm") or []
    by_field = {f: {"owner_signed": 0, "corroborated": 0, "provenance": 0, "assumed": 0,
                    "eligible": 0} for f in _FIELDS}
    n_pieces = 0
    for piece, _subroom in _all_pieces(spec):
        n_pieces += 1
        ctx, _nf = _piece_context(piece, outline, params, context)
        for field in _eligible_fields(piece):
            score, _basis = field_confidence(piece, field, confirmed, ctx)
            b = by_field[field]
            b["eligible"] += 1
            b[_tier(score)] += 1
    assessed = sum(b["eligible"] for b in by_field.values())
    flagged = sum(b["assumed"] for b in by_field.values())
    signed = sum(b["owner_signed"] for b in by_field.values())
    status = "READ" if n_pieces > 0 else "ABSENT"
    return {"status": status, "pieces": n_pieces, "assessed_fields": assessed,
            "owner_signed": signed, "flagged_unsure": flagged, "by_field": by_field,
            "threshold": SAY_UNSURE_THRESHOLD}
