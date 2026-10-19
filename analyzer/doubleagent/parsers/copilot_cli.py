"""GitHub Copilot CLI (`copilot`) session state (issue 50).

Closed source. Validated against the shipped event schema
(`schemas/session-events.schema.json`), the minified CLI and the Rust
runtime addon of `@github/copilot-darwin-arm64` 1.0.98, and real installs
on macOS and Linux (Copilot CLI 1.0.98, October 2026), with a synthetic
fixture; see `research/copilot-cli.md`. Paths are relative to the home, under
`.copilot` or, on installs that predate the XDG migration, under
`.local/state/.copilot` and `.config/.copilot` (written `<home>` below);
the bundle has no platform branch, so macOS, Linux and Windows share the
layout.

* `<home>/session-state/<session id>/events.jsonl`, the primary store: one
  event per line, envelope `id`, `parentId`, `timestamp` (ISO 8601 UTC),
  `type`, `data`, and `agentId` on a subagent's events. `parentId` is not
  read: a rewind truncates the file rather than branching it. Rows follow
  the log order, each at its line's `timestamp`; `session_id` is the
  directory name (= `session.start` `sessionId`). By `type`:
  - `session.start` (`copilotVersion`, `producer`, `context.cwd`,
    `context.branch`): `session start: copilot <version> producer=<p>
    cwd=<cwd>`; sets the project path and branch. `session.resume`
    (`context`): `session resumed`, and updates them;
    `session.context_changed` (the context, as `data` or `data.context`)
    updates them with no row.
  - `system.message` (`content`, `role`): `system prompt: <content>`, or
    `developer message: <content>` for `role` `developer`, never shortened.
  - `user.message` (`content`, `source`, `isAutopilotContinuation`, the
    envelope's `agentId`): `user` for typed input (no `agentId`, `source`
    absent or `user`, not a continuation), otherwise `system`
    `<label>: <content>`, the label `auto-continuation`, `subagent task`
    or the `source` value. `transformedContent` (the prompt with injected
    context) is not read: `turns.user_message` and the history repeat
    `content`.
  - `assistant.message` (`content`, `model`, `reasoningText`,
    `reasoningBlocks.blocks[].summary[].text`, `toolRequests[]` with
    `toolCallId`, `name`, `arguments`): an `assistant` row when `content`
    is not empty, a `thinking` row with `include_thinking` (`reasoningText`,
    else the block summaries; the encrypted blobs are never read), then
    one `tool_use` per request. `assistant.reasoning` (`content`) is a
    `thinking` row with `include_thinking`.
  - `tool.execution_start` (`toolCallId`, `toolName`, `arguments`): a
    `tool_use` only when no earlier request had the call id (a call the
    user or a subagent made). `tool.user_requested`: a `tool_use` prefixed
    `user requested: `. A `tool_use` text is `arguments` when it is a
    string (a `custom` grammar tool such as `apply_patch`), else its
    `command`, `url`, `query`, `path` or `input`, else compact JSON.
  - `tool.execution_complete` (`toolCallId`, `success`, `result.content`,
    `result.detailedContent`, `error.message`,
    `shellExecution.exitCode`): a `tool_result`. The schema calls
    `content` the concise, possibly truncated text sent to the model and
    `detailedContent` the complete one, so `detailedContent` is preferred;
    but a successful skill invocation puts the concise text in
    `detailedContent` (one observed record: 25 characters beside an
    8091-character `content`), so `content` wins when it is the longer.
    Prefixed `[exit N] ` for a non-zero exit code, and `error.message` on
    a line of its own when `success` is false.
  - Permissions (`permission.requested`: `permissionRequest.kind`,
    `.toolCallId`, `.intention`, `.fullCommandText`, `.url`, `.fileName`,
    `.path`, `.serverName`, `.toolName`, `permissionMode`, `agentMode`;
    `permission.completed`: `toolCallId`, `decisionSource`, `result.kind`,
    `.locationKey`, `.approval`, `.directories`, `.feedback`, `.rules`,
    `.message`, `.reason`, `.path`): `system` rows beside the call,
    `tool_use_id` the call id and `tool_name` the name its request gave:
    `permission request: <kind> <target> intention=<intention>`, then
    `permission mode: <mode> agent=<agentMode>` the first time and
    `permission mode: <old> -> <new>` when either changes;
    `permission decision: <kind> source=<decisionSource or ->` followed by
    ` location=`, ` approval=`, ` directories=`, ` feedback=`, ` rules=`,
    ` reason=`, ` path=` and ` message=` for the keys present (objects as
    compact JSON). `permission.carriedForward` is `permission decision:
    carried-forward source=<decisionSource>`. `session.permissions_changed`
    (`previousMode`, `mode`) is `permission mode: <old> -> <new>` and
    `session.mode_changed` (`previousMode`, `newMode`) `agent mode: <old>
    -> <new>`; both update the tracked mode, so the next request does not
    repeat the change. The Copilot Desktop app's bundled CLI (1.0.95-3,
    real install, Linux, October 2026; issue 147) writes
    `session.permissions_changed` with `previousAllowAllPermissions`,
    `allowAllPermissions`, `previousAllowAllPermissionMode` and
    `allowAllPermissionMode` instead, which the 1.0.98 schema does not
    name: with no `mode` and no `previousMode` the row is `permission mode:
    allow-all <previousAllowAllPermissionMode or -> ->
    <allowAllPermissionMode or ->` and the tracked mode becomes
    `allow-all <allowAllPermissionMode>`.
  - Model (`session.model_change`: `newModel`, `previousModel`, `cause`,
    `source`, `reasoningEffort`): `model: <id>` at the first and
    `model: <old> -> <new>` after, kept when the two are equal (a change
    the user typed), followed by ` cause=`, ` source=` and ` effort=` for
    the keys present. `session.auto_mode_resolved` (`chosenModel`,
    `routingMethod`) is `model: <old> -> <id> (auto, <routingMethod>)`.
    The `model` column is the event's own `model`, else the tracked one.
  - `session.info` (`infoType`, `message`, `url`, `tip`), the CLI's
    categorised timeline notice (the `infoType` `model` lines of a `/model`
    switch among them): `session.info <infoType>: <message>`, followed by
    ` url=` and ` tip=` for the keys present, with the tracked model.
  - `model.message` (`modelCall.model`, `message.content`): `utility model
    <model>: <content>` with that model in the `model` column; these are
    the runtime's calls to a utility model (the session-name generator,
    the task-analytics classifier) and never change the session model.
    The other `model.*` events are bookkeeping and give no row.
  - `session.compaction_complete` (`summaryContent`): `compaction summary:
    <text>`. `abort`, `session.error`, `session.warning` (`reason`,
    `message`): `<type>: <text>`. `session.task_complete`,
    `system.notification`, `session.schedule_created`, `skill.invoked`,
    `subagent.*`, `session.handoff`: `<type>: <main text>`,
    else compact JSON of `data`. `session.shutdown` (`shutdownType`,
    `errorReason`, `codeChanges.filesModified`): `session end: <type>
    <reason> files modified: <files>`.
  - `hook.start` (`hookInvocationId`, `hookType`, `input`,
    `parentToolCallId`) and `hook.end` (`hookInvocationId`, `hookType`,
    `output`, `success`, `error`, `parentToolCallId`), the schema's
    `HookStartData` and `HookEndData`, observed in the Copilot Desktop
    app's sessions (issue 147): `hook <hookType> start: <compact JSON of
    input, or {} when absent>` and `hook <hookType> end:
    success=<true|false> output=<compact JSON of output, or {}>`, then
    ` error=<compact JSON>` when `error` is present; `-` for a missing
    `hookType` or a `success` that is not a boolean. `tool_use_id` is
    `parentToolCallId` when present, `tool_name` empty; the payload is
    never shortened.
  - `assistant.turn_*`, `session.usage_*`, the other `model.*` events and
    unknown types are skipped. Each bad line is its own `system` row at
    the end, carrying the line in full (issue 136, `error_rows` in
    `base.py`), and the other lines are still read.
* `<home>/session-state/<id>/workspace.yaml` (`id`, `cwd`, `name`,
  `user_named`, `fork_count`, `summary_count`, `created_at`,
  `client_name`, `mc_session_id`, `mc_task_id`, `mc_last_event_id`,
  `remote_steerable`), read with a flat `key: value` reader since only
  top-level scalars are used: `session name: <name>` and `session
  metadata: user_named=<b> forks=<n> compactions=<n> client=<client_name>`
  at `created_at` (`client=` with an empty value when the key is absent).
  `client_name` is `github/cli` for a CLI session and `github/autopilot`
  for one the Copilot Desktop app ran through its bundled CLI (issue
  147). Its `cwd` is the project path of the log's rows before a
  `session.start` and of the snapshot rows. When the session directory
  holds no `events.jsonl` beside the file and `cwd` is set, the session
  is one the app pre-created and never prompted (Copilot Desktop's pool
  and probe sessions), and one more row follows the metadata row with
  the same columns: `scratch directory: <cwd> (working directory of a
  session the app pre-created and never prompted: no events.jsonl)`, so
  inventory.json lists the `cwd` under `scratch_directories` (issue
  149). When the file has a
  non-empty `mc_session_id`, the session is synced to the user's GitHub
  account (issue 151); the keys can be present as `null` on a session
  that is not, as in the research document's sample. One more row then, `session synced: remote session
  <mc_session_id> task <mc_task_id> last event <mc_last_event_id>
  remote_steerable=<remote_steerable> (from workspace.yaml, file mtime)`,
  at the file's modification time, `-` for a key absent or empty. The
  four keys were seen on Windows 1.0.98 (standalone, added at a resume)
  and in every Copilot Desktop session (Linux 1.1.29, Windows 1.1.30);
  the CLI deletes the file with the session, so the row is the only
  local trace of the sync while the session exists.
* Secondary sources, which repeat the log's events and are read always,
  so a session whose log was rewound, cut or deleted is still recovered
  (`dedup.py`):
  - `<home>/session-store.db` (SQLite in WAL mode; the "chronicle" store):
    `sessions` (`id`, `cwd`, `branch`, `summary`, `created_at`) gives
    `session name: <summary>` at `created_at`, the text the
    `workspace.yaml` row has, so the copy drops when the two agree;
    `turns` (`session_id`, `turn_index`, `user_message`,
    `assistant_response`, `timestamp`) a `user` and an `assistant` row per
    turn; `session_files` (`file_path`, `tool_name`, `first_seen_at`)
    `file changed: <path> tool=<tool>`; `session_refs` (`ref_type`,
    `ref_value`, `created_at`) `reference: <type> <value>`; `checkpoints`
    (`checkpoint_number`, `title`, `overview`, `history`, `work_done`,
    `technical_details`, `important_files`, `next_steps`, `created_at`)
    `checkpoint <n>: <title>` with each other non-null column on a line
    of its own; `forge_trajectory_events` (`tool_call_id`, `command`,
    `output`, `exit_code`, `created_at`) a `tool_use` and a `tool_result`
    joined on the call id. `forge_trajectory_events` was empty on both
    real installs and its `event_type` values are unknown, so it is not
    observed on any real install, bundle-derived: every column is read as
    possibly NULL and `event_type` is not used. `search_index`,
    `assistant_usage_events`, `forge_skill_proposals` and
    `dynamic_context_items` are not read (concatenated copies, accounting,
    no session). `project_path` and `git_branch` come from `sessions`.
    The runtime writes a turn as it ends, so `turns.timestamp` is the end
    of the turn (4 to 293 seconds after the prompt observed, and a turn
    with many tools runs longer): `secondary_tolerance()` is one hour, as
    for Letta's turn-end transcript. The pairing is confined to one
    session and one text, so the wide window only pairs a row with an
    identical event of the same session.
  - `<home>/session-state/<id>/rewind-file-snapshots/index.json`
    (`snapshots[]`: `eventId`, `timestamp`, `userMessage`, `fileCount`,
    `linesAdded`, `linesRemoved`, `files.<hex>.path`): a `user` row of the
    prompt at `timestamp` and `rewind snapshot: <n> files +<a> -<r>:
    <path>, ...`. The snapshot's time was not measured against the
    prompt's on a real install, so it gets the same one-hour window.
  - `<home>/command-history-state.json` (`commandHistory[]`, newest
    first): a `user` row per prompt with an empty `timestamp_utc`,
    `session_id` and `project_path`, since the file records none;
    `source_line` the 1-based index.
* `<home>/permissions-config.json` (`locations.<path>.tool_approvals[]`,
  `.allowed_directories[]`) and `<home>/settings.json` (`allowedUrls[]`,
  `deniedUrls[]`; JSON with comments, stripped before parsing): one
  `permission setting: <key>=<value> (from <file>, file mtime)` row per
  entry, at the file's modification time, `project_path` the location,
  empty `session_id`. A file that is not a JSON object is one `system`
  row.
* `<home>/sidebar-sessions-state/<sha256 of cwd>.json` (`cwd`,
  `sessionIds[]`): no rows; its `cwd` is the project path of database and
  snapshot rows whose session names none.
* `<home>/logs/process-<epoch ms>-<pid>.log`: `signed in: <host> as
  <login>` from the `Signed in to <host> as <login>.` line, at the line's
  time; `session_id` from `Workspace initialized: <uuid>` when the file
  names exactly one session.

Not read: `rewind-file-snapshots/tracking.json`, `checkpoints/index.md`,
`session.db` (the agent's own todo tables), the legacy flat
`session-state/<id>.jsonl` (its shape is not in the bundle),
`config.json`, `open-sessions-state.json`.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

from ..inputs import Artifact
from ..model import SCRATCH_PREFIX, Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    iter_jsonl,
    setting_value,
    track_change,
)

HOME = r"(?:\.copilot|\.local/state/\.copilot|\.config/\.copilot)"
SESSION_DIR = HOME + r"/session-state/([0-9a-f-]{36})/"
EVENTS_RX = re.compile("^" + SESSION_DIR + r"events\.jsonl$")
WORKSPACE_RX = re.compile("^" + SESSION_DIR + r"workspace\.yaml$")
SNAPSHOTS_RX = re.compile("^" + SESSION_DIR + r"rewind-file-snapshots/index\.json$")
STORE_RX = re.compile("^(" + HOME + r")/session-store\.db$")
HISTORY_RX = re.compile("^" + HOME + r"/command-history-state\.json$")
PERMISSIONS_RX = re.compile("^" + HOME + r"/permissions-config\.json$")
SETTINGS_RX = re.compile("^" + HOME + r"/settings\.json$")
SIDEBAR_RX = re.compile("^" + HOME + r"/sidebar-sessions-state/[0-9a-f]{64}\.json$")
LOG_RX = re.compile("^" + HOME + r"/logs/process-\d+-\d+\.log$")
HOME_PREFIX_RX = re.compile("^(" + HOME + ")/")

# `turns.timestamp` and the snapshot time are stamped at the end of a turn
# (or at a time not measured against the prompt's), so the prompt and the
# reply of the log are up to a turn's length earlier.
TURN_TOLERANCE_SECONDS = 3600.0

ARG_KEYS = ("command", "url", "query", "path", "input")
NOTE_TYPES = (
    "session.task_complete",
    "system.notification",
    "session.schedule_created",
    "skill.invoked",
    "session.handoff",
)
NOTE_PREFIXES = ("subagent.",)
# The Copilot Desktop app's form of `session.permissions_changed` (issue 147).
ALLOW_ALL_KEYS = (
    "previousAllowAllPermissions",
    "allowAllPermissions",
    "previousAllowAllPermissionMode",
    "allowAllPermissionMode",
)
NOTE_KEYS = ("summary", "content", "prompt", "message", "reason", "name", "agentName")
# `permission.completed` result keys appended to the decision row, in order.
DECISION_KEYS = (
    ("locationKey", "location"),
    ("approval", "approval"),
    ("directories", "directories"),
    ("feedback", "feedback"),
    ("rules", "rules"),
    ("reason", "reason"),
    ("path", "path"),
    ("message", "message"),
)
CHECKPOINT_COLUMNS = (
    "overview",
    "history",
    "work_done",
    "technical_details",
    "important_files",
    "next_steps",
)
SIGNED_IN_RX = re.compile(r"Signed in to (\S+) as (.+?)\.?\s*$")
WORKSPACE_LINE_RX = re.compile(r"Workspace initialized: ([0-9a-f-]{36})")
LOG_TIME_RX = re.compile(r"^(\d{4}-\d{2}-\d{2}T\S+Z)\s")


def _dict(v) -> dict:
    return v if isinstance(v, dict) else {}


def _str(v) -> str:
    if v is None:
        return ""
    return v if isinstance(v, str) else compact_json(v)


def args_text(args) -> str:
    """A `tool_use` text: a string argument (a `custom` grammar tool such as
    `apply_patch`) as it is, else the first of `ARG_KEYS`, else compact
    JSON."""
    if isinstance(args, str):
        return args
    if isinstance(args, dict):
        for k in ARG_KEYS:
            v = args.get(k)
            if v not in (None, ""):
                return _str(v)
        return compact_json(args) if args else ""
    return _str(args)


def result_text(data: dict) -> str:
    """A `tool.execution_complete` text. `detailedContent` is the complete
    result and `content` the concise one sent to the model, except that a
    successful skill invocation puts the concise text in `detailedContent`,
    so the longer of the two is taken, `detailedContent` on a tie."""
    res = _dict(data.get("result"))
    detailed = _str(res.get("detailedContent"))
    concise = _str(res.get("content"))
    text = concise if len(concise) > len(detailed) else detailed
    code = _dict(data.get("shellExecution")).get("exitCode")
    if code not in (None, 0, "0") and not isinstance(code, bool):
        text = "[exit %s] %s" % (code, text)
    if data.get("success") is False:
        msg = _str(_dict(data.get("error")).get("message"))
        if msg:
            text = text + "\n" + msg if text else msg
    return text


def request_target(req: dict) -> str:
    """What a `permissionRequest` asks about: the command, URL, file or
    path, or `<server>/<tool>` for an MCP tool."""
    for k in ("fullCommandText", "url", "fileName", "path"):
        v = req.get(k)
        if v not in (None, ""):
            return _str(v)
    server, tool = _str(req.get("serverName")), _str(req.get("toolName"))
    if server or tool:
        return "%s/%s" % (server, tool) if server else tool
    return ""


def decision_text(data: dict) -> str:
    """`permission decision: <kind> source=<decisionSource or -> ...`."""
    res = _dict(data.get("result"))
    text = "permission decision: %s source=%s" % (
        _str(res.get("kind")) or "-",
        _str(data.get("decisionSource")) or "-",
    )
    for key, label in DECISION_KEYS:
        if res.get(key) not in (None, "", [], {}):
            text += " %s=%s" % (label, setting_value(res.get(key)))
    return text


def strip_jsonc(text: str) -> str:
    """JSON with `//` and `/* */` comments and trailing commas made plain
    JSON. Strings are copied untouched, so a URL's `//` survives."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i : j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def read_flat_yaml(path: Path) -> dict[str, str | None]:
    """The top-level `key: value` scalars of a YAML file, `null` and `~` as
    None, quoted values unquoted. `workspace.yaml` holds only scalars; a
    nested or multi-line value is skipped, since none is read."""
    out: dict[str, str | None] = {}
    try:
        lines = path.read_bytes().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for line in lines:
        if not line or line[0] in " \t#-" or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value in ("", "null", "~"):
            out[key.strip()] = None
        elif value.startswith('"'):
            try:
                out[key.strip()] = str(json.loads(value))
            except ValueError:
                out[key.strip()] = value.strip('"')
        elif value.startswith("'") and value.endswith("'") and len(value) > 1:
            out[key.strip()] = value[1:-1].replace("''", "'")
        else:
            out[key.strip()] = value
    return out


def _read_json(path: Path):
    try:
        return json.loads(path.read_bytes().decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


class CopilotCliParser(Parser):
    agent = "copilot-cli"
    name = "copilot-cli"
    has_secondary = True
    records_sync = True

    def __init__(self) -> None:
        self._sidebar_cache: dict[Path, dict[str, str]] = {}

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.match(rel)
            for rx in (
                EVENTS_RX,
                WORKSPACE_RX,
                SNAPSHOTS_RX,
                STORE_RX,
                HISTORY_RX,
                PERMISSIONS_RX,
                SETTINGS_RX,
                SIDEBAR_RX,
                LOG_RX,
            )
        )

    def secondary(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return bool(STORE_RX.match(rel) or HISTORY_RX.match(rel) or SNAPSHOTS_RX.match(rel))

    def secondary_tolerance(self, artifact: Artifact) -> float:
        if STORE_RX.match(artifact.rel) or SNAPSHOTS_RX.match(artifact.rel):
            return TURN_TOLERANCE_SECONDS
        return super().secondary_tolerance(artifact)

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        m = EVENTS_RX.match(rel)
        if m:
            yield from self._parse_events(artifact, m.group(1), opts)
        elif m := WORKSPACE_RX.match(rel):
            yield from self._parse_workspace(artifact, m.group(1))
        elif m := SNAPSHOTS_RX.match(rel):
            yield from self._parse_snapshots(artifact, m.group(1))
        elif STORE_RX.match(rel):
            yield from self._parse_store(artifact)
        elif HISTORY_RX.match(rel):
            yield from self._parse_history(artifact)
        elif PERMISSIONS_RX.match(rel):
            yield from self._parse_permissions(artifact)
        elif SETTINGS_RX.match(rel):
            yield from self._parse_settings(artifact)
        elif LOG_RX.match(rel):
            yield from self._parse_log(artifact)
        # sidebar-sessions-state files give no rows of their own; they are
        # read as a join by `_sidebar`.

    # -- helpers ------------------------------------------------------------

    def _row(self, artifact: Artifact, line: int, turn: str, text: str, **cols) -> Row:
        r = self.base_row(artifact)
        r.source_line = line
        r.turn_type = turn
        r.text = compact(text)
        for k, v in cols.items():
            setattr(r, k, v or "")
        return r

    def _problem(self, artifact: Artifact, text: str, ts: str = "") -> Row:
        return self._row(artifact, 1, "system", text, timestamp_utc=ts)

    def _sidebar(self, artifact: Artifact) -> dict[str, str]:
        """Session id to cwd from the `sidebar-sessions-state/*.json` files of
        the Copilot home `artifact` is in; {} when there are none. Symlinks
        are not read."""
        m = HOME_PREFIX_RX.match(artifact.rel)
        if not m:
            return {}
        d = artifact.home.disk_path / m.group(1) / "sidebar-sessions-state"
        if d not in self._sidebar_cache:
            found: dict[str, str] = {}
            if d.is_dir() and not d.is_symlink():
                for f in sorted(d.glob("*.json")):
                    if f.is_symlink() or not f.is_file():
                        continue
                    doc = _dict(_read_json(f))
                    cwd = _str(doc.get("cwd"))
                    ids = doc.get("sessionIds")
                    if cwd and isinstance(ids, list):
                        for sid in ids:
                            found.setdefault(_str(sid), cwd)
            self._sidebar_cache[d] = found
        return self._sidebar_cache[d]

    @staticmethod
    def _workspace_cwd(session_dir: Path) -> str:
        f = session_dir / "workspace.yaml"
        if f.is_symlink() or not f.is_file():
            return ""
        return read_flat_yaml(f).get("cwd") or ""

    def _fallback_project(self, artifact: Artifact, session_dir: Path, sid: str) -> str:
        return self._workspace_cwd(session_dir) or self._sidebar(artifact).get(sid, "")

    # -- events.jsonl -------------------------------------------------------

    def _parse_events(self, artifact: Artifact, sid: str, opts: Options) -> Iterator[Row]:
        errors: list = []
        project = self._fallback_project(artifact, artifact.disk_path.parent, sid)
        state = {"project": project, "branch": "", "model": ""}
        names: dict[str, str] = {}
        requested: set[str] = set()
        models: dict = {}
        modes: dict = {}
        perm = {"mode": "", "agent": ""}

        for n, rec in iter_jsonl(artifact.disk_path, errors):
            etype = _str(rec.get("type"))
            data = _dict(rec.get("data"))
            ts = to_utc(rec.get("timestamp"))

            def row(
                turn: str,
                text: str,
                tool_name: str = "",
                tool_use_id: str = "",
                model: str = "",
                n=n,
                ts=ts,
            ) -> Row:
                return self._row(
                    artifact,
                    n,
                    turn,
                    text,
                    timestamp_utc=ts,
                    session_id=sid,
                    project_path=state["project"],
                    git_branch=state["branch"],
                    model=model or state["model"],
                    tool_name=tool_name,
                    tool_use_id=tool_use_id,
                )

            if etype in ("session.start", "session.resume", "session.context_changed"):
                ctx = _dict(data.get("context")) if "context" in data else data
                if ctx.get("cwd"):
                    state["project"] = _str(ctx.get("cwd"))
                if "branch" in ctx or etype == "session.context_changed":
                    state["branch"] = _str(ctx.get("branch"))
                if etype == "session.start":
                    yield row(
                        "system",
                        "session start: copilot %s producer=%s cwd=%s"
                        % (
                            _str(data.get("copilotVersion")) or "-",
                            _str(data.get("producer")) or "-",
                            _str(ctx.get("cwd")) or "-",
                        ),
                    )
                elif etype == "session.resume":
                    yield row("system", "session resumed")
            elif etype == "system.message":
                label = "developer message" if data.get("role") == "developer" else "system prompt"
                yield row("system", "%s: %s" % (label, _str(data.get("content"))))
            elif etype == "user.message":
                yield self._user_row(row, rec, data)
            elif etype == "assistant.message":
                yield from self._assistant_rows(row, data, opts, names, requested)
            elif etype == "assistant.reasoning":
                if opts.include_thinking and data.get("content"):
                    yield row("thinking", _str(data.get("content")))
            elif etype in ("tool.execution_start", "tool.user_requested"):
                cid = _str(data.get("toolCallId"))
                name = _str(data.get("toolName"))
                if cid and name:
                    names.setdefault(cid, name)
                if etype == "tool.execution_start" and cid in requested:
                    continue
                requested.add(cid)
                text = args_text(data.get("arguments"))
                if etype == "tool.user_requested":
                    text = "user requested: " + text
                yield row("tool_use", text, name, cid, _str(data.get("model")))
            elif etype == "tool.execution_complete":
                cid = _str(data.get("toolCallId"))
                yield row(
                    "tool_result",
                    result_text(data),
                    names.get(cid, ""),
                    cid,
                    _str(data.get("model")),
                )
            elif etype.startswith("permission.") or etype in (
                "session.permissions_changed",
                "session.mode_changed",
            ):
                yield from self._permission_rows(row, etype, data, names, modes, perm, sid)
            elif etype in ("session.model_change", "session.auto_mode_resolved"):
                yield from self._model_rows(row, etype, data, models, state, sid)
            elif etype == "session.info":
                yield row("system", self._info_text(data))
            elif etype == "model.message":
                call_model = _str(_dict(data.get("modelCall")).get("model"))
                content = _str(_dict(data.get("message")).get("content"))
                yield row(
                    "system", "utility model %s: %s" % (call_model, content), model=call_model
                )
            elif etype == "session.compaction_complete":
                yield row("system", "compaction summary: %s" % _str(data.get("summaryContent")))
            elif etype in ("abort", "session.error", "session.warning"):
                text = _str(data.get("reason")) or _str(data.get("message")) or compact_json(data)
                yield row("system", "%s: %s" % (etype, text))
            elif etype in ("hook.start", "hook.end"):
                yield row(
                    "system",
                    self._hook_text(etype, data),
                    tool_use_id=_str(data.get("parentToolCallId")),
                )
            elif etype in NOTE_TYPES or etype.startswith(NOTE_PREFIXES):
                main = next((_str(data[k]) for k in NOTE_KEYS if data.get(k) not in (None, "")), "")
                yield row("system", "%s: %s" % (etype, main or compact_json(data)))
            elif etype == "session.shutdown":
                yield row("system", self._shutdown_text(data))
            # assistant.turn_*, session.usage_*, the other model.* events and
            # unknown types are bookkeeping: no row.

        for r in error_rows(self, artifact, errors, sid, state["project"]):
            r.git_branch = state["branch"]
            yield r

    @staticmethod
    def _user_row(row: Callable[..., Row], rec: dict, data: dict) -> Row:
        """`user` for a typed prompt, else `system` with what sent it."""
        content = _str(data.get("content"))
        source = _str(data.get("source"))
        if data.get("isAutopilotContinuation"):
            label = "auto-continuation"
        elif rec.get("agentId"):
            label = "subagent task"
        elif source and source != "user":
            label = source
        else:
            return row("user", content)
        return row("system", "%s: %s" % (label, content))

    @staticmethod
    def _assistant_rows(
        row: Callable[..., Row], data: dict, opts: Options, names: dict, requested: set
    ) -> Iterator[Row]:
        model = _str(data.get("model"))
        content = _str(data.get("content"))
        if content.strip():
            yield row("assistant", content, model=model)
        if opts.include_thinking:
            thought = _str(data.get("reasoningText"))
            if not thought:
                parts = []
                for block in _dict(data.get("reasoningBlocks")).get("blocks") or []:
                    for s in _dict(block).get("summary") or []:
                        t = _dict(s).get("text")
                        if isinstance(t, str) and t:
                            parts.append(t)
                thought = "\n\n".join(parts)
            if thought:
                yield row("thinking", thought, model=model)
        for req in data.get("toolRequests") or []:
            req = _dict(req)
            cid = _str(req.get("toolCallId"))
            name = _str(req.get("name"))
            if cid:
                names[cid] = name
                requested.add(cid)
            yield row("tool_use", args_text(req.get("arguments")), name, cid, model)

    @staticmethod
    def _permission_rows(
        row: Callable[..., Row],
        etype: str,
        data: dict,
        names: dict,
        modes: dict,
        perm: dict,
        sid: str,
    ) -> Iterator[Row]:
        """Request, decision and mode rows. The tracked mode is
        `<permissionMode> agent=<agentMode>`; the two change events update
        their half of it."""
        if etype == "permission.requested":
            req = _dict(data.get("permissionRequest"))
            cid = _str(req.get("toolCallId"))
            text = "permission request: %s" % (_str(req.get("kind")) or "-")
            target = request_target(req)
            if target:
                text += " " + target
            if req.get("intention") not in (None, ""):
                text += " intention=%s" % _str(req.get("intention"))
            yield row("system", text, names.get(cid, ""), cid)
            if data.get("permissionMode"):
                perm["mode"] = _str(data.get("permissionMode"))
            if data.get("agentMode"):
                perm["agent"] = _str(data.get("agentMode"))
            if perm["mode"]:
                value = perm["mode"] + (" agent=%s" % perm["agent"] if perm["agent"] else "")
                mode_text = track_change("permission mode", modes, sid, value)
                if mode_text:
                    yield row("system", mode_text, names.get(cid, ""), cid)
        elif etype == "permission.completed":
            cid = _str(data.get("toolCallId"))
            yield row("system", decision_text(data), names.get(cid, ""), cid)
        elif etype == "permission.carriedForward":
            cid = _str(data.get("toolCallId"))
            yield row(
                "system",
                "permission decision: carried-forward source=%s"
                % (_str(data.get("decisionSource")) or "-"),
                names.get(cid, ""),
                cid,
            )
        elif etype == "session.permissions_changed":
            allow_all = (
                "mode" not in data
                and "previousMode" not in data
                and any(k in data for k in ALLOW_ALL_KEYS)
            )
            if allow_all:
                old = _str(data.get("previousAllowAllPermissionMode")) or "-"
                new = _str(data.get("allowAllPermissionMode"))
                yield row("system", "permission mode: allow-all %s -> %s" % (old, new or "-"))
                perm["mode"] = "allow-all %s" % new if new else perm["mode"]
            else:
                old, new = _str(data.get("previousMode")) or "-", _str(data.get("mode")) or "-"
                yield row("system", "permission mode: %s -> %s" % (old, new))
                perm["mode"] = _str(data.get("mode"))
            if perm["mode"]:
                modes[sid] = perm["mode"] + (" agent=%s" % perm["agent"] if perm["agent"] else "")
        elif etype == "session.mode_changed":
            old, new = _str(data.get("previousMode")) or "-", _str(data.get("newMode")) or "-"
            yield row("system", "agent mode: %s -> %s" % (old, new))
            perm["agent"] = _str(data.get("newMode"))
            if perm["mode"]:
                modes[sid] = perm["mode"] + (" agent=%s" % perm["agent"] if perm["agent"] else "")

    @staticmethod
    def _model_rows(
        row: Callable[..., Row], etype: str, data: dict, models: dict, state: dict, sid: str
    ) -> Iterator[Row]:
        """`model: <id>` at the first and `model: <old> -> <new>` after,
        kept when unchanged, since a change event is a decision even when it
        resolves to the same model."""
        if etype == "session.auto_mode_resolved":
            new = _str(data.get("chosenModel"))
            suffix = " (auto, %s)" % (_str(data.get("routingMethod")) or "-")
        else:
            new = _str(data.get("newModel"))
            suffix = ""
            for key, label in (("cause", "cause"), ("source", "source")):
                if data.get(key) not in (None, ""):
                    suffix += " %s=%s" % (label, _str(data.get(key)))
            if data.get("reasoningEffort") not in (None, ""):
                suffix += " effort=%s" % _str(data.get("reasoningEffort"))
        if not new:
            return
        old = models.get(sid) or _str(data.get("previousModel"))
        models[sid] = new
        state["model"] = new
        text = "model: %s -> %s" % (old, new) if old else "model: %s" % new
        yield row("system", text + suffix, model=new)

    @staticmethod
    def _hook_text(etype: str, data: dict) -> str:
        """`hook <hookType> start: <input>` or `hook <hookType> end:
        success=<b> output=<output>` and ` error=<error>` when present; each
        payload as compact JSON in full, `{}` when absent."""
        hook = _str(data.get("hookType")) or "-"
        if etype == "hook.start":
            payload = data.get("input")
            return "hook %s start: %s" % (hook, "{}" if payload is None else compact_json(payload))
        success = data.get("success")
        output = data.get("output")
        text = "hook %s end: success=%s output=%s" % (
            hook,
            setting_value(success) if isinstance(success, bool) else "-",
            "{}" if output is None else compact_json(output),
        )
        if data.get("error") is not None:
            text += " error=%s" % compact_json(data.get("error"))
        return text

    @staticmethod
    def _info_text(data: dict) -> str:
        """`session.info <infoType>: <message>`, then ` url=` and ` tip=`
        for the keys present."""
        text = "session.info %s: %s" % (_str(data.get("infoType")), _str(data.get("message")))
        for key in ("url", "tip"):
            if data.get(key) not in (None, ""):
                text += " %s=%s" % (key, _str(data.get(key)))
        return text

    @staticmethod
    def _shutdown_text(data: dict) -> str:
        files = _dict(data.get("codeChanges")).get("filesModified")
        if isinstance(files, list):
            files_text = ", ".join(_str(f) for f in files) or "none"
        else:
            files_text = _str(files) or "none"
        parts = ["session end:", _str(data.get("shutdownType")) or "-"]
        if data.get("errorReason") not in (None, ""):
            parts.append(_str(data.get("errorReason")))
        parts.append("files modified: %s" % files_text)
        return " ".join(parts)

    # -- workspace.yaml -----------------------------------------------------

    def _parse_workspace(self, artifact: Artifact, sid: str) -> Iterator[Row]:
        meta = read_flat_yaml(artifact.disk_path)
        sid = meta.get("id") or sid
        cols = {
            "timestamp_utc": to_utc(meta.get("created_at")),
            "session_id": sid,
            "project_path": meta.get("cwd") or self._sidebar(artifact).get(sid, ""),
        }
        if meta.get("name"):
            yield self._row(artifact, 1, "system", "session name: %s" % meta.get("name"), **cols)
        yield self._row(
            artifact,
            1,
            "system",
            "session metadata: user_named=%s forks=%s compactions=%s client=%s"
            % (
                meta.get("user_named") or "-",
                meta.get("fork_count") or "-",
                meta.get("summary_count") or "-",
                meta.get("client_name") or "",
            ),
            **cols,
        )
        # A session the app pre-created and never prompted (Copilot
        # Desktop's pool and probe sessions) has no events.jsonl; its cwd
        # is the agent's, not a project (issue 149).
        if meta.get("cwd") and not os.path.lexists(artifact.disk_path.parent / "events.jsonl"):
            yield self._row(
                artifact,
                1,
                "system",
                "%s %s (working directory of a session the app pre-created and never"
                " prompted: no events.jsonl)" % (SCRATCH_PREFIX, meta.get("cwd")),
                **cols,
            )
        if meta.get("mc_session_id"):
            yield self._row(
                artifact,
                1,
                "system",
                "session synced: remote session %s task %s last event %s remote_steerable=%s"
                " (from workspace.yaml, file mtime)"
                % tuple(
                    meta.get(k) or "-"
                    for k in ("mc_session_id", "mc_task_id", "mc_last_event_id", "remote_steerable")
                ),
                **{**cols, "timestamp_utc": file_mtime(artifact)},
            )

    # -- rewind-file-snapshots/index.json -----------------------------------

    def _parse_snapshots(self, artifact: Artifact, sid: str) -> Iterator[Row]:
        doc = _read_json(artifact.disk_path)
        if not isinstance(doc, dict):
            yield self._problem(artifact, "parser: rewind snapshot index is not a JSON object")
            return
        session_dir = artifact.disk_path.parent.parent
        project = self._fallback_project(artifact, session_dir, sid)
        for i, snap in enumerate(doc.get("snapshots") or [], 1):
            snap = _dict(snap)
            cols = {
                "timestamp_utc": to_utc(snap.get("timestamp")),
                "session_id": sid,
                "project_path": project,
            }
            if snap.get("userMessage") not in (None, ""):
                yield self._row(artifact, i, "user", _str(snap.get("userMessage")), **cols)
            paths = [
                _str(_dict(f).get("path"))
                for f in _dict(snap.get("files")).values()
                if _dict(f).get("path")
            ]
            text = "rewind snapshot: %s files +%s -%s" % (
                _str(snap.get("fileCount")) or "0",
                _str(snap.get("linesAdded")) or "0",
                _str(snap.get("linesRemoved")) or "0",
            )
            if paths:
                text += ": " + ", ".join(paths)
            yield self._row(artifact, i, "system", text, **cols)

    # -- session-store.db ---------------------------------------------------

    def _parse_store(self, artifact: Artifact) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield self._problem(artifact, "parser: not a SQLite database")
            return
        try:
            with open_copy(artifact.disk_path) as con:
                rows = list(self._store_rows(artifact, con))
        except sqlite3.DatabaseError as e:
            yield self._problem(artifact, "parser: SQLite error: %s" % e)
            return
        yield from rows

    @staticmethod
    def _select(con: sqlite3.Connection, table: str, order: str) -> list[dict]:
        sql = "select rowid as _rowid, * from %s order by %s" % (table, order)
        return [dict(r) for r in con.execute(sql)]

    def _store_rows(self, artifact: Artifact, con: sqlite3.Connection) -> Iterator[Row]:
        tables = table_names(con)
        sidebar = self._sidebar(artifact)
        sessions: dict[str, dict] = {}
        if "sessions" in tables:
            for s in self._select(con, "sessions", "created_at, rowid"):
                sessions[_str(s.get("id"))] = s

        def stamp(sid: str, line, turn: str, text: str, ts, **cols) -> Row:
            s = sessions.get(sid, {})
            return self._row(
                artifact,
                int(line or 0),
                turn,
                text,
                timestamp_utc=to_utc(ts),
                session_id=sid,
                project_path=_str(s.get("cwd")) or sidebar.get(sid, ""),
                git_branch=_str(s.get("branch")),
                **cols,
            )

        for sid, s in sessions.items():
            if s.get("summary") not in (None, ""):
                yield stamp(
                    sid,
                    s["_rowid"],
                    "system",
                    "session name: %s" % s["summary"],
                    s.get("created_at"),
                )
        if "turns" in tables:
            for t in self._select(con, "turns", "session_id, turn_index, rowid"):
                sid = _str(t.get("session_id"))
                for col, turn in (("user_message", "user"), ("assistant_response", "assistant")):
                    if t.get(col) not in (None, ""):
                        yield stamp(sid, t["_rowid"], turn, _str(t[col]), t.get("timestamp"))
        if "session_files" in tables:
            for f in self._select(con, "session_files", "first_seen_at, rowid"):
                text = "file changed: %s tool=%s" % (
                    _str(f.get("file_path")),
                    _str(f.get("tool_name")) or "-",
                )
                yield stamp(
                    _str(f.get("session_id")), f["_rowid"], "system", text, f.get("first_seen_at")
                )
        if "session_refs" in tables:
            for ref in self._select(con, "session_refs", "created_at, rowid"):
                text = "reference: %s %s" % (_str(ref.get("ref_type")), _str(ref.get("ref_value")))
                yield stamp(
                    _str(ref.get("session_id")),
                    ref["_rowid"],
                    "system",
                    text,
                    ref.get("created_at"),
                )
        if "checkpoints" in tables:
            for c in self._select(con, "checkpoints", "created_at, rowid"):
                lines = [
                    "checkpoint %s: %s" % (_str(c.get("checkpoint_number")), _str(c.get("title")))
                ]
                for col in CHECKPOINT_COLUMNS:
                    if c.get(col) not in (None, ""):
                        lines.append("%s: %s" % (col, _str(c[col])))
                yield stamp(
                    _str(c.get("session_id")),
                    c["_rowid"],
                    "system",
                    "\n".join(lines),
                    c.get("created_at"),
                )
        if "forge_trajectory_events" in tables:
            yield from self._forge_rows(con, stamp)

    def _forge_rows(self, con: sqlite3.Connection, stamp: Callable[..., Row]) -> Iterator[Row]:
        """`forge_trajectory_events`: not observed on any real install,
        bundle-derived. A row with a `command` is a `tool_use`, one with an
        `output` or an `exit_code` a `tool_result`, both joined on
        `tool_call_id`; every column may be NULL."""
        for e in self._select(con, "forge_trajectory_events", "created_at, rowid"):
            sid = _str(e.get("session_id"))
            cid = _str(e.get("tool_call_id"))
            if e.get("command") not in (None, ""):
                yield stamp(
                    sid,
                    e["_rowid"],
                    "tool_use",
                    _str(e.get("command")),
                    e.get("created_at"),
                    tool_use_id=cid,
                )
            code = e.get("exit_code")
            if e.get("output") is not None or code is not None:
                text = _str(e.get("output"))
                if code not in (None, 0, "0"):
                    text = "[exit %s] %s" % (code, text)
                yield stamp(
                    sid, e["_rowid"], "tool_result", text, e.get("created_at"), tool_use_id=cid
                )

    # -- command-history-state.json -----------------------------------------

    def _parse_history(self, artifact: Artifact) -> Iterator[Row]:
        doc = _read_json(artifact.disk_path)
        if not isinstance(doc, dict):
            yield self._problem(artifact, "parser: command history is not a JSON object")
            return
        for i, entry in enumerate(doc.get("commandHistory") or [], 1):
            if isinstance(entry, str) and entry.strip():
                yield self._row(artifact, i, "user", entry)

    # -- standing permissions -----------------------------------------------

    def _setting(self, artifact: Artifact, ts: str, key: str, value, project: str = "") -> Row:
        text = "permission setting: %s=%s (from %s, file mtime)" % (
            key,
            setting_value(value),
            artifact.rel,
        )
        return self._row(artifact, 1, "system", text, timestamp_utc=ts, project_path=project)

    def _parse_permissions(self, artifact: Artifact) -> Iterator[Row]:
        ts = file_mtime(artifact)
        doc = _read_json(artifact.disk_path)
        if not isinstance(doc, dict):
            yield self._problem(
                artifact, "parser: permissions-config.json is not a JSON object", ts
            )
            return
        for path, entry in _dict(doc.get("locations")).items():
            entry = _dict(entry)
            for key in ("tool_approvals", "allowed_directories"):
                items = entry.get(key)
                if not isinstance(items, list):
                    continue
                for item in items:
                    yield self._setting(artifact, ts, "locations.%s.%s" % (path, key), item, path)

    def _parse_settings(self, artifact: Artifact) -> Iterator[Row]:
        ts = file_mtime(artifact)
        try:
            raw = artifact.disk_path.read_bytes().decode("utf-8", errors="replace")
            doc = json.loads(strip_jsonc(raw))
        except (OSError, ValueError):
            doc = None
        if not isinstance(doc, dict):
            yield self._problem(artifact, "parser: settings.json is not a JSON object", ts)
            return
        for key in ("allowedUrls", "deniedUrls"):
            items = doc.get(key)
            if isinstance(items, list):
                for item in items:
                    yield self._setting(artifact, ts, key, item)

    # -- logs/process-*.log -------------------------------------------------

    def _parse_log(self, artifact: Artifact) -> Iterator[Row]:
        try:
            lines = artifact.disk_path.read_bytes().decode("utf-8", errors="replace").splitlines()
        except OSError:
            return
        sessions = {m.group(1) for line in lines for m in [WORKSPACE_LINE_RX.search(line)] if m}
        sid = next(iter(sessions)) if len(sessions) == 1 else ""
        for n, line in enumerate(lines, 1):
            m = SIGNED_IN_RX.search(line)
            if not m:
                continue
            t = LOG_TIME_RX.match(line)
            yield self._row(
                artifact,
                n,
                "system",
                "signed in: %s as %s" % (m.group(1), m.group(2)),
                timestamp_utc=to_utc(t.group(1)) if t else "",
                session_id=sid,
            )
