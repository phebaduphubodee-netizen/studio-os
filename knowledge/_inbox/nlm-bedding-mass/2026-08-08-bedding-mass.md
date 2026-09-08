# NLM DR — bedding mass and drape feedstock (REFERENCE tier)

**Tier:** REFERENCE, and **partly quarantined** — see the provenance note.
**Fired:** 2026-08-08, on the owner's order to spend both DR channels, against the
queued entry the 2026-08-04 triage wrote (topic 2). Its stated fire condition —
*"at the cloth/materials phase OPENING, before the first duvet bake"* — is past.
**Notebook:** `766052cb-…` ("STUDIO bedding mass 2026-08-08"), **139 sources**.
**Conversation turn:** 1. Transcript + provenance: `qa-history.json`.

## Why it fired, and why it is a NEW unit

The triage doc had already done the dedup and refuted the obvious shortcut:
`knowledge/_inbox/nlm-cloth-closedtube/` contains **zero** bedding content — it is
closed-tube garment-sim mechanics and nothing else — and its distilled child's own
Gaps section says "nothing on materials other than cotton-like wovens". The
consumer is named: the r5 R1 halt reclassified the duvet as free-form drapery, and
`drape.py`'s FABRIC table describes itself as retuned Blender defaults, i.e. the
exact untraced prior this research exists to replace.

## ⚠ PROVENANCE — which half of the answer is real

Two of the 139 sources are the DR's **own synthesised report**
(`SourceType.MARKDOWN`, `url: null`), titled *"Physical and Computational Modeling
of Bedding Systems: Characterization of Thermal, Structural, and Mechanical
Properties"*. The headline tog → GSM → loft tables cite it.

**Split the claim in two, because the two halves have different standing:**

- the **GSM bands by season/fill** are independently corroborated by retrievable
  retailer sources in the same answer (Mattress Miracle CA; Morgan & Reid AU/NZ),
  which agree closely — those may be staged as REFERENCE
- the **settled-loft-in-millimetres column** — the part this lane actually needs,
  because millimetres are what a mesh is built from — traces **only** to the
  synthesis. **Quarantined.** It is not a measurement; it is the model's own
  arithmetic, dressed as a table.

## The numbers, marked

| fill | band | fill weight (g/m²) | settled loft (mm) |
|---|---|---|---|
| goose down 700+FP | 1.0–4.5 tog | 150–200 ✔ corroborated | 15–25 ⚠ synthesis-only |
| goose down 700+FP | 7.5–10.5 tog | 300–400 ✔ | 45–60 ⚠ |
| goose down 700+FP | 12–15 tog | 450–550 ✔ | 65–85 ⚠ |
| wool | 8–14 tog equiv | 600 ⚠ | 15–22 ⚠ |
| microfibre | 7.5–10.5 tog | 350–500 ✔ | 30–45 ⚠ |
| microfibre | 12–15 tog | 500–700 ✔ | 45–65 ⚠ |

Feather: **NOT IN SOURCES**.

## What to do with it

The queue's own vehicle note put **measurement first and research second**, and
that ordering survives this answer intact — arguably it is now the only honest
route, because the column we need is the quarantined one. Drop, stack height,
slump and turn-back are all measurable locally from the anchor corpus with the
live backprojection sweep, at zero cost. **Measure those; use the GSM bands only
to sanity-check the class of duvet the target shows.**

Read the full answer before the first bake — sections 4–8 (drop conventions,
pillow slump under head load, areal weight and bending rigidity → solver mass, the
quilted/baffle-box representation, hotel turn-back proportions) are richer than
this summary and were not triaged here, because the cloth phase is not open yet
and triaging a phase that has not started is how items get accepted without
evidence.
