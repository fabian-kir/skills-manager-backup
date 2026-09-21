---
name: planning-handoffs
description: Use when a task is too big for one session and needs splitting across sessions or agents, when asked to hand off work or produce paste-able prompts, when deciding which model or effort level should do what, or when working out what can run in parallel. Also after a plan is approved and the work needs distributing.
---

# Planning Handoffs

## Overview

One big task becomes several self-contained prompts. Each labelled: number, title,
what it runs parallel to, which model, which effort.

**Core principle: specification substitutes for reasoning effort.** A prompt naming
files, line numbers, and a pattern to copy needs a weaker model than a prompt naming
a goal. So the split is not "hard parts to the big model" — it is *specify what you
can, assign by what is left*.

Second principle: **the handoff document and the chat titles must match.** Table row,
section heading, and the agent's chat title all carry the same number and title. User
scanning open chats sees the same labels as the plan.

## When to Use

- Work spans more commits than one session should carry
- User asks which model or effort level
- User asks for a prompt to paste into a fresh session
- Diagnosis or plan landed, now needs distributing
- Independent units exist, could run at once

**Not for:** single change one session finishes. Work where every unit depends on the
previous unit's judgment — split that by checkpoint, not by prompt.

## Step 0 — Ask the technical questions now, not later

Before writing prompts, decide for each open question: **you ask the user now**, or
**the receiving agent asks later**.

Default is **ask now**. You have the conversation context; the receiving agent starts
cold and will ask a worse version of the question.

| Ask user now | Delegate to receiving agent |
|---|---|
| Answer changes the split, the order, or which model | Answer only matters inside one unit, and depends on what the agent finds in the code |
| Answer is a preference or constraint only user holds | Question cannot be phrased without reading files first |
| You would otherwise write "agent should decide" | Genuinely reversible detail, cheap to redo |

Use `AskUserQuestion` — batch them, do not drip one at a time. Write the answers into
the prompts as stated facts.

When you do delegate a question, say so in the prompt and require the agent to ask it
**first, before any work**, batched with every other open question it has.

## Step 1 — Classify each unit

| Question | Why it matters |
|---|---|
| Can I name files, lines, target? | Yes → **mechanical**. Weaker model, lower effort. |
| Does it need deciding what **not** to change? | Expensive judgment, not the edit. |
| What does silent failure look like? | Drives review gate. Step 3. |
| Does it unblock or speed another unit? | Drives order. Step 4. |
| Can it finish without the human? | Drives ordering. Step 4. |

Mechanical and judgment work interleave inside one plan. Split on that boundary, not
on subject matter.

## Step 2 — Assign model and effort

| Unit shape | Model | Effort |
|---|---|---|
| Named files, named target, clear done-state | cheaper/faster | low–medium |
| Synthesis across sources; deciding scope; taste | strongest | high |
| Judgment, but reviewable before it lands | cheaper + review gate | medium |
| Opinion-carrying recommendation | strongest | medium |

**Never default to max effort.** Higher effort is slower. If user complains sessions
take too long, max effort fights the thing they asked you to fix. Reserve it for units
where you can name what the extra reasoning buys.

## Step 3 — Put the review gate where silent failure lives

Failure that matters is rarely breakage — tests and type checkers catch that. It is
**silent weakening**: a change leaves the suite green while proving less. Deleted
assertions, loosened checks, a test converted to a helper call that no longer tests its
subject.

Nothing downstream catches that. So:

- **Do not** upgrade the model and hope. Add a gate.
- Gate shape that works: **enumerate, then stop.** Agent produces a table of every
  candidate change, one-line verdict, reason. Halts before touching anything. Judgment
  becomes a reviewable artifact, not a diff you reverse-engineer.
- Name specific tests or files that must **not** change, with the reason. "Do not weaken
  tests" is ignorable. "`test_x.py` is about which credential reaches which route —
  converting it leaves it green and empty" is not.

Anything removing a stated guarantee gets a **recommendation-only** prompt: report the
change set and what is lost, change nothing, human decides.

## Step 4 — Order by what unblocks, then bunch the attended work

Rank by value to choose *what*. Order by dependency to choose *when*.

A low-value unit that makes verification faster or safer goes first — every unit after
gets cheaper. State this in the table, or the user reads the order as a priority ranking
and questions it.

Fill the **Parallel-To** column for every row: the numbers it shares no files with and
may run alongside, or `—` for none.

**Second sort key: units that cannot finish without the human go last, together.**
A unit needing a signature, a Touch ID, a credential, or a taste call the human reserved
is not "a unit that might stall" — it is the attended tail, by definition. Scattered
through the middle, one such unit stalls every session waiting behind it.
Bunched at the end, the human clears them in one pass.

Say in the prose which rows are the attended tail and why.

## Step 5 — Write self-contained prompts

Each prompt lands in a session with **zero** context. So each carries, in this order:

1. **Chat title line** — first instruction in every prompt:
   `First action: rename this chat to "<number> - <title>", exactly.`
   Same string as the table row and the section heading.
2. **Branch assertion** — the block from Step 5d. Second, before anything else runs.
3. **Open questions** — if any were delegated, agent asks them all up front, before any
   work, and waits.
4. **Why the work exists** — the finding, with numbers, so the agent does not re-derive it
5. **Repo conventions** to follow, named as files or skills, not summarized
6. **The work**, specific enough to act on
7. **Out of scope** — including what you considered and demoted, and why
8. **Never do** — the destructive or irreversible moves that are off the table here
9. **Done means** — verifiable conditions, not "it works"
10. **Finish** — the closing block from Step 5b

Prefer **one phase per prompt**. If a prompt genuinely needs phases (review gate, Step 3),
the agent must announce the current phase to the user at every phase boundary and at the
start of each reply inside a multi-phase run. Untold phase position is how users lose the
thread.

Two habits worth keeping:

- **Tell it to re-measure.** Numbers may have shifted. Give them as findings to verify,
  not facts.
- **Invite disagreement** wherever the prompt carries your opinion, or the agent echoes
  it back as analysis.

Target 3–6 prompts. Beyond that, coordination overhead eats the gain.

### Step 5b — Standard closing block

Every prompt ends with the same block. Paste verbatim:

```markdown
## Finish

1. Walk **Done means** item by item. Run the command, paste the output. No item
   claimed without evidence.
2. Confirm the branch is still the one named at the top: `git rev-parse --abbrev-ref HEAD`.
3. One commit for this unit, on that branch. Project verification green before you
   claim done.
4. Tick this unit's box in `HANDOFF.md`, in the same commit as the work.
5. Report: what landed, what you skipped and why, anything you disagreed with, and
   every decision you made without the human.
```

One commit per unit makes the unit reviewable alone, and lets a human switch model or
effort mid-plan without untangling a diff.

### Step 5c — Standard skill block

Every prompt carries this too:

```markdown
## Skills

- Prose a human reads in conversation — your replies, questions, PR bodies, release
  notes: run `/unslop` before sending.
- Every `.md` file you write, and your own internal reasoning: `/caveman` voice. See
  the voice rules at the top of this prompt for what stays uncompressed.
- Commit messages: `/caveman:caveman-commit`.
- Any choice the design documents did not already answer: `/decision-log`, before you
  claim the unit is done.
- Before creating, moving, or deleting any non-code artefact: `/project-hygiene`.
- If the user asks something that suggests they have lost track of what is going on
  — "wait, what?", "why are we doing this again?", "what does that even do?" — stop
  and run `/mattpocock-skills:wait-what` instead of answering inline.
```

### Step 5d — Standard branch block

Wrong-branch work is the most expensive recoverable mistake in this workflow: the commit
lands, verification passes, the tick appears in `HANDOFF.md`, and nothing is where it
should be. So every prompt asserts its branch **before** doing anything, and the plan
names one branch for all units.

Paste verbatim, substituting the branch name:

```markdown
## Branch

All work for this plan happens on `<branch>`.

Before anything else:

    git rev-parse --abbrev-ref HEAD

- Output is `<branch>` → continue.
- Output is anything else, and `<branch>` exists → `git switch <branch>`.
- Output is anything else, and `<branch>` does not exist → `git switch -c <branch>`
  from `main`.
- Working tree is dirty with changes that are not yours → stop and report. Do not
  stash, do not commit them.

Never commit to `main` in this unit. Never merge, rebase, or force-push anything.
Merging is the final unit's job.
```

## Step 6 — Voice

Two audiences, two skills, no overlap.

| What you are writing | Skill | Why |
|---|---|---|
| Replies to the human, questions, PR bodies, release notes | `/unslop` | A human reads it in conversation. AI tells are noise there. |
| Every `.md` file — `HANDOFF.md`, `handoff/*.md`, `docs/`, notes, reports — and your own reasoning | `/caveman` | Agent-facing or thinking-facing. Compression is free substance-wise and cuts tokens hard. |
| Commit messages | `/caveman:caveman-commit` | Terse subject, body only when "why" is not obvious. |

Paste this into each prompt:

```markdown
Write terse. Drop articles, filler, hedging. Fragments fine. Technical terms exact.
Applies to your reasoning and to every `.md` file you write.

Uncompressed, always: `file:line` lists, spec lines, **Done means**, **Never do**,
security warnings, irreversible-action confirmations. Fragment order carries meaning
there and a compressed spec is an ambiguous spec.

For prose a human reads in conversation — your replies, questions, PR bodies — run
`/unslop` instead.
```

**Caveman the argument. Never the specification.** The exemption above is not a style
preference; Caveman's own Auto-Clarity rule already carves out multi-step sequences
where fragment order risks misread, and a spec is exactly that.

`/project-hygiene` still governs *whether* a given `.md` should exist at all. This step
only governs how it reads once that question is settled.

## Output Format

Produce exactly this shape. The table row and the section heading carry identical data —
if they drift, the document is wrong.

### The table, first

```markdown
| Number | Title | Parallel-To | Model | Effort |
|---|---|---|---|---|
| A | Test infrastructure | — | Sonnet | medium |
| B | Decouple tests | C | Opus | high |
| C | Mechanism doc | B | Opus | high |
```

Titles are short, imperative, and stable — they become chat titles.

### Then one section per prompt

Heading repeats the row, in table order, separated by `·`:

```markdown
### A — Test infrastructure · parallel-to: — · Sonnet · medium
```

Under the heading, the prompt as one plain-text fenced block the user copies whole.
Four backticks so nested fences survive. Nothing else inside the block — no commentary,
no "note that", nothing the user has to strip out before pasting.

````markdown
First action: rename this chat to "A - Test infrastructure", exactly.

# Task: <imperative, one line>

<Branch block from Step 5d.>

<Open questions, if any were delegated. Ask all of them now, before any work, and wait.>

<Why this exists. The finding, with numbers.>

<Repo conventions: which files and skills to read first.>

<The voice block from Step 6.>

## <Section per unit of work>

<Specifics: files, line numbers, patterns to copy. Uncompressed.>

## Out of scope

<Including what was considered and demoted, with the reason.>

## Never do

<Destructive or irreversible moves off the table here. Uncompressed.>

## Done means

<Verifiable conditions. Name the command and the expected output. Uncompressed.>

<Skills block from Step 5c.>

<Finish block from Step 5b.>
````

### Prompts with an internal stop

A unit needing a review gate is still **one** prompt, not two — carries both phases,
halts between them. Split into two and phase 2 arrives without the context that made
phase 1's verdicts mean anything.

````markdown
This prompt has 2 phases. Tell the user which phase you are in at the start of every
reply.

## Phase 1 of 2 — enumerate, then STOP

<Produce the table: every candidate, one-line verdict, reason.>

Change nothing. Report the table and wait for review.

## Phase 2 of 2 — after approval

<The work. Then prove the guard holds: break it on purpose once, then fix it.>
````

Close the document with what the human should **not** delegate — the review gates and
the decisions that are theirs.

## Progress Tracking

Write the plan to `HANDOFF.md` at repo root. Same table, plus a checkbox column, so the
user ticks items off and any session reads what is left:

```markdown
# Handoff plan: <goal>

**Goal:** <one or two lines.>

<Why the work exists. The finding, with numbers.>

## Units

| Done | Number | Title | Parallel-To | Model | Effort |
|---|---|---|---|---|---|
| [ ] | A | Test infrastructure | — | Sonnet | medium |
| [ ] | B | Decouple tests | C | Opus | high |
| [ ] | C | Mechanism doc | B | Opus | high |

Prompt text, one file per unit, paste whole into a fresh session:
[A](handoff/A-test-infrastructure.md) ·
[B](handoff/B-decouple-tests.md) ·
[C](handoff/C-mechanism-doc.md)

**Why this order.** <Which row sits where, and why. Name the attended tail.>
```

This layout is load-bearing — the human reads the tick boxes as progress. Do not
reorder or rename the columns. Add rows, not columns.

Full prompt text goes in `handoff/<Number>-<slug>.md`, one file per unit, `<slug>`
kebab-cased from the title. Long prompts inline in `HANDOFF.md` make the table unreadable,
which is the one thing the human actually watches.

Each agent ticks its own box in the same commit as the work — that is in the Step 5b
Finish block already.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Table row and section heading disagree | They are the same data. Copy, do not retype. |
| Agent never renames its chat | First line of every prompt. Step 5. |
| Commentary inside the copy block | Block is paste-able as-is. Nothing to strip. |
| Deferred a question the user could have answered in one line | Step 0. Default is ask now. |
| Multi-phase prompt, user lost track of the phase | Announce phase every reply. Better: one phase. |
| Prompt assumes conversation context | Fresh session, zero context. Re-read as a stranger. |
| Bigger model where a review gate was needed | Reviewable judgment is cheaper to gate than to buy. |
| Ordered by value, user reads it as priority | Say why each sits where it sits. |
| Attended units scattered through the middle | Bunch them last. Step 4. |
| No branch block, work lands on `main` | Step 5d. Every prompt, second thing it does. |
| Eight prompts for a four-commit job | 3–6. Coordination is not free. |
| Opinion stated as fact, echoed back as analysis | "Disagree with me if you think I'm wrong." |
| No out-of-scope or never-do section | Agent adds the thing you deliberately dropped. |
| "Done means: it works" | Name the command and the expected output. |
| Work ends without commit or tick | Step 5b block. Non-optional. |
| Caveman applied to a spec | Caveman the argument, never the specification. Step 6. |
| `/unslop` applied to a `.md` file, or `/caveman` to a chat reply | Two audiences, two skills. Step 6 table. |
| Columns added to the `HANDOFF.md` table | The launcher parses by position. Add rows. |
