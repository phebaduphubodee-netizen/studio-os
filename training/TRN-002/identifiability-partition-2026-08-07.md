# TRN-002 — IDENTIFIABILITY PARTITION over `spec_r27.json` (62 masses)

> Read-only analysis, 2026-08-07. Every claim carries `file:line`.
> Source: `training/TRN-002/spec_r27.json` (1,471 lines, 62 masses),
> `training/TRN-002/gate-15-r27.md`, `pipeline/scripts/trn002_lightcheck.py`,
> `pipeline/scripts/rule_gate.py`, `qa/reproduction-curriculum.md`.

## Why this exists

The charter argues the loop terminates because *"The target image EXISTS →
'เหมือนงานเพื่อน' is a falsifiable finish line … The loop terminates"*
(`qa/reproduction-curriculum.md:12-15`). That is true only if the target
CONSTRAINS every free parameter. It does not. `gate-15-r27.md:10-11` records
the proof: closing the wardrobe slot destroyed the right wall's last
independent evidence, and *"ความกว้างห้องกับความลึกตู้กลายเป็นตัวไม่รู้ตัวเดียวกัน"* —
one equation, two unknowns, a cabinet now 1,290 mm deep against a 600-650 mm
built-in norm (`spec_r27.json:100`).

**What this partition finds is that the same collapse exists on the LEFT wall
and is undeclared**, and that the frame in general constrains PROJECTIONS, not
METRICS. That distinction is the whole result.

### Verdict rule (mechanical, reproducible)

Each mass has four quantities: extent-X, extent-Y, extent-Z, POSITION.
An extent counts as constrained only when **both** bounding faces are M or
D-on-M; D-on-A does not count. POSITION counts as constrained when a measured
landmark or contact pins the object's datum.

- **IDENTIFIABLE** = 4 of 4 constrained
- **PARTLY** = 1-3 of 4
- **UNIDENTIFIABLE** = 0 of 4

| bucket | count |
|---|---|
| IDENTIFIABLE (4/4) | **0** |
| PARTLY (1-3 / 4) | **59** |
| UNIDENTIFIABLE (0/4) | **3** |

A second, more operational number is given in §(c): **24-26 masses whose
projected SILHOUETTE is fully constrained.** That set — not the 4/4 set — is
what a per-object ladder score requires, and it is derived from the INPUT, so
it cannot move when our render moves.

---

## (a) The partition table

Codes: `x / y / z · pos`. `M` measured feature, `D` derived from a measured
contact, `A` assumed / occluded / no constraining feature. `D*` = derived from
a contact that is itself A (counted as A).

| # | mass | x/y/z · pos | what CONSTRAINS it | what does NOT | verdict |
|---|---|---|---|---|---|
| 1 | `floor` | A/A/A · M | top plane z=0 from the sill; joint darkness anchors the plank phase (`:47`) | every edge of the 4750×9500 slab — both walls are A and the room's depth in y was never measured | PARTLY |
| 2 | `back_wall` | A/A/M · M | H=3102 from the junction ratio; plane y=0 is the camera datum | its WIDTH. `seen:64` still offers the corner arris at u=730.0±0.5 as its evidence, but `right_wall:98` records r27 giving that edge to the cabinet: *"the edge alone cannot tell them apart"* | PARTLY |
| 3 | `left_wall` | A/A/M · **A** | ceiling height only; one hard BOUND x ≤ −4724 (console corner exits frame-left, `:81`) | its x. `seen:82`: *"Its x cannot be measured from this view — the plane is near edge-on, so it carries no scale, and every landmark that could pin it … belongs to another zone"* | PARTLY (x unidentifiable) |
| 4 | `right_wall` | A/A/A · A | nothing | `prov:98` *"x=0 now rests on nothing measured"*; `seen:99` *"NO. Not one pixel."* | **UNIDENTIFIABLE** |
| 5 | `ceil_main` | A/A/A · M | z=3102 from the junction ratio (`:115`) | plan extent (inherits both A walls); 100 mm slab typed | PARTLY |
| 6 | `ward_bulkhead` | A/A/M · M | course z≈2920 backprojected at six u-stations; far end y=−2290.8 fitted subpixel, sd 0.05/0.06, 250/250 rows (`:131`) | depth in x (runs to the A right wall); near end −6500 is off-frame | PARTLY |
| 7 | `ward_body` | A/A/M · M | bottom z=938±33 at 6 u-stations; top 2920; far end −2290.8 (`:148`) | the 1,290 mm DEPTH — half of the declared `right_wall_x` gap, yet prov carries no A tag | PARTLY |
| 8 | `ward_groove` | A/A/A · M | z=2668 confirmed against 15 traced stations to ~1 px (`:165-166`) | 6×30 mm section (sub-pixel); BOTH y ends — still −2550…−6500 (`:156,161`), i.e. 259.2 mm short of the cabinet after r27 | PARTLY |
| 9-13 | `rev_1`…`rev_5` | A/A/A · M | y from subpixel verticals, sd ≤0.03 px over five v-bands (`:182,199,216,233,250`); four are HELD-OUT judge lines (`:1436-1442`) | the 6×8 mm section (the target's own reveal measures 1.05 mm = unresolved at this camera, `triage-debt-2026-08-07.md` C3#6); z ends 895/2665 unmeasured | PARTLY ×5 |
| 14 | `door_leaf` | A/M*/M · **A** | both shadow-gap edges (u=630.0, 685.0) → 869.7 mm leaf; head trim → z=1914 (`:267`) | *the plane it was measured ON.* `gauges.open_tension:20`: *"door standards want ~−960..−976. ADOPTED r2"* — the leaf's width is computed on x=−974, so it scales with an assumed plane; 14 mm thickness typed | PARTLY |
| 15 | `artwork` | M/A/M · M | subpixel half-max on the 21 mm black bar, u 464.85..562.63, v 315.26..456.19 (`:285`) | 30 mm depth — face-on plane carries no depth | PARTLY |
| 16 | `part_head` | M/A/M · M | dark band backprojected on y=0 → 107.2 mm vs spec 107; level confirmed at two u (`:302`) | 70 mm depth (face-on) | PARTLY |
| 17 | `part_jamb_L` | A*/A/D · M | outer edge to 0.9 mm (`:319`) | the built 64 mm member: the target shows **two faces of 47.2 and 47.0 mm** with a hairline joint at u=155.0 | PARTLY |
| 18 | `part_jamb_R` | A*/A/D · M | front face x −2648.2..−2606.0 (`:336`) | built 64 vs **measured 42.2 mm**; the left sub-strip is a reveal receding into the closet | PARTLY |
| 19 | `part_stile_M` | A*/A/D · M | two bar positions (`:353`) | `seen:353` *"NOT as one member. Two dark bars with a bright gap … Total span 144.5 mm. Spec's single 72"* — the frame REFUTES the built member | PARTLY |
| 20 | `part_rail_B` | M/A/M · M | z 0..~52 vs spec 0..60, 0.5 px (`:370`) | 60 mm depth (face-on) | PARTLY |
| 21 | `closet_floor` | A/A/A · M | z=0 confirmed through the right bay (`:388`) | `why:387` *"Its dimensions are unmeasurable from this camera (the far-room geometry is behind glazing) and are not claimed"* | PARTLY (dims unidentifiable) |
| 22 | `closet_back` | A/A/A · A | nothing dimensional; only brightness (Ylin 0.812, `:405`) | `seen:406` *"NOT as modelled"* — the target shows a full-height wardrobe with a lit niche and a white door with a black lever | **UNIDENTIFIABLE** |
| 23 | `desk` | A/A/M · A | top z=875 confirmed at u=133; apron 185 from the apron groove (`:422`) | **depth 410 and therefore x**: it is the closing assumption for the left wall (`:81`), and `prov:422` contains no depth measurement at all. Length 2995 ends off-frame / typed | PARTLY |
| 24 | `console` | A/A/M · M | front −4495±8, top 753±22, thickness 258±10; float 495 (`:441`, `gauges.console_float:23`) | 255 mm depth (runs to the A wall); far end −3445 typed; `A-swept(end y −5160)` declared in prov | PARTLY |
| 25 | `tv` | A/A/A · M | silhouette u 9..40.78 incl. the HELD-OUT judge line `tv_right` (±0.05 px over 95 rows) (`:460`) | its METRIC. `why:463`: *"the standoff … is UNMEASURABLE … at 25/40/80 mm the panel comes out 56/53/43 inch and projects to the IDENTICAL silhouette"* | PARTLY (silhouette M, size A) |
| 26 | `rug` | A/A/M · M | left edge x=−3795 and far corner y=−1843, both fitted as lines (`:478-479`) | right end (`A(right end clipped at ward face)`), near end; 12 mm thickness ≈ 0.5 px at that range (`gate-15-r27.md`) | PARTLY |
| 27 | `bed_platform` | D*/M/M · M | both long sides from the platform's OWN edges: near −4180 from two independent lines agreeing to 0.2 mm, far −2105±20, plinth 221 (`:495`) | the head end −1490 rides the x=−1290 chain (below) | PARTLY |
| 28 | `bed_mattress` | D*/M-D/M · M | near face −3985±14; foot face −3394 from a contact-shadow line constant to 1 mm over 6 pts; far face D with contact bounds −2230..−2290 (`:514`) | head end rides x=−1290 | PARTLY |
| 29 | `bed_headboard` | A/A/A · M | near end u=1027.5 → y=−4745 (`:533`) | far end: *"kept at the band start −2550: its only direct read, −2401..−2581, dies at u~730 = the room corner's pixel column"* — the same ambiguity r27 proved; 176 mm thickness and 915 top typed | PARTLY |
| 30 | `ward_band` | A/A/M · M | top edge fitted v=477.0→511 reproduced to <1 px; z 0..938 (`:550-551`) | far end: `prov:550` *"Occluded in this frame either way; declared, not measured"* — its own fit says −2540±1.1 (12 of 52 rows, all behind the headboard) but it is built to −2290.8 | PARTLY |
| 31 | `nightstand` | A/A/A · M | top z≈481; front-face arris (`:567-568`) | prov cites an arris of **426 mm** (y −4706..−5132) for a mass built **700 mm** long (−4600..−5300); the 350 depth is the PLANE the arris was backprojected on, so it cannot also be its result; front face is cut by the frame at u=1080 | PARTLY |
| 32 | `bench` | A/A/M · A | one scalar: `prov:584` = *"M(top mid backprojection at z=420)"*; hard boundary against the petcave at u≈951 | the 1050 × 600 plan and the position carry NO provenance; `seen:587` — runs off the bottom of the frame | PARTLY |
| 33 | `petcave` | A/A/A · A | that SOMETHING is there (u 951..1080, arch apex at (1043,752)) | `prov:603` = `A(identity open …)`; `why:606` *"six blind critics have each bound it to something different"*; the cited floor point (−1599,−4392) is 1.4 m from the built centre | **UNIDENTIFIABLE** |
| 34-37 | `dl_1`…`dl_4` | A/A/A · M | four compact peak-255 blob centres, flush at z=3102 (`:623,639,655,671`; `gauges.downlight_table:22`) | Ø120 and the 10 mm proud: a CLIPPED core has no measurable extent — its size is an exposure artefact | PARTLY ×4 |
| 38 | `desk_pier` | D/A/D · M | y=−2131 mean of 16 floor-contact backprojections, spread −2115..−2151 (`:687`) | `why:688` *"Its y-DEPTH remains unmeasurable (occluded)"* — and s[1] is still **60.0** (`:683`) | PARTLY |
| 39 | `lamp` | A/A/D · M | shade silhouette u1057-1080 v484-508 with hard containment: no pixel left of u=1057 (`:705`) | the whole body — occluded in the target by a bird sculpture and a book stack (`:708`) | PARTLY |
| 40 | `chair_seat` | A/A/M · M | three foot contacts on z=0; seat top 450.5 and underside 297.5 both backprojected (`:728`) | the 600×620 plan (prov even under-claims: it tags `A(seat 450 vanity norm)` for a height its own `seen` measured at 450.5) | PARTLY |
| 41 | `chair_back` | A/A/M · D | top z≈774 on the far-leg plane vs built 780 (`:748`) | `seen:748` — the target's backrest is *"a single curved tub shell that wraps the back AND both arms"*; ours is an 80 mm panel | PARTLY |
| 42 | `shelf_col_back` | A/A/M · M | column top 3027 fitted over 38 columns, the +6.0 px slope ruling out the y=−60 plane; right end = the measured jamb outer −4292.9 (`:764`) | left end rides the A wall; 60 mm depth | PARTLY |
| 43 | `shelf_board2` | A/A/M · M | both edges fitted over 27 columns, 1339.0±1.0 / 1386.4 (`:784`) | 400 mm depth, declared `A-swept` in prov (`:781`) | PARTLY |
| 44 | `shelf_board3` | A/A/A · M | lower edge 1866.3±0.6 over 27 columns (`:800`) | upper edge = +48 assumed; and the SAME 400 mm depth that board2/board4 tag `A-swept` is untagged here | PARTLY |
| 45 | `shelf_board4` | A/A/M · M | lower 2392.4±1.5, upper band 2425..2455 (`:822`) | 400 mm `A-swept` depth | PARTLY |
| 46 | `floor_planks` | A/A/A · M | **the strongest measurement in the file**: w=132.1±0.6, L=619.6±0.8, 45°, phase anchored, 20 independent line fits, two families agreeing to 0.05 mm (`:839`) | field extent (inherits the floor) and 6 mm thickness | PARTLY (pattern IDENTIFIABLE) |
| 47 | `door_rev_near` | A/A/D · M | u=630.16/630.01/629.80 across three v-bands (`:855`) | 6×6 section (sub-pixel) | PARTLY |
| 48 | `door_rev_far` | A/A/D · M | u=685.0 (`:872`) | 6×6 section | PARTLY |
| 49 | `door_rev_head` | A/D/A · M | head band v 300..316, fitted dv/du=−0.1888 over 13 points (`:889`) | 6 mm section | PARTLY |
| 50 | `door_handle` | A/M/M · M | lever blob u 669..683, v 452..468 → y and z extents; the darkest pixels on that wall (`:906-907`) | `A(projection 56 mm off the leaf face - a lever's stand-off is not measurable at 14 px, so it is declared, not derived)` | PARTLY |
| 51 | `art_mat` | D/D*/D · D | fully derived: inset by the measured 21 mm bar on four sides, 2.5 mm proud (`:924`) — the cleanest derivation in the spec | its y datum stands on the artwork's ASSUMED 30 mm depth, so it is D-on-A | PARTLY (nearest to identifiable) |
| 52 | `door_wall_near` | A/M/M · A | y 0..−259.8: back wall M at one end, the leaf's measured near edge at the other; z 0..3102 (`:941`) | 100 mm fin thickness and the fin's x plane (door standards, `gauges:20`) | PARTLY |
| 53 | `door_wall_far` | A/A/M · A | near edge −1129.5 = the leaf's measured far edge | far edge **−1200 is typed**, so this 70.5 mm sliver has one measured and one invented boundary | PARTLY |
| 54 | `door_wall_head` | A/D/M · A | leaf span D-on-M; z 1914.2..3102 both M | fin thickness/plane | PARTLY |
| 55 | `door_jamb_back` | A/D/D · D | derived from the opening (`:992`) | 86 mm = typed 100 minus typed 14; `seen:993` *"NOT VISIBLE at this camera"* | PARTLY |
| 56 | `duvet` | M/A/A · M | footprint measured through the solved camera: head crease on z=545, foot hem on x=−3394 → z 216-227, near cascade hem corners z 204/160/113/43 (`:1048`) | `A(far-side hang: self-occluded, UNMEASURABLE - fed 250 mm and declared; band 200 …)` | PARTLY |
| 57 | `pillow_L` | A/M/M · M | run 1610±150 = two ~800 shams; bases on the duvet at z=545; tops 860-930; lean 20-25° (`:1068`) | `A(thickness 180: a sham's loft, not measurable side-on)`; tops are white-on-white ±20 | PARTLY |
| 58 | `pillow_R` | A/M/M · M | body near end −4250±150; flap tip dangling to z≈472-485 (`:1089`) | 180 loft; the flap itself declared unmodelled | PARTLY |
| 59 | `cushion_taupe` | A/M/M · M | four corners on the leaning face plane; 668 mm top edge; slant 382-396; lean 37° (`:1109`) | `A(thickness 120)` | PARTLY |
| 60 | `bolster` | M/A/M · M | end-cap ellipse D=165±8 by a rest-z sweep; cap plane y=−4311 (`:1129`) | `A(length: far end fully occluded behind P2 and its flap - UNMEASURABLE, >=250 visible; 400 declared)` (`:1129`) | PARTLY |
| 61 | `throw_woven` | M/A/A · M | head-side edge on z=555; near tail solving to z=0 only for y −4300..−4400; far crest 624-656 (`:1185`) | 2600 mm length (far end is *"a loose rolled bunch"*); thickness; fringe declared unmodelled | PARTLY |
| 62 | `throw_velvet` | M/A/A · M | foot-side edge 157-225 mm head-ward of the mattress arris; near hem z 206-208; far lip 474-486 (`:1239`) | 2500 mm length; thickness; piping declared unmodelled | PARTLY |

### The two structural collapses, side by side

| | RIGHT side | LEFT side |
|---|---|---|
| wall position | `right_wall_x = 0`, `A(UNMEASURED as of r27)` (`:98`) | `left_wall_x = −4750`, `A-banded` (`:31`), `seen:82` "cannot be measured" |
| what selects it | the wardrobe front x=−1290, which `gauges.G3:21` says was chosen by a **510 mm door-module standard**, and which explicitly **REFUTES** equal-modules as an instrument: *"cv is 0.0046 at every x in −1400..−518; the module WIDTH standard did the choosing"* | *"−4750 is the value at which the measured desk depth (410) closes"* (`:81`) — while `desk.prov:422` measures only z and contains **no depth measurement** |
| the joint unknown | room width ↔ wardrobe depth (1,290 vs a 600-650 norm) | room width ↔ desk depth 410 / console depth 255 |
| declared? | **YES** — `declared_gaps.right_wall_x:1466` | **NO** — nothing in `declared_gaps` |

**The left-hand collapse is the same defect, one round earlier, and nobody has
called it.** Both side walls of this room are placed by a joinery standard, not
by the image.

### And one gap that sits above every mass

`gauges.G1:19`: *"SWEPT r3: NOT ROBUST — cam_z band 1278..1338, H_main
3038..3180, lever dominates 2.5:1 … DECISION r3: do NOT rescale mid-lane."*
Every millimetre in this spec is expressed in a similarity whose absolute scale
is uncertain by **±2.3 %** (H 3102 ± 71). The render cannot see it; a
procurement claim can. It belongs in `declared_gaps` once, at the top, not in
the gauges where only the builder reads it.

---

## (b) Quantities that must become PERMANENT declared gaps

No future round can resolve these from this input. Each carries a stated
tolerance so a downstream reader can use the number without re-deriving the
doubt. **A permanent gap is not a to-do; it is a closed question with an
interval instead of a value.**

| # | quantity | why permanent (cited) | declare as |
|---|---|---|---|
| P1 | **room width ↔ wardrobe depth** (already declared) | `:100` — front measured x=−1290, back assumed to reach x=0; *"To settle it needs a datum this camera does not carry"* | either wardrobe depth **600 ± 50** (norm) → `right_wall_x = −690 ± 50`, or keep x=0 and record depth 1290 as non-physical. Room width uncertainty **±690 mm** |
| P2 | **room width ↔ desk / console depth (LEFT)** — NEW | `:82` plane is edge-on and carries no scale; only bound is x ≤ −4724 (`:81`) | desk depth **410 ± 50**; `left_wall_x = −(4340 + depth)`, one-sided bound ≤ −4724; console depth 255 and shelf x inherit |
| P3 | **room depth in y** (all shell masses built 9500 long) | nothing in the frame lies beyond the wardrobe's near end; the camera itself sits at y=−7992 (`:8`) | y_near ≤ −6500, otherwise **UNBOUNDED** — do not print 9500 as a dimension |
| P4 | **absolute scale of the whole spec** | `gauges.G1:19` cam_z 1278..1338, H 3038..3180 | every mm **± 2.3 %**; blocks procurement, invisible to the render |
| P5 | **TV panel size** | `why:463` — 25/40/80 mm standoff → 56/53/43 inch, IDENTICAL silhouette; *"a constraint that does not vary with the unknown cannot determine it"* | diagonal **50 ± 7 inch**, standoff 40 declared; pixel-invariant |
| P6 | **`bolster` length** | `:1129` *"far end fully occluded behind P2 and its flap - UNMEASURABLE, >=250 visible"* | **≥250 mm, unbounded above**; pixel-invariant. This is the answer to five successive critics: the object is real (cap ellipse D=165±8), its LENGTH is unknowable, and no round can change that |
| P7 | **sham / cushion loft** (`pillow_L`, `pillow_R` 180; `cushion_taupe` 120) | `:1068` *"a sham's loft, not measurable side-on"* | 180 ± 60 and 120 ± 40 |
| P8 | **duvet far-side hang** | `:1048` `A(far-side hang: self-occluded, UNMEASURABLE)` | 250 ± 150 |
| P9 | **every member depth on the y=0 plane** — `part_head` 70, `part_jamb_L/R` 60, `part_stile_M` 60, `part_rail_B` 60, `artwork` 30 | a face-on plane carries no depth, by projection | declare as ONE CLASS: depth declared, **±100 %**, invisible at this camera |
| P10 | **door-wall plane x and fin thickness 100** | `gauges.open_tension:20` — *"run-to-ceiling-3102 wants −940; door standards want ~−960..−976"* | plane **−958 ± 18**; and note the leaf's 869.7 mm width is computed ON it, so leaf width carries **±4 %** |
| P11 | **`desk_pier` y-depth** | `why:688` *"Its y-DEPTH remains unmeasurable (occluded)"* | 60 ± 60, or delete the mass to a declared gap (R10: the moment a pass says UNMEASURABLE, typing a number is the defect) |
| P12 | **`nightstand` length and depth** | the arris is cut by the frame edge at u=1080 (`:568`); the 350 depth is the plane the arris was projected on | length **≥426, unbounded**; depth 350 ± 100 |
| P13 | **`bench` plan and position** | runs off the bottom AND right frame edges (`:587`); prov is one scalar (`:584`) | only z_top = 420 is claimed; plan **UNBOUNDED** |
| P14 | **`petcave` identity + all three dimensions** | `why:606` — six critics, six bindings; *"a declared gap handed to the owner, not a modelling guess"* | hand to the owner as an identity/procurement decision (R8 / R10). Not a modelling round |
| P15 | **`closet_floor` / `closet_back` geometry** | `why:387` *"unmeasurable from this camera … not claimed"*; `why:405` *"Position assumed; only its BRIGHTNESS is answerable"* | no dimension claimed at all; the ONLY declared quantity is the aperture's luminance, Ylin 0.812 |
| P16 | **downlight aperture Ø 120** | the cores are peak-255 clipped (`:624` etc.); a blown blob's extent is an exposure artefact | Ø **120 ± 60**. Separately: their POOL is unidentifiable too — `gate-15-r27.md` measured the floor under dl_1 at 0.184 RISING to 0.220 a metre away, *"วงแสงที่นี่เครื่องหมายผิด"* |
| P17 | **`rug` thickness 12 mm** | ≈0.5 px at that range (`gate-15-r27.md`, C2#14 refutation) | 12 ± 10; the visible signal is pile + edge shadow, not thickness |
| P18 | **all groove / reveal sections** (`ward_groove` 6×30, `rev_1..5` 6×8, `door_rev_*` 6×6) | the target's own grooves measure 1.05 mm = *"unresolved ที่กล้องนี้"* (`triage-debt-2026-08-07.md`, C3#6) | sub-pixel; declare once, never iterate on any of them |
| P19 | **`ward_band` far end** | `:550` — its own fit gives −2540±1.1 but keeps 12 of 52 rows, *"every one of them behind the headboard … Occluded in this frame either way; declared, not measured"* | −2290.8 by structural closure, **±250**; the measured −2540 is refuted by occlusion, not by a better measurement |
| P20 | **`bed_headboard` top z 915 and thickness 176** | no prov entry; the only nearby reading is the pillow pass's *"headboard top 892-908"* (`:1068`), white-on-white ±20 | top 900 ± 20; thickness declared |

**Register health.** `declared_gaps` (`:1460-1467`) holds six entries. Two —
`lamp_stem:1462` and `shelf_col_base:1463` — are for masses that were REMOVED;
one — `duvet:1461` — declares cloth-sim licensing, not the far-side hang its
own prov calls UNMEASURABLE. **The live gap register is effectively two
entries (`artwork_relief`, `blind_slats`) plus `right_wall_x`, against the
twenty above.**

---

## (c) The scored subset — and why this is the fix for gate-15

### The mechanism gate-15 caught

`trn002_lightcheck.py:407-440` computes SHAPE as the px-weighted spread of
`ladder_error` about its mean, and drops rows by the instrument's own verdicts
(`alignment` OFF BY, `spread_ratio` > 2.0). Both verdicts are computed **from
the frame pair** — so a row can leave the set because OUR change moved it.
`gate-15-r27.md` measured exactly that: free membership gave SHAPE 0.2587 →
0.2000 (*"ดีที่สุดเท่าที่เลนนี้เคยวัดได้"*), pinned membership gave 0.1989 →
0.2000 — **r27 got 0.6 % WORSE**, and the whole apparent 23 % gain was one row
leaving the pile.

**The fix is not a better filter. It is a membership set that is a property of
the INPUT.** Identifiability cannot move when the render moves.

### The rule

A mass may carry a ladder score iff:

1. it is visible in the target (`seen` gives a pixel region), and
2. **every quantity that determines its projected OUTLINE is M or D-on-M**
   (dimensions along the view ray, invisible thicknesses and occluded ends do
   not matter — this is why metric-unidentifiable masses like `tv` and
   `bolster` can still score), and
3. the target region under our mask is the **same object** we model, and
4. it survives `min_px` after erosion (`trn002_lightcheck.py:281-285`) — a
   mechanical filter that stays.

Note what (2) buys: `ward_body`'s DEPTH is unidentifiable, but its front plane's
projection is validated subpixel by five reveals, the far silhouette and the
bottom edge — so its mask is right even though its metric is not. **Projection
identifiability and metric identifiability are different questions, and the
ladder only ever needed the first.**

### MAY be scored — 24 (+2 conditional)

`floor` · `floor_planks` · `back_wall`¹ · `ceil_main` · `ward_bulkhead` ·
`ward_body` · `ward_band` · `artwork` · `art_mat` · `part_head` ·
`part_rail_B` · `door_leaf` · `door_wall_near` · `door_wall_head` · `console` ·
`tv`² · `rug` · `bed_platform` · `bed_mattress` · `shelf_col_back` ·
`pillow_L` · `pillow_R` · `cushion_taupe` · `bolster`³ · `chair_seat`⁴

Conditional: `bed_headboard` — only after defect **D5** below is repaired;
`duvet` / `throw_woven` / `throw_velvet` — **VALUE only, with a pinned solver
seed, never in SHAPE**, because their outline is a solver output, not a spec
quantity.

¹ `back_wall` scores but **must not be the divisor.** `trn002_lightcheck.py:308-315`
picks the reference as the biggest clean row, and `gate-15-r27.md` measured that
**4.4 % of back_wall's own pixels read 0.14× while the other 163,871 read 1.23×
— an 8.8× split on one surface**, hidden by a median that is 1.00 by definition.
A surface with a known internal split disqualifies itself as a reference. Pin
`--ref` to `ceil_main` and pin it across frames.
² `tv` is legitimately scoreable: its silhouette is a HELD-OUT judge line
(`:1443`) and `gate-13-r25.md:24` records the new mask landing on the target's
real panel (target-side median 0.0538 → 0.0383, n 6,722 → 9,569).
³ `bolster` — cap region only; its length is P6 and cannot be judged.
⁴ `chair_seat` — advisory: feet and seat height are M, the 600×620 body is not.

### MUST be excluded — and why

| mass | reason |
|---|---|
| `right_wall` | 0 px by construction (`seen:99`) |
| `door_jamb_back` | *"NOT VISIBLE at this camera"* (`:993`) |
| `left_wall` | the target's pixels there contain the window aperture, which this spec **withdrew from the frame** (`declared_gaps.blind_slats:1465`); and its own silhouette is bounded by objects that ride the same unidentifiable wall x, so the row cannot fail independently |
| `dl_1..dl_4` | peak-255 clipped; `trn002_lightcheck.py:239` — *"every ladder row above the clip reads the same number"* |
| `closet_floor`, `closet_back` | our mask covers **another room's contents** in the target (`seen:406`) |
| `petcave` | identity open (`why:606`); comparing our clay lump's median to an unknown object is not a light measurement |
| `desk_pier` | `seen:689` *"NOT FOUND at its built location … row v=761, u=100..175 is flat 79..118 — bare herringbone"* |
| `lamp` | the body's mask covers a bird sculpture and a book stack in the target (`:708`) |
| `chair_back` | the target is a wrap-around tub shell, ours is a flat 80 mm panel (`:748`) |
| `part_jamb_L`, `part_jamb_R`, `part_stile_M` | built widths refuted by their own `seen` (64 vs 47+47; 64 vs 42.2; 72 vs 144.5) — a mask 1.5× the member samples wall on both sides |
| `door_wall_far` | a 70.5 mm sliver whose far edge (−1200) is **typed**. `gate-15-r27.md` reports this row moving 0.48 → 0.43 and charges it to r27 — a scored row bounded by an assumption is a scored assumption |
| `desk` | its visible sliver is bounded by the depth that closes the left wall (P2) |
| `bench`, `nightstand` | outline set by A dimensions and cut by two frame edges |
| `ward_groove`, `rev_1..5`, `door_rev_*`, `door_handle`, `shelf_board2/3/4` | below `min_px` after erode(3); grooves are sub-pixel at this camera |

### The membership law to wire

> SHAPE membership is computed **from the spec, before the render**, from the
> list above. `alignment` and `spread_ratio` stay as DIAGNOSTICS that WARN and
> may never remove a row. A row that leaves the set because our own change moved
> it is the tenth flattering scorer of this repo, and it has already happened.

The provenance-derived set (24-26) happens to be about the size of the 22-row
pinned set gate-15 used — but the members are chosen by the INPUT, so the
comparison is stable across rounds without anyone remembering to pin it.

---

## (d) Gaps declared but not honoured, honoured but not declared

**Root mechanism first.** `pipeline/scripts/rule_gate.py:119-124` accepts a
`why` **in place of** a `declared_gaps` entry. Running the gate on this spec
returns **0 violations** (`audit_spec(spec, require_seen=True)`), while at
least ten masses carry an unresolvable quantity. A prose `why` is read by a
builder; `declared_gaps` is read by a critic and by the next round. Secondary:
`ASSUMED_PART` at `rule_gate.py:61` is `\bA\b` with `re.I`, so it matches the
English article *"a"* — it fires on `dl_1`'s prov *"**a** disc hanging below the
plane"* (`:623`). The A-detector is noise on any prose prov.

| # | mass | the mismatch |
|---|---|---|
| **D1** | `left_wall` | `prov:80` `A(left wall x)`, `seen:82` *"cannot be measured"*, `audit:83` **UNRESOLVED**, `shell._left_wall_prov:31` `A-banded` — and **no `declared_gaps` entry**, while its exact twin `right_wall_x` has one (`:1466`). Honoured everywhere except the one place a critic reads |
| **D2** | `desk` ↔ `left_wall` | `left_wall.why:81` cites *"the measured desk depth (410)"* as the closing datum; `desk.prov:422` measures only z (top 875, apron 185) and carries **no depth measurement and no A tag**. The wall is placed to make the desk 410; the desk is 410 because it runs to the wall. Neither mass records the other |
| **D3** | `ward_body`, `ward_bulkhead` | `right_wall.audit:100` declares *"the room's WIDTH and the wardrobe's DEPTH are now one undetermined quantity"* — but `ward_body.prov:148` still reads `M(x_wall=−1290 equal modules …)` with no A tag, and `ward_bulkhead.prov:131` likewise. **A gap declared against only one of the two masses that share it.** Compounded by `gauges.G3:21`, which refutes equal-modules as an instrument in the spec's own words |
| **D4** | `ward_groove` | still spans y −2550..−6500 (`c:156`, `s:161`) while `ward_body` (`:124-129`), `ward_bulkhead` (`:141-146`) and `ward_band` (`:541,546`) all moved to −2290.8 in r27. **The groove now stops 259.2 mm short of the cabinet it runs on** — the exact quantity r27 added. `prov:165` tags M but covers only z |
| **D5** | `bed_headboard` | `prov:533` pins the far end at *"the band start −2550"*. The band's extent is now −2290.8..−6500 (`:541,546`). **The named datum moved in r27 and the dependent did not** — R9's own law: a position derivable from a contact must never be typed |
| **D6** | `desk_pier` | `why:688` states *"the 60 mm that was typed is gone"* — `s[1]` is still **60.0** (`:683`). And `seen:689` reads *"NOT FOUND at its built location"* while `prov:687` says the location was corrected to the measured mean −2131. One of the two texts is stale; either way the R10 item the owner raised on 2026-08-05 still carries a typed depth its own `why` calls unmeasurable |
| **D7** | `back_wall` | `seen:64` still offers the corner arris (*"spec projects (x=0,y=0) to u=730.64 → 0.6 px agreement"*) as this wall's own evidence, but `right_wall.prov:98` records r27 reassigning that edge to the cabinet. `audit:65` = **KEEP**. The wall's width is now unevidenced at BOTH ends while its `seen` cites evidence that left |
| **D8** | `petcave` | `why:606` says in its own words that such an object *"is a declared gap handed to the owner, not a modelling guess"* — and `declared_gaps` has **no petcave entry** |
| **D9** | `closet_floor`, `closet_back` | `why:387` / `why:405` say the dimensions are *"unmeasurable from this camera"* and *"not claimed"* / *"Position assumed"*; neither is declared. The word "unmeasurable" sits in `why`, not `prov`, so `rule_gate.py:119` (which reads `prov` only) never fires. `closet_back` is additionally **mis-identified**, not merely undimensioned (`seen:406`) |
| **D10** | `tv` | `prov:460` contains `DECLARED(standoff from the wall)` and `why:463` calls it UNMEASURABLE; **no `declared_gaps` entry**. Honoured impeccably — the pixel-invariance is proven — and invisible to anyone reading the register |
| **D11** | `bolster`, `pillow_L`, `door_handle` | all three say UNMEASURABLE / "not measurable" / "not derived" in `prov` (`:1129`, `:1068`, `:906`); all three are saved from the gate by a `why`; none is in `declared_gaps` |
| **D12** | `duvet` | the ONE key that exists (`declared_gaps.duvet:1461`) declares **cloth-sim class licensing**, not the far-side hang that `prov:1048` calls UNMEASURABLE. A gap key that declares a different thing than the gap |
| **D13** | `shelf_board3` | `prov:800` claims plain `M` while `shelf_board2:781` and `shelf_board4:819` declare the **same 400 mm depth** as `A-swept`. All three sit at y −400..0. Identical assumption, tagged in two masses, untagged in the third |
| **D14** | `part_stile_M` | `prov:352` = `M`; its own `seen:353` = *"NOT as one member … Total span 144.5 mm. Spec's single 72"*. `audit:354` says FIX, but the M tag and the refuted number both survive. Milder for `part_jamb_L` (built 64 vs measured 47.2+47.0, `:319`) and `part_jamb_R` (built 64 vs measured 42.2, `:336`) |
| **D15** | `nightstand` | `prov:567` tags M for an arris of **426 mm** under a mass built **700 mm** long, and the cited *"depth 350"* is the plane the arris was backprojected on — it cannot also be that backprojection's result. No A tag, no `why`, no gap |
| **D16** | `bench` | `prov:584` = *"M(top mid backprojection at z=420)"* — an M tag covering **1 of the 7 numbers** on the mass. The 1050×600 plan and the position carry no provenance at all |
| **D17** | `gauges.open_tension:20` | still records the open slot as *"y −1.15..−2.55"* though r27 moved the far side of that slot to −2.2908; the other end of the same slot is `door_wall_far`'s typed −1200. **A stale gauge feeding a scored row** (`gate-15-r27.md` charges `door_wall_far` 0.48 → 0.43 to r27) |

### Under-claims (the honest direction, listed for completeness)

`chair_seat.prov:725` tags `A(seat 450 vanity norm)` for a height its own
`seen:728` **measured** at 450.5; `console.prov:441` tags `A-swept(end y −5160)`
for a near end its `seen:444` bounds at ≈−5140 from a backprojected arc. Both
are safe errors, but they mean the M/A tags cannot be counted mechanically —
which is precisely why this partition had to read the prose.

---

## What this changes

1. **The charter's termination argument needs one sentence added**
   (`qa/reproduction-curriculum.md:12-15`): the target image makes the
   *projection* falsifiable, not the *metric*. Rounds spent on P1-P20 are
   rounds spent on quantities the input cannot decide, and blind critics will
   go on naming them forever — `bolster` five times — because from the frame
   they are genuinely unknowable, and the critics are RIGHT.
2. **The left wall gets the same treatment the right wall just got** (D1/D2),
   before another round prices cabinetry against it.
3. **Four r27 staleness repairs are cheap and mechanical**: D4, D5, D6, D7.
4. **SHAPE membership moves into the spec** (§c), where our own render cannot
   reach it.
5. **`declared_gaps` becomes a live register**, not a graveyard — and
   `rule_gate.py:119` should stop accepting a `why` as a substitute for one.