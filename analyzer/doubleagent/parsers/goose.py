"""Goose CLI and desktop sessions.

Goose (block/goose, checked at 591edd4) resolves its directories with
etcetera's app strategy: XDG paths on Linux and macOS, `AppData/Roaming/
Block/goose/{config,data}` on Windows, where state falls back to data. See
`research/goose.md`.

Files, relative to the home directory (`<data>` is `.local/share/goose` or
`AppData/Roaming/Block/goose/data`, `<state>` is `.local/state/goose` or the
Windows data directory):

* `<data>/sessions/sessions.db`, with `-wal` and `-shm` sidecars (WAL mode),
  schema version 16. Older databases lack columns added by later
  migrations, so every column is read with a default.
  - `sessions`: `id`, `name`, `description`, `session_type`, `working_dir`,
    `created_at` (SQLite `CURRENT_TIMESTAMP` text or RFC 3339),
    `provider_name`, `model_config_json` (`model_name`),
    `parent_session_id`, `schedule_id`, `accumulated_total_tokens`.
  - `messages`: `id`, `session_id`, `role` (`user`, `assistant`),
    `content_json`, `created_timestamp` (epoch seconds; values above 1e10
    are milliseconds, as Goose itself normalises them),
    `metadata_json` (`userVisible`, `inference.provider`,
    `inference.requestedModel`, `inference.resolvedModel`).
* `<data>/sessions/<YYYYMMDD_HHMMSS>.jsonl`: legacy sessions, imported into
  the database once. Line 1 is metadata (`id`, `description`,
  `working_dir`, `created_at`); each later line is a message with `id`,
  `role`, `created` (epoch seconds) and `content`.
* `<state>/logs/llm_request.<N>.jsonl`: one file per provider call, the
  last 10 kept. A request line with `model_config.model_name` and
  `input.messages`, then response lines with `data` (a message: `id`,
  `role`, `created`, `content`) and `usage`. A streaming provider logs one
  line per chunk; consecutive chunks with the same `data.id` are assembled
  into one message as `Conversation::push` does
  (goose-provider-types/src/conversation.rs:75-119 at aaif-goose/goose
  fb9e3c8), so the assembled text equals the `sessions.db` row's. A
  secondary source (issue 126): `secondary()` is True for it, because the
  response messages repeat the database's assistant messages, and it
  outlives a session removed, cleared or rewound until 10 later calls rotate
  it out. `secondary_tolerance()` is 600 seconds: the log stamps a message
  with its first chunk's `created`, while `sessions.db` stores
  `max(created, the session's newest created_timestamp)`
  (session/session_manager.rs:2109-2118 at fb9e3c8), so the database row
  can be later by as long as the tool calls before it ran, and a chunk
  with no message id keeps its own, later, time. The request row has no
  twin in the database and is always kept. Source-derived; not observed on
  any real install.
* `<config>/permission.yaml` (`<config>` is `.config/goose` or
  `AppData/Roaming/Block/goose/config`): the standing tool lists, a map
  from category (`user`, `smart_approve`) to `always_allow`, `ask_before`
  and `never_allow` block lists, as serde_yaml writes them
  (config/permission.rs:13-44, 260-262 at fb9e3c8). Only that nesting is
  read, without a YAML dependency; any other line is a bad line.
* `<config>/roaming_trust.json`: `{allowed: [<peer key>], revoked_keys:
  [<peer key>]}`, the roaming peers allowed or refused
  (goose-roaming/src/trust.rs:19-26 at fb9e3c8).
* `<data>/schedule.json`: a JSON array of scheduled jobs, `id`, `source`,
  `cron`, `last_run` (RFC 3339 or null), `currently_running`, `paused`,
  `current_session_id`, `parameters` (pairs), `recipe_base_dir`
  (scheduler/common.rs:167-187 at fb9e3c8).
* `<state>/history.txt` and the older `.config/goose/history.txt`: rustyline
  V2 history, `#V2` header then one prompt per line with `\\n` and `\\\\`
  escaped. No timestamps and no session id. A secondary source (issue
  122): `secondary()` is True for it and the database is the primary
  store. The CLI adds every non-empty line typed at its prompt, slash
  commands included, and saves the file before the message is sent
  (`goose-cli/src/session/input.rs`, `session/mod.rs` at 591edd4), so a
  prompt's text equals its `messages` row's once both are stripped; a
  session removed with `goose session remove` leaves its prompts here.
  Rows have an empty `timestamp_utc`, `session_id` and `project_path`, so
  `dedup.deduplicate` pairs them with a database `user` row of any
  session on text alone. rustyline keeps the last 100 entries and drops
  a consecutive repeat. When both files exist each is read.

Content blocks (`type`, camelCase): `text` {`text`}; `image` {`mimeType`};
`document` {`name`, `mimeType`}; `toolRequest` {`id`, `toolCall`: {`status`,
`value`: {`name`, `arguments`} | `error`}}; `toolResponse` {`id`,
`toolResult`: {`status`, `value`: {`content`, `isError`} or a bare content
array | `error`}}; `thinking` {`thinking`}; `redactedThinking`;
`toolConfirmationRequest` {`toolName`, `arguments`, `prompt`};
`actionRequired` {`data`}; `systemNotification` {`notificationType`, `msg`};
`error` {`kind`, `message`}.

Rows: one `system` row per session; one row per content block: text by
role, `toolRequest` as `tool_use`, `toolResponse` as `tool_result` (the tool
name looked up from the request with the same id), thinking blocks only with
`--include-thinking`, the rest as `system`. Text the user never saw
(`userVisible: false`, such as compaction summaries) is prefixed
`[hidden]`. The model is `inference.provider/resolvedModel` (or
`requestedModel`) per message, falling back to the session's
`provider_name/model_config_json.model_name`. No git branch is recorded.
The request log has no session id or cwd: its request line becomes one
`system` row and each response message becomes rows like a transcript's,
timestamped by the response's `created`; the request row inherits the first
response's time. History entries carry no timestamp.

Model and permission rows from `sessions.db` (issues 96 and 97), all
`system`:

* `model: <model_config_json.model_name> provider=<provider_name>` and
  `permission mode: <goose_mode>` after each session's start row, at
  `created_at`. `goose_mode` (default `auto`) is one value per session row,
  so there is no mode change row.
* `model: <old> -> <new> provider=<inference.provider>` before the rows of
  a message whose `metadata_json.inference` names a different model
  (`resolvedModel`, else `requestedModel`), with ` requested=<requestedModel>`
  when the two differ; the start value is the session's model. Messages
  without `inference` (user messages) do not change it.
* Per call (issue 209), from `actionRequired` blocks
  (`data.actionType`, message.rs:194-219 at fb9e3c8):
  `permission request: <toolName> | <prompt> | <arguments>` for a
  `toolConfirmation` (an empty prompt is left out) and `permission
  decision: <permission> (toolConfirmationResponse)` for its answer
  (`allow_once`, `always_allow`, `deny_once`, `always_deny`, `cancel`),
  each with the block's `id` as `tool_use_id` and the tool name (the
  answer's looked up from the request). A `toolRequest` whose `_meta`
  holds `goose.executable` `false` and that no `toolConfirmationResponse`
  of its session answers, a call the permission check refused or held, is
  followed by `permission decision: not executable
  (goose.executable=false)` with its tool name and id
  (agents/state_machine/ops_tool_approval.rs:23, 57-127, 271-289 at
  fb9e3c8); only `sessions.db` is checked. An `elicitation` or
  `elicitationResponse` keeps the generic `action required: <compact
  JSON>` row; an older `toolConfirmationRequest` block keeps its
  `confirmation requested:` row.
* Standing (issue 209), at the file's modification time with an empty
  `session_id`: `permission setting: <category>.<level>=<tool> (from
  <file>, file mtime)` per tool in `permission.yaml` and `permission
  setting: roaming_trust.<allowed|revoked_keys>=<key> (from <file>, file
  mtime)` per peer key, `<file>` the path relative to the home.
* Scheduled jobs (issue 209), one row per `schedule.json` job at the
  file's modification time with an empty `session_id`: `scheduled task:
  <id> <cron> paused=<true|false> running=<true|false> source=<source>
  last_run=<time> current_session=<id> recipe_base_dir=<dir>[
  parameters=<compact JSON>] (from <file>, file mtime)`, `-` for an absent
  value, `parameters` only when the job has any. A job's sessions run in
  mode `auto` (scheduler/full.rs:876-882 at fb9e3c8) and name it in their
  start row's `schedule=`.
* Every row from these sources is source-derived; not observed on any
  real install. A whole-file problem in `roaming_trust.json` or
  `schedule.json` (unreadable, not JSON, not the expected type) is one
  `parser: <message>` row; a `schedule.json` job that is not an object is
  `parser: unparseable record <N> (not a JSON object): <record>`.

The legacy JSONL sessions record no model, and the request log has no
session id, so neither yields model rows.

Bad stored values in `sessions.db` (issue 183): a `content_json`,
`metadata_json` or `model_config_json` that does not decode as JSON, or
decodes to another type than Goose writes (an array for `content_json`,
an object for the other two), is one `system` row through `error_rows`,
`parser: unparseable record <N> (<table>.<column>: <reason>): <stored
value>`, the stored text in full, `<N>` the `messages.id` or the
`sessions` rowid, with the session's `session_id` and `working_dir`, an
empty `timestamp_utc` and `source_line` `<N>`. A NULL or empty
`content_json` gives the same row with reason `empty` and no value. The
session's other rows are still yielded: a bad `model_config_json` row
follows the session start row and the session has no model; a bad
`metadata_json` row precedes the message's content rows, which are kept
with the session's model and as visible; a bad `content_json` row stands
in for the message's content rows. Fixture only: the shapes are
source-derived (block/goose at 591edd4), no real install has shown a bad
value.

Relayed sessions (issue 153): a `sessions` row whose `session_type` is
`gateway` was carried through the gateway's chat bot (Telegram, the one
platform implemented), so the chat keeps a copy on the platform. Its
`name` is `<platform>/<display name or user id>` and its `working_dir`
`.config/goose/gateway/<platform>/<user_id>`
(`crates/goose/src/gateway/handler.rs:304-326` at aaif-goose/goose
bfcc6ee). One `system` row after the session's start row, at
`created_at`: `session relayed: gateway <platform> user <user_id> display
<display> (from sessions.db session_type gateway, created_at)`, platform
and user id from `working_dir` (the platform from `name` when the path
does not match), display from `name`, `-` when it is absent or is the user
id. It is not vendor sync, so `records_sync` stays False; `records_relay`
is set, so a session without the row is `relayed` `no`. `config.yaml`
`gateway_pairings` repeats the platform and user id and adds `paired_at`,
but it is nested YAML (no YAML dependency) and a secret glob, so it is
not read. Fixture only: no real install has shown a gateway session.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterator

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
    line_text,
    setting_value,
    text_of,
    track_change,
)

DATA = r"(?:\.local/share/goose|AppData/Roaming/Block/goose/data)"
STATE = r"(?:\.local/state/goose|AppData/Roaming/Block/goose/data)"
CONFIG = r"(?:\.config/goose|AppData/Roaming/Block/goose/config)"
DB_RX = re.compile(r"^%s/sessions/sessions\.db$" % DATA)
LEGACY_RX = re.compile(r"^%s/sessions/[^/]+\.jsonl$" % DATA)
LLM_RX = re.compile(r"^%s/logs/llm_request\.[^/]+\.jsonl$" % STATE)
HISTORY_RX = re.compile(r"^(?:%s|\.config/goose)/history\.txt$" % STATE)
PERMISSION_RX = re.compile(r"^%s/permission\.yaml$" % CONFIG)
TRUST_RX = re.compile(r"^%s/roaming_trust\.json$" % CONFIG)
SCHEDULE_RX = re.compile(r"^%s/schedule\.json$" % DATA)
# The request log stamps each streamed chunk when it arrives, while
# `sessions.db` stamps the assembled message with the later of its first
# chunk's time and the session's newest stored message (issue 126).
LLM_TOLERANCE_SECONDS = 600.0
TOOL_EXECUTABLE_KEY = "goose.executable"
# A gateway session's working directory, `<config>/gateway/<platform>/<user_id>`.
GATEWAY_DIR_RX = re.compile(r"[/\\]gateway[/\\]([^/\\]+)[/\\]([^/\\]+)[/\\]?$")


def epoch(value) -> str:
    """`created_timestamp` is seconds, but some clients write milliseconds;
    Goose divides anything above 1e10 by 1000 (session_manager.rs:729-741)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 10_000_000_000:
        value = value / 1000.0
    return to_utc(value)


def _stored_json(value, kind: type) -> tuple[object, str, str]:
    """(decoded value, reason, stored text) of a JSON column of `sessions.db`.
    `kind` is the type Goose writes there (`list` for `content_json`, `dict`
    for `metadata_json` and `model_config_json`). A NULL or empty column
    gives (None, "", ""); a value that does not decode, or decodes to a
    type other than `kind` (a JSON `null` excepted), gives (None, reason,
    the stored text in full) for an `unparseable record` row (issue 183).
    A BLOB is read as UTF-8 with replacement."""
    if value is None or value == "" or value == b"":
        return None, "", ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if not isinstance(value, str):
        return None, "not JSON text", str(value)
    try:
        obj = json.loads(value)
    except ValueError as e:
        return None, str(e), value
    if obj is not None and not isinstance(obj, kind):
        return None, "not a JSON %s" % ("array" if kind is list else "object"), value
    return obj, "", value


def _join(*parts: str) -> str:
    return " | ".join(x for x in parts if x)


def gateway_text(session: dict) -> str:
    """The `session relayed:` text of a `gateway` session, `""` for any
    other: platform and user id from `working_dir`
    (`<config>/gateway/<platform>/<user_id>`), else the platform from
    `name`; the display name from `name` (`<platform>/<display name or user
    id>`), `-` when it is the user id or absent."""
    if session.get("session_type") != "gateway":
        return ""
    m = GATEWAY_DIR_RX.search(str(session.get("working_dir") or ""))
    platform, user_id = m.groups() if m else ("", "")
    name_platform, _, display = str(session.get("name") or "").partition("/")
    platform = platform or name_platform
    if display == user_id:
        display = ""
    return (
        "session relayed: gateway %s user %s display %s"
        " (from sessions.db session_type gateway, created_at)"
        % (platform or "-", user_id or "-", display or "-")
    )


def _model(provider: str, name: str) -> str:
    return "%s/%s" % (provider, name) if provider and name else name or ""


def result_text(tool_result) -> tuple[str, bool]:
    """(text, is_error) of a toolResponse.toolResult."""
    if not isinstance(tool_result, dict):
        return compact_json(tool_result), False
    if tool_result.get("status") == "error":
        return str(tool_result.get("error") or ""), True
    value = tool_result.get("value")
    if isinstance(value, list):  # older rows: bare content array
        return text_of(value), False
    if isinstance(value, dict):
        text = text_of(value.get("content"))
        if not text and value.get("structuredContent") is not None:
            text = compact_json(value["structuredContent"])
        return text, bool(value.get("isError"))
    return "", False


def unescape_history(line: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            nxt = line[i + 1]
            out.append("\n" if nxt == "n" else nxt)
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _unquote(value: str) -> str:
    """A YAML scalar as `serde_yaml` writes it: plain, single-quoted (`''`
    for a quote) or double-quoted (JSON escapes)."""
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except ValueError:
            return value[1:-1]
        return decoded if isinstance(decoded, str) else value[1:-1]
    return value


def permission_entries(path, errors: list) -> Iterator[tuple[int, str, str, str]]:
    """(line, category, level, tool) for each tool in `permission.yaml`,
    which `serde_yaml` writes as a map from category (`user`,
    `smart_approve`) to `{always_allow, ask_before, never_allow}`, each a
    block list of tool names or `[]` (config/permission.rs:13-44, 260-262 at
    aaif-goose/goose fb9e3c8). Only that one nesting level is read: a line
    that is not a category, a level or a list item under both is appended to
    `errors` as (line, message, raw), as `iter_jsonl` does for JSONL."""
    category = level = ""
    with open(path, "rb") as fh:
        for n, raw in enumerate(fh, 1):
            text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            body = text.strip()
            if not body or body.startswith("#") or body in ("---", "{}"):
                continue
            indent = len(text) - len(text.lstrip(" "))
            if body.startswith("- ") or body == "-":
                tool = _unquote(body[1:].strip())
                if category and level and tool:
                    yield n, category, level, tool
                    continue
            elif body.endswith(":") and indent == 0:
                category, level = _unquote(body[:-1].strip()), ""
                continue
            elif indent > 0 and category:
                key, sep, value = body.partition(":")
                if sep and value.strip() in ("", "[]") and key.strip():
                    level = _unquote(key.strip())
                    continue
            errors.append(
                (n, "unparseable line (not a category, level or list item)", line_text(raw))
            )


def _audience(block: dict):
    annotations = block.get("annotations")
    return annotations.get("audience") if isinstance(annotations, dict) else None


def merge_delta(blocks: list, new: list) -> None:
    """Append one streamed chunk's content blocks to the message assembled so
    far, as `Conversation::push` does for chunks with the same message id
    (goose-provider-types/src/conversation.rs:75-119 at aaif-goose/goose
    fb9e3c8): a one-block text chunk extends a last text block of the same
    audience, a one-block thinking chunk extends a last thinking block that
    is unsigned or has its signature, and anything else is appended."""
    if len(new) == 1 and blocks and isinstance(blocks[-1], dict) and isinstance(new[0], dict):
        last, block = blocks[-1], new[0]
        kind = last.get("type")
        if kind == "text" == block.get("type") and _audience(last) == _audience(block):
            blocks[-1] = dict(last, text=str(last.get("text") or "") + str(block.get("text") or ""))
            return
        if kind == "thinking" == block.get("type") and (
            not last.get("signature") or block.get("signature") == last.get("signature")
        ):
            merged = dict(
                last, thinking=str(last.get("thinking") or "") + str(block.get("thinking") or "")
            )
            if block.get("signature"):
                merged["signature"] = block["signature"]
            blocks[-1] = merged
            return
    blocks.extend(new)


def schedule_text(job: dict, rel: str) -> str:
    """The `scheduled task:` text of one `schedule.json` job
    (`ScheduledJob`, scheduler/common.rs:167-187 at aaif-goose/goose
    fb9e3c8), `-` for an absent value; `parameters` is added only when the
    job has any."""

    def value(key: str) -> str:
        v = job.get(key)
        return "-" if v is None or v == "" else setting_value(v)

    params = job.get("parameters")
    return (
        "scheduled task: %s %s paused=%s running=%s source=%s last_run=%s"
        " current_session=%s recipe_base_dir=%s%s (from %s, file mtime)"
        % (
            value("id"),
            value("cron"),
            setting_value(bool(job.get("paused"))),
            setting_value(bool(job.get("currently_running"))),
            value("source"),
            to_utc(job.get("last_run")) or value("last_run"),
            value("current_session_id"),
            value("recipe_base_dir"),
            " parameters=%s" % compact_json(params) if params else "",
            rel,
        )
    )


class GooseParser(Parser):
    agent = "goose"
    name = "goose"
    has_secondary = True
    records_relay = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.match(rel)
            for rx in (
                DB_RX,
                LEGACY_RX,
                LLM_RX,
                HISTORY_RX,
                PERMISSION_RX,
                TRUST_RX,
                SCHEDULE_RX,
            )
        )

    def secondary(self, artifact: Artifact) -> bool:
        return bool(HISTORY_RX.match(artifact.rel) or LLM_RX.match(artifact.rel))

    def secondary_tolerance(self, artifact: Artifact) -> float:
        if LLM_RX.match(artifact.rel):
            return LLM_TOLERANCE_SECONDS
        return super().secondary_tolerance(artifact)

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        if DB_RX.match(rel):
            yield from self._parse_db(artifact, opts)
        elif LEGACY_RX.match(rel):
            yield from self._parse_legacy(artifact, opts)
        elif LLM_RX.match(rel):
            yield from self._parse_llm_log(artifact, opts)
        elif PERMISSION_RX.match(rel):
            yield from self._parse_permission_yaml(artifact)
        elif TRUST_RX.match(rel):
            yield from self._parse_roaming_trust(artifact)
        elif SCHEDULE_RX.match(rel):
            yield from self._parse_schedule(artifact)
        else:
            yield from self._parse_history(artifact, opts)

    def _row(
        self,
        artifact: Artifact,
        line: int,
        session_id: str = "",
        project_path: str = "",
        model: str = "",
        ts: str = "",
    ) -> Row:
        row = self.base_row(artifact)
        row.source_line = line
        row.session_id = session_id
        row.project_path = project_path
        row.model = model
        row.timestamp_utc = ts
        return row

    @staticmethod
    def _system_copy(base: Row, text: str) -> Row:
        """A `system` row with `base`'s attribution, time and model."""
        row = Row(**base.__dict__)
        row.turn_type = "system"
        row.tool_name = ""
        row.tool_use_id = ""
        row.text = text
        return row

    # -- content blocks, shared by every store ------------------------------------------
    def _block_rows(
        self,
        artifact: Artifact,
        base: Row,
        role: str,
        content,
        user_visible: bool,
        tool_names: dict[str, str],
        opts: Options,
        answered: set[str] | None = None,
    ) -> Iterator[Row]:
        """`answered` holds the ids of the tool requests the session's
        `toolConfirmationResponse` blocks answer; when it is given (only for
        `sessions.db`), a `toolRequest` whose `_meta` holds
        `goose.executable` `false` and no answer is followed by its
        `permission decision: not executable` row."""
        if isinstance(content, str):
            text_block: dict = {"type": "text", "text": content}
            content = [text_block]
        if not isinstance(content, list):
            return
        text_type = role if role in ("user", "assistant") else "system"
        for b in content:
            if not isinstance(b, dict):
                continue
            kind = b.get("type")
            row = Row(**base.__dict__)
            if kind == "text":
                row.turn_type = text_type
                text = b.get("text") or ""
                if role not in ("user", "assistant"):
                    text = "%s: %s" % (role, text)
                if not user_visible:
                    text = "[hidden] " + text
            elif kind in ("image", "document"):
                row.turn_type = text_type
                text = "[%s] %s" % (
                    kind,
                    _join(str(b.get("name") or ""), str(b.get("mimeType") or "")),
                )
            elif kind == "toolRequest":
                row.turn_type = "tool_use"
                row.tool_use_id = str(b.get("id") or "")
                call = b.get("toolCall") or {}
                if call.get("status") == "error":
                    text = "[error] " + str(call.get("error") or "")
                else:
                    value = call.get("value") or {}
                    row.tool_name = str(value.get("name") or "")
                    text = compact_json(value.get("arguments") or {})
                tool_names[row.tool_use_id] = row.tool_name
            elif kind == "toolResponse":
                row.turn_type = "tool_result"
                row.tool_use_id = str(b.get("id") or "")
                row.tool_name = tool_names.get(row.tool_use_id, "")
                text, is_error = result_text(b.get("toolResult"))
                if is_error:
                    text = "[error] " + text
            elif kind in ("thinking", "redactedThinking"):
                if not opts.include_thinking:
                    continue
                row.turn_type = "thinking"
                text = (b.get("thinking") or "") if kind == "thinking" else "[redacted thinking]"
            elif kind == "toolConfirmationRequest":
                row.turn_type = "system"
                row.tool_name = str(b.get("toolName") or "")
                row.tool_use_id = str(b.get("id") or "")
                text = _join(
                    "confirmation requested: " + row.tool_name,
                    str(b.get("prompt") or ""),
                    compact_json(b.get("arguments") or {}),
                )
            elif kind == "systemNotification":
                row.turn_type = "system"
                text = "%s: %s" % (b.get("notificationType") or "notification", b.get("msg") or "")
            elif kind == "error":
                row.turn_type = "system"
                text = "error %s: %s" % (b.get("kind") or "", b.get("message") or "")
            elif kind == "actionRequired":
                row.turn_type = "system"
                text = self._action_text(row, b.get("data"), tool_names)
            else:
                row.turn_type = "system"
                text = compact_json(b)
            row.text = compact(text)
            yield row
            if kind == "toolRequest" and answered is not None:
                verdict = b.get("_meta")
                if (
                    isinstance(verdict, dict)
                    and verdict.get(TOOL_EXECUTABLE_KEY) is False
                    and row.tool_use_id not in answered
                ):
                    denied = Row(**row.__dict__)
                    denied.turn_type = "system"
                    denied.text = "permission decision: not executable (goose.executable=false)"
                    yield denied

    @staticmethod
    def _action_text(row: Row, data, tool_names: dict[str, str]) -> str:
        """The text of an `actionRequired` block, setting `row`'s tool join:
        a tool confirmation is a `permission request:`, its answer a
        `permission decision:` (message.rs:194-219 at aaif-goose/goose
        fb9e3c8); an elicitation keeps the generic `action required:` row."""
        kind = data.get("actionType") if isinstance(data, dict) else None
        if isinstance(data, dict) and kind == "toolConfirmation":
            row.tool_name = str(data.get("toolName") or "")
            row.tool_use_id = str(data.get("id") or "")
            return _join(
                "permission request: " + row.tool_name,
                str(data.get("prompt") or ""),
                compact_json(data.get("arguments") or {}),
            )
        if isinstance(data, dict) and kind == "toolConfirmationResponse":
            row.tool_use_id = str(data.get("id") or "")
            row.tool_name = tool_names.get(row.tool_use_id, "")
            return "permission decision: %s (toolConfirmationResponse)" % setting_value(
                data.get("permission") or "-"
            )
        return "action required: " + compact_json(data)

    # -- sessions.db ---------------------------------------------------------------------
    def _parse_db(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            row = self._row(artifact, 0)
            row.turn_type = "system"
            row.text = "parser: not a SQLite database"
            yield row
            return
        try:
            with open_copy(artifact.disk_path) as con:
                tables = table_names(con)
                if "messages" not in tables:
                    return
                sessions: dict[str, dict] = {}
                seen_model: dict[str, str] = {}
                seen_mode: dict[str, str] = {}
                if "sessions" in tables:
                    for s in con.execute(
                        "select rowid as _rowid, * from sessions order by created_at, rowid"
                    ):
                        s = dict(s)
                        cfg, reason, raw = _stored_json(s.get("model_config_json"), dict)
                        cfg_errors = []
                        if reason:
                            cfg_errors.append(
                                (
                                    s["_rowid"],
                                    "unparseable record %d (sessions.model_config_json: %s)"
                                    % (s["_rowid"], reason),
                                    raw,
                                )
                            )
                        model_name = str(
                            (cfg.get("model_name") if isinstance(cfg, dict) else "") or ""
                        )
                        s["_model"] = _model(s.get("provider_name") or "", model_name)
                        sid = str(s.get("id") or "")
                        sessions[sid] = s
                        row = self._row(
                            artifact,
                            s["_rowid"],
                            sid,
                            s.get("working_dir") or "",
                            s["_model"],
                            to_utc(s.get("created_at")),
                        )
                        row.turn_type = "system"
                        row.text = compact(
                            _join(
                                "session start",
                                s.get("name") or "",
                                s.get("description") or "",
                                "type=%s" % s["session_type"] if s.get("session_type") else "",
                                "parent=%s" % s["parent_session_id"]
                                if s.get("parent_session_id")
                                else "",
                                "schedule=%s" % s["schedule_id"] if s.get("schedule_id") else "",
                                "archived=%s" % s["archived_at"] if s.get("archived_at") else "",
                            ),
                        )
                        yield row
                        yield from error_rows(
                            self, artifact, cfg_errors, sid, s.get("working_dir") or ""
                        )
                        text = gateway_text(s)
                        if text:
                            yield self._system_copy(row, text)
                        text = track_change("model", seen_model, sid, model_name)
                        if text:
                            if s.get("provider_name"):
                                text += " provider=%s" % s["provider_name"]
                            yield self._system_copy(row, text)
                        text = track_change(
                            "permission mode", seen_mode, sid, str(s.get("goose_mode") or "")
                        )
                        if text:
                            yield self._system_copy(row, text)
                answered = self._answered(con)
                tool_names: dict[str, str] = {}
                for m in con.execute(
                    "select * from messages order by session_id, created_timestamp, id"
                ):
                    m = dict(m)
                    sid = str(m.get("session_id") or "")
                    s = sessions.get(sid, {})
                    project_path = s.get("working_dir") or ""
                    record = m.get("id") or 0
                    msg_errors: list = []
                    meta, reason, raw = _stored_json(m.get("metadata_json"), dict)
                    if reason:
                        msg_errors.append(
                            (
                                record,
                                "unparseable record %s (messages.metadata_json: %s)"
                                % (record, reason),
                                raw,
                            )
                        )
                    meta = meta if isinstance(meta, dict) else {}
                    inf = meta.get("inference") or {}
                    model = _model(
                        inf.get("provider") or "",
                        inf.get("resolvedModel") or inf.get("requestedModel") or "",
                    ) or s.get("_model", "")
                    base = self._row(
                        artifact,
                        record,
                        sid,
                        project_path,
                        model,
                        epoch(m.get("created_timestamp")) or to_utc(m.get("timestamp")),
                    )
                    resolved = str(inf.get("resolvedModel") or inf.get("requestedModel") or "")
                    text = track_change("model", seen_model, sid, resolved)
                    if text:
                        if inf.get("provider"):
                            text += " provider=%s" % inf["provider"]
                        requested = str(inf.get("requestedModel") or "")
                        if requested and requested != resolved:
                            text += " requested=%s" % requested
                        yield self._system_copy(base, text)
                    yield from error_rows(self, artifact, msg_errors, sid, project_path)
                    content, reason, raw = _stored_json(m.get("content_json"), list)
                    if content is None and not reason:
                        reason = "not a JSON array" if raw else "empty"
                    if reason:
                        yield from error_rows(
                            self,
                            artifact,
                            [
                                (
                                    record,
                                    "unparseable record %s (messages.content_json: %s)"
                                    % (record, reason),
                                    raw,
                                )
                            ],
                            sid,
                            project_path,
                        )
                        continue
                    yield from self._block_rows(
                        artifact,
                        base,
                        str(m.get("role") or ""),
                        content,
                        meta.get("userVisible", True) is not False,
                        tool_names,
                        opts,
                        answered.get(sid, set()),
                    )
        except sqlite3.DatabaseError as e:
            row = self._row(artifact, 0)
            row.turn_type = "system"
            row.text = "parser: SQLite error: %s" % e
            yield row

    @staticmethod
    def _answered(con) -> dict[str, set[str]]:
        """Session id to the tool request ids its `toolConfirmationResponse`
        blocks answer. A pre-scan: a `content_json` that does not decode is
        skipped here and reported by the full read of the same row."""
        answered: dict[str, set[str]] = {}
        for sid, stored in con.execute(
            "select session_id, content_json from messages"
            " where content_json like '%toolConfirmationResponse%'"
        ):
            content, _, _ = _stored_json(stored, list)
            for b in content if isinstance(content, list) else []:
                data = b.get("data") if isinstance(b, dict) else None
                if isinstance(data, dict) and data.get("actionType") == "toolConfirmationResponse":
                    answered.setdefault(str(sid or ""), set()).add(str(data.get("id") or ""))
        return answered

    # -- legacy sessions/<YYYYMMDD_HHMMSS>.jsonl ------------------------------------------
    def _parse_legacy(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        session_id = artifact.disk_path.name[: -len(".jsonl")]
        project_path = ""
        tool_names: dict[str, str] = {}
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            if "role" not in rec and "content" not in rec:
                session_id = str(rec.get("id") or session_id)
                project_path = str(rec.get("working_dir") or "")
                row = self._row(
                    artifact, n, session_id, project_path, ts=to_utc(rec.get("created_at"))
                )
                row.turn_type = "system"
                row.text = compact(
                    _join(
                        "session start (legacy)",
                        str(rec.get("description") or ""),
                        "%s messages" % rec["message_count"] if "message_count" in rec else "",
                    ),
                )
                yield row
                continue
            meta = rec.get("metadata")
            if not isinstance(meta, dict):
                meta = {}
            base = self._row(artifact, n, session_id, project_path, ts=epoch(rec.get("created")))
            yield from self._block_rows(
                artifact,
                base,
                str(rec.get("role") or ""),
                rec.get("content"),
                meta.get("userVisible", True) is not False,
                tool_names,
                opts,
            )
        yield from error_rows(self, artifact, errors, session_id, project_path)

    # -- logs/llm_request.*.jsonl ---------------------------------------------------------
    def _parse_llm_log(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        request: Row | None = None
        pending: list[Row] = []
        model = ""
        tool_names: dict[str, str] = {}
        # The message being assembled from streamed chunks: its first chunk's
        # row (time, line), its id, its role and its content blocks so far.
        current: tuple[Row, str, str, list] | None = None

        def flush() -> None:
            nonlocal current
            if current is not None:
                base, _, role, blocks = current
                pending.extend(
                    self._block_rows(artifact, base, role, blocks, True, tool_names, opts)
                )
                current = None

        for n, rec in iter_jsonl(artifact.disk_path, errors):
            if "input" in rec or "model_config" in rec:
                flush()
                cfg = rec.get("model_config") or {}
                inp = rec.get("input")
                if not isinstance(inp, dict):
                    inp = {}
                model = str(cfg.get("model_name") or inp.get("model") or "")
                msgs = inp.get("messages")
                if not isinstance(msgs, list):
                    msgs = []
                last_user = next(
                    (
                        text_of(m.get("content"))
                        for m in reversed(msgs)
                        if isinstance(m, dict) and m.get("role") == "user"
                    ),
                    "",
                )
                request = self._row(artifact, n, model=model)
                request.turn_type = "system"
                request.text = compact(
                    _join(
                        "llm request",
                        "%d messages" % len(msgs),
                        "last user: " + last_user if last_user else "",
                    ),
                )
                continue
            data = rec.get("data")
            if isinstance(data, dict) and "content" in data:
                content = data.get("content")
                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                if not isinstance(content, list) or not content:
                    continue  # a usage or metadata chunk adds no content
                mid = str(data.get("id") or "")
                if current is not None and mid and current[1] == mid:
                    merge_delta(current[3], content)
                    continue
                flush()
                base = self._row(artifact, n, model=model, ts=epoch(data.get("created")))
                if request is not None and not request.timestamp_utc:
                    request.timestamp_utc = base.timestamp_utc
                current = (base, mid, str(data.get("role") or "assistant"), list(content))
            elif rec.get("error"):
                flush()
                row = self._row(artifact, n, model=model)
                row.turn_type = "system"
                row.text = compact(
                    "llm error: "
                    + (
                        rec["error"]
                        if isinstance(rec["error"], str)
                        else compact_json(rec["error"])
                    ),
                )
                pending.append(row)
        flush()
        if request is not None:
            yield request
        yield from pending
        yield from error_rows(self, artifact, errors)

    # -- standing files: permission.yaml, roaming_trust.json, schedule.json -------------
    def _standing_row(self, artifact: Artifact, line: int, ts: str, text: str) -> Row:
        row = self._row(artifact, line, ts=ts)
        row.turn_type = "system"
        row.text = compact(text)
        return row

    def _read_json_file(self, artifact: Artifact) -> tuple[object, str]:
        """(document, error message) of a whole-file JSON store."""
        try:
            raw = artifact.disk_path.read_bytes().decode("utf-8", errors="replace")
        except OSError as e:
            return None, "unreadable %s (%s)" % (artifact.rel, e)
        try:
            return json.loads(raw), ""
        except ValueError as e:
            return None, "%s is not JSON (%s)" % (artifact.rel, e)

    def _parse_permission_yaml(self, artifact: Artifact) -> Iterator[Row]:
        errors: list = []
        ts = file_mtime(artifact)
        for n, category, level, tool in permission_entries(artifact.disk_path, errors):
            yield self._standing_row(
                artifact,
                n,
                ts,
                "permission setting: %s.%s=%s (from %s, file mtime)"
                % (category, level, tool, artifact.rel),
            )
        yield from error_rows(self, artifact, errors)

    def _parse_roaming_trust(self, artifact: Artifact) -> Iterator[Row]:
        doc, message = self._read_json_file(artifact)
        ts = file_mtime(artifact)
        if not message and not isinstance(doc, dict):
            message = "%s is not a JSON object" % artifact.rel
        if message or not isinstance(doc, dict):
            yield self._standing_row(artifact, 0, ts, "parser: " + message)
            return
        for key in ("allowed", "revoked_keys"):
            values = doc.get(key)
            for peer in values if isinstance(values, list) else []:
                yield self._standing_row(
                    artifact,
                    1,
                    ts,
                    "permission setting: roaming_trust.%s=%s (from %s, file mtime)"
                    % (key, setting_value(peer), artifact.rel),
                )

    def _parse_schedule(self, artifact: Artifact) -> Iterator[Row]:
        doc, message = self._read_json_file(artifact)
        ts = file_mtime(artifact)
        if not message and not isinstance(doc, list):
            message = "%s is not a JSON array" % artifact.rel
        if message or not isinstance(doc, list):
            yield self._standing_row(artifact, 0, ts, "parser: " + message)
            return
        errors: list = []
        for i, job in enumerate(doc, 1):
            if not isinstance(job, dict):
                errors.append(
                    (0, "unparseable record %d (not a JSON object)" % i, compact_json(job))
                )
                continue
            yield self._standing_row(artifact, 1, ts, schedule_text(job, artifact.rel))
        yield from error_rows(self, artifact, errors)

    # -- history.txt ------------------------------------------------------------------------
    def _parse_history(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        with open(artifact.disk_path, "rb") as fh:
            for n, raw in enumerate(fh, 1):
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line or (n == 1 and line.startswith("#V")):
                    continue
                row = self._row(artifact, n)
                row.turn_type = "user"
                row.text = compact(unescape_history(line))
                yield row
