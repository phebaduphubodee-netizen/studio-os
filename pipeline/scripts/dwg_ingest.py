"""

CLI-ONLY: run by hand on every DXF/DWG ingest (sheet-first lane); the reachability checker names this module as its own declaration example — triage 2026-08-25.
dwg_ingest.py — INTERIOR-AI DWG/DXF ingest (read the friend's real CAD files).

The friend works in CAD; her deliverables arrive as DWG (AutoCAD binary). ezdxf cannot
read DWG directly, so this tool converts DWG -> DXF. Reader hierarchy by LICENSE
(verified — knowledge/_inbox/interior-ai/2026-07-01-plan-read-write-tools-DR.md §2/§7a):
  * .dxf -> ezdxf directly (MIT) — COMMERCIAL-CLEAN. Preferred input: have the friend
            export DXF from CAD and the licensing question disappears entirely.
  * .dwg -> GNU LibreDWG `dwg2dxf` (GPL-3) if installed — commercial-SAFE as a back-office
            CLI (its copyleft stays inside the converter and never touches our output).
            Auto-preferred over ODA whenever present. ($INTERIOR_LIBREDWG overrides the path.)
  * .dwg -> ODA File Converter FALLBACK — ⚠️ the ODA Community User Agreement licenses it for
            NON-COMMERCIAL use only (non-members). Loudly warned; never ship a paid deliverable
            built off this path. Fix: export to DXF, or install commercial-safe LibreDWG.

It is a READER, not a spec-builder: it converts, detects the drawing UNIT (so nothing is
ever mis-scaled — the 0.0254x / cm-vs-mm trap), and reports what the file contains
(layers, the TEXT schedule incl. BF built-in codes, furniture/fixture block insert points
in millimetres, dimensions) + renders the plan to PNG. Turning that into a room-spec@0.2 is
a deliberate, human-verified step (a real architectural DWG merges walls/furniture across
many layers and the room boundary is a design judgment — auto-tracing risks fabricating
coordinates, which this project must not do).

    python pipeline/dwg_ingest.py <file.dwg|file.dxf> [--render] [--window x0 x1 y0 y1]

Outputs to output/dwg_converted/: <name>.dxf (cached) + <name>*.png (if --render).
Needs ezdxf; a DWG also needs LibreDWG (commercial-safe) or the ODA converter (non-commercial);
matplotlib for --render.
"""
import glob
import os
import sys
from collections import Counter, defaultdict

try:  # so the license WARNING (stderr) + Thai/emoji output don't mojibake on a cp-console
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import ezdxf
except ImportError:
    sys.exit("dwg_ingest needs ezdxf -> pip install ezdxf")

HERE = os.path.dirname(os.path.abspath(__file__))

# $INSUNITS code -> millimetres-per-unit. The whole point: never trust a coordinate
# until the unit is known (a 6500 mm room is 650 units in cm, 6500 in mm, 6.5 in m).
_UNIT_MM = {1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0, 8: 25400.0}
_UNIT_NAME = {0: "unitless", 1: "inch", 2: "foot", 4: "mm", 5: "cm", 6: "m", 8: "mile"}


def find_oda():
    """Locate ODAFileConverter.exe even if it is not on PATH (winget installs it under
    Program Files\\ODA\\ODAFileConverter <ver>\\). $INTERIOR_ODA overrides."""
    env = os.environ.get("INTERIOR_ODA")
    if env and os.path.exists(env):
        return env
    pats = [
        r"C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe",
        r"C:\Program Files (x86)\ODA\ODAFileConverter*\ODAFileConverter.exe",
        "/usr/bin/ODAFileConverter", "/usr/local/bin/ODAFileConverter",
    ]
    hits = []
    for p in pats:
        hits.extend(glob.glob(p))
    hits = sorted((h for h in hits if os.path.exists(h)), reverse=True)
    return hits[0] if hits else None


def find_libredwg():
    """Locate GNU LibreDWG's `dwg2dxf` (the commercial-SAFE GPL-3 DWG reader). $INTERIOR_LIBREDWG
    overrides. Not installed by default on Windows — build via MSYS2
    (`pacman -S mingw-w64-x86_64-libredwg`) or drop in a prebuilt binary; once present it is
    auto-preferred over ODA and no code change is needed."""
    from shutil import which
    env = os.environ.get("INTERIOR_LIBREDWG")
    if env and os.path.exists(env):
        return env
    exe = which("dwg2dxf") or which("dwg2dxf.exe")
    if exe:
        return exe
    pats = [
        r"C:\msys64\mingw64\bin\dwg2dxf.exe",
        r"C:\Program Files\LibreDWG\bin\dwg2dxf.exe",
        r"C:\Program Files\libredwg*\dwg2dxf.exe",
        "/usr/bin/dwg2dxf", "/usr/local/bin/dwg2dxf",
    ]
    hits = []
    for p in pats:
        hits.extend(glob.glob(p))
    hits = sorted((h for h in hits if os.path.exists(h)), reverse=True)
    return hits[0] if hits else None


def _dwg_to_dxf_libredwg(exe, path, out_dxf):
    """Convert DWG -> DXF with LibreDWG (`dwg2dxf`), a back-office CLI. Its GPL-3 copyleft
    covers only this converter process, never the drawings we output. Returns out_dxf on
    success else None. ⚠️ UNTESTED against the friend's real DWG until LibreDWG is installed —
    the DR gates 'retire ODA' on a capability test vs the ODA output (flag count/layers/BF
    schedule); this only wires the path so the swap is one install away."""
    import subprocess
    try:
        r = subprocess.run([exe, "-y", "-o", out_dxf, path],
                           capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and os.path.exists(out_dxf) and os.path.getsize(out_dxf) > 0:
            return out_dxf
        # some builds ignore -o and emit <name>.dxf in the cwd -> relocate it.
        alt = os.path.splitext(os.path.basename(path))[0] + ".dxf"
        if os.path.exists(alt) and os.path.abspath(alt) != os.path.abspath(out_dxf):
            os.replace(alt, out_dxf)
            return out_dxf
    except Exception:
        pass
    return None


# Reader hierarchy by LICENSE (verified — DR §2/§7a). DXF = commercial-clean; LibreDWG =
# commercial-safe back-office CLI; ODA = NON-COMMERCIAL for non-members (last resort, warned).
def load(path, verbose=True):
    """Return an ezdxf Document. DXF is read directly (clean); a DWG is converted via
    LibreDWG when available (commercial-safe) else ODA (non-commercial — warns loudly)."""
    if path.lower().endswith(".dxf"):
        if verbose:
            print("  reader: ezdxf (DXF, MIT) — commercial-clean")
        return ezdxf.readfile(path)

    # DWG: prefer the commercial-safe LibreDWG reader when it is installed.
    lib = find_libredwg()
    if lib:
        out_dxf = os.path.join(_outdir(),
                               os.path.splitext(os.path.basename(path))[0] + ".libredwg.dxf")
        conv = _dwg_to_dxf_libredwg(lib, path, out_dxf)
        if conv:
            if verbose:
                print(f"  reader: LibreDWG dwg2dxf (GPL-3, back-office) — commercial-safe  [{lib}]")
            return ezdxf.readfile(conv)
        if verbose:
            sys.stderr.write(f"  ⚠️ LibreDWG found ({lib}) but conversion failed — falling back to ODA.\n")

    # Fallback: ODA File Converter — non-commercial-only for non-members.
    exe = find_oda()
    if not exe:
        sys.exit(
            "DWG needs a converter. COMMERCIAL-SAFE options: export the file to DXF from CAD "
            "(ezdxf reads DXF directly, license-clean), or install GNU LibreDWG's dwg2dxf "
            "(set $INTERIOR_LIBREDWG). NON-COMMERCIAL only: `winget install ODA.ODAFileConverter`.")
    if verbose:
        sys.stderr.write(
            "  ⚠️ LICENSE WARNING: reading this DWG via the ODA File Converter, which the ODA\n"
            "     Community User Agreement licenses for NON-COMMERCIAL use only (non-members).\n"
            "     Do NOT ship a paid deliverable built off this path. Commercial-safe fix: export\n"
            "     to DXF, or install GNU LibreDWG. (verified: DR §2, plan-read-write-tools)\n")
    from ezdxf.addons import odafc
    try:
        ezdxf.options.set("odafc-addon", "win_exec_path", exe)
    except Exception:
        pass
    return odafc.readfile(path)


def unit_mm(doc):
    """(mm_per_unit, source) — header $INSUNITS if set, else infer from dimension sizes."""
    ins = doc.header.get("$INSUNITS", 0)
    if ins in _UNIT_MM:
        return _UNIT_MM[ins], f"$INSUNITS={ins} ({_UNIT_NAME.get(ins,'?')})"
    # fallback: median dimension measurement -> guess (rooms are ~1000s of mm)
    meas = []
    for e in doc.modelspace():
        if e.dxftype() == "DIMENSION":
            try:
                meas.append(abs(e.get_measurement()))
            except Exception:
                pass
    if meas:
        med = sorted(meas)[len(meas) // 2]
        # a wall/room dim ~ 100s-1000s of real mm; if median < 1000 the unit is likely cm
        return (10.0, f"inferred cm (median dim {med:.0f})") if med < 1000 else (1.0, f"inferred mm (median dim {med:.0f})")
    return 1.0, "assumed mm (no $INSUNITS, no dimensions)"


def _pts(e):
    t = e.dxftype()
    if t == "LWPOLYLINE":
        return [(x, y) for x, y, *_ in e.get_points()]
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t in ("INSERT", "TEXT", "MTEXT"):
        p = e.dxf.insert
        return [(p.x, p.y)]
    if t in ("CIRCLE", "ARC"):
        c = e.dxf.center
        return [(c.x, c.y)]
    return []


def report(doc, mm, window=None):
    msp = doc.modelspace()
    def inwin(xy):
        if not window:
            return True
        x0, x1, y0, y1 = window
        return any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in xy)

    # layer x type counts (in-window)
    by = Counter()
    for e in msp:
        xy = _pts(e)
        if xy and inwin(xy):
            by[(e.dxf.layer, e.dxftype())] += 1
    print("\n=== layers x type (top 20, in window) ===")
    for (lay, t), n in by.most_common(20):
        print(f"  {n:4d}  {lay:20s} {t}")

    # TEXT schedule (built-in BF codes, room labels)
    print("\n=== TEXT / MTEXT (schedule + labels), position in mm ===")
    texts = []
    for e in msp:
        if e.dxftype() in ("TEXT", "MTEXT"):
            xy = _pts(e)
            if not inwin(xy):
                continue
            t = (e.dxf.text if e.dxftype() == "TEXT" else e.text).replace("\n", " ").strip()
            if t:
                texts.append((round(xy[0][0] * mm), round(xy[0][1] * mm), e.dxf.layer, t[:48]))
    for x, y, lay, t in sorted(texts, key=lambda r: (-r[1], r[0])):
        print(f"  ({x:7d},{y:7d})mm  {t}")

    # INSERT blocks (furniture/fixtures) with size (block def bbox) in mm
    print("\n=== INSERT blocks (furniture/fixtures), pos + size in mm ===")
    for e in msp:
        if e.dxftype() != "INSERT":
            continue
        xy = _pts(e)
        if not inwin(xy):
            continue
        bd = doc.blocks.get(e.dxf.name)
        xs, ys = [], []
        for be in (bd or []):
            for px, py in _pts(be):
                xs.append(px); ys.append(py)
        sx = e.dxf.xscale or 1.0; sy = e.dxf.yscale or 1.0
        size = (f"{(max(xs)-min(xs))*mm*sx:.0f}x{(max(ys)-min(ys))*mm*sy:.0f}mm" if xs else "?")
        print(f"  ({round(xy[0][0]*mm):7d},{round(xy[0][1]*mm):7d})mm  [{e.dxf.layer:14s}] {e.dxf.name:16s} {size}")

    # dimensions
    print("\n=== DIMENSIONS (measurement in mm) ===")
    for e in msp:
        if e.dxftype() == "DIMENSION":
            try:
                print(f"  {e.get_measurement()*mm:.0f} mm  (layer {e.dxf.layer})")
            except Exception:
                pass


def geom_bbox(doc, exclude_text=True):
    """XY bbox of drawing geometry, ignoring far-out strays (|coord|>1e5) and (optionally)
    stray label text, so a render frames the plan not the whole sheet."""
    xs, ys = [], []
    for e in doc.modelspace():
        if exclude_text and e.dxftype() in ("TEXT", "MTEXT"):
            continue
        for x, y in _pts(e):
            if abs(x) < 1e5 and abs(y) < 1e5:
                xs.append(x); ys.append(y)
    return (min(xs), max(xs), min(ys), max(ys)) if xs else None


def render(doc, path, window=None, figsize=(22, 14)):
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        from ezdxf.addons.drawing.properties import LayoutProperties
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    plt.rcParams["font.sans-serif"] = ["Tahoma", "Leelawadee UI", "DejaVu Sans"]
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    lp = LayoutProperties.from_layout(doc.modelspace())
    lp.set_colors("#FFFFFF")
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(
        doc.modelspace(), finalize=True, layout_properties=lp)
    if window:
        ax.set_xlim(window[0], window[1]); ax.set_ylim(window[2], window[3])
    else:
        bb = geom_bbox(doc)
        if bb:
            ax.set_xlim(bb[0], bb[1]); ax.set_ylim(bb[2], bb[3])
    ax.set_axis_off()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def _outdir():
    d = os.path.join(os.path.dirname(HERE), "output", "dwg_converted")
    os.makedirs(d, exist_ok=True)
    return d


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: python pipeline/dwg_ingest.py <file.dwg|.dxf> [--render] [--window x0 x1 y0 y1]")
    src = args[0]
    do_render = "--render" in args
    window = None
    if "--window" in args:
        i = args.index("--window")
        window = tuple(float(v) for v in args[i + 1:i + 5])   # in DRAWING units
    if not os.path.exists(src):
        sys.exit(f"not found: {src}")

    doc = load(src)
    mm, usrc = unit_mm(doc)
    name = os.path.splitext(os.path.basename(src))[0]
    out = _outdir()
    print(f"=== {os.path.basename(src)} ===")
    print(f"  DXF {doc.dxfversion} {doc.acad_release} | {len(list(doc.modelspace()))} entities | "
          f"{len(doc.layers)} layers")
    print(f"  UNIT: 1 unit = {mm:g} mm  [{usrc}]")
    if not src.lower().endswith(".dxf"):
        dxf_path = os.path.join(out, f"{name}.dxf")
        doc.saveas(dxf_path)
        print(f"  cached DXF -> {dxf_path}")
    report(doc, mm, window=window)
    if do_render:
        png = render(doc, os.path.join(out, f"{name}.png"), window=window)
        print(f"\n  rendered -> {png}" if png else "\n  (render skipped: pip install matplotlib)")
    print("\n  NOTE: this is a READER. Building a room-spec@0.2 from it is a human-verified step "
          "(walls span many layers; the room boundary is a design call — don't auto-fabricate coords).")
