---
name: lighting-design
description: >
  Design or repair the LIGHT of a room render — where the light comes from, how many
  fixtures, colour temperature, the three layers, dynamic range, and whether what is
  bright in the frame has a source the eye can find. Use when a critic says the frame is
  flat / grey / lit from nowhere, when placing or changing fixtures, when the value
  ladder or a D-row about light fails, and before any lighting-led round. Solves the rig
  from the room's geometry (lumen method + codes), never by turning a knob until it looks
  bright. Not a camera skill (see camera-composition).
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Lighting — solved from the room, not tuned by eye

## The two laws that cost this lane the most rounds

**1. LIGHT AFTER OBJECTS.** The rig is SOLVED from geometry, so solving it while the room
is still missing masses bakes the error into the light table and every later object
inherits it. Build order is dimension → objects → light.

**2. A DIRECTION CANNOT BE PROVEN BY AN AMOUNT.** For 43 rounds the key beam ran
perpendicular to the mirror it was supposed to bounce off — dot product **0.000** — while
every wattage check said the rig was fine. The lever that finally moved the frame was
dimming a portal to 0.20, not the sun. **If the claim is about direction, the measurement
must be a direction** (a dot product, a projected position), never an intensity.

## The open defect class this skill serves (P3)

"The light has no source" now has three independent measurements: a ceiling gradient of
**0.73 with no fixture anywhere in the frame**; four wall-washers at z=2.74 m sitting
**outside the frustum** while being the brightest thing in the picture (fixed by the
camera, D-152, not by the rig); and the mirror-bounce dot above. Also on the record from
the ground-truth study: delivered work runs a dynamic range of roughly **191-2500:1**
where ours measured about **10:1** — flatness is a measurable property, not a taste.

## Procedure

**Step 0 — statutory floors first.** `knowledge/codes-th/` outranks everything here and
is the ONLY source for legal values (never take a statutory number from an NLM answer).
Cross-refs sit at the top of both lighting knowledge files.

**Step 1 — count the fixtures with the lumen method, do not guess.**
`knowledge/lighting/lumen-method-and-fixture-placement.md` §6 turns a target illuminance
into a fixture count; §2 carries IES residential targets; §4 the placement/spacing rules.
Design illuminance pointers + the law floor: `residential-lighting.md`.

**Step 2 — three layers, with their ratios.** Ambient · task · accent
(`lumen-method §1`, `residential-lighting`). A room with one layer reads as a showroom
regardless of how correct its lux is.

**Step 3 — colour temperature per zone, and the mixing rule.** CCT per zone and the hard
rule against mixing 4000 K with 2700 K in one zone are both in `residential-lighting`.
CRI / R9 floors live there too.

**Step 4 — EVERY BRIGHT THING NEEDS A SOURCE, and every visible fixture must emit.**
Run `frame_geometry.py` and check that each light lighting what you see is inside the
frustum or has its source visible/implied in frame. A lamp modelled with no emitter, a
strip that glows but lights nothing, a switch plate with no buttons — these are the R10
SENSE list, and a critic files them every round until they are built.

**Step 5 — measure the range, not the brightness.** `value_ladder.py` / `value_floor.py` /
`value_probe.py` for the ladder; the D-rows in the exit test carry the bands. Report the
ratio and where each end of it sits.

**Step 6 — playblast before full fidelity (R5), then hand it to eyes.** Spawn
`cold-critic-c2` on the finished frame and run the cross-vendor rung. Light is the one
subject where an instrument agreeing with itself is worth least: the eye names WHAT is
wrong, the measurement names HOW MUCH and WHICH KNOB.

## Refusals

- Never fix a "flat" verdict by raising an intensity. Flatness is a RANGE, and the knob
  that moves a range is rarely the one that moves brightness.
- Never light a room the camera has not been settled on — the frustum decides which
  fixtures exist for the viewer.
- Never carry both power and colour on one lever. A portal that supplies the watts AND
  the cool cast is one parameter carrying two things, and it will fail one of them.
- Exit 2 from any light check = COULD NOT RUN, never "fine" (R11).

## Output

Into the round's gate artifact: the fixture count and the target it came from, the layer
ratios, the CCT per zone, the measured dynamic range before/after, and one line per
in-frame light naming its source. A fixture that cannot be justified leaves the frame as
a declared gap (R10) rather than glowing from nowhere.

## Cross-refs

`pipeline/scripts/element5_lighting.py` · `lighting.py` · `trn002_lightcheck.py` ·
`value_ladder.py` · `frame_geometry.py` ·
`knowledge/lighting/lumen-method-and-fixture-placement.md` ·
`knowledge/lighting/residential-lighting.md` ·
`knowledge/rendering/cycles-lighting-camera-presets.md`.
