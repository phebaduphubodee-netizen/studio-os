#!/usr/bin/env python3
"""skill_usage.py — does anything ever CALL the skills and agents this repo builds?

WHY THIS EXISTS (2026-08-27, owner: "ทั้งหมดนี้คุณต้องเป็นคนเรียกใช้เองเมื่อต้องใช้").
The repo's six skills were written on 2026-07-02, produced concept.md / ffe-candidates.json
/ bom.md within two days, and then never fired again for 54 days and 86 render rounds.
Nothing noticed, because nothing could: a skill leaves no trace when it is NOT used, and
the roster prints identically whether it is loaded every round or never again. That is the
repo's own recurring defect — a queue whose consumer never visits it — aimed at the layer
that was supposed to fix it. The proposal that created these files carried an acceptance
test ("evidence it was called within 3 rounds") with NO INSTRUMENT BEHIND IT, which is
R13's "obedience there is only declared" one level up.

So: every Skill and Agent call is stamped by a hook, and the roster prints its own
last-used age at every session open. A skill nobody calls prints as such until it is
either called or retired — never silently.

IT REPORTS ITS OWN WIRING, and that is the point rather than a nicety. A counter reading
zero has two completely different meanings — "nothing was invoked" and "the hook is not
firing" — and a rung that cannot tell those apart is exactly the kind of instrument this
file exists to replace. The SessionStart stamp is the discriminator: sessions > 0 proves
the hook layer is alive, so zero skill rows then means zero skill calls, for real.

MODES
  hook      read a PreToolUse payload on stdin, append one row, exit 0 ALWAYS
  session   the SessionStart stamp (same contract)
  report    the plan_status section
  selftest  prove the write path works without a live hook

A HOOK MUST NEVER BLOCK THE LANE. Every failure here is swallowed and exits 0: this
counts work, it does not police it. The moment it gains an opinion it stops being free.
"""
import json
import os
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(REPO, "qa", "skill-usage.json")
LOG = os.path.join(REPO, "qa", "skill-usage.jsonl")
SKILLS_DIR = os.path.join(REPO, ".claude", "skills")
AGENTS_DIR = os.path.join(REPO, ".claude", "agents")
STALE_DAYS = 14


# ------------------------------------------------------------------ pure part --

def roster(skills_dir=None, agents_dir=None):
    """Every skill and agent this REPO ships, discovered from disk.

    DISCOVERED, NEVER LISTED. A hard-coded roster is the allowlist defect this repo has
    paid for repeatedly (the placement guards it replaced covered 2 of 5 classes, so 8 of
    13 objects were exempt) — with a typed list, the next skill added is the one nobody
    counts, and it would be missing from the exact report built to catch that.
    """
    out = []
    for d, kind in ((skills_dir or SKILLS_DIR, "skill"), (agents_dir or AGENTS_DIR, "agent")):
        try:
            entries = sorted(os.listdir(d))
        except OSError:
            continue
        for e in entries:
            p = os.path.join(d, e)
            if kind == "skill" and os.path.isdir(p) and os.path.exists(
                    os.path.join(p, "SKILL.md")):
                out.append((kind, e))
            elif kind == "agent" and e.endswith(".md") and e != "README.md":
                out.append((kind, e[:-3]))
    return out


def name_of(tool, tool_input):
    """The thing that was invoked, as the roster names it. PURE."""
    ti = tool_input or {}
    if tool == "Skill":
        return str(ti.get("skill") or "?")
    if tool in ("Agent", "Task"):
        return str(ti.get("subagent_type") or "?")
    return "?"


def summarise(rows, ros, today=None, stale_days=STALE_DAYS):
    """(sessions, calls, last-use per name, never-used, stale) from raw rows. PURE."""
    today = today or date.today()
    sessions = sum(1 for r in rows if r.get("kind") == "session")
    # `__selftest__` rows prove the WRITE PATH and nothing about the lane, so they are
    # excluded from the count for the same reason blenderkit excludes probe runs from
    # its month clock: an instrument must never count its own heartbeat as work.
    calls = [r for r in rows if r.get("kind") in ("skill", "agent")
             and not str(r.get("name", "")).startswith("__")]
    last = {}
    for r in calls:
        n = r.get("name")
        if not n:
            continue
        d = str(r.get("ts", ""))[:10]
        prev_day, prev_n = last.get(n, ("", 0))
        last[n] = (max(prev_day, d), prev_n + 1)
    never = [f"{k}:{n}" for k, n in ros if n not in last]
    stale = []
    for k, n in ros:
        if n in last:
            try:
                age = (today - date.fromisoformat(last[n][0])).days
            except ValueError:
                continue
            if age >= stale_days:
                stale.append((n, age))
    return sessions, len(calls), last, never, sorted(stale, key=lambda t: -t[1])


# ------------------------------------------------------------------ the store --

def _append(row, log=None):
    """One line, one write() — the store is append-only JSONL because THREE SESSIONS RUN
    ON THIS REPO AT ONCE (the session registry says so at every open), and a
    read-modify-write of a single JSON would silently drop whichever call lost the race."""
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with open(log or LOG, "a", encoding="utf-8") as fh:
        fh.write(line)


def read_rows(log=None):
    rows = []
    try:
        with open(log or LOG, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except ValueError:
                    continue
    except OSError:
        pass
    return rows


def read_state(state=None):
    try:
        with open(state or STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


# ------------------------------------------------------------------- the hook --

def hook(payload, log=None):
    """Stamp one invocation. Returns the row, or None when the tool is not ours."""
    tool = payload.get("tool_name") or ""
    if tool not in ("Skill", "Agent", "Task"):
        return None
    row = {"ts": datetime.now().isoformat(timespec="seconds"),
           "kind": "skill" if tool == "Skill" else "agent",
           "name": name_of(tool, payload.get("tool_input")),
           "session": (payload.get("session_id") or "")[:8]}
    _append(row, log)
    return row


def session_stamp(payload, log=None):
    row = {"ts": datetime.now().isoformat(timespec="seconds"), "kind": "session",
           "name": (payload.get("source") or "start"),
           "session": (payload.get("session_id") or "")[:8]}
    _append(row, log)
    return row


# ----------------------------------------------------------------- the report --

def off_roster(rows, ros, today=None):
    """Names that were STAMPED but that `roster()` does not govern. PURE.

    WHY THIS EXISTS, measured on this file 2026-08-28. `hook()` stamps EVERY Skill/Agent
    call by name and has no allowlist — correctly, since an allowlist is the defect
    `roster()`'s own docstring refuses. But `roster()` discovers only what THIS REPO ships
    (`.claude/skills`, `.claude/agents`), so a skill installed at the machine level is
    counted and never named: it can never appear under "ยังไม่เคยถูกเรียกเลย", never age
    into the ≥14-day line, and never be told to justify itself.

    The reading that made it a defect rather than a gap: the headline said "ถูกเรียกจริง 4
    ครั้ง" while SIX of the SEVEN roster skills had never been called once — because two of
    those four calls were `scrutinize` and `watch`, which the roster does not govern. A
    total that borrows other lanes' work to describe this one is a flattering counter, the
    family this repo has caught in a dozen places.

    So the count is SPLIT and these rows are named. They are deliberately NOT merged into
    the roster: "shipped by this repo" and "installed on this machine" are different
    claims, and a fresh clone has the first and not the second.
    """
    known = {n for _k, n in ros}
    today = today or date.today()
    seen = {}
    for r in rows:
        if r.get("kind") not in ("skill", "agent"):
            continue
        n = r.get("name") or "?"
        if n in known or n == "__selftest__":
            continue
        e = seen.setdefault(n, {"name": n, "kind": r["kind"], "calls": 0, "last": None})
        e["calls"] += 1
        ts = (r.get("ts") or "")[:10]
        if ts and (e["last"] is None or ts > e["last"]):
            e["last"] = ts
    out = []
    for e in sorted(seen.values(), key=lambda x: x["name"]):
        e["age"] = None
        if e["last"]:
            try:
                y, m, d = (int(x) for x in e["last"].split("-"))
                e["age"] = (today - date(y, m, d)).days
            except (ValueError, TypeError):
                e["age"] = None
        out.append(e)
    return out


def report_lines(rows=None, ros=None, state=None, today=None):
    rows = read_rows() if rows is None else rows
    ros = roster() if ros is None else ros
    st = read_state() if state is None else state
    wired = st.get("wired_at", "?")
    sessions, calls, last, never, stale = summarise(rows, ros, today)
    n_sk = sum(1 for k, _ in ros if k == "skill")
    n_ag = len(ros) - n_sk
    off = off_roster(rows, ros, today)
    off_calls = sum(e["calls"] for e in off)
    # THE HEADLINE COUNTS THE ROSTER, NOT THE LOG. Before this split it printed the log's
    # total, so calls to skills this roster does not govern made the roster look alive
    # while six of its seven skills had never been called.
    out = ["", "SKILL/AGENT roster {} skill · {} agent (นับตั้งแต่ {}) — ถูกเรียกจริง {} "
                "ครั้ง{} · session ที่เห็น {}".format(
                    n_sk, n_ag, wired, calls - off_calls,
                    " (+{} นอกทะเบียน)".format(off_calls) if off_calls else "",
                    sessions)]
    # THE DISCRIMINATOR IS "NO EVIDENCE OF THE HOOK AT ALL", NOT "NO SESSION STAMP".
    # Caught on this rung's first live reading, minutes after it shipped: the log held a
    # real Skill row (the hook fired mid-session, before any SessionStart could) while
    # `sessions` was 0, and the report printed "the hook has never fired" directly under
    # the row that hook had just written. A confident wrong line is the exact failure this
    # file was built to end, so the test is now: has ANY row ever arrived, by either route?
    if sessions == 0 and calls == 0:
        out.append("            **hook ยังไม่เคยยิงเลย — ตัวเลขข้างบนพิสูจน์อะไรไม่ได้** "
                   "(ยังไม่ wired หรือยังไม่ได้ restart session) — .claude/settings.local.json "
                   "แล้ว `python pipeline/scripts/skill_usage.py selftest`")
        return out
    if sessions == 0:
        out.append("            (ยังไม่มี SessionStart stamp — hook เพิ่งถูกต่อสายกลางเซสชัน "
                   "หรือเซสชันนี้เริ่มก่อนมันถูกต่อ; แถวที่นับได้ข้างบนพิสูจน์ว่า hook ทำงาน)")
    if never:
        out.append("            ยังไม่เคยถูกเรียกเลย: {}".format(", ".join(never)))
    if stale:
        out.append("            ไม่ถูกเรียก ≥{}วัน: {}".format(
            STALE_DAYS, " · ".join("{} ({}d)".format(n, a) for n, a in stale)))
    if not never and not stale and calls:
        out.append("            ทุกตัวในทะเบียนถูกเรียกภายใน {} วัน".format(STALE_DAYS))
    if off:
        out.append("            ถูกประทับแต่ไม่อยู่ในทะเบียน (ติดตั้งระดับเครื่อง — กฎ ≥{}วัน "
                   "เอื้อมไม่ถึง): {}".format(
                       STALE_DAYS,
                       " · ".join("{} ({}× {})".format(
                           e["name"], e["calls"],
                           "{}d".format(e["age"]) if e["age"] is not None else "?")
                           for e in off)))
    out.append("            เรียกเองไม่ได้ = ถอนทิ้ง (owner 2026-08-27: "
               "'ทั้งหมดนี้คุณต้องเป็นคนเรียกใช้เองเมื่อต้องใช้')")
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # The report is Thai and this machine's console is cp1252; a section that CRASHES on
    # its own text is worse than one that prints a box glyph, and plan_status calls this
    # in-process where an exception would take the whole session brief down with it.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    mode = argv[0] if argv else "report"
    if mode in ("hook", "session"):
        try:
            payload = json.load(sys.stdin)
        except Exception:
            return 0
        try:
            (hook if mode == "hook" else session_stamp)(payload)
        except Exception:
            return 0
        return 0
    if mode == "selftest":
        probe = {"tool_name": "Skill", "tool_input": {"skill": "__selftest__"},
                 "session_id": "selftest"}
        before = len(read_rows())
        hook(probe)
        after = len(read_rows())
        ok = after == before + 1
        print("selftest: write path {} ({} -> {} rows in {})".format(
            "OK" if ok else "BROKEN", before, after, os.path.relpath(LOG, REPO)))
        print("  a __selftest__ row proves THIS FILE works. It does NOT prove the hook is")
        print("  wired — only a real Skill/Agent call or a session stamp does that.")
        return 0 if ok else 1
    if mode == "report":
        print("\n".join(report_lines()).lstrip("\n"))
        return 0
    print(__doc__.splitlines()[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
