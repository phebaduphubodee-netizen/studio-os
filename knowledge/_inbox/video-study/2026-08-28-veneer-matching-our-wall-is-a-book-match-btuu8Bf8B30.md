# Our wood wall has a trade name, and it is BOOK MATCH

**Sources (REFERENCE tier), the veneer trade.**

1. `btuu8Bf8B30` — <https://www.youtube.com/watch?v=btuu8Bf8B30> · Oakwood Veneer (Chris),
   *"Wood Veneer Matching Techniques Explained: Book Match, Slip Match…"* · 3 min 26 s.
2. `9rdokhlNL94` — <https://www.youtube.com/watch?v=9rdokhlNL94> · New England School of
   Architectural Woodworking, *"Creating a Bookmatched Veneer Panel — Part 1"* · 9 min 32 s.

Watched 2026-08-28 via `pipeline/scripts/watch_local.py` (26 frames each); transcripts via
`youtube-transcript-api`. Timestamps verbatim.

**Why.** P2r-2 has been open since p2r49 and its live reading is C2's, filed by eye at
p2r64: *"grain runs continuously across the black grooves, **a visible mirror axis
mid-wall**, the same block repeated left and right."* The lane has treated that as a texture
problem. **It is a named woodworking pattern, it is the commonest one, and the trade has
four alternatives to it.**

---

## 1. THE TAXONOMY, with the one we have at the top

`btuu8Bf8B30`:

| Match | What it is | Verbatim |
|---|---|---|
| **BOOK MATCH** | *"the most common way that veneer is matched"* — flip alternate leaves | `[00:00]` *"You simply take two sheets of the veneer, **flip one open like it's the pages of a book**, and you'll end up with the sapwood in the centre"* |
| **SEQUENCE MATCH** | sapwood removed first, leaves arranged for uniformity | `[00:25]` *"I'm first **cutting off the sapwood**, and I'm arranging the pieces in any way that I want so that they appear the **most uniform** in colour and pattern"* |
| **SLIP MATCH** | slide the next leaf alongside — **no flip, no mirror** | `[00:25]` *"simply **sliding one sheet of veneer alongside of the other** and attaching them"* |
| **END MATCH** | leaves flipped along the ends to read as one longer piece | `[00:49]` *"leaves are flipped along the ends, making it look like **one longer piece continuing the pattern** in that direction"* |
| **RANDOM MATCH** | no rule; some book, some slip | `[01:37]` *"there is **no rhyme or reason**… you get a varying look that's often associated with a **rustic** look"* |
| **PLANK MATCH** | like random, but **the pieces vary in width** | `[02:03]` *"the biggest difference is **the pieces have different widths**"* |

And a separate, orthogonal property that gives us a **testable rule**:

`[01:12]` *"notice that I have marks here showing that they're each **spaced evenly**. This
means that this sheet is what is called **balance matched**. **There's not a skinny stripe
at this end or a skinny stripe at this end.**"*

> **BALANCE MATCH IS CHECKABLE ON OUR WALL FROM THE SCENE DUMP, TODAY.** If our end boards
> are a fraction of a full board width, the wall is not balance-matched and a real joiner
> would not have built it that way. Nobody has looked.

---

## 2. THE PHYSICAL FACT THAT EXPLAINS WHY OUR WALL READS WRONG

`9rdokhlNL94` `[00:44]`, on how veneer actually comes off a log:

> *"when veneer is cut from the tree it's cut into sheets that are anywhere from **a
> 32nd to a 40th of an inch thick**, and they're **kept in the same order as they came in
> the tree**, so any pattern that's in any given piece is going to continue to occur in the
> next piece — it's going to look **almost** the same as the previous piece, and so on
> through the line. **As you get down further in the stack the pattern might change a bit
> more**, but any two leaves that are **consecutive** are going to have something that looks
> pretty similar."*

And the worked example `[01:28]`: *"this little **eye** here has become **a bit smaller**
here, yet the overall pattern is still pretty much the same."*

**Leaf thickness: 1/32″ – 1/40″ = 0.79 – 0.64 mm.**

> **This is the mechanism our wall is missing.** A real matched wall is neither identical
> nor random: consecutive leaves are *nearly* the same, and the similarity **DRIFTS
> monotonically along the wall** as you move down the flitch. Ours is an exact repeat with
> an exact mirror — two states the tree cannot produce. The fix is therefore not "a
> different texture" and not "randomise"; it is **a controlled drift** across the boards,
> plus a decision about which match type the wall is.

`btuu8Bf8B30` `[02:28]` adds the procurement half: *"just because pieces of wood or veneer
are cut from the same species of tree **does not necessarily mean they're going to have the
same appearance**. If you look at these two pieces of cherry, they are very similar in size
and colour. However, if I look at these two pieces of **white oak, they are very different
in colour.** So you need to make sure that you request **sequenced panels** if more than one
panel is needed for a particular project."*

Drift is real, it is expected, and on a real job it is MANAGED by ordering sequenced
panels — not left to chance.

---

## 3. TWO CRAFT DETAILS WORTH KEEPING

- **A book match on straight grain is deliberately angled** `[02:12]`: *"since this is a
  pretty straight-grained wood, if we just simply open it up like this **it isn't quite as
  interesting**, so what we're going to do is **angle it just a little bit** so it kind of
  makes a **V-shape** for our pattern — and we can decide later if we want the **V to go up
  or go down**."* A joiner introduces a deliberate small angle; the mirror is not
  perpendicular by default.
- **A panel must be veneered on BOTH faces** `[03:42]`: *"the reason we have to veneer both
  sides of a panel is because **it keeps it balanced**. If you only veneered one side you
  would actually **cause the panel to bend**, and that's due to the glue drying and pulling
  on one side."* A backing veneer with *"similar characteristics"* is used even where it
  will never be seen.

  That is an R10-class fact: a panel finished on one face only is not a thing that exists.
- Leaves are **numbered** as they come from the supplier `[02:59]` — *"you're going to
  assume that they're in consecutive order and you want to **put numbers on them**"* —
  because the sequence IS the material.
- A **four-way book match** is used for burls `[02:12]`, mirroring in both axes.

---

## 4. WHAT IS OWED FROM THIS UNIT

1. **Name our wall's match type in the spec.** It is currently an unnamed exact
   repeat + mirror. Choose one: slip (no mirror, our likely answer for a wall of boards),
   plank (varying widths), or a real book match with drift.
2. **Test BALANCE MATCH from the scene dump** — no skinny board at either end. Free, no
   render needed, and nobody has checked it.
3. **Model the DRIFT, not randomness**: consecutive boards nearly alike, changing
   monotonically along the wall. That is a different generator from the per-tile random
   rotation the archviz sources prescribe for grass, and it is the correct one for boards.
4. **Leaf/board width is still unknown** and must come from a supplier catalogue (VG-09) —
   without it the lane will fix the mirror and then invent a width, which is R10's
   typed-number defect again.
5. Record the both-faces rule (§3) against any panel in the build that is veneered on one
   side only.
