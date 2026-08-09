"""craft_check.py — the first craft property in this lane that is a NUMBER. PURE (no bpy).

    python pipeline/scripts/craft_check.py --spec <spec.json> [--acuity 1.0] [--soft]

WHY THIS EXISTS
---------------
`docs/.../triage-debt-2026-08-07.md` ended on an observation that should have been
a specification: every critic item this lane DROPPED was a craft item — an edge, a
surface, a glass, a junction, a piece of hardware — and *"ข้อที่เครื่องมือของเลนนี้
ให้คะแนนได้ จะถูกหยิบเสมอ … ส่วนข้อที่ให้คะแนนไม่ได้ ต้องอาศัยคนจำมันไว้ — และการ
หล่นหายทั้งหมดเกิดในกลุ่มหลัง."* Items a tool scores get picked up. Items only a
person remembers get lost. So the way to stop losing a craft item is not to
remember harder; it is to make one of them scoreable.

SILHOUETTE FACETING IS SCOREABLE, EXACTLY
-----------------------------------------
A rounded corner of radius R drawn with N segments per quarter-turn deviates from
the true arc by a sagitta

    sag = R · (1 − cos(θ/2)),    θ = (π/2)/N

and that deviation is invisible when it subtends less than the eye's acuity limit
α at the viewing distance D:

    sag ≤ α · D    ⟹    N ≥ (π/2) / (2·arccos(1 − α·D/R))

α = 1 arcminute = 2.909e-4 rad is the standard acuity figure.

PROVENANCE, AND WHY IT IS TRUSTED
---------------------------------
A NotebookLM Deep Research (2026-08-08, notebook "STUDIO craft cg-tells") returned
a segment table for D = 3000 mm citing the 1-arcminute limit: R = 2.5/5/10/25/50/
100/250/500 mm → 4/6/8/12/17/24/38/54 segments **per full circle**. Its citation
pointed at the DR's own synthesised report rather than a primary source, which by
this repo's quarantine rule is not good enough to enter `knowledge/`.

STAGED SOURCE OF RECORD: `knowledge/_inbox/nlm-craft-cg-tells/2026-08-08-craft-and-cg-tells.md`
(transcript + attribution: `knowledge/_inbox/nlm-craft-cg-tells/qa-history.json`).
Cited by PATH and not only by notebook name, because the inbox audit's backlink map
matches paths — and named-but-unpathed is how a DR that DID change something still
reads as write-only debt. This module is that unit's successor of record.

So it was not trusted — it was DERIVED. The closed form above reproduces all eight
rows exactly, from acuity and geometry alone. That is the difference between a
number we accepted and a number we can regenerate: this module does not carry the
table, it carries the derivation, and the table is a test.

WHAT IT CHECKS AND WHAT IT CANNOT
---------------------------------
Reads `oct` masses (rounded prisms: `cut` is the corner radius, the builder's
`seg` is per quarter-turn and defaults to 6), measures each one's distance to the
solved camera, and reports the segment floor. It cannot see occlusion — a corner
hidden behind the bed is charged the same as one in the open — so it reports and
does not veto. Over-reporting is the correct error here: the alternative is a
scope that shrinks until the check is silent, which is how the last two guards in
this repo died.
"""
import argparse
import json
import math
import sys

ACUITY_ARCMIN = 1.0  # standard human visual acuity limit
DEFAULT_SEG = 6      # trn002_geom.oct_mesh(seg=6)


def acuity_rad(arcmin=ACUITY_ARCMIN):
    return arcmin / 60.0 * math.pi / 180.0


def min_segments(radius_mm, distance_mm, arcmin=ACUITY_ARCMIN, quarter=True):
    """Segments needed so the chord error is below acuity.

    `quarter=True` counts segments per 90° corner (what `oct_mesh` takes);
    False counts them per full circle (how the published tables are written).
    Returns 1 when the whole radius is below the acuity limit — a 2 mm fillet at
    5 m is invisible whatever you do to it, and pretending otherwise would have
    this check demand geometry that cannot be seen.
    """
    if radius_mm <= 0 or distance_mm <= 0:
        return 1
    allowed = acuity_rad(arcmin) * distance_mm
    if allowed >= radius_mm:
        return 1
    theta = 2.0 * math.acos(1.0 - allowed / radius_mm)
    full = math.ceil(2.0 * math.pi / theta)
    return max(1, math.ceil(full / 4.0)) if quarter else max(1, full)


def camera_distance(cam, centre_mm):
    dx = centre_mm[0] - cam["x_mm"]
    dy = centre_mm[1] - cam["y_mm"]
    dz = centre_mm[2] - cam["z_mm"]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def audit_silhouette(spec, arcmin=ACUITY_ARCMIN):
    """Return (rows, shortfalls). Pure."""
    cam = spec.get("camera") or {}
    if not {"x_mm", "y_mm", "z_mm"} <= set(cam):
        return [], ["spec has no solved camera — cannot measure any viewing distance"]
    rows, short = [], []
    for m in spec.get("masses", []):
        if m.get("kind") != "oct":
            continue
        cut = m.get("cut")
        if not cut:
            continue
        seg = int(m.get("seg", DEFAULT_SEG))
        d = camera_distance(cam, m["c"])
        need = min_segments(float(cut), d, arcmin)
        rows.append({"name": m["name"], "cut_mm": float(cut), "dist_mm": round(d),
                     "seg": seg, "need": need})
        if seg < need:
            short.append(
                f"{m['name']}: corner R={cut:g} mm at {d/1000:.2f} m needs "
                f"{need} segments per quarter, has {seg} — the arc deviates "
                f"{float(cut) * (1 - math.cos((math.pi / 2 / seg) / 2)):.2f} mm "
                f"where {acuity_rad(arcmin) * d:.2f} mm is the visibility limit")
    return rows, short


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--acuity", type=float, default=ACUITY_ARCMIN,
                    help="acuity limit in arcminutes (default 1.0)")
    ap.add_argument("--soft", action="store_true", help="report only, exit 0")
    a = ap.parse_args()

    spec = json.loads(open(a.spec, encoding="utf-8").read())
    rows, short = audit_silhouette(spec, a.acuity)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"SILHOUETTE: {len(rows)} rounded masses at {a.acuity:g} arcmin")
    for r in sorted(rows, key=lambda r: r["seg"] - r["need"]):
        mark = "  " if r["seg"] >= r["need"] else "<<"
        print(f"  {mark} {r['name']:16s} R={r['cut_mm']:6.1f} mm  d={r['dist_mm']/1000:5.2f} m"
              f"  seg={r['seg']}  need={r['need']}")
    if short:
        print(f"SILHOUETTE SHORTFALLS ({len(short)}):")
        for s in short:
            print("  - " + s)
        if not a.soft:
            sys.exit(1)


if __name__ == "__main__":
    main()
