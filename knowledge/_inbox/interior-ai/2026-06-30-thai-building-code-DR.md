# Thai building-code requirements — DR (2026-06-30)

Cited web Deep Research (workflow wf_4a006356) to replace the DRAFT US (Panero & Zelnik)
clearance rules with locally-correct Thai numbers. Primary source is **กฎกระทรวง ฉบับที่ 55
พ.ศ. 2543** under **พ.ร.บ. ควบคุมอาคาร พ.ศ. 2522**. Treat every number as UNVERIFIED-until-
cross-checked against the actual ratchakitcha text before it gates a client deliverable
(law: verify citations); confidence tags below are the DR's own.

## FIRM (encode into metric clearance rules)
| Requirement | Value | Source |
|---|---|---|
| Habitable-room ceiling height (min) | **2.60 m** | กฎกระทรวง 55 §21 |
| Ground-floor ceiling (multi-unit) | 3.5 m | §21 |
| Upper-floor ceiling (multi-unit) | 3.0 m | §21 |
| Bathroom/toilet ceiling height (min) | **2.00 m** | กฎกระทรวง 55 |
| Bedroom floor area (min) | **8.0 m²** | §20 |
| Bedroom narrowest width (min) | **2.5 m** | §20 |
| Dwelling-unit total area (min) | 20.0 m² | §19 |
| Corridor width — single house | **1.0 m** | พ.ร.บ.ควบคุมอาคาร §22 / กฎกระทรวง 55 |
| Corridor width — apartment/dorm | 1.5 m | §22 |
| Dwelling / exit door width | **0.80 m** | กฎกระทรวง 55 Art.31 |
| Exit door height | **1.90 m** | กฎกระทรวง 55 |
| Stair width (residential, net) | 0.80 m | Art.23 |
| Stair riser (max) / tread (min) | 0.20 m / 0.22 m | Art.23 |
| Stair headroom | 1.90 m | Art.23 |
| Ventilation opening (exterior) | 1.40 m² per floor | กฎกระทรวง 55 |
| Thai bed — 5 ft / 6 ft | 1.5×2.0 m / 1.8×2.0 m | Thai furniture industry |

## LEGAL — professional licensing (LOAD-BEARING for the business model)
- Interior design (**สถาปัตยกรรมภายในและมัณฑนศิลป์**) IS a **controlled profession** — Architects Act **พ.ร.บ.สถาปนิก พ.ศ. 2543 §4** (สภาสถาปนิก). **FIRM.**
- **Permit-required** interior drawings must carry a licensed **architect's seal** (Building Control Act §23). **FIRM.**
- Whether purely non-structural / decorative FF&E-only interior work needs a seal = **UNVERIFIED** (not in public English sources).
- ⚠️ Implication vs the US assumption ("unstamped interior แบบ is sellable"): in Thailand this is CONSTRAINED. → reinforces the model **friend = licensed practitioner who signs / provides professional cover · founder+AI = back-office production**. Confirm the FF&E-only carve-out with the friend / สภาสถาปนิก.

## UNCERTAIN / UNVERIFIED (do NOT gate on these — re-check)
- Window/natural-light opening = ~10% of floor area (no §cited).
- Residential bathroom min area; fixture clearances (DR fell back to the ASEAN **public-toilet** standard — 0.90 m cubicle width, 1.52 m depth, 0.90 m front clearance — NOT confirmed for residential).
- Bed→wardrobe 0.50 m, wardrobe depth 0.60 m, door clearances 0.70–0.90 m = international design norms, not Thai code.

## Top-3 changes vs the US DRAFT rules
1. Ceiling min **2.60 m** (not 90"/2.29 m) — this suite's 2.8 m passes.
2. Door **0.80×1.90 m** and corridor **1.0 m** are the Thai residential minimums.
3. Bedroom **≥ 8 m² and ≥ 2.5 m wide** is a hard code floor to check.

Full run: `tasks/w8ijcsrta.output` (workflow wf_4a006356).
