# TRN-002 r38 — which face holds is not in the measurement

**Tier:** distillation of a measured round. Every number is ours, back-projected
through this lane's own solved camera (unchanged since r1). No external claim.
Sits beside `trn002-r34-measuring-from-one-plane/` and
`trn002-r33-surface-texture/`.

The round's headline is local: an upholstered headboard panel built 176 mm thick
measures ~93 mm. **Half of what the round first concluded was refuted before it
shipped, by an adversarial pass fired at its own claims — and the refutations are
worth more than the conclusion.** Nine things it taught are not local.

---

## 1. A MEASUREMENT CANNOT TELL YOU WHICH FACE HOLDS

The panel's thickness was measured a round earlier and could not be applied for a
whole round, and the reason is worth stating as a rule rather than as a story.
Three masses met at one plane — a wall panel, a headboard, and a bed — and the
headboard's thickness was the invented number in the middle. Shrink it and
*something* has to move: either the bed follows the panel, or the panel leaves the
wall.

**The pixels are equally happy with both.** Both readings fit the same two lines;
they differ only in which plane you declare, and the declaration is not in the
image. So:

> **A number plus a contact is two facts, and only one of them is measurable from
> a frame. The round that types a coordinate for the other one has not decided —
> it has hidden the decision inside an edit that looks like arithmetic.**

This is R9 (*a coordinate encodes a RESULT, never a RELATIONSHIP*) one level up:
R9 says derive a position from a contact; this says **the contact itself is a
declaration and needs a datum, a reason, and a stated cost.**

## 2. THE TEST THAT PICKS THE DATUM: hold what other derivations already stand on

Not taste. Two mechanical questions:

| question | this round's answer |
|---|---|
| Which plane is **load-bearing for numbers already derived**? | the wall plane — the panel's height AND its near end were both back-projected onto it. Moving it re-derives the height (882.95 → 894.23), the near end (−4555.1 → −4645.4) and therefore the panel's length (2005.1 → 2095.4) |
| Which number in the chain **nobody ever measured**? | the bed's head coordinate. The lane's own identifiability audit had written it down a month earlier: *"the head end −1490 rides the x=−1290 chain"* |

**Hold the plane that other measurements are standing on; move the number that
was arithmetic all along.** That test survived the adversarial pass and picked the
panel's side correctly. **What it does NOT license is the second half of the
sentence** — see §8. "This number was never measured" tells you it may move; it
does not tell you where to.

## 3. THE DECLARED PLANE IS PART OF THE MEASURED VALUE

The thickness is not a fixed quantity that the contact then places. Under
"back on the wall" the near end sits at y=−4555.1 and the depth measures 92–95 mm;
under "front on the bed" the near end moves to −4645.4 and the SAME two pixel
lines give 90.2 mm. One view cannot separate an object's size from its distance —
this lane's geometry module says so in its own header — and a joint is one of the
declarations that closes that gap. **Report the plane with the number, always.**

## 4. AN ABSENCE TEST NEEDS A POSITIVE CONTROL, NOT JUST A NOISE FLOOR

The round argued that the built 176 mm was *"refuted by absence"*: where 176 puts
the panel's front arris, the strongest luminance step over 101 rows is 2.9 L,
against 2.4–3.1 L of flat field either side. That felt rigorous. **It has no
power, and the way to find out took one control.**

A skeptic ran the same statistic across a same-frame, same-class feature — the bed
plinth's own 90° vertical corner, white upholstered fabric meeting white
upholstered fabric — and the strongest response anywhere along **a corner that
indisputably exists** was **3.50 L**. Under this room's flat light the panel's two
faces differ by 0.8 L in luminance, so no corner on this object can produce a step
at any radius. The absence proved nothing about the geometry; it measured the
lighting.

> **"There is nothing there" is evidence only when the same instrument, in the
> same frame, is shown to respond to a thing of that kind that IS there.** A noise
> floor tells you the measurement is quiet. A positive control tells you the
> measurement can hear.

The conclusion survived anyway, on a statistic that does have power: the two
visible lines are 18.5 px apart on the near end and 2.95–3.66 px on the top, where
176 mm requires ~38 px and 4.8–6.6 px — a factor of two, at fit rms 0.24–0.35 px.
**A right answer defended by a powerless argument is still a defect**, because the
argument is what the next round inherits: this one had already been written into
the spec's permanent provenance.

## 5. A CONSEQUENCE THAT CANNOT FAIL IS NOT A CHECK

The round offered a second corroboration: hold the mattress's measured foot, put
its head on the panel, and it comes out 1987.3 mm — 7.3 mm from a manufactured
1980 and 12.7 from 2000, where the value it replaced (1904) *"is not a size anyone
makes"*. Four things were wrong with that, and every one of them is a general
trap:

* **The premise was false, by our own `knowledge/` file.** Panero & Zelnik,
  already promoted into the vault: bed 1905 mm = 75 in. The old value was **1.0 mm**
  from a standard length; the new one is 7.3 mm.
* **It could not fail.** Over the round's own declared depth bracket (84.0–95.1 mm)
  the length runs 1984.9–1996.0, and three of the four bracket values score
  *better* than the adopted one. Widen it by the foot line's own 24 mm width and
  the whole uncertainty region passes the test.
* **It preferred the rejected branch.** Leave the bed where it was and the mattress
  is 1904 — 1.0 mm from 1905.
* **Base rate.** Over a plausible 1850–2050 window, a two-size list at ±13 mm
  passes 23% of all lengths; the fuller size list passes 51%.

> **Before quoting an agreement, compute what fraction of your own uncertainty
> would have agreed.** If the answer is "most of it", the agreement is base rate
> wearing a decimal point. And check the sibling dimension: the same mattress is
> 1719 mm wide, which is 111 mm from the nearest size anyone sells — the test that
> "confirmed" one axis refutes the object on the other.

## 6. THE ESTIMATOR IS PART OF THE MEASUREMENT, AND THE BRACKET IS THE OUTPUT

The inner feature is a 2 px dark welt, not a razor edge. Two defensible sub-pixel
conventions on the same rows returned **84.0** and **92.7 mm**; a third party's
returned 85.3. Neither is wrong; the spread *is* the bead's own width (~9 mm).

Report the **band**, keep the first fit as the value of record (re-typing inside a
feature's own width is how a number drifts), and state the cost downstream in the
units that matter.

## 7. A JOINT THAT ONLY EXISTS IN PROSE IS NOT A JOINT

The strongest placement instrument here reads the BUILT scene and answers
FLOATING / OVERHANG / OFF-AXIS — all questions about *support*. **A butt joint has
no support relation**: a bed and a headboard 83 mm apart both stand on the floor.
It passes, correctly, and says nothing. The fix is a spec-side register of
declared contacts with a `datum` on every row, checked before every render — two
faces on one axis, at the declared gap, with the masses not overlapping along it
and overlapping on the other two.

**And the register cuts both ways, which is the point.** This round's first cut
declared two joints that a measurement then refuted. Had they shipped, a false
relationship would have been enforced as blocking law — strictly worse than
leaving it undeclared. *A register makes a claim checkable; it does not make it
true.*

## 8. RUN YOUR OWN INSTRUMENT TO THE OTHER END BEFORE CALLING SOMETHING UNMEASURABLE

The round declared the bed's head *"the one number in this chain nobody
measured"* and moved it to the panel. It is measurable, and the instrument had
been sitting in the lane for twenty-two rounds: r16 fitted the plinth's near-side
**base contact (z=12)** and its **top arris (z=221)** to fix the bed's near face
at y=−4180. Nobody had ever run those two lines toward the head. Run out
column by column they hold

    z = 12   y = −4181 ± 3 mm   u 800..980   contrast 61–142 L
    z = 221  y = −4174 ± 5 mm   u 840..980   contrast   8–11 L

— unbroken past x = −1406.7, out to x ≈ −1220…−1300. **The bed runs to the wall.**
It does not stop at the panel, which means the upholstered panel is *wall-hung*
above the base, which in turn explains the one number nobody had ever measured
about it: its bottom, typed z=0 since r1.

> **"Unmeasured" and "unmeasurable" are different words. Before declaring the
> second, check whether an instrument you already built and already trusted was
> simply never pointed there.**

The same round furnished the falsification test for its own edit and did not run
it: at the column where the proposed head face must cut that line, the response is
4.0 L against 3.0–4.0 L of flat field — nothing, by the very statistic the round
used to kill the 176.

## 9. WHAT THE ADVERSARIAL PASS COST AND WHAT IT BOUGHT

Three independent skeptics, one per load-bearing claim, each told to REFUTE and to
default to "refuted" when the evidence is thin. Two of three came back REFUTED and
both reproduced on the first attempt. They cost roughly half an hour of wall clock
and returned: one dead argument (§4), one dead corroboration (§5), one dead
conclusion (§8), plus four defects nobody had asked about — including that the
headboard is built as a square box while the reference's panel is radiused, and
that the plinth is modelled 221 mm tall when its own provenance measures the base
contact 12 mm up in the rug, so "top at z=221" and "height 221" are one parameter
carrying two things.

> **Point the skeptics at the round's OWN claims, one agent per claim, after the
> work is done and before it is committed.** A critic asked "what is wrong with
> this picture" finds what is wrong with the picture. A critic asked "break this
> specific sentence" finds what is wrong with the reasoning — and the reasoning is
> what the next round inherits.

---

## What this owes `knowledge/`

§1, §2, §3, §4, §5, §6 and §8 are general measurement discipline and belong beside
the existing rules on *plane ≠ surface* and *an arris holds its u*. §4, §5 and §8
are the three most reusable and none of them existed here before. §7 and §9 are
pipeline law, not domain knowledge. Nothing here is a Thai statutory value and
nothing here came from outside this machine.
