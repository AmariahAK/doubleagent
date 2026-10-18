# OpenHands transcript schema

Catalog agent: `openhands`. Current OpenHands (Agent Canvas and the
`openhands` CLI) persists conversations through the Software Agent SDK as
one JSON file per event. Path research is in
[../../collectors/research/openhands.md](../../collectors/research/openhands.md).

## 1. Source

[OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) at
[`b347047e2dcdd8f4b2be810aa8bc6632bc756d41`](https://github.com/OpenHands/software-agent-sdk/commit/b347047e2dcdd8f4b2be810aa8bc6632bc756d41)
(SDK and Agent Server), [OpenHands/OpenHands-CLI](https://github.com/OpenHands/OpenHands-CLI) at
[`954f2ba646e8d749261a8f2b2b7e3031fa39be9f`](https://github.com/OpenHands/OpenHands-CLI/commit/954f2ba646e8d749261a8f2b2b7e3031fa39be9f),
and the legacy app at [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) tags `1.11.0`
([`11ca68ab2e15dcd85c21e4d7d3409e7a259369ac`](https://github.com/OpenHands/OpenHands/commit/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac))
and `0.62.0` ([`7fbb48c40679afd674970966b96185657d92a487`](https://github.com/OpenHands/OpenHands/commit/7fbb48c40679afd674970966b96185657d92a487)). MIT, open source.

Sync and upload were checked on 2026-10-17 at
[`fd26808`](https://github.com/OpenHands/software-agent-sdk/commit/fd268089e257bee4ad704ce4fdc6466bc756c71c)
(SDK) and
[`0403f1a`](https://github.com/OpenHands/OpenHands-CLI/commit/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2)
(CLI), newer than the commits above.

## 2. Transcript files

One directory per conversation, named by the conversation UUID as 32 hex
digits ([`openhands-sdk/openhands/sdk/conversation/base.py:331-345`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/base.py#L331-L345)), under:

- `.openhands/agent-canvas/dev_conversations/<hex>/` (Canvas, native) and
  `.openhands/agent-canvas/conversations/<hex>/` (Canvas in Docker);
- `.openhands/conversations/<hex>/` (CLI).

Inside ([`conversation/persistence_const.py:4-10`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/persistence_const.py#L4-L10)):

- `events/event-<idx, 5+ digits>-<event id>.json`, one compact JSON object
  per event ([`conversation/event_store.py:225-232`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/event_store.py#L225-L232),[`313-318`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/event_store.py#L313-L318)),
  plus an empty `.eventlog-len-<n>.marker` ([`event_store.py:27`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/event_store.py#L27)).
- `base_state.json`: `ConversationState` (agent with its LLM config,
  workspace, stats, secret registry)
  ([`conversation/state.py:82-225`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/state.py#L82-L225), [`435-447`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/state.py#L435-L447)).
- `meta.json` (Agent Server only): `StoredConversation`
  ([`openhands-agent-server/openhands/agent_server/event_service.py:276-297`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/event_service.py#L276-L297)).
- `bash_events/` for terminal sessions bound to the conversation
  ([`agent_server/dependencies.py:72-80`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/dependencies.py#L72-L80)); the global
  `.openhands/agent-canvas/bash_events/` has the same files.
- `TASKS.json` (CLI plan panel,
  [`openhands_cli/tui/panels/plan_side_panel.py:107`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/tui/panels/plan_side_panel.py#L107)).

The CLI also keeps `.openhands/projects/<sha256(cwd)>/prompt_history.json`
([`openhands_cli/locations.py:34-47`](https://github.com/OpenHands/OpenHands-CLI/blob/954f2ba646e8d749261a8f2b2b7e3031fa39be9f/openhands_cli/locations.py#L34-L47)).

## 3. Record schema

Every event has `kind` (the Python class name,
[`openhands-sdk/openhands/sdk/utils/models.py:202-205`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/utils/models.py#L202-L205)), `id` (UUID string),
`timestamp`, `source` in `agent|user|environment|hook`, `parent_id`
([`event/base.py:24-40`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/base.py#L24-L40); [`event/types.py:4-5`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/types.py#L4-L5)).
`timestamp` is `datetime.now().isoformat()`: **naive local time** with
microseconds and no zone ([`base.py:28-31`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/base.py#L28-L31)). The parser needs the
host's zone to convert it; `meta.json` `created_at`/`updated_at` are UTC
with offset ([`agent_server/models.py:120-121`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/models.py#L120-L121); [`agent_server/utils.py:53-55`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/utils.py#L53-L55))
and can anchor the offset. Files are written with `exclude_none`.

Kinds:

- `MessageEvent`: `source` user or agent, `llm_message` (`role`
  `user|system|assistant|tool`, `content` list of `{type:"text",text}` or
  `{type:"image",image_urls}`, `tool_calls?`, `reasoning_content?`,
  `thinking_blocks?`), `activated_skills`, `extended_content`, `sender`
  ([`event/llm_convertible/message.py:25-60`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/llm_convertible/message.py#L25-L60);
  [`llm/message.py:174-176`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/message.py#L174-L176), [`205-207`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/message.py#L205-L207), [`219-245`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/message.py#L219-L245)).
- `ActionEvent`: `thought` (text list), `reasoning_content`,
  `thinking_blocks` (`{type:"thinking",thinking,signature}` or
  `redacted_thinking`), `action` (object with its own `kind`, for example
  `TerminalAction` with `command`), `tool_name`, `tool_call_id`, `tool_call`
  (`id`, `name`, `arguments` JSON string, `origin`), `llm_response_id`,
  `security_risk`, `summary`
  ([`event/llm_convertible/action.py:24-80`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/llm_convertible/action.py#L24-L80);
  [`llm/message.py:25-40`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/message.py#L25-L40), [`123-147`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/message.py#L123-L147);
  [`openhands-tools/openhands/tools/terminal/definition.py:86-89`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-tools/openhands/tools/terminal/definition.py#L86-L89)).
  Tool names are the snake-cased class name without `_tool`, so
  `terminal`, `file_editor` ([`tool/tool.py:397`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/tool/tool.py#L397)).
- `ObservationEvent`: `tool_name`, `tool_call_id`, `action_id`,
  `observation` (own `kind`, `content` list, `is_error`; `TerminalObservation`
  adds `command`, `exit_code`)
  ([`event/llm_convertible/observation.py:17-40`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/llm_convertible/observation.py#L17-L40);
  [`tool/schema.py:367-382`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/tool/schema.py#L367-L382); [`terminal/definition.py:146-152`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-tools/openhands/tools/terminal/definition.py#L146-L152)).
- `UserRejectObservation` (`rejection_reason`, `rejection_source`,
  `action_id`) and `AgentErrorEvent` (`error`, `classification`)
  ([`observation.py:86-147`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/llm_convertible/observation.py#L86-L147)).
- `SystemPromptEvent`: `system_prompt`, `tools`, `dynamic_context`
  ([`event/llm_convertible/system.py:12-35`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/llm_convertible/system.py#L12-L35)).
- `ACPToolCallEvent` (Claude Code, Codex, Gemini driven over ACP):
  `tool_call_id`, `title`, `status`, `tool_kind`, `raw_input`,
  `raw_output`, `content`, `is_error` ([`event/acp_tool_call.py:46-65`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/acp_tool_call.py#L46-L65)).
- `HookExecutionEvent` (`hook_event_type`, `hook_command`, `exit_code`,
  `stdout`, `stderr`, `blocked`; [`event/hook_execution.py:22-80`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/hook_execution.py#L22-L80)),
  `Condensation` and `CondensationSummaryEvent` (`summary`;
  [`event/condenser.py:11-37`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/condenser.py#L11-L37), [`120-126`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/condenser.py#L120-L126)),
  `ConversationStateUpdateEvent` (`key`, `value`;
  [`event/conversation_state.py:18-35`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/conversation_state.py#L18-L35)), `PauseEvent`, `InterruptEvent`
  ([`event/user_action.py:7-32`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/event/user_action.py#L7-L32)).

`meta.json`: `id`, `title`, `created_at`, `updated_at`,
`forked_from_conversation_id`, `workspace` (`kind`, `working_dir`),
`parent_conversation_id`, `secrets`, `initial_message`
([`agent_server/models.py:102-143`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/models.py#L102-L143);
[`conversation/request.py:93-156`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/request.py#L93-L156)). `base_state.json`: `id`,
`agent.llm.model` ([`llm/llm.py:272`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/llm.py#L272); [`agent/base.py:117`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/agent/base.py#L117)),
`workspace.working_dir` ([`workspace/base.py:43`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/workspace/base.py#L43)), `execution_status`,
`stats.usage_to_metrics`.

Bash events (`bash_events/<YYYYMMDDHHMMSSffffff>_<kind>_[<command id>_]<event id>`,
no extension, indented JSON;
[`agent_server/bash_service.py:61-85`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/bash_service.py#L61-L85)): `BashCommand` (`id`,
`timestamp` UTC, `command`, `cwd`), `BashOutput` (`command_id`, `order`,
`exit_code`, `stdout`, `stderr`), `BashError`
([`agent_server/models.py:616-660`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-agent-server/openhands/agent_server/models.py#L616-L660)).

## 4. Joins

Session to project: `meta.json` or `base_state.json`
`workspace.working_dir` (a container path under Canvas-in-Docker).
Tool call to result: `ActionEvent.tool_call_id` = `ObservationEvent.tool_call_id`;
also `ObservationEvent.action_id` = `ActionEvent.id`. Parent to child
conversation: `meta.json` `parent_conversation_id`,
`forked_from_conversation_id`. Event order: the `idx` in the file name;
`parent_id` forms a tree when the user navigated back and branched.

## 5. SQLite or binary stores

None for current transcripts. Legacy 1.x kept conversation metadata in
`.openhands/openhands.db`
([`openhands/app_server/services/db_session_injector.py:192`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/services/db_session_injector.py#L192)). Legacy 0.x
wrote `agent_state.pkl` and `conversation_stats.pkl` (Python pickle; never
unpickle evidence) ([`openhands/storage/locations.py:29-38`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/storage/locations.py#L29-L38)).
`.openhands/automation/automations.db` is SQLite (automation schedules and
runs), outside this parser's scope.

## 6. Format versions

- Current SDK: as above. The 5-digit index is a minimum
  ([`persistence_const.py:6-10`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/persistence_const.py#L6-L10)).
- Legacy 1.x app: `.openhands/[<user_id>/]v1_conversations/<hex>/<event hex>.json`
  ([`openhands/app_server/conversation_paths.py:12`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/conversation_paths.py#L12); [`event/event_service_base.py:89`](https://github.com/OpenHands/OpenHands/blob/11ca68ab2e15dcd85c21e4d7d3409e7a259369ac/openhands/app_server/event/event_service_base.py#L89)),
  SDK events stored by id rather than index (inferred: the app server
  relays SDK events; field shapes not re-read).
- Legacy 0.x: `.openhands/sessions/<sid>/events/<n>.json` with top-level
  `id`, `timestamp`, `source`, `message`, `cause`, `action` or
  `observation`, `tool_call_metadata`, `llm_metrics`, and `args`/`extras`
  ([`openhands/events/serialization/event.py:15-25`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/events/serialization/event.py#L15-L25);
  [`openhands/storage/locations.py:1-18`](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/storage/locations.py#L1-L18)). A different parser.

## 7. Secrets

`base_state.json` `agent.llm.api_key`, `aws_secret_access_key`
([`llm/llm.py:277`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/llm.py#L277), [`327`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/llm/llm.py#L327)) and `secret_registry`, and
`meta.json` `secrets`, are Fernet ciphertext when the server has
`OH_SECRET_KEY` (in `.openhands/agent-canvas/secret-key.txt`), else
redacted as `**********` ([`conversation/state.py:435-447`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/conversation/state.py#L435-L447);
[`utils/pydantic_secrets.py:48-78`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/utils/pydantic_secrets.py#L48-L78)). `thinking_blocks[].signature`,
`responses_reasoning_item.encrypted_content` are opaque blobs. Terminal
output in observations and bash events can contain pasted tokens.

`.openhands/cloud/api_key.txt` holds the OpenHands Cloud account key in
plain text (mode 0600), written by `openhands login` and read by
`openhands cloud` and `openhands acp --cloud`
([`openhands_cli/auth/token_storage.py:19-37`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/auth/token_storage.py#L19-L37));
the collector flags it through the `.openhands/cloud/*` secret glob.

## 8. Parser plan

Globs: `.openhands/agent-canvas/dev_conversations/*/events/event-*.json`,
`.openhands/agent-canvas/conversations/*/events/event-*.json`,
`.openhands/conversations/*/events/event-*.json`; read the sibling
`meta.json` and `base_state.json` once per conversation. Optional:
`bash_events/*`. One row per event; an `ActionEvent` also yields a
`thinking` row for `thought`/`reasoning_content`. Detect and report legacy
`sessions/*/events/*.json` without parsing.

| Column | Source |
| --- | --- |
| timestamp_utc | event `timestamp` (naive local; convert with the host zone, else mark) |
| session_id | conversation directory name (hex) or `meta.json` `id` |
| project_path | `workspace.working_dir` |
| git_branch | empty |
| turn_type | `MessageEvent` by `llm_message.role`; `ActionEvent`, `ACPToolCallEvent` → tool_use; `ObservationEvent`, `UserRejectObservation` → tool_result; others → system |
| model | `base_state.json` `agent.llm.model` |
| tool_name, tool_use_id | `tool_name`, `tool_call_id` |
| text | message text; `action.command` or `tool_call.arguments`; observation `content[].text`; `error`; `summary` |

Model and permission rows (issues 96 and 97):

- `model: <id>`: a `system` row after the conversation's header row, at
  the header's time, from `base_state.json` `agent.llm.model`. The
  research records one model per conversation and no event that records a
  model switch, so no `model: <old> -> <new>` row is written; whether a
  switch in the middle of a conversation is persisted is not researched.
- `permission decision: rejected rejection_source=<rejection_source>
  <rejection_reason>`: a `system` row immediately after the
  `UserRejectObservation`'s `tool_result` row, with its `tool_name` and
  `tool_call_id`, from `rejection_source` (`-` when missing) and
  `rejection_reason`.
- ` security_risk=<value>` at the end of an `ActionEvent`'s `tool_use`
  text, from `security_risk`.

Sync: OpenHands records no sync state on disk. Two features send work
to OpenHands Cloud (the vendor's hosted service at `app.all-hands.dev`,
which runs each conversation in a sandbox of its own), and neither
writes a local file that names the remote conversation:

- `openhands cloud -t <task>` (or `-f <file>`) posts the task text and
  the GitHub or GitLab `owner/repo` and branch of the working directory's
  `origin` remote to `/api/v1/app-conversations`, then prints the remote
  conversation id and its browser URL
  ([`openhands_cli/cloud/conversation.py:54-133`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/cloud/conversation.py#L54-L133);
  [`auth/api_client.py:109-112`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/auth/api_client.py#L109-L112);
  [`argparsers/cloud_parser.py:16-45`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/argparsers/cloud_parser.py#L16-L45)).
  The id goes to stdout only; the CLI's only file writes are the API
  key, `cli_config.json`, the prompt history and the SDK's local
  conversation store, which this command does not open
  ([`auth/token_storage.py:27-37`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/auth/token_storage.py#L27-L37);
  [`stores/cli_settings.py:56-62`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/stores/cli_settings.py#L56-L62);
  [`stores/prompt_history.py:92-93`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/stores/prompt_history.py#L92-L93)).
  A cloud-backed conversation store is a stub that raises
  `NotImplementedError`
  ([`conversations/store/cloud.py:10-50`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/conversations/store/cloud.py#L10-L50)).
- `openhands acp --cloud` (ACP, the Agent Client Protocol an editor such
  as Zed uses to drive the CLI as its agent) runs every session as an SDK
  `RemoteConversation` in an OpenHands Cloud workspace: the events are
  kept by the agent server inside the cloud sandbox, and the call that
  builds the conversation passes no `persistence_dir`, unlike the local
  agent, so nothing is written under `.openhands/conversations/`
  ([`acp_impl/agent/remote_agent.py:186-258`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/acp_impl/agent/remote_agent.py#L186-L258);
  [`acp_impl/agent/local_agent.py:188`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/acp_impl/agent/local_agent.py#L188);
  [`argparsers/acp_parser.py:32-46`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/argparsers/acp_parser.py#L32-L46)).
  The only local file a remote conversation can leave is an LLM
  completion log, and only when `log_completions` is set on the agent's
  LLM
  ([`sdk/conversation/impl/remote_conversation.py:1251-1282`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py#L1251-L1282)).
  The session id the editor holds is the remote conversation id; the
  editor's own state is outside this catalog entry.

Both need `openhands login`, which stores the account key in
`.openhands/cloud/api_key.txt` ([section 7](#7-secrets)) and pulls the
account's settings down rather than pushing anything up
([`auth/login_command.py:31`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/auth/login_command.py#L31);
[`auth/api_client.py:307-347`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/auth/api_client.py#L307-L347)).
Neither has a local delete: the CLI has no conversation delete command,
and the remote copy is managed in the web app, whose code is not in
these repositories.

Other traffic that leaves the host beyond the model call, none of which
carries a session marker:

- The critic (an OpenHands model that scores whether the agent's run
  succeeded) is on by default (`critic.enable_critic` in
  `.openhands/cli_config.json`) for models served through the OpenHands
  provider, and sends the conversation's messages and tools to the
  vendor's LLM proxy at `llm-proxy.app.all-hands.dev/vllm`
  ([`stores/cli_settings.py:23-26`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/stores/cli_settings.py#L23-L26);
  [`stores/agent_store.py:91-130`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/stores/agent_store.py#L91-L130);
  [`sdk/critic/impl/api/critic.py:58-105`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-sdk/openhands/sdk/critic/impl/api/critic.py#L58-L105)).
  Each critic result is also sent to PostHog (a product analytics
  service) as a `critic_inference` event, and each feedback button
  press other than dismiss as `critic_feedback`, with the raw local
  conversation id as the PostHog identity, the score, the agent model and
  the critic's `event_ids`, but no message text, with no consent check
  ([`tui/utils/critic/feedback.py:29-79`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/tui/utils/critic/feedback.py#L29-L79),
  [`228-270`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/tui/utils/critic/feedback.py#L228-L270);
  [`tui/widgets/richlog_visualizer.py:332-345`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/tui/widgets/richlog_visualizer.py#L332-L345)).
  The `posthog` package arrives through `browser-use`, so it is present
  in a source install
  ([`uv.lock:263-290`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/uv.lock#L263-L290)).
- The Agent Server's product telemetry is off by default (consent
  `unset` is not consent, the exporter defaults to `none`), allowlists
  scalar fields so no prompt or reply text can be sent, and pseudonymises
  conversation ids; the consent is kept in
  `.openhands/settings.json` `misc_settings.telemetry.consent`
  (`granted`, `denied` or `unset`)
  ([`agent_server/telemetry/policy.py:160-216`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/telemetry/policy.py#L160-L216);
  [`agent_server/config.py:151-172`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/config.py#L151-L172);
  [`agent_server/telemetry/models.py:1-16`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/telemetry/models.py#L1-L16);
  [`agent_server/telemetry/factory.py:112-124`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/telemetry/factory.py#L112-L124);
  [`agent_server/persistence/store.py:821-829`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/persistence/store.py#L821-L829)).
- Agent Server webhooks post events and conversation info to a
  configured URL; the list is empty by default and is set by whoever
  launches the server, not stored per conversation
  ([`agent_server/config.py:91-105`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/config.py#L91-L105),
  [`322-325`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/config.py#L322-L325)).

The trajectory export (`GET /download-trajectory/<id>`, Agent Canvas's
download) is a download to the user, not an upload: it zips the
conversation directory with credential fields redacted into a temporary
`<hex>.zip` beside it and deletes the zip once the response is sent
([`agent_server/file_router.py:179-216`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/file_router.py#L179-L216),
[`937-960`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/file_router.py#L937-L960)).
A conversation deleted through the Agent Server loses its whole
directory; a child or fork keeps its `parent_conversation_id` or
`forked_from_conversation_id` pointing at it
([`agent_server/conversation_service.py:1774-1838`](https://github.com/OpenHands/software-agent-sdk/blob/fd268089e257bee4ad704ce4fdc6466bc756c71c/openhands-agent-server/openhands/agent_server/conversation_service.py#L1774-L1838)).
No `session synced:` row is proposed. Searched: `cloud`, `share`,
`upload`, `sync`, `export`, `trajectory`, `feedback`, `posthog`,
`telemetry`, `webhook`, `remote`, `app_conversation_id`, `sandbox_id`,
`all-hands.dev` in `openhands_cli/`, `openhands-sdk/`,
`openhands-agent-server/` and `openhands-workspace/`. The Agent Canvas
front end and the OpenHands Cloud server are not in these repositories,
so a share or sync feature of theirs is not covered here.

Fixture (`.openhands/conversations/0f0e0d0c111140008000000000000001/`):

`meta.json`:
`{"id":"0f0e0d0c-1111-4000-8000-000000000001","title":"List files","created_at":"2026-10-01T10:00:00Z","updated_at":"2026-10-01T10:00:05Z","workspace":{"kind":"LocalWorkspace","working_dir":"/home/alice/proj"}}`

```json
{"kind":"MessageEvent","id":"6b1d5c2e-0000-4000-8000-000000000001","timestamp":"2026-10-01T12:00:01.000000","source":"user","llm_message":{"role":"user","content":[{"type":"text","text":"list the files"}]},"activated_skills":[],"extended_content":[]}
{"kind":"ActionEvent","id":"6b1d5c2e-0000-4000-8000-000000000002","timestamp":"2026-10-01T12:00:03.000000","source":"agent","thought":[{"type":"text","text":"I will run ls."}],"action":{"kind":"TerminalAction","command":"ls"},"tool_name":"terminal","tool_call_id":"call_1","tool_call":{"id":"call_1","name":"terminal","arguments":"{\"command\":\"ls\"}","origin":"completion"},"llm_response_id":"resp_1","security_risk":"LOW"}
{"kind":"ObservationEvent","id":"6b1d5c2e-0000-4000-8000-000000000003","timestamp":"2026-10-01T12:00:04.000000","source":"environment","tool_name":"terminal","tool_call_id":"call_1","action_id":"6b1d5c2e-0000-4000-8000-000000000002","observation":{"kind":"TerminalObservation","content":[{"type":"text","text":"README.md"}],"is_error":false,"command":"ls","exit_code":0}}
```

(files `events/event-00000-6b1d5c2e-...0001.json` and so on, one object
each).

Confidence. High: directory layout, file naming, `kind` discriminator,
event field names, the naive local `timestamp`, Fernet secrets. Also high: `security_risk` values `UNKNOWN`, `LOW`, ...
([`security/risk.py:13-21`](https://github.com/OpenHands/software-agent-sdk/blob/b347047e2dcdd8f4b2be810aa8bc6632bc756d41/openhands-sdk/openhands/sdk/security/risk.py#L13-L21)). Medium: the 1.x `v1_conversations` event shape. Not determined: whether
any surface writes a zone-aware event timestamp, and the full set of
action and observation `kind` values, which grows with each tool.
