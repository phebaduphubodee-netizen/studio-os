# LOOK round-4 — 2026-07-28 (garment identity, second verdict)

Owner, interrupting the light-story pass: "geometry ก็ยังเพี้ยนอยู่ เสื้อผ้าในตู้
ดูไม่เหมือนเสื้อผ้าจริง" — overruling my round-3 close AND my bench-sheet reading
that geometry was done. First round-4 gate artifact lane run under the adopted
R-rules (quick-look ladder, 2-cycle stop-loss, owner-only close).

## The diagnosis (LOOK at g7's wardrobe band, honest this time)

The round-3 garments were the silhouette of a GARMENT BAG: narrow top opening to
a fuller body (`shoulder=0.62 → 1.0` profile), no sleeves anywhere, paper edges,
±6 mm creases invisible at render distance (the pitch budget capped them), and a
full-thickness bottom ring that presented a literal plank edge. Boards, fanned.

## The mechanism (softgoods.garment rebuilt, styling species extended)

1. **Profile inverted** — widest at the hanger tips, easing to a genuinely
   narrower body (0.74 ± dev) by the knee. GARMENT_FLARE stays the true span
   bound (wf peaks at 1.0).
2. **Sleeves** (`sleeves=True`) — two flattened tapered tubes per shirt in the
   same mesh, living in the side band the narrowed body freed: outer edge AT the
   shoulder tip (span untouched), riding one face (front/back per arm) so they
   read as ridges under light. FIRST CUT FAILED INVISIBLY: constrained fully
   inside the body envelope, the tubes were buried inside the body's volume —
   the quick-look showed literally nothing changed. The quick rung caught it for
   ~1/13 the price of the old loop.
3. **Deep folds, inward-only** — real drape folds are 15-30 mm; the 68 mm rail
   pitch cannot give that outward. The folds now CARVE toward the midplane
   (valleys, never bumps): envelope untouched, pitch untouched, faces finally
   stripe under light. Fold lines also nick the silhouette edges.
4. **Knife hem** — bottom ring thins 68% over the last fifth of the drop.
5. **Third length species** — ~¼ of shirts are short pieces (0.62 × drop):
   the short-long rhythm of a worn closet (trousers were already the second).

Armour: shoulder-widest pin (old narrower-than-body pin INVERTED with the
verdict recorded), sleeve containment + silhouette-notch pin (a buried sleeve
fails the test now), 2117 green.

## Evidence

`room_bedroom_suite_eye_g8.png` (full fidelity) vs g7: every piece stripes with
drape folds, silhouettes step shoulder→sleeve→body, hems vary at three scales.
Quick-loop renders: `*_eye_ql.png`, `*_wardrobe_bay_entry_ql.png` (48 spp, 68 s).

## Residuals (disclosed, unclosed)

- **Palette** — the rail is still near-monochrome charcoal/greige; the
  three-value ladder varies VALUE, not hue. Material lane.
- **Light** — flat fill still mutes the fold striping; the light-story pass
  (interrupted by this round) remains next.
- `--room bedroom` in look_bench cannot filter (anchors carry no machine room
  type by LOCAL-ONLY design; designer bucketing pending).

## Spend (R6)

4 quick renders (~68 s each) + 1 full render (~5 min) + full suite ×3.
Two design iterations inside the quick loop; the R1 2-cycle budget was not
breached (no full-price failure — the one failed idea died at quick price).
