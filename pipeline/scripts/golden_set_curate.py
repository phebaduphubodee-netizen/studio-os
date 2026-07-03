#!/usr/bin/env python3
"""golden_set_curate.py — assemble the M3.2 judge-calibration golden set.

Scans pipeline/output/*.critique*.json (the pipeline's full scored history, 1/5
sterile clays through 5/5 pro-tier SHIPs), copies every still-existing scored
render into assets/qa/golden-set/ (LFS: assets/**/*.png) under a stable blind ID,
and writes:

    qa/golden-set/manifest.json        image inventory (NO scores — safe to open)
    qa/golden-set/machine-scores.json  the judge's historical rolls per image
                                       (owner: do NOT open before labeling)
    qa/golden-set/labels.template.json owner fills overall_0_5 + verdict per ID

Blind-labeling discipline: NEW stems are numbered in crc32-of-stem order, so the
first sheet correlates with neither room, prompt version, nor score. The manifest
deliberately omits machine scores; they live in machine-scores.json only.

Re-runnable — STABLE IDs: the stem→ID assignment is PERSISTED in
qa/golden-set/id-map.json. A stem keeps its GS-ID forever; only genuinely new
stems get new (higher) numbers, appended in crc32 order. This is load-bearing:
labels.json is keyed by GS-ID, so a position-based ID (the pre-2026-07-03 bug)
would silently remap the owner's ground truth every time a render was added.
A stem that vanishes from pipeline/output keeps its map entry (never recycled).

Usage:  python pipeline/scripts/golden_set_curate.py [--dry-run]
"""
import glob
import json
import os
import shutil
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(ROOT, "pipeline", "output")
IMG_DIR = os.path.join(ROOT, "assets", "qa", "golden-set")
GS_DIR = os.path.join(ROOT, "qa", "golden-set")
ID_MAP = os.path.join(GS_DIR, "id-map.json")


def assign_ids(stems):
    """Stable stem→'GS-NN' via a persisted map. Existing stems keep their ID;
    new stems (crc32-ordered for a blind first sheet) take the next free numbers.
    Never renumbers or recycles — labels.json is keyed by these IDs."""
    mapping = {}
    if os.path.exists(ID_MAP):
        mapping = json.load(open(ID_MAP, encoding="utf-8")).get("map", {})
    used = {int(g.split("-")[1]) for g in mapping.values()}
    nxt = (max(used) + 1) if used else 1
    for s in sorted(stems, key=lambda s: zlib.crc32(s.encode())):
        if s not in mapping:
            while nxt in used:                       # defensive: skip taken numbers
                nxt += 1
            mapping[s] = f"GS-{nxt:02d}"
            used.add(nxt)
            nxt += 1
    return mapping


def collect():
    """{stem: {"image": path, "rolls": [critique dicts]}} for existing renders."""
    by_img = {}
    for p in sorted(glob.glob(os.path.join(OUT_DIR, "*.critique*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  !! unreadable critique {os.path.basename(p)}: {e}", file=sys.stderr)
            continue
        if d.get("_kind") != "render" or d.get("verdict") == "ERROR":
            continue
        art = os.path.basename(d.get("_artifact", ""))
        img = os.path.join(OUT_DIR, art)
        if not art or not os.path.exists(img):
            continue
        stem = os.path.splitext(art)[0]
        e = by_img.setdefault(stem, {"image": img, "rolls": []})
        e["rolls"].append({
            "overall_0_5": d.get("overall_0_5"),
            "verdict": d.get("verdict"),
            "model": d.get("_model"),
            "scores": d.get("scores", {}),
            "source": os.path.relpath(p, ROOT).replace(os.sep, "/"),
        })
    return by_img


def main():
    dry = "--dry-run" in sys.argv
    by_img = collect()
    prior = set()
    if os.path.exists(ID_MAP):
        prior = set(json.load(open(ID_MAP, encoding="utf-8")).get("map", {}))
    ids = assign_ids(by_img.keys())                  # PERSISTED, stable per stem
    if len(set(ids[s] for s in by_img)) != len(by_img):
        sys.exit("ID collision — id-map.json is corrupt")
    # present in crc32 order (stable, blind) for readable output/sheets
    stems = sorted(by_img, key=lambda s: zlib.crc32(s.encode()))

    manifest, machine, template = [], {}, {}
    for s in stems:
        gid = ids[s]
        dest = os.path.join(IMG_DIR, f"{gid}.png")
        manifest.append({
            "id": gid,
            "image": os.path.relpath(dest, ROOT).replace(os.sep, "/"),
            "source_stem": s,
            "n_machine_rolls": len(by_img[s]["rolls"]),
        })
        machine[gid] = {"source_stem": s, "rolls": by_img[s]["rolls"]}
        template[gid] = {"overall_0_5": None, "verdict": None,
                         "note": ""}
        if not dry:
            os.makedirs(IMG_DIR, exist_ok=True)
            shutil.copy2(by_img[s]["image"], dest)

    if dry:
        for m in manifest:
            tag = "NEW " if m["source_stem"] not in prior else "     "
            print(tag + m["id"], "<-", m["source_stem"], f"({m['n_machine_rolls']} roll)")
        print(f"  ({len(manifest)} present; {len([m for m in manifest if m['source_stem'] not in prior])} new)")
        return

    os.makedirs(GS_DIR, exist_ok=True)
    def w(name, obj):
        with open(os.path.join(GS_DIR, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
        print(f"  wrote qa/golden-set/{name}")
    # persist the stem→ID map FIRST — it is the stability contract; keep entries
    # for stems no longer present so their numbers are never recycled.
    w("id-map.json", {"_note": "stable stem->GS-ID; never renumber/recycle (see script header)",
                      "map": ids})
    w("manifest.json", {"purpose": "M3.2 judge-calibration golden set (blueprint 9.4)",
                        "images": manifest})
    w("machine-scores.json", {"_warning": "judge history — owner must NOT read before labeling",
                              "images": machine})
    tpl = os.path.join(GS_DIR, "labels.template.json")
    if os.path.exists(os.path.join(GS_DIR, "labels.json")):
        print("  labels.json exists — template NOT refreshed over real labels")
    else:
        w("labels.template.json", {
            "_instructions": "copy to labels.json, fill every image; see LABELING.md",
            "labels": template})
    print(f"  {len(manifest)} images -> assets/qa/golden-set/ (LFS)")


if __name__ == "__main__":
    main()
