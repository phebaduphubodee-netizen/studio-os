# Thai retail mattress sizes — web reference (staged 2026-08-22)

REFERENCE tier. Retrieved 2026-08-22 by web search (generic question, no client
data). Why it exists: D-114 (2026-08-22) had to adopt the bed standard 1800x2000
as a DECLARED ASSUMPTION because `knowledge/ergonomics/` held only US sizes
(Panero & Zelnik) — the studio designs for the Thai market and its own knowledge
base could not name a Thai bed. This unit closes that gap with sourced values.

## Values (W x L, cm; brands vary ±1-2 cm on width, length 198-200)

| Thai size | typical W x L | range seen across sources |
|---|---|---|
| 3.5 ฟุต (single) | 107 x 198 | 105-107 wide |
| 5 ฟุต (queen) | 152 x 198 | 150-152 wide |
| 6 ฟุต (king) | 180 x 198 | 180-183 wide, some 200 long |

Nominal machine values adopted (inside every listed brand's range):
`th_single_3_5ft` 1070x1980 · `th_queen_5ft` 1520x1980 · `th_king_6ft` 1800x2000.
D-114's chosen 1800x2000 sits inside the 6-ft band — the assumption upgrades to a
sourced value with this unit.

## Sources (retrieved 2026-08-22)

- https://lunio.co.th/blog/ขนาดที่นอน-ความยาว/ (105x198 / 150x198 / 180x198)
- https://dunlopillo.co.th/th/news/how-to-choose-bed-size-n112.html
- https://sleephappy.co.th/en/blogs/lifestyle/mattress-size
- https://patexstore.com/content/mattress-sizes-thailand/ (107x198; American-vs-Thai companion page)
- https://zcoopysleep.com/blog/ขนาดที่นอน-3-5-ฟุต-5-ฟุต-6-ฟุต/ (183x198 king)

## Distillation (same commit)

- `knowledge/ergonomics/tv-viewing-and-furniture-dimensions.md` — §Thai-market
  mattress sizes appended (values gate a deliverable via dim_check, so the
  distillation is immediate per the _inbox law).
- `pipeline/scripts/ergonomics_ref.py` — `BED_SIZES_TH_MM` (machine copy), cited
  back to this unit.
