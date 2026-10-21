"""OpenCode sessions.

Validated against source, sst/opencode at 907b3bc for 1.x and
anomalyco/opencode at cb07c55 (CLI 2.0.32, the `dev` branch) for 2.0 (see
`research/opencode.md`), with a synthetic fixture; no real install
was used, and the 2.0 layout is source-derived only. The same storage model is used by Kilo Code's CLI, which is an
OpenCode fork, so `KiloCodeParser` subclasses this one with its own paths.

Files, relative to the home directory (XDG paths on every OS):

* `.local/share/opencode/opencode.db`, or `opencode-<channel>.db`, with
  `-wal` and `-shm` sidecars (WAL mode, so the sidecar holds the newest
  rows). Opened through `sqlite_util.open_copy`. Tables read:
  - `session_v2` (OpenCode 2.0) and `session(id, project_id, parent_id,
    slug, directory, title, version, agent, time_created)`, the same
    columns; `session_v2` adds `fork_session_id`. `directory` is the cwd.
    A database created by 2.0 has only `session_v2`; one upgraded to 2.0
    keeps the 1.x `session`, `message` and `part` tables beside it, and a
    session deleted in 2.0 is left only there.
  - `project(id, worktree)`: repository root; `/` for the `global` project.
  - `message(id, session_id, time_created, data)`: `data` JSON is the V1
    message without `id` and `sessionID`: `role`, `time.created`, `agent`,
    user `model.{providerID, modelID}`, assistant `providerID`, `modelID`,
    `path.cwd`, `error.{name, data.message}`.
  - `part(id, message_id, session_id, time_created, data)`: `data` JSON has
    a `type` discriminator: `text` (`text`, `synthetic`, `time.start`),
    `reasoning` (`text`, `time.start`), `tool` (`callID`, `tool`,
    `state.{status, input, output, error, title, time.{start, end}}`, the
    call and its result in one part), `step-start`, `step-finish` (`reason`,
    `cost`, `tokens`), `subtask` (`agent`, `description`, `prompt`),
    `compaction`, `file` (`filename`, `url`), `agent` (`name`), `retry`
    (`attempt`, `error`), `patch` (`files`), `snapshot`.
  - `session_message(id, session_id, type, seq, time_created, data)`: the
    V2 transcript, `data` without `id` and `type`. In a 1.x database it is
    a projection that was wiped once by a migration, so it is read only
    for sessions that have no V1 `message` rows. In a database with
    `session_v2` it is the transcript of every session, the upgrade having
    copied each 1.x session into it, so the 1.x `message` and `part` rows
    are read only for a session it does not hold, and those rows other
    than `system` are marked `recovered` "yes" (the parser's own pairing,
    exact on the session id, since both copies are in one file). `data`
    for `user` (`text`), `synthetic` and `system` (`text`), `shell` (1.x
    `callID`, `command`, `output`; 2.0 `shellID`, `command`, `status`,
    `exit`, `output.output`, `time.completed`), `compaction` (`reason`,
    `status`, `summary`, `error`), `model-switched` (`model.{id,
    providerID}`), `agent-switched` (`agent`), `assistant` (`agent`,
    `model.{id or modelID, providerID}`, `content[]` of `text`,
    `reasoning` and `tool` items with `id`, `name`, `state.{status, input,
    content[], error.{type, message}}`, `time.{created, completed}`) and,
    since 2.0, `location-switched` (`location.{directory, workspaceID}`,
    `previous.location.directory`, `subpath`), `skill` (`name`, `text`)
    and `idle` (`outcome`, `error`).
  - `session_share(session_id, id, secret, url, time_created)`: one row
    per session published to OpenCode's share service. `secret`, the
    credential for the public copy, is never read.
  - `event(rowid, aggregate_id, seq, type, data)`: only `type`
    `session.updated.1`, whose `data` is `{sessionID, info}` with the
    session's `info.share.url` while it is shared and `info.time.updated`
    (ms). The table was emptied once by the reset migration.
  The `credential` and `account` tables are not read.
* `.local/share/opencode/opencode-next.db`: a database of a pre-release
  2.0 build (`project`, `session`, `session_message`) that 2.0 imports into
  `opencode.db` and leaves in place. Read as above and returned by
  `secondary()`, so `dedup.deduplicate` drops what the database it was
  imported into repeats and keeps a session deleted after the import.
* Legacy JSON tree `.local/share/opencode/storage/`: `session/<projectID>/
  <sessionID>.json` (`id`, `projectID`, `parentID`, `directory`, `title`,
  `version`, `time.created`), `message/<sessionID>/<messageID>.json` (the V1
  message with `id` and `sessionID` inline), `part/<messageID>/<partID>.json`
  and `project/<projectID>.json` (`worktree`).
* Older per-project tree `.local/share/opencode/project/<slug>/storage/
  session/`: `info/<sessionID>.json`, `message/<sessionID>/<messageID>.json`,
  `part/<sessionID>/<messageID>/<partID>.json`. The project root comes from
  the assistant message's `path.root`.

Rows. A session header (database row or session JSON file) becomes one
`system` row. A user message becomes one `user` row with its non-synthetic
text parts joined; every other part becomes its own row: assistant `text` is
`assistant`, `reasoning` is `thinking` (with `--include-thinking`), `tool` is
a `tool_use` row plus a `tool_result` row once the status is `completed` or
`error`, `step-finish`, `subtask`, `compaction`, `file`, `agent`, `retry`,
`patch` and synthetic text are `system`; `step-start` and `snapshot` carry
nothing but a snapshot hash and are skipped. A message-level `error` is a
`system` row. The model column is `providerID/modelID`. A `session_message`
record is one row per kind: `user` is `user`; assistant content as for V1
parts; `shell` a `tool_use` row (tool `shell`, id `callID` or `shellID`)
and, once it has output or has ended, a `tool_result` row whose text
starts `[timeout]`, `[killed]` or `[exit <code>]` when it did not exit 0;
`location-switched` is `location switched: <old> -> <new>` (the
`project_path` stays the session's `directory`), `skill` is `skill <name>:
<text>`, `idle` is `idle: <outcome>`, all `system`. A session that a 2.0
database holds only in the 1.x `session` table gets `(only in the 1.x
session table)` at the end of its session-start row.

Model and mode rows, per session: the first message that names a model
(a user message's `model` or an assistant's `providerID`/`modelID`; a V2
assistant's `model`) is preceded by a `system` row `model: <modelID>
provider=<providerID>`, and every later message or V2 `model-switched`
record whose model differs by `model: <old> -> <new> provider=<providerID>`.
The message's `agent` (V1 user and assistant, V2 assistant, V2
`agent-switched`) is tracked the same way as `permission mode:
agent=<name>` and `permission mode: agent=<old> -> agent=<new>`: an
OpenCode agent is a mode with its own permission ruleset. Both rows take
the message's timestamp and `source_line` and sit before its other rows.
In the JSON trees, where a file holds one message, the starting value is
the message file before it in the same session directory. The session's
`permission` rules are read (see below); the project's `sandboxes` are
not. Timestamps come from the
part's `time.start` (tool results: `state.time.end`), else the part row's
`time_created`, else the message's `time.created`; user text parts carry no
time of their own and inherit the message's. `project_path` is the
session's `directory` (the cwd, as in the other parsers), else the project
`worktree` unless it is `/`, else the message's `path.cwd`. No git branch is
recorded. `source_line` is the SQLite `rowid` of the record for databases
and 1 for the one-record JSON files.

Sync rows (issue 153), `system`, after the session-start rows, so
`records_sync` is set: one per `session_share` row, at its `time_created`,
`session synced: share <id> url <url> (from <database> session_share,
time_created)`. A session with no `session_share` row whose
`session.updated.1` events carry `info.share.url` (shared and then
unshared, which deletes the share row but not the events) gets
`session synced: share url <url> (from <database> event
session.updated.1, info.time.updated)` at the first such event's
`info.time.updated`, and `session unshared (from <database> event
session.updated.1, info.time.updated)` at the first later event without
`share`; a later re-share is not reported again. `<database>` is the
file name (`opencode.db`, `opencode-<channel>.db`, `kilo.db`). An absent
value prints `-`. The legacy JSON trees have no share record, so their
sessions have no sync row. Kilo Code's fork writes the same tables (see
`kilo_code.py`).

Permission, deletion and scratch rows (issue 194), source-derived; not
observed on any real install (anomalyco/opencode at cb07c55; the 1.x texts
at 907b3bc). All `system`:

* A refused tool call: after its `tool_result` row, on its `tool_name` and
  `tool_use_id` and at its time, `permission decision: rejected` (1.x
  `state.error` "The user rejected permission to use this specific tool
  call.", or 2.0 `error.type` `aborted` with "The user declined this tool
  call"), `permission decision: rejected with feedback` (1.x "... with the
  following feedback: <text>"), `permission decision: denied by rule` (1.x
  "The user has specified a rule which prevents you ...") or `permission
  decision: rejected (permission.rejected)` (2.0 `error.type`
  `permission.rejected`, a deny rule or a rejection with feedback, which the
  message does not tell apart). An approval leaves no record.
* After the session-start and sync rows: per session with `time_archived`
  set, `session archived (from <database> <table>, time_archived)` at that
  time; per rule of the session's `permission` column (a JSON array of 2.0
  `{action, resource, effect}` or 1.x `{permission, pattern, action}`),
  `permission setting: session <permission> <pattern>=<effect> (from
  <database> <table>.permission, time_updated)` at `time_updated`, a value
  that is not a JSON array being `parser: unparseable record <rowid>
  (<table>.permission: not a JSON array): <value>`; per row of the 2.0
  `worktree(project_id, directory, strategy, time_created)` table, else of
  the deprecated `project_directory` with `type` `git_worktree`, `scratch
  directory: <directory> (git worktree of <project worktree> strategy=
  <strategy>) (from <database> <table>, time_created)` with `project_path`
  the directory and no session; per row of the `permission(id, project_id,
  action, resource, time_created)` table of saved "always" grants,
  `permission setting: <action> <resource>=allow (from <database>
  permission, time_created)` with `project_path` the project's worktree.

Terminal UI state (issue 194), source-derived; not observed on any real
install, under `.local/state/opencode` (Kilo Code: `.local/state/kilo`):

* `prompt-history.jsonl`, secondary (`secondary()`): the last 50 prompts,
  2.0 `{text, files, agents, skills, pasted, mode?}`, 1.x and Kilo Code
  `{input, parts, mode?}`, no session, project or time. One row per line
  with an empty `timestamp_utc`: a `user` row, or for `mode` `shell` a
  `tool_use` row with tool `shell` and no id, which pairs on text with the
  transcript's command.
* `prompt-stash.jsonl`: prompts set aside unsent, 2.0 `{prompt: {text},
  timestamp}`, 1.x and Kilo Code `{input, parts, timestamp}` (epoch ms);
  one `system` row per line at `timestamp`, `prompt stashed (unsent):
  <text> (from <file>, timestamp)`.
* `session.json` (OpenCode only), secondary: `{pinned: [<session id>]}`;
  one `system` row per id, `session pinned: <id> (from <file> pinned, file
  mtime)`, with that `session_id`, at the file's modification time. The id
  outlives a deleted session. A file that is not a JSON object is one
  `parser:` row.

Bad lines in both JSONL files are `parser: unparseable line` rows
(`error_rows`).

Bad records (issue 139): each `message`, `part`, `session_message` or
`event` row whose `data` is not a JSON object is its own `system` row
`parser: unparseable record <rowid> (<table>.data: <reason>): <data>`,
the stored value in full, with the session id and project of its row, an
empty timestamp and `source_line` the rowid; a part row's follows its
message's rows, the others end the database's rows. A part file of the
JSON trees that does not decode is `parser: unparseable part <partID>
(<reason>): <file text>`, `source_file` the part file, after its message's
rows. A message or session file that does not decode is one `parser:`
row for the whole file.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Generator, Iterator
from pathlib import Path

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    iter_jsonl,
    track_change,
)

# The session-start row of a session that a 2.0 database holds only in the 1.x
# `session` table: deleted in 2.0, which leaves the 1.x rows behind.
LEGACY_NOTE = "(only in the 1.x session table)"

# Which tool input field best identifies the action, in order of preference.
TOOL_KEYS = (
    "command",
    "filePath",
    "file_path",
    "pattern",
    "path",
    "url",
    "query",
    "description",
    "prompt",
)


def tool_summary(value) -> str:
    """The most identifying argument of a tool input, else the input as JSON."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in TOOL_KEYS:
            v = value.get(key)
            if isinstance(v, str) and v:
                if key == "pattern" and isinstance(value.get("path"), str) and value.get("path"):
                    return "%s | %s" % (v, value["path"])
                return v
    if value in (None, "", {}):
        return ""
    return compact_json(value)


def model_name(provider, model) -> str:
    provider = provider if isinstance(provider, str) else ""
    model = model if isinstance(model, str) else ""
    if provider and model:
        return "%s/%s" % (provider, model)
    return model or provider


def message_ref(msg: dict) -> tuple[object, object]:
    """(providerID, model id) of a V1 message: the assistant's own
    `providerID`/`modelID`, else the user message's `model` object."""
    if msg.get("role") == "assistant":
        return msg.get("providerID"), msg.get("modelID")
    m = msg.get("model")
    if isinstance(m, dict):
        return m.get("providerID"), m.get("modelID") or m.get("id")
    return None, None


def message_model(msg: dict) -> str:
    return model_name(*message_ref(msg))


def model_row_text(seen: dict, key, provider, model_id) -> str:
    """The `model:` row text for a model reference, through `track_change`:
    `model: <id> provider=<provider>` for the first model of a session and
    `model: <old id> -> <new id> provider=<provider>` when the id or the
    provider changes; "" when it is unchanged or names no model id."""
    provider = provider if isinstance(provider, str) else ""
    model_id = model_id if isinstance(model_id, str) else ""
    if not model_id:
        return ""
    old = seen.get(key)
    if not track_change("model", seen, key, "%s\n%s" % (provider, model_id)):
        return ""
    text = "model: %s -> %s" % (old.split("\n", 1)[1], model_id) if old else "model: " + model_id
    return text + (" provider=" + provider if provider else "")


def agent_row_text(seen: dict, key, agent) -> str:
    """The `permission mode: agent=<name>` row text when a session's agent is
    new or changed. An OpenCode agent (`build`, `plan`, a custom one) is a
    mode with its own permission set, so it is tracked as the mode."""
    if not isinstance(agent, str) or not agent:
        return ""
    return track_change("permission mode", seen, key, "agent=" + agent)


def _d(value) -> dict:
    return value if isinstance(value, dict) else {}


def _loads(value) -> dict | None:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if not isinstance(value, str):
        return None
    try:
        v = json.loads(value)
    except ValueError:
        return None
    return v if isinstance(v, dict) else None


def _decode(value) -> tuple[dict | None, str, str]:
    """(record, reason, raw text) of a stored JSON value: the record when it
    decodes to an object, else None with the reason and the value as text
    (bytes decoded UTF-8 with `errors="replace"`), for an error row that
    carries it in full (issue 139)."""
    if value is None:
        return None, "no data", ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    elif isinstance(value, str):
        text = value
    else:
        return None, "not JSON text", str(value)
    try:
        v = json.loads(text)
    except ValueError as e:
        return None, str(e), text
    if not isinstance(v, dict):
        return None, "not a JSON object", text
    return v, "", text


def _read_part(path: Path) -> tuple[dict | None, str, str]:
    """`_decode` of a part file's bytes; an unreadable file gives the
    reason and no text."""
    try:
        with open(path, "rb") as fh:
            return _decode(fh.read())
    except OSError as e:
        return None, "unreadable: %s" % (e.strerror or e), ""


def _read_json(path: Path) -> dict | None:
    try:
        with open(path, "rb") as fh:
            return _loads(fh.read())
    except OSError:
        return None


def _join(*parts) -> str:
    return " ".join(str(p) for p in parts if p not in (None, ""))


def _error_text(err) -> str:
    if isinstance(err, str):
        return err
    e = _d(err)
    data = _d(e.get("data"))
    msg = data.get("message") or e.get("message") or ""
    return _join(e.get("name") or e.get("type") or "", msg) or (compact_json(err) if err else "")


# The refusal texts a tool's error carries (research/opencode.md, Permission
# records; research/kilo-code.md, Permission rows). 1.x and Kilo Code store
# the error's message as the tool part's `state.error` string; 2.0 stores
# `{type, message}` on the tool item.
V1_REJECTED = "The user rejected permission to use this specific tool call."
V1_FEEDBACK = (
    "The user rejected permission to use this specific tool call with the following feedback: "
)
V1_RULE = "The user has specified a rule which prevents you from using this specific tool call."
V2_DECLINED = "The user declined this tool call"


def decision_text(err) -> str:
    """The `permission decision:` row text for a tool error that records a
    refusal, else "". The 2.0 `permission.rejected` type covers both a deny
    rule and a rejection with feedback, which its message does not tell
    apart, so it keeps the agent's own term."""
    if isinstance(err, str):
        etype, msg = "", err
    elif isinstance(err, dict):
        etype, msg = err.get("type"), err.get("message")
        etype = etype if isinstance(etype, str) else ""
        msg = msg if isinstance(msg, str) else ""
    else:
        return ""
    if etype == "permission.rejected":
        return "permission decision: rejected (permission.rejected)"
    if etype in ("", "aborted") and msg == V2_DECLINED:
        return "permission decision: rejected"
    if msg.startswith(V1_FEEDBACK):
        return "permission decision: rejected with feedback"
    if msg.startswith(V1_REJECTED):
        return "permission decision: rejected"
    if msg.startswith(V1_RULE):
        return "permission decision: denied by rule"
    return ""


def session_rules(value) -> list[tuple[str, str, str]] | None:
    """(permission, pattern, effect) per rule of a session's `permission`
    column: a JSON array of 2.0 `{action, resource, effect}` or 1.x and
    Kilo Code `{permission, pattern, action}` objects. None when the value
    is not a JSON array; entries that are neither shape are skipped."""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    try:
        rules = json.loads(value) if isinstance(value, str) else None
    except ValueError:
        return None
    if not isinstance(rules, list):
        return None
    out = []
    for rule in rules:
        rule = _d(rule)
        if "effect" in rule:
            keys = ("action", "resource", "effect")
        elif "permission" in rule:
            keys = ("permission", "pattern", "action")
        else:
            continue
        perm, pattern, effect = (
            str(rule[k]) if rule.get(k) not in (None, "") else "-" for k in keys
        )
        out.append((perm, pattern, effect))
    return out


class _Ctx:
    """Session-level values shared by every row of a session."""

    def __init__(self, session_id: str = "", project_path: str = ""):
        self.session_id = session_id
        self.project_path = project_path
        # The model and agent last seen in the session, for `track_change`.
        self.models: dict = {}
        self.modes: dict = {}


class OpenCodeParser(Parser):
    agent = "opencode"
    name = "opencode"
    records_sync = True
    # The pre-release 2.0 database (`opencode-next.db`) that 2.0 imports and
    # leaves in place is secondary to the database it was imported into.
    has_secondary = True
    next_db = "opencode-next.db"
    data_dir = ".local/share/opencode"
    db_prefixes: tuple[str, ...] = ("opencode",)
    # The terminal UI's state directory: `prompt-history.jsonl` (secondary),
    # `prompt-stash.jsonl` and, for OpenCode, `session.json` (secondary).
    state_dir = ".local/state/opencode"
    pinned_sessions = True

    def __init__(self) -> None:
        dd = re.escape(self.data_dir)
        sd = re.escape(self.state_dir)
        self.history_rx = re.compile(r"^%s/prompt-history\.jsonl$" % sd)
        self.stash_rx = re.compile(r"^%s/prompt-stash\.jsonl$" % sd)
        self.pinned_rx = re.compile(r"^%s/session\.json$" % sd if self.pinned_sessions else r"(?!)")
        prefixes = "|".join(re.escape(p) for p in self.db_prefixes)
        self.db_rx = re.compile(r"^%s/(?:%s)(?:-[^/]+)?\.db$" % (dd, prefixes))
        self.session_rx = re.compile(r"^%s/storage/session/([^/]+)/([^/]+)\.json$" % dd)
        self.message_rx = re.compile(r"^%s/storage/message/([^/]+)/([^/]+)\.json$" % dd)
        self.old_session_rx = re.compile(
            r"^%s/project/[^/]+/storage/session/info/([^/]+)\.json$" % dd
        )
        self.old_message_rx = re.compile(
            r"^%s/project/[^/]+/storage/session/message/([^/]+)/([^/]+)\.json$" % dd
        )

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.match(rel)
            for rx in (
                self.db_rx,
                self.session_rx,
                self.message_rx,
                self.old_session_rx,
                self.old_message_rx,
                self.history_rx,
                self.stash_rx,
                self.pinned_rx,
            )
        )

    def secondary(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        if self.history_rx.match(rel) or self.pinned_rx.match(rel):
            return True
        return bool(self.db_rx.match(rel)) and self.db_label(artifact) == self.next_db

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        if self.history_rx.match(rel):
            yield from self._parse_history(artifact)
        elif self.stash_rx.match(rel):
            yield from self._parse_stash(artifact)
        elif self.pinned_rx.match(rel):
            yield from self._parse_pinned(artifact)
        elif self.db_rx.match(rel):
            yield from self._parse_db(artifact, opts)
        elif self.session_rx.match(rel) or self.old_session_rx.match(rel):
            yield from self._parse_session_file(artifact, opts)
        elif self.message_rx.match(rel):
            yield from self._parse_message_file(artifact, opts, old=False)
        elif self.old_message_rx.match(rel):
            yield from self._parse_message_file(artifact, opts, old=True)

    # -- shared row builders --------------------------------------------------------
    def _row(
        self, artifact: Artifact, ctx: _Ctx, source_file: str, line: int, ts: str, model: str = ""
    ) -> Row:
        row = self.base_row(artifact)
        if source_file:
            row.source_file = source_file
        row.source_line = line
        row.session_id = ctx.session_id
        row.project_path = ctx.project_path
        row.timestamp_utc = ts
        row.model = model
        return row

    def _session_row(
        self,
        artifact: Artifact,
        ctx: _Ctx,
        s: dict,
        created,
        line: int,
        opts: Options,
        source_file: str = "",
        note: str = "",
    ) -> Row:
        row = self._row(artifact, ctx, source_file, line, to_utc(created))
        row.turn_type = "system"
        row.text = compact(
            _join(
                "session start:",
                s.get("title") or "",
                "slug=%s" % s["slug"] if s.get("slug") else "",
                "version=%s" % s["version"] if s.get("version") else "",
                "agent=%s" % s["agent"] if s.get("agent") else "",
                "parent=%s" % (s.get("parent_id") or s.get("parentID"))
                if (s.get("parent_id") or s.get("parentID"))
                else "",
                "fork=%s" % s["fork_session_id"] if s.get("fork_session_id") else "",
                "directory=%s" % s["directory"] if s.get("directory") else "",
                note,
            ),
        )
        return row

    def _message_rows(
        self,
        artifact: Artifact,
        ctx: _Ctx,
        msg: dict,
        msg_src: tuple[str, int, object],
        parts: list[tuple[dict, str, int, object]],
        opts: Options,
        errors: list,
    ) -> Iterator[Row]:
        """Rows for one V1 message and its parts. `msg_src` and each part
        entry carry (source_file, source_line, fallback time). A part whose
        data could not be decoded is in `errors` instead, as (line, message,
        raw, source_file), and becomes its own `parser:` row after the
        message's rows; `source_file` "" means the artifact."""
        role = msg.get("role")
        model = message_model(msg)
        msg_file, msg_line, msg_time = msg_src
        msg_ts = to_utc(_d(msg.get("time")).get("created")) or to_utc(msg_time)
        if not ctx.project_path:
            ctx.project_path = str(_d(msg.get("path")).get("cwd") or "")
        for text in (
            model_row_text(ctx.models, ctx.session_id, *message_ref(msg)),
            agent_row_text(ctx.modes, ctx.session_id, msg.get("agent")),
        ):
            if text:
                row = self._row(artifact, ctx, msg_file, msg_line, msg_ts, model)
                row.turn_type = "system"
                row.text = text
                yield row
        user_text: list[str] = []
        first_user: tuple[str, int, int] | None = None
        out: list[Row] = []
        for data, pfile, pline, ptime in parts:
            ptype = data.get("type")
            pts = to_utc(_d(data.get("time")).get("start")) or to_utc(ptime) or msg_ts

            def mk(turn: str, text, ts: str = "") -> Row:
                row = self._row(artifact, ctx, pfile, pline, ts or pts, model)
                row.turn_type = turn
                row.text = compact(text)
                out.append(row)
                return row

            if ptype == "text":
                text = data.get("text") or ""
                if data.get("synthetic") or data.get("ignored"):
                    mk("system", _join("synthetic:" if data.get("synthetic") else "ignored:", text))
                elif role == "user":
                    if text:
                        user_text.append(text)
                        if first_user is None:
                            first_user = (pfile, pline, len(out))
                elif text:
                    mk("assistant", text)
            elif ptype == "reasoning":
                if opts.include_thinking and data.get("text"):
                    mk("thinking", data.get("text"))
            elif ptype == "tool":
                self._tool_rows(mk, data)
            elif ptype == "step-finish":
                tokens = _d(data.get("tokens"))
                mk(
                    "system",
                    _join(
                        "step-finish",
                        "reason=%s" % data["reason"] if data.get("reason") else "",
                        "cost=%s" % data["cost"] if data.get("cost") is not None else "",
                        "tokens_in=%s" % tokens["input"] if tokens.get("input") is not None else "",
                        "tokens_out=%s" % tokens["output"]
                        if tokens.get("output") is not None
                        else "",
                    ),
                )
            elif ptype == "subtask":
                mk(
                    "system",
                    _join(
                        "subtask",
                        "agent=%s" % data["agent"] if data.get("agent") else "",
                        (data.get("description") or "") + ":",
                        data.get("prompt") or "",
                    ),
                )
            elif ptype == "compaction":
                mk("system", _join("compaction", "auto" if data.get("auto") else ""))
            elif ptype == "file":
                mk("system", _join("file:", data.get("filename") or "", data.get("url") or ""))
            elif ptype == "agent":
                mk("system", _join("agent:", data.get("name") or ""))
            elif ptype == "retry":
                mk(
                    "system",
                    _join(
                        "retry",
                        "attempt=%s" % data["attempt"] if data.get("attempt") else "",
                        _error_text(data.get("error")),
                    ),
                )
            elif ptype == "patch":
                files = data.get("files")
                mk(
                    "system",
                    _join(
                        "patch:", " ".join(str(f) for f in files) if isinstance(files, list) else ""
                    ),
                )
            elif ptype in ("step-start", "snapshot"):
                continue
            else:
                mk("system", _join("%s:" % (ptype or "part"), compact_json(data)))
        if user_text and first_user:
            pfile, pline, at = first_user
            row = self._row(artifact, ctx, pfile, pline, msg_ts, model)
            row.turn_type = "user"
            row.text = compact("\n".join(user_text))
            out.insert(at, row)
        yield from out
        if msg.get("error"):
            row = self._row(
                artifact,
                ctx,
                msg_file,
                msg_line,
                to_utc(_d(msg.get("time")).get("completed")) or msg_ts,
                model,
            )
            row.turn_type = "system"
            row.text = compact("error: " + _error_text(msg.get("error")))
            yield row
        bad_rows = error_rows(self, artifact, errors, ctx.session_id, ctx.project_path)
        for entry, row in zip(errors, bad_rows, strict=True):
            if entry[3]:
                row.source_file = entry[3]
            yield row

    @staticmethod
    def _tool_rows(mk, data: dict) -> None:
        """Append a tool_use row, and a tool_result row once finished, via `mk`."""
        state = _d(data.get("state"))
        times = _d(state.get("time"))
        name = str(data.get("tool") or "")
        call_id = str(data.get("callID") or "")
        use = mk(
            "tool_use",
            tool_summary(state.get("input")) or state.get("title") or "",
            to_utc(times.get("start")),
        )
        use.tool_name, use.tool_use_id = name, call_id
        status = state.get("status")
        if status in ("completed", "error"):
            if status == "error":
                text = "[error] " + _error_text(state.get("error"))
            else:
                out = state.get("output")
                text = out if isinstance(out, str) else compact_json(out)
            res = mk("tool_result", text, to_utc(times.get("end")) or to_utc(times.get("start")))
            res.tool_name, res.tool_use_id = name, call_id
            decision = decision_text(state.get("error")) if status == "error" else ""
            if decision:
                row = mk("system", decision, res.timestamp_utc)
                row.tool_name, row.tool_use_id = name, call_id

    # -- SQLite ---------------------------------------------------------------------
    def _parse_db(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            return
        rows: list[Row] = []
        try:
            with open_copy(artifact.disk_path) as con:
                for row in self._db_rows(con, artifact, opts):
                    rows.append(row)
        except sqlite3.DatabaseError as e:
            row = self.base_row(artifact)
            row.turn_type = "system"
            row.text = "parser: database could not be read: %s" % e
            rows.append(row)
        yield from rows

    def _db_rows(self, con: sqlite3.Connection, artifact: Artifact, opts: Options) -> Iterator[Row]:
        tables = table_names(con)
        projects: dict[object, dict] = {}  # keyed by the raw id column value
        if "project" in tables:
            for r in con.execute("select * from project"):
                projects[r["id"]] = dict(r)
        # OpenCode 2.0 keeps its sessions in `session_v2` and leaves the 1.x
        # `session`, `message` and `part` tables behind after the upgrade.
        v2 = "session_v2" in tables
        sessions: dict[str, tuple[int, dict, str]] = {}  # id -> (rowid, row, table)
        for table in ("session_v2", "session"):
            if table in tables:
                for r in con.execute(
                    "select rowid as _rowid, * from %s order by time_created, id" % table
                ):
                    sessions.setdefault(str(r["id"]), (r["_rowid"], dict(r), table))
        ctxs: dict[str, _Ctx] = {}

        def ctx_for(sid: str) -> _Ctx:
            c = ctxs.get(sid)
            if c is None:
                s = sessions.get(sid, (0, {}, ""))[1]
                path = s.get("directory") or ""
                if not path:
                    wt = projects.get(s.get("project_id"), {}).get("worktree") or ""
                    path = wt if wt != "/" else ""
                c = ctxs[sid] = _Ctx(sid, path)
            return c

        for sid, (rowid, s, table) in sessions.items():
            note = LEGACY_NOTE if v2 and table == "session" else ""
            yield self._session_row(
                artifact, ctx_for(sid), s, s.get("time_created"), rowid, opts, note=note
            )

        # (rowid, message, raw, session id) per record whose data does not decode.
        errors: list[tuple[int, str, str, str]] = []
        yield from self._share_rows(con, tables, artifact, ctx_for, errors)
        yield from self._state_rows(con, tables, artifact, sessions, projects, ctx_for, errors)
        if v2:
            # 2.0: `session_message` is the transcript. The 1.x rows repeat a
            # migrated session and are read only for a session it does not
            # hold (one deleted in 2.0, which leaves the 1.x rows), as
            # recovered rows.
            covered = self._session_message_ids(con, tables)
            yield from self._v2_messages(con, tables, artifact, ctx_for, set(), errors, opts)
            yield from self._v1_messages(
                con, tables, artifact, ctx_for, covered, errors, opts, recovered=True
            )
        else:
            # 1.x: `message` and `part` are the transcript; the V2 projection
            # was wiped once by a migration, so it is read only for a session
            # with no V1 rows.
            covered = yield from self._v1_messages(
                con, tables, artifact, ctx_for, set(), errors, opts
            )
            yield from self._v2_messages(con, tables, artifact, ctx_for, covered, errors, opts)
        for entry, row in zip(errors, error_rows(self, artifact, errors), strict=True):
            sid = entry[3]
            row.session_id = sid
            row.project_path = ctx_for(sid).project_path if sid else ""
            yield row

    @staticmethod
    def _session_message_ids(con: sqlite3.Connection, tables: set) -> set[str]:
        """The ids of the sessions that have a `session_message` row."""
        if "session_message" not in tables:
            return set()
        return {
            str(r[0] or "") for r in con.execute("select distinct session_id from session_message")
        }

    def _v1_messages(
        self,
        con: sqlite3.Connection,
        tables: set,
        artifact: Artifact,
        ctx_for,
        skip: set[str],
        errors: list,
        opts: Options,
        recovered: bool = False,
    ) -> Generator[Row, None, set[str]]:
        """Rows of the V1 `message` and `part` tables for every session not
        in `skip`. An undecodable `message` row is appended to `errors` as
        (rowid, message, raw, session id); an undecodable `part` row becomes
        a `parser:` row after its message's rows. With `recovered`, every
        row other than `system` is marked `recovered` "yes". Returns the ids
        of the sessions that have a `message` row."""
        covered: set[str] = set()
        if "message" not in tables:
            return covered
        has_parts = "part" in tables
        for m in con.execute(
            "select rowid as _rowid, id, session_id, time_created, data from message "
            "order by session_id, time_created, id"
        ).fetchall():
            sid = str(m["session_id"] or "")
            covered.add(sid)
            if sid in skip:
                continue
            msg, reason, raw = _decode(m["data"])
            if msg is None:
                label = "unparseable record %d (message.data: %s)" % (m["_rowid"], reason)
                errors.append((m["_rowid"], label, raw, sid))
                continue
            msg.setdefault("id", m["id"])
            parts = []
            part_errors: list[tuple[int, str, str, str]] = []
            if has_parts:
                for p in con.execute(
                    "select rowid as _rowid, time_created, data from part "
                    "where message_id = ? order by id",
                    (m["id"],),
                ):
                    data, reason, raw = _decode(p["data"])
                    if data is None:
                        label = "unparseable record %d (part.data: %s)" % (p["_rowid"], reason)
                        part_errors.append((p["_rowid"], label, raw, ""))
                    else:
                        parts.append((data, "", p["_rowid"], p["time_created"]))
            msg_src = ("", m["_rowid"], m["time_created"])
            for row in self._message_rows(
                artifact, ctx_for(sid), msg, msg_src, parts, opts, part_errors
            ):
                if recovered and row.turn_type != "system":
                    row.recovered = "yes"
                yield row
        return covered

    def _v2_messages(
        self,
        con: sqlite3.Connection,
        tables: set,
        artifact: Artifact,
        ctx_for,
        skip: set[str],
        errors: list,
        opts: Options,
    ) -> Iterator[Row]:
        """Rows of `session_message` for every session not in `skip`; an
        undecodable row is appended to `errors` as (rowid, message, raw,
        session id)."""
        if "session_message" not in tables:
            return
        for m in con.execute(
            "select rowid as _rowid, session_id, type, seq, time_created, data "
            "from session_message order by session_id, seq, time_created"
        ).fetchall():
            sid = str(m["session_id"] or "")
            if sid in skip:
                continue
            data, reason, raw = _decode(m["data"])
            if data is None:
                label = "unparseable record %d (session_message.data: %s)" % (m["_rowid"], reason)
                errors.append((m["_rowid"], label, raw, sid))
                continue
            yield from self._v2_rows(
                artifact,
                ctx_for(sid),
                m["type"] or data.get("type") or "",
                data,
                m["_rowid"],
                m["time_created"],
                opts,
            )

    def _share_rows(
        self, con: sqlite3.Connection, tables: set, artifact: Artifact, ctx_for, errors: list
    ) -> Iterator[Row]:
        """The sync rows of the database: one per `session_share` row, then,
        for a session with no such row, the share URL and the unshare that
        its `session.updated.1` events record. An event row whose `data`
        does not decode is appended to `errors` as (rowid, message, raw,
        session id). `secret` is never selected."""
        db = self.db_label(artifact)
        shared: set[str] = set()
        if "session_share" in tables:
            for r in con.execute(
                "select rowid as _rowid, session_id, id, url, time_created from session_share "
                "order by time_created, session_id"
            ):
                sid = str(r["session_id"] or "")
                shared.add(sid)
                row = self._row(artifact, ctx_for(sid), "", r["_rowid"], to_utc(r["time_created"]))
                row.turn_type = "system"
                row.text = compact(
                    "session synced: share %s url %s (from %s session_share, time_created)"
                    % (r["id"] or "-", r["url"] or "-", db)
                )
                yield row
        if "event" not in tables:
            return
        state: dict[str, str] = {}  # session id -> "shared" or "unshared"
        for r in con.execute(
            "select rowid as _rowid, aggregate_id, data from event "
            "where type = 'session.updated.1' order by aggregate_id, seq"
        ):
            sid = str(r["aggregate_id"] or "")
            data, reason, raw = _decode(r["data"])
            if data is None:
                label = "unparseable record %d (event.data: %s)" % (r["_rowid"], reason)
                errors.append((r["_rowid"], label, raw, sid))
                continue
            if sid in shared or state.get(sid) == "unshared":
                continue
            info = _d(data.get("info"))
            url = _d(info.get("share")).get("url")
            ts = to_utc(_d(info.get("time")).get("updated"))
            if url and sid not in state:
                state[sid] = "shared"
                text = "session synced: share url %s" % url
            elif not url and state.get(sid) == "shared":
                state[sid] = "unshared"
                text = "session unshared"
            else:
                continue
            row = self._row(artifact, ctx_for(sid), "", r["_rowid"], ts)
            row.turn_type = "system"
            row.text = compact(
                "%s (from %s event session.updated.1, info.time.updated)" % (text, db)
            )
            yield row

    def _state_rows(
        self,
        con: sqlite3.Connection,
        tables: set,
        artifact: Artifact,
        sessions: dict,
        projects: dict,
        ctx_for,
        errors: list,
    ) -> Iterator[Row]:
        """The database's standing state, all `system` rows: per session a
        `session archived` row at `time_archived` and one `permission
        setting: session ...` row per rule of its `permission` column at
        `time_updated`; one `scratch directory:` row per worktree OpenCode
        made (`worktree`, else `project_directory` of type `git_worktree`);
        one `permission setting:` row per saved grant of the `permission`
        table. A `permission` value that is not a JSON array is appended to
        `errors` as (rowid, message, raw, session id)."""
        db = self.db_label(artifact)

        def mk(ctx: _Ctx, line: int, when, text: str, project: str | None = None) -> Row:
            row = self._row(artifact, ctx, "", line, to_utc(when))
            row.turn_type = "system"
            row.text = compact(text)
            if project is not None:
                row.project_path = project
            return row

        for sid, (rowid, s, table) in sessions.items():
            if s.get("time_archived"):
                yield mk(
                    ctx_for(sid),
                    rowid,
                    s["time_archived"],
                    "session archived (from %s %s, time_archived)" % (db, table),
                )
            if s.get("permission") in (None, ""):
                continue
            rules = session_rules(s["permission"])
            if rules is None:
                raw = s["permission"]
                raw = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
                label = "unparseable record %d (%s.permission: not a JSON array)" % (rowid, table)
                errors.append((rowid, label, raw, sid))
                continue
            for perm, pattern, effect in rules:
                yield mk(
                    ctx_for(sid),
                    rowid,
                    s.get("time_updated"),
                    "permission setting: session %s %s=%s (from %s %s.permission, time_updated)"
                    % (perm, pattern, effect, db, table),
                )

        def worktree_of(project_id) -> str:
            wt = projects.get(project_id, {}).get("worktree") or ""
            return wt if wt != "/" else ""

        seen: set[str] = set()
        for table in ("worktree", "project_directory"):
            if table not in tables:
                continue
            for r in con.execute(
                "select rowid as _rowid, * from %s order by time_created, directory" % table
            ):
                r = dict(r)
                directory = str(r.get("directory") or "")
                if not directory or directory in seen:
                    continue
                if table == "project_directory" and r.get("type") != "git_worktree":
                    continue
                seen.add(directory)
                text = "scratch directory: %s (git worktree of %s strategy=%s) (from %s %s, " % (
                    directory,
                    worktree_of(r.get("project_id")) or "-",
                    r.get("strategy") or "-",
                    db,
                    table,
                )
                yield mk(
                    _Ctx(), r["_rowid"], r.get("time_created"), text + "time_created)", directory
                )

        if "permission" in tables:
            for r in con.execute(
                "select rowid as _rowid, * from permission order by time_created, id"
            ):
                r = dict(r)
                if "action" not in r:
                    # The first migration's `permission(project_id, data)`,
                    # dropped later; its `data` shape is not in the research.
                    break
                yield mk(
                    _Ctx(),
                    r["_rowid"],
                    r.get("time_created"),
                    "permission setting: %s %s=allow (from %s permission, time_created)"
                    % (r.get("action") or "-", r.get("resource") or "-", db),
                    worktree_of(r.get("project_id")),
                )

    @staticmethod
    def db_label(artifact: Artifact) -> str:
        """The database's file name for row text (`opencode.db`, `kilo.db`,
        `opencode-<channel>.db`)."""
        return artifact.rel.rsplit("/", 1)[-1]

    def _v2_rows(
        self,
        artifact: Artifact,
        ctx: _Ctx,
        mtype: str,
        data: dict,
        line: int,
        created,
        opts: Options,
    ) -> Iterator[Row]:
        ts = to_utc(_d(data.get("time")).get("created")) or to_utc(created)
        m = _d(data.get("model"))
        model = model_name(m.get("providerID"), m.get("modelID") or m.get("id"))

        def mk(turn: str, text, when: str = "") -> Row:
            row = self._row(artifact, ctx, "", line, when or ts, model)
            row.turn_type = turn
            row.text = compact(text)
            return row

        if mtype == "model-switched":
            text = model_row_text(
                ctx.models, ctx.session_id, m.get("providerID"), m.get("id") or m.get("modelID")
            )
            if text:
                yield mk("system", text)
        elif mtype == "agent-switched":
            text = agent_row_text(ctx.modes, ctx.session_id, data.get("agent"))
            if text:
                yield mk("system", text)
        elif mtype == "user":
            yield mk("user", data.get("text") or "")
        elif mtype in ("synthetic", "system"):
            yield mk("system", _join("%s:" % mtype, data.get("text") or ""))
        elif mtype == "shell":
            yield from self._shell_rows(mk, data)
        elif mtype == "compaction":
            yield mk(
                "system",
                _join(
                    "compaction",
                    data.get("reason") or "",
                    data.get("status") or "",
                    data.get("summary") or "",
                    _error_text(data.get("error")) if data.get("error") else "",
                ),
            )
        elif mtype == "location-switched":
            loc = _d(data.get("location"))
            prev = _d(_d(data.get("previous")).get("location"))
            yield mk(
                "system",
                _join(
                    "location switched:",
                    "%s ->" % prev["directory"] if prev.get("directory") else "",
                    loc.get("directory") or "",
                    "workspace=%s" % loc["workspaceID"] if loc.get("workspaceID") else "",
                    "subpath=%s" % data["subpath"] if data.get("subpath") else "",
                ),
            )
        elif mtype == "skill":
            yield mk(
                "system", _join("skill %s:" % (data.get("name") or ""), data.get("text") or "")
            )
        elif mtype == "idle":
            yield mk(
                "system",
                _join(
                    "idle:",
                    data.get("outcome") or "",
                    _error_text(data.get("error")) if data.get("error") else "",
                ),
            )
        elif mtype == "assistant":
            for text in (
                model_row_text(
                    ctx.models, ctx.session_id, m.get("providerID"), m.get("id") or m.get("modelID")
                ),
                agent_row_text(ctx.modes, ctx.session_id, data.get("agent")),
            ):
                if text:
                    yield mk("system", text)
            for item in data.get("content") or []:
                item = _d(item)
                itype = item.get("type")
                if itype == "text" and item.get("text"):
                    yield mk("assistant", item["text"])
                elif itype == "reasoning":
                    if opts.include_thinking and item.get("text"):
                        yield mk("thinking", item["text"])
                elif itype == "tool":
                    state = _d(item.get("state"))
                    times = _d(item.get("time"))
                    name, call_id = str(item.get("name") or ""), str(item.get("id") or "")
                    use = mk(
                        "tool_use", tool_summary(state.get("input")), to_utc(times.get("created"))
                    )
                    use.tool_name, use.tool_use_id = name, call_id
                    yield use
                    status = state.get("status")
                    if status in ("completed", "error"):
                        if status == "error":
                            text = "[error] " + _error_text(state.get("error"))
                        else:
                            text = "\n".join(
                                str(c.get("text"))
                                for c in state.get("content") or []
                                if isinstance(c, dict) and c.get("text") is not None
                            )
                        res = mk(
                            "tool_result",
                            text,
                            to_utc(times.get("completed")) or to_utc(times.get("ran")),
                        )
                        res.tool_name, res.tool_use_id = name, call_id
                        yield res
                        decision = decision_text(state.get("error")) if status == "error" else ""
                        if decision:
                            row = mk("system", decision, res.timestamp_utc)
                            row.tool_name, row.tool_use_id = name, call_id
                            yield row
            if data.get("error"):
                yield mk("system", "error: " + _error_text(data.get("error")))
        elif mtype:
            yield mk(
                "system",
                _join("%s:" % mtype, compact_json({k: v for k, v in data.items() if k != "time"})),
            )

    @staticmethod
    def _shell_rows(mk, data: dict) -> Iterator[Row]:
        """A `shell` record's tool_use row and, once it has output or has
        ended, its tool_result row. 1.x: `callID`, `output` a string. 2.0:
        `shellID`, `status` (`running`, `exited`, `timeout`, `killed`),
        `exit` and `output.output`; a result that did not exit 0 starts
        `[<status>]` or `[exit <code>]`."""
        call_id = str(data.get("callID") or data.get("shellID") or "")
        times = _d(data.get("time"))
        use = mk("tool_use", data.get("command") or "")
        use.tool_name, use.tool_use_id = "shell", call_id
        yield use
        output, status, code = data.get("output"), data.get("status"), data.get("exit")
        if output is None and status in (None, "running"):
            return
        text = _d(output).get("output") if isinstance(output, dict) else output
        text = text if isinstance(text, str) else ""
        if status in ("timeout", "killed"):
            text = _join("[%s]" % status, text)
        elif code not in (None, 0):
            text = _join("[exit %s]" % code, text)
        res = mk("tool_result", text, to_utc(times.get("completed")))
        res.tool_name, res.tool_use_id = "shell", call_id
        yield res

    # -- terminal UI state ----------------------------------------------------------
    def _parse_history(self, artifact: Artifact) -> Iterator[Row]:
        """`prompt-history.jsonl`, the last 50 prompts typed into the terminal
        UI: one row per line with an empty `timestamp_utc`, `session_id` and
        `project_path`, since the line records none. A prompt is a `user`
        row; a shell command (`mode` `shell`) a `tool_use` row with tool
        `shell` and no id, which pairs on text with the transcript's command.
        2.0 writes the prompt as `text`, 1.x and Kilo Code as `input`."""
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            text = rec.get("text") if isinstance(rec.get("text"), str) else rec.get("input")
            if not isinstance(text, str) or not text.strip():
                continue
            row = self._row(artifact, _Ctx(), "", n, "")
            if rec.get("mode") == "shell":
                row.turn_type, row.tool_name = "tool_use", "shell"
            else:
                row.turn_type = "user"
            row.text = compact(text)
            yield row
        yield from error_rows(self, artifact, errors)

    def _parse_stash(self, artifact: Artifact) -> Iterator[Row]:
        """`prompt-stash.jsonl`, prompts the user set aside unsent: one
        `system` row per line at its `timestamp` (epoch ms), `prompt stashed
        (unsent): <text> (from <file>, timestamp)`. 2.0 writes `{prompt:
        {text, ...}, timestamp}`, 1.x and Kilo Code `{input, parts,
        timestamp}`."""
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            prompt = rec.get("prompt")
            text = _d(prompt).get("text") if isinstance(prompt, dict) else rec.get("input")
            if not isinstance(text, str) or not text.strip():
                continue
            row = self._row(artifact, _Ctx(), "", n, to_utc(rec.get("timestamp")))
            row.turn_type = "system"
            row.text = compact(
                "prompt stashed (unsent): %s (from %s, timestamp)" % (text.strip(), artifact.rel)
            )
            yield row
        yield from error_rows(self, artifact, errors)

    def _parse_pinned(self, artifact: Artifact) -> Iterator[Row]:
        """`session.json`, `{pinned: [<session id>...]}`: one `system` row per
        pinned id, `session pinned: <id> (from <file> pinned, file mtime)`,
        with that `session_id`, at the file's modification time. The id stays
        after the session is deleted, so a pinned session with no other row
        is a trace of a deleted one. A file that is not a JSON object is one
        `parser:` row."""
        doc = _read_json(artifact.disk_path)
        ts = file_mtime(artifact)
        if doc is None:
            row = self._row(artifact, _Ctx(), "", 1, ts)
            row.turn_type = "system"
            row.text = "parser: %s is not a JSON object" % artifact.rel
            yield row
            return
        pinned = doc.get("pinned")
        for sid in pinned if isinstance(pinned, list) else []:
            if not isinstance(sid, str) or not sid:
                continue
            row = self._row(artifact, _Ctx(sid), "", 1, ts)
            row.turn_type = "system"
            row.text = "session pinned: %s (from %s pinned, file mtime)" % (sid, artifact.rel)
            yield row

    # -- legacy JSON tree -----------------------------------------------------------
    @staticmethod
    def _orig_root(artifact: Artifact, depth: int) -> tuple[str, str, Path]:
        """(original root, separator, disk root) for the directory `depth`
        levels above the artifact file. The original path is cut by the length
        of the relative tail, which is the same whatever the separator."""
        tail = "/".join(artifact.rel.split("/")[-depth:])
        orig = artifact.original
        sep = "\\" if orig.count("\\") > orig.count("/") else "/"
        root = orig[: len(orig) - len(tail)].rstrip("/\\")
        disk = artifact.disk_path
        for _ in range(depth):
            disk = disk.parent
        return root, sep, disk

    @staticmethod
    def _children(directory: Path) -> list[Path]:
        try:
            return sorted(
                p
                for p in directory.iterdir()
                if p.suffix == ".json" and not p.is_symlink() and p.is_file()
            )
        except OSError:
            return []

    def _previous_message(self, path: Path) -> dict | None:
        siblings = self._children(path.parent)
        names = [p.name for p in siblings]
        if path.name not in names:
            return None
        i = names.index(path.name)
        return _read_json(siblings[i - 1]) if i > 0 else None

    def _session_ctx(self, root: Path, session_id: str, old: bool, msg: dict) -> tuple[_Ctx, dict]:
        s: dict | None = None
        if old:
            s = _read_json(root / "info" / (session_id + ".json"))
        else:
            sdir = root / "session"
            try:
                cands = sorted(
                    d / (session_id + ".json")
                    for d in sdir.iterdir()
                    if not d.is_symlink() and d.is_dir()
                )
            except OSError:
                cands = []
            for c in cands:
                if c.is_file() and not c.is_symlink():
                    s = _read_json(c)
                    if s is not None:
                        break
        s = s or {}
        path = s.get("directory") or ""
        if not path and not old and s.get("projectID"):
            wt = (_read_json(root / "project" / (str(s["projectID"]) + ".json")) or {}).get(
                "worktree"
            ) or ""
            path = wt if wt != "/" else ""
        if not path:
            p = _d(msg.get("path"))
            path = p.get("root") or p.get("cwd") or ""
        return _Ctx(session_id, str(path)), s

    def _parse_session_file(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        s = _read_json(artifact.disk_path)
        if s is None:
            row = self.base_row(artifact)
            row.source_line = 1
            row.session_id = artifact.disk_path.stem
            row.turn_type = "system"
            row.text = "parser: session file could not be decoded"
            yield row
            return
        path = s.get("directory") or ""
        if not path and s.get("projectID") and not self.old_session_rx.match(artifact.rel):
            proj = (
                artifact.disk_path.parent.parent.parent
                / "project"
                / (str(s["projectID"]) + ".json")
            )
            wt = (_read_json(proj) or {}).get("worktree") or ""
            path = wt if wt != "/" else ""
        ctx = _Ctx(str(s.get("id") or artifact.disk_path.stem), str(path))
        yield self._session_row(artifact, ctx, s, _d(s.get("time")).get("created"), 1, opts)

    def _parse_message_file(self, artifact: Artifact, opts: Options, old: bool) -> Iterator[Row]:
        # new: storage/message/<ses>/<msg>.json, root is storage/
        # old: project/<slug>/storage/session/message/<ses>/<msg>.json, root is storage/session/
        orig_root, sep, root = self._orig_root(artifact, 3)
        session_id = artifact.disk_path.parent.name
        msg = _read_json(artifact.disk_path)
        if msg is None:
            ctx, _ = self._session_ctx(root, session_id, old, {})
            row = self._row(artifact, ctx, "", 1, "")
            row.turn_type = "system"
            row.text = "parser: message file could not be decoded"
            yield row
            return
        session_id = str(msg.get("sessionID") or session_id)
        msg_id = str(msg.get("id") or artifact.disk_path.stem)
        msg.setdefault("id", msg_id)
        ctx, _ = self._session_ctx(root, session_id, old, msg)
        # One file holds one message, so the model and agent in force come
        # from the message before it (message ids sort in time order).
        prev = self._previous_message(artifact.disk_path)
        if prev is not None:
            model_row_text(ctx.models, ctx.session_id, *message_ref(prev))
            agent_row_text(ctx.modes, ctx.session_id, prev.get("agent"))
        pdir_rel = ["part", session_id, msg_id] if old else ["part", msg_id]
        pdir = root.joinpath(*pdir_rel)
        parts = []
        errors: list[tuple[int, str, str, str]] = []
        for f in self._children(pdir):
            data, reason, raw = _read_part(f)
            src = orig_root + sep + sep.join([*pdir_rel, f.name])
            if data is None:
                errors.append((1, "unparseable part %s (%s)" % (f.stem, reason), raw, src))
            else:
                parts.append((data, src, 1, None))
        yield from self._message_rows(artifact, ctx, msg, ("", 1, None), parts, opts, errors)
