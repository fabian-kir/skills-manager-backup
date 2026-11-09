# The contract: what lives where, in what shape, written by whom

Every script resolves the project root as the nearest ancestor holding `agents/config.json`.
Paths below are relative to that root. Frontmatter = minimal YAML subset (scalars, `[a, b]` lists, one level).

## Folder map

```
AGENTS.md                  entry file, router, ≤ 200 lines; loaded every session
CLAUDE.md                  one line `@AGENTS.md` (+ Claude-only notes below it)
.claude/settings.json      optional Claude adapter (written by init only if absent)
<work folders>             per profile, listed in agents/config.json "work_folders"
agents/
  config.json              profile, spike_inactive_days, register_write, work_folders, gate_dirs, thresholds
  README.md                plain-language explanation for humans (de or en)
  STATUS.md                goal, position, checkpoints, who owns what
  LOG.md                   one line per event
  registers/
    decisions/             INDEX.md + YYYY-MM-DD-<slug>.md
    lessons/               INDEX.md + YYYY-MM-DD-<slug>.md (standing rules are lessons with rung: rule)
    examples/              INDEX.md + <stable-id>.<ext> + <stable-id>.json sidecar
    questions.md  sources.md  glossary.md
  inbox/                   proposals waiting for the curator (all of them in inbox mode; the flagged ones in direct mode)
  scratch/YYYY-MM-DD-<slug>/   one spike per folder, spike.md + free-form files
  templates/               decision.md, lesson.md (+ profile extras: finding.md, PROJECT.md, …)
  scripts/                 copies of the skill's scripts; the project runs without the skill
  roles/                   worker.md, curator.md, verifier.md
  adapters/claude/  adapters/codex-README.md
  .trash/                  soft-deleted spikes and replaced examples; purged after 30 days
  .nudge.json  .lint-last.json   script state
```

Git repos: init appends `agents/scratch/`, `agents/.trash/`, `agents/.nudge.json`, `agents/.lint-last.json`
to `.gitignore`. Inbox and registers are committed.

## Who writes what

| Kind | Files | Rule |
|---|---|---|
| Generated | `registers/*/INDEX.md`, `.lint-last.json`, `.nudge.json` | never hand-edit; `index.py`, `lint.py`, `status.py` rewrite them. `promote.py` reindexes after every change |
| Append-only | `agents/LOG.md`, `agents/registers/questions.md`, `agents/registers/sources.md`, notes and TENTATIVE lines in `spike.md` | one line per entry via `agents/scripts/append.sh`, `propose.py question`, `spike.py note\|tentative`; never an editor tool, never reorder |
| Owned: curator/human | `AGENTS.md`, `agents/config.json`, everything under `agents/registers/decisions/`, `lessons/`, `examples/`, `glossary.md` | registers change only through `promote.py`, plus `propose.py` in direct mode (below); `AGENTS.md` by hand in a curator run |
| Owned: orchestrator/human | `agents/STATUS.md` | workers report via `LOG.md` instead |
| Owned: author | inbox items (`propose.py`, written once), direct-written register entries until attested (`propose.py`, written once, never edited afterwards), a spike's files (its workers), work products (one file per agent, `YYYYMMDD_<topic>_<name>.md`) | edit only files you created in this run |

## Direct or inbox — the decision rule

`agents/config.json` `"register_write"`: `inbox` (every proposal waits for a curator) or `direct`
(`propose.py` writes a qualifying decision or lesson into the register at once). Profile defaults:
code-repo and procedure `direct`; research-case and maker `inbox`. `init.py --register-write`
overrides. A config without the key is `inbox`.

In one line: **write direct when you made the choice, it can be undone, and a check will catch bad
shape; otherwise propose.** The three conditions, all required:

| Condition | Holds when | Fails when (→ inbox) |
|---|---|---|
| one attestation is enough | the entry is reversible, scoped to the artefact or spike it came from, and names no in-force entry | kind `rule` (touches `AGENTS.md`) or `example` (one current best per id needs a comparison); `--supersedes`, `--contradicts`; `--scope`, `--replacement-cost high`, `--touches-entry` |
| a mechanical gate exists | the project runs `index.py --check` or `lint.py --strict` before a commit, in CI, or at session end — a malformed entry cannot survive | no git, no verify command, nobody runs the scripts (research-case, maker: the inbox is the quarantine CI would be) |
| the author had context | the session that made the choice records it, in the same run | `--inbox`: you report another's choice, run as a subagent or at reduced effort, or harvest a stale spike; several writers a day into one register |

The first row is checked by `propose.py` from its flags and the kind. The second is the profile's
default and the human's override. The third is the worker's honesty, so `--inbox` exists and
`AGENTS.md` §5 tells subagents to use it.

What direct writes cost, and what bounds it: a wrong entry is in force until a curator sees it.
It is marked `attested: author` and `written: direct`, listed by `promote.py unreviewed`, counted
by `status.py` (`due: direct` at ≥ 10 or oldest > 14 days, `thresholds.direct_unreviewed*`) and
flagged by `lint.py` (`direct-unreviewed`). The curator applies the same trigger and ladder as to
an inbox item: `attest` (meets it) or `retire` (does not; file kept, out of the index). In inbox
mode a direct entry is a lint finding (`direct-in-inbox-mode`).

Init writes each file once and never overwrites (rerun = upgrade, adds what is missing).

## Ids

- Scheme `YYYY-MM-DD-<slug>`. Slug: lowercase, ä/ö/ü/ß → ae/oe/ue/ss, other non-alphanumerics → `-`, ≤ 60 chars. Collision → `-2`, `-3`.
- Inbox item: `agents/inbox/YYYY-MM-DD-<kind>-<slug>.md` (example: plus the file `…<ext>` and a `.json` sidecar).
- Register entry: date of the *proposal* + slug of the title; `id:` = filename stem. `index.py --check` fails if the filename date ≠ `date:` or ids repeat.
- Spike: `agents/scratch/YYYY-MM-DD-<slug>/` (creation date). `spike.py` accepts the bare slug when unique.
- Example: stable id **without** date (`--example-id`, default = title slug) — one current best per id.
- Source: agent prefix + number (`SA12`, `SE201`). Research questions in the brief: `A1`, `B2` (research-case).
- Refer to entries by id or `decisions/<id>`; never by title.

## Statuses

```
inbox item      proposed ──accept──▶ register entry   (or ──drop──▶ gone, DROP line in LOG)
direct write    propose.py ─────────▶ register entry, tentative, attested author ──attest──▶ attested curator
register entry  tentative ─▶ confirmed ─▶ superseded      (or ──retire──▶ retired, file kept)
```

- `proposed` — only in `agents/inbox/`; not in force.
- `tentative` — default of `promote.py accept` and of a direct write; **in force**, unconfirmed (`attested: curator` after accept or attest, `attested: author` after a direct write).
- `confirmed` — `promote.py accept … --as confirmed --attested human` at accept time, or later `promote.py confirm <id> --by <human>` (human only; sets `attested: human`, `confirmed: <date>`, reindexes). Tentative entries may stay tentative indefinitely.
- `superseded` — set by `promote.py supersede <old> --with <new>` or by accepting a decision with `supersedes:`; adds `superseded_by`. Out of the index; `lint.py` flags files still citing it. Never delete an entry.
- `retired` — set by `promote.py retire <id> --by … --reason …`; out of the index, file kept with `retired`, `retired_by`, `retired_because`. The verb for a direct entry that fails the trigger, and for any entry the human takes out of force without a successor.
- `index.py` also leaves out `dropped` and `deleted`; no script sets these.
- One `promote.py mark <id> --harmful` sets `needs: human` on the entry; `lint.py` suggests REPLACE when harmful > helpful.
- Elsewhere: spike `status: open`; question lines `open` / `answered` (append a second line); finding `draft` / `final`; example sidecar `current`.

## Frontmatter keys

| File | Keys |
|---|---|
| inbox item (all) | `kind` decision\|lesson\|rule\|example, `title`, `date`, `by`, `status: proposed`, `refs`, `tags`, `origin`?, `needs` curator\|human, `needs_human_because`? |
| + decision | `replacement_cost` low\|medium\|high, `supersedes`?, `contradicts`? |
| + lesson | `rung` structure\|check\|rule\|lesson, `helpful: 0`, `harmful: 0` |
| decision entry | inbox keys minus `kind`/`needs*`, plus `id`, `status`, `attested` author\|curator\|human, `promoted`; direct writes add `written: direct`, attest adds `reviewed`; later `superseded_by`, `supersedes`, `last_updated` (merge), `retired`/`retired_by`/`retired_because` |
| lesson / rule entry | as decision entry plus `rung`, `helpful`, `harmful` (`rule` → lesson with `rung: rule`) |
| example sidecar (JSON) | `id`, `title`, `file`, `created`, `by`, `settings` {k: v}, `provenance` {`source_url`, `publisher`, `usage_basis`}, `status: current`, `attested`, `promoted`, `notes` |
| `spike.md` | `slug`, `created`, `by`, `status: open`, `question`?; body: Goal, Exit condition, `- TENTATIVE <time> (<by>): …`, `- <time> (<by>): …` |
| finding (research-case) | `title`, `question`, `agent`, `date`, `status`, `confidence` |

Templates for bodies: `agents/templates/decision.md`, `agents/templates/lesson.md`.

## One-line formats

```
LOG.md        | KIND | <ISO time> | <who> | <what> | <note> |
              KIND: INIT PROPOSE DIRECT ASK PROMOTE DROP ATTEST RETIRE MARK CONFIRM SUPERSEDE SPIKE CURATE DONE AUTO
questions.md  | <time> | <by> | <question> | <searched> | <for> | open |
sources.md    | <id> | <type> | <title> | <url or locator> | <publisher> | <published> | <accessed> | <used in> | <note> |
```

Index line = one row per in-force entry, newest first; decisions show date/status/title, lessons add rung/helpful/harmful.
