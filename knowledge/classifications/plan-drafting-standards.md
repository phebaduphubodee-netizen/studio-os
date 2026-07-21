# มาตรฐานการเขียนแบบ (ฝั่งเขียน) / Plan drafting standards — the WRITE-side convention (REFERENCE)

> PROVENANCE: promoted 2026-07-13 from `knowledge/_inbox/interior-ai/2026-07-01-plan-read-write-tools-DR.md`
> §6 (lines 111–117) and §7c (lines 163–182), plus §4.5 (lines 95–97) and §8.2 (lines 190–192).
> §7c originates from a **NotebookLM DR** ("fresh notebook `58051acf…`, cited web sources",
> source line 123) and the source itself labels that section *"Convention, not software — no
> verification needed"* (line 165) — i.e. it was **not** put through the primary-source
> verification pass that the DR's license claims were.
> **Tier: REFERENCE — strong-but-unaudited.** Not Authority, not statutory.
> This file holds **no statutory values**; `knowledge/codes-th/` remains the sole source of
> Thai law (setbacks, ceiling heights, MR55 dimensions) and outranks everything here.

**Foreign-reference warning (read before using any number below).** Everything in §7c of the
source is **US convention** — the National CAD Standard (NCS), which incorporates the AIA CAD
Layer Guidelines (source line 113), authored in **imperial** units. It is promoted here as a
**foreign professional reference**, NOT as a standard applicable in Thailand. For a Thai
deliverable the Thai professional standard governs: see
`knowledge/classifications/thai-cad-layers-asa2554.md` (ASA มาตรฐานการเขียนแบบก่อสร้าง พ.ศ. 2554,
บทที่ 6), which was verified against the primary PDF and whose pen widths **conflict** with the
US numbers below — the conflict is tabulated in §1.

**Why this file exists:** the reader side (2D → geometry) is covered by the layer/symbol tables;
this is the **writer** side — what a generated "แบบ" must look like to be taken seriously by a
Thai contractor or client. The writers that must honour these values carry their weights as
hard-coded integers in `pipeline/scripts/plan_2d.py` (`LAYERS`, lines 44–51) and
`pipeline/scripts/suite_plan.py` (`LAYERS`, line 52); this file is the citable rule behind them.

---

## 1. Line-weight hierarchy — and its conflict with ASA 2554

The source ties the hierarchy to the **floor-plan cut plane at 4 ft / 1.2 m** (source line 169;
4 ft = 1.2192 m — the source rounds to 1.2 m). In the source's own terms: **cut** elements are
drawn Heavy, **uncut** elements Medium. The source gives no mechanism beyond those two words; do
not gloss it further.

| Band | Weight (source, mm) | Applies to |
|---|---|---|
| Extra-Heavy | **0.70–1.00** | sheet borders, property lines |
| Heavy | **0.50–0.60** | cut structural / exterior walls |
| Medium | **0.35–0.40** | uncut: doors, stairs, casework |
| Extra-Light | **0.13–0.18** | dimensions, structural grid, hatch / poché |

*(source lines 169–171, verbatim bands)*

Per-layer plot weights the source gives separately (line 167–168):

| Layer | Weight (source, mm) |
|---|---|
| `A-WALL-FULL` | 0.50–0.60 |
| `A-DOOR` | 0.25–0.35 |
| `A-GLAZ` (windows) | 0.25 |
| `A-ANNO-DIMS` / `A-ANNO-TEXT` | "extra-light" (no mm given) |

⚠️ **Internal inconsistency in the source, recorded not resolved.** The per-layer list puts
`A-DOOR` at 0.25–0.35 mm (line 167) while the band table puts uncut doors in Medium 0.35–0.40 mm
(line 171). The two overlap only at 0.35 mm. Do not silently pick one; if a value is needed,
0.35 mm is the only figure both lines admit.

⚠️ **Conflict with the Thai standard.** The two pen sets disagree, and they disagree **row by row,
not uniformly**. Both sets, tabulated (ASA rows from `thai-cad-layers-asa2554.md:23-24, :27,
:34-36, :49-50, :57`):

| Row | ASA 2554 pen | US value above | Relation |
|---|---|---|---|
| exterior wall (`A-WALL-FULL-EXTR`) | **0.35** mm | Heavy band 0.50–0.60 mm | US ~1.4–1.7× the ASA pen |
| interior wall (`A-WALL-FULL-INTR`) | **0.25** mm | (no US interior-wall row) | — |
| glass (`A-GLAZ-FULL`) | **0.25** mm | `A-GLAZ` 0.25 mm | equal |
| A- furniture (`A-FURN-FREE`) | **0.25** mm | (no US furniture row) | — |

So ASA is **not** thinner across the board, and these rows are why:

- `A-DOOR-PRHT` = **0.35** mm (`thai-cad-layers-asa2554.md:34`) — *equal to*, not below, the top of
  the DR's `A-DOOR` 0.25–0.35 mm.
- On an **I- (interior) sheet** — this studio's sheet type — `I-FURN-FREE` and `I-FURN-SEAT` are
  **0.35** mm (`:49-50`), i.e. *inside* the US Medium band 0.35–0.40, not thinner than it.
- A grade-level tree `L-PLNT-TREE` = **0.5** mm (`:57`).

**There is no ordering invariant to carry across — resolve the DISCIPLINE first.**
`thai-cad-layers-asa2554.md`, "What the reader may and may not infer", item 4 (`:81-88`) is
explicit: the ordering *exterior wall (0.35) > interior wall = glass = furniture (0.25) >
sills/annotation (0.18/0.13)* holds **"only on an A- sheet"**; on an I- sheet "I-FURN-FREE and
I-FURN-SEAT are **0.35** — the same pen as A-WALL-FULL-EXTR", and "an interior sheet is exactly
the sheet type this studio works from". The same item calls `A-DOOR-PRHT` "a second 0.35 non-wall
row inside the A- discipline itself" (`:88`) — so even on an A- sheet an *uncut door* carries the
exterior-wall pen. Do not treat "cut wall > uncut door > annotation" as an invariant: neither
source states it, and ASA's rows contradict it.

**Which pens govern.** For a Thai-delivered sheet, take the absolute pens from ASA 2554; the US mm
values here apply only when a client explicitly asks for an NCS-conformant set. (Real-sheet
deviation from the ASA pens: same file, "What the reader may and may not infer", item 5 — "Real
sheets deviate from ASA pens" (`:89-93`) — calibrate per sheet, never assume.)

**Implementation note.** ezdxf restricts `lineweight` to the DXF line-weight enum;
`pipeline/scripts/plan_2d.py` lines 42–43 records that enum as "(…,18,25,30,35,40,50,…)" — so
arbitrary intermediate values are not expressible. The ellipses are the source comment's own:
before plotting a band value outside that listed range (0.13, or 0.60–1.00), check the DXF
line-weight enum itself — plan_2d.py does not enumerate them.

---

## 2. Layer naming (NCS / AIA — foreign reference)

- Format: **discipline–major–minor–minor–status** — e.g. `A-WALL`, `A-DOOR`, `A-ANNO-DIMS`.
  The **`AI-` prefix = Architectural Interiors** (source lines 113–115).
- NCS **incorporates** the AIA CAD Layer Guidelines (confirmed in the source's verification pass,
  line 49–50).
- ⚠️ Caveat the source itself raises (line 115): the **`ANNO` major group breaks ISO-13567**, if
  ISO-13567 is ever required.
- No library enforces layer naming — "our writer must emit correct layer names" (line 115).

For Thai work the ASA 2554 layer table (`A-WALL-FULL-EXTR`, `A-GLAZ-FULL`, `A-FURN-FREE`, …) is
the citable one; the NCS format above is the fallback/foreign convention and is what the shipped
`LAYERS` maps currently approximate.

---

## 3. Dimensioning — 3 concentric tiers

The source prescribes **three concentric tiers of unbroken continuous dimension strings**
(source lines 175–178):

| Tier | Carries |
|---|---|
| **Inner** | individual openings / offsets |
| **Middle** | structural grid / wall transitions |
| **Outer** | overall building width |

Mechanics (source lines 176–178, imperial-native — metric conversions are exact arithmetic on the
source's own fractions):

| Rule | Source value | Exact metric |
|---|---|---|
| Extension-line gap from the object | 1/16″ | 1.5875 mm (source writes "1.5mm") |
| Extension line extends past the dim line | 1/16″ | 1.5875 mm |
| Text height — the source says **exactly** 3/32″ | 3/32″ | 2.38125 mm (source writes "2.5mm") |
| Round dimensions to nearest | 1/8″ | 3.175 mm |

Rationale the source gives for the text height: it stays **legible when a 24×36 sheet is reduced
to 11×17** (line 177). That is the only rationale offered; no other reason is supplied here.

**Honest carry-over limit.** "Round to nearest 1/8″" is an imperial-paper habit. This repo authors
in millimetres (`suite_plan.py` sets `doc.units = MM`). Do **not** invent a millimetre rounding
increment from it — the source gives none. Carry over the *tiering* and the *unbroken-string* rule;
leave the rounding increment as an open question (§7).

Also from the source's §5.1 (lines 104–105): dimensions should be **chained** and **snapped to
centerlines / wall faces**, not free-floating.

---

## 4. Symbol conventions (plan view)

| Element | Convention (source lines 172–174) |
|---|---|
| Wall | heavy outline + **poché** fill |
| Door | thin leaf line + **fine quarter-circle swing arc** |
| Window | **three parallel lines** drawn in the opening |
| Stairs | tread lines + **direction arrow** + "**UP**" / "**DN**" |
| Structural grid | **extra-light centerlines** terminating in **lettered / numbered bubbles** |

Symbols should be emitted as **reusable blocks** (inserted, not redrawn) — source lines 116–117
and 195.

---

## 5. Scale and the scale bar

- **1/4″ = 1'-0″ residential** (= 1:48 exactly) · **1/8″ = 1'-0″ commercial** (= 1:96 exactly)
  — source line 179. These are the US imperial ratios; the source names no metric ratio.
- **A graphic scale bar on EVERY sheet** — the source's reason: it *"survives photocopy/rescale"*
  (line 179). A printed ratio does not; a drawn bar does.

---

## 6. Provenance discipline for any dimension printed on a sheet

Two rules from the source that govern *what may legally be drawn as a dimension*:

- **Dimension chain-of-custody** (source lines 190–192): tag every coordinate with its source —
  `as-built` (read from a real DWG) · `generated` (our layout engine) · `unreliable_annotation`
  (any VLM tag) — and **block `unreliable_annotation` geometry from ever entering a CD**. The
  source presents this as an idea to *adopt* ("Adopt Gemini's dimension chain-of-custody idea",
  line 32), not as an established industry standard; it is recorded here as studio doctrine, not
  as external convention.
- **Never use an off-the-shelf vision-LLM for coordinates or dimensions** (source lines 95–97).
  The source calls this "geometric hallucination" and reports it as verified across sources:
  off-the-shelf Claude / GPT-4V / Gemini "fabricate plausible-but-wrong coordinates". Vision-LLMs
  may be used **only to tag rooms already found geometrically** — semantic tagging, never geometry.

---

## 7. Open questions (not answered by the source — do not invent)

- The metric scale ratios a Thai sheet actually uses (the source gives only imperial 1:48 / 1:96).
- The millimetre rounding increment that replaces "nearest 1/8″" on a mm-authored sheet.
- The `A-DOOR` weight, given the source contradicts itself (0.25–0.35 vs 0.35–0.40 mm).

---

## Related
- `knowledge/classifications/thai-cad-layers-asa2554.md` — the Thai layer/pen/colour table (verified
  against the primary ASA PDF); it **outranks** the US values here for Thai deliverables.
- `knowledge/classifications/cd-set-anatomy.md` — CD *set* anatomy (which sheets exist); this file
  covers how each sheet is *drawn*. For reference, the source's own complete-CD-set list (lines
  180–182) runs: dimensioned floor plans (walls, doors, windows, stairs, dims, room labels) +
  elevations + section cuts + **material-symbol legend** + **structural grid IDs** + title block
  with project data + **graphic scale**.
- `pipeline/scripts/plan_2d.py`, `pipeline/scripts/suite_plan.py` — the writers whose `LAYERS` maps
  and dimension emission these values govern.
- `knowledge/_inbox/interior-ai/2026-07-01-plan-read-write-tools-DR.md` — source. Only its
  drafting-convention half (§6, §7c, plus §4.5 / §8.2) is in scope for this file. The source's
  software-licensing half (§2 / §3 / §7a / §7b: ezdxf, ODA File Converter, LibreDWG, pstoedit,
  Shapely, PyMuPDF) is tooling/legal material rather than design-domain truth, and belongs in
  `docs/`, not in `knowledge/` — this file makes no claim about it either way.
