#!/usr/bin/env python3
"""dim_check.py — BUILT dimensions vs WORLD standards. Pure python, no bpy (layer law).

Run:  python dim_check.py <room_*.scene.json> [--deficits qa/dim-deficits.json]

WHY THIS EXISTS (ORD-2026-08-22-front-door-dims, owner "ลุย" on the advice of
2026-08-22, docs/owner-advice-2026-08-22.md). Measured that morning: of 28 rungs the
render gate ran, 3 compared anything to a world standard, 1 of those blocked, and
0 asked whether a built object was the size of the real thing it claims to be. The
knowledge to ask sat on disk 46 days (ergonomics_ref.nearest_bed_size would have
failed the p2r52 mattress by 336 mm) with no path from the BUILT scene to it. Three
of the owner's eye-catches are this one defect class: the bed at 0.58x (08-18), the
garment rails at 570-637 mm vs a real shirt's 700-760 (08-12), the nightstand datum
proportion (08-22). ADMISSION per D-112: ordered by the owner; gives an instrument
to a defect class only his eye could see; extends asset_scale, whose own docstring
names the gap ("a child's shirt and an adult's are both inside any band wide enough
to be useful" — it asserts the UNIT, this rung asserts the SIZE, post-fit).

WHAT IT JUDGES (v1 — every rule cites its source; a class with no world band prints
as UNJUDGED, never as clear, and never exempts by omission — R9b's no-allowlist law):
  bed          acquired cluster (bed__*__acq*) plan union vs standard mattress tables
               (US Panero & Zelnik + Thai retail, ergonomics_ref; tol 150 mm because
               the cluster includes the frame — the ±50 knowledge rule is for bare
               mattresses; D-110 records the owner's own size tolerance as loose)
  garment_rail per-rail shell-cluster z-span vs a real adult garment: floor 700 mm
               (shirt 700-760, ORD-2026-08-12's own measured numbers), ceiling
               1900 mm (long coat + drop, asset_scale garment_hung upper bound)
  side_table   top height vs ergonomics side/end table band 380-480 (+/-25 general
               tolerance — comfort bands, brand variance)
  bench        seat top vs seat-height band 400-450 (+/-25), knowledge/ergonomics
               tv-viewing-and-furniture-dimensions.md seat row

THREE STATES (the R13 third state — never an opt-in flag): ok / interim / fail.
A deficit already ordered or decided in a register (qa/dim-deficits.json row citing
an ORD-/D- id that reproduces in that register) prints LOUDLY with its age and does
not stop the build — but only down to its signed_down_to_mm floor: a signature
covers the deficit it names, never every future worse instance (CLASS != INSTANCE).

EXIT CODES (R11 contract): 0 = judged, no fail (interim prints loudly); 1 = a fail
with no signature; 2 = COULD NOT RUN (unreadable dump, or zero judgeable masses —
grammar drift must never read as a clean frame). Last line always "DIMS: ...".
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ergonomics_ref as ERGO  # noqa: E402  (stdlib-only, pure)

DIM_CHECK_VERSION = "1.0 (2026-08-22)"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFICITS_REL = os.path.join("qa", "dim-deficits.json")
REGISTERS = (os.path.join("qa", "owner-orders.json"),
             os.path.join("qa", "open-decisions.json"))

GENERAL_TOL_MM = 25            # comfort bands are ranges, not points (D-115)
GARMENT_LEN_MM = (700, 1900)   # shirt floor (ORD-2026-08-12) .. long-coat ceiling
SIDE_TABLE_TOP_MM = ERGO.TABLE_H_MM["side_table"]          # (380, 480)
BENCH_SEAT_TOP_MM = (400, 450)  # knowledge/ergonomics tv-viewing md, seat row

_GARMENT = re.compile(r"^mill__style_garment")


def _mm(v):
    return round(v * 1000.0)


def _plan_union(objs):
    lo0 = min(o["aabb"][0][0] for o in objs); hi0 = max(o["aabb"][1][0] for o in objs)
    lo1 = min(o["aabb"][0][1] for o in objs); hi1 = max(o["aabb"][1][1] for o in objs)
    return _mm(hi0 - lo0), _mm(hi1 - lo1)


def _z_span(objs):
    lo = min(o["aabb"][0][2] for o in objs); hi = max(o["aabb"][1][2] for o in objs)
    return _mm(hi - lo)


def _top(objs):
    return _mm(max(o["aabb"][1][2] for o in objs))


def load_deficits(root=REPO, path=None):
    """Signed deficits: a row counts only if its cited ORD-/D- id reproduces in the
    register it points at — a signature nobody can find was never given. Unreadable
    file loses every signature (fails CLOSED: violations harden, never soften)."""
    p = path or os.path.join(root, DEFICITS_REL)
    if not os.path.isfile(p):
        return [], None
    try:
        with open(p, encoding="utf-8") as f:
            rows = json.load(f).get("rows", [])
    except Exception as e:                                  # noqa: BLE001
        return [], f"deficit register unreadable ({e}) — signatures LOST, fails stand"
    reg_text = ""
    for rel in REGISTERS:
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                reg_text += f.read()
        except Exception:                                   # noqa: BLE001
            pass
    good = [r for r in rows
            if r.get("cite") and r["cite"] in reg_text
            and r.get("id") and r.get("since")]
    dropped = [r.get("id", "?") for r in rows if r not in good]
    note = (f"deficit rows dropped (cite not found in a register): {dropped}"
            if dropped else None)
    return good, note


def _sig(deficits, cls, measured_mm):
    for r in deficits:
        if r.get("class") != cls:
            continue
        floor = r.get("signed_down_to_mm")
        if floor is not None and measured_mm < floor:
            return None   # worse than what was signed — the signature does not stretch
        return r
    return None


def check(dump, deficits):
    """Returns (findings, unjudged) — findings rows carry state ok|interim|fail."""
    objs = [o for o in dump.get("objects", []) if not o.get("hidden_render")]
    findings = []

    bed = [o for o in objs if o["name"].startswith("bed__") and "__acq" in o["name"]]
    if bed:
        w, d = _plan_union(bed)
        name, (sw, sl), ok, worst = ERGO.nearest_bed_size(w, d)
        f = {"cls": "bed", "what": f"acq cluster {w}x{d} mm",
             "band": f"~ {name} {sw}x{sl} (worst {worst:.0f} mm, tol "
                     f"{ERGO.BED_SIZE_TOL_MM})", "measured": min(w, d)}
        f["state"] = "ok" if ok else "fail"
        if not ok:
            f["why"] = "no standard mattress within tolerance — the p2r52 defect class"
        findings.append(f)

    rails = {}
    for o in objs:
        if _GARMENT.match(o["name"]):
            key = o["name"].split("__")[1].rsplit("_", 1)[0]
            rails.setdefault(key, []).append(o)
    for key in sorted(rails):
        z = _z_span(rails[key])
        lo, hi = GARMENT_LEN_MM
        f = {"cls": "garment_rail", "what": f"{key} z-span {z} mm",
             "band": f"{lo}-{hi} (shirt 700-760, ORD-2026-08-12)", "measured": z}
        f["state"] = "ok" if lo <= z <= hi else "fail"
        if f["state"] == "fail":
            f["why"] = "reads as the DOLL tell — length below a real adult garment"
        findings.append(f)

    for o in objs:
        if o["name"].startswith("side_table__"):
            t = _top([o])
            lo, hi = SIDE_TABLE_TOP_MM
            f = {"cls": "side_table", "what": f"{o['name']} top {t} mm",
                 "band": f"{lo}-{hi} +/-{GENERAL_TOL_MM}", "measured": t}
            f["state"] = ("ok" if lo - GENERAL_TOL_MM <= t <= hi + GENERAL_TOL_MM
                          else "fail")
            if f["state"] == "fail":
                f["why"] = "outside the ergonomic side-table band"
            findings.append(f)

    bench = [o for o in objs if o["name"].startswith("bench__")]
    if bench:
        t = _top(bench)
        lo, hi = BENCH_SEAT_TOP_MM
        f = {"cls": "bench", "what": f"seat top {t} mm",
             "band": f"{lo}-{hi} +/-{GENERAL_TOL_MM}", "measured": t}
        f["state"] = ("ok" if lo - GENERAL_TOL_MM <= t <= hi + GENERAL_TOL_MM
                      else "fail")
        if f["state"] == "fail":
            f["why"] = "outside the seat-height band"
        findings.append(f)

    for f in findings:
        if f["state"] == "fail":
            sig = _sig(deficits, f["cls"], f["measured"])
            if sig:
                f["state"] = "interim"
                f["sig"] = sig

    judged_names = set()
    for o in objs:
        n = o["name"]
        if ((n.startswith("bed__") and "__acq" in n) or _GARMENT.match(n)
                or n.startswith("side_table__") or n.startswith("bench__")):
            judged_names.add(n)
    rest = [o for o in objs if o["name"] not in judged_names]
    sheet_governed = sum(1 for o in rest if o["name"].startswith("mill__")
                         and not o["name"].startswith("mill__style_"))
    unjudged = {"masses": len(rest), "sheet_governed": sheet_governed}
    return findings, unjudged


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # noqa: BLE001
        pass
    args = [a for a in argv if not a.startswith("--")]
    dpath = None
    if "--deficits" in argv:
        dpath = argv[argv.index("--deficits") + 1]
    if not args:
        print("DIMS: COULD NOT RUN — no scene dump given")
        return 2
    try:
        with open(args[0], encoding="utf-8") as f:
            dump = json.load(f)
    except Exception as e:                                  # noqa: BLE001
        print(f"DIMS: COULD NOT RUN — dump unreadable ({e}); could-not-look must "
              f"never print like looked-and-fine")
        return 2
    deficits, dnote = load_deficits(path=dpath)
    print(f"DIM-CHECK v{DIM_CHECK_VERSION} — built dims vs WORLD standards "
          f"(admitted per D-112: owner order 2026-08-22 'ลุย'; the class only his "
          f"eye had an instrument for)")
    if dnote:
        print(f"  !! {dnote}")
    findings, unjudged = check(dump, deficits)
    if not findings:
        print("DIMS: COULD NOT RUN — zero judgeable masses in this dump (name "
              "grammar drift?); nothing judged must never read as nothing wrong")
        return 2
    n = {"ok": 0, "interim": 0, "fail": 0}
    for f in findings:
        n[f["state"]] += 1
        if f["state"] == "ok":
            continue
        line = f"  {f['state'].upper()} {f['cls']}: {f['what']} vs {f['band']}"
        if f.get("why"):
            line += f" — {f['why']}"
        if f.get("sig"):
            s = f["sig"]
            line += (f" [signed {s['id']} since {s['since']} citing {s['cite']}"
                     f" — prints until cleared, floor {s.get('signed_down_to_mm')}]")
        print(line)
    ok_lines = [f for f in findings if f["state"] == "ok"]
    for f in ok_lines[:6]:
        print(f"  ok {f['cls']}: {f['what']} vs {f['band']}")
    if len(ok_lines) > 6:
        print(f"  ok ... {len(ok_lines) - 6} more")
    print(f"  unjudged: {unjudged['masses']} masses carry no world band "
          f"({unjudged['sheet_governed']} of them sheet-governed millwork — R12's "
          f"jurisdiction); they print, they never pass silently")
    print(f"DIMS: {len(findings)} judged — ok {n['ok']} · interim {n['interim']} · "
          f"fail {n['fail']} · unjudged {unjudged['masses']}")
    return 1 if n["fail"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
