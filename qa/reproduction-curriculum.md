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

## The finish line — ADOPTED 2026-08-01 (owner: "ทำต่อให้มันจบซักที")

The charter has claimed since it was written that "the target image EXISTS ->
'เหมือนงานเพื่อน' is a falsifiable finish line... the loop TERMINATES". It did not
terminate. Nine rounds ran because nobody had written the THRESHOLD, so every
round ended with "พร้อมให้ตัดสิน" and the only stopping condition available was the
owner running out of patience. A finish line that only one person can call is
not a criterion; it is a queue.

**THE TEST.** `python pipeline/scripts/look_bench.py <our frame> --blind` builds
a panel of delivered anchors with our frame shuffled in UNLABELLED, and writes
the answer to a separate `.ANSWER.txt` beside the sheet. The owner picks which
panel is ours. **If he cannot pick it, or picks wrong, the reproduction CLOSES.**

Three reasons this and not a number:
* It is R4's own law, already adopted — "แพ้งานส่งจริง = ขายไม่ได้" — rather than a
  new criterion invented to make a lane end.
* An aggregate over named patches can be gamed by the patches. The panel cannot:
  it judges the whole frame, against work that was actually delivered and paid
  for, by the person who has to sell ours.
* It orders the work correctly. A frame missing the objects a room is FOR gets
  picked instantly no matter how good its light is, which is why round 10 built
  the florals before touching the remaining light findings.

**And R4's daily instrument could not run it.** `compose` puts our frame first,
rings it in red and writes "OURS" over it — right for "how does this compare",
structurally incapable of "can you still tell". A judge who is told the answer
cannot fail. `--blind` (2026-08-01) is that gap closed, and it is general: every
future unit of this curriculum closes the same way.

---

## THE IDENTIFICATION TEST IS REFUTED — 2026-08-02, one sentence from the owner

> *"ผมต้องชี้ได้สิว่าอันไหนของเรา เพราะผมนั่งดูตลอดว่าคุณผิดอะไร"*

**He is right, and it invalidates the test above for every unit this curriculum
will ever run.** A blind identification test assumes a judge with no priors about
the candidate. The only judge the privacy rules permit is the owner — the anchors
are other people's delivered client work and may never leave this machine — and
he is the single most contaminated observer possible for this frame: he watched
twenty rounds of it, he knows our lilies are magenta and our altar is blond, and
he has been told every defect as it was found. **He picks ours by RECOGNITION and
the sheet reads it as a quality verdict.**

The instrument measures his memory of the build. It cannot return "close enough"
no matter how good the render gets, so it has no passing state — which makes it
not a finish line but a second queue, the exact failure the section above was
written to fix. Adopted at round 11, never usable, and nine rounds' worth of
"the finish line finally exists" rested on it.

Note the shape, because this repo has now paid for it many times: **an instrument
was adopted on the strength of the gap it closed, and nobody asked what it
assumed about its own judge.**

**THE REPLACEMENT — RANK, DO NOT IDENTIFY.** The same sheet, the same six
panels, already lettered A–F. The question changes:

> เรียง A–F จาก "ดูเสร็จ/ส่งลูกค้าได้" มากสุดไปน้อยสุด และให้เหตุผลสั้น ๆ ต่อช่อง

**PASS = ours does not come last, and no reason given against it names a defect
rather than a preference.** Knowing which panel is ours tells the judge nothing
about where it BELONGS in a quality order, so recognition cannot leak into the
answer. A contaminated judge who is harsh on the frame he built biases the result
CONSERVATIVE — toward keeping the lane open — which is the safe direction for a
stopping rule to fail in.

And it is a strictly better artefact than a binary: the per-panel reasons are the
work queue for the next round, in the owner's own words, ranked by him. The
binary produced one bit and no direction.

Same law underneath, stated more exactly: R4 says **แพ้งานส่งจริง = ขายไม่ได้**.
The finish line is therefore *not losing to delivered work* — never *being
indistinguishable from it*, which was always a stronger claim than the law asked
for and than a reproduction exercise needs.

**Standing exclusion, declared before the test rather than after:** TRN-001 is
judged WITHOUT the three Buddha figures. The zero-baht CC0 pool holds no
religious statuary (521 models searched), and hand-modelling a Buddha image was
refused on decision (ข)'s own wording, "used respectfully as-is". That is a
STUDIO capability gap — every Thai residential job with a prayer room meets it —
and not a defect of this reproduction. It is the owner's to price, not this
lane's to fake.

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
| TRN-001 | 2026-07-30 (seed …-002; …-001 re-rolled: site photo, not render) | ACTIVE | 6: cubby POCKET built — the model had one depth where the unit has two (proud 100 CONFIRMED + pocket 176.5 NEW = cavity 276.5, measured 274.8); the wall now opens for it. Rounds 1–3 closed by owner; gates #4 (light), #5 (styling), #6 (depth) all OPEN. R1 STOP on cubby mouth brightness. Round 7: PALETTE's roughness column was dead for every mapped material (marble asked 0.18, rendered 0.506 — the hero object's polish reached no frame in four rounds); veneer wore the floor's micro-bevel relief; DR fired on veneer figure; step depth 311 taken back OFF the owner's queue as unconstrained rather than wrong. Round 8: the cubby was never too bright, it was too WARM (hue err 0.339 -> 0.095 at unchanged luminance); bookmatch built per the DR; the ID pass rebuilt to give every mass a unique decodable colour, which promptly acquitted a matcheck row the previous commit had convicted. Round 9 (owner order 1, take light OFF the floor): SHIPPED wall-wash tilt 7 deg + 5.ies + diffuse_bounces 4->16, aggregate |abs-1| 3.26 -> 2.01 and worst patch 1.18 -> 0.34, at the cost of header/plinth and p99/p1; found and fixed a 180-degree yaw error in every aimed light this lane ever built, which invalidates the FILL's two refutations; and measured the one thing no knob can move -- the target's floor carries a left-right ramp of +0.199/m that ours reports as -0.005/m in all 30 configs. Round 10 (florals): round 5's 'the CC0 pool holds 13 models' was a CACHE MISS -- the real pool is 521 and its conclusion survives on it; lilies BUILT (decision (kho)'s refusal was about religious statuary 'used respectfully as-is' and never covered cut flowers), Buddha figures still refused and now recorded as a STUDIO capability gap rather than a TRN-001 defect. Round 11 (11-agent fleet): the ROOM IS 105 mm TALLER than nine rounds assumed and nothing in the model ever disagreed; the floor's texture was in the map all along and being lost in delivery; and the finish line finally has a threshold the owner can run. Rounds 12-18: the figures, ACQUIRED after the owner asked where models come from and a working designer said 3D Warehouse — a source our own asset DR never mentions | 19 | 36 | VP-pinned camera solve (pin what the vanishing points measured — focal/yaw/horizon — solve only station; residual pattern read back as per-element mm); **a solved camera turns the target into a MEASURING INSTRUMENT** — back-project any probed pixel onto the face plane it lies on and read mm directly (`trn001_measure.py`), which found the 428mm shelf ladder, the five identical 513mm drawers and every depth without one proportion guess; **sweep a dimension against the landmark fit to tell a MEASUREMENT from an ASSUMPTION** — a real minimum means the image constrains it, a flat curve (plinth corner radius) means only a direct probe can; the rounded-mass SILHOUETTE trap recurred (a curved end's outline sits at y=-(d-r), not the face plane) and cost a wrong altar width until caught; foreign-object-in-scene class: spec-side projection checks can NEVER see an object the spec doesn't know (--factory-startup default cube corrupted 3 renders; ID-mask emission render = the catcher, now a standing rung); quarantine wired (look_bench.load_trained fail-loud) ; **ONE PARAMETER CARRYING TWO THINGS is the shape to hunt** — five rounds of light could not fix a cubby because `tower.d_mm` meant both 'how far the carcass stands proud' and 'how deep the cavity is', so proving the first read as proving the second (a note was CLOSED on it); the tell was a gating metric (p99/p1) that no amount of the lane's own knobs could move, and it moved 57.8→157.9 the moment the second dimension existed; **an instrument that cannot reproduce a value you already know must not be asked for one you don't** — two reads were disqualified here by their own controls (a horizontal-plane back-projection failing by 57-172mm, and a grazing side wall returning y=+323.7 for an arris that must be ~-100), which is cheaper than believing them; **plane≠surface paid for the 4th time** and is now the `first_hit` instrument rather than a memory — it reversed a conclusion from 'left tower fine, right dark' to 'both dark, consistently'; **coincident faces are not a style question** — the hero marble sat inside the wall body with front faces exactly flush and had been winning a BVH coin flip on every render since the recess landed ; **the cure you already wrote for one input is not applied to the next** — MAP_MEAN normalises the diffuse map so the map gives VARIATION and the table gives IDENTITY, and the roughness map two lines below was still linked raw, silently overriding a whole column of the table (found only because two roughness values gave byte-identical ladders: identical to three decimals is not a weak effect, it is NO effect); **one-parameter-carrying-two-things recurred twice in one day** — tower.d_mm (proud vs cavity) and NORMAL_STRENGTH keyed by map slug (a veneer forced to wear the floor's plank bevel), so hunt the SHAPE and not the instance; **a finding rejected on a broken measurement is not yet a finding** — the geometry fix invalidated the criterion that had killed the fill and the wide beam, so both went back on trial: the fill's refutation survived on an untouched metric and the beam's held too, and re-opening was still right; **a vault MISS is not a vault GAP until the search runs in the language the vault is written in** (an English grep for bookmatch/flitch found nothing in a file indexing them in Thai) |

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

- **(ข) Scanned/acquired assets — เคาะ 2026-07-31 (owner delegated), AMENDED
  2026-08-01 (owner order, below)**: styling-tier organic objects (statuary,
  florals, candlesticks) in this lane USE external assets; millwork/joinery
  stays build-not-buy (the build IS the learning; the ground-truth study
  measured every pro file leaning on assets for organics). Rules: **any licence
  that permits commercial use in our renders** (see the amendment for what
  replaced "฿0 + CC0/public-domain only"); generic search terms only (privacy —
  never client context in queries); scale ASSERTED in mm on every ingest before
  the spec consumes it (pipeline law); religious statuary used respectfully
  as-is. First live case: TRN-001 Buddha figures + lilies at the styling rung.

- **(ข-แก้) THE ฿0 + CC0-ONLY CLAUSE IS CANCELLED — owner order 2026-08-01,
  *"฿0 + CC0/public-domain เท่านั้น ยกเลิกข้อนี้"***. It was written on
  2026-07-12 to close a *paid-library* question, and by 2026-08-01 it was
  fencing out the best FREE source available (3D Warehouse, Trimble General
  Model License: free to download and use commercially, not public domain, not
  redistributable as models). It had also become the narrowest rule in the repo
  about its own subject — `docs/LICENSING.md` already whitelists 3D Warehouse
  as a Combined-Work source, and `warehouse.py` + `.gitignore:50` already
  handle it correctly. The clause was the only thing still saying no.

  **What the sourcing rule IS now:** any source whose licence permits
  commercial use of the RENDER. That admits CC0/PD, Trimble GML (3D Warehouse),
  CC-BY with attribution recorded, and paid royalty-free libraries.

  **What did NOT change, because it is licence text and client-liability law
  rather than a studio preference** (`docs/LICENSING.md`, unchanged and still
  binding):
  1. A model that may not be redistributed **never enters version control** —
     it lives in a gitignored cache with its `SOURCE.json` provenance, and the
     fetch is reproducible from the entity id instead. Already wired.
  2. The client receives the **assembled room scene** only. Never a standalone
     model, never the asset bundle (GML §2.4 / §2.6 aggregation ban).
  3. **Scale is ASSERTED on every ingest**, never assumed (pipeline/CLAUDE.md).
     A plausible-but-wrong-scale model is the exact failure this studio sells
     against, and user-uploaded warehouse content carries no scale guarantee.
  4. **Trade dress is not a licence question.** A permissive licence on a model
     that copies a named product's design clears the model, not the design.
  5. **Money is still the owner's call, per purchase.** ฿0 is no longer a RULE,
     but a spend is an irreversible outward action and is never made without an
     explicit go-ahead. What the cancellation buys immediately is the FREE
     sources the old clause excluded — those need no decision at all.

  **Reality check recorded with the amendment:** 13 warehouse models were
  already fetched and rendered on 2026-08-01 (rounds 13–17) under R8's
  build-vs-acquire order, so this amendment makes the written rule match code
  that was already correct — the standing "the file of record is not
  automatically the file that runs" defect, wearing its licensing shape.

Target profile (generic, committable): prayer-room built-in feature wall —
backlit stone panel with warm edge halo, symmetric dark-wood open shelf
towers, trim-lined header band, stepped rounded-corner altar platforms on a
white drawer plinth, statuary + floral + candlestick styling, light plank
floor, recessed downlights + soft side daylight. Square format. Primary
lessons expected: edge-lit backlight story, warm/neutral light mix, stone
figure material, wood grain at near-horizontal camera, brass trim lines,
small-object styling assets (first live case for the CC0-scanned-assets
question ข).


**Round-9 (2026-08-01, owner order "1" = take light off the floor).**
**The mechanism worked on the axis it could reach.** Fitted in world
millimetres rather than in pixels, the floor's DEPTH gradient went +0.762/m →
+0.213/m against the target's +0.308/m, floor_far_left 2.18× → 1.30×, and the
whole ladder's aggregate |abs−1| fell 3.26 → 2.01 with the worst single patch
1.18 → 0.34. Nothing was added to the room to do it: a row of downlights sitting
605 mm off the wall was leaned 7° at the wall it was always described as
washing. Two other levers came with it — 5.ies, which `_beam_retest` had
measured as better overall and SHELVED because it broke header/plinth/cubby,
the exact three patches a wall-wash feeds; and `diffuse_bounces`, which had been
sitting at Blender's factory 4 because nothing ever set it, in a CLOSED BOX
whose deepest pockets can only be reached by light that has already bounced
several times.

**Three method lessons, each of which changed a conclusion.**

First, **the normaliser was the thing under test.** Every rel_err this lane ever
printed divides by `wall_bay_right`, and a wall-wash exists to move that patch —
so the first sweep read floor_far_left crashing to 0.56× when it had merely
become brighter more slowly than its own denominator. Same shape as the annulus
normaliser the fleet killed a day earlier. Setting exposure so the two frames'
medians agree is what made the mechanism measurable at all, and it is now in
the spec as a measurement, not a look.

Second, **a knob you cannot bisect is not a knob.** `aim_z_mm` could not express
a gentle wash: the fixture is 605 mm off a 2682 mm ceiling, so aiming at the
wall's very base is already 12.7° and there is no aim point below it — the
parameter's own floor was most of its useful range. Replaced by `tilt_deg`,
which is the angle actually built (pinned by a test), and the useful answer
turned out to be 7°.

Third, and the one worth carrying: **the aim code had been 180° wrong in yaw
since it was written.** `atan2(dy, dx) + π/2` names the perpendicular to the run
turned the wrong way. Blender's own transform was asked instead of argued with:
44.4° of error for the shipped formula, 0.0 for the replacement. The cove
survived by luck (3.4° of tilt, so being flipped put it 6.8° off and it still
read as "down"), but the FILL did not — both `_fill_refuted` and `_fill_retest`
describe a source aimed INTO the room, and what was built faced the back wall
and reached the frame only as bounce. **A source that can only arrive as bounce
is a diffuse fill by construction**, which is precisely the "raises everything
at once and FLATTENS" result both refutations recorded. Those two verdicts
convicted a mechanism that was never on trial. Recorded, not re-opened.

**The finding that outlives the round: our model of that room is SYMMETRIC and
the room is not.** The target's floor carries a left-to-right brightness ramp of
**+0.199/m** (planar R² 0.603, present in four independent bands, and
strengthening toward the camera: 25% → 38% → 62%). Ours reports **−0.005/m** —
zero — across all thirty configurations rendered this round: four beam profiles,
tilts from 0° to 51.5°, three power splits, four bounce budgets and a fivefold
floor-gloss sweep. That is the same tell as the cubby: a metric no knob in the
lane can move.

Three hypotheses were put to it and two died. A **post-production gradient** is
refuted because post does not know about geometry and would tilt everything at
one rate per pixel — the target's floor runs +0.349 per 1000 px while its
ceiling runs −0.091 and its wall −0.018. A **source off-frame right** is
refuted because a source lights every surface facing it, and the target's wall
shows +0.019/m at R² **0.001**. That left the floor's own material, and the LOOK
supported it beautifully — the target's planks carry a broad specular SHEEN band
and ours are dead matte, and gloss is the one effect that can live on a floor
and nowhere else, because a floor is viewed at a grazing angle where Fresnel
reflectance is large and a wall is not. **Refuted too**: roughness 0.40 → 0.08,
a fivefold change, moved dL/dx from −0.006 to −0.013. Gloss is the CARRIER of a
lateral asymmetry, not a source of one — a mirror floor in a symmetric room
still mirrors something symmetric.

So the asymmetry is real, it is on the floor plane and nowhere else, and it is
not any of the three cheap explanations. What our model lacks is a left-right
feature of that room which the frame does not show — the room's opening, most
likely — and that is a fact about the friend's room, not a setting.

## GATE #9 — พร้อมให้ตัดสิน

**Pair**: `_private/…/look/trn001_gate9_r9wash.png` (target ‖ ours), against
`trn001_gate9_r8gate.png` for the before. Crops: `…_crop_floor.png`,
`…_crop_altar.png`.

1. **SHIPPED and measured**: the wall-wash round moved every one of the twelve
   ladder patches toward the target and none away, aggregate 3.26 → 2.01. It
   made two things worse and they are named, not buried: header_face 0.78× →
   0.66×, plinth_face 1.00× → 0.77×, and p99/p1 fell 73.6 → 53.5 against a
   target of 141.4. More bounce lifts p1 (0.0120 → 0.0137) when the target wants
   0.0055 — **the target's darkness is not a bounce deficit, something there
   absorbs**, and that is now the lane's clearest open question.
2. **Owner's call, not mine**: the fill's two refutations were both measured on
   a light aimed 180° away from where the note says it pointed. Re-open it, or
   leave it convicted?
3. **The ramp**: our rig cannot produce a left-right floor gradient because it
   is symmetric by construction. Building the room's asymmetry means inferring
   something the frame does not show. Do we infer it, or do we stop the light
   lane here and take the round's remaining budget to the floor MATERIAL, which
   the LOOK says is the most visibly wrong surface in the frame (planks nearly
   uniform where the target's vary strongly, no sheen at all)?

**Spend, round 9**: 30 quick renders (~12–15 s each), **1 full frame** (89 s),
0 external calls, 2210 tests green. R1 not tripped: one mechanism, one build.
Critic ladder: C0 instruments ✓, C1 builder LOOK + reference ✓ (native-resolution
crops, never upscaled). **C2 cold critic and C3 cross-vendor NOT run** — this
session is not spawning agents; both are available on your word.


**Round-10/11 (2026-08-01, owner: "ทำต่อให้มันจบซักที จะได้ตกผลึก").**

**A CACHE MISS READ AS A SOURCE GAP.** Round 5 closed the styling rung on "the
pool holds 13 models". 13 was the count of `assets/shared/cc0/models` ON THIS
DISK. The real Poly Haven pool is 521 and was searched exhaustively: its only
flowers are Namaqualand field flowers and ground cover, its only figures a gothic
statue, a marble bust, a horse and three bronze sea animals. The conclusion
survives on the full pool; the evidence never supported it. Same shape as the
vault search that ran in the wrong language.

**And the SPLIT the refusal actually licensed.** Decision (ข) guards religious
statuary — "used respectfully as-is" — and cut flowers are ordinary props that
reasoning never covered. So the lilies are built and the figures are not, and the
figures' absence is now a STUDIO capability gap (every Thai job with a prayer
room meets it; a zero-baht CC0 pool does not supply it) rather than a defect of
this reproduction.

**Four things the numbers alone would not have fixed**, each caught by putting
the built spray beside the reference: heads at 0.17 of spray height landed as
SEPARATE blobs 36 px wide where the target's spray is one connected mass 111 px
wide; six tepals at width 0.58L merged into a trumpet where a lily shows daylight
between every petal; every head aimed along its own stem read as a splayed
starfish, because in the reference the flowers face the VIEWER; and the stems
carried no leaves, which no magenta mask can see because a leaf is neither petal
nor background to it.

**Two measurement lessons, both paid for in renders.** (1) **Albedo response here
is albedo^0.35, not linear** — the first correction scaled albedo by 2.15x and
moved the rendered petal by 1.30x, because AgX has a shoulder and these petals
sit well up it, so a linear correction under-shoots forever. (2) **Two metrics
that share a threshold are not two measurements** — extent was read off a mask
keyed on absolute chroma AND absolute brightness, so darkening the petals to fix
their COLOUR dropped pixels out of the mask and the spray appeared to shrink 30%
while its geometry never moved. The envelope was scaled 1.36x to chase it, and
re-measured against distance-from-the-local-wall the spray had been the right
size all along (168x219 px against 172x218).

**THE ROOM IS 105 mm TALLER THAN NINE ROUNDS ASSUMED**, and the error was
invisible because it was self-consistent: every landmark the solve could see sat
on the header band's BOTTOM arris, which was already right, while the edge it
could not see was 73 mm out. **A least-squares fit can only test the geometry you
told it about** — the same sentence round 1 wrote about the 360 mm tower depth,
paid for again. Three detectors put the target's unit top at z=2773 (two with
controls reproducing our known 2700 to 2 mm; a third failed its control by
-32 mm and was read only for the OFFSET, where it agreed at +66 against +73).
The ceiling is a SEPARATE number — back-projecting a top edge onto an assumed
header setback trades ceiling height against header depth — and was closed with
an instrument containing no header in it at all: the side wall's FLOOR junction
fixes its plane, its CEILING junction then gives the height. Ceiling 2805, header
top 2773 hanging 32 below it, header depth 93.

**And the downlight row was internally inconsistent with its own spec.** The
recorded "both 605 mm off the wall to within 0.5 mm" is not reproducible from the
lens discs at ANY ceiling height, and the coplanarity that justified it is
VACUOUS as a height argument: two lamps in one row are coplanar in y at every
candidate ceiling for this camera. Round 9 argued its wall-wash from "605 mm on a
2700 ceiling"; the real setback is 522 under 2805.

**The floor's texture was never missing from the map.** Band-passed to the
7-60 mm band it is projected onto, the CC0 map measures robust sd 0.0869 and the
target's floor 0.0852 — a match — while ours delivered 0.0388. A DELIVERY
problem, which no amount of hunting for a better texture set would have found.

**Five reads of one number.** How far apart in R/B the rail and the carcass sit,
measured on the same target, returned 1.254, 1.401, 1.499, 1.95 and 2.05 —
differing only in which part of each surface was sampled. Raw R/B on a mapped
wood at this scale is not a material descriptor, so veneer_pier was NOT changed
and only the fascia moved, on the consensus of the two reads that cancel the
light by dividing by a white wall at the same height.

**A guard that compared an albedo ratio to a rendered number**, and blocked the
correction it existed to enable. The table-to-frame transfer is itself measurable
(x1.202 here), and magnitude now belongs to the instrument that reads frames.

**AND MY OWN FLEET FILTER SILENTLY FAILED.** The refuters returned each verdict
prefixed "CLAIM 1 — ...", the survivor filter matched claim strings exactly, so
nothing matched and "24 findings survived" counted findings that were never
paired with their verdicts at all — the returned build order ranked #3 a claim
its own refuter had killed in detail. Every item was re-checked against the
verdicts by hand. **A filter that matches nothing looks exactly like a filter
that rejects nothing.**

## GATE #11 — พร้อมให้ตัดสิน

**Pair**: `_private/…/look/trn001_gate11_r11.png`. **Blind finish sheet**:
`_private/benchmark/look-bench/blind_trn001_blockout_r10_s0.png` (the answer key
sits in the `.ANSWER.txt` beside it — do not open it first).

1. **THE FINISH TEST IS READY AND IT IS YOURS TO RUN.** Look at the blind sheet
   and say which panel is ours. If you cannot, or you pick wrong, TRN-001 CLOSES
   and the lane moves to the next image. A fresh sheet on r11 is one command.
2. **The ladder is flat this round and that is expected**: aggregate |abs-1|
   2.01 → 2.09, while the round's gains were GEOMETRY (room height, box, marble)
   and floor MATERIAL, neither of which a light ladder can see. What it did
   report for the first time in this lane's history is *ABSOLUTE COMPARISON
   VALID* — the two frames' medians are 1.043 apart.
3. **Still open, in order**: everything wooden in our frame is lighter in VALUE
   than the target's (a whole-palette claim, and the first thing a client sees
   after the missing figures); the marble's veining is far fainter; p99/p1 is
   51.7 against 141.4 and the fleet's best explanation for it was refuted three
   separate ways, so the absorber is still unnamed.

**Spend, rounds 10-11**: 20 quick renders, 3 full frames, one 11-agent fleet
(2.38 M subagent tokens, 5 diagnostic lanes + 5 adversaries + 1 planner, 0
errors), 2211 tests green. Critic ladder: C0 ✓ C1 ✓ (native-resolution crops),
C2 cold critic and C3 cross-vendor NOT run.


**Rounds 12-18 (2026-08-01, the figures).**

**THE REFUSAL IS WITHDRAWN.** Owner: *"ไหนพระล่ะ"*. Round 5 declined to model the
images and round 10 upheld it, both citing decision (ข)'s *"religious statuary
used respectfully as-is"*. That is a rule about ASSETS — do not distort a scan to
make it fit — and it never said do not model one. A prayer room with no image in
it is not a reproduction of a prayer room, every Thai visualiser puts one in, and
the room being copied has three. **Over-caution wearing the costume of respect**,
and it cost two rounds.

**Then the owner asked a working designer and the answer was 3D Warehouse** —
which `knowledge/_inbox/interior-ai/2026-07-01-asset-sourcing-DR.md` does not
mention at all, while our own DISTILLATION-LEDGER already recorded that the same
DR fabricates its prices and licences. Our files pointed there from three
directions (the SketchUp interop law, `build_room.rb`, a SketchUp/3ds Max Discord
corpus) and none of it was followed. CLAUDE.md gains a PRACTITIONER RUNG in front
of the whole research ladder; the ฿0/CC0 sourcing clause is cancelled and
propagated; `warehouse.py` and `scripts/asset_license.py` land.

**R8 CUTS BOTH WAYS, and this round is the demonstration.** The FIGURE is
acquired, because free form cannot be measured. Its stepped BASE is built, from
the same `BASE_CANON` the hand-built figure used, because boxes with ledges can.
*Acquire what cannot be measured, build what can.*

**A chain of my own errors, each caught by the owner's eye, each a general
shape.** Searching in English only returned seven well-made figures that were all
the WRONG IMAGE (East Asian dhyana, not Thai bhumisparsha) — a model can be far
better made than anything we could build and still be the wrong object. The one
that shipped was a **FLAT COIN**, depth/width 0.29, and the proof was printed in
my own output and unread: the width profile that found the pedestal join also
printed a DEPTH column sitting at a constant 0.74 m while the width fell from
3.36 to 0.04. I then rendered it from the one camera angle a cutout survives —
the script's own comment reads *"STRAIGHT ON, because a mudra is read from the
front"*. **One viewpoint is not a look.** Guard now code: an acquired figure must
measure depth/width ≥ 0.45 AND vary ≥ 25% in depth down its height, verified by
pointing it at what shipped.

Then three rounds of the same shape, each named as an instance and not as a
class: **a constant drawn around one object is not a constant** — base WIDTH from
a canon drawn for the hand-built figure, an x nudge that centred the figure on
the BOX while sliding it off its own BASE, and base DEPTH (`BASE_CANON`'s
depth/width is 0.75, the acquired figure's is 0.54, so the base jutted 24 mm
toward the camera). The last one hid from every measurement taken along x:
**bbox centres agreed to 0.5 mm and the contact bands to 0.0** while the object
still read wrong. And a nudge folded into asset space was multiplied by the
placement scale k=0.0798 and moved 2.7 mm instead of 33.4 — **a correction
expressed in the wrong space silently does almost nothing.**

`TRN001_GEOCHK=1` now dumps built widths, centres and contact bands — and it grew
three times, each time just far enough to answer the question last asked. It
still prints nothing about depth, which is what round 18 turned on.

## GATE #12 — พร้อมให้ตัดสิน

**Pair**: `_private/…/look/trn001_gate15_r17.png`; latest frame
`trn001_blockout_r20.png`. **Blind finish sheet**:
`_private/benchmark/look-bench/blind_trn001_blockout_r13_s0.png`.

1. **The room is now complete** — three images, both florals, candlesticks, the
   corrected room height, the rebuilt floor. Nothing in the reference is missing
   from ours any more, which means **the finish test can finally be run as
   written**: pick our frame out of the blind panel, and if you cannot, TRN-001
   closes.
2. **Still open and unchanged by these rounds**: everything wooden reads lighter
   in VALUE than the target's; the marble's veining is far fainter; p99/p1 is
   51.7 against 141.4 with the absorber still unnamed. The figures were a
   styling lane, not a light one.
3. **Owner's call, carried forward**: the fill's two refutations were measured on
   a light aimed 180° away from where the note says it pointed. Re-open, or leave
   convicted?

**Spend, rounds 12-18**: 7 full frames, ~25 quick, 13 models fetched and
measured (7 rejected on scale, 1 on flatness, 1 on iconography), 2212 tests
green. Critic ladder: C0 ✓ C1 ✓ — C2/C3 not run.


**Round 19 (2026-08-02, no render spent — the instrument round).**

**THE LANE'S PALETTE SHEET HAD BEEN CARRYING TWO NUMBERS THAT WERE NOT
MEASUREMENTS.** `trn001_matcheck`'s two stile rows reported 2.50x and 0.95x, and
the 2.50 was the largest number on the sheet. An id mask rendered off the same
build says what they sampled: at this camera `tower_R_sA` is **20 px** wide on
screen and `tower_R_sB` is **17 px**, because those panels are 18 mm thick and we
see them EDGE ON. The 2.50 was a sliver of a panel's thickness. The outer row's
box ran u1946-1956 against a feature ending at u1954 — two of its ten columns
were off the object.

`_check_narrow` passed both, and was right to by its own logic: a 10 px box is
fine on a 400 px panel. **It asks whether the BOX is narrow when the question is
whether the FEATURE is, and no box can answer that about itself.** Same family as
the bounding box that could not tell a vase from a plank and the return band that
could not tell a shallow box from a deep pocket — the instrument measured itself
instead of its subject. `audit_against_mask` now asks the renderer, `--mask`
wires it in where the numbers are made, and `_check_narrow` checks BOTH axes
(round 18 lost three rounds to a defect that hid in the axis nothing measured).

**AND THE SAME MASK MAKES THE HAND-PLACED TABLE LARGELY OBSOLETE.**
`compare_objects` reads the median of EVERY object in BOTH frames off one pixel
set — 39 surfaces instead of 9 boxes, no placement, no slivers by construction.
Its first run overturned the sheet's biggest surviving claim: **the altar step
reads 2.38x too bright from a 140x30 box and 1.02x over the whole 120,103 px
object.** A 30 px band on a graded surface is not that surface. The declared
limit, which is the only thing here to distrust: the mask is OUR geometry, so a
row is a comparison only where our geometry lands on the target's — hence the
6 px erosion and the px count on every row.

**WHAT THE 39-OBJECT TABLE THEN SAID, AND IT IS NOT WHAT ANY EARLIER ROUND
BELIEVED.** Sorted by height, the horizontal surfaces:

| surface | z mm | px | target | ours | delta |
|---|---|---|---|---|---|
| floor | -50 | 673266 | 165.2 | 160.3 | **-4.9** |
| tower_L_shelf0 | 597 | 1261 | 44.2 | 118.1 | +73.9 |
| tower_R_shelf0 | 597 | 4615 | 59.2 | 113.4 | +54.2 |
| tower_R_shelf3 | 1957 | 5316 | 22.0 | 44.6 | +22.6 |
| tower_L_top | 2421 | 2810 | 19.3 | 46.5 | +27.1 |
| tower_R_top | 2421 | 9030 | 20.3 | 42.0 | +21.7 |
| ceiling | 2855 | 449509 | 154.4 | 158.8 | **+4.4** |

**Every horizontal surface inside a cubby is 1.9-2.7x too bright. The two
horizontals that are not inside a cubby — floor at 673 k px and ceiling at 449 k
px — are both right to within 3%.** That is not exposure and not albedo.

**AND THE LANE HAD BEEN TUNING THE ONE CUBBY SURFACE THAT AGREES.**
`tower_R_back` is 230,233 px — bigger than the other seven pocket surfaces
together — and it measures **0.99**. It is also where the hand table's
"cavity (cubby interior)" box sits. Round 12-18 raised the cavity albedo 0.05 →
0.15 to bring the back panel up, the back panel came up, and the seven surfaces
around it stayed where they were: `tower_L_sA` 1.57 (60 k px), `tower_L_back`
1.59 (52 k px), `tower_L_sB` 1.59 (19 k px). **The cavity's own note said the
mouth was running 1.42x too bright; it is still true, now measured over 60,000 px
instead of a hand box, and the albedo change never addressed it.** The veneer
rows carry a written warning against exactly this — "cooling it would pay for the
light's error inside the material table, permanently" — and the cavity row is
where it happened.

**Second mass-weighted finding: all four plinth faces are 0.77-0.86x** (172 k px
together, deltas -28 to -48) **while the plinth's TOP is 0.97.** An albedo error
cannot make a top right and its four faces dark.

**Whole-frame, the one large difference:** the target puts 1.56% of its pixels
under luma 20 and we put 0.04% — 65,514 px against 1,349. A 16-cell map places
55% of the target's darks in the two cubby columns, which agrees with
`_cove_refuted`'s 93.2% and with the picture (`look/trn001_darks.png`).

**REFUTED THIS ROUND, BY ME, AGAINST MY OWN FIRST READ.** I proposed that the
target's palette sits in three tiers with an empty band between wood and white,
and that our altar had climbed out of the wood tier. A whole-frame histogram
kills it: **43.1% of the target's pixels live in that "empty" band against our
47.4%.** The tiers were an artefact of having chosen nine boxes. Also killed: a
context crop read OPPOSITE in sign to the numbers on two rows — flat swatches on
a grey surround settled it, and the numbers were right. **A crop with a surround
has a known way to lie; look at swatches when the question is value.**

**Also fixed, and it was not a measurement problem.** `id_mask.py` wrote its PNG
with `scene.render.filepath` and its sidecar with `open()`. On Windows those
disagree about a drive-less relative path — Python resolves against the CWD,
Blender against the current DRIVE ROOT — so the image landed in `C:\_private\`
and the JSON in the repo, and the run printed OK. **The half that escaped carried
a client scene's pixels, outside every `.gitignore` written to contain it.** One
function, two writers, two notions of "here"; `value_probe.mask_paths` resolves
once for both.

## GATE #13 — พร้อมให้ตัดสิน

**Sheets**: `look/trn001_darks.png` (where the target is dark and we are not),
`look/trn001_altar_pair.png`, `look/trn001_swatches.png`,
`look/trn001_patch_audit.png`. Frame unchanged: `trn001_blockout_r20.png`.
**The blind finish sheet is still the open test**:
`benchmark/look-bench/blind_trn001_blockout_r13_s0.png`.

1. **No pixel of the render changed this round and that is the result.** Two
   instruments were wrong, one of them was writing client pixels outside the
   repo, and the numbers the next build would have been steered by included a
   2.50 and a 2.38 that are now known to be artefacts. Building on them first
   would have bought a round of chasing them.
2. **The light question is now stated in mass, not in boxes**: seven cubby
   surfaces at 1.6-2.7x with the eighth — the biggest, the one the lane was
   watching — at 0.99, and four plinth faces at 0.8 under a plinth top at 0.97.
   Both say light is distributed wrongly, not that a material is wrong.
3. **Owner's call, carried forward unchanged**: the fill's two refutations were
   measured on a light aimed 180° away from where the note said it pointed.
   Re-open, or leave convicted? And gates #4-#12 remain unanswered.

**Spend, round 19**: 0 beauty renders, 1 id-mask probe (2.2 s), 0 quick renders,
10 new tests, 2347 green, guards 88/0.
