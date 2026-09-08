"""warehouse.py — search and fetch models from SketchUp 3D Warehouse.

CLI-ONLY: run by hand during an R8 ACQUIRE decision —
`python pipeline/scripts/warehouse.py search "<generic query>"` then
`... fetch <entity_id> --slug <slug> --assert-class <cls>`. It is deliberately
NOT on an automatic path: every fetch is a licence decision and a spend
decision, and R8 makes both the owner's. Queries are generic by the same
privacy rule that governs the NLM lane — no client names, no room dimensions.

WHY THIS EXISTS, and why it is a separate module from assets.py. The owner asked
a working designer where furniture models come from and the answer was 3D
Warehouse — a source our 2026-07-01 asset-sourcing DR does not mention at all,
while our own DISTILLATION-LEDGER already recorded that the same DR fabricates
prices and licences. Our own files pointed here from three directions (the
SketchUp interop law in pipeline/CLAUDE.md, build_room.rb, and a SketchUp/3ds Max
Discord corpus) and none of it was followed.

LICENCE — THE REASON THIS DOES NOT SHARE assets.py's CACHE. Poly Haven is CC0:
public domain, redistributable, safe to commit. 3D Warehouse is NOT. Its models
carry Trimble's General Model License: free to download and to USE in your own
work including commercially, but NOT public domain and NOT redistributable as
models. So they land in their own cache directory with a LICENSE note beside
them, and that directory is kept out of git — a model that may not be
redistributed must not be pushed anywhere, and the safest way to honour that is
for it never to enter version control at all.

SCALE — a MUST, not a nicety (pipeline/CLAUDE.md): "SketchUp exports IMPERIAL
even when the model was authored in metres (~0.0254x error) — a plausible-but-
wrong-scale model = the exact failure we sell against." Nothing here asserts
scale, because scale can only be checked after import; `triage()` reports the
bounds it measured and the CALLER must assert against a per-class band before a
spec consumes it.

    python pipeline/scripts/warehouse.py search "buddha statue"
    python pipeline/scripts/warehouse.py fetch <entity-id> [--slug name]
"""
import argparse
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                   # noqa: BLE001
    pass

API = "https://3dwarehouse.sketchup.com/warehouse/v1.0"
# same reasoning as assets.py: this machine sits behind a TLS-intercepting
# VPN, so certificates do not verify against the default store
_CTX = ssl._create_unverified_context()
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(REPO, "assets", "shared", "warehouse")
# THE PROVENANCE OF A SEARCH, which this module recorded nowhere until p2r46.
# `SOURCE.json` records what we DOWNLOADED — entity id, bytes, licence. It has
# never recorded what we ASKED, and the difference decided a round: on 2026-08-17
# this lane reported to the owner that "the free tier is exhausted (68 models, one
# repository)". 68 was the whole cache — chairs, towels, garments — of which
# exactly TEN ever staged as bed cloth, and the number of bed-cloth QUERIES behind
# them was unrecoverable from disk. A claim of exhaustion that cannot be checked
# against the queries actually asked is not a finding, it is a mood. R13's law
# ("'unbought' is not 'unavailable'") one level in: not-found-in-ten is not
# does-not-exist.
# ...AND IT LIVES IN `qa/`, NOT IN THE CACHE. The cache is gitignored on purpose
# (a Trimble-licensed mesh may not be redistributed, so it never enters git), but
# the LOG is our own record and carries no licensed bytes. Written beside the
# models it would die with them on any cache clear — and a record of what we
# searched that cannot outlive the shelf answers the exhaustion question exactly
# once.
SEARCH_LOG = os.path.join(REPO, "qa", "warehouse-search-log.json")

LICENSE_NOTE = """SketchUp 3D Warehouse models — Trimble General Model License.

Free to download and to USE in renders and client work, including commercially.
NOT public domain. NOT redistributable AS MODELS.

This directory is therefore gitignored on purpose: a model that may not be
redistributed must not enter version control. Fetch is reproducible instead —
every model here can be re-downloaded from its entity id, which the spec that
consumes it records.
"""


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "studio-os/1.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=60) as r:
        return json.load(r)


def search(q, count=12):
    """[(id, title, downloads, formats)] — newest API shape as probed 2026-08-01."""
    url = f"{API}/entities?" + urllib.parse.urlencode(
        {"q": q, "contentType": "3dw", "count": count})
    out = []
    for e in (_get(url).get("entries") or []):
        names = e.get("binaryNames") or []
        fmts = sorted({f for f in ("glb", "skp", "dae", "kmz", "usdz", "obj")
                       if f in names})
        out.append((e["id"], e.get("title", "?"), int(e.get("downloads") or 0), fmts))
    return out


def binary_url(entity_id, fmt="glb"):
    """Direct content URL for one binary, or None if that format is absent."""
    b = (_get(f"{API}/entities/{entity_id}") or {}).get("binaries") or {}
    if fmt not in b:
        return None, None
    rec = b[fmt]
    return rec.get("contentUrl"), int(rec.get("fileSize") or 0)


def cached_ids(cache=CACHE):
    """Every entity id already on the shelf, from the SOURCE.json files themselves.

    Read from disk rather than from the log, because the shelf is the fact and the
    log is a record of one lane's asks — 68 models predate the log entirely."""
    out = {}
    for name in sorted(os.listdir(cache)) if os.path.isdir(cache) else []:
        src = os.path.join(cache, name, "SOURCE.json")
        if not os.path.isfile(src):
            continue
        try:
            with open(src, encoding="utf-8") as fh:
                eid = (json.load(fh) or {}).get("entity_id")
        except (OSError, ValueError):
            continue
        if eid:
            out[eid] = name
    return out


def plan_sweep(hits, have, limit=None, min_bytes=0, max_bytes=0):
    """PURE. Decide which search hits to fetch and say why each other one is out.

    `hits`  [{id, title, downloads, fmts, bytes, query}] — bytes may be None when
            the size probe has not run yet.
    `have`  {entity_id: slug} already on the shelf.
    Returns (fetch_rows, skipped_rows) with `skipped` carrying a REASON per id, so
    a sweep that fetches nothing still says what it looked at and why it passed.

    RANKED BY BYTES, AND THERE IS NO SIZE CUT UNLESS THE CALLER ASKS FOR ONE.
    File size is the only density signal available before a download, and density
    is what the bed-cloth lane is short of: the acquired PILLOWS that pass the
    fineness rule are 10.8 MB and 18.8 MB, while every bed cover this lane has
    auditioned is 1-3 MB and measures 15-124 mm median edge against a 10.3 mm cut.
    But a byte floor is a number nobody measured, and this repo's own word for that
    is "taste wearing a threshold" (`bedcloth_rules.survives`). So bytes ORDER the
    queue and never decide membership — the same split the bench already uses,
    where three cuts decide who is in and mesh edge decides who is looked at first.
    """
    seen, keep, skip = {}, [], []
    for h in hits:
        eid = h.get("id")
        if not eid:
            continue
        if eid in have:
            skip.append({**h, "why": f"already cached as {have[eid]}"})
            continue
        if eid in seen:                       # the same model answering two queries
            seen[eid].setdefault("also_found_by", []).append(h.get("query"))
            continue
        if "glb" not in (h.get("fmts") or []):
            skip.append({**h, "why": "no glb binary"})
            continue
        if min_bytes and (h.get("bytes") or 0) < min_bytes:
            skip.append({**h, "why": f"{h.get('bytes') or 0} bytes < floor {min_bytes}"})
            continue
        # A CEILING IS AN OPERATIONAL LIMIT, NOT A QUALITY JUDGEMENT, and it is
        # recorded as a skip with its reason for exactly that: the top of one
        # sweep's rank was a 384 MB entity, which is a whole scene rather than a
        # bed cover and would have eaten the fetch budget and the bench's memory
        # alone. "No silent caps" — a bound that shrinks coverage has to print.
        if max_bytes and (h.get("bytes") or 0) > max_bytes:
            skip.append({**h, "why": f"{h.get('bytes') or 0} bytes > ceiling "
                                     f"{max_bytes} (deferred, not judged)"})
            continue
        seen[eid] = dict(h)
        keep.append(seen[eid])
    keep.sort(key=lambda r: -(r.get("bytes") or 0))
    if limit is not None and len(keep) > limit:
        for r in keep[limit:]:
            skip.append({**r, "why": f"past --limit {limit} in the size rank"})
        keep = keep[:limit]
    return keep, skip


def log_sweep(record, path=SEARCH_LOG):
    """Append one sweep to the search log. Never rewrites a prior run."""
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
        json.dump({"_what": "Every 3D Warehouse query this repo has asked, with "
                            "what came back and what was fetched. Written so "
                            "'we searched and there is nothing' is a checkable "
                            "sentence instead of a memory.",
                   "runs": runs}, fh, indent=1, ensure_ascii=False)
    return path


def fetch(entity_id, slug=None, fmt="glb", found_by=None):
    """Download one model into the warehouse cache. Returns the local path.
    Idempotent: an existing non-empty file is kept.

    `found_by` {query, title, downloads} is written into SOURCE.json — the ask that
    produced this model, which the sidecar never carried (see SEARCH_LOG)."""
    url, size = binary_url(entity_id, fmt)
    if not url:
        raise SystemExit(f"warehouse: entity {entity_id} has no {fmt} binary")
    base = os.path.join(CACHE, slug or entity_id)
    os.makedirs(base, exist_ok=True)
    note = os.path.join(CACHE, "LICENSE.txt")
    if not os.path.exists(note):
        with open(note, "w", encoding="utf-8") as f:
            f.write(LICENSE_NOTE)
    # the entity id is the provenance: it is what makes the fetch reproducible
    src_path = os.path.join(base, "SOURCE.json")
    if found_by is None and os.path.exists(src_path):
        # never let a re-fetch ERASE an ask that an earlier sweep recorded
        try:
            with open(src_path, encoding="utf-8") as f:
                found_by = (json.load(f) or {}).get("found_by")
        except (OSError, ValueError):
            found_by = None
    with open(src_path, "w", encoding="utf-8") as f:
        json.dump({"source": "3dwarehouse.sketchup.com", "entity_id": entity_id,
                   "format": fmt, "bytes": size, "found_by": found_by,
                   # machine-readable FIRST: scripts/asset_license.py reads this
                   # id, and matching an English sentence is a fallback for the
                   # models fetched before the id existed, not the contract
                   "license_id": "trimble-gml",
                   "license": "Trimble General Model License — use yes, "
                              "redistribute as a model no"}, f, indent=1)
    dest = os.path.join(base, f"{slug or entity_id}.{fmt}")
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "studio-os/1.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=600) as r, \
            open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return dest


def sweep(queries, count=12, limit=None, min_bytes=0, max_bytes=0,
          dry_run=False, probe=True):
    """Run many queries, size-probe what is new, fetch the densest, LOG ALL OF IT.

    The size probe is one extra API call per unseen entity and it is what makes the
    rank possible before any download — `binary_url` returns the binary's fileSize
    from the entity record. Cached ids are never probed.
    """
    from datetime import datetime, timezone
    have = cached_ids()
    hits = []
    for q in queries:
        try:
            found = search(q, count)
        except Exception as e:                                # noqa: BLE001
            print(f"SWEEP {q!r}: SEARCH FAILED ({str(e)[:70]})")
            hits.append({"id": None, "query": q, "error": str(e)[:200]})
            continue
        print(f"SWEEP {q!r}: {len(found)} result(s)")
        for eid, title, dl, fmts in found:
            hits.append({"id": eid, "title": title, "downloads": dl,
                         "fmts": fmts, "bytes": None, "query": q})
    if probe:
        for h in hits:
            if not h.get("id") or h["id"] in have or "glb" not in (h.get("fmts") or []):
                continue
            try:
                _, h["bytes"] = binary_url(h["id"], "glb")
            except Exception as e:                            # noqa: BLE001
                h["probe_error"] = str(e)[:120]
    keep, skip = plan_sweep(hits, have, limit=limit, min_bytes=min_bytes,
                            max_bytes=max_bytes)
    print(f"\nSWEEP {len(hits)} hit(s) over {len(queries)} query(ies): "
          f"{len(keep)} to fetch, {len(skip)} passed over "
          f"({sum(1 for s in skip if 'already cached' in s.get('why', ''))} already on the shelf)")
    for r in keep:
        print(f"  {r['id']}  {(r.get('bytes') or 0)/1e6:7.2f} MB  "
              f"{r.get('downloads', 0):>7} dl  {(r.get('title') or '')[:46]}   <- {r['query']!r}")
    fetched = []
    if not dry_run:
        for r in keep:
            try:
                p = fetch(r["id"], None, "glb",
                          found_by={"query": r["query"], "title": r.get("title"),
                                    "downloads": r.get("downloads")})
                fetched.append(r["id"])
                print(f"  fetched {os.path.basename(p)} "
                      f"({os.path.getsize(p)/1e6:.2f} MB)")
            except Exception as e:                            # noqa: BLE001
                r["fetch_error"] = str(e)[:160]
                print(f"  FETCH FAILED {r['id']}: {str(e)[:80]}")
    log_sweep({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "queries": list(queries), "count": count, "limit": limit,
               "min_bytes": min_bytes, "max_bytes": max_bytes,
               "dry_run": bool(dry_run),
               "n_hits": len(hits), "fetched": fetched,
               "hits": hits, "skipped": skip})
    print(f"SWEEP logged -> {SEARCH_LOG}")
    return fetched


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--count", type=int, default=12)
    w = sub.add_parser("sweep", help="many queries -> size-ranked fetch, all logged")
    w.add_argument("queries", nargs="+")
    w.add_argument("--count", type=int, default=12)
    w.add_argument("--limit", type=int, default=None,
                   help="fetch at most N, densest first")
    w.add_argument("--min-bytes", type=int, default=0, dest="min_bytes")
    w.add_argument("--max-bytes", type=int, default=0, dest="max_bytes",
                   help="defer anything larger (logged with its reason, never silent)")
    w.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("fetch")
    f.add_argument("entity_id")
    f.add_argument("--slug", default=None)
    f.add_argument("--format", default="glb")
    # THE ASSERTION RUNS HERE, IN THE PATH THAT ALREADY RUNS. This line used to
    # print "the caller must check" and there was never a caller — the standing
    # rule in pipeline/CLAUDE.md ("no external geometry reaches a spec until its
    # unit is asserted, never assumed") had no program behind it, which is the
    # only kind of rule this repo has ever failed to keep. A sidecar is written
    # on EVERY fetch whether or not a class is named, so "unasserted" is a fact
    # on disk rather than the absence of one.
    f.add_argument("--assert-class", default=None, dest="cls",
                   help="scale class from asset_scale.BANDS; refusal exits 1")
    a = ap.parse_args(argv)

    if a.cmd == "search":
        for eid, title, dl, fmts in search(a.query, a.count):
            print(f"{eid}  {dl:>7} dl  [{','.join(fmts) or '-'}]  {title[:52]}")
        return 0
    if a.cmd == "sweep":
        sweep(a.queries, count=a.count, limit=a.limit,
              min_bytes=a.min_bytes, max_bytes=a.max_bytes, dry_run=a.dry_run)
        return 0
    path = fetch(a.entity_id, a.slug, a.format)
    print(f"fetched {path} ({os.path.getsize(path)} bytes)")
    return _assert_scale_sidecar(path, a.cls)


def _assert_scale_sidecar(path, cls):
    """Read the bounds, write `<asset>.scale.json`, and refuse a bad unit.

    Kept out of `fetch()` so a cached re-fetch still runs it, and so the import
    stays at the CLI edge: `asset_scale` is pure but this module is the network
    one, and the layer law wants the pure thing importable without it.
    """
    import asset_scale as S
    # THE BODY MOVED TO asset_scale.write_sidecar (2026-08-16, P2r-9). It lived
    # here, and `assets.py` — the COMMITTED Poly Haven shelf — had no equivalent
    # line, so 13 of the repo's models were never asserted at all while this one
    # function made the rule look enforced. One implementation, two fetchers.
    ok, rep = S.write_sidecar(path, cls)
    print(f"  scale sidecar -> {os.path.basename(S.sidecar_path(path))}")
    if ok is None:
        print("  UNIT NOT ASSERTED (no --assert-class). Bounds mm: "
              + ", ".join(f"{k}={v}" for k, v in rep["bbox_mm"].items()))
        return 0
    if ok:
        print(f"  SCALE ASSERTED as {cls}: {rep['measured_mm']} mm on "
              f"{rep['axis']}, band {rep['band_mm']}")
        return 0
    print(f"  SCALE REFUSED: {rep.get('planar_refusal') or rep.get('error') or ''}"
          f" measured {rep.get('measured_mm')} mm against band {rep.get('band_mm')}"
          f"{' — would be in band under ' + str(rep['in_band_under']) if rep.get('in_band_under') else ''}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
