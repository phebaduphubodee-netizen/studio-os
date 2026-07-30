# Blender ground-truth study — measured gaps vs open-license photoreal files (2026-07-30)

Stats extracted headless (Blender 5.1.2) from 5 open files + our 2 g10 builds.
Raw stats: `C:/Users/teza_/blender-study/stats/*.json` (outside repo).
Ours = `pipeline/output/room_bedroom_suite_eye_lc1.blend` (+ `_bedhero`, identical scene, 24 vs 26mm lens).
Files: **Classroom** (C. Seux, 2019/2.7x era) · **Barbershop** (Agent 327, 2.78 era) · **Italian Flat**
(flat-archiviz, same genre+era as us) · **PH Gothic Bed** · **PH Throw Pillows** (bare Poly Haven assets).

## 1. Verdict

Three gaps dominate, all measured, none taste. **(1) Image-free materials:** 2/41 of our materials carry
any texture image (4.9%); the three full scenes run 52/85 (61%), 359/547 (66%), 54/109 (50%) — and both
Poly Haven cloth assets are 100% map-driven (diff+rough+nor) with sheen at 0.0. Our fabric realism budget
sits in a channel (Sheen 0.7–1.0 flat) that the pros barely use (Italian Flat max = 0.4 const, 8 fabric
mats; every other file 0.0). **(2) No key in the light rig:** our 30-light energy range is 5.93–60 W
(10:1), the top source a 2 m cool-blue fill — while Classroom spans 0.79–1963.5 W (~2500:1, daylight-keyed),
Barbershop 0.79–150 W (191:1, one warm 150 W chair key), and Italian Flat drives the frame with HDRI @ 2.0
+ exposure +1.116 vs our 0.55 @ −0.1. IES: 0/30 for us; Italian Flat (the one same-genre file) is the only
scene using IES and uses it on 4/13 lights. Flat light is in the numbers, not the eye. **(3) Pinhole camera
+ hollow soft geometry:** every scene camera is f/1.4–f/2.4 (Barbershop 1.4, Classroom 2.08, Italian 2.0–2.4
on 4 "Details" cams); even PH turnaround cams stop at f/4–8. Ours is f/9. Meanwhile our pillows are 156
polys vs 3,124–3,238 (PH pillows) and 88,374 (Italian Flat's `Pillows`, no modifiers, raw sim/sculpt).

## 2. Gap table

| Lever | THEIR numbers (named) | OURS | Gap reading |
|---|---|---|---|
| Fabric materials | PH Pillows: 3 maps (diff/rough/nor), Sheen 0.0, R+N LINKED. Italian: 8 fabric mats sheen const 0.4 (×7) / 0.2 (×1), Normal 53/97 linked. Classroom/Barbershop: fabric = Diffuse+Aniso stacks w/ image tex + Bump (38 / 91 mats w/ Bump) | 0 image maps on any fabric; Sheen flat 0.7 (duvet/towel), 0.8 (pillow), 0.9–1.0 (curtains); noise-driven R/N | We compensate missing rough/normal MAPS with 2× the max pro sheen. Pro cloth = maps + geometry, sheen ≤0.4 |
| Hard materials | Classroom 52/85 textured (1024² ×21, 512² ×14); Barbershop 359/547 (512² ×361 — small tileables reused); Italian 54/109 (2048² ×25, 4096² ×9), Rough 22/97 linked | 2/41 textured (floor 3×2k, rug 4×2k); oak veneer = Wave+Noise procedural, Roughness const 0.38; 23/39 mats const Roughness | 95% image-free vs 50–66%; pros vary roughness per-pixel even on 512² tiles |
| Light rig | Classroom 10 (5 SPOT @100 W, AREA 1963.5 exterior + 0.79, SUN, range ~2500:1). Barbershop 15 (AREA 0.79–3.93 @0.15–1.46 m; SPOT 1–150 warm key). Italian 13 (7 AREA 2.36–7.85 @0.2–2.02 m; 4/5 POINT w/ **IES** @0.5 W; SUN 1.91) | 30 lights (22 AREA, 6 SPOT, 2 POINT), 5.93–60 W = **10:1**; biggest = 2 m cool-blue Fill 60 W; IES 0/30 | 2–3× more lights, 20–250× less dynamic range, zero photometric profiles; our strongest light is a flat fill, theirs is always a key |
| World / HDRI | Classroom: strength 0.0 (SUN+sky portal). Barbershop: 1.0, no HDRI (lamp-lit). Italian: qwantani_4k @ **2.0** + LightPath dual-BG + Blackbody | rainforest_trail_4k @ 0.55 | Same-genre file feeds ~3.6× our env energy; our HDRI is fill-only, not a light story |
| Color mgmt | Standard/None/0.0 (Classroom); Filmic/None/0.0 (Barbershop, both PH); Filmic + High Contrast, exposure **+1.116** (Italian) | AgX + Medium High Contrast, exposure **−0.1** | Transform choice fine (AgX newer than all files); the sign differs — Italian grades UP a strong rig, we grade DOWN a weak one |
| Camera | f/2.08 25mm (Classroom); f/1.4 13mm (Barbershop); f/2.0–2.4 on 4 DoF cams incl. 2 "Details" 50–70mm (Italian); f/4–8 turnaround (PH Bed) | f/9.0, 24/26mm | Ours is past even asset-catalog aperture; no detail-shot camera exists |
| Cloth mesh density | Italian `Pillows` 88,374 (no mods), `Pouf` 58,309; PH pillows 3,238/3,124; Classroom `coat 1` 2,308 + SUBSURF+SOLIDIFY | pillowsoft 156, garments 544–1,232, duvet 3,364, coverlet 13,578 | Pillows 20–566× under pro floor; garments ~2–4× under a 2019 coat; coverlet/curtains are in range |
| Modifiers | SUBSURF 33/300 meshes (Classroom), 726/1989 (Barbershop), 56/476 (Italian); BEVEL 0 / 251 / 90 | BEVEL 395/488 (81%), COLLISION 2, **SUBSURF 0** | We bevel everything and subdivide nothing; pros smooth soft forms with SUBSURF |
| Samples | 300 (Classroom), 800 (Barbershop), 576+denoise (Italian), 128 (PH) | 256 + denoise | **No gap** — inside pro band; not a lever |

## 3. What to wire (ranked by measured distance)

1. **Fabric texture maps** [geometry-side for rough/normal response; base-color weave partly
   image/beauty-pass-side] — put 2k diff/rough/nor tileables on duvet/coverlet/pillow/curtain like the
   rug already has (`pipeline/scripts/build_room.py` fabric block). PH proves 3 maps + 3k polys reads as
   cloth; a Gemini pass can paint weave but cannot create map-driven specular breakup under our lights.
2. **Sheen cap 0.4** [geometry-side] — clamp all Sheen Weight to ≤0.4 (Italian's measured max); ours run
   0.7–1.0. One-line change, zero cost, removes an out-of-range physical claim no beauty pass will fix.
3. **Key-light ratio** [geometry-side] — raise HDRI toward Italian's 2.0 (or add a dominant warm key) and
   demote the 60 W cool Fill; target energy range ≥100:1 vs today's 10:1. This IS the flat-light residual.
4. **IES on downlights** [geometry-side] — 30 local `.ies` files already fetched; Italian confirms same-genre
   use (4/13 lights). Beam structure on walls is geometry/light transport; Gemini cannot invent it coherently.
5. **f/2.0–2.8 hero/detail camera** [geometry-side] — add a details-cam path (Italian ships 2 dedicated
   "Details" cams at f/2.0–2.4); keep f/9 only for documentation wides. Bokeh from a beauty pass fakes
   occlusion; real DoF doesn't.
6. **Pillow density floor ~3k polys** [geometry-side] — 156 → ≥3,124 (PH measured floor); garments toward
   ≥2,308 (Classroom coat) via SUBSURF, which we use exactly 0 times against their 33/726/56.
7. **Grunge/two-tone fabric break-up** [image/beauty-pass-side — the Gemini pass would largely erase this;
   wire only the cheap deterministic version from the vault recipe if the pass stays billing-blocked].
8. **Do NOT touch samples** — 256+denoise sits inside the measured 128–800 band; spend the cycles elsewhere.

## 4. Vault already knew (file evidence now confirms — wiring justified twice over)

- **IES rule** (`knowledge/lighting/cycles-lighting-camera-presets.md:59`, DR rule 5; local files listed in
  `knowledge/lighting/ies-and-lighting-notes-discord.md:68-93`) — Italian Flat: 4/13 lights IES. Confirmed.
- **HDRI strength band open knob** (`cycles-lighting-camera-presets.md:104-114`) — Italian runs 2.0 + exposure
  +1.116 vs our 0.55 @ −0.1. The starved-fill hypothesis now has a same-genre number. Confirmed.
- **Luminance-ratio 20:1 instrument** (`cycles-lighting-camera-presets.md:169`) — our 10:1 energy range vs
  their 191–2500:1 is exactly what this C0 instrument would have flagged years of "flat" verdicts ago. Confirmed.
- **f/2.8 detail shot** (`knowledge/rendering/render-quality.md:128-129`) — Italian ships f/2.0–2.4 Details
  cams; every pro scene cam ≤ f/2.4. Confirmed.
- **Fabric falloff/two-tone recipe** (`knowledge/materials/texture-sets-discord.md:191-195`) — partially:
  files show fabric = maps + low sheen, not the sheen=1.0 fake; the specific two-tone recipe itself is not
  observable in stats.
- Not evidenced by these files (stats can't see it): texture-scale sanity (MA-02), albedo scorer, dressing
  WARN rules, AOV passes — still vault-justified, just not double-confirmed here.

## 5. Honest limits (DR-worthy questions these files could not answer)

- Light **placement/aim** and portal geometry are invisible in stats — WHERE the classroom sun enters, how
  the Italian PRTL areas sit in window openings. Needs opening the .blend in a viewer, not JSON.
- **Texture content quality** — a 512² tileable can be great or mud; stats count maps, not their craft.
  UV texel density (rule 6/MA-02) unverifiable here.
- Two of three scenes (Classroom, Barbershop) are **pre-Principled film sets** (Diffuse+Anisotropic idiom,
  2.7x era) — their material numbers describe a different shading system; only Italian Flat is same-genre,
  same-era evidence. n=1 for archviz.
- **AgX is unjudged** — no reference file uses it; our transform choice has no comparison point here.
- Poly Haven assets carry **no lighting/camera context** — they bound cloth asset quality only.
- Whether map-driven fabric vs sheen-driven fabric is visible at OUR camera distances — needs a paired A/B
  render, not file forensics.
- What the Gemini beauty pass can actually erase (item 7 vs items 1–6) — no evidence here; that boundary is
  the owner's billing-gated experiment.

พร้อมให้ตัดสิน
