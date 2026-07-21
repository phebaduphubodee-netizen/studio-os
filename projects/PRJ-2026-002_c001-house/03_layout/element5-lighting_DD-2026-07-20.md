# ELEMENT 5 — Lighting (the 3 real layers) · Design Development
**PRJ-2026-002 master suite · 2026-07-20**

> PROVENANCE: DD workflow `wf_0280f6a3-7e7` (37 agents, 0 error): 7 grounded readers
> (vault lighting ×2, cycles-presets + render-defaults, PH defects, prior DDs, canonical
> spec geometry, statutory/wired tier) → 1 synthesis → 27 adversarial verify votes
> (9 decisions × 3 lenses: grounding / coherence / buildability — 0 REFUTED, every
> AMEND folded below) → 2 critics (completeness + scope; 15 findings, all resolved
> below). Scope = the ASSEMBLY stage: the three real light layers built into the
> Cycles render as spec DATA with a pure derivation module — ambient / task at the
> two mirrors / accent — plus the practicals that were built dark.
>
> WHAT THIS DD FIXES (live defects in today's render, all verified in code):
> (a) the suite renders 26 identical ambient downlights and NOTHING else = wired
> defect **PH-01** (flat single-layer) by construction;
> (b) `suite_lighting.py` accent branch sniffs kinds `headboard_tv/feature/tv` — BF14
> is kind `headboard`, so the accent is DEAD against the canonical spec (it fires only
> on the stale DO-NOT-RENDER fixture `04_visualization/cd-set_v01/bedroom_suite.spec.json:113`);
> (c) the ensuite auto-ambient achieves ~189 lux, BELOW the wired bathroom band
> 215–323 lux (`dimensional_rules.v0.2.json` bathroom 20–30 fc) — stale
> `TARGET_LUX["wet"]=200`;
> (d) the element-3 nightstand brass dome lamps are built but DO NOT EMIT;
> (e) the element-2 (BF11 mirror) and element-4 (ensuite mirror) task lights were
> DECIDED and never built — the revert-by-omission class, shapes 4 and 5 of 6.

---

## §0 Channel law (how the decisions travel — the buildability lens' unanimous amendment)

`spec["lighting"]["fixtures"]` is NOT used: that verbatim-override branch
(`suite_lighting.py:116-126`) replaces the ENTIRE auto plan on first use, freezes
coordinates so an outline move no longer moves the lights, and silently
centre-defaults any fixture missing x/y — three swallow shapes in one channel.
Instead:

- a NEW validated block `spec["lighting"]` (schema `e5-layers@0.1`) carries
  **derivation PARAMETERS, never baked fixture arrays** (derive-not-entrench,
  the test-pinning lesson from the curtain build);
- a NEW pure module `pipeline/scripts/element5_lighting.py` (bpy-free, the
  curtains.py / exterior.py law) derives every fixture from the spec's own
  geometry at build time and **RAISES on any malformed or missing referent**
  (renamed BF, absent mirror block, ≠1 bathtub, unknown key — the 831fc1b
  swallow law); consumed by `build_room.add_interior_lights`;
- the ONE code-side carry: `suite_lighting.TARGET_LUX["wet"] 200 → 270`, so
  future auto plans agree with the wired check they are scored against.

## §1 D-E5-1 — Ambient, bedroom: lumen-method grid on the NET polygon, clipped out of full-height masses → 10 downlights

Bedroom NET polygon = room outline minus the subroom band (the two subrooms tile
y5850..8650 exactly; the module RAISES if a spec edit breaks the tiling) =
`[[0,-697.8],[5500,-697.8],[5500,2650],[5650,2650],[5650,5850],[0,5850]]` = 36.49 m².
Target 150 lux (inside wired bedroom 10–20 fc = 107.6–215.3 lux,
`dimensional_rules.v0.2.json`). Lumen method (wired Φ800/CU 0.65/LLF 0.80):
n_target = 13 → `_grid_in_poly` 3×4 → 12 in-poly points
x∈{941.7, 2825.0, 4708.3} × y∈{120.7, 1757.6, 3394.6, 5031.5}.

**Full-height-mass clip (coherence lens catch):** the auto plan's envelope-grid
defect recurs one tier down — row y3394.6 puts recessed cans at (2825.0, 3394.6)
and (4708.3, 3394.6) INSIDE BF09-3's floor-to-ceiling carcass (x2353–5654 ×
y2800–3400, h2800). Rule adopted: a grid point survives only if it is outside
every builtin/fixture with h ≥ zone ceiling (BF14, BF09-3, BF10 here). → **10
fixtures, achieved 114.0 lux** — still in the wired band; every dropped point is
DISCLOSED in meta (no silent caps). CCT 3000 K via `light_warm` [1.0,0.9,0.8]
(E1 law: warm-WHITE, never the 2400 K amber). The 100-lux floor is the
STUDIO-ADOPTED analogy for a detached-house bedroom (mr39 ตาราง 3 has no house-
bedroom row) — never cited as LAW. Render: disk AREA lights z = ceiling−60,
~14 W [est, inside cycles-presets' 8–15 W hedged band], deterministic ±12 % spread
(existing behavior). Cameras: every bedroom view.

## §2 D-E5-2 — Ambient, ensuite: wet target 200 → 270 lux → 6 downlights, 283 lux

The stale target contradicts the wired band; resolved toward `dimensional_rules`
because that is what `clearance_check.check_lighting` reads. New target 270 =
mid of 20–30 fc. n = round(270 × 8.82 / 416) = **6**, grid x∈{525,1575,2625} ×
y∈{6550,7950}, achieved **283.0 lux** — inside 215.3–322.9, clears the statutory
**≥100 lux ห้องน้ำ floor (LAW, mr39 ตาราง 3)**, lands inside E4 §4's decided
215–323. AREA CONVENTION DISCLOSED (critique): 8.82 m² = the spec-convention
outline the grid is laid on; the ink-true 8.36 m² gives n=5 — the convention that
POSITIONS fixtures also SIZES them, one polygon, stated here. CCT 3000 K = both
the wired bathroom band minimum and the suite family. The north row (y7950) sits
over shower + tub: **wet-location luminaire IP / IEC 60364-7-701 / RCD are
STATUTORY-NOT-INGESTED [GAP]** — geometry note only, no IP number exists anywhere
in this DD; M&E call at CD tier. z from the ROOM ceiling 2800 (subrooms[0] has no
ceiling_mm key — the build must not read one). 3:1 honesty (verify lens): over
283 ambient the task band 538–861 spans 1.90–3.04:1 — ≤3:1 holds across ~96 % of
the band; the 850–861 sliver grazes it by ≤1.5 % (REFERENCE steering, never a gate).
Cameras: ensuite_vanity + ensuite_wet together cover all 6.

## §3 D-E5-3 — Ambient, wardrobe bay: centred aisle row, clipped → 2 downlights, RCP placeholder, deliberately uncovered

Bay 7.00 m², default band 107.6–322.9 lux, target 150 → n_target 3, single
centred row x4400, y thirds {6316.7, 7250.0, 8183.3} (row-not-grid = [est]
placement call pending the bay's fit-out). The same full-height clip drops
(4400, 8183.3) — it sits 133 mm INSIDE BF09-1's north leg (critique catch) —
→ **2 fixtures, 118.9 lux**, in band. NO eye_camera_variant enters the bay
(verified) — the placeholder status is the recorded decision, excluded from LOOK
sign-off; BF09-3 rail/under-shelf/niche accent is NOT decided here (a
decided-but-unseen value is the revert-by-omission incubator) → gaps §10.

## §4 D-E5-4 — Task, BF11 makeup mirror: element-2's flanking verticals, built as mirror-edge opal strips in the 51/50 mm pier margins

Builds E2 D2-3 VERBATIM (flanking verticals, CRI≥90, 3000–3500 K, 538–861 lux
vertical-on-face — flanking is NOT re-decided). The geometry forces the FORM: the
solid pier y3498.3..4999.6 leaves only ~51 mm beyond each mirror edge (mirror
y3549..4949), so separate sconces cannot fit → **mirror-edge-integrated vertical
opal strips**, ~30 mm wide [est], luminous z850..1550 (= the mirror field),
centres S y≈3523.7 / N y≈4974.3 — DERIVED from the mirror block + the two
casement rects (RAISE if either referent is missing). Kelvin: **3000 K** = the E4
§11.2 family resolution applied suite-wide (high CRI, not cooler CCT, renders
skin; no third number invented). Finish: opal + black-alu — **zero brass at the
mirror** (E2 D2-4 / PH-02: the windows are the luminance point). Implementation
(buildability lens): each strip = an EMISSIVE-MESH box (visible in frame — a bare
area light is invisible to camera rays) + a paired same-size RECT area light
aimed east at the seated face zone (mirror centre y4249 = kneehole centre;
aim [est] 1 m east at z1200) for clean face illumination, ~8 W [est].
**DISCLOSED DEPENDENCY (critique finding, the would-be 7th omission shape):** E2's
"sheer diffuses the casement backlight" mechanism does NOT exist yet — the curtain
system covers only the glass-L, not the two casements (the spec's own glz-west-win1
note calls casement curtains a coordinated follow-on). This DD does NOT claim the
diffuser; the strips must deliver the face band alongside BARE-casement daylight,
and the casement-sheer follow-on is held open in §10 — not silently absorbed.
Camera: west_vanity (the vanity decision-instrument view).

## §5 D-E5-5 — Task, ensuite mirror: the flanking-vs-bar GAP is DECIDED → one full-width opal bar above the mirror

The D7-law call this element owns (E4 §9.7 held "mirror-flank vs bar" open; the
vault refuses it): **BAR** — decided, built, rendered, no A/B menu.
**Confronting the source honestly (scope critic):** E4 §4 L78's row reads
"538-861 lux VERTICAL on the face, CRI ≥ 90, **flanking** the mirror" — the word
is confronted, not elided: §9.7's DELIBERATE hold-open ("mirror-flank vs bar
placement = [GAP]") outranks the row's boilerplate, and E2's "never a single
overhead" gloss was authored for the PRIMARY seated makeup station (which
correctly gets flanking, §4). Reasons, all from geometry: (1) one full-width
frameless plane serving TWO stations — per-station flanking = four verticals with
the middle pair ON the reflective plane, fragmenting D-E4-2's full-width gesture;
(2) outer-edge-only flanking leaves each face ~500 mm from its strip and the
between-basins zone unlit; (3) the ensuite is the standing SECONDARY grooming
station (E4 §11.2) — the bar's weaker under-chin modeling is acceptable here
where it would not be at the primary; (4) one bar keeps ALL mass off the mirror
plane. Form: bar length = mirror width **2047** (x1077..3124, = the cabinet, not
the 3047 counter), black-alu body + opal face, NO brass. Underside z = mirror
top + 10 reveal = **2110** (derives from `bathroom.py` MIRROR_SILL 1100 +
MIRROR_H 1000, both [est] — an owner nudge moves mirror AND bar together).
**Aim honesty (verify catch):** the earlier "25° tilt reaches the faces" claim
was FALSE (25° descending ~500 mm lands ~200–300 mm off the wall; the faces stand
~700–900 mm out, which would need the ~55–60° steepness class D-E5-8 rejects) —
the bar illuminates by **broad soft wash** (2 m physical length = the softness,
PH-05), implemented as the opal face emissive mesh + one long area light gently
inclined toward the basin line, ~16 W total [est], LOOK-tuned. Photometrics:
538–861 lux vertical at BOTH basin centres = schedule-tier targets ([est]);
LOOK verifies ordering/gradient only (§9). Build home (buildability lens): the
bar body + opal face are emitted as PURE parts in `bathroom.py` beside the mirror
constants, consumed through the same fixture-part loop — one source moves both.
**Camera (critique catch):** ensuite_vanity's level frame TOPS OUT below the bar
(~z2103 at the wall) — a NEW spec variant **ensuite_mirror** (shift_y +0.15,
stand in the dry strip) is added so the bar itself is seen; ensuite_vanity keeps
verifying the bar's WASH (gradient on mirror wall + lit face zone).

## §6 D-E5-6 — Practicals: the nightstand brass domes EMIT — 2850 K dim pools

Fixes defect (d). Both lamps emit at the spec datum `cct_k` **2850** — the
reconciliation of E4's "2850K" citation with E3's decided 2700–3000 band (spec
data sits inside the band; no third number). Implementation (buildability lens):
`_build_nightstand` re-authors `lamp_shade` as an **open-bottomed 5-face shell**
(from_pydata, headless-safe) so a small point light INSIDE the shade pools DOWN
through the mouth — MA-04 needs the glow AND the cast pool; PH-05 needs real
falloff. Emitter z DERIVED from `millwork.nightstand_lamp_parts`:
z = h + base_h + stem_h + shade_h/2 − 0.02 ≈ **h + 260 mm** (≈780 for the
canonical h520; the earlier 870 [est] is RETRACTED — it lies above the built
shade). Emitter positions = item footprint centres (N ≈ (4952.5, 2449), S ≈
(4952.5, −199.5)) — derived, not restated. Shade material gains a faint warm
emission for the glow half. 2850 K RGB stand-in [1.0, 0.88, 0.75] — interpolated
between the repo's own anchors (2400 K amber [1.0,0.82,0.60] / 3000 K
[1.0,0.9,0.8]), [est]. ~8 W each [est], tuned DOWN at LOOK until windows > lamps
in every daytime frame (PH-02 tests INCIDENT light, E3's own ruling). Reading-
plane 323–538 lux = schedule-tier target. Cameras: bed_hero (both, symmetric),
hero (N lamp oblique).

## §7 D-E5-7 — Accent: BF14 slat-wall wash — 4 aimed pools as derivation DATA, the dead kind-sniff killed

BF14 CONFIRMED as the accent target: the signature focal millwork, and grazing
light across 77 vertical slats produces exactly the directional relief whose
absence IS PH-01. Declined: BF09-3 (brass rails already sparkle; bay uncovered by
cameras) and the bookshelf (glz-west already backlights it — stacking emphasis
the 60-30-10 economy doesn't need). Channel: `spec.lighting.accent` block
{target_bf "BF14", n 4, setback H/3, axis_ref bed, aim_z 1600 [est], cone 35°
[est], blend 0.4 [est]} → pure derivation: fixture line x = 5203 − 2800/3 =
**4270**; 4 pools spacing 812.5 ≈ setback, y symmetric about the bed axis **1125.5**
(the spec's real bed centre; the workflow draft said 1125) → y∈{−93.25, 719.25,
1531.75, 2344.25} — derived live by `element5_lighting.py`, end margins ~357/456
inside the BF14 run;
aim (5203, y, 1600) → tilt ≈39° < 40° gimbal [est]. SPOT lights (data-API,
headless-safe), ~12 W each [est], 3000 K via light_warm, graded scallop energies.
target_bf resolves against builtins by `bf` — a rename RAISES (never reverts).
3:1 honesty: pools ≈3× the 114-lux bedroom ambient ≈ 340–450 lux [est schedule
arithmetic]; the day-scene daylight on the slat field may exceed the pools —
the anti-flat claim is verified at LOOK as RELATIVE layer legibility, disclosed.
Cameras: bed_hero (all 4 scallops frontal), hero (oblique at the corner).

## §8 D-E5-8 — Accent, ensuite: tub wash — two aimed pools from the dry strip

E4 §4 layer-3 (niche/cove/tub, ~3:1): NICHE — none exists in spec geometry, none
invented; COVE — RCP-deferred (E4 §11.8); **TUB WASH — chosen.**
**Statutory-smuggle fix (scope critic):** the earlier "600 mm envelope" derivation
was the IEC 60364-7-701 zone-2 extent wearing a [GAP] tag — RETRACTED. Placement
is keyed to DRAWN geometry only: the fixtures stand in the **dry strip between
the vanity front (y6577) and the shower curb / partition line (y7320/7329)** —
row y6950 [est, the strip's clear middle], selected by kind=="bathtub" (RAISE if
≠1 match): (1625, 6950) and (2625, 6950) = tub centre x2125 ± 500 [est]. Aim the
deck/water centreline (x, 8085, 560) → tilt ≈27°; the rejected 61° wall-graze is
recorded so the steepness check isn't re-litigated. Wet-location IP/zones/RCD
remain STATUTORY-NOT-INGESTED [GAP] — no number, M&E call. SPOTs ~12 W each
[est], 3000 K family; pool ≈3× the 283 ambient = schedule-tier ~850 lux target;
PH-02: the pools must lose to the casements at LOOK. Camera: ensuite_wet (tub +
pools + the daylight they lose to, one frame).

## §9 D-E5-9 — Scene integration: one warm family under unchanged daylight; LOOK is a RELATIVE instrument

Unchanged decided data: HDRI rainforest_trail 0.55 (inside the 0.5–1.5 ambient-
IBL band — the HDRI IS the daylight half of the ambient layer and the scene's
ONLY second CCT, satisfying ≥2-CCT the one legitimate way: across KINDS), AgX
Medium High Contrast, sheer drawn α0.38, blackout parked. NO fake key light; the
world-fill knob (0.12/0.30) untouched (equivalence to the DR band unestablished —
do not swap without a test render). Family audit (PH-03 impossible by
construction): 18 downlights + 6 spots + 2 strips + 1 bar at 3000 K/light_warm;
2 lamps at 2850 K — one warm family, zero electrics in 4500–5500 K, second CCT =
daylight only. **Unit-bridge honesty (critique):** lumen-method lux, Cycles
radiometric watts, and the unitless HDRI strength are three incommensurate
scales with no calibration defined — so every absolute-lux figure in this DD is
SCHEDULE-TIER; the LOOK pass verifies ONLY relative/ordering claims per view:
PH-01 ≥2 legible layers in every occupied frame; PH-02 windows brightest in every
daytime frame; PH-03 family-by-construction; PH-05 falloff (physical sizes);
20:1 / 3:1 as visual steering (both single-source REFERENCE — the 20:1 is IES
second-hand via the DR, the 3:1 is the lumen-file's Gemini ratio — never gates).
Exposure: numberless by source (DR:64), set LAST at LOOK.
**Material-story law (critique — the Gemini-polish trap):** the new luminaire
surfaces and the DELIBERATE lit state are NAMED in the render's material story
(`material_presets` lighting story bits): opal strips + bar (black-alu bodies),
glowing 2850 K dome lamps, graded BF14 wash + tub wash — so the polish pass cannot
repaint, flatten, or "unify" them away. (An earlier draft also claimed "black-alu
downlight trims" — RETRACTED by the 2026-07-21 scrutiny: no trim geometry exists,
the ambient cans are camera-invisible area disks; the story must never claim more
than the render shows.)

## §10 Gaps held open (do-not-invent — unchanged + additions)

1. **Wet-location IP / IEC 60364-7-701 zones / RCD** — statutory, not ingested;
   geometry notes only; M&E at CD tier.
2. **R9 / Rf / Rg numerics** — absent from vault; CRI≥90 is the only floor used.
3. **3500 K owner option** at the ensuite mirror (E4 §11.2 makeup-acuity) — a
   single-value swap on D-E5-5 if the owner opts.
4. **Fixture SKU / exact lumens / heights** (strips, bar, domes, trims) —
   stage-05 supplier tier; every lumen/watt here is [est].
5. **Casement sheer** (glz-west-win1/2, ensuite casements) — element-2 curtain
   follow-on, still unbuilt; D-E5-4 explicitly does NOT lean on it.
6. **Shower niche light** — E4 §7's niche has no geometry yet; when the RCP
   supplies it, its light is a NEW decision (wet-IP [GAP] binds there too).
7. **BF09-3 rail / under-shelf / bay accent** — needs a camera variant before it
   may become a rendered decision.
8. **Cove anywhere** — the 250 curtain pocket is curtains-only (NITAS +50–100);
   perimeter cove = RCP tier with a drop-ceiling section, not this element.
9. **Dimming protocol per room** (0-10V/DALI/DMX512) — vault has taxonomy +
   match-infrastructure rule only; M&E coordination.
10. **Exposure number / world-fill equivalence / Δ_light_angle thresholds** —
    numberless by source; any real gate via PR to qa/thresholds.yaml.
11. **Ensuite ceiling_mm key absence** — 2800 lives in outline_note prose;
    z pins to the room tier (spec hygiene item, not design).
12. **Wired comfort bands self-declare DRAFT** vs current IES RP — they steer
    this render tier; re-verify before gating a CLIENT deliverable.

## §11 Binding checklist (prior decisions → where built)

- E1 light_warm 3000 K warm-white family → §1/§2/§3 (all ambient), §9 audit.
- E2 D2-3 flanking verticals / CRI≥90 / 3000–3500 K / 538–861 vertical → §4
  (3000 K = family resolution inside the band; flanking form forced by the pier).
- E2 D2-4 no brass at the mirror; windows = luminance point → §4 (opal+black-alu).
- E2 sheer-diffuser mechanism → **NOT claimable** — disclosed dependency §4/§10.5.
- E3 D3-3 lamps glow 2850 K dim, 323–538 reading plane, PH-02-incident → §6.
- E4 §4 layer-1 215–323 lux → §2 (270 target / 283 achieved).
- E4 §4 layer-2 538–861 vertical CRI≥90 → §5 (bar; the "flanking" word confronted).
- E4 §9.7 flank-vs-bar hold-open → §5 DECIDES bar (D7 law).
- E4 §11.2 grooming 3000 K/CRI≥90 (3500 K = owner option) → §5 + §10.3.
- E4 §4 layer-3 accent ~3:1, ≤20:1 → §7 (BF14) + §8 (tub wash).
- E4 CCT law (one family + daylight-as-kind) → §9 audit, every fixture.
- E4 wet-IP do-not-invent → §2/§8 notes; zero IP numbers in this DD.
- Curtains pocket = curtains-only → no cove anywhere (§10.8); the accent need is
  met by the BF14 wash.
- Spec lamp cct_k 2850 datum → §6 (spec data = the reconciliation point).

## §11b LOOK pass results (2026-07-20, 6 renders @256 samples GPU)

**PASS on first render:** hero eye (BF14 wash gradient legible, lamp glow, room reads
LIT — PH-01 resolved), bed_hero (both lamps GLOW with nightstand pools, dim vs the
sheer/garden — PH-02 ✓), west_vanity (both opal strips visible flanking the mirror,
task pools on the counter, windows brightest ✓).

**TWO LOOK catches, both fixed + re-rendered:**
1. **The bar rendered OAK** — `_fixture_part_name` (build_room) had no branch for the
   new `blackalu`/`opal` mats, so both bar parts fell to the `mill__<base>` oak
   default SILENTLY (the same silent-default class as the 7 revert-by-omission
   shapes, this time in the material ROUTER). Branch added; `mill_object_role` and
   the router now carry the roles end-to-end.
2. **The ensuite mirror wall read as WAVY OAK** — raycast-diagnosed: BF10's
   floor-to-ceiling carcass (bedroom side) has its north face EXACTLY on the
   ensuite's south line y5850, coplanar with `wall_s0_0`'s face; Cycles' tie goes to
   BF10, and ABOVE z2000 (the subroom ring's default height) BF10 was directly
   exposed. A pre-existing element-4 build residual that the new task-bar wash made
   plainly visible — the DECIDED cool ground (D-E4-1) was rendering as a 5th oak
   mass. Fix: a data-driven COPLANAR-BACKER SKIN in build_suite — only an edge that a
   h≥ceiling builtin provably backs (≤2 mm) gets a 4 mm plaster skin 2 mm inside the
   subroom, floor to the ROOM ceiling, disclosed in the build log.

**Noted, not fixed here:** ensuite_wet reads hazy-bright (stacked frameless glass +
all-cool surfaces under 283 lux + casement daylight) with dark corners at the very
top of frame (camera near the subroom ring's 2000 top) — element-4 view residuals,
listed for the assembly follow-on, not lighting defects.

## §11c Pre-commit scrutiny (2026-07-21, workflow `wf_ae1948a7-c6c`: 6 trace lenses + 2-vote refute, 52 agents — 19 confirmed / 4 refuted, ALL FIXED)

The load-bearing catches, recorded because each is a recurring class:
1. **The client lane contradicted the render** — `suite_package`/`suite_rcp` derive the
   RCP + lighting schedule from the AUTO planner, which is blind to the e5 block: the
   client documents would have shown 28 unclipped envelope cans while the render shows
   the designed 29 sources. FIX: `plan_lighting` now returns
   `element5_lighting.schedule_fixtures(spec)` for e5 specs — render, RCP and schedule
   agree BY CONSTRUCTION (one source; parity pinned by test).
2. **Two sources of truth for the bar profile** — the spec block carried
   reveal/height/depth copies of `bathroom.BAR_*`. The spec copies are RETIRED (now
   RAISE as unknown keys); bathroom's constants are the one source for solid + light.
3. **The strip's paired light entrenched wall-at-x0** — box derived from the mirror
   block, light hardcoded absolute. Both now ride the same referent.
4. **The taskbar was un-gated** — every future non-e5 bathroom spec would have grown an
   emissive bar. `vanity_parts(taskbar=)` now gates on the schema opt-in.
5. **The paid polish pass dropped every data-driven story bit** — `experiment_3leg`
   called `material_story(resolved)` without spec (the element-3 latent flag, still
   live), so linen/lighting sentences never reached the Gemini prompt. Fixed both sites.
6. **`reconcile_elements` fail-loud was false** for the two intercepted bespoke shapes
   (lamped side_table, tub-chair stool) — `bespoke_built()` now refuses them.
7. **LAYER-LAW drift** — the coplanar-skin predicate lived inline in the bpy layer;
   extracted pure (`coplanar_backer_skins`) + canonical tests (exactly one skin: BF10).
8. **Mesh math** — `_arc_shell`'s th1 end cap was wound inside-out (smeared smooth
   normals at one rim end); bedroom mass-clip was blind to full-height SUBROOM fixtures
   protruding into the bedroom band (BF09-2 crosses y5850).
9. **Honesty edits** — the "legacy byte-identical" claim scoped (the wet-270 fix
   re-sizes legacy wet grids, disclosed); DD trim-phrase + 0.5 mm pool-centre drift
   corrected; three frozen [est] literals in tests re-derived from their constants.

## §12 Camera coverage map

| decision | verified by |
|---|---|
| §1 bedroom ambient | every bedroom view (context) |
| §2 ensuite ambient | ensuite_vanity + ensuite_wet (all 6 positions) |
| §3 bay placeholder | NONE — deliberate, excluded from LOOK |
| §4 BF11 strips | west_vanity |
| §5 ensuite bar | **ensuite_mirror (NEW variant)** for the bar itself; ensuite_vanity for its wash |
| §6 lamp glow | bed_hero (both), hero (N oblique) |
| §7 BF14 wash | bed_hero (frontal scallops), hero (oblique) |
| §8 tub wash | ensuite_wet |
| §9 PH battery | per-view checklist across all variants |
