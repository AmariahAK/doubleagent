"""Qwen Code transcripts.

Validated against source, QwenLM/qwen-code at 2c591ecc (0.24.7, October
2026) and, for the injected user records, 5dcf7c7c (0.25.3), with a
synthetic fixture; see `research/qwen-code.md`. Qwen Code
forked Gemini CLI but its session format is a Claude-Code-style record
stream, not Gemini's. Files:

* `~/.qwen/projects/<sanitized cwd>/chats/<sessionId>.jsonl`, and archived
  sessions under `chats/archive/`. One `ChatRecord` per line, each with
  `uuid`, `parentUuid`, `sessionId`, `timestamp` (ISO 8601 Z), `type`
  (user, assistant, tool_result, system), `subtype`, `cwd`, `gitBranch`
  and `version`. `message` is a Gemini `Content` `{role, parts}`:
  - user: `parts[].text`; `systemPayload.displayText` is used when the
    parts carry no text. A `user` row only when `provenance` is absent or
    `real_user`. A record the user did not type is a `system` row
    `<subtype> (provenance=<provenance> agent=<agentName> agentId=<agentId>):
    <text>`, absent parts left out: `notification` and `cron` records
    (`provenance: system`; 0.24.7 already writes them), `agent_message`
    and an agent's `agent_mention` (`provenance: external_agent`, with
    top-level `agentId` and `agentName` on `agent_message` and
    `systemPayload.author {agentId, name}` on both; 0.25.x, issue 172),
    `goal_runtime` (`provenance: goal_runtime`). A user's own
    `agent_mention` has `provenance: real_user` and stays a `user` row.
  - assistant: top-level `model`; `parts[]` hold `text`, `thought: true`
    text (a `thinking` row, opt-in) and `functionCall {id, name, args}`.
  - tool_result: `parts[].functionResponse {id, name, response}` and
    `toolCallResult {callId, status, resultDisplay, errorType}`.
  - system: `subtype` plus `systemPayload`; slash_command (`rawCommand`),
    session_model (`modelId`, `authType`; see below), custom_title
    (`customTitle`), turn_result (`state`, `resultText`), rewind
    (`truncatedCount`),
    chat_compression (`info`) are summarised, other subtypes (including
    the managed-engine `managed_session_header_v1` records) are emitted
    with their subtype name and the payload as JSON.
  The sidecars `<sessionId>.runtime.json`, `.worktree.json` and
  `.ledger.jsonl` in the same directory are not transcripts and are skipped.
* `~/.qwen/tmp/<sha256(cwd)>/logs.json`: a JSON array of the Gemini-legacy
  `LogEntry {sessionId, messageId, timestamp, type, message}`, `type` user
  or model_switch (whose `message` is a JSON `ModelSwitchEvent {fromModel,
  toModel, reason}`). The directory is a hash, so these rows have no
  project path. A truncated array still yields the entries before the cut.
  A secondary source: the timeline drops an entry whose event a chat file
  also records, matched by `sessionId` (`dedup.py`).

* `~/.qwen/trustedFolders.json`: a JSON object, read with comments
  stripped, whose keys are folder paths and whose values are a
  `TrustLevel` string (`TRUST_FOLDER`, `TRUST_PARENT`, `DO_NOT_TRUST`;
  `packages/cli/src/config/trustedFolders.ts`). One `system` row per key,
  `permission setting: trustedFolders.<path>=<value> (from <file>, file mtime)`,
  read by the Gemini CLI parser's `trusted_folder_rows`, with
  `project_path` the folder, `timestamp_utc` the file's modification time
  and no session id.

* `~/.qwen/channels/sessions.json`, written by `qwen channel start` (which
  drives sessions from a messaging platform such as Telegram, WeChat,
  DingTalk, Feishu, GitHub or email, so the conversation also sits on that
  platform's servers), and its daemon form
  `~/.qwen/channels/daemon/<workspace hash>/routes.json`: one JSON object
  keyed by routing key, each value `{sessionId, target: {channelName,
  messageRoute?, senderId, chatId, threadId?, isGroup?}, cwd, turns?,
  startedAt?}` with `startedAt` epoch milliseconds
  (`packages/channels/base/src/SessionRouter.ts:25-36`, `1559-1593`). One
  `system` row per entry, `source_line` its position in the object,
  `session_id` its `sessionId` and `project_path` its `cwd`:
  `session relayed: channel <channelName> chat <chatId> sender <senderId>
  thread <threadId> (from channels/sessions.json, startedAt)`, `-` for a
  key absent or empty, at `startedAt`, or at the file's modification time
  with the text ending `file mtime)` when the entry has none; the daemon
  form names `channels/daemon/<hash>/routes.json`. The relay is a copy on
  the platform, not a sync to a Qwen account, so `records_sync` stays
  False and `records_relay` is set: a session without a route is
  `relayed` `no`. `sessions.json` is deleted on a clean shutdown, so its rows show
  only a running or crashed service. A file that is not a JSON object is
  one `parser:` row, and so is an entry that is not one. Fixture only: no
  real install has shown either file.

* `~/.qwen/settings.json` and a project's `.qwen/settings.json` (a project
  catalog file; `project_path` the project), read as JSONC (comments and a
  byte-order mark allowed, as `packages/cli/src/config/settings.ts` reads
  it): one `system` row per entry of `permissions.allow`,
  `permissions.ask` and `permissions.deny` and one for
  `tools.approvalMode`, `permission setting: <key>=<value> (from <file>,
  file mtime)`, at the file's modification time with no session id. No
  other key is read (the file holds `modelProviders[].apiKey` and channel
  tokens). A file that is not a JSON object is one `parser:` row. The
  collector flags the home copy `secret: true`, so a `--no-secrets`
  collection lacks it. Source-derived (5dcf7c7c), issue 187.

* `~/.qwen/usage_record.jsonl`: one `UsageSummaryRecord` per line
  (`sessionId`, `startTime` epoch ms, `project`, `durationMs`, `models`
  keyed by model id, `tools.byName.<tool>.count`), written at session exit,
  at `/clear` and before a session's transcript is deleted. One `system`
  row per line, `session usage: project <project> duration <durationMs>ms
  models <id>,... tools <tool>=<count>,... (from usage_record.jsonl,
  startTime)`, `-` for an absent part, at `startTime`, with the record's
  `sessionId` and `project`. A secondary source: what is left of a deleted
  session. Source-derived (5dcf7c7c), issue 187.

Model and permission rows. A `session_model` record is the row
`model: <modelId> auth=<authType>` (`model: <old> -> <new> auth=<authType>`
when it names a model other than the one in force); an assistant
record's `model` yields `model: <id>` before its rows when no earlier
record of the session named a model, and `model: <old> -> <new>` when it
differs from the one in force, tracked per `sessionId`. A `logs.json`
`model_switch` entry is `model: <fromModel> -> <toModel> reason=<reason>`.
A `tool_result` whose `toolCallResult.status` is `cancelled` or
`awaiting_approval` keeps the `[<status>]` prefix and is followed by a
`system` row `permission decision: <status>` with its `tool_name` and
`tool_use_id`.

Source-derived from 5dcf7c7c (issue 187), not observed on any real
install: a record's `executionContext {modelId, authType?, approvalMode}`
(user prompts and `mid_turn_user_message` records) feeds the same per-session
model tracking, as `model: <modelId>[ auth=<authType>]` or `model: <old> ->
<new>[ auth=<authType>]` before the record's rows, and a per-session approval
mode tracking, `permission mode: <approvalMode>` the first time and
`permission mode: <old> -> <new>` on a change. A `session_approval_mode`
record (`systemPayload {mode, prePlanMode?, planExecutionMode?}`) is the row
`permission mode: <mode>` or `permission mode: <old> -> <mode>`, followed by
` prePlanMode=<p>` and ` planExecutionMode=<e>` when recorded. A
`ui_telemetry` record whose `systemPayload.uiEvent` has `event.name`
`qwen-code.tool_call` and a `decision` (`accept`, `reject`, `modify`,
`auto_accept`) keeps its `ui_telemetry: <JSON>` row and is followed by
`permission decision: <decision> (tool_call ui_telemetry)` with `tool_name`
the event's `function_name` and `tool_use_id` its `call_id`.

Not parsed: `checkpoint-<tag>.json` (a raw `Content[]` without timestamps)
and `shell_history`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator

from ..inputs import Artifact
from ..model import Row, compact
from ..timeutil import to_utc
from .base import (
    Options,
    Parser,
    compact_json,
    error_rows,
    file_mtime,
    iter_jsonl,
    setting_value,
    tail_text,
    track_change,
)
from .gemini_cli import parse_jsonc, trusted_folder_rows

SESSION_RX = re.compile(r"^\.qwen/projects/[^/]+/chats/(?:archive/)?[^/]+\.jsonl$")
LOGS_RX = re.compile(r"^\.qwen/tmp/[^/]+/logs\.json$")
TRUSTED_RX = re.compile(r"^\.qwen/trustedFolders\.json$")
CHANNELS_RX = re.compile(r"^\.qwen/(channels/(?:sessions\.json|daemon/[^/]+/routes\.json))$")
# `~/.qwen/settings.json`, or a project's `.qwen/settings.json` (a project
# catalog file), for the standing permission rules (#187).
SETTINGS_RX = re.compile(r"^\.qwen/settings\.json$")
USAGE_RX = re.compile(r"^\.qwen/usage_record\.jsonl$")
PERMISSION_LISTS = ("allow", "ask", "deny")
# `ToolCallEvent` as `logToolCall` records it in a `ui_telemetry` record.
TOOL_CALL_EVENT = "qwen-code.tool_call"
DECISION_STATUSES = ("cancelled", "awaiting_approval")
SIDECAR_SUFFIX = ".ledger.jsonl"
# `type: user` subtypes that never hold a prompt the user typed (#172).
INJECTED_SUBTYPES = ("notification", "cron", "agent_message")

ARG_KEYS = (
    "command",
    "absolute_path",
    "file_path",
    "path",
    "pattern",
    "url",
    "query",
    "prompt",
    "description",
)


def args_summary(args) -> str:
    """The most identifying argument of a function call, else the arguments
    as JSON."""
    if isinstance(args, dict):
        for k in ARG_KEYS:
            v = args.get(k)
            if v not in (None, ""):
                return v if isinstance(v, str) else compact_json(v)
        return compact_json(args)
    if args in (None, ""):
        return ""
    return args if isinstance(args, str) else compact_json(args)


def _parts(rec: dict) -> list:
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return []
    parts = msg.get("parts")
    return [p for p in parts if isinstance(p, dict)] if isinstance(parts, list) else []


def _response_text(response) -> str:
    if isinstance(response, dict):
        for k in ("output", "error", "llmContent"):
            v = response.get(k)
            if isinstance(v, str) and v:
                return v
        return compact_json(response)
    if response in (None, ""):
        return ""
    return response if isinstance(response, str) else compact_json(response)


def system_text(subtype: str, payload) -> str:
    p = payload if isinstance(payload, dict) else {}
    if subtype == "slash_command":
        detail = "%s %s" % (p.get("phase") or "", p.get("rawCommand") or "")
    elif subtype == "session_model":
        detail = "%s auth=%s" % (p.get("modelId") or "", p.get("authType") or "")
    elif subtype == "custom_title":
        detail = p.get("customTitle") or ""
    elif subtype == "turn_result":
        detail = "%s %s" % (p.get("state") or "", p.get("resultText") or "")
    elif subtype == "rewind":
        detail = "truncated %s record(s)" % p.get("truncatedCount")
    elif subtype == "chat_compression":
        detail = compact_json(p.get("info")) if p.get("info") is not None else ""
    else:
        detail = compact_json(payload) if payload else ""
    detail = str(detail).strip()
    return "%s: %s" % (subtype, detail) if detail else subtype


def injected_origin(rec: dict) -> str:
    """For a `type: user` record that the user did not type, its row prefix
    `<subtype> (provenance=<provenance> agent=<agentName> agentId=<agentId>)`,
    with the parts not recorded left out; "" for a prompt the user typed.
    A record is the user's when its `provenance` is absent or `real_user`,
    unless its subtype is one only the system or another agent writes."""
    provenance = str(rec.get("provenance") or "")
    subtype = str(rec.get("subtype") or "")
    if provenance in ("", "real_user") and subtype not in INJECTED_SUBTYPES:
        return ""
    payload = rec.get("systemPayload")
    author = payload.get("author") if isinstance(payload, dict) else None
    author = author if isinstance(author, dict) else {}
    name = rec.get("agentName") or author.get("name")
    agent_id = rec.get("agentId") or author.get("agentId")
    keys = [
        "%s=%s" % (k, v)
        for k, v in (("provenance", provenance), ("agent", name), ("agentId", agent_id))
        if v not in (None, "")
    ]
    label = subtype or "user"
    return "%s (%s)" % (label, " ".join(keys)) if keys else label


class QwenCodeParser(Parser):
    agent = "qwen-code"
    name = "qwen-code"
    has_secondary = True
    records_relay = True

    def wants(self, artifact: Artifact) -> bool:
        rel = artifact.rel
        for rx in (LOGS_RX, TRUSTED_RX, CHANNELS_RX, SETTINGS_RX, USAGE_RX):
            if rx.match(rel):
                return True
        return bool(SESSION_RX.match(rel)) and not rel.endswith(SIDECAR_SUFFIX)

    def secondary(self, artifact: Artifact) -> bool:
        return bool(LOGS_RX.match(artifact.rel) or USAGE_RX.match(artifact.rel))

    def parse(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        channels = CHANNELS_RX.match(artifact.rel)
        if TRUSTED_RX.match(artifact.rel):
            yield from trusted_folder_rows(self, artifact)
        elif SETTINGS_RX.match(artifact.rel):
            yield from self._parse_settings(artifact)
        elif USAGE_RX.match(artifact.rel):
            yield from self._parse_usage(artifact)
        elif channels:
            yield from self._parse_channel_routes(artifact, channels.group(1))
        elif LOGS_RX.match(artifact.rel):
            yield from self._parse_logs(artifact, opts)
        else:
            yield from self._parse_session(artifact, opts)

    def _parse_channel_routes(self, artifact: Artifact, name: str) -> Iterator[Row]:
        """One `session relayed:` row per entry of a channel routes file."""
        try:
            doc = json.loads(artifact.disk_path.read_bytes().decode("utf-8", errors="replace"))
        except (OSError, ValueError):
            doc = None
        if not isinstance(doc, dict):
            yield from error_rows(self, artifact, [(0, "%s is not a JSON object" % name, "")])
            return
        mtime = ""
        errors: list = []
        for n, (key, entry) in enumerate(doc.items(), 1):
            if not isinstance(entry, dict):
                errors.append((n, "entry %s is not a JSON object" % key, ""))
                continue
            target = entry.get("target")
            target = target if isinstance(target, dict) else {}

            def value(k: str, target: dict = target) -> str:
                v = target.get(k)
                return str(v) if v not in (None, "") else "-"

            row = self.base_row(artifact)
            row.source_line = n
            row.turn_type = "system"
            row.session_id = str(entry.get("sessionId") or "")
            row.project_path = str(entry.get("cwd") or "")
            row.timestamp_utc = to_utc(entry.get("startedAt"))
            when = "startedAt"
            if not row.timestamp_utc:
                mtime = mtime or file_mtime(artifact)
                row.timestamp_utc, when = mtime, "file mtime"
            row.text = "session relayed: channel %s chat %s sender %s thread %s (from %s, %s)" % (
                value("channelName"),
                value("chatId"),
                value("senderId"),
                value("threadId"),
                name,
                when,
            )
            yield row
        yield from error_rows(self, artifact, errors)

    def _settings_row(self, artifact: Artifact, ts: str, project: str, text: str) -> Row:
        row = self.base_row(artifact)
        row.source_line = 1
        row.turn_type = "system"
        row.timestamp_utc = ts
        row.project_path = project
        row.text = compact(text)
        return row

    def _parse_settings(self, artifact: Artifact) -> Iterator[Row]:
        """One `permission setting:` row per `permissions.allow`, `ask` and
        `deny` rule and one for `tools.approvalMode` of a `settings.json`,
        read as JSONC as Qwen Code reads it; no other key is read, since
        the file can hold provider keys and channel tokens."""
        ts = file_mtime(artifact)
        project = artifact.home.original if artifact.home.project else ""
        try:
            doc = parse_jsonc(artifact.disk_path.read_bytes())
        except (OSError, ValueError):
            doc = None
        if not isinstance(doc, dict):
            text = "parser: %s is not a JSON object" % artifact.rel
            yield self._settings_row(artifact, ts, project, text)
            return
        settings: list = []
        perms = doc.get("permissions")
        perms = perms if isinstance(perms, dict) else {}
        for key in PERMISSION_LISTS:
            entries = perms.get(key)
            if isinstance(entries, list):
                settings.extend(("permissions." + key, entry) for entry in entries)
        tools = doc.get("tools")
        if isinstance(tools, dict) and tools.get("approvalMode") is not None:
            settings.append(("tools.approvalMode", tools["approvalMode"]))
        for key, value in settings:
            text = "permission setting: %s=%s (from %s, file mtime)" % (
                key,
                setting_value(value),
                artifact.rel,
            )
            yield self._settings_row(artifact, ts, project, text)

    def _parse_usage(self, artifact: Artifact) -> Iterator[Row]:
        """One `session usage:` row per `usage_record.jsonl` line, at its
        `startTime`; a secondary source that survives the session's delete."""
        errors: list = []
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            models = rec.get("models")
            tools = rec.get("tools")
            by_name = tools.get("byName") if isinstance(tools, dict) else None
            counts = [
                "%s=%s" % (name, v.get("count") if isinstance(v, dict) else v)
                for name, v in (by_name.items() if isinstance(by_name, dict) else ())
            ]
            row = self.base_row(artifact)
            row.source_line = n
            row.turn_type = "system"
            row.timestamp_utc = to_utc(rec.get("startTime"))
            row.session_id = str(rec.get("sessionId") or "")
            row.project_path = str(rec.get("project") or "")
            duration = rec.get("durationMs")
            row.text = compact(
                "session usage: project %s duration %s models %s tools %s"
                " (from usage_record.jsonl, startTime)"
                % (
                    row.project_path or "-",
                    "%sms" % duration if duration not in (None, "") else "-",
                    ",".join(models) if isinstance(models, dict) and models else "-",
                    ",".join(counts) or "-",
                )
            )
            yield row
        yield from error_rows(self, artifact, errors)

    @staticmethod
    def _context_changes(rec: dict, session_id: str, models: dict, modes: dict) -> list:
        """The `model:` and `permission mode:` row texts (with the model for
        the `model` column) for a record's `executionContext`, when either
        differs from the one in force for the session."""
        ctx = rec.get("executionContext")
        if not isinstance(ctx, dict):
            return []
        out = []
        model = str(ctx.get("modelId") or "")
        change = track_change("model", models, session_id, model)
        if change:
            auth = ctx.get("authType")
            out.append((change + (" auth=%s" % auth if auth else ""), model))
        mode = track_change(
            "permission mode", modes, session_id, str(ctx.get("approvalMode") or "")
        )
        if mode:
            out.append((mode, ""))
        return out

    def _parse_session(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        session_id = project_path = ""
        models: dict = {}  # session id -> model in force, for the model rows
        modes: dict = {}  # session id -> approval mode in force
        for n, rec in iter_jsonl(artifact.disk_path, errors):
            rtype = rec.get("type")
            if rec.get("sessionId"):
                session_id = str(rec["sessionId"])
            if rec.get("cwd"):
                project_path = str(rec["cwd"])

            def base(turn_type: str, text: str) -> Row:
                row = self.base_row(artifact)
                row.source_line = n
                row.timestamp_utc = to_utc(rec.get("timestamp"))
                row.session_id = session_id
                row.project_path = str(rec.get("cwd") or "")
                row.git_branch = str(rec.get("gitBranch") or "")
                row.turn_type = turn_type
                row.text = compact(text)
                return row

            for text, model in self._context_changes(rec, session_id, models, modes):
                row = base("system", text)
                row.model = model
                yield row
            parts = _parts(rec)
            if rtype == "user":
                text = "\n".join(
                    p["text"]
                    for p in parts
                    if isinstance(p.get("text"), str) and not p.get("thought")
                )
                if not text:
                    payload = rec.get("systemPayload")
                    if isinstance(payload, dict):
                        text = str(payload.get("displayText") or "")
                origin = injected_origin(rec)
                if origin:
                    yield base("system", "%s: %s" % (origin, text) if text else origin)
                else:
                    yield base("user", text)
            elif rtype == "assistant":
                model = str(rec.get("model") or "")
                change = track_change("model", models, session_id, model)
                if change:
                    row = base("system", change)
                    row.model = model
                    yield row
                for p in parts:
                    fc = p.get("functionCall")
                    if isinstance(fc, dict):
                        row = base("tool_use", args_summary(fc.get("args")))
                        row.tool_name = str(fc.get("name") or "")
                        row.tool_use_id = str(fc.get("id") or "")
                    elif isinstance(p.get("text"), str) and p.get("thought"):
                        if not opts.include_thinking:
                            continue
                        row = base("thinking", p["text"])
                    elif isinstance(p.get("text"), str) and p["text"]:
                        row = base("assistant", p["text"])
                    else:
                        continue
                    row.model = model
                    yield row
            elif rtype == "tool_result":
                tcr = rec.get("toolCallResult")
                tcr = tcr if isinstance(tcr, dict) else {}
                responses = [
                    p["functionResponse"]
                    for p in parts
                    if isinstance(p.get("functionResponse"), dict)
                ]
                fr = responses[0] if responses else {}
                display = tcr.get("resultDisplay")
                if isinstance(display, str) and display:
                    text = display
                elif fr:
                    text = _response_text(fr.get("response"))
                else:
                    text = compact_json(display) if display else ""
                status = str(tcr.get("status") or "")
                if status and status != "success":
                    tag = (
                        status
                        if not tcr.get("errorType")
                        else "%s %s" % (status, tcr.get("errorType"))
                    )
                    text = "[%s] %s" % (tag, text)
                row = base("tool_result", text)
                row.tool_name = str(fr.get("name") or "")
                row.tool_use_id = str(tcr.get("callId") or fr.get("id") or "")
                yield row
                if status in DECISION_STATUSES:
                    dec = base("system", "permission decision: %s" % status)
                    dec.tool_name, dec.tool_use_id = row.tool_name, row.tool_use_id
                    yield dec
            elif rtype == "system":
                subtype = str(rec.get("subtype") or "system")
                payload = rec.get("systemPayload")
                text = system_text(subtype, payload)
                model = ""
                if subtype == "session_model" and isinstance(payload, dict):
                    model = str(payload.get("modelId") or "")
                    if model:
                        change = track_change("model", models, session_id, model)
                        text = "%s auth=%s" % (
                            change or "model: %s" % model,
                            payload.get("authType") or "",
                        )
                elif subtype == "session_approval_mode" and isinstance(payload, dict):
                    mode = str(payload.get("mode") or "")
                    if mode:
                        change = track_change("permission mode", modes, session_id, mode)
                        extras = [
                            " %s=%s" % (k, payload[k])
                            for k in ("prePlanMode", "planExecutionMode")
                            if payload.get(k)
                        ]
                        text = (change or "permission mode: %s" % mode) + "".join(extras)
                row = base("system", text)
                row.model = model
                yield row
                event = payload.get("uiEvent") if isinstance(payload, dict) else None
                if (
                    subtype == "ui_telemetry"
                    and isinstance(event, dict)
                    and event.get("event.name") == TOOL_CALL_EVENT
                    and event.get("decision")
                ):
                    dec = base(
                        "system",
                        "permission decision: %s (tool_call ui_telemetry)" % event["decision"],
                    )
                    dec.tool_name = str(event.get("function_name") or "")
                    dec.tool_use_id = str(event.get("call_id") or "")
                    yield dec
        yield from error_rows(self, artifact, errors, session_id, project_path)

    def _parse_logs(self, artifact: Artifact, opts: Options) -> Iterator[Row]:
        errors: list = []
        for idx, entry in self._iter_array(artifact.disk_path, errors):
            row = self.base_row(artifact)
            row.source_line = idx
            row.timestamp_utc = to_utc(entry.get("timestamp"))
            row.session_id = str(entry.get("sessionId") or "")
            etype = entry.get("type")
            message = entry.get("message")
            if etype == "user":
                row.turn_type = "user"
                text = message if isinstance(message, str) else compact_json(message)
            else:
                row.turn_type = "system"
                event = message
                if isinstance(message, str):
                    try:
                        event = json.loads(message)
                    except ValueError:
                        event = message
                if etype == "model_switch" and isinstance(event, dict):
                    text = "model: %s -> %s reason=%s" % (
                        event.get("fromModel"),
                        event.get("toModel"),
                        event.get("reason"),
                    )
                    row.model = str(event.get("toModel") or "")
                else:
                    text = "%s: %s" % (
                        etype,
                        event if isinstance(event, str) else compact_json(event),
                    )
            row.text = compact(text)
            yield row
        yield from error_rows(self, artifact, errors)

    @staticmethod
    def _iter_array(path, errors: list):
        """Yield (1-based index, entry) from a JSON array, decoding element by
        element so a file cut mid-write still yields the entries before the
        cut. A parse failure is recorded in `errors` as (index, message, raw)
        and ends the walk; raw is the text from the element the failed decode
        started at to the end of the file, less a trailing line terminator,
        since a broken element has no boundary of its own and nothing after
        it is decoded (issue 136). A whole-file error has raw `""`."""
        with open(path, "rb") as fh:
            data = fh.read().decode("utf-8", errors="replace")
        dec = json.JSONDecoder()
        pos = 0
        n = len(data)

        def skip(p: int) -> int:
            while p < n and data[p] in " \t\r\n":
                p += 1
            return p

        pos = skip(pos)
        if pos >= n:
            return
        if data[pos] != "[":
            errors.append((0, "not a JSON array", ""))
            return
        pos = skip(pos + 1)
        idx = 0
        while pos < n and data[pos] != "]":
            idx += 1
            try:
                value, pos = dec.raw_decode(data, pos)
            except ValueError as e:
                errors.append((idx, "unparseable record %d (%s)" % (idx, e), tail_text(data, pos)))
                return
            if isinstance(value, dict):
                yield idx, value
            pos = skip(pos)
            if pos < n and data[pos] == ",":
                pos = skip(pos + 1)
        if pos >= n:
            errors.append((idx + 1, "unterminated JSON array", ""))
