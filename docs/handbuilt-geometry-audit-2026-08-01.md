# Hand-built geometry audit — 2026-08-01

**Why this exists.** The owner, 2026-08-01: *"ผมสังเกตุว่าเวลาคุณต้องปั้น model
ที่มีรายละเอียดส่วนเว้าส่วนโค้งต่าง ๆ มันมักจะเพี้ยนเสมอ ตั้งแต่ทำมาในทุก project
มีวิธีแก้ที่ยั่งยืนมั้ย"* — an observation across every project, not one lane.
He is right, the pattern has a clean edge, and this file is the measured half of
the answer. The rules it produced are R8 and R8b in `CLAUDE.md`.

## The edge the evidence draws

| built from MEASURABLE numbers | rounds to land |
|---|---|
| vase (`lathe` from a row-by-row probed profile) | **1** |
| candlestick (`lathe`) | **1** |
| all millwork — towers, header, plinth, steps, box, drawers | **1** each |

| FREE FORM, hand-modelled | rounds spent |
|---|---|
| garments (PRJ-2026-002) | **5**, plus 785 hand-written lines of cloth physics; sim ended at 3/12 |
| Buddha figure (TRN-001) | **5**, still approximate |
| lily spray (TRN-001) | **6** |
| pillows | 156 polys against 3,000 in every pro file measured |

**The dividing line is not difficulty, it is whether the shape is RECOVERABLE
FROM MEASUREMENT.** A cabinet *is* its dimensions. A vase is a 1D profile turned
about an axis, and that profile can be read off the target row by row. A seated
figure is several hundred correlated decisions and no measurement of a 200 px
render recovers them, so the parameterisation has to be invented first — and the
invented parameterisation is the guess. Each round then fixes what it named and
reveals what no setting of it can express (no face, no robe folds, no crossed
legs). Same family as *a knob that cannot reach* and *one parameter carrying two
things*, both already in the measurement-discipline record.

## The probe: what Blender already does, headless

`scratchpad/organic_probe.py`, run under `-b --factory-startup`. Every technique
built with `bpy.data.*` and `ob.modifiers.new()` only — **no `bpy.ops` touched
geometry**, so none of it collides with the headless law in `pipeline/CLAUDE.md`.

| technique | output | n-gons | cost | deterministic |
|---|---|---|---|---|
| SUBSURF level 1 / level 3 | 24f / 384f from a 6f cage | 0 | 4 / 2 ms | yes |
| SKIN + subsurf (edge skeleton → limb) | 928f | 0 | 3 ms | yes |
| METABALL (masses that MERGE) | 1020f | 0 (352 tris) | 3 ms | yes |
| CURVE bevel + taper | 360f | 0 | 1 ms | yes |
| DISPLACE on a subdivided cage | 1536f | 0 | 5 ms | yes |
| REMESH voxel | 1734f | 0 | 18 ms | yes |
| CORRECTIVE_SMOOTH | 96f | 0 | 1 ms | yes |
| GEOMETRY NODES | 96f | 0 | 2 ms | yes |
| **our hand-built figure** | **759f** | **3 ⚠** | 5 ms | yes |
| our figure + SUBSURF 2 | 12,176f | 0 | 41 ms | yes |

Two things to carry out of that table. **Nothing is blocked by headless** — the
one honest reason for hand-writing generators does not exist. And **our own
hand-built geometry carries n-gons that every one of these tools avoids**, which
the export law in `pipeline/CLAUDE.md` forbids outright.

## And the part the probe got wrong

On the numbers subdivision looked free: 759 → 12,176 faces in 41 ms with the
n-gons gone, and the 2026-07-30 ground-truth study had already measured our
files at SUBSURF 0 against pro files that use it. **Rendered, it was worth
nothing.** Applied to everything it rounded away the stepped pedestal's ledges —
the exact thing flat shading had been introduced to save two commits earlier.
Restricted to the cast body it changed nothing visible at all, because the body
is smooth-shaded at 24 segments per ring and at 200 px on screen there was never
any faceting to remove. 16× the geometry for zero, reverted to a spec-gated 0
with the code path kept.

**Subdivision smooths what EXISTS and cannot add what was never there.** The
figure does not read wrong because it is faceted. A probe proves REACHABILITY;
only a look proves VALUE — and I claimed the win off the table before looking at
the picture, which is the failure this repo has written down more often than any
other.

## The inventory — 1,370 lines of hand-written generator

Measured by AST (a function counts if it builds verts/faces), largest first.

| module | generator | lines | what Blender already has | verdict |
|---|---|---|---|---|
| trn001_geom | `masses` | 174 | — (spec → boxes, the millwork core) | **KEEP** |
| softgoods | `garment` | 160 | cloth sim + DISPLACE | **DUPLICATE** |
| trn001_styling | `build_styling` | 131 | — (materialiser, not a generator) | **KEEP** |
| softgoods | `flat_sheet` | 110 | subdivided grid + cloth/DISPLACE | **DUPLICATE** |
| softgoods | `cushion` | 82 | METABALL or subdivided cage + cloth | **DUPLICATE** |
| trn001_styling | `floral_spray` | 74 | CURVE bevel/taper + Geometry Nodes | **DUPLICATE** |
| softgoods | `hanger` | 73 | CURVE bevel, or SKIN | **DUPLICATE** |
| softgoods | `folded_sheet` | 60 | cloth sim | **DUPLICATE** |
| curtains | `ribbon_mesh` | 51 | cloth sim, or DISPLACE on a grid | **DUPLICATE** |
| trn001_geom | `_plinth_masses` | 43 | — | **KEEP** |
| trn001_styling | `rect_loft` | 41 | no built-in equivalent | **KEEP** |
| trn001_geom | `landmarks_3d` | 39 | — (solver, not geometry) | **KEEP** |
| trn001_styling | `loft` | 38 | no built-in equivalent | **KEEP** |
| trn001_styling | `lathe` | 37 | SCREW modifier | **REVIEW** — ours is pure + testable, the modifier is not |
| trn001_styling | `_tepal` | 30 | CURVE bevel + taper | **DUPLICATE** |
| trn001_styling | `_leaf` | 29 | CURVE bevel + taper | **DUPLICATE** |
| trn001_geom | `_header_masses` | 29 | — | **KEEP** |
| softgoods | `trouser_fold` | 27 | cloth sim | **DUPLICATE** |
| trn001_styling | `_tube` | 22 | **SKIN modifier** or CURVE bevel | **DUPLICATE** |
| trn001_styling | `buddha_figure` | 18 | nothing — and that is the point (R8: acquire) | **MISCLASSIFIED** |
| softgoods | `arm`, `bar`, `_loft_faces`, `_grid_faces`, `bbox`, `verts_in_rect` | 64 | — (helpers) | **KEEP** |

**Totals: ~646 lines DUPLICATE, ~706 KEEP, 18 misclassified.** The duplicates are
not evenly valuable to replace — `garment`/`flat_sheet`/`folded_sheet`/
`trouser_fold`/`ribbon_mesh` (408 lines) are all the same bet on hand-written
cloth, and the cloth sim was already proven headless, deterministic and 0.48 s in
July. That is one lane, not five.

## What NOT to conclude

* **Not "rewrite everything with modifiers."** The KEEP column is 706 lines that
  are pure, testable under plain `python`, and answer to the LAYER LAW — a
  modifier is none of those, and `lathe` is on the fence for exactly that reason.
  A modifier's output can only be inspected through a depsgraph, i.e. inside
  Blender, which puts it on the wrong side of the layer split for anything a
  gate has to check.
* **Not "assets solve it."** The CC0 pool was searched exhaustively (521 models):
  it has no religious statuary and no cut-flower arrangement. Acquisition is the
  right default and it still fails for the two classes this room is *about*.
* **Not "we needed a DR."** The sourcing half was already researched on
  2026-07-01 (`knowledge/_inbox/interior-ai/2026-07-01-asset-sourcing-DR.md`),
  and the DISTILLATION-LEDGER already records that its prices and licences are
  fabricated and were overridden by web checks. Firing another would have been
  the fifth repeat of *search our own vault first*.

## 3D Warehouse — the source the research missed, and the reason it did

**Owner, same day, after asking a working designer:** *"เค้าบอกว่า model
furniture ส่วนใหญ่หาจาก 3D warehouse ทำไมคุณไม่เคยไปหามา?"*

Because it is **not in our 2026-07-01 asset-sourcing DR at all.** That DR lists
Poly Haven, BlenderKit, 3dassets.one, manufacturer sites, Poliigon, Dimensiva,
3D Sky and Design Connected — and our own DISTILLATION-LEDGER already records
that its prices and licences are FABRICATED and had to be overridden by web
checks. I leaned on a document this repo had itself flagged as partly invented,
instead of asking someone who does this for a living. The signal was also
everywhere in our own files: `pipeline/CLAUDE.md` carries an entire *Export and
interop law (SketchUp-using collaborator)* section, we ship a `build_room.rb`
SketchUp generator, and the Discord corpus is a SketchUp/3ds Max designer
community. Every one of those points at 3D Warehouse and I followed none of them.

**Probed 2026-08-01, and it works end to end:**

* API is open and needs no key:
  `3dwarehouse.sketchup.com/warehouse/v1.0/entities?q=…&contentType=3dw`
* The classes this studio keeps failing at are all there — *"Thai Buddha altar"*
  (862 downloads), Buddha statues (one at 27,511), lily flower vases — and so is
  ordinary furniture.
* **Every hit offers `.glb`**, which the glTF path already in `build_room.py`
  ingests. No new format work at all.
* Downloaded and imported the Thai altar headless: **3,394,819 verts /
  2,110,314 faces / 0 n-gons**, 55 materials, 11 images, one root, clean import.

**Two honest caveats, and they decide HOW it gets used rather than whether.**

1. **The content is unfiltered.** That "Thai Buddha altar" is not a component —
   it is somebody's entire project, 13.9 × 17.3 × 3.1 m of room at 2.1M faces.
   Usable, but it has to be MINED for the part we want, and the scale assertion
   `pipeline/CLAUDE.md` already mandates is what tells you which you have got
   (17.3 m reads as a room in metres; under the SketchUp inch trap the same
   model would be 439 mm, which is why that assertion is not optional).
2. **The licence is not CC0.** 3D Warehouse models carry Trimble's General Model
   License: free to download and use in your work, not public domain, and not
   redistributable AS MODELS. Decision (ข) currently reads "฿0 + CC0/
   public-domain only", and that rule now excludes the best free source
   available. **Widening it is the owner's call, not this lane's.** Nothing has
   been written into the repo's asset cache; the downloaded model sits in the
   scratchpad pending that decision.

## Open items

1. **The n-gons.** `lathe`, `loft` and `rect_loft` all cap their first and last
   ring with a single face — a 24-gon on the figure. The export law forbids
   n-gons. Fix is a fan to a centre vertex (triangles are allowed); a test now
   pins it.
2. **The cloth lane, 408 lines against a simulator proven in July.** Own lane.
3. **Statuary acquisition** — photogrammetry of a real image (฿0, one-time,
   respectful, and it gives a model with provenance) versus a paid library.
   Owner's call; recorded as a fact, not proposed as a purchase.
