"""
assets.py — fetch CC0 3D assets from Poly Haven (models / HDRIs / textures).

Poly Haven is CC0 (public domain) → free for commercial client deliverables (see
docs/LICENSING.md). This module downloads + caches assets so build_room.py can place
REAL furniture (a real sofa, not a box) and light with a real HDRI.

Two environment realities handled here:
  * the machine sits behind a TLS-intercepting VPN/filter (NordLayer) → HTTPS certs don't
    verify against curl/urllib's default store, so we use an UNVERIFIED SSL context (same
    as `curl -k`; we are trusting the founder's own VPN interception, not a stranger's MITM).
  * gltf models are multi-file (.gltf + .bin + textures/) → we download every file in the
    API's `include` map, preserving relative paths, so the .gltf resolves locally.

    python pipeline/assets.py <slug> [--type models|hdris] [--res 1k|2k]

Cache: raw/assets/cc0/<type>/<slug>/...  (idempotent; skips files already present).
"""
import json
import os
import shutil
import ssl
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API = "https://api.polyhaven.com"
_CTX = ssl._create_unverified_context()   # trust the local NordLayer TLS interception (curl -k equiv)
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(HERE), "raw", "assets", "cc0")


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "interior-ai/1.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=45) as r:
        return json.load(r)


def _download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "interior-ai/1.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=180) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    return dest


def fetch_model(slug, res="1k"):
    """Download a Poly Haven model as gltf (+ .bin + textures). Returns the local .gltf path."""
    files = _get_json(f"{API}/files/{slug}")
    if "gltf" not in files or res not in files["gltf"]:
        res = next(iter(files["gltf"]))
    g = files["gltf"][res]["gltf"]
    base = os.path.join(CACHE, "models", slug)
    main = _download(g["url"], os.path.join(base, os.path.basename(g["url"])))
    for rel, info in (g.get("include") or {}).items():
        _download(info["url"], os.path.join(base, rel.replace("/", os.sep)))
    return main


def fetch_hdri(slug, res="2k", fmt="hdr"):
    """Download a Poly Haven HDRI. Returns the local .hdr path."""
    files = _get_json(f"{API}/files/{slug}")
    hd = files.get("hdris") or files.get("hdri")   # API key differs by endpoint
    if res not in hd:
        res = next(iter(hd))
    entry = hd[res].get(fmt) or hd[res][next(iter(hd[res]))]
    dest = os.path.join(CACHE, "hdris", f"{slug}_{res}.{fmt}")
    return _download(entry["url"], dest)


# PBR texture-set maps we care about for interior surfaces. Poly Haven names vary; we take
# the first present of each logical channel. `arm` packs (AO, Rough, Metal) in R/G/B.
_TEX_MAPS = ("Diffuse", "nor_gl", "Rough", "arm", "AO", "Metal", "Displacement")


def fetch_texture(slug, res="2k", fmt="jpg", maps=_TEX_MAPS):
    """Download a Poly Haven PBR texture set. Returns {logical_map: local_path} for every
    requested map that exists (e.g. Diffuse/nor_gl/Rough). All files cached under
    raw/assets/cc0/textures/<slug>/."""
    files = _get_json(f"{API}/files/{slug}")
    base = os.path.join(CACHE, "textures", slug)
    got = {}
    for m in maps:
        node = files.get(m)
        if not node:
            continue
        r = res if res in node else next(iter(node))
        entry = node[r].get(fmt) or node[r][next(iter(node[r]))]
        ext = os.path.splitext(entry["url"])[1] or f".{fmt}"
        got[m] = _download(entry["url"], os.path.join(base, f"{slug}_{m}_{r}{ext}"))
    return got


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: python pipeline/assets.py <slug> [--type models|hdris] [--res 1k|2k]")
    slug = args[0]
    typ = args[args.index("--type") + 1] if "--type" in args else "models"
    default_res = {"hdris": "2k", "textures": "2k"}.get(typ, "1k")
    res = args[args.index("--res") + 1] if "--res" in args else default_res
    if typ == "hdris":
        path = fetch_hdri(slug, res)
        print(f"  fetched {slug} (hdris, {res}) -> {path}  ({os.path.getsize(path)} bytes)")
    elif typ == "textures":
        got = fetch_texture(slug, res)
        print(f"  fetched {slug} (textures, {res}): " +
              ", ".join(f"{k}={os.path.basename(v)}" for k, v in got.items()))
    else:
        path = fetch_model(slug, res)
        print(f"  fetched {slug} ({typ}, {res}) -> {path}  ({os.path.getsize(path)} bytes)")
