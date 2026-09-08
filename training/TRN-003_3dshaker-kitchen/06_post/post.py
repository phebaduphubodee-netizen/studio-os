#!/usr/bin/env python3
"""post.py - the tutorial's stage 5 (28:45-34:20), with his gestures written as measurements.

    python 06_post/post.py 05_build/out/p8_noisy.png 05_build/out/p8_denoised.png \
        --out 06_post/out/final.png

WHAT HE DOES, IN ORDER, AND WHAT WE DO INSTEAD
==============================================

1. SAVE THE NOISY FRAME, THEN THE DENOISED ONE. Both are inputs here. Same as him.

2. PAINT THE DENOISED BACK OVER THE NOISY, BY HAND, WITH A MASK - "and in some cases like
   the curtain here I will only use 50% opacity of the brush because the denoised image
   killed too much detail of the curtain".
   OURS: the same result, driven by a measurement instead of a brush. The blend weight at
   every pixel is a LOCAL NOISE ESTIMATE - the local standard deviation of (noisy minus
   denoised), which is large where the renderer was still converging and near zero where
   the denoiser only smoothed real detail away. So the denoised image wins in the noisy
   places and the noisy one keeps its detail everywhere else, which is exactly the
   judgement his brush is making, made per pixel and repeatably.
   This is BETTER than the brush in one specific way and worse in none: a brush cannot tell
   noise from texture, and his own commentary says so.

3. MAGNIFIC AI, x2 UPSCALE, FOUR GENERATIONS AT RISING "CREATIVITY", THEN PAINT IN THE
   BITS YOU LIKE (30:40-32:30).
   OURS: NOT RUN, and this is a decision with reasons, not an omission.
     (a) It is a paid external service. R6/R8: a SPEND is the owner's call per purchase.
     (b) It sends the frame off this machine. Our own render is the one thing that IS
         allowed to leave (R7b), so this is the weakest of the three reasons.
     (c) THE ONE THAT DECIDES IT: a generative upscaler INVENTS detail. At creativity 4 and
         6 it is writing wood grain, fabric weave and stone veining that no measurement in
         this lane put there. This studio's entire ledger is about not fabricating readings;
         shipping a frame whose last 30% of detail was hallucinated, into a lane whose
         purpose is learning to MAKE that detail, would teach the wrong thing.
   AND IT IS WORTH SAYING WHAT THAT MEANS ABOUT THE REFERENCE WORKFLOW: the tutorial's
   final image is substantially generated. Anyone benchmarking a hand-built render against
   his result is comparing against a hybrid. That is a fact about the target, and this lane
   should know it.
   WHAT WE DO INSTEAD: pipeline/scripts/upscale.py, which already exists, uses Real-ESRGAN
   if it is installed and an honest Lanczos+unsharp if it is not, and writes a sidecar
   saying WHICH. Run it separately; it is not part of this file, because a deliverable's
   scale should be a disclosed decision and not a side effect of a post script.

4. HIGH PASS ON A SMART OBJECT, BLEND MODE SOFT LIGHT, OPACITY ~20%, then a second copy at
   50% masked into some areas (32:40-33:20).
   OURS: the same operation exactly - a high-pass (image minus a Gaussian blur, centred on
   mid-grey) composited in soft light at a stated opacity. This one is deterministic in
   Photoshop too, so it is a port rather than a replacement. His second masked copy is not
   done: a mask painted by taste has no measurement behind it and one opacity is honest.

5. CAMERA RAW (33:30) - he tries it and says it did not help this image. Not done.

6. BEFORE / AFTER, AND LOWER THE OPACITY IF IT WENT TOO FAR (33:45-34:15). This is the best
   habit in the whole video and it is free, so it is built in: --sheet writes the pair side
   by side with the numbers underneath.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def to_f(im):
    return np.asarray(im.convert("RGB")).astype(np.float32) / 255.0


def to_im(a):
    return Image.fromarray(np.clip(a * 255.0, 0, 255).astype(np.uint8), "RGB")


def local_sd(a, r=3):
    """Local standard deviation, per pixel, over a (2r+1) box - a noise estimate."""
    g = a.mean(axis=2)
    k = 2 * r + 1
    pad = np.pad(g, r, mode="edge")
    c = np.cumsum(np.cumsum(pad, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))

    def box(arr):
        return (arr[k:, k:] - arr[:-k, k:] - arr[k:, :-k] + arr[:-k, :-k])
    s1 = box(c)
    pad2 = np.pad(g ** 2, r, mode="edge")
    c2 = np.pad(np.cumsum(np.cumsum(pad2, axis=0), axis=1), ((1, 0), (1, 0)))
    s2 = box(c2)
    n = float(k * k)
    var = np.maximum(s2 / n - (s1 / n) ** 2, 0.0)
    return np.sqrt(var)


def local_mean(a, r=3):
    g = a.mean(axis=2) if a.ndim == 3 else a
    k = 2 * r + 1
    pad = np.pad(g, r, mode="edge")
    c = np.pad(np.cumsum(np.cumsum(pad, axis=0), axis=1), ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / float(k * k)


def noise_blend(noisy, denoised, coherence_full=0.9, floor=0.35):
    """Step 2. Which pixels get the denoised version, decided by a statistic.

    THE FIRST VERSION OF THIS USED THE WRONG QUANTITY and the render said so immediately:
    it weighted by the MAGNITUDE of the local noise, normalised to the 99th percentile, so
    only the worst one per cent of the frame was actually denoised, the mean weight came out
    at 0.24, and the output was grainier than either input. Magnitude cannot separate noise
    from detail, because both are large.

    COHERENCE CAN. Take d = noisy - denoised. Where the denoiser removed REAL DETAIL, d is
    locally CONSISTENT - a curtain thread or a plank joint pushes a whole neighbourhood the
    same way, so |mean(d)| over the box is comparable to sd(d) over it. Where d is Monte
    Carlo noise it is zero-mean and incoherent, so |mean(d)| collapses relative to sd(d).
    The ratio is dimensionless, needs no threshold in absolute units, and is exactly the
    judgement his brush is making when he goes to 50% opacity over the curtain and 100%
    everywhere else - said as a number, per pixel.

    `floor` keeps a minimum share of the denoised image everywhere, because a render at a
    finite sample count is noisy even where the statistic is undecided, and shipping visible
    Monte Carlo grain as if it were texture is the failure this whole step exists to avoid.
    """
    d = noisy - denoised
    sd = local_sd(d, r=3)
    mu = np.abs(local_mean(d, r=3))
    coh = mu / (sd + 1e-6)
    keep_noisy = np.clip(coh / coherence_full, 0.0, 1.0) * (1.0 - floor)
    w = (1.0 - keep_noisy)[..., None]
    return denoised * w + noisy * (1.0 - w), w[..., 0]


def high_pass_soft_light(a, radius=2.0, opacity=0.20):
    """Step 4. High pass = image minus its own blur, centred on 0.5; soft light on top."""
    blur = np.asarray(to_im(a).filter(ImageFilter.GaussianBlur(radius))).astype(np.float32) / 255.0
    hp = np.clip(a - blur + 0.5, 0.0, 1.0)
    # Photoshop's soft light, the W3C/SVG formulation
    def d(x):
        return np.where(x <= 0.25, ((16 * x - 12) * x + 4) * x, np.sqrt(x))
    b, s = a, hp
    out = np.where(s <= 0.5,
                   b - (1 - 2 * s) * b * (1 - b),
                   b + (2 * s - 1) * (d(b) - b))
    return np.clip(a * (1 - opacity) + out * opacity, 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("noisy")
    ap.add_argument("denoised")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hp-radius", type=float, default=2.0)
    ap.add_argument("--hp-opacity", type=float, default=0.20)
    ap.add_argument("--sheet", default="")
    o = ap.parse_args()

    a, b = Image.open(o.noisy), Image.open(o.denoised)
    if a.size != b.size:
        print(f"exit 2 - COULD NOT RUN. {a.size} vs {b.size}. The two halves of the pair "
              f"must be the same render at the same size.", file=sys.stderr)
        return 2
    A, B = to_f(a), to_f(b)

    merged, w = noise_blend(A, B)
    final = high_pass_soft_light(merged, o.hp_radius, o.hp_opacity)

    os.makedirs(os.path.dirname(os.path.abspath(o.out)), exist_ok=True)
    to_im(final).save(o.out)

    stats = dict(
        noisy=os.path.basename(o.noisy), denoised=os.path.basename(o.denoised),
        out=os.path.basename(o.out),
        noise_blend=dict(
            mean_weight_toward_denoised=round(float(w.mean()), 4),
            share_of_pixels_over_half=round(float((w > 0.5).mean()), 4),
            note="1.0 = took the denoised pixel, 0.0 = kept the noisy one"),
        high_pass=dict(radius=o.hp_radius, opacity=o.hp_opacity, blend="soft light"),
        not_done=dict(
            magnific_ai="refused - a generative upscaler invents detail; see the docstring",
            camera_raw="the tutorial tries it at 33:30 and says it did not help",
            second_masked_high_pass="a mask painted by taste has no measurement behind it"),
        before_after_rms=round(float(np.sqrt(((final - A) ** 2).mean())), 5),
    )
    json.dump(stats, open(os.path.splitext(o.out)[0] + ".post.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))

    if o.sheet:
        W, H = a.size
        sc = 900.0 / W
        sw, sh = int(W * sc), int(H * sc)
        sheet = Image.new("RGB", (sw * 2 + 24, sh + 56), (18, 18, 18))
        sheet.paste(to_im(A).resize((sw, sh), Image.LANCZOS), (0, 40))
        sheet.paste(to_im(final).resize((sw, sh), Image.LANCZOS), (sw + 24, 40))
        d = ImageDraw.Draw(sheet)
        d.text((8, 14), "BEFORE  (the noisy render, straight out of Cycles)",
               fill=(230, 230, 230))
        d.text((sw + 32, 14), f"AFTER  (noise-weighted denoise merge + high pass "
                              f"{o.hp_opacity:.0%} soft light)", fill=(230, 230, 230))
        d.text((8, sh + 44), f"rms difference {stats['before_after_rms']:.4f}   "
                             f"mean weight toward denoised "
                             f"{stats['noise_blend']['mean_weight_toward_denoised']:.2f}   "
                             f"NO generative upscale", fill=(160, 160, 160))
        sheet.save(o.sheet)
        print("sheet ->", o.sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
