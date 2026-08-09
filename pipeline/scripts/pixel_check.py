#!/usr/bin/env python3
"""pixel_check.py — the first gate rung in this repo that OPENS THE PICTURE.

    python pipeline/scripts/pixel_check.py --spec <spec.json> --render <ours.png>
                                            --target <target.jpg> [--soft]

OWNER ORDER 2026-08-09: *"ผมขอบังคับให้ทุกกลไก ทุกขั้นตอนต้องมองรูปจริง"* — after
he looked at r38b and said *"ในสายตาผมมันยังไม่ใกล้กับคำว่าเสร็จเลย"* on the very
day all three of the lane's closing conditions first held at once.

THE COUNT THAT MAKES HIM RIGHT, measured before writing a line of this file:

    modules the render gate calls               8
    ...of those that ever open an image         0
    instruments in pipeline/scripts that DO     21
    ...of those any gate module calls           0

Every rung deciding whether a frame ships was reading DECLARATIONS ABOUT the
picture — prov tags, a manifest of ids, a markdown item count, a directory
listing, AABBs of the built scene. All of them can go green while the frame gets
worse, and on 2026-08-09 all of them did, on a frame four independent critics read
as a room with no headboard, no styling, flat light and cloth like plastic.

The sharpest instance is in the spec itself: `judge_lines` says in its own words
*"held out of every derivation above; the build is scored against them (rule: a
metric that can fail)"* — and it names six features, stores no values for any of
them, and has ZERO consumers in the repo. A held-out scoring set with no data and
no reader.

WHAT THIS CHECKS, AND WHAT IT CANNOT
------------------------------------
A `pixel_claims` row names an image feature the round says it fixed, carries the
TARGET's fit of that feature, and this module re-measures the SAME feature in BOTH
images with ONE estimator and compares. Four ways it fails, and each is a defect
this lane has actually shipped:

  1. SELF-CHECK FIRST. The stored target fit is re-derived from the target file.
     If it no longer reproduces, the claim's numbers stopped describing the file
     and everything downstream is arithmetic about nothing. Fails closed.
  2. IS THE FEATURE IN OUR FRAME AT ALL? Contrast below a fraction of the
     target's own contrast means we are fitting noise. This is the positive
     control an absence test needs — earned at r38, where "no step at u=989" was
     quoted as proof until a same-class corner that certainly exists scored the
     same 3.5 L.
  3. IS IT STILL A LINE? Our rms above a multiple of the target's means the
     pixels there are not one edge.
  4. IS IT IN THE RIGHT PLACE? |ours - target| at the middle of the range,
     against the row's own tolerance.

WHAT IT CANNOT SEE, said before anyone trusts it: **it checks the features
someone CLAIMED.** A defect nobody wrote a claim for is invisible to it, exactly
as an unwritten contact was invisible before `contact_check`. That hole is
reported, not hidden: `unclaimed()` counts the masses with no pixel claim at all,
and on the day this shipped that number was almost all of them. This rung makes
the gate open the picture; it does not yet make the gate SEE the picture, and the
difference is the whole remaining work.

It also cannot judge beauty, styling, light quality or believability. Those are
the critic rungs (R7/R7b/R7c) and the owner's eye (R3), and this does not replace
either — it stops the DECLARATIVE half of the gate from passing a frame whose own
claimed features have moved.
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                       # noqa: BLE001
    pass

# A claim's stored target fit must still describe the target file. Half a pixel
# is below what any estimator disagreement in this lane has produced and well
# above float noise.
SELF_TOL_PX = 0.5
# Our feature must carry at least this fraction of the target's own contrast, or
# we are fitting noise and calling it a measurement.
MIN_CONTRAST_RATIO = 0.25
# ...and still be a line: our rms may not exceed this multiple of the target's.
MAX_RMS_RATIO = 4.0


def _luma(path):
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def _peak(profile, base, seed, half):
    """Sub-pixel location of the strongest step within +-half of `seed`.

    Gradient magnitude, parabolic interpolation on the peak — the same estimator
    on both images, which is the only thing that makes the comparison mean
    anything. Returns (position, contrast) or None.
    """
    import numpy as np
    g = np.abs(np.diff(profile))
    lo, hi = int(seed - half) - base, int(seed + half) - base
    lo, hi = max(1, lo), min(len(g) - 1, hi)
    if hi <= lo:
        return None
    k = lo + int(np.argmax(g[lo:hi]))
    y0, y1, y2 = g[k - 1], g[k], g[k + 1]
    den = y0 - 2 * y1 + y2
    d = (y0 - y2) / (2 * den) if den else 0.0
    return base + k + 0.5 + d, float(y1)


def fit_feature(L, claim, seed_line, search_px):
    """(slope, intercept, rms, n, contrast) of `claim`'s feature in image L.

    `seed_line` is the line to search around — the TARGET's fit, so both images
    are searched in the same place and a feature that has MOVED shows up as a
    move rather than as two independently-found features.
    """
    import numpy as np
    kind = claim.get("kind", "v_edge")
    lo, hi = claim["along"]
    step = int(claim.get("step", 1))
    pts, amps = [], []
    for t in range(int(lo), int(hi) + 1, step):
        seed = seed_line[0] * t + seed_line[1]
        base = max(0, int(seed - search_px) - 2)
        if kind == "v_edge":                       # u varies with v: scan a row
            if not (0 <= t < L.shape[0]):
                continue
            prof = L[t, base:int(seed + search_px) + 3]
        else:                                      # h_edge: v varies with u
            if not (0 <= t < L.shape[1]):
                continue
            prof = L[base:int(seed + search_px) + 3, t]
        if len(prof) < 5:
            continue
        r = _peak(prof, base, seed, search_px)
        if r is None:
            continue
        pts.append((t, r[0]))
        amps.append(r[1])
    if len(pts) < 5:
        return None
    x = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    A = np.vstack([x, np.ones_like(x)]).T
    m, b = np.linalg.lstsq(A, y, rcond=None)[0]
    rms = float(np.sqrt(((A @ [m, b] - y) ** 2).mean()))
    return float(m), float(b), rms, len(pts), float(np.mean(amps))


class NotComparable(Exception):
    """The frame cannot be compared to the reference at all — a DIFFERENT answer
    from 'the claims hold'.

    Earned immediately: the first build to call this rung was an R5 playblast at
    540x410 against a 1080x821 reference, and every claim's column simply does not
    exist in a half-width frame. Rescaling was the tempting fix and is wrong — a
    sub-pixel comparison at half resolution is a different measurement, and R5
    already says only full fidelity closes a gate. So the rung refuses, LOUDLY,
    and the caller decides. What it must never do is return [] and let 'could not
    look' read as 'looked and it was fine'."""


def _same_size(a, b):
    from PIL import Image
    return Image.open(a).size == Image.open(b).size


def check(spec, render_path, target_path):
    """[violation str] — every pixel claim that our frame does not honour.

    Raises NotComparable when the frame is not the reference's size."""
    claims = spec.get("pixel_claims")
    if not claims:
        return []
    if not isinstance(claims, list):
        return ["`pixel_claims` is present but is not a list."]
    for p in (render_path, target_path):
        if not p or not os.path.isfile(p):
            return [f"pixel_check cannot open {p!r} — a rung that cannot read "
                    f"the picture must not report that it looked."]
    if not _same_size(render_path, target_path):
        from PIL import Image
        raise NotComparable(
            f"{os.path.basename(render_path)} is "
            f"{Image.open(render_path).size} against a reference of "
            f"{Image.open(target_path).size}. Every claim is written in the "
            f"reference's pixels; at another size they are not the same "
            f"measurement. Run the claims on the FULL-FIDELITY frame (R5).")
    LO, LT = _luma(render_path), _luma(target_path)
    out = []
    for n, c in enumerate(claims):
        name = c.get("name", f"pixel_claims[{n}]")
        if not isinstance(c, dict) or "target" not in c or "along" not in c:
            out.append(f"{name}: malformed claim (needs `along` and `target`).")
            continue
        tgt = c["target"]
        seed = (float(tgt["slope"]), float(tgt["intercept"]))
        search = float(c.get("search_px", 25))
        mid = (float(c["along"][0]) + float(c["along"][1])) / 2.0
        tf = fit_feature(LT, c, seed, search_px=6.0)
        if tf is None:
            out.append(f"{name}: the TARGET's own feature could not be refitted "
                       f"— the claim's numbers no longer describe the file.")
            continue
        t_at = tf[0] * mid + tf[1]
        stored_at = seed[0] * mid + seed[1]
        if abs(t_at - stored_at) > SELF_TOL_PX:
            out.append(
                f"{name}: SELF-CHECK FAILED. The stored target fit puts this "
                f"feature at {stored_at:.2f} px and refitting the target file "
                f"puts it at {t_at:.2f} ({t_at - stored_at:+.2f}). The claim is "
                f"arithmetic about a file that has changed.")
            continue
        of = fit_feature(LO, c, seed, search_px=search)
        if of is None:
            out.append(f"{name}: no feature found in OUR frame within "
                       f"+/-{search:.0f} px of the target's line.")
            continue
        o_at = of[0] * mid + of[1]
        ratio = of[4] / tf[4] if tf[4] else 0.0
        if ratio < MIN_CONTRAST_RATIO:
            out.append(
                f"{name}: our frame carries {of[4]:.1f} L of contrast where the "
                f"target carries {tf[4]:.1f} ({ratio:.2f}x, floor "
                f"{MIN_CONTRAST_RATIO}). The feature this claim names is not in "
                f"our frame; the position below would be a fit to noise.")
            continue
        if of[2] > MAX_RMS_RATIO * max(tf[2], 0.05):
            out.append(
                f"{name}: our fit's rms is {of[2]:.2f} px against the target's "
                f"{tf[2]:.2f} — the pixels there are not one edge.")
            continue
        tol = float(c.get("tol_px", 2.0))
        if abs(o_at - t_at) > tol:
            out.append(
                f"{name}: ours sits at {o_at:.2f} px, the target at {t_at:.2f} "
                f"({o_at - t_at:+.2f} px, tolerance {tol}). "
                f"{c.get('why', '')}".rstrip())
    return out


def report(spec, render_path, target_path):
    """[(name, ours, target, delta, contrast_ratio, rms)] — the numbers, pass or
    fail. A gate that only speaks when it fails teaches nobody what it measures."""
    rows = []
    claims = spec.get("pixel_claims") or []
    if not claims or not (render_path and os.path.isfile(render_path)):
        return rows
    if not _same_size(render_path, target_path):
        return rows
    LO, LT = _luma(render_path), _luma(target_path)
    for c in claims:
        seed = (float(c["target"]["slope"]), float(c["target"]["intercept"]))
        mid = (float(c["along"][0]) + float(c["along"][1])) / 2.0
        tf = fit_feature(LT, c, seed, 6.0)
        of = fit_feature(LO, c, seed, float(c.get("search_px", 25)))
        if not tf or not of:
            rows.append((c.get("name", "?"), None, None, None, None, None))
            continue
        rows.append((c.get("name", "?"), of[0] * mid + of[1], tf[0] * mid + tf[1],
                     (of[0] * mid + of[1]) - (tf[0] * mid + tf[1]),
                     of[4] / tf[4] if tf[4] else 0.0, of[2]))
    return rows


def unclaimed(spec):
    """[note] — ADVISORY, one line: how much of the frame no pixel claim covers.

    The honest counterweight to this module. It checks what was claimed, so the
    number that matters is how much was not."""
    masses = [m for m in spec.get("masses", []) if m.get("name")]
    if not masses:
        return []
    claimed = {c.get("mass") for c in (spec.get("pixel_claims") or [])
               if isinstance(c, dict)}
    claimed.discard(None)
    return [f"{len(masses) - len(claimed)} of {len(masses)} masses carry no pixel "
            f"claim — this rung opens the picture, it does not yet SEE it."]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--soft", action="store_true")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    # EXIT CODES ARE A CONTRACT, and the third one is the point of having them:
    #   0 = the claims hold      1 = a claim is broken      2 = COULD NOT RUN
    # A caller that cannot tell 2 from 0 will eventually read "not run" as
    # "passed", which is the mute this whole rung exists to end.
    try:
        v = check(spec, a.render, a.target)
    except NotComparable as e:
        print(f"PIXEL GATE: NOT RUN — {e}")
        sys.exit(0 if a.soft else 2)
    rows = report(spec, a.render, a.target)
    if rows:
        print("PIXEL CHECK — our frame vs the target, one estimator on both:")
        for name, o, t, d, cr, rms in rows:
            if o is None:
                print(f"  {name:34s} NOT MEASURABLE")
            else:
                print(f"  {name:34s} ours {o:8.2f}  target {t:8.2f}  "
                      f"{d:+6.2f} px   contrast {cr:4.2f}x   rms {rms:4.2f}")
    for s in unclaimed(spec):
        print(f"~~ {s}")
    if v:
        print(f"\nPIXEL CHECK: {len(v)} violation(s)")
        for s in v:
            print(f"  !! {s}")
    else:
        print(f"PIXEL CHECK: {len(spec.get('pixel_claims') or [])} claim(s) hold")
    sys.exit(0 if a.soft else (1 if v else 0))


if __name__ == "__main__":
    main()
