# The wardrobe contents: a stylist's ordering rules, and the three rod heights

**Sources (REFERENCE tier), two units watched together because one supplies the rules and
the other the numbers.**

1. YouTube `MqfBg3-yzY4` — <https://www.youtube.com/watch?v=MqfBg3-yzY4> · Hollywood
   Stylist Erin Ross, *"Organize Your Closet Like a Stylist (The Closet Boutique Method)"*
   · 12 min 54 s · *"After 20 plus years of working with luxury clients…"* `[00:31]`.
2. YouTube `eDUQkwlLzBk` — <https://www.youtube.com/watch?v=eDUQkwlLzBk> · Get Organized
   With Bridges & CO, *"The Standard Length Needed to Hang a Clothes Rod by a Professional
   Organizer"* · 1 min 12 s.

Watched 2026-08-28 via `pipeline/scripts/watch_local.py`; transcripts via
`youtube-transcript-api`. Timestamps verbatim.

**Why they were picked.** `ORD-2026-08-26` is a standing owner verdict — *"ของในตู้
built-in ยังไม่เป็นธรรมชาติ"* — and the lane has never had a source for what the contents of
an open wardrobe are supposed to do.

**Caveat, recorded because it matters for how these are used.** `MqfBg3-yzY4` is
**narration over title cards and stock photography**, not a closet being worked on camera
(verified from the extracted frames). It is a RULES source, not a pixel source. Both are
US residential-organiser practice; neither is Thai, and neither shows a wardrobe at the
3-4 m viewing distance our frame is judged at — that gap is recorded as **VG-01** in
`qa/video-curriculum.json` and can only be closed by measuring the anchor pool.

---

## 1. THE THREE ROD HEIGHTS — and our rail matches none of them

`eDUQkwlLzBk` `[00:25]`-`[00:40]`, verbatim: *"the single hang portion of your closet needs
to hang between **66 and 68 inches** to the top of the rod. For a double hung rod it needs
to be **40 to 42 inches** from the bottom, and then the top rod needs to be **80 to 82
inches**."*

| Condition | Stated | Metric (to top of rod) |
|---|---|---|
| single hang | 66-68 in | **1676 - 1727 mm** |
| double hang — lower rod | 40-42 in | **1016 - 1067 mm** |
| double hang — upper rod | 80-82 in | **2032 - 2083 mm** |

**Our BF09-3 hang rail sits at z 1850-1880 mm** (p2r84/p2r85 scene dump). That is
**~125-200 mm above the single-hang band and ~150-230 mm below the double-hang upper
band** — it matches neither condition. The rail height in our spec appears never to have
been checked against any standard.

This is a REPORT, not a conviction (R7d): the numbers are US organiser practice and Thai
garment lengths and ceiling heights differ. What it earns is a row — *the rail height has
no cited source* — of exactly the kind the heights source ladder (R12/DRW-2) exists for.

**It also settles a smaller puzzle.** carry_check reads our garment top at 1735 mm under a
rail at 1850 mm and calls it 115 mm of air. Against these standards, a garment hanging
~115 mm below its rod is *normal* — that distance is the hanger's hook rise plus the
shoulder. The defect is not the gap; it is that **the hanger occupying that gap is three
pixels wide and is a Blender CURVE that no rung in the repo can see.** The gap is the
symptom of the invisible hanger, not a second fault.

---

## 2. THE GOVERNING PRINCIPLE

`[02:14]` *"Most closets are designed for **storage**. A stylist's closet is designed for
**visibility**."*

Our nine cells are modelled as storage. Every rule below follows from choosing visibility
instead, and each one is buildable.

---

## 3. THE ORDERING RULES — all of them buildable

### 3.1 ALL GARMENTS FACE THE SAME DIRECTION
`[06:04]` *"save space by making sure your clothing is all **facing the same direction**."*

This is `P2r-20` (garment hang orientation), which is R1-stopped territory in the plan. It
is not an aesthetic preference in the trade — it is stated as standard practice, and it is
a single-line constraint in the builder.

### 3.2 MATCHING HANGERS ARE THE RULE, AND THE SHAPE VARIES BY GARMENT
`[03:27]` *"**Use the same color hangers.** Remember, you're creating your personal
boutique… This is your boutique and your boutique has matching hangers."*

Then the shape taxonomy `[03:57]`: **thin flocked/slip-resistant** (space saving),
**rounded or padded shoulder** *"to protect the shoulder shape of your jackets and
lightweight knits"*, **wood** *"offer the most support for heavy coats"*, **clip hangers**
for skirts and trousers.

So: one hanger COLOUR/material family across the wardrobe, but a **shoulder profile that
changes with the garment class**. Our hangers are 37 identical curves.

### 3.3 COLOUR RUNS, RESTARTED PER CATEGORY
`[06:04]` *"Keep clothing categories together and arrange them from **light to dark**
colors. **Start from light to dark at the beginning of each new category.**"*

A sawtooth, not one monotonic ramp across the whole wardrobe. That is a precise,
testable value pattern for the band — and it is the closest thing found to the *"value
rhythm"* the critics asked for, though it is still not the 3-4 m measurement (VG-01).

### 3.4 SHORT AND LONG GARMENTS GET SEPARATE ZONES
`[04:56]` *"It helps to have a **separate hanging area for short and long garments**. Short
items such as shirts and skirts can be **stacked on top of one another** by using a hanging
rod."*

Our nine cells are, as far as the spec is concerned, interchangeable. A real wardrobe has
**double-hang cells and long-hang cells**, and the two rod heights in §1 are exactly that
distinction. This is the single most structural item in this note: it changes the
casework, not the styling.

### 3.5 WHAT IS FOLDED RATHER THAN HUNG, AND WHY
`[06:37]` shelves take *"jeans, thick sweaters, handbags, and optionally shoes"*; drawers
take knitwear, tees, activewear, lingerie. `[07:44]` *"bulky and heavy sweaters… **don't
hang well because their weight stretches them out**"* — heavy cardigans are folded too.
`[07:13]` *"**Shelf dividers and bins help maintain uniform stacks.** Arrange them from
light to dark colors."*

### 3.6 SHOES ARE A TRAP
`[08:45]` *"if you're hard on your shoes, or they aren't all display-worthy, **shoe shelves
can look a little bit sloppy** and get very dusty"* — boxes labelled with a photo *"creating
a **uniform look**"* is offered as the alternative. Arrange footwear by category; handbags
*"by style and height"* `[09:55]`.

---

## 4. THE ITEM THAT MOST DIRECTLY ANSWERS THE OWNER'S VERDICT

`[11:04]` *"Most Rodeo Drive boutiques have a **display person** who specializes in
artistic product placement and creating the mood of the space… **Beautiful boutiques have
beautiful decor.** Look at your space for opportunities to incorporate items that make you
happy… Do you have any room for **a small framed photo, a clock, or some faux flowers**? A
display of **favorite jewelry, a special handbag, or a fabulous pair of shoes** adds
personality to your space."*

And then, on the casework itself `[11:34]`: decorative knobs, decorative hooks and shelf
brackets, *"a more **substantial light fixture**"*, *"an accent wall or just **the backs of
shelves painted in a bold color that really pops**"*, a full-length mirror *"with some
character"*, a candle or diffuser, *"a stool, a storage bench, or a pretty rug"*.

> **A designed open wardrobe is not only clothes.** It carries a small number of
> NON-GARMENT objects, and its own back panels may be a different colour from the carcass.
> If our nine cells contain only garments and folded stacks on a uniform carcass, that
> alone could be the whole of *"ยังไม่เป็นธรรมชาติ"* — and it is the cheapest thing in this
> entire curriculum to test.
>
> It also rhymes exactly with the two other critics in this curriculum: *"all flat things
> on the wall — that falls flat"* and *"you wouldn't have just one type of vegetation"*.
> **Three independent sources, three disciplines, one law: a field of one kind of object
> reads as fake, and the fix is a different KIND, not more of the same.**

---

## 4b. A THIRD SOURCE, FROM RETAIL — and it says LESS, not more

Added 2026-08-28 from a third unit watched into this same file:
`1NI4zETSrQs` — <https://www.youtube.com/watch?v=1NI4zETSrQs> · Pure London × JATC, *"The
Do's and Don'ts of Visual Merchandising with Debbie Flowerday"* · 4 min 15 s · the speaker
is **an associate lecturer in visual merchandising at London College of Fashion**, walking
a real independent store.

- **DENSITY: less, not more.** `[01:28]` *"when customers come inside **don't bombard them
  with merchandise — keep it simple. They're more likely to buy if there's less
  merchandise.**"*

  This is the one instruction in the whole G2 group that points *against* the lane's
  instinct. Our reflex on a wardrobe that reads wrong is to add more garments, more stacks,
  more props. A merchandising lecturer's first rule for a space people are meant to enjoy
  looking at is the opposite. **Whether our nine cells are too FULL has never been asked.**
- **A FOCAL POINT, again.** `[01:02]` *"regardless whether your store is large or small it's
  very important to **create a strong focal point**."* That is the fourth independent source
  in this curriculum naming a focal point as a required part (see also `kmCHv3PG2XM`
  `[05:47]` and `[09:11]`).
- **SHELVES ARE DISPLAY, NOT STORAGE** — the same split as §2, from the retail side.
  `[01:57]` *"**don't waste the shelves, create a display area** — and the **plants soften
  the whole look** and engage the customer in the store identity."* `[01:28]` on
  non-merchandise objects: *"there's nothing stopping you purchasing **books and ceramics**
  as long as it relates to the store identity."*

  Third independent source for **non-garment objects inside the casework**.
- **THE SHELF BACK IS A SURFACE TO TREAT.** `[02:24]` *"these **panels** are absolutely
  perfect — they create a **3D effect** and can be **painted or textured** depending on your
  merchandise."*

  Second independent source for treating the back of the cell differently from the carcass
  (Erin Ross `[11:34]`: *"the backs of shelves painted in a bold color that really pops"*).

## 5. WHAT IS OWED FROM THESE UNITS

1. **Row the rail height against the three standards (§1)** with a cited source, per the
   R12 heights ladder. Currently it has none.
2. **Split the cells into double-hang and long-hang** (§3.4) — casework change, and the
   two rod heights come with it.
3. **All garments one facing** (§3.1) closes the direction half of P2r-20 with a trade
   citation behind it.
4. **Hanger family: one colour/material, shoulder profile by garment class** (§3.2) — and
   the hangers must become geometry an instrument can see before any of this is testable.
5. **Light-to-dark runs restarted per category** (§3.3) as the value pattern for the band.
6. **Put non-garment objects and a contrasting shelf back into the cells** (§4) and judge
   the result — the cheapest available test of the standing owner verdict.
