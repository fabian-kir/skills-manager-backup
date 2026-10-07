---
name: t3-handoff-run
description: Use when running a handoff plan as T3 Code threads - creating one configured thread per unit, starting units as their dependencies land, watching for stalled or runaway units, and killing one that has gone wrong. Also use when asked to "run the handoff", "spin up the units", "what is unit C doing", or "kill that run". Do not use to write a handoff plan; that is planning-handoff.
---

# Running a handoff plan as T3 Code threads

`planning-handoff` produces the plan. This skill runs it: one T3 Code thread per unit,
configured correctly, started when its dependencies land, and watchable while it runs.

**Why threads and not subagents.** A subagent is invisible while it works, cannot be killed
individually, and cannot be reached from a phone. A thread is a first-class row in the same
list as everything else, it can be interrupted with one command, and it survives the client
disconnecting. That is the whole argument, and it is why this skill exists.

## The control surface

Everything goes through T3 Code's own command bus, `POST /api/orchestration/dispatch`, wrapped
in `t3.py` beside this file. **Nothing here modifies or rebuilds T3 Code** — it is a client of
the contract in `packages/contracts/src/orchestration.ts` in `pingdotgg/t3code`. When T3
updates and something breaks, re-read that file; do not patch the app.

Reads that need to be frequent go straight to `~/.t3/userdata/state.sqlite`, read-only,
because the projections carry more than the HTTP snapshot — including the literal shell
command a unit is inside right now.

## Setup, once a month

```bash
t3.py whoami
```

If that 401s, mint a pairing link in T3 Code (Settings, paired clients) and redeem it:

```bash
t3.py pair <TOKEN>
```

Three things about that token, each of which cost a session to learn:

- **It is one-time.** Opening the pairing link in a browser consumes it. A token that has been
  clicked is dead; mint another.
- **The session lasts 30 days.** Not per handoff. Re-pairing is monthly, not per run.
- **It is bound to an origin.** `t3.py` pins `127.0.0.1` on purpose. The app advertises its LAN
  address in `server-runtime.json`, that address moves with DHCP, and a credential minted
  against it dies when the network changes. Pair against loopback and this never happens.

The credential lands in `~/.config/t3-orchestrator/cookies.txt`, mode 0600. It carries
`orchestration:operate` — it can create, start, interrupt and delete threads. Treat it as the
secret it is, and never put it in a skill, a plan, or a commit. `t3.py` reads
`$T3_COOKIE_JAR` if you need it somewhere else.

## Reading the plan

A handoff plan is `handoff/handoff.md` at the repo root plus one prompt file per unit,
`handoff/Unit_<N>-<model>_<effort>.md`. Whether they are tracked or local scratch is the
repository's call; the plan's **Handoff persistence** line says which. From the plan you need
four things:

| What | Where |
|---|---|
| Unit number, title, model, effort, prompt file | the Units table |
| What may run alongside what | the `Parallel-To` column |
| The branch each unit works on | the `Branch` column |
| Which units cannot finish without the human | the **Attended tail** line; the final unit is always on it |
| When you may raise a unit's model or effort mid-run, and for which units you must ask first | the **Escalation:** line; the **Model choices.** paragraph says why each row got its model |

Pick **one emoji for the whole handoff** and use it on every unit, so the plan's threads are
visually one group in the thread list. Titles are exactly:

```
<emoji> Unit <Number> - <short task summary>
```

The number and summary are the plan's own `Number` and `Title` for that unit. Do not invent a
new one — `planning-handoff` gives the table row and the `### Unit <N> — <title>` heading
identical text on purpose, and this is the step that makes the chat title match them.

## Creating the threads

Create every unit up front, unstarted. They appear as a labelled group immediately, so the
human can see the shape of the run before any of it moves.

```bash
t3.py create --project Ecotonomous \
  --title "🧪 Unit 1 - Default model in the kernel" \
  --model fable --effort high --branch t3code/improve-model-setup
```

It prints the thread id. Keep a mapping of unit number to thread id — you will need it for
every later command.

Four fields decide whether a unit does the right work:

- **`--branch`** is that unit's `Branch` column: the one work branch for sequential units,
  `<work-branch>/unit-<N>` for a unit in a parallel wave.
- **`--worktree`** is omitted for the usual case. **Omitting it means "Current checkout"**,
  which is the setting that matters most and the one the UI gets wrong. Over the API it is a
  literal `null` and it is deterministic. Pass an absolute path only when the plan calls for a
  separate worktree.
- **`--model`** is the plan's Model column, in the plan's own vocabulary: `fable`, `opus`,
  `sonnet`. Those map to the current generation T3 Code's `claudeAgent` provider lists —
  `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`. `opus5` and `sonnet5` pin the older
  generation when a plan says so. Unknown values pass through unchanged, so a full id works too.
- **`--effort`** is the plan's Effort column: `low`, `medium`, `high`, `xhigh`, `max`. T3 Code's
  picker also shows `ultracode` and `ultrathink`; they are not plan vocabulary and `t3.py`
  rejects them. **There is no fast mode.** `t3.py` never sets it, Fable has no such option, and
  no plan asks for it.

Verify before starting anything:

```bash
t3.py status --project Ecotonomous
```

Every unit should read `NEW`, with the right branch, `current checkout`, and the model and effort
from its table row printed after the thread id — `fable high`, `opus high`, `sonnet medium`. A
unit that reads `opus medium` when the table says otherwise is a unit about to do worse work than
the plan paid for; fix it with `t3.py model` before starting.

**There is no way to stage prompt text without sending it.** The API has no draft-text command;
`thread.turn.start` sends immediately. So a unit is either unstarted and empty, or started. Do
not try to pre-fill a composer — that was a UI-era workaround and it does not survive here.

## Starting units, and chaining them

Start a unit by handing it its prompt file whole:

```bash
t3.py start <thread-id> --prompt-file handoff/Unit_1-opus_high.md
```

Then work the dependency graph: a unit starts when every unit it depends on has landed. The
`Parallel-To` column says which units share no files and may run at once; everything else is
sequential. Start those together, wait, then start their dependents.

**Stop dead at the attended tail.** The plan's **Attended tail** line names the units that need a
signature, a Touch ID, or a taste call the human reserved, and always the final integration
unit, which asks before merging. Those are never started automatically. Tell the human the
plan has reached one, say which, and wait.

**A caution the plan will not state.** Units in a parallel wave share no *files*, but each is on
its own branch, and one checkout can only have one branch checked out — two of them on
`current checkout` would switch branches under each other, and two agents running tests in one
directory interfere even when their edits do not overlap. Before starting a wave together, say
so and let the human decide between sequential starts and a worktree each (`--worktree`).

## Follow-ups, and changing the model mid-run

A follow-up is `start` again on the same thread, with `--text` or another prompt file. It runs
on the thread's current model and effort unless you say otherwise:

```bash
t3.py start <thread-id> --text "Selector still red on test_x; state what you are waiting on."
t3.py start <thread-id> --text "..." --model fable --effort high   # this turn onward
t3.py model <thread-id> --model fable                             # keep effort, change model
t3.py model <thread-id> --effort xhigh                            # keep model, raise effort
```

`model` goes through `thread.meta.update` and takes effect at the next turn; a turn already
running finishes on the model it started with. Both commands fill whatever you leave out from
the thread's stored selection, so one flag is enough. `status` shows the result.

**When to escalate.** The plan's **Escalation:** line is the rule; this is what it usually says,
and what to do when it is silent:

- **Second correction follow-up on the same unit.** The first follow-up is normal. The second
  means the unit is not converging on this model. Escalate before sending it.
- **Wrong-direction stall.** `status` shows the same failing selector, or edits to files outside
  the unit's scope, across three or more tool calls. `interrupt` first, then escalate, then send
  the follow-up.
- **The unit reports it cannot verify, or made a design decision alone**, and the plan did not
  mark it attended. Escalate for the follow-up that asks it to re-check.
- **A `BLOCKED-ON-YOU` question that is really a judgement call** the prompt should have settled.
  Answer it, and escalate so the rest of the unit gets the same judgement.

Default ladder: `opus` → `fable high`; `fable high` → `fable xhigh`. `sonnet` escalates straight
to `fable high`, not to opus — the unit was supposed to be mechanical, and it is not. Up only,
never down inside a unit; a cheaper model gets its chance on the next unit, not this one. `max`
only when the plan names it.

**Restate the state when you switch.** The new model gets the transcript but not the old model's
reasoning. The follow-up that escalates should say in two or three lines what has been tried,
what is failing, and what done looks like — not "see above".

**Ask first where the plan says so.** Units the **Escalation:** line lists as ask-first, and every
unit in the attended tail: tell the human what you see and propose the switch; do not run
`model` until they answer. Everywhere else, escalate, then tell the human you did, with the
reason in one line. Say so again in the final summary so the integration unit knows which units
changed model mid-flight.

**Pick fable up front for the next unit** if two units of the same kind have already escalated.
That is plan feedback: say it, so the next plan's **Model choices.** paragraph starts there.

## Watching

```bash
t3.py status --project Ecotonomous        # one line per unit, with its live command
t3.py running --project Ecotonomous       # every live tool call, oldest first
t3.py status --only STALLED
t3.py status --only BLOCKED-ON-YOU
```

Five states, and the distinction between the last two is the point:

| State | Means |
|---|---|
| `NEW` | created, never started |
| `RUNNING` | a turn is live and its newest tool call is recent |
| `STALLED` | a turn is live and its tool call has not moved for `--stall-minutes` (45 by default) |
| `BLOCKED-ON-YOU` | the unit asked for an approval or an answer and is waiting |
| `IDLE` | no live turn |

`BLOCKED-ON-YOU` is never reported as stuck. A unit waiting for a human is working as designed,
and conflating the two is what makes a monitor useless.

`status` and `running` print the **actual shell command** a unit is inside, with its age. The
two-hour-wrong-test-setup failure shows up as a single `pytest` line that has not moved in
ninety minutes — you see which command, not just that the unit is slow.

When a unit stalls: report it to the human naming the unit, the thread id, the command and its
age, and post a message into that thread asking it to state what it is waiting on, so the
answer is already there when they look. Do not kill it automatically — a legitimately long unit
and a hung one look identical from outside, and only the human knows which this is.

Fable units run long turns by design. A fable thread with a *moving* command — the age resets
as it works — is not stalled however long the turn has run; only a single command that has not
moved counts. Apply the same `--stall-minutes` to every model, and read the command line, not
the turn's age.

## Killing and restarting

```bash
t3.py interrupt <thread-id>    # stop the current turn, keep the session and its context
t3.py stop <thread-id>         # stop the whole session
```

`interrupt` is almost always the right one: the thread keeps its history, and the human can
correct course and continue in the same place. Restarting a unit from scratch means `start`
again with the same prompt file.

## Reference

`t3.py` also has `projects`, `messages <thread>`, `model <thread>`, `rename <thread> <title>`
and `delete <thread>`. Run `t3.py --help`.

Commands the bus accepts that `t3.py` does not yet wrap, should you need them:
`thread.approval.respond`, `thread.user-input.respond`, `thread.settle`, `thread.archive`,
`thread.meta.update` with `branch` and `expectedBranch` for optimistic concurrency. They are all
in `packages/contracts/src/orchestration.ts`.

## What to distrust

- **Verify, do not assume, after a T3 update.** `t3.py whoami` proves the credential;
  `t3.py status` proves the projections still have the columns it reads. Both are cheap and
  both fail loudly.
- **Do not drive the T3 web UI with browser automation to do any of this.** It was tried. The
  composer is a rich contenteditable that ignores synthetic input, the rename field commits
  through neither typing nor a native setter, controls collapse into an overflow menu below
  about 1200px, the workspace picker silently disappears while the environment is reconnecting,
  empty drafts are discarded on navigation, and a new draft inherits the previous thread's
  model and branch. Every one of those is invisible until it has already gone wrong. The API
  has none of them.
- **Do not let a unit inherit the UI's default model.** T3 Code's own default for new chats is
  whatever its picker last had, and the picker's effort default is `medium`. Every unit thread
  is created by `t3.py create` with the plan's row, and `status` proves it before `start`.
