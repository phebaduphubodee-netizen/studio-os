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
