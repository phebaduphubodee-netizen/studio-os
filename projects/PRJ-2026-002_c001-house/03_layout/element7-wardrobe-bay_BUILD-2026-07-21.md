# Element 7 — wardrobe bay — BUILD record

**Date:** 2026-07-21 · **DD:** `element7-wardrobe-bay_DD-2026-07-21.md` (commit
`9ca73ac`) · **Manifest:** `element7-wardrobe-bay_dd-decisions.json` · **Ink:**
`element7-wardrobe-bay_ink-read-2026-07-21.json`

## What was built (data + consumer, one commit)

- **`pipeline/scripts/wardrobe_bay.py`** (NEW, pure, no bpy) — the bay's closed
  mineral joinery. Routed **BY SUBROOM TYPE** from build_suite's subroom loop
  (D-E7-3 merge ruling): `type=='wardrobe'` → `wardrobe_bay.bay_parts(sr)` owns
  every fixture; nothing can fall through to the bathroom lane's silent `[]` →
  `fix__` white slab. Joinery truth = `millwork.millwork_parts`' closed tall run
  called once per DRAWN station segment; fronts DERIVED toward the free floor
  (larger outline gap — north leg S, east leg W, BF09-2 E), never declared.
  RAISES on: missing `zone-open-south`; foreign kind; absent/unsorted/out-of-run
  stations; unknown design keys; front_stop violations; square (front-ambiguous)
  mass; zero millwork parts. The 73.0 scribe = leafless filler under the declared
  `MIN_BAY_MM` (never a hardcoded 73); the L-corner beyond the east leg's drawn
  `front_stop_mm` 7995.8 = blind carcass.
- **Canonical spec** — the three bay fixtures ink-trued (D-E7-1): north leg
  x3254.4 y7995.8 1799.7×599.9 (stations 3327.4/4428.8), east leg x5054.1
  y4621.9 599.9×3973.8 (stations 5174.1/6272.4/7373.7, front_stop 7995.8, owns
  the corner, 4.0mm outline overshoot disclosed), BF09-2 x3302.0 y5199.5
  501.5×1498.1 (drawn depth built, label conflict + fabricator note recorded,
  the flush claim deleted). NEW `ink_faces` machine-readable record; NEW
  `door_ensuite_slide` working-read record (owner_confirm **OPEN**); NEW
  `zone-open-south` full-edge opening (the phantom wall dies as data — head =
  ceiling → the edge builds NOTHING); `door-ensuite-baycut` NARROWED to the 898
  clear passage [3150,6698,3150,7596] while the ensuite-side `door-ensuite`
  stays byte-identical (the drawn REBATE, D-E7-9 merge ruling); the e5 bay
  lighting note amended (the no-camera-sees exclusion is dead); three
  `eye_camera_variants` added, all `in_subroom:'wardrobe'` (view 1 stands
  outside — disclosed semantic stretch).
- **`material_presets.py`** — ONE new row in the closed vocabulary:
  `FIXTURE_MAT_OBJECT['mineral'] → mill__{b}__cool` (the proven `__cool` token →
  microcement; no new material plumbing; no bay part can reach the oak default).
  NEW `wardrobe_bay_story_bits`: gated on the bay's own referent, wired
  unconditionally into `material_story()`, every counted/measured clause DERIVES
  (mass count from fixtures, passage width from the baycut rect, openness looked
  up BY ID with a RAISE — the cross-block pin).
- **`test_wardrobe_bay.py`** — 33 tests: the manifest's probes walked (RAISE
  contract ×10, derived-facing + swap-and-demand-red, closed part vocabulary,
  microcement-never-oak routing, containment, filler rule, blind corner,
  stations-derivation, millwork-is-the-source (monkeypatch), junction pins over
  `ink_faces` (both operands spec data), flush-claim deletion, zone-open record,
  baycut narrowing + ensuite-side byte-identical, cameras + amendment strings,
  e5 re-derivation (3→2, dropped can disclosed inside BF09-1), build_room
  routing SOURCE-TEXT pin, bathroom scope pin, story armour ×4.
- **Scope pins held:** `bathroom.py` and `millwork.py` **zero diff** (git-
  verified); no other element's geometry touched (residual #9c).

## Derived numbers (pre-computed before LOOK, the critic's ordering)

28 parts / 12 leaves, every reveal ON a drawn station: north leg
[filler 73.0 | 546.2 + 546.2 | 619.3], east leg [546.2 | 544.6×2 | 546.2×2 |
616.1 | blind 599.9-to-wall], BF09-2 [495.4×3]. Leaf height 2690 (plinth 80 +
pull-gap 30, module constants [est]). E5 bay row re-derived: grid 3 → kept 2 at
(4400, 6316.7) + (4400, 7250.0), dropped (4400, 8183.3) INSIDE the trued
BF09-1 north leg — disclosure fired; bedroom 10 @114lx and ensuite 6 @283lx
byte-identical to e5 (zero cross-zone perturbation; the DD critic's grazing-can
guess n=2/y7950 did not materialize — kept can #2 sits 745.8 clear of the
north-leg front).

## LOOK (eye renders, 256-sample GPU, pipeline/output/)

- **`wardrobe_bay_entry`** — THE PHANTOM IS DEAD: the camera stands south of
  y5850 and sees the bay interior through the throat; oak floor continues
  unbroken (D-E7-11 in pixels); north-leg mineral fronts + recessed plinth dead
  ahead; BF09-2's east fronts = the left wall (grazing; its reveals verified in
  doorlane instead); floor BARE; zero oak/brass/gloss on any bay surface. PASS.
  Honesty notes: the e5 cans' EFFECT (lit bay) verifies — the fixture heads sit
  above the frame top; the BF10-junction watch-item region is OUT of this frame
  (see below).
- **`wardrobe_bay_dressing`** — PROJECTION-VERIFIED (not axis-arithmetic): at
  the x5054.1 plane the frame maps left-edge≈y8465 → right-edge≈y6135, and the
  four visible reveal lines land at ~20%/47%/70%/94% of frame width = y7995.8
  (front-stop) / y7373.7 (station) / y6824.5 (mid-leaf) / y6272.4 (station) —
  the drawn stations to ~1%. The unbroken left 20% band IS the blind corner.
  Matte mineral, no wood grain, no gloss. PASS. Projection honesty (e2
  precedent, recorded in the cam note): a 1.6m throw cannot frame the full 2.8
  height — rhythm/material view; full height verified in entry.
- **`wardrobe_bay_doorlane`** — the ensuite doorway renders OPEN through the
  narrowed baycut (the e6 catch re-verified from the bay side): the full e4/e6
  ensuite reads through it (oak vanity + Caesarstone + basin, Purist bar + 2
  towels + paper holder, bath mat, shower glass + garden through the BARE
  casement, tub deck). BF09-2's east fronts fill frame left, mineral with
  visible leaf reveal — **the predicted 8th omission (BF09-2 ships wrong behind
  zero coverage) is PREVENTED in pixels.** The mouth stub reads as a stepped
  left jamb FROM THE BAY SIDE. PASS for the bay's own decisions.
- **`ensuite_hooks_east`** (e6 regression view re-rendered) — the doorway now
  shows the BAY'S east-leg mineral fronts + continuing oak floor through the
  passage. **CORRECTION (review E7R-1/LOOK-1, verified by geometry): the e6 jamb
  accessories are NOT intact in this frame** — see the coincident-wall finding
  below. PARTIAL: the doorway/fronts/floor read correctly; the e6 hooks/robes/
  south-jamb hand towel are occluded.

**Coincident doubled party wall (review E7R-1/LOOK-1/E7R-2 — CONFIRMED, recorded
not fixed):** the ensuite (east edge → wall x3150..3250, into the bay) and the
bay (west edge → wall x3050..3150, into the ensuite) each build a full 100mm wall
on the SHARED x3150 party plane, so the plane carries a 200mm doubled wall and
the bay's half bulges 100mm INTO the ensuite. The e6 accessories mount on the
x3150 plane and protrude only ~45mm west (hooks/robes/hand-towel at x3080..3150),
so they sit INSIDE the bay's west-wall slab and are occluded from the ensuite
camera (its west face at x3050 fronts them). **This is PRE-EXISTING (the bay
subroom's west wall predates e7; e7's baycut narrowing y6596→6698 does not touch
the jamb accessories at y6246/y7946 — they were buried at e6 too; the e6 BUILD's
"hooks/robes visible" was itself an overclaim, corrected here).** It also means
the D-E7-9 mouth stub does NOT read as a recess from the ensuite side (the bay
wall occludes it) — it reads only as a bay-side jamb step; the spec cam note and
D-E7-9 are corrected accordingly. The fix is a build_room SHARED-WALL model
change (build a party plane once / half-thickness each side) — infrastructure
sized, cross-cutting to every multi-subroom spec, and OWNED BY a future
wall-model element, NOT smuggled into e7's tail (residual #9c; the x1125 / BF10
"record-don't-smuggle" precedent). Recorded as a first-class watch-item with this
reproduction. Companion, same root: the **ensuite ring builds to z2.0** (its
subroom carries no `ceiling_mm` → build_room default 2000) vs the bay's 2800,
which is the dark wedge at the entry frame's throat top — the same black-band the
e6 BUILD already recorded as pre-existing/e4-domain.

Watch-items (recorded, not e7 defects): the **BF10-junction ~152 slit** (stale
BF10 builtin east face x3150 vs trued BF09-2 west face x3302) — occluded by
BF09-2 from every bay camera, BF10-domain (residual #9c); the **doubled party
wall** + **ensuite ceiling default** above.

## Review (workflow wf_4025a4a7 — 5 find lenses → 29-agent refute-first verify)

Ran across TWO passes (the first hit the monthly spend limit mid-verify; resumed
from cache to complete all 29). Confirmed findings and their disposition:

**Fixed in code (e7's own lane):**
1. **`h < millwork.TALL_H` silently left the closed-leaf vocabulary** (E7-CODE-1):
   below 1.6m the tall run fell through to millwork's LOW worktop branch (non-
   empty → the zero-parts RAISE never fired), so a decided full-height wardrobe
   could render as a desk. Now RAISES; test added.
2. **`open:true` on a bay fixture was silently swallowed** (E7-F2): the module
   never read the flag, so a decided-open mass would build CLOSED — the exact
   revert-by-omission the docstring bans, and `open` is live vocabulary
   (build_room.py:2490 consumes it for BF09-3). Now RAISES; module test + the
   canonical pin as second layer.
3. **Equal-gap facing tie guessed silently** (E7-CODE-2): `front_axis_sign`
   resolved a centred-mass tie to sign −1 instead of RAISING like the square
   case. Now RAISES; test added.
4. **Vacuous scope-pin assert** (E7-F3/E7-CODE-3/E7R-3): `... in ([], None) or
   True` is a tautology — it could not catch the bathroom lane growing a wardrobe
   owner. Dropped the `or True` (now `== []`); and the source-text routing pin
   now asserts ORDER (`i_pred < i_bay < i_bath` + the `continue`), so the branch
   can't drift below the bathroom dispatch and white-slab the bay first.
5. **Junction pin pinned x only** (E7R-2 geom): BF09-2's y-extent (the mouth
   line) and the east leg's back were prose-only. Added asserts tying
   `bf092.y+d == baycut south edge` and `eastleg.x+w == ink_faces.east_party_face_x`
   — "moving either datum alone goes red" now holds for the full slide geometry.
6. **Latent tag collision** (E7-CODE-6): `bay{bf}{i}` concatenated bare (`'X1',0`
   vs `'X',10` → `bayX10`). Now `bay{bf}-{i}`.
7. **Bare-floor armour was hardcoded prose + unwalked probe** (E7-F1, REAL — the
   e6 census prose-copy shape): the "floor is BARE" clause derived from nothing
   and no test pinned the bay floor empty. Added pure `wardrobe_bay.bay_floor_intruders`;
   the story clause now RAISES if any spec item/builtin intrudes on the bay
   clear floor (the polish armour can never silently order a decided item erased);
   test + mutation leg walk it.
8. **Log mislabel** (E7-CODE-4): bay masses were counted into `n_fix` and printed
   under "ensuite fixture(s) … oak / brass" — a label the zero-oak/zero-brass bay
   must not ride. Removed from the tally (the bay has its own line).
9. **Unitless story number** (E7-CODE-5): "~898 passage" → "~898mm".

**Fixed in docs / spec notes (honesty to the pixels):**
- Camera MUST-SEE lists trimmed to what each frame actually shows (LOOK-2/3,
  E7R-4): removed "full height", "plinth/pull-gap shadow lines", station y5174.1
  from the dressing view's verified list (all outside the 24mm FOV — no bay
  camera sees full height, recorded); the doorlane scribe-sliver downgraded from
  MUST-SEE to "not resolvable at this angle".
- D-E7-9 probe reworded (E7-F4): the 9.5/side figure is step 4 of the slide
  derivation, allowed only inside a NOT-QUOTABLE disclaimer — not "a lane
  clearance quoted".
- DD coverage map gains D-E7-7/-8 (E7R-5) so "every id appears" holds.
- `test_element5_lighting.py` stale docstring fixed (E7R-5): BF09-2 y5180..6680 →
  the trued y5199.5..6697.6 (the name-based assertion was always correct).

**Recorded, not fixed (out of e7 scope):** the coincident doubled party wall +
buried e6 accessories + ensuite ceiling default — see the section above.

## Test state

Baseline before e7: 1871 (pipeline/scripts + projects). After build: **1904**
(+33). Renders + .blends live in `pipeline/output/` (LFS lane law; nothing
binary rides the commit).

## Open at the owner/designer tier (unchanged by the build)

BF09-2 depth-vs-label (with BF11's); the slide-mechanism confirm
(`door_ensuite_slide.owner_confirm` = OPEN); corner-ownership sign-off; the
dashed x5054.1 stroke's meaning; every [est] z (plinth 80/18, reveal 3,
pull-gap 30, leaf head 2690).
