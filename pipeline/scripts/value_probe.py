#!/usr/bin/env python3
"""value_probe.py — measure a render's tonal structure PER OBJECT (pure core; no bpy).

WHY THIS EXISTS (2026-07-23). `docs/strategy.md` carried "the bed is two near-white values
and reads pale" for five days as an unfixed note, and when it was finally measured with
hand-drawn region boxes the answer came back WRONG: the boxes straddled object boundaries
and reported four bed pieces at 183 +-2 that are in fact four different objects at 155,
165, 178 and 199. Region boxes are an eyeball probe wearing arithmetic — the same
"hardcoded prose over an unwalked probe" shape this repo's reviews have caught twice.

So the question "which object owns this pixel" is answered by the renderer, not by me:
`id_mask.py` re-renders the SAME camera with every object flat-emitting a palette colour
(1 sample, 0 bounces, Standard view transform — 2.5 s on this machine), and this module
decodes that mask and reports each object's median rendered value.

THE PALETTE round-trips EXACTLY. Ids are encoded in 6 levels per channel whose 8-bit sRGB
codes are 0/51/102/153/204/255, and decoded by nearest level — so a denoiser, a filter
width or a colour-management surprise cannot silently shift an id into its neighbour. An
out-of-palette pixel decodes to the nearest legal id, which is why `id_mask.py` renders
with a near-box filter: an anti-aliased silhouette blends two ids and belongs to neither.
The MEDIAN (not the mean) is what makes that survivable — a rim of blended edge pixels
cannot move it.

VALUE = Rec.709 luma computed on the sRGB-ENCODED pixels. That is deliberate and it is
not a physics mistake: this module measures what the EYE RANKS in the delivered image,
which is the display-encoded value. Linear-luminance averaging would over-weight the
highlights and report a ladder no viewer sees.
"""
import os

# --------------------------------------------------------------------------- where it writes


def mask_paths(out_png):
    """(png, json) for a mask, both ABSOLUTE and both in the SAME directory.

    2026-08-02: `id_mask.py` wrote its two halves with two different writers —
    `scene.render.filepath = out_png` for the image and `open(...)` for the sidecar —
    and on Windows those disagree about what a relative path means. Python resolves
    against the CWD; Blender hands a drive-less path to the OS, which resolves it
    against the CURRENT DRIVE ROOT. So `_private/…/mask.png` landed in `C:\\_private\\`
    while `_private/…/mask.json` landed in the repo, the run printed OK, and a frame
    derived from a client scene sat outside every `.gitignore` that was written to
    contain it. One function, two writers, two notions of "here" — the sidecar's whole
    job is to certify the image beside it, which it cannot do from another directory.
    """
    png = os.path.abspath(out_png)
    return png, os.path.splitext(png)[0] + ".json"


# --------------------------------------------------------------------------- palette

LEVELS = (0, 51, 102, 153, 204, 255)
MAX_ID = len(LEVELS) ** 3 - 1          # 215; id 0 is reserved for "not measured"


class ProbeError(ValueError):
    """A probe/palette violation. Raised, never warned — a measurement that quietly
    mis-attributes pixels is worse than no measurement, because it reads as evidence."""


def id_to_srgb(i):
    """id 1..MAX_ID -> the (r, g, b) 8-bit sRGB triple that encodes it.

    id 0 is RESERVED for everything the probe was not asked about, so a black pixel can
    never be confused with a measured object."""
    if not isinstance(i, int) or isinstance(i, bool):
        raise ProbeError(f"id {i!r} must be an int")
    if not 1 <= i <= MAX_ID:
        raise ProbeError(f"id {i} outside 1..{MAX_ID} — the palette holds {MAX_ID} objects")
    n = len(LEVELS)
    return (LEVELS[i // (n * n)], LEVELS[(i // n) % n], LEVELS[i % n])


def srgb_to_id(rgb):
    """An 8-bit (r, g, b) from the mask -> the id it encodes, by NEAREST level per channel."""
    n = len(LEVELS)
    idx = [min(range(n), key=lambda k: abs(LEVELS[k] - c)) for c in tuple(rgb)[:3]]
    return idx[0] * n * n + idx[1] * n + idx[2]


def luma(rgb):
    """Rec.709 luma of an 8-bit sRGB triple, on the 0..255 scale the studio band uses."""
    r, g, b = (float(c) for c in tuple(rgb)[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def median(values):
    """Median of a non-empty sequence. Local so the pure core needs no numpy."""
    s = sorted(values)
    if not s:
        raise ProbeError("median of an empty sample")
    m = len(s) // 2
    return s[m] if len(s) % 2 else 0.5 * (s[m - 1] + s[m])


# --------------------------------------------------------------------------- aggregation

MIN_PIXELS = 200          # below this an object is a sliver: reported, never ranked


def aggregate(samples, names, total_px=None, min_px=MIN_PIXELS):
    """`samples` = iterable of (id, luma). `names` = {id: object_name}.

    Returns a list of dicts sorted brightest-first:
        {name, id, px, share, value}     value is None when px < min_px
    An id with NO pixels is still returned (px 0, value None) — an object the probe could
    not see is a finding, and dropping it silently is how a probe starts flattering.
    """
    buckets = {int(k): [] for k in names}
    for i, v in samples:
        b = buckets.get(int(i))
        if b is not None:
            b.append(float(v))
    rows = []
    for k, name in names.items():
        vals = buckets[int(k)]
        rows.append({
            "name": name,
            "id": int(k),
            "px": len(vals),
            "share": (len(vals) / total_px) if total_px else None,
            "value": median(vals) if len(vals) >= min_px else None,
        })
    rows.sort(key=lambda r: (r["value"] is not None, r["value"] or 0.0), reverse=True)
    return rows


def measured_map(rows):
    """{object_name: value} for the rows that carry one — the input `value_ladder.
    check_render()` consumes. Sliver rows are OMITTED rather than zero-filled, so a rung
    measured on a piece the camera cannot see reports as MISSING instead of as black."""
    return {r["name"]: r["value"] for r in rows if r["value"] is not None}


def report(rows):
    """Human-readable table (the LOOK pass pastes this into the record)."""
    out = [f"{'object':26s} {'px':>9s} {'%frame':>7s} {'value':>7s}"]
    for r in rows:
        share = f"{100 * r['share']:6.2f}%" if r["share"] is not None else "      -"
        val = f"{r['value']:7.1f}" if r["value"] is not None else "  (slice)"
        out.append(f"{r['name']:26s} {r['px']:9d} {share} {val}")
    return "\n".join(out)


# --------------------------------------------------------------------------- the real path

def decode_ids(mask_rgb):
    """HxWx3 mask pixels (0..255) -> HxW array of ids, by NEAREST palette level.

    Extracted 2026-08-09 so `edge_drift.py` reads ids through the SAME code that
    `decode()` uses. It was inline in `decode()`, and a second caller copying those four
    lines is precisely how id 0's reservation, the nearest-level rule and the palette
    width drift apart between two files that both claim to read the same mask.
    """
    import numpy as np
    lv = np.abs(mask_rgb[..., None, :3].astype(np.int16)
                - np.array(LEVELS, dtype=np.int16)[None, None, :, None]).argmin(axis=2)
    n = len(LEVELS)
    return lv[..., 0] * n * n + lv[..., 1] * n + lv[..., 2]


def decode(beauty_rgb, mask_rgb, names, min_px=MIN_PIXELS):
    """Vectorised (numpy) equivalent of luma() + srgb_to_id() + aggregate(), for whole
    frames. `beauty_rgb` and `mask_rgb` are HxWx3 arrays of 0..255.

    WHY THIS IS A NAMED FUNCTION AND NOT INLINE IN _main. It used to be inline, which meant
    the ONLY code that ever measured a real render was a second implementation of the four
    functions the tests pin — the tests proved a decoder that never ran. It is still a
    second implementation (numpy cannot use the scalar path over 2.8 M pixels), so
    `test_value_probe` now asserts the two agree EXACTLY on a synthetic frame. Equivalence
    proven beats equivalence assumed."""
    import numpy as np
    lum = (0.2126 * beauty_rgb[..., 0] + 0.7152 * beauty_rgb[..., 1]
           + 0.0722 * beauty_rgb[..., 2])
    ids = decode_ids(mask_rgb)
    rows = []
    for k, name in names.items():
        sel = ids == int(k)
        px = int(sel.sum())
        rows.append({"name": name, "id": int(k), "px": px, "share": px / lum.size,
                     "value": float(np.median(lum[sel])) if px >= min_px else None})
    rows.sort(key=lambda r: (r["value"] is not None, r["value"] or 0.0), reverse=True)
    return rows


# --------------------------------------------------------------------------- CLI

def _main(argv):
    import json
    import numpy as np
    from PIL import Image

    if len(argv) < 5:
        # THE FRAME IS REQUIRED. A first cut defaulted it to value_ladder.FRAME, so probing
        # any OTHER camera and forgetting the argument scored the hero frame's targets
        # against a different view and reported four defects that were not defects. A probe
        # whose default answer is "assume this is the frame I was calibrated on" is exactly
        # the flattering-instrument shape this repo keeps finding; make the caller say it.
        print("value_probe: usage  <beauty.png> <idmask.png> <idmask.json> <frame-name>\n"
              f"  frame-name is the camera the beauty frame came from (e.g. 'eye', "
              f"'bed_hero'). It is REQUIRED: the ladder's per-rung targets are only "
              f"scorable on the frame they were solved against.")
        return 2
    beauty, mask, names_json, frame = argv[1], argv[2], argv[3], argv[4]
    side = json.load(open(names_json, encoding="utf-8"))
    src = side.get("source") or {}
    names = {int(k): v for k, v in (side.get("ids") or {}).items()}
    if not names:
        raise ProbeError(f"{names_json}: no `ids` block — this sidecar predates the "
                         f"alignment fingerprint; re-run id_mask.py")
    b = np.asarray(Image.open(beauty).convert("RGB")).astype(np.float32)
    m = np.asarray(Image.open(mask).convert("RGB")).astype(np.int16)
    if b.shape[:2] != m.shape[:2]:
        raise ProbeError(f"beauty {b.shape[:2]} and mask {m.shape[:2]} are not the same "
                         f"size — nothing here can be measured")
    # SHAPE IS NOT ALIGNMENT. Every non-hero camera in this build renders 2000x1400, so a
    # mask from another view passes the size check and mis-attributes every pixel. The
    # build writes `room_<name>.blend` and `room_<name>.png` from ONE `save()`/`render()`
    # pair, so their stems are equal by construction — and unequal stems mean the mask and
    # the beauty frame came from different builds.
    import os as _os
    b_stem = _os.path.splitext(_os.path.basename(beauty))[0]
    if src.get("blend") and src["blend"] != b_stem:
        raise ProbeError(
            f"MASK/BEAUTY MISMATCH: the mask was rendered from {src['blend']!r} but the "
            f"beauty frame is {b_stem!r}. They are the same SIZE, which is why this has to "
            f"be checked by provenance — measuring one camera's pixels through another "
            f"camera's mask produces numbers that look exactly like evidence")
    rows = decode(b, m, names)
    if src:
        print(f"mask source: blend={src.get('blend')!r} camera={src.get('camera')!r} "
              f"res={src.get('res')} meshes={src.get('meshes')}")
    print(report(rows))

    try:
        import value_ladder as vl
    except ImportError as e:
        # NEVER a silent 0. A first cut swallowed this and exited SUCCESS, so a probe run
        # from the wrong directory printed a perfectly good table and reported "no ladder
        # violations" without ever having checked one.
        print(f"\nvalue_ladder.check_render: NOT RUN — could not import value_ladder ({e}). "
              f"The table above is a measurement, not a verdict.")
        return 3
    viol = vl.check_render(measured_map(rows), frame=frame)
    real = [v for v in viol if not v.startswith("NOTE:")]
    print(f"\nvalue_ladder.check_render (frame={frame!r}):")
    for v in viol:
        print(("  - " if v.startswith("NOTE:") else "  ! ") + v)
    if not real:
        print("  CLEAN — the ladder the design decided is the ladder the render shows")
    # A NOTE is scope, not a defect: an off-frame run legitimately skips the per-rung
    # targets, and exiting non-zero for saying so would train the caller to ignore the
    # exit code — which is how a check stops being a check.
    return 1 if real else 0


if __name__ == "__main__":                       # pragma: no cover
    import sys
    sys.exit(_main(sys.argv))
