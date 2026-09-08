"""research_call.py — TEXT deep-research calls to Gemini for THIS studio.

CLI-ONLY: run by hand for grounded DR calls (the uncontaminated caller; BRAINDEAD/gemini_query.py carries a contaminated system prompt) — triage 2026-08-25.

  python pipeline/scripts/research_call.py --prompt-file Q.md --out docs/research/x.md \
      [--mode deep|pro|flash] [--tag slug]

WHY THIS EXISTS AND IS NOT `BRAINDEAD/scripts/gemini_query.py`
  That script is the sibling repo's research caller and its SYSTEM_PROMPT hard-codes
  "BTC perpetuals signal research" — every answer it returns is framed for a trading
  desk, and its DEEP mode ends with "IMPLICATIONS: … for BTC perpetuals signal
  research". Pointing it at an interior-render question does not merely waste a call,
  it CONTAMINATES the answer with the wrong consumer. The prompt is the instrument.

THREE LAWS ARE STRUCTURAL HERE, NOT REMEMBERED
  1. URL-OR-QUARANTINE. `knowledge/_inbox/DISTILLATION-LEDGER.md` records this
     vendor class fabricating prices and licences, so every number must carry the
     page it came from. The instruction is baked into the system prompt AND the
     grounding URIs are archived beside the answer, so a claim with no source is
     visible as such at staging time instead of being taken on faith.
  2. PRIVACY. Generic questions only. The prompt is refused if it names a client
     path, a project dir, the private anchor tree, or the reproduction target —
     same fence as `critique_call.py` and the NLM lane's guard.
  3. SPEND IS COUNTED. `.gemini_usage.json` is bumped per call, per mode, like
     every other paid channel in this repo.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODELS = {"deep": "gemini-2.5-pro", "pro": "gemini-2.5-pro", "flash": "gemini-2.5-flash"}

# What must never travel. Mirrors critique_call.FORBIDDEN plus the paths the NLM
# privacy rule names (`clients/`, `projects/`) — a research question has no
# legitimate reason to carry any of them.
FORBIDDEN = re.compile(
    r"target\.(jpg|png)|anchor[- _]?pool|_private[\\/]|clients[\\/]|projects[\\/]PRJ-",
    re.I,
)

SYSTEM = """You are a research assistant to an architectural-visualisation and interior
design studio. The consumer of your answer is a builder who will turn it into
numbers in a Blender scene and rows in a materials/lighting knowledge base, so
answers are useful in proportion to how measurable they are.

RULE ZERO — SEARCH, DO NOT RECALL. You have a web search tool. USE IT, for every
question, before answering. Answering an interior/material/lighting question from
memory produces confident, plausible, WRONG values — that failure has already been
caught twice in this studio's records, both times as fabricated prices and product
specifications. For every value you report, the URL you actually retrieved must
appear. If a search returns nothing usable, write "NO SOURCED VALUE FOUND" — that
is a correct answer and is more valuable than a remembered number.

RULES, in priority order:
1. EVERY numeric value, band, or product/standard claim MUST carry the source it
   came from — a URL, or a named standard/section, or an author+title+year. A
   number with no attribution is worse than no number, because it will be read as
   measured. If you cannot source a value, say "NO SOURCED VALUE FOUND" for that
   item and continue; that is a valid and useful answer.
2. Distinguish MEASURED values (from a manufacturer datasheet, a standard, a
   scanned material library, a peer-reviewed measurement) from PRACTICE
   CONVENTIONS (what practitioners typically do) from YOUR OWN INFERENCE. Label
   each claim as [MEASURED], [PRACTICE], or [INFERENCE].
3. Prefer primary sources (manufacturer pages, standards bodies, published
   measurements, official software documentation) over blog summaries and
   AI-generated content farms. Name the vendor/standard explicitly.
4. Give ranges with units (mm, m, lux, lm/m, K, g/m², degrees, ΔE) rather than
   adjectives. If a source gives a single value, say n=1 and name it.
5. Where sources conflict, show the conflict rather than averaging it.

Structure the answer as:
## ANSWERS
One numbered section per question asked, in the order asked. Each claim tagged
[MEASURED]/[PRACTICE]/[INFERENCE] with its source inline.
## CONFLICTS AND UNCERTAINTY
Where the sources disagree, and which values you would NOT stake a build on.
## WHAT I COULD NOT SOURCE
Explicitly list every question or sub-item that returned no sourced value.
"""


def extract_sources(resp):
    """Pull grounding URIs out of the response, defensively.

    The SDK's grounding metadata shape has moved between versions, and a missing
    attribute must not lose an answer we already paid for — so every access is
    guarded and failure degrades to an empty list, never an exception.
    """
    out, queries = [], []
    try:
        for cand in getattr(resp, "candidates", None) or []:
            gm = getattr(cand, "grounding_metadata", None)
            if gm is None:
                continue
            queries += list(getattr(gm, "web_search_queries", None) or [])
            for ch in getattr(gm, "grounding_chunks", None) or []:
                web = getattr(ch, "web", None)
                if web is None:
                    continue
                out.append({"title": getattr(web, "title", "") or "",
                            "uri": getattr(web, "uri", "") or "",
                            "domain": getattr(web, "domain", "") or ""})
    except Exception as e:  # metadata is a bonus, the answer is the artifact
        print(f"[research_call WARN] grounding extract: {type(e).__name__}: {e}",
              file=sys.stderr)
    return out, queries


def bump_usage(mode: str) -> None:
    usage = REPO / ".gemini_usage.json"
    try:
        data = json.loads(usage.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if data.get("date") != date.today().isoformat():
        data = {"date": date.today().isoformat(), "flash": 0, "pro": 0,
                "thinking": 0, "deep": 0, "vision": 0}
    data[mode] = data.get(mode, 0) + 1
    usage.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="deep", choices=list(MODELS))
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    prompt = Path(a.prompt_file).read_text(encoding="utf-8")
    m = FORBIDDEN.search(prompt)
    if m:
        sys.exit(f"prompt carries forbidden reference '{m.group(0)}' — refusing to send")

    from dotenv import load_dotenv
    import os
    load_dotenv(REPO / ".env")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY not in repo .env")

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key)

    cfg = {"temperature": 0.2, "system_instruction": SYSTEM}
    if a.mode in ("deep", "pro", "flash"):
        cfg["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    # DELIBERATELY NO thinking_config ANYWHERE IN THIS FILE.
    #
    # Measured 2026-08-08, same prompt, same system instruction, back to back:
    #   pro  (google_search, no thinking budget)      -> 58 search queries, 21 sources
    #   deep (google_search + thinking_budget=32768)  ->  0 search queries,  0 sources
    # A 32k thinking budget SUPPRESSES the search tool on gemini-2.5-pro through this
    # SDK path. The model then answers from memory and recites manufacturers and
    # standards by name, so the output looks MORE authoritative than the grounded one.
    # That is the worst possible failure: a mode named "deep" that is the shallowest.
    # 9 of the first 10 calls this session came back that way before it was caught.
    # `deep` is kept as an alias of `pro` so existing call sites keep working and
    # get grounded answers; a thinking-only mode would need its own name AND its own
    # loud "this cannot cite anything" banner before it is worth having.

    resp = client.models.generate_content(
        model=MODELS[a.mode], contents=prompt,
        config=types.GenerateContentConfig(**cfg),
    )
    text = resp.text or ""
    srcs, queries = extract_sources(resp)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # An answer with zero grounding chunks was written from MODEL MEMORY, however
    # many source names it recites — and reciting them is exactly what it does.
    # Say so at the top of the file, where a reader lands, not only in a sidecar
    # nobody opens. Discovered 2026-08-08: 4 of the first 5 deep-mode calls came
    # back with empty grounding while citing manufacturers by name.
    grounded = bool(srcs)
    head = [f"# {a.tag or out.stem}", "",
            f"- vendor: Gemini `{MODELS[a.mode]}` mode `{a.mode}`"
            + (" (google_search grounded)" if grounded else " — **SEARCH DID NOT FIRE**"),
            f"- date: {date.today().isoformat()}",
            f"- prompt: `{Path(a.prompt_file).name}` (archived beside this file)",
            f"- tier: REFERENCE — un-distilled. A number with no source below is QUARANTINED.",
            ""]
    if not grounded:
        head += ["> **UNGROUNDED — the vendor reported ZERO retrieved sources.** Every value",
                 "> below came from model memory, including the ones that name a manufacturer",
                 "> or a standard. Nothing here may enter `knowledge/` until a second pass",
                 "> retrieves the page. Treat source names in the text as CLAIMS, not citations.",
                 ""]
    tail = ["", "---", "", "## GROUNDING (vendor-reported)", ""]
    tail += [f"- search queries issued: {len(queries)}"] if queries else ["- search queries issued: none reported"]
    for q in queries:
        tail.append(f"  - `{q}`")
    tail.append("")
    if srcs:
        tail.append(f"- grounding chunks: {len(srcs)}")
        seen = set()
        for s in srcs:
            k = s["uri"]
            if k in seen:
                continue
            seen.add(k)
            tail.append(f"  - {s['title'] or s['domain'] or '(untitled)'} — {s['uri']}")
    else:
        tail.append("- grounding chunks: NONE REPORTED — treat every number here as "
                    "unsourced until verified by hand.")
    out.write_text("\n".join(head) + text + "\n".join(tail) + "\n", encoding="utf-8")
    (out.parent / (out.stem + ".grounding.json")).write_text(
        json.dumps({"queries": queries, "chunks": srcs}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    bump_usage(a.mode)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"[research_call] {a.tag or out.stem}: {len(text)} chars, "
          f"{len(srcs)} grounding chunks -> {out}")


if __name__ == "__main__":
    main()
