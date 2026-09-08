CONTEXT: A small archviz team builds interior rooms procedurally in Blender/Cycles
from measured dimensions — walls, millwork, wardrobe runs, bed bases, doors — using
box primitives with radii and swept profiles. The geometry lands dimensionally
accurate to within a few millimetres, and the frame still reads unmistakably as CG
rather than as a photograph of a built room. The team's instruments score pixel
LEVEL and pixel DISTRIBUTION against a reference; they score nothing about craft,
so craft defects survive every round.

I need the measurable craft layer: what a photoreal interior has that a
dimensionally-correct box model does not.

QUESTIONS:

1. EDGE TREATMENT. What bevel/chamfer/fillet radii do real architectural interior
elements actually carry — painted MDF panel edges, veneered plywood panel edges,
solid-timber millwork arrises, plasterboard external corners with corner bead,
door leaf edges, stone/quartz worktop arrises? Give radii in millimetres per
element class with sources (millwork/joinery standards, AWI/WI/AWMAC quality
standards, manufacturer fabrication guides). Separately: what bevel width do
archviz practitioners apply in Blender for camera distances of roughly 2–6 m, and
is there any published guidance relating bevel width to pixel size at the camera
rather than to the real-world radius?

2. SHADING AND NORMALS. What is the current correct practice in Blender 4.x for
shading hard-surface architectural geometry — shade smooth vs shade auto smooth
(the modifier that replaced the old auto-smooth-angle property), the Weighted
Normal modifier, and the interaction of each with a Bevel modifier and with
n-gons? What specifically goes wrong visually when a hard-surface mesh is left
flat-shaded with unbeveled 90° edges, and what goes wrong when smooth shading is
applied without either a bevel or weighted normals? Cite Blender manual sections
and named practitioner sources.

3. SILHOUETTE RESOLUTION. For a curved profile that is visible in frame at roughly
2–6 m — a rounded bed-base corner, a cylindrical lamp body, a bullnose edge — how
many segments does a curve need before the silhouette stops reading as faceted?
Is there any published rule tied to the subtended pixel count of the arc? What
polygon-count bands do published production archviz assets carry for common
interior items (pillow, upholstered chair, table lamp, curtain panel)?

4. CONTACT. What makes an object read as RESTING on a floor rather than floating
or intersecting, in a path-traced render — contact shadow behaviour, ambient
occlusion at the contact line, the dust/shadow line at a skirting, gap tolerances
in real construction? Is there published guidance on the minimum shadow evidence a
believable contact needs?

5. SURFACE VARIATION. What do published archviz material breakdowns say about
per-pixel variation in roughness and base colour on architectural surfaces —
typical roughness map mean and standard deviation for matte interior wall paint,
lacquered oak veneer, satin powder-coated metal? What is the measured contribution
of "imperfection" layers (fingerprints, dust, micro-scratches, edge wear) — is
there any published before/after evaluation, or is it only assertion?

6. THE HONEST QUESTION. Is there any published, quantitative work — perceptual
studies, VFX/archviz technical papers, image-quality metrics literature — that
identifies which cues most strongly drive the human "this is CG" judgement for
INTERIOR images specifically, and ranks them? If the ranking exists only as
practitioner opinion, say so plainly and give the strongest such sources rather
than dressing opinion as measurement.

7. SCORING. Does any published tool or metric score the craft properties above
automatically from a rendered image or from the mesh itself — e.g. edge-sharpness
statistics, silhouette faceting detection, normal-map/curvature analysis, mesh
quality checkers used in production pipelines? Name the tools and what exactly
they measure.
