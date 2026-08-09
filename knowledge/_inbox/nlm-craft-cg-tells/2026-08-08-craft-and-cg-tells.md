# NLM DR — the craft layer: edges, shading, silhouette, contact, surface (REFERENCE tier)

**Tier:** REFERENCE. Not domain truth. Distil into `knowledge/rendering/` and
`knowledge/materials/` before any value here gates a deliverable.

**Fired:** 2026-08-08, by the builder, on the owner's order to spend both DR
channels — and independently on DR trigger 2: the CRAFT defect class was entering
its third build round with **no instrument in the lane able to score it.**
**Notebook:** `2e17f80e-…` ("STUDIO craft cg-tells 2026-08-08"), **104 sources**.
**Conversation turn:** 1. Full transcript: `qa-history.json` beside this file.

## Why it fired — the lane named this gap in its own voice

`training/TRN-002/triage-debt-2026-08-07.md` closes on the observation that every
critic item this lane DROPPED was a craft item — an edge, a surface, a glass, a
junction, a piece of hardware — and that *items a tool can score are always picked
up, while items only a person remembers are the ones that get lost.* Vault check
first: `bevel` appears in 10 knowledge files and `transmission` in 10, but
`shade_smooth`, `auto smooth`, `weighted normals` and `edge wear` appear in
**none**. The vault holds material and lighting values and no geometry-craft
values at all. That is a real gap, and it was searched in both the languages the
vault is written in.

## ⚠ PROVENANCE WARNING — READ BEFORE QUOTING ANYTHING BELOW

Two of the 104 sources are **the DR's own synthesised report**
(`SourceType.MARKDOWN`, `url: null`), titled *"Computational Aesthetics and
Perceptual Mechanics: What Separates Photorealistic Interiors from Synthetic
Renders"* — and it is the **most-cited source in the answer.** Cited in the same
format as a manufacturer datasheet, it reads exactly like one. It is the model's
own prose, one hop removed.

**Any value whose only citation is that title has no external attribution and
stays quarantined.** Detect it with `python pipeline/scripts/nlm_provenance.py
<notebook>`, which splits a notebook's sources into retrievable and synthesised.

## What survives, ranked by how well it is sourced

### A. VERIFIED AGAINST THE PRIMARY SOURCE — the strongest result of the run

*Rademacher, Lengyel, Cutrell & Whitted, **"Measuring the Perception of Visual
Realism in Images"**, EGRW 2001* — a real PDF in the notebook
(`cutrell.org/papers/EGRW2001-Rademacher-final_version.pdf`), pulled in full and
read directly rather than trusted through the DR:

| finding | number | statistic |
|---|---|---|
| perceived realism rises with shadow softness up to a **5.21° penumbra angle**; softer than that buys nothing | 5.21° | χ²=5.39, df=1, **p=.0203**; softest two levels not different (χ²=2.64, p=.1043) |
| **surface roughness beats shadow softness** as a realism cue | ℜ **.71 rough** vs **.39 smooth** | χ²=13.04, df=1, **p=.0003** — the paper says in its own words this effect "was stronger than the effect due to shadow softness" |
| more LIGHT SOURCES does not increase perceived realism | — | not significant |
| more OBJECTS, or more variety of object shapes, does not increase perceived realism | — | not significant |

n = 18 subjects per experiment; penumbra levels measured at .39°, 1.5°, 2.5°,
5.2°, 10.3°.

**Why this matters more than anything else here.** Our own ground-truth study
(2026-07-30) measured this repo's texture-map coverage at **4.9%** against
**50–66%** in five delivered photoreal `.blend` files. That was an in-house
observation about what other people do. This is an independent controlled
experiment saying the same cue is the **strongest** measured driver of the
"is it real" judgement — stronger than the shadow work, stronger than adding
lights, and unaffected by adding objects. Two lines of evidence, from completely
different directions, land on one lever.

And it reads the other way too: our area lights are 1600–3000 mm across at 2–5 m,
so their penumbra angles are already tens of degrees — far past 5.21°. **Softening
light further is not a lever for us; the paper says the return is flat above the
threshold.** So is adding lights or adding objects.

### B. SOURCED TO A REAL STANDARD — Architectural Woodwork Standards (AWI)

**Checked against the source's own text, not against the DR's summary of it**
(`notebooklm source fulltext d1c39041`, URL `awinet.org/standards/millwork-and-
wood-trim/…/3-4-aesthetic-6/`). The check mattered: two of the numbers the answer
presented beside an AWI citation are **not in AWI**.

**IN THE AWI TEXT, verbatim — promotable:**

| detail | value |
|---|---|
| sharp edges | *"Sharp edges shall be eased."* — a requirement |
| veneer / veneer-tape edgeband | minimum **.5 mm [.018"]** thick |
| HPDL / PVC / ABS edges | minimum **.5 mm [.018"]**, maximum **3 mm [.118"]** |
| PVC/ABS edgeband over **1 mm [.039"]** | *"shall be radiused or beveled on edges and corners"* |
| paint-grade visible edges | filled and sanded MDF, or paintable PVC/ABS/closed-grain veneer |

**NOT IN THE AWI TEXT — quarantined, they trace to the synthesised report:**
eased radius **3.2 mm (1/8")** for Premium/Custom · square edge **1.6 mm (1/16")**
· stone eased **3.0–5.0 mm**. The answer cited AWI and the synthesis in one
sentence, which is how a synthesised number acquires a standard's authority. It
was the citation this reader trusted most.

Our `EASE` bevel is **1.5 mm / 2 segments**, which sits mid-band inside the
standard's own 0.5–3 mm range for a visible cabinetry edge. **No retrievable
source says it is wrong**, and the earlier draft of this file said it did.

### C. DERIVED, NOT TRUSTED — the silhouette segment floor

The answer returned a segment table for D = 3000 mm citing the 1-arcminute acuity
limit — and cited it to the **synthesised** report, so by the rule above it was
quarantined. It was then **re-derived from geometry**:

    sag = R·(1 − cos(θ/2)),  θ = 2π/N     visible when   sag > α·D,  α = 1 arcmin

The closed form reproduces **all eight rows exactly** (R = 2.5/5/10/25/50/100/250/
500 mm → N = 4/6/8/12/17/24/38/54). A number that can be regenerated does not need
to be trusted, so this one is promoted while its citation is not.

**WIRED THE SAME DAY:** `pipeline/scripts/craft_check.py` (+13 tests, one of which
IS the eight-row table). Run against `spec_r31`: **13 of 16 rounded masses pass,
3 fail** — `petcave` (needs 9 segments, has 6), `bed_platform` (8 vs 6), `bench`
(8 vs 6). This corrects a claim in our own source code, which asserts that "every
arc in the frame renders as visible facets": at this camera, most do not.

### D. USEFUL BUT SYNTHESIS-CITED — quarantined until traced

- face-weighted normals with weights wᵢ = face area or corner angle; Bevel
  modifier's *Harden Normals* aligns split normals with adjacent base geometry
- smooth shading with no bevel produces the "pillowed"/"bulging" gradient across
  flat faces — the averaging tilts boundary normals with nothing to isolate them
- unbevelled 90° edges: adjacent same-material planes merge into one undifferentiated
  mass, losing the specular edge highlight, the self-shadow and the AO in the joint
- contact: sub-millimetre penumbrae, micro-occlusion in the contact crease, and
  the "Peter Panning" detachment when shadow bias is too high

These describe mechanisms we can verify ourselves in one render each. None is
quotable as a value.

### E. ANSWERED "NOT IN SOURCES" — and that is the useful answer

Blender bevel width for a 2–6 m camera · any rule tying segment count to the arc's
PIXEL width · production polygon counts for pillow / chair / lamp / curtain · the
dark line at a skirting · **any tool that scores craft from the MESH** (the corpus
holds image-space perceptual metrics only — HDR-VDP-2, visual-equivalence
predictors — and no mesh-side scorer).

That last one is worth stating plainly: **nothing off the shelf scores this. The
instrument had to be built, and now one of the five craft properties has one.**

## What this changes

1. `craft_check.py` — BUILT, tested, and already returning three real shortfalls.
2. **Surface variation is the ranked lever**, by an outside experiment and by our
   own ground-truth measurement. That is the materials lane's next round, and it
   outranks more light and more objects — both of which that experiment found do
   nothing.
3. The bevel bracket is NOT a change this research licenses — see B. The number
   that would have justified it did not survive being looked up.

**The method note worth keeping:** of the three headline numbers in this unit, one
was verified against a primary PDF (5.21°), one was re-derived from geometry (the
segment table), and one dissolved on contact with its own cited source (3.2 mm).
Three different fates, one procedure — go and read the thing the answer names.
