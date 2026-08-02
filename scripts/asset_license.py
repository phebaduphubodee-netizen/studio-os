"""asset_license.py — every TRACKED asset must declare a licence that permits
redistribution. Pure python, no bpy, no network (LAYER LAW).

WHY THIS EXISTS, and why it exists NOW. On 2026-08-01 the owner cancelled the
"฿0 + CC0/public-domain only" sourcing clause: the studio may now acquire from
any source whose licence permits commercial use of the RENDER. That is the right
call and it changes this repo's risk shape in one specific way —

    until today every asset in `assets/` was CC0, so "may we commit this?" had
    the same answer for all of them. From today the tree holds several licences
    at once, and the answer differs per asset: CC0 yes, our own renders yes,
    CC-BY yes but attribution travels, Trimble GML (3D Warehouse) NO, a paid
    royalty-free mesh usually NO.

The only thing standing between that and a redistribution breach was ONE line of
`.gitignore` (`assets/shared/warehouse/`). **A .gitignore protects a PATH, not a
LICENCE.** Copy one .glb out of that directory into `assets/shared/cc0/models/`
and it commits silently, because the licence of everything under `cc0/` is
asserted by the DIRECTORY NAME and by nothing else — the exact "a convention
asserted in five places and tested in none is five rumours" shape this repo has
paid for before. `docs/strategy.md` §F says the same thing in its own words.

So the check is on the licence, resolved per file, and it FAILS CLOSED: an asset
that declares nothing is a violation, not a pass. That is the whole point — the
dangerous asset is not the one labelled "do not redistribute", it is the one
labelled nothing at all.

WHAT THIS DOES NOT DO. It does not judge whether a licence claim is TRUE; it
checks that one was made and that it permits what the repo is doing with the
file. Verifying the claim is `docs/LICENSING.md`'s job and a human's.

    python scripts/asset_license.py           # audit the real tree, exit 1 on violations
    python scripts/asset_license.py --json
"""
import argparse
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                   # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# redistributable = may this file live in version control and travel with the
# repo? attribution = does a credit have to ride along with every downstream use?
# Fail-closed by construction: anything not in this table resolves to UNKNOWN,
# and UNKNOWN is not redistributable.
LICENCES = {
    "cc0":                     {"redistributable": True,  "attribution": False},
    "public-domain":           {"redistributable": True,  "attribution": False},
    "original":                {"redistributable": True,  "attribution": False},
    "cc-by":                   {"redistributable": True,  "attribution": True},
    # 3D Warehouse. Free to download and to USE commercially in a render; NOT
    # public domain and NOT redistributable AS A MODEL (Trimble GML §2.4/§2.6).
    "trimble-gml":             {"redistributable": False, "attribution": False},
    # the shape a paid library normally takes: the render is yours, the mesh is
    # not. Assume the restrictive reading until the specific EULA says otherwise.
    "royalty-free-commercial": {"redistributable": False, "attribution": False},
    "unknown":                 {"redistributable": False, "attribution": False},
}

# Legacy free-text licence strings already on disk (warehouse.py has written
# 13 of them) mapped to ids. Matched on a lowercased substring, longest first,
# so "general model license" cannot be shadowed by a shorter pattern.
_TEXT_TO_ID = (
    ("general model license", "trimble-gml"),
    ("trimble", "trimble-gml"),
    ("royalty-free", "royalty-free-commercial"),
    ("royalty free", "royalty-free-commercial"),
    ("public domain", "public-domain"),
    ("cc-by", "cc-by"),
    ("cc by", "cc-by"),
    ("cc0", "cc0"),
    ("original", "original"),
)

# A marker declares the licence of its own directory and everything below it.
MARKERS = ("SOURCE.json", "LICENSE.json")
# Not assets: the bookkeeping beside them, and empty-dir placeholders.
NON_ASSET_NAMES = {".gitkeep", "LICENSE.txt", "ATTRIBUTION.md", "README.md"}
NON_ASSET_EXTS = {".md", ".txt", ".yaml", ".yml"}
# .json is ambiguous — a marker or an experiment record, never geometry — so it
# is excluded wholesale rather than by name.
NON_ASSET_EXTS |= {".json"}


def licence_id(raw):
    """Normalise whatever a marker declared into an id in LICENCES.

    Accepts an explicit id (`license_id`) or the human sentence `warehouse.py`
    already writes. Anything unrecognised → 'unknown', which is a VIOLATION and
    not a shrug: the point of failing closed is that silence is the dangerous
    case."""
    if not raw:
        return "unknown"
    s = str(raw).strip().lower()
    if s in LICENCES:
        return s
    for pat, lid in _TEXT_TO_ID:
        if pat in s:
            return lid
    return "unknown"


def _marker_licence(data):
    """The licence a parsed marker declares, or None if it declares none."""
    if not isinstance(data, dict):
        return None
    for key in ("license_id", "licence_id", "license", "licence"):
        if data.get(key):
            return licence_id(data[key])
    return None


def is_asset(rel):
    """Assets are the files a licence can attach to. Bookkeeping is not."""
    name = os.path.basename(rel)
    if name in MARKERS or name in NON_ASSET_NAMES:
        return False
    return os.path.splitext(name)[1].lower() not in NON_ASSET_EXTS


def resolve(rel, read_json, root_rel="assets"):
    """(licence_id, declaring_dir) for one repo-relative path.

    Walks UP from the file's own directory to `root_rel`, nearest marker wins —
    so a per-model SOURCE.json overrides a tree-wide LICENSE.json, which is the
    order that lets one non-redistributable model sit inside an otherwise
    permissive tree and still be seen.

    `read_json` is injected rather than called: this function must stay runnable
    with no filesystem so the tests can exercise trees that do not exist."""
    d = os.path.dirname(rel.replace("\\", "/"))
    stop = root_rel.replace("\\", "/")
    while True:
        for m in MARKERS:
            lic = _marker_licence(read_json(f"{d}/{m}" if d else m))
            if lic:
                return lic, d
        if d == stop or not d or "/" not in d:
            break
        d = d.rsplit("/", 1)[0]
    # one last look at the root itself (the loop above exits before testing it
    # when the file sits directly under it)
    for m in MARKERS:
        lic = _marker_licence(read_json(f"{stop}/{m}"))
        if lic:
            return lic, stop
    return "unknown", None


def audit(tracked, read_json, exists=None, root_rel="assets"):
    """Violations for a list of repo-relative TRACKED paths. Pure.

    `tracked` is injected because "is this file in version control" is a git
    question and this module answers a licence question — the split keeps the
    logic testable without a repo."""
    out = []
    for rel in sorted(tracked):
        rel = rel.replace("\\", "/")
        if not rel.startswith(root_rel + "/") or not is_asset(rel):
            continue
        lic, where = resolve(rel, read_json, root_rel)
        meta = LICENCES.get(lic, LICENCES["unknown"])
        if lic == "unknown":
            out.append({
                "class": "TRACKED-UNDECLARED", "path": rel, "license": lic,
                "why": "in version control with no licence declared anywhere "
                       "above it — add a LICENSE.json to its tree or a "
                       "SOURCE.json beside it"})
        elif not meta["redistributable"]:
            out.append({
                "class": "TRACKED-NONREDISTRIBUTABLE", "path": rel, "license": lic,
                "why": f"'{lic}' does not permit redistribution, and committing "
                       f"a file redistributes it. It belongs in a gitignored "
                       f"cache (see assets/shared/warehouse/)"})
        elif meta["attribution"] and exists is not None and where is not None \
                and not exists(f"{where}/ATTRIBUTION.md"):
            out.append({
                "class": "MISSING-ATTRIBUTION", "path": rel, "license": lic,
                "why": f"'{lic}' obliges credit that travels downstream; "
                       f"{where}/ATTRIBUTION.md does not exist"})
    return out


# ------------------------------------------------------------------ real tree ---

def _reader(repo):
    cache = {}

    def read_json(rel):
        if rel not in cache:
            p = os.path.join(repo, rel.replace("/", os.sep))
            try:
                with open(p, encoding="utf-8") as f:
                    cache[rel] = json.load(f)
            except Exception:                       # noqa: BLE001
                cache[rel] = None
        return cache[rel]
    return read_json


def tracked_assets(repo, root_rel="assets"):
    """Repo-relative paths git is tracking under `root_rel`. [] if not a repo."""
    try:
        out = subprocess.run(["git", "ls-files", root_rel], cwd=repo,
                             capture_output=True, text=True, timeout=60)
    except Exception:                               # noqa: BLE001
        return []
    if out.returncode != 0:
        return []
    return [l.strip() for l in out.stdout.splitlines() if l.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    tracked = tracked_assets(a.repo)
    read_json = _reader(a.repo)
    def exists(rel):
        return os.path.exists(os.path.join(a.repo, rel.replace("/", os.sep)))
    v = audit(tracked, read_json, exists)

    if a.json:
        print(json.dumps({"tracked": len(tracked), "violations": v}, indent=1))
        return 1 if v else 0

    assets = [t for t in tracked if is_asset(t)]
    print(f"asset-licence audit: {len(assets)} tracked assets under assets/")
    if not v:
        by = {}
        for t in assets:
            lic, _ = resolve(t, read_json)
            by[lic] = by.get(lic, 0) + 1
        for lic, n in sorted(by.items(), key=lambda kv: -kv[1]):
            print(f"  {n:5d}  {lic}")
        print("  -> OK: every tracked asset declares a redistributable licence")
        return 0
    for x in v:
        print(f"  !! {x['class']:28s} {x['path']}\n     {x['why']}")
    print(f"  -> {len(v)} VIOLATION(S). A licence that forbids redistribution "
          f"must live in a gitignored cache, never in a commit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
