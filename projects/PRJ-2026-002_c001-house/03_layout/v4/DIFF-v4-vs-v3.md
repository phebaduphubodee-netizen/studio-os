# Floor-2 v4 vs v3 — what v3 read WRONG (diff report)

**Baseline v3** (known-flawed, kept per RESTART-PROMPT): `pipeline/output/floor2/*` +
`03_layout/scene-graph.*.json` + `floor2-manifest.json` (pre-2026-07-06).
**v4** (this rebuild): `03_layout/v4/*` + `pipeline/output/floor2_v4/*`.

The point of this diff is not the pixels — it is **which class of read went wrong**. v3 already
had the entire deterministic stack (clusters + BF-label sizes + the hardened `placement_gate.py` +
self-verify), and it shows: v3's **geometric + completeness** work was largely right — it already
had the tub, shower, WC, and the BF12/BF13 casework correctly sized. The genuine v3 faults were all
in the **semantic** layer the machine cannot read from the raster: **identity** (BF10), a
**labelled-but-unplaced unit** (BF09-2), and the **indoor/outdoor boundary** (the sliding glass
door). Row 5 is the mirror image — a semantic read (facing) that v3 had RIGHT and the v4 clean
rebuild REGRESSED — which proves the same point from the other side.

| # | Item | v3 (wrong / incomplete) | v4 (corrected) | class | caught by |
|---|------|-------------------------|----------------|-------|-----------|
| 1 | **BF10** | ensuite **double vanity** (อ่างล้างหน้า), inside the bathroom | **dressing cabinet** OUTSIDE the bath, between BF11 & BF09-2, on the ensuite south wall | identity | owner |
| 2 | **BF09 north** | BF09-3 (3300) + BF09-1 (already an L) present; **BF09-2 (1.5m) omitted** ("wall not clear") | three distinct: **BF09-1** (L: N-leg 2.5m + E-leg 2.1m box ≈ 2.7m east wall run), **BF09-2** (1.5m, meets BF10, clears the ensuite door — **NEW**), **BF09-3** (3.3m over-bed) | completeness (BF09-2) | owner |
| 3 | **Ensuite fixtures** | **already had** WC + bathtub + shower + a vanity — but the **vanity was conflated under BF10** (label "BF10=อ่างล้างหน้า"); fixtures under-sized | BF10 **un-conflated** (→ dressing cabinet), vanity now separate sanitaryware; tub 1360×870→1800×900, shower 780×950→1050×1150 | identity / sizing | this session |
| 4 | **Sitting south boundary** | sitting floor treated as reaching **y0**; one uniform thin "ระเบียง (700)" strip; **no sliding door** | enclosed room **stops at the sliding glass door (y2050)**; deep **OUTDOOR terrace lounge** below; the **L pier** (console wall y2600 → pier at x7050 → y2050) + 2-panel glass door (x7150–9900) read | boundary / thin-line | owner |
| 5 | **Tub-chair facing** | rot 0 (south, axis-aligned; note "face terrace") — **v3 had this RIGHT** | **v4 first REGRESSED** to rot 120/290 "face interior table", then corrected to **rot 12 / 335 facing OUT**, converging south beyond the terrace edge (computed ~y-650) | facing (v4 regression, fixed) | owner |
| 6 | **Tub-chair angle/size** | axis-aligned (cardinal), larger footprint (768×780 / 738×726) | oriented boxes **680×640 (left) / 660×640 (right)**, angle derived to face out (owner earlier: don't force cardinal / don't oversize) | geometric (improvement) | this session |

## The ONE regression this session introduced (honest disclosure)

Row 5: v3 had the tub chairs **facing south / out to the terrace** (rot 0, correct in direction).
The v4 "clean rebuild" **re-derived facing from the oriented min-area box and picked the wrong
180° interpretation** ("faces the interior round table"), silently overwriting a correct v3 read.
Nothing flagged it — the gate cannot see facing. The owner caught it and it was corrected to
rot 12/335 (out to the garden). **Lesson (now in `docs/strategy.md`): a confirmed semantic read
must persist as durable, owner-signed structured data the generator honours — never re-derived
from geometry each rebuild, never left in a prose note.**

## Net v4 vs v3
v4 = v3's correct south-facing chairs **+** the true drawn chair angle (v3 was axis-aligned)
**+** the newly-read terrace / sliding-door structure **+** correct BF10 / BF09 identities
**+** the full ensuite. The gate stayed honestly at REVIEW throughout both versions.

## Resolved 2026-07-06 (owner)
- **TV/west-wall = TALL TV cabinet** — identity confirmed; footprint 2046×600 read, **height set 1800**.
- **BF12-2 = indoor** → floor zone reverted to a uniform y2050 room/terrace split (L-jog was an over-correction).
- **BF12-2 (tall cabinet) ≠ the orchid table** — un-merged into two separate pieces (owner). BF12-2 vs
  table exact position still to confirm.

## Deliverables
- Key plan: `pipeline/output/floor2_v4/floor2_v4_keyplan.png` (numbered, Thai legend, footer
  cites the gate marker not a fabricated IoU; sliding door + L annotated as owner-read thin-line).
- 3D: `pipeline/output/floor2_v4/floor2_top.png`, `floor2_overview.png`, `floor2_tv_eye.png`.
- Reads + provenance: `READING-NOTES-v4.md`; verify crops `review-door-reading.png`,
  `review-terrace-chairs-facing.png`, `overlay-v4-selfverify.png`.
