# VS Code chat session schema (Copilot Chat)

Catalog agent: `vscode`. VS Code's built-in chat store is used by GitHub
Copilot Chat and by any other chat participant, so parsing it covers Copilot
Chat without touching the closed-source extension. The same layout exists in
VSCodium, Cursor, Windsurf and the other forks whose `User` directories the
catalog collects. Paths cited are relative to the [microsoft/vscode](https://github.com/microsoft/vscode) clone.

Paths, credentials and the rest of the per-user state are in
[`collectors/research/vscode.md`](../../collectors/research/vscode.md).

## 1. Source

[microsoft/vscode](https://github.com/microsoft/vscode) at [`d7622a529314a4abcefd7ca9e3d7344bc9ccba9e`](https://github.com/microsoft/vscode/commit/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e), MIT
([`LICENSE.txt`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/LICENSE.txt)). Open source. The Copilot Chat extension itself is closed;
the `modelId`, `agent.id` and `responderUsername` string values in the
fixture are therefore invented.

Sync was checked at [`661e013`](https://github.com/microsoft/vscode/commit/661e013024de5052af476650250dabbebb4c1165)
on 2026-10-17. The Copilot Chat extension's source is now in that
repository under `extensions/copilot/`: the
[microsoft/vscode-copilot-chat](https://github.com/microsoft/vscode-copilot-chat)
repository was archived at [`5863f5a`](https://github.com/microsoft/vscode-copilot-chat/commit/5863f5a7088958050792b5dccbe8b46c6e13eccc)
with a notice that development moved into microsoft/vscode
([`README.md:1-8`](https://github.com/microsoft/vscode-copilot-chat/blob/5863f5a7088958050792b5dccbe8b46c6e13eccc/README.md#L1-L8)),
so the sync citations below read the extension at the same vscode commit.
Two names run through them. Chronicle is the extension's internal name for
its session tracking and upload code (the `chronicle` directories and the
`/chronicle` chat command). A cloud agent session, session type
`copilot-cloud-agent`, is a task run by the Copilot coding agent on
GitHub's servers, which VS Code lists and renders but does not run
([`chatSessionsService.ts:408-417`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/chatSessionsService.ts#L408-L417)).

## 2. Transcript files

[`common/model/chatSessionStore.ts`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts), under the user data directory
(`~/.config/Code/`, `Library/Application Support/Code/`,
`AppData/Roaming/Code/`, likewise for Insiders and VSCodium):

- Workspace: `User/workspaceStorage/<hash>/chatSessions/<sessionId>.jsonl`
  (1.109 and later, an append log) or `<sessionId>.json` (before 1.109, flat
  JSON) ([`:72-73`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L72-L73), [`:731-741`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L731-L741)). Log mode is the default
  (`getValue('chat.useLogSessionStorage') !== false`, registered nowhere
  else).
- Empty window: `User/globalStorage/emptyWindowChatSessions/<sessionId>.jsonl|json`
  ([`:72`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L72)); older `User/workspaceStorage/no-workspace/chatSessions/*.json`
  ([`:75-76`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L75-L76), [`:714-729`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L714-L729)).
- Transferred: `User/globalStorage/transferredChatSessions/<sessionId>.json`
  ([`:78`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L78), [`:745-750`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L745-L750)).

One file is one chat session.

## 3. Record schema

[`common/model/chatModel.ts`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts). Top level `ISerializableChatData3`
[`:2196-2227`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2196-L2227): `version: 3`, `sessionId`, `creationDate` (ms epoch),
`initialLocation`, `requests: ISerializableChatRequestData[]`,
`responderUsername`, `customTitle?`, `hasPendingEdits?`, `inputState?`,
`repoData?`, `pendingRequests?`, `workingDirectory?` (URI string). Written in
that order by `storageSchema` ([`chatSessionOperationLog.ts:203-216`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L203-L216)).

`ISerializableChatRequestData` [`:2037-2094`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2037-L2094), one user turn plus response:
`requestId`, `timestamp?` (ms, request start), `message: string | {text,
parts[]}` ([`requestParser/chatParserTypes.ts:20-23`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/requestParser/chatParserTypes.ts#L20-L23)), `variableData:
{variables: [{id, name, fullName?, value, range?}]}`
([`attachments/chatVariableEntries.ts:63-75`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/attachments/chatVariableEntries.ts#L63-L75)), `agent?: {id, name, fullName?,
extensionId, ...}` ([`participants/chatAgents.ts:63-71`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/participants/chatAgents.ts#L63-L71)), `modelId?`
(user-selected model id, [`chatServiceImpl.ts:1291`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts#L1291)), `modeInfo?: {kind,
telemetryModeId: 'ask'|'agent'|'edit'|'custom'|...}` ([`chatModel.ts:394-401`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L394-L401)),
`response: SerializedChatResponsePart[]`, `responseId?`,
`responseTimestamp?` (ms), `result?: {errorDetails?, timings?, metadata?}`,
`modelState?`, `vote?`, `followups?`, `usedContext?`, `contentReferences?`,
`codeCitations?`, `promptTokens?`, `completionTokens?`, `latestModelCall?`,
`elapsedMs?`, `editedFileEvents?: [{uri, eventKind}]`, `isSystemInitiated?`,
`requestSource?`, `terminalExecutionId?`, `confirmation?`, deprecated
`isHidden?`, `isCanceled?`.

Response parts ([`:2064`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2064)): a bare `IMarkdownString` `{value, isTrusted?, ...}`
for assistant text ([`chatSessionOperationLog.ts:45`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L45)); objects keyed by
`kind`: `"thinking"` `{value?: string|string[], id?, reasoningDurationMs?}`
([`chatService.ts:635-644`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L635-L644)); `"toolInvocationSerialized"` `{toolCallId,
toolId, invocationMessage, pastTenseMessage?, isComplete, isConfirmed,
resultDetails?` (URI[] or `{input: string, output: [...], isError?}`,
[`tools/languageModelToolsService.ts:283-290`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/tools/languageModelToolsService.ts#L283-L290)), `resultError?`,
`toolSpecificData?` (`{kind:'terminal', commandLine:{original,
userEdited?}, cwd?}` [`chatService.ts:686-700`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L686-L700); `{kind:'input', rawInput}`
[`:847-850`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L847-L850)), `subAgentInvocationId?}` ([`chatService.ts:1196-1215`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1196-L1215)); plus
`textEditGroup`, `codeblockUri`, `progressMessage`, `confirmation`,
`undoStop`, `inlineReference` and others ([`chatSessionOperationLog.ts:62-95`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L62-L95)).
Tool call and result are the same object: the call is `toolCallId`, `toolId`
and `toolSpecificData`, the result is `resultDetails`, `resultError` and
`isComplete`. No git branch field; `repoData` is unspecified here.

Permission state on a tool invocation
([`chatService.ts:1204-1210`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1204-L1210)):
`isConfirmed` is `ConfirmedReason | boolean | undefined`, the boolean
being the pre-1.104 form. `ConfirmedReason`
([`:880-889`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L880-L889))
is an object whose `type` is a `ToolConfirmKind`, a `const enum`
([`:870-877`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L870-L877))
with no explicit values, so TypeScript inlines and serialises the
declaration index: `Denied` 0, `ConfirmationNotNeeded` 1, `Setting` 2,
`LmServicePerTool` 3, `UserAction` 4, `Skipped` 5. Beside `type`:
`source` (`user`, `hook` or `riskAssessment`, the actor of a denial or
skip, optional) for `Denied` and `Skipped`; `reason` (string or
markdown) for `ConfirmationNotNeeded`; `id` (the setting) for `Setting`;
`scope` (`session`, `workspace` or `profile`) for `LmServicePerTool`;
`selectedButton` and `selectedButtonKind` for `UserAction`. The
invocation's own `source` field is a different thing: the
`ToolDataSource` the tool came from, undefined before 1.104, an object
with `type` (`extension`, `mcp`, `user`, `internal`, `external`) and
`label`
([`tools/languageModelToolsService.ts:109-134`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/tools/languageModelToolsService.ts#L109-L134)).

A `confirmation` response part is `{kind: 'confirmation', title, message,
data, buttons?, isUsed?}`
([`chatService.ts:514-522`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L514-L522)),
a question a chat participant puts to the user. Clicking a button sends a
new request whose prompt is `<label>: "<title>"` and whose `confirmation`
is the button's label, and sets `isUsed`
([`browser/widget/chatContentParts/chatConfirmationContentPart.ts:42-60`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatConfirmationContentPart.ts#L42-L60));
the request field is a string
([`chatModel.ts:2084`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2084)).

A local chat delegated to the cloud agent ("Continue In" the cloud) leaves
one `pullRequest` response part in the local session, `{kind:
'pullRequest', uri?, command, title, description, author, linkTag}`
([`chatService.ts:1243-1254`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1243-L1254),
a kind the operation log persists,
[`chatSessionOperationLog.ts:86`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L86)).
The extension fills it with the task's web URL as `uri` and as the
argument of a `vscode.open` command, and the task title as `title` and
`linkTag`, with empty `description` and `author`
([`copilotCloudSessionsProvider.ts:1948-1960`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L1948-L1960)).
Before the task is created the chat history is summarised and sent with
it ([`:1873-1876`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L1873-L1876)).

JSONL framing ([`common/model/objectMutationLog.ts:196-215`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/objectMutationLog.ts#L196-L215), read
[`:340-385`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/objectMutationLog.ts#L340-L385)): each line is `{"kind":0,"v":<full session>}` (Initial),
`{"kind":1,"k":[path...],"v":...}` (Set), `{"kind":2,"k":[...],"v":[items],
"i"?:index}` (Push; `i` truncates from that index) or `{"kind":3,"k":[...]}`
(Delete). Replay in order to rebuild the object; `k` is a path of keys and
array indexes, for example `["requests",3,"response"]`.

## 4. Joins

`workspaceStorage/<hash>/workspace.json` is `{"folder": "<file URI>"}` or
`{"workspace": "<.code-workspace URI>"}`
([`platform/storage/electron-main/storageMain.ts:416`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L416),[`472-474`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L472-L474)); the agents
window also records `workingDirectory` in the session. Tool call and result
share one object; `toolCallId` is the join key to extension telemetry.
`agent.id` and `responderUsername` identify the participant (Copilot).

## 5. SQLite stores

`state.vscdb` (`ItemTable(key, value)`, [`base/parts/storage/node/storage.ts:73`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/base/parts/storage/node/storage.ts#L73))
in `workspaceStorage/<hash>/` and `globalStorage/`
([`storageMain.ts:285`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L285),[`353`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L353),[`415`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L415)). Keys: `interactive.sessions` is the legacy
JSON blob of all sessions from before the file store
([`chatServiceImpl.ts:67`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts#L67),[`341`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts#L341), migrated by [`chatSessionStore.ts:611-633`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L611-L633));
`chat.ChatSessionStore.index` is `{version:1, entries:{<sessionId>:{sessionId,
title, lastMessageDate (ms), timing:{created, lastRequestStarted,
lastRequestEnded}, workingDirectory?, isEmpty?, isExternal?, ...}}}`
([`:39`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L39),[`780-836`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L780-L836)); `ChatSessionStore.transferIndex` ([`:40`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L40)).

An external session, one whose resource is not a local chat URI (a cloud
agent task or another provider's session), gets no file under
`chatSessions/`: the store writes only its index entry, keyed by the
resource URI string rather than a session id
([`chatSessionStore.ts:405-418`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L405-L418)), with
`isExternal: true`
([`:802-805`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L802-L805), [`:875-877`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L875-L877)) and
`inputState`, the unsent draft
([`:813-818`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L813-L818)). External entries are exempt from the
400-session trim ([`:441`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L441)). A cloud agent entry's key is
`copilot-cloud-agent:/task/<taskId>`
([`copilotCloudSessionsProvider.ts:495`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L495),
[`copilotCodingAgentUtils.ts:132-134`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode/copilotCodingAgentUtils.ts#L132-L134)).

Sync state, all written by the Copilot Chat extension under its
global storage directory `User/globalStorage/github.copilot-chat/`
(`globalStorageUri`, lower-cased extension id) or its global state:

- `cloudSessions.json`, a JSON object
  `{<local session id>: {cloudSessionId, cloudTaskId}}`, both strings
  ([`cloudSessionIdStore.ts:10-22`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionIdStore.ts#L10-L22),
  [`cloudSessionTypes.ts:28-31`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/common/cloudSessionTypes.ts#L28-L31),
  path from [`remoteSessionExporter.ts:277`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L277)).
  An entry is added when the cloud session is created, at the first agent
  turn of a session with sync on
  ([`remoteSessionExporter.ts:1066-1071`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L1066-L1071)),
  and the whole object is rewritten on each change
  ([`cloudSessionIdStore.ts:145-156`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionIdStore.ts#L145-L156)).
  A reconcile with the server, run before a delete or a reindex, adds an
  entry for every session the account's listing returns, so the file can
  also name sessions uploaded from another machine
  ([`:96-127`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionIdStore.ts#L96-L127),
  [`remoteSessionExporter.ts:244-258`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L244-L258)).
  A session never uploaded has no entry; the file is absent until the
  first upload. The key is the chat session id, the same id as
  `chatSessions/<sessionId>.jsonl` for a local chat: the sidebar's delete
  passes `LocalChatSessionUri.parseLocalSessionId` values to the delete
  command, which looks them up in this file
  ([`agentSessionsActions.ts:844-875`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/agentSessions/agentSessionsActions.ts#L844-L875)).
- `session-store.db`, the chronicle index, SQLite with tables
  `sessions(id, cwd, repository, host_type, branch, summary, agent_name,
  agent_description, created_at, updated_at)`, `turns(session_id,
  turn_index, user_message, assistant_response, timestamp)`,
  `checkpoints`, `session_files` and `session_refs`
  ([`services.ts:280-283`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/extension/vscode-node/services.ts#L280-L283),
  [`sessionStore.ts:194-250`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/platform/chronicle/node/sessionStore.ts#L194-L250)),
  written when `github.copilot.chat.localIndex.enabled` is on, its
  default
  ([`package.json:3227-3233`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/package.json#L3227-L3233)).
  Its `sessions.id` is the key of `cloudSessions.json`; the extension
  counts synced sessions by that join
  ([`remoteSessionExporter.ts:172-191`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L172-L191)).
  It holds no sync flag of its own.
- `github.copilot.cloudAgent.ownedTasks` in the extension's global state,
  which VS Code keeps as one JSON value in the `ItemTable` row keyed
  `GitHub.copilot-chat` of `User/globalStorage/state.vscdb`
  ([`extHostMemento.ts:117-118`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/api/common/extHostMemento.ts#L117-L118),
  [`extensionStorage.ts:175`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/extensionManagement/common/extensionStorage.ts#L175)):
  `{<taskId>: {recordedAt: <ms>, application?: <string>}}` (or a bare
  number, the older form), the newest 1,000 cloud agent tasks started or
  messaged from VS Code
  ([`cloudTaskOwnership.ts:8-14`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/cloudTaskOwnership.ts#L8-L14),
  [`:36-63`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/cloudTaskOwnership.ts#L36-L63)).
  `application` is `vscode` for a task created here, else the task's
  `event_type` or `github/autopilot`
  ([`copilotCloudSessionsProvider.ts:2766-2772`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L2766-L2772)).
  Each task is a session held on GitHub's servers that this install
  started or messaged, so it marks a synced session in the sense of the
  parser plan ([section 8](#8-parser-plan)), and one whose origin is
  remote: it began on the vendor's side and is only listed here.

## 6. Format versions

`version` absent means v1, `2` adds `computedTitle`, `3` adds `customTitle`;
`normalizeSerializableChatData` ([`chatModel.ts:2422-2461`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2422-L2461)) fills a missing
`sessionId` or `creationDate` (defaulting to one year ago). `message` may be
a plain string in old data ([`:2069`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2069)); `response` may be a string or string[]
([`chatSessionStore.ts:688-699`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L688-L699)). Storage moved from `state.vscdb` to `.json`
to `.jsonl` (1.109 and later); flat `.json` is still read as a fallback
([`:653-675`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L653-L675)). `isConfirmed` was boolean before 1.104; `source` was undefined
before 1.104 ([`chatService.ts:1204-1209`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1204-L1209)).

## 7. Secrets

`variableData.variables[].value` and `usedContext` may hold attached file
contents; `toolSpecificData.rawInput` and `commandLine` may hold command-line
secrets. `state.vscdb` stores extension auth material under other keys (out
of scope here; see the Cursor and Windsurf notes in
[`collectors/docs/coverage.md`](../../collectors/docs/coverage.md#credentials)).

Session sync uses no credential file of its own: each request goes to the
`api` endpoint named in the Copilot token, the short-lived token the
extension exchanges for the user's GitHub sign-in
([`cloudSessionApiClient.ts:329-341`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionApiClient.ts#L329-L341)),
and `cloudSessions.json` holds only ids. Uploaded events pass a filter
that replaces known token values and token patterns
([`secretFilter.ts:117-172`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/common/secretFilter.ts#L117-L172)).

## 8. Parser plan

Globs: `**/User/workspaceStorage/*/chatSessions/*.{json,jsonl}`,
`**/User/globalStorage/emptyWindowChatSessions/*.{json,jsonl}`,
`**/User/workspaceStorage/no-workspace/chatSessions/*.json`,
`**/User/globalStorage/transferredChatSessions/*.json`, plus the sibling
`workspace.json`.

Rows: one `user` per request, one `assistant` per contiguous markdown run,
one `thinking` per thinking part, one `tool_use` plus `tool_result` per
`toolInvocationSerialized`.

| Column | Source |
| --- | --- |
| timestamp_utc | `timestamp` for the user row, `responseTimestamp` for response parts (ms) |
| session_id | `sessionId` |
| project_path | `workspace.json` `folder` (file URI to path) or `workingDirectory` |
| git_branch | empty |
| model | `modelId` |
| tool_name, tool_use_id | `toolId`, `toolCallId` |
| text | text, `invocationMessage` or `commandLine.original` |

Model and permission rows, all `system` (issues 96 and 97):

- `model: <id>` at the first request whose `modelId` is set and
  `model: <old> -> <new>` on every later request with a different
  `modelId`, before the request's user row, with its `timestamp`. The
  model is chosen per request, so a session can change model at any
  request.
- `permission mode: <mode>` and `permission mode: <old> -> <new>` from
  the request `modeInfo.telemetryModeId` (`ask`, `agent`, `edit`,
  `custom`), placed and timed the same way.
- `permission decision: confirmed=<value>` after a tool invocation's
  `tool_result` row, with its `toolCallId` and `toolId`: `<value>` is
  `true` or `false` for the boolean form, else the `ToolConfirmKind`
  name and number (`UserAction(4)`), followed by the `ConfirmedReason`'s
  other fields as `key=value` (`reason` last), and `tool_source=<type>`
  from the invocation's `source`. An invocation without `isConfirmed`
  gets no row.
- `permission decision: confirmation isUsed=<bool> buttons=<list>
  title=<title>` and the part's `message` on the next line, for a
  `confirmation` response part, at the response time.
- `permission decision: confirmation=<label>` after the user row of a
  request whose `confirmation` is set.

The `chat.*` auto-approve settings in `settings.json` are not read:
their keys are not recorded in this document or in
[`collectors/research/vscode.md`](../../collectors/research/vscode.md).

Sync: Copilot Chat's session sync uploads chat sessions to the user's
GitHub account and marks each uploaded session in
`User/globalStorage/github.copilot-chat/cloudSessions.json`
([section 5](#5-sqlite-stores)). It runs when `chat.sessionSync.enabled`
is on, a core setting whose default is `false` but which is tagged
experimental with `experiment: {mode: 'auto'}`, so an experiment can turn
it on, and which the organisation policy `CopilotSessionSync` can force
off
([`chat.shared.contribution.ts:830-851`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/chat.shared.contribution.ts#L830-L851)),
and when `github.copilot.chat.localIndex.enabled` is on, which it is by
default
([`remoteSessionExporter.ts:320-366`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L320-L366)). A session is
uploaded only when the workspace resolves to a GitHub repository not
matched by `chat.sessionSync.excludeRepositories`
([`:905-961`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L905-L961),
[`sessionIndexingPreference.ts:48-65`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/common/sessionIndexingPreference.ts#L48-L65)).
What leaves is a cloud session created at the first agent turn
(`POST /agents/sessions` with the repository's owner and repository ids
and the local session id), then the turns as Copilot CLI-compatible
events (`session.start`, `user.message`, `assistant.message`,
`tool.execution_start`, `tool.execution_complete`) posted to
`/agents/sessions/<id>/events` about 500 ms after each turn ends
([`cloudSessionApiClient.ts:152-199`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionApiClient.ts#L152-L199),
[`remoteSessionExporter.ts:49`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L49)). `/chronicle reindex` and
the `github.copilot.chronicle.reindex` command also upload past sessions
that have no entry yet
([`sessionReindexer.ts:349-376`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/sessionReindexer.ts#L349-L376)).
The parser yields one `system` row per `cloudSessions.json` entry,
`session synced: remote session <cloudSessionId> task <cloudTaskId>
(from User/globalStorage/github.copilot-chat/cloudSessions.json, file
mtime)`, with the entry's key as `session_id`, timestamped by the file's
modification time; an entry with no local session is still a row, since
it names a session deleted here or uploaded from another machine. The
`ownedTasks` list of cloud agent tasks ([section 5](#5-sqlite-stores)) is
the other remote record: one `system` row per entry, `session synced:
cloud agent task <taskId> application=<application or -> (from
state.vscdb GitHub.copilot-chat github.copilot.cloudAgent.ownedTasks,
recordedAt)` at `recordedAt`,
with `session_id` `copilot-cloud-agent:/task/<taskId>` to match the
index entry; the older bare-number form is read as `recordedAt` with no
`application`. A task is a `session synced:` row although nothing was
uploaded from the host: it began on GitHub's servers, and GitHub holds
its copy as it holds an uploaded session's, so for a responder it is a
session the vendor can still produce. Its session reads `synced` `yes`.
Only the origin differs, and it is a second row at the same time and
session: `session origin: remote GitHub cloud agent (from state.vscdb
GitHub.copilot-chat github.copilot.cloudAgent.ownedTasks, recordedAt)`.
The parser sets `records_origin`, so a task's session reads `origin`
`remote` and every other VS Code session `local`. Both
rows are fixture only: no real install has shown either file. A delete
removes the marker. The sidebar's delete of a local session calls
`github.copilot.sessionSync.deleteSessionFromCloud`, which deletes the
session's `session-store.db` rows and its `cloudSessions.json` entry,
and sends `DELETE /agents/tasks/<cloudTaskId>` only while sync is still
on, so a session deleted after sync was turned off keeps its remote copy
and loses its local marker
([`remoteSessionExporter.ts:656-690`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L656-L690),
[`cloudSessionApiClient.ts:286-287`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionApiClient.ts#L286-L287)).
The Delete Session Sync Data command
(`github.copilot.sessionSync.deleteSessions`) offers local and cloud or
cloud only; both remove the entry
([`remoteSessionExporter.ts:545-616`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L545-L616)). Neither path writes
a log line: the exporter reports through telemetry only. VS Code Settings
Sync does not carry chat sessions. Its resources are settings,
keybindings, snippets, prompt files, tasks, MCP configuration,
extensions, global state and profiles
([`userDataSync.ts:169-181`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSync.ts#L169-L181)); global
state carries only keys stored with the `USER` target
([`globalStateSync.ts:296-304`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/globalStateSync.ts#L296-L304)), and
the chat session index and every extension's state are stored with the
`MACHINE` target
([`chatSessionStore.ts:425`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L425),
[`extensionStorage.ts:175`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/extensionManagement/common/extensionStorage.ts#L175)).
Its local state, `User/sync/<resource>/lastSync<resource>.json`
(`{ref, syncData: {version, machineId?, content}}`) and the timestamped
`<yyyymmddThhmmss>.json` backups kept 30 days by default
(`sync.localBackupDuration`)
([`userDataSync.ts:187-189`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSync.ts#L187-L189),
[`:457-466`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSync.ts#L457-L466),
[`userDataSyncLocalStoreService.ts:99-125`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSyncLocalStoreService.ts#L99-L125)),
records that settings, prompt files and MCP configuration were synced, not
sessions, and gets no row. Export Chat (`workbench.action.chat.export`)
writes the session as JSON to a file the user picks, `chat.json` by
default, and uploads nothing
([`chatImportExport.ts:23`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/actions/chatImportExport.ts#L23),
[`:42-79`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/actions/chatImportExport.ts#L42-L79));
no share command was found (searched `share`, `shareChat` and
`ShareSession` in `src/vs/workbench/contrib/chat` and
`extensions/copilot/src`). Copilot CLI sessions run in VS Code's agent
host pass the same setting to the Copilot SDK as `enableRemoteSessions`
([`copilotAgent.ts:3846`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/agentHost/node/copilot/copilotAgent.ts#L3846))
and keep their state under `~/.copilot/session-state/`, where the
`copilot-cli` parser reads the sync marker
([`analyzer/research/copilot-cli.md`](copilot-cli.md#8-parser-plan)).

Fixture `chatSessions/9ab.jsonl`:

```jsonl
{"kind":0,"v":{"version":3,"creationDate":1759400000000,"customTitle":null,"initialLocation":"panel","responderUsername":"GitHub Copilot","sessionId":"9ab","requests":[{"requestId":"request_1","timestamp":1759400001000,"message":{"text":"run tests","parts":[]},"agent":{"id":"github.copilot.default","name":"GitHub Copilot","extensionId":{"value":"GitHub.copilot-chat"}},"modelId":"copilot/gpt-4.1","modeInfo":{"kind":"agent","telemetryModeId":"agent","isBuiltin":true},"variableData":{"variables":[]},"response":[{"kind":"thinking","value":"Need pytest","id":"t1"},{"kind":"toolInvocationSerialized","toolCallId":"call_a","toolId":"run_in_terminal","invocationMessage":"Running command","isComplete":true,"isConfirmed":true,"toolSpecificData":{"kind":"terminal","commandLine":{"original":"pytest"}},"resultDetails":{"input":"pytest","output":[{"type":"embed","value":"3 passed"}]}},{"value":"All tests pass."}],"responseId":"response_1","responseTimestamp":1759400002000,"modelState":{"value":"complete"}}],"workingDirectory":"file:///home/u/proj"}}
{"kind":2,"k":["requests"],"v":[{"requestId":"request_2","timestamp":1759400010000,"message":{"text":"thanks","parts":[]},"variableData":{"variables":[]},"response":[{"value":"You're welcome."}]}]}
```

`workspace.json`: `{"folder": "file:///home/u/proj"}`

Confidence. High: field set, JSONL framing, bare `{value}` markdown parts.
Low: the actual `modelId`, `agent.id` and `responderUsername` values, which
come from the closed Copilot extension. Not determined: the exact release in
which `.jsonl` became the default beyond the `1.109` code comment; Copilot's
own data in `state.vscdb` keys other than `interactive.sessions`. Sync:
high for `cloudSessions.json`, `ownedTasks` and the delete path, from
source at the 2026-10-17 commit; none of it has been observed on a real
install.
