# Retired skills — moved OUT of `.claude/skills/` on 2026-08-27

A skill in `.claude/skills/` is loaded into the roster of every session and printed to
the model as an available move. A skill whose subject does not exist in this repo is
therefore not harmless clutter: it is a permanent suggestion to do something impossible,
sitting in the same list as the ones that matter. These two were moved here rather than
deleted, because the pipelines they describe may yet arrive.

## `usd-validate` and `material-lint`

Both were written 2026-07-02 for the pipeline the blueprint described. Measured on
2026-08-27, that pipeline has never existed in this repo:

    find . -name "*.usd*" -not -path "./.git/*"   -> 0 files
    find . -name "*.mtlx"  -not -path "./.git/*"  -> 0 files
    ls pipeline/workflows/                        -> empty (no ComfyUI graphs)

The lane that actually renders is Blender/Cycles with `pipeline/scripts/build_room.py`
and PBR materials assembled by `material_presets.py` / `material_defaults.py`. Neither
skill has produced an output in 56 days, and neither could have.

**They are not deleted.** Stage 04's contract still describes a ComfyUI + FLUX dispatch
(`projects/PRJ-2026-002_c001-house/04_visualization/_contract.md`), which is a separate
open question — either that contract is stale, or the pipeline is genuinely planned and
these skills come back with it. Whoever settles that question moves these two back into
`.claude/skills/` (a plain `git mv`, the frontmatter is unchanged) or deletes them.

**What replaces `material-lint` in the meantime:** nothing, and that is worth saying out
loud rather than implying coverage. Material correctness in the live lane is checked by
`texture_scale.py` (world size of a texture repeat, asserted at ingest), `texture_check.py`,
`style_check.py` and the STY slot signatures printed by `plan_status`. If a MaterialX
lint is wanted for the Blender path, it is a new instrument and admission is governed by
D-112 — not a revival of this file.
