CONTEXT: A Blender/Cycles interior pipeline builds materials procedurally from a
small parameter set — base colour, roughness, metallic, emission. It has NO
transmission, NO coat, and NO IOR handling at all. Consequently every glazed
element in the scene is faked as an opaque light or white surface: a frosted-glass
partition door, a dressing-table mirror, a wardrobe mirror panel, window glazing.
The frosted partition and the mirror are both first-order elements of the frame.

I need what is required to make these read correctly, with sourced numbers.

QUESTIONS:

1. FROSTED / ACID-ETCHED / SATIN GLASS. What are the published optical properties
of architectural frosted, acid-etched, sandblasted and reeded glass — visible light
transmittance (%), haze (%), and the difference between one-side-etched and
two-side-etched? Cite glass manufacturer datasheets by name and give per-product
values. What visible-light transmittance band should a 6–10 mm satin/acid-etched
interior partition panel be modelled at?

2. MODELLING FROSTED GLASS IN CYCLES. What is the correct current construction in
Blender 4.x Principled BSDF for acid-etched glass — transmission weight, IOR,
transmission roughness vs surface roughness, thin-walled vs solid geometry, whether
the panel must have real thickness, and how the "rough transmission is slow and
noisy" problem is handled in production (light path settings, caustics flags,
blurry-refraction approximations, or substituting a translucent/mix setup). Cite
the Blender manual and named practitioner sources, and state which advice predates
the 4.x Principled rewrite.

3. WHAT A FROSTED PANEL LOOKS LIKE PHOTOMETRICALLY. When a camera sees a lit room
through an acid-etched partition, what happens to the visible image — at what
etch/haze level do object silhouettes behind it stop resolving, how does the
apparent brightness of the panel relate to the brightness of the room behind it,
and does the panel read brighter or darker than an adjacent white-painted wall
under typical interior lighting? Any measured or published values, not intuition.

4. MIRRORS. How is an interior mirror correctly built in Cycles — metallic vs
glossy BSDF, the base colour of real silvered mirror glass (published reflectance
of silver-backed float glass, typically quoted around 90–95%: give the sourced
value), the greenish tint of float glass, the secondary reflection from the front
surface, and the frame/bevel? What are the common failure modes that make a
rendered mirror read as a white or emissive panel rather than a mirror?

5. CLEAR GLAZING AND WINDOWS. For window glass seen from inside a lit room, what
do practitioners actually build — real glass, a shadow-catching invisible plane, or
nothing at all — and what are the published trade-offs for interior renders
(reflection of the room in the glazing, light portals, noise)? Give values: float
glass IOR, low-E coating effect on visible transmittance, typical VLT bands for
residential glazing with sources.

6. GLASS AND LIGHT TRANSPORT. What Cycles settings materially change the quality
and cost of glass in an interior — caustics (reflective/refractive per-object
flags), light path bounce counts for transmission, "filter glossy", and portals?
Give the recommended interior-render values from named sources and say which cost
what in render time.

7. VERIFICATION. How would one verify from a rendered image alone that a glass
material is behaving physically — measurable checks (transmitted vs incident
luminance ratio, reflection at grazing angle, Fresnel behaviour across the panel)
that could be automated as a test rather than judged by eye?
