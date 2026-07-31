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
| TRN-001 | 2026-07-30 (seed …-002; …-001 re-rolled: site photo, not render) | ACTIVE | 4: LIGHT พร้อมให้ตัดสิน (gate #4); 1–3 closed by owner ("พอได้" / "พอใช้ ลุยต่อ" / owner corrections + "ลุยต่อ"); next = 5 styling (first live case of the (ข) decision) | 4 | 14 | VP-pinned camera solve (pin what the vanishing points measured — focal/yaw/horizon — solve only station; residual pattern read back as per-element mm); **a solved camera turns the target into a MEASURING INSTRUMENT** — back-project any probed pixel onto the face plane it lies on and read mm directly (`trn001_measure.py`), which found the 428mm shelf ladder, the five identical 513mm drawers and every depth without one proportion guess; **sweep a dimension against the landmark fit to tell a MEASUREMENT from an ASSUMPTION** — a real minimum means the image constrains it, a flat curve (plinth corner radius) means only a direct probe can; the rounded-mass SILHOUETTE trap recurred (a curved end's outline sits at y=-(d-r), not the face plane) and cost a wrong altar width until caught; foreign-object-in-scene class: spec-side projection checks can NEVER see an object the spec doesn't know (--factory-startup default cube corrupted 3 renders; ID-mask emission render = the catcher, now a standing rung); quarantine wired (look_bench.load_trained fail-loud) |

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

**Round-3 material lessons (2026-07-31).** A texture map is evidence of how a
material VARIES, not an instruction to wear that material's character — the CC0
wood is a worn table, and at full strength it dressed cabinet veneer in knots
the delivered work does not have, while painted plaster keeps almost none of
its map because a smooth wall really is nearly flat. **Grain has a direction**:
the cold critic measured our veneer at 1.57 directional energy against the
reference's 2.41 and that isotropy alone is why wood read as cast concrete —
the same measurement also caught our rail and our altar wearing the SAME
material where the delivered piece uses two. And **normalise a map by its
luminance, never per channel**: the wood map's blue mean is 0.008, so
per-channel normalisation applied ~14x gain to a channel holding nothing but
compression noise and sprayed blue specks across both hero surfaces. Colour
work needs its own numeric track (`trn001_matcheck.py`) because reprojection
error says nothing about it — and that track must be honest that a uniform
brightness gap is the LIGHT round's, so what it really catches is one surface
wrong relative to its neighbours.

**Round-4 light lessons (2026-07-31).** The round's biggest find was not about
light. **A decision that lives only in a scratch file is not a decision:** the
spec of record still carried round 1's PRE-SOLVE camera while every gate frame
since round 2 had been rendered from a private copy holding the solved one, so
rebuilding from the spec silently un-did the camera solve — 83 mm of height, a
~40 px shift, landmark median 15.5 → 54.6 px — and nothing failed, because a
spec with a plausible camera renders a plausible picture. This is the
revertible-by-omission class wearing a new shape (the file that renders is not
automatically the file of record), and the guard is a test that refuses any spec
whose camera carries no `_solved` marker.

Second: **a material sample inherits the lighting model it was taken under.**
Round 3 backed every albedo out by dividing the target patch by the white wall
and taking the wall as 0.80 — which assumes both surfaces receive the same
illuminance. True under a flat form light, false under downlights, where a
horizontal floor collects far more from a ceiling fixture than a vertical wall.
The floor therefore came out at 0.72 albedo — brighter than most white paint, on
the largest surface in the room — and behaved as a second ceiling, bouncing every
gradient flat (frame range 22:1 against the target's 141:1, cavities 2.6× too
bright, the floor's own 37.6% falloff reduced to 2.5%). Our own vault had the
physical value the whole time (`knowledge/lighting/lumen-method-and-fixture-
placement.md:150` — ceiling ~80%, walls ~50%, floor ~20%), which is the
search-our-own-vault-first lesson landing a fourth time.

Third: **two hand-bracketed constants in another project were one rule.**
build_room's IES norms (0.20 for 5.ies, 0.065 for 7.IES) multiply out to 125.8
and 126.6 against their own measured candela means — i.e. norm = K/mean. A pure
LM-63 parser reproduces both (0.2003, 0.0647), so a beam profile can now be
swapped without silently re-powering the room, and the beam became something
choosable BY MEASUREMENT: of three real profiles, the tight downlight fixed four
independent readings at once where the flood fixed none.

Fourth, on instruments: **a profile measure that moves when the background moves
is measuring the background.** The halo's half-fall was defined against half the
PEAK, so when round 4 raised the room's ambient the same unchanged glow reported
as spreading from 72 to 98 px. Measured against half the peak-to-floor it reads
22 px, exactly the target's. And an honest first guess still has to be tested:
the floor's 1.64× error looked like round 3's board-to-board variation failing,
until splitting the strip into board-wide columns showed a 37.6% smooth ramp
with only a 3.4% neighbour jump — light, not material.

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
