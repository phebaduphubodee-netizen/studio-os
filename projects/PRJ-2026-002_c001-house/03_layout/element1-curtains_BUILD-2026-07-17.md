# Element 1 — Curtain BUILD record (2026-07-17)

The curtain finally EXISTS. The spec carried `curtain_track` + `curtains` since
2026-07-16 with no consumer (`grep curtain build_room.py` = 0); every render showed
bare glass where the owner decided fabric, and 3ce5f5e measured that omission as a
"pale band" design finding. This session closed the loop: the data now has a
materializer, and the materializer is verified three ways (unit geometry, raycast,
LOOK).

## What was built

- `pipeline/scripts/curtains.py` — pure layout (LAYER LAW: no bpy). Glass runs are
  CHAINED from `room.openings`; each leg comes from matching an axis-aligned
  `curtain_track.path_mm` segment to the glass run it dresses; pocket width and the
  2-layer make-up come from `curtains`. Nothing project-specific is hardcoded — the
  generator is reusable (same shape as the open-wall generator).
- `build_room._add_curtains` — extrudes each ribbon floor→ceiling (top hidden in the
  ceiling slab on --eye; clipped under the wall top on the slab-less overview),
  smooth-shaded, fabric assigned directly (`ph_model` opts out of bevel/reassign).
- Spec DATA (owner-vetoable, never revertible-by-omission): `curtains.render_state`
  (day scene: sheer DRAWN, blackout PARKED; south over-glass park at the west end;
  fabric tints joining the plaster ground per Albers/D1-A, DR 3ce5f5e) and
  `eye_camera_variants` (`--eyecam=curtains_south|curtains_semouth`) — because the
  canonical hero eye view sees ZERO curtain pixels (the "camera must SEE the
  decision" lesson, third occurrence).

## Geometry decided by data, disclosed where the world is imperfect

- Pocket = 250 (ink), envelopes: sheer 20–105 (glass side), blackout 110–240 (room
  side); the ≥250 vault rule is now a geometric RAISE, not prose.
- EAST leg: the spec's BF14 still carries the #9c ~53mm-east residual, so the spec
  slot is 197 (ink truth 250.8). Fabric must not render inside the slat wall →
  envelopes compress ×0.75, DISCLOSED (`squeezed_by`) — and the tests DERIVE this
  from BF14's own footprint, so the day BF14 is ink-trued the compression and the
  assertions both dissolve (review finding: never entrench a residual in a test).
- L-CORNER MITRES (22-finding adversarial review, the one real design catch): drawn
  = glass∩track left a ~144mm floor-to-ceiling bare band on the SE return beside
  the curtain mouth — the exact pale-band class again. CONVENTION adopted (recorded,
  owner-vetoable): the RETURN legs extend along their own glass into each corner
  (S1/S2 draw arrows), the long south panel TRIMS to meet the neighbours' drawn
  envelopes (+5mm) so panels MEET and never cross. Verified: east sheer now spans
  the full return; ribbons' plan bboxes pairwise disjoint across legs.

## Verification

- 28 unit tests (containment, slot lock derived-not-hardcoded, mitre coverage,
  no-crossing, real-wave pinning ±amp + ~2 crossings/fold, park adjacency, all
  fail-loud paths). Full pipeline suite 1639 green.
- Raycast (element-1 lesson): camera-to-target probes hit fabric BEFORE glass on
  all three legs; the SE mouth chain is jamb → fabric → glass.
- LOOK: `--eyecam=curtains_south` shows the drawn sheer full-run with the view
  diffusing through; `curtains_semouth` shows the mouth region dressed.

## Still owner / still open (unchanged by this build)

- Heights (pelmet/RCP), track hardware + fabric SKU: owner/supplier tier — the
  build invents none of them (top edge simply hides in the slab).
- Single-vs-blackout day/night states beyond the recorded default: owner taste.
- The outside is still the studio HDRI, not the garden (option B, next lever).
- West park column stands in the x0–306 corridor BEHIND the freestanding ex-TV
  bookshelf (visible above its 1800 top) — revisit when element 2 ink-trues the
  west wall.
