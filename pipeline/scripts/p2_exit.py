"""p2_exit.py — the P2 reopened-bar exit harness (plan item P2r-7).

WHY A COMMAND AND NOT A RITUAL: the r7 exit measured two crops whose frames
lived in a session scratchpad; the method survived only because the gate
artifact happened to copy it out by hand. A bar that lives in a scratchpad
drifts back to two pre-chosen spots the next time someone is tired. This file
IS the bar: every 100% crop of P2's reopened exit test, with its box, its
method and its anchor DECLARED here, so closing P2 is one command anyone can
re-run.

BOXES ARE FROZEN BEFORE THE FRAMES THEY JUDGE. The duvet/wood/rug boxes were
declared 2026-08-11 from the p3r2 frame, before the p2r8 frame existed
(instrument-before-build, the program's own law). The throw box is the r7
record verbatim (gate-DELIV001-P2r7). Moving a box is a recorded decision,
never a convenience — that is exactly the drift this command exists to stop.

LOCAL-ONLY (R10b): the anchor is the friend's DELIVERED CLIENT WORK. The hard
line is git — anchor-side crops and ours-beside-anchor composites are written
under _private/deliv-001/p2-exit/ (gitignored) and never enter a commit or a
critique bundle. Only OUR-side crops land in the project stage dir. Sending an
anchor to an external vendor stays off by default (a judge shown the answer
stops being a judge).

EXIT CODES ARE A CONTRACT (R11): 0 = every rung ran and every DECLARED cut
holds · 1 = a declared cut is broken · 2 = COULD NOT RUN (missing file, a _ql
playblast, a scene dump without aabb) — and "could not look" must never print
like "looked and it was fine". Rungs whose bar is judged-beside-anchor (the
two energy crops) print their numbers and archive their crops; they cut
nothing here because the reopened bar cuts them at the critic clause, not at
a number. The rug edge graduated from that list at P2r-3: its cut is declared
on the crop registry with its grounding.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deliverable_check as dc  # noqa: E402  — pure (no bpy); _octave_energy + LE1600 normalise

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGE_DIR = os.path.join(REPO, "projects", "PRJ-2026-002_c001-house",
                         "04_visualization", "p2-exit-crops")
PRIVATE_DIR = os.path.join(REPO, "_private", "deliv-001", "p2-exit")

# The one delivered-bedroom anchor this suite reads (I-23-023 #499473 — the
# same image the throw was judged against at r7 and the bed rank dimensions
# derive from). Repo-relative so the registry survives a checkout move.
ANCHOR_BEDROOM = os.path.join(
    REPO, "_private", "discord", "MY-DATA-PEAT", "โปรเจ็ก",
    "002_I-23-023-คุณแอ้ม", "files", "499473_Bedroom_1_main.png")

# name -> dict. Boxes are (x0, y0, x1, y1) fractions of the LONG-EDGE-1600
# normalised image (deliverable_check's own normalise rule: resolution must
# not buy detail — ours 2400 and the anchor's 3840 meet at the same 1600).
CROPS = {
    "duvet_fold": {
        "kind": "octave_energy",
        "asks": "fold-structure energy of the duvet beside the delivered comforter",
        "ours_box": (0.70, 0.55, 0.955, 0.73),   # right-flank drape, textile-only
        "anchor": ANCHOR_BEDROOM,
        "anchor_box": (0.30, 0.83, 0.52, 0.99),  # foreground comforter with loft
        "declared": "2026-08-11 from the p3r2 frame, before p2r8 existed",
    },
    "throw_weave": {
        "kind": "octave_energy",
        "asks": "weave detail energy of the foot-of-bed throw (r7 exit crop, kept as trend)",
        "ours_box": (0.45, 0.52, 0.68, 0.68),    # r7 record verbatim
        "anchor": ANCHOR_BEDROOM,
        "anchor_box": (0.30, 0.80, 0.47, 0.95),  # r7 record verbatim
        "declared": "r7 (gate-DELIV001-P2r7) — 1.126x at close",
        # p2r29 (pre-registered at r27, opened at r28's third drift): the r7 box
        # is FROZEN IN FRAME SPACE while the cloth under it re-bakes downstream
        # of every duvet change — a dead box measures composition drift, not
        # weave. The mask half scopes the SAME band-energy to the throw's own
        # rendered pixels (matmask id), eroded by the band's outer radius so
        # neighbours cannot bleed into the blur. Both halves print: the box
        # stays as the r7 trend line, the mask answers whether the cloth or
        # the crop moved.
        "mask_material": "bed_throw",
    },
    "wood_boards": {
        "kind": "autocorr",
        "asks": "two adjacent veneer panels: no periodic figure repeat above the noise floor",
        "ours_box": (0.24, 0.03, 0.46, 0.20),    # two bay back-panels, no contents
        "declared": "2026-08-11 from the p3r2 frame (C3#2 tiling = positive control)",
    },
    "rug_edge": {
        "kind": "edge_profile",
        "asks": "rug boundary reads as a rolled-over edge, not a 90-degree step",
        "ours_box": (0.06, 0.82, 0.32, 0.99),    # binding + floor, bottom-left
        "declared": "2026-08-11 from the p3r2 frame",
        # CUT DECLARED at P2r-3 (was report-only): an ideal step reads 0-1 px by
        # this rung's own first-crossing rule and a resample-sharp real step
        # 1-2 px (edge_rise_width docstring), so >= 3.0 px sits strictly above
        # the whole step band. Grounded before the cut went live: the frame it
        # judges read 5.0 px two consecutive rounds (p2r14/p2r15).
        "cut_rise_px": 3.0,
    },
    "garment_shells": {
        "kind": "dup_shells",
        "asks": "coincident duplicate garment shells in the built scene == 0",
        "declared": "2026-08-11 (p3r2 .blend probe found acq0==acq10 class pairs)",
    },
}


def _norm_img(path):
    return dc._norm(dc._load(path))


def _crop(im, box):
    w, h = im.size
    return im.crop((round(box[0] * w), round(box[1] * h),
                    round(box[2] * w), round(box[3] * h)))


def _lum_arr(im):
    return dc._lum(np.asarray(im, dtype=np.float64))


# ---------------------------------------------------------------- rungs

def _erode(mask, r):
    """Binary erosion by r px via iterated 4-neighbour min — no scipy."""
    m = mask.copy()
    for _ in range(int(r)):
        p = np.pad(m, 1, mode="constant", constant_values=False)
        m = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1]
             & p[1:-1, :-2] & p[1:-1, 2:])
    return m


def rung_octave_mask(ours_im, render_path, spec, lo=4, hi=32):
    """The mask half of an octave rung: same band, same 3-pass blur, but the
    mean runs over the named material's OWN rendered pixels (matmask id),
    eroded by hi//2 so the box blur cannot pull neighbouring materials into
    the band. Returns (res, why_not) — exactly one is None."""
    base = render_path.rsplit(".", 1)[0]
    mj, mp = base + ".matmask.json", base + ".matmask.png"
    if not (os.path.exists(mj) and os.path.exists(mp)):
        return None, "no matmask beside the render"
    meta = json.load(open(mj, encoding="utf-8"))
    wanted = spec["mask_material"]
    mid = next((int(k) for k, v in meta.get("ids", {}).items() if v == wanted),
               None)
    if mid is None:
        return None, f"material {wanted!r} not in matmask ids"
    # the mask png stores ids as value_probe's sRGB palette triples (levels of
    # 51), never raw indices — decode first, or every lookup reads channel
    # noise as "zero pixels"
    import value_probe as _vp
    ids = _vp.decode_ids(np.asarray(Image.open(mp).convert("RGB")))
    mask_full = ids == mid
    if not mask_full.any():
        return None, f"{wanted!r} has zero pixels in the mask"
    # to LE1600 (the same normalise rule as the luminance), NEAREST — an id is
    # a label, interpolating one invents materials
    w, h = ours_im.size
    mask = np.asarray(Image.fromarray(mask_full.astype(np.uint8) * 255)
                      .resize((w, h), Image.NEAREST)) > 127
    core = _erode(mask, hi // 2)
    if core.sum() < 2000:
        return None, (f"eroded {wanted!r} core is {int(core.sum())} px — too "
                      f"thin to band-measure")
    L = _lum_arr(ours_im)
    band = np.abs(dc._blur(L, lo // 2) - dc._blur(L, hi // 2))
    e_ours = float(band[core].mean())
    anchor_c = _crop(_norm_img(spec["anchor"]), spec["anchor_box"])
    e_anchor = dc._octave_energy(_lum_arr(anchor_c))
    ys, xs = np.nonzero(mask)
    return {"ours": round(e_ours, 4), "anchor": round(e_anchor, 4),
            "ratio": round(e_ours / max(e_anchor, 1e-9), 3),
            "mask_px": int(mask.sum()), "core_px": int(core.sum()),
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            }, None


def rung_octave(ours_im, spec):
    """The r7 throw-crop method: LE1600 -> textile-only crop -> _octave_energy
    (mean |band 4-32 px|, 3-pass — the only variant that survived its own noise
    negative control). Returns (ours, anchor, ratio). Report-only: the reopened
    bar judges these crops at the critic clause, not at a number."""
    ours_c = _crop(ours_im, spec["ours_box"])
    anchor_c = _crop(_norm_img(spec["anchor"]), spec["anchor_box"])
    e_ours = dc._octave_energy(_lum_arr(ours_c))
    e_anchor = dc._octave_energy(_lum_arr(anchor_c))
    return ours_c, anchor_c, {
        "ours": round(e_ours, 4), "anchor": round(e_anchor, 4),
        "ratio": round(e_ours / max(e_anchor, 1e-9), 3),
    }


def _median_filter_1d(p, win=9):
    """Odd-window running median, edges padded by reflection. No scipy — the
    profile is a few hundred samples and a plain loop is honest and fast."""
    r = win // 2
    pad = np.concatenate([p[r:0:-1], p, p[-2:-2 - r:-1]])
    return np.array([np.median(pad[i:i + win]) for i in range(len(p))])


def autocorr_peak(L, min_lag=24, despike_win=9):
    """Max normalised autocorrelation of the DESPIKED column-mean profile at
    lag >= min_lag, plus a noise floor from shuffled surrogates.

    THE ASK IS FIGURE TILING, NOT PANEL EDGES. Two adjacent boards carrying the
    same cathedral figure repeat along x at the panel pitch — but so do the
    panel SEAMS, which are real, correct geometry. A rung that cannot tell them
    apart calls every well-built cabinet a tiling defect. The separation is
    width: a seam is a 1-3 px dark line, the figure is broad streaks — so the
    column profile is despiked with a running median before the correlation,
    which removes narrow combs and keeps broad repeats (verified both ways in
    the tests' synthetic controls).

    The verdict is peak vs the measured floor of shuffled surrogates (same
    histogram, no spatial order), not peak vs zero. Returns (peak, lag, floor)."""
    a = L - L.mean(axis=1, keepdims=True)
    p0 = a.mean(axis=0)
    W = len(p0)
    hi = W // 2
    if min_lag >= hi:
        return 0.0, 0, 0.0

    def _peak_of(raw):
        # THE SURROGATE WALKS THE SAME PIPELINE AS THE FRAME. The first version
        # despiked only the real profile and shuffled the despiked result — so
        # the median filter's own short-range smoothness counted as "structure"
        # the surrogate lacked, and pure noise read as periodic (caught by this
        # file's own noise control). Despike AFTER shuffling, normalise by the
        # surrogate's own variance, and the bias enters both sides equally.
        #
        # AND THE PEAK MUST BE A LOCAL MAXIMUM THAT ROSE FROM A VALLEY. The
        # first live run on p2r8 called the global max at exactly min_lag
        # "PERIODIC": the profile was a smooth monotonic decay (broad grain
        # correlates over tens of px — real wood, no repeat), and a global-max
        # rule reads the shoulder of that decay as a peak. A periodic figure
        # dips BETWEEN repeats and rises again at the pitch, so the rung now
        # demands rise-from-preceding-valley >= prom_min. Pinned by the
        # broad-gradient control in the tests.
        prof = _median_filter_1d(raw, despike_win)
        prof = prof - prof.mean()
        var = float((prof * prof).mean())
        if var < 1e-12:
            return 0.0, 0
        f = np.fft.rfft(prof, n=2 * W)
        ac = np.fft.irfft(f * np.conj(f))[:W] / (W - np.arange(W)) / var
        best, best_lag = 0.0, 0
        prom_min = 0.25
        for m in range(max(min_lag, 1), hi - 1):
            if not (ac[m] >= ac[m - 1] and ac[m] >= ac[m + 1]):
                continue
            rise = float(ac[m] - ac[min_lag:m + 1].min())
            if rise < prom_min:
                continue
            if float(ac[m]) > best:
                best, best_lag = float(ac[m]), m
        return best, best_lag

    peak, lag = _peak_of(p0)
    rng = np.random.default_rng(0)  # fixed seed: same frame -> same floor
    floors = [_peak_of(p0[rng.permutation(W)])[0] for _ in range(8)]
    floor = float(np.mean(floors) + 3.0 * np.std(floors))
    return peak, lag, floor


def rung_autocorr(ours_im, spec):
    c = _crop(ours_im, spec["ours_box"])
    peak, lag, floor = autocorr_peak(_lum_arr(c))
    return c, None, {"peak": round(peak, 3), "lag_px": lag,
                     "floor": round(floor, 3), "periodic": peak > floor}


def edge_rise_width(L, lo_frac=0.1, hi_frac=0.9):
    """Median 10-90% rise width (px) of the strongest vertical transition per
    column. A resample-sharp 90-degree step reads ~1-2 px; a rolled-over edge
    reads wider and asymmetric. Cut declared at P2r-3 (see the crop registry)."""
    H, W = L.shape
    widths = []
    for x in range(W):
        col = L[:, x]
        g = np.abs(np.diff(col))
        if g.max() < 4.0:          # no real edge in this column
            continue
        y = int(np.argmax(g))
        a, b = max(0, y - 12), min(H - 1, y + 13)
        seg = col[a:b]
        v0, v1 = seg[0], seg[-1]
        if abs(v1 - v0) < 8.0:
            continue
        # first-crossing 10%/90% (an ideal step crosses both at the same sample
        # and reads 0-1 px — the between-samples count read an ideal step as
        # "no transition", which is the vacuous-NaN twin of the vacuous zero)
        s = (seg - v0) / (v1 - v0)
        i_lo = int(np.argmax(s >= lo_frac))
        i_hi = int(np.argmax(s >= hi_frac))
        if s[i_lo] >= lo_frac and s[i_hi] >= hi_frac and i_hi >= i_lo:
            widths.append(i_hi - i_lo)
    return float(np.median(widths)) if widths else float("nan")


def rung_edge(ours_im, spec):
    c = _crop(ours_im, spec["ours_box"])
    w = edge_rise_width(_lum_arr(c))
    return c, None, {"rise_px_median": round(w, 2) if w == w else None}


def rung_dup_shells(scene_path):
    """Coincident duplicate shells among acquired garment/prop meshes, from the
    BUILT scene dump (never the spec — the file that renders is the file of
    record). Two records in the same item whose world AABBs agree to 0.1 mm on
    all six numbers are one mesh imported twice. CUT: count == 0."""
    with open(scene_path, encoding="utf-8") as f:
        d = json.load(f)
    objs = [o for o in d.get("objects", []) if "__acq" in o.get("name", "")]
    missing = [o["name"] for o in objs if "aabb" not in o]
    if missing:
        return None, {"could_not_run": f"scene dump has no aabb on {len(missing)} "
                      f"acquired records (pre-aabb dump) — rerun the build"}
    pairs = []
    by_item = {}
    for o in objs:
        stem = o["name"].split("__acq")[0]
        by_item.setdefault(stem, []).append(o)
    for stem, group in by_item.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = np.asarray(group[i]["aabb"], dtype=np.float64).ravel()
                b = np.asarray(group[j]["aabb"], dtype=np.float64).ravel()
                if a.shape == b.shape and np.all(np.abs(a - b) < 1e-4):
                    pairs.append((group[i]["name"], group[j]["name"]))
    return pairs, {"coincident_pairs": len(pairs)}


# ---------------------------------------------------------------- driver

def _save(im, *path):
    p = os.path.join(*path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    return os.path.relpath(p, REPO)


def _composite(ours_c, anchor_c):
    h = max(ours_c.size[1], anchor_c.size[1])
    w = ours_c.size[0] + anchor_c.size[0] + 4
    out = Image.new("RGB", (w, h), (20, 20, 20))
    out.paste(ours_c, (0, 0))
    out.paste(anchor_c, (ours_c.size[0] + 4, 0))
    return out


def run(render_path, scene_path=None, only=None, tag=None):
    base = os.path.basename(render_path)
    if base.rsplit(".", 1)[0].endswith("_ql"):
        print("P2-EXIT COULD NOT RUN: a _ql playblast is not the deliverable's "
              "size — a sub-pixel crop at half resolution is a different "
              "measurement (R5/R11). Render full fidelity first.")
        return 2
    if not os.path.exists(render_path):
        print(f"P2-EXIT COULD NOT RUN: no render at {render_path}")
        return 2
    tag = tag or base.rsplit(".", 1)[0].split("_")[-1]
    scene_path = scene_path or render_path.rsplit(".", 1)[0] + ".scene.json"
    ours_im = _norm_img(render_path)

    could_not = []
    broken = []
    keys = [only] if only else list(CROPS)
    for key in keys:
        spec = CROPS[key]
        kind = spec["kind"]
        if kind == "dup_shells":
            if not os.path.exists(scene_path):
                could_not.append((key, f"no scene dump at {scene_path}"))
                print(f"[{key}] COULD NOT RUN — no scene dump at {scene_path}")
                continue
            pairs, res = rung_dup_shells(scene_path)
            if pairs is None:
                could_not.append((key, res["could_not_run"]))
                print(f"[{key}] COULD NOT RUN — {res['could_not_run']}")
                continue
            ok = res["coincident_pairs"] == 0
            if not ok:
                broken.append(key)
            print(f"[{key}] coincident duplicate pairs = {res['coincident_pairs']} "
                  f"-> {'PASS' if ok else 'FAIL'}"
                  + ("" if ok else " " + "; ".join(f"{a}=={b}" for a, b in pairs[:6])))
            continue
        if "anchor" in spec and not os.path.exists(spec["anchor"]):
            could_not.append((key, "anchor image missing (local-only pool)"))
            print(f"[{key}] COULD NOT RUN — anchor image missing")
            continue
        if kind == "octave_energy":
            ours_c, anchor_c, res = rung_octave(ours_im, spec)
            p1 = _save(ours_c, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            _save(anchor_c, PRIVATE_DIR, tag, f"{key}-anchor-100pct.png")
            _save(_composite(ours_c, anchor_c), PRIVATE_DIR, tag,
                  f"{key}-beside-anchor.png")
            print(f"[{key}] energy ours {res['ours']} vs anchor {res['anchor']} "
                  f"-> {res['ratio']}x  (crop: {p1}; composite: _private, local-only)")
            if spec.get("mask_material"):
                mres, why = rung_octave_mask(ours_im, render_path, spec)
                if mres is None:
                    could_not.append((key, f"mask half: {why}"))
                    print(f"[{key}] MASK HALF COULD NOT RUN — {why} "
                          f"(the box number above is composition-blind trend, "
                          f"not a substitute)")
                else:
                    print(f"[{key}] mask-scoped ({spec['mask_material']}): "
                          f"energy {mres['ours']} vs anchor {mres['anchor']} "
                          f"-> {mres['ratio']}x  ({mres['core_px']} core px of "
                          f"{mres['mask_px']}, bbox {mres['bbox']})")
        elif kind == "autocorr":
            c, _, res = rung_autocorr(ours_im, spec)
            p1 = _save(c, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            verdict = "PERIODIC (cut broken)" if res["periodic"] else "no peak above floor"
            if res["periodic"]:
                broken.append(key)
            print(f"[{key}] autocorr peak {res['peak']} @ lag {res['lag_px']}px "
                  f"vs floor {res['floor']} -> {verdict}  (crop: {p1})")
        elif kind == "edge_profile":
            c, _, res = rung_edge(ours_im, spec)
            p1 = _save(c, STAGE_DIR, tag, f"{key}-ours-100pct.png")
            w = res["rise_px_median"]
            cut = spec.get("cut_rise_px")
            if w is None:
                # no measurable transition inside a box declared to hold one —
                # "could not look" must never print like "looked and it was fine"
                could_not.append((key, "no luminance transition found in the box"))
                print(f"[{key}] COULD NOT RUN — no transition in the declared box")
            elif cut is not None:
                ok = w >= cut
                if not ok:
                    broken.append(key)
                print(f"[{key}] edge 10-90% rise width median = {w} px vs cut "
                      f">= {cut} -> {'ROLLED (pass)' if ok else 'STEP (cut broken)'}"
                      f"  (crop: {p1})")
            else:
                print(f"[{key}] edge 10-90% rise width median = {w} px  "
                      f"(report-only; crop: {p1})")

    print()
    if could_not:
        print(f"P2-EXIT: {len(could_not)} rung(s) COULD NOT RUN — this is not a "
              "pass: " + "; ".join(f"{k} ({why})" for k, why in could_not))
        return 2
    if broken:
        print(f"P2-EXIT: declared cut broken on: {', '.join(broken)}")
        return 1
    print("P2-EXIT: every rung ran; declared cuts hold (energy rungs are "
          "judged beside anchors at the critic clause, not here)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("render")
    ap.add_argument("--scene", default=None)
    ap.add_argument("--only", choices=sorted(CROPS), default=None)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    sys.exit(run(args.render, scene_path=args.scene, only=args.only, tag=args.tag))


if __name__ == "__main__":
    main()
