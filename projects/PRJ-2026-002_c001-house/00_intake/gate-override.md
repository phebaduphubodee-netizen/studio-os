# Stage 00 gate — HUMAN OVERRIDE record · 2026-07-02

Owner directive (chat, 2026-07-02, verbatim): "ผมไม่มีข้อมูลพวกนั้น ลงเดินต่อแบบเป็น
best case ให้มันสวยที่สุดเท่าที่เราจะทำได้ไปก่อน (เพราะงานนี้ยังเป็นแค่งานตัวอย่าง)"

Ruling: brief.json is CONFIRMED as-is; the three ⭐ gaps are answered by studio
best-case assumptions; project status = SHOWCASE / sample work, not a client
deliverable. This override satisfies the Stage-00 human gate and stands as the
standing sign-off for downstream human-gate checkpoints THIS RUN ONLY, up to but
NOT including Stage-05 per-image approval (contract keeps that human).

## Best-case assumptions adopted (each must be restated where used)
- A1 WINDOWS: undocumented in CAD (inventory gap 1). Assume glazing on the master
  bay terrace wall (the 700 mm dashed strip = facade): full-width sliding door /
  window band — the daylighting the Gate-0 layout and v004 prompt already assume.
  No other openings invented on shared/interior walls.
- A2 SUITE SCOPE: master suite = bedroom band + ensuite + WIC per the Gate-0-proven
  spec `pipeline/scripts/specs/bedroom_suite.json` (PASS 0/0 as-built). The adjacent
  F2 sitting room stays OUT of scope (matches current derived spec; showcase = the
  room with gate evidence).
- A3 BUDGET: unconstrained for the showcase (`budget_ceiling_thb` stays null).
  Materials/FF&E chosen on design merit; costing deferred to any real engagement.
- A4 BATH CEILING: the ~1.95 m reading is treated as TUB LENGTH (best case);
  ensuite ceiling assumed ≥ the 2.00 m floor in pipeline/dimensional_rules.v0.2.json.
  Flagged for site verification before any real deliverable.
- A5 TOOLING: Stage-04 contract names ComfyUI/FLUX (blueprint text); direction of
  record is Gemini HYBRID (pipeline/CLAUDE.md + docs/research/2026-07-02-comfyui-
  flux-feasibility.md, decided 2026-07-02). Showcase renders use the evidence path:
  registry render-hybrid production=v004, pro image tier, camera v0.4.1.

If the client later supplies real answers, re-run Stage 00 merge → any assumption
that breaks invalidates downstream stages from the first stage that consumed it.
