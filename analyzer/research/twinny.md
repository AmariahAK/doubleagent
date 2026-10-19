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

- **Source review (2026-10-19)**: [twinnydotdev/twinny](https://github.com/twinnydotdev/twinny) at
  [`0337b26`](https://github.com/twinnydotdev/twinny/commit/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a)
  (version 4.3.15, today's HEAD, committed 2026-10-16), against
  [`9339bd1`](https://github.com/twinnydotdev/twinny/commit/9339bd108e60781ec4d693fbec3f0bc7a0d7d3e6)
  (4.3.5), which most citations below still name; VS Code's extension
  storage and log-channel paths from
  [microsoft/vscode](https://github.com/microsoft/vscode) at
  [`4d22f4f`](https://github.com/microsoft/vscode/commit/4d22f4f922eb012217ac65672ccce02f59d63706).
  Between the two Twinny commits 160 files changed; every key and field
  the parser reads is still written at HEAD.
  - Permission state: found. The standing grants `alwaysRunCommands`,
    `alwaysRunMcpTools` and `autoRunCommands` and the `agentMode` switch
    are kept in the same `rjmacarthy.twinny` row the parser reads, and
    the `twinny.chatTools*` settings in `settings.json`
    ([section 8](#8-parser-plan)); the parser reads none of them. The
    per-call `waiting` and `skipped` steps are already covered.
  - Model: already covered for `meta.model` per reply; found that it is
    the configured model name, not one the server reports, and that a
    team-pool reply's `meta.provider` names the teammate's machine.
  - Past use beyond the primary store: found. The per-reply file-change
    records under the workspace's `agent-changes/` directory and the
    Twinny log channel ([section 2](#2-transcript-stores)).
  - Sync, relay and origin: already covered (checked at this commit on
    2026-10-17); nothing new.
  - Scratch directories: none; agent mode works in the first workspace
    folder.
  - Deletion: already covered; found that a delete leaves the
    `agent-changes/` records and the log lines.
  - Version drift: found. New message and step fields (`changes`,
    `toolSteps[].said`, `mcpTool`, `noAlways`, `meta.outOfSteps`,
    `meta.instructions`); a `said` step, a user message sent mid-reply,
    is emitted by the parser as a `tool_use` row.
  - Bad lines: no line-oriented file is read today; the two new sources
    would need `error_rows` if parsed.

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

- Per-reply file-change records (secondary, new since 4.3.5): when agent
  mode changes files, the extension keeps one JSON file per reply under
  the workspace's extension storage, `agent-changes/<uuid>.json`
  ([src/extension/chat/index.ts:210-221](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L210-L221);
  [src/extension/chat/reply-changes.ts:211-228](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L211-L228)).
  The extension's workspace storage is
  `<User dir>/workspaceStorage/<id>/rjmacarthy.twinny/`, and the global
  `globalStorage/rjmacarthy.twinny/` when no folder is open
  ([extHostStoragePaths.ts:82-91](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/api/common/extHostStoragePaths.ts#L82-L91)).
  A record is `{id, root, createdAt, files[]}`, each file
  `{path, status, added, removed, undone?, noUndo?, before, afterHash}`
  ([reply-changes.ts:35-47](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L35-L47)):
  `root` is the absolute workspace root, `createdAt` epoch ms at the end
  of the reply, `status` `modified`, `created` or `deleted`, `before` the
  whole file text before the reply (files up to 1 MiB, text only,
  [`:25-26`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L25-L26)) and
  `undone` set when the user put it back
  ([`:238-245`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L238-L245)).
  The newest 50 records are kept and older ones deleted by modification
  time ([`:28`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L28),
  [`:247-259`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/reply-changes.ts#L247-L259)). A
  record joins its conversation through the assistant message's
  `changes.id` ([src/common/types.ts:76-101](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/types.ts#L76-L101)), and survives the
  conversation's deletion and "clear all", which touch only
  `globalState`. It is the only Twinny record that names the project
  path.
- The **Twinny** log channel (secondary, line-oriented): a VS Code log
  output channel ([src/common/logger.ts:93-97](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/logger.ts#L93-L97)), which VS Code
  writes to `<extension host logs>/rjmacarthy.twinny/Twinny.log`
  ([extHostOutput.ts:148-150](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/api/common/extHostOutput.ts#L148-L150))
  under the editor's `logs/` directory, collected as agent `vscode`.
  With `twinny.enableLogging` on (the default,
  [package.json:633-638](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/package.json#L633-L638)) each chat request
  is one line `Chat → <model> (<provider label>) · <n> messages, <n>
  chars` and each reply one line with its duration
  ([src/extension/chat/generation.ts:188-207](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/generation.ts#L188-L207),
  [`:150-153`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/generation.ts#L150-L153)); at the
  channel's Debug level the messages and the reply are written in full
  as blocks ([logger.ts:140-144](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/logger.ts#L140-L144)), after the secret shield's
  redaction. A line joins its conversation by time and text only (no
  conversation id) and survives the conversation's deletion until VS Code
  removes the log session.

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

Fields added between 4.3.5 and 4.3.15 ([types.ts:76-165](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/types.ts#L76-L165) at HEAD):
`changes` on an assistant message (`{id, files[{path, status, added,
removed, undone?, noUndo?}]}`, the view of the record in
[section 2](#2-transcript-stores)); `toolSteps[].said` (`true` on a step
whose `name` is `said` and whose `summary` is a message the user typed
while the reply ran,
[`src/extension/chat/tool-steps.ts:101-104`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/tool-steps.ts#L101-L104));
`toolSteps[].mcpTool` (`server/tool`, a call to a tool of an MCP server,
Model Context Protocol, the standard by which an external program offers
tools to a model) and `noAlways` (the team gateway asks for every
command), both cleared when the step finishes
([`:79-97`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/tool-steps.ts#L79-L97)); `meta.outOfSteps` (the reply used every tool
step `twinny.chatToolsMaxSteps` allows) and `meta.instructions`
(relative paths of the `AGENTS.md` files agent mode followed).

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

Requirement classes, from the source review of 2026-10-19 at
[`0337b26`](https://github.com/twinnydotdev/twinny/commit/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a):

- Permission, standing grants (gap, not parsed). In the same
  `rjmacarthy.twinny` value, under keys prefixed `twinny-global-context-`
  (the prefix the webview gives every global value): `alwaysRunCommands`
  (array of normalised commands the user chose Always run for),
  `alwaysRunMcpTools` (array of `server/tool` names), `autoRunCommands`
  (boolean, the composer's auto-run switch: every command runs unasked)
  and `agentMode` (boolean, tools on)
  ([src/common/constants/storage.ts:25-35](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/constants/storage.ts#L25-L35);
  [src/extension/chat/index.ts:162-192](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L162-L192),
  [`:466-491`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L466-L491)). The
  command `twinny.forgetAlwaysRunCommands` clears the first list
  ([src/index.ts:517-526](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/index.ts#L517-L526)). Until the
  switches are first used, the editor settings `twinny.chatTools`
  (boolean), `twinny.chatToolsCommands` (`ask`, `allow`, `off`) and
  `twinny.chatToolsEdits` (`apply`, `review`) decide
  ([package.json:645-683](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/package.json#L645-L683)); those are in
  `settings.json`, which the `vscode` parser owns. The plan is a row per
  entry, `permission setting: <key>=<value> (from state.vscdb
  rjmacarthy.twinny, file mtime)`. An Always run choice leaves no mark on
  the step itself, which ends `done` like any other
  ([tool-steps.ts:169-176](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/tool-steps.ts#L169-L176)),
  so the list is the only record of it. A team gateway's agent policy
  (commands asked or off, blocked paths) is held in memory only
  ([src/common/team-policy.ts:79-89](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/common/team-policy.ts#L79-L89)).
- Model: covered by the `model:` rows from `meta.model`. That value is
  the provider entry's configured `modelName`, set before the request
  ([generation.ts:112](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/generation.ts#L112)), not a model the server
  reports, and `meta.provider` is overwritten with the backend's name
  when a team gateway routes the request
  ([`:123-126`](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/generation.ts#L123-L126)), so for
  a team pool it names the teammate's machine that answered. The current
  selection is also kept as `twinny-global-context-twinny.selectedModel`
  and in `twinny.active-chat-provider`
  ([src/extension/providers/store.ts:92-100](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/providers/store.ts#L92-L100));
  neither is history.
- Past use: the `agent-changes/` records (secondary for the reply they
  belong to, but the only source of its file changes and project path)
  and the log channel (secondary, line-oriented), both in
  [section 2](#2-transcript-stores); neither is read. The plan for the
  first is a `system` row per changed file, `file changed: <status>
  <path> +<added> -<removed>`, with `project_path` from `root`, joined to
  the conversation by `changes.id`, at `createdAt`.
- Sync, relay and origin: the agent records none (the paragraph below is
  unchanged at HEAD). Team share and P2P lend compute; a team-pool reply
  only names the teammate's machine in `meta.provider`.
- Scratch directories: none. Agent mode works only in the first
  workspace folder
  ([index.ts:494-497](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/index.ts#L494-L497)); the
  one temporary file, a copy of the repository's index named
  `twinny-index-<uuid>` in the system temporary directory, used to
  snapshot the tree around a command, is deleted at once
  ([src/extension/chat/command-snapshot.ts:62-80](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/command-snapshot.ts#L62-L80)).
- Deletion: deleting a conversation removes its key from
  `twinny.conversations` and clears `twinny.active-conversation` when it
  was open; "clear all" writes `{}`
  ([conversation-history.ts:157-178](https://github.com/twinnydotdev/twinny/blob/0337b265bf3b9f8f00ff45d597ae1f2e99ef230a/src/extension/chat/conversation-history.ts#L157-L178)).
  Neither touches `agent-changes/` or the log.
- Drift: a `toolSteps[]` entry with `said: true` is a user message, and
  the parser emits it as a `tool_use` named `said` and an empty
  `tool_result`; `changes`, `mcpTool`, `meta.outOfSteps` and
  `meta.instructions` are not read.
- Bad lines: the one source read is a single JSON value, and a value
  that does not decode is one whole-file `parser:` row; no line-oriented
  file is read.

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
