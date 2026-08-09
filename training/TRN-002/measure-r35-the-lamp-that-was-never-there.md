# TRN-002 r35 measurement — the bedside lamp is a hanging pendant, and the
# body we built for it stands in a volume the reference shows as lit oak wall

Every number below is a sub-pixel read off our own target, back-projected (where
back-projection is possible) through this lane's camera, unchanged since r1.

---

## 1. WHAT SENT ME TO LOOK

C2 (blind, r34) filed *"no nightstand, no bedside lamp"* and I accepted it as an
R10 object item. C3 (Gemini, r34) never mentioned it — correctly, since with no
reference it cannot know what belongs there. Neither critic found what is
actually wrong. **The projection did:** `nightstand` and `lamp` are at the
extreme right edge, 116 px and 62 px of them inside a 1080-wide frame, so C2 was
describing a sliver rather than an absence.

Then the sliver turned out to be wrong in a way no critic could have named.

## 2. THE MEASUREMENT

`lamp` in `spec_r34.json`: one mass, 220 x 220 x 640.7 mm, standing on the
nightstand top at z 481 and rising to z 1122, material `shade_black` for its
whole height. Its own provenance:

> M(shade silhouette u1057-1080, v484-508, hard containment: no pixel left of
> u=1057) / **DECLARED(the body below the shade is OCCLUDED in the reference by
> the bird sculpture and book stack**, so it is modelled as the minimum envelope
> that stands the measured shade on the measured nightstand top 481 …)

**The occlusion claim is false, and the pixels say so plainly.** The strip
directly below the cone, in the rows where the invented body would stand:

| region | rows | mean RGB | L |
|---|---|---|---|
| the cone itself | v 484-508 | (104, 96, 89) | **96.6** |
| **u 1057-1080, below the cone** | v 510-530 | (169, 144, 115) | **142.7** |
| " | v 530-550 | (175, 147, 114) | **145.1** |
| " | v 550-570 | (164, 138, 108) | **136.4** |
| known oak wall, same rows, to the LEFT | v 510-570 | (149→134, …) | 108-127 |
| known black object (the bird) | v 600-630 | (75, 61, 48) | **61.0** |

The volume our lamp body occupies is **oak wall — and brighter than the oak
beside it**, not darker. The bird sits at v 600-630 and the books below that;
both are *under* most of the span they were said to occlude.

## 3. WHAT IS ACTUALLY THERE — a conical PENDANT, and it is measurable

Leftmost dark pixel per row, sub-pixel, u 1040-1080:

    u = -0.84893 * v + 1488.422      rms 0.170 px over 24 rows (v 483-506)

**Straight to 0.17 px, and it DRIFTS.** That settles the class by itself, using
the discriminator this lane earned in r34: under a yaw-only camera a vertical
edge holds its u at every height. A cylinder's silhouette would hold; an arris
would hold. **A steady slant is a cone flank.**

* apex at v = 483, u = 1078.4 — essentially on the frame's right edge
* rim at v = 507, u = 1058.0; the edge kicks back right at v 507-508 and ends
  (the rim closing), then nothing
* image rim radius 20.4 px, cone height 24 px
* **a cord at u 1044.9 → 1044.7 across v 512-515 — 0.26 px of drift in 3 rows,
  a true vertical.** A hanging cable, which is what a pendant has and a table
  lamp on a nightstand does not

So: black conical shade, point up, flaring down, hung on a cord, its axis at or
just beyond u 1080. Not a lamp standing on the nightstand.

## 4. WHAT IS STILL NOT MEASURABLE, AND WILL NOT BE TYPED

**The pendant's depth in y.** One view, one silhouette; the cone's distance from
camera and its true size trade off exactly, and nothing in the frame pins them
apart. R10 is explicit: the moment a measurement pass says a dimension is
unmeasurable, typing a number for it is the defect. It goes in as a DECLARED
assumption against a named datum (the nightstand's own measured y centre-line)
with a bound, or the pendant is a declared gap. It does **not** get a plausible
number.

The same restraint retires the old lamp: its height was never measured either,
and 640.7 mm was the length of the gap between two measured things.

## 5. THE PROCESS FINDING, which is the part worth keeping

CLAUDE.md's R10 already names this exact object:

> `lamp_stem`, a bare post whose provenance literally reads "carries shade" — it
> exists so a measured shade would have something under it, and the target shows
> a bird and books there

That was caught, and the fix was to **merge `lamp_shade` + `lamp_stem` into one
mass**, whose `why` says so approvingly: *"It is ONE mass because the previous
two-mass version invented `lamp_stem`."*

**Merging deleted the accusation and kept the fabrication.** R10's gate asks
every mass to justify itself; a fabricated volume folded into a measured
object's mass inherits that object's provenance and stops being a separate thing
to justify. The bare post was visible precisely *because* it had to carry its own
`why`.

> **A justification gate counts masses. Merge two masses and you halve the
> number of justifications it will ask for — without removing anything from the
> frame.** The cure for an unjustifiable object is deleting it, never absorbing
> it into a neighbour.

Same family as ONE PARAMETER CARRYING TWO THINGS, arriving from the other side:
there, one number quietly meant two; here, one *mass* quietly means one measured
thing and one invented thing, and the gate can only see the pair.

## 6. LANE FOR r35

1. **DELETE** the fabricated body. The pendant is built from the fit above, its
   y declared against the nightstand datum and bounded — or declared a gap.
2. The nightstand top carries **a book stack (BUILD — boxes, measurable) and a
   bird figure (ACQUIRE — R8 forbids hand-modelling animals; a declared gap if
   acquisition fails)**.
3. The nightstand reads in the reference as a **floating oak slab** with a
   shadow gap under it; confirm against `veneer_oak_h`, already assigned.
4. Re-check `nightstand`'s y: its own prov records an arris spanning
   y -4706..-5132 (**426 mm**) while the spec carries **700 mm**. Unreconciled;
   measure before touching.
