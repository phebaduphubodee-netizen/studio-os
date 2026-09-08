# floor2 v5 — BLIND structural re-derivation (phase 1)

**Date:** 2026-07-10 · **Instruction:** rebuild floor2 as v5 WITHOUT looking at the old one
(ห้ามแอบดูของเก่า) · **Source:** `00_intake/raw-local/The City สาทร - สุขสวัสดิ์_Plan funiture 02.pdf`,
page 1 = `PLAN FURNITURE FLOOR 2` (1:75, A3) · **Tools:** `pdf_extract_walls.py` (unedited),
`fitz` render/overlay · **Output dir:** `03_layout/v5/`

## What "blind" meant here

- **Read/used:** the source PDF only (raw input), the pipeline tools, this stage's `_contract.md`,
  and the ASA-2554 layer standard. Wrote to a FRESH `v5/` path so `pdf_extract_walls`'
  `merge_carried` found no prior and did **not** pull v4's owner wall-patches — the extract is
  pure machine walls (`manual_additions: false`, verified).
- **Did NOT read:** `03_layout/v4/**`, the root `03_layout/floor2-walls-mm.json` (it carries v4's
  owner `manual_additions` — **CORRECTION 2026-08-04, measured:** that reason was FALSE. Root's
  md5 is identical to this v5 extract and has no `manual_additions` key; root is the untouched v3
  machine baseline, and the owner wall-patches live ONLY in `v4/floor2-walls-mm.json`. The
  not-reading itself was still correct blindness — only the stated reason misdescribed root's
  content. See `../README-walls.md` for which copy is truth), or any v4 scene-graph / openings /
  gate / defect / manifest.
- **Honesty limit (stated, not hidden):** prior session context held v4 *REVIEW-state summaries*
  (s2 sliding door, shower niche, tub, outline offsets). Those specific v4 answers were **not
  imported** — geometry is derived independently from the PDF and every owner-signature point is
  re-flagged **open**, never copied. A v5-vs-v4 diff is the payoff and it is the **owner's to run**;
  I stayed on the v5 side of the wall.

## Result — the wall backbone (machine layer)

`floor2-walls-mm.json`: **992 wall segments**, bbox X[-345..20448] Y[-1152..12896] mm →
**20.79 × 14.05 m**; seg length median 102 mm (double-line wall faces), max 4.30 m (the BF15 built-in
run). Calibration = the tool's built-in `26.45 mm/pt, origin (171.2, 596.5)` — a property of this PDF
page (verified <1% vs the drawn dims 5500/5100/2850/2950/700), not a v4 decision.

**QA overlay (`floor2_v5-walls-overlay.png`, red machine walls over the plan):**
- **Coverage strong** — every structural wall (perimeter, room partitions, all bathroom walls)
  is captured, with thickness (double-line); alignment is spot-on → calibration correct.
- **Openings show as gaps** — doorways/windows appear as breaks where red stops.
- **Machine MISSED (black, no red) = the two-layer boundary:** the master-bedroom **south terrace
  glazing** (dashed thin line under the bed, inboard of the two potted trees) and the terrace
  perimeter — both drawn below the 0.6 pt wall gate. These are the owner-signed indoor/outdoor line,
  captured as flags, not walls.
- **Minor noise:** two furniture-legend cross symbols (bottom-centre) were thick enough to be kept
  as red — false positives to prune when furniture is separated in phase 2.

## Independent room read (from the PDF, not v4)

Master bedroom (bed 7'×6.5', wardrobe BF09-3.330, seating cluster, opens south to terrace) ·
master bathroom (tub, double vanity, toilet, shower; dim 3.05) · terrace (outdoor, 2 trees, dashed
edge) · two small bathrooms (top-left, top-centre; toilet+shower) · ensuite bath 2 (top-right; tub
1.95 m) · central straight-run stair (UP → floor 1) · right room = bedroom 2 / multipurpose
(built-in BF15-4.30 m + ตู้พระ Buddha shrine). Interior area stated **70.4 m²**. Owner **K.NUT**,
source drawn by **RAAR DESIGN & BUILT-IN**.

## Owner-signature candidates (`floor2_v5-thin-glass-flags.json`)

- **tg1 — master-bedroom → terrace sliding-glass facade** (the real indoor/outdoor line).
- **tg2 — terrace outline** (dashed; owner classifies glass balustrade vs parapet vs open edge — an
  F5 plane call, never auto-placed).

Both are `OWNER-CONFIRM-PENDING` → machine-INERT (not injected into the wall segments; `merge_carried`
refuses unsigned stubs), so nothing unconfirmed reaches built geometry. Coordinates are approximate
(1:75 visual read) — owner sets exact.

## Status & next

- **Phase 1 (this) = structural layer:** walls + owner-signature flags + provenance. **Blind, clean.**
- **NOT done — the stage-03 gate is NOT claimed:** `scene-graph.json` (furniture placement) and
  `clearance-report.md` (zero-collision / zero-clearance-violation geometry gate) are **phase 2**.
  The source is a *furniture* plan, so phase 2 can READ furniture positions + the BF## built-in specs
  from the PDF rather than re-designing, then run the clearance engine.
- **Diff-vs-v4:** deliberately not run (would break blindness). Ready for the owner to compare v5's
  independent walls/flags against v4's contested extraction.
