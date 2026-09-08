# floor2 v5 phase-2 — the furniture layer is owner-authored (evidence, not a shortcut)

**Date:** 2026-07-10 · **Goal was:** read furniture from the PDF → v5 scene-graph → run the
`suite_clearance` + `placement_gate` gates → close stage-03. **Finding:** the furniture layer
cannot be auto-derived on this sheet; it is owner-signed placement, and the gates confirm why.

## Two independent blockers, both measured

1. **Furniture identity labels are OUTLINED text, not selectable text.** The whole page has 83
   extractable words (title block only). Every `BF09 / BF10 / BF15 / 7'x6.5' / 3.05` label is drawn
   as vector paths → no machine-readable identity. The clusterer gets geometry, never a kind.

2. **`plan_cluster.extract_clusters` recovers only fragments — the dense-furniture merge wound.**
   Master-bedroom zone:
   - narrow zone → **2 partial boxes** (one is a 906 mm slice of the 2134 mm bed);
   - full zone (bed + headboard + wardrobe + case goods) → **0 kept clusters** — the adjacent pieces
     merge into blobs that exceed the `merged_blob` screen and are DROPPED.
   The bed, BF14 headboard and BF09 wardrobe sit flush against each other and the wall, so the
   deterministic clusterer cannot separate them. This is the same fusion wound measured all session
   (Structured3D within-room fusion; FloorPlanCAD 60 % isolated-furniture misses) — now on the
   studio's OWN sheet.

Because `placement_gate` re-derives its check clusters from this same `plan_cluster`, it would flag
almost any placed bedroom furniture as FLOATING/UNPLACED — not because the placement is wrong, but
because the clusterer can't see the merged furniture. The gate cannot machine-certify furniture here.

## The two-layer law, now measured across ALL THREE layers (floor2)

| layer | machine can… | measured on this sheet |
|---|---|---|
| **thick walls** | fully derive | v5 blind ≡ v4 EXACT (992 segs) — 100 % reproducible |
| **thin glazing / boundary** | PROPOSE candidates, not select | recall 84 % (16/19) at precision 6.8 % — owner SELECTS + INFERS 3 undrawn |
| **furniture placement** | not even propose cleanly | 0–2 fragments; dense pieces merge into dropped blobs — fully owner-authored |

The machine share **decreases monotonically** structure → boundary → furniture. That is the whole
project thesis, now quantified on the studio's real plan: geometry is machine-solved; the boundary is
owner-selected; the furniture layout is owner-authored. (v4's `scene-graph.master_bedroom.json` was
itself built by `gen_floor2_v4_specs.py` — a human-authored spec, not a reader output — which
independently confirms furniture is a hand-placed layer.)

## Stage-03 status for v5 (honest)

- **Delivered (machine + candidate layers):** walls (`floor2-walls-mm.json`), thin-glass owner
  candidates (`floor2_v5-thin-glass-flags.json` + the 706-candidate `floor2_v5-thin-predicted.json`
  review queue), full provenance + diff vs v4.
- **NOT delivered — requires owner-signed placement:** `scene-graph.json` (furniture) and therefore
  the `suite_clearance` / `placement_gate` gate. This is not a tooling gap to grind away; it is the
  irreducibly-human layer the pipeline is designed around.
- **Offered next step:** build the v5 scene-graph by owner-signed VISUAL placement (the real
  workflow — place each piece, run `placement_gate` to sign off what the clusterer can't) — a human
  step, not an auto-read. Say the word and I'll draft it for the master suite for you to sign.
