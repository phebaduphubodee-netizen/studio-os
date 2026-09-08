# TRN-002 — measurement pass, 2026-08-08: the four objects nobody had measured

Ordered under the owner's build law (dimension → objects complete → light): before any light
work, every manifest entry must be BUILT or DECLARED, and three of the seven UNCOVERED entries
had no measurement of any kind. Four objects were measured through the solved camera, each by an
independent pass, each then **verified by reprojection** with `G.project` against pixels the
verifier re-fitted from the JPEG itself.

Method is the lane's own: sub-pixel edge fits over many columns, backprojected with
`trn002_geom.backproject` on a NAMED plane, camera unchanged since r1
(`-4491, -7992, 1305`, yaw 20.0417°, f 38.841 mm).

---

## สรุปสำหรับเจ้าของ — สองในสี่ "ชิ้นที่ต้องสร้าง" ไม่ควรถูกสร้าง

| entry | ผล | ทำอะไรต่อ |
|---|---|---|
| `mirror` | **ไม่มีอยู่ในภาพเป้า** พิสูจน์ด้วยการสะท้อนรังสี ไม่ใช่การมองไม่เห็น | ลบ/แก้ entry — **ต้องลายเซ็นคุณ** |
| `wall_floor_junction` | รอยต่อผนัง–พื้นห้องนอน **วัดไม่ได้ทั้งสามผนัง** (ถูกบัง 100%) สิ่งที่วัดได้คือ **plinth ของตู้โอ๊ค สูง 106.2 mm** ซึ่งเป็นคนละของ | แก้ขอบเขต entry — **ต้องลายเซ็นคุณ** |
| `closet_shelf` | **วัดได้: z = 822.9 mm** | สร้างได้เลย |
| `far_room` | วัดกรอบช่องเปิดได้ครบ · ด้านในหลังม่านบาง **วัดไม่ได้** | สร้างส่วนที่วัดได้ |

**และพบของแถมที่แรงกว่าทั้งสี่ข้อ:** `closet_oak` ของเราประกาศหน้าตู้ไว้ที่ `y = 2330` — **ผิด**
หน้าจริงอยู่ที่ **y ≈ 1130** (วัดจากเส้นสัมผัสพื้นของตู้ 65 คอลัมน์) และความสูงที่เราประกาศไว้
`2008 mm` ก็ผิด — ตู้วิ่งขึ้นไปถึงอย่างน้อย **z ≈ 2524**

---

## 1. `mirror` — NOT PRESENT. Not occluded, not ambiguous: absent.

**The test was a measurement, not a look.** Reflect the camera ray about the partition plane
`y = 0` for 24 bay pixels (u 185/210/235/260 × v 270/330/400/470/540/580) and intersect the
bedroom shell — i.e. compute what a plane mirror in that bay would be *obliged* to show:

- at **v 540–580** it must show the bedroom's own floor. The bay shows long straight parallel
  planks; the bedroom's herringbone chevrons sit 15 px lower **in the same crop**, side by side
  and plainly different. (The verifier sharpened this: a mirror would show the **white rug** over
  u 181–498, v 516–568 and the bed platform over u 214–469, v 509–562. The bay shows neither.)
- at **v 270** it must show the flat bedroom ceiling. The bay instead shows a receding soffit
  arris running (215,251)→(243,278) into a vertical wall corner held at u 241 from v 250 to 590.
- the bay shows a **sheer-curtained window with a transom**. The bedroom's only window is the
  venetian blind on the left wall; its mirror image projects to u 78–84 — outside the bay
  (u 178–271) entirely.

The verifier reproduced the reflection independently and confirmed the verdict three further ways.

### Why the entry existed at all — and this is the finding worth keeping

`coverage-manifest.json`'s `mirror` entry cites **C3#11 at r23** as its whole provenance. By R7b
law Gemini was sent **our own render and nothing else**. At r23 the partition's left bay was
filled by `closet_back` — a blank panel we assumed — which rendered as a blown-white surface. The
critic correctly described *our frame* and called it "the mirror". That description was then
written into the manifest as an object **the reference shows**, and it is not.

> A blind critic answers *"is this believable"*. It cannot answer *"does this match the
> reference"* — R10b, in the lane's own words. This is the first time that gap has been caught
> putting a phantom object into the build list.

### What actually occupies those pixels (measured, since the pass was there)

| | value | basis |
|---|---|---|
| glazed pane, clear width | **597.8 mm** on y=0 | u 178.386 → 271.220 |
| glazed pane, clear height | **2319.1 mm** | head 2371.1 − sill 52.0 |
| head underside z | **2371.1 ± 0.4** | 89-column fit, rms 0.037 px (spec's own `part_head` says 2372) |
| **leaf stile width** — a member **no spec in 33 rounds has carried** | **47.9 mm** | 149 rows, sd 0.072 / 0.097 px |

**CORRECTED BY THE VERIFIER — carry the corrected numbers, not the pass's:** the pass wrote that
the pane *narrows* with setback (594.8 at y+60). It widens: the same two pixels backproject to
**602.3 mm at y=+60** and **612.7 mm at y=+200**. A plane further from the camera subtends more.
The pass got the sign right for the stile in the same report and wrong here.

Also correct the pass's over-caution: the bottom rail IS measurable at ~50 mm (verifier's refit
rms 0.682 px, not the 1.44 px the pass rejected its own fit on).

---

## 2. `wall_floor_junction` — the bedroom's is UNMEASURABLE; what was measured is a different object

**The critic's two pixel bands are r27's pixels, not the reference's.** In the target,
(140–200, 590–625) is a wood pier face, the partition's bottom rail and two chair legs;
(415–430, 600–620) is entirely bed. **Neither band contains a wall meeting a floor.**

**All three bedroom walls are fully occluded at their base:** left `x=-4750` → u 17..72 (behind
the travertine console), back `y=0` → u 72..731, right `x=0` → u 731..1128. There is no column
anywhere in this frame where a bedroom wall meets the floor in view.

**This answers the precondition its own triage set** (`triage-debt-2026-08-07.md:40`, C2#15:
*"เงื่อนไขก่อนสร้าง: วัดว่าภาพเป้ามีบัว มีร่อง หรือไม่มีอะไรเลย"*). The answer is a fourth option
nobody listed: **you cannot see it.** And that changes the cure — a base that reads wrong in our
frame is then a **contact-shadow** problem (light), not a missing-skirting problem (geometry).

### What IS measured, and it is a different object

The **closet-oak cabinet's base band**: height **106.2 ± 1.0 mm** (top edge fitted over 60 columns
u 296–355, rms 0.133 px; bottom over 50 columns, rms 0.193 px), on the contact plane y = +1128.3.
Tone rules out a *proud* board; it cannot separate a recessed plinth from a flush board with a
shadow-gap groove above it.

- **Recess DEPTH: UNMEASURABLE.** 0.16 px per 10 mm, so the whole 0–100 mm range spans 0–1.6 px
  inside a dark line whose FWHM the verifier measures at **1.6–2.6 px** (wider than the pass's
  own 0.77–1.93). The verifier's remeasurement makes the unmeasurable verdict *stronger*.
- **CATEGORY SLIDE, flagged by the verifier and accepted:** the pass titled this "the only
  wall-to-floor detail in the frame". It is **joinery on a cabinet**. It licenses a shadow-gap
  plinth on `closet_oak` and **nothing about any wall**.
- Error bars on the partition rail were understated 4× (±0.2 mm = 0.026 px is tighter than the
  best fit in the pass). Honest: contact −5.0 ± 9.9 mm, top 56.8 ± 13.5 mm — means agree, the
  conclusion holds.

---

## 3. `closet_shelf` — MEASURED

**Shelf top surface z = 822.9 mm** on plane y = 1130. E2 (top front arris) fitted over **70
columns** u 295–364, rms 0.095 px, with three *disjoint* column groups agreeing to 1.9 mm
(824.0 / 822.7 / 822.1). Verifier reproduced every fitted line bit-for-bit and confirms the
headline.

**The bigger find is the plane, not the shelf.** `closet_oak` declares its front face at
`y = 2330`. On that plane a floor line (z=0) projects to v = 554.97 at u = 326 — and the image at
v 555 is **unbroken cabinet-door wood** with no boundary of any kind. The measured
wardrobe/floor contact is at v 574.33 → **y = 1132.3** (sd 14.4 over 65 columns). Independently
re-derived by the verifier. **`closet_oak`'s declared depth is wrong by ~1200 mm.**

Bounds and honest gaps:
- board thickness **≤ 31.2 mm** — an upper bound only (E3 is a 4-px luminance ramp, a cast shadow,
  not an arris)
- **REFUTED by the verifier:** the pass's "niche depth 462 mm". The niche's right internal return
  is visible and gives a probe ~4× more sensitive; the pass never ran it and then listed that
  return as *unseen* — "listing as unseen the one feature that contradicts the derived number".
- how far LEFT the shelf runs: every horizontal edge terminates at u 292.8, which is the
  partition mullion's edge, not the wardrobe's. UNMEASURABLE.
- E1/E2 image slopes sit 6–7.6 σ outside the physically possible family for two level lines at
  that z, so these fits carry systematics several times their quoted rms. The 822.9 headline
  survives; do not quote it tighter than ± a few mm.

---

## 4. `far_room` — the partition has TWO bays showing TWO different things

One mass (`closet_back`) has been standing for both. It cannot: the bays do not show the same
kind of thing.

| | measured | basis |
|---|---|---|
| partition head top z | **2479.3 ± 0.4** | 16 blocks, u 166–386, rms 0.073 px |
| leaf soffit z | **2370.5 ± 1.5** | on y = 0 |
| LEFT bay clear width | **695.6** (x −4198.0 … −3502.4) | glazed sliding leaf |
| RIGHT bay clear width | **685.6** (x −3364.0 … −2678.4) | the walk-through; floor runs through |
| opening overall | **1684.2** | x −4292.1 … |

Verifier: **mean reprojection error 0.22 px, max 0.69 px over 34 independent checks. No derived
value fails; no plane is wrong.** (`agrees=false` is set on identification defects, not geometry.)

- **LEFT bay interior: UNMEASURABLE.** A daylit sheer curtain with vertical folds — nothing behind
  it can be fitted. Do not build a window, a table or a curtain to it.
- **`wardrobe_width 556.8` is not a measurement of the wardrobe.** Its left datum is the frame
  **mullion's occluding contour** — the same profile at every height from v 310 to 550. Discard.
- **The wardrobe's depth IS measurable** (the pass wrongly listed it unmeasurable): the niche's
  right internal return reads as a dark band the full niche height (at v 400: `355:0.230
  356:0.142 357:0.041 … 362:0.046 363:0.118` — lit back panel → dark return → lit front stile).
- **`closet_oak`'s declared height 2008 mm is refuted.** The soffit read on the *wardrobe's own*
  plane (y ≈ 1153) is **z = 2524**, constant at u 300/330/360 — not the 2370 read on y=0. The unit
  runs to at least 2524.
- the chair behind the glass is **in front of** the partition, not behind it: its black legs cross
  the bottom rail and stand on bedroom herringbone; `chair_leg_1/2/3` reproject to (163.5,632.0) /
  (204.5,611.0) / (245.7,621.0) against a darkest-blob tip at (163.5,632). Our shell is **too
  wide** — a chroma silhouette stops at u 256.0 at v 495 where our geometry does not.

---

## What this changes

**Buildable now, with numbers:** `closet_shelf` (z 822.9) · the `far_room` opening frame ·
a shadow-gap plinth on `closet_oak` (106.2 mm) · and — unchanged by this pass — `led_strip`.

**Two manifest entries are wrong and need the owner (they are claims about the TARGET, and the
entries ratchet now refuses a silent edit):**
1. `mirror` — remove, or rewrite as "the glazed leaf of the partition's left bay". It is not a
   mirror and never was; the entry inherited a critic's reading of our own r23 render.
2. `wall_floor_junction` — re-scope to the closet-oak plinth, or declare it a gap. The bedroom's
   junction cannot be reproduced from a frame that never shows it.

**Three corrections to masses that already exist**, none of them asked for and all of them larger
than the objects this pass was sent to measure: `closet_oak` front face y 2330 → ≈1130,
`closet_oak` height 2008 → ≥2524, and the shell too wide at the partition.

**Provenance for the spec** (paste as `prov`):

```
closet_shelf   M(top front arris fitted over 70 columns u295-364, v469.46..468.50, rms 0.095 px,
               three disjoint column groups agreeing to 1.9 mm; backprojected on the wardrobe's
               own front plane y=1130, itself measured from the floor contact at v574.33 over 65
               columns -> z 822.9)
closet_plinth  M(base band top edge over 60 columns u296-355 rms 0.133 px, bottom over 50 columns
               rms 0.193 px, on the contact plane y=+1128.3 -> height 106.2 +/- 1.0) /
               A(recessed vs flush-with-groove: UNDECIDABLE, tone rules out proud only)
part_head      M(underside fitted over 89 columns u181-269, rms 0.037 px, on y=0 -> z 2371.1,
               spread 0.4 mm across the bay; top over 16 blocks u166-386 rms 0.073 px -> 2479.3)
part_leaf_stile M(vertical member fitted over 149 rows v250-442, sd 0.072/0.097 px -> width 47.9;
               u independent of z under this camera, which is why rows could be averaged)
```
