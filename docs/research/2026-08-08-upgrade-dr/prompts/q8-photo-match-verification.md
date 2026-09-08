CONTEXT: A team is reproducing a single interior photograph as a 3D scene, to
learn by matching it. They recover the camera from vanishing points, then build
geometry, then materials, then light, checking each round against the photograph by
comparing pixel statistics in hand-chosen regions. Thirty rounds in, the pixel
statistics keep confirming local matches while whole-frame, first-order errors
survive — a missing opening, an object at the wrong scale, a mass that should not
exist. I want to know what the established practice is, and what is measurable.

QUESTIONS:

1. CAMERA MATCHING. What is the established workflow for recovering a camera from a
single interior photograph — fSpy, Blender's own tools, PhotoMatch, commercial
camera-match tools, or classical single-view metrology? What accuracy do published
evaluations report for focal length and camera position recovered this way, and
what are the documented failure modes?

2. SINGLE-VIEW METROLOGY. What does the computer-vision literature (Criminisi,
Zisserman, and later work) establish about measuring real distances and heights
from one image given a known reference length and vanishing geometry — what error
bounds, and what conditions make it fail?

3. INVERSE GRAPHICS / SCENE RECONSTRUCTION. What is the current state of research on
reconstructing an EDITABLE 3D scene from a single indoor image — including
vision-language-model-driven approaches that emit scene programs or Blender scripts
in staged phases (geometry, then material, then lighting) with a verifier loop per
phase? Name specific papers and their reported metrics. In particular, if you can
find the paper "Thinking in Blender: Staged Executable Inverse Graphics with
Vision-Language Models", report its phase structure, its per-phase round budgets,
its verifier design, the metrics it uses per phase, and the failure modes its
authors report.

4. HOW A MATCH IS SCORED. Which image-similarity metrics are used in this
literature to judge whether a reconstruction matches its reference photograph —
PSNR, SSIM, LPIPS, DINO/CLIP feature similarity, FID — and what do published
evaluations say about which of them correlate with human judgement of "same room"
versus "same pixels"? Critically: which metrics can detect a STRUCTURAL error (a
missing opening, an object at the wrong scale) as opposed to a photometric one?

5. THE FAILURE WE ARE LIVING IN. Is there published evidence about the specific
failure mode where local, region-wise photometric comparison confirms a match while
a large structural error survives? Anything from image-quality-assessment,
change-detection, or reconstruction-evaluation literature about metrics that are
blind to missing or extra objects.

6. STAGED VERIFICATION. In published pipelines that iterate on a reconstruction,
what is the stopping criterion per phase, how many rounds are budgeted, and what
does the verifier get to see? Is there evidence that a monolithic single-pass
approach performs worse than a staged one, with numbers?

7. WHAT A REPRODUCTION EXERCISE SHOULD MEASURE. Is there any published curriculum,
teaching method, or studio training practice for learning archviz by reproducing an
existing photograph — how the exercise is scored, and what students are told to
match first?
