# Element 1 — Garden view + Juliet rail BUILD record (2026-07-17b, option B)

The outside of the glass-L finally IS the owner's photo. Since the curtain build
(17fdb87) the fabric was right but the world behind it was a photo STUDIO
(brown_photostudio_02) — the spec itself already recorded the truth ("floor-to-
ceiling CLEAR glass ... onto a tropical garden + a Juliet balcony rail", glz-south-w /
glz-slider notes, correction #11b) and no renderer consumed it. Same disease the
curtain materializer cured, one layer further out. This session gave the view a
data block and a consumer.

## What was built

- `spec.exterior` (canonical spec) — the view as owner-vetoable DATA:
  * `hdri`: slug/strength/rot/exposure/look for the world environment. Consumed by
    `build_room._exterior_world_args`; a DECLARED slug whose file is missing RAISES
    (the studio default must never silently return — revert-by-omission law).
  * `juliet_rail`: the black-metal rail the owner's photo shows outside `glz-slider`.
    DEPICTED, NOT DESIGNED — it exists in the photo; every dim is [est] render-tier
    (no elevation on a furniture plan; `knowledge/codes-th/mr55-residential-dimensions.md`
    has stair rails + roof-deck parapets only, NO balcony-rail height = VAULT GAP,
    no statutory value invented).
- `pipeline/scripts/exterior.py` — pure layout (LAYER LAW, no bpy, reuses
  curtains.py's plan helpers): resolves/validates the HDRI block fail-loud
  (unknown keys refused — the typo'd-key lesson), and derives the rail wholly from
  spec data: named opening rect + outline → facade plane + OUTSIDE side; bars pack
  until clear gap <= gap_max. 41 unit tests (test_exterior.py), expectations
  derived from fixture arithmetic, never pasted from output.
- `build_room._add_juliet_rail` — boxes + black POWDER-COAT (dielectric paint,
  metallic 0, albedo 0.045 — first build used metallic 0.8/0.03 and tripped the
  albedo WARN; a coated rail is paint over steel, not bare metal). `ph_model`
  opts out of the 5 mm suite bevel (would swallow a 14 mm bar) + the prefix pass.
- HDRI: `rainforest_trail` 4k, CC0 Poly Haven (฿0, asset-lever rule), fetched via
  `assets.py`. LOOK-CHOSEN from 12 garden/nature candidates viewed as thumbnails —
  dense broadleaf foliage fills the view band at every height, which is what a
  close tropical garden shows an upper floor; 360° green makes rot_deg
  composition-robust. Runner-up `pool` (real palms + hard sun, but the entire
  lower hemisphere is pool water → the room would claim an infinity pool the
  photo doesn't) is cached 4k for an owner A/B.

## Verification (3 ways + a false alarm honestly spent)

- Unit: 41 new tests; full pipeline suite 1680 green.
- Raycast (scene truth): camera→rail probes hit sheer → glass → juliet member on
  the top rail AND a mid bar; above rail height: no juliet hit; every member bbox
  fully outside the facade (min clearance = the 90 mm standoff exactly); member
  count 15 = pure layout; world env image = rainforest_trail_4k.hdr.
- LOOK (`--eyecam=curtains_south`): the drawn sheer now veils dappled tropical
  canopy instead of studio void; the rail reads as a quiet dark line + bars at the
  slider; the parked blackout S-fold column sits at the west end as render_state
  discloses.
- FALSE ALARM SPENT: I first read the rail as "rendered at the wrong x" because I
  mapped the frame left-to-right as west-to-east. A camera facing -Y puts EAST on
  the LEFT. `world_to_camera_view` projection (rail top mid → px 264,652) matches
  the render exactly; the raycast and the image agreed all along. Lesson kept:
  verify pixel claims by PROJECTION, not by mental arithmetic about mirrored axes.

## Disclosed conventions (owner-vetoable, recorded)

- Rail: square sections, 11 bars @ ~110 gap over a 1550 run (slider + 75 margins),
  top rail at 1000 [est], 90 standoff, 50 below-slab drop. If the photo says a
  different pattern/height, nudge `spec.exterior.juliet_rail` — geometry re-derives.
- HDRI strength 0.55 / rot 0 / AgX MHC are LOOK-tuned numbers in the spec, data
  like everything else.

## Adversarial review (6 lenses / 51 agents) → 9 fixes applied

The review hit the monthly spend limit mid-verify (25 of 54 agents done); the
findings whose verification COMPLETED are acted on, the rest I judged by hand.
Fixed this session:

1. **Top-level block-name typo reverted silently** (fail-loud): `exterior.hdris` /
   `juliet_rai` was indistinguishable from opt-out → garden/rail silently dropped.
   `_ext` now whitelists `{hdri, juliet_rail}` (+ underscore doc keys), the same
   law the inner blocks already enforced, one level up.
2. **Typo'd `look` value swallowed** (fail-loud): `look` was type-checked only, then
   fed into `_hdri_world`'s `try/except:pass`. resolve_hdri now validates it against
   the Blender look-name family (`_LOOK_RE`) — pure layer, no bpy.
3. **HDRI that globs but won't LOAD → magenta void at exit 0** (fail-loud): the
   missing-FILE branch raised but the unloadable-file branch (truncated / unhydrated
   OneDrive placeholder) did not. `_exterior_world_args` now pre-loads the image
   (check_existing → no double I/O) and raises on load failure / 0×0.
4. **build_rect silently ignored `exterior`** (fail-loud): a rect spec carrying it
   dropped the block. Extended the suite-only guard to `exterior` AND swept in
   `curtains`/`curtain_track` (the prior session left the identical hole).
5. **Exterior override wrongly on hero + overview** (scoping): the garden is an
   eye-level WINDOW view. Hero restages behind SOLID walls (curtains already skipped
   there); overview is the open-top hybrid CONTROL leg. Both reverted to their tuned
   studio env — the override is now EYE-ONLY.
6. **No canonical-file integration test**: the suite tested a static COPY of the
   exterior block, not the file build_room consumes. Added
   `test_canonical_spec_integration` (load-skip-derive, sibling convention).
7. **Two geometric raises untested**: `no bar field` + `cannot resolve the outside`
   had no pin (a mutation survived green). Two tests added.
8. **Bar-count minimality untested**: N_BARS/GAP transcribed the module's own
   formula; added the one-line minimality assert (N_BARS−1 would break gap_max) that
   an over-packing shared bug cannot pass.
9. **Untracked HDRI**: `rainforest_trail_4k.hdr` (+ the `pool` A/B) are committed on
   LFS with this change — otherwise fix #3 fires on every other checkout.

Tests 41 → 59 (file), full pipeline 1680 → 1698 green. All three fail-loud mutants
the review reproduced (`hdris`, `juliet_rai`, `Agx - …`) now raise; F3/F4 verified
firing inside Blender.

NOT fixed (judged out-of-scope / immaterial): `wall_thk_mm` defaults to 100 (matches
sibling curtains.py's `ceiling_mm` default; canonical spec sets it explicitly);
`_hdri_file` prefix-glob lets a truncated slug match a neighbour (inherent to the
whole HDRI system, pre-dates this diff); `look: null/""` coerces to no-look (the spec
cannot express it, but "None" is the real enum and passes — true but immaterial).

## Still owner / still open

- Rail height + profile vs the actual photo (Claude never saw the photo file —
  only the spec notes recording it); fabric/track SKUs unchanged from the curtain
  build; ceiling heights unchanged.
- The garden HDRI depicts a LUSH GARDEN, not the client's actual planting; if a
  sales render must show the real garden, that is a photography/compositing task.
- West wall (element 2) untouched; the bookshelf/vanity questions carry over.
