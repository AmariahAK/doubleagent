"""Continue (IDE extensions and the `cn` CLI) sessions.

The module is not called `continue.py` because `continue` is a Python
keyword. Validated against source, continuedev/continue at 5522c6f
(`core/index.d.ts`, `core/util/history.ts`, `core/data/log.ts`,
`packages/config-yaml/src/schemas/data/`), with a synthetic fixture; see
`research/continue.md`. Files, relative to the home directory:

* `.continue/sessions/<sessionId>.json`: one pretty-printed JSON session,
  keys `sessionId`, `title`, `workspaceDirectory`, `history[]`, `mode`,
  `chatModelTitle`, `usage` (`promptTokens`, `completionTokens`,
  `totalCost`). Each `history[]` item has `message` (`role` user, assistant,
  thinking, system or tool; `content` a string or a list of
  `{type:"text",text}` / `{type:"imageUrl",imageUrl:{url}}` parts;
  assistant `toolCalls[]` with `id` and `function.name`/`function.arguments`;
  tool `toolCallId`), `toolCallStates[]` (`toolCallId`, `toolCall`,
  `status`, `output[].content`), `promptLogs[].modelTitle` and `reasoning`
  (`text`, `startAt` in epoch milliseconds).
* `.continue/sessions/sessions.json`: the index, an array of
  `{sessionId, title, dateCreated, workspaceDirectory, messageCount}` with
  `dateCreated` a millisecond epoch as a string. It is read for the
  timestamp and yields rows only for what it loses (issue 170): a file
  that cannot be read is one `parser: unreadable session index: <reason>`
  row, a file that is not a JSON array one `parser: not a JSON array`
  row, an element that does not decode (the file cut mid-write) a
  `parser: unparseable record <N> (<reason>): <the text from that
  element to the end of the file>` row, an array with no closing bracket
  `parser: array cut off after record <N>`, and an element that is not
  an object with a `sessionId` (or the pre-1.0 `session_id` the
  extension filters out) `parser: unparseable record <N> (not an object
  with a sessionId): <the element as JSON>`; data after the array is
  `parser: unparseable data after the JSON array`. The entries before a cut
  still give their sessions a time; a session the index lost has an
  empty `timestamp_utc`, and the row says why.
* `.continue/dev_data/<schema>/chatInteraction.jsonl` (and the unversioned
  legacy `dev_data/chatInteraction.jsonl`): `timestamp` ISO 8601,
  `sessionId`, `prompt`, `completion`, `modelTitle`, `modelName`.
* `.continue/dev_data/<schema>/toolUsage.jsonl`: `timestamp`,
  `toolCallId`, `functionName`, `functionParams`, `toolCallArgs`,
  `accepted`, `succeeded`, `output[].content`.

Session files carry no per-message timestamp: every row of a session
inherits the session's `dateCreated` from `sessions.json` (empty when the
index is missing or lacks the session), except thinking rows from
`reasoning.startAt`. Order within a session is the order of `history[]`,
and `source_line` is the 1-based position in `history[]` (0 for the session
row). The `dev_data` events do carry real timestamps; chatInteraction rows
are joined to the session's `workspaceDirectory` through `sessions.json`,
and toolUsage rows join the session's tool calls on `tool_use_id` but carry
no session id of their own. `logs/prompt.log` has no date or session id and
is not parsed. A truncated session file yields the turns decoded before the
cut plus one `system` row.

Model rows: `model: <chatModelTitle>` follows the session row (same time,
`source_line` 0), and an item whose `promptLogs[].modelTitle` differs from
the model before it yields `model: <old> -> <new>` ahead of the item's
rows, with the item's `source_line`. The format has no switch record, so a
change is only seen as a different `modelTitle` between items, and
`chatModelTitle` is a single value per session file. `dev_data` events
fill the `model` column only. `permissions.yaml` (the `cn` CLI's tool
policy) is not read: its shape is not recorded in the research.

Per-call decisions: each `toolUsage.jsonl` record that has `accepted`
yields `permission decision: accepted=<accepted>` after its `tool_result`
row (which keeps its own `accepted=` text), with the record's time,
`tool_use_id` and `tool_name`. A `toolCallStates[]` entry whose `status`
is `canceled` yields `permission decision: canceled` with the call's
`tool_use_id` and `tool_name`, after the state's `tool_result` row when
there is one, at the session time.

Agent metadata posts: `.continue/logs/cn.log` and the files winston (the
`cn` CLI's logging library) rotates it to at 10 MB, `cn1.log`, `cn2.log`
and so on, five kept (`extensions/cli/src/util/logger.ts:102-115`; the
names from winston 3.17.0's `File` transport, `_getFile`). Each line is
`YYYY-MM-DD HH:mm:ss.SSS [<8 hex>] [<level>]: <message>`, then the call's
extra fields as one JSON object (`logger.ts:74-95`); the eight hex digits
are a random id per process, not a session id. Only two kinds of line are
events, both written when the hidden `cn serve --id <agentId>` mode talks
to Continue's agent API (`extensions/cli/src/util/metadata.ts:125-181`,
`extensions/cli/src/services/StorageSyncService.ts:85-90`); every other
line is the CLI's diagnostics, not an event, and no line of the file can
be a bad line:

* `[metadata] POST <url> {"agentId":"<id>","metadataKeys":[...]}` yields
  `agent metadata posted: agent <agentId> keys <metadataKeys joined by ,>
  <status> (from logs/<file>, log line time, host-local)`, where
  `<status>` is `Success`, `Unexpected response`, `Auth required`,
  `Failed` or `Error` from the first later `[metadata]` result line of the
  same process for the same URL, and `-` when there is none. The
  `[metadata] Request body` line between them carries the posted fields
  (the last reply's text among them) and is never put in a row.
* A line containing `Storage sync requested but no Continue API key`
  yields `storage upload requested, skipped (from logs/<file>, log line
  time, host-local)`: `cn serve` asked for snapshot uploads and the CLI
  skipped them.

Both are `system` rows with an empty `session_id`, since the log names no
session, and `source_line` the line number. The log time is host-local
with no zone, and the collection does not record the host's zone, so it
is emitted as if it were UTC, as the aider parser does; correct it by the
host's offset. Neither row is a session sync, so `records_sync` stays
False. Fixture only: no real install has shown either line.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator

from ..inputs import Artifact, error_reason
from ..model import Row, compact
from ..timeutil import to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    iter_jsonl,
    line_text,
    setting_value,
    text_of,
    track_change,
)
from .cline_legacy import iter_array_at

SESSION_RX = re.compile(r"^(?:.*/)?\.continue/sessions/([^/]+)\.json$")
DEV_DATA_RX = re.compile(
    r"^(?:.*/)?\.continue/dev_data/(?:[^/]+/)?(chatInteraction|toolUsage)\.jsonl$"
)
INDEX_NAME = "sessions.json"
CN_LOG_RX = re.compile(r"^\.continue/logs/cn[0-9]*\.log$")
LOG_LINE_RX = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[([0-9a-fA-F]{8})\] \[[A-Za-z]+\]: (.*)$"
)
METADATA_POST_RX = re.compile(r"^\[metadata\] POST (\S+)(?: (\{.*\}))?$")
# `[metadata]` result lines (extensions/cli/src/util/metadata.ts:144-180):
# the status word, then the URL, which ends `/metadata`, followed on a
# `Failed` line by the response as JSON.
METADATA_RESULT_RX = re.compile(
    r"^\[metadata\] (Success|Unexpected response|Auth required|Failed|Error)\b.* "
    r"(\S+/metadata)(?: \{.*\})?$"
)
AGENT_URL_RX = re.compile(r"/agents/([^/]+)/metadata$")
STORAGE_SKIPPED = "Storage sync requested but no Continue API key"
HEADER_KEYS = ("sessionId", "title", "workspaceDirectory", "mode", "chatModelTitle")


def read_index(path) -> tuple[dict[str, dict], list]:
    """sessionId -> entry for the `sessions.json` index at `path`, and the
    errors for `error_rows`: an unreadable file, a file that is not a JSON
    array, an element that does not decode (with the text from it to the
    end of the file, the entries before it kept) and an element that is
    not an object with a `sessionId`. Entries keyed `session_id` are a
    pre-1.0 format the extension itself filters out, so they are skipped
    without a row. An absent file or a symlink is an empty index with no
    error, since the collector does not materialise symlinks. Shared with
    the PearAI parser, whose fork keeps the same index."""
    out: dict[str, dict] = {}
    errors: list = []
    try:
        if not path.is_file() or path.is_symlink():
            return out, errors
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
    except OSError as e:
        errors.append((0, "unreadable session index: %s" % error_reason(e), ""))
        return out, errors
    if text.startswith("\ufeff"):
        text = text[1:]
    end: list = []
    count = 0
    for n, e in iter_array_at(text, 0, errors, end):
        count = n
        if isinstance(e, dict) and e.get("sessionId"):
            out[str(e["sessionId"])] = e
        elif not (isinstance(e, dict) and e.get("session_id")):
            errors.append(
                (n, "unparseable record %d (not an object with a sessionId)" % n, compact_json(e))
            )
    if end and text[end[0] :].strip(" \t\r\n"):
        errors.append((count + 1, "unparseable data after the JSON array", ""))
    return out, errors


def message_text(content) -> str:
    """Flatten a ChatMessage content: image parts become `[image]`."""
    if isinstance(content, list):
        content = [
            {"type": "text", "text": "[image]"}
            if isinstance(p, dict) and p.get("type") == "imageUrl"
            else p
            for p in content
        ]
    return text_of(content)


def output_text(output) -> str:
    """Text of a ContextItem[] tool output."""
    if not isinstance(output, list):
        return text_of(output)
    parts = []
    for item in output:
        if isinstance(item, dict):
            c = item.get("content")
            parts.append(
                c
                if isinstance(c, str)
                else compact_json(c)
                if c is not None
                else str(item.get("name") or "")
            )
        else:
            parts.append(str(item))
    return "\n".join(p for p in parts if p)


def load_session(text: str) -> tuple[dict, str]:
    """Parse a session file. On failure, recover the header keys and every
    `history[]` item that decodes before the damage, and say what went wrong."""
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj, ""
        return {}, "session file is not a JSON object"
    except ValueError as e:
        first_error = str(e)
    dec = json.JSONDecoder()
    start = text.find("{")
    if start >= 0:
        try:
            obj, end = dec.raw_decode(text, start)
            if isinstance(obj, dict):
                return obj, "trailing data after the session object at offset %d" % end
        except ValueError:
            pass
    out: dict = {}
    for key in HEADER_KEYS:
        m = re.search(r'"%s"\s*:\s*("(?:[^"\\]|\\.)*")' % key, text)
        if m:
            try:
                out[key] = json.loads(m.group(1))
            except ValueError:
                pass
    history: list[dict] = []
    m = re.search(r'"history"\s*:\s*\[', text)
    if m:
        pos = m.end()
        while True:
            while pos < len(text) and text[pos] in " \t\r\n,":
                pos += 1
            if pos >= len(text) or text[pos] == "]":
                break
            try:
                item, pos = dec.raw_decode(text, pos)
            except ValueError:
                break
            if isinstance(item, dict):
                history.append(item)
    out["history"] = history
    return out, "session file did not parse (%s); recovered %d history item(s)" % (
        first_error,
        len(history),
    )


class ContinueParser(Parser):
    agent = "continue"
    name = "continue"

    def __init__(self) -> None:
        self._index_cache: dict[str, tuple[dict[str, dict], list]] = {}

    def wants(self, artifact: Artifact) -> bool:
        # sessions.json too, for the rows that say what the index lost
        return bool(
            SESSION_RX.match(artifact.rel)
            or DEV_DATA_RX.match(artifact.rel)
            or CN_LOG_RX.match(artifact.rel)
        )

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if CN_LOG_RX.match(artifact.rel):
            yield from self._parse_cn_log(artifact)
            return
        m = DEV_DATA_RX.match(artifact.rel)
        if m and m.group(1) == "chatInteraction":
            yield from self._parse_chat_interaction(artifact, opts)
        elif m:
            yield from self._parse_tool_usage(artifact, opts)
        elif artifact.disk_path.name == INDEX_NAME:
            yield from error_rows(self, artifact, self.index_errors(artifact.disk_path))
        else:
            yield from self._parse_session(artifact, opts)

    # ---- sessions.json --------------------------------------------------------

    def _read_index(self, path) -> tuple[dict[str, dict], list]:
        """`read_index` of `path`, cached per file for the session files
        that share it."""
        key = str(path)
        if key not in self._index_cache:
            self._index_cache[key] = read_index(path)
        return self._index_cache[key]

    def _index(self, sessions_dir) -> dict[str, dict]:
        """sessionId -> sessions.json entry for the index beside the session
        files; empty when it is absent or unreadable. What it lost is
        reported once, by `index_errors` on the index's own artifact."""
        return self._read_index(sessions_dir / INDEX_NAME)[0]

    def index_errors(self, path) -> list:
        """The errors `read_index` found in the index at `path`, a fresh
        list each call."""
        return list(self._read_index(path)[1])

    # ---- session files --------------------------------------------------------

    def _parse_session(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        try:
            raw = artifact.disk_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            row = self.base_row(artifact)
            row.turn_type = "system"
            row.text = "parser: unreadable session file: %s" % error_reason(e)
            yield row
            return
        sess, problem = load_session(raw)
        session_id = sess.get("sessionId")
        if not session_id:
            m = SESSION_RX.match(artifact.rel)
            assert m is not None  # wants() accepted only matching paths
            session_id = m.group(1)
        session_id = str(session_id)
        entry = self._index(artifact.disk_path.parent).get(session_id, {})
        ts = to_utc(entry.get("dateCreated"))
        project = str(sess.get("workspaceDirectory") or entry.get("workspaceDirectory") or "")
        session_model = str(sess.get("chatModelTitle") or "")
        history = sess.get("history")
        if not isinstance(history, list):
            history = []

        def base(n: int, model: str = "") -> Row:
            row = self.base_row(artifact)
            row.source_line = n
            row.timestamp_utc = ts
            row.session_id = session_id
            row.project_path = project
            row.model = model
            return row

        row = base(0, session_model)
        row.turn_type = "system"
        usage = sess.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        bits = ["session start: %s" % (sess.get("title") or entry.get("title") or "")]
        if sess.get("mode"):
            bits.append("mode=%s" % sess["mode"])
        bits.append("items=%d" % len(history))
        for k in ("promptTokens", "completionTokens", "totalCost"):
            if usage.get(k) is not None:
                bits.append("%s=%s" % (k, usage[k]))
        if not ts:
            bits.append("dateCreated unknown")
        row.text = compact(" ".join(bits))
        yield row
        models: dict = {}
        change = track_change("model", models, session_id, session_model)
        if change:
            row = base(0, session_model)
            row.turn_type = "system"
            row.text = change
            yield row

        # Tool results normally arrive as a later `tool` message; a call that
        # never got one (canceled, errored) keeps its output in toolCallStates.
        answered = set()
        for item in history:
            msg = item.get("message") if isinstance(item, dict) else None
            if isinstance(msg, dict) and msg.get("role") == "tool" and msg.get("toolCallId"):
                answered.add(str(msg["toolCallId"]))
        names: dict[str, str] = {}

        for i, item in enumerate(history, 1):
            if not isinstance(item, dict):
                continue
            msg = item.get("message")
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            model = session_model
            logs = item.get("promptLogs")
            if isinstance(logs, list):
                for pl in logs:
                    if isinstance(pl, dict) and pl.get("modelTitle"):
                        model = str(pl["modelTitle"])
                        change = track_change("model", models, session_id, model)
                        if change:
                            row = base(i, model)
                            row.turn_type = "system"
                            row.text = change
                            yield row
            reasoning = item.get("reasoning")
            if opts.include_thinking and isinstance(reasoning, dict) and reasoning.get("text"):
                row = base(i, model)
                row.turn_type = "thinking"
                row.timestamp_utc = to_utc(reasoning.get("startAt")) or ts
                yield self._fill(row, reasoning.get("text"), opts)
            text = message_text(msg.get("content"))
            if role == "user":
                if text:
                    row = base(i)
                    row.turn_type = "user"
                    yield self._fill(row, text, opts)
            elif role == "assistant":
                if text:
                    row = base(i, model)
                    row.turn_type = "assistant"
                    yield self._fill(row, text, opts)
                calls = msg.get("toolCalls")
                states = item.get("toolCallStates")
                states = (
                    [s for s in states if isinstance(s, dict)] if isinstance(states, list) else []
                )
                if not isinstance(calls, list) or not calls:
                    calls = [
                        s.get("toolCall") for s in states if isinstance(s.get("toolCall"), dict)
                    ]
                for call in calls:
                    if not isinstance(call, dict):
                        continue
                    fn = call.get("function")
                    if not isinstance(fn, dict):
                        fn = {}
                    call_id = str(call.get("id") or "")
                    name = str(fn.get("name") or "")
                    names[call_id] = name
                    args = fn.get("arguments")
                    row = base(i, model)
                    row.turn_type = "tool_use"
                    row.tool_name = name
                    row.tool_use_id = call_id
                    yield self._fill(
                        row,
                        args
                        if isinstance(args, str)
                        else compact_json(args)
                        if args is not None
                        else "",
                        opts,
                    )
                for st in states:
                    call_id = str(st.get("toolCallId") or "")
                    if not call_id:
                        continue
                    out = output_text(st.get("output"))
                    status = str(st.get("status") or "")
                    if call_id not in answered and (
                        out or status not in ("", "done", "generated", "generating", "calling")
                    ):
                        row = base(i, model)
                        row.turn_type = "tool_result"
                        row.tool_use_id = call_id
                        row.tool_name = names.get(call_id, "")
                        yield self._fill(
                            row,
                            "[%s] %s" % (status, out) if status and status != "done" else out,
                            opts,
                        )
                    if status == "canceled":
                        row = base(i, model)
                        row.turn_type = "system"
                        row.tool_use_id = call_id
                        row.tool_name = names.get(call_id, "")
                        row.text = "permission decision: canceled"
                        yield row
            elif role == "thinking":
                if opts.include_thinking and text:
                    row = base(i, model)
                    row.turn_type = "thinking"
                    yield self._fill(row, text, opts)
            elif role == "tool":
                call_id = str(msg.get("toolCallId") or "")
                row = base(i)
                row.turn_type = "tool_result"
                row.tool_use_id = call_id
                row.tool_name = names.get(call_id, "")
                yield self._fill(row, text, opts)
            elif text:
                row = base(i)
                row.turn_type = "system"
                yield self._fill(
                    row, "%s: %s" % (role or "unknown", text) if role != "system" else text, opts
                )

        if problem:
            row = base(0)
            row.turn_type = "system"
            row.text = "parser: " + problem
            yield row

    # ---- dev_data -------------------------------------------------------------

    def _dev_index(self, artifact: Artifact) -> dict[str, dict]:
        # .continue/dev_data/<schema>/x.jsonl or .continue/dev_data/x.jsonl
        d = artifact.disk_path.parent
        base = d.parent if d.parent.name == ".continue" else d.parent.parent
        return self._index(base / "sessions")

    def _parse_chat_interaction(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        index = self._dev_index(artifact)
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            sid = str(rec.get("sessionId") or "")
            entry = index.get(sid, {})
            for turn, key in (("user", "prompt"), ("assistant", "completion")):
                text = rec.get(key)
                if not text:
                    continue
                row = self.base_row(artifact)
                row.source_line = n
                row.timestamp_utc = to_utc(rec.get("timestamp"))
                row.session_id = sid
                row.project_path = str(entry.get("workspaceDirectory") or "")
                row.turn_type = turn
                if turn == "assistant":
                    row.model = str(rec.get("modelTitle") or rec.get("modelName") or "")
                yield self._fill(row, text if isinstance(text, str) else compact_json(text), opts)
        yield from error_rows(self, artifact, errors)

    def _parse_tool_usage(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            ts = to_utc(rec.get("timestamp"))
            call_id = str(rec.get("toolCallId") or "")
            name = str(rec.get("functionName") or "")
            row = self.base_row(artifact)
            row.source_line = n
            row.timestamp_utc = ts
            row.turn_type = "tool_use"
            row.tool_name = name
            row.tool_use_id = call_id
            args = rec.get("toolCallArgs")
            if not args and rec.get("functionParams") is not None:
                args = compact_json(rec.get("functionParams"))
            yield self._fill(
                row,
                args if isinstance(args, str) else compact_json(args) if args is not None else "",
                opts,
            )
            row = self.base_row(artifact)
            row.source_line = n
            row.timestamp_utc = ts
            row.turn_type = "tool_result"
            row.tool_name = name
            row.tool_use_id = call_id
            yield self._fill(
                row,
                "accepted=%s succeeded=%s %s"
                % (
                    compact_json(rec.get("accepted")),
                    compact_json(rec.get("succeeded")),
                    output_text(rec.get("output")),
                ),
                opts,
            )
            if "accepted" in rec:
                row = self.base_row(artifact)
                row.source_line = n
                row.timestamp_utc = ts
                row.turn_type = "system"
                row.tool_name = name
                row.tool_use_id = call_id
                row.text = "permission decision: accepted=%s" % setting_value(rec["accepted"])
                yield row
        yield from error_rows(self, artifact, errors)

    # ---- logs/cn.log ---------------------------------------------------------

    def _parse_cn_log(self, artifact: Artifact) -> Iterator[Row]:
        """`agent metadata posted:` and `storage upload requested, skipped`
        rows of a `cn` CLI log, in line order."""
        source = "logs/" + artifact.disk_path.name
        # Each post as [process id, url, fields JSON, status, row]; a post
        # waits in `pending` for the result line of its process and URL.
        posts: list[list] = []
        pending: list[list] = []
        rows: list[Row] = []
        try:
            with open(artifact.disk_path, "rb") as fh:
                for n, raw in enumerate(fh, 1):
                    m = LOG_LINE_RX.match(line_text(raw))
                    if not m:
                        continue
                    when, pid, message = m.groups()
                    if STORAGE_SKIPPED in message:
                        text = "storage upload requested, skipped (from %s, log line time, %s)"
                        rows.append(self._log_row(artifact, n, when, text % (source, "host-local")))
                        continue
                    post = METADATA_POST_RX.match(message)
                    if post:
                        row = self._log_row(artifact, n, when, "")
                        posts.append([pid, post.group(1), post.group(2), "-", row])
                        pending.append(posts[-1])
                        rows.append(row)
                        continue
                    result = METADATA_RESULT_RX.match(message)
                    if result:
                        self._settle(pending, pid, result.group(2), result.group(1))
        except OSError as e:
            yield from error_rows(self, artifact, [(0, "unreadable (%s)" % error_reason(e), "")])
            return
        for _pid, url, fields, status, row in posts:
            row.text = self._post_text(url, fields, status, source)
        yield from rows

    @staticmethod
    def _settle(pending: list[list], pid: str, url: str, status: str) -> None:
        """Give the oldest pending post of process `pid` to `url` its status."""
        for entry in pending:
            if entry[0] == pid and entry[1] == url:
                entry[3] = status
                pending.remove(entry)
                return

    def _log_row(self, artifact: Artifact, n: int, when: str, text: str) -> Row:
        row = self.base_row(artifact)
        row.source_line = n
        row.timestamp_utc = to_utc(when)
        row.turn_type = "system"
        row.text = text
        return row

    @staticmethod
    def _post_text(url: str, fields: str | None, status: str, source: str) -> str:
        try:
            doc = json.loads(fields) if fields else {}
        except ValueError:
            doc = {}
        doc = doc if isinstance(doc, dict) else {}
        agent = doc.get("agentId")
        if not isinstance(agent, str) or not agent:
            m = AGENT_URL_RX.search(url)
            agent = m.group(1) if m else "-"
        keys = doc.get("metadataKeys")
        keys = ",".join(str(k) for k in keys) if isinstance(keys, list) and keys else "-"
        return "agent metadata posted: agent %s keys %s %s (from %s, log line time, host-local)" % (
            agent,
            keys,
            status,
            source,
        )

    @staticmethod
    def _fill(row: Row, text, opts: Options) -> Row:
        row.text = compact(text)
        return row
