---
description: Process a raw transcript or notes into a structured client brief
---

User wants to turn raw input (transcript, notes, voice memo text) into a structured client brief.

## Steps

1. **Identify the project**:
   - If a project folder is mentioned, use it
   - Otherwise ask: "ลูกค้าใหม่ใช่ไหม? ขอชื่อ + ประเภท property"
   - For new client: scaffold from `10-Clients/_TEMPLATE/` (see `/new-project`)

2. **Extract from input** and fill the structure in `01-brief.md`:
   - Household members (age, lifestyle clues)
   - Daily routine
   - Property details
   - Budget (target + ceiling)
   - Timeline
   - Must-have / nice-to-have / deal-breakers
   - Style direction (words used by client)
   - **Hidden needs** — things the client said indirectly
   - Decision-makers

3. **Mark uncertain items** with `[CONFIRM]` rather than guessing

4. **Generate follow-up questions** (5-7 things not yet covered)

5. **Output**:
   - Save filled brief to `10-Clients/[project-slug]/01-brief.md`
   - Show the follow-up questions in chat for user to ask client next meeting
   - Log this brief event in `04-decisions.md`

## Style

- Direct, no fluff
- Use original client wording in quotes where useful
- If transcript is in Thai, brief in Thai
- Always cite source: `Source: [[meetings/YYYY-MM-DD-...]]`
