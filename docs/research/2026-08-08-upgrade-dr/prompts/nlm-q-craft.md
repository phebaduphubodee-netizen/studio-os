A dimensionally-accurate interior built from boxes and swept profiles in Blender
still reads as CG rather than as a photograph. Answer for the CRAFT layer, with a
source title per number:

1. EDGES. What bevel/chamfer radii do real interior elements carry — painted MDF
panel edges, veneered panel edges, timber millwork arrises, plasterboard external
corners, door leaf edges, stone worktop arrises? Millimetres per element class.
And what bevel width do archviz practitioners apply in Blender for a camera at
2–6 m?

2. SHADING. Correct practice for shading hard-surface architectural geometry in
Blender 4.x — shade smooth vs shade auto smooth (the modifier that replaced the old
auto-smooth property), the Weighted Normal modifier, and how each interacts with a
Bevel modifier and with n-gons. What goes wrong visually with flat shading and
unbeveled 90° edges, and what goes wrong with smooth shading and no bevel?

3. SILHOUETTE. How many segments does a visible curved profile need before it stops
reading as faceted at 2–6 m? Any rule tied to the arc's pixel width? What polygon
counts do production archviz assets carry for pillow, upholstered chair, table lamp,
curtain panel?

4. CONTACT. What makes an object read as RESTING on the floor in a path-traced
render — contact shadow behaviour, occlusion at the contact line, the dark line at
a skirting? Any guidance on the minimum shadow evidence a believable contact needs?

5. SURFACE VARIATION. Typical roughness-map mean and spread for matte interior wall
paint, lacquered oak veneer, satin powder-coated metal. What do sources say the
"imperfection" layer (dust, fingerprints, micro-scratches, edge wear) actually
contributes — is there any before/after evaluation, or only assertion?

6. RANKING. Do the sources identify WHICH cues most strongly drive the "this is CG"
judgement for interior images, and rank them? Say plainly whether the ranking is
measured or is practitioner opinion.

7. SCORING. Do the sources describe any tool or metric that scores these craft
properties automatically — from the rendered image or from the mesh?
