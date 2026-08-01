# NLM ask queue (lane-down fallback + batch material)

When the NLM lane is DOWN mid-run (auth expired / quota / network — see
CLAUDE.md "External research lane"), the run continues vault-only and appends
the unanswered question here. Re-ask after `notebooklm login` or the next day,
then clear the entry. Questions must already be privacy-clean (generic, no
client specifics) — the same rule as a live ask.

Format: `- [ ] <question> — <notebook id> — queued <date> — <why it came up>`

## Queue

(empty)

- 2026-08-01 **AUDIT GAP, not a queued question** — `scripts/inbox_audit.py`
  `classify()` whitelists `knowledge/_inbox/nlm-design-systems/` by name, but
  CLAUDE.md prescribes `_inbox/nlm-<topic>/` generally. Every DR staged by the
  documented process therefore lands in UNCLASSIFIED + PROVENANCE-ORPHAN:
  nlm-backlit-stone, nlm-cloth-closedtube, nlm-process-rules, nlm-veneer-figure
  (4 units, 8 of the audit's 11 integrity failures). The staging is correct and
  the CLASSIFIER is behind the convention. NOT FIXED HERE: inbox_audit.py is
  uncommitted-modified by a parallel session and belongs to that lane.
