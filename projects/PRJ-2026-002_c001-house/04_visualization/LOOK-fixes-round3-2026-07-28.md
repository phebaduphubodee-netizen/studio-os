# LOOK round-3 fixes — 2026-07-28 (object identity)

Owner, after round 2 shipped: "แก้เท่าไรก็ไม่หายห่วย … องค์ประกอบในภาพยังเพี้ยนอยู่เลย" with
four named examples. This round is a DIFFERENT defect class from round 2: round 2
killed surface artifacts (terracing, sawtooth, mitre steps); round 3 is about objects
that do not read AS THEMSELVES — a garment that isn't a garment, a duvet that is an
island lump, pillows that are stacked blobs, a lamp that is a glowing box.

Final frames: `pipeline/output/room_bedroom_suite_eye_g7.png` +
`room_bedroom_suite_eye_g7_bedhero.png` (the round-4 baseline pair). Suite: 2100 green.

## 1. เตียง "ก้อนอะไรซักอย่างอยู่บนผ้าปู" — the duvet was the last box

`bed__duvet` was a 90 mm bevelled slab inset 110 mm from every edge (an island ON the
bedding) with a second box playing its turned-back fold. Now the THIRD simulated cloth
on the bed: `softgoods.folded_sheet` pre-bends the head band 180° over the main panel
(one connected lattice) and the solver settles the crease into a real hotel-fold roll;
the sheet spans the mattress and falls past its flanks. `bed__duvet_fold` the object
is gone — the fold is cloth of `bed__duvet` itself (value_ladder.BUILT_OBJECTS and the
armour test moved with it; the ladder's rungs are unchanged).

**The cloth-stack contact law (cost three failed bakes to learn, fx6→fx8):** a frozen
cloth collider is a SOLIDIFIED mesh — two shells. A later sheet tunnels between them
and gets trapped, rendering as mottled cloth-through-cloth whatever the distance
(graze at 0.004, shard-crumple at 0.012 — the repulsion impulse at birth outgrew the
cloth forces, and the bbox guards cannot see a contained crumple — still patched at
0.008). The fix is mechanism, not tuning: every `sim_surface=True` bake leaves a
hidden SINGLE-SHELL proxy (`drape.sim_surface_of`), later sheets collide with THAT,
collide_dist only has to clear the render shells, sheets are born above the collision
field, and the proxies are deleted after the last bake in the stack
(`drape.drop_sim_surfaces`). Throw hem re-solves clear at 0.282; no patches, no
shards (fx9 LOOK).

## 2. หมอน "เป็นก้อนอะไรไม่รู้ซ้อน ๆ กัน" — no sewn identity, no contact

`softgoods.cushion` grew `seam` + `ear`: a piped seam ridge around the equator with
corner ears — the sewn-case cue that separates a pillow from a blob — spent from a
pre-shrunk radius so the footprint invariant holds. Sleeping pillows + lumbar wear it;
the standing shams deliberately do NOT (their piped edge runs around the FACE — a
half-height horizontal ring would lie). The sleeping pair now LEANS back against the
shams (`styling._lean_to_head`, one shared angle — the no-dent armour pins the pair
to equal heights — plus a head-ward ease that closes most of the rank's air gap):
stacked soft pieces finally touch. LOOK fx6/fx9: the rank reads as pillows against
shams, front row no longer one tube.

## 3. โคมไฟ "เป็นเหลี่ยม ดูไม่มีจริง" — boxes wearing a dome's docstring

The pure part list (envelopes + containment proof in millwork) is untouched; the
materializer now turns each part on the lathe: tapering brass base, round stem, drum
shade via `_cyl_frustum` — mouth open downward so the point light still pools onto
the cabinet. The other half of the unreal read was emission: measured 221±1
edge-to-edge, no hotspot (round-2 verdict #11). The shade's Emission Strength is now
driven by shade-height (MapRange+Math over object-Z): 1.5 at the mouth falling to
0.4 at the top — a bulb lives somewhere. LOOK fx7: reads as a lit table lamp.

## 4. ผ้าในตู้ "ไม่สมจริง" — one species, cloned

Two changes on top of round 2's pose DNA:
- `garment(collar=...)`: most shirts grow a neck collar (raised band at the neck
  zone, capped under SHOULDER_DROP so it never pokes above the rail) — the cue that
  reads "shirt" over "felt blank".
- NEW `softgoods.trouser_fold`: trousers folded over the hanger bar — narrow,
  near-straight, HALF the drop (vault row: 500 mm) with a cylindrical roll at the
  bar. ~30% of rail slots become trousers (`styling.garments_on_rail`), their
  roll-top wrapping the bar (placement 0.6×SHOULDER_DROP). LOOK fx7: the rails read
  as a real mixed closet — long/short rhythm, air gaps, species variety.

## Instruments' role this round

The render caught THREE defects the guards could not: fx6's mottled patches, fx7's
shard crumple (bbox-clean, motion-clean — a contained explosion passes every
numeric guard), and fx8's still-patched contact. Each drove a mechanism change, not
a tune. This is the LOOK law working exactly as written.

## Residuals (disclosed)

- The throw's big surface remains near-featureless under this flat light — with the
  duvet real, the read is now "bedspread over bedding" rather than "ก้อน", but the
  surface's dead-band is the MATERIAL/LIGHT lane (knit weave invisible at 256
  samples under soft fill; same family as towerback/charcoal garments/lamp-pool).
  Next per the standing plan: the light-story pass, then the Gemini leg (owner's
  billing gate).
- Trouser hangers show bare angled arms beside the narrow fold — true of real
  trouser hangers, noted in case the owner reads it as a defect.
- Verdict-round-2 #7-#9 (dead-black holes, folded-stack edges, soffit ripple)
  remain untouched and unordered.

## Test/armour deltas

- `softgoods.folded_sheet` + 5 feedstock tests; `cushion(seam, ear)`;
  `trouser_fold`; `garment(collar)`.
- `drape.sim_surface_of` / `drop_sim_surfaces` + the contact law recorded at the
  duvet bake site.
- `test_value_ladder`: the duvet-fold armour re-pinned to the sim mechanism
  (folded_sheet + duvt_m + no fold box); BUILT_OBJECTS drops the dead name.
- `test_styling`: no-dent pin amended (3 mm, lean-aware) with the reason recorded.
- Full suite: 2100 green.
