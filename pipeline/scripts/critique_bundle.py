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


# --- R7c: the C2 rung's blindness is a property of the ASK -------------------
# EARNED 2026-08-08 on the r35 bundle. C2 and C3 were fired IN PARALLEL into one
# directory, so `ANSWER_gemini25pro.md` was sitting in the folder the C2 agent
# had been pointed at while it was reading. The agent reported it never opened
# the file and its items do not track C3's, so nothing is known to be
# contaminated — and that is exactly the problem. R7c replaced the Cowork rung
# with a bundle-scoped local agent BECAUSE a spawned subagent can be handed
# anything, so blindness had to be enforced by what the ask CONTAINS. Compliance
# restored the outcome; it did not restore the architecture.
#
# So the ask stops being "the bundle dir" and becomes a dir that provably holds
# two files. Whatever else lands in the bundle afterwards — a second critic's
# answer, a triage, a README — cannot be reached by an ask that names this dir,
# because there is nothing else in it. The render is hard-linked where the
# filesystem allows it, so the guarantee costs no bytes.
C2_ASK = "c2-ask"
# Named, not inlined, so `assert_blind` can refuse it by name if it ever turns up
# inside the blind ask (see the OWNER_NOTE comment for what it is doing here).
OWNER_NOTE_NAME = "OWNER-NOTE-not-part-of-the-ask.md"
C2_ASK_NOTE = """This directory IS the C2 ask (R7c). It holds the render and the
standing cold-critic prompt, and nothing else, by construction — see
`critique_bundle.assert_blind`. Point the fresh-context agent HERE, never at the
bundle root: the bundle root also holds the other critics' answers, and a judge
shown another judge's answer stops being a judge.
"""


def _link_or_copy(src, dst):
    """Hard-link when the filesystem allows it; copy otherwise. Same bytes either
    way — the point is that the ask dir holds a real render, not a pointer a
    reader could follow back into the bundle."""
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except (OSError, AttributeError, NotImplementedError):
        shutil.copy2(src, dst)


def c2_ask_dir(bundle_dir, render_name=None):
    """Create/refresh <bundle>/c2-ask/ holding EXACTLY the render + PROMPT.md.

    Refreshing DELETES anything else that has appeared in it. A dir that merely
    started blind is the discipline story again; this one is blind every time it
    is asked for."""
    if render_name is None:
        pngs = sorted(p for p in os.listdir(bundle_dir) if p.lower().endswith(".png"))
        if len(pngs) != 1:
            raise RefusedError(
                f"{bundle_dir!r} holds {len(pngs)} PNGs — the C2 ask carries exactly "
                f"one render, so name it explicitly rather than guessing")
        render_name = pngs[0]
    src = os.path.join(bundle_dir, render_name)
    prompt = os.path.join(bundle_dir, "PROMPT.md")
    for p in (src, prompt):
        if not os.path.exists(p):
            raise RefusedError(f"cannot build a blind C2 ask: {p!r} is missing")
    ask = os.path.join(bundle_dir, C2_ASK)
    os.makedirs(ask, exist_ok=True)
    keep = {render_name, "PROMPT.md", "README.md"}
    for name in os.listdir(ask):
        if name not in keep:
            p = os.path.join(ask, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    _link_or_copy(src, os.path.join(ask, render_name))
    shutil.copy2(prompt, os.path.join(ask, "PROMPT.md"))
    with open(os.path.join(ask, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(C2_ASK_NOTE)
    assert_blind(ask)
    return ask


def assert_blind(ask_dir):
    """Raise unless the ask dir holds one render, PROMPT.md and its own note.

    An ANSWER file here is the failure this exists to make impossible, so it is
    named in the message rather than lumped in with 'unexpected file'."""
    if not os.path.isdir(ask_dir):
        raise RefusedError(f"no C2 ask dir at {ask_dir!r}")
    names = sorted(os.listdir(ask_dir))
    pngs = [n for n in names if n.lower().endswith(".png")]
    extra = [n for n in names if n not in set(pngs) | {"PROMPT.md", "README.md"}]
    if len(pngs) != 1 or "PROMPT.md" not in names or extra:
        answers = [n for n in extra if n.upper().startswith(("ANSWER", "TRIAGE"))]
        raise RefusedError(
            f"C2 ask dir {ask_dir!r} is not blind: {len(pngs)} render(s), "
            f"PROMPT.md {'present' if 'PROMPT.md' in names else 'MISSING'}, "
            f"extra {extra}." + (f" {answers} is another rung's work — R7c: a judge "
                                 f"shown the answer stops being a judge." if answers else ""))
    return ask_dir


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
"""

# THE ROUND NOTE LIVES OUTSIDE THE BUNDLE, and this filename is the whole fix.
#
# It used to be appended to README.md as "## หมายเหตุรอบนี้", one directory above the
# render — and on 2026-08-26 the C2 critic opened it and said so in its own verdict:
# *"README.md contains a line naming what this round changed. I read it before opening
# the image and deliberately used none of it — but a bundle built for a blind rung
# should not carry that line."* It was right, and the blind sub-directory (`c2-ask/`)
# that exists precisely to prevent this did prevent nothing, because the ASK NAMED THE
# PARENT DIRECTORY. R7c's law is that blindness is enforced by the ASK'S CONSTRUCTION;
# a construction that only works when the spawner types the right path is a procedure,
# not a construction.
#
# So the note stops living anywhere a critic can wander into. It goes to a file the
# blind reader has no reason to open and whose name says who it is for, and README.md
# keeps only the paste ritual, which is the same for every round and tells a judge
# nothing about this one.
OWNER_NOTE = """# หมายเหตุรอบนี้ — สำหรับเจ้าของ/ผู้ triage เท่านั้น

ไฟล์นี้ **ไม่ใช่ส่วนหนึ่งของ ask** ทั้ง C2 (fresh-context local) และ C3 (Gemini)
ตัดสินจาก render + PROMPT.md เท่านั้น — กรรมการที่เห็นเฉลยไม่ใช่กรรมการอีกต่อไป

{note}
"""


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
        fh.write(README.format(render=os.path.basename(render)))
    if note:
        with open(os.path.join(d, OWNER_NOTE_NAME), "w", encoding="utf-8") as fh:
            fh.write(OWNER_NOTE.format(note=note))
    c2_ask_dir(d, os.path.basename(render))
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
