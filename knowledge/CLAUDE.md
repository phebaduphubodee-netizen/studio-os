# knowledge/ — domain truth (loaded when working here)

- READ + CITE only. Every assertion drawn from here must carry its file path
  (e.g. `knowledge/studio-vault/00-Studio-Knowledge/pricing-formula.md`).
  No citation → the claim does not ship.
- Authority order (highest first): codes-th/ > client contract > studio
  standards (studio-vault/, brand-standards/) > general references. On
  conflict, the higher tier wins and the artifact says so.
- codes-th/ is the Authority tier: NEVER write there (hook-enforced).
  Content enters only via a reviewed PR with named legal sources
  (พ.ร.บ.ควบคุมอาคาร, กฎกระทรวง, ระเบียบนิติฯ) — summaries and DR reports are
  NOT sufficient sources for Authority values.
- New material goes to _inbox/ only; the ingestion flow (Phase 4 routine, or
  manual filing until then) moves it into place. Generation/render tasks never
  write anywhere under knowledge/.
- Retrieval: use `python3 scripts/vault_search.py "<query>"` for keyword/BM25
  search with path citations before falling back to manual grep/reads.
- studio-vault/ is the migrated v2.2 vault, structure preserved. Its old
  orchestration file is parked at studio-vault/_vault-CLAUDE-v2.2.md — treat as
  historical reference, NOT active instructions. Old slash commands live in
  studio-vault/.claude/commands/ as porting source for skills.
- Heavy reads (long PDFs in _inbox/) go to a subagent that returns a short
  structured summary with paths; do not stream whole PDFs into this context.
