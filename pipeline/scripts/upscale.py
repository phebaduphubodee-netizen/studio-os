#!/usr/bin/env python3
"""upscale.py — deliverable upscaler (closes the 'final = native-res, upscaler

CLI-ONLY: run by hand on a candidate deliverable frame (Stage-07 native-res gap disclosure) — triage 2026-08-25.
unwired' disclosure from PRJ-2026-002 Stage 07).

Hybrid renders come back from the image model at native ~1-2 MP; client
deliverables want 2x/4x. Two backends, auto-detected:

  1. realesrgan-ncnn-vulkan  (real SR, runs on the RTX 3060 via Vulkan, no Python
     deps). Owner install (one time):
       - download the Windows release zip of Real-ESRGAN ncnn from the official
         xinntao/Real-ESRGAN GitHub releases
       - unzip anywhere; either add the folder to PATH or set
         REALESRGAN_BIN to the full path of realesrgan-ncnn-vulkan.exe
  2. PIL Lanczos + mild unsharp (NOT super-resolution — an honest fallback so
     the pipeline slot is never blocked; output is tagged `method` in the
     sidecar JSON and the QA line must disclose it).

(A torch-realesrgan backend was dropped: it needs a real weights path/URL, so
a stub with model_path=None never actually ran — it only masqueraded as an SR
backend before falling through. ncnn is the one real SR path on this machine.)

Every output writes a sidecar <out>.upscale.json {method, scale, src_sha256}
so Stage 05/07 can state HOW the deliverable was scaled (never silently).

Usage:
  python pipeline/scripts/upscale.py IN.png OUT.png [--scale 2|3|4]
Exit 0 on success (any backend), 1 on failure.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys


def _sha256(p, n=1 << 16):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(n):
            h.update(chunk)
    return h.hexdigest()


def _find_ncnn():
    env = os.environ.get("REALESRGAN_BIN")
    if env and os.path.exists(env):
        return env
    return shutil.which("realesrgan-ncnn-vulkan")


def _ncnn(inp, out, scale):
    exe = _find_ncnn()
    if not exe:
        return None
    r = subprocess.run([exe, "-i", inp, "-o", out, "-s", str(scale)],
                       capture_output=True, text=True, timeout=600)
    if r.returncode == 0 and os.path.exists(out):
        return "realesrgan-ncnn-vulkan"
    print(f"  (ncnn failed: {(r.stderr or r.stdout)[:300]})", file=sys.stderr)
    return None


def _lanczos(inp, out, scale):
    from PIL import Image, ImageFilter
    im = Image.open(inp).convert("RGB")
    im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    im.save(out)
    return "lanczos+unsharp (NOT super-resolution — install Real-ESRGAN for SR)"


def upscale(inp, out, scale=2):
    method = _ncnn(inp, out, scale) or _lanczos(inp, out, scale)
    side = {"method": method, "scale": scale, "src": os.path.basename(inp),
            "src_sha256": _sha256(inp)}
    with open(out + ".upscale.json", "w", encoding="utf-8") as f:
        json.dump(side, f, indent=1)
    print(f"OK [{method}] x{scale} -> {out}")
    return method


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    sc = 2
    if "--scale" in sys.argv:
        sc = int(sys.argv[sys.argv.index("--scale") + 1])
    upscale(sys.argv[1], sys.argv[2], sc)
