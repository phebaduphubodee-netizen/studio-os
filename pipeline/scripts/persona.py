#!/usr/bin/env python3
"""persona.py — PERSONA-DRIVEN design layer: derive a program of requirements from WHO
the client is + how they live, then check the design BOTH ways against it.

The chain the owner wants (runs opposite to a normal geometry spec):

    WHO + lifestyle  ->  ACTIVITIES / rituals  ->  a REQUIREMENT per activity  ->  ELEMENT(s)
      (persona)          (morning coffee, read)     ("a place for coffee")         (balcony nook, bookshelf)

An element's "why it is here" becomes *serves activity X (the client does Y)*, not
"declared in spec". Two-way COVERAGE is the point:
  - GAP    — a stated activity with NO serving element (the design misses the person's life).
  - ORPHAN — a lifestyle element serving NO stated activity ("why is this here?").

HONESTY split (this is the whole integrity of the layer):
  - DETERMINISTIC: activity -> requirement (activity_taxonomy) and element -> activity
    (activity_taxonomy). Pure lookups.
  - JUDGMENT:      persona free-text ("I read before bed") -> an activity id (`read`). That
    mapping is done ONCE, at persona-authoring time (LLM- or human-assisted), and RECORDED
    on the persona as a structured `activity` field CITED to the source line. This module
    CONSUMES those structured activities — it never re-infers an activity from prose (that
    would be fabrication). A ritual with prose but no `activity` tag is FLAGGED
    "un-mapped ritual (needs an activity tag)", never silently guessed.

SCOPE: a persona's life spans the whole HOME, but specs are per-room. So the checker is
HOME-AWARE: pass one spec OR a list of the home's specs. An activity is a GAP only when NO
room serves it (a bedroom is not faulted for lacking a kitchen). Orphans are per element.

SEVERITY: a GAP/ORPHAN/AMBIGUOUS is a WARN -> the deliverable goes to REVIEW, never a hard
FAIL. A persona is inherently incomplete and a missing reading nook is a designer's call,
not a safety breach like a FUNCTION FAIL (TV behind the sleeper's head). No persona ->
UNWIRED (honest: never a silent pass, never a false gap). Same (results, verdict) shape as
placement_logic.report / suite_clearance, so it drops into the same gate + deliverable
machinery. Degrade-never-throw: any sub-failure yields an honest UNWIRED row, never a crash.

PRIVACY: a real persona is CLIENT DATA — local only, C-NNN not a name, band numerics before
any outbound tool call (.claude/rules/client-privacy.md). The demo persona MUST be fictional
and labelled `_fictional: true` (examples convention). This module reads a persona dict/file;
it performs NO outbound calls.

    python pipeline/scripts/persona.py PERSONA.json SPEC.json [SPEC2.json ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import activity_taxonomy as AT

PASS, WARN, FAIL, UNWIRED = "PASS", "WARN", "FAIL", "UNWIRED"

# priority ranking for a requirement's source (a gap on a must-have is louder than on a
# nice-to-have). Ordinal only — it colours the detail, it does not change the WARN verdict.
PRIORITY = {"must_have": 3, "ritual": 2, "work": 2, "entertain": 2, "hobby": 1, "nice_to_have": 1}


# --------------------------------------------------------------------------- #
# Persona loading (tolerant)                                                    #
# --------------------------------------------------------------------------- #
def load_persona(src):
    """Accept a path, a dict, or None. Returns a dict (possibly {}) — never throws."""
    if src is None:
        return {}
    if isinstance(src, dict):
        return src
    try:
        import json
        with open(src, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def find_persona_for(spec, spec_path=None):
    """Locate a persona for a spec WITHOUT forcing one (most specs have none yet):
      (1) spec['persona'] as an inline dict, or a path (abs, or relative to the spec dir);
      (2) a sibling '<spec-stem>.persona.json' or 'persona.json' in the spec's directory.
    Returns a persona dict, or {} when none is found. Never throws — a discovery hiccup must
    not touch the deliverable. Absent persona -> {} -> the coverage layer is UNWIRED (no-op)."""
    try:
        p = spec.get("persona") if isinstance(spec, dict) else None
        if isinstance(p, dict):
            return p
        base = os.path.dirname(os.path.abspath(spec_path)) if spec_path else None
        cands = []
        if isinstance(p, str) and p.strip():
            cands.append(p if os.path.isabs(p) else (os.path.join(base, p) if base else p))
        if base:
            stem = os.path.splitext(os.path.basename(spec_path))[0]
            cands += [os.path.join(base, stem + ".persona.json"), os.path.join(base, "persona.json")]
        for c in cands:
            if c and os.path.exists(c):
                return load_persona(c)
    except Exception:
        pass
    return {}


# --------------------------------------------------------------------------- #
# Requirement derivation — persona -> [{activity, sources, priority, requirement}]        #
# --------------------------------------------------------------------------- #
def derive_requirements(persona):
    """The 'programming' pass: turn the persona's STRUCTURED, cited activities into a
    program of requirements. Returns (requirements, unmapped) where:
      requirements = [{activity, label, needs, zone, adjacency, baseline, priority,
                       sources:[{statement, cite}], cite}]  (one per distinct activity)
      unmapped     = [{statement, cite, why}]  — rituals/wants with prose but no activity tag
                     (JUDGMENT owed; surfaced to the human, NOT auto-inferred).
    A persona with no structured activities yields ([], [...]) — honest, not a fake program."""
    persona = persona or {}
    by_activity = {}     # activity -> {"sources": [...], "priority": int}
    unmapped = []

    def note(activity, statement, cite, priority_key):
        if not activity:
            unmapped.append({"statement": statement, "cite": cite,
                             "why": "no `activity` tag — mapping this to an activity is a "
                                    "judgment call owed to the author, not auto-inferred"})
            return
        if activity not in AT.ACTIVITIES:
            unmapped.append({"statement": statement, "cite": cite,
                             "why": f"activity '{activity}' is not in the taxonomy"})
            return
        slot = by_activity.setdefault(activity, {"sources": [], "priority": 0, "priority_key": "ritual"})
        slot["sources"].append({"statement": statement, "cite": cite})
        pv = PRIORITY.get(priority_key, 1)
        if pv > slot["priority"]:                 # carry the WINNING key (not a reverse-lookup,
            slot["priority"] = pv                 # which mislabels keys that share a numeric value)
            slot["priority_key"] = priority_key

    # daily rituals: {ritual, activity, cite}
    for r in _as_list(persona.get("daily_rituals")):
        if isinstance(r, dict):
            note(r.get("activity"), r.get("ritual") or r.get("statement") or "(ritual)",
                 r.get("cite") or "persona.daily_rituals", "ritual")
        elif isinstance(r, str):
            note(None, r, "persona.daily_rituals", "ritual")
    # hobbies: {hobby, activity, cite} — default activity 'hobby' when tagged loosely
    for h in _as_list(persona.get("hobbies")):
        if isinstance(h, dict):
            note(h.get("activity") or "hobby", h.get("hobby") or h.get("statement") or "(hobby)",
                 h.get("cite") or "persona.hobbies", "hobby")
        elif isinstance(h, str):
            note(None, h, "persona.hobbies", "hobby")
    # work pattern: wfh true implies the 'work' activity
    wp = persona.get("work_pattern")
    if isinstance(wp, dict) and wp.get("wfh"):
        note("work", wp.get("note") or "works from home", "persona.work_pattern.wfh", "work")
    # entertaining: {frequency, activity, note}. An explicit "never/rarely" is NOT a
    # requirement — gating on truthiness alone would let "never" manufacture a false entertain GAP.
    ent = persona.get("entertaining")
    if isinstance(ent, dict):
        freq = str(ent.get("frequency") or "").strip().lower()
        negative = freq in {"never", "none", "no", "not", "rarely", "n/a", "not at all"}
        if ent.get("activity") or (freq and not negative):
            note(ent.get("activity") or "entertain",
                 ent.get("note") or f"entertains ({ent.get('frequency', 'sometimes')})",
                 "persona.entertaining", "entertain")
    # must_have / nice_to_have: [str] or [{want, activity, cite}]
    for key, pk in (("must_have", "must_have"), ("nice_to_have", "nice_to_have")):
        for w in _as_list(persona.get(key)):
            if isinstance(w, dict):
                note(w.get("activity"), w.get("want") or w.get("statement") or "(want)",
                     w.get("cite") or f"persona.{key}", pk)
            elif isinstance(w, str):
                note(None, w, f"persona.{key}", pk)

    requirements = []
    for activity, slot in by_activity.items():
        req = AT.requirement_for(activity)
        req = dict(req) if req else {"activity": activity}
        req["sources"] = slot["sources"]
        req["priority"] = slot["priority"]
        req["priority_label"] = slot["priority_key"]
        requirements.append(req)
    # loud first: must-have gaps before nice-to-haves
    requirements.sort(key=lambda r: -r.get("priority", 0))
    return requirements, unmapped


def persona_lifestyle_activities(persona):
    """The set of LIFESTYLE activities the persona actually does (baseline activities are
    universal, so they are excluded here — they justify an element on their own)."""
    reqs, _ = derive_requirements(persona)
    return {r["activity"] for r in reqs if r["activity"] in AT.LIFESTYLE_ACTIVITIES}


# --------------------------------------------------------------------------- #
# Element iteration across a room-spec                                          #
# --------------------------------------------------------------------------- #
def _iter_room_elements(spec):
    """Yield (element, group) over builtins + items + every subroom's fixtures. Skips any
    non-dict element / non-dict subroom at this single choke point so one junk entry in an
    LLM-emitted spec degrades that element out, never crashes check()/report()/to_markdown()
    (the module's degrade-never-throw contract)."""
    for b in _as_list(spec.get("builtins")):
        if isinstance(b, dict):
            yield b, "builtins"
    for it in _as_list(spec.get("items")):
        if isinstance(it, dict):
            yield it, "items"
    for sr in _as_list(spec.get("subrooms")):
        if isinstance(sr, dict):
            for fx in _as_list(sr.get("fixtures")):
                if isinstance(fx, dict):
                    yield fx, "fixtures"


def _room_label(spec, i):
    rt = (spec.get("room") or {}).get("type") or spec.get("room_type") or f"room{i + 1}"
    return str(rt)


def _elname(el):
    return el.get("name") or el.get("kind") or "?"


# --------------------------------------------------------------------------- #
# Two-way coverage checker (home-aware)                                         #
# --------------------------------------------------------------------------- #
def check(spec_or_specs, persona):
    """Two-way persona coverage over ONE spec or a LIST of the home's specs.

    Returns {status, requirements:[...], elements:[...], unmapped:[...],
             has_persona, n_rooms}. Never throws."""
    persona = load_persona(persona) if not isinstance(persona, dict) else persona
    specs = spec_or_specs if isinstance(spec_or_specs, list) else [spec_or_specs]
    specs = [s for s in specs if isinstance(s, dict)]

    requirements, unmapped = derive_requirements(persona)
    lifestyle = {r["activity"] for r in requirements if r["activity"] in AT.LIFESTYLE_ACTIVITIES}

    # --- forward: what does the HOME serve (aggregate across rooms)? ---
    served = {}                          # activity -> [{"room","element"}]
    element_records = []                 # per element, for the orphan pass
    for i, spec in enumerate(specs):
        room = _room_label(spec, i)
        for el, group in _iter_room_elements(spec):
            ea = AT.element_activities(el)
            acts = ea["activities"]
            kind = str(el.get("kind", "") or "").strip()
            for a in acts:
                # a served link is SOFT when it rests only on the NAME signal (not the kind
                # map, not an explicit `serves` tag) — honesty: a "reading chair" meeting the
                # `read` requirement must not read as decisively as a real bookshelf would.
                soft = ea["source"] != "serves" and a not in AT.KIND_ACTIVITY.get(kind, [])
                served.setdefault(a, []).append({"room": room, "element": _elname(el), "soft": soft})
            element_records.append({"room": room, "element": _elname(el),
                                    "kind": el.get("kind"), "group": group,
                                    "activities": acts, "source": ea["source"], "detail": ea["detail"]})

    # --- requirement coverage (GAP the persona activities that no room serves) ---
    req_rows = []
    for req in requirements:
        a = req["activity"]
        met = served.get(a, [])
        req_rows.append({**req, "met_by": met, "status": (PASS if met else WARN),
                         "coverage": ("met" if met else "gap")})

    # --- element coverage (ORPHAN / AMBIGUOUS) ---
    el_rows = []
    for rec in element_records:
        acts = rec["activities"]
        unjustified = []
        if not acts:
            status, coverage = WARN, "ambiguous"
        else:
            # ORPHAN judged PER lifestyle-activity, not all-or-nothing per element: an
            # element that ALSO serves a baseline need is STILL an orphan if it carries a
            # LIFESTYLE activity the persona never states — e.g. a fused headboard_tv =
            # sleep(baseline)+relax; fusing the TV into a baseline built-in must not hide
            # the unstated 'relax' (the exact fused-vs-standalone blind spot the FUNCTION
            # layer exists to expose). `entertain` is excluded: it is deliberately over-
            # assigned to all seating/dining in the taxonomy to avoid false GAPs, so it must
            # not manufacture false ORPHANs symmetrically (every sofa/dining chair).
            unjustified = [a for a in acts
                           if a in AT.LIFESTYLE_ACTIVITIES and a not in lifestyle and a != "entertain"]
            if unjustified:
                status, coverage = WARN, "orphan"
            elif any(a in AT.BASELINE_ACTIVITIES or a in lifestyle for a in acts):
                status, coverage = PASS, "served"
            else:
                status, coverage = WARN, "orphan"
        el_rows.append({**rec, "status": status, "coverage": coverage, "unjustified": unjustified})

    if not persona:
        status = UNWIRED
    elif unmapped:
        status = WARN                            # a judgment is owed -> never a clean PASS (agrees with report())
    elif not requirements and not any(r["activities"] for r in element_records):
        status = UNWIRED
    else:
        worst = [r["status"] for r in req_rows] + [r["status"] for r in el_rows]
        status = WARN if WARN in worst else (PASS if worst else UNWIRED)

    return {"status": status, "requirements": req_rows, "elements": el_rows,
            "unmapped": unmapped, "has_persona": bool(persona), "n_rooms": len(specs)}


def report(spec_or_specs, persona=None):
    """Gate-shaped result: (results, verdict). Rows share {status, check, detail} with
    every check prefixed 'persona:' so they never collide with a clearance/function row.

    verdict: UNWIRED if no persona / nothing derivable (never a silent pass); REVIEW if any
    GAP/ORPHAN/AMBIGUOUS (a design-completeness call for the human); PASS if two-way clean.
    Advisory by design — never FAIL (a persona gap is not a render-blocking safety breach)."""
    try:
        r = check(spec_or_specs, persona)
    except Exception as e:   # noqa: BLE001 — a coverage bug must never break a deliverable
        return [{"status": UNWIRED, "check": "persona:routing", "detail": str(e)}], UNWIRED
    if not r.get("has_persona"):
        return [], UNWIRED                       # no persona -> nothing to check against (not a pass)

    results = []
    for req in r["requirements"]:
        src = "; ".join(s["statement"] for s in req.get("sources", []))
        if req["coverage"] == "met":
            who = ", ".join(f"{m['element']}@{m['room']}" for m in req["met_by"][:4])
            soft = bool(req["met_by"]) and all(m.get("soft") for m in req["met_by"])
            caveat = " (SOFT name signal — verify intent)" if soft else ""
            results.append({"status": PASS, "check": f"persona:met:{req['activity']}",
                            "detail": f"'{req.get('label', req['activity'])}' ({src}) -> served by {who}{caveat}"})
        else:
            kinds = AT.kinds_serving(req["activity"])
            hint = f" (add e.g. {', '.join(kinds[:4])})" if kinds else ""
            results.append({"status": WARN, "check": f"persona:gap:{req['activity']}",
                            "detail": f"GAP [{req.get('priority_label', 'ritual')}]: the client "
                                      f"'{req.get('label', req['activity'])}' ({src}) but NO element in the "
                                      f"home serves it — needs {req.get('needs', 'an element')}{hint}"})
    for el in r["elements"]:
        if el["coverage"] == "orphan":
            unj = el.get("unjustified") or el["activities"]
            results.append({"status": WARN, "check": f"persona:orphan:{el['kind']}",
                            "detail": f"ORPHAN: '{el['element']}'@{el['room']} serves {unj} "
                                      f"which the persona never states — why is it here? "
                                      f"(cut it, or tag the persona / element)"})
        elif el["coverage"] == "ambiguous":
            results.append({"status": WARN, "check": f"persona:ambiguous:{el['kind']}",
                            "detail": f"AMBIGUOUS: '{el['element']}'@{el['room']} — {el['detail']}"})
    for um in r["unmapped"]:
        results.append({"status": WARN, "check": "persona:unmapped-ritual",
                        "detail": f"'{um['statement']}' ({um['cite']}): {um['why']}"})

    if not results:
        return [], UNWIRED                       # persona present but nothing derivable/served (honest)
    verdict = "REVIEW" if any(x["status"] == WARN for x in results) else PASS
    return results, verdict


# --------------------------------------------------------------------------- #
# Presence-axis context for rationale.py                                        #
# --------------------------------------------------------------------------- #
def presence_context(persona):
    """A small dict rationale.py uses to upgrade an element's PRESENCE 'why' from
    'declared in spec' to 'serves activity X (client does Y)'. None-safe."""
    persona = load_persona(persona) if not isinstance(persona, (dict, type(None))) else persona
    if not persona:
        return None
    reqs, _ = derive_requirements(persona)
    lifestyle = {}
    for r in reqs:
        if r["activity"] in AT.LIFESTYLE_ACTIVITIES:
            lifestyle[r["activity"]] = "; ".join(s["statement"] for s in r.get("sources", []))
    return {"lifestyle": lifestyle, "persona_id": persona.get("persona_id", "persona")}


# --------------------------------------------------------------------------- #
# Markdown (deliverable COVERAGE section)                                       #
# --------------------------------------------------------------------------- #
def to_markdown(spec_or_specs, persona=None, name=""):
    r = check(spec_or_specs, persona)
    pid = (load_persona(persona) if not isinstance(persona, dict) else persona).get("persona_id", "persona") \
        if persona else "—"
    L = [f"# PERSONA COVERAGE — {name or 'home'}", "",
         "Does the design serve the person who lives here — and does every element earn its "
         "place? Chain: *who + lifestyle -> activities -> a requirement per activity -> the "
         "element(s) that serve it*. Honesty-first: a persona activity is only a requirement "
         "when the persona STATES it (cited); an unjustified lifestyle element is FLAGGED, not "
         "blessed. Baseline dwelling needs (sleep/wash/store/eat) justify themselves.", ""]
    if not r["has_persona"]:
        L.append("_No persona supplied — coverage UNWIRED (not a pass; there is simply nothing to check against)._")
        return "\n".join(L)
    L.append(f"**Persona:** `{pid}` · rooms checked: {r['n_rooms']} · status: **{r['status']}**")
    L.append("")
    L.append("## Program of requirements (activity -> requirement -> served?)")
    for req in r["requirements"]:
        mark = "✓ met" if req["coverage"] == "met" else "✗ GAP"
        src = "; ".join(s["statement"] for s in req.get("sources", []))
        L.append(f"- **{req.get('label', req['activity'])}** [{req.get('priority_label', 'ritual')}] — {mark}")
        L.append(f"  - client: _{src}_")
        L.append(f"  - needs: {req.get('needs', '?')} · zone: {req.get('zone', '?')}")
        if req["coverage"] == "met":
            served_by = ", ".join("{0}@{1}".format(m["element"], m["room"]) for m in req["met_by"])
            soft = bool(req["met_by"]) and all(m.get("soft") for m in req["met_by"])
            L.append(f"  - served by: {served_by}" + ("  _(SOFT name signal — verify intent)_" if soft else ""))
        else:
            L.append(f"  - **no element serves this — the design misses this part of the client's life**")
    orphans = [e for e in r["elements"] if e["coverage"] == "orphan"]
    ambig = [e for e in r["elements"] if e["coverage"] == "ambiguous"]
    if orphans:
        L += ["", "## Orphans (element serves no stated activity — why is it here?)"]
        for e in orphans:
            L.append(f"- '{e['element']}'@{e['room']} (`{e['kind']}`) serves {e['activities']} — persona never states it")
    if ambig:
        L += ["", "## Ambiguous (purpose undetermined — add a `serves` tag)"]
        for e in ambig:
            L.append(f"- '{e['element']}'@{e['room']} (`{e['kind']}`) — {e['detail']}")
    if r["unmapped"]:
        L += ["", "## Un-mapped persona statements (a judgment is owed — not auto-inferred)"]
        for um in r["unmapped"]:
            L.append(f"- _{um['statement']}_ ({um['cite']}): {um['why']}")
    return "\n".join(L)


if __name__ == "__main__":
    import json
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        raise SystemExit("usage: python persona.py PERSONA.json SPEC.json [SPEC2.json ...]")
    persona = load_persona(sys.argv[1])
    specs = [json.load(open(p, encoding="utf-8")) for p in sys.argv[2:]]
    print(to_markdown(specs, persona, name="+".join(os.path.basename(p) for p in sys.argv[2:])))
    _res, verdict = report(specs, persona)
    print(f"\n-- verdict: {verdict} --")
    sys.exit(0)
