# pearai

Catalog agent: `pearai`, a VS Code fork with two bundled AI extensions. PearAI writes two
independent transcript stores, one per bundled extension: chat sessions from its Continue fork in
`~/.pearai/sessions`, and agent tasks from its Roo Code fork in the editor's `globalStorage`. Both
are older snapshots of their upstreams, so the shapes differ from [continue.md](continue.md) and
[roo-code.md](roo-code.md) in ways a parser must handle. Paths are in
[`collectors/research/pearai.md`](../../collectors/research/pearai.md).

## 1. Source and evidence

[trypear/pearai-submodule](https://github.com/trypear/pearai-submodule) (Continue fork) at
[`51eceef62a90c29f712b3a9607ea70a9dca657e9`](https://github.com/trypear/pearai-submodule/commit/51eceef62a90c29f712b3a9607ea70a9dca657e9)
and [trypear/PearAI-Roo-Code](https://github.com/trypear/PearAI-Roo-Code) (Roo Code 3.15.3 fork) at
[`0b6df736c9b2799c38b9ee629668407521a7bdda`](https://github.com/trypear/PearAI-Roo-Code/commit/0b6df736c9b2799c38b9ee629668407521a7bdda),
both Apache-2.0, open source. The editor ([trypear/pearai-app](https://github.com/trypear/pearai-app)) stores no
transcripts of its own.

### Observed

No real install.

- Unverified on a real install: whether a malformed `sessions.json` index occurs
  ([Bad lines](#bad-lines)).

### Source reviews

- **Source review (2026-10-19)**: the HEADs of all three repositories are
  still the commits cited here, [`51eceef`](https://github.com/trypear/pearai-submodule/commit/51eceef62a90c29f712b3a9607ea70a9dca657e9) (pearai-submodule),
  [`0b6df73`](https://github.com/trypear/PearAI-Roo-Code/commit/0b6df736c9b2799c38b9ee629668407521a7bdda) (PearAI-Roo-Code) and [`d930f02`](https://github.com/trypear/pearai-app/commit/d930f0233c14668df9f85c6a78a81828f4251194)
  (pearai-app), so nothing has drifted; the extension forks have taken no
  commit since 2026-06-19 and the editor none since 2025-05-15. The Roo
  fork is Roo Code 3.15.3 and predates every Roo Code change since
  ([roo-code.md](roo-code.md) describes 3.53.0): it has no
  `history_item.json`, no `isAnswered`, plain-text denials, and a
  `creatorModeConfig` of its own. One line per requirement class:
  - Permission state: found for the agent surface, not read by the
    parser: denial and approval texts in the API history, and the
    `alwaysAllow*` settings and MCP `alwaysAllow` lists. The chat surface
    has no tool calls and so no permission state.
  - Model: already covered for chat; the agent surface records none.
  - Past use beyond the primary store: found, none of it read. The
    "PearAI" output channel log in the editor's `logs/` directory holds
    every chat prompt with its context and every completion;
    `dev_data/chat.jsonl` repeats rated prompts; `/share` exports and
    `pearai_memories.json` outlive the sessions; the agent surface's
    `taskHistory` in `state.vscdb` is read for the workspace only.
  - Sync, relay and origin: already covered, none.
  - Scratch directories: found. Creator mode makes a new project under
    `~/Documents/PearAI` by default; it is a project, not a scratch
    directory, and the catalog does not collect it.
  - Deletion: already covered for chat; found for agent tasks.
  - Version drift: none; every HEAD is the cited commit.
  - Bad lines: `dev_data/*.jsonl` would need per-line handling. Found
    through the Continue review of the same day: the chat surface's
    `sessions.json` index is read through the Continue parser's
    own index reader (`PearAIParser` keeps a `ContinueParser` for it),
    which drops an unreadable `sessions.json` without a `parser:` row
    ([section 1 of `continue.md`](continue.md#source-reviews)), so the sessions
    lose their timestamps silently. The sharing is visible in the
    analyzer's code; that a malformed index occurs on a real PearAI
    install is unverified.

## 2. Transcript stores

Chat (Continue fork), `~/.pearai` or `$CONTINUE_GLOBAL_DIR`
([`core/util/paths.ts:11-12`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/paths.ts#L11-L12)):

- `.pearai/sessions/<sessionId>.json`: one session, compact JSON
  ([`paths.ts:43-45`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/paths.ts#L43-L45);
  [`core/util/history.ts:91-96`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/history.ts#L91-L96)).
- `.pearai/sessions/sessions.json`: index array
  ([`paths.ts:47-53`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/paths.ts#L47-L53)).

Agent (Roo fork), `<User>/globalStorage/pearai.pearai-roo-cline/tasks/<taskId>/`
or under `roo-cline.customStoragePath`
([`src/shared/storagePathManager.ts:52-57`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/shared/storagePathManager.ts#L52-L57)):
`api_conversation_history.json`, `ui_messages.json`,
`task_metadata.json` ([`src/shared/globalFileNames.ts:1-7`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/shared/globalFileNames.ts#L1-L7)).

### What survives a delete

Deleting a chat session removes its `sessions/<sessionId>.json` file and
its `sessions.json` entry only
([`core/util/history.ts:41-66`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/history.ts#L41-L66));
deleting an agent task removes its `taskHistory` entry, its shadow
checkpoint repository or branch and its task directory
([`src/core/webview/ClineProvider.ts:1138-1169`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/webview/ClineProvider.ts#L1138-L1169)).
A per-prompt history file is not stated for either surface. Neither
delete touches the other records of chat use in [section 5](#5-other-stores): the `PearAI`
output channel log, which holds every chat prompt and completion with
no session id or per-entry time and lasts until the editor drops its log
session directory (the newest 49 are kept besides the current one,
[`logsDataCleaner.ts:24-35`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/workbench/contrib/logs/common/logsDataCleaner.ts#L24-L35));
`dev_data/chat.jsonl`, the rated prompts with their `sessionId` and no
time; `dev_data/tokens_generated.jsonl`, which names the models used;
the `/share` Markdown exports; and `pearai_memories.json`, derived from
chats but naming none. PearAI's analytics may hold the ids of tasks
deleted locally, but nothing on disk marks a deletion. The analyzer
reads none of these survivors yet: it reads the chat session files with
the `sessions.json` index and the agent tasks'
`api_conversation_history.json`, and the plan in
[Past use and secondary sources](#past-use-and-secondary-sources) names the output channel log and
`dev_data/chat.jsonl` as secondary sources still to be read (see
[Secondary sources](../docs/output.md#secondary-sources)).

## 3. Record schema

### Chat session

`PersistedSessionInfo`
([`core/index.d.ts:207-213`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L207-L213)): `sessionId`,
`title`, `workspaceDirectory`, `history: ChatHistoryItem[]` and
`perplexityHistory: ChatHistoryItem[]`, the second holding the
"PearAI Search" (Perplexity) conversation. The GUI saves one or the other
per session ([`gui/src/hooks/useHistory.tsx:43-51`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/hooks/useHistory.tsx#L43-L51),
[`79-85`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/hooks/useHistory.tsx#L79-L85)).

`ChatHistoryItem` ([`index.d.ts:325-332`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L325-L332)):
`message`, `contextItems` (`content`, `name`, `description`, `id`
[`298-306`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L298-L306)), `editorState?`,
`modifiers?`, `promptLogs?` (`completionOptions.model`, `prompt`,
`completion`; [`314-318`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L314-L318),
[`257-259`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L257-L259)), `citations?` (`url`,
`title`).

`ChatMessage` ([`index.d.ts:261-275`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L261-L275)):
`role` is only `user`, `assistant` or `system`; `content` is a string
or `[{type:"text",text}|{type:"imageUrl",imageUrl:{url}}]`. **There are no
tool calls, `tool` messages or `thinking` messages** in this fork, unlike
current Continue. No per-message timestamp.

`sessions.json` entry (`SessionInfo`, [`index.d.ts:215-221`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L215-L221)):
`sessionId`, `title`, `dateCreated` (`String(Date.now())`, millisecond
epoch as a string), `workspaceDirectory`, `integrationType`
(`"continue"` or `"perplexity"`;
[`history.ts:7-20`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/history.ts#L7-L20),
[`118-135`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/history.ts#L118-L135)).

### Agent task

Roo 3.15 shape. `api_conversation_history.json` is an
array of Anthropic `MessageParam` plus `ts` (`Date.now()`, ms epoch;
[`src/core/Cline.ts:323-327`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/Cline.ts#L323-L327)). Tool use
is **not** native `tool_use` blocks: the assistant message is one text
block whose text contains XML tool tags such as
`<execute_command><command>…</command></execute_command>`
([`Cline.ts:1905-1909`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/Cline.ts#L1905-L1909);
[`src/core/assistant-message/parse-assistant-message.ts:6-30`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/assistant-message/parse-assistant-message.ts#L6-L30)),
and the result is a user message whose first text block is
`[<tool> for '<arg>'] Result:` followed by the output
([`Cline.ts:1271-1276`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/Cline.ts#L1271-L1276),
[`1341-1352`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/Cline.ts#L1341-L1352)). `ui_messages.json` is
`ClineMessage[]`: `ts`, `type` (`ask`/`say`), `ask`, `say`, `text`,
`images`, `partial`, `reasoning`, `conversationHistoryIndex`,
`checkpoint` ([`src/schemas/index.ts:868-880`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/schemas/index.ts#L868-L880)).
`task_metadata.json` holds only `files_in_context`
([`src/core/context-tracking/FileContextTrackerTypes.ts:23-25`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/context-tracking/FileContextTrackerTypes.ts#L23-L25)).

### Permission records

Source review of 2026-10-19, agent surface. A denied tool call
is answered in the API history with the plain text `The user denied this
operation.`, or `The user denied this operation and provided the
following feedback:` followed by a `<feedback>` block, and an approval
with a typed note with `The user approved this operation and provided
the following context:` and a `<feedback>` block
([`src/core/prompts/responses.ts:8-14`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/prompts/responses.ts#L8-L14)).
An approval without a note, by the user or by the auto-approve settings,
leaves no mark. The `taskHistory` entry (`HistoryItem`) also carries
`creatorModeConfig{creatorMode, newProjectType, newProjectPath}`
([`src/schemas/index.ts:327-331`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/schemas/index.ts#L327-L331),
[`:339-352`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/schemas/index.ts#L339-L352)), set for a task
started from PearAI Creator, the mode that builds a new project from a
description.

## 4. Joins and timestamps

- Chat session to project: `workspaceDirectory` in both the session and
  `sessions.json`; time from `sessions.json` `dateCreated`.
- `dev_data/chat.jsonl` rows carry `sessionId`.
- Agent task to project: `taskHistory[].workspace` in the editor's
  `User/globalStorage/state.vscdb` `ItemTable`, key `taskHistory` of the
  extension's global state
  ([`src/schemas/index.ts:339-352`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/schemas/index.ts#L339-L352);
  [`ClineProvider.ts:1091`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/webview/ClineProvider.ts#L1091)).
  The task directory name is `HistoryItem.id`.
- Tool call to result: by position, the assistant XML block followed by the
  next user message's `[tool ...] Result:` block. No ids.

## 5. Other stores

`dev_data/devdata.sqlite` (token counts, excluded by the collector);
`index/*.sqlite` (code index, excluded). The agent's `taskHistory` is in
`state.vscdb`, read through `sqlite_util`.

The other records of chat use below were found in the source review of 2026-10-19.

### Output channel log

The chat extension hands its core a log callback that appends every
model request to the editor output channel named `PearAI`
([`extensions/vscode/src/extension/VsCodeExtension.ts:132`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/extensions/vscode/src/extension/VsCodeExtension.ts#L132),
[`:147-155`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/extensions/vscode/src/extension/VsCodeExtension.ts#L147-L155)).
Logging is on unless a caller passes `log: false`
([`core/llm/index.ts:361`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L361)), and each chat
request writes `Settings:`, the context length and completion options
(the model among them), a `####` rule and the full prompt, then
`Completion:` and the reply
([`:247-261`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L247-L261),
[`:551-554`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L551-L554),
[`:586-587`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L586-L587)). The editor, a VS Code
fork, backs every extension output channel with a file,
`<User data dir>/logs/<YYYYMMDDTHHMMSS>/window<N>/exthost/output_logging_<time>/<n>-PearAI.log`
([`pearai-app src/vs/workbench/api/common/extHostOutput.ts:121`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/workbench/api/common/extHostOutput.ts#L121),
[`:160-170`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/workbench/api/common/extHostOutput.ts#L160-L170)),
and keeps the newest 49 log session directories besides the current one
([`src/vs/workbench/contrib/logs/common/logsDataCleaner.ts:24-35`](https://github.com/trypear/pearai-app/blob/d930f0233c14668df9f85c6a78a81828f4251194/src/vs/workbench/contrib/logs/common/logsDataCleaner.ts#L24-L35)).
The file has no session id and no per-entry time; the log session
directory's name and the file's modification time bound it. It
outlives a deleted chat session. `logs/prompt.log` under `~/.pearai`
is written only by the JetBrains binary
([`binary/src/index.ts:34-37`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/binary/src/index.ts#L34-L37)),
which PearAI does not ship as an editor.

### `dev_data` tables

`.pearai/dev_data/<table>.jsonl`: appended JSON lines
([`core/util/devdata.ts:4-8`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/devdata.ts#L4-L8));
tables `chat` (written only when the user clicks feedback;
[`gui/src/components/gui/StepContainer.tsx:87-96`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/components/gui/StepContainer.tsx#L87-L96)),
`tokens_generated`
([`core/llm/index.ts:286-291`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L286-L291))
and `autocomplete`.

`dev_data/chat.jsonl` gets one line per prompt log of an item the user
rated, `{...promptLog, feedback, sessionId}`, where a prompt log is
`{completionOptions, prompt, completion}`
([`gui/src/components/gui/StepContainer.tsx:88-97`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/components/gui/StepContainer.tsx#L88-L97));
`dev_data/tokens_generated.jsonl` one line per request, `{model,
provider, promptTokens, generatedTokens}`
([`core/llm/index.ts:286-291`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L286-L291)).
Lines are only appended
([`core/util/devdata.ts:4-8`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/devdata.ts#L4-L8)), carry
no time, and survive a session delete.

### `/share` exports

`/share` writes `<YYYYMMDDTHHMMSS>_session.md` to `~/.pearai` or the
given directory ([Sync, relay and origin](#sync-relay-and-origin)), a Markdown copy of the
session that the session delete does not remove.

### `pearai_memories.json`

`pearai_memories.json`, the assistant's memories about the user, a JSON
array of `{id, content, timestamp, isNew?, isModified?, isDeleted?}`
([`extensions/vscode/src/integrations/mem0/types.ts:1-8`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/extensions/vscode/src/integrations/mem0/types.ts#L1-L8),
[`localMemoryService.ts:33-35`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/extensions/vscode/src/integrations/mem0/localMemoryService.ts#L33-L35)),
written by both extensions; it is derived from chats but names none.

### Aider integration

The integration with Aider, a separate terminal coding agent, is
commented out in full at this commit
([`extensions/vscode/src/integrations/aider/aiderProcess.ts:121-146`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/extensions/vscode/src/integrations/aider/aiderProcess.ts#L121-L146)),
so PearAI writes no Aider state.

## 6. Format versions

No version field in either store. The Continue fork predates Continue's
tool-calling session format; the Roo fork predates Roo's native tool calls
and `history_item.json`.

## 7. Secrets

`promptLogs[].prompt` and `dev_data/chat.jsonl` carry full prompts with
context items, which can include file and `.env` contents. Tool results
in `api_conversation_history.json` hold raw command output. No account
tokens are written to these files; they are in SecretStorage.

## 8. Parser plan

Globs (home-relative): `.pearai/sessions/*.json` (read `sessions.json`
as the index through the Continue parser's `read_index`; it yields rows
only for what it loses, with the texts listed under "Bad lines" in
[section 8 of `continue.md`](continue.md#bad-lines), since issue 170),
`*/User/globalStorage/pearai.pearai-roo-cline/tasks/*/api_conversation_history.json`.
The Roo fork task files can reuse the Roo Code parser if it accepts
XML-in-text tool calls; otherwise rows are emitted per message.

| Column | Chat session | Agent task |
| --- | --- | --- |
| timestamp_utc | `sessions.json` `dateCreated` for every row | message `ts` |
| session_id | `sessionId` | task directory name |
| project_path | `workspaceDirectory` | `taskHistory[].workspace` when `state.vscdb` is present |
| git_branch | empty | empty |
| turn_type | `message.role`; items from `perplexityHistory` also by role | `role`; XML tool tag → tool_use; `[x] Result:` block → tool_result |
| model | `promptLogs[0].completionOptions.model` | empty |
| tool_name | empty | XML tag name |
| tool_use_id | empty | empty |
| text | `message.content` (text parts joined) | text block |

### Permission state

Source review of 2026-10-19 (the parser reads none of it yet), agent surface: a `tool_result` row
whose text starts with `The user denied this operation` can be followed by
`permission decision: denied` (`denied with feedback` when the `<feedback>` block follows), and one
starting `The user approved this operation` by `permission decision: approved with feedback`, on the
same `tool_use_id`. Standing: the global-state keys `autoApprovalEnabled`, `alwaysAllowReadOnly`,
`alwaysAllowReadOnlyOutsideWorkspace`, `alwaysAllowWrite`, `alwaysAllowWriteOutsideWorkspace`,
`alwaysAllowBrowser`, `alwaysApproveResubmit`, `alwaysAllowMcp`, `alwaysAllowModeSwitch`,
`alwaysAllowSubtasks`, `alwaysAllowExecute` and `allowedCommands`
([`src/schemas/index.ts:584-597`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/schemas/index.ts#L584-L597)),
in the extension's row of `state.vscdb`, and each MCP server's `alwaysAllow` list in
`settings/pearai_agent_mcp_settings.json` or a project's `.pearai-agent/mcp.json`
([`src/services/mcp/McpHub.ts:47`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/services/mcp/McpHub.ts#L47)).
Each can be one `permission setting:` row at the file's modification time. The chat surface has no
tools and no permission state.

The plan before that review said: Permission state was not researched for either surface, and the
parser reads none.

### Model

Model rows, typed `system`, chat sessions only: the first item whose
`promptLogs[].completionOptions.model` names a model yields `model:
<model>` ahead of the item's rows, and a later item naming a different
one yields `model: <old> -> <new>`. Mid-session switching is not
researched: the format has no switch record, so a change shows only as a
different value between items. Agent tasks record no model (the Roo fork
writes no `modelInfo` and no `model_usage`).

### Past use and secondary sources

Source review of 2026-10-19 (the parser reads none of it yet): the `PearAI` output channel log is a
secondary source for chat: one `user` row per logged prompt and one `assistant` row per
`Completion:`, with no session id, matched to session rows on text, and a `model:` value from its
`Settings:` block. `dev_data/chat.jsonl` is secondary too, joined on `sessionId` and the prompt
text; `tokens_generated.jsonl` names models used even after their sessions are gone. The `/share`
Markdown files and `pearai_memories.json` are not transcripts the dedup rule can pair and stay
unread. The agent surface's `taskHistory` entries can be one `system` row per task, as the `cline`
parser yields from `state/taskHistory.json`, so a task whose directory is gone still shows.

### Sync, relay and origin

Sync: neither surface records sync state, and neither uploads a session,
a transcript or a prompt history beyond the model call. The chat fork
keeps upstream Continue's local-only paths, described under `Sync:` in
[section 8 of `continue.md`](continue.md#sync-relay-and-origin), with these
differences. `/share` is a default slash command
([`core/config/default.ts:64`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/config/default.ts#L64)) that writes the same
`<YYYYMMDDTHHMMSS>_session.md` Markdown export to `~/.pearai` or the
given `outputDir`, never to a server
([`core/commands/slash/share.ts:38-98`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/commands/slash/share.ts#L38-L98)). `dev_data` tables are
appended locally with no remote destination
([`core/util/devdata.ts:4-8`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/devdata.ts#L4-L8)). The fork has no `cn` CLI and so
no `serve --id` upload.

What does leave for PearAI's server
(`https://server.trypear.ai/pearai-server-api2`,
[`core/util/parameters.ts:38`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/parameters.ts#L38)) carries no message text: before
every chat request a `GET /anonymousTelemetry` whose headers are the
model, the provider and the event name `streamChat`
([`core/pearaiServer/util.ts:5-28`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/pearaiServer/util.ts#L5-L28);
[`core/llm/index.ts:535-546`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L535-L546)), on by default and turned off by
`allowAnonymousTelemetry: false` in `~/.pearai/config.json`
([`core/config/load.ts:121-122`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/config/load.ts#L121-L122);
[`core/config/profile/doLoadConfig.ts:47-52`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/config/profile/doLoadConfig.ts#L47-L52); the code comment
names the key `sendAnonymousTelemetry`, which nothing reads); and, for
PearAI's hosted models, a `POST /log_tokens` with token counts
([`core/llm/llms/PearAIServer.ts:320-339`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/llms/PearAIServer.ts#L320-L339)). The PostHog product
analytics client is commented out
([`core/util/posthog.ts:36-64`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/posthog.ts#L36-L64)), and team analytics
(`TeamAnalytics`, upstream's PostHog, Logstash (Elastic's log pipeline) or Continue-proxy sink
chosen by an `analytics` block in the config) start only when that block
is present and send event names and counts
([`core/control-plane/TeamAnalytics.ts:8-54`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/control-plane/TeamAnalytics.ts#L8-L54);
[`core/config/profile/doLoadConfig.ts:54-59`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/config/profile/doLoadConfig.ts#L54-L59);
[`core/llm/index.ts:262-293`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L262-L293)).

The agent fork has no cloud or
share feature (the Roo Code Cloud service of later upstream releases is
absent from `src/services`); its PostHog client is forced on
([`src/services/telemetry/PostHogClient.ts:53`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/services/telemetry/PostHogClient.ts#L53),
[`86-104`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/services/telemetry/PostHogClient.ts#L86-L104)) and sends
task events keyed by the local task id (`taskId`, the task directory
name) with `source: "user"` or `"assistant"` and no message text
([`src/services/telemetry/TelemetryService.ts:87-101`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/services/telemetry/TelemetryService.ts#L87-L101);
[`src/core/Cline.ts:1697`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/core/Cline.ts#L1697)), so PearAI's analytics may hold the ids
of tasks deleted locally, but nothing on disk says so. Searched `share`,
`sync`, `upload`, `remote`, `telemetry`, `posthog`, `SERVER_URL` and
`trypear.ai` in both clones' `core/`, `gui/src`, `extensions/vscode/src`,
`src/` and `webview-ui/src`.

### Scratch directories

None. Creator mode's default parent,
`~/Documents/PearAI/<generated name>`
([`gui/src/pages/creator/index.tsx:106-114`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/pages/creator/index.tsx#L106-L114);
the path picker's default is `~/pearai-projects/`,
[`gui/src/components/ui/path-select.tsx:19`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/components/ui/path-select.tsx#L19)),
is created and opened as the workspace
([`extensions/vscode/src/integrations/creator/index.ts:130-160`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/extensions/vscode/src/integrations/creator/index.ts#L130-L160)),
so it is the user's new project and appears as the task's `workspace`
and `creatorModeConfig.newProjectPath`. The latter can name the
project on a `system` row.

### Deletion

Not stated: what each surface's delete removes and what survives it is in
[What survives a delete](#what-survives-a-delete).

### Bad lines

The source review of 2026-10-19 found that `dev_data/*.jsonl` would need per-line handling, and that
the chat surface's `sessions.json` index, read through the Continue parser's index reader, was
dropped when unreadable without a `parser:` row ([Source reviews](#source-reviews)); since issue
170 that reader yields rows for what it loses (the globs at the top of this section).

### Fixtures

Fixture `.pearai/sessions/9b1c2d3e-0000-4000-8000-000000000001.json`:

```json
{"history":[{"message":{"role":"user","content":"why does build.sh fail"},"contextItems":[{"content":"set -e\nmake all","name":"build.sh","description":"/home/alice/proj/build.sh","id":{"providerTitle":"file","itemId":"build.sh"}}]},{"message":{"role":"assistant","content":"The make target is missing."},"contextItems":[],"promptLogs":[{"completionOptions":{"model":"pearai_model"},"prompt":"<user>why does build.sh fail","completion":"The make target is missing."}]}],"perplexityHistory":[],"title":"why does build.sh fail","sessionId":"9b1c2d3e-0000-4000-8000-000000000001","workspaceDirectory":"/home/alice/proj"}
```

`.pearai/sessions/sessions.json`:

```json
[{"sessionId":"9b1c2d3e-0000-4000-8000-000000000001","title":"why does build.sh fail","dateCreated":"1759400000000","workspaceDirectory":"/home/alice/proj","integrationType":"continue"}]
```

Agent `tasks/1759400100000/api_conversation_history.json`:

```json
[{"role":"user","content":[{"type":"text","text":"<task>\nrun the tests\n</task>"}],"ts":1759400100000},{"role":"assistant","content":[{"type":"text","text":"<execute_command>\n<command>npm test</command>\n</execute_command>"}],"ts":1759400103000},{"role":"user","content":[{"type":"text","text":"[execute_command for 'npm test'] Result:"},{"type":"text","text":"12 passing"}],"ts":1759400109000}]
```

### Confidence

High: file locations, session and index fields, absence of tool
calls in chat sessions, Roo message shape and the result prefix (source).
Medium: the `<task>` wrapper on the first user message and the model
string `pearai_model` in the fixture, which are illustrative. Not
determined: which extension commits a given PearAI build shipped, so older
installs may differ.
