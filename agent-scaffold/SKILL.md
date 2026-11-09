---
name: agent-scaffold
description: Set up or maintain the agent knowledge structure of a project — an AGENTS.md entry file plus an agents/ folder with registers (decisions, lessons, examples, sources, questions), templates, scripts and roles — so every agent saves its findings automatically and knowledge carries between sessions and projects. Use when starting a project for agents, when a folder is messy and agents keep re-learning things, when asked to "scaffold", "set up the agents folder", "Struktur anlegen", run a "cleanup", "curator run" or "harvest a spike". Three modes - init, curate, harvest. Works for research cases, code repos, procedure skills and maker/hardware folders; harness-agnostic (Claude Code, Codex, Cursor).
---

# agent-scaffold

One skill, three modes. Everything it creates is copied into the project, so the project keeps
working without this skill installed.

| Mode | When | Read |
|---|---|---|
| **init** | a folder has no `AGENTS.md`/`agents/`, or has an older scaffold to upgrade | `references/init.md` |
| **curate** | the human says cleanup / curator run / aufräumen, or a session's `status.py` says `NUDGE: yes` and the human said yes | `references/curate.md` |
| **harvest** | a spike (scratch folder) is done, stale, or the human says "we're done with X" | `references/harvest.md` |

Shared structure and add-on contracts: `references/structure.md` and `references/addons.md`.

## Rules that hold in every mode

1. **Seed structure and templates, never content.** Decisions, lessons, questions and examples are earned by work; the scaffold does not invent them. Context derived from the project's own inputs (a brief, a glossary term, machine facts the human stated) is allowed — it is derived, not guessed.
2. **Never overwrite.** `init.py` skips existing files and says so. Upgrades add what is missing.
3. **Never move or delete the human's files without a dry run and an explicit yes.** `inventory.py` proposes; the human approves; then move.
4. **Ask the input contract in one batch, at most six questions**, then derive the rest (see `references/init.md`). Do not ask what the folder already tells you.
5. **The entry file stays a router, ≤ 200 lines.** Detail goes into `agents/` and loads on demand.
6. **Harness-agnostic.** `AGENTS.md` is the single entry file; `CLAUDE.md` only imports it. Enforcement is plain scripts; Claude hooks are optional adapters.
7. **Roles by invocation.** A session started for cleanup is the curator; everything else is a worker and only proposes. If you are a subagent or at reduced effort and are asked to curate, say so and stop.

## Quick commands (run from the project root, `python3 -I`)

```
agents/scripts/status.py                      one-line state; last line NUDGE: yes|no
agents/scripts/propose.py <kind> --title … --by …   worker: decision|lesson|rule|example|question
agents/scripts/spike.py new|list|show|tentative|note|close
agents/scripts/promote.py list|show|accept|drop|mark|supersede     curator only
agents/scripts/lint.py [--strict] [--purge-trash]
agents/scripts/index.py [--check]
agents/scripts/inventory.py                   loose files → proposed moves
```

Skill location note: `scripts/init.py` must be run from this skill directory (it copies from `../templates`, `../profiles`, `../adapters`):
`python3 -I <skill-dir>/scripts/init.py --profile <p> --target <dir> --name … --purpose … --deliverable … --owner … [--dry-run]`
