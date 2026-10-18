# Continue transcript schema

Catalog agent: `continue`. Covers the IDE extensions and the `cn` CLI, which
share [`core/util/history.ts`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts) ([`extensions/cli/src/session.ts:12`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L12),[`50-51`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L50-L51)).
Paths cited are relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/continue.md`](../../collectors/research/continue.md).

## 1. Source

[continuedev/continue](https://github.com/continuedev/continue) at [`5522c6f44ca0ac3528b37244818fbfa39b5af470`](https://github.com/continuedev/continue/commit/5522c6f44ca0ac3528b37244818fbfa39b5af470),
Apache-2.0 ([`LICENSE`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/LICENSE)). Open source.

## 2. Transcript files

`~/.continue`, overridable by `CONTINUE_GLOBAL_DIR`
([`core/util/paths.ts:27-35`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L27-L35)):

- `sessions/<sessionId>.json`: one session, pretty-printed JSON
  ([`paths.ts:102-103`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L102-L103), [`history.ts:131-134`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L131-L134)).
- `sessions/sessions.json`: JSON array of session metadata
  ([`paths.ts:106-112`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L106-L112), [`history.ts:168-181`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L168-L181)).
- `logs/prompt.log`: human-readable LLM interaction log ([`paths.ts:397-399`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L397-L399)),
  written only by the binary used by JetBrains ([`binary/src/index.ts:35-38`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/binary/src/index.ts#L35-L38)),
  not by the VS Code extension.
- `dev_data/0.2.0/<eventName>.jsonl`: one JSON object per line per event
  ([`paths.ts:240-249`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L240-L249), [`core/data/log.ts:20`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L20),[`73-97`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L73-L97)). Events include
  `chatInteraction`, `chatFeedback`, `toolUsage`, `tokensGenerated`,
  `autocomplete`, `editInteraction`, `quickEdit`
  ([`packages/config-yaml/src/schemas/data/`](https://github.com/continuedev/continue/tree/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data)). Legacy `dev_data/0.1.0/*.jsonl`
  and pre-version `dev_data/*.jsonl` ([`paths.ts:441-460`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L441-L460)).
- `dev_data/devdata.sqlite`, table `tokens_generated` ([`paths.ts:236-238`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/paths.ts#L236-L238),
  [`core/data/devdataSqlite.ts:16-20`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/devdataSqlite.ts#L16-L20)).
- `<YYYYMMDDTHHMMSS>_session.md`: a Markdown export written by the `/share`
  slash command ("Export the current chat session to markdown"), or by
  the history page's share button in VS Code, which asks for a destination
  folder first
  ([`core/commands/slash/built-in-legacy/share.ts:7-16`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/commands/slash/built-in-legacy/share.ts#L7-L16);
  [`extensions/vscode/src/commands.ts:383-412`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/vscode/src/commands.ts#L383-L412)).
  The file goes to `~/.continue` unless a folder or `outputDir` is given,
  is named by the host-local export time, and starts
  `### [Continue](https://continue.dev) session transcript` and
  `Exported: <locale time>`, then one `#### _User_` or `#### _Assistant_`
  heading per message with the text as a block quote; it has no session
  id ([`core/util/historyUtils.ts:41-65`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/historyUtils.ts#L41-L65),
  [`67-105`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/historyUtils.ts#L67-L105)).
  Nothing is uploaded: "share" means a local file.
- `logs/cn.log`: the `cn` CLI's log, kept by the winston logging library
  at level `info`, rotated at 10 MB with five files kept
  ([`extensions/cli/src/util/logger.ts:16-31`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/logger.ts#L16-L31),
  [`102-115`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/logger.ts#L102-L115)).
  Each line is `YYYY-MM-DD HH:mm:ss.SSS [<8 hex>] [<level>]: <message>`
  followed by the call's extra fields as one JSON object
  ([`:74-95`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/logger.ts#L74-L95)).
  The time is host-local with no offset, and the eight hex digits are a
  random id per process, not the session id
  ([`:12-13`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/logger.ts#L12-L13)).
  In `cn serve --id <agentId>` mode it holds the only local record of
  what the CLI posted to Continue's agent API (the sync marker, below):
  `[metadata] POST https://api.continue.dev/agents/<agentId>/metadata`
  with `{"agentId":"<agentId>","metadataKeys":[...]}`, then
  `[metadata] Request body` with `{"metadata":{...}}` (the posted fields,
  `summary` text included), then `[metadata] Success: <status>
  (<ms>ms) <url>` or an `Unexpected response`, `Auth required
  (skipping)`, `Failed` or `Error` line
  ([`extensions/cli/src/util/metadata.ts:125-181`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/metadata.ts#L125-L181)).
  The base URL is `CONTINUE_API_BASE` or `https://api.continue.dev/`
  ([`extensions/cli/src/env.ts:9`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/env.ts#L9)).

## 3. Record schema

Session ([`core/index.d.ts`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts)). `Session` [`:279-290`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L279-L290): `sessionId`, `title`,
`workspaceDirectory`, `history: ChatHistoryItem[]`, `mode?:
"chat"|"agent"|"plan"|"background"`, `chatModelTitle?`, `usage?: SessionUsage`
(`promptTokens`, `completionTokens`, `totalCost`, [`:275-277`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L275-L277),[`407-422`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L407-L422)). Key
order is forced ([`history.ts:115-129`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L115-L129)).

`ChatHistoryItem` [`:534-545`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L534-L545): `message: ChatMessage`, `contextItems:
ContextItemWithId[]` (`content, name, description, uri?{type,value},
id{providerTitle,itemId}` [`:459-473`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L459-L473)), `editorState?`, `promptLogs?:
PromptLog[]` (`modelTitle, modelProvider, prompt, completion`, [`:488-493`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L488-L493)),
`toolCallStates?: ToolCallState[]`, `reasoning?: {active, text, startAt:
number (ms epoch), endAt?}` ([`:527-532`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L527-L532); [`gui/src/redux/slices/sessionSlice.ts:561`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/gui/src/redux/slices/sessionSlice.ts#L561)),
`conversationSummary?`, `appliedRules?`.

`ChatMessage` [`:440-445`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L440-L445) by `role` ([`:335-340`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L335-L340)): `user` `{content: string |
{type:"text",text}|{type:"imageUrl",imageUrl:{url}}[]}`; `assistant`
`{content, toolCalls?: [{id?, type?:"function", function?:{name?, arguments?:
string (JSON)}}], usage?}`; `thinking` `{content, signature?,
redactedThinking?, reasoning_details?}`; `system` `{content}`; `tool`
`{content, toolCallId}`. All may carry `metadata?`.

`ToolCallState` [`:516-525`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L516-L525): `toolCallId`, `toolCall: {id, type:"function",
function:{name, arguments}}`, `status: "generating"|"generated"|"calling"|
"errored"|"done"|"canceled"`, `parsedArgs`, `processedArgs?`, `output?:
ContextItem[]` (tool result text in `content`).

No per-message timestamp exists in session files. `sessions.json` entry
(`BaseSessionMetadata` [`:292-298`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/index.d.ts#L292-L298)): `sessionId`, `title`, `dateCreated`
(`String(Date.now())`, millisecond epoch as a string, [`history.ts:171`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L171)),
`workspaceDirectory`, `messageCount?` (assistant messages only, [`:154-156`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L154-L156)).
The CLI drops `system` messages before saving and copies user content into
`editorState` ([`extensions/cli/src/session.ts:211-231`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L211-L231)).

`dev_data/0.2.0/chatInteraction.jsonl` ([`schemas/data/chatInteraction/v0.2.0.ts`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data/chatInteraction/v0.2.0.ts),
[`index.ts:4-19`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data/chatInteraction/index.ts#L4-L19), [`base.ts:3-11`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data/base.ts#L3-L11)): `eventName`, `schema`, `timestamp` (ISO
8601, [`log.ts:50`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L50)), `userId`, `userAgent`, `selectedProfileId`, `prompt`,
`completion`, `modelName`, `modelTitle`, `modelProvider`, `sessionId`,
`tools?`, `rules?`. `toolUsage.jsonl` ([`toolUsage/v0.2.0.ts:13-19`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data/toolUsage/v0.2.0.ts#L13-L19)):
`toolCallId`, `functionName`, `functionParams`, `toolCallArgs`, `accepted`,
`succeeded`, `output`. `chatFeedback` adds `feedback`.

`prompt.log` ([`core/llm/logFormatter.ts:43-75`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/llm/logFormatter.ts#L43-L75)): `HH:MM:SS.s [Chat]` (UTC,
[`:29-41`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/llm/logFormatter.ts#L29-L41)), `Options: {json}`, `Role: user`, text lines prefixed `| `,
relative `+N.N` deltas, `Success`, `PromptTokens: N`; overlapping
interactions get a column prefix character from `" |&%#"` ([`:19`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/llm/logFormatter.ts#L19)). No date,
no session id.

## 4. Joins

`sessions.json[].sessionId` with `sessions/<sessionId>.json`;
`workspaceDirectory` is in both. Tool call with result:
`assistant.toolCalls[].id` = `toolCallStates[].toolCallId` = the next `tool`
message's `toolCallId`. `chatInteraction.sessionId` joins the session file;
`toolUsage.toolCallId` joins `toolCallStates[].toolCallId`. No git branch is
recorded.

## 5. SQLite stores

`dev_data/devdata.sqlite` `tokens_generated(model, provider, tokens_prompt,
tokens_generated, timestamp)` ([`devdataSqlite.ts:16-49`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/devdataSqlite.ts#L16-L49)). Excluded by the
collector as low value.

## 6. Format versions

`sessions.json` entries with `session_id` are an old format and are filtered
([`history.ts:34-36`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L34-L36)); `dev_data` schema `0.1.0` became `0.2.0`; no version
field inside session files.

## 7. Secrets

`promptLogs[].prompt` and `dev_data/*/chatInteraction.jsonl` `prompt` embed
full context, possibly `.env` contents. `dev_data` `userId` is the Continue
hub `userToken` ([`log.ts:64-66`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L64-L66)). Session files hold no API keys; the
collector flags `config.yaml`, `config.json` and `index/globalContext.json`.
A `data:` block in `config.yaml` can carry an `apiKey` that the extension
sends as a bearer token to the block's `destination`
([`packages/config-yaml/src/schemas/data/index.ts:71-81`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/data/index.ts#L71-L81),
[`core/data/log.ts:192-194`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L192-L194)); `config.yaml`
is already flagged. The CLI still names `auth.json` for a Continue Hub
(Continue's hosted account and configuration service) sign-in
([`extensions/cli/src/auth/authEnv.ts:5`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/auth/authEnv.ts#L5)),
but at this commit Hub sign-in is a stub that never saves
([`extensions/cli/src/auth/workos.ts:1-7`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/auth/workos.ts#L1-L7),
[`86-88`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/auth/workos.ts#L86-L88));
an older `cn` may have left one, and `.continue/auth*.json` is a secret
glob.

## 8. Parser plan

Globs: `.continue/sessions/*.json` (skip `sessions.json` itself, but read it
for `dateCreated`), `.continue/dev_data/*/chatInteraction.jsonl`,
`.continue/dev_data/*/toolUsage.jsonl`.

Rows: one per `history[]` item (user, assistant, thinking, tool), plus one
`tool_use` per `toolCalls[]`.

| Column | Source |
| --- | --- |
| timestamp_utc | `sessions.json` `dateCreated` (session level; message rows inherit); `reasoning.startAt` if present |
| session_id | `sessionId` |
| project_path | `workspaceDirectory` |
| git_branch | empty |
| turn_type | by `message.role`; `thinking` → thinking; `tool` → tool_result |
| model | `chatModelTitle` or `promptLogs[].modelTitle` |
| tool_name, tool_use_id | `toolCall.function.name`, `toolCallId` |
| text | text, `function.arguments`, output `content` |

Model rows, typed `system`: `model: <chatModelTitle>` right after the
session row, and `model: <old> -> <new>` ahead of a `history[]` item whose
`promptLogs[].modelTitle` differs from the model before it. When
`chatModelTitle` is missing (or lost after a cut in a truncated file), the
first `modelTitle` starts the session. Mid-session switching is not
researched: the session format has no switch record, so a change shows
only as a different `modelTitle` between items, and `chatModelTitle` is
one value per file with no record of when it was set. The CLI's
`permissions.yaml` is named in
[`collectors/research/continue.md`](../../collectors/research/continue.md)
but its shape is not recorded, so the parser does not read it.

Per-call decision rows, typed `system`:

- `toolUsage.jsonl` `accepted` yields `permission decision:
  accepted=<accepted>` after the record's `tool_result` row, with its
  `timestamp`, `toolCallId` and `functionName`; the result row keeps its
  `accepted=` and `succeeded=` text.
- A `ToolCallState` whose `status` is `canceled` yields `permission
  decision: canceled` with the call's `toolCallId` and function name,
  after the state's `tool_result` row when there is one, at the session
  time.

Sync: only the hidden `cn serve --id <agentId>` mode sends session
content to Continue, and the only local trace is in `logs/cn.log`
([section 2](#2-transcript-files)). `cn serve` is an HTTP front end
(`/state`, `/message`, `/permission`, `/exit`) that Continue's hosted
agents drive; `--id` is described as "Upload session snapshots to
Continue-managed storage" ([`extensions/cli/src/index.ts:310-326`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/index.ts#L310-L326)).
With an id, after every agent turn and at exit, the CLI posts to
`agents/<agentId>/metadata` the last assistant message cut to 500
characters (`summary`), the `git diff main` line counts (`additions`,
`deletions`), token usage and `isComplete`/`hasChanges`
([`extensions/cli/src/commands/serve.ts:487-494`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/serve.ts#L487-L494);
[`extensions/cli/src/util/exit.ts:97-135`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/exit.ts#L97-L135);
[`extensions/cli/src/util/metadata.ts:70-116`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/metadata.ts#L70-L116)),
and an unhandled error posts `status: "FAILED"` to `agents/<agentId>/status`
([`extensions/cli/src/index.ts:98-115`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/index.ts#L98-L115)). The requests carry no
credential at this commit ([`extensions/cli/src/util/apiClient.ts:58-83`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/util/apiClient.ts#L58-L83)).
The snapshot upload itself (the full state as JSON and the `git diff main`
text, PUT every 30 seconds to presigned storage URLs from
`agents/storage/presigned-url`,
[`extensions/cli/src/services/StorageSyncService.ts:221-264`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/services/StorageSyncService.ts#L221-L264),
[`359-414`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/services/StorageSyncService.ts#L359-L414)) never
starts, because `serve` passes `accessToken: null` and the service then
logs `Storage sync requested but no Continue API key is available;
skipping uploads.` ([`extensions/cli/src/commands/serve.ts:185-198`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/commands/serve.ts#L185-L198);
[`extensions/cli/src/services/StorageSyncService.ts:85-90`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/services/StorageSyncService.ts#L85-L90)). The
session file and `sessions.json` record no agent id: the `isRemote` and
`remoteId` fields of the CLI's session list exist only in memory, are
always `false` and absent for local sessions, and remote sessions are a
stub returning none ("Hub integration removed",
[`extensions/cli/src/session.ts:21-26`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L21-L26),
[`441-446`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/session.ts#L441-L446)). Planned form: one `system`
row per `[metadata] POST` line, `session synced: agent <agentId> metadata
posted (<metadataKeys>) <status from the following Success, Failed or
Error line> (from logs/cn.log, log line time)`, timestamped by the line's
own time read as host-local, with `session_id` empty since the log names
no session; a `Storage sync requested` warning line yields `session
synced: storage upload requested, skipped (from logs/cn.log, log line
time)`. The parser does not read `cn.log` today. Deleting a session
(`history/delete`) removes the session file and its `sessions.json` entry
only ([`core/util/history.ts:60-75`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/util/history.ts#L60-L75)); `cn.log`, the
`dev_data` lines carrying its `sessionId` and any `/share` export
survive, and no command deletes the remote copy. The other paths that
leave the host carry no transcript and leave no per-session marker:
`/share` writes a local Markdown file ([section 2](#2-transcript-files));
`dev_data` events go to remote destinations only when a `data:` block in
`config.yaml` names an `http` or `https` `destination` (opt-in, no
default block), posted as `{name, data, schema, level, profileId}` with
the prompt and completion at level `all`, and nothing local records the
post beyond a console error on failure
([`core/data/log.ts:104-117`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L104-L117), [`184-236`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/data/log.ts#L184-L236));
the CLI's OpenTelemetry metrics (counts, cost, lines changed) export only
when an `OTEL_EXPORTER_OTLP_*` or `OTEL_METRICS_EXPORTER` variable is set
([`extensions/cli/src/telemetry/telemetryService.ts:69-84`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/extensions/cli/src/telemetry/telemetryService.ts#L69-L84)); and the
extension core has no PostHog or other product analytics client at this
commit (`allowAnonymousTelemetry` survives only as a shared-config flag,
[`core/config/sharedConfig.ts:48-55`](https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/sharedConfig.ts#L48-L55)). Searched `share`, `sync`,
`upload`, `remote`, `remoteId`, `storage`, `telemetry`, `posthog`,
`agents/`, `api.continue.dev` and `userToken` in `core/`, `gui/src`,
`extensions/vscode/src` and `extensions/cli/src`.

Fixture `sessions/0f1e.json`:

```json
{"sessionId":"0f1e","title":"Fix bug","workspaceDirectory":"/home/u/proj","history":[
 {"message":{"role":"user","content":"rename foo"},"contextItems":[]},
 {"message":{"role":"assistant","content":"","toolCalls":[{"id":"call_1","type":"function","function":{"name":"edit_existing_file","arguments":"{\"filepath\":\"a.py\"}"}}]},"contextItems":[],
  "toolCallStates":[{"toolCallId":"call_1","toolCall":{"id":"call_1","type":"function","function":{"name":"edit_existing_file","arguments":"{\"filepath\":\"a.py\"}"}},"status":"done","parsedArgs":{"filepath":"a.py"},"output":[{"name":"Edit","description":"","content":"ok"}]}]},
 {"message":{"role":"tool","content":"ok","toolCallId":"call_1"},"contextItems":[]}],"chatModelTitle":"GPT-4o"}
```

`sessions.json`: `[{"sessionId":"0f1e","title":"Fix bug","dateCreated":"1759400000000","workspaceDirectory":"/home/u/proj","messageCount":1}]`

`dev_data/0.2.0/chatInteraction.jsonl`: `{"eventName":"chatInteraction","schema":"0.2.0","timestamp":"2026-10-02T10:00:00.000Z","userId":"","userAgent":"vscode/1.1 (Continue/1.0)","selectedProfileId":"local","prompt":"rename foo","completion":"done","modelName":"gpt-4o","modelTitle":"GPT-4o","modelProvider":"openai","sessionId":"0f1e"}`

Confidence. High: session, `sessions.json` and `dev_data` schemas (typed
source). Medium: `prompt.log` format (from a doc comment; only the JetBrains
binary writes it). Not determined: per-message timestamps (absent by
design).
