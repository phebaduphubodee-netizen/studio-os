#!/usr/bin/env python3
"""Pull knowledge threads from a Discord server into knowledge/_inbox/discord/.

Reads forum/media channels (each post = one thread) via the Discord REST API
with a bot token, and writes one folder per thread:

    knowledge/_inbox/discord/<guild-slug>/<channel-slug>/<NNN_thread-slug>/
        thread.md    - human-readable transcript (REFERENCE tier, frontmatter)
        raw.json     - full API payload for lossless re-processing
        files/       - downloaded attachments (images/PDF by default)

Videos are recorded but NOT downloaded unless --videos is passed (Discord CDN
links in raw.json are signed and expire within ~24h, so re-run if needed).

Setup (one time, by the server owner/admin):
  1. https://discord.com/developers/applications -> New Application -> Bot
     - Bot tab: Reset Token -> copy it
     - Privileged Gateway Intents: enable MESSAGE CONTENT INTENT
  2. OAuth2 -> URL Generator: scope "bot", permissions "View Channels" +
     "Read Message History" -> open URL, invite bot to the server.
  3. Discord app: Settings -> Advanced -> Developer Mode ON, then
     right-click the server icon -> Copy Server ID.

Run:
  $env:DISCORD_BOT_TOKEN = "<token>"           (PowerShell)
  python3 scripts/discord_ingest.py --guild <SERVER_ID> --types all --dry-run
      -> prints the FULL channel inventory (type + selected/skipped). Do this first.
  python3 scripts/discord_ingest.py --guild <SERVER_ID> --types all --no-download
      -> pulls text, sizes every attachment, downloads nothing.
  python3 scripts/discord_ingest.py --guild <SERVER_ID> --types all --max-file-mb 100

COVERAGE NOTE (2026-07-12): --types defaulted to forum-only, so the 2026-07-03 ingest
silently skipped every GUILD_TEXT channel on the server (the #3dskymodel category —
furniture-2022/2024, prop-2022/23/24, lighting-2024, tree-2024 and their -preview
twins — plus #lookingfor-work). It also never walked threads hanging off text
channels. Both are fixed; a re-run needs a fresh bot token (Discord CDN URLs in the
old raw.json expired ~24 h after the pull, so nothing is re-fetchable from disk).
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://discord.com/api/v10"
FORUM_TYPES = {15, 16}          # GUILD_FORUM, GUILD_MEDIA
TEXT_TYPES = {0, 5}             # GUILD_TEXT, GUILD_ANNOUNCEMENT
TYPE_NAMES = {0: "text", 2: "voice", 4: "category", 5: "announcement",
              13: "stage", 15: "forum", 16: "media"}
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "knowledge" / "_inbox" / "discord"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def api_get(token: str, path: str, params: dict | None = None):
    """GET with Discord rate-limit handling (preemptive + 429 retry)."""
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bot {token}",
            "User-Agent": "STUDIO-OS knowledge ingest (discord_ingest.py, 1.0)",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if resp.headers.get("X-RateLimit-Remaining") == "0":
                    time.sleep(float(resp.headers.get("X-RateLimit-Reset-After", 1)) + 0.1)
                return body
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    retry = float(json.loads(e.read().decode("utf-8")).get("retry_after", 2))
                except Exception:
                    retry = 2.0
                time.sleep(retry + 0.2)
                continue
            if e.code in (500, 502, 503, 504) and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            if e.code == 401:
                die("token rejected (401) - check DISCORD_BOT_TOKEN")
            if e.code == 403:
                raise PermissionError(path)
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"gave up after retries: {path}")


def download(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "STUDIO-OS ingest"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                while chunk := resp.read(1 << 16):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"    ! download failed {dest.name}: {e}", file=sys.stderr)
        return False


def slug(text: str, max_len: int = 60) -> str:
    """Filesystem-safe slug; keeps Thai, trims length (OneDrive path limits)."""
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", text).strip().rstrip(".")
    text = re.sub(r"\s+", "-", text)
    return text[:max_len] or "untitled"


def clean_content(text: str) -> str:
    """Strip raw mention IDs; keep everything else verbatim."""
    text = re.sub(r"<@!?\d+>", "@user", text)
    text = re.sub(r"<#\d+>", "#channel", text)
    text = re.sub(r"<@&\d+>", "@role", text)
    return text


def fetch_all_messages(token: str, channel_id: str) -> list[dict]:
    messages, before = [], None
    while True:
        params = {"limit": 100}
        if before:
            params["before"] = before
        batch = api_get(token, f"/channels/{channel_id}/messages", params)
        if not batch:
            break
        messages.extend(batch)
        before = batch[-1]["id"]
        if len(batch) < 100:
            break
    messages.reverse()  # oldest first
    return messages


def fetch_threads(token: str, guild_id: str, channel_ids: set[str]) -> dict[str, list[dict]]:
    """All threads (forum posts) grouped by parent channel id."""
    by_parent: dict[str, list[dict]] = {cid: [] for cid in channel_ids}
    seen: set[str] = set()

    active = api_get(token, f"/guilds/{guild_id}/threads/active").get("threads", [])
    for t in active:
        if t.get("parent_id") in channel_ids and t["id"] not in seen:
            by_parent[t["parent_id"]].append(t)
            seen.add(t["id"])

    for cid in channel_ids:
        before = None
        while True:
            params = {"limit": 100}
            if before:
                params["before"] = before
            try:
                page = api_get(token, f"/channels/{cid}/threads/archived/public", params)
            except PermissionError:
                print(f"    ! no access to archived threads of channel {cid}", file=sys.stderr)
                break
            threads = page.get("threads", [])
            for t in threads:
                if t["id"] not in seen:
                    by_parent[cid].append(t)
                    seen.add(t["id"])
            if not page.get("has_more") or not threads:
                break
            before = threads[-1]["thread_metadata"]["archive_timestamp"]
    return by_parent


def render_thread_md(guild_name: str, channel_name: str, thread: dict,
                     messages: list[dict], tag_names: list[str],
                     attach_log: list[str]) -> str:
    created = thread.get("thread_metadata", {}).get("create_timestamp") or ""
    lines = [
        "---",
        "source: discord",
        f"server: {guild_name}",
        f"channel: {channel_name}",
        f"thread: \"{thread['name']}\"",
        f"thread_id: {thread['id']}",
        f"tags: [{', '.join(tag_names)}]",
        f"created: {created[:10]}",
        f"pulled: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        "tier: REFERENCE",
        "---",
        "",
        f"# {thread['name']}",
        "",
    ]
    for i, m in enumerate(messages, 1):
        author = m.get("author", {}).get("global_name") or m.get("author", {}).get("username", "?")
        ts = m.get("timestamp", "")[:16].replace("T", " ")
        lines.append(f"## [{i}] {author} — {ts}")
        content = clean_content(m.get("content", "")).strip()
        if content:
            lines.append(content)
        for e in m.get("embeds", []):
            bits = [b for b in (e.get("title"), e.get("url"), e.get("description")) if b]
            if bits:
                lines.append("> embed: " + " — ".join(bits))
        lines.append("")
    if attach_log:
        lines += ["## Attachments", *attach_log, ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--guild", required=True, help="Discord server ID")
    ap.add_argument("--channels", help="comma-separated channel IDs (default: all forum/media channels)")
    ap.add_argument("--types", default="forum",
                    help="channel kinds to pull: forum | text | all (default forum). "
                         "The 2026-07-03 run was forum-only and MISSED every text channel.")
    ap.add_argument("--include", help="only channels whose name contains one of these comma-separated substrings")
    ap.add_argument("--exclude", help="skip channels whose name contains one of these comma-separated substrings")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output root (default {DEFAULT_OUT})")
    ap.add_argument("--max-file-mb", type=float, default=25.0, help="max attachment size to download (default 25)")
    ap.add_argument("--videos", action="store_true", help="also download video attachments")
    ap.add_argument("--no-download", action="store_true",
                    help="manifest mode: write thread.md/raw.json and LIST every attachment with size, "
                         "but download nothing (use to size a channel before pulling GBs)")
    ap.add_argument("--dry-run", action="store_true", help="list channels/threads only, write nothing")
    args = ap.parse_args()

    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        die("DISCORD_BOT_TOKEN not set.\n"
            '  PowerShell:  $env:DISCORD_BOT_TOKEN = "<bot token>"\n'
            "  See the docstring at the top of this script for bot setup steps.")

    guild = api_get(token, f"/guilds/{args.guild}")
    guild_name = guild.get("name", args.guild)
    print(f"Server: {guild_name}")

    channels = api_get(token, f"/guilds/{args.guild}/channels")
    wanted_ids = set(args.channels.split(",")) if args.channels else None
    inc = [s.strip().lower() for s in args.include.split(",")] if args.include else None
    exc = [s.strip().lower() for s in args.exclude.split(",")] if args.exclude else None

    kinds = {k.strip().lower() for k in args.types.split(",")}
    if "all" in kinds:
        pull_types = FORUM_TYPES | TEXT_TYPES
    else:
        pull_types = set()
        if "forum" in kinds:
            pull_types |= FORUM_TYPES
        if "text" in kinds:
            pull_types |= TEXT_TYPES
    if not pull_types and wanted_ids is None:
        die(f"--types {args.types}: nothing to pull (use forum | text | all)")

    cat_names = {c["id"]: c["name"] for c in channels if c.get("type") == 4}

    targets = []
    for ch in channels:
        if wanted_ids is not None:
            if ch["id"] in wanted_ids:
                targets.append(ch)
            continue
        if ch.get("type") not in pull_types:
            continue
        name = ch.get("name", "").lower()
        if inc and not any(s in name for s in inc):
            continue
        if exc and any(s in name for s in exc):
            continue
        targets.append(ch)

    # Full server inventory — the ONLY way to know what a run did not see.
    sel = {c["id"] for c in targets}
    print("\nServer channel inventory (type / selected / category / name):")
    for ch in sorted(channels, key=lambda c: (cat_names.get(c.get("parent_id"), ""), c.get("position", 0))):
        if ch.get("type") == 4:
            continue
        tname = TYPE_NAMES.get(ch.get("type"), str(ch.get("type")))
        mark = "PULL" if ch["id"] in sel else "skip"
        cat = cat_names.get(ch.get("parent_id"), "-")
        print(f"  [{mark}] {tname:12s} {cat:24s} #{ch['name']}  ({ch['id']})")
    n_unseen = sum(1 for c in channels
                   if c.get("type") in (FORUM_TYPES | TEXT_TYPES) and c["id"] not in sel)
    if n_unseen:
        print(f"  !! {n_unseen} readable channel(s) NOT selected by this run — widen --types/--include")

    if not targets:
        die("no matching channels found")
    print(f"\nChannels: {', '.join(c['name'] for c in targets)}")

    text_targets = [c for c in targets if c.get("type") in TEXT_TYPES]
    # Text channels can carry threads too — the forum-only 2026-07-03 run never looked.
    threads_by_parent = fetch_threads(token, args.guild, {c["id"] for c in targets})

    run_stats, skipped_files = [], []
    guild_dir = args.out / slug(guild_name)

    for ch in targets:
        tag_map = {t["id"]: t["name"] for t in ch.get("available_tags", [])}
        units = sorted(threads_by_parent.get(ch["id"], []), key=lambda t: int(t["id"]))
        if ch in text_targets:
            # the channel's own message stream is a unit, plus any threads hanging off it
            units = [{"id": ch["id"], "name": ch["name"], "thread_metadata": {}, "applied_tags": []}] + units
        print(f"\n#{ch['name']}: {len(units)} thread(s)")
        if args.dry_run:
            for t in units:
                print(f"  - {t['name']}")
            continue

        ch_dir = guild_dir / slug(ch["name"])
        for n, t in enumerate(units, 1):
            messages = fetch_all_messages(token, t["id"])
            t_dir = ch_dir / f"{n:03d}_{slug(t['name'])}"
            t_dir.mkdir(parents=True, exist_ok=True)

            attach_log = []
            for m in messages:
                for a in m.get("attachments", []):
                    size_mb = a.get("size", 0) / (1 << 20)
                    ctype = a.get("content_type", "") or ""
                    fname = slug(a.get("filename", "file"), 80)
                    dest = t_dir / "files" / f"{a['id'][-6:]}_{fname}"
                    is_video = ctype.startswith("video/")
                    if args.no_download:
                        attach_log.append(f"- [ ] {a.get('filename')} ({ctype}, {size_mb:.1f}MB) — MANIFEST ONLY")
                        skipped_files.append(f"{ch['name']}/{t['name']}: {a.get('filename')} ({size_mb:.1f}MB, manifest)")
                    elif (is_video and not args.videos) or size_mb > args.max_file_mb:
                        why = "video, use --videos" if is_video and not args.videos else f"{size_mb:.0f}MB > cap"
                        attach_log.append(f"- [ ] {a.get('filename')} ({ctype}, {size_mb:.1f}MB) — SKIPPED ({why})")
                        skipped_files.append(f"{ch['name']}/{t['name']}: {a.get('filename')} ({why})")
                    elif download(a["url"], dest):
                        attach_log.append(f"- [x] files/{dest.name} ({ctype}, {size_mb:.1f}MB)")
                    else:
                        attach_log.append(f"- [ ] {a.get('filename')} — DOWNLOAD FAILED")

            tag_names = [tag_map.get(tid, tid) for tid in t.get("applied_tags", [])]
            (t_dir / "thread.md").write_text(
                render_thread_md(guild_name, ch["name"], t, messages, tag_names, attach_log),
                encoding="utf-8")
            (t_dir / "raw.json").write_text(
                json.dumps({"thread": t, "messages": messages}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            run_stats.append((ch["name"], t["name"], len(messages), str(t_dir.relative_to(args.out))))
            print(f"  [{n:3d}/{len(units)}] {t['name']} ({len(messages)} msg)")

    if args.dry_run:
        return

    index = [f"# Discord ingest — {guild_name}",
             f"Pulled: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | tier: REFERENCE (distill into knowledge/ before use)", ""]
    cur = None
    for ch_name, t_name, n_msg, rel in run_stats:
        if ch_name != cur:
            index += [f"\n## #{ch_name}"]
            cur = ch_name
        index.append(f"- [{t_name}]({rel.replace(os.sep, '/')}/thread.md) — {n_msg} msg")
    if skipped_files:
        index += ["", "## Skipped attachments (re-run with --videos / higher --max-file-mb; CDN URLs in raw.json expire ~24h)"]
        index += [f"- {s}" for s in skipped_files]
    guild_dir.mkdir(parents=True, exist_ok=True)
    (guild_dir / "_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    print(f"\nDone: {len(run_stats)} threads -> {guild_dir}")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} attachment(s) — see _index.md")


if __name__ == "__main__":
    main()
