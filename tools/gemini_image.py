#!/usr/bin/env python3
"""Minimal Gemini image-model (Nano Banana) editor: feed an input image + instruction,
get a repainted image back. Used to test the HYBRID render path — a dimensionally-correct
3D/CAD render as the structural control, Gemini for photoreal beauty.

Self-contained: reads only PlingPeat/.env (no BRAINDEAD dependency).

Usage:
  python tools/gemini_image.py INPUT.png "make this a photoreal luxury Thai condo interior" OUTPUT.png
"""
import sys, os, base64, json, urllib.request, urllib.error

def _load_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    here = os.path.dirname(os.path.abspath(__file__))
    env = os.path.join(here, "..", ".env")   # self-contained: only PlingPeat/.env
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GEMINI_API_KEY not found (env or PlingPeat/.env; see .env.example)")

MODELS = ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image",
          "gemini-2.0-flash-preview-image-generation"]

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
            req = urllib.request.Request(
                url, data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            last = f"{model}: HTTP {e.code} {e.read().decode()[:300]}"
            print("  ..", last)
            # some models reject responseModalities=IMAGE-only; retry with TEXT+IMAGE
            if e.code == 400 and body["generationConfig"]["responseModalities"] == ["IMAGE"]:
                body["generationConfig"]["responseModalities"] = ["TEXT", "IMAGE"]
                try:
                    req = urllib.request.Request(
                        url, data=json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        data = json.load(r)
                except Exception as e2:
                    last = f"{model} (retry): {e2}"; print("  ..", last); continue
            else:
                continue
        except Exception as e:
            last = f"{model}: {e}"; print("  ..", last); continue
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

if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    edit(sys.argv[1], sys.argv[2], sys.argv[3])
