---
name: usd-validate
description: >
  Validates USD scene/asset files against studio conventions before they
  enter assets/ or a project stage: ASCII-parseable .usda checks now
  (naming, payload boundaries, layer structure by text inspection);
  full schema validation via usd-core arrives Phase 2. Use when the user
  adds/reviews USD assets or asks to "validate the scene".
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# /usd-validate — convention checks for *.usda (Phase-2-lite)

Scope today (text-level, .usda only; binary .usdc → LFS pointer check only):
1. Naming: prim/file names follow `Prefix_Base_Variant_Suffix`
   (SM_ static mesh, M_ material, T_ texture, HDRI_). Report violations;
   renames only via scripts.
2. Structure (blueprint §7.2): geometry referenced behind `payload` arcs —
   flag `references`/inline meshes where a payload boundary is expected;
   lighting rigs as sublayers, style options as variants. Grep for
   `payload`, `subLayers`, `variantSet` and report what's missing.
3. Hygiene: no absolute local paths (C:\ or /home/) inside the file;
   texture paths resolve inside the asset's own folder tree; `.usda` stays
   ASCII (reject if binary content sneaks in under the extension).
4. LFS sanity: `.usd/.usdc/.usdz` files must be LFS pointers in git
   (`git lfs ls-files` covers them); a real binary blob in history is a
   blocking finding — report, do not attempt history rewrite.
5. Output: a short pass/fail list per file with line cites. This skill
   never edits scene files.
Phase 2 upgrade: swap steps 1–3's text checks for usd-core `UsdUtils`
compliance checks in `pipeline/scripts/`; keep this CLI contract.
