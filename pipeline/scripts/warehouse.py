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


def fetch(entity_id, slug=None, fmt="glb"):
    """Download one model into the warehouse cache. Returns the local path.
    Idempotent: an existing non-empty file is kept."""
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
    with open(os.path.join(base, "SOURCE.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "3dwarehouse.sketchup.com", "entity_id": entity_id,
                   "format": fmt, "bytes": size,
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--count", type=int, default=12)
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
