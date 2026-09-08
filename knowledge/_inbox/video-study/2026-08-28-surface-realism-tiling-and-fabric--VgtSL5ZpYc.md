# Surface realism: four ways to kill texture tiling, and five to make cloth read as cloth

**Sources (REFERENCE tier), watched together because they are the two halves of our P2
surface problem.**

1. `-VgtSL5ZpYc` — <https://www.youtube.com/watch?v=-VgtSL5ZpYc> · Blender Guru (Andrew
   Price), *"How to Tile a Texture Without Repetition — Blender Tutorial"* · 22 min 24 s →
   **P2r-2, the wood wall that repeats and mirrors.**
2. `3SiZCxaNM28` — <https://www.youtube.com/watch?v=3SiZCxaNM28> · SouthernShotty, *"Why
   your Fabric material looks fake in Blender 3D"* · 4 min 06 s → **the cloth half of the
   P2 exit clause.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py` (30 frames each); transcripts via
`youtube-transcript-api`. Timestamps verbatim.

---

## 1. THE TILING THRESHOLD, stated as a number

`[00:47]` *"if you tile anything **10 plus times** your eye will always notice distinct
repeating patterns and shapes throughout it."*

And the trap our lane would otherwise walk into, refuted before we try it `[01:34]`:
*"one solution that a lot of people think would work is to **capture a larger surface**…
this usually doesn't solve the problem, because in order to see any of that detail you need
a larger image texture… if you go from a 1k texture to an 8k texture you're usually using
**53 times the amount of memory**… and also you can't really get the camera in very close
anyway."*

`[00:47]` also states what the goal is NOT: *"there are very few surfaces in the real world
other than maybe like fine sand which is totally uniform… everything else will always have
some distinction **which you want to keep**, because the real world has irregularities."*
The target is not a uniform surface; it is an irregular one whose irregularities do not
repeat.

---

## 2. THE FOUR TECHNIQUES

### 2.1 TILE ROTATION — and it is the one nobody has
`[02:22]` *"one of the big reasons why this looks so noticeably tiled is because it's
laying out texture in a **grid fashion side by side** and those patterns are obvious. **If
each of those tiles were to be rotated independently at random amounts** that would fix
that problem for us. Unfortunately almost no 3D software as far as I know gives you this
tool out of the box, Blender included, so you would need to know a bunch of vector math in
order to figure that out — **which is why nobody does it.**"*

The technique is called **mosaic rotation**; each tile is rotated independently. It
introduces hard seams (a seamless texture is only seamless in a grid), and the second
control, **mosaic noise**, converts those straight seams into squiggly ones `[05:33]`:
*"instead of it being hard lines it's now just created squiggly lines, which just makes it
a little bit harder for your eye to detect a hard seam."*

**Stated limitation** `[05:33]`: *"it's not going to work for like brick tile and other
fixed patterns."*

> **This is the technique our wood wall needs and the one it certainly does not have.** Our
> defect is not merely a repeat: C2 filed *"a visible mirror axis mid-wall, the same block
> repeated left and right"* — a MIRROR, which is the grid's most visible form. It also
> rhymes exactly with Nuno Silva's fix for a repeated 3D asset (`UmJaVnO3Sxw` `[13:01]`:
> *"at least try to rotate the asset… scale it, rotate it"*). **Two independent
> professionals, one texture and one geometry, giving the same instruction: break the
> grid per instance.**
>
> Caveat for our case: a wood wall of BOARDS is closer to "brick tile and other fixed
> patterns" than to grass, so free rotation is wrong — the transferable form is
> **per-board offset, flip and hue jitter along the board's own axis**, which is what the
> veneer trade calls slip-matching rather than book-matching. That connects this unit to
> the veneer-matching row in the same harvest.

### 2.2 COLOUR VARIATION, at two scales
`[06:20]` *"in the real world every single surface has slight variations to the **hue,
saturation and value** of a colour… it adds so much to the realism and breaks up surfaces.
**There's no excuse for not doing it.**"*

Mechanism: a hue/saturation node with a **noise texture plugged into the factor** as a mask
`[07:09]`. His working pattern `[08:44]`: *"I add in like one for the **big large scale
shapes** and then I duplicate it and this one becomes the **small scale shapes**"* — a
second copy at higher scale producing *"almost like a flick, like a little splatter of a
few little dark spots."* Dark-spot and bright-spot thresholds are separate controls.

### 2.3 BLEND A SECOND MATERIAL IN
`[09:31]` *"over a large enough surface **no material is continuous**… even sports fields
aren't a continuous grass texture forever."*

And the version that applies to a wood wall `[16:40]`: *"a little trick — I use dirt here to
make the dirt patches, but you can also do the exact same thing by just taking **a material
which is similar to your existing one**. So if you've got one grass texture and then you
blend it with **another grass texture**, that's a good way of keeping the same material…
but using this same effect it's going to look far less repetitive."*

**The failure mode of this technique is named too**, and it is the one our lane would hit
`[15:53]`: *"a really key thing, if you find yours just looks awful, is to make sure that
your materials **blend — like they have the same VALUES**. I typically find that's usually
a big key factor in why something doesn't look right."* Two textures pulled off the
internet *"are probably not going to work together out of the box."*

### 2.4 HEIGHT VARIATION — displace the actual geometry
`[17:27]` *"the fourth and final technique is **height variation** — adding waviness to your
actual surface, to displace the actual geometry of it. That sounds painfully obvious but
it's **very easy to overlook**, and it actually adds a lot to the believability."*

Method `[18:14]`: subsurf modifier set to **simple** (so corners are not rounded off) with
**adaptive subdivision** — *"so that parts that are closer to the camera have more geometry
added"* — then a displacement modifier driven by a noise texture, with the material's
displacement setting changed from **Bump Only to Displacement and Bump**.

And the same masks can drive it `[19:48]`: *"dirt would be lower than grass, so if I can
make that dig into the surface then that would help me out"* — mix the material blend mask
into the height so the two materials sit at different heights rather than only different
colours.

His closing justification `[19:48]`: *"**the world is just naturally wavy**, man, and you
gotta try and replicate that."*

---

## 3. WHY CLOTH READS AS PLASTIC — five tips, and one general law

### 3.1 THE GENERAL LAW, which is bigger than fabric
`3SiZCxaNM28` `[01:19]` *"**your model needs to represent fabric in its topology.** If we
just toss a fabric material on a sphere, we know that's a fabric material — but if we add
some **cloth wrinkles**, or maybe some **indents**, you can see how it begins to read much
more realistically as fabric… **unless you're going for an abstract look, you're going to
want that object's topology and shape to match the material that it is holding.**"*

> A material cannot rescue a shape that does not belong to it. This is the same law R8
> states from the other direction (a class that cannot be built from measurable numbers
> must be acquired), and it is the reason our cloth work has always been a geometry
> problem wearing a shader's clothes.

### 3.2 FUZZ IS THE BIGGEST ONE
`[00:00]` *"tip number one and **the biggest tip in my opinion is add fuzz**."* Method
`[00:27]`: a particle system with a **vertex group controlling density** so fuzz appears
only where wanted; **simple children**; **kink set to curl or spiral**; **length way down**;
particle count up; *"then add a **hair node** that you can use to make it so the **light
passes through the fuzz**, giving it a more realistic look."* The newer curve-based hair
system is the higher-control alternative.

**Our fabrics carry a procedural weave and sheen and no fuzz at all.** For a boucle in
particular — the preset is literally named `fabric_boucle` — fuzz is not a refinement, it
is the defining feature of the material.

### 3.3 THE OTHER THREE
- **Colour** `[00:52]`: *"a lot of beginners just using **flat washes of colour**… when you
  zoom in on fabric you'll see that there are a lot of little **micro segments of colours**,
  and oftentimes they're interweaving and blending different colours to create a richer
  colour."* The same law as §2.2, at thread scale.
- **Stitches** `[02:40]`: adding stitching, painted or from a brush/geometry-nodes asset.
- **Sheen** `[03:08]`: *"by turning the sheen up **just a little bit on ALL of my fabric
  materials**, it will help kind of catch the light and give a more natural falloff across
  the fabric. **It's not technically physically accurate**, however… it reads better as
  fabric in the final render."*

  Worth noting against our own history: `material_presets` already applies sheen 0.8 on
  `_woven`, so this rung is met — and it is the only one of the five that is.

- Tools he names for adding the wrinkles §3.1 requires `[02:12]`: **scrape and indent
  sculpt brushes around seams**, and *"the amazing **cloth sim brush** for adding
  wrinkles"* — brush-driven, not a full simulation. That is directly relevant to a lane
  that once hand-wrote 785 lines of cloth physics.

---

## 4. WHAT IS OWED FROM THIS UNIT

1. **P2r-2**: per-instance break-up on the wood wall — offset/flip/hue jitter per board
   (the slip-match form of §2.1), colour variation at two scales (§2.2), a second wood
   material blended in at matched VALUE (§2.3), and height variation (§2.4). Four
   independent levers where the lane has been treating this as one texture problem.
2. Record the **10× tiling threshold** and the **1k→8k = 53× memory** refutation so nobody
   proposes a bigger texture as the fix.
3. **Fuzz on every fabric**, starting with the boucle, via particle hair with a density
   vertex group and a hair shader (§3.2). This is the largest un-pulled lever on our cloth.
4. Adopt §3.1 as a general rule beside R8: **the shape must belong to the material**, and a
   material assigned to a shape that could not hold it will read fake no matter how good
   the material is.
5. Wrinkles via **sculpt brushes / the cloth brush**, not simulation, where a shape needs
   fold structure (R8b's "do not hand-write what Blender already generates").
