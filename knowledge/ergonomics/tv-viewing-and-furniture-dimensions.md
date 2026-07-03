# TV viewing geometry, furniture dimensions & seating — ergonomic values

REFERENCE tier. Distilled 2026-07-03 from NLM DR notebook `5de4bb36` (see
`knowledge/_inbox/nlm-ergonomics-2026-07-03.md` for the verbatim answer, source
corpus, and marker caveat). These are ergonomic/comfort values (SMPTE, THX,
Panero & Zelnik, Neufert, NKBA, ANSI/BIFMA) — **codes-th statutory floors always
outrank** where they overlap. Complements `residential-clearances.md` (which holds
sofa-coffee gap, conversation distance, WC/basin/shower clearances, bed circulation).

Purpose: feed the deterministic FUNCTION layer (`pipeline/scripts/placement_logic.py`),
replacing hardcoded heuristics with cited values. All metric (mm / deg).

## TV / flat-screen viewing (SMPTE, THX)
| quantity | value | note |
|---|---|---|
| viewing distance | diagonal × **1.6** (SMPTE 30° FOV) · × **1.4** (THX 36°) · × **1.2** (THX 40° immersive) | distance = f(screen size); the studio spec has no screen size → use as a comfort BAND, not an exact gate |
| example (65 in = 1651 mm) | 2642 / 2311 / 1981 mm | SMPTE / THX36 / THX40 |
| mount height (center AFF), living-room seated | **1016–1118 mm** | relaxed eye level over a sofa |
| mount height (center AFF), bedroom reclined | **≈ 1270 mm**, tilt down **10–15°** | higher for a lying viewer |
| vertical viewing angle | **≤ 15°** off seated eye level (absolute max **35°**) | above this = neck strain (the GS-24 "เงยคอดู" failure) |
| horizontal off-axis | **≤ 40°** (THX) / 45° (cinema) | beyond = colour shift / distortion |

Rule use: a bedroom/living TV band of roughly **1.5–3.0 m** centre-to-viewer covers a
typical 50–75 in screen across THX40→SMPTE; treat outside that as WARN, and the
vertical-angle ≤35° absolute as the hard "not over/above the head" backstop.

## Standard furniture dimensions
| piece | dimension | value |
|---|---|---|
| bed — Twin/Single | mattress W×L | **991 × 1905 mm** |
| bed — Double/Full | | **1372 × 1905 mm** |
| bed — Queen | | **1524 × 2032 mm** |
| bed — Eastern King | | **1930 × 2032 mm** |
| seat height (chair/sofa) | floor→seat | **400–450 mm** |
| sofa seat depth | | **400–550 mm** (lounge/easy 500–660) |
| dining / desk table | height | **720–760 mm** |
| coffee table | height | **300–460 mm** |
| side / end table | height | **380–480 mm** |
| wardrobe | depth | **600 mm** (min 500–550 w/ sliding) |
| dresser / chest | depth | **457–500 mm** |

Rule use (furniture scale/height): a spec `bed` footprint should match a standard
mattress ±~50 mm; a `coffee_table` h in 300–460, `dining_table`/`desk` in 720–760,
`side_table` in 380–480; a `wardrobe` depth ≈ 500–600. Outside range → WARN
(oversize/wrong-scale — the GS-02/06 "สัดส่วนไม่ได้ / เฟอร์ฯใหญ่ไป" family). Overall
chair/sofa `h` is the backrest, NOT the seat, so seat-height 400–450 is NOT checkable
from the current spec (would need a seat_h field).

## Seating arrangement
| quantity | value |
|---|---|
| sofa → coffee-table | min 300 mm · **460 mm** comfort · **920 mm** if a person passes |
| conversation angle | **180°** face-to-face or **90°** L-shape |
| min gap between independent seats | **100 mm** |
| face-to-face conversation distance | 2134–2845 mm (P&Z, from `residential-clearances.md`) |

## Circulation & reach (complements residential-clearances.md)
| quantity | value |
|---|---|
| walkway — 1 person (min) | **600 mm** (Neufert) |
| walkway — comfortable | **800–900 mm** |
| walkway — two-person | **1200–1500 mm** |
| bed under-drawer activity zone | **1168–1575 mm**; +762 mm if circulation bypasses |
| interior door leaf width | **800–900 mm** |
| bathroom frequent-use storage height | **381–1219 mm** AFF |

## Known gaps (follow-up DR fired 2026-07-03)
Bathroom fixture-to-fixture spacing (basin/shower/tub), wet/dry zoning, fixture order
by use frequency (GS-05); kitchen work-triangle metric limits.
