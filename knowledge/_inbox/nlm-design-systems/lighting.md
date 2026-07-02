# Residential lighting: CCT/TM-30 + layering + Birn render principles
> PROVENANCE: NotebookLM notebook "Design Systems and Integration Protocols Interface"
> (a5a43395-e085-4fe6-a46c-4a8f7b438cc2, 118 sources), asked 2026-07-03.
> STATUS: secondary summary grounded in the notebook's book/standard sources —
> REFERENCE tier, NOT Authority. Numbered [n] citations refer to notebook sources
> (full Q&A in qa-history.json). File to: knowledge/lighting/ after human review.

Here is the information regarding residential lighting standards and photoreal 
lighting principles based *only* on the provided sources. 

Please note that while the sources confirm that the Illuminating Engineering 
Society (IES) publishes detailed recommended illuminance criteria in clear 
tables [1], the excerpts provided **do not contain the specific lux levels, 
exact layering ratios, or detailed CRI guidelines** you requested. Similarly, 
while Jeremy Birn’s *Digital Lighting and Rendering* is extensively referenced,
the excerpts only provide high-level summaries of his techniques rather than 
detailed definitions of "motivation" or "exposure discipline."

### **A. Recommended Residential Lighting Standards**

The available data from the sources regarding residential lighting targets is 
summarized below:

| Space / Task | Recommended Illuminance (Lux) | Correlated Color Temp (CCT) | 
Color Rendering Index (CRI) / TM-30 |
| :--- | :--- | :--- | :--- |
| **General Residential Spaces** | *Not specified in sources* | **2200K – 
3000K** (Warm atmosphere) [2] | High R9 values required for rendering reds [2]*
|
| **Specific Rooms (Living, Dining, Kitchen, Bedroom, Bath, Corridor)** | *Not 
specified in sources* | **2700K** is noted as a typical warm residential 
incandescent source [3] | *Not specified in sources* |
| **Task Lighting (Reading, Vanity, Counter)** | *Not specified in sources* | 
*Not specified in sources* | *Not specified in sources* |

*\*Note: The sources mention that the modern TM-30 metrics (Color Fidelity/Rf 
and Color Gamut/Rg) have largely replaced the outdated CRI system to ensure 
colors look natural and appropriately saturated [2].*

***

### **B. Core Lighting-Design Principles for Interiors**

**Ambient, Task, and Accent Layering**
A convincing, photorealistic interior requires a carefully balanced hierarchy 
of lighting, though the sources do not provide specific mathematical ratios for
this balance [3]:
*   **Ambient Light:** Provides the overall fill illumination for the room [3].
*   **Task Light:** Directed lighting used for focused utility and specific 
activities [3].
*   **Accent Light:** Used specifically for highlighting architectural features
or artwork [3].

**Jeremy Birn’s Principles for Photoreal Rendered Lighting**
Based on the provided summaries and indexes of Birn's *Digital Lighting and 
Rendering*, his approach to digital illumination involves the following core 
concepts:
*   **Photographic & Cinematic Mimicry:** Renderings must simulate real-life 
camera optics, utilizing natural color temperatures (Kelvin), f-stops, exposure
times, lens breathing, and bokeh effects to achieve photorealism [4, 5]. 
*   **Three-Point Adaptation:** The foundational setup involves adapting 
traditional lighting elements—specifically the **key light, fill light, and 
backlight**—to the 3D environment [6]. 
*   **Exposure & Shadow Management:** Birn emphasizes strict control over 
post-processing exposure values, shadow softness, and the mimicking of 
photographic exposure to manage the visual structure of the scene [5, 7].
*   **Linear Workflow & Compositing:** For convincing lighting and global 
illumination, scenes should be broken into distinct passes and layers (such as 
highlight passes) and managed through a linear workflow before being composited
into real-world environments [5, 6].
*   **Advanced Rendering Techniques:** Achieving photorealism requires the use 
of physically based lighting, subsurface scattering, caustics, and High Dynamic
Range Images (HDRI) [5].
