"""rebuild_diff.py -- Tier-1 self-doubt check: "this round I changed my mind about X from
last round -- intentional, or a SILENT REGRESSION?".

THE WOUND THIS CLOSES (docs/strategy.md ~L639-647, v4/DIFF-v4-vs-v3.md row 5): the v4 clean
rebuild re-derived the terrace tub-chair facing straight from geometry and SILENTLY FLIPPED a
facing v3 had read RIGHT (v3 rot 0 = south, toward the glass/garden -> an intermediate rebuild
rot that faced the interior). NOTHING flagged it: placement_gate certifies COMPLETENESS + NO-
FLOATING + ON-INK, but it CANNOT see facing (a cardinal rotation barely moves the axis-aligned
footprint, so IoU stays ~1.00 through a 180 flip). The gate is single-round; this module is the
BETWEEN-ROUNDS instrument -- it diffs the prior reading against the current one and asks, for
every matched piece, "did a SEMANTIC field (identity/facing/zone) change with NO owner signature
covering the new value?". A signed change is intentional (quiet, at most a LOW provenance trace);
an UNSIGNED change is a possible regression (loud). That asymmetry -- signed=quiet, unsigned=loud
-- is the whole instrument.

DESIGN LAWS (STUDIO-OS):
  * TWO-LAYER. Geometry (position/size/which-blob) is machine-solved and a re-snap between rounds
    is EXPECTED -- we NEVER diff position. We diff only OWNER-layer semantics: kind (identity),
    rot/facing, zone (indoor/outdoor/below). We DOUBT + PROPOSE; we never rewrite a piece, never
    re-label, never auto-correct. Advisory/REVIEW records only.
  * OWNER-FREE / PURE. diff_rounds/match_pieces/diff_coverage are pure functions over already-
    loaded dicts (the two round specs + the owner confirmed[] ledger). No disk, no argparse, no
    prompting. Deterministic (sorted outputs, no now()/random).
  * SUPPRESSION. An owner signature on the CURRENT piece that MATCHES the new value
    (placement_gate.confirmed_kind/confirmed_rot/confirmed_zone) ALWAYS wins -> the change is
    adjudicated -> the doubt is SUPPRESSED (emitted only as a LOW provenance note, never a
    regression flag). Exactly the tub-chair case: v4 rot 8/332 are owner-signed, so the facing
    change is EXPLAINED and stays quiet; strip the signature and the SAME change goes loud.
  * CONSERVATIVE. Below rot_abstain_deg (a re-fit nudge) we ABSTAIN. A radially-symmetric piece
    (shape round/circle) has no meaningful facing -> its rot change is never flagged. A malformed
    rot (unparseable) can neither be shown to change NOR suppressed cleanly -> we abstain rather
    than cry wolf. A false positive on the flagship tub-chair case is a hard failure.
  * HONEST COVERAGE. diff_coverage distinguishes READ (two rounds shared a room, diffed) from
    UNWIRED (no prior round, or no shared room.type -- a first build has NOTHING to diff, which is
    NOT a clean pass) from ABSENT (no current round). "0 flags" must never secretly mean "did not
    look" -- there was no prior round to look at.

SEVERITY (mirrors self_audit.py bands):
  CRITICAL  a facing REVERSAL (circular rot delta >= rot_flip_deg) with no covering signature --
            "silently flipped a facing that was RIGHT", the v4 wound; a confident regression backstop.
  HIGH      an IDENTITY (kind) change or a ZONE-class change with no covering signature -- the
            piece is a different THING / a different indoor-outdoor call than last round, unsigned.
  MEDIUM    a smaller facing change (rot_abstain_deg < delta < rot_flip_deg) with no signature.
  LOW       piece added / dropped between rounds (a rebuild legitimately does this, but a silently
            vanished piece must not be lost); AND the provenance trace of a SIGNED semantic change.

PUBLIC API:
  diff_rounds(prior_specs, current_specs, confirmed=None, params=None) -> list[record]
  match_pieces(prior_items, current_items, iou_th=IOU_MATCH) -> [(prior|None, current|None), ...]
  diff_coverage(prior_specs, current_specs) -> {status, shared_rooms, ...}
prior_specs/current_specs = a LIST of room-spec dicts OR a dict keyed by room.type (both accepted).
confirmed = the owner confirmed[] ledger list (placement_gate.load_confirmed output).
"""
import placement_gate as PG

MODULE = "rebuild_diff"
SCHEMA = "interior-ai/rebuild-diff@0.1"

# geometry fallback pairing threshold: when a piece was RENAMED between rounds (name-match fails),
# pair it to the current piece whose renderer-true footprint has the highest IoU, provided >= this.
# 0.5 admits the real renamed tub chairs (v3->v4 IoU 0.93 left / 0.69 right) and the split orchid
# console (0.60) while rejecting the moved-and-rotated BF12-2 cabinet (IoU 0.0 -> honestly dropped/
# added, not a false semantic-change pair).
IOU_MATCH = 0.5
# a rot change below this is a re-fit nudge, not a facing decision -> ABSTAIN (conservative). The
# real signed left chair moved 0->8 (below threshold, silent even unsigned); the right chair 0->28
# clears it. A near-reversal at/above rot_flip_deg is the CRITICAL wound band.
ROT_ABSTAIN_DEG = 20.0
ROT_FLIP_DEG = 135.0

DEFAULTS = dict(iou_match=IOU_MATCH, rot_abstain_deg=ROT_ABSTAIN_DEG, rot_flip_deg=ROT_FLIP_DEG)

_SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
_ROUND_SHAPES = {"round", "circle", "disc", "disk", "oval"}


# ---- record + normalisation ----------------------------------------------------------
def _rec(check, severity, confidence, room, subjects, detail, why, resolve_by):
    subs = sorted({s for s in subjects if s is not None}, key=str)
    return {"signal": f"{MODULE}:{check}", "severity": severity,
            "confidence": round(float(confidence), 2), "room": room,
            "subjects": subs, "detail": detail, "why": why, "resolve_by": resolve_by}


def _iter_specs(specs):
    """Normalise the polymorphic input to [(room_type, spec_dict), ...]. Accepts a LIST of
    room-spec dicts OR a dict keyed by room.type. The spec's own room.type is authoritative;
    a dict key is only a fallback when the spec omits it. Non-dict members are skipped, never a
    crash (the caller may hand-assemble the rounds)."""
    out = []
    if not specs:
        return out
    if isinstance(specs, dict):
        pairs = list(specs.items())
    elif isinstance(specs, (list, tuple)):
        pairs = [(None, v) for v in specs]
    else:
        return out
    for key, spec in pairs:
        if not isinstance(spec, dict):
            continue
        rt = ((spec.get("room") or {}).get("type")) or key
        out.append((rt, spec))
    return out


def _pieces(spec):
    """Every diffable piece in a room-spec: builtins + loose items + subroom fixtures. All three
    layers carry name/kind/x/y/w/d and can be renamed/re-kinded between rounds, so all three are
    diffed (a silently dropped built-in is as real a completeness loss as a dropped item)."""
    out = list(spec.get("builtins") or [])
    out += list(spec.get("items") or [])
    for sr in spec.get("subrooms") or []:
        out += list(sr.get("fixtures") or [])
    return [p for p in out if isinstance(p, dict)]


def _group(specs):
    """{room_type: [pieces...]} pooled across every spec of that room.type."""
    rooms = {}
    for rt, spec in _iter_specs(specs):
        rooms.setdefault(rt, [])
        rooms[rt].extend(_pieces(spec))
    return rooms


def _footprint(p):
    """Renderer-true AABB via placement_gate.footprint, or None if the piece lacks x/y/w/d
    (then it can only ever be paired by exact name, never by geometry)."""
    try:
        return PG.footprint(p)
    except Exception:
        return None


def _is_round(p):
    return str((p or {}).get("shape", "")).strip().lower() in _ROUND_SHAPES


def _rot_delta(r0, r1):
    """Minimal circular distance (deg, 0..180) between two rotations, absent rot defaulting to 0
    (the renderer's default facing = south). None if EITHER rot is present-but-unparseable -- an
    unreadable orientation must not be coerced into a false 'changed' (conservative)."""
    a = PG._norm_rot(0 if r0 is None else r0)
    b = PG._norm_rot(0 if r1 is None else r1)
    if a is None or b is None:
        return None
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ---- piece matching ------------------------------------------------------------------
def match_pieces(prior_items, current_items, iou_th=IOU_MATCH):
    """Pair pieces across two rounds. Returns [(prior|None, current|None), ...]: a matched pair
    (both non-None), a DROPPED piece (current None), or an ADDED piece (prior None). Two passes:
      1. EXACT NAME -- the generator names pieces deterministically, so an unchanged name is the
         strongest identity link (first available current piece of that name; each consumed once).
      2. GEOMETRY FALLBACK -- for the RENAMED survivors, greedily pair the highest footprint-IoU
         cross-pair >= iou_th, each piece consumed once. This is what re-attaches the tub chairs
         after they were renamed off 'ระเบียง' (name-match dead), so their facing change is still
         diffed instead of read as a drop+add.
    Deterministic: name pass in prior order, geometry pass by (-iou, prior_idx, current_idx)."""
    prior = [p for p in (prior_items or []) if isinstance(p, dict)]
    curr = [c for c in (current_items or []) if isinstance(c, dict)]
    used_p, used_c, pairs = set(), set(), []

    curr_by_name = {}
    for j, c in enumerate(curr):
        curr_by_name.setdefault(c.get("name"), []).append(j)
    for i, p in enumerate(prior):
        nm = p.get("name")
        if nm is None:
            continue
        for j in curr_by_name.get(nm, []):
            if j not in used_c:
                pairs.append((i, j))
                used_p.add(i)
                used_c.add(j)
                break

    cand = []
    for i, p in enumerate(prior):
        if i in used_p:
            continue
        fpp = _footprint(p)
        if fpp is None:
            continue
        for j, c in enumerate(curr):
            if j in used_c:
                continue
            fpc = _footprint(c)
            if fpc is None:
                continue
            v = PG.iou(fpp, fpc)
            if v >= iou_th:
                cand.append((v, i, j))
    cand.sort(key=lambda t: (-t[0], t[1], t[2]))
    for v, i, j in cand:
        if i in used_p or j in used_c:
            continue
        pairs.append((i, j))
        used_p.add(i)
        used_c.add(j)

    result = [(prior[i], curr[j]) for i, j in pairs]
    result += [(prior[i], None) for i in range(len(prior)) if i not in used_p]
    result += [(None, curr[j]) for j in range(len(curr)) if j not in used_c]

    def _key(pair):
        p, c = pair
        ref = c if c is not None else p
        return (str(ref.get("name")), ref.get("x") or 0, ref.get("y") or 0,
                0 if (p is not None and c is not None) else (1 if p is not None else 2))
    result.sort(key=_key)
    return result


# ---- per-pair diff -------------------------------------------------------------------
def _subjects(prior, current):
    return [prior.get("name") if prior else None, current.get("name") if current else None]


def _facing_change(prior, current, room, confirmed, p):
    """rot/facing change record(s) for a matched pair, or []. ABSTAINS on: a radially-symmetric
    piece (rot cosmetic), a sub-threshold nudge, or an unparseable rot. SUPPRESSES (LOW provenance)
    when the CURRENT piece's owner-signed rot equals its built rot; else raises unexplained, CRITICAL
    for a reversal (>= rot_flip_deg) and MEDIUM otherwise."""
    if _is_round(prior) or _is_round(current):
        return []
    d = _rot_delta(prior.get("rot"), current.get("rot"))
    if d is None or d <= p["rot_abstain_deg"]:
        return []
    a = PG._norm_rot(0 if prior.get("rot") is None else prior.get("rot"))
    b = PG._norm_rot(0 if current.get("rot") is None else current.get("rot"))
    subs = _subjects(prior, current)
    name = current.get("name")
    signed = PG.confirmed_rot(current, confirmed)
    if signed is not None and signed == b:
        return [_rec("semantic_change_signed", "LOW", 0.2, room, subs,
                     f"{name}: facing rot {a} -> {b} (delta {d}), owner-signed -> intentional",
                     "the orientation changed between rounds but an owner signature covers the new "
                     "rot -- provenance trace, not a doubt",
                     "none -- adjudicated by the owner's confirmed_rot signature")]
    reversal = d >= p["rot_flip_deg"]
    sev = "CRITICAL" if reversal else "MEDIUM"
    conf = 0.9 if reversal else 0.85
    word = "REVERSED" if reversal else "changed"
    return [_rec("semantic_change_unexplained", sev, conf, room, subs,
                 f"{name}: facing {word} rot {a} -> {b} (delta {d} deg) between rounds, UNSIGNED",
                 "the rebuild re-derived this piece's facing from geometry and " +
                 ("reversed a direction the prior round had" if reversal else
                  "swung it well off the prior round") +
                 " with NO owner signature covering the new orientation -- the placement gate "
                 "cannot see facing, so this is exactly the class of silent regression that slips",
                 "confirm the correct facing on the sheet and sign it (confirmed_rot); if the prior "
                 "round was right, restore that rot")]


def _kind_change(prior, current, room, confirmed):
    """identity (kind) change record, or []. Suppress -> LOW provenance when the current piece's
    signed kind equals its built kind; else HIGH unexplained."""
    pk, ck = PG._norm_kind(prior.get("kind")), PG._norm_kind(current.get("kind"))
    if pk == ck or (pk is None and ck is None):
        return []
    subs = _subjects(prior, current)
    name = current.get("name")
    signed = PG.confirmed_kind(current, confirmed)
    if signed is not None and signed == ck:
        return [_rec("semantic_change_signed", "LOW", 0.2, room, subs,
                     f"{name}: kind {pk!r} -> {ck!r}, owner-signed -> intentional",
                     "identity changed between rounds but an owner signature covers the new kind "
                     "-- provenance trace, not a doubt",
                     "none -- adjudicated by the owner's confirmed_kind signature")]
    return [_rec("semantic_change_unexplained", "HIGH", 0.9, room, subs,
                 f"{name}: identity changed kind {pk!r} -> {ck!r} between rounds, UNSIGNED",
                 "the rebuild re-labelled what this piece IS with no owner signature covering the "
                 "new kind -- identity is owner-layer truth, so a machine re-identification between "
                 "rounds is a possible silent regression",
                 "confirm the piece's identity on the sheet and sign it (confirmed_kind); if the "
                 "prior round was right, restore that kind")]


def _zone_change(prior, current, room, confirmed):
    """indoor/outdoor/below-grade zone-class change record, or []. Suppress -> LOW provenance when
    the current piece's signed zone equals its built zone; else HIGH unexplained."""
    pz, cz = PG._norm_zone(prior.get("zone")), PG._norm_zone(current.get("zone"))
    if pz == cz or (pz is None and cz is None):
        return []
    subs = _subjects(prior, current)
    name = current.get("name")
    signed = PG.confirmed_zone(current, confirmed)
    if signed is not None and signed == cz:
        return [_rec("semantic_change_signed", "LOW", 0.2, room, subs,
                     f"{name}: zone {pz!r} -> {cz!r}, owner-signed -> intentional",
                     "the indoor/outdoor call changed between rounds but an owner signature covers "
                     "the new zone -- provenance trace, not a doubt",
                     "none -- adjudicated by the owner's confirmed_zone signature")]
    return [_rec("semantic_change_unexplained", "HIGH", 0.9, room, subs,
                 f"{name}: zone changed {pz!r} -> {cz!r} between rounds, UNSIGNED",
                 "the rebuild changed this piece's indoor-vs-outdoor-vs-below-grade class with no "
                 "owner signature -- zone is the hardest owner-layer semantic (the F3 terrace/lounge "
                 "wound), so an unsigned change between rounds is a possible silent regression",
                 "confirm the zone on the sheet and sign it (confirmed_zone); if the prior round "
                 "was right, restore that zone")]


def _diff_pair(prior, current, room, confirmed, p):
    if prior is None:
        name = current.get("name")
        return [_rec("piece_added", "LOW", 0.5, room, [name],
                     f"{name}: NEW piece this round (absent last round)",
                     "a piece appeared in the rebuild the prior round did not have -- usually "
                     "intentional, but a silently-added piece should still be seen",
                     "confirm the piece belongs in this room; if spurious, remove it")]
    if current is None:
        name = prior.get("name")
        return [_rec("piece_dropped", "LOW", 0.6, room, [name],
                     f"{name}: present last round, GONE this round",
                     "a piece the prior round had vanished in the rebuild -- a rebuild legitimately "
                     "drops pieces, but a silently-lost one must not go unnoticed",
                     "confirm the removal was intentional; if not, restore the piece")]
    recs = []
    recs += _kind_change(prior, current, room, confirmed)
    recs += _facing_change(prior, current, room, confirmed, p)
    recs += _zone_change(prior, current, room, confirmed)
    return recs


# ---- public entrypoints --------------------------------------------------------------
def diff_rounds(prior_specs, current_specs, confirmed=None, params=None):
    """Diff two reading rounds and return doubt records for every UNSIGNED semantic change (plus
    LOW provenance traces of signed changes and added/dropped pieces). Rooms are matched by
    room.type; only SHARED rooms are piece-diffed (a whole-room delta is a coverage fact, not a
    per-piece flood -- see diff_coverage). Deterministic, owner-free, pure."""
    p = dict(DEFAULTS)
    if params:
        p.update(params)
    prior_rooms = _group(prior_specs)
    curr_rooms = _group(current_specs)
    recs = []
    for rt in sorted(set(prior_rooms) & set(curr_rooms), key=lambda x: str(x)):
        for pr, cu in match_pieces(prior_rooms[rt], curr_rooms[rt], p["iou_match"]):
            recs += _diff_pair(pr, cu, rt, confirmed, p)
    recs.sort(key=lambda r: (_SEV_ORDER[r["severity"]], r["signal"], str(r["room"]),
                             tuple(r["subjects"])))
    return recs


def diff_coverage(prior_specs, current_specs):
    """Honest coverage for the diff lane. READ = the two rounds shared >=1 room.type, diffed.
    UNWIRED = no prior round (a FIRST build has nothing to diff -- silence is NOT a clean pass) OR
    the rounds share no room.type. ABSENT = no current round at all. So a caller can never mistake
    '0 diff flags' for 'no regression' when the truth is 'there was nothing to diff against'."""
    prior_rooms = _group(prior_specs)
    curr_rooms = _group(current_specs)
    shared = sorted(set(prior_rooms) & set(curr_rooms), key=lambda x: str(x))
    if not curr_rooms:
        status, note = "ABSENT", "no current round supplied -- nothing to diff"
    elif not prior_rooms:
        status, note = "UNWIRED", ("no prior round supplied -- a first build has nothing to diff "
                                   "against (not a clean pass)")
    elif not shared:
        status, note = "UNWIRED", ("prior and current share no room.type -- nothing comparable "
                                   "(not a clean pass)")
    else:
        status, note = "READ", f"diffed {len(shared)} shared room(s)"
    return {"status": status, "shared_rooms": [str(r) for r in shared],
            "prior_rooms": sorted(str(r) for r in prior_rooms),
            "current_rooms": sorted(str(r) for r in curr_rooms),
            "prior_only": sorted(str(r) for r in (set(prior_rooms) - set(curr_rooms))),
            "current_only": sorted(str(r) for r in (set(curr_rooms) - set(prior_rooms))),
            "note": note}
