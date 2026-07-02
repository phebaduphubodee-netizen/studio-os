---
description: Log a change order with impact estimate
---

User has identified a scope/cost/timeline change to log.

## Steps

1. **Identify project** (use active project)

2. **Gather inputs** (ask one focused question at a time if missing):
   - What changed? (specific — old → new)
   - Who requested? (client / designer / contractor / supplier)
   - Why?
   - What files / sections does it affect?

3. **Estimate impact** (use Cost Estimate Standard from CLAUDE.md):
   - Cost: ฿ — mark `[ESTIMATE]` or `[CONFIRMED]`
   - Time: +X days / no change
   - Risk added: brief description → also update `risks.md` if material
   - Confidence: high / medium / low

4. **Determine status**:
   - `[PENDING CLIENT]` (default for client-driven)
   - `[PENDING SUPPLIER]` (need supplier quote first)
   - `[ESTIMATE]` (need more data)
   - `[CONFIRM]` (need spec/quantity)
   - `[CONFIRMED]` (client already approved in writing — show evidence)

5. **Append to `change-orders.md`**:
   - Increment CO number
   - Fill all fields per template
   - Update summary table at top

6. **Update related files**:
   - If risk added → append to `risks.md`
   - If decision implied → DO NOT auto-add to `04-decisions.md` until `[CONFIRMED]`
   - Add reminder to `99-followup.md` if waiting

7. **DO NOT** silently update `06-boq.md` — change order stays separate until:
   - Status becomes `[CONFIRMED]` AND
   - User explicitly requests merge

8. **Output to chat**:
   - CO summary row
   - Impact estimate
   - What still needs confirmation
   - Next action (e.g., "send to client for approval", "request supplier quote")

## Style

- Single-row summary first, then detail
- Always flag the assumptions
- Make the cost/time impact unambiguous
