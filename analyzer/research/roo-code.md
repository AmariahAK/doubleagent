# Roo Code transcript schema

Catalog agent: `roo-code`. Roo Code forked Cline and keeps Cline's task
layout, so the record shapes in [cline.md](cline.md) apply with the
differences listed here. Paths cited are relative to the clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/roo-code.md`](../../collectors/research/roo-code.md).

## 1. Source

[RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) at [`b867ec9145750d0ae1ff7f02d35406e9bf2a0b16`](https://github.com/RooCodeInc/Roo-Code/commit/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16),
Apache-2.0. Open source. Applies to the VS Code extension
(`RooVeterinaryInc.roo-cline`, [`src/package.json:2`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L2),[`5`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/package.json#L5)) and the CLI
(`apps/cli`).

## 2. Transcript files

VS Code: `globalStorage/rooveterinaryinc.roo-cline/tasks/<taskId>/` with
`api_conversation_history.json`, `ui_messages.json`, `task_metadata.json`,
`history_item.json`; index `tasks/_index.json`
([`src/shared/globalFileNames.ts:1-9`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/shared/globalFileNames.ts#L1-L9)). The root can be redirected by the
setting `roo-cline.customStoragePath` ([`src/utils/storage.ts:14-48`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/utils/storage.ts#L14-L48)). CLI
root: `~/.vscode-mock/global-storage/` ([`apps/cli/src/lib/task-history/index.ts:8`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/task-history/index.ts#L8);
[`packages/vscode-shim/src/utils/paths.ts:8`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L8),[`65-66`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/utils/paths.ts#L65-L66)), plus
`~/.vscode-mock/workspace-storage/<hash>/`, `logs/`, and
`global-storage/secrets.json` ([`vscode-shim/src/storage/SecretStorage.ts:47`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/vscode-shim/src/storage/SecretStorage.ts#L47)).
`~/.roo` holds CLI config and global rules only
([`apps/cli/src/lib/storage/config-dir.ts:5`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/config-dir.ts#L5)). The legacy transcript name
`claude_messages.json` is read and then deleted on upgrade
([`src/core/task-persistence/apiMessages.ts:73-91`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/apiMessages.ts#L73-L91)).

The CLI also keeps an input history, `~/.roo/cli-history.json`: the file name is joined to `getConfigDir()` ([`apps/cli/src/lib/storage/history.ts:20-22`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L20-L22)), which is `~/.roo` on every platform ([`apps/cli/src/lib/storage/config-dir.ts:5-9`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/config-dir.ts#L5-L9)). The catalog line `roo-code|.roo` collects it. It is the history the interactive prompt steps through with the arrow keys, not a transcript: see [section 3](#3-record-schema) for its shape.

## 3. Record schema

`api_conversation_history.json` is the Anthropic `MessageParam[]` shape as
in Cline ([`apiMessages.ts:12`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/apiMessages.ts#L12)), extended with `ts` (ms), `isSummary`, `id`,
`type:"reasoning"`, `summary`, `encrypted_content`, `reasoning_details`,
`reasoning_content`, `condenseId`, `condenseParent`, `truncationId`,
`truncationParent`, `isTruncationMarker` ([`apiMessages.ts:13-37`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/apiMessages.ts#L13-L37)). Tool calls
are mostly XML inside text blocks.

`ui_messages.json` ([`packages/types/src/message.ts:249-274`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L249-L274)): `ts, type, ask,
say, text, images, partial, reasoning, conversationHistoryIndex,
checkpoint{}, progressStatus, contextCondense{cost, prevContextTokens,
newContextTokens, summary, condenseId}, contextTruncation, isProtected,
apiProtocol, isAnswered`. Asks [`:27-40`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L27-L40); says [`:144-174`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/message.ts#L144-L174) add
`subtask_result`, `checkpoint_saved`, `condense_context`,
`codebase_search_result`, `api_req_retried`. `ClineSayTool`
([`packages/types/src/vscode-extension-host.ts:693-760`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/vscode-extension-host.ts#L693-L760)) adds `appliedDiff`,
`codebaseSearch`, `newTask`, `switchMode`, `finishTask`, `batchFiles[]`;
`ClineApiReqInfo` ([`:780-790`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/vscode-extension-host.ts#L780-L790)) adds `apiProtocol`. No model name appears
anywhere in Roo transcripts; `HistoryItem.apiConfigName` is a profile name.

`HistoryItem` ([`packages/types/src/history.ts:7-29`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/packages/types/src/history.ts#L7-L29)): `id, rootTaskId?,
parentTaskId?, number, ts, task, tokensIn, tokensOut, totalCost, size?,
workspace?, mode?, apiConfigName?, status?, delegatedToId?, childIds?, ...`.
`_index.json` is `{version:1, updatedAt, entries: HistoryItem[]}`
([`TaskHistoryStore.ts:14-18`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L14-L18)). `task_metadata.json` holds only
`files_in_context` ([`src/core/context-tracking/FileContextTracker.ts:117-135`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/context-tracking/FileContextTracker.ts#L117-L135)).

Timestamps are millisecond epochs. No git branch is recorded.

`cli-history.json` is `{version: 1, entries: string[]}` ([`history.ts:9-15`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L9-L15)), written pretty-printed with tabs and trimmed to the newest `MAX_HISTORY_ENTRIES` (500) on every save ([`history.ts:6-7`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L6-L7), [`64-77`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L64-L77)). `addToHistory` appends the trimmed line, skipping an empty one and one equal to the last entry ([`history.ts:90-108`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L90-L108)); `loadHistory` keeps only non-blank strings ([`history.ts:44-45`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/lib/storage/history.ts#L44-L45)). Entries are oldest first and carry no time, task id or workspace. The input box adds every submitted line before acting on it ([`apps/cli/src/ui/components/autocomplete/AutocompleteInput.tsx:180-198`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/ui/components/autocomplete/AutocompleteInput.tsx#L180-L198); [`apps/cli/src/ui/hooks/useInputHistory.ts:83-97`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/ui/hooks/useInputHistory.ts#L83-L97)), so it holds the first prompt of a task, the answers to follow-up questions and later messages, and CLI commands such as `/new` that the CLI handles itself and never sends to a task ([`apps/cli/src/ui/hooks/useTaskSubmit.ts:56-132`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/cli/src/ui/hooks/useTaskSubmit.ts#L56-L132)). A prompt given on the command line rather than typed into the input box does not pass through it.

## 4. Joins

Directory name = `HistoryItem.id`; workspace = `workspace` in
`history_item.json` or `_index.json`; `rootTaskId` and `parentTaskId` link
subtasks. `ClineMessage.conversationHistoryIndex` indexes into the API
history.

A `cli-history.json` entry joins a task on text only. The first prompt of a task becomes the task's first `say: "text"` record with the same text ([`src/core/task/Task.ts:1908`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L1908)), and a later message or follow-up answer becomes a `say: "user_feedback"` record ([`Task.ts:2027-2029`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L2027-L2029)); both are `user` rows of the task. The API history wraps the first prompt in `<user_message>` tags ([`Task.ts:1935`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task/Task.ts#L1935)), so a task that has only `api_conversation_history.json` left does not match on text. The file outlives a deleted task directory, a removed workspace and the extension's task-history pruning, since nothing but the 500-entry cap removes an entry; it does not record which task or workspace a line went to.

## 5. SQLite stores

None. The VS Code side keeps secrets in SecretStorage (`state.vscdb`).

## 6. Format versions

`claude_messages.json` became `api_conversation_history.json` (deleted on
read); globalState `taskHistory` became `history_item.json` plus
`_index.json` with `version: 1` ([`TaskHistoryStore.ts:320-360`](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/task-persistence/TaskHistoryStore.ts#L320-L360)).
`.roo-code` has no references in current source and is legacy only.

## 7. Secrets

CLI `~/.vscode-mock/global-storage/secrets.json` holds provider profiles
with API keys and should be a collector `SECRET_GLOBS` entry (tracked in
issue 23). Transcripts carry file contents and command output.

## 8. Parser plan

Globs: `<GS>/rooveterinaryinc.roo-cline/tasks/*/{api_conversation_history,ui_messages,history_item}.json`,
`<GS>/rooveterinaryinc.roo-cline/tasks/_index.json`,
`.vscode-mock/global-storage/tasks/**` (same files),
`.roo/cli-history.json`.

The task files are the primary store. `cli-history.json` is a secondary source (issue 122): one `user` row per entry, with empty `timestamp_utc`, `session_id` and `project_path` because the file records none, so the timeline's deduplication pairs it with a task's `user` row of the same text and keeps it only when no task has the text (a prompt whose task directory was deleted, or a CLI command such as `/new`).

Rows and columns follow the Cline legacy mapping, with `ApiMessage.ts`
available as a fallback timestamp, `condense_context` typed `system`,
`session_id` the directory name, `project_path` from `history_item.workspace`,
and `model` always empty.

Roo Code records no model in any of these files (`apiConfigName` is a
profile name, not a model id), so the parser yields no `model:` rows.

Fixture:

```json
{"_file":"tasks/_index.json","record":{"version":1,"updatedAt":1760000005000,"entries":[{"id":"8f1c2b7e-1","number":1,"ts":1760000000000,"task":"fix tests","tokensIn":1200,"tokensOut":80,"totalCost":0.0041,"workspace":"/home/u/proj","mode":"code","status":"completed"}]}}
{"_file":"api_conversation_history.json","record":{"role":"assistant","content":[{"type":"tool_use","id":"toolu_01A","name":"execute_command","input":{"command":"pytest -q"}}],"ts":1760000002000}}
{"_file":"api_conversation_history.json","record":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_01A","content":"3 passed","is_error":false}],"ts":1760000003000}}
```

Confidence. High: file names, layouts and type definitions (read from
source). Not determined: the `checkpoint` object keys.
