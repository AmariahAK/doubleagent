"""Amazon Q Developer CLI conversations, the open-source predecessor of the
Kiro CLI (catalog agent `kiro`).

Validated against the source of aws/amazon-q-developer-cli at 15cc8f3
(1.19.7, `crates/chat-cli`), with a synthetic fixture; see
`research/kiro.md`. No real install was used. Files, relative to
the home directory:

* `data.sqlite3` under `.local/share/amazon-q/`, `Library/Application
  Support/amazon-q/` or `AppData/Local/amazon-q/`, and the same three under
  `kiro-cli/` (the rebrand; those directories are from the catalog and not
  verified from source). Rollback journal, not WAL. Tables read:
  - `conversations(key, value)`: one row per working directory. `key` is the
    cwd, `value` is the serialised `ConversationState` below. Only the
    latest conversation per directory survives.
  - `history(command, shell, pid, session_id, cwd, start_time | time,
    end_time, duration, hostname, exit_code)`: legacy Fig shell history with
    no writer in the current source; old installs may hold rows. Each row
    becomes a `system` row prefixed `shell history:` since it records a
    shell command, not an agent turn. `session_id` is the shell session.
  - `auth_kv` and `state` hold tokens and are never read.
* Saved `/save` exports anywhere under the agent's directories: a `.json`
  file whose top-level object has `conversation_id` and `history`, the same
  `ConversationState` schema pretty-printed.

`ConversationState` fields used: `conversation_id`, `history[]`,
`next_message`, `latest_summary` (`[text, RequestMetadata]`),
`model_info.model_id`, legacy `model`. Each history entry is `{user,
assistant, request_metadata}`:

  - `user.content` is `{"Prompt": {prompt}}`, `{"ToolUseResults":
    {tool_use_results}}` or `{"CancelledToolUses": {prompt,
    tool_use_results}}`; each result is `{tool_use_id, content: [{"Text"} |
    {"Json"}], status}`. `user.timestamp` is RFC 3339 with the local offset
    or null; `user.env_context.env_state.current_working_directory`.
  - `assistant` is `{"Response": {message_id, content}}` or `{"ToolUse":
    {message_id, content, tool_uses: [{id, name, orig_name, args}]}}`.
  - `request_metadata`: `request_start_timestamp_ms`,
    `stream_end_timestamp_ms`, `model_id`, `message_meta_tags`.

Rows: `user` per prompt; `tool_result` per tool use result (text suffixed
with the status, and `cancelled` for CancelledToolUses), named by looking up
the id among earlier tool uses; `assistant` per response text; `tool_use`
per `tool_uses[]` entry with `name` as the tool name and the JSON `args` as
the text (prefixed `orig_name=` when the MCP original name differs);
`system` rows for a `Compact` meta tag, the `latest_summary` and a pending
`next_message`. There are no thinking blocks in this format.

Timestamps: user and tool_result rows use `user.timestamp`, which is null
on tool-result messages; they fall back to the same entry's
`request_start_timestamp_ms`. Assistant and tool_use rows use
`stream_end_timestamp_ms`, then `request_start_timestamp_ms`. Entries with
neither (old releases without `request_metadata`) inherit the previous
row's timestamp. `project_path` is the database row key, else the first
`current_working_directory`. No git branch is recorded.

Model rows (issue 96), `system`: `model: <id>` before the rows of the first
history entry and `model: <old> -> <new>` before the rows of each entry
whose model differs, timestamped like the entry's user row. The model is
the entry's `request_metadata.model_id`; an entry without one falls back to
the conversation's `model_info.model_id` (or the legacy `model`), and the
row then ends ` source=model_info` (or ` source=model`), because that field
is a conversation-level value serialised with the whole state, not a record
of the request.

Everything below was added from the same source on 2026-10-21
(issue 212); it is source-derived and not observed on any real install.

Permission rows, `system`. A cancelled tool use stays a `tool_result`
prefixed `cancelled` and is followed by a row with its `tool_use_id` and
`tool_name`, chosen by the CancelledToolUses `prompt`: `permission
decision: denied by=n` for the fixed text a bare `n` sends ("I deny this
tool request. Ask a follow up question clarifying the expected action"),
`permission decision: denied by=deny-rule tool=<name>` for "Tool use with
<name> was rejected because the arguments supplied were forbidden" (a
deny rule of the agent's `toolsSettings`), `permission decision: cancelled
by=interrupt` for "The user interrupted the tool execution.", `permission
decision: denied by=user-text` for any other prompt (what the user typed
instead of `y` or `t`) and `permission decision: cancelled` for none. The
deny-rule text in a `Prompt` message (no pending call to cancel) gives the
same deny-rule row after the user row, with `tool_name` and no id. An
approval (`y`, `t`, `--trust-all-tools`) is not persisted.

Standing grants: `cli-agents/<name>.json` under `.aws/amazonq/` (global)
or `.amazonq/` (a project; `project_path` is the project): camelCase
`allowedTools` (a list) and `toolsSettings` (`{<tool>: {<key>: value}}`,
e.g. `allowedCommands`, `deniedCommands`, `denyByDefault`,
`autoAllowReadonly`, `allowedPaths`, `deniedPaths`). One row per entry,
`permission setting: allowedTools=<entry> (from <file>, file mtime)` and
`permission setting: toolsSettings.<tool>.<key>=<value> (from <file>, file
mtime)`, at the file's modification time with no session.

Past use. `.aws/amazonq/.cli_bash_history`, the chat prompt's rustyline 15
history, is secondary: a first line `#V2` marks the multi-line format, in
which `\\n` is a line feed and `\\\\` a backslash; without it each line is
one entry as written. One `user` row per entry with no timestamp, session
or project. A line that is not UTF-8 is a bad line. Inside each blob,
`checkpoint_manager.checkpoints[]` (`tag`, `timestamp`, `description`,
`tool_name`, `history_snapshot`) and `tangent_state.main_history` are copies
of `history`: the entries the history no longer holds (equal on user
content, user timestamp and assistant message) are yielded after the
history's rows, behind one `system` row `checkpoint snapshot: tag=<tag>[
tool=<tool_name>] recovered=<n> entries[: <description>]` at the
checkpoint's time or `tangent mode: main conversation held aside,
recovered=<n> entries`, and every non-`system` row of them is marked
`recovered` "yes"; their model rows track their own sequence.
`.amazonq/.subagents/<agent>.json` (`agent`, `task`, `status`,
`launched_at` and `completed_at` in Unix seconds, `pid`, `exit_code`,
`output`, `summary`, `cwd`) is primary: `delegate task launched:
agent=<agent> pid=<pid>[ trust_all_tools=true]: <task>` at `launched_at`
(`trust_all_tools` for the default agent `q_cli_default`, which the
delegate tool runs with `--trust-all-tools`) and, once it ended, `delegate
task <status>: agent=<agent> exit_code=<code>` with `summary:` and
`output:` lines at `completed_at`; `project_path` is `cwd`.

Kiro CLI's `settings/permissions.yaml`, `sandbox-state/` and
`workspace-roots/<hash>/.trust-migration.json` have no recorded shape and
are not read.

A blob or export that fails to parse as a whole (an export truncated
mid-write) is salvaged entry by entry: the history entries before the cut
are still yielded, followed by one `system` row.

Not parsed: Kiro CLI's `.kiro/sessions/` files. That closed-source format is
unverified (the research suggests the camelCase `crates/agent` schema, but
that is inference), so `wants()` ignores it until the format is confirmed
from a shipped binary or a real install. The Kiro IDE stores are not parsed
either.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator

from ..inputs import Artifact
from ..model import Row, compact
from ..sqlite_util import is_sqlite, open_copy, table_names
from ..timeutil import to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    line_text,
    setting_value,
    track_change,
)

DB_RX = re.compile(
    r"^(?:\.local/share|Library/Application Support|AppData/Local)/(?:amazon-q|kiro-cli)/data\.sqlite3$"
)
SESSIONS_RX = re.compile(r"^\.kiro/sessions/")
# The chat prompt's rustyline history (Q `paths.rs` `CLI_BASH_HISTORY`).
HISTORY_RX = re.compile(r"^\.aws/amazonq/\.cli_bash_history$")
# Agent configurations, global and per project (Q `paths.rs` `AGENTS_DIR`).
AGENT_RX = re.compile(r"^(?:\.aws/amazonq|\.amazonq)/cli-agents/[^/]+\.json$")
# The delegate tool's per-agent task records (Q `paths.rs` `SUBAGENTS_DIR`).
SUBAGENT_RX = re.compile(r"^\.amazonq/\.subagents/[^/]+\.json$")
# The header rustyline writes first in a multi-line-aware history file.
HISTORY_V2 = "#V2"
# The fixed prompts of a CancelledToolUses message (Q `cli/chat/mod.rs`).
DENY_TEXT = "I deny this tool request. Ask a follow up question clarifying the expected action"
INTERRUPT_TEXT = "The user interrupted the tool execution."
DENY_RULE_RX = re.compile(
    r"^Tool use with (.+) was rejected because the arguments supplied were forbidden$", re.S
)
# The agent the delegate tool runs with --trust-all-tools (Q `cli/agent/mod.rs`).
DEFAULT_AGENT_NAME = "q_cli_default"
SNIFF_BYTES = 4096

_CONV_ID_RX = re.compile(r'"conversation_id"\s*:\s*"((?:[^"\\]|\\.)*)"')
_HISTORY_RX = re.compile(r'"history"\s*:\s*\[')


def _sniff_export(path) -> bool:
    try:
        with open(path, "rb") as fh:
            head = fh.read(SNIFF_BYTES)
    except OSError:
        return False
    return head.lstrip()[:1] == b"{" and b'"conversation_id"' in head


def salvage(text: str) -> tuple[dict | None, str]:
    """Parse a ConversationState. On failure, recover `conversation_id` and
    every complete `history` entry before the damage; the second value is the
    error message, empty when the whole document parsed."""
    try:
        state = json.loads(text)
        if isinstance(state, dict):
            return state, ""
        return None, "not a JSON object"
    except ValueError as e:
        err = str(e)
    m = _HISTORY_RX.search(text)
    if not m:
        return None, err
    state = {"history": []}
    cid = _CONV_ID_RX.search(text, 0, m.start())
    if cid:
        try:
            state["conversation_id"] = json.loads('"%s"' % cid.group(1))
        except ValueError:
            pass
    dec = json.JSONDecoder()
    i = m.end()
    n = len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n,":
            i += 1
        if i >= n or text[i] == "]":
            break
        try:
            entry, i = dec.raw_decode(text, i)
        except ValueError:
            break
        if isinstance(entry, dict):
            state["history"].append(entry)
    return state, err


def _variant(value) -> tuple[str, dict]:
    """Unpack a serde externally tagged enum: {"Tag": {...}}."""
    if isinstance(value, dict) and len(value) == 1:
        tag, body = next(iter(value.items()))
        return str(tag), body if isinstance(body, dict) else {}
    return "", {}


def result_text(result: dict) -> str:
    parts: list[str] = []
    for block in result.get("content") or []:
        if not isinstance(block, dict):
            parts.append(str(block))
        elif isinstance(block.get("Text"), str):
            parts.append(block["Text"])
        elif "Json" in block:
            parts.append(compact_json(block["Json"]))
        else:
            parts.append(compact_json(block))
    text = "\n".join(parts)
    status = result.get("status")
    if status:
        text = "%s [%s]" % (text, status) if text else "[%s]" % status
    return text


def unescape_history(line: str) -> str:
    """One entry of a rustyline `#V2` history file: `\\n` becomes a line
    feed and `\\\\` a backslash. A line with any other escape, or a trailing
    backslash, is kept exactly as written, as rustyline 15's `load_from`
    keeps it."""
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        nxt = line[i + 1] if i + 1 < n else ""
        if nxt == "n":
            out.append("\n")
        elif nxt == "\\":
            out.append("\\")
        else:
            return line
        i += 2
    return "".join(out)


def decision_text(prompt) -> str:
    """The `permission decision:` row text for a CancelledToolUses message
    whose `prompt` is `prompt`: a bare `n` answer (the fixed denial text), a
    deny rule of the agent's `toolsSettings`, an interrupt, or the user's own
    words typed at the approval prompt."""
    if not isinstance(prompt, str) or not prompt:
        return "permission decision: cancelled"
    if prompt == DENY_TEXT:
        return "permission decision: denied by=n"
    if prompt == INTERRUPT_TEXT:
        return "permission decision: cancelled by=interrupt"
    m = DENY_RULE_RX.match(prompt)
    if m:
        return "permission decision: denied by=deny-rule tool=%s" % m.group(1)
    return "permission decision: denied by=user-text"


def _entry_key(entry: dict) -> str:
    """What identifies a history entry across the copies one blob holds:
    the user content and time and the assistant message. A snapshot entry is
    a clone of the history entry, so the two are equal on these."""
    user = entry.get("user")
    user = user if isinstance(user, dict) else {}
    return compact_json([user.get("content"), user.get("timestamp"), entry.get("assistant")])


class KiroParser(Parser):
    agent = "kiro"
    name = "kiro"
    has_secondary = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        if DB_RX.match(rel) or HISTORY_RX.match(rel):
            return True
        if AGENT_RX.match(rel) or SUBAGENT_RX.match(rel):
            return True
        if SESSIONS_RX.match(rel) or not rel.endswith(".json"):
            return False
        return _sniff_export(artifact.disk_path)

    def secondary(self, artifact: Artifact) -> bool:
        return bool(HISTORY_RX.match(artifact.rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        rel = artifact.rel
        if DB_RX.match(rel):
            yield from self._parse_db(artifact, opts)
        elif HISTORY_RX.match(rel):
            yield from self._parse_history(artifact)
        elif AGENT_RX.match(rel):
            yield from self._parse_agent_config(artifact)
        elif SUBAGENT_RX.match(rel):
            yield from self._parse_delegate(artifact)
        else:
            yield from self._parse_export(artifact, opts)

    # -- .cli_bash_history ---------------------------------------------------------
    def _parse_history(self, artifact: Artifact) -> Iterator[Row]:
        """One `user` row per entry, with no timestamp, session or project,
        since the file records none."""
        errors: list = []
        v2 = False
        with open(artifact.disk_path, "rb") as fh:
            for n, raw in enumerate(fh, 1):
                try:
                    line = raw.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append((n, "unparseable line (not valid UTF-8)", line_text(raw)))
                    continue
                line = line_text(raw)
                if n == 1 and line == HISTORY_V2:
                    v2 = True
                    continue
                if not line:
                    continue
                row = self.base_row(artifact)
                row.source_line = n
                row.turn_type = "user"
                row.text = compact(unescape_history(line) if v2 else line)
                yield row
        yield from error_rows(self, artifact, errors)

    # -- cli-agents/<name>.json ---------------------------------------------------
    def _json_doc(self, artifact: Artifact, what: str) -> tuple[dict | None, Row | None]:
        """The file as a JSON object, or a `system` row saying it is not one."""
        try:
            doc = json.loads(artifact.disk_path.read_bytes().decode("utf-8", errors="replace"))
        except (OSError, ValueError):
            doc = None
        if isinstance(doc, dict):
            return doc, None
        row = self.base_row(artifact)
        row.source_line = 1
        row.turn_type = "system"
        row.timestamp_utc = file_mtime(artifact)
        row.text = "parser: %s is not a JSON object" % what
        return None, row

    def _parse_agent_config(self, artifact: Artifact) -> Iterator[Row]:
        """One `permission setting:` row per `allowedTools` entry and per key
        of each `toolsSettings` tool, at the file's modification time."""
        doc, bad = self._json_doc(artifact, "agent configuration")
        if doc is None:
            if bad is not None:
                yield bad
            return
        ts = file_mtime(artifact)
        project = artifact.home.original if artifact.home.project else ""

        def setting(key: str, value) -> Row:
            row = self.base_row(artifact)
            row.source_line = 1
            row.turn_type = "system"
            row.timestamp_utc = ts
            row.project_path = project
            row.text = compact(
                "permission setting: %s=%s (from %s, file mtime)"
                % (key, setting_value(value), artifact.rel)
            )
            return row

        allowed = doc.get("allowedTools")
        if isinstance(allowed, list):
            for entry in allowed:
                yield setting("allowedTools", entry)
        tools = doc.get("toolsSettings")
        if isinstance(tools, dict):
            for tool, conf in tools.items():
                if isinstance(conf, dict):
                    for key, value in conf.items():
                        yield setting("toolsSettings.%s.%s" % (tool, key), value)
                else:
                    yield setting("toolsSettings.%s" % tool, conf)

    # -- .amazonq/.subagents/<agent>.json -----------------------------------------
    def _parse_delegate(self, artifact: Artifact) -> Iterator[Row]:
        """A `system` row at `launched_at` and, once the task ended, one at
        `completed_at` with its status, exit code, summary and output."""
        doc, bad = self._json_doc(artifact, "delegate record")
        if doc is None:
            if bad is not None:
                yield bad
            return
        cwd = str(doc.get("cwd") or "")
        if not cwd or cwd == "Unknown":
            cwd = artifact.home.original if artifact.home.project else ""
        agent = str(doc.get("agent") or "")

        def when(value) -> str:
            ok = isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
            return to_utc(value) if ok else ""

        def event(ts: str, text: str) -> Row:
            row = self.base_row(artifact)
            row.source_line = 1
            row.turn_type = "system"
            row.timestamp_utc = ts
            row.project_path = cwd
            row.text = compact(text)
            return row

        trust = " trust_all_tools=true" if agent == DEFAULT_AGENT_NAME else ""
        yield event(
            when(doc.get("launched_at")),
            "delegate task launched: agent=%s pid=%s%s: %s"
            % (agent, doc.get("pid", ""), trust, doc.get("task") or ""),
        )
        status = str(doc.get("status") or "")
        completed = doc.get("completed_at")
        if completed is None and status in ("", "running"):
            return
        exit_code = doc.get("exit_code")
        text = "delegate task %s: agent=%s exit_code=%s" % (
            status or "ended",
            agent,
            "" if exit_code is None else exit_code,
        )
        if doc.get("summary"):
            text += "\nsummary: %s" % doc["summary"]
        if doc.get("output"):
            text += "\noutput: %s" % doc["output"]
        yield event(when(completed), text)

    # -- data.sqlite3 -------------------------------------------------------------
    def _parse_db(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        if not is_sqlite(artifact.disk_path):
            return
        with open_copy(artifact.disk_path) as con:
            tables = table_names(con)
            if "conversations" in tables:
                for n, r in enumerate(
                    con.execute("select key, value from conversations order by rowid"), 1
                ):
                    value = r["value"]
                    if isinstance(value, bytes):
                        value = value.decode("utf-8", errors="replace")
                    yield from self._conversation(
                        artifact, opts, str(value or ""), str(r["key"] or ""), n
                    )
            if "history" in tables:
                yield from self._shell_history(artifact, opts, con)

    def _shell_history(self, artifact: Artifact, opts: Options, con) -> Iterator[Row]:
        for n, r in enumerate(con.execute("select * from history order by rowid"), 1):
            r = dict(r)
            row = self.base_row(artifact)
            row.source_line = n
            start = r.get("start_time") if "start_time" in r else r.get("time")
            row.timestamp_utc = to_utc(start)
            row.session_id = str(r.get("session_id") or "")
            row.project_path = str(r.get("cwd") or "")
            row.turn_type = "system"
            extras = [
                "%s=%s" % (k, r[k])
                for k in ("exit_code", "shell", "hostname", "duration")
                if r.get(k) not in (None, "")
            ]
            text = "shell history: %s" % (r.get("command") or "")
            if extras:
                text += " (%s)" % " ".join(extras)
            row.text = compact(text)
            yield row

    # -- /save exports ------------------------------------------------------------
    def _parse_export(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        with open(artifact.disk_path, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        yield from self._conversation(artifact, opts, text, "", 0)

    # -- ConversationState --------------------------------------------------------
    def _conversation(
        self, artifact: Artifact, opts: Options, text: str, key: str, line: int
    ) -> Iterator[Row]:
        state, err = salvage(text)
        if state is None or not isinstance(state.get("history"), list):
            if err:
                row = self.base_row(artifact)
                row.source_line = line
                row.project_path = key
                row.turn_type = "system"
                row.text = "parser: unparseable conversation: %s" % err
                yield row
            return
        session_id = str(state.get("conversation_id") or "")
        info = state.get("model_info")
        conv_model = ""
        conv_source = ""
        if isinstance(info, dict) and info.get("model_id"):
            conv_model, conv_source = str(info["model_id"]), "model_info"
        elif isinstance(state.get("model"), str):
            conv_model, conv_source = state["model"], "model"
        project = key or self._first_cwd(state)
        names: dict[str, str] = {}
        seen_model: dict[str, str] = {}
        last_ts = [""]

        def base(ts: str, model: str = "") -> Row:
            row = self.base_row(artifact)
            row.source_line = line
            if ts:
                last_ts[0] = ts
            row.timestamp_utc = ts or last_ts[0]
            row.session_id = session_id
            row.project_path = project
            row.model = model
            return row

        def fill(row: Row, s: str) -> Row:
            row.text = compact(s)
            return row

        def entry_rows(entry: dict, seen_model: dict[str, str]) -> Iterator[Row]:
            meta = entry.get("request_metadata")
            meta = meta if isinstance(meta, dict) else {}
            model = str(meta.get("model_id") or conv_model)
            start_ts = to_utc(meta.get("request_start_timestamp_ms"))
            end_ts = to_utc(meta.get("stream_end_timestamp_ms")) or start_ts
            user = entry.get("user")
            user_ts = to_utc(user.get("timestamp")) if isinstance(user, dict) else ""
            text = track_change("model", seen_model, session_id, model)
            if text:
                if not meta.get("model_id"):
                    text += " source=%s" % conv_source
                row = base(user_ts or start_ts or end_ts, model)
                row.turn_type = "system"
                yield fill(row, text)
            if isinstance(user, dict):
                user_ts = user_ts or start_ts
                yield from self._user(user.get("content"), user_ts, model, names, base, fill)
            assistant = entry.get("assistant")
            tag, body = _variant(assistant)
            if tag in ("Response", "ToolUse"):
                content = body.get("content")
                if content:
                    yield self._assistant(base(end_ts, model), content, fill)
                for use in body.get("tool_uses") or []:
                    if not isinstance(use, dict):
                        continue
                    tid = str(use.get("id") or "")
                    tname = str(use.get("name") or use.get("orig_name") or "")
                    names[tid] = tname
                    row = base(end_ts, model)
                    row.turn_type = "tool_use"
                    row.tool_name = tname
                    row.tool_use_id = tid
                    args = use.get("args")
                    s = args if isinstance(args, str) else compact_json(args)
                    orig = use.get("orig_name")
                    if orig and orig != tname:
                        s = "orig_name=%s %s" % (orig, s)
                    yield fill(row, s)
            tags = meta.get("message_meta_tags") or []
            if isinstance(tags, list) and "Compact" in tags:
                row = base(end_ts, model)
                row.turn_type = "system"
                yield fill(row, "compact: conversation history summarised")

        seen_entries: set[str] = set()
        for entry in state["history"]:
            if isinstance(entry, dict):
                seen_entries.add(_entry_key(entry))
                yield from entry_rows(entry, seen_model)

        # Copies of the history inside the same blob: each checkpoint's
        # history_snapshot (kept through /checkpoint restore) and the main
        # conversation held aside in tangent mode. Only entries the history
        # no longer holds are yielded, marked recovered.
        seen_copy_model: dict[str, str] = {}
        for head, tail, ts, entries in self._history_copies(state):
            fresh = []
            for entry in entries:
                if isinstance(entry, dict) and _entry_key(entry) not in seen_entries:
                    seen_entries.add(_entry_key(entry))
                    fresh.append(entry)
            if not fresh:
                continue
            row = base(ts)
            row.turn_type = "system"
            yield fill(row, "%s recovered=%d entries%s" % (head, len(fresh), tail))
            for entry in fresh:
                for row in entry_rows(entry, seen_copy_model):
                    if row.turn_type != "system":
                        row.recovered = "yes"
                    yield row

        summary = state.get("latest_summary")
        if isinstance(summary, list) and summary:
            smeta = summary[1] if len(summary) > 1 and isinstance(summary[1], dict) else {}
            ts = to_utc(smeta.get("stream_end_timestamp_ms")) or to_utc(
                smeta.get("request_start_timestamp_ms")
            )
            row = base(ts, str(smeta.get("model_id") or ""))
            row.turn_type = "system"
            yield fill(
                row,
                "summary: %s"
                % (summary[0] if isinstance(summary[0], str) else compact_json(summary[0])),
            )

        pending = state.get("next_message")
        if isinstance(pending, dict):
            tag, body = _variant(pending.get("content"))
            prompt = body.get("prompt") if tag in ("Prompt", "CancelledToolUses") else None
            row = base(to_utc(pending.get("timestamp")))
            row.turn_type = "system"
            yield fill(
                row,
                "pending message (not sent): %s" % (prompt or compact_json(pending.get("content"))),
            )

        if err:
            row = self.base_row(artifact)
            row.source_line = line
            row.session_id = session_id
            row.project_path = project
            row.turn_type = "system"
            row.text = "parser: truncated conversation, %d history entries recovered: %s" % (
                len(state["history"]),
                err,
            )
            yield row

    @staticmethod
    def _assistant(row: Row, content, fill) -> Row:
        row.turn_type = "assistant"
        return fill(row, content if isinstance(content, str) else compact_json(content))

    @staticmethod
    def _history_copies(state: dict) -> Iterator[tuple[str, str, str, list]]:
        """(row text before and after the entry count, timestamp, entries)
        for each checkpoint's `history_snapshot`, in checkpoint order, then
        for `tangent_state.main_history`. The tangent row has no time of its
        own (`tangent_start_time` is not read)."""
        manager = state.get("checkpoint_manager")
        checkpoints = manager.get("checkpoints") if isinstance(manager, dict) else None
        for cp in checkpoints if isinstance(checkpoints, list) else []:
            if not isinstance(cp, dict) or not isinstance(cp.get("history_snapshot"), list):
                continue
            head = "checkpoint snapshot: tag=%s" % (cp.get("tag") or "")
            if cp.get("tool_name"):
                head += " tool=%s" % cp["tool_name"]
            tail = ": %s" % cp["description"] if cp.get("description") else ""
            yield head, tail, to_utc(cp.get("timestamp")), cp["history_snapshot"]
        tangent = state.get("tangent_state")
        if isinstance(tangent, dict) and isinstance(tangent.get("main_history"), list):
            head = "tangent mode: main conversation held aside,"
            yield head, "", "", tangent["main_history"]

    @staticmethod
    def _user(content, ts: str, model: str, names: dict[str, str], base, fill) -> Iterator[Row]:
        tag, body = _variant(content)
        prompt = body.get("prompt")
        if tag in ("Prompt", "CancelledToolUses") and prompt:
            row = base(ts, model)
            row.turn_type = "user"
            yield fill(row, prompt)
        if tag == "Prompt" and isinstance(prompt, str):
            m = DENY_RULE_RX.match(prompt)
            if m:
                # the rejection reached the model as a plain prompt: it names
                # the tool but not the call
                row = base(ts, model)
                row.turn_type = "system"
                row.tool_name = m.group(1)
                yield fill(row, decision_text(prompt))
        if tag in ("ToolUseResults", "CancelledToolUses"):
            for result in body.get("tool_use_results") or []:
                if not isinstance(result, dict):
                    continue
                row = base(ts, model)
                row.turn_type = "tool_result"
                row.tool_use_id = str(result.get("tool_use_id") or "")
                row.tool_name = names.get(row.tool_use_id, "")
                s = result_text(result)
                if tag == "CancelledToolUses":
                    s = "cancelled %s" % s if s else "cancelled"
                yield fill(row, s)
                if tag == "CancelledToolUses":
                    dec = base(ts, model)
                    dec.turn_type = "system"
                    dec.tool_use_id = row.tool_use_id
                    dec.tool_name = row.tool_name
                    yield fill(dec, decision_text(prompt))

    @staticmethod
    def _first_cwd(state: dict) -> str:
        for entry in state.get("history") or []:
            try:
                cwd = entry["user"]["env_context"]["env_state"]["current_working_directory"]
            except (KeyError, TypeError):
                continue
            if cwd:
                return str(cwd)
        return ""
