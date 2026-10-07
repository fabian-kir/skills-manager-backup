#!/usr/bin/env python3
"""Client for the T3 Code environment API, for running handoff plans.

Writes go over HTTP to the environment's own command bus
(`POST /api/orchestration/dispatch`). Reads that need to be cheap and frequent
go straight to the SQLite projections, read-only, because polling the HTTP
snapshot for a watch loop is wasteful and the projections carry strictly more
detail -- including the literal shell command a unit is running right now.

Nothing here modifies T3 Code. It is a client of the contract published in
`packages/contracts/src/orchestration.ts`.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from http.cookiejar import MozillaCookieJar
from pathlib import Path

T3_HOME = Path.home() / ".t3" / "userdata"
STATE_DB = T3_HOME / "state.sqlite"
RUNTIME_FILE = T3_HOME / "server-runtime.json"
COOKIE_JAR = Path(
    os.environ.get("T3_COOKIE_JAR", Path.home() / ".config" / "t3-orchestrator" / "cookies.txt")
)

# Plan tables say "fable", "opus", "sonnet"; the API wants ids. Bare names
# resolve to the current generation T3 Code lists for its claudeAgent
# provider. Versioned keys exist for plans that pin an older model.
MODEL_IDS = {
    "fable": "claude-fable-5-1",
    "fable5.1": "claude-fable-5-1",
    "opus": "claude-opus-5-5",
    "opus5.5": "claude-opus-5-5",
    "opus5": "claude-opus-5",
    "sonnet": "claude-sonnet-5-5",
    "sonnet5.5": "claude-sonnet-5-5",
    "sonnet5": "claude-sonnet-5",
}
SHORT_NAMES = {v: k for k, v in MODEL_IDS.items() if "." not in k and k[-1].isalpha()}
SHORT_NAMES.update({"claude-opus-5": "opus5", "claude-sonnet-5": "sonnet5"})
# The plan's effort vocabulary. T3 Code also offers "ultracode" and
# "ultrathink"; neither is plan vocabulary and neither is accepted here.
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# No fast mode, ever. Fable has no such option and the plans never ask for it.
RUNTIME_MODES = {"approval-required", "auto-accept-edits", "auto", "full-access"}


# --------------------------------------------------------------------------
# transport
# --------------------------------------------------------------------------


def origin() -> str:
    """Prefer 127.0.0.1 over whatever the app advertises.

    The app writes its LAN address here when serving remotely, and that address
    changes with DHCP. A credential is bound to an origin, so pinning loopback
    is what stops a re-pair every time the network moves.
    """
    env = os.environ.get("T3_ORIGIN")
    if env:
        return env.rstrip("/")
    try:
        port = json.loads(RUNTIME_FILE.read_text())["port"]
    except Exception:
        port = 3773
    return f"http://127.0.0.1:{port}"


def _opener() -> urllib.request.OpenerDirector:
    COOKIE_JAR.parent.mkdir(parents=True, exist_ok=True)
    jar = MozillaCookieJar(str(COOKIE_JAR))
    if COOKIE_JAR.exists():
        jar.load(ignore_discard=True, ignore_expires=True)
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), jar


def call(path: str, payload: dict | None = None, method: str | None = None) -> dict:
    opener, jar = _opener()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        origin() + path,
        data=data,
        method=method or ("POST" if data else "GET"),
        headers={"content-type": "application/json"},
    )
    try:
        with opener.open(req, timeout=30) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:400]
        if exc.code == 401:
            raise SystemExit(
                f"401 from {path}: {detail}\n"
                "Credential missing or expired. Mint a pairing link in T3 Code "
                "(Settings, paired clients) and run:  t3.py pair <TOKEN>"
            )
        raise SystemExit(f"HTTP {exc.code} from {path}: {detail}")
    COOKIE_JAR.parent.mkdir(parents=True, exist_ok=True)
    jar.save(ignore_discard=True, ignore_expires=True)
    COOKIE_JAR.chmod(0o600)
    return json.loads(body) if body else {}


def dispatch(command: dict) -> dict:
    command.setdefault("commandId", str(uuid.uuid4()))
    command.setdefault("createdAt", now())
    return call("/api/orchestration/dispatch", command)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# --------------------------------------------------------------------------
# read side -- SQLite projections, read-only
# --------------------------------------------------------------------------


def db() -> sqlite3.Connection:
    if not STATE_DB.exists():
        raise SystemExit(f"no database at {STATE_DB}")
    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def age_minutes(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        stamp = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - stamp).total_seconds() / 60


def project_id(name: str) -> str:
    snap = call("/api/orchestration/snapshot")
    for proj in snap["projects"]:
        if proj["title"] == name or proj["id"] == name:
            return proj["id"]
    known = ", ".join(p["title"] for p in snap["projects"])
    raise SystemExit(f"no project named {name!r}. Known: {known}")


def model_id(model: str) -> str:
    key = model.lower().replace(" ", "").replace("-", "")
    return MODEL_IDS.get(key, model)


def model_selection(model: str, effort: str, context: str = "1m") -> dict:
    if effort not in EFFORTS:
        raise SystemExit(f"effort {effort!r} not one of {list(EFFORTS)}")
    return {
        "instanceId": "claudeAgent",
        "model": model_id(model),
        "options": [
            {"id": "effort", "value": effort},
            {"id": "contextWindow", "value": context},
        ],
    }


def describe_selection(selection: dict | None) -> str:
    """'fable high' from a stored modelSelection; '-' when the thread has none."""
    if not selection:
        return "-"
    mid = selection.get("model") or "?"
    opts = {o.get("id"): o.get("value") for o in selection.get("options") or []}
    short = SHORT_NAMES.get(mid, mid)
    effort = opts.get("effort") or opts.get("reasoningEffort") or "?"
    return f"{short} {effort}"


def current_selection(thread_id: str) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "select model_selection_json from projection_threads where thread_id = ?",
            (thread_id,),
        ).fetchone()
    if row is None:
        raise SystemExit(f"no thread {thread_id}")
    if not row["model_selection_json"]:
        return None
    try:
        return json.loads(row["model_selection_json"])
    except json.JSONDecodeError:
        return None


def merged_selection(thread_id: str, model: str | None, effort: str | None, context: str | None) -> dict:
    """Thread's stored selection with the given fields overridden.

    Lets `start --effort xhigh` keep the model, and `model --model fable` keep
    the effort. Missing pieces fall back to fable high, the plan's own default
    for anything that reaches an escalation.
    """
    cur = current_selection(thread_id) or {}
    opts = {o.get("id"): o.get("value") for o in cur.get("options") or []}
    stored_effort = opts.get("effort")
    if stored_effort not in EFFORTS:  # T3-only values such as ultracode
        stored_effort = None
    return model_selection(
        model or cur.get("model") or "fable",
        effort or stored_effort or "high",
        context or opts.get("contextWindow") or "1m",
    )


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def cmd_pair(args) -> None:
    result = call("/api/auth/browser-session", {"credential": args.token})
    print(json.dumps(result, indent=1))
    expires = result.get("expiresAt", "")
    print(f"\ncookie stored 0600 at {COOKIE_JAR}")
    print(f"expires {expires} -- re-pair after that, not per handoff")


def cmd_whoami(args) -> None:
    print(json.dumps(call("/api/auth/session"), indent=1))


def cmd_projects(args) -> None:
    for proj in call("/api/orchestration/snapshot")["projects"]:
        print(f"{proj['id']}  {proj['title']}  {proj['workspaceRoot']}")


def cmd_create(args) -> None:
    thread_id = str(uuid.uuid4())
    dispatch(
        {
            "type": "thread.create",
            "threadId": thread_id,
            "projectId": project_id(args.project),
            "title": args.title,
            "modelSelection": model_selection(args.model, args.effort, args.context),
            "runtimeMode": args.runtime,
            "interactionMode": "default",
            "branch": args.branch,
            # null means "current checkout". A path here means a worktree.
            "worktreePath": args.worktree,
        }
    )
    print(thread_id)


def cmd_start(args) -> None:
    text = Path(args.prompt_file).read_text() if args.prompt_file else args.text
    if not text or not text.strip():
        raise SystemExit("refusing to start a turn with an empty prompt")
    command = {
        "type": "thread.turn.start",
        "threadId": args.thread,
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "user",
            "text": text,
            "attachments": [],
        },
        "runtimeMode": args.runtime,
        "interactionMode": "default",
    }
    if args.model or args.effort or args.context:
        selection = merged_selection(args.thread, args.model, args.effort, args.context)
        command["modelSelection"] = selection
        print(f"turn runs as {describe_selection(selection)}")
    dispatch(command)
    print(f"started turn on {args.thread}")


def cmd_model(args) -> None:
    """Change a thread's model or effort for its next turns. Up only is policy, not code."""
    before = current_selection(args.thread)
    after = merged_selection(args.thread, args.model, args.effort, args.context)
    dispatch({"type": "thread.meta.update", "threadId": args.thread, "modelSelection": after})
    print(f"{describe_selection(before)} -> {describe_selection(after)} on {args.thread}")


def cmd_interrupt(args) -> None:
    dispatch({"type": "thread.turn.interrupt", "threadId": args.thread})
    print(f"interrupted {args.thread}")


def cmd_stop(args) -> None:
    dispatch({"type": "thread.session.stop", "threadId": args.thread})
    print(f"stopped session on {args.thread}")


def cmd_rename(args) -> None:
    dispatch({"type": "thread.meta.update", "threadId": args.thread, "title": args.title})
    print(f"renamed {args.thread}")


def cmd_delete(args) -> None:
    dispatch({"type": "thread.delete", "threadId": args.thread})
    print(f"deleted {args.thread}")


def cmd_messages(args) -> None:
    with db() as conn:
        rows = conn.execute(
            "select role, text from projection_thread_messages "
            "where thread_id = ? order by created_at",
            (args.thread,),
        ).fetchall()
    for row in rows:
        print(f"--- {row['role']}\n{row['text']}\n")


def _thread_rows(conn, project: str | None):
    sql = (
        "select t.thread_id, t.title, t.branch, t.worktree_path, "
        "       t.pending_approval_count, t.pending_user_input_count, "
        "       t.model_selection_json, "
        "       p.title as project "
        "from projection_threads t "
        "join projection_projects p on p.project_id = t.project_id "
        "where t.deleted_at is null and t.archived_at is null"
    )
    params: list = []
    if project:
        sql += " and p.title = ?"
        params.append(project)
    sql += " order by t.updated_at desc"
    return conn.execute(sql, params).fetchall()


def _latest_turn(conn, thread_id: str):
    return conn.execute(
        "select state, started_at, completed_at from projection_turns "
        "where thread_id = ? order by requested_at desc limit 1",
        (thread_id,),
    ).fetchone()


def _running_command(conn, thread_id: str):
    """The shell command this thread is inside right now, if any.

    A tool call appears as tool.started / tool.updated / tool.completed rows.
    The newest row whose payload still says inProgress is the live one.
    """
    rows = conn.execute(
        "select payload_json, created_at from projection_thread_activities "
        "where thread_id = ? and kind in ('tool.started','tool.updated','tool.completed') "
        "order by created_at desc limit 40",
        (thread_id,),
    ).fetchall()
    seen: set[str] = set()
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            continue
        call_id = payload.get("toolCallId")
        if not call_id or call_id in seen:
            continue
        seen.add(call_id)
        if payload.get("status") != "inProgress":
            continue
        data = payload.get("data") or {}
        command = data.get("command") or (data.get("input") or {}).get("command")
        return {
            "tool": data.get("toolName") or payload.get("title"),
            "command": command,
            "since": row["created_at"],
        }
    return None


def classify(turn, pending_approval, pending_input, running, stall_minutes):
    if pending_approval or pending_input:
        return "BLOCKED-ON-YOU"
    if turn is None:
        return "NEW"
    if turn["state"] in ("running", "pending", "starting"):
        age = age_minutes(running["since"]) if running else age_minutes(turn["started_at"])
        if age is not None and age >= stall_minutes:
            return "STALLED"
        return "RUNNING"
    return "IDLE"


def cmd_status(args) -> None:
    with db() as conn:
        rows = _thread_rows(conn, args.project)
        for row in rows:
            turn = _latest_turn(conn, row["thread_id"])
            running = _running_command(conn, row["thread_id"]) if turn else None
            state = classify(
                turn,
                row["pending_approval_count"],
                row["pending_user_input_count"],
                running,
                args.stall_minutes,
            )
            if args.only and state != args.only:
                continue
            where = row["worktree_path"] or "current checkout"
            try:
                selection = json.loads(row["model_selection_json"] or "null")
            except json.JSONDecodeError:
                selection = None
            print(f"{state:15} {row['title'][:48]:48} {row['branch'] or '-':28} {where}")
            print(f"{'':15} {row['thread_id']}  {describe_selection(selection)}")
            if running:
                age = age_minutes(running["since"])
                mins = f"{age:.0f}m" if age is not None else "?"
                command = (running["command"] or "").strip().replace("\n", " ")
                print(f"{'':15} {running['tool']} for {mins}: {command[:110]}")
            print()


def cmd_running(args) -> None:
    """Every live tool call across every thread, oldest first. The runaway finder."""
    with db() as conn:
        found = []
        for row in _thread_rows(conn, args.project):
            running = _running_command(conn, row["thread_id"])
            if running:
                found.append((age_minutes(running["since"]) or 0, row, running))
        for age, row, running in sorted(found, reverse=True):
            command = (running["command"] or "").strip().replace("\n", " ")
            print(f"{age:6.0f}m  {row['title'][:40]:40} {running['tool']}: {command[:100]}")
            print(f"{'':8}  {row['thread_id']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pair", help="redeem a one-time pairing token")
    p.add_argument("token")
    p.set_defaults(func=cmd_pair)

    sub.add_parser("whoami", help="show the current session and its scopes").set_defaults(
        func=cmd_whoami
    )
    sub.add_parser("projects", help="list projects and ids").set_defaults(func=cmd_projects)

    p = sub.add_parser("create", help="create a configured thread, unstarted")
    p.add_argument("--project", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--model", default="opus", help="fable | opus | sonnet, or a full id")
    p.add_argument("--effort", default="high", choices=EFFORTS)
    p.add_argument("--context", default="1m", choices=["200k", "1m"])
    p.add_argument("--branch", default=None)
    p.add_argument(
        "--worktree",
        default=None,
        help="absolute path; omit for the current checkout (the usual case)",
    )
    p.add_argument("--runtime", default="auto", choices=sorted(RUNTIME_MODES))
    p.set_defaults(func=cmd_create)

    p = sub.add_parser(
        "start",
        help="send a prompt and start a turn; --model/--effort override for this turn onward",
    )
    p.add_argument("thread")
    p.add_argument("--prompt-file")
    p.add_argument("--text")
    p.add_argument("--model", default=None, help="fable | opus | sonnet; default: thread's own")
    p.add_argument("--effort", default=None, choices=EFFORTS, help="default: thread's own")
    p.add_argument("--context", default=None, choices=["200k", "1m"])
    p.add_argument("--runtime", default="auto", choices=sorted(RUNTIME_MODES))
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("model", help="change a thread's model/effort for its next turns")
    p.add_argument("thread")
    p.add_argument("--model", default=None, help="fable | opus | sonnet; default: keep")
    p.add_argument("--effort", default=None, choices=EFFORTS, help="default: keep")
    p.add_argument("--context", default=None, choices=["200k", "1m"])
    p.set_defaults(func=cmd_model)

    for name, func, helptext in (
        ("interrupt", cmd_interrupt, "stop the current turn, keep the session"),
        ("stop", cmd_stop, "stop the whole session"),
        ("delete", cmd_delete, "delete a thread"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("thread")
        p.set_defaults(func=func)

    p = sub.add_parser("rename", help="retitle a thread")
    p.add_argument("thread")
    p.add_argument("title")
    p.set_defaults(func=cmd_rename)

    p = sub.add_parser("messages", help="print a thread's conversation")
    p.add_argument("thread")
    p.set_defaults(func=cmd_messages)

    p = sub.add_parser("status", help="one line per thread with its live command")
    p.add_argument("--project")
    p.add_argument("--stall-minutes", type=int, default=45)
    p.add_argument(
        "--only",
        choices=["RUNNING", "STALLED", "BLOCKED-ON-YOU", "IDLE", "NEW"],
    )
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("running", help="every live tool call, oldest first")
    p.add_argument("--project")
    p.set_defaults(func=cmd_running)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
