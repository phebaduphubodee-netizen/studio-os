---
description: Generate BOQ from material/furniture spec + rate card
---

User wants to generate BOQ for an active project.

## Steps

1. **Identify project**: ask if not in context, or use active project

2. **Load inputs** following Source Hierarchy from CLAUDE.md:
   - Signed quotation (if exists)
   - `04-decisions.md` — confirmed material/furniture decisions
   - `05-furniture-and-materials.md` — selected items
   - `06-boq.md` previous version (if exists)
   - `[[00-Studio-Knowledge/rate-card]]` — pricing
   - `[[00-Studio-Knowledge/pricing-formula]]` — formula
   - Drawing list (if available — for quantity takeoff)
   - **DO NOT** merge in items from `change-orders.md` unless explicitly `[CONFIRMED]` and `[MERGED]`

3. **Generate BOQ** using this REQUIRED column schema:

   | Area | Item | Specification | Quantity | Unit | Material cost | Labor cost | Contingency | Total | Source | Status |

   - **Status** must be one of: `[CONFIRMED]` / `[ESTIMATE]` / `[CONFIRM]`
   - **Source** must be one of: `rate-card` / `supplier-quote` / `past-project` / `web` / `[ASSUMPTION]`
   - Group rows by 15 sections (demolition → cleaning) with section subtotals
   - Each cost cell: numeric, with `฿` and thousand separator

4. **Mark uncertainties strictly**:
   - Items missing spec: `[CONFIRM SPEC]` in spec column, `[CONFIRM]` in status
   - Items missing quantity: `[NEED TAKEOFF]` in qty column, `[CONFIRM]` in status
   - Items missing supplier price: leave cost blank, source = `[ASSUMPTION]`, status = `[CONFIRM]`
   - **DO NOT estimate without a documented basis** — flag instead

5. **Save** to `06-boq.md`, increment version in YAML frontmatter

6. **Output summary** in chat:
   - Grand total
   - Comparison vs budget (% over / under)
   - Top 3 items by cost
   - List of `[CONFIRM]` items to resolve, sorted by potential impact
   - List of `[ESTIMATE]` items with confidence flags

## Confidence reporting

For the BOQ as a whole, output:
- **Confidence**: high / medium / low
- **Reason for confidence level**: what % of line items are `[CONFIRMED]` vs `[ESTIMATE]` vs `[CONFIRM]`

## Style

- Tables in markdown
- Numbers always with thousand separator
- Currency: ฿
- Flag anything > 20% of total as "key item"
- Never blend material + labor + contingency
