#!/usr/bin/env python3
"""carry_check.py — WHAT CARRIES THIS MASS? PURE (no bpy), reads `scene-dump@2`.

    python pipeline/scripts/carry_check.py <room_*.scene.json> [--ledger qa/carry-ledger.json]

WHAT EARNED IT, AND IT IS NOT A NEW QUESTION — IT IS THE ONE TWO FILES ASK FOR BY NAME
--------------------------------------------------------------------------------------
`placement_check`'s FLOATING branch declares its own hole in its own docstring:
*"An object with NO support escapes FLOATING if anything at all touches it."* The
repo then paid for that sentence twice more and wrote the missing rung down both
times — `build_room._recessed_trim`: *"It took a rung that asks what HOLDS a mass,
not whether it touches one"*, and DEBT-19's covers-text, which excludes by name
*"a slab that is supported at one end and unsupported at the other"*.

p2r84 produced the sharpest instance this lane has: **every brass hang rail in the
room stops 40 mm short of BOTH gables** (millwork's own `l0 + 0.04` / `lw - 0.08`)
— a tube carried at neither end, on every frame this lane has ever shipped. Nine of
them. And two of the nine were EXCUSED FROM `FLOATING` BY THE CLOTHES HANGING ON
THEM: the contact graph read `rail -> garment -> gable -> floor` and called it
supported. **A mass excused by the load it carries** is the vase-and-flowers hole
with the ambiguity removed — a garment on a rail is unambiguously LOAD.

THE PREMISE, and the scope is derived from it rather than from a list of names
(R9b): every rendered mass must have a LOAD PATH — some other mass that can hand
its weight downward, and so on until the ground. Five relations, each directional,
each expressible from an AABB, each a thing a builder does:

  RESTS-ON     my bottom meets its top, footprints overlap        (a book on a shelf)
  HANGS-FROM   my top meets its bottom, footprints overlap        (a trim under a soffit)
  HUNG-ON      a horizontal MEMBER lies deep inside me, passing
               clean through me or lying in my top quarter        (a hanger over a rail)
  FIXED-IN     we overlap deeply on all three axes                (a mirror let into a back)
  FASTENED-TO  we share a FACE: one axis at zero overlap, real
               overlap on the other two                           (a drawer front on its box)
  ANCHORED-TO  a lateral touch with a COLUMN that spans me in z   (a switch plate on a wall)

A COLUMN is the ground, or anything that RESTS-ON a column, transitively.

TWO ASYMMETRIES DO ALL THE WORK, and both were found by running it:

  (1) **ANCHORING DOES NOT CHAIN.** An ANCHORED-TO carrier must be a COLUMN, not
      merely something already carried. Leaning on a wall makes you stable; it does
      not make you a wall. Without this, a garment brushing a gable became a wall
      that could then carry the rail it hangs from, and the defect this file exists
      for read GREEN.
  (2) **A MEMBER THREADED THROUGH A MASS IS THE CARRIER, NOT THE CARRIED.**
      FIXED-IN is a symmetric test — deep overlap has no direction — so a rail
      inside a hanger and a hanger over a rail are the same six numbers. HUNG-ON
      breaks the tie with the one asymmetry an AABB does carry: a long thin
      HORIZONTAL member either passes clean out of the other mass on its own long
      axis, or sits in the top quarter of a taller mass. Either way it is the rail
      and the other thing is the coat.

WHAT IT CANNOT SEE — said here so nobody reads a pass as more than it is:
  * AABBs, not geometry. Two boxes that overlap may not touch at all.
  * No moments. A 3 m shelf held at one end passes; it is held.
  * A wall's AABB spans its own window openings, so a mass floating inside a reveal
    can be excused by a wall it does not touch. (The west sheers are NOT — they
    hang 18 mm proud of the wall's inner face, which is why they are in the list.)
  * A mass that penetrates a slab is FIXED-IN it. That is right for a let-in mirror
    and wrong for a curtain whose top simply disappears into the ceiling with no
    pocket — this rung reads the second as carried. Interpenetration is
    `placement_check`'s advisory and stays there.
    **AND THE EYE PROVED THIS HOLE ON THE RUNG'S FIRST LIVE FRAME.** C2 read
    p2r85 and filed, correctly, that the wardrobe garment "hangs from nothing":
    the scene agrees to the millimetre — BF09-3's rail spans z 1850-1880 and the
    set hanging on it tops out at 1735, so 115 mm of air. This rung passed it,
    because the garment pokes ~20 mm into the carcass BACK PANEL and a 5 mm
    overlap on three axes is read as "let into". Measured: that overlap is 2.7%
    of the garment's own depth. A containment-fraction cut on FIXED-IN closes it
    and is NOT applied here, because it is a decision with a blast radius that
    wants its own round rather than a quiet retune inside the round that shipped
    the rung: swept on this frame, a 10% cut takes UNCARRIED from 32 to 68 and a
    25% cut to 78 — and most of the difference is real (curtains vanishing into
    the ceiling, book covers floating over their blocks) rather than noise. It is
    filed as P2r-30 with those numbers. **Until then this rung answers "is there a
    load path at all", not "is the load path the one a builder would build".**
  * It says nothing about whether the object should EXIST (R10 / existence_check)
    or whether it is in the right PLACE (placement_check, dim_check).

D-112 (instrument-admission quota): admitted because it gives an eye to the class
DEBT-19 excludes in writing and to DEBT-08 on a lane where `placement_check` has
never once been spawned (qa/coverage-map.json's own `room_lane_debt` row, open
since 2026-08-24, whose `restart_by` names this wiring).

THE LEDGER AND THE RATCHET (R13: a machine that hard-fails every historical
instance on day one gets switched off). `qa/carry-ledger.json` carries one row per
KNOWN uncarried mass, each with a verdict and a named action. An uncarried mass
with no row FAILS THE BUILD. A row whose masses are all carried again is STALE and
also fails — a queue nobody empties is this repo's signature defect, and a ledger
is a queue. A row's `covers_n` is the count it was written against: if the real
count RISES above it, the row is hiding new instances and the build fails.

EXIT CODES ARE A CONTRACT: 0 = every mass is carried or rowed, 1 = it is not,
2 = COULD NOT RUN. "Could not look" must never print like "looked and it was fine".
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                       # noqa: BLE001
    pass

# --- tolerances, in mm, and each one is a claim about the real world -----------
# A join is a contact, not a hover — 1 mm is below what any camera in this studio
# resolves at room scale and above float noise from a metre-scale matrix multiply.
# Same number as placement_check.CONTACT_TOL_MM, and deliberately so: two rungs
# reading one built scene must not disagree about what "touching" means.
CONTACT_TOL_MM = 1.0
# How deeply two boxes must overlap on every axis before it reads as one being
# LET INTO the other rather than two parts sharing a face.
EMBED_MM = 5.0
# A "member": its longest horizontal axis is at least this many times its largest
# other dimension. 3.0 keeps a rail (652 x 30 x 30 = 21.7x) and a plinth in, and
# keeps a wall (6000 x 110 x 2800 = 2.1x) and a shelf (650 x 600 x 18 = 1.1x) out
# — a wall passing through something must never read as a rail it hangs on.
MEMBER_RATIO = 3.0
# Where on a taller mass a member has to sit before "it hangs on this" beats
# "it is embedded in this". A hanger's rail is in the top few percent; a quarter
# is generous and still excludes a member crossing a mass at mid-height.
HANG_BAND = 0.75

VERDICTS = ("fix", "signed-gap", "unresolved")


# --------------------------------------------------------------- the scene

def load_dump(path):
    """scene-dump@2 -> [{name, min[3], max[3], in_frustum}] in MILLIMETRES.

    Refuses a dump with no `aabb`: the schema that lacks it is the one
    `placement_dump` writes, and silently reading zero masses out of a 546-object
    scene is exactly the vacuous zero this repo keeps rebuilding."""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    objs = doc.get("objects", doc if isinstance(doc, list) else [])
    out = []
    seen_aabb = False
    for o in objs:
        ab = o.get("aabb")
        if ab is None:
            continue
        seen_aabb = True
        if o.get("hidden_render"):
            continue                                    # never drawn -> never carried
        out.append({"name": o["name"],
                    "min": [float(v) * 1000.0 for v in ab[0]],
                    "max": [float(v) * 1000.0 for v in ab[1]],
                    "in_frustum": o.get("in_frustum")})
    if objs and not seen_aabb:
        raise ValueError("no object in this dump carries an `aabb` — this is not a "
                         "scene-dump@2 and a carrier verdict cannot be computed "
                         "from it")
    return out


# --------------------------------------------------------------- geometry

def _ov(a, b, k):
    return min(a["max"][k], b["max"][k]) - max(a["min"][k], b["min"][k])


def touches(a, b, tol=CONTACT_TOL_MM):
    return all(_ov(a, b, k) >= -tol for k in range(3))


def _dims(o):
    return [o["max"][k] - o["min"][k] for k in range(3)]


def member_axis(o, ratio=MEMBER_RATIO):
    """The long axis of a HORIZONTAL member (0=x, 1=y), or None. A vertical stick
    is a post, not a rail: you do not hang a coat on it."""
    d = _dims(o)
    la = max(range(3), key=lambda k: d[k])
    if la == 2:
        return None
    other = max(d[k] for k in range(3) if k != la)
    return la if other > 0 and d[la] >= ratio * other else None


def hangs_on(a, b, tol=CONTACT_TOL_MM, band=HANG_BAND):
    """Is `b` a horizontal member that `a` HANGS ON? (see asymmetry (2) above)

    NO DEEP-OVERLAP REQUIREMENT, and that was measured rather than assumed: the
    garment sets in this room import their hanger as a 4 mm plate, so a hook over a
    30 mm rail overlaps it by 4 mm on one axis and the 5 mm embed test read seven
    real hangers as hanging on nothing. What makes it a hook is not how thick it is
    — it is that it REACHES OVER the member and hangs below it."""
    la = member_axis(b)
    if la is None:
        return False
    if not touches(a, b, tol):
        return False
    if b["max"][2] > a["max"][2] + tol:
        return False                                    # it is above me: I am not on it
    if b["min"][2] <= a["min"][2] + tol:
        return False                                    # it is at my foot: that is a floor
    if b["min"][la] < a["min"][la] - tol and b["max"][la] > a["max"][la] + tol:
        return True                                     # passes clean through
    return b["max"][2] >= a["min"][2] + band * _dims(a)[2]


def relations(objs, tol=CONTACT_TOL_MM, embed=EMBED_MM):
    """{relation: {name: set(carrier names)}} — every candidate load path in the
    scene, before anything is asked whether it reaches the ground."""
    rel = {k: {o["name"]: set() for o in objs}
           for k in ("RESTS-ON", "HANGS-FROM", "HUNG-ON", "FIXED-IN",
                     "FASTENED-TO", "ANCHORED-TO")}
    for a in objs:
        an = a["name"]
        for b in objs:
            if b is a:
                continue
            bn = b["name"]
            dx, dy = _ov(a, b, 0), _ov(a, b, 1)
            if abs(b["max"][2] - a["min"][2]) <= tol and dx > tol and dy > tol:
                rel["RESTS-ON"][an].add(bn)
            if abs(b["min"][2] - a["max"][2]) <= tol and dx > tol and dy > tol:
                rel["HANGS-FROM"][an].add(bn)
            deep = all(_ov(a, b, k) >= embed for k in range(3))
            if hangs_on(a, b, tol):
                rel["HUNG-ON"][an].add(bn)
            elif deep and not hangs_on(b, a, tol):
                rel["FIXED-IN"][an].add(bn)
                # the `elif`/`and not` IS asymmetry (2): when b hangs on a, a is the
                # RAIL and cannot be carried by what it carries.
            if not deep and touches(a, b, tol):
                o3 = [_ov(a, b, k) for k in range(3)]
                flat = [k for k in range(3) if abs(o3[k]) <= tol]
                if len(flat) == 1 and all(o3[k] > tol for k in range(3)
                                          if k != flat[0]):
                    rel["FASTENED-TO"][an].add(bn)
                if b["min"][2] < a["min"][2] - tol and b["max"][2] > a["max"][2] + tol:
                    rel["ANCHORED-TO"][an].add(bn)
    return rel


def columns(objs, rel, tol=CONTACT_TOL_MM):
    """What may ANCHOR something else: the ground, and whatever stands on it.
    See asymmetry (1) — this set grows through RESTS-ON alone, on purpose."""
    if not objs:
        return set()
    gz = min(o["min"][2] for o in objs)
    col = {o["name"] for o in objs if abs(o["min"][2] - gz) <= tol}
    rests = rel["RESTS-ON"]
    changed = True
    while changed:
        changed = False
        for o in objs:
            n = o["name"]
            if n not in col and (rests[n] & col):
                col.add(n)
                changed = True
    return col


# ORDER MATTERS ONLY FOR THE REPORTED REASON, never for the verdict: the fixpoint
# below is monotone, so a mass carried by any relation is carried. The order names
# the most load-bearing relation first so the printed WHY is the useful one.
_LADDER = (("RESTS-ON", False), ("HANGS-FROM", False), ("HUNG-ON", False),
           ("FIXED-IN", False), ("FASTENED-TO", False), ("ANCHORED-TO", True))


def carriers(objs, rel=None, tol=CONTACT_TOL_MM):
    """(how, col) — how[name] is the relation that carries it, or None."""
    rel = rel if rel is not None else relations(objs, tol)
    col = columns(objs, rel, tol)
    if not objs:
        return {}, col
    gz = min(o["min"][2] for o in objs)
    how = {o["name"]: None for o in objs}
    carried = set()
    for o in objs:
        if abs(o["min"][2] - gz) <= tol:
            how[o["name"]] = "GROUND"
            carried.add(o["name"])
    changed = True
    while changed:
        changed = False
        for o in objs:
            n = o["name"]
            if n in carried:
                continue
            for name, needs_column in _LADDER:
                if rel[name][n] & (col if needs_column else carried):
                    carried.add(n)
                    changed = True
                    break
    # THE REASON IS RE-DERIVED AGAINST THE FINAL SET, never against whatever the
    # fixpoint happened to have proved when this mass was first reached. Otherwise
    # the printed WHY depends on the order objects were dumped in, and a reader
    # comparing two runs would see a relation "change" that never moved.
    for o in objs:
        n = o["name"]
        if how[n] is not None or n not in carried:
            continue
        for name, needs_column in _LADDER:
            if rel[name][n] & (col if needs_column else carried):
                how[n] = name
                break
    return how, col


def uncarried(objs, tol=CONTACT_TOL_MM):
    how, _ = carriers(objs, None, tol)
    return [o for o in objs if how[o["name"]] is None]


# --------------------------------------------------------------- the ledger

def load_ledger(path):
    """Rows, validated. A malformed ledger RAISES — a gate whose ledger cannot be
    read has not passed, it has not looked."""
    if path is None:
        return []
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    rows = doc.get("rows", doc if isinstance(doc, list) else [])
    for i, r in enumerate(rows):
        pre = r.get("prefix")
        if not isinstance(pre, str) or not pre:
            raise ValueError(f"carry-ledger row {i}: `prefix` missing — a row must "
                             f"name the masses it covers")
        v = r.get("verdict")
        if v == "pending":
            raise ValueError(f"carry-ledger `{pre}`: verdict 'pending' is refused by "
                             f"name — a mass carried by nothing is either being "
                             f"fixed, signed as a gap, or unresolved and dated")
        if v not in VERDICTS:
            raise ValueError(f"carry-ledger `{pre}`: verdict {v!r} must be one of "
                             f"{VERDICTS}")
        if not r.get("why"):
            raise ValueError(f"carry-ledger `{pre}`: `why` missing — what is holding "
                             f"it up in the real world, or nothing is")
        if not r.get("since"):
            raise ValueError(f"carry-ledger `{pre}`: `since` missing — an unfixed "
                             f"defect must print its own age")
        if v in ("fix", "unresolved") and not r.get("restart_by"):
            raise ValueError(f"carry-ledger `{pre}`: verdict {v!r} needs `restart_by` "
                             f"— a named builder action, or it is not a debt, it is "
                             f"a shrug")
        if v == "signed-gap" and not r.get("signed_by"):
            raise ValueError(f"carry-ledger `{pre}`: a signed gap must cite the order "
                             f"or decision that signed it (`signed_by`)")
        if not isinstance(r.get("covers_n"), int) or r["covers_n"] < 1:
            raise ValueError(f"carry-ledger `{pre}`: `covers_n` must be the integer "
                             f"count this row was written against — without it a "
                             f"prefix hides every new instance that joins it")
    return rows


def check(objs, ledger, tol=CONTACT_TOL_MM):
    """(violations, notes, summary). Pure."""
    rel = relations(objs, tol)
    how, col = carriers(objs, rel, tol)
    unc = [o for o in objs if how[o["name"]] is None]
    names = [o["name"] for o in unc]
    in_frame = [o for o in unc if o.get("in_frustum")]

    viol, notes = [], []
    covered = set()
    for r in ledger:
        pre = r["prefix"]
        hit = [n for n in names if n.startswith(pre)]
        covered |= set(hit)
        age = r.get("since", "?")
        if not hit:
            viol.append(f"LEDGER STALE `{pre}` ({r['verdict']}, since {age}) — the "
                        f"scene carries every mass this row covers. A row for a "
                        f"defect that no longer exists is a queue nobody empties: "
                        f"delete it in the commit that fixed it.")
            continue
        if len(hit) > r["covers_n"]:
            viol.append(f"LEDGER BACKLOG ROSE `{pre}`: {len(hit)} uncarried now vs "
                        f"covers_n={r['covers_n']} when the row was written "
                        f"({age}) — the row is hiding {len(hit) - r['covers_n']} "
                        f"new instance(s). Re-triage, do not re-count.")
            continue
        notes.append(f"  ledger {r['verdict']:<11} {len(hit):>2}/{r['covers_n']} "
                     f"since {age}  `{pre}`")
    for o in unc:
        if o["name"] in covered:
            continue
        d = _dims(o)
        viol.append(f"UNCARRIED {'[IN FRAME] ' if o.get('in_frustum') else ''}"
                    f"{o['name']} — {d[0]:.0f}x{d[1]:.0f}x{d[2]:.0f} mm at "
                    f"z {o['min'][2]:.0f}..{o['max'][2]:.0f}: nothing in this scene "
                    f"can hand its weight to the ground. Touches "
                    f"{sum(1 for p in objs if p is not o and touches(o, p, tol))} "
                    f"mass(es), carries-relation to none of them.")
    summary = {"meshes": len(objs), "columns": len(col), "uncarried": len(unc),
               "uncarried_in_frame": len(in_frame), "rowed": len(covered),
               "rows": len(ledger), "violations": len(viol)}
    return viol, notes, summary


def one_line(s):
    return (f"CARRY: {s['meshes']} drawn masses, {s['columns']} standing on the "
            f"ground; {s['uncarried']} carried by nothing "
            f"({s['uncarried_in_frame']} in frame), {s['rowed']} of them rowed in "
            f"{s['rows']} ledger row(s)")


# --------------------------------------------------------------- selftest

def _b(name, x0, y0, z0, dx, dy, dz, frustum=True):
    return {"name": name, "min": [x0, y0, z0],
            "max": [x0 + dx, y0 + dy, z0 + dz], "in_frustum": frustum}


def selftest():
    """Controls, POSITIVE AND NEGATIVE, on the exact geometry that earned the file.
    A rung whose pass is 'we found nothing' must show it can fire (D-056)."""
    fails = []

    def want(cond, msg):
        if not cond:
            fails.append(msg)

    floor = _b("floor", 0, 0, -100, 4000, 3000, 100)
    gable_l = _b("gable_l", 0, 0, 0, 18, 600, 2400)
    gable_r = _b("gable_r", 1000, 0, 0, 18, 600, 2400)
    # (1) THE DEFECT, exactly as p2r84 measured it: 40 mm short at both ends.
    short = _b("rail_short", 58, 270, 1850, 924, 30, 30)
    how, _ = carriers([floor, gable_l, gable_r, short])
    want(how["rail_short"] is None, "a rail 40 mm short of both gables must be UNCARRIED")
    want(how["floor"] == "GROUND" and how["gable_l"] == "RESTS-ON",
         "the slab is the ground and the gables stand on it")
    # (2) THE FIX: the same rail landing 2 mm into each gable.
    land = _b("rail_land", 16, 270, 1850, 1006, 30, 30)
    how, _ = carriers([floor, gable_l, gable_r, land])
    want(how["rail_land"] == "ANCHORED-TO", "a rail that dies into its gables is carried")
    # (3) THE HOLE THIS FILE EXISTS TO CLOSE: the coat must not hold up the rail.
    coat = _b("coat", 300, 200, 1000, 400, 140, 890)          # hanger reaches over the rail
    coat["max"][2] = 1890                                     # hook crown just above it
    how, _ = carriers([floor, gable_l, gable_r, short, coat])
    want(how["rail_short"] is None,
         "a rail excused by the garment hanging on it is the hole, not a pass")
    want(how["coat"] is None, "a coat on a floating rail is itself floating")
    # (4) ... and on a rail that IS carried, the same coat hangs.
    how, _ = carriers([floor, gable_l, gable_r, land, coat])
    want(how["coat"] == "HUNG-ON", "a coat on a landed rail hangs on it")
    want(how["rail_land"] == "ANCHORED-TO", "the coat never becomes the rail's carrier")
    # (5) a wall is not a rail: a mass overlapping a wall must not read as HUNG-ON.
    wall = _b("wall", 0, 0, 0, 6000, 110, 2800)
    want(member_axis(wall) is None, "a 6000x110x2800 wall is not a member")
    want(member_axis(short) == 0, "a 924x30x30 rail is a member on x")
    shelf = _b("shelf", 0, 0, 0, 650, 600, 18)
    want(member_axis(shelf) is None, "a 650x600x18 shelf is not a member")
    # (6) the relations that keep correct construction out of the report
    book = _b("book", 100, 100, 18, 150, 200, 220)
    how, _ = carriers([floor, _b("shelf2", 0, 0, 0, 650, 600, 18), book])
    want(how["book"] == "RESTS-ON", "a book on a shelf rests on it")
    trim = _b("trim", 500, 500, 2794, 96, 96, 6)
    ceil = _b("ceil", 0, 0, 2800, 4000, 3000, 50)
    how, _ = carriers([floor, wall, ceil, trim])
    want(how["trim"] == "HANGS-FROM", "a trim flush under a soffit hangs from it")
    front = _b("front", 20, 0, 60, 400, 20, 200)
    body = _b("body", 20, 20, 0, 400, 500, 700)
    how, _ = carriers([floor, front, body])
    want(how["front"] == "FASTENED-TO", "a drawer front sharing its box's face is fastened")
    # (7) the ledger refuses what it must refuse
    for bad, why in (({"prefix": "x", "verdict": "pending", "why": "w", "since": "d",
                       "covers_n": 1}, "pending"),
                     ({"prefix": "x", "verdict": "fix", "why": "w", "since": "d",
                       "covers_n": 1}, "fix with no restart_by"),
                     ({"prefix": "x", "verdict": "fix", "why": "w", "since": "d",
                       "restart_by": "r"}, "no covers_n")):
        try:
            load_ledger_rows([bad])
            fails.append(f"ledger accepted a row it must refuse: {why}")
        except ValueError:
            pass
    for f in fails:
        print(f"  !! SELFTEST {f}")
    print(f"carry_check selftest: {'PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def load_ledger_rows(rows):
    """`load_ledger`'s validation, on rows already in memory (selftest + tests)."""
    import tempfile
    fd, p = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"rows": rows}, f)
        return load_ledger(p)
    finally:
        os.unlink(p)


# --------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dump", nargs="?", help="room_*.scene.json written by scene_dump")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.dump:
        print("usage: carry_check.py <scene.json> [--ledger <path>]")
        return 2
    led = a.ledger
    if led is None:
        repo = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        cand = os.path.join(repo, "qa", "carry-ledger.json")
        led = cand if os.path.exists(cand) else None
    try:
        objs = load_dump(a.dump)
    except (OSError, ValueError) as e:
        print(f"CARRY: COULD NOT RUN — {e}")
        return 2
    try:
        ledger = load_ledger(led)
    except (OSError, ValueError) as e:
        print(f"CARRY: COULD NOT RUN — ledger unreadable ({e}). A gate whose ledger "
              f"cannot be read has not passed; it has not looked.")
        return 2
    viol, notes, summary = check(objs, ledger)
    if a.json:
        print(json.dumps({"summary": summary, "violations": viol, "notes": notes},
                         indent=1, ensure_ascii=False))
        return 1 if viol else 0
    print(one_line(summary))
    for n in notes:
        print(n)
    for v in viol:
        print(f"  !! {v}")
    if not viol:
        print("  -> OK: every drawn mass has a load path to the ground, or a row "
              "that names what is being done about it")
    return 1 if viol else 0


if __name__ == "__main__":
    sys.exit(main())
