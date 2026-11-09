# Mode: curate — empty the inbox, apply lint, keep the entry file a router

The step-by-step run is [templates/roles/curator.md](../templates/roles/curator.md) (in a project:
`agents/roles/curator.md`). Follow it. This file says when the run starts, how to make its three
judgments, and how the digest closes it.

## When it starts

Only on an explicit start — role by invocation, never self-assessment:
- the human says cleanup / curator run / aufräumen, or answers yes to a nudge; or
- the human runs it themselves.

Before step 1: if you were started as a subagent or at reduced effort, you are a worker. Say
"cleanup is due — start a curator session" and stop. Never start a cleanup because things look messy.

How the nudge reaches the human (workers relay it, they do not judge it):
- every session runs `python3 -I agents/scripts/status.py`; level `DUE` when inbox ≥ 5 or oldest > 7 days, direct-written entries unreviewed ≥ 10 or oldest > 14 days, a spike idle past `spike_inactive_days`, scratch > 200 files or 200 MB, an index older than its register, lint older than 14 days or ≥ 5 open findings, `AGENTS.md` > 200 lines. Thresholds: `agents/config.json`.
- `CRITICAL` when inbox ≥ 15, scratch ≥ 3× threshold, or an inbox item `contradicts`/`supersedes` an entry — ignores snoozes.
- last line `NUDGE: yes` → the worker ends its first reply with one sentence offering a run, then `status.py --nudged`. Human says not now → `status.py --snooze`. It nudges again only when the numbers moved ≥ 50 % or a new trigger fires.

## The run: 30 minutes, then stop

Order (detail in `agents/roles/curator.md`): status + lint → inbox → direct-written entries (`promote.py unreviewed`) → stale spikes (procedure:
`references/harvest.md`) → lint verdicts → entry-file pruning → `index.py` + `status.py` → `CURATE`
line in `agents/LOG.md` → digest. Past 30 minutes: finish the item in hand, leave the rest in the
inbox, and say so in the digest. A partial run with an honest digest beats a long one.

Work only through the scripts: `promote.py` for registers, `spike.py close` for spikes,
`index.py` for indexes. Hand edits are limited to `AGENTS.md` §8, the fixes the ladder asks for, and
flipping `status: tentative` → `confirmed` after a human yes.

## Judgment 0 — direct-written entries: same tests, different verbs

In a `register_write: direct` project (`references/structure.md`, "Direct or inbox") workers have
already written unflagged decisions and lessons into the registers. They are in force, `tentative`,
`attested: author`. `promote.py unreviewed` lists them oldest first. Per entry apply judgment 1 or 2
below exactly as for an inbox item, then:
- meets the trigger or sits on the right rung → `promote.py attest <id> --by curator` (attested becomes `curator`; status stays `tentative`);
- does not → `promote.py retire <id> --by curator --reason "does not meet trigger"` — out of force, file kept;
- duplicates an existing entry → `retire` naming the id it duplicates; add anything new to the existing entry by hand only if it is a sentence, otherwise leave it;
- climbs the ladder (a check or structure fix would carry it) → make the fix, then `retire --reason "fixed by <path>"`;
- carries `supersedes` or `contradicts`, or reads as chosen *for* the user → it should have gone to the inbox: do not attest; hold it for the digest as `HUMAN`.
A direct entry is never edited by the curator except through these verbs and `supersede`.

## Judgment 1 — decision: the trigger sentence

> Could someone later undo this without knowing why it was made?

- No (obvious from the artefact, trivially reversible, already said by the commit or log line) → `promote.py drop <item> --by curator --reason "does not meet trigger"`.
- Yes, and new → `promote.py accept <item> --by curator`. It lands `tentative`: in force, unconfirmed. That is the normal end state; do not ask the human to confirm it.
- Yes, but already recorded in substance → `--merge-into <id>`.
- Check the worker's flags. Item that was chosen *for* the user, reinterprets an ambiguous instruction, contradicts an in-force entry, or is costly to undo, but is not flagged `HUMAN`: do not accept. Leave it in the inbox and put it under "Held for you".
- `HUMAN` items: `promote.py` refuses them without `--attested human`. Never pass that flag on your own.

## Judgment 2 — lesson or rule: the ladder, top rung first

1. **Structure** — can a template, folder or script change make the mistake impossible? Make the change, then `drop --reason "fixed by <path>"`.
2. **Check** — can `agents/scripts/lint.py`, a test, or a hook catch it? Add the check, then drop with the same kind of reason.
3. **Rule** — one imperative line with its situation? Rules are always flagged `HUMAN` (they touch `AGENTS.md`): hold for the digest. After the human's yes: `promote.py accept <item> --by <human> --attested human`, then add the one-liner to `AGENTS.md` §8 by hand — merge with an existing line before appending.
4. **Lesson** — only reasoning none of the above can carry → accept as lesson.

The proposer's `rung:` is a guess; you decide. Each rung climbed is context no future session pays for.
Existing lessons: a `harmful` mark (`promote.py mark <id> --harmful --by …`) sends the entry to the human; lint says REPLACE once harmful > helpful.

## Judgment 3 — example: current best, or nothing

Open the file and its sidecar (`promote.py show <item>`), then `agents/registers/examples/INDEX.md`.
- Accept only if it beats the current entry for that id, or the id is new: `promote.py accept <item> --by curator --example-id <stable-id>`. The previous best moves to `agents/.trash/`.
- `<stable-id>` names the kind of output, never a version or date (`bracket-pla-0.4`, not `bracket-v3`).
- Drafts, variants, "also good" → drop with reason. One per id; no galleries.
- Settings missing from the sidecar, or external material without provenance → drop with the reason, or hold if only the human knows them.

## The digest — the human answers yes/no

Last message of the run, in the shape `agents/roles/curator.md` gives. Rules for it:
- One line per item; "Held for you" lines end with the reason it needs the human and are answerable with yes or no.
- Nothing promoted silently: every accept, merge, drop, attest, retire and spike close appears once.
- Mention what you did not reach in 30 minutes.

Answers:
- yes → `promote.py accept <item> --by <human-name> --attested human` (add `--as confirmed` if the human confirms it outright); for a rule, then edit §8. A tentative entry the human confirms later: `promote.py confirm <id> --by <human-name>`.
- no → `promote.py drop <item> --by <human-name> --reason "human: no"`.
- no answer → item stays in the inbox; `status.py` raises it again by age.

Then `python3 -I agents/scripts/index.py` and `status.py` once more; it should read `OK`.
