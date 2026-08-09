"""spec_r32 -> spec_r33.  THE TWO TEXTILES THAT DECLARED A RELIEF AND NEVER GOT ONE.

WHAT THE ROUND IS TESTING, WRITTEN DOWN BEFORE THE RENDER
--------------------------------------------------------
Giving `upholstery_bed` and `velvet_taupe` a normal-only linen relief should
raise our σ=2 high-frequency figure on their five objects from 0.008-0.016
toward the target's 0.046-0.075, and should leave LEVEL and SHAPE where r32 put
them, because DIFFUSE_OFF means no colour touches the surface. If SHAPE moves
materially, the relief is changing the shading enough to matter and that is a
finding about the amplitude, not a failure of the round. If the high-frequency
figure barely moves, the amplitude is too low to render — the trn001 result
this lane already paid for, where a physically honest bump rendered as nothing.

WHY THESE TWO, AND NOT THE OTHER THREE
--------------------------------------
Five materials carried a `NORMAL_STRENGTH` that no code path could reach:
`build_materials` returns EARLY for a row with no map, so a relief written for
an unmapped material is an intention that cannot be delivered — the same class
of dead declaration r30 found in the PALETTE and deleted. All five were
candidates. The measurement cut it to two.

`texture_check.py` (built 2026-08-08) high-passes both frames and compares
per object, which separates SURFACE TEXTURE from the LIGHTING GRADIENT that
r32 already settled. Read as a raw ratio it would have sent this round at the
wardrobe: `ward_body` is the largest object in the frame and reads 10.66x at
σ=1. But its two numbers are 0.0049 and 0.0131 — a lacquered door IS smooth in
the target, and a ratio between two near-zeros explodes. Ranked instead by
texture that is ABSENT AND ACTUALLY THERE:

    object          material         ours    target
    bench           upholstery_bed   0.0106  0.0581     43,368 px
    bed_headboard   upholstery_bed   0.0081  0.0457     18,429 px
    bed_platform    upholstery_bed   0.0165  0.0291     18,528 px
    throw_velvet    velvet_taupe     0.0162  0.0749     13,025 px
    petcave         upholstery_bed   0.0073  0.0545      3,154 px

Textiles, ~96,500 px, a 2-7x real deficit, and a relief declaration already
written for both. `paint_ceiling` is EXCLUDED because it measures 1.06 — the
ceiling already matches, and turning on relief there would be building to a
table rather than to a measurement. `paint_white` is EXCLUDED because its own
objects disagree with each other (1.76 / 2.54 / 2.98 / 3.73 / 4.50 / 22.21):
one material cannot be six different amounts wrong, so that deficit is CONTENT
we do not model, not a surface property. `lacquer_wardrobe` is excluded for the
near-zero reason above.

MECHANISM: the machinery already exists and is not being invented here.
`DIFFUSE_OFF` was written for exactly this — "keeps a map set for its NORMAL
(weave, grain relief) but must NOT take its colour variation" — and it is what
protects r32's freshly re-derived albedos from being moved by a texture round.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
spec = json.loads((HERE / "spec_r32.json").read_text(encoding="utf-8"))

spec["id"] = "TRN-002 r33"
spec["round"] = 33
spec["STATUS"] = (
    "r33 = r32 with the two TEXTILE materials given the normal-only linen relief "
    "their NORMAL_STRENGTH already declared and no code path could deliver. "
    "Predicted before rendering: sigma-2 high-frequency on bench / bed_headboard / "
    "bed_platform / throw_velvet / petcave rises from 0.008-0.016 toward the "
    "target's 0.046-0.075; LEVEL and SHAPE hold at r32's values because "
    "DIFFUSE_OFF means no colour is touched. Three of the five dead declarations "
    "are deliberately NOT turned on: the ceiling already measures 1.06, and "
    "paint_white's six objects disagree with each other, which makes that deficit "
    "content rather than surface."
)
# --- repair: r32 turned declared_gaps from {id: reason} into [id], by doing
# `list(spec.get("declared_gaps", []))` on a dict — which yields its KEYS. Ten
# reasons were dropped silently, and three light tickets were then appended as
# if a whole paragraph were a gap NAME. Restore the reasons from r31, key the
# tickets, and keep the dict shape. Found by coverage_check.py, which cannot
# tell a name from a declaration and says so.
r31 = json.loads((HERE / "spec_r31.json").read_text(encoding="utf-8"))
old = r31["declared_gaps"]
repaired, ticket_n = {}, 0
for entry in spec.get("declared_gaps", []):
    if entry in old:
        repaired[entry] = old[entry]
    elif entry.startswith("LIGHT TICKET"):
        ticket_n += 1
        repaired[f"light_ticket_{ticket_n}"] = entry
    else:
        repaired[entry] = "REASON LOST in the r32 list(dict) round-trip — restore it"
spec["declared_gaps"] = repaired

spec["declared_gaps"]["texture_paint_white"] = (
    "paint_white reads 1.76-22.21x the target's fine detail depending on WHICH "
    "object wears it. A single material cannot be six different amounts wrong, so "
    "this is content in the target we do not model — most of it on closet_back, "
    "which already stands in for both a wall and a window. Declared here rather "
    "than fixed with a relief, because a relief would make the number better and "
    "the model worse."
)

(HERE / "spec_r33.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
print("wrote spec_r33.json")
