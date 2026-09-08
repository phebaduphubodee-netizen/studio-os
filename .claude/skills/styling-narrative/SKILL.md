---
name: styling-narrative
description: >
  Style a room or a vignette the way a designer does — story first, then the object list,
  then counts and placement, then a measurement that the objects actually reached the
  pixels. Use when adding or arranging decor, filling shelves / nightstands / benches /
  open casework, when a critic says the room reads empty, staged, unnatural or
  "half-made", when choosing a style for a room, and before any shopping round (pair it
  with the acquisition protocol). Consumes knowledge/styles/*. Not a sourcing skill and
  not a camera skill.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Styling — the story comes before the objects

## Three standing owner orders live here, and all three are still open

- **ORD-2026-08-23** — the style is CHOSEN BEFORE objects are selected, and chosen as
  DATA the machine reads, not as a document. (STY program: 9 slots, 4 signed.)
- **ORD-2026-08-25c** — styling is STORY-DRIVEN, start to finish.
- **ORD-2026-08-26** — the built-in's contents still do not read as natural.

## What the measurements say the problem actually is

- **POOL, not arrangement.** Delivered work carries **25-40 objects per frame**; this lane
  had **~8**, all already placed. p2r84 proved the set was locked by four of our own code
  rules and unlocked them — the count went 5 → 8 and stopped, because there was nothing
  left to place. **A styling round with an empty shelf of assets is a shopping round.**
- **Share of frame, not count of objects.** C2 gave "the wardrobe looks empty" its first
  number at p2r85: headboard 7.9% + curtain 12.2% + ceiling 2.6% = **22.7% of the frame
  carries no information at all.** Judge by area, not by inventory.
- **Cadence.** A 50-frame survey of delivered work reads **1-2 items per cell/bay**, not
  one per shelf and not a crowd.
- **Bought ≠ in the picture.** p2r86 bought 9, one survived to the scene, and its dump
  said `in_frustum=True occluded=True` — **zero pixels moved.** Nothing counts until it
  is measured on the frame's own matmask.

## Procedure

**Step 1 — STORY (ORD-2026-08-25c).** Write, in two or three sentences, who lives here,
what they just did, and what time it is. This is the thing that produces an object list a
prop stylist would recognise; a list assembled from categories produces a showroom.
`knowledge/styles/decor-placement-grammar.md §6` grounds this step (story → object list).

**Step 2 — STYLE AS DATA (ORD-2026-08-23).** Check the STY slots before choosing anything:
`plan_status` prints which of the 9 are signed. An unsigned slot renders as a legacy
default that no one chose — sign it in the spec, or say plainly that this round runs on
the legacy value. Style membership criteria: `decor-placement-grammar.md §7`.

**Step 3 — OBJECT LIST with counts, from the grammar and not from taste.**
`knowledge/styles/decor-placement-grammar.md`:
- §1 odd rule mapped to surfaces: **3** on a nightstand or a compact bay, **5** on a
  dresser or credenza, **7** on a long table or multi-bay run. Too heavy → remove the
  smallest item.
- §1 decorative triangle: tallest at the back is the anchor, medium **½–⅔ of the tall
  one**, low item grounds the front. A flat skyline reads unresolved.
- §1 contrast footprints: never two identical-height, identical-base neighbours.
- §1 depth layering: largest first, medium next, small last; tall/flat leaned at the
  rear, trays and low platforms at the front.
- Symmetry legitimately OVERRIDES the odd rule at flanking bed positions.
- **§4 says there is NO cited total count for a room. Do not invent one** — and never
  quote a **[SYNTH]** number as if it were an industry convention; the file marks every
  value **[CITED] / [1SRC] / [SYNTH]** for exactly this reason.
- Bed vignette → `knowledge/styles/bed-styling-grammar.md`. Palette → `color-composition.md`
  (60/30/10; the lane measures it off pixels and is currently 0.300 away).

**Step 4 — SOURCE what the list needs.** If the list names classes the shelf does not
hold, this becomes a shopping round: follow the acquisition protocol
(`pipeline/scripts/blenderkit.py status` FIRST — the baseline order is now a refusal),
and remember the panel judges a VENDOR THUMBNAIL, not your frame at your distance in your
light. Two instances paid for that lesson (the cognac bag, the card-fold garments).

**Step 5 — PLACE by contact, never by coordinate (R9).** `rest_on` / `centre_on` /
measured offset from a named datum. A `nudge` is the tell that a derivation is missing.
Open casework has its own grammar: `decor-placement-grammar.md §5`.

**Step 6 — MEASURE THAT IT REACHED THE PICTURE. This step is not optional and it is
where the last three rounds died.**
- Scene dump: is the piece `in_frustum` AND not `occluded`? A cell the camera cannot see
  is not a styling slot.
- Matmask: how many PIXELS does each new object hold? Report the number, not the
  intention.
- `style_measure` / `style_check` for the palette split; `id_mask.py` to count by object.

**Step 7 — HAND IT TO EYES.** Spawn the `cold-critic-c2` agent on the finished frame and
run the cross-vendor rung. **A styling item that a critic's eye filed cannot be closed by
the builder's own measurement** (closure grammar) — close it when the eye stops filing it.

## Refusals

- Never fill a shelf to make it look full. Delivered work leaves gaps; `§5` says so.
- Never treat an INSTANCE verdict ("this bought one is a mess") as repealing the CLASS
  order. The answer to a bad purchase is a different purchase (R13).
- Never let a code rule silently pick the set. Four of ours did, for five rounds, and the
  frame looked like taste.

## Output

The story paragraph, the object list with its counts and their grammar citation, and the
pixel/occlusion measurement per new object — into the round's gate artifact. New classes
that could not be sourced become a declared gap with a price, never a modelling task (R8).
