# An instrument that cannot fail — the four shapes, and how to test for them

Promoted from `knowledge/_inbox/trn003-3dshaker-study/what-a-tutorial-workflow-actually-assumes.md`
(TRN-003, 2026-08-29). Sits beside `knowledge/brand-standards/iteration-control-and-review-gates.md`,
which sets WHEN the studio stops; this file is about whether the thing it stops on can say no.

**Why it exists.** In one round this studio built four guards and every one of them could be
passed without the thing it measured being true. They were not sloppy: each carried a docstring
arguing it was sound, and two of them argued it in the same paragraph as the defect. **A guard
is not proved by the gap it closes. It is proved by being made to fail on purpose.**

---

## SHAPE 1 — THE DEFINITION THAT MAKES THE ANSWER TRUE

A quantity is *solved from* the condition it is later reported as *checking*.

**Case.** A camera solve set the focal length as `f = sqrt(-(vpA-px)(vpB-px))` — exactly the
focal that makes the two horizontal axes perpendicular — and then reported *"the two axes come
out 90.02° apart and nothing forced this"* as its headline validation, in three files and a
commit message.

**Test: feed it nonsense.** Forcing the principal point to x = 300, 600, 720 and 900 returned
orthogonality **90.0000000° every time** while the focal moved from 3983 to 4331 px. Four
fabricated input lines returned 90.000000000 as well. The 0.02 was float noise.

**What to report instead:** the reproduction of features the solve did NOT set. Here that
number existed and was recorded nowhere; when it was finally computed it was 33.59 px, and
fixing what it exposed took it to 4.36.

## SHAPE 2 — THE IRRELEVANT KNOB THAT MOVES THE VERDICT

A rung claims to measure a physical property and is in fact reachable from a control that
changes nothing physical.

**Case.** A lit-minus-shadow contrast check claimed *"exposure cannot fake it: raising exposure
raises both samples together."* Same lights, same scene, only the exposure knob moving:
`-2.0 → 128 FAIL`, `-1.0 → 99 PASS`, `0.0 → 70 PASS`. The knob walks the rung from fail to
pass. **Why:** raising exposure lifts both samples only while both CAN move; once the bright
one is against the end of the display range it stops, the dark one keeps climbing, and the
difference collapses.

**Test: turn every knob that should have no effect, and watch the verdict.**

**Two fixes, and both are refusals rather than corrections.** A sample whose median is against
the end of the range is not a reading. And two frames must sit at the same place on the tone
curve before their differences may be compared — which also SPENDS the knob: exposure is now
used to match the levels and is no longer free to move the answer.

## SHAPE 3 — THE SELF-CHECK AGAINST A NUMBER IT COMPUTED ITSELF

A cross-check compares two quantities, one of which was derived from the other.

**Case.** A repeated-object solver's whole claim to be a measurement was its self-check: object
depth from the contact row against object depth from silhouette width, refuse if they disagree
by more than 5%. It was fed a block in which the second object's silhouette width had been
COMPUTED from the first object's radius. It reported **`width_agreement = 0.0000%`, exactly
zero, on both instances.**

**Test: an agreement of exactly zero is not a good result, it is a red flag.** Real independent
measurements of unequal quality do not agree perfectly. When both were read independently the
agreement became 3.4% — a number that could have been 8% and failed.

**Corollary on conditioning:** two quantities of unequal quality agreeing is not agreement. The
near silhouette here read to sd 0.04 px (a 165-level step); the far one wandered 5.6% across
row bands (a 15 px ramp into background). Cite the conditioning next to the agreement or the
agreement is decoration.

## SHAPE 4 — THE GUARD THAT LOOKS AT THE WRONG THING

A guard is real, fails closed, and inspects a surface adjacent to the one that leaks.

**Case.** A blind-critic bundle builder refused the reference image and the comparison pool BY
CODE — the leak everyone thinks about — and never looked at the PROSE it copied in. The standing
prompt handed the judge a named earlier render, how many items a previous critic had filed
against it, and a narrated past defect complete with its offset in millimetres. **The blind
critic found this itself and filed it against the bundle.**

**Test: name what the guard inspects, then name what actually travels.** If those differ, the
gap is the leak.

## AND THE SHAPE THAT BITES WHILE YOU ARE FIXING THE OTHERS

**A guard calibrated on one failure will refuse a good reading for the wrong reason, and that is
not the safe direction to err in — it is how a rung gets switched off.**

The clip refusal from Shape 2 was written against a blown-highlight frame and applied its
threshold to the WHOLE PATCH at 2%. One frame later it refused the best reading the lane had
ever produced (lit 180 / shadow 92 against a target of 176 / 100) because 2% of that patch sat
at pure black in a deep shadow, while the relevant sample's median was 92 and nothing was
holding it anywhere. Wrong denominator, and a threshold far below anything that could move a
median. **A threshold belongs to the sample it could corrupt, not to the box the sample came
from** — and it must be set at the level where the corruption could actually change the answer.

## THE STANDING PRACTICE

1. **Every new guard ships with a NEGATIVE CONTROL**: the exact input that should convict it,
   run and recorded, in the same commit. Not a hypothetical — a run.
2. **Every "we found nothing" needs a POSITIVE CONTROL**: something in the same data, measured
   the same way, that certainly IS there and scores clearly.
3. **Write down what the guard CANNOT catch.** The blind-prompt scanner catches mechanical
   recurrence — a round identifier, an item count, a quoted offset. It cannot catch paraphrase,
   and saying so in the file is the difference between a limit and a false sense of coverage.
4. **A refusal is a result.** `COULD NOT RUN` must never print like `looked and it was fine`,
   and a verdict sized smaller than its own inputs' noise is the defect, not the number.
