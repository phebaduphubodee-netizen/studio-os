# clients/ — PRIVACY-SENSITIVE (loaded when working here)

- .claude/rules/client-privacy.md is law here: no client names, addresses,
  floor plans, or budgets in web searches, external APIs, or any tool call
  that leaves this machine. Anonymize before any outbound use.
- Layout: clients/<client-id>/profile.md (curated, conflict-resolved truths)
  + episodes/*.md (append-only, dated event log). Client IDs are C-NNN;
  artifacts reference the ID, never the real name.
- profile.md edits: latest-wins with provenance ("changed 2026-05-14, see
  episode E-041"). Never silently delete a preference — supersede it.
- Memory never overrides Authority: a remembered client wish that violates
  codes-th/ values still fails the gate; say so in the artifact.
- Episodes record decisions, approvals, rejections, and the exact settings
  that worked (seeds, weights) — they are the studio's compounding memory.
- Writes here are ask-tier by permission config; expect a prompt.
