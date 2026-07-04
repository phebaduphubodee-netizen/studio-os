#!/usr/bin/env python3
"""activity_taxonomy.py — the deterministic half of the PERSONA-DRIVEN design layer.

Two lookups, one source of truth:
  (1) kind -> [activity]         which human ACTIVITY a furniture kind serves
  (2) activity -> requirement    what an activity NEEDS (element + zone + adjacency)

WHY: the pipeline is geometry-first — elements arrive pre-placed and the only "why is
this here" the repo can emit is "declared in spec" (rationale.py). This module supplies
the missing link so an element can trace to a human activity, and an activity (a client
ritual) can trace to the element(s) that serve it. That two-way link is what persona.py's
coverage checker walks (GAP = a stated activity with no serving element; ORPHAN = a
lifestyle element serving no stated activity).

HONESTY doctrine (same as placement_logic / rationale):
  - `kind` is DECISIVE for the unambiguous kinds; a `name` is only ever a SOFT signal.
  - Polymorphic kinds (chair/stool/table/bench) that carry no `serves` tag and no name
    signal are left AMBIGUOUS (activities = []), never guessed — the coverage checker
    flags them "tag serves", it does not fabricate a purpose.
  - The kind role-sets are REUSED from placement_logic (BED_KINDS, SEATING_KINDS, the
    BATH_* families, the TV families) so this map can never drift from the FUNCTION gate's
    notion of what a kind is. Additions here (dining/desk/wardrobe/storage) extend, never
    fork, that vocabulary.

GROUNDING: the activity set + each activity's requirement (needed element, zone, preferred
adjacency) follow established architectural-PROGRAMMING / activity-based space-planning
method, distilled into knowledge/programming/architectural-programming-and-activity-taxonomy.md
(NLM DR 2026-07-04, notebook 053ff5e6, 241 sources: NCIDQ/IDFX programming; Karlen & Fleming
*Space Planning Basics* 8-step procedure; Peña & Parshall *Problem Seeking*; Neufert + NKBA
FF&E footprints; Space Syntax adjacencies). That DR independently reproduces this exact
causal chain and a canonical 12-activity taxonomy 1:1 — CONFIRMING the set was not invented.
The kind->activity mappings themselves are self-evident (bed->sleep) and low-risk.

Pure stdlib. Importable (feeds persona.py + rationale.py). Metric where geometry matters,
but this module is mostly symbolic (kind/activity strings), so it is unit-agnostic.
"""
import re

import placement_logic as PL   # reuse the kind role-sets — one source of truth, no drift

# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
CITE_PROGRAMMING = ("architectural programming / activity-based space planning "
                    "(Karlen & Fleming Space Planning Basics; Peña & Parshall Problem Seeking; "
                    "NCIDQ/IDFX; Neufert; NKBA) — "
                    "knowledge/programming/architectural-programming-and-activity-taxonomy.md "
                    "(REFERENCE tier, NLM DR 2026-07-04)")
CITE_KIND = "kind->activity taxonomy (activity_taxonomy.KIND_ACTIVITY; reuses placement_logic kind sets)"
CITE_NAME = "element name signal (SOFT — a name hints intent; kind is decisive)"
CITE_SERVES = "spec element `serves` tag (author-declared intent — authoritative)"


# --------------------------------------------------------------------------- #
# (1) Canonical residential ACTIVITY set + the requirement each implies        #
# --------------------------------------------------------------------------- #
# baseline=True  -> a dwelling needs this REGARDLESS of stated lifestyle (sleep, wash,
#                   store, eat). A baseline element is never an ORPHAN even if the persona
#                   never named the activity — you don't have to say "I sleep" to justify a
#                   bed. baseline=False -> a LIFESTYLE activity: an element serving it is
#                   only justified if the persona actually does it (else it is an orphan).
# needs/zone/adjacency are the human-readable "program of requirements" row for the activity;
# zone/adjacency are ADVISORY narrative (we cannot verify orientation/daylight from an @0.2
# spec — same limit placement_logic honours by refusing to model windows), never a hard gate.
ACTIVITIES = {
    "sleep":         {"label": "sleep",            "th": "นอน",         "baseline": True,
                      "needs": "a bed (+ bedside surface)", "zone": "private, quiet",
                      "adjacency": "away from the entry; not sharing a wall with a wet zone"},
    "groom":         {"label": "groom / toilet",   "th": "ทำธุระ/แต่งตัว", "baseline": True,
                      "needs": "a basin + WC (+ mirror)", "zone": "bathroom (dry sub-zone)",
                      "adjacency": "basin nearest the door (most-used)"},
    "bathe":         {"label": "bathe",            "th": "อาบน้ำ",       "baseline": True,
                      "needs": "a shower or tub", "zone": "bathroom (wet sub-zone)",
                      "adjacency": "deepest from the door; wet kept off the dry zone"},
    "dress_store":   {"label": "dress / store",    "th": "แต่งตัว/เก็บของ", "baseline": True,
                      "needs": "a wardrobe / closet (450–650 mm hanging depth)", "zone": "bedroom / dressing",
                      "adjacency": "off the sleep zone, screened from the entry"},
    "store":         {"label": "general storage",  "th": "เก็บของ",      "baseline": True,
                      "needs": "a cabinet / sideboard", "zone": "any",
                      "adjacency": "near the function it stores for"},
    "dine":          {"label": "dine",             "th": "ทานข้าว",      "baseline": True,
                      "needs": "a dining table + seats for the household", "zone": "dining",
                      "adjacency": "near the kitchen; a serving path"},
    "cook":          {"label": "cook",             "th": "ทำอาหาร",      "baseline": True,
                      "needs": "counter + hob + sink + fridge (work triangle)", "zone": "kitchen",
                      "adjacency": "adjacent to dining"},
    # ---- lifestyle activities (justify an element only if the persona does them) ----
    "work":          {"label": "work (WFH)",       "th": "ทำงาน",        "baseline": False,
                      "needs": "a desk + task chair (+ storage)", "zone": "quiet, daylit, low-traffic",
                      "adjacency": "away from the lounge/TV noise; a window is a plus"},
    "read":          {"label": "read",             "th": "อ่านหนังสือ",   "baseline": False,
                      "needs": "a comfortable seat + task light + book storage", "zone": "a quiet corner",
                      "adjacency": "good light; bedside if reading before sleep"},
    "relax":         {"label": "relax / lounge",   "th": "พักผ่อน/ดูทีวี", "baseline": False,
                      "needs": "lounge seating oriented to a focal (TV / coffee table)", "zone": "living",
                      "adjacency": "seating faces the focal; TV in the line of sight"},
    "coffee_ritual": {"label": "coffee / tea ritual", "th": "กาแฟ/ชายามเช้า", "baseline": False,
                      "needs": "a seat + a small table (a nook)", "zone": "balcony / by a window (morning light)",
                      "adjacency": "outdoor or a bright window; away from work clutter"},
    "entertain":     {"label": "entertain guests", "th": "รับแขก",       "baseline": False,
                      "needs": "extra seating + a social surface (lounge or dining capacity)", "zone": "social",
                      "adjacency": "near the entry / dining; conversational seating"},
    "exercise":      {"label": "exercise",         "th": "ออกกำลังกาย",   "baseline": False,
                      "needs": "clear floor area (+ equipment)", "zone": "a flex space",
                      "adjacency": "ventilation; some privacy"},
    "hobby":         {"label": "hobby",            "th": "งานอดิเรก",     "baseline": False,
                      "needs": "a hobby surface + its storage (task-specific)", "zone": "a flex / dedicated corner",
                      "adjacency": "task-specific (light for craft, quiet for music, …)"},
}
BASELINE_ACTIVITIES = frozenset(a for a, v in ACTIVITIES.items() if v["baseline"])
LIFESTYLE_ACTIVITIES = frozenset(a for a, v in ACTIVITIES.items() if not v["baseline"])


# --------------------------------------------------------------------------- #
# (2) kind -> [activity]  (built ON TOP of placement_logic's kind role-sets)   #
# --------------------------------------------------------------------------- #
def _build_kind_activity():
    m = {}

    def add(kinds, *acts):
        for k in kinds:
            m.setdefault(k, [])
            for a in acts:
                if a not in m[k]:
                    m[k].append(a)

    # sleep — reuse BED_KINDS; extend with the sleep-zone built-ins
    add(PL.BED_KINDS, "sleep")
    add({"headboard", "platform", "nightstand"}, "sleep")
    # relax / lounge / TV — reuse the seating + focal + TV families. Lounge seating and a
    # social surface also host guests, so they serve `entertain` too (a home supports
    # entertaining when it has seating + a lounge/dining surface — a GAP only when it has
    # neither). This keeps `entertain` from being a false gap on any furnished living room.
    add(PL.SEATING_KINDS, "relax", "entertain")          # sofa/loveseat/armchair/…: lounge + guests
    add(PL.CONVERSATION_FOCAL_KINDS, "relax", "entertain")  # coffee_table / round_table
    add({"rug"}, "relax")
    add(PL.TV_STANDALONE_KINDS | PL.TV_FUSED_KINDS, "relax")
    # a fused headboard_tv is both a sleep built-in and a screen
    add({"headboard_tv"}, "sleep", "relax")
    # dine — dining set (also hosts guests) + sideboard (also stores)
    add({"dining_table", "dining_chair"}, "dine", "entertain")
    add({"sideboard"}, "dine", "store")
    # groom / bathe — reuse the bathroom families
    add(PL.BATH_BASIN_KINDS | PL.BATH_WC_KINDS, "groom")
    add(PL.BATH_WET_KINDS, "bathe")
    add({"vanity"}, "groom")                             # a bedroom vanity = grooming
    # store / dress
    add({"wardrobe"}, "dress_store")
    add({"cabinet"}, "store")
    # work
    add({"desk"}, "work")
    return m


KIND_ACTIVITY = _build_kind_activity()

# Polymorphic kinds we deliberately leave UNMAPPED (bar? vanity? kids? dine? work?): they
# stay AMBIGUOUS unless the spec carries a `serves` tag or the name signals intent. Listed
# explicitly so the checker can say "ambiguous, tag serves" instead of "unknown kind".
# (`chair` is NOT here — placement_logic.SEATING_KINDS already types it as lounge seating,
# so KIND_ACTIVITY maps chair->relax; a dining use is recovered from the name signal.)
POLYMORPHIC_KINDS = frozenset({"stool", "table", "bench", "side_table", "end_table"})


# --------------------------------------------------------------------------- #
# (3) SOFT name signals — a Thai/English keyword in the free-text name that     #
#     hints an activity the kind can't express (a "reading chair" is an         #
#     armchair by kind but a READING seat by intent). Never decisive.          #
# --------------------------------------------------------------------------- #
NAME_SIGNALS = {
    "read":          re.compile(r"อ่าน|หนังสือ|\bread(ing)?\b|\bbook", re.I),
    "work":          re.compile(r"ทำงาน|โต๊ะทำงาน|\bwork\b|\bdesk\b|\boffice\b|\bstudy\b", re.I),
    "coffee_ritual": re.compile(r"กาแฟ|ชายามเช้า|\bcoffee\b|\btea\b|ระเบียง|\bbalcon", re.I),
    "groom":         re.compile(r"เครื่องแป้ง|แต่งหน้า|โต๊ะเครื่องแป้ง|\bvanity\b|\bmakeup\b|dressing table", re.I),
    "exercise":      re.compile(r"ออกกำลัง|โยคะ|\byoga\b|\bexercise\b|\bgym\b|ฟิตเนส", re.I),
    "dine":          re.compile(r"ทานข้าว|โต๊ะอาหาร|\bdining\b|\bdinner\b", re.I),
    "hobby":         re.compile(r"เปียโน|\bpiano\b|งานอดิเรก|\bhobby\b|\beasel\b|\bcraft\b", re.I),
    "sleep":         re.compile(r"เตียง|หัวเตียง|\bbed\b", re.I),
}


def _name_activities(name):
    n = str(name or "")
    return [a for a, rx in NAME_SIGNALS.items() if rx.search(n)]


# --------------------------------------------------------------------------- #
# Public: what activities does ONE element serve, and how confident are we?     #
# --------------------------------------------------------------------------- #
def element_activities(el):
    """-> {"activities": [ids], "source": <serves|kind|name|kind+name|ambiguous>,
           "detail": <human note>}.

    Precedence: an explicit `serves` tag WINS (author-declared). Otherwise we UNION the
    kind-default (deterministic) with any name signal (soft) — a reading armchair serves
    BOTH relax (kind) and read (name). A polymorphic/unknown kind with neither -> AMBIGUOUS
    (activities [], flagged, never guessed). Degrades on any malformed element, never throws."""
    try:
        kind = str(el.get("kind", "") or "").strip()
        name = el.get("name", "")

        # (a) explicit serves tag — the un-inferable cases the taxonomy can't reach
        carry = ""
        serves = el.get("serves")
        if serves:
            requested = [serves] if isinstance(serves, str) else list(serves)
            acts = [a for a in requested if a in ACTIVITIES]
            bad = [a for a in requested if a not in ACTIVITIES]
            note = "author-declared via `serves`"
            if bad:
                note += f" (ignored unknown activity {bad})"
            if acts:
                return {"activities": acts, "source": "serves", "detail": note}
            # serves present but ALL entries unknown -> fall through to inference, but SURFACE
            # the typo (never silently swallow it — flag-never-guess).
            if bad:
                carry = f"; unknown `serves` {bad} ignored — check for a typo"

        kind_acts = list(KIND_ACTIVITY.get(kind, []))
        name_acts = _name_activities(name)

        if kind_acts and name_acts:
            merged = kind_acts + [a for a in name_acts if a not in kind_acts]
            return {"activities": merged, "source": "kind+name",
                    "detail": f"kind '{kind}' -> {kind_acts}; name signal -> {name_acts}{carry}"}
        if kind_acts:
            return {"activities": kind_acts, "source": "kind", "detail": f"kind '{kind}'{carry}"}
        if name_acts:
            return {"activities": name_acts, "source": "name",
                    "detail": f"kind '{kind}' is unmapped; name signals {name_acts} (SOFT){carry}"}

        why = ("polymorphic kind — dine/work/accent are all possible"
               if kind in POLYMORPHIC_KINDS else f"kind '{kind}' has no activity mapping")
        return {"activities": [], "source": "ambiguous",
                "detail": f"{why}; add a `serves` tag to declare intent{carry}"}
    except Exception as e:   # a malformed element must never break the layer
        return {"activities": [], "source": "ambiguous", "detail": f"unreadable element ({type(e).__name__})"}


def requirement_for(activity):
    """The program-of-requirements row for an activity id, or None if unknown."""
    v = ACTIVITIES.get(activity)
    if not v:
        return None
    return {"activity": activity, "label": v["label"], "th": v["th"], "baseline": v["baseline"],
            "needs": v["needs"], "zone": v["zone"], "adjacency": v["adjacency"], "cite": CITE_PROGRAMMING}


def kinds_serving(activity):
    """Every kind whose default mapping serves `activity` — the inverse of KIND_ACTIVITY
    (used to phrase a GAP: 'no <kinds> present')."""
    return sorted(k for k, acts in KIND_ACTIVITY.items() if activity in acts)


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("ACTIVITIES (baseline*):")
    for a, v in ACTIVITIES.items():
        print(f"  {'*' if v['baseline'] else ' '} {a:14s} {v['th']:12s} needs: {v['needs']}")
    print("\nKIND -> ACTIVITY:")
    for k in sorted(KIND_ACTIVITY):
        print(f"  {k:16s} -> {KIND_ACTIVITY[k]}")
    print(f"\npolymorphic (ambiguous unless tagged): {sorted(POLYMORPHIC_KINDS)}")
