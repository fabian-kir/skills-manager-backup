# Agent log (append-only)

One line per event. `AUTO` lines come from a write hook where one is installed; `DONE` lines are written by agents with `agents/scripts/append.sh`; `PROPOSE`, `PROMOTE`, `SPIKE`, `CURATE` lines come from the scripts.
Done-line: `| DONE | <ISO time> | <agent> | <file or scope> | <three-word status> |`

| kind | time | who | what | note |
|---|---|---|---|---|
