# RESTART PROMPT — PRJ-2026-002 Floor 2 (fresh, correct pass "v4")

> Paste this whole file into a new Claude Code session. It is self-contained context.
> Repo: `c:\Users\teza_\OneDrive\Desktop\PlingPeat` (STUDIO-OS). Work from there.

## 0. First actions (do before anything else)
1. Read: `CLAUDE.md`, `pipeline/CLAUDE.md`, `projects/CLAUDE.md`.
2. Read the memory files in
   `C:\Users\teza_\.claude\projects\c--Users-teza--OneDrive-Desktop-PlingPeat\memory\`
   — especially `plan-extraction-pipeline.md`, `cad-rederivation.md`,
   `user-working-style.md`, `machine-constraints.md`.
3. Read the v3 files (the KNOWN-FLAWED baseline you will diff against — see §2), but
   DO NOT trust any built-in dimension in them.

## 1. THE ONE LESSON THAT CAUSED THIS RESTART (read twice)
The previous session failed, repeatedly, at the SAME thing: **reading dimension labels,
wall lengths, and door positions off the plan raster by eye, then building geometric
conclusions on those misreads.** Concrete, verified failures (kept in v3 to diff against):
- Read the built-in label **BF09-1 = 1.520 m (1520 mm)** as **"520 cm = 5200 mm"** (wrong
  decimal/unit).
- **Swapped** BF09-1 (1520) and BF09-2 (2150).
- Then invented "no straight 5200 mm wall exists" → an "L-shaped 5200 wardrobe" → **deleted
  the walk-in closet** — a whole speculative geometry rebuild founded on the misread.
  Error stacked on error. This is exactly what the owner has said all along Claude does worst.

**Division of labor for this project is now FIXED:**
- **The OWNER is ground-truth for every dimension, wall assignment, door position, and
  built-in size.** The owner reads Thai construction plans fluently; the plan already has
  the answers. ASK the owner. NEVER parse a label number or infer a wall/door from the raster.
- **You (Claude) transcribe the owner's values faithfully** into the scene-graph and place
  each built-in on the wall/position the owner names.
- **The machine (placement_gate) verifies only what a machine can deterministically check:**
  COMPLETENESS (no drawn furniture cluster silently dropped), NO-FLOATING (nothing placed on
  empty floor), ON-INK (built-ins overlap drawn ink). Identity, exact built-in size, facing,
  and wall assignment are HUMAN calls.
- **What the machine CAN read reliably (keep using):** deterministic connected-component
  clustering of *loose-furniture ink* (bed, chairs, tables) via `plan_cluster.py`, with
  placed footprints SNAPPED to the drawn clusters (0–4 mm). Trust that. Trust NO dimension
  you "read" off an image.

> Rule: if you are about to state a wall length, a door location, or a label number that you
> got by looking at the plan image — STOP and ask the owner instead.

## 2. What to build, and WHERE (keep v3 as the comparison baseline)
Rebuild Floor 2 in **NEW, separate files.** Do NOT overwrite v3 — the owner keeps it as the
"what was wrong" reference and wants a v3-vs-v4 diff at the end.
- Keep as flawed reference: `pipeline/output/floor2/*`, and in
  `projects/PRJ-2026-002_c001-house/03_layout/`: `scene-graph.master_bedroom.json`,
  `scene-graph.sitting_room.json`, `floor2-manifest.json`, `placement-gate.json`,
  `gen_floor2_specs.py`, `gen_floor2_keyplan.py`.
- Do v4 work in clearly separate files, e.g. a `03_layout/v4/` subdir + `pipeline/output/
  floor2_v4/`, or a `.v4` suffix. Pick one clean scheme, tell the owner, don't touch v3.
- When v4 is owner-approved, diff v4 vs v3 and report exactly which reads v3 got wrong.

## 3. Project facts
- Windows 11, repo in OneDrive. `python3` shim works. Bash AND PowerShell tools both available.
- PRJ-2026-002 (anonymized Thai house). Floor 2 "blue zone" scope: master bedroom +
  dressing/work zone + ensuite + wardrobes + sitting room + terrace. OUT of scope: far-east
  ห้องน้ำ2/ห้องพระ (x>10800) and the two north bedrooms.
- Plan PDF (VECTOR, but TEXT IS OUTLINED → `page.get_text()` returns nothing; you literally
  cannot extract label strings programmatically — one more reason to get values from the
  owner): `projects/PRJ-2026-002_c001-house/00_intake/raw-local/The City สาทร - สุขสวัสดิ์_Plan funiture 02.pdf`
  Use fitz page index **1** (rotated 270°).
- mm calibration: `SCALE=26.45` mm/pt, `OX=171.2`, `OY=596.5`;
  `mm(P) = ((Q.x-OX)*SCALE, (OY-Q.y)*SCALE)` with `Q = fitz.Point(P) * page.rotation_matrix`.
  Drawing strokes with width ≥ 0.6 = thick walls; < 0.6 = furniture/dim lines.
- Coordinates: absolute floor coords, millimetres, offset (0,0). Master suite ≈ 5500 mm wide
  (bottom dimension chain reads 5500 then 5100).
- Facing convention: `F(rot) = (sin rad, −cos rad)`; rot 0=faces S, 90=E, 180=N, 270=W; a
  piece's head/back edge is opposite its facing.

## 4. Ground-truth gathered so far — CONFIRM ALL with the owner before using
The owner gave these in the prior session; they OVERRIDE anything you'd "measure". Some are
still uncertain — re-confirm every one, plus the ones marked (?), before touching geometry:
- **BF09-1 = 1.520 m (1520 mm)** wardrobe — top/north of the wardrobe area.
- **BF09-2 = 2.150 m (2150 mm)** wardrobe — mid-right/east.
- **BF11 = 1.320 m (1320 mm)** built-in work desk — left/west. (v3 had 3200 = WRONG.)
- **BF14 = 3.25 m (3250 mm)** headboard slat — east wall. (owner confirmed 3.25.)
- **BF09-3 ≈ 3.30 m (3330 mm)** wardrobe over the bed — north of bed. (confirm)
- **BF10 double vanity** — ensuite south wall; sheet also dimensions the vanity run **3.05 m**;
  confirm the cabinet width the owner wants (2.50 vs 3.05). (confirm)
- Sitting built-ins **BF12-1, BF12-2, BF13** — v3 used eye-read sizes (1575 / 700 / 4100);
  CONFIRM these too, they came from the same unreliable eye-reads.
- The label format looks like "[code].[metres]x[depth cm]x[height cm]" but the prior session
  mis-parsed it every time — DO NOT parse it; take every number from the owner.
- OPEN QUESTION for the owner: is there a separate walk-in closet ROOM, or an open wardrobe
  zone? (The prior "no closet / option ก" answer was given on the WRONG 5200 premise — re-ask.)

## 5. Loose furniture (machine-readable — this part worked; reuse it, just re-verify)
Snapped to deterministic clusters (0–4 mm); trust these placements + facings:
- Master: bed 7'×6.5' head EAST (faces W toward the west TV console); foot bench; 2 nightstands
  (flank the bed head); desk chair (faces W into the BF11 desk); TV console (west wall).
- Sitting: 3-seat sofa (faces E); 2 tub chairs (face S / the terrace); 2 round accent tables.
- Dismissed non-furniture (signed in `placement-review.json`, keep): sitting NW door swing
  (894×948), master SW wall hatching (390×1074), room-spanning dimension/boundary linework.

## 6. Tools (`pipeline/scripts/` + `03_layout/`)
- `plan_cluster.py` — deterministic scipy clustering of furniture ink (the reliable reader).
- `placement_gate.py` — machine verifier; writes `placement-gate.json`; hash-bound;
  `build_floor` refuses on FAIL / unsigned REVIEW / input-hash mismatch.
  Run: `python3 pipeline/scripts/placement_gate.py "<plan.pdf>" <manifest.json>`
  Verdicts: MATCHED / DRIFT / ON_INK / FLOATING / UNPLACED. FLOATING→FAIL (blocks build);
  REVIEW needs `--accept-review` at build.
- `gen_floor2_specs.py` — CLUSTER-DRIVEN scene-graph generator: loose furniture snapped to
  clusters (anchor + kind + facing hand-set); built-ins hand-placed at OWNER-GIVEN size/wall.
  Copy to a v4 version and edit the built-ins from the owner's values.
- `gen_floor2_keyplan.py` — honest communication overlay: numbered KEY PLAN (ASCII index on
  the plan + Thai legend in the right margin via the Windows **Tahoma** font so Thai renders);
  zone polygons = the room outlines (can't spill past walls); footer cites the gate MARKER,
  never a fabricated "IoU 1.00" (per-piece IoU after snapping is tautological). Numeric
  self-checks: furniture-in-zone, index collisions, marker-read-from-disk. Copy to v4.
- `build_floor.py` — Blender build; requires the gate marker. Blender 5.1 at
  `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`.
  Run: `"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup
  --python pipeline/scripts/build_floor.py -- <manifest.json> --render --accept-review`
- `facing_reader.py` — pure facing cross-check (advisory).

## 7. Honest-image rule
Never print a fabricated aggregate metric (e.g. "IoU 1.00") on a deliverable image. State the
gate marker's real guarantees (completeness / no-floating / facing_flags / calibration) and
mark every human-confirm item (identity, facing of rot-less seats, built-in sizes) as such.

## 8. Hard constraints (CLAUDE.md — hook-enforced)
Never modify `qa/thresholds.yaml`, `knowledge/codes-th/**`, `.claude/settings.json`,
`.gitattributes`. No destructive shell (`rm -rf`, force-push, `chmod 777`, `curl|sh`, hard
reset). Client data stays LOCAL — no client names/addresses/dimensions in web searches or any
external/`notebooklm` call. Generation/render tasks never write into `knowledge/` or
`clients/`. Metric-first (mm). Commit/push ONLY when the owner asks.

## 9. Working style + the loop for THIS work
Owner works in **Thai**; wants outcome-first single reports; normally likes full-autonomy.
But for THIS rebuild the loop is deliberately owner-in-the-loop on dimensions:
1. Ask the owner for the authoritative built-in list (each BF: size + which wall + rough
   position) and the walk-in-closet-vs-open-zone question — BEFORE touching geometry.
2. Transcribe faithfully into the v4 scene-graph. Keep the loose-furniture cluster snapping.
3. Run the gate; render key-plan + 3D only AFTER ground-truth is set.
4. When done, diff v4 vs the v3 reference and report which reads v3 got wrong.
5. Never re-guess a dimension. If unsure, ask.

## 10. Your first message to the owner (send this, in Thai)
Confirm you've read the context and the lesson, then ask for the authoritative built-in list
(BF09-1/2/3, BF10, BF11, BF14, BF12-1/2, BF13 — size + wall + rough position) and the
walk-in-closet-or-open-zone question. Do not read any dimension off the plan yourself.
