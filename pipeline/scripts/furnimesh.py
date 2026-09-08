"""furnimesh.py — list and fetch free models from FurniMesh (furnimesh.com).

CLI-ONLY, like `warehouse.py`: run by hand during an R8 ACQUIRE decision —
`python pipeline/scripts/furnimesh.py list lighting/table-lamp` then
`... sweep lighting/table-lamp --limit 4 --assert-class table_lamp`.
Queries are generic by the same privacy rule as the NLM lane — no client names,
no client dimensions; a category path is all that ever leaves this machine.

WHY THIS EXISTS, and why it took a paid Deep Research to trigger it.
`docs/LICENSING.md` ranked FurniMesh FIRST ("cleanest — the ONLY source legal to
script-fetch", with an explicit automation carve-out) and the shelf held 0 files
from it while every model came from the source the same table marks "manual
download only". `repo_first.py` was written from that instance; this module is
the consumer that closes it (ORD-2026-08-22-process-review-actions item 3).

LICENCE — verified LIVE on the library pages, 2026-08-22 (re-verifying the
2026-08-17 check recorded in `knowledge/_inbox/nlm-free-asset-sources/`):
  * "all 3D models in this library are free for commercial use without
    attribution ... no royalties, no licensing fees, and no 'personal use only'
    restrictions on either the free tier or paid plans"  (furnimesh.com/library/)
  * "All models are provided under a perpetual, royalty-free license for
    unrestricted commercial use, requiring no attribution"  (category pages)
The grant is USE, not redistribution of the models themselves, so the cache is
gitignored exactly like the Warehouse and BlenderKit shelves (.gitignore) and a
LICENSE.txt sits beside the models. Operated by UAB FURNISYSTEMS (Lithuania).

WHAT THE SITE IS, mechanically (probed 2026-08-22). A Next.js app; the library
is server-rendered HTML: category pages (`/library/<cat>/<sub>/`, 24 models a
page, `?page=N`) carry plain model hrefs, and every model page embeds
schema.org JSON-LD — a `3DModel` block whose `encoding` list names direct
download URLs on storage.googleapis.com with `contentSize`, `license` and
`isAccessibleForFree: true`. GLB and OBJ need no account; SKP/BLEND do, so this
module fetches GLB (the shelf's native format — mesh_import.EXT_PREFERENCE).
The 2026-08-17 recon read "no JSON payload, no /api/ route" from the HOME page;
the library pages turned out to carry the whole contract in JSON-LD.

CAVEAT THAT IS THE CLASS, NOT A FOOTNOTE: these are AI photo→3D models
(`examples/furniture_catalog.example.json` already carries `fit: true` "for
inaccurate/AI models, e.g. FurniMesh"). An AI-generated mesh has no reason to
arrive at real-world scale, so the R8 scale assertion is not a formality here —
expect refusals, and record them as results, not failures. Scale is ASSERTED on
every fetch via `asset_scale.write_sidecar` (same call as `warehouse.py`).

THE SEARCH LOG lives in `qa/furnimesh-search-log.json`, same spirit and reason
as `qa/warehouse-search-log.json`: "we looked and there is nothing" must be a
checkable sentence, so every listing, every skip reason, every fetch and every
scale verdict is appended there — never rewritten.

    python pipeline/scripts/furnimesh.py list lighting/table-lamp
    python pipeline/scripts/furnimesh.py sweep tables/nightstand --limit 4 \
        --assert-class nightstand
    python pipeline/scripts/furnimesh.py fetch <model-page-url> --assert-class vase
"""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                   # noqa: BLE001
    pass

SITE = "https://furnimesh.com"
# same reasoning as assets.py / warehouse.py: this machine sits behind a
# TLS-intercepting VPN, so certificates do not verify against the default store
_CTX = ssl._create_unverified_context()
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(REPO, "assets", "shared", "furnimesh")
SEARCH_LOG = os.path.join(REPO, "qa", "furnimesh-search-log.json")

LICENSE_NOTE = """FurniMesh (furnimesh.com) models — library licence, verified live 2026-08-22.

The library pages state, verbatim: "all 3D models in this library are free for
commercial use without attribution ... There are no royalties, no licensing
fees, and no 'personal use only' restrictions", and "All models are provided
under a perpetual, royalty-free license for unrestricted commercial use,
requiring no attribution". Operated by UAB FURNISYSTEMS (Lithuania).

The grant is USE in our own work (renders, client scenes). It is not an
explicit grant to redistribute the model files, so this directory is
gitignored on purpose — same law as the 3D Warehouse and BlenderKit shelves.
Fetch is reproducible instead: every model's page URL is in its SOURCE.json.

These are AI photo->3D models: scale is asserted on every fetch
(<asset>.scale.json beside each file) and a refusal is recorded, never shrugged.
"""


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "studio-os/1.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=timeout) as r:
        return r.read()


# ------------------------------------------------------------------ pure part --

def cat_path(category):
    """'lighting/table-lamp' -> '/library/lighting/table-lamp/'. Accepts the
    already-slashed form too, so a pasted href round-trips."""
    c = "/" + category.strip("/") + "/"
    if not c.startswith("/library/"):
        c = "/library" + c
    return c


def model_links(html, category):
    """Model-page paths under one category, in page order, deduped. PURE.

    The category page carries them as plain quoted hrefs
    ("/library/lighting/table-lamp/<slug>/"); anchoring to the category path
    keeps related-model links from other categories out."""
    pat = re.escape(cat_path(category)) + r"[a-z0-9][a-z0-9-]*/"
    out, seen = [], set()
    for m in re.findall(r'"(%s)"' % pat, html or ""):
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def slug_of(model_path):
    """Last path segment = the shelf directory name, like warehouse's entity id."""
    return model_path.rstrip("/").rsplit("/", 1)[-1]


def _ld_blocks(html):
    for raw in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            html or "", re.S):
        try:
            yield json.loads(raw)
        except ValueError:
            continue


def parse_model(html):
    """{name, formats: {ext: {url, bytes}}} from a model page's JSON-LD. PURE.

    Reads the `3DModel` block's `encoding` list — the page's own machine-readable
    statement of what may be downloaded (each entry carries `license` and
    `isAccessibleForFree`). Raises ValueError when the block is absent, because
    a page with no downloads must not print like an empty catalogue entry."""
    fmt_by_enc = {"model/gltf-binary": "glb", "model/obj": "obj",
                  "model/vnd.sketchup": "skp", "application/x-blender": "blend"}
    for d in _ld_blocks(html):
        if d.get("@type") != "3DModel":
            continue
        formats = {}
        for enc in d.get("encoding") or []:
            ext = fmt_by_enc.get(enc.get("encodingFormat"))
            url = enc.get("contentUrl")
            if not ext or not url:
                continue
            try:
                size = int(enc.get("contentSize") or 0)
            except (TypeError, ValueError):
                size = 0
            formats[ext] = {"url": url, "bytes": size}
        return {"name": d.get("name") or "?", "formats": formats}
    raise ValueError("no 3DModel JSON-LD block on this page — not a model page, "
                     "or the site changed shape; refused rather than guessed")


def cached_slugs(cache=CACHE):
    """Every slug already on the shelf, from the SOURCE.json files themselves
    (same rule as warehouse.cached_ids: the shelf is the fact, the log is a
    record of asks)."""
    out = {}
    for name in sorted(os.listdir(cache)) if os.path.isdir(cache) else []:
        if os.path.isfile(os.path.join(cache, name, "SOURCE.json")):
            out[name] = name
    return out


def plan_fetch(rows, have, limit=None):
    """PURE. Which listed models to fetch, and why each other one is passed over.

    `rows` [{slug, path, ...}] in SITE order — FurniMesh is hand-curated, so page
    order is the library's own ranking and this module does not re-rank (unlike
    warehouse.plan_sweep, whose bytes-rank exists because 3DW density starves the
    bed lane; nothing here has measured a reason to re-order). A `limit` is an
    operational cap and every row past it is logged with that reason — no silent
    caps."""
    keep, skip = [], []
    for r in rows:
        if r["slug"] in have:
            skip.append({**r, "why": f"already cached as {have[r['slug']]}"})
        elif limit is not None and len(keep) >= limit:
            skip.append({**r, "why": f"past --limit {limit} in page order"})
        else:
            keep.append(r)
    return keep, skip


def log_run(record, path=SEARCH_LOG):
    """Append one run to the search log. Never rewrites a prior run."""
    runs = []
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                runs = json.load(fh).get("runs") or []
        except (OSError, ValueError):
            runs = []
    runs.append(record)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"_what": "Every FurniMesh listing/fetch this repo has run, "
                            "with what came back, what was skipped and why, and "
                            "each fetch's scale-assert verdict. Same law as "
                            "qa/warehouse-search-log.json: 'we looked and there "
                            "is nothing' must be checkable.",
                   "runs": runs}, fh, indent=1, ensure_ascii=False)
    return path


# --------------------------------------------------------------- network part --

def list_category(category, pages=1):
    """[{slug, path, page}] for up to `pages` pages of one category."""
    rows = []
    for page in range(1, pages + 1):
        url = SITE + cat_path(category) + (f"?page={page}" if page > 1 else "")
        html = _get(url).decode("utf-8", errors="ignore")
        links = model_links(html, category)
        if not links:
            break
        for p in links:
            rows.append({"slug": slug_of(p), "path": p, "page": page})
    # a later page can repeat a trending model from an earlier one
    seen, out = set(), []
    for r in rows:
        if r["slug"] not in seen:
            seen.add(r["slug"])
            out.append(r)
    return out


def fetch(model_path, cls=None, found_by=None):
    """Download one model's GLB into the cache; write SOURCE.json + LICENSE.txt;
    assert scale. Returns (local_path, scale_report_or_None).

    Idempotent on the binary (an existing non-empty file is kept) but the page
    is always re-read so SOURCE.json carries the site's current statement."""
    slug = slug_of(model_path)
    page_url = SITE + model_path if model_path.startswith("/") else model_path
    html = _get(page_url).decode("utf-8", errors="ignore")
    meta = parse_model(html)
    glb = meta["formats"].get("glb")
    if not glb:
        raise SystemExit(f"furnimesh: {slug} offers no GLB "
                         f"(has: {', '.join(sorted(meta['formats'])) or 'nothing'})"
                         f" — refused; GLB is the account-free format")
    base = os.path.join(CACHE, slug)
    os.makedirs(base, exist_ok=True)
    note = os.path.join(CACHE, "LICENSE.txt")
    if not os.path.exists(note):
        with open(note, "w", encoding="utf-8") as f:
            f.write(LICENSE_NOTE)
    with open(os.path.join(base, "SOURCE.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "furnimesh.com", "model_url": page_url,
                   "name": meta["name"], "format": "glb",
                   "bytes": glb["bytes"], "content_url": glb["url"],
                   "found_by": found_by,
                   # machine-readable FIRST (same contract as warehouse.py's
                   # trimble-gml): 'furnimesh' is the first token of the
                   # permissive set build_room.rb enforces
                   "license_id": "furnimesh",
                   "license": "FurniMesh library licence — perpetual, "
                              "royalty-free, unrestricted commercial use, no "
                              "attribution (verified live 2026-08-22); use yes, "
                              "redistribute as a model no"}, f, indent=1,
                  ensure_ascii=False)
    dest = os.path.join(base, f"{slug}.glb")
    if not (os.path.exists(dest) and os.path.getsize(dest) > 0):
        req = urllib.request.Request(glb["url"],
                                     headers={"User-Agent": "studio-os/1.0"})
        with urllib.request.urlopen(req, context=_CTX, timeout=600) as r, \
                open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
    # SCALE IS ASSERTED ON EVERY INGEST (R8; asset_scale owns the one
    # implementation — the warehouse/assets split taught why). Import at the
    # CLI edge, same as warehouse.py.
    import asset_scale as S
    ok, rep = S.write_sidecar(dest, cls)
    return dest, {"ok": ok, "class": cls,
                  "measured_mm": rep.get("measured_mm"),
                  "band_mm": rep.get("band_mm"),
                  "bbox_mm": rep.get("bbox_mm"),
                  "refusal": rep.get("planar_refusal") or rep.get("error"),
                  "in_band_under": rep.get("in_band_under")}


def sweep(category, limit=None, pages=1, cls=None, dry_run=False):
    """List a category, fetch what the plan keeps, assert scale, LOG ALL OF IT."""
    from datetime import datetime, timezone
    rows = list_category(category, pages)
    print(f"SWEEP {category!r}: {len(rows)} model(s) listed over {pages} page(s)")
    keep, skip = plan_fetch(rows, cached_slugs(), limit=limit)
    print(f"  {len(keep)} to fetch, {len(skip)} passed over "
          f"({sum(1 for s in skip if 'already cached' in s['why'])} already on "
          f"the shelf)")
    fetched, scale = [], {}
    if not dry_run:
        for r in keep:
            try:
                p, rep = fetch(r["path"], cls=cls,
                               found_by={"category": category, "page": r["page"]})
                fetched.append(r["slug"])
                scale[r["slug"]] = rep
                verdict = ("ASSERTED" if rep["ok"]
                           else "UNASSERTED (no class)" if rep["ok"] is None
                           else "REFUSED")
                print(f"  fetched {r['slug'][:52]:52s} "
                      f"{os.path.getsize(p) / 1e6:7.2f} MB  scale {verdict}"
                      + (f" ({rep['measured_mm']} mm vs {rep['band_mm']})"
                         if rep.get("measured_mm") is not None else ""))
            except Exception as e:                            # noqa: BLE001
                r["fetch_error"] = str(e)[:160]
                print(f"  FETCH FAILED {r['slug']}: {str(e)[:90]}")
    log_run({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "category": category, "pages": pages, "limit": limit,
             "assert_class": cls, "dry_run": bool(dry_run),
             "n_listed": len(rows), "fetched": fetched, "scale": scale,
             "hits": rows, "skipped": skip})
    print(f"SWEEP logged -> {SEARCH_LOG}")
    return fetched


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list", help="list a category's model pages (logged)")
    ls.add_argument("category", help="e.g. lighting/table-lamp")
    ls.add_argument("--pages", type=int, default=1)
    w = sub.add_parser("sweep", help="list -> fetch -> scale-assert, all logged")
    w.add_argument("category")
    w.add_argument("--limit", type=int, default=None,
                   help="fetch at most N, in the library's own page order")
    w.add_argument("--pages", type=int, default=1)
    w.add_argument("--assert-class", default=None, dest="cls",
                   help="scale class from asset_scale.BANDS (R8: asserted, "
                        "never assumed); omitting records bounds only")
    w.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("fetch")
    f.add_argument("model_url", help="model page URL or /library/... path")
    f.add_argument("--assert-class", default=None, dest="cls")
    a = ap.parse_args(argv)

    if a.cmd == "list":
        rows = list_category(a.category, a.pages)
        for r in rows:
            print(f"  p{r['page']}  {r['slug']}")
        print(f"{len(rows)} model(s)")
        from datetime import datetime, timezone
        log_run({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "category": a.category, "pages": a.pages, "dry_run": True,
                 "n_listed": len(rows), "fetched": [], "scale": {},
                 "hits": rows, "skipped": []})
        return 0
    if a.cmd == "sweep":
        sweep(a.category, limit=a.limit, pages=a.pages, cls=a.cls,
              dry_run=a.dry_run)
        return 0
    path, rep = fetch(a.model_url, cls=a.cls)
    print(f"fetched {path} ({os.path.getsize(path)} bytes)")
    if rep["ok"] is None:
        print("  UNIT NOT ASSERTED (no --assert-class). Nothing may consume "
              "this until a class is named.")
        return 0
    print(f"  scale {'ASSERTED' if rep['ok'] else 'REFUSED'}: "
          f"{rep.get('measured_mm')} mm vs band {rep.get('band_mm')}"
          f"{' — ' + str(rep['refusal']) if rep.get('refusal') else ''}")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
