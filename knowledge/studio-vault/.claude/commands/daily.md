---
description: Generate today's daily note with active project status
---

User wants today's daily note.

## Steps

1. **Check** `70-Daily-Notes/` for today's file (`YYYY-MM-DD.md`)
   - If exists → open and show
   - If not → create new from template

2. **Scan** `10-Clients/` for active projects:
   - Files modified in last 14 days
   - For each: read `00-project-overview.md` → current stage + active items

3. **Fill** today's note:
   ```markdown
   # YYYY-MM-DD

   ## Active projects
   - [[project A]] — stage X — next: [action]
   - [[project B]] — stage Y — blocked on: [item]

   ## Today's plan
   (ask user)

   ## Meetings today
   (check meetings/ for today's date)
   ```

4. **Ask user**:
   - "วันนี้ focus อะไรเป็นหลัก?"
   - "มีอะไรที่เป็น blocker ตอนนี้?"

5. **Save** and open the file

## Style

Brief. Bullet-only. No fluff.
