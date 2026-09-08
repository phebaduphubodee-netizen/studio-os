# สภาพผ้าบนเตียง / Bed-cloth state mechanisms — corner splay, hem resonance, loft, tucks, stack-on-cushion dent

> PROVENANCE: promoted 2026-08-13 from three staged DR units, all from NotebookLM
> notebook `ae3dd665` (blender-cloth-corner-drape corpus):
> - `knowledge/_inbox/dr-cloth-corner-drape-2026-08-11.md` (turn 1 — corner
>   held open; already CONSUMED into code at p2r22/p3r2 before this promotion)
> - `knowledge/_inbox/dr-cloth-hem-serration-2026-08-12.md` (p2r25 R1 stop —
>   periodic sine-hem)
> - `knowledge/_inbox/dr-cloth-state-loft-tuck-cushion-2026-08-13.md` (owner
>   verdict #2 p2r26 + C2-r27#1 + the bench folded-stack site)
> - `knowledge/_inbox/dr-cloth-tuck-hands-2026-08-13.md` (turn 5 — the p2r28 R1
>   stop's own question: a hand-tuck that is not a clamp; distilled 2026-08-14
>   into §5's successor-mechanism table before the p2r29 re-entry, per the rule)
> Raw turns: `knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json`.
> **Tier REFERENCE — practice-report grounding, not domain truth, not statute.**
> No parameter below may gate a deliverable by itself; a value becomes live only
> when a named file consumes it and a LOOK/critic round judges the result.

## ลำดับอำนาจ / Authority + precedence

1. What a run of the actual solver MEASURES outranks every parameter below —
   starting points and a diagnostic map, not settings of record.
2. `pipeline/CLAUDE.md` §Blender build law binds: geometry via the DATA API, no
   `bpy.ops` on geometry, headless one-process-per-job. Modifiers (Soft Body,
   Hook, Displace, Smooth) and keyframes are data-API; the effector-weight
   keyframe path must be verified headless before first use.
3. This file.

## 1. Corner splay (มุมผ้ากางค้าง) — CONSUMED, kept here as the map

Diagnosis (2026-08-11 DR): a free corner must bend in two directions at once;
the default ANGULAR bending model resists that double curvature like a shell,
premature self-collision repulsion inflates an air bubble between folds, and a
55-frame bake freezes the corner mid-splay.

Ranked fixes and their consumption state (of record in
`pipeline/scripts/drape.py` + `pipeline/scripts/build_room.py`, gate-DELIV001-P2r22):

- `bending_model = 'LINEAR'` + bending 0.15-0.35, mass ~0.12 — CONSUMED
  PER-PIECE (throw + coverlet; the duvet keeps ANGULAR for its standing-fold
  preset). Failure mode: corner shard collapse if bending falls too low.
- self-collision distance 1-3 mm + self_friction 5→~12-15 — CONSUMED.
- frames 55 → 120-150, quality 12, collision_quality 8 — CONSUMED.
- Sewing-spring corner darts (`use_sewing_springs`, `sewing_force_max` 10-25) —
  recorded NEXT mechanism, needs dart cuts in `softgoods.flat_sheet`.

## 2. Hem serration (คลื่นคาบสม่ำเสมอเหมือน sine) — NOT yet consumed

Diagnosis (2026-08-12 DR): a UNIFORM quad grid draping under gravity is a
physical-numerical RESONATOR with a **single dominant buckling eigenmode** —
compressive stress along the free hem resolves at one wavelength. The LINEAR
bending model on a regular grid is *more* susceptible (grid-aligned virtual
cross-springs), and uniform shrink expands every structural spring identically
— exactly the symmetry the eigenmode needs. Bending stiffness only scales the
wavelength (~(B/K)^(1/4)) — which matches our p2r25 measurement (same lag,
softer teeth: autocorr 0.434→0.489, not reduced).

Levers, ranked; the two already-spent mechanisms (slack field, hem bending)
never broke the symmetry, so these are NEW mechanisms, not re-turns:

1. **Hem MASS** — a weighted hem strip: body ~0.12 → hem 0.25-0.5 kg (2-4×)
   via the mass vertex group. Never touched in our lane.
2. **Symmetry-breaking vertex SPACING at the hem** — irregular in-plane station
   spacing (or triangulated hem topology) removes the single eigenmode. The
   sheet stays FLAT — the enter-smooth law is untouched; this is the
   "irregular cell" half of the r23 triage suggestion, now with a mechanism.
3. **shrink_max ≤ ~5% along the hem** — over-contracting the edge is its own
   pucker source (throw currently ≈3%, inside the band; check per piece).
4. **Post-sim Smooth modifier on the hem vertex group** (factor ~0.5, 5-15
   iterations, after Cloth, before Subdivision) — render-side kill switch,
   damps serration, keeps aperiodic primary folds.
5. Simulate coarse, render fine (SurfaceDeform) — industry frame; heavier.

What this does NOT license: pre-wrinkled feedstock (z-noise). Spacing jitter is
in-plane and flat; the solver stays the only wrinkle author.

## 3. Stack-on-cushion dent (กองผ้าพับบนเบาะ) — CONSUMED p2r28

Diagnosis (2026-08-13 DR): the folded stack sits on a RIGID cushion, so contact
reads as plastic-on-plastic; C2 filed "ผ้าพับวางบนเบาะนุ่มต้องยุบ" four rounds
running and every knob available was a forbidden re-turn.

Mechanism: convert the cushion to a deformable target with **Soft Body** —
**goal stiffness ~0.5** via a painted vertex group (core holds, surface
yields), edges pull/push ~0.8 — so the stack DENTS the cushion. First
mechanism for this site that is not a knob re-turn.

CONSUMED 2026-08-14 (`drape.dent_soft_body`, gate-DELIV001-P2r28, D-046) with
three measured corrections the DR could not know: (1) a static presser has no
weight — the press must be a MOTION (keyframed travel; probe first measured
the cushion RISING off the collision field); (2) the soft body's own gravity
must be ZERO — the seat's rest shape is already its settled shape, and leaving
gravity on double-applies it; (3) the dent is measured on the yield band's own
verts — a z-window filter returned its own constant (36.0 mm twice) because
the overhanging stack puts seat-side verts in the presser's footprint.
Result: 23 mm dent from a 16 mm press; the four-round critic item was absent
from the next blind C2 read.

## 4. Batting loft (duvet/coverlet all-over undulation) — CONSUMED p2r28

The full frame is sim-coarse-render-fine (SurfaceDeform + post-sim Solidify
~10 mm) — heavier pipeline change. The REACHABLE half first: **procedural
quilting/loft via displacement driven by a distance-function thickness** on the
render mesh, no re-sim. Displacement on a subdivided cage is already
R8b-lawful.

CONSUMED 2026-08-14 (`softgoods.boundary_dist_weights` → `drape._freeze`
vertex-group solidify, gate-DELIV001-P2r28, D-047): 18→36 mm graded by
edge-distance, with two additions the DR did not carry — the CREASE is an
extra distance source (a 180° fold compresses batting; also the two layers'
solidify normals point OPPOSITE ways on a folded lattice, so an untapered roll
grazes its own visible surface), and the thickness biases UPWARD
(solid_offset 0.4) because batting squashes flat against what it lies on and
the lofted inner shell must clear the collider stack. duvet_fold octave
energy moved 1.91x → 1.80x toward the anchor.

## 5. Tucked-sheet fold irregularity (รอยเหน็บมือ) — R1-STOPPED p2r28, successor staged

Three techniques for the ruler-straight tucked fold:

- **Hook modifiers on hem vertex groups parented to animated empties** = the
  hand that tucks — localized asymmetric folds.
- **Gravity ramp keyframed 0.0→1.0 over ~40 of 120-150 frames** — tucks slide
  and settle instead of bouncing rigid.
- Asymmetric initial state (rotate the sheet before the drape): the 45-70°
  figure smells like a loose-drape number — verify before using on a MADE bed.

MEASURED DEAD END 2026-08-14 (2 mechanism cycles, R1 stop — gate-DELIV001-
P2r28): hook + pin weight 1.0 is an infinite-mass CLAMP, not a hand — the
settling roll lofts ~27 mm around press points frozen at feedstock height, so
every dip bottoms at one plane (35.8/33.4/33.3 mm, then 28.5/26.9/26.9 after
halving travel — cv 0.03 both, uniform by construction). The ramp lever is
also COUPLED to pins: on an unpinned sheet the weightless first third slides
laterally (52-64 mm proud, invariant to slack). Ramp CONSUMED per-piece where
pins exist (bench throw); duvet ramp waits for the tuck pins.

SUCCESSOR MECHANISMS (2026-08-13 DR, the stop's own question — four ranked,
distilled 2026-08-14; the stop record above is the negative control every one
of them must beat):

1. **SPRING PINNING (partial pin weights) — ranked first for this lane.**
   Radial gradient in the pin group (center ~0.5 falling to ~0.1 over ~50 mm)
   + `pin_stiffness` in the **1.5-4.0** band (start 2.0) — the pin becomes a
   spring, the press yields to local tension, dips vary organically; the
   solver stays the author. Failure mode: **spring lag** — stiffness/weights
   too low and the loft pulls the pins out (press flattens away). LANE
   CONSTRAINT: our solver sets `pin_stiffness = 5.0` for ALL pins; the tuck
   path needs its OWN stiffness, never a global re-tune (the duvet's real
   pins are a different mechanism).
2. **TIMED PIN RELEASE** — hard-pin through settle (~frame 45), keyframe
   stiffness to 0 over ~20 frames. Failure mode: **elastic snap** (stored
   spring energy → self-collision instability). If used, verify the
   pin_stiffness keyframe path headless first (same caveat class as the
   effector-weights ramp).
3. **POST-SIM HOOK (falloff sculpt after the sim) — REFUSED BY PRECEDENT.**
   Authored guidance is a typed result (R9's family); the DR's own matrix
   concurs (wrinkle realism LOW, folds don't accommodate the press).
   Recorded so nobody buys it later.
4. **FINGER COLLISION PROXIES** (animated capsules, friction 20-40). Maximum
   realism, but failure mode **wrinkle pop-back** is ARMED for us: cloth has
   perfect elastic memory and our duvet deliberately keeps high bending
   (standing-fold preset 2.6) — so (4) likely needs (1) as its holding
   mechanism anyway.

Acceptance test unchanged: `clothcheck` crease believability — depths vary
inside the §6 chaos band, crease aperiodic.

CONSUMPTION 2026-08-14 (p2r29, gate-DELIV001-P2r29): (1) and (2) are both
MEASURED DEAD in our solver, two different ways:

- **(1) SPRING PINNING — dead in 2 cycles (R1 stop #2 for this site).**
  Cycle 1 (weights 0.5→0.1 over 1.2× the grid cell ≈ 50 mm, stiffness 2.0):
  the DR's named failure mode arrived on cue — spring lag pulled two of three
  hands out (depths 19.8/4.1/5.4 mm, cv 0.73 over the 0.60 damage line) and
  the slackened crease found a periodic mode (autocorr 0.871 — the §2
  eigenmode family surfacing on the fold line). Cycle 2 (stiffness 3.5, the
  DR's own counter, inside the band): periodicity cured (0.622) and wander
  healthy (rms 22.8 mm), but the spread blew past the band's other end —
  20.3/9.0/0.0 mm, cv 0.85, hand 3's press fully absorbed. What the pair
  measures: LOCAL tension along the crease differs by construction (the
  flank turndowns load the ends), so ONE piece-level stiffness cannot make
  three stations yield inside one chaos band — too low and the loft wins
  everywhere, high enough and it wins only where tension already holds.
  Per-station stiffness would type the answer per site (the
  parameterisation-is-the-guess family) — not taken.
- **(2) TIMED PIN RELEASE — DEAD ON PROBE, zero build cycles spent.** The
  DR's own precondition check (verify the keyframe path headless first)
  killed it: keyframing `pin_stiffness` 5.0→0.0 lands an action on the
  object, and the solver never reads it — settled verts byte-identical to
  the constant leg (0.00 mm max delta; the pinned row should have fallen).
  Blender reads pin_stiffness at sim build, once. Same probe family as the
  effector-weights ramp — that one proved clean, this one proved dead.
- (3) stays REFUSED by precedent. (4)'s pop-back failure mode is armed for
  us AND its prescribed holder was (1), now dead.

**(5) TWO-STAGE RELEASE — BUILT AND R1-STOPPED p2r30 (stop #3), a PARTIAL
mechanism with a measured trade.** Probe-proven first (cache resets on a
base-mesh rebake; a zero-tension crumple retains its form through release —
`probe_twostage_release2`), then two cycles in `drape.bake_sheet
release_frames`: stage 1 presses with the clamp, the settle is rebaked as
REST (press = geometry, not stored energy — elastic-snap disarmed), hands
let go, short unpinned settle. Results:

- **The depth-diversity rung is SOLVED — the only mechanism ever to pass
  it.** cv 0.24 (depths 11.5/7.0/12.7 mm) at 25 release frames, cv 0.28
  (10.5/5.6/11.5) at 12 — uniform clamp presses relax DIFFERENTLY under the
  same local-tension variation that defeated spring pinning. In band both
  cycles; clamp gave 0.03, spring 0.73/0.85.
- **The line-periodicity rung is UNSOLVED and invariant to release length:**
  autocorr 0.743 @ 25 frames, 0.765 @ 12 (rms healthy, 35 mm). The
  time-growth hypothesis is refuted — the mode is immediate. Read with the
  clamp stops, the two halves TRADE: pins hold the line aperiodic but
  uniform the dips; release diversifies the dips and frees the line to
  resonate. The resonator is the REGULAR GRID itself — §2's diagnosis
  verbatim, now measured on the crease.

NEXT ENTRY (staged from §2's own untouched levers — no new DR owed):
symmetry-breaking SPACING at the crease stations (§2 lever 2, in-plane and
flat — enter-smooth law untouched) and/or crease-strip MASS (§2 lever 1),
run UNDER the two-stage release so the solved cv half is kept. Site remains
OPEN after three stops; the instrument is unchanged and has passed its
negative controls at every stop.

## 6. Empirical chaos bands — what a believability test may cut against

Real re-draped fabric varies **±15% drape coefficient**,
**±25% fold/node dimensions**, **±3 fold count** between identical trials. A frame whose repeated
features vary LESS than this band reads as machine-made; a symmetry test can be
written against it — same family as the aperiodicity test that closed the
sine-hem's measurement side.

## 7. ช่องว่าง / Gaps — do not fill from model knowledge

- The corpus has **no physical constants for fold crease radius or stack-edge
  bulge** (stated explicitly in the 08-13 turn) — the folded-stack GEOMETRY
  question stays partly open; the dent mechanism (§3) does not depend on it.
- All numeric bands are model-cited REFERENCE values; `[n]` markers in the raw
  turns could not be resolved to source titles from the CLI (same caveat class
  as DRW-4). Original-source verification still owed; until then no band above
  is a threshold of record — bands parameterise TESTS, tests are judged by
  LOOK + critics.
- §2-§6 are UNTESTED against our solver as of promotion; §1 is the only tested
  section. Consumption state must be updated here when a round consumes a row.
- Nothing on knits, sheers, leather; settling drape only, no motion.


## 8. ขนและขนผ้า / FUZZ AND PILE — the mechanism this file has never carried

> PROVENANCE: promoted 2026-08-28 from
> `knowledge/_inbox/video-study/2026-08-28-surface-realism-tiling-and-fabric--VgtSL5ZpYc.md` and
> `knowledge/_inbox/video-study/2026-08-28-trim-margins-lighting-physics-and-rug-pile-KQZKc8PLV2A.md`.
> Source video ids: `3SiZCxaNM28` (why a fabric material reads fake) · `qXKERWIATjw` (building a
> rug in Blender). Tier REFERENCE — craft technique demonstrated on camera.
> §1-§7 above are cloth STATE mechanisms (what a surface does). This section is about what the
> surface is MADE of, which none of them addresses.

### 8.1 THE LAW THAT SITS ABOVE EVERY MECHANISM IN THIS FILE
> *"**your model needs to represent fabric in its topology.** If we just toss a fabric material
> on a sphere, we know that's a fabric material — but if we add some cloth wrinkles, or maybe
> some indents, you can see how it begins to read much more realistically as fabric… **unless
> you're going for an abstract look, you're going to want that object's topology and shape to
> match the material that it is holding.**"*

**A material cannot rescue a shape that does not belong to it.** This is R8's build-or-acquire
test stated from the shader side, and it is why every mechanism in §1-§5 is a GEOMETRY
mechanism rather than a texture one.

### 8.2 FUZZ IS NAMED AS THE SINGLE BIGGEST FABRIC LEVER
> *"tip number one and **the biggest tip in my opinion is add fuzz**."*

Method, as demonstrated: a **particle system** with a **vertex group controlling density** so
fuzz appears only where wanted · **simple children** · **kink set to curl or spiral** ·
**length turned way down** · count raised · and *"then add a **hair node** that you can use to
make it so the **light passes through the fuzz**."* The newer curve-based hair system is the
higher-control alternative.

For a bouclé in particular the fuzz is not a refinement — it is the defining feature of the
material, and a bouclé rendered as a woven-and-sheened plane is missing the thing that makes it
a bouclé.

### 8.3 A RUG IS THE SAME MECHANISM AT A DIFFERENT LENGTH
A rug is built as a hair field on a backing, guide-driven:
- **guide hairs** placed with an Add brush, **count ~50** over the surface, then a **comb**
  brush aims them — *"this is basically **telling all the other hairs what it should be
  doing**… each one has an area in which it affects the fur around it."*
- **length ~0.02 m = 20 mm** — explicitly *"not going to be fur, that's too long."*
- **frizz** and **noise** modifiers stacked on top; **preserve length** enabled so combing does
  not stretch the strands; viewport density reduced for working.

> **Consequence for two separate filed defects at once.** A pile has real thickness, so its cut
> edge **rolls** instead of stepping — and it catches light **per strand** rather than as a
> plane. A rug modelled as a surface with a material can produce neither, no matter how the
> shader is tuned. The same mechanism answers the bouclé in §8.2, so this is one technique, not
> two.
> Edge treatments a real rug carries are in **§9 below** (serged deep pile whose fibres hide the
> cut, or a flat weave with a ~50 mm fabric binding read as a deliberate stripe) — one home for
> the edge rule, not a pointer at the inbox unit it came from.

### 8.4 THE THREE SMALLER FABRIC LEVERS
- **Colour is not a flat wash**: *"when you zoom in on fabric you'll see that there are a lot of
  little **micro segments of colours**, and oftentimes they're interweaving and blending
  different colours to create a richer colour."* The same law as per-instance variation, at
  thread scale.
- **Stitches** — painted, brush-driven, or from a geometry-nodes asset.
- **Sheen**, used deliberately beyond its physical purpose: *"by turning the sheen up **just a
  little bit on ALL of my fabric materials**, it will help catch the light and give a more
  natural falloff… **it's not technically physically accurate**, however… it reads better as
  fabric in the final render."*

Honest scorekeeping at promotion time: of that source's five levers, **sheen is the only one a
BSDF preset already meets**; fuzz, thread-scale colour, stitching and the topology law are all
unbuilt.

### 8.5 WRINKLES COME FROM BRUSHES, NOT ONLY FROM SIMULATION
Tools named for putting fold structure into a shape that needs it: **scrape and indent sculpt
brushes** around seams, and *"the amazing **cloth sim brush** for adding wrinkles"*, plus bought
wrinkle asset packs. This is R8b's law — do not hand-write what the software already generates
— pointed at the specific case this file exists for.

## 9. ขอบพรม / THE RUG EDGE — two legitimate edges, and a bead is not a chamfer

> PROVENANCE: promoted 2026-08-28 from
> `knowledge/_inbox/video-study/2026-08-28-rug-and-bedcover-numbers-1kItQdeo9oc.md` §2.
> Source video ids: `axFPC-8MS_0` (NCCarpetBinding, *"Handmade rug minimal edge serge vs. micro
> serge and standard"*, 55 s — a fabricator showing ONE rug edged three ways) and `1kItQdeo9oc`
> (Lisa Holt Design, rug sizing) for the flat-weave alternative.
> Tier REFERENCE — trade practice demonstrated on camera, not a spec sheet.
> §8.3 built the PILE. This section is what the pile has to END in; it is the other half of the
> same defect, and neither half works alone.

### 9.1 THE VARIABLE THE FABRICATOR NAMES IS DEPTH AND COVERAGE, NOT PROFILE

Three grades of the same operation, in his own words — the whole 55 seconds is one variable:

- `[00:00]` *"here is your **standard serge**, as far as depth into the carpet, how far it
  stitches in"*
- *"here is the **micro serge**… you just get a different stitch tongue and you can set the
  **depth a little shorter**"*
- `[00:23]` *"then there is the **minimal edge serge**, or the hand-serge machine… it is an
  enormous difference as far as **coverage being at an absolute bare minimum**."*

So a serged edge is a **stitched bead that WRAPS the cut edge**, and the three products differ
only in how far the stitching penetrates and how much of the edge it covers. `frame_0013` shows
it plainly: the pile runs to a cut edge, the bead wraps that edge, and the rug's own thickness
reads as a **rolled shoulder** instead of a 90° step.

**What this source does NOT give is a number.** Not one dimension is spoken in the clip — no bead
radius, no serge depth in mm, no thread gauge. It establishes the ORDER (standard > micro >
minimal) and the MECHANISM (a bead wrapping a thickness); it cannot be converted into a value.
Typing one anyway would be R10's fabricated reading: he said "depth", he never said how much.

### 9.2 TWO LEGITIMATE EDGES ARE NAMED, AND OUR RUG HAS NEITHER

`1kItQdeo9oc` `[12:52]`: *"you can either do it **serged**, if it's a deep pile, so that you don't
see the edge and you just have this lovely **deep pile flowing over the edges**. Or if it's sort
of a flat weave like a sisal, then you can add a **binding** to the edge, which is a couple of
inches wide, and it gives you a nice **accent strip** around the edge."*

| Edge | What carries it | Geometry it implies at mm scale |
|---|---|---|
| **Serged deep pile** | the pile itself | fibres flow over the cut edge and HIDE it; the visible thickness IS the pile (≈20 mm on §8.3's build) and the terminating surface is strands, not a face. The bead is a thin rim following the backing's cut edge. |
| **Bound flat weave** | a separate fabric strip | binding *"a couple of inches"* ≈ **50 mm** (2 in = 50.8 mm) folded over the edge onto the underside — a SECOND material with its own colour, read as a deliberate stripe, not a bevel of the field. |

Both are built things. Neither is a chamfer, a bevel or a rounded corner on the field mesh.

### 9.3 WHY THIS LANDS ON A FILED DEFECT

The P2 exit clause's `rug_edge` crop asks whether the edge ROLLS or STEPS, and the measured answer
has been a step. §8.3 supplies what rolls — a guide-driven hair field whose real thickness makes a
cut edge roll. **This section supplies what it rolls INTO, and the finding is that our rug has
neither legitimate edge**: it is a surface carrying a material, so there is nothing for a bead to
wrap and no strands to flow over. No shader tuning reaches either state, and tuning the step down
is not a third option — it is the absence of both.

Two routes, and no third is named by either source — the pair is what was SAID, not a proof
that nothing else exists (fringe, hand-hem and sealed edges are simply outside what was asked):

1. **Serged deep pile** — build the pile (§8.3) and let the strands overhang the backing outline;
   the edge then becomes an emergent property of the hair field rather than a modelled profile.
   The bead is a thin wrapped rim on the backing's cut edge. Its depth and coverage are a LOOK
   call — this source names three grades but measures none of them.
2. **Bound flat weave** — no hair field at all; a woven-flat field plus a ~50 mm binding as a
   separate mesh strip with its own material, wrapping the rug's thickness onto the underside. It
   is correct only when it reads as a stripe, because that is what the source says it is for.

### 9.4 WHAT DOES NOT TRANSFER — said plainly

- The source is a **carpet-binding fabricator's 55-second side-by-side clip** for handmade area
  rugs, not a room, not a residential brief. The vendor's own market is not recorded in the unit. Whether "micro serge" or a hand-serge
  machine is obtainable from a Bangkok fabricator is UNKNOWN and was never asked. For a render
  that does not matter; for a spec sheet handed to a client it does, and the three names are the
  fabricator's own trade vocabulary and no Thai supplier is bound to them.
- **The clip recommends nothing.** It is a side-by-side comparison with no room, no style and no
  context, so it cannot tell us which grade a bedroom rug should carry. Reading a preference into
  it would be inflating one source into a rule.
- The `[12:52]` binding width is a designer's spoken *"couple of inches"*. **50 mm is the
  conversion of an approximation** and must never harden into a threshold or a gate value.
- §8.3's ≈20 mm pile comes from a **different video and a different demonstration**
  (`qXKERWIATjw`). Pairing that length with this edge is OUR pairing; neither source states it.
- Nothing here touches rug PLAN size, pad thickness or floor offset. Those numbers live in the
  same inbox unit's §1 and are a separate debt.
