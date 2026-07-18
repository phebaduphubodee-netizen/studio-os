# Element 2 — West wall BUILD record (2026-07-17)

The west wall the bed FOOT faces is now BUILT geometry, not a spec estimate. Element 2
= an OPEN display bookshelf + a LOW makeup vanity BF11, with TWO casement windows in the
wall above the vanity. The premise was ink-trued (adversarial read) and owner-confirmed
(windows + low vanity), then designed vault-first and materialized.

## Provenance chain
- **Ink read** → `element2-west-wall_ink-read-2026-07-17.json` (+ `.png`): 5 independent
  readers + 3-lens adversarial verify. The spec was materially WRONG (BF11 freestanding
  at x306 not x0; west wall NOT solid — two ~600 windows; bookshelf 1800 not 2046).
- **Owner premise** (2026-07-17): the two openings are casement windows; BF11 is a LOW
  ~750 seated vanity (windows show above it).
- **DD** → `element2-west-wall_DD-2026-07-17.md`: grounded design decisions (D2-1..D2-5).

## What was built

- **Spec** (`master-suite.CANONICAL.spec.json`): bookshelf y130→248 / d2046→1800;
  BF11 x0→306 (freestanding) / y2650→2600 / w600→498 / h750 kept / `face:E`;
  `room.openings` += `glz-west-win1` (y2898.4–3498.3) + `glz-west-win2` (y4999.6–5599.5),
  sill 1000 / head 2200 `[est]`; BF11 `design.mirror` block; `eye_camera_variants` +=
  `west_vanity`, `west_bookshelf`.
- **`millwork.py`** — two PURE branches (bpy-free, CAD-safe by `part()`):
  * `kind=="bookshelf"` — an OPEN grid (oak shelf boards on a COOL/microcement carcass,
    NO back panel; verticals keep every bay ≤ MAX_SPAN). Intercepts the tall-door-run
    branch that h1800 would otherwise hit.
  * `kind=="vanity"` — a Caesarstone COUNTER over two drawer banks that FLANK a seated
    kneehole (design-driven width/centre); drawer fronts + body + toe = cool.
- **`material_presets.py`** — `caesarstone_quartz` (cool dielectric quartz) +
  `mirror_silver` (metallic near-mirror) presets; `mill_object_role` routes
  `counter*`→caesarstone, `mirror*`→mirror, `cool*`→microcement.
- **`build_room.py`** — registers + routes the two new materials; `_add_vanity_mirror`
  builds the frameless mirror on the wall between the windows from `design.mirror`
  (fail-loud on a malformed block; a decided element, never reverted by omission).
- **The two windows** cut + glaze via the existing `poly_walls_bpy` (sill band + glass
  pane + lintel); the garden HDRI shows through them.

## Design (grounded — DD §1/§4)
- The west wall is the **COOL counterpoint** to the warm oak signature (east BF14 /
  north BF09-3) — which is how D1-A's 60-30-10 anti-monopoly is kept (no third oak mass).
- Counter = **Caesarstone** (durable/non-porous, `caesarstone-engineered-stone-th.md`);
  **frameless mirror**, **brass low-profile-or-none** — PH-02, the two windows are the
  luminance point (`render-defects.md#L51`).
- Vanity counter 750 (ergonomic 711–762); mirror centre 1250 AFF (seated 1120–1267);
  kneehole 1400 (knee ≥196). Bookshelf shelves ~345 clear, bays ≤ MAX_SPAN.

## Verification
- **Unit**: +10 element-2 tests (bookshelf open-grid + no-back + bay-span; vanity
  kneehole + full-run counter + design-driven kneehole; canonical-spec integration;
  material routing + preset typing/pinning). `test_millwork.py` + `test_material_presets.py`
  = 207 green; **full pipeline suite 1698 → 1708 green**, no regression.
- **Build**: Blender 5.1 `--eye --eyecam=west_vanity` → EXIT 0; 8 openings cut / 7 glazed,
  5 built-ins with real joinery, mirror built, curtains still 3 legs.
- **Raycast (scene truth)**: camera→mirror hits `mill__bf11vanity__mirror` [silver];
  camera→window1/2 hit `glass__*` [glazing] (glass, not masonry); camera→counter hits
  `[m_mill_caesar]`; pier above the mirror = cool plaster; world env = `rainforest_trail_4k.hdr`.
- **LOOK** (the D7 decision instrument): `west_vanity` — the low vanity below two casement
  windows flanking the frameless mirror, garden through both, Caesarstone counter over cool
  drawer banks; reads clean/cool (the deliberate counterpoint), garden supplies the colour.
  `west_bookshelf` — the open oak-on-cool grid, see-through (no back) to the SW garden glass +
  curtain behind. Both realize the premise. (Render pngs in `pipeline/output/room_bedroom_suite_
  eye_west_{vanity,bookshelf}.png`.)

## Adversarial review (4-lens / 12 agents) → 4 findings, all fixed

The review (correctness / revert-by-omission / integration / test-quality lenses, each finding
adversarially verified against the real code) found 4 distinct defects (2 blocking); all fixed:

1. **[BLOCKING] Mirror geometry copied from the kneehole** (1400w × 900h, centre 1250) —
   contradicted its own DD D2-3 (field ~700, centre ~1200) + ergonomic 610-762, and self-
   contradicted (decision "~1200" vs _note "1250"): a wrong-sized mirror on every west_vanity
   view. FIX: h 900→700, sill 800→850 (centre 1200); width 1400 KEPT as a deliberate wide
   pier-mirror (documented in the spec _note + DD). Pinned by test (field 610-762, centre 1120-1267).
2. **[BLOCKING] Caesarstone counter + silver mirror absent from `material_story()`** → the
   Gemini render-polish prompt was told the millwork is oak, so it would warm the cool counter
   (killing the counterpoint) / repaint the frameless mirror — the cardinal revert-by-omission.
   FIX: `millwork_subpart_presets` gained a `kind=='vanity'` branch (caesarstone + mirror roles) +
   `_MILL_SUBPART` rows. Pinned by a canonical-spec `material_story` test.
3. **Mirror reverted silently on spec-block omission + zero unit coverage.** FIX: extracted the
   find+validate to a PURE `millwork.vanity_mirror_box` (build_room consumes it); a canonical-spec
   test now asserts BF11 resolves a well-formed mirror (catches removal/typo in CI, not only at render).
4. **Vanity kneehole values unvalidated** (the headboard branch raises on bad design values; the
   vanity branch didn't) — a metre/mm slip (1400 vs 1.40) silently built a seat-less sideboard /
   floating counter. FIX: the vanity branch RAISES on implausible `kneehole_width_m`/`center_frac`/
   collapsed kneehole, matching the module's fail-loud contract. Pinned by test.

Tests +4 guards (14 element-2 total); **full suite 1708 → 1712 green**; re-rendered west_vanity
with the corrected mirror (log confirms material_story now names the Caesarstone counter + the
frameless mirror; mirror built 1400×700 @ sill 850 → centre 1200 AFF).
NOT fixed (out of scope, noted): `experiment_3leg.make_leg_b` calls `material_story` WITHOUT spec,
dropping ALL millwork subparts (element-1's brass/microcement too) on that experiment path — a
pre-existing limitation of that experiment, not an element-2 regression.

## Still owner / still open (DD §3/§5)
- Window **sill/head** height (`[est]` 1000/2200; vault + codes-th gap — arch-plan to confirm).
- BF11 **depth** 498 (drawn) vs 600 (label) — building the drawn 498; designer to confirm.
- **Curtains on the two west windows** — sheet draws them; the west curtain_track leg
  (y-450..2650) does not yet reach them — coordinated follow-on.
- **Brass on the vanity pulls** vs none (default minimal); makeup-light fixture SKU (stage 05).
