"""
layout_gen.py — brief -> DRAFT spec (rule-based auto-layout), self-validated.

Turns a tiny brief (room type + size) into a placed furniture SPEC and runs it
through clearance_check until it PASSES (shrinking / dropping pieces on failure).
This is the "layout" step research flagged as the human-kept part — so the output
is honestly a DRAFT a designer refines, NOT a final design. It exists to make the
pipeline runnable end-to-end (brief -> spec -> 3 deliverables) and to give the
human a sane starting point instead of a blank room.

    python pipeline/layout_gen.py living 14 16            # -> prints spec, PASS/REVIEW
    python pipeline/layout_gen.py living 14 16 out.json   # -> also writes the spec

Convention matches furniture.py: an item's front faces -Y (toward the south wall).
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clearance_check as cc

_DEFAULT_SIZE = {  # kind -> (w, d, h) inches
    "sofa": (84, 36, 34), "armchair": (32, 32, 34), "coffee_table": (42, 22, 18),
    "tv_console": (60, 16, 24), "dining_table": (60, 36, 30), "dining_chair": (18, 18, 34),
    "bed": (60, 80, 40), "nightstand": (18, 18, 26), "desk": (48, 24, 30), "chair": (18, 18, 34),
}


def generate(brief):
    W = round(brief["width_ft"] * 12)
    D = round(brief["depth_ft"] * 12)
    H = brief.get("ceiling_in", 96)
    rt = brief.get("room_type", "living")
    door = brief.get("door", {"w_in": 32, "h_in": 80, "wall": "south"})

    items = _living(W, D) if rt == "living" else _generic(W, D, brief.get("kinds", []))
    spec = _wrap(rt, W, D, H, door, items, brief)

    status = _validate(spec)
    if status == "FAIL" and rt == "living":          # fallback: a sparser arrangement
        spec["items"] = _living(W, D, minimal=True)
        status = _validate(spec)
    spec["layout_status"] = status
    return spec


def _wrap(rt, W, D, H, door, items, brief):
    room = {"type": rt, "width_in": W, "depth_in": D, "ceiling_in": H,
            "wall_thk_in": 4.5, "floor_thk_in": 4.0, "door": door}
    # ข้อ 22 basis is ระยะดิ่ง (floor-to-floor) — pass it through when the brief
    # KNOWS it; never invent one (an absent value = an honest engine WARN).
    if brief.get("floor_to_floor_mm") is not None:
        room["floor_to_floor_mm"] = float(brief["floor_to_floor_mm"])
    return {
        "schema": "interior-ai/room-spec@0.1",
        "note": f"AUTO-LAYOUT DRAFT for a {rt} {brief['width_ft']}x{brief['depth_ft']}ft room - a designer refines this.",
        "room": room,
        "render": False,
        "items": items,
    }


def _living(W, D, minimal=False):
    margin = 6.0
    sd = 36.0
    sw = min(84.0, W - 48.0)                          # 24" side clearance each side
    sx = (W - sw) / 2.0
    sy = D - margin - sd                             # sofa back near the north wall
    items = [{"name": "sofa", "kind": "sofa", "x": sx, "y": sy, "w": sw, "d": sd, "h": 34}]

    # Everything past the sofa needs depth. If the room is too shallow the full
    # layout FAILs (coffee table out of bounds) -> generate() retries with
    # minimal=True, which must actually be SPARSER (sofa only) to rescue it.
    if not minimal:
        cd, cw = 22.0, min(42.0, sw * 0.55)          # coffee table 16" in front of the sofa
        cx = (W - cw) / 2.0
        cy = sy - 16.0 - cd
        items.append({"name": "coffee table", "kind": "coffee_table", "x": cx, "y": cy, "w": cw, "d": cd, "h": 18})

        # tv console on the south wall, OFFSET to clear the centered door swing
        dwn = 32.0
        dl = (W - dwn) / 2.0
        west, east = dl - margin, (W - margin) - (dl + dwn)
        if max(west, east) >= 30.0:
            if west >= east:
                tw, tx = min(72.0, west - 6.0), margin
            else:
                tw, tx = min(72.0, east - 6.0), dl + dwn + 6.0
            items.append({"name": "tv console", "kind": "tv_console", "x": tx, "y": margin, "w": tw, "d": 16.0, "h": 24})
        rw = min(96.0, W - 24.0)                      # rug under the seating group
        ry = max(cy - 6.0, margin)
        rd = min(96.0, D - 2 * margin, (sy + sd) - ry)
        items.append({"name": "rug", "kind": "rug", "x": (W - rw) / 2.0, "y": ry, "w": rw, "d": rd, "h": 1})
    return items


def _generic(W, D, kinds):
    """Fallback: lay the requested kinds along the south wall, non-overlapping."""
    items, cx, margin = [], 12.0, 12.0
    for k in kinds:
        w, d, h = _DEFAULT_SIZE.get(k, (36, 24, 30))
        if cx + w > W - 12:
            break
        items.append({"name": k.replace("_", " "), "kind": k, "x": cx, "y": margin, "w": float(w), "d": float(d), "h": float(h)})
        cx += w + 18.0
    return items


def _validate(spec):
    r = spec["room"]
    room = cc.room_from_spec(r)   # shared plumbing: rtype + floor-to-floor + door
    items = [cc.Item(it.get("name", it["kind"]), it["kind"], it["x"], it["y"], it["w"], it["d"])
             for it in spec["items"]]
    res = cc.check(room, items)
    fails = sum(1 for x in res if x["status"] == "FAIL")
    warns = sum(1 for x in res if x["status"] == "WARN")
    return "FAIL" if fails else ("REVIEW" if warns else "PASS")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("usage: python layout_gen.py <room_type> <width_ft> <depth_ft> [out.json]")
    brief = {"room_type": sys.argv[1], "width_ft": float(sys.argv[2]), "depth_ft": float(sys.argv[3])}
    spec = generate(brief)
    print(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"\n  layout_status = {spec['layout_status']}  ({len(spec['items'])} items)", file=sys.stderr)
    if len(sys.argv) > 4:
        with open(sys.argv[4], "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"  wrote {sys.argv[4]}", file=sys.stderr)
