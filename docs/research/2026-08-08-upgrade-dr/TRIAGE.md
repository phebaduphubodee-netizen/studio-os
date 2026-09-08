# Triage — 2026-08-08 DR run (R7: every item accepted with a lane, or refuted with a measurement)

**Scope, stated so it cannot be mistaken for completeness:** ten answers ×2 passes
plus three NotebookLM Deep Researches is far more material than one round can
absorb. Triaged here are the claims that **would change a build, a number, or a
rule**. Everything else stays in the answer files at REFERENCE tier, undistilled
and uncited by anything. Naming the scope is the point — the last time items were
left untriaged in this lane, a blind critic named a 259 mm wardrobe error a round
before the owner had to, and it was dropped because nothing counted the items.

---

## REFUTED — with a measurement, per R7

### T1. "Set **Transmission Roughness** for frosted glass" (q2, grounded, sourced)

**REFUTED.** Probed live in the Blender this repo actually runs:

```
BLENDER 5.1.2
SOCKETS: Base Color|Metallic|Roughness|IOR|Alpha|Normal|Weight|Diffuse Roughness|
Subsurface Weight|…|Specular IOR Level|Specular Tint|Anisotropic|…|
Transmission Weight|Coat Weight|Coat Roughness|Coat IOR|Coat Tint|Coat Normal|
Sheen Weight|Sheen Roughness|Sheen Tint|Emission Color|Emission Strength|
Thin Film Thickness|Thin Film IOR
```

There is **no `Transmission Roughness` socket.** It existed in the pre-4.0
Principled and was folded into `Roughness` in the v2 rewrite. The frosted lobe
therefore comes off `Roughness` itself, or off a separate Glass BSDF mixed in.

**The general lesson is bigger than the socket:** nearly every returned Blender
answer says "Blender 4.x", and this lane runs **5.1.2** — two majors past the
advice. *A version number is a measurement.* Any returned Blender construction
gets probed against the live socket list before it is built.

**What survives from that answer and is usable:** IOR **1.52** for soda-lime
glass (physical constant, not a UI claim); the Pilkington Optifloat Satin VLT
ladder (4 mm **84%**, 6 mm **82%**, 9.5 mm **80%**) and clear float ~**91%** at
4 mm; and the production practice of disabling refractive caustics and mixing a
Transparent BSDF on `Is Shadow Ray` to keep rough transmission affordable.

### T2. "SEIG budgets 3 correction rounds per phase; 3D IoU 0.42 vs 0.28" (q8, first pass)

**REFUTED by the paper itself** (arXiv 2606.02580, fetched directly):

| claim | the paper |
|---|---|
| 3 rounds per phase | geometry **5**, material **3**, composition **3**, lighting **2** |
| 3D IoU 0.42 vs 0.28 | no 3D IoU — PSNR/SSIM/LPIPS/DreamSim/DINO/CLIP; PSNR **13.58** vs **12.33** |
| authors "K. Ling, K. Rempe" | **Guangzhao He, Rundong Luo, Wei-Chiu Ma, Hadar Averbuch-Elor** |

Cause diagnosed and fixed at the tool: the call never searched (see README).

### T3. FOUR of the five lighting numbers our knowledge base carries are misfiled

This is the run's second headline, and it came from the rung the triage
prescribed: an ask to the **existing** 315-source lighting corpus (`79476082`,
which holds Gordon's *Interior Lighting for Designers* 5th ed. first-hand), not a
new DR. Each number is REAL and PUBLISHED — and attached to the wrong thing.

| our file says | the corpus says | what actually happened |
|---|---|---|
| accent:ambient **3:1** | accent should be **5:1**; **3:1 is Gordon's TASK-to-SURROUND contrast** limit | two different ratios collapsed into one number |
| **20:1** max within the FIELD OF VIEW | 20:1 is the **fenestration-to-adjacent-surface** limit (also luminaire-to-adjacent); the field-of-view limit is **< 40:1** | right number, wrong scope — by a factor of two |
| **108–215 lux** general bedroom ambient | that is **10–20 fc, hotel bedroom READING**; IES bedroom *ambient* is **6–15 fc ≈ 65–162 lux** | a task figure filed as an ambient figure |
| **323–538 lux** bedside reading | **30–50 fc is the KITCHEN** general standard; reading areas are **20–50 fc ≈ 215–538 lux** | a kitchen figure filed as a bedside figure |
| CRI ≥ 90 residential | DISAGREES as a general requirement | — |

**Note which channel got this right.** The grounded Gemini pass called (a), (c)
and (d) *"Agrees"* — including calling 65–100 lux and 108–215 lux "in the same
ballpark". The curated corpus, holding the actual books, disagreed with four of
five and named the page each real number belongs to. **A looser channel produced
a more agreeable answer, and agreeableness was the error.** This is the argument
for keeping both channels and for asking the corpus rather than the web whenever
the corpus owns the authority.

**Lane:** amend `residential-lighting.md` and
`lumen-method-and-fixture-placement.md` — each value keeps its number and gains
the scope it actually belongs to. This is not a "the vault was wrong" finding, it
is the single-source flag on those files doing exactly the job it was put there
to do.

**Bonus from the same ask — cove geometry, sourced at last** (Gordon, 5th ed.):
cove pocket setback **7½" min (190 mm)**, fascia lip **2" min (51 mm)**, lamp
centreline to ceiling **12" min (305 mm)** for rapid-start, and the lip height is
set by a **sight-line analysis** from the furthest viewing point — not by a rule
of thumb. Element 5's cove was derived at 10 W/m with no source; the geometry now
has one. Cove sits in Kelly's **Ambient Luminescence**. Lumens-per-metre and the
ceiling gradient length: **NOT IN SOURCES** — a real gap, now evidenced rather
than assumed.

---

## ACCEPTED — with the lane each one enters

### T4. Edge ease — and a correction I had to make to my own triage an hour later

**First version of this entry was wrong, and the way it was wrong is the lesson.**
I wrote that NotebookLM's craft DR "returned the Architectural Woodwork Standards
directly", and tabled an eased radius of 3.2 mm (1/8") for Premium & Custom grade
and 1.6 mm (1/16") for a square edge, alongside the edgeband thicknesses. Then I
pulled the AWI source's own indexed text (`notebooklm source fulltext`, URL
`awinet.org/standards/millwork-and-wood-trim/…/3-4-aesthetic-6/`) and grepped it.

**Verified, verbatim, in the AWI text:**

> *"b) Sharp edges shall be eased."*
> *"a) … edgebanded with solid wood, veneer, or veneer tape a minimum of .5 mm
> [.018"] thick"*
> *"c) Edges shall be HPDL, PVC, or ABS a minimum of .5 mm [.018"] thick and a
> maximum of 3 mm [.118"]"*
> *"d) PVC and ABS edgebanding thicker than 1 mm [.039"] shall be radiused or
> beveled on edges and corners."*

**Not in the AWI text at all:** the 3.2 mm and 1.6 mm radii, and the 3.0–5.0 mm
stone figure. Grep for `1/16`, `1/8`, `radius` returns the radius-assembly
headings and nothing else. Those numbers came from the **synthesised** report,
and the DR's answer had cited AWI *and* the synthesis in the same sentence — which
is precisely how a quarantined number gets laundered into a sourced one. It was
the citation I was most confident in.

**What actually survives, and it is smaller and truer:**

- AWI *requires* that sharp edges be eased — a requirement, not a preference, and
  our `_ease` pass satisfies it
- the visible edge feature on cabinetry runs **0.5–3 mm** by the standard's own
  edgeband limits, and our **1.5 mm** bevel sits mid-band

**Lane: the bevel bracket is WITHDRAWN as a sourced change.** There is no
retrievable value saying 1.5 mm is wrong. It may still be widened on LOOK
grounds — the R9b placement gate is the referee, and it already refused a 5 mm
pass for floating both pillows 1.7 mm — but that would be a taste decision, and
this triage does not get to dress it as a measurement.

### T5. Wall-to-floor junction: the item accepted at gate #15 with no number now has bands

C2#15 ("no skirting, shadow gap, or any wall-to-floor junction detail") was
accepted into the craft lane with the condition *"measure whether the target has
a skirting, a groove, or nothing at all"*. q7 supplies both the bands and,
better, the argument that the third option is nearly a non-option:

- timber/MDF skirting: **70–145 mm** high (145 mm the most-sold), **12–18 mm**
  projection (18 mm most common)
- shadow-gap systems: **5–22 mm**, with **10 mm** the recurring value across
  four named manufacturer systems
- **the decisive one:** a timber floor's expansion gap of **10–15 mm** has to be
  concealed by *something*. A wall meeting parquet in a single line is not a
  minimalist choice, it is an unbuilt floor.

**Lane:** measure the target's wall-floor line for a skirting band or a dark
groove, then build whichever it shows. The prior "or nothing at all" branch is
struck — with a parquet floor it is not a candidate.

### T6. The metric blindness is a published class, and the instrument is now built

q8 (grounded) and the SEIG paper together name our thirty-round failure:

- windowed similarity metrics (SSIM and family) are computed over a sliding
  window; a large missing object averages away — the windows on the wall that
  should have been a doorway report a perfect match with the wall that is there
- detection-style metrics "do not fulfil the critical requirement of detecting
  all objects in a data set" (Maier-Hein et al. 2022, via q8)
- SEIG's **initialisation verifier judges object PRESENCE only**, "scoped to its
  corresponding stage … while ignoring errors assigned to other stages", and
  selects the scaffold with "the most complete object coverage"
- SEIG's own reported failure mode: *"errors introduced in early stages may
  propagate throughout the pipeline, leading to local minima from which later
  stages cannot easily recover"*

**Lane: BUILT THIS SESSION** — `pipeline/scripts/coverage_check.py` +
`test_coverage_check.py` (15 tests). It asks the question no instrument here has
ever asked: *which object that the reference shows has no mass in our scene?*
Every manifest entry must resolve to BUILT or to a declared gap **with a
reason**, and the allowed-absence list ratchets down only. Its negative controls
are this lane's three real omissions — the opening, the blind, the chair legs —
and the first draft **failed its own blind test**: prefix matching let
`blind_light` (the area light named after the blind) satisfy the entry for the
blind. Prefix matching is now opt-in per entry.

### T7. Verifier design: what the critics are asked for changes

SEIG's verifier returns "an explicit approval checklist: a concrete, actionable
todo list of visual discrepancies", **stage-scoped**. Our C2/C3 prompt asks for
critique in free form and gets prose, which is why triage debt accumulates —
prose items have no id, and an item with no id is one nobody can count.

**Lane:** propose to the owner that `templates/cold-critic-prompt.md` require a
numbered checklist with one line per discrepancy, and that each critic be told
which PHASE it is judging and to ignore defects belonging to other phases.
Not adopted unilaterally: every R-rule in this repo carries an owner order.

### T8. Per-phase round budgets — ours is tighter, and that is worth knowing

SEIG: geometry 5, material 3, composition 3, lighting 2. Ours: R1 stop-loss of
**2 rounds per mechanism without a pass**, uniformly. **Accepted as context, not
as a change:** their budgets are per-phase for an automated agent with a
verifier in the loop; ours is per-mechanism with a human gate. The number worth
carrying across is the *shape* — geometry gets the most rounds, lighting the
fewest, because early errors propagate. Our lane spent thirty rounds inverting
that shape.

### T9. Inspection blindness: the one countermeasure we have never tried has no literature either

q9 returned honest emptiness: **NO SOURCED VALUE FOUND** for controlled evidence
that inverting, mirror-flipping, blurring or rescaling an image restores a
habituated viewer's error detection — in proofreading, art practice, radiology
or industrial inspection. Practice conventions exist (read backwards, read
aloud, change the font); measured effect sizes do not.

**Lane:** this stops being a research question and becomes a **local
experiment**, which is cheap: flip the next full frame horizontally, re-run the
builder LOOK, count items found that the unflipped LOOK did not name. n=1 per
round, free, and it is the only way this question gets an answer at all. Do not
write it into the rules until it has fired twice.

---

## Deferred with a reason (not dropped)

- **q3 palette / q4 bedding** — belong to the materials and cloth phases; the NLM
  DRs on both are still landing and the two channels must be reconciled before
  any value is promoted. The delta-E gate's missing `--brand-palette` file is the
  intended destination.
- **q6 camera** — the queue's own verdict stands: **measure first**. The 704-frame
  anchor sweep with existing tools beats any document corpus for our own
  question, and this lane solves its camera from the target anyway.
- **q10 acquire** — reads onto the R8 ACQUIRE lane, which has still never bought
  or imported a single asset. Its scale-assertion half is the part that binds.
- **q5 lighting practice** — hold for the `79476082` corpus answer, then amend
  `residential-lighting.md`'s GAP list in one edit rather than two.
