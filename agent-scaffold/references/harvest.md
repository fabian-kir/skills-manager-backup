# Mode: harvest — end a spike, keep what survives, soft-delete the rest

A spike is a folder under `agents/scratch/`. It is not authoritative: nothing in it is in force
until harvested into `agents/registers/`. Harvest runs inside a curator session (`references/curate.md`).

## How a spike starts — nobody has to declare it

Worker rule: no template or register for what you are about to write → it goes to scratch.

```
python3 -I agents/scripts/spike.py new <slug> --goal "…" --exit "…" --by <name>
```

That folder *is* the spike: `agents/scratch/YYYY-MM-DD-<slug>/spike.md` with goal and exit
condition. Explicit starts use the same command:
- the human says explore / try / quick check;
- a plan marks a unit exploratory, or a handoff plan starts (`references/addons.md`);
- research-case: a question opens a spike keyed to it, `--question <id>`, goal = the question restated in one line.

While it runs: free-form files inside; `spike.py note <slug> --by … --note "…"` for working notes;
`spike.py tentative <slug> --by … --text "…"` for every choice made on the way (one line, prefixed
TENTATIVE). Registers stay untouched. A folder in scratch without `spike.md` is flagged by lint.

## Exit events

Any one of these ends the spike:

| Event | Who notices | Mechanical? |
|---|---|---|
| driving question answered or dropped | worker | no — `spike.py note <slug> --note "exit: …"` |
| derived work product reaches `final`, or is proposed as current-best example | worker | no — note it |
| the plan's final unit runs | final unit | no — it harvests (`references/addons.md`) |
| the human says done / drop it | anyone | no — note it |
| idle longer than `spike_inactive_days` (`agents/config.json`; research-case 2, code-repo 14, procedure and maker 30) | `spike.py list` (STALE), `lint.py` (`stale-spike`, DELETE), `status.py` (`due: spikes`) | yes |

Workers record the event; only a curator (or a final unit the plan names) closes. Discarding is a
valid outcome.

## show → propose → accept → close

Per spike, in this order, no step skipped.

**1. show** — `python3 -I agents/scripts/spike.py show <slug>`. Read `spike.md`, every TENTATIVE
line it finds in the folder, and the file listing. Open files only where a line needs evidence.

**2. propose** — sort everything into one of four bins; write proposals with `--origin <slug>`:

| Material | Test | Action |
|---|---|---|
| TENTATIVE line | decision trigger (`references/curate.md`, judgment 1) | `propose.py decision --title "…" --by curator --origin <slug>`, or let it go |
| something learned | ladder (judgment 2) | make the structure/check fix, or `propose.py lesson --rung … --origin <slug>` |
| a winner (candidate that won) | current best? (judgment 3) | into the profile's work folder as `final`, or `propose.py example --file <path> --settings k=v …` |
| open question still alive | — | `propose.py question --title "…" --by curator` |

Everything else stays behind and is deleted with the folder. Flags: set `--scope`, `--supersedes`,
`--contradicts`, `--replacement-cost high` honestly; they route the item to the human.

**3. accept** — `promote.py list`, then for each new item `promote.py accept <item> --by curator`
(lands `tentative`). `HUMAN` items stay in the inbox and go into the digest.

**4. close**

```
python3 -I agents/scripts/spike.py close <slug> --outcome harvested --by curator --note "2 decisions, 1 example"
python3 -I agents/scripts/spike.py close <slug> --outcome discarded --by curator --note "approach dropped: …"
```

Close moves the folder to `agents/.trash/` and appends a `SPIKE` line to `agents/LOG.md`. The
log line is the record; do not write a summary file.

Close only after step 3: a proposal that still points into the spike (`--refs`, `--file`) needs the
file copied out first — `propose.py example` copies it into the inbox; anything else, move it to a
work folder before closing.

## Soft delete: `agents/.trash/`

- Closed spikes keep their folder name in `agents/.trash/`; replaced examples land there as `<date>-example-<file>`.
- Restore within 30 days: move the folder back to `agents/scratch/` and note it in the log with `agents/scripts/append.sh`.
- `lint.py` flags trash older than 30 days (`trash-old`, DELETE); `lint.py --purge-trash` deletes it. Purge only in a curator run.
- After purge the archive is the cloud recycle bin (OneDrive/iCloud) and session transcripts. In git repos scratch and trash are ignored and never committed, so everything worth keeping must be proposed before close — repeat notes in the closing report.

## Report

One line per spike in the curator digest: `<slug> — harvested|discarded: n decisions, m lessons, k examples proposed; held: …`.
