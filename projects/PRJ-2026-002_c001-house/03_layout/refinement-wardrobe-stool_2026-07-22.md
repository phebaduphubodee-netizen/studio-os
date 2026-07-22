# Refinement — wardrobe bay fronts + vanity stool (owner feedback 2026-07-22)

**Trigger:** owner, on the element-7 renders — *"wardrobe ยังไม่ค่อยสวย + เก้าอี้โต๊ะ
แต่งหน้ายังดูไม่สวย"* (owner ground-truth on a render = the ONE instrument he
operates; his aesthetic verdict outranks the design theory — memory
[[owner-is-an-engineer-not-a-designer]]).

## Diagnosis (from the renders, not guessed)

Both pieces read as **plain smooth solids** — the one thing the suite's whole
design language is built to avoid. Everything else in the room earns its beauty
from TACTILE ARTICULATION that catches light: the oak slat headboard, the fluted
ensuite vanity base, the wave curtains, the shadow-gap reveals. The wardrobe and
the stool were the two pieces that never got that treatment.

- **Wardrobe bay fronts** (`wardrobe_bay_dressing`): flat matte cool-grey
  full-height leaves (~550 × 2690), 3 mm reveals invisible at render scale →
  reads as a blank LOCKER wall / cold slab, not designed joinery. The e7 DD's
  "recede as quiet mineral" (anti-monopoly, S12) went past *quiet* into *dead*.
- **Vanity stool** (`west_vanity`): a uniform-height annular wrap + a flush seat
  disc → reads as a ceramic BUCKET / ice bin, not an upholstered tub chair. No
  cushion definition, no back-vs-arm differentiation, pale tone dissolving into
  the equally-pale counter and drawers.

## Decisions (refinement of decided elements — no new DD; the owner's verdict IS
the design signal; both stay INSIDE their element's decided constraints)

### R1 — Wardrobe fronts: VERTICAL FLUTING (reeds + shadow grooves)
Each closed door leaf becomes a recessed **backer + vertical reed battens** proud
of it (`wardrobe_bay._flute_leaf`; REED_PROUD 13 / PITCH 55 / GROOVE 30% [est]).
- **Why it's the right move, not just texture:** it brings the bay into the
  suite's own shadow-line language (slat wall / fluted vanity / reveals), so it
  reads as bespoke joinery that casts REAL grooves — visible in raw 3D and
  surviving the Gemini pass — and "detail-rich = sells expensive" (north star).
- **Anti-monopoly INTACT:** still the cool `microcement` identity, ZERO oak added
  (the DD's core reasoning survives — the reeds add tactility, not a 5th warm
  mass); still closed + handleless (the pull-gap kept); the leaf-to-leaf reveals
  still land on the DRAWN carcass stations (derivation unchanged).
- **Bbox-safe:** the front plane is UNMOVED — reeds fill the leaf's own proud
  depth, grooves recess toward the carcass — so nothing exceeds the plan
  footprint (the CAD invariant). 12 leaves → 12 backers + 119 reeds (147 bay
  parts total, all `mineral`, all unique-named).

### R2 — Vanity stool: real TUB-CHAIR silhouette
`millwork.tub_chair_curved` + `build_room._build_tub_chair`:
- **Swept rim** — the wrap is now TALL at the back (the real backrest = the label
  rim height) sweeping DOWN to LOW arms at the opening (a hand-rest rise above the
  seat). `_arc_shell` applies `arm + (back−arm)·sin(π·t)` per arc vertex. This is
  the silhouette that separates a tub chair from a bucket.
- **Proud domed cushion** — the seat pad sits ABOVE the seat plane and BELOW the
  arm rim, gently domed (top taper), inset from the shell → reads as a cushion
  nested in the wrap, not a flush disc.
- **Deeper greige linen + more sheen** (0.40,0.37,0.33 / sheen 0.45) so the fabric
  reads as fabric against the pale counter, still the ONE bed-base textile family
  (D1-A — not a new tone); legs the bench dark, tapered, visible.
- Stays inside the element-2 curtain-wave law (identity IS a curve — refine the
  curve, don't box it) and the clay-ceiling ruling (the single Gemini beauty pass
  still owns the final soft upholstery detail).

## Verify
Tests: tub_chair rim/seat pins updated to the swept keys (`z1_back`/`z1_arm`/
`dome_z`); a new `test_fronts_are_fluted_reeds_proud_of_a_backer` pins the
fluting; the station-derivation + facing-swap pins updated to be fluting-robust
(backer = the leaf proxy). Full pure suites green.

## LOOK (256-sample renders — verified)
- `wardrobe_bay_dressing` + `wardrobe_bay_entry`: the flat grey slab is GONE — the
  walk-in now reads as floor-to-ceiling **fluted joinery wrapping three sides**,
  the reeds catching a soft vertical rhythm and casting real grooves, the plinth
  recess + warm oak floor grounding it. Reads as a designed luxe dressing room,
  not a locker. Fluting NAMED in `wardrobe_bay_story_bits` so the Gemini polish
  keeps the reeding (anti-repaint armour).
- `west_vanity`: the bucket is GONE — the stool now shows a **tall curved
  backrest** sweeping to low arms with a proud cushion, reading as an upholstered
  tub chair (confirmed in the mirror reflection too). Tone deepened; still the one
  linen family.

Full pure + project suite: **1909 green**.

## Open (owner to judge on the new renders)
Whether the fluted mineral now reads "สวย" or wants a further move (a warmer
greige tone / a horizontal drawer-bank break); whether the tub chair silhouette +
cushion read as upholstered. Beauty is his call — these renders are for his eye.
