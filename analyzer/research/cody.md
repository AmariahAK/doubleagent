# Sourcegraph Cody transcript schema

Catalog agent: `cody`. Cody keeps all chats of all accounts in one JSON
object, `AccountKeyedChatHistory`, stored under the key
`cody-local-chatHistory-v2`. In VS Code that object sits inside the
`sourcegraph.cody-ai` row of `User/globalStorage/state.vscdb`; in the
JetBrains plugin it is a file of the same name, and the `cody chat` CLI
keeps it in memory only. Source is the
frozen public snapshot, so later releases may differ. Paths are in
[`collectors/research/cody.md`](../../collectors/research/cody.md).

## 1. Source

[sourcegraph/cody-public-snapshot](https://github.com/sourcegraph/cody-public-snapshot) at
[`8e20ac6c1460c08b0db581c0204658112a246eda`](https://github.com/sourcegraph/cody-public-snapshot/commit/8e20ac6c1460c08b0db581c0204658112a246eda)
(2025-08-01), archived copy of the now-private Cody repository
([`README.md:1-5`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/README.md#L1-L5)).

- **Source review (2026-10-19)**: the repository's HEAD on 2026-10-19 is
  still
  [`8e20ac6`](https://github.com/sourcegraph/cody-public-snapshot/commit/8e20ac6c1460c08b0db581c0204658112a246eda),
  committed 2025-08-01, the commit this document already cited. The
  public source has been frozen since August 2025, so this review is of
  the VS Code extension 1.116.0, the JetBrains plugin and the agent as of
  that date; nothing later can be read from source. Deep Cody, named
  below, is the agentic context mode in which a helper model gathers
  context with tools before the chat model answers. Per class:
  - Permission state: found. Deep Cody's terminal confirmations are
    `processes[]` entries of type `confirmation` stored on the human
    message; a refusal leaves `state` `error` with `error.message`
    `Command rejected`, an approval leaves `pending`. The agentic chat
    (`intent` `agentic`) runs its tools, the shell included, with no
    per-call prompt. Standing settings are
    `cody.agentic.context.experimentalOptions.shell.allow` and `.block`,
    the deprecated `cody.agentic.context.experimentalShell`, and
    `cody.mcpServers.<server>.disabled` and `.disabledTools` in the
    editor's user `settings.json`; the parser names a refusal
    `rejected` and a `pending` step `approved or unanswered`, and reads
    no setting ([section 3](#3-record-schema), [section 8](#8-parser-plan)).
    No real install has shown a confirmation step: the layout the parser
    handles is not observed on any real install, source-derived
    (sourcegraph/cody-public-snapshot at
    [`8e20ac6`](https://github.com/sourcegraph/cody-public-snapshot/commit/8e20ac6c1460c08b0db581c0204658112a246eda)).
  - Model: already covered per assistant message; found the
    `cody-model-preferences` global-state key (the selected and default
    model per endpoint and usage) and the per-chat `llm` element of the
    JetBrains plugin's legacy history, which the parser does not read
    ([section 2](#2-transcript-files)).
  - Past use beyond the primary store: found. The JetBrains plugin's
    pre-agent history `cody_history.xml` in each project's `.idea/` is
    copied once into the agent store and never deleted, so it outlives a
    delete or clear in the plugin; it is neither collected nor parsed.
    A deprecated `cody-chat-memory` key is cleared at every activation.
    Export files go wherever the user saves them
    ([section 2](#2-transcript-files)).
  - Sync, relay and origin: already covered (none recorded locally);
    added that the agentic chat's `cody.runTerminalCommand` and
    `cody.tool-use` telemetry events carry each tool call's arguments
    ([section 8](#8-parser-plan)).
  - Scratch directories: none. Both the Deep Cody terminal tool and the
    agentic `run_terminal_command` run in the first workspace folder.
  - Deletion: found. Clear empties only the signed-in account's chats in
    the shared object, delete removes one chat key; neither leaves a
    marker ([section 8](#8-parser-plan)).
  - Version drift: none at the source level. The parser's keys
    (`sourcegraph.cody-ai`, `cody-local-chatHistory-v2`, the message and
    process fields) are at the cited lines; whether builds after August
    2025 still write them cannot be determined from source.
  - Bad lines: already covered. Both inputs are one JSON value and the
    parser recovers a damaged history chat by chat; the uncollected
    legacy XML has no reader to drop lines.

## 2. Transcript files

- VS Code (and forks): `<User>/globalStorage/state.vscdb`, table
  `ItemTable`, row `key = 'sourcegraph.cody-ai'`; `value` is the
  extension's whole global state as JSON
  ([PearAI VS Code fork `extensionStorage.ts:170-175`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/platform/extensionManagement/common/extensionStorage.ts#L170-L175)),
  and `value["cody-local-chatHistory-v2"]` is the history
  ([`vscode/src/services/LocalStorageProvider.ts:29`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L29),
  [`190-212`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L190-L212)).
  Collected today under `vscode`.
- JetBrains: `<Cody-nodejs data>/JetBrains-globalState/cody-local-chatHistory-v2`,
  a file whose whole content is the JSON-encoded history
  ([`agent/src/global-state/AgentGlobalState.ts:115-121`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/AgentGlobalState.ts#L115-L121),
  [`134-140`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/AgentGlobalState.ts#L134-L140)).
  Home-relative globs: `.local/share/Cody-nodejs/JetBrains-globalState/cody-local-chatHistory-v2`,
  `Library/Application Support/Cody-nodejs/JetBrains-globalState/...`,
  `AppData/Local/Cody-nodejs/Data/JetBrains-globalState/...`.
- The whole history is rewritten on every save
  ([`vscode/src/chat/chat-view/ChatHistoryManager.ts:94-108`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatHistoryManager.ts#L94-L108)).
- The `cody chat` CLI writes no history. Its client info asks for no
  global-state capability
  ([`agent/src/cli/command-chat.ts:141-158`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-chat.ts#L141-L158)),
  so the agent opens its global state without a directory
  ([`agent/src/agent.ts:1470-1480`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/agent.ts#L1470-L1480)),
  which is an in-memory database
  ([`AgentGlobalState.ts:23-33`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/AgentGlobalState.ts#L23-L33)).

Other sources of past use and model state (source review of 2026-10-19):

- **Legacy JetBrains history, secondary.** Before the plugin ran the
  agent, it kept chats in a project-level persistent component,
  `HistoryService`, stored as `cody_history.xml`
  ([`jetbrains/.../history/HistoryService.kt:13-15`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/history/HistoryService.kt#L13-L15)).
  The IntelliJ Platform keeps a project-level component's file in the
  project's `.idea/` directory, so the path is
  `<project>/.idea/cody_history.xml` (platform behaviour, not re-read
  from platform source here). Each `<chat>` has `internalId`,
  `updatedAt`, `messages` of `<message>` with `text` and `speaker`
  (`HUMAN`, `ASSISTANT`), the deprecated `model` and `accountId`, an
  `llm` element (`model`, `title`, `provider`, `tags`, `usage`) and
  `enhancedContext`
  ([`history/state/ChatState.kt:13-31`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/history/state/ChatState.kt#L13-L31),
  [`MessageState.kt:10-20`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/history/state/MessageState.kt#L10-L20),
  [`LLMState.kt:10-18`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/history/state/LLMState.kt#L10-L18)).
  The run-once migration `CodyMigrateChatHistory-v2`
  ([`config/migration/SettingsMigration.kt:69-71`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/config/migration/SettingsMigration.kt#L69-L71))
  copies it into the agent store through `chat/import` with merge on,
  keyed `<server url>-<account name>` with `updatedAt` as both the chat
  id and `lastInteractionTimestamp`, the chat's `llm.model` on every
  message, and only complete human and assistant pairs
  ([`ChatHistoryMigration.kt:17-79`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/jetbrains/src/main/kotlin/com/sourcegraph/cody/config/migration/ChatHistoryMigration.kt#L17-L79)).
  Nothing deletes the XML, so it survives a delete or clear of the
  migrated chat in the agent store, and it is the only record of a
  dropped unpaired message. It names the project by where it sits. It
  joins the primary store on account key, chat id (`updatedAt`) and
  message text.
- **`cody-model-preferences`, a model setting.** A global-state key
  (`sourcegraph.cody-ai` row in VS Code, a file of that name under
  `JetBrains-globalState/` for the plugin) holding, per endpoint,
  `defaults` and `selected`, each a map from usage (`chat`, `edit`,
  `autocomplete`, `unlimitedChat`) to model id
  ([`LocalStorageProvider.ts:37`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L37),
  [`338-344`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L338-L344);
  [`lib/shared/src/models/modelsService.ts:198-219`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/models/modelsService.ts#L198-L219),
  [`545`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/models/modelsService.ts#L545);
  [`lib/shared/src/models/types.ts:3-8`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/models/types.ts#L3-L8)).
  It records the user's current choice, not when it was made. Deep
  Cody's helper model is chosen at run time and recorded nowhere
  ([`DeepCodyHandler.ts:162-167`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/handlers/DeepCodyHandler.ts#L162-L167)).
- **`cody-chat-memory`, gone.** Listed as a deprecated key that
  `clearDeprecatedKeys` sets to null whenever the storage is attached at
  activation
  ([`LocalStorageProvider.ts:42-46`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L42-L46),
  [`63-72`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L63-L72),
  [`374-384`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L374-L384)).
  Its earlier content is not in the snapshot (no other reference found
  for `cody-chat-memory` or `CODY_CHAT_MEMORY`); a `state.vscdb` from a
  build that predates the cleanup may still hold it.
- No other mirror, index, backup or archive of chats: the `symf` index
  holds code, not chats, and export writes only where the user saves.

## 3. Record schema

`AccountKeyedChatHistory` = `{ "<endpoint>-<username>": { "chat": { "<chatID>": SerializedChatTranscript } } }`
([`lib/shared/src/chat/transcript/messages.ts:193-204`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/messages.ts#L193-L204);
key built at [`LocalStorageProvider.ts:393-397`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L393-L397)).
The endpoint is a URL such as `https://sourcegraph.com/`, so split the key
on the last `-` only with care: usernames may contain hyphens, endpoints
rarely end in one.

`SerializedChatTranscript`
([`lib/shared/src/chat/transcript/index.ts:7-24`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/index.ts#L7-L24)):
`id`, `chatTitle?`, `lastInteractionTimestamp`, `interactions[]` of
`{humanMessage, assistantMessage|null}`. `id` and
`lastInteractionTimestamp` are both the chat's **creation** time as
`Date.toUTCString()`, e.g. `"Fri, 03 Oct 2026 10:00:00 GMT"` (UTC, second
resolution), despite the name
([`vscode/src/chat/chat-view/ChatBuilder.ts:97`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatBuilder.ts#L97),
[`337-341`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatBuilder.ts#L337-L341)).
Chats whose human message errored are not saved
([`ChatBuilder.ts:325-331`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatBuilder.ts#L325-L331)).

`SerializedChatMessage`
([`messages.ts:156-171`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/messages.ts#L156-L171);
serialiser [`index.ts:26-42`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/index.ts#L26-L42)):
`speaker` (`human`, `assistant`, `system`), `text`, `model`,
`intent` (`search`, `chat`, `edit`, `insert`, `agentic`),
`manuallySelectedIntent`, `contextFiles` (context items with `type`,
`uri`, `content`, ...), `editorState`, `error` (`ChatError`:
`name`, `message`, rate-limit fields), `search` (`query`, `response`),
`agent`, `processes`, `subMessages`, `content`.

Agentic tool use appears two ways:

- `processes[]` (`ProcessingStep`,
  [`messages.ts:92-140`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/messages.ts#L92-L140)):
  `type` (`tool`, `confirmation`, `step`), `id`, `title`,
  `description`, `content`, `state` (`pending`/`success`/`error`),
  `items`.
- `content[]` (`MessagePart`,
  [`lib/shared/src/sourcegraph-api/completions/types.ts:63-97`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/sourcegraph-api/completions/types.ts#L63-L97)):
  `{type:"text",text}`, `{type:"context_file",uri,content?}`,
  `{type:"tool_call",tool_call:{id,name,arguments}}` (assistant),
  `{type:"tool_result",tool_result:{id,content}}` (human).

No per-message timestamp. `model` is on the assistant message.

Where the two carry permission state (source review of 2026-10-19):

- **Deep Cody confirmations.** Deep Cody's terminal tool asks once per
  command: `addConfirmationStep` adds a `processes[]` step of type
  `confirmation` with `state` `pending`, `title` the tool's title and
  `content` the command
  ([`vscode/src/chat/agentic/CodyTool.ts:166-181`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/CodyTool.ts#L166-L181);
  [`ProcessManager.ts:14-27`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/ProcessManager.ts#L14-L27),
  [`46-49`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/ProcessManager.ts#L46-L49)),
  and the webview's buttons answer it
  ([`vscode/webviews/chat/cells/agenticCell/ApprovalCell.tsx:14-16`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/webviews/chat/cells/agenticCell/ApprovalCell.tsx#L14-L16)).
  A refusal completes the step with `new Error('Command rejected')`, so
  the saved step has `state` `error` and `error` `{name, message:
  "Command rejected"}`
  ([`ProcessManager.ts:51-61`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/ProcessManager.ts#L51-L61);
  [`messages.ts:253-260`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/messages.ts#L253-L260)).
  An approval changes nothing on the confirmation step, which keeps
  `pending`: the only completion calls name the tool's or the main
  step's id
  ([`DeepCody.ts:176`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/DeepCody.ts#L176),
  [`253`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/DeepCody.ts#L253),
  [`274`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/agentic/DeepCody.ts#L274)).
  A `pending` step in a saved chat is therefore an approval or a
  request never answered; source cannot tell them apart. The steps are
  saved on the **human** message: `postStatuses` calls
  `setLastMessageProcesses`, which refuses any message but a human one
  ([`ChatController.ts:943-946`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatController.ts#L943-L946);
  [`ChatBuilder.ts:238-247`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatBuilder.ts#L238-L247)).
  The command then runs only if no `shell.allow` prefix list excludes
  it and its first word is not on the block list
  ([`vscode/src/commands/context/shell.ts:28`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/context/shell.ts#L28),
  [`40-54`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/context/shell.ts#L40-L54)).
- **Agentic chat has no per-call decision.** The `agentic` intent's
  tools are `get_file`, `run_terminal_command`, `get_diagnostic`
  and `text_editor`, all enabled by default
  ([`vscode/src/chat/chat-view/tools/index.ts:22-27`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/index.ts#L22-L27)).
  `run_terminal_command` runs the command in the first workspace folder
  with no prompt
  ([`tools/shell.ts:42-69`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/shell.ts#L42-L69));
  its schema's `danger` flag says "user will be asked to confirm", but no
  code reads it
  ([`tools/schema.ts:21-25`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/schema.ts#L21-L25);
  grepped `.danger` and `danger:` across `vscode`, `lib` and `agent`).
  The MCP server schema's `autoApprove` list is likewise parsed and never
  used
  ([`tools/MCPManager.ts:23-29`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/MCPManager.ts#L23-L29);
  grepped `autoApprove` across the repository). Tool results go into
  the next human message's `content[]` and `contextFiles[]`, the latter
  `tool-state` items with a `status`
  ([`AgenticHandler.ts:154-162`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/handlers/AgenticHandler.ts#L154-L162);
  [`lib/shared/src/codebase-context/messages.ts:271-296`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/codebase-context/messages.ts#L271-L296)).
- **Standing settings**, all in the editor's user `settings.json` (or,
  for the JetBrains plugin, `<project>/.idea/.sourcegraph/cody_settings.json`
  with the `jsonConfig` string of the IDE's `cody.xml` as fallback; see
  [section 2 of `collectors/research/cody.md`](../../collectors/research/cody.md#2-per-user-storage)):
  `cody.agentic.context.experimentalOptions` `shell.allow` (command
  prefixes, empty allows all) and `shell.block` (added to a built-in
  block list), `cody.agentic.context.experimentalShell` (deprecated,
  "Now configurable via UI"), `cody.chat.agenticContext` (default
  `true`), and `cody.mcpServers.<server>` with `disabled` and
  `disabledTools`, which the extension itself rewrites at the global
  target when the user toggles a tool
  ([`vscode/package.json:1136-1140`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/package.json#L1136-L1140),
  [`1176-1213`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/package.json#L1176-L1213);
  [`MCPManager.ts:330-370`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/MCPManager.ts#L330-L370),
  [`592-599`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/MCPManager.ts#L592-L599)).
  The UI toggle that replaced `experimentalShell` is not persisted: Deep
  Cody's shell configuration is a static object rebuilt from the
  instance's feature flag and the client's shell
  ([`DeepCodyHandler.ts:31-35`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/handlers/DeepCodyHandler.ts#L31-L35),
  [`169-172`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/handlers/DeepCodyHandler.ts#L169-L172)).

## 4. Joins

- Account: the outer key; it names the server and the user that owned
  the chat, which is attribution evidence in its own right.
- Session to project: none recorded; infer from `contextFiles[].uri`
  paths.
- Tool call to result: `tool_call.id` = `tool_result.id`.
- No subagents.

## 5. SQLite or binary stores

VS Code: read `ItemTable` from `state.vscdb` through
`doubleagent/sqlite_util.py` (WAL sidecars). The value is UTF-8 JSON
text in a BLOB column. History over 50 MB triggers a size warning
([`LocalStorageProvider.ts:40`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L40);
[`ChatHistoryManager.ts:104`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatHistoryManager.ts#L104)),
so expect large values.

## 6. Format versions

The key suffix `-v2` is the version
([`LocalStorageProvider.ts:28-29`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L28-L29)).
JetBrains histories imported from the pre-agent plugin had UUID chat ids;
the agent migration rewrites them to `toUTCString()` ids and records
`migrated-chat-history-cody-3538`
([`agent/src/global-state/migrations/chat-id-migration-CODY3538.ts:7-41`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/global-state/migrations/chat-id-migration-CODY3538.ts#L7-L41)).
Older VS Code keys (`cody-local-chatHistory` without `-v2`) were not
traced.

## 7. Secrets

The access token is not in the history; it is in SecretStorage. Do not
treat `SOURCEGRAPH_CODY_ENDPOINT` as a secret: it is a URL, and the
extension refuses to save a token there
([`LocalStorageProvider.ts:92-100`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L92-L100)).
`contextFiles[].content` and `tool_result.content` carry file and command
output.

## 8. Parser plan

Inputs: the `sourcegraph.cody-ai` row of any collected `state.vscdb`
(attribute it to `cody` even though the file is under `vscode`), and
`*/Cody-nodejs/**/JetBrains-globalState/cody-local-chatHistory-v2`.

| Column | Source |
| --- | --- |
| timestamp_utc | chat `id` parsed as RFC 1123 date, for every row of the chat |
| session_id | chat `id` (prefix with the account key if ids collide across accounts) |
| project_path | empty, or the common parent of `contextFiles[].uri.fsPath` |
| git_branch | empty |
| turn_type | `human` → user; `assistant` → assistant; `system` → system; `tool_call` part → tool_use; `tool_result` part → tool_result; `processes[]` with `type:"tool"` → tool_use |
| model | `assistantMessage.model` |
| tool_name | `tool_call.name` or process `title` |
| tool_use_id | `tool_call.id` / `tool_result.id` / process `id` |
| text | `text`; for tool_use the `arguments`; for tool_result its `content` |
| source_line | 1 (single JSON value) |

Model and permission rows, all `system` (issues 96 and 97):

- `model: <id>` at the first assistant message of a chat whose `model`
  is set and `model: <old> -> <new>` on every later assistant message
  with a different `model`, before that message's rows, at the chat's
  time. The model is recorded per assistant message, so a change inside
  a chat shows.
- `permission decision: <decision> confirmation state=<state>
  error=<error.message> title=<title>` for a
  `processes[]` entry of `type` `confirmation`, which the source
  describes as "a process that prompts the user confirmation"
  ([`messages.ts:76-79`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/messages.ts#L76-L79)),
  with its `description` and `content` on the following lines and
  `tool_use_id` its `id`. `state` and `error.message` are printed as
  recorded (`pending`, `success`, `error`,
  [`messages.ts:117-124`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/chat/transcript/messages.ts#L117-L124)):
  and `<decision>` follows the states the source review of 2026-10-19
  traced ([section 3](#3-record-schema)): `rejected` for `state` `error`
  with `error.message` `Command rejected`, and `approved or unanswered`
  for `pending`, which source cannot split. Any other state is written
  `permission decision: confirmation state=<state>`, with `error=` when
  the step has an `error.message`, and the row does not interpret it
  (issue 169).

Source review of 2026-10-19, one line per class:

- Permission: per-call, the Deep Cody confirmation row above; the agentic
  chat records no per-call decision. Standing: the `settings.json` keys
  in [section 3](#3-record-schema) (`cody.agentic.context.experimentalOptions`,
  `cody.agentic.context.experimentalShell`, `cody.chat.agenticContext`,
  `cody.mcpServers.<server>.disabled` and `.disabledTools`) are not read
  by this parser; the editor's `settings.json` is collected under the
  editor's agent, and the JetBrains `cody.xml` and `.idea/.sourcegraph/cody_settings.json` are not collected.
- Model: per message, already read. `cody-model-preferences` (selected
  model per endpoint and usage, no time) and the legacy XML's
  `llm.model` are not read; a row from the former would carry the
  file's modification time and say so.
- Past use: `<project>/.idea/cody_history.xml` is a secondary source the
  parser should read when it is collected, marking `secondary()` and
  matching on account key, `updatedAt` and text; neither the collector
  nor the parser handles it today. Export files are wherever the user
  saved them.
- Sync, relay, origin: none recorded locally (below). Also leaving the
  host without a local mark: `cody.runTerminalCommand` `accepted` and
  `cody.tool-use` `executed`/`failed` telemetry carry each agentic tool
  call's arguments in `privateMetadata`
  ([`tools/shell.ts:58-66`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/shell.ts#L58-L66);
  [`AgenticHandler.ts:410-444`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/handlers/AgenticHandler.ts#L410-L444)).
- Scratch directories: none; both shell paths run in the first workspace
  folder
  ([`tools/shell.ts:52-55`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/shell.ts#L52-L55), [`67-69`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/tools/shell.ts#L67-L69),
  [`commands/context/shell.ts:37`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/commands/context/shell.ts#L37)).
  The only temp directory in the agent is the internal `cody bench`
  evaluation command's `cody-bench-` worktree
  ([`agent/src/cli/command-bench/testTypecheck.ts:49-55`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/agent/src/cli/command-bench/testTypecheck.ts#L49-L55)),
  a developer tool.
- Deletion: "Delete All Chats" (`cody.chat.history.clear`, with a modal
  confirmation unless called with `clear-all-no-confirm`) replaces only
  the signed-in account's entry with `{chat: {}}`, so other accounts'
  chats stay in the same value; `cody.chat.history.delete` removes one
  chat key and rewrites the whole value
  ([`ChatsController.ts:505-531`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatsController.ts#L505-L531);
  [`LocalStorageProvider.ts:231-241`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L231-L241),
  [`270-276`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L270-L276)).
  No tombstone or deletion record is written, so the parser has nothing
  to yield for a delete; the legacy JetBrains XML is the one local copy
  that a delete does not reach.
- Version drift: none in source (the snapshot is HEAD); post-August-2025
  builds need a real-install round before any parser change.
- Bad lines: covered; one JSON value per input, recovered chat by chat
  with one `parser:` row.

Sync: Cody records no sync state. The frozen snapshot has no chat
history sync, no share link and no server copy of a chat: history is
kept only in the local `cody-local-chatHistory-v2` value and deleted
there
([`LocalStorageProvider.ts:190-240`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L190-L240),
[`270-272`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/LocalStorageProvider.ts#L270-L272)),
the history commands are clear, delete, rename and export
([`ChatsController.ts:227-233`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatsController.ts#L227-L233)),
and export writes a JSON file to a path the user picks in a save dialog
([`ChatsController.ts:401-420`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatsController.ts#L401-L420);
the webview's download button,
[`vscode/webviews/chat/downloadChatHistory.ts:11-30`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/webviews/chat/downloadChatHistory.ts#L11-L30)).
The GraphQL queries the client sends name no chat or history operation
([`lib/shared/src/sourcegraph-api/graphql/queries.ts`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/sourcegraph-api/graphql/queries.ts)),
and Cody Web, the chat embedded in the Sourcegraph web app, keeps its
history in the browser's IndexedDB rather than on the server
([`web/lib/agent/agent.worker.ts:25`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/web/lib/agent/agent.worker.ts#L25),
[`web/lib/agent/index-db-storage.ts:9`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/web/lib/agent/index-db-storage.ts#L9)).
Searched `share`, `sync`, `upload`, `export`, `cloud`, `remote`,
`teleport`, `remoteId` and `chatHistory` in `vscode/src`,
`vscode/webviews`, `lib/shared/src`, `agent/src`, `web/lib` and the
JetBrains plugin's `history/` package. Prompt and reply text does leave
the host outside the model call, with no local marker: the telemetry
events `cody.chat-question/submitted` and `cody.chat-question/executed`
carry the prompt (truncated to the 7,000-token chat input budget,
[`lib/shared/src/token/constants.ts:4`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/token/constants.ts#L4))
and the chat id (`ChatBuilder.sessionID`, the same `toUTCString()`
value,
[`ChatBuilder.ts:97`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatBuilder.ts#L97))
as `sessionID` in their `privateMetadata`, the event part that
sourcegraph.com exports and private instances drop unless allowlisted
([`vscode/src/services/telemetry-v2.ts:118-121`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/services/telemetry-v2.ts#L118-L121)),
and `cody.chatResponse` carries the reply, but only when the account's
endpoint is sourcegraph.com (`isDotCom`) or, for the executed event,
Sourcegraph's internal instance sourcegraph.sourcegraph.com (`isS2`)
([`lib/shared/src/telemetry-v2/events/chat-question.ts:45-75`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/telemetry-v2/events/chat-question.ts#L45-L75),
[`107-148`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/telemetry-v2/events/chat-question.ts#L107-L148);
[`ChatController.ts:1570-1586`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/chat/chat-view/ChatController.ts#L1570-L1586);
[`lib/shared/src/sourcegraph-api/environments.ts:7-35`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/sourcegraph-api/environments.ts#L7-L35)).
The events go to the connected instance's GraphQL API
([`GraphQLTelemetryExporter.ts:33-45`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/lib/shared/src/sourcegraph-api/telemetry/GraphQLTelemetryExporter.ts#L33-L45)),
on by default; the hidden setting `cody.telemetry.level` (`all` or
`off`, default `all`) is read
([`vscode/src/configuration.ts:95`](https://github.com/sourcegraph/cody-public-snapshot/blob/8e20ac6c1460c08b0db581c0204658112a246eda/vscode/src/configuration.ts#L95)),
but this document does not trace whether `off` stops these events. A
responder with a sourcegraph.com account in the history key can ask
Sourcegraph for the events by the chat id; nothing local says they were
sent, so the parser yields no sync row.

Fixture (`JetBrains-globalState/cody-local-chatHistory-v2`):

```json
{"https://sourcegraph.com/-alice":{"chat":{"Fri, 03 Oct 2026 10:00:00 GMT":{"id":"Fri, 03 Oct 2026 10:00:00 GMT","chatTitle":"Fix flaky test","lastInteractionTimestamp":"Fri, 03 Oct 2026 10:00:00 GMT","interactions":[{"humanMessage":{"speaker":"human","text":"why is test_login flaky?","intent":"chat","contextFiles":[{"type":"file","uri":{"$mid":1,"fsPath":"/home/alice/proj/tests/test_login.py","path":"/home/alice/proj/tests/test_login.py","scheme":"file"},"source":"user"}]},"assistantMessage":{"speaker":"assistant","model":"anthropic::2024-10-22::claude-sonnet-4-latest","text":"It depends on wall-clock time.","intent":"chat"}}]}}}}
```

Agentic variant of an interaction:

```json
{"humanMessage":{"speaker":"human","text":"run the tests","intent":"agentic"},"assistantMessage":{"speaker":"assistant","model":"anthropic::2024-10-22::claude-sonnet-4-latest","text":"Running tests.","content":[{"type":"text","text":"Running tests."},{"type":"tool_call","tool_call":{"id":"toolu_01","name":"run_terminal_command","arguments":"{\"command\":\"pytest -q\"}"}}],"processes":[{"type":"tool","id":"toolu_01","title":"run_terminal_command","content":"pytest -q","state":"success"}]}}
```

Confidence. High (frozen source): key names, transcript and message
fields, `toUTCString` ids, tool part shapes, the JetBrains file location.
Medium: the serialised form of `uri` (a VS Code URI's JSON form; field set
not traced), the tool name `run_terminal_command` and the model string in
the fixture, and how tool results are threaded into the next
`humanMessage.content` in agentic chats. Not determined: anything after
August 2025.
