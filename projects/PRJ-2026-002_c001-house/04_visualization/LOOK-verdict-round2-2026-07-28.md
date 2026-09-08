# LOOK verdict, round 2 — 2026-07-28

Owner: "ดูด้วยตัวเองแล้วตัดสินเองอีกรอบว่าอะไรยังเพี้ยน" + standing rule (same day):
LOOK-and-judge is now a MANDATORY per-step discipline in this project, not per-element.

Frames judged: `pipeline/output/room_bedroom_suite_eye_g5.png` (hero 3/4) and
`room_bedroom_suite_eye_g5_bedhero.png` (frontal). Method: my own read of both frames →
zoom crops → id-mask ownership (all-scene masks rendered for this pass, scratchpad
`judge2/idmask_g5_nonmill|_bf`) → 4-lens independent panel (54 candidates, wf_bd905337) →
every load-bearing claim verified or refuted in pixels. JUDGMENT ONLY — nothing fixed yet.

## Confirmed build defects (ranked, mechanism named)

1. **Flat-shaded bevel terracing on the whole `_rbox` fleet.** Bench seat is stair-step
   banded across its entire top/front in BOTH frames (light-lens pixel profile: plateaus
   142→84 in 3–7-code steps every ~18 px); same terracing on the mattress/topper rolls at
   the bed corners and the bed base edge. Mechanism read in code: `build_room._rbox`
   (build_room.py:2077) bevels (seg 3–5) but never sets `use_smooth`, unlike curtains
   (1279), sheers (1330), `_smooth_mesh_obj` (2526), drape.py (204). Affected here:
   `bed__base`, `bed__mattress`, `bench__seat`, nightstands (+ sofa/deco in other rooms).
2. **The throw's drop face is a fold-less slab with a near-level hem.** The largest cloth
   face in both frames (~1.4 m wide in bedhero) carries zero vertical folds and its free
   hem runs essentially level — the literal e8 softgoods law ("crease grows from the
   suspension line, hem never level") is not applied to the throw's cantilever fall.
   This is the biggest remaining carrier of the "แข็ง" read on the bed.
3. **Bed-skirt left corner breaks in a squared 90° Z-step** (bedhero ~[175–310, 960–1060],
   verified at 2× zoom): drop → horizontal shelf → drop, knife-clean, against the dark oak
   floor. Cloth cannot do this; mitre-corner mesh artifact. Right corner has a milder
   stiff-flap cousin in g5.
4. **East sheer hem is a row of detached triangular spikes, one per pleat** (verified at
   2× zoom): vertical-blind read, the same sawtooth class e8 killed elsewhere —
   curtains.py's sheer (built 07-17, pre-softgoods-law) still holds this shape. Pleat
   pitch also metronomically constant to the hem.
5. **Garment rack reads as cloned boards, not clothes**: every garment shares one S-bend
   at the same height, shoulder line dead-level off a single point hook, hems flick
   forward in unison, card-thin edges; several charcoal pieces collapse to detail-free
   black cores (12 % of sampled area ≤ 8 luma). dev() varies WIDTHS only — bend
   phase/amplitude and shoulder profile are uniform.
6. **Sleeping pillows are zero-deformation capsules**: level continuous silhouette, no
   contact compression between pieces (the known deferred no-collision class); in g5 the
   front row merges into one bed-width tube read.
7. **Dead-black holes**: hard-edged 0-luma rectangle under the floating drawer bank next
   to the left nightstand (18.6 % of px ≤ 8, min 0); right-edge nightstand in g5 renders
   as a near-unlit mass (mean 63) against the brightest bedding. Reads as missing
   geometry, not shadow.
8. **Folded stacks are laminated boards**: razor 90° edges, flush layers, no fold bulge —
   the painted-slab class surviving on shelf props.
9. Minor: soffit undersides show non-monotonic ripple bands (denoise/low-sample tier);
   sham silhouettes show faint chord kinks (nu=13 cushion mesh).

## Signed design that renders illegibly (owner's call, not re-decided)

10. **The "mystery grey slab" in the wardrobe is BF09-3's microcement towerback** —
    id-mask-proven (`…BF09-3__towerback` + `gable2`), routing owner-signed
    (D3-A/D4-A/D6-A: '*front*'/'towerback' → microcement). Measured: towerback luma
    100.5 flat with no texture read at this distance; oak gable2 beside it luma 85
    (warm, r−b 53) — near-equal values fuse them into one unreadable panel that two
    lenses flagged as "placeholder geometry". Class = amplitude-bisect: real material
    rendering as nothing. Remedy would be texture gain/lighting, not a re-decision.
11. **Lamp shades read as fake glowing boxes**: measured 221±1 edge-to-edge (NOT
    clipped — max 234), no bulb hotspot, no rim falloff, near-neutral white while their
    wall pools are amber; in g5 the nightstand is hidden so the shade floats. Panel's
    "corner sliced off both shades" claim REFUTED at 4× zoom — that is the shade's lit
    BOTTOM FACE, but at frame scale it feeds the fake-box read.

## Camera / plan reads (not build defects)

12. Bedhero framing: the bench is cropped legless into a floating second mattress and the
    low camera stacks coverlet/bed-face/bench into grey bands filling ~60 % of frame.
13. The "ghost behind the sheer" (3 lenses) is almost certainly the DEPICTED Juliet rail
    + garden through glass — real ambiguity, correct geometry.
14. Drawer bank facing the bed with no aisle, and the anteroom/bedroom running as one
    plane, are ink-derived plan facts the camera compresses further.

## Refuted this round

- Lamp corner notch (= lit bottom face, mirrored on both lamps by construction).
- "Duvet fold edge dead straight" — my own earlier claim; at full res the crest waves.
- "Hard rectangular blocks inside the sheer" (= Juliet rail seen through glass).
