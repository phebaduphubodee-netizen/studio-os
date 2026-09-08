"""Tests for scripts/asset_license.py.

The load-bearing one is `test_a_real_warehouse_model_would_be_caught_if_tracked`:
a guard that has never blocked anything is a rumour, and this repo has written
that lesson down more than once. It feeds the audit a path to a model that is
ACTUALLY ON DISK, with the licence string `warehouse.py` ACTUALLY wrote, and
asserts the audit convicts it — so the check is proven against the real failure
rather than against a fixture built to pass.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_license as A                            # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def reader(tree):
    """read_json over a dict of {path: obj} — no filesystem, so a test can
    describe a tree that does not exist."""
    return lambda rel: tree.get(rel)


# ------------------------------------------------------------- licence ids ---

@pytest.mark.parametrize("raw,want", [
    ("cc0", "cc0"),
    ("CC0", "cc0"),
    ("  Public Domain  ", "public-domain"),
    ("CC-BY 4.0", "cc-by"),
    ("original", "original"),
    # the exact sentence warehouse.py writes into every SOURCE.json
    ("Trimble General Model License — use yes, redistribute as a model no",
     "trimble-gml"),
    ("Royalty-Free Commercial Use", "royalty-free-commercial"),
    ("", "unknown"),
    (None, "unknown"),
    ("some licence nobody has heard of", "unknown"),
])
def test_licence_id_normalisation(raw, want):
    assert A.licence_id(raw) == want


def test_unknown_is_not_redistributable():
    """Fail-closed is the whole design. If this ever flips, an undeclared asset
    becomes a silent pass and the audit stops being a guard."""
    assert A.LICENCES["unknown"]["redistributable"] is False
    assert A.LICENCES["trimble-gml"]["redistributable"] is False
    assert A.LICENCES["cc0"]["redistributable"] is True


def test_cc_by_is_redistributable_but_carries_attribution():
    """CC-BY is not the same risk as GML and must not be lumped with it: the
    mesh MAY travel, the credit must travel with it."""
    assert A.LICENCES["cc-by"] == {"redistributable": True, "attribution": True}


# ---------------------------------------------------------------- resolve ---

def test_tree_marker_covers_everything_below_it():
    tree = {"assets/shared/cc0/LICENSE.json": {"license_id": "cc0"}}
    lic, where = A.resolve("assets/shared/cc0/models/vase/vase.gltf", reader(tree))
    assert (lic, where) == ("cc0", "assets/shared/cc0")


def test_nearest_marker_wins_so_one_bad_asset_inside_a_good_tree_is_seen():
    """The failure a path-based .gitignore cannot see: a non-redistributable
    model copied INTO the permissive tree."""
    tree = {
        "assets/shared/cc0/LICENSE.json": {"license_id": "cc0"},
        "assets/shared/cc0/models/smuggled/SOURCE.json": {
            "license": "Trimble General Model License — use yes, redistribute "
                       "as a model no"},
    }
    lic, _ = A.resolve("assets/shared/cc0/models/smuggled/x.glb", reader(tree))
    assert lic == "trimble-gml"


def test_no_marker_anywhere_resolves_unknown():
    assert A.resolve("assets/loose/x.glb", reader({}))[0] == "unknown"


def test_a_marker_that_declares_no_licence_does_not_count_as_a_declaration():
    """A SOURCE.json recording bytes and an entity id but no licence is exactly
    the silence this audit exists to catch."""
    tree = {"assets/x/SOURCE.json": {"source": "somewhere", "bytes": 12}}
    assert A.resolve("assets/x/m.glb", reader(tree))[0] == "unknown"


def test_marker_directly_beside_the_root(tmp_path):
    tree = {"assets/LICENSE.json": {"license_id": "original"}}
    assert A.resolve("assets/render.png", reader(tree))[0] == "original"


# ------------------------------------------------------------------ audit ---

def test_nonredistributable_tracked_asset_is_a_violation():
    tree = {"assets/shared/w/SOURCE.json": {"license_id": "trimble-gml"}}
    v = A.audit(["assets/shared/w/a.glb"], reader(tree))
    assert [x["class"] for x in v] == ["TRACKED-NONREDISTRIBUTABLE"]


def test_undeclared_tracked_asset_is_a_violation():
    v = A.audit(["assets/mystery/a.glb"], reader({}))
    assert [x["class"] for x in v] == ["TRACKED-UNDECLARED"]


def test_clean_tree_has_no_violations():
    tree = {"assets/shared/cc0/LICENSE.json": {"license_id": "cc0"}}
    assert A.audit(["assets/shared/cc0/a.gltf"], reader(tree)) == []


def test_cc_by_without_an_attribution_file_is_flagged():
    tree = {"assets/x/LICENSE.json": {"license_id": "cc-by"}}
    v = A.audit(["assets/x/a.glb"], reader(tree), exists=lambda p: False)
    assert [x["class"] for x in v] == ["MISSING-ATTRIBUTION"]
    assert A.audit(["assets/x/a.glb"], reader(tree), exists=lambda p: True) == []


def test_bookkeeping_is_not_an_asset_and_needs_no_licence():
    for p in ("assets/x/LICENSE.json", "assets/x/SOURCE.json", "assets/x/.gitkeep",
              "assets/x/README.md", "assets/x/notes.txt", "assets/x/run.json"):
        assert not A.is_asset(p), p
    for p in ("assets/x/a.glb", "assets/x/a.gltf", "assets/x/a.png",
              "assets/x/a.hdr", "assets/x/a.bin", "assets/x/a.blend"):
        assert A.is_asset(p), p
    # and the audit agrees, so bookkeeping never generates noise
    assert A.audit(["assets/x/README.md", "assets/x/.gitkeep"], reader({})) == []


def test_paths_outside_the_asset_root_are_not_this_guards_business():
    assert A.audit(["pipeline/scripts/build_room.py", "docs/a.png"], reader({})) == []


def test_windows_separators_do_not_defeat_the_walk():
    """guard_paths had a Windows canonicalisation bypass once; do not repeat it."""
    tree = {"assets/shared/cc0/LICENSE.json": {"license_id": "cc0"}}
    assert A.audit([r"assets\shared\cc0\a.gltf"], reader(tree)) == []


# -------------------------------------------------------------- real tree ---

def _tracked():
    out = subprocess.run(["git", "ls-files", "assets"], cwd=REPO,
                         capture_output=True, text=True)
    if out.returncode != 0:
        pytest.skip("not a git repo")
    return [l.strip() for l in out.stdout.splitlines() if l.strip()]


def test_the_real_tree_is_clean():
    v = A.audit(_tracked(), A._reader(REPO),
                exists=lambda p: os.path.exists(os.path.join(REPO, p)))
    assert v == [], f"tracked assets with a redistribution problem: {v}"


def test_every_tracked_asset_actually_resolves_to_a_named_licence():
    """Not the same assertion as above: the audit passing could also mean it
    found nothing to look at. This one proves the tree is non-empty and that
    every file in it was really classified."""
    read = A._reader(REPO)
    assets = [t for t in _tracked() if A.is_asset(t)]
    assert len(assets) > 50, "the asset tree went missing — audit proves nothing"
    for t in assets:
        lic, _ = A.resolve(t.replace("\\", "/"), read)
        assert lic in A.LICENCES and lic != "unknown", t


def test_a_real_warehouse_model_would_be_caught_if_tracked():
    """THE POINT OF THE GUARD. 3D Warehouse models are on this disk right now
    (fetched under R8's acquire rule) and are kept out of git by one .gitignore
    line. Prove that if that line failed — or if someone copied one of these
    files somewhere tracked — the audit convicts it, using the licence string
    warehouse.py really wrote."""
    cache = os.path.join(REPO, "assets", "shared", "warehouse")
    if not os.path.isdir(cache):
        pytest.skip("no warehouse cache on this machine")
    models = [d for d in sorted(os.listdir(cache))
              if os.path.isfile(os.path.join(cache, d, "SOURCE.json"))]
    if not models:
        pytest.skip("warehouse cache holds no fetched model")
    rel = f"assets/shared/warehouse/{models[0]}/{models[0]}.glb"
    v = A.audit([rel], A._reader(REPO))
    assert [x["class"] for x in v] == ["TRACKED-NONREDISTRIBUTABLE"], v
    assert v[0]["license"] == "trimble-gml"


def test_the_warehouse_cache_is_still_gitignored():
    """The audit is the second line of defence; this is the first, and it is one
    line in .gitignore that nothing else was pinning."""
    out = subprocess.run(
        ["git", "check-ignore", "-q", "assets/shared/warehouse/probe.glb"],
        cwd=REPO, capture_output=True, text=True)
    assert out.returncode == 0, (
        "assets/shared/warehouse/ is NO LONGER gitignored — a "
        "non-redistributable mesh can now be committed")


def test_every_fetched_warehouse_model_declares_its_licence():
    """warehouse.py writes SOURCE.json on fetch. If a model ever arrives without
    one — hand-copied, or written by a future fetcher that forgot — it resolves
    to 'unknown', which is still a violation, but the message would misdiagnose
    a known-restrictive asset as merely undeclared."""
    cache = os.path.join(REPO, "assets", "shared", "warehouse")
    if not os.path.isdir(cache):
        pytest.skip("no warehouse cache on this machine")
    read = A._reader(REPO)
    for d in sorted(os.listdir(cache)):
        if not os.path.isdir(os.path.join(cache, d)):
            continue
        lic, _ = A.resolve(f"assets/shared/warehouse/{d}/x.glb", read)
        assert lic == "trimble-gml", f"{d} declares '{lic}'"


def test_cli_exits_zero_on_the_real_tree():
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts",
                                                       "asset_license.py")],
                         cwd=REPO, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "OK: every tracked asset declares" in out.stdout


def test_cli_json_mode_is_machine_readable():
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts",
                                                       "asset_license.py"),
                          "--json"], cwd=REPO, capture_output=True, text=True)
    d = json.loads(out.stdout)
    assert d["violations"] == [] and d["tracked"] > 50
