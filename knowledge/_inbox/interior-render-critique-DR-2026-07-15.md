---
title: How to critique a photoreal interior render — plausibility, material palette, sellability, and a scoring rubric
tier: REFERENCE
source: NotebookLM Deep Research (2026-07-15), notebook 639575c3-9d1c-4b34-92c9-18c141a855c4 ("DR: Interior render critique"), turn 1; 99 auto-discovered sources settled (1 errored), DR budget slot 2/20.
primary_refs:
  - Colour/material distribution — the 60-30-10 (and 70-20-10) proportional hierarchy: dominant base / secondary contrast / accent.
  - Detailing authorities the answer leans on — recessed base/zocalo (10-15mm), mitered returns, aluminium shadow-gap (Z-reveal 10-20mm), L-bead cladding terminations, edge bevel/chamfer 1-2mm, PBR (normal/roughness/specular) + UV randomisation.
  - Lighting/camera — IES profiles, 2700-3000K interior + daylight, bracketed exposure holding shadow + window; 2-point perspective, eye height 1.2-1.6m, 24-50mm focal, avoid <20mm fisheye.
  - Style-identity material signatures — Minimalist (glass/polished metal + clean concrete/stone), Japandi (straight-grain white oak/ash + hardwax oil + oat plaster + raw linen; AVOID gloss lacquer, wenge/teak, book-matched marble), Luxury (book-matched marble + walnut + brushed brass + bouclé/mohair).
status: STAGED 2026-07-15 (not yet distilled). Distillation target = knowledge/classifications/qa-dimensions.md + knowledge/rendering/render-defaults.md (a plausibility + material-palette QA lane) and a scorecard rubric for pipeline QA. Do NOT let any value here gate a client deliverable before distillation.
provenance_note: >
  Deep Research question was GENERIC (no client name/dim/plan — passes the NLM privacy hook). Turn 1
  is the payload; the wrapper's --iterate 2 harvested NotebookLM's own suggested follow-ups, which
  DRIFTED to a "Japandi vs Scandi" tangent (turns 2-4, partly duplicated) — those turns are audit-trail
  only, not distilled. [n] markers below are the notebook's internal citations into the 99-source corpus;
  per-[n] source-title resolution is DEFERRED to distillation (the notebook 639575c3 is the retained
  audit trail, alongside qa-history JSON in this same folder). Blog/archviz-tier guidance corroborated
  across many sources; treat construction dimensions (zocalo 10-15mm, shadow-gap 10-20mm, bevel 1-2mm,
  Kelvin, focal lengths) as archviz convention, NOT Thai statute — codes-th always outranks.
why_this_matters: >
  Fired to answer the FIRST sellability-pilot verdicts (designer judged our render LOSING on every pair)
  with two named reasons this DR grounds exactly: (a) the "รูหัวเตียง" = §1 Feature-Wall Terminations +
  Dark Dead-End Recesses; (b) "ไม้ไปหมด" = §2 The Mono-Material Trap. See [[discord-projects-benchmark-plan]].
---

# Critiquing a photoreal interior render (professional methodology + 1-5 rubric)

> REFERENCE — NotebookLM DR turn 1, verbatim. Applies to the benchmark-sellability lane and pipeline QA.
> Our two live wounds map onto §1 (feature-wall termination / black-hole recess) and §2 (mono-timber).

### 1. Architectural Plausibility: Structural Diagnostic Protocols
A professional critique evaluates renderings as digital representations of physical reality; when a visualization ignores physics or construction standards, the brain registers cognitive dissonance [1].

*   **Floating or Cantilevered Elements:** Gravity dictates that heavy objects must have a continuous load path to the foundation [2]. Reviewers should look for deep, ultra-thin stone shelves or vanities spanning long distances without visible steel brackets or wall chases [2, 3]. If a thick natural stone countertop floats without a sub-top substrate or visible support, it is structurally impossible [2].
*   **Plinths and Shelves Without Support:** Volumetric blocks or stone plinths are frequently rendered as paper-thin boxes sitting perfectly flush on flooring [3]. A reviewer detects this by scanning the base for a lack of a 10-15mm recessed base (zocallo), mitered base detail, or shadow line [4, 5].
*   **Unresolved Wall and Ceiling Junctions:** Materials expand and contract, meaning a perfect, razor-sharp 90-degree joint between drywall and concrete or timber is physically impossible without cracking [6]. Check wall-to-ceiling or wall-to-floor transitions for an absolute 0mm intersection [5, 6]. Plausible renders feature baseboards, coving, or extruded aluminum shadow gap profiles (10mm-20mm Z-reveals) to bridge materials [7]. Missing trims often result in artificial "light leaks" where illumination bleeds through the boundary [8].
*   **Feature Wall Terminations:** Heavy clad walls (timber slats, stone, or acoustic panels) must have logical terminations [9]. Reviewers should inspect outside corners to see if textures end abruptly, exposing raw drywall profiles [5, 9]. Correct geometry requires the cladding to wrap around the corner, utilize a mitered return, or terminate into a metal trim like an L-bead [5, 9].
*   **Dark, Dead-End Recesses and Cavities:** In reality, light bounces off surfaces to illuminate tight voids and corners [10]. If recesses under cabinetry, inside shelving, or between furniture and walls are rendered as opaque, absolute black (0,0,0 RGB) "black holes," the engine's global illumination (GI) is configured incorrectly [5, 10]. Plausible shadows must be soft, transparent, and carry color bleeding from adjacent materials [10].

### 2. Material and Colour Palette Composition
The curation and distribution of finishes govern the psychological impact and visual credibility of an interior [11].

*   **Dominant, Secondary, and Accent Hierarchy:** Professional designers rely on the 60-30-10 rule to establish visual harmony [11]. The dominant base (60%) consists of large, low-saturation surfaces like walls and primary flooring [12]. The secondary layer (30%) provides contrast through cabinetry, large upholstery, and rugs [12]. The accent layer (10%) delivers visual energy via high-contrast metallics, art, or lighting fixtures [12].
*   **The Mono-Material Trap:** Applying a single material, such as timber, uniformly across floors, walls, and ceilings flattens the image because the camera struggles to resolve depth [13, 14]. It also creates psychological dissonance, as the brain anticipates intense echoing and reads the space as cold and stressful [14]. Furthermore, it deprives the eye of a natural resting place by eliminating material hierarchy [14].
*   **Adding Cohesive Contrast:** To cure monotony, balance large wooden or hard surfaces with soft, light-absorbing textiles (raw linen, wool) and matte mineral finishes (microcement, lime plaster, honed stone) [15]. Tactile contrast — rough against smooth, matte against subtle sheen — creates depth and visual balance without breaking cohesion [15].
*   **Expressing Style Identity:**
    *   **Minimalist:** Relies on clean geometry and high-contrast reflective relationships [16]. Pair smooth, light-receptive planes like glass and polished metal with the monumentality of clean-faced concrete or stone, keeping ornamentation to an absolute zero [16].
    *   **Japandi:** Merges Japanese *wabi-sabi* with Scandinavian *hygge* [17]. Use quiet, straight-grained woods (white oak, ash) with matte, hardwax oil finishes, paired with warm white/oat plaster walls and highly tactile, breathable textiles like raw linen [17, 18]. Explicitly avoid high-gloss lacquers, heavy-grained tropical woods (wenge, teak), and book-matched marbles [17, 18].
    *   **Luxury:** Balances monumentality with warmth through rich natural stones (book-matched marble) and structured dark hardwoods (walnut paneling) [19]. Utilize brushed brass or polished nickel for luminous signature details, softened by custom bouclé or mohair upholstery [18, 19].

### 3. Sellability and Finish
A polished, client-ready render demonstrates mastery over computational physics and emotional storytelling, moving far beyond a technical draft [20].

*   **Styling and Dressing:** A photorealistic render must capture a "lived-in" quality through subtle, curated imperfections [21]. Look for thoughtful staging: a slightly rumpled linen throw, an open book, or a single hand-thrown ceramic vase [21]. Avoid sterile, vacant spaces or the amateur mistake of placing identical, repeating 3D assets across a scene [20, 21].
*   **Lighting Narrative:** Believable lighting establishes a clear hierarchy [22]. Combine daylight exposure with warm interior fixtures (2700K to 3000K), using IES light profiles to cast physically accurate, complex wash patterns on walls [22]. A single, flat ceiling light creates an unconvincing, institutional atmosphere [22]. Proper bracketed exposure should hold detail in both the interior shadows and the exterior window view without blowing out to pure white [22].
*   **Composition and Camera:** The camera must be placed at a natural human eye height (1.2m to 1.6m); placing it too high feels like a security camera, while placing it too low unnaturally stretches furniture [23]. Utilize a 2-point perspective to keep vertical lines perfectly straight [23]. Use realistic focal lengths (35mm-50mm for natural sight, 24mm-35mm for room capture) and strictly avoid extreme wide-angle lenses (<20mm) that cause intense fisheye distortion [23].
*   **Level of Detail (LoD):** Digital perfection ruins realism [24]. Reviewers must verify that sharp 90-degree edges are beveled or chamfered (even 1-2mm) to catch light highlights [24]. Textures must use Physically Based Rendering (PBR) maps (normal, roughness, specular) to simulate scratches, dust, or variable glossiness [24]. Finally, ensure large planes utilize seamless textures and UV randomization to prevent obvious, repeating "tiling" patterns [24].

### 4. Professional Critique Rubric
Professionals score visualizations on a scale of 1 (Unacceptable/Distorts Reality) to 5 (Exemplary/Photographically Indistinguishable) [25].

*   **Architectural Plausibility:**
    *   *Check:* Load path integrity, plinth zocallo details, shadow gaps at wall/ceiling transitions, and soft GI shadows carrying color bounce [26].
    *   *Red Flags:* 20mm thick floating stone shelves, geometry clipping through floors, 0mm razor-sharp wall junctions, light leaks, and absolute black (0,0,0) cavities [26].
*   **Material & Palette Curation:**
    *   *Check:* 60-30-10 or 70-20-10 proportional hierarchy, tactile contrast (hard vs. soft), and strict adherence to the specified style identity [26].
    *   *Red Flags:* Mono-material timber applied to all planes, flat single-color surfaces without PBR normal maps, or high-gloss finishes used in Japandi scenes [26].
*   **Sellability & Finish:**
    *   *Check:* Human "lived-in" storytelling, layered lighting (natural + artificial), 2-point perspective at 1.2m-1.6m height, and micro-detailed bevels on edges [26].
    *   *Red Flags:* Sterile environments, duplicated props, blown-out window exposures, converging vertical lines, fisheye lenses (<20mm), and visible polygon facets on curved objects [26].

---

## How this scores OUR current work (the two pilot losses)
- **BF14 headboard "รู"** → fails §1 *Feature Wall Terminations* (the freestanding slat wall ends with no mitered return / L-bead, exposing the cavity) AND *Dark Dead-End Recesses* (the ~250mm cavity renders as an absolute-black hole → GI/geometry not resolved). Rubric: **Architectural Plausibility red flags** hit.
- **"ไม้ไปหมด"** → textbook §2 *Mono-Material Trap* (timber on floor + headboard + wardrobe + TV cabinet; no 60-30-10 hierarchy, no secondary/accent, no tactile contrast). Rubric: **Material & Palette red flag** hit.
- Lighting was PRAISED by the designer, consistent with §3 valuing lighting narrative — our gap is plausibility + palette, not light.
