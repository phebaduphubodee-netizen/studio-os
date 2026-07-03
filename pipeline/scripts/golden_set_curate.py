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

Blind-labeling discipline: IDs are ordered by crc32 of the source stem, so the
sheet order correlates with neither room, prompt version, nor score. The manifest
deliberately omits machine scores; they live in machine-scores.json only.

Re-runnable: new scored images append (existing IDs never change — crc32 order is
stable because it is keyed to the source stem, and collisions abort loudly).

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
    # blind, stable ordering: crc32 of the stem
    stems = sorted(by_img, key=lambda s: zlib.crc32(s.encode()))
    ids = {s: f"GS-{i+1:02d}" for i, s in enumerate(stems)}
    if len(set(ids.values())) != len(stems):
        sys.exit("ID collision — widen the ID scheme")

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
            print(m["id"], "<-", m["source_stem"], f"({m['n_machine_rolls']} roll)")
        return

    os.makedirs(GS_DIR, exist_ok=True)
    def w(name, obj):
        with open(os.path.join(GS_DIR, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
        print(f"  wrote qa/golden-set/{name}")
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
