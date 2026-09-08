"""MUTATION PROBE. A green test proves nothing until you have watched it go RED.

This repo's own history: `test_thai_skeleton_survives_split_combining_marks` asserted
`title_is_floor_plan("NOT A PLAN TITLE", split)[0]` with the message "the Thai fallback must fire".
It never fired -- "NOT A PLAN TITLE" contains the substring PLAN, so the LATIN branch answered, and
the test stayed green even after the fallback was deleted. It could not fail. That is the 15th
recurrence of the flattering-scorer shape in this repo, and it is why this file exists.

For each new gate check: break the code, assert the test that guards it turns RED, restore.
A probe that leaves a mutation in the working tree is worse than no probe, so the original bytes
are held on disk (<reader>.probe-backup, gitignored) for the whole run: the finally restores from
that file and verifies byte-identity, and if the process is killed mid-probe the backup survives
for a hand restore. Three more honesty rules, each bought by an incident:
  - PREFLIGHT: the guarding tests must be GREEN on the unmutated reader before anything is
    mutated -- a broken pytest environment fails EVERY run, which would otherwise read as 9/9 RED
    (the flattering-scorer shape wearing the probe's own uniform).
  - The probe records the reader's raw-byte md5 + git-dirty state up front -- the same md5 the
    census stamps, after a background agent edited the reader DURING a measurement run.
  - A concurrent edit to the reader mid-probe is DETECTED (the tree is compared against the last
    bytes the probe itself wrote) and the run exits nonzero: the restore must clobber the edit to
    leave the tree sane, but it never pretends nothing happened.
Exit 0 only when every mutation went RED, the restore verified byte-identical, and no concurrent
edit was seen.
"""
import hashlib
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(REPO)
READER = os.path.join("pipeline", "scripts", "bluehouse_plan_reader.py")
BACKUP = READER + ".probe-backup"

# (label, guarding test, old, new)  -- `old` must appear EXACTLY once or the probe aborts.
MUTATIONS = [
    ("PUA marks dropped from _THAI_MARKS", "font_private",
     "               | set(range(0xF700, 0xF720)))",
     "               )"),

    ("accept BEFORE veto (order flipped)", "veto_runs_first",
     "    skel = thai_skeleton(dt)\n    for bad in THAI_NOT_PLAN_SKELS:",
     "    skel = thai_skeleton(dt)\n    if THAI_PLAN_SKEL in skel:\n"
     "        return True, 'ACCEPT-FIRST MUTANT'\n    for bad in THAI_NOT_PLAN_SKELS:"),

    ("page_text fallback resurrected", "fallback_is_GONE",
     '    if THAI_PLAN_SKEL in skel:\n        return True, f"DRAWING TITLE {dt!r} names a Thai plan'
     ' (แปลน) and no veto matched"',
     '    if THAI_PLAN_SKEL in skel:\n        return True, "plan"\n'
     '    if THAI_FLOORPLAN_SKEL in thai_skeleton(page_text or ""):\n'
     '        return True, "FALLBACK MUTANT"'),

    ("T3 removed from read_bands' own list", "T3_is_wired",
     '        {"id": "T3", "name": "the plan is of a STOREY, not of one room", "ok": ok_x,\n'
     '         "detail": why_x},\n        {"id": "T2", "name": "the title block STATES a plan scale",',
     '        {"id": "T2", "name": "the title block STATES a plan scale",'),

    ("T3 made blind to extent", "ONE_ROOM_is_not_a_FLOOR",
     '    if plan_extent(drawing_title) == "room":',
     '    if False:'),

    ("RCP veto removed", "WALL_POCHE",
     'THAI_NOT_BUILDABLE_SKELS = ("ฝาเพดาน",)',
     'THAI_NOT_BUILDABLE_SKELS = ()'),

    # --- the sheet-shrink fix. THE POINT: the gate's own scoreboard (accepted-count, recall,
    # false-accepts) is BLIND to every one of these. Only an ABSOLUTE dimension catches them.
    ("shrink dropped at the call site", "A4_EXPORT",
     "resolve_scale([t for _, t in candidates], tb, shrink or 1.0)",
     "resolve_scale([t for _, t in candidates], tb, 1.0)"),

    ("sheet_shrink INTERPOLATES instead of refusing", "FAIL_CLOSED",
     "    raise RefuseSheet(\n"
     "        f\"the sheet border is {s:.4f}x the A3 design sheet -- not a known paper step \"",
     "    return s, 'INTERPOLATING MUTANT'\n"
     "    raise RefuseSheet(\n"
     "        f\"the sheet border is {s:.4f}x the A3 design sheet -- not a known paper step \""),

    ("wall family widened to 100/150/200/250", "DISARM_the_half_size_veto",
     "WALL_MM_LO, WALL_MM_HI = 95.0, 106.0",
     "WALL_MM_LO, WALL_MM_HI = 95.0, 260.0"),

    # --- the geometric boundary-ink class (the 0.42 lesson). Four ways to quietly break it:
    ("wall pen loses its exclusion from boundary ink", "GEOMETRIC_class",
     "    return round(width or 0, 2) != WALL_PEN_PT",
     "    return True"),

    ("composite cavity tol bridges a corridor", "cavity_not_a_corridor",
     "WALL_CAVITY_TOL_MM = 60.0",
     "WALL_CAVITY_TOL_MM = 1000.0"),

    ("run-backs-gap containment becomes same-axis-anything", "not_the_far_wall",
     "    return prun[1] <= key[1] + 0.11 and key[2] <= prun[2] + 0.11",
     "    return True"),

    ("pen evidence silently dropped from openings", "REPORTS_the_pens",
     '            rec["ink_pens"] = gap_pen_mm(g, boundary)',
     "            pass"),

    # --- the 2026-07-14 review round (2 MAJOR + hardening). Each mutation re-opens one hole.
    # NOTE the tol mutation above (60->1000) now goes RED via the 90mm-coextensive case, not the
    # corridor: the corridor is ALSO blocked by MAX_COMPOSITE_MM, and two vetoes mask each other.
    ("composite merge goes extent-blind again", "NEVER_COEXIST",
     "            if not _ivs_overlap(iva, ivb):\n                continue",
     "            if False:\n                continue"),

    ("composite width cap removed", "cavity_not_a_corridor",
     "MAX_COMPOSITE_MM = 300.0",
     "MAX_COMPOSITE_MM = 10000.0"),

    ("crossing ink admitted as stub backing", "crossing_line_cannot_cut_a_stub",
     "STUB_BACKER_OVERSHOOT_MM = 100.0",
     "STUB_BACKER_OVERSHOOT_MM = 1e9"),

    ("composite evidence zeroed", "only_through_a_COMPOSITE",
     "            mm += b - a",
     "            pass"),

    ("pen evidence loses its largest-first ordering", "REPORTS_the_pens",
     "sorted(out.items(), key=lambda kv: -kv[1])",
     "list(out.items())"),
]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if os.path.exists(BACKUP):
    sys.exit(f"{BACKUP} already exists -- a previous probe died mid-run. Compare it against "
             f"{READER}, restore by hand, delete the backup, then re-run.")

pinned = open(READER, encoding="utf-8").read()
md5 = hashlib.md5(open(READER, "rb").read()).hexdigest()   # raw bytes = census.py's stamp
gs = subprocess.run(["git", "status", "--porcelain", READER], capture_output=True, text=True)
dirty = f"git status FAILED rc={gs.returncode}" if gs.returncode else gs.stdout.strip()
print(f"probing reader md5={md5}  working-tree={'DIRTY: ' + dirty if dirty else 'clean (== HEAD)'}")
shutil.copyfile(READER, BACKUP)

TESTS = os.path.join("pipeline", "scripts", "test_bluehouse_plan_reader.py")

# PREFLIGHT: prove the guarding tests can pass at all. Without this, a pytest environment that
# fails every run (missing dep, collection error) reads as 9/9 RED = a perfect score for nothing.
pre = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q",
                      "-k", " or ".join(k for _, k, _, _ in MUTATIONS)],
                     capture_output=True, text=True, encoding="utf-8", errors="replace",
                     env={**os.environ, "PYTHONIOENCODING": "utf-8"})
if pre.returncode != 0 or "no tests ran" in (pre.stdout or ""):
    os.remove(BACKUP)
    sys.exit("preflight FAILED -- the guarding tests are not GREEN on the UNMUTATED reader, so a "
             "RED verdict would prove nothing. pytest said:\n" + (pre.stdout or "")[-2000:])
# PREFLIGHT 2: every selector must MATCH, individually. The OR-join above hides ONE renamed
# guarded test among live ones, and the per-mutation run then read the rename as RED (pytest
# exits 5 on all-deselected, 5 != 0 -- the probe's own flattering-scorer shape; review
# 2026-07-14, MAJOR). --collect-only is cheap; exit 5 here = a dead selector, named.
dead = []
for _, k, _, _ in MUTATIONS:
    col = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "--collect-only", "-k", k],
                         capture_output=True, text=True, encoding="utf-8", errors="replace",
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if col.returncode == 5:
        dead.append(k)
if dead:
    os.remove(BACKUP)
    sys.exit(f"preflight FAILED -- selector(s) match NO test: {dead}. A guarded test was renamed "
             "or deleted; the probe would have reported a FALSE RED for it forever.")
print("preflight: guarding tests GREEN and every selector matches on the unmutated reader\n")

print(f"{'MUTATION':<40} {'GUARDED BY':<26} VERDICT")
print("-" * 84)
bad = 0
last_written = None
try:
    for label, testk, old, new in MUTATIONS:
        n = pinned.count(old)
        if n != 1:
            print(f"{label:<40} {testk:<26} ABORT: anchor found {n}x, not 1")
            bad += 1
            continue
        last_written = pinned.replace(old, new)
        open(READER, "w", encoding="utf-8").write(last_written)
        r = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "-k", testk],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        r.stdout = r.stdout or ""
        # pytest's exit-code contract: 5 = nothing collected/selected. The old sniff for the
        # STDOUT PHRASE 'no tests ran' never fired here -- with a collectible file and a dead -k,
        # pytest prints 'N deselected' and exits 5, which `!= 0` scored as RED: a renamed guarded
        # test would have earned a permanent FALSE RED (review 2026-07-14, MAJOR).
        collected = r.returncode != 5
        red = r.returncode not in (0, 5)
        verdict = ("RED (test earns its keep)" if red and collected
                   else "!!! STILL GREEN -- THE TEST CANNOT FAIL" if collected
                   else "!!! -k MATCHED NOTHING")
        if not (red and collected):
            bad += 1
        print(f"{label:<40} {testk:<26} {verdict}")
finally:
    # was the tree still holding OUR last write? If not, someone edited the reader mid-probe --
    # the incident class this suite exists to catch. The restore below must clobber their edit to
    # leave the tree sane; the exit code says so instead of pretending nothing happened.
    try:
        on_disk = open(READER, encoding="utf-8").read()
    except Exception:
        on_disk = None
    concurrent = on_disk != (last_written if last_written is not None else pinned)
    shutil.copyfile(BACKUP, READER)
    same = open(READER, encoding="utf-8").read() == pinned
    print("-" * 84)
    if concurrent:
        print(f"*** CONCURRENT EDIT DETECTED: {READER} changed under the probe mid-run; "
              f"the foreign bytes were OVERWRITTEN by the restore ***")
    print("restored:", "OK" if same else f"*** FAILED -- RESTORE {READER} FROM {BACKUP} BY HAND ***")
    if same:
        os.remove(BACKUP)

print(f"\n{len(MUTATIONS) - bad}/{len(MUTATIONS)} new checks are guarded by a test that can go red.")
sys.exit(1 if (bad or not same or concurrent) else 0)
