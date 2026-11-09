#!/usr/bin/env python3
"""Claude Code SubagentStop hook: a subagent may stop only after it saved something.

Passes when the subagent's transcript shows a Write/Edit into one of the project's gate dirs
(agents/config.json "gate_dirs") or into agents/inbox|scratch, or a Bash call to propose.py /
spike.py / append.sh. Otherwise exits 2 with the rule text, and Claude Code feeds that back to the
subagent, which keeps working. `stop_hook_active` guards against loops: blocks at most once.
Any internal error lets the agent stop (exit 0). Optional adapter; the rule itself is in AGENTS.md §3.
"""
import json
import os
import re
import sys


def find_root(start):
    p = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(p, "agents", "config.json")):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent


try:
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        sys.exit(0)
    root = find_root(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    tpath = data.get("agent_transcript_path") or data.get("transcript_path")
    if not root or not tpath or not os.path.exists(tpath):
        sys.exit(0)
    with open(os.path.join(root, "agents", "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    dirs = [d.strip("/") for d in cfg.get("gate_dirs", [])] + ["agents/inbox", "agents/scratch"]
    dir_re = re.compile(r"(?:^|/)(?:" + "|".join(re.escape(d) for d in dirs) + r")/[^\"'\s\\]+")
    cmd_re = re.compile(r"(propose\.py|spike\.py|append\.sh)\b")
    saved = False
    with open(tpath, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name", "")
                inp = block.get("input") or {}
                if name in ("Write", "Edit", "MultiEdit") and dir_re.search(str(inp.get("file_path", ""))):
                    saved = True
                elif name == "Bash" and (cmd_re.search(str(inp.get("command", ""))) or dir_re.search(str(inp.get("command", "")))):
                    saved = True
                if saved:
                    break
            if saved:
                break
    if saved:
        sys.exit(0)
    sys.stderr.write(
        "Project rule (AGENTS.md §3): nothing exists until it is in a file. No write into "
        + ", ".join(dirs) + " was found in your work. Save your result now — your owned file in the work "
        "folder for your task, or a spike via agents/scripts/spike.py if it is unfinished, or a proposal via "
        "agents/scripts/propose.py — then append your DONE line to agents/LOG.md with agents/scripts/append.sh "
        "and report in the shape from AGENTS.md §3. A documented 'not found' is a valid result.\n"
    )
    sys.exit(2)
except SystemExit:
    raise
except Exception:
    sys.exit(0)
