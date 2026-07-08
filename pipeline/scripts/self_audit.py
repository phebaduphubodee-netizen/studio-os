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

    glazing_path = os.path.join(layout_dir, "glazing-candidates.json")
    if os.path.exists(glazing_path):
        gl = collect_glazing(_load(glazing_path),
                             source_file=os.path.relpath(glazing_path, project_dir))
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
