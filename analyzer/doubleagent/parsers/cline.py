"""Cline transcripts, legacy task layout and SDK sessions.

Validated against source (cline/cline at 39ff2359, see
`analyzer/research/cline.md`) with a synthetic fixture; no real install.

Legacy task layout, under the VS Code extension's
`<editor>/User/globalStorage/saoudrizwan.claude-dev/` or `~/.cline/data/`
(CLI and JetBrains): `tasks/<taskId>/ui_messages.json`,
`api_conversation_history.json` and `task_metadata.json` are read by the
shared mapping in `cline_legacy.py`, whose docstring lists the fields. The
task id is a `Date.now()` millisecond string, which is also the session
timestamp that API history records (which carry no timestamp of their own)
inherit when `ui_messages.json` is missing. The API history stays a
fallback, not a secondary source: it records a turn in other words than
`ui_messages.json` (the first prompt wrapped in `<task>` tags, tool calls
as content blocks or XML), so `dedup.deduplicate` could not pair the two
(section 8 of the research document).

* `state/taskHistory.json`: JSON array of `HistoryItem {id, ts, task,
  tokensIn, tokensOut, cacheWrites, cacheReads, totalCost, size,
  cwdOnTaskInitialization, modelId, apiProvider}`. One `system` row per
  task, kept because it survives deletion of the task directory; it is also
  where the task's project path and fallback model come from. Older VS Code
  builds kept this list in the editor's `state.vscdb`, which is not read.

SDK session layout, `~/.cline/data/sessions/<sessionId>/`:

* `<sessionId>.json` manifest: `session_id, source, pid, started_at,
  ended_at, exit_code, status, interactive, provider, model, cwd,
  workspace_root, prompt, metadata.title`. A `system` row for the start,
  then `model: <model> provider=<provider>` when the manifest names a
  model, and, when `ended_at` is set, one row for the end.
* `<sessionId>.messages.json` and subagent `<agentId>[__<teamTaskId>]
  .messages.json`: `{version, updated_at, agent, sessionId, messages:
  [{id, role, content, modelInfo: {id, provider}, metrics, ts}]}` with
  Anthropic-style content blocks (`text`, `tool_use {id, name, input}`,
  `tool_result {tool_use_id, name, content, is_error}`, `thinking`,
  `redacted_thinking`, `image`, `file {path}`). One row per block;
  `ts` is epoch milliseconds; a message without one takes the previous
  message's time, or for the first message the manifest `started_at` and
  then the file's `updated_at`. `session_id` is the session directory
  name, so subagent rows group with their lead session; `project_path` and
  the fallback model come from the manifest beside it. A message whose
  `modelInfo.id` differs from the model before it yields `model: <old> ->
  <new> provider=<modelInfo.provider>` ahead of its rows; the lead
  transcript starts from the manifest `model`, so its first message yields
  `model: <id>` only when the manifest names none, and a subagent
  transcript starts from its own first `modelInfo.id`.
* `~/.cline/data/db/sessions.db`, table `sessions` (`session_id, source,
  started_at, ended_at, status, provider, model, cwd, workspace_root,
  prompt, parent_session_id, is_subagent`): a `system` row, followed by
  `model: <model> provider=<provider>`, only for a session whose manifest
  is not on disk, so deleted sessions still show.
* `~/.cline/data/db/session-search.db`, a secondary source (issue 122):
  the full-text index the SDK hub server keeps of each session's lead
  transcript, tables `indexed_sessions (session_id, source_revision,
  indexed_at, document_count, index_version, title)` and the FTS5 (SQLite
  full-text search) table `session_search (session_id, document_id,
  ordinal, role, started_at, workspace_root, title, content)`. Per session
  one document `<sessionId>:metadata`, `ordinal` -1 and `role` `session`,
  holds the title and the session's `prompt`; then one document per
  `<sessionId>.messages.json` message with any text, `ordinal` its 0-based
  position in that file, `role` the message's (`unknown` when it has
  none), and `content` every string value of the message's `content`
  (block type names, tool ids and tool input included; `data`, `image`,
  `images`, `reasoning`, `thinking` and `metadata` values left out) joined
  with line breaks and capped at 128 KiB. Rows: one `system` row per
  session, `session search index: title=... workspace_root=... prompt=...
  document_count=... indexed_at=...`, at the session's `started_at`; then
  one row per message document in `ordinal` order, `user` or `assistant`
  by `role` (`system` for any other), with an empty `timestamp_utc`, since
  the index records no time per message, so `dedup.deduplicate` matches
  them on text and session alone. `source_line` is `ordinal + 1`, the
  message's position in the transcript (0 when the ordinal is not a
  number). `session_id` is the index's, the SDK session id the manifest
  and messages rows carry; `project_path` is the manifest's `cwd` (else
  `workspace_root`) when the manifest is on disk, as the messages reader
  takes it, else the document's `workspace_root`. A message whose
  `content` is a plain string (a prompt with no attached image or file)
  pairs with its transcript row; a block array's text keeps the block type
  names and tool ids, so it never equals a transcript row and is kept. The
  hub reconciles the index at start and every five minutes while it runs:
  it drops a session that has left `sessions.db` and re-indexes one whose
  messages file changed or is gone, so the index outlives a deleted
  transcript only until the hub next runs. When the SQLite build lacks
  FTS5, one `system` row says so and only `indexed_sessions` is read, each
  session row then without a time.

* `~/.cline/data/cache/user_input_history.jsonl`, a secondary source
  (issue 122): the CLI's prompt history for up-arrow recall, one JSON line
  `{prompt, ts}` per prompt submitted in the terminal UI, trimmed, oldest
  first, each prompt kept once (a repeat moves to the end) and the last 20
  kept. No session id and no project are recorded. The CLI rewrites the
  whole file on every prompt and stamps every line with that write's
  `Date.now()`, so only the last line's `ts` (epoch milliseconds) is its
  own prompt's time. Rows: one `user` row per line, `source_line` the
  line; the last line has its `ts`, the others an empty `timestamp_utc`,
  and every line is undated when the file has a bad line, since the last
  parsed line may then not be the newest. Undated rows match a
  transcript row of any Cline session on text alone.

Not read: `<sessionId>.compaction.json`, `sessions/sessions.index.json`,
`teams/teams.db` and `logs/hooks.jsonl`.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import Options, iter_jsonl, track_change
from .cline_legacy import (
    LegacyTaskParser,
    content_rows,
    error_row,
    iter_array_at,
    iter_json_array,
    load_json,
    read_text,
)

ROOT = r"(?:(?:.*/)?User/globalStorage/saoudrizwan\.claude-dev|\.cline/data)"
STATE_RX = re.compile(r"^%s/state/taskHistory\.json$" % ROOT, re.I)
MANIFEST_RX = re.compile(r"^\.cline/data/sessions/([^/]+)/\1\.json$")
MESSAGES_RX = re.compile(r"^\.cline/data/sessions/[^/]+/[^/]+\.messages\.json$")
SESSIONS_DB_REL = ".cline/data/db/sessions.db"
SEARCH_DB_REL = ".cline/data/db/session-search.db"
INPUT_HISTORY_REL = ".cline/data/cache/user_input_history.jsonl"
SEARCH_COLUMNS = (
    "session_id, document_id, ordinal, role, started_at, workspace_root, title, content"
)
SEARCH_KEYS = ("title", "workspace_root", "prompt", "document_count", "indexed_at")
MESSAGES_KEY_RX = re.compile(r'"messages"\s*:\s*(?=\[)')


class ClineParser(LegacyTaskParser):
    agent = "cline"
    name = "cline"
    ROOT = ROOT
    PROJECT_KEY = "cwdOnTaskInitialization"

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return bool(
            self.task_match(artifact)
            or STATE_RX.match(rel)
            or MANIFEST_RX.match(rel)
            or MESSAGES_RX.match(rel)
        ) or rel in (SESSIONS_DB_REL, SEARCH_DB_REL, INPUT_HISTORY_REL)

    def secondary(self, artifact: Artifact) -> bool:
        return artifact.rel in (SEARCH_DB_REL, INPUT_HISTORY_REL)

    def history_item(self, task_dir: Path, root: Path, task_id: str) -> dict | None:
        items = self.cached_json(root / "state" / "taskHistory.json")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and str(item.get("id")) == task_id:
                    return item
        return None

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        if self.task_match(artifact):
            yield from self.parse_task_file(artifact, opts)
        elif STATE_RX.match(rel):
            yield from self._parse_task_history(artifact, opts)
        elif MANIFEST_RX.match(rel):
            yield from self._parse_manifest(artifact, opts)
        elif MESSAGES_RX.match(rel):
            yield from self._parse_messages(artifact, opts)
        elif rel == SESSIONS_DB_REL:
            yield from self._parse_sessions_db(artifact, opts)
        elif rel == SEARCH_DB_REL:
            yield from self._parse_search_db(artifact)
        elif rel == INPUT_HISTORY_REL:
            yield from self._parse_input_history(artifact)

    def _parse_task_history(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        for n, item in iter_json_array(artifact.disk_path, errors):
            if isinstance(item, dict):
                yield self.history_row(artifact, item, n, opts)
        if errors:
            yield error_row(self, artifact, errors)

    # -- SDK sessions

    def _session_start(
        self, m: dict, artifact: Artifact, n: int, opts: Options, ts_key: str, label: str, keys
    ) -> Row:
        row = self.base_row(artifact)
        row.source_line = n
        row.timestamp_utc = to_utc(m.get(ts_key))
        row.session_id = str(m.get("session_id") or "")
        row.project_path = str(m.get("cwd") or m.get("workspace_root") or "")
        row.model = str(m.get("model") or "")
        row.turn_type = "system"
        detail = " ".join("%s=%s" % (k, m[k]) for k in keys if m.get(k) not in (None, ""))
        row.text = compact("%s: %s" % (label, detail))
        return row

    def _model_start(self, start: Row, m: dict) -> Iterator[Row]:
        """`model: <model> provider=<provider>` after a session start or index
        row, with its time, session and project."""
        model = str(m.get("model") or "")
        if not model:
            return
        provider = str(m.get("provider") or "")
        yield replace(
            start,
            model=model,
            text=compact("model: %s%s" % (model, " provider=%s" % provider if provider else "")),
        )

    START_KEYS = (
        "source",
        "provider",
        "status",
        "interactive",
        "pid",
        "parent_session_id",
        "is_subagent",
        "title",
        "prompt",
    )
    END_KEYS = ("status", "exit_code")

    def _parse_manifest(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        m = load_json(artifact.disk_path)
        if not isinstance(m, dict):
            yield error_row(
                self,
                artifact,
                [(0, "session manifest is not a JSON object")],
                artifact.disk_path.parent.name,
            )
            return
        m = dict(m)
        m.setdefault("session_id", artifact.disk_path.parent.name)
        meta = m.get("metadata")
        if isinstance(meta, dict) and meta.get("title"):
            m["title"] = meta["title"]
        start = self._session_start(
            m, artifact, 0, opts, "started_at", "session start", self.START_KEYS
        )
        yield start
        yield from self._model_start(start, m)
        if m.get("ended_at"):
            yield self._session_start(
                m, artifact, 0, opts, "ended_at", "session end", self.END_KEYS
            )

    def _parse_messages(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        session_id = artifact.disk_path.parent.name
        manifest = load_json(artifact.disk_path.parent / (session_id + ".json"))
        manifest = manifest if isinstance(manifest, dict) else {}
        project = str(manifest.get("cwd") or manifest.get("workspace_root") or "")
        s = read_text(artifact.disk_path)
        errors: list = []
        payload = None
        if s is None:
            errors.append((0, "unreadable"))
        else:
            try:
                payload = json.loads(s)
            except ValueError:
                payload = None
        if isinstance(payload, dict):
            messages = enumerate(payload.get("messages") or [], 1)
            fallback = to_utc(manifest.get("started_at")) or to_utc(payload.get("updated_at"))
        elif s is not None:
            # Cut mid-write: walk the messages array as far as it parses.
            m = MESSAGES_KEY_RX.search(s)
            if m:
                messages = iter_array_at(s, m.end(), errors)
            else:
                errors.append((0, "messages file is not a JSON object"))
                messages = iter(())
            fallback = to_utc(manifest.get("started_at"))
        else:
            messages = iter(())
            fallback = ""
        # The lead transcript continues from the manifest's model, whose start
        # row the manifest yields; a subagent transcript tracks its own.
        seen: dict = {}
        if artifact.disk_path.name == session_id + ".messages.json" and manifest.get("model"):
            seen[session_id] = str(manifest["model"])
        for n, msg in messages:
            if not isinstance(msg, dict):
                continue
            ts = to_utc(msg.get("ts")) or fallback
            fallback = ts
            info = msg.get("modelInfo")
            info = info if isinstance(info, dict) else {}
            model = str(info.get("id") or manifest.get("model") or "")
            change = track_change("model", seen, session_id, str(info.get("id") or ""))
            if change:
                row = self.base_row(artifact)
                row.source_line = n
                row.timestamp_utc = ts
                row.session_id = session_id
                row.project_path = project
                row.model = model
                row.turn_type = "system"
                provider = str(info.get("provider") or "")
                row.text = compact(change + (" provider=%s" % provider if provider else ""))
                yield row
            role = msg.get("role")
            base_turn = (
                "user" if role == "user" else "assistant" if role == "assistant" else "system"
            )
            for turn, text, name, tid in content_rows(
                msg.get("content"), base_turn, opts.include_thinking
            ):
                row = self.base_row(artifact)
                row.source_line = n
                row.timestamp_utc = ts
                row.session_id = session_id
                row.project_path = project
                row.model = model
                row.turn_type = turn
                row.tool_name = name
                row.tool_use_id = tid
                row.text = compact(text)
                yield row
        if errors:
            yield error_row(self, artifact, errors, session_id, project)

    def _parse_sessions_db(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield error_row(self, artifact, [(0, "sessions.db is not a SQLite database")])
            return
        sessions_dir = artifact.disk_path.parent.parent / "sessions"
        try:
            with open_copy(artifact.disk_path) as con:
                if "sessions" not in table_names(con):
                    return
                rows = [dict(r) for r in con.execute("select rowid as _rowid, * from sessions")]
        except Exception as e:  # noqa: BLE001 - a damaged database must not stop the timeline
            yield error_row(self, artifact, [(0, "sessions.db unreadable (%s)" % e)])
            return
        for r in rows:
            sid = str(r.get("session_id") or "")
            if sid and (sessions_dir / sid / (sid + ".json")).is_file():
                continue
            if r.get("metadata_json"):
                meta = load_json_text(r["metadata_json"])
                if isinstance(meta, dict) and meta.get("title"):
                    r["title"] = meta["title"]
            start = self._session_start(
                r,
                artifact,
                int(r.get("_rowid") or 0),
                opts,
                "started_at",
                "session index",
                (*self.START_KEYS, "ended_at", "exit_code"),
            )
            yield start
            yield from self._model_start(start, r)

    # -- cache/user_input_history.jsonl

    def _parse_input_history(self, artifact: Artifact) -> Iterator[Row]:
        errors: list = []
        entries = [
            (n, rec["prompt"], rec.get("ts"))
            for n, rec in iter_jsonl(artifact.disk_path, errors)
            if isinstance(rec.get("prompt"), str) and rec["prompt"].strip()
        ]
        for k, (n, prompt, ts) in enumerate(entries):
            row = self.base_row(artifact)
            row.source_line = n
            row.turn_type = "user"
            # Every line carries the time of the file's last rewrite, the
            # newest prompt's own time only; a bad line makes that unsure.
            if k == len(entries) - 1 and not errors and isinstance(ts, (int, float)):
                row.timestamp_utc = to_utc(ts)
            row.text = compact(prompt)
            yield row
        if errors:
            n, e = errors[0]
            yield error_row(self, artifact, [(n, "line %d unparseable (%s)" % (n, e))])

    # -- session-search.db

    def _parse_search_db(self, artifact: Artifact) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield error_row(self, artifact, [(0, "session-search.db is not a SQLite database")])
            return
        problem = ""
        try:
            with open_copy(artifact.disk_path) as con:
                tables = table_names(con)
                indexed = []
                if "indexed_sessions" in tables:
                    indexed = [
                        dict(r)
                        for r in con.execute("select * from indexed_sessions order by rowid")
                    ]
                docs = []
                if "session_search" in tables:
                    try:
                        docs = [
                            dict(r)
                            for r in con.execute(
                                "select %s from session_search order by rowid" % SEARCH_COLUMNS
                            )
                        ]
                    except sqlite3.OperationalError as e:
                        problem = "session_search unreadable (%s), indexed_sessions read alone" % e
        except Exception as e:  # noqa: BLE001 - a damaged database must not stop the timeline
            yield error_row(self, artifact, [(0, "session-search.db unreadable (%s)" % e)])
            return
        if problem:
            yield error_row(self, artifact, [(0, problem)])
        by_session: dict[str, list[dict]] = {}
        for s in indexed:
            by_session.setdefault(str(s.get("session_id") or ""), [])
        for d in docs:
            by_session.setdefault(str(d.get("session_id") or ""), []).append(d)
        meta = {str(s.get("session_id") or ""): s for s in indexed}
        sessions_dir = artifact.disk_path.parent.parent / "sessions"
        for sid, session_docs in by_session.items():
            yield from self._search_session(
                artifact, sid, meta.get(sid, {}), session_docs, sessions_dir
            )

    def _search_session(
        self, artifact: Artifact, sid: str, indexed: dict, docs: list, sessions_dir: Path
    ) -> Iterator[Row]:
        """The index's rows for one session: the session row, then one row
        per message document in transcript order."""
        head = next((d for d in docs if d.get("role") == "session"), None)
        docs = sorted(
            (d for d in docs if d.get("role") != "session"),
            key=lambda d: _ordinal(d.get("ordinal")),
        )
        workspace = str((head or (docs[0] if docs else {})).get("workspace_root") or "")
        manifest = load_json(sessions_dir / sid / (sid + ".json")) if sid else None
        if isinstance(manifest, dict):
            project = str(manifest.get("cwd") or manifest.get("workspace_root") or "")
        else:
            project = workspace
        fields = {
            "title": indexed.get("title") or (head or {}).get("title"),
            "workspace_root": workspace,
            "prompt": (head or {}).get("content"),
            "document_count": indexed.get("document_count"),
            "indexed_at": indexed.get("indexed_at"),
        }
        row = self.base_row(artifact)
        row.timestamp_utc = to_utc((head or (docs[0] if docs else {})).get("started_at"))
        row.session_id = sid
        row.project_path = project
        row.turn_type = "system"
        detail = " ".join(
            "%s=%s" % (k, fields[k]) for k in SEARCH_KEYS if fields[k] not in (None, "")
        )
        row.text = compact("session search index: %s" % detail)
        yield row
        for d in docs:
            role = d.get("role")
            row = self.base_row(artifact)
            row.source_line = _ordinal(d.get("ordinal")) + 1
            row.session_id = sid
            row.project_path = project
            row.turn_type = role if role in ("user", "assistant") else "system"
            row.text = compact(d.get("content"))
            yield row


def _ordinal(value) -> int:
    """A message document's `ordinal`, -1 when it is not a number."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def load_json_text(s):
    try:
        return json.loads(s)
    except (TypeError, ValueError):
        return None
