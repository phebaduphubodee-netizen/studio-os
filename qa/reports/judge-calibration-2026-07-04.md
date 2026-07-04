# Judge calibration — 2026-07-04 (M3.2, blueprint §9.4)
Golden set: 26 designer-labeled images. Machine = mean over stored rolls (gemini-2.5-flash rubric). Pass bound 4.0 (thresholds client_qa).

| metric | value | bound | status |
|---|---|---|---|
| Spearman rho (ranking) | 0.428 | >= 0.8 | FAIL |
| Cohen's kappa (SHIP/REWORK) | 0.000 | >= 0.8 | FAIL |

**M3.2 acceptance: FAIL** (an uncalibrated judge is a broken test, not a lenient one — do not gate production on it)

| id | source | judge mean (n) | designer | Δ |
|---|---|---|---|---|
| GS-18 | room_living_condo_eye_hybrid_v004pro | 4.75 (2) | 1.5 REWORK | 3.25 |
| GS-11 | room_bedroom_suite_eye_hybrid_v003 | 5.00 (1) | 2.0 REWORK | 3.00 |
| GS-21 | room_living_hybrid | 4.00 (1) | 1.0 REWORK | 3.00 |
| GS-17 | room_bedroom_suite_eye_hybrid_prj002_v01 | 4.75 (2) | 2.0 REWORK | 2.75 |
| GS-05 | room_bedroom_suite_hybrid | 3.00 (1) | 0.5 REWORK | 2.50 |
| GS-10 | room_living_condo_eye_hybrid | 4.00 (1) | 1.5 REWORK | 2.50 |
| GS-09 | room_bedroom_suite_eye_hybrid_clayfix2_pro | 4.75 (2) | 2.5 REWORK | 2.25 |
| GS-06 | room_living_condo_eye_hybrid_v004 | 4.00 (1) | 2.0 REWORK | 2.00 |
| GS-08 | room_bedroom_suite_eye_hybrid_v004pro | 4.50 (1) | 2.5 REWORK | 2.00 |
| GS-12 | room_living_condo_eye_hybrid_oldclay_pro | 3.00 (2) | 1.0 REWORK | 2.00 |
| GS-14 | room_bedroom_suite_eye_hybrid_v005 | 4.00 (1) | 2.0 REWORK | 2.00 |
| GS-23 | room_bedroom_suite_eye_hybrid_v004 | 4.50 (1) | 2.5 REWORK | 2.00 |
| GS-24 | room_bedroom_suite_eye_hybrid_v005pro | 4.00 (1) | 2.0 REWORK | 2.00 |
| GS-01 | room_bedroom_suite_eye_hybrid | 2.50 (1) | 1.0 REWORK | 1.50 |
| GS-02 | room_living_hybrid_v001 | 2.00 (1) | 0.5 REWORK | 1.50 |
| GS-03 | room_living_condo_eye_hybrid_v005 | 3.00 (1) | 1.5 REWORK | 1.50 |
| GS-16 | room_bedroom_suite_eye_hybrid_clayfix_pro | 4.00 (3) | 2.5 REWORK | 1.50 |
| GS-19 | room_living_hybrid_v003 | 3.00 (1) | 1.5 REWORK | 1.50 |
| GS-20 | room_living_condo_eye_hybrid_clayfix2_pro | 3.50 (2) | 2.0 REWORK | 1.50 |
| GS-25 | room_bedroom_suite_eye_hybrid_v004b | 4.00 (1) | 2.5 REWORK | 1.50 |
| GS-04 | room_living | 1.00 (1) | 0.0 REWORK | 1.00 |
| GS-07 | room_living_condo_eye_hybrid_clayfix_pro | 3.50 (2) | 2.5 REWORK | 1.00 |
| GS-15 | room_living_hybrid_v002 | 3.50 (1) | 2.5 REWORK | 1.00 |
| GS-22 | room_bedroom_suite | 1.00 (1) | 0.0 REWORK | 1.00 |
| GS-26 | room_living_condo_eye_hybrid_v004b | 2.50 (1) | 3.0 REWORK | 0.50 |
| GS-13 | room_living_hybrid_v003b | 3.00 (1) | 3.0 REWORK | 0.00 |
