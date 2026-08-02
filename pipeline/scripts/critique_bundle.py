#!/usr/bin/env python3
"""critique_bundle.py — assemble the R7b designer-critique paste bundle. PURE (no bpy).

WHY THIS IS A SCRIPT AND NOT A HABIT (owner order 2026-08-02: "ใช้ gemini ตัวช่วย
วิเคราะห์และตัดสินในฐานะ designer หลังผล render ออกทุกครั้ง"). R7's cross-vendor rung
existed for two days, was scoped to "big gates", and fired exactly once — because
a rung that depends on the builder remembering to climb it is a rung the builder
skips on the rounds he is most sure of. This turns it into an artefact the render
step produces whether or not anyone feels like it.

WHAT IT REFUSES TO BUNDLE, AND WHY THAT IS THE POINT. Our own render goes out.
The TARGET image and the anchor pool never do — they are another studio's
delivered client work, so sending them is a privacy breach AND benchmark leakage
(a judge shown the answer stops being a judge). The path allowlist below is the
enforcement, not a convention: `_private/**/reproduction/**/target*`, anything
under an anchor/benchmark pool, and anything under `clients/` are hard-refused
even when the caller asks for them by name.

    python pipeline/scripts/critique_bundle.py <render.png> [--out DIR] [--note TEXT]

Writes <out>/critique-<stem>/ containing the render, PROMPT.md (the standing
cold-critic prompt, unedited) and README.md telling the owner exactly what to
paste where and what to bring back.
"""
import argparse
import os
import shutil
import sys

PROMPT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "templates", "cold-critic-prompt.md")

# A path matching any of these never enters a bundle. Substring match on the
# POSIX-normalised, lowercased path so a Windows separator cannot slip one past.
NEVER_SEND = (
    "/clients/",
    "/target",
    "/anchor",
    "/look-bench/",
    "/golden-set/",
    "_target.",
)


class RefusedError(ValueError):
    """A bundle that would carry someone else's client work. Raised, never warned."""


def check_sendable(path):
    """Our render may go out. The benchmark may not. Raises rather than filtering,
    because a bundle silently missing a file reads as a bundle that was built."""
    p = os.path.abspath(path).replace("\\", "/").lower()
    for bad in NEVER_SEND:
        if bad in p:
            raise RefusedError(
                f"refusing to bundle {path!r}: it matches {bad!r}. The target image "
                f"and the anchor pool are another studio's delivered client work — "
                f"sending them leaks a client AND shows the judge the answer. "
                f"Bundle OUR render only (R7b in CLAUDE.md).")
    if not p.endswith((".png", ".jpg", ".jpeg")):
        raise RefusedError(f"{path!r} is not an image; a critique bundle carries "
                           f"renders and nothing else")
    return path


README = """# ส่งให้ Gemini ตัดสินในฐานะ designer — R7b

**ทำทุกครั้งหลัง render ออก** (คำสั่งเจ้าของ 2026-08-02)

## วิธีใช้ (2 นาที)

1. เปิด Gemini
2. แนบไฟล์ **`{render}`** — ไฟล์เดียวเท่านั้น
3. วาง **ทุกบรรทัดใน `PROMPT.md`** (ใต้เส้นคั่น) เป็นข้อความ
4. เอาคำตอบกลับมาวางในแชท

## สิ่งที่ห้ามส่งเด็ดขาด

**ภาพ target และคลัง anchor ห้ามออกจากเครื่องนี้** — มันคืองานลูกค้าที่สตูดิโออื่น
ส่งมอบจริง การส่งออกไปคือทั้งการรั่วข้อมูลลูกค้า *และ* การทำให้กรรมการเห็นเฉลย
สคริปต์นี้ปฏิเสธไฟล์พวกนั้นให้อัตโนมัติแล้ว แต่อย่าแนบเองด้วยมือ

ห้ามพิมพ์ชื่อลูกค้า ที่อยู่ ขนาดห้อง หรือ path ของไฟล์ไปกับภาพ

## สิ่งที่จะเกิดขึ้นกับคำตอบ

ทุกข้อที่ Gemini ตอบมาจะได้ **triage เป็นลายลักษณ์อักษร** ตาม R7 —
รับแล้วเข้าเลนไหน หรือตีตกพร้อม **ตัวเลขที่วัดได้** ไม่มีการตีตกด้วยรสนิยม

และเกณฑ์การชั่งน้ำหนัก (R7b): **ตาบอกว่า "อะไร" ผิด เครื่องมือบอกว่า "เท่าไร"
และ "ปุ่มไหน"** — ถ้าสองอย่างขัดกันเรื่อง *มีปัญหาหรือไม่* ให้ตาชนะ
{note}"""


def build(render, out_dir, note=""):
    check_sendable(render)
    if not os.path.exists(PROMPT):
        raise FileNotFoundError(f"the standing prompt is missing: {PROMPT}")
    stem = os.path.splitext(os.path.basename(render))[0]
    d = os.path.join(out_dir, f"critique-{stem}")
    os.makedirs(d, exist_ok=True)
    shutil.copy2(render, os.path.join(d, os.path.basename(render)))
    shutil.copy2(PROMPT, os.path.join(d, "PROMPT.md"))
    with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(README.format(render=os.path.basename(render),
                               note=("\n## หมายเหตุรอบนี้\n\n" + note) if note else ""))
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description="R7b designer-critique paste bundle")
    ap.add_argument("render")
    ap.add_argument("--out", default=None,
                    help="default: a 'critique' dir beside the render")
    ap.add_argument("--note", default="", help="one line of round context for the owner")
    a = ap.parse_args(argv)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.render)), "critique")
    d = build(a.render, out, a.note)
    print(f"R7b bundle ready: {d}")
    print(f"  attach {os.path.basename(a.render)} to Gemini, paste PROMPT.md, "
          f"bring the answer back. Target/anchors are refused by construction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
