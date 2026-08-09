# GATE — generative-edit probe on trn002_mat_r32 (2026-08-09)

Not a build round. A ฿-scale experiment answering one question the Rebelway research
(`docs/research/2026-08-09-rebelway-ai-interior-workflow.md`) could not answer from any
document: **when an image model is told to change only the surface, does it move our
geometry?** Instrument built first, on purpose: `pipeline/scripts/edge_drift.py`.

## The pair

| | |
|---|---|
| SENT (all three asks) | `_private/…/renders/editprobe-*/trn002_mat_r32.png` — r32 full frame, centre-cropped 1080x821 → 1080x810 (4:3, no resampling; the mask is cut by the same slice) |
| BACK | `after_A_surface_flash.png` · `after_B_relight.png` · `after_C_softgoods.png`, each 2400x1792 |

Prompts: `A_surface.md` · `B_relight.md` · `C_softgoods.md` in this directory. Each carries
the same hard constraint — *do not move, rotate, resize, add or remove any object.*

## The measurement (`edge_drift.py`, 73 objects, tol 3.4 px = 0.25 % of the diagonal)

| ask | model | DRIFT | HELD | UNCHECK | invented edges | what drifted |
|---|---|---|---|---|---|---|
| A surface restyle | 3.1-flash-image | **4** | 59 | 3 | **34.3 %** | petcave_mouth 54 %, petcave 40 %, chair_back 31 %, closet_oak 17 % |
| B relight | 3-pro-image | **4** | 59 | 3 | 19.8 % | ceil_main 33 %, back_wall_head 26 %, bed_platform 23 %, bed_mattress 20 % |
| C add a throw | 3-pro-image | **0** | 63 | 3 | 13.4 % | — |

## Three lines

1. **The ask that sounded safest was the most destructive, and the one that sounded
   riskiest was clean.** "Only change the surface" came back having replaced the bench
   with a different armchair, put books and vases on the shelves, and painted a window
   into the closet mirror that exists nowhere in the room. "Add one throw" changed
   nothing else — 0 DRIFT across all 63 checkable objects.
2. **What every ask held is exactly what R8 says to BUILD, and what they rewrote is
   exactly what R8 says to ACQUIRE.** Walls, ceiling, wardrobe, door, artwork, shelving,
   the bed's own mass — held to the pixel. The chair, the soft goods, the decor — rewritten
   or invented. That is not a coincidence to be grateful for; it is the same boxes-and-
   sweeps / free-form line the studio already drew, showing up in a vendor's model.
3. **C is the R8 third branch working:** a crumpled linen throw with real folds, weight and
   a contact shadow, in one call, on the object class that previously cost five rounds and
   785 hand-written lines of cloth physics and still ended at 3/12.

## Triage of what the probe caught in ITSELF

- **B's four DRIFTs are false alarms, and the reason matters.** The bed platform, mattress,
  ceiling and head wall did not move — the warm relight simply washed their junctions below
  the edge threshold, and `edge_drift` cannot tell "the edge left because the mass moved"
  from "the edge left because the contrast did". Confirmed by eye against the pair. So the
  instrument is sound for restyle and insert edits and only ADVISORY under a relight —
  and it fails toward the alarm, which is the correct side.
- A's `petcave` / `petcave_mouth` rows are true: that mass is the one r36 had just
  re-bounded, and the model reshaped its mouth.
- **Nothing here was checked on 10 of 73 objects** (3 UNCHECKABLE — outline never visible
  in the frame we sent; 7 NO-OUTLINE — too few boundary pixels). A silent pass on those
  would have been the flattering answer; they are printed instead.

## What it cost (R6)

| item | n | USD |
|---|---|---|
| gemini-3-pro-image, full frame (B, C) | 2 | 0.268 |
| gemini-3.1-flash-image, full frame (A) | 1 | 0.039 |
| isolation tests (tiny frames, both models) | 5 | 0.290 |
| **total** | **8** | **≈ $0.60 ≈ ฿21** |

Estimated ฿15, spent ฿21. The overrun is the four `gemini-3-pro-image` calls that died
mid-connection on prompt A and had to be re-routed to flash — see the transport note in
`edit_call.py`. No render cycles, no build cycles, no GPU time.

## Decided (R3 — nothing waits for the owner; overrule from the image)

`qa/open-decisions.json` D-011 · D-012 · D-013.
