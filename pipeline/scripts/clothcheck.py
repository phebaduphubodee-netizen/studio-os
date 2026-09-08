"""clothcheck.py — the SHRED/CRUMPLE detector for baked cloth. PURE, no bpy.

WHY THIS EXISTS (the instrument-first order, round 5 → owner verdict "ก"):
every numeric guard the bed stack owns — bbox, hem, min-motion — passed a
contained cloth explosion (fx7) and passed the round-5 shredded shirt: a wad or
a shred is numerically CLEAN on all of them. The class they cannot see is
SURFACE ROUGHNESS: healthy draped cloth is a smooth developable-ish surface —
adjacent faces are nearly coplanar, and the angles between their normals stay
small; shredded or wadded cloth flips normals violently between neighbours.
The cloth-stack contact law named face-normal variance as the candidate
instrument the day the class was discovered; this is that instrument.

The metric: over every INTERIOR edge (shared by exactly two faces), the angle
in degrees between the two face normals. Reported as a profile:
  frac_over  — fraction of interior edges whose angle exceeds SHRED_EDGE_DEG
  p95        — 95th-percentile angle
  mean       — mean angle
A piece fails when frac_over > SHRED_FRAC_MAX.

CALIBRATION (2026-07-30, measured on the real build via shred_guard="report",
not chosen from priors): healthy simmed shirts settle well under the line and
the round-5 shredded/wadded states sit far above it — see the calibration
table in LOOK-round5b (04_visualization). Thresholds are published constants
so the pure tests can pin them and a retune is a visible diff.
"""
import math

# An interior edge whose face normals disagree by more than this is a CREASE-or-WORSE.
# Real drape carries some deep creases (the duvet's fold, a sleeve's bend), so single
# hard edges are fine — failure is a POPULATION of them.
SHRED_EDGE_DEG = 60.0
# Fraction of interior edges allowed past SHRED_EDGE_DEG before the piece is ruled
# shredded/wadded. Calibrated against the round-5 states (see module docstring).
SHRED_FRAC_MAX = 0.06


def _face_normal(verts, face):
    """Newell's method — robust for slightly non-planar quads."""
    nx = ny = nz = 0.0
    n = len(face)
    for k in range(n):
        x0, y0, z0 = verts[face[k]]
        x1, y1, z1 = verts[face[(k + 1) % n]]
        nx += (y0 - y1) * (z0 + z1)
        ny += (z0 - z1) * (x0 + x1)
        nz += (x0 - x1) * (y0 + y1)
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    if ln < 1e-12:
        return None                                   # degenerate face: no direction
    return (nx / ln, ny / ln, nz / ln)


def crease_profile(verts, faces):
    """The normal-field roughness profile. Degenerate faces are EXCLUDED from
    angles (a zero-area face has no normal) but COUNTED — a torn sheet grows
    them, and silence about that would be the guard lying by omission."""
    normals, degenerate = {}, 0
    for fi, f in enumerate(faces):
        nrm = _face_normal(verts, f)
        if nrm is None:
            degenerate += 1
        else:
            normals[fi] = nrm
    edge_faces = {}
    for fi, f in enumerate(faces):
        n = len(f)
        for k in range(n):
            e = (min(f[k], f[(k + 1) % n]), max(f[k], f[(k + 1) % n]))
            edge_faces.setdefault(e, []).append(fi)
    angles = []
    for e, fs in edge_faces.items():
        if len(fs) != 2 or fs[0] not in normals or fs[1] not in normals:
            continue
        a, b = normals[fs[0]], normals[fs[1]]
        dot = max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))
        angles.append(math.degrees(math.acos(dot)))
    if not angles:
        return {"n_edges": 0, "frac_over": 1.0, "p95": 180.0, "mean": 180.0,
                "degenerate": degenerate}
    angles.sort()
    return {
        "n_edges": len(angles),
        "frac_over": sum(1 for a in angles if a > SHRED_EDGE_DEG) / len(angles),
        "p95": angles[min(len(angles) - 1, int(0.95 * len(angles)))],
        "mean": sum(angles) / len(angles),
        "degenerate": degenerate,
    }


# ---------------------------------------------------------------------------
# CREASE BELIEVABILITY (p2r28) — the chaos-band instrument for a MADE fold.
#
# The 2026-08-13 cloth DR (knowledge/rendering/bed-cloth-state-mechanisms.md §6)
# gives the band real re-draped fabric varies between identical trials: ±15%
# drape coefficient, ±25% fold/node dimensions, ±3 fold count. That is
# trial-to-trial variance; this instrument transfers it WITHIN one frame as a
# declared analogy (recorded, not hidden): repeated features of one crease —
# its wander and its hand-tuck depths — must vary at least a floor's worth,
# because a row of identical features is the one state real cloth never
# produces. Same cut family as the aperiodicity measurement that closed the
# sine-hem (p2r24-25: autocorr 0.591/0.489 = machine, the critics' own words
# "a deliberate, perfectly regular sine").
#
# The thresholds are TEST parameters derived from a REFERENCE-tier band — they
# gate a mechanism's output, never a deliverable by themselves (the knowledge
# file's own law). Published constants so pure tests pin them.
# ---------------------------------------------------------------------------
CREASE_RMS_MIN = 0.003        # m — a settled fold line straighter than this is a ruler
# The periodicity cut is scoped to SHORT lags (2..CREASE_MAX_LAG): the machine
# class the critics named is cell-scale teeth, and a pure sine scores 0.98
# there. Long lags are excluded BY MEASUREMENT, not convenience: the dev()
# golden-ratio generator that lawfully drives crease wander has Fibonacci
# near-repeats (lag 8: 0.69, lag 13: 0.64, lag 34: 0.997 — measured
# 2026-08-13), which are equidistribution artifacts invisible as periodicity
# at render scale; a cut that saw them would fail every lawful wander and
# force the mechanism back to the very uniformity it exists to break.
# Short-lag separation is wide: sine 0.98 vs dev 0.48 — the 0.65 cut sits in
# the gap, not on a knife edge (the shred calibration law).
CREASE_MAX_LAG = 7
CREASE_AUTOCORR_MAX = 0.65    # detrended wander must stay aperiodic (sine-hem family)
TUCK_CV_BAND = (0.10, 0.60)   # tuck-depth spread: under = machine row, over = damage


def _detrended(samples):
    """Least-squares line fit t->v; returns residuals (the wander signal)."""
    n = len(samples)
    ts = [s[0] for s in samples]
    mt = sum(ts) / n
    denom = sum((t - mt) ** 2 for t in ts) or 1e-12
    out = []
    for vi in range(1, len(samples[0])):
        vs = [s[vi] for s in samples]
        mv = sum(vs) / n
        slope = sum((t - mt) * (v - mv) for t, v in zip(ts, vs)) / denom
        out.append([v - (mv + slope * (t - mt)) for t, v in zip(ts, vs)])
    return out


def _max_autocorr(x, max_lag=None):
    """Max normalised autocorrelation over lags 2..max_lag (default
    CREASE_MAX_LAG, capped at n/2) — 1.0 = perfectly periodic, ~0 = aperiodic.
    Guarded for a flat signal."""
    n = len(x)
    e = sum(v * v for v in x)
    if n < 6 or e < 1e-18:
        return 0.0
    if max_lag is None:
        max_lag = CREASE_MAX_LAG
    best = 0.0
    for lag in range(2, min(int(max_lag), n // 2) + 1):
        num = sum(x[i] * x[i + lag] for i in range(n - lag))
        den = math.sqrt(sum(v * v for v in x[:n - lag]) *
                        sum(v * v for v in x[lag:])) or 1e-18
        best = max(best, abs(num / den))
    return best


def crease_believability(line_pts, tuck_depths, rms_min=None, autocorr_max=None,
                         cv_band=None):
    """(bad, profile, message) for a settled fold line and its hand-tuck depths.

    line_pts     [(t, u, z), ...] — the crease's settled verts, t = the
                 across-bed coordinate, u = in-plan position, z = height.
                 Sorted by t here; caller passes raw.
    tuck_depths  measured z-drop at each tuck site, metres (>= 2 sites).

    Reads the module constants at call time (same law as shredded: an override
    must reach the guard)."""
    if rms_min is None:
        rms_min = CREASE_RMS_MIN
    if autocorr_max is None:
        autocorr_max = CREASE_AUTOCORR_MAX
    if cv_band is None:
        cv_band = TUCK_CV_BAND
    if len(line_pts) < 8:
        return True, {}, f"crease has {len(line_pts)} samples — too few to judge"
    if len(tuck_depths) < 2:
        return True, {}, f"{len(tuck_depths)} tuck depth(s) — the spread of one is undefined"
    pts = sorted(line_pts)
    resid = _detrended(pts)
    rms = math.sqrt(sum(sum(r * r for r in rs) for rs in resid)
                    / len(pts))
    auto = max(_max_autocorr(rs) for rs in resid)
    mean_d = sum(tuck_depths) / len(tuck_depths)
    if mean_d <= 1e-9:
        return True, {}, "tuck depths average zero — the hand never pressed"
    cv = math.sqrt(sum((d - mean_d) ** 2 for d in tuck_depths)
                   / len(tuck_depths)) / mean_d
    prof = {"rms": rms, "autocorr": auto, "tuck_cv": cv,
            "n_line": len(pts), "n_tucks": len(tuck_depths)}
    bad = rms < rms_min or auto > autocorr_max or not (cv_band[0] <= cv <= cv_band[1])
    msg = (f"crease wander rms {rms * 1000:.1f} mm (floor {rms_min * 1000:.1f}), "
           f"autocorr {auto:.3f} (max {autocorr_max:.2f}), "
           f"tuck-depth cv {cv:.2f} (band {cv_band[0]:.2f}-{cv_band[1]:.2f})")
    return bad, prof, msg


def shredded(verts, faces, frac_max=None):
    """(bad, profile, message). The single entry point a bake guard calls.
    frac_max=None reads the MODULE-LEVEL constant at call time, so a calibration
    override (build_room --shred-max=) actually reaches the guard — a def-time
    default would freeze the original value and the flag would silently lie."""
    if frac_max is None:
        frac_max = SHRED_FRAC_MAX
    p = crease_profile(verts, faces)
    bad = p["frac_over"] > frac_max or p["degenerate"] > 0
    msg = (f"normal-field roughness: {p['frac_over'] * 100:.1f}% of edges past "
           f"{SHRED_EDGE_DEG:.0f}° (max {frac_max * 100:.0f}%), p95 {p['p95']:.0f}°, "
           f"{p['degenerate']} degenerate face(s)")
    return bad, p, msg
