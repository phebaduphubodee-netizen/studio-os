# Reference board — soft goods (garments / pillows / duvet) — 2026-07-29

Owner, after the round-4 gate: "คุนเคยไปหา reference บ้างมั้ยว่าเสื้อผ้า, หมอน,
ผ้าห่ม ต้องหน้าตาเป็นยังไง? เพราะผมมองว่ามันไม่ใช่เสื้อผ้า"

The honest answer was NO — four rounds of soft-goods work were built from priors
and judged by the same head that built them. This board is the correction, and
the standing rule that comes with it: **no soft-goods build or LOOK judgment
without the object-class reference open beside the crop.** The reference of
record is the sellability anchor pool itself (delivered, sold work — the exact
standard the sellability law measures against). Anchors JUDGE; they never
DICTATE (no copying — that is benchmark leakage, R4's own recorded failure mode).

## Class 1 — garments on a rail

**Reference:** anchor `I-24-062` file `125386_09-1-open.jpg` (delivered dressing
room; LOCAL-ONLY under `_private/`, cited by I-code + file number, never by
client name).

Cues the reference shows, in priority order:
1. **SPARSE**: two garments on ~a metre of rail; the lower rail left EMPTY.
   Density is the first identity signal — packed files hide every silhouette.
2. **Sleeves are the LOWEST part**: free tubes falling PAST the body hem,
   splaying slightly outward, ending in a buttoned CUFF.
3. Visible hanger hooks curving over an exposed rail.
4. Multi-directional cloth CRUMPLE, not only vertical folds.
5. Slight tone difference between neighbouring pieces (same family, not clones).

What this refuted in our build: 68 mm pitch (→ 240 mm, scaling down to a
132 mm-floor pair on short rails), sleeves shorter than the body, the "two
garments = bare towel bar" pin (inverted: two IS the styled read).

## Class 2 — bed pillows

**Reference:** anchor `I-23-023` file `499473_Bedroom_1_main.png` (delivered
bedroom).

Cues: pillows SLUMP back into the rank behind (~30-45°), never stand at
attention; overstuffed volume with soft side curvature; ranks big→small
front-to-back with real overlap; occasional pinch-tuft wrinkles on the front
accent. → our shared lean went 10° → 26° (kept SHARED for the no-dent armour).

## Class 3 — duvet

Same reference frame. Cues: a comforter has LOFT — a thick soft mass in
large gentle billows; the hem falls as a ROUNDED ROLL over the foot/side; a
second flat layer peeks beneath (layering). → sim feedstock cell 28 → 42 mm,
solidify thickness 8 → 18 mm, collide distances re-derived per the cloth-stack
contact law (shell arithmetic recorded at the bake site).

## Provenance + how to reuse

- Anchor paths resolve through `_private/benchmark/candidates.json`; view them
  locally only. This doc carries NO client names and no image copies.
- To pull the board up beside a new crop: `python pipeline/scripts/look_bench.py
  <render> --n 4` for the panel, plus open the two cited anchors directly.
- The web adds nothing the pool lacks for these classes (stock-photo sites are
  paywalled/watermarked and the pool IS the selling standard); if a class has no
  anchor coverage (e.g. open shelving styling), fetch generic real-photo
  references FIRST, then build.
