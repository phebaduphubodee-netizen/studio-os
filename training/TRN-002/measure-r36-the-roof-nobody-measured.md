# r36 · item 1 — the roof nobody measured, and the corroboration that was never evidence

`petcave` is the largest mass in the lower third of the frame. Its height was
**550 mm, typed at round 1 and never revisited in 35 rounds** — its own
provenance said so: `A(x, z, and all three sizes still assumed — unchanged from
r1)`. Gate #23 set this round's first item: declare the front plane against the
measured mouth datum **with bounds**, derive z from the measured line, never
type z.

---

## 1. The measurement, re-taken rather than inherited

Ten columns across the top boundary of the pale mass in the lower right,
sub-pixel edge where luminance steps by more than 40 L, scanning v 690..790:

| u | 940 | 955 | 970 | 985 | 1000 | 1015 | 1030 | 1045 | 1060 | 1075 |
|---|---|---|---|---|---|---|---|---|---|---|
| v | 755.410 | 738.863 | 730.931 | 727.732 | 725.525 | 722.755 | 720.781 | 718.892 | 717.383 | 715.709 |

**The ten are not one edge.** One line through all ten fits to rms **4.97 px**
with a clean sign pattern and an 11.9 px residual at u=940. Restricted:

| subset | n | slope | rms |
|---|---|---|---|
| u ≥ 940 | 10 | −0.23898 | 4.967 |
| u ≥ 955 | 9 | −0.17298 | 1.857 |
| u ≥ 970 | 8 | −0.14299 | 0.582 |
| **u ≥ 985** | **7** | **−0.13385** | **0.401** ← adopted |
| u ≥ 1000 | 6 | −0.12778 | 0.351 |

The left columns run at −1.103 px/px (940→955) against −0.134 for the straight
stretch; the break is at u ≈ 977.

**Which plane the edge lies on** — a horizontal edge back-projects to a constant
z only on the right plane family. Relative spread of the four back-projected z:

| plane | y = −5914.8 | y = −5464.8 | y = −5014.8 | x = −2100 | x = −1750 | x = −1400 |
|---|---|---|---|---|---|---|
| spread / mean | 0.0168 | 0.0274 | 0.0489 | **0.3219** | **0.5420** | **1.1498** |

A y-plane, decisively. **Which y-plane is not answerable from the spread** — and
that is not a limitation to work around, it is arithmetic: back-projection onto
a parallel plane is a uniform scaling about the camera, so spread/(cam_z − z) is
identically 0.01437 on all three. The image cannot see depth.

## 2. The two measurements could not both describe one object

The arch was fitted at r29 over 76 back-projected points on the host's −x face:
centre (y −5464.8, z 199.6), R 149.9, rms 2.77 mm — **crown at z 349.5**. The
ridge on the plane the spec then declared reads **z 296.5**.

**The roof was measured 53 mm below the crown of its own mouth.** Only the
never-measured 550 hid it: set the height to the measured value and
`arch_pocket` raises its own guard, *"the mouth's crown reaches the top of its
host face"* — a guard the repo has had, and pinned with a test, since r29.

The contradiction is **scale-invariant**. Link the arch's plane and the ridge's
plane through the object's left corner and the crown/roof ratio is fixed by that
corner's column alone: 1.18 at the sharp corner, 1.097 at u=951, 0.998 at the
built oct's own silhouette. Moving the object along the camera rays scales crown
and roof together, so no distance and no size fixes it.

## 3. r29's `CORROBORATED` clause is retired — three independent reasons

The record has carried, since r29, *"the boucle silhouette edge reads u~950 …
the derived y projects that corner to u = 935 = 15 px, inside the error of an
oct's rounded corner"*.

1. **It compared a sharp corner against a mass that has no sharp corner.** The
   built oct's leftmost silhouette is at **u = 970.46**. The rounding does not
   close a 15 px gap; it opens a 19 px one on the other side.
2. **A vertical arris there makes the object impossible** — crown/roof = 1.097,
   scale-invariantly (§2).
3. **Built at every shell thickness in the whole legal bracket**, this object
   covers only 5–6 of the ten measured columns and its left silhouette never
   goes left of **u = 989**. The pale mass from 951 to ~990 is not the pet cave
   in *any* variant.

So the left columns belong to the neighbouring mass, and the `seen` field's
*"body u 951..1080"* was **two objects read as one** — which is what let a
550 mm height look supported for 35 rounds.

## 4. What breaks the tie, and what it costs

Height and depth are one unknown from one view. What converts the free parameter
into a **bracket** is that the arch is a *hole in this object*: its crown is
under this roof and its jamb is inside this face.

| | far plane | z_top | |
|---|---|---|---|
| t = 0.0 mm | −5314.9 | **398.1** | arch tangent to the far face; all material over the crown |
| t = 143.5 mm | −5171.4 | **349.5** | roof grazes the crown; all material beside the jamb |

**Both ends are measurements, so the bracket is a measurement.** The typed 550
sits **152 mm outside it**.

**DECLARED, one sentence:** the shell is the same thickness over the crown as
beside the jamb. → **t = 36.30 mm, z_top = 385.80 mm**, roof and crown+shell
agreeing to 6e−14 mm. The 36 mm is its own R10 question-3 check: a moulded
boucle shell is a few tens of mm, and a solve returning 4 mm or 300 mm would
have been telling us the model is wrong.

**Still declared:** the arch's own plane, x = −2100, assumed since r1. z_top
moves **−0.38 mm per +1 mm** of it. The object now hangs on exactly **one**
declared scalar. It used to hang on two, and the two disagreed by 53 mm.

**What the same sentence forces**, listed so it reverses as one thing:

| | was | now | why |
|---|---|---|---|
| depth y | 900 | 372.4 | 2(R+t); mouth stays centred in y per r29's own derivation |
| width x | 700 | 486.3 | pocket depth + t; the back wall was 250 mm against a 36 mm shell |
| plan cut | 250 | 18.15 | **derived ceiling**: the flat face must still reach the arch's far jamb, so cut < t |

The plan-cut ceiling is where the old shape family dies: with cut = 250 the mouth
needs a half-depth ≥ 399.9, which caps z_top at 313.9 — still 35.6 mm below the
crown. **No depth rescues cut = 250.** Shrinking it is the only escape inside
this shape family, and that it is the only escape is itself a mark against the
family (see `declared_gaps.petcave_class`).

## 5. Verification

- Built roof reprojected onto the measured columns: **rms 0.468 px over 6/7**.
  r35's roof missed the same columns by **80–96 px**.
- Closure residual (roof from ridge vs crown+shell from the arch): **6e−14 mm**.
- Seam host↔patch after deriving `face`: **watertight to 0.0 mm** (was 50 mm
  overhang on both sides).
- Nightstand interpenetration (AABB, advisory per R9b): **170 → 21.4 mm**, a
  corner clip. NOT fixed here — r35 recorded in writing that neither end of the
  nightstand is measurable, so moving it would swap one typed number for
  another. Carried to r36 item 3.
- Independent adversarial re-derivation (fresh context, own sub-pixel fit from
  the target): **CONFIRMED**; its ridge columns agree with these to **0.85 px**,
  and its full-silhouette solve (110 columns, sd 3.4 mm) gives z_top 298.1 on
  the old plane against the 296.5 read here.

## 6. A second defect, found while doing this

The pocket's `face` tuple — the hole the surround strips fill — was typed as the
mouth centre ± the **cut** (250) where `oct_mesh` drops the quad at
± (half-depth − cut) (**200**). Both strips overhung the host by 50 mm and hung
in air. `arch_pocket`'s docstring promises the seam is *"watertight by
construction rather than by tolerance"*, and the construction was reading a
hand-typed field **no generator ever emitted** — `_mk_r29.py` writes the pocket
and not this field; it was added to the JSON out of band.

Now derived by `open_face_quad`, refused by `pocket_face_violations`, and the
check runs on the **build path**, not only in tests: a hand-editable field needs
a guard where the file is consumed, not one that fires when somebody remembers
to re-run a maker.

> **Class:** the same shape as R9, one level up. A coordinate encodes a RESULT
> and a `face` tuple encodes a RESULT, so resizing the host leaves both
> perfectly legal and silently wrong. And the height had *three* independent
> copies — `s[2]`, `c[2]` (= s[2]/2), and `face[2]` — with nothing cross-checking
> them.
