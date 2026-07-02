"""
gemini_dr.py — PlingPeat / STUDIO-OS Deep Research via Gemini (domain-clean).

WHY A SEPARATE WRAPPER (not BRAINDEAD's scripts/gemini_query.py or perplexity/chatgpt):
  Those scripts hard-code a BTC-derivatives system prompt ("All research is BTC-focused…
  IMPLICATIONS for BTC perpetuals") which would contaminate an interior-design query.
  PlingPeat is a separate domain. This wrapper is FULLY SELF-CONTAINED: its own
  PlingPeat/.env key and its own project-local daily-cost counter (.gemini_usage.json).
  It does NOT read BRAINDEAD/.env or any sibling project.

MODE: gemini-2.5-pro + Google Search grounding + 32k thinking budget (= "deep").

USAGE:
  python tools/gemini_dr.py "<research question>" [--out research/file.md]
"""
import sys, io, os, json, time, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Self-contained: key + cost counter are project-local (no BRAINDEAD dependency).
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
load_dotenv(PROJECT_ROOT / ".env")

import httpx
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("ERROR: GEMINI_API_KEY not found in PlingPeat/.env (see .env.example)")

USAGE_FILE = PROJECT_ROOT / ".gemini_usage.json"  # project-local daily-cost counter
DEEP_CAP = 12  # self-imposed daily deep cap (cost control, not a Google limit)

_TRANSIENT = (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout)

_httpx = httpx.Client(
    timeout=httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0),
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=0, keepalive_expiry=0),
)
client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(httpx_client=_httpx))

SYSTEM_PROMPT = """You are a senior interior-design research assistant supporting an AI-assisted
interior-design drafting/rendering studio for THAI RESIDENTIAL work (condos, houses, townhomes).
The audience is a builder who is NOT a trained interior designer and needs textbook-grade,
professional ground truth — not consumer/blog fluff.

Prioritize, and EXPLICITLY NAME, authoritative sources:
- Interior-design textbooks: Ching "Interior Design Illustrated"; Karlen & Fleming "Space Planning
  Basics"; Panero & Zelnik "Human Dimension & Interior Space"; Nielson & Taylor "Interiors";
  Binggeli "Materials for Interior Environments".
- Lighting: IES Lighting Handbook / IES standards; Gary Gordon "Interior Lighting for Designers";
  Steffy "Architectural Lighting Design".
- THAI regulatory authority (highest priority when jurisdiction matters): พ.ร.บ.ควบคุมอาคาร
  (Building Control Act) and its กฎกระทรวง (ministerial regulations), condominium juristic-person
  rules (นิติบุคคลอาคารชุด), and any Thai accessibility/fire/egress standards. Name the specific
  act/regulation and clause where possible.

Work METRIC-FIRST (mm / m / m²). Cite the specific book/standard/clause for each substantive claim,
and give real professional terminology, typical numeric values, ranges, and units. Flag anything
speculative or vendor-marketing. Do NOT invent citations, page numbers, or clause numbers."""

DR_STRUCTURE = """

Conduct structured Deep Research. Structure the answer as:
## QUESTION DECOMPOSITION — the sub-questions that must be answered.
## EVIDENCE / FINDINGS — substantive content, organized by topic, with the authoritative
   textbook/standard/clause named for each block. Include concrete terminology, typical values,
   ranges, units (metric).
## CANONICAL SOURCES — a bulleted list of the specific books/standards/Thai regulations a builder
   should acquire, with author + title (+ edition/year if known) and what each is the authority FOR.
## SYNTHESIS — an integrated, builder-usable answer to the original question.
## ACTIONABLE FOR AN AI DRAFTING PIPELINE — concrete elements/fields/checks this implies for a
   spec-driven generator (what a "complete" deliverable must contain; what to encode as rules)."""


def update_cost_counter():
    today = str(date.today())
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8")) if USAGE_FILE.exists() else {}
    except Exception:
        data = {}
    if data.get("date") != today:
        data = {"date": today, "flash": 0, "pro": 0, "thinking": 0, "deep": 0}
    used = data.get("deep", 0)
    if used >= DEEP_CAP:
        print(f"WARNING: Gemini deep counter at {used}/{DEEP_CAP} today (self-imposed cost cap). "
              f"Proceeding anyway (founder-authorized DR); edit DEEP_CAP to change.", file=sys.stderr)
    data["deep"] = used + 1
    try:
        USAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[cost] Gemini deep counter -> {data['deep']}/{DEEP_CAP} for {today}", file=sys.stderr)
    except Exception as e:
        print(f"[cost WARN] could not update counter: {type(e).__name__}: {e}", file=sys.stderr)


def query(prompt: str) -> str:
    # STREAMING (not generate_content): long DR answers with 32k thinking + search take
    # long enough that Google's edge drops a non-streaming connection BEFORE headers arrive
    # ("Server disconnected without sending a response"). Streaming keeps the socket
    # actively receiving chunks. We accumulate chunks; a mid-stream drop re-runs the attempt.
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        thinking_config=types.ThinkingConfig(thinking_budget=32768),
    )
    contents = f"{SYSTEM_PROMPT}\n\n{prompt}{DR_STRUCTURE}"
    last = None
    for attempt in range(4):
        try:
            chunks = []
            for chunk in client.models.generate_content_stream(
                    model="gemini-2.5-pro", contents=contents, config=config):
                if chunk.text:
                    chunks.append(chunk.text)
            text = "".join(chunks)
            if not text.strip():
                raise RuntimeError("empty stream returned")
            return text
        except (_TRANSIENT + (RuntimeError,)) as exc:
            last = exc
            if attempt == 3:
                break
            d = 2 ** attempt
            print(f"[gemini_dr] {type(exc).__name__} attempt {attempt+1}/4: retrying in {d}s", file=sys.stderr)
            time.sleep(d)
    raise last


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="PlingPeat Gemini Deep Research (domain-clean).")
    ap.add_argument("prompt", nargs="*")
    ap.add_argument("--out", default=None, help="write the answer to this path (also printed to stdout)")
    args = ap.parse_args()
    prompt = " ".join(args.prompt) if args.prompt else sys.stdin.read().strip()
    if not prompt:
        sys.exit("ERROR: no prompt provided")

    update_cost_counter()
    result = query(prompt)
    print(result)
    if args.out:
        outp = Path(args.out)
        if not outp.is_absolute():
            outp = PROJECT_ROOT / outp
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(result, encoding="utf-8")
        print(f"\n[saved] {outp}", file=sys.stderr)
