---
name: material-lint
description: >
  Lints MaterialX (.mtlx) material definitions against studio PBR rules and
  the container convention before they enter assets/shared/materials-mtlx/.
  Use when the user adds/edits materials or asks to "lint materials".
  Read-only on qa/thresholds.yaml.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# /material-lint — *.mtlx PBR + convention checks

.mtlx is XML — parse with python stdlib (xml.etree), no external deps.
1. Container convention (blueprint §7.2): one root `.mtlx` per material
   folder + `textures/` subfolder beside it; textures referenced by
   RELATIVE path into that folder; stored uncompressed. Report violations.
2. Naming: `M_Base_Variant_NN[_Inst]` for materials, `T_..._<ORM|N|D>` for
   textures. Mismatches listed; renames only via scripts.
3. PBR ranges (mirror qa/thresholds.yaml material_qa — read it, don't
   restate stale values):
   - albedo/base_color defaults within the thresholds' sRGB band
   - metalness effectively binary (flag mid-gray defaults)
   - roughness not pinned to absolute 0.0 or 1.0
   Values checked are the .mtlx input defaults; rendered-pixel QA is
   Pillar 4 at render time, not here.
4. Texture sanity: referenced files exist; ORM/normal maps named per
   convention; flag texture files sitting outside textures/.
5. Output: per-file pass/warn/fail list with line cites, plus a one-line
   fix suggestion each. This skill never edits .mtlx content and never
   touches thresholds.
