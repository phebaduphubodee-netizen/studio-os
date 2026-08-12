# DR (NLM ask): why a simulated free hem serrates periodically, and what kills it

- **Tier:** REFERENCE (research answer, not domain truth). Nothing here gates a
  deliverable until distilled into `knowledge/` per the inbox law.
- **Provenance:** NotebookLM notebook `ae3dd665` (blender-cloth-corner-drape
  corpus — source manifest lives with `dr-cloth-corner-drape-2026-08-11.md`),
  new turn asked 2026-08-12 during the p2r25 R1 stop; raw turn archived in
  `knowledge/_inbox/nlm-cloth-corner-drape/qa-history.json` (refreshed same
  commit). Question was generic — no client data, no dimensions beyond band
  values.
- **Why it was fired (DR-initiation criteria):** R1 stop naming a mechanism
  mystery + the defect class's 2nd build round. Two mechanisms were spent on
  the sine-hem class (p2r24 slack field: tooth-line autocorr 0.591→0.434;
  p2r25 hem bending 8×: 0.434→0.489, i.e. NOT reduced) and the critics still
  file the hem as "คลื่นคาบสม่ำเสมอเหมือน sine".

## The diagnosis (sharper than both of ours)

A UNIFORM quad grid draping under gravity is a physical-numerical RESONATOR:
the system has a **single dominant buckling eigenmode**, so compressive stress
along the free hem resolves at one wavelength — the machine-cut sawtooth. The
LINEAR bending model on a regular grid is *more* susceptible to grid-aligned
buckling (its virtual cross-springs), and uniform shrink expands every
structural spring identically, which is exactly the symmetry the eigenmode
needs. Our two spent levers (WHERE the fullness goes; how stiff the boundary
bends) never broke that symmetry — bending stiffness only scales the
wavelength (~(B/K)^(1/4)), which matches what we measured: same lag, softer
teeth.

## The levers practitioners actually use (ranked for our next round)

1. **Hem MASS** — the real-world fix is literally a weighted hem strip:
   body ~0.12 → hem ~0.25-0.5 kg (2-4×) via the mass vertex group, dragging
   the buckles down. We have never touched mass. (Band = REFERENCE, verify
   against original sources at distillation.)
2. **Symmetry-breaking vertex SPACING at the hem** — irregular in-plane
   station spacing (or isotropic/triangulated hem topology) removes the single
   eigenmode. The sheet stays FLAT, so the enter-smooth law is untouched —
   this is the "irregular cell" half of the r23 triage suggestion, now with a
   mechanism behind it.
3. **shrink_max ≤ ~5% along the hem** — over-contracting the edge is its own
   pucker source. (Our throw hem rides fall weight 0.30 × slack 10% ≈ 3% —
   inside the band; the coverlet ladder solves lower. Check per piece.)
4. **Post-sim Smooth modifier targeted at the hem vertex group** (factor ~0.5,
   5-15 iterations, placed after Cloth, before Subdivision) — damps the
   high-frequency serration, keeps the aperiodic primary folds. Render-side
   kill switch, no physics re-run.
5. **Simulate coarse, render fine (SurfaceDeform)** — the industry-standard
   frame for all of the above; heavier change, keep for later.

## What this does NOT license

- No pre-WRINKLING of feedstock (z-noise) — spacing jitter is in-plane and
  flat; the solver stays the only wrinkle author.
- The numeric bands above are model-cited from the corpus; they are
  REFERENCE-tier until checked against the original sources ([n] citation
  markers in the raw turn could not be resolved to source titles from the CLI
  output — same caveat class as DRW-4's cut-plane table, recorded rather than
  hidden).
