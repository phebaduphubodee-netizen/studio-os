# Reproduction curriculum — เรียนจากงานส่งจริงด้วยการสร้างซ้ำจนเหมือน

> OWNER ORDER 2026-07-30: ยกระดับการเรียนรู้จาก "อ่าน text" เป็น "สุ่มงานของ
> เพื่อน 1 งาน แล้ว trial-and-error ใน Blender จนกว่าจะได้รูปที่เหมือน" และ
> "ทำไปเรื่อยๆ ทุก session จนกว่าจะสร้างงานของเพื่อนออกมาได้ทั้งหมด".
> This file is the standing charter + ledger. It is COMMITTED — therefore it
> must never contain a client/project name, folder path, or image filename
> from the corpus; the pick↔target mapping lives under
> `_private/benchmark/reproduction/<TRN-id>/` (gitignored).

## Why this lane exists (the learning theory)

- The target image EXISTS → "เหมือนงานเพื่อน" is a falsifiable finish line
  (the F4 acceptance-contract law satisfied by construction). The loop
  terminates; "ยังไม่เหมือนของจริง" against an imagined ideal does not.
- Reproduction forces discovery of the actual craft (light rig, exposure,
  material response, camera grammar) instead of reading about it — the active
  successor to the 2026-07-30 ground-truth study (which read pro .blend files
  and measured the gap numerically).
- The copies are NOT deliverables. The product is the LEARNING: after each
  work converges, its transferable techniques are distilled into `knowledge/`
  (via `_inbox/`) and, where applicable, into pipeline capabilities.

## Standing rules

1. **Pick**: seeded random from the SAME pool R4 judges against
   (`look_bench.anchor_pool` — residential renders only). Every seed + result
   is logged in the private pick record; a non-render pick re-rolls with the
   next numbered seed (documented, never silently).
2. **Benchmark quarantine (R4 leakage law)**: the moment a work becomes a
   training target, its ENTIRE project (all sibling renders) is quarantined
   from every future look_bench panel — trained-on anchors may never judge
   our frames again. WIRING REQUIRED before the first look_bench run of any
   training round: exclusion list at
   `_private/benchmark/trained-anchors.json`, honored by `anchor_pool()` +
   pinned by a test. Until wired, look_bench runs are FORBIDDEN in this lane.
3. **Privacy**: target images and side-by-side comparisons stay under
   `_private/` forever. Committed build specs use the TRN-id and generic
   descriptions only. Target images never enter Gemini, NLM, web, or any
   external call.
4. **Element ladder per work** (order fixed): camera+blockout → architecture/
   joinery → materials → LIGHT → styling/assets → convergence pass. One
   element at a time; quick rung (`--quick`) before any full frame (R5).
5. **Iteration control**: R1 applies PER ELEMENT (2 rounds without measured
   improvement on the same element → stop → DR-pull or gate). The lane itself
   is standing (owner-ordered) — the stop-loss governs elements, not the
   curriculum.
6. **Convergence verdict**: side-by-side at matched crop + at least one
   numeric track (SSIM / ΔE band / luminance-histogram distance) recorded per
   round so progress is measured, not felt. The CLOSE verdict is the owner's
   (R3) against the side-by-side.
7. **Spend**: rounds/renders logged per work in the ledger row (R6).
8. **DR-pull**: any element that stalls fires vault → NLM → full DR before
   its 2nd rebuild round (CLAUDE.md §External research lane, 2026-07-30).

## Ledger

| id | picked | status | element | rounds | full frames | learnings distilled |
|---|---|---|---|---|---|---|
| TRN-001 | 2026-07-30 (seed …-002; …-001 re-rolled: site photo, not render) | ACTIVE | 3: materials พร้อมให้ตัดสิน (gate #3); 1–2 closed by owner ("พอได้" / "พอใช้ ลุยต่อ"); next = 4 LIGHT (the study's measured #1 gap) | 3 | 6 | VP-pinned camera solve (pin what the vanishing points measured — focal/yaw/horizon — solve only station; residual pattern read back as per-element mm); **a solved camera turns the target into a MEASURING INSTRUMENT** — back-project any probed pixel onto the face plane it lies on and read mm directly (`trn001_measure.py`), which found the 428mm shelf ladder, the five identical 513mm drawers and every depth without one proportion guess; **sweep a dimension against the landmark fit to tell a MEASUREMENT from an ASSUMPTION** — a real minimum means the image constrains it, a flat curve (plinth corner radius) means only a direct probe can; the rounded-mass SILHOUETTE trap recurred (a curved end's outline sits at y=-(d-r), not the face plane) and cost a wrong altar width until caught; foreign-object-in-scene class: spec-side projection checks can NEVER see an object the spec doesn't know (--factory-startup default cube corrupted 3 renders; ID-mask emission render = the catcher, now a standing rung); quarantine wired (look_bench.load_trained fail-loud) |

**Gate #2's open question — CLOSED 2026-07-31 by a third instrument.** The
built-in is ~100 mm deep, not 360. A shelf board below the horizon shows its
top surface as a band whose height reads the cubby depth directly: the target's
is 5.0 px, and the model gives 4/5/6 px at 80/100/120 mm against 17.8 px at the
old 342. The side-return test agreed at 75 mm once its sweep started low enough
— the earlier run began at 200 mm, so the answer was outside the range it could
see. Our render's side band is now 30 px against the target's 28 (was 101).
**The lesson is about the fit, not the depth:** the landmark solve had a clean,
confident minimum at 360 because the only landmarks that depended on tower depth
were DEFINED wrongly. A least-squares fit can only test the geometry you told it
about — it will report a precise answer to a mis-posed question, and the round-1
rounded-silhouette trap was the same class. Cross-check a fitted dimension
against a feature the fit never saw before believing it.

## Decisions

- **(ข) CC0 scanned assets — เคาะ 2026-07-31 (owner delegated)**: styling-tier
  organic objects (statuary, florals, candlesticks) in this lane USE external
  CC0/PD assets; millwork/joinery stays build-not-buy (the build IS the
  learning; the ground-truth study measured every pro file leaning on assets
  for organics). Rules: ฿0 + CC0/public-domain only (asset-lever law upheld);
  generic search terms only (privacy — never client context in queries); scale
  ASSERTED in mm on every ingest before the spec consumes it (pipeline law);
  religious statuary used respectfully as-is. First live case: TRN-001 Buddha
  figures + lilies at the styling rung.

Target profile (generic, committable): prayer-room built-in feature wall —
backlit stone panel with warm edge halo, symmetric dark-wood open shelf
towers, trim-lined header band, stepped rounded-corner altar platforms on a
white drawer plinth, statuary + floral + candlestick styling, light plank
floor, recessed downlights + soft side daylight. Square format. Primary
lessons expected: edge-lit backlight story, warm/neutral light mix, stone
figure material, wood grain at near-horizontal camera, brass trim lines,
small-object styling assets (first live case for the CC0-scanned-assets
question ข).
