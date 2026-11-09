#!/usr/bin/env python3
"""Scaffold (or upgrade) a project's agents/ structure. Never overwrites an existing file.

  init.py --profile research-case|code-repo|procedure|maker --target <dir> --name "..." \
          --purpose "..." --deliverable "..." --deadline "..." --owner "..." \
          [--lang-files English] [--lang-chat "German or English"] [--human-lang de|en] \
          [--out-of-scope "..."] [--confidentiality "..."] \
          [--verify-command "..."] [--machine-facts "..."] [--skill-slug name] [--dry-run]

Seeds structure and templates only — never content. Anything derivable from the project's inputs
(brief, questions, glossary terms) is written by the agent afterwards, into the work folders.
Re-running on an existing project adds what is missing and reports what it skipped (upgrade).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

SCRIPTS = ["common.py", "append.sh", "propose.py", "promote.py", "index.py", "status.py", "lint.py", "spike.py", "inventory.py"]
AGENT_DIRS = ["registers/decisions", "registers/lessons", "registers/examples", "inbox", "scratch", "templates", "scripts", "roles", "adapters/claude"]
KEEP_DIRS = ["registers/decisions", "registers/lessons", "registers/examples", "inbox"]


class Plan:
    def __init__(self, target: Path, dry: bool):
        self.target, self.dry = target, dry
        self.created: list[str] = []
        self.skipped: list[str] = []
        self.notes: list[str] = []

    def rel(self, p: Path) -> str:
        return str(p.relative_to(self.target))

    def mkdir(self, rel: str):
        p = self.target / rel
        if p.exists():
            return
        self.created.append(rel + "/")
        if not self.dry:
            p.mkdir(parents=True, exist_ok=True)

    def write(self, rel: str, text: str, executable: bool = False):
        p = self.target / rel
        if p.exists():
            self.skipped.append(rel)
            return
        self.created.append(rel)
        if not self.dry:
            C.atomic_write(p, text)
            if executable:
                p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def copy(self, src: Path, rel: str, executable: bool = False):
        self.write(rel, src.read_text(encoding="utf-8"), executable)

    def append_missing_lines(self, rel: str, lines: list[str], header: str = ""):
        p = self.target / rel
        existing = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
        missing = [l for l in lines if l not in existing]
        if not missing:
            return
        self.created.append(f"{rel} (+{len(missing)} lines)")
        if not self.dry:
            with open(p, "a", encoding="utf-8") as fh:
                if existing and existing[-1].strip():
                    fh.write("\n")
                if header:
                    fh.write(header + "\n")
                fh.write("\n".join(missing) + "\n")


def render(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, choices=[p.stem for p in (SKILL / "profiles").glob("*.json")])
    ap.add_argument("--target", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--purpose", required=True)
    ap.add_argument("--deliverable", required=True)
    ap.add_argument("--deadline", default="none stated")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--lang-files", default="English")
    ap.add_argument("--lang-chat", default="German or English")
    ap.add_argument("--human-lang", choices=["de", "en"], default="de")
    ap.add_argument("--out-of-scope", default="nothing stated")
    ap.add_argument("--confidentiality", default="")
    ap.add_argument("--verify-command", default="<set the verify command>")
    ap.add_argument("--machine-facts", default="<machine, nozzles, plate, materials — fill in>")
    ap.add_argument("--skill-slug", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    target = Path(a.target).expanduser().resolve()
    if not target.is_dir():
        C.die(f"target is not a directory: {target}")
    profile = json.loads((SKILL / "profiles" / f"{a.profile}.json").read_text(encoding="utf-8"))
    section = (SKILL / "profiles" / profile["section_file"]).read_text(encoding="utf-8").rstrip("\n")
    plan = Plan(target, a.dry_run)

    ctx = {
        "PROJECT_NAME": a.name, "PURPOSE": a.purpose, "DELIVERABLE": a.deliverable, "DEADLINE": a.deadline,
        "OWNER": a.owner, "LANGUAGE_FILES": a.lang_files, "LANGUAGE_CHAT": a.lang_chat, "HUMAN_LANG": a.human_lang,
        "OUT_OF_SCOPE": a.out_of_scope, "PROFILE": a.profile, "DATE": C.today(),
        "SPIKE_DAYS": profile["spike_inactive_days"],
        "CONFIDENTIALITY": f"- Confidentiality: {a.confidentiality}" if a.confidentiality else "",
        "VERIFY_COMMAND": a.verify_command, "MACHINE_FACTS": a.machine_facts,
        "SKILL_SLUG": a.skill_slug or C.slugify(a.name),
        "WORK_FOLDERS_JSON": json.dumps(profile["work_folders"], ensure_ascii=False),
        "GATE_DIRS_JSON": json.dumps(profile["output_dirs_for_gate"]),
    }
    ctx["PROFILE_SECTION"] = render(section, ctx)

    # 1. folders
    for d in AGENT_DIRS:
        plan.mkdir(f"agents/{d}")
    for d in profile["work_folders"]:
        plan.mkdir(d)
    for d in KEEP_DIRS:
        plan.write(f"agents/{d}/.gitkeep", "")

    # 2. config, entry files, status, readme
    plan.write("agents/config.json", render((SKILL / "templates/config.json").read_text(encoding="utf-8"), ctx))
    plan.write("AGENTS.md", render((SKILL / "templates/AGENTS.md.tmpl").read_text(encoding="utf-8"), ctx))
    claude = target / "CLAUDE.md"
    if claude.exists():
        if "@AGENTS.md" not in claude.read_text(encoding="utf-8"):
            plan.notes.append("CLAUDE.md exists and does not import AGENTS.md — add a line `@AGENTS.md` to it (not done automatically).")
        plan.skipped.append("CLAUDE.md")
    else:
        plan.write("CLAUDE.md", "@AGENTS.md\n\n<!-- Single entry file for every tool. Add Claude-only notes below this line; keep project rules in AGENTS.md. -->\n")
    plan.write("agents/STATUS.md", render((SKILL / "templates/STATUS.md").read_text(encoding="utf-8"), ctx))
    plan.write("agents/README.md", render((SKILL / f"templates/agents-README.{a.human_lang}.md").read_text(encoding="utf-8"), ctx))
    plan.write("agents/LOG.md", (SKILL / "templates/registers/LOG.md").read_text(encoding="utf-8"))

    # 3. registers, templates, roles
    for name in ("questions.md", "sources.md", "glossary.md"):
        plan.copy(SKILL / "templates/registers" / name, f"agents/registers/{name}")
    for name in ("decision.md", "lesson.md"):
        plan.copy(SKILL / "templates/entries" / name, f"agents/templates/{name}")
    for src, dest in profile.get("extra_templates", {}).items():
        plan.write(dest, render((SKILL / "templates" / src).read_text(encoding="utf-8"), ctx))
    for role in ("worker.md", "curator.md", "verifier.md"):
        plan.copy(SKILL / "templates/roles" / role, f"agents/roles/{role}")

    # 4. scripts (copied, so the project works without the skill)
    for s in SCRIPTS:
        plan.copy(HERE / s, f"agents/scripts/{s}", executable=True)

    # 5. adapters
    for f in (SKILL / "adapters/claude").iterdir():
        if not f.is_file() or f.name.startswith("."):  # skip __pycache__/ and dotfiles
            continue
        plan.copy(f, f"agents/adapters/claude/{f.name}", executable=f.suffix == ".py")
    plan.copy(SKILL / "adapters/codex/README.md", "agents/adapters/codex-README.md")
    settings = target / ".claude" / "settings.json"
    if settings.exists():
        plan.notes.append("`.claude/settings.json` exists — merge the hooks from `agents/adapters/claude/settings.json` by hand.")
    else:
        plan.write(".claude/settings.json", (SKILL / "adapters/claude/settings.json").read_text(encoding="utf-8"))

    # 6. git
    if (target / ".git").exists():
        snippet = (SKILL / "templates/gitignore.snippet").read_text(encoding="utf-8").splitlines()
        plan.append_missing_lines(".gitignore", [l for l in snippet if l and not l.startswith("#")], header="# agent-scaffold")

    # report
    print(("DRY RUN — " if a.dry_run else "") + f"profile {a.profile} → {target}")
    for c in plan.created:
        print("  + " + c)
    for s in plan.skipped:
        print("  = kept " + s)
    for n in plan.notes:
        print("  ! " + n)
    if not a.dry_run:
        subprocess.run([sys.executable, "-I", str(target / "agents/scripts/index.py"), "--root", str(target)], check=False)
        # first lint run: records .lint-last.json so a fresh project does not nudge for cleanup on day one
        subprocess.run([sys.executable, "-I", str(target / "agents/scripts/lint.py"), "--root", str(target)], check=False,
                       stdout=subprocess.DEVNULL)
        C.append_line(target / "agents/LOG.md", f"| INIT | {C.now()} | agent-scaffold | profile {a.profile} | {len(plan.created)} created, {len(plan.skipped)} kept |")
        leftovers = []
        for rel in ("AGENTS.md", "agents/STATUS.md"):
            t = (target / rel).read_text(encoding="utf-8")
            if "{{" in t or "<set " in t or "fill in" in t:
                leftovers.append(rel)
        if leftovers:
            print("  ! placeholders left in: " + ", ".join(leftovers) + " — fill them from the project's inputs now")
    print("\nNext: fill `agents/STATUS.md` from the inputs; derive context files into the work folders; "
          "never seed decisions, lessons or questions the project has not produced. Then run `agents/scripts/status.py`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
