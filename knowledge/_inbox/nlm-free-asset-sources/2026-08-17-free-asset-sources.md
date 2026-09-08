---
source: notebooklm
notebook_id: 5482788c-1b7b-417a-a282-9afa411cebfe
conversation_id: ea8f6ddc-bb17-48a0-b65c-fb4ab54e07d7
turns: 4 (1 asked + 3 auto-iterate)
sources_imported: 168 (162 ready, 6 error)
asked: 2026-08-17
asked_by: owner order — "ทำ DR หาแหล่ง free ก่อน"
tier: REFERENCE
---

# DR — free sources of ready-made interior assets, and made beds specifically

Transcript of record: `dr.json` (all four turns, complete answers).
Question of record: `QUESTION.txt`.

## WHY THIS FILE LEADS WITH A VERIFICATION SECTION

This repo's own DISTILLATION-LEDGER already records that the 2026-07-01
asset-sourcing DR **fabricated prices and licences**, and that it omitted 3D
Warehouse entirely while a working designer named it in one sentence. So every
count, price and licence below is REFERENCE tier and none of it may gate a
deliverable until checked. One claim was checked the same hour and it did not
survive.

## CHECKED THE SAME HOUR — what survived and what did not

| DR claim | verdict |
|---|---|
| FurniMesh is "a specialized, hand-reviewed furniture library hosting over **267** 3D bed models featuring **pre-simulated fabric covers**" | **DID NOT SURVIVE.** The site's own `<title>` is *"FurniMesh — AI Image to 3D Model Generator for Furniture"*. No 267-bed claim appears anywhere on the home or library page. The number looks invented — the same failure mode the ledger already pinned on the 2026-07-01 DR. |
| FurniMesh is genuinely free, no paid tier, commercial use, no attribution, native GLB/OBJ/SKP/BLEND | **SURVIVED**, verified on the live pages 2026-08-17: *"Browse 9,778+ hand-curated 3D furniture models in GLB, OBJ, SKP, and BLEND — every model reviewed by our editorial team"* · *"every output is licensed for commercial use, no attribution required"* · operated by UAB FURNISYSTEMS (Lithuania, EU-funded). It is ALSO an AI photo→3D generator (free tier ≈10 generations). |
| whether FurniMesh's library holds beds authored MADE (duvet covering the whole mattress) | **NOT CHECKED.** The category filter is client-side, so the HTML carries no per-category count. This is the next cheap test, not a claim. |
| 3dsky free tier = 3 downloads / 24 h; 15,167 models in its Bed category; PRO $7/asset | **NOT CHECKED.** If true it is the industry's own bed library at ฿0/day, and `ASK-001` priced 3dsky as if buying were the only route. |
| CGMood 3 free/day + Pro €6/mo · Zeel Basic $9.99/mo · Dimensiva €289–299/yr · Chaos Cosmos free WITH a V-Ray/Corona/Enscape licence (V-Ray Solo ~$470/yr) | **NOT CHECKED.** |
| BlenderKit Full ≈ **$108/yr** | **CONFLICTS WITH OUR OWN FILE** — `ASK-002` and `docs/DECISIONS-render-assets.md` carry **$118.80/yr**. Verify before any spend. |

## THE ANSWER THAT CHANGES OUR METHOD (turn 1, question 4)

Studios split bedding acquisition in two, and neither half is what this lane does:

- **80–90% — download, then REBUILD THE MATERIALS.** Pre-made beds come from
  3dsky / CGMood / Dimensiva, and *"they rarely use these beds straight out of
  the box"*: default low-res textures are discarded and custom PBR is built from
  high-resolution fabric scans (Poliigon, Quixel Megascans), with roughness and
  displacement tuned and a fuzz/sheen layer added.
  → **We do the download and skip the rebuild.** P2h ("materials split by ROLE
  on acquired meshes") is not polish that comes after — it is half of the
  standard method.
- **10–20% — custom cloth simulation for hero shots**, master suites and
  close-ups, in **Marvelous Designer** (pattern-based, drape onto a subdivided
  collision proxy of the mattress, pins for a folded-back duvet, particle
  distance lowered at the end for micro-wrinkles, exported as thick FBX/OBJ).
  → DELIV-001 is a master-suite hero frame — the 10–20% case by the DR's own
  description. **Marvelous Designer had never been named once in this repo**
  before this DR; our five failed cloth attempts were all hand-written Blender
  physics, which is not how the trade does it. Routed as an ask, never a builder
  decision: it touches his standing order that bed cloth is ACQUIRED (R13).

## AND OUR OWN FILE ALREADY RANKED THE WINNER FIRST

`docs/LICENSING.md` has said all along:

> | **FurniMesh** | ✅ **cleanest** | Explicit "free to use in commercial projects"; **the ONLY source legal to script-fetch.** |

and, under Automation: *"**Exception: FurniMesh** may be fetched directly."* The
permissive-licence set enforced in `build_room.rb` literally begins
`furnimesh / 3dwarehouse-combined / original / cc0 / commercial-ok`.

**We have never fetched one model from it.** There is no `furnimesh.py`; the two
fetchers that exist are `assets.py` (Poly Haven) and `warehouse.py` (3D
Warehouse). Shelf provenance, counted 2026-08-17: **166 `trimble-gml` + 26
`3dwarehouse.sketchup.com` + 3 `blenderkit-royalty-free` + 0 furnimesh** — i.e.
the entire shelf comes from the source the same table marks *"manual download
only (ToS 10.5.6 bans scraping; ~100-dl cap + bans)"*.

This is the repo's own recorded corollary happening a second time: *"When an
outside answer surprises you, check whether the repo was already implying it."*
Last time the outside answer was 3D Warehouse and our files pointed at it from
three directions. This time the outside answer is FurniMesh and our own licence
table had already ranked it #1.

## LICENCE FLAG, not a route

`knowledge/_inbox/discord/MY-DATA-PEAT/model-for-sale/` holds Dropbox links to
shared **"3DSKY FURNITURE 2024 / 2022"** collections. Those are redistributed
paid-library models, and `LICENSING.md`'s own rule applies — *"the personal-use
restriction travels with the file; sharing it does not launder the license."*
Not a sourcing route unless the owner holds his own 3dsky licence. Filed as an
ask rather than left in prose.

## WHAT THIS DR DOES NOT SETTLE

- Whether any free library holds a bed authored MADE at this bed's size.
- Whether Enscape has a headless/scripting API (asked; the answer describes
  ecosystems, not automation surfaces). ASK-025 still carries it.
- Every price and count above except the two marked SURVIVED.
