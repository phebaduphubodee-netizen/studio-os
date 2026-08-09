CONTEXT: A studio has ruled that free-form objects (figures, plants, cut flowers,
drapery, upholstery, food) must be ACQUIRED rather than hand-modelled — hand-built
free-form geometry has cost five or six rounds each and still only approximates.
The rule is decided; what is missing is the practitioner mechanics of acquiring and
INGESTING an asset so it is usable and correct, and the tooling for it. Licences
must permit commercial use of the render; that constraint is settled and is not the
question here.

QUESTIONS:

1. What do working archviz studios actually use as asset sources today, ranked by
what a professional would reach for first — 3D Warehouse, Poly Haven, BlenderKit,
Quixel/Fab, Chaos Cosmos, paid libraries, manufacturer BIM/3D portals? For each,
what is the practical quality of the geometry (topology, polycount, UVs, scale
correctness) and what cleanup does it typically need?

2. SCALE. What is the established procedure for asserting that an imported asset is
at real-world scale — what goes wrong per format (SKP, FBX, OBJ, glTF, USD) with
unit systems, and how do practitioners verify rather than assume? Is there any
automated check published (a script, an addon, a validator) that flags an asset
whose bounding box is implausible for its class?

3. TOPOLOGY AND CLEANUP. What is the standard cleanup sequence for a downloaded
model destined for a still render — n-gon handling, normals, doubled vertices,
shading, material replacement, decimation? Which steps actually matter for a still
image at 2–6 m camera distance, and which are cargo-culted from animation/game
pipelines?

4. FORMAT. What is the current practitioner consensus on which interchange format
survives a round trip best for archviz props, and what specifically breaks in each?
Include what happens to materials and textures per format.

5. AUTOMATION. What published tools or scripts exist for programmatic asset search
and import into Blender — Poly Haven's API, BlenderKit's API, Fab/Quixel access,
3D Warehouse's programmatic access and its terms — and what are the real
constraints (auth, rate limits, headless usability)?

6. LIBRARY DISCIPLINE. How do studios organise an asset library so an asset is
found again — naming conventions, Blender asset browser catalogues, tagging,
metadata sidecars? Name the conventions that are actually published (studio
pipeline talks, published naming standards) rather than invented.

7. THE HONEST TEST. Is there any published comparison of hand-modelled vs acquired
props in finished archviz work — time cost, quality, and when practitioners say
modelling it yourself is still correct? What classes of object do professionals
still model by hand?

8. For plants and greenery specifically — the class most often called out as a
realism failure — what do practitioners use (scanned libraries, generators like the
Grove/Graswald/Botaniq, procedural), and what is the published guidance on
polycount and instancing for interior plants in a still render?
