# Three trade details for three filed cannot-be-built defects

**Sources (REFERENCE tier), watched together because each answers one open P2 row.**

1. `iJYto0muSd4` — <https://www.youtube.com/watch?v=iJYto0muSd4> · The Honest Carpenter
   (Ethan James), *"Wooden Closet Rods Are TERRIBLE! Try This Better Alternative… (Metal
   Clothing Rod Install Tips)"* · 5 min 18 s → **P2r-28, the hang rail.**
2. `saFsrHObKyk` — <https://www.youtube.com/watch?v=saFsrHObKyk> · Blindspace Concealing
   Blinds, *"How to Install Recessed Curtain Tracks in TrackTrim"* · 2 min 22 s →
   **P2r-29, the curtain half.**
3. `t3F0dwsBFjw` — <https://www.youtube.com/watch?v=t3F0dwsBFjw> · The Honest Carpenter
   with Harrison Peacock (CCS Triangle Electric), *"LED Recessed Lighting — 5 THINGS TO
   KNOW!!"* · 5 min 30 s → **P2r-19, the twelve downlights.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py` (28 frames each); transcripts via
`youtube-transcript-api`. Timestamps verbatim. All three are US trade practice — the
DIMENSIONS below are US-market products and must be checked against a Thai supplier before
any of them becomes a spec value (VG-04 / VG-05 / VG-07 in `qa/video-curriculum.json`).
What transfers without qualification is the **assembly**: which parts exist and what
carries what.

---

## 1. THE HANG RAIL — the span rule the BUILD judge said no candidate supplied

`[00:30]` *"metal closet rods… tend to come in the same thicknesses, **one and a quarter
inches to one and a half inches**, in the same lengths, **four feet to eight feet**. They
usually have **chrome, white or black** finishes."* → **Ø 31.75 – 38.1 mm**, lengths
1219 – 2438 mm.

`[00:59]` *"metal rods tend to be **hollow tubes with a thick rigid wall**. The tube shape
itself is naturally very strong — **it functions like an arch in architecture.** This means
that an elongated tube has very little willingness to bend across a span… they're more
than capable of carrying **70 to 90 pounds across a six-foot span**."* → **31.8 – 40.8 kg
over 1829 mm.**

### 1.1 THE NUMBER THAT WAS MISSING
`[04:13]` *"**spans over five or six feet may require an intermediate support**, but these
can usually be mounted to a trim plate on the **back wall** in a very similar fashion."*

**A centre support becomes necessary somewhere between 1524 and 1829 mm**, and it is
carried on the BACK wall, not the sides. The BUILD judge's lane_gap said in as many words
that no candidate in 47 rows stated a centre-support rule for spans over ~1000 mm. This
one does.

### 1.2 THE END CONDITION, AND WHY OUR 40 mm INSET IS THE DEFECT
`[02:51]` *"nearly all of these rods install with a **cup bracket system on the side
walls**. The ends of the rods just **sit in the lips of these little cups**, and these cups
will typically be installed on **trim plates** on the side walls."*
`[03:18]` *"measure your span from wall to wall… you're looking for a **surface to surface**
reading. I go with a measurement about **a sixteenth shy of the total opening**."*
`[04:13]` one cup closed, the other **open side up**, so the rod drops in.

> **A trade rod is cut ~1.6 mm short of its opening and lands in a cup on each side wall.
> Ours stops 40 mm short of BOTH gables** (millwork's own `l0+0.04 / lw-0.08` inset) —
> about **25× the trade allowance** — in nine cells, on every frame this lane has produced.
> C2 filed it by eye at p2r84 as *"ราวตัดจบกลางอากาศ"*. The inset exists to avoid coincident
> faces; the trade answer is not a smaller inset, it is that **the gap is filled by a
> part** — a cup bracket on a trim plate. p2r87b's socket flange is the right shape; this
> is the outside citation it did not have.

`[01:27]` also names the failure mode we should expect to see if a rail is under-supported:
wooden rods *"start **sagging** very early on if they're under supported — I can't count the
number of times I've seen this in houses."*

### 1.3 AND THE ROUND SECTION IS STRUCTURAL, NOT DECORATIVE
The tube *"functions like an arch"* `[00:59]`. `millwork.py`'s own comment admitted
*"round rail modelled square"* and p2r87b made it round. This is why that mattered beyond
appearance.

### 1.4 TWO PLACEMENT RULES FOR THE BRACKET
`[04:13]` *"position the closed bracket where you want the rod to sit — **far enough out
that clothes won't rub against the back wall**, and **far enough below a shelf that you can
hook the hangers in easily.**"*

Two clearances our spec has never stated: rod-to-back-panel, and rod-to-shelf-above.

---

## 2. THE CURTAIN TRACK — the member our curtains do not have

Our curtain tops vanish into the ceiling slab with no pocket and no track. All three
critics filed it by eye; `carry_check` cannot see it because it reads the condition as
FIXED-IN. This video is the assembly, from a manufacturer:

- The track is **recessed inside a "Track Trim" profile** set into the ceiling. `[00:56]`
  *"we provide specific fixing brackets for different curtain track systems, **making them
  flush with the ceiling independent of the height of the curtain track**."*
- `[00:00]` *"the first step is to prepare the curtain track by **drilling holes from the
  back of the track** where you want the fixing points."* The on-screen detail in
  `frame_0004` dimensions that hole as **Ø 10 mm**, with a profile cross-section marked
  correct/incorrect.
- `[00:27]` **the load rule, and it is the one that matters for us:** *"we recommend that
  you put an **extra fixing point where you will have the curtain stack**, as that's usually
  the section that will take the most load."*
- `[00:56]` two profile types: one with a **screw channel that centres the track**, one
  with none where you fix through the back of the profile; a **centraliser** for flat track.
- `[01:51]` a **track protector** while driving the fixing screws.

> **The assembly is: ceiling profile (a box with a slot) → fixing bracket → track → gliders
> → heading.** That is R8's BUILD class end to end — extrusions and boxes with radii,
> nothing free-form — so the curtain-pocket half of P2r-29 is a millwork job, not an
> unresolved gap. What is still missing is the **stack-back width** that decides how far
> past the reveal the pocket must run, and that is a track-maker's table, not a video
> (VG-08).

---

## 3. THE TWELVE DOWNLIGHTS — the measurement that convicts 60 mm

`[03:42]` *"thanks to newer LED technologies, **ultra thin recessed lights** can now go
virtually anywhere. These units are **only as thick as the drywall they mount into**, which
means they can be positioned directly beneath framing obstructions, and because they're so
lightweight they **hold themselves in place just by means of spring-loaded clips**."*

> **A recessed fixture is flush.** The thin class is the thickness of the board it sits in
> — on the order of 12.5 mm, and that is the *housing*, not a protrusion. Our twelve
> downlights hang **60 mm below the ceiling they are recessed into**, which is not a
> shallow recessed can, a deep one, or a surface-mounted fixture. It is a fixture class
> that does not exist. P2r-19 is filed as `fix` with a named action; this is the outside
> reference for what the fixed state looks like.

### 3.1 SPACING, with two numbers
`[02:19]` *"Harrison doesn't like to have lights **more than four feet away from each
other** on a linear path — even with larger six-inch lights, the overlapping cones of
illumination may fail to reach effectively beyond this distance. He also prefers a
**minimum spacing of two feet between walls and recessed lights.**"*

→ **pitch ≤ 1219 mm; standoff from a wall ≥ 610 mm.**

And the reason for the wall standoff is a named visual defect `[02:47]`: *"this distance
produces better **wall washing**… going closer than this can result in **wall grazing**, or
sharp light that **picks out contours and defects** and fails to maximize broad
illumination."* Two lighting behaviours with a distance threshold between them — directly
usable in the lighting solve, and directly relevant to a room whose walls are boards.

`[02:47]` also: *"projections and obstructions should be taken into consideration — open
top cabinets… can encroach on downlights, so cans should be **positioned relative to
cabinet fronts** to avoid interference."* Our full-height wardrobe wall is exactly such an
obstruction and the downlight array has never been positioned relative to it.

### 3.2 COLOUR TEMPERATURE — a second independent 3000 K, and a warning aimed at our room
`[00:31]` *"the **3000 Kelvin** range will give you that yellowish light similar to
incandescents, which is **best for bedrooms, living rooms**, comfortable places where you
want to relax."* 4000-5000 K for bathrooms, kitchens and work areas.

This is the second independent source in this curriculum giving 3000 K for living spaces
(the first is Nuno Silva, `UmJaVnO3Sxw` `[24:23]`).

**And then the warning, which is about a room like ours:** `[00:59]` *"light in the low
yellowish or high bluish range can **interact adversely with the color of your walls**.
Harrison had recalled one instance where a homeowner had used 3000K bulbs in a bedroom with
**brown walls** — that yellowish light **turned those walls pink**. CCS Electric switched
those fixtures to the higher **4000K** bulbs, and the wider light once again brought out the
brown paint colors in the room."*

> Our room is **wood-dominant — a brown room** — and its palette is already measured 0.300
> away from its declared 60/30/10. A warm source pushing brown toward pink is a specific,
> named, testable interaction, and it means **3000 K is not automatically the right answer
> here**: it is the right answer for a bedroom in general and possibly the wrong one for a
> bedroom whose dominant surface is brown. That is a question for the lighting solve, and
> it is exactly the kind of coupled failure that a value-ladder measurement alone cannot
> see.

`[01:26]` also: LED cans *"should typically be installed on **dimmer switches**"*, and LEDs
need a **CL dimmer** rather than a generic one — a switch-plate detail for the SENSE list.

---

## 4. WHAT IS OWED FROM THIS UNIT

1. **P2r-28**: cite the cup-bracket-on-trim-plate end condition and the ~1.6 mm cut
   allowance against our 40 mm inset; add the **1524-1829 mm centre-support threshold** as
   a rule `carry_check` can apply to any rail.
2. **P2r-29 curtain half**: build the ceiling profile + bracket + track as millwork, and
   carry the extra fixing point at the stack. Row VG-08 (stack-back width) as the
   remaining unknown.
3. **P2r-19**: a recessed fixture is flush; the thin class is board-thickness. Row the
   60 mm protrusion against that, plus pitch ≤ 1219 mm and wall standoff ≥ 610 mm, plus
   position relative to the wardrobe front.
4. **Lighting solve**: 3000 K as the bedroom default from two independent sources, WITH
   the brown-goes-pink caveat as an explicit check on our wood-dominant palette.
5. Two rail clearances our spec has never stated: rod-to-back-panel and rod-to-shelf.
