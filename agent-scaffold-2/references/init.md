# Mode: init — scaffold or upgrade a project

Goal: the folder gets `AGENTS.md` + `agents/` for one profile, filled with what the project's
inputs say and nothing more. Contract of the result: `references/structure.md`.

## 1. Look before asking

Run from the target folder, read-only:

```
ls -la                         # AGENTS.md? CLAUDE.md? agents/? .git? .claude/?
find . -maxdepth 2 -type f -not -path './.git/*' | head -100
```

- `agents/config.json` exists → **upgrade**: rerun init with the same profile; it adds missing files, keeps the rest. Read `agents/config.json` for the profile and skip questions it answers.
- `AGENTS.md` or `CLAUDE.md` exists without `agents/` → keep them; init skips existing files and prints `= kept`. Merging old rules into the new structure is a curator job, not init's.
- Note what the folder already tells you: name (folder name, README title), language of the files, inputs (briefs, PDFs, decks), repo facts (`.git`, test config), loose binaries.
- Looks like a one-shot task (a single file, no lifetime)? Ask once whether it is worth scaffolding. No → stop.

## 2. Pick the profile

| Folder shows | Profile |
|---|---|
| `.git`, source tree, tests, specs | `code-repo` |
| brief, client material, deadline, a written deliverable; no git | `research-case` |
| a repeatable task to package as a skill (form, slide, ticket) | `procedure` |
| `.3mf` / `.stl` / `.blend` / `.gcode`, slicer presets, photos | `maker` |

Read `profiles/<profile>.json` (`summary`, `work_folders`, `spike_inactive_days`, `register_write`,
`init_questions`) and the profile's section file next to it. Unclear between two → make the profile
your first question.

`register_write` comes with the profile and is not a question: code-repo and procedure write
decisions and lessons straight into the registers (`direct`), research-case and maker go through the
inbox. Override with `--register-write` only when the folder contradicts the profile's assumption —
a code repo with no verify command and no CI is an inbox project; a research case with one author
and a lint step in its daily rhythm may be direct. Say which you chose and why in the report.

## 3. Ask the input contract — one batch, at most six questions

`scripts/init.py` needs: `--name`, `--purpose`, `--deliverable`, `--owner` (required); `--deadline`,
`--out-of-scope`, `--confidentiality`, `--lang-files`, `--lang-chat`, `--human-lang de|en` (optional);
profile flags `--verify-command` (code-repo), `--machine-facts` (maker), `--skill-slug` (procedure).

Build one message, numbered:
1. Base: purpose and deliverable (one sentence each); owner, deadline or cadence; out of scope and confidentiality. Merge into ≤ 3 questions; drop any the folder already answers.
2. All `init_questions` of the profile (three each), unless the folder answers them.
3. Propose defaults instead of asking: name from the folder, files in the language you found, `--human-lang` from the language the human writes in.

Then wait. Never trickle questions one by one. Unanswered optional items → defaults (`none stated`, `nothing stated`).

Where the profile answers go:

| Profile | Answer → |
|---|---|
| code-repo | verify command → `--verify-command`; conventions and normative docs → `agents/STATUS.md` and §9 of `AGENTS.md` after init |
| research-case | recipient/form → `--deliverable`; streams → `01_context/` after init; confidential inputs → `--confidentiality` |
| procedure | product + hard rule → `--purpose`, then the top of `skill/SKILL.md`; output types and format references → `skill/references/` after init |
| maker | machines and materials → `--machine-facts`; "three things" → one `propose.py rule` each after init; inventory yes/no → step 6 |

## 4. Dry run, then real

`scripts/init.py` must be called by its path in this skill directory (it copies from `templates/`, `profiles/`, `adapters/`):

```
python3 -I <skill-dir>/scripts/init.py --profile <p> --target <dir> --name "…" --purpose "…" \
  --deliverable "…" --deadline "…" --owner "…" [profile flags] --dry-run
```

Show the human the `+` (create), `= kept`, `!` (manual step) lines in one short message. Then rerun
without `--dry-run`. The real run also builds the indexes, runs a first lint (so day one does not
nudge) and appends an `INIT` line to `agents/LOG.md`.

Handle the `!` lines:
- `CLAUDE.md` exists without `@AGENTS.md` → it is the human's file: ask, then add the one line `@AGENTS.md`.
- `.claude/settings.json` exists → hooks are optional; offer to merge from `agents/adapters/claude/settings.json`, do nothing without a yes. Other harnesses: `agents/adapters/codex-README.md`.
- `agents/config.json predates register_write` (upgrade of a pre-0.2 scaffold) → the scripts assume `inbox`. Tell the human the profile's default and add the key only after a yes; `agents/config.json` is the curator's file.
- `placeholders left in: …` → fill them now (step 5) from answers or inputs; never invent a value. No answer → ask, or leave it and name it in the report.

## 5. Derive context from the inputs — do not seed

Allowed, because it is derived from what the human gave:
- `agents/STATUS.md`: goal, first checkpoints, position line. Replace remaining `{{…}}` / `<set …>` / `fill in`.
- research-case: text extracts of `00_inputs/originals/` into `00_inputs/extracted/`; brief, research questions with ids (`A1`, `B2`) and framework into `01_context/`; terms the inputs define into `agents/registers/glossary.md`.
- code-repo: normative docs and verify command named in `AGENTS.md` §9 / `STATUS.md`, as the human stated them.
- procedure: `skill/SKILL.md` from the copied template; hard rule at its top.
- maker: machine facts already in §9 via `--machine-facts`.

Forbidden — these are earned by work, never written at init:
- files in `agents/registers/decisions/`, `agents/registers/lessons/`, `agents/registers/examples/`
- lines in `agents/registers/questions.md` (the brief's research questions go to `01_context/`, not here)
- inbox items or direct entries you made up. Exception: a correction or rule the human *stated* during the questions → `propose.py rule|decision --by init --inbox` (a rule is flagged for the human anyway; `--inbox` keeps a decision out of the registers until the human has seen it, whatever the mode).

## 6. Moving the human's files (maker, or any messy folder)

Only after a yes to the inventory question:
`python3 -I agents/scripts/inventory.py` → present the groups as a proposed move list → move only
what the human approves, one group at a time. Never delete; never rename sources.

## 7. Check and report

```
python3 -I agents/scripts/lint.py        # 0 placeholder / dead-path findings
python3 -I agents/scripts/status.py      # level OK, NUDGE: no
```

Report: profile, target, number of files created and kept, `!` items still open, what you derived
and from which input, the session-start line every agent now runs (`python3 -I agents/scripts/status.py`).
