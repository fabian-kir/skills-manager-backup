# Add-ons — how other skills plug into a scaffolded project

An add-on is any skill that does task work in a project with `agents/` (handoff planning, slide or
document generation, ticket filing). It does not invent folders or registers: it reads the
project's conventions and writes into the slots below. The base skill stays small; task skills
compound into the same registers.

## Detect

`agents/config.json` exists above the working directory → the project is scaffolded: use the slots.
Absent → the add-on runs its own default workflow; do not create `agents/` from an add-on.

## Slots

| Slot | Read | Write | How |
|---|---|---|---|
| `agents/scratch/<date>-<slug>/` | own spike | yes, freely | `spike.py new <slug> --goal … --exit …`; candidates, drafts, plans, notes live here |
| `agents/inbox/` | no (curator only) | yes | `propose.py decision\|lesson\|rule\|example …`, always `--origin <slug>` |
| `agents/registers/examples/` | `INDEX.md` first, then the example | never directly | `propose.py example --file … --settings k=v … [--source-url … --publisher … --usage-basis …]` |
| `agents/registers/sources.md` | yes | append only | `agents/scripts/append.sh agents/registers/sources.md "<row>"`, row shape in the register header |
| `agents/registers/questions.md` | yes | append only | `propose.py question --title … --by …` |
| `agents/LOG.md` | tail | append only | `DONE` line via `append.sh` |
| decisions/lessons `INDEX.md`, `agents/registers/glossary.md`, `agents/STATUS.md` | yes | no | follow them; report through LOG |
| profile work folders (`agents/config.json` "work_folders") | yes | the add-on's own output files | final outputs land here, per the profile's §9 rules |

Never: write into `agents/registers/`, edit `AGENTS.md`, close a spike unless the plan names your
unit as the harvester, keep a second log, decision list or example gallery of your own.

## Declare the slots in the add-on's SKILL.md

Two lines, so a curator can see where the add-on's output should be:

```
Reads (agent-scaffold): agents/registers/examples/INDEX.md, agents/registers/sources.md
Writes (agent-scaffold): agents/scratch/<date>-<slug>/, agents/inbox/ via propose.py
```

`lint.py` does not check add-on slots yet; the curator checks the declaration by eye. Files an
add-on leaves outside its slots are inventory candidates (`agents/scripts/inventory.py`).

## planning-handoff: a handoff plan is a spike with a plan

planning-handoff obeys "repository policy" for where `handoff/` lives and whether it is tracked
(it reads repository instructions and runs `git check-ignore`). It needs no change: the policy
lines come from the code-repo profile's §9, which init writes into `AGENTS.md`:

> Handoff plans (planning-handoff skill) live in `agents/scratch/<date>-<plan>/handoff.md` with the
> "Notes between units" section there; the final integration unit harvests: decisions made by units →
> `propose.py decision --origin <plan>`, then `spike.py close`. `agents/scratch/` is gitignored: never
> force-add; repeat every note in the closing report.

Mapping:

| planning-handoff | agent-scaffold |
|---|---|
| `handoff/` folder | the spike: `spike.py new <plan> --goal "<plan goal>" --exit "final unit merged"`, then the planner writes `handoff.md` and unit prompts into that folder |
| persistence check | `agents/scratch/` is in `.gitignore` → the plan stays local and untracked, no `git add -f`, no commit-then-delete |
| unit prompts, "Notes between units" | files and section inside the spike folder; notes stay in `handoff.md`, not in `spike.md` |
| a unit chooses something a later reader could undo | `propose.py decision --origin <plan>` (lands in inbox as `proposed`); also `spike.py tentative <plan> …` |
| a unit learns a quirk | `propose.py lesson --rung check\|rule\|lesson --origin <plan>` |
| durable decisions must leave the scratch plan | they reach the registers only through the inbox; the next curator run promotes them |
| final unit (review, verify, wait for user) | also the harvester: proposes remaining TENTATIVE lines, then `spike.py close <plan> --outcome harvested --by <unit>` after the user approved the merge |

Units remain workers: they propose, never promote. The final unit closes the spike because the plan
names it; it does not accept inbox items. `references/harvest.md` is its procedure.

Other profiles: the policy lines exist only in the code-repo section. To run planning-handoff in a
research-case, procedure or maker project, the curator adds the same lines to `AGENTS.md` §9 — an
entry-file change, so only after the human's yes.

Not covered: a plan that must travel through git (another machine, a shared branch) cannot live in
gitignored scratch. Ask the human; record the answer as a decision before planning.

## Example: a slide or document generator

- Candidates in a spike; only the winner leaves it.
- Winner → the profile's output folder (procedure: `output/<stable-id>.<ext>` plus its `.json`), then `propose.py example --file … --settings …` if later work should copy it.
- External images or data → provenance on the example (`--source-url`, `--publisher`, `--usage-basis`) and a line in `agents/registers/sources.md`.
- Layout choices the human could later undo → `propose.py decision`; corrections the human gives → `propose.py rule`.
