# Element 3 — Bed + base · BUILD layer (as-built)
## 2026-07-18 — follows element3-bed_DD-2026-07-18.md

**What got built** (the DD's §6, realized + rendered + adversarially reviewed):

## Spec reconcile (`master-suite.CANONICAL.spec.json`)
- **bed** item → ink footprint: `x3204 y51 w2000 d2149` (was the transposed `3092/110/2134/1981`),
  keep `h600 rot270` (head EAST). Added an element-3 `design` block + `base_material:
  upholstered_greige_linen`.
- **nightstands** (×2) → ink `~501×498/501` @ `x4702` (was `300×300` @ `4794`); added
  `lamp: {kind: dome, finish: brass, cct_k: 2850}` + design blocks.
- **bench** → ink `498×1000` @ `x2654 y626` (matched to ink); note = D3-4 greige linen.
- **eye_camera_variants.bed_hero** ADDED — stand `[1400,1125]` → aim `[5180,1125]`, 26 mm,
  shift −0.14: the bed-foot hero (bed + both lamped nightstands + BF14 headboard wall).

## Code
- `millwork.nightstand_lamp_parts(w,d,h,lamp)` — **PURE + unit-tested** (metres, footprint-local):
  a solid low cabinet + a brass dome lamp (base+stem+shade), all part half-widths scaled off
  `min(w,d)` so the lamp can never overhang, any aspect ratio.
- `build_room._build_nightstand` — consumes it; matte-dark cabinet `(0.13,0.12,0.11)`, brass
  base/stem `(0.60,0.44,0.20)` metallic, warm shade `(0.93,0.86,0.72)`. Dispatch intercepts
  `side_table` **with a `lamp` key** (opt-in; plain side tables keep the model path).
- `build_room._build_bed` base retinted → mid-greige **linen** `(0.46,0.43,0.39)` sheen 0.2 (was
  a dark wood-brown) — joins the plaster ground, NOT a fifth oak mass (D1-A).
- `build_room._build_bench` seat retinted → the **same greige** `(0.46,0.43,0.39)` so build == DD
  == story (fix from review — it was left pale-cream satin).
- `material_presets.furniture_material_story_bits(spec)` + wired into `material_story()` — names
  the bed base + bench linen, the matte-dark nightstands + brass dome lamps, and the poly-wool rug,
  DATA-driven from the items, so the Gemini polish pass can never repaint the base oak or drop the
  lamps (closes the recurring element-2 revert-by-omission).

## Render
`pipeline/output/room_bedroom_suite_eye_bed_hero.png` (clay control, GPU Cycles 256spp, 2000×1400).
Verifies: head flush to the BF14 oak slats (headboard = the wall), upholstered platform base, two
dark nightstands with brass dome/mushroom lamps flanking the head, the greige bench at the foot,
the rug, garden glass right / bookshelf left.

**Owner LOOK — "ยังเหลี่ยม" ×2 → massing softened three passes** (2026-07-18): (1) generous bevels;
(2) a recessed floating base so the mattress overhangs + a shadow reveal; (3) a LOW recessed plinth
under a full-width **draped coverlet** that falls over the sides to just above the plinth (the
fabric fall that breaks the hard box faces). **Owner then accepted the clay as the STRUCTURAL
CONTROL** — like element 1/2, the bed CLOSES on clay and the true softness (linen drape, wrinkles,
tonal separation) is deferred to a single **Gemini beauty pass for the whole hero suite** (run once
the Google-AI-Studio billing is topped up — was 429 billing-blocked 2026-07-11). The clay is the
skeleton, not the deliverable image. **Also caveat**: the upholstered pieces read pale in clay (the
greige base is light-by-design to join the ground; the linen-vs-crisp-bedding tone lands in the
beauty pass, now NAMED in material_story). Lamps are geometry-only (unlit) — the warm glow is a
stage-05 lighting concern, PH-02-bounded.

## Adversarial review (2 independent reviewers, 2026-07-18)
Both converged on ONE blocking defect — **the bench material contradicted its own story/DD** (built
cream satin, described greige linen). FIXED (retinted to the base's greige). A second, low/latent
finding — the lamp **stem** was a fixed 0.028 m box that would overhang a sub-28 mm top and the test
never reached that regime — FIXED (stem scaled off `min(w,d)`; test now exercises 0.02 m + 0.001 m).
Everything else CLEARED: revert-by-omission (all 4 at-risk materials named), spec-vs-ink (<1 mm),
anti-monopoly (base + nightstands not oak), camera-sees-the-decision, geometry (no collisions, head
flush to BF14). Tests: 218 pure (millwork+materials, incl. 10 new) + the full 1719 suite green.

## Deferred (flagged, not blocking)
- **Lamp emission** (warm bedside glow) — stage-05 lighting, PH-02-bounded (dim vs the windows).
- **Gemini beauty pass** — material_story is now correct for it, but the pass is BILLING-BLOCKED
  (429 RESOURCE_EXHAUSTED, per eye-camera.master_bedroom.json) — run when topped up.
- **`reconcile_elements` latent** — a `materials.elements` key targeting a lamped `side_table`
  would pass the anti-silent-drop gate yet be ignored by `_build_nightstand` (bespoke). Not
  triggered (no `materials.elements` block exists); a one-line follow-up if one is ever added.
- **Bed proportion**: a 2000-head-foot × 2149-wide feature bed (the '7' is the width) — owner-
  adopted from the ink; a designer/owner nudge is a furniture edit, not a rebuild.

NEXT (element 3+ remaining): ensuite (ห้องน้ำ) · 3-layer lighting (ไฟ) · textiles (ผ้า) → assemble → hero.
