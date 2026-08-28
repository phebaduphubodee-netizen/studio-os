# A door's margin, the arithmetic behind a lighting rig, and how a rug pile is actually built

**Sources (REFERENCE tier), three unrelated trades, each closing one open item.**

1. `KQZKc8PLV2A` — <https://www.youtube.com/watch?v=KQZKc8PLV2A> · Skill Builder, *"How To
   Fit Door Trims, Architraves & Skirting Boards"* · 20 min 41 s → **P2r-29(c): our room has
   no door and no skirting.**
2. `EBFzvBbFeaM` — <https://www.youtube.com/watch?v=EBFzvBbFeaM> · Sparky Help, *"Lighting
   Calculations — Inverse Square, Cosine, Efficacy"* · 19 min 46 s → **the arithmetic that
   lets a lighting rig be DERIVED rather than tuned.**
3. `qXKERWIATjw` — <https://www.youtube.com/watch?v=qXKERWIATjw> · iMeshh, *"Creating the
   perfect rug in 20 mins — Blender 4.2"* · 24 min 02 s → **the rug, ORD-2026-08-25b.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py`; transcripts via
`youtube-transcript-api`. Timestamps verbatim.

---

## 1. THE DOOR — order of work, and one visible number

`[00:04]` *"**architrave always first**, and then we'll come away with the skirting board"* —
and the reason at `[06:20]`: *"the architrave always comes first because **you want to come
away from the architrave**."* Skirting dies into the architrave, never the reverse.

### 1.1 THE MARGIN — the number that makes a door read as a real door
`[00:53]` *"when I first did my apprenticeship it was **no more than six millimetres, the
margin** that you leave there. Now that's since changed, because now we tend to use a lot of
**ball-race hinges**, and the knuckle of a ball-race hinge is a little bit bigger — so even
with a **75 mm** ball-race hinge you need to allow a little bit more, otherwise when you chop
in those parts… it **interferes with the edge of the architrave**… So what we tend to do now
is to leave **at least nine, ten millimetres**."*

> **The MARGIN is the reveal between the door-lining edge and the inner edge of the
> architrave: historically 6 mm, now 9-10 mm because of hinge knuckles and latch plates.**
> It is a visible line that runs the whole way round a door opening, and it is the kind of
> detail that separates a modelled door from a door-shaped box. The same allowance is what
> the latch/handle plate needs.

### 1.2 THE MATERIAL AND ITS CONSEQUENCE
`[00:04]` *"I'm using a typical **MDF architrave** — this is basically what everyone's using
now… **cost**, and also **it doesn't shrink**, and it comes in **pre-primed**, so it's a
fairly good product, it's quite reliable, and it **paints really nicely**."*

Its drawback drives the joint: at **13-14 mm thick** a pin through the top edge splits it
*"straight through the fibres"*, so the corners are made *"**like a picture frame** using a
mitre-type adhesive"* — mitred and glued, not pinned. Fixing to the lining uses **30-40 mm
pins**.

Skirting is measured per piece with a couple of inches added, cut to a pile, then **scribed**
with a coping saw, and it is run **around boxings** (e.g. a boxed-in pipe) rather than
stopping at them.

---

## 2. THE ARITHMETIC — a rig that can be derived instead of tuned

| Law | Formula | Meaning |
|---|---|---|
| **inverse square** | **E = I / d²** | E = illuminance at the surface (**lux**, lm/m²); I = luminous intensity (**candela**); d = distance (**m**) |
| **cosine** | **E = (I / d²) · cos θ** | for a point NOT directly below: **d is the diagonal** (hypotenuse), and cos θ = adjacent / hypotenuse = mounting height / diagonal |

`[00:55]` the plain statement of the law: *"**every time you double the distance, the light
received at the surface drops by a quarter**."*

Worked examples given on camera:
- 1000 cd at **2.4 m** directly below → **173.6 lux**.
- 1500 cd at 2.4 m high and 1.8 m across → diagonal 3.0 m by Pythagoras, cos θ = 2.4/3 =
  **0.8**, so E = 1500/3² × 0.8 = **133.3 lux**.
- And the part that matters for a grid `[05:20]`: a point is lit by the fixture above it AND
  **by every other fixture at its own angle**, and the contributions **add** — directly
  below a 1500 cd fixture at 2.4 m gives **260.4 lux**, *"however it's also lit from the
  diagonal."*

> **This is how a downlight layout is checked without rendering it.** Given a fixture's
> candela (or its lumens and beam angle) and the mounting height, the lux at any floor point
> is arithmetic, and the sum over the array is the uniformity the grid was supposed to
> deliver. Our twelve-fixture grid has never been evaluated this way — and the same
> arithmetic tells you what a WALL receives, which is the input to the luminance-ratio
> structure recorded from the workplace source.
>
> It also converts a lighting change from "turn a knob and re-render" into "solve, then
> render" — which is R5's law (a cheap rung before the expensive one) applied to light.

---

## 3. THE RUG IS HAIR, AND THAT IS WHY OURS READS FLAT

The method is Blender's curve-based hair system, and the workflow is guide-driven:

- `[03:30]` **guide hairs** are added with the Add brush, then a **comb** brush aims them:
  *"this is basically **telling all the other hairs what it should be doing**… each one
  basically has an **area in which it affects the fur around it**."*
- `[06:29] `The pile is NOT fur length: *"set it to **02** because this is not going to be
  fur, that's too long"* — **~0.02 m = 20 mm pile** — and *"set the **count to 50**, then
  simply brush over the surface so there's a nice even amount throughout."*
- Modifiers stacked on top: **frizz** and **noise** (both demonstrated toggling on and off,
  *"if I turn off the frizz it looks less frizzy, if I turn off the noise it looks less
  noisy"*), plus `[09:50]` *"make sure we turn on **preserve length**, so that all the length
  stays the same"* when deforming.
- Viewport density is reduced for working and raised for render.

> **Our rug is a surface with a material.** A real one is a **20 mm field of hair on a
> backing**, and that single fact explains the two things critics keep filing: the pile has
> real thickness so the **edge rolls over** instead of stepping, and the pile catches light
> per-strand instead of as a flat plane. It is also the same technique family as the fabric
> **fuzz** already recorded from `3SiZCxaNM28` — **one mechanism answers the rug and the
> boucle at once.**
>
> Cost note the source states plainly at `[00:00]`: an asset library exists because *"clients
> do not pay you to make all the individual assets — time is money"*, but *"there will be a
> time where a client says I want this specific chair and that chair just won't exist
> online, so you'll have to make it yourself."* That is R8's build-or-acquire fork stated by
> a vendor of the acquire side.

---

## 4. WHAT IS OWED FROM THIS UNIT

1. **Give the room a door**, with a **9-10 mm margin** around the lining, architrave mitred
   at the corners, and **skirting that dies into the architrave** and runs around any boxing.
2. **Solve the downlight array arithmetically** (§2) before the next lighting round: lux at
   the floor and at the wall from candela, height and angle, summed over the array. Then
   compare against the luminance-ratio structure rather than adjusting exposure.
3. **Rebuild the rug as a hair field**: ~20 mm pile, guide hairs combed, frizz + noise,
   preserve length. One mechanism also fixes the boucle fuzz.
