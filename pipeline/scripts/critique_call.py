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


def prompt_body(text):
    """Everything the JUDGE is meant to read — the text below the first `---`.

    THE API PATH MUST SEND WHAT THE PASTE PATH SENDS, and until r38 it did not.
    Every bundle README tells the owner to paste *"ทุกบรรทัดใน PROMPT.md (ใต้เส้น
    คั่น)"* — below the separator. `critique_call` sent the WHOLE file, and the
    part above the separator is an HTML comment addressed to the operator that
    carries build history by its nature: which C2 run caught which defect on
    which round, which rungs exist, what a previous prompt got wrong. **That is
    exactly the context R7 exists to keep away from the judge.** The rung's whole
    claim is that the critic does not know how the work was made, and the
    automated half of it had been quietly telling him.

    It surfaced as a false refusal rather than as a leak: the comment explains
    that the bundle *"refuses target/anchors by code"*, the word `anchor` is in
    FORBIDDEN, and so the guard blocked r38's C3 on the prompt's own description
    of the privacy rule. Widening the pattern would have been the wrong repair —
    the pattern was right and the payload was wrong.

    No separator: return the text unchanged. A prompt with no operator preamble
    is all body, and inventing a split would be worse than sending one comment.
    """
    # Index arithmetic rather than splitlines(), so the body comes back BYTE FOR
    # BYTE as it sits under the separator — a rejoin quietly eats the trailing
    # newline, and "what is sent" must mean what is on disk.
    pos = 0
    for line in text.splitlines(keepends=True):
        pos += len(line)
        if line.strip() == "---":
            return text[pos:].lstrip("\n")
    return text


def png_size(path):
    """(w, h) from the IHDR, or None. Stdlib — a 24-byte read, no decode."""
    try:
        head = path.read_bytes()[:24]
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"))


def declare_mode(render):
    """Tell the judge whether it is looking at a playblast, DERIVED FROM PIXELS.

    EARNED 2026-08-08, and it cost a whole C3 turn. r34's bundle went out as a
    540x410 frame — R5's `--quick` rung, half res per axis and 64 samples — and
    Gemini's number-one item, its "if you fix only one thing" item, was that the
    image is blurry and looks unfinished. It was right, and about the playblast
    rather than the work: measured at the size a viewer sees, the quick frame
    carries 0.17x the high-frequency energy of this lane's full frames.

    That is not a one-off. R7b fires C3 on EVERY render and R5 says the quick
    frame comes first, so the standing procedure guaranteed a wasted top slot on
    every playblast, forever. A judge cannot discount what it was not told.

    Derived from the pixel counts on disk, never from the filename: this lane
    has 137 PNGs without a `_quick` token of which only 44 are full frames, so
    a name-based test would mislabel three frames in four. The comparison size
    is the largest render sitting beside it, which is what "full" means here.
    """
    size = png_size(render)
    if not size:
        return ""
    # Search the bundle dir AND its ancestors: the lane's frames live two levels
    # up (renders/ -> critique/ -> the bundle). The first version globbed one
    # level only, found no peers, and therefore declared a 540x410 playblast to
    # be full-fidelity — this function's own failure mode, in its first run.
    peers = [s for anc in [render.parent, *render.parents[:3]]
             for s in (png_size(p) for p in anc.glob("*.png")) if s]
    full = max(peers, key=lambda wh: wh[0] * wh[1]) if peers else size
    if size[0] * size[1] >= full[0] * full[1]:
        return (f"**MODE: full-fidelity frame, {size[0]}x{size[1]} px.** "
                f"ตัดสินได้ทุกมิติรวมทั้งความคมและ noise\n\n")
    return (
        f"**MODE: PLAYBLAST — {size[0]}x{size[1]} px, ครึ่งความละเอียดต่อแกน "
        f"64 samples. เฟรมส่งจริงของเลนนี้คือ {full[0]}x{full[1]} px.**\n"
        f"ภาพนี้จงใจ render หยาบเพื่อดูโครงเร็ว ๆ **อย่าเสียข้อวิจารณ์ไปกับความคมชัด "
        f"noise ความละเอียด หรือ 'ดูเหมือน render ไม่เสร็จ'** — ทั้งหมดนั้นเป็นผลของ "
        f"โหมด ไม่ใช่ของงาน และเรารู้อยู่แล้ว\n"
        f"สิ่งที่ playblast ตอบได้จริงและเราต้องการ: **วัตถุมีอะไรขาด/เกิน · สัดส่วนและ "
        f"ขนาด · ตำแหน่งและการสัมผัสพื้น · องค์ประกอบภาพ · ทิศทางและความสมเหตุสมผล "
        f"ของแสง · ของชิ้นไหนที่ไม่น่าจะสร้างได้จริง**\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", help="bundle dir name, e.g. critique-trn002_blockout_r2")
    ap.add_argument("--model", default="pro", choices=list(MODELS))
    a = ap.parse_args()

    # Since the training/ split (2026-08-04) a bundle is TWO mirrored dirs:
    # binaries stay under _private/**, text (PROMPT/ANSWER/README) lives under
    # training/**. Resolve both; the answer archives on the text side.
    hits = [p for p in REPO.glob(f"_private/**/critique/{a.bundle}") if p.is_dir()]
    text_hits = [p for p in REPO.glob(f"training/**/critique/{a.bundle}") if p.is_dir()]
    if not hits and len(text_hits) == 1:
        # A TRAINING LANE WHOSE RENDER IS NOT UNDER _private IS STILL A VALID BUNDLE.
        # The two-directory split exists because the DELIV lane's binaries are the
        # friend's delivered client work and may never be committed. A training lane
        # reproducing a PUBLIC magazine photograph has no such binary: its renders sit
        # under training/ and are gitignored there by .gitignore:52, which is the same
        # protection by a different route. Refusing this bundle sent the operator off to
        # call the API by hand, which is exactly how a guard stops being used.
        bundle = text_dir = text_hits[0]
    else:
        if len(hits) != 1:
            sys.exit(f"bundle '{a.bundle}' matched {len(hits)} render dirs — need exactly 1")
        bundle = hits[0]
        text_dir = text_hits[0] if len(text_hits) == 1 else bundle
    render = bundle / (a.bundle.replace("critique-", "") + ".png")
    if not render.exists():
        sys.exit(f"bundle render {render.name} missing — the ONLY image allowed out")
    prompt_path = text_dir / "PROMPT.md"
    if not prompt_path.exists():
        prompt_path = bundle / "PROMPT.md"
    # SCAN WHAT IS SENT, not what is on disk. Scanning the operator preamble was
    # how this guard produced a false refusal on the prompt's own account of the
    # privacy rule — and a guard that blocks a clean send teaches the operator to
    # route around it, which is worse than the leak it was protecting against.
    prompt = prompt_body(prompt_path.read_text(encoding="utf-8"))
    m = FORBIDDEN.search(prompt)
    if m:
        sys.exit(f"PROMPT.md contains forbidden reference '{m.group(0)}' — refusing to send")
    prompt = declare_mode(render) + prompt

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
