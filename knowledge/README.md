# Knowledge Layer — Migration from studio-vault v2.2 (Phase 0 → M1.1)
1. COPY your studio-vault content into these folders (do not restructure yet):
   templates/checklists → keep in vault paths; codes & regulations → codes-th/;
   ergonomics & clearances → ergonomics/; material specs → materials/;
   lighting specs → lighting/; style references → styles/;
   CSI/OmniClass notes → classifications/; developer/hotel standards → brand-standards/.
2. Your vault's Source-and-Truth Hierarchy becomes the Authority tier:
   codes-th/ outranks everything; conflicts resolve per CLAUDE.md order.
3. New documents go to _inbox/ — the Phase 4 ingestion routine will chunk,
   index, and open a PR. Until then, file manually.
4. Indexing (hybrid retrieval + rerank) is Phase 1 work — content first, index second.
