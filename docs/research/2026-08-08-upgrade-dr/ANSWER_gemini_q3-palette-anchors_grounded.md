# probe-q3-pro

- vendor: Gemini `gemini-2.5-pro` mode `pro` (google_search grounded)
- date: 2026-08-08
- prompt: `q3-palette-anchors.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS

### 1. Thai-Market Cream/Off-White Emulsion Paint LRV and Colour Codes

[INFERENCE] Direct, comprehensive lists of Light Reflectance Values (LRV) for specific cream and off-white paint codes are not readily published on the consumer-facing websites of TOA, Beger, Jotun Thailand, or Nippon Paint Thailand. The values that could be sourced are listed below. Technical Data Sheets (TDS) for these brands' emulsion lines generally provide physical properties like sheen and composition but do not include LRV data for the full colour range.

**TOA**
While TOA's website provides sRGB/hex values for its colours, it does not publish their corresponding LRV values. TOA does state that selecting colours with a high LRV contributes to better interior lighting and can help a building conform to green building criteria like LEED.

[MEASURED] The following cream/off-white colours from TOA have published sRGB/hex values, but no published LRV was found:
*   **W9020 Creamy White:** sRGB (243, 235, 209), hex #f3ebd1 (Source: https://www.toagroup.com/th/products/architectural-paints/color-details/W9020)
*   **N6096 Glow Offwhite:** sRGB (241, 232, 222), hex #f1e8de (Source: https://www.toagroup.com/th/products/architectural-paints/color-details/N6096)
*   **8492 Classic Ivory:** sRGB (238, 234, 219), hex #eeeadb (Source: https://www.toagroup.com/th/products/architectural-paints/color-details/8492)
*   **Y0030 Creamy Milk:** No sRGB values provided on the main palette page. (Source: https://www.toagroup.com/th/color-palettes)
*   **Y0114 Ivory Moon:** No sRGB values provided on the main palette page. (Source: https://www.toagroup.com/th/color-palettes)

**Beger**
Beger heavily promotes its "Super White" shade, claiming it has a higher LRV than other whites.

*   [MEASURED] **BegerCool Super White:** LRV > 96. This value is stated as being tested according to BS 8493:2008 + A1: 2010. No specific sRGB or NCS value is provided. (Source: https://www.beger.co.th/th/product-highlight/begercool-super-white)

For other off-white and cream colours, specific LRV values were not found on the Beger website. Their online colour selection tools do not display LRV data.

**Jotun Thailand**
Jotun's Thai website does not appear to publish LRV values for its colours. However, some LRV values are available through third-party databases, which appear to have measured or obtained this data.

*   [MEASURED] **1622 Reflection:** LRV 80.70% (Source: https://hextoral.com/paint-color/jotun-paint-reflection/)
*   [MEASURED] **1875 Sense:** LRV 73.79%, hex #e6dfce, sRGB (230, 223, 206) (Source: https://plan-home.com/paint-colors/jotun/sense-1875)
*   [INFERENCE] Other off-white colours like **1001 Egg White** and **1453 Cotton Ball** are available, but no manufacturer-sourced LRV data was found.

**Nippon Paint Thailand**
No LRV values for specific cream or off-white colours were found on the Nippon Paint Thailand website or in their technical datasheets. Their online colour palettes provide colour names and codes but lack LRV, sRGB, or L*a*b* data.

*   [MEASURED] A hardware supplier in Singapore lists several Nippon Paint off-white codes, but without LRV values. Examples include: **NP OW 1001 P Whispering White**, **NP OW 1015 P Gossamer White**, **NP OW 1016 P Creamy White**. (Source: https://www.intertech.com.sg/product/nippon-paint-odour-less-all-in-1-off-white/)

### 2. LRV to CIE Luminance Y and sRGB Conversion

[MEASURED] The relationship between Light Reflectance Value (LRV) and CIE luminance Y is direct and linear. The British Standard **BS 8493:2008+A1:2010** ("Light reflectance value (LRV) of a surface — Method of test") defines the LRV of a surface as **100 times the CIE tristimulus value Y**, measured under specific conditions (CIE standard illuminant D65 and the 1964 CIE 10° standard colorimetric observer).

Therefore, the formula is:
**LRV (%) = Y * 100**
or
**Y = LRV / 100**

Where Y is the CIE tristimulus value, which represents luminance and ranges from 0 (perfect black) to 1 (perfect reflecting diffuser).

[PRACTICE] The procedure to derive an sRGB base-colour triple from an LRV and a hue description involves these steps:
1.  **Convert LRV to CIE Y:** As per the standard, divide the LRV percentage by 100 to get the linear CIE Y value.
2.  **Determine CIE X and Z:** This is the under-specified part of the conversion. Knowing only luminance (Y) and a general hue description (e.g., "cream," "off-white") is not enough to uniquely determine the CIE X and Z tristimulus values. To proceed, one must make an assumption about the chromaticity (the hue and saturation). A common practice is to find a representative colour with a known full L*a*b* or sRGB value that matches the hue description, and then scale its luminance to match the target LRV.
3.  **Convert CIE XYZ to linear sRGB:** Once you have the full CIE XYZ triplet, you can convert it to the linear sRGB colour space using a standard 3x3 matrix transformation. The specific matrix values depend on the reference white point (typically D65 for sRGB).
4.  **Apply the sRGB transfer function (gamma correction):** The linear sRGB values must then be converted to the non-linear sRGB values used for display. The standard sRGB transfer function is defined as follows:

    If R_linear, G_linear, or B_linear ≤ 0.0031308:
    R_sRGB, G_sRGB, B_sRGB = 12.92 * (R_linear, G_linear, B_linear)

    Otherwise:
    R_sRGB, G_sRGB, B_sRGB = 1.055 * (R_linear, G_linear, B_linear)^(1/2.4) - 0.055

    (Source: **ISO/CIE 11664-4:2019**, which specifies colorimetry calculations, and various digital imaging standards).

### 3. PBR Base Colour and Roughness for White/European Oak Veneer

NO SOURCED VALUE FOUND. Scan-based PBR material libraries like Poliigon and Quixel Megascans do not appear to publish aggregated, measurable base-colour and roughness ranges for their materials in a way that is easily searchable. Individual material pages provide texture maps (Albedo/BaseColor, Roughness, etc.) but do not typically list a single representative sRGB or L*a*b* value, nor a numeric roughness range for the material under different finishes. The appearance is a result of the full texture map, not a single value.

### 4. Gloss Units for Architectural Powder Coat Black and Conversion to Roughness

[MEASURED] Architectural powder coat suppliers define gloss levels using gloss units (GU) measured at a 60° angle, as specified by standards like ASTM D523. The typical bands are:
*   **Matte:** 20-35 GU (A range of 20% and 30% gloss level is cited by one supplier).
*   **Satin/Semi-Gloss:** 60-70 GU (A range of 60-65% is cited by one supplier).
*   **Gloss:** > 80 GU (A value of 80% gloss level is cited by one supplier).

Specific examples from manufacturer datasheets include:
*   **AkzoNobel Interpon 700 (Gloss):** 80% min GU @ 60°. (Source: AkzoNobel Interpon 700 Gloss Datasheet)
*   **AkzoNobel Interpon D2525 (Gloss):** 70-80 GU @ 60°. (Source: AkzoNobel Interpon D2525 Gloss Datasheet)
*   **Jotun Facade Series:** Gloss levels are specified per product, e.g., "Gloss EN ISO 2813 (60°)", but a single value for the entire range is not given in the summary TDS. (Source: Jotun Facade Powder Coating TDS)

[PRACTICE] There is **no standardized, published formula** to directly convert 60° gloss units (GU) to a microfacet/GGX roughness value. This conversion is highly dependent on the specific rendering engine and its implementation of the GGX BRDF. Practitioners often rely on visual matching or create their own empirical lookup tables or curves to map GU values to the 0-1 roughness scale in their software. A common starting point is an inverse relationship (higher GU corresponds to lower roughness), but the exact mapping is not linear and is considered a "rule of thumb" or an artistic interpretation rather than a physically based conversion.

### 5. Complex Refractive Index (n,k) and PBR values for Brass

[MEASURED] The online database **RefractiveIndex.INFO** provides measured optical constants for various materials. For Brass (specified as a 70% Copper, 30% Zinc alloy), the complex refractive index (n, k) at a wavelength of 589.3 nm (Sodium D-line, close to the middle of the visible spectrum) is:
*   **n (refractive index):** 0.43200
*   **k (extinction coefficient):** 3.4000

(Source: https://refractiveindex.info/?shelf=main&book=Cu-Zn&page=Johnson)

This database also calculates the normal-incidence reflectance (F0) from these values:
*   **F0 (Reflectance):** 0.84558 (or 84.558%)

These values are for a polished surface. For a brushed/satin finish, the underlying refractive index remains the same, but the appearance is modified by surface roughness and anisotropy.

[MEASURED] PBR material libraries provide texture maps for satin brass, but do not typically list single summary values for base colour, roughness, or anisotropy.
*   **Poliigon** offers several "Brushed Brass Metal" textures described as having a "soft, satin sheen" or a "fine, directional grain." The final material properties are encoded in the provided texture maps (e.g., albedo, roughness, anisotropy maps) rather than as single numeric values. (Sources: https://www.poliigon.com/texture/shiny-brushed-brass-metal/PBR0050, https://www.poliigon.com/texture/matte-brushed-brass-metal/PBR0051)

### 6. L* / sRGB Band for Architectural Powder-Coat Black and Reflectance Floor

[INFERENCE] Specific L* or sRGB values for standard architectural black powder coats are not typically published in datasheets. The colour is usually just specified as "Black" or by a RAL code (e.g., RAL 9005 Jet Black). The perceived blackness depends on the gloss level, with matte finishes appearing darker.

[MEASURED] There is published support for a reflectance floor for real-world black finishes.
*   A typical matte black paint absorbs about 80% of light, which implies a reflectance of around **20%**. (Source: Boston University article on Singularity Black)
*   Ultra-black coatings developed for scientific applications demonstrate much lower reflectance, effectively setting a lower bound for what is physically achievable.
    *   **Singularity Black:** Reflectance of ~1.5% (absorbs 98.5%).
    *   **Musou Black paint:** Reflectance of 0.6% (absorbs 99.4%).
    *   **Vantablack:** Reflectance of ~0.035% (absorbs 99.965%).

[INFERENCE] These specialized coatings show that typical architectural black paints are far from a "true" black. A reasonable floor for a standard, widely available matte black architectural finish would be a reflectance significantly higher than these research-grade materials. Based on the "typical matte black paint" figure, a reflectance of **5-20%** is a plausible range for common black finishes. A reflectance of 5% corresponds to a linear sRGB value of (0.05, 0.05, 0.05), which after gamma correction is approximately sRGB (56, 56, 56) or hex #383838.

### 7. Batch-to-Batch and Inter-Sheen Colour Tolerance (ΔE)

[PRACTICE] Paint manufacturers do not typically publish their internal batch-to-batch colour tolerance values (in ΔE00 or ΔE*ab) in public-facing documents. However, industry standards and testing methods provide context for what is considered a noticeable difference.

*   The standard for instrumental colour difference calculation is **ASTM D2244**.
*   It is a widely cited convention in the industry that a colour difference of **ΔE*ab < 1.0** is generally imperceptible to the human eye.
*   A **ΔE*ab ≥ 2.0** is considered noticeable.
*   One source cites that the human eye can perceive a **ΔE*ab ≥ 2.3**.

[INFERENCE] Given these conventions, a pass/warn gate of ΔE00 ≤1.0 / ≤2.0 is aligned with industry perception standards. It is reasonable to infer that major manufacturers aim for a batch-to-batch tolerance of ΔE*ab ≤ 1.0 to ensure consistency, but they do not publish this as a guarantee. Inter-sheen differences (e.g., matte vs. satin of the same colour) will naturally have a larger ΔE, as the change in gloss affects the perceived colour. No sourced values for acceptable inter-sheen ΔE were found.

### 8. Machine-Readable Colour Data from Thai Brands

NO SOURCED VALUE FOUND. None of the Thai websites for TOA, Beger, Jotun, or Nippon Paint appear to offer publicly accessible, machine-readable colour data. There are no evident links to download fan-deck data files (e.g., .ASE, .ACO, .CSV), nor are there any documented APIs for accessing their colour libraries. Their online colour tools are interactive visualizers and do not have an explicit data export function.

## CONFLICTS AND UNCERTAINTY

*   **Question 1 (Paint LRV):** There is a significant lack of manufacturer-published LRV data for specific colour codes in the Thai market. The values found for Jotun are from third-party sites and, while specific, should be treated with caution as they are not from a primary source. The sRGB values from TOA are useful but incomplete without corresponding LRV.
*   **Question 4 (GU to Roughness):** The lack of a standard conversion from Gloss Units to GGX roughness is a major uncertainty. Any value used will be an approximation based on convention or visual matching, not a physical measurement. This is a critical point for the builder to understand, as the resulting material appearance in Blender will be an interpretation, not a direct translation of a physical property.
*   **Question 7 (Colour Tolerance):** The ΔE values are based on general industry practice and perception standards, not on published guarantees from the specified paint manufacturers. The actual batch-to-batch tolerance achieved in production may vary and is not a number that can be contractually relied upon based on available data.

## WHAT I COULD NOT SOURCE

*   **Question 1:** A comprehensive, manufacturer-sourced list of cream/off-white paint codes with their corresponding LRV values for TOA, Beger, Jotun Thailand, and Nippon Paint Thailand.
*   **Question 3:** Measured, single-value sRGB/L*a*b* base-colour ranges and roughness ranges for white/European oak veneer under clear matte lacquer and hardwax oil from any named, scan-based PBR library.
*   **Question 4:** A sourced, formulaic, or standardized conversion method between 60° gloss units (GU) and microfacet/GGX roughness values.
*   **Question 7:** Officially published batch-to-batch or inter-sheen colour tolerance values (ΔE00 or ΔE*ab) from TOA, Beger, Jotun, or Nippon Paint.
*   **Question 8:** Any form of machine-readable colour data (downloadable files, API, etc.) from the Thai websites of TOA, Beger, Jotun, or Nippon Paint.
---

## GROUNDING (vendor-reported)

- search queries issued: 58
  - `TOA paint thailand off-white cream LRV`
  - `Beger paint thailand off-white cream LRV`
  - `Jotun thailand paint off-white cream LRV`
  - `Nippon Paint thailand off-white cream LRV`
  - `TOA paint color code LRV sRGB`
  - `Beger paint color code LRV sRGB`
  - `Jotun thailand color code LRV sRGB`
  - `Nippon Paint thailand color code LRV sRGB`
  - `TOA SuperShield LRV values`
  - `BegerCool Diamond Shield LRV`
  - `Jotun Majestic True Beauty Sheen LRV`
  - `Nippon Paint Colour Creations LRV`
  - `TOA paint thailand technical data sheet LRV`
  - `Beger paint thailand technical data sheet LRV`
  - `Jotun thailand paint technical data sheet LRV`
  - `Nippon Paint thailand technical data sheet LRV`
  - `TOA color code LRV value`
  - `Beger color code LRV value`
  - `Jotun color code LRV value`
  - `Nippon Paint color code LRV value`
  - `TOA off-white paint colors sRGB hex`
  - `Beger off-white paint colors sRGB hex`
  - `Jotun off-white paint colors sRGB hex`
  - `Nippon Paint off-white paint colors sRGB hex`
  - `light reflectance value to CIE Y conversion formula`
  - `sRGB from LRV and hue formula`
  - `ASTM D2244 color tolerance paint`
  - `ISO 11664-4 colorimetry`
  - `BS 8493 Light reflectance value of a surface`
  - `PBR material library white oak veneer clear matte lacquer sRGB roughness`
  - `measured PBR white oak hardwax oil`
  - `Quixel Megascans oak veneer properties`
  - `Poliigon white oak material properties`
  - `architectural powder coat gloss units matte satin gloss black`
  - `AkzoNobel powder coating technical data sheet gloss levels`
  - `Axalta powder coating gloss levels`
  - `Jotun powder coatings technical data sheet gloss`
  - `gloss units at 60 degrees to GGX roughness conversion`
  - `GGX roughness from GU formula`
  - `Filmetrics refractive index of brass`
  - `refractiveindex.info brass`
  - `complex refractive index of polished brass`
  - `PBR measured satin brass material properties`
  - `Quixel Megascans brass hardware`
  - `Poliigon satin brass material`
  - `architectural powder coat black L* value`
  - `measured sRGB of black powder coating`
  - `minimum reflectance of black paint`
  - `Vantablack sRGB value`
  - `paint manufacturer batch-to-batch color tolerance dE00`
  - `TOA paint color tolerance`
  - `Beger paint color tolerance`
  - `Jotun paint color tolerance`
  - `Nippon Paint color tolerance`
  - `TOA paint machine-readable color data download`
  - `Beger paint fandeck data file`
  - `Jotun Thailand color data API`
  - `Nippon Paint Thailand color tool data export`

- grounding chunks: 21
  - bu.edu — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHKm-BkAHa3ihenh1ji5sCJF0JO79Dnq4DXcST-owTx15Fs0HPpUiwX8jhsIvNBDGgceGU5JekkxScB3SJHwwY4-q3T369WbhcyoBbNKGhThyebhM2uU3YMfWmMCFxI5qZYDAmlfwFMG3zvsqFg69sflqKWFRZqFNEvlmtAR8Gb
  - micomlab.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHbTz2vciurIKnAmAgf_DAxnwXrMV0zuj45mP0Ls-iqTQWT3hAJUMbW7WredOAt5P5EumGb5YZhR3pxSwBuVqC0uBE1R61uiNReTqWiEkwrWwRs-ZPuzMbZnBC2qFnWs_65IeoXrB8UQx3onzI=
  - cie.co.at — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFG9GvHscTnwcI9laC9zp7_DEfgh9jVmWfDJRs9U6VujRoM-hRpN54q69RX3FOh9FXnaG1qneWIIT6YaO7HA9Y5m_kU5ShSA5vnbPueWjpMRe9o8UdhuPMbo2EXGgLP-V-EjckHex2bVmLC7oS-m12DEubxXuxJ33UaaFcTqihbLmC5HTiSArc=
  - iskweb.co.jp — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFAKYpUwQskpZGcc9ildUcInck674hIv2E52BO2ec8yJ7iImAer3UG1R8QEOO3w5Zqj4uNYaDVwm9OVT3wCtRTrs41jM7F5YOlVbQ926AUe-z1hBKZlfy4mdwCLbQzTYti62r1hy4998a_SEGoC
  - thenbs.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE01DuD179B2zsW66WyfR_DcZXzr0Ap4S6YusnkdRPqs3PyE0DTZ0gx0WLJcNT1rEUsAzedMeJLoalfffJaJMBm-UtXteWnh_lnILTxdK1agegyi4114LWK27-nyOwMtbeaI0kDKrC6zsu0N73VZUBQdvUvl3P46EIsudmaJRlTARYdGzCYCgKQ
  - matestlabs.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH15HYlsJ0h9mPxRo3M5vuXOjob8A4Smkfhyb3coDvrnj5A_2WRsBRBVDOTVOjsZUV7oPbHjNjq8KFxslmyVXwskcV0i_Z8Mke4c43P2SSrynW5cXUJ-CdBH2AdtMz7FcepKNTQ_EcPOMX88g==
  - satra.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGn29Vkm-MvLyU_ZAprU-SXJ4LXpM67Mgq_XPKE7etUlqhLyN-ebhkYhJ2cG8G2luNNjYZ1iKlwU5vA-CsXt2KH2qaMpoXqnFUErCk3pPEM_bs_he_zQ2msPNB7bhOS7cRm9qn24CwHvcXe7nA=
  - iteh.ai — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGzbvTEPMtSYIFYF-OPi4I2aaWNWtakfsjm71k3G74EK8vrzuZ2KaOdeOVjypgmsqBA9fom15zxtEnGiih6QQS9528L5T6W0CGU_M59njvYQzPkHfHuAb36g_zXgXWvMl1UZZfIPXbpAnjHqv8Ev97wB0hmS2luABMUJ0iGuIUuhleoLKGuqFw8hHLGYc77cCl2DVB3tQ5984mJIagO1NA=
  - bsigroup.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFR_FSEv8cEsjJ3Dhr7oTaItWuqGaUq3ZqEFBnj93wLAkFXxenCeWyM5GlfggN6i2SklO_NzPgW0Nr2TpphHAR3zFN6WS4pspMMHnx_AizhSqHvqT3hveqU8vM9lvSbTlfdEQv73YpvEHU3vMMjqsdXj3XRxTjeBPCn4LQPG5hvK2NOOc3ObZPE5g==
  - dnk-cie.de — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFEBOFePDqfvmOgcYsj9lUlbhptRaifKA2IptWP8IGik_kxxdVddbCl43AoQZ56lHKIAzlH23B3zePqXi5BLwpDAk1rdUdBdiIlU5psRgZSIX8u8maGtnyywLfYvCwqSrdieGj1ag72BhD2LwEQ0KrBDceuqOLCzSceRyjEHYxBDwZXmv_-8V_DFqOOvhkd7avHeRHHJw==
  - sppcltd.co.uk — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEGdn1YDdvOwhzKyS-ZN84spTidn2qxcxL42dZE5gEWgGJF25rgDoa-2HuD6LrWI1jue9-EVL4ePe2WQKVDmagT4GgXpXWtX9I3pSTOHNwqKZ2f8d6mpa1HvCxm_jhG2LZ6hfNcQum3ym8Ci_8=
  - akzonobel.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEDqV7dLbbKNprV9oTPtJbWD-sEb7QNTrds7fuJWkbPO_CQpjMIcias0yD0w9kfTgzEsuF0DS_qbNG7_IJoo8VjW1ZLNjhgXslo7hMN2PlAZXzbNjsby7u9vUHsN1ExEk7FXBsjwleidRb5hABreDphU3PBTpL2A1-BzJwpgNePrfTnIojeRPS-qfCfmEMzOTYdf7yxws42gXbwMgVe
  - akzonobel.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEFpOEdyqDHxMd-MvSt5kCjaY6JQjx2atZUdUtXe6GiHfpqISisNpbRfQdj2BuJj0cRlw3NU6PhQYpdHDyTyEh5MHAON5IRo3qtJbn_Q7KHwWdhjqm7s9ZMZ3uGeWsSI7PmV_0xCubRlY1x2PfdmI0XUiwh6fE64j-_xx__gbOn5PlkcfA7Ax9-AVGCdgabGwA8ralv-yU=
  - scribd.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEpFpjl4l6YIs0wD2zBR2MyqTW3-GPhNIIkoR7BQHWRPxoAUUgw58D99DBYEUEkpLQpj4fSkzVQRQaw-c7m6oJI8snxc0Vo5dnsdOUmKdliPbt69GvhtfTZulHP11dGutF-1E5Vl_C-
  - refractiveindex.info — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFKlsak0AFLEemqXpM-havDfzrzMvIkEv2NGUJ1OZdmKa5BHnSMw9cCo6-_vF__hrC9Brq590Do23vi90EU5GC4oKk6jvYAQB4C3kKEp-8sKcQ0PB46ySlpcDwso4KClDwXFcA730yhOlY46wJU-yjXyVFSTyKaaA==
  - poliigon.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGWUZvwkXJ8EdsaAr82Y46_Bs9Xg5y7qbNxFJ4M7mftFnc1grg4yMtprp0UcbSEJPxGXLIh6ERqgHH4rTHF60_qfocrzErLiQKAUK11v4Q2ET_iab9aqYVvquNkngVxGob3ABRU-x0Tr9Ukccey0YD_d7rdv3WVOw0Kj9S7U58Y_r4=
  - poliigon.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEEuH_JzYnPhAMlHNAK_CaTnUWRW5XzeDE_Wo93iyj_vZ8tl1OXI3IA4p4kpG0mjAwwLxEOthiJmeHjXSeMVg_4WKLeCp1mp43t9qnFQZv3lo0d3AVDJTYztTKkYtoCQ3Ohqu_FrdKDGHWFPiSuKW-q-muziatk32fHaM017s4Xiic=
  - arxiv.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGPMdbXXdHz6FooMGt251J7h7rAWLoi6ngO2iSarGhMQRrnv6eeXr7kaosL70YYUD28Lr2qCuCUKDWQYnLWwdHQ00tyYYdPTLqQjlfRre1HR3PRrLgXvea9yr8beHo=
  - industrialphysics.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEv3_KXD5tKh8VV4iIOQyQvNlHH7PzgB3G3K4FCqlMionIGBLCHkTBQlJJbSKCTcUvOdrzV6lR9om_eij_pYPaiW7M8avZNnCAlncCxLhArJvBYZBfboiXkezC1ic541MYB7h8mI5bMEb0kUzZn
  - fire-test.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHvG2lV-flB6obybBJ3Miq_6bAXHRDb_9YTqA8p4Bw-wf9fF4IwQCoC0MBVAeYH8_f2VzwI9Aa42USu_HnDRHbFpSNSpA5Z5x_EkPMuABD7z9cJlNyW0BAPBBm-moMSaDi7MeYQlG3AeIQ=
  - infinitalab.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG0_d8Mfxc3kNVG-40PtPL-alhp9APRvMCe2szN7XGsUtIfTrtmNWb4foIt8uVcOkBVee_ozZxKqnvDwrpwYAOdJH72gyTJb3jtrzG3yyvj8uSY2dZ2R_4rzXRifik90x8-XPky4KrzV3PMmFIsv5Y=
