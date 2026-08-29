"""test_pose_check.py — seeded suite for pose_check.py.

THE NEGATIVE CONTROL IS THE POINT (D-056). A guard written after an incident must
be run against the state that produced the incident, or all it proves is that it
agrees with today's numbers. So the first two tests are the TRN-003 island before
and after the correction: the axis the build actually carried (perpendicular to the
kitchen wall) must print 90 deg and FAIL, and the measured one (87.3 deg, parallel)
must pass. Everything else here is a way the row itself can lie.

Pure Python, no test framework:  python pipeline/scripts/test_pose_check.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pose_check as pc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def audit1(row):
    rows, viol, cnr = pc.audit({"poses": [row]})
    return rows[0], viol, cnr


# The kitchen wall runs along +Y, so a mass laid PARALLEL to it has a heading near
# 90 deg. The drums measured 87.3.
REF_ISLAND = 87.3

# ---------------------------------------------------------------- negative control
r, viol, _ = audit1(dict(id="island_slab", ours=177.3, ref=REF_ISLAND, fold=2,
                         method="recurrence", tol_deg=5))
check("NEGATIVE CONTROL — the island as it was actually built (a quarter turn out) FAILS",
      r["state"] == "FAIL" and abs(r["error_deg"] - 90.0) < 1e-6, str(r))
check("…and it names 90 degrees, the number nobody in the repo could print",
      viol and "90.0 deg" in viol[0], str(viol))

r, viol, _ = audit1(dict(id="island_slab", ours=87.3, ref=REF_ISLAND, fold=2,
                         method="recurrence", tol_deg=5))
check("POSITIVE CONTROL — the corrected island passes",
      r["state"] == "PASS" and not viol, str(r))

# fold 2 must fold 180 and must NOT fold 90 — the island end-for-end is the same
# island, a quarter turn is a different room.
r, _, _ = audit1(dict(id="isl", ours=REF_ISLAND + 180, ref=REF_ISLAND, fold=2,
                      method="recurrence"))
check("fold 2 folds 180 to zero", r["state"] == "PASS" and r["error_deg"] < 1e-6, str(r))
r, _, _ = audit1(dict(id="isl", ours=REF_ISLAND + 90, ref=REF_ISLAND, fold=2,
                      method="recurrence"))
check("fold 2 does NOT fold 90", abs(r["error_deg"] - 90.0) < 1e-6, str(r))

# ------------------------------------------------------------- vectors and headings
r, _, _ = audit1(dict(id="v", ours=[0, 1, 0], ref=[0.0472, 1, 0], fold=2,
                      method="recurrence", tol_deg=5))
check("a 3-vector is projected to the plan and compared",
      r["state"] == "PASS" and 2.6 < r["error_deg"] < 2.8, str(r))
r, viol, _ = audit1(dict(id="v", ours=[0, 0, 1], ref=90, fold=2, method="recurrence"))
check("a vertical axis has no heading and is refused, not rounded to zero",
      r["state"] == "MALFORMED" and "no length in plan" in r["detail"], str(r))

# ------------------------------------------------------- the three ways a row lies
# 1. a chord of a curve
r, viol, _ = audit1(dict(id="isl", ours=87.3, ref=REF_ISLAND, fold=2,
                         method="line_fit", spans=[-1.776, -2.806], tol_deg=5))
check("line_fit on the oval's two real spans is REFUSED (they disagree)",
      r["state"] == "MALFORMED" and "CURVED" in r["detail"], str(r))
check("…and the refusal says do not average", "third chord" in r["detail"], str(r))
r, viol, _ = audit1(dict(id="wall", ours=0.0, ref=0.0, fold=2,
                         method="line_fit", spans=[0.0, 0.4], tol_deg=5))
check("line_fit on a genuinely straight edge is accepted",
      r["state"] == "PASS", str(r))
r, _, _ = audit1(dict(id="wall", ours=0.0, ref=0.0, fold=2, method="line_fit",
                      spans=[0.0]))
check("one span is not two — a single fit cannot tell an edge from a chord",
      r["state"] == "MALFORMED" and "TWO independent spans" in r["detail"], str(r))

# 2. an ill-conditioned vanishing point
r, _, _ = audit1(dict(id="isl", ours=87.3, ref=REF_ISLAND, fold=2,
                      method="vp_intersection", segment_angle_deg=0.6, tol_deg=5))
check("a VP from near-parallel segments is refused",
      r["state"] == "MALFORMED" and "near-parallel" in r["detail"], str(r))
check("…and the gate is the ANGLE, not the VP's distance off-frame",
      "not how far off-frame" in r["detail"], str(r))
r, _, _ = audit1(dict(id="isl", ours=87.3, ref=REF_ISLAND, fold=2,
                      method="vp_intersection", segment_angle_deg=34.0, tol_deg=5))
check("a well-separated VP pair is accepted", r["state"] == "PASS", str(r))

# 3. symmetry as a bypass
r, _, _ = audit1(dict(id="isl", ours=177.3, ref=REF_ISLAND, fold=4,
                      method="recurrence", tol_deg=5))
check("fold 4 without a reason is refused — it would erase exactly this error",
      r["state"] == "MALFORMED" and "fold_reason" in r["detail"], str(r))
r, _, _ = audit1(dict(id="drum0", ours=0, ref=90, fold=0, method="recurrence"))
check("fold 0 (a drum) is REFUSED, never passed — it has no orientation to check",
      r["state"] == "MALFORMED" and "did not make" in r["detail"], str(r))

# ------------------------------------------------------------------ the tolerance
r, _, _ = audit1(dict(id="isl", ours=177.3, ref=REF_ISLAND, fold=2,
                      method="recurrence", tol_deg=91))
check("a tolerance that would swallow the defect is refused by name",
      r["state"] == "MALFORMED" and "above the cap" in r["detail"], str(r))

# ------------------------------------------------------------- could-not-run vs pass
r, viol, cnr = audit1(dict(id="isl", ours=87.3, fold=2, method="recurrence"))
check("a row with no reference is COULD NOT RUN, not a violation",
      r["state"] == "COULD NOT RUN" and cnr and not viol, str((r, viol, cnr)))
check("a method that was never recorded is refused",
      audit1(dict(id="x", ours=1, ref=2, method="vibes"))[0]["state"] == "MALFORMED")

# ------------------------------------------------------------------- exit contract
import json
import subprocess
import tempfile

def run(poses, extra=()):
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(poses, f)
    try:
        cp = subprocess.run([sys.executable, os.path.join(HERE, "pose_check.py"),
                             "--poses", p, *extra], capture_output=True, text=True)
        return cp.returncode, (cp.stdout or "") + (cp.stderr or "")
    finally:
        os.unlink(p)

rc, _ = run({"poses": [dict(id="i", ours=87.3, ref=87.3, fold=2, method="recurrence")]})
check("exit 0 when the claim holds", rc == 0, str(rc))
rc, out = run({"poses": [dict(id="i", ours=177.3, ref=87.3, fold=2, method="recurrence")]})
check("exit 1 when a pose is wrong", rc == 1, str(rc) + out)
rc, _ = run({"poses": []})
check("exit 2 on an empty pose file — a mute check must not print like a pass", rc == 2, str(rc))
rc, _ = run({"poses": [dict(id="i", ours=87.3, fold=2, method="recurrence")]})
check("exit 2 when the reference was never measured", rc == 2, str(rc))

# -------------------------------------------------------------------------- report
bad = [r for r in RESULTS if not r[1]]
for name, ok, detail in RESULTS:
    print(f"  [{'ok' if ok else 'XX'}] {name}")
    if not ok and detail:
        print(f"        got: {detail}")
print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
sys.exit(1 if bad else 0)
