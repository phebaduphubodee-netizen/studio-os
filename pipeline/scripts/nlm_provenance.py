"""nlm_provenance.py — split a NotebookLM notebook's sources into RETRIEVABLE and SYNTHESISED.

    python pipeline/scripts/nlm_provenance.py <notebook-id-prefix> [--json]

WHY
---
A NotebookLM Deep Research writes its OWN synthesised report into the notebook as
a source, typed `MARKDOWN` with `url: null`. The answer then cites that report by
title, in the same format it cites a manufacturer datasheet or a standards page:

    (*"Computational Aesthetics and Perceptual Mechanics: What Separates
      Photorealistic Interiors from Synthetic Renders"* [cite: 71])

Read at speed, that is indistinguishable from a citation. It is not one. It is the
model's own prose, one hop removed, and in both notebooks fired on 2026-08-08 the
MOST-CITED "source" in the answer was exactly this. A number that traces only to
it has no external attribution at all and is quarantined under the same rule that
quarantines an unsourced Gemini value.

This is the NotebookLM half of a pair found the same morning; the Gemini half is
in `research_call.py` (a thinking budget silently disabling web search). Both
channels had a way of making unsourced content look sourced, and neither is
detectable by reading the answer — only by asking the vendor what the source IS.

So the staging step does not remember to check. It runs this.
"""
import argparse
import json
import subprocess
import sys


def sources(notebook):
    cp = subprocess.run(["notebooklm", "source", "list", "-n", notebook, "--json"],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=180)
    out = cp.stdout or ""
    # Warnings go to stdout on some builds; skip to the first JSON opener.
    starts = [i for i in (out.find("{"), out.find("[")) if i != -1]
    if not starts:
        sys.exit(f"no JSON from `source list` (rc={cp.returncode}): {(cp.stderr or '')[:200]}")
    d = json.loads(out[min(starts):])
    return d.get("sources", d if isinstance(d, list) else [])


def split(src):
    """Three classes, because there turned out to be three ways to not be a source.

    RETRIEVABLE  — has a url. Someone else's document, and we can go read it.
    SYNTHESISED  — MARKDOWN with no url: the DR's own report, written by the model.
    UPLOADED     — any other type with no url: a file a human put in the notebook.

    UPLOADED was added after the third finding of 2026-08-08. Asked about the
    "light story" of an interior photograph, notebook a5a43395 answered by citing
    `Automated Vision QA for Interiors.pdf` and `Knowledge Base Architecture for a
    World-Class AI Interior Design Studio Powered by Claude Code` — **both of them
    OUR OWN documents**, uploaded into that corpus earlier. The channel returned
    this studio's prior beliefs to it as grounding.

    That is the flattering-scorer failure this repo has pinned nine other shapes
    of, arriving in the research lane: an instrument that can only agree with you
    because you wrote its evidence. The doctrine "vault first, then NLM for the
    GAPS" silently assumes the notebook is EXTERNAL to the vault. For a corpus
    holding our own output, it is not, and no amount of careful reading of the
    ANSWER reveals it — only the source list does.

    So the tool splits on the mechanism (no url = we cannot go and check it),
    not on the instance.
    """
    syn, up, ret = [], [], []
    for s in src:
        t = str(s.get("type", ""))
        if s.get("url"):
            ret.append(s)
        elif t.endswith("MARKDOWN"):
            syn.append(s)
        else:
            up.append(s)
    return ret, syn, up


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ret, syn, up = split(sources(a.notebook))
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if a.json:
        print(json.dumps({"retrievable": ret, "synthesised": syn, "uploaded": up},
                         indent=2, ensure_ascii=False))
        return
    print(f"NOTEBOOK {a.notebook}: {len(ret)} retrievable, "
          f"{len(syn)} SYNTHESISED, {len(up)} UPLOADED")
    for s in syn:
        print(f"  [SYNTHESISED] {(s.get('title') or '')[:100]}")
    for s in up:
        print(f"  [UPLOADED]    {(s.get('title') or '')[:100]}")
    if syn:
        print("\nAny value whose only citation is a SYNTHESISED title has NO external "
              "source — it is the model's own report. Quarantine it or find the page.")
    if up:
        print("\nUPLOADED sources have no url and cannot be checked from here. Read the "
              "titles: if any of them is OUR OWN work, an answer citing it is this "
              "studio agreeing with itself, not evidence.")


if __name__ == "__main__":
    main()
