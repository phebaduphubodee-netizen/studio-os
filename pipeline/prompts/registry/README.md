# prompts/registry — compiled prompt payloads (M2.2)

Conventions (pipeline/CLAUDE.md is law):
- One directory per **intent/domain** (never per model): `render-hybrid/`, later
  `critique-vision/`, `layout-brief/`, …
- Versions are **immutable**: `v001.json`, `v002.json`, … Never edit a published
  version — copy, bump, edit, test.
- `labels.json` maps `dev | staging | production` → a version. **Promote by
  re-pointing the label only.** Production label = proven by the critique gate
  (≥4/5) on at least two distinct room types.
- Payloads are *compiled*: a `template` with explicit `{slots}` + `defaults`.
  Dispatch scripts resolve `@<intent>[@label]` and fill slots from CLI
  `key=value` pairs (see `hybrid_render.py`).
- Dual-track (T5/CLIP) rule applies to diffusion payloads only; Gemini
  image-edit instructions are single-track prose.

Usage from a dispatch script:

    python pipeline/scripts/hybrid_render.py IN.png "@render-hybrid" OUT.png room_type="master bedroom suite"
    python pipeline/scripts/hybrid_render.py IN.png "@render-hybrid@dev" OUT.png style_brief="..."
