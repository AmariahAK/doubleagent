"""nanobot sessions, memory history, the WebUI mirror and the CLI history.

Validated against source, HKUDS/nanobot at acdae3d (see
`analyzer/research/nanobot.md`), with a synthetic fixture; no real install
was checked. The state directory is `.nanobot`, or `.nanobot-<instance>`.
Files:

* `sessions/<workspace-id>/<stem>.jsonl`: one file per session key,
  `<workspace-id>` 32 hex characters, `<stem>` the URL-safe base64 of the
  key without padding. The sibling `sessions/<workspace-id>/.workspace`
  holds the workspace path, used as `project_path`. Legacy global
  `sessions/<key with ":" as "_">.jsonl` files (no `.workspace`) and
  `sessions/<workspace-id>/.migration-conflicts/*.jsonl` copies have the
  same format. Line 1 is `{"_type":"metadata", "key", "created_at",
  "updated_at", "metadata"}` (`metadata._nanobot_model_preset`,
  `metadata.last_channel`); an optional `{"_type":"provider_state"}` line
  is opaque and skipped; every other line is an OpenAI chat message:
  `role` (`user`, `assistant`, `tool`, `system`), `content` (string or
  `{type:"text", text}` blocks), `timestamp`, assistant `tool_calls[]`
  {`id`, `function`: {`name`, `arguments` (JSON string)}} and
  `reasoning_content`, tool `tool_call_id` and `name`, and the flags
  `_hidden_history` (a synthetic user message standing in for summarised
  history, emitted as `system`) and `_runtime_context` (context attached to
  a real user message, which stays `user`). `*.checkpoint.json` sidecars
  are volatile and not read.
* `memory/history.jsonl` under a nanobot directory (the default workspace
  is `.nanobot/workspace`): the compressed long-term journal, lines
  `{cursor, timestamp: "YYYY-MM-DD HH:MM", content, session_key?}`, each
  one `system` row with `session_id` the `session_key` and `project_path`
  the workspace holding `memory/`.

`session_id` is the metadata `key` (`<channel>:<chat_id>` names the
external sender, or `cli:direct`, `heartbeat`, `unified:default`), falling
back to the decoded file name. Every timestamp nanobot writes is naive host
local time (`datetime.now().isoformat()`), and the collection does not
record the host's zone, so they are emitted as if they were UTC, the same
convention as the Aider parser; correct them by the host's offset, which
`llm_usage.sqlite3` `llm_calls.started_at_ms` (true UTC) can give. Messages
without a timestamp inherit the previous one, else the metadata
`updated_at`. No model is recorded per message: the session's
`_nanobot_model_preset`, when set, is the `model` of every row. No git
branch is recorded. A preset also becomes a `system` row after the session
start row, at its time, `model: <preset> (preset)`: the value names a model
preset of nanobot's configuration, not a model id. A file has one
metadata line, so it names one preset and no change row is written. No
permission state is read: `pairing.json` (the chat senders the operator
approved) is named in the collector research without its shape. `/new`
empties a session file, so earlier turns may survive only in
`memory/history.jsonl` and the WebUI mirror below.

`memory/history.jsonl` is a primary record, not a secondary source: its
entries are model-written summaries of archived messages, or `[RAW] <n>
messages` blocks of several formatted messages, never one event of the
session file, so no row of it repeats a session row.

Two secondary sources (issue 122) repeat session events and are read on
every run; `secondary()` is True for them, and `dedup.deduplicate` drops
a row the session file also yields:

* `webui/<safe key>.jsonl` and `webui/<safe key>.segments/NNNNNN.jsonl`
  under a nanobot directory: the WebUI display transcript (schema version
  3), written only for WebUI chats, whose session key is
  `websocket:<chat_id>`. `<safe key>` is the key with `:` as `_`
  (`websocket_<chat_id>`), not the base64 stem of the session files. The
  active file holds the recent turns; when it passes 2 MiB, nanobot moves
  the older turns into the next numbered segment and rewrites the active
  file with the rest, so each file holds different turns and every one is
  read (`segments/manifest.json` is an index and is not). One event per
  line, `event` naming it, with `chat_id` and `created_at_ms` (epoch
  milliseconds, true UTC): `user` (`text`, `media_paths[]`) is a `user`
  row; `message` with no `kind` is an `assistant` row of `text`;
  `message` with `kind` `tool_hint` or `progress` carries `tool_events[]`
  {`phase` `start`/`end`/`error`, `call_id`, `name`, `arguments` (an
  object), `result`, `error`}, each `start` a `tool_use` row and each
  `end` or `error` a `tool_result` row, joined on `call_id` (the session's
  `tool_calls[].id`), and its `text`, a breadcrumb, becomes a `system`
  row only when it has no tool events; `message` `kind` `reasoning` and
  `reasoning_end` (`text`) are `thinking` rows, opt-in; `stream_end`
  (`text`) is an `assistant` row, except one with `merge_next`, whose
  text the next `stream_end` repeats; `file_edit` `edits[]` {`call_id`,
  `tool`, `absolute_path`, `phase`, `status`, `added`, `deleted`,
  `operation`} gives one `system` row per finished edit; `fork_marker`
  and `context_compaction` (`phase`) are `system` rows; `delta`,
  `reasoning_delta` (folded into their end records, and no longer
  written) and `turn_end` (latency and token counts) yield nothing, and
  any other event is a `system` row naming it. `session_id` is
  `websocket:` plus the record's `chat_id` (the session file's metadata
  `key`), else from the file name; `project_path` is the `.workspace` of
  the session file of that key under the same nanobot directory, when
  exactly one workspace has one, else empty. The legacy
  `webui/<safe key>.json` thread is not read: its shape is not recorded.
  Times: `created_at_ms` is true UTC while the session file's times are
  host local time emitted as if UTC, so the two differ by the host's UTC
  offset, at most 14 hours (UTC-12 to UTC+14); and the session file
  stamps a turn's assistant and tool messages when the turn is saved, at
  its end, while the WebUI stamps each as it streams. The tolerance is
  therefore `WEBUI_TOLERANCE_SECONDS`, 15 hours: the largest offset plus
  an hour of turn. A turn longer than that hour, a transcript written by
  a fork (every row stamped at the fork) and a user message carrying
  runtime context (appended to the session's copy, not the WebUI's) are
  shown twice. A WebUI row kept because no session row matched carries
  true UTC, unlike every other nanobot row.
* `.nanobot/history/cli_history` (always under `~/.nanobot`, whatever
  instance runs): the CLI's prompt_toolkit `FileHistory`, `# <timestamp>`
  then one `+<line>` per input line, read with the Aider parser's
  `read_input_history`. Each entry is a `user` row at its own time (naive
  local time, emitted as if UTC like the session file's, so the default
  2-second window applies), with no `session_id` or `project_path`: the
  file is shared by every CLI session, so a row matches a session row of
  the same text on time alone.
"""

from __future__ import annotations

import base64
import re
from collections.abc import Iterator
from pathlib import Path

from ..inputs import Artifact
from ..model import Row, compact
from ..timeutil import to_utc
from .aider import read_input_history
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    iter_jsonl,
    text_of,
    track_change,
)
from .openclaw import tool_args_text

STATE = r"\.nanobot(?:-[^/]+)?"
SESSION_RX = re.compile(
    r"^" + STATE + r"/sessions/(?:(?P<ws>[0-9a-f]{32})/(?:\.migration-conflicts/)?)?"
    r"(?P<stem>[^/]+)\.jsonl$"
)
HISTORY_RX = re.compile(r"^" + STATE + r"/(?:.+/)?memory/history\.jsonl$")
WEBUI_RX = re.compile(
    r"^" + STATE + r"/webui/(?:(?P<seg>[^/]+)\.segments/\d{6}|(?P<stem>[^/]+))\.jsonl$"
)
CLI_HISTORY_REL = ".nanobot/history/cli_history"
WEBUI_PREFIX = "websocket:"
# The host's UTC offset (at most 14 hours) plus an hour of turn; see the
# module docstring.
WEBUI_TOLERANCE_SECONDS = 15 * 3600.0
# Stream chunks (folded into their end records) and the turn boundary.
WEBUI_SILENT = frozenset({"delta", "reasoning_delta", "turn_end"})
ORIGINAL_MEMORY_RX = re.compile(r"^(.*)[\\/]memory[\\/]history\.jsonl$")


def decode_stem(stem: str) -> str:
    """Session key from a file stem: URL-safe base64 without padding, or the
    legacy lossy `<channel>_<chat>` form returned unchanged."""
    try:
        key = base64.urlsafe_b64decode(stem + "=" * (-len(stem) % 4)).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return stem
    if base64.urlsafe_b64encode(key.encode("utf-8")).decode("ascii").rstrip("=") != stem:
        return stem
    return key


def _read_marker(path: Path) -> str:
    """The stripped text of a `.workspace` file, "" when it is missing, a
    symlink or unreadable."""
    try:
        if path.is_symlink() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


class NanobotParser(Parser):
    agent = "nanobot"
    name = "nanobot"
    has_secondary = True

    def wants(self, artifact: Artifact) -> bool:
        return bool(
            SESSION_RX.match(artifact.rel)
            or HISTORY_RX.match(artifact.rel)
            or WEBUI_RX.match(artifact.rel)
            or artifact.rel == CLI_HISTORY_REL
        )

    def secondary(self, artifact: Artifact) -> bool:
        return bool(WEBUI_RX.match(artifact.rel)) or artifact.rel == CLI_HISTORY_REL

    def secondary_tolerance(self, artifact: Artifact) -> float:
        if WEBUI_RX.match(artifact.rel):
            return WEBUI_TOLERANCE_SECONDS
        return super().secondary_tolerance(artifact)

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if SESSION_RX.match(artifact.rel):
            yield from self._parse_session(artifact, opts)
        elif WEBUI_RX.match(artifact.rel):
            yield from self._parse_webui(artifact, opts)
        elif artifact.rel == CLI_HISTORY_REL:
            yield from self._parse_cli_history(artifact)
        else:
            yield from self._parse_history(artifact, opts)

    @staticmethod
    def _workspace(artifact: Artifact) -> str:
        marker = artifact.disk_path.parent / ".workspace"
        m = SESSION_RX.match(artifact.rel)
        assert m is not None  # parse() routes only matching paths here
        if not m.group("ws"):
            return ""
        if artifact.disk_path.parent.name == ".migration-conflicts":
            marker = artifact.disk_path.parent.parent / ".workspace"
        return _read_marker(marker)

    def _parse_session(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        m = SESSION_RX.match(artifact.rel)
        assert m is not None  # parse() routes only matching paths here
        session_id = decode_stem(m.group("stem"))
        project = self._workspace(artifact)
        model = ""
        last_ts = ""
        errors: list = []
        models: dict = {}

        def row(
            n: int, turn_type: str, text: str, tool_name: str = "", tool_use_id: str = ""
        ) -> Row:
            r = self.base_row(artifact)
            r.source_line = n
            r.session_id = session_id
            r.project_path = project
            r.timestamp_utc = last_ts
            r.model = model
            r.turn_type = turn_type
            r.tool_name = tool_name
            r.tool_use_id = tool_use_id
            r.text = compact(text)
            return r

        for n, rec in iter_jsonl(artifact.disk_path, errors):
            rtype = rec.get("_type")
            if rtype == "metadata":
                if rec.get("key"):
                    session_id = str(rec["key"])
                meta = rec.get("metadata")
                if not isinstance(meta, dict):
                    meta = {}
                model = str(meta.get("_nanobot_model_preset") or "")
                last_ts = to_utc(rec.get("created_at")) or to_utc(rec.get("updated_at"))
                yield row(
                    n,
                    "system",
                    " ".join(
                        x
                        for x in (
                            "session start: key=%s" % session_id,
                            "last_channel=%s" % meta["last_channel"]
                            if meta.get("last_channel")
                            else "",
                            "updated_at=%s" % rec["updated_at"] if rec.get("updated_at") else "",
                            "workspace=%s" % project if project else "",
                        )
                        if x
                    ),
                )
                text = track_change("model", models, session_id, model)
                if text:
                    yield row(n, "system", text + " (preset)")
                continue
            if rtype is not None and "role" not in rec:
                continue  # provider_state and future record types
            last_ts = to_utc(rec.get("timestamp")) or last_ts
            role = rec.get("role")
            text = text_of(rec.get("content"))
            if role == "user":
                if rec.get("_hidden_history"):
                    yield row(n, "system", "summarised history: " + text)
                else:
                    yield row(n, "user", text)
            elif role == "assistant":
                reasoning = rec.get("reasoning_content")
                if opts.include_thinking and isinstance(reasoning, str) and reasoning:
                    yield row(n, "thinking", reasoning)
                if text:
                    yield row(n, "assistant", text)
                for tc in rec.get("tool_calls") or []:
                    if not isinstance(tc, dict):
                        continue
                    fn = tc.get("function")
                    if not isinstance(fn, dict):
                        fn = {}
                    yield row(
                        n,
                        "tool_use",
                        tool_args_text(fn.get("arguments")),
                        str(fn.get("name") or ""),
                        str(tc.get("id") or ""),
                    )
            elif role == "tool":
                yield row(
                    n,
                    "tool_result",
                    text,
                    str(rec.get("name") or ""),
                    str(rec.get("tool_call_id") or ""),
                )
            else:
                yield row(n, "system", "%s: %s" % (role or "message", text))
        yield from error_rows(self, artifact, errors, session_id, project)

    def _parse_history(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        m = ORIGINAL_MEMORY_RX.match(artifact.original or "")
        project = m.group(1) if m else ""
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            r = self.base_row(artifact)
            r.source_line = n
            r.session_id = str(rec.get("session_key") or "")
            r.project_path = project
            r.timestamp_utc = to_utc(rec.get("timestamp"))
            r.turn_type = "system"
            r.text = compact(
                "memory history #%s: %s" % (rec.get("cursor", ""), rec.get("content") or ""),
            )
            yield r
        yield from error_rows(self, artifact, errors, "", project)

    @staticmethod
    def _webui_workspace(artifact: Artifact, session_id: str) -> str:
        """The `.workspace` of the session file for `session_id` under the
        same nanobot directory, when exactly one workspace holds one."""
        m = WEBUI_RX.match(artifact.rel)
        assert m is not None  # parse() routes only matching paths here
        state = artifact.disk_path.parents[2 if m.group("seg") else 1]
        stem = base64.urlsafe_b64encode(session_id.encode("utf-8")).decode("ascii").rstrip("=")
        found: set[str] = set()
        try:
            for f in (state / "sessions").glob("*/%s.jsonl" % stem):
                if not (f.is_symlink() or f.parent.is_symlink()) and f.is_file():
                    found.add(_read_marker(f.parent / ".workspace"))
        except OSError:
            return ""
        found.discard("")
        return found.pop() if len(found) == 1 else ""

    def _parse_webui(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        m = WEBUI_RX.match(artifact.rel)
        assert m is not None  # parse() routes only matching paths here
        stem = m.group("seg") or m.group("stem")
        fallback = stem
        if stem.startswith("websocket_"):
            fallback = WEBUI_PREFIX + stem[len("websocket_") :]
        projects: dict[str, str] = {}
        errors: list = []

        def row(n: int, sid: str, ts: object, event: tuple[str, str, str, str]) -> Row:
            turn_type, text, tool_name, tool_use_id = event
            if sid not in projects:
                projects[sid] = self._webui_workspace(artifact, sid)
            r = self.base_row(artifact)
            r.source_line = n
            r.session_id = sid
            r.project_path = projects[sid]
            r.timestamp_utc = to_utc(ts)
            r.turn_type = turn_type
            r.tool_name = tool_name
            r.tool_use_id = tool_use_id
            r.text = compact(text)
            return r

        sid = fallback
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            chat = rec.get("chat_id")
            sid = WEBUI_PREFIX + chat if isinstance(chat, str) and chat else fallback
            for event in self._webui_events(rec, opts):
                yield row(n, sid, rec.get("created_at_ms"), event)
        if errors:
            if sid not in projects:
                projects[sid] = self._webui_workspace(artifact, sid)
            yield from error_rows(self, artifact, errors, sid, projects[sid])

    @staticmethod
    def _webui_events(rec: dict, opts: Options) -> Iterator[tuple[str, str, str, str]]:
        """(turn_type, text, tool_name, tool_use_id) per row of one WebUI
        record; the module docstring maps each event."""
        event = rec.get("event")
        text = rec.get("text") if isinstance(rec.get("text"), str) else ""
        if event == "user":
            media = [str(p) for p in rec.get("media_paths") or [] if p]
            yield "user", text or " ".join("[media: %s]" % p for p in media), "", ""
        elif event == "message":
            kind = rec.get("kind")
            tool_events = [e for e in rec.get("tool_events") or [] if isinstance(e, dict)]
            for e in tool_events:
                name, call_id = str(e.get("name") or ""), str(e.get("call_id") or "")
                if e.get("phase") == "start":
                    yield "tool_use", tool_args_text(e.get("arguments")), name, call_id
                elif e.get("phase") == "end":
                    result = e.get("result")
                    body = result if isinstance(result, str) else compact_json(result)
                    yield "tool_result", body, name, call_id
                elif e.get("phase") == "error":
                    yield "tool_result", str(e.get("error") or ""), name, call_id
            if kind == "reasoning":
                if opts.include_thinking and text:
                    yield "thinking", text, "", ""
            elif kind in ("tool_hint", "progress"):
                if text and not tool_events:
                    yield "system", "%s: %s" % (str(kind).replace("_", " "), text), "", ""
            elif text:
                yield "assistant", text, "", ""
        elif event == "stream_end":
            if text and not rec.get("merge_next"):
                yield "assistant", text, "", ""
        elif event == "reasoning_end":
            if opts.include_thinking and text:
                yield "thinking", text, "", ""
        elif event == "file_edit":
            for e in rec.get("edits") or []:
                if isinstance(e, dict) and e.get("phase") != "start":
                    yield (
                        "system",
                        "file edit: %s %s +%s -%s%s"
                        % (
                            e.get("status") or e.get("phase") or "",
                            e.get("absolute_path") or e.get("path") or "",
                            e.get("added", 0),
                            e.get("deleted", 0),
                            " (%s)" % e["operation"] if e.get("operation") else "",
                        ),
                        str(e.get("tool") or ""),
                        str(e.get("call_id") or ""),
                    )
        elif event == "fork_marker":
            yield "system", "webui fork marker: the fork starts here", "", ""
        elif event == "context_compaction":
            yield "system", "context compaction: %s" % (rec.get("phase") or ""), "", ""
        elif isinstance(event, str) and event and event not in WEBUI_SILENT:
            yield "system", "webui event: %s" % event, "", ""

    def _parse_cli_history(self, artifact: Artifact) -> Iterator[Row]:
        errors: list = []
        for n, ts, text in read_input_history(artifact.disk_path, errors):
            r = self.base_row(artifact)
            r.source_line = n
            r.timestamp_utc = to_utc(ts)
            r.turn_type = "user"
            r.text = compact(text)
            yield r
        yield from error_rows(self, artifact, errors)


__all__ = ["NanobotParser", "decode_stem"]
