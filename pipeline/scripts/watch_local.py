#!/usr/bin/env python3
"""watch_local.py — the ONLY way this repo's own video may reach the `watch` skill.

    python pipeline/scripts/watch_local.py <video-path-or-url> [any watch.py flag ...]

WHY THIS IS A WRAPPER AND NOT A SENTENCE IN A README
----------------------------------------------------
The `watch` skill (bradautomates/claude-video, installed at machine level 2026-08-28) has
exactly one path that leaves this machine: when a source has no captions it extracts a mono
16 kHz audio clip and uploads it to Groq or OpenAI for transcription. For a public YouTube
URL that is unremarkable. For a turntable of a client's bedroom, or a walkthrough the owner
shot on site, it is the friend's delivered work and the client's home going to a third
party.

The skill's own guard against that is the flag `--no-whisper`, **which somebody has to
type**. R13 names that shape and prices it: *"an order carried out as an OPT-IN is an order
that was not carried out, because nobody types the flag."* The repo has eight recorded
instances, one of them a comment citing an owner order seventeen lines above the constant
that disobeyed it. A ninth is not worth adding for the sake of a convenience.

So the decision is moved off the typist and onto the PATH:

  * a source inside `projects/`, `clients/`, `_private/`, `assets/` or anywhere under this
    repo is OURS -> `--no-whisper` is INJECTED, and an explicit `--whisper` is refused by
    name rather than silently overridden (a flag that is ignored teaches the next caller
    that it works);
  * a URL is public data -> passed through untouched, whisper allowed;
  * anything that is neither a URL nor an existing file is REFUSED. Fail closed: a typo in
    a path must not fall through to "treat it as a URL and send it somewhere".

WHAT THIS DOES NOT CLAIM. It does not stop a human from calling `watch.py` directly, and it
cannot. It removes the case where the LANE forgets — which is the case that actually
happened eight times.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Roots whose contents may never have audio uploaded. `_private` is the friend's delivered
# client work; `clients` and `projects` are the studio's own client material; `assets` holds
# licensed binaries. The list is a floor, not a fence: ANY path under the repo is treated as
# ours, so a new directory is protected the day it is created rather than the day someone
# remembers to add it here. A rule that names the directories it applies to will always
# exempt the next one (R9b).
NAMED_ROOTS = ("projects", "clients", "_private", "assets", "training", "pipeline/output")

SKILL_DIR_ENV = "WATCH_SKILL_DIR"
DEFAULT_SKILL_DIR = os.path.join(os.path.expanduser("~"), ".claude", "skills", "watch")


class RefusedError(Exception):
    """The wrapper will not run this. Callers turn it into exit 2."""


def is_url(source):
    return "://" in source[:12] and source.split("://", 1)[0].lower() in (
        "http", "https", "ftp", "ftps", "rtmp", "rtsp")


def classify(source, repo=REPO, exists=os.path.exists):
    """'url' | 'ours' | 'foreign' — and it RAISES rather than guessing.

    PURE apart from the injected `exists`, so the tests drive every branch without touching
    a disk.
    """
    if not source or not str(source).strip():
        raise RefusedError("no source given")
    source = str(source)
    if is_url(source):
        return "url"
    p = os.path.abspath(os.path.expanduser(source))
    if not exists(p):
        raise RefusedError(
            f"{source!r} is neither a URL nor a file that exists. Refusing rather than "
            f"guessing — a mistyped path must never fall through to 'send it somewhere'.")
    try:
        inside = os.path.commonpath([os.path.abspath(repo), p]) == os.path.abspath(repo)
    except ValueError:            # different drives on Windows
        inside = False
    return "ours" if inside else "foreign"


def audit(source, repo=REPO):
    """The one-line reason this run is allowed to do what it does. Printed, always."""
    kind = classify(source, repo=repo)
    if kind == "url":
        return kind, ("PUBLIC SOURCE — whisper fallback allowed; nothing of ours travels.")
    if kind == "ours":
        return kind, ("OUR OWN MEDIA (inside the repo) — whisper fallback REFUSED by "
                      "construction; no audio leaves this machine.")
    return kind, ("FOREIGN LOCAL FILE (outside the repo) — whisper fallback REFUSED by "
                  "default; it is not ours to send either.")


def build_argv(source, extra, skill_dir, python=sys.executable):
    """The exact command that will run. PURE, so a test can read it without spawning."""
    if any(a == "--whisper" or a.startswith("--whisper=") for a in extra):
        raise RefusedError(
            "--whisper is refused here. This wrapper exists because the protection must "
            "not depend on a flag; accepting an override would reinstate the defect it "
            "removes. Call watch.py directly and own that decision explicitly.")
    watch = os.path.join(skill_dir, "scripts", "watch.py")
    argv = [python, watch, source] + list(extra)
    kind, _why = audit(source)
    if kind != "url" and "--no-whisper" not in extra:
        argv.append("--no-whisper")
    return argv


def resolve_skill_dir(env=None, exists=os.path.exists):
    env = os.environ if env is None else env
    d = env.get(SKILL_DIR_ENV) or DEFAULT_SKILL_DIR
    if not exists(os.path.join(d, "scripts", "watch.py")):
        raise RefusedError(
            f"the watch skill is not at {d!r} (no scripts/watch.py). This is a HARD STOP, "
            f"not a warning: a guard that cannot find the thing it guards has not guarded "
            f"anything. Set {SKILL_DIR_ENV} or reinstall the skill.")
    return d


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    source, extra = argv[0], argv[1:]
    try:
        kind, why = audit(source)
        skill_dir = resolve_skill_dir()
        cmd = build_argv(source, extra, skill_dir)
    except RefusedError as e:
        print(f"watch_local: REFUSED — {e}", file=sys.stderr)
        return 2
    # FLUSHED, and that is not a style point. Python buffers stdout when it is piped, while
    # the child writes to the same fd unbuffered — so without this the line explaining WHY
    # a run was allowed prints AFTER the run it authorised, or is lost if the child dies.
    # A guard whose reason arrives after its own decision is a guard nobody can audit.
    print(f"watch_local: {kind.upper()} — {why}", flush=True)
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
