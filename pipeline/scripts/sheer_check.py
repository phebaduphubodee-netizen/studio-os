#!/usr/bin/env python3
"""sheer_check.py — DOES THE WINDOW WALL HAVE STRUCTURE, AND DOES THE CLOTH TOUCH DOWN?

Two numbers, both measured on the rendered pixels, both of which decided P2r-38/P2r-39
and neither of which any rung in this repo could see.

WHY IT EXISTS (2026-09-02, P2r-39)
----------------------------------
1. THE STRUCTURE NUMBER, and why it is LOCAL rather than a spread. The plan's inherited
   bar was "share of the window band inside [0.80, 0.90) <= 40%". A five-point bracket of
   the sheer's openness showed that bar passing by GOING DARK: at `--sheer-direct=0.90`
   the share collapses to 8.89% while local detail falls 44% (0.0367 -> 0.0204) and the
   band's spread falls 0.434 -> 0.364. A bar that a uniform darkening satisfies measures
   LEVEL, and the complaint — six sighted judges, C2 and C3 across three rounds — is
   about STRUCTURE. So this rung measures RMS CONTRAST — `std(L - blur(L))` divided by
   the bright field's own mean — and the division is not cosmetic: the first cut used the
   bare std and OVERCLAIMED, because L -> kL scales it by k, so a uniform darkening still
   moves it. Positive control on a real frame: darkening x1.00 / x0.85 / x0.70 gives
   std 0.0367 / 0.0311 / 0.0256 but RMS contrast 0.0452 / 0.0451 / 0.0451. The flattering
   direction is closed by construction only in the normalised form.
   AND THE PIXEL SET IS CHOSEN BY MATERIAL, NOT BY BRIGHTNESS, for the same reason. The
   first cut selected "the fabric field" with a fixed luma threshold (L > 0.60) and its
   own synthetic test refused it inside a minute: darkening the frame moves pixels ACROSS
   that threshold, so the metric was being computed on a different set each time and the
   invariance was fake. The mask already knows which pixels are cloth. Selecting them by
   name is exact, needs no threshold, and cannot be gamed by exposure at all.

2. THE HEM NUMBER, and the fact that its FIRST DEFINITION WAS WRONG. C2 filed the defect
   by eye on p2r95 — "each strip terminates at its own height, timber floor is visible
   underneath several of them" — and the first cut of this rung took that sentence
   literally and counted columns with FLOOR below the hem. That predicate is always-ish
   true and cannot fail: the floor lies BETWEEN the camera and the cloth, so it is under
   every hem at every height. The tell came immediately — lowering the hem from 15-47 mm
   to 4-13 mm made the number get WORSE (47.2% -> 62.0%), which is the shape of an
   instrument measuring the wrong thing, not of a fix going backwards.
   WHAT IS ACTUALLY PATHOLOGICAL is seeing what is BEHIND the cloth below its hem: on
   p2r95, 133 of 706 columns (18.8%) had `glazing` directly under the fabric — the window
   itself, visible beneath a curtain that was supposed to cover it. After the hem came
   down that is 0. Floor under a hem is a room; GLASS under a hem is a curtain that does
   not reach. The cited grammar is a working drapery designer's ("hem 3-6 mm clear, or
   graze, or puddle"), staged in this repo since 2026-08-28 and unread until the round
   that needed it.

EXIT CODES ARE A CONTRACT, the same one R11 wrote for pixel_check:
  0 = both readings taken and inside their bars
  1 = a reading is outside its bar
  2 = COULD NOT RUN (no mask, no sheer in frame, wrong frame size). "Could not look"
      must never print like "looked and it was fine".

PURE-ISH LAYER 3: needs PIL + numpy, which Blender's bundled Python does not have, so
this is SPAWNED out of process after a render — never imported into a gate module inside
`bpy` (pipeline/CLAUDE.md layer law).
"""
import argparse
import json
import os
import sys

# ---- the bars. Both are LOOK-chosen against this lane's own frames and say so. -------
# RMS contrast, measured on FULL-FIDELITY frames only — a playblast is half the
# resolution per axis and resolves different detail, so its numbers do not transfer here
# (the same reason R11's pixel_check refuses to compare across resolutions).
#
# WHAT THIS NUMBER IS, said plainly so nobody reads a PASS as "the sheer is fixed": it is
# a RATCHET FLOOR — "do not get worse" — not a quality bar. Full frames measured:
# p2r93b 0.0304 · p2r95 0.0444 · p2r96 0.0495 · p2r97 0.0444.
# It sat at 0.045 for exactly one round. p2r96 crossed it by lowering the sheer's
# openness, and the sighted panel then ranked that frame 4/5, 4/5, 4/5 against 2/3/2 —
# because the same change raised the cloth's LEVEL (p50 0.8460 -> 0.8586) and three judges
# independently called it "a pure white void" / "a light box" / "a hole, not a window".
# The change was reverted, so 0.045 became a bar no frame could reach by any lever this
# lane still has, and a bar like that prints FAIL forever and stops being read.
# The floor is therefore the ACHIEVED level. Raising it needs a NEW mechanism, not another
# turn of the transmission knob — that one is exhausted in both directions (see
# _SHEER_DIRECT_FRAC in build_room.py) — and the honest next lever is not on this metric
# at all: judges name the bench and the headboard further above the field than the sheer
# (panel_diff.py). Do not raise this number to make a round look like progress.
STRUCTURE_MIN = 0.044
# behind-under-hem: share of fabric columns showing GLASS OR WALL beneath the hem. The
# bar is 1% rather than 0 because a pleat tip at the very end of a run can legitimately
# clear the glass edge; 18.8% is a curtain that does not reach.
BEHIND_UNDER_MAX_PCT = 1.0
# what counts as "behind the cloth" — matched on the material name, so a renamed or newly
# acquired glazing material joins automatically instead of being silently exempt (R9b:
# a rule that names the objects it applies to will always miss the next one)
BEHIND_TOKENS = ("glaz", "glass", "wall", "mullion", "jamb")
BLUR_SIGMA = 6.0
PROBE_PX = 3               # how far below the hem to look for floor
MIN_CLOTH_PX = 5000        # below this the reading is refused, never reported thin


def rms_contrast(reg, sel):
    """Local RMS contrast of `reg` over the boolean selection `sel`.

    Split out so a test can hold `sel` FIXED and prove the number does not move when the
    image is scaled — which is the one property this rung is built on."""
    import numpy as np
    from PIL import Image, ImageFilter
    blur = np.asarray(Image.fromarray((np.clip(reg, 0, 1) * 255).astype("uint8"))
                      .filter(ImageFilter.GaussianBlur(BLUR_SIGMA))).astype(np.float32) / 255.0
    hp = reg - blur
    mu = float(reg[sel].mean())
    if mu <= 1e-6:
        raise RuntimeError("selection has no level to normalise by")
    return float(hp[sel].std()) / mu


def _luma(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def measure(beauty_png, mask_png, mask_json, band=None):
    """-> dict of readings. Raises RuntimeError when it cannot measure (caller -> exit 2)."""
    import numpy as np
    from PIL import Image, ImageFilter
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import value_probe as vp

    with open(mask_json, encoding="utf-8") as fh:
        side = json.load(fh) or {}
    ids = {int(k): v for k, v in (side.get("ids") or {}).items()}
    if not ids:
        raise RuntimeError(f"{mask_json} carries no ids")
    n2i = {v: k for k, v in ids.items()}
    if "curtain_sheer" not in n2i:
        raise RuntimeError("no `curtain_sheer` material in this frame's mask — this rung "
                           "measures a sheer and there is not one here")
    beauty = np.asarray(Image.open(beauty_png).convert("RGB"))
    maskim = np.asarray(Image.open(mask_png).convert("RGB"))
    if beauty.shape[:2] != maskim.shape[:2]:
        raise RuntimeError(f"beauty {beauty.shape[:2]} and mask {maskim.shape[:2]} are "
                           f"different sizes — a mask from another frame measures nothing")
    idm = vp.decode_ids(maskim)
    L = _luma(beauty.astype(np.float32) / 255.0)
    H, W = L.shape

    # ---- 1. structure over the window band ------------------------------------------
    if band is None:
        # DERIVED FROM THE FABRIC, NOT TYPED — but from ALL of it. The first cut took the
        # SHEER's bounding box alone and the two frames it was first run on proved that
        # wrong inside a minute: parking the blackout over the west end moved the band
        # from x1694 to x1877, so the "before" and "after" numbers described different
        # rectangles and were not comparable. A derived box fixes the
        # `crop-box-is-a-typed-coordinate` defect only if it is derived from something
        # that does not move when the thing under test moves. The CURTAIN WALL does not:
        # it is sheer UNION opaque, and re-parking shuffles which is which without
        # changing the union.
        _fab = np.zeros_like(idm, bool)
        for _m in ("curtain_sheer", "curtain_opaque"):
            if _m in n2i:
                _fab |= (idm == n2i[_m])
        ys, xs = np.where(_fab)
        if xs.size == 0:
            raise RuntimeError("curtain materials are declared in the mask but reach 0 px")
        band = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    x0, y0, x1, y1 = band
    reg = L[y0:y1, x0:x1]
    if reg.size < 10000:
        raise RuntimeError(f"window band is {reg.size} px — too small to measure")
    # THE CLOTH'S OWN PIXELS, by material — no brightness threshold to drift across
    cloth = np.zeros_like(idm, bool)
    for _m in ("curtain_sheer", "curtain_opaque"):
        if _m in n2i:
            cloth |= (idm == n2i[_m])
    sel = cloth[y0:y1, x0:x1]
    if sel.sum() < MIN_CLOTH_PX:
        raise RuntimeError(f"only {int(sel.sum())} cloth px inside the band — refusing to "
                           f"report a structure number from that")
    local_std = rms_contrast(reg, sel)
    _mu = float(reg[sel].mean())

    # ---- 2. does the cloth touch down? ----------------------------------------------
    fabric = np.zeros_like(idm, bool)
    for m in ("curtain_sheer", "curtain_opaque"):
        if m in n2i:
            fabric |= (idm == n2i[m])
    behind_ids = {i for i, n in ids.items()
                  if any(t in n.lower() for t in BEHIND_TOKENS)}
    cols = under = 0
    for c in range(W):
        col = np.where(fabric[:, c])[0]
        if col.size < 5:
            continue
        cols += 1
        b = int(col.max())
        if b + PROBE_PX < H and int(idm[b + PROBE_PX, c]) in behind_ids:
            under += 1
    if cols == 0:
        raise RuntimeError("no fabric column has a bottom edge in this frame")
    if not behind_ids:
        raise RuntimeError("no glazing/wall material in this frame's mask — this reading "
                           "would be a guaranteed 0% and that is not a measurement")
    return {
        "band": [x0, y0, x1, y1],
        "local_contrast": local_std,
        "bright_mean": _mu,
        "cloth_px": int(sel.sum()),
        "spread_p5_p95": float(np.percentile(reg, 95) - np.percentile(reg, 5)),
        "fabric_columns": cols,
        "behind_under_hem": under,
        "behind_under_pct": 100.0 * under / cols,
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("beauty")
    ap.add_argument("--mask", default=None, help="default: <beauty>.matmask.png")
    ap.add_argument("--structure-min", type=float, default=STRUCTURE_MIN)
    ap.add_argument("--behind-under-max", type=float, default=BEHIND_UNDER_MAX_PCT)
    a = ap.parse_args(argv)
    stem = a.beauty[:-4] if a.beauty.lower().endswith(".png") else a.beauty
    mask = a.mask or (stem + ".matmask.png")
    mjson = mask[:-4] + ".json" if mask.lower().endswith(".png") else mask + ".json"
    for p in (a.beauty, mask, mjson):
        if not os.path.isfile(p):
            print(f"SHEER  COULD NOT RUN — missing {p}", file=sys.stderr)
            return 2
    try:
        r = measure(a.beauty, mask, mjson)
    except Exception as e:                                   # noqa: BLE001
        print(f"SHEER  COULD NOT RUN — {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    ok_s = r["local_contrast"] >= a.structure_min
    ok_h = r["behind_under_pct"] <= a.behind_under_max
    print(f"SHEER  structure(RMS contrast) {r['local_contrast']:.4f} vs >={a.structure_min:.3f} "
          f"{'PASS' if ok_s else 'FAIL'}  [band {r['band']}, {r['cloth_px']:,} cloth px, "
          f"spread {r['spread_p5_p95']:.3f}]")
    print(f"SHEER  hem reaches: glass/wall visible under the hem in "
          f"{r['behind_under_hem']}/{r['fabric_columns']} columns = "
          f"{r['behind_under_pct']:.1f}% vs <={a.behind_under_max:.1f}% "
          f"{'PASS' if ok_h else 'FAIL'}")
    if not ok_s:
        print("SHEER  the window wall is flat — and NOT because it is too bright: this "
              "number cannot be moved by exposure, only by structure in the cloth")
    if not ok_h:
        print("SHEER  the window is visible BENEATH its own curtain — the hem does not "
              "reach. C2 named this by eye before any instrument could see it")
    return 0 if (ok_s and ok_h) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
