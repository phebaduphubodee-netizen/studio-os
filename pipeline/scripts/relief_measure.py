#!/usr/bin/env python3
"""relief_measure.py — WHERE A SURFACE'S BUMP HEIGHT COMES FROM, as a re-runnable
measurement rather than a hand-written number in a JSON file.

    python pipeline/scripts/relief_measure.py                 # check every measured slug
    python pipeline/scripts/relief_measure.py --write <slug>  # (re)measure and store

exit 0 = every stored `relief` block reproduces from the texture files it names
exit 1 = a stored number no longer reproduces
exit 2 = COULD NOT RUN (PIL/numpy missing, or a slug's maps are not on disk)

WHY THIS FILE EXISTS, AND IT IS A CORRECTION
--------------------------------------------
On 2026-08-29 `_image_wood`'s relief was moved off an unusable Displacement map onto
the diffuse luminance, with the Bump Distance solved per slug and stored in
`<slug>.scale.json`. The comment at the call site then said the sidecar "carries its
own method and its own refusal test". **It carried neither.** The method was a prose
string; the refusal was a hand-written boolean the build simply trusted; and nothing
in the repo could re-derive any of it. A number that cannot be re-derived is an
assertion wearing a decimal point — the exact thing the sidecar format was invented to
stop for texture SCALE.

WHAT IT MEASURES, AND THE THREE APPROXIMATIONS IT DECLARES
----------------------------------------------------------
`bump_distance_m_from_diffuse` is solved so that a Bump node fed the diffuse luminance
reproduces the mean surface slope the VENDOR'S OWN `nor_gl` map reports. That solve is
honest about its own footing and these three limits are stored beside the number rather
than left for a reader to discover:

  1. **IT IS NOT SCALE-INVARIANT.** A mean image gradient depends on the baseline it is
     differenced over. Measured on oak_veneer_01: 41.5 /m at a 0.89 mm baseline, 25.6 at
     1.79 mm, 15.5 at 3.57 mm. The stored figure is the +/-1-texel central difference at
     the slug's asserted `tile_m`, and `gradient_baseline_mm` now records which one it is.
     The renderer's footprint is the pixel, not the texel, so at the millwork wall's
     ~3.2 mm/px the delivered slope is BELOW the vendor figure, not equal to it.
  2. **THE SOLVE IS ON GAMMA-ENCODED LUMINANCE; THE SHADER READS LINEAR.** The diffuse is
     loaded as sRGB, so Blender hands Bump linear values whose mean gradient differs by
     roughly a tenth. `gradient_linear_per_m` records both so the gap is visible.
  3. **DARK = LOW IS AN ASSUMPTION**, correct for open-pore wood where the grain lines are
     the pores, and DECLARED for anything else. `height_from_luminance_assumption` names
     which case a slug is.

So the stored distance lands the mean slope in the right ORDER, not on the nose. That is
still worth having — the state it replaced delivered 0.0010 deg against a vendor 2.246 —
but this file exists so the claim is the measured one.

THE REFUSAL, WHICH IS NOW A TEST AND NOT A SENTENCE. A Displacement map is usable as a
height field only if it carries signal: `displacement_map_std_8bit` is measured here and
the map is REFUSED below `DISP_STD_MIN`. oak_veneer_01 reads 0.31 with 89.3% of its
pixels on one value; plastered_wall_03 reads 0.556. Both are refused, by measurement.
"""
import glob
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX_ROOT = os.path.join(REPO, "assets", "shared", "cc0", "textures")

# An 8-bit map with less spread than this is a constant with compression noise on it.
# The two live slugs read 0.31 and 0.556; the nearest thing this would ACCEPT is any
# map with a visible tonal range, which on these sets means tens of codes.
DISP_STD_MIN = 2.0

# How closely a stored figure must still reproduce. Loose enough for a different PIL
# JPEG decoder minor version, tight enough that a changed file or a changed method is
# a failure rather than a shrug.
REPRO_TOL = 0.02        # 2% relative


def _np():
    import numpy as np                                      # noqa: PLC0415
    from PIL import Image                                   # noqa: PLC0415
    return np, Image


def _one(pattern, d):
    hits = sorted(glob.glob(os.path.join(d, pattern)))
    return hits[0] if hits else None


def measure(slug, root=None):
    """-> the `relief` block for `slug`, measured from its own texture files.

    PURE of the sidecar: it reads `tile_m` from the sidecar because that is the
    ASSERTED scale (R8) and this file does not get to re-decide it, but every other
    number here comes from the pixels."""
    np, Image = _np()
    d = os.path.join(root or TEX_ROOT, slug)
    sc_p = os.path.join(d, f"{slug}.scale.json")
    with open(sc_p, encoding="utf-8") as f:
        tile = float(json.load(f)["tile_m"])
    nor = _one("*_nor_gl_*", d)
    dif = _one("*_Diffuse_2k*", d) or _one("*_Diffuse_*", d)
    dsp = _one("*_Displacement_*", d)
    if not (nor and dif):
        raise FileNotFoundError(f"{slug}: needs a nor_gl and a Diffuse map")

    n = np.asarray(Image.open(nor).convert("RGB")).astype(np.float32) / 127.5 - 1.0
    z = np.clip(n[..., 2], 1e-6, 1.0)
    slope = float((np.hypot(n[..., 0], n[..., 1]) / z).mean())

    g8 = np.asarray(Image.open(dif).convert("L")).astype(np.float32) / 255.0
    px_m = tile / g8.shape[1]
    gy, gx = np.gradient(g8)
    grad_srgb = float(np.hypot(gx, gy).mean() / px_m)
    lin = np.where(g8 <= 0.04045, g8 / 12.92, ((g8 + 0.055) / 1.055) ** 2.4)
    gy, gx = np.gradient(lin)
    grad_lin = float(np.hypot(gx, gy).mean() / px_m)

    disp_std = None
    if dsp:
        disp_std = float(np.asarray(Image.open(dsp).convert("L"))
                         .astype(np.float32).std())

    return {
        "vendor_mean_slope_tan": round(slope, 6),
        "vendor_mean_slope_deg": round(math.degrees(math.atan(slope)), 4),
        "diffuse_mean_grad_per_m": round(grad_srgb, 4),
        "gradient_linear_per_m": round(grad_lin, 4),
        "gradient_baseline_mm": round(px_m * 2000.0, 4),
        "bump_distance_m_from_diffuse": round(slope / grad_srgb, 6),
        "displacement_map_std_8bit": None if disp_std is None else round(disp_std, 3),
        "displacement_map_usable_as_height": bool(
            disp_std is not None and disp_std > DISP_STD_MIN),
    }


def _slugs(root=None):
    r = root or TEX_ROOT
    out = []
    for p in sorted(glob.glob(os.path.join(r, "*", "*.scale.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                if isinstance(json.load(f).get("relief"), dict):
                    out.append(os.path.basename(os.path.dirname(p)))
        except Exception:                                   # noqa: BLE001
            continue
    return out


def main(argv):
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                   # noqa: BLE001
            pass
    try:
        _np()
    except Exception as e:                                  # noqa: BLE001
        print(f"COULD NOT RUN: numpy/PIL unavailable — {e}", file=sys.stderr)
        return 2

    if argv and argv[0] == "--write":
        if len(argv) < 2:
            print("usage: relief_measure.py --write <slug>", file=sys.stderr)
            return 2
        slug = argv[1]
        blk = measure(slug)
        p = os.path.join(TEX_ROOT, slug, f"{slug}.scale.json")
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        blk["measured"] = "2026-08-29"
        blk["method"] = ("DERIVED by pipeline/scripts/relief_measure.py, which re-runs "
                         "and is the authority on every figure here. Run it to check "
                         "them; do not hand-edit. See that file for the three declared "
                         "approximations (gradient baseline, sRGB-vs-linear, dark=low).")
        doc["relief"] = blk
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"{slug}: relief written — {blk}")
        return 0

    slugs = _slugs()
    if not slugs:
        print("COULD NOT RUN: no slug on disk carries a stored `relief` block.",
              file=sys.stderr)
        return 2
    bad = 0
    for slug in slugs:
        with open(os.path.join(TEX_ROOT, slug, f"{slug}.scale.json"),
                  encoding="utf-8") as f:
            stored = json.load(f)["relief"]
        fresh = measure(slug)
        drift = []
        for k, v in fresh.items():
            s_v = stored.get(k)
            if isinstance(v, bool) or v is None or isinstance(s_v, bool) or s_v is None:
                if s_v != v:
                    drift.append(f"{k}: stored {s_v!r} now {v!r}")
                continue
            if s_v is None or abs(float(s_v) - v) > REPRO_TOL * max(abs(v), 1e-9):
                drift.append(f"{k}: stored {s_v} now {v}")
        if drift:
            bad += 1
            print(f"!! {slug}: {len(drift)} figure(s) no longer reproduce")
            for d_ in drift:
                print(f"     {d_}")
        else:
            print(f"   {slug}: {len(fresh)} figure(s) reproduce · "
                  f"vendor slope {fresh['vendor_mean_slope_deg']}deg · "
                  f"bump {fresh['bump_distance_m_from_diffuse'] * 1000:.3f}mm · "
                  f"displacement usable={fresh['displacement_map_usable_as_height']}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
