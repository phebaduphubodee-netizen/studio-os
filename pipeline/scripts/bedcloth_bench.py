"""BED-CLOTH ACQUISITION BENCH — measure every candidate set against THIS bed,
before any of them costs a build.

Run:  blender -b <built>.blend --python bedcloth_bench.py -- <cache_dir> <out.json>
                                                            [slug,slug,...]

WHY IT EXISTS: p2r31's first acquired leg rendered a bare white mattress with a
knotted rag on it, and the coverage guard inside the build passed it — because that
guard compared BOUNDING BOXES, and a bounding box cannot tell a spread sheet from a
crumpled one (R9b's own lesson: an AABB cannot tell interlocking from intersecting).
This measures the thing itself, by ray.

REWRITTEN p2r41, and the reason is the finding of that round. This file used to carry
its OWN copy of the staging rules, and the copy was the pre-p2r32 one: parts were kept
only at >= 33% of the mattress plan, so every accessory cloth — one set's 374 x 1600 mm
turned-down runner among them — was DELETED before the candidate was measured or
photographed. From p2r32 to p2r41 the build dressed the bed with runners and the
audition judged the same files without them. It also computed a rotation and never
applied it. Staging now comes from `bedcloth_fit`, the module the build itself uses:
the audition and the frame cannot be two different objects again.

WHAT IS MEASURED, all derived from the bed in the open .blend — nothing typed:
  coverage    fraction of mattress plan points with cloth above them (RAY)
  relief_mm   p90-p10 spread of cloth height over the mattress
  fall_sides  how many of the four flanks carry cloth below the mattress top
  need_scale  the scale this asset needs to COVER this mattress — the spec's own
              `model_requirements.covers` rule (max_scale 1.0: never stretch)

AND THE RANK IS NOT COVERAGE, which is the mistake that decided a purchase. p2r31
ranked on coverage, and coverage is MAXIMISED by a cloth that lies flat on the mattress
without reaching past it — a duvet too small to drape scores best. The number that
answers the real question was printed in the same table and read past: falls past 2 of
4 sides. So the machine now applies three HARD filters and then stops:

    size_ok      need_scale <= 1.0     (a mesh is never stretched to fit)
    covered      coverage   >= 0.80    (the build's own cut: our mattress must not
                                        show through)
    drapes       fall_sides >= 2       (a cover falls over the flanks; on a bed
                                        against a headboard the reachable maximum
                                        is 3 — two sides and the foot)

relief_mm stays REPORT-ONLY with both of its failure directions named — a crumple
(the signed DD says the room is made, not slept in) and a painted plane (what both
critics have filed for three rounds). No number in this repo can currently ground a
band for it, and inventing one would be taste wearing a threshold. The eye decides
style; the machine's job is only to stop the eye wasting time on sets that cannot fit,
cannot cover, or cannot drape. That split is the owner's practitioner rung, made into
a tool.
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedcloth_fit as fit  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CACHE, OUT = argv[0], argv[1]
ONLY = set(argv[2].split(",")) if len(argv) > 2 and argv[2] else None

COVER_CUT = 0.80
FALL_CUT = 2
MAX_SCALE = 1.0

matt = bpy.data.objects["bed__mattress"]
mw = [matt.matrix_world @ v.co for v in matt.data.vertices]
MX0, MY0 = min(c.x for c in mw), min(c.y for c in mw)
MX1, MY1 = max(c.x for c in mw), max(c.y for c in mw)
MTOP = max(c.z for c in mw)
RECT = (MX0, MY0, MX1 - MX0, MY1 - MY0)
base = bpy.data.objects.get("bed__base")
bw = [base.matrix_world @ v.co for v in base.data.vertices] if base else mw
BZ = max(c.z for c in bw)                 # base top = where a hem may reach
# CEILING and FLOOR, both derived from the bed (see bedcloth_fit.plan_scale). The
# rule this replaces used min(bed outer line, mattress + 40 mm) as a TARGET, which on
# this bed is 1800 x 1949 against a mattress of 1820 x 1969 — it shrank every
# candidate to smaller than the thing it must cover.
LIMIT, COVER = fit.limits_for(RECT, MTOP, BZ)

print(f"BENCH bed: mattress {RECT[2]*1000:.0f} x {RECT[3]*1000:.0f} mm, top "
      f"{MTOP*1000:.0f}, base top {BZ*1000:.0f}, fall {(MTOP-BZ)*1000:.0f} mm; "
      f"must cover {COVER[0]*1000:.0f} x {COVER[1]*1000:.0f}, may not exceed "
      f"{LIMIT[0]*1000:.0f} x {LIMIT[1]*1000:.0f} x {LIMIT[2]*1000:.0f} mm "
      f"at scale <= {MAX_SCALE}")

# strip the bedding the build shipped so it cannot be measured as a candidate's cloth
for o in list(bpy.data.objects):
    if o.type == 'MESH' and ("cloth__acq" in o.name or o.name in
                             ("bed__coverlet", "bed__duvet", "bed__throw")):
        bpy.data.objects.remove(o, do_unlink=True)

rows = []
for slug in sorted(os.listdir(CACHE)):
    d = os.path.join(CACHE, slug)
    if not os.path.isdir(d) or (ONLY and slug not in ONLY):
        continue
    glbs = [f for f in os.listdir(d) if f.endswith(".glb")]
    if not glbs:
        continue
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=os.path.join(d, glbs[0]))
    except Exception as e:                                    # noqa: BLE001
        rows.append({"slug": slug, "error": str(e)[:120]})
        print(f"BENCH {slug:14s} IMPORT FAILED: {str(e)[:60]}")
        continue
    news = [o for o in bpy.data.objects if o not in before]
    names = [o.name for o in news]
    row = {"slug": slug, "file": glbs[0]}
    st = fit.stage(news, RECT, MTOP, BZ, LIMIT, cover=COVER, max_scale=MAX_SCALE)
    if "reject" in st:
        row.update({"verdict": st["reject"], "parts_total": st.get("parts_total"),
                    "need_scale": st.get("need_scale"),
                    "native_mm": st.get("native_mm"), "survives": False})
        print(f"BENCH {slug:14s} — {st['reject']}")
    else:
        need = st["need_scale"]
        size_ok = need <= st["scale"] + 1e-9
        covered = st["coverage"] >= COVER_CUT
        drapes = st["fall_sides"] >= FALL_CUT
        row.update({
            "parts_total": st["parts_total"], "field": len(st["field"]),
            "extra": len(st["extra"]), "dropped": st["parts_dropped"],
            "buried": st["parts_buried"], "scale": round(st["scale"], 3),
            "rot": st["rot"], "native_mm": st["native_mm"],
            "coverage": round(st["coverage"], 3),
            "relief_mm": round(st["relief_mm"], 1),
            "fall_sides": st["fall_sides"], "need_scale": round(need, 3),
            "size_ok": size_ok, "covered": covered, "drapes": drapes,
            "survives": bool(size_ok and covered and drapes)})
        print(f"BENCH {slug:14s} {len(st['field'])}F+{len(st['extra'])}E of "
              f"{st['parts_total']:2d}  scale {st['scale']:5.3f}  "
              f"cover {st['coverage']*100:5.1f}%  relief {st['relief_mm']:6.1f} mm  "
              f"fall {st['fall_sides']}/4  need {need:5.3f}x  "
              f"{'SURVIVES' if row['survives'] else 'out: ' + ','.join(
                  k for k, ok in (('size', size_ok), ('cover', covered),
                                  ('drape', drapes)) if not ok)}")
    rows.append(row)
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"bed": {"mattress_mm": [round(RECT[2] * 1000), round(RECT[3] * 1000)],
                       "limit_mm": [round(v * 1000) for v in LIMIT],
                       "must_cover_mm": [round(v * 1000) for v in COVER],
                       "fall_mm": round((MTOP - BZ) * 1000)},
               "cuts": {"coverage": COVER_CUT, "fall_sides": FALL_CUT,
                        "max_scale": MAX_SCALE},
               "candidates": rows}, fh, indent=1)
surv = [r["slug"] for r in rows if r.get("survives")]
print(f"BENCH wrote {OUT} ({len(rows)} candidate(s), {len(surv)} survive all three "
      f"cuts): {','.join(surv) if surv else '(none)'}")
