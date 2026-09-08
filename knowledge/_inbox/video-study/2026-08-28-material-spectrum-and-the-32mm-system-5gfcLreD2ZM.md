# A material palette is a SPECTRUM, and the shelf-pin grid finally has numbers

**Sources (REFERENCE tier).**

1. `5gfcLreD2ZM` — <https://www.youtube.com/watch?v=5gfcLreD2ZM> · Noah Daniel, *"material
   palettes for interiors & how to get them right"* · 18 min 53 s → **G7, and the
   wood-dominant palette question.**
2. `EO62T1LHdNA` — <https://www.youtube.com/watch?v=EO62T1LHdNA> · Bent's Woodworking,
   *"Festool LR 32 — Intro"* · 26 min 25 s → **the 32 mm system, a named BUILD gap.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py` (30 frames each); transcripts via
`youtube-transcript-api`. Timestamps verbatim.
**Disclosure:** `5gfcLreD2ZM` carries a sponsor read for a supplement brand at `[03:06]`;
the design content is unaffected but the unit is a sponsored video.

---

## 1. THE SPECTRUM — a way to reason about a wood-dominant room

`[04:36]` *"I think the **key to a successful material palette is to focus on CONTRAST**, and
to think about your materials **on a spectrum**."*

The spectrum he uses, `[05:23]`-`[06:54]`, running from soft/natural to harsh/manmade:

**woven textiles · wood → brick · natural stone · textured ceramics · leather · some
concrete → linoleum · painted elements · fibreglass · acrylic · laminate → glass · glossy
tiles → METALS**

He renames it mid-explanation, and the correction is the useful part `[06:54]`: *"maybe a
better word for it is like **sharper** or like **harsher**… we can all agree that **metal
feels harsher than fabric**."*

And the qualifier that stops it being a lookup table `[07:39]`:
> *"there isn't a strict place on this spectrum for each material — **a highly reflective
> polished marble floor is going to feel way harsher than a more raw matte limestone floor
> tile**. So it's not as simple as saying stone is in one place."*

**Position on the spectrum is set by FINISH, not by material class.** That is directly
relevant to a room whose 60 % is wood: a satin oak and a high-gloss lacquered oak are not the
same entry.

### 1.1 THE RECIPE, AND OUR ROOM ALREADY HAS THE INGREDIENT
`[07:39]` *"the tried and true easiest way of doing this is to bring in some nice **wood
furniture with some fabric upholstery**, and then **sort of CUT IT with a much harsher
material** — like a metallic table for example — because when you bring in materials from
the **further ends of that spectrum** you get this interesting **tension and contrast** that
just makes a space feel **more deep** and ultimately more balanced."*

> Our room is wood floor + wood wall + fabric — precisely the soft end he describes — and it
> **does** contain a metal: the brass hang rail. So the ingredient exists. The open question
> is whether it READS at the frame's scale, or whether it is 3 px of brass behind a garment.
> That is measurable from the matmask and has never been asked as a palette question.
>
> It also reframes the measured 0.300 distance from the declared 60/30/10: the failure may
> not be that the proportions are wrong, but that **all three tiers sit at the same end of
> the spectrum**, which no ratio can fix.

### 1.2 THE HOUSE RULE HE STATES FIRST
`[01:36]` *"we do have one very strict rule on my channel and that is **honest materials,
authentic materials** — meaning **no vinyl flooring that's meant to look like hardwood**, no
tile that's printed to look like marble, or… **plastic faux plants**. Nothing fake, nothing
faux… **there are no bad materials as long as they are authentic.**"*

For a renderer this reads oddly — everything we make is faux by definition. But the
transferable half is real: **a material should be doing what that material does**, and a
surface pretending to be a different material is a defect the eye catches. It is the same law
SouthernShotty states from the 3D side (*"your model needs to represent fabric in its
topology"*) and the veneer trade states from the joinery side.

---

## 2. THE 32 mm SYSTEM — the shelf-pin geometry, complete

The BUILD gap judge wrote: *"NO SHELF-PIN / 32 mm SYSTEM SOURCE: no line-boring pitch, pin
type, or shelf thickness vs span sag."* This closes the first two.

| Quantity | Value | Verbatim |
|---|---|---|
| **hole pitch** | **32 mm** | `[09:11]` *"those holes are spaced **32 millimetres** apart"* |
| **hole diameter** | **5 mm** | `[11:14]` *"each one of these holes… those are all **five millimetre holes**, meaning they will accept these **five millimetre euro style screws**"* |
| **setback, front** | **37 mm** | `[09:43]` *"so it's going to be **37 millimetres from the front edge**"* |
| **setback, back** | **37 mm from the back-panel groove** | `[09:43]` *"and 37 millimetres from the front edge of the **panel groove**"* |
| **panel height** | an exact multiple of 32 | `[06:09]` *"this is **672 millimetres** from the bottom to the top… because it is an **exact multiple of 32**"* |

### 2.1 WHY 37, AND WHY IT MATTERS THAT IT IS THE SAME BOTH SIDES
`[09:43]` *"I don't want to put my shelf pin holes the same distance from this back edge in
as I do the front edge in — **I want them to be the same distance from the back PANEL in and
the front edge in**… **that way it gives a balanced look.** My shelf pin holes are going to
be here, there's going to be a panel, my shelf pin holes are going to be here, so it's going
to be the **same distance when you're looking at it**, and **it just looks better**."*

The 37 itself is a compromise with drawer hardware `[11:14]`: *"just about every set of
drawer slides… has a **centre line hole location of 35 millimetres**… the reason I'm going to
use 37 is because not only is it going to work for my shelf pin holes, but it'll also
**universally work for my drawer slides**, because you're never going to make them perfectly
flush with the front of the cabinet — they always talk about backing it off about a
sixteenth of an inch."*

### 2.2 THE BALANCED PANEL
`[06:09]` a panel sized to an exact multiple of 32 is called **balanced**, and the reason is
that *"it is going to fall exactly in the same location **no matter what direction I have the
board** or what direction I have the rail"* — the hole pattern is symmetric end to end, so
the panel cannot be installed upside down wrongly.

Hinge plates for frameless hinges sit on the **same 32 mm grid at the same setback**
`[09:11]`, which is why the whole system is one grid.

> **For our casework this is a complete, buildable, testable specification**, and it is
> visible: a real cabinet side shows **two columns of 5 mm holes at 32 mm pitch, 37 mm in
> from front and from the back panel**. Our cells have shelves that rest on nothing. It also
> gives the *balanced look* rule (§2.1) — the two columns equidistant from their own edges —
> which is the same family as the veneer trade's **balance match** (no skinny stripe at
> either end) recorded from `btuu8Bf8B30`. Joiners keep saying the same thing: **the
> spacing at the two ends must match, and it is judged by eye.**

---

## 3. WHAT IS OWED FROM THIS UNIT

1. **Ask the palette question as a spectrum question, not a ratio question** (§1.1): does our
   room contain anything at the harsh end that actually READS at frame scale? Measure the
   brass's pixel share before adjusting any 60/30/10 number.
2. **Record that spectrum position depends on FINISH** — satin vs gloss on the same wood are
   different palette entries.
3. **Build the 32 mm hole grid** into the wardrobe carcass: 5 mm holes, 32 mm pitch, 37 mm
   from the front edge and from the back panel groove, panel heights on the 32 multiple.
   Shelves then rest on pins that exist.
4. **Adopt the balanced-look rule** (equal setback at both ends), which is now stated by two
   separate trades about two different things.
