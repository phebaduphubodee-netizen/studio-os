# q8-photo-match-verification (grounded pass)

- vendor: Gemini `gemini-2.5-pro` mode `pro` (google_search grounded)
- date: 2026-08-08
- prompt: `q8-photo-match-verification.md` (archived beside this file)
- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.
## ANSWERS
### 1. CAMERA MATCHING

[PRACTICE] The established workflow for recovering a camera from a single interior photograph involves using vanishing points to determine the camera's orientation, position, and focal length. This is supported by software tools specifically designed for this purpose. Commonly used tools include the open-source standalone application fSpy and built-in tools or plugins for 3D software like Blender's own camera matching tools and Perspective Plotter, or commercial software like Lumion's Photo Matching feature. The general process is to identify sets of lines in the image that are parallel in the real world (e.g., the edges of a rectangular room, window frames, floorboards). The intersection of these lines in the image defines the vanishing points.

[MEASURED] The accuracy of these methods is subject to several sources of error. The fSpy documentation provides an example where a known 24mm focal length was estimated as 26mm, with the discrepancy attributed to potential lens distortion and the real-world geometry not being perfectly orthogonal (fSpy, "Tutorial", n.d.). The accuracy is highly dependent on the quality of the input image and the user's precision in marking the parallel lines. The fSpy documentation notes that when the line segments used to define a vanishing point are near-parallel, the vanishing point position cannot be computed accurately; a larger angle between the lines yields better results (fSpy, "Basics", n.d.).

[INFERENCE] Classical single-view metrology, as described in the computer vision literature, forms the theoretical basis for these tools. The process relies on the geometric principles of perspective projection.

[PRACTICE] Documented failure modes include:
*   **Lens Distortion:** fSpy explicitly states that it does not work well with images that have significant, uncorrected lens distortion (e.g., from fisheye or wide-angle lenses) (fSpy, "Basics", n.d.).
*   **Non-Perpendicular Geometry:** The tools assume that the sets of parallel lines chosen correspond to mutually perpendicular directions in 3D space. If the real-world geometry is not perfectly orthogonal, the camera solution will be inaccurate (fSpy, "Tutorial", n.d.).
*   **Ambiguous Vanishing Points:** In scenes without strong, clear parallel lines, or where lines are short or close together, accurately defining vanishing points is difficult, leading to poor calibration (fSpy, "Basics", n.d.).
*   **One- and Two-Point Perspectives:** While fSpy can handle these, users have noted that two-point perspectives can be "horribly troublesome" for determining focal length, as it relies on the less constrained position of the principal point (GitHub user 'barto', 2022).

### 2. SINGLE-VIEW METROLOGY

[MEASURED] The computer-vision literature, particularly the work of Criminisi, Reid, and Zisserman, establishes that it is possible to compute 3D affine measurements from a single perspective view given minimal geometric information. This typically requires a known reference length in the scene, a vanishing line of a reference plane (e.g., the floor), and a vanishing point for a direction not parallel to that plane (e.g., vertical lines) (Criminisi, Reid, and Zisserman, 2000). The method allows for the computation of distances between planes parallel to the reference plane and area/length ratios on any parallel plane, all without knowing the camera's intrinsic parameters like focal length (Criminisi, Reid, and Zisserman, 2000).

[INFERENCE] Error bounds are not typically given as a single percentage, as they are highly dependent on the accuracy of the initial geometric information provided by the user (i.e., the placement of vanishing lines and points). Criminisi's work includes a first-order error propagation analysis to associate an uncertainty with each measurement, acknowledging that errors in the initial setup will propagate through the calculations (Criminisi, Reid, and Zisserman, 2000).

[PRACTICE] Conditions that make single-view metrology fail or become inaccurate include:
*   **Lack of a Reference Scale:** Without a known length in the scene, all measurements are relative, and the absolute scale of the scene cannot be determined (Zhu et al., n.d.).
*   **Inaccurate Vanishing Geometry:** The success of the method is critically dependent on the accurate estimation of the vanishing points and lines (Criminisi and Zisserman, n.d.). If these cannot be determined precisely (e.g., due to a lack of parallel lines or the presence of lens distortion), all subsequent measurements will be incorrect.
*   **Non-Planar Reference Surfaces:** The classical methods assume a reference plane (like the ground). If the reference surface is not planar, the geometric constraints are violated.
*   **Objects Not on the Reference Plane:** Measuring the height of an object that is not in contact with the reference plane requires additional steps to project its position onto the plane, introducing more potential for error (Torralba, Isola, and Freeman, n.d.).

### 3. INVERSE GRAPHICS / SCENE RECONSTRUCTION

[MEASURED] The current state of research on reconstructing an editable 3D scene from a single indoor image includes vision-language-model-driven approaches. A key paper is "Thinking in Blender: Staged Executable Inverse Graphics with Vision-Language Models" (He et al., 2026). This paper introduces the Staged Executable Inverse Graphics (SEIG) framework, which uses a VLM (Vision-Language Model) to generate executable Blender Python code to reconstruct a scene.

[MEASURED] The paper **"Thinking in Blender: Staged Executable Inverse Graphics with Vision-Language Models"** reports the following:
*   **Phase Structure:** The reconstruction is decomposed into a sequence of stages that mimics a human artist's workflow: **scaffolding** (approximate object layouts and proportions), then **geometry** (refining primitives into complex shapes), then **materials** (defining colors and textures), then **composition** (ensuring objects rest on surfaces correctly), and finally **lighting** (He et al., 2026, as described by "Two Minute Papers", 2026).
*   **Per-Phase Round Budgets:** NO SOURCED VALUE FOUND. The paper describes an iterative process but does not specify a fixed budget of rounds per phase.
*   **Verifier Design:** The framework uses a "generator-verifier" feedback loop at each stage. The VLM generates a piece of Python code for the current stage. A verifier module then executes this script in a headless instance of Blender, renders an image of the current 3D state, and feeds this render back to the VLM along with the original target image for comparison and refinement (He et al., 2026, as described by "Two Minute Papers", 2026).
*   **Metrics Used Per Phase:** The paper evaluates the final output using a range of metrics covering pixel-level, perceptual, and semantic fidelity (He et al., 2026). It does not specify distinct metrics used to judge the completion of each intermediate phase. The overall evaluation uses metrics like PSNR, SSIM, and LPIPS (He et al., 2026).
*   **Reported Failure Modes:** The authors note that a monolithic (single-pass) approach often leads to the VLM getting "lost in the vast search space of possible programs" and hallucinating details. The staged approach is presented as the solution to this failure mode, as it "substantially improves reconstruction fidelity" (He et al., 2026). Another paper, "Vision-as-Inverse-Graphics Agent" (VIGA), notes that VLMs inherently lack fine-grained spatial grounding in one-shot settings, which their proposed code-render-inspect loop aims to solve (Chi et al., 2024).

### 4. HOW A MATCH IS SCORED

[PRACTICE] The literature on 3D reconstruction and image generation uses a variety of image-similarity metrics to judge the match between a render and a reference photograph. The most common are:
*   **PSNR (Peak Signal-to-Noise Ratio):** A pixel-level metric that measures the ratio between the maximum possible power of a signal and the power of corrupting noise. It is based on Mean Squared Error (MSE) (Wang et al., 2004). Higher PSNR generally indicates a better reconstruction in terms of pixel-wise error.
*   **SSIM (Structural Similarity Index Measure):** A perceptual metric that evaluates image quality based on three components: luminance, contrast, and structure. It is designed to correlate better with human perception than PSNR by focusing on structural information (Wang et al., 2004). An SSIM value of 1 indicates perfect similarity (Wikipedia, n.d.).
*   **LPIPS (Learned Perceptual Image Patch Similarity):** A deep-learning-based metric that measures the distance between two images in the feature space of a pre-trained neural network (e.g., VGG). It is designed to better approximate human perceptual judgments of similarity (He et al., 2026).

[INFERENCE] Published evaluations and descriptions suggest that LPIPS and SSIM correlate better with human judgment of "same room" than PSNR. PSNR is sensitive to small pixel-wise differences that may be perceptually insignificant, such as a slight shift in brightness, while SSIM is designed to be more robust to such changes and focus on structural content (Bhandari, 2026; Wang et al., 2004). LPIPS, being trained on human judgments, is intended to capture perceptual similarity even more effectively (He et al., 2026).

[MEASURED] **SSIM** is the metric most explicitly designed to detect **structural errors**. The core idea behind SSIM is that the human visual system is highly adapted for extracting structural information from a scene (Wang et al., 2004). It is sensitive to degradations in edges, textures, and structures (Bhandari, 2026). However, its sensitivity to *global* structural changes (like a missing object) can be limited because it is typically calculated using a sliding window over the image (Wikipedia, n.d.; Ebrahimi et al., 2026). A metric called Mean Deviation Similarity Index (MDSI) is noted to use local gradients on a single scale and "may fail to detect geometric distortions that alter the overall structure" (Ebrahimi et al., 2026). This implies that metrics operating locally can be blind to larger-scale structural errors.

### 5. THE FAILURE WE ARE LIVING IN

[MEASURED] Yes, there is published evidence and discussion about the failure mode where local comparisons confirm a match while large structural errors survive. This is a known limitation of certain image quality assessment (IQA) metrics. The paper "Image Quality Assessment: Unifying Local and Global Distortions..." states that a "prevailing limitation of existing...IQA methods is their segregated focus on either local texture or global structure, preventing a unified analysis" (Xian et al., 2026). Another paper notes that while voxel-based metrics like the Dice Similarity Coefficient are widely used, they "do not fulfill the critical requirement of detecting all objects in a data set" and can fail to measure the presence or absence of an instance (Maier-Hein et al., 2022).

[INFERENCE] This failure mode arises because many popular metrics, including SSIM, are often applied locally using a sliding window approach (Wikipedia, n.d.). If a large object is missing, the windows that fall entirely within the empty (but correctly rendered) background will report a perfect match. The windows that fall on the boundary of the missing object will report an error, but this local error can be averaged out over the entire image, resulting in a deceptively high overall similarity score. The metric is effectively "blind" to the global structural error because its local view is largely correct. This is a problem of local consistency versus global consistency. Research is ongoing into metrics that combine both global and local feature analysis to address this (Li et al., 2025; An et al., 2014).

### 6. STAGED VERIFICATION

[MEASURED] In published pipelines like the SEIG framework from "Thinking in Blender," the verification is staged and iterative.
*   **Stopping Criterion:** The paper does not specify a hard, quantitative stopping criterion (e.g., reaching a certain metric threshold). [INFERENCE] The process appears to be guided by the VLM's own assessment of the visual discrepancy between its render and the target image, continuing until a satisfactory match is achieved within the overall process.
*   **Budgeted Rounds:** NO SOURCED VALUE FOUND. The number of rounds is not explicitly budgeted in the paper.
*   **Verifier's View:** The verifier gets to see the rendered image of the current 3D scene state generated by executing the proposed code snippet. This render is then compared with the original reference photograph by the VLM in the next step of the loop (He et al., 2026, as described by "Two Minute Papers", 2026).

[MEASURED] There is explicit evidence that a monolithic (single-pass) approach performs worse than a staged one. The "Thinking in Blender" paper states, "Our experiments show that staged reconstruction substantially improves reconstruction fidelity, highlighting the importance of task decomposition for executable inverse graphics with general-purpose VLMs" (He et al., 2026). The VIGA paper reports substantial empirical gains from its iterative code-render-inspect loop over one-shot baselines: a 35.32% improvement on BlenderGym and a 124.70% improvement on their proposed BlenderBench (Chi et al., 2024).

### 7. WHAT A REPRODUCTION EXERCISE SHOULD MEASURE

[PRACTICE] There is no single, standardized, published curriculum for learning archviz by reproducing a photograph. However, a common practice recommended in community forums and reflected in course outlines is to start by matching the fundamental aspects of the scene before moving to finer details. One user on a forum advises to "take a simple photo from an interior design blog or something and recreate it" as a weekly exercise (Reddit user 'archvis', 2019).

[INFERENCE] Based on the staged approach in the "Thinking in Blender" paper and general archviz workflows, a logical sequence for a student to follow would be:
1.  **Camera and Composition:** Match the camera position, rotation, and focal length first. This sets the "canvas" for the entire scene.
2.  **Blocking and Geometry:** Create simple geometric primitives to represent the main masses (walls, floor, ceiling, large furniture) to get the scale and proportions correct.
3.  **Lighting (Primary):** Establish the main light sources (e.g., sun, sky, large interior lights) to define the overall mood and primary shadows.
4.  **Materials (Basic):** Apply basic materials with correct diffuse colors and roughness values to establish the color palette and light interaction.
5.  **Refinement:** Iteratively refine the geometry, materials, and lighting with more detail.

[PRACTICE] Archviz training courses emphasize doctrines key to the design of an image, such as photography, composition, the study of light, and color theory, before moving into the practical application in 3D software (Lucydreams, n.d.). This suggests that the exercise should be scored not just on pixel-perfect replication, but on the successful application of these artistic principles.

## CONFLICTS AND UNCERTAINTY

*   **Accuracy of Camera Matching:** While sources agree on the methods (vanishing points), there is a lack of hard, measurable error bands (e.g., +/- X% on focal length) in published evaluations of common tools like fSpy or Blender's built-in utilities. The accuracy is highly dependent on image quality and user input, making a universal metric difficult. I would not stake a build on a focal length recovered from a single image without cross-verification if high precision were required.
*   **Metrics for Structural Errors:** While SSIM is designed to be sensitive to structure, its common implementation with a sliding window limits its ability to reliably detect large-scale global errors like missing objects. There is no single, widely adopted metric that is guaranteed to catch both local photometric errors and global structural errors effectively. Relying solely on a high SSIM or LPIPS score could be misleading if a major geometric error is present.

## WHAT I COULD NOT SOURCE

*   **Quantitative Accuracy of Camera Matching Tools:** I could not find peer-reviewed papers or manufacturer datasheets that provide specific, measurable error bounds (e.g., mean error in mm for camera position, or percentage error for focal length) for tools like fSpy or Blender's camera matching tools under controlled conditions.
*   **Per-Phase Budgets and Stopping Criteria:** For the staged reconstruction process described in "Thinking in Blender," I could not find specific details on the number of iterative rounds budgeted for each phase (geometry, material, etc.) or the explicit, quantitative stopping criteria used to determine when a phase is complete.
*   **Formal Archviz Reproduction Curricula:** I could not find any formally published and scored curriculum or teaching method from an academic institution or major training center detailing how a photo-reproduction exercise for archviz students should be structured and evaluated. The information available is from practitioner blogs, forums, and general course descriptions, which outline a logical workflow but do not provide a formal, measurable scoring rubric.
---

## GROUNDING (vendor-reported)

- search queries issued: 36
  - `camera matching workflow interior architecture`
  - `fSpy vs Blender camera matching accuracy`
  - `accuracy of camera matching from single photo focal length position`
  - `failure modes of single view camera calibration`
  - `single view metrology accuracy Criminisi`
  - `error bounds single view reconstruction Zisserman`
  - `conditions for failure single view metrology`
  - `state of the art single image 3D scene reconstruction editable`
  - `vision-language models for 3D scene generation Blender`
  - `inverse graphics Blender script from image`
  - `Thinking in Blender: Staged Executable Inverse Graphics with Vision-Language Models paper`
  - `image similarity metrics for 3D reconstruction evaluation`
  - `PSNR vs SSIM vs LPIPS in scene reconstruction`
  - `perceptual similarity metrics for architectural visualization`
  - `image metrics for detecting structural errors in 3D scenes`
  - `local vs global error in image similarity metrics`
  - `image metrics blind to structural changes`
  - `failure modes of photometric comparison in scene reconstruction`
  - `change detection metrics for missing objects`
  - `staged vs monolithic 3D scene reconstruction performance`
  - `iterative refinement in inverse graphics stopping criteria`
  - `verifier design in generative 3D models`
  - `architectural visualization training reproducing photographs curriculum`
  - `archviz curriculum photo matching exercise scoring`
  - `scoring criteria for 3D scene reproduction in education`
  - `Thinking in Blender Staged Executable Inverse Graphics with Vision-Language Models arxiv`
  - `accuracy of fSpy focal length estimation`
  - `Blender camera match tool accuracy evaluation`
  - `single view metrology error analysis Criminisi paper`
  - `limitations and failure modes of single view metrology`
  - `image metrics failing to detect geometric errors`
  - `local vs global consistency in image quality assessment`
  - `structural error detection in image similarity metrics`
  - `architectural visualization photo matching tutorial`
  - `archviz training exercises photo reproduction`
  - `learning archviz by copying photos curriculum`

- grounding chunks: 27
  - designblendz.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGuX8NQggNPV5ymeAP4AgFJiS41a4Q8IV4rKxNytGc6EAQLlf9fzGFHztRVB6tAWCMCkOiXafdNuqaME3RjafBEZ_C_YAZmpnIQse9CcwBx6uWPrXIub7_rDx370VhSIn815UCK7jYIxhp8OaBNdqw4ffGuRzEna7x52sotzNCejwJEWCSt_c2i4_OVMmBO84lEfw==
  - bluentcad.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHiEdiRcGzQbJ46Md-BEBoBoNoOvVXJv4Gf5JBufEq5QptwntjY4DRLDc_XCqbEOmS7jD-_jDWlM4sjFXqLfwcap1NrNujNB_ZD6gNvZX_a96At2nelEp7o8pMwo1bm8JOAjxPpoMQp4UtxB5RbUe3aQWAeCot85awOtl0sUrUkgwXa0pogAomkzgXw
  - lumion.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE5oTVUqpixahrZ0M584YKlKSrI_RJPxnUca8KytCRbRzW3pMqNfngTbri1pjwrkF-5OFxq-XsFwpNmNvh9W94oHbi0Ncb2pFATBLfis_gSGQJDA_LTOJxPxIYFyvI3T6dA6_7fSsrWLLHnDpHvlByBhXnH2qWY_7sLTXmW5xRWSYBwKorSj9ltmKUo3mWdG5s0z2-1zGlt4c4=
  - youtube.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGYVqmLy69ENwZpo6foUCsFbMU3T89h0tiBv4GRYFxXHLJ1wk3iGY-wNGJ2knkASr7Epum2_Jv5PqQfVGQmhgilmjuPgUzt4cUMLbFE6i6RunkcpTEAlpRZhFL4ec9NiT0G9Ki73Oc=
  - youtube.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEFylIp17zlcbCgTNZsoqkgUS97mYCWrpE_ExoFLon6v1-1kPSWTjL3B67ovntPVyzGu0wDr9B2Me_kV5XsHVRXA6mraAO4QMr6w9PT1abourV6jdi14_usXO3TRtCwJAH7ekRg_L8=
  - fspy.io — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQERj1b6WDLnE-qPWSIrHhaW_8W3QewWhiwQC-_Q4Awihn8odm0h8pMACWSpyKc0gIu0K1MUKsk3gfYfgzwzoErNoX-Ynd8rABlmZhIfZFTinYEDvQ==
  - fspy.io — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBrXBK3Sy-10rRkGizioe2YTjec8kKvOmoITwQgzuOACMZ4r6_w0ZNQjWSOWtyNDvyo3BxUEGiLgVOQ-3Bfis0X6ZJZEuoAYWhX7cyDpr2lB0=
  - github.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHTfXhA0yctPg0MpEX6Ql78tssqXlAMhpyW8cyr-t_FOIPiCJrZAQZJ6NST5sO_m4wXzloQeGU9s8HtI7h0FQKwxV234lJUjOFnJ--YKeKCXsAxgegItASRR06WFwrGjMA6KYl2r42TnA==
  - ucf.edu — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFP_2YSAElEroMWqQUxbv_rCZ7srgX2WPZ3cYZhoMEC8jgrd4ZtVI5sP4NNZoQ-BCS297qvJWHIqTDVWLhTWMaOfqC2BnhXEJJKCYwDpI0FAoep6iuoPD5DPmH5lnbg4IGHg6cQT14OdWyXuepu71xyd0MhLyLdfk_V3Now83GP
  - ucsd.edu — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEoIM16hVLNHT3Jneac6YFVuz4dxFkUnQa9ES0mbchuOxk5fiZ9HTbah5WxV7dMOMngAjJmkX77O-V_BDo4mrDPl21raqy07Wyj0jio-Vam8wO7X_rpMcKqy7cRNeIzykxksSuHjcwV9TZFYpsxadlUTHorWaru6yq1
  - github.io — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHophxBAr7BW1aB2wBoN3xNiL1YLwNKlLLJiJJSTKTNfLD01Pa5xsX2UwDO3aapR0vx5OWDtDbAfBMOsIYfzvKKh4tBGL0Ink8n3g0mX-bHVkH3YXB1XjrnAvBEARl347GRXA==
  - mdpi.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFREl-lWNiPUy14fNnWv0isbmOoeBrEYq1d7CgWG40T1Y4gfittMmdabvvXGP8v8ZlmCY_R5i6hheXFlW9tEzsdexdvFGt5qPyIWG6xbT2bTPfHkzX1I-FopTl8FjRuDBGPPWGK
  - mit.edu — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGXKvytI8cCu0KL9W_CSCWDHJzkFFr6FpoOxhI_tfysRNnFzfqubEWSongou_Uev1o1GrDHhqYzukvItOM-EH58I5Av3aQ7jJs5ATDbxnaw9BNr9Q7tE9UlWvYXmI1jJABQYfeYY5Vxm2qiIdazvBiW3PYnnLANQkbMj__tOw==
  - huggingface.co — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGtOVG_8A6Bi0JLSPX-QAPfLNzM6JqkbvHyD-AE2RxsOVvvsb-_0109QoopAARt-mO_mV5YFg7P-SdMB5A9pqhuQobWxbjWAQk0KQkQc_GtfwuW4nmCyYRpqMmZnDLOl0nG7GM=
  - arxiv.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQElvHajl1pLm0aTIInhoVDdy1M-xwEHNntKLTSzjZ3pVg6LSF5bQdGy5JFlm4LJPqvL2Uv0ALxXEt_X3OOi6L5nkRmhQZXAeCMICRSeioh194J-DDaF-bHMu-T1
  - medium.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHKXQspakvOvG5u-dcC4jgPPwogpNKN0qaj_EGcPgAFxK9vp6wGrIcibJRKTLOwAV0WXqhs0ey4pjJZpfKb59GP_vcUSR8SxOMCYD4dxcQGx0RjwOYhPseMBSnk_kg4fxRCBIOfF8ONU-DJ0rY762AxrOwPr95fb2dJSDTwjDrthN3pox5tuFTPkNyREPJ20bNab0YbBuh4LU9E4xCWDXJF
  - researchgate.net — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8eC8-ekXkV6sWGLwz2WRhf0_7fZShjQ_7ZIp7MEIzI63W0WOFgGK06GUIgf2U4OKCzclTSxtOHe3znerpnKAZett8I5HQfcRPgvgNFfkc-2vFQWxmAA1XGWz5PR_ZWcs7nOeobWVekxrQG-ABWBallMuOrcCkXyVxsWa6zce289AI3XBAU3Db7siy_-WIPnTAr1FqqOpsBt56TNwGIJK8kxUFQMMcxusG7dAPFctg5Obm7a3xbocXnund5m55W8O1
  - arxiv.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE1NMC5zZRHV_bcwBKMUvk16fFRavAaF_XfY03y2ttsNyZVkXvzrJjDPVQ4dSZqcKHJM-Ez6T1CNwxSH1laHNex134DNy-qyDR49yhxVHZLsHx6pmvPiaUR1Qd-JcXW
  - uwaterloo.ca — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6lWW2H12z4adltTDzng67qFn0vU5cn5pvYWUvoJW-dyFWgyzoA2x2hGcdYlFlQfJW6hWvREXuus6mSRxAXcC0ZZRzo_rCmGyuERnRkSMvFh_ywGVit93WFFMk6fGOme6Pr2rPeGqJjuBq4WwtED2EoO4e
  - wikipedia.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHZZj3iFsZp8xluphpB0tP6yvyw6KrN1JoplpjV1BMsg2Vpuhd-ILu-v46qu8sJHbqcPMcQLLIQo4gpfQmsXTtyrQCA6oXW21Y4-8dTXk1mVUAaCqjMWBVzxoTSNp2Ew_alWK59zRGkc1yGoJx9gmg6fiPy9kCV7rZtcWpz
  - arxiv.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEV2-Z_Q4x71vWl4HrKUbnpfdGEX9cZbhY8Kli1gOg4xtG3aEaBiyKVVQX56n4Kdb4KOh92GDdI40sGUMwHDuS30tcRqF9fsQkUAe07IS1PWZJ_7O8IqMIzWXde0u6V
  - researchgate.net — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHVZBW7i4zVnVP37eZcabafEt2J729Z6NIh9hpkvIs_wT-9-MHITPNOYNcB-inSdEoCYsazyWWEvk33QuVO_9km-lTMBDYWrVLvLKBUcMM4hievpnxFb372KwYwdf1q2h1rcVe3D84TSC5UanNOqckGJ-08ZRj4GFpUffowzLm4rHNukvjPCAMeoAzNdO5HOe_6EL3Z0qMagAII1q9T5EURpD8v696lio_1sYXO2_B6QHhq2OHJw-ogO8rN_UkrVt90edHQskd7o3pNyqSMXSaiMzxHrTQa0j0t266eWRdj9LjzT2-TW90OKs9T2A==
  - nih.gov — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHDtIbE8WmwZnvMx5NxJYvaGKIIzvCC3UnzF8ixZIIjCMuLJm-Wo_o8eHwJoMbFvMqgbFFQUCpG1uq0k_hRlrqe3Tv-a3SwbQ2gmVqOBv__B2p2j6Zl2X_TLHmhHmvlfs7EjLaW2GdI-JGnhHna
  - nih.gov — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF88hX2aw1gCZ0MjCJUdZmKDRygM0Mgqcu2tYpGFECLVPKryPidUgPYTKVi7ZxUb7w01UHUlHvtD9RODhHoXFLglmCImjCujt8fATaHaf5Tl4PMyc_-QI8es81EId5h5t9tde-h91sIERRcEnXs
  - arxiv.org — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE_5Bq0tVDz5tQMloavMajmw-1pgWqsdU9NMy6C3wP1D6aFeQVvBWi9xeRy6XE5ffGyxyXtOUpZpabwLoYVvQPHLwD3SZvp62PiLhbqoAXDd8ijTZSQZal2TAo=
  - reddit.com — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEIaNY86zQY8G_NYBIzBCZd9Q9NTdNalzEf7FO9n90nxUtmf20c-kuUGiSAxL-0Ww5KOe1ropLpVaZQupswbZvpQ8d5Hp5o-LRvwGJzZuJmw7JSHj__Lx6Why-eClnuvl_vYLHhZR1CI-24E0RZb3U7-eUDaeiUv9ZxcvTXkWAdOkrsY8f7eUpqEv3OimR3FA_4TSMZ2_pQAw==
  - das3d.ch — https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHA59mlXvHTwIsByNwEcXh3Qp80DCKgsJl2Lt0MqpfjtFCwE8YMQL36ImyQ-5UjRON0gTf63-w9uZt0oGLNO-pfydJOKQdTDsmLV-zFindSGCOrOj8kmAoDldNx36iBb-b2u5MXILjc7E76YZ4RnaMp
