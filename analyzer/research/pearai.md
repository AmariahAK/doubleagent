# PearAI transcript schema

Catalog agent: `pearai`. PearAI writes two independent transcript stores,
one per bundled extension: chat sessions from its Continue fork in
`~/.pearai/sessions`, and agent tasks from its Roo Code fork in the
editor's `globalStorage`. Both are older snapshots of their upstreams, so
the shapes differ from [continue.md](continue.md) and
[roo-code.md](roo-code.md) in ways a parser must handle. Paths are in
[`collectors/research/pearai.md`](../../collectors/research/pearai.md).

## 1. Source

[trypear/pearai-submodule](https://github.com/trypear/pearai-submodule) (Continue fork) at
[`51eceef62a90c29f712b3a9607ea70a9dca657e9`](https://github.com/trypear/pearai-submodule/commit/51eceef62a90c29f712b3a9607ea70a9dca657e9)
and [trypear/PearAI-Roo-Code](https://github.com/trypear/PearAI-Roo-Code) (Roo Code 3.15.3 fork) at
[`0b6df736c9b2799c38b9ee629668407521a7bdda`](https://github.com/trypear/PearAI-Roo-Code/commit/0b6df736c9b2799c38b9ee629668407521a7bdda),
both Apache-2.0, open source. The editor ([trypear/pearai-app](https://github.com/trypear/pearai-app)) stores no
transcripts of its own.

## 2. Transcript files

Chat (Continue fork), `~/.pearai` or `$CONTINUE_GLOBAL_DIR`
([`core/util/paths.ts:11-12`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/paths.ts#L11-L12)):

- `.pearai/sessions/<sessionId>.json`: one session, compact JSON
  ([`paths.ts:43-45`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/paths.ts#L43-L45);
  [`core/util/history.ts:91-96`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/history.ts#L91-L96)).
- `.pearai/sessions/sessions.json`: index array
  ([`paths.ts:47-53`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/paths.ts#L47-L53)).
- `.pearai/dev_data/<table>.jsonl`: appended JSON lines
  ([`core/util/devdata.ts:4-8`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/devdata.ts#L4-L8)); tables
  `chat` (written only when the user clicks feedback;
  [`gui/src/components/gui/StepContainer.tsx:87-96`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/gui/src/components/gui/StepContainer.tsx#L87-L96)),
  `tokens_generated` ([`core/llm/index.ts:286-291`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L286-L291))
  and `autocomplete`.

Agent (Roo fork), `<User>/globalStorage/pearai.pearai-roo-cline/tasks/<taskId>/`
or under `roo-cline.customStoragePath`
([`src/shared/storagePathManager.ts:52-57`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/shared/storagePathManager.ts#L52-L57)):
`api_conversation_history.json`, `ui_messages.json`,
`task_metadata.json` ([`src/shared/globalFileNames.ts:1-7`](https://github.com/trypear/PearAI-Roo-Code/blob/0b6df736c9b2799c38b9ee629668407521a7bdda/src/shared/globalFileNames.ts#L1-L7)).

## 3. Record schema

**Chat session** (`PersistedSessionInfo`,
[`core/index.d.ts:207-213`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/index.d.ts#L207-L213)): `sessionId`,
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

**Agent task** (Roo 3.15 shape). `api_conversation_history.json` is an
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

## 4. Joins

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

## 5. SQLite or binary stores

`dev_data/devdata.sqlite` (token counts, excluded by the collector);
`index/*.sqlite` (code index, excluded). The agent's `taskHistory` is in
`state.vscdb`, read through `sqlite_util`.

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
as the index, do not emit rows for it),
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

Model rows, typed `system`, chat sessions only: the first item whose
`promptLogs[].completionOptions.model` names a model yields `model:
<model>` ahead of the item's rows, and a later item naming a different
one yields `model: <old> -> <new>`. Mid-session switching is not
researched: the format has no switch record, so a change shows only as a
different value between items. Agent tasks record no model (the Roo fork
writes no `modelInfo` and no `model_usage`). Permission state was not
researched for either surface, and the parser reads none.

Sync: neither surface records sync state, and neither uploads a session,
a transcript or a prompt history beyond the model call. The chat fork
keeps upstream Continue's local-only paths, described under `Sync:` in
[section 8 of `continue.md`](continue.md#8-parser-plan), with these
differences. `/share` is a default slash command
([`core/config/default.ts:64`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/config/default.ts#L64)) that writes the same
`<YYYYMMDDTHHMMSS>_session.md` Markdown export to `~/.pearai` or the
given `outputDir`, never to a server
([`core/commands/slash/share.ts:38-98`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/commands/slash/share.ts#L38-L98)). `dev_data` tables are
appended locally with no remote destination
([`core/util/devdata.ts:4-8`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/devdata.ts#L4-L8)). The fork has no `cn` CLI and so
no `serve --id` upload. What does leave for PearAI's server
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
[`core/llm/index.ts:262-293`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/llm/index.ts#L262-L293)). Deleting a chat session removes its
file and its `sessions.json` entry only
([`core/util/history.ts:41-66`](https://github.com/trypear/pearai-submodule/blob/51eceef62a90c29f712b3a9607ea70a9dca657e9/core/util/history.ts#L41-L66)). The agent fork has no cloud or
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

Confidence. High: file locations, session and index fields, absence of tool
calls in chat sessions, Roo message shape and the result prefix (source).
Medium: the `<task>` wrapper on the first user message and the model
string `pearai_model` in the fixture, which are illustrative. Not
determined: which extension commits a given PearAI build shipped, so older
installs may differ.
