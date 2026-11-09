#!/usr/bin/env python3
"""Claude Code PostToolUse hook: log every Write/Edit/MultiEdit as an AUTO line in agents/LOG.md.

Optional adapter — the structure works without it (agents write DONE lines themselves).
Never blocks the tool call; any error is swallowed so logging can never stop an agent saving.
"""
import datetime
import json
import os
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
    tool = data.get("tool_name", "?")
    path = (data.get("tool_input") or {}).get("file_path", "")
    root = find_root(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    if not root or not path:
        sys.exit(0)
    rel = os.path.relpath(path, root)
    if rel.startswith("..") or rel.endswith("LOG.md") or os.path.basename(rel).startswith(".") or "/.trash/" in rel:
        sys.exit(0)
    who = (data.get("agent_type") or data.get("agent_name") or "session") + ":" + (data.get("session_id") or "")[:8]
    line = f"| AUTO | {datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')} | {who} | {rel} | {tool} |\n"
    log = os.path.join(root, "agents", "LOG.md")
    fd = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)
except Exception:
    pass
sys.exit(0)
