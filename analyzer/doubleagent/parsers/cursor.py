"""Cursor IDE agent conversations (issue 51).

Closed source. Validated against a real install of the Cursor IDE on macOS
(3.24.18, 3.25.9 and 3.26.13, October 2026), one step per listing, and the
3.25.9 and 3.26.13 bundles (`workbench.glass.main.js`) for the run modes;
see `research/cursor.md`, whose Parsing part this module follows (Record
schema, Joins and timestamps, Parser plan). The standalone Cursor Agent
CLI's `~/.cursor/chats` and `acp-sessions` stores are not read: no real
install has shown them. The IDE's paths are under `<ide>`, which is
`Library/Application Support/Cursor`, `.config/Cursor` or
`AppData/Roaming/Cursor`. Cursor's names: a composer is one conversation
(`composerId`), a bubble one message, reasoning block or tool call in it
(`bubbleId`), `toolFormer` a tool call's record, `yolo` auto-run.

* `<ide>/User/globalStorage/state.vscdb`, the primary store, opened through
  `sqlite_util` with its `-wal`:
  - `cursorDiskKV` `composerData:<composerId>` (`status`, `name`,
    `createdAt`, `lastUpdatedAt`, `isArchived`, `workspaceIdentifier.uri
    .fsPath`, `trackedGitRepos[].repoPath` and `.branches`,
    `fullConversationHeadersOnly[]`). A composer with `status` `none` and
    an empty header list in both layouts is a draft and yields only its
    `composerDraft:<composerId>` row (`text`): `unsent draft: <text>` at the
    composer's `createdAt`. The header list is `fullConversationHeadersOnly`
    (3.25.9) when not empty, else every `composerConvHeaders:<composerId>:
    <NNNNNN>` chunk (3.26.13, a JSON array) in suffix order, concatenated;
    each entry has `bubbleId` (with its `/s:<n>` or `/t:call-...` LF
    `fc_...` suffix), `type` and `createdAt`, and names the row
    `bubbleId:<composerId>:<bubbleId>`. A conversation's rows:
    `session name: <name>` at `createdAt`; then per entry, in list order,
    the bubble's rows; an entry with no bubble row is `parser: missing
    bubble <bubbleId>` at the entry's `createdAt`.
  - User bubble (`type` 1: `text`, `createdAt`, `modelInfo.modelName`):
    a `model: <id>` row the first time a user bubble names a model and
    `model: <old> -> <new>` when a later one names another, then the `user`
    row at `createdAt`. Every row of the turn carries that model in
    `model`; assistant records name none. `composerData.modelConfig` is
    the current selection with no history and is not read.
  - Assistant sub-bubble (`type` 2, no `toolFormerData`: `thinking.text`,
    `text`, `createdAt`, `startedAtMs`): a `thinking` row with
    `opts.include_thinking`, then an `assistant` row when `text` is not
    empty, at `createdAt`, else `startedAtMs`, else the entry's
    `createdAt`.
  - Tool bubble (`toolFormerData`: `name`, `params`, `rawArgs`, `result`,
    `toolCallId`, `additionalData.status`, `.startedAtMs`, `.blockReason`,
    `.reviewData.selectedOption`, `.approvalType`, `.allowlistOptions[]
    {id, commandName}`, `.appliedAllowlistOptionIds`; the bubble's
    `startedAtMs` and `completedAtMs`): a `tool_use` row, `params`, else
    `rawArgs`, at `startedAtMs`; when `reviewData` is present a `system`
    row `permission decision: <selectedOption> outcome=<status>
    approval=<approvalType> reason=<blockReason>`, with ` allowlisted=<the
    commandName of each applied option, else its id>` when
    `appliedAllowlistOptionIds` is present (`-` for a missing value); then
    a `tool_result` row, `result`, prefixed `[rejected] ` when
    `additionalData.status` is `rejected`, at `completedAtMs`. `tool_name`
    is `toolFormerData.name` and `tool_use_id` `toolCallId` on all three.
    A call that ran under auto-run has no `reviewData` and gets no
    permission row; the run mode in force is a standing row.
  - `composerHeaders` table (`composerId`, `createdAt`, `lastUpdatedAt`,
    `isArchived`, and `value`: `name`, `isArchived`,
    `workspaceIdentifier.uri.fsPath`, `trackedGitRepos[]`,
    `agentLocation.type`, `agentLocationHistory[]`). `project_path` is the
    header's `workspaceIdentifier.uri.fsPath`, else the composer's, else
    the first `trackedGitRepos[].repoPath`; `git_branch` the first entry
    of that repository's `branches`. A conversation whose header is
    archived (`isArchived` 1 or `value.isArchived` true; the composer's own
    `isArchived` stays null) gets `conversation archived` at the header's
    `lastUpdatedAt`. A header with no `composerData` that is not a draft
    (it has an `agentLocationHistory` entry or is archived) is a deleted
    conversation: `conversation deleted (header kept; time is the header's
    lastUpdatedAt)` at `lastUpdatedAt`. An `agentLocation.type` other than
    `local` gives `session origin: remote <type>` (bundle-derived: only
    `local` has been seen), so `records_origin` is set.
  - `agentKv:blob:<sha256>` rows, read only for deleted conversations: a
    JSON blob (`role`, `content`) whose `content` contains the id of a
    deleted composer yields a `user` or `assistant` row from `content`
    (`system prompt: <content>` for `role` `system`, `<role> message:
    <content>` for another role), with an empty `timestamp_utc`, the
    composer's session and project, and `recovered` "yes", since nothing
    else in the store holds the event. Blobs of a conversation still
    present are not read: their user text is the whole prompt with its
    context, which repeats the bubbles in a form deduplication cannot
    match. Protobuf blobs yield nothing. The plan calls these blobs
    secondary; `secondary()` decides per file and the database is the
    primary store, so the parser sets `recovered` on these rows itself.
  - Standing settings, at the file's modification time with an empty
    `session_id`, from `ItemTable`
    `src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl
    .persistentStorage.applicationUser` and
    `cursor/sandboxAutoRunSettingEnabled`: `permission setting:
    <list>=<entry> (from state.vscdb composerState, file mtime)` per entry
    of `composerState.yoloCommandAllowlist`, `yoloCommandDenylist`,
    `smartAllowlistDenylist`, `webFetchDomainAllowlist` and
    `autoApprovedModeTransitions`; `permission setting: run mode <id>=<mode>
    autoRun=<b> smartModeAutoRun=<b> fullAutoRun=<b> sandbox=<b> (from ...)`
    per `composerState.modes4` entry, the mode derived from the flags and
    the sandbox key (`RUN_MODES`); `permission setting: <switch>=<value>
    (from ...)` per boolean switch in `SWITCHES`; and `model last used:
    <id> (from state.vscdb aiSettings.modelLastUsedAt)` per entry of
    `aiSettings.modelLastUsedAt`, at its own time.
* `.cursor/projects/<sanitized cwd>/agent-transcripts/<composerId>/
  <composerId>.jsonl`, the agent worker's copy, a secondary source
  (`secondary()`): `{role, message{content[{type text|tool_use, text,
  name, input}]}}` and `{type: turn_ended}` lines. A user text block is
  `<timestamp>Thursday, Oct 1, 2026, 6:00 AM (UTC-4)</timestamp>` LF
  `<user_query>Q</user_query>`; the row's text is Q and its time the tag
  converted to UTC with its offset, at minute precision. A block whose
  wrapper does not parse keeps its whole text and an empty time. Assistant
  text blocks are `assistant` rows and tool blocks `tool_use` rows
  (`tool_name` the transcript's CamelCase name, `text` the compact JSON of
  `input`), with an empty time, so they pair on text alone; the
  transcript's tool names differ from `toolFormerData.name` and are not
  mapped, so a live conversation's transcript `tool_use` rows do not pair
  with the bubbles' and are kept beside them. `turn_ended` lines and lines
  of any other shape yield nothing. `session_id` is the file name and
  `project_path` the composer's in the home's `state.vscdb`.
  `secondary_tolerance()` is 60 seconds: the tag has minute precision and
  the bubble's `createdAt` milliseconds.
* `.cursor/ai-tracking/ai-code-tracking.db` (not secondary: it repeats no
  event), each table read when present: `ai_code_hashes` (`fileName`,
  `source`, `model`, `requestId`, `conversationId`, `timestamp`) as `ai
  code: <fileName> source=<source> model=<model> request=<requestId>` at
  `timestamp`; `conversation_summaries` (`conversationId`, `title`,
  `tldr`, `model`, `updatedAt`) as `conversation summary: <title>: <tldr>`
  at `updatedAt`; `ai_deleted_files` (`gitPath`, `composerId`,
  `conversationId`, `model`, `deletedAt`) as `file deleted by agent:
  <gitPath> model=<model>` at `deletedAt`; `scored_commits`
  (`commitHash`, `branchName`, `linesAdded`, `linesDeleted`, `scoredAt`)
  as `scored commit: <commitHash> branch=<branchName> +<linesAdded>
  -<linesDeleted>` at `scoredAt`, with no session. Only `ai_code_hashes`
  has been seen populated; the other three are fixture only.
* `<ide>/User/globalStorage/conversation-search.db` (not secondary):
  `conversations` (`id`, `title`, `source`, `is_archived`, `updated_at`),
  one `conversation index: <title> source=<source> archived=<is_archived>`
  row per row with a title, at `updated_at`.
* `.cursor/cli-config.json` (`approvalMode`, `permissions.allow[]`,
  `permissions.deny[]`, `sandbox.mode`) and `.cursor/permissions.json` in
  the home or a project (`approvalMode`, `allowlists.mcp[]`,
  `allowlists.terminal[]`, and top-level `allowInstructions[]` and
  `blockInstructions[]`; bundle-derived, fixture only): `permission
  setting: <key>=<value> (from <path>, file mtime)` per value or entry.

The project path, the session and the model of an ai-tracking,
conversation-search or transcript row come from the home's `state.vscdb`
when it is there (`composerHeaders` and `composerData` by composer id).
Bad lines of the transcript are `error_rows` rows. A `cursorDiskKV`,
`composerHeaders` or `ItemTable` value that should be JSON and is not is
an error entry `unparseable record <rowid> (<key>: <reason>)` with the value
as stored, reported per composer with its session and project. A database
that is not SQLite is one `parser: not a SQLite database` row, a SQLite
error one `parser: SQLite error: <message>` row, and a JSON settings file
that does not decode one `parser:` row.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..inputs import Artifact, error_reason
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import format_utc, to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    iter_jsonl,
    setting_value,
    text_of,
    track_change,
)

IDE = r"(?:Library/Application Support|\.config|AppData/Roaming)/Cursor"
IDE_PARENTS = ("Library/Application Support/Cursor", ".config/Cursor", "AppData/Roaming/Cursor")
STATE_RX = re.compile(r"^%s/User/globalStorage/state\.vscdb$" % IDE)
SEARCH_RX = re.compile(r"^%s/User/globalStorage/conversation-search\.db$" % IDE)
TRANSCRIPT_RX = re.compile(r"^\.cursor/projects/[^/]+/agent-transcripts/[^/]+/([^/]+)\.jsonl$")
TRACKING_RX = re.compile(r"^\.cursor/ai-tracking/ai-code-tracking\.db$")
CLI_CONFIG_RX = re.compile(r"^\.cursor/cli-config\.json$")
PERMISSIONS_RX = re.compile(r"^\.cursor/permissions\.json$")

SETTINGS_KEY = (
    "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl"
    ".persistentStorage.applicationUser"
)
SANDBOX_KEY = "cursor/sandboxAutoRunSettingEnabled"
STANDING_LISTS = (
    "yoloCommandAllowlist",
    "yoloCommandDenylist",
    "smartAllowlistDenylist",
    "webFetchDomainAllowlist",
    "autoApprovedModeTransitions",
)
SWITCHES = (
    "yoloEnableRunEverything",
    "yoloDeleteFileDisabled",
    "yoloMcpToolsDisabled",
    "yoloOutsideWorkspaceDisabled",
    "autoApproveModeTransitions",
    "autoAcceptWebSearchTool",
    "autoApplyFilesOutsideContext",
    "doNotShowYoloModeWarningAgain",
    "doNotShowFullYoloModeWarningAgain",
    "useLegacyTerminalTool",
    "playwrightProtection",
    "mcpAuthBlocking",
)
COMPOSER_SOURCE = "(from state.vscdb composerState, file mtime)"
DELETED_TEXT = "conversation deleted (header kept; time is the header's lastUpdatedAt)"

# `<timestamp>Thursday, Oct 1, 2026, 6:00 AM (UTC-4)</timestamp>` LF
# `<user_query>Q</user_query>`, the worker's wrapper of a user text block.
WRAPPER_RX = re.compile(
    r"^<timestamp>([^<]*)</timestamp>\s*<user_query>(.*)</user_query>\s*$", re.DOTALL
)
TAG_RX = re.compile(
    r"^\s*[A-Za-z]+,\s+([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}):(\d{2})"
    r"\s*([AaPp][Mm])\s*\(UTC(?:([+-])(\d{1,2})(?::?(\d{2}))?)?\)\s*$"
)
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")

TRACKING_TABLES = {
    "ai_code_hashes": (
        "fileName",
        "source",
        "model",
        "requestId",
        "conversationId",
        "timestamp",
    ),
    "conversation_summaries": ("conversationId", "title", "tldr", "model", "updatedAt"),
    "ai_deleted_files": ("gitPath", "composerId", "conversationId", "model", "deletedAt"),
    "scored_commits": ("commitHash", "branchName", "linesAdded", "linesDeleted", "scoredAt"),
}
SEARCH_COLUMNS = ("id", "title", "source", "is_archived", "updated_at")


def run_mode(mode: dict, sandbox: bool) -> str:
    """The UI label of a `modes4` entry's run mode, derived from its
    `autoRun`, `smartModeAutoRun` and `fullAutoRun` flags and the sandbox
    key (research/cursor.md, Run mode and standing lists); no run-mode
    string is stored."""
    if mode.get("fullAutoRun") is True:
        return "Run Everything"
    if mode.get("autoRun") is not True:
        return "Ask Every Time"
    label = "Auto-review" if mode.get("smartModeAutoRun") is True else "Allowlist"
    return label + " (with Sandbox)" if sandbox else label


def tag_time(tag: str) -> str:
    """The transcript's `<timestamp>` tag as a UTC timeline timestamp, or ""
    when it does not parse. The tag is local time to the minute with its
    UTC offset in parentheses."""
    m = TAG_RX.match(tag)
    if not m:
        return ""
    mon, day, year, hour, minute, ampm, sign, off_h, off_m = m.groups()
    if mon.lower() not in MONTHS:
        return ""
    hour_n = int(hour) % 12 + (12 if ampm.lower() == "pm" else 0)
    try:
        local = datetime(int(year), MONTHS.index(mon.lower()) + 1, int(day), hour_n, int(minute))
    except ValueError:
        return ""
    offset = timedelta(hours=int(off_h or 0), minutes=int(off_m or 0))
    if sign == "-":
        offset = -offset
    return format_utc((local - offset).replace(tzinfo=timezone.utc))


def unwrap_query(text: str) -> tuple[str, str]:
    """(query, timestamp) of a transcript user text block: the text inside
    `<user_query>` and the tag's time, or the whole text and "" when the
    wrapper or its tag does not parse."""
    m = WRAPPER_RX.match(text)
    if m:
        when = tag_time(m.group(1))
        if when:
            return m.group(2), when
    return text, ""


def _as_text(value) -> str:
    """A database value as text: bytes decoded as UTF-8 with replacement."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).decode("utf-8", errors="replace")
    return "" if value is None else str(value)


def _object(value) -> dict:
    return value if isinstance(value, dict) else {}


def _decode(rowid: int, key: str, value, errors: list):
    """The JSON value of a row, or None, appending an error entry when it
    does not decode."""
    text = _as_text(value)
    try:
        return json.loads(text)
    except ValueError as e:
        errors.append((rowid, "unparseable record %d (%s: %s)" % (rowid, key, e), text))
        return None


def _prefixed(con: sqlite3.Connection, prefix: str) -> list[tuple[int, str, object]]:
    """The `cursorDiskKV` rows whose key starts with `prefix`, in key order,
    by a range over the key so the table's index is used."""
    end = prefix[:-1] + chr(ord(prefix[-1]) + 1)
    sql = "select rowid, key, value from cursorDiskKV where key >= ? and key < ? order by key"
    return [(int(r[0]), _as_text(r[1]), r[2]) for r in con.execute(sql, (prefix, end))]


def _one(con: sqlite3.Connection, key: str) -> tuple[int, object] | None:
    row = con.execute("select rowid, value from cursorDiskKV where key = ?", (key,)).fetchone()
    return (int(row[0]), row[1]) if row else None


def _select(con: sqlite3.Connection, table: str, wanted: tuple[str, ...]) -> list[dict]:
    """Every row of `table` as a dict of the `wanted` columns it has, plus
    `_rowid`, in rowid order."""
    have = {r[1] for r in con.execute("pragma table_info(%s)" % table)}
    cols = [c for c in wanted if c in have]
    if not cols:
        return []
    sql = 'select rowid as _rowid, %s from "%s" order by rowid' % (
        ", ".join('"%s"' % c for c in cols),
        table,
    )
    return [dict(r) for r in con.execute(sql)]


def _project(*docs: dict) -> tuple[str, str]:
    """(project_path, git_branch) of a composer from its header value and
    its `composerData`, in that order of preference."""
    path = ""
    for doc in docs:
        path = str(_object(_object(doc.get("workspaceIdentifier")).get("uri")).get("fsPath") or "")
        if path:
            break
    repos = [r for doc in docs for r in doc.get("trackedGitRepos") or [] if isinstance(r, dict)]
    if not path and repos:
        path = str(repos[0].get("repoPath") or "")
    for repo in repos:
        if str(repo.get("repoPath") or "") == path:
            branches = repo.get("branches") or []
            if branches and isinstance(branches[0], str):
                return path, branches[0]
            break
    return path, ""


class _Composer:
    """What the store holds about one composer: its `composerData` (or
    None), its header row and the header's `value`."""

    def __init__(self, cid: str) -> None:
        self.cid = cid
        self.data: dict | None = None
        self.data_rowid = 0
        self.header: dict | None = None
        self.head: dict = {}
        self.errors: list = []

    @property
    def project(self) -> tuple[str, str]:
        return _project(self.head, self.data or {})

    def created(self):
        for doc in (self.data or {}, self.head, self.header or {}):
            if doc.get("createdAt") not in (None, ""):
                return doc.get("createdAt")
        return None

    def header_updated(self):
        h = self.header or {}
        value = h.get("lastUpdatedAt")
        return value if value not in (None, "") else self.head.get("lastUpdatedAt")

    def archived(self) -> bool:
        h = self.header or {}
        return (
            bool(h.get("isArchived"))
            or self.head.get("isArchived") is True
            or ((self.data or {}).get("isArchived") is True)
        )


def _read_headers(con: sqlite3.Connection, composers: dict) -> None:
    """Attach each `composerHeaders` row and its decoded `value` to its
    composer; a value that does not decode is an error of that composer."""
    if "composerHeaders" not in table_names(con):
        return
    wanted = ("composerId", "createdAt", "lastUpdatedAt", "isArchived", "value")
    for rec in _select(con, "composerHeaders", wanted):
        cid = str(rec.get("composerId") or "")
        if not cid:
            continue
        c = composers.setdefault(cid, _Composer(cid))
        c.header = rec
        if rec.get("value") is not None:
            label = "composerHeaders " + cid
            c.head = _object(_decode(int(rec["_rowid"]), label, rec["value"], c.errors))


def read_composers(con: sqlite3.Connection) -> dict[str, _Composer]:
    """Every composer of the store by id, `composerData` rows in rowid
    order first, then the header-only ones."""
    composers: dict[str, _Composer] = {}
    if "cursorDiskKV" in table_names(con):
        rows = sorted(_prefixed(con, "composerData:"))
        for rowid, key, value in rows:
            cid = key[len("composerData:") :]
            c = composers.setdefault(cid, _Composer(cid))
            c.data = _object(_decode(rowid, key, value, c.errors))
            c.data_rowid = rowid
    _read_headers(con, composers)
    return composers


def project_map(path: Path) -> dict[str, tuple[str, str]]:
    """composerId -> (project_path, git_branch) from the `state.vscdb` at
    `path`; {} when it is missing or unreadable. Cached by the file's and
    its sidecar's size and mtime, since every transcript and side database
    of a home asks for the same file."""
    key = [str(path)]
    for p in (path, Path(str(path) + "-wal")):
        try:
            st = p.stat()
            key += [st.st_size, st.st_mtime_ns]
        except OSError:
            key += [None, None]
    cache_key = tuple(key)
    if cache_key in _PROJECT_CACHE:
        return _PROJECT_CACHE[cache_key]
    found: dict[str, tuple[str, str]] = {}
    if is_sqlite(path):
        try:
            with open_copy(path) as con:
                # A pre-scan: the file's own parse reports its errors.
                found = {cid: c.project for cid, c in read_composers(con).items()}
        except sqlite3.DatabaseError:
            found = {}
    _PROJECT_CACHE.clear()
    _PROJECT_CACHE[cache_key] = found
    return found


_PROJECT_CACHE: dict[tuple, dict[str, tuple[str, str]]] = {}


def home_projects(artifact: Artifact) -> dict[str, tuple[str, str]]:
    """The composer projects of the IDE `state.vscdb` in the artifact's
    home, the first of the platform parents that has one."""
    for parent in IDE_PARENTS:
        path = artifact.home.disk_path / parent / "User/globalStorage/state.vscdb"
        if path.is_file():
            return project_map(path)
    return {}


class CursorParser(Parser):
    agent = "cursor"
    name = "cursor"
    records_origin = True
    has_secondary = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.match(rel)
            for rx in (
                STATE_RX,
                SEARCH_RX,
                TRANSCRIPT_RX,
                TRACKING_RX,
                CLI_CONFIG_RX,
                PERMISSIONS_RX,
            )
        )

    def secondary(self, artifact: Artifact) -> bool:
        return bool(TRANSCRIPT_RX.match(artifact.rel))

    def secondary_tolerance(self, artifact: Artifact) -> float:
        """60 seconds: the transcript's `<timestamp>` tag has minute
        precision, the user bubble's `createdAt` milliseconds."""
        return 60.0

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        if STATE_RX.match(rel):
            yield from self._database(artifact, self._state, opts)
        elif SEARCH_RX.match(rel):
            yield from self._database(artifact, self._search, opts)
        elif TRACKING_RX.match(rel):
            yield from self._database(artifact, self._tracking, opts)
        elif TRANSCRIPT_RX.match(rel):
            yield from self._transcript(artifact)
        else:
            yield from self._settings_file(artifact)

    # -- shared -----------------------------------------------------------

    def _row(
        self, artifact: Artifact, turn_type: str, text: str, when: object = "", line: int = 0
    ) -> Row:
        row = self.base_row(artifact)
        row.turn_type = turn_type
        row.text = text
        row.timestamp_utc = to_utc(when) if when not in (None, "") else ""
        row.source_line = line
        return row

    def _database(self, artifact: Artifact, reader, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            yield self._row(artifact, "system", "parser: not a SQLite database")
            return
        try:
            with open_copy(artifact.disk_path) as con:
                rows = list(reader(artifact, con, opts))
        except sqlite3.DatabaseError as e:
            yield self._row(artifact, "system", "parser: SQLite error: %s" % e)
            return
        yield from rows

    # -- state.vscdb ------------------------------------------------------

    def _state(self, artifact: Artifact, con: sqlite3.Connection, opts: Options) -> Iterator[Row]:
        errors: list = []
        composers = read_composers(con)
        kv = "cursorDiskKV" in table_names(con)
        drafts = {
            key[len("composerDraft:") :]: (rowid, key, value)
            for rowid, key, value in (_prefixed(con, "composerDraft:") if kv else [])
        }
        for cid in drafts:
            composers.setdefault(cid, _Composer(cid))
        deleted: list[_Composer] = []
        for c in composers.values():
            stamp = self._stamper(artifact, c)
            if c.data is not None:
                entries = self._entries(con, c, kv)
                # A draft: never sent, no header list in either layout.
                if entries or c.data.get("status") != "none":
                    yield from self._conversation(con, c, entries, stamp, opts)
            elif self._was_conversation(c):
                deleted.append(c)
                yield from self._deleted(c, stamp)
            if c.cid in drafts:
                yield from self._draft(c, drafts[c.cid], stamp)
            yield from error_rows(self, artifact, c.errors, c.cid, c.project[0])
        if deleted and kv:
            yield from self._blobs(artifact, con, deleted)
        yield from self._standing(artifact, con, errors)
        yield from error_rows(self, artifact, errors)

    def _stamper(self, artifact: Artifact, c: _Composer):
        path, branch = c.project

        def stamp(turn_type: str, text: str, when="", line=0, model="") -> Row:
            row = self._row(artifact, turn_type, text, when, line)
            row.session_id = c.cid
            row.project_path = path
            row.git_branch = branch
            row.model = model
            return row

        return stamp

    @staticmethod
    def _was_conversation(c: _Composer) -> bool:
        """A header with no `composerData` is a deleted conversation when it
        is not a draft: it has an `agentLocationHistory` entry or is
        archived."""
        return bool(c.head.get("agentLocationHistory")) or c.archived()

    def _entries(self, con: sqlite3.Connection, c: _Composer, kv: bool) -> list[dict]:
        inline = (c.data or {}).get("fullConversationHeadersOnly")
        if isinstance(inline, list) and inline:
            return [e for e in inline if isinstance(e, dict)]
        if not kv:
            return []
        entries: list[dict] = []
        for rowid, key, value in _prefixed(con, "composerConvHeaders:%s:" % c.cid):
            chunk = _decode(rowid, key, value, c.errors)
            if isinstance(chunk, list):
                entries += [e for e in chunk if isinstance(e, dict)]
        return entries

    def _conversation(
        self, con: sqlite3.Connection, c: _Composer, entries: list[dict], stamp, opts: Options
    ) -> Iterator[Row]:
        data = c.data or {}
        name = compact(data.get("name") or c.head.get("name"))
        if name:
            yield stamp("system", "session name: " + name, c.created(), c.data_rowid)
        yield from self._origin(c, stamp)
        seen: dict = {}
        model = ""
        for entry in entries:
            bid = str(entry.get("bubbleId") or "")
            key = "bubbleId:%s:%s" % (c.cid, bid)
            found = _one(con, key) if bid else None
            if found is None:
                yield stamp("system", "parser: missing bubble " + bid, entry.get("createdAt"))
                continue
            rowid, value = found
            bubble = _object(_decode(rowid, key, value, c.errors))
            if not bubble:
                continue
            if (bubble.get("type") or entry.get("type")) == 1:
                change = track_change(
                    "model",
                    seen,
                    c.cid,
                    str(_object(bubble.get("modelInfo")).get("modelName") or ""),
                )
                model = seen.get(c.cid, "")
                when = bubble.get("createdAt") or entry.get("createdAt")
                if change:
                    yield stamp("system", change, when, rowid, model)
                text = compact(bubble.get("text"))
                if text:
                    yield stamp("user", text, when, rowid, model)
            elif isinstance(bubble.get("toolFormerData"), dict):
                yield from self._tool(bubble, entry, rowid, stamp, model)
            else:
                when = (
                    bubble.get("createdAt") or bubble.get("startedAtMs") or entry.get("createdAt")
                )
                thinking = compact(_object(bubble.get("thinking")).get("text"))
                if thinking and opts.include_thinking:
                    yield stamp("thinking", thinking, when, rowid, model)
                text = compact(bubble.get("text"))
                if text:
                    yield stamp("assistant", text, when, rowid, model)
        if c.archived():
            yield stamp("system", "conversation archived", c.header_updated(), c.data_rowid, model)

    def _origin(self, c: _Composer, stamp) -> Iterator[Row]:
        kind = str(_object(c.head.get("agentLocation")).get("type") or "")
        if kind and kind != "local":
            yield stamp("system", "session origin: remote " + kind, c.created())

    def _tool(self, bubble: dict, entry: dict, rowid: int, stamp, model: str) -> Iterator[Row]:
        tool = bubble["toolFormerData"]
        extra = _object(tool.get("additionalData"))
        name = str(tool.get("name") or "")
        call_id = str(tool.get("toolCallId") or "")
        started = (
            bubble.get("startedAtMs")
            or extra.get("startedAtMs")
            or bubble.get("createdAt")
            or entry.get("createdAt")
        )
        args = tool.get("params") or tool.get("rawArgs")
        args_text = args if isinstance(args, str) else compact_json(args) if args else ""

        def row(turn_type: str, text: str, when) -> Row:
            r = stamp(turn_type, text, when, rowid, model)
            r.tool_name, r.tool_use_id = name, call_id
            return r

        yield row("tool_use", compact(args_text), started)
        review = extra.get("reviewData")
        if isinstance(review, dict):
            yield row("system", permission_text(extra, review), started)
        result = tool.get("result")
        result_text = ""
        if result not in (None, ""):
            result_text = compact(result if isinstance(result, str) else compact_json(result))
        rejected = extra.get("status") == "rejected"
        if result_text or rejected:
            text = ("[rejected] " if rejected else "") + result_text
            yield row("tool_result", compact(text), bubble.get("completedAtMs") or started)

    def _deleted(self, c: _Composer, stamp) -> Iterator[Row]:
        line = int((c.header or {}).get("_rowid") or 0)
        name = compact(c.head.get("name"))
        if name:
            yield stamp("system", "session name: " + name, c.created(), line)
        yield from self._origin(c, stamp)
        yield stamp("system", DELETED_TEXT, c.header_updated(), line)

    def _draft(self, c: _Composer, found, stamp) -> Iterator[Row]:
        rowid, key, value = found
        draft = _object(_decode(rowid, key, value, c.errors))
        text = compact(draft.get("text"))
        if text:
            yield stamp("system", "unsent draft: " + text, c.created(), rowid)

    def _blobs(
        self, artifact: Artifact, con: sqlite3.Connection, deleted: list[_Composer]
    ) -> Iterator[Row]:
        """User and assistant rows from the JSON `agentKv` blobs that name a
        deleted composer. A blob that is not JSON is protobuf, not an
        error."""
        for rowid, _key, value in _prefixed(con, "agentKv:blob:"):
            try:
                blob = json.loads(_as_text(value))
            except ValueError:
                continue
            if not isinstance(blob, dict) or "content" not in blob:
                continue
            content = blob.get("content")
            haystack = content if isinstance(content, str) else compact_json(content)
            for c in deleted:
                if c.cid not in haystack:
                    continue
                stamp = self._stamper(artifact, c)
                role = str(blob.get("role") or "")
                text = compact(text_of(content))
                if role in ("user", "assistant"):
                    row = stamp(role, text, "", rowid)
                    row.recovered = "yes"
                else:
                    row = stamp("system", "%s: %s" % (_role_label(role), text), "", rowid)
                yield row

    def _standing(self, artifact: Artifact, con: sqlite3.Connection, errors: list) -> Iterator[Row]:
        if "ItemTable" not in table_names(con):
            return
        items = {}
        sql = "select rowid, key, value from ItemTable where key in (?, ?)"
        for rowid, key, value in con.execute(sql, (SETTINGS_KEY, SANDBOX_KEY)):
            items[_as_text(key)] = (int(rowid), value)
        if SETTINGS_KEY not in items:
            return
        rowid, value = items[SETTINGS_KEY]
        settings = _object(_decode(rowid, SETTINGS_KEY, value, errors))
        sandbox = False
        if SANDBOX_KEY in items:
            sandbox = _decode(items[SANDBOX_KEY][0], SANDBOX_KEY, items[SANDBOX_KEY][1], []) is True
        mtime = file_mtime(artifact)
        for text in standing_texts(_object(settings.get("composerState")), sandbox):
            yield self._row(artifact, "system", text, mtime, rowid)
        used = _object(_object(settings.get("aiSettings")).get("modelLastUsedAt"))
        for model_id, when in used.items():
            text = "model last used: %s (from state.vscdb aiSettings.modelLastUsedAt)" % model_id
            yield self._row(artifact, "system", text, when, rowid)

    # -- side databases --------------------------------------------------

    def _search(self, artifact: Artifact, con: sqlite3.Connection, opts: Options) -> Iterator[Row]:
        if "conversations" not in table_names(con):
            return
        projects = home_projects(artifact)
        for rec in _select(con, "conversations", SEARCH_COLUMNS):
            title = compact(_as_text(rec.get("title")))
            if not title:
                continue
            text = "conversation index: %s source=%s archived=%s" % (
                title,
                _field(rec.get("source")),
                _field(rec.get("is_archived")),
            )
            row = self._row(artifact, "system", text, rec.get("updated_at"), int(rec["_rowid"]))
            self._join(row, _as_text(rec.get("id")), projects)
            yield row

    def _tracking(
        self, artifact: Artifact, con: sqlite3.Connection, opts: Options
    ) -> Iterator[Row]:
        tables = table_names(con)
        projects = home_projects(artifact)
        for table, columns in TRACKING_TABLES.items():
            if table not in tables:
                continue
            for rec in _select(con, table, columns):
                text, when, sid = tracking_text(table, rec)
                row = self._row(artifact, "system", text, when, int(rec["_rowid"]))
                self._join(row, sid, projects)
                row.model = _as_text(rec.get("model"))
                if table == "scored_commits":
                    row.git_branch = _as_text(rec.get("branchName"))
                yield row

    @staticmethod
    def _join(row: Row, sid: str, projects: dict) -> None:
        row.session_id = sid
        if sid in projects:
            row.project_path, row.git_branch = projects[sid]

    # -- transcript JSONL -------------------------------------------------

    def _transcript(self, artifact: Artifact) -> Iterator[Row]:
        m = TRANSCRIPT_RX.match(artifact.rel)
        sid = m.group(1) if m else ""
        path, branch = home_projects(artifact).get(sid, ("", ""))
        errors: list = []

        def row(turn_type: str, text: str, when: str, line: int) -> Row:
            r = self._row(artifact, turn_type, text, "", line)
            r.timestamp_utc = when
            r.session_id, r.project_path, r.git_branch = sid, path, branch
            return r

        for n, rec in iter_jsonl(artifact.disk_path, errors):
            role = rec.get("role")
            if role not in ("user", "assistant"):
                continue
            content = _object(rec.get("message")).get("content")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    if role == "user":
                        query, when = unwrap_query(block["text"])
                        text = compact(query)
                        if text:
                            yield row("user", text, when, n)
                    elif compact(block["text"]):
                        yield row("assistant", compact(block["text"]), "", n)
                elif block.get("type") == "tool_use":
                    r = row("tool_use", compact_json(block.get("input")), "", n)
                    r.tool_name = str(block.get("name") or "")
                    yield r
        yield from error_rows(self, artifact, errors, sid, path)

    # -- settings files ---------------------------------------------------

    def _settings_file(self, artifact: Artifact) -> Iterator[Row]:
        rel = artifact.rel
        try:
            with open(artifact.disk_path, "rb") as fh:
                doc = json.loads(fh.read().decode("utf-8", errors="replace"))
        except (OSError, ValueError) as e:
            yield self._row(
                artifact, "system", "parser: unreadable %s: %s" % (rel, error_reason(e))
            )
            return
        if not isinstance(doc, dict):
            yield self._row(artifact, "system", "parser: %s is not a JSON object" % rel)
            return
        if CLI_CONFIG_RX.match(rel):
            settings = cli_config_settings(doc)
        else:
            settings = permissions_settings(doc)
        mtime = file_mtime(artifact)
        project = artifact.home.original if artifact.home.project else ""
        for setting in settings:
            row = self._row(
                artifact,
                "system",
                compact("permission setting: %s (from %s, file mtime)" % (setting, rel)),
                mtime,
                1,
            )
            row.project_path = project
            yield row


def _field(value) -> str:
    text = _as_text(value)
    return text if text != "" else "-"


def _role_label(role: str) -> str:
    return "system prompt" if role == "system" else "%s message" % (role or "-")


def permission_text(extra: dict, review: dict) -> str:
    """`permission decision: <selectedOption> outcome=<status>
    approval=<approvalType> reason=<blockReason>`, then ` allowlisted=` with
    the applied allowlist entries when there are any."""
    text = "permission decision: %s outcome=%s approval=%s reason=%s" % (
        _field(review.get("selectedOption")),
        _field(extra.get("status")),
        _field(review.get("approvalType")),
        _field(extra.get("blockReason")),
    )
    applied = review.get("appliedAllowlistOptionIds")
    if isinstance(applied, list):
        names = {}
        for option in review.get("allowlistOptions") or []:
            if isinstance(option, dict) and option.get("id") is not None:
                names[str(option["id"])] = str(option.get("commandName") or option["id"])
        text += " allowlisted=" + ",".join(names.get(str(i), str(i)) for i in applied)
    return text


def standing_texts(state: dict, sandbox: bool) -> Iterator[str]:
    """The `permission setting:` texts of the settings blob's
    `composerState`: one per standing-list entry, one per `modes4` entry
    and one per boolean switch."""
    for key in STANDING_LISTS:
        for entry in state.get(key) or [] if isinstance(state.get(key), list) else []:
            yield "permission setting: %s=%s %s" % (key, setting_value(entry), COMPOSER_SOURCE)
    for mode in state.get("modes4") or [] if isinstance(state.get("modes4"), list) else []:
        if not isinstance(mode, dict):
            continue
        flags = " ".join(
            "%s=%s" % (flag, setting_value(mode[flag]) if flag in mode else "-")
            for flag in ("autoRun", "smartModeAutoRun", "fullAutoRun")
        )
        yield "permission setting: run mode %s=%s %s sandbox=%s %s" % (
            _field(mode.get("id")),
            run_mode(mode, sandbox),
            flags,
            setting_value(sandbox),
            COMPOSER_SOURCE,
        )
    for key in SWITCHES:
        if key in state:
            yield "permission setting: %s=%s %s" % (key, setting_value(state[key]), COMPOSER_SOURCE)


def _entries(value) -> list:
    return value if isinstance(value, list) else []


def cli_config_settings(doc: dict) -> Iterator[str]:
    """`<key>=<value>` per setting of `.cursor/cli-config.json` that
    governs permissions."""
    if "approvalMode" in doc:
        yield "approvalMode=%s" % setting_value(doc["approvalMode"])
    permissions = _object(doc.get("permissions"))
    for key in ("allow", "deny"):
        for entry in _entries(permissions.get(key)):
            yield "permissions.%s=%s" % (key, setting_value(entry))
    sandbox = _object(doc.get("sandbox"))
    if "mode" in sandbox:
        yield "sandbox.mode=%s" % setting_value(sandbox["mode"])


def permissions_settings(doc: dict) -> Iterator[str]:
    """`<key>=<value>` per entry of a `permissions.json`."""
    allowlists = _object(doc.get("allowlists"))
    for key in ("mcp", "terminal"):
        for entry in _entries(allowlists.get(key)):
            yield "allowlists.%s=%s" % (key, setting_value(entry))
    if "approvalMode" in doc:
        yield "approvalMode=%s" % setting_value(doc["approvalMode"])
    for key in ("allowInstructions", "blockInstructions"):
        for entry in _entries(doc.get(key)):
            yield "%s=%s" % (key, setting_value(entry))


def tracking_text(table: str, rec: dict) -> tuple[str, object, str]:
    """(text, time, session id) of an `ai-code-tracking.db` row."""
    f = {k: _field(v) for k, v in rec.items()}
    sid = _as_text(rec.get("conversationId") or rec.get("composerId"))
    if table == "ai_code_hashes":
        text = "ai code: %s source=%s model=%s request=%s" % (
            f.get("fileName", "-"),
            f.get("source", "-"),
            f.get("model", "-"),
            f.get("requestId", "-"),
        )
        return text, rec.get("timestamp"), sid
    if table == "conversation_summaries":
        text = "conversation summary: %s: %s" % (f.get("title", "-"), f.get("tldr", "-"))
        return text, rec.get("updatedAt"), sid
    if table == "ai_deleted_files":
        text = "file deleted by agent: %s model=%s" % (f.get("gitPath", "-"), f.get("model", "-"))
        return text, rec.get("deletedAt"), sid
    text = "scored commit: %s branch=%s +%s -%s" % (
        f.get("commitHash", "-"),
        f.get("branchName", "-"),
        f.get("linesAdded", "-"),
        f.get("linesDeleted", "-"),
    )
    return text, rec.get("scoredAt"), ""
