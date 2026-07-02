"""
overlay_fidelity.py — layout-fidelity check for the HYBRID render pass (M2.1 acceptance).

The HYBRID direction only works if the Gemini beauty pass keeps the layout the 3D
control render encodes. This script makes that checkable instead of vibes:

  * edge-detect both images (control = clay render, candidate = hybrid output)
  * dilate control edges by a pixel tolerance, measure how many candidate edge
    pixels land on (dilated) control edges and vice versa (precision / recall)
  * write a colour overlay: control edges RED, candidate edges GREEN — aligned
    structure reads YELLOW; lone red = structure the repaint LOST, lone green =
    structure it INVENTED. A human eyeballs the overlay; the numbers only flag.

    python pipeline/scripts/overlay_fidelity.py CONTROL.png CANDIDATE.png [OUT_overlay.png]

Numbers are a DRAFT heuristic (texture detail in the photoreal pass legitimately
adds edges, so precision runs low by design) — the RED channel of the overlay is
the real verdict: heavy lone-red lines = walls/furniture moved. Needs numpy +
matplotlib (already required for the PNG previews).
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("overlay_fidelity needs numpy + pillow -> pip install numpy pillow")

TOL_PX = 8           # alignment tolerance after resize (≈ wall-thickness scale)
EDGE_PCTL = 90       # gradient percentile that counts as an "edge"


def _edges(img_gray):
    gy, gx = np.gradient(img_gray.astype(float))
    mag = np.hypot(gx, gy)
    return mag >= np.percentile(mag, EDGE_PCTL)


def _dilate(mask, r):
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy == 0 and dx == 0:
                continue
            shifted = np.zeros_like(mask)
            ys = slice(max(dy, 0), mask.shape[0] + min(dy, 0))
            xs = slice(max(dx, 0), mask.shape[1] + min(dx, 0))
            ys_src = slice(max(-dy, 0), mask.shape[0] + min(-dy, 0))
            xs_src = slice(max(-dx, 0), mask.shape[1] + min(-dx, 0))
            shifted[ys, xs] = mask[ys_src, xs_src]
            out |= shifted
    return out


def check(control_path, candidate_path, out_path=None):
    ctrl = Image.open(control_path).convert("L")
    cand = Image.open(candidate_path).convert("L").resize(ctrl.size, Image.LANCZOS)
    e_ctrl = _edges(np.asarray(ctrl))
    e_cand = _edges(np.asarray(cand))
    d_ctrl = _dilate(e_ctrl, TOL_PX)
    d_cand = _dilate(e_cand, TOL_PX)

    # recall: control structure the candidate kept (the load-bearing number);
    # precision: candidate edges explained by control (texture detail drags it down — informational)
    recall = float((e_ctrl & d_cand).sum()) / max(1, e_ctrl.sum())
    precision = float((e_cand & d_ctrl).sum()) / max(1, e_cand.sum())

    if out_path is None:
        base, _ = os.path.splitext(candidate_path)
        out_path = f"{base}.overlay.png"
    rgb = np.stack([np.asarray(ctrl)] * 3, axis=-1) // 3 + 120   # faded grey base
    rgb = rgb.astype(np.uint8)
    lone_red = e_ctrl & ~d_cand
    lone_green = e_cand & ~d_ctrl
    matched = e_ctrl & d_cand
    rgb[lone_red] = (220, 40, 40)      # control structure LOST by the repaint
    rgb[lone_green] = (40, 180, 40)    # structure the repaint INVENTED (texture is fine)
    rgb[matched] = (230, 210, 60)      # aligned structure
    Image.fromarray(rgb).save(out_path)

    verdict = "PASS" if recall >= 0.80 else ("REVIEW" if recall >= 0.60 else "FAIL")
    print(f"=== overlay fidelity: {os.path.basename(candidate_path)} vs "
          f"{os.path.basename(control_path)} (tol {TOL_PX}px) ===")
    print(f"  structure recall   : {recall:.1%}  (control edges kept by the repaint)")
    print(f"  edge precision     : {precision:.1%}  (informational — photoreal texture lowers this)")
    print(f"  overlay            : {out_path}  (lone RED = layout drift; eyeball before trusting)")
    print(f"  -> {verdict}  (DRAFT heuristic — human eyeballs the overlay for the real call)")
    return recall, precision, verdict, out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    _, _, verdict, _ = check(sys.argv[1], sys.argv[2],
                             sys.argv[3] if len(sys.argv) > 3 else None)
    sys.exit(0 if verdict != "FAIL" else 1)
