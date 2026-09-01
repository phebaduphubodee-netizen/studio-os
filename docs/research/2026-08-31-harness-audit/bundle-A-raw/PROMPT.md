# Drawing-read task — one pass, from these images only

You are reading THREE crops of one page of a Thai residential FURNITURE PLAN
(CAD-exported PDF, printed scale 1:75). Labels on built-ins read like
`BF09-1.520x60x280CM` = code, then W x D x H in cm. Some dimension chains are in
mm (e.g. `2850`, `5500`); one furniture label is in feet (`7'x6.5'`). Some label
text is mirrored — that is in the source drawing.

Files in THIS directory (read all three):
- `ms_overview.png` — the whole master-suite region (bedroom, ensuite, walk-in bay, terrace)
- `bay_zoom.png` — walk-in wardrobe bay + ensuite (tub, WC, twin basins) + party wall between them
- `bed_zoom.png` — sleeping zone (bed, bench, nightstands, west wall band)

HARD RULE: judge ONLY from these three images. Do not open, glob, or grep any
other file or directory. You may use local Python/PIL to zoom into, crop, or
measure pixels of THESE images — that is encouraged. Say how you measured every
number.

Deliver (structured output), all lengths in mm REAL-WORLD:

1. CALIBRATION — how you converted px to mm. Name the printed dimensions you
   calibrated on, give mm-per-px per crop, and cross-check against a second
   printed dim; report the disagreement honestly.
2. ELEMENTS — every BF-coded built-in and loose furniture piece you can see:
   label text as printed; the label's own dims in mm; the DRAWN footprint
   measured from its strokes in mm; where label and drawn ink disagree by more
   than ~30 mm, flag it and say which you would trust for a build, and why.
3. PARTY WALL between wardrobe bay and ensuite: its thickness; the lengths of
   its solid segments; the clear width of the sliding-door opening in it.
4. GAPS — clearances between freestanding built-ins and the nearest wall;
   the gap between the foot-of-bed bench and the bed.
5. BED — drawn size in both axes; what its printed label means; WHICH direction
   the head faces, with the ink evidence (pillows, fold, what it touches).
6. CHAINS — printed dimension chains you can find; do the parts sum to the
   printed totals; give the deltas.
7. UNMEASURABLE — what these crops cannot give you (state it plainly; never
   type a number you did not measure).

Never guess. A declared unmeasurable is a correct answer; a fabricated number
is the only wrong one.
