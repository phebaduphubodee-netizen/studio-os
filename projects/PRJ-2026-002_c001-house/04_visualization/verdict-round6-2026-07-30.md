# Verdict round-6 — 2026-07-30 — the first R7 critic-ladder round

Inputs, in order of arrival:
- **C3 (cross-vendor)**: the owner ran the g10 pair through Gemini with a
  designer-critique prompt — the event that triggered R7's adoption.
- **C2 (cold critic)**: fresh-context agent, R7's first official run — saw ONLY
  the g10 pair + the two reference anchors + `templates/cold-critic-prompt.md`.
  Returned 15 grounded defects; its "one fix" pick = lighting.
- Standing evidence: the first look_bench sheet (loses on light story) and the
  owner's five verdict rounds.

**Consensus, four independent judges**: the #1 sellability gap is the LIGHT
STORY. (bench sheet → owner → Gemini → cold critic — unanimous.)

## Triage (R7 discipline: accept→lane, or refute WITH measurement/reference)

### LANE A — LIGHT STORY (the pass this round opens with)
| item | source | note |
|---|---|---|
| flat wash, no visible light sources, no story | C2#1, Gemini, bench | the ONE fix all judges chose |
| no contact shadows / AO — everything floats | C2#1, Gemini | bed, bench, tables, slat grooves |
| lamp glows uniformly, no bulb hotspot, no pool/falloff | C2#8, Gemini | round-3 emission gradient measured 221±1 — insufficient |
| shadow smears on wardrobe carcass read as stains | C2#13 | render artifact class — sampling/light, not geometry |
| AgX/Filmic view transform, DoF, subtle glare/grain | Gemini | post chain — end of lane A |

### LANE B — MATERIAL HIERARCHY
| item | source | note |
|---|---|---|
| one matte greige everywhere; fabric/wood/metal indistinguishable | C2#6, Gemini | roughness hierarchy + sheen on textiles + normal maps |
| mustard carcass single-value all faces | C2#6 | material variance per face role |
| rug: no pile, paper-thin, no deformation under bed | C2#12 | thickness + edge binding + displacement-ish pile |

### LANE C — GEOMETRY SMALL FIXES (one batch, quick-laddered)
| item | source | note |
|---|---|---|
| hangers read MISSING (hook only, body invisible) | C2#3 | wire 3.5mm vanishes at render distance; reference shows full black hangers |
| bedside lamps too small vs bed/headboard | Gemini | scale up per reference sconce/lamp mass |
| nightstands = sealed boxes (no drawer line, pull, legs) | C2#7, Gemini#4 | + drawer pulls on wardrobe whites (Gemini) |
| headboard pads float on slat wall, no frame/connection | C2#5 | frame or full-panel per reference 2 |
| duvet corners mirror-symmetric L/R | C2#4 | per-corner salt asymmetry in the sim feedstock |
| pillow seams/case corners invisible | C2#5 | seam 0.008 too subtle + material flat |
| folded stacks on shelves = perfect boxes | C2#9, Gemini | soften: sag, edge rounding, per-stack jitter |
| mattress edge too crisp/boxy | Gemini | round + slight bulge |
| ottoman too deep, kisses bed base | C2#11 | ~1/3 bed length + walking gap per reference |
| no cabinetmaker detail: plinth/shadow gaps/door edges | C2#14 | joinery pass on the wardrobe system |
| sheer curtain = perfectly even corrugation | C2#10 | already partly addressed in e8 law — amplitude variance up |

### LANE D — STYLING LIFE (bounded by ฿0/CC0 + no-defect-object law)
| item | source | note |
|---|---|---|
| zero signs of life: no art/books/tray/plant; frame-1 wall bare | C2#9, Gemini | procedural simple objects only; keep restraint of reference |

### REFUTED / OPINION (with the evidence, per R7)
- **"ottoman too deep, kisses bed base" (C2#11)** — REFUTED by ink at lane-C
  recon: the bench footprint 498×1000 and its ~51mm gap to the bed foot are the
  designer's own drawn lines (spec note: "INK x2654.5-3152.8 y625.8-1625.6 …
  matched to ink", element-3 ink-true, owner-confirmed 2026-07-18). Drawing-tier
  law: findings inside the ink are not findings. No change.
- **"headboard pads float, need frame/full-panel" (C2#5, was accepted to lane C)**
  — RE-ROUTED to the gate at recon: the fix collides with TWO signed decisions —
  "the headboard IS the wall" (BF14, element 1/3) and the bed head sitting FLUSH
  on BF14's face (x5204 vs x5203; there is no air for a panel behind the shams).
  A mounted upholstered panel would cover the signed slat wall. Not smuggled;
  owner decides beside the cove/sconce question (both are the reference
  vocabulary asking to amend a signed element).
- **"garments should hang side-on for a 600mm closet" (Gemini)** — REFUTED by
  measurement: spec depth = 600 (`builtins BF09-3 d:600`) and the generator
  already places shoulders ACROSS the depth axis (styling orientation law,
  `test_garment_thickness_runs_along_the_rail_not_its_shoulder`) — i.e. real
  side-hang. The face-on READ comes from the camera axis vs the bay opening;
  the reference's own display rail reads face-on identically.
- **"rail too high in first bay" (C2#15)** — critic self-marked opinion; rail
  heights are signed joinery (element 7). No action.
- **"garments are black rags" (C2#2)** — the construction cues exist (collar,
  sleeves, cuffs) but die under flat light + monotone material; routed to
  lanes A+B rather than another geometry round. If they still fail the critic
  AFTER A+B, geometry reopens ((ก3) open-form is next in that lane by the
  owner's own sequencing).

## Order of work (approved "ลุย" 2026-07-30)

A (light story) → C (small geometry batch) → B (materials) → D (styling life),
re-critic (C2) after each lane, C3 + owner gate after A+C and again at the end.
Every lane under R1 budget (2 full cycles) + R5 quick ladder.

---

# Lane A closed — light story (2026-07-30, pair ls3)

**Mechanism found by recon**: the flat wash was the lumen-method ambient grid
doing its CD job — 18 cans at even 114-283 lx by design. A hero frame is made
at the DIMMERS, not the fixture list.

**Shipped (all behind `--light-story`; the signed CD state is untouched and
byte-identical when off — armour-pinned):**
- Photoshoot dimmer state over the SAME signed e5 plan: ambient 0.48 with a
  PER-ZONE exception (dressing zone 0.70 — task+display), spots 1.50 →
  focal ratio 3.1:1, past the vault's 3:1 floor (lumen-method:48, Kelly
  Focal Glow); lamps 1.5; AgX + exposure trim.
- VISIBLE LUMINAIRES: every plan position (18 cans + 6 spots) now carries a
  recessed trim — dark ring + warm emissive lens — geometry at the exact
  signed positions (C2 re-critic: "แสงไม่มีที่มา").
- Convergence discipline: quick ladder ×5 across three sub-mechanisms
  (uniform dim → too dark; per-zone; brightness lift after the C2 verdict
  "ยังจมมืดหม่น"); full pairs ls1 (caught the wardrobe sink the bed_hero
  quick could not see) → ls2 (C2 re-critic input) → ls3 (closing pair).

**The lane's honest ceiling — a DECISION, not a defect**: both deliverable
cameras barely see the ceiling, so recessed trims cannot be the frame's
visible origin. The reference's language is a visible COVE (behind headboard/
slat wall) + paired SCONCES — fixtures element 5's signed DD does not contain.
Adding them = amending a signed element → owner's call at the gate:
(a) amend e5 (cove + sconces; the reference's exact vocabulary), or
(b) accept off-frame origins and proceed to lane C.

C2 items #1/#8 partially closed (pools, falloff, practicals, brightness);
#13 smear watch-item improved with brightness, re-check after lane B
materials. Full pair of record: `room_bedroom_suite_eye_ls3.png` +
`room_bedroom_suite_eye_ls3_bedhero.png`; 2127 green.

---

# Lane C closed — geometry small batch (2026-07-30, pair lc1)

**Shipped (all pure-layer first, 2132 green):**
- HANGERS (C2#3): wire 3.5→5mm; ONE bare hanger parked per breathing rail
  (pitch ≥180mm — the full silhouette that says "wardrobe" when every worn
  hanger is covered by its garment by construction; the 132mm-floor bay rails
  refuse it, tested). 6 empties emitted in the suite build, verified in-blend.
- LAMPS (Gemini "เล็กจิ๋ว"): shade 270→340mm dia, stack taller; millwork now
  PUBLISHES the lamp dims and build_room's emission-gradient window derives
  from them (the hand-copied 0.035/0.17/0.15 was hardcode-drift waiting for
  exactly this rescale); e5's bulb z already derived → moved automatically.
- NIGHTSTANDS (C2#7): sealed box → toe-shadow (near-black, inset 22mm) +
  carcass + drawer face with a 6mm wrapped reveal; symmetric, rot-honesty and
  footprint invariants kept (tests amended WITH the design change).
- PILLOWS (C2#5): sleeping-pillow seam 8→12mm, lumbar 6→9mm.
- FOLDED STACKS (C2#9): per-item thickness ±12% (cumulative height exact —
  headroom contract pinned), bevel 8→14mm, alternating 4/3-high piles.
- MATTRESS (Gemini): edge bevel 50→75mm seg 5 — the visible sliver is all edge.
- DUVET (C2#4): feedstock enters per-corner asymmetric (folded_sheet salt);
  the baked corners stopped mirroring (LOOK-confirmed on the full pair).
- SHEERS (C2#10): per-wave amplitude 72–100% (strictly ≤ the published bound —
  clearance math untouched), per-window fold DNA.
- WHITE DRAWERS (C2#14): stack reveal 6→10mm — reads at deliverable distance.

**Spend:** quick ×3 (eye ×2 — one self-inflicted overwrite re-run — + bedhero),
full ×1 pair = the R1 budget's 2 full builds. Sim share unchanged (3/12, same
stable DNAs). Pair of record: `room_bedroom_suite_eye_lc1.png` +
`room_bedroom_suite_eye_lc1_bedhero.png`.

## C2 re-critic on lc1 (fresh agent, R7) — 11 items, triaged
1. **Hanging garments read as rags/ribbons (worst)** — ✓ known: the analytic
   twins are what fails (sim-passed pieces read right); already routed —
   lane B material weave first, then the owner's own queued (ก3) open-form
   feedstock. The critic confirming it post-C is the recorded trigger arming.
2. **Bedding: white corner wads read as crumpled paper; near-mirror folds** —
   ✓ partial: the DUVET corners stopped mirroring (this lane), but the
   COVERLET's feedstock is still symmetric and its corner gathers pile both
   sides alike → residual accepted, fold into the lane-B build cycle.
3. **Pillows: seams still invisible; "only 3 pillows"** — seam ridge now 12mm
   but SAME-COLOUR under soft light = value problem → lane B (normal/sheen
   contrast). Count ✗ refuted by spec: the head ladder is FIVE pieces (2 sham
   + 2 sleeping + 1 lumbar, element 8 signed); the front pair merges into the
   shams from the head-on camera — a value-separation issue (lane B), not a
   missing-object one.
4. **Light: still flat-amber, no visible origins, weak contact shadows, shade
   glow uniform** — ✓ the standing lane-A ceiling = the COVE/SCONCE gate
   question (unchanged); shade gradient exists but reads uniform → widen the
   mouth-to-top ratio in the lane-B cycle; contact shadows partly a material
   issue (monotone greige hides AO) → lane B.
5. **Monotone material world** — ✓ LANE B verbatim (the queued next lane).
6. **Missing architecture finish: no skirting, no bulkhead over wardrobe, no
   door/switches in frame** — ✓ NEW CLASS (nobody had named it). Routed:
   check the INK first (drawing-tier law — if the CD set draws skirting, build
   it; if not, it is an owner design question at the next gate). Queued as
   lane C2 (architecture finish batch).
7. **Zero styling life** — ✓ LANE D (queued, ฿0/CC0 law).
8. **Sheer still too even + no track** — ✓ partial: variance shipped but reads
   subtle at deliverable distance → widen range + add the track piece in the
   lane-B cycle.
9. **Split headboard floats on the wall** — ✓ known: THE second gate question
   (frame/panel collides with signed BF14 "the headboard IS the wall").
10. **Bench: no seams/piping, kisses bed, no shadow** — footprint/gap ✗
    REFUTED by ink (498×1000, 51mm gap — the designer's drawn lines; the
    "kiss" is head-on projection overlap). Seam/piping detail ✓ accepted →
    small-geometry residual with the lane-B cycle.
11. **bed_hero one-point camera** — critic self-marked opinion; the camera is
    CAD-derived deliverable spec. No action.

**Verdict shape:** lane C's mechanisms all landed and read (hangers, lamps,
joinery, stacks, asymmetry). What still fails is exactly what lanes B/D and
the two gated signed-element questions own. R1 spent → this is the scheduled
A+C gate.
