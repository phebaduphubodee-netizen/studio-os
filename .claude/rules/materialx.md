---
paths: ["assets/shared/materials-mtlx/**", "**/*.mtlx"]
---
# MaterialX Rule
- One root .mtlx per material package; textures under ./textures/; archives
  stored UNCOMPRESSED (renderer memory-mapping).
- PBR sanity on edit: albedo values within 30–240 sRGB, metalness binary
  (0 or 1), roughness never absolute 0.0/1.0 across large areas.
- Naming: M_Base_Variant (e.g. M_Oak_Fumed_02). Never rename via raw file moves.
