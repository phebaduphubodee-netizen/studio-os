# Stage 02 — Concept · PRJ-2026-002 (c001-house) · master-suite proof room · 2026-07-02
Status: SHOWCASE (00_intake/gate-override.md A1–A5). Anonymized (C-001/P-001).
Revision: post-MARS r1 (see critique-log.md — 3 reviewers + critic, 15-edit mandate applied).
Geometry of record: `pipeline/scripts/specs/bedroom_suite.json` (Gate-0 as-built PASS) —
this concept DESCRIBES that layout; it never contradicts it (override A2).

## 1) Zoning (rooms → functions → adjacencies; mm + m², per spec)
Suite envelope 5500 × 6500 = 35.75 m² gross, ceiling 2800 (ensuite 2000), origin SW.
Ensuite interior 2900 × 2600 = 7.54 m²; bedroom ≈ 27.6 m² net of the as-built ensuite
enclosure (walls extrude 100 outward per build_room) — ≥ 8.0 m² statutory floor
(ฉ.55 ข้อ 20 via dimensional_rules; R-01).

| Zone | Extent | Function | Adjacency logic |
|---|---|---|---|
| Sleep band | y ≈ 966–3226, x 600–5500 (east of the wardrobe leg, which overlaps the band at x 0–600) | 6-ft bed (2000×2160) on 150 platform, headboard/TV built-in 3330×574 h2800 at y 3226 | Bed faces south (terrace light, A1); TV/headboard wall doubles as the ensuite buffer — sleeping zone never touches a wet wall directly |
| Wardrobe/dressing leg | west: 2100×600 run at y 0 + 600×2500 leg at y 1200 | Closet run (client BF program basis: BF09-3/BF12) | L-shape creates a screened dressing pocket away from the entry; the sleep zone is buffered from the entry by the ~966 mm foot-of-bed circulation band along the south wall; 1000 mm walkway held between the wardrobe RUN's east end (x 2100) and the platform (x 3100) (Gate-0 revision note) |
| Ensuite (wet zone) | NW: interior 2900×2600 at y 3900–6500 | Tub 1700, shower 900×900, double vanity 2850, WC | Stacked on the F2 north plumbing band (brief.json fixed_constraints); door 800 out-swing on its south wall — swing proven clear (suite_clearance) |
| Entry | south wall, door 900 at x 4400 | Suite entrance from F2 hall | Opens onto the circulation spine starting at the SE corner, running west along the bed foot; side built-in 100×3250 at x 5350 |
| Terrace edge (A1) | south strip beyond y 0 (700 deep, outside envelope) | Daylight edge: assumed glazing band ≈ x 0–4400 ONLY — interrupted by the 900 entry door at x 4400–5300 (A1 sub-flag: A1 said "full-width", scoped here; hall-vs-facade double duty of the south wall = site-verify) | Drives daylight direction for renders + vent assumption R-09. Stage-04 scene note: the entry door must never render embedded in glazing (batch-level scene text only — registry v004 untouched) |

Circulation spine: entry (SE) → west along the bed foot → ensuite door (NW) —
engine-proven reach (R-05 / suite_clearance v0.4.2; Stage 03 re-verifies; SC-1 =
success-criteria.md SC-1).

## 2) Style direction — "Warm Contemporary Thai-Tropical Minimal"
Named style + restrictive edges (violations = style-graph contradictions, flag at
review not render):

- Built-in-first, flat-panel, full-height (2800) joinery; shadow-gap reveals.
  EDGE: no ornamental moulding / cornice / classic profile anywhere (contemporary
  restrictive rule; render prompt v004 already carries lived-in contemporary
  language, do not fight it).
- Natural-material priority (knowledge/studio-vault/00-Studio-Knowledge/
  design-principles.md — core principle #2; NOTE file is template-status, cited
  as studio default direction, not filled identity).
- Tropical-humidity realism (knowledge/materials/residential-materials.md):
  EDGE: no solid-wood flooring (severe dimensional movement in humid heat —
  GROUNDED row [t3-1]); engineered wood only. EDGE: no unlined natural drapery
  (mold risk — *-tier vault note, unverified) — mildew-resistant lining required.
  EDGE: no standard vinyl wallcovering behind AC'd walls (trapped-moisture mold —
  *-tier vault note, unverified). *-tier = the vault's own "notebook industry
  knowledge, verify before it drives a spec" marker.
- Light as material (design-principles.md core #3): warm 2700–3000 K everywhere
  in the suite; EDGE: no cool-white source in the sleep zone. Ensuite held at
  3000 K so the open-door sightline stays within the warm band — a 2700-vs-3000 K
  step is permitted; the prohibited clash is 4000-vs-2700 K in one localized zone
  (knowledge/lighting/residential-lighting.md CCT mixing rule; R-10/R-11).
- EDGE (privacy/brand): nothing figurative or text-bearing in artwork slots
  (render-tell + anonymity).

## 3) Palette 60/30/10 (knowledge/styles/color-composition.md §2) — concrete finishes
Buckets follow §2 carrier definitions; one finish family per bucket. Visible-surface
rationale: the oak field (floor ~27.6 m² + full-height joinery runs ~2100+2500+3330 mm
× 2800 h) is the largest continuous visible surface in this room, so oak = dominant.
- **60% dominant — light-oak field:** engineered oak floor, light natural matt +
  rift-oak veneer matte-lacquer full-height joinery (headboard/TV wall, wardrobe
  run) (residential-materials.md flooring: engineered core more humidity-stable
  than solid — *-tier; solid-wood Poor rating is the GROUNDED row [t3-1]).
- **30% secondary — warm greige + linen:** matte low-VOC paint, warm greige
  (LRV target = declared vault GAP — no paint-system values in sources
  (color-composition.md §10); set at paint spec), walls + ceiling; bed + drapery
  in stonewashed linen, greige-oatmeal (tactile vocabulary per
  color-composition.md §8 — weave named so light computes correctly).
- **10% accent — matte black + brushed brass:** door/wardrobe hardware, reading
  sconces, frame lines; brass positioned to catch specular highlights
  (color-composition.md §9 item 11).
Harmony: closest §1 taxonomy types = analogous / monochromatic — the hybrid
warm-neutral classification is studio judgment (§1 cited for taxonomy only).

## 4) Materials shortlist (tropical-vetted; law outranks: wet-area floors under
ฉ.39 ข้อ 9 slope 1:100 — dimensional_rules)
| Surface | Selection | Why (cite + tier) |
|---|---|---|
| Bedroom floor | Engineered oak, matt | solid wood rates Poor in tropical humidity — GROUNDED [t3-1]; engineered "moderate, more humidity-stable core" is *-tier, unverified (residential-materials.md flooring) |
| Ensuite FLOOR | Porcelain tile, slip-rated finish | excellent tropical / impervious wet-zone rating — *-tier, unverified, re-verify before client spec (residential-materials.md tile rows); DCOF per supplier data — numeric threshold = declared vault GAP, do not fill from model knowledge (ibid. gaps) |
| Ensuite WALLS | Porcelain tile, honed | honed kept OFF the floor (slip); same *-tier caveat as above |
| Vanity top | Engineered quartz | non-porous / no-sealing / humid-proof — all *-tier cells, unverified, re-verify before client spec (residential-materials.md countertops) |
| Built-ins | Rift-oak veneer + matte lacquer, on moisture-resistant engineered core, sealed edges/backs, ventilation gap at the ensuite wet-wall face (headboard/TV built-in abuts the wet wall) | studio premium-alt default (design-principles.md material table, template-tier). GROUNDED caution: solid wood paneling rates Poor in high humidity (residential-materials.md wall finishes [t3-1]); veneer-on-stable-core is the mitigation — confirm substrate at Stage 03 |
| Bed textiles | Stonewashed linen bedding | tactile realism, heavy drape, pilling imperfection (color-composition.md §8 grounded lines; physical layering technique = §8's dropped list, not claimed) |
| Drapery | Linen-look, mildew-resistant lining | tropical drapery rule — *-tier, unverified (residential-materials.md) |
| Accent chair | Bouclé | tactile vocab (color-composition.md §9). Fiber content = Stage-03 selection criterion (vault *-tier note favors synthetic blends for tropical mildew — unverified, must not drive the spec as-is); carry grounded abrasion minimums Wyzenbeek ≥ 15,000 / Martindale ≥ 20,000 double-rubs/cycles [t3-5] into FF&E criteria |

## 5) Lighting concept
Legal floor 100 lux (ฉ.39 ตาราง 3 via dimensional_rules): STATUTORY for the ensuite
bathroom (ห้องน้ำ-บ้าน row); for the detached-house bedroom, 100 lux is ADOPTED as a
conservative studio floor via dimensional_rules `legal_lux_floors.residential_unit`
(extension by analogy to the collective-residential row — not directly statutory;
codes-th outranks). Upstream: scoping note on dimensional_rules + R-10 MUST re-tier
queued for the PR lane (mirrors the R-06 door re-tier precedent) — outside this stage.

- Layers: grounded 3-layer minimum — ambient (cove: existing strip-light geometry
  in build_room clay) / task (bedside reading, brass sconces) / accent (art +
  joinery wash) per knowledge/lighting/residential-lighting.md; decorative table
  lamp = studio-default 4th layer (design-principles.md — template-tier example
  text, disclosed). All dimmable (same template-tier source).
- Ensuite layers: vanity TASK layer at 3000 K reaching the face — mirror-flanking
  or backlit-mirror, never ceiling-only over the 2850 double vanity (R-08) — plus
  ambient fill; tub/shower zone rides ambient (residential-lighting.md 3-layer
  model; task-CCT numeric = declared vault GAP).
- CCT: 2700–3000 K suite-wide; 3000 K ensuite (R-10/R-11; §2 mixing rule). Never
  a single uniform ceiling source (residential-lighting.md — flat/sterile tell).
- Ambient targets, metric-first: bedroom ≈ 108–215 lux (10–20 fc), ensuite
  ≈ 215–323 lux (20–30 fc) (dimensional_rules lighting, DRAFT tier; conversion per
  its _ref, 100 lux ≈ 9.3 fc). Design minimum clears the 100-lux floor by ~8% at
  the low end; dimmed scenes may drop below the floor only as scene settings — the
  maintained-average design value stays at or above it.
- CRI: all suite sources CRI ≥ 90 (R-10; dimensional_rules cri_min, DRAFT tier);
  R9 / Rf / Rg numeric targets = vault GAP pending IES/TM-30 ingestion
  (residential-lighting.md).
- Render direction (batch-level only — registry v004 untouched): each Stage-04
  batch declares a temporal mood axis — golden hour (warm dramatic shadows) or
  blue hour (warm interior vs cool exterior sky through the south glazing; the sky
  is not an in-zone source, so the CCT mixing rule is intact) — breaks the
  all-warm monotone flat-render risk (residential-lighting.md temporal mood;
  color-composition.md §9 items 5/8).

## 6) Mood narrative (client-facing)
ห้องนอนใหญ่ที่ตั้งใจให้ "เงียบ" ตั้งแต่ก้าวแรก — ประตูเปิดเข้ามาเจอผนังตู้ไม้โอ๊คเรียบตลอดความสูง
ที่ค่อย ๆ นำสายตาไปยังเตียงบนแท่นไม้ ซึ่งหันรับแสงธรรมชาติจากแนวกระจกฝั่งระเบียงทางทิศใต้
โทนสีทั้งห้องคือสีอบอุ่นของไม้โอ๊คอ่อนตัดกับผนังสีเทาอมเบจด้าน แสงไฟทุกดวงเป็นแสงวอร์ม
เหมือนช่วงพระอาทิตย์ใกล้ตก ผ้าปูเตียงลินินซักนุ่มจัดวางแบบไม่เนี้ยบจนเกินจริง ให้ห้องรู้สึก
"มีคนอยู่จริง" ไม่ใช่ห้องโชว์ หัวเตียง built-in ทำหน้าที่เป็นทั้งผนังทีวีและตัวกั้นเสียงจาก
ห้องน้ำในตัวที่ซ่อนอยู่ด้านหลัง ในห้องน้ำ อ่างล้างหน้าคู่ยาวเกือบสามเมตรท็อปควอตซ์รองรับ
กิจวัตรเช้าพร้อมกันสองคนโดยไม่เบียดกัน อ่างอาบน้ำวางชิดผนังกระเบื้องพอร์ซเลนโทนอุ่น
รายละเอียดโลหะสีทองด้านและสีดำด้านถูกใช้อย่างประหยัด — พอให้ประกายเมื่อแสงผ่าน
ไม่มากจนแย่งซีน ทั้งหมดนี้คือความหรูแบบไม่ต้องพูดเสียงดัง: วัสดุจริง สัดส่วนถูก และแสงที่ถูกต้อง

## 7) Self-check vs rubric (contract gate)
- Zoning references plan dims + areas ✓ (all mm/m² from spec, R-01 demonstrated).
  Style edges declared ✓. Palette = 3 concrete finish families, §2-carrier-labeled ✓.
  Mood 5–10 sentences ✓. Citations per claim ✓ (tier-scoped: grounded vs *-tier vs
  template-tier disclosed inline).
- Style-graph contradictions found NOW: velvet/heavy-pile luxury cliché rejected
  (humidity); solid-wood floor rejected (humidity, grounded [t3-1]) — replaced above.
- Privacy: BF schedule tags (BF09-3/BF12) are non-identifying program tags retained
  for R-08 traceability — waiver recorded (R-13 reviewed; re-identification risk
  negligible).
- UNMET / honest flags: design-principles.md is an UNFILLED TEMPLATE — its
  citations are default-direction tier. residential-materials.md *-tier
  (unverified notebook knowledge) underlies the tropical/durability ratings used
  here — re-verify before any client spec. CRI has a DRAFT numeric (90); R9/Rf/Rg
  and per-room IES lux remain vault GAPs. Client style history = observations only
  (profile.md), no confirmed preference (showcase override A2/A3 covers).
- MARS review DONE this session (workflow, 3 reviewers + critic): all BLOCKER/MAJOR
  resolved in one Reflexion round — critique-log.md. Human approval = standing
  best-case override (gate-override.md); Stage-05 per-image human gate still live.
