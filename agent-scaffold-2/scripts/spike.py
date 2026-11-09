#!/usr/bin/env python3
"""Spike (scratch) lifecycle. A spike is a folder under agents/scratch/ that is NOT authoritative.

  spike.py new <slug> [--goal "..."] [--exit "..."] [--question <id>] [--by name]
  spike.py list
  spike.py show <slug>            # for the curator: spike.md + TENTATIVE lines + file listing
  spike.py note <slug> --by name --note "..."        # append a one-line working note
  spike.py tentative <slug> --by name --text "..."   # record a tentative decision, one line
  spike.py close <slug> --outcome harvested|discarded --by name [--note "..."]
        # moves the folder to agents/.trash/<date>-<slug>/ (soft delete; lint purges after 30 days)

Workers create spikes freely ("no template for it -> scratch"). Only a curator closes one.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def spike_dir(L: C.Layout, slug: str) -> Path:
    # accept either the full folder name or just the slug part
    if (L.scratch / slug).is_dir():
        return L.scratch / slug
    hits = [d for d in L.scratch.iterdir() if d.is_dir() and d.name.endswith("-" + slug)] if L.scratch.exists() else []
    if len(hits) == 1:
        return hits[0]
    if not hits:
        C.die(f"no spike named {slug}")
    C.die(f"ambiguous spike name {slug}: " + ", ".join(h.name for h in hits))
    raise SystemExit


def cmd_new(L, a):
    name = f"{C.today()}-{C.slugify(a.slug)}"
    d = L.scratch / name
    if d.exists():
        C.die(f"spike exists: {L.rel(d)}")
    d.mkdir(parents=True)
    fm = {"slug": name, "created": C.today(), "by": a.by, "status": "open"}
    if a.question:
        fm["question"] = a.question
    body = (f"# Spike: {a.slug}\n\n**Goal:** {a.goal or '<one line>'}\n\n"
            f"**Exit condition:** {a.exit or '<when is this done or dropped?>'}\n\n"
            "Not authoritative. Nothing here is in force until harvested into agents/registers/.\n\n"
            "## Tentative decisions (one line each, prefix TENTATIVE)\n\n"
            "## Notes (append, one line each)\n\n")
    C.write_entry(d / "spike.md", fm, body)
    L.log_line("SPIKE", a.by, L.rel(d), "opened")
    print(L.rel(d))


def cmd_list(L, a):
    if not L.scratch.exists():
        print("no spikes")
        return
    n_days = int(L.config.get("spike_inactive_days", 14))
    for d in sorted(p for p in L.scratch.iterdir() if p.is_dir()):
        age = C.days_since(C.newest_mtime(d))
        files, mb = C.folder_stats(d)
        flag = "STALE" if age > n_days else "open"
        print(f"{flag:5s} {d.name}  files={files} size={mb:.1f}MB idle={age:.1f}d")


def cmd_show(L, a):
    d = spike_dir(L, a.slug)
    sm = d / "spike.md"
    if sm.exists():
        print(sm.read_text(encoding="utf-8"))
    print("\n## TENTATIVE lines found")
    for p in d.rglob("*.md"):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lstrip().startswith(("- TENTATIVE", "TENTATIVE")):
                print(f"  {L.rel(p)}: {line.strip()}")
    print("\n## Files")
    for p in sorted(d.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(d)}  ({p.stat().st_size} B)")


def cmd_note(L, a):
    d = spike_dir(L, a.slug)
    C.append_line(d / "spike.md", f"- {C.now()} ({a.by}): {a.note}")
    print("noted")


def cmd_tentative(L, a):
    d = spike_dir(L, a.slug)
    C.append_line(d / "spike.md", f"- TENTATIVE {C.now()} ({a.by}): {a.text}")
    print("recorded as tentative")


def cmd_close(L, a):
    d = spike_dir(L, a.slug)
    L.trash.mkdir(parents=True, exist_ok=True)
    dest = L.trash / d.name  # folder name already carries its creation date
    n = 2
    while dest.exists():
        dest = L.trash / f"{d.name}-closed-{C.today()}-{n}"
        n += 1
    shutil.move(str(d), str(dest))
    L.log_line("SPIKE", a.by, L.rel(d), f"{a.outcome}: {a.note or ''}".strip())
    print(f"{a.outcome}: moved to {L.rel(dest)} (purged by lint after 30 days)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("slug"); s.add_argument("--goal"); s.add_argument("--exit")
    s.add_argument("--question"); s.add_argument("--by", default="session"); s.set_defaults(fn=cmd_new)
    s = sub.add_parser("list"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("show"); s.add_argument("slug"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("note"); s.add_argument("slug"); s.add_argument("--by", required=True); s.add_argument("--note", required=True); s.set_defaults(fn=cmd_note)
    s = sub.add_parser("tentative"); s.add_argument("slug"); s.add_argument("--by", required=True); s.add_argument("--text", required=True); s.set_defaults(fn=cmd_tentative)
    s = sub.add_parser("close"); s.add_argument("slug"); s.add_argument("--outcome", required=True, choices=["harvested", "discarded"])
    s.add_argument("--by", required=True); s.add_argument("--note"); s.set_defaults(fn=cmd_close)
    a = p.parse_args()
    L = C.Layout(C.find_root(a.root))
    a.fn(L, a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
