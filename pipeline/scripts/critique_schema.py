"""critique_schema.py — A CRITIQUE IS A NUMBERED LIST, NOT PROSE. PURE (no bpy).

    python pipeline/scripts/critique_schema.py ANSWER_*.md --stage lighting

WHY THIS FILE EXISTS — T7, ordered 2026-08-29 ("ทำให้หมดเลย"), owed since 08-08
--------------------------------------------------------------------------------
The 08-08 deep read of SEIG ("Thinking in Blender", He, Luo, Ma & Averbuch-Elor,
Cornell, arXiv 2606.02580) produced two findings. T6 was built the same day and
became `coverage_check.py`. **T7 was not**, and it is the half that governs how a
critic ANSWERS:

    SEIG's verifier returns a NUMBERED, STAGE-SCOPED CHECKLIST of discrepancies.
    Ours asks for free prose.

Three things follow from prose, all of them measured in this repo's own critique
corpus (367 items across C2 and C3):

  1. **Items cannot be counted, so they cannot be tracked.** R7 says every critic
     item gets a written triage — accept+lane, or refute WITH A MEASUREMENT. An
     unnumbered paragraph containing three complaints gets one triage line, and
     two of the three are gone. Nobody can tell afterwards.
  2. **Items cannot be routed.** SEIG scopes each verifier to one stage so it
     "judges only the active factor … while ignoring errors assigned to other
     stages", precisely because "errors introduced in early stages may propagate
     throughout the pipeline, leading to local minima from which later stages
     cannot easily recover." Thirty rounds of material work on a wall that should
     have had a doorway is that sentence, already paid for once here.
  3. **And the most useful signal in the whole ladder is invisible without it.**
     If a LIGHTING round keeps collecting GEOMETRY items, the round is being run
     on a broken foundation and should stop (R1 Andon: stopping is the correct
     move). That is a ratio, and a ratio needs countable, tagged items. With
     `--stage`, this checker computes it and FAILS the round when the majority of
     what the critic saw belongs to a stage upstream of the one being worked.

FRAME-ANCHORED, which is the other half. The spatial-reasoning literature's own
mitigation — ViSA, Verification through Spatial Assertions — grounds checks in
"verifiable, frame-anchored micro-claims". So every item must say WHERE in frame,
not only what. "The lighting feels flat" cannot be verified, actioned, or refuted
with a measurement; "the floor under the island, lower-left third, has no contact
shadow" can be all three.

WHAT IT REFUSES
    * an answer with no numbered items                 -> that is prose
    * numbering with gaps or duplicates                -> items were lost
    * an item with no `stage:` from the SEIG five      -> unroutable
    * an item with no `where:`                         -> unverifiable
    * an item with no `ground:` of reference|physics|opinion   (R7's own law)
    * an item with no `sellability:` rank              -> R7 ranks by client harm
    * with --require-triage, an item with no `triage:` -> R7's mandatory written
      triage, which prose has been quietly skipping

WHAT IT DOES NOT DO. It does not judge whether an item is TRUE. A critic's items
are still judged by the builder's triage and by him. This rung only makes sure
that what came back can be counted, routed, and answered one by one — which is
the difference between a critique and an impression.
"""
import argparse
import os
import re
import sys


# SEIG's stage order. A round works one of these; items are tagged to the stage
# that OWNS the defect, which is often not the stage being worked.
STAGES = ["scaffolding", "geometry", "materials", "composition", "lighting"]
STAGE_NOTE = {
    "scaffolding": "the room shell, its openings, and what exists at all",
    "geometry": "the shape, size and orientation of a mass",
    "materials": "surface, colour, roughness, believability of a finish",
    "composition": "arrangement, styling density, what sits where (and framing)",
    "lighting": "key/fill, shadow, contact, mood",
}
GROUNDS = ["reference", "physics", "opinion"]
SELL = ["high", "medium", "low"]
FIELDS = {"stage": STAGES, "ground": GROUNDS, "sellability": SELL}

ITEM_RE = re.compile(r"^\s{0,3}(\d+)\.\s+(.*)$")
FIELD_RE = re.compile(r"(?:^|[\s(*_·|-])(%s)\s*:\s*([A-Za-z_-]+)" %
                      "|".join(list(FIELDS) + ["where", "triage"]), re.I)


def parse(text):
    """-> [{n, head, body, fields}] in file order. An item runs to the next number."""
    items, cur = [], None
    for line in text.splitlines():
        m = ITEM_RE.match(line)
        if m:
            if cur:
                items.append(cur)
            cur = {"n": int(m.group(1)), "head": m.group(2).strip(), "body": []}
            continue
        if cur is not None:
            cur["body"].append(line)
    if cur:
        items.append(cur)
    for it in items:
        blob = it["head"] + "\n" + "\n".join(it["body"])
        it["text"] = blob
        it["fields"] = {}
        for key, val in FIELD_RE.findall(blob):
            it["fields"].setdefault(key.lower(), val.strip().lower())
        # `where:` is free text, so take the rest of its line rather than one token
        w = re.search(r"where\s*:\s*(.+)", blob, re.I)
        if w:
            it["fields"]["where"] = w.group(1).strip()
        t = re.search(r"triage\s*:\s*(.+)", blob, re.I)
        if t:
            it["fields"]["triage"] = t.group(1).strip()
    return items


def audit(text, stage=None, require_triage=False):
    """-> (items, violations, stage_report). Pure."""
    items = parse(text)
    viol = []
    if not items:
        viol.append(
            "no numbered items — this answer is PROSE. A critique that cannot be "
            "counted cannot be triaged one by one, and R7 requires a written triage "
            "for every item. Return `1.` `2.` `3.` …")
        return items, viol, {}

    ns = [i["n"] for i in items]
    for want, got in zip(range(1, len(ns) + 1), ns):
        if want != got:
            viol.append(f"numbering breaks at {got} (expected {want}) — a gap or a "
                        f"duplicate means an item was lost between the critic and the "
                        f"triage, and nobody can tell which")
            break

    for it in items:
        for key, allowed in FIELDS.items():
            v = it["fields"].get(key)
            if v is None:
                viol.append(f"item {it['n']}: no `{key}:` — "
                            + ("unroutable: which stage owns this defect?"
                               if key == "stage" else
                               "R7 needs it" if key == "ground" else
                               "R7 ranks by client harm, not by ease of fix"))
            elif v not in allowed:
                viol.append(f"item {it['n']}: `{key}: {v}` is not one of {allowed}")
        if not it["fields"].get("where"):
            viol.append(
                f"item {it['n']}: no `where:` — an item with no place in frame cannot "
                f"be verified, actioned, or refuted with a measurement. Frame-anchored "
                f"micro-claims are the whole mitigation")
        if require_triage and not it["fields"].get("triage"):
            viol.append(f"item {it['n']}: no `triage:` — R7 requires accept+lane or a "
                        f"refutation carrying a MEASUREMENT, never taste, for EVERY item")

    tally = {s: 0 for s in STAGES}
    for it in items:
        s = it["fields"].get("stage")
        if s in tally:
            tally[s] += 1
    rep = {"tally": tally, "n": len(items)}
    if stage:
        if stage not in STAGES:
            viol.append(f"--stage {stage} is not one of {STAGES}")
        else:
            idx = STAGES.index(stage)
            upstream = sum(tally[s] for s in STAGES[:idx])
            rep["upstream"] = upstream
            rep["stage"] = stage
            if upstream * 2 > len(items):
                viol.append(
                    f"ANDON: {upstream} of {len(items)} items belong to stages UPSTREAM "
                    f"of `{stage}` ({', '.join(STAGES[:idx])}). This round is being run "
                    f"on a foundation the critic can see is wrong; more work at this "
                    f"stage cannot recover it. STOP and go back (R1 — stopping is the "
                    f"correct move, never an admission)")
    return items, viol, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answer", help="the critic's ANSWER_*.md")
    ap.add_argument("--stage", default="", help="the stage this round is working; "
                                                "enables the upstream-items Andon")
    ap.add_argument("--require-triage", action="store_true")
    ap.add_argument("--soft", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not os.path.exists(a.answer):
        print(f"CRITIQUE SCHEMA: no answer at {a.answer} — a rung that could not run "
              f"must never print like a rung that passed")
        return 0 if a.soft else 2
    text = open(a.answer, encoding="utf-8", errors="replace").read()
    items, viol, rep = audit(text, a.stage or None, a.require_triage)
    print(f"CRITIQUE SCHEMA: {len(items)} numbered items in "
          f"{os.path.basename(a.answer)}")
    if rep.get("tally"):
        print("  by stage: " + ", ".join(f"{s}={rep['tally'][s]}" for s in STAGES))
    if "upstream" in rep:
        print(f"  {rep['upstream']} of {rep['n']} belong upstream of `{rep['stage']}`")
    if viol:
        print(f"CRITIQUE SCHEMA VIOLATIONS ({len(viol)}):")
        for v in viol:
            print("  - " + v)
        return 0 if a.soft else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
