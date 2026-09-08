# Rug and bedcover: the numbers, including the conversion VG-02 said was missing

**Sources (REFERENCE tier).**

1. `1kItQdeo9oc` — <https://www.youtube.com/watch?v=1kItQdeo9oc> · Lisa Holt Design, *"How
   to Choose the Right Rug Size"* · 14 min 12 s → **ORD-2026-08-25b (*"พรมยังไม่สวย"*).**
2. `axFPC-8MS_0` — <https://www.youtube.com/watch?v=axFPC-8MS_0> · NCCarpetBinding,
   *"Handmade rug minimal edge serge vs. micro serge and standard"* · 55 s → **the rug edge
   rung.**
3. `kcefHTeuXNE` — <https://www.youtube.com/watch?v=kcefHTeuXNE> · Just Get It Done Quilts
   (Karen Brown), *"What size quilt do you need for your mattress"* · 8 min 11 s → **VG-02.**

Watched 2026-08-28 via `pipeline/scripts/watch_local.py` (26 frames each); transcripts via
`youtube-transcript-api`. Timestamps verbatim.

---

## 1. THE BEDROOM RUG RULE, and it is not about the rug

`1kItQdeo9oc` `[02:00]`, unprompted and emphatic:

> *"There's nothing I hate worse than walking in and seeing a little rug in front of a bed.
> **What is that for?** You don't get off the bed in the front. **You get off the bed on the
> side**, and when your feet hit that floor, you want your feet to hit a carpet. So **you
> want that area rug to hold that whole space — bed AND nightstands**, if you have them."*

**A single testable predicate for our frame: does the rug's plan extent contain the bed and
both nightstands?** Answerable from the scene dump with no render. Our rug work has been
about edge geometry and scale; this is a different question and it has never been asked.

### 1.1 THE GOLDEN RULE, with a number
`[00:00]` *"the number one golden rule… **you want to make sure that there's a four to
six-inch border around all of the furniture pieces and all of their legs** on anything
you're going to place it underneath."* → **102-152 mm of rug beyond every leg.**

Method `[00:42]`: measure the piece end to end, **add six inches each side**, same for the
width. And a caveat that matters in a room like ours `[01:21]`: *"make note of anything that
is on the floor that might cause the rug to be a different shape or need to be a different
size — things like a raised hearth, **bookshelves that project into the room**, or an oddly
shaped corner."* Our wardrobe wall projects into the room.

### 1.2 WHAT THE RUG IS FOR
`[01:21]` *"what the area rug does is **it defines the space** as different from the rest of
the floor… if it's in the master bedroom, it's **defining your sleeping area**."*

Third source in this curriculum for the rug as a ZONE definer (see also Caroline Winkler
`[27:27]`, and Darren Jett's *"a big rug to join the two spaces together"*).

### 1.3 STANDARD SIZES AND MATERIALS
`[02:38]` prefabricated sizes in feet: **3×5, 4×6, 5×8, 6×9, 9×12, 10×12, 10×14, 10×15,
12×15** — *"those are the general referral sizes."*

`[03:56]` for a master bedroom specifically: *"if it's going into a master bedroom suite,
and you're **only gonna walk on it in your bare feet**, then doing something really
**delicate and silk and lovely** that's soft underneath"* — and `[08:21]` *"you can go to a
very luxurious **wool or silk shag**, which would be really soft underneath."* Wool is
*"the granddaddy of all the natural fibres"* `[05:13]`, its drawback being price.

Constructions named `[06:28]`: flat weave, low/medium pile, **Berber (loop)**, cut-and-loop,
carved, wovens (Wilton), hides, carpet tiles, **shag (tufted, super long pile)**.

### 1.4 A PAD IS ALWAYS THERE
`[09:37]` *"you always want to **put a pad under almost every area rug** situation. At
minimum, it needs to be a non-skid or slip-proof mat. Anything other than a super deep pile
or a shag will definitively need a pad."*

An R10 item: a real rug sits on a pad, so its top surface is above the floor by pile +
pad — which is also why a rug lying at 0 mm reads wrong.

---

## 2. THE RUG EDGE — three named grades, and it is a stitched bead

`axFPC-8MS_0` is 55 seconds of a fabricator showing the same rug edged three ways, and the
variable he names is **how far the stitching penetrates and how much of the edge it
covers**:

- `[00:00]` *"here is your **standard serge**, as far as depth into the carpet, how far it
  stitches in"*
- *"here is the **micro serge**… you just get a different stitch tongue and you can set the
  **depth a little shorter**"*
- `[00:23]` *"then there is the **minimal edge serge**, or the hand-serge machine… it is an
  enormous difference as far as **coverage being at an absolute bare minimum**."*

`frame_0013` shows it plainly: the pile runs to a cut edge and a **stitched bead wraps that
edge**, with the rug's own thickness visible as a rolled shoulder rather than a 90° step.

The alternative for flat weaves, from the rug video `[12:52]`: *"you can either do it
**serged**, if it's a deep pile, so that you don't see the edge and you just have this
lovely **deep pile flowing over the edges**. Or if it's sort of a flat weave like a sisal,
then you can add a **binding** to the edge, which is a couple of inches wide, and it gives
you a nice **accent strip** around the edge."*

> **Two legitimate edges, and our rug has neither**: a deep pile whose fibres roll over the
> cut edge and hide it, or a flat weave with a 2-inch fabric binding that reads as a
> deliberate stripe. The P2 exit clause's `rug_edge` crop was asking whether the edge rolls
> or steps; this names what it should be rolling INTO.

---

## 3. THE BEDCOVER CONVERSION — VG-02, answered

VG-02 records that bedding charts give a **side drop** while our defect is a **plan
coverage** (43 % against ~80 %), and that converting one to the other *"requires assuming
how far the covering is pulled up toward the pillows — which is a styling decision, not a
catalogue number."*

`kcefHTeuXNE` `[02:50]` states the whole method, including that assumption:

> *"some quilts will lie on top of the mattress, some will drop down and cover the sides,
> some will tuck in, and some will hang down to the floor like a bedspread… **to get the
> proper drape you need to know how thick the mattress is** — and there's a huge variation,
> from a 4-inch foam to the thick coil with toppers at **10 inches plus**. Once you know the
> thickness, **add the drape length to the height measurement** of the mattress, and **twice
> the drape to the width** measurement. **Pillows normally sit on top of a quilt, so we
> don't normally add any drape to the top.**"*

And the missing constant, at `[03:56]`: *"draw out the mattress size, then add the drape,
and just note that **pillows will cover about 20 inches** as well."*

**So:**

| Quantity | Rule |
|---|---|
| cover width | mattress width **+ 2 × drape** |
| cover length | mattress length **+ 1 × drape** (foot only — no drape at the head) |
| drape | mattress thickness (**102-254 mm+**) plus however far below it should fall |
| head end | the top **~508 mm (20 in) is under the pillows** |

That last line is the conversion. Plan coverage is not "how much cloth" — it is the
mattress area minus the pillow band, and the styling decision VG-02 named has a working
default of **20 inches**.

### 3.1 AND THE SENTENCE THAT SHOULD GO STRAIGHT INTO THE ROW
`[01:06]`, repeated at `[04:29]`: *"**it's those EDGES of the quilt that you see first as
you walk into a bedroom.** Size matters."*

A maker who has no idea our project exists says the bedcover is read **at its edges,
first**. Our duvet-coverage defect is an edge defect by that definition, and our fold-energy
work has been measuring the field.

Two more usable facts: `[01:06]` *"I found **no less than 36 commercially available mattress
sizes**… I found no less than **10 sizes of king mattresses**"* — which is the same lesson
`BED_SIZES_TH` already carries; and `[06:41]` unwashed fabrics and batting shrink **up to
12 %**, pre-washed a further 2 %.

---

## 4. WHAT IS OWED FROM THIS UNIT

1. **Predicate: the rug plan must contain the bed and both nightstands** (§1) — check on the
   scene dump today.
2. **102-152 mm of rug beyond every furniture leg** as the sizing rule, measured against the
   wardrobe wall's projection into the room.
3. **The rug sits on a pad**; its top is pile + pad above the floor, never 0 mm.
4. **Give the rug edge a named type** — serged deep pile that rolls over, or a flat weave
   with a ~50 mm binding — and build that, rather than tuning a step down.
5. **Feed the bedcover formula into VG-02**: width + 2×drape, length + 1×drape, pillow band
   ≈ 508 mm, drape ≥ mattress thickness. Then re-measure the anchor pool with the same
   definition so ours and theirs are the same quantity.
6. **Judge the bedcover at its EDGES**, not only over its field.
