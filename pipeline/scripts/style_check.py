#!/usr/bin/env python3
"""A STYLE IS NINE ROWS, NOT A NAME — `qa/style-of-record.json`.

WHAT PRODUCED IT (2026-08-23, owner: *"ต้องเลือกก่อนว่าห้องนี้จะเป็นสไตล์ไหน
แล้วค่อยเอาของมาเติม"*, then *"ทำตัวเป็น project director และวางแผนแก้ปัญหานี้
ระยะยาว"*). He was right, and the repo's own contract already said so —
`03_layout/_contract.md` names `02_concept/concept.md` as input #1 to the stage
that selects furniture. The audit that followed found the same shape DRW found
on 2026-08-11 and recorded in the plan: **not a missing capability, a missing
wire.**

  * `02_concept/concept.md` declares a style, a 60/30/10 palette and seven EDGE
    prohibitions. No `.py` and no `.json` in this repo names that file.
  * `style_fingerprint.py` MEASURES a 60/30/10 palette split from pixels. It
    has zero production consumers. The declaration and the instrument that
    could check it were built seven weeks apart in the same repo and were never
    introduced.
  * `build_room._suite_materials` exposes NINE spec-addressable material roles
    (`material_presets.ALLOWED_SURFACES` + `ALLOWED_FAMILIES`). The canonical
    spec fills THREE. The other six fall through to module constants — the
    floor among them, which is the largest surface in every frame and
    concept.md's declared 60% dominant.
  * One constant, `FLOOR_SLUG = "wood_floor"`, is the floor AND the "walnut"
    feature wall AND the wood on every loose item (build_room.py:4572/4576/
    4589). One parameter carrying three things.
  * Six style NAMES were in force at once, and the one sitting in the files
    code actually reads ("Japandi", `qa/blenderkit-month-classes.json`
    `_pass_rule`) entered the repo as a blind critic's DESCRIPTION OF OUR OWN
    RENDER on 2026-08-11 and hardened into the criterion that selects what we
    buy next. A room cannot be styled by a summary of its own pixels.
  * The client never gave a style at all (`brief.json`
    `style_direction_hint: null`). Every name is studio-invented, so the one in
    force must at least be DECIDED rather than inherited.

THE LAW THIS FILE INSTALLS: a room has ONE style name; that name carries a
decision row; and the name governs nothing until all NINE material slots are
either SIGNED to a preset or recorded `legacy-unsigned` with a date and a named
restart action. A prohibition with no test is prose. A style derived from our
own render is refused by name.

THREE STATES AND NO FOURTH, per R13: signed / legacy-unsigned (loud, dated,
with `restart_by`) — silence is not a state. A machine that hard-fails every
existing slot on day one gets switched off and joins the dead queues this file
exists to stop, so the unsigned slots are DECLARED, not failed.

NOTHING HERE BLOCKS ON THE OWNER (R3). Every violation is on the builder's
side. He overrules the style from the image at any time, and an overruled style
locks to him.

LAYER LAW: pure Python — no `bpy`, no PIL, no network. It imports
`material_presets` and `material_defaults`, both pure stdlib by construction.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STYLE_REL = "qa/style-of-record.json"

SLOT_STATES = ("signed", "legacy-unsigned")
DECIDERS = ("builder", "owner")
REQUIRED_STYLE = ("name", "decided_by", "decision_row", "date", "derived_from")
REQUIRED_SLOT = ("slot", "kind", "status")
REQUIRED_EDGE = ("id", "rule", "source", "test")

# A style may never be a restatement of our own output. These are refused BY
# NAME in `derived_from` for the reason the Japandi row was written: a critic
# describing our render, promoted to the rule that picks the next purchase, is
# a closed loop that can only ratify what we already built.
SELF_DERIVED = ("our_own_render", "critic_description", "our own render",
                "own_render", "self")

# A prohibition needs a way to be wrong. "none" is refused by name for the same
# reason `pending` is refused in the decision register.
EDGE_TESTS = ("preset-vocabulary", "light-table", "spec-key", "panel",
              "pixel", "none-yet")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def load(path=None, repo_root=None):
    p = path or os.path.join(repo_root or _repo_root(), STYLE_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def slots(data):
    rows = (data or {}).get("slots")
    return [s for s in rows if isinstance(s, dict)] if isinstance(rows, list) else []


def edges(data):
    rows = (data or {}).get("edges")
    return [e for e in rows if isinstance(e, dict)] if isinstance(rows, list) else []


def _vocab():
    """(preset keys, allowed surfaces, allowed families) read from the LIVE
    preset library — never a list typed here, so the two cannot drift."""
    try:
        import material_presets as MP
        return (set(MP.PRESETS), tuple(MP.ALLOWED_SURFACES),
                tuple(MP.ALLOWED_FAMILIES))
    except Exception:
        return None, (), ()


def _age_days(iso, today=None):
    try:
        return ((today or datetime.date.today())
                - datetime.date.fromisoformat(str(iso))).days
    except (ValueError, TypeError):
        return None


def _spec_selection(spec):
    """{slot: preset} the SPEC actually carries, flattening surfaces+families."""
    mats = (spec or {}).get("materials") or {}
    out = {}
    for key in ("surfaces", "families"):
        blk = mats.get(key)
        if isinstance(blk, dict):
            for k, val in blk.items():
                if isinstance(val, str) and val:
                    out[k] = val
    return out


def check(data, repo_root=None, spec=None, today=None, path_hint=STYLE_REL):
    """Violations, all on the builder's side. Returns [] when the register
    tells the truth about what renders today."""
    if data is None:
        return [f"no readable style register at {path_hint}. Style was prose "
                f"with zero consumers for seven weeks; losing this file puts "
                f"it back there, and the drift back to invisible."]

    root = repo_root or _repo_root()
    presets, allowed_surf, allowed_fam = _vocab()
    v = []

    # ---- the style itself -------------------------------------------------
    st = data.get("style")
    if not isinstance(st, dict):
        v.append("the register carries no `style` object. A room with no named "
                 "style selects objects by whatever word the last critic used.")
        st = {}

    missing = [k for k in REQUIRED_STYLE if not st.get(k)]
    if missing:
        v.append(f"style is missing {', '.join(missing)}.")

    if st.get("decided_by") and st["decided_by"] not in DECIDERS:
        v.append(f"style decided_by {st['decided_by']!r} is not one of "
                 f"{', '.join(DECIDERS)}. There is no pending state — somebody "
                 f"chose this style or it was never chosen.")
    if st.get("owner_override") and st.get("decided_by") != "owner":
        v.append("style carries an owner_override but is still labelled the "
                 "builder's call. Once his words are in the row it is his "
                 "(decisions_check rule 4, applied to style).")

    der = str(st.get("derived_from") or "").strip().lower()
    if der in SELF_DERIVED:
        v.append(f"style derived_from {st.get('derived_from')!r} — REFUSED BY "
                 f"NAME. 'Japandi' entered this repo on 2026-08-11 as a blind "
                 f"critic's description of our own render and became the rule "
                 f"that picks what we buy. A style read off our own pixels can "
                 f"only ratify what we already built.")

    v += retired_name_hits(data, root)

    # ---- the nine slots ---------------------------------------------------
    rows = slots(data)

    # THE RATCHET. Rule "spec agrees with register" below compares two files the
    # builder wrote in the same commit — `qa/coverage-map.json` calls that class
    # 'a', self-consistency, and it is the class D-112 was written about. A
    # count that may only fall is not self-consistency: it cannot be satisfied
    # by editing both sides to agree.
    ceil_ = data.get("_unsigned_ceiling")
    unsigned_now = len([s for s in rows
                        if s.get("status") == "legacy-unsigned"])
    if isinstance(ceil_, int) and unsigned_now > ceil_:
        v.append(f"{unsigned_now} slots are legacy-unsigned against a ceiling "
                 f"of {ceil_}. THE CEILING ONLY EVER FALLS. A slot may be "
                 f"signed, never un-signed, and a new addressable role arrives "
                 f"signed or the ceiling rises by a decision row — not by an "
                 f"edit.")

    floor = data.get("_slot_floor")
    if isinstance(floor, int) and len(rows) < floor:
        v.append(f"the register holds {len(rows)} slots against a floor of "
                 f"{floor}. A SLOT DOES NOT LEAVE THIS FILE — it is signed or "
                 f"declared legacy-unsigned, and the row stays. Deleting one "
                 f"restores exactly the silence this file replaces.")

    if presets is None:
        v.append("material_presets is not importable, so no slot preset can be "
                 "validated — refusing to call this register checked.")

    named = set()
    for s in rows:
        sid = s.get("slot") or "<no slot>"
        if sid in named:
            v.append(f"{sid}: duplicate slot row.")
        named.add(sid)

        miss = [k for k in REQUIRED_SLOT if not s.get(k)]
        if miss:
            v.append(f"{sid}: slot row is missing {', '.join(miss)}.")
            continue

        if s.get("kind") not in ("surface", "family"):
            v.append(f"{sid}: kind {s.get('kind')!r} is not surface|family.")

        stt = s.get("status")
        if stt not in SLOT_STATES:
            v.append(f"{sid}: status {stt!r} is not one of "
                     f"{', '.join(SLOT_STATES)}. The third state would be "
                     f"silence, and silence is what this file replaces.")
            continue

        if stt == "signed":
            pk = s.get("preset")
            if not pk:
                v.append(f"{sid} is signed with no preset.")
            elif presets is not None and pk not in presets:
                v.append(f"{sid}: preset {pk!r} is not in the live preset "
                         f"library. A signature naming a material that cannot "
                         f"be built is not a signature.")
            if not s.get("signed_where"):
                v.append(f"{sid} is signed with no signed_where.")
            for rel in str(s.get("signed_where") or "").split(","):
                rel = rel.strip()
                if rel and not os.path.exists(
                        os.path.join(root, rel.replace("/", os.sep))):
                    v.append(f"{sid}: signed_where names {rel}, which does not "
                             f"exist. R10's test applied to a signature: a "
                             f"decision in force nowhere was never taken.")
        else:
            if not s.get("since"):
                v.append(f"{sid} is legacy-unsigned with no `since`. An "
                         f"unsigned slot must print its own age — that age is "
                         f"the metric, exactly as it is for an open ask.")
            if not s.get("restart_by"):
                v.append(f"{sid} is legacy-unsigned with no `restart_by`. "
                         f"Unsigned is allowed; unsigned with nobody named to "
                         f"end it is the debt going quiet.")
            if not s.get("renders_as"):
                v.append(f"{sid} is legacy-unsigned and does not say what it "
                         f"RENDERS AS today. An unsigned slot that will not "
                         f"state its own value is not declared, it is hidden.")

    # every role the builder can actually address must have a row
    if allowed_surf or allowed_fam:
        want = {k: "surface" for k in allowed_surf}
        want.update({k: "family" for k in allowed_fam})
        for slot_name, kind in sorted(want.items()):
            if slot_name not in named:
                v.append(f"{slot_name}: the build exposes this {kind} slot and "
                         f"the register has no row for it. An addressable slot "
                         f"with no row is exactly how the floor came to be "
                         f"unsigned for seven weeks.")
        for extra in sorted(named - set(want)):
            v.append(f"{extra}: the register names a slot the build cannot "
                     f"address. A row nothing consumes is the defect this "
                     f"register exists to stop.")

    # ---- the spec must agree with the register ----------------------------
    if spec is not None:
        sel = _spec_selection(spec)
        by_slot = {s.get("slot"): s for s in rows}
        for slot_name, preset in sorted(sel.items()):
            row = by_slot.get(slot_name)
            if row is None:
                v.append(f"{slot_name}: the spec selects {preset!r} and the "
                         f"register has no row for it.")
            elif row.get("status") != "signed":
                v.append(f"{slot_name}: the spec selects {preset!r} but the "
                         f"register calls the slot {row.get('status')!r}. The "
                         f"register must describe what renders, not what we "
                         f"meant.")
            elif row.get("preset") != preset:
                v.append(f"{slot_name}: the spec renders {preset!r}, the "
                         f"register signs {row.get('preset')!r}. The spec is "
                         f"what renders — reopen the register, never the "
                         f"frame.")
        for slot_name, row in sorted(by_slot.items()):
            if row.get("status") == "signed" and slot_name not in sel:
                v.append(f"{slot_name}: the register signs "
                         f"{row.get('preset')!r} and the spec selects nothing, "
                         f"so the build renders the legacy constant. A "
                         f"signature the renderer never reads is prose.")

    # ---- the one rule that opens the picture (R11) -------------------------
    v += palette_gap(data, today=today)

    # ---- the client-facing description must not contradict a signature ----
    v += client_description(data, rows)

    # ---- the prohibitions -------------------------------------------------
    seen_edges = set()
    for e in edges(data):
        eid = e.get("id") or "<no id>"
        if eid in seen_edges:
            v.append(f"{eid}: duplicate edge id.")
        seen_edges.add(eid)
        miss = [k for k in REQUIRED_EDGE if not e.get(k)]
        if miss:
            v.append(f"{eid}: edge is missing {', '.join(miss)}.")
            continue
        t = e.get("test")
        if t not in EDGE_TESTS:
            v.append(f"{eid}: test {t!r} is not one of {', '.join(EDGE_TESTS)}. "
                     f"A prohibition with no way to be wrong is prose, and "
                     f"concept.md's seven EDGE rules sat as prose for seven "
                     f"weeks while one of them (no velvet — humidity) shipped "
                     f"a live preset with nothing in its way.")
        if t == "none-yet" and not e.get("restart_by"):
            v.append(f"{eid}: test is none-yet with no restart_by. Admitting a "
                     f"prohibition cannot be tested today is honest; leaving "
                     f"nobody named to make it testable is the queue going "
                     f"quiet.")
        for rel in str(e.get("source") or "").split(","):
            rel = rel.split(":")[0].strip()
            if rel and "/" in rel and not os.path.exists(
                    os.path.join(root, rel.replace("/", os.sep))):
                v.append(f"{eid}: source names {rel}, which does not exist.")
    return v


WALK_DIRS = ("qa", "pipeline/scripts", "pipeline/prompts")
WALK_EXT = (".json", ".py", ".md", ".yaml", ".yml")


def retired_name_hits(data, repo_root=None):
    """A retired style name may not survive ANYWHERE the machine reads.

    The first version of this rule grepped a NAMED list of four files. That is
    the construction R9b forbids in its own words — "a rule that names the
    objects it applies to will always exempt the next one" — and the two guards
    it replaced there covered 2 classes out of 5. The sixth style name will be
    typed into a fifth file. So this walks the trees the machine reads and
    fails on EVERY hit that is not acknowledged in `name_debt` with a `since`
    and a `restart_by`. Acknowledging is cheap and dated; exempting is not
    available."""
    root = repo_root or _repo_root()
    st = (data or {}).get("style") or {}
    retired = [str(n) for n in (st.get("retired_names") or []) if n]
    if not retired:
        return []
    debts = data.get("name_debt")
    debts = debts if isinstance(debts, dict) else {}
    own = os.path.relpath(os.path.abspath(__file__), root).replace(os.sep, "/")
    v, hits = [], {}
    for d in WALK_DIRS:
        base = os.path.join(root, d.replace("/", os.sep))
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "__pycache__", "node_modules")]
            for fn in filenames:
                if not fn.endswith(WALK_EXT):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, root).replace(os.sep, "/")
                # SCOPE DERIVED FROM THE PREMISE, never chosen to silence a
                # false positive (R9b's own distinction). The premise is "a
                # retired name must not be live in anything that SELECTS". The
                # register names its own retired list; this module names them to
                # refuse them; a test names the thing it tests. None of the
                # three can select an object. Every other file in these trees is
                # in scope, including ones nobody has written yet.
                if rel == own or rel == STYLE_REL or fn.startswith("test_"):
                    continue
                try:
                    with open(fp, encoding="utf-8") as f:
                        body = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                low = body.lower()
                for name in retired:
                    if name.lower() in low:
                        hits.setdefault(name, []).append(rel)
    for name, where in sorted(hits.items()):
        d = debts.get(name)
        acked = (isinstance(d, dict) and d.get("since") and d.get("restart_by"))
        known = set(str(d.get("where_seen") or "").split(",")) if acked else set()
        known = {w.strip() for w in known if w.strip()}
        fresh = [w for w in where if w not in known]
        if not acked:
            v.append(f"retired style name {name!r} still appears in "
                     f"{len(where)} file(s) the machine reads "
                     f"({', '.join(sorted(where)[:4])}"
                     f"{' …' if len(where) > 4 else ''}) and is not "
                     f"acknowledged in `name_debt` with a `since` and a "
                     f"`restart_by`. A name retired in one file and live in "
                     f"another is how six names came to be in force at once.")
        elif fresh:
            v.append(f"retired style name {name!r} has appeared in "
                     f"{len(fresh)} NEW file(s) since it was acknowledged "
                     f"({', '.join(sorted(fresh)[:4])}"
                     f"{' …' if len(fresh) > 4 else ''}). The debt is dated and "
                     f"allowed to exist; it is not allowed to SPREAD.")
    return v


def palette_gap(data, today=None):
    """R11 APPLIED TO STYLE: this register must OPEN THE PICTURE.

    Everything else in this file reads JSON and greps text — declarations
    about the room, every one of which can go green while the frame gets
    worse. That is the exact shape R11 was written to end, and a style rung
    is the last place it should be tolerated, because style is a thing you can
    only see.

    The repo already owned the instrument and never wired it:
    `style_fingerprint.py` measures the 60/30/10 dominant/secondary/accent area
    split, warmth and chromatic-mono concentration FROM PIXELS, is tested,
    runs local-only with no egress — and had ZERO non-test consumers for seven
    weeks, sitting beside a concept document that declares a 60/30/10 palette.

    It needs PIL + numpy + sklearn, so it is run OUT OF PROCESS by
    `style_measure.py` and its numbers are stored here — the same layer law
    `pixel_check` follows, and for the same reason: a rules module must not
    import an image library.

    THREE STATES, and the middle one is the point. A gap this wide on day one
    cannot be a hard failure (the frame measures 0.30 dominant against a
    declared 0.60 and always has), because a machine that fails everything on
    day one gets switched off. So the GAP is declared and dated; what fails is
    NOT HAVING LOOKED — no measurement, or a measurement of a frame that is no
    longer the frame of record — and the gap WIDENING. "Could not look" must
    never print like "looked and it was fine"."""
    m = data.get("palette_measured")
    if not isinstance(m, dict):
        return ["the register declares a palette and carries no measurement of "
                "the frame. R11: a style rung that never opens the picture is "
                "the defect it exists to catch. Run "
                "`python pipeline/scripts/style_measure.py <frame>`."]
    v = []
    for k in ("frame", "measured_at", "dominant_share", "secondary_share",
              "accent_share", "declared"):
        if m.get(k) is None:
            v.append(f"palette_measured is missing `{k}`.")
    if v:
        return v
    if m.get("could_not_run"):
        return [f"palette measurement COULD NOT RUN on {m.get('frame')}: "
                f"{m.get('could_not_run')}. Exit 2 is not a pass — "
                f"\"could not look\" must never print like \"looked and it was "
                f"fine\"."]

    root = _repo_root()
    frame = str(m.get("frame"))
    if not os.path.exists(os.path.join(root, frame.replace("/", os.sep))):
        v.append(f"palette_measured names frame {frame}, which does not exist. "
                 f"A measurement of a frame nobody can open was never made.")

    decl = m.get("declared") or {}
    gap = {}
    for key, dk in (("dominant_share", "dominant"),
                    ("secondary_share", "secondary"),
                    ("accent_share", "accent")):
        try:
            gap[dk] = round(float(m[key]) - float(decl[dk]), 4)
        except (KeyError, TypeError, ValueError):
            v.append(f"palette_measured cannot be compared on {dk}.")
    if v:
        return v

    worst = max(abs(x) for x in gap.values())
    ceil_ = m.get("gap_ceiling")
    if not isinstance(ceil_, (int, float)):
        v.append("palette_measured carries no `gap_ceiling`. The gap is "
                 "allowed to be wide and dated; it is not allowed to be "
                 "unbounded, because an unbounded gap is a number nobody can "
                 "fail.")
    elif worst > ceil_ + 1e-9:
        v.append(f"the frame's palette is {worst:.3f} from the declared "
                 f"60/30/10 against a ceiling of {ceil_:.3f} — measured "
                 f"dominant {m['dominant_share']:.3f} / secondary "
                 f"{m['secondary_share']:.3f} / accent {m['accent_share']:.3f} "
                 f"on {frame}. THE CEILING ONLY EVER FALLS. This is the one "
                 f"rule here that read pixels, and it is the one that says the "
                 f"room drifted.")
    if not m.get("gap_since"):
        v.append("palette_measured records a gap with no `gap_since`. An "
                 "unclosed gap must print its own age.")
    if not m.get("close_by"):
        v.append("palette_measured records a gap with no `close_by`. A gap "
                 "with nobody named to close it is the debt going quiet.")
    return v


def client_description(data, rows=None):
    """A SIGNED slot that `material_defaults` still describes as the legacy
    material means the CLIENT is handed a material list the render contradicts.

    This is not hypothetical. `rationale.py:223` says in its own comment "today
    the spec carries NO material field and build_room ignores the spec anyway";
    the spec grew that block on 2026-07-14 and build_room has read it since
    (build_room.py:4558). So the deliverable tells the client the feature wall
    is walnut while the render builds the owner-signed oak, and
    `test_rationale` stays green because it drift-guards those strings against
    build_room's SOURCE, which still contains the legacy names — a
    self-consistency check that can prove the build correct and never notice
    the description is wrong.

    Acknowledged debt prints loudly and does not fail (R13's third state);
    UNacknowledged contradiction fails."""
    rows = slots(data) if rows is None else rows
    try:
        import material_defaults as MD
    except Exception as exc:                                # pragma: no cover
        return [f"material_defaults is not importable ({exc}); the "
                f"client-facing material description cannot be checked."]

    pairs = {"walls": MD.WALL_MATERIAL,
             "feature_wall": MD.FEATURE_WALL_MATERIAL,
             "floor": MD.FLOOR_MATERIAL,
             "fixtures": MD.FIXTURE_MATERIAL,
             "fabric": MD.FABRIC_MATERIAL,
             "wood": MD.WOODEN_MATERIAL,
             "neutral": MD.NEUTRAL_MATERIAL,
             "millwork": MD.BUILTIN_MATERIAL}
    ack = data.get("client_description_debt")
    ack = ack if isinstance(ack, dict) else {}
    v = []
    for s in rows:
        if s.get("status") != "signed":
            continue
        name = s.get("slot")
        if name not in pairs:
            continue
        human, slug = pairs[name]
        preset = s.get("preset") or ""
        stem = preset.split("_")[0]
        if stem and (stem in slug or stem in human.lower()):
            continue                      # the description still names it
        row = ack.get(name)
        if not isinstance(row, dict) or not row.get("since") \
                or not row.get("restart_by"):
            v.append(f"{name}: signed to {preset!r} while material_defaults "
                     f"still describes it to the CLIENT as {human!r} "
                     f"(slug {slug!r}), and the contradiction is not "
                     f"acknowledged in `client_description_debt` with a "
                     f"`since` date and a `restart_by`. rationale.py ships "
                     f"that string in the client package.")
    return v


# ---------------------------------------------------------------- reporting --
def summary(data, today=None):
    rows = slots(data)
    signed = [s for s in rows if s.get("status") == "signed"]
    un = [s for s in rows if s.get("status") == "legacy-unsigned"]
    ages = [a for a in (_age_days(s.get("since"), today) for s in un)
            if a is not None]
    st = (data or {}).get("style") or {}
    return {"style": st.get("name"), "decided_by": st.get("decided_by"),
            "signed": len(signed), "unsigned": len(un), "slots": len(rows),
            "oldest_unsigned_days": max(ages) if ages else None,
            "edges": len(edges(data)),
            "edges_untestable": len([e for e in edges(data)
                                     if e.get("test") == "none-yet"])}


def one_line(data, today=None):
    s = summary(data, today)
    if not s["slots"]:
        return "STYLE: no register"
    age = ("" if s["oldest_unsigned_days"] is None
           else f", oldest {s['oldest_unsigned_days']}d")
    return (f"STYLE: {s['style']} ({s['decided_by']}) | "
            f"{s['signed']}/{s['slots']} slots signed | "
            f"{s['unsigned']} legacy-unsigned{age} | "
            f"{s['edges']} edges, {s['edges_untestable']} not yet testable")


def style_lines(data=None, repo_root=None, today=None):
    """The session-open / render-path block. Never raises."""
    data = data if data is not None else load(repo_root=repo_root)
    if data is None:
        return ["", f"STYLE: no readable register at {STYLE_REL}"]
    out = ["", one_line(data, today)]
    for s in slots(data):
        if s.get("status") != "legacy-unsigned":
            continue
        age = _age_days(s.get("since"), today)
        aged = f"{age}d" if age is not None else "?d"
        out.append(f"  unsigned {str(s.get('slot')):<12} {aged:>5}  "
                   f"renders as {s.get('renders_as')} — {s.get('restart_by')}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--register", default=None)
    ap.add_argument("--spec", default=None,
                    help="canonical spec to cross-check against the register")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    data = load(a.register)
    spec = None
    if a.spec:
        try:
            with open(a.spec, encoding="utf-8") as f:
                spec = json.load(f)
        except (OSError, ValueError) as exc:
            print(f"COULD NOT READ SPEC {a.spec}: {exc}")
            return 2
    v = check(data, spec=spec)
    if a.json:
        print(json.dumps({"violations": v, "summary": summary(data)},
                         ensure_ascii=False, indent=1))
    else:
        for ln in style_lines(data):
            print(ln)
        for x in v:
            print(f"  VIOLATION: {x}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
