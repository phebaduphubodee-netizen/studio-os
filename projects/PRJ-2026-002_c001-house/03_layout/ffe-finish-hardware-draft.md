# FF&E draft — built-in finishes & hardware (PRJ-2026-002, 3 rooms)

> DRAFT / back-office FF&E slice. Maps each **built-in** element in the real-takeoff room specs
> (`pipeline/scripts/specs/{master_bedroom,sitting_room,living_room}.json`) to concrete Thai products
> from the studio vault. Covers **millwork FINISH + HARDWARE only**; loose furniture (`items`: bed,
> sofa, armchairs, nightstands, coffee/side tables) + sanitaryware = separate FF&E (web / other suppliers).
>
> SOURCES (all cited): `knowledge/materials/wall-cladding-and-decorative-mouldings-th.md`,
> `knowledge/materials/aella-hardware-th.md`, `knowledge/studio-vault/40-Suppliers/discord-supplier-directory.md`.
> STATUS: **layout provisional** (positions per the CAD-dimension takeoff, pending owner confirmation) —
> but finish/hardware selection is **robust to exact position**, so this is safe to draft now.
> PRICES: supplier list, **VAT status unstated on the sheets — re-confirm before quoting**; metric mm/THB.
> This is the first artifact that CONSUMES the fetched Discord catalogues → closes "citable → consumed".

Convention: **carcass door faces** → laminate (Formica/Lamitak/EDL) or CO-EX/VCP panel; **feature walls**
(TV wall, headboard) → WPC slat / AKUWALL / STONE WALL; **all hardware** → AELLA.

## Master bedroom — builtins: 2 wardrobes + headboard wall
| Element (dims mm) | Finish / material candidate | Hardware candidate (AELLA) | Est. qty | Indicative | Cite |
|---|---|---|---|---|---|
| Wardrobe, west wall `BF11` (600 d × **2300** run × 2800 h) | door face: laminate 1220×2440 (Formica PROTEC+ ~1,020–1,930 /sheet · Lamitak · EDL) **or** CO-EX/VCP 8×1220×2900 (3,500 /sheet) | parliament/butt hinges **H50-series** (sold in **pairs**; ~5/leaf @2800 h) · vertical pulls **long bar L3018 4XL = 288** or knob | ~4 leaves → **~9 hinge-pairs** + **4 pulls** | hinges pair + pulls 250–2,100 ea | aella §hinges/§long-bar · supplier-dir Formica/EDL |
| Wardrobe/dresser, NE corner `BF09-3` (2100 run × 600 d × 2800 h) | same | same | ~4 leaves → ~8 hinge-pairs + 4 pulls | as above | aella |
| Headboard built-in wall (**2200 w × 1400 h** = 3.08 m²) | **AKUWALL acoustic** (catalogue application = "bedroom headboards") 1200×2900 oak-veneer ×2, trim to 1400 **or** **WPC slat** 10×150×2900 ×~15 (economical) | — | AKUWALL 2 panels **or** ~15 slats | AKUWALL veneer ~2×16,470 (offcut-heavy at 1400 h) · **WPC ~15×440 ≈ 6,600** | wall-cladding §1d / §1a |

## Sitting room — builtin: 1 low display console
| `BF12` low console/cabinet (500 d × **1100** run × 600 h) | door face laminate or CO-EX/VCP | AELLA **square handles L1037/L1054** (230–650) or edge pulls · butt hinges | ~2 doors → 4 hinges + 2 pulls | pulls 230–650 ea | aella §square/§edge · supplier-dir |

## Living room — builtins: media console + TV feature wall
| Media console, north wall `F02` (2000 run × 400 d × 500 h) | door/drawer face laminate or CO-EX/VCP | AELLA **long bar pulls L30xx** or drawer pulls L3118/L3129 (210–990) · hinges/slides | ~4 doors/drawers → 4–6 pulls | pulls 210–990 ea | aella §drawer/§long-bar |
| **TV feature wall** behind wall-mounted TV (`tv_panel` 1400 w × 800 h @ mount 900; est. feature zone ~2400 w × 2800 h ≈ 6.7 m²) | **WPC slat** 10×150×2900 ×~16 (SQW10 440 /pc std) **or** **AKUWALL** (home-theatre app) 1200×2900 ×2 **or** **STONE WALL** PU 600×1200 (no price) | — | WPC ~16 slats | **WPC ~16×440 ≈ 7,040** · AKUWALL PVC 2×14,400 = 28,800 | wall-cladding §1a/1d/1f |

## Covered vs. not
- ✅ **Covered by this draft** (from vault): all built-in finishes + all door/wardrobe/cabinet hardware + TV & headboard feature walls.
- ⛔ **Not covered** (needs a separate FF&E pass — web / sanitaryware / lighting suppliers): loose furniture
  (bed, bed bench, nightstands, sofa, armchairs, coffee/side tables), the ensuite fixtures (wc/tub/shower/vanity), and light fittings.

## Next step
When owner confirms furniture layout (or supplies a clean CAD/elevation), promote this into the full
`03_layout/ffe-candidates.json` via the `ffe-research` skill: add the loose `items` with real dims/prices,
lock finish/hardware picks above, and let the scene-graph pull each selected `dimensions_mm` into drawings + BOM.
