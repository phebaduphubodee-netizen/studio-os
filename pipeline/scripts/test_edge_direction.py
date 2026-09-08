"""test_edge_direction.py — seeded suite for edge_direction.py.

EVERY NUMBER IN THE NEGATIVE CONTROL IS FROM THE REPO, not invented for the test:
they are the seven fitted lines in
`training/TRN-003_3dshaker-kitchen/02_camera/solved-camera.json`, the file that was
sitting on disk while the island was built a quarter turn out.

    family A (kitchen wall)   A1 -0.26984, A4 -0.09445, A5 -0.02538,
                              A3 +0.17576, A7 -0.28678      -> widest pair 25.97 deg
    family B (glazing+island) B1 +0.04296, B4 -0.03109      -> widest pair  4.24 deg

Family B is the one the island's axis came from. The gate must pass A and refuse B,
and the test must also show WHY the obvious alternative fix would not have worked:
by angle, the island chord fits family B beautifully.

Pure Python, no test framework:  python pipeline/scripts/test_edge_direction.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edge_direction as ed

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


FAM_A = [{"m": -0.26984, "b": 534.93}, {"m": -0.09445, "b": 862.85},
         {"m": -0.02538, "b": 985.10}, {"m": 0.17576, "b": 1343.17},
         {"m": -0.28678, "b": 512.73}]
FAM_B = [{"m": 0.04296, "b": 690.88}, {"m": -0.03109, "b": 1270.75}]
ISLAND = {"name": "B4_island_top", "m": -0.03109, "b": 1270.75, "u": 850.0}

# ---------------------------------------------------------------- conditioning
wa = ed.family_conditioning(FAM_A, "A")
wb = ed.family_conditioning(FAM_B, "B")
check("family A (cabinetry) is well conditioned: widest pair 25.97 deg "
      "(A7 at -16.00 vs A3 at +9.97)", 25.8 < wa < 26.1, f"{wa:.2f}")
check("family B (glazing + island) is 4.24 deg — the number fSpy warns about",
      4.1 < wb < 4.4, f"{wb:.2f}")

try:
    ed.vanishing_point(FAM_A, "A")
    ok_a = True
except ed.Unsupported as e:
    ok_a = False
check("A's vanishing point is allowed", ok_a)

try:
    ed.vanishing_point(FAM_B, "B")
    ok_b, msg = True, ""
except ed.Unsupported as e:
    ok_b, msg = False, str(e)
check("NEGATIVE CONTROL: B's vanishing point is REFUSED", not ok_b, msg)
check("...and the refusal names the angle, not the VP's distance off-frame",
      "4.2" in msg and "off-frame" not in msg, msg)
check("...and says nothing derived from it may be trusted",
      "including which lines belong to it" in msg, msg)

# ---------------------------------------------- the fix that would NOT have worked
# By angle, the island chord is a textbook member of family B. This is the point:
# the assignment was fine and the FAMILY was rotten, so an assignment test could
# never have caught it.
fams_ok = {"A": {"vp": ed.vanishing_point(FAM_A, "A")[0], "lines": FAM_A},
           "B": {"vp": (7814.0, 1031.0), "lines": FAM_A}}   # B's lines swapped for
#                                                              well-conditioned ones,
#                                                              purely to let the
#                                                              assignment run at all
lab, res = ed.assign_family(ISLAND, fams_ok, "island chord")
check("by ANGLE the island chord fits family B to under a tenth of a degree — "
      "an assignment test alone would have passed it", lab == "B" and res < 0.1,
      f"{lab} {res:.3f}")

# ...and with B's REAL lines, the assignment is refused before it is even scored.
fams_real = {"A": {"vp": ed.vanishing_point(FAM_A, "A")[0], "lines": FAM_A},
             "B": {"vp": (7814.0, 1031.0), "lines": FAM_B}}
try:
    ed.assign_family(ISLAND, fams_real, "island chord")
    refused = ""
except ed.Unsupported as e:
    refused = str(e)
check("with B's real lines the assignment is refused, not scored",
      "family B" in refused, refused)

# ------------------------------------------------------------------ straightness
try:
    ed.straight_direction([-0.031, -0.049], "island front edge")
    curved = ""
except ed.Unsupported as e:
    curved = str(e)
check("NEGATIVE CONTROL: the island's two real spans are refused as CURVED",
      "CURVED" in curved, curved)
check("...and the refusal forbids averaging", "Do not average" in curved, curved)
h, worst = ed.straight_direction([-0.2698, -0.2712], "a real straight edge")
check("a genuinely straight edge passes and returns its heading",
      worst < 0.1 and -15.2 < h < -15.0, f"{h:.2f} / {worst:.3f}")
try:
    ed.straight_direction([-0.031], "one span")
    one = ""
except ed.Unsupported as e:
    one = str(e)
check("one span is refused", "at least two" in one, one)

# ---------------------------------------------------------------- ambiguity guard
amb = {"A": {"vp": (-1809.0, 1031.0), "lines": FAM_A},
       "B": {"vp": (-1805.0, 1031.0), "lines": FAM_A}}
try:
    # a line aimed straight at BOTH near-identical vanishing points
    ed.assign_family({"m": -0.01236, "b": 1008.65, "u": 700.0}, amb, "amb")
    a_msg = ""
except ed.Unsupported as e:
    a_msg = str(e)
check("two families that fit equally well refuse the assignment", "coin toss" in a_msg,
      a_msg)

# A line belonging to neither.
try:
    ed.assign_family({"m": 3.0, "b": 0.0, "u": 700.0},
                     {"A": {"vp": ed.vanishing_point(FAM_A, "A")[0], "lines": FAM_A}},
                     "stray")
    stray = ""
except ed.Unsupported as e:
    stray = str(e)
check("a line matching no axis is refused rather than forced into the nearest one",
      "belongs to no measured axis" in stray, stray)

bad = [r for r in RESULTS if not r[1]]
for name, ok, detail in RESULTS:
    print(f"  [{'ok' if ok else 'XX'}] {name}")
    if not ok and detail:
        print(f"        got: {detail}")
print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
sys.exit(1 if bad else 0)
