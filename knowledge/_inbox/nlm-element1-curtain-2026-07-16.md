---
title: "Element 1 — the curtain: colour/quantity in a 60-30-10 room, and the fold-geometry GAP"
source: notebooklm
notebook: a5a43395-e085-4fe6-a46c-4a8f7b438cc2  # "Design Systems and Integration Protocols"
turns: 19-20 (of 20)  # snapshot: nlm-element1-curtain-2026-07-16-qa-history.json (sibling, per lane convention)
date: 2026-07-16
tier: REFERENCE
status: staged — distil into knowledge/styles/color-composition.md before it gates a deliverable
privacy: generic/banded question only; no client identity, address, or plan detail left the machine
project: PRJ-2026-002 (element 1, the curtain)
---

# Element-1 curtain — the DR, and the honest A/B it produced again

**Why this DR fired.** Vault-first recon (5 knowledge-manager agents, 49 facts / 41 gaps) found the
studio ALREADY holds every clearance number we need — they are distilled at
`knowledge/ergonomics/casework-fixture-clearances-th-practice.md:186-198` from the owner's own
NITAS TESSILE sheets (`knowledge/_inbox/discord/MY-DATA-PEAT/dimension-interior/002_ม่าน-Curtain/`).
So NLM was fired ONLY on what the vault genuinely lacks.

**The A/B split repeated itself, exactly as in element 1's first cascade:** the notebook GROUNDS
composition (Albers) and honestly REFUSES detailing. That is now twice, and it is a reliable
property of this corpus — treat it as the lane's shape, not as luck.

---

## Ask 1 — GROUNDED (safe to gate a decision)

> **Q (banded, generic).** In a bedroom with a full-height glazed wall ~5.5 m long, a floor-to-ceiling
> curtain covers a very large share of the visible surface. The scheme already assigns its 30 %
> secondary to light oak, with cool off-white plaster as the 60 % ground and brushed brass as the
> 10 % accent. How should such a large treatment's colour/value be chosen so it does not displace or
> compete with the existing 30 % secondary? Should a large curtain read as part of the 60 % ground?
> What does the literature say about choosing a textile value relative to the wall it hangs against?

**What it confirmed, cited:** the 60/30/10 rule does put **window treatments in the 30 % secondary**
alongside furniture (dominant = walls/large rugs; accent = accessories/artwork) `[1]`.

**What it HONESTLY REFUSED — record this, it is the useful half:**
- The sources give **no guidance** on resolving the conflict when a treatment is so massive it
  displaces another 30 % element (our oak).
- The sources contain **no rule** for choosing a textile value relative to its wall.

**What it GROUNDED instead (Albers, *Interaction of Color*):**
- A colour's visual weight is set by its **"extension in area"** `[2]`.
- Increasing the amount of a colour **"visually reduces distance"** — the mass advances, producing a
  sense of **"nearness"** `[3]`.
- **THE LEVER:** *"any ground subtracts its own hue from colors which it carries"*, and *"the light of
  a ground subtracts in the same way that its hue does"* `[4]`. Therefore **a light-valued curtain on
  a light-valued ground has the visual diversion between them "reduced if not obliterated
  visually"** `[4]`.
- To make the boundary vanish **completely** the two must have exact **"equal light intensity"** —
  which the sources call a rare and difficult perceptual effect `[5, 6]`.

### The decision this supports (element 1, D8)

**The curtain JOINS THE 60 % GROUND. It is not a secondary colour.** Cool off-white linen-look at
(near) the plaster's value, so Albers' ground-subtraction collapses the wall/curtain boundary and the
**oak keeps the 30 %** that D1-A — the load-bearing call of the whole element — depends on.

**This is not a new idea imposed by the DR — it is D1-A's own words, now grounded.** D1-A already
issued: *"Put the remaining 60 % in matte, cool-toned off-white limewash / plaster / **textured
linen** — low-frequency texture that rests the eye and lets the oak grain read."* The signed decision
and the DR agree; the DR supplies the WHY and the citation.

**Deliberately NOT at exact equal intensity.** Albers says exact match is rare and hard, and it is
not the goal: a hair of value difference lets the curtain read as FABRIC, with the separation carried
by **texture and the wave's own self-shading** rather than by hue. A curtain that vanished into the
plaster would be a wall, not a curtain.

---

## Ask 2 — REFUSED, in full, verbatim

> **Q.** Wave-fold / ripple-fold (S-fold) drapery: fullness ratio, carrier spacing along the track,
> wave depth perpendicular to the track when fully drawn, hem height above finished floor, and
> track-forward-of-glass offset. Answer only from sources; say plainly if not covered.

> **A.** *"Based on the provided sources, **none of the specific information you requested is
> covered.** The sources do not contain any geometrical data, measurements, or specifications
> regarding wave-fold/ripple-fold (S-fold) drapery, including fabric fullness ratios, carrier
> spacing, wave depths, hem heights above the floor, or track clearances from the glass."*

**Consequence:** every fold-geometry number is **CONVENTION tier** — mine to decide, never to cite as
grounded. Anchor them on the one hard number the studio DOES own: **single-layer S-fold stack depth
= 130 mm** (`casework-fixture-clearances-th-practice.md:187`, from the owner's own NITAS sheet). For
a wave-fold system the carriers hold the wave whether stacked or drawn, so **stack depth ≈ drawn wave
depth** — that inference is MINE and is convention, not a cited fact.

---

## What the VAULT already had (so nobody re-fires this DR)

| Fact | Value | Citation |
|---|---|---|
| S-fold stack depth, single layer | **130 mm** | `ergonomics/casework-fixture-clearances-th-practice.md:187` |
| 3-pinch-pleat stack depth, single layer | 85 mm | `...:186` |
| Recessed pocket, single-layer S-fold | **≥ 150 mm** | `...:192` |
| Recessed pocket, single-layer 3-pleat | ≥ 100 mm | `...:191` |
| Pocket, 2-layer (S-fold + 3-pleat sheer) | ≥ 250 mm | `...:194` |
| Cove light in a drop-ceiling pocket | **+50–100 mm** | `...:196` |
| Curtains = floor-to-ceiling sheer or linen | required where windows exist | `rendering/cycles-lighting-camera-presets.md:265` |
| Fabric BSDF | rough 0.75 · IOR 1.5 · sheen 1.0 · sheen-rough 0.4–0.6 | `materials/texture-sets-discord.md:170-178` |
| Tropical humidity | unlined naturals rot/mould → mildew-resistant blend + UV lining | `materials/residential-materials.md:150-157` |
| Plastic-looking fabric | render defect **MA-05** | `classifications/render-defects.md:69` |
| Linen's heavy drape / micro-imperfection (pilling) | required for authenticity | `styles/color-composition.md:180-186` |

**A consequence worth putting in front of the owner:** our slot clears ~220–240 mm. A single S-fold
needs ≥150 → **fits, 70–90 spare**. But a SECOND layer (S-fold + sheer) needs **≥250** → **it does not
fit**. So *single layer* is not just this year's choice; **the slot permanently forecloses adding a
blackout layer later.** If the client needs a dark bedroom, that has to be solved another way (a
separate blackout pocket, or a different heading) and it has to be solved NOW, not after the blade is
built.

## Still GAP after this DR (do not fabricate)

Fullness ratio · carrier spacing · hem-to-floor gap · track-to-glass offset · sheer transmission
values for a BSDF · what should appear BEYOND the glazing (garden/context) · curtain drawing-symbol
convention (`plan-reading-conventions.md:90` logs it as an open gap; ASA 2554 carries **no** curtain
/ track / pelmet layer at all — `thai-cad-layers-asa2554.md:18-74`).

## Provenance

- Notebook `a5a43395-e085-4fe6-a46c-4a8f7b438cc2`, turns 19–20 of 20 (`history --json`).
- Ask 1 citations `[1]`–`[6]` resolve to the notebook's colour/design-principles sources; `[2]`–`[6]`
  are Josef Albers, *Interaction of Color* (the same source that grounded element 1's Ask 4 — see
  `nlm-element1-dressing-wall-2026-07-16.md`). `[1]` is the 60-30-10 design-principles source.
- Vault recon: 5 knowledge-manager agents, workflow `wf_54ed2c2b-8d3`.
- Single-flight, `-n <id>` explicit, `--timeout 120`, `--json`. 2 asks. Lane healthy.
