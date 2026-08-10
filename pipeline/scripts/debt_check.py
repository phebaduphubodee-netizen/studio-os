#!/usr/bin/env python3
"""debt_check.py — a critic item closes through a DOOR THAT IS A PROGRAM, never
through a sentence. PURE python (no bpy, no network).

    python pipeline/scripts/debt_check.py                    # the ledger's own honesty
    python pipeline/scripts/debt_check.py --scene <dump.json> --frame <r.png> --spec <s.json>
    python pipeline/scripts/debt_check.py --spec <spec.json>  # a spec alone cannot discharge

WHAT EARNED IT, AS A COUNT
--------------------------
Measured 2026-08-09, and it is one of three measurements of the same defect taken
that day: **357 critic items filed / ~22 built · ~61 DR units / 39 write-only ·
21 gate artifacts / 2 with an owner verdict.** Every one is a queue whose consumer
never visits it. The critic queue is the largest of the three, and it is the one
with a rule already written against it: R7 says EVERY critic item gets a written
triage — accept and lane it, or refute it WITH A MEASUREMENT. What R7 never had
was a consumer. An item was "accepted" in a gate artifact and the gate artifact
was the last place it was ever seen.

The proof that this is not paperwork: the same defect classes come back on frame
after frame from critics who cannot see each other's answers. Cloth stiffness was
filed in every one of the 28 TRN-002 answer files. Faceting and flat light in 26
of 28. Those are not new findings each round; they are one debt, re-billed 28
times, against a lane that closed 22 items in 40 rounds.

THE ONE RULE, AND WHY IT IS SHAPED THIS WAY
-------------------------------------------
    AN ITEM CLOSES ONLY WHEN ITS DOOR RESOLVES AGAINST SOMETHING BUILT,
    OR IT IS REFUTED WITH A NUMBER.

`closes_when` names the door. Every door is an instrument that already exists and
that can FAIL:

  object      the object is in the BUILT SCENE — matched against a placement dump,
              not against a spec. For debts that are genuine ABSENCES (no bedside
              lamp, no styling, no curtain).
  image_row   a row of `qa/deliverable-standard.json` passes on the RENDERED FRAME.
              D1-D6 and D10, whose thresholds are percentiles of 658 delivered
              renders — the one set of numbers in this repo the builder cannot
              quietly move. This door OPENS THE PICTURE (R11).
  scene_row   D7/D8/D9, which read the built model rather than pixels: styling
              count, R8-ACQUIRE-class objects built as primitives, curved forms
              rendering flat-shaded.
  guard       an existing guard's verdict on the BUILT SCENE — today
              `placement_check`'s FLOATING / OVERHANG / OFF-AXIS, read off a
              placement dump. "The stool's legs stop short of the seat" and "the
              timber run cantilevers and ends in mid-air" are not opinions; they
              are that guard's two FAIL kinds, and it has been able to say so
              since 2026-08-02.
  none_yet    NO INSTRUMENT IN THIS REPO CAN SEE THIS DEFECT. It must name
              `blocked_on` — what would have to be built for it to be resolvable —
              and it may never be marked built or refuted while it says this.

`none_yet` is the honest residue and it is the number worth reading on every run.
SC-6 measured the same shape one level up: a sighted judge named five defects in
our best frame and the image rows can see exactly one of them. A ledger that
pretended every filed item had an instrument behind it would be the flattering
version of this file.

EVIDENCE TIERS — DECLARED IS NEVER CLOSED
------------------------------------------
This is the half that makes the rule bite, and it is R9b's law and R11's in one
sentence: *a spec is what we said, a dump and a frame are what happened.*

    BUILT      a placement dump (object doors) or a rendered frame (image rows).
               A row MAY close on this.
    DECLARED   a spec, and nothing else. Every row resolved this way is reported
               DECLARED-ONLY, which is NOT a pass, and no row may close on it.
    NOT RUN    no evidence was given. NOT RUN IS NEVER PASS — the same contract as
               `deliverable_check` and `pixel_check` exit code 2. "Could not look"
               must never print like "looked and it was fine."

So `--spec <anything>` alone is REFUSED, by name, and that is not a formality: it
is the exact move this ledger exists to stop. The 20 seeded rows crossed out of
TRN-002 as that unit closed, and the plan's own condition says why —
**CLOSING IS NOT DISCHARGING.** A unit may be closed while every defect it was
filed for is still in the frame. Transferring a row records WHERE it will be paid;
it does not pay it.

WHAT THIS CANNOT DO, said before anyone trusts it
--------------------------------------------------
  * It checks the rows that were SEEDED. The seed is the top-20 by recurrence
    across 28 answer files; ~248 accepted-and-unbuilt items are not in it. The
    ledger says so on every run rather than implying the twenty are the whole debt.
  * A door can be satisfied by the wrong fix. D9 goes to zero if every curved mass
    is deleted. The doors are a floor; the critic ladder (R7/R7b/R7c) and the
    owner's eye (R3) stay terminal and this replaces neither.
  * It cannot tell a real refutation from a confident one. It can only insist the
    refutation carries a NUMBER and names a file that exists — R7's rule and R10's
    point-at-it test. A wrong number is still a number, and only a re-measurement
    catches that.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                       # noqa: BLE001
    pass

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER_REL = "qa/critic-debt.json"
PLAN_REL = "qa/deliverable-plan.json"

STATUSES = ("open", "built", "refuted")
DOORS = ("object", "image_row", "scene_row", "guard", "none_yet")

# Guards a `guard` door may name, and the verdicts each can return. Kept as a
# closed list rather than an import-anything hook: a door onto a module that does
# not exist, or onto a verdict that module never emits, is a door onto nothing —
# which is the shape R10 refuses and the shape `decisions_check` refuses.
GUARDS = {"placement_check": ("FLOATING", "OVERHANG", "OFF-AXIS")}

REQUIRED = ("id", "defect", "object", "kind", "filed_in", "recurrence",
            "crosses_into", "due_phase", "closes_when", "status")

# A refutation must carry a MEASUREMENT (R7). The cheapest honest test for "is
# there a number in this sentence" — and it is deliberately cheap, because the
# expensive version (is the number RIGHT) is a re-measurement, not a regex.
HAS_NUMBER = re.compile(r"\d")

IMAGE_ROWS = ("D1", "D2", "D3", "D4", "D5", "D6", "D10")
SCENE_ROWS = ("D7", "D8", "D9")


# ------------------------------------------------------------------- loading --

def load(path=None, repo_root=None):
    """The ledger, or None. Never raises: a malformed ledger in a gate path must
    become a violation that NAMES the file, not a traceback. `decisions_check`
    learned this the same way — a crash reads as a broken tool and gets worked
    around; a violation gets fixed."""
    p = path or os.path.join(repo_root or REPO, LEDGER_REL)
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def rows(ledger):
    r = ledger.get("rows") if isinstance(ledger, dict) else None
    return [x for x in r if isinstance(x, dict)] if isinstance(r, list) else []


def _d(x):
    """`x` if it is a dict, else {}.

    NOT `(x or {})`, which is what this module shipped first: that idiom defends
    against None and against {} and lets a truthy NON-dict through, so one scalar
    typed where an object belongs raised AttributeError out of the render gate and
    the session opener — a traceback in exactly the two paths `load()` promises
    will produce a named violation instead."""
    return x if isinstance(x, dict) else {}


def _drawable(objs):
    """The objects the RENDERER actually draws, from a placement dump.

    THE ONE POPULATION, and it has to be the same one `placement_check` judges.
    Reading the raw dump instead cost three doors at once: a LIGHT named
    `lamp_glow`, an EMPTY, or a mesh with `hidden_render: true` all satisfied "the
    object is in the built scene" while contributing nothing to the frame and
    while `placement_check` — which filters them — never examined them. So HIDING
    a mass closed its debt, and an absence door could be paid by something no
    viewer can see."""
    out = []
    for o in objs or []:
        if not isinstance(o, dict):
            continue
        if o.get("type") != "MESH" or o.get("hidden_render"):
            continue
        if "min" not in o or "max" not in o:
            continue                    # no geometry: nothing to see and nothing to judge
        out.append(o)
    return out


def _current_phase(plan_path=None, repo_root=None):
    """The phase the plan is actually in — the first not marked done. Same rule as
    `plan_status.current`: `current_phase` is a hint, never the authority."""
    p = plan_path or os.path.join(repo_root or REPO, PLAN_REL)
    try:
        with open(p, encoding="utf-8") as f:
            plan = json.load(f)
    except (OSError, ValueError):
        return None
    for ph in plan.get("phases", []):
        if ph.get("status") != "done":
            return ph.get("id")
    return None


def _plan_phases(plan_path=None, repo_root=None):
    """Phase ids in plan order, or [] if the plan cannot be read. Order matters:
    'is this debt due yet' is a comparison of positions, not of strings."""
    p = plan_path or os.path.join(repo_root or REPO, PLAN_REL)
    try:
        with open(p, encoding="utf-8") as f:
            plan = json.load(f)
    except (OSError, ValueError):
        return []
    return [ph.get("id") for ph in plan.get("phases", []) if ph.get("id")]


# ------------------------------------------------------- the ledger's honesty --

def check(ledger, plan_phases=None, repo_root=None, standard=None,
          path_hint=LEDGER_REL):
    """[violation str] — every way the ledger is lying about itself.

    Empty means: every row is well formed, every closed row closed through a door
    with evidence behind it, and every refutation carries a number."""
    if ledger is None:
        return [f"no readable critic-debt ledger at {path_hint}. The ledger is "
                f"the only thing standing between 'accepted' and the 357/22 "
                f"count that produced it — losing it does not discharge the "
                f"debt, it makes it invisible."]

    root = repo_root or REPO
    phases = plan_phases if plan_phases is not None else _plan_phases(repo_root=root)
    std_rows = set(_d(_d(standard).get("rows"))) if standard else None
    v, seen = [], set()

    for n, r in enumerate(rows(ledger)):
        rid = r.get("id") or f"<row {n}, no id>"

        missing = [k for k in REQUIRED if r.get(k) in (None, "", [], {})]
        if missing:
            v.append(f"{rid}: missing {', '.join(missing)}.")

        if rid in seen:
            v.append(f"{rid}: declared twice — two debts with one id means one "
                     f"of them can be paid off by closing the other.")
        seen.add(rid)

        status = r.get("status")
        if status is not None and status not in STATUSES:
            v.append(f"{rid}: `status` is '{status}'. It must be one of "
                     f"{'/'.join(STATUSES)} — there is no fourth value, because "
                     f"a fourth value is where 'accepted' went to die.")

        door_spec = r.get("closes_when")
        door = door_spec.get("door") if isinstance(door_spec, dict) else None
        if door not in DOORS:
            v.append(f"{rid}: `closes_when.door` is {door!r}. It must be one of "
                     f"{'/'.join(DOORS)}. A row with no door is a row that can "
                     f"only be closed by someone saying so.")
        else:
            v += _check_door(rid, door, door_spec, std_rows)

        if r.get("due_phase") and phases and r["due_phase"] not in phases:
            v.append(f"{rid}: due in phase '{r['due_phase']}', which is not a "
                     f"phase of the plan ({'/'.join(phases)}). A debt due in a "
                     f"phase that does not exist is a debt due never.")

        v += _check_recurrence(rid, r.get("recurrence"), ledger)
        v += _check_closure(rid, r, door, root)

    # THE RULE ITSELF, and it lives here rather than in a caller so that every
    # consumer gets it: a `built` row has its own door RE-RUN against its own
    # evidence. Without this the module checked that a file existed and called
    # that a closure.
    v += verify_closures(ledger, root, standard)

    if not phases:
        v.append("the plan could not be read, so no row's `due_phase` could be "
                 "checked and nothing can be DUE. That is unknown, not nothing "
                 "owed — the same distinction the exit codes draw between "
                 "'could not run' and 'fine'.")
    return v


def _check_door(rid, door, spec, std_rows):
    v = []
    if door == "object":
        if not str(spec.get("match", "")).strip():
            v.append(f"{rid}: an `object` door needs `match` — the name to look "
                     f"for in the built scene.")
        mc = spec.get("min_count", 1)
        # `isinstance(True, int)` is True, so `"min_count": true` silently meant 1.
        if not isinstance(mc, int) or isinstance(mc, bool) or mc < 1:
            v.append(f"{rid}: `min_count` must be a positive integer, not {mc!r}.")
        if not str(spec.get("covers", "")).strip():
            v.append(f"{rid}: an `object` door must say what it COVERS. A "
                     f"substring match on a mass name is narrower than the "
                     f"defect a person filed — `match: \"handle\"` was paid by "
                     f"the entrance door's lever while the wardrobe had none.")
    elif door in ("image_row", "scene_row"):
        want = IMAGE_ROWS if door == "image_row" else SCENE_ROWS
        row = spec.get("row")
        if row not in want:
            v.append(f"{rid}: a `{door}` door must name one of {'/'.join(want)}, "
                     f"not {row!r}.")
        elif std_rows is not None and row not in std_rows:
            v.append(f"{rid}: door names standard row {row}, which is not in "
                     f"qa/deliverable-standard.json. A door onto a row that does "
                     f"not exist is R10's test failed by a door.")
    elif door == "guard":
        mod = spec.get("module")
        if mod not in GUARDS:
            v.append(f"{rid}: a `guard` door must name one of "
                     f"{'/'.join(sorted(GUARDS))}, not {mod!r}.")
        elif spec.get("verdict") not in GUARDS[mod]:
            v.append(f"{rid}: {mod} does not emit the verdict "
                     f"{spec.get('verdict')!r} — it emits "
                     f"{'/'.join(GUARDS[mod])}. A door onto a verdict a guard "
                     f"never returns can never close and never fail.")
        if not str(spec.get("covers", "")).strip():
            v.append(f"{rid}: a `guard` door must say what the guard COVERS. A "
                     f"guard verdict is always narrower than the defect a person "
                     f"filed, and a clean sheet that prints without its scope "
                     f"reads as the whole defect being gone.")
    elif door == "none_yet":
        if not str(spec.get("blocked_on", "")).strip():
            v.append(f"{rid}: a `none_yet` door must name `blocked_on` — what "
                     f"would have to be built for this defect to be measurable. "
                     f"Without it, 'no instrument can see it' is the escape "
                     f"hatch every row eventually takes.")
    return v


def _check_recurrence(rid, rec, ledger):
    if not isinstance(rec, dict):
        return [f"{rid}: `recurrence` must be an object carrying the count that "
                f"earned this row its place."]
    v = []
    files, of = rec.get("files"), rec.get("of")
    corpus = _d(_d(ledger).get("_seeded_from")).get("answer_files")
    if not isinstance(files, int) or not isinstance(of, int):
        v.append(f"{rid}: `recurrence.files` and `.of` must both be integers.")
    elif files > of:
        v.append(f"{rid}: recurrence says {files} of {of} — a defect cannot be "
                 f"filed in more files than the corpus holds.")
    elif corpus is not None and of != corpus:
        v.append(f"{rid}: recurrence is out of {of} but the ledger's corpus is "
                 f"{corpus} answer files. Two denominators means the ranking "
                 f"that picked these twenty rows cannot be reproduced.")
    return v


def _check_closure(rid, r, door, root):
    """The rule itself: closing needs evidence, refuting needs a number."""
    v = []
    status = r.get("status")
    if status == "built":
        if door == "none_yet":
            v.append(f"{rid}: marked built while its door says no instrument can "
                     f"see it. One of the two is false.")
        ev = r.get("closed_by")
        if not isinstance(ev, dict) or not str(ev.get("how", "")).strip():
            v.append(f"{rid}: marked built with no `closed_by.how`. An item "
                     f"closes through its door, not through a sentence.")
            return v
        paths = _ev_paths(ev)
        if not paths:
            v.append(f"{rid}: marked built with no `closed_by.evidence` — name "
                     f"the placement dump or the rendered frame it resolved "
                     f"against.")
        for p in paths:
            full = os.path.join(root, p)
            if not os.path.exists(full):
                v.append(f"{rid}: `closed_by.evidence` names {p}, which does not "
                         f"exist. A debt closed against a file that is not there "
                         f"was closed against nothing.")
                continue
            k = evidence_kind(full)
            if k is None:
                v.append(f"{rid}: `closed_by.evidence` names {p}, which is "
                         f"neither a rendered frame, a placement dump, nor a "
                         f"spec. Evidence is judged by CONTENT — a filename "
                         f"test is how `docs/strategy.md` discharged a debt.")
            elif k == "spec" and door != "scene_row":
                v.append(f"{rid}: closed against {os.path.basename(p)} — a SPEC. "
                         f"A spec is what we said; a `{door}` door closes against "
                         f"what was BUILT (a placement dump) or what was RENDERED "
                         f"(a frame).")
    elif status == "refuted":
        if door == "none_yet":
            v.append(f"{rid}: refuted while its door says no instrument can see "
                     f"it. A refutation with no instrument is taste.")
        ref = str(r.get("refuted_by", "")).strip()
        if not ref:
            v.append(f"{rid}: marked refuted with no `refuted_by`.")
        elif not HAS_NUMBER.search(ref):
            v.append(f"{rid}: refuted with no number in `refuted_by` — R7 allows "
                     f"a refutation only WITH A MEASUREMENT, never with taste.")
        m = str(r.get("measured_in", "")).strip()
        if not m:
            v.append(f"{rid}: refuted with no `measured_in` — the measurement "
                     f"has to have been made somewhere real.")
        elif not os.path.exists(os.path.join(root, m)):
            v.append(f"{rid}: `measured_in` names {m}, which does not exist.")
    return v


# --------------------------------------------------------------- the ratchet --

def ratchet(ledger, previous=None, repo_root=None):
    """A row may change status. It may never LEAVE.

    Same mechanism as `reachability_check.baseline_ratchet` and for the same
    reason: the failure being fixed is items quietly disappearing between the
    gate artifact that accepted them and the round that was supposed to build
    them. Deleting a row is the one edit that reproduces the original defect
    exactly, so it is the one edit that fails."""
    root = repo_root or REPO
    if previous is None:
        try:
            p = subprocess.run(["git", "show", "HEAD:" + LEDGER_REL], cwd=root,
                               capture_output=True, text=True, encoding="utf-8",
                               timeout=30)
        except Exception as e:                          # noqa: BLE001
            return [f"cannot read the committed ledger to check the ratchet ({e})"]
        if p.returncode != 0:
            return []                                   # first landing
        try:
            previous = json.loads(p.stdout)
        except ValueError:
            return []
    was = {r.get("id") for r in rows(previous) if r.get("id")}
    now = {r.get("id") for r in rows(ledger) if r.get("id")}
    gone = sorted(was - now)
    if gone:
        return [f"{', '.join(gone)} left {LEDGER_REL} without being built or "
                f"refuted. A row may change status; it may never vanish. "
                f"Deleting it is exactly the 357-filed/22-built move this "
                f"ledger was written to make impossible."]
    return []


# ------------------------------------------------------------- the resolution --

def scene_names(scene):
    """Object names from a placement dump, with the SM_<UNIT>_ prefix stripped.

    The dump is what BUILT, so the names carry the materialiser's prefix while
    the ledger speaks the spec's language. Matching on the bare tail is what lets
    one row read both."""
    out = []
    for o in _drawable(_d(scene).get("objects")):
        n = o.get("name")
        if not n:
            continue
        out.append(re.sub(r"^SM_[A-Za-z0-9]+_", "", n))
    return out


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".exr", ".tif", ".tiff", ".webp")


def evidence_kind(path):
    """What a piece of evidence IS, read from its CONTENT — never from its name.

    The first version of the closure check judged evidence by its filename: any
    existing path was accepted unless it was a `.json` with "spec" in the
    basename. That is a name test wearing a content test's clothes, and this repo
    has the matching precedent one level up — `reachability_check` counted a prose
    MENTION of a module as a call until a docstring citation produced a false
    green. Renaming `spec_r38.json` to `r38.json` defeated the whole rule."""
    if str(path).lower().endswith(IMAGE_EXT):
        return "frame"
    data = _load_json(path)
    if isinstance(data, dict):
        if isinstance(data.get("objects"), list):
            return "dump"
        if isinstance(data.get("masses"), list):
            return "spec"
    return None


# What each door needs before it can be RE-RUN against a closure's evidence.
# A scene row needs BOTH: the spec carries `kind` and `beauty.soft`, which is
# where D8/D9 are measured, and the dump is what proves the spec describes
# something that was actually built.
DOOR_NEEDS = {"object": ("dump",), "guard": ("dump",),
              "image_row": ("frame",), "scene_row": ("spec", "dump")}


def _ev_paths(closed_by):
    """Evidence paths, from a string or a list. A scene row cites two files."""
    e = _d(closed_by).get("evidence")
    if isinstance(e, str):
        return [e.strip()] if e.strip() else []
    if isinstance(e, list):
        return [str(x).strip() for x in e if str(x).strip()]
    return []


def spec_is_built(spec, scene):
    """(ok, detail) — does the BUILT scene contain what the spec declared?

    This is what lets a `scene_row` row close at all. D7/D8/D9 are measured off
    the spec (they need `kind` and `beauty.soft`, which only the spec carries), so
    on their own they can never say more than DECLARED. Pairing the spec's claim
    with the dump's contents is the corroboration: the metric passes AND the
    masses it counted are in the file that rendered. Without this, three of the
    twenty-one rows — including the 28-of-28 row — had no legitimate closure path
    at all, which is exactly what made the escape hatch load-bearing."""
    declared = {str(m.get("name", "")).lower()
                for m in _d(spec).get("masses", []) if isinstance(m, dict)}
    declared.discard("")
    if not declared:
        return False, "the spec declares no masses"
    built = {n.lower() for n in scene_names(scene)}
    missing = sorted(declared - built)
    if missing:
        return False, (f"{len(missing)} declared mass(es) are not drawable in the "
                       f"built scene: {', '.join(missing[:4])}")
    return True, f"all {len(declared)} declared masses are in the built scene"


def verify_closures(ledger, repo_root=None, standard=None):
    """[violation str] — every row marked `built` whose door does not actually
    resolve against the evidence it cites.

    THIS IS THE RULE. Before it existed, `built` was checked by `os.path.exists`
    and a substring, so the 28-of-28 cloth row closed on the sentence "soft goods
    now drape" plus `CLAUDE.md`, `check()` printed "every closed row closed
    through its door", and `resolve()` and `due_now()` skipped it forever. Twelve
    of the twenty-one rows — precisely the twelve that HAVE a working instrument —
    were dischargeable that way. The nine that resisted were the `none_yet` rows,
    which have no door to run. A ledger whose free pass is available exactly where
    a measurement exists is worse than no ledger.
    """
    root = repo_root or REPO
    out = []
    for r in rows(ledger):
        if r.get("status") != "built":
            continue
        rid = r.get("id") or "<no id>"
        door = _d(r.get("closes_when")).get("door")
        if door not in DOOR_NEEDS:
            continue                    # already reported by check()
        paths = _ev_paths(r.get("closed_by"))
        if not paths:
            continue                    # already reported by check()
        arts, kinds = {}, []
        for p in paths:
            full = os.path.join(root, p)
            k = evidence_kind(full)
            kinds.append(f"{os.path.basename(p)}={k or 'unrecognised'}")
            if k == "frame":
                arts["frame"] = full
            elif k in ("dump", "spec"):
                arts[k] = _load_json(full)
        need = DOOR_NEEDS[door]
        missing = [k for k in need if arts.get(k) is None]
        if missing:
            out.append(f"{rid}: closed against {', '.join(kinds)}, but a "
                       f"`{door}` door needs {', '.join(need)}. Evidence is "
                       f"judged by CONTENT, not by filename.")
            continue
        got = {x[0]: x for x in resolve({"rows": [dict(r, status="open")]},
                                        scene=arts.get("dump"),
                                        frame=arts.get("frame"),
                                        spec=arts.get("spec"),
                                        standard=standard)}
        verdict, detail = got[rid][1], got[rid][2]
        if verdict != "RESOLVED":
            extra = ("" if verdict != "PARTIAL" else
                     " A guard door alone cannot close a row: it answers a "
                     "narrower question than the one that was filed.")
            out.append(f"{rid}: marked built, but re-running its own door "
                       f"against {', '.join(os.path.basename(p) for p in paths)} "
                       f"returns {verdict} — {detail}{extra}")
    return out


def resolve(ledger, scene=None, frame=None, spec=None, standard=None):
    """[(id, verdict, detail)] for every OPEN row.

    verdict is RESOLVED / PARTIAL / UNRESOLVED / DECLARED-ONLY / NOT RUN.
    ONLY RESOLVED IS A PASS. The other four are different KINDS of not-passing and
    that is the whole reason this returns a word instead of a boolean:
      UNRESOLVED     we looked and the defect is there
      PARTIAL        the instrument's half holds; it is narrower than the defect
      DECLARED-ONLY  we said so, and nothing built confirms it
      NOT RUN        we did not look
    'We did not look' and 'we looked and it was fine' are the two this repo has
    confused most often, and they want opposite fixes."""
    names = scene_names(scene) if scene else None
    img = None
    if frame:
        try:
            import deliverable_check as DC
            img = DC.measure_image(frame)
        except Exception as e:                          # noqa: BLE001
            img = {"_error": f"{type(e).__name__}: {e}"}
    scene_meas = None
    if spec is not None:
        try:
            import deliverable_check as DC
            scene_meas = DC.measure_scene_spec(spec)
        except Exception:                               # noqa: BLE001
            scene_meas = None
    # A scene row may only rise above DECLARED when the dump corroborates the
    # spec — see `spec_is_built`.
    corrob = bool(spec is not None and scene is not None
                  and spec_is_built(spec, scene)[0])

    out = []
    for r in rows(ledger):
        if r.get("status") != "open":
            continue
        rid = r.get("id")
        d = _d(r.get("closes_when"))
        door = d.get("door")

        if door == "none_yet":
            out.append((rid, "NOT RUN",
                        f"no instrument sees this yet — blocked on "
                        f"{d.get('blocked_on', '?')}"))
        elif door == "object":
            want = str(d.get("match", ""))
            # `check()` has already named a bad min_count, but `main()` resolves
            # BEFORE it prints violations, so a bare int() here threw and took the
            # violation list with it — a traceback replacing the named refusal.
            mc = d.get("min_count", 1)
            need = mc if isinstance(mc, int) and not isinstance(mc, bool) and mc >= 1 else None
            if need is None:
                out.append((rid, "NOT RUN",
                            f"`min_count` is {mc!r}, not a positive integer"))
                continue
            if names is None:
                if spec is None:
                    out.append((rid, "NOT RUN", "no built scene given"))
                else:
                    got = sum(1 for m in spec.get("masses", [])
                              if want.lower() in str(m.get("name", "")).lower())
                    out.append((rid, "DECLARED-ONLY",
                                f"the spec declares {got} mass(es) matching "
                                f"'{want}' (need {need}) — a spec is not a "
                                f"built scene"))
            else:
                got = sum(1 for n in names if want.lower() in n.lower())
                out.append((rid, "RESOLVED" if got >= need else "UNRESOLVED",
                            f"{got} object(s) matching '{want}' in the built "
                            f"scene (need {need})"))
        elif door in ("image_row", "scene_row"):
            out.append(_resolve_row(rid, d, door, img, scene_meas, standard,
                                    corroborated=corrob))
        elif door == "guard":
            out.append(_resolve_guard(rid, d, scene))
        else:
            out.append((rid, "NOT RUN", f"unknown door {door!r}"))
    return out


def _resolve_guard(rid, d, scene):
    """Run the named guard on the BUILT SCENE and read its verdict.

    A guard that cannot be imported is NOT RUN, never RESOLVED — the same law as
    every other rung here. 'The guard was missing' and 'the guard was happy' are
    the two readings this repo has confused before, and they are not close."""
    if scene is None:
        return (rid, "NOT RUN", f"{d.get('module')} needs a placement dump")
    try:
        import placement_check as PC
    except ImportError as e:                            # pragma: no cover
        return (rid, "NOT RUN", f"{d.get('module')} is not importable ({e})")
    objs = _drawable(_d(scene).get("objects"))
    if not objs:
        return (rid, "NOT RUN",
                "the placement dump holds no drawable mesh — a guard cannot "
                "judge a scene the renderer would not draw")
    want = d.get("verdict")
    match = str(d.get("match", "")).lower()
    scope = f" matching '{match}'" if match else ""

    # THE OBJECT HAS TO BE THERE BEFORE A GUARD CAN EXONERATE IT. Without this,
    # a row naming `headboard` closes the moment the headboard is DELETED —
    # nothing floats if nothing is there. That is R9b's own finding ("a rule that
    # names the objects it applies to will always exempt the next one") wearing a
    # different hat, and it was live in this function for one draft.
    if match and not any(match in str(o.get("name", "")).lower() for o in objs):
        return (rid, "UNRESOLVED",
                f"no object matching '{match}' is in the built scene — a guard "
                f"cannot exonerate an object that is not there, and deleting the "
                f"mass would otherwise close this row")

    findings = PC.check(objs)
    hits = [f for f in findings
            if f.get("kind") == want
            and (not match or match in str(f.get("object", "")).lower())]
    if hits:
        return (rid, "UNRESOLVED",
                f"{len(hits)} {want}{scope}: "
                f"{', '.join(str(f.get('object')) for f in hits[:4])}")
    # A CLEAN SHEET IS REPORTED AS A CLEAN SHEET. The total FAIL count is the
    # positive control this repo learned to demand at r38: "no step at u=989" was
    # quoted as proof until a corner that certainly exists scored the same. If the
    # guard returns zero FAILs across the whole scene, that is either a genuinely
    # clean build or a detector that is not biting, and the reader needs the
    # number to tell. `covers` says what this guard can and cannot see, so a
    # resolve is never read as the whole defect being gone.
    fails = sum(1 for f in findings if f.get("sev") == "FAIL")
    # PARTIAL, NOT RESOLVED — and this word is the whole finding.
    #
    # On r38b all three guard rows came back RESOLVED: `bed_headboard` is in the
    # dump, is drawable, and placement_check says it is supported. Meanwhile the
    # critic who filed the row wrote "no headboard; pillows lean directly on
    # full-height wardrobe doors". Both are true. The guard answers "is it held
    # up"; the row says "absent, leaning, floating OR IMPLAUSIBLE". A guard
    # verdict is always NARROWER than the defect a person filed, and printing a
    # `covers` line under the word RESOLVED does not stop `due_now` from clearing
    # the row or `verify_closures` from accepting it as paid.
    #
    # So a satisfied guard returns PARTIAL: its half holds, the row stays owed,
    # and the row cannot be CLOSED on this door alone. That is the same law R9
    # states about one parameter carrying two things — the remedy is a second
    # door for the other half, not a looser word for this one.
    return (rid, "PARTIAL",
            f"no {want} finding{scope} ({len(objs)} drawable objects; the guard "
            f"returned {fails} FAIL finding(s) across the whole scene). This "
            f"guard COVERS ONLY: {d.get('covers', '?')} The rest of the filed "
            f"defect has no instrument, so the row stays open.")


def _resolve_row(rid, d, door, img, scene_meas, standard, corroborated=False):
    row = d.get("row")
    if standard is None:
        return (rid, "NOT RUN", "no standard loaded")
    t = _d(_d(standard).get("rows")).get(row)
    if not t:
        return (rid, "NOT RUN", f"{row} is not in the standard")
    src = img if door == "image_row" else scene_meas
    if src is None:
        return (rid, "NOT RUN",
                f"{row} needs {'a rendered frame' if door == 'image_row' else 'a spec'}")
    if "_error" in src:
        return (rid, "NOT RUN", f"{row}: {src['_error']}")
    key = t.get("metric")
    if key not in src:
        return (rid, "NOT RUN", f"{row}: {key} was not measured")
    val, thr, direction = src[key], t["threshold"], t["direction"]
    if direction == "min":
        ok = val >= thr
    elif direction == "max":
        ok = val <= thr
    else:
        ok = thr[0] <= val <= thr[1]
    detail = f"{row}: {key}={val} vs {thr} ({direction})"
    # A scene row is measured off the SPEC, so on its own it can only say what we
    # DECLARED. It rises to RESOLVED only when a placement dump corroborates that
    # the spec describes something that was actually built.
    if door == "scene_row":
        if not ok:
            return (rid, "UNRESOLVED", detail)
        if not corroborated:
            return (rid, "DECLARED-ONLY", detail + " — declared, not built")
        return (rid, "RESOLVED", detail + " — and the built scene carries it")
    return (rid, "RESOLVED" if ok else "UNRESOLVED", detail)


def due_now(ledger, phases, current_phase):
    """Ids of open rows whose due_phase is at or before `current_phase`.

    A row not yet due is OWED, not FAILED — the lane is allowed to be at P0 with
    a P2 debt on the books. Blocking on that would be the enforcement clause R3
    revoked, one level down."""
    if not phases or current_phase not in phases:
        return []
    here = phases.index(current_phase)
    return [r.get("id") for r in rows(ledger)
            if r.get("status") == "open" and r.get("due_phase") in phases
            and phases.index(r["due_phase"]) <= here]


# ------------------------------------------------------------ the spec refusal --

def refuse_spec(ledger, spec, spec_path):
    """[line] — why a spec alone may not discharge a single row. Never empty when
    open rows exist, and it NAMES THE FILE."""
    base = os.path.basename(spec_path)
    open_rows = [r for r in rows(ledger) if r.get("status") == "open"]
    if not open_rows:
        return []
    unit = str(_d(spec).get("id") or _d(spec).get("unit") or "").lower()

    def _norm(s):
        return re.sub(r"[^a-z0-9]", "", str(s).lower())

    # Normalised BOTH sides, because "TRN-002" and "trn002_mat_r38" are the same
    # unit written two ways and raw substring containment only matched by luck.
    # An EMPTY `filed_in` matches nothing — check() reports it by name, and a row
    # with no unit must not silently belong to every spec.
    filed_here = [r for r in open_rows
                  if _norm(r.get("filed_in")) and _norm(r.get("filed_in")) in _norm(unit)]
    masses = {str(m.get("name", "")).lower()
              for m in _d(spec).get("masses", []) if isinstance(m, dict)}
    absent = [r for r in open_rows
              if _d(r.get("closes_when")).get("door") == "object"
              and not any(str(_d(r.get("closes_when")).get("match", "")).lower() in m
                          for m in masses)]
    out = [f"{base} is a SPEC. A spec is what we said; a debt closes against what "
           f"was BUILT (a placement dump) or what was RENDERED (a frame). No row "
           f"below is closed by this file.",
           f"{len(open_rows)} row(s) open"
           + (f", {len(filed_here)} of them filed against this spec's own unit "
              f"({', '.join(sorted({str(r.get('filed_in')) for r in filed_here}))})"
              if filed_here else "")
           + ".",
           "CLOSING IS NOT DISCHARGING: a unit may be closed with every defect it "
           "was filed for still in the frame. Crossing a row into another lane "
           "records where it will be paid, not that it was paid."]
    if absent:
        out.append(f"{len(absent)} row(s) name an object this spec does not "
                   f"contain at all: "
                   f"{', '.join(str(r.get('id')) for r in absent)}.")
    return out


# ------------------------------------------------------------------- reporting --

def tally(ledger):
    r = rows(ledger)
    by = {s: sum(1 for x in r if x.get("status") == s) for s in STATUSES}
    by["none_yet"] = sum(1 for x in r
                         if _d(x.get("closes_when")).get("door") == "none_yet")
    by["total"] = len(r)
    return by


def one_line(ledger):
    """The line that prints in the render path and at the top of every session.

    ONE line, for the reason `contact_check.undeclared` is one line: an advisory
    nobody finishes reading is the mute this repo keeps rediscovering."""
    t = tally(ledger)
    filed = _d(_d(ledger).get("_seeded_from")).get("items_filed")
    tail = (f"; seeded from the top {t['total']} by recurrence of {filed} filed "
            f"items" if filed else "")
    return (f"CRITIC DEBT  {t['open']} open / {t['built']} built / "
            f"{t['refuted']} refuted, {t['none_yet']} with no instrument that "
            f"can see them{tail}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="The critic-debt ledger: what was "
                                             "filed, what was built, what no "
                                             "instrument can see.")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--standard", default=None)
    ap.add_argument("--scene", default=None, help="a placement dump (BUILT)")
    ap.add_argument("--frame", default=None, help="a rendered frame (BUILT)")
    ap.add_argument("--spec", default=None, help="a spec (DECLARED — cannot close)")
    ap.add_argument("--phase", default=None,
                    help="treat this as the current plan phase (default: read it "
                         "off the plan)")
    ap.add_argument("--soft", action="store_true", help="report, do not exit 1")
    a = ap.parse_args(argv)

    ledger = load(a.ledger)
    if ledger is None:
        print(f"!! {check(None)[0]}")
        return 2

    standard = None
    try:
        import deliverable_check as DC
        standard = DC.load_standard(a.standard)
    except Exception as e:                              # noqa: BLE001
        print(f"~~ the standard could not be read ({e}) — image and scene doors "
              f"cannot be resolved, which is unknown, not fine")

    spec = None
    if a.spec:
        try:
            with open(a.spec, encoding="utf-8") as f:
                spec = json.load(f)
        except (OSError, ValueError) as e:
            print(f"!! cannot read spec {a.spec}: {e}")
            return 2
    scene = None
    if a.scene:
        try:
            with open(a.scene, encoding="utf-8") as f:
                scene = json.load(f)
        except (OSError, ValueError) as e:
            print(f"!! cannot read scene dump {a.scene}: {e}")
            return 2

    phases = _plan_phases(a.plan)
    v = check(ledger, plan_phases=phases, standard=standard)
    v += ratchet(ledger)

    print(one_line(ledger))

    res = resolve(ledger, scene=scene, frame=a.frame, spec=spec, standard=standard)
    # WHICH ROWS ARE ALLOWED TO BE UNPAID TODAY. A P2 debt is not a failure while
    # the lane is at P0 — halting on that is the enforcement clause R3 revoked,
    # one level down. A debt whose own due phase has arrived is the BUILDER's side
    # slipping, and that is the half `decisions_check` blocks on.
    due = set(due_now(ledger, phases, a.phase or _current_phase(a.plan)))
    if res:
        print("\nOPEN ROWS — the door, and what it says today:")
        for rid, verdict, detail in res:
            flag = "DUE" if rid in due else "   "
            print(f"  {flag} {rid:9s} {verdict:14s} {detail}")
    overdue = [rid for rid, verdict, _d in res
               if rid in due and verdict != "RESOLVED"]

    refusal = []
    if spec is not None and scene is None and not a.frame:
        refusal = refuse_spec(ledger, spec, a.spec)
        if refusal:
            print("\nREFUSED:")
            for s in refusal:
                print(f"  !! {s}")

    if overdue:
        print(f"\nDUE AND UNPAID: {', '.join(overdue)} — the due phase for these "
              f"has arrived and the door still does not resolve.")

    if v:
        print(f"\nDEBT LEDGER: {len(v)} violation(s)")
        for s in v:
            print(f"  !! {s}")
    else:
        print("\nDEBT LEDGER: every row is well formed and every closed row "
              "closed through its door.")

    bad = bool(v) or bool(refusal) or bool(overdue)
    return 0 if a.soft else (1 if bad else 0)


if __name__ == "__main__":
    raise SystemExit(main())
