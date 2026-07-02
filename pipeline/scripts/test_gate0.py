"""
test_gate0.py — seeded-violation acceptance suite for suite_clearance v0.4.1 (Gate 0).

M3.1 acceptance (blueprint §13): "Seeded violations (blocked swing, 800 mm
corridor, collision) all caught pre-render" — plus the v0.4 leg-width tiers,
ข้อ 21 corridor tiers, ฉ.39 bath tiers, the v0.3.1 ข้อ 22 honesty regressions,
and regression seeds for every confirmed finding of the v0.4 adversarial
scrutiny (qa/reports/2026-07-02-gate0-full.md): as-built wall bands, separated
WC tier, net-area containment, condo-corridor honesty, off-centre doorway
starts, through-wall reach, platform-ledge bed access, rot 90, swing-vs-wall.

Pure Python, no test framework:  python3 pipeline/scripts/test_gate0.py
Exit 0 = all seeded violations caught with the exact expected tier.
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite_clearance as sc

RESULTS = []


def room(w, d, rtype="study", ceiling=2800, **room_extra):
    spec = {"schema": "interior-ai/room-spec@0.2", "units": "metric",
            "room": {"type": rtype, "ceiling_mm": ceiling,
                     "outline_mm": [[0, 0], [w, 0], [w, d], [0, d]]},
            "items": [], "builtins": [], "subrooms": []}
    spec["room"].update(room_extra)
    return spec


def expect(name, res, check_sub, status, detail_has=None):
    rows = [r for r in res if check_sub in r["check"]]
    if not rows:
        RESULTS.append((False, name, f"no check matching {check_sub!r}"))
        return
    got = rows[0]
    ok = got["status"] == status and (detail_has is None or detail_has in got["detail"])
    RESULTS.append((ok, name,
                    f"{check_sub!r}: want {status}"
                    + (f" containing {detail_has!r}" if detail_has else "")
                    + f", got {got['status']} — {got['detail'][:110]}"))


def expect_verdict(name, res, fails, warns):
    f = sum(r["status"] == "FAIL" for r in res)
    w = sum(r["status"] == "WARN" for r in res)
    RESULTS.append(((f, w) == (fails, warns), name,
                    f"want {fails} fail/{warns} warn, got {f}/{w}: "
                    + "; ".join(f"{r['check']}={r['status']}" for r in res
                                if r["status"] != "PASS")[:220]))


# ---- M3.1 seed 1: blocked door swing -> FAIL ------------------------------
s = room(4000, 4000)
s["door"] = {"x": 500, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
s["builtins"] = [{"name": "wardrobe-in-the-arc", "kind": "wardrobe",
                  "x": 600, "y": 200, "w": 900, "d": 600, "h": 2400}]
expect("seed1 blocked swing", sc.check(s), "door swing: entry", "FAIL")

s = room(4000, 4000)
s["door"] = {"x": 500, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
s["builtins"] = [{"name": "wardrobe-clear", "kind": "wardrobe",
                  "x": 2000, "y": 0, "w": 900, "d": 600, "h": 2400}]
expect("seed1b clear swing", sc.check(s), "door swing: entry", "PASS")

# leaf reaching past the room boundary (L-room, arc crosses the notch) -> WARN
s = room(3000, 4000)
s["room"]["outline_mm"] = [[0, 0], [3000, 0], [3000, 600], [1500, 600], [1500, 4000], [0, 4000]]
s["door"] = {"x": 2000, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
expect("seed1c swing vs room wall", sc.check(s), "door swing: entry", "WARN")

# ---- M3.1 seed 2: 800 mm corridor between furniture -> caught (WARN) ------
def pinched(gap):
    s = room(3000, 5000, rtype="living")
    s["door"] = {"x": 1050, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
    half = (3000 - gap) / 2.0
    s["builtins"] = [
        {"name": "left-unit", "kind": "cabinet", "x": 0, "y": 2000, "w": half, "d": 1000, "h": 2400},
        {"name": "right-unit", "kind": "cabinet", "x": 3000 - half, "y": 2000, "w": half, "d": 1000, "h": 2400}]
    s["items"] = [{"name": "sofa", "kind": "sofa", "x": 800, "y": 4000, "w": 1500, "d": 900, "h": 850}]
    return s

expect("seed2 800mm corridor", sc.check(pinched(800)), "circulation: entry -> sofa", "WARN")
expect("seed2b 1000mm corridor", sc.check(pinched(1000)), "circulation: entry -> sofa", "PASS")
expect("seed2c 500mm pinch", sc.check(pinched(500)), "circulation: entry -> sofa", "FAIL")

# entry console blocking only the doorway CENTRE must not zero the bottleneck
s = room(5000, 5000, rtype="living")
s["door"] = {"x": 2000, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
s["builtins"] = [{"name": "post", "kind": "cabinet", "x": 2000, "y": 200, "w": 200, "d": 200, "h": 1000}]
s["items"] = [{"name": "sofa", "kind": "sofa", "x": 1500, "y": 4000, "w": 2000, "d": 900, "h": 850}]
expect("seed2d off-centre console -> still passable", sc.check(s),
       "circulation: entry -> sofa", "PASS")

# console across the doorway centre: tight but NOT 'no clear path'
s["builtins"] = [{"name": "console", "kind": "cabinet", "x": 2300, "y": 0, "w": 300, "d": 450, "h": 1000}]
res = sc.check(s)
rows = [r for r in res if "circulation: entry -> sofa" in r["check"]]
RESULTS.append((bool(rows) and "bottleneck" in rows[0]["detail"],
                "seed2e centre console -> measured, not unreachable",
                rows[0]["detail"][:110] if rows else "row missing"))

# target behind a full-width thin partition must NOT be 'reached' through it
s = room(4000, 5000, rtype="bedroom")
s["door"] = {"x": 1500, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
s["builtins"] = [{"name": "partition", "kind": "partition", "x": 0, "y": 2000, "w": 4000, "d": 100, "h": 2800}]
s["items"] = [{"name": "bed", "kind": "bed", "x": 1000, "y": 2150, "w": 2000, "d": 2200, "h": 600}]
expect("seed2f no reach through a thin wall", sc.check(s),
       "circulation: entry -> bed", "FAIL", detail_has="no clear path")

# a bed on a wide platform ledge is reachable by stepping onto the platform
s = room(5000, 5500, rtype="bedroom")
s["door"] = {"x": 2000, "y": 0, "w": 900, "h": 2000, "wall": "south", "swing": "in-left"}
s["items"] = [
    {"name": "platform", "kind": "platform", "x": 1100, "y": 2000, "w": 2800, "d": 3000, "h": 150},
    {"name": "bed", "kind": "bed", "x": 1500, "y": 2400, "w": 2000, "d": 2200, "h": 600}]
expect("seed2g platform-ledge bed reachable", sc.check(s),
       "circulation: entry -> bed", "PASS")

# ---- M3.1 seed 3: collision (bbox overlap) -> caught (WARN) ----------------
s = room(4000, 4000)
s["builtins"] = [
    {"name": "cabinet-A", "kind": "cabinet", "x": 500, "y": 500, "w": 1200, "d": 600, "h": 2000},
    {"name": "cabinet-B", "kind": "cabinet", "x": 1000, "y": 700, "w": 1200, "d": 600, "h": 2000}]
expect("seed3 collision", sc.check(s), "overlap: cabinet-A / cabinet-B", "WARN")

s = room(4000, 4000)
s["items"] = [{"name": "chair-outside", "kind": "armchair", "x": 3800, "y": 100, "w": 500, "d": 500, "h": 800}]
expect("seed3b out-of-bounds", sc.check(s), "in-bounds: chair-outside", "FAIL")

# room furniture inside a walled sub-room (as-built keep-out) -> FAIL
s = room(4000, 4000)
s["subrooms"] = [{"name": "bath", "outline_mm": [[0, 2500], [1500, 2500], [1500, 4000], [0, 4000]],
                  "ceiling_mm": 2200, "fixtures": []}]
s["items"] = [{"name": "desk-in-bath", "kind": "desk", "x": 200, "y": 2700, "w": 600, "d": 600, "h": 750}]
expect("seed3c item inside sub-room", sc.check(s), "in-bounds: desk-in-bath", "FAIL")

# inside the WALL BAND (as-built keep-out beyond the raw outline) -> FAIL too
s["items"] = [{"name": "desk-in-band", "kind": "desk", "x": 1520, "y": 2700, "w": 600, "d": 600, "h": 750}]
expect("seed3c2 item in the wall band", sc.check(s), "in-bounds: desk-in-band", "FAIL")

# flush against the as-built band face (x >= 1600 = 1500 + thk 100) stays legal
s["items"] = [{"name": "desk-flush", "kind": "desk", "x": 1600, "y": 2700, "w": 600, "d": 600, "h": 750}]
expect("seed3d flush to as-built wall", sc.check(s), "in-bounds: desk-flush", "PASS")

# fixture-vs-fixture overlap inside a sub-room -> WARN
s = room(4000, 4000)
s["subrooms"] = [{"name": "bath", "outline_mm": [[0, 2500], [2000, 2500], [2000, 4000], [0, 4000]],
                  "ceiling_mm": 2200, "fixtures": [
                      {"name": "shower", "kind": "shower", "x": 100, "y": 2600, "w": 900, "d": 900},
                      {"name": "stool-on-shower", "kind": "stool", "x": 500, "y": 2800, "w": 400, "d": 400}]}]
expect("seed3e fixture overlap", sc.check(s), "overlap in bath", "WARN")

# rot 90 swaps the footprint about the centre (matching build_room)
s = room(4000, 4000)
s["items"] = [{"name": "console-rot", "kind": "console", "x": 3600, "y": 200, "w": 200, "d": 900, "h": 800}]
expect("seed3f unrotated in-bounds", sc.check(s), "in-bounds: console-rot", "PASS")
s["items"][0]["rot"] = 90
expect("seed3g rot90 pushes it out", sc.check(s), "in-bounds: console-rot", "FAIL")

# ---- v0.4 leg-width tiers (ฉ.55 ข้อ 20 narrow side, AS-BUILT basis) --------
# mixed legs (pre-revision bedroom_suite geometry): WARN with as-built numbers
s = room(5500, 6500, rtype="bedroom_suite")
s["subrooms"] = [{"name": "ensuite", "outline_mm": [[0, 3900], [3100, 3900], [3100, 6500], [0, 6500]],
                  "ceiling_mm": 2000, "fixtures": []}]
s["items"] = [{"name": "bed", "kind": "bed", "x": 3298, "y": 1066, "w": 2000, "d": 2160, "h": 600}]
res = sc.check(s)
expect("leg mixed -> interpretation WARN", res, "bedroom narrow side (interpretation)", "WARN")
row = [r for r in res if "interpretation" in r["check"]][0]
RESULTS.append(("2300" in row["detail"] and "3800" in row["detail"],
                "leg mixed reports AS-BUILT widths (2300-3800)", row["detail"][:130]))

# every as-built leg >= 2500 (ensuite interior 2900 + 100 band) -> decisive PASS
s["subrooms"][0]["outline_mm"] = [[0, 3900], [2900, 3900], [2900, 6500], [0, 6500]]
expect("leg all >= 2500 as-built -> PASS", sc.check(s), "bedroom narrow side (leg-proof", "PASS")

# no clear zone >= 2500 anywhere (plus-shape, bbox 6000 but all legs 2000) -> FAIL
s = room(6000, 6000, rtype="bedroom")
s["room"]["outline_mm"] = [[2000, 0], [4000, 0], [4000, 2000], [6000, 2000], [6000, 4000],
                           [4000, 4000], [4000, 6000], [2000, 6000], [2000, 4000],
                           [0, 4000], [0, 2000], [2000, 2000]]
expect("leg nowhere >= 2500 -> FAIL", sc.check(s), "bedroom narrow side (leg-proof", "FAIL")

# bbox itself under 2500 -> proven breach (v0.3.1 path kept)
s = room(2300, 8000, rtype="bedroom")
expect("bbox < 2500 -> FAIL", sc.check(s), "bedroom narrow side", "FAIL")

# ---- ข้อ 20 net area: exact grid, no false FAIL from malformed sub-rooms ----
s = room(3200, 3000, rtype="bedroom")   # 9.6 m², fully compliant
s["subrooms"] = [{"name": "ensuite", "ceiling_mm": 2200,
                  "outline_mm": [[3200, 0], [5000, 0], [5000, 1800], [3200, 1800]]}]  # OUTSIDE
expect("net area ignores sub-room outside the outline", sc.check(s),
       "bedroom area", "PASS")
s = room(4000, 4000, rtype="bedroom")   # 16 m²; two OVERLAPPING closets, union 6.25 m²
s["subrooms"] = [
    {"name": "closet-a", "ceiling_mm": 2400, "outline_mm": [[0, 1500], [2500, 1500], [2500, 4000], [0, 4000]]},
    {"name": "closet-b", "ceiling_mm": 2400, "outline_mm": [[1500, 1500], [2500, 1500], [2500, 4000], [1500, 4000]]}]
expect("net area counts overlapping sub-rooms once", sc.check(s),
       "bedroom area", "PASS")

# ---- ข้อ 21 corridor tiers --------------------------------------------------
def corridor(w, building=None):
    s = room(w, 4000, rtype="corridor")
    if building:
        s["room"]["building"] = building
    return sc.check(s)

expect("corridor 900 house -> FAIL", corridor(900, "house"), "corridor width", "FAIL")
expect("corridor 1200 house -> PASS", corridor(1200, "house"), "corridor width", "PASS")
expect("corridor 1200 condo -> WARN (in-unit 1500 = vault gap)", corridor(1200, "condo"),
       "corridor width", "WARN", detail_has="vault gap")
expect("corridor 1600 condo -> PASS", corridor(1600, "condo"), "corridor width", "PASS")
expect("corridor 1200 unknown -> WARN", corridor(1200), "corridor width", "WARN")
expect("corridor 1600 unknown -> PASS", corridor(1600), "corridor width", "PASS")

# a door niche must NOT produce a false statutory FAIL
s = room(1200, 4000, rtype="corridor", building="house")
s["room"]["outline_mm"] = [[0, 0], [1200, 0], [1200, 1500], [1600, 1500],
                           [1600, 2400], [1200, 2400], [1200, 4000], [0, 4000]]
expect("corridor with niche -> WARN not FAIL", sc.check(s), "corridor width", "WARN")

# corridor that also holds a bed keeps BOTH the ข้อ 21 row and the heuristic row
# (1600 x 4000 = 6.4 m² < 8 -> the bed-item heuristic surfaces as WARN tier)
s = room(1600, 4000, rtype="corridor", building="house")
s["items"] = [{"name": "daybed", "kind": "bed", "x": 100, "y": 100, "w": 900, "d": 2000, "h": 500}]
res = sc.check(s)
expect("corridor+bed keeps ข้อ 21 row", res, "corridor width", "PASS")
expect("corridor+bed keeps bedroom heuristic row", res, "bedroom area", "WARN")

# ---- ข้อ 22 tiers ------------------------------------------------------------
s = room(4000, 4000, floor_to_floor_mm=2550, ceiling=2400)
expect("f2f 2550 -> statutory FAIL", sc.check(s), "ระยะดิ่ง (room, floor-to-floor)", "FAIL")
s = room(4000, 4000, ceiling=2500)
expect("clear 2500, no f2f -> WARN", sc.check(s), "ceiling height (room)", "WARN")
s = room(3000, 2000, rtype="balcony (ระเบียง)", floor_to_floor_mm=2300, ceiling=2100)
expect("balcony f2f 2300 -> PASS (2200 tier)", sc.check(s),
       "ระยะดิ่ง (room, floor-to-floor)", "PASS")
s = room(4000, 4000, rtype="home_office (สำนักงาน)", floor_to_floor_mm=2800, ceiling=2600)
res = sc.check(s)
expect("office f2f 2800 -> PASS at 2600", res, "ระยะดิ่ง (room, floor-to-floor)", "PASS")
expect("office 3000-tier surfaces as WARN", res, "office/dining tier", "WARN")

# ---- ฉ.39 wet-room tiers -----------------------------------------------------
# combined (fixtures show both) 1.4 m² -> FAIL
s = room(4000, 4000)
s["subrooms"] = [{"name": "bath", "ceiling_mm": 2200,
                  "outline_mm": [[0, 2600], [1000, 2600], [1000, 4000], [0, 4000]],
                  "fixtures": [{"name": "shower", "kind": "shower", "x": 50, "y": 2650, "w": 900, "d": 900},
                               {"name": "wc", "kind": "wc", "x": 100, "y": 3600, "w": 400, "d": 380}]}]
expect("combined bath 1.4 m2 -> FAIL", sc.check(s), "bath area", "FAIL")
# separated WC 900x1400 = 1.26 m² -> PASS (0.9 tier + 900 width), NOT a 1.5 FAIL
s = room(4000, 4000)
s["subrooms"] = [{"name": "wc (separate)", "th": "ห้องส้วมแยก", "ceiling_mm": 2200,
                  "outline_mm": [[0, 2600], [900, 2600], [900, 4000], [0, 4000]],
                  "fixtures": [{"name": "wc", "kind": "wc", "x": 250, "y": 3200, "w": 400, "d": 650}]}]
res = sc.check(s)
expect("separated WC 1.26 m2 -> PASS", res, "bath area", "PASS")
expect("separated WC width 900 -> PASS", res, "bath width", "PASS")
# no fixture data, 1.4 m² -> WARN (tier unresolved), never a statutory FAIL
s = room(4000, 4000)
s["subrooms"] = [{"name": "bath", "ceiling_mm": 2200,
                  "outline_mm": [[0, 2600], [1000, 2600], [1000, 4000], [0, 4000]], "fixtures": []}]
expect("bath 1.4 m2 unknown tier -> WARN", sc.check(s), "bath area", "WARN")
# wet MAIN room: ฉ.39 rows + wet ceiling basis (2200 clear = PASS, not a ข้อ 22 WARN)
s = room(1200, 1000, rtype="guest bath (ห้องน้ำแขก)", ceiling=2200)
s["items"] = [{"name": "shower", "kind": "shower", "x": 100, "y": 100, "w": 900, "d": 900, "h": 2000},
              {"name": "wc", "kind": "wc", "x": 100, "y": 550, "w": 400, "d": 380, "h": 400}]
res = sc.check(s)
expect("wet main room ceiling 2200 -> PASS (พื้นถึงเพดาน)", res, "ceiling height (room, wet)", "PASS")
expect("wet main room 1.2 m2 combined -> FAIL", res, "bath area", "FAIL")

# blocked SUB-room door swing (out-swing into furniture) -> FAIL
s = room(5000, 5000, rtype="bedroom_suite")
s["subrooms"] = [{"name": "ensuite", "ceiling_mm": 2200,
                  "outline_mm": [[0, 3000], [2500, 3000], [2500, 5000], [0, 5000]],
                  "door": {"x": 800, "y": 3000, "w": 800, "wall": "south", "swing": "out-right"},
                  "fixtures": []}]
s["items"] = [{"name": "bed", "kind": "bed", "x": 2800, "y": 500, "w": 2000, "d": 2200, "h": 600},
              {"name": "ottoman-in-arc", "kind": "ottoman", "x": 900, "y": 2400, "w": 600, "d": 500, "h": 400}]
expect("sub-room out-swing blocked -> FAIL", sc.check(s), "door swing: ensuite", "FAIL")
s["items"] = s["items"][:1]
expect("sub-room out-swing clear -> PASS", sc.check(s), "door swing: ensuite", "PASS")

# donut room (interior sub-room island): ring legs 2000 -> proven ข้อ 20 breach
s = room(6000, 6000, rtype="bedroom")
s["subrooms"] = [{"name": "island-closet", "ceiling_mm": 2400,
                  "outline_mm": [[2000, 2000], [4000, 2000], [4000, 4000], [2000, 4000]]}]
expect("donut ring legs -> FAIL", sc.check(s), "bedroom narrow side (leg-proof", "FAIL")

# ---- shipped specs stay green ----------------------------------------------
for spec_name, exp_f, exp_w in (("bedroom_suite.json", 0, 0), ("living_condo.json", 0, 0)):
    with open(os.path.join(HERE, "specs", spec_name), encoding="utf-8") as fh:
        expect_verdict(f"shipped {spec_name}", sc.check(json.load(fh)), exp_f, exp_w)

# ---- report -----------------------------------------------------------------
fails = [r for r in RESULTS if not r[0]]
print(f"\n=== Gate 0 seeded-violation suite: {len(RESULTS) - len(fails)}/{len(RESULTS)} passed ===")
for ok, name, detail in RESULTS:
    print(f"  [{'OK' if ok else 'XX'}] {name}" + ("" if ok else f"\n       {detail}"))
if fails:
    sys.exit(1)
print("M3.1 acceptance: blocked swing, 800 mm corridor, collision — all caught pre-render.")
