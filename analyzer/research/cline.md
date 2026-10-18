# Cline transcript schema

Catalog agent: `cline`. Researched together with Roo Code and Kilo Code; Roo
forked Cline and still shares its task layout ([roo-code.md](roo-code.md)),
Kilo has since moved to an OpenCode-derived store
([kilo-code.md](kilo-code.md)). Paths cited are relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/cline.md`](../../collectors/research/cline.md).

## 1. Source

[cline/cline](https://github.com/cline/cline) at [`39ff2359f7e08231281539696e48a166ce49270c`](https://github.com/cline/cline/commit/39ff2359f7e08231281539696e48a166ce49270c), Apache-2.0. Open
source. Applies to the VS Code extension (`saoudrizwan.claude-dev`), the CLI
and JetBrains, all through the `sdk/` packages.

## 2. Transcript files

Legacy task layout, one directory per task. Root is VS Code
`globalStorage/saoudrizwan.claude-dev/` for the extension
([`apps/vscode/src/core/storage/disk.ts:190-194`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L190-L194)) or `~/.cline/data/` for CLI
and JetBrains ([`apps/vscode/src/sdk/legacy-state-reader.ts:24-29`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/sdk/legacy-state-reader.ts#L24-L29)); env
`CLINE_DATA_DIR` or `CLINE_DIR` overrides. Files ([`disk.ts:17-36`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L17-L36),
[`legacy-state-reader.ts:42-72`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/sdk/legacy-state-reader.ts#L42-L72)): `tasks/<taskId>/api_conversation_history.json`
(JSON array), `ui_messages.json` (JSON array), `context_history.json`,
`task_metadata.json`, `settings.json`; index `state/taskHistory.json` (JSON
array of `HistoryItem`); `globalState.json`, `secrets.json`,
`settings/cline_mcp_settings.json`. `taskId` is a `Date.now()` millisecond
string (`HistoryItem.id`).

SDK session layout, current on all hosts: `~/.cline/data/sessions/<sessionId>/`
([`sdk/packages/shared/src/storage/paths.ts:179-192`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/storage/paths.ts#L179-L192)) holding
`<sessionId>.json` (manifest), `<sessionId>.messages.json`,
`<sessionId>.compaction.json` ([`sdk/packages/core/src/services/session-artifacts.ts:75-94`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/session-artifacts.ts#L75-L94));
subagent transcripts in the same directory as `<agentId>.messages.json` or
`<agentId>__<teamTaskId>.messages.json` ([`:34-57`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/session-artifacts.ts#L34-L57),[`132-144`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/session-artifacts.ts#L132-L144)). `sessionId` is
`${Date.now()}_${nanoid(5)}` ([`session/services/persistence-service.ts:109`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/services/persistence-service.ts#L109)).
Fallback index `sessions/sessions.index.json`
([`session/services/file-session-service.ts:63`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/services/file-session-service.ts#L63)). SQLite in `~/.cline/data/db/`
([section 5](#5-sqlite-stores)). Hook audit `~/.cline/data/logs/hooks.jsonl`
([`hooks/hook-file-hooks.ts:647`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/hooks/hook-file-hooks.ts#L647)).

The CLI's prompt history for up-arrow recall is
`~/.cline/data/cache/user_input_history.jsonl`
([`apps/cli/src/utils/input-history.ts:7-9`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/input-history.ts#L7-L9)). Each line is
`{"prompt": <string>, "ts": <epoch ms>}`. When the terminal UI submits a
prompt that is not a queued delivery
([`apps/cli/src/tui/hooks/use-prompt-input-controller.ts:335-337`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/tui/hooks/use-prompt-input-controller.ts#L335-L337),
[`use-input-history.ts:109-116`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/tui/hooks/use-input-history.ts#L109-L116)),
the CLI reads the file, removes any earlier copy of the trimmed prompt,
appends it, keeps the last 20 (`MAX_HISTORY`) and rewrites the whole file,
stamping every line with that write's `Date.now()`
([`input-history.ts:5`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/input-history.ts#L5), [`:37-72`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/input-history.ts#L37-L72)). So the lines
are oldest first, each prompt once, and only the last line's `ts` is its
own prompt's time; the others carry the time of the last write. No
session id, working directory or model is recorded. Malformed lines are
skipped when the CLI reads it ([`:11-30`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/input-history.ts#L11-L30)) and dropped at the
next rewrite.

The VS Code extension keeps its enterprise prompt upload queue, the task
files waiting for or done with an upload to the organisation's bucket, in
`<GS>/saoudrizwan.claude-dev/cache/sync-queue.json`
([`apps/vscode/src/shared/services/worker/sync.ts:27-29`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/sync.ts#L27-L29)):
`{items: {<taskId>/<key>: {id, taskId, key, data, timestamp, status,
retryCount, lastError}}}`, where `key` is the task file's name (such as
`api_conversation_history.json`), `data` the file's whole content,
`timestamp` the enqueue time in epoch ms and `status` `pending`, `synced`
or `failed` ([`queue.ts:9-31`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/queue.ts#L9-L31),
[`157-170`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/queue.ts#L157-L170)). An upload marks its item `synced`
([`212-220`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/queue.ts#L212-L220)); a synced item older than seven days
and a failed one past its retries or seven days old are removed
([`302-315`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/queue.ts#L302-L315), [`325-338`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/queue.ts#L325-L338);
[`worker.ts:201-204`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/services/worker/worker.ts#L201-L204)), so the file holds the
recent uploads only. Not seen on a real install.

## 3. Record schema

`api_conversation_history.json` is `Anthropic.MessageParam[]` ([`disk.ts:155`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L155)):
`{role: "user"|"assistant", content: string | [{type:"text",text} |
{type:"tool_use",id,name,input} | {type:"tool_result",tool_use_id,content,is_error?}
| {type:"thinking",thinking} | {type:"image",source:{type:"base64",media_type,data}}]}`
(block handling [`apps/vscode/src/sdk/legacy-task-handling.ts:13-45`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/sdk/legacy-task-handling.ts#L13-L45)). No
timestamps. Legacy tool calls are mostly XML inside text blocks, not
`tool_use`.

`ui_messages.json` is `ClineMessage[]` ([`apps/vscode/src/shared/ExtensionMessage.ts:178-208`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/ExtensionMessage.ts#L178-L208)):
`ts` (ms, also the identity), `type: "ask"|"say"`, `ask?`, `say?`, `text?`,
`reasoning?`, `images?`, `files?`, `partial?`, `conversationHistoryIndex?`,
`lastCheckpointHash?`, `modelInfo?: {modelId, providerId, mode}`
([`shared/messages/metrics.ts`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/messages/metrics.ts)). Asks [`:210-228`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/ExtensionMessage.ts#L210-L228) (followup,
plan_mode_respond, act_mode_respond, command, command_output,
completion_result, tool, api_req_failed, resume_task, use_mcp_server,
new_task, condense, ...); says [`:230-267`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/ExtensionMessage.ts#L230-L267) (task, error, api_req_started,
api_req_finished, text, reasoning, completion_result, user_feedback, command,
command_output, tool, browser_action*, mcp_server_request_started,
mcp_server_response, checkpoint_created, hook_status, subagent, compaction,
...). `text` is JSON for `say`/`ask` `"tool"` (`ClineSayTool {tool, path,
diff, content, regex, filePattern}`, [`:269-294`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/ExtensionMessage.ts#L269-L294)), `"api_req_started"`
(`ClineApiReqInfo {request, tokensIn, tokensOut, cacheWrites, cacheReads,
cost, cancelReason}`, [`:370-379`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/ExtensionMessage.ts#L370-L379)) and `"use_mcp_server"` (`{serverName, type,
toolName, arguments, uri}`, [`:346-352`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/ExtensionMessage.ts#L346-L352)).

`HistoryItem` ([`apps/vscode/src/shared/HistoryItem.ts:1-26`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/HistoryItem.ts#L1-L26)): `id, ulid?, ts,
task, tokensIn, tokensOut, cacheWrites?, cacheReads?, totalCost, size?,
cwdOnTaskInitialization?, modelId?, apiProvider?, isLegacy?`.

`task_metadata.json` ([`core/context/context-tracking/ContextTrackerTypes.ts:28-32`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/context/context-tracking/ContextTrackerTypes.ts#L28-L32)):
`files_in_context[{path, record_state, record_source, cline_read_date,
cline_edit_date}]`, `model_usage[{ts, model_id, model_provider_id, mode}]`,
`environment_history[{ts, os_name, os_version, host_name, cline_version}]`.

SDK manifest `<id>.json` ([`sdk/packages/core/src/session/models/session-manifest.ts:6-28`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/models/session-manifest.ts#L6-L28)):
`version:1, session_id, source, pid, started_at (ISO 8601), ended_at?,
exit_code?, status (idle|running|pending|completed|failed|cancelled,
shared/src/session/records.ts:1-15), interactive, provider, model, cwd,
workspace_root, team_name?, enable_tools, enable_spawn, enable_teams,
prompt?, metadata?{title,...}, messages_path?`.

The manifest's `metadata` object, also stored as the `sessions.db` column
`metadata_json`
([`session-manifest.ts:25`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/models/session-manifest.ts#L25),
[`session/services/session-service.ts:167-170`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/services/session-service.ts#L167-L170)),
carries the enterprise prompt-upload marker. Remote config is the organisation
settings document the Cline account API serves to a signed-in member of an
enterprise organisation, at `/api/v1/users/me/remote-config`
([`sdk/packages/core/src/account/cline-account-service.ts:98-102`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/account/cline-account-service.ts#L98-L102)).
When its `enterpriseTelemetry.promptUploading` block is enabled with access
keys for an S3 (Amazon's object store), R2 (Cloudflare's S3-compatible store)
or Azure Blob bucket
([`sdk/packages/shared/src/remote-config/schema.ts:148-174`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/schema.ts#L148-L174),
[`remote-config/blob-storage.ts:91-127`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/blob-storage.ts#L91-L127)),
the session's metadata gets the key `enterprise.blobUpload`
([`:56-57`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/blob-storage.ts#L56-L57)):
`{version: 1, storage: {adapterType: "s3"|"r2"|"azure", bucket, region?,
endpoint?, accountId?}, userDistinctId?}`, the target with the access keys
stripped
([`:79-89`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/blob-storage.ts#L79-L89),
[`:129-160`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/blob-storage.ts#L129-L160)).
The CLI writes it with `updateSession` right after the session starts
([`apps/cli/src/connectors/session-runtime.ts:248-258`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/connectors/session-runtime.ts#L248-L258),
[`apps/cli/src/runtime/run-zen.ts:110-119`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/runtime/run-zen.ts#L110-L119),
[`apps/cli/src/utils/enterprise.ts:167-186`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/enterprise.ts#L167-L186)),
without `userDistinctId`; the VS Code host adds it, with `userDistinctId` set
to the remote-config token's subject, to the start input
([`apps/vscode/src/sdk/vscode-session-host.ts:150-153`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/sdk/vscode-session-host.ts#L150-L153),
[`sdk/packages/core/src/remote-config/integration.ts:74-108`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/remote-config/integration.ts#L74-L108)),
which the runtime merges into the manifest at start
([`local-runtime-host.ts:630-634`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/runtime/host/local-runtime-host.ts#L630-L634)).
A session started without such a remote config has no `enterprise.blobUpload`
key. The CLI hands its session store an uploader
([`apps/cli/src/session/session.ts:66`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/session/session.ts#L66)),
and every time that store rewrites `<sessionId>.messages.json` it PUTs the
same bytes to the object `sessions/<userDistinctId or
unknown>/<sessionId>/messages.json` in that bucket
([`session/stores/session-manifest-store.ts:238-248`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/stores/session-manifest-store.ts#L238-L248),
[`blob-storage.ts:367-414`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/blob-storage.ts#L367-L414));
a failed upload is logged at debug level only and leaves the key in place.
`keyPrefix` is read back from the stored metadata but not used in the object
name.

SDK `<id>.messages.json` ([`services/session-data.ts:334-359`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/session-data.ts#L334-L359),[`281-294`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/session-data.ts#L281-L294)):
`{version:1, updated_at (ISO), agent:"lead"|"subagent"|"teammate",
sessionId, taskType?, origin{source, mode, sessionId, parentThreadId?,
subagent?, version?, trigger?}, system_prompt?, messages:
MessageWithMetadata[]}`. Message ([`sdk/packages/shared/src/llms/messages.ts:130-165`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/llms/messages.ts#L130-L165)):
`role: "user"|"assistant"`, `content: string|ContentBlock[]`, `id?`, `agent?`,
`sessionId?`, `metadata?` (keys seen at call sites: `displayOnly`,
`displayRole`, `kind`, `userRunSpan`, `checkpoint`), `modelInfo?{id, provider,
family?}`, `metrics?{inputTokens, outputTokens, cacheReadTokens,
cacheWriteTokens, cost}`, `ts?` (ms epoch, [`session-data.ts:196`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/session-data.ts#L196)). Blocks
([`messages.ts:19-125`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/llms/messages.ts#L19-L125)): `text{text}`, `tool_use{id, call_id?, name, input}`,
`tool_result{tool_use_id, name, content, is_error?}`, `thinking{thinking,
signature?}`, `redacted_thinking{data}`, `image{data, mediaType}`,
`file{content, path}`, `media`.

Timestamps are millisecond epochs except the SDK manifest and payload
(`started_at`, `updated_at` ISO). No git branch is recorded.

## 4. Joins

Legacy: directory name = `HistoryItem.id`; workspace =
`cwdOnTaskInitialization` in `state/taskHistory.json`;
`ClineMessage.conversationHistoryIndex` indexes into
`api_conversation_history.json`; `tool_use.id` pairs with
`tool_result.tool_use_id` within the array (rare, since most tool traffic is
XML text). SDK: `messages.json.sessionId` = manifest `session_id` =
`sessions.session_id`; workspace = manifest `cwd` or `workspace_root`;
`tool_use.id` pairs with `tool_result.tool_use_id`. `session-search.db`
`session_search.session_id` = `sessions.session_id` = the session directory
name, and a message document's `ordinal` is the message's 0-based position
in the lead `<sessionId>.messages.json` ([section 5](#5-sqlite-stores)).
VS Code merges the legacy
and SDK lists ([`apps/vscode/src/sdk/sdk-task-history.ts:413-424`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/sdk/sdk-task-history.ts#L413-L424)), stamping
`metadata.legacyTask`.

## 5. SQLite stores

`~/.cline/data/db/sessions.db` ([`paths.ts:240-249`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/storage/paths.ts#L240-L249);
[`shared/src/db/sqlite-db.ts:188-273`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/db/sqlite-db.ts#L188-L273)): `sessions(session_id, source, pid,
started_at, ended_at, exit_code, status, status_lock, interactive, provider,
model, cwd, workspace_root, team_name, enable_*, parent_session_id,
parent_agent_id, agent_id, conversation_id, is_subagent, prompt,
metadata_json, transcript_path, hook_path, messages_path, updated_at)`,
`subagent_spawn_queue`, `schedules(prompt, system_prompt, ...)`,
`schedule_executions`. `db/session-search.db`: `indexed_sessions` plus FTS5
`session_search(session_id, document_id, ordinal, role, started_at,
workspace_root, title, content)` ([`session/search/session-history-search.ts:123-153`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L123-L153),[`196`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L196)),
a full-text copy of every transcript, described below. `teams/teams.db`
([`services/storage/sqlite-team-store.ts:210-330`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/storage/sqlite-team-store.ts#L210-L330),[`431-445`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/storage/sqlite-team-store.ts#L431-L445)): `team_events(payload_json)`,
`team_tasks`, `team_runs`, `team_mailbox(data_json)`,
`team_mission_log(data_json)`.

`session-search.db` in detail. It sits beside `sessions.db` in the
directory `resolveDbDataDir()` names, `~/.cline/data/db` unless
`CLINE_DB_DATA_DIR` or `CLINE_DATA_DIR` moves it
([`paths.ts:179-185`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/storage/paths.ts#L179-L185),
[`240-246`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/storage/paths.ts#L240-L246),
[`session-history-search.ts:196`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L196)); nothing writes it under an
editor's `globalStorage`. FTS5 is SQLite's full-text search extension; the
table is created with five `UNINDEXED` columns (stored, not searchable)
and three indexed ones ([`:143-153`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L143-L153)), and
`indexed_sessions(session_id, source_revision, indexed_at, document_count,
index_version, title)` records one row per indexed session
([`:123-142`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L123-L142)). The SDK's hub server builds and maintains
it
([`hub-server-transport.ts:283-287`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/hub/server/hub-server-transport.ts#L283-L287)).
Per session ([`session-history-search.ts:402-465`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L402-L465)):

- one document `<sessionId>:metadata`, `ordinal` -1, `role` `session`,
  `title` the session's `metadata.title` or else its `prompt`, whitespace
  collapsed and cut to 240 characters
  ([`:102-109`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L102-L109),
  [`prompt/format.ts:195-206`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/prompt/format.ts#L195-L206)),
  and `content` the session's `prompt` ([`:423-432`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L423-L432));
- one document `<sessionId>:<n>` per message of the lead transcript with any
  text, `ordinal` the message's 0-based index in the array (so a message
  with no text leaves a gap), `role` the message's `role` or `unknown`
  ([`:97-100`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L97-L100), [`:434-448`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L434-L448)). The
  messages are read from the session's `messages_path`
  ([`local-runtime-host.ts:1559-1570`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/runtime/host/local-runtime-host.ts#L1559-L1570)),
  the lead `<sessionId>.messages.json`; subagent transcripts are not
  indexed;
- `started_at` and `workspace_root` on every document are the session's
  (`SessionRecord.startedAt`, an ISO 8601 string, and `workspaceRoot`,
  [`shared/src/session/records.ts:34-55`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/session/records.ts#L34-L55)).
  No document records a time of its own.

A document's `content` is every string value found by walking the
message's `content` (or the message, when it has none), object keys in
order, skipping the keys `data`, `image`, `images`, `reasoning`,
`thinking` and `metadata`, joined with line breaks, trimmed, and capped at
128 KiB ([`:14`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L14), [`:54-95`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L54-L95)). A plain-string
`content` is therefore indexed as itself: a user prompt with no attached
image or file is a string
([`user-input-builder.ts:10-37`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/runtime/orchestration/user-input-builder.ts#L10-L37)).
A block array is indexed with the block `type` names, tool ids, tool names
and tool input strings in it (`[{"type":"text","text":"Fixed."}]` becomes
`text` and `Fixed.` on two lines), and the text of `thinking` blocks is
left out. Numbers and booleans are left out.

What it survives. The hub reconciles the index when it starts and every
five minutes while it runs ([`:13`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L13), [`:204-216`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L204-L216)):
a session no longer listed in `sessions.db` is deleted from the index, and
a session whose `updated_at`, messages file size or mtime changed is
re-indexed from the file as it now is, so a deleted messages file leaves
only the metadata document ([`:350-400`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L350-L400)). Deleting a
session through the hub removes it at once ([`:242-257`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/search/session-history-search.ts#L242-L257)).
The index therefore holds a session's turns after its transcript is gone
only until the hub next runs: a session deleted by hand, by a cleanup
script or by an attacker while no Cline process ran is still in it at
collection time. It holds no compaction or rewind history of its own,
since each re-index replaces a session's documents.

## 6. Format versions

Three generations coexist on disk: VS Code globalStorage tasks,
`~/.cline/data/tasks` with `state/taskHistory.json`, and
`~/.cline/data/sessions/<id>/`. The VS Code to file migration of state and
secrets uses the sentinel `__migrationVersion`
([`hosts/vscode/vscode-to-file-migration.ts:11-31`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/hosts/vscode/vscode-to-file-migration.ts#L11-L31)); task files are not moved.
SDK files carry `version: 1`. Legacy tasks resumed in the SDK get
`metadata.legacyTask: true`. `sessions.db` has ALTER-based column migrations
([`sqlite-db.ts:275-340`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/db/sqlite-db.ts#L275-L340)).

## 7. Secrets

`secrets.json` keys ([`apps/vscode/src/shared/storage/state-keys.ts`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/storage/state-keys.ts)
SECRETS_KEYS): `apiKey, clineApiKey, clineAccountId, openRouterApiKey,
awsAccessKey, awsSecretKey, awsSessionToken, openAiApiKey, geminiApiKey, ...,
mcpOAuthSecrets, openai-codex-oauth-credentials, ocaRefreshToken`. Also
`messages.json.system_prompt`, `manifest.prompt`, `schedules.system_prompt`,
`session-search.db` content, `images[]` base64, and file contents and command
output in every transcript.

Two files that the upload features use hold credentials and are collected
without the secret flag. The VS Code extension caches each organisation's
remote config, `promptUploading` access keys (`accessKeyId`,
`secretAccessKey`) included, as
`<GS>/saoudrizwan.claude-dev/cache/remote_config_<organizationId>.json`
([`apps/vscode/src/core/storage/disk.ts:35`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L35),
[`:186-188`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L186-L188),
[`:248-252`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L248-L252),
[`core/storage/remote-config/sdk-control-plane.ts:198`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/remote-config/sdk-control-plane.ts#L198));
the CLI fetches it on each session start and keeps no copy
([`apps/cli/src/utils/enterprise.ts:37-73`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/enterprise.ts#L37-L73)).
The LG CNS webhook integration (named for LG CNS, the LG group's IT services
company, in the source directory `lg-cns-integration`) writes
`~/Documents/Cline/webhook_config.json` with `webhook_url`, `webhook_token` (a
bearer token) and `created_at`
([`apps/vscode/src/services/lg-cns-integration/webhook-hooks.ts:11-30`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/services/lg-cns-integration/webhook-hooks.ts#L11-L30)).

## 8. Parser plan

Globs (home-relative; `<GS>` is each VS Code `User/globalStorage`):
`<GS>/saoudrizwan.claude-dev/tasks/*/{api_conversation_history,ui_messages,task_metadata}.json`,
`<GS>/saoudrizwan.claude-dev/state/taskHistory.json`, the same under
`.cline/data/`, `.cline/data/sessions/*/*.json`,
`.cline/data/sessions/*/*.messages.json`, `.cline/data/db/sessions.db`,
`.cline/data/db/session-search.db`, `.cline/data/cache/user_input_history.jsonl`,
`.cline/data/logs/hooks.jsonl`, `<GS>/saoudrizwan.claude-dev/cache/sync-queue.json`.

Sources, primary or secondary (the analyzer drops a row of a secondary
source that a primary store records too, issue 122):

- Primary: `ui_messages.json`, `api_conversation_history.json` (when no
  `ui_messages.json` is beside it), `task_metadata.json`,
  `state/taskHistory.json`, the SDK manifest and `*.messages.json`, and
  `sessions.db` (only for sessions whose manifest is gone).
- Secondary: `session-search.db`. One `system` row per indexed session at
  its `started_at`, `session search index: title=<title>
  workspace_root=<workspace_root> prompt=<metadata content>
  document_count=<n> indexed_at=<indexed_at>`; then one row per message
  document in `ordinal` order, `user` or `assistant` by `role`, `system`
  for any other, `source_line` `ordinal + 1` (the message's position in
  the transcript, as the messages reader numbers it), and no
  `timestamp_utc`, since the index records none per message.
  `session_id` is the index's `session_id`, which is the session
  directory name the messages reader uses; `project_path` is the
  manifest's `cwd` (else `workspace_root`) when the manifest is on disk,
  as the messages reader takes it, and the document's `workspace_root`
  otherwise. A plain-string message pairs with its transcript row on
  text and session; a block-array message's text carries the block type
  names and tool ids and never equals a transcript row, so it is kept
  whether or not the transcript survives. When the SQLite build lacks
  FTS5, one `system` row says so and `indexed_sessions` is read alone,
  each session row without a time.
- Secondary: `cache/user_input_history.jsonl`
  ([section 2](#2-transcript-files)). One `user` row per line, with no
  `session_id` or `project_path`; the last line at its `ts`, every other
  line with no `timestamp_utc`, and every line undated when the file has a
  bad line, since the last line read may then not be the newest. An
  undated row matches a transcript prompt of any Cline session on text
  alone; the dated one matches within 2 seconds. It survives the deletion
  of the sessions it came from, holding their last 20 distinct prompts.
  When a prompt is in this file and in `session-search.db` too, whichever
  secondary row the duplicate rule reaches first takes the transcript row,
  and in the fixture the index's copy is the one left over.

The API history is not a second copy of `ui_messages.json` that the rule
could pair, so it stays a fallback for a task without `ui_messages.json`.
The two record different texts for the same turn: the API history wraps
the first prompt as `<task>\n...\n</task>` (with environment details in
real tasks) where `ui_messages.json` holds the prompt as typed, as the
extension's own sample-task generator writes them
([`apps/vscode/src/dev/commands/tasks.ts:95-117`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/dev/commands/tasks.ts#L95-L117),
[`:172-177`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/dev/commands/tasks.ts#L172-L177)).
Its tool calls are content blocks or XML inside text, where
`ui_messages.json` has one `say`/`ask` record per tool with JSON text, and
its records carry no time. In the fixture the task's API user row is
`<task>fix tests</task>` beside the UI row `fix tests | [1 image(s)]`, and
its tool rows have no UI twin with the same text.

Rows: one per `ui_messages` entry for legacy tasks (preferred over the API
history because it has `ts`), one per content block of SDK messages.

| Column | Legacy | SDK |
| --- | --- | --- |
| timestamp_utc | `ClineMessage.ts` ms | `message.ts` ms, else manifest `started_at` |
| session_id | directory name | `sessionId` |
| project_path | `cwdOnTaskInitialization` | manifest `cwd` |
| git_branch | empty | empty |
| turn_type | say `task`/`user_feedback` → user; `text`/`completion_result` → assistant; `reasoning` → thinking; `tool`/`command`/`use_mcp_server` → tool_use; `command_output`/`mcp_server_response` → tool_result; `error`/`api_req_*` → system | text → by role; tool_use; tool_result; thinking |
| model | `modelInfo.modelId` or `task_metadata.model_usage` | `modelInfo.id` or manifest `model` |
| tool_name | `ClineSayTool.tool` / `use_mcp_server.toolName` | `tool_use.name` |
| tool_use_id | `ts` | `tool_use.id` / `tool_use_id` |
| text | `text` | first text or tool input |

Model and mode rows, all typed `system`:

- Legacy: the task's first `task_metadata.json` `model_usage[]` entry
  yields `model: <model_id> model_provider_id=<model_provider_id>
  mode=<mode>`, and a later entry whose `model_id` differs yields
  `model: <old> -> <new>` with the same pairs, at the entry's `ts`.
- Legacy: the first entry's `mode` yields `permission mode: <mode>` and a
  later entry whose `mode` differs yields `permission mode: <old> ->
  <new>`, so an entry that changes only the mode still has a row.
- SDK: the manifest `model` and `provider` (or the `sessions.db` row of a
  session whose manifest is gone) yield `model: <model>
  provider=<provider>` at `started_at`, and the session start row no
  longer carries `model=`.
- SDK: a message whose `modelInfo.id` differs from the model before it
  yields `model: <old> -> <new> provider=<modelInfo.provider>` ahead of
  its rows. The lead transcript starts from the manifest `model`; a
  subagent transcript starts from its own first `modelInfo.id`.
- `ui_messages.json` `modelInfo` and `HistoryItem.modelId` fill the
  `model` column only.

Permission decisions: whether the answer to an `ask` (approve or reject)
is stored, and where the auto-approval settings live, are not in this
research, so the parser yields no `permission decision:` or `permission
setting:` row.

Sync: the SDK manifest `metadata` key `enterprise.blobUpload` (and the same
object in `sessions.db` `metadata_json`, [section 3](#3-record-schema)) marks
a session whose transcript is uploaded to the organisation's own S3, R2 or
Azure bucket under an enterprise remote config. It is written once, at session
start, and the upload repeats on every rewrite of the messages file, so the
remote copy is the transcript as last written; the organisation's remote
config turns it on, not a local setting.
The parser yields one `system` row after the session start row (and its
`model:` row), `session
synced: enterprise prompt upload to <adapterType> bucket <bucket> object
sessions/<userDistinctId or unknown>/<session_id>/messages.json
endpoint=<endpoint or -> region=<region or -> account=<accountId or -> (from
<session_id>.json metadata enterprise.blobUpload, started_at)`, timestamped by
the manifest's `started_at`, since the key is written at the start of the
session. For a session whose manifest is gone, the `sessions.db` row
yields the same text ending `(from sessions.db sessions.metadata_json
enterprise.blobUpload, started_at)` at that row's `started_at`. The
parser sets `records_sync`, so an SDK session without the key is `synced`
`no`. Fixture only: no real install has shown the key. For the VS Code
extension's legacy tasks the marker is the upload queue
`cache/sync-queue.json` ([section 2](#2-transcript-files)): the parser
yields one `system` row per item, with `session_id` the `taskId` and
`project_path` the task's `cwdOnTaskInitialization` from
`state/taskHistory.json`, at the item's `timestamp`: for a `synced`
item `session synced: enterprise prompt upload synced key <key> retries
<retryCount> (from saoudrizwan.claude-dev/cache/sync-queue.json, item
timestamp)`, and for a `pending` or `failed` one the same text without
the `session synced: ` prefix (`enterprise prompt upload <status> key
...`), since that file has not reached the bucket, so a task with only
such items is `synced` `no`; `-` for a value absent or empty. It never
prints `data` (the file's content) or
`lastError`. A file that is not a JSON object with an `items` object is
one `parser:` row. Fixture only: no real install has shown the file. A
delete through the hub removes the manifest, the messages file and the
`sessions.db` row
([`session/services/persistence-service.ts:586-630`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/session/services/persistence-service.ts#L586-L630)),
so no marker survives on disk, and nothing deletes the uploaded object: the
bucket adapter has only `write`
([`blob-storage.ts:28-30`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/shared/src/remote-config/blob-storage.ts#L28-L30)).
The CLI also reports each upload as a telemetry event
`enterprise.prompt_upload_succeeded` or `enterprise.prompt_upload_failed` with
the session id and bucket
([`apps/cli/src/utils/enterprise.ts:75-115`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/cli/src/utils/enterprise.ts#L75-L115)),
which leaves the host and is not written locally.

Other paths by which session content leaves the host record nothing the parser
can read. The LG CNS webhook is installed by opening a `vscode://` link to the
extension's `/lg-task` path with `prompt-file`, `webhook-url` and
`webhook-token`
([`apps/vscode/src/services/uri/SharedUriHandler.ts:98-121`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/services/uri/SharedUriHandler.ts#L98-L121));
it writes `webhook_config.json` ([section 7](#7-secrets)) and three hook
scripts, `TaskStart`, `PostToolUse` and `TaskComplete` (`.ps1` on Windows),
into `~/Documents/Cline/Hooks/`
([`:32-59`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/services/lg-cns-integration/webhook-hooks.ts#L32-L59),
[`apps/vscode/src/core/storage/disk.ts:88-97`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/core/storage/disk.ts#L88-L97)),
which POST every task start, tool call (tool name and parameters) and task
completion to the webhook
([`:230-322`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/services/lg-cns-integration/webhook-hooks.ts#L230-L322)).
Those files are configuration, not per-task markers; the hooks are already in
the collected `Documents/Cline` tree. Cloud handoff, the SDK's move of a local
session into a Cline cloud sandbox with its transcript as the seed, defines a
`metadata.handoff` object (`toCloudSessionId`, `handedOffAt`, `status`,
`innerSessionId`, `dashboardUrl`, `fingerprint`)
([`sdk/packages/core/src/services/cloud-handoff/types.ts:13-20`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/cloud-handoff/types.ts#L13-L20),
[`cloud-handoff/metadata.ts:98-132`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/core/src/services/cloud-handoff/metadata.ts#L98-L132)),
but no host in the repository starts a handoff or writes that object: the only
caller of the cloud session controller is the example desktop app
([`apps/examples/desktop-app/sidecar/cloud-sessions.ts:31-53`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/examples/desktop-app/sidecar/cloud-sessions.ts#L31-L53)),
whose cloud sessions run and are stored server-side. Model-call tracing to
Langfuse (an LLM tracing service) is configured from the environment only:
direct `LANGFUSE_*` credentials, or a host OpenTelemetry relay whose spans carry
prompt and reply text only with `CLINE_TRACE_RECORD_CONTENT` set
([`sdk/packages/llms/src/services/langfuse-telemetry.ts:146-163`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/llms/src/services/langfuse-telemetry.ts#L146-L163),
[`:198-268`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/sdk/packages/llms/src/services/langfuse-telemetry.ts#L198-L268)).
The task history (`HistoryItem`) has no share, sync or remote field
([`apps/vscode/src/shared/HistoryItem.ts:1-26`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/shared/HistoryItem.ts#L1-L26)),
and no share-task feature or `shareUrl` exists at this commit (searched
`share`, `shareUrl`, `shareTask` in `apps/` and `sdk/`).

Fixtures (invented content, real field names):

```json
{"_file":"ui_messages.json","record":{"ts":1760000000000,"type":"say","say":"tool","text":"{\"tool\":\"readFile\",\"path\":\"src/app.py\",\"content\":\"/home/u/proj/src/app.py\"}","modelInfo":{"modelId":"claude-sonnet-4-5","providerId":"anthropic","mode":"act"}}}
{"_file":"ui_messages.json","record":{"ts":1760000001000,"type":"say","say":"api_req_started","text":"{\"request\":\"<task>fix tests</task>\",\"tokensIn\":1200,\"tokensOut\":80,\"cacheWrites\":0,\"cacheReads\":900,\"cost\":0.0041}"}}
{"_file":"api_conversation_history.json","record":{"role":"assistant","content":[{"type":"tool_use","id":"toolu_01A","name":"execute_command","input":{"command":"pytest -q"}}]}}
{"_file":"api_conversation_history.json","record":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_01A","content":"3 passed","is_error":false}]}}
{"_file":"state/taskHistory.json","record":{"id":"1760000000000","ulid":"01JAX3Q8M4","ts":1760000000000,"task":"fix tests","tokensIn":1200,"tokensOut":80,"totalCost":0.0041,"cwdOnTaskInitialization":"/home/u/proj","modelId":"claude-sonnet-4-5","apiProvider":"anthropic"}}
{"_file":"sessions/<id>/<id>.json","record":{"version":1,"session_id":"1760000000000_k3x9q","source":"cli","pid":4242,"started_at":"2026-10-03T09:00:00.000Z","status":"completed","interactive":true,"provider":"anthropic","model":"claude-sonnet-4-5","cwd":"/home/u/proj","workspace_root":"/home/u/proj","enable_tools":true,"enable_spawn":false,"enable_teams":false,"prompt":"fix tests","metadata":{"title":"fix tests"},"messages_path":"/home/u/.cline/data/sessions/1760000000000_k3x9q/1760000000000_k3x9q.messages.json"}}
{"_file":"sessions/<id>/<id>.messages.json","record":{"version":1,"updated_at":"2026-10-03T09:00:05.000Z","agent":"lead","sessionId":"1760000000000_k3x9q","origin":{"source":"cli","mode":"user","sessionId":"1760000000000_k3x9q"},"messages":[{"id":"m1","role":"user","content":"fix tests","ts":1760000000000},{"id":"m2","role":"assistant","content":[{"type":"thinking","thinking":"run the suite"},{"type":"tool_use","id":"call_1","name":"bash","input":{"command":"pytest -q"}}],"modelInfo":{"id":"claude-sonnet-4-5","provider":"anthropic"},"metrics":{"inputTokens":1200,"outputTokens":80,"cost":0.0041},"ts":1760000002000},{"id":"m3","role":"user","content":[{"type":"tool_result","tool_use_id":"call_1","name":"bash","content":"3 passed","is_error":false}],"ts":1760000003000}]}}
```

Confidence. High: file names, layouts, `ClineMessage`, `HistoryItem`,
manifest and `MessageWithMetadata` fields, `sessions.db` columns. Medium:
exact `metadata` keys in SDK messages (collected from call sites, not a
schema); whether the VS Code extension now writes new tasks to
`~/.cline/data/sessions` rather than globalStorage (code reads both;
`legacyExtensionStorageDir` is the globalStorage path, [`SdkController.ts:505`](https://github.com/cline/cline/blob/39ff2359f7e08231281539696e48a166ce49270c/apps/vscode/src/sdk/SdkController.ts#L505)).
