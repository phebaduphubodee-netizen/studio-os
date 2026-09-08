# DR PLAN — furniture recognition from dense 2D floor plans (the fusion/detection wound)

**Status:** PLAN only (not executed — DR is ask-tier/paid; greenlight before running).
**Date:** 2026-07-10 · **Owner of question:** the recurring reader ceiling across the whole
2D→3D lane · **Interpretation of "เรื่องนี้":** how to auto-detect + instance-separate + classify
furniture symbols in dense 2D architectural plans (vector CAD/PDF), where pieces are drawn flush
against walls and each other (fusion) and identity labels are outlined/absent — and whether SOTA
changes our owner-signed-placement equilibrium. (Say the word if you meant a broader/narrower topic.)

## Why (the gap this DR must fill — do NOT re-run what we know)

Already measured, don't repeat (see `docs/research/2026-07-06-paired-2d3d-backlearn.md`, the wall/
symbol/blind lanes, and today's `floor2_v5-furniture-note.md`): the wound is DETECTION MASS from
FUSION — dense furniture merges and is screened/dropped; size+curve priors fail at identity;
FloorPlanCAD ~60% of furniture misses are the reader's own detection; on the studio's own sheet the
bed+headboard+wardrobe merge into a dropped blob (0–2 fragments). **The GAP is METHODS**: our prior
research was corpus/adapter-focused; it never surveyed the SOTA on *separating + typing fused furniture
symbols*. That is this DR.

## Refined question + sub-questions (for a `deep-research`-style fan-out)

**Q0 (headline):** What is the state of the art for detecting, instance-separating, and classifying
furniture/fixture symbols in dense 2D floor plans, and which techniques are transferable to a
vector-PDF + owner-signed pipeline — or does the evidence confirm human-in-the-loop as the equilibrium?

1. **SOTA methods & numbers.** Panoptic/instance segmentation, symbol spotting, GNN-on-primitives
   (CADTransformer, GAT/GCN on the CAD graph), raster-to-vector, transformer detectors — reported
   furniture **detection recall/precision** on FloorPlanCAD / CubiCasa5K / R2V / SESYD, *specifically
   for furniture* (not walls/rooms, which are easier).
2. **Fusion / dense separation specifically.** How does SOTA separate symbols drawn flush against
   walls and each other — learned instance embeddings, watershed/energy, part-based, panoptic stuff-vs-
   thing? Any method that explicitly targets overlapping/contiguous symbols? Measured gain vs a
   morphology clusterer like ours?
3. **Identity WITHOUT text labels.** When labels are outlined/absent, how is a symbol TYPED —
   geometry-only, learned embeddings, room-context priors, or **retrieval against a symbol library**
   (we have a BF## built-in catalog to key on)? What beats size+curve priors (which we proved fail)?
4. **Vector-native vs raster.** Do methods operating on CAD primitives/paths beat raster CNNs for
   this (we have vector PDFs)? Evidence from CADTransformer / primitive-graph GNNs.
5. **Industry equilibrium (the honesty check).** What do commercial plan-digitizers / BIM-from-PDF /
   takeoff / real-estate plan-AI products actually ship — full auto or human-assisted review? Does
   anyone credibly claim reliable *dense-furniture* auto-read, or is owner-signed-assist the industry
   norm (which would CONFIRM our two-layer thesis rather than refute it)?
6. **Transfer shortlist.** Rank 3–5 concrete, implementable techniques by (effort on our vector-PDF +
   owner-signed stack) × (expected recall gain on the fused/dense case), each with a kill-criterion.

## Method

Fan-out per sub-question across two lanes → deep-read top sources → **adversarially verify** each
headline number (is the recall on DENSE furniture or isolated? vector or raster? does it need labels
we don't have? train/test leakage?) → synthesize a ranked report + a go/no-go recommendation
(invest in method X, or confirm owner-signed-assist as the equilibrium and stop chasing auto-read).

## Lanes (recommended)

- **PRIMARY: `deep-research` skill (web fan-out + adversarial verify)** — papers, GitHub, product docs.
- **AUGMENT: `scite` MCP** — peer-reviewed CV/document-analysis literature with citation verification
  (avoids fabricated cites; check retractions).
- **NOT NotebookLM** — the a5a43395/79476082 corpora are DESIGN-THEORY + lighting, not CV methods;
  wrong tool here. (If a design-theory angle ever emerges, NLM per the research-lane rules.)
- **Vault first?** `knowledge/` holds codes/design, not CV methods → genuine external gap; skip vault.

## Privacy guardrails (HARD — enforce on every query)

Generic CV topic → naturally safe, but: **no** client name (K.NUT), project id, "The City …",
building name, specific dimensions, or the actual plan/PDF in ANY external query. Ask about "furniture
symbol recognition in floor plans" in the abstract only; round any of our numerics to bands. The DR
never sees `projects/` or `clients/` content.

## Deliverable & cost

- Output → `docs/research/2026-07-<dd>-furniture-reading-DR.md`: SOTA table (method / corpus / furniture
  recall-precision / vector-or-raster / needs-labels), the fusion-separation verdict, the industry
  equilibrium finding, and the ranked transfer shortlist with kill-criteria + a single go/no-go.
- Cost: `deep-research` fan-out (moderate, many searches + verify). If an NLM DR is ever added,
  ≤10 asks budget, `notebooklm_dr.py`, prune the notebook after distillation.
- **Ask-tier: greenlight before I run.** Then I distill into the reader roadmap ([[plan-extraction-pipeline]]).
