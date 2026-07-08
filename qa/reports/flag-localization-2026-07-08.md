# flag-localization (benchmark F7) -- PRJ-2026-002_c001-house

**macro localization-recall 1.0** (by-expected 1.0; 6/6 should-flag lanes exercised)  ·  on-target precision 0.949  ·  overfire mutations 0  ·  blind classes: none  ·  unwired (never-exercised) classes: none  ·  backstopped-only classes: none

> Synthetic-answer-key lane: the 'truth' is MINTED by injecting one deliberate error into one item of an otherwise-good read, so recall/precision measure whether the tier-1 self-doubt suite FINGERS the broken item on THIS project. This is NOT a corpus benchmark and does not measure generalisation -- its sibling `benchmark_reader.py` is the have-ground-truth corpus lane (annotated Structured3D / FloorPlanCAD).

## Per-class recall / precision

| class | recall | precision | caught-by-expected | severity-match | n_mut | n_skip |
|---|---|---|---|---|---|---|
| facing_flip_directional | 1.0 | 0.714 | 1.0 | 1.0 | 5 | 21 |
| kind_change_unsigned | 1.0 | 0.929 | 1.0 | 1.0 | 26 | 0 |
| kind_change_vs_signature | 1.0 | 0.929 | 1.0 | 0.0 | 26 | 0 |
| size_implausible | 1.0 | 1.0 | 1.0 | 1.0 | 20 | 6 |
| rot_stripped_directional | 1.0 | 0.667 | 1.0 | n/a | 1 | 25 |
| zone_below_grade_unsigned | 1.0 | 1.0 | 1.0 | 1.0 | 26 | 0 |
| facing_flip_box expect NO flag | n/a (nonflag) | n/a | overfire 0/19 | - | 19 | 7 |

recall = mutations whose planted error raised a NEW on-target flag by ANY collector / eligible mutations. by-expected recall = the same but crediting ONLY the collector the class targets (a lower by-expected number means another collector is backstopping the headline -- listed as *backstopped-only*, so a target-lane regression can't hide). precision = on-target new flags / all new flags (splash onto innocents lowers it). caught-by-expected = share caught by the collector the class targets. severity-match = of hits, share whose expected collector fired at the expected band. *unwired* should-flag classes had zero eligible items -- the lane was never exercised (distinct from *blind* = ran on real items and caught none).

## Misses (planted errors the suite did NOT localize -- the blind spots)
- (none — every eligible planted error raised an on-target flag)

## Overfires (render-inert mutations that WRONGLY raised a flag -- precision leaks)
- (none — every render-inert box-flip stayed silent, as designed)

## Severity gaps (caught, but not at the expected band)
- **ผนังระแนงหัวเตียง BF14 (325x10x280)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้เสื้อผ้าเหนือเตียง BF09-3 (330x60x280)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โต๊ะทำงาน built-in BF11 (320x60x280)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้/ชั้น BF10 (250x60x280)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **เตียง 7'x6.5' หัวตะวันออก** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ม้านั่งปลายเตียง (bench)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โต๊ะข้างเตียง เหนือ (มีโคมไฟ)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โต๊ะข้างเตียง ใต้ (มีโคมไฟ)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **เก้าอี้ทำงาน (หันเข้าโต๊ะ W)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้ทีวีสูง ผนังตะวันตก** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **อ่างล้างหน้าคู่ (ในห้องน้ำ)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โถสุขภัณฑ์ WC** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **อ่างอาบน้ำ (bathtub)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ฝักบัว (shower)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้เสื้อผ้า BF09-1 ขาเหนือ (L 5.2m)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้เสื้อผ้า BF09-1 ขาตะวันออก (L 5.2m)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้เสื้อผ้า BF09-2 (150x60x280)** [scene-graph.master_bedroom.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้โชว์ BF12-1 (157.5x40x280)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ตู้สูง BF12-2 (70x40x280)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **ชั้นวางทีวี ผนังตะวันออก BF13 (410x30x50)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โซฟา 3 ที่นั่ง** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **เก้าอี้ tub ซ้าย (เลานจ์ริมกระจก หันชมสวน)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **เก้าอี้ tub ขวา (เลานจ์ริมกระจก หันชมสวน)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โต๊ะกลม (ระหว่างเก้าอี้)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โต๊ะกลม (ข้างโซฟา)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']
- **โต๊ะวางกล้วยไม้ (console)** [scene-graph.sitting_room.json] (kind_change_vs_signature) — expected CRITICAL, got ['HIGH']

## Collector coverage (was the lane even looking?)
- **cross_signal**: READ
- **anomaly**: READ
- **confidence**: READ
- **rebuild_diff**: READ — F7 supplies the prior round synthetically (unmutated base) per mutation; a REAL prior reading round is absent on this single-round project -- the diff lane is exercised, not idle

READ = the lane had eligible inputs; UNWIRED = ran but nothing eligible (never a pass); ABSENT = no input; ERROR = the lane raised (a blind spot in the harness itself). A low recall under UNWIRED/ERROR coverage means *did not look*, not *clean*.

*Generated by flag_localization.py (F7). Sibling corpus lane: benchmark_reader.py.*
