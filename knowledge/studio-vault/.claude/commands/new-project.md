---
description: Scaffold a new client project folder from _TEMPLATE
---

User wants to create a new client project.

## Steps

1. **Ask for these inputs** (one at a time, in Thai):
   - ชื่อลูกค้า (เช่น "Khun Aom")
   - Property type (Condo / House / Townhome)
   - Location (one-word for folder)
   - Year (default: current year)

2. **Generate folder name**: `YYYY-FirstName-PropertyType-Location`
   Example: `2026-Khun-Aom-Condo-Sukhumvit`

3. **Copy** `10-Clients/_TEMPLATE/` → `10-Clients/[new-folder-name]/`

4. **Pre-fill** `00-project-overview.md`:
   - Client name
   - Property type, location
   - Today as start date
   - status: brief
   - stage: 1

5. **Create** today's meeting note if it doesn't exist:
   `meetings/YYYY-MM-DD-initial-meeting.md`

6. **Report back**:
   - Folder created path
   - Suggest: "พร้อมรับ brief แล้ว → ใช้ `/brief` ตอนคุณมี transcript"

## Tone

Quick, no hand-holding. User has done this before.
