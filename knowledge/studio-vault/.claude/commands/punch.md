---
description: Compile punch list across all site reports for a project
---

User wants consolidated punch list.

## Steps

1. **Identify project**

2. **Read** all files in `08-site-reports/` for that project

3. **Extract** all 🔴 (critical) and 🟡 (minor) findings

4. **Deduplicate** — same issue mentioned multiple times = 1 entry

5. **Update** `09-punch-list.md`:
   - New items appended with date found
   - Existing items: update status if reports show progress
   - Move "verified" items to "Verified" section

6. **Generate stats**:
   - Total / Open / In-progress / Verified
   - % complete
   - Items aging > 14 days (red flag)

7. **Output to chat**:
   - Critical items still open
   - Aging items
   - Suggest next action

## Style

Group by zone. Order: critical > aging > recent.
