# Build vocabulary — what the interpreter can execute

You design a furniture build as a JSON plan. The interpreter executes EXACTLY
these operations in Blender; anything else fails the build.

## Operations (one per component)

1. `box_round` — a box with rounded edges and an optional upholstery crown.
   Fields: `size_mm [x,y,z]` (x = width across the piece, y = depth
   front-to-back, z = height), `bevel_mm`, `bevel_segments` (2-4),
   `crown_mm` (raises the top face INTERIOR in a smooth dome, edges stay
   straight — use for cushions), `subsurf` (0/1/2 — smooths everything; needs
   bevel first to hold edges), `taper_bottom_frac` (0.05-1.0 — scales the
   BOTTOM face toward its centre; 0.55 makes a leg whose foot is ~55% of its
   top width — use for tapered legs).
2. `extrude_profile` — a measured 2D outline extruded straight.
   Fields: `profile_mm` = closed polyline `[[a,b],...]` (8-16 points),
   `profile_plane`: `"xz"` = SIDE silhouette (a=x width-direction, b=z height),
   extruded `depth_mm` along y (front-to-back); `"yz"` = FRONT silhouette
   (a=y, b=z) extruded along x. Plus `bevel_mm`, `bevel_segments`, `subsurf`.
   This is how a ROLLED ARM is made: its side silhouette as a polyline
   (the roll drawn as 5-8 points of the curve), extruded to the arm width.
3. mirror — `mirror_of: "<component>"`, `mirror_about: "<component>"`:
   an instance of an existing component reflected about the x-centre of
   `mirror_about`. The mirrored copy takes no other geometry fields.

## Placement — derived, never typed (hard law)

Every non-mirrored component MUST carry:
- `rest_on`: `"floor"` or a component name — its bottom sits on that top.
- `x_anchor` and `y_anchor`: `{ref: "<component>"|"origin", ref_face:
  "min"|"max"|"center", own_face: "min"|"max"|"center", gap_mm: <number>}` —
  this face of me sits at that face of the ref, offset by gap_mm (signed,
  along +axis). There is NO position field. An unknown ref fails the build.
  x = width axis (viewer's left→right = min→max), y = depth (front = min).

## Materials
`material_hint`: "fabric" (default, charcoal) or "wood/leg" (dark legs).

## Budget and bar
Target ≤ ~8,000 triangles after subsurf (the interpreter prints the count).
The bar is the reference photo: proportions, arm shape, cushion read —
"looks intentionally created", not "good enough".

## Measuring rule
State ONE assumed overall dimension (e.g. overall width 2030 mm for a
standard 3-seater) and derive every other number from the photo BY MEASURED
PROPORTION against it — say what you measured (pixel ratios) for each major
dimension. Never invent a number you did not derive.
