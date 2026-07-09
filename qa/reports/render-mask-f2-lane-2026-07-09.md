# Structured3D render-mask F2 lane — built + synthetically proven, owner-download-gated

2026-07-09. Lane A of the tier1-self-doubt session menu: wire F2_facing on Structured3D via
render-mask pairing (the un-blocked alternative to the owner-gated 3D-FRONT email). This
session took it as far as an agent environment physically can; the one remaining step is a
render-zip download that the network sandbox blocks (owner action).

## What is proven (no download spent)

- **instance.png pixel ID ≡ bbox_3d.json object ID, 1:1.** Verified on scene_00000: the union
  of the 4 panorama-room instance masks = 127 instance values, **every one inside bbox IDs
  0..140, zero out-of-range**; sentinel `65535` = void. Fraction of mask IDs that are real bbox
  IDs = **1.000**. So a mask pixel *is* the obj_id — the pairing recipe is sound. (The 14 bbox
  IDs absent from the panoramas are objects occluded / outside every room FOV — expected.)
- **`semantic.png` = single-channel uint8 NYU-40 class id** (1..40, 0=void), NOT a colormap —
  from the S3D repo `data_organization.md` + `metadata/labelids.txt`. S3D does not renumber.
- **`render_mask_labels.py` (new) pairs the two masks → `{obj_id: kind}` and the whole path is
  proven end-to-end on synthetic + real-mask I/O:** `--selftest` shows F2 going
  **UNWIRED (n=0) → WIRED (n=4, cardinal_correct=1.0, PASS)** through the real
  `structured3d_adapter.convert(labels=)`; 69 tests green (17 new + 52 existing regression); the
  real 16-bit panorama mask (`I;16`) loads through the hardened reader.
- **Zero edits to any existing file.** The adapter already accepts a labels sidecar
  (`convert(labels=)`, `run_batch(labels_path=)`, CLI positional). Pure addition; zero collision
  with the parallel `synth_plan_2d.py` lane.

## The one remaining step (owner — needs network the agent session lacks)

Agent Bash has **no outbound network** (verified: `example.com` + `github.com` both `http=000`;
DNS resolves, egress is sandboxed). `semantic.png` lives only in the un-downloaded
`Structured3D_panorama_XX.zip` parts. So the owner pulls one part, exactly as the annotation/
bbox zips were owner-pulled on 2026-07-07 via the licence form.

1. Download **one** `Structured3D_panorama_00.zip` (base URL
   `https://zju-kjl-jointlab-azure.kujiale.com/Structured3D/`, licence: form already signed,
   see `studio-datasets/structured3d/SOURCE.txt`) into `C:/Users/teza_/studio-datasets/structured3d/`
   (local disk, **not** OneDrive).
2. Extract its `semantic.png` **and** the bbox zip's `instance.png` into one mask root so they
   co-locate (both zips share the `Structured3D/scene_*/2D_rendering/.../panorama/full/` layout —
   `instance.png` + `semantic.png` land as siblings, which is how the pairer finds them).
3. Two commands, no code change:
   ```
   python render_mask_labels.py --batch <mask_root> corpus_labels.json
   python structured3d_adapter.py --batch 0:200 <gt_out_dir> corpus_labels.json   # F2 WIRED
   ```

## Caveats to clear before trusting F2 *numbers* (all disclosed in the module)

1. **F2 is WIRED, not yet ANGLE-VALIDATED.** GT rot is emitted as NATIVE yaw; benchmark_reader's
   schema expects build_floor `front=(sin,-cos)` — a ~270° offset with UNVALIDATED y-handedness
   (`structured3d_adapter.ROT_CONVENTION`). gt-vs-gt cancels it (selftest PASSes), but a real
   reader emitting build_floor rot would score F2≈0 while being perfect. **Reconcile the offset +
   handedness against a real rot-emitting reader (svg_plan_reader) before reporting
   `cardinal_correct` as truth.** This is the headline caveat.
2. **Class indexing is documented, not empirically checked.** The `--batch` report prints
   `observed_nyu_classes` — eyeball it on the first real run for an off-by-one (0-indexed) or a
   255-void surprise; the map is one dict, corrections one line.
3. **Panorama views only by default.** instance-id≡bbox-id was verified on panorama; perspective
   MAY use a per-view local id space that would corrupt the merged majority. `--perspective`
   opts in *after* you confirm perspective ids are the same global bbox ids.
4. **Paletted/RGB semantic PNGs are rejected loudly** (`read_mask` keys on PIL mode, not just
   ndim) — a colormapped label PNG can't silently become palette-index garbage.
5. **Ambiguous objects stay unlabelled.** A coin-flip majority (≤ `MIN_CONF_EMIT`) or an
   occlusion-noise object (< `MIN_PIXELS`) is reported, never given a guessed kind. Both floors
   are tunable on real masks.
6. **Judgement calls:** NYU 25 `television`→`tv_panel`; wardrobes fold into NYU 3 `cabinet`
   (no distinct wardrobe class). Both flagged inline; spot-check vs the rendered rgb.

## Files

- `pipeline/scripts/render_mask_labels.py` — the pairing module + `--selftest`/`--scene`/`--batch` CLI
- `pipeline/scripts/test_render_mask_labels.py` — 17 unit tests (pairing math, 16-bit I/O, mode
  guard, cross-view majority, emit floors, panorama-only, corpus format, map-drift guards)
