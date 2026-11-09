#!/usr/bin/env python3
"""Lint the agents/ structure. Reports findings with a suggested verdict; changes nothing
except purging agents/.trash/ entries older than 30 days when --purge-trash is given.

  lint.py [--json] [--strict] [--purge-trash]

Verdict vocabulary (Every's refresh outcomes): KEEP, UPDATE, CONSOLIDATE, REPLACE, DELETE.
Checks: dead path references, register frontmatter/date/duplicates, stale indexes, examples
without sidecar (and vice versa), inbox age, direct-written entries nobody reviewed, stale spikes, scratch size, trash age, entry-file
length, lessons marked harmful, references to superseded entries, placeholders left in files.
Writes agents/.lint-last.json so status.py knows when lint last ran and how much is open.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

PATH_RE = re.compile(r"`([^`\s]+/[^`\s]*|[^`\s]+\.(?:md|py|sh|json|yaml|yml|toml|txt|csv))`")
# in-force register entries: angle-bracket template placeholders are leftovers
PLACEHOLDER_RE = re.compile(r"<[a-z][^<>\n]{2,60}>|\{\{[A-Z_]+\}\}|TODO:|TBD")
# entry file: only fill-in markers count; `<kind>`-style instruction placeholders are intentional
ENTRY_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_]+\}\}|<set [^>]*>|fill in|TODO:|TBD")
SKIP_PREFIX = ("http://", "https://", "mailto:", "<", "{{", "$", "~", "@")
SKIP_INSIDE = ("…", "...", "<", "*", "{{")
# names that legitimately exist only later (created per spike / per project)
CREATED_LATER = {"spike.md", "PROJECT.md", "handoff.md", "INDEX.md"}


class Finding:
    def __init__(self, code, path, msg, verdict):
        self.code, self.path, self.msg, self.verdict = code, path, msg, verdict

    def as_dict(self):
        return {"code": self.code, "path": self.path, "message": self.msg, "verdict": self.verdict}

    def __str__(self):
        return f"[{self.verdict:11s}] {self.code:18s} {self.path}: {self.msg}"


def md_files(L: C.Layout, skip=(".trash", "scratch", "inbox")):
    yield L.entry
    for p in L.agents.rglob("*.md"):
        if any(s in p.parts for s in skip):
            continue
        yield p


def known_basenames(L: C.Layout) -> set[str]:
    names = set()
    for p in L.root.iterdir():
        names.add(p.name)
    for p in L.agents.rglob("*"):
        if ".trash" in p.parts:
            continue
        names.add(p.name)
    return names | CREATED_LATER


def check_paths(L, F):
    """Dead references. Checked in AGENTS.md, agents/README.md, STATUS.md, roles/, registers/.
    Not checked: templates/ (intentional placeholders) and adapters/ (generic harness notes)."""
    names = known_basenames(L)
    for p in md_files(L, skip=(".trash", "scratch", "inbox", "templates", "adapters")):
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in PATH_RE.finditer(text):
            ref = m.group(1)
            if ref.startswith(SKIP_PREFIX) or any(s in ref for s in SKIP_INSIDE):
                continue
            ref_clean = ref.split("#")[0].rstrip("/")
            if "/" not in ref_clean:
                if ref_clean in names:
                    continue
                F.append(Finding("dead-path", L.rel(p), f"`{ref}` not found anywhere in the project", "UPDATE"))
                continue
            cands = [L.root / ref_clean, p.parent / ref_clean, L.agents / ref_clean]
            if not any(c.exists() for c in cands):
                F.append(Finding("dead-path", L.rel(p), f"`{ref}` does not exist", "UPDATE"))


def check_registers(L, F):
    r = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("index.py")), "--check", "--root", str(L.root)],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("problem:"):
            F.append(Finding("register", "agents/registers", line[len("problem:"):].strip(), "UPDATE"))
        elif line.startswith("stale:"):
            F.append(Finding("index-stale", line[len("stale:"):].strip(), "regenerate with index.py", "UPDATE"))
    # harmful lessons, superseded references, placeholders
    in_force = set()
    superseded = set()
    th = L.config.get("thresholds", {})
    review_days = int(th.get("direct_unreviewed_days", 14))
    mode = str(L.config.get("register_write", "inbox"))
    if mode not in ("inbox", "direct"):
        F.append(Finding("config", "agents/config.json", f'register_write is {mode!r}; must be inbox or direct', "UPDATE"))
    for folder in (L.decisions, L.lessons):
        if not folder.exists():
            continue
        for p in folder.glob("*.md"):
            if p.name == "INDEX.md":
                continue
            fm, body = C.read_entry(p)
            status = str(fm.get("status", "")).lower()
            (superseded if status == "superseded" else in_force).add(p.stem)
            if str(fm.get("attested", "")) == "author" and status not in ("superseded", "retired"):
                if mode != "direct":
                    F.append(Finding("direct-in-inbox-mode", L.rel(p), "written direct but register_write is inbox — attest or retire", "UPDATE"))
                age = C.days_since(p.stat().st_mtime)
                if age > review_days:
                    F.append(Finding("direct-unreviewed", L.rel(p), f"attested author for {age:.0f}d > {review_days}d — promote.py attest|retire", "UPDATE"))
            if int(fm.get("harmful", 0) or 0) > int(fm.get("helpful", 0) or 0) and int(fm.get("harmful", 0) or 0) > 0:
                F.append(Finding("harmful-lesson", L.rel(p), f"harmful={fm.get('harmful')} > helpful={fm.get('helpful')}", "REPLACE"))
            if PLACEHOLDER_RE.search(body) and str(fm.get("status", "")) != "proposed":
                F.append(Finding("placeholder", L.rel(p), "template placeholder left in an in-force entry", "UPDATE"))
    for p in md_files(L):
        if not p.exists() or p.name in ("INDEX.md", "LOG.md"):  # history and generated files may cite old entries
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, _ = C.parse_frontmatter(text)
        for s in superseded:
            if s in text and p.stem != s and str(fm.get("supersedes", "")) != s:
                F.append(Finding("cites-superseded", L.rel(p), f"references superseded entry {s}", "UPDATE"))


def check_scratch_inbox(L, F):
    th = L.config.get("thresholds", {})
    n_days = int(L.config.get("spike_inactive_days", 14))
    if L.scratch.exists():
        for d in L.scratch.iterdir():
            if d.is_dir():
                idle = C.days_since(C.newest_mtime(d))
                if idle > n_days:
                    F.append(Finding("stale-spike", L.rel(d), f"idle {idle:.0f}d > {n_days}d — harvest or discard", "DELETE"))
                if not (d / "spike.md").exists():
                    F.append(Finding("spike-no-goal", L.rel(d), "no spike.md (goal/exit missing)", "UPDATE"))
    files, mb = C.folder_stats(L.scratch)
    if files > int(th.get("scratch_files", 200)) or mb > float(th.get("scratch_mb", 200)):
        F.append(Finding("scratch-size", "agents/scratch", f"{files} files / {mb:.0f} MB", "CONSOLIDATE"))
    if L.inbox.exists():
        for p in L.inbox.glob("*.md"):
            age = C.days_since(p.stat().st_mtime)
            if age > int(th.get("inbox_oldest_days", 7)):
                F.append(Finding("inbox-age", L.rel(p), f"waiting {age:.0f}d", "UPDATE"))
    if L.trash.exists():
        for d in L.trash.iterdir():
            if C.days_since(d.stat().st_mtime) > 30:
                F.append(Finding("trash-old", L.rel(d), "older than 30d — purge with --purge-trash", "DELETE"))


def check_entry(L, F):
    if L.entry.exists():
        n = len(L.entry.read_text(encoding="utf-8").splitlines())
        mx = int(L.config.get("thresholds", {}).get("entry_max_lines", 200))
        if n > mx:
            F.append(Finding("entry-long", "AGENTS.md", f"{n} lines > {mx}: move detail to agents/ or a rule file", "CONSOLIDATE"))
        text = L.entry.read_text(encoding="utf-8")
        if ENTRY_PLACEHOLDER_RE.search(text):
            F.append(Finding("placeholder", "AGENTS.md", "fill-in placeholder still present ({{…}}, <set …>, fill in, TODO)", "UPDATE"))
    else:
        F.append(Finding("entry-missing", "AGENTS.md", "no entry file", "REPLACE"))
    status_md = L.status_file
    if status_md.exists() and ENTRY_PLACEHOLDER_RE.search(status_md.read_text(encoding="utf-8")):
        F.append(Finding("placeholder", "agents/STATUS.md", "fill-in placeholder still present", "UPDATE"))
    claude = L.root / "CLAUDE.md"
    if claude.exists() and "@AGENTS.md" not in claude.read_text(encoding="utf-8"):
        F.append(Finding("entry-drift", "CLAUDE.md", "does not import AGENTS.md — two entry files will drift", "UPDATE"))


def purge_trash(L) -> int:
    n = 0
    if L.trash.exists():
        for d in list(L.trash.iterdir()):
            if C.days_since(d.stat().st_mtime) > 30:
                shutil.rmtree(d) if d.is_dir() else d.unlink()
                n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 when findings exist")
    ap.add_argument("--purge-trash", action="store_true")
    ap.add_argument("--root")
    a = ap.parse_args()
    L = C.Layout(C.find_root(a.root))
    F: list[Finding] = []
    check_paths(L, F); check_registers(L, F); check_scratch_inbox(L, F); check_entry(L, F)
    purged = purge_trash(L) if a.purge_trash else 0
    C.save_json(L.lint_last, {"ran_at": C.now(), "ran_at_ts": dt.datetime.now().timestamp(), "findings": len(F),
                              "by_code": {c: sum(1 for f in F if f.code == c) for c in {f.code for f in F}}})
    if a.json:
        print(json.dumps([f.as_dict() for f in F], indent=2))
    else:
        for f in F:
            print(f)
        print(f"\n{len(F)} finding(s)" + (f", purged {purged} trash item(s)" if purged else ""))
    return 1 if (a.strict and F) else 0


if __name__ == "__main__":
    sys.exit(main())
