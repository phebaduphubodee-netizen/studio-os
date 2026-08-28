# "Where does your eye go?" — one question applied to nine renders in a row

**Sources (REFERENCE tier).**

1. `vXVLTBvLCbo` — <https://www.youtube.com/watch?v=vXVLTBvLCbo> · Andy Christoforou
   (ArchViz Academy), *"I Reviewed YOUR Renders, Here's What Everyone's Getting Wrong"* ·
   19 min 34 s → **G3.** Strong.
2. `2stNv09sbe8` — <https://www.youtube.com/watch?v=2stNv09sbe8> · iPad For Architects,
   *"Step-By-Step Critique Of An Interior Rendering By My UCLA Student"* · 36 min 12 s →
   **weaker than it was picked for; recorded honestly in §5.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py` (36 frames each); transcripts via
`youtube-transcript-api`. Timestamps verbatim.

---

## 1. THE QUESTION HE ASKS EVERY SINGLE TIME

`[00:37]` *"one thing to always think about when you're doing archviz and you export the
image is **where does your eye go?** Right? Archviz is all about **storytelling and
focus.**"*

He then asks it again at `[02:29]`, `[05:00]`, `[17:14]` — once per submission — and in
every case **the answer is not the subject**:

- `[00:37]` *"my eye goes here because of all the **white** on this bookshelf… the problem
  with that is it's a little too bright, a little bit too intense."*
- `[02:29]` *"it either goes to light **or it goes to weird details.** I actually noticed
  there's like this **crazy open flame.** Not sure why that's there."*
- `[07:31]` *"the **saturation** is like way out of whack… **instead of me looking at your
  building** because it's all grey and in shade, **I actually go to this bright green bush**
  or this bright orange elephant."*
- `[08:10]` *"specularity, intensity of the glass — this is just like bright white… my eye
  is kind of **ping-ponging** between here and then here and then here."*
- `[17:14]` *"because of the kind of monochromatic design here… **my eye actually goes out
  here**, and there's like nothing really interesting out there except a bunch of fog…
  I've completely forgotten about **this**, because my eyes just go outside."*

> **This is a builder-runnable rung and we do not have it.** Ask of our own frame: what is
> the brightest thing, what is the most saturated thing, and are they the subject? Both are
> answerable from the render with `id_mask` and a luminance/saturation read — the difference
> is that nobody has ever asked the question. It is the same law John Cullen states from the
> lighting side (*"the eye is naturally drawn to the brightest point… decide what NOT to
> light"*), arriving here as an image test rather than a design intent.

---

## 2. SHADOW DIRECTS THE EYE, AND IT HAS A RULE OF THUMB

`[05:38]` *"**you never want the shadows pointing towards you**… you can use the shadows as
a way to **direct the viewer's eye**. So if the shadows are actually going this way, it
would let me focus a little bit on the project — because right now **the whole project is in
shade**, and it's like, well, that's not exciting."*

`[06:16]` *"**make sure your project is in light.** That's like rule of thumb: **always have
light on your focus.** You know, it's like you go to a museum and they've got all the
paintings on the wall — **there's always a light illuminating that.**"*

The museum analogy is the same one Luke Thomas uses (`aRWwOhjbvfs` `[01:51]`: *"a technique
that you'll see employed in museums and theatres where the light is concealed from view and
focused onto a certain feature, with other areas left in darkness"*). **Two independent
professionals reaching for the same reference.**

---

## 3. THE REPEATED-ASSET LAW — this is now the FOURTH independent source

`[12:40]` *"all these trees — this guy, this guy, this guy, this guy — **they're all placed
at the same scale, rotation.** And I can tell this because it's going to sound crazy: you
see these **stray leaves** here? I can easily pick them out because it just sticks out. You
don't really want that. So just **rotate the tree**, because I feel like it **breaks the
immersion** there."*

`[14:37]` *"watch out for **repetitive assets** — you want to randomise all that."*

`[06:54]` *"I would fix all these plants, I'd **randomise them**… you can randomise the
scale, the size, the location."*

**And then the interior case, which is our wood wall exactly** `[15:52]`:
> *"I'd even play with **changing the material channels**. So pay attention to this material
> right here: **I can see the same grain of wood.** Like make this one and then make this
> two and then just **move them, shift them around, change the scale a little bit** — that
> way it seems a little bit more natural. And **I'd also try and fix this material so we're
> not getting that same tiling everywhere.**"*

Plus a directional one `[11:21]`: *"you could also just revisit the **rotations or the UVs
of some woods**. So like look at that — that looks great. **This one is going the wrong
way.**"*

Running total for "a field of one repeated thing reads fake, and the fix is per-instance
variation": Nuno Silva (`UmJaVnO3Sxw`), Blender Guru (`-VgtSL5ZpYc`), Caroline Winkler on
interiors (`Sz4TC-VJ2PQ`, *"all flat things on the wall — that falls flat"*), and now this.
**Four sources, three disciplines.** It is no longer a tip; it is the law our wood wall is
breaking.

---

## 4. THE CLOSET LINE — and it CONTRADICTS the merchandising lecturer, usefully

`[15:52]`, on a rendered interior he otherwise praises:
> *"I did like how well this was staged. Um, you know, **maybe fill it even more. Like my
> closet's like stuffed with stuff. Like this is valuable real estate — you got to fill this
> up.**"*

Against `1NI4zETSrQs` `[01:28]`, a visual-merchandising lecturer: *"**don't bombard them
with merchandise — keep it simple. They're more likely to buy if there's less
merchandise.**"*

> **Both are right, and the resolution is the answer to the owner's standing verdict.** A
> SHOP is merchandised sparse, because the goal is to sell one item. A HOME closet is
> **full**, because a real person owns a lot of clothes and puts them all in there. If our
> nine open cells are styled to shop density — evenly spaced, one kind of thing, generous
> air around each garment — then they read as a **display**, not as somebody's wardrobe,
> and *"ยังไม่เป็นธรรมชาติ"* is exactly the right words for that.
>
> This is a testable hypothesis with two opposite fixes, and the lane has never distinguished
> them. It should be settled by measuring fill fraction on the anchor pool (VG-01), not by
> choosing which video to believe.

---

## 5. THE SECOND SOURCE WAS WEAKER THAN IT WAS PICKED FOR — recorded, not hidden

The gap judge warned on verification that `2stNv09sbe8` was *"a hand-drawn Procreate
critique"* rather than a photorealistic render review. **That is correct**, confirmed by
watching: it is a UCLA instructor marking up a student's iPad sketch in Procreate, and the
craft is illustration, not rendering. It should not carry weight as a CG-critique source.

What it still gives, honestly:

- The instructor's read is the same read-order: `[00:43]` *"I see **this wall as being a
  little flat**… I want that wall to be **more inviting**, I want the perspective to invite
  me in a little bit more."*
- A construction-consistency error caught purely by eye `[01:26]`: *"there's a very obvious
  thing here where the **venetian blinds aren't parallel**."*
- **Facing directs the viewer** `[01:26]`-`[02:09]`: *"here I'm going to make it so the
  **chair is facing in**… so now in the rendering **I've directed her attention this way**,
  just so that she can feel what it's like to be in that office."* Third source for the
  gaze/facing rule after Arch Viz Artist and the closet facing rule.
- **Depth is built from a stack of small moves** `[03:34]`-`[04:16]`: give objects depth,
  add a frame around the diplomas *"because it is her pride and joy"* (a narrative reason for
  an object), a **drop shadow under the frames**, a drop shadow under the chair, darken the
  wall, and *"we'll pretend that light's coming in the room and the edge of the desk is
  casting a shadow"* — then: *"several of these things that we just did are **all trying to
  address that depth issue**."*
- Let a surface **run out of frame** `[02:51]`: *"I might pull this floor out further, it's a
  little abrupt… I could even see this carpet **coming right out off the page**."*

Its status in the ledger stays `watched` with this caveat attached. **A pick that turned out
weaker is a result, not a failure** — and it is the reason the row carries a note rather than
a link.

---

## 6. THE REST OF THE TAXONOMY (`vXVLTBvLCbo`)

- **Physical plausibility, checked out loud** — the R10 test performed by a reviewer's eye:
  `[03:07]` *"this reads as **concrete**, but if it's concrete, **there's no way you're going
  to install a light like that** — you're going to have a **junction box** and you're going
  to see **exposed conduit** coming out of here, and then this is like a box, and it's a
  whole thing."*; `[04:22]` *"this **countertop isn't actually flush**… putting my architect
  hat on, if I was cooking and my pan handle's hitting that…"*; `[02:29]` the open flame,
  *"that just seems dangerous, right? That's a fire hazard."*
- **"Not done" as a verdict** `[14:37]`: *"the biggest thing kind of hurting me right now is
  it's almost like **it's not done** — like you're in the middle of this… we're missing a lot
  of **context**… everything seems a little bit **too simple, too empty**. Add all that,
  that'll help **ground** your project."*
- **Lived-in is the target** `[01:16]`: *"I like how everything looks **lived in** — like
  that's what we should always strive for."* And the prescription `[03:07]`: *"I feel like up
  here we could use some nice cups, plates, you know, just something to make it look like
  it's lived in. Like we already have this nice little place mat — might as well expand on
  that."*
- **Focal length** `[01:16]`: *"this distortion with the camera — just look at how this chair
  looks, and the leg. **That's when the focal length is like super low, like a 15 or 12**,
  and it just distorts all of it. Not a big fan of that."*
- **Roughness consistency** `[17:53]`: *"the materials look too intense and shiny here, but
  then a little dull here, here and here, but then really intense here… **it'd be nice if
  each of your materials had a little bit of roughness.**"*
- **Decals** `[08:10]`: default opacity 100 % is too strong — *"crank them down so they blend
  in… it just looks like someone spilled milk on the asphalt and drove away."*
- **People**: `[18:30]` *"if it's a public place, it should have people. Otherwise it just
  feels empty and weird. **For residential renderings I usually don't**, because if you're
  putting someone in there, the homeowner is like 'well, who is that person?'"* — a direct
  answer for our own residential frame.
- **Depth layering** `[13:19]`: foreground blurred, midground (the subject) in focus,
  background blurred — *"just so you see the depth."*
- **Post-processing** `[08:48]`: *"the post-processing is like **the magic that really brings
  an image together.**"*

---

## 7. WHAT IS OWED FROM THIS UNIT

1. **Build the "where does your eye go" rung**: on the frame of record, report the brightest
   and the most saturated region, and whether either is the subject. Both are already
   computable; the question is what is missing.
2. **Shadow direction**: check that our key does not throw shadows toward camera, and that
   the subject is in light rather than in shade.
3. **Per-instance variation** is now carried by four independent sources — treat it as the
   named fix for P2r-2 and for any repeated prop, including UV DIRECTION per board.
4. **Settle the closet-density question** (§4) by measuring fill fraction on the anchor pool
   rather than choosing between two correct-but-opposite rules.
5. **Roughness consistency across materials**, and a residential frame with **no people**.
6. Record that `2stNv09sbe8` is an illustration lesson, so nobody re-picks it as CG critique.
