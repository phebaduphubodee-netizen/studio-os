# codes-th/ — Thai Building-Law Authority Tier

**This directory outranks every other knowledge source** (CLAUDE.md source-of-truth
order). Every value here carries its statute citation (ฉบับ + ข้อ) and the source
PDF page. No value may be asserted downstream without one.

## Source register
| File here | Statute | Consolidated source (in `knowledge/_inbox/codes-th-sources/`) | Gazette |
|---|---|---|---|
| mr55-residential-dimensions.md | กฎกระทรวง ฉ.55 (พ.ศ. 2543) แก้ไขถึง ฉ.68 (พ.ศ. 2563) | `mr43-55-upd68.pdf` (ASA law library) | รก. 117/75ก, 7 ส.ค. 2543 |
| mr39-fire-sanitation-ventilation.md | กฎกระทรวง ฉ.39 (พ.ศ. 2537) แก้ไขถึง ฉ.63 (พ.ศ. 2551) | `mr37-39-upd63.pdf` (ASA law library) | รก. 111/23ก, 13 มิ.ย. 2537 |
| cba-act-2522-overview.md | พ.ร.บ.ควบคุมอาคาร พ.ศ. 2522 (ฉบับปรับปรุง) | `cba22-upd60.pdf` (ASA law library) | รก. 96/80, 14 พ.ค. 2522 |

## Rules
1. **PR-only.** This directory is hook-protected; content changes arrive only via a
   reviewed pull request with the source PDF staged in `_inbox/codes-th-sources/`.
2. **Scope note.** Extraction focuses on residential work (condo / house / townhome).
   Factory, warehouse, and signage clauses are intentionally summarized or omitted —
   read the source PDF when those come into scope.
3. **Local ordinances outrank nothing here but ADD constraints** — Bangkok work must
   also check ข้อบัญญัติ กทม. (ควบคุมอาคาร 2544), not yet ingested. Flag as a gap when
   relevant.
4. **Not legal advice.** Design reference only; the architect-of-record verifies
   compliance at permit time. Check for amendments after 2563/2551 before relying on
   edge-case values.
