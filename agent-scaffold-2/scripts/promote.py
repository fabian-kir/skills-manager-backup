#!/usr/bin/env python3
"""Curator entry point: empty the inbox into the registers, review direct-written entries.

  promote.py list                              # inbox items, flagged ones first
  promote.py show <item>                       # print one item
  promote.py accept <item> --by <name> [--as tentative|confirmed] [--attested curator|human] [--merge-into <id>]
  promote.py drop <item> --by <name> --reason "..."
  promote.py unreviewed                        # register entries written direct (attested: author), oldest first
  promote.py attest <register/id> --by <name>  # curator reviewed a direct entry: attested author -> curator
  promote.py retire <register/id> --by <name> --reason "..."   # a direct entry that fails the trigger: out of force, kept
  promote.py mark <register/id> --helpful|--harmful --by <name>   # usefulness counters on lessons
  promote.py confirm <register/id> --by <human>                   # human only: tentative -> confirmed
  promote.py supersede <old-id> --with <new-id> --by <name>       # sets relations on the old record

Rules enforced here (not left to judgment):
  - items with needs: human are refused unless --attested human (the human said yes)
  - accepted decisions/lessons default to status tentative — in force, unconfirmed
  - a `rule` becomes a lesson with rung=rule; the curator edits AGENTS.md by hand afterwards
  - entries are never deleted: retire sets status retired (out of the index) and keeps the file
  - indexes are regenerated after every change
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def inbox_items(L: C.Layout) -> list[Path]:
    if not L.inbox.exists():
        return []
    return sorted(p for p in L.inbox.iterdir() if p.suffix == ".md")


def find_item(L: C.Layout, name: str) -> Path:
    p = L.inbox / name
    if not p.suffix:
        p = p.with_suffix(".md")
    if not p.is_file():
        hits = [q for q in inbox_items(L) if name in q.stem]
        if len(hits) == 1:
            return hits[0]
        C.die(f"inbox item not found or ambiguous: {name}")
    return p


def register_entries(L: C.Layout) -> list[Path]:
    out = []
    for folder in (L.decisions, L.lessons):
        if folder.exists():
            out += [p for p in folder.glob("*.md") if p.name != "INDEX.md"]
    return sorted(out)


def find_register_entry(L: C.Layout, ref: str) -> Path:
    """ref like 'decisions/2026-11-09-slug' or just the stem."""
    cands = [p for p in register_entries(L) if p.stem == ref or f"{p.parent.name}/{p.stem}" == ref]
    if len(cands) != 1:
        C.die(f"register entry not found or ambiguous: {ref}")
    return cands[0]


def reindex(L: C.Layout) -> None:
    r = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("index.py")), "--root", str(L.root)],
                       check=False, capture_output=True, text=True)
    for line in (r.stdout + r.stderr).splitlines():
        if line.startswith("problem:"):
            print(line)


def cmd_list(L, a):
    items = inbox_items(L)
    if not items:
        print("inbox empty")
    rows = []
    for p in items:
        fm, _ = C.read_entry(p)
        rows.append((0 if fm.get("needs") == "human" else 1, p.name, fm))
    for _, name, fm in sorted(rows):
        flag = "HUMAN " if fm.get("needs") == "human" else "      "
        why = "; ".join(fm.get("needs_human_because", [])) if isinstance(fm.get("needs_human_because"), list) else ""
        print(f"{flag}{fm.get('kind', '?'):8s} {name}  — {fm.get('title', '')}  {('[' + why + ']') if why else ''}")
    n = len(unreviewed(L))
    if n:
        print(f"\n{n} direct-written entr{'y' if n == 1 else 'ies'} await review: promote.py unreviewed")


def cmd_show(L, a):
    p = find_item(L, a.item)
    print(p.read_text(encoding="utf-8"))
    side = p.with_suffix(".json")
    if side.exists():
        print("\n--- sidecar ---\n" + side.read_text(encoding="utf-8"))


def cmd_accept(L, a):
    p = find_item(L, a.item)
    fm, body = C.read_entry(p)
    kind = fm.get("kind")
    if fm.get("needs") == "human" and a.attested != "human":
        C.die("this item needs human attestation; rerun with --attested human after the human said yes")
    status = a.status
    if a.merge_into:
        target = find_register_entry(L, a.merge_into)
        tfm, tbody = C.read_entry(target)
        tbody = tbody.rstrip("\n") + f"\n\n## Merged {C.today()} from inbox ({fm.get('by')})\n\n{fm.get('title')}\n\n" + body
        tfm["last_updated"] = C.today()
        C.write_entry(target, tfm, tbody)
        p.unlink()
        L.log_line("PROMOTE", a.by, L.rel(target), f"merged {p.name}")
        print(f"merged into {L.rel(target)}")
        reindex(L)
        return
    if kind in ("decision", "lesson", "rule"):
        folder = L.decisions if kind == "decision" else L.lessons
        folder.mkdir(parents=True, exist_ok=True)
        stem = f"{fm.get('date', C.today())}-{C.slugify(str(fm.get('title', p.stem)))}"
        dest = folder / f"{stem}.md"
        n = 2
        while dest.exists():
            dest = folder / f"{stem}-{n}.md"
            n += 1
        new_fm = {k: v for k, v in fm.items() if k not in ("needs", "needs_human_because", "kind")}
        new_fm["id"] = dest.stem
        new_fm["status"] = status
        new_fm["attested"] = a.attested
        new_fm["promoted"] = C.today()
        if kind == "rule":
            new_fm["rung"] = "rule"
            new_fm.setdefault("helpful", 0)
            new_fm.setdefault("harmful", 0)
            body = body.rstrip("\n") + "\n\n_Standing rule: add the one-line form to AGENTS.md (curator does this by hand)._\n"
        if kind == "decision" and fm.get("supersedes"):
            old = find_register_entry(L, str(fm["supersedes"]))
            ofm, obody = C.read_entry(old)
            ofm["status"] = "superseded"
            ofm["superseded_by"] = dest.stem
            C.write_entry(old, ofm, obody)
            print(f"marked superseded: {L.rel(old)}")
        C.write_entry(dest, new_fm, body)
        p.unlink()
        L.log_line("PROMOTE", a.by, L.rel(dest), f"{status}, attested {a.attested}")
        print(L.rel(dest))
    elif kind == "example":
        L.examples.mkdir(parents=True, exist_ok=True)
        side_src = p.with_suffix(".json")
        if not side_src.exists():
            C.die("example sidecar missing in inbox")
        side = json.loads(side_src.read_text(encoding="utf-8"))
        ex_id = a.example_id or C.slugify(str(fm.get("title", p.stem)))
        src_file = L.inbox / side["file"]
        dest_file = L.examples / f"{ex_id}{Path(side['file']).suffix}"
        if dest_file.exists():
            # one current-best per id: the new one replaces the old one
            prev = L.trash / f"{C.today()}-example-{dest_file.name}"
            L.trash.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest_file), str(prev))
            print(f"previous best moved to {L.rel(prev)}")
        shutil.move(str(src_file), str(dest_file))
        side.update({"id": ex_id, "file": dest_file.name, "status": "current", "attested": a.attested, "promoted": C.today(),
                     "notes": body.strip()})
        C.save_json(L.examples / f"{ex_id}.json", side)
        p.unlink(); side_src.unlink()
        L.log_line("PROMOTE", a.by, L.rel(dest_file), "example current")
        print(L.rel(dest_file))
    else:
        C.die(f"unknown kind {kind}")
    reindex(L)


def cmd_drop(L, a):
    p = find_item(L, a.item)
    for q in (p, p.with_suffix(".json")):
        if q.exists():
            q.unlink()
    side_files = [q for q in L.inbox.glob(p.stem + ".*") if q.suffix not in (".md", ".json")]
    for q in side_files:
        q.unlink()
    L.log_line("DROP", a.by, L.rel(p), a.reason)
    print(f"dropped {p.name}: {a.reason}")


# --- direct-written entries ------------------------------------------------------------------

def unreviewed(L: C.Layout) -> list[tuple[Path, dict]]:
    """Entries a worker wrote straight into a register (attested: author), oldest first."""
    out = []
    for p in register_entries(L):
        fm, _ = C.read_entry(p)
        if str(fm.get("attested", "")) == "author" and str(fm.get("status", "")) not in ("superseded", "retired"):
            out.append((p, fm))
    out.sort(key=lambda t: str(t[1].get("date", "")))
    return out


def cmd_unreviewed(L, a):
    rows = unreviewed(L)
    if not rows:
        print("no direct-written entries await review")
        return
    for p, fm in rows:
        flags = [k for k in ("supersedes", "contradicts") if fm.get(k)]
        print(f"{fm.get('date', '')}  {p.parent.name}/{p.stem}  — {fm.get('title', '')}  by {fm.get('by', '?')}"
              + (f"  [{', '.join(flags)}]" if flags else ""))
    print(f"\n{len(rows)} to review: promote.py attest <id> --by curator | promote.py retire <id> --by curator --reason ...")


def cmd_attest(L, a):
    """Curator reviewed a direct entry and it meets the trigger: attested author -> curator (status unchanged)."""
    p = find_register_entry(L, a.entry)
    fm, body = C.read_entry(p)
    if str(fm.get("attested", "")) != "author":
        C.die(f"{p.stem} is attested {fm.get('attested')!r}, not author; nothing to attest")
    fm["attested"] = "curator"
    fm["reviewed"] = C.today()
    C.write_entry(p, fm, body)
    L.log_line("ATTEST", a.by, L.rel(p), "author -> curator")
    print(f"{p.stem}: attested curator")
    reindex(L)


def cmd_retire(L, a):
    """Out of force, file kept. For a direct entry that fails the trigger, or any entry the human retires."""
    p = find_register_entry(L, a.entry)
    fm, body = C.read_entry(p)
    if str(fm.get("status", "")) in ("superseded", "retired"):
        C.die(f"{p.stem} is already {fm.get('status')}")
    fm["status"] = "retired"
    fm["retired"] = C.today()
    fm["retired_by"] = a.by
    fm["retired_because"] = a.reason
    C.write_entry(p, fm, body)
    L.log_line("RETIRE", a.by, L.rel(p), a.reason)
    print(f"{p.stem}: retired ({a.reason})")
    reindex(L)


def cmd_mark(L, a):
    p = find_register_entry(L, a.entry)
    fm, body = C.read_entry(p)
    key = "helpful" if a.helpful else "harmful"
    fm[key] = int(fm.get(key, 0) or 0) + 1
    if key == "harmful":
        fm["needs"] = "human"  # one harmful mark sends it back to the human
    C.write_entry(p, fm, body)
    L.log_line("MARK", a.by, L.rel(p), key)
    print(f"{L.rel(p)}: helpful={fm.get('helpful', 0)} harmful={fm.get('harmful', 0)}")
    reindex(L)


def cmd_confirm(L, a):
    """tentative → confirmed. Only the human confirms (attested: human); the curator never does."""
    p = find_register_entry(L, a.entry)
    fm, body = C.read_entry(p)
    if str(fm.get("status", "")) in ("superseded", "retired"):
        C.die(f"cannot confirm a {fm.get('status')} entry")
    fm["status"] = "confirmed"
    fm["attested"] = "human"
    fm["confirmed"] = C.today()
    fm.pop("needs", None)
    C.write_entry(p, fm, body)
    L.log_line("CONFIRM", a.by, L.rel(p), "human")
    print(f"{p.stem}: confirmed")
    reindex(L)


def cmd_supersede(L, a):
    old = find_register_entry(L, a.old)
    new = find_register_entry(L, a.new)
    ofm, obody = C.read_entry(old)
    ofm["status"] = "superseded"
    ofm["superseded_by"] = new.stem
    C.write_entry(old, ofm, obody)
    nfm, nbody = C.read_entry(new)
    nfm["supersedes"] = old.stem
    C.write_entry(new, nfm, nbody)
    L.log_line("SUPERSEDE", a.by, L.rel(old), f"by {new.stem}")
    print(f"{old.stem} superseded by {new.stem}")
    reindex(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("show"); s.add_argument("item"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("accept"); s.add_argument("item"); s.add_argument("--by", required=True)
    s.add_argument("--as", dest="status", choices=["tentative", "confirmed"], default="tentative")
    s.add_argument("--attested", choices=["curator", "human"], default="curator")
    s.add_argument("--merge-into"); s.add_argument("--example-id"); s.set_defaults(fn=cmd_accept)
    s = sub.add_parser("drop"); s.add_argument("item"); s.add_argument("--by", required=True); s.add_argument("--reason", required=True); s.set_defaults(fn=cmd_drop)
    s = sub.add_parser("unreviewed", help="direct-written entries awaiting curator review"); s.set_defaults(fn=cmd_unreviewed)
    s = sub.add_parser("attest", help="curator reviewed a direct entry: attested author -> curator"); s.add_argument("entry"); s.add_argument("--by", required=True); s.set_defaults(fn=cmd_attest)
    s = sub.add_parser("retire", help="take an entry out of force; the file stays"); s.add_argument("entry"); s.add_argument("--by", required=True); s.add_argument("--reason", required=True); s.set_defaults(fn=cmd_retire)
    s = sub.add_parser("mark"); s.add_argument("entry"); s.add_argument("--by", required=True)
    g = s.add_mutually_exclusive_group(required=True); g.add_argument("--helpful", action="store_true"); g.add_argument("--harmful", action="store_true")
    s.set_defaults(fn=cmd_mark)
    s = sub.add_parser("confirm", help="human only: tentative -> confirmed"); s.add_argument("entry"); s.add_argument("--by", required=True); s.set_defaults(fn=cmd_confirm)
    s = sub.add_parser("supersede"); s.add_argument("old"); s.add_argument("--with", dest="new", required=True); s.add_argument("--by", required=True); s.set_defaults(fn=cmd_supersede)
    a = ap.parse_args()
    L = C.Layout(C.find_root(a.root))
    a.fn(L, a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
