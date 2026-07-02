"""
critique.py — INTERIOR-AI honest self-critique gate.

WHY THIS EXISTS (2026-07-01, founder challenge):
  The founder pointed out a real blind spot: the pipeline (and the AI driving it)
  will happily call its own output "verified / professional" while grading only
  "does it run / are the dimensions right" — never "is this actually GOOD?".
  An AI that cannot say its own work is bad is exactly how you ship an illusion.

  This gate turns aesthetic discernment into a GUARDRAIL. It sends a produced
  artifact (a Cycles render, or a 2D plan/elevation PNG) to a VISION model acting
  as a brutally honest, INDEPENDENT critic with NO stake in the image, scored
  against a FIXED rubric and prompted to find what is WRONG. It does not block
  (human stays in the loop) — it refuses to let "looks fine" go unchallenged.

  Known failure modes it must catch (things a self-serving grader misses):
    RENDER: furniture that is primitive boxes/blocks; a subject floating in an
            empty void with no room; flat/even unlit lighting; zero styling/life.
    PLAN:   colliding labels/dimensions; furniture drawn as plain boxes not
            symbols; no line-weight hierarchy; an unprofessional sheet.

USAGE:
  python pipeline/critique.py output/room_bedroom_suite_hero.png
  python pipeline/critique.py output/suiteplan_bedroom_suite.png --kind plan
  python pipeline/critique.py <img> [--kind auto|render|plan] [--model flash|pro] [--out x.json]

Uses Gemini vision (shared GEMINI_API_KEY). A different "mind" than the generator,
so the critique is not the author grading itself. Not a substitute for a human
designer's final taste call — a floor, not a ceiling.
"""
import argparse
import io
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
INTERIOR_ROOT = HERE.parent
# Self-contained: load ONLY this project's .env (no BRAINDEAD fallback).
load_dotenv(INTERIOR_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("ERROR: GEMINI_API_KEY not found in INTERIOR-AI/.env (see .env.example)")

from google import genai
from google.genai import types

USAGE_FILE = INTERIOR_ROOT / ".gemini_usage.json"   # project-local daily-cost counter
MODELS = {"flash": "gemini-2.5-flash", "pro": "gemini-2.5-pro"}

# Fixed rubrics. Each dimension scored 0-5 (0 = broken, 5 = genuinely publishable /
# a professional would sign it). The critic is told to be STINGY — 5 is rare.
RUBRIC = {
    "render": [
        ("palette_coherence",      "One controlled colour/material story, or does it clash?"),
        ("lighting_quality",       "Layered/intentional light with mood + shadow, or flat & evenly lit?"),
        ("composition",            "Framed inside a believable space, or floating / dead-centre catalogue shot?"),
        ("furniture_realism",      "Real, believable furniture, or PRIMITIVE boxes/blocks (the AI-geometry tell)?"),
        ("room_context",           "A real room (walls, window, ceiling, context), or a subject in an empty VOID?"),
        ("styling_and_life",       "Layered styling that feels lived-in (art, plants, textiles), or sterile & bare?"),
        ("proportion_and_scale",   "Believable proportions/scale, or awkward, oversized or mismatched pieces?"),
        ("photoreal_believability","Reads as a real photograph, or obviously CG / rendered?"),
    ],
    "plan": [
        ("line_weight_hierarchy",  "Walls heaviest -> annotation lightest, readable hierarchy? Or all one weight?"),
        ("annotation_legibility",  "Labels & dimensions readable and NOT COLLIDING/overlapping?"),
        ("symbol_clarity",         "Doors/windows/furniture read as standard architectural symbols, or plain boxes?"),
        ("sheet_composition",      "Balanced, titled, scale bar, professional sheet? Or cramped/amateur?"),
        ("dimensioning",           "Dimensions complete, chained, and clear?"),
        ("overall_professionalism","Would a working designer/contractor accept this as a real drawing?"),
    ],
}

VERDICTS = ["SHIP", "REWORK", "PLACEHOLDER_ONLY", "NOT_CLIENT_READY"]


def _detect_kind(path: str) -> str:
    n = os.path.basename(path).lower()
    if any(k in n for k in ("plan", "rcp", "elev", "schedule", "sheet")):
        return "plan"
    return "render"


def _prompt(kind: str) -> str:
    dims = RUBRIC[kind]
    dim_lines = "\n".join(f'  - "{k}": {desc}' for k, desc in dims)
    what = ("a photorealistic 3D interior render" if kind == "render"
            else "a 2D architectural floor plan / construction drawing")
    return f"""You are a BRUTALLY HONEST, independent interior-design critic reviewing {what}.
You did NOT create this image and have ZERO stake in it. Your job is to find what is WRONG.
Default to skepticism: most machine-generated interiors are mediocre, and a self-serving grader
would call this "fine" — do not be that grader. Be specific and unsparing.

Score EACH dimension 0-5 (0 = broken/unacceptable, 3 = passable but flawed, 5 = genuinely
PUBLISHABLE — a professional would put their name on it). Be STINGY: reserve 4-5 for real
professional quality. If a piece of furniture looks like a primitive box, if the subject floats
in an empty void, if the lighting is flat, or if labels collide — those are serious defects and
must pull scores DOWN and appear in "top_defects".

Dimensions to score:
{dim_lines}

Return ONLY valid JSON, no prose, exactly this shape:
{{
  "scores": {{ {", ".join(f'"{k}": <0-5 int>' for k, _ in dims)} }},
  "overall_0_5": <number, your honest overall, NOT just the mean>,
  "verdict": "<one of: {' | '.join(VERDICTS)}>",
  "top_defects": ["<specific concrete flaw>", "..."],
  "one_line": "<a single brutally honest sentence a critic would say out loud>",
  "if_client_deliverable": "<is this acceptable to hand a paying client? why / why not>"
}}
Verdict guide: SHIP = publishable as-is; REWORK = real defects, fix before use;
PLACEHOLDER_ONLY = fine as a rough massing/draft but NOT a client deliverable;
NOT_CLIENT_READY = do not put this in front of a paying client."""


def _bump_usage():
    today = str(date.today())
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8")) if USAGE_FILE.exists() else {}
    except Exception:
        data = {}
    if data.get("date") != today:
        data = {"date": today, "flash": 0, "pro": 0, "thinking": 0, "deep": 0, "vision": 0}
    data["vision"] = data.get("vision", 0) + 1
    try:
        USAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip().rstrip("`").strip()
    return json.loads(t)


def critique(path: str, kind: str, model_key: str = "flash") -> dict:
    img = Path(path).read_bytes()
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    client = genai.Client(api_key=GEMINI_API_KEY)
    _bump_usage()
    resp = client.models.generate_content(
        model=MODELS[model_key],
        contents=[types.Part.from_bytes(data=img, mime_type=mime), _prompt(kind)],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    result = _parse_json(resp.text)
    result["_artifact"] = os.path.basename(path)
    result["_kind"] = kind
    result["_model"] = MODELS[model_key]
    return result


def render_report(r: dict) -> str:
    lines = [f"\n=== CRITIQUE: {r['_artifact']}  ({r['_kind']}, {r['_model']}) ==="]
    for k, v in r.get("scores", {}).items():
        bar = "#" * int(round(float(v))) + "." * (5 - int(round(float(v))))
        lines.append(f"  {v}/5  [{bar}]  {k}")
    lines.append(f"  ----")
    lines.append(f"  OVERALL: {r.get('overall_0_5')}/5   VERDICT: {r.get('verdict')}")
    lines.append(f"  \"{r.get('one_line', '')}\"")
    if r.get("top_defects"):
        lines.append("  DEFECTS:")
        for d in r["top_defects"]:
            lines.append(f"    - {d}")
    lines.append(f"  CLIENT-READY? {r.get('if_client_deliverable', '')}")
    return "\n".join(lines)


def run_batch(paths, kind="auto", model_key="flash"):
    """Critique several artifacts; never raises (a failed call becomes an ERROR verdict
    so it can NEVER silently pass). Returns a list of result dicts."""
    out = []
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        k = _detect_kind(p) if kind == "auto" else kind
        try:
            out.append(critique(p, k, model_key))
        except Exception as e:
            out.append({"_artifact": os.path.basename(p), "_kind": k, "scores": {},
                        "overall_0_5": None, "verdict": "ERROR", "top_defects": [],
                        "one_line": f"critique call failed: {type(e).__name__}: {e}",
                        "if_client_deliverable": "unknown — critic did not run"})
    return out


# Verdicts that mean "an independent critic says this is NOT ready for a paying client".
NOT_READY = {"REWORK", "PLACEHOLDER_ONLY", "NOT_CLIENT_READY", "ERROR"}


def to_markdown(results) -> str:
    """A CRITIQUE.md that travels WITH the deliverable, so the human reviewer sees the
    independent verdict next to the QA sign-off."""
    P = ["# MACHINE CRITIQUE — independent vision critic (non-blocking)", "",
         "_An independent Gemini-vision critic scored these artifacts against a fixed rubric, "
         "prompted to find what is WRONG, with **no stake** in defending the output. This is a "
         "FLOOR, not the human designer's final taste call. A `NOT_CLIENT_READY` / "
         "`PLACEHOLDER_ONLY` verdict means: do not hand this to a paying client as a deliverable._", ""]
    for r in results:
        P.append(f"## {r.get('_artifact')} — **{r.get('verdict')}** (overall {r.get('overall_0_5', '?')}/5)")
        P.append(f"> {r.get('one_line', '')}")
        P.append("")
        if r.get("scores"):
            P.append("| dimension | score |"); P.append("|---|---|")
            for k, v in r["scores"].items():
                P.append(f"| {k} | {v}/5 |")
            P.append("")
        if r.get("top_defects"):
            P.append("**Defects:**")
            for d in r["top_defects"]:
                P.append(f"- {d}")
            P.append("")
        if r.get("if_client_deliverable"):
            P.append(f"**Client-ready?** {r['if_client_deliverable']}")
            P.append("")
    return "\n".join(P)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="INTERIOR-AI honest self-critique gate (vision).")
    ap.add_argument("image")
    ap.add_argument("--kind", choices=["auto", "render", "plan"], default="auto")
    ap.add_argument("--model", choices=["flash", "pro"], default="flash")
    ap.add_argument("--out", default=None, help="write the critique JSON here (default: <image>.critique.json)")
    args = ap.parse_args()
    if not os.path.exists(args.image):
        sys.exit(f"not found: {args.image}")
    kind = _detect_kind(args.image) if args.kind == "auto" else args.kind
    r = critique(args.image, kind, args.model)
    print(render_report(r))
    outp = args.out or (os.path.splitext(args.image)[0] + ".critique.json")
    Path(outp).write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[saved] {outp}", file=sys.stderr)
