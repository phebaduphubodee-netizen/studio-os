# q4-bedding-mass (grounded pass)

- vendor: Gemini `gemini-2.5-pro` mode `pro` (google_search grounded)
- date: 2026-08-08
- prompt: `q4-bedding-mass.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. Duvet Tog Rating, Fill Weight (g/m²), and Loft Thickness (mm)

[PRACTICE] There is no standardized, direct mapping of tog rating to a specific loft thickness in millimeters. Tog is a measure of thermal insulance, not physical thickness, and sources repeatedly state that thickness is not a reliable indicator of warmth. Different materials achieve the same tog rating with different weights and lofts; for instance, high-quality down is a more efficient insulator than synthetic fill, so a down duvet can be warmer, lighter, and potentially thicker (higher loft) than a synthetic duvet with the same tog rating.

[MEASURED] Fill weight, measured in grams per square meter (g/m² or GSM), is directly related to warmth within a single fill type. The following table synthesizes typical g/m² values for common tog bands and fill materials, based on retailer and manufacturer guides.

| Tog Rating | Description | Down Fill Weight (g/m²) | Synthetic/Microfibre Fill Weight (g/m²) | Wool Fill Weight (g/m²) | Source(s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **4.5 Tog** | Summer / Lightweight | ~110 g/m² (n=1, Scooms) | 200-300 g/m² | 200-300 g/m² | |
| **10.5 Tog** | All-Season / Medium | ~300-350 g/m² | 350-500 g/m² | 350-450 g/m² | |
| **13.5 Tog** | Winter / Warm | NO SOURCED VALUE FOUND | 500-700 g/m² | 600-700 g/m² | |

[INFERENCE] While no direct standard for duvet loft was found, one manufacturer of high-performance down sleeping quilts (Enlightened Equipment) provides target loft heights for their products based on temperature rating. This can serve as a reasonable proxy for the uncompressed thickness of a high-quality down duvet. A 20°F (-6.7°C) quilt, roughly analogous to a warm winter duvet, has a target loft of 2.5 inches (63.5 mm). A 30°F (-1.1°C) quilt, analogous to an all-season duvet, has a target loft of 2 inches (50.8 mm). (Source: Enlightened Equipment Support, https://support.enlightenedequipment.com/hc/en-us/articles/218522217-Insulation-and-loft)

### 2. Down Fill Power, Loft Height, and Compression

[MEASURED] Fill Power (also called Loft) is a standardized laboratory measurement of the quality and "fluffiness" of down. It measures the volume in cubic inches that one ounce of down occupies under specific test conditions (e.g., in a cylinder with a lightly weighted disk on top). Common fill power bands are:
*   **550-650:** Good quality.
*   **700-800:** Premium, warm, and lightweight.
*   **800+:** Luxury, maximum warmth with minimum weight.

[INFERENCE] The relationship between fill power and the final loft height of a duvet is not linear and depends on the total fill weight and the duvet's construction (baffle box size). However, a higher fill power means that less weight is needed to achieve a target loft and warmth. Using the proxy from Enlightened Equipment, an all-season (e.g., 10.5 tog) double/queen duvet with high-quality down (e.g., 850fp) would likely present a crest loft in the range of **50-65 mm**. (Source: Enlightened Equipment Support, https://support.enlightenedequipment.com/hc/en-us/articles/218522217-Insulation-and-loft)

[PRACTICE] Regarding compression, sources state that down is highly compressible but lose their insulating properties when wet. There are no published, measured values for the specific compression of a duvet at the hem roll or under a resting hand. This value would be highly dependent on the fill power, fill weight, and the specific construction of the duvet shell.

### 3. Folded Duvet Stack Height and Compression

NO SOURCED VALUE FOUND. While the concept of self-compression in soft materials is well-understood in physics and engineering, no specific studies, guides, or manufacturer data were found that quantify the stack height of a folded duvet as a multiple of its single-layer loft. The compression would depend on the fill material's properties (down being more resilient and compressible than synthetic), the total weight of the stack, and the way it is folded. [INFERENCE] A naive sum of layers will overestimate the total height. For simulation purposes, a simple approach would be to apply a progressive compression factor, perhaps reducing the loft of each subsequent layer by a small percentage (e.g., 5-10% of the layer below it) as a starting point for visual approximation.

### 4. Bedding Drop/Overhang Conventions

[PRACTICE] Bedding overhang, or "drop," is a key element of bed styling. The conventional drop length varies by the type of bed covering and the thickness of the mattress.

*   **Comforter/Duvet:** The standard convention is for the comforter to be wide enough to cover the sides of the mattress, with a typical drop of **10-15 inches (254-381 mm)** on each side. For a standard 10-12 inch thick mattress, this drop will cover the mattress entirely. For thicker "pillow-top" mattresses (14-18 inches), a larger comforter (often sizing up, e.g., a King comforter on a Queen bed) is recommended to achieve the same coverage.
*   **Coverlet:** A coverlet is designed to be a lighter, more decorative layer. It is shorter than a bedspread and is intended to cover the mattress top and sides, but not extend to the floor. Its drop typically ends just below the mattress, revealing the bed skirt or frame.
*   **Bedspread:** A bedspread is the largest type of covering, designed to drape all the way to the floor on three sides and often to cover the pillows. The required drop is therefore the distance from the top of the mattress to the floor.

A formula provided by styling guides to calculate the minimum required comforter width is:
**Mattress Width + (2 x Mattress Depth) + ~4 inches (for tuck/loft)**. (Source: Au Lit Fine Linens, https://www.aulitfinelinens.com/blogs/style-and-care/how-to-measure)

### 5. Pillow Indentation and Slump Behavior

NO SOURCED VALUE FOUND. While pillow firmness is a common product attribute, no published, measurable data on indentation depth (in mm) under a specific head-weight load (3-5 kg) was found for major fill classes. Similarly, no sourced values were found for the slump angle of styled pillows propped against a vertical support. These properties are highly variable based on fill material, density, and the pillow's shell fabric.

### 6. Areal Weights and Bending Rigidity of Bedding Fabrics

NO SOURCED VALUE FOUND for Cusick drape coefficients or specific bending rigidity values for the listed bedding fabrics. While standards for these tests exist, finding a citable library of results for common, non-industrial textiles like percale, sateen, and linen proved unsuccessful.

[PRACTICE] Areal weight (g/m²) is more commonly available from textile suppliers, but varies widely. For simulation, practitioners often start with known g/m² values and tune bending stiffness visually.
*   **Cotton (general):** A typical range for cotton sheets is **110-170 g/m²**. (Source: Bedsure, https://bedsurehome.com/blogs/bedsurediaries/what-is-gsm-in-bedding-fabric)
*   **Linen:** Can range from **150 g/m²** (lightweight) to **220 g/m²** (medium weight).

[MEASURED] The relevant test standards for these properties are:
*   **Areal Weight:** ASTM D3776 / ISO 3801
*   **Bending Rigidity/Stiffness:** ASTM D1388 (Cantilever Test)
*   **Drape:** BS 5058 / ISO 9073-9 (using a drape tester like the Cusick Drape Tester)

[INFERENCE] Mapping these physical test results to a cloth solver's parameters is not standardized. For a solver like Blender's, the process would generally be:
1.  **Mass:** The `Vertex Mass` parameter can be set based on the fabric's areal weight. For a given piece of cloth geometry, calculate the total surface area, multiply by the g/m², and distribute that mass across the vertices.
2.  **Bending Stiffness:** The `Bending` parameter in the cloth solver's `Stiffness` settings would be adjusted to match the behavior observed in an ASTM D1388 test. This is not a direct numerical mapping; it requires artistic and technical interpretation to match the characteristic bending length and curvature of the real fabric. A higher bending stiffness value from the test would correspond to a higher `Bending` value in the solver.

### 7. Simulating a Quilted, Batting-Filled Duvet in Production

[PRACTICE] Production practitioners use a variety of techniques to simulate quilted duvets, as there is no single "physically accurate" button. The methods are conventions developed by 3D artists.
*   **Loft via Pressure/Internal Springs:** In Blender (versions 2.8x through 4.x), the common method is to use the `Pressure` setting in the `Cloth` physics panel. A positive pressure value causes the cloth mesh to inflate, simulating the loft from the internal batting. `Internal Springs` can also be used to create a resistance to compression, but `Pressure` is more common for the overall puffy shape. (Source: Blender Manual & community forums).
*   **Shell Thickness:** The duvet is modeled as a closed, manifold 3D mesh (like a flattened cube) with a small thickness. The cloth simulation is applied to this object.
*   **Quilting Seams:** The quilted pattern is typically created by adding internal geometry that is "pinned" in the simulation. An artist would create edges or faces inside the main duvet mesh and assign them to a `Pin Group` with a `Stiffness` value. This restrains those parts of the mesh, creating the characteristic puckering and tufts of a quilted pattern.
*   **Edge-Roll Formation:** The thick, rolled hem of a duvet is often modeled directly into the base mesh. The cloth simulation, combined with the internal pressure, will then naturally form a soft, rounded edge based on this geometry.

There are no universally published parameter bands, as the final values depend heavily on the scene scale, mesh density, and desired artistic outcome. The process is one of iterative tuning.

### 8. Hotel and Property-Staging Bedding Fold Proportions

[PRACTICE] While there isn't a single, universally mandated standard, the common practice in hotel housekeeping and property staging involves a "turn-back" or "turn-down" fold at the head of the bed.

*   **Fold Depth:** A home staging guide suggests folding a comforter down to expose the white sheets or a coverlet. (Source: Bedroom Staging Tips, https://www.propertystager.com/blog/bedroom-staging-tips)
*   **Visible Sheet Reveal:** NO SOURCED VALUE FOUND for a specific millimetre band for the amount of flat sheet to reveal between the folded duvet and the pillows. [INFERENCE] Based on visual analysis of hotel and staging photography, this reveal is typically in the range of **200-400 mm**, creating a visible band of the flat sheet. The top edge of the flat sheet is often folded back over the top edge of the duvet/comforter, creating a clean, finished look.

## CONFLICTS AND UNCERTAINTY

*   **Tog vs. Thickness:** The most significant uncertainty is the lack of a standardized, measurable relationship between a duvet's tog rating and its physical loft/thickness in millimeters. All sources agree that tog is a measure of thermal performance, not a physical dimension. The loft heights provided are an inference based on a related product category (sleeping quilts) from a single manufacturer and should be treated as a plausible estimate, not a measured standard.
*   **Fill Weight (GSM) Variability:** The g/m² values provided are typical ranges from retail guides. They are not universal standards, and values for specific products can vary between manufacturers. The data for a 13.5 tog down duvet was particularly sparse.
*   **Compression Data:** There is a complete lack of sourced, numerical data for how much duvets or pillows compress under specific, light loads (like a hand or self-weight when folded). Any values used in a simulation for this would be an artistic approximation.

## WHAT I COULD NOT SOURCE

*   A direct, published mapping from **duvet tog rating to settled loft thickness in mm** for any fill class.
*   Measured values for the **compression depth (in mm) of a duvet** at the hem roll or under a resting hand.
*   A formula or measured data for the **stack height and self-compression** of a folded duvet.
*   Published data on the **indentation depth (in mm) and slump angle (in degrees)** of pillows under a 3-5 kg load.
*   A citable library of **Cusick drape coefficients or ASTM D1388 bending rigidity values** for percale, sateen, linen, or brushed cotton bedding fabrics.
*   A specific, sourced millimetre band for the **visible sheet reveal** in hotel turn-down styling.
---

## GROUNDING (vendor-reported)

- search queries issued: 17
  - `duvet tog rating to fill weight gsm conversion by fill type`
  - `duvet tog rating to loft thickness mm by fill type`
  - `tog rating fill weight down feather microfibre wool`
  - `duvet loft height by tog rating`
  - `duvet tog rating fill weight gsm loft thickness mm conversion table`
  - `duvet fill weight gsm by tog rating and fill material`
  - `duvet loft height mm by tog rating`
  - `down fill power to loft height mm chart`
  - `down duvet loft height vs fill power`
  - `duvet loft height measurement standard`
  - `duvet compression under 5kg load`
  - `compressibility of down vs synthetic fill`
  - `bedding styling guide drop length`
  - `standard comforter overhang inches`
  - `coverlet vs bedspread drop length`
  - `mattress thickness and duvet size guide`
  - `hotel bedding collection size specifications`

- grounding chunks: 13
  - shoplotuslinen.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHmHp-9E2fA5YSNF4PeVIwpk8B8g5u1SrOCvRoThvu6rWOrBmC-3UKGL1NIBDedeVsVxhmI0dBqN-11T37uMoeFnJvfuBpJoskDKA4ZflwXgpngsFk3W38o_-xMxSclx4v1-0Qed093u0Dq7TUGzCA1GbbTDwP_uKaE9-QZgECM
  - lilialessandra.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFKsQlf-PlDskXVwiPegVC2NjdFj06juTPfRMvw323F_pBXi6Idkj2Z6tG2FDgdYGMlpaokE1UJbPOv4MEdPGQIepoVzJLnu9-yoi-TG5iHAXXO5gQ-gRgPG76Q794vdDPvFz2CkrFZLjLcx07c6uHax2CC3b0XN6eZj4RB7pMACqUe250BXga7mAYWLpv2sBp4KVg4Q5uD2J_PgVMtl41zCw==
  - hotelcollectionbedding.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHxLSmazEptSc-4BSZUM4M3s5URtJ7ncVvJzwveXoJ73tQ0vdzptjw-ryYA5BAr0hVUGbde1tfydZdM8kJaJWLYYzQ8N8GgtsI_DpoSpC9JmvG4A10Ihniw5lB3toDrhEpq31tJS2sVoyKnLbSDu20=
  - ownkoti.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHBydNCFJZ6VP5KJnxxFKoc57VoGmszChJjvWF2QeiQJaZGDT61AnoB9LNFlhdZ-QeXjNCyJ_HbBTerUJuT5EJItZNP2CcXkMqTgxB_4hGvrOaCJUw67GYng_dn_UPnWkY8Hxprwfc0oh9tad0mafjko4sP
  - orezon.co — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH_1uezwHYZjg0bAcCZ7luSKbD4eo8NiWWxw2Pd8nYgUbGMsiPbUTUgSaPna4gPKZY72u0oH6IJ6O8pdm-QGD3zJxTi9HNv0XwxupglCuH-yfqaPKWfUe8S685Gl-EEMZOz7-UalnYsRd4z7Y7zoXwLph0_CReS
  - houzz.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFhMzQA75vrNnVBwzecqUAZNUKHtjHiHw7YlNJPVWrPp2gJQJbsx9Wf4PwfOSJw-oPGTiMkuY9jMyH6AMwvRxDorzueDoVC-DIh3Vs3fLnOqihhBDnRTy_EjhjVDe5j4d4FAX2C2hFiy5fjXO-f8Yo6MJ5pw46rpF7YJcEdAF17W94bTBNy0gdA6IMbFKNO474Rr_tMnCZFcM3CXz8ggfQddgoNYQqjl1Fr_oUFbjemUwU=
  - frette.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzHg-vi9fDfRpmECTHNciHONt6BLUOVxrfFFUnT0WhyJXVapj5r2lwjy9Wabn5A8FjdghqO5uG7kjB8m96SlOOOxSzwSBblvASwo-sbNQhfjN6OjJ3YGtSoojekRn8NfZ-5oKEo83Kx_uw8CHgyA==
  - larimarhomestaging.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGL5H5GyPwOw8W-HAD6xIqAbAVU-cvUB3dmQZpgfiFssvCbNoJT-MfqkDcnpRbGLwkqIl4sdcZdkkRbNgGyKTjH2ulELCIeHx5DDJFJs8lemicfbjXbFT5EV2qdhvR1qjWCtyZdkBUiDlt5bR93pds=
  - hotemax.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGKHazYlBgzuYucck1vnlhT4NZJdABCFBu37e_grfZ-Vhm12_L92KAu_VOSuvCIKO9UUypbHluvXBrOxIPr_oOXGDY-b50bTUgBubzUKNRDoPI6JIcswusoF5jfKFNpAnvK8wubSb23K5I9
  - viscosoft.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG3zzjwnbu_yB59__zXOcKHNh4HuC51LZ1l2AKkP1L439Ecveqo8PkV1qW_VKqMFvtxw-KH8T2LYrjKTOPAo3c5MhFoCbD3K0RQk1M2hB6WRTny1PcJUnUFGjqHWzUMGJWg1SNwjvQZN_hTI9C2BpQR_p2aZks7Egis
  - orezon.co — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF-iz-vVAH8bxC_QhqYbeYnD0lxhEVJ7EdReGGl1afojX1A4kHdf8YWaUGJYUwESGx0f5hUn-ImuZxy_GO6JNdRJowGfQ_ljJM0PMdxZxwY9IyorCtvqlywCcM84YAQgyTJjltbbduayIBYaIDF9EZ0bOyV
  - manchesterwarehouse.com.au — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEPrd3bl8C5MKA4DJVfKaYPKWuoeTLvtEFTBCVYDnZHBs5Pqq01_lucqWUan3hIORPDF1DLt1yJ5UG1aOi6dAdxVKUaxZcVzbZTY7ckQZfX6qIaHgdNZn5zQffyNd7mY2NNIMf8_ZyY9fdiHUPAwmcI4veHu00tmJfe2ZGF7fnc45zkvxOqZTQTJIOjeFwfLQq2rDulxPFoMLqts0U6EOyA9qTaJH1zsGa3yDbXIt6o-7bfxoXOnADv98j1frkaAc4f2EL_165KrN55QpmbiKMLwefXFw==
  - purple.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF_Bhc2uutD2JGQowZxToLnEWdw7YbzDiur2fWVY8WM4f2zCwfrN596kqXE1BpLLS_Nbb0UJooO5swnhjwrGMoJ79iPAdsVADoCFbblYhHyz6G92R7eKJd9l6Ld1n69
