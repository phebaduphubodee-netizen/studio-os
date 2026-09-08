# floor2 v5 (BLIND) vs v4 — diff

**Date:** 2026-07-10 · **Authorized:** owner said "diff กับ v4 ดูสิ" AFTER the blind v5 was complete
(the blindness had served its purpose — v5 was produced without seeing v4). Read-only on v4.
**Note:** `v4/floor2-walls-mm.json` was the floor2 pane's *uncommitted* working copy at diff time.

## The two layers separated cleanly

| | v5 (blind) | v4 |
|---|---|---|
| calibration | 26.45 mm/pt, origin (171.2, 596.5), page 1 | **identical** |
| wall segments | 992 | 1011 |
| unique wall keys | 833 | 852 |
| v5-only | — | **0** |
| v4-only | — | **19** |
| `manual_additions` | false | true (**19** segments) |

**The entire v5↔v4 wall difference is the 19 owner `manual_additions`.** v4 = the machine walls
(byte-identical to v5's 992) **plus** 19 hand-signed segments. `v5-only = 0`: every wall the blind
extract found, v4 also has.

### Layer 1 — machine walls: reproducible, 0 divergence
Same tool + same PDF + same calibration → the blind extract reproduced v4's machine walls exactly
(0 v5-only, 0 v4-only among machine segments). **The pipeline's wall extraction is deterministic —
no hidden path-dependence.** This is the confidence signal the blind replication was for.

### Layer 2 — owner signature: partially blind-discoverable
v4's 19 `manual_additions` (`by='owner-confirmed (SW-corner wall flagged 2026-07-06)'`, dates
2026-07-06 + 07-10 + 07-10r2) are the thin-line walls `pdf_extract_walls` is blind to. Against my
blind flags:

- **HIT — the main indoor/outdoor boundary:** the owner's SW-corner + south-terrace return walls
  (segments around x[-47..604] & x[3054..5654] at y≈-698/-799, plus the master west return down to
  y=-799) are the big **green L** at bottom-left of `floor2_v5-vs-v4-overlay.png` — exactly where my
  blind **tg1** (master-bedroom → terrace glazing) + **tg2** (terrace outline) pointed. The owner's
  own reason ("SW-corner wall face-segments … that pdf_extract_walls is BLIND to") matches my flag
  verbatim in intent. Coordinates were approximate on my side (I estimated y≈0; actual y≈-750) —
  flagged as approximate, owner sets exact.
- **MISS — finer interior thin-lines:** the owner also signed vertical walls at **x≈5654–5752**
  (piers, y 2800–5698) and **x≈10600** (the party wall near the central stair, y −1000..2000), added
  in the later 07-10 sessions. My phase-1 *visual* read did not catch these. A phase-2 thin-stroke
  extraction (keep sub-0.6 pt strokes that close a loop) would be needed to find them blind.

## Verdict
- **Machine extraction: validated reproducible** (v5 blind ≡ v4, 992 segments).
- **Owner-signature layer: the biggest boundary is independently discoverable; the finer interior
  patches are not (yet)** — they remain genuinely owner-knowledge or a thin-stroke phase-2 pass.
  This is a clean empirical measurement of *how much* of the two-layer "owner" work a blind machine
  read can recover on this sheet: the dominant indoor/outdoor line, not the interior detail.

Artifacts: `floor2_v5-vs-v4-overlay.png` (RED v5 / BLUE v4 / GREEN v4 owner additions).
