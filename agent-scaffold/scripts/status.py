#!/usr/bin/env python3
"""Session-start status. Deterministic, ~5 lines, decides whether a cleanup nudge is due.

  status.py              # print summary; last line is NUDGE: yes|no
  status.py --snooze     # the human said "not now": store the current snapshot
  status.py --nudged     # record that a nudge was shown this session
  status.py --json

Levels: OK, DUE, CRITICAL. A nudge is shown when DUE and the picture moved materially since
the last nudge/snooze (any value up >= 50 %, or a quiet trigger now fires). CRITICAL ignores
snoozes. Thresholds live in agents/config.json ("thresholds").
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

DEFAULTS = {
    "inbox_items": 5, "inbox_oldest_days": 7, "spike_inactive_days": 14,
    "scratch_files": 200, "scratch_mb": 200, "lint_max_age_days": 14, "lint_open_findings": 5, "entry_max_lines": 200,
    "critical_inbox_items": 15, "critical_scratch_factor": 3,
}


def snapshot(L: C.Layout) -> dict:
    th = {**DEFAULTS, **L.config.get("thresholds", {})}
    th["spike_inactive_days"] = int(L.config.get("spike_inactive_days", th["spike_inactive_days"]))
    inbox = [p for p in L.inbox.glob("*.md")] if L.inbox.exists() else []
    inbox_oldest = max((C.days_since(p.stat().st_mtime) for p in inbox), default=0.0)
    flagged_conflicts = 0
    for p in inbox:
        fm, _ = C.read_entry(p)
        if fm.get("contradicts") or fm.get("supersedes"):
            flagged_conflicts += 1
    spikes = [d for d in L.scratch.iterdir() if d.is_dir()] if L.scratch.exists() else []
    stale_spikes = [d.name for d in spikes if C.days_since(C.newest_mtime(d)) > th["spike_inactive_days"]]
    s_files, s_mb = C.folder_stats(L.scratch)
    # index staleness: any register entry newer than its INDEX.md
    index_stale = False
    for folder in (L.decisions, L.lessons, L.examples):
        idx = folder / "INDEX.md"
        if folder.exists():
            newest = max((p.stat().st_mtime for p in folder.iterdir() if p.name != "INDEX.md"), default=0)
            if newest and (not idx.exists() or idx.stat().st_mtime < newest):
                index_stale = True
    lint = C.load_json(L.lint_last, {}) or {}
    lint_age = C.days_since(lint["ran_at_ts"]) if lint.get("ran_at_ts") else 999.0
    lint_open = int(lint.get("findings", 0))
    entry_lines = len(L.entry.read_text(encoding="utf-8").splitlines()) if L.entry.exists() else 0
    snap = {
        "inbox_items": len(inbox), "inbox_oldest_days": round(inbox_oldest, 1), "inbox_conflicts": flagged_conflicts,
        "spikes": len(spikes), "stale_spikes": len(stale_spikes), "stale_spike_names": stale_spikes,
        "scratch_files": s_files, "scratch_mb": round(s_mb, 1), "index_stale": index_stale,
        "lint_age_days": round(lint_age, 1), "lint_open_findings": lint_open, "entry_lines": entry_lines,
    }
    due = {
        "inbox": snap["inbox_items"] >= th["inbox_items"] or snap["inbox_oldest_days"] > th["inbox_oldest_days"],
        "spikes": snap["stale_spikes"] > 0,
        "scratch": snap["scratch_files"] > th["scratch_files"] or snap["scratch_mb"] > th["scratch_mb"],
        "index": index_stale,
        "lint": lint_age > th["lint_max_age_days"] or lint_open >= th["lint_open_findings"],
        "entry": entry_lines > th["entry_max_lines"],
    }
    critical = {
        "inbox": snap["inbox_items"] >= th["critical_inbox_items"],
        "scratch": snap["scratch_files"] > th["scratch_files"] * th["critical_scratch_factor"] or snap["scratch_mb"] > th["scratch_mb"] * th["critical_scratch_factor"],
        "conflict": flagged_conflicts > 0,
    }
    snap["due"] = [k for k, v in due.items() if v]
    snap["critical"] = [k for k, v in critical.items() if v]
    snap["level"] = "CRITICAL" if snap["critical"] else ("DUE" if snap["due"] else "OK")
    return snap


def moved_materially(prev: dict, cur: dict) -> bool:
    if not prev:
        return True
    for k in ("inbox_items", "stale_spikes", "scratch_files", "scratch_mb", "lint_open_findings", "entry_lines"):
        a, b = float(prev.get(k, 0) or 0), float(cur.get(k, 0) or 0)
        if b > 0 and (a == 0 or b >= a * 1.5):
            return True
    if set(cur.get("due", [])) - set(prev.get("due", [])):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snooze", action="store_true")
    ap.add_argument("--nudged", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root")
    a = ap.parse_args()
    L = C.Layout(C.find_root(a.root))
    cur = snapshot(L)
    state = C.load_json(L.nudge, {}) or {}
    if a.snooze or a.nudged:
        state = {"at": C.now(), "kind": "snooze" if a.snooze else "nudged", "snapshot": cur}
        C.save_json(L.nudge, state)
        print("recorded", state["kind"])
        return 0
    prev = state.get("snapshot", {})
    nudge = cur["level"] == "CRITICAL" or (cur["level"] == "DUE" and moved_materially(prev, cur))
    cur["nudge"] = nudge
    if a.json:
        print(json.dumps(cur, indent=2))
        return 0
    print(f"{cur['level']}  inbox={cur['inbox_items']} (oldest {cur['inbox_oldest_days']}d, conflicts {cur['inbox_conflicts']})  "
          f"spikes={cur['spikes']} stale={cur['stale_spikes']}  scratch={cur['scratch_files']} files/{cur['scratch_mb']}MB  "
          f"index_stale={cur['index_stale']}  lint_age={cur['lint_age_days']}d open={cur['lint_open_findings']}  entry_lines={cur['entry_lines']}")
    if cur["due"]:
        print("due:", ", ".join(cur["due"]), ("| critical: " + ", ".join(cur["critical"])) if cur["critical"] else "")
    if cur["stale_spike_names"]:
        print("stale spikes:", ", ".join(cur["stale_spike_names"]))
    print("NUDGE:", "yes" if nudge else "no")
    return 0


if __name__ == "__main__":
    sys.exit(main())
