"""Kilo Code sessions.

Validated against source, Kilo-Org/kilocode at 76bcfd4 (see
`research/kilo-code.md`), with a synthetic fixture; no real install
was used. Kilo Code's CLI, TUI and server are an OpenCode fork with the same
SQLite and JSON storage, so this parser is `OpenCodeParser` (see
`opencode.py` for the tables, fields and row mapping) pointed at Kilo's
paths, plus the pre-migration task directories of the VS Code extension.

Files, relative to the home directory:

* `.local/share/kilo/kilo.db`, `kilo-<channel>.db`, or a pre-existing
  `opencode-<channel>.db` in the same directory, with WAL sidecars. Kilo
  writes both the V1 `message`/`part` tables and V2 `session_message`;
  V1 is read and V2 only for sessions with no V1 rows, as for OpenCode.
  The `model:` and `permission mode: agent=<name>` rows therefore come
  from each V1 message's model and `agent` (see `opencode.py`); the V2
  `model-switched` and `agent-switched` records are read only for a
  session that has no V1 rows. The OpenCode 2.0 reading (`session_v2`
  headers, `session_message` as the transcript, the 1.x tables only for a
  session it lacks; issue 165) and the full-record `parser: unparseable
  record` and `unparseable part` rows (issue 139) apply here through the
  subclass, though Kilo Code at 87cc35c has no `session_v2` table.
* `.local/share/kilo/storage/{session,message,part,project}/...` and the
  older `.local/share/kilo/project/<slug>/storage/session/...` JSON trees,
  laid out exactly as OpenCode's.
* `<VS Code user dir>/User/globalStorage/kilocode.kilo-code/tasks/<id>/
  api_conversation_history.json`: Roo-style tasks from before the move to
  the OpenCode core. Kilo's own importer reads this file
  (`packages/kilo-vscode/src/legacy-migration/task-store.ts`), so it is the
  one parsed here; `ui_messages.json` repeats the same turns for display.
  It is a JSON array of Anthropic `MessageParam` records: `role`, `content`
  (a string or blocks typed `text`, `image`, `tool_use` with `id`, `name`,
  `input`, `tool_result` with `tool_use_id`, `content`, `is_error`, and
  `thinking` or `reasoning`), plus Roo's `ts` (epoch ms), `isSummary`, and
  top-level `type: "reasoning"` records with `summary` or
  `reasoning_content`. The task's `workspace`, `task` and `ts` come from
  `history_item.json` in the same directory, else the matching entry of
  `tasks/_index.json` (`{entries: [HistoryItem]}`). The session id is the
  directory name. The history item, when found, becomes one `system` row
  with `source_line` 0. No model is recorded. Records without `ts` inherit the
  task's `ts`. `source_line` is the record's 1-based position in the array
  (Roo writes the array on one line). A file cut mid-write keeps every
  complete record before the cut and adds one `system` row (`error_rows`,
  issue 136): `parser: unparseable record <N> (<reason>): <raw>`, carrying
  the cut record's text from its first character to the end of the file,
  or `parser: array cut off after record N` when the cut falls between
  records. Tool calls
  written as XML inside text blocks, as older Roo prompts did, stay in the
  text of the `assistant` row; text blocks that are only
  `<environment_details>` are `system` rows.
* `.local/share/kilo/storage/session_share/<sessionID>.json`: Kilo's cloud
  session marker, `{id, ingestPath, url?}`, written when Kilo's session
  ingest service registers the session (at creation, for a user signed in
  to Kilo); `url`, the public link, is added by `/share` and removed by
  `/unshare`, which keeps the file. One `system` row at the file's
  modification time (issue 153), `session_id` from the file name,
  `session synced: kilo session <id> ingest <ingestPath> share <url>
  (from storage/session_share/<sessionID>.json, file mtime)`, `-` for an
  absent value. A file that is not a JSON object is one `parser:` row.
  The upstream `session_share` table, which Kilo leaves empty, and the
  `session.updated.1` event rows are read by the OpenCode reader, so a
  public URL recorded there gives the OpenCode sync rows too.

Issues 192 and 221, source-derived; not observed on any real install
(Kilo-Org/kilocode at 87cc35c). The OpenCode reader's refusal rows, archive,
session rule, worktree and grant rows and the terminal UI's
`.local/state/kilo/prompt-history.jsonl` (secondary, `{input, mode?,
parts}`) and `prompt-stash.jsonl` (`{input, parts, timestamp}`) apply here
(see `opencode.py`); Kilo keeps no pinned-session file. Kilo's own files,
each row `system` with no `session_id` unless said:

* `.config/kilo/{kilo.jsonc, kilo.json, opencode.jsonc, opencode.json,
  config.json}`, read as JSONC: the `permission` key that an "always"
  approval writes, `{<permission>: {<pattern>: <action>} or <action>}` or
  one action (`ConfigPermissionV1.Info`, `null` the delete sentinel). One
  row per rule at the file's modification time, `permission setting:
  permission.<permission>.<pattern>=<action> (from <file>, file mtime)`,
  `permission.<permission>=<action>` or `permission=<action>`. A file that
  does not decode is one `parser:` row.
* `.local/state/kilo-sandbox-policy/<sha256>/<sha256>.json`, `{enabled,
  mode, allowedHosts, writablePaths, version}`: one `permission setting:
  sandbox.<key>=<value> (from <file>, file mtime)` row per key; and
  `.local/state/kilo-sandbox-preference/<sha256>.json`, `true` or `false`:
  `permission setting: sandbox.enabled=<value> (from <file>, file mtime)`.
  The names are hashes of the session id and directory, so no session.
* `.local/share/kilo/retention/state.json`, `{at, scanned, deleted,
  skippedActive, failed, durationMs, cancelled?, reclaimedBytes?}`: one row
  at `at`, `sessions deleted by retention: deleted=<n> scanned=<n>
  skippedActive=<n> failed=<n> durationMs=<n>[ cancelled=<v>][
  reclaimedBytes=<n>] (from retention/state.json, at)`.
* `.local/share/kilo/log/<time>.log`, lines `<LEVEL> <UTC time> +<n>ms
  <key>=<value>... <message>`: the remote control lines only, `remote
  control: connection enabled connected=<v>`, `remote control: connection
  disabled` (line time), `remote control: session started model=<model>
  directory=<directory>` (at `startedAt`, with `sessionID` and the
  directory as `project_path`) and `remote control: session ended
  reason=<reason> durationMs=<n> startedAt=<time>` (line time, with
  `sessionID`), each ending `(from log/<file>, <time basis>)`. Remote
  control lets Kilo Cloud drive and create sessions on this host over a
  live channel; the transcript stays in `kilo.db` and the vendor's copy is
  the ingest sync the cloud session marker records, so these rows are
  neither sync nor relay rows. A line ending with one of the four messages
  without its fields is a `parser: unparseable line` row.
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
    line_text,
    setting_value,
    tail_text,
    text_of,
)
from .gemini_cli import parse_jsonc
from .opencode import OpenCodeParser, tool_summary

TASK_RX = re.compile(
    r"(?:^|/)User/globalStorage/kilocode\.kilo-code/tasks/([^/]+)/api_conversation_history\.json$"
)
# The global config files an "always" approval writes the `permission` key of,
# the first that exists in this order (packages/opencode/src/config/config.ts
# globalConfigFile at 87cc35c).
CONFIG_RX = re.compile(
    r"^\.config/kilo/(?:kilo\.jsonc|kilo\.json|opencode\.jsonc|opencode\.json|config\.json)$"
)
# Beside the state directory, not inside it (`path.dirname(Global.Path.state)`).
SANDBOX_POLICY_RX = re.compile(r"^\.local/state/kilo-sandbox-policy/[^/.][^/]*/[^/.][^/]*\.json$")
SANDBOX_PREFERENCE_RX = re.compile(r"^\.local/state/kilo-sandbox-preference/[^/.][^/]*\.json$")
# A log line: `<LEVEL> <UTC time to the second> +<n>ms <key>=<value>... <message>`.
LOG_HEAD_RX = re.compile(r"^(?:DEBUG|INFO|WARN|ERROR)\s+(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) \+\d+ms ")
REMOTE_MESSAGES = (
    "remote connection enabled",
    "remote connection disabled",
    "remote session started",
    "remote session ended",
)
REMOTE_RX = {
    "remote connection enabled": re.compile(
        r" connected=(?P<connected>\S+) remote connection enabled$"
    ),
    "remote connection disabled": re.compile(r" remote connection disabled$"),
    "remote session started": re.compile(
        r" sessionID=(?P<sid>\S+) startedAt=(?P<started>\S+)(?: model=(?P<model>\S+))?"
        r"(?: directory=(?P<directory>.+?))? remote session started$"
    ),
    "remote session ended": re.compile(
        r" sessionID=(?P<sid>\S+) startedAt=(?P<started>\S+) durationMs=(?P<duration>\d+)"
        r" reason=(?P<reason>\S+) remote session ended$"
    ),
}


def iter_json_array(raw: str, errors: list) -> list[object]:
    """Decode a JSON array element by element so a file truncated mid-write
    still yields its complete leading elements. A record that does not
    decode ends the walk and is appended to `errors` as (position,
    `unparseable record <position> (<reason>)`, the text from the record's
    first character to the end of `raw`); a file that is not an array, an
    array cut off between records and data after the closing bracket are
    (position, message, "")."""
    dec = json.JSONDecoder()
    items: list[object] = []
    i = 0
    n = len(raw)

    def skip(j: int) -> int:
        while j < n and raw[j] in " \t\r\n":
            j += 1
        return j

    i = skip(i)
    if i >= n or raw[i] != "[":
        errors.append((1, "not a JSON array", ""))
        return items
    i = skip(i + 1)
    if i < n and raw[i] == "]":
        return items
    while i < n:
        k = len(items) + 1
        try:
            obj, end = dec.raw_decode(raw, i)
        except ValueError as e:
            errors.append((k, "unparseable record %d (%s)" % (k, e), tail_text(raw, i)))
            return items
        items.append(obj)
        i = skip(end)
        if i < n and raw[i] == ",":
            i = skip(i + 1)
            continue
        if i < n and raw[i] == "]":
            if skip(i + 1) < n:
                errors.append((k + 1, "unexpected data after the array", ""))
            return items
        break
    errors.append((len(items) + 1, "array cut off after record %d" % len(items), ""))
    return items


def _read_json(path: Path):
    try:
        with open(path, "rb") as fh:
            return json.loads(fh.read().decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


class KiloCodeParser(OpenCodeParser):
    agent = "kilo-code"
    name = "kilo-code"
    data_dir = ".local/share/kilo"
    db_prefixes = ("kilo", "opencode")
    # Kilo Code at 87cc35c has no `session_v2` table and no pre-release
    # database that a later build imports, so every database under its
    # directory, `opencode-next.db` included, is primary. Its one secondary
    # source is the terminal UI's `prompt-history.jsonl` (see `opencode.py`).
    has_secondary = True
    next_db = ""
    state_dir = ".local/state/kilo"
    # Kilo's terminal UI keeps no `session.json` of pinned sessions.
    pinned_sessions = False

    def __init__(self) -> None:
        super().__init__()
        dd = re.escape(self.data_dir)
        self.share_rx = re.compile(r"^%s/storage/session_share/([^/]+)\.json$" % dd)
        self.log_rx = re.compile(r"^%s/log/([^/]+\.log)$" % dd)
        self.retention_rx = re.compile(r"^%s/retention/state\.json$" % dd)

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        return bool(
            TASK_RX.search(rel)
            or self.share_rx.match(rel)
            or self.log_rx.match(rel)
            or self.retention_rx.match(rel)
            or CONFIG_RX.match(rel)
            or SANDBOX_POLICY_RX.match(rel)
            or SANDBOX_PREFERENCE_RX.match(rel)
        ) or super().wants(artifact)

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        m = self.share_rx.match(rel)
        if TASK_RX.search(rel):
            yield from self._parse_task(artifact, opts)
        elif m:
            yield from self._parse_share(artifact, m.group(1))
        elif self.log_rx.match(rel):
            yield from self._parse_log(artifact)
        elif self.retention_rx.match(rel):
            yield from self._parse_retention(artifact)
        elif CONFIG_RX.match(rel):
            yield from self._parse_config(artifact)
        elif SANDBOX_POLICY_RX.match(rel) or SANDBOX_PREFERENCE_RX.match(rel):
            yield from self._parse_sandbox(artifact)
        else:
            yield from super().parse(artifact, opts)

    def _setting_row(self, artifact: Artifact, ts: str, text: str, session_id: str = "") -> Row:
        row = self.base_row(artifact)
        row.session_id, row.source_line, row.turn_type = session_id, 1, "system"
        row.timestamp_utc = ts
        row.text = compact(text)
        return row

    # -- standing permission state ----------------------------------------------------
    def _parse_config(self, artifact: Artifact) -> Iterator[Row]:
        """A global config file of `~/.config/kilo`: one `permission setting:
        permission.<permission>.<pattern>=<action> (from <file>, file mtime)`
        row per rule of its `permission` key, `permission.<permission>=<action>`
        for a rule given as one action and `permission=<action>` for a
        `permission` key that is one action, at the file's modification time.
        An "always" approval writes `{<permission>: {<pattern>: "allow"}}`
        here; `null` is Kilo's delete sentinel. A file that does not decode
        as JSONC is one `parser:` row; a file with no `permission` key yields
        nothing."""
        ts = file_mtime(artifact)
        try:
            doc = parse_jsonc(artifact.disk_path.read_bytes())
        except (OSError, ValueError) as e:
            yield self._setting_row(
                artifact, ts, "parser: %s could not be decoded (%s)" % (artifact.rel, e)
            )
            return
        if not isinstance(doc, dict):
            yield self._setting_row(artifact, ts, "parser: %s is not a JSON object" % artifact.rel)
            return
        if "permission" not in doc:
            return
        src = "(from %s, file mtime)" % artifact.rel
        perm = doc["permission"]
        if not isinstance(perm, dict):
            yield self._setting_row(
                artifact, ts, "permission setting: permission=%s %s" % (setting_value(perm), src)
            )
            return
        for name, rule in perm.items():
            if isinstance(rule, dict):
                for pattern, action in rule.items():
                    yield self._setting_row(
                        artifact,
                        ts,
                        "permission setting: permission.%s.%s=%s %s"
                        % (name, pattern, setting_value(action), src),
                    )
            else:
                yield self._setting_row(
                    artifact,
                    ts,
                    "permission setting: permission.%s=%s %s" % (name, setting_value(rule), src),
                )

    def _parse_sandbox(self, artifact: Artifact) -> Iterator[Row]:
        """A sandbox policy file (`kilo-sandbox-policy/<sha256 of session
        id>/<sha256 of directory>.json`, `{enabled, mode, allowedHosts,
        writablePaths, version}`) gives one `permission setting:
        sandbox.<key>=<value> (from <file>, file mtime)` row per key; a
        sandbox preference file (`kilo-sandbox-preference/<sha256 of
        directory>.json`, `true` or `false`) one `permission setting:
        sandbox.enabled=<value>` row. Both at the file's modification time,
        with no `session_id`, since the file names are hashes. A file that
        is not the expected JSON is one `parser:` row."""
        ts = file_mtime(artifact)
        src = "(from %s, file mtime)" % artifact.rel
        doc = _read_json(artifact.disk_path)
        if SANDBOX_PREFERENCE_RX.match(artifact.rel):
            if isinstance(doc, bool):
                yield self._setting_row(
                    artifact,
                    ts,
                    "permission setting: sandbox.enabled=%s %s" % (setting_value(doc), src),
                )
            else:
                yield self._setting_row(
                    artifact, ts, "parser: %s is not true or false" % artifact.rel
                )
            return
        if not isinstance(doc, dict):
            yield self._setting_row(artifact, ts, "parser: %s is not a JSON object" % artifact.rel)
            return
        for key, value in doc.items():
            yield self._setting_row(
                artifact,
                ts,
                "permission setting: sandbox.%s=%s %s" % (key, setting_value(value), src),
            )

    # -- deletion -------------------------------------------------------------------
    def _parse_retention(self, artifact: Artifact) -> Iterator[Row]:
        """`retention/state.json`, the counts of the last automatic deletion
        pass: one `system` row at its `at` (epoch ms), `sessions deleted by
        retention: deleted=<n> scanned=<n> skippedActive=<n> failed=<n>
        durationMs=<n>` with ` cancelled=true` and ` reclaimedBytes=<n>` when
        present and `-` for an absent count, then `(from retention/state.json,
        at)`, with no `session_id`, since the file names no session. A file
        that is not a JSON object is one `parser:` row."""
        doc = _read_json(artifact.disk_path)
        if not isinstance(doc, dict):
            yield self._setting_row(
                artifact, file_mtime(artifact), "parser: retention/state.json is not a JSON object"
            )
            return
        parts = [
            "%s=%s" % (k, setting_value(doc[k]) if doc.get(k) is not None else "-")
            for k in ("deleted", "scanned", "skippedActive", "failed", "durationMs")
        ]
        parts += [
            "%s=%s" % (k, setting_value(doc[k]))
            for k in ("cancelled", "reclaimedBytes")
            if doc.get(k) is not None
        ]
        yield self._setting_row(
            artifact,
            to_utc(doc.get("at")),
            "sessions deleted by retention: %s (from retention/state.json, at)" % " ".join(parts),
        )

    # -- remote control -------------------------------------------------------------
    def _parse_log(self, artifact: Artifact) -> Iterator[Row]:
        """`log/<time>.log`: the remote control lines only, one `system` row
        each, `remote control: ...` and `(from log/<file>, <time basis>)`:
        `connection enabled connected=<true|false>` and `connection disabled`
        at the line's time; `session started model=<model>
        directory=<directory>` at its `startedAt`, with the session as
        `session_id` and the directory as `project_path`; `session ended
        reason=<reason> durationMs=<n> startedAt=<time>` at the line's time,
        with the session. Remote control lets Kilo Cloud drive and create
        sessions on this host; the transcript stays in `kilo.db`, so these
        are not sync rows. A line that ends with one of the four messages
        and lacks the fields it should carry is a `parser: unparseable line`
        row with the line in full; every other line is not read."""
        name = artifact.rel.rsplit("/", 1)[-1]
        errors: list = []
        with open(artifact.disk_path, "rb") as fh:
            for n, raw in enumerate(fh, 1):
                line = line_text(raw)
                msg = next((m for m in REMOTE_MESSAGES if line.endswith(" " + m)), "")
                if not msg:
                    continue
                row = self._remote_row(artifact, name, n, line, msg)
                if row is None:
                    errors.append((n, "unparseable line (%s without its fields)" % msg, line))
                else:
                    yield row
        yield from error_rows(self, artifact, errors)

    def _remote_row(self, artifact: Artifact, name: str, n: int, line: str, msg: str):
        head = LOG_HEAD_RX.match(line)
        fields = REMOTE_RX[msg].search(line) if head else None
        if head is None or fields is None:
            return None
        f = fields.groupdict()
        row = self.base_row(artifact)
        row.source_line, row.turn_type = n, "system"
        row.timestamp_utc = to_utc(head.group(1))
        if msg == "remote connection enabled":
            text = "connection enabled connected=%s" % f["connected"]
            basis = "line time"
        elif msg == "remote connection disabled":
            text, basis = "connection disabled", "line time"
        elif msg == "remote session started":
            row.session_id = f["sid"]
            row.project_path = f.get("directory") or ""
            row.timestamp_utc = to_utc(f["started"]) or row.timestamp_utc
            text = "session started model=%s directory=%s" % (
                f.get("model") or "-",
                f.get("directory") or "-",
            )
            basis = "startedAt"
        else:
            row.session_id = f["sid"]
            text = "session ended reason=%s durationMs=%s startedAt=%s" % (
                f["reason"],
                f["duration"],
                f["started"],
            )
            basis = "line time"
        row.text = compact("remote control: %s (from log/%s, %s)" % (text, name, basis))
        return row

    # -- cloud session marker -------------------------------------------------------
    def _parse_share(self, artifact: Artifact, session_id: str) -> Iterator[Row]:
        """`storage/session_share/<sessionID>.json`: one sync row at the
        file's modification time, or one `parser:` row when the file is not
        a JSON object."""
        doc = _read_json(artifact.disk_path)
        row = self.base_row(artifact)
        row.session_id, row.source_line, row.turn_type = session_id, 1, "system"
        row.timestamp_utc = file_mtime(artifact)
        rel = "storage/session_share/%s.json" % session_id
        if not isinstance(doc, dict):
            row.text = "parser: %s is not a JSON object" % rel
            yield row
            return

        def val(key: str) -> str:
            v = doc.get(key)
            return str(v) if v not in (None, "") else "-"

        row.text = compact(
            "session synced: kilo session %s ingest %s share %s (from %s, file mtime)"
            % (val("id"), val("ingestPath"), val("url"), rel)
        )
        yield row

    # -- legacy Roo-style tasks -----------------------------------------------------
    @staticmethod
    def _history_item(task_dir: Path, task_id: str) -> dict:
        item = None
        f = task_dir / "history_item.json"
        if f.is_file() and not f.is_symlink():
            item = _read_json(f)
        if not isinstance(item, dict):
            idx = task_dir.parent / "_index.json"
            data = _read_json(idx) if idx.is_file() and not idx.is_symlink() else None
            entries = data.get("entries") if isinstance(data, dict) else None
            for e in entries if isinstance(entries, list) else []:
                if isinstance(e, dict) and e.get("id") == task_id:
                    item = e
                    break
        return item if isinstance(item, dict) else {}

    def _parse_task(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        task_dir = artifact.disk_path.parent
        task_id = task_dir.name
        item = self._history_item(task_dir, task_id)
        project = str(item.get("workspace") or "")
        task_ts = to_utc(item.get("ts"))
        if not task_ts and task_id.isdigit():
            task_ts = to_utc(int(task_id))

        def base(line: int, ts: str) -> Row:
            row = self.base_row(artifact)
            row.source_line = line
            row.session_id = task_id
            row.project_path = project
            row.timestamp_utc = ts
            return row

        if item:
            row = base(0, task_ts)
            row.turn_type = "system"
            row.text = compact(
                " ".join(
                    p
                    for p in (
                        "task:",
                        str(item.get("task") or ""),
                        "mode=%s" % item["mode"] if item.get("mode") else "",
                        "status=%s" % item["status"] if item.get("status") else "",
                        "parent=%s" % item["parentTaskId"] if item.get("parentTaskId") else "",
                    )
                    if p
                ),
            )
            yield row

        with open(artifact.disk_path, "rb") as fh:
            raw = fh.read().decode("utf-8", errors="replace")
        errors: list = []
        items = iter_json_array(raw, errors)
        for n, msg in enumerate(items, 1):
            if not isinstance(msg, dict):
                continue
            ts = to_utc(msg.get("ts")) or task_ts

            def mk(turn: str, text) -> Row:
                row = base(n, ts)
                row.turn_type = turn
                row.text = compact(text)
                return row

            if msg.get("type") == "reasoning":
                if opts.include_thinking:
                    text = text_of(msg.get("summary")) or str(
                        msg.get("reasoning_content") or msg.get("text") or ""
                    )
                    if text:
                        yield mk("thinking", text)
                continue
            role = msg.get("role")
            content = msg.get("content")
            if msg.get("isSummary"):
                yield mk("system", "summary: " + text_of(content))
                continue
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            if not isinstance(content, list):
                continue
            # The text blocks of one message become one row, placed where the
            # first of them was so it keeps its order relative to tool blocks.
            texts: list[str] = []
            text_at = -1
            out: list[Row] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype in ("text", "image"):
                    t = "[image]" if btype == "image" else (block.get("text") or "")
                    if t.lstrip().startswith("<environment_details>"):
                        out.append(mk("system", t))
                    elif t:
                        if text_at < 0:
                            text_at = len(out)
                        texts.append(t)
                elif btype == "tool_use":
                    row = mk("tool_use", tool_summary(block.get("input")))
                    row.tool_name = str(block.get("name") or "")
                    row.tool_use_id = str(block.get("id") or "")
                    out.append(row)
                elif btype == "tool_result":
                    text = text_of(block.get("content"))
                    row = mk("tool_result", ("[error] " + text) if block.get("is_error") else text)
                    row.tool_use_id = str(block.get("tool_use_id") or "")
                    out.append(row)
                elif btype in ("thinking", "reasoning"):
                    t = block.get("thinking") or block.get("text") or ""
                    if opts.include_thinking and t:
                        out.append(mk("thinking", t))
                else:
                    out.append(mk("system", "%s: %s" % (btype or "block", compact_json(block))))
            if texts:
                out.insert(
                    text_at,
                    mk(
                        "user"
                        if role == "user"
                        else "assistant"
                        if role == "assistant"
                        else "system",
                        "\n".join(texts),
                    ),
                )
            yield from out
        yield from error_rows(self, artifact, errors, task_id, project)
