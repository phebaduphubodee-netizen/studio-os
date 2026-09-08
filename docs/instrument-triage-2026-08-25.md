# Reachability triage — merged verdict table (2026-08-25)

Provenance: per-instrument verdicts from the clerk fan-out over `qa/reachability-baseline.txt` (81 rows), merged with cross-clerk consistency enforced: an ALREADY-REACHED whose only named consumers are themselves DELETE in this batch is demoted to DELETE (4 demotions: confidence, cross_signal, floorplancad_adapter, rationale); trn002_lightcheck flips DELETE→ALREADY-REACHED because texture_check (WIRE) statically imports it at texture_check.py:87; discord_ingest demoted WIRE→DELETE (re-run stalled ~6 weeks on an owner-minted token; ingest lane closed; git recovers). Spot-checks run live: gen_diff (build_room.py:229/:11192), dim_check (build_room.py:396), plus existence_check :368, bed_pixels :565, p2_exit :610; CLI-ONLY mechanism verified at scripts/reachability_check.py:114/219; warehouse.py exists; open-decisions.json rows 542/1130/1393/1440 verified. facing_reader was not in the clerk batch — it is ALREADY BEING WIRED by the main session tonight and is listed here so no one double-wires it.

| instrument | verdict | consumer / reason |
|---|---|---|
| facing_reader | WIRE (in progress) | Being wired by the main session tonight — do not touch, do not double-wire |
| cloth_highlights | WIRE | build_room.py post-render spawn beside bed_pixels (:565); P2r-5's declared instrument, open-decisions.json:542/2135 name it; ~3 lines |
| texture_check | WIRE | build_room.py full-fidelity spawn block (same site); fabric surface = both critics' #1 on DELIV-001; keeps trn002_lightcheck alive (import :87); advisory-print first |
| glb_flatten | WIRE | warehouse.py post-fetch: spawn when glTF chunk shows per-triangle primitives; plan lever 2 (deliverable-plan.json:509); ~5 lines, same commit as mesh_density |
| mesh_density | WIRE | warehouse.py post-fetch screen — sourcing-tiers.json's own standing instruction with no consumer; ~3 lines, same commit as glb_flatten |
| bedcloth_bench | WIRE (declaration) | One `CLI-ONLY:` header line (blender -b … D-104/D-119 lane); cannot be deleted — open-decisions.json:1130/1393/1440 `where` paths would fail decisions_check |
| bedcloth_shoot | WIRE (declaration) | One `CLI-ONLY:` header line (owner-eye candidate shoots); named in open-decisions.json:1130 `where` |
| dwg_ingest | WIRE (declaration) | One `CLI-ONLY:` line — reachability_check.py:54 names it as its own intended example; sheet-first DXF work live |
| research_call | WIRE (declaration) | One `CLI-ONLY:` line; deleting forces DR through BRAINDEAD/gemini_query.py's contaminated system prompt; load-bearing 08-08 upgrade DR |
| upscale | WIRE (declaration) | One `CLI-ONLY:` line; checker docstring names it by name; closes disclosed Stage-07 native-res gap |
| bed_pixels | ALREADY-REACHED | build_room.py:565 subprocess spawn (verified); exit adjudicated by rule_gate.py:1031 |
| benchmark_precut | ALREADY-REACHED | look_bench.py:35 import; look_bench = R4 standing command (CLAUDE.md) |
| blenderkit | ALREADY-REACHED | Active owner order ORD-2026-08-22; sourcing-tiers.json:110 tier fetcher; fetch-log modified in today's working tree |
| critique_call | ALREADY-REACHED | R7b every-render mandate; owner-orders.json:72,97 obeyed_where + open-decisions.json:288 `where` (orders/decisions_check enforce) |
| dim_check | ALREADY-REACHED | build_room.py:396 blocking subprocess spawn — spot-checked live |
| edge_shadow | ALREADY-REACHED | p2_exit.py:45 import; p2_exit spawned at build_room.py:610 (verified) |
| existence_check | ALREADY-REACHED | build_room.py:368 blocking R10 spawn (verified) |
| ffe_schedule | ALREADY-REACHED | .claude/skills/ffe-research/SKILL.md:74,141 skill command (stands even with suite_package deleted) |
| furnimesh | ALREADY-REACHED | sourcing-tiers.json:30 tier tool (sourcing_check) + owner-orders.json:549 obeyed_assert greps the file |
| gen_diff | ALREADY-REACHED | build_room.py:229 subprocess path, called at :11192 every full round — spot-checked live; ORD-2026-08-13 pins the site |
| glance | ALREADY-REACHED | blenderkit.py:1006-1007 import+call; owner-orders.json:540 obeyed_where |
| look_bench | ALREADY-REACHED | CLAUDE.md R4 standing command; deliverable-plan P5 exit condition; pick_reproduction_target.py:35 import |
| p2_exit | ALREADY-REACHED | build_room.py:610 subprocess spawn (verified); plan-of-record P2 exit harness |
| pick_reproduction_target | ALREADY-REACHED | reproduction-curriculum.md:858 charter draw step (standing owner order, TRN-002 in flight) |
| raster_overlay | ALREADY-REACHED | gen_floor2_v4_specs.py:535,538 (outside checker scan dirs); outputs enforced by reached placement_gate.py:903-923 |
| synth_plan_pdf | ALREADY-REACHED | test_bluehouse_plan_reader.py:876 import — sole negative-control fixture for the live plan reader's fail-closed scale |
| trn002_lightcheck | ALREADY-REACHED (flipped from DELETE) | texture_check.py:87 static import (verified); survives because texture_check is WIREd. If texture_check's wire is refused, both go together |
| activity_taxonomy | DELETE | All importers (persona/rationale/suite_package) dead in this batch; advisory persona lane, no entry point |
| anomaly_flags | DELETE | Tier-1 doubt lane, all importers unreached; parked since 07-16 reset |
| audit_model_fit | DELETE | Zero references anywhere; stale one-shot audit constants |
| benchmark_reader | DELETE | All five importers unreached; F2 lane closed; git recovers |
| blind_wall_lane | DELETE | Research cluster, only importer unreached; delete with unit_adoption_lane |
| closure_run | DELETE | Plan-gate lane closed (e13eace); no consumer |
| confidence | DELETE (demoted from ALREADY-REACHED) | Only consumers self_audit.py:510 + flag_localization.py:97 — both DELETE in this batch; rides with the doubt island |
| cross_signal | DELETE (demoted from ALREADY-REACHED) | Same shape: self_audit.py:423 + flag_localization.py:95, both DELETE |
| derive_curve_priors | DELETE | One-shot derivation; output committed in qa/priors; no caller |
| dim_string_score | DELETE | Takeoff lane closed; test-only consumers |
| discord_ingest | DELETE (demoted from WIRE) | Re-run stalled ~6 weeks on a bot token only the owner can mint; ingest lane recorded closed; git recovers when a token exists |
| eval_retrieval | DELETE | M1.1 milestone long passed; no invoker |
| f2_facing_lane | DELETE | Research cluster (importers all unreached); delete cluster as one commit |
| facade_reader | DELETE | Paused floor2 lane; placement_gate reads only its output json if present |
| flag_localization | DELETE | Hand-run bench, no caller; same commit as self_audit/rebuild_diff |
| floor2_defect_gate | DELETE | Floor2 lane paused; no import/spawn anywhere; git recovers at resume |
| floorplancad_adapter | DELETE (demoted from ALREADY-REACHED) | Named importers kind_priors.py:51 + svg_plan_reader.py:61 are both DELETE; whole island goes together |
| glazing_candidates | DELETE | Importers facade_reader/svg_plan_reader both DELETE; bluehouse reader computes its own glazing |
| golden_set_curate | DELETE | M3.2 judge lane deferred (kappa degenerate); prose-only references |
| judge_calibrate | DELETE | Same deferred M3.2 lane; labels never filled |
| kind_priors | DELETE | Island hub, all importers unreached; own docstring fences it from gate paths; delete island as one unit |
| mutation_probe | DELETE | Zero references; hardcoded to a closed incident |
| nlm_provenance | DELETE | Prose-only references; NLM lane under unsub review |
| persona | DELETE | Only importer rationale (also DELETE); persona.json never authored |
| pilot_blindpack | DELETE | Sellability pilot explicitly UNWIRED, never ran |
| plan_symbol_unit | DELETE | Importers unreached; co-delete with unit_adoption_lane |
| precut_pair | DELETE | Same parked pilot lane; exits 2 waiting on labels that never came |
| probe_duvet_levers | DELETE | One-shot probe; answer archived; lane moved to acquired cloth |
| rationale | DELETE (demoted from ALREADY-REACHED) | Sole consumer suite_package.py:240 is DELETE; falls in the same commit, with test_rationale.py |
| rebuild_diff | DELETE | Importers self_audit/flag_localization both DELETE; same commit |
| render_mask_labels | DELETE | Prose-only references; feeds structured3d_adapter (also DELETE) |
| rot_reconcile | DELETE | Premise refuted 2026-07-09 by its own docstring; convention pinned elsewhere |
| self_audit | DELETE | Checker's own canonical unwired example; lane dead ~6 weeks; same commit as flag_localization/rebuild_diff |
| structured3d_adapter | DELETE | Consumers all DELETE; durable outputs persist as committed data |
| style_embed | DELETE | CLIP lane unwired pending designer pilot; test-only consumer |
| suite_elevations | DELETE | v0.2 CAD suite; delete the four suite_* files as one commit |
| suite_package | DELETE | CD-set assembler, no entry point; remove TestSuitePackageIntegration in same commit (guarded skip would go silent) |
| suite_plan | DELETE | Suite cluster hub; all consumers in-cluster |
| suite_rcp | DELETE | Only importer suite_package; leaves suite_lighting/lighting untouched |
| svg_plan_reader | DELETE | Cluster hub, all 8 importers themselves DELETE; one commit with siblings |
| swing_door_candidates | DELETE | Benchmark lane; test-only consumers |
| symbol_unit_lane | DELETE | One-shot research measurement; co-delete with plan_symbol_unit |
| synth_plan_2d | DELETE | Retired research hub; delete only together with sibling importers |
| trn001_lightcheck | DELETE | TRN-001 closed 08-02; successor exists |
| trn001_matcheck | DELETE | TRN-001 closed; remove/skip the 9 importing tests in test_trn001_geom.py |
| trn001_measure | DELETE | Lane-specific, lane closed |
| trn001_overlay | DELETE | Lane closed; shared grammar lives in overlay_fidelity.py |
| trn001_solve | DELETE | Lane-specific solver, lane closed |
| trn002_lines | DELETE | Reproduction lane closed; fix/remove test_trn002_geom.py:83 import in same commit |
| trn002_look | DELETE | Zero references anywhere |
| trn002_station | DELETE | One-shot driver, output spec on disk |
| trn002_station_r2 | DELETE | Same class, zero references |
| unit_adoption_lane | DELETE | Corpus lane closed 07-10; test-only consumer |
| wall_aware_lane | DELETE | Transitive deadness; delete with its three importers (all DELETE here, condition satisfied) |
| wall_detect | DELETE | Importers both DELETE; doctrine preserved in reports |

Batch discipline for the executor: the research islands (svg_plan_reader cluster, doubt suite, suite_* CAD set, TRN lanes, persona/rationale) must each be deleted as one commit or surviving imports/tests go red; three WIRE files (bedcloth_bench/shoot, cloth_highlights) are named in open-decisions.json `where` fields, so any future deletion requires decision-row edits, not just rm.

## Execution status (2026-08-26 night)

- Owner approval: "ลุยเต็มที่ ผมอนุมัติทุกอย่าง" on debate proposal 5 (docs/process-debate-2026-08-25.md).
- DONE tonight: facing_reader wired (front_registry -> rule_gate.check_room + build_room); 5 CLI-ONLY declarations added (bedcloth_bench, bedcloth_shoot, dwg_ingest, research_call, upscale); baseline pruned of the 5 checker-reported closed rows.
- NAMED FOLLOW-UP (one clean commit, next build session; decision row D-142 carries the default): 4 code wires (cloth_highlights + texture_check into build_room's post-render spawn block; glb_flatten + mesh_density into warehouse.py post-fetch) and the 55 DELETE verdicts (git-recoverable; their test files go in the same commit). Executing 55 deletions mid-flight in a working tree another session holds uncommitted work in is churn, not diligence.
- Standing rule adopted with the table: NO NEW INSTRUMENT lands without its gate-path consumer named in the same commit.
