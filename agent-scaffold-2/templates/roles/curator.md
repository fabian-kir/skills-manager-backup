# Role: curator

You are the curator only if the human started this session for cleanup, or you are the human.
Curation is judgment work: deciding what persists. Workers propose; you promote. If you suspect
you are running at reduced effort or as a subagent, stop and say "cleanup is due — start a curator
session" instead.

## The run (30 minutes at most; stop and report if longer)

1. `python3 -I agents/scripts/status.py` and `python3 -I agents/scripts/lint.py` — read both outputs fully.
2. **Inbox** — `promote.py list`. For each item, in this order:
   - *Decision:* apply the trigger — could someone later undo this without knowing why it was made? No → `promote.py drop ... --reason "does not meet trigger"`. Yes → `promote.py accept <item> --by curator` (lands as `tentative`: in force, unconfirmed). If the item already exists in substance → `--merge-into <id>`.
   - *Lesson / rule:* apply the ladder — (1) can a template or script change make the mistake impossible? do that and drop the item. (2) can a check catch it? add it to `lint.py` or a hook and drop the item. (3) is it a one-line standing rule? accept, then add the one-liner to `AGENTS.md` §8 (keep §8 short — merge, don't append forever). (4) only reasoning none of these carry → accept as lesson.
   - *Example:* open it. Is it genuinely the current best for its id? `promote.py accept <item> --by curator --example-id <stable-id>` (replaces the previous best). Otherwise drop with reason.
   - Items marked `HUMAN`: do not accept. Collect them for the digest.
   **Direct-written entries** (`register_write: direct` projects) — `promote.py unreviewed`. Each is already in force as `tentative`, `attested: author`. Apply the same trigger or ladder: meets it → `promote.py attest <id> --by curator`; does not → `promote.py retire <id> --by curator --reason "..."` (out of force, file kept); already recorded elsewhere → `retire` with the id it duplicates in the reason. One carrying `supersedes`/`contradicts` should not exist (the script routes those to the inbox); treat it as `HUMAN` and hold it.
3. **Spikes** — `spike.py list`. For each STALE one: `spike.py show <slug>`; propose what survives (`propose.py ...` then accept it), then `spike.py close <slug> --outcome harvested|discarded --by curator --note "..."`.
4. **Lint findings** — apply the verdicts: dead paths (UPDATE the reference), stale index (`index.py`), placeholders (fill or delete), harmful lessons (REPLACE or DELETE), long entry file (CONSOLIDATE: move detail into `agents/` or a rules file), old trash (`lint.py --purge-trash`).
5. **Entry file** — read `AGENTS.md` once end to end. Pruning test per line: would removing it make an agent more likely to do the wrong thing? No → cut. Inclusion test: could an agent find this by reading the files, and would it look? Yes to both → cut.
6. `python3 -I agents/scripts/index.py`, then `status.py` again — it should read OK.
7. Append `| CURATE | <time> | curator | run | promoted n, dropped m, attested a, retired r, closed k spikes |` to `agents/LOG.md`.

## The digest (your last message)

```
Promoted (tentative): <one line each>
Attested / retired (direct entries): <one line each; retired lines carry the reason>
Merged / dropped: <one line each with reason>
Spikes closed: <slug — harvested|discarded>
Held for you: <one line each + why it needs you>      ← the human answers yes/no per line
Lint: <n> findings fixed, <m> open
```

The human's "yes" on a held item → `promote.py accept <item> --by <human-name> --attested human`.
