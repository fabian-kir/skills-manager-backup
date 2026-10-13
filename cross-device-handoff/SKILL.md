---
name: cross-device-handoff
description: Plan a feature on this machine and have it built, reviewed and merged on another machine the human also runs (another Mac, "STU-RF", "my other device"). Use when a handoff plan must leave this device - the human names a second machine, asks to "run it over there", or wants the units to run while this Mac is busy. Produces a tracked `handoff/` on the work branch, a `REMOTE-SETUP.md` orchestrator prompt, and a two-line bootstrap the human pastes into T3 Code on the other machine. Builds on planning-handoff; do not use for a plan that runs on this machine.
---

# Cross-device handoff

Plan here, build there. `planning-handoff` writes the plan; this skill changes how it persists, how
its paths read, and how the other machine picks it up. Everything below is a delta on
`planning-handoff` - read that first, write the plan with it, then apply this.

## Why the default breaks

Default handoff is untracked scratch at repo root. Other machine never sees it. Only transport both
machines share is `origin`. So the plan rides the **work branch** and leaves before `main`.

Repo rule (project-hygiene tier 4, `.gitignore` names `handoff/`) still holds for `main`: the final
unit `git rm -r handoff` and the merge is a **squash**, so `main`'s tree and history never carry a
plan. Human approved this exception 2026-10-01; cite it in the plan's persistence line.

## Steps

1. **Plan as usual** with `planning-handoff`. Then rewrite three things before any commit:
   - **Persistence line:** tracked on `<work-branch>` only, force-added once by the planner, units
     commit their slot with their work, final unit removes it and squash-merges.
   - **Paths:** none absolute. Other machine's layout is unknown. Worktree is reached by
     `cd "$(git rev-parse --git-common-dir)/../.worktrees/<name>"`, which works from the main
     checkout and from inside the worktree. Plan file is `handoff/handoff.md` relative to it.
   - **Notes section:** pre-created slots `### Setup`, `### Unit 1` … `### Unit N`, first line
     `Status: pending | running | done | WIP`. Units fill their own slot in-commit. Nobody ticks the
     table; the slot is the status. Parallel branches then never edit the same lines.
2. **Plan location is `handoff/handoff.md`**, not a subdirectory - `t3-handoff-run` reads it there.
   Local untracked plans in `handoff/` stay ignored and do not collide: the tracked files exist only
   on the branch.
3. **Git.** Branch off `main` only when `main` equals `origin/main` (`git status -sb` shows no
   `ahead`); push `main` first if not - the other device branches from what origin has. Create a
   local worktree for the baseline. Measure the baseline here into § Baseline with real numbers; it
   is the reference the other machine's `### Setup` slot is compared against.
4. **Write `handoff/REMOTE-SETUP.md`** - the orchestrator's prompt (template below). It is the only
   thing the other machine's first session reads.
5. **Commit and push:**
   ```bash
   git add -f handoff && git commit -m "chore(handoff): plan for <topic>

   Cross-device exception: handoff/ is force-added on this work branch only. Unit N removes it
   before the squash merge, so main never holds it." && git push -u origin <work-branch>
   ```
   Verify every `Unit_*.md` is verbatim its section body after the rewrite - regenerate from
   `handoff.md`, never hand-edit a unit file.
6. **Hand over.** Give the human the two-line bootstrap. Stop. Do not start `t3-handoff-run` here;
   the human's go is required for a run (memory: handoff runs need the human's go).

## Final unit, in plain words

The final unit's prompt must contain, after the human's go, in this order:

1. `git rm -r handoff && git commit -m "chore(handoff): remove the <topic> plan before the merge"`, then `git ls-files -- handoff 'HANDOFF*.md'` prints nothing.
2. `git push origin <work-branch>`.
3. In the main checkout: `git switch main && git status --short && git pull --ff-only origin main`.
4. `git merge --squash <work-branch>`, then one commit naming the feature and listing the unit subjects.
5. `git ls-files -- handoff 'HANDOFF*.md'` and `git log --oneline -1 -- handoff` on `main` both print nothing. Any result: stop, do not push, tell the human.
6. `git push origin main`. Tell the human the planning machine can now `git pull --ff-only`, and the worktree and branch are theirs to remove on both machines.

## REMOTE-SETUP.md template

Caveman, one screen. Sections, in order:

1. **Set up** - unsandboxed, in the main checkout: `git fetch origin`,
   `git worktree add .worktrees/<name> -b <work-branch> origin/<work-branch>`, environment sync
   (for Ecotonomous: `UV_PROJECT_ENVIRONMENT="$PWD/.venv" uv sync --extra dev --extra browser` and
   `(cd frontend && npm install)` - never `make install`, it strips Playwright), checks that no other
   verify or pytest runs, then the full verification command.
2. **Record the baseline** into slot `### Setup`: machine, date, counts, every red and PROBLEMS line
   marked environment or code. Compare with the plan's § Baseline. Code red: stop, tell the human.
   Commit `chore(handoff): baseline on <machine>` and push.
3. **Create every unit thread up front, unstarted**, via `t3-handoff-run`: one emoji the human
   picked for the whole handoff, title `<emoji> Unit <N> - <Title>`, model and effort from the
   table, `--branch <work-branch>`, `--worktree <absolute path>` when the plan runs in a worktree.
   `t3.py status` before any start.
4. **Start order** - which units, after which, how to tell a unit landed (`Status: done` in its slot
   on the branch, commit present). Paste the whole unit file as the first message.
5. **Attended units** - name each and why; tell the human before starting one.
6. **Watch** - selectors only, one verify at a time, WIP or out-of-scope edits stop the chain, the
   plan's escalation rule.
7. **Never merge to `main` yourself** - the final unit does, squash, after the human's go, after
   deleting `handoff/`.

## Bootstrap the human pastes

Two lines, into a fresh T3 Code thread on the other machine, project selected, fable high:

```
Fetch origin and read handoff/REMOTE-SETUP.md on branch <work-branch> (git show origin/<work-branch>:handoff/REMOTE-SETUP.md). You are the orchestrator it describes; follow it from step 1.
```

## Launching the orchestrator from here

The human's paste is the launch. T3 Code's orchestration bus is **per environment**: `t3.py` reaches
the server in `~/.t3/userdata/server-runtime.json`, and a pairing credential is bound to one origin.
Reaching the other machine therefore needs its LAN origin reachable from here and a pairing link
minted on it. When both are at hand it works like this, and then the bootstrap goes in as `--text`:

```bash
export T3_ORIGIN=http://<other-ip>:3773 T3_COOKIE_JAR=~/.config/t3-orchestrator/cookies-<machine>.txt
t3.py pair <TOKEN> && t3.py projects
t3.py create --project <project> --title "<emoji> Orchestrator - <topic>" --model fable --effort high
t3.py start <thread-id> --text "<bootstrap>"
```

Check reachability first (`curl -m 4 http://<other-ip>:3773/api/auth/session`); an old address in
`~/.t3/userdata/logs` is a hint, not a fact. Unreachable: hand over the bootstrap and stop.
Measured 2026-10-12: planning Mac `10.53.40.42`, the other machine's remembered address did not
answer, the paste path was used.

## After the merge, on the planning machine

`git pull --ff-only`. If the plan changed `schema.sql`, the live instance needs `eco stop
--everything`, `eco reset`, `eco start --web`, and any new tool or source classified with a
passkey. Count those taps in the plan's final unit so the human knows before they say go.
