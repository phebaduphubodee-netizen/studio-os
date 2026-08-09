# NLM DR + Gemini — sourced colour/reflectance anchors for cream · oak · black (REFERENCE tier)

**Tier:** REFERENCE. This unit is the intended promotion path for
`bsdf-material-presets.md` (whose own header forbids gating a deliverable until a
value is promoted with a named source) and the missing input to the ΔE00 gate.

**Fired:** 2026-08-08 on the owner's order, against queued topic 3.
**Notebook:** `941a2620-…` ("STUDIO palette anchors 2026-08-08"), **113 sources**.
**Second channel:** Gemini `gemini-2.5-pro` + google_search, **21 retrieved sources**
(`docs/research/2026-08-08-upgrade-dr/ANSWER_gemini_q3-palette-anchors_grounded.md`).

## The gap this closes was declared by the repo itself, three times

`color-composition.md:238` — no paint-system values (LRV/NCS/Munsell) in the colour
sources · `residential-materials.md:187` — no numeric LRV targets ·
`render-defaults.md §7` — roughness bands and F0 tables are do-not-invent GAPs.
Meanwhile `brand_delta_e00` is built, proven against Sharma 2005, and **has never
scored**, because the `--brand-palette` file it eats does not exist. This research
is that file's contents.

## ⚠ PROVENANCE

2 of the 113 NLM sources are the DR's **own synthesised report** (`MARKDOWN`,
`url: null`): *"Quantitative Modeling of Cream, White Oak, and Black Architectural
Palettes"*. The LRV/sRGB pairs below cite it as `[1]`. **Anything traceable only
to `[1]` is quarantined.** The answer did flag one internal discrepancy against a
retrievable source on its own, which is the behaviour the URL-mandatory prompt was
written to produce.

## The finding neither channel could have produced alone

**NLM: "NOT IN SOURCES"** for TOA, Beger, Jotun Thailand and Nippon Paint Thailand
— none of them appears in a 113-source corpus. **Gemini, searching the live web,
answered the Thai half** — and the structural answer is more useful than any single
number:

> **Thai paint brands publish sRGB/hex, and do NOT publish LRV.**

| brand | what is published | source |
|---|---|---|
| TOA `W9020` Creamy White | sRGB (243, 235, 209) `#f3ebd1`, **no LRV** | toagroup.com colour-details page |
| TOA `N6096` Glow Offwhite | sRGB (241, 232, 222) `#f1e8de`, **no LRV** | toagroup.com |
| TOA `8492` Classic Ivory | sRGB (238, 234, 219) `#eeeadb`, **no LRV** | toagroup.com |
| Beger BegerCool Super White | **LRV > 96**, tested to **BS 8493:2008+A1:2010** — no sRGB/NCS | beger.co.th |
| Jotun `1622` Reflection | LRV 80.70% — via a **third-party** database, not Jotun | hextoral.com |

That asymmetry decides the method: for Thai-market work the **sRGB is the primary
datum and the LRV must be derived from it**, not looked up. The reverse (LRV → sRGB)
is the path the international brands support.

## International anchors in the 75–90 LRV band (NLM, `[1]`-cited → quarantined pending trace)

Farrow & Ball Wimborne White No. 239 LRV 89.00 `#F4F0E5` · F&B Pointing No. 2003
LRV 88.19 `#F7F1E3` · Dulux Natural White SW1F4 LRV 85 `#EEECE5` · Dulux Antique
White SW1H7 LRV 84 `#EFEAE0` · Sherwin-Williams Alabaster SW 7008 LRV 82 `#EDEBE2`
· Benjamin Moore Swiss Coffee OC-45 LRV 81 `#EEECE1`.

Useful as a CROSS-CHECK on the LRV↔sRGB conversion rather than as our palette:
six independent (LRV, sRGB) pairs are six test cases for whatever formula we adopt.

## Still open in this unit

Oak veneer sRGB/roughness from scan-based libraries, powder-coat gloss-unit →
roughness conversion, brass complex IOR/F0, and the ΔE00 batch tolerance question
are all answered at length in both files and are **not triaged here** — the
materials round has not opened, and this lane's own ledger records that accepting
an item without evidence is more expensive than refuting one wrongly, because
nothing re-checks an accepted item.

**Before any value here is promoted:** trace it to a retrievable page, or derive
it and keep the derivation, as was done for the silhouette table in
`nlm-craft-cg-tells`.
