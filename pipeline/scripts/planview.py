"""planview.py — LOOK AT IT FROM ABOVE. Pure PIL, no bpy.

    python pipeline/scripts/planview.py --boxes boxes.json --out plan.png

CLI-ONLY: the builder runs it at the START of every reproduction round, from the
lane's own driver (e.g. training/TRN-003_3dshaker-kitchen/03_blockout/make_plan.py),
before any render. It draws rather than judges, so it has no place inside a pure
rule module — but the ARTEFACT is not optional: `rule_gate.audit_planview` fails a
lane that has a blockout and no plan newer than it. Owner order 2026-08-29,
"PLAN VIEW เป็น output บังคับของทุกรอบทำซ้ำ".

WHY THIS FILE EXISTS
--------------------
2026-08-29, TRN-003. The owner said the island looked laid the wrong way. The
builder answered with a number confirming its own model, and he had to say it a
second time — *"ผมเห็นว่าไอแลนมันชี้ประมาณเข้าหากล้อง"* — before it turned out the
island was a full quarter turn out.

**In plan it takes a quarter of a second.** A 3072 x 1250 slab lying across the
room instead of along the wall is not a subtle reading; it is the difference
between a rectangle that is tall and a rectangle that is wide. The reason nobody
saw it for a day is that nobody ever drew one. Every image this lane produced was
a perspective frame from the one camera the plate was shot from, and in that view
the island's near end is 3 m closer than its far end, every edge of it converges,
and its long axis runs almost exactly along the line of sight — the single
direction in which perspective encodes an angle worst.

That is not local bad luck. The spatial-reasoning literature is blunt about it:
models "struggle to correctly predict changes in relative position, ORIENTATION,
and visibility when the egocentric viewpoint shifts", performance collapses on
non-canonical orientations, and — the cheapest sentence in the whole field —
**rotation tasks are defined relative to a TOP-DOWN VIEW.** The canonical frame
for the question "which way is it laid" is the plan, and this studio, which makes
interiors for a living, had no plan.

WHAT IT DRAWS, and why each piece is here
-----------------------------------------
* Every mass as its footprint, from the SAME numbers the build consumes. Not a
  redrawn plan: a redrawn plan is a second derivation that can disagree with the
  first, and R12 already cost this repo three weeks on exactly that.
* THE LONG AXIS of every mass, as an arrow with its heading in degrees. A footprint
  already shows orientation; the arrow makes a quarter turn unmissable, and the
  printed heading is the same number `pose_check.py` compares.
* THE CAMERA and its frustum. His sentence was "it points at the camera" — that is
  a relation between two things, and a picture that contains only one of them
  cannot show it.
* NAMED GAPS with their millimetres. The walkway that was NEGATIVE 420 mm — two
  solids in the same place — is a line you cannot draw without noticing.

WHAT IT IS NOT. It is not a construction drawing and carries no title block,
no annotation standard, no line weights. It is an INSTRUMENT: the cheapest
question in the ladder, asked before anything expensive runs.
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont


BG = (250, 249, 246)
GRID = (226, 222, 214)
GRID_MAJOR = (204, 198, 188)
INK = (38, 38, 38)
FILL = (214, 222, 231)
EDGE = (92, 112, 138)
AXIS = (196, 62, 42)
CAM = (32, 132, 96)
BAD = (200, 40, 40)
WARN_C = (204, 140, 20)
OK_C = (40, 140, 70)


# THAI FIRST. The client lane names every mass in Thai, and `arial.ttf` has no Thai
# glyphs — the first DELIV-001 plan came out with eleven rows of tofu boxes. A
# drawing whose labels cannot be read is a drawing nobody opens twice, and this one
# exists to be opened before anything expensive runs.
FONTS = ("leelawui.ttf", "tahoma.ttf", "segoeui.ttf",
         "NotoSansThai-Regular.ttf", "arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc")


def _font(size):
    for name in FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _label(d, xy, text, font, fill):
    """Text with a background plate. A plan whose labels are unreadable over the
    thing they name is a picture nobody opens twice."""
    x, y = xy
    try:
        x0, y0, x1, y1 = d.textbbox((x, y), text, font=font)
    except AttributeError:                       # very old PIL
        x0, y0, x1, y1 = x, y, x + 7 * len(text), y + 12
    d.rectangle([x0 - 3, y0 - 2, x1 + 3, y1 + 2], fill=BG)
    d.text((x, y), text, font=font, fill=fill)


def _corners(b):
    """Footprint corners in mm. An AABB, or a rectangle rotated about its centre."""
    if b.get("poly"):
        return [(float(x), float(y)) for x, y in b["poly"]]
    x0, y0, x1, y1 = float(b["x0"]), float(b["y0"]), float(b["x1"]), float(b["y1"])
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    rot = float(b.get("rot_deg", 0.0))
    if abs(rot) < 1e-9:
        return pts
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + (px - cx) * c - (py - cy) * s,
             cy + (px - cx) * s + (py - cy) * c) for px, py in pts]


def long_axis(b):
    """(heading_deg, length_mm, width_mm, centre) of the footprint's long side.

    THE HEADING IS THE NUMBER pose_check COMPARES, computed here from the same
    corners that get drawn — so the arrow in the picture and the row in the gate
    cannot drift apart. A square footprint has no long side; it returns None
    rather than picking one, for the same reason pose_check refuses `fold: 0`:
    an object with no distinguishable axis has no orientation to report, and
    reporting one anyway is a measurement nobody made.
    """
    pts = _corners(b)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    best = None
    for i in range(len(pts)):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % len(pts)]
        L = math.hypot(bx - ax, by - ay)
        if best is None or L > best[0]:
            best = (L, math.degrees(math.atan2(by - ay, bx - ax)) % 180.0)
    # the OTHER side, for squareness
    other = min(math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0],
                           pts[(i + 1) % len(pts)][1] - pts[i][1])
                for i in range(len(pts)))
    if best[0] <= 0 or other <= 0:
        return None
    if best[0] / other < 1.05:
        return None                      # square in plan: no long axis to name
    return best[1], best[0], other, (cx, cy)


class Plan:
    def __init__(self, bounds, px_w=1500, margin=70):
        x0, y0, x1, y1 = bounds
        self.bx, self.by = x0, y0
        span_x, span_y = max(1.0, x1 - x0), max(1.0, y1 - y0)
        self.k = (px_w - 2 * margin) / span_x
        self.m = margin
        self.W = px_w
        self.H = int(span_y * self.k + 2 * margin)
        self.span_y = span_y
        self.img = Image.new("RGB", (self.W, self.H), BG)
        self.d = ImageDraw.Draw(self.img)

    def p(self, x, y):
        """mm -> pixels. +Y in the world goes UP the page, as a plan does."""
        return (self.m + (x - self.bx) * self.k,
                self.H - self.m - (y - self.by) * self.k)

    def grid(self, step=1000.0):
        x = math.floor(self.bx / step) * step
        while x < self.bx + self.W / self.k:
            major = abs((x / step) % 5) < 1e-6
            px = self.p(x, self.by)[0]
            self.d.line([(px, 0), (px, self.H)], fill=GRID_MAJOR if major else GRID)
            x += step
        y = math.floor(self.by / step) * step
        while y < self.by + self.span_y + step:
            major = abs((y / step) % 5) < 1e-6
            py = self.p(self.bx, y)[1]
            self.d.line([(0, py), (self.W, py)], fill=GRID_MAJOR if major else GRID)
            y += step


def draw(boxes, out, camera=None, gaps=(), title="", px_w=1500):
    # THE SHEET IS SIZED BY THE MASSES, NOT BY THE CAMERA. This lane's camera stands
    # 5.3 m beyond the back of the room; including it in the extent shrank everything
    # being judged into one corner of the page. A drawing whose subject is small
    # because of something outside the subject is the same defect as a crop box
    # nobody measured — so the camera is CLAMPED to the margin when it falls off
    # sheet, and the distance it was clamped by is printed rather than hidden.
    xs, ys = [], []
    for b in boxes:
        for x, y in _corners(b):
            xs.append(x)
            ys.append(y)
    pad = 500.0
    bounds = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    pl = Plan(bounds, px_w=px_w)
    pl.grid()
    d, f, fs = pl.d, _font(15), _font(12)

    if camera:
        cx, cy = float(camera["x"]), float(camera["y"])
        head = float(camera.get("heading_deg", 90.0))
        fov = float(camera.get("fov_deg", 40.0))
        bx0, by0, bx1, by1 = bounds
        off = math.hypot(max(0.0, bx0 - cx, cx - bx1), max(0.0, by0 - cy, cy - by1))
        mx = min(max(cx, bx0 + 200), bx1 - 200)
        my = min(max(cy, by0 + 200), by1 - 200)
        reach = math.hypot(bx1 - bx0, by1 - by0)
        for s in (-1, 1):
            a = math.radians(head + s * fov / 2.0)
            d.line([pl.p(mx, my), pl.p(mx + reach * math.cos(a), my + reach * math.sin(a))],
                   fill=CAM, width=1)
        a = math.radians(head)
        d.line([pl.p(mx, my), pl.p(mx + reach * 0.30 * math.cos(a),
                                   my + reach * 0.30 * math.sin(a))], fill=CAM, width=3)
        px, py = pl.p(mx, my)
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=CAM)
        tag = f"camera  {head:.1f}°"
        if off > 1.0:
            tag += f"  ({off / 1000.0:.1f} m off sheet, shown on the margin)"
        _label(d, (px + 12, py - 8), tag, f, CAM)

    placed = []
    for b in boxes:
        pts = [pl.p(x, y) for x, y in _corners(b)]
        d.polygon(pts, fill=b.get("fill") and tuple(b["fill"]) or FILL, outline=EDGE)
        la = long_axis(b)
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        label = b.get("name", "")
        if la:
            head, L, wid, (wx, wy) = la
            a = math.radians(head)
            hx, hy = pl.p(wx + L * 0.42 * math.cos(a), wy + L * 0.42 * math.sin(a))
            tx, ty = pl.p(wx - L * 0.42 * math.cos(a), wy - L * 0.42 * math.sin(a))
            d.line([(tx, ty), (hx, hy)], fill=AXIS, width=2)
            for s in (150, -150):
                ah = math.radians(head + 180 + s / 10.0)
                d.line([(hx, hy), (hx + 11 * math.cos(ah), hy - 11 * math.sin(ah))],
                       fill=AXIS, width=2)
            label += f"  {L:.0f}x{wid:.0f}  {head:.1f} deg"
        else:
            label += "  (no long axis in plan)"
        lx, ly = cx + 6, cy - 8
        for _ in range(14):                     # nudge off any label already placed
            if not any(abs(lx - px) < 190 and abs(ly - py) < 15 for px, py in placed):
                break
            ly += 17
        placed.append((lx, ly))
        _label(d, (lx, ly), label, fs, INK)

    for g in gaps:
        (ax, ay), (bx, by) = g["a"], g["b"]
        mm = g.get("mm")
        col = {"FAIL": BAD, "WARN": WARN_C, "PASS": OK_C}.get(g.get("verdict"), INK)
        d.line([pl.p(*g["a"]), pl.p(*g["b"])], fill=col, width=3)
        mx, my = pl.p((ax + bx) / 2.0, (ay + by) / 2.0)
        txt = g.get("label") or (f"{mm:.0f} mm" if mm is not None else "")
        _label(d, (mx, my - 24), txt, f, col)

    # scale bar: 1 m
    sx, sy = pl.m, pl.H - 26
    d.line([(sx, sy), (sx + 1000 * pl.k, sy)], fill=INK, width=3)
    d.text((sx + 1000 * pl.k + 8, sy - 8), "1 m", font=f, fill=INK)
    if title:
        d.text((pl.m, 18), title, font=_font(19), fill=INK)
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    pl.img.save(out)
    return out


SHELL_TOKENS = ("floor", "ceil", "wall", "soffit", "slab", "bulkhead")


def boxes_from_spec(spec, drop_shell=True, min_mm=1.0):
    """A build spec's `masses` -> plan boxes. Centre `c` + size `s`, in mm.

    Shell masses (floor, ceiling, walls) are dropped by default for one reason
    only: they set the drawing extent to the whole room and shrink every object
    being judged into a corner. That is the same defect as a crop box nobody
    measured, and it is stated here rather than hidden behind a name.
    """
    out = []
    # THE CANONICAL ROOM-SPEC SCHEMA (added 2026-09-02, P2r-38). `masses` is the
    # REPRODUCTION lane's shape; the client lane (PRJ-*/03_layout/*.CANONICAL.spec.json)
    # carries `builtins` + `items` with corner x/y + w/d instead. Until this branch the
    # rung above printed "ONE COMMAND CLEARS IT" and named a command that exited 2 with
    # "no drawable masses" on every client spec in the repo — a guard whose stated
    # remedy did not run on the lane it fires at, which is the same defect class as a
    # rule with no reader. Corner+size here, centre+size there; both end as x0y0x1y1.
    for m in list(spec.get("builtins", [])) + list(spec.get("items", [])):
        n = m.get("name") or ""
        try:
            x, y = float(m["x"]), float(m["y"])
            w, d = float(m["w"]), float(m["d"])
        except (KeyError, TypeError, ValueError):
            continue
        if min(abs(w), abs(d)) < min_mm:
            continue
        if drop_shell and any(k in n.lower() for k in SHELL_TOKENS):
            continue
        out.append(dict(name=n, x0=min(x, x + w), y0=min(y, y + d),
                        x1=max(x, x + w), y1=max(y, y + d)))
    for m in spec.get("masses", []):
        n = m.get("name") or ""
        c, sz = m.get("c"), m.get("s")
        if not (isinstance(c, (list, tuple)) and isinstance(sz, (list, tuple))):
            continue
        if len(c) < 2 or len(sz) < 2:
            continue
        if min(abs(float(sz[0])), abs(float(sz[1]))) < min_mm:
            continue
        # SUBSTRING, not startswith. The first version prefix-matched and kept
        # `back_wall`, `left_wall`, `right_wall` and `ceil_main` — every shell
        # mass in the lane it was written for. A filter that names the objects it
        # applies to will always miss the next one (R9b), so the tokens are
        # matched wherever they appear in the name, and `--keep-shell` is there
        # for the case where the shell IS the subject.
        if drop_shell and any(k in n.lower() for k in SHELL_TOKENS):
            continue
        hx, hy = abs(float(sz[0])) / 2.0, abs(float(sz[1])) / 2.0
        out.append(dict(name=n, x0=float(c[0]) - hx, y0=float(c[1]) - hy,
                        x1=float(c[0]) + hx, y1=float(c[1]) + hy))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boxes", default="",
                    help="JSON: {title, camera:{x,y,heading_deg,fov_deg}, "
                         "boxes:[{name,x0,y0,x1,y1[,rot_deg][,poly]}], gaps:[...]}")
    ap.add_argument("--spec", default="",
                    help="a build spec — draws its `masses` directly. This is the "
                         "one-command answer to rule_gate's plan-view rung.")
    ap.add_argument("--keep-shell", action="store_true",
                    help="keep floor/ceiling/wall masses (they set the extent)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not (a.boxes or a.spec):
        print("give --boxes or --spec", file=sys.stderr)
        return 2
    if a.spec:
        raw = json.loads(open(a.spec, encoding="utf-8").read())
        spec = {"boxes": boxes_from_spec(raw, drop_shell=not a.keep_shell),
                "title": os.path.basename(a.spec)}
        if not spec["boxes"]:
            print(f"no drawable masses in {a.spec} — a plan of nothing is not a plan",
                  file=sys.stderr)
            return 2
    else:
        spec = json.loads(open(a.boxes, encoding="utf-8").read())
    p = draw(spec.get("boxes", []), a.out, camera=spec.get("camera"),
             gaps=spec.get("gaps", []), title=spec.get("title", ""))
    print(f"PLAN: {p}")
    for b in spec.get("boxes", []):
        la = long_axis(b)
        if la:
            print(f"  {b.get('name','?'):16s} heading {la[0]:6.1f}°  "
                  f"{la[1]:.0f} x {la[2]:.0f} mm")


if __name__ == "__main__":
    sys.exit(main() or 0)
