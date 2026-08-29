"""
test_clearance_check.py — seeded suite for clearance_check.py Thai-floor unification.

Round 1 (2026-07-02): ฉ.55 ข้อ 22 on its own basis, ข้อ 20 bedroom floors, ฉ.39 wet
rooms, door 800/1900 studio floor, lux floor, @0.2 schema guard.
Round 2 (2026-07-03, post-adversarial-verification): wet rooms exempt from the
IRC + habitable-2600 ladder (clear IS the wet basis — was a false-FAIL BLOCKER),
ฉ.39 combined/separated tier resolution, balcony 2200 / office-dining 3000 tiers,
defaulted door dims -> WARN not PASS, room_from_spec shared plumbing + f2f
round-trips, schema-guard variants, whole-verdict assertions.

Pure Python, no test framework:  python3 pipeline/scripts/test_clearance_check.py
Exit 0 = every seed produced the exact expected tier.
"""
import json
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clearance_check as cc

RESULTS = []


def expect(name, res, check_sub, status, detail_has=None):
    hits = [r for r in res if check_sub in r["check"]]
    ok = any(r["status"] == status and (detail_has is None or detail_has in r["detail"])
             for r in hits)
    RESULTS.append((name, ok, hits if not ok else None))


def expect_none(name, res, check_sub):
    hits = [r for r in res if check_sub in r["check"]]
    RESULTS.append((name, not hits, hits or None))


def expect_verdict(name, res, fails, warns):
    f = sum(r["status"] == "FAIL" for r in res)
    w = sum(r["status"] == "WARN" for r in res)
    ok = (f == fails and w == warns)
    RESULTS.append((name, ok, f"got {f} fail/{w} warn" if not ok else None))


def run(w_in, d_in, h_in, rtype=None, door=None, f2f_mm=None, items=None):
    room = cc.Room(w_in, d_in, h_in, door=door, rtype=rtype, floor_to_floor_mm=f2f_mm)
    return cc.check(room, items or [])


def tmp_spec(spec):
    fd, p = tempfile.mkstemp(suffix=".json"); os.close(fd)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(spec, f)
    return p


# --- ข้อ 22 ระยะดิ่ง (non-wet): three bases ---------------------------------------
expect("kh22 indeterminate -> WARN", run(168, 192, 96, rtype="living"),
       "Thai ข้อ 22", "WARN", "cannot prove or refute")
expect("kh22 a-fortiori PASS", run(168, 192, 108, rtype="living"),
       "Thai ข้อ 22", "PASS", "a fortiori")
expect("kh22 f2f 2700 PASS", run(168, 192, 96, rtype="living", f2f_mm=2700),
       "Thai ข้อ 22", "PASS", "floor-to-floor 2700")
expect("kh22 f2f 2500 FAIL", run(168, 192, 96, rtype="living", f2f_mm=2500),
       "Thai ข้อ 22", "FAIL")

# --- ข้อ 22 tier by rtype: ระเบียง 2200; office/dining 3000 WARN-only --------------
rb = run(60, 120, 96, rtype="balcony", f2f_mm=2300)
expect("kh22 balcony 2300 vs 2200 PASS", rb, "Thai ข้อ 22", "PASS")
expect("kh22 balcony no 2600 FAIL", rb, "Thai ข้อ 22", "PASS", "2200")
# round-3: balcony gets NO IRC ergonomic row (legal regime sits below 90in);
# terrace is NOT balcony-tier per doctrine (2600 applies)
expect_none("balcony: no IRC row", run(60, 120, 88, rtype="balcony", f2f_mm=2300),
            "ceiling height (ergonomic)")
expect("terrace stays 2600 tier", run(60, 120, 96, rtype="terrace", f2f_mm=2300),
       "Thai ข้อ 22", "FAIL", "2600")
ro = run(120, 140, 96, rtype="office", f2f_mm=2700)
expect("kh22 office 2700 base PASS", ro, "ceiling height (Thai ข้อ 22)", "PASS")
expect("kh22 office 3000-tier WARN", ro, "office/dining tier", "WARN", "never FAIL")
expect("kh22 office 3100 tier PASS", run(120, 140, 96, rtype="office", f2f_mm=3100),
       "office/dining tier", "PASS")
expect_none("kh22 office tier silent only below 2600 (already WARNed)",
            run(120, 140, 96, rtype="office"), "office/dining tier")
expect("kh22 dining 2700 tier WARN", run(120, 140, 96, rtype="dining", f2f_mm=2700),
       "office/dining tier", "WARN")
# round-3: the [2600,3000) a-fortiori window must NOT go silent — clear 2743
# proves the 2600 row but is only a lower bound vs 3000 -> WARN
expect("kh22 office a-fortiori window WARN", run(120, 140, 108, rtype="office"),
       "office/dining tier", "WARN", "proven basis")
expect("kh22 office clear 3048 tier PASS", run(120, 140, 120, rtype="office"),
       "office/dining tier", "PASS")
# round-4 (NEW-4): compound names hit the tier too (substring, like wet/bed vocab)
expect("kh22 home_office 2700 tier WARN", run(120, 140, 96, rtype="home_office", f2f_mm=2700),
       "office/dining tier", "WARN")

# --- WET rooms: exempt from IRC + habitable ladder (round-2 BLOCKER seeds) ---------
wet_f2f = run(48, 60, 87, rtype="bathroom", f2f_mm=2400)   # legal bath, low slab
expect_none("wet: no habitable kh22 row", wet_f2f, "ceiling height (Thai ข้อ 22)")
expect_none("wet: no IRC row", wet_f2f, "ceiling height (ergonomic)")
expect("wet: clear 2210 decisive PASS", wet_f2f, "bath ceiling", "PASS", "decisive")
expect("wet: kh22 wet row noted", wet_f2f, "bath ceiling", "PASS", "ข้อ 22 wet row agrees")
expect("f39 ceiling 1981 FAIL", run(48, 60, 78, rtype="bath"), "bath ceiling", "FAIL")
# round-3 vocab seeds: substring wet detection (the round-2 fix only covered 4 exact strings)
for _wt in ("ensuite", "powder room", "master_bath", "ห้องน้ำแขก"):
    _wr = run(48, 60, 84, rtype=_wt)
    expect_none(f"wet vocab '{_wt}': no IRC row", _wr, "ceiling height (ergonomic)")
    expect(f"wet vocab '{_wt}': ฉ.39 basis fires", _wr, "bath ceiling", "PASS")

# --- ฉ.39 area tiers: combined / separated / unresolved ---------------------------
wcit = [cc.Item("wc", "wc", 2, 2, 15, 25), cc.Item("shower", "shower", 2, 27, 36, 33)]
comb = run(48, 60, 79.5, rtype="bath", items=wcit)
expect("f39 combined 1.86 PASS", comb, "bath area", "PASS", "combined tier")
expect_verdict("wet legal bath whole-verdict PASS", comb, fails=0, warns=0)
expect("f39 combined 1.40 FAIL",
       run(42, 52, 79.5, rtype="bath", items=[cc.Item("wc", "wc", 2, 2, 15, 25),
                                              cc.Item("shower", "shower", 2, 30, 30, 20)]),
       "bath area", "FAIL", "combined tier")
sep_ok = run(42, 38, 79.5, rtype="wc")            # 1.03 m², narrow 965 mm
expect("f39 separated PASS", sep_ok, "bath area", "PASS", "separated tier")
expect("f39 separated area FAIL", run(36, 36, 79.5, rtype="wc"), "bath area", "FAIL")
expect("f39 separated width FAIL", run(34, 50, 79.5, rtype="wc"), "bath area", "FAIL")
expect("f39 unresolved between (width ok) -> WARN", run(36, 48, 79.5, rtype="bath"),
       "bath area", "WARN", "tier unresolved")
expect("f39 unresolved below both -> FAIL", run(30, 36, 79.5, rtype="bath"),
       "bath area", "FAIL", "EVERY tier")
expect("f39 unresolved above both -> PASS", run(48, 60, 79.5, rtype="bath"),
       "bath area", "PASS", "either tier")
# round-3: area in [0.9,1.5) AND width < 900 = breach under every reading -> FAIL
expect("f39 every-reading breach -> FAIL", run(33.5, 55.6, 79.5, rtype="bath"),
       "bath area", "FAIL", "EVERY tier")
# area >= 1.5 but width < 900: combined passes, separated fails -> honest WARN
expect("f39 wide-area narrow-width -> WARN", run(34, 70, 79.5, rtype="bath"),
       "bath area", "WARN")
# round-3: wc-TYPED room + wash fixture stays SEPARATED (type never upgrades tier)
expect("f39 wc-typed + shower -> separated FAIL",
       run(31.5, 98.4, 79.5, rtype="wc", items=[cc.Item("shower", "shower", 2, 2, 30, 30)]),
       "bath area", "FAIL", "separated tier")
# round-3: substring wash kind ('shower_stall') + wc item -> combined tier
expect("f39 shower_stall kind -> combined",
       run(42, 44, 79.5, rtype="bath", items=[cc.Item("wc", "wc", 2, 2, 15, 25),
                                              cc.Item("stall", "shower_stall", 2, 30, 30, 12)]),
       "bath area", "FAIL", "combined tier")
# round-3: Thai fixture NAME evidence (kind generic)
expect("f39 Thai name evidence -> combined",
       run(48, 60, 79.5, rtype="bath", items=[cc.Item("ชักโครก", "fixture", 2, 2, 15, 25),
                                              cc.Item("ฝักบัว", "fixture", 2, 30, 30, 12)]),
       "bath area", "PASS", "combined tier")
# round-4 (NEW-1): a type label must not DOWNGRADE authored fixture evidence —
# wc-typed room with authored wc+shower is physically combined -> 1.5 floor FAILs
expect("f39 wc-typed + authored both -> combined FAIL",
       run(37.4, 49.6, 79.5, rtype="wc", items=[cc.Item("wc", "wc", 2, 2, 15, 25),
                                                cc.Item("shower", "shower", 2, 30, 30, 15)]),
       "bath area", "FAIL", "combined tier")
# round-4 (NEW-3): English item NAMES are not fixture evidence — a 'shower curtain'
# accessory must not upgrade the tier and drop the 900 mm separated width floor
expect("f39 'shower curtain' name is not wash evidence",
       run(31.5, 98.4, 79.5, rtype="bath", items=[cc.Item("wc", "wc", 2, 2, 15, 25),
                                                  cc.Item("shower curtain", "accessory", 2, 30, 20, 2)]),
       "bath area", "FAIL", "separated tier")
# round-4 (NEW-2): a wet-token bedroom name must still get the ข้อ 20 section —
# 'bedroom_ensuite' routes via the suite branch (never a silent statutory skip)
_be = run(96, 108, 96, rtype="bedroom_ensuite")
expect("bedroom_ensuite: wet rows fire", _be, "bath ceiling", "PASS")
expect("bedroom_ensuite: kh20 section not swallowed", _be, "bedroom area", "WARN", "suite_clearance")
# round-5 (FRESH-1): plain 'ensuite' is a WET room whose name contains "suite" by
# accident — it must NOT collect the suite-routing WARN (whole verdict stays clean)
expect_verdict("ensuite whole-verdict clean", run(48, 60, 84, rtype="ensuite"),
               fails=0, warns=0)
expect("living_suite (non-wet) still routes", run(120, 140, 96, rtype="living_suite"),
       "bedroom area", "WARN", "suite_clearance")

# --- ข้อ 20 bedroom floors (typed) ------------------------------------------------
r99 = run(108, 108, 96, rtype="bedroom")
expect("kh20 area 7.5m2 FAIL", r99, "bedroom area", "FAIL")
expect("kh20 narrow 2743 PASS", r99, "bedroom narrow side", "PASS")
r814 = run(96, 168, 96, rtype="bedroom")
expect("kh20 area 10.4m2 PASS", r814, "bedroom area", "PASS")
expect("kh20 narrow 2438 FAIL", r814, "bedroom narrow side", "FAIL")
expect_none("kh20 not fired for living", run(96, 168, 96, rtype="living"), "bedroom area")
# round-3: doctrine regex typing — compound bedroom names get the statutory rows
expect("kh20 master_bedroom 6.75m2 FAIL", run(96, 108, 96, rtype="master_bedroom"),
       "bedroom area", "FAIL")
expect("kh20 bedroom2 typed", run(120, 168, 96, rtype="bedroom2"), "bedroom area", "PASS")
# suite-typed @0.1 cannot claim the statutory net basis (any '*suite*' routes)
rsuite = run(217, 256, 110, rtype="bedroom_suite")
expect("kh20 suite-typed -> WARN routing", rsuite, "bedroom area", "WARN", "suite_clearance")
expect_none("kh20 suite-typed no narrow claim", rsuite, "bedroom narrow side")
expect("kh20 master_suite routes too", run(217, 256, 110, rtype="master_suite"),
       "bedroom area", "WARN", "suite_clearance")
# bed item in an untyped room -> advisory WARN (ข้อ 20 not silently skipped)
expect("bed item untyped -> WARN", run(120, 140, 96, rtype="studio",
       items=[cc.Item("bed", "bed", 10, 10, 60, 80)]), "bedroom area", "WARN", "not bedroom-typed")

# --- door studio floor (mm); defaulted dims never assert PASS ----------------------
d32 = run(168, 192, 96, door={"w_in": 32, "h_in": 80})
expect("door 813mm PASS", d32, "door width (studio floor)", "PASS")
expect("door 2032mm PASS", d32, "door height (studio floor)", "PASS")
d30 = run(168, 192, 96, door={"w_in": 30, "h_in": 74})
expect("door 762mm FAIL", d30, "door width (studio floor)", "FAIL")
expect("door 1880mm FAIL", d30, "door height (studio floor)", "FAIL")
dnone = run(168, 192, 96, door={"wall": "south"})
expect("door w defaulted -> WARN", dnone, "door width (studio floor)", "WARN", "assumed")
expect("door h defaulted -> WARN", dnone, "door height (studio floor)", "WARN", "assumed")

# --- ergonomic tier unchanged for non-wet (regression) -----------------------------
expect("IRC ergonomic ceiling PASS", run(168, 192, 96), "ceiling height (ergonomic)", "PASS")
expect("IRC ergonomic ceiling FAIL", run(168, 192, 84), "ceiling height (ergonomic)", "FAIL")

# --- the shipped living_demo spec (carries floor_to_floor_mm 2700 as demo data):
#     geometry whole-verdict must be a clean PASS -----------------------------------
_demo_spec_path = os.path.join(HERE, "specs", "living_demo.json")
if os.path.exists(_demo_spec_path):
    _dr, _di, _ds = cc.load_spec(_demo_spec_path)
    expect_verdict("living_demo whole-verdict PASS (f2f known)", cc.check(_dr, _di),
                   fails=0, warns=0)
else:
    RESULTS.append(("living_demo.json exists for verdict test", False, _demo_spec_path))

# --- room_from_spec plumbing + f2f round-trips -------------------------------------
rm = cc.room_from_spec({"type": "living", "width_in": 168, "depth_in": 192,
                        "ceiling_in": 96, "floor_to_floor_in": 110})
RESULTS.append(("room_from_spec f2f_in -> 2794 mm", abs(rm.f2f_mm - 2794.0) < 1e-9, rm.f2f_mm))
rm2 = cc.room_from_spec({"type": "living", "width_in": 168, "depth_in": 192,
                         "ceiling_in": 96, "floor_to_floor_mm": 2650, "floor_to_floor_in": 110})
RESULTS.append(("room_from_spec mm wins over in", rm2.f2f_mm == 2650.0, rm2.f2f_mm))
rm3 = cc.room_from_spec({"type": "living", "width_in": 168, "depth_in": 192, "ceiling_in": 96})
RESULTS.append(("room_from_spec no f2f -> None", rm3.f2f_mm is None, rm3.f2f_mm))
try:
    cc.room_from_spec({"type": "living", "width_in": 168, "depth_in": 192,
                       "ceiling_in": 96, "floor_to_floor_mm": "2.7m"})
    RESULTS.append(("room_from_spec malformed f2f -> loud exit", False, "no exit"))
except SystemExit as e:
    RESULTS.append(("room_from_spec malformed f2f -> loud exit", "invalid" in str(e), str(e)))
except Exception as e:
    RESULTS.append(("room_from_spec malformed f2f -> loud exit", False, repr(e)))

# --- @0.2 schema guard: loud routing, never a KeyError -----------------------------
def guard_case(name, spec, want_sub):
    p = tmp_spec(spec)
    try:
        cc.load_spec(p)
        RESULTS.append((name, False, "no exit raised"))
    except SystemExit as e:
        RESULTS.append((name, want_sub in str(e), str(e)))
    except Exception as e:
        RESULTS.append((name, False, repr(e)))
    finally:
        os.unlink(p)

guard_case("guard: @0.2 outline_mm", {"schema": "interior-ai/room-spec@0.2",
    "room": {"type": "x", "ceiling_mm": 2600, "outline_mm": [[0, 0], [1, 0], [1, 1], [0, 1]]}},
    "suite_clearance")
guard_case("guard: @0.2.1 variant, no outline", {"schema": "interior-ai/room-spec@0.2.1",
    "room": {"type": "x", "ceiling_mm": 2600}}, "suite_clearance")
guard_case("guard: units=metric only", {"units": "metric", "room": {"type": "x"}},
    "suite_clearance")
guard_case("guard: units=Metric capitalized", {"units": "Metric", "room": {"type": "x"}},
    "suite_clearance")
guard_case("guard: no markers -> width_in msg", {"room": {"type": "x", "depth_in": 100}},
    "width_in missing")
guard_case("guard: room is not an object", {"room": 5}, "must be an object")
guard_case("guard: top-level array", [1, 2, 3], "must be an object")
# inch spec carrying auxiliary metric data must still process
_p = tmp_spec({"schema": "interior-ai/room-spec@0.1",
               "room": {"type": "living", "width_in": 168, "depth_in": 192, "ceiling_in": 96,
                        "outline_mm": [[0, 0], [4267, 0], [4267, 4877], [0, 4877]]}})
try:
    _room, _items, _s = cc.load_spec(_p)
    RESULTS.append(("guard: @0.1 with aux outline processes", _room.W == 168.0, None))
except BaseException as e:
    RESULTS.append(("guard: @0.1 with aux outline processes", False, repr(e)))
finally:
    os.unlink(_p)

# --- legal lux floor: unconditional demo test + statutory tier for wet -------------
_demo_spec = os.path.join(HERE, "specs", "living_demo.json")
if not os.path.exists(_demo_spec):
    RESULTS.append(("living_demo.json exists for lux test", False, _demo_spec))
else:
    _, _, _s = cc.load_spec(_demo_spec)
    expect("legal lux floor line present", cc.check_lighting(_s),
           "legal lux floor", "PASS", "studio-adopted")
_bath_light_spec = {"room": {"type": "Bathroom", "width_in": 48, "depth_in": 60,
                             "ceiling_in": 84, "wall_thk_in": 4.5}, "items": []}
lres = cc.check_lighting(_bath_light_spec)
_lux_hits = [r for r in lres if "legal lux floor" in r["check"]]
RESULTS.append(("lux tier statutory for 'Bathroom' (case-insensitive)",
                any("statutory" in r["detail"] for r in _lux_hits),
                _lux_hits or "no lux line (no ambient fixtures?)"))

# --- kitchen aisles: the 2026-08-29 negative control --------------------------------
# THE STATE THAT PRODUCED THE INCIDENT, not today's numbers (D-056). TRN-003's island
# was built a quarter turn out: its long axis ran ACROSS the room instead of along the
# kitchen wall, putting its near edge 420 mm INSIDE the 650 mm counter run. Every rung
# in the render lane was green. These rows prove the checker convicts that layout, and
# they are written in the room's real millimetres, converted at the boundary.
MM = cc.MM_PER_IN


def _in(mm):
    return mm / MM


# The room the plate shows: 8000 mm along the glazing wall, 6500 deep, 3514 ceiling.
_kroom = cc.Room(_in(8000), _in(6500), _in(3514), rtype="kitchen")
# The counter run against the kitchen wall: 650 mm deep, 2804 long.
_bench = cc.Item("bench", "bench", 0, 0, _in(650), _in(2804))

# WRONG: long axis 3072 mm across the room, near edge at x = 230 mm.
_isl_wrong = cc.Item("island_slab", "island", _in(230), _in(2256), _in(3072), _in(1250))
_res_wrong = cc.check(_kroom, [_bench, _isl_wrong])
expect("TRN-003 NEGATIVE CONTROL: the island as built overlaps the counter run",
       _res_wrong, "overlap: bench / island_slab", "FAIL", "420 mm")
expect("...and the aisle row calls it an impossible kitchen, not a tight one",
       _res_wrong, "kitchen aisle", "FAIL", "NEGATIVE aisle")

# CORRECTED: long axis 3072 mm ALONG the wall, near edge at x = 1693 mm -> 1043 mm aisle.
_isl_right = cc.Item("island_slab", "island", _in(1693), _in(2256), _in(1250), _in(3072))
_res_right = cc.check(_kroom, [_bench, _isl_right])
expect("TRN-003: the corrected island no longer overlaps",
       _res_right, "kitchen aisle (island_slab <-> bench)", "WARN")
_aisle = [r for r in _res_right if "kitchen aisle" in r["check"]]
RESULTS.append(("...and it is REVIEW, not PASS: 1043 mm is under the studio's own "
                "1219 mm opposing-counter figure",
                bool(_aisle) and "1043 mm" in _aisle[0]["detail"], _aisle))

# A genuinely generous aisle passes, so the rung can say yes.
_isl_wide = cc.Item("island_slab", "island", _in(2000), _in(2256), _in(1250), _in(3072))
expect("a 1350 mm aisle passes", cc.check(_kroom, [_bench, _isl_wide]),
       "kitchen aisle (island_slab <-> bench)", "PASS")

# The rules that had no reader now have one, and the row cites them.
RESULTS.append(("kitchen_NKBA is actually read (the row names both authorities)",
                any("NKBA" in r["detail"] and "P and Z" in r["detail"]
                    for r in _res_right if "kitchen aisle" in r["check"]), None))

# Landing + triangle: they report COULD NOT RUN rather than passing silently.
_sink = cc.Item("sink", "sink", _in(100), _in(400), _in(600), _in(500))
_res_nl = cc.check(_kroom, [_sink])
expect("a sink on no counter reports COULD NOT RUN, never PASS",
       _res_nl, "landing beside sink", "WARN", "COULD NOT RUN")
_res_tri = cc.check(_kroom, [_sink, cc.Item("hob", "cooktop", _in(100), _in(1500),
                                            _in(600), _in(600))])
expect("two of three triangle vertices is COULD NOT RUN",
       _res_tri, "work triangle", "WARN", "COULD NOT RUN")

# --- report ------------------------------------------------------------------------
fails = [(n, d) for n, ok, d in RESULTS if not ok]
for n, ok, _d in RESULTS:
    print(f"  [{'OK' if ok else 'XX'}] {n}")
print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} green")
if fails:
    for n, d in fails:
        print(f"  FAILED: {n}: {d}")
    sys.exit(1)
