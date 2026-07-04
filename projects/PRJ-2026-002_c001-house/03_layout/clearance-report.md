# Stage 03 — Clearance report · PRJ-2026-002 · 2026-07-04 (3-room re-derivation)

Engine: **suite_clearance v0.4.3** (Gate 0 full: exact maximal-clear-rectangle legs,
L∞-erosion circulation + exact Liang-Barsky LOS, quarter-disc swings, as-built wall
bands; statutory floors from `pipeline/dimensional_rules.v0.2.json`, cited to
`knowledge/codes-th`) + **placement_logic FUNCTION gate** (human-usage rules).

Supersedes the 2026-07-02 single-room report (which scored a byte-identical copy of the
anonymized `bedroom_suite.json`). The 2026-07-04 CAD re-derivation (commit `e093084`)
corrected the master interior (6500→5800, carving the 700 mm south terrace; bed
2000→2134×1981) and expanded real scope to **3 rooms**, retiring the fictional
`living_condo`. Committed placements frozen in `scene-graph.{master_bedroom,sitting_room,living_room}.json`
(sha256 in `scene-graph.json` manifest). Furniture XY/orientation = ergonomic **design
judgement** within CAD-authoritative envelopes (per each spec's note), not traced.

**Reading the gate (Gate-0 doctrine):** the contract HARD gate is *zero collisions,
zero clearance violations vs `knowledge/codes-th`*. The ergonomic 610/910 walkway floors
are **Panero, NOT statute** (`dimensional_rules` circulation) — an ergonomic FAIL is a
documented **REVIEW** flag, not a statutory-gate breach. Statutory rows are proven on the
AS-BUILT basis (walls extruded 100 mm outward per `build_room`).

---

## 1 · master_bedroom — `REVIEW` (owner decision required)

**Verdict:** statutory PASS (one narrow-side interpretation WARN) · **ergonomic FAIL**
(120 mm ensuite-access pinch, non-statutory) · FUNCTION WARN (wet/dry zoning). This room
is **blocked on the owner's bed-orientation decision** — a 2134-deep N-S bed in the
2950 mm sleeping band cannot meet the 610/910 ergonomic floor (`derivation-notes.md`);
the 120 mm FAIL is downstream of that. Do **not** gate a deliverable on this room until
orientation is confirmed.

### Gate 0 — clearance (verbatim)
```
=== suite clearance master_bedroom.json (metric, Thai code, Gate 0) ===
  [OK] ceiling height (room): clear 2800 mm >= 2600 floor-to-floor min -> compliant a fortiori (ฉ.55 ข้อ 22 (ระยะดิ่ง พื้นถึงพื้น))
  [OK] ceiling (ห้องน้ำในตัว (ensuite)): 2000 mm vs 2000 min (ฉ.39 ข้อ 9 (แก้ไขโดย ฉ.63) — พื้นถึงเพดาน)
  [OK] bath area (ห้องน้ำในตัว (ensuite)): 9.12 m² vs 1.5 m² min (ฉ.39 ข้อ 9 — ห้องน้ำ+ส้วมรวมกัน; fixtures show both)
  [OK] door width: 900 mm vs 800 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] door height: 2000 mm vs 1900 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] bedroom area (net of sub-rooms): 22.2 m² net as-built (outline 31.9; sub-rooms + wall bands carved exactly) vs 8 m² min (ฉ.55 ข้อ 20)
  [!!] bedroom narrow side (interpretation): as-built legs measure 2200–2850 mm; the sleeping zone sits in a 2850 mm leg: the narrowest leg is under 2500 but wider zones exist — how ด้านแคบที่สุด applies to a carved room is not resolved in the vault; human call, or widen the 2200 mm leg to 2500 to make it decisive (ฉ.55 ข้อ 20)
  [OK] in-bounds: ฐานเตียง: inside the net room
  [OK] in-bounds: เตียง 7'x6.5': inside the net room
  [OK] in-bounds: ม้านั่งปลายเตียง (bed bench): inside the net room
  [OK] in-bounds: โต๊ะข้างเตียง ซ้าย: inside the net room
  [OK] in-bounds: โต๊ะข้างเตียง ขวา: inside the net room
  [!!] in-bounds: เก้าอี้พักผ่อน (armchair): rot 225° is not axis-aligned — checked as the unrotated footprint; verify placement on plan
  [OK] in-bounds: เก้าอี้พักผ่อน (armchair): inside the net room
  [OK] in-bounds: ตู้เสื้อผ้า ผนังตะวันตก (BF11.320): inside the net room
  [OK] in-bounds: ตู้เสื้อผ้า/แต่งตัว มุมเหนือ-ออก (BF09-3.330): inside the net room
  [OK] in-bounds: หัวเตียง built-in: inside the net room
  [!!] overlap: ฐานเตียง / หัวเตียง built-in: footprints intersect (ok if stacked/against a wall)
  [!!] overlap: เตียง 7'x6.5' / หัวเตียง built-in: footprints intersect (ok if stacked/against a wall)
  [!!] overlap: โต๊ะข้างเตียง ซ้าย / หัวเตียง built-in: footprints intersect (ok if stacked/against a wall)
  [!!] overlap: โต๊ะข้างเตียง ขวา / หัวเตียง built-in: footprints intersect (ok if stacked/against a wall)
  [OK] fixture in ห้องน้ำในตัว (ensuite): อ่างล้างหน้าคู่ 3.05m (BF10.250): inside
  [OK] fixture in ห้องน้ำในตัว (ensuite): ชักโครก (WC): inside
  [OK] fixture in ห้องน้ำในตัว (ensuite): ฝักบัว (shower): inside
  [OK] fixture in ห้องน้ำในตัว (ensuite): อ่างอาบน้ำ (tub): inside
  [OK] circulation: entry -> เตียง 7'x6.5': bottleneck 1188 mm >= 910 main walkway (ergonomic; reach tolerance 300 mm)
  [XX] circulation: entry -> ห้องน้ำในตัว (ensuite) door: bottleneck 120 mm < 610 minimum passage pinch (dimensional_rules circulation — ergonomic buildability floor, not statute)
  [OK] door swing: entry: quarter-disc sweep is clear
  [!!] door swing: ห้องน้ำในตัว (ensuite): swing not specified — leaf arc not checked (add door.swing in/out-left/right)
  -> FAIL  (1 fail, 7 warn)
```
**Interpretation of the FAIL/WARNs:**
- `[XX]` **ensuite-access 120 mm** — the sleeping cluster's north edge sits 120 mm from
  the ensuite's as-built south wall, leaving a dead pinch behind the bed; the ensuite is
  reachable via the wider west corridor, but the pathfinder's shortest route hits the
  120 mm gap. **Root cause = the 2134 N-S bed in a 2950 band; the fix is the bed-orientation
  decision (owner), not a nudge.** Non-statutory (Panero floor), so the statutory gate is
  unaffected.
- `[!!]` **narrow-side (ข้อ 20)** — statutory, but an *interpretation* WARN (legs 2200–2850;
  sleeping zone is a 2850 leg). Not a hard violation; resolvable by widening the 2200 leg
  or a human call.
- `[!!]` **4 overlaps** — all headboard/platform/bed/nightstand against the headboard wall
  (stacked/against-wall = OK, not collisions).
- `[!!]` **armchair rot 225°** — non-axis-aligned footprint checked unrotated (engine limit,
  shared with placement/camera); verify on plan. In-bounds either way.
- `[!!]` **ensuite door swing** — modelled as sliding (no arc); add `door.swing` if hinged.

### FUNCTION gate — placement_logic (verbatim)
```
placement_logic: specs/master_bedroom.json -> WARN  (tv=absent, viewer=bed)
  [ok  ] door_vs_bed_head: bed head ('north') is clear of the door wall ('east')
  [ok  ] furniture_dimensions: furniture sizes/heights within ergonomic norms
  [WARN] bathroom_logic: ห้องน้ำในตัว (ensuite): the wet zone (shower/tub) is not pushed to the back (wet mean 2145 ≤ dry mean 2192 mm) — GS-05 wet/dry zoning
  [ok  ] camera_has_a_reason: eye camera frames ฐานเตียง from 2.3 m (26 mm; 100% of view directions on a subject)
```

---

## 2 · sitting_room — `PASS`

**Verdict:** statutory PASS · ergonomic PASS · FUNCTION PASS. Clean on both gates. (Depth
3300 mm is an ESTIMATE pending a cleaner CAD export — a firmer depth only widens margins.)

### Gate 0 — clearance (verbatim)
```
=== suite clearance sitting_room.json (metric, Thai code, Gate 0) ===
  [OK] ceiling height (room): clear 2800 mm >= 2600 floor-to-floor min -> compliant a fortiori (ฉ.55 ข้อ 22 (ระยะดิ่ง พื้นถึงพื้น))
  [OK] door width: 1000 mm vs 800 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] door height: 2000 mm vs 1900 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] floor area (informational): 16.8 m² — not detected as a bedroom (by type/items heuristic); if it IS one, ฉ.55 ข้อ 20 applies (>= 8 m² net, narrow side >= 2500 mm); unit-level ฉ.55 ข้อ 19 (20 m²) binds the whole unit, not this room
  [OK] in-bounds: โซฟา 3 ที่นั่ง: inside the net room
  [OK] in-bounds: โต๊ะกลาง (round coffee table): inside the net room
  [OK] in-bounds: เก้าอี้อาร์มแชร์ 1: inside the net room
  [OK] in-bounds: เก้าอี้อาร์มแชร์ 2: inside the net room
  [OK] in-bounds: คอนโซล/ตู้โชว์เตี้ย ผนังตะวันตก (BF12): inside the net room
  [OK] circulation: entry -> โซฟา 3 ที่นั่ง: bottleneck 1698 mm >= 910 main walkway (ergonomic; reach tolerance 300 mm)
  [OK] door swing: entry: quarter-disc sweep is clear
  -> PASS  (0 fail, 0 warn)
```

### FUNCTION gate — placement_logic (verbatim)
```
placement_logic: specs/sitting_room.json -> PASS  (tv=absent, viewer=sofa)
  [ok  ] furniture_dimensions: furniture sizes/heights within ergonomic norms
  [ok  ] seating_faces_focal: lounge seating is oriented toward a focal (table/TV/other seat)
  [ok  ] camera_has_a_reason: eye camera frames โซฟา 3 ที่นั่ง from 3.3 m (28 mm; 80% of view directions on a subject)
```

---

## 3 · living_room — `PASS` (with ergonomic REVIEW notes)

**Verdict:** statutory PASS · **FUNCTION PASS — every TV rule green** · ergonomic REVIEW
(3 non-statutory warn). This is the room the designer's round-2 critiqued (TV on the floor
/ TV behind the seated viewer); the FUNCTION gate now confirms the fix: TV wall-mounted at
900 mm, faces the sofa, sofa faces TV, distance 3277 mm in range, no seat in the sightline.
(Envelope 4800×4200 is an ESTIMATE pending a cleaner CAD export.)

### Gate 0 — clearance (verbatim)
```
=== suite clearance living_room.json (metric, Thai code, Gate 0) ===
  [OK] ceiling height (room): clear 2800 mm >= 2600 floor-to-floor min -> compliant a fortiori (ฉ.55 ข้อ 22 (ระยะดิ่ง พื้นถึงพื้น))
  [OK] door width: 900 mm vs 800 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] door height: 2400 mm vs 1900 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] floor area (informational): 20.2 m² — not detected as a bedroom (by type/items heuristic); if it IS one, ฉ.55 ข้อ 20 applies (>= 8 m² net, narrow side >= 2500 mm); unit-level ฉ.55 ข้อ 19 (20 m²) binds the whole unit, not this room
  [OK] in-bounds: โซฟา 3 ที่นั่ง (F03): inside the net room
  [OK] in-bounds: โต๊ะกลาง 1x1m (F03.100x100): inside the net room
  [OK] in-bounds: อาร์มแชร์ ตะวันตก: inside the net room
  [OK] in-bounds: อาร์มแชร์ ตะวันออก: inside the net room
  [OK] in-bounds: โต๊ะข้างโคมไฟ ซ้าย: inside the net room
  [OK] in-bounds: โต๊ะข้างโคมไฟ ขวา: inside the net room
  [OK] in-bounds: ตู้คอนโซล/media ผนังเหนือ (F02.200x40x50): inside the net room
  [OK] in-bounds: ทีวี แขวนผนัง: inside the net room
  [!!] overlap: โซฟา 3 ที่นั่ง (F03) / โต๊ะข้างโคมไฟ ซ้าย: footprints intersect (ok if stacked/against a wall)
  [!!] overlap: ตู้คอนโซล/media ผนังเหนือ (F02.200x40x50) / ทีวี แขวนผนัง: footprints intersect (ok if stacked/against a wall)
  [!!] circulation: entry -> โซฟา 3 ที่นั่ง (F03): bottleneck 850 mm — passable but below the 910 main-walkway ergonomic target (dimensional_rules circulation)
  [OK] door swing: entry: quarter-disc sweep is clear
  -> REVIEW  (0 fail, 3 warn)
```
**Interpretation:** the two overlaps are a side-table beside the sofa arm and the TV wall-
mounted above the media console (both against-wall/stacked = OK, not collisions). The
850 mm entry→sofa bottleneck is passable, 60 mm under the 910 comfort target — a
non-statutory REVIEW note, not a violation.

### FUNCTION gate — placement_logic (verbatim)
```
placement_logic: specs/living_room.json -> PASS  (tv=positioned, viewer=sofa)
  [ok  ] tv_positioned: TV has its own coordinates (build_room can place the control mass)
  [ok  ] tv_faces_viewer: TV is in front of the sofa (in the line of sight)
  [ok  ] tv_not_over_viewer: TV is clear of the sofa footprint
  [ok  ] tv_viewing_distance: sofa–TV 3277 mm within 1500–4500
  [ok  ] furniture_dimensions: furniture sizes/heights within ergonomic norms
  [ok  ] seating_faces_focal: lounge seating is oriented toward a focal (table/TV/other seat)
  [ok  ] seating_clear_of_screen: no lounge seat sits in the viewer→TV sightline
  [ok  ] tv_mount_height: wall TV mounted at 900 mm AFF (base), top 1700 mm — floats on the wall
  [ok  ] camera_has_a_reason: eye camera frames โซฟา 3 ที่นั่ง (F03) from 3.6 m (35 mm; 100% of view directions on a subject)
```

---

## Gate ruling (Stage 03)

| room | statutory (codes-th) | collisions | ergonomic (Panero) | FUNCTION | stage status |
|---|---|---|---|---|---|
| sitting_room | PASS | none | PASS | PASS | **PASS — gate met** |
| living_room | PASS | none | REVIEW (3 warn, passable) | PASS | **PASS — gate met, ergonomic notes** |
| master_bedroom | PASS (narrow-side WARN) | none | **FAIL (120 mm)** | WARN | **REVIEW — owner decision** |

- **HARD gate (zero collisions, zero codes-th violations):** met on all three — no
  overlaps are real collisions (all against-wall/stacked); no statutory row FAILs
  (master's narrow-side is an unresolved *interpretation* WARN, not a violation).
- **sitting_room + living_room advance** to Stage 04 (living carries ergonomic REVIEW notes;
  both carry ESTIMATED-envelope flags).
- **master_bedroom does NOT cleanly close.** Its 120 mm ensuite-access ergonomic FAIL is a
  real buildability flag rooted in the 2134-deep N-S bed in a 2950 band. Per the spec's own
  note, this must not gate a deliverable until the owner confirms **bed orientation**.

## Owner questions carried forward (blocking the master deliverable, not Stage-04 on the other two)
1. **master_bedroom bed orientation — N-S or E-W?** The spec models N-S (headboard north,
   foot to the south terrace glazing); the CAD `bed bench 1` insert (rot 270) implies E-W
   (headboard on a side wall). N-S cannot meet the ergonomic walkway floor in this band; E-W
   likely can. This is the decisive input for the 120 mm FAIL.
2. **Estimated envelopes** — sitting_room depth (3300) and living_room (4800×4200) are
   plan-proportion estimates; a cleaner CAD/DWG export would firm them (both currently pass
   with margin, so this is a confidence, not a blocker, item).

## Engine scope limits (unchanged, not violations)
- Non-axis-aligned (non-90°) footprints checked unrotated across placement/clearance/camera
  (the master armchair rot 225°, the living armchairs rot 90/270 swap w/d correctly).
- Turning circles + knee/toe: pending furniture-catalog metadata (ffe-research pass).
- ข้อ 21 1500-tier / ข้อ 22 3000-tier: n/a to these house rooms (no WARN fired).
