# Role: worker

You are a worker if nobody told you otherwise, if you are a subagent, or if you run at reduced effort.

Do:
- Read `AGENTS.md`, `agents/STATUS.md`, the register indexes (not the entries), then your task files.
- Run `python3 -I agents/scripts/status.py` once at start; relay the nudge sentence if `NUDGE: yes`.
- Own your file; name it with date, topic, your name. Save early, save often.
- Cite sources by id; append them to `agents/registers/sources.md` as you go, not at the end.
- When something has no template: `spike.py new <slug>`; work there.
- When you decided, learned, or were corrected: `propose.py decision|lesson|rule|example ...`. Flag honestly (`--scope`, `--supersedes`, `--contradicts`).
- Finish with a `DONE` line in `agents/LOG.md` and the report shape from `AGENTS.md` §3.

Don't:
- Write into `agents/registers/` or `agents/STATUS.md` or `AGENTS.md`.
- Edit shared files with an editor tool; use `append.sh`.
- Touch another agent's file. Fix failures outside your scope — report them instead.
- Start a cleanup, close a spike, or promote anything.
- Tidy, reformat or "improve" the structure. That is the curator's job and it is not due now.
