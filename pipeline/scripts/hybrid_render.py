#!/usr/bin/env python3
"""hybrid_render.py — the HYBRID beauty pass (blueprint render direction of record).

Feed the dimensionally-correct 3D render (the STRUCTURAL CONTROL image from
build_room.py) + a "make photoreal, keep exact layout" instruction to Google's
Gemini image model; get a photoreal repaint back. The 3D/spec pipeline stays the
dimensional source of truth; Gemini supplies fabric/wood/light (the part 3D+CC0
can't cheaply reach). Proven in INTERIOR-AI at ~PORS quality, ~$0.04/image
(docs/DECISIONS-render-assets.md). Ported from INTERIOR-AI tools/gemini_image.py.

Usage:
  python pipeline/scripts/hybrid_render.py INPUT.png "instruction" OUTPUT.png
  python pipeline/scripts/hybrid_render.py INPUT.png "@render-hybrid" OUTPUT.png room_type="master bedroom suite"
      # "@<intent>[@label]" resolves a compiled prompt from pipeline/prompts/registry/
      # (label defaults to staging); trailing key=value args fill template {slots}.

Commercial note: free tier restricts commercial rights — client work must run on
the PAID tier (docs/DECISIONS-render-assets.md). Output is a DRAFT until it passes
the critique gate (critique.py) + human QA.
"""
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent  # pipeline/scripts -> repo root (STUDIO-OS layout)
USAGE_FILE = REPO_ROOT / ".gemini_usage.json"   # project-local daily-cost counter


def _load_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env = REPO_ROOT / ".env"   # self-contained: only this repo's .env
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GEMINI_API_KEY not found (env or repo .env)")


MODELS = ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image",
          "gemini-2.0-flash-preview-image-generation"]


def _bump_usage():
    today = str(date.today())
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8")) if USAGE_FILE.exists() else {}
    except Exception:
        data = {}
    if data.get("date") != today:
        data = {"date": today}
    data["image"] = data.get("image", 0) + 1
    try:
        USAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _post(url, body, ctx=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
        return json.load(r)


def edit(inp, prompt, out):
    key = _load_key()
    b64 = base64.b64encode(open(inp, "rb").read()).decode()
    mime = "image/png" if inp.lower().endswith(".png") else "image/jpeg"
    body = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": b64}},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    last = ""
    for model in MODELS:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={key}")
        try:
            try:
                data = _post(url, body)
            except urllib.error.URLError as e:
                if not isinstance(getattr(e, "reason", None), ssl.SSLError):
                    raise
                # machine sits behind a TLS-intercepting VPN (NordLayer) — same
                # trust call as assets.py: unverified context = curl -k equivalent
                data = _post(url, body, ctx=ssl._create_unverified_context())
        except urllib.error.HTTPError as e:
            last = f"{model}: HTTP {e.code} {e.read().decode()[:300]}"
            print("  ..", last)
            # some models reject responseModalities=IMAGE-only; retry with TEXT+IMAGE
            if e.code == 400 and body["generationConfig"]["responseModalities"] == ["IMAGE"]:
                body["generationConfig"]["responseModalities"] = ["TEXT", "IMAGE"]
                try:
                    data = _post(url, body)
                except Exception as e2:
                    last = f"{model} (retry): {e2}"; print("  ..", last); continue
            else:
                continue
        except Exception as e:
            last = f"{model}: {e}"; print("  ..", last); continue
        _bump_usage()
        # extract the first inline image part
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                blob = part.get("inline_data") or part.get("inlineData")
                if blob and blob.get("data"):
                    open(out, "wb").write(base64.b64decode(blob["data"]))
                    print(f"OK [{model}] -> {out}")
                    return True
        last = f"{model}: no image part in response ({json.dumps(data)[:300]})"
        print("  ..", last)
    print("FAILED:", last)
    return False


REGISTRY = REPO_ROOT / "pipeline" / "prompts" / "registry"


def resolve_prompt(ref, overrides):
    """'@<intent>[@label]' -> compiled instruction from the prompt registry.
    Registry payloads are immutable versions; labels.json picks the version.
    `overrides` (dict) fills template {slots} on top of the payload defaults."""
    parts = ref.lstrip("@").split("@")
    intent, label = parts[0], (parts[1] if len(parts) > 1 else "staging")
    d = REGISTRY / intent
    labels = json.loads((d / "labels.json").read_text(encoding="utf-8"))
    version = labels.get(label)
    if not version:
        raise SystemExit(f"registry: label '{label}' of '{intent}' points to no version yet")
    payload = json.loads((d / f"{version}.json").read_text(encoding="utf-8"))
    slots = dict(payload.get("defaults", {}))
    slots.update(overrides)
    try:
        prompt = payload["template"].format(**slots)
    except KeyError as e:
        raise SystemExit(f"registry: missing required slot {e} for {intent}@{label} "
                         f"({version}) — pass it as key=value")
    print(f"  prompt registry: {intent}@{label} -> {version}")
    return prompt


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    instruction = sys.argv[2]
    if instruction.startswith("@"):
        overrides = dict(kv.split("=", 1) for kv in sys.argv[4:] if "=" in kv)
        instruction = resolve_prompt(instruction, overrides)
    ok = edit(sys.argv[1], instruction, sys.argv[3])
    sys.exit(0 if ok else 1)
