# Blender Pipeline Research (2026-06-30) — workflow wf_31936472

4 parallel research angles (bpy headless / SketchUp interop / arch addons / headless render) +
synthesis. Confirms the engine choice and gives a concrete, honest architecture.

## Architecture — 3 decoupled layers (only the middle is Blender)
1. **RULES + SPEC + CLEARANCE ENGINE** — pure Python, NO `bpy`. The differentiator lives HERE:
   dimensional correctness is a CONSTRAINT problem, not a Blender problem. Claude emits a room/layout
   SPEC (coords in metres) + the clearance check vs `dimensional_rules.json`. Unit-testable with plain
   `python`. ✅ **`pipeline/clearance_check.py` built + passing this layer.**
2. **BLENDER MATERIALIZER** — headless `bpy`, one process per job:
   `blender -b --factory-startup -P build.py -- spec.json`. Use the DATA API only
   (`bpy.data.meshes.new`+`from_pydata`, `bpy.data.libraries.load`) — **never `bpy.ops`** (dies with
   `poll() failed` in `--background`). Build openings as authored quad face-loops, NOT boolean (booleans
   → n-gons the SketchUp friend will see). ✅ `build_room.py` already uses the right pattern.
3. **RENDER + EXPORT** — Cycles GPU (EEVEE needs EGL/Xvfb, avoid headless); script owns engine/device/
   output (CLI flag-ordering trap); log active device + samples to catch silent CPU fallback.

## Interop verdict (friend uses SketchUp) — ONE-WAY only
- **No native .skp exchange, no clean round-trip.** Never promise an editable SketchUp file back —
  Blender→SketchUp arrives as triangle soup (non-solid, multi-material), destroying her component/section workflow.
- **FINE / Blender SUPERIOR:** final Cycles renders, walkthroughs, view-only GLB/USDZ; and one-way
  INGEST of her `.skp` (open-source SketchUp Importer, Win/Mac only) to run the clearance check on it.
- **3D exchange drops dimensions/text/sections** → construction docs must be FLAT 2D (PDF/DWG/DXF/annotated), never a 3D round-trip.
- ⚠️ **SCALE TRAP:** SketchUp exports Imperial even when modeling in metres (~0.0254× error) → a
  plausible-but-wrong-scale model = the exact failure we sell against. **MUST add a scale assertion on every ingest.**

## Deliverable decision (RECOMMENDED — founder to confirm)
Sell **view-only / terminal** outputs, NOT editable models:
1. **Cycles photoreal RENDERS** = primary product (SketchUp's known weakness → our edge).
2. **GLB/USDZ** presentation 3D for client review (viewed, not edited).
3. **Flat 2D dimensioned PDF/DWG** = the construction/"แบบ" deliverable (dimensions only survive in 2D).
Standardize handoff on glTF if friend on SketchUp 2025+, else DAE/COLLADA.

## Automation ceiling (HONEST — do not over-promise)
~**70–85% of the LABOR** for a still is automatable (spec→geometry, units, asset import, camera rig,
lighting, render, denoise, batch, AND the clearance/scale check). The **un-automatable ~15–30%** =
**LAYOUT GENERATION** (where furniture goes — constraint+taste, the genuinely hard piece; automation
CHECKS a layout, a human GENERATES it), composition/lighting taste, and **final scale/dimensional QA**.
→ Market as **"automated, dimensionally-checked drafting that a designer directs and signs off"** — NOT "fully automated interior design."

## Top risks
Scale-trap silently corrupts the differentiator (add assertion) · maintaining TWO generators (.py + .rb)
drifts (pick engine-of-record) · over-promising editable .skp · `bpy.ops` creep breaks headless ·
EEVEE-on-headless crash · DRAFT rules JSON ≠ friend's local code (verify before client use).

## Stays MANUAL (the human ceiling)
Layout generation · aesthetic/client judgment · hero camera+lighting final tuning · dimensional
APPROPRIATENESS (code proves 80cm apart; human knows if 80cm is right here) · local-code compliance ·
final QA sign-off that scale/clearances are right on every deliverable.
