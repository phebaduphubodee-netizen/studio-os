# Plan READ + WRITE tooling — DR synthesis (2026-07-01)

**Question (founder):** เครื่องมือในการอ่าน plan และการเขียน plan — i.e. software tools/libraries/methods for
**reading** an existing floor plan / แปลน (DWG/DXF/PDF/scan → structured geometry) and **writing/generating** a
floor plan (dimensioned 2D "แบบ" + auto-layout), for our **headless, Python, $0-first, commercially-sellable** pipeline.

**Engines fired:** Gemini DR (Google-Search-grounded software landscape) + NotebookLM DR (drafting methods & standards, §7)
+ **two primary-source verification passes** (12-agent on Gemini's claims `wf_977834e0-fc9`; 4-agent on NLM's new tool
claims `wf_f6a11001-a59`).
**Raw:** `research/2026-07-01-plan-read-write-tools-gemini-DR.md` · `research/2026-07-01-plan-tools-nlm-DR-history.json`.

**Method note (why this is trustworthy):** every license verdict below was re-checked against the **primary source**
(PyPI classifier, the GitHub `LICENSE` file, or the vendor's own EULA/pricing page), not the DR's wording. That pass
**overturned 4 of Gemini's claims** — see §2. This honors the project rule "verify the shipped capability/license, not the marketing."

---

## 1. TL;DR (decision)

- **Your current spine is right and already the best $0 option:** `ezdxf` (MIT) + `IfcOpenShell` (LGPL-3.0) for the
  file I/O, your own pure-Python semantic layer on top. No better free library exists — the missing pieces are things
  **you build**, not things you're failing to install.
- **The two real gaps are both "build-yourself":** (A) turning parsed CAD lines into *rooms/walls* (semantic
  interpretation), and (B) generative auto-layout. There is **no production-grade $0 tool** for either.
- **One "buy" lane** if you ever need to read *scanned/photographed* plans at quality: CubiCasa (paid API) — but with caveats (§2).
- ⚠️ **One licensing landmine that touches your EXISTING pipeline:** the free **ODA File Converter** may be licensed
  **non-commercial-only** for non-members (a EULA/contract limit, not just copyright). You already depend on it in
  `dwg_ingest.py`. **Cleanest fix (verified): swap DWG ingest to GNU `LibreDWG`** — a mature $0 GPL-3 DWG reader run as a
  back-office CLI tool (its copyleft doesn't touch the drawings you output). Or just standardize on **DXF** (which
  `plan_2d.py` already emits) and skip DWG conversion entirely. (§2, §7a)
- **Do NOT use vision-LLMs to extract coordinates/dimensions** — verified "geometric hallucination"; use them only for
  semantic tagging, never geometry (§4.5). Adopt Gemini's **dimension chain-of-custody** idea to enforce this (§8).

---

## 2. Verified corrections (the load-bearing ones)

The verification pass CONFIRMED 8 claims and corrected 4. The corrections matter for money/legal:

| # | Claim (Gemini said) | Verdict | What's actually true | Why it matters |
|---|---|---|---|---|
| 1 | **ODA File Converter** = free, **commercial-use OK** | ⚠️ **REFUTED (commercial part)** | Free + headless CLI + not-OSS all confirmed, BUT the binding *ODA Community User Agreement* says non-members may use it for **non-commercial applications only** and may **not** "resell or distribute … as part of any commercial application." Commercial use → **paid ODA membership/SDK**. | **We depend on it now** (`dwg_ingest.py` DWG→DXF). Real open legal question for sellable deliverables — confirm with ODA directly; consider membership or an alternative DWG route. |
| 2 | **DeepFloorplan / R2V** = non-commercial (CC BY-NC) | **REFUTED (in our favor)** | **R2V** (`art-programmer/FloorplanTransformation`) = **MIT** → commercially safe. **DeepFloorplan** = **GPL-3.0** (copyleft — commercial OK but distribution triggers source-disclosure), not non-commercial. | R2V is actually a usable starting point if we ever build raster→vector. Gemini wrongly closed it off. |
| 3 | **House-GAN / Graph2Plan** = non-commercial research license | **REFUTED** | House-GAN/++ = **GPLv3** (copyleft). **Graph2Plan = no license file at all** (= all rights reserved). | The "avoid" conclusion stands (research-grade + copyleft/no-license), but for the *correct* legal reason. |
| 4 | **CubiCasa** = paid API, outputs SVG/**DXF**/IFC | **PARTIALLY_CONFIRMED** | Paid ✓ (per-scan A$15/30/99; APIs enterprise/"fees apply"). But **DXF export is NOT documented** (only JPG/PNG/SVG/PDF + BIM SVG/OBJ/IFC), the Conversion API converts **CubiCasa's own mobile-SDK scans** (not arbitrary uploads), and its free repo *CubiCasa5k* is **CC BY-NC** (barred from commercial use). | Less of a drop-in "buy" than implied. If we need scan→plan, scope it carefully and benchmark. |

**Confirmed as stated (safe to rely on):** `ezdxf`=MIT · `IfcOpenShell`=LGPL-3.0 (read+write IFC) · `PyMuPDF`=AGPL
(needs paid Artifex license *if our shipped product is closed-source*) · `pdfplumber`=MIT (deps also permissive) ·
`svgwrite`/`drawsvg`=MIT · `OR-Tools`=Apache-2.0 · VLM geometric-hallucination is real & documented · NCS incorporates
the AIA CAD Layer Guidelines (A-WALL / A-DOOR / A-ANNO-DIMS pattern).

---

## 3. Verified tool map

### READ (existing plan → structured geometry)

| Tool | License (verified) | Cost | Verdict | Note |
|---|---|---|---|---|
| **ezdxf** (+ `path`, `drawing` add-ons) | MIT | $0 | **ADOPT** | Foundational DXF parse. Gives raw entities only — no rooms/walls. |
| **ODA File Converter** (DWG→DXF) | Freeware, ⚠️ **non-commercial per EULA** | $0 (non-comm.) | **RESOLVE LICENSE** | We already use it. Commercial use likely needs paid ODA membership. |
| **IfcOpenShell** (read) | LGPL-3.0 | $0 | **ADOPT** (if IFC input appears) | Full semantic BIM: IfcWall/IfcSpace/IfcDoor/IfcWindow. |
| **pdfplumber** | MIT | $0 | **EVALUATE** | Vector-PDF line/text extraction; permissive. Reconstruction is on us. |
| **PyMuPDF (fitz)** | AGPL / paid Artifex | $0 or paid | **AVOID if closed-source** | Faster than pdfplumber but AGPL trap for a proprietary product. |
| **R2V** (raster→vector) | **MIT** | $0 | **EVALUATE** (research-grade) | Actually usable license-wise; accuracy is research-level. |
| **DeepFloorplan** | GPL-3.0 | $0 | **AVOID** (copyleft) | Source-disclosure risk on distribution. |
| **CubiCasa** (scan→plan) | Paid commercial | $$ | **BUY-only, scope carefully** | For scanned/photo plans. DXF export unconfirmed; free repo is NC. |
| **Vision-LLM** (GPT-4V/Claude/Gemini) | vendor terms | paid | **AVOID for geometry** | Semantic tagging only — hallucinates coordinates (verified, §4.5). |

### WRITE (spec → professional plan)

| Tool | License (verified) | Cost | Verdict | Note |
|---|---|---|---|---|
| **ezdxf** | MIT | $0 | **ADOPT** | Our core drafting engine (already in `plan_2d.py`). Dimensions/layers/blocks/hatch. |
| **ODA File Converter** (DXF→DWG) | ⚠️ non-commercial EULA | $0 | **RESOLVE LICENSE** | Only if a client demands native DWG. Same landmine as READ. |
| **IfcOpenShell** (write) | LGPL-3.0 | $0 | **EVALUATE** | BIM/IFC deliverable = heavy lift; defer until a client needs it. |
| **svgwrite / drawsvg** | MIT | $0 | **EVALUATE (previews only)** | Not a CAD format — never the final CD. |
| **OR-Tools** (layout solver) | Apache-2.0 | $0 | **EVALUATE (build)** | For constraint-based auto-layout — the engine, not the architecture logic. |
| **House-GAN / Graph2Plan** | GPLv3 / no-license | $0 | **AVOID** | Research-grade + copyleft/no-license; non-constructible output. |

---

## 4. Reading a plan — routes & failure modes

- **4.1 Vector CAD (DWG/DXF) — our primary path.** `ezdxf` parses entities; **semantic extraction (walls, rooms,
  openings) is on us**: layer heuristics (`A-WALL`, `A-DOOR`), block/INSERT name matching to a known-symbol library,
  wall-centerline **boundary tracing** (graph/flood-fill) to detect enclosed rooms, then spatial text-association for
  labels. This is the #1 gap (§7). Our concrete open task: turn an *ingested* DWG (`dwg_ingest.py`, block/INSERT-based,
  unit-calibrated) into a room-spec **without fabricating coordinates**.
- **4.2 IFC/BIM.** `IfcOpenShell` gives semantics directly (no tracing needed). Best input *if* we can get it.
- **4.3 Vector PDF.** `pdfplumber` (MIT) exposes lines/rects/text; walls arrive as many disconnected segments →
  reconstruction is a real engineering cost. Avoid `PyMuPDF` for a closed-source product (AGPL).
- **4.4 Raster / scanned.** Open-source ML is research-grade (R2V=MIT usable, DeepFloorplan=GPL). For quality, CubiCasa
  is the paid route (scope caveats in §2). Not needed unless clients send scans/photos.
- **4.5 Vision-LLM — do NOT trust for geometry.** Verified across sources ("geometric hallucination"; probabilistic
  tokens conflict with deterministic precision). Fine-tuned/purpose-built vectorizers reduce it, but **off-the-shelf
  Claude/GPT-4V/Gemini fabricate plausible-but-wrong coordinates.** Use only to *tag* rooms already found geometrically.
- **4.6 Scale/unit.** `$INSUNITS` header first (we do this); fall back to a **witness dimension** (text value ÷ measured
  line length). The cm/mm/inch trap is already guarded in `dwg_ingest.py::unit_mm`.

## 5. Writing a plan — routes

- **5.1 2D CD "แบบ".** `ezdxf` is correct and already in use (`plan_2d.py`). To look professional, encode: NCS layering,
  line-weight hierarchy (walls heaviest → furniture lightest), standard **symbols as reusable blocks**, chained
  dimensions snapped to centerlines/wall-faces, a title block. (Standards detail in §7.)
- **5.2 Native DWG / IFC.** DWG via ODA (⚠️ license) only on client demand; IFC via IfcOpenShell is a separate major feature.
- **5.3 Auto-layout.** Classical **constraint/optimization** (OR-Tools: rectangle packing + adjacency constraints) is the
  viable build path — mathematically optimal but "architecturally naive," so seed it with clearance/adjacency rules from
  Panero-Zelnik / Karlen (which we already encode in `clearance_check.py` + `dimensional_rules.json`). ML generative = avoid.

## 6. Standards a plan must honor (to be taken seriously)

- **Layering:** US **National CAD Standard (NCS)**, which incorporates the **AIA CAD Layer Guidelines**. Format is
  *discipline–major–minor–minor–status* (e.g. `A-WALL`, `A-DOOR`, `A-ANNO-DIMS`; `AI-` prefix = Architectural Interiors).
  No library enforces this — our writer must emit correct layer names. ⚠️ caveat: `ANNO` major-group breaks ISO-13567 if that's ever required.
- **Line weights** convey hierarchy (walls heaviest). **Symbols** standardized as blocks. **Dimensioning**: chained,
  snapped to significant features. **Title block** on every sheet. (We already do most of this; the gap is NCS-compliant layer names + a block library.)

---

## 7. NotebookLM DR — drafting methods & professional standards

NLM (fresh notebook `58051acf…`, cited web sources) corroborated §4–§6 and added new, decision-relevant material.
Raw: `research/2026-07-01-plan-tools-nlm-DR-history.json`.

### 7a. New READ tools — **verified** (delta-verify `w2xfx7vn1`)

> **The load-bearing distinction (read this first).** Our pipeline is a **back-office drawing factory**: we RUN these
> tools to produce drawings (DXF/PDF/renders) that we sell. **GPL copyleft attaches to *redistributing the software*,
> not to the drawings it outputs** (a floor plan is our data, not a derivative of the tool's code — standard FSF
> position). So a GPL CLI tool run at arm's length, and **not bundled/redistributed inside a shipped product**, is
> generally fine for commercial use. The tools' "NO for closed-source distribution" verdicts below assume the *worst
> case* (linking the code into a shipped binary) — which is **not our model**. *(Not legal advice; confirm the
> no-redistribution posture before relying on it.)*

- **GNU `LibreDWG` — the real ODA escape hatch for INGEST.** Verified **GPL-3.0-or-later**; the **reader is mature —
  reads *all* DWG versions** (only some advanced R2010+ objects skipped), writer is partial. Under the back-office model
  above, this is a **viable $0 replacement for the ODA File Converter for DWG *reading*** (we don't redistribute it).
  → **Next step: capability-test it on the friend's real `.dwg` vs the current ODA output.** This sidesteps the §2 ODA
  EULA question for ingest.
- **`libdxfrw` — do NOT rely on for DWG.** Verified GPL-2.0-or-later, and its DWG reading is **"rudimentary" (the
  project's own word)** — not a robust reader. Fine for DXF, not a DWG solution.
- **Vector PDF:** `pstoedit` — verified **GPL-2.0**, and its **DXF + SVG drivers are FREE built-ins** (the "paid plugin"
  worry was REFUTED; only unrelated MS-Office/other plugins are paid). Usable as a back-office CLI (depends on Ghostscript,
  which is AGPL — same back-office logic). · `Inkscape CLI` (PDF→DXF via SVG, but loses layer hierarchy + splits arcs) ·
  `Apryse/PDFNet` (commercial, high-fidelity). `Teigha/ODA SDK` = the paid production-grade DWG route if we ever need writes.
- **Raster ML models (research metrics, NLM-sourced — UNVERIFIED, not adopting):** `MitUNet` (89.12% mIoU on CubiCasa5K,
  "production-ready" per NLM — *treat "production-ready" skeptically*; fails on non-standard hatch + angled walls) ·
  `FloorSAM` (SAM-based zero-shot room boundary) · `TF2DeepFloorplan` (legacy) · `FloorplanVLM` (research VLM, 92.52%
  external-wall IoU **but coordinate drift/hallucination on low-contrast lines** — independently corroborates §4.5).

### 7b. New WRITE tools

- **`Shapely` — verified BSD-3-Clause, ADOPT.** Production-stable 2D computational geometry: polygon area, boundary
  offsets/buffers, boolean ops. **The one unambiguous clean permissive add.** (Its GEOS engine is LGPL-2.1 — keep it as
  the default dynamically-linked wheel, don't static-link/strip its notice.) **Directly useful** for room-boundary math (§4.1) and future auto-layout.
- **`IfcOpenShell.draw`** — projects a 3D model to 2D sheets with hidden-line removal, exports SVG/DXF (useful if we go BIM).
- **`svg2plan`** — cleans raw SVG sketches into overlap-free geometry (JSON).
- **Layout:** MILP solvers (**OR-Tools** ✓Apache, SCIP, Gurobi[paid]) — "scales exponentially, intractable for complex
  geometries" (matches §5.3). ML generative (research-only): House-GAN/++, **HouseDiffusion** (handles slanted walls +
  solar orientation), **LLM+RLVR** (RL with verifiable rewards penalizing overlaps).

### 7c. Professional drafting STANDARDS (the actionable gold — encode these in our generators)

*Convention, not software — no verification needed. This is what makes a generated "แบบ" look professional.*

- **Layer names + plot line-weights (NCS/AIA):** `A-WALL-FULL` 0.50–0.60mm · `A-DOOR` 0.25–0.35mm · `A-GLAZ` (windows)
  0.25mm · `A-ANNO-DIMS` / `A-ANNO-TEXT` (dims/notes, extra-light).
- **Line-weight hierarchy** (floor-plan cut plane @ **4 ft / 1.2 m**): Extra-Heavy 0.70–1.00mm (borders/property) ·
  Heavy 0.50–0.60mm (cut structural / exterior walls) · Medium 0.35–0.40mm (uncut: doors, stairs, casework) ·
  Extra-Light 0.13–0.18mm (dimensions, grid, hatch/poché).
- **Symbols:** walls = heavy outline + poché fill · door = thin leaf line + fine quarter-circle **swing arc** (we do this) ·
  window = **three parallel lines** in the opening · stairs = tread lines + direction arrow + "UP/DN" · structural grid =
  extra-light centerlines ending in lettered/numbered bubbles.
- **Dimensioning — 3 concentric tiers** (unbroken continuous strings): **Inner** = individual openings/offsets ·
  **Middle** = structural grid / wall transitions · **Outer** = overall building width. Extension line: **1/16″ (1.5mm)
  gap** from the object, extend 1/16″ past the dim line. Text height **exactly 3/32″ (2.5mm)** (legible when 24×36 → 11×17).
  Round to nearest 1/8″.
- **Scale:** 1/4″ = 1'-0″ residential, 1/8″ = 1'-0″ commercial. Put a **graphic scale bar on every sheet** (survives photocopy/rescale).
- **Complete CD set:** dimensioned floor plans (walls, doors, windows, stairs, dims, room labels) + elevations + section
  cuts + material-symbol legend + structural grid IDs + title block w/ project data + graphic scale. *(We already produce
  most of this in `suite_package.py` — the gaps are NCS-compliant layer names, the 3-tier dimensioning, and exact line weights.)*

---

## 8. Concrete implications for our pipeline

1. **The #1 build target = the DWG→spec semantic layer** (`dwg_ingest.py` is a *reader* today; it deliberately stops
   before fabricating coordinates). Build room-boundary tracing + block→symbol matching on top of ezdxf, human-verified.
2. **Adopt dimension chain-of-custody** (Gemini's best idea, and it operationalizes our "never fabricate coordinates"
   rule): tag every coordinate `source: as-built` (read from a real DWG) / `generated` (our layout engine) /
   `unreliable_annotation` (any VLM tag) — and **block `unreliable_annotation` geometry from ever entering a CD.**
3. **Enforce NCS layer names in the writer** — replace `plan_2d.py`'s ad-hoc `LAYERS` map (`WALLS`, `FURNITURE`, `DOOR`,
   `DIMENSIONS`) with NCS-compliant names (`A-WALL`, `I-FURN`/`A-FURN`, `A-DOOR`, `A-ANNO-DIMS`).
4. **Build a standardized block library** (door swings, windows, plumbing fixtures) as reusable DXF blocks, inserted not redrawn.
5. **Enrich the room-spec** toward Gemini's schema: explicit `boundary_polygon`, `openings[]` (type/wall/width/height),
   `required_clearances` (already have via `dimensional_rules.json`), `required_adjacencies` (feeds a future OR-Tools layout).
6. **Resolve the ODA license question** before any commercial ship — it gates both DWG ingest and DWG output. Verified
   options, best-first: **(a)** swap DWG *ingest* to **GNU `LibreDWG`** (mature $0 GPL-3 reader, back-office CLI — copyleft
   doesn't touch output drawings), pending a capability test on the friend's real `.dwg`; **(b)** standardize on **DXF**
   (already emitted by `plan_2d.py`) so no DWG conversion is needed; **(c)** buy an ODA membership only if a client
   hard-requires native DWG *output*. (`libdxfrw` rejected — its DWG read is "rudimentary.")
7. **Upgrade the 2D generator to professional convention** (from §7c): the **3-tier dimensioning** (inner openings /
   middle grid / outer overall), the **line-weight hierarchy** (walls 0.50–0.60mm heaviest → dims 0.13–0.18mm lightest),
   text height 3/32″, and a **graphic scale bar on every sheet**. These are concrete, encodable numbers for
   `plan_2d.py` / `suite_plan.py`.
8. **Add `Shapely`** (verified BSD-3) for room-area/offset/boolean geometry — cleaner than hand-rolled math for boundary
   tracing (§4.1) and future auto-layout.

---

## 9. Open questions / DR triggers (surfaced proactively)

- **ODA commercial licensing** — largely resolved by §7a: the mature $0 **LibreDWG** back-office path avoids the ODA EULA
  for ingest. Remaining action = **capability-test LibreDWG on the friend's real `.dwg`** vs current ODA output; if it
  matches, retire ODA from `dwg_ingest.py`. Only reopen the ODA-membership question if a client hard-requires native DWG *output*.
- **Is native DWG (not DXF) actually required by the friend's clients?** If DXF suffices, the ODA landmine largely disappears.
- **Do we ever need to read scanned/photo plans?** If the friend always has the CAD source, the whole raster/CubiCasa lane is moot.
- Whether to invest in the DWG→spec semantic tracer now, or keep DWG ingest human-verified until a real client volume justifies it.
