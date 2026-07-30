"""Armour for the shred detector (clothcheck.py) — the instrument the round-5
gate ordered BEFORE any more sim spend. Synthetic meshes with known roughness:
the guard must separate smooth drape from crumple by a wide margin, so the
calibrated threshold sits in a gap, not on a knife edge."""
import math
import random

import clothcheck as cc


def _grid(nu, nv, z=lambda u, v: 0.0):
    verts = [(u / nu, v / nv, z(u / nu, v / nv)) for v in range(nv + 1) for u in range(nu + 1)]
    faces = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return verts, faces


def test_flat_sheet_is_perfectly_smooth():
    bad, p, _ = cc.shredded(*_grid(12, 12))
    assert not bad
    assert p["frac_over"] == 0.0 and p["mean"] < 1e-6


def test_gentle_drape_curvature_passes():
    # a soft sine billow at real-drape scale: what a healthy baked sheet looks like
    bad, p, _ = cc.shredded(*_grid(16, 16, z=lambda u, v: 0.03 * math.sin(3 * u * math.pi)
                                   * math.sin(2 * v * math.pi)))
    assert not bad
    assert p["frac_over"] < cc.SHRED_FRAC_MAX * 0.5      # well clear, not knife-edge


def test_crumpled_wad_fails_loudly():
    rng = random.Random(7)
    verts, faces = _grid(16, 16)
    crumpled = [(x + rng.uniform(-0.04, 0.04), y + rng.uniform(-0.04, 0.04),
                 z + rng.uniform(-0.04, 0.04)) for x, y, z in verts]
    bad, p, msg = cc.shredded(crumpled, faces)
    assert bad
    assert p["frac_over"] > cc.SHRED_FRAC_MAX * 3        # far past, not marginal
    assert "normal-field" in msg


def test_a_single_deep_crease_is_not_a_shred():
    # a duvet fold: one hard ridge across the sheet must NOT trip a population guard
    verts, faces = _grid(16, 16, z=lambda u, v: 0.08 * max(0.0, 0.5 - abs(u - 0.5)) * 2)
    bad, p, _ = cc.shredded(verts, faces)
    assert not bad


def test_degenerate_faces_are_counted_and_fatal():
    verts, faces = _grid(6, 6)
    verts[0] = verts[1] = verts[7] = verts[8]            # collapse one quad to a point
    bad, p, _ = cc.shredded(verts, faces)
    assert bad and p["degenerate"] >= 1


def test_profile_reports_edge_population():
    _, p, _ = cc.shredded(*_grid(8, 8))
    assert p["n_edges"] == 2 * 8 * 7                     # interior edges of an 8x8 quad grid
