# The `agents/` folder — what it is, in plain words

This folder belongs to the AI agents working in this project. You never have to open it, but it
is yours to read. Everything outside `agents/` is for people: inputs, work results, deliverables.

**How saving works without you asking.** `AGENTS.md` at the project root is loaded into every
agent session. It says: nothing counts until it is in a file; every agent owns its own files; shared
lists are append-only; anything worth keeping is *proposed*, not written straight into the
knowledge base. A small script tells each session whether a cleanup is due.

**What is in here**

| Folder / file | Meaning |
|---|---|
| `STATUS.md` | Goal, current position, checkpoints, who works on what. Read this first if you want to know where things stand. |
| `LOG.md` | One line per thing an agent did. Read from the bottom. |
| `registers/decisions/` | One file per decision that someone could later undo without knowing why. `INDEX.md` is generated; it lists only decisions in force. |
| `registers/lessons/` | What agents learned the hard way, incl. your corrections as standing rules. Also indexed. |
| `registers/examples/` | The current best example of each kind of output, one per name, no versions. |
| `registers/questions.md`, `sources.md`, `glossary.md` | Open questions, every source used, one meaning per term. |
| `inbox/` | Proposals waiting for a curator. `tentative` entries already work; only flagged ones need your yes. |
| `scratch/` | Unfinished experiments ("spikes"). Not authoritative. Gets cleaned up. |
| `templates/`, `scripts/`, `roles/` | What agents copy, what they run, how each role behaves. |

**What you do**

- When an agent ends a reply with "cleanup is due — start a curator run?", say yes when convenient.
  It takes a few minutes and ends with a short digest; you answer yes/no to the items it held for you.
- Correct an agent once; it should propose a standing rule. If it keeps happening, ask for a curator run.
- `python3 -I agents/scripts/status.py` shows the state in one line; `lint.py` shows what is messy.

Created {{DATE}} with the agent-scaffold skill, profile `{{PROFILE}}`. The folder works without that skill installed.
