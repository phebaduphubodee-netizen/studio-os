# Luminance ratios (the gap nobody was answering) and the LED rebate, built

**Sources (REFERENCE tier), five watched, two of them thin and said so.**

1. `reK_jQ1UtaY` — <https://www.youtube.com/watch?v=reK_jQ1UtaY> · Catalin Design,
   *"Luminance ratios for a workplace"* · 4 min 15 s → **the "how bright relative to what"
   gap.**
2. `AAoo_VwqQZc` — <https://www.youtube.com/watch?v=AAoo_VwqQZc> · Insider Carpentry
   (Spencer Lewis), *"Floating Shelves LED Lighting — How to Router Channel for Tape
   Lights"* · 12 min 42 s → **P2r-29(b), the rebate.**
3. `axVhLMkgq2U` — <https://www.youtube.com/watch?v=axVhLMkgq2U> · RRR Woodworks,
   *"Building Long Bookshelves That Don't Sag"* · 10 min 06 s → **shelf span.**
4. `22ijpgjmkWY` — <https://www.youtube.com/watch?v=22ijpgjmkWY> · Technogips Pro, *"How to
   Build Decorative Hidden Curtain Rod"* · 3 min 20 s → **frames only, no speech.**
5. `KX6ZYSo8apo` — <https://www.youtube.com/watch?v=KX6ZYSo8apo> · Unity Interiors by Ekta,
   *"Perfect Switch & Socket Placement for Every Room"* · 7 min 44 s → **yielded nothing;
   see §5.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py`; transcripts via
`youtube-transcript-api`. Timestamps verbatim.

---

## 1. LUMINANCE RATIOS — the first quantitative answer to "how bright, relative to what"

The G4 gap judge wrote: *"NOBODY TEACHES LUMINANCE RATIOS — every candidate answers WHERE a
fixture goes; none answers HOW BRIGHT each surface should be relative to the others, which
is exactly the number our flat frame needs."* This unit answers it.

`[00:55]`-`[01:52]`, a lighting engineer stating the recommended bands:

| Zone | Ratio to the task | His words |
|---|---|---|
| **task area** | **1 : 1** | *"where we have the laptops… we have a 500 lux, here we will be the ratio one to one, the maximum output"* |
| **immediate surrounding** | **3 : 1** | *"the area around the task, the ratio will be three to one"* |
| **surrounding area** | **5 : 1** | *"then we go to ratio five to one"* |
| **background (walls)** | **10 : 1** | *"background — so means walls… where we have also a limit of 0.5 metres from the walls, we call it the background area, we'll have a ratio of ten to one"* |

And the failure mode he opens with `[00:28]`, which is our situation named from the other
side:

> *"when you're using **downlights** or luminaires which have **low luminance**, then it
> might occur that **the top of the walls and the ceiling being too dark**, and therefore
> you need to pay attention to the luminance ratio."*

Two things follow for us:

- **The unit is cd/m², a measured surface luminance** — not lux at a point, and not the
  render's exposure. `[00:00]` he explicitly separates *illuminance* from *luminance*. Our
  D-rows measure image statistics; this is a scene quantity with a published target
  structure, and the two can be reconciled on a linear render.
- **It gives the SHAPE of a correct lighting solution, not just an amount**: a 10:1 spread
  between the brightest task surface and the wall background, with two graded steps between.
  A frame where everything sits inside ~1.5:1 is flat *by this definition*, which is what
  every critic has said about ours in words.

**Caveat, recorded plainly: this is a WORKPLACE standard** (EN 12464 territory — task,
immediate surround, surround, background, and the 0.5 m wall band). A bedroom is not an
office and the numbers should not be lifted wholesale. What transfers is the **framework and
the order of magnitude**: a designed room has a deliberate luminance hierarchy several times
wide, and ours has never been measured as a hierarchy at all.

He also gives display-luminance classes `[02:47]`-`[03:41]` (high-luminance ≥ 1000-3000
cd/m² depending on task type) — not relevant to us, recorded so nobody re-watches for it.

---

## 2. THE LED REBATE, BUILT — what P2r-29(b) is actually asking for

C2's item on our casework strips: *"they glow but light nothing."* The plan row says the
strips should *"sit in a REBATE instead of reading as raw bars on the soffit."* This is a
carpenter routing exactly that rebate, and the assembly has four parts, not one:

`[00:00]` *"I purchased these **channels**… They come with **the channel and a diffuser**,
which will go across the top over the **tape lighting**."*

So: **shelf → routed dado → aluminium channel → LED tape inside → diffuser lid.** The light
the eye sees is the diffuser, flush with the timber; the tape is never visible.

Numbers and practice worth keeping:

- **End inset** `[00:37]`: *"These particular channels were **39 inches** long, and my
  shelves were **41 inches** long, which **gave me an inch on both sides**."* The channel
  stops ~**25 mm short at each end** — the same order as the hang-rail's cup-bracket
  allowance, and the opposite of a bar running the full width.
- **Fit clearance** `[02:58]`: the jig's spacers are the channel width **+ 1/8 inch**
  (3.2 mm) *"if you make this too tight, you might have trouble getting your aluminium
  channel into your dado, or getting it out"* — he then went to **3/16 in (4.8 mm)** for
  extra room. A real rebate is slightly wider than its extrusion.
- **Depth** `[06:29]`: set by placing the channel under the jig and dropping the bit until
  it touches the shelf — i.e. **dado depth = channel depth**, so the diffuser finishes flush.
- **A down-cut spiral bit** `[05:54]` *"is important, because that is going to make sure we
  get a really nice cut on this dado and we're not actually pulling chips up, which might
  lead to some tear out."*
- The tape is held with **double-sided tape** rather than the supplied clips `[00:37]`.

> **For the build this is a box-and-slot, R8 BUILD class**: a groove of the extrusion's
> section, inset 25 mm from each end, with a diffuser face flush with the timber. It is
> also why "glow but light nothing" is a geometry defect — a bar sitting proud of a soffit
> has no channel, no diffuser and no depth, so it can only ever read as an emissive strip.

---

## 3. SHELVES THAT DO NOT SAG — the method, seen rather than said

`axVhLMkgq2U` is mostly music, but the brief is spoken `[00:01]`-`[00:34]`: a bookcase for
*"this big old set of law books"*, **320 inches of shelf space**, seven shelves, *"about
five feet wide"* (**~1524 mm span**) — and the constraint:

> *"what that means for support with these big heavy books is **I don't want the shelf to
> sag or bow** or anything, and I really don't want to make it that way with a divider in
> the middle for support. So I'm going to be using **a slightly different method than the
> traditional 3/4 inch piece of plywood that is generally used for shelves.**"*

`frame_0058` shows the answer: every shelf carries a **solid-wood front rail** — a deeper
apron glued along the front edge of the plywood shelf, with arched cut-outs — which turns a
flat plate into a stiff T-section without a centre divider.

**Bearing on P2r-29(c) "shelves with no pins" and on our own casework:** a real long shelf
is either thicker at the front or supported in the middle. Ours is a plate. And this pairs
with the hang-rail rule already recorded (`iJYto0muSd4`): **a span over ~1524-1829 mm needs
either a section change or an intermediate support** — the same threshold appearing for a
shelf and for a rod.

---

## 4. THE GYPSUM CURTAIN POCKET — frames only

`22ijpgjmkWY` carries **no speech at all** (music and captions only), so nothing is quoted.
The frames show a proprietary gypsum profile being screwed to a stud line to form a
recessed pocket in the ceiling plane. It corroborates the assembly already recorded from
`saFsrHObKyk` — pocket → bracket → track — in **plasterboard construction**, which is the
relevant case for a Thai ceiling, and nothing more. Kept as corroboration, not as a source
of numbers.

---

## 5. ONE PICK YIELDED NOTHING, AND THAT IS THE RECORD

`KX6ZYSo8apo` (*"Perfect Switch & Socket Placement for Every Room"*) was picked to close the
setting-out-heights half of the switch-plate row. It returned **no English captions**, and
its extracted frames are title cards and blank transitions — `frame_0011` is a stylised
title, `frame_0090` is blank white. **No usable content was obtained.**

It stays in the ledger as `watched` pointing at this section, so that:

1. nobody re-picks it expecting numbers, and
2. the switch-plate row keeps its honest status — **placement heights are still unsourced**,
   and the plate's own face geometry was already recorded as VG-07 (supplier catalogue).

A pick that returns nothing is a result. Two of the last nine picks have now failed on
verification-by-watching (`2stNv09sbe8`, `KX6ZYSo8apo`), which is a **22 % miss rate for
title-and-channel judging** — worth knowing before trusting any unwatched row in the
curriculum.

---

## 6. WHAT IS OWED FROM THIS UNIT

1. **Measure our frame as a luminance HIERARCHY**, not as an amount: the ratio between the
   brightest intended surface and the wall background, and whether there are graded steps
   between. A 10:1 workplace target is not our target, but a ~1.2:1 frame fails any version
   of it.
2. **P2r-29(b) becomes a millwork row**: dado of the extrusion's section, channel +
   diffuser, inset 25 mm each end, clearance ~3-5 mm, diffuser flush.
3. **Shelf spans**: front rail or intermediate support beyond ~1500 mm — the same threshold
   already recorded for the hang rail.
4. Switch/socket **setting-out heights remain unsourced**; do not treat the row as covered.
