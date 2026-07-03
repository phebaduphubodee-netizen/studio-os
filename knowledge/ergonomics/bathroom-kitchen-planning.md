# Bathroom & kitchen planning — ergonomic values & functional logic

REFERENCE tier. Distilled 2026-07-03 from NLM DR notebook `f61fded1` (see
`knowledge/_inbox/nlm-bath-kitchen-2026-07-03.md` for the verbatim answer + corpus).
NKBA / Neufert / Panero & Zelnik. **codes-th statutory floors outrank** these
comfort values where they overlap (ห้องน้ำ = ฉ.39; see `knowledge/codes-th/`).
Feeds the FUNCTION layer (`placement_logic.py` bathroom_logic rule) + future kitchen.

## Bathroom — the GS-05 functional logic (fixture ordering + wet/dry zoning)
Designer GS-05: "โถส้วม/อ่างล้างหน้า สลับตามการใช้บ่อย … แยกโซนเปียกแห้ง." Neufert best
practice, ordered from the entry door inward:
| zone | fixtures | placement |
|---|---|---|
| primary (most-used) | **basin / vanity** | **closest to the entry door** |
| intermediate (privacy) | **WC** | deeper / shielded, out of the direct sight line |
| deep (least-frequent, wet) | **shower, tub** | **deepest point** — the wet zone, at the back |

Wet/dry zoning: wet (shower/tub) grouped at the back, isolated from dry (basin/WC/
storage). → rule: basin is the nearest fixture to the door; no wet fixture is nearer
the door than the basin; the wet-zone centroid is deeper than the dry-zone centroid.

## Bathroom — fixture spacing / clearance (mm) [reference; clearance gate = suite_clearance / codes-th]
| pair / fixture | NKBA | code min | Neufert | P&Z |
|---|---|---|---|---|
| basin centreline ↔ WC/sidewall | 508 | 381 | 400 | 300 (edge→vanity) |
| WC centreline ↔ shower/tub | 457 | 381 | 400 | 300 (edge→entry) |
| basin ↔ basin (double) | 914 c/c | 762 | — | 102 edge min |
| clear floor — WC | 762 | 533 | 600 | 750–900 |
| clear floor — basin | 762 | 533 | 700 | 762×1219 |
| clear floor — shower | 762 | 610 | 900×900 | 900×900 |
| clear floor — tub | 762 | 533 | — | 600 |
| curbless shower slope | ≥20.8 mm/m (~2%) | | | |
| waterproofing height AFF | ≥1829 (or ≥76 above showerhead) | | | |
| GFCI within of basin | 914 | | | |

## Kitchen work-triangle (NKBA / Neufert / P&Z)
| quantity | value |
|---|---|
| each leg (sink–cooktop–fridge) | ≥ **1219**, ≤ **2743** mm (NKBA); Neufert 1200–2700 |
| total perimeter | ≤ **7925** mm (NKBA); Neufert 3600–6600 opt (max 8000); P&Z 3962–7925 |
| leg obstruction by island/cabinet | ≤ 305 mm |
| aisle — single cook | ≥ **1067** mm (NKBA) / Neufert 1060 / P&Z 1050–1200 |
| aisle — multi cook | ≥ **1219** mm (NKBA) / Neufert 1200 |
| general walkway (off triangle) | ≥ **914** mm (NKBA) / Neufert 900 / P&Z 1000 |

(No kitchen spec exists yet — kitchen values are reference for a future work-triangle rule.)
