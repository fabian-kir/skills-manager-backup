---
name: planning-handoff
description: Turns a finished planning, design or debugging session into a `handoff/` directory — `handoff/handoff.md` holding the work cut into numbered units, a dependency and parallelism table, the reasoning for the cut, a notes section units use to pass findings to each other, and the complete paste-ready prompt for every unit, plus one file per unit (`handoff/Unit_1-opus_high.md`) containing that prompt and nothing else. Each unit prompt carries its own branch, its own slice of the test suite, and its own commit; a final integration unit runs the full suite, checks the other units' work, and asks the user before merging to main. Prompts are written caveman-compressed. Use whenever someone wants work handed to other agents or fresh sessions, for example "write a handoff", "turn this into a plan", "cut this into units", "make prompts for each piece", "how do I parallelise this", "write this up so someone else can execute it", or when a long planning conversation has converged and execution happens elsewhere. Works in any code repo — branch names, verification commands, test selectors and baseline state get derived from the repo, not assumed.
---

# Planning handoff

Plan is not conversation summary. Plan = instructions tight enough that agent with zero context run
one unit alone, land green, commit.

## Output

All output land in `handoff/` at repo root. Two kinds of file, nothing else:

```
handoff/handoff.md              # plan — goal, reasoning, unit table, unit notes, all prompts
handoff/Unit_1-opus_high.md     # prompt for unit 1, nothing else
handoff/Unit_2-sonnet_medium.md
handoff/Unit_N-opus_high.md     # final integration unit
```

**`handoff/handoff.md` is the source.** Holds goal, reasoning, unit table, the unit-notes section
(see below), and full prompt text of every unit inlined under own heading. Nothing a unit needs live
outside it. No separate design doc, no runbook.

**Per-unit file = exact copy of that unit's prompt body from `handoff.md`, and nothing else.** No
heading repeated, no frontmatter, no preamble, no "see plan for context", no trailing notes. Open
file, select all, paste into fresh session — that is whole use. Copy text, do not re-write it: two
copies must not drift. Prompt change in `handoff.md` → rewrite the unit file same moment.

Filename `Unit_<N>-<model>_<effort>.md`: `<N>` unit number from table, `<model>` short model name
lowercase (`opus`, `sonnet`, `haiku`) from Model column, `<effort>` Effort column lowercase (`low`,
`medium`, `high`). Unit 1, opus, high → `handoff/Unit_1-opus_high.md`.

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

**Commit `handoff/` to work branch before any unit start.** Per-unit branches cut off it then carry
plan and prompts, and unit notes land as normal commits on the branch that produced them.

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

Note is part of unit's commit: `git add handoff/handoff.md` with the rest of the work.

**Parallel wave = separate branches = same file touched by several units.** Say so in the prompts:
append-own-block-only keep conflicts small, and when git still conflict, resolution is keep both
blocks — never drop one. Final unit reconcile when it merge the wave.

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

**Baseline:** <green/red> at `<sha>` — <exact numbers verification report>.
<If red: which parts, since when, and no unit start from it.>

## Why work cut this way

<Evidence, then responses. Cite earlier comparable stage with real numbers if one exist: files,
insertions, share that was tests and prose, replans. Then two or three structural choices that
follow, each a bold claim with justification after it.>

## Units

| Done | Number | Title | Branch | Parallel-To | Tests | Model | Effort | Prompt file |
|---|---|---|---|---|---|---|---|---|
| [ ] | 1 | <title> | `<branch>` | — | `<selector>` | <model> | <low/medium/high> | `handoff/Unit_1-<model>_<effort>.md` |
| [ ] | 2 | <title> | `<branch>` | 3, 4 | `<selector>` | <model> | <effort> | `handoff/Unit_2-<model>_<effort>.md` |
| [ ] | N | Integration and merge | `<work-branch>` | — | full suite | <model> | <effort> | `handoff/Unit_N-<model>_<effort>.md` |

**Why this order.** <What unit 1 establish, which units copy it, what unit N wait on — name the
artefact (table, type, interface), not "dependencies".>

**Attended tail: <n>, <m>.** <Why each, as property of work. Final unit always here.>

---

## Notes between units

Channel between units that never share a session. Read this section before you start your unit.
Before you commit, append anything a later unit needs and cannot read off the diff.

Own block at end, `### From unit <N> — <date> — <branch/sha>`. Never edit or delete another unit's
block; on merge conflict here, keep both. Commit the note with your work.

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
  another block, commit it with the work. Nothing to say → nothing to write.
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

Then write files, present them. User want units run → units run in fresh sessions, one prompt file
each. This conversation's context is what the document exist to replace.
