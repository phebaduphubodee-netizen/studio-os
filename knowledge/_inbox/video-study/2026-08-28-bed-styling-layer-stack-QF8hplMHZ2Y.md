# A studio principal builds a bed on camera — the layer stack, and which layer is allowed to wrinkle

**Source (REFERENCE tier).** YouTube `QF8hplMHZ2Y` —
<https://www.youtube.com/watch?v=QF8hplMHZ2Y> · Studio McGee, *"The Art of Bed Styling:
How To Style Your Bed Like An Interior Designer with Shea McGee"* · 10 min 17 s. Watched
2026-08-28 (36 scene frames via `pipeline/scripts/watch_local.py`; transcript via
`youtube-transcript-api`). Timestamps verbatim.

**Why it was picked.** The bed is the largest styled mass in our frame and it is
measurably wrong in two ways at once: duvet plan coverage **43 %** where delivered beds
read **~80 %**, and cloth carrying **2.1× (duvet) / 3.7× (throw)** the fold energy of the
delivered comforter. This is a working studio principal assembling a bed layer by layer
and saying why each layer is there.

**Caveat.** Studio McGee sells bedding and this is a brand video; the layering is
US-market and heavier than a Thai master suite would carry. The STACK and the
structured/relaxed law transfer; the product list does not.

---

## 1. THE FINDING THAT MAPS ONTO OUR NUMBERS

`[08:46]` — *"with my duvet and my quilts and even my pillows I like to place them in a way
that feels pretty **structured**, but when I place my throw at the end of the bed **I want
some wrinkle and I want it to feel relaxed**, because it's that last finishing layer that
makes your bed — and therefore your room — feel like you want to live there instead of it
feeling too stiff."*

**The wrinkle is assigned to ONE layer, deliberately, and every other layer is
structured.** Our own measurements read duvet 2.1× and throw 3.7× the delivered
comforter's fold energy. Against this law:

- the **direction** is right — our throw does carry more fold energy than our duvet, which
  is what a designer intends;
- the **duvet is wrong in CLASS, not merely in amount.** A structured layer at 2.1× the
  reference is not a slightly over-tuned parameter, it is a layer behaving like the wrong
  layer. That reframes the fix: the duvet does not need less noise, it needs to stop being
  a relaxed surface at all.

The confirming visual is `frame_0055`: the finished bed's duvet field is essentially
planar with a slow ripple, and the only high-frequency cloth in the whole frame is the
throw laid across the lower third.

And the opposite failure is named too, `[03:44]`: *"if you really wanted to you could just
do a coverlet, but you need to know that it's going to **look very flat** on your bed —
for me a luxurious bed has layers and some of that down fluffiness."* So the target is not
"flat"; it is **structured with volume**. Two different faults — flat, and crumpled — with
the correct state between them.

---

## 2. THE STACK, IN ORDER

1. **Fitted sheet + flat sheet** `[00:30]`. Fibre changes the read: *"percale is going to
   give you that crisp look but it gets wrinkly faster… linen wrinkles but it kind of
   looks like it's intentionally supposed to be that way"* `[00:56]`. Wrinkle is
   acceptable when the material makes it read as intentional — a material-dependent
   licence, not a blanket one.
2. **Quilt**, in one of two positions `[01:48]` `[04:17]`: *under* the duvet pulled high
   enough that *"when I fold my duvet I get a little sliver of this quilt pattern
   showing"*, or *on top* — the choice is *"all about the pattern… the other way is more
   about saturated colour"*.
3. **Duvet** `[02:50]`, and this is a coverage rule stated out loud:
   > *"When I am doing my duvet covers I'm going to pull it so you get **the reveal of the
   > bed frame**, and then you get to see kind of some **drape around the edges**."*

   The duvet is deliberately NOT taken to full coverage — the frame is meant to show. Our
   43 % is far below the delivered 80 %, but the ceiling is not 100 %: it is *"reveal the
   frame, drape the edges."*
4. **The fold-back**, `[03:20]`: *"you can just do a fold in half, but I prefer to **fold
   back and then back again**, so that I get like this **extra fluffy band** across the
   bed."* A double fold-back producing a raised band — a buildable geometric feature, not
   a cloth-sim outcome. Visible as the pale band in `frame_0055`.
5. **Pillows** `[05:11]`-`[07:02]`: two sleeping pillows, two shams — *"make sure that
   you're buying shams that fit the size of your bed… if you have a full or a queen you're
   going with a standard sham, and if you have a king go with a king size sham, **so it
   fills the length of the bed**"* — then decoratives. Counts: *"I tend to like **odd
   groupings, so three or five pillows**"* `[06:33]`; the maximal set she builds is *"two
   big, two medium, and then one lumbar"* `[07:26]`.
6. **Throw** `[07:52]`: *"I prefer a throw that goes over the end of the bed and **drapes
   on both sides**"* — over the corner also works.

---

## 3. A STATED MINIMUM FOR "FINISHED" — the half-made threshold

`[06:08]` *"once you finish things off with a sham, a quilt and a duvet you've got nice
sheeting. It's **a very simple look but it IS finished.** But these next steps are the
layers that add a bit more interest, and if you're going for that look of things that feel
a bit more **collected**, we add the decorative pillows and then a throw at the end."*

This is the only threshold for "finished" found anywhere in the curriculum so far, and it
is a **count of layer TYPES, not of objects**: sham + quilt + duvet = finished; decorative
pillows + throw = collected. Our lane's half-made verdict has never been expressed as a
missing layer type. It is worth checking our bed against this list before adding anything
else — the answer may be that a whole layer is absent rather than that the existing ones
are badly tuned.

`[09:10]` also gives the permission to subtract: *"if you are a person that likes a very
modern interior then you might consider either foregoing the throw… because it does help
relax some of those structured lines."*

---

## 4. WHAT IS OWED FROM THIS UNIT

1. **Re-frame the duvet fold-energy row.** It is not "2.1× too noisy", it is "a structured
   layer is behaving as a relaxed one". The throw is the only element licensed to wrinkle.
2. **Row the double fold-back band** (§2.4) as a buildable feature — box-and-fold geometry,
   R8 BUILD class, not a simulation.
3. **Check our bed against the layer-TYPE list** (§3) before tuning any existing layer.
4. **Duvet coverage has an upper bound as well as a lower one**: reveal the frame, drape
   the edges. Feed this into VG-02 alongside the anchor-pool measurement.
5. Pillow counts: odd groupings, 3 or 5 decorative; shams sized to fill the bed width.
