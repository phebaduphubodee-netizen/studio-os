# Render photorealism: styling & lighting rules (REFERENCE — NLM-grounded)

- **Source:** NotebookLM notebook `a5a43395` "Design Systems and Integration
  Protocols Interface" (118 sources), conversation `b39e68d6` turn 7, 2026-07-02.
  Inline `[n]` markers cite notebook sources (resolve inside the notebook).
- **Status:** REFERENCE tier — staged via the NLM research lane; distill into
  `knowledge/` proper (and reconcile with lighting.md / color-composition.md)
  before any value gates a deliverable.
- **Question asked:** what styling/lighting principles separate a professional,
  lived-in interior image from a sterile one (concrete, actionable rules).
- **Why now:** the critique gate dings every clay-derived hybrid on
  lighting_quality / styling_and_life; registry v003 fixed lighting by prompt —
  these rules are the checklist for v004+ and for the clay controls themselves.

## The six rules (as answered)

**1. Strict lighting hierarchy** — never one uniform ceiling source (flattens
the image, reads AI-generated). Layer ambient + task + accent; harmonize color
temperatures (no clinical 4000K against warm 2700K in one localized zone) [1].

**2. Foreground layering** — head-on rooms with nothing breaking the camera
plane read institutional. Put a physical object (plant, chair edge, tabletop)
in the immediate foreground for depth + scale anchor [2].

**3. Material imperfection / micro-texture** — 0.0 or 1.0 roughness virtually
never exists; add wear, fingerprints, scratches, terrazzo chips, brushed-metal
refraction [3, 4, 5].

**4. Physical camera optics** — 35–50 mm focal length for natural perspective;
shallow DoF (~f/2.8) on a lived-in detail; never arbitrary non-physical blur
[6, 7, 8]. *(Pipeline note: our `--eye` suite camera is 26 mm — wide-angle CG
tell; candidate v0.4 change.)*

**5. Environmental light + contact shadows** — furniture floats without them.
Pick a temporal quality (golden hour / blue hour / overcast) and force ambient
occlusion + soft contact shadows [9, 10, 11].

**6. Parallel verticals** — camera back perfectly vertical or tilt-shift;
leaning walls = spatial disorientation [7, 12]. *(Already encoded: build_room's
level-camera + shift_y rule.)*
