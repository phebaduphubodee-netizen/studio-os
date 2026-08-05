"""critique_call.py — R7b C3: send a critique BUNDLE to Gemini and archive the
answer in the bundle dir. Billing opened 2026-08-04; this replaces the
owner-paste ritual (which remains the fallback when this errors).

  python pipeline/scripts/critique_call.py <bundle-name> [--model pro|flash]

The bundle name is resolved under the repo's private tree INTERNALLY so no
private path travels on a command line (the bash guard tripwires on that, and
it should). What may leave the machine is enforced HERE, structurally:
  - exactly one image: the bundle's own render (must match the bundle name)
  - the bundle's PROMPT.md text, scrubbed: refuses to send if it references
    target/anchor imagery or carries a client-ish path fragment
The TARGET IMAGE AND ANCHORS NEVER TRAVEL (R7b hard rule; they are another
studio's delivered client work).
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODELS = {"flash": "gemini-2.5-flash", "pro": "gemini-2.5-pro"}
FORBIDDEN = re.compile(r"target\.(jpg|png)|anchor|_private[\\/]+discord|clients[\\/]", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", help="bundle dir name, e.g. critique-trn002_blockout_r2")
    ap.add_argument("--model", default="pro", choices=list(MODELS))
    a = ap.parse_args()

    # Since the training/ split (2026-08-04) a bundle is TWO mirrored dirs:
    # binaries stay under _private/**, text (PROMPT/ANSWER/README) lives under
    # training/**. Resolve both; the answer archives on the text side.
    hits = [p for p in REPO.glob(f"_private/**/critique/{a.bundle}") if p.is_dir()]
    if len(hits) != 1:
        sys.exit(f"bundle '{a.bundle}' matched {len(hits)} render dirs — need exactly 1")
    bundle = hits[0]
    text_hits = [p for p in REPO.glob(f"training/**/critique/{a.bundle}") if p.is_dir()]
    text_dir = text_hits[0] if len(text_hits) == 1 else bundle
    render = bundle / (a.bundle.replace("critique-", "") + ".png")
    if not render.exists():
        sys.exit(f"bundle render {render.name} missing — the ONLY image allowed out")
    prompt_path = text_dir / "PROMPT.md"
    if not prompt_path.exists():
        prompt_path = bundle / "PROMPT.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    m = FORBIDDEN.search(prompt)
    if m:
        sys.exit(f"PROMPT.md contains forbidden reference '{m.group(0)}' — refusing to send")

    from dotenv import load_dotenv
    import os
    load_dotenv(REPO / ".env")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY not in repo .env — fall back to the owner-paste ritual")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=MODELS[a.model],
        contents=[types.Part.from_bytes(data=render.read_bytes(), mime_type="image/png"), prompt],
        config=types.GenerateContentConfig(temperature=0.3),
    )
    out = text_dir / f"ANSWER_gemini25{a.model}.md"
    out.write_text(resp.text, encoding="utf-8")

    usage = REPO / ".gemini_usage.json"
    try:
        data = json.loads(usage.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if data.get("date") != date.today().isoformat():
        data = {"date": date.today().isoformat(), "flash": 0, "pro": 0,
                "thinking": 0, "deep": 0, "vision": 0}
    data["vision"] = data.get("vision", 0) + 1
    data[a.model] = data.get(a.model, 0) + 1
    usage.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # The answer is usually Thai; a cp1252 console cannot print it and the
    # UnicodeEncodeError made this tool exit 1 AFTER successfully archiving —
    # so every scripted caller read "failed" on calls that worked (it did so on
    # both r14 and r15). Reconfigure stdout rather than strip the text: the
    # answer's exact words are the artifact.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"answer -> {out.relative_to(REPO)}\n{'=' * 70}\n{resp.text}")


if __name__ == "__main__":
    main()
