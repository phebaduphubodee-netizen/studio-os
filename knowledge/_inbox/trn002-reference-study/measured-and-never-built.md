# MEASURED AND NEVER BUILT — a defect class that no audit in this repo could see

- Source: TRN-002 reproduction lane, rounds 13–14 (2026-08-05).
- Tier: REFERENCE. Distilled from our own build, not from a document.
- **n = 3 instances in one lane.** Treat as a hypothesis with three examples,
  not a law. What would kill it: a lane where the identifying feature and the
  built geometry are produced by the same pass and the defect still appears.

---

## The class

A measurement pass identifies an object **by a feature** — the feature is what
makes the object findable, and it gets written down in the spec, precisely, with
subpixel coordinates. Then a different pass builds the object **from its
bounding box**, and the feature is never built. The spec still reads as
impeccably measured. Nothing fails. The object renders as a blank slab.

Three instances, all found in one evening by looking at a crop beside the
reference rather than by running any check we own:

| object | what its own `seen` field recorded | what got built |
|---|---|---|
| `artwork` | "a 21 mm black frame bar at luma 28–33 against a 175–187 wall" — a 6:1 contrast, the strongest edge on that wall | a white slab at 0.78 albedo |
| `door_leaf` | "leaf edges (shadow-gap dark minima) at u=630.16/630.01/629.80 … black lever handle at u 669–683, v 452–468" | a flat white rectangle, no gaps, no handle |
| `ward_band` / the left run | "fine vertical fibrous striations, irregular linear porosity" | an isotropic marble map with tile coursing |

**Why no audit caught it.** Every check we own asks *does this object's number
have a basis*. All three had one. The provenance strings are honest and
complete. The question none of them asks is *does the built object still carry
the feature it was IDENTIFIED by* — and that question is the whole difference
between a measured object and a legible one.

→ **Transferable check**, and it is cheap: for every mass whose `seen` field
names a *feature* (an edge, a bar, a gap, a fitting, a grain direction) rather
than only an extent, assert that a mass or a material property exists which
produces that feature. *Killed by:* a lane where `seen` fields only ever record
extents, in which case the check has nothing to bind to and the class shows up
somewhere else instead.

---

## The sibling: BURIED GEOMETRY

`door_leaf` was worse than featureless. It was a 14 mm slab living **inside** a
100 mm wall, protruding 2 mm on the face that points away from the camera — so
the alcove wall stood between the camera and its own door. It had been invisible
since r2, for twelve rounds, while its `seen` field described the target's door
in detail and its plane fitted the target's head line to 0.001 in slope.

Nothing failed, because nothing was wrong: the leaf was on the right plane, at
the right height, with the right provenance. **A mass can be simultaneously
well-measured, well-placed, and unrenderable**, and no reprojection metric can
see it, because reprojection measures where a point *would* land, not whether
anything is there to be seen.

→ **Transferable check:** a mass whose `seen` field says VISIBLE must own pixels
in the render. Our id-mask machinery already produces exactly that per-object
map; nothing was comparing it against the `seen` claims. This is a rule that can
be a program, which by this repo's own standard is the only kind that is real.

---

## And the correction that made both findable: identity is not texture

The left run — étagère, console, desk, headboard band, nightstand — was called
**travertine** from r6 to r13 on the strength of an 8× crop showing "fine
vertical striations and irregular linear porosity". That reading is defensible;
rift oak and vein-cut travertine produce the same tight parallel lines.

It is **oak**, and the evidence is not a better crop. It is that the console
carries those fibre lines *continuously around a full half-round end*, and stone
does not bend.

→ **A crop answers "what does this surface look like". Identity needs "what
could have been MADE this way"** — and only the second question has an answer a
measurement can refute. The hue check we did run agreed the whole time
(corrected B/R 0.59–0.69 target against 0.66–0.77 ours). What separates them is
**anisotropy**: the target's veneer varies ~6× more along the grain than across
it (nightstand 6.3:1, band 5.8:1); our marble-mapped frame returned 2.1:1 and
0.42:1. *Killed by:* a delivered render whose cabinetry really is stone, where
this test would call it wood.

---

## Two smaller ones, both about instruments

**A probe that needs more care than the thing it probes is not a probe.** Three
flat-panel probes failed to answer which mapping rotation turns wood grain — a
degenerate zero-thickness quad, a sample window straddling a panel edge, objects
rotated out of frame. The real scene answered in one quick render. *When the
apparatus is more delicate than the subject, render the subject.*

**Two world features can share one pixel column.** An audit agent measured the
wardrobe run's end at y = −2299 mm. That corner projects to u = 730.94; the
room's own back corner projects to u = 730.64. The agent had fitted the room
corner and attributed it to the wardrobe. The wardrobe's true end (−2550) is
confirmed independently at u = 754.33 against a measured 753.80 — **0.5 px**.
→ A single-feature fit on a wall full of parallel verticals is not a
measurement; it is a label applied to an edge. Require a second, *different*
feature before adopting.
