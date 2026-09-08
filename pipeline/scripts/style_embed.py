"""style_embed.py -- LOCAL perceptual embedding lane (Stage B2 of the sellability learning engine).

WHY: the color style_fingerprint is a tape measure -- it reads palette/mono/lighting but is BLIND
to composition, camera, staging and furnishing. We proved that blindness on 2026-07-15: the de-wood
"improvement" moved mostly through camera + staging, which the color fingerprint could not see. To
LEARN from HUNDREDS of the friend's delivered renders that neither the owner can hand-annotate nor
a cloud model may look at, we give the MACHINE local perceptual eyes: a CLIP image embedding,
computed ON THIS MACHINE, captures style/composition/material-feel far richer than colour stats.
The system sees; no human and no cloud does. (Evidence it works: two clay renders of the SAME
bedroom in OPPOSITE colours -- brown walnut vs warm-white de-wood -- still read cos=0.87, so CLIP
is keying on scene STRUCTURE, not the palette the fingerprint already covers.)

LOCAL-ONLY (owner decision 2026-07-12; qa/benchmark-sellability.md): images NEVER leave the
machine. CLIP runs on CPU locally (torch+cpu, open_clip). The ONLY network touch is a one-time
download of PUBLIC model WEIGHTS (ViT-B-32) into the local cache -- fetching a public model IN is
not sending a client image OUT, the same category as `pip install`. Every emitted identifier goes
through _safe_ref (imported from style_fingerprint, one source of truth): a _private/ path becomes
a non-reversible "private:<hash>" token, so a nearest-neighbour pointer surfaces a client's work by
I-code only, never a name. Embeddings are lossy 512-d vectors (no image is reconstructable) but are
still client-derived: write banks ONLY to gitignored locations, never commit them.

NOT A BEAUTY SCORE: a perceptual DISTANCE is not a verdict. This answers "how far is our render
from the sellable cluster, and which sellable renders look most like it" -- a POINTER for the
designer's eye, never a replacement for it. Turning a distance into a better render still flows
through the generation levers (materials/lighting/camera/staging) + designer taste.

ANTI-FLATTERING tripwire (test_style_embed.py, our own repo renders): our un-textured CLAY massing
renders must sit perceptually FARTHER from the FINISHED render pool than finished renders sit from
each other -- a CLIP space that cannot tell a 3D massing test from a photoreal interior is useless
here. Measured: clay->finished mean cos 0.852 < finished->finished 0.922.

Determinism: model.eval() + torch.no_grad(), fixed weights, CPU -> identical bytes in, identical
vector out (verified max|delta| = 0.0).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from style_fingerprint import _safe_ref  # shared privacy scrubber -- single source of truth

EMBED_VERSION = "1.1"           # 1.1: fixed QuickGELU pairing (space changed -> banks must rebuild)
MODEL_NAME = "ViT-B-32-quickgelu"   # openai weights were trained with QuickGELU; plain 'ViT-B-32'
PRETRAINED = "openai"               # runs them through nn.GELU (off-spec) -- review 2026-07-15
EMBED_DIM = 512

_MODEL = None
_PREPROCESS = None


def _load_model():
    """Lazily create the CLIP model once (eval mode, CPU). First call may download public weights."""
    global _MODEL, _PREPROCESS
    if _MODEL is None:
        import open_clip
        model, _, preprocess = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED)
        model.eval()
        _MODEL, _PREPROCESS = model, preprocess
    return _MODEL, _PREPROCESS


def _open_rgb(path) -> Image.Image:
    """Open as RGB; RGBA/transparency composited over WHITE (render bg), matching style_fingerprint."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    return im


def embed(path) -> np.ndarray:
    """Deterministic L2-normalized 512-d CLIP image embedding. NO image egress (local CPU inference)."""
    import torch
    model, preprocess = _load_model()
    x = preprocess(_open_rgb(path)).unsqueeze(0)
    with torch.no_grad():
        f = model.encode_image(x)
        f = f / f.norm(dim=-1, keepdim=True)
    return f[0].cpu().numpy().astype(np.float32)


def embed_many(paths):
    """-> (refs, vecs). refs are I-coded via _safe_ref (never a raw _private/ path). Deterministic
    order = the order given; callers building a bank should pass SORTED paths for reproducibility."""
    refs, vecs = [], []
    for p in paths:
        refs.append(_safe_ref(str(p)))
        vecs.append(embed(p))
    mat = np.stack(vecs) if vecs else np.zeros((0, EMBED_DIM), np.float32)
    return refs, mat


def save_bank(out_path, refs, vecs, extra_meta=None):
    """Write a gitignored embedding bank (I-coded refs + vectors + meta). Never commit a bank."""
    meta = {"version": EMBED_VERSION, "model": MODEL_NAME, "pretrained": PRETRAINED,
            "dim": EMBED_DIM, "n": len(refs)}
    if extra_meta:
        meta.update(extra_meta)
    np.savez(out_path, refs=np.array(refs, dtype=object),
             vecs=vecs.astype(np.float32), meta=json.dumps(meta, ensure_ascii=False))
    return meta


def load_bank(path):
    z = np.load(path, allow_pickle=True)
    return list(z["refs"]), z["vecs"].astype(np.float32), json.loads(str(z["meta"]))


def nearest(query_vec, bank_vecs, refs, k=5):
    """Top-k bank rows by cosine (both normalized) -> [(ref, cos)]. Refs are I-coded pointers."""
    if len(bank_vecs) == 0:
        return []
    sims = bank_vecs @ query_vec
    # stable, value-only order: -cos then ref -> tied (byte-identical) anchors don't reorder across
    # numpy builds and the k-boundary survivor is reproducible (matches style_fingerprint._palette).
    order = sorted(range(len(sims)), key=lambda i: (-float(sims[i]), refs[i]))[:k]
    return [(refs[i], round(float(sims[i]), 4)) for i in order]


def gap_stats(query_vec, bank_vecs):
    """Where does our render sit vs the sellable cluster? our_mean_cos_to_bank compared to each bank
    member's centrality (mean cos to the OTHERS). A LOW percentile = our render is a perceptual
    OUTLIER to the sellable pool (far from their look), a HIGH percentile = as TYPICAL of the pool
    as its own central members. It is NOT a beauty verdict -- typicality is not quality; a bland
    render can be central. Only a distance/pointer.

    Percentile uses a tie-MIDPOINT rank (review 2026-07-15): a render that fits the cluster exactly
    as well as members fit each other lands at ~50, not at an extreme. n<2 returns None (a
    centrality-of-others, and hence a percentile, is undefined for a lone member -- the benchmark's
    room buckets really do yield n=1 sub-banks)."""
    n = len(bank_vecs)
    if n == 0:
        return {"n_bank": 0}
    sims = bank_vecs @ query_vec
    out = {"our_mean_cos_to_bank": round(float(sims.mean()), 4),
           "our_max_cos": round(float(sims.max()), 4), "n_bank": n}
    if n < 2:
        out.update({"our_percentile_in_bank": None, "bank_centrality_median": None,
                    "note": "bank too small (n<2) for a centrality percentile"})
        return out
    our_mean = float(sims.mean())
    G = bank_vecs @ bank_vecs.T
    np.fill_diagonal(G, 0.0)
    bank_centr = G.sum(1) / (n - 1)
    tie = np.isclose(bank_centr, our_mean)
    below = float(((bank_centr < our_mean) & ~tie).mean())
    pct = (below + 0.5 * float(tie.mean())) * 100.0     # mid-rank: ties count half
    out["bank_centrality_median"] = round(float(np.median(bank_centr)), 4)
    out["our_percentile_in_bank"] = round(pct, 1)
    return out


def _refuse_committable(out_path):
    """Client-derived banks must be gitignored, never committable. HARD-refuse (before any write) an
    --out that git does not ignore -- unless it resolves OUTSIDE the repo (e.g. scratchpad/temp), which
    cannot be committed here anyway. Replaces the old post-write advisory warning (review 2026-07-15)."""
    import subprocess
    repo = Path(__file__).resolve().parents[2]
    p = Path(out_path).resolve()
    try:
        p.relative_to(repo)
    except ValueError:
        return  # outside the repo tree -> not committable here
    r = subprocess.run(["git", "check-ignore", "-q", str(p)], cwd=str(repo))
    if r.returncode != 0:
        sys.exit(f"REFUSED: bank --out '{out_path}' is not gitignored; a client-derived bank must "
                 f"never be committable. Write under _private/ (or outside the repo).")


def _check_bank_meta(meta, bank_path):
    """A bank is only comparable to queries embedded by the SAME model/version. Fail LOUD on drift
    (e.g. querying a pre-QuickGELU-fix bank) instead of returning silently-wrong cosines."""
    want = {"model": MODEL_NAME, "pretrained": PRETRAINED, "dim": EMBED_DIM, "version": EMBED_VERSION}
    got = {k: meta.get(k) for k in want}
    if got != want:
        sys.exit(f"REFUSED: bank '{bank_path}' was built with {got} but this tool embeds with {want}; "
                 f"rebuild the bank (embeddings are not comparable across models/versions).")


def _main(argv=None):
    ap = argparse.ArgumentParser(description="LOCAL CLIP perceptual embedding lane (no image egress).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="embed images into a gitignored bank .npz")
    b.add_argument("images", nargs="+")
    b.add_argument("--out", required=True, help="bank .npz path (MUST be a gitignored location)")

    n = sub.add_parser("nearest", help="top-k bank renders most like OUR render (by I-code)")
    n.add_argument("query")
    n.add_argument("--bank", required=True)
    n.add_argument("-k", type=int, default=5)

    g = sub.add_parser("gap", help="where OUR render sits vs the sellable bank")
    g.add_argument("query")
    g.add_argument("--bank", required=True)

    args = ap.parse_args(argv)

    if args.cmd == "build":
        _refuse_committable(args.out)                  # HARD-refuse a committable bank before writing
        paths = sorted(args.images)                    # reproducible bank ordering
        refs, vecs = embed_many(paths)
        meta = save_bank(args.out, refs, vecs)
        print(json.dumps({"built": _safe_ref(args.out), **meta}, ensure_ascii=False, indent=2))
    elif args.cmd == "nearest":
        refs, vecs, meta = load_bank(args.bank)
        _check_bank_meta(meta, args.bank)
        q = embed(args.query)
        print(json.dumps({"query": _safe_ref(args.query),
                          "nearest": [{"ref": r, "cos": c} for r, c in nearest(q, vecs, refs, args.k)]},
                         ensure_ascii=False, indent=2))
    elif args.cmd == "gap":
        refs, vecs, meta = load_bank(args.bank)
        _check_bank_meta(meta, args.bank)
        q = embed(args.query)
        print(json.dumps({"query": _safe_ref(args.query), **gap_stats(q, vecs)},
                         ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
