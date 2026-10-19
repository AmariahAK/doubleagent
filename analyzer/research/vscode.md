# vscode

Catalog agent `vscode`. VS Code's built-in chat store is used by GitHub Copilot Chat and by any
other chat participant, so parsing it covers Copilot Chat without touching the closed-source
extension. The same layout exists in VSCodium, Cursor, Windsurf and the other forks whose `User`
directories the catalog collects. Paths cited are relative to the
[microsoft/vscode](https://github.com/microsoft/vscode) clone. Paths, credentials and the rest of
the per-user state are in [`collectors/research/vscode.md`](../../collectors/research/vscode.md).

## 1. Source and evidence

[microsoft/vscode](https://github.com/microsoft/vscode) at
[`d7622a529314a4abcefd7ca9e3d7344bc9ccba9e`](https://github.com/microsoft/vscode/commit/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e),
MIT
([`LICENSE.txt`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/LICENSE.txt)).
Open source. The Copilot Chat extension itself is closed; the `modelId`, `agent.id` and
`responderUsername` string values in the fixture are therefore invented.

Sync was checked at
[`661e013`](https://github.com/microsoft/vscode/commit/661e013024de5052af476650250dabbebb4c1165) on
2026-10-17. The Copilot Chat extension's source is now in that repository under
`extensions/copilot/`: the
[microsoft/vscode-copilot-chat](https://github.com/microsoft/vscode-copilot-chat) repository was
archived at
[`5863f5a`](https://github.com/microsoft/vscode-copilot-chat/commit/5863f5a7088958050792b5dccbe8b46c6e13eccc)
with a notice that development moved into microsoft/vscode
([`README.md:1-8`](https://github.com/microsoft/vscode-copilot-chat/blob/5863f5a7088958050792b5dccbe8b46c6e13eccc/README.md#L1-L8)),
so the sync citations below read the extension at the same vscode commit. Two names run through
them. Chronicle is the extension's internal name for its session tracking and upload code (the
`chronicle` directories and the `/chronicle` chat command). A cloud agent session, session type
`copilot-cloud-agent`, is a task run by the Copilot coding agent on GitHub's servers, which VS Code
lists and renders but does not run
([`chatSessionsService.ts:408-417`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/chatSessionsService.ts#L408-L417)).

Confidence is high for field set, JSONL framing, bare `{value}` markdown parts. Low: the actual
`modelId`, `agent.id` and `responderUsername` values, which come from the closed Copilot extension.
Not determined: the exact release in which `.jsonl` became the default beyond the `1.109` code
comment; Copilot's own data in `state.vscdb` keys other than `interactive.sessions`. Sync: high for
`cloudSessions.json`, `ownedTasks` and the delete path, from source at the 2026-10-17 commit; none
of it has been observed on a real install.

### Observed

- No real install. Sync (`cloudSessions.json`, `ownedTasks` and the delete path) has not been
  observed on a real install and its rows are fixture only ([Sync, relay and
  origin](#sync-relay-and-origin)); the Agents-window layout the parser handles is not observed on
  any real install, source-derived ([Scratch directories](#scratch-directories)).

### Source reviews

- 2026-10-19: review of microsoft/vscode at
  [`4d22f4f`](https://github.com/microsoft/vscode/commit/4d22f4f922eb012217ac65672ccce02f59d63706),
  the Copilot Chat extension read under `extensions/copilot/` at the same commit (the archived
  microsoft/vscode-copilot-chat repository is still at
  [`5863f5a`](https://github.com/microsoft/vscode-copilot-chat/commit/5863f5a7088958050792b5dccbe8b46c6e13eccc)).
  The document previously cited
  [`d7622a5`](https://github.com/microsoft/vscode/commit/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e)
  for the store and
  [`661e013`](https://github.com/microsoft/vscode/commit/661e013024de5052af476650250dabbebb4c1165)
  for sync. One line per requirement class:
  - Permission: found. The per-request `modeInfo.permissionLevel` (already in the type at `d7622a5`)
    and five standing-grant keys in `state.vscdb` are not read by the parser
    ([section 3](#3-record-schema), [section 5](#5-other-stores)).
  - Model: per-request `modelId` already covered; found the per-request `modelConfiguration` and the
    session's `inputState.selectedModel`, not read ([section 3](#3-record-schema)).
  - Past use: found. Chat editing session state, Copilot Chat's `session-store.db` turns, hook
    transcripts, debug logs and memory files are records the parser does not read
    ([section 5](#5-other-stores)).
  - Sync, relay and origin: already covered; `cloudSessions.json`, `ownedTasks` and
    `chat.sessionSync.enabled` are unchanged at HEAD. No relay.
  - Scratch directories: found. The Agents window's workspace file and the worktrees Copilot CLI
    sessions get ([section 8](#8-parser-plan)). The Agents-window layout the parser now handles
    (issue 185), a chat stored under the storage hash of `User/agent-sessions.code-workspace` with
    its project in `workingDirectory`, is not observed on any real install, source-derived
    (microsoft/vscode at
    [`4d22f4f`](https://github.com/microsoft/vscode/commit/4d22f4f922eb012217ac65672ccce02f59d63706)):
    the storage hash is inferred from the store's rule and unconfirmed on an install.
  - Deletion: found. Delete removes the session file and its index entry and leaves the other
    records; trimming the index to 400 sessions leaves the files ([section 5](#5-other-stores)).
  - Version drift: none in what the parser reads. The store paths, the mutation-log framing, the
    request fields, `ToolConfirmKind` and `ConfirmedReason` are the same at HEAD with moved line
    numbers; the session object gained `sessionCostInfo`.
  - Bad lines: already covered for every file the parser reads; the new JSONL sources need the same
    error rows when they are read.

## 2. Transcript stores

[`common/model/chatSessionStore.ts`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts),
under the user data directory (`~/.config/Code/`, `Library/Application Support/Code/`,
`AppData/Roaming/Code/`, likewise for Insiders and VSCodium):

- Workspace: `User/workspaceStorage/<hash>/chatSessions/<sessionId>.jsonl` (1.109 and later, an
  append log) or `<sessionId>.json` (before 1.109, flat JSON)
  ([`:72-73`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L72-L73),
  [`:731-741`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L731-L741)).
  Log mode is the default (`getValue('chat.useLogSessionStorage') !== false`, registered nowhere
  else).
- Empty window: `User/globalStorage/emptyWindowChatSessions/<sessionId>.jsonl|json`
  ([`:72`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L72));
  older `User/workspaceStorage/no-workspace/chatSessions/*.json`
  ([`:75-76`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L75-L76),
  [`:714-729`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L714-L729)).
- Transferred: `User/globalStorage/transferredChatSessions/<sessionId>.json`
  ([`:78`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L78),
  [`:745-750`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L745-L750)).

One file is one chat session.

### What survives a delete

The chat view's delete, and clearing all sessions (which does the same for each), remove each
session's `.json` and `.jsonl` file and its index entry
([`chatSessionStore.ts:455-482`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L455-L482),
[`:493-498`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L493-L498),
[`:500-508`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L500-L508));
trimming the index to the newest 400 local sessions drops entries and keeps their files. A
per-prompt history file is not stated. What remains is the chat editing state
(`chatEditingSessions/<key>/`, which files each request edited, with which model, whether the user
kept the edit, and the file before and after), the hook transcript and debug logs where they were
written, the memory tool files and, unless the sessions view's delete ran, the `session-store.db`
turns (texts cut to 1,000 and 5,000 characters) and the `cloudSessions.json` entry. That delete
removes both and asks GitHub to delete the remote copy only while sync is still on
([`remoteSessionExporter.ts:656-690`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L656-L690)),
so a session deleted after sync was turned off keeps its remote copy and loses its local marker;
neither delete path writes a log line. The analyzer reads the `cloudSessions.json` entries, which
also name sessions deleted here, and the `ownedTasks` list, but not the editing state,
`session-store.db`, the hook transcripts, the debug logs, the memory files or the index; the plan in
[section 8](#8-parser-plan) makes the editing state a primary source and the `session-store.db`
turns, the hook transcripts, the debug logs and the memory files secondary sources (see [Secondary
sources](../docs/output.md#secondary-sources)).

## 3. Record schema

[`common/model/chatModel.ts`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts).
Top level `ISerializableChatData3`
[`:2196-2227`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2196-L2227):
`version: 3`, `sessionId`, `creationDate` (ms epoch), `initialLocation`,
`requests: ISerializableChatRequestData[]`, `responderUsername`, `customTitle?`, `hasPendingEdits?`,
`inputState?`, `repoData?`, `pendingRequests?`, `workingDirectory?` (URI string). Written in that
order by `storageSchema`
([`chatSessionOperationLog.ts:203-216`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L203-L216)).

`ISerializableChatRequestData`
[`:2037-2094`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2037-L2094),
one user turn plus response: `requestId`, `timestamp?` (ms, request start),
`message: string | {text, parts[]}`
([`requestParser/chatParserTypes.ts:20-23`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/requestParser/chatParserTypes.ts#L20-L23)),
`variableData: {variables: [{id, name, fullName?, value, range?}]}`
([`attachments/chatVariableEntries.ts:63-75`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/attachments/chatVariableEntries.ts#L63-L75)),
`agent?: {id, name, fullName?, extensionId, ...}`
([`participants/chatAgents.ts:63-71`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/participants/chatAgents.ts#L63-L71)),
`modelId?` (user-selected model id,
[`chatServiceImpl.ts:1291`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts#L1291)),
`modeInfo?: {kind, telemetryModeId: 'ask'|'agent'|'edit'|'custom'|...}`
([`chatModel.ts:394-401`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L394-L401)),
`response: SerializedChatResponsePart[]`, `responseId?`, `responseTimestamp?` (ms),
`result?: {errorDetails?, timings?, metadata?}`, `modelState?`, `vote?`, `followups?`,
`usedContext?`, `contentReferences?`, `codeCitations?`, `promptTokens?`, `completionTokens?`,
`latestModelCall?`, `elapsedMs?`, `editedFileEvents?: [{uri, eventKind}]`, `isSystemInitiated?`,
`requestSource?`, `terminalExecutionId?`, `confirmation?`, deprecated `isHidden?`, `isCanceled?`.

Response parts
([`:2064`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2064)):
a bare `IMarkdownString` `{value, isTrusted?, ...}` for assistant text
([`chatSessionOperationLog.ts:45`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L45));
objects keyed by `kind`: `"thinking"` `{value?: string|string[], id?, reasoningDurationMs?}`
([`chatService.ts:635-644`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L635-L644));
`"toolInvocationSerialized"` `{toolCallId, toolId, invocationMessage, pastTenseMessage?, isComplete,
isConfirmed, resultDetails?` (URI[] or `{input: string, output: [...], isError?}`,
[`tools/languageModelToolsService.ts:283-290`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/tools/languageModelToolsService.ts#L283-L290)),
`resultError?`, `toolSpecificData?` (`{kind:'terminal', commandLine:{original, userEdited?}, cwd?}`
[`chatService.ts:686-700`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L686-L700);
`{kind:'input', rawInput}`
[`:847-850`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L847-L850)),
`subAgentInvocationId?}`
([`chatService.ts:1196-1215`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1196-L1215));
plus `textEditGroup`, `codeblockUri`, `progressMessage`, `confirmation`, `undoStop`,
`inlineReference` and others
([`chatSessionOperationLog.ts:62-95`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L62-L95)).
Tool call and result are the same object: the call is `toolCallId`, `toolId` and `toolSpecificData`,
the result is `resultDetails`, `resultError` and `isComplete`. No git branch field; `repoData` is
unspecified here.

### Tool confirmation and permission fields

Permission state on a tool invocation
([`chatService.ts:1204-1210`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1204-L1210)):
`isConfirmed` is `ConfirmedReason | boolean | undefined`, the boolean being the pre-1.104 form.
`ConfirmedReason`
([`:880-889`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L880-L889))
is an object whose `type` is a `ToolConfirmKind`, a `const enum`
([`:870-877`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L870-L877))
with no explicit values, so TypeScript inlines and serialises the declaration index: `Denied` 0,
`ConfirmationNotNeeded` 1, `Setting` 2, `LmServicePerTool` 3, `UserAction` 4, `Skipped` 5. Beside
`type`: `source` (`user`, `hook` or `riskAssessment`, the actor of a denial or skip, optional) for
`Denied` and `Skipped`; `reason` (string or markdown) for `ConfirmationNotNeeded`; `id` (the
setting) for `Setting`; `scope` (`session`, `workspace` or `profile`) for `LmServicePerTool`;
`selectedButton` and `selectedButtonKind` for `UserAction`. The invocation's own `source` field is a
different thing: the `ToolDataSource` the tool came from, undefined before 1.104, an object with
`type` (`extension`, `mcp`, `user`, `internal`, `external`) and `label`
([`tools/languageModelToolsService.ts:109-134`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/tools/languageModelToolsService.ts#L109-L134)).

The request's `modeInfo` also carries `permissionLevel`
([`chatModel.ts:397-405`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L397-L405)),
the `ChatPermissionLevel` the request ran under: `default` (the auto-approve settings apply),
`assisted` (approval decisions are delegated to a model), `autoApprove` (every tool call approved,
errors retried) and `autopilot` (as `autoApprove`, plus an internal stop hook that continues until
the task is done)
([`constants.ts:204-213`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/constants.ts#L204-L213)).
The field is in the type at `d7622a5` as well, so older `.jsonl` files can carry it. Beside
`modelId` each request has `modelConfiguration`, a dictionary of the selected model's options such
as context size or thinking effort
([`chatModel.ts:2157-2158`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2157-L2158)).
The session's `inputState`, the unsent draft, holds `selectedModel`
`{identifier, metadata, modelConfiguration?}` and `permissionLevel`
([`chatModel.ts:2422-2442`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2422-L2442),
[`:2293`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2293)).
Since `d7622a5` the session object gained `sessionCostInfo` `{credits, status?}`
([`:2299`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2299),
[`:2027-2030`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2027-L2030)).
`ToolConfirmKind` keeps the same six members in the same order at HEAD
([`chatService.ts:881-888`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L881-L888)),
and `ConfirmedReason` the same fields
([`:890-900`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L890-L900)).

A `confirmation` response part is `{kind: 'confirmation', title, message, data, buttons?, isUsed?}`
([`chatService.ts:514-522`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L514-L522)),
a question a chat participant puts to the user. Clicking a button sends a new request whose prompt
is `<label>: "<title>"` and whose `confirmation` is the button's label, and sets `isUsed`
([`browser/widget/chatContentParts/chatConfirmationContentPart.ts:42-60`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatConfirmationContentPart.ts#L42-L60));
the request field is a string
([`chatModel.ts:2084`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2084)).

### Cloud agent hand-off

A local chat delegated to the cloud agent ("Continue In" the cloud) leaves one `pullRequest`
response part in the local session,
`{kind: 'pullRequest', uri?, command, title, description, author, linkTag}`
([`chatService.ts:1243-1254`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1243-L1254),
a kind the operation log persists,
[`chatSessionOperationLog.ts:86`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts#L86)).
The extension fills it with the task's web URL as `uri` and as the argument of a `vscode.open`
command, and the task title as `title` and `linkTag`, with empty `description` and `author`
([`copilotCloudSessionsProvider.ts:1948-1960`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L1948-L1960)).
Before the task is created the chat history is summarised and sent with it
([`:1873-1876`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L1873-L1876)).

### JSONL framing

JSONL framing
([`common/model/objectMutationLog.ts:196-215`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/objectMutationLog.ts#L196-L215),
read
[`:340-385`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/objectMutationLog.ts#L340-L385)):
each line is `{"kind":0,"v":<full session>}` (Initial), `{"kind":1,"k":[path...],"v":...}` (Set),
`{"kind":2,"k":[...],"v":[items], "i"?:index}` (Push; `i` truncates from that index) or
`{"kind":3,"k":[...]}` (Delete). Replay in order to rebuild the object; `k` is a path of keys and
array indexes, for example `["requests",3,"response"]`.

## 4. Joins and timestamps

`workspaceStorage/<hash>/workspace.json` is `{"folder": "<file URI>"}` or
`{"workspace": "<.code-workspace URI>"}`
([`platform/storage/electron-main/storageMain.ts:416`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L416),[`472-474`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L472-L474));
the agents window also records `workingDirectory` in the session. Tool call and result share one
object; `toolCallId` is the join key to extension telemetry. `agent.id` and `responderUsername`
identify the participant (Copilot).

Times are in ms: `creationDate`, the request `timestamp` and `responseTimestamp`
([section 3](#3-record-schema)).

## 5. Other stores

`state.vscdb` (`ItemTable(key, value)`,
[`base/parts/storage/node/storage.ts:73`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/base/parts/storage/node/storage.ts#L73))
in `workspaceStorage/<hash>/` and `globalStorage/`
([`storageMain.ts:285`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L285),[`353`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L353),[`415`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/platform/storage/electron-main/storageMain.ts#L415)).
Keys: `interactive.sessions` is the legacy JSON blob of all sessions from before the file store
([`chatServiceImpl.ts:67`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts#L67),[`341`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts#L341),
migrated by
[`chatSessionStore.ts:611-633`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L611-L633));
`chat.ChatSessionStore.index` is `{version:1, entries:{<sessionId>:{sessionId, title,
lastMessageDate (ms), timing:{created, lastRequestStarted, lastRequestEnded}, workingDirectory?,
isEmpty?, isExternal?, ...}}}`
([`:39`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L39),[`780-836`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L780-L836));
`ChatSessionStore.transferIndex`
([`:40`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L40)).

An external session, one whose resource is not a local chat URI (a cloud agent task or another
provider's session), gets no file under `chatSessions/`: the store writes only its index entry,
keyed by the resource URI string rather than a session id
([`chatSessionStore.ts:405-418`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L405-L418)),
with `isExternal: true`
([`:802-805`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L802-L805),
[`:875-877`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L875-L877))
and `inputState`, the unsent draft
([`:813-818`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L813-L818)).
External entries are exempt from the 400-session trim
([`:441`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L441)).
A cloud agent entry's key is `copilot-cloud-agent:/task/<taskId>`
([`copilotCloudSessionsProvider.ts:495`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L495),
[`copilotCodingAgentUtils.ts:132-134`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode/copilotCodingAgentUtils.ts#L132-L134)).

### Sync state

Sync state, all written by the Copilot Chat extension under its global storage directory
`User/globalStorage/github.copilot-chat/` (`globalStorageUri`, lower-cased extension id) or its
global state:

- `cloudSessions.json`, a JSON object `{<local session id>: {cloudSessionId, cloudTaskId}}`, both
  strings
  ([`cloudSessionIdStore.ts:10-22`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionIdStore.ts#L10-L22),
  [`cloudSessionTypes.ts:28-31`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/common/cloudSessionTypes.ts#L28-L31),
  path from
  [`remoteSessionExporter.ts:277`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L277)).
  An entry is added when the cloud session is created, at the first agent turn of a session with
  sync on
  ([`remoteSessionExporter.ts:1066-1071`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L1066-L1071)),
  and the whole object is rewritten on each change
  ([`cloudSessionIdStore.ts:145-156`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionIdStore.ts#L145-L156)).
  A reconcile with the server, run before a delete or a reindex, adds an entry for every session the
  account's listing returns, so the file can also name sessions uploaded from another machine
  ([`:96-127`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionIdStore.ts#L96-L127),
  [`remoteSessionExporter.ts:244-258`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L244-L258)).
  A session never uploaded has no entry; the file is absent until the first upload. The key is the
  chat session id, the same id as `chatSessions/<sessionId>.jsonl` for a local chat: the sidebar's
  delete passes `LocalChatSessionUri.parseLocalSessionId` values to the delete command, which looks
  them up in this file
  ([`agentSessionsActions.ts:844-875`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/agentSessions/agentSessionsActions.ts#L844-L875)).
- `session-store.db`, the chronicle index, SQLite with tables `sessions(id, cwd, repository,
  host_type, branch, summary, agent_name, agent_description, created_at, updated_at)`,
  `turns(session_id, turn_index, user_message, assistant_response, timestamp)`, `checkpoints`,
  `session_files` and `session_refs`
  ([`services.ts:280-283`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/extension/vscode-node/services.ts#L280-L283),
  [`sessionStore.ts:194-250`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/platform/chronicle/node/sessionStore.ts#L194-L250)),
  written when `github.copilot.chat.localIndex.enabled` is on, its default
  ([`package.json:3227-3233`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/package.json#L3227-L3233)).
  Its `sessions.id` is the key of `cloudSessions.json`; the extension counts synced sessions by that
  join
  ([`remoteSessionExporter.ts:172-191`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L172-L191)).
  It holds no sync flag of its own.
- `github.copilot.cloudAgent.ownedTasks` in the extension's global state, which VS Code keeps as one
  JSON value in the `ItemTable` row keyed `GitHub.copilot-chat` of `User/globalStorage/state.vscdb`
  ([`extHostMemento.ts:117-118`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/api/common/extHostMemento.ts#L117-L118),
  [`extensionStorage.ts:175`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/extensionManagement/common/extensionStorage.ts#L175)):
  `{<taskId>: {recordedAt: <ms>, application?: <string>}}` (or a bare number, the older form), the
  newest 1,000 cloud agent tasks started or messaged from VS Code
  ([`cloudTaskOwnership.ts:8-14`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/cloudTaskOwnership.ts#L8-L14),
  [`:36-63`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/cloudTaskOwnership.ts#L36-L63)).
  `application` is `vscode` for a task created here, else the task's `event_type` or
  `github/autopilot`
  ([`copilotCloudSessionsProvider.ts:2766-2772`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts#L2766-L2772)).
  Each task is a session held on GitHub's servers that this install started or messaged, so it marks
  a synced session in the sense of the parser plan ([section 8](#8-parser-plan)), and one whose
  origin is remote: it began on the vendor's side and is only listed here.

### Standing permission grants

From the source review of 2026-10-19:

"Always allow" choices are kept in `ItemTable` rows, not in the session. `ToolConfirmStore` writes
five keys, each a JSON object keyed by tool id (or MCP server id) whose value is `true`, a label
string, or `{label, arguments}`; older builds wrote a JSON array of ids
([`languageModelToolsConfirmationService.ts:139-190`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/tools/languageModelToolsConfirmationService.ts#L139-L190),
[`:240-244`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/tools/languageModelToolsConfirmationService.ts#L240-L244)):
`chat/autoconfirm` (run without approval), `chat/autoconfirm-post` (continue without reviewing the
result), `chat/servers/autoconfirm` and `chat/servers/autoconfirm-post` (the same for every tool of
an MCP server) and `chat/autoconfirm-combination`. Each key exists in workspace scope, the
workspace's `workspaceStorage/<hash>/state.vscdb`, and in profile scope, `globalStorage/state.vscdb`
for the default profile
([`:49-50`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/tools/languageModelToolsConfirmationService.ts#L49-L50));
a session-scope grant is held in memory only. These are the grants whose per-call record is
`LmServicePerTool` with `scope` `workspace` or `profile`. Two more keys:
`chat.tools.global.autoApprove.optIn` (application scope, `true` once the user accepted the warning
for global auto-approve,
[`languageModelToolsService.ts:73`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/tools/languageModelToolsService.ts#L73),
[`:1526`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/tools/languageModelToolsService.ts#L1526))
and `chat.externalPath.workspaceAllowlist` (workspace scope, a JSON array of paths outside the
workspace the user allowed,
[`chatExternalPathConfirmation.ts:22-30`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/tools/builtinTools/chatExternalPathConfirmation.ts#L22-L30),
[`:58`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/tools/builtinTools/chatExternalPathConfirmation.ts#L58)).
The settings behind the same decisions live in `User/settings.json` (and a profile's):
`chat.tools.global.autoApprove`, `chat.tools.edits.autoApprove`, `chat.tools.urls.autoApprove`,
`chat.tools.eligibleForAutoApproval`
([`constants.ts:72-75`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/constants.ts#L72-L75)),
`chat.permissions.default`
([`:135`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/constants.ts#L135)),
`chat.tools.terminal.enableAutoApprove` and `chat.tools.terminal.autoApprove`
([`terminalChatAgentToolsConfiguration.ts:46-47`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/terminalContrib/chatAgentTools/common/terminalChatAgentToolsConfiguration.ts#L46-L47)),
and the default model `chat.defaultModel`
([`constants.ts:138`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/constants.ts#L138)).

### Chat editing sessions

Chat editing sessions (VS Code core),
`User/workspaceStorage/<hash>/chatEditingSessions/<key>/state.json` with the file bodies in
`contents/<hash>`
([`chatEditingSessionStorage.ts:22-23`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingSessionStorage.ts#L22-L23),
[`:43-47`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingSessionStorage.ts#L43-L47)).
`<key>` is the chat session id for a local chat, else the SHA-1 of the session resource
([`chatEditingOperations.ts:137-146`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingOperations.ts#L137-L146)).
`state.json` is `{version: 2, recentSnapshot, timeline, initialFileContents}`; a snapshot entry is
`{resource, languageId, originalHash, currentHash, state, snapshotUri, telemetryInfo: {requestId,
agentId?, command?, modelId?, modeId?, feature?}, isDeleted?}`
([`:242-288`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingSessionStorage.ts#L242-L288)).
`state` is the `ModifiedFileEntryState` const enum, serialised as its index: `Modified` 0,
`Accepted` 1, `Rejected` 2
([`chatEditingService.ts:353-357`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/editing/chatEditingService.ts#L353-L357)).
So it says which file each request edited, with which model, whether the user kept or undid the
edit, and the file before and after. It joins the session on session id and `requestId`. It survives
the chat's deletion: only `stop(true)` removes the folder
([`chatEditingSession.ts:492-497`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingSession.ts#L492-L497),
[`chatEditingSessionStorage.ts:205-213`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingSessionStorage.ts#L205-L213)),
and no caller passes `true`: the only call is `stop()`
([`chatEditingServiceImpl.ts:93`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/browser/chatEditing/chatEditingServiceImpl.ts#L93);
`stop(true)` and `.clearState(` grepped in `src/vs/workbench/contrib/chat`).

### Copilot Chat's chronicle index

Copilot Chat's chronicle index `globalStorage/github.copilot-chat/session-store.db` ([Sync
state](#sync-state) names it for the sync join) is also a copy of the conversation:
`turns(session_id, turn_index, user_message, assistant_response, timestamp)`, `checkpoints`
(compaction summaries: `title`, `overview`, `history`, `work_done`, `technical_details`,
`important_files`, `next_steps`), `session_files(file_path, tool_name, turn_index, first_seen_at)`,
`session_refs` and an FTS5 table `search_index`
([`sessionStore.ts:194-271`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/platform/chronicle/node/sessionStore.ts#L194-L271)).
The texts are cut to 1,000 characters for the user message and 5,000 for the response
([`sessionStoreTracking.ts:17-23`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chronicle/common/sessionStoreTracking.ts#L17-L23)),
so a match against the session on text needs a prefix rule. Written by default
(`github.copilot.chat.localIndex.enabled`, default `true`,
[`package.json:3227-3233`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/package.json#L3227-L3233));
without a global storage directory it falls back to `<OS temp>/copilot-session-store.db`, outside
the home
([`services.ts:280-283`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/extension/vscode-node/services.ts#L280-L283)).
Its rows are removed only by the sessions view's delete, which runs `_deleteSessionsFromCloud`
([`remoteSessionExporter.ts:656-669`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L656-L669)),
so a chat deleted another way keeps its turns here. `sessions.id` is the chat session id.

### Hook transcripts

Hook transcripts, `workspaceStorage/<hash>/GitHub.copilot-chat/transcripts/<sessionId>.jsonl`
([`sessionTranscriptService.ts:58-67`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/sessionTranscriptService.ts#L58-L67),
[`:88`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/sessionTranscriptService.ts#L88)):
one JSON object per line, `{type, data, id, timestamp (ISO 8601), parentId}`
([`platform/chat/common/sessionTranscriptService.ts:16-27`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/platform/chat/common/sessionTranscriptService.ts#L16-L27)),
with types `session.start` (`sessionId`, `version` 1, `producer` `copilot-agent`, `copilotVersion`,
`vscodeVersion`, `startTime`, `context.cwd`), `user.message`, `assistant.turn_start`,
`assistant.message`, `tool.execution_start`, `tool.execution_complete` and `assistant.turn_end`
([`sessionTranscriptService.ts:118-200`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/sessionTranscriptService.ts#L118-L200)).
Written only when the agent loop has hooks configured
([`toolCallingLoop.ts:1200-1222`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/intents/node/toolCallingLoop.ts#L1200-L1222)),
the newest 20 per workspace kept
([`sessionTranscriptService.ts:23`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/sessionTranscriptService.ts#L23),
[`:239-275`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/sessionTranscriptService.ts#L239-L275)).
Independent of the chat file, so it survives the chat's deletion.

### Debug logs

Debug logs, `workspaceStorage/<hash>/GitHub.copilot-chat/debug-logs/<sessionId>/main.jsonl`,
`<label>-<childSessionId>.jsonl` for a subagent, and `models.json`
([`chatDebugFileLoggerService.ts:24-30`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/chatDebugFileLoggerService.ts#L24-L30),
[`:295-296`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/chatDebugFileLoggerService.ts#L295-L296),
[`:563-564`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chat/vscode-node/chatDebugFileLoggerService.ts#L563-L564)):
entries of type `session_start`, `user_message`, `agent_response`, `tool_call` and
`child_session_ref`, up to 100 MB per session and the newest 50 sessions. Off unless the
experiment-controlled setting registered as `chat.chatDebug.fileLogging.enabled` (default `false`)
turns it on
([`configurationService.ts:843`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/platform/configuration/common/configurationService.ts#L843)).

### Memory tool files

Memory tool files: `globalStorage/github.copilot-chat/memory-tool/memories/` (user scope),
`workspaceStorage/<hash>/GitHub.copilot-chat/memory-tool/memories/repo/` and
`.../memory-tool/memories/<sessionId>/`
([`tools.ts:71`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/tools/vscode-node/tools.ts#L71),
[`:92`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/tools/vscode-node/tools.ts#L92),
[`:115`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/tools/vscode-node/tools.ts#L115)):
notes the model wrote with its memory tool, with no time of their own beyond the file's.

### The session index

The session index `chat.ChatSessionStore.index`: trimming keeps the newest 400 local sessions in the
index and deletes the other entries, not their files
([`chatSessionStore.ts:37`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L37),
[`:438-452`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L438-L452)),
so `chatSessions/` can hold more files than the index names. An external entry is the only local
record of a cloud or other provider's session title and times; the parser does not read the index.

## 6. Format versions

`version` absent means v1, `2` adds `computedTitle`, `3` adds `customTitle`;
`normalizeSerializableChatData`
([`chatModel.ts:2422-2461`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2422-L2461))
fills a missing `sessionId` or `creationDate` (defaulting to one year ago). `message` may be a plain
string in old data
([`:2069`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatModel.ts#L2069));
`response` may be a string or string[]
([`chatSessionStore.ts:688-699`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L688-L699)).
Storage moved from `state.vscdb` to `.json` to `.jsonl` (1.109 and later); flat `.json` is still
read as a fallback
([`:653-675`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L653-L675)).
`isConfirmed` was boolean before 1.104; `source` was undefined before 1.104
([`chatService.ts:1204-1209`](https://github.com/microsoft/vscode/blob/d7622a529314a4abcefd7ca9e3d7344bc9ccba9e/src/vs/workbench/contrib/chat/common/chatService/chatService.ts#L1204-L1209)).

## 7. Secrets

`variableData.variables[].value` and `usedContext` may hold attached file contents;
`toolSpecificData.rawInput` and `commandLine` may hold command-line secrets. `state.vscdb` stores
extension auth material under other keys (out of scope here; see the Cursor and Windsurf notes in
[`collectors/docs/coverage.md`](../../collectors/docs/coverage.md#credentials)).

Session sync uses no credential file of its own: each request goes to the `api` endpoint named in
the Copilot token, the short-lived token the extension exchanges for the user's GitHub sign-in
([`cloudSessionApiClient.ts:329-341`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionApiClient.ts#L329-L341)),
and `cloudSessions.json` holds only ids. Uploaded events pass a filter that replaces known token
values and token patterns
([`secretFilter.ts:117-172`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/common/secretFilter.ts#L117-L172)).

## 8. Parser plan

Globs: `**/User/workspaceStorage/*/chatSessions/*.{json,jsonl}`,
`**/User/globalStorage/emptyWindowChatSessions/*.{json,jsonl}`,
`**/User/workspaceStorage/no-workspace/chatSessions/*.json`,
`**/User/globalStorage/transferredChatSessions/*.json`, plus the sibling `workspace.json`.

Rows: one `user` per request, one `assistant` per contiguous markdown run, one `thinking` per
thinking part, one `tool_use` plus `tool_result` per `toolInvocationSerialized`.

| Column | Source |
| --- | --- |
| timestamp_utc | `timestamp` for the user row, `responseTimestamp` for response parts (ms) |
| session_id | `sessionId` |
| project_path | `workingDirectory`, else `workspace.json` `folder` (file URI to path); never `workspace` |
| git_branch | empty |
| model | `modelId` |
| tool_name, tool_use_id | `toolId`, `toolCallId` |
| text | text, `invocationMessage` or `commandLine.original` |

### Permission state

Rows written today, all `system` (issues 96 and 97):

- `permission mode: <mode>` and `permission mode: <old> -> <new>` from the request
  `modeInfo.telemetryModeId` (`ask`, `agent`, `edit`, `custom`), placed and timed the same way.
- `permission decision: confirmed=<value>` after a tool invocation's `tool_result` row, with its
  `toolCallId` and `toolId`: `<value>` is `true` or `false` for the boolean form, else the
  `ToolConfirmKind` name and number (`UserAction(4)`), followed by the `ConfirmedReason`'s other
  fields as `key=value` (`reason` last), and `tool_source=<type>` from the invocation's `source`. An
  invocation without `isConfirmed` gets no row.
- `permission decision: confirmation isUsed=<bool> buttons=<list> title=<title>` and the part's
  `message` on the next line, for a `confirmation` response part, at the response time.
- `permission decision: confirmation=<label>` after the user row of a request whose `confirmation`
  is set.

The `chat.*` auto-approve settings in `settings.json` are not read. Their keys are now recorded
under [Standing permission grants](#standing-permission-grants).

Additions from the source review of 2026-10-19:

- Permission: `permission level: <level>` and `permission level: <old> -> <new>` from
  `modeInfo.permissionLevel`, placed and timed like the `permission mode` rows; one `system` row per
  entry of the five `chat/autoconfirm*` keys, `chat.tools.global.autoApprove.optIn` and
  `chat.externalPath.workspaceAllowlist`, from each `state.vscdb`, timestamped by the database's
  modification time and saying so; one row per auto-approve key set in `User/settings.json`, the
  same way.

### Model

Rows written today, all `system` (issues 96 and 97):

- `model: <id>` at the first request whose `modelId` is set and `model: <old> -> <new>` on every
  later request with a different `modelId`, before the request's user row, with its `timestamp`. The
  model is chosen per request, so a session can change model at any request.

Additions from the source review of 2026-10-19:

- Model: append the request's `modelConfiguration` (as `key=value`) to its `model:` row when
  present; the session's `inputState.selectedModel` is a draft, not a record of use, and gets no
  row.

### Past use and secondary sources

Additions from the source review of 2026-10-19:

- Past use, by role: `chatEditingSessions/<key>/state.json` primary for its accept and reject states
  (`edit state: <Modified|Accepted|Rejected> <resource> request=<requestId> model=<modelId>`, at the
  file's modification time) and the files a request touched; `session-store.db` `turns`,
  `checkpoints` and `session_files` secondary (truncated texts, own `timestamp`);
  `transcripts/<sessionId>.jsonl` secondary (own `timestamp`); `debug-logs/<sessionId>/*.jsonl`
  secondary; memory files secondary with an empty timestamp. Each needs `has_secondary` and a
  `secondary()` match.

### Sync, relay and origin

Sync: Copilot Chat's session sync uploads chat sessions to the user's GitHub account and marks each
uploaded session in `User/globalStorage/github.copilot-chat/cloudSessions.json`
([section 5](#5-other-stores)). It runs when `chat.sessionSync.enabled` is on, a core setting whose
default is `false` but which is tagged experimental with `experiment: {mode: 'auto'}`, so an
experiment can turn it on, and which the organisation policy `CopilotSessionSync` can force off
([`chat.shared.contribution.ts:830-851`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/chat.shared.contribution.ts#L830-L851)),
and when `github.copilot.chat.localIndex.enabled` is on, which it is by default
([`remoteSessionExporter.ts:320-366`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L320-L366)).
A session is uploaded only when the workspace resolves to a GitHub repository not matched by
`chat.sessionSync.excludeRepositories`
([`:905-961`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L905-L961),
[`sessionIndexingPreference.ts:48-65`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/common/sessionIndexingPreference.ts#L48-L65)).
What leaves is a cloud session created at the first agent turn (`POST /agents/sessions` with the
repository's owner and repository ids and the local session id), then the turns as Copilot
CLI-compatible events (`session.start`, `user.message`, `assistant.message`, `tool.execution_start`,
`tool.execution_complete`) posted to `/agents/sessions/<id>/events` about 500 ms after each turn
ends
([`cloudSessionApiClient.ts:152-199`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionApiClient.ts#L152-L199),
[`remoteSessionExporter.ts:49`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L49)).
`/chronicle reindex` and the `github.copilot.chronicle.reindex` command also upload past sessions
that have no entry yet
([`sessionReindexer.ts:349-376`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/sessionReindexer.ts#L349-L376)).
The parser yields one `system` row per `cloudSessions.json` entry, `session synced: remote session
<cloudSessionId> task <cloudTaskId> (from User/globalStorage/github.copilot-chat/cloudSessions.json,
file mtime)`, with the entry's key as `session_id`, timestamped by the file's modification time; an
entry with no local session is still a row, since it names a session deleted here or uploaded from
another machine. The `ownedTasks` list of cloud agent tasks ([section 5](#5-other-stores)) is the
other remote record: one `system` row per entry, `session synced: cloud agent task <taskId>
application=<application or -> (from state.vscdb GitHub.copilot-chat
github.copilot.cloudAgent.ownedTasks, recordedAt)` at `recordedAt`, with `session_id`
`copilot-cloud-agent:/task/<taskId>` to match the index entry; the older bare-number form is read as
`recordedAt` with no `application`. A task is a `session synced:` row although nothing was uploaded
from the host: it began on GitHub's servers, and GitHub holds its copy as it holds an uploaded
session's, so for a responder it is a session the vendor can still produce. Its session reads
`synced` `yes`. Only the origin differs, and it is a second row at the same time and session:
`session origin: remote GitHub cloud agent (from state.vscdb GitHub.copilot-chat
github.copilot.cloudAgent.ownedTasks, recordedAt)`. The parser sets `records_origin`, so a task's
session reads `origin` `remote` and every other VS Code session `local`. Both rows are fixture only:
no real install has shown either file. A delete removes the marker. The sidebar's delete of a local
session calls `github.copilot.sessionSync.deleteSessionFromCloud`, which deletes the session's
`session-store.db` rows and its `cloudSessions.json` entry, and sends
`DELETE /agents/tasks/<cloudTaskId>` only while sync is still on, so a session deleted after sync
was turned off keeps its remote copy and loses its local marker
([`remoteSessionExporter.ts:656-690`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L656-L690),
[`cloudSessionApiClient.ts:286-287`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/node/cloudSessionApiClient.ts#L286-L287)).
The Delete Session Sync Data command (`github.copilot.sessionSync.deleteSessions`) offers local and
cloud or cloud only; both remove the entry
([`remoteSessionExporter.ts:545-616`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/extensions/copilot/src/extension/chronicle/vscode-node/remoteSessionExporter.ts#L545-L616)).
Neither path writes a log line: the exporter reports through telemetry only. VS Code Settings Sync
does not carry chat sessions. Its resources are settings, keybindings, snippets, prompt files,
tasks, MCP configuration, extensions, global state and profiles
([`userDataSync.ts:169-181`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSync.ts#L169-L181));
global state carries only keys stored with the `USER` target
([`globalStateSync.ts:296-304`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/globalStateSync.ts#L296-L304)),
and the chat session index and every extension's state are stored with the `MACHINE` target
([`chatSessionStore.ts:425`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/common/model/chatSessionStore.ts#L425),
[`extensionStorage.ts:175`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/extensionManagement/common/extensionStorage.ts#L175)).
Its local state, `User/sync/<resource>/lastSync<resource>.json`
(`{ref, syncData: {version, machineId?, content}}`) and the timestamped `<yyyymmddThhmmss>.json`
backups kept 30 days by default (`sync.localBackupDuration`)
([`userDataSync.ts:187-189`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSync.ts#L187-L189),
[`:457-466`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSync.ts#L457-L466),
[`userDataSyncLocalStoreService.ts:99-125`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/userDataSync/common/userDataSyncLocalStoreService.ts#L99-L125)),
records that settings, prompt files and MCP configuration were synced, not sessions, and gets no
row. Export Chat (`workbench.action.chat.export`) writes the session as JSON to a file the user
picks, `chat.json` by default, and uploads nothing
([`chatImportExport.ts:23`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/actions/chatImportExport.ts#L23),
[`:42-79`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/workbench/contrib/chat/browser/actions/chatImportExport.ts#L42-L79));
no share command was found (searched `share`, `shareChat` and `ShareSession` in
`src/vs/workbench/contrib/chat` and `extensions/copilot/src`). Copilot CLI sessions run in VS Code's
agent host pass the same setting to the Copilot SDK as `enableRemoteSessions`
([`copilotAgent.ts:3846`](https://github.com/microsoft/vscode/blob/661e013024de5052af476650250dabbebb4c1165/src/vs/platform/agentHost/node/copilot/copilotAgent.ts#L3846))
and keep their state under `~/.copilot/session-state/`, where the `copilot-cli` parser reads the
sync marker ([`analyzer/research/copilot-cli.md`](copilot-cli.md#8-parser-plan)).

Additions from the source review of 2026-10-19:

- Sync, relay and origin: no change.

### Scratch directories

Additions from the source review of 2026-10-19:

- Scratch directories: the session's project was `workspace.json`'s `folder` or `workspace` before
  `workingDirectory` ([`vscode.py`](../doubleagent/parsers/vscode.py) `_workspace_folder`). A chat
  in the Agents window runs in the workspace `User/agent-sessions.code-workspace`
  ([`environmentService.ts:280-281`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/src/vs/platform/environment/common/environmentService.ts#L280-L281)),
  so its project would be that file, under the catalog's `User` entry, which the analyzer classes as
  a scratch directory, while the real project is in `workingDirectory`. Since issue 185 the parser
  takes the session's `workingDirectory` first, then `workspace.json`'s `folder`, and never the
  `workspace` value, which names a `.code-workspace` file rather than a directory (a user's
  multi-root workspace file as well as the Agents window's); the workspace file is named in the
  session-start row as `workspace=<path>`, and a `workspace.json` that cannot be read or is not a
  JSON object gives a `parser: workspace.json not read (<reason>)` or
  `parser: workspace.json is not a JSON object` row. That the Agents window's chats are stored under
  that workspace's hash follows from the store's rule ([section 2](#2-transcript-stores)) and was
  not traced further; it is unconfirmed on an install. An empty-window chat has no project. The
  worktrees VS Code makes for Copilot CLI sessions, `<repo parent>/<repo>.worktrees/<branch>` unless
  the git extension's global state holds a `worktreeRoot:<repo>` root
  ([`extensions/git/src/repository.ts:1952-1970`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/git/src/repository.ts#L1952-L1970),
  [`chatSessionWorktreeServiceImpl.ts:113`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorktreeServiceImpl.ts#L113)),
  are recorded in `~/.copilot/session-state/<id>/vscode.metadata.json`
  ([`chatSessionMetadataStoreImpl.ts:186`](https://github.com/microsoft/vscode/blob/4d22f4f922eb012217ac65672ccce02f59d63706/extensions/copilot/src/extension/chatSessions/copilotcli/vscode-node/chatSessionMetadataStoreImpl.ts#L186)),
  which belongs to the `copilot-cli` parser.

### Deletion

Additions from the source review of 2026-10-19:

- Deletion: see [What survives a delete](#what-survives-a-delete); a session-store, transcript or
  editing-state record with no chat file is a deleted chat.

### Bad lines

Additions from the source review of 2026-10-19:

- Bad lines: the transcript and debug-log readers go through `iter_jsonl` and `error_rows`;
  `state.json` and `session-store.db` errors are whole-file `parser:` rows.

### Fixtures

Fixture `chatSessions/9ab.jsonl`:

```jsonl
{"kind":0,"v":{"version":3,"creationDate":1759400000000,"customTitle":null,"initialLocation":"panel","responderUsername":"GitHub Copilot","sessionId":"9ab","requests":[{"requestId":"request_1","timestamp":1759400001000,"message":{"text":"run tests","parts":[]},"agent":{"id":"github.copilot.default","name":"GitHub Copilot","extensionId":{"value":"GitHub.copilot-chat"}},"modelId":"copilot/gpt-4.1","modeInfo":{"kind":"agent","telemetryModeId":"agent","isBuiltin":true},"variableData":{"variables":[]},"response":[{"kind":"thinking","value":"Need pytest","id":"t1"},{"kind":"toolInvocationSerialized","toolCallId":"call_a","toolId":"run_in_terminal","invocationMessage":"Running command","isComplete":true,"isConfirmed":true,"toolSpecificData":{"kind":"terminal","commandLine":{"original":"pytest"}},"resultDetails":{"input":"pytest","output":[{"type":"embed","value":"3 passed"}]}},{"value":"All tests pass."}],"responseId":"response_1","responseTimestamp":1759400002000,"modelState":{"value":"complete"}}],"workingDirectory":"file:///home/u/proj"}}
{"kind":2,"k":["requests"],"v":[{"requestId":"request_2","timestamp":1759400010000,"message":{"text":"thanks","parts":[]},"variableData":{"variables":[]},"response":[{"value":"You're welcome."}]}]}
```

`workspace.json`: `{"folder": "file:///home/u/proj"}`
