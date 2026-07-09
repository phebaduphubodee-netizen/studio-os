"""
render_mask_labels.py -- Structured3D render-mask pairing -> the REAL {obj_id: kind} labels
sidecar that structured3d_adapter.convert(labels=) / run_batch(labels_path=) consume to
unblock F2_facing (and enrich F1_identity). This is the SECOND of the two real label recipes
the adapter names (the first, 3D-FRONT layout JSON, is owner-gated on an email); it needs no
external service beyond the render zips the studio already has a signed licence for.

WHY THIS EXISTS (the data path, verified 2026-07-09 on scene_00000, NO render download):
  Structured3D bbox_3d.json carries the object GEOMETRY (basis/centroid/coeffs -> footprint +
  native-yaw rot) but NO class label. The class lives only in the render masks. Two masks pair
  to recover it, PER RENDERED VIEW (same room, same 'full' style, pixel-aligned):
    - instance.png  uint16, pixel = OBJECT INSTANCE ID.  Ships INSIDE Structured3D_bbox.zip
                    (already on disk; ~104k masks, still compressed -- extract per slice).
                    VERIFIED: the instance ID == bbox_3d.json "ID", 1:1. scene_00000 union of
                    4 panorama rooms = 127 instance values, EVERY one inside bbox IDs 0..140,
                    zero out-of-range; sentinel 65535 = void. So the mask pixel IS the obj_id.
    - semantic.png  pixel = NYU-40 CLASS ID (1..40; 0 = void). VERIFIED 2026-07-09 on
                    Structured3D_panorama_00 (65 masks): it is a PALETTED PNG (PIL mode 'P')
                    whose palette is a DISPLAY colormap and whose INDEX is the class id -- every
                    index in 0..40, standard NYU colormap. read_mask() decodes the index directly
                    (see read_mask). Lives in the panorama render zips; PULLED 2026-07-09 with
                    HTTP range requests straight off the licensed README host (Bash egress works
                    -- the earlier "network sandbox blocks the pull" note was stale). Only the
                    first ~900 MB (14 scenes) of the 10.78 GB panorama_00.zip was fetched: the
                    zip is STORED/flags=0 in scene order, so a byte prefix yields whole early
                    scenes' semantic.png (the rgb/depth bulk is skipped). The instance.png sibling
                    each pairs against is extracted from the on-disk bbox.zip.
  For each object: overlay the two masks, take the MAJORITY NYU class over that instance's
  pixels (summed across every view the object appears in), map NYU-name -> the benchmark's kind
  vocab, and emit {obj_id: kind}. The kind is NEVER guessed from geometry -- an object with no
  render pixels, or only void-semantic pixels, or an NYU class outside the map, gets NO label
  (reported, never fabricated). This keeps the adapter's honesty contract: a labelled element's
  kind is real data; an unlabelled one stays F2-UNWIRED.

F2 IS *WIRED*; the ANGLE CONVENTION is now *VALIDATED* (geometric oracle 2026-07-09, 4 independent
methods -- qa/reports/f2-facing-convention-validated-2026-07-09.md):
  This lane makes score_facing SCORE (n>0) with REAL kinds instead of UNWIRED. The prior caveat here
  warned GT rot needed a ~270deg/+90 reconcile before a real reader could be scored -- that is now
  REFUTED. The adapter emits GT rot as NATIVE yaw, and that value is ALREADY the build_floor front
  rot: basis[0] is the object's SIDE axis (perpendicular to the true front, exact identity), and the
  real (into-room) front = (sin R,-cos R) = build_floor front(R). So a correct build_floor reader
  emits rot=R and scores EXACT with NO conversion (see structured3d_adapter.ROT_CONVENTION); the +90
  reconcile is WITHDRAWN (applying it CORRUPTS F2). What genuinely remains: (a) a real rot-EMITTING
  reader (svg_plan_reader is facing-blind, emits none), and (b) the ~5% left-handed tail + semantic
  front-vs-mirror, which sit in non-wall-backed/bed objects and stay render-gated. Angular buckets
  against a real reader are still un-exercised end-to-end until an oriented-symbol rot reader lands.

CLASS MAP PROVENANCE + WHAT IS STILL UNVERIFIED (read before trusting F2 numbers):
  NYU40_TO_BENCH below is transcribed from the S3D repo's metadata/labelids.txt (the canonical
  NYUv2-40 numbering; S3D does NOT renumber) cross-checked against data_organization.md. The
  numbering is authoritative. Empirically VERIFIED 2026-07-09 on panorama_00 (was: unverified):
    (a) semantic.png's PIL encoding -- CONFIRMED mode 'P' (paletted), INDEX == class id, palette is
        a display colormap. read_mask() decodes the index and STILL fails hard if any index exceeds
        the NYU ceiling (an unexpected colormap), so a real surprise on another part is never silent.
    (b) the class INDEXING -- CONFIRMED NYU 1..40 with 0=void: the observed winners across 14 scenes
        (ceiling/wall/floor/window/door/chair/sofa/bed/table/cabinet) match the NYU names with NO
        off-by-one and no odd-void; the batch report still prints observed_nyu_classes each run.
    (c) the two JUDGEMENT calls in the map: NYU 25 'television' -> 'tv_panel' (the screen, not
        the media console 'tv_console'), and that S3D wardrobes fall under NYU 3 'cabinet' /
        39 'otherfurniture' (no distinct wardrobe class) -- both FLAGGED inline.
    (d) PANORAMA views only by default: the instance-id==bbox-id 1:1 fact was verified on panorama
        masks -- CONFIRMED AT SCALE 2026-07-09 straight from the on-disk bbox.zip, NO render download
        (50 scenes / 6,273 panorama instances, 0 out-of-range, 50/50 fully within the scene's bbox
        IDs). Perspective was FEARED to use a per-view local (0..k) id space; the same 50-scene scan
        REFUTES that -- perspective ids are ALSO 0-out-of-range and reach the LARGE global bbox ids
        (max 397 seen, >> any local 0..k), so the id space is GLOBAL, not per-view local. The default
        STAYS panorama-only pending the stronger per-object cross-view identity check (that a given id
        paints the SAME physical object in both views -- that one wants the semantic/geo grounding),
        but --perspective is now evidence-supported and would ~4x the pixels-per-object majority.
  A coin-flip / occlusion-noise majority is NOT emitted (MIN_CONF_EMIT + MIN_PIXELS floors) -- an
  ambiguous object is reported unlabelled, never given a guessed kind F2 would then score as truth.
  When a real panorama part lands, run --selftest, eyeball observed_nyu_classes, AND spot-check a
  few (obj_id, kind) against the rendered rgb: the map is one dict, corrections are one line each.

USAGE (after the owner extracts a render part's semantic.png alongside the bbox zip's
instance.png into one mask root -- both zips share the Structured3D/scene_*/2D_rendering/...
layout, so they co-locate on extraction and pair as siblings in the same directory):
  python render_mask_labels.py --scene <scene_mask_dir> [out.json]      # {obj_id: kind}
  python render_mask_labels.py --batch <mask_root>       [corpus.json]  # {scene_id:{obj_id:kind}}
  python render_mask_labels.py --selftest                               # synthetic, no data
then feed the sidecar straight into the adapter (no adapter edit -- its CLI already takes it):
  python structured3d_adapter.py --batch 0:200 <gt_out_dir> corpus.json   # F2 WIRED
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

VERSION = "render_mask_labels v1.0"

INSTANCE_VOID = 65535      # uint16 sentinel in instance.png (background / no object)
SEMANTIC_VOID = 0         # 0 in semantic.png = unlabelled/void (NYU ids start at 1) -- DOCUMENTED,
                          # not empirically checked; the batch report prints observed class ids so
                          # an off-by-one (0-indexed) or 255-void surprise is visible on run 1.
LOW_CONF = 0.6           # emitted labels below this majority fraction are FLAGGED (still emitted)
MIN_CONF_EMIT = 0.5      # a label whose majority does NOT exceed this is a coin-flip -> NOT emitted
MIN_PIXELS = 30          # an object with fewer total classified pixels than this is boundary/
                         # occlusion noise -> NOT emitted (tunable; calibrate on real masks). GT
                         # stays conservative: an ambiguous object is reported unlabelled, never
                         # given a majority-of-noise kind that F2 would then score as truth.
# safe PIL modes: single-channel intensity ('L'=uint8 semantic) or integer ('I*'=uint16 instance).
# An RGB image would make np.asarray return channels, NOT class ids -> read_mask REJECTS it. A
# paletted ('P') image is the ACTUAL Structured3D semantic.png encoding: its palette is a display
# colormap and its INDEX is the NYU class id (VERIFIED 2026-07-09, see read_mask) -> 'P' is decoded,
# not rejected, after a class-ceiling check (the original blanket-reject-'P' guard was conservative).
_SAFE_MASK_MODES = ("L", "I", "I;16", "I;16B", "I;16L")
# NYU-40 label set: valid class ids are 0(void)..40. A paletted mask whose index exceeds this is NOT
# a class-id-as-index encoding (a genuinely different colormap) -> read_mask fails hard on it.
_NYU_MAX_CLASS = 40

# NYU-40 class id -> benchmark_reader kind string. Source: github.com/bertjiazheng/Structured3D
# metadata/labelids.txt (canonical NYUv2-40; S3D does not renumber) + data_organization.md.
# Only classes that map to a real benchmark kind are listed; every other NYU id (wall, floor,
# door, window, picture, curtain, pillow, person, otherfurniture, otherprop, ...) is deliberately
# ABSENT -> such an instance gets NO label (reported as unmapped, never guessed).
#   * = facing-asymmetric in benchmark_reader.FACING_KINDS -> these are the ones that WIRE F2.
NYU40_TO_BENCH = {
    3:  "cabinet",       # * (also the fallback bucket for wardrobes -- no distinct NYU wardrobe)
    4:  "bed",           # *
    5:  "chair",         # *
    6:  "sofa",          # *
    14: "desk",          # *
    25: "tv_panel",      # * JUDGEMENT: NYU 'television' is the SCREEN -> tv_panel (not tv_console)
    33: "toilet",        # *
    # --- non-facing furniture: enriches F1 identity, never scored by F2 (kept honest + real) ---
    7:  "table",
    10: "bookshelf",
    17: "dresser",
    24: "refrigerator",
    32: "nightstand",    # benchmark norm_kind folds nightstand -> side_table (non-facing) -- fine
    34: "sink",
    36: "bathtub",
}

# NYU id -> human name, for readable reports only (never gates anything).
NYU40_NAMES = {
    1: "wall", 2: "floor", 3: "cabinet", 4: "bed", 5: "chair", 6: "sofa", 7: "table", 8: "door",
    9: "window", 10: "bookshelf", 11: "picture", 12: "counter", 13: "blinds", 14: "desk",
    15: "shelves", 16: "curtain", 17: "dresser", 18: "pillow", 19: "mirror", 20: "floor mat",
    21: "clothes", 22: "ceiling", 23: "books", 24: "refrigerator", 25: "television", 26: "paper",
    27: "towel", 28: "shower curtain", 29: "box", 30: "whiteboard", 31: "person", 32: "nightstand",
    33: "toilet", 34: "sink", 35: "lamp", 36: "bathtub", 37: "bag", 38: "otherstructure",
    39: "otherfurniture", 40: "otherprop",
}


def _facing_kinds():
    """benchmark_reader.FACING_KINDS -- the single source of truth for which kinds F2 scores.
    Imported lazily so this module produces labels even if benchmark_reader is absent; only the
    report's n_facing count needs it (falls back to a static mirror if the import fails)."""
    try:
        from benchmark_reader import FACING_KINDS, norm_kind
        return FACING_KINDS, norm_kind
    except Exception:
        fk = {"bed", "sofa", "loveseat", "armchair", "chair", "bench", "tv_panel",
              "tv_console", "desk", "toilet", "wardrobe", "cabinet"}
        return fk, (lambda k: (k or "").strip().lower())


# ---- mask I/O + core pairing (pair_arrays is pure: the unit tests drive it directly) --------
def read_mask(path):
    """Load a class-id/instance-id mask PNG -> 2D int ndarray.

    Structured3D's semantic.png is a PALETTED ('P') PNG whose palette is a DISPLAY colormap and whose
    INDEX is the NYU class id (VERIFIED 2026-07-09 on Structured3D_panorama_00, 65 masks: every index
    in 0..40, standard NYU colormap -- index 1=wall (174,199,232), 2=floor (152,223,138), 22=ceiling;
    ceiling/wall/floor/window/door dominate every room render). np.asarray on mode 'P' returns those
    INDICES, which ARE the class ids -> 'P' is DECODED here, guarded by the NYU class ceiling: if any
    index exceeds _NYU_MAX_CLASS the palette is NOT class-id-as-index (a genuinely different colormap)
    and read_mask fails HARD (the original blanket-reject-'P' guard's intent, kept for the surprise
    case). RGB/RGBA is still rejected (a real colour->class map would be needed). An instance.png is
    uint16 ('I;16', ids seen up to ~400) so it is never 'P' -- the branches don't collide."""
    img = Image.open(path)
    if img.mode == "P":
        arr = np.asarray(img)
        if arr.ndim != 2:
            raise ValueError(f"{path}: paletted mask is not 2D (shape {arr.shape})")
        mx = int(arr.max()) if arr.size else 0
        if mx > _NYU_MAX_CLASS:
            raise ValueError(f"{path}: paletted mask index {mx} > NYU-40 ceiling {_NYU_MAX_CLASS} -- "
                             f"palette is NOT class-id-as-index (an unexpected colormap); decode via "
                             f"the palette->class map before pairing, or it mislabels every object.")
        return arr.astype(np.int64)
    if img.mode not in _SAFE_MASK_MODES:
        raise ValueError(f"{path}: PIL mode {img.mode!r} is not a raw class-id mask (safe modes "
                         f"{_SAFE_MASK_MODES} or a class-id-as-index paletted 'P'). An RGB semantic "
                         f"mask yields channels, NOT NYU class ids -- decode to class ids upstream "
                         f"before pairing, or this silently mislabels every object.")
    arr = np.asarray(img)
    if arr.ndim != 2:
        raise ValueError(f"{path}: expected single-channel mask, got shape {arr.shape}")
    return arr.astype(np.int64)


def pair_arrays(inst, sem):
    """(instance ndarray, semantic ndarray) -> {obj_id: Counter(nyu_class_id -> pixel_count)}.
    One view. Skips the instance void sentinel and semantic-void (0) pixels. Pure -- no I/O."""
    if inst.shape != sem.shape:
        raise ValueError(f"instance {inst.shape} vs semantic {sem.shape} shape mismatch "
                         f"(masks are not the same rendered view -- cannot pair)")
    out = defaultdict(Counter)
    ids = np.unique(inst)
    for oid in ids:
        if oid == INSTANCE_VOID:
            continue
        sem_vals = sem[inst == oid]
        sem_vals = sem_vals[sem_vals != SEMANTIC_VOID]
        if sem_vals.size == 0:
            out[int(oid)]  # touch: instance seen but all-void semantics -> reported, unmapped
            continue
        counts = np.bincount(sem_vals)
        for cls in np.nonzero(counts)[0]:
            out[int(oid)][int(cls)] += int(counts[cls])
    return out


def pair_view(inst_path, sem_path):
    """Pair one rendered view's instance.png with its sibling semantic.png (same directory)."""
    return pair_arrays(read_mask(inst_path), read_mask(sem_path))


# ---- scene / corpus aggregation -------------------------------------------------------------
def _find_view_pairs(scene_dir, include_perspective=False):
    """Every instance.png under scene_dir that has a semantic.png sibling -> [(inst, sem)].
    Also returns (unpaired, perspective_skipped): instance.png with NO semantic sibling (the
    un-downloaded-render case) and perspective views skipped by default.

    DEFAULT = PANORAMA VIEWS ONLY. The 'instance pixel == bbox ID, 1:1' correspondence was
    verified on PANORAMA masks; perspective renders MAY use a per-view local instance id space
    (UNVERIFIED), which would dump one object's pixels onto another's bbox id and flip the merged
    majority (adversarial finding 2026-07-09). include_perspective=True opts in AFTER you have
    confirmed perspective ids are the same global bbox ids on a real part."""
    pairs, unpaired, persp_skip = [], 0, 0
    for inst in sorted(glob.glob(os.path.join(scene_dir, "**", "instance.png"), recursive=True)):
        norm = inst.replace("\\", "/")
        if "/panorama/" not in norm and not include_perspective:
            persp_skip += 1
            continue
        sem = os.path.join(os.path.dirname(inst), "semantic.png")
        if os.path.exists(sem):
            pairs.append((inst, sem))
        else:
            unpaired += 1
    return pairs, unpaired, persp_skip


def scene_labels(scene_dir, include_perspective=False):
    """(labels {obj_id: kind}, report) for one scene from its render masks. Majority NYU class
    per object over ALL its pixels across ALL paired views; NYU -> benchmark kind via the map.
    A label is EMITTED only when the majority clears MIN_CONF_EMIT and the object clears
    MIN_PIXELS -- an ambiguous/occlusion-noise object is REPORTED unlabelled, never given a
    coin-flip kind (GT must not fabricate). unmapped / void / ambiguous are all reported, never
    guessed. labels obj_ids are ints (the adapter's _lookup_label tries both int and str keys)."""
    facing, norm = _facing_kinds()
    view_pairs, unpaired, persp_skip = _find_view_pairs(scene_dir, include_perspective)
    merged = defaultdict(Counter)
    for inst_path, sem_path in view_pairs:
        for oid, ctr in pair_view(inst_path, sem_path).items():
            merged[oid].update(ctr)

    labels = {}
    low_conf, disagreements, ambiguous = [], [], []
    unmapped_by_class, observed_classes, n_void = Counter(), Counter(), 0
    for oid in sorted(merged):
        ctr = merged[oid]
        if not ctr:                                   # instance had only void semantics
            n_void += 1
            continue
        total = sum(ctr.values())
        cls, hits = ctr.most_common(1)[0]
        conf = hits / total
        observed_classes[cls] += 1                    # for the off-by-one / void sanity report
        if len(ctr) > 1:
            disagreements.append({"obj_id": oid, "winner": NYU40_NAMES.get(cls, cls),
                                  "conf": round(conf, 3),
                                  "classes": {NYU40_NAMES.get(c, c): n for c, n in ctr.most_common()}})
        # emit floors: below either, the majority is a coin-flip / boundary noise -> DON'T emit
        if conf <= MIN_CONF_EMIT or total < MIN_PIXELS:
            ambiguous.append({"obj_id": oid, "winner": NYU40_NAMES.get(cls, cls),
                              "conf": round(conf, 3), "pixels": total})
            continue
        kind = NYU40_TO_BENCH.get(cls)
        if kind is None:
            unmapped_by_class[NYU40_NAMES.get(cls, str(cls))] += 1
            continue
        labels[oid] = kind
        if conf < LOW_CONF:
            low_conf.append({"obj_id": oid, "kind": kind, "conf": round(conf, 3)})

    n_facing = sum(1 for k in labels.values() if norm(k) in facing)
    report = {
        "scene": os.path.basename(os.path.normpath(scene_dir)),
        "views_paired": len(view_pairs), "views_unpaired_no_semantic": unpaired,
        "perspective_views_skipped": persp_skip,
        "instances_seen": len(merged), "labelled": len(labels), "facing_wired": n_facing,
        "void_only_instances": n_void, "ambiguous_unlabelled": ambiguous,
        "unmapped_by_class": dict(unmapped_by_class.most_common()),
        "observed_nyu_classes": {NYU40_NAMES.get(c, str(c)): n
                                 for c, n in observed_classes.most_common()},
        "low_confidence": low_conf, "disagreements": disagreements,
    }
    return labels, report


def corpus_labels(mask_root, include_perspective=False):
    """Walk scene_* dirs under mask_root -> ({scene_id: {obj_id: kind}}, [reports]). Scenes with
    no paired masks contribute an empty entry (reported), never a fabricated one."""
    out, reports = {}, []
    scene_dirs = sorted(glob.glob(os.path.join(mask_root, "**", "scene_*"), recursive=True))
    scene_dirs = [d for d in scene_dirs if os.path.isdir(d)]
    for sd in scene_dirs:
        labels, rep = scene_labels(sd, include_perspective)
        reports.append(rep)
        if labels:
            out[rep["scene"]] = {str(k): v for k, v in labels.items()}
    return out, reports


# ---- report + selftest ----------------------------------------------------------------------
def _print_reports(reports):
    tot_lab = sum(r["labelled"] for r in reports)
    tot_fac = sum(r["facing_wired"] for r in reports)
    tot_unpaired = sum(r["views_unpaired_no_semantic"] for r in reports)
    tot_persp = sum(r.get("perspective_views_skipped", 0) for r in reports)
    tot_ambig = sum(len(r.get("ambiguous_unlabelled", [])) for r in reports)
    unmapped, observed = Counter(), Counter()
    for r in reports:
        unmapped.update(r["unmapped_by_class"])
        observed.update(r.get("observed_nyu_classes", {}))
    print(f"{VERSION}: {len(reports)} scenes; labelled objects={tot_lab}; "
          f"facing objects (F2-wired)={tot_fac}; views missing semantic.png={tot_unpaired}; "
          f"perspective views skipped={tot_persp}; ambiguous (below emit floor)={tot_ambig}")
    if observed:
        print(f"  observed semantic classes (winner per object) -- eyeball for an OFF-BY-ONE / "
              f"void surprise on the first real run: {dict(observed.most_common(12))}")
    if unmapped:
        print(f"  unmapped NYU classes (no benchmark kind -> unlabelled, honest): "
              f"{dict(unmapped.most_common(12))}")
    if tot_unpaired and tot_lab == 0:
        print("  NOTE: every view lacked a semantic.png sibling -- the render part is not "
              "extracted next to the instance masks yet (owner download step).")


def run_selftest():
    """Synthetic in-memory proof of the WHOLE path -- NO render download. Paints a tiny
    instance/semantic pair with known (obj_id, NYU class), derives labels, feeds them through
    structured3d_adapter.convert(), and asserts F2 goes from UNWIRED -> WIRED (n>0, PASS on
    gt-vs-gt). This is the standing regression that proves the pairing math + class map + the
    adapter handshake without waiting on the panorama zip."""
    # 20x20: obj 0 = bed(4), obj 1 = sofa(6), obj 2 = toilet(33), obj 3 = television(25),
    # obj 5 = otherfurniture(39, UNMAPPED -> must stay unlabelled), plus void.
    inst = np.full((20, 20), INSTANCE_VOID, dtype=np.int64)
    sem = np.zeros((20, 20), dtype=np.int64)
    paint = {0: (4, (slice(0, 5), slice(0, 10))), 1: (6, (slice(5, 10), slice(0, 10))),
             2: (33, (slice(10, 15), slice(0, 10))), 3: (25, (slice(15, 20), slice(0, 10))),
             5: (39, (slice(0, 10), slice(10, 20)))}
    for oid, (cls, sl) in paint.items():
        inst[sl] = oid
        sem[sl] = cls
    # a smear of noise on obj 0 (a few sofa pixels) -> majority must still resolve to bed
    inst[0, 0], sem[0, 0] = 0, 6
    got = pair_arrays(inst, sem)
    labels = {}
    for oid, ctr in got.items():
        cls = ctr.most_common(1)[0][0] if ctr else None
        k = NYU40_TO_BENCH.get(cls)
        if k:
            labels[oid] = k
    assert labels == {0: "bed", 1: "sofa", 2: "toilet", 3: "tv_panel"}, labels
    assert 5 not in labels, "otherfurniture must stay unlabelled (unmapped)"
    print(f"  pairing+map OK: {labels} (obj5 otherfurniture correctly unlabelled)")

    # --- adapter handshake: build a synthetic S3D scene, run convert() WITH these labels -----
    import structured3d_adapter as A
    import benchmark_reader as B
    # one square room 0..4000mm, floor z=0; four objects at distinct centroids inside it.
    juncs = [{"ID": i, "coordinate": c} for i, c in enumerate(
        [[0, 0, 0], [4000, 0, 0], [4000, 4000, 0], [0, 4000, 0]])]
    lines = [{"ID": i, "direction": [0, 0, 0], "point": [0, 0, 0]} for i in range(4)]
    ljm = [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1], [1, 0, 0, 1]]      # edge i -> junc i,i+1
    plm = [[1, 1, 1, 1]]                                                 # floor plane owns all 4 edges
    anno = {"junctions": juncs, "lines": lines, "planes": [{"ID": 0, "type": "floor"}],
            "planeLineMatrix": plm, "lineJunctionMatrix": ljm,
            "semantics": [{"ID": 0, "planeID": [0], "type": "bedroom"}]}
    def box(i, cx, cy):
        return {"ID": i, "basis": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "centroid": [cx, cy, 500], "coeffs": [400, 300, 250]}
    boxes = [box(0, 1000, 1000), box(1, 3000, 1000), box(2, 1000, 3000),
             box(3, 3000, 3000), box(5, 2000, 2000)]
    import tempfile
    d = tempfile.mkdtemp(prefix="rml_self_")
    ap = os.path.join(d, "annotation_3d.json"); json.dump(anno, open(ap, "w"), ensure_ascii=False)
    bp = os.path.join(d, "bbox_3d.json"); json.dump(boxes, open(bp, "w"), ensure_ascii=False)

    blind = A.convert(anno_path=ap, bbox_path=bp, scene_id="synthetic", labels=None)
    wired = A.convert(anno_path=ap, bbox_path=bp, scene_id="synthetic", labels=labels)
    assert blind["meta"]["n_kinded"] == 0, "blind lane must emit no kinds"
    assert wired["meta"]["n_kinded"] == 4, f"expected 4 kinded, got {wired['meta']['n_kinded']}"
    assert all("kind" not in e for e in blind["elements"])
    kinded_ids = {e["id"] for e in wired["elements"] if "kind" in e}
    assert kinded_ids == {"o0", "o1", "o2", "o3"}, kinded_ids
    assert all("kind" not in e for e in wired["elements"] if e["id"] == "o5")

    card_blind = B.score_pair(blind, blind)
    card_wired = B.score_pair(wired, wired)
    assert card_blind["F2_facing"]["verdict"] == "UNWIRED", card_blind["F2_facing"]
    f2 = card_wired["F2_facing"]
    assert f2["n"] >= 4 and f2["verdict"] == "PASS", f2
    print(f"  adapter handshake OK: F2 UNWIRED(n=0) -> WIRED(n={f2['n']}, "
          f"cardinal_correct={f2['cardinal_correct']}, verdict={f2['verdict']})")
    print("selftest PASS: render-mask pairing WIRES F2 end-to-end (synthetic, no download).")
    print("  NOTE (not tested here): gt-vs-gt cancels rot, so this proves F2 is WIRED with real "
          "kinds -- not that its ANGULAR buckets are exercised. The GT rot is NATIVE yaw, which is "
          "ALREADY the build_floor front rot (basis[0]=side; front=(sin,-cos)(R), VALIDATED "
          "2026-07-09 -- see structured3d_adapter.ROT_CONVENTION); do NOT apply the withdrawn +90. "
          "Cardinal_correct is only un-exercised because svg_plan_reader emits no rot yet.")


def main(argv):
    # optional flag anywhere in argv; default is PANORAMA-ONLY (the verified instance-id space)
    include_perspective = "--perspective" in argv
    argv = [a for a in argv if a != "--perspective"]
    if len(argv) >= 2 and argv[1] == "--selftest":
        run_selftest()
    elif len(argv) >= 3 and argv[1] == "--scene":
        labels, rep = scene_labels(argv[2], include_perspective)
        _print_reports([rep])
        out = argv[3] if len(argv) > 3 else None
        payload = {str(k): v for k, v in labels.items()}
        if out:
            json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"wrote {out}  ({len(payload)} objects)")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=1))
    elif len(argv) >= 3 and argv[1] == "--batch":
        out_obj, reports = corpus_labels(argv[2], include_perspective)
        _print_reports(reports)
        out = argv[3] if len(argv) > 3 else "corpus_labels.json"
        json.dump(out_obj, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"wrote {out}  ({len(out_obj)} scenes with labels)")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
