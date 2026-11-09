# Codex (and other harnesses) — wiring notes

Nothing here is required. The structure is enforced by `AGENTS.md` plus the scripts, which any
harness or human can run. Harness-specific hooks are a bonus.

- **Entry file.** Codex reads `AGENTS.md` natively (nearest file wins). Claude Code reads `CLAUDE.md`,
  which contains only `@AGENTS.md`. Cursor and others: point their rules file at `AGENTS.md` or paste
  its §2–§6 as the always-on rule.
- **Session start.** No hook: `AGENTS.md` §6 tells every session to run `python3 -I agents/scripts/status.py`
  first. If your harness offers a session-start hook, run that command there so its one-line output
  lands in context automatically.
- **Write logging / stop gate.** Without hooks, agents write their own `DONE` lines (§3). If the
  harness has post-tool or stop hooks, adapt `agents/adapters/claude/log_write_hook.py` and
  `stop_gate.py` — both read JSON on stdin and only depend on `agents/config.json`.
- **Skills.** Codex discovers skills in `.agents/skills/<name>/SKILL.md`; Claude Code in
  `.claude/skills/<name>/`. A procedure-profile project keeps its skill in `skill/` and can be
  symlinked or copied into either location.
- **CI.** `python3 -I agents/scripts/lint.py --strict` and `python3 -I agents/scripts/index.py --check`
  are safe to run in CI; both exit non-zero on findings.
