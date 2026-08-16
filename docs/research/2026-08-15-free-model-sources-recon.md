# Free 3D model sources — live recon, licence / format / scriptability

**2026-08-15. Owner-initiated.** He named eight free sources and cancelled the pending
spend ask: *"หากคุณกำลังมองหาของตกแต่งหรือเฟอร์นิเจอร์ที่ดูดีมีสไตล์ แนะนำให้เริ่มค้นหาจาก
Dimensiva และ Poly Haven ก่อน"*.

Method: one probe agent per source, then a second agent per source whose only instruction
was to REFUTE the first using a different URL or a different method, defaulting to refuted
when it could not reproduce. Two failure modes were hunted by name: a licence described
from memory rather than quoted from a fetched page (this repo has already been burned by a
DR that fabricated licences and prices), and a format list that waves `.max` or `.skp`
through as importable. Only re-verified claims appear below. **Every licence quote here
came off a page that was fetched twice, by two different agents.**

---

## 0. THE BLOCKER IS OUR CODE, NOT THE SOURCES

`grep -rEn 'bpy\.ops\.(import_scene|import_mesh|wm\.(usd|obj|ply|stl|collada|alembic))'`
over the whole repo returns **six hits and all six are the same call:
`bpy.ops.import_scene.gltf`.**

Probed against the installed binary (`Blender 5.1.2`, `-b --factory-startup`), Blender
itself offers `import_scene.gltf`, `import_scene.fbx`, `wm.obj_import`, `wm.usd_import`,
`wm.collada_import`, `wm.stl_import`, `wm.ply_import`. `has_max = False`, `has_skp =
False` — confirmed by string-scanning every operator name, so those two really are poison
and everything else is ours to open.

Four places need code for a new format: `build_room.py:6683` (extension dispatch in
`place_model`), `build_room.py:6447-6448` (`_model_path` globs only `*.gltf`/`*.glb`, so a
`.obj` on the shelf is invisible), the fetch half (already format-agnostic —
`warehouse.py:143` passes any `--format` string through, and `search()` at :83 lists
glb/skp/dae/kmz/usdz/obj), and `asset_scale`, which is deliberately bpy-free and cannot
measure the bounds of a non-glTF file.

---

## 1. VERDICTS

### USABLE TODAY — no new code, no account

**Poly Haven** — `USABLE_NOW`, and the catalogue is the whole limitation.
- Formats: all **85/85** furniture assets ship the identical set `(blend, fbx, gltf, usd)`
  — the format-combination histogram returns a single entry. **There is no `.glb`
  anywhere (0/85)**, yet `build_room.py` globs for it; that half of the glob is dead here.
- Import proven, not inferred: gltf → 1 mesh, 2002 faces, 1 material, 3 textures that
  resolve; `.blend` via `bpy.data.libraries.load` → same 2002 faces, 12-node material.
- **Free scale oracle.** Blender measured `ClassicNightstand_01` at 567.8 × 424.2 × 700.0
  mm against the API's declared `[567.7522, 424.1928, 699.9649]` — agreement under 0.1 mm.
- Licence: CC0 1.0 site-wide. `polyhaven.com/license` (200): *"You can use our assets for
  any purpose, including commercial work."* Mesh redistribution permitted — which is why
  `assets/shared/cc0/` is committed.
- **Scripting is governed by a separate document the first probe never fetched.** Site ToS
  3.2 bars web scraping; ToS 5 points at the API Terms
  (`github.com/Poly-Haven/Public-API/blob/master/ToS.md`, 200): 2.1 free commercial use,
  2.3 never a key — **so the API is the licensed channel and scraping the site is not.**
  2.4 requires a unique Referer or User-Agent matching your software name; we comply by
  luck of an existing line — `assets.py:38,47` sends `interior-ai/1.0`. Bare curl would
  not comply.
- Stress: 12 rapid `/files/` calls → 12/12 200; a further 85 sequential → 85/85 200.
- **Catalogue, confirmed by full-catalogue search not sampling: 521 models, furniture 85,
  seating 34, lighting 29, table 27, shelves 16, bed 3 — and ZERO rug, carpet, wardrobe,
  dresser, curtain, drape, mattress.** Tag histogram over the 85: vintage 51, wood 35,
  old 33, antique 25. The 3 beds are a Gothic bed, a 905 mm-wide frame and a day bed.
  **It cannot supply any of the top three targets.**
- Latent bug: `assets.py:56-57` guards on `'gltf' not in files` then dereferences
  `files['gltf']` in its own fallback. All 85 currently ship gltf, so it has not fired.
- Resolution is **per asset**, not a site ladder: of 521, max_resolution 8192 → 316,
  4096 → 198, 16384 → 7. A script hardcoding `8k` KeyErrors on 38% of the catalogue,
  including `ClassicNightstand_01` and `GothicBed_01`.

**Dimensiva** — `USABLE_WITH_WORK`, small but clean.
- **The free catalogue is 82 models, not thousands.** The free grid terminates at page 2
  (50 + 32); the "1 … 559" pagination belongs to a second, site-wide EDD widget sharing
  the page.
- Scriptable with **zero auth**: `?edd_action=free_downloads_process_download&download_id=<id>`
  returns the real zip to bare curl with only a browser UA. Verified on two ids derived
  from the listing: 38614 → 200, `application/zip`, 89,311,075 B,
  `bunky-bunk-bed-by-magis.zip`; 35229 → 200, 17.5 MB. Ids come off each grid item's own
  `data-download-id` attribute — a whole page in one fetch.
- Archives contain a **native `.blend`** (first four bytes `28 b5 2f fd` = zstd; after
  decompression the header reads `BLENDER-v402REND`) plus `.FBX`, `.obj/.mtl`, textures.
  Model pages declare `TYPE: Blend, 3ds Max 2017 (Vray + Corona), fbx, obj`.
- Licence, `dimensiva.com/license/` (200) §IV: *"Any items downloaded from DIMENSIVA … can
  be used in your private or commercial projects as you needed"*; content may not be sold,
  redistributed or exported separately.
- Pages publish dimensions in cm → per-model scale assertion before download.
- **Almost all of it is branded designer product** (IKEA / Magis / Flos / Fredericia).
  Trade dress is not cleared by a licence (R8) and is an owner call.

### USABLE ONLY AFTER AN OWNER ACTION

**3DSky** — the only source that holds our catalogue.
- Free-filtered totals, reproduced exactly by both agents: overall **92,745**; sofa 7,564;
  **bed 4,274**; wardrobe 2,791; **rug 1,878**; pillow 1,395; curtain 952; nightstand 561.
  The API's own category assignment is coherent (bed 60/60 in `Bed`, curtain 57/60 in
  `Curtain`, rug 51/60 `Carpets` + 8 `Rug`). **This maps onto exactly the R8 free-form
  classes we are forbidden to hand-model and keep hand-modelling.**
- English Terms of Use ARE retrievable by script: `3dsky.org/faq/category/10005/show`
  → 200, 123,990 B. **Clause numbers cited from `3ddd.ru`'s Russian numbering do not
  exist in the binding English document** — 10.1.9.2 and 10.3 are the operative ones and
  they permit our deliverable: a 2D render, distributable to the client.
- **Blocked on: free registration and a cap of 3 free models per day**
  (`3dsky.org/faq/228/show`, 200). Every API endpoint returns a blanket 500 to a script,
  including ones that must be public, so the 500 carries no signal.
- The licence is **revocable** — cache everything; never assume re-download.
- `fbx`/`obj` is a seller-typed string. **No archive has been opened. Unproven.**

**Sketchfab** — ships the one format we can already import, and is the hardest to trust.
- 360/360 downloadable furniture models expose `glb`.
- **`/v3/search` hard-429s after ~9 unauthenticated calls**, no `Retry-After`, no
  recovery in ~45 minutes. Use `/v3/models?downloadable=true&categories=furniture-home`.
- **`licenses=` is INERT on `/v3/models`** — a deliberately fake slug returns a uid list
  byte-identical to `cc0`. A `licenses=by` query handed back CC-BY-NC-SA models.
  **Filter licence client-side or you will ship a non-commercial mesh.**
- Licence mix of downloadable furniture (n=360): CC-BY 347 (96.4%), CC-BY-NC 3, CC-BY-SA
  3, Free Standard 3, CC-BY-NC-SA 2, CC-BY-NC-ND 2, **CC0 zero**. So 10 of 360 (2.8%)
  forbid commercial use and arrive unlabelled through the API.
- CC-BY 4.0 §3(a)(1) attribution is **seven items**, and it rides on the delivered render.
  CC-BY-SA is excluded: §3(b) would arguably force the render itself out under BY-SA.
  `free-st` excluded by default — its terms are unreadable from this machine by any route
  (WAF 202, Wayback 429/503, help centre 404).
- No scale field anywhere in the detail schema. Median 826 faces.
- **`/download` 401s even for a garbage uid. No download has ever been performed.**

**CGTrader** — real depth, WAF in front of it.
- AWS WAF returns 202/0 bytes to curl on every catalogue URL including the sitemap.
  `?search=…&free=1` works from a browser but is robots-Disallowed.
- 98.3% of free sofa cards (118 of 120) carry an importable format chip.
- Structured metadata is **two fields — `Native file format` and `Exchange formats`.**
  Two of three free pages sampled were MAX-native with importability only in the Exchange
  list; an ingest reading one field will mislabel them.
- Royalty Free (no AI) permits the render; §21A.1 bars redistribution.
- Needs headless Playwright + an account. No download proven.

### DEAD — say this plainly

**TurboSquid — DEAD for us, on yield and access, not licence.**
- Of the first 20 cards on its own *Price: Free* sofa grid (run twice, identical):
  **10 were priced $1–$45**, 2 were Editorial-Uses-Only, 3 had no importable format →
  **5 of 20 usable (25%).**
- **The Editorial label is invisible on the grid** — zero occurrences of "editorial" in
  the rendered body of the free sofa and free wardrobe grids; it appears only on the
  product page. Standard License §4: *"The following restrictions apply to any 3D Model
  with an 'Editorial Uses Only' label on its Product Page."* Editorial share ~19.7%
  (sofa) and 24.0% (wardrobe).
- It is also a .max trap in places: `garden-sofa-732823` is free, Standard License, and
  ships 3ds Max 2010/2011/2012 and nothing else.
- Access needs a **headed Chrome with a persistent on-disk profile** and a deliberate
  first 403 to earn the DataDome cookie. Plain headed Chrome got 403 on all 5 URLs. **No
  unattended job is possible.** Manual one-off only, never a pipeline.

**XOIO / Viz People — background props only, and materials do not arrive at all.**
- Licence verbatim (XOIO `00_READ_ME_FIRST_disclaimer.txt`): *"provided free of any
  charge. There are no limitations on their personal or commercial use"*; redistribution
  barred. Both are anonymous and fully scriptable (six complete XOIO zips pulled, 6.5–20.6
  MB; Viz People's OVH mirror HEAD 200 on all three OBJ packs).
- **18 of 18 `.mtl` files across five packs contain ZERO `map_` lines.** Materials do not
  land at all — they are not "single diffuse JPGs needing an upgrade". The Viz People
  chairs pack has no `.mtl` whatsoever.
- **XOIO fuses a studio backdrop into the model file** (`S_Plane_Studio`, `S_Box_Studio`)
  and Blender lands the whole file as ONE object; import it naively and a 13-metre
  invisible plane enters the room and every R9b placement check reads off it.
- Scale is neither metres nor consistent between houses: XOIO Fjord 13.457 × 8.844 ×
  8.117 units, Viz People Plattner 26.858 × 20.484 × 30.431. No single factor fixes both.
- Folder names ARE the brands: `Knoll_Plattner`, `Driade_Pavo`, `Moroso_Smock`,
  `Porada_Malindi`, `Zanotta_Yuki`, `Ligne_Roset_TOGO_CORNER`, `Ikea_kramfors`.
- Real totals: XOIO 6 packs / ~260 named groups of which ~7 are furniture-scale (the rest
  are desk and kitchen props — a class this studio is short of); Viz People 25 `.obj`
  across 4 packs.

**ambientCG — DEAD.** No meshes at any filter; textures and HDRI only.
**chocofur — UNRESOLVED, not rejected.** `/free-3d-models` 404s; the root is a JS shell.
**BlenderKit — blocked, cheap to unblock.** Royalty-free licence is fine;
`/api/v1/downloads/` returns 403 without an API key and a `scene_uuid`.

---

## 2. WHAT TO REPLACE, RANKED BY MEASURED FRAME SHARE

From `room_bedroom_suite_eye_p2r35` — the shipped id mask where it covers the object, and
a second mask render (same blend, same camera, alignment verified) where it does not. No
proxy was needed. **This ranking is one camera, one round**; lifting the camera reorders
it immediately.

| # | piece | share | px | required bbox (mm) | scale band |
|---|---|---|---|---|---|
| 1 | **rug** | **11.5534%** | 499,109 | 3100 × 2500, **aspect 1.24 is the hard constraint** | `rug` 1000–5000 on `maxxy`, `asset_scale.py:129` |
| 2 | **bed foot throw** | **8.1994%** | 354,213 | ~1700 × 1400 flat; falls 438 mm over both flanks | none exists |
| 3 | **bed cloth set** | **4.8819%** | 210,897 | dresses a 1820 × 1969 mattress, top plane z=600 | `bedding_set` 1400–2900 on y, `:85` |
| 4 | bench | 4.8292% | 208,622 | 498 × 1000 × 450 — **long axis is world y** | `bench_seat` 300–600 on z, `:125` |
| 5 | bed frame (no headboard) | 3.0590% | 132,150 | 2000 × 2149 × 600 | `bed_frame` 1800–2600 on `maxxy`, `:116` |
| 6 | bench throw | 0.8880% | 38,363 | 413 × 506 × 241 as placed | none exists |
| 7 | nightstands ×2 (cased only) | 0.5822% | 25,153 | 501 × 498 × 580, h derived from the mattress datum (D-045) | `nightstand` 300–800 on z, `:121` |
| 8 | book stacks ×2 | 0.5117% | 22,106 | 215 × 155 × 60 | none |
| 9 | folded linen / towels | 0.5115% | 22,098 | three families, 158–398 × 350–535 × 38–46 | `towel_folded` 20–160 on z |

The headboard is excluded on purpose: the client's sheet draws it as custom joinery, so
hand-building it is correct (R12).

**T1 rug** — 3DSky primary (1,878 free rugs is the only pool that can hold a 1.24; the
three prior candidates failed at aspect 0.68 / 1.17 / 1.50). CGTrader fallback, because it
publishes cm dimensions on-page so aspect is filterable *before* download.
**T2 throw** — 3DSky primary; **Sketchfab fallback is the only source that needs zero new
code**, because it ships glb.
**T3 bed cloth set — needs no source. It is already bought.**
`bed_models.cloth_set = ub806591a`, asserted at 2198.1 mm, switched off by
`_BED_CLOTH_ACQ = False` (`build_room.py:1593`) because the part cut discarded `Mesh_1`
(374 × 1600 mm = 16.7% plan area against a 33% threshold). Fix the cut, flip the flag.
**Cheapest item on the list; it must not be re-searched.**

---

## 3. WHAT MUST BE FIXED BEFORE ANY NON-CC0 MESH IS INGESTED

All four found by reading or calling our own code, not by inspection of the sources.

1. **`asset_license.licence_id('CC-BY-NC 4.0')` returns `'cc-by'` → `redistributable
   True`.** So does `'CC BY-NC-ND'`. Verified by calling the function.
   `_TEXT_TO_ID` (`scripts/asset_license.py:76`) matches the bare `cc-by` substring before
   any NC/ND variant. The NC/ND rows must be inserted above it.
2. **Nothing screens licence at render time.** `audit()` iterates `git ls-files assets`
   (`:208-217`) and `assets/shared/warehouse/` is gitignored at `.gitignore:63` — so the
   68 acquired `.glb` on the one non-CC0 shelf are never audited. The data is on disk:
   `warehouse.fetch` writes a `SOURCE.json` beside every model (`warehouse.py:111-119`)
   and 68 of 68 carry one. Read it in `place_model`; fail closed.
3. **The licence schema cannot record the question these eight sources must be screened
   on.** Every row in `LICENCES` (`:53-65`) carries `redistributable` and `attribution`
   and nothing about **commercial use of the rendered image**. `CATALOG.json`'s `licence`
   field has **zero readers repo-wide** — the queue-with-no-consumer shape again.
4. **Cased goods have no material policy, and it is an active opt-out, not an omission.**
   `place_model` sets `o["ph_model"] = True` unconditionally (`:6744`) and
   `_suite_materials` skips those objects (`:3964`). The `carries_a_pbr_surface is False
   → replace_material` branch is fenced behind `kind in _UPHOLSTERED` (`:7097-7106`),
   whose tuple (`:4515`) is sofa/loveseat/armchair/chair/lounge_chair/stool/bench/ottoman.
   Measured on the live shelf: `warehouse/th_d`, `bd_a` and `tub_chair_c` all carry
   0 normal and 0 metallicRoughness maps → the test that would fix them never runs, so a
   bought cabinet renders in a stranger's flat colour inside a signed palette.
   Soft goods DO have a policy and it is the strongest one we have (`:5098-5100` clears
   every imported material and assigns from the DD's signed value ladder) — extend that
   shape to `throw` and `rug`. **We buy fold geometry, not someone else's fabric.**
5. Known and not yet bitten: `place_model` fits `(w,d)` **then** rotates, while the spec
   stores w/d as the world footprint. Every case so far was near-square enough to hide it.
   **The bench slot is 498 × 1000 and is where it stops hiding.**
6. 15 of 68 warehouse models have no `.scale.json` sidecar; 39 of 81 shelf models read as
   `unclassified` because slot class comes from the directory name and most fetches were
   slugged with a raw entity id, so `model_fit`'s class gate is handed `None`.

---

## 4. THE OPEN FETCHES — each one settles a question nothing else can

1. **Can a file be got out of 3DSky at all?** Owner registers a free account, downloads
   **one** free rug (aspect 1.20–1.28). We open the archive, confirm an obj/fbx is really
   there and textured, and measure its unit. **Everything about the only source with our
   catalogue is on hold until this happens.**
2. **Do any of Dimensiva's 82 include a rug or a throw?** One fetch of `/free-3d-models/`
   + `/page/2/`, parse `data-download-id`. Free, zero auth — do it first; it could
   collapse T1.
3. Sketchfab token, CGTrader Playwright download, and the `free-st` terms from a different
   network. Each needs a human in a real browser once.
