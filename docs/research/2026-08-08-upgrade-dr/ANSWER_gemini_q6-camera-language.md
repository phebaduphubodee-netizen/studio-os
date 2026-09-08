# q6-camera-language

- vendor: Gemini `gemini-2.5-pro` mode `deep` (google_search grounded)
- date: 2026-08-08
- prompt: `q6-camera-language.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. Focal Lengths (35 mm equivalent) by Room Type and Size

**Real Estate / Listing Photography (Wider Angles)**
*   **General Interiors:** 14mm to 20mm on full-frame cameras is what most professionals use [PRACTICE] (Real Estate Photography Atlanta, 2025).
*   **General Interiors:** A wide-angle zoom in the 16-35mm range for full-frame cameras, or a 10-18mm equivalent for APS-C sensors, is what nearly every working real estate photographer relies on [PRACTICE] (Amplifiles, 2026). One professional cites using a Canon 17-40mm f/4L for 95% of their residential real estate work [PRACTICE] (SLR Lounge, 2019).
*   **Bathrooms:** A lens with a 24-35mm focal length works well to show both space and details [PRACTICE] (Phixer Blog, 2024). Another source suggests a 16-35mm wide-angle lens is ideal for capturing an entire bathroom in one shot [PRACTICE] (Virtually Anywhere, 2024). To get everything pivotal in a bathroom, you may need to shoot as wide as 16mm or 17mm [PRACTICE] (Invision Studio, n.d.).

**Architectural Visualization (Tighter, More Naturalistic Angles)**
*   **General Interiors:** An archviz artist recommends avoiding focal lengths shorter than 30mm, often using something between 35mm to 55mm to avoid the distortion that is "criminally abused in arch-viz" [PRACTICE] (Ronen Bekerman, writing for Architizer, 2014).
*   **General Interiors:** For interior renderings, a 40-80mm focal length is commonly used [PRACTICE] (AIMIR CG, 2020).
*   **V-Ray Specific Guide:** A guide for V-Ray rendering recommends specific focal lengths by shot type: 24mm for a full room overview in a tight space, 35mm as the standard for most shots (closest to natural vision), and 50mm for "hero" shots focusing on a single object or piece of furniture [PRACTICE] (Blog, "How to Get Accurate Focal Length In Rendering for Interior Design," 2026).

**Furniture / Product-in-Situ Photography (Standard to Telephoto)**
*   **Furniture:** To maintain natural proportions and avoid distortion, standard or slightly telephoto lenses (e.g., 50mm or 85mm) are recommended [PRACTICE] (Robbie Ewing, 2025). Another guide recommends a 24mm or 35mm prime lens, or a tilt-shift lens for best results [PRACTICE] (Orbitvu, 2023).

### 2. Camera Height Above Finished Floor

**General Rules & Sourced Bands**
*   **Chest Height / 1.2–1.5 m Band:** Most professional real estate photographers recommend placing the camera between 4 and 5 feet (1.22–1.52 m) from the floor [PRACTICE] (Real Estate Photography Atlanta, 2025; PFRE, 2021; Vertex AI Search, n.d.). This is often described as "chest height" [PRACTICE] (Real Estate Photography Atlanta, 2025) or "from the heart" [PRACTICE] (Rob Moroto, cited in Vertex AI Search, n.d.).
*   **Mid-Point Rule:** An alternative convention is to place the camera exactly halfway between the floor and the ceiling to theoretically avoid distortion [PRACTICE] (Vertex AI Search, n.d.; YouTube, "Real Estate Photography Masterclass," 2025).

**Room-Specific Adjustments**
*   **Kitchens:** Set the camera height at 1.25 to 2 feet (0.38–0.61 m) above the counter height [PRACTICE] (PFRE, 2021). Another guide suggests "chest height or slightly lower to avoid seeing the underside of cabinets" [PRACTICE] (Mastering Architectural Photography, 2025).
*   **Bathrooms:** Set the camera height at 1.25 to 2 feet (0.38–0.61 m) above the counter height [PRACTICE] (PFRE, 2021). One guide suggests shooting from "waist height to avoid a cramped look" [PRACTICE] (Phixer Blog, 2024).
*   **Bedrooms:** Have the camera height 1.25 to 2 feet (0.38–0.61 m) above the height of the bed [PRACTICE] (PFRE, 2021). For beds specifically, one guide suggests shooting from 3 feet (0.91 m) above the floor [PRACTICE] (Valyou Hawaii, 2021).
*   **Living Rooms / Rooms with Furniture:** For living areas, shoot from a seated height ("waist level") to make the viewer feel like they are in the room [PRACTICE] (Mastering Architectural Photography, 2025). For living rooms in general, a height of 3-4 feet (0.91–1.22 m) is suggested [PRACTICE] (Valyou Hawaii, 2021). For very low furniture, a photographer noted going as low as 1.5 to 2 feet (0.46–0.61 m) to give the furniture a "sense of presence" rather than looking down on it [PRACTICE] (Jason Krider, for Davey's Imaging Group, 2020).

### 3. Conventions for Vertical Shift / Horizon Placement

*   **Keeping Verticals Parallel:** The "single most important element" that separates professional architectural photography is aligning verticals so they are parallel to the picture plane (i.e., not converging) [PRACTICE] (Steven Brooke, 2023). This is achieved by keeping the camera sensor plane perfectly vertical [PRACTICE] (Photo.net forum, 2003).
*   **Mechanism of Shift:** To achieve parallel verticals while framing a shot, the convention is to keep the camera back (sensor) straight and use the rise/fall movement of a tilt-shift lens or view camera (or the digital equivalent) to adjust the composition up or down [PRACTICE] (Photo.net forum, 2003). The camera is raised or lowered to the desired height, leveled, and then shift is applied to frame the shot without tilting [PRACTICE] (DPReview Forums, 2018).
*   **Digital Shift Limits (Archviz):** In V-Ray, it is a convention to never use camera tilt. Instead, one should use the "Vertical Tilt (Lens Shift)" correction. A stated limit is that a lens shift value above 0.2 can begin to stretch the foreground noticeably [PRACTICE] (Blog, "How to Get Accurate Focal Length In Rendering for Interior Design," 2026).
*   **Horizon Placement:** NO SOURCED VALUE FOUND for a specific convention on where the horizon line should fall in the frame (e.g., lower third, center). The primary rule is to keep the camera level, which places the horizon line in the vertical center of the perspective projection.

### 4. One-Point vs. Two-Point Perspective Selection Criteria

*   **One-Point (Straight-On):** A one-point perspective is used for "straight-on" angles, particularly for symmetrical spaces [PRACTICE] (Real Estate Photography Atlanta, 2025). It is chosen when the subject is "head on" relative to the viewer and the goal is to emphasize "one thing or straightness" [PRACTICE] (Graphic Design Stack Exchange, 2015).
*   **Two-Point (Corner View):** A two-point perspective is the more common and "normal" situation for interiors [PRACTICE] (Graphic Design Stack Exchange, 2015). It is generally preferred for eye-level interior and architectural images because it aligns with how the human brain perceives space [PRACTICE] (McNeel Forum, 2017). It is used to create a more three-dimensional world in the image compared to the flatter look of one-point perspective [PRACTICE] (Study.com, n.d.). Corner angles using a two-point perspective typically make rooms appear larger because they show two walls and increase visible depth [PRACTICE] (Real Estate Photography Atlanta, 2025).
*   **Yaw Angle Band:** NO SOURCED VALUE FOUND that quantifies the yaw angle separating a one-point from a two-point view. The choice is described based on composition and subject matter rather than a specific numerical angle.

### 5. Listing/Marketing vs. Editorial/Portfolio Register Differences

*   **Lens/Framing:** [INFERENCE] Based on the focal length data in Question 1, the LISTING register prioritizes showing the entire space and its layout, favoring wider focal lengths (16-24mm). The EDITORIAL register prioritizes mood, detail, and a curated viewpoint, favoring more naturalistic or compressed focal lengths (35-85mm).
*   **How Much of Room is Included:** [INFERENCE] The LISTING register aims to include as much of the room as possible to be informative to a potential buyer, often shooting from a corner to show three surfaces (two walls and a floor/ceiling). The EDITORIAL register is more selective, often using tighter framing, vignettes, or straight-on shots that might only show one or two walls to focus on a specific design element or composition.
*   **Height:** [INFERENCE] While both registers follow the general rules of keeping verticals straight, the LISTING register may more consistently use a standard "chest height" to quickly and efficiently capture a property. The EDITORIAL register may use more deliberate and varied heights (e.g., very low shots of furniture) to achieve a specific compositional effect.
*   **Straight-on vs. Angled:** [INFERENCE] The LISTING register heavily relies on angled, two-point perspective shots from corners to maximize the sense of space. The EDITORIAL register makes more frequent use of straight-on, one-point perspective shots for their formal, graphic, and often symmetrical quality, especially when highlighting a specific piece of furniture or architectural feature.

### 6. Orientation and Aspect Ratio per Medium

*   **MLS Listings:** The majority of MLS photos should be in landscape (horizontal) orientation [PRACTICE] (HomeJab, 2023). The most common aspect ratios are 4:3 and 3:2 [PRACTICE] (PropertyPixel, 2026; RoomLift AI, 2026).
*   **Print / Portfolio:** A 4:5 ratio has been commonly used for photographing architecture and can give status to images [PRACTICE] (Place Photography, n.d.). Magazines and printed marketing materials also tend toward 2:3 or 4:5 ratios [PRACTICE] (Safelight Imaging, 2025).
*   **Social Media (Instagram):** A vertical 3:4 format is recommended whenever possible for interior photography, as the taller crop occupies more screen space on a mobile device [PRACTICE] (Stacy Markow, 2025). Instagram Reels and Stories can expand to fill a 16:9 vertical screen [PRACTICE] (Safelight Imaging, 2025).
*   **Fine Art / Formal:** A square 1:1 aspect ratio brings formality and symmetry to an image and is commonly used in fine art photography [PRACTICE] (Place Photography, n.d.).

### 7. Quantitative Signatures of Amateur vs. Professional Images

*   **Convergence of Verticals:** The single most-cited differentiator is that professional architectural and interior photos have verticals that are parallel to the frame, while amateur photos often have verticals that converge ("falling over backwards" look) due to the camera being tilted up or down [PRACTICE] (Steven Brooke, 2023). NO SOURCED VALUE FOUND for a specific tolerance in degrees.
*   **Barrel Distortion:** Amateurs may use lenses that are "too wide," such as a fisheye, which visibly distorts the edges of the photo [PRACTICE] (Drench, 2021). Professionals use high-quality wide-angle lenses and apply lens correction profiles in post-production to minimize this effect [PRACTICE] (Building Photography Guide, n.d.). NO SOURCED VALUE FOUND for a specific quantitative threshold of distortion (e.g., a percentage).
*   **Ceiling and Floor in Frame:** This is controlled by camera height and lens choice. While professionals are deliberate about it, there is NO SOURCED VALUE FOUND that gives a quantitative signature (e.g., "amateur photos show >50% ceiling"). The choice is contextual. For example, a lower camera height intentionally includes more floor and less ceiling to emphasize furniture [PRACTICE] (Real Estate Photography Atlanta, 2025).
*   **Subject Placement:** [INFERENCE] Based on composition guides, professional work is more likely to adhere to compositional rules like the Rule of Thirds or use axial (one-point) composition for stability [PRACTICE] (Steven Brooke, 2023; Architizer, 2014). Amateur work may have less intentional subject placement. This is difficult to quantify automatically.

### 8. Published Datasets Measuring Camera Parameters

*   **DataSeeds.AI Interior Design Dataset:** A dataset of over 330,000 high-quality interior design images from photographers is available. The dataset description explicitly states it "includes full EXIF data, detailing camera settings such as aperture, ISO, shutter speed, and focal length" [MEASURED] (DataSeeds.AI, n.d.; Databricks Marketplace, 2026).
*   **InteriorNet Dataset:** This is a mega-scale *synthetic* dataset of 20 million images rendered from 22 million interior layouts created by professional designers using 1 million CAD models. While not from real photographs, it represents a massive corpus of professionally designed interior scenes where camera parameters would be known and could be analyzed [MEASURED] (InteriorNet, 2018).
*   **Northern Architectural Spaces Dataset:** A scientific dataset published in a peer-reviewed journal contains high-dynamic range (HDR) panoramic images of 7 interior and 6 exterior settings. While the focus is on photobiological lighting analysis, the capture methodology is documented and the raw image data exists for analysis [MEASURED] (PMC, 2022).

## CONFLICTS AND UNCERTAINTY

*   **Focal Length:** There is a significant conflict between the conventions of real estate photography (which favors wide angles like 16-24mm to show space) and architectural visualization/editorial photography (which favors more naturalistic 35-55mm lenses to avoid distortion and create a specific mood). The choice is register-dependent.
*   **Camera Height:** There is no single rule for camera height. The "4-5 feet" (1.2-1.5m) rule is a general starting point, but it conflicts with the "midway between floor and ceiling" rule in rooms with very high or low ceilings. It also conflicts with more specific advice to shoot lower (waist or seated height) to create a more intimate feel or to properly frame furniture. The height is highly situational.

## WHAT I COULD NOT SOURCE

*   **Horizon Placement Rule:** I could not find a sourced, measurable convention for where the horizon line should be placed within the frame (e.g., "in the lower third"), beyond the general principle of keeping the camera level.
*   **Yaw Angle for Perspective Choice:** I found no source that provides a quantitative yaw angle in degrees that dictates when a one-point perspective view becomes a two-point perspective view. The decision is described purely in compositional terms.
*   **Quantitative Amateur/Pro Thresholds:** I could not find any source that provided a specific, measurable threshold to define an image as "amateur." For example, there was no value for "more than X degrees of vertical convergence" or "more than Y% of barrel distortion." The distinction is described qualitatively.
*   **Floor/Ceiling Percentage:** I could not find any source that dictates a "correct" percentage of the frame that should be occupied by the floor or ceiling. This is treated as a compositional choice dependent on camera height and the subject of the room.
---

## GROUNDING (vendor-reported)

- search queries issued: 33
  - `professional interior photography focal length by room type`
  - `architectural visualization focal length standards`
  - `real estate photography lens recommendations`
  - `what focal length for small bedroom photography`
  - `best lens for living room architectural photos`
  - `kitchen interior photography focal length`
  - `bathroom photography lens choice`
  - `interior photography camera height standards`
  - `real estate photography camera height above floor`
  - `photographing furniture camera height`
  - `architectural photography camera height conventions`
  - `bathroom vs kitchen camera height photography`
  - `architectural photography vertical shift conventions`
  - `tilt-shift lens interior photography guide`
  - `horizon placement interior photography`
  - `one-point vs two-point perspective interior photography criteria`
  - `compositional guidelines for interior photography one-point perspective`
  - `when to use two-point perspective in architectural visualization`
  - `yaw angle interior photography one-point vs two-point`
  - `editorial vs listing interior photography style`
  - `architectural digest vs MLS photo style`
  - `framing and composition for marketing vs portfolio interior photos`
  - `interior photography aspect ratio for print vs web`
  - `MLS photo aspect ratio requirements`
  - `instagram aspect ratio for interior design`
  - `vertical vs horizontal orientation interior photography`
  - `quantitative analysis of professional vs amateur interior photography`
  - `measuring vertical convergence in photos`
  - `barrel distortion correction interior photography`
  - `how much ceiling and floor in interior photos`
  - `dataset of interior photography EXIF data`
  - `analysis of camera parameters in professional architectural photography`
  - `corpus of interior design photos with camera settings`

- grounding chunks: NONE REPORTED — treat every number here as unsourced until verified by hand.
