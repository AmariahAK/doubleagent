"""Zed agent panel threads.

Validated against source, zed-industries/zed at a84689073d29 and, for
the settings, `db.sqlite` stores, denials, scratch directories and drafts,
at 9cd14daad768 (see `research/zed.md`), with a synthetic fixture; no real
install was checked, and every row the 9cd14daad768 review added is
source-derived, not observed on any real install. Files, relative to the
Zed data directory (`.local/share/zed`, `Library/Application Support/Zed`,
`AppData/Local/Zed`, or the Flatpak `.var/app/dev.zed.Zed*/data/zed`), and
to the config directory (`.config/zed`, `AppData/Roaming/Zed`, or
`.var/app/dev.zed.Zed*/config/zed`):

* `threads/threads.db` (rollback journal, so a `-journal` may sit beside it):
  table `threads(id, summary, updated_at, data_type, data, parent_id,
  folder_paths, folder_paths_order, created_at)`. `id` is the session id,
  `folder_paths` the project paths joined by newlines, `updated_at` and
  `created_at` RFC 3339. `data` is zstd-compressed JSON when `data_type` is
  `zstd` (decoded with the `zstandard` package) and raw UTF-8 JSON when
  `json`.
  The thread JSON, `version` `0.3.0`: `title`, `updated_at`,
  `initial_project_snapshot.timestamp`,
  `initial_project_snapshot.worktree_snapshots[].worktree_path`,
  `.git_state.current_branch` and `.git_state.remote_url`, `model.provider`, `model.model`,
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
  The blob's `sandboxed_terminal_temp_dir` (macOS only) is a
  `scratch directory: <path> (sandboxed terminal temp directory of thread
  <id>) (thread blob, as of updated_at)` row after the grant rows, with the
  path as `project_path` and no `session_id`, so the thread stays counted
  under its project; its `draft_prompt` (a list of ACP `ContentBlock`s,
  `type` `text`, `resource_link`, `resource`, `image`, `audio`) is an
  `unsent draft: <text> (thread blob, as of updated_at)` row after the
  messages.
* `db/0-<channel>/db.sqlite` (WAL), all `system` rows:
  - table `sidebar_threads(thread_id, session_id, agent_id, title,
    title_override, updated_at, interacted_at, folder_paths, archived,
    main_worktree_paths)`. A row with `agent_id` set is an external ACP agent
    thread whose transcript is not in `threads.db`: `external agent thread
    (no transcript in threads.db): agent=<id> title=<title>[ archived]` at
    `interacted_at`, else `updated_at`. A native row (`agent_id` NULL) with a
    `session_id` is the thread's sidebar state: `sidebar thread:
    title=<title> archived=<true|false> interacted_at=<time|-> main_worktree=
    <path|->` at `updated_at`, with the thread id. It is not a secondary
    source: it repeats no event of `threads.db` and is deleted with the
    thread. A native row with no `session_id` is a draft and has no row of
    its own.
  - table `trusted_worktrees(absolute_path, user_name, host_name)`:
    `permission setting: trusted_worktrees.<path>=true[ host=<user>@<host>]
    (from <file> trusted_worktrees, file mtime)`, `project_path` the path.
  - table `scoped_kv_store(namespace, key, value)`, namespace
    `agent_draft_prompts` (key the hyphenated `sidebar_threads.thread_id`,
    value a JSON array of ACP `ContentBlock`s): `unsent draft: <text>` at
    the draft's sidebar `updated_at`, `project_path` its first folder, or
    with ` (from <file> agent_draft_prompts, file mtime)` at the file's
    modification time when the sidebar row is gone; namespace
    `created_git_worktrees` (key `<host>` newline `<worktree path>`, `local`
    for this machine, value `{created_at_seconds, created_at_subsec_nanos}`):
    `scratch directory: <path> (Zed-created git worktree[ of <main>][
    host=<host>]) (from <file> created_git_worktrees, created_at)` at that
    time, `project_path` the worktree, `<main>` the
    `sidebar_threads.main_worktree_paths` of a thread whose `folder_paths`
    holds the worktree, else the `archived_git_worktrees.main_repo_path`.
  - tables `archived_git_worktrees(id, worktree_path, main_repo_path,
    branch_name, staged_commit_hash, unstaged_commit_hash,
    original_commit_hash)` and `thread_archived_worktrees(thread_id,
    archived_worktree_id)`: `archived worktree: <worktree_path> of
    <main_repo_path> branch=<b> staged=<hash> unstaged=<hash>
    original=<hash> ref=refs/archived-worktrees/<id> (from <file>
    archived_git_worktrees, file mtime)`, one per linked thread with its
    `session_id`, `project_path` the main repository; the archive time is not
    recorded.
  - table `sidebar_terminal_threads(title, custom_title, created_at,
    working_directory, folder_paths)`: `sidebar terminal: <title> cwd=<dir>`
    at `created_at`, `project_path` the first folder, no `session_id`.
  A value in `scoped_kv_store` that does not decode is `parser: unparseable
  record <rowid> (<namespace ...>: <reason>): <value>` at the end of the file.
* `settings.json` and `global_settings.json` in the config directory (JSONC,
  read with `parse_jsonc`): one `permission setting: <key>=<value> (from
  <file>, file mtime)` row per leaf of `agent.tool_permissions` (`default`,
  `tools.<tool>.default`, one per `always_allow`, `always_deny` and
  `always_confirm` entry `{pattern, case_sensitive}` as compact JSON) and of
  `agent.sandbox_permissions` (one per `network_hosts` and `write_paths`
  entry), and per `agent.always_allow_tool_actions` (the legacy boolean),
  `agent_servers.<id>.default_mode` and `session.trust_all_worktrees`, in
  the top level and in each `dev`, `nightly`, `preview`, `stable`, `macos`,
  `linux`, `windows` and `profiles.<name>.settings` block, whose name
  prefixes the key. A project's `.zed/settings.json` cannot hold these keys
  (it parses as `ProjectSettingsContent`) and is not read. A file that is
  not a JSON object is one `parser: <file> is not a JSON object` row.

There are no per-message timestamps. Every message row carries the thread's
`updated_at` (approximate: it is the last write, not the message time); the
thread-start row carries `initial_project_snapshot.timestamp`, falling back
to `created_at`. `source_line` is the SQLite `rowid` of the thread or
sidebar row. The git branch is the one captured at thread start, and so
is the remote: the `git_state.remote_url` of the snapshot whose
`worktree_path` is the thread's project (else of the first snapshot, as
for the branch) is a `system` row `git remote: <url>` at the thread-start
time, right after the thread-start row (issue 253).

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

Per-call decisions: a failed tool result (`is_error` true) whose text is
`Permission to run tool denied by user` is followed by `permission
decision: denied`, and one whose text is a rule's automatic denial
(`Blocked by global default: deny`, `Command blocked by security rule for
<tool> tool`, `<tool> tool is disabled`, `Blocked by built-in security
rule. ...`, the invalid-terminal-command, invalid-regex and
unsupported-shell messages) by `permission decision: auto_denied
reason=<text>`, each with the call's `tool_name` and `tool_use_id`. An
approval, once or always, leaves no record in the thread, so it has no row;
an "always" choice shows only as the settings rows above.

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
import uuid
from collections.abc import Iterator

import zstandard

from ..inputs import Artifact
from ..model import GIT_REMOTE_PREFIX, Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import Options, Parser, compact_json, error_rows, file_mtime, setting_value
from .gemini_cli import parse_jsonc

DATA_DIR = r"(?:\.local/share/zed|Library/Application Support/Zed|AppData/Local/Zed|\.var/app/dev\.zed\.Zed[A-Za-z]*/data/zed)"
SANDBOX_FLAGS = ("network_any_host", "allow_fs_write_all", "unsandboxed", "sandbox_fallback")
CONFIG_DIR = r"(?:\.config/zed|AppData/Roaming/Zed|\.var/app/dev\.zed\.Zed[A-Za-z]*/config/zed)"
THREADS_RX = re.compile(r"^" + DATA_DIR + r"/threads/threads\.db$")
SIDEBAR_RX = re.compile(r"^" + DATA_DIR + r"/db/0-[^/]+/db\.sqlite$")
SETTINGS_RX = re.compile(r"^" + CONFIG_DIR + r"/(?:global_)?settings\.json$")
# Release-channel and platform override blocks of a user settings file
# (`ReleaseChannelOverrides`, `PlatformOverrides`), each a whole settings
# object of its own.
SETTINGS_OVERRIDES = ("dev", "nightly", "preview", "stable", "macos", "linux", "windows")
USER_DENIAL = "Permission to run tool denied by user"
# The texts `ToolPermissionDecision::Deny` carries when the rules deny a
# call with no prompt (crates/agent/src/tool_permissions.rs at 9cd14da).
AUTO_DENIAL_RX = re.compile(
    r"(?:Blocked by global default: deny"
    r"|Command blocked by security rule for \S+ tool"
    r"|\S+ tool is disabled"
    r"|Blocked by built-in security rule\..*"
    r"|The terminal command could not be approved because .*"
    r"|The \S+ tool cannot run because \d+ regex patterns? failed to compile\..*"
    r'|The .+ shell does not support "always allow" patterns .*)',
    re.S,
)


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


def acp_blocks_text(blocks) -> str:
    """Text of a list of ACP `ContentBlock`s (`{"type": "text", "text"}`,
    `resource_link` and `resource` by URI, `image` and `audio` as markers),
    as a draft prompt stores them; another block is compact JSON."""
    if isinstance(blocks, dict):
        blocks = [blocks]
    if not isinstance(blocks, list):
        return compact_json(blocks)
    parts = []
    for b in blocks:
        kind = b.get("type") if isinstance(b, dict) else None
        if isinstance(b, str):
            parts.append(b)
        elif kind == "text" and isinstance(b.get("text"), str):
            parts.append(b["text"])
        elif kind == "resource_link" and isinstance(b.get("uri"), str):
            parts.append("[mention] " + b["uri"])
        elif kind == "resource" and isinstance(b.get("resource"), dict):
            uri = b["resource"].get("uri")
            parts.append("[mention] " + (uri if isinstance(uri, str) else compact_json(uri)))
        elif kind in ("image", "audio"):
            parts.append("[%s]" % kind)
        else:
            parts.append(compact_json(b))
    return "\n".join(parts)


def denial_text(res: dict) -> str:
    """The `permission decision:` row text for a failed tool result whose
    text is one Zed writes when a call is denied, else "". An approval
    leaves no record, so only denials have a row."""
    if not res.get("is_error"):
        return ""
    text = content_text(res.get("content")).strip()
    if text == USER_DENIAL:
        return "permission decision: denied"
    if AUTO_DENIAL_RX.fullmatch(text):
        return "permission decision: auto_denied reason=" + text
    return ""


def thread_key(blob) -> str:
    """A `sidebar_threads.thread_id` (16 raw UUID bytes) as the hyphenated
    string the key-value store keys drafts by, else ""."""
    if isinstance(blob, (bytes, bytearray)) and len(blob) == 16:
        return str(uuid.UUID(bytes=bytes(blob)))
    return str(blob or "")


def flatten_setting(key: str, value) -> Iterator[tuple[str, object]]:
    """(dotted key, value) per leaf of a settings value: one per object
    member, recursively, and one per list entry."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from flatten_setting("%s.%s" % (key, k), v)
    elif isinstance(value, list):
        for e in value:
            yield key, e
    else:
        yield key, value


class ZedParser(Parser):
    agent = "zed"
    name = "zed"

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return bool(THREADS_RX.match(rel) or SIDEBAR_RX.match(rel) or SETTINGS_RX.match(rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if SETTINGS_RX.match(artifact.rel):
            yield from self._parse_settings(artifact)
            return
        if not is_sqlite(artifact.disk_path):
            yield self._file_error(artifact, "not a SQLite database")
            return
        try:
            if THREADS_RX.match(artifact.rel):
                yield from self._parse_threads(artifact, opts)
            else:
                yield from self._parse_sidebar(artifact)
        except sqlite3.DatabaseError as e:
            yield self._file_error(artifact, "SQLite error: %s" % e)

    def _file_error(self, artifact: Artifact, message: str) -> Row:
        """The one `parser: <message>` row for a file that cannot be read."""
        row = self.base_row(artifact)
        row.turn_type = "system"
        row.text = "parser: " + message
        return row

    def _state_row(
        self,
        artifact: Artifact,
        text: str,
        ts: str,
        source_line: int,
        session_id: str = "",
        project: str = "",
    ) -> Row:
        """A `system` row of `artifact` with the given text and context."""
        row = self.base_row(artifact)
        row.source_line = source_line
        row.session_id = session_id
        row.project_path = project
        row.timestamp_utc = ts
        row.turn_type = "system"
        row.text = compact(text)
        return row

    # -- settings.json, global_settings.json ----------------------------------------
    def _parse_settings(self, artifact: Artifact) -> Iterator[Row]:
        """One `permission setting:` row per standing permission entry of a
        user settings file, at the file's modification time."""
        try:
            raw = artifact.disk_path.read_bytes()
        except OSError as e:
            yield self._file_error(artifact, "unreadable: %s" % e)
            return
        if not raw.strip():
            return
        try:
            doc = parse_jsonc(raw)
        except ValueError:
            doc = None
        if not isinstance(doc, dict):
            yield self._file_error(artifact, "%s is not a JSON object" % artifact.rel)
            return
        ts = file_mtime(artifact)
        for key, value in self._settings_entries(doc):
            text = "permission setting: %s=%s (from %s, file mtime)" % (
                key,
                setting_value(value),
                artifact.rel,
            )
            yield self._state_row(artifact, text, ts, 1)

    @staticmethod
    def _settings_entries(doc: dict) -> Iterator[tuple[str, object]]:
        """(dotted key, value) per entry of `agent.tool_permissions`,
        `agent.sandbox_permissions`, the legacy
        `agent.always_allow_tool_actions`, `agent_servers.<id>.default_mode`
        and `session.trust_all_worktrees`, in the top level, each
        release-channel and platform override block and each
        `profiles.<name>.settings`, the key prefixed with the block's."""
        layers: list[tuple[str, dict]] = [("", doc)]
        for name in SETTINGS_OVERRIDES:
            if isinstance(doc.get(name), dict):
                layers.append((name + ".", doc[name]))
        profiles = doc.get("profiles")
        if isinstance(profiles, dict):
            for name, prof in profiles.items():
                if isinstance(prof, dict) and isinstance(prof.get("settings"), dict):
                    layers.append(("profiles.%s.settings." % name, prof["settings"]))
        for prefix, block in layers:
            agent = block.get("agent")
            if isinstance(agent, dict):
                for sub in ("tool_permissions", "sandbox_permissions"):
                    if sub in agent:
                        yield from flatten_setting(prefix + "agent." + sub, agent[sub])
                if "always_allow_tool_actions" in agent:
                    legacy = agent["always_allow_tool_actions"]
                    yield prefix + "agent.always_allow_tool_actions", legacy
            servers = block.get("agent_servers")
            if isinstance(servers, dict):
                for sid, cfg in servers.items():
                    if isinstance(cfg, dict) and "default_mode" in cfg:
                        yield prefix + "agent_servers.%s.default_mode" % sid, cfg["default_mode"]
            session = block.get("session")
            if isinstance(session, dict) and "trust_all_worktrees" in session:
                yield prefix + "session.trust_all_worktrees", session["trust_all_worktrees"]

    # -- db/0-<channel>/db.sqlite -------------------------------------------------
    def _parse_sidebar(self, artifact: Artifact) -> Iterator[Row]:
        errors: list = []
        with open_copy(artifact.disk_path) as con:
            tables = table_names(con)
            sidebar = self._select(
                con,
                tables,
                "sidebar_threads",
                "select rowid as _rowid, * from sidebar_threads order by updated_at",
            )
            trusted = self._select(
                con,
                tables,
                "trusted_worktrees",
                "select rowid as _rowid, * from trusted_worktrees order by rowid",
            )
            kv = self._select(
                con,
                tables,
                "scoped_kv_store",
                "select rowid as _rowid, namespace, key, value"
                " from scoped_kv_store where namespace in ('agent_draft_prompts',"
                " 'created_git_worktrees') order by rowid",
            )
            link = "thread_archived_worktrees" in tables
            archived = self._select(
                con,
                tables,
                "archived_git_worktrees",
                "select a.rowid as _rowid, a.*, t.thread_id as _thread from"
                " archived_git_worktrees a left join thread_archived_worktrees t"
                " on t.archived_worktree_id = a.id order by a.id"
                if link
                else "select rowid as _rowid, *, null as _thread from archived_git_worktrees"
                " order by id",
            )
            terminals = self._select(
                con,
                tables,
                "sidebar_terminal_threads",
                "select rowid as _rowid, * from sidebar_terminal_threads order by created_at",
            )
        by_key = {thread_key(r.get("thread_id")): r for r in sidebar}
        for r in sidebar:
            yield from self._sidebar_row(artifact, r)
        for r in trusted:
            yield self._trusted_row(artifact, r)
        for r in kv:
            if r["namespace"] == "agent_draft_prompts":
                yield from self._draft(artifact, r, by_key, errors)
            else:
                yield from self._created_worktree(artifact, r, sidebar, archived, errors)
        for r in archived:
            yield self._archived_worktree(artifact, r, by_key)
        for r in terminals:
            title = r.get("custom_title") or r.get("title") or ""
            text = "sidebar terminal: %s cwd=%s" % (title, r.get("working_directory") or "-")
            project = first_folder(r.get("folder_paths"))
            ts = to_utc(r.get("created_at"))
            yield self._state_row(artifact, text, ts, r["_rowid"], "", project)
        yield from error_rows(self, artifact, errors)

    @staticmethod
    def _select(con: sqlite3.Connection, tables: set, table: str, sql: str) -> list[dict]:
        """The rows of `sql` as dicts, or [] when `table` does not exist."""
        if table not in tables:
            return []
        return [dict(r) for r in con.execute(sql)]

    def _sidebar_row(self, artifact: Artifact, r: dict) -> Iterator[Row]:
        """An external agent's thread (no transcript in `threads.db`), or the
        sidebar state of a native thread; a draft (no `session_id`) has no
        row of its own, only its draft prompt."""
        title = r.get("title_override") or r.get("title") or ""
        project = first_folder(r.get("folder_paths"))
        session_id = str(r.get("session_id") or "")
        if r.get("agent_id"):
            text = "external agent thread (no transcript in threads.db): agent=%s title=%s%s" % (
                r["agent_id"],
                title,
                " archived" if r.get("archived") else "",
            )
            ts = to_utc(r.get("interacted_at") or r.get("updated_at"))
            yield self._state_row(artifact, text, ts, r["_rowid"], session_id, project)
        elif session_id:
            text = "sidebar thread: title=%s archived=%s interacted_at=%s main_worktree=%s" % (
                title,
                "true" if r.get("archived") else "false",
                to_utc(r.get("interacted_at")) or "-",
                first_folder(r.get("main_worktree_paths")) or "-",
            )
            ts = to_utc(r.get("updated_at"))
            yield self._state_row(artifact, text, ts, r["_rowid"], session_id, project)

    def _trusted_row(self, artifact: Artifact, r: dict) -> Row:
        """The `permission setting:` row of one trusted project path."""
        path = str(r.get("absolute_path") or "")
        host = str(r.get("host_name") or "")
        if host and r.get("user_name"):
            host = "%s@%s" % (r["user_name"], host)
        text = "permission setting: trusted_worktrees.%s=true%s (from %s trusted_worktrees," % (
            path,
            " host=%s" % host if host else "",
            artifact.rel,
        )
        ts = file_mtime(artifact)
        return self._state_row(artifact, text + " file mtime)", ts, r["_rowid"], "", path)

    def _draft(self, artifact: Artifact, r: dict, by_key: dict, errors: list) -> Iterator[Row]:
        """`unsent draft: <text>` for an `agent_draft_prompts` entry, at the
        draft's sidebar `updated_at`, or at the file's modification time,
        saying so, when the draft has no sidebar row."""
        rowid, key, value = r["_rowid"], str(r["key"]), r["value"]
        try:
            blocks = json.loads(value)
        except (TypeError, ValueError) as e:
            label = "unparseable record %d (agent_draft_prompts %s: %s: %s)" % (
                rowid,
                key,
                type(e).__name__,
                e,
            )
            errors.append((rowid, label, str(value)))
            return
        text = acp_blocks_text(blocks)
        if not text.strip():
            return
        side = by_key.get(key)
        if side is not None:
            ts = to_utc(side.get("updated_at"))
            project = first_folder(side.get("folder_paths"))
            yield self._state_row(artifact, "unsent draft: " + text, ts, rowid, "", project)
            return
        text = "unsent draft: %s (from %s agent_draft_prompts, file mtime)" % (text, artifact.rel)
        yield self._state_row(artifact, text, file_mtime(artifact), rowid)

    def _created_worktree(
        self, artifact: Artifact, r: dict, sidebar: list, archived: list, errors: list
    ) -> Iterator[Row]:
        """`scratch directory:` for a `created_git_worktrees` entry, at the
        worktree's recorded creation time, `project_path` the worktree, and
        the main repository from the sidebar or the archived worktrees."""
        rowid, value = r["_rowid"], r["value"]
        host, _, path = str(r["key"]).partition("\n")
        try:
            rec = json.loads(value)
            seconds = rec["created_at_seconds"] + rec.get("created_at_subsec_nanos", 0) / 1e9
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            label = "unparseable record %d (created_git_worktrees: %s: %s)" % (
                rowid,
                type(e).__name__,
                e,
            )
            errors.append((rowid, label, str(value)))
            return
        main = next(
            (
                first_folder(s.get("main_worktree_paths"))
                for s in sidebar
                if s.get("main_worktree_paths")
                and path in str(s.get("folder_paths") or "").split("\n")
            ),
            "",
        ) or next((str(a["main_repo_path"]) for a in archived if a["worktree_path"] == path), "")
        text = "scratch directory: %s (Zed-created git worktree%s%s) (from %s" % (
            path,
            " of %s" % main if main else "",
            " host=%s" % host if host and host != "local" else "",
            artifact.rel,
        )
        text += " created_git_worktrees, created_at)"
        yield self._state_row(artifact, text, to_utc(seconds), rowid, "", path)

    def _archived_worktree(self, artifact: Artifact, r: dict, by_key: dict) -> Row:
        """The row of one archived worktree and one thread linked to it."""
        side = by_key.get(thread_key(r.get("_thread"))) if r.get("_thread") else None
        session_id = str((side or {}).get("session_id") or "")
        text = (
            "archived worktree: %s of %s branch=%s staged=%s unstaged=%s original=%s"
            " ref=refs/archived-worktrees/%s (from %s archived_git_worktrees, file mtime)"
        ) % (
            r.get("worktree_path") or "",
            r.get("main_repo_path") or "",
            r.get("branch_name") or "-",
            r.get("staged_commit_hash") or "-",
            r.get("unstaged_commit_hash") or "-",
            r.get("original_commit_hash") or "-",
            r.get("id"),
            artifact.rel,
        )
        project = str(r.get("main_repo_path") or "")
        ts = file_mtime(artifact)
        return self._state_row(artifact, text, ts, r["_rowid"], session_id, project)

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
        remotes = [
            (w.get("worktree_path") == project, str(w["git_state"]["remote_url"]))
            for w in worktrees
            if isinstance(w.get("git_state"), dict)
            and isinstance(w["git_state"].get("remote_url"), str)
            and w["git_state"]["remote_url"].strip()
        ]
        remote = max(remotes, key=lambda b: b[0])[1] if remotes else ""
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
        if remote:
            yield base("system", GIT_REMOTE_PREFIX + remote, start_ts, model, branch)
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

        temp_dir = thread.get("sandboxed_terminal_temp_dir")
        if isinstance(temp_dir, str) and temp_dir:
            # Its own project_path and no session_id, so the thread stays
            # counted under its project.
            text = (
                "scratch directory: %s (sandboxed terminal temp directory of thread %s)"
                " (thread blob, as of updated_at)" % (temp_dir, session_id)
            )
            yield self._state_row(artifact, text, updated, r["_rowid"], "", temp_dir)

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
        draft = thread.get("draft_prompt")
        if draft:
            text = acp_blocks_text(draft)
            if text.strip():
                text = "unsent draft: %s (thread blob, as of updated_at)" % text
                yield base("system", text, "", model, branch)
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
            name, tid = str(res.get("tool_name") or ""), str(res.get("tool_use_id") or key)
            yield "tool_result", text, name, tid
            decision = denial_text(res)
            if decision:
                yield "system", decision, name, tid

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
                    yield from result(tid, results[tid])
            elif "Image" in c:
                yield "assistant", "[image]", "", ""
            else:
                bad(n, "unknown Agent content variant, content[%d]" % k, c)
        for key, res in results.items():
            if key in done:
                continue
            if isinstance(res, dict):
                yield from result(key, res)
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
                tid = str(res.get("tool_use_id") or "")
                yield "tool_result", text, "", tid
                decision = denial_text(res)
                if decision:
                    yield "system", decision, "", tid


__all__ = [
    "ZedParser",
    "acp_blocks_text",
    "content_text",
    "decompress",
    "denial_text",
    "first_folder",
    "record_json",
    "tool_input_text",
]
