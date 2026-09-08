"""cloth_highlights.py — P2r-5's instrument: per-material HIGHLIGHT histograms
read off the FRAME (R11: the rung opens the picture), attributed through the
census mask pair (`map_census_mask.py`).

WHY IT EXISTS. The plan item's close condition is "no clipped-plastic highlight
family on cloth" and until this file nothing could measure it — the two nulls
that opened P2r-5 (sheen already capped; wood bump unreachable) were both paid
to learn that the critics' "พลาสติก" verdict has no instrument behind it. This
gives the claim a number BEFORE the mechanism round builds anything
(instrument-before-build, the P2r-7 law).

WHAT IT MEASURES, so the verdict can fail: within one material's visible
pixels, the CLIPPED SHARE is the % whose peak channel is >= CLIP_LEVEL. Cloth
under this room's soft light must not carry a clipped family
(share >= CLIP_SHARE_MAX_PCT); a lamp face or brass may. The table prints for
EVERY material above a share floor — no allowlist (R9b: a rule that names the
objects it applies to will always exempt the next one) — and the VERDICT
applies to the rows the caller names as cloth (default: the three largest bed
whites, the plan item's own scope, overridable with --cloth).

HONESTY CONTRACTS (R11): no mask pair -> NOT RUN, exit 2, never a number. A
named cloth material with zero visible pixels -> COULD NOT JUDGE, exit 2 — an
invisible surface must never print like a clean one.

    python pipeline/scripts/cloth_highlights.py pipeline/output/room_x.png
        [--cloth bed_duvet,bed_coverlet,bed_pillow] [--json]
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

import map_census as MC

CLIP_LEVEL = 250          # peak-channel sRGB code read as "clipped" (8-bit frame)
BRIGHT_LEVEL = 235        # the shoulder band under it, reported for trend
CLIP_SHARE_MAX_PCT = 0.2  # a cloth row at/above this share carries a clipped family
SHARE_FLOOR_PCT = 0.5     # table print floor; the verdict ignores this floor
DEFAULT_CLOTH = ("bed_duvet", "bed_coverlet", "bed_pillow")


def stats(render_png, mask_png=None):
    """Per-material highlight stats, or None when the mask pair is absent.

    Peak channel (max of R,G,B), not luminance: clipping shows first in one
    channel, and a luminance mean would hide a blown channel behind two dark
    ones — the exact read this instrument exists to catch."""
    mask_png = mask_png or MC.mask_sidecar(render_png)
    meta_path = os.path.splitext(mask_png)[0] + ".json"
    if not (os.path.exists(render_png) and os.path.exists(mask_png)
            and os.path.exists(meta_path)):
        return None
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    ids = {int(k): v for k, v in meta["ids"].items()}
    frame = np.asarray(Image.open(render_png).convert("RGB"))
    plane = MC.decode_ids(np.asarray(Image.open(mask_png).convert("RGB")))
    if frame.shape[:2] != plane.shape:
        # a mask from another resolution attributes the wrong pixels — refuse
        # rather than resample (R11: a resampled comparison is a different
        # measurement; "could not look" must never print like "looked, fine")
        return {"error": f"mask {plane.shape[::-1]} != frame {frame.shape[1::-1]}"}
    peak = frame.max(axis=2)
    total = plane.size
    rows = []
    for i, nm in sorted(ids.items()):
        sel = peak[plane == i]
        if sel.size == 0:
            rows.append({"material": nm, "share_pct": 0.0, "px": 0})
            continue
        rows.append({
            "material": nm,
            "share_pct": 100.0 * sel.size / total,
            "px": int(sel.size),
            "p50": float(np.percentile(sel, 50)),
            "p95": float(np.percentile(sel, 95)),
            "p99": float(np.percentile(sel, 99)),
            "max": int(sel.max()),
            "clip_share_pct": 100.0 * float((sel >= CLIP_LEVEL).mean()),
            "bright_share_pct": 100.0 * float((sel >= BRIGHT_LEVEL).mean()),
        })
    rows.sort(key=lambda r: -r.get("clip_share_pct", -1.0))
    return {"rows": rows}


def verdict(rows, cloth_names):
    """(fails, unjudgeable): cloth rows carrying a clipped family, and cloth
    rows with no visible pixels. Both lists name materials; neither is empty
    silently — the caller prints each by name."""
    by_name = {r["material"]: r for r in rows}
    fails, unjudgeable = [], []
    for nm in cloth_names:
        r = by_name.get(nm)
        if r is None or r.get("px", 0) == 0:
            unjudgeable.append(nm)
        elif r["clip_share_pct"] >= CLIP_SHARE_MAX_PCT:
            fails.append((nm, r["clip_share_pct"]))
    return fails, unjudgeable


def report_lines(res, cloth_names):
    lines = []
    printable = [r for r in res["rows"]
                 if r.get("px", 0) and r["share_pct"] >= SHARE_FLOOR_PCT]
    lines.append(f"CLOTH-HIGHLIGHTS (peak-channel codes; clip >= {CLIP_LEVEL}, "
                 f"cloth family fails at clip-share >= {CLIP_SHARE_MAX_PCT}%)")
    for r in printable:
        tag = " [cloth]" if r["material"] in cloth_names else ""
        lines.append(
            f"  {r['material'][:28]:28} share {r['share_pct']:5.1f}%  "
            f"p50 {r['p50']:5.1f}  p95 {r['p95']:5.1f}  p99 {r['p99']:5.1f}  "
            f"max {r['max']:3d}  clip {r['clip_share_pct']:.3f}%{tag}")
    fails, unjudgeable = verdict(res["rows"], cloth_names)
    for nm, share in fails:
        lines.append(f"  FAIL {nm}: clipped-plastic highlight family "
                     f"({share:.3f}% of its pixels >= {CLIP_LEVEL})")
    for nm in unjudgeable:
        lines.append(f"  COULD NOT JUDGE {nm}: no visible pixels in this frame")
    if not fails and not unjudgeable:
        lines.append("  no clipped-plastic highlight family on the named cloth")
    return lines, fails, unjudgeable


def main(argv):
    # The P1 lesson verbatim: a Thai material name through a cp1252 console
    # kills the process with exit 1 — this tool's code for "ran, found fails".
    # A crashed instrument must never print like a verdict, so unmappable
    # characters degrade to '?' instead of taking the process down.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print("usage: cloth_highlights.py <render.png> [--cloth a,b,c] [--json]")
        return 2
    cloth = DEFAULT_CLOTH
    for a in argv[1:]:
        if a.startswith("--cloth="):
            cloth = tuple(x for x in a.split("=", 1)[1].split(",") if x)
    res = stats(args[0])
    if res is None:
        print("CLOTH-HIGHLIGHTS NOT RUN — no census mask pair beside the "
              "render (full builds write it; absence is not a pass)")
        return 2
    if "error" in res:
        print(f"CLOTH-HIGHLIGHTS COULD NOT RUN — {res['error']}")
        return 2
    lines, fails, unjudgeable = report_lines(res, cloth)
    for ln in lines:
        print(ln)
    if "--json" in argv:
        print(json.dumps({"rows": res["rows"], "fails": fails,
                          "unjudgeable": unjudgeable}))
    if unjudgeable:
        return 2
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
