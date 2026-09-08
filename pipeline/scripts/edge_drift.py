#!/usr/bin/env python3
"""edge_drift.py — did a generative edit MOVE our geometry? (pure core; no bpy)

    python pipeline/scripts/edge_drift.py <before.png> <after.png> <mask.png> <mask.json>

CLI-ONLY: the builder, on any frame an image model returned — and `edit_call.py` runs it
itself on every frame it fetches, which is the path that actually matters (D-011). It is
declared here as well because `reachability_check` treats a CLI-ONLY module as a dead-end
root and cannot see the call inside one; the declaration is the honest exit, not a claim
that nothing calls this.

`before.png` is the frame we SENT to an image model, `after.png` is what came back, and
the mask/sidecar pair is `id_mask.py`'s output for `before`. Exit 0 = every checkable
object HELD; exit 1 = at least one DRIFTed; exit 2 = the comparison could not be made.

WHY THIS EXISTS (2026-08-09). The Rebelway lane's one useful move is: let a crude 3D
proxy own placement, scale and orientation, and let an instruction-edit model resolve only
the SURFACE. That is admissible under R9 — the position is still derived from a contact in
Blender, nothing is typed — but ONLY if the model actually keeps its hands off the
geometry. It is free to not. An edit model asked for "the same room, photoreal" will
happily slide a bed 3 % to improve its own composition, and R10 already told us why we
would not catch it by eye: flat clay gives every mass the same standing, so a mass that
moved looks exactly like a mass that did not.

WHY NOT PER-OBJECT IoU, WHICH IS WHAT WAS FIRST PROMISED. IoU needs the object's
silhouette in BOTH frames. We have it exactly in `before` (the renderer drew it) and not
at all in `after` — the model returns pixels, not objects, and recovering silhouettes from
them needs a segmentation model, i.e. a second guessing machine to check the first one.
So this measures the thing that IS measurable: for every pixel on an object's silhouette,
HOW FAR AWAY IS THE NEAREST IMAGE EDGE IN THE RETURNED FRAME. Geometry held in place ⇒
the edge is still under the silhouette (≈0 px). Geometry moved ⇒ the silhouette now lies
on flat surface and the nearest edge is wherever the object went.

READ THE VERDICT ONE-SIDEDLY, WHICH IS THE HONEST WAY: a large drift PROVES movement; a
small drift does NOT prove stillness, because a coincidental edge (a new texture seam, a
shadow line) can sit under an old silhouette. This is a tripwire, not a certificate — and
naming that here is cheaper than rediscovering it as a flattering scorer for the tenth
time.

THREE FAILURE MODES OF THIS PROBE, EACH ANSWERED BY CONSTRUCTION RATHER THAN BY A TUNED
CONSTANT — the repo's own history is that a threshold chosen to silence false positives
also silences the real one (R9b, round 16):

  1. AN OBJECT WHOSE SILHOUETTE WAS NEVER VISIBLE. R10's white-box-next-to-a-white-box:
     the mask knows the boundary is there, the picture never showed it. Measuring drift on
     it reports movement that no edit performed. So every object is measured against the
     BEFORE frame first, and one whose own silhouette carries no edge in the frame we sent
     is reported UNCHECKABLE — never PASS. An object this probe cannot see is a finding
     about the probe's coverage, not a clean bill for the object.
  2. A RETURNED FRAME THAT IS SIMPLY BUSIER. More edges everywhere ⇒ every silhouette
     finds one nearby ⇒ the test gets easier exactly when the model rewrote the most. The
     edge threshold is therefore derived from the BEFORE frame and applied UNCHANGED to
     both, and the after/before edge-density RATIO is printed on every run. A ratio far
     from 1 means this probe just got easier and the reader must know it.
  3. A RETURNED FRAME THAT IS NOT THE SAME PICTURE. Models re-crop and re-aspect silently.
     A differently-cropped frame makes every number here meaningless while producing
     numbers, so an aspect-ratio mismatch over ASPECT_TOL RAISES. Scaling alone is fine
     and is recorded; recropping is not fine and is refused.

TOLERANCE is expressed as a fraction of the frame DIAGONAL, not in pixels, so the same
verdict survives a resize: TOL_PCT_DIAG = 0.25 % ≈ 6 px on this lane's 2000x1400 frames.
That is a DETECTION FLOOR, not a quality claim — it is roughly a 0.5 % linear error on a
large object, and the defect that started all of this (R7b's figure at 0.65x the target's
area) was ~20 % linear. Nothing here says an object inside the floor is correctly placed;
it says this instrument did not catch it moving.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import value_probe as _vp                    # palette codec — ONE definition, both halves

TOL_PCT_DIAG = 0.25       # % of the frame diagonal a silhouette may sit from an edge
ASPECT_TOL = 0.01         # 1 % — beyond this the returned frame is a different picture
EDGE_PCTILE = 90.0        # "an edge" = the top decile of BEFORE's gradient magnitude …
EDGE_ABS_FLOOR = 8.0      # … but never below a real step. See THE FLOOR below.
MIN_BOUNDARY_PX = 60      # below this an object's visible outline is too short to rank
BASE_MISS_MAX = 0.50      # >half the outline invisible in the SENT frame ⇒ UNCHECKABLE
LOST_TOL = 0.15           # share of outline whose edge the EDIT erased ⇒ DRIFT

# THE FLOOR, and it is not a taste constant. A percentile alone has a failure mode this
# probe hit on its own first test run: on a frame flatter than the percentile (a clay
# blockout, a fog pass), the 90th percentile of gradient magnitude is 0.0, `grad >= 0.0`
# marks EVERY pixel an edge, every silhouette finds one at distance 0, and the report
# comes back HELD for everything including objects that moved across the frame. A probe
# whose answer on a featureless frame is "all clear" is the flattering-scorer shape again.
# Sobel on 8-bit luma gives ≈4 per one-level step, so 8.0 is a two-level step — below that
# an "edge" is quantisation, not structure. When the floor binds, the report says so.

# WHY THE VERDICT IS A SHARE OF THE OUTLINE AND NOT A MEDIAN DISTANCE. Also earned on the
# first run: translate a box 8 px along x and its top and bottom runs still overlap the
# moved box's top and bottom runs, so most boundary pixels still sit on an edge and the
# MEDIAN distance stays ~0 — HELD, for a mass that plainly moved. Interiors are made of
# long straight runs, so this is the common case, not a corner. The honest question is
# what FRACTION of an object's outline lost its edge: that box loses its two vertical runs
# = 2·80/400 = 40 % of its perimeter, and any real object moving off-axis loses more.
# LOST_TOL = 0.15 sits well under the smallest interesting case and well over pixel noise.


class DriftError(ValueError):
    """A comparison that cannot be made. Raised, never warned — see value_probe.ProbeError:
    a drift number computed across two different pictures reads exactly like evidence."""


# --------------------------------------------------------------------------- pure pieces

def gradient_magnitude(lum):
    """Sobel magnitude of a 2-D luma array. Plain numpy: scipy is used below for the
    distance transform, but a 3x3 convolution does not need a dependency to be correct."""
    import numpy as np
    a = np.pad(lum.astype(np.float32), 1, mode="edge")
    gx = (a[:-2, 2:] + 2 * a[1:-1, 2:] + a[2:, 2:]) - (a[:-2, :-2] + 2 * a[1:-1, :-2] + a[2:, :-2])
    gy = (a[2:, :-2] + 2 * a[2:, 1:-1] + a[2:, 2:]) - (a[:-2, :-2] + 2 * a[:-2, 1:-1] + a[:-2, 2:])
    return np.hypot(gx, gy)


def luma_of(rgb):
    """Rec.709 luma of an HxWx3 array — the same weights value_probe.luma uses on scalars."""
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def boundary_mask(ids, oid, drop_frame_border=True):
    """Pixels of object `oid` that touch a DIFFERENT id — its silhouette, one pixel wide.

    The frame border is dropped by default: an object the camera cuts off has a boundary
    there that no edge in any render will ever sit under, so counting it would charge the
    model for the crop.
    """
    import numpy as np
    sel = ids == oid
    if not sel.any():
        return np.zeros_like(sel)
    nb = np.zeros_like(sel)
    nb[1:, :] |= sel[1:, :] & ~sel[:-1, :]
    nb[:-1, :] |= sel[:-1, :] & ~sel[1:, :]
    nb[:, 1:] |= sel[:, 1:] & ~sel[:, :-1]
    nb[:, :-1] |= sel[:, :-1] & ~sel[:, 1:]
    if drop_frame_border:
        nb[0, :] = nb[-1, :] = False
        nb[:, 0] = nb[:, -1] = False
    return nb


def distance_to_edges(edges):
    """Per-pixel distance to the nearest True in `edges` (exact Euclidean, scipy EDT)."""
    import numpy as np
    from scipy import ndimage
    if not edges.any():
        # No edges at all: every distance is "infinite". Say so as a number the caller
        # can print rather than as a nan that silently sorts first.
        return np.full(edges.shape, float(np.hypot(*edges.shape)), dtype=np.float32)
    return ndimage.distance_transform_edt(~edges).astype(np.float32)


def verdict_for(base_miss, after_miss, base_max=BASE_MISS_MAX, lost_tol=LOST_TOL):
    """One object's verdict from the share of its outline that carries no edge, before and
    after. Pure, so the table and the tests agree on the same three words.

    UNCHECKABLE comes FIRST and is not a pass: if the outline had no edge under it in the
    frame we SENT, this probe never had a signal to lose. And the charge is the INCREASE,
    so a partly-hidden object is judged only on the part that was visible.
    """
    if base_miss > base_max:
        return "UNCHECKABLE"
    return "DRIFT" if (after_miss - base_miss) > lost_tol else "HELD"


# --------------------------------------------------------------------------- the real path

def compare(before_rgb, after_rgb, mask_rgb, names,
            tol_pct=TOL_PCT_DIAG, edge_pctile=EDGE_PCTILE, min_boundary=MIN_BOUNDARY_PX):
    """All three frames already the SAME HxW. Returns (rows, summary)."""
    import numpy as np

    h, w = mask_rgb.shape[:2]
    tol_px = (tol_pct / 100.0) * float(np.hypot(w, h))

    g_before = gradient_magnitude(luma_of(before_rgb))
    g_after = gradient_magnitude(luma_of(after_rgb))
    # ONE threshold, taken from the frame we sent, applied to both. See failure mode 2.
    pct = float(np.percentile(g_before, edge_pctile))
    thr = max(pct, EDGE_ABS_FLOOR)
    e_before, e_after = g_before >= thr, g_after >= thr

    d_before, d_after = distance_to_edges(e_before), distance_to_edges(e_after)
    ids = _vp.decode_ids(mask_rgb)

    rows = []
    for k, name in names.items():
        nb = boundary_mask(ids, int(k))
        n = int(nb.sum())
        if n < min_boundary:
            rows.append({"name": name, "id": int(k), "boundary_px": n, "base_miss": None,
                         "after_miss": None, "after_p95": None, "verdict": "NO-OUTLINE"})
            continue
        base_miss = float((d_before[nb] > tol_px).mean())
        after = d_after[nb]
        after_miss = float((after > tol_px).mean())
        rows.append({
            "name": name, "id": int(k), "boundary_px": n,
            "base_miss": base_miss, "after_miss": after_miss,
            "lost": after_miss - base_miss,
            "after_p95": float(np.percentile(after, 95)),
            "verdict": verdict_for(base_miss, after_miss),
        })
    rows.sort(key=lambda r: (r["verdict"] != "DRIFT", -(r.get("lost") or 0)))

    # REVERSE DIRECTION: structure in the returned frame that was in NO before-edge's
    # neighbourhood — i.e. something the model ADDED. R10's question ("what is this object
    # doing here") asked of a frame we did not build.
    invented = float((d_before[e_after] > tol_px).mean()) if e_after.any() else 0.0
    summary = {
        "frame": [w, h], "tol_px": tol_px, "tol_pct_diag": tol_pct,
        "lost_tol": LOST_TOL, "base_miss_max": BASE_MISS_MAX,
        "edge_threshold": thr, "edge_pctile": edge_pctile,
        "edge_threshold_from": "floor" if thr > pct else "percentile",
        "edge_density_before": float(e_before.mean()),
        "edge_density_after": float(e_after.mean()),
        "edge_density_ratio": float(e_after.mean() / e_before.mean()) if e_before.any() else None,
        "invented_edge_share": invented,
        "counts": {v: sum(1 for r in rows if r["verdict"] == v)
                   for v in ("DRIFT", "HELD", "UNCHECKABLE", "NO-OUTLINE")},
    }
    return rows, summary


def report(rows, summary):
    s = summary
    out = [
        f"frame {s['frame'][0]}x{s['frame'][1]}  tolerance {s['tol_px']:.1f} px "
        f"({s['tol_pct_diag']:.2f}% diag)  DRIFT when the edit erases the edge under "
        f">{100*s['lost_tol']:.0f}% of an outline",
        f"edge>={s['edge_threshold']:.1f} (from the {s['edge_threshold_from']}"
        + ("; the SENT frame is flatter than p"
           f"{s['edge_pctile']:.0f} — little structure to check" if s["edge_threshold_from"] == "floor" else "")
        + ")",
        f"edge density  before {100*s['edge_density_before']:.2f}%  after "
        f"{100*s['edge_density_after']:.2f}%  ratio "
        + (f"{s['edge_density_ratio']:.2f}" if s["edge_density_ratio"] else "-")
        + ("   <-- the returned frame is busier: this test got EASIER"
           if (s["edge_density_ratio"] or 1) > 1.25 else ""),
        f"structure the model ADDED (after-edges far from any before-edge): "
        f"{100*s['invented_edge_share']:.1f}% of its edge pixels",
        "",
        f"{'object':30s} {'outline':>8s} {'was':>6s} {'now':>6s} {'lost':>6s} {'p95px':>7s}  verdict",
    ]
    for r in rows:
        pc = lambda v: f"{100*v:5.0f}%" if v is not None else "     -"   # noqa: E731
        px = f"{r['after_p95']:7.1f}" if r["after_p95"] is not None else "      -"
        out.append(f"{r['name']:30s} {r['boundary_px']:8d} {pc(r['base_miss'])} "
                   f"{pc(r['after_miss'])} {pc(r.get('lost'))} {px}  {r['verdict']}")
    c = s["counts"]
    out += ["", f"DRIFT {c['DRIFT']}  ·  HELD {c['HELD']}  ·  UNCHECKABLE "
                f"{c['UNCHECKABLE']}  ·  NO-OUTLINE {c['NO-OUTLINE']}"]
    if c["DRIFT"] == 0 and c["HELD"] == 0:
        out.append("NOTHING WAS CHECKED — every object was uncheckable or had no outline. "
                   "That is a verdict about this probe, not about the edit.")
    return "\n".join(out)


def _load(path, want_shape=None, label=""):
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if want_shape and (im.height, im.width) != want_shape:
        ah, aw = want_shape
        if abs((im.width / im.height) - (aw / ah)) > ASPECT_TOL * (aw / ah):
            raise DriftError(
                f"{label} is {im.width}x{im.height} but the mask frame is {aw}x{ah} — the "
                f"aspect ratios differ by more than {100*ASPECT_TOL:.0f}%. The model "
                f"returned a DIFFERENT CROP, so no silhouette in the mask names the same "
                f"place in it. Refusing: this probe would still print numbers")
        print(f"note: {label} {im.width}x{im.height} -> {aw}x{ah} "
              f"(scale {aw/im.width:.3f}, aspect preserved)")
        im = im.resize((aw, ah), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


def _main(argv):
    if len(argv) < 5:
        print("edge_drift: usage  <before.png> <after.png> <mask.png> <mask.json>\n"
              "  before = the frame SENT to the model; after = what it returned;\n"
              "  mask/json = id_mask.py output for BEFORE (alignment is the contract).")
        return 2
    before_p, after_p, mask_p, json_p = argv[1:5]
    side = json.load(open(json_p, encoding="utf-8"))
    names = {int(k): v for k, v in (side.get("ids") or {}).items()}
    if not names:
        raise DriftError(f"{json_p}: no `ids` block — re-run id_mask.py")

    mask = _load(mask_p, label="mask")
    shape = mask.shape[:2]
    before = _load(before_p, label="before")
    if before.shape[:2] != shape:
        raise DriftError(f"before {before.shape[:2]} != mask {shape} — the mask is only "
                         f"honest about the frame it was rendered with")
    # SAME PROVENANCE CHECK AS value_probe: equal size is not equal camera.
    b_stem = os.path.splitext(os.path.basename(before_p))[0]
    src = side.get("source") or {}
    if src.get("blend") and src["blend"] != b_stem:
        raise DriftError(f"MASK/BEFORE MISMATCH: mask rendered from {src['blend']!r}, "
                         f"before frame is {b_stem!r}")
    after = _load(after_p, want_shape=shape, label="after")

    rows, summary = compare(before, after, mask, names)
    print(report(rows, summary))
    out = os.path.splitext(after_p)[0] + ".edgedrift.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"before": before_p, "after": after_p, "mask": mask_p,
                   "summary": summary, "objects": rows}, fh, indent=1)
    print(f"\n-> {out}")
    return 1 if summary["counts"]["DRIFT"] else 0


if __name__ == "__main__":                       # pragma: no cover
    try:
        sys.exit(_main(sys.argv))
    except DriftError as e:
        print(f"EDGE DRIFT REFUSED: {e}")
        sys.exit(2)
