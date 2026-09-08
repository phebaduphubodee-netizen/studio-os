"""Tests for style_embed.py -- the LOCAL CLIP perceptual embedding lane (Stage B2).

Needs torch + open_clip + the ViT-B-32 weights present; the whole module skips VISIBLY if not
(never a silent green). The load-bearing anti-flattering check is the clay-vs-finished tripwire on
our OWN repo renders: CLIP must place an un-textured clay massing render FARTHER from the finished
render pool than finished renders sit from each other -- else the space cannot tell a 3D test from
a photoreal interior and is useless as a sellability teacher. It skips visibly if the renders are
absent (LFS not pulled); the hermetic tests still guard determinism / shape / privacy.
"""
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

pytest.importorskip("torch", reason="VISIBLE SKIP: torch not installed (local CLIP lane unavailable)")
pytest.importorskip("open_clip", reason="VISIBLE SKIP: open_clip not installed")

import style_embed as se  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
MAPS = REPO / "assets/projects/PRJ-2026-002/maps"
RENDERS = REPO / "assets/projects/PRJ-2026-002/renders"
DEWOOD = REPO / ("projects/PRJ-2026-002_c001-house/04_visualization/experiments/"
                 "dewood-2026-07-15/R_PRJ002_MasterSuite_dewood_clay.png")
FINISHED = [RENDERS / f"R_PRJ002_{r}_Cam01_v01.png" for r in ("MasterSuite", "LivingRoom", "SittingRoom")]
CLAY = [MAPS / "R_PRJ002_MasterSuite_Cam01_v01_control-clay.png",
        MAPS / "R_PRJ002_LivingRoom_Cam01_v01_control-clay.png", DEWOOD]


def _png(tmp_path, arr, name="x.png"):
    p = tmp_path / name
    Image.fromarray(arr.astype(np.uint8)).save(p)
    return str(p)


def _solid(color, h=64, w=64):
    a = np.zeros((h, w, 3), np.uint8)
    a[:, :] = color
    return a


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / np.linalg.norm(v)


# ----------------------------- hermetic: shape / norm / determinism -----------------------------

def test_embed_shape_and_unit_norm(tmp_path):
    v = se.embed(_png(tmp_path, _solid((180, 100, 40))))
    assert v.shape == (se.EMBED_DIM,)
    assert v.dtype == np.float32
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-3


def test_embed_is_deterministic(tmp_path):
    p = _png(tmp_path, _solid((120, 150, 200)))
    assert float(np.abs(se.embed(p) - se.embed(p)).max()) == 0.0


def test_embed_distinguishes_different_images(tmp_path):
    """Not a constant encoder: two different images must give different vectors (cos < 1)."""
    a = se.embed(_png(tmp_path, _solid((200, 40, 40)), "r.png"))
    b = se.embed(_png(tmp_path, _solid((40, 60, 200)), "b.png"))
    assert not np.allclose(a, b)
    assert float(a @ b) < 0.999


def test_rgba_composited_over_white_not_black(tmp_path):
    """A transparent render bg reads as WHITE, not black: embed(transparent) ~= embed(white)."""
    rgba = np.zeros((64, 64, 4), np.uint8)  # fully transparent
    tp = tmp_path / "t.png"
    Image.fromarray(rgba, "RGBA").save(tp)
    white = se.embed(_png(tmp_path, _solid((255, 255, 255)), "w.png"))
    assert float(se.embed(str(tp)) @ white) > 0.99


# ----------------------------- privacy: refs I-coded in bank + queries -----------------------------

def test_bank_refs_scrub_private_client_paths(tmp_path):
    """embed_many/save_bank must surface a _private/ anchor only as an I-coded token, never the
    client folder/basename (LOCAL-ONLY law; reuses style_fingerprint._safe_ref)."""
    secret = "SomchaiPrivateClientName"
    d = tmp_path / "_private" / "discord" / secret
    d.mkdir(parents=True)
    p = d / f"{secret}.png"
    Image.fromarray(_solid((180, 100, 40))).save(p)
    refs, vecs = se.embed_many([str(p)])
    assert refs[0].startswith("private:")
    out = tmp_path / "bank.npz"
    se.save_bank(str(out), refs, vecs)
    r2, v2, meta = se.load_bank(str(out))
    assert secret not in json.dumps(r2) and secret not in json.dumps(meta)
    assert v2.shape == (1, se.EMBED_DIM)


def test_build_cli_stdout_scrubs_client_name(tmp_path, capsys):
    """The `build` stdout 'built' field was the ONE emitted id bypassing _safe_ref (review, HIGH).
    Drive the real CLI on a _private/ path and assert the client name never reaches stdout."""
    secret = "SomchaiPrivateClientName"
    d = tmp_path / "_private" / "discord" / secret
    d.mkdir(parents=True)
    img = d / f"{secret}.png"
    Image.fromarray(_solid((180, 100, 40))).save(img)
    se._main(["build", str(img), "--out", str(d / "bank.npz")])  # tmp is outside repo -> not refused
    printed = capsys.readouterr().out
    assert secret not in printed
    assert '"built": "private:' in printed


# ----------------------------- gap_stats percentile: direction + small-bank (hermetic vectors) -----------------------------

def test_gap_percentile_direction_and_small_bank():
    """Pins the DIRECTION and small-n behaviour of the load-bearing percentile with hand-built unit
    vectors (no model needed). A central query must read HIGH, an outlier query LOW -- so flipping
    the `<`/`>` on the comparison (or returning a constant) fails. n<2 must return None, not a
    falsely-precise 100.0 (review 2026-07-15, findings 2-5)."""
    # bank: 3 tightly clustered near the x-axis + 1 orthogonal outlier
    bank = np.stack([_unit([1, 0, 0]), _unit([0.98, 0.2, 0]), _unit([0.98, -0.2, 0]), _unit([0, 0, 1])])
    central = se.gap_stats(_unit([1, 0, 0]), bank)["our_percentile_in_bank"]
    outlier = se.gap_stats(_unit([0, 0, 1]), bank)["our_percentile_in_bank"]
    assert central > 60 and outlier < 40 and central > outlier
    # n<2: a centrality percentile is undefined -> None, never a spurious 100.0
    g1 = se.gap_stats(_unit([1, 0, 0]), np.stack([_unit([0.9, 0.1, 0])]))
    assert g1["n_bank"] == 1 and g1["our_percentile_in_bank"] is None


# ----------------------------- nearest / gap plumbing (hermetic) -----------------------------

def test_nearest_and_gap_on_tiny_bank(tmp_path):
    refs, vecs = se.embed_many([_png(tmp_path, _solid(c), f"{i}.png")
                                for i, c in enumerate([(200, 40, 40), (40, 200, 40), (40, 40, 200)])])
    q = se.embed(_png(tmp_path, _solid((200, 40, 40)), "q.png"))  # == first bank image
    near = se.nearest(q, vecs, refs, k=2)
    assert len(near) == 2 and near[0][1] >= near[1][1]      # sorted desc by cosine
    assert near[0][1] > 0.99                                 # identical image is the top match
    g = se.gap_stats(q, vecs)
    assert g["n_bank"] == 3 and 0.0 <= g["our_percentile_in_bank"] <= 100.0


# ----------------------------- the anti-flattering ACCEPTANCE tripwire (real repo renders) -----------------------------

@pytest.mark.skipif(not (all(p.exists() for p in FINISHED) and all(p.exists() for p in CLAY)),
                    reason="VISIBLE SKIP: PRJ-002 clay/finished renders absent (LFS not pulled)")
def test_tripwire_clay_farther_than_finished():
    """CLIP must place a CLAY massing render FARTHER from the FINISHED pool than finished renders sit
    from each other -- else it cannot tell a 3D test from a photoreal interior. Measured 0.852<0.922;
    a comfortable margin is required so a degenerate near-constant encoder (all cos~1) fails."""
    import itertools
    fin = {p: se.embed(str(p)) for p in FINISHED}
    clay = {p: se.embed(str(p)) for p in CLAY}
    ff = [float(fin[a] @ fin[b]) for a, b in itertools.combinations(FINISHED, 2)]
    cf = [float(clay[c] @ fin[f]) for c in CLAY for f in FINISHED]
    mean_ff, mean_cf = float(np.mean(ff)), float(np.mean(cf))
    assert mean_cf < mean_ff - 0.02, f"clay not an outlier: clay->fin {mean_cf:.3f} vs fin->fin {mean_ff:.3f}"
