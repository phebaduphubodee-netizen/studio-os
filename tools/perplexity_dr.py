"""
perplexity_dr.py — Second-opinion web research via Perplexity AI (domain-clean, interior design).

Independent search index from Gemini/ChatGPT — use for a third opinion on a mechanism/spec
claim, recent product/material info, or when Gemini + Claude consensus feels too neat.

Ported from BRAINDEAD/scripts/perplexity_query.py but domain-cleaned for PlingPeat:
  - interior-design system prompt (the original hard-codes a BTC-derivatives prompt)
  - uses httpx instead of curl.exe (cross-platform: works on native Windows AND WSL)
  - no BRAINDEAD dr_resolution_log dependency
Self-contained: reads only PlingPeat/.env.

Usage:
  python tools/perplexity_dr.py "your question"          # sonar-pro (default, web search)
  python tools/perplexity_dr.py --thinking "question"    # sonar-reasoning-pro (web + reasoning)
  python tools/perplexity_dr.py --no-search "question"   # sonar (fast, no web)

Cost (Perplexity API, pay-per-use — no hard daily limit, cost is the throttle):
  sonar-pro ~$3/1000 req · sonar-reasoning-pro ~$5/1000 req · sonar ~$1/1000 req

When to use vs Gemini vs ChatGPT vs /deep-research skill:
  /deep-research (Claude skill) — $0, adversarial-verify + cited; FIRE THIS FIRST
  Gemini (gemini_dr.py)         — real-time Google Search, broad web, 32k thinking
  Perplexity (this)             — independent index; alt second opinion
  ChatGPT (chatgpt_dr.py)       — 4th independent web index; agentic deep-research mode
"""
import sys, io, os, json, time, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
load_dotenv(PROJECT_ROOT / ".env")

import httpx

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    print("ERROR: PERPLEXITY_API_KEY not found in PlingPeat/.env (see .env.example)", file=sys.stderr)
    print("  Get a key at: https://www.perplexity.ai/settings/api", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.perplexity.ai/chat/completions"
USAGE_FILE = PROJECT_ROOT / ".perplexity_usage.json"  # project-local request counter (informational)

SYSTEM_PROMPT = (
    "You are a senior interior-design research assistant supporting an AI-assisted interior-design "
    "studio for Thai residential work (condos, houses, townhomes). The audience is a builder who is "
    "NOT a trained interior designer and needs textbook-grade professional ground truth. "
    "Prioritize authoritative sources — interior-design textbooks (Ching; Karlen & Fleming; Panero & "
    "Zelnik), lighting standards (IES), and Thai building regulations (พ.ร.บ.ควบคุมอาคาร and its "
    "ministerial regulations) when jurisdiction matters. Work metric-first (mm/m/m2). Cite the "
    "specific book/standard/clause and give real terminology, typical values, ranges, and units. "
    "Flag speculative claims and vendor marketing explicitly. Do NOT invent citations."
)

MODEL_DEFAULT  = "sonar-pro"           # web search, high quality
MODEL_THINKING = "sonar-reasoning-pro" # web search + chain-of-thought
MODEL_FAST     = "sonar"               # no search, fast

_TRANSIENT = (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout)


def query(prompt: str, model: str = MODEL_DEFAULT) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "return_citations": True,
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    last = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)) as c:
                r = c.post(BASE_URL, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            break
        except _TRANSIENT as exc:
            last = exc
            if attempt == 2:
                raise
            d = 2 * (attempt + 1)
            print(f"[perplexity_dr] {type(exc).__name__} attempt {attempt+1}/3: retrying in {d}s", file=sys.stderr)
            time.sleep(d)
    else:  # pragma: no cover
        raise last

    if "error" in data:
        raise RuntimeError(f"Perplexity API error: {data['error']}")

    text = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])
    if citations:
        text += "\n\n---\n**Sources:**\n"
        for i, url in enumerate(citations, 1):
            text += f"[{i}] {url}\n"
    return text


def _bump_counter(model: str) -> None:
    today = str(date.today())
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8")) if USAGE_FILE.exists() else {}
    except Exception:
        data = {}
    if data.get("date") != today:
        data = {"date": today}
    data[model] = data.get(model, 0) + 1
    try:
        USAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--thinking", action="store_true",
                        help="Use sonar-reasoning-pro (web + chain-of-thought)")
    parser.add_argument("--no-search", dest="no_search", action="store_true",
                        help="Use sonar model without web search (fast, cheaper)")
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()

    prompt = " ".join(args.prompt) if args.prompt else sys.stdin.read().strip()
    if not prompt:
        print("ERROR: no prompt provided", file=sys.stderr)
        sys.exit(1)

    if args.thinking:
        model = MODEL_THINKING
    elif args.no_search:
        model = MODEL_FAST
    else:
        model = MODEL_DEFAULT

    print(f"[perplexity/{model}]\n", file=sys.stderr)
    result = query(prompt, model=model)
    print(result)
    _bump_counter(model)
