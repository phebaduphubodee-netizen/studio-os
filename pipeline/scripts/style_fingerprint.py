"""style_fingerprint.py -- LOCAL, deterministic, NO-API fingerprint of an interior render.

WHY (Stage B of the sellability LEARNING engine, 2026-07-15):
  The sellability benchmark is a JUDGE -- it tells us our renders LOSE to the friend's
  delivered Discord work; it does NOT tell us WHERE. This module is the measuring tape.
  It scores any render (an anchor OR ours) on the quantitative axes the interior-render-
  critique DR (knowledge/_inbox/interior-render-critique-DR-2026-07-15.md) names:
    1. palette hierarchy   -- the 60-30-10 dominant/secondary/accent area split
    2. warmth              -- warm interior light vs cool
    3. material spread     -- CHROMATIC mono-material concentration (chromatic_mono_index; the
                              "ไม้ไปหมด" wound, §2 -- see the OVERCLAIM GUARD caveat below)
    4. lighting            -- layered range vs flat "institutional" (§3)
    5. wounds              -- black-hole dead-end cavity share (the "รู" wound, §1)
  so we can read the per-axis GAP between our render and the sellable cluster and know
  which generation lever to pull. It does NOT decide beauty.

LOCAL-ONLY LAW (owner decision 2026-07-12; qa/benchmark-sellability.md):
  this reads pixels on THIS machine only. It calls NO external API of any kind -- the
  benchmark anchor pool is a client's paid work, and a Gemini/cloud/NLM call on those
  images is banned. Pure PIL + numpy + scikit-learn. Nothing here leaves the machine.
  PATH PRIVACY (review 2026-07-15): the anchors live under _private/ with client PERSONAL
  NAMES in the folder segments; the standing law forbids surfacing a name "even inside a
  quoted filename". So every emitted identifier goes through _safe_ref(): any _private/ path
  becomes a non-reversible "private:<hash>" token -- no raw client path/basename ever reaches
  stdout, --out JSON, or a pasted gap report. Our own render paths pass through readable.

NOT A BEAUTY SCORE (anti-flattering; this is the 17th scorer in a repo that has caught 16):
  the fingerprint emits per-axis METRICS, never a single "overall" number -- an overall
  score is exactly the lenient shape the M3.2 judge (rho=0.428) already failed at, and
  beauty parity is the DESIGNER's pairwise call. The CONTROLLED anti-flattering evidence is
  the SYNTHETIC suite (solid vs half-neutral vs multi-hue at identical synthetic geometry --
  test_multi_hue_* kills a hue_resultant:=1.0 mutation that otherwise passes everything).
  CONFOUND caught by ACTUALLY LOOKING at the two clay PNGs (2026-07-15, owner asked "did you
  see it or just read numbers"): the de-wood pair is NOT a materials-only control. The walnut
  render is Cam01_v01 aimed at the brown feature wall with a bare block bed; the de-wood render
  uses a DIFFERENT eye_camera (26mm, aim 5150,1000) aimed at the fluted WHITE headboard with
  added furniture (bench, nightstands, pillows, mattress). So walnut reads MORE chromatic-mono
  than de-wood (0.805 -> 0.338) partly from the millwork swap and partly from camera + staging
  -- this pair is only a WEAK directional corroboration, NOT clean causal proof of the material
  lever (the SAME confound sits under the Gemini 2->4 material_variety score, commit 94648d3).
  Clean control still OWED: render walnut AND de-wood at the SAME eye_camera + SAME furniture,
  differing ONLY in millwork. See test_style_fingerprint.py::test_tripwire_dewood_directional.

Determinism: fixed work-size resize (LANCZOS), fixed KMeans seed, no random subsampling.
  Same bytes in -> identical fingerprint out (asserted by test_determinism).

CAVEATS found by DRIVING it on the tripwire + a 6-lens adversarial review (honest limits, not
hidden -- each a refinement target; the load-bearing claim rests on chromatic_mono_index +
neutral_share, and even there a DROP means "less CHROMATIC monopoly", necessary-not-sufficient
for material variety):
  * chromatic_mono_index is BLIND to NEUTRAL mono-material: an all-white plaster or all-grey
    concrete room (a textbook DR §2 trap) has colored_share~0 -> index~0 (reads LEAST mono), and
    the index also FALLS under mere whitening/over-exposure/desaturation with NO second material
    added. It measures CHROMATIC-hue monopoly, not material count. A neutral-mono / tactile-
    variety detector is a separate un-built lane; never gate on this metric alone. The de-wood
    tripwire is honest because that fix added a warm-white PAINT base (a real second material),
    but the metric by itself cannot tell that apart from pure exposure whitening.
  * palette.entropy measures AREA concentration across the clusters, NOT material diversity:
    on the tripwire the walnut render scored HIGHER entropy than de-wood (de-wood's big warm-
    white base dominates one cluster -> lower entropy). So entropy is DESCRIPTIVE only. (Now
    normalized by log(PALETTE_K), a FIXED denominator, so it is comparable across renders.)
  * lighting.highlight_share / range are confounded by palette LIGHTNESS: de-wood read MORE
    "highlights" (0.00 -> 0.048) purely because white walls are bright, while the Gemini gate
    judged de-wood's lighting WORSE (2 -> 1, flatter mood). These metrics describe the luminance
    HISTOGRAM, not lighting QUALITY; do not read a whiter render as "better lit". Calibrate
    against designer verdicts before trusting lighting as a sellability signal.
  * wounds.black_hole_share is a small-magnitude (~0.1%) per-pixel proxy: it detects PRESENCE of
    near-absolute-black and anchors the "refuse to reward the unfixed hole" tripwire, but it does
    not distinguish one connected dead-end cavity from scattered dark pixels, nor catch a "very
    dark but > BLACK_LEVEL" void. Refine with connected-components before gating on it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

FINGERPRINT_VERSION = "1.0"

# ---- Frozen constants (documented; a mutation probe should flip a verdict if these move) ----
WORK_MAX_EDGE = 400          # long edge of the working image; caps KMeans cost, fixes determinism
PALETTE_K = 6                # number of palette clusters
KMEANS_SEED = 0              # deterministic KMeans
KMEANS_N_INIT = 3            # enough to be stable at k=6, cheap
CHROMA_NEUTRAL = 10.0        # LAB chroma <= this => "neutral" (white/gray/black wall/base)
BLACK_LEVEL = 16             # 8-bit: max(R,G,B) < this => near-absolute-black cavity pixel
HIGHLIGHT_L = 85.0           # LAB L* above this => held highlight (window / key)
SHADOW_L_LO, SHADOW_L_HI = 5.0, 25.0   # soft (non-black) shadow band

# sRGB(D65) -> XYZ matrix (IEC 61966-2-1)
_RGB2XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
], dtype=np.float64)
_WHITE_D65 = np.array([0.95047, 1.00000, 1.08883], dtype=np.float64)


def _srgb_to_lab(rgb01: np.ndarray) -> np.ndarray:
    """rgb01: (...,3) in [0,1] sRGB -> LAB (L in [0,100], a,b ~ [-128,127])."""
    a = np.asarray(rgb01, dtype=np.float64)
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    xyz = lin @ _RGB2XYZ.T
    xyz = xyz / _WHITE_D65
    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16.0) / 116.0)
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]
    L = 116.0 * fy - 16.0
    aa = 500.0 * (fx - fy)
    bb = 200.0 * (fy - fz)
    return np.stack([L, aa, bb], axis=-1)


def _load_rgb(path: str) -> np.ndarray:
    """Load image -> uint8 RGB array (H,W,3). RGBA is composited over WHITE (render bg)."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    return np.asarray(im, dtype=np.uint8)


def _work_resize(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    scale = WORK_MAX_EDGE / max(h, w)
    if scale >= 1.0:
        return rgb
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    im = Image.fromarray(rgb).resize((nw, nh), Image.LANCZOS)
    return np.asarray(im, dtype=np.uint8)


def _palette(lab_px: np.ndarray) -> dict:
    """KMeans the LAB pixels; return clusters sorted by descending area share.
    Robust to tiny inputs (k clamped to the sample count, so a <PALETTE_K-pixel image cannot crash
    KMeans) and to tied shares (STABLE sort with a deterministic L*,hue tiebreak, so clusters[] is
    a pure function of the pixel values -- not of the numpy sort build, whose unstable default
    could reorder tied-share clusters across versions and flip the emitted JSON). Entropy is
    normalized by log(PALETTE_K) -- a FIXED denominator -- so it is comparable across renders
    (dividing by log of the OCCUPIED-cluster count would let a 2-colour and a 6-colour image both
    reach 1.0)."""
    k = int(min(PALETTE_K, lab_px.shape[0]))
    km = KMeans(n_clusters=k, random_state=KMEANS_SEED, n_init=KMEANS_N_INIT, max_iter=100)
    labels = km.fit_predict(lab_px)
    counts = np.bincount(labels, minlength=k).astype(np.float64)
    shares = counts / counts.sum()
    centers = km.cluster_centers_
    center_L = centers[:, 0]
    center_hue = np.degrees(np.arctan2(centers[:, 2], centers[:, 1])) % 360.0
    # stable, value-only ordering: -share, then L*, then hue -> identical bytes on any numpy build
    order = sorted(range(k), key=lambda i: (-float(shares[i]),
                                            round(float(center_L[i]), 4),
                                            round(float(center_hue[i]), 4)))
    clusters = []
    for idx in order:
        L, a, b = centers[idx]
        chroma = float(np.hypot(a, b))
        hue = float(np.degrees(np.arctan2(b, a)) % 360.0)
        clusters.append({
            "share": round(float(shares[idx]), 5),
            "L": round(float(L), 2), "a": round(float(a), 2), "b": round(float(b), 2),
            "chroma": round(chroma, 2), "hue": round(hue, 1),
        })
    nz = shares[shares > 0]
    entropy = float(-(nz * np.log(nz)).sum() / np.log(PALETTE_K)) if len(nz) > 1 else 0.0
    return {
        "k": PALETTE_K,
        "dominant_share": clusters[0]["share"],
        "secondary_share": clusters[1]["share"] if len(clusters) > 1 else 0.0,
        "accent_share": clusters[2]["share"] if len(clusters) > 2 else 0.0,
        "entropy": round(entropy, 4),
        "clusters": clusters,
    }


def _material(lab_px: np.ndarray) -> dict:
    """CHROMATIC mono-material detector. colored = chroma>CHROMA_NEUTRAL; chromatic_mono_index =
    colored_share * R, where R (hue_resultant) is the chroma-weighted circular resultant length of
    the colored hues (1 = ALL colored area is ONE hue; low = colored area spans many hues). Walnut
    (large single-hue wood area) -> high; de-wood (wood repainted warm-WHITE, low-chroma =>
    neutral) -> lower, because colored_share drops.

    OVERCLAIM GUARD (review 2026-07-15): this is the CHROMATIC half of the DR §2 mono trap ONLY.
    It is BLIND to neutral/achromatic mono -- an all-white or all-concrete room (a textbook §2
    trap) reads colored_share~0 -> index~0 (LEAST mono) -- and it falls under pure whitening/
    over-exposure with NO material added. A DROP means "less chromatic-hue monopoly", NOT "more
    material variety". Never gate on this alone; the two factors are exposed separately so a
    caller can see whether colored_share (area) or hue_resultant (hue spread) moved."""
    a, b = lab_px[:, 1], lab_px[:, 2]
    chroma = np.hypot(a, b)
    colored = chroma > CHROMA_NEUTRAL
    colored_share = float(colored.mean())
    if colored.sum() > 0:
        ang = np.arctan2(b[colored], a[colored])
        w = chroma[colored]
        resultant = float(np.abs((w * np.exp(1j * ang)).sum()) / w.sum())
        chroma_mean_colored = float(w.mean())
    else:
        resultant, chroma_mean_colored = 0.0, 0.0
    return {
        "colored_share": round(colored_share, 5),
        "neutral_share": round(1.0 - colored_share, 5),
        "hue_resultant": round(resultant, 5),
        "chromatic_mono_index": round(colored_share * resultant, 5),
        "chroma_mean_colored": round(chroma_mean_colored, 3),
    }


def _lighting(lab_px: np.ndarray) -> dict:
    L = lab_px[:, 0]
    p05, p50, p95 = (float(x) for x in np.percentile(L, [5, 50, 95]))
    return {
        "L_p05": round(p05, 2), "L_p50": round(p50, 2), "L_p95": round(p95, 2),
        "range": round(p95 - p05, 2),
        "std": round(float(L.std()), 3),
        "highlight_share": round(float((L > HIGHLIGHT_L).mean()), 5),
        "shadow_share": round(float(((L > SHADOW_L_LO) & (L < SHADOW_L_HI)).mean()), 5),
    }


def _wounds(rgb_full_work: np.ndarray) -> dict:
    """black_hole_share: fraction of near-absolute-black pixels (max channel < BLACK_LEVEL).
    The DR's §1 dead-end cavity. Measured on 8-bit RGB before any LAB transform."""
    mx = rgb_full_work.max(axis=-1)
    return {"black_hole_share": round(float((mx < BLACK_LEVEL).mean()), 6)}


def _safe_ref(path: str) -> str:
    """Privacy scrubber (LOCAL-ONLY law, qa/benchmark-sellability.md:49-59). A client's paid work
    lives under _private/ with client PERSONAL NAMES in the folder segments -- the law forbids
    surfacing a name "even inside a quoted filename". Any path under a _private/ segment is
    replaced by a non-reversible "private:<hash>" token, so no client name can reach stdout,
    --out JSON, or a pasted report. Our OWN render paths (projects/, assets/) use internal project
    codes and pass through readable. This is the sole identifier that leaves fingerprint()."""
    try:
        parts = Path(path).parts
    except (TypeError, ValueError):
        parts = ()
    if "_private" in parts:
        return "private:" + hashlib.sha1(str(path).encode("utf-8", "surrogatepass")).hexdigest()[:12]
    return str(path)


def fingerprint(path: str) -> dict:
    """Deterministic per-axis fingerprint of one interior render. NO network access."""
    rgb = _load_rgb(path)
    h0, w0 = rgb.shape[:2]
    work = _work_resize(rgb)
    hw = work.reshape(-1, 3)
    lab = _srgb_to_lab(hw.astype(np.float64) / 255.0)
    return {
        "ref": _safe_ref(path),
        "size": [int(w0), int(h0)],
        "palette": _palette(lab),
        "warmth": {
            "warmth_index": round(float(lab[:, 2].mean()), 3),   # mean b* (yellow+ = warm)
            "mean_a": round(float(lab[:, 1].mean()), 3),
            "std_b": round(float(lab[:, 2].std()), 3),
        },
        "material": _material(lab),
        "lighting": _lighting(lab),
        "wounds": _wounds(work),
        "_meta": {
            "version": FINGERPRINT_VERSION,
            "work_size": [int(work.shape[1]), int(work.shape[0])],
            "kmeans_seed": KMEANS_SEED, "palette_k": PALETTE_K,
        },
    }


# axes on which "more is more mono / less sellable" -- used only for readable compare output
def compare(fp_a: dict, fp_b: dict) -> dict:
    """Directional deltas b - a on the load-bearing axes (for tripwire reads / gap reports)."""
    def g(fp, *ks):
        x = fp
        for k in ks:
            x = x[k]
        return x
    axes = {
        "chromatic_mono_index": ("material", "chromatic_mono_index"),
        "colored_share": ("material", "colored_share"),
        "neutral_share": ("material", "neutral_share"),
        "palette_entropy": ("palette", "entropy"),
        "warmth_index": ("warmth", "warmth_index"),
        "lighting_range": ("lighting", "range"),
        "highlight_share": ("lighting", "highlight_share"),
        "black_hole_share": ("wounds", "black_hole_share"),
    }
    return {name: {"a": g(fp_a, *ks), "b": g(fp_b, *ks),
                   "delta": round(g(fp_b, *ks) - g(fp_a, *ks), 5)}
            for name, ks in axes.items()}


def _main(argv=None):
    ap = argparse.ArgumentParser(description="LOCAL interior-render style fingerprint (no API).")
    ap.add_argument("images", nargs="+", help="image path(s)")
    ap.add_argument("--json", action="store_true", help="emit raw JSON list to stdout")
    ap.add_argument("--compare", action="store_true",
                    help="with exactly 2 images: print directional deltas (b - a)")
    ap.add_argument("--out", help="write JSON to this path instead of stdout")
    args = ap.parse_args(argv)

    fps = [fingerprint(p) for p in args.images]
    if args.compare:
        if len(fps) != 2:
            ap.error("--compare needs exactly 2 images")
        result = {"a": fps[0]["ref"], "b": fps[1]["ref"], "deltas": compare(fps[0], fps[1])}
    else:
        result = fps

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    elif args.json or args.compare:
        print(text)
    else:
        for fp in fps:
            m, l, w = fp["material"], fp["lighting"], fp["wounds"]
            ref = fp["ref"]
            print(ref if ref.startswith("private:") else Path(ref).name)
            print(f"  chromatic_mono_index {m['chromatic_mono_index']:.3f}  "
                  f"neutral_share {m['neutral_share']:.3f}  colored {m['colored_share']:.3f}")
            print(f"  palette entropy {fp['palette']['entropy']:.3f}  "
                  f"warmth {fp['warmth']['warmth_index']:+.1f}")
            print(f"  light range {l['range']:.1f}  highlight {l['highlight_share']:.3f}  "
                  f"shadow {l['shadow_share']:.3f}  black_hole {w['black_hole_share']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
