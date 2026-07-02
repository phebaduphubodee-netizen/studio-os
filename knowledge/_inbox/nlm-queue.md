# NLM ask queue (lane-down fallback + batch material)

When the NLM lane is DOWN mid-run (auth expired / quota / network — see
CLAUDE.md "External research lane"), the run continues vault-only and appends
the unanswered question here. Re-ask after `notebooklm login` or the next day,
then clear the entry. Questions must already be privacy-clean (generic, no
client specifics) — the same rule as a live ask.

Format: `- [ ] <question> — <notebook id> — queued <date> — <why it came up>`

## Queue

(empty)
