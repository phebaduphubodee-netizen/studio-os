Of course. Here is the requested research on software tools, libraries, and techniques for an automated interior-design drafting pipeline, presented from the perspective of a senior interior-design research assistant.

***

## QUESTION DECOMPOSITION

To provide a textbook-grade answer for a builder, the research must address these sub-questions for both reading and writing floor plans within the specified technical constraints (headless, Python, $0/open-source, commercial use):

**Part A: Reading / Parsing a Plan**
1.  How can we move from a raw list of DXF entities to a structured model of rooms, walls, and openings?
2.  What is the state-of-the-art in open-source BIM (IFC) parsing with Python?
3.  What is the practical viability of extracting dimensionally-correct geometry from vector PDFs?
4.  Are there any commercially-usable, open-source models for converting raster images of floor plans into usable vector data?
5.  Can Vision-LLMs be trusted to extract structured, dimensionally-accurate data from plan images, and what are the failure modes?
6.  What are robust, automatable methods for determining a drawing's scale and units?

**Part B: Writing / Generating a Plan**
1.  Which Python libraries are best suited for generating professional-grade 2D construction drawings (DXF/SVG/PDF) that adhere to drafting conventions?
2.  What are the reliable, headless methods for writing to proprietary formats like DWG and interoperating with BIM (IFC), SketchUp, and Blender?
3.  What is the maturity of open-source algorithms (both classical and ML-based) for automated space planning, and are they suitable for professional use?
4.  Which commercial APIs provide reliable parsing or generation capabilities that might justify their cost?
5.  What specific drafting standards must an automated system adhere to for its output to be considered professional, and what tools help enforce them?

## EVIDENCE / FINDINGS

### PART A — READING / PARSING A PLAN

#### A.1. Semantic Vector-CAD (DWG/DXF) Extraction

This is the task of inferring architectural intelligence (walls, rooms) from "dumb" geometry (lines, arcs, polylines).

*   **Tool: `ezdxf` and its add-ons (`drawing`, `path`, `acis`)**
    *   **Actual Capability:** `ezdxf` is the definitive Python library for low-level reading/writing of DXF entities. It can read DWG files via an integration with the ODA File Converter. It correctly parses all entities, including blocks/INSERTs, layers, and text. Its `path` add-on can convert complex entities (polylines, splines) into paths for geometric computation. It does **not**, out of the box, identify "rooms" or "walls." It provides the geometric primitives from which you must build this intelligence.
    *   **Input/Output:** DXF (native R12-R2018), DWG (via ODA File Converter).
    *   **Automation:** Fully headless and Python-native.
    *   **License:** MIT License (permissive, commercial use is fine).
    *   **Cost:** $0.
    *   **Maturity:** Excellent. Actively maintained, extensive documentation, considered the standard.
    *   **Failure Modes:** Correctly resolving all possible nested blocks, proxy entities, and proprietary ADT/AEC objects from complex drawings can be challenging. It provides the raw data; the semantic interpretation is your burden.
    *   **VERDICT: ADOPT.** This is the foundational tool for any DXF/DWG work in Python.

*   **Approach: Custom Heuristics & Room Boundary Tracing**
    *   To build room intelligence on top of `ezdxf`, you must implement your own algorithms. A common approach involves:
        1.  **Layer Filtering:** Use layer names (e.g., "A-WALL", "I-DOOR") as a primary heuristic to identify candidate entities for walls, doors, etc. This relies on the input drawing following a known standard.
        2.  **Block Name Matching:** Identify doors, windows, and fixtures by matching block INSERT names to a library of known symbols (e.g., "Door-36", "Window-Fixed-48x60").
        3.  **Boundary Tracing:** Use a graph-based or flood-fill-like algorithm on wall centerlines to detect enclosed polygonal spaces (rooms). This is non-trivial and must handle small gaps, intersections, and complex wall geometries.
        4.  **Text Association:** Spatially associate `TEXT` or `MTEXT` entities with detected room polygons to label them (e.g., "BEDROOM 1").

#### A.2. BIM/IFC Parsing

*   **Tool: `IfcOpenShell`**
    *   **Actual Capability:** The leading open-source library for working with the Industry Foundation Classes (IFC) BIM standard. It can parse the full IFC schema (IFC2x3, IFC4), allowing you to traverse the model hierarchy and extract entities with full semantic meaning: `IfcWall`, `IfcSpace` (rooms), `IfcDoor`, `IfcWindow`, including their geometry, properties (`PSet_*`), and relationships.
    *   **Input/Output:** IFC.
    *   **Automation:** Fully headless. The Python wrapper is comprehensive and the standard way to script interactions.
    *   **License:** LGPL-3.0. This means you can use it in a commercial application, but if you modify the library itself, you must share those changes. Using it as a dynamic library in your closed-source application is generally considered acceptable.
    *   **Cost:** $0.
    *   **Maturity:** Very mature and widely used in the AEC open-source community. The core of many other tools (e.g., BlenderBIM).
    *   **Failure Modes:** IFC files can have inconsistent or non-standard geometry representations. Performance can be a consideration on very large, complex models. The learning curve for the IFC schema itself is steep.
    *   **VERDICT: ADOPT.** If you need to read BIM data, this is the correct and only mature open-source tool for the job.

#### A.3. Vector PDF Plan Parsing

*   **Tool: `PyMuPDF` (fitz)**
    *   **Actual Capability:** A high-performance Python library for accessing PDF content. It can extract raw vector graphics (paths, lines, rectangles) and text with coordinates. It does **not** understand architectural semantics. The output is a list of drawing commands, not a structured scene graph. You would need to re-implement scale detection and geometric analysis to find walls.
    *   **Input/Output:** PDF (input), various (output).
    *   **Automation:** Fully headless and Python-native.
    *   **License:** GNU AGPL 3.0 (viral open-source) for the free version. A commercial license is required for use in closed-source applications, with pricing available upon request from Artifex.
    *   **Cost:** $0 for open-source projects, paid for commercial use.
    *   **Maturity:** Excellent, very well-maintained.
    *   **Failure Modes:** PDFs lack a formal layer structure. Line styles (dashes, dots) are often represented as many small, disconnected segments. Identifying a continuous wall from these fragments is a significant engineering challenge.
    *   **VERDICT: AVOID (for commercial pipeline due to AGPL license) or EVALUATE (if a commercial license is purchased).** The technical challenge of re-constituting a coherent plan from raw PDF drawing commands is high.

*   **Tool: `pdfplumber`**
    *   **Actual Capability:** Built on top of `pdfminer.six`, it's designed for extracting tables and text but also exposes line and rectangle primitives. It is generally slower than PyMuPDF and offers a higher-level, more forgiving API.
    *   **Input/Output:** PDF.
    *   **Automation:** Fully headless and Python-native.
    *   **License:** MIT License (permissive, commercial use is fine).
    *   **Cost:** $0.
    *   **Maturity:** Good, actively maintained.
    *   **Failure Modes:** Same as PyMuPDF; it provides geometric primitives, not architectural intelligence. It may struggle with complex clipping paths or unusual PDF generators.
    *   **VERDICT: EVALUATE.** A good MIT-licensed option for experimenting with vector PDF extraction, but be prepared for the significant challenge of geometric reconstruction.

#### A.4. Raster / Scanned Plan Recognition

*   **Tool: Open-Source ML Models (e.g., DeepFloorplan, R2V, etc.)**
    *   **Actual Capability:** These are primarily research models. They demonstrate the potential of using CNNs or other architectures to perform image segmentation (pixels belonging to walls, doors, windows) and sometimes vectorization. They are almost never production-ready systems.
    *   **Input/Output:** Raster image (PNG, JPG) in, structured data (JSON) or vector lines out.
    *   **Automation:** Runnable headlessly, but requires setting up complex Python ML environments (PyTorch/TensorFlow).
    *   **License:** Almost always a restrictive, non-commercial research license (e.g., CC BY-NC-SA 4.0).
    *   **Cost:** $0 in software, but high cost in engineering time and compute resources.
    *   **Maturity:** Research/prototype level. Not robustly maintained.
    *   **Failure Modes:** Highly sensitive to image quality, rotation, and lighting. Often fails on stylistic variations (thick lines, hatching, furniture). Accuracy is far from the 99%+ required for construction documents. Dimension/label OCR is a separate, challenging problem.
    *   **VERDICT: AVOID.** Unsuitable for a commercial pipeline due to licensing and lack of production-grade robustness.

*   **Service: CubiCasa API**
    *   **Actual Capability:** A commercial service that takes a scan (from their mobile app) or an existing floor plan image and returns a structured floor plan. They are a market leader and their output is a good benchmark for quality.
    *   **Input/Output:** Image/scan in, various formats out (SVG, DXF, IFC).
    *   **Automation:** API-driven, so inherently automatable.
    *   **License:** Commercial.
    *   **Cost:** Paid, per-scan pricing model.
    *   **Maturity:** Mature commercial product.
    *   **Failure Modes:** Dependent on a third-party service. Cost can scale. Accuracy is high but not infallible; may still require a human QC step.
    *   **VERDICT: EVALUATE (as a paid alternative).** This is a "buy" decision. If raster parsing is a core requirement, this is a known-good solution to benchmark against.

#### A.5. Vision-LLM Route (GPT-4V, Claude 3, Gemini)

*   **Actual Capability:** Multimodal LLMs can look at a floor plan image and describe it in structured formats like JSON. They can identify rooms, approximate their sizes, list furniture, and transcribe text.
    *   **Input/Output:** Image/PDF in, structured text (JSON, etc.) out.
    *   **Automation:** API-driven.
    *   **License:** Commercial terms of use from the provider (OpenAI, Anthropic, Google).
    *   **Cost:** Paid, per-token/per-image pricing.
    *   **Maturity:** Rapidly evolving.
    *   **Failure Modes:** **Crucially, they hallucinate coordinates and are not dimensionally reliable.** They cannot be trusted for generating geometrically precise vector data. They will invent coordinates that look plausible but are not based on the source geometry. This makes them unsuitable for creating the base model for construction drawings. They are better at semantic tagging (e.g., "This room is a bedroom and contains a queen bed") than geometric extraction.
    *   **VERDICT: AVOID (for geometric extraction). EVALUATE (for semantic annotation).** Useful for a first-pass analysis or tagging rooms identified by other methods, but do not trust its coordinates or dimensions for drafting.

#### A.6. Scale / Unit Detection Best Practice

*   **Approach: Asserting Scale from Witness Dimensions**
    *   This is a critical, unavoidable step for any "untrusted" input (PDF, raster, some DXF).
    *   **Process:**
        1.  **Find a Dimension:** Scan for a dimension line with text. In vector formats (DXF, vector PDF), this involves finding a pattern of a text object near a line with ticks or arrows. In raster formats, this requires OCR.
        2.  **Measure the Geometry:** Measure the pixel or coordinate-space distance of the dimension line itself.
        3.  **Calculate the Scale:** The scale is the numeric value of the dimension text divided by the measured length of the line (e.g., 3500 mm / 175 drawing units = 20 drawing units per mm).
    *   **Units (`$INSUNITS`):** For DXF/DWG, always check the `$INSUNITS` header variable first. It explicitly sets the drawing's units (e.g., 1=Inches, 4=mm, 6=meters). If it's undefined (0) or incorrect, you must fall back to the witness dimension method.
    *   **Reference:** This process is a standard pre-flight check in professional practice, though often done manually. There is no single authoritative text for the algorithm, but the principles of drafting scale are covered in *Interior Design Illustrated* by Francis D.K. Ching.

### PART B — WRITING / GENERATING A PLAN

#### B.1. Headless 2D Drafting Output

*   **Tool: `ezdxf`**
    *   **Actual Capability:** Excellent for creating professional-grade DXF files. It supports layers, complex line types, hatching, dimensioning (`LinearDimension`, `AlignedDimension`), blocks, and title blocks. Its dimensioning tools can be complex to use but are powerful enough to create standards-compliant output.
    *   **Input/Output:** DXF.
    *   **Automation:** The canonical tool for headless DXF generation in Python.
    *   **License:** MIT.
    *   **Cost:** $0.
    *   **Maturity:** Excellent.
    *   **Failure Modes:** Creating truly professional-looking dimensions that automatically avoid collisions and place themselves neatly requires significant custom logic on top of `ezdxf`. The API is low-level, giving you power but also responsibility.
    *   **VERDICT: ADOPT.** This is the best tool for generating the core 2D construction drawing.

*   **Tool: `svgwrite` / `drawsvg`**
    *   **Actual Capability:** These libraries generate Scalable Vector Graphics (SVG). SVG is an XML-based web standard, excellent for previews and web display. It supports layers (via SVG groups), fills, and text.
    *   **Input/Output:** SVG.
    *   **Automation:** Fully headless and Python-native.
    *   **License:** MIT.
    *   **Cost:** $0.
    *   **Maturity:** Mature and stable.
    *   **Failure Modes:** SVG is not a CAD format. It lacks built-in support for professional dimensioning entities, architectural symbols, or the block/INSERT model. It is unsuitable as the final deliverable for a builder, who expects DWG/DXF.
    *   **VERDICT: EVALUATE (for previews). AVOID (for final construction documents).**

#### B.2. Writing DWG, IFC/BIM, and Interop

*   **Tool: ODA File Converter**
    *   **Actual Capability:** A free (but not open-source) command-line utility from the Open Design Alliance that performs robust, high-fidelity conversions between DXF and various versions of the DWG format.
    *   **Input/Output:** DXF, DWG.
    *   **Automation:** Headless command-line tool. Can be called from Python using `subprocess`.
    *   **License:** Freeware license. Can be used for commercial purposes.
    *   **Cost:** $0.
    *   **Maturity:** Industry standard for conversion.
    *   **Failure Modes:** It is an external binary dependency that must be present on the system running the pipeline.
    *   **VERDICT: ADOPT.** The standard, reliable way to produce DWG output from your pipeline after generating a DXF with `ezdxf`.

*   **Tool: `IfcOpenShell` (Write capability)**
    *   **Actual Capability:** Can be used to programmatically construct an IFC model from scratch. You create entities (`IfcWall`, `IfcSpace`, etc.), define their geometry (e.g., as extruded profiles), set their properties, and establish relationships.
    *   **Automation:** Fully headless via the Python wrapper.
    *   **License:** LGPL-3.0.
    *   **Cost:** $0.
    *   **Maturity:** Mature. Writing IFC is more complex than reading it, as you are responsible for creating a valid and compliant file.
    *   **Failure Modes:** The complexity of the IFC schema is the primary challenge. It is easy to create a syntactically valid IFC file that is semantically meaningless or geometrically broken. Requires deep domain knowledge.
    *   **VERDICT: EVALUATE.** This is the correct path for generating BIM deliverables, but plan for significant development effort to get it right.

*   **Interop: SketchUp (Ruby) and Blender (Python)**
    *   **SketchUp:** The path is DXF -> SketchUp. SketchUp has a robust DXF importer. There is no good, direct Python-to-native-SketchUp-file library. The standard automation path is to generate geometry via a Ruby script inside SketchUp, which is not suitable for a pure Python, headless pipeline.
    *   **Blender:** The path is simpler as Blender's API is Python-based. You can write a Python script that calls `ezdxf` to read a DXF and then uses the `bpy` module to create corresponding Blender mesh objects. Alternatively, BlenderBIM (built on IfcOpenShell) can directly import an IFC file generated by your pipeline.

#### B.3. Automated Space-Planning / Layout Generation

*   **Approach: Constraint Solvers / Optimization**
    *   **Actual Capability:** Techniques like rectangle packing and constraint programming (using libraries like Google's `OR-Tools`) can arrange a set of defined rooms ("rectangles") within a boundary subject to constraints (e.g., "Kitchen must be adjacent to Dining," "Bedroom must have one exterior wall").
    *   **Maturity:** The underlying solver libraries are mature, but their application to architectural space planning is a complex custom implementation. This is a "build it yourself" route.
    *   **Output Quality:** Tends to produce mathematically optimal but architecturally naive or sterile layouts. Lacks a nuanced understanding of human circulation, light, and aesthetics.
    *   **VERDICT: EVALUATE.** A powerful approach for programmatic layout, but requires significant expertise in both architecture and operations research to produce good results.

*   **Approach: ML Generative Approaches (House-GAN, Graph2Plan, etc.)**
    *   **Actual Capability:** These are deep learning research models that learn to generate floor plans, often from an input bubble diagram or graph representing room adjacencies.
    *   **Maturity:** Research/prototype. Like their raster-parsing cousins, they are not production-ready tools.
    *   **License:** Almost always a non-commercial research license.
    *   **Output Quality:** Often produces plausible but non-optimal, non-constructible, or bizarre layouts. They lack fine-grained control over dimensions and constraints. The output is a "suggestion" or "inspiration," not a buildable plan.
    *   **VERDICT: AVOID.** Unsuitable for a pipeline that must produce dimensionally-correct, professional-grade output.

#### B.4. Commercial APIs/SDKs

*   **Tool: Archilogic, Foyr, Cedreo, etc.**
    *   These are generally end-to-end platforms, often with a GUI, aimed at real estate marketing or consumer-level design. Some may offer APIs.
    *   **Pricing:** Typically subscription-based, can be expensive.
    *   **Flagging:** These are flagged as paid, often closed-source commercial products. They are generally not a fit for the specified pipeline, which is building the core capability from scratch, not just calling a black-box service.
    *   **VERDICT: AVOID (for this pipeline's goals).**

#### B.5. Standards and Conventions for Professional Output

A generated plan MUST honor these to be taken seriously by a builder.

*   **Layering:** The **United States National CAD Standard (NCS)**, which incorporates the AIA's layer guidelines, is the primary authority. Layers are named with a discipline designator, a major group, and minor groups (e.g., `A-WALL` for architectural walls, `A-DOOR` for doors, `A-FLOR-PATT` for floor patterns, `A-ANNO-DIMS` for dimensions).
    *   **Python Tooling:** There is no library that "enforces" this. Your code must be written to generate entities on the correct, named layers.
*   **Line Weights:** Line weights convey depth and object importance. As per Ching's *Interior Design Illustrated*, walls should have the heaviest lines, doors and windows medium, and furniture the lightest. This is controlled by layer properties in DXF/DWG.
*   **Architectural Symbols:** Doors, windows, and other symbols should be standardized. While no single digital library is universal, the symbols presented in textbooks like *Interior Design Illustrated* represent common practice. These should be created as blocks (`BLOCK` definitions in DXF) and inserted (`INSERT`).
*   **Dimensioning:** Dimensions should be clear, chained together, and follow professional practice (e.g., ANSI Y14.5 is the formal mechanical standard, but architectural practice is a distinct dialect). They should snap to significant features (centerlines of doors/windows, faces of walls). Your generator logic must encode these snapping and chaining rules.
*   **Title Block:** All professional drawings are issued on a sheet with a title block containing project name, drawing title, scale, date, and author. This is typically a `BLOCK` in DXF.

## CANONICAL SOURCES

A builder's professional library for this domain should include:

*   **Ching, Francis D.K. *Interior Design Illustrated*.** (Any recent edition). **Authority for:** Fundamental principles of space planning, drawing conventions, standard symbols, and graphic communication.
*   **Panero, Julius, and Martin Zelnik. *Human Dimension & Interior Space: A Source Book of Design Standards*.** **Authority for:** Ergonomic data and clearance standards. This is the source of truth for numeric values like "minimum hallway width" or "clearance around a dining table."
*   **Karlen, Mark, and James Fleming. *Space Planning Basics*.** **Authority for:** The process of programming, schematic design, and layout development, including adjacency matrices and bubble diagrams.
*   **United States National CAD Standard® (NCS).** **Authority for:** Standardized layer naming, sheet organization, and drafting conventions in the US. This is the official source for professional CAD standards.
*   **IES *The Lighting Handbook*.** (10th Edition or later). Illuminating Engineering Society. **Authority for:** All technical aspects of lighting design, including recommended light levels (illuminance), color rendition (CRI), and glare control (UGR) for different space types.

## SYNTHESIS

### Recommended Technology Stack

Based on the research, the most pragmatic and robust stack that meets the headless, $0/open-source, and commercial-use constraints is:

*   **For Reading / Parsing:**
    *   **Primary Path (Vector CAD):** Use the **ODA File Converter** to convert incoming DWG files to DXF. Use **`ezdxf`** to parse the DXF into raw geometric and text entities. On top of this, you will **build your own Python logic** for semantic interpretation (room finding, symbol recognition) using geometric and layer-based heuristics.
    *   **Secondary Path (BIM):** Use **`IfcOpenShell`** to parse IFC files directly into a rich, semantic model of the building. This is a much more direct path to the data if you can get input in this format.
    *   **Avoid:** Do not use raster-to-vector or Vision-LLM approaches for generating the core, dimensionally-correct geometry. The risk of inaccuracy and hallucination is too high for professional work.

*   **For Writing / Generating:**
    *   **Core Drafting Engine:** Use **`ezdxf`** to generate all geometry, hatching, layers, blocks, and dimensions for the 2D floor plan, strictly following NCS layer standards.
    *   **Final Deliverable:** After generating the DXF, use the **ODA File Converter** (called via `subprocess`) to convert the final drawing to the client's required DWG version.
    *   **BIM Output:** If required, use **`IfcOpenShell`** to generate an IFC model. This is a heavy lift and should be treated as a separate, major feature.
    *   **Previews:** Use **`svgwrite`** or `matplotlib` to generate fast, non-CAD previews for web display or internal validation.

### Top 3 Gaps & Build-vs-Buy Decisions

1.  **Semantic Interpretation of Vector CAD:** This is the biggest gap. No open-source tool reliably performs "plan recognition" (turning lines into rooms) from a generic DWG/DXF. **This is the core component you will have to build yourself.** It involves significant work in computational geometry and heuristics.
2.  **Production-Grade Raster-to-Vector:** The open-source ML world is not a viable source for a tool that can reliably convert a scanned drawing into a dimensionally-correct CAD file for commercial use. The licenses are wrong and the reliability is too low. **This is a "buy" decision.** If this capability is essential, a service like the **CubiCasa API** is the only practical route.
3.  **Generative Automated Layout:** Open-source tools for automated space planning are either too primitive (basic rectangle packing) or too experimental (GANs) for professional interior design. They lack the nuanced constraints required. **You will have to build this yourself**, likely using a constraint programming library like Google `OR-Tools` seeded with architectural principles from Karlen, Ching, and Panero/Zelnik.

## ACTIONABLE FOR AN AI DRAFTING PIPELINE

This research implies the following concrete requirements for your spec-driven generator and internal data models:

1.  **A Rich "Room Spec" JSON:** Your input JSON must go beyond a simple name and dimensions. It should include:
    *   `uuid`: A unique identifier for the room.
    *   `room_type`: (e.g., 'Bedroom', 'Kitchen'). This drives rule-based checks.
    *   `boundary_polygon`: The explicit wall-centerline coordinates.
    *   `openings`: A list of objects specifying `type` ('door', 'window', 'cased_opening'), `location` (on which wall segment), `width`, `height`.
    *   `required_clearances`: Based on *Human Dimension & Interior Space*, specify values like `circulation_path_width: 914` (in mm) or `dining_chair_pullout_space: 760`.
    *   `required_adjacencies`: A list of other room `uuid`s this room should be next to.

2.  **Implement a Clearance Validator:** A pure-Python module that takes a proposed layout (room polygons, furniture locations) and checks it against the `required_clearances` from the spec. This is a core part of a professional pipeline.

3.  **Enforce NCS Layering:** Your DXF-writing module must not use hardcoded layer names. It should have a dictionary mapping entity types to a strict NCS-compliant layer name (e.g., `{'wall': 'A-WALL', 'door': 'A-DOOR', 'dimension': 'A-ANNO-DIMS'}`).

4.  **Standardized Block Library:** Your pipeline needs a resource directory of pre-drawn, standardized DXF files for common symbols (door swings, windows, toilets, etc.). Your generator code will insert these as blocks, not redraw them from scratch.

5.  **Chain-of-Custody for Dimensions:** Log the source of every coordinate. If a coordinate is read directly from an input DWG, flag it as `source: 'as-built'`. If it's generated by your layout engine, flag it as `source: 'generated'`. If it's from a Vision-LLM, flag it as `source: 'unreliable_annotation'`. This prevents hallucinated geometry from ever making it into a construction document.