---
title: MY-DATA-PEAT — external-link manifest (UN-FETCHED payload)
source: discord / MY DATA PEAT
generated: 2026-07-03
tier: REFERENCE
status: LINKS-ONLY — none of the external content below has been downloaded
---

# External data behind the Discord ingest — accounting

The 2026-07-03 ingest pulled Discord **text + inline image/PDF attachments only**.
External cloud-storage links (Dropbox / Google Drive) were captured as text and
**never followed**. The real bulk of the design library lives behind these links
and is NOT in the repo. WebFetch cannot read the folder listings (JS-rendered);
the sandbox has no network egress (`curl` → HTTP 000) — pulling requires a
deliberate, un-sandboxed download step.

codes-th outranks anything distilled from this. All below is REFERENCE tier.

## Dropbox — 7 folders (model-for-sale, 3DSKY .max model packs)

Format `.max` (3ds Max native — pipeline is Blender/ComfyUI, needs conversion).
Likely multi-GB each. LOW near-term value; no consuming stage yet.

| thread | folder |
|---|---|
| 001_3DSKY-PROP-2024      | https://www.dropbox.com/scl/fo/suoew75g2f4jl35qqfgnl/h?rlkey=xu4p2gs85vpq6cyp4df6uqh0o |
| 002_3DSKY-PROP-2023      | https://www.dropbox.com/sh/97u1u03wtron0ai/AACkDAcmuNn0PyBz7NCadT6na |
| 003_3DSKY-PROP-2022      | https://www.dropbox.com/sh/qyx7lirzdvn4lzk/AAByHixffAXWbHBVS_vtZWAca |
| 004_3DSKY-FURNITURE-2024 | https://www.dropbox.com/sh/33im5lgn4x5hjlt/AABdFmy6aTKZ2knVwMph7zxta |
| 005_3DSKY-FURNITURE-2022 | https://www.dropbox.com/sh/jkqmrqxt1z08r4f/AADcYth6aKFnB1qCkP5orcfea |
| 006_3DSKY-LIGHTING-2024  | https://www.dropbox.com/scl/fo/l2zgkfmnqnb8kjb70e9gy/h?rlkey=z89ysfihu7rkm1c87pm7049gi |
| 007_3DSKY-TREE-2024      | https://www.dropbox.com/scl/fo/qqgs9pc24udihaii638ed/h?rlkey=esjz4sbx1ttp12p2ydt6nm2ra |

Whole-folder download: append `?dl=1` (zip). Size unknown — HEAD-probe before pulling.

## Google Drive — 6 folders + 2 files

HIGH value / feasible — real Thai manufacturer catalogues + photometric data;
feeds FF&E / BOM / lighting stages. Small (PDFs). Folders need `gdown`; single
files download via `uc?export=download&id=`.

| thread | type | target |
|---|---|---|
| catalogue/012_ระแนงสำเร็จรูป-(Wall) | folder | https://drive.google.com/drive/folders/1n0ySR8NFzQ4UIr8zDHOTQo1jWgS6i_uw |
| catalogue/016_TIPTOP | file (TIP-TOP Catalogue V3.pdf) | https://drive.google.com/file/d/1oVHjyvl9zTd5iYGMF8YY1D2rF5kfal8s |
| catalogue/017_WDC | folder | https://drive.google.com/drive/folders/1-RFvLFw-bFHxD4brfs79DLclJyfyPPHe |
| catalogue/018_FUTURTECH | folder | https://drive.google.com/drive/folders/1opNK8mfv_ghuC__Fd3yK9NxrG5nrahCv |
| catalogue/023_AELLA-HARDWARE | folder | https://drive.google.com/drive/folders/1i-OcOQGxaM3QdXSwItpgRmELTgkksEKV |
| ข้อมูลแบ่งปัน/001_Sketchup-แบ่ง-Model | file | https://drive.google.com/file/d/1gsf6xHJFTY_DotYFSql5gF2LPhinzKaU |
| ข้อมูลแบ่งปัน/002_ค่าแสง-IES | folder | https://drive.google.com/drive/folders/1OdKvl2v4U5ha4b36HRKOCxVIQP2Oof39 |
| ข้อมูลแบ่งปัน/012_รวมสูตรคำนวล-Excel | folder | https://drive.google.com/drive/folders/1GNZBgOwySfP9s3_kLOZ492q8lxupn44d |

## Other external hosts (not bulk stores)

autocad-tip / 3dmax-tip / maps / ข้อมูลแบ่งปัน also link to blogs, YouTube,
vendor sites (e.g. anmarbangkok patterns, blogspot CAD tips) — software how-to,
not asset libraries. Left as-is.

## FETCH STATUS — 2026-07-04 (via gdown; curl/Schannel blocked, Python net OK)

Fetched into `_external-fetched/` (342 MB, 110 files). NOT yet distilled into knowledge/.

| target | result |
|---|---|
| TIPTOP Catalogue V3.pdf | ✅ 48 MB PDF |
| catalogue/ระแนง (Wall/stone) | ✅ 6 catalogue PDFs incl. 121 MB pricelist + 84 MB Wallthailand |
| catalogue/WDC | ◑ 52 tile product JPGs (~complete; folder aborted on 1 straggler) |
| catalogue/FUTURTECH | ◑ 54 closet/hardware JPGs (~complete; aborted on 1) |
| catalogue/AELLA hardware | ✅ 14 catalogue PDFs (retry 2026-07-04 after cooldown) — distilled → materials/aella-hardware-th.md |
| sharing/IES photometrics | ✅ 30 .ies files (real BEGA/Kurt Versen/Lithonia/Halo) — mapped in lighting/ies-and-lighting-notes-discord.md §2a |
| sharing/Excel take-off | ◑ 1 of many (`รายการราคาค่าบริการ1.xls`); rest still hit the big-file confirm page |
| Dropbox ×7 (.max packs) | ⏸ deferred (not attempted) |
| Sketchup share (1.4 GB RAR) | ⏸ pulled then removed — asset library, not knowledge slice |

**Blocked (AELLA / IES / Excel):** gdown folder-mode can't clear Drive's virus-scan
confirm page for the large first file + we're rate-limited after many hits today.
Retry needs a quota cooldown (hours) OR a per-file `fuzzy=True` pull OR manual
browser download. Do NOT hammer Drive again immediately — it deepens the throttle.

## DISTILLED — 2026-07-04 ✅

The 7 fetched catalogue PDFs were distilled (workflow wf_7a1e709a, prices re-verified) into:
- `knowledge/materials/wall-cladding-and-decorative-mouldings-th.md` (product/dimension/price tables)
- `knowledge/studio-vault/40-Suppliers/discord-supplier-directory.md` (WALL, TIPTOP, WDC, AELLA entries)
Confirmed discoverable via `scripts/vault_search.py` (ranks #1–2 for WPC/AKUWALL/PU-moulding queries) →
now in the FF&E/concept/knowledge-manager retrieval path = USED, not just stored.

PRIVACY: FUTURTECH folder held a named client's photos (คุณเมย์ขอนแก่น) → moved whole folder to
`_private/discord/` (gitignored), out of knowledge/.

## Still open

1. **Excel take-off folder** — only 1 of several `.xls` came down; the rest hit Drive's big-file
   confirm page. Low priority (service rate cards / take-off formulas) — retry per-file or browser-pull.
2. **Dropbox .max packs + Sketchup RAR** — DEFER to a real asset-ingestion stage
   (format-mismatched vs Blender; multi-GB into OneDrive).
