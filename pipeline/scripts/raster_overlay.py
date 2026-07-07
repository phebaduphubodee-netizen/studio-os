"""
raster_overlay.py — the REQUIRED pre-owner surfacing step: paint the machine's ENTIRE read
(footprint box + facing arrow + kind + room boundary) over the TRUE PDF raster (the sheet the
owner actually sees), high-DPI, cropped per room + full — so a misread is something the owner
SCANS off a pre-drawn picture instead of HUNTS by reconstructing the read in his head.

Why this exists (2026-07-06 diagnosis): the 2D→3D read's recurring faults are SEMANTIC
(identity / facing / indoor-outdoor) — classes the placement gate structurally cannot verify,
so the owner is the sole verifier. This overlay is the machine's half of that deal: every
rebuild MUST emit it (the generator calls render_read_overlay and fails loudly if it can't),
and every piece is NUMBERED to match a pre-filled review checklist (review-read-vs-sheet.md)
that says exactly which reads are owner-signed (✓, gate-backed) vs hand-read (needs the eye).

Facing-arrow colour = provenance: GREEN = owner-signed (ledger-backed, a rebuild cannot
re-roll it, gate raises contradicts_signed on drift); ORANGE = hand-read (the exact class the
v3→v4 rebuild regressed — these are what the owner's scan is FOR).

    python raster_overlay.py <manifest.json> [out_base]

Manifest-driven like placement_gate.run: source_pdf / page / calibration / furnish[] are read
from the SAME manifest fields the gate uses, so overlay and gate can never disagree on the
coordinate frame. out_base defaults to 'review-read-vs-sheet' next to the manifest.

Pure logic (pieces / room_bbox / crops_for / resolve_calib / facing pieces / checklist) is
import-testable without a PDF; only render_read_overlay/main touch fitz+matplotlib.
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from placement_gate import _FACING_KINDS, footprint   # single source: the gate's own facing set + bbox math
from facing_reader import facing_from_rot              # cardinal letter for a rot, None if non-cardinal

DPI = 200
CROP_PAD = 350.0          # mm around a room crop, enough to show the wall context
# Box colours deliberately contain NO green and NO orange: those two are the PROVENANCE channel
# (arrows only). A green wardrobe box would false-train the scanning eye that green = signed.
KIND_COL = {"bed": "#d01010", "sofa": "#d01010", "armchair": "#c02050", "chair": "#c02050",
            "loveseat": "#c02050", "bench": "#8040a0",
            "side_table": "#7a5230", "console": "#7a5230",
            "tv_console": "#0090d0", "cabinet": "#0090d0",
            "wardrobe": "#405090", "headboard": "#405090",
            "vanity_double": "#00a0a0", "toilet": "#00a0a0", "bathtub": "#00a0a0",
            "shower": "#00a0a0"}
ARROW_SIGNED = "#00a020"   # owner-signed facing: ledger-backed, rebuild-proof
ARROW_HANDREAD = "#ff6a00" # hand-read facing: the class a rebuild can re-roll — scan these


def room_letter(idx):
    """Stable one-letter room prefix (A, B, C…) so badge ids are UNIQUE across rooms — badge
    'A5' can never collide with 'B5' on the full crop or bleed ambiguously into a neighbour."""
    return chr(65 + idx)


# ---------------------------------------------------------------- pure helpers (no fitz)
def pieces(spec):
    """Every placed piece of a room spec in a DETERMINISTIC order (builtins, items, subroom
    fixtures) with its group tag — the same order the checklist numbers, so badge N on the
    overlay IS row N in review-read-vs-sheet.md."""
    out = [("builtin", it) for it in spec.get("builtins", [])]
    out += [("loose", it) for it in spec.get("items", [])]
    for sr in spec.get("subrooms", []):
        out += [("fixture", it) for it in sr.get("fixtures", [])]
    return out


def room_bbox(spec, offset=(0, 0), pad=CROP_PAD):
    """Crop rect for a room = its outline bbox (∪ subroom outlines), padded. Derived from the
    spec — never hardcoded — so any project's rooms crop correctly. A spec with NO outline
    falls back to the union of its piece footprints (gate bbox math), so a hand-built/foreign
    spec still gets a crop instead of silently emitting nothing."""
    pts = list(spec.get("room", {}).get("outline_mm", []))
    for sr in spec.get("subrooms", []):
        pts += list(sr.get("outline_mm", []))
    xs = [p[0] + offset[0] for p in pts]
    ys = [p[1] + offset[1] for p in pts]
    if not pts:
        for _g, it in pieces(spec):
            try:
                x0, y0, x1, y1 = footprint(it, offset)
            except (KeyError, TypeError):
                continue
            xs += [x0, x1]
            ys += [y0, y1]
    if not xs:
        return None
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def crops_for(rooms, pad=CROP_PAD):
    """[(name, bbox)] = one crop per room + a 'full' union crop. rooms = [{id, spec, offset}]."""
    crops = []
    for r in rooms:
        bb = room_bbox(r["spec"], r.get("offset", (0, 0)), pad)
        if bb:
            crops.append((r["id"], bb))
    if crops:
        xs0, ys0, xs1, ys1 = zip(*[bb for _n, bb in crops])
        crops.append(("full", (min(xs0), min(ys0), max(xs1), max(ys1))))
    return crops


def resolve_calib(doc):
    """(scale, ox, oy) from the manifest 'calibration' field, else the shared plan_cluster
    defaults — the EXACT resolution placement_gate.run uses (line-for-line), so the overlay
    is drawn in the same frame the gate verified."""
    if isinstance(doc, dict) and "calibration" in doc:
        return tuple(doc["calibration"])
    from plan_cluster import SCALE, OX, OY   # lazy: keeps this module import-light
    return (SCALE, OX, OY)


def wants_arrow(it):
    """A facing arrow is drawn for the gate's facing kinds + ANY piece carrying an owner-signed
    facing (the generator applies a sign to any kind, so the overlay must show any kind)."""
    return it.get("kind") in _FACING_KINDS or it.get("facing_source") == "owner-signed"


def arrow_color(it):
    return ARROW_SIGNED if it.get("facing_source") == "owner-signed" else ARROW_HANDREAD


def _rot_gloss(rot):
    """'270 (หัน W)' for a cardinal rot, plain degrees for a non-cardinal one — the row becomes
    self-checkable without the owner translating machine-degrees in his head."""
    letter = facing_from_rot(rot)
    return f"{rot} (หัน {letter})" if letter else f"{rot}"


def checklist(rooms):
    """The pre-filled review checklist (markdown lines): every piece badged (A1, B3, …) to match
    the overlay, with the SEMANTIC reads the machine cannot verify spelled out per piece, and a
    READY-TO-PASTE sign stub per unsigned facing — so 'ถูกแล้ว' costs one paste, not JSON
    archaeology. That is the whole product thesis: the machine makes corrections (and
    confirmations) CHEAP; an orange row that stays orange forever is a per-rebuild cost."""
    lines = ["# REVIEW — machine read vs true sheet (สแกน overlay แล้ว ยืนยัน/แก้ทีละแถว)",
             "",
             "- ลูกศร**เขียว** = เจ้าของเซ็นแล้ว (อยู่ใน ledger — rebuild ทอยใหม่ไม่ได้, gate จับถ้าเบี่ยง)",
             "- ลูกศร**ส้ม** = hand-read ยังไม่เซ็น — จุดที่ต้องใช้ตาดู (ถูกแล้วก็เซ็นได้เลย ↓ จะได้เขียวถาวร)",
             "- เส้นประ**น้ำเงิน** = ขอบเขตห้องที่เครื่องอ่าน — เถียงได้ (เช่น แนวประตูกระจก / เขตใน-นอก)",
             "- ชิ้นที่**วาดในแบบแต่ไม่มีกรอบสี** = เครื่องอ่านไม่เห็น (ตกหล่น เคสแบบ BF09-2) — ชี้ตำแหน่งบอกได้เลย",
             ""]
    stubs = []
    kind_stubs = []
    for ri, r in enumerate(rooms):
        L = room_letter(ri)
        lines.append(f"## {L} — {r['id']}")
        lines.append("")
        lines.append("| badge | ชิ้น | kind (identity = human call) | rot | facing |")
        lines.append("|-------|------|------|-----|--------|")
        for i, (group, it) in enumerate(pieces(r["spec"]), 1):
            rot = it.get("rot", 0)
            if it.get("facing_source") == "owner-signed":
                fac = "✓ owner-signed"
            elif wants_arrow(it):
                fac = "● hand-read — ตรวจ/เซ็น"
                stubs.append((f"{L}{i}", r["id"], it))
            else:
                fac = "–"
            kind_cell = f"{it.get('kind', '?')} ({group})"
            if it.get("kind_source") == "owner-signed":
                kind_cell += " ✓ owner-signed"
            elif group == "loose":
                # only LOOSE pieces consult the ledger (builtins/fixtures never do — a sign aimed
                # at one ORPHANS the generate), so only loose rows get a paste-ready kind stub.
                kind_stubs.append((f"{L}{i}", r["id"], it))
            lines.append(f"| {L}{i} | {it.get('name', '?')} | {kind_cell} "
                         f"| {_rot_gloss(rot)} | {fac} |")
        lines.append("")
    if stubs:
        lines.append("## เซ็น facing (แถวส้ม) — ถูกแล้ว = วาง stub ตามเดิม / ผิด = แก้ `rot` ก่อนวาง")
        lines.append("")
        lines.append("วางลง `confirmed[]` ใน `placement-review.json` แล้ว regenerate — rebuild จะ "
                     "re-apply ค่านี้แทนการทอยใหม่; orphan gate จะ FAIL ถ้าลายเซ็นหลุดจากชิ้น:")
        lines.append("")
        for badge, room_id, it in stubs:
            stub = {"room": room_id, "name": it.get("name"), "rot": it.get("rot", 0),
                    "w": it.get("w"), "d": it.get("d"),
                    "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
            lines.append(f"**{badge}** — {it.get('name', '?')}:")
            lines.append("```json")
            lines.append(json.dumps(stub, ensure_ascii=False))
            lines.append("```")
            lines.append("")
    if kind_stubs:
        lines.append("## เซ็น kind (identity, แถว loose) — ถูกแล้ว = วาง stub ตามเดิม / ผิด = แก้ค่า `kind` ก่อนวาง")
        lines.append("")
        lines.append("วางลง `confirmed[]` ใน `placement-review.json` แล้ว regenerate — identity จะติดถาวร "
                     "(rebuild เปลี่ยนเองไม่ได้, gate ยก contradicts_signed_kind ถ้าเบี่ยง). วางเฉพาะแถวที่ "
                     "ตรวจด้วยตาแล้วจริง; แก้ทีหลัง = APPEND entry ใหม่ชื่อ+ขนาดเดิม (ตัวหลังชนะ):")
        lines.append("")
        for badge, room_id, it in kind_stubs:
            stub = {"room": room_id, "name": it.get("name"), "kind": it.get("kind"),
                    "w": it.get("w"), "d": it.get("d"),
                    "by": "owner (ระบุวิธียืนยัน)", "date": "YYYY-MM-DD"}
            lines.append(f"**{badge}** — {it.get('name', '?')}:")
            lines.append("```json")
            lines.append(json.dumps(stub, ensure_ascii=False))
            lines.append("```")
            lines.append("")
    lines.append("หมายเหตุ identity: คอลัมน์ kind เซ็นเข้า ledger ได้แล้ว (confirmed_kind) — วาง stub "
                 "จากส่วน 'เซ็น kind' ข้างบน; แก้ทีหลัง = APPEND entry ใหม่ (ชื่อ+ขนาดเดิม, ตัวหลังชนะ). "
                 "ชิ้น builtin/fixture ไม่มี stub (generator ไม่ apply sign) — แก้ identity ของพวกนั้น = "
                 "บอกเลข badge + ชนิดที่ถูก แล้วเราแก้ generator ให้")
    return lines


# ---------------------------------------------------------------- render (fitz/matplotlib)
def render_read_overlay(pdf, page, calib, rooms, out_base, dpi=DPI):
    """Paint every room's read over the true sheet and write <out_base>_<room>.png per room +
    <out_base>_full.png + the numbered checklist <out_base>.md. rooms = [{id, spec, offset}]
    with IN-MEMORY spec dicts (the generator passes what it just built — no re-read race).
    Returns the list of written paths. Raises on any failure: this artifact is REQUIRED —
    a rebuild without its overlay is a rebuild the owner cannot scan."""
    import fitz
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import FancyArrow, Polygon

    # Thai-capable font so titles/kind labels render readable, not tofu (same fallback chain
    # as gen_floor2_v4_keyplan; harmless no-op on a machine without these fonts).
    for _fp in (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\LeelawUI.ttf",
                r"C:\Windows\Fonts\upcjl.ttf"):
        if os.path.exists(_fp):
            try:
                font_manager.fontManager.addfont(_fp)
                plt.rcParams["font.family"] = font_manager.FontProperties(fname=_fp).get_name()
                break
            except Exception:
                pass

    scale, ox, oy = calib
    doc = fitz.open(pdf)
    p = doc[page]
    pix = p.get_pixmap(dpi=dpi)
    import numpy as np
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    zoom = dpi / 72.0
    wpt, hpt = pix.width / zoom, pix.height / zoom
    ext = [(0 - ox) * scale, (wpt - ox) * scale, (oy - hpt) * scale, (oy - 0) * scale]

    def draw(ax, only=None):
        # A per-room crop (only=<room id>) draws ONLY that room: matplotlib text bleeding in
        # from a neighbour room would carry ITS badge numbers into this crop and break the
        # "badge = checklist row" contract. The full crop draws everything; its badges stay
        # unambiguous because every badge is room-letter-prefixed (A5 vs B5).
        ax.imshow(img, extent=ext, origin="upper", aspect="equal", zorder=0)
        for ri, r in enumerate(rooms):
            if only is not None and r["id"] != only:
                continue
            L = room_letter(ri)
            offx, offy = r.get("offset", (0, 0))
            # the machine's ROOM-BOUNDARY read (itself a semantic call — v4's sliding-door
            # lesson) drawn dashed so the owner can dispute the boundary, not just the pieces
            for poly_pts, style in ([(r["spec"].get("room", {}).get("outline_mm"), "--")] +
                                    [(sr.get("outline_mm"), ":") for sr in r["spec"].get("subrooms", [])]):
                if poly_pts:
                    pts = [(px + offx, py + offy) for px, py in poly_pts]
                    ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor="#2050c0",
                                         lw=1.2, ls=style, alpha=0.65, zorder=3))
            for i, (group, it) in enumerate(pieces(r["spec"]), 1):
                w, d, rot = it["w"], it["d"], it.get("rot", 0)
                cx, cy = it["x"] + w / 2 + offx, it["y"] + d / 2 + offy
                col = KIND_COL.get(it.get("kind"), "#606060")
                a = math.radians(rot)
                ca, sa = math.cos(a), math.sin(a)
                corners = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
                pts = [(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in corners]
                ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor=col, lw=2.0, zorder=5))
                if wants_arrow(it):
                    fx, fy = math.sin(a), -math.cos(a)       # front = -Y rotated by rot
                    alen = 0.3 * min(w, d) + 200             # NOT 'L' — that's the room letter
                    ax.add_patch(FancyArrow(cx, cy, fx * alen, fy * alen, width=25, head_width=160,
                                            head_length=140, color=arrow_color(it), zorder=6,
                                            length_includes_head=True))
                # clip_on: text is NOT axes-clipped by default -> the other rooms' labels would
                # escape a per-room crop and wreck the whole figure layout
                ax.text(cx, cy + d / 2 + 60, it.get("kind", "?"), ha="center", va="bottom",
                        fontsize=6, color=col, zorder=7, clip_on=True)
                ax.text(pts[3][0], pts[3][1], f"{L}{i}", ha="center", va="center", fontsize=7,
                        color="white", zorder=8, fontweight="bold", clip_on=True,
                        bbox=dict(boxstyle="round,pad=0.2", fc=col, ec="none"))

    crops = crops_for(rooms)
    if not crops:
        raise SystemExit("raster_overlay: no crops derivable (no room outlines and no placeable "
                         "pieces) — the REQUIRED read-vs-sheet overlay cannot be produced")
    written = []
    for name, (x0, y0, x1, y1) in crops:
        fig, ax = plt.subplots(figsize=(max(4.0, (x1 - x0) / 500.0),
                                        max(4.0, (y1 - y0) / 500.0)), dpi=150)
        draw(ax, only=None if name == "full" else name)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_title(f"READ vs TRUE SHEET — {name}  (badge = แถวใน checklist; "
                     f"ลูกศรเขียว = เซ็นแล้ว, ส้ม = hand-read ตรวจด้วยตา; เส้นประ = ขอบเขตที่เครื่องอ่าน)",
                     fontsize=9)
        fig.tight_layout()
        out = f"{out_base}_{name}.png"
        fig.savefig(out, dpi=150)
        plt.close(fig)
        written.append(out)
    md = out_base + ".md"
    with open(md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(checklist(rooms)) + "\n")
    written.append(md)
    return written


def _resolve(path, base):
    """A manifest stores repo-relative paths; resolve against cwd, then the manifest dir, then
    (gate parity — placement_gate.run does exactly this) the file's BASENAME next to the
    manifest, so the CLI also works when run from inside the manifest's own directory."""
    for cand in (path, os.path.join(base, path), os.path.join(base, os.path.basename(path))):
        if os.path.exists(cand):
            return cand
    raise SystemExit(f"raster_overlay: cannot resolve {path!r} (tried cwd, manifest-relative, "
                     f"and basename beside the manifest)")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    man_path = sys.argv[1]
    man_dir = os.path.dirname(os.path.abspath(man_path))
    doc = json.load(open(man_path, encoding="utf-8"))
    pdf = _resolve(doc["source_pdf"], man_dir)
    page = doc.get("page", 1)
    calib = resolve_calib(doc)
    rooms = []
    for f in doc.get("furnish", []):
        spec = json.load(open(_resolve(f["spec"], man_dir), encoding="utf-8"))
        rooms.append({"id": f["id"], "spec": spec, "offset": tuple(f.get("offset_mm", (0, 0)))})
    if not rooms:
        raise SystemExit("raster_overlay: manifest has no furnish[] rooms")
    out_base = sys.argv[2] if len(sys.argv) > 2 else os.path.join(man_dir, "review-read-vs-sheet")
    print(f"overlay calibration: scale={calib[0]} ox={calib[1]} oy={calib[2]}  page={page}")
    for w in render_read_overlay(pdf, page, calib, rooms, out_base):
        print("wrote", w)


if __name__ == "__main__":
    main()
