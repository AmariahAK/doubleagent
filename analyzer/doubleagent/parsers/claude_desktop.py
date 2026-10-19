"""Claude Desktop local agent sessions (Cowork, the Code tab, scheduled tasks).

Closed source. The shapes come from the app bundle 2.31226.1
(`Contents/Resources/app.asar`, macOS), read without running it, with the
top-level keys of `scheduled-tasks.json` and `git-worktrees.json` observed
on an install of the same version; see `research/claude-desktop.md`. Paths
below are relative to the app-data directory, one of the catalog bases
`Library/Application Support/Claude[-3p]`, `.config/Claude[-3p]`,
`AppData/Roaming/Claude[-3p]`, `AppData/Local/Claude[-3p]`,
`AppData/Local/Claude-Data[/<package family>]` or, for the MSIX build,
whose MSIX container redirects `AppData/Roaming/Claude` there,
`AppData/Local/Packages/<Claude_* or AnthropicPBC.Claude_*>/LocalCache/Roaming/Claude`
(observed on Windows 11, 2026-10-10, and Ubuntu 26.04, 2026-10-11);
`<acct>` and `<org>` are account and organization UUIDs (or their first
eight hex digits). Files:

* `local-agent-mode-sessions/<acct>/<org>/[agent/]<session dir>/.claude/
  projects/<slug>/<cliSessionId>.jsonl`, the subagent files under
  `<cliSessionId>/subagents/`, the same under
  `claude-code-sessions/<acct>/<org>/<session dir>/`, and
  `claude-code-sessions/<acct>/<org>/imported-staging/<cliSessionId>.jsonl`:
  Claude Code JSONL, read by `ClaudeCodeParser._parse_session`, so the
  field names in `claude_code.py` apply. The rows keep the JSONL
  `sessionId`. `project_path` is taken from the session record's
  `userSelectedFolders[0]` when the record is found and has one, because
  the JSONL `cwd` is the guest path `/sessions/<name>` when the CLI runs
  in the desktop's VM; otherwise it is the JSONL `cwd` as claude-code sets
  it. The record is `<org>/local_<uuid>.json` or
  `<org>/agent/local_<uuid>.json`, found from the session dir name
  `local_<uuid>` or its eight-hex short form; staged imports have no
  session dir and keep the JSONL `cwd`.
* `local-agent-mode-sessions/<acct>/<org>/[agent/]<session dir>/audit.jsonl`:
  one Agent SDK message per line plus `_audit_timestamp` (ISO 8601) and
  `_audit_hmac`. Read: `type`, `subtype`, `timestamp`, `_audit_timestamp`,
  `session_id`, `cwd`, `model`, `client_platform`, `isSynthetic`,
  `message.model`, `message.content` blocks (`text`, `tool_use` with `id`,
  `name`, `input`; `tool_result` with `tool_use_id`, `content`,
  `is_error`; `thinking`, `redacted_thinking`), `tool_name`, `tool_input`,
  `decision`, `granted`, `source`, `scheduled_task_id`, `matched_ops`,
  `num_turns`, `is_error`. Permission events (`system` subtypes
  `permission_request`, `permission_response`, `permission_auto_approved`,
  `permission_auto_denied`) and `result` lines are always `system` rows.
  The `system` `init` line's `model` is a `system` row `model: <id>`
  (issues 96 and 97) followed by an `init: cwd=<cwd> model=<model>` row,
  and each `assistant` line whose `message.model` differs is
  `model: <old> -> <new>` before its rows; one tracker per session id. A
  `system` `model_refusal_fallback` line (the subtype is in the bundle,
  its fields are not recorded) is a `system` row
  `model_refusal_fallback: <compact JSON of the line less its envelope>`.
  Desktop prompts (`client_platform` `desktop_app`) are `user` rows,
  `isSynthetic` notifications and other user text are `context:` system
  rows, and the `assistant` and `tool_result` blocks are rows as in the
  transcript. Every line is read on every run, whether or not the session
  dir holds a transcript. The file is a secondary source (issue 122): its
  `user`, `assistant`, tool and `model:` rows repeat the transcript's, and
  `dedup.deduplicate` drops those the transcript also yields, so a session
  whose transcript is gone keeps its turns from the audit log, and the
  permission, `result` and `init` rows, which the transcript does not
  record, are always kept. Each row carries the line's own time (the
  prompt's `timestamp`, else `_audit_timestamp`, the write time) and the
  default 2-second window applies: the desktop stamps a prompt as it sends
  it and logs each SDK message as the query loop yields it, but no real
  audit log has been compared with its transcript, so the gap is not
  measured. Known misses, shown twice: a Bash `tool_use` whose transcript
  record has `wireToolInputs` (the audit line has only `input`), a
  persisted tool output, and a prompt the CLI received later than the
  desktop stamped it.
  To pair with the transcript rows, the session id is the record's
  `cliSessionId` (the transcript's file name and JSONL `sessionId`), else
  the line's `session_id`, and `project_path` is the record's
  `userSelectedFolders[0]`, as for the transcript, else the first `init`
  line's `cwd` (the CLI's working directory, which the transcript records
  as its JSONL `cwd`), else the record's `cwd`.
* `local-agent-mode-sessions/<acct>/<org>/[agent/]local_<uuid>.json` (Cowork)
  and `claude-code-sessions/<acct>/<org>/local_<uuid>.json` (Code tab):
  `sessionId`, `cliSessionId`, `sessionType`, `title`, `createdAt`,
  `model`, `userSelectedFolders`, `originCwd`, `cwd`, `branch` (Code tab),
  `initialMessage`, `error`, `errorCategory`, `errorAt`. One `system` row
  at `createdAt`. Both forms are a secondary source (issue 122). A Cowork
  record's `initialMessage` is always a `user` row, with an empty
  `timestamp_utc` because the record keeps no time for the prompt
  (`createdAt` is the session's), so it matches the transcript's or the
  audit log's copy on text within the session, and survives when both
  are gone; the record's own `system` rows have no twin and are always
  kept. A Code-tab record's `initialMessage` is a `user` row at
  `createdAt` only when the session's transcript is not in the input
  (`_session_collected`): that transcript is `~/.claude/projects/` under
  agent `claude-code`, and the rule pairs rows of one agent only, so a
  row yielded beside it would be shown twice. On a
  Code-tab record the row's text ends with the persisted Remote Control
  state, `remote_control=<remoteControlUserEnabled> bridges=<number of
  bridgeSessionIds> spawned_remotely=<remoteControlSpawn is a non-empty
  object> steered_remotely=<steeredByRemoteClient>` (absent keys read
  `false` and `0`; real installs have shown only those), and a
  `remoteControlLiveAtUpdateQuit` object with a numeric `at` (epoch ms)
  is a second `system` row at that time, `remote control live at update
  quit`. The `true` values rest on the bundle and the fixture only. The
  record row of either kind ends with ` permission_mode=<permissionMode>
  effort=<effort>` (`-` for an absent key; the Cowork record's bundle key
  list has no `effort`, so it usually reads `-` there). Then, for issue 93,
  one `system` row per entry of `alwaysAllowedReasons` and
  `sessionPermissionUpdates`, `permission grant: <key> <entry> (as of
  <field>)`, and one per `chromePermissionMode`, `chromeAllowedDomains`,
  `cuAllowedApps`, `cuGrantFlags` and `cuFlagsGrantedAt` that holds a
  value (not absent, empty string, `[]` or `{}`), `permission grant:
  <key>=<value> (as of <field>)`; an entry or value that is not a string is
  its compact JSON. The record keeps no time per grant, so these rows take
  `lastActivityAt` (the grant was held by then), else `createdAt`, and
  `<field>` names which. The entries' inner shape is not determined: real
  installs have shown both lists empty and `chromePermissionMode` a string.
  The Cowork grants `approvedToolNames`, `webFetchAllowedUrls`,
  `egressAllowedDomains`, `userApprovedFileAccessPaths`, `enabledMcpTools`
  and `fileDeleteApprovedMounts` (issue 97; "arrays and objects" in the
  bundle, which key is which not determined) follow at the same time: a
  list is one `permission grant: <key> <entry> (as of <field>)` row per
  entry, an object one `permission grant: <key>.<member>=<value> (as of
  <field>)` row per member, and any other value one `permission grant:
  <key>=<value> (as of <field>)` row.
* `.../scheduled-tasks.json`: `scheduledTasks[]` with `id`,
  `cronExpression` or `fireAt`, `enabled`, `createdAt`, `cwd`,
  `userSelectedFolders`, `permissionMode`, `model`; the row ends with
  ` permission_mode=<permissionMode> model=<model>` (`-` when absent) and
  its `model` column is the task's model.
* `local-agent-mode-sessions/<acct>/<org>/remote-session-spaces.json`:
  `entries[]` with `sessionId` (the server-side session id) and
  `folders[]`, the folders granted to a remote Cowork session. One
  `system` row per folder, `permission setting:
  entries.<sessionId>.folders=<folder> (from <file>, file mtime)`, at the
  file's modification time, `project_path` the folder, `session_id`
  empty. A file that is not a JSON object is one `system` row.
* `git-worktrees.json`: `worktrees{}` values with `path`, `branch`,
  `sourceBranch`, `baseRepo`, `leasedBy` (the desktop session id, kept in
  the text, not as `session_id`), `createdAt`.

Every `createdAt`, `errorAt` and `fireAt` is epoch milliseconds, which
`to_utc` takes as milliseconds because the value is above 1e11.

Not parsed: the claude.ai LevelDB stores, the logs, `spaces.json`,
memory files, `rpm/` and caches, and `claude_desktop_config.json`, whose
`preferences.remoteChatFolderGrants` holds folder grants but which is a
secret-glob file (its `mcpServers.*.env` can embed API keys).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

from ..inputs import Artifact
from ..model import Row, compact
from ..timeutil import to_utc
from .base import (
    Options,
    compact_json,
    error_rows,
    file_mtime,
    iter_jsonl,
    text_of,
    track_change,
)
from .claude_code import ClaudeCodeParser, result_text, tool_summary

BASE = (
    r"^(?:Library/Application Support/Claude(?:-3p)?"
    r"|\.config/Claude(?:-3p)?"
    r"|AppData/Roaming/Claude(?:-3p)?"
    r"|AppData/Local/Claude(?:-3p)?"
    r"|AppData/Local/Claude-Data(?:/[^/]+)?"
    r"|AppData/Local/Packages/(?:AnthropicPBC\.)?Claude_[^/]+/LocalCache/Roaming/Claude)/"
)
_TREES = r"(?:local-agent-mode-sessions|claude-code-sessions)/[^/]+/[^/]+/"
# Group `sess` is the session dir, relative to the home.
TRANSCRIPT_RX = re.compile(
    r"(?P<sess>"
    + BASE
    + _TREES
    + r"(?:agent/)?[^/]+)/\.claude/projects/[^/]+/"
    + r"(?:[^/]+\.jsonl|[^/]+/subagents/(?:[^/]+/)*agent-[^/]+\.jsonl)$"
)
STAGED_RX = re.compile(BASE + r"claude-code-sessions/[^/]+/[^/]+/imported-staging/[^/]+\.jsonl$")
AUDIT_RX = re.compile(
    r"(?P<sess>" + BASE + r"local-agent-mode-sessions/[^/]+/[^/]+/(?:agent/)?[^/]+)/audit\.jsonl$"
)
RECORD_RX = re.compile(BASE + r"(?P<tree>" + _TREES + r")(?:agent/)?local_[0-9a-f-]{36}\.json$")
SCHED_RX = re.compile(BASE + _TREES + r"scheduled-tasks\.json$")
WORKTREE_RX = re.compile(BASE + r"git-worktrees\.json$")
SPACES_RX = re.compile(BASE + r"local-agent-mode-sessions/[^/]+/[^/]+/remote-session-spaces\.json$")

LONG_RX = re.compile(r"^local_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
SHORT_RX = re.compile(r"^[0-9a-f]{8}$")


def _bool(v) -> str:
    """`true`/`false` as in the JSON, the value as text otherwise."""
    if v is None:
        return ""
    return json.dumps(v) if isinstance(v, bool) else str(v)


def _flag(v) -> str:
    """`true` only for a JSON true; absent or anything else is `false`."""
    return "true" if v is True else "false"


def _str(v) -> str:
    return "" if v is None else str(v)


def _value(v) -> str:
    """A grant value as text: a string as it is, anything else as JSON."""
    return v if isinstance(v, str) else compact_json(v)


# Session-record keys that hold per-session permission grants (research
# section 8): lists read one row per entry, then keys read one row each.
GRANT_LISTS = ("alwaysAllowedReasons", "sessionPermissionUpdates")
GRANT_KEYS = (
    "chromePermissionMode",
    "chromeAllowedDomains",
    "cuAllowedApps",
    "cuGrantFlags",
    "cuFlagsGrantedAt",
)
# Cowork tool, network and folder grants (research section 8, "arrays and
# objects"; which key is which type is not determined): a list is one row
# per entry, an object one row per member, anything else one row.
COWORK_GRANTS = (
    "approvedToolNames",
    "webFetchAllowedUrls",
    "egressAllowedDomains",
    "userApprovedFileAccessPaths",
    "enabledMcpTools",
    "fileDeleteApprovedMounts",
)
# Envelope keys of an audit line, left out of a generic row's JSON.
AUDIT_ENVELOPE = frozenset(
    (
        "type",
        "subtype",
        "uuid",
        "session_id",
        "timestamp",
        "_audit_timestamp",
        "_audit_hmac",
        "_audit_redactions",
    )
)


def _read_json(path: Path):
    """The parsed file, or None when it cannot be read or parsed."""
    try:
        return json.loads(path.read_bytes().decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


def _plain_dir(d: Path) -> bool:
    return not d.is_symlink() and d.is_dir()


def _plain_file(f: Path) -> bool:
    return not f.is_symlink() and f.is_file()


def _org_dir(sess: Path) -> Path:
    return sess.parent.parent if sess.parent.name == "agent" else sess.parent


def _find_record(sess: Path) -> dict | None:
    """The session record of a session dir named `local_<uuid>` or with the
    UUID's first eight hex digits, from `<org>/` or `<org>/agent/`; never
    through a symlink."""
    org = _org_dir(sess)
    name = sess.name
    if not (LONG_RX.match(name) or SHORT_RX.match(name)):
        return None
    if org.is_symlink() or sess.parent.is_symlink():
        return None
    for d in (org, org / "agent"):
        if not _plain_dir(d):
            continue
        if LONG_RX.match(name):
            candidates = [d / (name + ".json")]
        else:
            try:
                candidates = sorted(d.glob("local_%s-*.json" % name))
            except OSError:
                candidates = []
        for f in candidates:
            if not LONG_RX.match(f.name[: -len(".json")]) or not _plain_file(f):
                continue
            rec = _read_json(f)
            if isinstance(rec, dict):
                return rec
    return None


def _jsonl_files(d: Path, name: str = "*.jsonl") -> list[Path]:
    """`d/*/<name>` regular files, through no symlink."""
    if not _plain_dir(d):
        return []
    out = []
    try:
        for slug in sorted(d.iterdir()):
            if _plain_dir(slug):
                out.extend(f for f in sorted(slug.glob(name)) if _plain_file(f))
    except OSError:
        return out
    return out


def _has_transcript(sess: Path) -> bool:
    claude = sess / ".claude"
    return _plain_dir(sess) and _plain_dir(claude) and bool(_jsonl_files(claude / "projects"))


def _folder(rec: dict | None) -> str:
    if not rec:
        return ""
    folders = rec.get("userSelectedFolders")
    if isinstance(folders, list) and folders and folders[0]:
        return str(folders[0])
    return ""


class ClaudeDesktopParser(ClaudeCodeParser):
    agent = "claude-desktop"
    name = "claude-desktop"
    has_secondary = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return any(
            rx.match(rel)
            for rx in (
                TRANSCRIPT_RX,
                STAGED_RX,
                AUDIT_RX,
                RECORD_RX,
                SCHED_RX,
                WORKTREE_RX,
                SPACES_RX,
            )
        )

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        m = TRANSCRIPT_RX.match(rel)
        if m:
            yield from self._transcript(artifact, opts, self._sess(artifact, m.group("sess")))
        elif STAGED_RX.match(rel):
            yield from self._transcript(artifact, opts, None)
        elif AUDIT_RX.match(rel):
            m = AUDIT_RX.match(rel)
            assert m is not None
            yield from self._audit(artifact, opts, self._sess(artifact, m.group("sess")))
        elif RECORD_RX.match(rel):
            yield from self._record(artifact)
        elif SCHED_RX.match(rel):
            yield from self._scheduled(artifact)
        elif WORKTREE_RX.match(rel):
            yield from self._worktrees(artifact)
        elif SPACES_RX.match(rel):
            yield from self._spaces(artifact)

    @staticmethod
    def _sess(artifact: Artifact, sess_rel: str) -> Path:
        return artifact.home.disk_path / sess_rel

    def _system(self, artifact: Artifact, text: str, line: int = 0) -> Row:
        row = self.base_row(artifact)
        row.turn_type = "system"
        row.source_line = line
        row.text = compact(text)
        return row

    # -- transcripts -----------------------------------------------------------

    def _transcript(self, artifact: Artifact, opts: Options, sess: Path | None) -> Iterator[Row]:
        folder = _folder(_find_record(sess)) if sess is not None else ""
        for row in self._parse_session(artifact, opts):
            if folder:
                row.project_path = folder
            yield row

    # -- audit.jsonl -----------------------------------------------------------

    def secondary(self, artifact: Artifact) -> bool:
        return bool(AUDIT_RX.match(artifact.rel) or RECORD_RX.match(artifact.rel))

    @staticmethod
    def _init_cwd(artifact: Artifact) -> str:
        """The `cwd` of the audit log's first `system` `init` line, the CLI's
        working directory, which its transcript records as the JSONL `cwd`."""
        for _, line in iter_jsonl(artifact.disk_path, []):
            if line.get("type") == "system" and line.get("subtype") == "init":
                cwd = _str(line.get("cwd"))
                if cwd:
                    return cwd
        return ""

    def _audit(self, artifact: Artifact, opts: Options, sess: Path) -> Iterator[Row]:
        rec = _find_record(sess)
        project = _folder(rec) or self._init_cwd(artifact) or (_str(rec.get("cwd")) if rec else "")
        cli_id = _str(rec.get("cliSessionId")) if rec else ""
        errors: list = []
        models: dict = {}
        last_sid = cli_id
        for n, line in iter_jsonl(artifact.disk_path, errors):
            sid = cli_id or _str(line.get("session_id"))
            last_sid = sid or last_sid
            ts = to_utc(line.get("timestamp")) or to_utc(line.get("_audit_timestamp"))

            def row(turn_type: str, text: str, n=n, ts=ts, sid=sid) -> Row:
                r = self.base_row(artifact)
                r.source_line = n
                r.timestamp_utc = ts
                r.session_id = sid
                r.project_path = project
                r.turn_type = turn_type
                r.text = compact(text)
                return r

            ltype = line.get("type")
            subtype = line.get("subtype")
            if ltype == "system" and subtype in (
                "permission_request",
                "permission_response",
                "permission_auto_approved",
                "permission_auto_denied",
            ):
                tool = _str(line.get("tool_name"))
                if subtype == "permission_request":
                    inp = line.get("tool_input")
                    text = "permission request: %s %s" % (
                        tool,
                        "" if inp is None else tool_summary(tool, inp),
                    )
                elif subtype == "permission_response":
                    text = "permission response: %s %s granted=%s" % (
                        tool,
                        _str(line.get("decision")),
                        _bool(line.get("granted")),
                    )
                else:
                    word = "approved" if subtype == "permission_auto_approved" else "denied"
                    why = line.get("source") or line.get("scheduled_task_id")
                    if not why and line.get("matched_ops") is not None:
                        why = compact_json(line.get("matched_ops"))
                    text = "permission auto-%s: %s" % (word, tool)
                    if why:
                        text += " (%s)" % why
                r = row("system", text)
                r.tool_name = tool
                yield r
            elif ltype == "result":
                yield row(
                    "system",
                    "result: %s turns=%s error=%s"
                    % (
                        _str(line.get("subtype")),
                        _str(line.get("num_turns")),
                        _bool(line.get("is_error")),
                    ),
                )
            elif ltype == "system" and subtype == "init":
                # The session's model, even when a transcript exists.
                model = _str(line.get("model"))
                text = track_change("model", models, sid, model)
                if text:
                    r = row("system", text)
                    r.model = model
                    yield r
                parts = ["%s=%s" % (k, line.get(k)) for k in ("cwd", "model") if line.get(k)]
                yield row("system", "init: " + " ".join(parts) if parts else "init")
            elif ltype == "system" and subtype == "model_refusal_fallback":
                # The subtype is in the bundle, its fields are not recorded:
                # print them as they are.
                rest = {k: v for k, v in line.items() if k not in AUDIT_ENVELOPE}
                yield row("system", "model_refusal_fallback: " + compact_json(rest))
            elif ltype == "user":
                yield from self._audit_user(line, row)
            elif ltype == "assistant":
                model = _str((line.get("message") or {}).get("model"))
                text = track_change("model", models, sid, model)
                if text:
                    r = row("system", text)
                    r.model = model
                    yield r
                yield from self._audit_assistant(line, row, opts)
        yield from error_rows(self, artifact, errors, last_sid, project)

    @staticmethod
    def _audit_user(line: dict, row) -> Iterator[Row]:
        content = (line.get("message") or {}).get("content")
        blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
        typed = line.get("client_platform") == "desktop_app" and not line.get("isSynthetic")
        for b in blocks:
            if not isinstance(b, dict):
                continue
            btype = b.get("type")
            if btype == "tool_result":
                text = result_text(b.get("content"))
                if b.get("is_error"):
                    text = "[error] " + text
                r = row("tool_result", text)
                r.tool_use_id = _str(b.get("tool_use_id"))
                yield r
            elif btype in ("text", "image"):
                text = text_of([b])
                if not text:
                    continue
                if typed:
                    yield row("user", text)
                elif line.get("isSynthetic"):
                    yield row("system", "context: notification: " + text)
                else:
                    yield row("system", "context: " + text)

    @staticmethod
    def _audit_assistant(line: dict, row, opts: Options) -> Iterator[Row]:
        msg = line.get("message") or {}
        model = _str(msg.get("model"))
        content = msg.get("content")
        blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
        for b in blocks:
            if not isinstance(b, dict):
                continue
            btype = b.get("type")
            if btype == "tool_use":
                name = _str(b.get("name"))
                r = row("tool_use", tool_summary(name, b.get("input")))
                r.tool_name = name
                r.tool_use_id = _str(b.get("id"))
            elif btype == "text" and b.get("text"):
                r = row("assistant", _str(b.get("text")))
            elif btype == "thinking" and opts.include_thinking and b.get("thinking"):
                r = row("thinking", _str(b.get("thinking")))
            elif btype == "redacted_thinking" and opts.include_thinking:
                r = row("thinking", "[redacted]")
            else:
                continue
            r.model = model
            yield r

    # -- session records -------------------------------------------------------

    def _record(self, artifact: Artifact) -> Iterator[Row]:
        m = RECORD_RX.match(artifact.rel)
        assert m is not None
        code = m.group("tree").startswith("claude-code-sessions/")
        rec = _read_json(artifact.disk_path)
        if not isinstance(rec, dict):
            yield self._system(artifact, "parser: session record is not a JSON object", 1)
            return
        cli_id = _str(rec.get("cliSessionId"))
        project = _folder(rec) or _str(rec.get("originCwd")) or _str(rec.get("cwd"))
        created = to_utc(rec.get("createdAt"))
        model = _str(rec.get("model"))
        title = _str(rec.get("title"))

        def row(turn_type: str, text: str, ts: str = created) -> Row:
            r = self.base_row(artifact)
            r.source_line = 1
            r.timestamp_utc = ts
            r.session_id = cli_id
            r.project_path = project
            r.git_branch = _str(rec.get("branch")) if code else ""
            r.model = model
            r.turn_type = turn_type
            r.text = compact(text)
            return r

        mode_effort = " permission_mode=%s effort=%s" % (
            _str(rec.get("permissionMode")) or "-",
            _str(rec.get("effort")) or "-",
        )
        if code:
            spawn = rec.get("remoteControlSpawn")
            bridges = rec.get("bridgeSessionIds")
            yield row(
                "system",
                'desktop code session: "%s" remote_control=%s bridges=%d '
                "spawned_remotely=%s steered_remotely=%s"
                % (
                    title,
                    _flag(rec.get("remoteControlUserEnabled")),
                    len(bridges) if isinstance(bridges, list) else 0,
                    _flag(isinstance(spawn, dict) and bool(spawn)),
                    _flag(rec.get("steeredByRemoteClient")),
                )
                + mode_effort,
            )
            quit_ = rec.get("remoteControlLiveAtUpdateQuit")
            at = quit_.get("at") if isinstance(quit_, dict) else None
            if isinstance(at, (int, float)) and not isinstance(at, bool):
                yield row("system", "remote control live at update quit", to_utc(at))
        else:
            yield row(
                "system",
                'desktop session: %s "%s"' % (_str(rec.get("sessionType")), title) + mode_effort,
            )
        yield from self._grants(rec, row, created)
        initial = _str(rec.get("initialMessage"))
        if initial and not code:
            # Cowork: always, with no time of its own (a secondary source).
            yield row("user", initial, "")
        elif initial and not self._session_collected(artifact, rec):
            # Code tab: its transcript is claude-code's, another agent, so
            # the rule could not pair the two; only when it is absent.
            yield row("user", initial)
        if rec.get("error"):
            cat = _str(rec.get("errorCategory"))
            err = _str(rec.get("error"))
            yield row(
                "system",
                "session error: %s" % ("%s: %s" % (cat, err) if cat else err),
                to_utc(rec.get("errorAt")),
            )

    @staticmethod
    def _grants(rec: dict, row, created: str) -> Iterator[Row]:
        """One `system` row per `alwaysAllowedReasons` and
        `sessionPermissionUpdates` entry and per browser or computer-use
        grant key that holds a value. The record keeps no time per grant, so
        the rows take `lastActivityAt` (the grant held by then), else
        `createdAt`, and say which."""
        last = to_utc(rec.get("lastActivityAt"))
        ts, field = (last, "lastActivityAt") if last else (created, "createdAt")
        for key in GRANT_LISTS:
            entries = rec.get(key)
            if isinstance(entries, list):
                for entry in entries:
                    yield row(
                        "system",
                        "permission grant: %s %s (as of %s)" % (key, _value(entry), field),
                        ts,
                    )
        for key in GRANT_KEYS:
            v = rec.get(key)
            if v is None or v == "" or v == [] or v == {}:
                continue
            yield row("system", "permission grant: %s=%s (as of %s)" % (key, _value(v), field), ts)
        for key in COWORK_GRANTS:
            v = rec.get(key)
            if isinstance(v, list):
                for entry in v:
                    yield row(
                        "system",
                        "permission grant: %s %s (as of %s)" % (key, _value(entry), field),
                        ts,
                    )
            elif isinstance(v, dict):
                for k, entry in v.items():
                    yield row(
                        "system",
                        "permission grant: %s.%s=%s (as of %s)" % (key, k, _value(entry), field),
                        ts,
                    )
            elif v is not None and v != "":
                yield row(
                    "system", "permission grant: %s=%s (as of %s)" % (key, _value(v), field), ts
                )

    @staticmethod
    def _session_collected(artifact: Artifact, rec: dict) -> bool:
        """Whether a transcript or audit log for the record's session is in
        the input: the session dir (full or short name, beside the record or
        in its org dir), the org's `imported-staging/`, or for the Code tab
        `~/.claude/projects/*/`."""
        rdir = artifact.disk_path.parent
        org = rdir.parent if rdir.name == "agent" else rdir
        sid = _str(rec.get("sessionId")) or artifact.disk_path.stem
        names = [sid]
        if LONG_RX.match(sid):
            names.append(sid[len("local_") : len("local_") + 8])
        for d in dict.fromkeys((rdir, org)):
            for name in names:
                sess = d / name
                if not _plain_dir(sess):
                    continue
                if _plain_file(sess / "audit.jsonl") or _has_transcript(sess):
                    return True
        cli_id = _str(rec.get("cliSessionId"))
        if cli_id:
            staging = org / "imported-staging"
            if _plain_dir(staging) and _plain_file(staging / (cli_id + ".jsonl")):
                return True
            claude = artifact.home.disk_path / ".claude"
            if _plain_dir(claude) and _jsonl_files(claude / "projects", cli_id + ".jsonl"):
                return True
        return False

    # -- scheduled tasks and worktrees -----------------------------------------

    def _scheduled(self, artifact: Artifact) -> Iterator[Row]:
        doc = _read_json(artifact.disk_path)
        if not isinstance(doc, dict):
            yield self._system(artifact, "parser: unreadable scheduled-tasks.json", 1)
            return
        # A fresh install's file has the markers but no task list yet.
        tasks = doc.get("scheduledTasks")
        if not isinstance(tasks, list):
            return
        for i, task in enumerate(tasks, 1):
            if not isinstance(task, dict):
                continue
            when = task.get("cronExpression") or to_utc(task.get("fireAt"))
            r = self._system(
                artifact,
                "scheduled task: %s %s enabled=%s permission_mode=%s model=%s"
                % (
                    _str(task.get("id")),
                    _str(when),
                    _bool(task.get("enabled")),
                    _str(task.get("permissionMode")) or "-",
                    _str(task.get("model")) or "-",
                ),
                i,
            )
            r.timestamp_utc = to_utc(task.get("createdAt"))
            r.model = _str(task.get("model"))
            r.project_path = _str(task.get("cwd")) or _folder(task)
            yield r

    def _worktrees(self, artifact: Artifact) -> Iterator[Row]:
        doc = _read_json(artifact.disk_path)
        if not isinstance(doc, dict):
            yield self._system(artifact, "parser: unreadable git-worktrees.json", 1)
            return
        # Observed on a fresh Windows install: `{"schemaVersion": 2}` and no
        # `worktrees` key until the Code tab creates one.
        trees = doc.get("worktrees")
        if not isinstance(trees, dict):
            return
        for i, wt in enumerate(trees.values(), 1):
            if not isinstance(wt, dict):
                continue
            text = "worktree created: %s branch=%s from=%s" % (
                _str(wt.get("path")),
                _str(wt.get("branch")),
                _str(wt.get("sourceBranch")),
            )
            if wt.get("leasedBy"):
                text += " leased by %s" % wt.get("leasedBy")
            r = self._system(artifact, text, i)
            r.timestamp_utc = to_utc(wt.get("createdAt"))
            r.project_path = _str(wt.get("baseRepo"))
            r.git_branch = _str(wt.get("branch"))
            yield r

    # -- remote-session-spaces.json --------------------------------------------

    def _spaces(self, artifact: Artifact) -> Iterator[Row]:
        """One standing row per folder granted to a remote Cowork session:
        `entries[].folders[]`, keyed by the entry's `sessionId` (the server's
        id, kept in the text; `session_id` stays empty)."""
        doc, bad = self._settings_doc(artifact, "remote-session-spaces.json")
        if doc is None:
            if bad is not None:
                yield bad
            return
        entries = doc.get("entries")
        if not isinstance(entries, list):
            return
        ts = file_mtime(artifact)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            folders = entry.get("folders")
            if not isinstance(folders, list):
                continue
            sid = _str(entry.get("sessionId"))
            key = "entries.%s.folders" % sid if sid else "entries.folders"
            for folder in folders:
                if folder in (None, ""):
                    continue
                yield self._standing_row(artifact, ts, _str(folder), key, folder)
