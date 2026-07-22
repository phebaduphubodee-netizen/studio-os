# Element 7 — โซนตู้เสื้อผ้า (wardrobe bay) — Design Development

**Date:** 2026-07-21 · **Workflow:** `wf_649ed584-d02` (12 agents: 5 ground → 1 decide →
4 adversarial verify lenses → 2 critics; 0 core REFUTED; every AMEND applied below) ·
**Ink basis:** `element7-wardrobe-bay_ink-read-2026-07-21.json` (deterministic ink.py +
visual crops; calibration re-proven BF09-2 1498.1 vs 1500) · **NLM:** NOT FIRED —
vault-first-enough recorded as the lane (e2 precedent); every value ink-cited,
vault-cited, or honest [est]; GAPs held open instead of asked.

The bay is the suite's walk-in dressing ANTEROOM: bedroom → dressing corridor →
1250.6 throat → bay → ensuite sliding door. Three drawn masses (BF09-1 L: north leg +
east leg; BF09-2), a bare circulation floor, and NO south wall.

## Decisions (as amended by the verify pass)

### D-E7-1 — Adopt the trued ink for all three masses; BF09-2 builds the DRAWN 501.5
Spec fixture rects → ink: **east leg** x5054.1 y4621.9 w599.9 d3973.8 (runs unbroken
to the north wall, OWNS the L-corner; south end = door-sitting north jamb to the
stroke); **north leg** x3254.4 y7995.8 w1799.7 d599.9 (butts into the east leg;
drawn dividers x3327.4/x4428.8 → modules 73.0/1101.4/625.3); **BF09-2** x3302.0
y5199.5 w501.5 d1498.1. BF09-2 builds the DRAWN 501.5 (BF11 precedent e2; also inside
the vault 500-550 min-with-sliding band, tv-viewing-and-furniture-dimensions.md:41);
the −98.4 label conflict is FLAGGED to the designer beside BF11's, never machine-
resolved. The spec's "flush to ensuite east wall" is DELETED as ink-false — BF09-2
stands 47.6 off the party-wall bay face: **that lane is the ensuite door's slide lane
and BF09-2's position is load-bearing for it.** New machine-readable
`subrooms[wardrobe].ink_faces` record (party bay face 3254.4, north interior 8595.7,
east face 5654.0, lane 47.6, open-south clear span [3254.4,5552.4]) so every junction/
lane pin derives BOTH operands from spec data — never a literal in a test (kills the
predicted prose-hardcode omission). Junction pins (pure tests over the canonical
file): `north_leg.x + w == east_leg.x`; `east_leg.y + d == ink_faces.north_interior_y`;
`north_leg.y + d == ink_faces.north_interior_y`; `bf092.x == party_face + lane`.
DISCLOSED: east leg's back x5654.0 exceeds the outline edge x5650 by 4.0mm into the
wall solid (ink adopted as-is; buried, not coplanar; recorded so a future containment
check doesn't flag it as an error).

### D-E7-2 — ZONE-NOT-WALL: the phantom south wall dies as spec DATA
`subrooms[wardrobe].openings` gains `{id:'zone-open-south', type:'opening',
rect:[3150,5850,5650,5850]}` — the EXISTING mechanism: type 'opening' = sill 0, head →
ceiling; poly_walls_bpy builds no pier, no sill, no lintel, no pane on that edge.
The bedroom side has no coincident wall on this line (unlike the door baycut), so ONE
record suffices. Consumer + RAISE: `wardrobe_bay.py` RAISES when handed a wardrobe
subroom without zone-open-south — deleting the record can no longer silently re-seal
the bay. Disclosure on the record: the true ink open span is x[3254.4,5552.4] =
2298.0 clear; the last 101.6 at the east end is closed by the 200×200 pocket-terminus
column, CONCEALED inside BF09-1's east leg body. Record uses the spec-convention edge
y5850 (never ink faces) so `_openings_on_edge_m`'s 0.06m tolerance matches.

### D-E7-3 — Build lane: masses STAY subroom fixtures; NEW pure `wardrobe_bay.py`
The three masses remain `subrooms[wardrobe].fixtures` — moving to builtins flips five
consumers at once (coplanar_backer_skins, camera obstacles, e5 full_height_rects,
frame_subject_share, millwork_subpart_presets). New PURE module
`pipeline/scripts/wardrobe_bay.py` (casement_sheers precedent: own file, plan-mm, no
bpy, own RAISE contract, own tests) consumed in build_suite's subroom loop.
**MERGE RULING (main loop, resolving build-integrity's tripwire vs the scope pin):
routing is BY SUBROOM TYPE** — `type=='wardrobe'` → `wardrobe_bay.bay_parts(sr)` owns
EVERY fixture in that subroom (RAISING on kinds it doesn't know); other subrooms
continue to `bathroom.fixture_parts` untouched. `bathroom.py` stays BYTE-UNTOUCHED
(the recorded lane law — no tripwire added there). The routing-predicate-one-layer-up
hole (the e5 lesson) is pinned by a SOURCE-TEXT test: build_room.py must reference
`wardrobe_bay.bay_parts` inside the subroom loop with the type predicate (build_room
imports bpy, so a text pin is the honest testable form) + a canonical test pins the
subroom's `type=='wardrobe'`. Joinery truth = `millwork.millwork_parts`' closed tall
run, called once per drawn station segment (millwork.py BYTE-UNTOUCHED — reuse, not
modification). Materials: ONE new row in the CLOSED vocabulary —
`FIXTURE_MAT_OBJECT['mineral'] → mill__{b}__cool` (the 'cool' token already routes to
microcement in mill_object_role; the role already exists in _suite_materials) — no bay
part can reach the silent-oak default. RAISE paths: unknown kind in the bay; missing
zone-open-south; missing/out-of-run divider stations; a wardrobe fixture yielding
zero parts; unknown design keys (validate-keys, the 831fc1b swallow law).

### D-E7-4 — FRONTS: closed, handleless, matte-mineral (microcement_cool identity)
All three masses get CLOSED full-height fronts in the EXISTING `microcement_cool`
identity (#AEB2B2 rough 0.90 — the same surface as BF09-3's drawer fronts/tower back,
BF14's south jamb, BF11's cool body). GROUNDING AS AMENDED (composition lens): the
wrap does NOT literally "join the 60% ground" — #AEB2B2 vs cool_plaster #EAEDEF is
~2:1 in luminance; the honest claim is the bay joins the COOL FAMILY as a mid-value
mineral mass and RECEDES relative to any warm/figured alternative; S12
ground-subtraction is the studio inference applied, recorded as inference (the vault
§12 has no three-sided-builtin rule — SS12's own refusal). Anti-monopoly ledger line:
oak masses stay 4 (BF14, BF09-3, bookshelf shelves, ensuite vanity) — oak fronts here
would have been the largest single oak addition ever (S13 quantity = size ×
recurrence); ZERO new oak, ZERO brass, ~7m of pulls would multiply the 10% accent
into noise → HANDLELESS (the module's 30mm top pull-gap [est] IS the hardware; no
handle part exists to route, nothing for FF&E to source). RHYTHM: leaf reveals land ON
the drawn carcass stations — stations enter the spec as fixture `design.divider_stations_mm`
DATA (they are ink), leaves auto-fit per segment via millwork's LEAF_W (a ~1100 bay →
2 leaves ~550; the drawn carcass and front rhythm agree with no new schedule
mechanism). The 73.0 west sliver = leafless scribe/filler panel (filler rule = a
declared MIN_BAY constant [est] in wardrobe_bay.py, never a hardcoded 73). The corner
region x[5054.1,5654] × y[7995.8,8595.7] = BLIND carcass, no front (the drawn
front-stop at y7995.8 is the ink's own word). Z-language all [est] from module
constants: plinth 80/18, reveal 3, pull-gap 30.

### D-E7-5 — Internals: joinery-tier, NOT BUILT; open_front never borrowed
Closed fronts → rails/shelves/drawers/shoe zones are joinery-tier and unbuilt (the
render never sees behind a closed leaf; the vault fit-out sheets cover a 2000 carcass
only — stretching to 2800 would be an unconsumed [est], refused). NO module gets
`open:true` — borrowing it triggers BF09-3's open-dressing joinery and clones the
signature. BF09-2's 501.5 depth signals sliding-or-side-hang at joinery tier
(fabricator/owner note with the label flag). Hinge count for a ~2690 leaf is OUTSIDE
the vault table (caps 2400) — recorded GAP, no 6-hinge extrapolation.

### D-E7-6 — E5 bay-lighting premise amendment (citation-corrected)
The e5 record "bay = RCP-tier placeholder EXCLUDED from LOOK because NO camera sees
it" is EXPLICITLY AMENDED: the spec bay note text changes (the no-camera-sees claim
must not survive anywhere), and the 2-can row must PASS LOOK through the new bay
cameras. Positions re-derive by construction (ambient_plan reads outline +
full_height_rects reads the subroom fixtures → trued rects flow through with the
dropped_in_masses disclosure). If LOOK fails the centred-aisle [est], the fix is a
DERIVATION PARAMETER in spec.lighting (unknown keys RAISE) — never a fixtures array
(S9 stays closed). No new bay luminaires; no in-cabinet strips (vault GAP + closed
fronts make them moot). CITATION AS AMENDED (tier-scope lens): mr39 ตาราง 3 *does*
carry a single-house row — ห้องน้ำ (บ้าน) 100 lux, already e5's ensuite floor; the
honest gap claim is **ตาราง 3 has no closet/dressing (nor bedroom) row**, so nothing
statutory is quotable for the bay and nothing was invented.

### D-E7-7 — Cameras: THREE named variants + per-decision coverage map (as amended)
All three land in `eye_camera_variants` (fail-loud on typo'd names). **AMENDED per
all four lenses: view 1 as first decided could not render** — with no `in_subroom`
the bay bbox is an unconditional stand+ray block (_spot_is_clear rejects the stand at
250mm from the y5850 edge AND any ray into the bay). All three views therefore carry
`in_subroom:'wardrobe'`; view 1 STANDS OUTSIDE in the corridor (the mechanism drops
the bay bbox from the obstacle model — the stretch of `in_subroom` semantics is
disclosed in the cam note). (1) **wardrobe_bay_entry** — corridor stand ~[4430,5450]
[est], aims north: MUST SEE the south edge rendering OPEN (the first camera ever to
face the phantom), the throat, the north-leg mineral fronts, **BF09-2's east fronts
at frame left** (added per the completeness critic — the predicted 8th omission's
blind spot), the e5 cans lit, and the BF10-junction watch-item region. (2)
**wardrobe_bay_dressing** — clear-floor west ~[3500,7300] [est], aims east: MUST SEE
the east-leg fronts full height, reveals landing on the drawn rail stations,
matte-mineral (not oak, not gloss), the blind corner junction. (3)
**wardrobe_bay_doorlane** — clear-floor east ~[4900,7300] [est], aims at the doorway
plane ~[3254,7000] [est] (ray-end must stay east of the ensuite bbox — aim ON the
plane, never inside the ensuite): MUST SEE the ensuite doorway rendering OPEN through
the NARROWED baycut (D-E7-9), the mouth stub at its south edge, BF09-2's north end +
east fronts at frame left, the scribe sliver + north-leg west end. Stands are [est]
and move freely to satisfy _spot_is_clear; the MUST-SEE lists do NOT move silently.
ORDERING LAW: zone-open-south lands BEFORE bay LOOK sign-off (view 1 must never
verify a false room). Coverage map (every D-E7 id appears — manifest D-E7-7 probe): D-E7-1→2+3;
D-E7-2→1; D-E7-3/4→1+2+3 (fronts); D-E7-5→2 (no internals visible, closed-only);
D-E7-6→1+2 (cans lit); **D-E7-7→the three views themselves (this map is its own
deliverable);** **D-E7-8→all three (the story armour describes what all three
show — mineral fronts, open edge, bare oak floor, open doorway);** D-E7-9→3
(doorway open, bay-side stub); D-E7-10/11→all three (bare floor, oak floor). RESIDUALS (accepted, e4 precedent): subroom fixtures are
invisible to the obstacle model (stand correctness is on the hand-set coords + LOOK);
frame_subject_share may falsely WARN dead-wall on bay shots (advisory only). Verify
pixels by PROJECTION, not axis-arithmetic.

### D-E7-8 — Anti-repaint armour: `wardrobe_bay_story_bits`
New producer in material_presets.py: GATED on its own referent (type='wardrobe'
subroom with kind='wardrobe' fixtures — a bay-less spec emits nothing); WIRED by
hand-append inside material_story() + asserted through material_story(canonical) in
tests (an un-called bit function is silent); prose DERIVES from spec data (mass count
from the fixtures list, mineral identity from design data, openness from the
zone-open-south record LOOKED UP BY ID — RAISING if absent, the cross-block pin that
kills the armour-gate mutation; passage width from the baycut rect, never hardcoded).
Lines: closed matte-mineral handleless fronts, cool — NEVER wood-grain/oak; the bay
is OPEN to the bedroom on the south — never paint a wall there; the floor is
deliberately BARE — never add an island/bench/mirror/rug/valet; the doorway is an
open 898 passage with its mouth stub (leaf drawn-only) — never fill it, never
"clean up" the stub; the cans are deliberate, warm family; **the bay floor is the
bedroom's oak floor continuing (D-E7-11) — never tile or carpet the walk-in.**

### D-E7-9 — Ensuite-door mechanism record + THE MOUTH (merge-ruled)
Surface-slide SOUTH in the 47.6 lane behind BF09-2 = the WORKING READ (four-way
arithmetic reproduced independently by the verify pass: mouth stroke; parked-leaf
south end lands on the y5799.4 plane to 0.1mm; no north park room; BF09-2 covers the
parked leaf with 600 spare) — recorded with the owner-confirm flag EXPLICITLY OPEN
(e4 §8 Q1 stays the owner's; closing it requires an owner statement, never a silent
edit). **MERGE RULING (main loop, resolving the two lens amendments): the bay-side
cut narrows to the CLEAR PASSAGE — `door-ensuite-baycut` rect becomes
[3150,6698,3150,7596] (~898)** while the ensuite-side `door-ensuite` rect stays
[3150,6596,3150,7596] byte-untouched (e4's lane): this renders the REBATE the ink
draws — open 999.8 on the ensuite face, closed 101.6 mouth stub on the bay face (the
receiving rebate the closed leaf's edge tucks behind). View 3's aim + MUST-SEE were
recomputed against the NARROWED rect (D-E7-7). Leaf/track/rollers stay joinery-tier
UNBUILT (honest hole + stub). NOT quotable: 9.5/side lane clearances (below the
15.87 pen), the w0.48 track-tier strokes. Track hardware = CONFIRMED vault GAP (only
AELLA flush handles exist) — no SKU, no clearance minimum invented. e6's jamb-hook
backing note STAYS LIVE.

### D-E7-10 — The bay floor stays BARE (anti-reopen, citation-corrected)
DECIDED: no island, no bench, no freestanding mirror, no rug, no valet. Grounds: the
ink draws zero floor objects; the floor is the suite's circulation pivot crossed by
BOTH door lanes; an island needs 914 on all faces — geometrically impossible in a
1298.1 floor; the seated-vanity 1067-1168 row is not triggered (none drawn or
decided). CITATIONS AS AMENDED: the mr55 ข้อ 21 1.00m line is a conservative studio
APPLICATION to the intra-suite path (ข้อ 21 governs ทางเดินภายในอาคาร), not a direct
statutory command on the bay floor; the closet-lux claim reads "ตาราง 3 has no
closet/dressing row" (not "no single-house row"). Companion absences: no in-cabinet
lighting (GAP + closed fronts), no statutory closet lux quoted, no new brass/oak in
the bay. Re-opening any absence = a NEW owner/DD decision with the arithmetic re-run
— the record names the price of entry, it does not forbid the owner.

### D-E7-11 — Bay floor finish: the bedroom oak floor CONTINUES (critic catch)
Added per the completeness critic (the ensuite precedent shows a subroom can carry
its own floor; nothing armoured WHAT the bay floor is — a polish pass could tile the
walk-in without violating any line). DECIDED: zone-not-wall means ONE volume — the
bedroom's oak floor runs through the throat and bay unbroken (build truth by
construction: the poly floor is built from the ROOM outline; no floor-transition
stroke exists anywhere across the zone line — verified in the ink sweeps). Armour
line rides in D-E7-8. No new floor identity, no threshold strip invented.

## Recorded absences (verify-corrected, anti-reopen)
As returned by the workflow with three corrections applied: (a) shelf-span: "no
PROMOTED vault row carries a shelf span; ≤800-900 exists only as in-unit CONVENTION
(_inbox/nlm-element1-dressing-wall) + the BF09-3 DD's studio rule — a bay span limit
would be [est]" (the original over-correction "no such row exists in knowledge/" was
itself false at the letter); (b) mr39 wording per D-E7-6; (c) mr55 wording per
D-E7-10. Full list: no south wall (2298.0 clear span; column closure concealed);
no oak / no brass / no handles in the bay; no open_front borrowed; no internals; no
hinge count; blind corner unfronted; bare floor; no track SKU or lane-clearance
number; no pocket cavity in the 101.6 wall; no built leaf; no statutory closet lux;
no new luminaires / no fixtures-array; no internal divider in BF09-2 (the y5799.4
line is BF10-junction ink); OPEN at owner tier: BF09-2 depth-vs-label,
corner-ownership sign-off, slide mechanism confirm, the dashed x5054.1 stroke's
meaning.

## Pre-armed build risks (the two omission hunters, folded)
1. **BF09-2 builds wrong and ships green** (the predicted 8th) → BF09-2 fronts are
   now in TWO views' MUST-SEE + the routing RAISES on zero parts + junction pin on
   its x. 2. **Armour prose desyncs from the narrowed baycut** → the story bit
   derives passage width from the rect itself. 3. **Routing predicate one layer up**
   → source-text pin + canonical type pin (merge ruling, D-E7-3). 4. **Facing flip
   survives green** → per-mass front faces are DERIVED (front faces the clear-floor
   side) + a swap-and-demand-red test. 5. **Scribe threshold hardcoded to 73.0** →
   declared MIN_BAY [est] constant with the filler rule. 6. **Camera silently
   degraded to a corridor shot** → view 1's MUST-SEE pins the open-edge verdict; the
   EyeCameraError path is the loud one. 7. **Story bit gated on a nonexistent block**
   → gate = the subroom itself; zone-open lookup BY ID raises. 8. **e5-note edit and
   cameras split across commits** → single build commit (ritual). 9. **BF10 junction
   slit misread as an e7 defect** → disclosed watch-item: stale BF10 builtin east
   face x3150 vs trued BF09-2 west face x3302 opens a ~152 apparent slit the ink
   draws closed; BF10's truing belongs to BF10's element (residual #9c); LOOK notes
   it as known-stale. 10. **Grazing e5 can** (critic's guess n=2 y~7950 vs main-loop
   arithmetic n=3→2 at y6316.7/7250) → pre-compute EXACTLY via the pure module at
   build; record the real positions + clip disclosures in the BUILD doc before LOOK.

## LFS / output lane (critic catch — standing law, restated for e7)
Renders land in `pipeline/output/` (e6 precedent), NEVER in 03_layout/04_visualization
un-triaged; nothing binary rides the DD commit; `run_altcwd/` and the mis-homed
dewood PNG belong to the parallel pane's cleanup lane (director review B1) — e7 does
not touch them.

## Gaps ledger (held open, never filled from memory)
2800-carcass fit-out norms (sheets cover 2000); hinge table caps at 2400; rod
diameter/load + pull-out accessories; sliding/pocket TRACK hardware entirely; shelf
span (CONVENTION-tier only); closet illuminance (no ตาราง 3 row); wardrobe-interior
lighting; Gemini polish still billing-blocked (armour laid before the weapon fires).
