"""gen_diff.py — the GEN-DIFF diagnostic (owner idea, approved "ลุย" 2026-08-13):
Gemini image-gen produces "what this frame wants to be" variants FROM our own
render, and the builder then extracts the deltas as named, measurable gaps.

WHY THIS EXISTS: the owner's exact words — "ผมว่าภาพ render เรายังขาดอะไรอีกเยอะ
แต่ผมก็บอกไม่ได้ว่าขาดอะไร". The most expensive verdict class is a QUALITY with
no object ("ยังดูแปลก"); a generated variant converts it into pixels that can be
pointed at and measured, the same move as the 2026-07-30 ground-truth .blend
study (which produced the map-coverage / light-range / f-stop numbers driving
P2), with a generated sample standing in for the .blend.

TWO LOCKED CONDITIONS (recorded here so the tool itself carries them):
 1. A variant is a HYPOTHESIS GENERATOR, never a target. Its beauty is Gemini's
    generic-archviz prior, not the sellability anchor — every extracted gap must
    be cross-checked against the anchor pool before it becomes a work item
    (the blind-critic history: priors prescribed downlight pools for a room
    measured to have none). Anchors judge; NOTHING dictates (R4b).
 2. Geometry/structure deltas are NOISE by law — our geometry is bound to the
    drawing of record (R12, sheet outranks everything). Only surface / light /
    styling deltas survive the filter.

WHAT MAY TRAVEL: exactly one image, OUR OWN render (same egress class as R7b's
C3, which already sends every render out). Target/anchors/client data NEVER —
refused by path scan, same law as critique_call.

  python pipeline/scripts/gen_diff.py <render.png> [--n 3] [--model gemini-3-pro-image]

Variants + MANIFEST land in _private/deliv-001/gen-diff/<render-stem>/
(gitignored: diagnostic samples, not deliverables — the extracted FINDINGS go
into the round's gate artifact, which is the committed surface)."""
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FORBIDDEN = re.compile(r"target|anchor|clients[\\/]|_private[\\/]", re.I)

# Three distinct prompt ANGLES rather than one prompt resampled — diverse
# hypotheses are the point (the multi-modal-sweep pattern). All three pin the
# composition so the diff stays on the axes the filter keeps.
ANGLES = [
    ("photo", "Make this exact frame look like a professional interior "
              "photograph for a high-end residential portfolio. Keep the same "
              "room, same camera position, same furniture, same layout and the "
              "same material palette — change only what a photographer and "
              "stylist would: light, texture realism, soft-goods state, small "
              "styling touches."),
    ("editorial", "Turn this exact frame into an editorial interior shot as "
                  "styled for a design magazine. Do not move walls, furniture "
                  "or the camera; keep the material palette. Improve lighting "
                  "mood, fabric and surface realism, and add only small "
                  "believable styling props."),
    ("archviz", "Render this exact scene as a final-quality photorealistic "
                "archviz frame. Same geometry, same camera, same furniture and "
                "palette — refine surface micro-texture, light falloff, "
                "contact shadows and soft-goods realism only."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--model", default="gemini-3-pro-image")
    a = ap.parse_args()

    render = Path(a.render).resolve()
    rel = str(render)
    if FORBIDDEN.search(rel.replace(str(REPO), "")):
        sys.exit(f"refusing: {render} is not a plain render of ours")
    if not render.exists():
        sys.exit(f"render missing: {render}")

    out_dir = REPO / "_private" / "deliv-001" / "gen-diff" / render.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    from dotenv import load_dotenv
    import os
    load_dotenv(REPO / ".env")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY not in repo .env")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key)

    src = render.read_bytes()
    made, lines = 0, []
    for k in range(a.n):
        tag, prompt = ANGLES[k % len(ANGLES)]
        try:
            resp = client.models.generate_content(
                model=a.model,
                contents=[types.Part.from_bytes(data=src, mime_type="image/png"),
                          prompt],
            )
        except Exception as e:              # one variant failing must not kill the rest
            lines.append(f"- variant-{k + 1} ({tag}): CALL FAILED — {e}")
            continue
        img = None
        for cand in (resp.candidates or []):
            for part in (cand.content.parts or []):
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    img = part.inline_data.data
                    break
            if img:
                break
        if not img:
            lines.append(f"- variant-{k + 1} ({tag}): NO IMAGE IN RESPONSE "
                         f"(text: {(resp.text or '')[:120]!r})")
            continue
        p = out_dir / f"variant-{k + 1}-{tag}.png"
        p.write_bytes(img)
        made += 1
        lines.append(f"- variant-{k + 1} ({tag}): {p.name} ({len(img)} bytes)")

    manifest = out_dir / "MANIFEST.md"
    manifest.write_text(
        f"# gen-diff — {render.name}\n\n"
        f"- date: {date.today().isoformat()}\n"
        f"- model: {a.model}\n"
        f"- source: {render.name} sha256 {hashlib.sha256(src).hexdigest()[:16]}\n"
        f"- sent: the source render ONLY (egress class = R7b C3)\n"
        f"- status: HYPOTHESIS SAMPLES, never targets — every extracted gap "
        f"must be cross-checked against the anchor pool before it becomes a "
        f"work item; geometry/structure deltas are noise by law (R12)\n\n"
        f"## Variants\n" + "\n".join(lines) + "\n\n"
        f"## Prompts\n" +
        "\n".join(f"- {t}: {p}" for t, p in ANGLES[:a.n]) + "\n",
        encoding="utf-8")

    usage = REPO / ".gemini_usage.json"
    try:
        data = json.loads(usage.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if data.get("date") != date.today().isoformat():
        # same reset schema as critique_call, so whichever tool rolls the date
        # first does not clobber the other's counters
        data = {"date": date.today().isoformat(), "flash": 0, "pro": 0,
                "thinking": 0, "deep": 0, "vision": 0}
    data["image_gen"] = data.get("image_gen", 0) + made
    usage.write_text(json.dumps(data, indent=2), encoding="utf-8")

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"{made}/{a.n} variants -> {out_dir.relative_to(REPO)}")
    print(manifest.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
