# De-wood experiment — master bedroom (2026-07-15)

WHY: first sellability-pilot verdicts + interior-render-critique DR + Gemini critique.py all
flagged the master bedroom's MONO-TIMBER palette (walnut on floor/headboard/wardrobe/TV) as the
#1 Critical defect (material_variety 2/5).

CHANGE (Stage-04 render OVERLAY, owner-signed v4 geometry UNTOUCHED):
- `master_bedroom.dewood.spec.json` = v4 scene-graph (read-only) + eye_camera + a `materials`
  block overriding ONLY `surfaces.millwork` = `warm_white_paint`. So the wardrobe/TV/desk/shelf
  planes leave the wood palette and join the warm-white 60% base; oak floor + walnut headboard
  (BF14) stay as the 30% wood. build_room applies it at the Cycles level (no Gemini needed).

RESULT (critique.py --model pro, enriched rubric; clay-vs-clay, only materials differ):
| dimension                  | old clay (walnut) | new clay (de-wood) |
|----------------------------|-------------------|--------------------|
| material_variety           | 2/5               | 4/5  (fix landed)  |
| architectural_plausibility | 1/5               | 1/5  (hole untouched) |
| overall / verdict          | 1/5 PLACEHOLDER   | 1/5 PLACEHOLDER    |

READ: the material lever moved the material metric; the gate correctly did NOT reward the BF14
cavity (geometry not changed). Overall stays PLACEHOLDER because these are RAW CLAY controls —
the Gemini beauty pass that lifts clay->client-grade is BILLING-BLOCKED (eye-camera.master_bedroom
.json _beauty_pass_next: HTTP 429 prepayment credits depleted), and the BF14 end-cap/cavity is an
owner-signed Stage-03 geometry call (under parallel-session review) — NOT edited here.

NEXT (owner): (1) top up Google AI Studio credits -> run the Gemini beauty pass on this new clay;
(2) approve a BF14 end-cap/return + closed cavity in the v4 geometry to fix architectural_plausibility.
