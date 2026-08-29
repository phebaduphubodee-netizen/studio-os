"""test_critique_schema.py — seeded suite for critique_schema.py (T7).

The two tests that carry the file are the last two: PROSE must be refused, and a
lighting round whose critic keeps filing GEOMETRY items must be stopped. The
second is the one T7 was actually for — SEIG's own reported failure mode is that
"errors introduced in early stages may propagate throughout the pipeline, leading
to local minima from which later stages cannot easily recover", and until now
nothing here could even count that.

Pure Python, no test framework:  python pipeline/scripts/test_critique_schema.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import critique_schema as cs

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


GOOD = """
1. The island slab has no contact shadow where it meets the floor.
   where: lower-left third, the near end of the pale slab
   stage: lighting   ground: physics   sellability: high

2. The stools read as plywood, not the leather they should be.
   where: right of centre, the two seats facing the island
   stage: materials   ground: physics   sellability: medium

3. The counter run is empty — no kettle, no board, nothing.
   where: full length of the left-hand bench
   stage: composition   ground: opinion   sellability: low
"""

items, viol, rep = cs.audit(GOOD)
check("a well-formed answer parses into three items", len(items) == 3, str(len(items)))
check("...with no violations", not viol, viol)
check("...and tallies by stage",
      rep["tally"]["lighting"] == 1 and rep["tally"]["materials"] == 1
      and rep["tally"]["composition"] == 1, rep["tally"])

# ------------------------------------------------------------------ missing fields
_, v, _ = cs.audit("1. Something is off.\n   stage: lighting  ground: physics  "
                   "sellability: high\n")
check("an item with no `where:` is refused", any("no `where:`" in x for x in v), v)
check("...and the refusal says why a frame anchor is the mitigation",
      any("micro-claims" in x for x in v), v)

_, v, _ = cs.audit("1. x\n   where: middle\n   ground: physics  sellability: high\n")
check("an item with no `stage:` is refused as unroutable",
      any("no `stage:`" in x and "unroutable" in x for x in v), v)

_, v, _ = cs.audit("1. x\n   where: middle\n   stage: vibes  ground: physics  "
                   "sellability: high\n")
check("a stage outside SEIG's five is refused",
      any("is not one of" in x for x in v), v)

_, v, _ = cs.audit("1. x\n   where: m\n   stage: lighting  ground: physics  "
                   "sellability: high\n3. y\n   where: m\n   stage: lighting  "
                   "ground: physics  sellability: high\n")
check("a gap in the numbering is refused — an item was lost",
      any("numbering breaks" in x for x in v), v)

# --------------------------------------------------------------------------- triage
_, v, _ = cs.audit(GOOD, require_triage=True)
check("--require-triage refuses items with no written triage",
      sum("no `triage:`" in x for x in v) == 3, v)
_, v, _ = cs.audit(GOOD.replace("sellability: high",
                                "sellability: high\n   triage: accept -> lighting lane"),
                   require_triage=True)
check("...and accepts one that carries it", sum("no `triage:`" in x for x in v) == 2, v)

# ----------------------------------------------------------------------- PROSE
PROSE = """The render reads flat. The lighting has no direction and the island
looks like plastic. Styling is thin and the room feels unfinished. If I had to
fix one thing it would be the light."""
_, v, _ = cs.audit(PROSE)
check("THE HEADLINE: prose is refused",
      any("this answer is PROSE" in x for x in v), v)
check("...and the refusal names why: R7 needs a triage PER ITEM",
      any("triage" in x for x in v), v)

# --------------------------------------------------------------------- the Andon
LIGHTING_ROUND = """
1. The island is laid across the room instead of along the wall.
   where: centre of frame
   stage: geometry   ground: physics   sellability: high

2. The tall bank and the island occupy the same floor.
   where: left of centre
   stage: geometry   ground: physics   sellability: high

3. The key light is too soft to separate the counter from the wall.
   where: back wall
   stage: lighting   ground: physics   sellability: medium
"""
_, v, rep = cs.audit(LIGHTING_ROUND, stage="lighting")
check("THE ANDON: a lighting round whose items are mostly geometry is STOPPED",
      any("ANDON" in x for x in v), v)
check("...and it counts them", rep.get("upstream") == 2, rep)
check("...and it cites R1, that stopping is the correct move",
      any("never an admission" in x for x in v), v)

_, v, rep = cs.audit(LIGHTING_ROUND, stage="geometry")
check("the same items in a GEOMETRY round raise no Andon — they are its own work",
      not any("ANDON" in x for x in v), v)

bad = [r for r in RESULTS if not r[1]]
for name, ok, detail in RESULTS:
    print(f"  [{'ok' if ok else 'XX'}] {name}")
    if not ok and detail:
        print(f"        got: {detail}")
print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
sys.exit(1 if bad else 0)
