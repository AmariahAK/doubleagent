"""OpenClaw (formerly Clawdbot and Moltbot) agent transcripts.

Validated against source, openclaw/openclaw at 3b16db7 (see
`analyzer/research/openclaw.md`), with a synthetic fixture; no real install
was checked. The state directory is `.openclaw`, a profile's
`.openclaw-<profile>`, or the legacy `.clawdbot` / `.moltbot`. Files:

* `agents/<agentId>/agent/openclaw-agent.sqlite` (WAL, opened through
  `sqlite_util`), the live store since mid-2026:
  - `transcript_events(session_id, seq, event_json, event_zstd,
    created_at)`: one entry per row. Rows of 1 KiB to 4 MiB may hold the
    entry as one zstd frame in `event_zstd` with `event_json` NULL, decoded
    with the `zstandard` package; a frame that does not decode becomes one
    `system` row. `created_at` is epoch ms.
  - `session_windows(session_id, session_key, previous_session_id, reason,
    channel, account_id, chat_type, model_provider, model, started_at,
    parent_session_key, spawned_by, display_name)`: one row per transcript
    generation, read for the session-start row.
  - `session_transcript_archives(session_id, session_key, reason, encoding,
    archive_blob, archive_name, created_at)`: reset or deleted
    generations as JSONL (zstd when `encoding` is `zstd`), every one parsed,
    whether or not `published_at` says it was also written to the sessions
    directory. The schema calls this table the
    canonical owner of a reclaimed generation, from which the
    `.jsonl.reset.*` / `.jsonl.deleted.*` file is derived and may be
    recreated (`openclaw-agent-schema.sql:606-607`), so the blob is the
    primary copy and the file the secondary one.
  - `session_transcript_cold_archives(session_id, archive_name, storage,
    archive_blob)` with `storage` `sqlite`: a zstd JSONL envelope of
    `{"kind":"event","row":{"seq","event_json","created_at"}}` records
    (`src/config/sessions/session-cold-storage-codec.ts:48-100`, not in the
    research document). `storage` `file` means
    `agents/<id>/sessions/cold/<sha256>.jsonl.zst`, parsed as a file.
  - `session_nodes(rowid, session_key, current_session_id, entry_json)`:
    the session-metadata entry of each session key. Its `publicShare`
    `{id, sessionId, createdAt}` (a 48-hex grant id, the transcript
    generation it publishes, epoch ms; absent on a session never
    published, removed when access is turned off) marks a session whose
    user messages and final answers anyone with the public URL can read,
    served by the Gateway: one `session synced: public share <id>
    generation <sessionId> (from openclaw-agent.sqlite
    session_nodes.entry_json, publicShare.createdAt)` row after that
    generation's session-start row, at `createdAt`, `session_id` the
    generation (`records_sync`). A grant whose generation has no
    transcript rows in the database still yields its row, after the
    others. An `entry_json` that does not decode is its own `parser:` row
    carrying the column in full. The share URL's token is not stored.
    Fixture only: no real install has shown the key.
  - `auth_profile_store`, `auth_profile_state` and `session_suggestions`
    hold credentials and are never read.
* `state/openclaw.sqlite` (WAL, opened through `sqlite_util`), the
  Gateway's state database, table `backup_runs(id, created_at,
  archive_path, status, manifest_json)`, one row per `openclaw backup`
  attempt (`src/state/openclaw-state-schema.sql:1843-1849`), with
  `manifest_json` `{kind, target, namespace, pushFailed, bytes, location
  {name, provider, locationId, key, namespace, ...}}`
  (`src/state/backup-run-records.contract.ts:98-124`). A backup uploads
  the whole state directory, every agent database included, so the row is
  host-wide, not per session: one `system` row with an empty `session_id`
  per run with `status` `ok` and either a `location` (an upload to a
  storage location) or a Git `target` (the commit sha) without
  `pushFailed`, at `created_at`: `backup uploaded: <kind> to
  <location.name or archive_path> key <location.key or target> namespace
  <location.namespace or namespace or -> (from state/openclaw.sqlite
  backup_runs, created_at)`. A Git backup run without `--push` records
  the same manifest as a pushed one (`src/commands/backup-git.ts:140-151`),
  so a Git row says a commit was made and, unless the push failed, may
  have been pushed. A `manifest_json` that does not decode is its own
  `parser:` row carrying the column in full; a file that is not SQLite or
  does not open is one `parser:` row. The database's other tables are not
  read. Fixture only.
* `agents/<agentId>/sessions/<sessionId>.jsonl` (and `sessions/` at the
  state root, the older single-agent layout): legacy transcripts not yet
  imported by `openclaw doctor`. The sibling legacy `sessions.json`,
  `{<sessionKey>: {"sessionId", ...}}`
  (`src/infra/state-migrations.legacy-session-store.ts:202-205`), gives the
  session key.
* Copies of a transcript in the same `sessions/` directory, each a
  secondary source (`secondary()`), in the same entry format and read the
  same way; their rows carry the entries' own timestamps, ids and header
  `cwd`, so they pair exactly with the primary store's rows for the same
  entries:
  - `<sessionId>.jsonl.reset.<ts>[.<gen>][.zst]` and `.jsonl.deleted.<...>`:
    the published file of a `session_transcript_archives` blob, one zstd
    frame when `.zst`. Kept after the database is lost or excluded; the
    blob outlives the file otherwise, since retention deletes the row
    only once the file is gone (`session-history-archive-pruning.worker.ts:105-114`).
  - `<sessionId>.checkpoint.<uuid>.jsonl`: a pre-compaction snapshot,
    `fs.copyFile` of the session file before compaction (written by
    releases before openclaw/openclaw c59635a,
    `src/gateway/session-compaction-checkpoints.ts:383-389` at 6814525; no
    release at 3b16db7 writes new ones, `legacy-compaction-history.ts:3-7`).
    It holds the entries the compaction later summarised.
  - `<sessionId>.jsonl.pre-doctor-(branch|openai-codex)-repair-<ts>.bak`:
    `fs.copyFile` of a legacy transcript before `openclaw doctor` rewrote
    it (`src/commands/doctor-session-transcripts.ts:258-261`, `285-288` at
    6559e3f, before 4273ca9 removed the file-era runtime). A branch repair
    keeps only the active branch, so the copy holds the abandoned branches
    too, which no other store has.
  The session id of every JSONL file, the legacy transcript and its
  copies alike, is its header `id`, else the name before the suffix, so a
  copy carries the id the database and the legacy file carry: a session
  forked from a checkpoint was written as `<ts>_<sessionId>.jsonl` (line
  323 at 6814525), its own checkpoints named after that file, and an
  archive of an id over 96 bytes is named `session-<sha256>`
  (`session-accessor.sqlite-archive-artifact.ts:24-29`). The session-start
  row of a copy names it (`archive=<reason>.<ts>`, `copy=<suffix>`), so it
  never pairs and each copy shows one row of its own.
  Not read: `*.trajectory.jsonl`, the trajectory flight recorder, whose
  runtime events are a different schema (`openclaw-trajectory`,
  `docs/tools/trajectory.md:76-102`); `*.migrated[.N]`, whose transcript
  writer is not in the source at 3b16db7 or 6559e3f (the suffix is used
  there for other migrated files, cron logs and pairing stores); and the
  `.jsonl.bak.<ts>` legacy compact backups (`artifacts.ts:43-50`), whose
  content is not recorded.

Entry fields: header `{type:"session", version, id, timestamp, cwd,
parentSession}`; then `type`, `id`, `parentId`, `timestamp` (ISO 8601) and
per type `message` (`message`), `model_change` (`provider`, `modelId`),
`thinking_level_change` (`thinkingLevel`), `compaction` (`summary`,
`tokensBefore`, `tokensAfter`), `reset` (`reason`), `branch_summary`
(`summary`), `custom` (`customType`, `data`), `custom_message`
(`customType`, `content`), `label` (`label`, `targetId`), `session_info`
(`name`). `message.role`: `user` (`content`, `runtimeContext`,
`runtimeContextCarrier`), `assistant` (`content` blocks `text`, `thinking`
{`thinking`, `redacted`}, `toolCall` {`id`, `name`, `arguments`}, `image`;
`model`, `responseModel`, `stopReason`, `errorMessage`), `toolResult`
(`toolCallId`, `toolName`, `content`, `isError`), `bashExecution`
(`command`, `output`, `exitCode`, `cancelled`), `custom`, `branchSummary`,
`compactionSummary` (`summary`); `message.timestamp` is epoch ms.

Rows: one `system` row per session carrying the session key
(`agent:<agentId>:<channel>:<accountId>:direct:<peerId>` names the external
sender), channel, account, chat type and parent; `session_id` is the
transcript id (`transcript_events.session_id`, the header `id`), and
`project_path` the header `cwd`. User messages flagged `runtimeContext` are
injected context, not human input, and become `system` rows. A
`bashExecution` (a `!` command the operator ran) becomes a `tool_use` row
named `bash` and a `tool_result` row, joined on the entry `id`. An assistant
message that ended with `stopReason` `error` or `aborted`, or carries an
`errorMessage`, adds a `system` row. Model rows: `model: <id>
provider=<provider>` at the first model a session names (the
`session_windows` `model` and `model_provider`, at the session-start time,
else a `model_change` `modelId` or an assistant `responseModel`, else
`model`) and `model: <old> -> <new> provider=<provider>` on every later
entry whose model differs, with ` requested=<model>` when an assistant
`responseModel` differs from its `model` (`pi.model_text`). A
`model_change` entry naming the model already in force still yields the
plain `model: <id> provider=<provider>` row (`pi.switch_text`). The
permission tables of `state/openclaw.sqlite` (`exec_approvals_config`,
`operator_approvals`, `audit_events`) are not read: their columns are not
in the research. Timestamps are the entry `timestamp`,
else the message's ms timestamp, else the row's `created_at`. `source_line`
is the `transcript_events` (or archive table) rowid, or the JSONL line. No
git branch is recorded.

A line that does not decode is its own `system` row (issue 136, `error_rows`
in `base.py`), carrying the line in full after `parser: unparseable line
(<reason>): `, with the session's id and `cwd`; a line that decodes to a
JSON value other than an object is the same row with the reason `not a
JSON object` (issue 177). A legacy `sessions.json` that cannot be read,
does not decode or is not a JSON object is one whole-file row in each
transcript beside it, `parser: sessions.json unreadable (<reason>)`,
`parser: sessions.json unparseable (<reason>)` or `parser: sessions.json
is not a JSON object`, with `source_line` 0, after the line rows;
the transcript's other rows are still yielded, without the key. For a line inside an archive
blob the text is `parser: archive <name> line <n>: unparseable line
(<reason>): <line>` (or `cold archive`) and `source_line` is the archive row's rowid, as for the blob's other rows.
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
from .base import Options, Parser, compact_json, error_rows, line_text, text_of
from .pi import model_text, switch_text
from .zed import decompress

STATE = r"(?:\.openclaw(?:-[^/]+)?|\.clawdbot|\.moltbot)"
DB_RX = re.compile(r"^" + STATE + r"/agents/[^/]+/agent/openclaw-agent\.sqlite$")
STATE_DB_RX = re.compile(r"^" + STATE + r"/state/openclaw\.sqlite$")
SESSIONS = r"^" + STATE + r"/(?:agents/[^/]+/)?sessions/"
ARCHIVE_SUFFIX = r"\.jsonl\.(reset|deleted)\.\d{4}-\d\d-\d\dT\d\d-\d\d-\d\d(?:\.\d{3})?Z(?:\.[0-9a-f]{32})?(?:\.zst)?"
# A pre-compaction checkpoint and a pre-doctor repair backup (`artifacts.ts:13-17`).
COPY_SUFFIX = (
    r"\.checkpoint\.[0-9a-fA-F-]{36}\.jsonl"
    r"|\.jsonl\.pre-doctor-(?:branch|openai-codex)-repair-"
    r"\d{4}-\d\d-\d\dT\d\d-\d\d-\d\d-\d{3}Z\.bak"
)
JSONL_RX = re.compile(
    SESSIONS
    + r"(?P<name>[^/]+?)(?:(?P<archive>"
    + ARCHIVE_SUFFIX
    + r")|(?P<copy>"
    + COPY_SUFFIX
    + r")|\.jsonl)$"
)
COLD_RX = re.compile(SESSIONS + r"cold/[0-9a-f]{64}\.jsonl\.zst$")
SKIP_NAME_RX = re.compile(r"\.trajectory$")
ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def tool_args_text(args) -> str:
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return args
    if isinstance(args, dict):
        for k in ("command", "path", "url"):
            if isinstance(args.get(k), str) and args[k]:
                return args[k]
    if args in (None, "", {}):
        return ""
    return compact_json(args)


def _maybe_zstd(blob: bytes) -> tuple[bytes | None, str]:
    """(data, error): zstd frames are decompressed, anything else returned."""
    blob = bytes(blob)
    if not blob.startswith(ZSTD_MAGIC):
        return blob, ""
    try:
        return decompress(blob), ""
    except Exception as e:  # noqa: BLE001 - zstandard.ZstdError or a stream read error
        return None, "%s: %s" % (type(e).__name__, e)


def _iter_lines(data: bytes, errors: list) -> Iterator[tuple[int, dict]]:
    """(line number, record) for each JSON object line of `data`; a line that
    does not decode, or decodes to a value other than an object (an array, a
    string, a number, `null`), is appended to `errors` as (line, message,
    line text), the message `unparseable line (not a JSON object)` for the
    second kind, so `error_rows` reports it in full (issue 177)."""
    for n, raw in enumerate(data.split(b"\n"), 1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            rec = json.loads(stripped.decode("utf-8", errors="replace"))
        except ValueError as e:
            errors.append((n, "unparseable line (%s)" % e, line_text(raw)))
            continue
        if not isinstance(rec, dict):
            errors.append((n, "unparseable line (not a JSON object)", line_text(raw)))
            continue
        yield n, rec


class _Session:
    """State carried across one transcript's entries."""

    def __init__(
        self,
        session_id: str = "",
        key: str = "",
        extra: str = "",
        model: str = "",
        provider: str = "",
    ):
        self.session_id = session_id
        self.key = key
        self.extra = extra
        self.model = model
        self.provider = provider
        self.cwd = ""
        self.header_id = False  # True: the header `id` replaces session_id
        self.started = False
        self.seen: dict = {}  # the model in use, for the `model:` rows
        # The database's `publicShare` grants, {generation: (rowid, grant)};
        # the session-start row pops its own and yields its row.
        self.shares: dict[str, tuple[int, dict]] = {}


class OpenClawParser(Parser):
    agent = "openclaw"
    name = "openclaw"
    has_secondary = True
    records_sync = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        if DB_RX.match(rel) or COLD_RX.match(rel) or STATE_DB_RX.match(rel):
            return True
        m = JSONL_RX.match(rel)
        return bool(m) and not SKIP_NAME_RX.search(m.group("name"))

    def secondary(self, artifact: Artifact) -> bool:
        """The published archive files and the checkpoint and pre-doctor
        copies; the database and the plain legacy `.jsonl` are primary."""
        m = JSONL_RX.match(artifact.rel)
        return bool(m) and bool(m.group("archive") or m.group("copy"))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if DB_RX.match(artifact.rel):
            if is_sqlite(artifact.disk_path):
                yield from self._parse_db(artifact, opts)
        elif STATE_DB_RX.match(artifact.rel):
            yield from self._parse_state_db(artifact)
        else:
            yield from self._parse_file(artifact, opts)

    # -- rows -------------------------------------------------------------------
    def _row(
        self,
        artifact: Artifact,
        s: _Session,
        line: int,
        ts: str,
        turn_type: str,
        text: str,
        opts: Options,
        model: str = "",
        tool_name: str = "",
        tool_use_id: str = "",
    ) -> Row:
        row = self.base_row(artifact)
        row.source_line = line
        row.session_id = s.session_id
        row.project_path = s.cwd
        row.timestamp_utc = ts
        row.turn_type = turn_type
        row.model = model
        row.tool_name = tool_name
        row.tool_use_id = tool_use_id
        row.text = compact(text)
        return row

    def _start(
        self,
        artifact: Artifact,
        s: _Session,
        line: int,
        ts: str,
        header: dict | None,
        opts: Options,
    ) -> Iterator[Row]:
        """The session-start row, then a `model:` row when the session
        window names the model the session started with."""
        s.started = True
        header = header or {}
        if header.get("id") and (s.header_id or not s.session_id):
            s.session_id = str(header["id"])
        if isinstance(header.get("cwd"), str):
            s.cwd = header["cwd"]
        parent = header.get("parentSession")
        text = " ".join(
            x
            for x in (
                "session start:",
                "key=%s" % s.key if s.key else "",
                s.extra,
                "version=%s" % header["version"] if header.get("version") is not None else "",
                "parent_session=%s" % parent if parent else "",
            )
            if x
        )
        ts = ts or to_utc(header.get("timestamp"))
        yield self._row(artifact, s, line, ts, "system", text, opts, s.model)
        mtext = model_text(s.seen, s.session_id, s.model, s.provider)
        if mtext:
            yield self._row(artifact, s, line, ts, "system", mtext, opts, s.model)
        share = s.shares.pop(s.session_id, None)
        if share is not None:
            yield self._share_row(artifact, s, *share)

    def _share_row(self, artifact: Artifact, s: _Session, rowid: int, grant: dict) -> Row:
        """The `session synced: public share` row of a `publicShare` grant,
        `source_line` the `session_nodes` rowid."""
        text = (
            "session synced: public share %s generation %s (from openclaw-agent.sqlite"
            " session_nodes.entry_json, publicShare.createdAt)"
            % (grant.get("id") or "-", grant.get("sessionId") or "-")
        )
        ts = to_utc(grant.get("createdAt"))
        return self._row(artifact, s, rowid, ts, "system", text, Options())

    def _entry_rows(
        self, artifact: Artifact, s: _Session, line: int, rec: dict, created_at, opts: Options
    ) -> Iterator[Row]:
        etype = rec.get("type")
        msg = rec.get("message")
        if not isinstance(msg, dict):
            msg = {}
        ts = to_utc(rec.get("timestamp")) or to_utc(msg.get("timestamp")) or to_utc(created_at)
        if etype == "session":
            yield from self._start(artifact, s, line, ts, rec, opts)
            return
        if not s.started:
            yield from self._start(artifact, s, line, ts, None, opts)
        if etype == "message":
            yield from self._message_rows(artifact, s, line, ts, rec, msg, opts)
            return

        def system(text: str, model: str = "") -> Row:
            return self._row(artifact, s, line, ts, "system", text, opts, model)

        if etype == "model_change":
            s.model = str(rec.get("modelId") or "")
            mtext = switch_text(s.seen, s.session_id, s.model, str(rec.get("provider") or ""))
            if mtext:
                yield system(mtext, s.model)
        elif etype == "thinking_level_change":
            yield system("thinking level: %s" % (rec.get("thinkingLevel") or ""))
        elif etype == "compaction":
            tokens = " ".join(
                x
                for x in (
                    "tokens_before=%s" % rec["tokensBefore"]
                    if rec.get("tokensBefore") is not None
                    else "",
                    "tokens_after=%s" % rec["tokensAfter"]
                    if rec.get("tokensAfter") is not None
                    else "",
                )
                if x
            )
            yield system(
                "compaction%s: %s" % (" (%s)" % tokens if tokens else "", rec.get("summary") or "")
            )
        elif etype == "reset":
            yield system("reset: %s" % (rec.get("reason") or ""))
        elif etype == "branch_summary":
            yield system("branch summary: %s" % (rec.get("summary") or ""))
        elif etype == "custom":
            yield system(
                "custom %s: %s" % (rec.get("customType") or "", compact_json(rec.get("data")))
            )
        elif etype == "custom_message":
            yield system(
                "custom message %s: %s" % (rec.get("customType") or "", text_of(rec.get("content")))
            )
        elif etype == "label":
            yield system(
                "label: %s (entry %s)" % (rec.get("label") or "", rec.get("targetId") or "")
            )
        elif etype == "session_info":
            yield system("session name: %s" % (rec.get("name") or ""))
        else:
            rest = {
                k: v for k, v in rec.items() if k not in ("type", "id", "parentId", "timestamp")
            }
            yield system("%s: %s" % (etype or "entry", compact_json(rest)))

    def _message_rows(
        self,
        artifact: Artifact,
        s: _Session,
        line: int,
        ts: str,
        rec: dict,
        msg: dict,
        opts: Options,
    ) -> Iterator[Row]:
        role = msg.get("role")
        if role == "user":
            text = text_of(msg.get("content"))
            if msg.get("runtimeContext") or msg.get("runtimeContextCarrier"):
                yield self._row(artifact, s, line, ts, "system", "runtime context: " + text, opts)
            else:
                yield self._row(artifact, s, line, ts, "user", text, opts)
        elif role == "assistant":
            requested = str(msg.get("model") or "")
            model = str(msg.get("responseModel") or "") or requested or s.model
            if model:
                s.model = model
            if msg.get("responseModel") or requested:
                mtext = model_text(
                    s.seen, s.session_id, model, str(msg.get("provider") or ""), requested
                )
                if mtext:
                    yield self._row(artifact, s, line, ts, "system", mtext, opts, model)
            content = msg.get("content")
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            for b in content if isinstance(content, list) else []:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "text":
                    if b.get("text"):
                        yield self._row(
                            artifact, s, line, ts, "assistant", str(b["text"]), opts, model
                        )
                elif bt == "thinking":
                    if opts.include_thinking:
                        t = b.get("thinking") or (
                            "[redacted thinking]" if b.get("redacted") else ""
                        )
                        if t:
                            yield self._row(artifact, s, line, ts, "thinking", str(t), opts, model)
                elif bt == "toolCall":
                    yield self._row(
                        artifact,
                        s,
                        line,
                        ts,
                        "tool_use",
                        tool_args_text(b.get("arguments")),
                        opts,
                        model,
                        str(b.get("name") or ""),
                        str(b.get("id") or ""),
                    )
                elif bt == "image":
                    yield self._row(artifact, s, line, ts, "assistant", "[image]", opts, model)
            stop = msg.get("stopReason")
            if stop in ("error", "aborted") or msg.get("errorMessage"):
                yield self._row(
                    artifact,
                    s,
                    line,
                    ts,
                    "system",
                    "assistant %s: %s" % (stop or "error", msg.get("errorMessage") or ""),
                    opts,
                    model,
                )
        elif role == "toolResult":
            text = text_of(msg.get("content"))
            if msg.get("isError"):
                text = "[error] " + text
            yield self._row(
                artifact,
                s,
                line,
                ts,
                "tool_result",
                text,
                opts,
                "",
                str(msg.get("toolName") or ""),
                str(msg.get("toolCallId") or ""),
            )
        elif role == "bashExecution":
            tid = str(rec.get("id") or "")
            yield self._row(
                artifact,
                s,
                line,
                ts,
                "tool_use",
                str(msg.get("command") or ""),
                opts,
                "",
                "bash",
                tid,
            )
            status = "exit=%s" % msg.get("exitCode")
            if msg.get("cancelled"):
                status += " cancelled"
            if msg.get("truncated"):
                status += " truncated"
            yield self._row(
                artifact,
                s,
                line,
                ts,
                "tool_result",
                "[%s] %s" % (status, msg.get("output") or ""),
                opts,
                "",
                "bash",
                tid,
            )
        elif role in ("branchSummary", "compactionSummary"):
            label = "branch summary" if role == "branchSummary" else "compaction summary"
            yield self._row(
                artifact, s, line, ts, "system", "%s: %s" % (label, msg.get("summary") or ""), opts
            )
        elif role == "custom":
            yield self._row(
                artifact,
                s,
                line,
                ts,
                "system",
                "custom %s: %s" % (msg.get("customType") or "", text_of(msg.get("content"))),
                opts,
            )
        else:
            yield self._row(
                artifact,
                s,
                line,
                ts,
                "system",
                "%s: %s" % (role or "message", text_of(msg.get("content")) or compact_json(msg)),
                opts,
            )

    def _bad(
        self, artifact: Artifact, s: _Session, line: int, text: str, opts: Options, ts: str = ""
    ) -> Row:
        return self._row(artifact, s, line, ts, "system", "parser: " + text, opts)

    def _blob_errors(
        self, artifact: Artifact, s: _Session, rowid: int, label: str, errors: list
    ) -> Iterator[Row]:
        """`error_rows` for the bad lines of an archive blob: `source_line` the
        archive row's rowid and the message prefixed with `label` and the
        line's number in the blob (`archive <name> line 3: unparseable line
        (<reason>)`)."""
        located = [(rowid, "%s line %d: %s" % (label, n, msg), raw) for n, msg, raw in errors]
        yield from error_rows(self, artifact, located, s.session_id, s.cwd)

    def _records(
        self, artifact: Artifact, s: _Session, records, opts: Options, fixed_line: int = 0
    ) -> Iterator[Row]:
        """Rows from (line, record) pairs of a JSONL transcript or a cold
        archive envelope; `fixed_line` overrides the line for blobs."""
        for n, rec in records:
            line = fixed_line or n
            if "kind" in rec and "type" not in rec:
                kind = rec.get("kind")
                if kind == "header" and not s.session_id:
                    s.session_id = str(rec.get("sessionId") or "")
                if kind != "event" or not isinstance(rec.get("row"), dict):
                    continue
                inner = rec["row"]
                try:
                    entry = json.loads(inner.get("event_json") or "")
                except (TypeError, ValueError) as e:
                    yield self._bad(
                        artifact,
                        s,
                        line,
                        "cold archive event seq %s unreadable: %s" % (inner.get("seq"), e),
                        opts,
                        to_utc(inner.get("created_at")),
                    )
                    continue
                if isinstance(entry, dict):
                    yield from self._entry_rows(
                        artifact, s, line, entry, inner.get("created_at"), opts
                    )
                continue
            yield from self._entry_rows(artifact, s, line, rec, None, opts)

    # -- JSONL files ----------------------------------------------------------------
    def _parse_file(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        m = JSONL_RX.match(artifact.rel)
        s = _Session(session_id=m.group("name") if m else "")
        s.header_id = True
        if m and m.group("archive"):
            s.extra = "archive=%s" % m.group("archive")[len(".jsonl.") :]
        elif m and m.group("copy"):
            s.extra = "copy=%s" % m.group("copy").lstrip(".")
        key_error = ""
        if m:
            s.key, key_error = self._legacy_key(artifact, s.session_id)
        with open(artifact.disk_path, "rb") as fh:
            raw = fh.read()
        data, err = _maybe_zstd(raw)
        if data is None:
            yield self._bad(artifact, s, 1, "could not decompress (%s)" % err, opts)
            if key_error:
                yield from error_rows(self, artifact, [(0, key_error, "")], s.session_id, s.cwd)
            return
        errors: list = []
        yield from self._records(artifact, s, _iter_lines(data, errors), opts)
        if key_error:
            errors.append((0, key_error, ""))
        yield from error_rows(self, artifact, errors, s.session_id, s.cwd)

    @staticmethod
    def _legacy_key(artifact: Artifact, session_id: str) -> tuple[str, str]:
        """(session key, error) for `session_id` from the sibling legacy
        `sessions.json`. A missing file is no error; a file that cannot be
        read, does not decode or is not a JSON object returns the whole-file
        message (`sessions.json unreadable (<reason>)`, `sessions.json
        unparseable (<reason>)`, `sessions.json is not a JSON object`) for a
        `parser:` row of the transcript that looked the key up (issue 177)."""
        store = artifact.disk_path.parent / "sessions.json"
        if store.is_symlink() or not store.is_file():
            return "", ""
        try:
            with open(store, encoding="utf-8", errors="replace") as fh:
                data = json.load(fh)
        except OSError as e:
            return "", "sessions.json unreadable (%s)" % e
        except ValueError as e:
            return "", "sessions.json unparseable (%s)" % e
        if not isinstance(data, dict):
            return "", "sessions.json is not a JSON object"
        for key, entry in data.items():
            if isinstance(entry, dict) and entry.get("sessionId") == session_id:
                return str(key), ""
        return "", ""

    # -- SQLite store -------------------------------------------------------------------
    def _parse_db(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        with open_copy(artifact.disk_path) as con:
            tables = table_names(con)
            windows: dict[str, dict] = {}
            if "session_windows" in tables:
                for w in con.execute("select * from session_windows"):
                    w = dict(w)
                    windows[str(w.get("session_id"))] = w
            errors: list = []
            shares = self._db_shares(con, errors) if "session_nodes" in tables else {}
            if "transcript_events" in tables:
                yield from self._db_events(artifact, con, windows, shares, opts)
            if "session_transcript_archives" in tables:
                yield from self._db_archives(artifact, con, windows, shares, opts)
            if "session_transcript_cold_archives" in tables:
                yield from self._db_cold(artifact, con, windows, shares, opts)
        # Grants whose generation has no transcript rows in the database.
        for sid, share in list(shares.items()):
            yield self._share_row(artifact, _Session(sid), *share)
        yield from error_rows(self, artifact, errors)

    @staticmethod
    def _db_shares(con, errors: list) -> dict[str, tuple[int, dict]]:
        """{generation: (rowid, publicShare)} from `session_nodes.entry_json`;
        an `entry_json` that does not decode is appended to `errors`."""
        shares: dict[str, tuple[int, dict]] = {}
        for r in con.execute(
            "select rowid as _rowid, current_session_id, entry_json from session_nodes"
            " order by rowid"
        ):
            raw = r["entry_json"] if isinstance(r["entry_json"], str) else ""
            try:
                entry = json.loads(raw)
            except ValueError as e:
                errors.append((r["_rowid"], "session_nodes entry_json unparseable (%s)" % e, raw))
                continue
            grant = entry.get("publicShare") if isinstance(entry, dict) else None
            if isinstance(grant, dict) and grant.get("id"):
                sid = str(grant.get("sessionId") or r["current_session_id"] or "")
                shares.setdefault(sid, (r["_rowid"], grant))
        return shares

    def _parse_state_db(self, artifact: Artifact) -> Iterator[Row]:
        """`backup uploaded:` rows from `state/openclaw.sqlite` `backup_runs`."""
        if not is_sqlite(artifact.disk_path):
            yield from error_rows(
                self, artifact, [(0, "state/openclaw.sqlite is not a SQLite database", "")]
            )
            return
        try:
            with open_copy(artifact.disk_path) as con:
                if "backup_runs" not in table_names(con):
                    return
                runs = [
                    dict(r)
                    for r in con.execute(
                        "select rowid as _rowid, id, created_at, archive_path, status,"
                        " manifest_json from backup_runs order by created_at, id"
                    )
                ]
        except sqlite3.DatabaseError as e:
            yield from error_rows(
                self, artifact, [(0, "state/openclaw.sqlite unreadable (%s)" % e, "")]
            )
            return
        errors: list = []
        for r in runs:
            raw = r["manifest_json"] if isinstance(r.get("manifest_json"), str) else ""
            try:
                manifest = json.loads(raw)
            except ValueError as e:
                errors.append((r["_rowid"], "backup_runs manifest_json unparseable (%s)" % e, raw))
                continue
            text = self._backup_text(r, manifest if isinstance(manifest, dict) else {})
            if text:
                row = self.base_row(artifact)
                row.source_line = r["_rowid"]
                row.timestamp_utc = to_utc(r.get("created_at"))
                row.turn_type = "system"
                row.text = text
                yield row
        yield from error_rows(self, artifact, errors)

    @staticmethod
    def _backup_text(run: dict, manifest: dict) -> str:
        """The `backup uploaded:` text of a successful upload or Git backup;
        `""` for a failed run, a local archive or a Git push that failed."""
        if run.get("status") != "ok":
            return ""
        location = manifest.get("location")
        location = location if isinstance(location, dict) else {}
        target = manifest.get("target")
        pushed = manifest.get("kind") == "git" and target and manifest.get("pushFailed") is not True
        if not location and not pushed:
            return ""
        return (
            "backup uploaded: %s to %s key %s namespace %s"
            " (from state/openclaw.sqlite backup_runs, created_at)"
            % (
                manifest.get("kind") or "-",
                location.get("name") or run.get("archive_path") or "-",
                location.get("key") or target or "-",
                location.get("namespace") or manifest.get("namespace") or "-",
            )
        )

    @staticmethod
    def _window_session(
        session_id: str,
        windows: dict[str, dict],
        shares: dict[str, tuple[int, dict]],
        key: str = "",
        extra: str = "",
    ) -> _Session:
        w = windows.get(session_id) or {}
        parts: list[str] = []
        for col in (
            "channel",
            "account_id",
            "chat_type",
            "reason",
            "previous_session_id",
            "parent_session_key",
            "spawned_by",
            "display_name",
        ):
            if w.get(col) not in (None, ""):
                parts.append("%s=%s" % (col, w[col]))
        if extra:
            parts.append(extra)
        if w.get("model_provider"):
            parts.append("model_provider=%s" % w["model_provider"])
        s = _Session(
            session_id,
            key or str(w.get("session_key") or ""),
            " ".join(parts),
            str(w.get("model") or ""),
            str(w.get("model_provider") or ""),
        )
        s.shares = shares
        return s

    def _db_events(
        self, artifact: Artifact, con, windows: dict[str, dict], shares: dict, opts: Options
    ) -> Iterator[Row]:
        s: _Session | None = None
        for r in con.execute(
            "select rowid as _rowid, session_id, seq, event_json, event_zstd, created_at "
            "from transcript_events order by session_id, seq"
        ):
            r = dict(r)
            sid = str(r.get("session_id") or "")
            if s is None or s.session_id != sid:
                s = self._window_session(sid, windows, shares)
            line = r["_rowid"]
            raw = r.get("event_json")
            if raw is None and r.get("event_zstd") is not None:
                data, err = _maybe_zstd(r["event_zstd"])
                if data is None:
                    if not s.started:
                        yield from self._start(
                            artifact, s, line, to_utc(r.get("created_at")), None, opts
                        )
                    yield self._bad(
                        artifact,
                        s,
                        line,
                        "event seq %s could not be decompressed (%s)" % (r.get("seq"), err),
                        opts,
                        to_utc(r.get("created_at")),
                    )
                    continue
                raw = data.decode("utf-8", errors="replace")
            err = None  # set only when the JSON does not parse
            try:
                rec = json.loads(
                    raw
                    if isinstance(raw, str)
                    else bytes(raw or b"").decode("utf-8", errors="replace")
                )
            except ValueError as e:
                rec = None
                err = str(e)
            if not isinstance(rec, dict):
                if not s.started:
                    yield from self._start(
                        artifact, s, line, to_utc(r.get("created_at")), None, opts
                    )
                yield self._bad(
                    artifact,
                    s,
                    line,
                    "event seq %s unreadable: %s"
                    % (r.get("seq"), err if err is not None else "not a JSON object"),
                    opts,
                    to_utc(r.get("created_at")),
                )
                continue
            yield from self._entry_rows(artifact, s, line, rec, r.get("created_at"), opts)

    def _db_archives(
        self, artifact: Artifact, con, windows: dict[str, dict], shares: dict, opts: Options
    ) -> Iterator[Row]:
        for r in con.execute(
            "select rowid as _rowid, session_id, session_key, reason, encoding, archive_name, "
            "created_at, archive_blob from session_transcript_archives "
            "order by created_at"
        ):
            r = dict(r)
            sid = str(r.get("session_id") or "")
            extra = "archive=%s name=%s" % (r.get("reason") or "", r.get("archive_name") or "")
            s = self._window_session(sid, windows, shares, str(r.get("session_key") or ""), extra)
            line = r["_rowid"]
            data, err = _maybe_zstd(r.get("archive_blob") or b"")
            if data is None:
                yield self._bad(
                    artifact,
                    s,
                    line,
                    "archive %s could not be decompressed (%s)"
                    % (r.get("archive_name") or sid, err),
                    opts,
                    to_utc(r.get("created_at")),
                )
                continue
            errors: list = []
            yield from self._records(artifact, s, _iter_lines(data, errors), opts, fixed_line=line)
            label = "archive %s" % (r.get("archive_name") or sid)
            yield from self._blob_errors(artifact, s, line, label, errors)

    def _db_cold(
        self, artifact: Artifact, con, windows: dict[str, dict], shares: dict, opts: Options
    ) -> Iterator[Row]:
        for r in con.execute(
            "select rowid as _rowid, session_id, archive_name, archived_at, archive_blob "
            "from session_transcript_cold_archives where storage = 'sqlite' order by archived_at"
        ):
            r = dict(r)
            sid = str(r.get("session_id") or "")
            s = self._window_session(
                sid, windows, shares, extra="cold_archive=%s" % (r.get("archive_name") or "")
            )
            line = r["_rowid"]
            data, err = _maybe_zstd(r.get("archive_blob") or b"")
            if data is None:
                yield self._bad(
                    artifact,
                    s,
                    line,
                    "cold archive %s could not be decompressed (%s)"
                    % (r.get("archive_name") or sid, err),
                    opts,
                    to_utc(r.get("archived_at")),
                )
                continue
            errors: list = []
            yield from self._records(artifact, s, _iter_lines(data, errors), opts, fixed_line=line)
            label = "cold archive %s" % (r.get("archive_name") or sid)
            yield from self._blob_errors(artifact, s, line, label, errors)


__all__ = ["OpenClawParser", "tool_args_text"]
