#!/usr/bin/env python3
"""Worker entry point: propose a decision, lesson, rule, example or question.

Writes ONE file into agents/inbox/. Workers never write into agents/registers/; the curator
promotes, merges or drops inbox items (see promote.py).

Usage:
  propose.py decision --title "..." --by <name> [--body "..."|--body-file f] [--supersedes <id>] [--replacement-cost low|medium|high]
  propose.py lesson   --title "..." --by <name> [--rung structure|check|rule|lesson] [--body ...] [--origin <spike-or-session>]
  propose.py rule     --title "..." --by <name> [--body ...]            # a one-line standing rule for AGENTS.md
  propose.py example  --title "..." --by <name> --file <path> [--settings k=v ...] [--source-url URL --publisher P --usage-basis "..."]
  propose.py question --title "..." --by <name> [--searched "..."] [--for who]   # appended to registers/questions.md directly (append-only register)

Flags that force human attention: --supersedes, --contradicts <id>, --scope (chosen for the user,
not with them), --replacement-cost high, --touches-entry (changes AGENTS.md). Set them honestly.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

KINDS = ("decision", "lesson", "rule", "example", "question")


def body_from(args) -> str:
    if getattr(args, "body_file", None):
        return Path(args.body_file).read_text(encoding="utf-8")
    return (getattr(args, "body", None) or "").strip() + "\n"


def needs_human(args) -> list[str]:
    reasons = []
    if getattr(args, "supersedes", None):
        reasons.append("supersedes an in-force entry")
    if getattr(args, "contradicts", None):
        reasons.append("contradicts an in-force entry")
    if getattr(args, "scope", False):
        reasons.append("chosen for the user, not with them")
    if getattr(args, "replacement_cost", "") == "high":
        reasons.append("high replacement cost")
    if getattr(args, "touches_entry", False) or args.kind == "rule":
        reasons.append("touches the root entry file")
    return reasons


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("kind", choices=KINDS)
    p.add_argument("--title", required=True)
    p.add_argument("--by", required=True, help="agent or session name")
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.add_argument("--refs", nargs="*", default=[], help="paths in the project or source ids")
    p.add_argument("--tags", nargs="*", default=[])
    p.add_argument("--origin", help="spike slug or session id this came from")
    # decision
    p.add_argument("--supersedes")
    p.add_argument("--contradicts")
    p.add_argument("--replacement-cost", choices=["low", "medium", "high"])
    p.add_argument("--scope", action="store_true")
    p.add_argument("--touches-entry", action="store_true")
    # lesson
    p.add_argument("--rung", choices=["structure", "check", "rule", "lesson"], default="lesson",
                   help="ladder rung you believe this belongs on (structure fix > check > rule > lesson)")
    # example
    p.add_argument("--file", help="example file to register (copied into inbox)")
    p.add_argument("--settings", nargs="*", default=[], help="k=v pairs stored in the sidecar")
    p.add_argument("--source-url")
    p.add_argument("--publisher")
    p.add_argument("--usage-basis")
    # question
    p.add_argument("--searched", default="")
    p.add_argument("--for", dest="for_whom", default="team")
    p.add_argument("--root")
    args = p.parse_args()

    L = C.Layout(C.find_root(args.root))
    slug = C.slugify(args.title)

    if args.kind == "question":
        # Questions are an append-only register, not inbox items: one line, cheap, visible at once.
        line = f"| {C.now()} | {args.by} | {args.title} | {args.searched} | {args.for_whom} | open |"
        C.append_line(L.questions, line)
        L.log_line("ASK", args.by, L.rel(L.questions), slug)
        print(f"question appended to {L.rel(L.questions)}")
        return 0

    L.inbox.mkdir(parents=True, exist_ok=True)
    stem = f"{C.today()}-{args.kind}-{slug}"
    path = L.inbox / f"{stem}.md"
    n = 2
    while path.exists():
        path = L.inbox / f"{stem}-{n}.md"
        n += 1

    fm = {
        "kind": args.kind,
        "title": args.title,
        "date": C.today(),
        "by": args.by,
        "status": "proposed",
        "refs": args.refs,
        "tags": args.tags,
    }
    if args.origin:
        fm["origin"] = args.origin
    reasons = needs_human(args)
    fm["needs"] = "human" if reasons else "curator"
    if reasons:
        fm["needs_human_because"] = reasons

    body = body_from(args)
    if args.kind == "decision":
        fm["replacement_cost"] = args.replacement_cost or "low"
        if args.supersedes:
            fm["supersedes"] = args.supersedes
        if args.contradicts:
            fm["contradicts"] = args.contradicts
        if not body.strip():
            body = ("## Context\n\n<why this came up>\n\n## Decision\n\n| What was chosen | Why, incl. what it beats | Replacement cost |\n"
                    "|---|---|---|\n| | | |\n\n## What this changed elsewhere\n\n<files, rules, docs>\n\n## Would reconsider if\n\n<condition>\n")
    elif args.kind == "lesson":
        fm["rung"] = args.rung
        fm["helpful"] = 0
        fm["harmful"] = 0
        if not body.strip():
            body = "## Symptom\n\n## What didn't work\n\n## What works\n\n## Why\n\n## When to apply\n"
    elif args.kind == "rule":
        if not body.strip():
            body = "<one-line standing rule, imperative, with the situation it applies to>\n"
    elif args.kind == "example":
        if not args.file:
            C.die("--file is required for examples")
        src = Path(args.file)
        if not src.is_file():
            C.die(f"example file not found: {src}")
        dest = L.inbox / f"{stem}{src.suffix.lower()}"
        shutil.copy2(src, dest)
        fm["file"] = dest.name
        fm["settings"] = {}
        settings = {}
        for kv in args.settings:
            if "=" in kv:
                k, v = kv.split("=", 1)
                settings[k.strip()] = v.strip()
        # settings are stored as JSON sidecar next to the file so lint can check them
        sidecar = {
            "id": stem, "title": args.title, "file": dest.name, "created": C.today(), "by": args.by,
            "settings": settings,
            "provenance": {k: v for k, v in {"source_url": args.source_url, "publisher": args.publisher,
                                              "usage_basis": args.usage_basis}.items() if v},
        }
        C.save_json(L.inbox / f"{stem}.json", sidecar)
        del fm["settings"]
        if not body.strip():
            body = "<what this example demonstrates and why it is the current best>\n"

    C.write_entry(path, fm, body)
    L.log_line("PROPOSE", args.by, L.rel(path), ",".join(reasons) if reasons else "curator")
    print(L.rel(path))
    if reasons:
        print("flagged for human attention: " + "; ".join(reasons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
