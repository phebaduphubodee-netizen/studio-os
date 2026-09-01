# Reader scores — blind sheet-read experiment (wf_031bc1de-f6b)

Scored 2026-08-31 against `ANSWER-KEY.json` (pre-registered). Bands: **EXACT** ≤5 mm ·
**GOOD** ≤30 mm · **CLASS** ≤100 mm · **WRONG** >100 mm · **MISSING** = not clearly stated.
Source: 6 `type:result` lines in `wf_031bc1de-f6b/journal.jsonl`; arm/reader identity from each
agent transcript's spawn prompt (bundle path + "Independent read #N").

Extraction rules applied (mechanical, not generous):
- **N3**: readers gave two BF09-1 leg depths → the FIRST-stated leg was extracted (B3's east leg 600 would have been EXACT; scored 591 GOOD).
- **N11**: the reader's `bed.ew_mm` field verbatim; prose alternates (A3's "2002 to panel contact") not credited.
- **N15**: the gap row's `mm` field; A3's row says `mm:30` (face-to-face) with "49 centreline" only in prose → scored 30.
- **N8**: B1 never states a BF11-back-to-wall value → MISSING.

## Numeric rows (value / |Δ| mm / band)

| Row | Truth | A-raw 1 | A-raw 2 | A-raw 3 | B-rec 1 | B-rec 2 | B-rec 3 |
|---|---|---|---|---|---|---|---|
| N1 bf09_2 length | 1498.1 | 1494 / 4.1 / **EXACT** | 1499 / 0.9 / **EXACT** | 1513 / 14.9 / GOOD | 1498 / 0.1 / **EXACT** | 1499 / 0.9 / **EXACT** | 1502 / 3.9 / **EXACT** |
| N2 bf10 north face | 2497.9 | 2487 / 10.9 / GOOD | 2504 / 6.1 / GOOD | 2512 / 14.1 / GOOD | 2502 / 4.1 / **EXACT** | 2501 / 3.1 / **EXACT** | 2503 / 5.1 / GOOD |
| N3 wardrobe leg depth | 599.9 | 598 / 1.9 / **EXACT** | 597 / 2.9 / **EXACT** | 594 / 5.9 / GOOD | 599 / 0.9 / **EXACT** | 599 / 0.9 / **EXACT** | 591 / 8.9 / GOOD |
| N4 party wall thickness | 101.6 | 100 / 1.6 / **EXACT** | 129 / 27.4 / GOOD | 100 / 1.6 / **EXACT** | 144 / 42.4 / CLASS | 108 / 6.4 / GOOD | 117 / 15.4 / GOOD |
| N5 sliding opening | 898.2 | 847 / 51.2 / CLASS | 843 / 55.2 / CLASS | 875 / 23.2 / GOOD | 881 / 17.2 / GOOD | 889 / 9.2 / GOOD | 882 / 16.2 / GOOD |
| N6 bf11 length | 3199.4 | 3187 / 12.4 / GOOD | 3201 / 1.6 / **EXACT** | 3217 / 17.6 / GOOD | 3200 / 0.6 / **EXACT** | 3199 / 0.4 / **EXACT** | 3212 / 12.6 / GOOD |
| N7 bf11 depth | 498.3 | 497 / 1.3 / **EXACT** | 500 / 1.7 / **EXACT** | 500 / 1.7 / **EXACT** | 497 / 1.3 / **EXACT** | 498 / 0.3 / **EXACT** | 500 / 1.7 / **EXACT** |
| N8 bf11 gap to wall | 250.8 | 250 / 0.8 / **EXACT** | 241 / 9.8 / GOOD | 240 / 10.8 / GOOD | — / — / MISSING | 207 / 43.8 / CLASS | 229 / 21.8 / GOOD |
| N9 bookshelf length | 1799.7 | 1800 / 0.3 / **EXACT** | 1801 / 1.3 / **EXACT** | 1801 / 1.3 / **EXACT** | 1802 / 2.3 / **EXACT** | 1809 / 9.3 / GOOD | 1817 / 17.3 / GOOD |
| N10 bookshelf depth | 599.9 | 599 / 0.9 / **EXACT** | 601 / 1.1 / **EXACT** | 599 / 0.9 / **EXACT** | 601 / 1.1 / **EXACT** | 601 / 1.1 / **EXACT** | 600 / 0.1 / **EXACT** |
| N11 bed E-W | 1999.6 | 2000 / 0.4 / **EXACT** | 1941 / 58.6 / CLASS | 1941 / 58.6 / CLASS | 1940 / 59.6 / CLASS | 1942 / 57.6 / CLASS | 1941 / 58.6 / CLASS |
| N12 bed N-S | 2148.8 | 2149 / 0.2 / **EXACT** | 2151 / 2.2 / **EXACT** | 2151 / 2.2 / **EXACT** | 2152 / 3.2 / **EXACT** | 2149 / 0.2 / **EXACT** | 2153 / 4.2 / **EXACT** |
| N13 bench E-W | 498.3 | 484 / 14.3 / GOOD | 499 / 0.7 / **EXACT** | 499 / 0.7 / **EXACT** | 499 / 0.7 / **EXACT** | 499 / 0.7 / **EXACT** | 498 / 0.3 / **EXACT** |
| N14 bench N-S | 999.8 | 998 / 1.8 / **EXACT** | 1002 / 2.2 / **EXACT** | 1002 / 2.2 / **EXACT** | 1002 / 2.2 / **EXACT** | 1002 / 2.2 / **EXACT** | 1000 / 0.2 / **EXACT** |
| N15 bench-bed gap | 50.8 | 53 / 2.2 / **EXACT** | 49 / 1.8 / **EXACT** | 30 / 20.8 / GOOD | 49 / 1.8 / **EXACT** | 49 / 1.8 / **EXACT** | 49 / 1.8 / **EXACT** |
| **Bands E/G/C/W/M** | | **11/3/1/0/0** | **10/3/2/0/0** | **7/7/1/0/0** | **11/1/2/0/1** | **10/3/2/0/0** | **7/7/1/0/0** |

## Categorical rows

| Row | A-raw 1 | A-raw 2 | A-raw 3 | B-rec 1 | B-rec 2 | B-rec 3 |
|---|---|---|---|---|---|---|
| C1 BF11 600-vs-~500 caught + which to trust | YES | YES | YES | YES | YES | YES |
| C2 same class on BF09-2 | YES | YES | YES | YES | YES | YES |
| C3 bed head EAST with ink evidence | YES | YES | YES | YES | YES | YES |
| C4 bed label read as feet, axes mapped | YES | YES | YES | YES | YES | YES |
| C5 chain-sum check with printed totals | YES | YES | YES | YES* | **NO** | YES* |
| C6 declared unmeasurables, not typed | YES | YES | YES | YES | YES | YES |
| C7 contamination tells | none | none | none | none | none | none |

\* Qualified: the recolor crops carried no chain numerals; B1 assumed the nominal 2850+2950+700=6500 and
checked the drawn total (6502, +2 mm); B3 measured intervals summing to 6500 but declared parts-vs-printed
uncheckable. B2 declared the mm chains "NOT present inside these crops" and ran only label-vs-ink sum checks → NO.
All six trusted the DRAWN depth for placement and flagged the label (C1/C2). All six cited pillow band,
nightstand pair, duvet fold and the BF14 panel as ink evidence for EAST (C3).

## Arm summary

| | A-raw (3 readers, 45 rows) | B-recolor (3 readers, 45 rows) |
|---|---|---|
| EXACT / GOOD / CLASS / WRONG / MISSING | 28 / 13 / 4 / 0 / 0 | 28 / 11 / 5 / 0 / 1 |
| Median abs delta (non-missing) | 2.2 mm | 2.25 mm |
| C1 / C2 / C3 / C4 caught | 3/3 each | 3/3 each |
| C5 chain-sum | 3/3 | 2/3 |
| C6 unmeasurables declared | 3/3 | 3/3 |
| C7 contamination | 0 | 0 |

**Arm comparison.** The arms are statistically indistinguishable on accuracy — 28 EXACT rows each,
medians 2.2 vs 2.25 mm — and both went 6/6 on every trap the experiment was actually about: both
label-vs-drawn depth discrepancies caught with a trust verdict, bed head EAST from ink, the feet
label mapped to the right axes, heights declared rather than typed, zero contamination. The real
arm difference is upstream of the readers: all three RECOLOR readers report the printed chain
numerals (2850/2950/700/5500/5100) as absent from their crops, where all three RAW readers quote
them — so B calibrated from BF labels, the 3.05 dim and cross-crop stroke transfer, which cost the
arm its chain-sum rung (B2's NO) and its one MISSING row but, notably, no accuracy. Recolor hurt
exactly one measurement class: party-wall thickness (A 100/100/129 with two EXACT; B 108/117/144
with none — colour-separated finish lines absorbed into the wall), while B beat A cleanly on the
sliding opening (all GOOD 881–889 vs A's two CLASS 843/847). N11 is a shared convention failure,
not an arm effect: 5 of 6 readers committed the bed frame rectangle (~1941) where the key's 1999.6
is head-to-foot to the panel; A-raw 1 alone matched the key's convention.

## Notable single-reader results

1. **A-raw 1 (ad341cbe)** — best card: 11 EXACT, 0 MISSING, and the ONLY reader whose bed E-W
   (2000) matched the key's head-to-foot convention; the other five all sat CLASS on the frame stroke.
2. **B-recolor 3 (acb9e1b7)** — only reader to flag BF13 as unbuildable (drawn 4100 overlaps the
   wall piers ~100 mm at both ends; clear bay 3894) and documented two self-corrections of its own
   misreads; paid for the designer-grade audit with the most GOOD-band drift (7 GOOD, 591 on N3).
3. **B-recolor 1 (a6f76530)** — claimed a programmatic enumeration guaranteeing "no printed number
   in the crops was missed", yet holds the experiment's only MISSING row (N8, BF11 standoff never
   stated) and its worst wall reading (144 mm, CLASS).
