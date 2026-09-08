# NLM DR — cabinet veneer figure vs wood floor plank (REFERENCE tier)

**Tier:** REFERENCE. Not domain truth, not statute. Distil into `knowledge/materials/`
before any value here gates a deliverable.

**Fired:** 2026-08-01, by the builder, under CLAUDE.md DR triggers 2 + 4.
**Notebook:** `2638a889-9c7f-47fc-b49a-a390e0882007` ("TRN veneer figure 2026-08-01"), 60 sources.
**Conversation:** `579867c3-e210-474f-bf80-2d4a8f5285ab`, turn 1.

## Why it fired — vault first, then NLM, then DR

- **Vault**: `knowledge/materials/millwork-casework.md` §2–3 already holds the
  taxonomy (rotary / plain sliced / quarter sliced / rift; book vs slip match),
  in Thai and English. But every appearance claim there carries a `*` and an
  explicit GAP note: *"the corpus names the four cuts but describes **no**
  appearance or yield differences"*. So the vault knew the NAMES and not the LOOK,
  and the look is the whole question for a render.
  - Worth recording: the first vault search missed this entirely, because it
    grepped English (`bookmatch`, `flitch`, `crown cut`) against a file that
    indexes these in Thai (`การผ่าวีเนียร์`, `การเรียงลายวีเนียร์`). The gap was
    real; the first search for it was not. A vault miss is not a vault gap until
    the search has been run in the language the vault is written in.
- **NLM** (`a5a43395`, Design Systems, 118 sources) was asked before the DR. It
  answered — and said plainly that the specifics were *"not covered in the
  sources"* and that it was *"drawing entirely on information outside of the given
  sources"*. That is model memory, the failure mode CLAUDE.md warns about. Recorded
  as UNGROUNDED, not used, and it is precisely what justified paying for a DR.

## The answer

To accurately render a fine cabinet panel rather than a tiled wood floor, you must replicate the specific geometric, anatomical, and fabrication signifiers of architectural veneer. When a flat plane meant to be high-end millwork registers perceptually as a floor, it is usually because the texture misrepresents the scale, orientation, symmetry, or edge detailing of real cabinet construction [1]. 

Here is how the visible grain figure of a bookmatched plain-sliced cabinet panel differs from a wood floor, and the exact visual cues needed to render it correctly:

**Leaf Width and Panel Geometry (1-2 Meters)**
Fine cabinetry is not tiled with narrow, random planks [2]. Instead, a panel is synthesized by splicing together multiple thin "leaves" of veneer. Plain-sliced leaves typically range from 152 mm to 305 mm (6 to 12 inches) in width [3]. Premium architectural standards mandate that a panel must be "center-balanced," meaning it is divided into an even number of equal-width leaves centered across the face [4]. 
* **For a 1.0-meter (1000 mm) panel:** You should render a highly structured distribution of 4, 6, or 8 equal leaves (e.g., 6 leaves of 166.7 mm) [5].
* **For a 2.0-meter (2000 mm) panel:** The distribution should consist of 8, 10, or 12 equal-width leaves [5]. 
**Flooring, by contrast, uses offset units of mixed or random widths that are never symmetrically balanced or centered across a specific one-to-two-meter frame** [6].

**Direction of the Cathedral Figure**
Plain-slicing (flat-cutting) a log tangentially intersects the growth rings, yielding a nested, parabolic "cathedral" arch pattern [7, 8]. Because these arches represent the longitudinal growth of the tree trunk, **the cathedral figures must run strictly vertically (along the length) of the panel** [8]. Cabinetmakers intentionally orient the apex of these cathedral arches to point *upward*, which draws the eye up and conveys a sense of lightness and height while visually grounding the denser grain at the base [9]. Rendering cathedral arches running horizontally across the width of a door is anatomically impossible for a continuous trunk cut and instantly breaks the illusion [8].

**The Mirror Seam and Barber Pole Effect**
Bookmatching involves flipping every other veneer leaf over like the pages of a book [10]. This creates a **perfect, biological mirror image at the joint line, forming symmetrical diamond or heart-shaped figures** [10]. Because the straight-line rift edges are joined together, the actual physical seam becomes nearly invisible [10].
However, flipping the veneer introduces an optical phenomenon known as the **"barber pole effect"** [11]. The slicing blade compresses one side of the wood (the "tight" side) and slightly fractures the other (the "loose" side) [11, 12]. Because these alternating tight and loose faces react to light differently, **a bookmatched panel will display alternating light and dark vertical bands** [12, 13]. As the viewer's angle or the light source shifts, these light and dark bands dynamically invert [13]. Floor planks are always laid "slip-matched" (tight-side up) for uniform wear and light reflection, completely lacking this anisotropic optical behavior [13].

**Flitch Sequencing**
In a continuous wall of fine cabinetry, fabricators use "flitch sequencing" [14]. This means that consecutive leaves from a single sliced log are arranged in order, ensuring that organic characteristics—such as a localized mineral streak or a slight sweep in the grain—transition gradually and intentionally across adjacent cabinet panels [14]. **Flooring aims for the exact opposite effect**, intentionally scattering random, unsequenced planks from various parts of different trees to mimic a rugged, highly varied aesthetic [15].

**The Betrayal of Staggered Butt Joints and Micro-Bevels**
The most damning visual errors that will expose a digital cabinet render as a repurposed flooring texture are horizontal seams and beveled edges:
* **Staggered Butt Joints:** Flooring relies on randomized, short boards (300 mm to 2200 mm) that meet at staggered end joints to distribute physical load and allow for seasonal expansion [16]. Fine cabinetry panels use continuous, unbroken veneer leaves that cover the full vertical height of the door (up to 2.4 or 3.0 meters) [17]. **Introducing horizontal or offset seams across a cabinet face is a major structural defect that immediately codes the surface as a floor** [17].
* **Micro-Bevels:** Modern pre-finished flooring uses a 1-2 mm angled V-groove (micro-bevel) around the perimeter of each plank to disguise subfloor unevenness ("lippage") [18, 19]. Cabinet panels, conversely, are spliced perfectly flush and sanded into a single, seamless plane [20, 21]. **If your render includes linear micro-shadows catching the light at the joint lines, the continuous optical reflection of the cabinet face is broken,** and the eye instantly recognizes the boundary markers of individual floor planks [20, 21].

## Triage against OUR frame — what was applied and what was refused

**APPLIED — micro-bevel relief.** The DR names the tell: flooring carries a 1–2 mm
V-groove around every plank; cabinet panels are spliced flush and sanded to one
plane, and *"linear micro-shadows catching the light at the joint lines"* are what
make the eye read a panel as floor. Ours ran the floor's normal map at the 0.8
default on all three veneers and the cubby lining, because `NORMAL_STRENGTH` was
keyed by map SLUG and every veneer shares the `wood_floor` slug with the actual
floor — one parameter carrying two things, the same shape found in `tower.d_mm`
the same day. Veneer relief is now 0.10 against the floor's 0.8, pinned by a test
as a RELATION so the two cannot be collapsed again.

**REFUSED — "cathedral figure must run vertically".** The DR states horizontal
cathedral arches are *"anatomically impossible for a continuous trunk cut"*.
Round 4 MEASURED the target's altar at 2.26 horizontal-to-vertical grain energy
and set `MAP_ASPECT["veneer_altar"]` to match. The measurement of the artefact
being reproduced outranks generic trade theory — the same precedence CLAUDE.md
already fixes for statutory values, generalised. (The DR is also describing tall
door panels; grain run horizontally on a long low drawer front is ordinary.)
Not changed.

**NOT YET USED — leaf count and centre-balancing.** "Center-balanced, an even
number of equal-width leaves"; 4–8 leaves across 1 m, 8–12 across 2 m, leaves
152–305 mm. Our veneer is a stretched CC0 floor map with no leaf structure and no
mirror seams at all. This is the actual content of the outstanding rank-4 item
(altar veneer map replacement) and it is now specified well enough to build:
generate leaves at a measured pitch, mirror alternate leaves, centre the set.
Left unbuilt under R1 — the altar was already at its 2nd round.

**NOT YET USED — barber-pole.** Alternating tight/loose faces make a bookmatched
panel show alternating light/dark vertical bands that invert with viewing angle.
Testable against the target directly; not measured yet.
