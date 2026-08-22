# LICENSING — furniture models & client deliverables (LOAD-BEARING)

Research wf_0246d7e9 (2026-06-30, with an adversarial license skeptic). The founder has
real money + liability exposure → these rules are binding, not advisory. **When in doubt,
do NOT ship the model.**

> **2026-08-01 — nothing in this file changed, and that is the point.** The owner cancelled the
> separate "฿0 + CC0/public-domain only" SOURCING clause (`docs/DECISIONS-render-assets.md`, top
> entry), which had been narrower than this file: the table below already whitelists 3D Warehouse.
> The sourcing rule is now *any licence permitting commercial use of the render*. **Every DELIVERY
> rule here survives it unchanged** — Combined-Work-scene-only, no standalone model, no aggregation,
> no redistribution of a non-redistributable mesh (which is why `assets/shared/warehouse/` is
> gitignored), provenance recorded per asset, and the scale sanity-check. A wider sourcing rule makes
> this file MORE load-bearing, not less: the repo now holds assets under several licences at once, so
> "which licence is this one?" stops being rhetorical.

## The one rule that protects us
**Deliver to a client ONLY the assembled ROOM SCENE** (`.skp` = shell + layout + multiple
placed components + in-model dimensions = a "Combined Work" with substantial added content).
**NEVER** hand over / sell / re-upload / publish:
- a **standalone** furniture model, or
- the **`furniture_catalog.json` + `raw/assets/` bundle** (= prohibited aggregation).

The catalog is an **INTERNAL build input only** — kept out of every client handoff and out of
any public repo (`furniture_catalog.json` is gitignored; `raw/assets/*.skp` is gitignored).

## Sources — whitelist vs blacklist
| Source | Client-deliverable? | Notes |
|---|---|---|
| **SketchUp 3D Warehouse** | ✅ ONLY as a Combined-Work scene | General Model License 1.3.2 "Combined Work" carve-out; 2.4 no standalone sell, 2.6 no aggregation. Manual download only (ToS 10.5.6 bans scraping; ~100-dl cap + bans). |
| **FurniMesh** | ✅ cleanest — **FETCHED 2026-08-22 (17 models)** | Explicit "free to use in commercial projects"; the ONLY source legal to script-fetch. **Fetcher: `pipeline/scripts/furnimesh.py`** (ORD-2026-08-22-process-review-actions item 3), cache `assets/shared/furnimesh/` (gitignored — the grant is USE, not redistribution), every query logged in `qa/furnimesh-search-log.json`. Licence re-verified live 2026-08-22 on the library pages: *"free for commercial use without attribution … no royalties, no licensing fees, and no 'personal use only' restrictions"*. Shelf as of 2026-08-22: **17 models** (6 nightstand, 4 bench, 4 table lamp, 3 vase), all scale-asserted — 9 in band, 8 refused, **and the refusal pattern is the tier's real caveat: these are AI photo→3D models normalized to ~1.0 m on the longest axis** (8 of 17 within 5 mm of exactly 1000), so arrival size ≠ real size and `fit: true` scaling at placement is mandatory (`examples/furniture_catalog.example.json`). History: this row said NOT YET FETCHED for weeks — a paid Deep Research on 2026-08-17 "found" the source this table had ranked first all along, with 0 files on the shelf; `repo_first.py` was written from that instance. Record: `knowledge/_inbox/nlm-free-asset-sources/`. |
| **Your own original models** / **CC0** | ✅ | No restriction. |
| **BIMobject** (incl. Häfele on BIMobject) | ❌ personal-use only | EULA 4.4(b) personal/non-commercial; 4.7(f)(g) no transfer/incorporate-for-third-party. |
| **CADENAS / PARTcommunity / 3Dfindit** (the Häfele CAD route) | ❌ personal-use only | §8 "personal uses only … passing to third parties is not permitted". |
| **Häfele own portal** | ❌ until verified | EULA un-retrieved; "free of charge" ≠ a redistribution grant. Read it before relying. |
| **XSurface** | n/a (materials) | Thai MATERIAL library (laminates/tiles/panels) — a finish/spec tool, **never** a geometry source. |
| **HomePro** | facts only | Retail catalog; ToS forbids reuse of their images/spec text. The **dimensions** (uncopyrightable facts) are usable → re-model from measurements; never lift their images. |
| **Poly Haven** | ✅ | CC0 — commercial use, redistribution and AI/ML all explicitly permitted on their own licence page. Already fetched by `pipeline/scripts/assets.py`; committable. |
| **ambientCG** | ✅ (not yet used) | CC0 — "may be used for commercial purposes, even if that means redistributing them as files". No fetcher yet, **and deliberately not written yet** — see the note under Automation. |
| **Poliigon** | ❌ **DECLINED 2026-08-08** | Not a legal finding — a **decision**, and the reason is below the table so it cannot be skimmed past. |
| **BlenderKit** | ⚠️ CC0 tier only | Two licences: CC0 (free) and Royalty-Free (commercial OK, no resale as an asset). Only the CC0 tier may be committed; RF must be gitignored like 3D Warehouse. **Their docs are silent on AI/ML — treat that as unanswered, not as permitted.** |
| **Sketchfab / Fab** | ⚠️ per-model | CC0 / CC-BY / CC-BY-NC / CC-BY-ND all coexist; **CC-BY-NC is unusable for client work**. Fab (Epic, incl. Quixel Megascans) forbids redistribution at every tier and its terms are still changing; Quixel's own licence page returned 403 on 2026-08-05, so the post-2024 "free" status is **unverified**. Read the individual model's licence, every time. |

### Poliigon — DECLINED, and why a decision rather than a reading
**Owner order 2026-08-08.** Poliigon's terms forbid AI/ML use without a separate licence.
Our intent is a perceptual *metric*, not model training — but `pipeline/scripts/style_embed.py`
is real, runs CLIP (open_clip, local CPU) over our renders, and **builds embedding banks**; a
Poliigon texture would sit inside the images that get embedded. The interpretation risk is
therefore not zero, and the community has reported terms being tightened without notice
(no-cloud-render, no-bake-to-UV, no-embed-in-a-sold-model).

**What decides it is the price of saying no, and the price is about zero:** ambientCG is CC0,
carries the same `Fabric0xx` / `Carpet0xx` sets *with displacement*, may be committed, and we
have never once used Poliigon. **We would be buying permanent uncertainty for something the
public domain already gives us.** Revisit only if a specific material exists there and nowhere
CC0 — and then buy the separate licence rather than reasoning about intent.

## Automation
**Manual-download workflow by design.** Scripted/bulk fetch is independently ToS-banned on 3D
Warehouse, BIMobject, CADENAS (account ban + legal risk) — even where the model license is
permissive. **Exception: FurniMesh** may be fetched directly. At ~12 mapped kinds, hand-curation
is fine.

### No second fetcher before there is a consumer (2026-08-08)
An `ambientcg.py` is worth writing and is **deliberately not written yet**. TRN-002 r34 ran this
studio's first real acquisition and it failed in a place nobody had looked: sourcing worked on
the first try, the licence was clean, `pipeline/scripts/asset_scale.py` asserted the unit — and
then **`trn002_build.py` turned out to have no glTF import path at all.** `build_room.py` has the
ingest; that builder never got one. **That, not licences and not "no CC0 wardrobe exists", is why
26 assets sit unused in `assets/shared/`.** Writing a second fetcher before the ingest path exists
would be the same mistake with a new logo. Order: **ingest path → then the fetcher.**

## Dimensional correctness
Warehouse models are user-uploaded with **no accuracy/scale guarantee**. `build_room.rb`
warns (SCALE WARNING) when a placed model's footprint deviates >50% from the spec — a wrong-scale
model silently destroys the whole "dimensionally-correct" value prop. Always sanity-check.

## Provenance discipline (enforced in code)
Every catalog entry carries `source` + `license`. `build_room.rb` prints a **LICENSE WARNING** for
any model whose license is not in the permissive set
(`furnimesh / 3dwarehouse-combined / original / cc0 / commercial-ok`). Keep the provenance honest so
every shipped model is auditable to a permissive source.

## Furniture is stored LOCALLY (the cloud-furniture plan was dropped)
Per the 2026-06-30 `/scrutinize` rework, furniture `.skp` live in **`raw/assets/` (local)**, never re-hosted in R2 and
never served to the friend via presigned URL. This sidesteps the redistribution question entirely (especially for 3D
Warehouse models, which may NOT be aggregated/redistributed) and avoids duplicating SketchUp's native component browser.
R2 (`r2int:`) is reserved for hosting **finished client deliverables**, not model assets.

## The friend's library is NOT automatically safe
If her shared `.skp` came from BIMobject / Häfele / PARTcommunity, the personal-use restriction
**travels with the file** — her sharing it does not launder the license. **Ask her where each model
came from** before treating it as deliverable. Her own-modeled / 3D-Warehouse / FurniMesh assets are
fine; BIMobject/Häfele-sourced ones are not.
