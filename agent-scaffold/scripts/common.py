#!/usr/bin/env python3
"""Shared helpers for agent-scaffold scripts. Stdlib only. Run scripts with `python3 -I`.

Project root = nearest ancestor of the current directory (or of --root) that contains
`agents/config.json`. Every script resolves paths through here so it works from any cwd.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

AGENTS_DIR = "agents"
CONFIG_NAME = "config.json"


def today() -> str:
    return _dt.date.today().isoformat()


def now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def die(msg: str, code: int = 2) -> None:
    sys.stderr.write(f"error: {msg}\n")
    sys.exit(code)


def find_root(start: str | os.PathLike | None = None) -> Path:
    p = Path(start or os.getcwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / AGENTS_DIR / CONFIG_NAME).is_file():
            return cand
    die(f"no agents/{CONFIG_NAME} found above {p}; run init first")
    raise SystemExit  # unreachable, keeps type checkers calm


def load_config(root: Path) -> dict:
    with open(root / AGENTS_DIR / CONFIG_NAME, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data: dict) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path, default=None):
    if not path.is_file():
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def slugify(text: str, max_len: int = 60) -> str:
    text = text.lower()
    text = re.sub(r"[äöüß]", lambda m: {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}[m.group()], text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len].rstrip("-") or "untitled"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def append_line(path: Path, line: str) -> None:
    """Single-line O_APPEND write; safe with many parallel writers."""
    if "\n" in line.rstrip("\n"):
        die("append_line: entry must be a single line")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (line.rstrip("\n") + "\n").encode("utf-8"))
    finally:
        os.close(fd)


# --- minimal frontmatter (subset of YAML: scalars, [a, b] lists, one level) ---------------

_FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


def _parse_scalar(v: str):
    v = v.strip()
    if v == "":
        return ""
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [] if not inner else [_parse_scalar(x) for x in inner.split(",")]
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _dump_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[" + ", ".join(_dump_scalar(x) for x in v) + "]"
    if v is None:
        return ""
    s = str(v)
    if s == "" or re.search(r"[:#\[\]{},]|^\s|\s$", s) or s.lower() in ("true", "false", "null"):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    data: dict = {}
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        data[k.strip()] = _parse_scalar(v)
    return data, text[m.end():]


def dump_frontmatter(data: dict, body: str) -> str:
    lines = ["---"] + [f"{k}: {_dump_scalar(v)}" for k, v in data.items()] + ["---", ""]
    return "\n".join(lines) + body.lstrip("\n")


def read_entry(path: Path) -> tuple[dict, str]:
    with open(path, encoding="utf-8") as fh:
        return parse_frontmatter(fh.read())


def write_entry(path: Path, data: dict, body: str) -> None:
    atomic_write(path, dump_frontmatter(data, body))


# --- project layout ------------------------------------------------------------------------

class Layout:
    def __init__(self, root: Path):
        self.root = root
        self.agents = root / AGENTS_DIR
        self.config = load_config(root)
        self.registers = self.agents / "registers"
        self.decisions = self.registers / "decisions"
        self.lessons = self.registers / "lessons"
        self.examples = self.registers / "examples"
        self.questions = self.registers / "questions.md"
        self.sources = self.registers / "sources.md"
        self.glossary = self.registers / "glossary.md"
        self.inbox = self.agents / "inbox"
        self.scratch = self.agents / "scratch"
        self.trash = self.agents / ".trash"
        self.log = self.agents / "LOG.md"
        self.status_file = self.agents / "STATUS.md"
        self.nudge = self.agents / ".nudge.json"
        self.lint_last = self.agents / ".lint-last.json"
        self.entry = root / "AGENTS.md"

    def rel(self, p: Path) -> str:
        try:
            return str(p.resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(p)

    def log_line(self, kind: str, who: str, what: str, note: str = "") -> None:
        append_line(self.log, f"| {kind} | {now()} | {who} | {what} | {note} |")


def newest_mtime(folder: Path) -> float:
    best = folder.stat().st_mtime if folder.exists() else 0.0
    for p in folder.rglob("*"):
        try:
            best = max(best, p.stat().st_mtime)
        except OSError:
            pass
    return best


def folder_stats(folder: Path) -> tuple[int, float]:
    """(file_count, size_mb)"""
    n, size = 0, 0
    if not folder.exists():
        return 0, 0.0
    for p in folder.rglob("*"):
        if p.is_file():
            n += 1
            try:
                size += p.stat().st_size
            except OSError:
                pass
    return n, size / (1024 * 1024)


def days_since(ts: float) -> float:
    return (_dt.datetime.now().timestamp() - ts) / 86400.0
