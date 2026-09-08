# Floor-2 v4 reading notes (owner-authoritative dims + deterministic furniture reads)

Division of labor (RESTART-PROMPT-floor2-v4.md): OWNER = ground-truth for every dimension /
wall / built-in size. Claude transcribes + places. Machine (placement_gate) verifies
completeness / no-floating / on-ink only. Loose-furniture position/size/angle = read from the
drawing (clusters + oriented boxes). NO dimension eyeballed off the raster.

## BF label format (now unambiguous, verified on all 9 labels)
`BF{code}.{Wcm}x{Dcm}x{Hcm}CM` — all three numbers are CENTIMETRES.
The prior "1520 / 2150" values were a MIS-PARSE: the code's `-1`/`-2` was glued onto the
dimension (`BF09-1.520` misread as `1.520 m`). Owner re-read (2026-07-05) confirms the cm reading.

## Built-ins — OWNER-AUTHORITATIVE (mm = cm×10)
| BF | W×D×H mm | wall / position (owner) | identity |
|----|----|----|----|
| BF09-1 | 5200×600×2800 | wardrobe bay, top-right corner in front of bathroom (N) — bay is only 2500×2800, so 5200 = an **L wrapping N wall (2500) + E wall (2700)** | wardrobe — **owner CONFIRMED the L (2026-07-06)** |
| BF09-2 | 1500×600×2800 | next to ensuite door, runs south, S end meets BF10 | wardrobe — owner CONFIRMED position (meets BF10, clears door) |
| BF09-3 | 3300×600×2800 | on the divider N of the bed, runs E-W | wardrobe over bed — **owner CONFIRMED 330×60×280 (2026-07-06); earlier "150" was a slip** |
| BF10 | 2500×600×2800 | DRESSING (between BF11 and BF09-2), against the ensuite south wall, E-W — owner correction 2026-07-05: NOT the vanity | cabinet/shelf. The ensuite's double vanity is separate sanitaryware. |
| BF11 | 3200×600×2800 | master WEST wall, N-S, chair faces into it | built-in work desk |
| BF12-1 | 1575×400×2800 | sitting WEST/party wall, NW, behind sofa, next to door | display cabinet |
| BF12-2 | 700×400×2800 | sitting SW, orchid console against the y2650 wall | console |
| BF13 | 4100×300×500 | sitting EAST wall, N-S — sofa faces it | low media shelf + TV |
| BF14 | 3250×100×2800 | master EAST wall behind the headboard, N-S | headboard slat |

## Deterministic wall grid (floor2-walls-mm.json, vector, verified <1%)
master west x0 · party wall x5750 (sleeping interior x5500, north-wing x5650) · sitting east x10650
· suite north y8650 · ensuite south y5850 (x0–3150) · sitting north y6250 · master south niche y-450.
Owner-circled zone dims: 5500 (master W) + 5100 (sitting W) = 10600 ✓; 2850/2950/700 west stack.

## Sitting SOUTH = INDOOR lounge by the glass (NOT a terrace) — CORRECTED 2026-07-06
> CORRECTION (owner 2026-07-06): "the tub chairs ARE floor 2; there is NO terrace — outside the
> wall is grass BELOW; the trees are not on a balcony." So the south area is an INDOOR floor-2
> lounge by the south glass facade (the 2 tub chairs + round table are real floor-2 furniture),
> and the garden TREES are ground level (y<0), OUTSIDE/below the glass — not floor-2 planters.
> Actioned: dropped the manifest `terrace` slab + tree-planters; the tan `sitting_terrace` floor
> zone became the interior green `sitting_lounge` (y0–2050). Chairs kept + owner-aimed (rot 8/332,
> converge just right of the left tree below). The prose BELOW is the superseded terrace reading.

The sitting room is enclosed only down to the exterior door line; SOUTH of it is an OUTDOOR
terrace lounge (2 tub chairs + 1 round table + trees). The envelope JOGS (owner: "an L wall
juts from the west first, THEN the sliding door"):
  * WEST of the L (x5752–7050): south wall = console wall at **y2600** (BF12-2 orchid console in
    its niche projects south of it). CONFIRM: is BF12-2 indoor, or terrace-side?
  * the **L pier** turns south at **x7050–7150** from y2600 down to y2050.
  * **sliding glass door** (2-panel) = **x7150–9900 at y2050** (glass = thin lines, not in the
    wall extract → renders as the wall gap already). Solid wall east x9900–10450.
Floor zones now follow this jog (4 convex rects: green room + green bay east-of-L + tan terrace
W up to y2600 / tan terrace E up to y2050). Tub chairs FACE OUT to the garden (rot 12 / 335,
sightlines converge ~(6670,-650) at the terrace tree) — NOT the earlier inward-to-a-table read.

## Loose furniture — read from clusters (plan_cluster) / oriented boxes
MASTER: bed 7'×6.5' (E-W 1981 × N-S 2134) head EAST vs BF14, foot faces W; foot bench id37
(504×1002) at west foot; 2 lamp nightstands id30 (NE)/id41 (SE) flank the head, both ~300×300;
desk chair id18 (546×516) faces W into BF11; TV/west-wall unit id34 (600×2052).
SITTING: 3-seat sofa id7 (1002×2202) faces EAST toward BF13/TV; round table id18 (Ø600) between
chairs; round table id9 (Ø600) beside sofa; **2 tub chairs id19/id17 — ANGLED** (min-area boxes
52°/72°), placed at true angle facing the focal round table (left rot≈120°, right rot≈290°),
realistic ~680×640 (NOT the 774 AABB, NOT forced cardinal — per owner feedback).

## Non-furniture to dismiss (human-signed)
sitting NW door swing id2 (894×948); terrace tree id20 (924×684, y<0 = planting); master SW wall
hatching id38; west-wall riser symbols id14/id25. (Confirm against the live gate output.)

## Confirm log
- ✅ BF09-3 = 3300×600×2800 — owner CONFIRMED 2026-07-06 (earlier "150" was a slip).
- ✅ BF09-1 = 5200 L-wrap (N leg 2500 + E leg 2700) — owner CONFIRMED the L 2026-07-06.
- ✅ BF09-2 meets BF10 exactly at the SE corner + clears the ensuite door (gap y6698–7596) — owner-directed 2026-07-05.
- ✅ BF10 = dressing cabinet, NOT the ensuite vanity — owner correction 2026-07-05.

## Resolved 2026-07-06 (owner)
- **TV/west-wall = TALL TV cabinet** — identity confirmed; footprint 2046×600 from cluster, **height set 1800** (owner "ตู้ทีวีสูง").
- **BF12-2 is INDOOR** (not terrace-side) → floor zone reverted to a uniform y2050 room/terrace split (the L-jog zones were an over-correction; the L pier stays as a rendered wall + keyplan annotation).
- **BF12-2 (700×400 tall cabinet) and the ORCHID TABLE (~1002×402, cluster id2) are SEPARATE pieces** — un-merged (I had wrongly fused them as one "console+orchid"). BF12-2 sits against the y2600 wall; the orchid console table is loose furniture in front. Confirm BF12-2's exact spot vs the table.
- tub chairs face OUT to the garden (rot 12/335); sliding glass door (x7150–9900 @ y2050) + L pier read.
