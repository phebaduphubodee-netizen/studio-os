# Color schemes (Albers) + interior camera/composition (Shulman/Block/Adams)
> PROVENANCE: NotebookLM notebook "Design Systems and Integration Protocols Interface"
> (a5a43395-e085-4fe6-a46c-4a8f7b438cc2, 118 sources), asked 2026-07-03.
> STATUS: secondary summary grounded in the notebook's book/standard sources —
> REFERENCE tier, NOT Authority. Numbered [n] citations refer to notebook sources
> (full Q&A in qa-history.json). File to: knowledge/styles/ + pipeline prompt lexicons after human review.

### **PART 1: Practical Rules for Interior Color Schemes**
*   **Color Harmony Types:** Interior palettes can be systematically organized 
using six primary types of color harmony: Complementary, Split-complementary, 
Double (Tetrad) complementary, Analogous, Triadic, and Monochromatic [1].
*   **The 60/30/10 Application:** This mathematical formula serves as the 
"golden ratio" of spatial color distribution. To achieve visual balance, 60% of
a room should feature the dominant color (e.g., walls and large rugs), 30% the 
secondary color (e.g., furniture and window treatments), and 10% the accent 
color (e.g., artwork and small accessories) [2].
*   **Adjacency and Simultaneous Contrast:** Color is the most relative medium 
in design; a single color can look like two entirely different colors depending
on its background [3, 4]. This is driven by simultaneous contrast (the 
after-image effect), where a ground color essentially "subtracts" its own hue 
and lightness from the object placed upon it [5-7]. Therefore, a fabric or 
paint color will visually shift as soon as it is placed next to a new adjacent 
room color. 
*   **Testing Colors in Context:** Because color perception changes based on 
quantity, area size, and lighting conditions, harmonious swatches can fail if 
tested in isolation [8-10]. Josef Albers championed testing colors in physical 
proximity using colored paper instead of paint, which allows for exact, 
unvarying comparisons without the distracting texture of brushstrokes [11-13]. 
Additionally, the physical boundary between colors matters; a soft boundary 
(like torn paper or draped fabric) connects colors, while a hard boundary (like
cut paper or sharp architectural edges) separates them [14-16].

### **PART 2: Composition and Camera Principles for Photographing and 
Rendering**
*   **Viewpoint Height and Distance:** A natural, eye-level perspective is 
ideal for capturing interior spaces, typically achieved using a 28mm or 35mm 
prime lens to establish broad environmental context while minimizing edge 
distortion [17]. Ansel Adams notes that true perspective is governed solely by 
camera-to-subject distance; moving the camera closer drastically enlarges 
foreground elements relative to the background, altering the room's perceived 
scale and depth [18-20].
*   **Keeping Verticals Parallel:** A strict rule in architectural imaging is 
that the camera back (or film plane) must remain perfectly vertical to prevent 
the convergence of parallel lines—the optical illusion where straight walls 
appear to lean or fall backward [21, 22]. In AI rendering workflows, this is 
enforced by using "tilt-shift" as a prompt modifier to simulate physical 
perspective correction [17].
*   **One-Point vs. Two-Point Perspective:** Maintaining strict two-point 
perspective rules is essential for spatial coherence in interior rendering [23,
24]. If shooting a space head-on (one-point perspective), the camera back must 
be aligned completely parallel to the subject's horizontal surfaces as well as 
its vertical lines to ensure absolute geometric accuracy without distortion 
[21, 22, 25].
*   **Foreground Layering:** To prevent a room from feeling flat and 
institutional, photographers and rendering artists must utilize foreground 
depth [26]. Positioning an object—such as a plant or the edge of a chair—in the
immediate foreground creates spatial hierarchy, adds dimension, and provides 
the viewer with a realistic anchor for scale [26].
*   **Contrast and Visual Structure:** Following Bruce Block's methodology, the
staging of a camera must deliberately organize visual components like space, 
line, shape, tone, and color to structure the frame [27]. Drawing from Julius 
Shulman’s mid-century photography, interior images must carefully balance 
artificial interior lighting with natural daylight to highlight architectural 
volumes and preserve realistic spatial transitions [28]. Implementing specific 
lighting contrasts—such as high-contrast chiaroscuro or soft ambient 
occlusion—forces realistic shadow behavior, establishing the three-dimensional 
geometry of the room [29].
