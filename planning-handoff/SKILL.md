---
name: planning-handoff
description: Turns finished planning, design, or debugging into a `handoff/` plan and paste-ready numbered unit prompts. Each unit gets a branch, focused tests, commit, and shared-note instructions; a final unit reviews work, runs full verification, and waits for user approval before merging. Use for handoffs, execution plans, parallel agent units, fresh-session prompts, or requests to split work for others. Derives repository facts and obeys repository policy for tracked files versus local scratch.
---

# Planning handoff

Plan is not conversation summary. Plan = instructions tight enough that agent with zero context run
one unit alone, land green, commit.

## Repository policy wins

Before deciding how `handoff/` persists, read repository instructions and check whether target is
ignored:

```bash
git check-ignore -v handoff/handoff.md 2>/dev/null || true
```

Repository-specific rules override this skill's default workflow. If repository says handoffs are
scratch, ignored, untracked, or never committed:

- keep `handoff/` local and untracked;
- never use `git add -f` or change `.gitignore` to bypass that rule;
- do not commit handoff notes with unit work;
- state in plan that handoff is worktree-local;
- before merge, verify no handoff path is tracked.

Deleting handoff in later commit is not equivalent. Merge would retain scratch in repository
history. Durable decisions must move into repository's chosen docs, tests, or decision log before
handoff is deleted.

If separate worktrees need same untracked handoff, use repository-approved copy or shared scratch
location. If none exists, ask user. Do not invent temporary Git history that final branch might
merge. Same-worktree branch switches retain ignored files and need no transport.

## Output

All output land in `handoff/` at repo root. Two kinds of file, nothing else:

```
handoff/handoff.md              # plan — goal, reasoning, unit table, unit notes, all prompts
handoff/Unit_1-opus_high.md     # prompt for unit 1, nothing else
handoff/Unit_2-sonnet_medium.md
handoff/Unit_N-fable_high.md    # final integration unit
```

**`handoff/handoff.md` is the source.** Holds goal, reasoning, unit table, the unit-notes section
(see below), and full prompt text of every unit inlined under own heading. Nothing a unit needs live
outside it. No separate design doc, no runbook.

**Per-unit file = exact copy of that unit's prompt body from `handoff.md`, and nothing else.** No
heading repeated, no frontmatter, no preamble, no "see plan for context", no trailing notes. Open
file, select all, paste into fresh session — that is whole use. Copy text, do not re-write it: two
copies must not drift. Prompt change in `handoff.md` → rewrite the unit file same moment.

Filename `Unit_<N>-<model>_<effort>.md`: `<N>` unit number from table, `<model>` short model name
lowercase (`fable`, `opus`, `sonnet`) from Model column, `<effort>` Effort column lowercase (`low`,
`medium`, `high`, `xhigh`, `max`). Unit 1, opus, high → `handoff/Unit_1-opus_high.md`. Model and
effort come from § "Model and effort per unit", chosen per unit — never from habit.

User give other directory or plan filename → use it, keep same layout inside.

## Style — caveman

Write plan caveman. Unit prompts caveman. Any subagent instruction the plan tells a unit to write —
caveman too. Prompt text get re-read by every fresh session, so token cost repeat every time; dense
prompt is cheaper prompt.

If `caveman` skill installed, invoke it (level `full`) before writing. Else apply rules inline: drop
articles, filler, hedging, pleasantries. Fragments fine. Short synonyms. No tool narration, no
decorative tables, no emoji.

**Never compress these — verbatim always:** file paths, commands, flags, branch names, test
selectors, identifiers, API names, error strings, commit-type keywords, and any decision this
session made (interface, column name, error mode).

**Drop caveman where compression hide order or risk:** merge steps, destructive commands, warnings,
the user-confirmation gate. Plain full sentences there. Resume after.

## Derive facts from repo

Guess any of these → plan die on first command. Find them:

```bash
git status --short && git log --oneline -5      # tree clean? HEAD?
git branch -a --sort=-committerdate | head -20  # branch naming convention
ls Makefile justfile Taskfile.yml package.json pyproject.toml Cargo.toml go.mod 2>/dev/null
cat .github/workflows/*.y*ml 2>/dev/null | head -60   # what CI run = real gate
```

Read whichever exist for real command names — `make verify`, `npm test`, `cargo test`,
`uv run pytest`, `mypy --strict src`. Skim `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md` if present —
commit and branch conventions live there.

**Also map test layout.** Need per-unit selectors later: test dir structure, marker or tag scheme,
`-k` support, path filters. Cheap now, blocking later.

**State baseline in document with SHA.** Run verification. Green → say so with numbers it report
(test count, type-check status). Red → say which parts, since when (`git log -S`, `git bisect` if
worth it), and say no unit start from that tree. This load-bearing: agent on red tree cannot tell
own breakage from inherited breakage, and cheapest way to green a red suite is delete the check that
fail.

**Ask user only what repo cannot answer**: branch name if no convention, scope edge if conversation
left it fuzzy. Two questions max. Rest derivable, or your call — state it.

## Branch

Planner create branch before writing plan. Off the green baseline commit:

```bash
git switch -c <work-branch>          # e.g. stage-11/toolstore-operational
```

Not a git repo → skip this section entirely, and say so in plan.

**One work branch when units run in sequence.** Every unit commit to it.

**Own branch per unit when a wave run parallel** — separate sessions on one branch in one checkout
collide even when files disjoint:

```bash
git switch -c <work-branch>/unit-<N> <work-branch>
```

Put exact branch name in that unit's prompt. Unit check branch before first edit, never assume
session start clean.

**Every unit commit own work at end.** No unit leave changes uncommitted for next unit to find.

**Persist `handoff/` according to repository policy before any unit starts.** If repository permits
tracked handoffs, commit it to work branch; per-unit branches then carry plan and prompts. If
repository marks handoffs scratch or ignored, leave files local and untracked. Never force-add
them. State chosen persistence in `handoff/handoff.md` and every unit prompt so a fresh session
knows whether notes belong in commit.

## Cut work into units

Unit = one fresh session, one commit, tree green after.

**Lead with reference slice.** First unit alone, smallest complete example of the shape everything
copy — simplest case, no migration, no special authority, no interesting edge. Usually not most
valuable unit. Goes first anyway: every later unit copy its layout, tests, registration, argument
conventions. Landed example beat prose describing same thing.

**Parallel units share no files.** Not "mostly". Two units touch same registry or schema → they
sequential, or they one unit. Write parallelism in table so nobody infer it.

**Docs run once, at end, one unit.** Split docs across units = write same cross-references six times
in miniature, then reconcile six partial versions. Normative docs behind sync check cannot
parallelise with themselves either.

**Weight by measured diff share, not by how interesting work is.** Comparable earlier stage exists →
measure it (`git diff --stat` across its range) and use numbers. Work that was 1% of last diff goes
last, does not drive sequencing. Tests and prose usually dominate code; effort estimate reflect
that, not feature line count.

**Name attended tail.** Some units must not run unattended. State reason as property, not caution:
removes a guarantee stated elsewhere (so only honest output is recommendation), needs credential or
physical confirmation, touches cross-referenced docs two agents cannot edit at once, or correctness
is judgement not passing suite. Final integration unit (below) always in this tail.

**Resolve open questions before cutting.** Anything conversation left undecided that a unit would
decide → decide here, in plan, in prompt. Or flag unit attended. Unit forced to decide alone will
decide, and you find out after three units built on it.

## Model and effort per unit

Three models in play, all 1M context. List price per million tokens, in / out:

| Model | Short | $/M in / out | Use for |
|---|---|---|---|
| Claude Fable 5.1 | `fable` | 10 / 50 | judgement, unknown failure mode, long horizon, anything that drew follow-ups on opus before |
| Claude Opus 5.5 | `opus` | 4 / 20 | default — complete spec, shape to copy, moderate scope |
| Claude Sonnet 5.5 | `sonnet` | 2 / 10 | mechanical repeat of landed shape, selector catches wrong result cheap |

**Judge cost per landed unit, not per token.** Opus unit that needs two correction follow-ups
costs more than one clean fable turn — in tokens, and in human attention each follow-up burns,
which is the scarcer thing. Habit says opus medium or opus high for every row. Habit is right for
most rows and wrong for a known minority; find that minority with the tests below.

**Fable when any one holds:**

- Unit decides what plan could not pin: interface shape, error mode, layout later units copy.
  Reference slice qualifies when existing code does not already dictate its conventions.
- Correctness is judgement, not passing suite: integration review, reconciling notes, data
  migration, security-relevant change.
- Failure mode unknown at plan time: debugging, flaky test, "make X work" with cause not found.
- Long horizon: measured diff share above roughly 30% of batch, or more than ~15 files expected,
  or several stages (build, migrate, verify) that must land in one session.
- Evidence: comparable earlier unit on opus needed two or more correction follow-ups, replan, or
  stalled. Same kind of work → fable. Check earlier `handoff/` plans and thread history if there.
- Prompt cannot remove an ambiguity and unit must still run unattended.

**Opus when:** spec complete, shape exists to copy, scope moderate, selector shows failure
plainly. Most units.

**Sonnet when:** work is landed shape copied N more times, rename sweep, test additions from
template, docs sync behind a check — and selector would catch a wrong result cheaply. Not for
anything where wrong-but-green is possible.

**Effort tiers** — `low`, `medium`, `high`, `xhigh`, `max`:

- `high` — default for opus and fable units. Not `medium`: Opus 5.5 defaults to medium and that
  sits one step below what Claude Code runs agentic work at; a medium unit reads less and asks
  more.
- `xhigh` — long tool-call chain, debugging, many expected test cycles. Final integration unit
  with two or more parallel branches to merge.
- `max` — only where wrong answer is expensive to undo and selector cannot catch it. Rare. Reason
  in plan.
- `medium` — sonnet mechanical units. Never for fable: paying for the model, then throttling it.
- `low` — subagents a unit spawns for lookups. Not a unit tier.
- `ultracode`, `ultrathink` exist in T3 Code's picker. Not plan vocabulary; keep out of table.

**Final integration unit: fable high.** Batch of one or two units → opus high acceptable.

**Fable prompts differ.** State what done looks like, constraints, selector, commit rule. Do not
script every step — over-prescription lowers fable's output. Verbatim rules still verbatim.
Fable turns run long; quiet twenty minutes on fable usually means working, not stuck.

**Escalation rule, written in plan.** Runner may raise a unit's model or effort mid-run — second
correction follow-up, stall with wrong-direction work, unit says it cannot verify. Up only, never
down inside a unit. Plan line `**Escalation:**` states default (`opus → fable high`;
`fable high → fable xhigh`) and names units where runner must ask human before switching.
`t3-handoff-run` executes it.

**Reason per non-default row.** Any row not opus high gets a short why in `**Model choices.**`
under the table. Reader sees why fable, why sonnet, without re-deriving.

## Tests per unit

Common failure: every unit run whole suite. Slow, and worse — unit that run everything start fixing
failures it did not cause, in files it does not own.

**Each unit prompt name its own selector.** Exact, derived from repo layout:

```bash
uv run pytest -q tests/kernel/test_tools.py tests/tools/          # path filter
uv run pytest -q -k "delegation or completed"                      # keyword
npm test -- src/messages                                           # path filter
cargo test messages::                                              # module filter
```

Plus whatever fast check cover the changed files — lint, types on changed paths only.

**Failure outside own selector → do not fix. Note in closing report.** That failure belong to
another unit or to baseline. Fixing it hide who broke it.

**Full suite run once, in final unit.** Not per unit.

## Unit notes — how units talk to each other

Units run in separate sessions, share no context. Unit 2 find thing unit 5 must know — schema column
renamed, helper moved, plan assumption wrong, edge case discovered — and it die in unit 2's
transcript. Plan need one place for it.

**`handoff/handoff.md` carry section `## Notes between units`.** Planner create it empty, with the
rules in it. Units append. That is the only channel — no side files, no chat, no editing each
other's prompts.

Every unit prompt say both directions:

- **Read before start.** `handoff/handoff.md` § "Notes between units", plus own prompt. Note that
  contradict prompt wins if it come from a unit that already landed — that unit saw the real code,
  prompt was written before. Contradiction that change unit's scope → stop, report, do not guess.
- **Write before commit.** Anything a later unit would want and cannot see from the diff: decision
  made alone, plan assumption that turned out wrong, interface actually landed, trap avoided.
  Nothing to say → write nothing. Same content go in closing report too; note is for the units,
  report is for the user.

Append format — own block at end of section, never touch another unit's block:

```markdown
### From unit <N> — <date> — <branch/sha>

- **For unit <M> (or: all):** <the fact, one or two lines, concrete.>
- **For all:** <plan said X, real code does Y — <path>.>
```

When repository permits tracked handoffs, note is part of unit's commit: add
`handoff/handoff.md` with rest of work. When repository requires untracked scratch, note stays
local and must not be staged. Closing report carries same fact so it survives if local scratch is
lost.

**Parallel wave = separate branches = same file touched by several units.** For tracked handoffs,
say so in prompts: append-own-block-only keeps conflicts small, and conflict resolution keeps both
blocks. For untracked handoffs in same worktree, branches share one local file and no merge occurs.
Separate worktrees need repository-approved transport decided before units start; otherwise wave
cannot run parallel. Final unit reconciles every note.

**Note reach nobody who already started.** Unit running parallel right now will not see it. Finding
that blocks a running unit → note it, and say in closing report that unit <M> need re-check; final
unit act on it. Plan cannot deliver interrupts.

## Final unit — integration and merge gate

Last unit in every plan. Attended. Its work is checking, not building:

1. Full suite, full type-check, full lint. Report every failure with the unit that most likely
   caused it. Do not silently fix — a failure here is information about an earlier unit.
2. Read each earlier unit's diff (`git log --oneline <work-branch>`, `git show <sha>`) against that
   unit's declared scope. Flag: files touched outside scope, verification skipped, tests weakened,
   guarantees deleted to make a suite green.
3. Collect each unit's closing report — what it decided alone, what it could not verify, where it
   disagreed with plan.
4. Read `handoff/handoff.md` § "Notes between units" end to end. Every note addressed to a unit that
   had already started → check that unit's diff against it. Notes are the only record of what units
   learned mid-flight; unread, they are worth nothing.
5. Parallel-wave branches exist → merge them into `<work-branch>` first, resolve conflicts (notes
   section: keep every block, drop none), rerun suite.
6. Repository forbids tracked handoffs → run `git ls-files -- handoff 'HANDOFF*.md'` and
   `git log --oneline <baseline>..HEAD -- handoff 'HANDOFF*.md'`. Any result is a blocker. A later
   deletion commit does not fix history; report it and stop before merge.

Then the merge gate, written plain in the prompt because compression here is dangerous:

> Do not merge to `main`. Present the summary to the user first: suite result, anything found in
> review, anything each unit could not verify, and the exact merge command you propose. Wait for
> the user's explicit go-ahead. If they do not answer, stop — leave the work on the branch. Merging
> unreviewed work is the one action in this plan that cannot be undone cheaply.

## Document template

`handoff/handoff.md`. Keep order: goal, reasoning, table, sequencing, notes, prompts. Adapt headings
to project vocabulary.

```markdown
# Handoff plan: <short name for batch>

**Goal:** <one or two sentences — what exists when all units landed.>

**Work branch:** `<branch>` — created off `<sha>`. <Per-unit branches for wave N, if any.>

**Handoff persistence:** <tracked and committed because repository permits it / local untracked
scratch because repository forbids committing it>. <Transport rule for separate worktrees, if any.>

**Baseline:** <green/red> at `<sha>` — <exact numbers verification report>.
<If red: which parts, since when, and no unit start from it.>

## Why work cut this way

<Evidence, then responses. Cite earlier comparable stage with real numbers if one exist: files,
insertions, share that was tests and prose, replans. Then two or three structural choices that
follow, each a bold claim with justification after it.>

## Units

| Done | Number | Title | Branch | Parallel-To | Tests | Model | Effort | Prompt file |
|---|---|---|---|---|---|---|---|---|
| [ ] | 1 | <title> | `<branch>` | — | `<selector>` | fable | high | `handoff/Unit_1-fable_high.md` |
| [ ] | 2 | <title> | `<branch>` | 3, 4 | `<selector>` | opus | high | `handoff/Unit_2-opus_high.md` |
| [ ] | N | Integration and merge | `<work-branch>` | — | full suite | fable | high | `handoff/Unit_N-fable_high.md` |

**Model choices.** <One line per row that is not opus high: unit, model, effort, why — per
§ "Model and effort per unit". Example: "1 fable high — sets layout 2–4 copy, conventions not
in repo yet." "3 sonnet medium — copies unit 1 shape, selector catches drift.">

**Escalation:** <default, e.g. second correction follow-up → fable high; fable already → xhigh.
Units where runner asks human before switching: <n>, <m>, or none.>

**Why this order.** <What unit 1 establish, which units copy it, what unit N wait on — name the
artefact (table, type, interface), not "dependencies".>

**Attended tail: <n>, <m>.** <Why each, as property of work. Final unit always here.>

---

## Notes between units

Channel between units that never share a session. Read this section before you start your unit.
Before you commit, append anything a later unit needs and cannot read off the diff.

Own block at end, `### From unit <N> — <date> — <branch/sha>`. Never edit or delete another unit's
block; on merge conflict here, keep both. If handoff is tracked, commit note with work. If handoff
is repository-required scratch, keep note untracked and repeat it in closing report.

<empty until first unit writes>

---

## Unit prompts

Each section complete. Body of each section copied verbatim into its own file under `handoff/`.

### Unit 1 — <title> → `handoff/Unit_1-<model>_<effort>.md`

<prompt body>

### Unit 2 — <title> → `handoff/Unit_2-<model>_<effort>.md`

<prompt body>
```

Heading line with the `→ <file>` pointer is not part of prompt body. Per-unit file start at first
line after it.

## What each unit prompt contain

Reader has no memory of this conversation, no access to it. Assume competence, assume nothing else.

- **Branch check first, before any edit:**
  ```bash
  git rev-parse --abbrev-ref HEAD   # must print <branch>; if not: git switch <branch>
  git status --short                # must be empty
  <verify-command>                  # must pass before you touch anything
  ```
  Wrong branch or red tree → stop, say so, change nothing.
- **Read first** — `handoff/handoff.md` § "Notes between units" (what earlier units learned), then
  two or three files by path, one line each on what to take. Units after first: "copy executor
  shape, test layout, registry block from `<path>` as landed in unit 1." Note from landed unit
  contradict this prompt → note wins; contradiction that move scope → stop and report.
- **The change, concrete.** Files to create, files to modify, names of things added. Description of
  the change, not of the goal. Decision made this session (interface, column name, error mode) →
  state decision, not the considerations behind it.
- **Out of scope** — what neighbouring unit own that a reasonable agent would otherwise touch. This
  is what keep parallel units off each other's files.
- **Test selector for this unit**, exact. Plus: failure outside selector is not yours — report it,
  do not fix it.
- **Note for other units, before commit.** Anything later unit need and cannot see in diff — decision
  made alone, plan assumption wrong, interface actually landed, trap. Append own block to
  `handoff/handoff.md` § "Notes between units", address it (`For unit 5:` / `For all:`), never touch
  another block. Commit it with work only when repository permits tracked handoffs. Otherwise keep
  it untracked and repeat same fact in closing report. Nothing to say → nothing to write.
- **Done means:** selector clean, changed-file checks clean, work committed:
  ```bash
  git add -A && git commit -m "<type>(<scope>): <subject>"
  ```
  Cannot run verification → unit not done. Commit what exist with `WIP:` in subject, tick nothing,
  stop. Half unit you can see beat whole unit you cannot trust.
- **Closing report:** what it decided without user, what it could not verify, what it skipped, where
  it disagreed with plan. Ask every unit. Unit that ran clean and report nothing it decided alone is
  unit that did not notice it was deciding.
- **Subagents** — unit spawn any, instructions go caveman too, same verbatim exceptions.

One screen, two max. Length come from specificity, not from restating project background.

## Before hand over

Check draft against each:

1. Could fresh session run unit 3 from `handoff/Unit_3-*.md` alone, asking nothing?
2. Every pair marked parallel touch disjoint files?
3. Baseline stated with SHA and real verification result?
4. Every command found in this repo, not invented?
5. Every unit have own selector, and only final unit run full suite?
6. Every unit end in a commit, on a named branch it check first?
7. Final unit stop at user before merging to `main`?
8. Anything in reasoning unsupported by a number or artefact you can point at?
9. One prompt file per unit in `handoff/`, name match table's model and effort, content identical to
   that unit's section body — no heading, no extra line? Diff them to be sure.
10. Notes section present with its rules, and every unit prompt say both read-it and write-it?
11. Repository handoff policy checked with `git check-ignore` and repository instructions? If
    handoffs are scratch, confirm no `git add -f`, no tracked handoff path, and no plan to
    commit-then-delete.
12. Model and effort per row chosen against § "Model and effort per unit", not habit? Every row
    not opus high has its line under `**Model choices.**`? `**Escalation:**` line present? Final
    unit fable high (or opus high with reason)?

Then write files, present them. User want units run → units run in fresh sessions, one prompt file
each. This conversation's context is what the document exist to replace.
