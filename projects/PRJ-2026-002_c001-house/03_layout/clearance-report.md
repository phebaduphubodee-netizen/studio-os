# Stage 03 — Clearance report · PRJ-2026-002 · 2026-07-02
Engine: suite_clearance v0.4.2 (Gate 0 full: exact maximal-clear-rectangle legs,
L∞-erosion circulation + exact Liang-Barsky LOS, quarter-disc swings, as-built wall
bands; statutory floors from pipeline/dimensional_rules.v0.2.json, cited to
knowledge/codes-th). test_gate0.py 57/57 seeds green at this engine version.

Scene graph: 03_layout/scene-graph.json — byte-identical copy (sha256 f34c999f…)
of pipeline/scripts/specs/bedroom_suite.json (Gate-0-revised layout; anonymized,
real-derived; draft-judgment items per its embedded note). Furniture dims =
client BF program basis; catalog-real FF&E swap = later ffe-research pass.

## Engine output (verbatim)
```
=== suite clearance scene-graph.json (metric, Thai code, Gate 0) ===
  [OK] ceiling height (room): clear 2800 mm >= 2600 floor-to-floor min -> compliant a fortiori (ฉ.55 ข้อ 22 (ระยะดิ่ง พื้นถึงพื้น))
  [OK] ceiling (ensuite): 2000 mm vs 2000 min (ฉ.39 ข้อ 9 (แก้ไขโดย ฉ.63) — พื้นถึงเพดาน)
  [OK] bath area (ensuite): 7.54 m² vs 1.5 m² min (ฉ.39 ข้อ 9 — ห้องน้ำ+ส้วมรวมกัน; fixtures show both)
  [OK] door width: 900 mm vs 800 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] door height: 2000 mm vs 1900 min (studio floor — no general statutory interior-door min (ฉ.55 ข้อ 31 = fire doors))
  [OK] bedroom area (net of sub-rooms): 27.6 m² net as-built (outline 35.8; sub-rooms + wall bands carved exactly) vs 8 m² min (ฉ.55 ข้อ 20)
  [OK] bedroom narrow side (leg-proof, as-built): min clear leg width 2500 mm >= 2500 with sub-room wall bands carved — every maximal clear rectangle is >= 2500 narrow, so the strictest reading of ด้านแคบที่สุด is satisfied (ฉ.55 ข้อ 20)
  [OK] in-bounds: ฐานเตียง: inside the net room
  [OK] in-bounds: เตียง 6 ฟุต: inside the net room
  [OK] in-bounds: หัวเตียง/ทีวี built-in: inside the net room
  [OK] in-bounds: ตู้เสื้อผ้า built-in: inside the net room
  [OK] in-bounds: ตู้ built-in: inside the net room
  [OK] in-bounds: ตู้ built-in ข้างเตียง: inside the net room
  [OK] fixture in ensuite: อ่างอาบน้ำ (tub): inside
  [OK] fixture in ensuite: ฝักบัว (shower): inside
  [OK] fixture in ensuite: อ่างล้างหน้าคู่ 2.85m: inside
  [OK] fixture in ensuite: ชักโครก (WC): inside
  [OK] fixture in ensuite: เก้าอี้เครื่องแป้ง (vanity stool): inside
  [OK] circulation: entry -> เตียง 6 ฟุต: bottleneck 964 mm >= 910 main walkway (ergonomic; reach tolerance 300 mm)
  [OK] circulation: entry -> ensuite door: bottleneck 964 mm >= 910 main walkway (ergonomic; reach tolerance 300 mm)
  [OK] door swing: entry: quarter-disc sweep is clear
  [OK] door swing: ensuite: quarter-disc sweep is clear
  -> PASS  (0 fail, 0 warn)
  (statutory floors from dimensional_rules.v0.2.json thai_code_minimums, cited to knowledge/codes-th.
   ENFORCED: ceiling ข้อ 22 tiers (habitable/ระเบียง; wet = พื้นถึงเพดาน 2000 with ฉ.39) + ฉ.39 bath
   area/width tiers; ข้อ 20 net-area + narrow side and ข้อ 21 corridor width with AS-BUILT wall bands
   (PASS on as-built, FAIL only on the charitable basis, WARN between); in-bounds vs net room;
   overlaps; circulation bottleneck + door-swing arcs (Gate 0; ergonomic floors 610/910 = Panero,
   not statute). Door 800/1900 = STUDIO floor. NOT yet: turning circles, knee/toe (need catalog);
   clearance_check.py unification still open.)
```

## Gate ruling
**PASS — 0 FAIL, 0 WARN, 22/22 checks OK** (collisions/overlaps enforced by the
engine's in-bounds + overlap pass; none reported). Statutory rows proven on the
AS-BUILT basis per Gate-0 doctrine. Contract HARD gate satisfied: zero collisions,
zero clearance violations vs knowledge/codes-th values.

## Known engine scope limits (not violations; tracked in memory/phase status)
- Turning circles + knee/toe clearances: pending furniture-catalog metadata.
- ข้อ 21 1500-tier (in-unit condo corridor) + ข้อ 22 3000-tier (in-unit office/
  dining): interpretation open — n/a to this house-bedroom scene (no WARN fired).
- clearance_check.py (living engine) unification still open — not used here.
