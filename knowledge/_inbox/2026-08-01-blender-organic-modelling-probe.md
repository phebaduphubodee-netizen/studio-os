# Blender's own organic-modelling tools, headless — measured 2026-08-01

**Tier: REFERENCE (a probe, not domain truth). Staged for distillation into
`knowledge/rendering/`.**

**Why this is staged in the vault and not left in `docs/`.** It was written into
`docs/handbuilt-geometry-audit-2026-08-01.md` first, and a finding that lives
only in `docs/` is not findable by a vault query — which is the failure this
studio recorded three separate times on the same day (an English grep missing a
Thai-indexed file; a 154-line DR that omitted the source a working designer named
in one sentence; our own files implying 3D Warehouse from three directions with
nobody following). Studio-general knowledge belongs where a search will hit it.

## The question

The studio had hand-written **1,370 lines of geometry generators** across
`trn001_styling`, `softgoods` and `curtains`, including 785 lines of cloth
physics that were then DISABLED for want of a collision term that turned out to
be one line. The standing justification was that a headless, script-only Blender
pipeline cannot use the interactive tooling. **Is that true?**

## The measurement

`-b --factory-startup`, every technique built with `bpy.data.*` and
`ob.modifiers.new()` only — **no `bpy.ops` touched geometry**, so none of it
collides with the headless law in `pipeline/CLAUDE.md`.

| technique | output | n-gons | cost | deterministic |
|---|---|---|---|---|
| SUBSURF level 1 / level 3 | 24f / 384f from a 6f cage | 0 | 4 / 2 ms | yes |
| SKIN + subsurf — an edge skeleton becomes a limb | 928f | 0 | 3 ms | yes |
| METABALL — masses that MERGE | 1020f | 0 (352 tris) | 3 ms | yes |
| CURVE bevel + taper | 360f | 0 | 1 ms | yes |
| DISPLACE on a subdivided cage — folds, no simulation | 1536f | 0 | 5 ms | yes |
| REMESH voxel | 1734f | 0 | 18 ms | yes |
| CORRECTIVE_SMOOTH | 96f | 0 | 1 ms | yes |
| GEOMETRY NODES | 96f | 0 | 2 ms | yes |
| *our hand-built figure, for comparison* | *759f* | **3** | 5 ms | yes |

**Nothing is blocked by headless.** The one honest reason for hand-writing
generators does not exist. And our own hand-built geometry carried n-gons that
every one of these tools avoids — which `pipeline/CLAUDE.md`'s export law forbids
outright, and which had gone unnoticed because nobody had asked.

## What each one is FOR

* **SKIN** — a limb, a stem, a branch, a cord, from a 5-vertex edge skeleton.
  This is what a hand-written tube generator reinvents.
* **METABALL** — masses that MERGE. A shoulder meeting an arm. **A loft of rings
  physically cannot do this**, which is why every ring-lofted figure has a seam
  where two masses should join.
* **CURVE bevel + taper** — stems, mouldings, cords, anything swept along a path.
* **DISPLACE on a subdivided cage** — folds and relief WITHOUT a simulation.
* **SUBSURF / CORRECTIVE_SMOOTH** — smoothing only. See the caveat.
* **REMESH / GEOMETRY NODES** — retopology and the whole procedural library.

## The caveat, which cost a render to learn

On the numbers subdivision looked free — 759 → 12,176 faces in 41 ms with the
n-gons gone, and the 2026-07-30 ground-truth study had already measured our files
at SUBSURF 0 against pro files that use it. **Rendered, it was worth nothing.**
Applied to everything it rounded away a stepped pedestal's deliberate ledges;
restricted to a smooth-shaded body it changed nothing visible at all, because at
200 px on screen there was no faceting to remove. 16× the geometry for zero.

> **Subdivision smooths what EXISTS and cannot add what was never there.**
> A probe proves REACHABILITY. Only a look proves VALUE.

The figure did not read wrong because it was faceted. It read wrong because it
had no face, no robe folds and no crossed legs — and no subdivision level
produces those. The bottleneck was the PARAMETERISATION, not the smoothness.

## What it implies for the studio

Wired as **R8b** in `CLAUDE.md`: do not hand-write what Blender already
generates. The audit naming which of our 1,370 lines duplicate a modifier —
~646, of which 408 are one bet on hand-written cloth against a simulator already
proven headless and deterministic at 0.48 s — is in
`docs/handbuilt-geometry-audit-2026-08-01.md`.

Probe source: `scratchpad/organic_probe.py` (session bb7e7749). Blender 5.1.2.
