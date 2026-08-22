"""glance.py — the seconds-level LOOK rung (ORD-2026-08-22-process-review-actions, item 4).

WHAT IT IS: build machinery, not a checker (D-112 side of the line): it renders a
cheap frame from a SAVED .blend so the builder can LOOK between edits, the way the
friend studio looks in Enscape. It judges nothing, gates nothing, writes no verdicts,
and never saves the .blend back (the deliverable file is opened, rendered from, and
left untouched). Cycles full fidelity stays what closes gates (R5 unchanged: the
glance KILLS bad work early, it never certifies good work).

ENGINE NOTE vs pipeline/CLAUDE.md "RENDER ENGINE = CYCLES": that law pins the
DELIVERABLE engine (and the .blend still records Cycles — this script changes the
engine only in its own Blender process's memory). The EEVEE-headless risk in the DR
is an EGL/Xvfb (Linux) failure; on this Windows machine both Workbench and Eevee
were measured working headless on 2026-08-22 (numbers in
docs/process-review-2026-08-22.md, "Glance rung — measured").

USAGE (plain python drives a headless Blender):
  python glance.py <file.blend|dir>              one-shot glance (dir -> newest .blend)
  python glance.py <blend> --mode=eevee          eevee instead of workbench
  python glance.py <blend> --scale=25            resolution % of the saved frame (default 50)
  python glance.py <blend> --watch               keep Blender open, serve --snap requests
  python glance.py <blend> --snap                ask the running watcher for a frame (~1-2 s)
  python glance.py <blend> --stop                stop the watcher
  --out=PATH   where the PNG lands (default <blend dir>/<stem>_glance_<mode>.png)
  --cam=NAME   render from a named camera instead of the scene's active (eye) camera

The camera is whatever the .blend saved as active — build_room sets the --eye camera
before save(), so a lane .blend glances from the lane's own eye view.

Pure logic (parsing, mode/engine selection, watch protocol) has no bpy import and is
tested in test_glance.py; bpy is imported only inside the in-Blender functions.
"""

import glob as _glob
import json
import os
import shutil
import subprocess
import sys
import time

WORKBENCH = "workbench"
EEVEE = "eevee"
MODES = (WORKBENCH, EEVEE)
# Default measured on this machine (RTX 3060 Laptop 6 GB), 2026-08-22, on the lane's
# 118 MB p2r55 .blend: one-shot workbench 6.6 s vs eevee 7.0 s warm (26.9 s the very
# first time — one-time shader compile, cached on disk after that); --watch snaps
# eevee 2.6-2.7 s vs workbench 0.7 s. EEVEE renders the scene's real node materials +
# lights (near-Cycles legibility: wood, slat wall, lit sconces) where workbench shows
# flat grey, and 2.7 s is inside the seconds target — so the trade picks EEVEE.
# Full numbers: docs/process-review-2026-08-22.md "Glance rung — measured".
DEFAULT_MODE = EEVEE
DEFAULT_SCALE = 50
EEVEE_SAMPLES = 16          # a glance needs shape/contact/tone, not converged AA
SNAP_TIMEOUT_S = 120.0      # first snap may still be paying the scene load
_POLL_S = 0.05

# eevee engine id renamed across Blender versions; try in order, first that sticks wins
EEVEE_CANDIDATES = ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")
WORKBENCH_CANDIDATES = ("BLENDER_WORKBENCH",)


# ---------------------------------------------------------------- pure logic

def parse_args(argv):
    """argv AFTER the script name (driver) or after `--` (in Blender) -> config dict.
    Loud on anything unknown: a glance that silently ignored a flag would be the
    'printed as a suggestion' defect in miniature."""
    cfg = {"blend": None, "mode": DEFAULT_MODE, "scale": DEFAULT_SCALE, "out": None,
           "cam": None, "watch": False, "snap": False, "stop": False,
           "inblender": False, "blender": None, "timeout": SNAP_TIMEOUT_S}
    for a in argv:
        if a == "--watch":
            cfg["watch"] = True
        elif a == "--snap":
            cfg["snap"] = True
        elif a == "--stop":
            cfg["stop"] = True
        elif a == "--_inblender":
            cfg["inblender"] = True
        elif a.startswith("--mode="):
            cfg["mode"] = a.split("=", 1)[1]
        elif a.startswith("--scale="):
            try:
                cfg["scale"] = int(a.split("=", 1)[1])
            except ValueError:
                raise SystemExit(f"glance: --scale wants an integer percent, got {a!r}")
        elif a.startswith("--out="):
            cfg["out"] = a.split("=", 1)[1]
        elif a.startswith("--cam="):
            cfg["cam"] = a.split("=", 1)[1]
        elif a.startswith("--blender="):
            cfg["blender"] = a.split("=", 1)[1]
        elif a.startswith("--timeout="):
            cfg["timeout"] = float(a.split("=", 1)[1])
        elif a.startswith("-"):
            raise SystemExit(f"glance: unknown flag {a!r} (modes: {', '.join(MODES)})")
        elif cfg["blend"] is None:
            cfg["blend"] = a
        else:
            raise SystemExit(f"glance: two positional args ({cfg['blend']!r}, {a!r}); "
                             f"one .blend (or dir) only")
    if cfg["mode"] not in MODES:
        raise SystemExit(f"glance: --mode={cfg['mode']!r} unknown (want one of {MODES})")
    if not 1 <= cfg["scale"] <= 100:
        raise SystemExit(f"glance: --scale={cfg['scale']} out of range 1-100")
    if cfg["watch"] and (cfg["snap"] or cfg["stop"]):
        raise SystemExit("glance: --watch starts the server; --snap/--stop talk to it — "
                         "pick one")
    if cfg["blend"] is None and not cfg["inblender"]:
        # inside Blender the scene is already open; the driver must name one
        raise SystemExit("glance: need a .blend file (or a directory holding one)")
    return cfg


def latest_blend(entries):
    """[(name, mtime)] -> newest *.blend name, skipping Blender's *.blend1/2 backups.
    None when the listing has no .blend at all."""
    cand = [(n, m) for n, m in entries if n.lower().endswith(".blend")]
    return max(cand, key=lambda t: t[1])[0] if cand else None


def default_out(blend_path, mode):
    stem = os.path.splitext(os.path.basename(blend_path))[0]
    return os.path.join(os.path.dirname(blend_path), f"{stem}_glance_{mode}.png")


def engine_candidates(mode):
    return WORKBENCH_CANDIDATES if mode == WORKBENCH else EEVEE_CANDIDATES


def ctl_paths(blend_path):
    """Watcher control files live NEXT TO the blend (pipeline/output is off-OneDrive,
    so mtime polling is honest there)."""
    base = blend_path + ".glance"
    return {"cmd": base + ".cmd", "done": base + ".done", "alive": base + ".alive"}


def make_request(seq, mode, scale, out, cam=None, stop=False):
    return json.dumps({"seq": seq, "mode": mode, "scale": scale, "out": out,
                       "cam": cam, "stop": bool(stop)})


def parse_request(text):
    d = json.loads(text)
    if not isinstance(d, dict) or "seq" not in d:
        raise ValueError(f"glance request without a seq: {text!r}")
    return d


def build_blender_cmd(blender_exe, blend_path, script_path, passthrough):
    """The headless invocation. NOT --factory-startup: the whole point is opening the
    saved scene of record."""
    return [blender_exe, "-b", blend_path, "--python", script_path, "--",
            "--_inblender"] + list(passthrough)


def find_blender(env=None, which=shutil.which, globber=_glob.glob):
    """$INTERIOR_BLENDER > PATH > newest 'C:\\Program Files\\Blender Foundation\\Blender *'.
    Same ladder as make_all._find_blender, standalone so glance stays importable alone."""
    env = os.environ if env is None else env
    p = env.get("INTERIOR_BLENDER")
    if p and os.path.isfile(p):
        return p
    p = which("blender")
    if p:
        return p
    hits = []
    for pat in (r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
                r"C:\Program Files (x86)\Blender Foundation\Blender*\blender.exe",
                "/usr/bin/blender", "/usr/local/bin/blender", "/snap/bin/blender"):
        hits += globber(pat)
    hits = [h for h in hits if os.path.isfile(h)]
    return sorted(hits)[-1] if hits else None


def resolve_blend(path):
    if os.path.isdir(path):
        entries = [(n, os.path.getmtime(os.path.join(path, n))) for n in os.listdir(path)]
        name = latest_blend(entries)
        if not name:
            raise SystemExit(f"glance: no .blend under {path!r}")
        return os.path.join(path, name)
    if not os.path.isfile(path):
        raise SystemExit(f"glance: {path!r} does not exist")
    return path


# ------------------------------------------------------------- in-Blender side
# (bpy imported only here; nothing above may touch it — LAYER LAW)

def _bpy_configure(cfg):
    import bpy
    scn = bpy.context.scene
    engine = None
    for cand in engine_candidates(cfg["mode"]):
        try:
            scn.render.engine = cand
            engine = cand
            break
        except TypeError:
            continue
    if engine is None:
        raise SystemExit(f"glance: no engine for mode {cfg['mode']!r} in this Blender "
                         f"(tried {engine_candidates(cfg['mode'])})")
    if cfg["mode"] == WORKBENCH:
        sh = scn.display.shading
        for attr, val in (("light", "STUDIO"), ("color_type", "TEXTURE"),
                          ("show_cavity", True), ("show_shadows", True)):
            try:
                setattr(sh, attr, val)
            except Exception:
                pass  # shading knobs vary by version; a plainer glance still glances
    else:
        for attr in ("taa_render_samples",):
            try:
                setattr(scn.eevee, attr, EEVEE_SAMPLES)
            except Exception:
                pass
    if cfg["cam"]:
        cam = bpy.data.objects.get(cfg["cam"])
        if cam is None or cam.type != "CAMERA":
            cams = [o.name for o in bpy.data.objects if o.type == "CAMERA"]
            raise SystemExit(f"glance: --cam={cfg['cam']!r} not a camera here "
                             f"(cameras: {cams})")
        scn.camera = cam
    scn.render.resolution_percentage = cfg["scale"]
    scn.render.image_settings.file_format = "PNG"
    scn.render.use_compositing = False   # compositor trees belong to the Cycles pass
    scn.render.use_sequencer = False
    return scn, engine


def _bpy_render_once(cfg):
    import bpy
    out = cfg["out"] or default_out(bpy.data.filepath, cfg["mode"])
    scn, engine = _bpy_configure(cfg)
    scn.render.filepath = out
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    print(f"GLANCE rendered: {out} (engine={engine} scale={cfg['scale']}% "
          f"cam={scn.camera.name if scn.camera else '?'} render_s={dt:.2f})")
    return out, dt, engine


def _atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def _bpy_watch(cfg):
    """Keep this Blender open; render whenever the cmd file carries a new seq.
    The scene load is paid ONCE — this loop is what makes the rung seconds-level."""
    import bpy
    ctl = ctl_paths(bpy.data.filepath)
    _atomic_write(ctl["alive"], json.dumps(
        {"pid": os.getpid(), "blend": bpy.data.filepath, "started": time.time()}))
    print(f"GLANCE watch: scene loaded, serving snaps (ctl={ctl['cmd']}) — "
          f"stop with: python glance.py {bpy.data.filepath!r} --stop")
    sys.stdout.flush()
    last_seq = None
    try:
        while True:
            try:
                with open(ctl["cmd"], encoding="utf-8") as f:
                    req = parse_request(f.read())
            except (OSError, ValueError):
                time.sleep(_POLL_S)
                continue
            if req["seq"] == last_seq:
                time.sleep(_POLL_S)
                continue
            last_seq = req["seq"]
            if req.get("stop"):
                _atomic_write(ctl["done"], json.dumps({"seq": req["seq"], "ok": True,
                                                       "stopped": True}))
                print("GLANCE watch: stopped by request")
                return
            merged = dict(cfg)
            for k in ("mode", "scale", "out", "cam"):
                if req.get(k) is not None:
                    merged[k] = req[k]
            try:
                out, dt, engine = _bpy_render_once(merged)
                _atomic_write(ctl["done"], json.dumps(
                    {"seq": req["seq"], "ok": True, "out": out,
                     "render_s": round(dt, 3), "engine": engine}))
            except Exception as e:  # a broken snap must answer, not hang the client
                _atomic_write(ctl["done"], json.dumps(
                    {"seq": req["seq"], "ok": False, "error": str(e)}))
            sys.stdout.flush()
    finally:
        for p in (ctl["alive"],):
            try:
                os.remove(p)
            except OSError:
                pass


# ------------------------------------------------------------------ driver side

def _drive_snap(cfg, blend):
    ctl = ctl_paths(blend)
    if not os.path.isfile(ctl["alive"]):
        raise SystemExit(f"glance: no watcher on {blend!r} — start one with: "
                         f"python glance.py {blend!r} --watch (in its own terminal)")
    seq = time.time_ns()
    out = cfg["out"]  # None -> watcher picks its default
    _atomic_write(ctl["cmd"], make_request(seq, cfg["mode"], cfg["scale"], out,
                                           cam=cfg["cam"], stop=cfg["stop"]))
    t0 = time.time()
    deadline = t0 + cfg["timeout"]
    while time.time() < deadline:
        try:
            with open(ctl["done"], encoding="utf-8") as f:
                d = json.loads(f.read())
        except (OSError, ValueError):
            d = None
        if d and d.get("seq") == seq:
            wall = time.time() - t0
            if d.get("stopped"):
                for p in (ctl["cmd"], ctl["done"]):   # the watcher already removed alive
                    try:
                        os.remove(p)
                    except OSError:
                        pass
                print(f"glance: watcher stopped ({wall:.2f}s)")
                return 0
            if not d.get("ok"):
                print(f"glance: snap FAILED in watcher: {d.get('error')}")
                return 1
            print(f"glance: snap done in {wall:.2f}s wall ({d.get('render_s')}s render, "
                  f"engine={d.get('engine')}) -> {d.get('out')}")
            return 0
        time.sleep(_POLL_S)
    raise SystemExit(f"glance: watcher did not answer within {cfg['timeout']}s "
                     f"(is the terminal running --watch still alive?)")


def main(argv):
    cfg = parse_args(argv)
    if cfg["inblender"]:
        if cfg["watch"]:
            _bpy_watch(cfg)
        else:
            _bpy_render_once(cfg)
        return 0
    blend = resolve_blend(cfg["blend"])
    if cfg["snap"] or cfg["stop"]:
        return _drive_snap(cfg, blend)
    exe = cfg["blender"] or find_blender()
    if not exe:
        raise SystemExit("glance: no Blender found (set $INTERIOR_BLENDER)")
    passthrough = [f"--mode={cfg['mode']}", f"--scale={cfg['scale']}"]
    if cfg["out"]:
        passthrough.append(f"--out={cfg['out']}")
    if cfg["cam"]:
        passthrough.append(f"--cam={cfg['cam']}")
    if cfg["watch"]:
        passthrough.append("--watch")
    cmd = build_blender_cmd(exe, blend, os.path.abspath(__file__), passthrough)
    t0 = time.time()
    rc = subprocess.run(cmd).returncode
    if not cfg["watch"]:
        print(f"glance: total wall {time.time() - t0:.2f}s "
              f"(Blender start + scene load + render; --watch amortizes the load)")
    return rc


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401 — running inside Blender: args come after `--`
        _argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        sys.exit(main(_argv))
    except ImportError:
        sys.exit(main(sys.argv[1:]))
