# Qwen Code transcript schema

Catalog agent: `qwen-code`. Qwen Code forked Gemini CLI, but its transcript
format has fully diverged: Gemini writes a metadata line plus message records
with `$set`/`$patch`/`$rewindTo` operations, Qwen writes a flat,
Claude-Code-style record stream with `uuid`, `parentUuid`, `cwd` and
`gitBranch` on every line. Only `logs.json`, `checkpoint-*.json`,
`shell_history` and the `tmp/<sha256>` layout are still shared with
[gemini-cli.md](gemini-cli.md). Paths cited are relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/qwen-code.md`](../../collectors/research/qwen-code.md).

## 1. Source

[QwenLM/qwen-code](https://github.com/QwenLM/qwen-code) at [`2c591ecc08a6fa080342f9b1b9f7f43215178cbb`](https://github.com/QwenLM/qwen-code/commit/2c591ecc08a6fa080342f9b1b9f7f43215178cbb) (2026-10-03),
version 0.24.7, Apache-2.0. Open source.

- **Source review (2026-10-19).** HEAD
  [`5dcf7c7`](https://github.com/QwenLM/qwen-code/commit/5dcf7c7cb162e825d95d531081f67ee60da3c0e1)
  (2026-10-20 UTC+8, version 0.25.3) against the commit above. Drift
  from Gemini CLI, checked first: Qwen Code has no `auto-saved.toml`
  policy file (an "always allow" goes to `settings.json`
  `permissions.allow`), no session retention cleanup
  (`sessionRetention` and `maxAge` occur in no session code), and an
  AUTO approval mode with a model classifier that Gemini CLI lacks; it
  keeps Gemini's start-up deletion of `checkpoints/`.
  - Permission state: found, not parsed. Every user record now carries
    `executionContext.approvalMode`; `session_approval_mode` records,
    the per-call `decision` inside `ui_telemetry` records and the
    `permissions` lists in `settings.json` are read only as generic
    rows or not at all. Detail in [section 8](#8-parser-plan).
  - Model: found. `executionContext.modelId` on every user record is
    new and not read; `session_model`, assistant `model` and the
    `logs.json` switch are covered.
  - Past use: found. `usage_record.jsonl`, written for a session before
    its transcript is deleted, and the managed auto-memory directory
    are not parsed. Detail in [section 2](#2-transcript-files).
  - Sync, relay and origin: relay covered (channels). New surfaces not
    reviewed in depth: the Qwen Code Desktop app and the `qwen serve`
    Local Control phone sharing (see [section 8](#8-parser-plan)).
  - Scratch directories: found. `~/.qwen/scratch-workspaces/` is
    already classed by the catalog rule; `<project>/.qwen/worktrees/<slug>`
    is not.
  - Deletion: found; see [section 2](#2-transcript-files).
  - Version drift: found. New record subtypes (`agent_mention`,
    `agent_message`, `turn_attempt`, `code_mode_tool_result`), the
    `executionContext` field, `cancelReason` on `turn_result`, and
    `trustedFolders.json` now parsed as JSONC (JSON with comments) with trailing commas and
    a byte-order mark allowed. The parser reads `notification`, `cron`,
    `agent_mention` and `agent_message` records, all `type: "user"`, as
    user prompts.
  - Bad lines: covered for the transcript, `logs.json`,
    `trustedFolders.json` and the channel routes; a `trustedFolders.json`
    that Qwen accepts (trailing comma, byte-order mark) is reported by
    the parser as not a JSON object.

## 2. Transcript files

Base directory `~/.qwen`, overridable by `$QWEN_HOME`
([`core/src/config/storage.ts:193-202`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L193-L202)) or the `runtimeOutputDir` setting
([128-130](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L128-L130)).

- Session: `~/.qwen/projects/<sanitizeCwd(cwd)>/chats/<sessionId>.jsonl`,
  one file per session ([storage.ts:619-623](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L619-L623); [`utils/paths.ts:388-392`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/utils/paths.ts#L388-L392): every
  character outside `[a-zA-Z0-9]` becomes `-`, Windows lower-cased;
  [`services/chatRecordingService.ts:1305`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L1305),[`1318-1321`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L1318-L1321)). `sessionId` is a UUID;
  listing accepts `/^[0-9a-fA-F-]{32,36}\.jsonl$/`
  ([`services/sessionService.ts:459`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/sessionService.ts#L459)). Archived sessions move to
  `chats/archive/` ([sessionService.ts:949-951](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/sessionService.ts#L949-L951)).
- Sidecars in the same directory: `<sessionId>.runtime.json`
  ([storage.ts:733-740](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L733-L740); snake_case keys, `startedAt` epoch seconds,
  [`utils/runtimeStatus.ts:46-60`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/utils/runtimeStatus.ts#L46-L60)), `<sessionId>.worktree.json`
  ([`worktreeSessionService.ts:38`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/worktreeSessionService.ts#L38)), `<sessionId>.ledger.jsonl` prompt ledger
  ([sessionService.ts:1043-1046](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/sessionService.ts#L1043-L1046)).
- `~/.qwen/tmp/<sha256(cwd)>/`: `logs.json`, `checkpoint-<tag>.json`,
  `checkpoints/`, `shell_history`, `tool-results/`
  ([storage.ts:625-633](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L625-L633),[742-744](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L742-L744),[772-774](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L772-L774); [`core/logger.ts:14`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/logger.ts#L14),[`203-204`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/logger.ts#L203-L204),[`693`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/logger.ts#L693);
  [`paths.ts:368-373`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/utils/paths.ts#L368-L373)).
- Managed-engine sessions: same `.jsonl` location plus
  `~/.qwen/resources/<sessionId>/` ([`utils/sessionStorageUtils.ts:806-816`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/utils/sessionStorageUtils.ts#L806-L816)).
- Channel routes: `~/.qwen/channels/sessions.json`, written by
  `qwen channel start`, which drives sessions from a messaging platform
  (Telegram, WeChat, QQ, DingTalk, WeCom, Feishu, GitHub, GitLab or
  email; the conversation then also lives on that platform's servers)
  ([`cli/src/commands/channel/runtime.ts:43-45`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/commands/channel/runtime.ts#L43-L45)).
  It is one JSON object keyed by routing key (`<channelName>:<chatId>`
  and similar forms by scope), each value
  `{sessionId, target: {channelName, messageRoute?, senderId, chatId,
  threadId?, isGroup?}, cwd, turns?, startedAt?, isolation?,
  workspaceCwd?}`, `startedAt` epoch milliseconds
  ([`channels/base/src/SessionRouter.ts:25-36`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/channels/base/src/SessionRouter.ts#L25-L36),
  [1559-1593](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/channels/base/src/SessionRouter.ts#L1559-L1593);
  [`channels/base/src/types.ts:180-187`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/channels/base/src/types.ts#L180-L187)).
  It is rewritten on every routing change and deleted on a clean
  shutdown (`clearAll`,
  [SessionRouter.ts:1461-1469](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/channels/base/src/SessionRouter.ts#L1461-L1469);
  [`cli/src/commands/channel/start.ts:158`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/commands/channel/start.ts#L158)),
  so it survives only a running service or a crash. The daemon-managed
  form writes the same shape to
  `~/.qwen/channels/daemon/<workspace hash>/routes.json`
  ([runtime.ts:47-62](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/commands/channel/runtime.ts#L47-L62);
  [`cli/src/commands/channel/daemon-worker.ts:656-662`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/commands/channel/daemon-worker.ts#L656-L662))
  and only disposes the router on shutdown
  ([877](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/commands/channel/daemon-worker.ts#L877),
  [892](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/commands/channel/daemon-worker.ts#L892)),
  so that file stays. The session transcripts themselves are ordinary
  `chats/<sessionId>.jsonl` files.

Past use beyond the transcript, at
[`5dcf7c7`](https://github.com/QwenLM/qwen-code/commit/5dcf7c7cb162e825d95d531081f67ee60da3c0e1)
(source review of 2026-10-19). All are collected under `.qwen`; only
`logs.json` is parsed.

- `logs.json` (secondary, parsed): user prompts and model switches.
  The session delete does not touch it (`logs.json` and
  `getProjectTempDir` do not occur in
  [`core/src/services/sessionService.ts`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/sessionService.ts)).
- `~/.qwen/usage_record.jsonl` (secondary, not parsed): one JSON object
  per session, `{version: 1, sessionId, timestamp, startTime, project,
  durationMs, totalLatencyMs?, models: {<model id>: {requests,
  inputTokens, outputTokens, cachedTokens, thoughtsTokens, totalTokens}},
  tools: {totalCalls, totalSuccess, totalFail, byName: {<tool>: {count,
  success, fail}}}, files: {linesAdded, linesRemoved}, skills?}`, with
  epoch-millisecond times, last record per `sessionId` winning
  ([`core/src/services/usageHistoryService.ts:37-77`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/usageHistoryService.ts#L37-L77),
  [140](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/usageHistoryService.ts#L140)).
  Removing a session first salvages its usage into this file and then
  deletes the transcript
  ([`sessionService.ts:3347-3358`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/sessionService.ts#L3347-L3358),
  [3440-3452](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/sessionService.ts#L3440-L3452)),
  so a deleted session survives here as its id, project, start and
  duration, the models it used and how often it called each tool. Joins
  on `sessionId`.
- `~/.qwen/projects/<sanitized project>/memory/` (a projection, not
  parsed): the managed auto-memory documents a background agent
  extracts from conversations, on by default
  (`memory.enableManagedAutoMemory` and `memory.enableManagedAutoDream`,
  [`cli/src/config/settingsSchema.ts:2457-2476`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/config/settingsSchema.ts#L2457-L2476);
  root at
  [`core/src/memory/paths.ts:116-148`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/memory/paths.ts#L116-L148),
  or `<project>/.qwen/memory` with `QWEN_CODE_MEMORY_LOCAL=1`). No
  session id or time; outlives the sessions.
- `shell_history`, `checkpoint-<tag>.json` and `checkpoints/` as in
  Gemini CLI (shell history at
  [`core/src/config/storage.ts:772-774`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/config/storage.ts#L772-L774));
  `checkpoints/` is deleted at start unless an execution sandbox is
  configured
  ([`cli/src/utils/cleanup.ts:126-136`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/utils/cleanup.ts#L126-L136);
  [`cli/src/llm.tsx:587`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/llm.tsx#L587)).

Deletion: removing a session deletes the transcript and then its
worktree and pull-request sidecars, its prompt ledger, its file-history
backups and its managed resources directory
([`sessionService.ts:3539-3558`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/sessionService.ts#L3539-L3558)).
It leaves `logs.json`, `shell_history`, the `/chat save` checkpoints,
`usage_record.jsonl` (with the salvaged summary) and the auto-memory
documents. There is no age-based retention as in Gemini CLI.

Scratch directories:

- `~/.qwen/scratch-workspaces/`: the managed scratch root `qwen serve`
  (the daemon behind the Web Shell and the desktop app) prepares for
  sessions that have no workspace
  ([`cli/src/serve/run-qwen-serve.ts:5285-5292`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/serve/run-qwen-serve.ts#L5285-L5292)).
  A transcript whose `cwd` is under it lies under the home catalog
  entry `.qwen`, so the analyzer's catalog rule already lists it under
  `scratch_directories`; the collector excludes the directory itself.
- `<project>/.qwen/worktrees/<slug>`: the git worktree the
  `enter_worktree` tool creates
  ([`core/src/tools/enter-worktree.ts:29`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/tools/enter-worktree.ts#L29)),
  recorded in `chats/<sessionId>.worktree.json` as `{slug,
  worktreePath, worktreeBranch, originalCwd, workspaceCwd?,
  originalBranch, originalHeadCommit, supersededBy?, supersedes?}`
  ([`core/src/services/worktreeSessionService.ts:38-80`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/worktreeSessionService.ts#L38-L80)).
  Records written inside it carry the worktree as `cwd`. No rule
  classes it as scratch.

## 3. Record schema

Every line is a `ChatRecord` ([`services/chatRecordingService.ts:336-521`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L336-L521)):
`uuid`, `parentUuid: string|null`, `sessionId`, `timestamp` (ISO 8601, [1490](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L1490)),
`type: 'user'|'assistant'|'tool_result'|'system'`, `subtype?` (36 values,
[354-389](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L354-L389), including `chat_compression`, `slash_command`, `custom_title`,
`session_model`, `rewind`, `turn_result`, `branch_checkpoint`,
`managed_session_header_v1`), `provenance?` ([270-276](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L270-L276)), `cwd`, `version` (CLI
version, [1501](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L1501)), `gitBranch?` ([1502-1510](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L1502-L1510) via `getGitBranch(cwd)`),
`promptId?`, `daemonPromptId?`, `message?: Content` (`{role, parts}`),
`usageMetadata?`, `model?`, `contextWindowSize?`, `toolCallResult?:
Partial<ToolCallResponseInfo> & {status?}`, `systemPayload?`, `agentId?`,
`agentName?`, `isSidechain?`, `agentRunId?`, `agentRound?`, `forkedFrom?:
{sessionId, messageUuid}`. Base fields are set at [1474-1504](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L1474-L1504); `parentUuid`
is the previous record's uuid.

- user: `message = {role:'user', parts:[{text}]}`, optional `systemPayload:
  UserPromptRecordPayload {displayText, hookContext, attachmentReferences?,
  resourceLinks?}` ([542-557](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L542-L557)), `promptId` ([2281-2304](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L2281-L2304)).
- assistant: `model`, `message = {role:'model', parts}` whose parts carry
  `text`, `thought: true` text, and `functionCall {id, name, args}`;
  `usageMetadata`, `contextWindowSize` ([2575-2611](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L2575-L2611)).
- tool_result: `message = {role:'user', parts:[{functionResponse:{id, name,
  response}}]}` plus `toolCallResult {callId, responseParts, resultDisplay,
  error, errorType, executionStatus, contentLength, status}`
  ([`core/turn.ts:219-246`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/turn.ts#L219-L246); status values [`core/coreToolScheduler.ts:710`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/coreToolScheduler.ts#L710),
  the same seven strings as Gemini) ([2741-2840](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L2741-L2840)).
- system payloads of interest: `ChatCompressionRecordPayload {info,
  compressedHistory: Content[], promptIds?}` ([610-621](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L610-L621)),
  `SlashCommandRecordPayload {phase, rawCommand, sentToModel?}` ([628-644](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L628-L644)),
  `SessionModelRecordPayload {modelId, authType, baseUrl?}` ([703-708](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L703-L708)),
  `TurnResultRecordPayload {promptId, state, startedAt?, endedAt, promptText?,
  resultText?}` ([949-965](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L949-L965)), `RewindRecordPayload {truncatedCount}` ([837-839](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/chatRecordingService.ts#L837-L839)).

`logs.json` adds `type: 'model_switch'` with `message` = JSON
`ModelSwitchEvent {fromModel, toModel, reason, context?}` ([logger.ts:16-33](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/logger.ts#L16-L33)).
`checkpoint-<tag>.json` is a raw `Content[]` array ([logger.ts:726](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/core/logger.ts#L726)), Gemini's
legacy shape.

## 4. Joins

Session = file = `sessionId` on every record; `cwd` and `gitBranch` on every
record (the lister reads the first record, [sessionService.ts:1184-1197](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/sessionService.ts#L1184-L1197)). Tool
call `message.parts[].functionCall.id` joins `tool_result.toolCallResult.callId`
and `message.parts[].functionResponse.id`. Turns group by `promptId`, the
tree by `parentUuid`, subagents by `isSidechain` and `agentId`, forks by
`forkedFrom`.

## 5. SQLite or binary stores

None; all stores are JSON or JSONL text.

## 6. Format versions

`version` on every record is the CLI version. Managed-engine transcripts
begin with `subtype:'managed_session_header_v1'` (`{formatVersion,
minimumReader, sessionKey, engine:'managed', ...}`,
[`managed-runtime/managed-session-records.ts:220-229`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/managed-runtime/managed-session-records.ts#L220-L229)) followed by
`managed_session_event_v1` and `commit_v1` records ([209-241](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/managed-runtime/managed-session-records.ts#L209-L241)); detector
[`sessionStorageUtils.ts:827`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/utils/sessionStorageUtils.ts#L827),[`920-958`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/utils/sessionStorageUtils.ts#L920-L958). `logs.json` and `checkpoint-*.json`
are the inherited Gemini legacy formats.

## 7. Secrets

`~/.qwen/oauth_creds.json` ([storage.ts:16](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L16); [`qwen/qwenOAuth2.ts:41`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/qwen/qwenOAuth2.ts#L41)),
`mcp-oauth-tokens.json` ([206](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/storage.ts#L206)), `.qwen-extension-git-credentials.json`
([`extension/extension-git-credentials.ts:20`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/extension/extension-git-credentials.ts#L20)). `session_model.systemPayload.baseUrl`
is an endpoint, not a key. `tool_result.toolCallResult.responseParts` and
`message.parts[].functionResponse.response` hold raw tool output;
`UserPromptRecordPayload.hookContext` is hook stdout. Session registry
records contain an `ipcToken` ([`services/session-registry.ts:235`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/services/session-registry.ts#L235)); location
not traced.

## 8. Parser plan

Globs (home-relative): `.qwen/projects/*/chats/*.jsonl`,
`.qwen/projects/*/chats/archive/*.jsonl`, `.qwen/tmp/*/logs.json`. Exclude
`*.runtime.json`, `*.worktree.json` and `*.ledger.jsonl` from transcript
parsing.

Rows: one per record; an assistant record additionally yields a `tool_use`
row per `functionCall` part and a `thinking` row per `thought:true` part.

| Column | Source |
| --- | --- |
| timestamp_utc | `timestamp` |
| session_id | `sessionId` |
| project_path | `cwd` |
| git_branch | `gitBranch` |
| turn_type | user/assistant/tool_result as-is; system → system; functionCall → tool_use; thought part → thinking |
| model | `model` |
| tool_name | `functionCall.name` / `functionResponse.name` |
| tool_use_id | `functionCall.id` / `toolCallResult.callId` |
| text | text parts, `systemPayload.displayText`, `rawCommand`, `toolCallResult.status` plus `errorType` |

Model and permission rows (issues 96 and 97):

- A `session_model` record is the row `model: <modelId> auth=<authType>`,
  or `model: <old> -> <modelId> auth=<authType>` when an earlier record
  of the session named another model (`model` column `modelId`).
- An assistant record's `model` yields `model: <id>` before its rows when
  no earlier `session_model` or assistant record of the session named a
  model, and `model: <old> -> <new>` when it differs from the model in
  force, tracked per `sessionId` with the record's timestamp and line.
- A `logs.json` `model_switch` entry is
  `model: <fromModel> -> <toModel> reason=<reason>` (`model` column
  `toModel`), printed from the entry, not tracked.
- `permission decision: <status>` (`system`, the result's `tool_name` and
  `tool_use_id`) after a `tool_result` row whose `toolCallResult.status`
  is `cancelled` or `awaiting_approval`; the `[<status>]` prefix on the
  result row stays. No other approval record is written to the session
  file.
- `permission setting: trustedFolders.<path>=<value> (from <file>, file
  mtime)` (`system`, `project_path` the folder, no session id, the
  file's modification time, line 1), one per key of
  `~/.qwen/trustedFolders.json`. The file is a JSON object read with
  comments stripped ([`cli/src/config/trustedFolders.ts:162`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/config/trustedFolders.ts#L162))
  and rewritten preserving them ([259](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/config/trustedFolders.ts#L259)); keys are
  folder paths and values a `TrustLevel`: `TRUST_FOLDER`, `TRUST_PARENT`
  or `DO_NOT_TRUST` ([44-48](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/config/trustedFolders.ts#L44-L48),
  [60-61](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/config/trustedFolders.ts#L60-L61)). The value is printed as recorded. A
  file that is not a JSON object is one
  `parser: <file> is not a JSON object` row.

Sync: the inherited Gemini CLI features are covered under `Sync:` in
[section 8 of `gemini-cli.md`](gemini-cli.md#8-parser-plan); Qwen Code
changed them as follows, at the commit in [section 1](#1-source).

- The Clearcut logger and Conseca are gone (neither name occurs in
  `packages/core/src` or `packages/cli/src`). Usage statistics go
  instead to Alibaba Cloud RUM (Real User Monitoring) at
  `gb4w8c3ygj-default-sea.rum.aliyuncs.com`, on by default under
  `privacy.usageStatisticsEnabled`
  ([`core/src/telemetry/qwen-logger/qwen-logger.ts:80`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/qwen-logger/qwen-logger.ts#L80),
  [215-217](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/qwen-logger/qwen-logger.ts#L215-L217);
  [`cli/src/config/settingsSchema.ts:1461-1466`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/config/settingsSchema.ts#L1461-L1466)).
  The prompt event carries its id and length, not its text
  ([qwen-logger.ts:549-556](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/qwen-logger/qwen-logger.ts#L549-L556)),
  user feedback a rating
  ([1044-1053](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/qwen-logger/qwen-logger.ts#L1044-L1053)),
  and error text is replaced by `***REDACTED***` before an event is
  queued ([146-147](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/qwen-logger/qwen-logger.ts#L146-L147),
  [247-262](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/qwen-logger/qwen-logger.ts#L247-L262)).
  OpenTelemetry export is as in Gemini CLI: off by default, prompt text
  in the record when `telemetry.logPrompts` is on
  ([`core/src/config/config.ts:3398-3405`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/config/config.ts#L3398-L3405);
  [`core/src/telemetry/loggers.ts:282-283`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/telemetry/loggers.ts#L282-L283)).
- There is no Code Assist backend and no `/privacy` opt-in;
  `chat.qwen.ai` is used for OAuth only
  ([`core/src/qwen/qwenOAuth2.ts:28-31`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/core/src/qwen/qwenOAuth2.ts#L28-L31)).
- `/export [md|html|json|jsonl] [path]` writes
  `qwen-code-export-<ISO time>.<ext>` to the working directory or the
  path given; it sends nothing
  ([`cli/src/ui/commands/exportCommand.ts:78-100`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/ui/commands/exportCommand.ts#L78-L100),
  [492-500](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/ui/commands/exportCommand.ts#L492-L500);
  [`cli/src/ui/utils/export/utils.ts:10-13`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/ui/utils/export/utils.ts#L10-L13)).
  `/bug` opens a GitHub issue URL and writes no history file
  ([`cli/src/ui/commands/bugCommand.ts:33-47`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/cli/src/ui/commands/bugCommand.ts#L33-L47)).
- New: channels. A session driven by `qwen channel start` is
  conducted on a messaging platform, so its prompts and replies sit on
  that platform's servers as well as in the local transcript. The
  marker is the channel routes file in
  [section 2](#2-transcript-files): an entry names the `sessionId`
  and the platform's `channelName`, `chatId`, `senderId` and
  `threadId`. The parser yields one `system` row per entry, with
  `session_id` the entry's `sessionId` and `project_path` its `cwd`:
  `session relayed: channel <channelName> chat <chatId or -> sender
  <senderId or -> thread <threadId or -> (from channels/sessions.json,
  startedAt)`, at `startedAt` when present and otherwise at the file's
  modification time with the text ending `file mtime)`, and
  `channels/daemon/<hash>/routes.json` named in place of
  `channels/sessions.json` for the daemon form. The row is `session
  relayed:`, not `session synced:`: the copy is on the messaging
  platform, not in a Qwen account, so the parser does not set
  `records_sync`. A file or an entry that is not a JSON object is one
  `parser:` row. Fixture only: no real install has shown either file.
  A clean shutdown deletes
  `sessions.json`, so a session whose entry is gone may still have
  been a channel session; the bot tokens are in the `channels` key of
  `settings.json` or in environment variables it names
  ([`docs/users/features/channels/overview.md:28-36`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/docs/users/features/channels/overview.md#L28-L36),
  [254-258](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/docs/users/features/channels/overview.md#L254-L258)). The sessions that
  remain on the platform are deleted, if at all, on the platform, and
  no local file records that.
- New: the Mem0 external-context extension
  (`integrations/external-context-mem0`, Mem0 being a memory service
  an administrator configures) sends the submitted prompt as a search
  query when its Auto Recall hook is installed, and an opt-in
  `context_remember` tool writes content to that service; both are
  off unless an administrator installs and configures them, and a
  write appears in the transcript only as that tool call. No other
  local marker records it.
- Qwen Live (`packages/qwen-live`, a voice daemon that drives coding
  sessions) keeps its own logs and memory under `~/.qwen-live`
  ([`qwen-live/src/config.ts:867-869`](https://github.com/QwenLM/qwen-code/blob/2c591ecc08a6fa080342f9b1b9f7f43215178cbb/packages/qwen-live/src/config.ts#L867-L869));
  it streams audio to the DashScope realtime model (Alibaba Cloud's
  model API), which is the model API, not sync.

Source review of 2026-10-19, at
[`5dcf7c7`](https://github.com/QwenLM/qwen-code/commit/5dcf7c7cb162e825d95d531081f67ee60da3c0e1),
one line per requirement class. `CRS` below is
[`core/src/services/chatRecordingService.ts`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts)
at that commit.

- Permission, per call (not parsed). A `system` record with subtype
  `ui_telemetry` holds `systemPayload.uiEvent`
  ([CRS 3124-3140](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L3124-L3140);
  written for every telemetry event,
  [`core/src/telemetry/loggers.ts:172-175`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/telemetry/loggers.ts#L172-L175)).
  For a tool call the event has `"event.name": "tool_call"`,
  `call_id`, `function_name`, `function_args`, `status`
  (`success`, `error`, `cancelled`) and `decision`, set only when the
  user was asked: `accept` (allow once), `auto_accept` (any "allow
  always" choice), `modify` (edited first) or `reject`
  ([`core/src/telemetry/types.ts:182-245`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/telemetry/types.ts#L182-L245);
  [`core/src/telemetry/tool-call-decision.ts:9-36`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/telemetry/tool-call-decision.ts#L9-L36)).
  The parser emits the record as `ui_telemetry: <JSON>`. Proposed:
  `permission decision: <decision> (tool_call ui_telemetry)` with
  `tool_name` `function_name` and `tool_use_id` `call_id`, beside the
  call. No separate record of the AUTO classifier's verdict was found
  (`classifier` and `denial` do not occur in `CRS`); a call it blocks
  shows only as the tool result.
- Permission, mode (not parsed). Every user prompt record, and every
  `mid_turn_user_message`, carries `executionContext: {modelId,
  authType?, approvalMode}`
  ([CRS 475-479](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L475-L479),
  [2329-2335](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L2329-L2335),
  [2356-2359](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L2356-L2359),
  [2420-2422](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L2420-L2422)),
  `approvalMode` one of `plan`, `default`, `auto-edit`, `auto`, `yolo`
  ([`core/src/config/approval-mode.ts:7-13`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/config/approval-mode.ts#L7-L13)).
  A daemon session also writes a `session_approval_mode` record,
  `systemPayload {mode, prePlanMode?, planExecutionMode?}`, whenever
  the mode changes
  ([CRS 749-754](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L749-L754),
  [3516-3545](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L3516-L3545)).
  Proposed: `permission setting: approvalMode=<mode>` at a session's
  first user record and `approvalMode=<old> -> <new>` on each change,
  tracked per session as the model is; the `session_approval_mode`
  record read the same way.
- Permission, standing (not parsed). `settings.json` (`~/.qwen/` and
  `<project>/.qwen/`) holds `permissions.allow`, `permissions.ask` and
  `permissions.deny` rule lists and `permissions.autoMode` (the AUTO
  classifier's hints and limits)
  ([`cli/src/config/settingsSchema.ts:2691-2740`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/config/settingsSchema.ts#L2691-L2740)),
  and `tools.approvalMode`, whose default is `auto`
  ([3286-3300](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/config/settingsSchema.ts#L3286-L3300)).
  An "always allow" choice for the project or for the user appends its
  rules to `permissions.allow` of the matching file
  ([`core/src/core/permission-helpers.ts:194-243`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/core/permission-helpers.ts#L194-L243);
  [`cli/src/config/config.ts:2624-2636`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/config/config.ts#L2624-L2636)).
  Proposed: one `permission setting: permissions.<list>=<rule> (from
  <file>, file mtime)` row per rule and one for `tools.approvalMode`.
  `~/.qwen/settings.json` is a secret glob, so a `--no-secrets`
  collection lacks it.
- Model: `executionContext.modelId` (with `authType`) on each user
  record is the model in force when the prompt was sent; proposed as a
  further input to the `model:` tracking above. `session_model`,
  assistant `model` and `logs.json` `model_switch` are covered.
- Past use: `usage_record.jsonl` (secondary, joins on `sessionId`;
  proposed row per record: `session usage: project <project> models
  <ids> tools <name>=<count>... (from usage_record.jsonl)` at
  `startTime`), then `shell_history` and `checkpoint-<tag>.json` as in
  Gemini CLI; the auto-memory directory after a real-install round
  ([section 2](#2-transcript-files)).
- Sync, relay and origin: channels covered. Not reviewed in depth: the
  Qwen Code Desktop app (`packages/desktop`, a Tauri shell, identifier
  `com.alibaba.qwen-code`, that runs `qwen serve` and keeps only
  `desktop-state.json` in its own config directory;
  [`desktop/src-tauri/tauri.conf.json:3-5`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/desktop/src-tauri/tauri.conf.json#L3-L5),
  [`desktop/src-tauri/src/desktop_state.rs:177-182`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/desktop/src-tauri/src/desktop_state.rs#L177-L182)),
  and its Local Control setting that shares the live daemon with a
  phone on the same network
  ([`desktop/README.md:17`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/desktop/README.md#L17)).
  Whether either leaves a local record of a paired device was not
  determined.
- Scratch directories: a record whose `cwd` lies under
  `<project>/.qwen/worktrees/`, or a `.worktree.json` sidecar, should
  yield `scratch directory: <worktreePath> (enter_worktree <slug>)`.
- Deletion: no row; nothing marks a removed session except its
  surviving `usage_record.jsonl` entry and `logs.json` prompts.
- Version drift, record subtypes. `notification` and `cron` records
  (`type: "user"`, `provenance: "system"`,
  [CRS 2655-2690](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L2655-L2690))
  and the new `agent_mention` and `agent_message` records (`type:
  "user"`, `provenance: "external_agent"` unless a user mention, with
  `agentId` and `agentName`; messages from another agent of the same
  workspace,
  [CRS 2541-2585](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L2541-L2585))
  are yielded by the parser as `user` rows, so a scheduled-task trigger
  or another agent's message reads as a prompt the user typed. They
  should be `system` rows naming the subtype (and the agent). New
  `turn_attempt` records and `turn_result.cancelReason`
  ([CRS 998](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L998),
  [3713-3734](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L3713-L3734))
  fall to the generic `system` row. A tool result may carry subtype
  `code_mode_tool_result`
  ([CRS 403](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/core/src/services/chatRecordingService.ts#L403));
  the parser reads it as an ordinary `tool_result`.
- Version drift, `trustedFolders.json`: since the commit first
  reviewed, Qwen reads the file with `parseJsoncObject`, which allows
  trailing commas and strips a byte-order mark
  ([`cli/src/utils/jsonc-editor.ts:24`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/utils/jsonc-editor.ts#L24),
  [92-107](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/utils/jsonc-editor.ts#L92-L107);
  [`cli/src/config/trustedFolders.ts:172-182`](https://github.com/QwenLM/qwen-code/blob/5dcf7c7cb162e825d95d531081f67ee60da3c0e1/packages/cli/src/config/trustedFolders.ts#L172-L182)).
  The shared `trusted_folder_rows` strips comments and calls
  `json.loads`, so a file Qwen accepts can yield only the whole-file
  `parser:` row.
- Bad lines: `usage_record.jsonl` is JSONL and needs `iter_jsonl` and
  `error_rows` when it is parsed.

Fixture:

```json
{"uuid":"0f0e0d0c-3333-4000-8000-000000000010","parentUuid":null,"sessionId":"e5f6a7b8-4444-4000-8000-000000000011","timestamp":"2026-10-01T10:00:00.000Z","type":"user","provenance":"real_user","cwd":"/home/alice/proj","version":"0.24.7","gitBranch":"main","promptId":"e5f6a7b8-4444-4000-8000-000000000011########1","message":{"role":"user","parts":[{"text":"run the tests"}]},"systemPayload":{"displayText":"run the tests","hookContext":""}}
{"uuid":"1a1b1c1d-5555-4000-8000-000000000012","parentUuid":"0f0e0d0c-3333-4000-8000-000000000010","sessionId":"e5f6a7b8-4444-4000-8000-000000000011","timestamp":"2026-10-01T10:00:03.000Z","type":"assistant","provenance":"assistant_output","cwd":"/home/alice/proj","version":"0.24.7","gitBranch":"main","model":"qwen3-coder-plus","message":{"role":"model","parts":[{"text":"Plan: run npm test.","thought":true},{"text":"Running tests."},{"functionCall":{"id":"call_abc123","name":"run_shell_command","args":{"command":"npm test"}}}]},"usageMetadata":{"promptTokenCount":200,"candidatesTokenCount":30,"totalTokenCount":230},"contextWindowSize":131072}
{"uuid":"2b2c2d2e-6666-4000-8000-000000000013","parentUuid":"1a1b1c1d-5555-4000-8000-000000000012","sessionId":"e5f6a7b8-4444-4000-8000-000000000011","timestamp":"2026-10-01T10:00:09.000Z","type":"tool_result","provenance":"tool_result","cwd":"/home/alice/proj","version":"0.24.7","gitBranch":"main","message":{"role":"user","parts":[{"functionResponse":{"id":"call_abc123","name":"run_shell_command","response":{"output":"12 passing"}}}]},"toolCallResult":{"callId":"call_abc123","status":"success","resultDisplay":"12 passing","errorType":null}}
{"uuid":"3c3d3e3f-7777-4000-8000-000000000014","parentUuid":"2b2c2d2e-6666-4000-8000-000000000013","sessionId":"e5f6a7b8-4444-4000-8000-000000000011","timestamp":"2026-10-01T10:00:10.000Z","type":"system","subtype":"custom_title","provenance":"system","cwd":"/home/alice/proj","version":"0.24.7","gitBranch":"main","systemPayload":{"customTitle":"Run tests","titleSource":"auto"}}
```

Confidence. High: record field names, file paths, status values, ISO
timestamps, sidecar names. Medium: `turn_result.startedAt/endedAt` unit
(numbers; inferred milliseconds); `errorType` serialised value. Not
determined: exact `logs.json` `model_switch` serialisation; the session
registry file location holding `ipcToken`; `hookContext` content.
