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

- **Source review (2026-10-19)**: SDK at
  [`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360)
  (previously [`b347047`](https://github.com/OpenHands/software-agent-sdk/commit/b347047e2dcdd8f4b2be810aa8bc6632bc756d41)
  and [`fd26808`](https://github.com/OpenHands/software-agent-sdk/commit/fd268089e257bee4ad704ce4fdc6466bc756c71c)),
  Agent Canvas at
  [`8d39305`](https://github.com/OpenHands/OpenHands/commit/8d39305538c1d17a30cbe477e57a0e18fcee7d95)
  (previously [`a6bba78`](https://github.com/OpenHands/OpenHands/commit/a6bba78ffd5a8b31620770f52383b1a2c0477fcd)),
  CLI at [`0403f1a`](https://github.com/OpenHands/OpenHands-CLI/commit/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2)
  (unchanged since 2026-10-09). Every statement below is from source at
  those commits; no install was used.
  - Permission state: found. A new `SecurityAnalysisEvent` records the
    security analyzer's verdict per action, and `base_state.json` holds the
    standing `confirmation_policy` and `security_analyzer`; an approval
    leaves no event. The parser reads rejections only
    ([section 3](#3-record-schema), [section 8](#8-parser-plan)).
  - Model: found. The agent's own switches leave a `SwitchLLMObservation`
    or `ClassifyAndSwitchLLMObservation` with `active_model`; a switch
    through the REST endpoint (Canvas `/model`) leaves only the final
    model in `base_state.json`; `stats.usage_to_metrics` keeps the model
    per LLM response. The parser writes one `model:` row per conversation.
  - Past use beyond the primary store: found. The CLI's
    `prompt_history.json` is not read; forks are full copies; Canvas keeps
    conversation metadata and an archive list in browser storage
    ([section 5](#5-sqlite-or-binary-stores)).
  - Sync, relay and origin: found for origin, none for relay. Agent Canvas
    lists conversations from OpenHands Cloud backends and from DigitalOcean
    Managed Agents sessions (new since [`a6bba78`](https://github.com/OpenHands/OpenHands/commit/a6bba78ffd5a8b31620770f52383b1a2c0477fcd)), whose only local traces
    are browser-storage entries; the earlier note that the Canvas front end
    is not in these repositories was wrong. No messaging relay: not found
    in OpenHands at [`8d39305`](https://github.com/OpenHands/OpenHands/commit/8d39305538c1d17a30cbe477e57a0e18fcee7d95), software-agent-sdk at [`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360) or
    OpenHands-CLI at [`0403f1a`](https://github.com/OpenHands/OpenHands-CLI/commit/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2) (grepped for `telegram`, `slack`,
    `discord`, `whatsapp` and `jira`; the last is only a cloud feature
    flag).
  - Scratch directories: found. `agent-canvas/workspaces/<hex>`,
    `~/.openhands/workspaces` (automation runs) and
    `/tmp/conversation-worktrees/<dir>` (outside the home) are the agent's
    own.
  - Deletion: found. The Agent Server removes the conversation directory
    and its worktree but leaves branches, children and forks; Canvas
    archive only hides; the CLI has no delete.
  - Version drift: the event file layout and every field the parser reads
    are unchanged; one new event kind (`SecurityAnalysisEvent`) falls into
    the parser's generic `system` row.
  - Bad lines: no file is read line by line; a `meta.json` or
    `base_state.json` that does not decode is dropped without a row.

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

### What survives a delete

The Agent Server's delete, which Agent Canvas uses, notifies webhooks
with status `DELETING` and removes the conversation directory and, once
no other conversation uses it, the worktree directory; the workspace and
the worktree's branches in the user's repository stay, and children and
forks keep their now dangling `parent_conversation_id` or
`forked_from_conversation_id`
([`agent_server/conversation_service.py:1774-1838`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/conversation_service.py#L1774-L1838)).
Canvas also deletes the hidden planning conversation and the metadata
entry, and for a cloud backend the remote conversation; its archive only
adds the id to `archived-conversations`. The CLI has no delete. What
remains: the CLI's `prompt_history.json`, the last 100 prompts per
working directory with text and local time and no conversation; a fork,
which is a full copy of its source's events and state; the global
`agent-canvas/bash_events/` record of terminal commands; and Canvas
browser-storage keys with no message text, such as
`openhands-last-conversation-by-backend`
([section 5](#5-sqlite-or-binary-stores)). Nothing local records a
deleted conversation. The analyzer reads a fork as its own conversation
and does not read the prompt history, the global terminal record or the
browser storage ([section 8](#8-parser-plan)).

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

Added or first described in the 2026-10-19 review, at SDK
[`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360):

- `SecurityAnalysisEvent` (new since [`b347047`](https://github.com/OpenHands/software-agent-sdk/commit/b347047e2dcdd8f4b2be810aa8bc6632bc756d41); `source` `environment`):
  `analyzer` (the analyzer's class name, for example
  `LLMSecurityAnalyzer`), `policy` (the confirmation policy's class name:
  `AlwaysConfirm`, `NeverConfirm` or `ConfirmRisky`), `risks` (a map from
  `ActionEvent` id to `UNKNOWN`, `LOW`, `MEDIUM` or `HIGH`) and `details`
  (analyzer-specific detail per action id)
  ([`event/security.py:11-39`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/event/security.py#L11-L39)).
  It is written once per batch of pending actions whenever an analyzer is
  configured, before the policy decides whether to ask
  ([`agent/agent.py:1130-1140`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/agent/agent.py#L1130-L1140),
  [`1164-1190`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/agent/agent.py#L1164-L1190)).
- An approval writes no event: the Agent Server's
  `ConfirmationResponseRequest` (`accept`, `reason`) resumes the run on
  `accept` and calls `reject_pending_actions` otherwise
  ([`agent_server/models.py:438-442`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/models.py#L438-L442);
  [`agent_server/event_service.py:2015-2029`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/event_service.py#L2015-L2029)),
  so an approved action shows only as an `ActionEvent` followed by its
  `ObservationEvent`. A `PreToolUse` hook's block is a
  `UserRejectObservation` with `rejection_source` `hook`
  ([`agent/agent.py:360-368`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/agent/agent.py#L360-L368)).
- `base_state.json` `confirmation_policy` (`kind` `AlwaysConfirm`,
  `NeverConfirm` or `ConfirmRisky` with `threshold`), `security_analyzer`
  (`kind`, or absent) and `blocked_actions` (action id to the hook's
  reason) ([`conversation/state.py:123-127`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/conversation/state.py#L123-L127),
  [`152-157`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/conversation/state.py#L152-L157);
  [`security/confirmation_policy.py:27-61`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/security/confirmation_policy.py#L27-L61)).
  A field assignment rewrites the file
  ([`state.py:596-610`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/conversation/state.py#L596-L610)),
  so it holds the policy in force at the last write, not its history. The
  CLI's "always proceed" and "risk based" answers set `NeverConfirm` or
  `ConfirmRisky` on the conversation through the same call
  ([`tui/core/confirmation_flow_controller.py:38-48`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/tui/core/confirmation_flow_controller.py#L38-L48);
  [`tui/core/confirmation_policy_service.py:25-29`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/tui/core/confirmation_policy_service.py#L25-L29);
  [`acp_impl/confirmation.py:116-128`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/acp_impl/confirmation.py#L116-L128)),
  and `--always-approve` or headless mode starts it at `NeverConfirm`
  ([`tui/textual_app.py:729-735`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/tui/textual_app.py#L729-L735)).
  The Agent Server's default for new conversations is
  `settings.json` `conversation_settings.confirmation_mode` (default
  `false`) and `security_analyzer` (default `llm`)
  ([`sdk/settings/model.py:1175-1201`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/settings/model.py#L1175-L1201),
  [`1221-1232`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/settings/model.py#L1221-L1232);
  [`agent_server/persistence/models.py:150-183`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/persistence/models.py#L150-L183)).
- Model switches. The agent's own `switch_llm` tool loads a saved LLM
  profile and returns a `SwitchLLMObservation` with `profile_name`,
  `reason` and `active_model`; the `classify_and_switch_llm` tool returns
  a `ClassifyAndSwitchLLMObservation` with `chosen_class`, `model` and
  `active_model`
  ([`tool/builtins/switch_llm.py:43-57`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/tool/builtins/switch_llm.py#L43-L57),
  [`136-147`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/tool/builtins/switch_llm.py#L136-L147);
  [`tool/builtins/classify_and_switch_llm.py:57-75`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/tool/builtins/classify_and_switch_llm.py#L57-L75)).
  Both tools were already present at [`b347047`](https://github.com/OpenHands/software-agent-sdk/commit/b347047e2dcdd8f4b2be810aa8bc6632bc756d41). A switch through the
  Agent Server's `switch_profile` or `switch_llm` endpoints writes no
  event; it replaces `agent.llm` in `base_state.json`
  ([`agent_server/conversation_router.py:586-651`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/conversation_router.py#L586-L651);
  [`conversation/impl/local_conversation.py:1673-1743`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L1673-L1743)).
  Canvas says so itself: "manual `/model` switches go through REST and
  leave no observation in history"
  ([`src/api/conversation-metadata-store.ts:38-48`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/conversation-metadata-store.ts#L38-L48)).
  The CLI's ACP `set_session_model` is a no-op
  ([`acp_impl/agent/base_agent.py:331-339`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/acp_impl/agent/base_agent.py#L331-L339)).
- Model per response. `base_state.json` `stats.usage_to_metrics.<usage
  id>` is a full `Metrics` object (not the snapshot form) with
  `model_name`, `costs[].model`, `response_latencies[]` (`model`,
  `response_id`) and `token_usages[]` (`model`, `response_id`)
  ([`llm/utils/metrics.py:21-59`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/llm/utils/metrics.py#L21-L59),
  [`76-130`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/llm/utils/metrics.py#L76-L130);
  [`conversation/state.py:430-451`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/conversation/state.py#L430-L451)).
  `response_id` matches the `llm_response_id` of the `ActionEvent` and
  agent `MessageEvent` that the response produced
  ([`event/llm_convertible/message.py:36-41`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/event/llm_convertible/message.py#L36-L41);
  [`action.py:58-61`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-sdk/openhands/sdk/event/llm_convertible/action.py#L58-L61)),
  so the model of each turn can be recovered even after a REST switch.
  `meta.json` also has `metrics` (a snapshot with `model_name`),
  `forked_from_event_id` and `launched_agent_profile`
  ([`agent_server/models.py:115-146`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/models.py#L115-L146)).

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

Agent Canvas front-end state (2026-10-19 review, Canvas at
[`8d39305`](https://github.com/OpenHands/OpenHands/commit/8d39305538c1d17a30cbe477e57a0e18fcee7d95)).
The front end keeps its own records in browser `localStorage`: in the
Electron app that is the Chromium `Local Storage/leveldb` directory
(LevelDB, the key-value file format Chromium stores it in) under
the app's user data directory, which the catalog collects; in a browser
it is the browser profile, outside the catalog. The analyzer has no
LevelDB reader for these keys. Each value is JSON:

| Key | Holds | Survives |
| --- | --- | --- |
| `openhands-backends` | every backend the front end talks to: `id`, `name`, `host`, `apiKey`, `kind` (`local` or `cloud`), and for a DigitalOcean session `marsSessionId` and `marsConfigId` ([`src/api/backend-registry/types.ts:4-22`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/backend-registry/types.ts#L4-L22); [`storage.ts:13-14`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/backend-registry/storage.ts#L13-L14), [`95-101`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/backend-registry/storage.ts#L95-L101)) | the backend's removal |
| `openhands-last-conversation-by-backend` | backend id (with `::<org id>` for an organisation) to the last conversation opened on it, a remote id for a cloud backend ([`last-conversation-store.ts:10-18`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/backend-registry/last-conversation-store.ts#L10-L18)) | the conversation's deletion |
| `openhands-agent-server-conversation-metadata` | conversation id to `selected_repository`, `selected_branch`, `git_provider`, `selected_workspace`, `workspace_mode` (`local_repo` or `new_worktree`), `active_profile` and `stamped_at` (the LLM profile last chosen and when), `plugins`, `local_planning_conversation_id` ([`src/api/conversation-metadata-store.ts:4-56`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/conversation-metadata-store.ts#L4-L56)) | removed on delete ([`agent-server-conversation-service.api.ts:1047-1081`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/conversation-service/agent-server-conversation-service.api.ts#L1047-L1081)) |
| `archived-conversations` | `archivesByBackendId`: backend id to the conversation ids the user archived ([`src/stores/archived-conversations-store.ts:4-8`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/stores/archived-conversations-store.ts#L4-L8), [`75-78`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/stores/archived-conversations-store.ts#L75-L78)) | archive is a hide; the conversation directory stays |

None of these holds message text, so none repeats an event; they mark a
conversation's origin, workspace choice, archive state and the profile
the user picked.

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
`openhands-agent-server/` and `openhands-workspace/`. The OpenHands Cloud
server is not in these repositories, so a share or sync feature of its
own is not covered here. The Agent Canvas front end is in
[OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) and was
reviewed on 2026-10-19 (the origin line below).

Requirement classes, from the 2026-10-19 review (SDK
[`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360),
Canvas [`8d39305`](https://github.com/OpenHands/OpenHands/commit/8d39305538c1d17a30cbe477e57a0e18fcee7d95),
CLI [`0403f1a`](https://github.com/OpenHands/OpenHands-CLI/commit/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2);
evidence in [section 3](#3-record-schema) and
[section 5](#5-sqlite-or-binary-stores)):

- Permission, per call: written, for rejections (`UserRejectObservation`,
  `rejection_source` `user` or `hook`). Not yet written: the
  `SecurityAnalysisEvent` verdict, today a generic
  `SecurityAnalysisEvent: <JSON>` `system` row; proposed as one
  `permission decision: analyzed risk=<risk> analyzer=<analyzer>
  policy=<policy>` row per entry of `risks`, joined to the `ActionEvent`
  whose `id` is the key (its `tool_call_id` as `tool_use_id`). An approval
  writes nothing, so none can be shown.
- Permission, standing: not yet written. Proposed: one `permission
  setting: confirmation_policy=<kind>[ threshold=<threshold>] (from
  base_state.json, file mtime)` row, one `security_analyzer=<kind>` row,
  and one `blocked_actions.<action id>=<reason>` row per entry, per
  conversation, at the file's modification time; the value is the policy
  at the last write, not its history.
- Model: written once per conversation from `agent.llm.model`. Not yet
  written: `model: <old> -> <new>` at each `SwitchLLMObservation` or
  `ClassifyAndSwitchLLMObservation` (`active_model`, with
  ` profile=<profile_name>`), and the per-response model from
  `stats.usage_to_metrics.*.token_usages[]` joined on `llm_response_id`,
  which is the only record of a switch made through the REST endpoints.
- Past use beyond the primary store: `.openhands/projects/<sha256 of
  cwd>/prompt_history.json` (CLI; secondary): a JSON array of the last
  100 prompts per working directory, `text` and `timestamp` (naive local
  `datetime.now().isoformat()`), oldest first
  ([`stores/prompt_history.py:11-15`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/stores/prompt_history.py#L11-L15),
  [`59-95`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/stores/prompt_history.py#L59-L95)).
  It names no conversation, and its project is only a hash of the path;
  it survives the removal of a conversation directory and joins on text
  and time. Not read by the parser. A fork's directory is a deep copy of
  its source's events and state
  ([`agent_server/conversation_service.py:1952-1995`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/conversation_service.py#L1952-L1995))
  that survives the source's deletion; it is parsed as its own
  conversation and joins on `meta.json` `forked_from_conversation_id`.
  The Canvas browser-storage keys hold no message text. The global
  `agent-canvas/bash_events/` (terminal commands typed in Canvas) is a
  record of its own, not a copy, and is not read. The agent keeps no
  search index or summaries database of conversations: not found in
  software-agent-sdk at [`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360) (grepped for `sqlite3`, `fts5` and
  `search_index`, and for `summar`, whose only hits under
  `openhands-agent-server/` are profile-store listings; the one `sqlite`
  hit is a system library in the Docker image).
- Sync: none, as above. Origin: not yet written. A Canvas backend of
  `kind` `cloud` lists OpenHands Cloud conversations, and a backend with
  `marsSessionId` is a DigitalOcean Managed Agents session (MARS, the
  vendor's name for DigitalOcean's hosted agent sandboxes: a microVM that
  runs its own Agent Server with its own disk and conversations)
  ([`src/api/mars/AGENTS.md:3`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/mars/AGENTS.md#L3),
  [`13`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/mars/AGENTS.md#L13);
  [`src/api/cloud/conversation-service.api.ts:70-104`](https://github.com/OpenHands/OpenHands/blob/8d39305538c1d17a30cbe477e57a0e18fcee7d95/src/api/cloud/conversation-service.api.ts#L70-L104)).
  Their transcripts never reach `~/.openhands`; the only local traces are
  the `localStorage` keys of [section 5](#5-sqlite-or-binary-stores).
  A `session origin: remote openhands-cloud` or `remote mars session
  <id>` row would need a LevelDB reader. Relay: none (the agent records
  none; grep evidence in [section 1](#1-source)).
- Scratch directories: not written. The analyzer's catalog rule already
  classes `.openhands/agent-canvas/workspaces/<hex>` and
  `.openhands/workspaces/<run>` (both under the `.openhands` entry). A
  worktree conversation's `workspace.working_dir` is under
  `/tmp/conversation-worktrees/<dir>` by default, outside every home, so
  it is listed as a project
  ([`agent_server/config.py:286-293`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/config.py#L286-L293);
  [`agent_server/local_storage.py:14-23`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/local_storage.py#L14-L23));
  a `scratch directory: <working_dir> (conversation worktree)` row for a
  `working_dir` under that default root is proposed. The root is
  configurable, so a non-default root cannot be recognised from the
  conversation's files.
- Deletion: the Agent Server's delete notifies webhooks with status
  `DELETING`, removes the conversation directory and, once no other
  conversation uses it, the worktree directory, whose branches stay in
  the user's repository; the workspace is kept, and children and forks
  keep dangling ids
  ([`agent_server/conversation_service.py:1774-1838`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/conversation_service.py#L1774-L1838);
  [`local_storage.py:26-37`](https://github.com/OpenHands/software-agent-sdk/blob/33d8aa29c3078d074799e2fbf5e847aeb2d71360/openhands-agent-server/openhands/agent_server/local_storage.py#L26-L37)).
  Canvas also deletes the hidden planning conversation and the metadata
  entry, and for a cloud backend deletes the remote conversation; its
  archive only adds the id to `archived-conversations`. The CLI has no
  delete; `openhands logout` removes `cloud/api_key.txt`
  ([`auth/token_storage.py:55-61`](https://github.com/OpenHands/OpenHands-CLI/blob/0403f1a79a9fc62a6c7be21c17d7b51f64245ad2/openhands_cli/auth/token_storage.py#L55-L61)).
  Nothing local records a deleted conversation.
- Bad lines: no file is read line by line, and an event file that does
  not decode gives one `parser: event file could not be decoded
  (<reason>)` row. A `meta.json` or `base_state.json` that exists but
  cannot be read, does not decode or is not a JSON object is read as
  empty and gives one whole-file `system` row on the conversation's first
  event file, after the header and model rows: `parser: <file name> could
  not be decoded (<reason>)`, `parser: <file name> could not be read
  (<reason>)` or `parser: <file name> is not a JSON object`, with an
  empty timestamp and the session id and `project_path` the other file
  still gives. The header then lacks what the file held (title, model,
  time basis). A missing file is not an error, since the CLI writes no
  `meta.json`. The cut-file shape is not observed on any real install,
  source-derived (OpenHands/software-agent-sdk at
  [`33d8aa2`](https://github.com/OpenHands/software-agent-sdk/commit/33d8aa29c3078d074799e2fbf5e847aeb2d71360)).

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
