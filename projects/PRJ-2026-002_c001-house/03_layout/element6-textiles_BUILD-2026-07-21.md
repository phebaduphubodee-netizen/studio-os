# Element 6 — Textiles BUILD (2026-07-21)

Builds `element6-textiles_DD-2026-07-21.md` (wf_565485c7-985, 0 cores refuted) —
the build followed the DD's **Build consequences 1-12 list, and that list only**.
Companion manifest `element6-textiles_dd-decisions.json`: every identity probe now
has a live artifact (walked by the adversarial review below). Tests 1755 → **1839**
(+84 after the review's fixes), full pipeline suite green. (The 2 standing reds in
`scripts/test_inbox_audit.py` are the parallel inbox-audit lane's, not this build's.)

## What was built

**D-E6-1 — casement sheers.** NEW pure module `pipeline/scripts/casement_sheers.py`
(curtains.py byte-untouched): sill-length flat micro-wave panels inside
glz-west-win1/2, z DERIVED from each opening's own sill/head (1015→2200, [est]),
room side by point-in-poly, wave amplitude DERIVED from the declared fullness 1.8
(one convention, not two constants). Drawn-only — `parked` RAISES until a park is
designed. Alpha = **cross-block pin** to `curtains.render_state.sheer_alpha`
(dropping/renaming the curtains block RAISES; pinned on the canonical FILE).
Consumer `build_room._add_casement_sheers` runs AFTER `_add_curtains` inside the
same `--hero` skip and RAISES if `curtain_sheer` is absent (get-or-create would
fork a second sheer identity); every ribbon carries `ph_model`. New spec block
`casement_sheers` (form / rod_offset 50 [est] / windows / state_note /
`no_blackout` recorded absence) landed in the SAME commit as its consumer.
`build_rect`'s suite-only guard now also refuses `casement_sheers`.

**D-E6-2 — BARE ensuite casements.** `D-E6-2 DECIDED BARE` appended to ALL FOUR
opening copies (envelope ×2 + subroom ×2, pinned by test); no build lane creates
fabric there (the sheers block covers exactly the two bedroom casements, pinned);
`ensuite_material_story_bits` gained the BARE line gated on the subroom's own
casements ("never add a shower curtain" — the Gemini anti-trope armour).

**D-E6-3 — towels on the locked Purist set.** `bathroom.accessory_parts` (pure,
subroom-derived — the entry itself is DATA-only, no bbox): 24in bar
(`bar_len_mm` 610 = spec data; 18in fallback is the same field, schedule FILE
byte-untouched) centred in the WC→curb segment derived from the wc/shower
fixtures; robe hooks ×2 at ±350 [est] from the door-ensuite jambs; paper holder
RE-SITED north of the cistern (derived wc_n+130 — 3D-clearance vs every WC part
is a test); 2 draped bath towels (slot-partitioned — a census the bar cannot
carry INTERPENETRATES and therefore RAISES), hand towel on the south hook +1
folded between the basin centres (derived), robes ×2 double-hung layered outward.
Hardware = the EXISTING brass row; every textile = the ONE `towel` token. Census
lives in spec data (`design.census`, D-E6-3 counts exactly) — an emitter run whose
soft-mass count ≠ census total RAISES; all-zero census RAISES (the white-box
fallback swallow, build_room:2367-2370, can never fire for this kind because the
pure layer raises instead of returning []).

**The towel token's THREE branches** (the buildability verifier's catch — the
closed `fixture_part_name` gate is one layer UP and protects none of this):
(a) `FIXTURE_MAT_OBJECT['towel'] = 'mill__{b}__towel'`; (b) `mill_object_role`
`pn == "towel"` branch ahead of the terminal `return "oak"`; (c) build_room
role-dict entry + the terry material in `_suite_materials` (greige-oatmeal
linear (0.60,0.575,0.52) [est] composition-not-SKU, rough 0.9, fabric sheen —
blackalu/opal precedent). The DD's forced touch-point executed: 'towel' left the
raises-list at test_material_presets and joined the hand-listed coupling loop.

**D-E6-4 — bath mat.** Centre DERIVED from the built shower entry gap via
`bathroom.shower_entry_gap` sharing `SCREEN_FRAC = 0.55` with `shower_parts`
(a screen nudge moves the mat — pinned by a test that shifts the shower and
checks both); 800×500×20 [est] in the drawn dry strip, north edge 50 off the
curb. No artifact claims tub-wash pooling (the refuted claim stayed deleted).
Mat rides the FIXTURE lane; the item-rug lane's closure is pinned
(`'rug' in UNAPPLIABLE_KINDS`).

**D-E6-5 — wet/dry law.** Pure 3D test: no textile part intersects the shower
enclosure volume, any tub part (incl. deck overhangs), or any glass. The story
carries "no towel over the glass or tub edge" verbatim (gated, pinned on the
canonical spec).

**Stories wired, not just written:** `casement_sheer_story_bits` (alpha 0.38,
unoccluded opal strips, BARE mirror pier) + the two new ensuite lines are all
HAND-APPENDED inside `material_story()` and asserted through
`material_story(canonical)` — the un-called-bit-function swallow is closed.

## LOOK (eye renders, 256-sample verify tier)

- `west_vanity` — both casements veiled by the drawn sheers, garden reads
  through at α0.38, panels stop at sill height, **opal strips + mirror pier fully
  unoccluded**, windows stay the brightest plane (PH-02). PASS.
- `ensuite_towels_west` (NEW cam) — bar + 2 greige towels + brass rail, paper
  holder clear of the cistern, mat flat at the shower entry gap, BARE casements
  carrying the garden. Greige reads neutral, NOT cream. PASS.
  - First stand [2900,6950] FAILED `_spot_is_clear`: `in_subroom` drops only the
    ENSUITE bbox — 250mm from the party wall is inside the 0.3m clearance of the
    NEIGHBOURING wardrobe-bay mass. Moved to x2750 (recorded in the cam note).
- `ensuite_hooks_east` (NEW cam) — **LOOK catch:** the first camera ever to FACE
  the ensuite door rendered it as SOLID WALL. The ensuite's east wall carries the
  door cut, but the wardrobe bay's COINCIDENT west wall (same x3150 plane) was
  never cut — the e4 both-coincident-walls lesson (recorded for glz-ensuite-win1/2)
  applied to windows only. Fixed as DATA: `door-ensuite-baycut` in the bay's
  openings (same rect/head; disclosed in the spec note). Same pre-existing-residual
  class as e5's coplanar-backer catch. Also re-aimed due east — the first aim
  pushed the south jamb to a grazing frame edge.

Pre-existing, NOT e6, unchanged: the black band at the top of interior ensuite
frames (visible identically in the 2026-07-20 e5-era `ensuite_wet` render); the
ensuite floor/walls rendering the bedroom's oak/plaster (the e4 clay-control
disclosure — porcelain ground is stated in material_story for the Gemini pass).

## Review (workflow wf_4a1c5120-801 — 5 lenses → refute-first verify, 16 agents)

Confirmed and FIXED in this build (tests 1834 → **1839**):

1. **Census was not ONE source** (real, caught independently by TWO lenses): the
   ensuite textiles story bit hardcoded "2 bath towels … 2 robes" instead of
   reading `design.census` — the DD's own 18in fallback (census bath_on_bar→1,
   forced by the interpenetration guard) would have built ONE towel while the
   prose told the Gemini polish to paint the second back. The bit now DERIVES its
   clauses from the census (zero-count clauses omitted; a censusless fixture —
   which the emitter RAISES on — contributes no counted prose); desync pinned.
2. **Hook side-assignment had no pin** (the verifier PROVED it: swapped s/n in
   `hook_y` and ran the full suite green): south=hand-towel / north=robes now
   pinned with door-rect-derived bounds.
3. **`material_story`'s `if not resolved` early return dropped EVERY protective
   bit** (BARE casements, terry, sheers, e5 lighting) for a spec without a
   materials block — all the anti-repaint armour hung on an unrelated block's
   presence. Pre-existing shape since e3, closed now: spec-derived bits ride
   regardless; the no-materials legacy sentence is byte-identical (pinned).
4. **Blender `.001` duplicate-name suffix** sent the exact-match router tokens
   (towel/opal/blackalu) to the silent oak default — the e5 task-bar shape one
   renaming away. Router now strips a trailing numeric Blender suffix (pinned).
5. **D-E6-5 literal-wording vs the DD's own robe siting** (real, interpreted +
   recorded): the robes plan-overlap the tub deck cap (it reaches within ~5mm of
   the party wall — ANY wall-hung piece there overlaps it). Ruling recorded in the
   test: "over the glass or tub edge" bans 3D CONTACT (the wet/dry test); robes
   must hang with ≥250mm air below them over any tub part (new pin).
6. **[est] scope** widened to cover the in-function massing literals (comment).
7. **Mat partially out of the towels_west frame** (east ~18% below frame bottom
   after the stand moved) — recorded honestly in the cam note; gap-centre
   derivation + west extent verified in-frame; ensuite_wet also covers the mat.

Recorded, NOT changed (pre-existing / other element's geometry):

- **x1125 four-way coplanar tie** (partition/tub-apron/tray/curb faces, machine-
  exact, different materials) — the BF10 Cycles-tie class, fixture-vs-fixture so
  outside `coplanar_backer_skins`' predicate. e4's element, no visible defect in
  any current frame; the ink even draws a 0.3mm offset (sub-pen-stroke — not
  quotable as a measurement). WATCH-ITEM: if a future frame shows the tie, the
  fix is a data nudge of the partition or a fixture-pair skin, at e4's table.
- The top-of-frame black band in interior ensuite shots — identical in the
  2026-07-20 e5-era renders; not e6's.

Refuted by the verify pass: "no LOOK artifact exists" (the finder scanned the
wrong directory — all renders + this record exist in pipeline/output/); one
finder quoted my draft eyecam numbers instead of the spec's finals (both verify).

## GAPs / still_owner (unchanged from the DD, held honest)

Sill/head 1000/2200 on all four casements [est]; every accessory AFF [est] (no
vault datum); Purist end-clearance vs the 680 segment unverified (18in fallback =
`bar_len_mm`); bath-linen fibre/GSM/SKU + sheer/rod SKUs still_owner; ensuite
privacy = owner geometry question; slide-vs-pocket door → jamb-hook backing gap
(named, render-safe). NEW [est] worth the owner's eye: the paper holder band
(y6640-6900, AFF650) sits directly below the bar's south towel slot — 40mm clear
in z, buildable, but both bands derive from the same WC edge; a nudge of either
is a one-line spec edit.
