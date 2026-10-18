# Letta transcript schema

Catalog agent: `letta`. Letta Code (the current `letta` CLI) keeps
conversations on the Letta server by default, but writes two parseable
JSONL stores under `~/.letta` and, in local-backend mode, the full message
history. The retired Letta V1 Python server kept messages in SQLite. Paths
are in [`collectors/research/letta.md`](../../collectors/research/letta.md).

## 1. Source

[letta-ai/letta-code](https://github.com/letta-ai/letta-code) at [`77faf36e34378946c8e69c0bfaa5595a7be4c326`](https://github.com/letta-ai/letta-code/commit/77faf36e34378946c8e69c0bfaa5595a7be4c326), Apache-2.0. The local-backend
message types are `@earendil-works/pi-ai`, read in [earendil-works/pi](https://github.com/earendil-works/pi) at
[`200387122ca450d6387f033949423114a270b96c`](https://github.com/earendil-works/pi/commit/200387122ca450d6387f033949423114a270b96c) (letta-code pins `^0.99.1`; the
pi checkout is newer, so optional fields may differ). V1 SQLite from
[letta-ai/letta](https://github.com/letta-ai/letta) tag 0.11.7 at [`bf9356ceaf8ac4c80f1b418f209ad49b04986885`](https://github.com/letta-ai/letta/commit/bf9356ceaf8ac4c80f1b418f209ad49b04986885).

## 2. Transcript files

| Glob (relative to home) | One file per | Mode |
| --- | --- | --- |
| `.letta/transcripts/*/*/transcript.jsonl` | agent and conversation | every turn, both backends |
| `.letta/lc-local-backend/conversations/*/messages.jsonl` | conversation | local backend only |
| `.letta/sessions.jsonl` | user (two lines per session) | always |
| `.letta/logs/chunk-logs/*/*.jsonl` | agent and CLI session, last 5 kept | always, truncated |
| `.letta/sqlite.db` | user | V1 server up to at least 0.11.7 |

`transcripts/<agent>/<conversation>/` names are the ids with anything outside
`[a-zA-Z0-9._-]` replaced by `_`
([reflection-transcript.ts:578-581](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/reflection-transcript.ts#L578-L581), [911-925](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/reflection-transcript.ts#L911-L925)); `state.json` and
`payload-*.json` sit beside it. Local-backend conversation directories are
base64url of `conversation:<id>`, or `default:<agent id>` for an agent's
default conversation ([local-store.ts:283-285](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L283-L285), [3262-3266](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L3262-L3266)), next to
`conversation.json`, `manifest.json` and `system-prompt.json`.

**Server-side session markers.** In the default backend, `api` (Letta
Cloud at `https://api.letta.com`, or a self-hosted Letta server named by
`LETTA_BASE_URL`), the agent and its conversations are server objects
and the local files name them by id
([settings-manager.ts:75](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L75),
[195](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L195),
[273-281](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L273-L281);
[cli/subcommands/backend.ts:38](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/subcommands/backend.ts#L38)).
A local-backend agent id starts `agent-local-`; any other agent id is a
server id ([agent/agent-id.ts:3-9](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/agent-id.ts#L3-L9)).

- `.letta/transcripts/<agent id>/<conversation id>/`: the two directory
  names are the server's ids, sanitised as above.
- `.letta/sessions.jsonl` `agent_id`: the server agent id; its
  `session_id` is the CLI's own telemetry session id, not a conversation
  ([cli/app/AppCoordinator.tsx:3841-3844](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/app/AppCoordinator.tsx#L3841-L3844)).
- `.letta/settings.json` `sessionsByServer`: an object keyed by the
  server's host and port (`api.letta.com`, `localhost:8283`, or
  `local:<store path>` for the local backend) whose values are
  `{agentId, conversationId}`, the last session used on that server;
  `lastSession` and `lastAgent` repeat it for server agents
  ([settings-manager.ts:53-56](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L53-L56),
  [94](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L94),
  [215-225](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L215-L225),
  [1231-1274](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L1231-L1274)). The project's
  `.letta/settings.local.json` has the same keys for that directory
  ([157](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L157),
  [995-996](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L995-L996),
  [1365-1405](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L1365-L1405)). Both are rewritten on
  every start, resume and conversation switch through `persistSession`
  ([1447-1455](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L1447-L1455);
  [index.ts:2356](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/index.ts#L2356)), so they hold one session per
  server, never a list.
- `.letta/settings.json` `agents[]`: per-agent settings with `agentId`
  and `baseUrl`, absent for Letta Cloud, and `memfs` when the memory
  filesystem is on ([agent-settings.ts:7-19](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent-settings.ts#L7-L19)).
  `deviceId` identifies the install to the server
  ([settings-manager.ts:100](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L100)).
- `.letta/agents/<agent id>/memory/.git/config`: the memory filesystem
  ("memfs", the agent's memory blocks kept as files in a git repository)
  has remote `origin` at `<server>/v1/git/<agent id>/state.git` and is
  pushed there
  ([agent/memory-git.ts:1-3](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/memory-git.ts#L1-L3),
  [89-96](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/memory-git.ts#L89-L96),
  [228-233](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/memory-git.ts#L228-L233)).
- `.letta/settings.local.json` `listenerEnvName`: the name under which
  `letta server` or `/listen` registered this machine as a remote
  environment with Letta Cloud (`/v1/environments/register`), so the
  web app can drive local sessions
  ([settings-manager.ts:158](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/settings-manager.ts#L158);
  [websocket/listen-register.ts:110-128](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/websocket/listen-register.ts#L110-L128)).

## 3. Record schema

**Reflection transcript** (`transcript.jsonl`). Appended after each completed
turn ([use-conversation-loop.ts:1443-1452](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/app/use-conversation-loop.ts#L1443-L1452), [reflection-transcript.ts:927-952](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/reflection-transcript.ts#L927-L952)).
One object per line ([reflection-transcript.ts:54-71](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/reflection-transcript.ts#L54-L71)):
`kind` in `user|assistant|reasoning|error` with `text`; or `kind:"tool_call"`
with `name`, `argsText`, `resultText`, `resultOk`. Every line has
`captured_at` (ISO 8601 UTC string, the same value for all lines of one turn
batch) and optional `source_line_id`, `source_message_id`. No model, no cwd,
no tool call id: a call and its result share one line.

`captured_at` is the time of the append, not of the event:
`appendTranscriptDeltaJsonl` takes `new Date().toISOString()` once and
stamps every line of the batch with it
([reflection-transcript.ts:927-946](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/reflection-transcript.ts#L927-L946)).
Its three callers append a turn's lines only after the turn ends with the
`end_turn` stop reason: the interactive loop
([use-conversation-loop.ts:1423-1452](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/app/use-conversation-loop.ts#L1423-L1452)),
headless mode when the result is a success
([headless.ts:4650-4652](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/headless.ts#L4650-L4652)) and the
WebSocket listener's `completeSuccessfulListenerTurn`
([turn-completion.ts:67-73](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/websocket/listener/turn-completion.ts#L67-L73)).
So a user prompt is stamped later than its submission by the whole turn,
tool calls and approval waits included, and a turn that ends in an error
or an interrupt is not appended at all. `argsText` is the tool call's
arguments string as streamed, the chunks concatenated
([accumulator.ts:1094](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/accumulator.ts#L1094),
[1150-1153](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/accumulator.ts#L1150-L1153)), so a
complete call holds the arguments JSON.

**Local-backend transcript** (`messages.jsonl`, `message_format`
`pi-session-entry-jsonl`, `schema_version` 2 in `manifest.json`;
[local-transcript.ts:24-46](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L24-L46)). Line 1 is the header
`{type:"session", version:3, id, timestamp, cwd}`; later lines are
`{type:"message", id, parentId, timestamp, message}` or
`{type:"compaction", id, parentId, timestamp, summary, firstKeptEntryId, tokensBefore, message, details}`
([local-transcript.ts:122-157](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L122-L157), [236-246](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L236-L246), [local-store.ts:3036-3061](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L3036-L3061)).
Entry `id` is 8 hex characters; entry `timestamp` is ISO, taken from
`message.metadata.created_at` or `message.timestamp`
([local-transcript.ts:479-494](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L479-L494)).

`message` ([local-message.ts:26-86](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-message.ts#L26-L86)) has `id` (prefix `letta-msg-`,
[local-store.ts:135-137](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L135-L137)), `role`, `timestamp` (Unix ms), optional
`metadata` {`created_at`, `agent_id`, `conversation_id`, `provider`{`provider_id`,`model_id`,`usage`}}, and:

- `role:"user"`: `content` string or array of `text`/`image` parts ([pi types.ts:542-546](https://github.com/earendil-works/pi/blob/200387122ca450d6387f033949423114a270b96c/packages/ai/src/types.ts#L542-L546)).
- `role:"assistant"`: `content` array of `{type:"text",text}`,
  `{type:"thinking",thinking,thinkingSignature?,redacted?}`,
  `{type:"toolCall",id,name,arguments}`; plus `api`, `provider`, `model`,
  `usage`, `stopReason` ([types.ts:397-427](https://github.com/earendil-works/pi/blob/200387122ca450d6387f033949423114a270b96c/packages/ai/src/types.ts#L397-L427), [548-571](https://github.com/earendil-works/pi/blob/200387122ca450d6387f033949423114a270b96c/packages/ai/src/types.ts#L548-L571)).
- `role:"toolResult"`: `toolCallId`, `toolName`, `content` (text/image), `isError` ([types.ts:596-609](https://github.com/earendil-works/pi/blob/200387122ca450d6387f033949423114a270b96c/packages/ai/src/types.ts#L596-L609)).

**sessions.jsonl** ([session-history.ts:6-35](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/session-history.ts#L6-L35)): `agent_id`, `session_id`,
`timestamp` (ms), `project`, `model`, `provider`, `usage`, `duration`, `cost`,
and on the exit line `message_count`, `tool_call_count`, `exit_reason`
([116-158](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/session-history.ts#L116-L158)). Session metadata, not turns.

**Chunk logs** hold the last 100 server stream chunks with content cut to
200 characters ([chunk-log.ts:1-12](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/chunk-log.ts#L1-L12), [27-30](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/chunk-log.ts#L27-L30)). Useful for message ids
and timing only; not parsed into turns.

## 4. Joins

- Reflection transcript: agent and conversation from the two directory names.
  Project path: the `sessions.jsonl` line with the same `agent_id` whose
  `timestamp` is nearest before `captured_at` (heuristic; a session id is not
  stored in the transcript).
- Local backend: session id is the header `id` (conversation id); project
  path is the header `cwd`; `conversation.json` gives `agent_id`
  ([local-types.ts:30-43](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-types.ts#L30-L43)) and `lc-local-backend/agents/*.json` the agent
  `name`, `model`, `system` ([local-types.ts:18-28](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-types.ts#L18-L28)). `toolCall.id` joins
  `toolResult.toolCallId`. Entries chain by `parentId`.
- Subagents: `conversation.json` `parent_agent_id`, `is_subagent`.
- Transcript to local backend, for one conversation. Session id: the
  transcript's conversation directory is the conversation id sanitised to
  `[a-zA-Z0-9._-]`, and the `messages.jsonl` header `id` is the same
  conversation id
  ([local-transcript.ts:236-246](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L236-L246)).
  Local-backend ids are `local-conv-<n>` or `local-conv-<uuid>`
  ([local-backend.ts:209](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-backend.ts#L209),
  [local-store.ts:3177-3181](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L3177-L3181),
  [762](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L762)), or `default` for the
  agent's default conversation
  ([local-store.ts:3262-3266](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L3262-L3266)),
  none of which the sanitisation changes, so the two `session_id`s are
  equal. Project path: the header `cwd` against the `sessions.jsonl`
  heuristic above; equal in the fixture, but the pairing is by session id
  and does not depend on it. Text: the same for user and assistant text,
  thinking and tool results; a tool call's `argsText`, parsed, gives the
  argument the pi reader shows for the matching `toolCall`. Time: the
  transcript line is later than its `messages.jsonl` entry by up to the
  turn's duration, the prompt by all of it.

## 5. SQLite or binary stores

No SQLite in Letta Code. V1 `~/.letta/sqlite.db` ([0.11.7 db.py:149](https://github.com/letta-ai/letta/blob/bf9356ceaf8ac4c80f1b418f209ad49b04986885/letta/server/db.py#L149)), table
`messages` ([orm/message.py:15-61](https://github.com/letta-ai/letta/blob/bf9356ceaf8ac4c80f1b418f209ad49b04986885/letta/orm/message.py#L15-L61)): `id`, `agent_id`, `role`
(`user|assistant|system|tool`), `text`, `content` (JSON parts), `model`,
`tool_calls` (OpenAI-shaped JSON), `tool_call_id`, `tool_returns`, `step_id`,
`sequence_id`, `created_at` ([orm/base.py:16](https://github.com/letta-ai/letta/blob/bf9356ceaf8ac4c80f1b418f209ad49b04986885/letta/orm/base.py#L16)). Proposed as a later parser;
the JSON column encodings were not verified.

## 6. Format versions

Local backend: schema 1 (`pi-ai-message-jsonl`, bare message per line) and
schema 2 (session entries); `letta local-backend migrate-transcripts`
converts 1 to 2 and leaves `messages.jsonl.pre-pi-backup-*`
([local-transcript.ts:24-81](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L24-L81)). Messages may be re-appended
with the same `message.id` as replacement snapshots
([local-transcript.ts:173-182](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-transcript.ts#L173-L182)); keep the last. Reflection
`state.json` `schema_version` is `v3_assistant_steps`
([reflection-transcript.ts:28-38](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/reflection-transcript.ts#L28-L38)).

## 7. Secrets

`thinkingSignature` and `textSignature` are opaque provider blobs. Tool
arguments and results can hold pasted keys. V1 `sqlite.db` table `providers`
column `api_key` ([0.11.7 orm/provider.py:30-32](https://github.com/letta-ai/letta/blob/bf9356ceaf8ac4c80f1b418f209ad49b04986885/letta/orm/provider.py#L30-L32)).

## 8. Parser plan

Parse `transcript.jsonl` and `messages.jsonl` always (issue 122). In
local-backend mode `messages.jsonl` is the store of record, the local
backend's own message store, with models, tool ids and per-message
times; it is primary. `transcript.jsonl` copies each completed turn of the
same conversation and is a secondary source: its rows are dropped when a
`messages.jsonl` row of the same conversation has the same turn type and
text within one hour, the window a turn's end-of-turn stamp needs (see
[section 3](#3-record-schema)); a turn longer than an hour leaves its
earlier lines shown twice. What only the transcript keeps survives the
rule: deleting an agent removes its local-backend conversation directories
and leaves `~/.letta/transcripts/` alone
([local-store.ts:481-517](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/local/local-store.ts#L481-L517)),
and in the default server-backend mode the transcript is the only local
copy of the conversation. `messages.jsonl` alone holds the turns that ended
in an error or an interrupt. `sessions.jsonl` is primary, one `system` row
per line, and gives the transcript's project attribution.

| Column | transcript.jsonl | messages.jsonl |
| --- | --- | --- |
| timestamp_utc | `captured_at` | entry `timestamp` |
| session_id | conversation directory name | header `id` |
| project_path | `sessions.jsonl` `project` (heuristic) | header `cwd` |
| git_branch | empty | empty |
| turn_type | `user`, `assistant`; `reasoning` → thinking; `error` → system; `tool_call` → one tool_use and one tool_result row | role/part type; `compaction` → system |
| model | empty | `message.model` (`responseModel` when set) |
| tool_name, tool_use_id | `name`, empty | `toolCall.name`/`id`, `toolResult.toolName`/`toolCallId` |
| text | `text`; `argsText` through pi's argument summary when it parses as JSON; `resultText` | text, thinking, the argument summary, result text |

**Model rows.** `messages.jsonl` goes through pi's reader, so it gets pi's
`model: <id> provider=<provider>` row at the first assistant
`message.model` of a conversation and `model: <old> -> <new>
provider=<provider>` on each change
([section 8 of `pi.md`](pi.md#8-parser-plan)). Each `sessions.jsonl` line
is one `system` row; after the first line of a `session_id` that names a
`model`, a `model: <model> provider=<provider>` row follows, and a later
line of the same `session_id` with another `model` gets a `model: <old> ->
<new> provider=<provider>` row. `transcript.jsonl` records no model.

**Permission rows.** None of the record shapes in
[section 3](#3-record-schema) records a permission decision. A project's
`.letta/settings.local.json` holds its permissions
([`collectors/research/letta.md`](../../collectors/research/letta.md)), but
their shape is not recorded here, so the file is not read.

Sync: in the default `api` backend the conversation is server state by
design, not an upload: Letta Code creates, reads and deletes the agent
and its conversations through the server's API
([backend/backend.ts:376](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/backend.ts#L376),
[481-524](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/backend.ts#L481-L524)), the server keeps every
message, and the Letta Chat web app opens the same conversation at
`https://chat.letta.com/chat/<agent id>?conversation=<conversation id>`
([cli/helpers/app-urls.ts:14-37](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/helpers/app-urls.ts#L14-L37)).
It is on unless the user ran `letta backend local`, which sets
`preferredBackendMode` to `local` in `.letta/settings.json`
([cli/subcommands/backend.ts:38](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/subcommands/backend.ts#L38),
[65](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/subcommands/backend.ts#L65)). The local markers are the ids
listed under "Server-side session markers" in
[section 2](#2-transcript-files). The parser yields, fixture only (no
real install has shown these files):

- per `transcripts/<agent id>/<conversation id>/` whose agent id does
  not start `agent-local-`, one `system` row `session synced:
  server conversation <conversation id> agent <agent id> server <server>
  (from .letta/transcripts path, first captured_at)`, at the first
  `captured_at` of its `transcript.jsonl`, with `<server>` the
  matching `agents[]` entry's `baseUrl`, `api.letta.com` when that
  entry has none, and `-` when there is no entry;
- per `sessionsByServer` entry whose key does not start `local:`, in
  `.letta/settings.json` and in each project's
  `.letta/settings.local.json`, one `system` row `session synced: last
  session on <key> agent <agentId> conversation <conversationId> (from
  <file>, file mtime)`, at the file's modification time, with
  `session_id` the conversation id and, for the project file,
  `project_path` the project.

Deleting an agent from the `/agents` selector deletes it on its server
and touches no local file
([cli/components/AgentSelector.tsx:486-514](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/components/AgentSelector.tsx#L486-L514)),
so the transcript directories, `sessions.jsonl` lines and settings
entries that name it survive, and nothing local records that the server
copy is gone. The only callers of `deleteConversation` remove internal
fork and ephemeral conversations
([agent/subagents/fork-conversation.ts:100](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/agent/subagents/fork-conversation.ts#L100),
[websocket/app-server-openai.ts:326](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/websocket/app-server-openai.ts#L326)).
Memfs pushes the agent's memory to the server's git endpoint (see
[section 2](#2-transcript-files)); a commit there is memory, not a
transcript, and is not a row. Telemetry is on unless `LETTA_CODE_TELEM`
is `0` or `false` or `DO_NOT_TRACK` is `1`, goes to
`/v1/metadata/telemetry`, and carries counts, tool names and lengths,
not prompt text; error events, sent for Letta Cloud users only, add
`recent_chunks` and `debug_log_tail`, which can hold fragments of
streamed output; the queue is in memory and leaves no file
([telemetry/index.ts:37-112](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/telemetry/index.ts#L37-L112),
[392-405](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/telemetry/index.ts#L392-L405),
[776-800](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/telemetry/index.ts#L776-L800),
[478-480](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/telemetry/index.ts#L478-L480);
[backend/api/metadata.ts:100](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/backend/api/metadata.ts#L100)).
`/feedback` sends the user's message with the agent id, telemetry
session id and last run id, and no transcript
([cli/app/use-feedback-handler.ts:78-94](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/cli/app/use-feedback-handler.ts#L78-L94)).

Fixture `.letta/transcripts/agent-1a2b/conv-9f/transcript.jsonl`:

```json
{"kind":"user","text":"list the repo","captured_at":"2026-10-01T12:00:05.120Z","source_line_id":"ui-1"}
{"kind":"tool_call","name":"Bash","argsText":"{\"command\":\"ls\"}","resultText":"README.md","resultOk":true,"captured_at":"2026-10-01T12:00:05.120Z","source_line_id":"ui-2"}
{"kind":"assistant","text":"One file: README.md","captured_at":"2026-10-01T12:00:05.120Z","source_line_id":"ui-3","source_message_id":"message-77"}
```

Fixture `.letta/lc-local-backend/conversations/Y29udmVyc2F0aW9uOmxvY2FsLWNvbnYtMQ/messages.jsonl`:

```json
{"type":"session","version":3,"id":"local-conv-1","timestamp":"2026-10-01T12:00:00.000Z","cwd":"/home/alice/repo"}
{"type":"message","id":"a1b2c3d4","parentId":null,"timestamp":"2026-10-01T12:00:01.000Z","message":{"id":"letta-msg-1","role":"user","content":"list the repo","timestamp":1759320001000}}
{"type":"message","id":"b2c3d4e5","parentId":"a1b2c3d4","timestamp":"2026-10-01T12:00:02.000Z","message":{"id":"letta-msg-2","role":"assistant","content":[{"type":"thinking","thinking":"use ls"},{"type":"toolCall","id":"call_1","name":"Bash","arguments":{"command":"ls"}}],"api":"anthropic-messages","provider":"anthropic","model":"claude-sonnet-4-5","usage":{"input":10,"output":5,"cacheRead":0,"cacheWrite":0,"totalTokens":15,"cost":{"input":0,"output":0,"cacheRead":0,"cacheWrite":0,"total":0}},"stopReason":"toolUse","timestamp":1759320002000}}
{"type":"message","id":"c3d4e5f6","parentId":"b2c3d4e5","timestamp":"2026-10-01T12:00:03.000Z","message":{"id":"letta-msg-3","role":"toolResult","toolCallId":"call_1","toolName":"Bash","content":[{"type":"text","text":"README.md"}],"isError":false,"timestamp":1759320003000}}
```

Fixture `.letta/sessions.jsonl`:

```json
{"agent_id":"agent-1a2b","session_id":"s-1","timestamp":1759320000000,"project":"/home/alice/repo","model":"claude-sonnet-4-5","provider":"anthropic","usage":{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cached_input_tokens":0,"cache_write_tokens":0,"reasoning_tokens":0,"steps":0},"duration":{"api_ms":0,"wall_ms":0},"cost":{"type":"hosted"}}
```

Confidence. High: file locations, line shapes, field names, timestamp units
(source). Medium: pi-ai optional fields at the pinned version; the
`api` value in the fixture is illustrative. Not determined: V1 `content`
and `tool_calls` JSON encodings; whether reflection transcripts are written
on Windows when auto-reflection is off (`LETTA_ENABLE_WINDOWS_AUTO_REFLECTION`,
[reflection-settings.ts:9](https://github.com/letta-ai/letta-code/blob/77faf36e34378946c8e69c0bfaa5595a7be4c326/src/reflection-settings.ts#L9),
exists, but the append path at the cited loop is unconditional).
