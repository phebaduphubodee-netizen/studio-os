# TRN-002 r34 — an arris holds its u, a silhouette does not

**Tier:** distillation of a measured round. Every number is ours, backprojected
through this lane's own solved camera (unchanged since r1). No external claim.

The round's headline is local and uninteresting outside this room: a wardrobe
had been standing 1,200 mm behind where it stands. **Four things it taught are
not local**, and three of them are about the difference between a measurement
and a number that looks like one.

---

## 1. THE TECHNIQUE: a real edge holds its image coordinate across rows

Under a camera with yaw only, a **vertical world edge lying on a plane of
constant depth projects to the SAME u at every height.** That is not a
convenience, it is a *discriminator*, and it settled three separate questions in
one round:

| feature | reading | verdict |
|---|---|---|
| wardrobe's right edge | u 366.5 at v 360 / 400 / 440 / 480 / 520 | **an arris.** Five agreeing heights is the check, not a repetition of one |
| niche return's near edge | u 361–362, steady | **an arris** |
| niche return's *far* edge | u 355.3 → 357.8 as v goes 360 → 420 | **NOT an edge.** It is a hanging shirt's silhouette |

**The same band had already been misread twice, in opposite directions, for
exactly this reason.** An earlier pass derived a 462 mm niche depth from it and
was refuted. My own pass today derived 245 mm from it — different rows, same
contamination. Refitted over only the 50 rows where nothing hangs in front
(v 332–355 and 440–465) it gives ~200 mm, and honestly a **bound of 100–350**
because the far edge's own scatter is 4.03 px.

> **Reusable rule: before believing a width, check whether both of its edges
> hold still. An occluding contour drifts with the thing that casts it.**
> The tell was present in both wrong readings and nobody looked for it.

Same family as the TRN-001 lesson *plane ≠ surface*: the arithmetic is right and
the thing being measured is not what you named.

## 2. ONE OBJECT, ONE PLANE — for every axis, not just the interesting one

The LED strip's **ends** were measured on the front plane (y = 1130) and its
**height** solved on its declared setback (y = 1193). Both readings were correct
and the object was wrong: its ends reprojected 1.2 and 1.6 px off the pixels
they came from. Solving all three axes on one declared plane put them at 0.05
and 0.04 px.

**A declared setback is a declaration about the whole object.** This is the
lane's own recurring shape — *one parameter carrying two things* — inverted:
here, two planes carrying one object.

## 3. A NUMBER TYPED INTO A CHECK IS NOT EVIDENCE

The pre-render verification failed on the plinth by 6.4 px and **the geometry
was right**. The expected pixel, `v = 567.2`, was an eyeball average I typed
from the phrase "the band runs v 560..574". Replaced with an actual 60-column
sub-pixel fit (`v = -0.04412u + 575.381`, rms 0.159 px) it agrees to 0.20 px —
and that fit independently gives the plinth height as 104.6 ± 0.1 against the
measurement pass's 106.2 ± 1.0, two fits agreeing to 1.6 mm.

**A check whose expected value was estimated tests the estimate.**

## 4. AND THE ONE THAT NO NUMBER FOUND: look at the thing

Hours of correct arithmetic produced a 600 mm wardrobe carcass, reasoned from a
garment chart's "hung shirt: 550 deep". **One crop of the niche showed a shallow
display alcove with a single shirt in it** and the reasoning collapsed — the
chart still applies, but to the **width** (a 550 mm shoulder in a 602 mm clear
opening), which is a *different* constraint that happened to share a number.

> **A shared number is not a shared quantity.** The chart's 550 was doing real
> work in the wrong dimension, and nothing numeric could have caught it, because
> nothing numeric was wrong.

This is R4b (reference-before-build) paid for again — not "we had no reference",
but "we had one and reasoned instead of opening it".

---

## Process findings, filed here because they are the round's real product

**A blind critic's description of OUR OWN render entered the manifest as a fact
about the target.** `mirror` was on the build list from C3#11 at r23; by R7b law
that critic saw our render and nothing else, and at r23 the bay was filled by an
assumed blank panel that rendered blown white. It described our frame correctly
and called it a mirror. **Deleted 2026-08-08** by reflecting 24 bay rays about
y=0: a plane mirror there would be *obliged* to show the bedroom's herringbone
at v 540–580 and the white rug over u 181–498, and the bay shows neither.
R10b already said a blind critic answers *"is this believable"* and never *"does
this match the reference"* — **this is the first case of that gap creating an
object rather than mis-describing one.**

**An instrument's declared blind spot is a confession, not a guard.** A new
scale-assertion module's docstring said in advance that it "cannot see
proportion at all". Its first real asset was 715 mm tall, in band, SCALE
ASSERTED — and 11.7 mm thick, a billboard cutout. Cheap to close; left open
because it had been written down. **Writing down a hole does not make it safe.**

**A rule needs its DATA reachable, not only its code.** R1's `cap_check` — the
first rule this studio adopted — was a working function with four passing tests
that nothing called for 34 rounds. Not an oversight in the code: it needed a
number only the owner may set, and the ledger meant to hold it is a markdown
table nothing parses, with no row for this unit at all. **A rule is real exactly
to the extent that it is a program that fails in a path someone already runs —
and that requires its inputs to live where a program can reach them.**

**A prose mention is not a call.** The instrument built to find unwired
instruments counted any occurrence of `<name>.py` in any text as an invocation,
and produced its own false green the hour a new docstring cited an old module.
Fixed; the unreached count went 55 → 71 **with the tree unchanged**. Two of the
sixteen sting: `look_bench` is R4's own command (named in prose, not in a
`## Commands` block) and `texture_check` was written and used the previous day.

---

**Distil to `knowledge/` next:** items 1 and 2 belong with the TRN-001
measurement laws (`plane ≠ surface`, `one parameter carrying two things`) —
they are the same family and should sit on one page. Items under "Process
findings" belong with the critic-ladder rules in `brand-standards/`.
