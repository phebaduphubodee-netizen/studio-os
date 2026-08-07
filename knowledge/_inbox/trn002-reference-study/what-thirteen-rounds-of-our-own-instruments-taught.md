# THE INSTRUMENT WAS THE DEFECT — thirteen rounds of a reproduction lane, banked at once

> **FACT-CHECK RECORD — read this before citing anything below.** This file was
> drafted from the gate artifacts and the instrument sources, and its automated
> adversarial fact-check rung **DIED MID-RUN** (API stall). It was not skipped
> quietly: the numbers below were then re-opened by hand, one citation at a
> time, against the files they name. **VERIFIED DIRECTLY:** §1 the aim_euler
> docstring including the 44.4°/0.0 bpy comparison, the cove's 3.4°/6.8°, and
> `BLIND` at `rot (90,0,90) -> (-1,0,0)` 15 mm from the wall; §1 the key's
> `(58,0,-14)` landing at `(-2371,-4973)` against the bench at
> `(-2738,-5182)` with 18,192 of 24,704 clipped pixels; §1 the clipping series
> 2.804 / 0.731 / 0.093 % against 0.034 % and `left_wall` 5,585 -> 5,535 -> 0;
> §2 the aperture bracket at a pinned 34.8 W key — 22 W 0.3664 / 45 W 0.2515 /
> 80 W 0.2570, scaled 0.8272 to 37.2 W + 28.8 W; §3 the fold at ~75 mm =
> 15.6 px at 4.66–4.95 mm/px against a 42 mm cell whose Nyquist is 84 mm, and
> the 12.8x -> 8.4x -> 3.1x series; §4 the contact bound — target -y 0.139 vs
> -x 0.701, r24 at 1.095, the albedo x0.70 leg WORSE at 1.226, and rho = 0.87
> giving 0.88 at 90 % occlusion; §10 the 1.5 mm ease at 0.22–0.47 px
> (bed 0.35 / desk 0.29 / console 0.47); §7 the r27 slot removal scoring 0.6 %
> WORSE on pinned SHAPE. **NOT independently re-checked:** §5, §9, §11, §13,
> §15 — treat those five as drafted-but-unaudited and re-open the citation
> before you build on them. §14 is not a citation at all: it was executed on
> 2026-08-07 and the numbers in it are that run's output.

- Source: TRN-002 reproduction lane, **rounds 15–27** (gates #6–#15,
  2026-08-05 → 2026-08-07). Round records in `qa/reproduction-curriculum.md`;
  gate artifacts `training/TRN-002/gate-06-r15.md … gate-15-r27.md`;
  instruments in `pipeline/scripts/trn002_*.py`.
- Tier: REFERENCE. Distilled from OUR OWN build and OUR OWN instruments — not
  one number here was read off a document.
- **n = 13 rounds, one lane, one reference image.** Instance counts are given
  per entry; where an entry is n = 1 it says so. Everything below is a
  hypothesis with a number attached and an explicit kill condition.
- **Why this file exists.** `qa/reproduction-curriculum.md:37-46` made
  distillation a GATE CONDITION on 2026-08-05: *"A round whose measurements
  produced transferable knowledge does not close until that knowledge is
  written to `knowledge/_inbox/`."* Thirteen rounds then closed and banked
  nothing. That is the repo's own recorded failure shape —
  DISTILLED-BUT-NEVER-WIRED — applied for the second time to the distillation
  step itself. The rule was not wrong; it had no counter, and a rule with no
  counter is a rule nobody can be caught skipping (see §14, which is the same
  shape in code).
- The two files already in this directory carry what the REFERENCE taught.
  This one carries what OUR OWN WORK taught, which is a different and less
  flattering subject: **eleven of the fifteen entries below are defects in the
  measuring, not in the making.**

---

## 1. An emitter's aim is TYPED, so nobody ever asks where the beam LANDS

R9 says a position that can be derived from a contact must never be typed,
because *a coordinate encodes a RESULT, never a RELATIONSHIP*. **Lights were
never in scope**, and `rot_deg` is three typed numbers with a comment above them
saying what the fixture is for. Both can be true at once and nothing fails.

**Three fixtures found aimed 180° from their own documentation, one at a time,
across two lanes:**

| fixture | what the comment said | what the numbers did |
|---|---|---|
| cove (`trn001_light.py:110-133`) | aimed at the wall | 180° out in yaw — and it HID: tilted 3.4° off vertical it landed 6.8° from its aim and still read as "down" |
| fill (same formula) | *"standing off frame on the camera side, aimed INTO the room"* | faced 180° away; reached the frame only as bounce — **so two recorded refutations (`_fill_refuted`, `_fill_retest`) measured a bounce card, not the source they name** |
| window aperture (`trn002_light.py:164-172`) | *"lights its own slats"* | `rot (90,0,90)` resolves to `(−1,0,0)` — firing into a wall **15 mm away**, every round of the lane; the slats are on the other side of it and did not exist until r25 |

The maths: `atan2(dy,dx)+π/2` names the direction perpendicular to the run,
turned the wrong way; the correct yaw is `atan2(−dx,dy)`, and the two differ by
exactly π. Verified against bpy rather than against the reasoning: **44.4° of
error for the shipped formula, 0.0 for the replacement.**

The evidence for the third one had been in the frame the whole time:
`left_wall` held **5,585 clipped pixels**; turned round it holds **0**, and the
frame's total clipping fell **0.731% → 0.093%** against the reference's 0.034%
(`gate-13-r25.md:17-18, 29-35`; commit `0bafb10`).

**And a fourth of a different shape.** The TRN-002 key carried `rot (58,0,−14)`
since the first build. Its beam lands on the floor at `(−2371,−4973)`; the
bench sits at `(−2738,−5182)` — **the key was aimed at the object that was
blowing out**, and that one mass held **18,192 of 24,704 clipped pixels**. The
round before had bracketed spread and power against the wall gradient and never
touched aim, because the defect it was chasing was a spread question:
***"a knob nobody brackets is a decision nobody made"***
(`trn002_light.py:65-76`; commit `fcc982c`).

→ **Transferable question:** what world POINT is this fixture aimed at, does a
ray from its origin along its emission axis hit that point, and **which object
is standing there**? Declare `aim_at`; derive the rotation; never type a euler
triple. This is R9 for emitters and it has four instances.
*Killed by:* a lane where emitters carry declared aim points with a build-time
direction assertion and a mis-aimed light still ships.

## 2. A setting made against a broken mechanism does not survive fixing it

Every calibrated number is calibrated against the system **as it behaved at that
moment, bugs included**. After the repair the number is not stale — it is a
setting for a different machine — and because it is still a legal value nothing
flags it. The repair then gets blamed for its own side effects.

The window aperture's **38 W** was chosen while it fired into a wall 15 mm away,
so its light reached the room almost only as bounce off that one patch. r25
corrected the aim and **the frame got worse**: p50 0.3742 → 0.3323, SHAPE
0.2761 → 0.3165. The ladder said exactly why — **every key-lit object rose
8–14%, everything on wall and ceiling fell 5–10%** — the aperture had been
feeding that side through the wall it was wrongly aimed at, nothing replaced it,
and the builder had raised the key 4.9% on top.

Re-derived with the key **pinned at 34.8 W** so the aperture was the only thing
moving (`gate-14-r26.md:28-44`; commit `2b15c59`):

| aperture | LEVEL | SHAPE |
|---|---|---|
| 22 W (r25's) | 0.860 | 0.3664 |
| **45 W** | 0.839 | **0.2515** |
| 80 W | 0.825 | 0.2570 (6.8% clipped) |

then both scaled ×0.8272 to put the full frame's p50 on the reference —
**SHAPE is exposure-independent, so the bracket's verdict survives the
scaling.** p99 landed at **0.7232 against 0.7153**, having been pinned at
1.0000 for four rounds.

→ **Transferable question:** when a mechanism is repaired, **list every setting
that was tuned against the broken version BEFORE looking at the new frame**,
and re-derive each with everything else held. Otherwise the repair is judged on
numbers that no longer describe it — and may be reverted for being right.
*Killed by:* a repair after which the old calibration re-measures within noise
of the re-derived one.

## 3. The stuck variable was never the knob — it was NYQUIST

A feature smaller than twice the discretisation of whatever must carry it
**cannot exist at any setting of any knob**. Tuning against that limit produces
a clean, repeatable, entirely false story about the knob being exhausted.

- reference fold period **15.6 px** at **4.66–4.95 mm/px** through the solved
  camera → **~75 mm folds**
- our cloth cell **42 mm** → **Nyquist wavelength 84 mm**
- → the mesh could not represent that fold **at all**: not at any slack, not
  for any number of frames, not with any fabric

**Both mechanisms refuted at r20 failed for that one reason**
(`gate-08-r20-STOP.md:19-30`; commit `bc65b85`): slack 2% → 6% bought **1.4× of
the ~13× needed** and is halved by `search_bake` on every billow *by its own
design*; a noise bump at 7.0/2.0/d0.12 hit rms **0.00788 against 0.00983** and
matched the 15.6 px period **exactly** — and rendered as **tree bark**, while
backed off to 3.2/0.7 it reads as cloth and measures 14× short. Nothing sits
between them, structurally: **a noise field is isotropic and real folds run in
FAMILIES along the drape's tension lines.**

The fix was representation, not tuning: cell 42 → **22 mm** (3.4 cells per
measured fold) plus a duvet fabric preset at **compression 1.0 against linen's
15** — the physical difference between a bedsheet and a quilted duvet — taking
the gap **9.7× → 1.9×**. Across rounds: **12.8× → 8.4× → 3.1×**, period
3.9 → 10.4 px against 15.6 (`gate-09-r21.md:6-24`; commit `4087822`).

**And the R1 STOP filed at r20 named the wrong cause.** Its own words: *"a
stop-loss is only worth what its diagnosis is worth, and this one was worth less
than it claimed."*

→ **Transferable question:** measure the target feature in world units and
compare it to the resolution of its carrier — mesh cell, texel, pixel, sample.
Under 2× → **no setting exists**; the round is a representation change. And
before any stop-loss is filed, ask what representational limit could produce the
same symptom.
*Killed by:* a feature comfortably above its carrier's Nyquist limit that is
still structurally unreachable by the knob.

## 4. Compute the mechanism's PHYSICAL BOUND before spending brackets on it

Seven probes, no build, four levers — bounces 8→32, world 0.018→0.15, a
room-wide source panel, every albedo ×0.70 — and not one moved the rug's
contact profile off **1.09–1.24** while the reference sits at **0.139**. The
albedo leg made it *worse*, 1.226 (`gate-12-r24-STOP.md:42-52`).

The bound is one line: **an occluder returns ρ× the ambient it blocks.** At
ρ = 0.87 the plinth returns nearly everything it blocks and — its face being lit
harder than the rug — returns more. **Even a crevice blocking 90% lands at
0.88.** You cannot light your way to 0.139. That refutes both critics'
prescription ("add a directional key so it casts contact shadow") in one line,
and separately the reference's own deepest cast shadow anywhere in frame is
**−8%**.

The asymmetry finished the diagnosis: **−y 0.139 against −x 0.701**, and
occlusion is symmetric. The missing thing is GEOMETRY (hypothesised: a recessed
toe under an overhanging base) — R8 BUILD class, not a light setting
(`gate-12-r24-STOP.md:59-68`; commit `038a5dc`).

→ **Transferable question:** what is the best value this mechanism could produce
**at its physical limit** — full occlusion, zero power, unit albedo? If the
limit does not reach the target, the mechanism is refuted before the first probe
renders, and the work belongs to a different class.
*Killed by:* a bound that says unreachable while a tuning pass reaches the
target anyway.

## 5. Two epistemic kills that cost one round each and are reusable verbatim

**(a) Extrapolate the knob to its limit.** The blind was built, measured and
**withdrawn**: pitch 29.4 mm from 89 peaks in the reference's own column, extent
confirmed twice independently (1 mm at the near edge, 32 mm at the top) — and it
still failed, because every gap looked through to an emitter 35 mm behind it, so
a gap was the *brightest* thing in the band instead of the darkest (0.445
against 0.250). Both knobs were bracketed: **8/16/22 W → 1.44/1.89/2.17 against
a target of 0.80, and extrapolating to ZERO aperture power still lands at
0.89.** A knob whose limit misses the target is not the lever
(`gate-13-r25.md:47-60`; commit `0bafb10`). Same family as the recorded law
*"a parameter that cannot reach the low side cannot be bisected"*.

**(b) A constraint that does not vary with the unknown cannot determine it.**
Chasing the TV's standoff, 16:9 looked like the missing equation. **Aspect is
invariant along the ray — 0.560 at every standoff** — so it can confirm a
silhouette and never a distance. The standoff was declared unmeasurable instead,
and the declaration proven free: 25/40/80 mm give a 56/53/43-inch panel with an
**identical silhouette** (`gate-13-r25.md:41-45`).

→ **Transferable question:** does this constraint's value CHANGE as the unknown
changes? If not it is a consistency check wearing a solver's clothes. And: what
does this knob read at both of its physical limits?
*Killed by:* a solve where an invariant constraint genuinely pins an unknown
through some coupling the invariance argument missed.

## 6. A metric aggregated over a set that the change itself edits — flattering-scorer #10

Free-membership SHAPE read **0.2587 → 0.2000**, *"best this lane has measured"*,
and was nearly shipped as the headline. **Pinned to the 22 rows both frames
share it is 0.1989 → 0.2000 — 0.6% WORSE** — and LEVEL is 0.849 either side.
The entire gain was **one row leaving the pool**, because the round's work was
to REMOVE a surface from the frame (`gate-15-r27.md:42-53`; commit `64cd167`).

Second instance, three gates earlier: a bracket scored on **a seven-object
subset the builder chose himself** returned a beautiful 0.995 — and the full
frame then showed floor, ceiling and wardrobe all falling to 0.72 **together**.
One defect (the divisor came up), not twenty-one. *"I moved the error, I did not
remove it."* That is what forced the split into **LEVEL** (pixel-weighted
geometric mean of the room against the wall) and **SHAPE** (the spread about it,
**invariant to which object is the reference**) (`gate-11-r24.md:28-34`).

n = 2 in thirteen rounds; the gate calls it the tenth of this repo.

→ **Transferable question:** does this metric's POPULATION differ between the
two frames being compared? Pin membership to the intersection before quoting any
delta, and prefer a per-pixel or per-area metric, which has no membership to
edit.
*Killed by:* pinned and free numbers agreeing within noise across a change that
adds or removes members.

## 7. The ladder has NO TERM for "this surface should not be in the frame"

An instrument answers the question it was built to ask. A per-surface brightness
ladder can say *too bright* and *too dark* and nothing else.

The round closed a **23 px floor-to-ceiling slot** — a wardrobe built **259 mm
short**, its far end TYPED at y = −2550 where the reference fits the cabinet's
own silhouette at **u = 730.21, sd 0.05/0.06 over two independent v-bands,
250/250 rows kept → y = −2290.8**. That slot was the ONLY band where the right
wall was ever visible (u 730.64..754.33). **The ladder scored the fix 0.6%
worse.** What could score it has no membership — per-pixel: gross disagreement
**17.74% → 17.14%**, too-dark **6.56% → 5.93%** (≈5,600 px, the size of the
slot), median |log(ours/target)| 0.2765 → 0.2720 (`gate-15-r27.md:55-66`).

And the same gate shows the second blind spot: the cost of the correct fix left
`back_wall` holding **4.4% of its own pixels at 0.14×** while the other
**163,871 px of the same paint read 1.23×** — **8.8× apart on one material**,
invisible to that surface's median (it is the reference; err = 1.00 by
definition).

→ **Transferable question:** which defect classes can this instrument not
express *at all* — presence/absence, identity, legibility, within-surface
bimodality? Write them into the instrument's own docstring, and pair every
per-object aggregate with one per-pixel metric.
*Killed by:* a presence/absence fix registering correctly on a per-object
primary metric without a per-pixel companion.

## 8. A broken instrument stays alive by being run on the one input that hides the break

The contact-shadow tool split faces by **whichever axis dominated**, which lumps
the floor on BOTH sides of an object into one bucket. A gradient symmetric about
the object then **cancels to exactly 1.000 on both faces and reads as "no
effect"**. It survived because this scene shows only two sides of the platform —
*a broken instrument staying alive by being run on the one input that hides the
break*. **A synthetic ramp caught it in one call.** It also eroded 2 px off the
mask, deleting the pixels nearest the object — **the measurement's own
subject** — so erosion became a declared parameter instead of a silent bias.

**Gate #11's headline contact numbers were WITHDRAWN** (`gate-12-r24-STOP.md:
12-20`; commit `038a5dc`). The corrected table shows r23 and r24 identical, so
the previous round never caused the regression it was charged with. The repaired
tool validates itself: a directional gradient MUST push two opposing faces
opposite ways while occlusion must darken both — the direct-light leg returns
**−y 1.007 / −x 0.822**, exactly as it must.

Same round, same class: **a probe that was not the test it claimed.**
`diffuse_bounces=1` was said to remove inter-reflection between white surfaces —
but **one diffuse bounce IS the bright-platform-face-onto-the-rug path.** It
removed the global fill and kept the exact term under suspicion.

→ **Transferable question:** what synthetic input has a KNOWN answer for this
instrument, and what invariant must its output obey (a sign flip, a
cancellation, a symmetry)? Run it before the first real reading. When a probe is
claimed to remove a term, write down the path that term travels and check the
probe cuts it.
*Killed by:* an instrument that passes a designed-to-fail fixture and still
fabricates on the real scene.

## 9. A patch of pixels borrowed from another image is not a measurement — n = 3 in one session

It never errors. It returns a confident ratio between two different objects.

| # | what was borrowed | the false number | the true one |
|---|---|---|---|
| 1 | strip u430–700, quoted all evening — **overlaps the reference's two throws** | "6.7× too smooth" (their woven herringbone vs our bare white duvet) | white-on-white **12.8×**, *worse* than reported |
| 2 | joint count read off an **upscaled quick render** (upscaling merges adjacent joints) | a missing-joint defect | at full res: 5.5 vs 10.5 dips/100 px, but depth already **deeper** (5.1% vs 3.9%) and pitch matching (55 vs 53 px) → **no defect; the extra dips are within-plank figure** |
| 3 | the reference's shadow-patch coordinates sampled on our frame | **1.163 — brighter UNDER the bed than beside it** | the "open rug" station in our frame is the **clipped-white bench** |

(commits `bc65b85`, `000f853`, `85feb66`; `gate-10-r23.md:33-37`)

The form that works: bin by **world distance** on a named surface, and normalise
**each image by its own far bin** (`gate-11-r24.md:43-45`).

→ **Transferable question:** is every sample taken by world position on a
surface both frames agree exists there, and is each image normalised by its own
reference region? A borrowed pixel box is valid only where the geometries
already match — and if they matched you would not need the measurement.
*Killed by:* a lane whose frames are geometrically identical by construction,
where borrowed and world-binned patches return the same ratios.

## 10. Physically honest and invisible at the same time: 1.5 mm ease = 0.22–0.47 px

Every mass got a 1.5 mm chamfer, and the critic **still filed "edges are razor
sharp" on the same frame** — correctly. Through the solved camera that ease
projects to **0.22–0.47 px on exactly the objects named** (bed 0.35 / desk 0.29 /
console 0.47). **5 mm would be ~1 px** and was already refused by R9b's contact
tolerance (a pillow floating 1.7 mm).

**The softness the reference has is not carpenter's chamfer at all — it is
10–20 mm upholstered radii on fabric-wrapped objects.** The item folds into the
soft-goods lane; it is not a bevel knob (`gate-06-r15.md:75-79`). Same class as
trn001's amplitude-bisect law, except the ceiling here is a contact guard rather
than "go loud, then take 70%".

→ **Transferable question:** what does this dimension measure **in pixels**
through the solved camera? Under ~1 px it will not appear at any honest value —
so either the read comes from a different object class, or it is a declared
non-deliverable. Either way the critic item is **re-routed, not re-tuned**.
*Killed by:* a frame where a sub-pixel chamfer is demonstrably visible through
anti-aliasing and specular breakup.

## 11. A fix can RESTORE a defect that was already declared solved

Three wood defects in one round, and **two of them were bugs in the fix for the
third** (commit `000f853`):

1. **Half the parquet planks had their grain running across.** The per-plank UV
   frame took `q0→q1` as the plank's length; on a herringbone the two arms wind
   in opposite senses, so for one arm that edge is the **132 mm WIDTH**. Proven
   before touching anything: plank 0 samples U 0..0.518 / V 0..0.109 while plank
   1 samples U 0..0.109 / V 0..0.518.
2. **All 458 planks then sampled the same rectangle of the map** — one board's
   figure printed 458 times. This is trn001's recorded *"printed laminate"*
   defect (it had measured its own floor at 1.9% plank-to-plank variation
   against a reference's 30.4%) and **it was reintroduced here by the per-plank
   UV frame added to fix defect 1.** *Nothing caught it because the thing it
   broke had already been declared solved.* After a deterministic per-plank
   offset+flip derived from world position: spread **48.5% against the
   reference's 41.9%**.
3. **The veneer wore a FLOOR map at FLOOR scale.** `wood_floor` carries board
   JOINTS; cabinetwork does not. At 1.10 m it laid a joint every ~120 mm across
   the etagere and repeated its whole tile 2.6× up the column. At 3.2 m one of
   the map's boards spans a whole panel — one leaf per panel, which is what the
   reference shows.

→ **Transferable question:** what did this fix touch that another finding had
already claimed? Re-run the metric of every previously-closed defect that shares
the changed code path — **a closed defect has no watcher.** And: does this
material map carry FEATURES the substrate it is being applied to cannot
physically have?
*Killed by:* a repo where closed defects carry standing regression metrics and a
fix still silently restores one.

## 12. Same-material RATIOS are the only readings that survive an unknown tonemap

The reference is an **8-bit display-referred JPEG**; absolute cd/m² is
unrecoverable and none is claimed. The rig is therefore **aimed at ratios, not
at watts** — every target in `pipeline/scripts/trn002_light.py:37-47` is a
same-material ratio:

    bed-base −Y face / −X face            1.38
    white bedding, head / foot            1.57
    ceiling, brightest / darkest corner   1.92
    rug, lit / shaded                     1.23
    back wall                             FLAT in x, −7.7 %/m upward
    etagere: strip / lit shelf / unlit     7.6 / 2.9 / 1

The discipline has teeth in both directions. It is why **165 W → 42 → 34.8 W is
recorded as an EXPOSURE match and not as a physical wattage** (lines 136-146),
and it is why the frame's p99/p1 of 182:1 was caught out as **palette, not
dynamic range** — both tails are material (a black screen and a void at one end,
clipped lens cores at the other), while the illumination range on any ONE
material is 1.2–1.9:1.

→ **Transferable question:** what is the reference's colour pipeline, and which
of my numbers survive not knowing it? Build the rig against within-frame,
same-material ratios; treat every absolute level as an exposure match that any
later exposure change is free to move.
*Killed by:* a reference delivered scene-referred with a known tonemap, where
absolute values are recoverable and ratios throw away information.

## 13. A metric measured on one rung does not transfer to another without its own calibration

R5 says quick kills bad work and only full fidelity closes a gate. The hazard it
does not name: **the two rungs do not agree numerically.** Measured here,
cross-checked two ways — r23 full 42 W → p50 0.3237 against a quick leg at
48.5 W → 0.3376, and a second quick leg at 41.5 W → 0.4016 — **full/quick =
1.107**, i.e. quick reads p50 ~11% LOW at identical power.

Setting the key's power from a quick bracket without that factor would have
landed the full frame **11% hot, which is most of the entire clipping budget**
(`trn002_light.py:147-154`).

→ **Transferable question:** what is the transfer factor between the cheap rung
and the expensive one **for this specific metric**, and has it been measured on
this scene rather than assumed? Brackets decide on the cheap rung; absolute
settings must be re-anchored on the rung that ships. Ratio metrics (SHAPE, any
same-material ratio) survive the crossing; scalar levels do not.
*Killed by:* a pipeline where quick and full agree within noise on level
metrics — in which case the calibration is ceremony and the risk is elsewhere.

## 14. A mute check is indistinguishable from compliance — and a gate that fails on correct work is the one that gets muted

`check()` runs `audit_bundle` only `if bundle_dir:`, and the single call site
passed none. **Every render therefore printed "RULE GATE: N masses, all
justified" while the triage rule never executed at all.** Nothing distinguished
*checked and clean* from *never checked*
(`training/TRN-002/triage-debt-2026-08-07.md:3-11`).

The paired failure is the opposite one, and it is why so many guards die: wired
at ITEM level across all 21 bundles the check **cleared 18 and named 3** — but a
**file-level** version of the same check reported **eleven correctly-triaged
rounds as violations**. *A gate that fails on correct work is the one that gets
muted.*

**The cost is on the record.** r26's C2#14 read the wardrobe's panel bays as
*"arbitrarily unequal, joints not aligned with the bulkhead, the headboard-height
ledge, or each other. Joinery is set out."* Nobody triaged it. **One round later
the owner looked at the same frame and asked why there are two doors at the head
of the bed** — and that round found the wardrobe built 259 mm short (§7). **The
blind critic named the defect a round before the eye had to, and the item was
dropped because nothing counted the items.** The loss was in the accounting, not
in the rung.

→ **Transferable question:** can this guard tell "passed" from "never ran"? Give
it a negative control that must FAIL, and make it emit **the count of items it
examined**. Set its granularity so it never flags correct work.
*Killed by:* a guard whose success banner is emitted only on a path that
provably executed the rule, making the count redundant.

## 15. The critic's WHAT is data; its WHY and its prescription are priors — count them

R10b already says this. Thirteen rounds put numbers on it, and the numbers are
worth carrying because they say **how often** and **in which direction**:

| item, filed repeatedly by independent critics | rounds refuted | the measurement |
|---|---|---|
| "converging verticals / perspective is distorted" | **5** | camera solved from the reference itself, 18 landmarks, mean **0.09 px** — the leaning lines are the reference's own |
| "the downlights must throw pools" | **3+** | reference floor under `dl_1` reads **0.184 and RISES to 0.220** a metre away; ceiling glow dead within 120–200 mm. **Wrong sign, not wrong value** |
| "the whites are one undifferentiated mass — add value separation" | **3** | our white family's std(log) is **0.3110 against the reference's 0.1552** — **theirs is 2× TIGHTER than ours.** The symptom is real; the cause is material and surrounding darks, not brightness |
| "wood texture is visibly tiled" | 3 | autocorrelation: ours r = **0.29** at lag 86 px, the reference **r = 0.50 at the same lag** — and that lag is the shelf pitch, not the texture |

And the reverse case, which is the more useful one: **five independent critics
could not identify the `bolster`** — an object whose provenance is M (end
ellipse u 903–949, D = 165 ± 8) and which demonstrably exists in the reference.
R10 ruled **keep, do not remove**: the object is justified; what failed is that
it does not *read* as what it is (`gate-15-r27.md:128`). **"Unidentifiable to
five critics" is a legibility measurement, not evidence the object is wrong.**

→ **Transferable question:** for each critic item — is the WHAT independently
observable, and is the WHY a generic prior this particular reference violates?
Refute with a measurement or accept; never with taste. Then check the inverse:
if several critics cannot NAME an object that is genuinely there, that is a
shading/material ticket, not a deletion.
*Killed by:* a lane where critic prescriptions, applied literally, measure
closer to the reference than the measured refutations do.

---

## Provenance and how to reuse

Thirteen rounds, one lane, one delivered reference image. Every number traces to
a scripted measurement or to a quoted commit in this repo; the gate artifacts
(`training/TRN-002/gate-06-r15.md … gate-15-r27.md`) hold the full triage tables
and the spend for each round. Nothing here came from a document and nothing came
from the builder's memory.

**This is `_inbox` tier.** Before any entry gates a deliverable it must be
distilled into `knowledge/` proper. Entries §1, §6 and §9 have n ≥ 2 instances
and are the closest to being rules; the rest are single-lane hypotheses with
kill conditions attached.

**The one that should be wired first**, because it is the only entry that
explains why the other fourteen went unbanked for thirteen rounds: §14 — a rule
with no counter is a rule nobody can be caught skipping. The distillation gate
of 2026-08-05 had no counter either.