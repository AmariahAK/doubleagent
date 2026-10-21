"""Crush sessions.

Crush (charmbracelet/crush, checked at ca6ae26) keeps one SQLite database per
project, written through sqlc with goose migrations. See
`research/crush.md`.

Files:

* `<project>/.crush/crush.db`, with `-wal` and `-shm` sidecars
  (`journal_mode=WAL`, so recent messages may exist only in the sidecar).
  The collector gathers it through its project catalog, so `artifact.rel`
  is `.crush/crush.db` relative to the project directory; a database under a
  home (Crush run in `~`) has the same relative path. `project_path` is the
  directory holding `.crush`, taken from the original path, because the
  database records no working directory.
  - `sessions`: `id`, `parent_session_id`, `title`, `message_count`,
    `prompt_tokens`, `completion_tokens`, `cost`, `created_at` (epoch
    seconds).
  - `messages`: `id`, `session_id`, `role` (`user`, `assistant`, `system`,
    `tool`), `parts` (JSON array of `{"type", "data"}`), `model`,
    `provider`, `prism_model_id`, `created_at`, `finished_at` (seconds).
  - Part `data` keys: `text` {`text`, `hidden`}; `reasoning` {`thinking`,
    `started_at`}; `tool_call` {`id`, `name`, `input`}; `tool_result`
    {`tool_call_id`, `name`, `content`, `is_error`}; `finish` {`reason`,
    `time`, `message`, `details`}; `shell_command` {`command`, `output`,
    `exit_code`}; `image_url` {`url`}; `binary` {`Path`, `MIMEType`}.
* `.local/share/crush/projects.json` and `AppData/Local/crush/projects.json`:
  `{"projects": [{"path", "data_dir", "last_accessed"}]}`, the registry of
  every project Crush has opened.
* Every `crush.json` scope (`.config/crush/crush.json`, the data
  `.local/share/crush/crush.json` or `AppData/Local/crush/crush.json`, a
  workspace `.crush/crush.json`, a project's `crush.json` or `.crush.json`):
  `permissions.allowed_tools`, `options.disabled_tools`,
  `mcp.<name>.disabled_tools`, `mcp.<name>.enabled_tools`, and
  `hooks.<event>` (lists of `{name, matcher, command, timeout}`). No other
  key is read, so provider keys and tokens never reach a row.
* `crushrc` shell configs (`.config/crush/crushrc`, a project's `crushrc` or
  `.crushrc`): lines `permissions allow <tool>...` and `permissions deny
  <tool>...` (internal/shellconfig/permissions.go at 7f799fb).
* In `crush.db` also: `sessions.channel`, `sessions.updated_at`,
  `mcp_enabled_servers.name`, `mcp_disabled_servers.name`, `files`
  (`session_id`, `path`, `version`, `content` length, `created_at`),
  `read_files` (`session_id`, `path`, `read_at`), and the `tool_result`
  part's `metadata` string (`{"hook": {"decision", "halt", "reason",
  "hooks": [{"name", "decision", "halt"}]}}`).

Rows: one `system` row per session (title, parent, counts); one row per part,
`text` by message role (`tool` and `system` roles become `system`),
`reasoning` as `thinking` with `--include-thinking`, `tool_call` as
`tool_use`, `tool_result` as `tool_result` joined on `tool_call_id`, and
`shell_command` as `system`. A `finish` part becomes a `system` row only
when the turn ended abnormally (max_tokens, canceled, error,
content_filter, unknown) or carries a message, since every message ends with
one. Parts carry no timestamp of their own: they inherit the message's
`created_at`, except tool calls and results, which use `finished_at` or the
finish part's `time` when set. No git branch is recorded.

Model rows: `model` and `provider` are the model the turn requested, and
`prism_model_id` (migration `20260902000000`, at crush 7f799fb) the model
Hyper's Prism router actually served it with. The served model is
`prism_model_id` when set, else `model`. The first message of a session that
names a model is preceded by a `system` row `model: <served>
provider=<provider>`, and every later message whose served model, requested
model or provider differs by `model: <old served> -> <new served>
provider=<provider>`; ` requested=<model>` is appended when the requested
model differs from the served one. The rows carry the message's `created_at`
and `source_line`, and the `model` column names `<provider>/<served>`. A
message with no `prism_model_id` that requests the same model from the same
provider as the session's last one is not a change, so a Hyper turn's step
without Prism headers does not flip the row back to the request; `tool`
messages carry no model and are skipped. The Prism layout is not observed on
any real install, source-derived (charmbracelet/crush at 7f799fb).

The rows below are source-derived (charmbracelet/crush at 7f799fb, fantasy
v0.45.1 for the metadata copy); not observed on any real install.

Permission rows: after a `tool_result` row, with its `tool_name` and
`tool_use_id`, `permission decision: denied by user` when the error content
is `User denied permission`; `permission decision: <allow|deny|halt> by hook
<names> reason=<reason>` from `metadata.hook` (decision `none` without a
halt is skipped); `permission decision: <deny|halt> by hook` for an error
starting `Tool call blocked by hook.` or `Turn halted by hook.` with no hook
metadata. An approved prompt, a session grant and yolo mode leave nothing.
Standing entries are one row each, `permission setting: <key>=<value> (from
<file>, file mtime)` at the file's modification time with an empty
`session_id`: the crush.json lists and hooks above, `crushrc` lines as
`permissions.allowed_tools=<tool>` (allow) or `options.disabled_tools=<tool>`
(deny) with `(from <file> line <n>, file mtime)`, and the per-project
`mcp_enabled_servers=<name>` and `mcp_disabled_servers=<name>` at the
database file's modification time.

Relay rows (`records_relay`): `session relayed: channel <server> (from
crush.db sessions.channel, as of updated_at)` after the session start of a
session bound to an MCP channel, and `session relayed: channel <source>
[sender <sender>] [group <group>] (from crush.db message <id>)` after the
first user message of a session pushed by each distinct channel, sender and
group (`<channel source=...>` text).

Deletion rows: a sub-agent session whose `parent_session_id` names no
session yields `session deleted: <parent> (parent_session_id of sub-agent
session <id> names no session in crush.db; time is the sub-agent's
updated_at)`, with `session_id` the deleted parent, once per parent.

File rows: `file version: <path> version=<n> bytes=<length> (from crush.db
files)` at the snapshot's `created_at`, and `file read: <path> (from
crush.db read_files, read_at)` at `read_at`; both are deleted with their
session. The snapshot content is not copied into the row.

Bad records: a `parts` value that is not a JSON array becomes one `system`
row through `error_rows`, `parser: unparseable record <rowid> (message <id>
parts: <reason>): <parts>`, carrying the stored value in full, with the
message's session and project, an empty timestamp and `source_line` set to
the rowid; the session's other messages are still yielded.
"""

from __future__ import annotations

import html
import json
import re
import shlex
import sqlite3
from collections.abc import Iterator

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import Options, Parser, compact_json, error_rows, file_mtime, setting_value

DB_RX = re.compile(r"(^|/)\.crush/crush\.db$")
PROJECTS_RX = re.compile(r"^(\.local/share/crush|AppData/Local/crush)/projects\.json$")
ORIGINAL_RX = re.compile(r"^(.*)[\\/]\.crush[\\/]crush\.db$")
# Every crush.json scope the catalog collects: the global config, the global
# data file, the workspace file in a data directory, and a project's own.
CONFIG_RX = re.compile(
    r"^(\.config/crush/crush\.json|\.local/share/crush/crush\.json"
    r"|AppData/Local/crush/crush\.json|\.crush/crush\.json|\.?crush\.json)$"
)
# The global shell config beside crush.json, and a project's crushrc or .crushrc.
CRUSHRC_RX = re.compile(r"^(\.config/crush/crushrc|\.?crushrc)$")
CONFIG_ORIGINAL_RX = re.compile(r"^(.*)[\\/]\.crush[\\/]crush\.json$")
CHANNEL_RX = re.compile(r"^<channel\s([^>]*)>")
ATTR_RX = re.compile(r'([A-Za-z_][\w.-]*)="([^"]*)"')
DENIED = "User denied permission"
HOOK_PREFIXES = (("Tool call blocked by hook.", "deny"), ("Turn halted by hook.", "halt"))
MCP_TABLES = ("mcp_enabled_servers", "mcp_disabled_servers")

NORMAL_FINISH = ("", "end_turn", "tool_use", "stop")


def _join(*parts: str) -> str:
    return " | ".join(x for x in parts if x)


def _str(value) -> str:
    return value if isinstance(value, str) else ""


def _model_text(seen: dict, session_id: str, provider: str, requested: str, prism: str) -> str:
    """The `model:` row text for one message, or "" when the session's model
    is unchanged. `seen` maps a session id to its last (provider, requested,
    served) triple. The served model is `prism` when set, else `requested`;
    a message without `prism` that repeats the last provider and request
    keeps the last served model rather than counting as a change."""
    old = seen.get(session_id)
    served = prism
    if not served:
        if old and old[:2] == (provider, requested):
            return ""
        served = requested
    if not served:
        return ""
    new = (provider, requested, served)
    if old == new:
        return ""
    seen[session_id] = new
    text = "model: %s -> %s" % (old[2], served) if old else "model: " + served
    if provider:
        text += " provider=" + provider
    if requested and requested != served:
        text += " requested=" + requested
    return text


def _metadata(value) -> dict:
    """A tool result's `metadata`, stored as a JSON string, as a dict."""
    if isinstance(value, str) and value:
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def _permission_text(d: dict) -> str:
    """The `permission decision:` text for one `tool_result` part's data, or
    "" when the result records none. A user denial is the error content
    `User denied permission`; a hook's decision is `metadata.hook`, and an
    error result that starts with a hook's block or halt message stands for
    it when the metadata is missing. A hook decision of `none` without a
    halt is not a decision."""
    content = _str(d.get("content"))
    if d.get("is_error") and content == DENIED:
        return "permission decision: denied by user"
    hook = _metadata(d.get("metadata")).get("hook")
    if isinstance(hook, dict):
        decision = "halt" if hook.get("halt") else _str(hook.get("decision"))
        if decision not in ("allow", "deny", "halt"):
            return ""
        hooks = [h for h in hook.get("hooks") or [] if isinstance(h, dict)]
        if decision == "halt":
            chosen = [h for h in hooks if h.get("halt")]
        else:
            chosen = [h for h in hooks if h.get("decision") == decision]
        names = ",".join(_str(h.get("name")) for h in chosen or hooks if _str(h.get("name")))
        text = "permission decision: %s by hook" % decision
        if names:
            text += " " + names
        if _str(hook.get("reason")):
            text += " reason=" + hook["reason"]
        return text
    if d.get("is_error"):
        for prefix, decision in HOOK_PREFIXES:
            if content.startswith(prefix):
                return "permission decision: %s by hook" % decision
    return ""


def _relay_text(text: str, message_id: str) -> tuple[str, str]:
    """For a user message an MCP channel pushed (`<channel source="<server>"
    <meta>>...</channel>`), the `session relayed:` text and the part of it
    that identifies the relay (source, sender, group); ("", "") otherwise."""
    m = CHANNEL_RX.match(text)
    if not m:
        return "", ""
    attrs = {k: html.unescape(v) for k, v in ATTR_RX.findall(m.group(1))}
    key = "session relayed: channel %s" % attrs.get("source", "")
    for name in ("sender", "group"):
        if attrs.get(name):
            key += " %s %s" % (name, attrs[name])
    return key + " (from crush.db message %s)" % message_id, key


def project_of(original: str) -> str:
    m = ORIGINAL_RX.match(original or "")
    return m.group(1) if m else ""


class CrushParser(Parser):
    agent = "crush"
    name = "crush"
    records_relay = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return bool(
            DB_RX.search(rel)
            or PROJECTS_RX.match(rel)
            or CONFIG_RX.match(rel)
            or CRUSHRC_RX.match(rel)
        )

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if PROJECTS_RX.match(artifact.rel):
            yield from self._parse_projects(artifact, opts)
        elif CONFIG_RX.match(artifact.rel):
            yield from self._parse_config(artifact)
        elif CRUSHRC_RX.match(artifact.rel):
            yield from self._parse_crushrc(artifact)
        else:
            yield from self._parse_db(artifact, opts)

    def _system(self, artifact: Artifact, text: str, line: int = 0) -> Row:
        row = self.base_row(artifact)
        row.turn_type = "system"
        row.source_line = line
        row.text = text
        return row

    # -- projects.json ---------------------------------------------------------------
    def _parse_projects(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        try:
            with open(artifact.disk_path, "rb") as fh:
                data = json.loads(fh.read().decode("utf-8", errors="replace"))
        except ValueError as e:
            yield self._system(artifact, "parser: projects.json did not parse: %s" % e)
            return
        projects = data.get("projects") if isinstance(data, dict) else None
        for n, p in enumerate(projects if isinstance(projects, list) else [], 1):
            if not isinstance(p, dict):
                continue
            row = self._system(artifact, "", n)
            row.timestamp_utc = to_utc(p.get("last_accessed"))
            row.project_path = str(p.get("path") or "")
            row.text = compact(
                _join(
                    "crush project last accessed",
                    "data_dir=%s" % p["data_dir"] if p.get("data_dir") else "",
                ),
            )
            yield row

    # -- crush.json and crushrc ------------------------------------------------------
    def _config_project(self, artifact: Artifact) -> str:
        """The project a config file belongs to: the directory holding the
        `.crush` of a workspace `crush.json`, the project directory of a
        project-catalog file, else "" (a global file)."""
        m = CONFIG_ORIGINAL_RX.match(artifact.original or "")
        if m:
            return m.group(1)
        return artifact.home.original if artifact.home.project else ""

    def _setting_row(
        self, artifact: Artifact, ts: str, key: str, value, where: str, line: int = 1
    ) -> Row:
        row = self._system(artifact, "", line)
        row.timestamp_utc = ts
        row.project_path = self._config_project(artifact)
        row.text = compact(
            "permission setting: %s=%s (from %s, file mtime)" % (key, setting_value(value), where)
        )
        return row

    def _parse_config(self, artifact: Artifact) -> Iterator[Row]:
        """One `permission setting:` row per standing entry of a crush.json:
        `permissions.allowed_tools`, `options.disabled_tools`,
        `mcp.<name>.disabled_tools` and `enabled_tools`, and each hook under
        `hooks.<event>`. Nothing else is read, so no key is printed."""
        ts = file_mtime(artifact)
        try:
            doc = json.loads(artifact.disk_path.read_bytes().decode("utf-8", errors="replace"))
        except (OSError, ValueError):
            doc = None
        if not isinstance(doc, dict):
            row = self._system(artifact, "parser: %s is not a JSON object" % artifact.rel, 1)
            row.timestamp_utc = ts
            row.project_path = self._config_project(artifact)
            yield row
            return
        lists = []
        for section, key in (("permissions", "allowed_tools"), ("options", "disabled_tools")):
            block = doc.get(section)
            if isinstance(block, dict):
                lists.append(("%s.%s" % (section, key), block.get(key)))
        mcp = doc.get("mcp")
        for name, server in mcp.items() if isinstance(mcp, dict) else []:
            if isinstance(server, dict):
                for key in ("disabled_tools", "enabled_tools"):
                    lists.append(("mcp.%s.%s" % (name, key), server.get(key)))
        hooks = doc.get("hooks")
        for event, entries in hooks.items() if isinstance(hooks, dict) else []:
            lists.append(("hooks.%s" % event, entries))
        for key, entries in lists:
            for entry in entries if isinstance(entries, list) else []:
                yield self._setting_row(artifact, ts, key, entry, artifact.rel)

    def _parse_crushrc(self, artifact: Artifact) -> Iterator[Row]:
        """One `permission setting:` row per tool named on a `permissions
        allow` or `permissions deny` line of a crushrc shell config: allow
        adds to `permissions.allowed_tools`, deny to `options.disabled_tools`.
        Only lines whose first word is `permissions` are read, as written,
        whether or not a condition around them runs; such a line that does
        not split into shell words (an unclosed quote) is a bad line."""
        try:
            lines = artifact.disk_path.read_bytes().decode("utf-8", errors="replace")
        except OSError as e:
            yield self._system(artifact, "parser: %s could not be read: %s" % (artifact.rel, e))
            return
        ts = file_mtime(artifact)
        keys = {"allow": "permissions.allowed_tools", "deny": "options.disabled_tools"}
        errors: list = []
        for n, line in enumerate(lines.split("\n"), 1):
            line = line[:-1] if line.endswith("\r") else line
            if not line.lstrip().startswith("permissions"):
                continue
            try:
                words = shlex.split(line, comments=True)
            except ValueError as e:
                errors.append((n, "unparseable line (%s)" % e, line))
                continue
            if len(words) < 3 or words[0] != "permissions" or words[1] not in keys:
                continue
            where = "%s line %d" % (artifact.rel, n)
            for tool in words[2:]:
                yield self._setting_row(artifact, ts, keys[words[1]], tool, where, n)
        yield from error_rows(self, artifact, errors, "", self._config_project(artifact))

    # -- .crush/crush.db ---------------------------------------------------------------
    def _parse_db(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        project_path = project_of(artifact.original)
        if not is_sqlite(artifact.disk_path):
            row = self._system(artifact, "parser: not a SQLite database")
            row.project_path = project_path
            yield row
            return
        try:
            with open_copy(artifact.disk_path) as con:
                tables = table_names(con)
                if "messages" not in tables:
                    return
                if "sessions" in tables:
                    yield from self._session_rows(artifact, con, project_path)
                yield from self._mcp_rows(artifact, con, tables, project_path)
                models: dict = {}
                relayed: set = set()
                for m in con.execute(
                    "select rowid as _rowid, * from messages order by created_at, rowid"
                ):
                    yield from self._message_rows(
                        artifact, dict(m), project_path, opts, models, relayed
                    )
                yield from self._file_rows(artifact, con, tables, project_path)
        except sqlite3.DatabaseError as e:
            row = self._system(artifact, "parser: SQLite error: %s" % e)
            row.project_path = project_path
            yield row

    def _session_rows(self, artifact: Artifact, con, project_path: str) -> Iterator[Row]:
        """A `session start` row per session, a `session relayed:` row for a
        session bound to an MCP channel (`sessions.channel`), and a `session
        deleted:` row per parent a sub-agent session names that has no
        `sessions` row: the delete removes one id, and `parent_session_id`
        has no foreign key."""
        sessions = [
            dict(s)
            for s in con.execute(
                "select rowid as _rowid, * from sessions order by created_at, rowid"
            )
        ]
        ids = {str(s.get("id") or "") for s in sessions}
        for s in sessions:
            sid = str(s.get("id") or "")
            row = self._system(artifact, "", s["_rowid"])
            row.session_id = sid
            row.project_path = project_path
            row.timestamp_utc = to_utc(s.get("created_at"))
            row.text = compact(
                _join(
                    "session start",
                    s.get("title") or "",
                    "parent=%s" % s["parent_session_id"] if s.get("parent_session_id") else "",
                    "%s messages" % s["message_count"]
                    if s.get("message_count") is not None
                    else "",
                    "tokens in=%s out=%s"
                    % (s.get("prompt_tokens") or 0, s.get("completion_tokens") or 0),
                    "cost=%s" % s["cost"] if s.get("cost") else "",
                ),
            )
            yield row
            if _str(s.get("channel")):
                row = self._system(artifact, "", s["_rowid"])
                row.session_id = sid
                row.project_path = project_path
                row.timestamp_utc = to_utc(s.get("updated_at")) or to_utc(s.get("created_at"))
                row.text = compact(
                    "session relayed: channel %s (from crush.db sessions.channel, as of updated_at)"
                    % s["channel"]
                )
                yield row
        orphans: set = set()
        for s in sessions:
            parent = _str(s.get("parent_session_id"))
            if not parent or parent in ids or parent in orphans:
                continue
            orphans.add(parent)
            row = self._system(artifact, "", s["_rowid"])
            row.session_id = parent
            row.project_path = project_path
            row.timestamp_utc = to_utc(s.get("updated_at")) or to_utc(s.get("created_at"))
            row.text = compact(
                "session deleted: %s (parent_session_id of sub-agent session %s names no "
                "session in crush.db; time is the sub-agent's updated_at)" % (parent, s.get("id"))
            )
            yield row

    def _mcp_rows(self, artifact: Artifact, con, tables, project_path: str) -> Iterator[Row]:
        """One `permission setting:` row per MCP server the user turned on or
        off for this project (`mcp_enabled_servers`, `mcp_disabled_servers`),
        at the database file's modification time."""
        for table in MCP_TABLES:
            if table not in tables:
                continue
            for r in con.execute("select rowid as _rowid, name from %s order by rowid" % table):
                row = self._system(artifact, "", r["_rowid"])
                row.timestamp_utc = file_mtime(artifact)
                row.project_path = project_path
                row.text = compact(
                    "permission setting: %s=%s (from %s, file mtime)"
                    % (table, r["name"], artifact.rel)
                )
                yield row

    def _file_rows(self, artifact: Artifact, con, tables, project_path: str) -> Iterator[Row]:
        """A `file version:` row per `files` snapshot (path, version and the
        stored content's length, not the content) at its `created_at`, and a
        `file read:` row per `read_files` entry at its `read_at`."""
        if "files" in tables:
            for f in con.execute(
                "select rowid as _rowid, session_id, path, version, length(content) as size,"
                " created_at from files order by created_at, rowid"
            ):
                row = self._system(artifact, "", f["_rowid"])
                row.session_id = str(f["session_id"] or "")
                row.project_path = project_path
                row.timestamp_utc = to_utc(f["created_at"])
                row.text = compact(
                    "file version: %s version=%s bytes=%s (from crush.db files)"
                    % (f["path"], f["version"], f["size"] or 0)
                )
                yield row
        if "read_files" in tables:
            for f in con.execute(
                "select rowid as _rowid, session_id, path, read_at from read_files"
                " order by read_at, rowid"
            ):
                row = self._system(artifact, "", f["_rowid"])
                row.session_id = str(f["session_id"] or "")
                row.project_path = project_path
                row.timestamp_utc = to_utc(f["read_at"])
                row.text = compact("file read: %s (from crush.db read_files, read_at)" % f["path"])
                yield row

    def _message_rows(
        self,
        artifact: Artifact,
        m: dict,
        project_path: str,
        opts: Options,
        models: dict,
        relayed: set,
    ) -> Iterator[Row]:
        role = str(m.get("role") or "")
        provider = _str(m.get("provider"))
        requested, prism = _str(m.get("model")), _str(m.get("prism_model_id"))
        model_id = prism or requested
        model = "%s/%s" % (provider, model_id) if provider and model_id else model_id
        created = to_utc(m.get("created_at"))
        session_id = str(m.get("session_id") or "")

        def base(ts: str = "") -> Row:
            row = self.base_row(artifact)
            row.source_line = m["_rowid"]
            row.session_id = str(m.get("session_id") or "")
            row.project_path = project_path
            row.model = model
            row.timestamp_utc = ts or created
            return row

        text = _model_text(models, session_id, provider, requested, prism)
        if text:
            row = base()
            row.turn_type = "system"
            row.text = text
            yield row
        raw = m.get("parts")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        elif raw is not None and not isinstance(raw, str):
            raw = str(raw)
        try:
            parts = json.loads(raw or "[]")
            if not isinstance(parts, list):
                raise ValueError("not a JSON array")
        except ValueError as e:
            reason = "unparseable record %s (message %s parts: %s)" % (m["_rowid"], m.get("id"), e)
            errors = [(m["_rowid"], reason, raw)]
            yield from error_rows(self, artifact, errors, session_id, project_path)
            return
        finished = to_utc(m.get("finished_at")) if m.get("finished_at") else ""
        for p in parts:
            if isinstance(p, dict) and p.get("type") == "finish":
                t = (p.get("data") or {}).get("time")
                if t and not finished:
                    finished = to_utc(t)
        text_type = role if role in ("user", "assistant") else "system"

        for p in parts:
            if not isinstance(p, dict):
                continue
            after: list = []  # rows that follow this part's own row
            kind = p.get("type")
            d = p.get("data")
            if not isinstance(d, dict):
                d = {}
            row = base()
            if kind == "text":
                row.turn_type = text_type
                text = d.get("text") or ""
                if role not in ("user", "assistant"):
                    text = "%s: %s" % (role, text)
                if d.get("hidden"):
                    text = "[hidden] " + text
                relay, key = _relay_text(text, str(m.get("id") or ""))
                if relay and role == "user" and (session_id, key) not in relayed:
                    relayed.add((session_id, key))
                    extra = base()
                    extra.turn_type = "system"
                    extra.text = compact(relay)
                    after.append(extra)
            elif kind == "reasoning":
                if not opts.include_thinking or not d.get("thinking"):
                    continue
                row.turn_type = "thinking"
                row.timestamp_utc = to_utc(d.get("started_at")) or created
                text = d.get("thinking")
            elif kind == "tool_call":
                row.turn_type = "tool_use"
                row.timestamp_utc = finished or created
                row.tool_name = str(d.get("name") or "")
                row.tool_use_id = str(d.get("id") or "")
                text = (
                    d.get("input")
                    if isinstance(d.get("input"), str)
                    else compact_json(d.get("input"))
                )
            elif kind == "tool_result":
                row.turn_type = "tool_result"
                row.timestamp_utc = finished or created
                row.tool_name = str(d.get("name") or "")
                row.tool_use_id = str(d.get("tool_call_id") or "")
                text = d.get("content") or ""
                if not text and d.get("mime_type"):
                    text = "[%s]" % d["mime_type"]
                if d.get("is_error"):
                    text = "[error] " + text
                decision = _permission_text(d)
                if decision:
                    extra = base(row.timestamp_utc)
                    extra.turn_type = "system"
                    extra.tool_name, extra.tool_use_id = row.tool_name, row.tool_use_id
                    extra.text = compact(decision)
                    after.append(extra)
            elif kind == "finish":
                reason = str(d.get("reason") or "")
                if reason in NORMAL_FINISH and not d.get("message"):
                    continue
                row.turn_type = "system"
                row.timestamp_utc = to_utc(d.get("time")) if d.get("time") else created
                text = _join("finish: " + reason, d.get("message") or "", d.get("details") or "")
            elif kind == "shell_command":
                row.turn_type = "system"
                text = _join(
                    "shell: " + str(d.get("command") or ""),
                    "exit=%s" % d["exit_code"] if "exit_code" in d else "",
                    d.get("output") or "",
                )
            elif kind == "image_url":
                row.turn_type = text_type
                url = str(d.get("url") or "")
                text = "[image] " + (url.split(",", 1)[0] if url.startswith("data:") else url)
            elif kind == "binary":
                row.turn_type = text_type
                text = "[binary] " + _join(
                    str(d.get("Path") or d.get("path") or ""),
                    str(d.get("MIMEType") or d.get("mime_type") or ""),
                )
            else:
                row.turn_type = "system"
                text = "%s: %s" % (kind, compact_json(d))
            row.text = compact(text)
            yield row
            yield from after
