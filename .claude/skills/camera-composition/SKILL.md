---
name: camera-composition
description: >
  Choose, move or judge the CAMERA of a room render — framing, eye height, what the
  frame must contain, depth of field, and whether the composition reads as a room or as
  a backdrop. Use before any camera change, when a critic says the frame reads flat /
  cropped / like a backdrop, when adopting a new hero view, and BEFORE the first
  full-fidelity frame of a new camera. Measures with frame_geometry.py before rendering,
  never after. Not a lighting skill (see lighting-design) and not a styling skill
  (see styling-narrative).
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Camera & composition

## Why this rung exists — it is the largest single measured win in the lane

On 2026-08-26 the owner picked a camera from an A/B pair (D-152) and the exit clause
that had never passed, passed: **p2r77 read 6 pass / 4 fail, p2r78rc read 8 pass / 2 fail,
DELIVERABLE: QUALIFIES.** No object changed. The camera did.

What his camera had, measured by `frame_geometry.py` before either frame rendered:

1. **The top of the room is in the picture.** On the old camera the BF14 slat-wall top +
   ceiling junction projected to v=0.4533 against a half-frame of 0.375 — outside. Three
   independent sighted judges each said the frame read as *a backdrop*, and none of the
   repo's 34 rungs could see it, because they all measure the SCENE or the PIXELS and
   none measured the MAPPING BETWEEN THEM.
2. **The nearest object stands on the floor.** The bench's floor contact moved from
   v=-0.5223 (cropped) to inside the frame. An object whose contact is cropped is an
   object floating, as far as the eye is concerned.
3. **The brightest light in the picture has a visible source.** Four wall-washers at
   z=2.74 m sat outside the frustum, so the strongest light in the frame came from
   nowhere. The ceiling entering the frame fixed the light, not the light rig.

## Procedure

**Step 0 — the sheet and the reference first (R12, R4b).** Open the drawing-of-record
crop for the room, and at least one delivered anchor frame of the same room type from the
pool. Anchors JUDGE, never DICTATE — no copying a composition.

**Step 1 — measure before you render (R5's law, applied to the lens).**

    python pipeline/scripts/frame_geometry.py <spec.json> [--camera <name>]

Read the `FRAME CONTAINS` line. It projects the spec's own masses through the spec's own
camera, so every question below is decidable with zero render time.

**Step 2 — the three containment questions. Any NO is a camera defect, not a build one:**
- Is the room's TOP EDGE (wall/ceiling junction, or the top of the tallest wall element)
  inside the frame? A room with no visible top is a backdrop.
- Is the NEAREST object's floor contact inside the frame? A cropped contact reads as
  floating no matter how correct the geometry is.
- Is every light that lights what you see inside the frustum, or is its source
  visible/implied? Light with no source is the P3 defect class by name.

**Step 3 — the camera is DERIVED, never typed (R9 applied to the lens).** `shift_y:
-0.14` is a stored RESULT. Say what the frame must contain and let the measurement solve
it. A second manual nudge to the same camera value means it is being typed — stop and
derive it from the contents instead.

**Step 4 — depth of field, with the correction attached.** Our frames have been sharp at
the back and mushy in front; delivered anchors run the FOREGROUND sharper than the back
wall (anchor bench book laplacian p99 1090 vs far panel wall 215; our ottoman rows read
7-9 against 68-81 in the pillow plane). **Do NOT copy "every pro camera is f/1.4-2.4"** —
`docs/strategy.md:2735` records that this number came from DETAIL cameras at close focus
and does not transfer to a room camera. Judge the near/far sharpness ORDER, and change
aperture only with a measurement of both planes in hand.

**Step 5 — playblast, then judge (R5).** `build_room.py … --quick` on the new camera
before any full-fidelity frame. A camera change is exactly the kind of change that must
never have its first look at full price.

**Step 6 — one A/B pair to his eye (R3).** When two cameras are both defensible, do not
argue them in prose: render the pair, put them in the render path, and let him answer
with a frame name in one sentence. That is how D-118 and D-152 were both decided, and it
costs him a sentence.

## Refusals

- Never judge a camera from the scene graph alone — that is the exact blindness
  `frame_geometry` was built to end.
- Never change camera and objects in the same round. The pair becomes unattributable and
  both measurements are lost.
- `frame_geometry` exit 2 = COULD NOT RUN, and that never counts as clear (R11).

## Output

Write the FRAME CONTAINS numbers into the round's gate artifact — before/after, one line
per containment question — and, when a camera of record changes, a decision row in
`qa/open-decisions.json` naming who decided it and how to reverse it.

## Cross-refs

`pipeline/scripts/frame_geometry.py` · `pipeline/scripts/camera_config.py` ·
`knowledge/rendering/cycles-lighting-camera-presets.md` ·
`pipeline/scripts/look_bench.py` (anchor pool, LOCAL-ONLY sheets under `_private/`) ·
D-118, D-152 in `qa/open-decisions.json`.
