# Twinny transcript schema

Catalog agent: `twinny`. A VS Code extension; its chats live inside the
editor's own SQLite state database, not in a file of its own. Paths are in
[`collectors/research/twinny.md`](../../collectors/research/twinny.md).

## 1. Source

[twinnydotdev/twinny](https://github.com/twinnydotdev/twinny) at [`9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6`](https://github.com/twinnydotdev/twinny/commit/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6),
MIT, open source. VS Code storage behaviour from [microsoft/vscode](https://github.com/microsoft/vscode) at the
commit cited in [vscode.md](vscode.md). Sync was checked at
[`0337b26`](https://github.com/twinnydotdev/twinny/commit/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a)
(version 4.3.15, [package.json:5](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/package.json#L5)) on 2026-10-17.

## 2. Transcript stores

- `<editor User dir>/globalStorage/state.vscdb`, `ItemTable` row whose `key`
  is `rjmacarthy.twinny`. Its `value` is one JSON object holding every
  `globalState` key of the extension
  ([extHostMemento.ts:118](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/api/common/extHostMemento.ts#L118);
  [extensionStorage.ts:159-176](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/extensionManagement/common/extensionStorage.ts#L159-L176)).
  Inside it, `twinny.conversations` is an object of conversations keyed by
  id, and `twinny.active-conversation` a copy of the open one
  ([src/common/constants/storage.ts:1](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L1), [6](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L6);
  [src/extension/chat/conversation-history.ts:80-104](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/conversation-history.ts#L80-L104)).
  Home-relative globs: `.config/*/User/globalStorage/state.vscdb`,
  `Library/Application Support/*/User/globalStorage/state.vscdb`,
  `AppData/Roaming/*/User/globalStorage/state.vscdb`,
  `.*-server*/data/User/globalStorage/state.vscdb`, all collected as agent
  `vscode`.
- Optional `twinny-server` recordings (`~/.twinny/server/recordings/`), off by
  default, cover requests from every team member; see [section 5](#5-sqlite-and-other-stores).

One row holds all conversations; deleting a conversation removes it from the
object ([conversation-history.ts:150-156](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/conversation-history.ts#L150-L156)), and
"clear all" writes `{}` ([:167-170](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/conversation-history.ts#L167-L170)).

## 3. Record schema

`Conversation` ([src/common/types.ts:127-135](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L127-L135)): `id` (uuid v4,
[src/webview/chat.tsx:494](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/webview/chat.tsx#L494)), `title`, `messages[]`, `pinnedTitle?`,
`updatedAt?` (Unix ms, set on every save,
[conversation-history.ts:97](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/conversation-history.ts#L97)).

`messages[]` are `ChatCompletionMessage`: the OpenAI-style
`ChatCompletionMessageParam` from `fluency.js` (`role`, `content`) plus
Twinny fields ([types.ts:50-76](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L50-L76)):

- `role`: `user` or `assistant` ([src/common/constants/misc.ts:8-11](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/misc.ts#L8-L11);
  user turns [chat.tsx:496-503](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/webview/chat.tsx#L496-L503), replies
  [src/extension/chat/generation.ts:151-157](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/generation.ts#L151-L157)). The system prompt sits
  only in the extension's in-memory turn list ([src/extension/chat/index.ts:192-195](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/index.ts#L192-L195));
  saves come from the webview's message list
  ([src/webview/hooks/useConversationHistory.ts:44](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/webview/hooks/useConversationHistory.ts#L44)).
- `content`: string. Reasoning models' output stays inline as
  `<think>...</think>` or `<thinking>...</thinking>`; the UI splits it
  ([src/webview/utils.ts:116-121](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/webview/utils.ts#L116-L121)).
- `id?`, `images?`, `prompt?` (what was actually sent when the UI shows a
  shorter text), `context?` (workspace search hits used),
  `toolNotes?` (tool inputs and outputs carried to the next turn).
- `meta?` `ReplyMeta` ([types.ts:104-125](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L104-L125)): `model`, `provider`,
  `durationMs`, `completionTokens`, `promptTokens`, `contextWindow`,
  `stopped`, `withheld[]` (counts of credentials the secret shield masked).
- `toolSteps?[]` `ToolStepView` ([types.ts:79-101](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L79-L101)): `id`, `name`,
  `summary`, `args` (string map), `output`, `status`
  (`running|waiting|done|failed|skipped|stopped`), `command`, `approval`.

There is no per-message timestamp; only the conversation's `updatedAt`.

## 4. Joins

Conversation `id` is the session. Tool steps are embedded in the assistant
message that used them, so there is no call/result join. No project path is
stored with a conversation; Twinny's per-workspace state is in
`workspaceStorage/<id>/state.vscdb` under the same key (`contextItems`,
`chatMessage`, [storage.ts:35-47](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L35-L47)), and `workspace.json` beside it
names the folder. The conversation list itself is global.

## 5. SQLite and other stores

`state.vscdb` is VS Code's SQLite `ItemTable(key, value)`; open through
`sqlite_util` so `-wal` is applied. The value is UTF-8 JSON text. VS Code
warns above 512 KB per extension ([extensionStorage.ts:47](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/extensionManagement/common/extensionStorage.ts#L47), [163-165](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/extensionManagement/common/extensionStorage.ts#L163-L165)),
so long histories are common in that one row.

`twinny-server` recordings, when enabled: SQLite `recordings.sqlite` (WAL)
with `recordings(id, ts, at, key, route, alias, model, provider, outcome,
ended, ms, prompt_tokens, completion_tokens, request, response, preview,
thread)`, or JSONL day files with the same `RecordingRecord` fields
([src/gateway/recording/store.ts:25-50](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L25-L50), [336-355](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L336-L355), [369-370](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L369-L370), [207-211](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L207-L211)).
`id` is `<ms, zero-padded to 14>-<hex>` ([:99-100](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/gateway/recording/store.ts#L99-L100)); `key` is
the client key's name, which attributes the request to a team member.

## 6. Format versions

No version field on conversations. `updatedAt` is absent on conversations
from older builds ([types.ts:133-134](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L133-L134)); `contextItems` was previously
`contextFiles` ([storage.ts:38](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/constants/storage.ts#L38)).

## 7. Secrets in the store

The same `rjmacarthy.twinny` JSON holds `twinny.inference-providers` and the
`twinny.active-*-provider` objects, each with `apiKey`
([types.ts:255-272](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L255-L272)). Redact `apiKey` wherever it appears in the
value. Gateway tokens and P2P seeds are separate encrypted `secret://` rows.

## 8. Parser plan

Select `state.vscdb` (and `-wal`) under any `User/globalStorage/`, read the
row `key = 'rjmacarthy.twinny'`, parse JSON, iterate
`twinny.conversations`. Attribute rows to `twinny`, not `vscode`.

| Column | Source |
| --- | --- |
| timestamp_utc | `updatedAt` (ms) on the last message of the conversation only; empty for the rest |
| session_id | conversation `id` |
| project_path | empty |
| git_branch | empty |
| turn_type | `role`; `<think>` block → thinking; each `toolSteps[]` → tool_use plus tool_result |
| model | `meta.model` (assistant) |
| tool_name, tool_use_id | `toolSteps[].name`, `toolSteps[].id` |
| text | `content` with think block removed; tool_use: `command` or `args` JSON; tool_result: `output` |
| source_line | empty (one SQLite row) |

Model and permission rows, all `system` (issues 96 and 97):

- `model: <id>` at the first assistant message of a conversation whose
  `meta.model` is set and `model: <old> -> <new>` on every later
  assistant message with a different one, before that message's rows.
  The model is recorded per reply, so a change inside a conversation
  shows.
- `permission decision: <status>`, with ` approval=<approval>` when the
  step records it, after the `tool_result` row of a `toolSteps[]` entry
  whose `status` is `waiting` or `skipped`, with the step's `id` and
  `name`. `approval` (`command` or `change`) is what the user is asked
  to approve, not the answer
  ([types.ts:87-92](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/common/types.ts#L87-L92)).
  A step that asks sets `status` `waiting` with `command` and `approval`;
  the user's Run or Skip returns it to `running` and clears both, a Skip
  (or a stop that answers every waiting step with Skip) records the step
  as skipped, and `finish` then saves it as `status` `skipped`; a step
  still running or waiting when the reply ends is saved `stopped`
  ([src/extension/chat/tool-steps.ts:76-93](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/tool-steps.ts#L76-L93),
  [131-176](https://github.com/twinnydotdev/twinny/blob/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6/src/extension/chat/tool-steps.ts#L131-L176)).
  So `waiting` is a prompt saved before it was answered, `skipped` is a
  step the user (or a stop) did not let run, and an approved step is
  indistinguishable from one that needed no approval: both end `done` or
  `failed`. A `stopped` step may or may not have been waiting, so it
  gets no decision row.
- `node/trusted-peers.json`, the `twinny-node` trusted-peer list named in
  [`collectors/research/twinny.md`](../../collectors/research/twinny.md),
  is not read: its shape is not recorded.

Sync: Twinny records no sync state. Conversations are written and
deleted only in the extension's `globalState`
([conversation-history.ts:100-110](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/conversation-history.ts#L100-L110),
[158-178](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/conversation-history.ts#L158-L178)),
and the extension never calls `setKeysForSync`, the call that would let
VS Code's Settings Sync (the editor's own upload of settings and
extension state to the user's Microsoft or GitHub account) carry a
`globalState` key to other devices
([vscode.d.ts:8445-8457](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vscode-dts/vscode.d.ts#L8445-L8457);
[extHostMemento.ts:113-114](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/api/common/extHostMemento.ts#L113-L114));
the P2P host says so in its own words, "global state is not synced"
([src/extension/p2p/host.ts:5-8](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/p2p/host.ts#L5-L8)).
The features whose names suggest sharing move compute, not chats:
team share and P2P (peer-to-peer) hosting lend this machine's local
model server to a team gateway or to paired devices
([src/extension/team/share.ts:1-9](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/team/share.ts#L1-L9);
[src/extension/team/sharer.ts:1-9](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/team/sharer.ts#L1-L9);
[host.ts:1-3](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/p2p/host.ts#L1-L3)), and their state
keys `twinny.teamShare`, `twinny.teamPluginsSeen` and `twinny.teamNudge`
hold the share switch and server, the plugin ids already announced and a
first-run notice flag
([src/common/constants/storage.ts:18-23](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/constants/storage.ts#L18-L23)).
The OpenAI Responses adapters, including the ChatGPT plan sign-in,
send `store: false`, so the provider keeps no server-side conversation
([src/extension/inference/adapters/openai-responses.ts:54](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/inference/adapters/openai-responses.ts#L54);
[src/extension/inference/adapters/chatgpt-plan.ts:192](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/inference/adapters/chatgpt-plan.ts#L192)).
Searched `sync`, `upload`, `share`, `publish`, `export`, `telemetry`,
`analytics`, `sentry`, `posthog`, `record` and `CONVERSATION_STORAGE_KEY`
in `src/extension`, `src/common` and `src/webview`; no telemetry client
was found. The one server copy is the team's own: when chat runs
through a `twinny-server` gateway, the request is the model call, and
the gateway keeps it only if its administrator turns on recording
(`recording.chat`, default `false`, and only with the licence's
`recording` feature,
[src/gateway/config.ts:147-148](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/gateway/config.ts#L147-L148),
[216-223](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/gateway/config.ts#L216-L223)), grouped by a `thread`
id the gateway derives from the key name and the first user message,
not one the extension sends
([src/gateway/recording/store.ts:125-135](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/gateway/recording/store.ts#L125-L135)).
The extension sends only the workspace name in `X-Twinny-Workspace`
([src/protocol/client.ts:83](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/protocol/client.ts#L83),
[252](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/protocol/client.ts#L252)), and nothing on the developer's
machine says a request was recorded, so the parser yields no sync row;
the gateway host's `recordings/` directory is the place to look
([section 5](#5-sqlite-and-other-stores)).

Fixture, the `value` of the `rjmacarthy.twinny` row:

```json
{"twinny.conversations":{"7d1c2b3a-1111-4000-8000-000000000001":{"id":"7d1c2b3a-1111-4000-8000-000000000001","title":"List the tests","updatedAt":1759999205000,"messages":[{"role":"user","content":"which tests fail?"},{"role":"assistant","content":"<think>run the suite</think>Two tests fail.","meta":{"model":"qwen2.5-coder:7b","provider":"Ollama","durationMs":5200},"toolSteps":[{"id":"step-1","name":"run_command","summary":"ran `npm test`","args":{"command":"npm test"},"output":"2 failing","status":"done"}]}]}},"twinny.active-conversation":{"id":"7d1c2b3a-1111-4000-8000-000000000001"},"twinny.inference-providers":{"p1":{"id":"p1","label":"Ollama","provider":"ollama","type":"chat","modelName":"qwen2.5-coder:7b","apiHostname":"localhost","apiPort":11434,"apiKey":"REDACTME"}}}
```

Confidence. High: row key, globalState key names, Conversation and message
fields, roles, `updatedAt` unit (all source). Medium: `content` is always a
string in saved chats (the `fluency.js` type also allows part arrays; Twinny
writes strings at the cited sites). Not determined: how `toolSteps[].args`
names the command for each tool; whether other editors running the
extension (VSCodium, Cursor) store it identically (they share the VS Code
storage code, so likely).
