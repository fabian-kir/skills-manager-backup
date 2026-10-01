---
name: shared-tool-scaffold
description: >-
  Scaffolds the clean base structure for a browser-based team tool: a Python/Flask
  backend serving a single-file index.html, built to run from a shared
  SharePoint/OneDrive folder on colleagues' Windows and Mac machines with
  zero-setup start files, a device-local virtualenv, YAML state persistence with
  atomic writes and rotating backups, and live multi-user sync with optimistic
  concurrency (rev polling + 409 conflict handling). Use this skill whenever the
  user wants to build a small internal/shared tool, a workshop or scoring tool, a
  team dashboard, or any local web app that several colleagues run from a shared
  drive and edit together — even if they don't say "scaffold". Also use it when
  someone asks to reproduce "the same base structure" as an existing tool of this
  kind, or asks how to make a Flask tool run on colleagues' machines with live
  sync and saving.
---

# Shared Tool Scaffold

## What this builds and why

This skill generates a proven base structure for a small, browser-based tool that
a handful of colleagues run **locally** from a **shared SharePoint/OneDrive
folder** and edit **together in real time**. It is deliberately dependency-light
(Python + Flask, no Node, no build step) so a non-technical colleague can
double-click one file and be running in under a minute.

The architecture solves the four things that make shared-folder tools break in
practice:

1. **OneDrive + virtualenv = breakage.** A venv committed to a synced folder
   corrupts across machines. So the venv lives **device-local**
   (`~/.cache/<slug>/venv` on Mac/Linux, `%LOCALAPPDATA%\<slug>\venv` on Windows),
   created on first run by the start script. Only source + state live in the
   shared folder.
2. **Two people saving at once = lost work.** The server owns a monotonic `rev`
   number. Every save sends the `baseRev` it started from; if another client saved
   in the meantime the server returns `409` and the client shows a
   "keep mine / load theirs" banner instead of silently clobbering.
3. **A crash mid-save = corrupt state.** Saves go to a temp file, `fsync`, then
   atomic `os.replace`. Every prior version is snapshotted to a **device-local**
   rotating backup dir first.
4. **Testing against live data = disaster.** All paths and the port are
   **env-overridable** (`<PREFIX>_STATE_FILE`, `<PREFIX>_BACKUP_DIR`,
   `<PREFIX>_PORT`) so tests never touch the real state file.

Because the server serves `index.html` fresh from disk on every request, **HTML/JS
edits need no restart** — only `server.py` changes do. This is the single biggest
day-to-day convenience of the setup, so preserve it.

## How to use it

The scaffold is produced by a deterministic script. Prefer it over hand-copying so
every project comes out identical.

### Step 1 — Gather parameters

Ask the user (or infer from context) for:

- **Project name** (display title, e.g. "AI Workshop Scoring") — `--name`
- **Slug** (lowercase, no spaces; used for the venv/cache dir, e.g. `ai_workshop`)
  — `--slug`. Derive a sensible default from the name if not given.
- **Port** (default `8080`) — `--port`
- **Theme color** (primary hex, default BCG green `#177b57`) — `--theme`
- **Destination folder** — `--dest` (the shared-drive folder the tool will live in)
- **Subtitle** (optional one-liner under the title) — `--subtitle`

### Step 2 — Run the scaffold script

```bash
python3 <skill-dir>/scripts/scaffold.py \
  --name "AI Workshop Scoring" \
  --slug ai_workshop \
  --port 8080 \
  --theme "#177b57" \
  --subtitle "Team edition" \
  --dest "/path/to/shared/folder/My Tool"
```

The script copies the templates from `assets/`, substitutes the placeholders, makes
the start scripts executable, and prints a summary + next steps. It refuses to
overwrite a non-empty destination unless `--force` is passed — check with the user
before forcing.

### Step 3 — Verify it boots

From the destination folder, run the platform start file (or, for a quick check,
create the venv-free smoke test):

```bash
<PREFIX>_PORT=8090 <PREFIX>_STATE_FILE=/tmp/smoke_state.yaml python3 server.py
```

Confirm `http://localhost:8090/health` returns `{"status":"ok",...}` and the page
loads. Then stop it.

### Step 4 — Explain deployment to the user

Tell them, concisely:

- Drop the whole folder into the shared SharePoint/OneDrive location.
- Colleagues open the folder and **double-click**: `start.command` (Mac — may need
  right-click → Open the first time to clear Gatekeeper) or `start.bat` (Windows).
  The script finds Python 3, builds the local venv, installs requirements, and
  opens the browser automatically.
- Everyone editing sees each other's changes within a few seconds. Saves are
  automatic (debounced) plus a manual Save button.
- If Python 3 isn't installed, the script prints the download link and stops.

## What gets generated

```
<dest>/
├── server.py            # Flask backend: state I/O, atomic writes, backups,
│                        #   rev/409 concurrency, /health, env config, schema ver.
├── index.html           # Single-file frontend + full live-sync client baked in.
│                        #   Contains a clearly marked "YOUR APP HERE" section.
├── requirements.txt     # flask + pyyaml (pinned)
├── start.command        # Mac double-click launcher (device-local venv)
├── start.sh             # Mac/Linux terminal launcher (identical logic)
├── start.bat            # Windows launcher
├── README.md            # Colleague-facing run instructions + architecture notes
├── DECISIONS.md         # ADR log, seeded with ADR-001 (the base architecture)
├── .gitignore           # venv, backups, __pycache__, temp state, OS cruft
└── favicon.svg          # tiny themed favicon (silences the /favicon.ico 404)
```

## Where the developer writes their app

`index.html` is intentionally the only place a developer edits for most features.
Point them at three anchors inside it:

- `serialize()` — returns the plain object that gets persisted and synced. Keep it
  to real data only; view-only preferences (filters, timers) stay out so they don't
  sync between machines.
- `hydrate(state)` — applies a loaded/remote state object to the app.
- `renderApp()` — the "YOUR APP HERE" render function.

The sync client (`apiLoad`, `apiSave`, `pollRev`, conflict banner, `autoSave`) is
already wired to those three functions, so a developer rarely touches networking.

## Adapting / extending

- **Add server-side features** (Excel export, file import, PDF, etc.): add routes
  in the marked section of `server.py`. Keep them stateless where possible; route
  all state mutation through the existing `/state` POST so concurrency stays intact.
- **Change the data model**: edit only `serialize()`/`hydrate()`/`renderApp()` in
  `index.html`. Bump `SCHEMA_VERSION` in `server.py` when the on-disk shape changes
  and add a migration in `migrate_state()` so old state files keep loading.
- **Re-theme**: the primary color is a single CSS variable (`--accent`) plus the
  favicon; both are set from `--theme` at scaffold time.

## Reference

`references/architecture.md` explains each guarantee (atomic write, backup
rotation, optimistic concurrency, the idle-adopt sync rule) in more depth. Read it
when a user asks *why* something is built the way it is, or when modifying the sync
or persistence logic — changing those without understanding the invariants is how
you reintroduce the lost-work and corrupt-state bugs this scaffold exists to
prevent.
