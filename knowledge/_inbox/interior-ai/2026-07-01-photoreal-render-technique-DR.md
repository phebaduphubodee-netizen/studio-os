## QUESTION DECOMPOSITION — the sub-questions that must be answered.

1.  **Authoritative Sources Identification:** What are the definitive, textbook-grade sources for interior design principles, lighting standards, and rendering techniques that a professional builder can trust?
2.  **Photorealistic Lighting in Blender Cycles:** What are the specific numerical parameters and methodologies for setting up interior lighting (HDRI/IBL, area lights) to achieve a warm, luxurious, and non-CG look, with values for strength, power (watts), and color temperature (Kelvin)?
3.  **Physically-Based Material Properties:** What are the precise Blender Principled BSDF parameter values (Base Color, Roughness, IOR, Metallic, etc.) required to accurately represent common high-end interior materials like warm oak, marbles, boucle, metals, glass, and paint?
4.  **Professional Interior Photography Composition:** What are the standard camera settings (focal length, height, f-stop) and compositional rules for creating a compelling "hero shot" of an interior seating area?
5.  **Color Management for Photorealism:** What is the professional workflow for color management in Blender (AgX vs. Filmic), including settings for exposure and contrast, to produce a warm, high-end final image?
6.  **Essential Scene Composition:** According to interior design principles, what are the minimum necessary elements of "scene dressing" (rugs, plants, etc.) to make a space feel complete and avoid appearing sterile or empty?
7.  **AI Pipeline Integration:** How can these professional standards and numerical values be structured as actionable data inputs, rules, and validation checks for an AI-driven design and drafting pipeline?

## EVIDENCE / FINDINGS

### Lighting for Photorealistic Interiors
Authoritative sources for lighting design emphasize a layered approach to create visual interest, depth, and mood. This is a direct countermeasure to the flat, sterile look common in CG. The key references are the **IES Lighting Handbook** for technical standards and books like Gary Gordon's **"Interior Lighting for Designers"** and Steffy's **"Architectural Lighting Design"** for application principles.

*   **Layered Lighting Strategy:** Professionals use three main layers of light:
    *   **Ambient:** The general, overall light that fills the space, allowing for safe navigation. In Blender, this is often best achieved with a low-strength HDRI/IBL (High-Dynamic-Range Image / Image-Based Lighting).
    *   **Task:** Directed light for specific activities (e.g., a reading lamp, under-cabinet lighting). These are typically represented by spotlights or smaller area lights.
    *   **Accent (or Focal):** Light used to highlight architectural features, artwork, or objects, creating contrast and visual hierarchy. This is a crucial step to avoid a flat look.

*   **Blender 5.x Cycles Lighting Values:**
    *   **HDRI/IBL for Ambient Fill:** Use a high-quality, overcast or soft-sun HDRI. Its purpose is to provide realistic, soft ambient light and accurate reflections.
        *   **Strength:** Keep it low, typically in the range of **0.5 to 1.5**. The HDRI should not be the primary light source, but rather a subtle fill that grounds the scene in reality.
    *   **Primary Light Source (Key Light):** This simulates the main source, like a window or a large ceiling fixture.
        *   **Type:** `Area Light` (set to Quad or Disk).
        *   **Power (Watts):** This depends on the light size and scene scale. A large area light simulating a sheer-curtained window might be **100W to 300W**. A recessed downlight (as an accent) might be **8W to 15W**. Start with real-world values and adjust.
        *   **Color Temperature (Kelvin):** This is critical for warmth. Avoid pure white.
            *   **Warm White (Cozy, Residential):** **2700K to 3000K**. This is the standard for high-end residential and hospitality.
            *   **Daylight from a Window:** Can range from **5000K (cool, direct sun) to 6500K+ (overcast sky)**. A good strategy is to have a slightly cooler "sun" area light (e.g., 4500K) balanced by warmer interior practical lights (2700K). This color contrast adds realism and depth.
    *   **Fill & Accent Lights:** Use smaller area lights, spotlights, or IES profiles for recessed lights.
        *   **IES Profiles:** For maximum realism with downlights or sconces, use IES light profiles from manufacturers (e.g., Philips, Erco). Blender's IES Light node allows for physically accurate light distribution.
    *   **Avoiding the "Sterile-CG Look":**
        *   **Light Color Variation:** Do not make all lights the same color temperature. The interplay between a cooler ambient/key light and warmer practical lights is key.
        *   **Softness:** Ensure area lights are sufficiently large to create soft shadows. In the real world, light is bounced and diffused. Use large, low-intensity lights to mimic this.
        *   **Contrast:** As per Gordon's "Interior Lighting for Designers," visual interest comes from the contrast between light and shadow. Don't be afraid of dark areas. The ratio of brightest to darkest areas (luminance ratio) should be managed. For general spaces, the IES recommends ratios no greater than 20:1.

### Physically-Based Materials (PBR) for Blender's Principled BSDF
The goal is to replicate how light interacts with real-world materials. The values below are starting points for a physically-based workflow. Authoritative data on material properties can be derived from sources like Binggeli's **"Materials for Interior Environments"** and knowledge from 3D art communities on physically-based rendering.

| Material | Base Color (sRGB Hex) | Roughness | IOR / Specular | Metallic | Sheen | Coat | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Warm Oak Wood Floor** | `#A68763` to `#8B6F4E` (Use texture) | 0.3 - 0.6 (texture-driven) | 1.52 (std) / 0.5 (std) | 0 | 0.1 - 0.3 | 0.01 - 0.05 | Use a roughness map for realistic variation between glossy and rough parts of the grain. A slight clear coat can simulate a polyurethane finish. |
| **Honed Marble** | `#EBEBEB` (Use texture) | 0.4 - 0.7 | 1.5 (std) / 0.5 (std) | 0 | 0 | 0 | Honed means it has a matte or satin finish. The roughness is high, diffusing reflections. Subsurface scattering can be used sparingly for high-end realism. |
| **Polished Marble** | `#EBEBEB` (Use texture) | 0.0 - 0.15 | 1.5 (std) / 0.5 (std) | 0 | 0 | 0 | Polished means low roughness for sharp reflections. A roughness map with subtle smudges or wear adds significant realism. |
| **Cream Boucle Upholstery** | `#F5F0E9` | 0.8 - 0.9 | 1.5 (std) / 0.5 (std) | 0 | 0.7 - 1.0 | 0 | The key here is high roughness and high `Sheen` to simulate the soft, fuzzy fabric look. Use a displacement or normal map for the looped texture. |
| **Brushed Brass** | `#B5A642` | 0.3 - 0.5 | N/A | 1.0 | 0 | 0 | Use a procedural or image texture for the brushed pattern, plugged into the Normal or Bump node. The `Anisotropic` parameter can be used to stretch reflections along the brush direction. |
| **Polished Chrome** | `#F0F0F0` | 0.0 - 0.05 | N/A | 1.0 | 0 | 0 | The key is very low roughness and high metallic value for a mirror-like finish. |
| **Clear Architectural Glass** | `#FFFFFF` | 0.0 | 1.52 | 0 | 0 | 0 | For this, you use the `Transmission` property, setting it to **1.0**. The IOR of 1.52 is standard for glass. Add a very slight `Base Color` tint (e.g., a faint green) for thick panes. |
| **Matte Warm-White Wall Paint** | `#F5F3EE` | 0.7 - 0.9 | 1.4 - 1.5 / 0.5 (std) | 0 | 0 | 0 | *Crucially*, do not use pure white (`#FFFFFF`), as it is unnatural and causes energy conservation issues in rendering. A warm off-white is more realistic. High roughness creates the desired matte, diffuse finish. |

### Camera and Composition
Professional interior photography techniques are the benchmark. Ching's **"Interior Design Illustrated"** and Panero & Zelnik's **"Human Dimension & Interior Space"** provide the principles for how spaces are perceived, which informs photography.

*   **Focal Length:** **24mm to 35mm** on a full-frame sensor is the professional standard. Wider than 24mm (e.g., 18mm) introduces distracting distortion. Narrower than 35mm may not capture the scope of the room.
*   **Camera Height:** Position the camera at a natural eye level or slightly lower to make the space feel more accessible and grand. A typical height is **1.0m to 1.2m** (approx. 3.5 to 4 ft) off the floor. This is often the height of a seated person or the mid-point of the main furniture group. Crucially, **keep the camera level** (zero pitch/roll) to avoid converging vertical lines, which looks amateur.
*   **Aperture / f-stop & DoF:** Interior hero shots often aim for a deep depth of field to keep the entire space in focus, mimicking how the human eye perceives the room.
    *   **f-stop:** Use a range of **f/8 to f/16**. This ensures the foreground coffee table and the background elements are all sharp. A shallow DoF (e.g., f/2.8) is an artistic choice used to isolate a single object, but is less common for an overall "hero" shot of a space.
*   **Composition:** Use standard photographic principles. The **Rule of Thirds** is effective for placing the main seating group or focal point off-center. **Leading lines** (e.g., the edge of a rug, flooring direction) can guide the viewer's eye through the scene. The goal is a balanced, inviting composition.

### Color Management for a Luxury Feel
This is a technical aspect of rendering that has a huge impact on the final "feel" of an image.

*   **AgX vs. Filmic:** For Blender 4.x and newer, **AgX** is the recommended color transform. It provides a wider dynamic range and handles extreme brightness and color saturation more gracefully than Filmic, preventing "burnout" in highlights (e.g., a bright window). This is closer to the way a high-end digital camera sensor would capture the scene.
*   **Exposure:** This is the overall brightness control. Adjust it after setting up your physical light values. There is no single correct value; it is an artistic adjustment to achieve the desired mood.
*   **Look (Contrast):** In the Color Management panel, after setting the transform to AgX, you can apply a "Look." A **"Medium High Contrast"** or **"High Contrast"** look can be a good starting point to add punch and separation, which is characteristic of professional photography. Avoid a flat, low-contrast image.

### Minimal Scene Dressing for Realism
To prevent a space from feeling like an empty CG shell, minimal, carefully chosen props are essential. This aligns with principles from Nielson & Taylor's **"Interiors,"** which discusses the importance of accessories in completing a design concept.

*   **Textiles:**
    *   **Rug:** An area rug is essential to anchor a seating group. It defines the space and adds texture and color.
    *   **Curtains/Drapery:** Simple, floor-to-ceiling sheer or linen curtains add softness and diffuse light from windows beautifully.
*   **Life:**
    *   **Plant:** A single, well-modeled plant (e.g., a Fiddle Leaf Fig, Monstera) adds an organic element and a touch of life.
*   **Accessories:**
    *   **Coffee Table Props:** Keep it simple: a stack of two or three books, a small tray, and a single sculptural object or small vase.
    *   **Art:** A single, large, abstract piece of art on a primary wall can serve as a focal point.
*   **Personal Touch:**
    *   **Throw Blanket:** A casually draped throw blanket on a sofa or chair breaks up straight lines and adds a sense of comfort.

## CANONICAL SOURCES

*   **Ching, Francis D.K. "Interior Design Illustrated."** (Various editions).
    *   **Authority for:** Fundamental principles of space, form, scale, proportion, and design elements. Excellent for grounding an AI in the "rules" of good design.
*   **Karlen, Mark, and Christina Fleming. "Space Planning Basics."** (Various editions).
    *   **Authority for:** The functional layout of interior spaces, adjacency diagrams, and circulation paths. Essential for generating logical and usable floor plans.
*   **Panero, Julius, and Martin Zelnik. "Human Dimension & Interior Space: A Source Book of Design Reference Standards."**
    *   **Authority for:** Ergonomics and anthropometrics. This is the definitive source for the dimensions of furniture, clearance requirements, and human scale, critical for creating dimensionally-correct models and layouts.
*   **Nielson, Karla J., and David A. Taylor. "Interiors: An Introduction."** (Various editions).
    *   **Authority for:** A broad overview of the interior design profession, including materials, finishes, and the use of accessories to complete a space.
*   **Binggeli, Corky. "Materials for Interior Environments."**
    *   **Authority for:** Detailed properties of interior materials and finishes, which directly informs the creation of physically-based rendering materials.
*   **IES "The Lighting Handbook."** (10th Edition or newer).
    *   **Authority for:** The technical, scientific standard for illumination engineering. Provides the physical basis for light levels (lumens/footcandles), luminance ratios, and color rendition.
*   **Gordon, Gary. "Interior Lighting for Designers."**
    *   **Authority for:** The practical application of lighting design principles in an accessible way. Translates IES standards into design strategies (layering light, creating mood).
*   **Steffy, Gary R. "Architectural Lighting Design."**
    *   **Authority for:** Advanced concepts in lighting design, including psychological and aesthetic considerations.
*   **Online Blender/Rendering Communities (e.g., Blender Artists, Poliigon, Chocofur):**
    *   **Authority for:** Practical, up-to-date techniques and best practices for implementing PBR materials and lighting setups within Blender's Cycles engine. While not textbooks, these are the *de facto* professional references for software-specific execution.

## SYNTHESIS

To create a photorealistic, warm, luxury interior hero render for a builder using Blender 5.x Cycles, a systematic, physically-based approach is required, grounded in professional design and lighting principles.

First, establish a layered lighting scheme based on the principles from Gary Gordon's **"Interior Lighting for Designers."** Start with a low-strength HDRI (0.5-1.5) for realistic ambient fill. Add a primary `Area Light` simulating a window, with a power of 100-300W and a neutral-to-cool temperature (~4500K). Contrast this with warm interior practical lights (lamps, sconces) set to 2700-3000K, using IES profiles for accuracy. This temperature contrast and the resulting interplay of soft shadows are critical to avoid a sterile look.

Second, construct materials using the Principled BSDF shader with physically-based values. For a warm oak floor, use a detailed texture with a roughness map and a slight clear coat. For polished marble, ensure roughness is near zero (0.0-0.15), while honed marble will be much higher (0.4-0.7). Create cream boucle with high roughness (0.8) and high `Sheen` (0.7-1.0). Metals like brushed brass and polished chrome are defined by having `Metallic` set to 1.0, with their appearance dictated by Base Color and Roughness. Wall paint must be a warm off-white (`#F5F3EE`), not pure white, with high roughness (0.7-0.9) for a matte finish.

Third, frame the shot like a professional photographer. Set the camera's focal length between **24mm and 35mm** and position it at a height of **1.0-1.2 meters**, keeping it perfectly level. Use an f-stop of **f/8 to f/16** to ensure the entire seating group is in sharp focus. Compose the shot using the rule of thirds.

Fourth, configure Blender's color management for a professional photographic output. Use the **AgX** color transform, which handles highlights more naturally than the older Filmic. Apply a **"Medium High Contrast"** look to give the image definition and depth.

Finally, dress the scene minimally but effectively to make it feel inhabited. As per Nielson & Taylor's "Interiors," an area rug to anchor the furniture, floor-to-ceiling curtains to soften the light, a single plant for life, and a few curated coffee table accessories are sufficient to complete the scene without clutter.

## ACTIONABLE FOR AN AI DRAFTING PIPELINE

This research translates into the following concrete specifications for an AI-driven pipeline:

*   **Data Fields for "Deliverable" Specification:** A "render request" must contain fields for:
    *   `mood`: (e.g., "Warm Luxury," "Bright & Airy," "Moody & Dramatic")
    *   `lighting_style`: ("Daylight," "Evening Interior," "Studio")
    *   `camera_angle`: ("Hero Seating Group," "Kitchen Island Detail," "Architectural One-Point Perspective")
    *   `primary_materials`: (List of material types: "Warm Oak," "Polished Calacatta," "Brushed Brass")

*   **Rule-Based Scene Assembly:** The AI should encode rules based on the findings:
    *   **Lighting Rule Engine:**
        *   If `mood` is "Warm Luxury" and `lighting_style` is "Daylight," then:
            *   Create HDRI source: Strength = random(0.5, 1.5).
            *   Create `key_light` (Area Light): color_temp = random(4500, 5500)K, power = random(100, 300)W.
            *   Create `interior_fill` lights (from lamps in model): color_temp = random(2700, 3000)K, power = real_world_watts(e.g., 10W LED).
            *   **Check:** At least two different color temperatures must be used.
    *   **Material Library:** Store materials not just by name, but by PBR parameters. A request for "Brushed Brass" must pull the full parameter set: Base Color `#B5A642`, Metallic `1.0`, Roughness `0.4`, and apply a procedural `Anisotropic` normal map.
        *   **Check:** Wall paint `base_color` value must be <= 240 (sRGB) to prevent pure white.
    *   **Camera Rule Engine:**
        *   If `camera_angle` is "Hero Seating Group," then:
            *   `focal_length` = random(24, 35)mm.
            *   `camera_height` = random(1.0, 1.2)m.
            *   `camera_rotation` = (90, 0, Z), where Z is the viewing angle. Pitch/Roll must be 0.
            *   `f_stop` = random(8, 16).
    *   **Color Management Preset:**
        *   Automatically set Color Management to `AgX` and Look to `Medium High Contrast` for all photorealistic render jobs.

*   **Automated "Completeness" Check (Scene Dressing):**
    *   Before rendering, the pipeline should parse the scene graph and check for the presence of essential dressing elements based on the room type.
    *   For a `living_room`, it should flag a warning if `scene.contains(rug) == false` or `scene.contains(curtains) == false` (if windows exist).
    *   It can suggest adding a `plant` object from a library if the scene lacks any "Organic" tagged assets. This ensures the output meets a minimum professional standard and doesn't look empty.