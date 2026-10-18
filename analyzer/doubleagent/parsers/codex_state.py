"""Codex's SQLite projections of its rollouts, read by `RolloutParser` for
Codex and its forks (issue 122). Both files sit beside `sessions/` under the
Codex home (`state/src/sqlite.rs:34-39` at 3e23877; the Open Interpreter
fork at 2767e5f names the same files, `state/src/sqlite.rs:29-34`), and both
are secondary sources: Codex writes them from the rollout, which stays the
store of record, so the timeline drops a row of theirs that a rollout row
repeats (`dedup.py`) and keeps the rest. What they add is a thread whose
rollout is gone (deleted by hand, excluded by size, truncated): Codex's
own thread delete removes the rollout and the database rows together
(`thread-store/src/local/delete_thread.rs:66-92`), so a surviving row
without a rollout is a rollout removed outside Codex. Citations are in
`research/codex-cli.md` section 5.

* `state_5.sqlite` table `threads`, one row per thread
  (`state/migrations/0001_threads.sql`, later columns by migration): `id`
  (the thread id, which is the rollout's `session_meta.id` and so the
  rollout rows' `session_id`), `rollout_path`, `created_at` (epoch
  seconds) and `created_at_ms` (epoch ms, from migration 0025), `cwd`,
  `title`, `name` (a rename, 0041), `git_branch`, `model`, `archived`,
  `source` and `thread_source` (0030), `first_user_message` (0007), each
  read when the table has it. Per thread, in creation order:
  - a `system` row `thread record: <id> title=<title> rollout=<path>`,
    then ` name=<name>`, ` branch=<branch>`, ` model=<model>` and
    ` archived` when set (`model` is the thread's last turn's), at the
    thread's creation time, with `session_id` the thread id,
    `project_path` the `cwd` and `git_branch`; `model` stays empty on
    every row of both files, which record no model per event;
  - the first prompt, `first_user_message`, as a `user` row with **no
    timestamp**: the column records the prompt's text but not its time
    (`created_at` is the thread's creation, before the prompt was typed;
    `state/src/runtime/threads.rs:666-703`), so the row matches the
    rollout's prompt on text and session alone. Codex stores the message
    trimmed and with the `## My request for Codex:` prefix removed, or
    `[Image]` / `[Audio]` for a prompt with no text
    (`protocol/src/protocol.rs:145-150`, `2614-2635`); the trimmed text is
    what the rollout row carries, the placeholders match nothing. In a
    subagent's thread (`thread_source` `subagent`, or a `source` that
    names a subagent) the first prompt is the parent's task and is a
    `system` row `subagent task: <text>`, as the rollout reader writes it.
  `sandbox_policy` and `approval_mode` copy the rollout's `turn_context`
  policy, which the rollout reader's `permission mode:` rows carry, and
  `preview` repeats the first prompt (or a thread goal); none is read.
* `thread_history_1.sqlite`, the projection of a paginated rollout's
  `item_completed` and turn events (`app-server-protocol/src/protocol/
  thread_history_projection.rs:21-99`):
  - `thread_turns` (`thread_id`, `turn_id`, `rollout_ordinal`, `status`
    `inProgress`, `completed`, `interrupted` or `failed`, `started_at` and
    `completed_at` in epoch seconds, `duration_ms`, and
    `rollout_end_ordinal` from migration 0003): a `system` row
    `task_started turn=<id>` at `started_at`, and for a completed or failed
    turn `task_complete turn=<id> duration_ms=<n>` at `completed_at`, the
    texts the rollout reader gives the same events. An interrupted turn's
    abort reason is only in the rollout, so it gets no closing row.
  - `thread_items` (`thread_id`, `turn_id`, `item_id`, `rollout_ordinal`,
    `created_at_ms`, `started_at_ms` and `completed_at_ms` from migration
    0007, `item_json`): `item_json` is the app server's camelCase
    `ThreadItem` (`app-server-protocol/src/protocol/v2/item.rs:236-429`).
    `created_at_ms` is the item's start, or the rollout line's time when
    the event has none (`thread-store/src/local/thread_history.rs:431-438`);
    `started_at_ms` is when the item started and `completed_at_ms` when it
    completed (`core/src/session/mod.rs:2546-2601`). The Open Interpreter
    fork has no migration 0007, so there every time is `created_at_ms`.
    By `type`: `userMessage` (`content[]`, the `text` of each `text`
    input joined by newlines) is a `user` row, `agentMessage` (`text`) an
    `assistant` row and `reasoning` (`summary[]`, else `content[]`) a
    `thinking` row when `opts.include_thinking` is set, each at
    `completed_at_ms`, which is when the rollout records the response
    item the rollout reader takes them from. The other types are renamed
    to the rollout's turn-item form (`commandExecution` to
    `CommandExecution`, `aggregatedOutput` to `aggregated_output`, a
    `fileChange` `changes[].path` list to the paths, `sleep` to the
    `clock.sleep` extension) and rendered by `codex.item_rows`, so a tool
    item is a `tool_use` at `started_at_ms` and a `tool_result` at
    `completed_at_ms` joined on the item `id`, exactly as the rollout
    reader renders the item when no response item carries it.
    `hookPrompt` and `contextCompaction` are skipped: the rollout's
    user-role context message and `compacted` line carry them.
  Rows go thread by thread in rollout order, a turn's start before its
  items and its end after them. `session_id` is `thread_id`; the
  `project_path` and `git_branch` come from the `threads` row of the
  `state_5.sqlite` beside the file when there is one, else are empty, and
  in a subagent's thread the first `userMessage` is a `system` row
  `subagent task: <text>`, as above.

The time rule: the projection's rows pair with the rollout's within the
default 2 seconds, since both are stamped from the same events. Known
misses, where a projection row and its rollout row differ and the event
is shown twice: an `agentMessage` on Open Interpreter, stamped at its
start; a web search that took longer than 2 seconds when the rollout also
has its `web_search_call` response item. A tool call the model made
through a function call has different texts in the two (the rollout's
`tool_use` text is the call's arguments, the projection's the parsed
command, so `exec_command` calls and `apply_patch` patches differ), and
pairs on the `tool_use_id` both rows carry. A thread's first prompt is in
`history.jsonl`, in `first_user_message` and in the projection: one of
the three pairs with the rollout's prompt and `dedup.deduplicate`
collapses the other two onto it (`research/codex-cli.md` section 8). A
corrupt `item_json` is counted in one `system` row and the
other items are still read.

* `logs_<N>.sqlite` (`logs_2.sqlite` at 3e23877, `state/src/sqlite.rs:34`),
  Codex's own tracing log, is not a projection and not a secondary
  source: it holds the one local record that a thread left the host. Table
  `logs` (`state/logs_migrations/0002_logs_feedback_log_body.sql:3-16`):
  `ts` and `ts_nanos` (epoch seconds and nanoseconds), `level`, `target`,
  `feedback_log_body` (the event's message and then its fields as
  `key=value` pairs, `state/src/log_db.rs:436-474`; the first migration
  called the column `message`, read when `feedback_log_body` is absent)
  and `thread_id`. Only the row a `/feedback` report writes once it is sent
  to Sentry (an error-reporting service OpenAI runs for Codex feedback) is
  read: `target` `codex_feedback` and the message `feedback event uploaded
  to Sentry`, with the fields `thread_id`, `uploaded_attachments`,
  `attachments_failed` and `elapsed_ms` in any order
  (`feedback/src/lib.rs:749-755`). The other `codex_feedback` rows (an
  attachment that failed or was skipped) are not uploads and every other
  target is Codex's diagnostics; neither is an event. One `system` row
  `session synced: feedback report uploaded to Sentry, attachments
  <uploaded_attachments> failed <attachments_failed> (from logs_<N>.sqlite
  logs, ts)`, `-` for a field the body lacks, at `ts` plus `ts_nanos`, with
  `source_line` the row id, `session_id` the body's `thread_id` (else the
  column's), empty when it starts `no-active-thread-` (a report sent with
  no thread open), and `project_path` and `git_branch` from the thread's
  `threads` row in the `state_5.sqlite` beside it when there is one.
  `uploaded_attachments` 0 means the user declined to upload logs, so no
  rollout went with the report. Fixture only: no real install has shown
  the row.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterator
from typing import TYPE_CHECKING

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import Options
from .codex import item_rows

if TYPE_CHECKING:
    from .codex import RolloutParser

STATE_DB = "state_5.sqlite"
THREAD_HISTORY_DB = "thread_history_1.sqlite"

THREAD_COLUMNS = (
    "id",
    "rollout_path",
    "created_at",
    "created_at_ms",
    "cwd",
    "title",
    "name",
    "git_branch",
    "model",
    "archived",
    "source",
    "thread_source",
    "first_user_message",
)
TURN_COLUMNS = (
    "thread_id",
    "turn_id",
    "rollout_ordinal",
    "rollout_end_ordinal",
    "status",
    "started_at",
    "completed_at",
    "duration_ms",
)
ITEM_COLUMNS = (
    "thread_id",
    "turn_id",
    "item_id",
    "rollout_ordinal",
    "created_at_ms",
    "started_at_ms",
    "completed_at_ms",
    "item_json",
)
# camelCase `ThreadItem` types and keys to the rollout's turn-item form
# that `item_rows` reads.
TURN_ITEM_TYPES = {
    "commandExecution": "CommandExecution",
    "mcpToolCall": "McpToolCall",
    "dynamicToolCall": "DynamicToolCall",
    "fileChange": "FileChange",
    "functionCallOutput": "FunctionCallOutput",
    "webSearch": "WebSearch",
    "plan": "Plan",
    "subAgentActivity": "SubAgentActivity",
    "imageGeneration": "ImageGeneration",
}
TURN_ITEM_KEYS = {
    "aggregatedOutput": "aggregated_output",
    "exitCode": "exit_code",
    "contentItems": "content_items",
    "agentPath": "agent_path",
    "agentThreadId": "agent_thread_id",
}
SKIPPED_ITEMS = ("hookPrompt", "contextCompaction")
# `key=value` in a tracing body: a bare value or a quoted string.
LOG_FIELD_RX = re.compile(r'(?:^|\s)([A-Za-z_][A-Za-z0-9_.]*)=("(?:[^"\\]|\\.)*"|\S+)')


def _select(con: sqlite3.Connection, table: str, wanted: tuple[str, ...]) -> list[dict]:
    """Every row of `table` as a dict of the `wanted` columns it has (a
    column a migration has not added is absent) plus `_rowid`."""
    have = {r[1] for r in con.execute("pragma table_info(%s)" % table)}
    cols = [c for c in wanted if c in have]
    sql = "select rowid as _rowid, %s from %s order by rowid" % (", ".join(cols), table)
    return [dict(r) for r in con.execute(sql)]


def _created(thread: dict):
    ms = thread.get("created_at_ms")
    return ms if ms is not None else thread.get("created_at")


def read_threads(con: sqlite3.Connection) -> list[dict]:
    """The `threads` rows in creation order, or [] without the table."""
    if "threads" not in table_names(con):
        return []
    rows = _select(con, "threads", THREAD_COLUMNS)
    rows.sort(key=lambda t: (_created(t) or 0, str(t.get("id") or "")))
    return rows


def _is_subagent(thread: dict) -> bool:
    source = str(thread.get("source") or "")
    return thread.get("thread_source") == "subagent" or (
        source.startswith("{") and '"subagent"' in source
    )


def _thread_text(thread: dict) -> str:
    text = "thread record: %s title=%s rollout=%s" % (
        thread.get("id") or "",
        thread.get("title") or "",
        thread.get("rollout_path") or "",
    )
    for key, label in (("name", "name"), ("git_branch", "branch"), ("model", "model")):
        if thread.get(key):
            text += " %s=%s" % (label, thread[key])
    if thread.get("archived"):
        text += " archived"
    return text


def _stamp(parser: RolloutParser, artifact: Artifact, thread: dict | None, sid: str) -> Row:
    """A row of thread `sid` with the project and branch of its `threads`
    row when there is one. `model` stays empty: the row holds the model of
    the thread's last turn, not of each event."""
    row = parser.base_row(artifact)
    row.session_id = sid
    if thread:
        row.project_path = str(thread.get("cwd") or "")
        row.git_branch = str(thread.get("git_branch") or "")
    return row


def _problem(parser: RolloutParser, artifact: Artifact, text: str) -> Row:
    row = parser.base_row(artifact)
    row.turn_type = "system"
    row.text = text
    return row


def parse_state(parser: RolloutParser, artifact: Artifact, opts: Options) -> Iterator[Row]:
    """Rows of `state_5.sqlite`: a thread record and the first prompt per thread."""
    if not is_sqlite(artifact.disk_path):
        yield _problem(parser, artifact, "parser: not a SQLite database")
        return
    try:
        with open_copy(artifact.disk_path) as con:
            threads = read_threads(con)
    except sqlite3.DatabaseError as e:
        yield _problem(parser, artifact, "parser: SQLite error: %s" % e)
        return
    for thread in threads:
        sid = str(thread.get("id") or "")
        row = _stamp(parser, artifact, thread, sid)
        row.source_line = int(thread["_rowid"])
        row.turn_type = "system"
        row.timestamp_utc = to_utc(_created(thread))
        row.text = compact(_thread_text(thread))
        yield row
        first = compact(thread.get("first_user_message"))
        if not first:
            continue
        prompt = _stamp(parser, artifact, thread, sid)
        prompt.source_line = row.source_line
        if _is_subagent(thread):
            prompt.turn_type = "system"
            prompt.text = "subagent task: " + first
        else:
            prompt.turn_type = "user"
            prompt.text = first
        yield prompt


def _sibling_threads(artifact: Artifact) -> dict[str, dict]:
    """The `threads` rows of the `state_5.sqlite` beside `artifact`, by id;
    {} when there is none or it cannot be read."""
    path = artifact.disk_path.parent / STATE_DB
    if not is_sqlite(path):
        return {}
    try:
        with open_copy(path) as con:
            return {str(t.get("id") or ""): t for t in read_threads(con)}
    except sqlite3.DatabaseError:
        return {}


def to_turn_item(item: dict) -> dict:
    """A camelCase `ThreadItem` in the rollout's turn-item form."""
    itype = str(item.get("type") or "")
    if itype == "sleep":
        return {"type": "Extension", "kind": "clock.sleep", "durationMs": item.get("durationMs")}
    out = {TURN_ITEM_KEYS.get(k, k): v for k, v in item.items()}
    out["type"] = TURN_ITEM_TYPES.get(itype, itype)
    changes = item.get("changes")
    if itype == "fileChange" and isinstance(changes, list):
        out["changes"] = {
            str(c.get("path")): c for c in changes if isinstance(c, dict) and c.get("path")
        }
    return out


def _joined(values, key: str = "") -> str:
    """Strings of a list, or the `key` of its dict members, joined by newlines."""
    if not isinstance(values, list):
        return ""
    parts = []
    for v in values:
        if key and isinstance(v, dict) and v.get("type") == "text":
            v = v.get(key)
        if isinstance(v, str) and v:
            parts.append(v)
    return "\n".join(parts)


def thread_item_rows(item: dict, rec: dict) -> list[tuple[str, object, dict, str]]:
    """Rows of one `thread_items` row (`rec`) whose `item_json` is `item`,
    as (turn_type, timestamp, {tool_name, tool_use_id}, text)."""
    itype = str(item.get("type") or "")
    created = rec.get("created_at_ms")
    t0 = rec.get("started_at_ms") if rec.get("started_at_ms") is not None else created
    t1 = rec.get("completed_at_ms") if rec.get("completed_at_ms") is not None else created
    if itype == "userMessage":
        text = _joined(item.get("content"), "text")
        return [("user", t1, {}, text)] if text else []
    if itype == "agentMessage":
        text = str(item.get("text") or "")
        return [("assistant", t1, {}, text)] if text else []
    if itype == "reasoning":
        text = _joined(item.get("summary")) or _joined(item.get("content"))
        return [("thinking", t1, {}, text)] if text else []
    if itype in SKIPPED_ITEMS:
        return []
    return item_rows(to_turn_item(item), {"started_at_ms": t0, "completed_at_ms": t1})


def _events(turns: list[dict], items: list[dict]) -> list[tuple]:
    """Turn starts, items and turn ends in rollout order, thread by thread,
    as sort keys ending in (kind, record)."""
    last_item: dict = {}
    for it in items:
        key = (it.get("thread_id"), it.get("turn_id"))
        last_item[key] = max(last_item.get(key, -1), it.get("rollout_ordinal") or 0)
    events = []
    for t in turns:
        start = t.get("rollout_ordinal") or 0
        end = t.get("rollout_end_ordinal")
        if end is None:
            end = max(start, last_item.get((t.get("thread_id"), t.get("turn_id")), start))
        events.append((str(t.get("thread_id") or ""), start, 0, t["_rowid"], "start", t))
        events.append((str(t.get("thread_id") or ""), end, 2, t["_rowid"], "end", t))
    for it in items:
        ordinal = it.get("rollout_ordinal") or 0
        events.append((str(it.get("thread_id") or ""), ordinal, 1, it["_rowid"], "item", it))
    events.sort(key=lambda e: e[:4])
    return events


def _turn_row(kind: str, turn: dict) -> tuple[object, str] | None:
    """(timestamp, text) of a turn's start or end row, or None."""
    tid = turn.get("turn_id") or ""
    if kind == "start":
        return turn.get("started_at"), "task_started turn=%s" % tid
    if turn.get("status") in ("completed", "failed"):
        text = "task_complete turn=%s duration_ms=%s" % (tid, turn.get("duration_ms") or "")
        return turn.get("completed_at"), text
    return None


def parse_thread_history(parser: RolloutParser, artifact: Artifact, opts: Options) -> Iterator[Row]:
    """Rows of `thread_history_1.sqlite`: turns and their items."""
    if not is_sqlite(artifact.disk_path):
        yield _problem(parser, artifact, "parser: not a SQLite database")
        return
    try:
        with open_copy(artifact.disk_path) as con:
            tables = table_names(con)
            turns = _select(con, "thread_turns", TURN_COLUMNS) if "thread_turns" in tables else []
            items = _select(con, "thread_items", ITEM_COLUMNS) if "thread_items" in tables else []
    except sqlite3.DatabaseError as e:
        yield _problem(parser, artifact, "parser: SQLite error: %s" % e)
        return
    threads = _sibling_threads(artifact)
    bad: list[int] = []
    tasked: set = set()  # subagent threads whose first prompt was seen
    for sid, _ordinal, _seq, rowid, kind, rec in _events(turns, items):
        thread = threads.get(sid)
        if kind != "item":
            turn = _turn_row(kind, rec)
            if turn is None:
                continue
            row = _stamp(parser, artifact, thread, sid)
            row.source_line = int(rowid)
            row.turn_type = "system"
            row.timestamp_utc = to_utc(turn[0])
            row.text = compact(turn[1])
            yield row
            continue
        try:
            item = json.loads(rec.get("item_json") or "")
        except (TypeError, ValueError):
            bad.append(int(rowid))
            continue
        if not isinstance(item, dict):
            bad.append(int(rowid))
            continue
        for turn_type, ts, fields, text in thread_item_rows(item, rec):
            if turn_type == "thinking" and not opts.include_thinking:
                continue
            row = _stamp(parser, artifact, thread, sid)
            row.source_line = int(rowid)
            row.turn_type = turn_type
            row.timestamp_utc = to_utc(ts)
            row.tool_name = fields.get("tool_name", "")
            row.tool_use_id = fields.get("tool_use_id", "")
            if turn_type == "user" and thread and _is_subagent(thread) and sid not in tasked:
                row.turn_type = "system"
                text = "subagent task: " + text
            if turn_type == "user":
                tasked.add(sid)
            row.text = compact(text)
            yield row
    if bad:
        row = _problem(parser, artifact, "")
        row.source_line = bad[0]
        row.text = "parser: %d thread_items row(s) with unreadable item_json, first at rowid %d" % (
            len(bad),
            bad[0],
        )
        yield row


LOGS_TARGET = "codex_feedback"
LOGS_MESSAGE = "feedback event uploaded to Sentry"
NO_THREAD_PREFIX = "no-active-thread-"


def _log_fields(body: str) -> dict[str, str]:
    """The `key=value` fields of a `feedback_log_body`, quotes removed from a
    value tracing recorded as a quoted string."""
    out: dict[str, str] = {}
    for m in LOG_FIELD_RX.finditer(body):
        value = m.group(2)
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        out[m.group(1)] = value
    return out


def _feedback_rows(con: sqlite3.Connection) -> list[dict]:
    """The `logs` rows of sent `/feedback` reports, in id order; [] without
    the table."""
    if "logs" not in table_names(con):
        return []
    have = {r[1] for r in con.execute("pragma table_info(logs)")}
    body = "feedback_log_body" if "feedback_log_body" in have else "message"
    if body not in have or "target" not in have:
        return []
    cols = ", ".join(
        "%s as %s" % (c if c in have else "null", c) for c in ("ts", "ts_nanos", "thread_id")
    )
    sql = (
        "select rowid as _rowid, %s, %s as body from logs where target = ? and instr(%s, ?) > 0"
        " order by rowid" % (cols, body, body)
    )
    return [dict(r) for r in con.execute(sql, (LOGS_TARGET, LOGS_MESSAGE))]


def _log_time(rec: dict) -> str:
    ts = rec.get("ts")
    if not isinstance(ts, (int, float)) or isinstance(ts, bool):
        return ""
    nanos = rec.get("ts_nanos")
    if isinstance(nanos, int) and not isinstance(nanos, bool) and 0 <= nanos < 1_000_000_000:
        return to_utc(ts + nanos / 1e9)
    return to_utc(ts)


def parse_logs(parser: RolloutParser, artifact: Artifact) -> Iterator[Row]:
    """Rows of `logs_<N>.sqlite`: one `session synced:` row per sent
    `/feedback` report."""
    if not is_sqlite(artifact.disk_path):
        yield _problem(parser, artifact, "parser: not a SQLite database")
        return
    try:
        with open_copy(artifact.disk_path) as con:
            reports = _feedback_rows(con)
    except sqlite3.DatabaseError as e:
        yield _problem(parser, artifact, "parser: SQLite error: %s" % e)
        return
    threads = _sibling_threads(artifact) if reports else {}
    for rec in reports:
        fields = _log_fields(str(rec.get("body") or ""))
        sid = fields.get("thread_id") or str(rec.get("thread_id") or "")
        if sid.startswith(NO_THREAD_PREFIX):
            sid = ""
        row = _stamp(parser, artifact, threads.get(sid) if sid else None, sid)
        row.source_line = int(rec["_rowid"])
        row.turn_type = "system"
        row.timestamp_utc = _log_time(rec)
        row.text = (
            "session synced: feedback report uploaded to Sentry, attachments %s failed %s"
            " (from %s logs, ts)"
            % (
                fields.get("uploaded_attachments") or "-",
                fields.get("attachments_failed") or "-",
                artifact.disk_path.name,
            )
        )
        yield row
