#!/usr/bin/env python3
"""sheet_recon.py — DRW-1: reconcile what the DRAWING draws against what the BUILD built.

WHY (owner, 2026-08-11, after the headboard round): the repo had two readers of one
drawing — plan_cluster (complete by construction, floor2 lane, 2026-07-05) and the
element derivations the canonical spec was built from — and the build consumed only
the second. Nothing reconciled them, so an element the sheet draws could vanish from
the build with nothing failing. The headboard did, for three weeks, past eight blind
critic voices. This file is the bridge: every drawn mass is MATCHED to a built
assembly, or carries a human-signed DECLARED GAP, or prints as UNRESOLVED and fails
the gate.

TWO-LAYER LAW (plan-extraction lane, unchanged): the machine verifies COMPLETENESS
and refreshes matches; IDENTITY (what a drawn rect IS) and GAPS are human-signed
fields this code never invents. Verdicts are RECOMPUTED on every run from the
current scene dump — a match that disappears un-matches itself (the door re-runs,
debt_check's law).

THE DRAWING OF RECORD is the snapshot in 00_intake (D-036): the owner states the
source file has since changed with no per-piece backup, so this PDF outranks any
"current" version and every derived doc of ours.

COORDINATE FRAME: sheet-mm floor coords == build world metres x1000 (verified: the
canonical spec's rects reproduce in the p2r11 dump aabbs to the wall-skin ~5mm).
`_frames_agree` asserts this on every run and exits 2 rather than reconciling in a
broken frame.

EXIT CODES ARE A CONTRACT (R11): 0 = no blocking row · 1 = a drawn mass in (or
possibly in) the camera frustum is UNRESOLVED · 2 = COULD NOT RUN, which must never
print like "looked and it was fine". Frustum UNKNOWN blocks — ignorance is not
clearance.

    python pipeline/scripts/sheet_recon.py --recon <scene.json>   # full table + refresh ledger
    python pipeline/scripts/sheet_recon.py --gate  <scene.json>   # one line + exit code
    python pipeline/scripts/sheet_recon.py --gate  <scene.json> --no-save   # render path
    python pipeline/scripts/sheet_recon.py --extract              # fresh ink vs roster (needs fitz)

--no-save RECOMPUTES every verdict exactly as usual and simply does not write the
ledger back. The render path uses it because this is the only checker a build
spawns that writes a tracked file: ledger churn would land in every unrelated diff
and would race the other sessions live on this repo. The refusal is unchanged; only
the write is dropped.

Pure python, no bpy (layer law). --extract lazy-imports plan_cluster (fitz/scipy).
"""
import json
import os
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = os.path.join(REPO, "qa", "sheet-recon.json")

# Matching knobs. Coverage is ASYMMETRIC on purpose: the question is "is the drawn
# thing covered by built stuff", not symmetric similarity — a bed drawn 2.1x2.0 m and
# built 2.0x2.15 m must match. The ratio cap is what stops the floor (50 m2) from
# covering everything: an assembly more than RATIO_MAX x the drawn area is scenery,
# not the object. Floor vs bed is 12x — the cap must sit well under that.
COVER_MIN = 0.55
RATIO_MAX = 6.0
# A drawn loose-furniture symbol is floor-standing; an assembly that BEGINS above
# this height (pelmet, downlight trim) may cover the same plan rect and is not it.
FLOOR_STAND_ZMIN_M = 1.2
ADJ_MM = 25.0        # parts whose inflated plan rects touch are one assembly


# ---------------------------------------------------------------- geometry (pure) --
def _overlap_1d(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def rect_overlap_area(r, s):
    """r,s = (x, y, w, d) in mm."""
    return (_overlap_1d(r[0], r[0] + r[2], s[0], s[0] + s[2])
            * _overlap_1d(r[1], r[1] + r[3], s[1], s[1] + s[3]))


def rect_intersects_convex_poly(rect, poly):
    """Axis-aligned rect (x,y,w,d) vs convex polygon [[x,y],...], same units.
    Separating-axis test: axes = rect's two + each polygon edge normal."""
    if not poly or len(poly) < 3:
        return None
    rx = (rect[0], rect[0] + rect[2])
    ry = (rect[1], rect[1] + rect[3])
    px = [p[0] for p in poly]
    py = [p[1] for p in poly]
    if max(px) < rx[0] or min(px) > rx[1] or max(py) < ry[0] or min(py) > ry[1]:
        return False
    corners = [(rx[0], ry[0]), (rx[1], ry[0]), (rx[1], ry[1]), (rx[0], ry[1])]
    n = len(poly)
    for i in range(n):
        ex = poly[(i + 1) % n][0] - poly[i][0]
        ey = poly[(i + 1) % n][1] - poly[i][1]
        ax, ay = -ey, ex                       # edge normal
        pmin = min(p[0] * ax + p[1] * ay for p in poly)
        pmax = max(p[0] * ax + p[1] * ay for p in poly)
        rmin = min(c[0] * ax + c[1] * ay for c in corners)
        rmax = max(c[0] * ax + c[1] * ay for c in corners)
        if rmax < pmin or rmin > pmax:
            return False
    return True


# ------------------------------------------------------------- built-side (pure) --
def _prefix(name):
    return name.split("__")[0] if "__" in name else name


def assemblies_from_dump(objects, adj_mm=ADJ_MM):
    """Group drawable meshes into ASSEMBLIES: same name prefix, then split into
    spatially-connected components (a prefix is not enough — `nightstand` names two
    separate pieces at opposite ends of the bed, and a union across both would be a
    phantom slab that matches the bed's cluster instead of either nightstand).
    Returns [{name, rect_mm, part_rects, footprint_m2, zmin_m, zmax_m, parts,
    part_recs, in_frustum}]. rect_mm is the union BBOX (display only — matching
    walks part_rects, see match_row); footprint_m2 is the SUM of part plan areas.
    in_frustum True if ANY part reads in-frustum, None if the dump predates it."""
    groups = {}
    for r in objects:
        if r.get("hidden_render") or "aabb" not in r:
            continue
        groups.setdefault(_prefix(r["name"]), []).append(r)

    out = []
    for key, parts in groups.items():
        n = len(parts)
        parent = list(range(n))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        rects = []
        for p in parts:
            (x0, y0, _z0), (x1, y1, _z1) = p["aabb"][0], p["aabb"][1]
            rects.append((x0 * 1000.0, y0 * 1000.0,
                          (x1 - x0) * 1000.0, (y1 - y0) * 1000.0))
        for i in range(n):
            gi = (rects[i][0] - adj_mm, rects[i][1] - adj_mm,
                  rects[i][2] + 2 * adj_mm, rects[i][3] + 2 * adj_mm)
            for j in range(i + 1, n):
                if rect_overlap_area(gi, rects[j]) > 0:
                    parent[find(i)] = find(j)

        comps = {}
        for i in range(n):
            comps.setdefault(find(i), []).append(i)
        for idxs in comps.values():
            xs0 = min(rects[i][0] for i in idxs)
            ys0 = min(rects[i][1] for i in idxs)
            xs1 = max(rects[i][0] + rects[i][2] for i in idxs)
            ys1 = max(rects[i][1] + rects[i][3] for i in idxs)
            zmin = min(parts[i]["aabb"][0][2] for i in idxs)
            zmax = max(parts[i]["aabb"][1][2] for i in idxs)
            fr = [parts[i].get("in_frustum") for i in idxs]
            in_fr = True if any(v is True for v in fr) else (
                None if any(v is None for v in fr) else False)
            nm = key if len(comps) == 1 else f"{key}@{int(xs0)},{int(ys0)}"
            prs = [rects[i] for i in idxs]
            out.append({"name": nm, "rect_mm": (xs0, ys0, xs1 - xs0, ys1 - ys0),
                        "part_rects": prs,
                        "footprint_m2": sum(r[2] * r[3] for r in prs) / 1e6,
                        "zmin_m": zmin, "zmax_m": zmax,
                        "parts": sorted(parts[i]["name"] for i in idxs),
                        "part_recs": [parts[i] for i in idxs],
                        "in_frustum": in_fr})
    return out


# ---------------------------------------------------------------- matching (pure) --
GRID_N = 40      # rasterization of the drawn rect for footprint coverage


def coverage_by_parts(rect, part_rects, grid_n=GRID_N):
    """Fraction of the drawn rect covered by the UNION of part rects, on a grid.
    The first live run matched a bed to an L-shaped millwork run because coverage
    was computed against the assembly's union BBOX — an L's bbox includes the empty
    interior it wraps. Footprint coverage cannot be fooled that way, and a grid is
    exact enough (2.5% cells) without polygon union code."""
    x0, y0, w, d = rect
    if w <= 0 or d <= 0 or not part_rects:
        return 0.0
    hit = 0
    for i in range(grid_n):
        cx = x0 + (i + 0.5) * w / grid_n
        for j in range(grid_n):
            cy = y0 + (j + 0.5) * d / grid_n
            for p in part_rects:
                if p[0] <= cx <= p[0] + p[2] and p[1] <= cy <= p[1] + p[3]:
                    hit += 1
                    break
    return hit / (grid_n * grid_n)


def match_row(row, assemblies):
    """Top candidates by drawn-rect FOOTPRINT coverage, at two granularities:
    whole assemblies and single parts. The part tier exists because a small drawn
    band (a 60mm headboard panel) is legitimately one PART of a much larger
    assembly — an area-ratio cap that protects loose items from being 'matched' by
    the floor would otherwise hide the covering part entirely (first live run:
    SR-18 read cov=0.00 while bed__headboard sat exactly on it). Ratio caps apply
    to the candidate's own FOOTPRINT, never to its bbox."""
    rect = row["rect_mm"]
    ra = max(rect[2] * rect[3], 1.0) / 1e6            # m2
    floor_standing = bool(row.get("floor_standing"))
    cands = []
    for a in assemblies:
        tiers = [("assembly", a["name"], a["part_rects"], a["footprint_m2"],
                  a["zmin_m"], a["zmax_m"], a["in_frustum"])]
        for pr, rec in zip(a["part_rects"], a["part_recs"]):
            tiers.append(("part", f"{a['name']}/{rec['name']}", [pr],
                          pr[2] * pr[3] / 1e6,
                          rec["aabb"][0][2], rec["aabb"][1][2],
                          rec.get("in_frustum")))
        for kind, name, prs, foot, zmin, zmax, in_fr in tiers:
            if foot > RATIO_MAX * ra:
                continue
            if floor_standing and zmin > FLOOR_STAND_ZMIN_M:
                continue
            cov = coverage_by_parts(rect, prs)
            if cov > 0.05:
                cands.append({"assembly": name, "kind": kind,
                              "coverage": round(cov, 3),
                              "footprint_m2": round(foot, 3),
                              "in_frustum": in_fr,
                              "_lowrise": floor_standing and zmax < 0.15})
    # ties: a rug under a bed covers the bed's rect as fully as the bed does —
    # prefer the candidate that actually RISES for a floor-standing symbol, then
    # the tighter footprint (naming precision, not verdict: both clear COVER_MIN).
    cands.sort(key=lambda c: (-c["coverage"], c["_lowrise"], c["footprint_m2"]))
    seen, uniq = set(), []
    for c in cands:
        if c["assembly"] not in seen:
            seen.add(c["assembly"])
            uniq.append(c)
    uniq = uniq[:3]
    # display promotion: if the top slot is a LOW-RISE surface (rug/mat) but a
    # rising candidate also clears COVER_MIN, the rising one is the named match —
    # a floor symbol names the thing standing there, not what it stands on.
    if uniq and uniq[0]["_lowrise"]:
        for i, c in enumerate(uniq[1:], 1):
            if not c["_lowrise"] and c["coverage"] >= COVER_MIN:
                uniq.insert(0, uniq.pop(i))
                break
    for c in uniq:
        c.pop("_lowrise", None)
    return uniq


def verdict_of(row, built_names=None, order_ids=None):
    """matched | declared_gap | superseded | UNRESOLVED.

    SUPERSEDED is the fourth state, added 2026-08-24, because the ledger had no
    honest way to say "built, and deliberately somewhere else". A LATER owner
    order can move a drawn piece -- the hug (ORD-2026-08-22-bed-standard-size-hug)
    moved both nightstands off their drawn rects -- and with only three states such
    a row can be `matched` (a lie), `declared_gap` (a lie the other way: it says the
    drawn thing was NOT built), or UNRESOLVED forever. A rung that is red on every
    render is a rung somebody switches off, and the rows' own note had already
    named what they must not become: a silent `matched`.

    It is the strictest state in this file, on purpose -- it is the only one that
    lets a drawn mass leave its rect and still clear the gate:
      * `by_order` must name an order id that EXISTS in qa/owner-orders.json.
        A displacement nobody ordered is not superseded, it is drift.
      * `built_as` must name an assembly (or part) PRESENT IN THIS FRAME'S dump.
        This is the anti-hiding guard and the whole reason the state is safe to
        add: `declared_gap` asserts the thing is absent, so `superseded` has to
        prove the thing is present somewhere else. Without that proof, "we moved
        it" becomes the place "we lost it" hides -- which is the exact defect
        DRW-1 was built for (the headboard vanished for three weeks past eight
        critic voices).
      * reason + decided_by, with `pending` refused by name, as everywhere else.
    """
    m = row.get("match") or {}
    best = (m.get("candidates") or [{}])[0] if m.get("candidates") else {}
    matched = best.get("coverage", 0.0) >= COVER_MIN
    sup = row.get("superseded")
    if matched and row.get("gap"):
        return "matched", "STALE GAP: a gap is declared but the object is built"
    if matched and sup:
        return "matched", ("STALE SUPERSESSION: the drawn rect is covered again -- "
                           "the piece came back, so the supersession is spent")
    if matched:
        return "matched", None
    if sup:
        if (not sup.get("reason") or not sup.get("decided_by")
                or sup.get("decided_by") == "pending"):
            return "UNRESOLVED", ("superseded row missing reason/decider "
                                  "('pending' is refused)")
        oid = sup.get("by_order")
        if not oid:
            return "UNRESOLVED", ("superseded row names no by_order -- a "
                                  "displacement nobody ordered is drift")
        if order_ids is not None and oid not in order_ids:
            return "UNRESOLVED", (f"superseded by_order '{oid}' is not an order in "
                                  f"qa/owner-orders.json")
        built = sup.get("built_as")
        if not built:
            return "UNRESOLVED", ("superseded row names no built_as -- it must "
                                  "point at the thing that IS built")
        if built_names is not None and built not in built_names:
            return "UNRESOLVED", (f"superseded built_as '{built}' is not in this "
                                  f"frame -- 'moved' is never where 'lost' hides")
        return "superseded", None
    if row.get("gap"):
        g = row["gap"]
        if not g.get("reason") or not g.get("decided_by") or g.get("decided_by") == "pending":
            return "UNRESOLVED", "gap row missing reason/decider ('pending' is refused)"
        return "declared_gap", None
    return "UNRESOLVED", None


def _order_ids():
    """Ids in qa/owner-orders.json, or None when it cannot be read. None SKIPS the
    by_order membership check rather than passing it -- the row still has to carry
    built_as + reason + decider, so an unreadable orders file weakens this rung
    without ever turning it green by accident."""
    try:
        with open(os.path.join(REPO, "qa", "owner-orders.json"), encoding="utf-8") as f:
            return {o.get("id") for o in (json.load(f).get("orders") or [])}
    except (OSError, ValueError):
        return None


def built_names_from(asm):
    """Every name a `built_as` may legally point at: the assembly name, the
    `assembly/part` path this module prints in its candidate rows, and THE BARE
    MESH NAME.

    The bare name is the one a signature should use, and the reason is R9's law
    about coordinates. An assembly name is `key` only while that prefix forms one
    spatial component; the moment it splits -- which is exactly what two
    nightstands at opposite ends of a bed do -- the name becomes
    `side_table@4803,2005`, i.e. it EMBEDS THE POSITION. Signing `built_as`
    against that would mean a supersession went stale every time the piece it
    describes moved a millimetre, so the rung would be red on every render, and a
    rung that is red on every render is a rung somebody switches off (R13). A mesh
    name says WHAT the thing is; a coordinate says where it happened to be.
    """
    names = set()
    for a in asm:
        names.add(a["name"])
        for rec in a["part_recs"]:
            names.add(rec["name"])
            names.add(f"{a['name']}/{rec['name']}")
    return names


def row_in_frustum(row, floor_poly_mm):
    """Drawn-side frustum: the drawn rect vs the camera's floor polygon when the
    dump carries one; else fall back to the best candidate assembly's own flag;
    else UNKNOWN (None) — which BLOCKS, because 'could not look' must never read
    like 'looked and it was clear'."""
    if floor_poly_mm:
        return rect_intersects_convex_poly(row["rect_mm"], floor_poly_mm)
    m = row.get("match") or {}
    if m.get("candidates"):
        return m["candidates"][0].get("in_frustum")
    return None


def reconcile(rows, dump, frame_name, today=None):
    """Refresh every row's MACHINE half in place; returns (rows, summary)."""
    objects = dump["objects"]
    asm = assemblies_from_dump(objects)
    cam = dump.get("camera") or {}
    poly = cam.get("floor_poly_mm")
    n_match = n_gap = n_sup = n_unres = n_block = 0
    names = built_names_from(asm)
    oids = _order_ids()
    for row in rows:
        cands = match_row(row, asm)
        row["match"] = {"frame": frame_name, "candidates": cands,
                        "checked": today or date.today().isoformat()}
        fr = row_in_frustum(row, poly)
        row["match"]["in_frustum"] = fr
        v, warn = verdict_of(row, built_names=names, order_ids=oids)
        row["verdict"] = v
        row["warning"] = warn
        if v == "matched":
            n_match += 1
        elif v == "declared_gap":
            n_gap += 1
        elif v == "superseded":
            n_sup += 1
        else:
            n_unres += 1
            if fr is not False:
                n_block += 1
    return rows, {"drawn": len(rows), "matched": n_match, "gaps": n_gap,
                  "superseded": n_sup, "unresolved": n_unres, "blocking": n_block,
                  "frustum_source": "floor_poly" if poly else "assembly-flag/unknown"}


# ----------------------------------------------------------------- frame check --
def _frames_agree(rows, dump):
    """The whole recon rides on sheet-mm == world-m x1000. Cheap assert: the dump's
    global plan bbox must land within 1 m of the roster's. A transform drift fails
    to 2 (could-not-run), never to a table full of confident mismatches."""
    xs, ys = [], []
    for r in dump["objects"]:
        if "aabb" in r:
            xs += [r["aabb"][0][0] * 1000, r["aabb"][1][0] * 1000]
            ys += [r["aabb"][0][1] * 1000, r["aabb"][1][1] * 1000]
    if not xs:
        return False
    rx = [c for row in rows for c in (row["rect_mm"][0], row["rect_mm"][0] + row["rect_mm"][2])]
    ry = [c for row in rows for c in (row["rect_mm"][1], row["rect_mm"][1] + row["rect_mm"][3])]
    return (abs(min(xs) - min(rx)) < 1000 and abs(max(xs) - max(rx)) < 1500
            and abs(min(ys) - min(ry)) < 1000 and abs(max(ys) - max(ry)) < 1500)


# ---------------------------------------------------------------- extract audit --
def extract_audit(ledger, close_mm=None):
    """Fresh ink vs the roster: every kept cluster must land on an existing row
    (coverage>=0.3 either way) or it becomes a NEW UNRESOLVED row — the half that
    guards against the roster itself having derived something away. Lazy-imports
    plan_cluster; caller handles ImportError as could-not-run."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from plan_cluster import extract_clusters
    src = ledger["source_sheet"]
    pp = ledger["extract_params"]
    pdf = os.path.join(REPO, src["pdf"])
    res = extract_clusters(pdf, src["page"], tuple(pp["zone"]),
                           close_mm or pp["close_mm"])
    fresh, new = [], []
    for c in res["items"]:
        rect = (c["x"], c["y"], c["w"], c["d"])
        ra = max(rect[2] * rect[3], 1.0)
        hit = None
        for row in ledger["rows"]:
            ov = rect_overlap_area(rect, row["rect_mm"])
            if ov / ra >= 0.3 or ov / max(row["rect_mm"][2] * row["rect_mm"][3], 1.0) >= 0.3:
                hit = row["id"]
                break
        fresh.append({"rect_mm": rect, "curve": c["curve"], "landed_on": hit})
        if hit is None:
            new.append(rect)
    return fresh, new, res["dropped"]


# --------------------------------------------------------------- spec ratchet --
def _spec_masses(spec):
    for it in spec.get("items", []):
        yield it
    for bt in spec.get("builtins", []):
        yield bt
    for s in spec.get("subrooms", []):
        for f in s.get("fixtures", []):
            yield f


def spec_ratchet_check(ledger, spec):
    """DRW-3: a mass NEW or EDITED versus the seeded baseline must carry
    `sheet_ref` — an SR-id that exists in this ledger, or a declared
    'not-in-drawing: <reason>' with a real reason. Grandfathered masses are
    never violations (zone-by-zone backfill, not big-bang), but the uncovered
    ones are COUNTED and printed — a silent grandfather clause is how the next
    headboard gets derived away. Returns (violations, stats)."""
    rat = ledger.get("spec_ratchet") or {}
    base = rat.get("baseline")
    if base is None:
        return None, None
    ids = {r["id"] for r in ledger.get("rows", [])}
    covered = {r.get("spec_mass") for r in ledger.get("rows", [])
               if r.get("spec_mass")}

    def _valid_ref(ref):
        return isinstance(ref, str) and (
            ref in ids
            or (ref.startswith("not-in-drawing:")
                and len(ref.split(":", 1)[1].strip()) >= 10))

    viol = []
    stats = {"masses": 0, "covered": 0, "backfill_debt": 0,
             "edited_ok": 0, "new_ok": 0}
    for m in _spec_masses(spec):
        stats["masses"] += 1
        name = m.get("name", "?")
        fp = [m.get("x"), m.get("y"), m.get("w"), m.get("d"), m.get("h")]
        ref = m.get("sheet_ref")
        if name in base and base[name] == fp:
            # a grandfathered mass is covered by a ledger row OR by carrying a
            # valid declared ref of its own (backfill lands either way)
            if name in covered or _valid_ref(ref):
                stats["covered"] += 1
            else:
                stats["backfill_debt"] += 1
            continue
        ok = _valid_ref(ref)
        if ok:
            stats["new_ok" if name not in base else "edited_ok"] += 1
        else:
            kind = "NEW" if name not in base else "EDITED"
            viol.append(f"{name}: {kind} mass carries no valid sheet_ref "
                        f"(an SR-id in qa/sheet-recon.json, or "
                        f"'not-in-drawing: <reason>')")
    return viol, stats


def ratchet_line(viol, stats):
    line = ("SPEC-RATCHET: %(masses)d masses | %(covered)d covered | "
            "%(backfill_debt)d backfill debt | %(edited_ok)d edited+ref | "
            "%(new_ok)d new+ref" % stats)
    return line + (f" | {len(viol)} VIOLATIONS" if viol else "")


# ------------------------------------------------------------------------ report --
def ledger_summary(ledger):
    """Counts from the ledger's STORED verdicts (last --recon/--gate run), for the
    session opener — plan_status must not need a scene dump on disk to say where
    the reconciliation stands. Returns (summary, frame, warnings)."""
    rows = ledger.get("rows", [])
    s = {"drawn": len(rows), "matched": 0, "gaps": 0, "superseded": 0,
         "unresolved": 0, "blocking": 0, "frustum_source": "stored"}
    frame = None
    warns = []
    for r in rows:
        v = r.get("verdict")
        m = r.get("match") or {}
        frame = m.get("frame") or frame
        if v == "matched":
            s["matched"] += 1
        elif v == "declared_gap":
            s["gaps"] += 1
        elif v == "superseded":
            s["superseded"] += 1
        else:
            s["unresolved"] += 1
            if m.get("in_frustum") is not False:
                s["blocking"] += 1
        if r.get("warning"):
            warns.append(f"{r.get('id', '?')}: {r['warning']}")
    return s, frame, warns


def gate_line(summary):
    return ("SHEET-RECON: %(drawn)d drawn | %(matched)d matched | %(gaps)d declared gaps"
            " | %(superseded)d superseded"
            " | %(unresolved)d UNRESOLVED (%(blocking)d blocking) [%(frustum_source)s]"
            % dict({"superseded": 0}, **summary))


def _load(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        print(f"SHEET-RECON: COULD NOT RUN — {what} unreadable: {e}")
        raise SystemExit(2)


def _save_ledger(ledger):
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv):
    # The rows carry Thai names and this tool's exit codes are a CONTRACT: a
    # cp1252 console must not turn a successful run into exit 1 by crashing the
    # table print — the exact defect P1's scorer shipped once (a crashed gate
    # printing like a completed one).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                   # noqa: BLE001
        pass
    if len(argv) < 2 or argv[1] not in ("--recon", "--gate", "--extract", "--spec"):
        raise SystemExit(__doc__)
    ledger = _load(LEDGER, "ledger qa/sheet-recon.json")

    if argv[1] == "--spec":
        path = argv[2] if len(argv) > 2 else os.path.join(
            REPO, (ledger.get("spec_ratchet") or {}).get("spec_path", ""))
        spec = _load(path, "spec")
        viol, stats = spec_ratchet_check(ledger, spec)
        if viol is None:
            print("SPEC-RATCHET: COULD NOT RUN — no baseline seeded in the ledger")
            raise SystemExit(2)
        print(ratchet_line(viol, stats))
        for v in viol:
            print(f"  !! {v}")
        return 1 if viol else 0

    if argv[1] == "--extract":
        try:
            fresh, new, dropped = extract_audit(ledger)
        except ImportError as e:
            print(f"SHEET-RECON: COULD NOT RUN — extraction needs {e.name}")
            raise SystemExit(2)
        for rect in new:
            nid = "SR-%02d" % (len(ledger["rows"]) + 1)
            ledger["rows"].append({
                "id": nid, "key": f"ink@{rect[0]},{rect[1]}",
                "source": "fresh extraction (plan_cluster) — unaccounted ink",
                "rect_mm": list(rect), "drawn_as": None, "floor_standing": True,
                "identity": None, "gap": None, "note": ""})
            print(f"NEW row {nid}: unaccounted ink at {rect}")
        print(f"extract audit: {len(fresh)} kept clusters, {len(new)} new, "
              f"{len(dropped)} size-dropped (see roster audit)")
        _save_ledger(ledger)
        return 0

    dump = _load(argv[2], "scene dump") if len(argv) > 2 else None
    if dump is None or "objects" not in dump:
        print("SHEET-RECON: COULD NOT RUN — no scene dump given")
        raise SystemExit(2)
    rows = ledger["rows"]
    if not _frames_agree(rows, dump):
        print("SHEET-RECON: COULD NOT RUN — dump and roster frames disagree "
              "(sheet-mm == world-m x1000 assumption broken)")
        raise SystemExit(2)
    rows, summary = reconcile(rows, dump, os.path.basename(argv[2]))
    ledger["rows"] = rows
    if "--no-save" not in argv:
        _save_ledger(ledger)

    if argv[1] == "--recon":
        for r in rows:
            m = r.get("match") or {}
            best = (m.get("candidates") or [{}])
            best = best[0] if best else {}
            fr = {True: "in-frustum", False: "off-camera", None: "frustum?"}[
                m.get("in_frustum")]
            print(f"{r['id']:6s} {r['verdict']:12s} {fr:11s} "
                  f"{(r.get('drawn_as') or r['key'])[:38]:38s} "
                  f"-> {best.get('assembly', '-'):28s} cov={best.get('coverage', 0):.2f}"
                  + (f"  !! {r['warning']}" if r.get("warning") else ""))
    print(gate_line(summary))
    return 1 if summary["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
