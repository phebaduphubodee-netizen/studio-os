# E-002 · 2026-07-02 · Showcase render APPROVED (PRJ-2026-002 batch 001)

Owner approved R_PRJ002_MasterSuite_Cam01_v01 via chat ("go"), no revision notes.
Judge: 4.5 SHIP + 5.0 SHIP (mean 4.75) — first pro-tier 5/5 roll; styling 5/5 both rolls.

## THE APPROVED CONFIGURATION (exact settings that worked — reuse verbatim)
- Prompt: registry render-hybrid **v004** @production (immutable version)
- Image model: **gemini-3-pro-image-preview** (GEMINI_IMAGE_MODEL env; PAID tier)
- Judge: critique.py default (gemini-2.5-flash), multi-roll mean basis
- Camera: build_room --eye, v0.4.1 subject-aware (26 mm tight-room doctrine)
- Clay: Blender Cycles GPU 256 samples, RCP-matched warm downlights
- Slots (the styling-5/5 combination — concept-fed):
  - room_type: "master bedroom suite — the tall dark wall behind the bed is an
    upholstered headboard / TV feature wall; the bright opening on the right is
    the entry door"
  - material_story: "light engineered-oak wood flooring in a matt natural finish,
    full-height rift-oak veneer built-in wardrobes and headboard/TV wall in matte
    lacquer, warm greige matte plaster walls and ceiling, stonewashed
    greige-oatmeal linen bedding with natural wrinkles, matte black and brushed
    brass hardware accents"
  - lighting_story: "low golden-hour evening light from the terrace-side glazing,
    one dominant soft warm key direction with deep soft shadows, layered with a
    warm cove glow and lit brass bedside sconces, all in one 2700-3000 K family"
  - style_brief: "warm contemporary Thai-tropical minimal, quiet luxury, calm and
    lived-in"
- Style direction approved by extension: concept 60/30/10 = oak field / greige+
  linen / matte black+brass (02_concept/concept.md post-MARS r1)

Caveat: SHOWCASE approval under best-case override A1–A5 — not a client release;
real windows/scope/budget answers may invalidate from the stage that consumed them.
