"""blenderkit.py — search and fetch models from Blendkit (formerly BlenderKit,
rebranded 2026-06-10 at the Blender Foundation's trademark request; the API
still answers at www.blendkit.com/api/v1 and the free tier needs no account).

CLI-ONLY, like `warehouse.py` and `furnimesh.py`: run during an R8 ACQUIRE
decision. Queries are generic by the NLM-lane privacy rule — class words and
asset ids are all that leave this machine; never a client name or dimension.

    python pipeline/scripts/blenderkit.py status
    python pipeline/scripts/blenderkit.py search "bed modern" --pages 2
    python pipeline/scripts/blenderkit.py fetch <assetBaseId> --assert-class whole_bed
    python pipeline/scripts/blenderkit.py shortlist --limit 10 --resolution 2K

WHY THIS EXISTS — owner order 2026-08-22, his words: "สมัคร blenderkit 1 เดือนเลย
ผมอยากจะรู้ว่ามันจะทำให้งานดีขึ้นยังไง" (ORD-2026-08-22-blenderkit-one-month).
Until today every Blendkit fetch in this repo was an ad-hoc script in a
`_private/` folder (the 08-18 free-tier sweep) — the shelf existed and the
fetcher did not, so the paid month would have started with nothing that could
consume the key. This module is the consumer: the moment `BLENDERKIT_API_KEY`
is in the repo `.env`, `shortlist` walks the panel-passed full-plan beds into
the cache with no further decision, and `status` prints the month clock.

THE PLAN HE IS BUYING (pricing page markup, verified 2026-08-22): the Full card
has three tabs — "30 day glimpse" $19.90 NON-recurring, "Monthly" $17.90
recurring, "Yearly" $9.90/month recurring ($118.80/yr). The page opens on the
Yearly tab, which is how "$9.90/mo" entered this repo's ledgers on the morning
of 08-22. ONE month as he ordered it is the glimpse. The action is ASK-031.

THE ROUTE, verified live 2026-08-22 on the public API (no account):
  * search:   GET /api/v1/search/?query=asset_type:model+bed&page_size=100
              -> {count, next, results[{assetBaseId, id, name, isFree,
                 canDownload, license, files[{fileType, downloadUrl}],
                 dictParameters{dimensionX/Y/Z, faceCount, ...}}]}
              `count` SATURATES AT 10,000 — derive a type-level total as
              is_free:true + is_free:false, never from an unfiltered count.
              An unknown qualifier key answers count=0, not an error, so a
              zero needs a positive control beside it (the census keeps one).
  * download: per-FILE, never per-asset — GET files[].downloadUrl
              (https://www.blendkit.com/api/v1/downloads/<fileId>/)
              ?scene_uuid=<uuid4>  ->  {"filePath": <signed URL>}
              A free asset answers 200 with no auth. A FULL-PLAN asset answers
              401 {"detail": "Unauthorized access. Please log in."} with no
              auth — that refusal is mapped to ASK-031 by name below. With the
              plan, the same call carries `Authorization: Bearer <key>` (the
              add-on's own header). The key is attached ONLY to URLs on SITE.
  * fileType 'blend' is the original upload (textures packed, up to 4K);
    'resolution_2K' / '1K' / '0_5K' are the same .blend with downscaled maps —
    `--resolution 2K` halves the bytes when 135 downloads are on the table.

BLEND -> GLB IS A SPAWNED BLENDER, NOT bpy IN THIS FILE (layer law,
pipeline/CLAUDE.md): `mesh_import` refuses `.blend` by design and the shelf's
native format is GLB, so every fetch ends in a headless export
(`export_scene.gltf`, export_apply=True — the 08-18 route, now in one place).
The spawn is `--factory-startup -Y` (user prefs off, auto-run scripts OFF):
these are third-party files opened unattended, 135 of them. The .blend is kept
beside the GLB unless `--drop-blend`: it carries the asset's Cycles materials,
which a GLB flattens to PBR maps — and whether THAT flattening is what limits
our cloth (P2r-5) is one of the month's report lines (D-119). Re-fetch is
reproducible from the asset id.

SCALE IS ASSERTED ON EVERY INGEST (R8) via `asset_scale.write_sidecar`, same
call as the other shelves, and a refusal is a RESULT that is logged, never a
failure that is shrugged. Declared dims in the catalogue are WHOLE-ASSET
numbers (the 08-17 caveat that decided the free test) — the sidecar measures
the GLB, the bench measures the truth in the room.

LICENCE: royalty_free (use in renders and client work yes; no resale as a
model) or cc_zero per asset, recorded raw in SOURCE.json with the repo's own
licence ids (scripts/asset_license.py: royalty-free-commercial / cc0). A row
the API leaves unlicensed is recorded `unknown`, never defaulted permissive.
The cache is gitignored (.gitignore:68). `docs/LICENSING.md` notes their terms
are silent on AI/ML use — treated as unanswered, not as permitted.

THE RUN LOG `qa/blenderkit-fetch-log.json` is appended to atomically, never
rewritten, and never overwritten when unreadable — it is the file the order's
`obeyed_assert` greps and the month clock's only source. Dry runs and the
`--log` override exist so probes and tests never write into it. It is a
SEPARATE file from `qa/blenderkit-search-log.json`, the 08-17/08-18
hand-written measurement record, which stays byte-identical.

EXIT CODES ARE A CONTRACT (R11): 0 = did it; 1 = did it and the result is a
refusal (scale refused, asset gone); 2 = COULD NOT RUN — no key for a
full-plan asset, key refused, no Blender, network/site down, log unreadable —
and 2 must never print like 0. Every path out of main() is one of the three.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                   # noqa: BLE001
    pass

SITE = "https://www.blendkit.com"
API = SITE + "/api/v1"
KEY_NAME = "BLENDERKIT_API_KEY"
ASK = "ASK-031"                      # pay + paste the key — the one owner action left
ORDER = "ORD-2026-08-22-blenderkit-one-month"
CRITERIA = "D-119"
MONTH_DAYS = 30
COUNT_CAP = 10000

# same reasoning as assets.py / warehouse.py / furnimesh.py: this machine sits
# behind a TLS-intercepting VPN, so certificates do not verify by default
_CTX = ssl._create_unverified_context()
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(REPO, "assets", "shared", "blenderkit")
FETCH_LOG = os.path.join(REPO, "qa", "blenderkit-fetch-log.json")
SHORTLIST = os.path.join(REPO, "_private", "deliv-001", "bed-size-2026-08-18",
                         "blenderkit-shortlist", "shortlist.json")
SPEC = os.path.join(REPO, "projects", "PRJ-2026-002_c001-house", "03_layout",
                    "master-suite.CANONICAL.spec.json")
DECISIONS = os.path.join(REPO, "qa", "open-decisions.json")
CLASSES = os.path.join(REPO, "qa", "blenderkit-month-classes.json")
# THE RESULTS DO NOT LIVE IN THE FROZEN FILE, and finding out why cost a probe.
# `criteria_digest` hashes CLASSES whole. The protocol in that file's own `_what` says
# `free_baseline` and then `paid_result` are "filled IN ORDER" — so RUNNING the test as
# written edits the bytes the freeze protects, and `status` answers the honest move with
# "CHANGED SINCE THE CLOCK STARTED ... the flattering-scorer defect". Measured 2026-08-24:
# filling ONE cushion_throw baseline and changing nothing else moved the digest from
# d95d5e9d... to 67b709df.... A machine that calls compliance a defect is switched off,
# which is R13's third-state warning arriving one level up, at the freeze itself.
# THE FIX KEEPS THE HASH AT FULL STRENGTH rather than loosening it: results move to their
# own unhashed file, and CLASSES stays byte-frozen. Editing a query, a control flag or the
# pass rule STILL prints CHANGED — and so does ADDING A CLASS, which is correct, because
# choosing the test set after seeing results is the very thing the freeze exists to catch.
RESULTS = os.path.join(REPO, "qa", "blenderkit-month-results.json")
PANEL_PROMPT = os.path.join(REPO, "docs", "blenderkit-month", "style-panel-prompt.md")

# THE QUERY GRAMMAR, MEASURED 2026-08-23 — not read off a page, tested.
#
# Every line below was verified against the live public endpoint with this repo's own
# positive/negative-control method: a REAL filter splits the set and its halves sum to the
# unfiltered count; an UNKNOWN qualifier silently answers 0, exactly like a deliberate
# misspelling; a MALFORMED field name answers HTTP 400. All three behaviours were observed,
# so "0 results" alone never proves a filter exists.
#
# WHY THIS SITS IN --help AND NOT IN A DOC: the filters already pass straight through
# `search` with no code change. What was missing was knowledge, and knowledge parked in
# knowledge/_inbox/ is this repo's oldest defect. The full workings, the refuted claims and
# the source quotes are in knowledge/_inbox/blenderkit-month/ (2026-08-23).
SEARCH_GRAMMAR = """\
FILTER GRAMMAR (measured 2026-08-23 against the live endpoint, not documented anywhere public)

  One query= string, tokens joined by '+', a colon separates field from value.

  REAL, and they discriminate:
    asset_type:model | material | scene | hdr | brush
    category_subtree:bed            bed 1244 name-hit -> 611 by category
    is_free:true | false            bed 282 + 962 = 1244  (perfect split = real)
    license:cc_zero | royalty_free  bed  22 + 1222 = 1244  (perfect split = real)
    manufacturer:<name>             bed+manufacturer:ikea = 23
    verification_status:validated   real, but every public asset is validated (= no-op here)

  REAL AND THE REASON THIS BLOCK EXISTS — server-side REAL-WORLD SIZE filters, which the
  add-on's own UI does not expose. Metres, float:
    dimensionX_gte / dimensionX_lte      and the same for Y and Z
      category_subtree:bed                                  611
      + dimensionX_gte:1.5                                  551
      + dimensionX_gte:1.5 + dimensionX_lte:2.2             171
      + dimensionZ_lte:1.0                                  304
      + dimensionX_gte:99                                     0   (sanity control)
    Shortlist by the size the slot needs BEFORE downloading anything. This is the cheapest
    fix available for the defect class that has cost this lane the most rounds (D-109 read a
    2,759 mm backdrop wall as bedding; D-120 fitted a bed FRAME into a mattress slot).

  BUT THE NUMBER IS A SEARCH KEY, NEVER A SPEC. Blendkit's own uploader does not enforce
  scale and its Terms disclaim measurement accuracy in writing. asset_scale must still
  assert on every ingest (R8) — this filter narrows the shelf, it does not certify a size.

  NOT REAL, though widely repeated — each answers 0, identically to a misspelling:
    rating:>=4    resolution:8k    license:cc0    author:<username>
  REJECTED outright with HTTP 400:
    quality_count:  faceCount:  textureResolutionMax:
"""
MONTH_DOC = "docs/blenderkit-month-2026-08-22.md"

RESOLUTIONS = {"blend": "blend", "4K": "resolution_4K", "2K": "resolution_2K",
               "1K": "resolution_1K", "0.5K": "resolution_0_5K"}

# the repo's licence ids (scripts/asset_license.py LICENCES) for the API's values
LICENSE_IDS = {"royalty_free": "royalty-free-commercial", "cc_zero": "cc0"}

LICENSE_NOTE = """Blendkit (formerly BlenderKit) assets — per-asset `license` field in each
SOURCE.json: `royalty_free` (free tier and Full plan) or `cc_zero`.

royalty_free: free to use in renders and client work; NOT public domain; NOT
redistributable as a model. cc_zero assets are public domain but sit on this
same gitignored shelf for simplicity — nothing here is committed.
Fetch is reproducible from the asset id (SOURCE.json: asset_base_id).

Their terms are silent on AI/ML use (docs/LICENSING.md) — treated as
unanswered, not as permitted.
"""

EXPORT_SCRIPT = """import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
try:
    bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
except Exception:
    pass
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True)
"""

_LOCAL_PATH = re.compile(r"[A-Za-z]:[\\/][^\s'\"]+|/(?:Users|home)/[^\s'\"]+|_private/[^\s'\"]+")


class Refused(RuntimeError):
    """The site, the shelf or the machine said no; the reason is the message.
    `code` is the CLI exit: 2 = could not run, 1 = ran and the answer is no.
    `logged` is set by a raiser that already wrote the run record, so main()
    does not write a second row for the same run."""

    def __init__(self, msg, code=2, logged=False):
        super().__init__(msg)
        self.code = code
        self.logged = logged


# ------------------------------------------------------------------ pure part --

def parse_env(text):
    """Minimal KEY=VALUE parser for a .env body, python-dotenv semantics for the
    cases a pasted key can hit: quotes stripped, `#` comment lines skipped, an
    UNQUOTED trailing ` # comment` dropped, `export ` prefix tolerated. PURE.
    Used only when python-dotenv is absent (critique_call.py reads the same
    file through dotenv, and the two must agree on the one line ASK-031 asks
    him to paste)."""
    out = {}
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[len("export "):]
        k, v = s.split("=", 1)
        v = v.strip()
        if v[:1] in ("\"", "'") and v.count(v[0]) >= 2:
            v = v[1:v.index(v[0], 1)]               # quoted: up to the closing quote
        else:
            v = re.split(r"\s+#", v, 1)[0].strip()  # unquoted: drop a ' # tail'
        out[k.strip()] = v
    return out


def headers(key=None):
    h = {"User-Agent": "studio-os/1.0", "accept": "application/json"}
    if key:
        h["Authorization"] = "Bearer " + key
    return h


def search_url(query, page=1, page_size=100):
    """Tokens joined with '+' the way the add-on does; `asset_type:`/`is_free:`
    qualifiers pass through. PURE."""
    q = "+".join(t for t in re.split(r"[\s+]+", (query or "").strip()) if t)
    return (f"{API}/search/?query={urllib.parse.quote(q, safe='+:')}"
            f"&page_size={int(page_size)}&page={int(page)}")


def tier_of(result):
    return "free" if result.get("isFree") else "full_plan"


def row_of(result):
    """The compact catalogue row this repo keeps (same shape as the 08-18
    shortlist rows, so the two join on assetBaseId). PURE."""
    dp = result.get("dictParameters") or {}
    return {"assetBaseId": result.get("assetBaseId"), "id": result.get("id"),
            "name": result.get("name"), "category": result.get("category"),
            "isFree": bool(result.get("isFree")),
            "canDownload": bool(result.get("canDownload")),
            "license": result.get("license"), "tier": tier_of(result),
            "dim_x_m": dp.get("dimensionX"), "dim_y_m": dp.get("dimensionY"),
            "dim_z_m": dp.get("dimensionZ"), "faceCount": dp.get("faceCount"),
            "simulation": dp.get("simulation"),
            "thumb": result.get("thumbnailMiddleUrl")}


def file_entry(result, resolution="blend"):
    """The files[] entry to download for `resolution` (a RESOLUTIONS key), or
    None when the asset has no such file. PURE."""
    want = RESOLUTIONS.get(resolution)
    if want is None:
        raise ValueError(f"unknown resolution {resolution!r}; "
                         f"one of {', '.join(RESOLUTIONS)}")
    for f in result.get("files") or []:
        if f.get("fileType") == want and f.get("downloadUrl"):
            return f
    return None


def refusal(status, tier, has_key):
    """Why a site call was refused, in the words the lane needs. PURE. The
    401-without-key case names the ask by id because that is the single owner
    action standing between the order and the shelf."""
    if status in (401, 403) and not has_key:
        if tier == "full_plan":
            return (f"full-plan asset and no {KEY_NAME} in .env — this is "
                    f"{ASK}: buy the Full plan's '30 day glimpse' ($19.90, "
                    f"non-recurring) at {SITE}/plans/pricing, copy the API key "
                    f"from {SITE}/profile into the repo .env as "
                    f"{KEY_NAME}=<key>. Nothing else is missing.")
        return (f"HTTP {status} on a FREE asset with no key — the public route "
                f"changed shape or the site is refusing; not a plan question.")
    if status in (401, 403):
        return (f"HTTP {status} WITH a key — the key is wrong, or the plan has "
                f"lapsed (the month is up). Check {SITE}/profile; a key with "
                f"spaces or a '#' tail is a paste error.")
    if status == 404:
        return ("HTTP 404 — the file id is gone from the catalogue (this module "
                "already uses the per-FILE files[].downloadUrl route; the naive "
                "/downloads/<asset_id>/ form 404s by design).")
    if status == 429:
        return "HTTP 429 — rate-limited by the site; wait, do not retry in a loop."
    if status and status >= 500:
        return f"HTTP {status} — site outage; could not run."
    if status == 200:
        return "HTTP 200 without a filePath — the route changed shape."
    return f"HTTP {status} — could not run."


def exit_code_for(status):
    """The exit a site status maps to: 404 is an answer (1); everything else
    that is not 200 is could-not-run (2). PURE."""
    return 1 if status == 404 else 2


def on_site(url):
    return isinstance(url, str) and url.startswith(SITE + "/")


def plan_fetch(rows, have, has_key, limit=None):
    """Which catalogue rows to fetch and why every other one is passed over.
    PURE. Matches the shelf on the base id AND the version id, because the
    08-22 hand-fetched dirs stored only the version id. No silent caps: every
    skip carries its reason into the log."""
    keep, skip = [], []
    for r in rows:
        bid, vid = r.get("assetBaseId"), r.get("id")
        hit = have.get(bid) or have.get(_dehyphen(bid)) or have.get(vid)
        if hit:
            skip.append({**r, "why": f"already cached as {hit}"})
        elif r.get("tier") == "full_plan" and not has_key:
            skip.append({**r, "why": f"full-plan asset, no key ({ASK})"})
        elif limit is not None and len(keep) >= limit:
            skip.append({**r, "why": f"past --limit {limit} in rank order"})
        else:
            keep.append(r)
    return keep, skip


def _dehyphen(s):
    return (s or "").replace("-", "")


def shortlist_rows(shortlist, tier="full_plan"):
    """The 08-18 shortlist's bench-worthy rows of one tier, in its rank order.
    PURE."""
    ranked = (shortlist or {}).get("ranked") or []
    return [r for r in ranked
            if r.get("bench_worthy") and (tier is None or r.get("tier") == tier)]


def month_clock(runs, today):
    """(first paid download date, days elapsed, days left) or None when the
    month has not started — no full-plan asset has ever been fetched. PURE.
    Probe/dry rows never start it. Dates are LOCAL (`date_local`), the same
    calendar every ledger row uses; the UTC `at` is a fallback for old rows."""
    dates = []
    for r in runs or []:
        if r.get("probe") or r.get("tier") != "full_plan" or not r.get("fetched"):
            continue
        try:
            dates.append(datetime.date.fromisoformat(
                str(r.get("date_local") or r.get("at"))[:10]))
        except ValueError:
            continue
    if not dates:
        return None
    first = min(dates)
    elapsed = (today - first).days
    return first, elapsed, MONTH_DAYS - elapsed


def scrub(text, limit=240):
    """Exception text for a COMMITTED log: local paths out, length capped. PURE."""
    return _LOCAL_PATH.sub("<path>", str(text))[:limit]


def bench_rect(spec):
    """'x,y,w,d' of the spec's bed slot, for wholebed_bench — DERIVED from the
    live spec item, never typed (R9). PURE on a parsed spec. None when there is
    no single bed item, so the caller prints 'could not derive' rather than a
    stale literal (the 3204,51,2000,2149 rect of 08-18 was retired by D-114)."""
    beds = [it for it in (spec or {}).get("items") or [] if it.get("kind") == "bed"]
    if len(beds) != 1:
        return None
    b = beds[0]
    try:
        return ",".join(str(int(b[k])) for k in ("x", "y", "w", "d"))
    except (KeyError, TypeError, ValueError):
        return None


def criteria_digest(in_effect, classes_bytes, prompt_bytes):
    """sha256 over the three things the month's criteria live in: D-119's
    `in_effect`, the pre-registered class file, the panel prompt. Stored on the
    first paid download; `status` re-derives it every run, so an edit after the
    clock started prints CHANGED — the flattering-scorer edit, made visible.
    PURE."""
    h = hashlib.sha256()
    h.update((in_effect or "").encode("utf-8"))
    h.update(b"\0")
    h.update(classes_bytes or b"")
    h.update(b"\0")
    h.update(prompt_bytes or b"")
    return h.hexdigest()


KEY_SHAPE = re.compile(r"[A-Za-z0-9._~\-]{16,}")


def upsert_env_line(text, name, value, shape=None):
    """Replace the `name=` line in a .env body, or append one. PURE. Keeps every
    other byte and the file's newline style; refuses a value that does not
    match `shape` (default KEY_SHAPE: a bare token — a pasted key with a space,
    a '#' tail or quotes is the paste error the 401 message already warns
    about)."""
    if not (shape or KEY_SHAPE).fullmatch(value or ""):
        raise Refused(f"{name}: a key is one bare token of 16+ letters/digits/"
                      f"'-._~' — this one is not (length {len(value or '')}; "
                      f"spaces, quotes or a '#' tail are a paste error)", code=1)
    nl = "\r\n" if "\r\n" in (text or "") else "\n"
    lines = (text or "").split(nl) if text else []
    done = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("export "):
            s = s[len("export "):]
        if s.startswith(name + "=") or s.startswith("#" + name + "=") or s.startswith("# " + name + "="):
            lines[i] = f"{name}={value}"
            done = True
            break
    if not done:
        if lines and lines[-1] != "":
            lines.append("")
        lines += [f"# Blendkit Full — one-month trial (ORD-2026-08-22-blenderkit-one-month)",
                  f"{name}={value}", ""]
    out = nl.join(lines)
    return out if out.endswith(nl) else out + nl


def pick_addon_key(addon_items):
    """PURE. From [(module_name, api_key), ...] as the in-Blender probe reports
    them, the key of the first enabled BlenderKit add-on/extension that holds
    one (`blenderkit` legacy, `bl_ext.blender_org.blenderkit` as an extension).
    None when no such add-on is enabled or it is not logged in."""
    for name, key in addon_items or []:
        if "blenderkit" in str(name).lower() and key and str(key).strip():
            return str(key).strip()
    return None


# Runs INSIDE Blender with the user's own preferences loaded (no
# --factory-startup: the whole point is reading the add-on's stored key). The
# Blender manual: "Your API Key … is automatically retrieved when you log in to
# the service" — so a Google login through the add-on is enough; nobody copies
# anything. The key goes to a temp file the parent reads and deletes; it is
# never printed.
ADDON_KEY_SCRIPT = """import bpy, json, sys
out = sys.argv[sys.argv.index('--') + 1]
rows = []
for name, mod in bpy.context.preferences.addons.items():
    prefs = getattr(mod, 'preferences', None)
    rows.append([name, getattr(prefs, 'api_key', None) if prefs else None])
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(rows, fh)
"""


def key_from_blender(blender=None):
    """Read the BlenderKit add-on's stored API key out of this machine's Blender
    preferences, or Refused(2) naming what is missing (add-on not installed,
    not logged in)."""
    import tempfile
    exe = blender or find_blender()
    fd, out = tempfile.mkstemp(prefix="bk_key_", suffix=".json")
    os.close(fd)
    script = out + ".py"
    try:
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(ADDON_KEY_SCRIPT)
        p = subprocess.run([exe, "-b", "-noaudio", "--python", script, "--", out],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        try:
            with open(out, encoding="utf-8") as fh:
                rows = json.load(fh)
        except (OSError, ValueError):
            raise Refused(f"Blender did not report its add-ons (exit {p.returncode}): "
                          f"{scrub((p.stderr or p.stdout)[-300:], 200)}", code=2)
    finally:
        for f in (out, script):
            try:
                os.remove(f)
            except OSError:
                pass
    key = pick_addon_key(rows)
    if not key:
        names = [n for n, _ in rows if "blenderkit" in str(n).lower()]
        raise Refused(("the BlenderKit add-on is enabled but holds no API key — log in "
                       "through it once (BlenderKit panel -> Login, Google account) and "
                       "run this again" if names else
                       "no BlenderKit add-on/extension is enabled in this Blender — "
                       "install it (Preferences -> Get Extensions -> 'BlenderKit'), log "
                       "in through it once, then run this again; or paste the key from "
                       f"your profile page with `blenderkit.py key <value>`"), code=2)
    return key


def write_key(value, repo=None, refresh=None, expires=None):
    """`blenderkit.py key …` — writes the key (and, from a login, the refresh
    token and expiry) into the repo .env so nobody hand-edits the file, then
    returns the key for `status` to test live. Values are never printed or
    logged."""
    p = os.path.join(repo or REPO, ".env")
    try:
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
    except OSError:
        text = ""
    text = upsert_env_line(text, KEY_NAME, value.strip())
    if refresh:
        text = upsert_env_line(text, REFRESH_NAME, refresh.strip())
    if expires:
        text = upsert_env_line(text, EXPIRES_NAME, str(int(expires)),
                               shape=re.compile(r"\d{1,12}"))
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return value.strip()


# --------------------------------------------------------- OAuth, as the add-on does it
# Read from the add-on's own source (BlenderKit/blenderkit bkit_oauth.py and
# BlenderKit/bk_client client/login.go, 2026-08-22): the add-on never shows
# anyone a key to copy — it opens the browser on /o/authorize with a PKCE
# challenge, the site redirects the logged-in browser back to
# http://localhost:<port>/consumer/exchange/?code=…&state=…, and the client
# POSTs the code to /o/token/ for access + refresh tokens. `key --login` does
# exactly that, on the add-on's own ports and client id, so his Google login
# in the browser is the whole of the owner's action.
OAUTH_CLIENT_ID = "IdFRwa3SGA8eMpzhRVFMg5Ts8sPK93xBjif93x0F"
OAUTH_PORTS = ("62485", "65425", "55428", "49452", "35452", "25152")
REFRESH_NAME = "BLENDERKIT_REFRESH_TOKEN"
EXPIRES_NAME = "BLENDERKIT_API_EXPIRES"
REFRESH_MARGIN_S = 600


def pkce_pair(rand=None):
    """(code_verifier, code_challenge) exactly as bkit_oauth.generate_pkce_pair:
    128 alphanumerics; challenge = urlsafe-b64(sha256(verifier)) without '='."""
    import random
    import string
    rand = rand or random.SystemRandom()
    verifier = "".join(rand.choices(string.ascii_letters + string.digits, k=128))
    import base64
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").replace("=", "")
    return verifier, challenge


def redirect_uri(port):
    return f"http://localhost:{port}/consumer/exchange/"


def authorize_url(port, state, challenge, system_id):
    """The add-on's authorize URL, parameter for parameter. PURE."""
    return (f"{SITE}/o/authorize?client_id={OAUTH_CLIENT_ID}&response_type=code"
            f"&state={state}&redirect_uri={redirect_uri(port)}"
            f"&code_challenge={challenge}&code_challenge_method=S256"
            f"&system_id={system_id}")


def parse_callback(path, expected_state):
    """The browser's GET back to localhost: ('code', value) on a matching
    state, ('error', reason) otherwise. PURE. A mismatched state is refused —
    that is the whole point of carrying one."""
    parsed = urllib.parse.urlparse(path)
    if not parsed.path.rstrip("/").endswith("/consumer/exchange"):
        return "error", f"unexpected path {parsed.path!r}"
    q = urllib.parse.parse_qs(parsed.query)
    if q.get("error"):
        return "error", f"{q['error'][0]}: {(q.get('error_description') or [''])[0]}"
    code = (q.get("code") or [None])[0]
    state = (q.get("state") or [None])[0]
    if not code:
        return "error", "no code in the callback"
    if state != expected_state:
        return "error", "state mismatch — refusing the code"
    return "code", code


def needs_refresh(expires_epoch, now_epoch, margin=REFRESH_MARGIN_S):
    """PURE: refresh when the stored expiry is within `margin` seconds (or
    unparseable)."""
    try:
        return float(expires_epoch) - float(now_epoch) < margin
    except (TypeError, ValueError):
        return True


def _post_form(url, fields, timeout=60):
    body = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": "studio-os/1.0", "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace"))
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError,
            ValueError) as e:
        raise Refused(f"could not reach {url}: {type(e).__name__}", code=2)


def token_request(port, code=None, verifier=None, refresh_token=None):
    """POST /o/token/ as client/login.go GetTokens does. Returns the token
    dict (access_token, refresh_token, expires_in, …) or Refused."""
    fields = {"client_id": OAUTH_CLIENT_ID, "redirect_uri": redirect_uri(port)}
    if code:
        fields.update(grant_type="authorization_code", code=code,
                      code_verifier=verifier or "")
    else:
        fields.update(grant_type="refresh_token", refresh_token=refresh_token or "")
    st, d = _post_form(f"{SITE}/o/token/", fields)
    if st != 200 or not isinstance(d, dict) or not d.get("access_token"):
        why = d.get("error_description") or d.get("error") if isinstance(d, dict) else ""
        raise Refused(f"token request refused (HTTP {st}{', ' + scrub(why, 120) if why else ''})",
                      code=2)
    return d


def _free_port(ports=OAUTH_PORTS):
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", int(p)))
            return int(p)
        except OSError:
            continue
        finally:
            s.close()
    raise Refused("none of the add-on's ports is free on 127.0.0.1 "
                  f"({', '.join(ports)}) — is Blender with BlenderKit running?", code=2)


def login(timeout_s=300, opener=None):
    """Run the add-on's login flow once: listen on 127.0.0.1:<port>, open the
    browser on /o/authorize, wait for the redirect, exchange the code.
    Returns the token dict. Nothing about the tokens is printed."""
    import http.server
    import secrets
    import threading
    import webbrowser
    port = _free_port()
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe()
    system_id = f"{uuid.getnode():015d}"
    got = {}
    done = threading.Event()

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                                   # noqa: N802
            kind, val = parse_callback(self.path, state)
            got["kind"], got["val"] = kind, val
            body = ("<html><body style='font-family:sans-serif'><h2>Blendkit login "
                    + ("received — you can close this tab.</h2>" if kind == "code"
                       else f"failed: {html_escape(val)}</h2>")
                    + "</body></html>").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            done.set()

        def log_message(self, *a):                          # silence
            pass

    srv = http.server.HTTPServer(("127.0.0.1", port), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        url = authorize_url(port, state, challenge, system_id)
        ok = (opener or webbrowser.open_new_tab)(url)
        print(f"  browser open {'OK' if ok else 'FAILED'} (port {port}); waiting up to "
              f"{timeout_s} s for the redirect — in that tab: log in with Google if asked, "
              f"press Authorize if asked.\n  If no tab appeared, open this URL yourself "
              f"(one-time, no secret in it):\n  {url}")
        if not done.wait(timeout_s):
            raise Refused("no redirect arrived in time — the browser was not logged "
                          "in, or the tab was closed; run `key --login` again", code=2)
    finally:
        srv.shutdown()
        srv.server_close()
    if got.get("kind") != "code":
        raise Refused(f"login callback: {got.get('val')}", code=2)
    return token_request(port, code=got["val"], verifier=verifier)


def html_escape(s):
    import html
    return html.escape(str(s))


def read_refresh(repo=None):
    """(refresh_token, expires_epoch) from .env, both possibly None."""
    p = os.path.join(repo or REPO, ".env")
    try:
        with open(p, encoding="utf-8") as fh:
            env = parse_env(fh.read())
    except OSError:
        return None, None
    return env.get(REFRESH_NAME) or None, env.get(EXPIRES_NAME) or None


def ensure_fresh_key(key, repo=None, now=None):
    """If the stored expiry is near and a refresh token exists, refresh and
    rewrite .env; otherwise hand the key back unchanged. Never raises — a
    failed refresh leaves the old key for `status` to report as refused."""
    if not key:
        return key
    refresh, expires = read_refresh(repo)
    if not refresh or not expires:
        return key
    import time
    if not needs_refresh(expires, now or time.time()):
        return key
    try:
        d = token_request(OAUTH_PORTS[0], refresh_token=refresh)
    except Refused:
        return key
    import time as _t
    write_key(d["access_token"], repo, refresh=d.get("refresh_token") or refresh,
              expires=_t.time() + float(d.get("expires_in") or 0))
    print("  (access token refreshed from the stored refresh token)")
    return d["access_token"]


def me_summary(body):
    """Plan-shaped SCALAR fields from /me, by exact key — identity never. PURE."""
    u = body.get("user") if isinstance(body.get("user"), dict) else body
    keys = ("currentPlanName", "plan", "planName", "planType", "subscription",
            "subscriptionEnd", "subscription_end", "validUntil", "valid_until",
            "remainingPrivateQuota", "sumAssetFilesSize")
    out = {}
    for k in keys:
        v = (u or {}).get(k)
        if isinstance(v, (str, int, float, bool)):
            out[k] = str(v)[:60]
    return out


# ------------------------------------------------------------ shelf and log --

def _source(dirpath):
    try:
        with open(os.path.join(dirpath, "SOURCE.json"), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def cached_ids(cache=None):
    """{id: dirname} for every id form a shelf entry can be known by — base id,
    base id without hyphens (the 13:10 hand-fetched dir names), version id —
    read from the SOURCE.json files themselves (the shelf is the fact, the log
    is a record of asks: warehouse.cached_ids' law)."""
    cache = cache or CACHE
    out = {}
    for name in sorted(os.listdir(cache)) if os.path.isdir(cache) else []:
        d = _source(os.path.join(cache, name))
        if not d:
            continue
        for k in ("asset_base_id", "asset_id", "asset_version_id"):
            v = d.get(k)
            if v:
                out[v] = name
                out[_dehyphen(v)] = name
        out[name] = name
    return out


def shelf_counts(cache=None):
    """{tier: {asserted, refused, unasserted}} — by SIDECAR STATE, because a
    refused or never-asserted entry must not print as stock."""
    cache = cache or CACHE
    out = {"free": {"asserted": 0, "refused": 0, "unasserted": 0},
           "full_plan": {"asserted": 0, "refused": 0, "unasserted": 0}}
    for name in sorted(os.listdir(cache)) if os.path.isdir(cache) else []:
        d = _source(os.path.join(cache, name))
        if not d:
            continue
        tier = d.get("tier") or "free"
        state = "unasserted"
        for fn in os.listdir(os.path.join(cache, name)):
            if fn.endswith(".scale.json"):
                try:
                    with open(os.path.join(cache, name, fn), encoding="utf-8") as fh:
                        ok = json.load(fh).get("ok")
                    state = "asserted" if ok else "refused" if ok is False else "unasserted"
                except (OSError, ValueError):
                    pass
        out.setdefault(tier, {"asserted": 0, "refused": 0, "unasserted": 0})
        out[tier][state] += 1
    return out


def log_path():
    return os.environ.get("BLENDERKIT_LOG") or FETCH_LOG


def load_log(path=None):
    """The log dict, {} when absent, Refused(2) when present but unreadable —
    it must never be silently replaced (it is the only evidence the month
    started)."""
    path = path or log_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        raise Refused(f"run log {os.path.basename(path)} exists but cannot be "
                      f"read ({type(e).__name__}) — not overwriting the evidence; "
                      f"fix the file by hand", code=2)
    return d if isinstance(d, dict) else {"_was": d}


def log_run(record, path=None):
    """Append one run under `runs`, atomically (tmp + replace). Other top-level
    keys are carried through untouched."""
    path = path or log_path()
    d = load_log(path)
    d.setdefault("_what", "Every run of pipeline/scripts/blenderkit.py — appended, "
                          "never rewritten; probe/dry runs carry probe=true and "
                          "never start the month clock. The order "
                          + ORDER + " reads THIS file.")
    d.setdefault("runs", []).append(record)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)
    return path


def _stamp():
    now = datetime.datetime.now().astimezone()
    return now.isoformat(timespec="seconds"), now.date().isoformat()


def _record(cmd, key, probe=False, **kw):
    at, day = _stamp()
    r = {"at": at, "date_local": day, "cmd": cmd, "probe": bool(probe),
         "key_present": bool(key)}
    r.update(kw)
    return r


# ------------------------------------------------------------- network part --

def read_key(repo=None):
    """The key from the repo .env, or None. Env var wins if set. python-dotenv
    (what critique_call.py uses) when installed; parse_env otherwise."""
    k = os.environ.get(KEY_NAME)
    if k and k.strip():
        return k.strip()
    p = os.path.join(repo or REPO, ".env")
    try:
        import logging
        from dotenv import dotenv_values
        # the repo .env carries lines dotenv cannot parse (it warns on every
        # one, on every run); the key line is the only one this reads
        logging.getLogger("dotenv.main").setLevel(logging.ERROR)
        v = (dotenv_values(p) or {}).get(KEY_NAME)
    except ImportError:
        try:
            with open(p, encoding="utf-8") as fh:
                v = parse_env(fh.read()).get(KEY_NAME)
        except OSError:
            return None
    except OSError:
        return None
    return (v or "").strip() or None


def _get_json(url, key=None, timeout=60):
    """(status, parsed body). HTTP errors are RETURNED so a 401 reads as a
    refusal with a reason; transport failures RAISE Refused(2) so they never
    escape as a traceback (exit 1 means 'ran and found a refusal' here)."""
    req = urllib.request.Request(url, headers=headers(key if on_site(url) else None))
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", "replace"))
        except ValueError:
            body = {}
        return e.code, body
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError,
            ValueError) as e:
        raise Refused(f"could not reach or parse {url.split('?')[0]}: "
                      f"{type(e).__name__}: {scrub(e, 120)}", code=2)


def _check(status, body, key, tier="full_plan"):
    if status == 200:
        return
    raise Refused(refusal(status, tier, bool(key)) +
                  (f" [{scrub(body.get('detail'), 80)}]" if isinstance(body, dict)
                   and body.get("detail") else ""),
                  code=exit_code_for(status))


def search(query, key=None, pages=1, page_size=100):
    """Raw results across pages. With a key the results' `canDownload` reflects
    the plan; without one it reflects the free tier."""
    out = []
    for page in range(1, pages + 1):
        st, d = _get_json(search_url(query, page, page_size), key)
        _check(st, d, key, tier="free")
        out += d.get("results") or []
        if not d.get("next"):
            break
    return out


def lookup(asset_base_id, key=None):
    """One asset by its base id (the id the shortlist carries)."""
    st, d = _get_json(search_url(f"asset_base_id:{asset_base_id}", 1, 5), key)
    _check(st, d, key, tier="free")
    for r in d.get("results") or []:
        if r.get("assetBaseId") == asset_base_id:
            return r
    raise Refused(f"asset {asset_base_id} is not in the catalogue any more "
                  f"(search returned {len(d.get('results') or [])} other rows)",
                  code=1)


def download_url(fentry, key=None, tier="free"):
    """The signed file URL for one files[] entry, or Refused. The key is never
    attached to an off-site URL."""
    base = fentry.get("downloadUrl")
    if not on_site(base):
        raise Refused(f"download URL is off-site ({scrub(base, 60)}) — refusing "
                      f"to attach the key", code=2)
    st, d = _get_json(base + "?scene_uuid=" + str(uuid.uuid4()), key)
    if st == 200 and isinstance(d, dict) and d.get("filePath"):
        return d["filePath"]
    _check(st if st != 200 else 0, d, key, tier)


def _download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "studio-os/1.0"})
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=900) as r, \
                open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError) as e:
        try:
            os.remove(dest)
        except OSError:
            pass
        raise Refused(f"download failed: {type(e).__name__}: {scrub(e, 120)}", code=2)
    return os.path.getsize(dest)


def find_blender():
    sys.path.insert(0, HERE)
    import glance
    exe = glance.find_blender()
    if not exe:
        raise Refused("no Blender found ($INTERIOR_BLENDER / PATH / Program "
                      "Files) — cannot export .blend to GLB", code=2)
    return exe


def export_glb(blend_path, glb_path, blender=None, cache=None):
    """Spawn Blender on the asset's own .blend and export GLB. `--factory-startup
    -Y`: no user prefs, auto-run scripts OFF (third-party files). Refused(2) when
    the export produced nothing or Blender failed — an empty shelf entry must
    never print like a fetched one."""
    exe = blender or find_blender()
    script = os.path.join(cache or CACHE, "_export_glb.py")
    os.makedirs(os.path.dirname(script), exist_ok=True)
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(EXPORT_SCRIPT)
    cmd = export_cmd(exe, blend_path, script, glb_path)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
    except subprocess.TimeoutExpired:
        raise Refused("GLB export timed out after 1800 s", code=2)
    ok = os.path.exists(glb_path) and os.path.getsize(glb_path) > 0
    if p.returncode != 0 or not ok:
        tail = scrub((p.stdout or "") + (p.stderr or ""), 600)
        try:
            if os.path.exists(glb_path):
                os.remove(glb_path)
        except OSError:
            pass
        raise Refused(f"GLB export failed (blender exit {p.returncode}, "
                      f"file {'written' if ok else 'missing'}): …{tail[-400:]}", code=2)
    return glb_path


def export_cmd(exe, blend_path, script, glb_path):
    """PURE: the headless invocation, and the two flags that make opening 135
    third-party files unattended defensible."""
    return [exe, "-b", "--factory-startup", "-Y", "-noaudio", blend_path,
            "--python", script, "--", glb_path]


def fetch(asset_base_id, key=None, cls=None, resolution="blend",
          found_by=None, drop_blend=False, blender=None, result=None,
          cache=None):
    """Download one asset's .blend into the cache, export GLB, assert scale,
    then write SOURCE.json (+ LICENSE.txt). Returns (glb_path, report).

    Order of failure is the order of cost: Blender is resolved BEFORE any byte
    is downloaded; the signed URL is obtained BEFORE the shelf dir exists (a
    refusal leaves no ghost entry); SOURCE.json is written AFTER the sidecar so
    a dir with a SOURCE.json always has its scale verdict beside it.
    Idempotent on the GLB; a re-fetch keeps the earlier `found_by` and
    `derived_from` (a different --resolution on a cached GLB does not rewrite
    the provenance of bytes that were never downloaded)."""
    cache = cache or CACHE
    have = cached_ids(cache)
    dirname = have.get(asset_base_id) or have.get(_dehyphen(asset_base_id)) or asset_base_id
    base = os.path.join(cache, dirname)
    glb = os.path.join(base, f"{dirname}.glb")
    prior = _source(base) or {}
    r = result or lookup(asset_base_id, key)
    tier = tier_of(r)
    fe = file_entry(r, resolution)
    if fe is None:
        raise Refused(f"{asset_base_id} offers no {resolution!r} file (has: "
                      f"{', '.join(f.get('fileType') or '?' for f in r.get('files') or [])})",
                      code=1)
    fetched_now, derived_from = False, prior.get("derived_from")
    if not (os.path.exists(glb) and os.path.getsize(glb) > 0):
        exe = blender or find_blender()                 # before any byte moves
        signed = download_url(fe, key, tier)            # Refused on 401/403
        os.makedirs(base, exist_ok=True)
        suffix = "orig" if resolution == "blend" else resolution.replace(".", "_")
        blend = os.path.join(base, f"{dirname}.{suffix}.blend")
        _download(signed, blend)
        export_glb(blend, glb, exe, cache)
        fetched_now = True
        derived_from = (f"{fe.get('filename') or fe.get('downloadUrl')} (fileType "
                        f"{fe.get('fileType')}) -> GLB via headless Blender "
                        f"export_scene.gltf export_apply=True")
        if drop_blend:
            try:
                os.remove(blend)
            except OSError:
                pass
    note = os.path.join(cache, "LICENSE.txt")
    if not os.path.exists(note):
        with open(note, "w", encoding="utf-8") as f:
            f.write(LICENSE_NOTE)
    # SCALE IS ASSERTED ON EVERY INGEST (R8); asset_scale owns the one
    # implementation. Imported at the CLI edge, same as the sibling fetchers.
    sys.path.insert(0, HERE)
    import asset_scale as S
    ok, rep = S.write_sidecar(glb, cls)
    dp = r.get("dictParameters") or {}
    lic = r.get("license")
    if found_by is None or found_by == {"cmd": "fetch"}:
        found_by = prior.get("found_by") or found_by
    with open(os.path.join(base, "SOURCE.json"), "w", encoding="utf-8") as f:
        json.dump({
            "source": "blendkit.com (formerly blenderkit.com)",
            "asset_base_id": asset_base_id, "asset_version_id": r.get("id"),
            "name": r.get("name"), "category": r.get("category"),
            "tier": tier, "format": "glb",
            # a cached GLB keeps the resolution it was made from; a legacy row
            # with none recorded stays None rather than claiming this call's
            "resolution": resolution if fetched_now else prior.get("resolution"),
            "bytes": os.path.getsize(glb),
            "derived_from": derived_from,
            "dims_declared_m": {k: dp.get(k) for k in
                                ("dimensionX", "dimensionY", "dimensionZ")},
            "dims_caveat": "WHOLE-ASSET numbers (carry-on scenery included); "
                           "the sidecar measures the GLB, the bench measures "
                           "the truth in the room",
            "face_count_declared": dp.get("faceCount"),
            "found_by": found_by,
            "fetched": prior.get("fetched") if not fetched_now and prior.get("fetched")
            else _stamp()[1],
            "spend": (f"Blendkit Full plan, one-month trial ({ASK}, {ORDER})"
                      if tier == "full_plan" else "THB 0 (free tier)"),
            "license": lic,
            # machine-readable FIRST (repo_first reads license_id/source tokens;
            # scripts/asset_license.py knows these ids). Unstated stays unknown.
            "license_id": LICENSE_IDS.get(lic, "unknown"),
            "license_note": ("cc_zero: public domain" if lic == "cc_zero" else
                             "royalty-free: use in renders and client work yes, "
                             "redistribute as a model no; gitignored shelf"
                             if lic == "royalty_free" else
                             "LICENCE NOT STATED BY THE API — unknown, not permissive"),
            "scale_asserted": ok,
        }, f, indent=1, ensure_ascii=False)
    return glb, {"ok": ok, "class": cls, "tier": tier,
                 "fetched_now": fetched_now, "dir": dirname,
                 "measured_mm": rep.get("measured_mm"),
                 "band_mm": rep.get("band_mm"), "bbox_mm": rep.get("bbox_mm"),
                 "refusal": rep.get("planar_refusal") or rep.get("error"),
                 "in_band_under": rep.get("in_band_under")}


def _verdict(rep):
    return ("ASSERTED" if rep["ok"] else "UNASSERTED (no class)"
            if rep["ok"] is None else "REFUSED")


def read_spec(path=None):
    try:
        with open(path or SPEC, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


_SEP_BYTE = bytes([0])          # field separator, kept as a name so no source file carries a NUL


def instrument_digest(bands=None, ratios=None):
    """sha256 over the SCALE INSTRUMENT itself — asset_scale.BANDS and MIN_DEPTH_RATIO.

    WHY IT IS A SECOND DIGEST AND NOT AN EXTRA INPUT TO THE FIRST. `criteria_digest`
    hashes D-119's `in_effect`, the class file and the panel prompt, and its stored value
    was stamped at the first paid download on 2026-08-22. That value is EVIDENCE: it
    proves those three things have not moved since the clock started, and re-stamping it
    to admit a fourth input would destroy the only thing it is for. So the fourth input
    gets its own digest, stamped when it was actually first taken, and says so.

    WHAT IT CLOSES. D-120 recorded the hole in writing and it was still open today:
    "criteria_digest แฮช D-119 in_effect + classes + prompt — ไม่แฮชโค้ดของ rung จึงยัง
    พิมพ์ MATCH ทั้งที่ instrument เปลี่ยน". Half of C2's pass rule is "passes dim_check in
    its asset_scale class", so WIDENING A BAND moves the criterion without touching a
    single byte the criteria digest reads. Five of the seven classes still need bands
    written before their first paid fetch — which is exactly when a widened band would be
    most tempting and least visible.

    HONEST ABOUT ITS OWN START DATE: this digest begins on 2026-08-24, day 2 of the month,
    not at the clock start. It cannot say anything about 08-22 to 08-24, and `status` must
    not let it imply otherwise.
    """
    SEP = _SEP_BYTE
    if bands is None or ratios is None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import asset_scale as _asc
        bands = _asc.BANDS if bands is None else bands
        ratios = getattr(_asc, "MIN_DEPTH_RATIO", {}) if ratios is None else ratios
    h = hashlib.sha256()
    for k in sorted(bands):
        h.update(repr((k, tuple(bands[k]))).encode("utf-8"))
        h.update(SEP)
    h.update(SEP + b"RATIOS" + SEP)
    for k in sorted(ratios):
        h.update(repr((k, ratios[k])).encode("utf-8"))
        h.update(SEP)
    return h.hexdigest()


# RE-STAMPED 2026-08-26 (p2r78), and the reason this line was stale is worth more than
# the line. The freeze test has been RED since the 08-24 stamp: nine classes were added
# to asset_scale.BANDS across p2r74/75/77 — throw_folded, book_stack, book_single,
# basket_box, shoe_pair, potted_plant, clock_small, tray_decor, headboard — each with a
# cited reason in its own tuple, and none of them re-stamped here. That is the benign
# direction (additions, no existing band edited, so no past verdict changes), which is
# exactly why nobody noticed.
#
# WHAT DID NOTICE, AND WHAT DID NOT: three gate artifacts in a row reported "tests
# green" from PER-FILE runs (54 + 55 + 141). A full `pytest pipeline/scripts` was red
# the whole time. A suite reported by the sum of its chosen subsets is the selected-
# sample defect this repo has already filed once (plan-gate, 2026-08-xx) — the set that
# gets run is chosen by the person whose change is being tested.
# FROZEN_AT stays 2026-08-24: it records when the freeze STARTED — its own test says
# the instrument "cannot speak for 08-22..08-24 and must not imply it can" — so moving
# it to the re-stamp date would erase the honest gap. The SHA is what tracks the bands.
INSTRUMENT_FROZEN_AT = "2026-08-24"
INSTRUMENT_RESTAMPED_AT = "2026-08-26"
INSTRUMENT_FROZEN_SHA = "e49106d7d175a0e9b7514c09784d64758e8e53ae24ff41158561d598ac735a90"


def load_results(path=None):
    """The month's RESULTS — baselines and paid outcomes — read from the unhashed file.

    Returns {} when the file is absent, because "no results yet" is a real state and
    must not be an error. It is deliberately NOT merged back into CLASSES: the whole
    point is that running the test cannot edit the test.
    """
    try:
        with open(path or RESULTS, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def current_digest(decisions_path=None, classes_path=None, prompt_path=None):
    """The criteria digest as the files stand now; None when D-119 is absent."""
    try:
        with open(decisions_path or DECISIONS, "rb") as fh:
            rows = json.loads(fh.read().decode("utf-8")).get("decisions") or []
    except (OSError, ValueError):
        return None
    row = next((d for d in rows if d.get("id") == CRITERIA), None)
    if not row:
        return None

    def _b(p):
        try:
            with open(p, "rb") as fh:
                return fh.read()
        except OSError:
            return b""
    return criteria_digest(row.get("in_effect"), _b(classes_path or CLASSES),
                           _b(prompt_path or PANEL_PROMPT))


def run_shortlist(key, limit=None, cls="whole_bed", resolution="blend",
                  dry_run=False, path=None, tier="full_plan", cache=None,
                  log=None):
    """Walk the 08-18 shortlist's bench-worthy rows of `tier` into the cache in
    its rank order; assert scale; LOG ALL OF IT. Stops at the shelf: the bench
    (wholebed_bench.py, in Blender, in the real room) is printed as the next
    command with its fit rect DERIVED from the spec.

    EXIT CONTRACT: no key while full-plan rows are wanted -> Refused(2) (the
    command the month runs must not print 'done' when it fetched nothing for
    want of the key); any code-2 refusal stops the walk (a bad key or a missing
    Blender would otherwise cost one API call or one download per row); fetched
    but none scale-asserted -> 1."""
    path = path or SHORTLIST
    try:
        with open(path, encoding="utf-8") as fh:
            sl = json.load(fh)
    except (OSError, ValueError) as e:
        raise Refused(f"no readable shortlist at {scrub(path, 80)}: "
                      f"{type(e).__name__}", code=2)
    rows = shortlist_rows(sl, tier)
    keep, skip = plan_fetch(rows, cached_ids(cache), bool(key), limit=limit)
    n_key = sum(1 for s in skip if ASK in s["why"])
    print(f"SHORTLIST {tier}: {len(rows)} bench-worthy row(s); {len(keep)} to "
          f"fetch, {len(skip)} passed over "
          f"({sum(1 for s in skip if 'already cached' in s['why'])} on the shelf, "
          f"{n_key} waiting on {ASK})")
    rec = _record("shortlist", key, probe=dry_run, tier=tier, assert_class=cls,
                  resolution=resolution, limit=limit, n_rows=len(rows),
                  fetched=False, fetched_ids=[], asserted_ids=[], scale={},
                  refusals={}, skipped={"by_reason": {}, "first_ids": []})
    for s in skip:
        why = s["why"].split(" as ")[0] if "already cached" in s["why"] else s["why"]
        rec["skipped"]["by_reason"][why] = rec["skipped"]["by_reason"].get(why, 0) + 1
    rec["skipped"]["first_ids"] = [s.get("assetBaseId") for s in skip[:5]]
    if not keep and n_key and not dry_run:
        rec["refusals"]["*"] = refusal(401, "full_plan", False)
        rec["exit"] = 2
        log_run(rec, log)
        raise Refused(refusal(401, "full_plan", False), code=2, logged=True)
    fetched, asserted, refusals = [], [], {}
    stop = None
    if not dry_run and keep:
        exe = find_blender()                            # once, before the walk
        for r in keep:
            bid = r["assetBaseId"]
            try:
                p, rep = fetch(bid, key, cls=cls, resolution=resolution,
                               found_by={"shortlist": os.path.relpath(path, REPO)
                                         if path.startswith(REPO) else "<shortlist>",
                                         "rank_note": r.get("note")},
                               blender=exe, cache=cache)
                fetched.append(bid)
                if rep["ok"]:
                    asserted.append(bid)
                rec["scale"][bid] = {k: rep.get(k) for k in
                                     ("ok", "tier", "measured_mm", "band_mm", "refusal")}
                print(f"  fetched {bid[:8]} {str(r.get('name'))[:40]:40s} "
                      f"{os.path.getsize(p) / 1e6:7.1f} MB  scale {_verdict(rep)}"
                      + (f" ({rep['measured_mm']} mm vs {rep['band_mm']})"
                         if rep.get("measured_mm") is not None else ""))
            except Refused as e:
                refusals[bid] = {"code": e.code, "why": scrub(e)}
                print(f"  REFUSED {bid[:8]} (exit {e.code}): {scrub(e, 140)}")
                if e.code == 2:
                    stop = scrub(e)
                    print("  -> stopping: a could-not-run reason repeats for every row")
                    break
            except Exception as e:                              # noqa: BLE001
                refusals[bid] = {"code": 2, "why": f"{type(e).__name__}: {scrub(e, 160)}"}
                print(f"  FETCH FAILED {bid[:8]}: {type(e).__name__}: {scrub(e, 120)}")
                if sum(1 for v in refusals.values() if v["code"] == 2) >= 2:
                    stop = f"two consecutive failures ({type(e).__name__})"
                    print("  -> stopping: two failures in a row (stop-loss)")
                    break
    rec.update(fetched=bool(fetched), fetched_ids=fetched, asserted_ids=asserted,
               refusals=refusals, stopped_by=stop,
               exit=2 if stop else 1 if (fetched and not asserted) else 0)
    if fetched and tier == "full_plan":
        rec["criteria_sha256"] = current_digest()
    log_run(rec, log)
    print(f"logged -> {os.path.basename(log or log_path())}")
    if asserted:
        rect = bench_rect(read_spec())
        print("NEXT (the bench, in the real room — rules in wholebed_rules.py):\n"
              "  blender -b pipeline/output/room_bedroom_suite_eye_<round>.blend "
              "--python pipeline/scripts/wholebed_bench.py -- "
              "assets/shared/blenderkit <out_dir> "
              + (rect if rect else "<could not derive the bed rect from the spec — "
                                   "fix the spec, do not type one>")
              + " " + ",".join(asserted))
    if stop:
        raise Refused(stop, code=2, logged=True)
    if fetched and not asserted:
        raise Refused("fetched, but no asset passed its scale assertion — nothing "
                      "here may reach the bench", code=1, logged=True)
    return fetched, asserted, refusals


def latest_built_blend(output_dir=None, pattern=re.compile(r"^room_bedroom_suite_eye_p2r(\d+)\.blend$")):
    """The newest full-fidelity build of record (room_bedroom_suite_eye_p2rNN.blend,
    highest NN; never a _ql playblast), or None."""
    d = output_dir or os.path.join(REPO, "pipeline", "output")
    best = None
    for name in os.listdir(d) if os.path.isdir(d) else []:
        m = pattern.match(name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), os.path.join(d, name))
    return best[1] if best else None


def last_asserted_ids(log=None):
    """PURE on the log: asserted ids of the newest non-probe shortlist run."""
    runs = load_log(log).get("runs") or []
    for r in reversed(runs):
        if r.get("cmd") == "shortlist" and not r.get("probe") and r.get("asserted_ids"):
            return list(r["asserted_ids"])
    return []


def bench_cmd(blender, blend, out_dir, rect, ids, cache=None):
    """PURE: the wholebed_bench invocation — rect and ids are DERIVED, never typed."""
    return [blender, "-b", blend, "--python", os.path.join(HERE, "wholebed_bench.py"),
            "--", cache or CACHE, out_dir, rect, ",".join(ids)]


def run_bench(out_dir, ids=None, blend=None, log=None):
    """Stage the asserted full-plan beds in the real room (wholebed_bench.py)."""
    ids = ids or last_asserted_ids(log)
    if not ids:
        raise Refused("no asserted ids: run `shortlist` first (or pass ids)", code=2)
    rect = bench_rect(read_spec())
    if not rect:
        raise Refused("could not derive the bed rect from the spec — fix the spec, "
                      "do not type a rect", code=2)
    blend = blend or latest_built_blend()
    if not blend:
        raise Refused("no room_bedroom_suite_eye_p2rNN.blend under pipeline/output", code=2)
    exe = find_blender()
    # ABSOLUTE, always: Blender resolves a bare relative render path against
    # the drive root, not the cwd — chunk A's PNGs landed in C:\_private\...
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    cmd = bench_cmd(exe, blend, out_dir, rect, ids)
    print(f"BENCH {len(ids)} candidate(s) in {os.path.basename(blend)} rect {rect} -> {out_dir}",
          flush=True)
    # Blender's output STREAMS to <out>/bench.log line by line (and WHOLEBED
    # lines echo here), so a stalled candidate is visible while it stalls —
    # the first run captured everything until the end and showed nothing for
    # 29 minutes.
    bench_log = os.path.join(out_dir, "bench.log")
    lines, tail = [], []
    with open(bench_log, "a", encoding="utf-8") as lg, \
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace",
                             bufsize=1) as p:
        for ln in p.stdout:
            lg.write(ln)
            lg.flush()
            tail = (tail + [ln])[-40:]
            if ln.startswith("WHOLEBED"):
                lines.append(ln.rstrip())
                print("  " + ln.rstrip(), flush=True)
        p.wait()
    res = os.path.join(out_dir, "wholebed_bench.json")
    if p.returncode != 0 or not os.path.exists(res):
        raise Refused(f"bench did not complete (blender exit {p.returncode}): "
                      f"{scrub(''.join(tail)[-500:], 400)}", code=2)
    log_run(_record("bench", read_key(), fetched=False, blend=os.path.basename(blend),
                    rect=rect, ids=ids, out=os.path.relpath(out_dir, REPO) if out_dir.startswith(REPO) else "<out>",
                    result_lines=lines[-len(ids) - 1:]), log)
    return res


def me(key):
    """(status, plan-shaped scalar fields) from /api/v1/me/ — identity never."""
    st, d = _get_json(f"{API}/me/", key)
    return st, (me_summary(d) if st == 200 and isinstance(d, dict) else {})


def status(key, today=None, cache=None, log=None):
    """The month, in numbers, printed — never a gate. Exit 2 when the month
    cannot run (no key, or a key the site refuses)."""
    today = today or datetime.date.today()
    code = 0
    print(f"BLENDKIT — {ORDER}")
    print(f"  key in .env ({KEY_NAME}): {'yes' if key else 'NO'}")
    plan = {}
    if key:
        st, plan = me(key)
        if st != 200:
            print(f"  /me: HTTP {st} — {refusal(st, 'full_plan', True)}")
            code = 2
        else:
            print(f"  /me: HTTP 200 {json.dumps(plan, ensure_ascii=False) if plan else '(no plan-shaped fields)'}")
    c = shelf_counts(cache)
    for t in ("free", "full_plan"):
        v = c.get(t, {})
        print(f"  shelf {t:9s}: asserted {v.get('asserted', 0)} · refused "
              f"{v.get('refused', 0)} · unasserted {v.get('unasserted', 0)}")
    runs = load_log(log).get("runs") or []
    real = [r for r in runs if not r.get("probe")]
    print(f"  logged runs: {len(runs)} ({len(runs) - len(real)} probe)")
    clock = month_clock(runs, today)
    if clock:
        first, elapsed, left = clock
        print(f"  MONTH CLOCK: first paid download {first} · day {elapsed} of "
              f"{MONTH_DAYS} · {left} day(s) left to answer him with numbers")
        stored = next((r.get("criteria_sha256") for r in real
                       if r.get("criteria_sha256")), None)
        now = current_digest()
        if stored and now:
            print(f"  criteria freeze ({CRITERIA} + classes + panel prompt): "
                  f"{'MATCH' if stored == now else 'CHANGED SINCE THE CLOCK STARTED — an edit after seeing results is the flattering-scorer defect; say so in the gate'}")
            _ind = instrument_digest()
            print("  instrument freeze (asset_scale BANDS + MIN_DEPTH_RATIO), stamped "
                  + INSTRUMENT_FROZEN_AT + " — NOT at the clock start, so it says "
                  "nothing about 2026-08-22..24: "
                  + ("MATCH" if _ind == INSTRUMENT_FROZEN_SHA else
                     "CHANGED — half of C2's pass rule is 'passes dim_check in its "
                     "asset_scale class', so a widened band moves the criterion "
                     "without touching a byte the criteria digest reads (D-120's "
                     "recorded blind spot). Say in the gate WHICH band moved, and "
                     "its cited source."))
    else:
        print(f"  MONTH CLOCK: not started — no full-plan asset fetched yet "
              f"({ASK}: pay the 30-day glimpse, paste the key; the clock starts "
              f"at the first paid download)")
    try:
        with open(CLASSES, encoding="utf-8") as fh:
            classes = json.load(fh).get("classes") or []
        res = load_results()
        rec = res.get("classes") or {}
        missing = [c["key"] for c in classes
                   if not (c.get("free_baseline")
                           or (rec.get(c["key"]) or {}).get("free_baseline"))]
        print(f"  C2 classes pre-registered: {len(classes)} · free baseline "
              f"still to run BEFORE a paid fetch in that class: "
              f"{', '.join(missing) if missing else 'none'}")
        paid = {k: v for k, v in rec.items() if (v or {}).get("paid_result")}
        inreg = {c["key"] for c in classes}
        print(f"  C2 paid results recorded: "
              f"{', '.join(sorted(paid)) if paid else 'none'} "
              f"(in {os.path.relpath(RESULTS, REPO)}, deliberately OUTSIDE the hash)")
        extra = sorted(set(rec) - inreg)
        if extra:
            print(f"  OUT-OF-TEST classes (shopped for, NOT evidence for C2 — they were "
                  f"not pre-registered): {', '.join(extra)}")
    except (OSError, ValueError):
        print(f"  C2 classes: {os.path.relpath(CLASSES, REPO)} unreadable")
    print(f"  criteria (frozen at the first paid download): {CRITERIA} in "
          f"qa/open-decisions.json · the plan: {MONTH_DOC}")
    if key and plan:
        log_run(_record("status", key, probe=False, fetched=False, me=plan), log)
    if not key:
        print(f"  -> {refusal(401, 'full_plan', False)}")
        return 2
    return code


# -------------------------------------------------------------------- the CLI --

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log", default=None,
                    help=f"run log path (default qa/blenderkit-fetch-log.json or "
                         f"$BLENDERKIT_LOG) — tests and probes point this elsewhere")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status", help="key present? plan? shelf? month clock?")
    s.add_argument("--no-key", action="store_true", help="pretend no key")
    k = sub.add_parser("key", help="write BLENDERKIT_API_KEY into the repo .env — --login "
                                   "(the add-on's own OAuth flow in your browser; nothing to "
                                   "copy), or a value you type in your own terminal (never "
                                   "paste the key into a chat), or --from-blender (read it from "
                                   "the logged-in add-on's preferences) — then run status")
    k.add_argument("value", nargs="?", default=None)
    k.add_argument("--login", action="store_true")
    k.add_argument("--from-blender", action="store_true")
    k.add_argument("--timeout", type=int, default=300)
    q = sub.add_parser(
        "search", help="catalogue search (logged as a probe, no download)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=SEARCH_GRAMMAR)
    q.add_argument("query", help='e.g. "bed modern" or "asset_type:model+rug" '
                                 '— see the filter grammar below')
    q.add_argument("--pages", type=int, default=1)
    q.add_argument("--page-size", type=int, default=100)
    q.add_argument("--free-only", action="store_true")
    q.add_argument("--json", default=None, help="write the compact rows here")
    f = sub.add_parser("fetch", help="one asset by assetBaseId -> GLB + sidecar")
    f.add_argument("asset_base_id")
    f.add_argument("--assert-class", default=None, dest="cls",
                   help="scale class from asset_scale.BANDS (R8: asserted, never "
                        "assumed); omitting records bounds only")
    f.add_argument("--resolution", default="blend", choices=sorted(RESOLUTIONS))
    f.add_argument("--drop-blend", action="store_true")
    w = sub.add_parser("shortlist", help="walk the 08-18 bed shortlist (full plan)")
    w.add_argument("--limit", type=int, default=10)
    w.add_argument("--tier", default="full_plan", choices=("full_plan", "free"))
    w.add_argument("--assert-class", default="whole_bed", dest="cls")
    w.add_argument("--resolution", default="2K", choices=sorted(RESOLUTIONS))
    w.add_argument("--dry-run", action="store_true")
    w.add_argument("--path", default=None)
    b = sub.add_parser("bench", help="stage the last shortlist's asserted beds in the real "
                                     "room (wholebed_bench.py; rect from the spec, blend = "
                                     "newest p2rNN build)")
    b.add_argument("--out", required=True)
    b.add_argument("--blend", default=None)
    b.add_argument("ids", nargs="*")
    a = ap.parse_args(argv)
    log = a.log

    key = None if getattr(a, "no_key", False) else read_key()
    try:
        if key and a.cmd in ("status", "search", "fetch", "shortlist"):
            key = ensure_fresh_key(key)
        if a.cmd == "key":
            if a.login:
                import time
                tok = login(timeout_s=a.timeout)
                key = write_key(tok["access_token"], refresh=tok.get("refresh_token"),
                                expires=time.time() + float(tok.get("expires_in") or 0))
                how = (f"from the browser login (expires in "
                       f"{int(float(tok.get('expires_in') or 0)) // 3600} h; refresh token stored)")
            elif a.from_blender:
                key = write_key(key_from_blender())
                how = "read from the BlenderKit add-on"
            elif a.value:
                key = write_key(a.value)
                how = "typed"
            else:
                raise Refused("key: --login, a value, or --from-blender", code=1)
            print(f"  {KEY_NAME} written to .env ({len(key)} chars, {how}) — testing it:")
            return status(key, log=log)
        if a.cmd == "status":
            return status(key, log=log)
        if a.cmd == "search":
            qry = a.query + ("+is_free:true" if a.free_only else "")
            res = search(qry, key, pages=a.pages, page_size=a.page_size)
            rows = [row_of(r) for r in res]
            free = sum(1 for r in rows if r["tier"] == "free")
            for r in rows[:40]:
                dims = "x".join(f"{(r[k] or 0) * 1000:.0f}"
                                for k in ("dim_x_m", "dim_y_m", "dim_z_m"))
                print(f"  {r['tier']:9s} {str(r['assetBaseId'])[:8]} "
                      f"{str(r['name'])[:44]:44s} {dims:>16s} mm  "
                      f"{r['faceCount'] or 0:>8} faces")
            print(f"{len(rows)} row(s): free {free} · full_plan {len(rows) - free}"
                  + ("  (first 40 shown)" if len(rows) > 40 else ""))
            if a.json:
                with open(a.json, "w", encoding="utf-8") as fh:
                    json.dump(rows, fh, indent=1, ensure_ascii=False)
            log_run(_record("search", key, probe=True, query=qry, pages=a.pages,
                            n=len(rows), free=free, full_plan=len(rows) - free,
                            fetched=False), log)
            return 0
        if a.cmd == "fetch":
            path, rep = fetch(a.asset_base_id, key, cls=a.cls,
                              resolution=a.resolution, drop_blend=a.drop_blend,
                              found_by={"cmd": "fetch"})
            rec = _record("fetch", key, asset=a.asset_base_id, tier=rep["tier"],
                          fetched=True, fetched_now=rep["fetched_now"],
                          assert_class=a.cls, resolution=a.resolution,
                          scale={k: rep.get(k) for k in
                                 ("ok", "measured_mm", "band_mm", "refusal")})
            if rep["tier"] == "full_plan" and rep["fetched_now"]:
                rec["criteria_sha256"] = current_digest()
            log_run(rec, log)
            print(f"fetched {path} ({os.path.getsize(path)} bytes) tier={rep['tier']}")
            if rep["ok"] is None:
                print("  UNIT NOT ASSERTED (no --assert-class). Nothing may "
                      "consume this until a class is named.")
                return 0
            print(f"  scale {_verdict(rep)}: {rep.get('measured_mm')} mm vs band "
                  f"{rep.get('band_mm')}"
                  f"{' — ' + str(rep['refusal']) if rep.get('refusal') else ''}")
            return 0 if rep["ok"] else 1
        if a.cmd == "bench":
            res = run_bench(a.out, ids=a.ids or None, blend=a.blend, log=log)
            print(f"bench rows -> {res}")
            return 0
        run_shortlist(key, limit=a.limit, cls=a.cls, resolution=a.resolution,
                      dry_run=a.dry_run, path=a.path, tier=a.tier, log=log)
        return 0
    except Refused as e:
        if not e.logged:
            try:
                log_run(_record(a.cmd, key, asset=getattr(a, "asset_base_id", None),
                                fetched=False, exit=e.code, refusal=scrub(e)), log)
            except Refused as e2:                   # the log itself is the problem
                print(f"REFUSED (exit 2): {e2}")
                return 2
        print(f"REFUSED (exit {e.code}): {e}")
        return e.code
    except Exception as e:                          # noqa: BLE001 — last resort
        try:
            log_run(_record(a.cmd, key, fetched=False, exit=2,
                            refusal=f"could not run: {type(e).__name__}: {scrub(e)}"),
                    log)
        except Refused:
            pass
        print(f"COULD NOT RUN (exit 2): {type(e).__name__}: {scrub(e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
