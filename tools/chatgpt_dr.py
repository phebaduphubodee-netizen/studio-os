"""
chatgpt_dr.py — OpenAI (GPT-5) research with mode selection + daily usage tracking (domain-clean).

A 4th independent web index alongside Gemini and Perplexity. Ported from
BRAINDEAD/scripts/chatgpt_query.py, domain-cleaned for PlingPeat (interior-design system prompt
instead of the original BTC-derivatives one; no BRAINDEAD dr_resolution_log dependency).
Self-contained: reads only PlingPeat/.env.

Usage:
  python tools/chatgpt_dr.py "question"                  # GPT-5 + Search (default, 30/day soft cap)
  python tools/chatgpt_dr.py --mini "question"           # GPT-5-mini + Search (cheap, ~unlimited)
  python tools/chatgpt_dr.py --reasoning "question"      # o3 reasoning, no search (30/day)
  python tools/chatgpt_dr.py --deep "question"           # GPT-5 + Search + DR PROMPT TEMPLATE (12/day)
  python tools/chatgpt_dr.py --deep-research "question"  # o4-mini-deep-research (real agentic DR, 5/day)
  python tools/chatgpt_dr.py --no-search "question"      # GPT-5, no search (30/day)

Daily caps are SELF-IMPOSED LOCAL cost controls (.openai_usage.json + QUOTA dict), NOT OpenAI
server limits. NOTE: a ChatGPT Plus subscription does NOT include API credits — this bills
per-token via the OPENAI_API_KEY. Edit QUOTA to adjust caps.

Two "deep" modes — DO NOT CONFUSE:
  --deep          = gpt-5 + web_search + DR prompt template. Single round, 10-30s, ~$0.10-0.50/query.
  --deep-research = o4-mini-deep-research. Real multi-step agentic DR, 5-30 min, ~$1-6/query.

When to use vs Gemini vs Perplexity vs /deep-research skill:
  /deep-research (Claude skill) — $0, adversarial-verify + cited; FIRE THIS FIRST
  Gemini (gemini_dr.py)         — real-time Google Search, broad web
  Perplexity (perplexity_dr.py) — independent index, alt second opinion
  ChatGPT (this)                — 4th independent web index; agentic deep-research mode
"""
import sys, io, argparse, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
load_dotenv(PROJECT_ROOT / ".env")

try:
    import httpx
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(1)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in PlingPeat/.env (see .env.example)", file=sys.stderr)
    print("  Get a key at: https://platform.openai.com/api-keys", file=sys.stderr)
    print("  NOTE: Plus subscription does NOT include API credits — separate billing.", file=sys.stderr)
    sys.exit(1)

# Disable keepalive (fresh connection per request) to avoid the stale-keepalive-pool
# RemoteProtocolError class on long web-search generations. SDK max_retries=4 handles residual
# single-flake transients. deep_research overrides max_retries=0 to cap the cost ceiling at 1x.
_httpx_client = httpx.Client(
    timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0),
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=0, keepalive_expiry=0),
)
client = OpenAI(api_key=OPENAI_API_KEY, http_client=_httpx_client, max_retries=4)

USAGE_FILE = PROJECT_ROOT / ".openai_usage.json"

QUOTA = {"default": 30, "mini": 9999, "reasoning": 30, "deep": 12, "deep_research": 5, "no_search": 30}

MODEL_DEFAULT       = "gpt-5"
MODEL_MINI          = "gpt-5-mini"
MODEL_REASONING     = "o3"
MODEL_DEEP_RESEARCH = "o4-mini-deep-research"   # swap to "o3-deep-research" for max depth (~5-10x cost)

WEB_TOOL = {"type": "web_search"}
DR_WEB_TOOL = {"type": "web_search_preview"}    # deep-research models require web_search_preview
DR_TIMEOUT_SEC = 1800.0   # 30 min — DR runs can take 5-30 min

SYSTEM_PROMPT = """You are a senior interior-design research assistant supporting an AI-assisted
interior-design studio for Thai residential work (condos, houses, townhomes). The audience is a
builder who is NOT a trained interior designer and needs textbook-grade professional ground truth.
Prioritize authoritative sources: interior-design textbooks (Ching; Karlen & Fleming; Panero &
Zelnik; Binggeli), lighting standards (IES; Gordon; Steffy), and Thai building regulations
(พ.ร.บ.ควบคุมอาคาร + ministerial regulations) when jurisdiction matters. Work metric-first (mm/m/m2).
Cite the specific book/standard/clause and give real terminology, typical values, ranges, units.
Flag speculative claims and vendor marketing clearly. Do NOT invent citations."""

DEEP_SYSTEM_PROMPT = SYSTEM_PROMPT + """

You are conducting structured Deep Research. Structure your response as:
## QUESTION DECOMPOSITION — sub-questions that must be answered.
## EVIDENCE GATHERED — key findings with the authoritative source/clause named for each.
## SYNTHESIS — integrated, builder-usable answer to the original question.
## LIMITATIONS — gaps, uncertainties, conflicting evidence, caveats.
## ACTIONABLE FOR AN AI DRAFTING PIPELINE — concrete elements/fields/checks this implies."""


def load_usage() -> dict:
    today = str(date.today())
    if USAGE_FILE.exists():
        try:
            data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
            if data.get("date") == today:
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    return {"date": today, "default": 0, "mini": 0, "reasoning": 0, "deep": 0, "deep_research": 0, "no_search": 0}


def save_usage(usage: dict) -> None:
    USAGE_FILE.write_text(json.dumps(usage, indent=2), encoding="utf-8")


def print_quota(usage: dict) -> None:
    lines = []
    for mode in ("default", "deep", "deep_research", "reasoning", "no_search", "mini"):
        used = usage.get(mode, 0)
        limit = QUOTA[mode]
        lines.append(f"{mode}: {used} used" if limit >= 9999 else f"{mode}: {limit - used}/{limit} remaining")
    print(f"[ChatGPT-API quota {usage['date']}: {' | '.join(lines)}]", file=sys.stderr)


def check_quota(usage: dict, mode: str) -> None:
    used = usage.get(mode, 0)
    limit = QUOTA[mode]
    if limit < 9999 and used >= limit:
        print(f"ERROR: {mode} quota exhausted ({used}/{limit} used today). "
              f"Local counter resets on date.today(). Edit QUOTA in chatgpt_dr.py to raise the cap.",
              file=sys.stderr)
        sys.exit(1)


def query(prompt: str, mode: str = "default") -> str:
    """Uses the OpenAI Responses API. ALWAYS streams (non-streaming drops idle connections on
    long web_search generations, surfacing as RemoteProtocolError)."""
    timeout = None
    if mode == "default":
        model, tools, system = MODEL_DEFAULT, [WEB_TOOL], SYSTEM_PROMPT
    elif mode == "mini":
        model, tools, system = MODEL_MINI, [WEB_TOOL], SYSTEM_PROMPT
    elif mode == "no_search":
        model, tools, system = MODEL_DEFAULT, None, SYSTEM_PROMPT
    elif mode == "reasoning":
        model, tools, system = MODEL_REASONING, None, SYSTEM_PROMPT
    elif mode == "deep":
        model, tools, system = MODEL_DEFAULT, [WEB_TOOL], DEEP_SYSTEM_PROMPT
    elif mode == "deep_research":
        model, tools, system = MODEL_DEEP_RESEARCH, [DR_WEB_TOOL], DEEP_SYSTEM_PROMPT
        timeout = DR_TIMEOUT_SEC
        print("[deep_research] Starting o4-mini-deep-research — may take 5-30 minutes. Do not interrupt.",
              file=sys.stderr)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    kwargs = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
    }
    if tools is not None:
        kwargs["tools"] = tools

    call_client = client.with_options(timeout=timeout) if timeout is not None else client
    if mode == "deep_research":
        call_client = call_client.with_options(max_retries=0)  # cost ceiling: 1x DR call

    text_parts = []
    stream = call_client.responses.create(**kwargs)
    for event in stream:
        etype = getattr(event, "type", "")
        if etype == "response.output_text.delta":
            text_parts.append(getattr(event, "delta", ""))
        elif etype == "response.error":
            raise RuntimeError(f"Responses API error event: {getattr(event, 'error', None)}")
        elif etype == "response.completed":
            break
    return "".join(text_parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mini",          action="store_true", help="GPT-5-mini + Search (cheap, ~unlimited)")
    parser.add_argument("--reasoning",     action="store_true", help="o3 reasoning, no search (30/day)")
    parser.add_argument("--deep",          action="store_true", help="GPT-5 + Search + DR template (12/day)")
    parser.add_argument("--deep-research", dest="deep_research", action="store_true",
                        help="o4-mini-deep-research — real agentic DR (5/day, 5-30 min, ~$1-6/query)")
    parser.add_argument("--no-search",     dest="no_search", action="store_true",
                        help="GPT-5, no search (30/day)")
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()

    prompt = " ".join(args.prompt) if args.prompt else sys.stdin.read().strip()
    if not prompt:
        print("ERROR: no prompt provided", file=sys.stderr)
        sys.exit(1)

    if args.deep_research:
        mode = quota_key = "deep_research"
    elif args.deep:
        mode = quota_key = "deep"
    elif args.reasoning:
        mode = quota_key = "reasoning"
    elif args.mini:
        mode = quota_key = "mini"
    elif args.no_search:
        mode = quota_key = "no_search"
    else:
        mode = quota_key = "default"

    usage = load_usage()
    print_quota(usage)
    check_quota(usage, quota_key)

    print(f"[chatgpt/{mode}]\n", file=sys.stderr)
    try:
        result = query(prompt, mode=mode)
    except Exception as e:
        # OpenAI gates the deep-research model class behind org verification. Degrade LOUDLY to
        # --deep rather than crash, and log honestly as 'deep' so the record is never overstated.
        msg = str(e)
        if mode == "deep_research" and ("must be verified" in msg or "Verify Organization" in msg):
            bar = "=" * 74
            print(f"\n{bar}", file=sys.stderr)
            print("DEEP-RESEARCH UNAVAILABLE: OpenAI org not verified for o4-mini-deep-research.", file=sys.stderr)
            print("ONE-TIME FIX (~15 min): https://platform.openai.com/settings/organization/general", file=sys.stderr)
            print("  -> click 'Verify Organization' (ID check via Persona); propagates in ~15 min.", file=sys.stderr)
            print("DEGRADING to --deep (gpt-5 + web_search; strong, but NOT agentic deep-research).", file=sys.stderr)
            print(f"{bar}\n", file=sys.stderr)
            mode = quota_key = "deep"
            check_quota(usage, quota_key)
            result = query(prompt, mode=mode)
        else:
            raise
    print(result)

    usage[quota_key] = usage.get(quota_key, 0) + 1
    save_usage(usage)
    remaining = QUOTA[quota_key] - usage[quota_key]
    if QUOTA[quota_key] < 9999:
        print(f"[{quota_key} slots remaining today: {remaining}/{QUOTA[quota_key]}]", file=sys.stderr)
