"""
self_audit.py -- the owner-free DOUBT aggregator: gather every scattered "I am not
sure" signal the reader pipeline already emits, per project, into ONE ranked list of
"points where the machine doubts itself" -- with NO owner in the loop.

    python pipeline/scripts/self_audit.py <project_dir> [--gate PATH] [--out DIR] [--json]

WHY (backlog Tier-0, the new north star: make the machine 'doubt itself at the RIGHT
points', not merely 'read better'): the pipeline scatters its uncertainty across a dozen
artifacts -- placement-gate REVIEW counts, facing/zone flags, facade & glazing candidates,
the sourceability gap, persona GAP/ORPHAN coverage, merged blobs, calibration fails. No
one place answers "where, ranked, is this project least certain?". Without that instrument
the loop cannot tell whether a change made the machine doubt itself BETTER. This module is
that instrument for a LIVE project (no ground truth): it ranks OPEN doubt and, crucially,
reports its OWN coverage so a short list never silently means "clean" when it means
"did not look". Its sibling benchmark_reader.py measures whether those doubt-flags land on
the genuinely-wrong items (flag-recall/precision) on the GT corpus -- the two are the
same instrument split by "have ground truth?" (no here, yes there).

DESIGN LAWS
  * Owner-free. Reads only PERSISTED, post-adjudication state (the gate marker already
    subtracted owner-signed dismissals/confirmations) plus re-derives the stateless
    candidate files and the in-process gates. It never prompts and never edits a ledger.
  * FAIL != doubt. A REVIEW ("I am unsure") is the harvest. A FAIL ("I am confident this
    is WRONG": a floating piece, a failed calibration, a regressed owner signature) is
    surfaced too, but as its own CRITICAL band -- ranked above doubt, never conflated.
  * Honest coverage. Every source family reports READ / ABSENT / UNWIRED / ERROR. A
    signal that persists nothing (sourceability, persona, per-piece facing detail) is
    re-derived in-process where possible and marked UNWIRED (never a silent pass) where
    not. The project doubt-score is only as trustworthy as the coverage line beside it.
  * Pure-logic core. The collect_* functions take already-loaded dicts and return plain
    records, so the ranking is unit-testable with zero disk. Disk/CLI is a thin shell.

SEVERITY -> rank weight (score = weight x count; the list sorts by score desc):
  CRITICAL 1000  regression / build-blocker: a contradicted owner signature (kind/zone),
                 a failed calibration, a floating piece, a detached (orphaned) signature.
  HIGH      100  strong open doubt: an unplaced drawn cluster, a merged blob (a real piece
                 may hide fused in linework -- the 'I don't know what I'm missing' doubt),
                 a double-claim identity flag.
  MEDIUM     10  softer open doubt: an ambiguous facing, an open below-grade zone proposal,
                 a strong glazed-facade candidate, a sourceability REVIEW, a geo-orphan sign.
  LOW         1  advisory: a long-thin dropped comp, the raw glazing-candidate pile
                 (summarised, never enumerated), persona GAP/ORPHAN, weaker facade cands.
"""
import glob
import json
import os
import re
import sys

SEVERITY_WEIGHT = {"CRITICAL": 1000, "HIGH": 100, "MEDIUM": 10, "LOW": 1}
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _rec(source, kind, scope, severity, count, detail, why, resolve_by,
         room=None, resolved=False, source_file=None, magnitude=None):
    """count = DOUBT MULTIPLICITY (how many independent things to look at: 2 merged blobs
    = 2). magnitude = raw underlying number for display only, defaults to count; it differs
    only for a summarised pile (the glazing review-artifact is ONE advisory, count=1, but
    magnitude=294). score = weight x count is an informational per-record magnitude; RANKING
    is band-first (see rank()) so a high-count LOW can never bury a low-count MEDIUM."""
    count = int(count)
    return {"source": source, "kind": kind, "scope": scope, "room": room,
            "severity": severity, "count": count,
            "magnitude": int(count if magnitude is None else magnitude),
            "score": SEVERITY_WEIGHT[severity] * max(count, 1),
            "resolved": bool(resolved), "detail": detail, "why": why,
            "resolve_by": resolve_by, "source_file": source_file}


# ---- collectors: pure (loaded dict -> list[record]), no disk --------------------------
def collect_gate(gate, source_file=None):
    """placement-gate.json is the doubt HUB: it already carries, per room and
    post-owner-adjudication, the counts for facing/zone/merged/identity/unplaced +
    calibration + signature/zone reconcile. Every count here is OPEN doubt (dismissed
    ones were already subtracted -> we never emit `dismissed`). Missing keys (older
    marker schema) read as 0, so a v3 marker degrades cleanly instead of KeyError-ing."""
    out = []
    sf = source_file

    # --- target-scope (whole-marker) signals -------------------------------------------
    for chk in (gate.get("calibration_fails") or []):
        out.append(_rec("calibration", "calibration_fail", "project", "CRITICAL", 1,
                        f"wall-grid calibration FAILED: {chk}",
                        "the extracted walls do not register at a written grid dim -- the "
                        "whole coordinate frame (scale/origin) may be wrong, so every "
                        "downstream mm is suspect",
                        "re-extract walls with the correct scale/origin triple, or fix the "
                        "manifest calibration_checks; a positive fail is reliable",
                        source_file=sf))
    sig = gate.get("signature_reconcile") or {}
    for name in (sig.get("orphaned_names") or []):
        out.append(_rec("signature", "orphaned_signature", "project", "CRITICAL", 1,
                        f"owner-signed piece '{name}' binds nothing this extraction",
                        "a facing/kind signature the owner personally made no longer "
                        "matches any built piece by name+size -- either the piece was "
                        "renamed/resized or the read regressed; the sign is stranded",
                        "re-bind or re-sign the piece, or remove the stale signature entry",
                        source_file=sf))
    zr = gate.get("zone_reconcile") or {}
    for name in (zr.get("name_orphans") or []):
        out.append(_rec("signature", "orphaned_signature", "project", "CRITICAL", 1,
                        f"owner zone-signature '{name}' binds no piece",
                        "a name-scoped zone signature matches no built piece -- a stranded "
                        "owner decision (hard regression, not soft doubt)",
                        "re-bind or re-sign the zoned piece, or remove the stale entry",
                        source_file=sf))
    if (zr.get("geo_orphans") or 0) > 0:
        out.append(_rec("signature", "geo_orphan_zone", "project", "MEDIUM",
                        zr["geo_orphans"],
                        f"{zr['geo_orphans']} owner below-grade annotation(s) bind no drawn "
                        "cluster this extraction",
                        "a geometry-scoped zone sign found no blob to attach to -- the "
                        "cluster it referenced may have moved or dissolved",
                        "re-run the gate against the current sheet; if it persists, re-place "
                        "the annotation on the drawn cluster", source_file=sf))

    # --- per-room signals --------------------------------------------------------------
    for r in (gate.get("rooms") or []):
        room = r.get("room")
        rf = r.get("floating") or []
        if rf:
            out.append(_rec("placement_gate", "floating", "room", "CRITICAL", len(rf),
                            f"{len(rf)} piece(s) float on empty floor in {room}: {rf}",
                            "a placed piece covers no drawn ink -- the build is confidently "
                            "WRONG here (FAIL), not merely unsure",
                            "move/remove the piece so it lands on real drawn furniture, or "
                            "dismiss the region if it is non-furniture linework",
                            room=room, source_file=sf))
        for key, kind, sev, why, fix in (
            ("kind_flags", "kind_regression", "CRITICAL",
             "the built kind contradicts an owner-signed kind -- a rebuild regressed a "
             "decision the owner personally made",
             "re-read the piece kind or re-sign it; a contradiction is confidence 1.0"),
            ("zone_flags", "zone_regression", "CRITICAL",
             "the built/proposed zone contradicts an owner-signed zone (regression backstop)",
             "re-read the zone or re-sign it"),
            ("unplaced", "unplaced", "HIGH",
             "a drawn cluster no placed piece covers -- either missing furniture we failed "
             "to place, or a mis-clustered label/dimension blob",
             "place the missing piece, or dismiss the blob as non-furniture in "
             "placement-review.json"),
            ("merged_regions", "merged_blob", "HIGH",
             "the clusterer fused 2+ pieces into one room-spanning blob it could not split "
             "-- a real piece may be HIDDEN inside it (a completeness blind spot: we do not "
             "know what we are missing)",
             "confirm on the sheet whether furniture hides in the blob; if it is pure "
             "dimension/boundary linework, dismiss it"),
            ("identity_flags", "identity", "HIGH",
             "two placed pieces resolve onto one drawn cluster (double-claim) -- at least "
             "one is misidentified",
             "re-read which piece the cluster is; correct the losing piece's identity"),
            ("facing_flags", "facing", "MEDIUM",
             "a piece's drawn back-strip disagrees with its typed facing (90-deg off, a soft "
             "180-flip, or a contradicted signature) -- which way it faces is uncertain",
             "confirm the facing on the sheet and sign it; note 0 flags != all confirmed "
             "(rot-less pieces read 'unknown' and emit no flag)"),
            ("zone_open", "zone_open", "MEDIUM",
             "an open below-grade / outdoor zone PROPOSAL the machine refuses to auto-decide "
             "-- is this element indoor-this-floor or below grade / outside?",
             "sign the zone on the piece (confirmed_zone) to resolve; STRONG/MEDIUM/LOW "
             "confidence lives in the gate stdout, not the marker"),
            ("zone_exterior_linework", "zone_exterior_linework", "LOW",
             "a candidate that may be exterior linework drawn through the storey",
             "confirm indoor/outdoor and sign it"),
            ("long_thin", "long_thin", "LOW",
             "a narrow dropped component that MIGHT be a slim real piece (a shelf/ledge), "
             "not a dimension tick",
             "confirm on the sheet; if a real piece, add it to the spec"),
        ):
            n = r.get(key) or 0
            if n > 0:
                out.append(_rec("placement_gate", kind, "room", sev, n,
                                f"{n} {kind} flag(s) in {room}", why, fix,
                                room=room, source_file=sf))
    return out


def _facade_signed(cand, review):
    """A facade candidate is RESOLVED only by an owner sign in placement-review.json,
    following the SAME contract as placement_gate.confirmed_facade so the audit never
    re-reports a doubt the gate/generators already treat as answered: a confirmed[] entry
    whose room is this room OR the '*' wildcard, whose `facade` is a real bool (True OR
    False -- either answers the 'is this glass?' question; a null/string is an unsigned or
    typo entry, NOT a resolution), whose `by` is not the OWNER-CONFIRM-PENDING template.
    A per-room sign with no/typo offset resolves the room; a numeric offset must match
    within a wall-thickness tolerance. Never raises on a hand-edited offset (that would
    abort the whole audit). (No project carries a facade sign yet -- wired ahead of use.)"""
    room = cand.get("room")
    for e in (review.get("confirmed") or []) if isinstance(review, dict) else []:
        if e.get("room") not in (room, "*") or not isinstance(e.get("facade"), bool):
            continue
        if str(e.get("by", "")).startswith("OWNER-CONFIRM-PENDING"):
            continue
        ec = e.get("c")
        if ec is None:
            return True                     # room-scoped sign, no offset -> resolves room
        try:
            if abs(float(ec) - float(cand.get("c", 0) or 0)) <= 150.0:
                return True
        except (TypeError, ValueError):
            return True                     # signed but unparseable offset still answers it
    return False


def collect_facade(facade, review=None, source_file=None):
    """facade-candidates.json is a STATELESS per-room re-derivation: one clean south-edge
    glazed-facade candidate per room (0..2), score 4/5. It carries no resolved flag -- the
    sign lives in placement-review.json, so we JOIN by room+offset. Presence of an open
    candidate = 'this MIGHT be a glass facade, but whether it is glass is a semantic call I
    cannot make'. Absence is AMBIGUOUS (walled edge / no evidence / empty scan), never a
    confident 'no facade', so we never emit a 'clean' record here."""
    out = []
    review = review or {}
    for c in (facade.get("candidates") or []):
        resolved = _facade_signed(c, review)
        sev = "MEDIUM" if (c.get("score") or 0) >= 5 else "LOW"
        room = c.get("room")
        out.append(_rec("facade", "facade_candidate", "facade", sev, 1,
                        f"glazed-facade candidate in {room} "
                        f"(score {c.get('score')}, {c.get('tier')}, "
                        f"len {round(c.get('length_mm', 0))}mm)",
                        "a strong thin-line run along the room's south edge looks like a "
                        "glazed facade / window wall, but glass-vs-wall is an owner call",
                        "set facade true|false in confirm_facade_stub, sign `by`, and merge "
                        "into placement-review.json confirmed[]",
                        room=room, resolved=resolved, source_file=source_file))
    return out


def collect_glazing(glazing, source_file=None):
    """glazing-candidates.json is the GLOBAL, noisy pass (hundreds of thin-line runs, no
    room binding) that facade_reader distills into the per-room handful above. We must NOT
    flood the doubt list with it -- it is summarised into ONE advisory record: how many
    unresolved runs remain (confirms_manual_patch == False), how many are 'strong'. A high
    score here is structural evidence strength, NOT probability-of-glass."""
    cands = glazing.get("candidates") or []
    unresolved = [c for c in cands if not c.get("confirms_manual_patch")]
    if not unresolved:
        return []
    strong = sum(1 for c in unresolved if c.get("tier") == "strong")
    # count=1: this is ONE advisory (a pile to skim), NOT len(unresolved) independent
    # doubts -- otherwise a 294-line noise pile would swamp the doubt-score and (pre-fix)
    # out-rank genuine MEDIUM doubts. The raw number lives in magnitude + the detail.
    return [_rec("glazing", "glazing_unresolved", "global", "LOW", 1,
                 f"{len(unresolved)} unresolved global glazing-line candidates "
                 f"({strong} strong) -- the raw pile facade_reader distils per-room",
                 "each is a thin-line run that MIGHT be glass; the pile is a review "
                 "artifact (furniture double-lines can score 'strong'), not per-room truth",
                 "confirm real glass runs and copy their segments into the walls JSON "
                 "manual_additions with a signed `by`; ignore the rest",
                 magnitude=len(unresolved), source_file=source_file)]


def collect_sourceability(specs):
    """sourceability_gate persists nothing -- re-derive it in-process per scene-graph.
    REVIEW = soft doubt (pick unverified, or no ffe_tag binding yet); FAIL = confident-wrong
    (a lying binding); UNWIRED = cannot check (no FF&E file). `specs` = [(path, spec_dict)].
    Import is lazy + guarded so a missing dep degrades to an ERROR-coverage note, never a
    crash of the whole audit."""
    out, status = [], {}
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import sourceability_gate as SG
    except Exception as e:                                    # dep/import failure
        return out, {"status": "ERROR", "note": f"import failed: {e}"}
    n_review = n_fail = n_unwired = 0
    for path, spec in specs:
        try:
            verdict, results = SG.check(path)
        except Exception as e:
            status[path] = f"ERROR: {e}"
            continue
        room = (spec.get("room") or {}).get("type") or os.path.basename(path)
        status[path] = verdict
        for it in results:
            st = it.get("status")
            if st == "FAIL":
                n_fail += 1
                out.append(_rec("sourceability", "sourceability_fail", "element",
                                "CRITICAL", 1,
                                f"{it.get('name')} in {room}: sourcing FAIL "
                                f"({','.join(it.get('failed') or []) or it.get('detail','')})",
                                "a binding points at a product that is wrong-sized / missing "
                                "supplier / resolves to nothing -- render would visualise an "
                                "unbuyable spec",
                                "fix or replace the FF&E pick so it is bound + right-sized + "
                                "supplied", room=room,
                                source_file=os.path.basename(path)))
            elif st == "REVIEW":
                n_review += 1
                out.append(_rec("sourceability", "sourceability_review", "element",
                                "MEDIUM", 1,
                                f"{it.get('name')} in {room}: sourcing REVIEW "
                                f"({','.join(it.get('failed') or []) or 'unverified'})",
                                "the pick is not yet verified-confirmed, or the element is "
                                "not yet bound to a sourceable product (binding pending)",
                                "verify the pick or bind an ffe_tag to a real product",
                                room=room, source_file=os.path.basename(path)))
            elif st == "UNWIRED":
                n_unwired += 1
    n_error = sum(1 for v in status.values()
                  if isinstance(v, str) and v.startswith("ERROR"))
    # honest-coverage precedence: a swallowed per-spec check() failure must NOT read as a
    # clean READ pass (a spec that errored was NOT reviewed) -- surface it as ERROR, and
    # always carry `errored`/reviewed-minus-errored so render_md cannot hide it.
    if not specs:
        st = "ABSENT"
    elif n_error and not out:
        st = "ERROR"                                        # ran, every result errored
    elif not out and n_unwired and not (n_fail or n_review):
        st = "UNWIRED"                                      # ran, but nothing checkable
    else:
        st = "READ"
    cov = {"status": st, "reviewed": len(specs) - n_error, "errored": n_error,
           "fail": n_fail, "review": n_review, "unwired_elements": n_unwired,
           "per_spec": status}
    return out, cov


def collect_persona(specs):
    """persona coverage (GAP/ORPHAN) persists nothing and needs a persona.json + the WHOLE
    home's specs (a single-room call intentionally withholds GAPs). Advisory only (WARN,
    never FAIL). No persona -> UNWIRED (never a silent pass). `specs` = [(path, spec_dict)]."""
    out = []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import persona as P
    except Exception as e:
        return out, {"status": "ERROR", "note": f"import failed: {e}"}
    if not specs:
        return out, {"status": "ABSENT", "note": "no scene-graph specs found"}
    spec_docs = [s for _p, s in specs]
    try:
        persona_obj = P.find_persona_for(spec_docs[0], specs[0][0])
    except Exception:
        persona_obj = None
    if not persona_obj:
        return out, {"status": "UNWIRED", "note": "no persona.json for this project -- "
                     "GAP/ORPHAN coverage cannot be computed (not a pass)"}
    try:
        results, verdict = P.report(spec_docs, persona_obj)
    except Exception as e:
        return out, {"status": "ERROR", "note": f"report failed: {e}"}
    n_gap = n_orphan = 0
    for row in results:
        if row.get("status") != "WARN":
            continue
        check = row.get("check", "")
        detail = row.get("detail", "")
        if check.startswith("persona:gap:"):
            n_gap += 1
            out.append(_rec("persona", "persona_gap", "project", "LOW", 1,
                            f"GAP: {detail}",
                            "the client states an activity but NO element in the home serves "
                            "it -- a coverage hole, advisory",
                            "add an element that serves the activity, or accept the gap",
                            source_file="persona (in-process)"))
        elif check.startswith("persona:orphan:"):
            n_orphan += 1
            out.append(_rec("persona", "persona_orphan", "element", "LOW", 1,
                            f"ORPHAN: {detail}",
                            "an element serves no stated activity -- why is it here?",
                            "state the activity in the persona, tag the element's `serves`, "
                            "or cut it", source_file="persona (in-process)"))
    return out, {"status": "READ", "verdict": verdict, "gaps": n_gap, "orphans": n_orphan}


# ---- Tier-1 self-doubt suite bridge ---------------------------------------------------
# cross_signal / anomaly_flags / confidence / rebuild_diff each emit their OWN domain record
# {signal:'<source>:<check>', severity, confidence, room, subjects[], detail, why, resolve_by}.
# _wrap_domain maps ONE into the self-audit _rec taxonomy so it ranks in the same doubt list; the
# module's own SEVERITY band drives the rank (an unsigned facing REVERSAL is CRITICAL, sitting with
# floating/regression; a soft facing nudge is MEDIUM). count=1 (each domain record is one doubt).
# Every collector: lazy+guarded import so a missing/broken suite module degrades to ERROR coverage,
# never a crash of the whole audit (mirrors collect_sourceability); honest coverage so a short list
# never silently means "clean" when it means "did not look".
def _wrap_domain(rec, scope="room", source_file=None):
    """Map ONE suite domain-record into the _rec taxonomy, or None if it cannot be mapped. NEVER
    raises: a non-dict record, a non-string/absent signal, or an out-of-taxonomy severity from a
    BUGGY module is dropped/clamped rather than allowed to abort the whole audit (the collectors'
    guarantee is 'a broken suite module degrades to ERROR coverage, never a crash'). A clamped-band
    record still surfaces at LOW so a real doubt is not silently lost to a typo'd severity."""
    if not isinstance(rec, dict):
        return None
    signal = rec.get("signal")
    signal = signal if isinstance(signal, str) else ":"
    source, _, check = signal.partition(":")
    sev = rec.get("severity")
    if sev not in SEVERITY_WEIGHT:
        sev = "LOW"                        # a typo'd/out-of-taxonomy band -> safe advisory, never KeyError
    detail = rec.get("detail") or ""
    conf = rec.get("confidence")
    if isinstance(conf, (int, float)) and not isinstance(conf, bool):
        detail = f"{detail}  (flag-confidence {round(float(conf), 2)})"
    subs = rec.get("subjects") or []
    if isinstance(subs, (list, tuple)) and subs:
        detail = f"{detail}  [{', '.join(str(s) for s in subs)}]"
    return _rec(source or "suite", check or "doubt", scope, sev, 1, detail,
                rec.get("why", ""), rec.get("resolve_by", ""),
                room=rec.get("room"), source_file=source_file)


def _wrap_all(recs, scope="room", source_file=None):
    """Map a suite module's records into _rec, DROPPING any _wrap_domain cannot map. This is the
    single choke point that keeps a malformed module RETURN (not just a raised call) from crashing
    audit_project -- the mapping is otherwise outside the per-spec try/except."""
    out = []
    for r in recs or []:
        w = _wrap_domain(r, scope=scope, source_file=source_file)
        if w is not None:
            out.append(w)
    return out


def collect_cross_signal(specs, walls, glazing_cands, confirmed):
    """Contradictions between two INDEPENDENT reads of a room (facing vs wall, function vs
    placement, zone vs geometry, facade vs wall, fixture vs room-type). specs = [(path, spec)].
    Returns (records, coverage). READ when >=1 check was ELIGIBLE somewhere (had the inputs it
    needs); UNWIRED when specs existed but nothing was eligible; ABSENT when no specs."""
    out = []
    try:
        import cross_signal as CS
    except Exception as e:
        return out, {"status": "ERROR", "note": f"import failed: {e}"}
    if not specs:
        return out, {"status": "ABSENT"}
    params = {"confirmed": confirmed} if confirmed else None
    per_spec, n_eligible, n_error = {}, 0, 0
    for path, spec in specs:
        sf = os.path.basename(path)
        try:
            recs = CS.check_room(spec, walls=walls, glazing_cands=glazing_cands, params=params)
            cov = CS.check_coverage(spec, walls=walls, glazing_cands=glazing_cands)
        except Exception as e:
            per_spec[sf] = f"ERROR: {e}"
            n_error += 1
            continue
        out += _wrap_all(recs, source_file=sf)
        elig = sorted(k for k, v in cov.items() if v.get("eligible"))
        n_eligible += len(elig)
        per_spec[sf] = {"eligible_checks": elig, "flags": len(recs)}
    # honest-coverage precedence: an all-errored run is a BLIND SPOT, never a clean UNWIRED
    status = "ERROR" if (n_error and not n_eligible) else ("READ" if n_eligible else "UNWIRED")
    return out, {"status": status, "flags": len(out), "eligible_checks": n_eligible,
                 "errored": n_error,
                 "per_spec": per_spec,
                 "note": None if n_eligible else "ran, but no check had its required inputs "
                 "(e.g. no walls/glazing for facade checks) -- not a clean pass"}


def collect_anomaly(specs, priors, confirmed):
    """Prior-violating reads (impossible size/aspect for a claimed kind, abnormal count). specs =
    [(path, spec)]. priors = a kind-priors artifact or None. Returns (records, coverage). The
    built-in gross bounds always run (READ when any measurable piece); the corpus prior-band lane
    is UNWIRED without a priors artifact -- honestly, never a silent clean pass."""
    out = []
    try:
        import anomaly_flags as AF
    except Exception as e:
        return out, {"status": "ERROR", "note": f"import failed: {e}"}
    if not specs:
        return out, {"status": "ABSENT"}
    params = {"confirmed": confirmed} if confirmed else None
    per_spec, measured_any, no_bound, n_error = {}, False, set(), 0
    for path, spec in specs:
        sf = os.path.basename(path)
        try:
            recs = AF.check_room(spec, priors=priors, params=params)
            cov = AF.check_coverage(spec, priors=priors, params=params)
        except Exception as e:
            per_spec[sf] = f"ERROR: {e}"
            n_error += 1
            continue
        out += _wrap_all(recs, source_file=sf)
        if (cov.get("size_implausible") or {}).get("status") == "READ":
            measured_any = True
        no_bound |= set(cov.get("no_bound_kinds") or [])
        per_spec[sf] = {"flags": len(recs)}
    status = "ERROR" if (n_error and not measured_any) else ("READ" if measured_any else "UNWIRED")
    return out, {"status": status, "flags": len(out), "errored": n_error,
                 "prior_band": "READ" if priors else "UNWIRED (no corpus priors -- gross "
                 "built-in bounds only)",
                 "no_bound_kinds": sorted(no_bound), "per_spec": per_spec}


def collect_confidence(specs, confirmed):
    """Base-read calibration: an ASSUMED/DEFAULTED semantic field (rot omitted -> assumed south;
    zone absent -> assumed indoor; kind hand-typed with nothing corroborating) shipped as if
    certain, below the say-unsure threshold. specs = [(path, spec)]. Returns (records, coverage)
    reporting how many fields were owner-signed vs flagged-unsure (the calibration STATE)."""
    out = []
    try:
        import confidence as CF
    except Exception as e:
        return out, {"status": "ERROR", "note": f"import failed: {e}"}
    if not specs:
        return out, {"status": "ABSENT"}
    per_spec, signed_tot, flagged_tot, assessed_tot, n_error = {}, 0, 0, 0, 0
    for path, spec in specs:
        sf = os.path.basename(path)
        try:
            recs = CF.assess_room(spec, confirmed)
            cov = CF.assess_coverage(spec, confirmed)
        except Exception as e:
            per_spec[sf] = f"ERROR: {e}"
            n_error += 1
            continue
        out += _wrap_all(recs, scope="element", source_file=sf)
        signed_tot += cov.get("owner_signed", 0)
        flagged_tot += cov.get("flagged_unsure", 0)
        assessed_tot += cov.get("assessed_fields", 0)
        per_spec[sf] = {"assessed": cov.get("assessed_fields"),
                        "owner_signed": cov.get("owner_signed"),
                        "flagged_unsure": cov.get("flagged_unsure")}
    status = "ERROR" if (n_error and not assessed_tot) else ("READ" if assessed_tot else "ABSENT")
    return out, {"status": status, "assessed_fields": assessed_tot, "owner_signed": signed_tot,
                 "flagged_unsure": flagged_tot, "errored": n_error, "per_spec": per_spec}


def collect_rebuild_diff(prior_specs, current_specs, confirmed):
    """Between-rounds regression backstop: a SEMANTIC field (kind/facing/zone) that changed from the
    prior reading round with NO owner signature covering the new value -- the v4 silent-facing-flip
    wound. prior_specs/current_specs = [spec, ...]. Returns (records, coverage). UNWIRED (never a
    clean pass) when there is no prior round to diff against."""
    out = []
    try:
        import rebuild_diff as RD
    except Exception as e:
        return out, {"status": "ERROR", "note": f"import failed: {e}"}
    try:
        recs = RD.diff_rounds(prior_specs, current_specs, confirmed=confirmed)
        cov = RD.diff_coverage(prior_specs, current_specs)
    except Exception as e:
        return out, {"status": "ERROR", "note": f"diff failed: {e}"}
    out += _wrap_all(recs)
    cov = dict(cov)
    cov["flags"] = len(out)
    return out, cov


# ---- ranking / scoring ----------------------------------------------------------------
def rank(records):
    """Open (unresolved) records, most-consequential-and-least-certain first. SEVERITY BAND
    dominates: every CRITICAL before every HIGH before every MEDIUM before every LOW -- so a
    high-count LOW noise pile can NEVER bury a low-count MEDIUM doubt (the bug the first live
    run exposed). Within a band, higher count/score first, then source/kind/room for a fully
    deterministic order."""
    open_recs = [r for r in records if not r["resolved"]]
    return sorted(open_recs, key=lambda r: (SEVERITY_ORDER[r["severity"]], -r["count"],
                                            -r["score"], r["source"], r["kind"],
                                            str(r.get("room"))))


def doubt_score(records):
    """One regressable number: summed weight of OPEN doubt. Reads meaningfully ONLY beside
    the coverage line -- a low score with poor coverage means 'did not look', not 'clean'."""
    return sum(r["score"] for r in records if not r["resolved"])


def summarise(records):
    open_recs = [r for r in records if not r["resolved"]]
    by_sev = {s: 0 for s in SEVERITY_WEIGHT}
    for r in open_recs:
        by_sev[r["severity"]] += 1
    return {"doubt_score": doubt_score(records), "open": len(open_recs),
            "resolved": sum(1 for r in records if r["resolved"]), "by_severity": by_sev}


# ---- disk / assembly ------------------------------------------------------------------
def _pick_gate(project_dir):
    """Prefer the marker in the highest-numbered version dir (v4 > v3 > root): later
    versions supersede earlier known-flawed ones. Returns (path or None, all_paths)."""
    paths = sorted(glob.glob(os.path.join(project_dir, "**", "placement-gate.json"),
                             recursive=True))
    if not paths:
        return None, []

    def ver(p):
        m = re.search(r"[\\/]v(\d+)[\\/]", p)
        return int(m.group(1)) if m else -1
    best = max(paths, key=lambda p: (ver(p), len(p)))
    return best, paths


def _resolve_out_dir(out_dir, gate_path, project_dir):
    """Where self-audit.json/.md land. Explicit --out wins; else the gate's layout dir;
    else the PROJECT dir itself -- never os.path.dirname(project_dir), which would drop
    the files in the parent (projects/ root) and let every gateless project clobber one
    shared file (and could brush the clients/ boundary)."""
    if out_dir:
        return out_dir
    if gate_path:
        return os.path.dirname(gate_path)
    return project_dir


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _find_specs(layout_dir):
    """Per-room scene-graphs for the in-process gates. The combined `scene-graph.json`
    (no room suffix) is skipped -- it is a bundle, and sourceability/persona want one room
    each. Returns [(path, spec_dict)] for the ones that parse."""
    specs = []
    for p in sorted(glob.glob(os.path.join(layout_dir, "scene-graph.*.json"))):
        base = os.path.basename(p)
        if base == "scene-graph.json":
            continue
        try:
            specs.append((p, _load(p)))
        except Exception:
            continue
    return specs


def _load_walls(layout_dir):
    """The floor's extracted wall segments [[[x1,y1],[x2,y2]],...] for the cross-signal facade
    checks, or None (UNKNOWN -> the checks that need walls ABSTAIN, never a silent pass). Takes the
    first *walls*.json beside the gated specs that carries a 'segments' list."""
    for p in sorted(glob.glob(os.path.join(layout_dir, "*walls*.json"))):
        try:
            doc = _load(p)
        except Exception:
            continue
        if isinstance(doc, dict) and isinstance(doc.get("segments"), list):
            return doc["segments"]
    return None


def _load_priors(project_dir):
    """A kind-priors corpus artifact (schema interior-ai/kind-priors@0.1) if one is present under
    qa/ or knowledge/, else None (-> anomaly's prior-band lane reports UNWIRED honestly; the gross
    built-in bounds still run). No artifact exists locally yet, so this returns None today."""
    for root in (os.path.join(project_dir, "..", "..", "qa"),
                 os.path.join(project_dir, "..", "..", "knowledge")):
        for p in sorted(glob.glob(os.path.join(root, "**", "*kind-priors*.json"), recursive=True)):
            try:
                doc = _load(p)
            except Exception:
                continue
            if isinstance(doc, dict) and str(doc.get("schema", "")).startswith(
                    "interior-ai/kind-priors"):
                return doc
    return None


def _round_version(d):
    """A reading-round dir's version: the vN in its path (a vN subdir), else 0 (the root round)."""
    m = re.search(r"[\\/]v(\d+)(?:[\\/]|$)", os.path.abspath(d) + os.sep)
    return int(m.group(1)) if m else 0


def _find_prior_specs(project_dir, current_layout_dir):
    """The reading round immediately BEFORE the current one, for rebuild_diff: the round dir whose
    version is the highest STRICTLY LESS than the current dir's version (the LAYOUT stage root = 0,
    a vN subdir = N). Returns [spec, ...] (empty when there is no prior round -> rebuild_diff reports
    UNWIRED, never a clean pass).

    SCOPED to the LAYOUT STAGE dir (the current round's own vN parent, or the round dir itself when
    it is the un-versioned root) -- NOT the whole project. A scene-graph copied into ANOTHER stage
    (e.g. 04_visualization/v2/) is a render artifact, not a reading round, and must never be mistaken
    for the prior read (it would diff the layout against a foreign ghost)."""
    current_layout_dir = os.path.abspath(current_layout_dir)
    cur_ver = _round_version(current_layout_dir)
    # the stage root that holds this round's sibling versions: a vN subdir's parent, else itself.
    stage_dir = os.path.dirname(current_layout_dir) if cur_ver > 0 else current_layout_dir
    round_dirs = {}
    for p in glob.glob(os.path.join(stage_dir, "**", "scene-graph.*.json"), recursive=True):
        if os.path.basename(p) == "scene-graph.json":
            continue
        d = os.path.dirname(os.path.abspath(p))
        round_dirs[d] = _round_version(d)
    below = [(v, d) for d, v in round_dirs.items() if v < cur_ver]
    if not below:
        return []
    _, prior_dir = max(below)
    return [spec for _p, spec in _find_specs(prior_dir)]


def audit_project(project_dir, gate_path=None):
    """Full owner-free audit of one project dir. Returns the report dict (records + ranked
    list + summary + per-source coverage). Every source that is absent/unwired says so."""
    project_dir = os.path.abspath(project_dir)
    coverage = {}
    records = []

    gate_path = gate_path or _pick_gate(project_dir)[0]
    if gate_path and os.path.exists(gate_path):
        gate = _load(gate_path)
        records += collect_gate(gate, source_file=os.path.relpath(gate_path, project_dir))
        coverage["placement_gate"] = {"status": "READ", "path": gate_path,
                                       "verdict": gate.get("verdict"),
                                       "calibration": gate.get("calibration")}
        layout_dir = os.path.dirname(gate_path)
    else:
        coverage["placement_gate"] = {"status": "ABSENT",
                                      "note": "no placement-gate.json under project"}
        layout_dir = os.path.join(project_dir, "03_layout")

    # owner ledger (for facade suppression) lives beside the gate
    review = {}
    review_path = os.path.join(layout_dir, "placement-review.json")
    if os.path.exists(review_path):
        try:
            review = _load(review_path)
        except Exception:
            review = {}

    facade_path = os.path.join(layout_dir, "facade-candidates.json")
    if os.path.exists(facade_path):
        fac = collect_facade(_load(facade_path), review,
                             source_file=os.path.relpath(facade_path, project_dir))
        records += fac
        coverage["facade"] = {"status": "READ", "path": facade_path,
                              "candidates": len(fac),
                              "resolved": sum(1 for r in fac if r["resolved"])}
    else:
        coverage["facade"] = {"status": "ABSENT"}

    glazing_doc = None
    glazing_path = os.path.join(layout_dir, "glazing-candidates.json")
    if os.path.exists(glazing_path):
        glazing_doc = _load(glazing_path)
        gl = collect_glazing(glazing_doc, source_file=os.path.relpath(glazing_path, project_dir))
        records += gl
        coverage["glazing"] = {"status": "READ" if gl else "UNWIRED", "path": glazing_path}
    else:
        coverage["glazing"] = {"status": "ABSENT"}

    specs = _find_specs(layout_dir)
    src_recs, src_cov = collect_sourceability(specs)
    records += src_recs
    coverage["sourceability"] = src_cov
    per_recs, per_cov = collect_persona(specs)
    records += per_recs
    coverage["persona"] = per_cov

    # ---- Tier-1 self-doubt suite: cross-signal / anomaly / confidence / rebuild-diff -----
    # These make the machine doubt itself at the RIGHT points with NO owner in the loop: an
    # owner sign always SUPPRESSES (two-layer law), so they converge toward quiet as the owner
    # adjudicates. The owner ledger (confirmed[]) drives that suppression; walls + glazing feed
    # the cross-signal facade checks; the prior reading round feeds the rebuild-diff regression
    # backstop; corpus priors (absent today) would sharpen anomaly's size bands (UNWIRED honest).
    confirmed = (review.get("confirmed") if isinstance(review, dict) else None) or []
    walls = _load_walls(layout_dir)
    glazing_cands = glazing_doc.get("candidates") if isinstance(glazing_doc, dict) else None
    priors = _load_priors(project_dir)

    cs_recs, cs_cov = collect_cross_signal(specs, walls, glazing_cands, confirmed)
    records += cs_recs
    coverage["cross_signal"] = cs_cov
    an_recs, an_cov = collect_anomaly(specs, priors, confirmed)
    records += an_recs
    coverage["anomaly"] = an_cov
    cf_recs, cf_cov = collect_confidence(specs, confirmed)
    records += cf_recs
    coverage["confidence"] = cf_cov
    prior_specs = _find_prior_specs(project_dir, layout_dir)
    current_specs = [spec for _p, spec in specs]
    rd_recs, rd_cov = collect_rebuild_diff(prior_specs, current_specs, confirmed)
    records += rd_recs
    coverage["rebuild_diff"] = rd_cov

    ranked = rank(records)
    return {"schema": "interior-ai/self-audit@0.1", "project_dir": project_dir,
            "gate_path": gate_path, "summary": summarise(records),
            "coverage": coverage, "records": records, "ranked": ranked}


def render_md(report):
    s = report["summary"]
    L = [f"# self-audit -- {os.path.basename(report['project_dir'])}", "",
         f"**doubt-score {s['doubt_score']}**  ({s['open']} open, {s['resolved']} "
         f"owner-resolved)  "
         f"CRITICAL {s['by_severity']['CRITICAL']} · HIGH {s['by_severity']['HIGH']} · "
         f"MEDIUM {s['by_severity']['MEDIUM']} · LOW {s['by_severity']['LOW']}", ""]
    L.append("> The doubt-score reads meaningfully ONLY with the coverage line below: a "
             "low score under thin coverage means *did not look*, not *clean*.")
    L.append("")
    L.append("## Ranked doubts (where I am least certain, worst first)")
    if not report["ranked"]:
        L.append("- (none open -- see coverage: a clean list is only as good as what was read)")
    for i, r in enumerate(report["ranked"], 1):
        where = f" @{r['room']}" if r.get("room") else ""
        L.append(f"{i}. **[{r['severity']}] {r['kind']}**{where} — {r['detail']}")
        L.append(f"   - why: {r['why']}")
        L.append(f"   - resolve: {r['resolve_by']}")
    L.append("")
    L.append("## Coverage (which of my doubt-sources actually reported)")
    for src, c in report["coverage"].items():
        extra = "  ".join(f"{k}={v}" for k, v in c.items()
                          if k not in ("status", "path", "per_spec", "note"))
        note = f" — {c['note']}" if c.get("note") else ""
        L.append(f"- **{src}**: {c['status']}  {extra}{note}")
    L.append("")
    L.append("READ = reported; ABSENT = artifact/input not present; UNWIRED = ran but no "
             "eligible data (never a pass); ERROR = source failed (a blind spot in the "
             "audit itself). CRITICAL = confident-WRONG (regression/build-blocker), not "
             "doubt; HIGH/MEDIUM/LOW = open doubt.")
    return "\n".join(L)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    project_dir = args[0]
    gate_path = None
    out_dir = None
    want_json = False
    i = 1
    while i < len(args):
        if args[i] == "--gate":
            gate_path = args[i + 1]; i += 2
        elif args[i] == "--out":
            out_dir = args[i + 1]; i += 2
        elif args[i] == "--json":
            want_json = True; i += 1
        else:
            i += 1
    report = audit_project(project_dir, gate_path=gate_path)
    md = render_md(report)
    print(md)
    out_dir = _resolve_out_dir(out_dir, report["gate_path"], report["project_dir"])
    if os.path.isdir(out_dir):
        with open(os.path.join(out_dir, "self-audit.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
        with open(os.path.join(out_dir, "self-audit.md"), "w", encoding="utf-8") as fh:
            fh.write(md + "\n")
        print(f"\nwrote self-audit.json + self-audit.md to {out_dir}")
    if want_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
