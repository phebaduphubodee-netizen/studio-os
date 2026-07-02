---
description: Compare site photo against render or spec, generate findings
---

User has uploaded site photo(s) and wants comparison.

## Steps

1. **Identify image type first** (Photo Routing rule from CLAUDE.md):
   - Site photo → continue with QC flow below
   - Reference / render / material / drawing → route differently per CLAUDE.md Photo Routing

2. **For site photos** — identify project and area in the photo

3. **Find reference** (using Source Hierarchy):
   - Original render → check `04-decisions.md` or project folder
   - Spec → `05-furniture-and-materials.md`
   - Drawing → ask for DWG/PDF path if needed
   - If reference unavailable → state limitation, ask user to provide

4. **Compare** systematically:
   - Material match (color, finish, texture)
   - Dimensions / proportions (if measurable)
   - Lighting position
   - Built-in details (gap, alignment, hardware)
   - Finishing quality (grout, paint edge, joint)

5. **Categorize findings**:
   - 🟢 Match — looks good
   - 🟡 Minor deviation — note for record
   - 🔴 Off-spec — needs fix

6. **Output**:
   - Markdown report in chat
   - For 🔴 items → propose punch list entries with format:

     | Issue | Zone | Reference | Priority | Confidence |
     |-------|------|-----------|----------|------------|

7. **Save** findings to today's site report:
   `08-site-reports/YYYY-MM-DD-visit.md`
   (Create if doesn't exist, append if exists)

8. **If discrepancy is significant** → flag for Change Order check:
   - "This deviation may need a CO if it reflects approved scope change"
   - Suggest user check `change-orders.md`

## Style

- Specific, not vague ("กระเบื้องแถวที่ 3 จากผนัง slope ลง 5mm" not "พื้นไม่เรียบ")
- Cite reference: "expected `[material spec from 05-...]`"
- Confidence on visual judgment: "high / medium / low — แนะนำให้วัดยืนยัน"
- If image quality insufficient → say so, ask for better photo
