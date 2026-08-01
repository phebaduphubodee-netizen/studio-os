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
| TRN-001 | 2026-07-30 (seed …-002; …-001 re-rolled: site photo, not render) | ACTIVE | 6: cubby POCKET built — the model had one depth where the unit has two (proud 100 CONFIRMED + pocket 176.5 NEW = cavity 276.5, measured 274.8); the wall now opens for it. Rounds 1–3 closed by owner; gates #4 (light), #5 (styling), #6 (depth) all OPEN. R1 STOP on cubby mouth brightness. Round 7: PALETTE's roughness column was dead for every mapped material (marble asked 0.18, rendered 0.506 — the hero object's polish reached no frame in four rounds); veneer wore the floor's micro-bevel relief; DR fired on veneer figure; step depth 311 taken back OFF the owner's queue as unconstrained rather than wrong. Round 8: the cubby was never too bright, it was too WARM (hue err 0.339 -> 0.095 at unchanged luminance); bookmatch built per the DR; the ID pass rebuilt to give every mass a unique decodable colour, which promptly acquitted a matcheck row the previous commit had convicted | 8 | 28 | VP-pinned camera solve (pin what the vanishing points measured — focal/yaw/horizon — solve only station; residual pattern read back as per-element mm); **a solved camera turns the target into a MEASURING INSTRUMENT** — back-project any probed pixel onto the face plane it lies on and read mm directly (`trn001_measure.py`), which found the 428mm shelf ladder, the five identical 513mm drawers and every depth without one proportion guess; **sweep a dimension against the landmark fit to tell a MEASUREMENT from an ASSUMPTION** — a real minimum means the image constrains it, a flat curve (plinth corner radius) means only a direct probe can; the rounded-mass SILHOUETTE trap recurred (a curved end's outline sits at y=-(d-r), not the face plane) and cost a wrong altar width until caught; foreign-object-in-scene class: spec-side projection checks can NEVER see an object the spec doesn't know (--factory-startup default cube corrupted 3 renders; ID-mask emission render = the catcher, now a standing rung); quarantine wired (look_bench.load_trained fail-loud) ; **ONE PARAMETER CARRYING TWO THINGS is the shape to hunt** — five rounds of light could not fix a cubby because `tower.d_mm` meant both 'how far the carcass stands proud' and 'how deep the cavity is', so proving the first read as proving the second (a note was CLOSED on it); the tell was a gating metric (p99/p1) that no amount of the lane's own knobs could move, and it moved 57.8→157.9 the moment the second dimension existed; **an instrument that cannot reproduce a value you already know must not be asked for one you don't** — two reads were disqualified here by their own controls (a horizontal-plane back-projection failing by 57-172mm, and a grazing side wall returning y=+323.7 for an arris that must be ~-100), which is cheaper than believing them; **plane≠surface paid for the 4th time** and is now the `first_hit` instrument rather than a memory — it reversed a conclusion from 'left tower fine, right dark' to 'both dark, consistently'; **coincident faces are not a style question** — the hero marble sat inside the wall body with front faces exactly flush and had been winning a BVH coin flip on every render since the recess landed ; **the cure you already wrote for one input is not applied to the next** — MAP_MEAN normalises the diffuse map so the map gives VARIATION and the table gives IDENTITY, and the roughness map two lines below was still linked raw, silently overriding a whole column of the table (found only because two roughness values gave byte-identical ladders: identical to three decimals is not a weak effect, it is NO effect); **one-parameter-carrying-two-things recurred twice in one day** — tower.d_mm (proud vs cavity) and NORMAL_STRENGTH keyed by map slug (a veneer forced to wear the floor's plank bevel), so hunt the SHAPE and not the instance; **a finding rejected on a broken measurement is not yet a finding** — the geometry fix invalidated the criterion that had killed the fill and the wide beam, so both went back on trial: the fill's refutation survived on an untouched metric and the beam's held too, and re-opening was still right; **a vault MISS is not a vault GAP until the search runs in the language the vault is written in** (an English grep for bookmatch/flitch found nothing in a file indexing them in Thai) |

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

**Round-5 styling lessons (2026-07-31).** **Symmetry is a CONSTRAINT, not a
complaint.** The owner said "not symmetric" twice about the same pair, and the
second time it stopped being a note and became the missing equation: a symmetric
pair standing on one surface has exactly ONE unknown — how far forward the pair
sits — so two measured pixels over-determine it and the position can be SOLVED.
It solved to 1.6 mm. What made three earlier attempts disagree is that every one
of them used the blob's BOTTOM, and **contact shadow displaces v, not u** — the
horizontal pixel was the uncontaminated measurement the whole time. The shape
those three attempts share is worth naming: each solved for two unknowns with one
equation and then patched the residue (keep x and clamp y → a vase inside a solid
pedestal; fix y at the step's front edge → half the base overhanging; displace
26 px to dodge the pedestal → a prop where the image does not put it). Stored now
as one offset mirrored about the centre box, the same relationship the owner's
own pedestal correction established, because two independent x values is exactly
what lets a pair drift apart one edit at a time.

Second: **`backproject()` answers where a ray meets a PLANE, and knows nothing
about the extent of the SURFACE.** It returned a confident millimetre for a point
108 mm past the step's front edge. Reading that as noise and clamping it is the
explain-away-the-anomaly move — same class as the depth sweep that began at
200 mm and concluded "no solution" from a range that excluded the answer. Guards
added: nothing may stand inside a solid, and every prop must rest on the top face
of a mass whose plan extent contains it.

Third, on assets: **LOOK AT THE ASSET.** A CC0 vase was chosen because its
bounding-box aspect matched the target's to 3%, and it rendered as a flat plank —
the asset is mispackaged, its mesh datablock literally named "Cube.001". A
bounding box cannot tell a vase from a board, exactly as round 3's figure metric
could not tell veins from tile joints; the lesson was already written down in the
same file, in my own words, and repeated anyway. Also: an asset that imports at
the right SCALE can still land in the wrong PLACE, and the build log will report
it placed because the log reports what was ASKED for — one vase printed
"414mm -> 259mm (x0.625)" while sitting unscaled at the world origin.

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
