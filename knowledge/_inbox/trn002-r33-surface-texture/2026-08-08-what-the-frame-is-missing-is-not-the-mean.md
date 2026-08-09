# TRN-002 r33 — what the frame is missing is not the mean, it is the grain

**Tier:** distillation of a measured round. The numbers are ours, from our own
frames; the one external claim is cited and was read in its primary source.

## The question the round had to answer first

An outside experiment says surface texture is the strongest single cue for
whether an image reads as photographic: *Rademacher, Lengyel, Cutrell & Whitted,
"Measuring the Perception of Visual Realism in Images", EGRW 2001* — rough
surfaces ℜ **.71** against smooth **.39**, χ²=13.04, **p=.0003**, n=18, and the
paper states the effect is **stronger than the one due to shadow softness**. Our
own ground-truth study had measured this repo's texture-map coverage at **4.9%**
against **50–66%** in five delivered photoreal `.blend` files.

Two lines pointing at one lever is not permission to build. **r32 had just
measured the neighbouring quantity and found it healthy** — LIGHT_SPAN 0.909,
our light modulating each material at ~92% of the target's. If the surfaces are
already varying as much as the target's, the lever is imaginary.

## The two quantities are not the same quantity, and only one had been measured

    r32's LIGHT_SPAN     spread of MEAN value ACROSS OBJECTS wearing one material
                         → object-to-object modulation by light   (measured: fine)

    surface texture      pixel-to-pixel variation WITHIN one surface
                         → the Rademacher cue                     (never measured here)

`texture_check.py` measures the second: high-pass each frame, then compare per
object, `hf = std(L − blur(L,σ)) / median(L)`. Dimensionless, so a dark surface
and a bright one are comparable — the same normalisation `_spread` already uses.

**Both confounds push against a positive result**, which is what makes one worth
acting on: our render's sampling noise INFLATES our hf, and the target is a JPEG
whose compression ERODES its fine detail.

## What it found on r32

| σ | unmapped materials | mapped materials |
|---|---|---|
| 1 | **5.38×** | 2.95× |
| 2 | 2.73× | 2.44× |
| 4 | 1.91× | 2.42× |

n=22 and n=15 objects. **Not a global sharpness difference** — the per-object
range is 0.78 to 11.5, and the ceiling measures **1.06**, so "our render is
softer than a photograph" is refuted by our own frame.

Two different deficits, which a single averaged number would have hidden:

- **at fine scale, having no map means having no grain** (5.38 vs 2.95)
- **at coarse scale our maps are no better than no map at all** (2.42 vs 1.91) —
  they deliver the weave and not the larger variation a real textile carries.
  Weaker evidence: at σ≥4 part of the target's residual is its own JPEG blocking.

## The ranking that a ratio would have got wrong

`ward_body` is the largest object in the frame and reads **10.66×** at σ=1. Its
two numbers are **0.0049 and 0.0131** — a lacquered door IS smooth in the target,
and a ratio between two near-zeros explodes. Ranked instead by texture that is
absent AND actually present, weighted by frame area, the round goes to textiles:

    bench          upholstery_bed   0.0106 → 0.0581     43,368 px
    bed_headboard  upholstery_bed   0.0081 → 0.0457     18,429 px
    bed_platform   upholstery_bed   0.0165 → 0.0291     18,528 px
    throw_velvet   velvet_taupe     0.0162 → 0.0749     13,025 px
    petcave        upholstery_bed   0.0073 → 0.0545      3,154 px

**A ratio is not a priority.** That is the reusable half of this round.

## The mechanism underneath, and it is the lane's oldest one

Both materials **already declared the relief they were missing.** `NORMAL_STRENGTH`
carried `upholstery_bed: 0.6` and `velvet_taupe: 0.2` — and `build_materials`
returns EARLY for a row with no map, so neither value could ever be applied. Five
of the thirteen entries in that table were unreachable in exactly this way.

**Same class as the dead PALETTE rows r30 found and deleted, in a different
table.** A written decision that no code path can reach reads, in the source, as
a decision someone made — which is worse than silence, because it stops anyone
looking. `texture_check.unreachable_normal_rows` now finds them, and it knows
that `EMISSIVE` sits on the OTHER side of that early return and must not be
flagged — the first version of the audit flagged it and was wrong.

## What was NOT turned on, and why that is the finding too

Three of the five stayed dead ON PURPOSE:

- **`paint_ceiling`** measures **1.06**. The ceiling already matches. Turning on
  a relief there would be building to the table instead of to the measurement.
- **`paint_white`**'s six objects disagree with each other: 1.76 / 2.54 / 2.98 /
  3.73 / 4.50 / 22.21. **One material cannot be six different amounts wrong**, so
  that deficit is CONTENT in the target we do not model — most of it on
  `closet_back`, which already stands in for both a wall and a window. Declared
  as a gap rather than fixed, because a relief there would make the number better
  and the model worse.
- **`lacquer_wardrobe`** is the near-zero case above.

**The table proposed five repairs and the measurement authorised two.** The three
it refused are the part of this round that will still be true next month.

## THE ROUND FAILED, AND THE FAILURE IS THE RESULT

The relief was turned on and **rendered as nothing.** Measured at the same
resolution against the same target, quick rung, with controls:

| object | r32 | r33 (0.6 / 0.2) | LOUD (5.0) | loud/r32 | target |
|---|---|---|---|---|---|
| `bench` | 0.0146 | 0.0146 | 0.0134 | **0.92** | 0.0816 |
| `bed_headboard` | 0.0076 | 0.0074 | 0.0080 | **1.05** | 0.0543 |
| `bed_platform` | 0.0225 | 0.0232 | 0.0211 | **0.94** | 0.0333 |
| `throw_velvet` | 0.0199 | 0.0197 | 0.0126 | **0.63** | 0.0941 |

controls: `ceil_main` 1.00, `ward_body` 1.01, `desk` 0.99.

Raising the amplitude **8.3×** and **25×** moved nothing. Three of four went
DOWN. **This is not "not enough yet" — it is a knob that cannot reach.**

And the mechanism was verified present in the rendered file, not assumed:

    upholstery_bed  imgs=['rough_linen_nor_gl_2k.jpg']  normal_nodes=1
                    strength=0.6  bsdf.Normal linked=True

**The strongest evidence had been sitting in the scene for rounds, unmeasured.**
`rug_cream` has used this exact path — DIFFUSE_OFF plus a normal map — at
strength **0.9** the whole time, and `rug` measures **0.0045 against the target's
0.0493, an 11× deficit.** The path has never produced measurable texture for any
material in this lane. It was there to be found and no instrument asked it.

### Why, and it is the same defect r32 ticketed from the other side

A normal map perturbs the surface normal; the shading response is N·L integrated
over the source. **Our area lights are 1.6–3.0 m across at 2–5 m — tens of
degrees of subtense** — and that integral barely moves when the normal moves.
Soft light washes relief out.

r32 wrote its own light ticket independently: *"paint_white is ONE material on
the back wall and the left wall. The target renders them 1.58× apart and we
render them 1.01× apart — our walls do not differ, so the room has no direction
in its light."*

**The texture deficit and the light-direction deficit are one defect seen from
two sides.** Two measurements, two rounds, two lanes, one cause.

Not yet proven directly: what IS proven is that it is not the amplitude and not
the wiring. The kill is cheap and is named in gate #21 — a small grazing light on
one surface, then re-measure that surface. **Do not bracket normal strength a
third time.**

## Banked for the lane

1. **A ratio between two near-zeros is not a defect, it is a division.** Rank a
   material round by the ABSENT QUANTITY, weighted by frame area, never by ratio.
2. **A tool measuring "variation" must say which spatial scale it means.** Ours
   answered two opposite things at σ=1 and σ=4, and the prescription flips.
3. **A dead declaration recurs per TABLE.** r30 found it in `PALETTE`, r33 in
   `NORMAL_STRENGTH`. The next one will be in a table nobody has audited yet, so
   the check is written over "tables that sit after the early return", not over
   the two tables that have been caught.
4. **A guard that fires on correct work gets switched off** — and it nearly
   happened here. The r32 bundle carried a 13 KB triage answering all 24 critic
   items, and `rule_gate` read it as empty because it globbed `TRIAGE_*.md` and
   the file was `TRIAGE.md`, and because its table-row regex could not survive
   `| **1** |` or `| **G1** |`. It refused the next render for 24 items that had
   all been answered. Fixed with four tests, one of which checks that tolerating
   the FORM did not start tolerating ABSENCE.
5. **And the gate that check was hiding:** with those false positives gone, the
   charter's distillation check became fatal for the first time. It had never
   fired, because `hard` is set to `not older` and there were always older
   violations. **A gate that only fires when nothing else is wrong has never
   fired.** This file exists because it finally did.
