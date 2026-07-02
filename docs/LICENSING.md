# LICENSING — furniture models & client deliverables (LOAD-BEARING)

Research wf_0246d7e9 (2026-06-30, with an adversarial license skeptic). The founder has
real money + liability exposure → these rules are binding, not advisory. **When in doubt,
do NOT ship the model.**

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
| **FurniMesh** | ✅ cleanest | Explicit "free to use in commercial projects"; the ONLY source legal to script-fetch. |
| **Your own original models** / **CC0** | ✅ | No restriction. |
| **BIMobject** (incl. Häfele on BIMobject) | ❌ personal-use only | EULA 4.4(b) personal/non-commercial; 4.7(f)(g) no transfer/incorporate-for-third-party. |
| **CADENAS / PARTcommunity / 3Dfindit** (the Häfele CAD route) | ❌ personal-use only | §8 "personal uses only … passing to third parties is not permitted". |
| **Häfele own portal** | ❌ until verified | EULA un-retrieved; "free of charge" ≠ a redistribution grant. Read it before relying. |
| **XSurface** | n/a (materials) | Thai MATERIAL library (laminates/tiles/panels) — a finish/spec tool, **never** a geometry source. |
| **HomePro** | facts only | Retail catalog; ToS forbids reuse of their images/spec text. The **dimensions** (uncopyrightable facts) are usable → re-model from measurements; never lift their images. |

## Automation
**Manual-download workflow by design.** Scripted/bulk fetch is independently ToS-banned on 3D
Warehouse, BIMobject, CADENAS (account ban + legal risk) — even where the model license is
permissive. **Exception: FurniMesh** may be fetched directly. At ~12 mapped kinds, hand-curation
is fine.

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
