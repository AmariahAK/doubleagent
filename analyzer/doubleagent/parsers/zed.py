"""Zed agent panel threads.

Validated against source, zed-industries/zed at a84689073d29 (see
`analyzer/research/zed.md`), with a synthetic fixture; no real install was
checked. Files, relative to the Zed data directory (`.local/share/zed`,
`Library/Application Support/Zed`, `AppData/Local/Zed`, or the Flatpak
`.var/app/dev.zed.Zed*/data/zed`):

* `threads/threads.db` (rollback journal, so a `-journal` may sit beside it):
  table `threads(id, summary, updated_at, data_type, data, parent_id,
  folder_paths, folder_paths_order, created_at)`. `id` is the session id,
  `folder_paths` the project paths joined by newlines, `updated_at` and
  `created_at` RFC 3339. `data` is zstd-compressed JSON when `data_type` is
  `zstd` (decoded with the `zstandard` package) and raw UTF-8 JSON when
  `json`.
  The thread JSON, `version` `0.3.0`: `title`, `updated_at`,
  `initial_project_snapshot.timestamp`,
  `initial_project_snapshot.worktree_snapshots[].worktree_path` and
  `.git_state.current_branch`, `model.provider`, `model.model`,
  `subagent_context.parent_thread_id`, and `messages[]`, externally tagged:
  - `{"User": {"id", "content": [{"Text"}, {"Mention": {"uri"}}, {"Image"}]}}`
  - `{"Agent": {"content": [{"Text"}, {"Thinking": {"text"}},
    {"RedactedThinking"}, {"ToolUse": {"id", "name", "raw_input",
    "input"}}], "tool_results": {<id>: {"tool_use_id", "tool_name",
    "is_error", "content": [{"Text"}]}}}}`
  - `"Resume"`, `{"Compaction": {"Summary"}}` or
    `{"Compaction": {"ProviderNative"}}`.
  Versions `0.1.0` and `0.2.0` (`messages[].role`, `segments[]` with
  `type` text/thinking/RedactedThinking, `tool_uses[]`, `tool_results[]`)
  and the unversioned legacy shape (`messages[].role`, `.text`) are read
  on a best-effort basis; their role spelling was not confirmed.
* `db/0-<channel>/db.sqlite` (WAL): table `sidebar_threads(session_id,
  agent_id, title, title_override, updated_at, interacted_at,
  folder_paths, archived)`. Rows with `agent_id` set are external ACP agent
  threads whose transcript is not in `threads.db`; each becomes one `system`
  row. Native rows (`agent_id` NULL) are skipped, their thread is parsed
  from `threads.db`.

There are no per-message timestamps. Every message row carries the thread's
`updated_at` (approximate: it is the last write, not the message time); the
thread-start row carries `initial_project_snapshot.timestamp`, falling back
to `created_at`. `source_line` is the SQLite `rowid` of the thread or
sidebar row. The git branch is the one captured at thread start.

Model and permission rows (issues 96 and 97), all `system`, after the
thread-start row and before the first message:

* `model: <model.model> provider=<model.provider>` once per thread, at the
  thread-start time. The blob holds one `model` per thread, so a switch
  inside a thread is not recorded and there is no change row.
* `permission setting: <key>=<value> (thread blob, as of updated_at)`, one
  row per entry of `profile`, `sandbox_grants.write_paths[]` (a path string,
  or an object in newer blobs, printed as compact JSON) and
  `sandbox_grants.network_hosts[]`, and one per `sandbox_grants` flag
  `network_any_host`, `allow_fs_write_all`, `unsandboxed` and
  `sandbox_fallback` that is `true`. These are the grants the user gave
  "for the rest of this thread", stored in the blob, so the row carries the
  thread id as `session_id` and the thread's `updated_at` as its time (the
  last write, not the moment of the grant, which is not recorded).

Bad files and records (issues 136 and 168). A file that is not SQLite is
one `parser: not a SQLite database` row, and a SQLite error while reading
one `parser: SQLite error: <error>` row. Inside `threads.db`, each record
that does not decode is a `system` row with an empty `timestamp_utc`, the
thread's `session_id` and `project_path`, and `source_line` the `threads`
rowid:

* A `data` blob that does not decode to a JSON object is
  `parser: unparseable record <rowid> (<reason>): <stored value>`, the
  stored value being a `json` row's text, or a `zstd` row's compressed
  bytes as lowercase hex (a truncated frame can decompress to nothing, so
  the bytes are what is carried), its reason then ending `stored zstd
  blob as hex`.
* A `messages[]` item of no known variant (not `User`, `Agent`,
  `Compaction` with `Summary` or `ProviderNative`, a string or a legacy
  `role` message), an `Agent` content item of no known variant, a content
  or `segments[]` item that is not an object, or a `tool_uses[]` or
  `tool_results` entry that is not an object is
  `parser: unparseable record <N> (<reason>): <item as JSON>`, N the
  message's 1-based position in `messages[]` and the reason naming the
  item's place inside it. These rows follow the thread's other rows. An
  unknown `User` content object stays in the prompt text as JSON, as
  before.
"""

from __future__ import annotations

import io
import json
import re
import sqlite3
from collections.abc import Iterator

import zstandard

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import Options, Parser, compact_json, error_rows, setting_value

DATA_DIR = r"(?:\.local/share/zed|Library/Application Support/Zed|AppData/Local/Zed|\.var/app/dev\.zed\.Zed[A-Za-z]*/data/zed)"
SANDBOX_FLAGS = ("network_any_host", "allow_fs_write_all", "unsandboxed", "sandbox_fallback")
THREADS_RX = re.compile(r"^" + DATA_DIR + r"/threads/threads\.db$")
SIDEBAR_RX = re.compile(r"^" + DATA_DIR + r"/db/0-[^/]+/db\.sqlite$")


def decompress(blob: bytes) -> bytes:
    dctx = zstandard.ZstdDecompressor()
    try:
        return dctx.decompress(blob)
    except zstandard.ZstdError:
        # No content size in the frame header: stream it instead.
        out = io.BytesIO()
        with dctx.stream_reader(io.BytesIO(blob)) as reader:
            while True:
                chunk = reader.read(65536)
                if not chunk:
                    break
                out.write(chunk)
        return out.getvalue()


def record_json(value) -> str:
    """A decoded blob item as error row text: compact JSON in the blob's own
    key order, non-ASCII kept, so the item is carried in full."""
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(value)


def content_text(content) -> str:
    """Text of a tool result `content`: a list of `{"Text": ...}` /
    `{"Image": ...}` items, a single such item, or a plain string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        content = [content]
    if not isinstance(content, list):
        return compact_json(content)
    parts = []
    for c in content:
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, dict):
            if isinstance(c.get("Text"), str):
                parts.append(c["Text"])
            elif "Image" in c:
                parts.append("[image]")
            elif isinstance(c.get("text"), str):
                parts.append(c["text"])
            else:
                parts.append(compact_json(c))
    return "\n".join(parts)


def mention_text(m) -> str:
    if not isinstance(m, dict):
        return "[mention]"
    uri = m.get("uri")
    return "[mention] " + (uri if isinstance(uri, str) else compact_json(uri))


def tool_input_text(tu: dict) -> str:
    inp = tu.get("input")
    if isinstance(inp, dict) and set(inp) <= {"type", "value"} and "value" in inp:
        inp = inp["value"]
    if inp not in (None, "", {}):
        return inp if isinstance(inp, str) else compact_json(inp)
    raw = tu.get("raw_input")
    return raw if isinstance(raw, str) else ""


def first_folder(folder_paths) -> str:
    if not isinstance(folder_paths, str):
        return ""
    for p in folder_paths.split("\n"):
        if p.strip():
            return p
    return ""


class ZedParser(Parser):
    agent = "zed"
    name = "zed"

    def wants(self, artifact: Artifact) -> bool:
        return bool(THREADS_RX.match(artifact.rel) or SIDEBAR_RX.match(artifact.rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield self._file_error(artifact, "not a SQLite database")
            return
        try:
            if THREADS_RX.match(artifact.rel):
                yield from self._parse_threads(artifact, opts)
            else:
                yield from self._parse_sidebar(artifact, opts)
        except sqlite3.DatabaseError as e:
            yield self._file_error(artifact, "SQLite error: %s" % e)

    def _file_error(self, artifact: Artifact, message: str) -> Row:
        """The one `parser: <message>` row for a file that cannot be read."""
        row = self.base_row(artifact)
        row.turn_type = "system"
        row.text = "parser: " + message
        return row

    # -- db/0-<channel>/db.sqlite -------------------------------------------------
    def _parse_sidebar(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        with open_copy(artifact.disk_path) as con:
            if "sidebar_threads" not in table_names(con):
                return
            for r in con.execute(
                "select rowid as _rowid, * from sidebar_threads order by updated_at"
            ):
                r = dict(r)
                if not r.get("agent_id"):
                    continue
                row = self.base_row(artifact)
                row.source_line = r["_rowid"]
                row.session_id = str(r.get("session_id") or "")
                row.timestamp_utc = to_utc(r.get("interacted_at") or r.get("updated_at"))
                row.project_path = first_folder(r.get("folder_paths"))
                row.turn_type = "system"
                row.text = compact(
                    "external agent thread (no transcript in threads.db): agent=%s title=%s%s"
                    % (
                        r["agent_id"],
                        r.get("title_override") or r.get("title") or "",
                        " archived" if r.get("archived") else "",
                    ),
                )
                yield row

    # -- threads/threads.db -------------------------------------------------------
    def _parse_threads(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        with open_copy(artifact.disk_path) as con:
            if "threads" not in table_names(con):
                return
            for r in con.execute("select rowid as _rowid, * from threads order by updated_at"):
                yield from self._thread_rows(artifact, dict(r), opts)

    def _thread_rows(self, artifact: Artifact, r: dict, opts: Options) -> Iterator[Row]:
        session_id = str(r.get("id") or "")
        project = first_folder(r.get("folder_paths"))
        updated = to_utc(r.get("updated_at"))

        def base(turn_type: str, text: str, ts: str = "", model: str = "", branch: str = "") -> Row:
            row = self.base_row(artifact)
            row.source_line = r["_rowid"]
            row.session_id = session_id
            row.project_path = project
            row.git_branch = branch
            row.timestamp_utc = ts or updated
            row.model = model
            row.turn_type = turn_type
            row.text = compact(text)
            return row

        thread, err, raw = self._decode(r)
        if thread is None:
            label = "unparseable record %d (%s)" % (r["_rowid"], err)
            yield from error_rows(self, artifact, [(r["_rowid"], label, raw)], session_id, project)
            return

        snap = thread.get("initial_project_snapshot")
        if not isinstance(snap, dict):
            snap = {}
        worktrees = [w for w in (snap.get("worktree_snapshots") or []) if isinstance(w, dict)]
        if not project and worktrees:
            project = str(worktrees[0].get("worktree_path") or "")
        branches = [
            (w.get("worktree_path") == project, str(w["git_state"]["current_branch"]))
            for w in worktrees
            if isinstance(w.get("git_state"), dict) and w["git_state"].get("current_branch")
        ]
        branch = max(branches, key=lambda b: b[0])[1] if branches else ""
        m = thread.get("model")
        if not isinstance(m, dict):
            m = {}
        model = "/".join(str(x) for x in (m.get("provider"), m.get("model")) if x)
        if not updated:
            updated = to_utc(thread.get("updated_at"))

        parent = r.get("parent_id") or (
            (thread.get("subagent_context") or {}).get("parent_thread_id")
            if isinstance(thread.get("subagent_context"), dict)
            else ""
        )
        start_ts = to_utc(snap.get("timestamp")) or to_utc(r.get("created_at")) or updated
        yield base(
            "system",
            " ".join(
                x
                for x in (
                    "thread start:",
                    str(thread.get("title") or r.get("summary") or ""),
                    "version=%s" % thread["version"] if thread.get("version") else "",
                    "parent=%s" % parent if parent else "",
                )
                if x
            ),
            start_ts,
            model,
            branch,
        )
        if m.get("model"):
            text = "model: %s" % m["model"]
            if m.get("provider"):
                text += " provider=%s" % m["provider"]
            yield base("system", text, start_ts, model, branch)
        for key, value in self._grants(thread):
            yield base(
                "system",
                "permission setting: %s=%s (thread blob, as of updated_at)"
                % (key, setting_value(value)),
                "",
                model,
                branch,
            )

        errors: list = []
        for kind, text, tool_name, tool_id in self._messages(thread, r["_rowid"], errors):
            if kind == "thinking" and not opts.include_thinking:
                continue
            if not text and kind not in ("tool_use", "tool_result"):
                continue
            row = base(kind, text, "", model, branch)
            row.tool_name = tool_name
            row.tool_use_id = tool_id
            yield row
        yield from error_rows(self, artifact, errors, session_id, project)

    @staticmethod
    def _grants(thread: dict) -> Iterator[tuple[str, object]]:
        """(dotted key, value) per thread-scoped grant: the agent profile,
        each granted write path and network host, and each sandbox escape
        flag that is set (`DbSandboxGrants`, db.rs:91-122 at a84689073d29)."""
        if thread.get("profile") not in (None, ""):
            yield "profile", thread["profile"]
        grants = thread.get("sandbox_grants")
        if not isinstance(grants, dict):
            return
        for key in ("write_paths", "network_hosts"):
            entries = grants.get(key)
            if isinstance(entries, list):
                for e in entries:
                    yield "sandbox_grants.%s" % key, e
        for key in SANDBOX_FLAGS:
            if grants.get(key) is True:
                yield "sandbox_grants.%s" % key, True

    @staticmethod
    def _decode(r: dict) -> tuple[dict | None, str, str]:
        """(thread, "", "") for a blob that decodes to a JSON object, else
        (None, reason, the stored value as text). A `json` row's stored
        value is its text, decoded UTF-8 with `errors="replace"`; a `zstd`
        row's is its compressed bytes as lowercase hex, since they have no
        faithful text form and a truncated frame can decompress to nothing,
        and its reason ends `stored zstd blob as hex`."""
        data = r.get("data")
        if data is None:
            return None, "no data", ""
        binary = isinstance(data, (bytes, bytearray))
        stored = bytes(data) if binary else str(data).encode("utf-8")
        is_zstd = str(r.get("data_type") or "").lower() == "zstd"
        try:
            raw = decompress(stored) if is_zstd else stored
            thread = json.loads(raw.decode("utf-8", errors="replace"))
            if not isinstance(thread, dict):
                raise ValueError("not a JSON object")
        except Exception as e:  # noqa: BLE001 - ZstdError, the stream reader's errors, ValueError
            if is_zstd:
                reason = "%s: %s; stored zstd blob as hex" % (type(e).__name__, e)
                return None, reason, stored.hex()
            return None, "%s: %s" % (type(e).__name__, e), stored.decode("utf-8", errors="replace")
        return thread, "", ""

    def _messages(
        self, thread: dict, rowid: int, errors: list
    ) -> Iterator[tuple[str, str, str, str]]:
        """(turn_type, text, tool_name, tool_use_id) in transcript order. A
        `messages[]` item, or a content, segment, tool use or tool result
        item inside one, of a shape not recognised is appended to `errors`
        as (rowid, `unparseable record <N> (<reason>)`, the item as JSON),
        N the message's 1-based position in `messages[]`."""
        messages = thread.get("messages")
        if messages is None:
            return
        if not isinstance(messages, list):
            reason = "unparseable record 0 (messages is not a list)"
            errors.append((rowid, reason, record_json(messages)))
            return

        def bad(n: int, reason: str, item) -> None:
            errors.append((rowid, "unparseable record %d (%s)" % (n, reason), record_json(item)))

        for n, msg in enumerate(messages, 1):
            if isinstance(msg, str):
                yield "system", msg.lower(), "", ""
            elif not isinstance(msg, dict):
                bad(n, "unknown message variant", msg)
            elif "User" in msg:
                yield from self._user(msg["User"], n, bad)
            elif "Agent" in msg:
                yield from self._agent(msg["Agent"], n, bad)
            elif "Compaction" in msg:
                c = msg["Compaction"]
                if isinstance(c, dict) and isinstance(c.get("Summary"), str):
                    yield "system", "compaction: " + c["Summary"], "", ""
                elif isinstance(c, dict) and "ProviderNative" in c:
                    yield "system", "compaction: provider native", "", ""
                else:
                    bad(n, "unknown Compaction variant", msg)
            elif "role" in msg:
                yield from self._legacy(msg, n, bad)
            else:
                bad(n, "unknown message variant", msg)

    @staticmethod
    def _user(u, n: int, bad) -> Iterator[tuple[str, str, str, str]]:
        # One row per prompt: text, mentions and images of one User message
        # are joined so sessions.jsonl counts prompts, not content items. A
        # content object of an unknown variant stays in the prompt text as
        # JSON; an item that is not an object or string goes to `bad`.
        if not isinstance(u, dict):
            bad(n, "User message is not an object", {"User": u})
            return
        content = u.get("content")
        if isinstance(content, (str, dict)):
            content = [content]
        elif content is not None and not isinstance(content, list):
            bad(n, "User content is not a list", content)
            content = []
        parts = []
        for k, c in enumerate(content or []):
            if isinstance(c, str):
                parts.append(c)
            elif not isinstance(c, dict):
                bad(n, "unknown User content variant, content[%d]" % k, c)
            else:
                if isinstance(c.get("Text"), str):
                    parts.append(c["Text"])
                elif "Mention" in c:
                    parts.append(mention_text(c["Mention"]))
                elif "Image" in c:
                    parts.append("[image]")
                else:
                    parts.append(compact_json(c))
        yield "user", "\n".join(parts), "", ""

    @staticmethod
    def _agent(a, n: int, bad) -> Iterator[tuple[str, str, str, str]]:
        if not isinstance(a, dict):
            bad(n, "Agent message is not an object", {"Agent": a})
            return
        results = a.get("tool_results")
        if results is not None and not isinstance(results, dict):
            bad(n, "Agent tool_results is not an object", results)
        if not isinstance(results, dict):
            results = {}
        done = set()

        def result(key, res: dict):
            text = content_text(res.get("content"))
            if not text and res.get("output") is not None:
                text = (
                    content_text(res["output"])
                    if not isinstance(res["output"], dict)
                    else compact_json(res["output"])
                )
            if res.get("is_error"):
                text = "[error] " + text
            return (
                "tool_result",
                text,
                str(res.get("tool_name") or ""),
                str(res.get("tool_use_id") or key),
            )

        content = a.get("content")
        if isinstance(content, (str, dict)):
            content = [content]
        elif content is not None and not isinstance(content, list):
            bad(n, "Agent content is not a list", content)
            content = []
        for k, c in enumerate(content or []):
            if isinstance(c, str):
                yield "assistant", c, "", ""
            elif not isinstance(c, dict):
                bad(n, "unknown Agent content variant, content[%d]" % k, c)
            elif isinstance(c.get("Text"), str):
                yield "assistant", c["Text"], "", ""
            elif "Thinking" in c:
                t = c["Thinking"]
                yield "thinking", (t.get("text") if isinstance(t, dict) else str(t)) or "", "", ""
            elif "RedactedThinking" in c:
                yield "thinking", "[redacted thinking]", "", ""
            elif isinstance(c.get("ToolUse"), dict):
                tu = c["ToolUse"]
                tid = str(tu.get("id") or "")
                yield "tool_use", tool_input_text(tu), str(tu.get("name") or ""), tid
                # The result follows its call, so the timeline reads in order.
                if isinstance(results.get(tid), dict):
                    done.add(tid)
                    yield result(tid, results[tid])
            elif "Image" in c:
                yield "assistant", "[image]", "", ""
            else:
                bad(n, "unknown Agent content variant, content[%d]" % k, c)
        for key, res in results.items():
            if key in done:
                continue
            if isinstance(res, dict):
                yield result(key, res)
            else:
                bad(n, "Agent tool_results entry %s is not an object" % key, res)

    @staticmethod
    def _legacy(msg: dict, n: int, bad) -> Iterator[tuple[str, str, str, str]]:
        role = str(msg.get("role") or "").lower()
        kind = "user" if role == "user" else "assistant" if role == "assistant" else "system"
        if isinstance(msg.get("text"), str):
            yield kind, msg["text"] if kind != "system" else "%s: %s" % (role, msg["text"]), "", ""
        for k, seg in enumerate(msg.get("segments") or []):
            st = str(seg.get("type") or "").lower() if isinstance(seg, dict) else ""
            if st == "text":
                yield kind, str(seg.get("text") or ""), "", ""
            elif st == "thinking":
                yield "thinking", str(seg.get("text") or ""), "", ""
            elif st == "redactedthinking":
                yield "thinking", "[redacted thinking]", "", ""
            else:
                bad(n, "unknown segment variant, segments[%d]" % k, seg)
        for k, tu in enumerate(msg.get("tool_uses") or []):
            if not isinstance(tu, dict):
                bad(n, "tool_uses[%d] is not an object" % k, tu)
            else:
                yield (
                    "tool_use",
                    tool_input_text(tu),
                    str(tu.get("name") or ""),
                    str(tu.get("id") or ""),
                )
        for k, res in enumerate(msg.get("tool_results") or []):
            if not isinstance(res, dict):
                bad(n, "tool_results[%d] is not an object" % k, res)
            else:
                text = content_text(res.get("content"))
                if res.get("is_error"):
                    text = "[error] " + text
                yield "tool_result", text, "", str(res.get("tool_use_id") or "")


__all__ = [
    "ZedParser",
    "content_text",
    "decompress",
    "first_folder",
    "record_json",
    "tool_input_text",
]
